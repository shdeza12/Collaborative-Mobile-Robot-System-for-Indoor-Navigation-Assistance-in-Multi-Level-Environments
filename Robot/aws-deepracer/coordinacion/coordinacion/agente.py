#!/usr/bin/env python3
"""Nodo de agente: publica el estado del robot en /<ns>/estado a 2 Hz (RF-08).

Es el cableado ROS alrededor de estado_agente.py. La decision de QUE estado
tiene el robot vive alli y se comprueba sin simulador con prueba_agente.py; aqui
solo queda lo que necesita un grafo vivo: suscribirse al status de la accion,
leer la TF y publicar a ritmo fijo.

Interfaces, segun §4 de Documentos/CONTRATO_INTERFACES.md:
    /<ns>/estado                              EstadoRobot a 2 Hz   (lo publica)
    /<ns>/navigate_to_pose/_action/status     GoalStatusArray      (lo lee)
    TF <ns>/map -> <ns>/base_link                                  (la lee)

Se lanza DENTRO del namespace del robot. Todos los nombres de arriba son
relativos a proposito: ROS los cuelga solo de /robot1/ o /robot2/. Escribirlos
absolutos rompe la separacion por namespace que el proyecto usa desde el
2026-08-30.

TRES COSAS QUE EN ESTE PROYECTO YA FALLARON EN SILENCIO, Y QUE AQUI SE EVITAN
DE FORMA DELIBERADA. Las tres dan el mismo sintoma -no hay error, no hay dato-,
que es el peor sintoma posible:

1. QoS DEL STATUS. El topico de status de una accion se publica con
   RELIABLE + TRANSIENT_LOCAL, no con el perfil por defecto. Suscribirse con
   el perfil por defecto (VOLATILE) NO empareja, y rclpy no avisa: el callback
   simplemente no se llama nunca y el robot se queda LIBRE para siempre. Por
   eso se usa qos_profile_action_status_default y no un numero suelto.

2. LA POSE NO SE LEE DE amcl_pose. Ese topico es TRANSIENT_LOCAL y nav2_amcl
   solo publica cuando el robot se mueve: un robot quieto entrega la ultima
   muestra caducada sin dar ningun error. Medido el 2026-08-24: 0 mensajes en
   10 s parado, 12 en movimiento. Lo advierte el propio EstadoRobot.msg. Se lee
   la TF, que si se republica con el robot quieto.

3. LA PUBLICACION NO SE PARA SI FALLA LA TF. El temporizador publica a 2 Hz
   pase lo que pase; si la TF no esta disponible se manda la ultima pose buena
   y se dice en 'detalle'. Si un fallo de TF pudiera cortar la publicacion, el
   criterio de aceptacion de RF-08 (ros2 topic hz devuelve 2 Hz) fallaria por
   un motivo que no tiene nada que ver con lo que RF-08 mide.
"""

import sys

import rclpy
import tf2_ros
from action_msgs.msg import GoalStatusArray
from coordinacion_msgs.msg import EstadoRobot
from rclpy.node import Node
from rclpy.qos import qos_profile_action_status_default

from coordinacion.estado_agente import (
    PERIODO_S, TOPICO_ESTADO, TOPICO_STATUS_ACCION, MaquinaEstado)

#: Cada cuantos ciclos se repite el aviso de TF ausente. A 2 Hz, 20 ciclos son
#: 10 s: suficiente para enterarse, poco para inundar el log de una mision larga.
CICLOS_ENTRE_AVISOS = 20


