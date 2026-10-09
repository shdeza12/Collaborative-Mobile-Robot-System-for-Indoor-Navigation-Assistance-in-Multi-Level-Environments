#!/usr/bin/env python3
"""Media vuelta del vehiculo a mano, con la misma logica protegida que usa el agente.

Uso, en el vehiculo, como root, con la particion y ~/coordinacion_ws cargado, el
puente corriendo y Nav2 SIN meta activa (este programa publica /cmd_vel):

    python3 ~deepracer/tesis/media_vuelta.py --pose 24.25 1.49 0.0
    python3 ~deepracer/tesis/media_vuelta.py --ns robot2 --giro auto

En las misiones no hace falta: el coordinador se la pide al agente cuando la
meta queda detras del vehiculo (coordinacion/media_vuelta.py). Esto es para
probarla suelta, sin coordinador.

--pose publica /initialpose ahi y espera a que AMCL converja (sigma < 0,20 m):
hace falta cuando el vehiculo se puso a mano.

QUE CAMBIO EL 2026-10-08. La primera version giraba en dos tiempos fijos
(reversa hasta 80 grados y avance hasta 170) sin mirar el LiDAR ni el mapa. En
p4r_11c funciono, pero su primer tiempo abrio el vehiculo hacia el vano de la
escalera. Ahora corta cada tiempo por espacio con el LiDAR y con el mapa (donde
la escalera esta cerrada con una lamina) y elige el costado con mas espacio.
"""
import argparse
import math
import sys
import threading
import time


def main():
    p = argparse.ArgumentParser(description='Media vuelta protegida, suelta.')
    p.add_argument('--pose', type=float, nargs=3, metavar=('X', 'Y', 'YAW'),
                   help='publica /initialpose ahi (mapa, yaw en radianes) antes de girar')
    p.add_argument('--giro', choices=('auto', 'izquierda', 'derecha'), default='auto',
                   help='sentido de rotacion; auto lo elige con el mapa')
    p.add_argument('--ns', default='', help="espacio de nombres, p. ej. 'robot2'")
    p.add_argument('--scan', default='/rplidar_ros/scan', help='topico del LiDAR')
    a = p.parse_args()
    ns = a.ns.strip('/')

    import rclpy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
    import tf2_ros
    from coordinacion.media_vuelta import ConexionMediaVuelta

    rclpy.init()
    nodo = rclpy.create_node('media_vuelta_manual', namespace=f'/{ns}' if ns else '')
    marco_mapa = f'{ns}/map' if ns else 'map'
    marco_base = f'{ns}/base_link' if ns else 'base_link'
    buffer_tf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buffer_tf, nodo)
    con = ConexionMediaVuelta(nodo, buffer_tf, marco_mapa, marco_base, topico_scan=a.scan)
    sigma = {'v': None}

    def on_amcl(m):
        c = m.pose.covariance
        sigma['v'] = math.sqrt(max(c[0], 0.0) + max(c[7], 0.0))
    nodo.create_subscription(PoseWithCovarianceStamped, 'amcl_pose', on_amcl,
                             QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                                        reliability=QoSReliabilityPolicy.RELIABLE))
    pub_ini = nodo.create_publisher(PoseWithCovarianceStamped, 'initialpose', 10)
    ejecutor = MultiThreadedExecutor(num_threads=2)
    ejecutor.add_node(nodo)
    threading.Thread(target=ejecutor.spin, daemon=True).start()

    try:
        if a.pose:
            m = PoseWithCovarianceStamped()
            m.header.frame_id = marco_mapa
            m.pose.pose.position.x, m.pose.pose.position.y = a.pose[0], a.pose[1]
            m.pose.pose.orientation.z = math.sin(a.pose[2] / 2)
            m.pose.pose.orientation.w = math.cos(a.pose[2] / 2)
            # 0,10 m y 0,05 rad, como corrida_nav2.py: lo que se acierta a mano.
            m.pose.covariance[0] = m.pose.covariance[7] = 0.10 ** 2
            m.pose.covariance[35] = 0.05 ** 2
            limite = time.monotonic() + 10.0
            while pub_ini.get_subscription_count() == 0 and time.monotonic() < limite:
                time.sleep(0.2)
            for _ in range(3):
                m.header.stamp = nodo.get_clock().now().to_msg()
                pub_ini.publish(m)
                time.sleep(0.3)
            limite = time.monotonic() + 20.0
            while (sigma['v'] is None or sigma['v'] >= 0.20) and time.monotonic() < limite:
                time.sleep(0.2)
            if sigma['v'] is None or sigma['v'] >= 0.20:
                print('ABORTA: AMCL no converge con la pose dada; no se mueve el vehiculo')
                return 1
            print(f'pose inicial puesta; AMCL con sigma {sigma["v"]:.2f} m')
        # El LiDAR y la odometria los escucha ejecutar() mientras dura la maniobra;
        # aqui solo se espera el mapa.
        limite = time.monotonic() + 15.0
        while con.celdas is None and time.monotonic() < limite:
            time.sleep(0.2)
        if con.celdas is None:
            print('AVISO: sin mapa; solo protege el LiDAR, que no ve la escalera')
        giro = {'auto': None, 'izquierda': 1, 'derecha': -1}[a.giro]
        ok, mensaje = con.ejecutar(giro=giro)
        print(mensaje)
        return 0 if ok else 1
    except KeyboardInterrupt:
        print('interrumpido')
        return 1
    finally:
        for _ in range(3):
            con.mandar(0.0, 0.0)
        ejecutor.shutdown()
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
