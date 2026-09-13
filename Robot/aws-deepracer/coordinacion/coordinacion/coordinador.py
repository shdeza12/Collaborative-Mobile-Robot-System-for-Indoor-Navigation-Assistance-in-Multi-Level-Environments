#!/usr/bin/env python3
"""Nodo de coordinacion. Sirve /coordinacion/guiar_usuario y manda a los robots.

Es el cableado ROS alrededor de planificador.py. La decision de QUE hacer -que
robot, cuantos tramos, cuantos relevos- vive alli y se prueba sin simulador; aqui
solo queda la parte que necesita un grafo vivo: publicar el catalogo, servir la
accion, llamar a navigate_to_pose y comprobar la llegada.

Interfaces, segun §4 de Documentos/CONTRATO_INTERFACES.md:
    /coordinacion/guiar_usuario    accion GuiarUsuario     (la sirve este nodo)
    /coordinacion/estado_mision    EstadoMision a 1 Hz     (lo publica)
    /coordinacion/puntos_interes   ListaPuntosInteres      (latched, al arrancar)
    /coordinacion/confirmacion_piso  std_msgs/String       (la escucha, RF-28)
    /<ns>/navigate_to_pose         accion de Nav2          (la llama)

UN AVISO QUE NO ES TEORICO. El §2 del contrato quedo refutado el 2026-08-18:
nav2_msgs/NavigateToPose CAMBIA de definicion entre Humble y Jazzy -en Humble el
result es std_msgs/Empty, en Jazzy lleva error_code y error_msg-. Este nodo, por
tanto, NO puede mandar a la vez a un robot simulado (Humble) y a uno fisico
(Jazzy): el cliente de accion simplemente no encontrara servidor, y sin mensaje
de error. El mismo codigo fuente sirve para los dos destinos, pero no a la vez.
Si un tramo se queda esperando servidor para siempre, mirar esto primero.
"""

import datetime
import math
import os
import sys
import time

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav2_msgs.srv import ClearEntireCostmap
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from rclpy.action import ActionClient, ActionServer, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile

from coordinacion_msgs.action import GuiarUsuario
from coordinacion_msgs.msg import EstadoMision, ListaPuntosInteres, PuntoInteres
from coordinacion.registrador import RegistroMision, entorno_simulacion

from coordinacion.planificador import (
    ASIGNACION_POR_DEFECTO, CANCELANDO, COMPLETADA, ErrorPlanificacion,
    ESPERANDO_CONFIRMACION, FALLIDA, INACTIVA, RECIBIDA, TRANSFERENCIA,
    condicion_de, generar_mision_id, planificar, yaw_a_cuaternion,
)
from coordinacion.espera_confirmacion import ALERTA_S, PLAZO_S, Enganche, fase


class _Cancelada(Exception):
    """Señal interna: el usuario canceló la misión (RF-29, botón Cancelar).

    La levanta cualquiera de los tres puntos de espera de _ejecutar (entre
    tramos, dentro de _navegar mientras Nav2 responde, y dentro de
    _esperar_confirmacion). La captura _ejecutar en un solo sitio, que es
    quien manda al robot en curso de vuelta a su escalera antes de cerrar la
    misión: no se le abandona a mitad de pasillo.
    """

    def __init__(self, robot):
        super().__init__(f"cancelada, {robot} vuelve a su escalera")
        self.robot = robot

# Criterio de llegada del §3.3 de PROTOCOLO_EXPERIMENTAL.md, medido contra
# /<ns>/odom. No inventar otro aqui: si se cambia, se cambia en el protocolo
# primero, y entonces las corridas anteriores dejan de ser comparables.
#
# YA NO ES la 'xy_goal_tolerance' de Nav2, aunque lo fue hasta el 2026-08-27.
# Son dos numeros distintos y conviene que lo sean: la tolerancia dice cuando
# Nav2 PARA -segun lo que CREE AMCL-, y este dice cuando la llegada se ACEPTA
# -segun la verdad de terreno-. Igualarlos dejaba margen cero, y por eso el
# 27-ago una etapa paro creyendose a 0.240 m, dentro, estando a 0.297 m, fuera.
# La tolerancia bajo a 0.15 justamente para comprar ese margen: 0.150 de parada
# + 0.065 de error previsto de AMCL + 0.023 de desfase del fin del plan = 0.238,
# que cabe en estos 0.25. Bajar este numero a 0.15 destruiria ese presupuesto.
TOLERANCIA_LLEGADA_M = 0.25


def _normalizar(a):
    """Lleva un angulo al intervalo (-pi, pi]."""
    return math.atan2(math.sin(a), math.cos(a))


