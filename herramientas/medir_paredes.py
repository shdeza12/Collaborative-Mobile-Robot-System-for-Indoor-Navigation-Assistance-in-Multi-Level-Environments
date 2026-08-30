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
  numero no sirve. La causa esta declarada en deepracer.xacro: el barrido va de
  -150 a +150 deg (lidar_360_degree_min_angle / max_angle, que pese al nombre
  son 300 deg y no 360), o sea un cono ciego de 60 deg centrado en los 180 deg
  del LASER. Y como el laser va girado 180 deg respecto al chasis, esos 60 deg
  caen sobre el FRENTE del vehiculo: el eje al que apunta el morro nunca es
  medible. Comprobado el 23-ago con tres poses de yaw distinto -robot1 a
  +91,34 deg ciego en +y, robot2 a -0,60 deg ciego en +x, robot2 a -36,77 deg
  sin ningun eje ciego-: el cono sigue al morro, no a un eje del mundo.
- Una distancia larga en una direccion donde el mapa esta abierto no es una
  pared: es el ground_plane. El vehiculo reposa inclinado ~1,4 deg, y los rayos
  que BAJAN son los de ATRAS. La distancia sigue r = (h/theta) / |cos(phi)| con
  phi medido desde el morro, y solo para phi > 90 deg; hacia adelante el rayo
  sube y no toca el suelo nunca. h/theta = 7,36 m, medido el 23-ago desde dos
  poses de robot2 (7,350 m a phi = 180,6 deg y 9,191 m a phi = 143,2 deg, que
  concuerdan al 0,24 %). Es un defecto conocido del modelo URDF de AWS.
  OJO: hasta el 23-ago aqui decia "morro abajo", que es el sentido CONTRARIO.
  La magnitud estaba bien y los 7,3 m tambien, pero el sentido nunca se pudo
  comprobar con esta herramienta, porque el rayo del morro cae justo dentro del
  cono ciego del punto anterior.

Uso:
    python3 herramientas/medir_paredes.py robot1
    python3 herramientas/medir_paredes.py robot2

    Sin exportar ningun dominio. Hasta el 2026-08-29 la segunda linea llevaba
    delante 'ROS_DOMAIN_ID=2', porque cada robot corria en su dominio DDS. Desde
    el 30-ago los dos viven en el dominio 0 -el defecto de ROS 2- y lo que los
    separa son los nombres: namespace, prefijo de TF y puerto de gzserver
    propios. Ver el comentario de DOMINIO en herramientas/robot.sh.
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
