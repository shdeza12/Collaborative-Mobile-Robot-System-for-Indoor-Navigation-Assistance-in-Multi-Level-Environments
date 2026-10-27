#!/usr/bin/env python3
"""Figuras del documento final: tres diagramas de bloques.

  nodos_sistema.png     los nodos de ROS 2 del sistema en la campaña con los agentes físicos y lo que
                        circula entre ellos (sección del contrato de interfaces);
  planificador.png      la función que planifica una misión a partir del catálogo, el origen y el
                        destino (sección del planificador);
  instrumentacion.png   cómo el coordinador verifica la llegada y cómo una misión se convierte en
                        registro y en métricas (sección de instrumentación).

Mismas cajas, colores y tamaños de letra que figura_arquitectura.py, para que las figuras del
documento se lean como una sola familia: a 6,5 pulgadas de ancho, la página las reproduce casi a
escala. Los nombres de nodos y tópicos son los del código: el lanzador
deepracer_bringup/launch/nav2_hardware.launch.py, herramientas/nav2_mapa_guardado.sh, los nodos del
paquete coordinacion y coordinacion/coordinacion/planificador.py.

Uso, desde la raíz del repositorio:
    python3 herramientas/figura_diagramas.py
Escribe las tres imágenes en Documentos/DocumentoFinal/imagenes/.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

RAIZ = Path(__file__).resolve().parent.parent
IMAGENES = RAIZ / 'Documentos/DocumentoFinal/imagenes'

TINTA, TINTA2, GRIS = '#0b0b0b', '#52514e', '#8a8984'
AZUL, AZUL_FONDO = '#2a78d6', '#e9f1fb'
NARANJA, NARANJA_FONDO = '#eb6834', '#fdeee6'
AGENTE_FONDO, MODULO_BORDE = '#f4f4f2', '#b9b8b3'
PUNTA = dict(arrowstyle='-|>', color=GRIS, lw=0.75, mutation_scale=6.5, shrinkA=0, shrinkB=0)


def lienzo(alto):
    """Ejes de 100 unidades de ancho y `alto` de alto, con unidades cuadradas."""
    fig = plt.figure(figsize=(6.5, 6.5 * alto / 100))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, alto)
    ax.axis('off')
    return fig, ax


def caja(ax, x, y, w, h, fondo='white', borde=MODULO_BORDE, grosor=0.7, radio=0.9, estilo='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radio}',
                                facecolor=fondo, edgecolor=borde, linewidth=grosor, linestyle=estilo))


def texto(ax, x, y, s, tam=6.4, peso='normal', color=TINTA, ha='center', fondo=None):
    marco = dict(boxstyle='square,pad=0.08', facecolor=fondo, edgecolor='none') if fondo else None
    ax.text(x, y, s, fontsize=tam, fontweight=peso, color=color, ha=ha, va='center',
            linespacing=1.15, bbox=marco)


def nodo(ax, x, y, w, h, s, fondo='white', borde=MODULO_BORDE, grosor=0.7, estilo='-', tam=6.4):
    caja(ax, x, y, w, h, fondo, borde, grosor, estilo=estilo)
    texto(ax, x + w / 2, y + h / 2, s, tam)


def rombo(ax, cx, cy, mw, mh, s, tam=6.0):
    ax.add_patch(Polygon([(cx - mw, cy), (cx, cy + mh), (cx + mw, cy), (cx, cy - mh)], closed=True,
                         facecolor='white', edgecolor=MODULO_BORDE, linewidth=0.7))
    texto(ax, cx, cy, s, tam)


def linea(ax, puntos, flecha=True, doble=False, discontinua=False):
    xs, ys = zip(*puntos)
    ax.plot(xs, ys, color=GRIS, lw=0.75, ls=(0, (3, 2)) if discontinua else '-', solid_capstyle='butt')
    if flecha:
        ax.annotate('', xy=puntos[-1], xytext=puntos[-2], arrowprops=PUNTA)
    if doble:
        ax.annotate('', xy=puntos[0], xytext=puntos[1], arrowprops=PUNTA)


def etiqueta(ax, x, y, s, ha='center', fondo=None):
    texto(ax, x, y, s, 5.9, color=TINTA2, ha=ha, fondo=fondo)


def guardar(fig, nombre):
    destino = IMAGENES / nombre
    fig.savefig(destino, dpi=300)
    plt.close(fig)
    print(destino.relative_to(RAIZ))


# ------------------------------------------------------------------ nodos del sistema
def nodos():
    fig, ax = lienzo(75)

    # Teléfono.
    caja(ax, 1, 53.5, 12.5, 19.5, AZUL_FONDO, AZUL, 0.9, 1.2)
    texto(ax, 7.25, 70.4, 'Teléfono', 7.2, 'bold')
    nodo(ax, 2.4, 55.5, 9.7, 12.0, 'Página\nweb')

    # Portátil, con sus dos entornos de ROS 2.
    caja(ax, 21, 51.5, 78, 22.5, AZUL_FONDO, AZUL, 0.9, 1.2)
    texto(ax, 60, 71.7, 'Portátil · Ubuntu 22.04', 7.2, 'bold')
    caja(ax, 23, 53, 20.5, 16.2, AZUL_FONDO, AZUL, 0.6, 0.9, '--')
    texto(ax, 33.25, 67.3, 'ROS 2 Humble', 5.9, color=TINTA2)
    nodo(ax, 24.3, 59.8, 18, 5.4, 'rosbridge_websocket')
    nodo(ax, 24.3, 54.0, 18, 5.0, 'servidor HTTP\nde la página')
    caja(ax, 55, 53, 42, 16.2, AZUL_FONDO, AZUL, 0.6, 0.9, '--')
    texto(ax, 76, 67.3, 'Contenedor con ROS 2 Jazzy', 5.9, color=TINTA2)
    nodo(ax, 57, 57.6, 17, 6.4, 'coordinador', borde=AZUL, grosor=1.3)
    nodo(ax, 80, 57.6, 15, 6.4, 'grabador\n(ros2 bag)')

    linea(ax, [(12.1, 63.4), (24.3, 63.4)], doble=True)
    etiqueta(ax, 17.2, 64.8, 'WebSocket')
    linea(ax, [(24.3, 56.5), (12.1, 56.5)], discontinua=True)
    etiqueta(ax, 17.2, 57.9, 'HTTP')
    linea(ax, [(42.3, 63.3), (57, 63.3)])
    etiqueta(ax, 49.6, 66.0, 'guiar_usuario\nconfirmacion_piso', fondo=AZUL_FONDO)
    linea(ax, [(57, 60.6), (42.3, 60.6)])
    etiqueta(ax, 49.6, 57.7, 'estado_mision\npuntos_interes', fondo=AZUL_FONDO)
    linea(ax, [(74, 60.8), (80, 60.8)], discontinua=True)
    etiqueta(ax, 77, 62.4, 'tópicos', fondo=AZUL_FONDO)

    # Agente: el de cada piso es igual.
    caja(ax, 1, 1, 98, 43, AGENTE_FONDO, TINTA2, 0.9, 1.4)
    texto(ax, 3, 41.2, 'Agente de un piso · Ubuntu 24.04 · ROS 2 Jazzy', 7.2, 'bold', ha='left')
    a, b, c, d = 32.5, 22.5, 12.5, 2.8          # filas
    alto = 5
    nodo(ax, 2.5, a, 14, alto, 'láser RPLIDAR', estilo='--')
    nodo(ax, 22.5, a, 17.5, alto, 'rf2o_laser_odometry')
    nodo(ax, 51, a, 14, alto, 'agente', borde=AZUL, grosor=1.3)
    nodo(ax, 69, a, 13, alto, 'bt_navigator')
    nodo(ax, 85, a, 13, alto, 'behavior_server')
    nodo(ax, 2.5, b, 14, alto, 'imu_bmi160')
    nodo(ax, 22.5, b, 17.5, alto, 'ekf_filter_node')
    nodo(ax, 45, b, 12, alto, 'amcl')
    nodo(ax, 62, b, 15, alto, 'planner_server\n(Smac híbrido)')
    nodo(ax, 80, b, 18, alto, 'controller_server\n(Regulated Pure Pursuit)', tam=6.0)
    nodo(ax, 45, c, 12, alto, 'map_server')
    nodo(ax, 80, c, 18, alto, 'cmdvel_to_servo')
    nodo(ax, 80, d, 18, alto + 0.4, 'servos de tracción\ny dirección', estilo='--')

    # Coordinador <-> agente.
    linea(ax, [(58.5, a + alto), (58.5, 57.6)])
    linea(ax, [(62, 57.6), (62, a + alto)])
    linea(ax, [(73.2, 57.6), (73.2, a + alto)])
    etiqueta(ax, 57.8, 47.4, 'estado\n(2 Hz)', ha='right')
    etiqueta(ax, 62.7, 47.4, 'media_vuelta\n(servicio)', ha='left')
    etiqueta(ax, 73.9, 47.4, 'navigate_to_pose\n(acción)', ha='left')

    # Dentro del agente.
    linea(ax, [(16.5, a + 2.5), (22.5, a + 2.5)])                     # láser -> rf2o
    etiqueta(ax, 19.5, a + 3.9, 'scan')
    linea(ax, [(9.5, a), (9.5, 29.6), (89, 29.6), (89, b + alto)])    # bus del láser -> controller
    linea(ax, [(48, 29.6), (48, b + alto)])                           # ... -> amcl
    linea(ax, [(52.5, 29.6), (52.5, a)])                              # ... -> agente
    etiqueta(ax, 10.6, 30.7, 'scan', ha='left')
    linea(ax, [(31.25, a), (31.25, b + alto)])                        # rf2o -> ekf
    etiqueta(ax, 32.0, 28.4, 'odom_rf2o', ha='left', fondo=AGENTE_FONDO)
    linea(ax, [(16.5, b + 2.5), (22.5, b + 2.5)])                     # imu -> ekf
    etiqueta(ax, 19.5, b + 3.9, 'imu/data')
    linea(ax, [(40, b + 2.5), (45, b + 2.5)])                         # ekf -> amcl
    etiqueta(ax, 42.5, b + 3.9, 'odom')
    linea(ax, [(51, c + alto), (51, b)])                              # map_server -> amcl
    etiqueta(ax, 50.3, 19.9, 'map', ha='right')
    linea(ax, [(57, c + 2.5), (70, c + 2.5), (70, b)])                # map_server -> planner
    etiqueta(ax, 63.5, c + 3.9, 'map')
    linea(ax, [(56.2, b + alto), (56.2, a)])                          # amcl -> agente
    etiqueta(ax, 56.7, 28.5, 'pose', ha='left', fondo=AGENTE_FONDO)
    linea(ax, [(72.5, a), (72.5, b + alto)])                          # bt -> planner
    etiqueta(ax, 73.2, 30.8, 'ruta', ha='left', fondo=AGENTE_FONDO)
    linea(ax, [(79, a), (84, b + alto)])                              # bt -> controller
    linea(ax, [(82, a + 2.5), (85, a + 2.5)])                         # bt -> behavior
    linea(ax, [(89, b), (89, c + alto)])                              # controller -> puente
    etiqueta(ax, 89.7, 19.9, 'cmd_vel', ha='left')
    linea(ax, [(60.5, a), (60.5, 19.8), (83, 19.8), (83, c + alto)])  # agente -> puente
    etiqueta(ax, 65.2, 21.0, 'cmd_vel')
    linea(ax, [(89, c), (89, d + alto + 0.4)])                        # puente -> servos
    etiqueta(ax, 89.7, 9.8, 'PWM', ha='left')

    guardar(fig, 'nodos_sistema.png')


# ------------------------------------------------------------------ planificador
def planificador():
    fig, ax = lienzo(50)
    nodo(ax, 27, 43, 46, 6.5, 'Catálogo de puntos de interés, origen y destino pedidos,\n'
                              'y el agente asignado a cada nivel', AZUL_FONDO, AZUL, 0.9)
    rombo(ax, 50, 36.5, 17, 4.6, '¿Los dos puntos existen, son\ndistintos y su nivel tiene agente?', 5.8)
    nodo(ax, 75, 32.6, 24, 7.8, 'Error de planificación con el\nmotivo redactado; ningún\nagente se mueve',
         NARANJA_FONDO, NARANJA, 0.9, tam=6.0)
    rombo(ax, 50, 24.5, 10, 4, '¿Mismo nivel?')
    rombo(ax, 82, 24.5, 14.5, 4.5, '¿Los dos niveles tienen\nagentes distintos?', 5.8)
    nodo(ax, 1, 8.6, 36, 9.2, 'Dos tramos del mismo agente:\n1. va al origen a recoger al usuario\n'
                              '2. lo guía hasta el destino\n0 relevos', tam=6.0)
    nodo(ax, 58, 6.6, 41, 11.2, 'Cuatro tramos:\n1. el agente del nivel de origen va al origen\n'
                               '2. guía al usuario hasta la escalera de su nivel\n'
                               '3. el agente del otro nivel va a su escalera\n'
                               '4. guía al usuario hasta el destino\n1 relevo', tam=6.0)
    nodo(ax, 24, 0.5, 30, 6.2, 'Plan: lista de tramos y\nnúmero de relevos', AZUL_FONDO, AZUL, 0.9, tam=6.0)

    linea(ax, [(50, 43), (50, 41.1)])
    linea(ax, [(67, 36.5), (75, 36.5)])
    etiqueta(ax, 71, 37.8, 'no')
    linea(ax, [(50, 31.9), (50, 28.5)])
    etiqueta(ax, 51.2, 30.2, 'sí', ha='left')
    linea(ax, [(40, 24.5), (19, 24.5), (19, 17.8)])
    etiqueta(ax, 30, 25.8, 'sí')
    linea(ax, [(60, 24.5), (67.5, 24.5)])
    etiqueta(ax, 63.7, 25.8, 'no')
    linea(ax, [(82, 29), (82, 32.6)])
    etiqueta(ax, 83, 30.8, 'no', ha='left')
    linea(ax, [(82, 20), (82, 17.8)])
    etiqueta(ax, 83, 18.9, 'sí', ha='left')
    linea(ax, [(13, 8.6), (13, 3.6), (24, 3.6)])
    linea(ax, [(88, 6.6), (88, 3.6), (54, 3.6)])
    etiqueta(ax, 71, 1.9, 'los tramos seguidos del mismo agente\nal mismo punto se funden en uno')
    guardar(fig, 'planificador.png')


# ------------------------------------------------------------------ instrumentación
def instrumentacion():
    fig, ax = lienzo(47)

    caja(ax, 1, 23, 98, 23, AGENTE_FONDO, TINTA2, 0.9, 1.4)
    texto(ax, 3, 43.6, 'Durante la misión, con los agentes físicos', 7.2, 'bold', ha='left')
    fila = 33.5
    nodo(ax, 5, fila, 14, 6.5, 'Nav2 da la meta\npor alcanzada')
    nodo(ax, 22.5, fila, 14.5, 6.5, 'el coordinador\nespera 1,5 s')
    nodo(ax, 40.5, fila, 16, 6.5, 'lee la pose que\npublica el agente')
    rombo(ax, 68, fila + 3.25, 9.5, 5.2, '¿a 0,5 m o\nmenos del\npunto?', 5.8)
    nodo(ax, 82, fila + 4.6, 16, 6, 'llegada aceptada:\nsigue la misión', AZUL_FONDO, AZUL, 0.9)
    nodo(ax, 82, fila - 4.1, 16, 6, 'llegada rechazada:\nmisión fallida', NARANJA_FONDO, NARANJA, 0.9)
    nodo(ax, 22.5, 25, 34, 6.2, 'grabador (ros2 bag), en el contenedor con Jazzy:\n'
                                'etapas, poses, planes y órdenes de los agentes', tam=6.0)
    linea(ax, [(19, fila + 3.25), (22.5, fila + 3.25)])
    linea(ax, [(37, fila + 3.25), (40.5, fila + 3.25)])
    linea(ax, [(56.5, fila + 3.25), (58.5, fila + 3.25)])
    linea(ax, [(77.5, fila + 3.25), (79.6, fila + 3.25), (79.6, fila + 7.6), (82, fila + 7.6)])
    etiqueta(ax, 80.8, fila + 8.9, 'sí')
    linea(ax, [(79.6, fila + 3.25), (79.6, fila - 1.1), (82, fila - 1.1)])
    etiqueta(ax, 80.8, fila - 2.4, 'no')

    caja(ax, 1, 1, 98, 19.5, AGENTE_FONDO, TINTA2, 0.9, 1.4)
    texto(ax, 5, 18.1, 'Después de la misión', 7.2, 'bold', ha='left')
    f2 = 8.2
    nodo(ax, 5, f2, 15, 7, 'conversión de la\ngrabación al formato\nque lee Humble', tam=6.0)
    nodo(ax, 23.5, f2, 19.5, 7, 'composición del registro:\nreloj del portátil, mapa\ndel piso y tolerancia', tam=6.0)
    nodo(ax, 46.5, f2, 15.5, 7, 'registro de la\nmisión, validado\ncontra el esquema', tam=6.0)
    nodo(ax, 65.5, f2, 15.5, 7, 'analizador:\nintegridad y cuatro\nmétricas con intervalo', tam=6.0)
    nodo(ax, 84.5, f2, 13.5, 7, 'métricas y\nveredicto de\nla campaña', AZUL_FONDO, AZUL, 0.9, tam=6.0)
    nodo(ax, 46.5, 2.3, 15.5, 4.2, 'medida con flexómetro,\nsi la hay', estilo='--', tam=5.6)
    linea(ax, [(22.5, 28.1), (2.6, 28.1), (2.6, f2 + 3.5), (5, f2 + 3.5)])
    linea(ax, [(20, f2 + 3.5), (23.5, f2 + 3.5)])
    linea(ax, [(43, f2 + 3.5), (46.5, f2 + 3.5)])
    linea(ax, [(62, f2 + 3.5), (65.5, f2 + 3.5)])
    linea(ax, [(81, f2 + 3.5), (84.5, f2 + 3.5)])
    linea(ax, [(54.25, 6.5), (54.25, f2)], discontinua=True)
    guardar(fig, 'instrumentacion.png')


if __name__ == '__main__':
    nodos()
    planificador()
    instrumentacion()