class Coordinador(Node):

    def __init__(self):
        super().__init__("coordinador")

        self.declare_parameter("ruta_puntos", "")
        self.declare_parameter("robot_nivel_1", ASIGNACION_POR_DEFECTO[1])
        self.declare_parameter("robot_nivel_2", ASIGNACION_POR_DEFECTO[2])
        self.declare_parameter("espera_servidor_s", 20.0)
        # Prefijo del identificador de mision. Lo pone quien lanza la campana;
        # vacio significa corrida suelta. Ver §2.1 de ESQUEMA_REGISTRO_MISION.md.
        self.declare_parameter("prefijo_mision", "")
        # RF-25. Carpeta vacia = no registrar, para poder usar el
        # coordinador en una demostracion sin ensuciar el disco.
        self.declare_parameter("ruta_registros", "")
        self.declare_parameter("condicion", "simulacion")

        self.asignacion = {
            1: self.get_parameter("robot_nivel_1").value,
            2: self.get_parameter("robot_nivel_2").value,
        }
        self.espera_servidor = self.get_parameter("espera_servidor_s").value
        self.prefijo_mision = self.get_parameter("prefijo_mision").value
        self.ruta_registros = self.get_parameter("ruta_registros").value
        self.condicion = self.get_parameter("condicion").value
        self.registro = None   # RegistroMision de la mision en curso

        self.catalogo = self._cargar_catalogo()
        self.grupo = ReentrantCallbackGroup()

        # Catalogo: latched, porque la HRI se conecta mucho despues de que este
        # nodo arranque. Ver la nota de ListaPuntosInteres.msg sobre por que aqui
        # retener SI es correcto y en amcl_pose no.
        qos_latched = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST,
                                 durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.pub_puntos = self.create_publisher(
            ListaPuntosInteres, "/coordinacion/puntos_interes", qos_latched)
        self._publicar_catalogo()

        self.pub_mision = self.create_publisher(
            EstadoMision, "/coordinacion/estado_mision", 10)
        self.estado = EstadoMision()
        self.estado.etapa = INACTIVA
        self.estado.mensaje_usuario = "Sin mision activa."
        self.create_timer(1.0, self._publicar_estado)   # 1 Hz, como pide el §4

        # Un cliente de navegacion y un lector de /odom por robot.
        self.clientes = {}
        self.ultimo_odom = {}
        for ns in set(self.asignacion.values()):
            self.clientes[ns] = ActionClient(
                self, NavigateToPose, f"/{ns}/navigate_to_pose",
                callback_group=self.grupo)
            self.create_subscription(
                Odometry, f"/{ns}/odom",
                lambda msg, n=ns: self._odom(msg, n), 10,
                callback_group=self.grupo)

        # Clientes para limpiar los costmaps antes de la vuelta a casa de una
        # cancelacion. MEDIDO EL 2026-09-13: cancelar a un robot a mitad de un
        # corredor estrecho -p. ej. cruzando una puerta- puede dejar SU PROPIA
        # posicion marcada como espacio letal en el costmap local un rato
        # despues de parar («Starting point in lethal space!»), y el
        # planificador rechaza cualquier goal nuevo, incluida la vuelta a
        # casa, hasta que decae solo. Limpiar antes de reintentar evita esa
        # espera.
        self.clientes_costmap = {
            ns: {
                "global": self.create_client(
                    ClearEntireCostmap, f"/{ns}/global_costmap/clear_entirely_global_costmap",
                    callback_group=self.grupo),
                "local": self.create_client(
                    ClearEntireCostmap, f"/{ns}/local_costmap/clear_entirely_local_costmap",
                    callback_group=self.grupo),
            }
            for ns in set(self.asignacion.values())
        }

        self.servidor = ActionServer(
            self, GuiarUsuario, "/coordinacion/guiar_usuario",
            execute_callback=self._ejecutar, cancel_callback=self._cancelar_solicitado,
            callback_group=self.grupo)

        # RF-28. El usuario avisa por aqui de que ya cambio de piso. Topico y no
        # servicio a proposito: 'ros2 bag' NO graba servicios, y el instante de
        # la confirmacion tiene que quedar en el bag para poder comprobarlo
        # despues. Es la misma razon por la que origen_id y destino_id estan en
        # EstadoMision y no solo en el goal.
        #
        # El callback_group NO es decoracion: el bucle de _esperar_confirmacion
        # bloquea dentro de _ejecutar. Solo porque self.grupo es reentrante y el
        # executor es multihilo puede correr este callback mientras aquel espera.
        # Con el grupo mutuamente excluyente por defecto, la espera se agotaria
        # SIEMPRE a los 120 s aunque el usuario confirmara al instante.
        self.enganche = Enganche()
        self.create_subscription(
            String, "/coordinacion/confirmacion_piso",
            self._confirmacion, 10, callback_group=self.grupo)

        self.get_logger().info(
            f"Coordinador listo. {len(self.catalogo)} puntos, "
            f"asignacion {self.asignacion}")

    # ---------------------------------------------------------------- catalogo

    def _cargar_catalogo(self):
        ruta = self.get_parameter("ruta_puntos").value
        if not ruta:
            from ament_index_python.packages import get_package_share_directory
            ruta = os.path.join(
                get_package_share_directory("deepracer_bringup"),
                "config", "puntos_interes.yaml")
        with open(ruta, encoding="utf-8") as f:
            puntos = yaml.safe_load(f)["puntos"]
        self.ruta_puntos = ruta

        provisionales = [p["id"] for p in puntos if p.get("provisional")]
        if provisionales:
            # No bloquea: sirve para construir e integrar el relevo. Si bloquea
            # es la campana de S24, que exige poses reales. Se avisa en cada
            # arranque para que nadie mida sobre una pose inventada sin saberlo.
            self.get_logger().warn(
                f"{len(provisionales)} puntos son PROVISIONALES y no valen para "
                f"la campana de OE4: {', '.join(provisionales)}")
        return puntos

    def _a_msg(self, p):
        m = PuntoInteres()
        m.id, m.nombre, m.nivel = p["id"], p["nombre"], int(p["nivel"])
        m.es_transferencia = bool(p.get("es_transferencia", False))
        m.pose.position.x = float(p["pose"]["x"])
        m.pose.position.y = float(p["pose"]["y"])
        _, _, z, w = yaw_a_cuaternion(float(p["pose"].get("yaw", 0.0)))
        m.pose.orientation.z, m.pose.orientation.w = z, w
        return m

    def _publicar_catalogo(self):
        lista = ListaPuntosInteres()
        lista.origen = self.ruta_puntos
        lista.stamp = self.get_clock().now().to_msg()
        lista.puntos = [self._a_msg(p) for p in self.catalogo]
        self.pub_puntos.publish(lista)

    def _publicar_estado(self):
        self.pub_mision.publish(self.estado)

    # ----------------------------------------------------------------- mision

    def _ejecutar(self, goal_handle):
        pet = goal_handle.request
        # t0 es t_solicitud del §3.1: el instante en que el servidor ACEPTA el
        # goal, no en que la HRI lo envia. La latencia del navegador no es del
        # sistema robotico y no se puede medir desde dentro.
        #
        # Sale de _ahora(), o sea del reloj del NODO: con use_sim_time es el
        # mismo /clock que sella el bag. time.time() lo ignora, y con RTF >= 0,99
        # las dos formas difieren hasta un 1 %: sobre t_respuesta eso no es
        # ruido, es sesgo. Ver §3 del protocolo.
        t0 = self._ahora()
        condicion = condicion_de(self.catalogo, pet.origen_id, pet.destino_id)
        mision_id = generar_mision_id(
            self.prefijo_mision, condicion, datetime.datetime.now())
        # Se fijan una vez y no cambian en toda la mision. El destino ACTUAL si
        # cambia, y lo pone _marcar; estos dos son lo que se pidio.
        self.estado.origen_id = pet.origen_id
        self.estado.destino_id = pet.destino_id
        res = GuiarUsuario.Result()

        self.registro = RegistroMision(
            mision_id, pet.origen_id, pet.destino_id,
            {str(k): v for k, v in self.asignacion.items()},
            t_solicitud=t0, condicion=self.condicion) if self.ruta_registros else None

        # Cualquier confirmacion anterior deja de valer: si no, una pulsacion
        # tardia de la mision pasada arrancaria el tramo 2 de esta sin preguntar.
        self.enganche.reiniciar(mision_id)

        self.get_logger().info(
            f"Mision: {pet.origen_id} -> {pet.destino_id}")

        # AQUI empieza a contar el tiempo de asignacion. Se publica ANTES de
        # planificar y con robot_activo todavia vacio: es el unico instante en
        # que el sistema sabe que hay una solicitud y aun no sabe a quien se la
        # dara. Hasta el 2026-08-29 esta publicacion no existia -_marcar fijaba
        # etapa y agente en la misma llamada- y las dos marcas de la §3.5 caian
        # en el mismo mensaje, con lo que el tiempo de asignacion, que es una de
        # las cuatro metricas de OE4, valia cero se ejecutara lo que se
        # ejecutara. Lo destapo el primer piloto de RF-25.
        self._marcar(RECIBIDA, "", None,
                     "Recibida la solicitud; asignando el robot.", mision_id)
        self._feedback(goal_handle)

        try:
            tramos, relevos = planificar(
                self.catalogo, pet.origen_id, pet.destino_id, self.asignacion)
        except ErrorPlanificacion as e:
            # Falla antes de mover un solo robot, y el motivo ya viene redactado.
            self.get_logger().error(f"No se puede planificar: {e}")
            self._marcar(FALLIDA, "", None, str(e), mision_id)
            goal_handle.abort()
            res.exito, res.motivo_fallo = False, str(e)
            res.tiempo_total_s = self._ahora() - t0
            return self._cerrar_registro(res, None)

        try:
            for i, tramo in enumerate(tramos, 1):
                if goal_handle.is_cancel_requested:
                    raise _Cancelada(tramo.robot)

                self._marcar(tramo.etapa, tramo.robot, tramo.punto,
                             tramo.mensaje_usuario, mision_id)
                self._feedback(goal_handle)
                self.get_logger().info(
                    f"  tramo {i}/{len(tramos)}: {tramo.robot} -> {tramo.punto['id']}")

                ok, motivo = self._navegar(tramo.robot, tramo.punto, goal_handle)
                if not ok:
                    self.get_logger().error(f"  tramo {i} fallo: {motivo}")
                    self._marcar(FALLIDA, tramo.robot, tramo.punto,
                                 f"No se pudo completar el trayecto: {motivo}",
                                 mision_id)
                    self._feedback(goal_handle)
                    goal_handle.abort()
                    res.exito, res.motivo_fallo = False, motivo
                    res.tiempo_total_s = self._ahora() - t0
                    res.num_relevos = relevos
                    return self._cerrar_registro(res, tramo.punto)

                # RF-28. Terminado el tramo de TRANSFERENCIA el robot del piso de
                # destino ya esta en su escalera, pero el usuario puede no haber
                # subido todavia. Sin esta pausa el tramo 2 arrancaba solo y la
                # mision podia completarse con el usuario en el otro piso.
                if tramo.etapa == TRANSFERENCIA:
                    ok, motivo = self._esperar_confirmacion(
                        tramo, goal_handle, mision_id)
                    if not ok:
                        self._marcar(FALLIDA, tramo.robot, tramo.punto,
                                     f"Mision detenida: {motivo}", mision_id)
                        self._feedback(goal_handle)
                        goal_handle.abort()
                        res.exito, res.motivo_fallo = False, motivo
                        res.tiempo_total_s = self._ahora() - t0
                        res.num_relevos = relevos
                        return self._cerrar_registro(res, tramo.punto)
        except _Cancelada as c:
            res.num_relevos = relevos
            return self._cancelar_e_ir_a_casa(c.robot, mision_id, res, t0, goal_handle)

        destino = next(p for p in self.catalogo if p["id"] == pet.destino_id)
        self._marcar(COMPLETADA, tramos[-1].robot, destino,
                     f"Ha llegado a {destino['nombre']}.", mision_id)
        self._feedback(goal_handle)
        goal_handle.succeed()
        res.exito = True
        res.tiempo_total_s = self._ahora() - t0
        res.num_relevos = relevos
        res.motivo_fallo = ""
        return self._cerrar_registro(res, destino)

    def _cerrar_registro(self, res, punto):
        """Cierra el registro de la mision y lo escribe. Devuelve 'res' tal cual.

        Va en TODAS las salidas de _ejecutar, incluidas las de fallo y
        cancelacion, y a proposito: una campana que solo guarda las misiones que
        salieron bien no puede calcular una tasa de exito. El §8 del protocolo
        dice que una corrida fallida cuenta como fallo salvo que su causa este
        en la lista cerrada de descartes, y para poder decidir eso hace falta el
        archivo.

        Por lo mismo, el desenlace se ANOTA aqui y no en cada salida de
        _ejecutar. Hasta el 2026-09-10 solo lo anotaba la salida de exito, y
        una mision muerta por plazo agotado dejaba la consola muda: la ultima
        linea era la alerta de los 60 s, de modo que quien operaba no podia
        distinguir una mision todavia viva de una ya terminada. Esta funcion es
        el unico punto por el que pasan TODAS las salidas, asi que es el unico
        donde el desenlace no se puede olvidar al agregar una salida nueva.
        """
        if res.exito:
            self.get_logger().info(
                f"Mision completada en {res.tiempo_total_s:.1f} s, "
                f"{res.num_relevos} relevo(s)")
        else:
            self.get_logger().warning(
                f"Mision terminada SIN exito tras {res.tiempo_total_s:.1f} s: "
                f"{res.motivo_fallo}")
        if self.registro is None:
            return res
        try:
            self.registro.cerrar(
                self._ahora(), res.exito, res.motivo_fallo, res.num_relevos,
                punto["pose"] if punto else {"x": 0.0, "y": 0.0, "yaw": 0.0})
            self.registro.entorno = entorno_simulacion(
                mundo=None, mapa=None, rtf=None,
                controladores={})   # los rellena quien lance la campana
            ruta = self.registro.guardar(self.ruta_registros)
            self.get_logger().info(f"Registro de mision escrito: {ruta}")
        except Exception as e:                      # noqa: BLE001
            # Que falle el registro NO puede tumbar una mision: el registrador
            # observa, no manda.
            self.get_logger().error(f"No se pudo escribir el registro: {e}")
        finally:
            self.registro = None
        return res

    def _cancelar_solicitado(self, goal_handle):
        """Acepta toda peticion de cancelacion (RF-29, boton Cancelar de la HRI).

        Antes de esto no habia ningun cancel_callback registrado, y el
        ActionServer de rclpy rechaza por omision (CancelResponse.REJECT):
        'is_cancel_requested' de _ejecutar nunca llegaba a valer True, pese a
        que ya lo comprobaba en tres sitios. La cancelacion en si no ocurre
        aqui -este metodo solo abre la puerta-: quien la ejecuta de verdad es
        _ejecutar, al ver 'is_cancel_requested' en su siguiente comprobacion.
        """
        del goal_handle  # no se usa: se acepta cualquier cancelacion en curso
        return CancelResponse.ACCEPT

    def _punto_home(self, robot):
        """La escalera del nivel que atiende 'robot': su posicion de reposo.

        Es la unica pose con sentido para "cancelar y volver": esta en el
        catalogo -no hay que inventar una pose nueva-, y es exactamente donde
        ese robot ya estaria si la mision nunca hubiera arrancado.
        """
        nivel = next((n for n, r in self.asignacion.items() if r == robot), None)
        return next((p for p in self.catalogo
                     if p.get("nivel") == nivel and p.get("es_transferencia")), None)

    def _limpiar_costmaps(self, robot):
        """Vacia los dos costmaps de 'robot'. Ver la nota de 'clientes_costmap'.

        Best-effort: si el servicio no responde a tiempo -o no existe, porque
        Nav2 de ese robot no llegara a arrancar del todo en algun escenario de
        prueba-, se registra y se continua. Un costmap sucio en el peor caso
        hace que el intento de vuelta a casa falle igual que antes de este
        arreglo; no limpiarlo nunca es peor que el estado de partida.
        """
        for capa, cliente in self.clientes_costmap[robot].items():
            if not cliente.wait_for_service(timeout_sec=2.0):
                self.get_logger().warn(
                    f"    costmap {capa} de {robot} no respondio; se intenta "
                    f"la vuelta a casa igual")
                continue
            self._esperar(cliente.call_async(ClearEntireCostmap.Request()), timeout=3.0)

    def _cancelar_e_ir_a_casa(self, robot, mision_id, res, t0, goal_handle):
        """El usuario canceló: 'robot' vuelve a su escalera antes de cerrar.

        No se le deja donde iba a mitad de tramo -eso bloquearia el pasillo y,
        si el usuario pide otra mision, el robot arrancaria desde un sitio que
        no esta en el catalogo-. La vuelta usa la misma _navegar de siempre,
        sin 'goal_handle': esta segunda cancelacion no se vigila, para no
        encadenar cancelaciones sobre la propia cancelacion.
        """
        casa = self._punto_home(robot) if robot else None
        if casa is not None:
            self._marcar(CANCELANDO, robot, casa,
                         "Cancelando: el robot vuelve a las escaleras.", mision_id)
            self._feedback(goal_handle)
            self.get_logger().info(f"  cancelada: {robot} vuelve a '{casa['id']}'")
            # MEDIDO EL 2026-09-13: cancelar a mitad de una cuspide de Hybrid-A*
            # -el giro en tres puntos que R12 ya documento en las esquinas del
            # pasillo- puede parar al robot en una pose donde su propio costmap
            # local lo ve pegado a la pared un instante. Un solo intento fallaba
            # con "Starting point in lethal space" incluso limpiando antes; tres
            # intentos con una pausa entre cada uno le dan tiempo al costmap a
            # asentarse. Si los tres fallan, es un atasco real y no uno
            # transitorio, y se informa tal cual en vez de reintentar para siempre.
            intentos = 3
            for intento in range(1, intentos + 1):
                self._limpiar_costmaps(robot)
                ok, motivo = self._navegar(robot, casa)
                if ok:
                    break
                self.get_logger().warn(
                    f"    vuelta a casa, intento {intento}/{intentos} fallo: {motivo}")
                if intento < intentos:
                    time.sleep(1.0)
            if not ok:
                # No hay mas remedio que decirlo tal cual: el robot no llego a
                # casa y no hay una segunda posicion de reposo que ofrecer.
                self.get_logger().error(f"  no volvio a casa tras {intentos} intentos: {motivo}")

        self._marcar(FALLIDA, robot, casa,
                     "Misión cancelada por el usuario.", mision_id)
        self._feedback(goal_handle)
        goal_handle.canceled()
        res.exito, res.motivo_fallo = False, "Cancelada por el usuario"
        res.tiempo_total_s = self._ahora() - t0
        return self._cerrar_registro(res, casa)

    def _ahora(self):
        """Segundos del reloj del NODO, no de pared.

        Con use_sim_time:=true esto sale de /clock, que es lo que exige el §3
        del protocolo: todas las marcas del mismo reloj. Aqui habia time.time(),
        y con el simulador corriendo a RTF distinto de 1 eso produce metricas
        sesgadas sin dar ningun error -que es el peor tipo de error que puede
        tener un instrumento de medida-.
        """
        return self.get_clock().now().nanoseconds / 1e9

    def _odom(self, msg, ns):
        """Ultima pose de cada robot, y muestra para la traza si hay mision."""
        self.ultimo_odom[ns] = msg
        if self.registro is None:
            return
        v = msg.twist.twist.linear
        q = msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        pos = msg.pose.pose.position
        self.registro.muestra(self._ahora(), ns, pos.x, pos.y, pos.z,
                              math.hypot(v.x, v.y), yaw)

    def _confirmacion(self, msg):
        """El usuario dice que ya cambio de piso (RF-28)."""
        self.enganche.recibir(msg.data)
        self.get_logger().info(f"confirmacion de piso recibida: '{msg.data}'")

    def _marcar(self, etapa, robot, punto, mensaje, mision_id):
        self.estado.mision_id = mision_id
        self.estado.etapa = etapa
        self.estado.robot_activo = robot
        self.estado.destino_actual = self._a_msg(punto) if punto else PuntoInteres()
        self.estado.mensaje_usuario = mensaje
        self.estado.distancia_restante = self._distancia(robot, punto) if punto else 0.0
        # PUBLICACION EXTRAORDINARIA, en el instante del cambio y no en el
        # siguiente tick. Lo pide el §3.2 del protocolo y no es un detalle:
        # 'estado_mision' va a 1 Hz, asi que sin esto t_asignacion -que se
        # espera en milisegundos- tendria resolucion de un segundo, y la
        # metrica no distinguiria una asignacion instantanea de una que tardo
        # medio segundo. El latido de 1 Hz sigue vivo para la HRI.
        #
        # UNA sola publicacion, y aqui hubo que elegir: la fusion del
        # 2026-08-30 dejo por un momento este publish MAS una llamada a
        # _publicar_estado(), que hace exactamente lo mismo. Cada cambio de
        # etapa habria salido dos veces al bag y el conteo de transiciones de
        # la campana habria salido al doble sin dar ningun error.
        self._publicar_estado()
        if self.registro is not None:
            self.registro.marca(self._ahora(), etapa, robot,
                                punto["id"] if punto else None)

    def _feedback(self, goal_handle):
        fb = GuiarUsuario.Feedback()
        fb.estado = self.estado
        goal_handle.publish_feedback(fb)

    def _distancia(self, robot, punto):
        od = self.ultimo_odom.get(robot)
        if od is None:
            return float("nan")
        return math.hypot(od.pose.pose.position.x - float(punto["pose"]["x"]),
                          od.pose.pose.position.y - float(punto["pose"]["y"]))

    # ------------------------------------------------------------- navegacion

    def _yaw_de_llegada(self, robot, punto):
        """Elige el rumbo con el que pedir la llegada: el del catalogo o el opuesto.

        POR QUE ESTO EXISTE. El 2026-08-26, yendo de ETM10 a ETM1, el robot dio
        media vuelta al llegar y se quedo pegado a la puerta. La causa NO es el
        comprobador de meta: ese ya esta relajado desde R12 (yaw_goal_tolerance
        3.15, o sea cualquier rumbo). La causa es el planificador, que es
        SmacPlannerHybrid: Hybrid-A* busca en SE(2), no busca un punto sino una
        POSE, y con motion_model REEDS_SHEPP tiene primitivas de marcha atras
        para conseguir el rumbo pedido. La maniobra viene cosida DENTRO del
        camino, asi que el robot no entra en los 0.25 m hasta haberla terminado
        y el comprobador ni llega a opinar. Se confirmo en el bag: el plan del
        tramo 2 termina en (-15.93, 10.61) con yaw final 0.0 grados yendo hacia
        el OESTE.

        En Nav2 de Jazzy esto se arregla con goal_heading_mode: BIDIRECTIONAL,
        pero ese parametro no existe en Humble, que es lo que corre el PC. Y
        cambiar a un planificador 2D no es opcion: ignoraria tambien el radio
        minimo de giro de 0.35 m, que es justo por lo que se puso el Hybrid.

        QUE HACE. Un carro puede ocupar el mismo sitio fisico en dos sentidos.
        Se eligen los dos candidatos del eje que puso el humano en el YAML
        -yaw y yaw+pi- y se coge el mas cercano al rumbo de aproximacion real,
        medido con /odom. Elegir entre esos dos NUNCA anade una maniobra: solo
        puede quitarla. No se usa el rumbo de aproximacion crudo porque en una
        ruta en L la recta origen-destino puede ser diagonal y acabariamos
        pidiendo un rumbo que tampoco es el de llegada.

        Contexto que justifica no respetar el YAML a rajatabla: de los 31 puntos
        del catalogo, 28 tienen yaw: 0.0. Ese valor no lo eligio nadie, es el
        que quedo por defecto. Para los puntos donde la orientacion SI signifique
        algo -las escaleras, donde el robot deberia quedar senalando por donde
        sube el usuario- se respeta el YAML poniendoles yaw_estricto: true.
        """
        yaml_yaw = float(punto["pose"].get("yaw", 0.0))
        if punto.get("yaw_estricto", False):
            return yaml_yaw, "yaw_estricto en el catalogo"

        od = self.ultimo_odom.get(robot)
        if od is None:
            return yaml_yaw, "sin /odom, no se puede medir la aproximacion"

        dx = float(punto["pose"]["x"]) - od.pose.pose.position.x
        dy = float(punto["pose"]["y"]) - od.pose.pose.position.y
        if math.hypot(dx, dy) < TOLERANCIA_LLEGADA_M:
            # Demasiado cerca: el rumbo de aproximacion es ruido.
            return yaml_yaw, "el robot ya esta sobre el punto"

        rumbo = math.atan2(dy, dx)
        opuesto = _normalizar(yaml_yaw + math.pi)
        if abs(_normalizar(rumbo - yaml_yaw)) <= abs(_normalizar(rumbo - opuesto)):
            return yaml_yaw, f"rumbo de aproximacion {math.degrees(rumbo):.0f} grados"
        return opuesto, f"rumbo de aproximacion {math.degrees(rumbo):.0f} grados"

    def _navegar(self, robot, punto, goal_handle=None):
        """Manda un goal a 'robot' hacia 'punto' y espera. Devuelve (ok, motivo).

        LA LLEGADA SE COMPRUEBA CONTRA /odom, NO CONTRA EL SUCCEEDED de Nav2.
        Es la regla del 2026-08-12 y no es formalismo: Nav2 devuelve SUCCEEDED en
        cuanto su controlador se da por satisfecho, y el 2026-08-24 se midio una
        llegada con 0,190 m de error real que habria pasado igual. Un goal de
        cero metros tambien devuelve SUCCEEDED al instante. Si el SUCCEEDED y el
        /odom no coinciden, manda el /odom.

        'goal_handle', si se pasa, es el goal de arriba (GuiarUsuario). Se vigila
        mientras Nav2 responde: si el usuario cancela a mitad de un tramo, el
        sub-goal de Nav2 se cancela con el -dejarlo navegando solo, sin que
        nadie lo vigile, es peor que la demora de pararlo-, y este metodo
        levanta _Cancelada para que _ejecutar mande al robot de vuelta a casa.
        Se pasa None para la propia vuelta a casa: esa no se vuelve a cancelar.
        """
        cliente = self.clientes[robot]
        if not cliente.wait_for_server(timeout_sec=self.espera_servidor):
            return False, (
                f"El robot '{robot}' no ofrece navigate_to_pose despues de "
                f"{self.espera_servidor:.0f} s. Si el robot esta vivo, sospechar "
                f"del desajuste Humble/Jazzy descrito en la cabecera de este "
                f"archivo")

        objetivo = NavigateToPose.Goal()
        objetivo.pose = PoseStamped()
        # El §3 del contrato: todos los marcos llevan el prefijo del namespace,
        # incluido map. Son dos arboles TF desconectados a proposito.
        objetivo.pose.header.frame_id = f"{robot}/map"
        objetivo.pose.header.stamp = self.get_clock().now().to_msg()
        objetivo.pose.pose = self._a_msg(punto).pose

        # El punto (x, y) es sagrado; el rumbo no. Ver _yaw_de_llegada.
        yaw, motivo_yaw = self._yaw_de_llegada(robot, punto)
        _, _, qz, qw = yaw_a_cuaternion(yaw)
        objetivo.pose.pose.orientation.z, objetivo.pose.pose.orientation.w = qz, qw
        yaml_yaw = float(punto["pose"].get("yaw", 0.0))
        if abs(_normalizar(yaw - yaml_yaw)) > 1e-6:
            self.get_logger().info(
                f"    rumbo de llegada invertido respecto al catalogo: "
                f"{math.degrees(yaml_yaw):.0f} -> {math.degrees(yaw):.0f} grados "
                f"({motivo_yaw}). Evita la media vuelta de Hybrid-A*")

        fut = cliente.send_goal_async(objetivo)
        gh = self._esperar(fut)
        if gh is None:
            return False, "Nav2 no respondio al envio del goal"
        if not gh.accepted:
            return False, f"'{robot}' rechazo el goal"

        resultado = self._esperar_resultado_nav2(gh, goal_handle, robot)
        if resultado is None:
            return False, "Nav2 no devolvio resultado"

        if resultado.status != GoalStatus.STATUS_SUCCEEDED:
            return False, f"Nav2 termino con estado {resultado.status}"

        # Y ahora la comprobacion que de verdad decide.
        d = self._distancia(robot, punto)
        if math.isnan(d):
            return False, (
                f"'{robot}' dijo SUCCEEDED pero no publica /odom, asi que "
                f"la llegada no se puede verificar. No se acepta")
        if d > TOLERANCIA_LLEGADA_M:
            return False, (
                f"'{robot}' dijo SUCCEEDED pero /odom lo situa a "
                f"{d:.3f} m del punto, por encima de los "
                f"{TOLERANCIA_LLEGADA_M} m de tolerancia")
        self.get_logger().info(f"    llegada verificada contra /odom: {d:.3f} m")
        return True, ""

    def _esperar_resultado_nav2(self, gh_nav2, goal_handle_top, robot):
        """Como _esperar(), pero ademas vigila la cancelacion del goal de arriba.

        Sin timeout, igual que antes de esto: una navegacion legitima puede
        tardar y no hay plazo que ponerle. 'goal_handle_top' en None -la vuelta
        a casa- se comporta exactamente como el _esperar() de siempre.

        MEDIDO EL 2026-09-13: cancelar el sub-goal y mandar el de vuelta a casa
        de inmediato -sin esperar a que Nav2 terminara de procesar la
        cancelacion- hacia que el segundo goal abortara solo (estado 6),
        porque el controller_server todavia estaba desmontando el plan
        anterior. Por eso aqui se espera DOS veces: a que el cancel_goal_async
        se confirme, y despues a que el propio 'fut' del sub-goal cancelado
        efectivamente termine -recien entonces Nav2 queda libre para un goal
        nuevo-.
        """
        fut = gh_nav2.get_result_async()
        while not fut.done():
            if goal_handle_top is not None and goal_handle_top.is_cancel_requested:
                self._esperar(gh_nav2.cancel_goal_async(), timeout=5.0)
                self._esperar(fut, timeout=5.0)
                raise _Cancelada(robot)
            time.sleep(0.05)
        return fut.result()

    def _esperar_confirmacion(self, tramo, goal_handle, mision_id):
        """La pausa de RF-28: el tramo 2 no arranca sin el visto bueno del usuario.

        Devuelve (True, "") si el usuario confirmo, y (False, motivo) si se
        agoto el plazo o se cancelo la mision.

        El robot que espera es el del piso de DESTINO -el tramo de
        TRANSFERENCIA ya es suyo, porque mientras el usuario sube el conduce
        hasta su escalera-, y se publica en 'robot_activo' siempre lleno: con
        ese campo vacio la continuidad del RF-24 se vuelve falsa en toda mision
        entre niveles.
        """
        nivel = tramo.punto.get("nivel", "")
        if self.enganche.consumir(mision_id):
            self.get_logger().info(
                "    el usuario ya habia confirmado antes de que el robot "
                "llegara: se sigue sin esperar")
            return True, ""

        self._marcar(ESPERANDO_CONFIRMACION, tramo.robot, tramo.punto,
                     f"¿Ya esta en el piso {nivel}? Confirmelo para continuar.",
                     mision_id)
        self._feedback(goal_handle)
        self.get_logger().info(
            f"    esperando confirmacion del usuario (alerta a {ALERTA_S:.0f} s, "
            f"plazo {PLAZO_S:.0f} s)")

        # time.time() y no self._ahora(): ver el docstring de _esperar y la §4
        # del diseno. El plazo es de paciencia humana, y si Gazebo muere /clock
        # se para y un plazo en tiempo de simulacion no venceria nunca.
        t0 = time.time()
        avisado = False
        while True:
            if goal_handle.is_cancel_requested:
                # Hasta que _cancelar_solicitado registro un cancel_callback,
                # esto era inerte -rclpy rechaza toda cancelacion por
                # omision- y este 'if' nunca se ejecutaba. El robot ya esta en
                # su propia escalera en esta etapa (es el destino de
                # TRANSFERENCIA), asi que _cancelar_e_ir_a_casa no tiene que
                # moverlo: solo cierra la mision.
                raise _Cancelada(tramo.robot)

            if self.enganche.consumir(mision_id):
                espera = time.time() - t0
                self.get_logger().info(
                    f"    confirmado por el usuario tras {espera:.1f} s")
                return True, ""

            estado = fase(time.time() - t0)
            if estado == "agotada":
                return False, (
                    f"el usuario no confirmo la llegada al piso {nivel} en "
                    f"{PLAZO_S:.0f} s")
            if estado == "alerta" and not avisado:
                # UNA sola vez, no en cada vuelta del bucle: a 20 Hz serian
                # 1200 marcas por minuto en el bag y el conteo de transiciones
                # dejaria de significar nada.
                avisado = True
                restante = PLAZO_S - ALERTA_S
                self._marcar(
                    ESPERANDO_CONFIRMACION, tramo.robot, tramo.punto,
                    f"Seguimos esperando su confirmacion. Quedan "
                    f"{restante:.0f} segundos.", mision_id)
                self._feedback(goal_handle)
                self.get_logger().warn(
                    f"    alerta: {ALERTA_S:.0f} s sin confirmacion")

            time.sleep(0.05)

    def _esperar(self, futuro, timeout=120.0):
        """Espera un futuro sin bloquear el executor (es multihilo).

        AQUI SI se usa time.time() y no self._ahora(), a proposito. Este timeout
        es un perro guardian contra un proceso colgado, no una marca temporal de
        ninguna metrica. Si se midiera con el reloj de simulacion y Gazebo
        muriera, /clock se detendria y el timeout NO venceria nunca: el
        coordinador se quedaria esperando para siempre justo en el caso para el
        que existe. Las marcas de las metricas van todas por self._ahora().
        """
        t0 = time.time()
        while not futuro.done():
            if timeout is not None and time.time() - t0 > timeout:
                return None
            time.sleep(0.05)
        return futuro.result()


