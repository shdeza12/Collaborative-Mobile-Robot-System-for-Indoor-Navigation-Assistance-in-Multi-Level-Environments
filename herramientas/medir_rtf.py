#!/usr/bin/env python3
"""Mide el real-time factor de una simulacion de Gazebo desde ROS 2.

No usa 'gz stats' a proposito: gz stats habla con el master de Gazebo por
GAZEBO_MASTER_URI y, con dos instancias, es facil apuntar a la equivocada.
Aqui se mide lo unico que le importa a ROS: cuanto avanza /clock por cada
segundo de reloj de pared. Ese es el numero que contamina o no las metricas
de tiempo del objetivo 4.

Uso:  python3 medir_rtf.py [--topico /clock] [--segundos 20]
      python3 medir_rtf.py --marca            -> imprime "<sim_s> <pared_s>"

EL MODO --marca EXISTE POR UN AGUJERO REAL. El 2026-08-29 las dos misiones de
la condicion A se grabaron sin medir RTF, y al componer el registro el esquema
lo exigio -banco simulacion => rtf numerico- cuando ya no habia forma de
sacarlo del bag: 'ros2 bag record --use-sim-time' sella TODO en tiempo de
simulacion, incluidos 'starting_time' y 'duration' del metadata.yaml, asi que
la razon sim/pared vale 1 por construccion. Medirlo despues mide otra cosa.

--marca da el par (sim, pared) tomado en la MISMA llamada, dentro del mismo
proceso y con microsegundos entre las dos lecturas. Tomando una marca antes de
grabar y otra al cerrar, RTF = dsim/dpared sobre exactamente la ventana de la
mision. El desfase entre el instante en que llega el /clock y el instante en
que se lee el reloj de pared es el mismo en las dos marcas, asi que se cancela
al restar; por eso no se lanzan dos procesos distintos.

Aqui se usa time.time() y no time.monotonic(): monotonic no es comparable
entre procesos, y las dos marcas son dos invocaciones separadas.
"""

import argparse
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from rosgraph_msgs.msg import Clock


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topico', default='/clock')
    ap.add_argument('--segundos', type=float, default=20.0)
    ap.add_argument('--marca', action='store_true',
                    help='imprime "<sim_s> <pared_s>" del primer /clock y sale')
    ap.add_argument('--espera', type=float, default=5.0,
                    help='segundos de espera del primer /clock en modo --marca')
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

    # En modo marca se guarda ademas el reloj de PARED del mismo instante. Las
    # dos lecturas van en la misma linea del callback justamente para que entre
    # una y otra no pase nada medible.
    marca = []

    def cb_marca(msg):
        if not marca:
            marca.append((msg.clock.sec + msg.clock.nanosec * 1e-9, time.time()))

    nodo.create_subscription(Clock, args.topico,
                             cb_marca if args.marca else cb, qos)

    if args.marca:
        inicio = time.monotonic()
        while not marca and time.monotonic() - inicio < args.espera:
            rclpy.spin_once(nodo, timeout_sec=0.1)
        nodo.destroy_node()
        rclpy.shutdown()
        if not marca:
            print(f'SIN DATOS en {args.topico} tras {args.espera:.0f} s.',
                  file=sys.stderr)
            return 1
        print(f'{marca[0][0]:.6f} {marca[0][1]:.6f}')
        return 0

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
