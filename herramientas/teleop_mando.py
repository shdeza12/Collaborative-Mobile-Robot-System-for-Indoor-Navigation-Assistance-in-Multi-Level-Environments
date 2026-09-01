#!/usr/bin/env python3
"""Teleoperacion del DeepRacer fisico con un mando (Nintendo Switch Pro).

Se ejecuta EN EL VEHICULO. Ver GUIA_TELEOP_MANDO.md.
"""

import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

from deepracer_interfaces_pkg.msg import ServoCtrlMsg

TOPICO_SERVO = "/ctrl_pkg/servo_msg"
TOPICO_JOY = "/joy"


class TeleopMando(Node):
    def __init__(self):
        super().__init__("teleop_mando")

        self.declare_parameter("eje_traccion", 1)
        self.declare_parameter("eje_direccion", 2)
        # ZR y ZL no llegan como botones sino como ejes analogicos: +1.0 en
        # reposo, -1.0 pulsados a fondo. Un gatillo sin estrenar puede leerse
        # 0.0 hasta que se toca por primera vez, y con el umbral negativo eso
        # cuenta como "sin pulsar", que es el lado seguro.
        self.declare_parameter("eje_habilitar", 5)
        self.declare_parameter("eje_turbo", 4)
        self.declare_parameter("umbral_gatillo", -0.5)
        self.declare_parameter("limite_normal", 0.35)
        self.declare_parameter("limite_turbo", 0.70)
        self.declare_parameter("limite_direccion", 1.0)
        self.declare_parameter("zona_muerta", 0.12)
        self.declare_parameter("timeout_s", 0.6)
        self.declare_parameter("invertir_traccion", True)
        self.declare_parameter("invertir_direccion", False)
        self.declare_parameter("frecuencia_hz", 20.0)

        p = self.get_parameter
        self.eje_traccion = p("eje_traccion").value
        self.eje_direccion = p("eje_direccion").value
        self.eje_habilitar = p("eje_habilitar").value
        self.eje_turbo = p("eje_turbo").value
        self.umbral_gatillo = p("umbral_gatillo").value
        self.limite_normal = p("limite_normal").value
        self.limite_turbo = p("limite_turbo").value
        self.limite_direccion = p("limite_direccion").value
        self.zona_muerta = p("zona_muerta").value
        self.timeout_s = p("timeout_s").value
        self.invertir_traccion = p("invertir_traccion").value
        self.invertir_direccion = p("invertir_direccion").value
        frecuencia = p("frecuencia_hz").value

        self.pub = self.create_publisher(ServoCtrlMsg, TOPICO_SERVO, 1)
        self.create_subscription(Joy, TOPICO_JOY, self._al_recibir_joy, 1)

        self.angulo = 0.0
        self.traccion = 0.0
        self.t_ultimo_joy = 0.0
        self.habilitado = False
        self.aviso_dado = False

        self.create_timer(1.0 / frecuencia, self._publicar)

        self.get_logger().info(
            f"Teleop de mando activo. Manten pulsado el gatillo del eje "
            f"{self.eje_habilitar} (ZR) para conducir; el eje "
            f"{self.eje_turbo} (ZL) es turbo. "
            f"Limites: {self.limite_normal} / {self.limite_turbo}.")

    def _escalar(self, valor):
        """Aplica zona muerta y reescala para que el recorrido util sea continuo.

        Sin el reescalado el mando saltaria de 0 al valor de la zona muerta en
        cuanto se supera el umbral, que en un vehiculo de 4 m/s es un tiron.
        """
        if abs(valor) < self.zona_muerta:
            return 0.0
        signo = 1.0 if valor > 0 else -1.0
        return signo * (abs(valor) - self.zona_muerta) / (1.0 - self.zona_muerta)

    def _al_recibir_joy(self, msg):
        self.t_ultimo_joy = time.monotonic()

        indice_max = max(self.eje_traccion, self.eje_direccion,
                         self.eje_habilitar, self.eje_turbo)
        if len(msg.axes) <= indice_max:
            if not self.aviso_dado:
                self.get_logger().error(
                    f"El mando publica {len(msg.axes)} ejes, insuficientes "
                    f"para la configuracion actual, que necesita al menos "
                    f"{indice_max + 1}. Revisa los indices con "
                    f"'ros2 topic echo /joy'.")
                self.aviso_dado = True
            self.habilitado = False
            return

        self.habilitado = msg.axes[self.eje_habilitar] < self.umbral_gatillo
        if not self.habilitado:
            self.angulo = 0.0
            self.traccion = 0.0
            return

        turbo = msg.axes[self.eje_turbo] < self.umbral_gatillo
        limite = self.limite_turbo if turbo else self.limite_normal

        traccion = self._escalar(msg.axes[self.eje_traccion])
        direccion = self._escalar(msg.axes[self.eje_direccion])

        if self.invertir_traccion:
            traccion = -traccion
        if self.invertir_direccion:
            direccion = -direccion

        self.traccion = max(-1.0, min(1.0, traccion * limite))
        self.angulo = max(-1.0, min(1.0, direccion * self.limite_direccion))

    def _publicar(self):
        """El hombre muerto vive aqui y no en el callback: si /joy deja de
        llegar —mando apagado, wifi caido, joy_node muerto— nadie ejecutaria el
        callback y el vehiculo conservaria el ultimo valor."""
        vencido = (time.monotonic() - self.t_ultimo_joy) > self.timeout_s
        if vencido or not self.habilitado:
            self.angulo = 0.0
            self.traccion = 0.0

        msg = ServoCtrlMsg()
        msg.angle = float(self.angulo)
        msg.throttle = float(self.traccion)
        self.pub.publish(msg)

    def parar(self):
        msg = ServoCtrlMsg()
        msg.angle = 0.0
        msg.throttle = 0.0
        for _ in range(10):
            self.pub.publish(msg)
            time.sleep(0.02)


def main():
    rclpy.init()
    nodo = TeleopMando()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.parar()
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