def _ya_hay_coordinador(espera_s):
    """¿Hay ya alguien sirviendo /coordinacion/guiar_usuario?

    EL FALLO QUE ESTO IMPIDE, medido el 2026-09-04. Ese dia se perdio la campana
    de OE4 con dos misiones caidas en 'Nav2 termino con estado 6'. El estado 6 es
    ABORTED, y no lo causo Nav2: 20 goals directos en limpio dieron 0 abortos,
    mientras que 8 pares de goals seguidos al mismo servidor dieron 8 abortos del
    goal desplazado, entre 9 y 13 ms. navigate_to_pose atiende un goal a la vez y
    al desplazado lo termina en ABORTED. Aquel dia habia dos coordinadores vivos
    -lo dejo escrito ROS 2 con 'There may be more than one action server'- y cada
    uno mandaba el suyo al mismo Nav2.

    Se sondea ANTES de construir el nodo, no dentro, para que el que llega tarde
    no alcance a publicar su catalogo retenido ni a montar un segundo servidor.

    LIMITACION, y conviene saberla: esto ve al que ya esta sirviendo, no al que
    arranca en el mismo instante. Cubre el caso real -lanzar uno con otro vivo-,
    no una carrera de dos arranques simultaneos.

    wait_for_server no necesita girar el nodo: consulta el grafo.
    """
    nodo = rclpy.create_node("guardian_coordinador")
    try:
        cliente = ActionClient(nodo, GuiarUsuario, "/coordinacion/guiar_usuario")
        try:
            return cliente.wait_for_server(timeout_sec=espera_s)
        finally:
            cliente.destroy()
    finally:
        nodo.destroy_node()


