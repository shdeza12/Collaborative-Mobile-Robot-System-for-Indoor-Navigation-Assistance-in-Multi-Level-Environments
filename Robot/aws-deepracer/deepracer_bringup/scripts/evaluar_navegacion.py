#!/usr/bin/env python3
"""Evaluacion cuantitativa de la navegacion autonoma sobre el mapa primer_piso.

Envia una bateria de objetivos NavigateToPose y registra, para cada uno,
si se alcanzo, el tiempo de navegacion, el numero de recuperaciones
ejecutadas y el error de posicion final respecto al objetivo.

Uso (con el stack nav_amcl_demo_sim ya activo):
    ros2 run deepracer_bringup evaluar_navegacion.py
    python3 evaluar_navegacion.py --objetivos "3,0;-5,1.5"
"""

import argparse
import math
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose


# Objetivos por defecto, verificados como libres sobre primer_piso.pgm
# con un margen de 0.30 m respecto a celdas ocupadas.
OBJETIVOS_POR_DEFECTO = [
    ("tramo recto corto", 3.0, 0.0),
    ("inversion de sentido", -5.0, 1.5),
    ("recorrido largo oeste", -9.0, 2.0),
    ("recorrido largo este", 8.0, 1.0),
]


class EvaluadorNavegacion(Node):
    def __init__(self):
        super().__init__('evaluador_navegacion')
        self.cliente = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.recuperaciones = 0
        self.distancia_restante = float('nan')

    def _al_recibir_feedback(self, mensaje):
        fb = mensaje.feedback
        self.recuperaciones = fb.number_of_recoveries
        self.distancia_restante = fb.distance_remaining

    def navegar_a(self, x, y, tiempo_limite=180.0):
        """Envia un objetivo y devuelve un dict con las metricas del intento."""
        self.recuperaciones = 0
        self.distancia_restante = float('nan')

        if not self.cliente.wait_for_server(timeout_sec=15.0):
            return {'estado': 'SIN_SERVIDOR', 'duracion': 0.0,
                    'recuperaciones': 0, 'error_final': float('nan')}

        objetivo = NavigateToPose.Goal()
        objetivo.pose = PoseStamped()
        objetivo.pose.header.frame_id = 'map'
        # Se deja el stamp en cero a proposito: Nav2 lo interpreta como "ahora"
        # y evita el desfase entre reloj de pared y tiempo de simulacion.
        objetivo.pose.pose.position.x = float(x)
        objetivo.pose.pose.position.y = float(y)
        objetivo.pose.pose.orientation.w = 1.0

        inicio = time.time()
        futuro_envio = self.cliente.send_goal_async(
            objetivo, feedback_callback=self._al_recibir_feedback)
        rclpy.spin_until_future_complete(self, futuro_envio, timeout_sec=20.0)

        handle = futuro_envio.result()
        if handle is None or not handle.accepted:
            return {'estado': 'RECHAZADO', 'duracion': time.time() - inicio,
                    'recuperaciones': 0, 'error_final': float('nan')}

        futuro_resultado = handle.get_result_async()
        rclpy.spin_until_future_complete(
            self, futuro_resultado, timeout_sec=tiempo_limite)

        duracion = time.time() - inicio
        if not futuro_resultado.done():
            handle.cancel_goal_async()
            estado = 'TIEMPO_AGOTADO'
        else:
            # 4 = SUCCEEDED, 6 = ABORTED, 5 = CANCELED
            estado = {4: 'ALCANZADO', 5: 'CANCELADO',
                      6: 'ABORTADO'}.get(futuro_resultado.result().status,
                                         f'CODIGO_{futuro_resultado.result().status}')

        return {'estado': estado, 'duracion': duracion,
                'recuperaciones': self.recuperaciones,
                'error_final': self.distancia_restante}


def analizar_objetivos(texto):
    objetivos = []
    for i, par in enumerate(t for t in texto.split(';') if t.strip()):
        x, y = par.split(',')
        objetivos.append((f'objetivo {i + 1}', float(x), float(y)))
    return objetivos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--objetivos', default=None,
                        help='Lista "x1,y1;x2,y2" en el marco map')
    parser.add_argument('--limite', type=float, default=180.0,
                        help='Tiempo limite por objetivo, en segundos')
    args = parser.parse_args()

    objetivos = (analizar_objetivos(args.objetivos) if args.objetivos
                 else OBJETIVOS_POR_DEFECTO)

    rclpy.init()
    evaluador = EvaluadorNavegacion()

    filas = []
    for nombre, x, y in objetivos:
        evaluador.get_logger().info(f'Enviando objetivo "{nombre}" -> ({x}, {y})')
        r = evaluador.navegar_a(x, y, tiempo_limite=args.limite)
        filas.append((nombre, x, y, r))
        evaluador.get_logger().info(
            f'  {r["estado"]} en {r["duracion"]:.1f} s, '
            f'{r["recuperaciones"]} recuperaciones')

    print('\n' + '=' * 78)
    print(f'{"Objetivo":<24}{"Destino":<14}{"Estado":<16}'
          f'{"t [s]":>8}{"recup.":>8}{"err [m]":>9}')
    print('-' * 78)
    alcanzados = 0
    for nombre, x, y, r in filas:
        if r['estado'] == 'ALCANZADO':
            alcanzados += 1
        err = r['error_final']
        err_txt = 'n/d' if math.isnan(err) else f'{err:.2f}'
        print(f'{nombre:<24}{f"({x}, {y})":<14}{r["estado"]:<16}'
              f'{r["duracion"]:>8.1f}{r["recuperaciones"]:>8}{err_txt:>9}')
    print('-' * 78)
    print(f'Tasa de exito: {alcanzados}/{len(filas)} '
          f'({100.0 * alcanzados / len(filas):.0f} %)')
    print('=' * 78)

    evaluador.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
