#!/usr/bin/env python3
"""Media vuelta en dos tiempos: reversa con la direccion a tope y avance con la contraria.

Uso, en el vehiculo, como root, con la particion y el entorno de la cadena, el
puente corriendo y Nav2 SIN meta activa (este programa publica /cmd_vel):

    python3 ~deepracer/tesis/media_vuelta.py --pose 24.25 1.49 0.0
    python3 ~deepracer/tesis/media_vuelta.py --giro derecha --primera 80 --total 170

--pose publica /initialpose ahi y espera a que AMCL converja (sigma < 0,20 m):
hace falta cuando el carro se puso a mano. Sin --pose parte de donde AMCL crea.

El giro se cierra sobre el rumbo de /odom (el filtro con la IMU, que midio
+90,17 grados en un giro de 90 el 2026-10-05). Primer tiempo: marcha atras
hasta --primera grados. Segundo: hacia adelante hasta --total grados en total.
Para antes de llegar porque el carro sigue rodando un poco al soltar. Con
--giro izquierda el carro rota en sentido antihorario: mirando al sur, el primer
tiempo lo lleva hacia el oeste y el segundo lo devuelve al carril, mirando al
norte, unos dos radios mas alla.

POR QUE EXISTE. Con el planificador suponiendo un radio de 0,35 m que el carro
no alcanza, la media vuelta de Nav2 en la salida del piso 4 alternaba adelante
y atras girando en sentidos opuestos y terminaba contra una pared (p4r_11 y
p4r_11b, 2026-10-07). La maniobra en dos tiempos es la que haria una persona.
De paso mide el radio real en cada tiempo (recorrido / angulo), la §3.1 del
plan.

Para en seco si el rumbo va al reves (mas de 15 grados), si un tiempo pasa de
--tope-m metros o de --tope-s segundos, o con Ctrl-C.
"""
import argparse
import math
import sys
import time


def yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def main():
    p = argparse.ArgumentParser(description='Media vuelta en dos tiempos.')
    p.add_argument('--pose', type=float, nargs=3, metavar=('X', 'Y', 'YAW'),
                   help='publica /initialpose ahi (mapa, yaw en radianes) antes de girar')
    p.add_argument('--giro', choices=('izquierda', 'derecha'), default='izquierda',
                   help='sentido de rotacion del carro (izquierda = antihorario)')
    p.add_argument('--primera', type=float, default=80.0, help='grados del tiempo en reversa')
    p.add_argument('--total', type=float, default=170.0, help='grados al terminar el avance')
    p.add_argument('--v', type=float, default=0.4, help='|linear.x|, m/s')
    p.add_argument('--w', type=float, default=1.5, help='|angular.z|, rad/s (1,5 da direccion a tope)')
    p.add_argument('--tope-m', type=float, default=1.8, help='recorrido maximo de cada tiempo')
    p.add_argument('--tope-s', type=float, default=6.0, help='duracion maxima de cada tiempo')
    p.add_argument('--ns', default='', help="espacio de nombres, p. ej. 'robot2'")
    a = p.parse_args()
    pre = f'/{a.ns.strip("/")}' if a.ns.strip('/') else ''
    marco = f'{a.ns.strip("/")}/map' if a.ns.strip('/') else 'map'
    s = 1.0 if a.giro == 'izquierda' else -1.0

    import rclpy
    from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
    from nav_msgs.msg import Odometry
    from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

    rclpy.init()
    nodo = rclpy.create_node('media_vuelta')
    pub = nodo.create_publisher(Twist, f'{pre}/cmd_vel', 10)
    est = {'odom': None, 'sigma': None, 'amcl': None}
    nodo.create_subscription(Odometry, f'{pre}/odom', lambda m: est.__setitem__('odom', m), 20)

    def on_amcl(m):
        c = m.pose.covariance
        est['sigma'] = math.sqrt(max(c[0], 0.0) + max(c[7], 0.0))
        p_ = m.pose.pose
        est['amcl'] = (p_.position.x, p_.position.y, math.degrees(yaw_de(p_.orientation)))
    nodo.create_subscription(PoseWithCovarianceStamped, f'{pre}/amcl_pose', on_amcl,
                             QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                                        reliability=QoSReliabilityPolicy.RELIABLE))
    pub_ini = nodo.create_publisher(PoseWithCovarianceStamped, f'{pre}/initialpose', 10)

    def girar(seg):
        fin = time.monotonic() + seg
        while time.monotonic() < fin:
            rclpy.spin_once(nodo, timeout_sec=0.01)

    def parar():
        for _ in range(5):
            pub.publish(Twist())
            girar(0.02)

    fin = time.monotonic() + 30.0
    while est['odom'] is None and time.monotonic() < fin:
        rclpy.spin_once(nodo, timeout_sec=0.1)
    if est['odom'] is None:
        print(f'ABORTA: no llega {pre}/odom en 30 s')
        return 1
    if pub.get_subscription_count() == 0:
        print(f'ABORTA: nadie escucha {pre}/cmd_vel. ¿Esta el puente corriendo?')
        return 1

    if a.pose:
        m = PoseWithCovarianceStamped()
        m.header.frame_id = marco
        m.pose.pose.position.x, m.pose.pose.position.y = a.pose[0], a.pose[1]
        m.pose.pose.orientation.z = math.sin(a.pose[2] / 2)
        m.pose.pose.orientation.w = math.cos(a.pose[2] / 2)
        # Lo mismo que corrida_nav2.py: 0,10 m y 0,05 rad, lo que se acierta
        # poniendo el carro a mano sobre una marca.
        m.pose.covariance[0] = m.pose.covariance[7] = 0.10 ** 2
        m.pose.covariance[35] = 0.05 ** 2
        limite = time.monotonic() + 10.0
        while pub_ini.get_subscription_count() == 0 and time.monotonic() < limite:
            girar(0.2)
        for _ in range(3):
            m.header.stamp = nodo.get_clock().now().to_msg()
            pub_ini.publish(m)
            girar(0.3)
        print(f'pose inicial publicada: {a.pose[0]:.2f} {a.pose[1]:.2f} {math.degrees(a.pose[2]):.0f} grados')
        limite = time.monotonic() + 20.0
        while (est['sigma'] is None or est['sigma'] >= 0.20) and time.monotonic() < limite:
            girar(0.2)
    else:
        girar(1.0)                      # la ultima pose de AMCL, si la hay
    if est['amcl']:
        x, y, r = est['amcl']
        print(f'AMCL antes: x={x:.2f} y={y:.2f} rumbo={r:.0f} grados (sigma {est["sigma"]:.2f} m)')
    if a.pose and (est['sigma'] is None or est['sigma'] >= 0.20):
        print('ABORTA: AMCL no converge con la pose dada; no se mueve el carro')
        return 1

    def pose():
        o = est['odom'].pose.pose
        return o.position.x, o.position.y, yaw_de(o.orientation)

    _, _, r_ini = pose()
    girado = {'total': 0.0, 'previo': r_ini}

    def actualizar():
        _, _, r = pose()
        girado['total'] += math.atan2(math.sin(r - girado['previo']), math.cos(r - girado['previo']))
        girado['previo'] = r
        return math.degrees(s * girado['total'])     # positivo = en el sentido pedido

    def tiempo(nombre, v, hasta):
        orden = Twist()
        orden.linear.x = v
        orden.angular.z = s * a.w
        x0, y0, _ = pose()
        g0 = actualizar()
        recorrido, (xp, yp) = 0.0, (x0, y0)
        t0 = time.monotonic()
        motivo = 'llego'
        while True:
            pub.publish(orden)
            girar(0.05)
            g = actualizar()
            x, y, _ = pose()
            recorrido += math.hypot(x - xp, y - yp)
            xp, yp = x, y
            if g >= hasta:
                break
            if g < g0 - 15.0:
                motivo = 'ABORTA: el rumbo va al reves'
                break
            if recorrido > a.tope_m:
                motivo = f'ABORTA: mas de {a.tope_m} m sin completar el giro'
                break
            if time.monotonic() - t0 > a.tope_s:
                motivo = f'ABORTA: mas de {a.tope_s} s sin completar el giro'
                break
        parar()
        girar(1.0)                      # lo que rueda al soltar
        g = actualizar()
        x, y, _ = pose()
        recorrido += math.hypot(x - xp, y - yp)
        angulo = abs(math.radians(g - g0))
        radio = recorrido / angulo if angulo > math.radians(10) else float('nan')
        print(f'{nombre}: {g - g0:+.1f} grados en {recorrido:.2f} m y {time.monotonic() - t0:.1f} s '
              f'-> radio {radio:.2f} m  ({motivo})', flush=True)
        return motivo == 'llego'

    ok = False
    try:
        print(f'giro hacia la {a.giro}: reversa hasta {a.primera:.0f} grados, avance hasta {a.total:.0f}', flush=True)
        ok = tiempo('reversa', -abs(a.v), a.primera) and tiempo('avance', abs(a.v), a.total)
    except KeyboardInterrupt:
        print('interrumpido')
    finally:
        parar()
    girar(1.0)
    print(f'girado en total: {math.degrees(s * girado["total"]):.1f} grados')
    if est['amcl']:
        x, y, r = est['amcl']
        print(f'AMCL despues: x={x:.2f} y={y:.2f} rumbo={r:.0f} grados (sigma {est["sigma"]:.2f} m)')
    nodo.destroy_node()
    rclpy.shutdown()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