def main(args=None):
    rclpy.init(args=args)

    # Segundos que se le dan al descubrimiento para delatar a un coordinador
    # anterior. En 0 el guardian queda desactivado.
    sonda = rclpy.create_node("guardian_parametros")
    sonda.declare_parameter("espera_guardian_s", 3.0)
    espera_guardian = float(sonda.get_parameter("espera_guardian_s").value)
    sonda.destroy_node()

    if espera_guardian > 0.0 and _ya_hay_coordinador(espera_guardian):
        print(
            "GUARDIAN: ya hay un coordinador sirviendo /coordinacion/guiar_usuario.\n"
            "\n"
            "No se arranca un segundo. Dos coordinadores mandan sus goals al mismo\n"
            "navigate_to_pose, que atiende uno a la vez, y el desplazado vuelve como\n"
            "ABORTED: es el 'Nav2 termino con estado 6' que costo la campana del\n"
            "2026-09-04.\n"
            "\n"
            "Para al anterior y vuelve a intentarlo:\n"
            "    pkill -f \"coordinacion[/]coordinador\"\n"
            "\n"
            "El patron va con BARRA, no con espacio. 'ros2 run' hace exec a la ruta\n"
            "instalada, asi que el proceso vivo se llama\n"
            "'.../lib/coordinacion/coordinador --ros-args ...': un patron con espacio\n"
            "no encuentra nada y parece que ya no hay nadie. Asi sobrevivio el\n"
            "coordinador de las 14:10 del 2026-09-04.\n"
            "\n"
            "Y los corchetes tampoco sobran: sin ellos pkill encuentra la propia\n"
            "orden que lo invoca y se mata a si mismo.",
            file=sys.stderr)
        rclpy.shutdown()
        return 1

    nodo = Coordinador()
    ejecutor = rclpy.executors.MultiThreadedExecutor()
    ejecutor.add_node(nodo)
    try:
        ejecutor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
