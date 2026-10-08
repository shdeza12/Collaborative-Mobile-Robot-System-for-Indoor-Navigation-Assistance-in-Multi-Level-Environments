#!/usr/bin/env python3
"""El servicio media_vuelta del agente, con ROS de verdad y un mundo simulado minimo.

POR QUE EXISTE
--------------
prueba_media_vuelta.py prueba la logica sin ROS. Aqui se prueba lo que solo falla
con un grafo vivo: que el agente encuentre el LiDAR, la TF del LiDAR y el mapa;
que el servicio, que bloquea durante la maniobra, no pare el estado a 2 Hz
(RF-08); y que no maniobre si Nav2 tiene una meta activa.

El mundo es la salida del piso 4 (paredes y lamina de la escalera): un nodo
publica /robot1/odom, la TF map -> odom -> base_link -> laser, un LiDAR por
trazado de rayos y el mapa, y mueve el vehiculo con /robot1/cmd_vel con un radio
de 0,6 m hacia un lado y 1,5 m hacia el otro, como racey.

QUE COMPRUEBA
-------------
  1. El agente ofrece /robot1/media_vuelta.
  2. Con una meta de Nav2 activa, la rechaza y no mueve el vehiculo.
  3. Desde la escalera del piso 4, mirando al sur: completa al menos 160 grados.
  4. La huella nunca toca una pared ni la lamina de la escalera.
  5. El estado sigue saliendo a unos 2 Hz durante la maniobra y lo dice en 'detalle'.

Uso, desde la raiz del repositorio:

    source ~/deepracer_sim_ws/install/setup.bash
    ROS_DOMAIN_ID=94 ROS_LOCALHOST_ONLY=1 python3 herramientas/prueba_media_vuelta_ros.py
"""
import importlib.util
import math
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time

import numpy as np
import rclpy
from action_msgs.msg import GoalStatus, GoalStatusArray
from coordinacion_msgs.msg import EstadoRobot
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import (QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy,
                       qos_profile_action_status_default, qos_profile_sensor_data)
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

RAIZ = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'media_vuelta', RAIZ / 'Robot/aws-deepracer/coordinacion/coordinacion/media_vuelta.py')
mv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mv)

NS = 'robot1'
SEGMENTOS = [((19.0, 0.11), (23.6, 0.11)), ((23.6, -0.07), (25.45, -0.07)),
             ((23.6, 0.11), (23.6, -0.07)), ((19.0, 2.46), (25.45, 2.46)),
             ((25.45, -0.07), (25.45, 2.46))]
X0, Y0, YAW0 = 24.39, 0.82, 0.0          # waypoint de la escalera del piso 4, mirando al sur


def puntos_pared(paso=0.02):
    return np.vstack([np.column_stack((np.linspace(a[0], b[0], int(math.dist(a, b) / paso) + 2),
                                       np.linspace(a[1], b[1], int(math.dist(a, b) / paso) + 2)))
                      for a, b in SEGMENTOS])


def cuaternio(yaw):
    return 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2)


