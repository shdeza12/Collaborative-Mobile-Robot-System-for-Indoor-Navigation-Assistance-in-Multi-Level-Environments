#!/usr/bin/env python3
"""Figuras del documento final: la arquitectura del sistema en simulación y en los vehículos.

Las dos tienen la misma estructura (interfaz, coordinador, dos agentes y la escalera donde ocurre el
relevo) para que se lean una contra la otra; lo que cambia es la implementación de cada bloque, que
el documento resume en la tabla de la sección «De la simulación a los vehículos».

Uso, desde la raíz del repositorio:
    python3 herramientas/figura_arquitectura.py
Escribe arquitectura_simulacion.png y arquitectura_vehiculos.png en Documentos/DocumentoFinal/imagenes/
y una copia de cada una en sitio/paginas/img/.
"""
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parent.parent
IMAGENES = RAIZ / 'Documentos/DocumentoFinal/imagenes'
SITIO = RAIZ / 'sitio/paginas/img'

TINTA, TINTA2, GRIS = '#0b0b0b', '#52514e', '#8a8984'
AZUL, AZUL_FONDO = '#2a78d6', '#e9f1fb'
NARANJA, NARANJA_FONDO = '#eb6834', '#fdeee6'
AGENTE_FONDO, MODULO_BORDE = '#f4f4f2', '#b9b8b3'

SIMULACION = {
    'archivo': 'arquitectura_simulacion.png',
    'interfaz': ['En el navegador del teléfono', 'Pide, confirma y cancela'],
    'coordinador': ('Coordinador', ['Asigna un agente por piso y organiza el relevo',
                                    'Portátil · Ubuntu 22.04 · ROS 2 Humble']),
    'enlace': 'Metas de navegación y estado',
    'agentes': [('Agente del piso 1', 'Proceso propio de Gazebo 11 · ROS 2 Humble'),
                ('Agente del piso 2', 'Proceso propio de Gazebo 11 · ROS 2 Humble')],
    'modulos': [('Sensado', ['Láser simulado', 'de 10 m de alcance']),
                ('Odometría', ['La que entrega', 'el simulador']),
                ('Localización', ['AMCL sobre un mapa', 'calculado del mundo']),
                ('Navegación', ['Nav2: Smac híbrido y', 'persecución pura']),
                ('Locomoción', ['Complemento Ackermann', 'de Gazebo y ros2_control']),
                ('Comunicación', ['Un computador, un dominio;', 'espacio de nombres propio'])],
    'escalera': 'La cruza el usuario · llegada a 0,25 m',
}

VEHICULOS = {
    'archivo': 'arquitectura_vehiculos.png',
    'interfaz': ['En el navegador del teléfono', 'Pide, confirma y cancela'],
    'coordinador': ('Portátil (Ubuntu 22.04)', ['Coordinador y grabador: ROS 2 Jazzy, en un contenedor',
                                                'rosbridge y página: ROS 2 Humble']),
    'enlace': 'Metas, media vuelta y estado',
    'agentes': [('Vehículo del piso 3', 'Tarjeta Intel Atom · Ubuntu 24.04 · ROS 2 Jazzy'),
                ('Vehículo del piso 4', 'Tarjeta Intel Atom · Ubuntu 24.04 · ROS 2 Jazzy')],
    'modulos': [('Sensado', ['RPLIDAR A1M8 y unidad', 'inercial; cámaras apagadas']),
                ('Odometría', ['Del láser (rf2o) con la', 'unidad inercial, con filtro']),
                ('Localización', ['AMCL sobre el mapa', 'de la planta medida']),
                ('Navegación', ['Nav2 como en simulación,', 'y media vuelta propia']),
                ('Locomoción', ['Puente a los servos,', 'con escala por vehículo']),
                ('Comunicación', ['Wi-Fi de 5 GHz; partición', 'propia; solo con el portátil'])],
    'escalera': 'Llegada verificada a 0,5 m, 1,5 s después',
}


def caja(ax, x, y, w, h, fondo, borde, grosor=0.8, radio=1.2, estilo='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radio}',
                                facecolor=fondo, edgecolor=borde, linewidth=grosor, linestyle=estilo))


def texto(ax, x, y, s, tam=6.8, peso='normal', color=TINTA2, **kw):
    ax.text(x, y, s, fontsize=tam, fontweight=peso, color=color, ha='center', va='center', **kw)


