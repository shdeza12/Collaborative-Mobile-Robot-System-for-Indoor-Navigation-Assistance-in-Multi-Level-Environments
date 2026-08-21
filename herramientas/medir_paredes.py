#!/usr/bin/env python3
"""Mide con el LiDAR la distancia a pared en las cuatro direcciones del MUNDO.

Por que no se leen los rayos "del frente"
-----------------------------------------
El laser va montado con rpy 0 0 3.1416 respecto al chasis, asi que el angulo 0
del barrido apunta hacia ATRAS del vehiculo. Cada rayo se lleva aqui a angulo
absoluto del mundo -yaw del robot mas pi mas el angulo del rayo- para poder
comparar contra las paredes del SDF, que estan en coordenadas del mundo.

Que hay que mirar en la salida
------------------------------
- El rayo elegido trae entre parentesis su desviacion respecto al eje pedido. Si
  esa desviacion pasa de unos pocos grados, NO hay rayo en esa direccion y el
  numero no sirve: el barrido tiene un sector ciego en el empalme +-180 deg.
- Una distancia larga en una direccion donde el mapa esta abierto no es una
  pared. El vehiculo reposa 1,4 deg de morro abajo y el rayo choca contra el
  piso a unos 7,3 m. Es un defecto conocido del modelo URDF de AWS.

Uso:
    python3 herramientas/medir_paredes.py robot1
    ROS_DOMAIN_ID=2 python3 herramientas/medir_paredes.py robot2
"""

import math
import sys

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

NS = sys.argv[1] if len(sys.argv) > 1 else "robot1"
EJES = {"+x mundo": 0.0, "+y mundo": 90.0, "-x mundo": 180.0, "-y mundo": -90.0}


class Medidor(Node):
    def __init__(self):
        super().__init__("medir_paredes")
        self.pose = None
        self.hecho = False
        self.create_subscription(Odometry, f"/{NS}/odom", self.od, 10)
        # El LiDAR publica BEST_EFFORT; un suscriptor por defecto es RELIABLE y
        # no recibiria nada, sin error visible.
        self.create_subscription(LaserScan, f"/{NS}/scan", self.sc, qos_profile_sensor_data)

    def od(self, m):
        p, q = m.pose.pose.position, m.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))
        self.pose = (p.x, p.y, p.z, yaw)

    def sc(self, m):
        if self.pose is None or self.hecho:
            return
        x, y, z, yaw = self.pose
        print(f"pose odom: x={x:+.3f} y={y:+.3f} z={z:+.4f} yaw={math.degrees(yaw):+.2f} deg")
        res = {}
        for nombre, grados in EJES.items():
            mejor = None
            for i, r in enumerate(m.ranges):
                if not math.isfinite(r) or not (m.range_min < r < m.range_max):
                    continue
                a = math.degrees(yaw + math.pi + m.angle_min + i * m.angle_increment)
                d = (a - grados + 180) % 360 - 180
                if mejor is None or abs(d) < abs(mejor[0]):
                    mejor = (d, r)
            res[nombre] = mejor
            aviso = "  <-- sin rayo en ese eje" if abs(mejor[0]) > 3.0 else ""
            print(f"  {nombre}: {mejor[1]:6.3f} m   (rayo a {mejor[0]:+.2f} deg del eje){aviso}")
        print(f"  ancho en x = {res['+x mundo'][1] + res['-x mundo'][1]:.3f} m")
        print(f"  ancho en y = {res['+y mundo'][1] + res['-y mundo'][1]:.3f} m")
        self.hecho = True
        raise SystemExit


def main():
    rclpy.init()
    nodo = Medidor()
    try:
        rclpy.spin(nodo)
    except SystemExit:
        pass
    if nodo.pose is None:
        print(f"no llego odometria de /{NS}/odom. Comprobar ROS_DOMAIN_ID.")


main()
