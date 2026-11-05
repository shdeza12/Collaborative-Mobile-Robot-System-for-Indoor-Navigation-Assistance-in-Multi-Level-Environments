#!/usr/bin/env python3
"""Saca el grafo de ROS 2 con el generador de rqt_graph, sin abrir la ventana.

Uso: capturar_grafo_rqt.py CARPETA

Guarda el .dot de cada vista: la lista de nodos y tópicos permite comparar con el diagrama del documento.
"""
import os
import sys
import time

import rclpy
from qt_dotgraph.pydotfactory import PydotFactory
from rqt_graph.dotcode import NODE_NODE_GRAPH, NODE_TOPIC_GRAPH, RosGraphDotcodeGenerator
from rqt_graph.rosgraph2_impl import Graph

salida = sys.argv[1]
rclpy.init()
nodo = rclpy.create_node('captura_rqt_graph')
for _ in range(30):
    rclpy.spin_once(nodo, timeout_sec=0.1)
time.sleep(2)
g = Graph(nodo)
g.set_node_stale(5.0)
g.update()

gen = RosGraphDotcodeGenerator(nodo)
# El nodo de esta captura y el demonio de ros2 no son parte del sistema: se filtran como en el campo de rqt_graph.
FUERA = '-/captura_rqt_graph,-/_ros2cli_daemon.*'
TOPICOS = dict(graph_mode=NODE_TOPIC_GRAPH, hide_single_connection_topics=True, hide_dead_end_topics=True)
VISTAS = {
    # El sistema completo: un recuadro por agente.
    'completo': dict(ns_filter=FUERA, topic_filter='/', cluster_namespaces_level=1, **TOPICOS),
    # Un agente con el coordinador y el puente: el otro agente es igual.
    'un_agente': dict(ns_filter=FUERA + ',-/robot2.*', topic_filter='-/robot2.*', cluster_namespaces_level=1, **TOPICOS),
    # Lo que rqt_graph muestra por omisión.
    'solo_nodos': dict(ns_filter=FUERA, topic_filter='/', graph_mode=NODE_NODE_GRAPH, cluster_namespaces_level=1),
}
for nombre, op in VISTAS.items():
    dot = gen.generate_dotcode(
        rosgraphinst=g, dotcode_factory=PydotFactory(), accumulate_actions=True, orientation='LR', quiet=True,
        unreachable=True, hide_tf_nodes=True, group_tf_nodes=False, group_image_nodes=True,
        hide_dynamic_reconfigure=True, **op)
    with open(os.path.join(salida, f'rqt_{nombre}.dot'), 'w', encoding='utf-8') as f:
        f.write(dot)
    print(nombre, len(dot), flush=True)

nombres = sorted(n for n in nodo.get_node_names_and_namespaces())
with open(os.path.join(salida, 'nodos.txt'), 'w', encoding='utf-8') as f:
    for n, ns in nombres:
        f.write(f"{ns.rstrip('/')}/{n}\n")
with open(os.path.join(salida, 'topicos.txt'), 'w', encoding='utf-8') as f:
    for t, tipos in sorted(nodo.get_topic_names_and_types()):
        f.write(f"{t} {','.join(tipos)}\n")
print('nodos', len(nombres), flush=True)
nodo.destroy_node()
rclpy.shutdown()
