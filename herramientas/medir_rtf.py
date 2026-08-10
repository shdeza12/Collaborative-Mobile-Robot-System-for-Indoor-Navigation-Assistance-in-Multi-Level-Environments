#!/usr/bin/env python3
"""Mide el real-time factor de una simulacion de Gazebo desde ROS 2.

No usa 'gz stats' a proposito: gz stats habla con el master de Gazebo por
GAZEBO_MASTER_URI y, con dos instancias, es facil apuntar a la equivocada.
Aqui se mide lo unico que le importa a ROS: cuanto avanza /clock por cada
segundo de reloj de pared. Ese es el numero que contamina o no las metricas
de tiempo del objetivo 4.

Uso:  python3 medir_rtf.py [--topico /clock] [--segundos 20]
"""

import argparse
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from rosgraph_msgs.msg import Clock


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topico', default='/clock')
    ap.add_argument('--segundos', type=float, default=20.0)
    args = ap.parse_args()

    rclpy.init()
    nodo = Node('medidor_rtf')

    # Gazebo publica /clock con QoS best-effort. Con el perfil por defecto
    # (reliable) la suscripcion es incompatible y no llega nada.
    qos = QoSProfile(depth=10,
                     reliability=QoSReliabilityPolicy.BEST_EFFORT,
                     durability=QoSDurabilityPolicy.VOLATILE)

    muestras = []

    def cb(msg):
        muestras.append((time.monotonic(),
                         msg.clock.sec + msg.clock.nanosec * 1e-9))

    nodo.create_subscription(Clock, args.topico, cb, qos)

    inicio = time.monotonic()
    while time.monotonic() - inicio < args.segundos:
        rclpy.spin_once(nodo, timeout_sec=0.1)

    nodo.destroy_node()
    rclpy.shutdown()

    if len(muestras) < 2:
        print(f'SIN DATOS en {args.topico}: {len(muestras)} mensajes. '
              'La simulacion no publica reloj o esta pausada.')
        return 1

    t0_wall, t0_sim = muestras[0]
    t1_wall, t1_sim = muestras[-1]
    d_wall = t1_wall - t0_wall
    d_sim = t1_sim - t0_sim
    rtf = d_sim / d_wall if d_wall > 0 else 0.0

    print(f'topico      : {args.topico}')
    print(f'mensajes    : {len(muestras)}')
    print(f'wall        : {d_wall:.2f} s')
    print(f'sim         : {d_sim:.2f} s')
    print(f'RTF         : {rtf:.3f}')
    print(f'frecuencia  : {len(muestras)/d_wall:.1f} Hz')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