def flecha(ax, puntos, doble=True, discontinua=False):
    xs, ys = zip(*puntos)
    ax.plot(xs[:-1] + (xs[-1],), ys, color=GRIS, lw=0.8, ls=(0, (3, 2)) if discontinua else '-',
            solid_capstyle='butt')
    ax.annotate('', xy=puntos[-1], xytext=puntos[-2],
                arrowprops=dict(arrowstyle='-|>', color=GRIS, lw=0.8, mutation_scale=7, shrinkA=0, shrinkB=0))
    if doble:
        ax.annotate('', xy=puntos[0], xytext=puntos[1],
                    arrowprops=dict(arrowstyle='-|>', color=GRIS, lw=0.8, mutation_scale=7, shrinkA=0, shrinkB=0))


def figura(d):
    fig = plt.figure(figsize=(6.5, 5.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.axis('off')

    # Interfaz y coordinador.
    caja(ax, 2, 64, 28, 14, AZUL_FONDO, AZUL)
    texto(ax, 16, 74.6, 'Interfaz web', 8, 'bold', TINTA)
    texto(ax, 16, 70.6, d['interfaz'][0])
    texto(ax, 16, 67.6, d['interfaz'][1])
    titulo, lineas = d['coordinador']
    caja(ax, 44, 62, 54, 16, AZUL_FONDO, AZUL)
    texto(ax, 71, 74.6, titulo, 8, 'bold', TINTA)
    texto(ax, 71, 70.2, lineas[0])
    texto(ax, 71, 66.6, lineas[1])
    flecha(ax, [(30.4, 71), (43.6, 71)])
    texto(ax, 37, 73.2, 'rosbridge', 6.3, color=GRIS)

    # Coordinador -> agentes.
    flecha(ax, [(58, 61.6), (58, 57.5), (25.5, 57.5), (25.5, 53.4)])
    flecha(ax, [(84, 61.6), (84, 57.5), (74.5, 57.5), (74.5, 53.4)])
    texto(ax, 40.5, 59.3, d['enlace'], 6.3, color=GRIS)

    # Agentes, con sus seis módulos en dos columnas.
    for k, (nombre, base) in enumerate(d['agentes']):
        x0 = 2 + k * 49
        caja(ax, x0, 14, 47, 39, AGENTE_FONDO, TINTA2, radio=1.6)
        texto(ax, x0 + 23.5, 49.6, nombre, 8, 'bold', TINTA)
        texto(ax, x0 + 23.5, 46.2, base, 6.5)
        for i, (modulo, contenido) in enumerate(d['modulos']):
            fila, col = divmod(i, 2)
            mx, my = x0 + 1.8 + col * 22.2, 34.2 - fila * 9.4
            caja(ax, mx, my, 21.2, 8.6, 'white', MODULO_BORDE, 0.6, 0.8)
            texto(ax, mx + 10.6, my + 6.5, modulo, 6.8, 'bold', TINTA)
            texto(ax, mx + 10.6, my + 4.0, contenido[0], 6.2)
            texto(ax, mx + 10.6, my + 1.8, contenido[1], 6.2)

    # Escalera: el usuario la cruza, ningún robot.
    caja(ax, 32, 2.2, 36, 9, NARANJA_FONDO, NARANJA)
    texto(ax, 50, 8.3, 'Escalera: punto de relevo', 8, 'bold', TINTA)
    texto(ax, 50, 4.7, d['escalera'], 6.5)
    flecha(ax, [(25.5, 13.6), (25.5, 6.7), (31.6, 6.7)], doble=False, discontinua=True)
    flecha(ax, [(74.5, 13.6), (74.5, 6.7), (68.4, 6.7)], doble=False, discontinua=True)
    texto(ax, 16, 6.7, 'Entrega al usuario', 6.3, color=GRIS)
    texto(ax, 84, 6.7, 'Recibe al usuario', 6.3, color=GRIS)

    destino = IMAGENES / d['archivo']
    fig.savefig(destino, dpi=300)
    plt.close(fig)
    shutil.copy(destino, SITIO / d['archivo'])
    print(destino.relative_to(RAIZ))


if __name__ == '__main__':
    figura(SIMULACION)
    figura(VEHICULOS)
