#!/usr/bin/env python3
"""Mide cuanto avanza y cuanto retrocede el vehiculo con la misma orden, para fijar escala_reversa.

Uso, en el vehiculo, como root, con la particion y el entorno del puente, el
puente corriendo y Nav2 SIN meta activa (este programa publica /cmd_vel):

    python3 ~deepracer/tesis/calibrar_reversa.py 0.8 0.7 0.6 [--segundos 1.0] [--v 0.4]

Para cada factor: lo pone en el parametro 'escala_reversa' del puente, da un
empujon hacia adelante y otro hacia atras con la misma |v| y mide con /odom
cuanto se movio en cada uno (durante el empujon y hasta quedar quieto) y la
velocidad maxima. Ida y vuelta: el vehiculo termina cerca de donde empezo.
Al final deja el parametro como estaba; el valor elegido se pone despues.

POR QUE EXISTE. El puente manda la misma magnitud de acelerador en los dos
sentidos, pero el motor no responde igual: en amss-jgm9, con escala 0,9, iba a
~0,6 m/s hacia adelante y a 1,1-1,7 m/s hacia atras (p4r_11, 2026-10-07). Cada
correccion de Nav2 en marcha atras se pasaba de largo, y la media vuelta en la
salida termino contra la pared. Bajar la velocidad de reversa en Nav2 no sirve:
el puente convierte en el mismo escalon cualquier orden por debajo de 1,2 m/s.

Hace falta espacio libre adelante y atras (cerca de 1,5 m) y una persona junto
al vehiculo. Ctrl-C lo para en seco.
"""
import argparse
import math
import sys
import time

PUENTE = '/cmdvel_to_servo_node'


def main():
    p = argparse.ArgumentParser(description='Calibra escala_reversa del puente.')
    p.add_argument('factores', type=float, nargs='+', help='valores de escala_reversa a probar')
    p.add_argument('--segundos', type=float, default=1.0, help='duracion de cada empujon')
    p.add_argument('--v', type=float, default=0.4, help='|linear.x| de cada empujon, m/s')
    p.add_argument('--ns', default='', help="espacio de nombres, p. ej. 'robot2'")
    a = p.parse_args()
    if any(not 0.0 < f <= 1.0 for f in a.factores):
        p.error('cada factor va de 0 (excluido) a 1')
    pre = f'/{a.ns.strip("/")}' if a.ns.strip('/') else ''

    import rclpy
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
    from rcl_interfaces.srv import GetParameters, SetParameters

    rclpy.init()
    nodo = rclpy.create_node('calibrar_reversa')
    pub = nodo.create_publisher(Twist, f'{pre}/cmd_vel', 10)
    odom = {'m': None}
    nodo.create_subscription(Odometry, f'{pre}/odom', lambda m: odom.__setitem__('m', m), 20)
    poner = nodo.create_client(SetParameters, f'{pre}{PUENTE}/set_parameters')
    leer = nodo.create_client(GetParameters, f'{pre}{PUENTE}/get_parameters')

    def girar(seg):
        fin = time.monotonic() + seg
        while time.monotonic() < fin:
            rclpy.spin_once(nodo, timeout_sec=0.01)

    def llamar(cliente, peticion):
        fut = cliente.call_async(peticion)
        fin = time.monotonic() + 10.0
        while not fut.done() and time.monotonic() < fin:
            rclpy.spin_once(nodo, timeout_sec=0.05)
        return fut.result()

    def factor(valor):
        r = llamar(poner, SetParameters.Request(parameters=[Parameter(
            name='escala_reversa',
            value=ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=valor))]))
        return r is not None and r.results[0].successful

    def parar():
        for _ in range(5):
            pub.publish(Twist())
            girar(0.02)

    fin = time.monotonic() + 30.0
    while odom['m'] is None and time.monotonic() < fin:
        rclpy.spin_once(nodo, timeout_sec=0.1)
    if odom['m'] is None:
        print(f'ABORTA: no llega {pre}/odom en 30 s')
        return 1
    if not (poner.wait_for_service(timeout_sec=10.0) and leer.wait_for_service(timeout_sec=10.0)):
        print(f'ABORTA: el puente no ofrece {pre}{PUENTE}/set_parameters. ¿Tiene el codigo con escala_reversa?')
        return 1
    if pub.get_subscription_count() == 0:
        print(f'ABORTA: nadie escucha {pre}/cmd_vel. ¿Esta el puente corriendo?')
        return 1
    r = llamar(leer, GetParameters.Request(names=['escala_reversa']))
    inicial = r.values[0].double_value if r and r.values and r.values[0].type == ParameterType.PARAMETER_DOUBLE else 1.0

    def pose():
        m = odom['m']
        q = m.pose.pose.orientation
        return (m.pose.pose.position.x, m.pose.pose.position.y,
                math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)))

    def empujon(v):
        """(m durante el empujon, m hasta quedar quieto, velocidad maxima), con signo."""
        x0, y0, r0 = pose()
        def avance():
            x, y, _ = pose()
            return (x - x0) * math.cos(r0) + (y - y0) * math.sin(r0)
        orden = Twist()
        orden.linear.x = v
        vmax, fin = 0.0, time.monotonic() + a.segundos
        while time.monotonic() < fin:
            pub.publish(orden)
            girar(0.05)
            vmax = max(vmax, abs(odom['m'].twist.twist.linear.x))
        durante = avance()
        parar()
        fin = time.monotonic() + 2.0
        while time.monotonic() < fin:
            girar(0.05)
            vmax = max(vmax, abs(odom['m'].twist.twist.linear.x))
        return durante, avance(), vmax

    filas = []
    try:
        for f in a.factores:
            if not factor(f):
                print(f'ABORTA: el puente no acepto escala_reversa={f}')
                break
            print(f'escala_reversa {f}: adelante...', flush=True)
            ade = empujon(a.v)
            print(f'escala_reversa {f}: atras...', flush=True)
            atr = empujon(-a.v)
            filas.append((f, ade, atr))
    except KeyboardInterrupt:
        print('interrumpido')
    finally:
        parar()
        factor(inicial)

    print(f'\n|v| = {a.v} m/s durante {a.segundos} s; escala_reversa vuelve a {inicial}')
    print(f'{"factor":>7} {"adelante, m":>12} {"(total)":>8} {"vmax":>6}   {"atras, m":>9} {"(total)":>8} {"vmax":>6}   {"atras/adelante":>14}')
    for f, (d1, t1, v1), (d2, t2, v2) in filas:
        cociente = abs(t2) / abs(t1) if abs(t1) > 0.02 else float('nan')
        print(f'{f:7.2f} {d1:12.3f} {t1:8.3f} {v1:6.2f}   {d2:9.3f} {t2:8.3f} {v2:6.2f}   {cociente:14.2f}')
    nodo.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
