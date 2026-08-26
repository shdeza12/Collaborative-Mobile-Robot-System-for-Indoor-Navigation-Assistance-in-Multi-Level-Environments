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
    /<ns>/navigate_to_pose         accion de Nav2          (la llama)

UN AVISO QUE NO ES TEORICO. El §2 del contrato quedo refutado el 2026-08-18:
nav2_msgs/NavigateToPose CAMBIA de definicion entre Humble y Jazzy -en Humble el
result es std_msgs/Empty, en Jazzy lleva error_code y error_msg-. Este nodo, por
tanto, NO puede mandar a la vez a un robot simulado (Humble) y a uno fisico
(Jazzy): el cliente de accion simplemente no encontrara servidor, y sin mensaje
de error. El mismo codigo fuente sirve para los dos destinos, pero no a la vez.
Si un tramo se queda esperando servidor para siempre, mirar esto primero.
"""

import math
import os
import time

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient, ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile

from coordinacion_msgs.action import GuiarUsuario
from coordinacion_msgs.msg import EstadoMision, ListaPuntosInteres, PuntoInteres
from coordinacion.registrador import RegistroMision, entorno_simulacion

from coordinacion.planificador import (
    ASIGNACION_POR_DEFECTO, COMPLETADA, ErrorPlanificacion, FALLIDA, INACTIVA,
    planificar, yaw_a_cuaternion,
)

# Tolerancia de llegada. Es la misma que xy_goal_tolerance de Nav2 y la que fija
# el §5 de PROTOCOLO_EXPERIMENTAL.md como criterio de exito. No inventar otra
# aqui: si se cambia, se cambia en el protocolo primero.
TOLERANCIA_LLEGADA_M = 0.25


class Coordinador(Node):

    def __init__(self):
        super().__init__("coordinador")

        self.declare_parameter("ruta_puntos", "")
        self.declare_parameter("robot_nivel_1", ASIGNACION_POR_DEFECTO[1])
        self.declare_parameter("robot_nivel_2", ASIGNACION_POR_DEFECTO[2])
        self.declare_parameter("espera_servidor_s", 20.0)
        # RF-25. Carpeta vacia = no registrar, para poder usar el
        # coordinador en una demostracion sin ensuciar el disco.
        self.declare_parameter("ruta_registros", "")
        self.declare_parameter("condicion", "simulacion")

        self.asignacion = {
            1: self.get_parameter("robot_nivel_1").value,
            2: self.get_parameter("robot_nivel_2").value,
        }
        self.espera_servidor = self.get_parameter("espera_servidor_s").value
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

        self.servidor = ActionServer(
            self, GuiarUsuario, "/coordinacion/guiar_usuario",
            execute_callback=self._ejecutar, callback_group=self.grupo)

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
        t0 = self._ahora()
        res = GuiarUsuario.Result()

        mision_id = f"{pet.origen_id}__{pet.destino_id}__{int(t0 * 1000)}"
        self.registro = RegistroMision(
            mision_id, pet.origen_id, pet.destino_id,
            {str(k): v for k, v in self.asignacion.items()},
            t_solicitud=t0, condicion=self.condicion) if self.ruta_registros else None

        self.get_logger().info(
            f"Mision: {pet.origen_id} -> {pet.destino_id}")

        try:
            tramos, relevos = planificar(
                self.catalogo, pet.origen_id, pet.destino_id, self.asignacion)
        except ErrorPlanificacion as e:
            # Falla antes de mover un solo robot, y el motivo ya viene redactado.
            self.get_logger().error(f"No se puede planificar: {e}")
            self._marcar(FALLIDA, "", None, str(e), pet.origen_id)
            goal_handle.abort()
            res.exito, res.motivo_fallo = False, str(e)
            res.tiempo_total_s = self._ahora() - t0
            return self._cerrar_registro(res, None)

        for i, tramo in enumerate(tramos, 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                res.exito, res.motivo_fallo = False, "Cancelada por el usuario"
                res.tiempo_total_s = self._ahora() - t0
                return self._cerrar_registro(res, tramos[-1].punto)

            self._marcar(tramo.etapa, tramo.robot, tramo.punto,
                         tramo.mensaje_usuario, pet.origen_id)
            self._feedback(goal_handle)
            self.get_logger().info(
                f"  tramo {i}/{len(tramos)}: {tramo.robot} -> {tramo.punto['id']}")

            ok, motivo = self._navegar(tramo)
            if not ok:
                self.get_logger().error(f"  tramo {i} fallo: {motivo}")
                self._marcar(FALLIDA, tramo.robot, tramo.punto,
                             f"No se pudo completar el trayecto: {motivo}",
                             pet.origen_id)
                self._feedback(goal_handle)
                goal_handle.abort()
                res.exito, res.motivo_fallo = False, motivo
                res.tiempo_total_s = self._ahora() - t0
                res.num_relevos = relevos
                return self._cerrar_registro(res, tramo.punto)

        destino = next(p for p in self.catalogo if p["id"] == pet.destino_id)
        self._marcar(COMPLETADA, tramos[-1].robot, destino,
                     f"Ha llegado a {destino['nombre']}.", pet.origen_id)
        self._feedback(goal_handle)
        goal_handle.succeed()
        res.exito = True
        res.tiempo_total_s = self._ahora() - t0
        res.num_relevos = relevos
        res.motivo_fallo = ""
        self.get_logger().info(
            f"Mision completada en {res.tiempo_total_s:.1f} s, "
            f"{relevos} relevo(s)")
        return self._cerrar_registro(res, destino)

    def _cerrar_registro(self, res, punto):
        """Cierra el registro de la mision y lo escribe. Devuelve 'res' tal cual.

        Va en TODAS las salidas de _ejecutar, incluidas las de fallo y
        cancelacion, y a proposito: una campana que solo guarda las misiones que
        salieron bien no puede calcular una tasa de exito. El §8 del protocolo
        dice que una corrida fallida cuenta como fallo salvo que su causa este
        en la lista cerrada de descartes, y para poder decidir eso hace falta el
        archivo.
        """
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
        # medio segundo.
        self.pub_mision.publish(self.estado)
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

    def _navegar(self, tramo):
        """Manda un goal y espera. Devuelve (ok, motivo).

        LA LLEGADA SE COMPRUEBA CONTRA /odom, NO CONTRA EL SUCCEEDED de Nav2.
        Es la regla del 2026-08-12 y no es formalismo: Nav2 devuelve SUCCEEDED en
        cuanto su controlador se da por satisfecho, y el 2026-08-24 se midio una
        llegada con 0,190 m de error real que habria pasado igual. Un goal de
        cero metros tambien devuelve SUCCEEDED al instante. Si el SUCCEEDED y el
        /odom no coinciden, manda el /odom.
        """
        cliente = self.clientes[tramo.robot]
        if not cliente.wait_for_server(timeout_sec=self.espera_servidor):
            return False, (
                f"El robot '{tramo.robot}' no ofrece navigate_to_pose despues de "
                f"{self.espera_servidor:.0f} s. Si el robot esta vivo, sospechar "
                f"del desajuste Humble/Jazzy descrito en la cabecera de este "
                f"archivo")

        objetivo = NavigateToPose.Goal()
        objetivo.pose = PoseStamped()
        # El §3 del contrato: todos los marcos llevan el prefijo del namespace,
        # incluido map. Son dos arboles TF desconectados a proposito.
        objetivo.pose.header.frame_id = f"{tramo.robot}/map"
        objetivo.pose.header.stamp = self.get_clock().now().to_msg()
        objetivo.pose.pose = self._a_msg(tramo.punto).pose

        fut = cliente.send_goal_async(objetivo)
        gh = self._esperar(fut)
        if gh is None:
            return False, "Nav2 no respondio al envio del goal"
        if not gh.accepted:
            return False, f"'{tramo.robot}' rechazo el goal"

        resultado = self._esperar(gh.get_result_async(), timeout=None)
        if resultado is None:
            return False, "Nav2 no devolvio resultado"

        if resultado.status != GoalStatus.STATUS_SUCCEEDED:
            return False, f"Nav2 termino con estado {resultado.status}"

        # Y ahora la comprobacion que de verdad decide.
        d = self._distancia(tramo.robot, tramo.punto)
        if math.isnan(d):
            return False, (
                f"'{tramo.robot}' dijo SUCCEEDED pero no publica /odom, asi que "
                f"la llegada no se puede verificar. No se acepta")
        if d > TOLERANCIA_LLEGADA_M:
            return False, (
                f"'{tramo.robot}' dijo SUCCEEDED pero /odom lo situa a "
                f"{d:.3f} m del punto, por encima de los "
                f"{TOLERANCIA_LLEGADA_M} m de tolerancia")
        self.get_logger().info(f"    llegada verificada contra /odom: {d:.3f} m")
        return True, ""

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


def main(args=None):
    rclpy.init(args=args)
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
