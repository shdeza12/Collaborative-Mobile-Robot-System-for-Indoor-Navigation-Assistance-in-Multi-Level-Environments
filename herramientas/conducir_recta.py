#!/usr/bin/env python3
"""Recorre un tramo recto en ida y vuelta, sin un solo giro.

POR QUE EXISTE
--------------
Es el conductor del ensayo de control del 2026-09-08
('S22_mapeo_pasillo_fallido.md' §8.4). Su unico proposito es dejar el
MOVIMIENTO fijo para que la unica variable del experimento sea la GEOMETRIA
DEL ENTORNO.

Hasta ese dia el fallo de mapeo se habia atribuido primero a la conduccion y
despues a la cadena, y las dos atribuciones eran prematuras. Comparar un
pasillo largo contra una caja cerrada solo prueba algo si el carro se mueve
igual en los dos; de ahi que este guion no gire nunca -'angular.z' es
literalmente 0,0- y mantenga la velocidad constante.

Con VELOCIDAD = 0,33 m/s -la de 'S21_piloto_bajada_01', o sea la misma que
fallo en el pasillo largo- y el modelo 'pasillo_usta' como caja cerrada de
7,70 x 2,70 m, la razon de registro longitudinal subio de 0,209 a 1,010 y el
mapa resultante fue el primero que este proyecto acepta con SLAM.

POR QUE INVIERTE POR ODOMETRIA Y NO POR TIEMPO
----------------------------------------------
Invertir a los N segundos deja la longitud recorrida a merced de la
aceleracion del plugin y del arranque, y entonces la distancia no es una
constante del experimento sino un resultado. Se invierte al cruzar un umbral
de posicion, que en simulacion es exacto porque '/odom' sale de
'model_->WorldPose()'.

EN EL CARRO FISICO NO SIRVE, y no por capricho: alli '/odom' es la estimacion
de rf2o, que es justo lo que se esta midiendo. Usarla como referencia seria
circular.

USO
    ros2 run ... o directamente:
    herramientas/conducir_recta.py [velocidad] [x_min] [x_max] [vueltas]

    velocidad   m/s, por defecto 0.33
    x_min/x_max metros en el marco de '/odom', por defecto -2.8 y 2.8
    vueltas     ida+vuelta completas, por defecto 2
"""
import sys

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class Conductor(Node):
    def __init__(self, velocidad, x_min, x_max, vueltas):
        super().__init__('conductor_recta')
        self.velocidad = velocidad
        self.x_min, self.x_max = x_min, x_max
        self.objetivo = vueltas
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.odom, 10)
        self.create_timer(0.05, self.tic)
        self.x = None
        self.sentido = 1.0
        self.vueltas = 0
        self.hecho = False

    def odom(self, m):
        self.x = m.pose.pose.position.x

    def tic(self):
        if self.x is None or self.hecho:
            return
        t = Twist()
        if self.sentido > 0 and self.x >= self.x_max:
            self.sentido = -1.0
            self.get_logger().info(f'giro a atras en x={self.x:.2f}')
        elif self.sentido < 0 and self.x <= self.x_min:
            self.sentido = 1.0
            self.vueltas += 1
            self.get_logger().info(f'vuelta {self.vueltas} en x={self.x:.2f}')
            if self.vueltas >= self.objetivo:
                self.hecho = True
                self.pub.publish(Twist())
                self.get_logger().info('terminado')
                return
        t.linear.x = self.velocidad * self.sentido
        t.angular.z = 0.0   # cero literal: el experimento exige recta pura
        self.pub.publish(t)


def main():
    a = sys.argv[1:]
    velocidad = float(a[0]) if len(a) > 0 else 0.33
    x_min = float(a[1]) if len(a) > 1 else -2.8
    x_max = float(a[2]) if len(a) > 2 else 2.8
    vueltas = int(a[3]) if len(a) > 3 else 2

    rclpy.init()
    n = Conductor(velocidad, x_min, x_max, vueltas)
    try:
        while rclpy.ok() and not n.hecho:
            rclpy.spin_once(n, timeout_sec=0.1)
    finally:
        n.pub.publish(Twist())
        rclpy.spin_once(n, timeout_sec=0.2)
        n.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