class Mundo:
    """El vehiculo, sus sensores y el mapa. Lo mueve /robot1/cmd_vel."""

    def __init__(self, nodo):
        self.n = nodo
        self.x, self.y, self.yaw, self.v, self.lado = X0, Y0, YAW0, 0.0, 0
        self.orden = (0.0, 0.0)
        self.paredes = puntos_pared()
        self.holgura_min = math.inf
        self.giro_total = 0.0
        self.tf = TransformBroadcaster(nodo)
        est = StaticTransformBroadcaster(nodo)
        estaticas = []
        for padre, hijo in ((f'{NS}/map', f'{NS}/odom'), (f'{NS}/base_link', f'{NS}/laser')):
            t = TransformStamped()
            t.header.stamp = nodo.get_clock().now().to_msg()
            t.header.frame_id, t.child_frame_id = padre, hijo
            t.transform.rotation.w = 1.0
            estaticas.append(t)
        est.sendTransform(estaticas)
        self.pub_odom = nodo.create_publisher(Odometry, f'/{NS}/odom', 10)
        self.pub_scan = nodo.create_publisher(LaserScan, f'/{NS}/scan', qos_profile_sensor_data)
        qos_mapa = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                              reliability=QoSReliabilityPolicy.RELIABLE)
        self.pub_mapa = nodo.create_publisher(OccupancyGrid, f'/{NS}/map', qos_mapa)
        nodo.create_subscription(Twist, f'/{NS}/cmd_vel', self._cmd, 10)
        self._publicar_mapa()
        nodo.create_timer(0.02, self._avanzar)
        nodo.create_timer(0.1, self._scan)

    def _cmd(self, m):
        self.orden = (m.linear.x, m.angular.z)

    def _publicar_mapa(self):
        m = OccupancyGrid()
        m.header.frame_id = f'{NS}/map'
        m.info.resolution = 0.06
        m.info.width, m.info.height = 150, 70
        m.info.origin.position.x, m.info.origin.position.y = 18.0, -1.0
        m.info.origin.orientation.w = 1.0
        datos = np.zeros((70, 150), dtype=np.int8)
        c = ((self.paredes[:, 0] - 18.0) / 0.06).astype(int)
        f = ((self.paredes[:, 1] + 1.0) / 0.06).astype(int)
        ok = (c >= 0) & (c < 150) & (f >= 0) & (f < 70)
        datos[f[ok], c[ok]] = 100
        m.data = datos.flatten().tolist()
        self.pub_mapa.publish(m)

    def _avanzar(self):
        dt = 0.02
        v_cmd, w_cmd = self.orden
        objetivo = 0.0 if v_cmd == 0 else (0.65 if v_cmd > 0 else -0.45)
        tasa = abs(objetivo) / 0.2 if objetivo else 0.65 / 0.3
        self.v += max(-tasa * dt, min(tasa * dt, objetivo - self.v))
        if v_cmd != 0 and w_cmd != 0:
            self.lado = 1 if w_cmd / v_cmd > 0 else -1
        if self.lado:
            dyaw = self.v / (0.6 if self.lado > 0 else 1.5) * self.lado * dt
            self.yaw += dyaw
            self.giro_total += dyaw
        self.x += self.v * math.cos(self.yaw) * dt
        self.y += self.v * math.sin(self.yaw) * dt
        self.holgura_min = min(self.holgura_min,
                               mv.holgura(mv.a_marco(self.paredes, self.x, self.y, self.yaw)))
        ahora = self.n.get_clock().now().to_msg()
        t = TransformStamped()
        t.header.stamp, t.header.frame_id, t.child_frame_id = ahora, f'{NS}/odom', f'{NS}/base_link'
        t.transform.translation.x, t.transform.translation.y = self.x, self.y
        (t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z,
         t.transform.rotation.w) = cuaternio(self.yaw)
        self.tf.sendTransform(t)
        o = Odometry()
        o.header.stamp, o.header.frame_id, o.child_frame_id = ahora, f'{NS}/odom', f'{NS}/base_link'
        o.pose.pose.position.x, o.pose.pose.position.y = self.x, self.y
        (o.pose.pose.orientation.x, o.pose.pose.orientation.y, o.pose.pose.orientation.z,
         o.pose.pose.orientation.w) = cuaternio(self.yaw)
        o.twist.twist.linear.x = self.v
        self.pub_odom.publish(o)

    def _scan(self):
        n = 360
        angulos = self.yaw + np.linspace(-math.pi, math.pi, n, endpoint=False)
        d = np.column_stack((np.cos(angulos), np.sin(angulos)))
        rangos = np.full(n, np.inf)
        for (ax, ay), (bx, by) in SEGMENTOS:
            ex, ey = bx - ax, by - ay
            den = d[:, 0] * ey - d[:, 1] * ex
            with np.errstate(divide='ignore', invalid='ignore'):
                t = ((ax - self.x) * ey - (ay - self.y) * ex) / den
                u = ((ax - self.x) * d[:, 1] - (ay - self.y) * d[:, 0]) / den
            ok = (np.abs(den) > 1e-9) & (t > 0) & (u >= 0) & (u <= 1)
            rangos[ok] = np.minimum(rangos[ok], t[ok])
        m = LaserScan()
        m.header.stamp, m.header.frame_id = self.n.get_clock().now().to_msg(), f'{NS}/laser'
        m.angle_min, m.angle_increment = -math.pi, 2 * math.pi / n
        m.angle_max = math.pi - m.angle_increment
        m.range_min, m.range_max = 0.15, 12.0
        m.ranges = [float(min(r, 12.0)) for r in rangos]
        self.pub_scan.publish(m)


