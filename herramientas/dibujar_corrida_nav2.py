#!/usr/bin/env python3
"""Dibuja una corrida de navegacion sobre su mapa, desde el bag. Deja un PNG.

    dibujar_corrida_nav2.py <bag> <mapa.yaml> <salida.png> [--ns NS] [--titulo T]

Corre en el portatil, con Humble:  source /opt/ros/humble/setup.bash

POR QUE EXISTE
--------------
Cada corrida de campana tiene que dejar una imagen que se vea en el
repositorio, no solo una fila de numeros. Hacerla a mano sobre una captura de
RViz no es repetible: esta herramienta la saca del bag, siempre igual, y la
misma orden vale para la corrida 1 y para la 10.

QUE DIBUJA
----------
  - el mapa, en metros
  - el primer plan de Nav2 (verde discontinuo): lo que el planificador quiso
  - la pose de AMCL a lo largo de la corrida (azul): lo que el carro creyo
  - el rastro de /odom (naranja), ALINEADO en la salida con la primera pose de
    AMCL. /odom vive en otro marco; alinearlo en el primer punto deja ver
    donde divergen las dos estimaciones, que es lo que interesa
  - salida (circulo verde), meta = ultimo punto del ULTIMO plan (X azul), y
    ultima pose de AMCL (circulo rojo)

Pensada para corridas de UNA meta, que es como se hace una campana. En una
mision de varias metas -las de la campana OE4- la meta que marca es la
final; la primera version tomaba la del primer plan y, probada sobre
S21_OE4_01, dio «18,6 m de la meta» con el robot ya camino de la siguiente.

Ninguna de esas trazas es la verdad de terreno: la verdad es la cinta. La
imagen sirve para ver QUE paso; cuanto se equivoco lo dice la cinta.

BAGS DE JAZZY
-------------
El vehiculo graba con metadata version 9, que Humble no sabe leer como
carpeta. Pero SI lee el '.mcap' suelto con la API de rosbag2_py -asi se
recuperaron los barridos de bag_mapa_1456 el 2026-09-01-, y eso es lo que se
hace: si la metadata es version 9, se abre el '.mcap' directamente.
"""
import argparse
import glob
import math
import os
import sys

import numpy as np
import yaml
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from rclpy.serialization import deserialize_message
from rosbag2_py import ConverterOptions, SequentialReader, StorageOptions
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, Path


def yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def abrir(bag):
    """Devuelve un SequentialReader abierto, sea el bag de Humble o de Jazzy."""
    meta = os.path.join(bag, 'metadata.yaml')
    uri, storage = bag, None
    if os.path.isfile(meta):
        with open(meta) as f:
            texto = f.read()
        for linea in texto.splitlines():
            if 'storage_identifier' in linea:
                storage = linea.split(':', 1)[1].strip().strip('"\'')
        if 'version: 9' in texto:
            mcaps = sorted(glob.glob(os.path.join(bag, '*.mcap')))
            if not mcaps:
                raise SystemExit('ERROR: bag de Jazzy sin .mcap dentro: %s' % bag)
            uri, storage = mcaps[0], 'mcap'
    elif bag.endswith('.mcap'):
        storage = 'mcap'
    lector = SequentialReader()
    lector.open(StorageOptions(uri=uri, storage_id=storage or 'sqlite3'),
                ConverterOptions('', ''))
    return lector


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('bag')
    ap.add_argument('mapa', help='YAML del mapa sobre el que se navego')
    ap.add_argument('salida', help='PNG a escribir')
    ap.add_argument('--ns', default='', help='espacio de nombres (simulacion: /robot1)')
    ap.add_argument('--titulo', default='')
    a = ap.parse_args()
    pre = a.ns.rstrip('/')

    amcl, odom, planes = [], [], []
    lector = abrir(a.bag)
    while lector.has_next():
        top, datos, _ = lector.read_next()
        if top == pre + '/amcl_pose':
            m = deserialize_message(datos, PoseWithCovarianceStamped)
            p = m.pose.pose
            amcl.append((p.position.x, p.position.y, yaw_de(p.orientation)))
        elif top == pre + '/odom':
            m = deserialize_message(datos, Odometry)
            p = m.pose.pose
            odom.append((p.position.x, p.position.y, yaw_de(p.orientation)))
        elif top == pre + '/plan':
            m = deserialize_message(datos, Path)
            if m.poses:
                planes.append([(q.pose.position.x, q.pose.position.y) for q in m.poses])

    print('bag: %d poses de AMCL, %d de /odom, %d planes' % (len(amcl), len(odom), len(planes)))
    if not amcl:
        print('ERROR: el bag no trae %s/amcl_pose; no hay nada que situar en el mapa.' % pre)
        return 1

    m = yaml.safe_load(open(a.mapa))
    img = m['image'] if os.path.isabs(m['image']) else \
        os.path.join(os.path.dirname(os.path.abspath(a.mapa)), m['image'])
    res = m['resolution']; ox, oy = m['origin'][0], m['origin'][1]
    mapa = np.array(Image.open(img))
    H, W = mapa.shape
    ext = [ox, ox + W * res, oy, oy + H * res]

    ax_, ay_ = zip(*[(p[0], p[1]) for p in amcl])
    xs = list(ax_); ys = list(ay_)
    for plan in planes[:1]:
        xs += [p[0] for p in plan]; ys += [p[1] for p in plan]
    x0, x1 = min(xs) - 1.5, max(xs) + 1.5
    y0, y1 = min(ys) - 1.5, max(ys) + 1.5

    ancho = 13.0
    alto = max(3.5, min(9.0, ancho * (y1 - y0) / max(x1 - x0, 0.1) + 1.0))
    fig, ax = plt.subplots(figsize=(ancho, alto), dpi=110)
    ax.imshow(mapa, cmap='gray', vmin=0, vmax=255, extent=ext, origin='upper',
              interpolation='nearest')
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    ax.set_xlabel('x en el marco del mapa (m)'); ax.set_ylabel('y (m)')
    ax.grid(color='#4a90d9', alpha=0.25, linewidth=0.6)

    if planes:
        px, py = zip(*planes[0])
        ax.plot(px, py, '--', color='#1b9e3a', lw=2, label='primer plan de Nav2')
        mx, my = planes[-1][-1]
        ax.plot(mx, my, 'X', ms=13, color='#1f5fd6',
                label='meta  (%.2f, %.2f)' % (mx, my))

    if odom:
        # Alinear /odom con la primera pose de AMCL: misma salida, mismo rumbo.
        sx, sy, syaw = amcl[0]
        ox0, oy0, oyaw = odom[0]
        g = syaw - oyaw
        c, s = math.cos(g), math.sin(g)
        tx = [sx + c * (x - ox0) - s * (y - oy0) for x, y, _ in odom]
        ty = [sy + s * (x - ox0) + c * (y - oy0) for x, y, _ in odom]
        ax.plot(tx, ty, '-', color='#f4a261', lw=2, alpha=0.9,
                label='/odom, alineado en la salida')

    ax.plot(ax_, ay_, '.-', color='#1f5fd6', lw=1, ms=5, alpha=0.8, label='pose de AMCL')
    ax.plot(ax_[0], ay_[0], 'o', ms=12, mfc='none', mec='#1b9e3a', mew=3,
            label='salida  (%.2f, %.2f)' % (ax_[0], ay_[0]))
    ax.plot(ax_[-1], ay_[-1], 'o', ms=12, mfc='none', mec='#d62828', mew=3,
            label='última pose de AMCL  (%.2f, %.2f)' % (ax_[-1], ay_[-1]))
    if planes:
        e = math.hypot(ax_[-1] - mx, ay_[-1] - my)
        ax.text(0.99, 0.02, 'distancia de la última pose de AMCL a la meta: %.3f m' % e,
                transform=ax.transAxes, ha='right', fontsize=9,
                bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
    ax.set_title(a.titulo or os.path.basename(os.path.normpath(a.bag)), fontsize=12)
    ax.legend(loc='best', fontsize=8.5, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(a.salida)
    print('escrito %s' % a.salida)
    return 0


if __name__ == '__main__':
    sys.exit(main())