class Agente(Node):
    """Publica lo que este robot dice de si mismo, a ritmo fijo."""

    def __init__(self):
        super().__init__("agente")

        # El namespace es la identidad del robot. Se declara robot_id como
        # parametro por si hiciera falta forzarlo, pero el valor util es el
        # namespace: asi un mismo lanzamiento sirve para robot1 y robot2 sin
        # tocar configuracion.
        ns = self.get_namespace().strip("/")
        self.declare_parameter("robot_id", ns)
        self.declare_parameter("nivel", 0)
        self.declare_parameter("marco_mapa", f"{ns}/map" if ns else "map")
        self.declare_parameter("marco_base", f"{ns}/base_link" if ns else "base_link")

        self.robot_id = self.get_parameter("robot_id").value or ns
        self.nivel = int(self.get_parameter("nivel").value)
        self.marco_mapa = self.get_parameter("marco_mapa").value
        self.marco_base = self.get_parameter("marco_base").value

        if not self.robot_id:
            self.get_logger().warn(
                "Este nodo no tiene namespace ni parametro robot_id, asi que "
                "publicara en /estado con robot_id vacio. Se lanza dentro del "
                "namespace del robot: ros2 run ... --ros-args -r __ns:=/robot1")

        # EstadoRobot.msg admite nivel 1 o 2. Un 0 no es un valor valido, es un
        # parametro que nadie puso. Se avisa en vez de publicarlo en silencio,
        # que es como el registro de una campana entera sale con un campo malo
        # y nadie se entera hasta que toca analizarla.
        if self.nivel not in (1, 2):
            self.get_logger().warn(
                f"nivel={self.nivel}, y EstadoRobot.msg solo admite 1 o 2. Se "
                "publicara igual para no ocultar el problema, pero el dato es "
                "invalido. Pasar 'nivel:=1' o 'nivel:=2' al lanzamiento.")

        self.maquina = MaquinaEstado()
        self.ultima_pose = None
        self.motivo_tf = "sin pose todavia: la TF aun no ha llegado"
        self.ciclos_sin_tf = 0

        self.buffer_tf = tf2_ros.Buffer()
        self.escucha_tf = tf2_ros.TransformListener(self.buffer_tf, self)

        self.pub = self.create_publisher(EstadoRobot, TOPICO_ESTADO, 10)

        # OJO: qos_profile_action_status_default, no el perfil por defecto.
        # Ver el aviso 1 de la cabecera.
        self.create_subscription(
            GoalStatusArray, TOPICO_STATUS_ACCION, self._status,
            qos_profile_action_status_default)

        self.create_timer(PERIODO_S, self._publicar)

        self.get_logger().info(
            f"Agente '{self.robot_id}' publicando {TOPICO_ESTADO} a "
            f"{1.0 / PERIODO_S:.1f} Hz; lee {TOPICO_STATUS_ACCION} y la TF "
            f"{self.marco_mapa} -> {self.marco_base}")

    # ------------------------------------------------------------- entradas
    def _status(self, msg):
        """Llega el status de navigate_to_pose. Es la unica fuente del estado."""
        self.maquina.actualizar([g.status for g in msg.status_list])

    def _leer_pose(self):
        """Devuelve (pose, motivo). La pose es None si la TF no esta.

        No lanza: un fallo de TF no puede tumbar el temporizador (aviso 3).
        """
        try:
            t = self.buffer_tf.lookup_transform(
                self.marco_mapa, self.marco_base, rclpy.time.Time())
        except tf2_ros.TransformException as e:
            return None, f"TF {self.marco_mapa} -> {self.marco_base} no disponible: {e}"

        pose = EstadoRobot().pose
        pose.header.stamp = t.header.stamp
        pose.header.frame_id = self.marco_mapa
        pose.pose.position.x = t.transform.translation.x
        pose.pose.position.y = t.transform.translation.y
        pose.pose.position.z = t.transform.translation.z
        pose.pose.orientation = t.transform.rotation
        return pose, ""

    # ------------------------------------------------------------- salida
    def _publicar(self):
        """Manda un EstadoRobot. Se ejecuta cada PERIODO_S pase lo que pase."""
        pose, motivo = self._leer_pose()

        if pose is not None:
            self.ultima_pose = pose
            self.motivo_tf = ""
            self.ciclos_sin_tf = 0
        else:
            self.motivo_tf = motivo
            # Se avisa la primera vez y luego cada CICLOS_ENTRE_AVISOS, para
            # que el problema se vea sin ahogar el log.
            if self.ciclos_sin_tf % CICLOS_ENTRE_AVISOS == 0:
                self.get_logger().warn(motivo)
            self.ciclos_sin_tf += 1

        msg = EstadoRobot()
        msg.robot_id = self.robot_id
        msg.nivel = self.nivel
        msg.estado = self.maquina.estado
        msg.stamp = self.get_clock().now().to_msg()
        if self.ultima_pose is not None:
            msg.pose = self.ultima_pose
            # Una pose vieja se publica, pero se declara vieja. Publicarla como
            # si fuera fresca es exactamente el engano de amcl_pose (aviso 2).
            msg.detalle = self.motivo_tf and f"pose caducada; {self.motivo_tf}"
        else:
            msg.detalle = self.motivo_tf

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    nodo = Agente()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