def main():
    ok_n, fallos = 0, []

    def exigir(cond, mensaje):
        nonlocal ok_n
        if cond:
            ok_n += 1
            print('  [OK ]', mensaje)
        else:
            fallos.append(mensaje)
            print('  [MAL]', mensaje)

    rclpy.init()
    nodo = rclpy.create_node('mundo_media_vuelta')
    mundo = Mundo(nodo)
    estados = []
    nodo.create_subscription(EstadoRobot, f'/{NS}/estado',
                             lambda m: estados.append((time.monotonic(), m.detalle)), 10)
    pub_status = nodo.create_publisher(GoalStatusArray, f'/{NS}/navigate_to_pose/_action/status',
                                       qos_profile_action_status_default)
    cliente = nodo.create_client(Trigger, f'/{NS}/media_vuelta')
    ejecutor = MultiThreadedExecutor(num_threads=3)
    ejecutor.add_node(nodo)
    hilo = threading.Thread(target=ejecutor.spin, daemon=True)
    hilo.start()

    agente = subprocess.Popen(
        ['ros2', 'run', 'coordinacion', 'agente', '--ros-args', '-r', f'__ns:=/{NS}',
         '-p', 'nivel:=4'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True)   # 'ros2 run' deja un hijo: se termina el grupo entero
    try:
        print('1. El servicio')
        exigir(cliente.wait_for_service(timeout_sec=30.0), f'/{NS}/media_vuelta disponible')
        time.sleep(3.0)                       # mapa, TF y primeros barridos

        def llamar(espera=150.0):
            fut = cliente.call_async(Trigger.Request())
            t0 = time.monotonic()
            while not fut.done() and time.monotonic() - t0 < espera:
                time.sleep(0.05)
            return fut.result() if fut.done() else None

        print('2. Con una meta de Nav2 activa')
        st = GoalStatusArray()
        g = GoalStatus()
        g.status = GoalStatus.STATUS_EXECUTING
        st.status_list = [g]
        pub_status.publish(st)
        time.sleep(1.5)
        x0, y0 = mundo.x, mundo.y
        r = llamar(10.0)
        exigir(r is not None and not r.success, f'la rechaza: {r.message if r else "sin respuesta"}')
        exigir(math.hypot(mundo.x - x0, mundo.y - y0) < 0.01, 'y el vehiculo no se movio')
        g.status = GoalStatus.STATUS_SUCCEEDED
        pub_status.publish(st)
        time.sleep(1.5)

        print('3. Desde la escalera del piso 4, mirando al sur')
        estados.clear()
        t0 = time.monotonic()
        r = llamar()
        dur = time.monotonic() - t0
        girado = math.degrees(abs(mundo.giro_total))
        exigir(r is not None and r.success, f'completa: {r.message if r else "sin respuesta"}')
        exigir(girado >= 160.0, f'giro real del vehiculo {girado:.0f} grados en {dur:.1f} s')
        print('4. Sin tocar nada')
        exigir(mundo.holgura_min > 0.0,
               f'holgura minima de la huella a paredes y escalera {mundo.holgura_min:.2f} m')
        exigir(mundo.y > -0.07 + mv.ANCHO_MEDIO,
               f'termina lejos de la lamina de la escalera (y = {mundo.y:.2f})')
        print('5. El estado durante la maniobra')
        durante = [e for e in estados if e[0] <= t0 + dur]
        hz = len(durante) / dur if dur > 0 else 0
        exigir(1.6 <= hz <= 2.4, f'{len(durante)} estados en {dur:.1f} s ({hz:.1f} Hz)')
        exigir(any('media vuelta en curso' in d for _, d in durante),
               "'detalle' dice 'media vuelta en curso'")
    finally:
        os.killpg(agente.pid, signal.SIGINT)
        try:
            salida = agente.communicate(timeout=10)[0]
        except subprocess.TimeoutExpired:
            os.killpg(agente.pid, signal.SIGKILL)
            salida = agente.communicate()[0]
        ejecutor.shutdown()
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    lineas = [l for l in salida.splitlines() if 'media vuelta' in l or 'espacio libre' in l]
    print('\n'.join('    agente: ' + l[l.find(']: ') + 3:] if ']: ' in l else l for l in lineas[-6:]))
    print('=' * 62)
    if fallos:
        print(f'{len(fallos)} comprobaciones FALLAN de {ok_n + len(fallos)}')
        return 1
    print(f'Todas las comprobaciones pasan ({ok_n}).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
