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

import datetime
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

from coordinacion.planificador import (
    ASIGNACION_POR_DEFECTO, COMPLETADA, ErrorPlanificacion, FALLIDA, INACTIVA,
    condicion_de, generar_mision_id, planificar, yaw_a_cuaternion,
)

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

        self.asignacion = {
            1: self.get_parameter("robot_nivel_1").value,
            2: self.get_parameter("robot_nivel_2").value,
        }
        self.espera_servidor = self.get_parameter("espera_servidor_s").value
        self.prefijo_mision = self.get_parameter("prefijo_mision").value

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
                lambda msg, n=ns: self.ultimo_odom.__setitem__(n, msg), 10,
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
        # El mismo reloj que /clock cuando use_sim_time esta puesto. time.time()
        # lo ignora, y con RTF >= 0,99 las dos formas difieren hasta un 1 %:
        # sobre t_respuesta eso no es ruido, es sesgo. Ver §3 del protocolo.
        t0 = self.get_clock().now()
        condicion = condicion_de(self.catalogo, pet.origen_id, pet.destino_id)
        mision_id = generar_mision_id(
            self.prefijo_mision, condicion, datetime.datetime.now())
        # Se fijan una vez y no cambian en toda la mision. El destino ACTUAL si
        # cambia, y lo pone _marcar; estos dos son lo que se pidio.
        self.estado.origen_id = pet.origen_id
        self.estado.destino_id = pet.destino_id
        res = GuiarUsuario.Result()

        self.get_logger().info(
            f"Mision: {pet.origen_id} -> {pet.destino_id}")

        try:
            tramos, relevos = planificar(
                self.catalogo, pet.origen_id, pet.destino_id, self.asignacion)
        except ErrorPlanificacion as e:
            # Falla antes de mover un solo robot, y el motivo ya viene redactado.
            self.get_logger().error(f"No se puede planificar: {e}")
            self._marcar(FALLIDA, "", None, str(e), mision_id)
            goal_handle.abort()
            res.exito, res.motivo_fallo = False, str(e)
            res.tiempo_total_s = (self.get_clock().now() - t0).nanoseconds * 1e-9
            return res

        for i, tramo in enumerate(tramos, 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                res.exito, res.motivo_fallo = False, "Cancelada por el usuario"
                res.tiempo_total_s = (self.get_clock().now() - t0).nanoseconds * 1e-9
                return res

            self._marcar(tramo.etapa, tramo.robot, tramo.punto,
                         tramo.mensaje_usuario, mision_id)
            self._feedback(goal_handle)
            self.get_logger().info(
                f"  tramo {i}/{len(tramos)}: {tramo.robot} -> {tramo.punto['id']}")

            ok, motivo = self._navegar(tramo)
            if not ok:
                self.get_logger().error(f"  tramo {i} fallo: {motivo}")
                self._marcar(FALLIDA, tramo.robot, tramo.punto,
                             f"No se pudo completar el trayecto: {motivo}",
                             mision_id)
                self._feedback(goal_handle)
                goal_handle.abort()
                res.exito, res.motivo_fallo = False, motivo
                res.tiempo_total_s = (self.get_clock().now() - t0).nanoseconds * 1e-9
                res.num_relevos = relevos
                return res

        destino = next(p for p in self.catalogo if p["id"] == pet.destino_id)
        self._marcar(COMPLETADA, tramos[-1].robot, destino,
                     f"Ha llegado a {destino['nombre']}.", mision_id)
        self._feedback(goal_handle)
        goal_handle.succeed()
        res.exito = True
        res.tiempo_total_s = (self.get_clock().now() - t0).nanoseconds * 1e-9
        res.num_relevos = relevos
        res.motivo_fallo = ""
        self.get_logger().info(
            f"Mision completada en {res.tiempo_total_s:.1f} s, "
            f"{relevos} relevo(s)")
        return res

    def _marcar(self, etapa, robot, punto, mensaje, mision_id):
        self.estado.mision_id = mision_id
        self.estado.etapa = etapa
        self.estado.robot_activo = robot
        self.estado.destino_actual = self._a_msg(punto) if punto else PuntoInteres()
        self.estado.mensaje_usuario = mensaje
        self.estado.distancia_restante = self._distancia(robot, punto) if punto else 0.0
        # Marca extraordinaria: el latido de 1 Hz sigue vivo para la HRI, pero el
        # cambio de etapa se publica en el instante en que ocurre. El §3.2 del
        # protocolo lo exige: 1 s de resolucion es demasiado grosero para el
        # hueco de relevo, que se espera en milisegundos.
        self._publicar_estado()

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

        # El punto (x, y) es sagrado; el rumbo no. Ver _yaw_de_llegada.
        yaw, motivo_yaw = self._yaw_de_llegada(tramo.robot, tramo.punto)
        _, _, qz, qw = yaw_a_cuaternion(yaw)
        objetivo.pose.pose.orientation.z, objetivo.pose.pose.orientation.w = qz, qw
        yaml_yaw = float(tramo.punto["pose"].get("yaw", 0.0))
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
        """Espera un futuro sin bloquear el executor (es multihilo)."""
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
