#!/usr/bin/env python3
"""Figuras del documento final: la red que comunica los dos agentes.

Son dos y se leen juntas:

  red_topologia.png    el montaje fisico -- enrutador, un punto de acceso por
                       piso unidos por cable, y un agente colgando de cada uno.
                       Complementa a arquitectura_vehiculos.png, que es el
                       diagrama logico: quien habla con quien. Esta dice por
                       donde pasa.

  red_carga.png        lo que el esquema de descubrimiento le cuesta a la
                       tarjeta. Es el resultado de red mas importante del
                       proyecto: con dos cadenas anunciandose por difusion la
                       tarjeta se satura y Nav2 no arranca.

Mismo estilo que figura_arquitectura.py (colores, cajas redondeadas, tamanos).

Uso, desde la raiz del repositorio:
    python3 herramientas/figura_red.py
Escribe las dos en Documentos/DocumentoFinal/imagenes/ y copia a sitio/paginas/img/.
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
VERDE, VERDE_FONDO = '#2f8f5b', '#e8f4ed'
AGENTE_FONDO, MODULO_BORDE = '#f4f4f2', '#b9b8b3'


def caja(ax, x, y, w, h, fondo, borde, grosor=0.8, radio=1.2, estilo='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radio}',
                                facecolor=fondo, edgecolor=borde, linewidth=grosor, linestyle=estilo))


def texto(ax, x, y, s, tam=6.8, peso='normal', color=TINTA2, **kw):
    ax.text(x, y, s, fontsize=tam, fontweight=peso, color=color, ha='center', va='center', **kw)


def linea(ax, puntos, discontinua=False, grosor=0.9, color=GRIS):
    xs, ys = zip(*puntos)
    ax.plot(xs, ys, color=color, lw=grosor, ls=(0, (3, 2)) if discontinua else '-',
            solid_capstyle='round', zorder=1)


def topologia():
    """El montaje fisico: por donde pasan de verdad los mensajes, con la direccion
    IP de cada equipo. Desde el 11 de noviembre va sin las direcciones MAC, por
    correccion de los autores: no hacen falta para leer el montaje.

    El enrutador esta en el piso 4, junto al punto de acceso de ese piso, y del
    piso 4 sale el cable al punto de acceso del piso 3 (confirmado por los
    autores el 6 de noviembre). Los puntos de acceso van sin IP y el telefono
    sin direcciones, por decision de los autores.
    """
    fig = plt.figure(figsize=(6.5, 5.3))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 82)
    ax.axis('off')

    # Enrutador, arriba y al centro: reparte direcciones para todos.
    caja(ax, 23, 61, 54, 19, AZUL_FONDO, AZUL)
    texto(ax, 50, 76.6, 'Enrutador TP-Link TL-WR940N · piso 4', 8, 'bold', TINTA)
    texto(ax, 50, 73.0, 'IP 192.168.0.1/24', 6.4, color=TINTA)
    texto(ax, 50, 69.6, 'Reparte las direcciones de toda la red', 6.4)
    texto(ax, 50, 66.4, 'Enlace de respaldo DEEPRACER en 2,4 GHz, canal 6', 6.4)

    # El telefono y el portatil se asocian al punto de acceso de 5 GHz de su piso
    # (confirmado por los autores el 12 de noviembre); el enlace de 2,4 GHz del
    # enrutador queda solo como respaldo. Se dibujan sobre el punto de acceso del
    # piso 3 y del piso 4, pero cada uno usa el del piso en que esta.
    caja(ax, 2, 64, 17, 13, AGENTE_FONDO, TINTA2, radio=1.6)
    texto(ax, 10.5, 72.6, 'Teléfono', 7.6, 'bold', TINTA)
    texto(ax, 10.5, 68.8, 'Interfaz web', 6.2)
    linea(ax, [(10.5, 63.6), (10.5, 51.4)], discontinua=True)
    texto(ax, 6.2, 57.6, 'Wi-Fi\n5 GHz', 5.6, color=GRIS)
    caja(ax, 81, 61, 17, 19, AGENTE_FONDO, TINTA2, radio=1.6)
    texto(ax, 89.5, 76.0, 'Portátil', 7.6, 'bold', TINTA)
    texto(ax, 89.5, 72.0, 'IP 192.168.0.105', 5.9, color=TINTA)
    texto(ax, 89.5, 67.6, 'Coordinador', 6.0)
    texto(ax, 89.5, 64.8, 'y página web', 6.0)
    linea(ax, [(89.5, 60.6), (89.5, 51.4)], discontinua=True)
    texto(ax, 93.8, 56.0, 'Wi-Fi\n5 GHz', 5.6, color=GRIS)

    # Los dos puntos de acceso, uno por piso, en puente y unidos por cable.
    for x0, piso, canal in ((3, '3', '44'), (55, '4', '36')):
        caja(ax, x0, 35, 42, 16, VERDE_FONDO, VERDE)
        texto(ax, x0 + 21, 46.8, f'Punto de acceso · piso {piso}', 7.6, 'bold', TINTA)
        texto(ax, x0 + 21, 42.8, f'5 GHz · canal {canal} · 40 MHz', 6.4)
        texto(ax, x0 + 21, 39.2, 'En puente: no reparte direcciones ni enruta', 6.0)

    # Cable del enrutador a cada punto de acceso: el del piso 3 baja entre pisos.
    linea(ax, [(38, 60.6), (38, 56), (24, 56), (24, 51.4)])
    linea(ax, [(62, 60.6), (62, 56), (76, 56), (76, 51.4)])
    texto(ax, 24, 57.6, 'cable entre pisos', 6.2, color=GRIS)
    texto(ax, 76, 57.6, 'cable', 6.2, color=GRIS)

    # Un agente colgando de cada punto de acceso, por aire.
    for x0, piso, ip, lat in ((3, '3', '192.168.0.102', '2,13 ms'),
                              (55, '4', '192.168.0.104', '1,99 ms')):
        caja(ax, x0 + 4, 11, 34, 16.5, AGENTE_FONDO, TINTA2, radio=1.6)
        texto(ax, x0 + 21, 23.4, f'Agente del piso {piso}', 7.6, 'bold', TINTA)
        texto(ax, x0 + 21, 19.4, f'IP {ip}, reservada', 6.4, color=TINTA)
        texto(ax, x0 + 21, 15.6, f'ida y vuelta {lat}', 6.4)
        linea(ax, [(x0 + 21, 34.6), (x0 + 21, 27.9)], discontinua=True)
        texto(ax, x0 + 29, 31.2, 'Wi-Fi', 6.2, color=GRIS)

    # Lo que la figura tiene que dejar claro de una sola vez.
    caja(ax, 10, 1.5, 80, 7.5, NARANJA_FONDO, NARANJA)
    texto(ax, 50, 6.6, 'Una sola subred, 192.168.0.0/24, y un solo servidor de direcciones', 7, 'bold', TINTA)
    texto(ax, 50, 3.6, 'Es la condición para que cada agente y el portátil se descubran', 6.4)

    destino = IMAGENES / 'red_topologia.png'
    fig.savefig(destino, dpi=300)
    plt.close(fig)
    return destino


def carga():
    """Lo que el esquema de descubrimiento le cuesta a la tarjeta."""
    fig = plt.figure(figsize=(6.5, 3.4))
    ax = fig.add_axes([0.1, 0.17, 0.87, 0.74])

    casos = ['Una cadena\n(un agente)', 'Dos cadenas\npor difusión', 'Dos cadenas\nen estrella']
    bajo = [52, 95, 68]
    alto = [63, 95, 74]
    colores = [GRIS, NARANJA, VERDE]

    for i, (b, a, c) in enumerate(zip(bajo, alto, colores)):
        ax.bar(i, a, 0.52, color=c, alpha=0.22, edgecolor=c, linewidth=1.1, zorder=2)
        if a != b:
            ax.plot([i, i], [b, a], color=c, lw=2.6, solid_capstyle='butt', zorder=3)
        # La etiqueta va DENTRO de la barra, porque fuera chocaba con la linea del 100 %, y
        # debajo del tramo del rango, para que ese tramo no la cruce.
        etiqueta = f'{b}–{a} %' if a != b else f'{a} %'
        altura = b - 2.5 if a != b else a - 5.5
        ax.text(i, altura, etiqueta, ha='center', va='top', fontsize=7.4,
                fontweight='bold', color=TINTA)

    ax.axhline(100, color=TINTA2, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.text(2.46, 103, 'tarjeta llena', fontsize=6.2, color=TINTA2, va='bottom', ha='right')
    ax.annotate('Nav2 no alcanzaba a arrancar', xy=(1, 80), xytext=(1, 40),
                fontsize=6.6, color=NARANJA, ha='center',
                arrowprops=dict(arrowstyle='-|>', color=NARANJA, lw=0.9, mutation_scale=8))

    ax.set_xticks(range(3))
    ax.set_xticklabels(casos, fontsize=7)
    ax.set_ylim(0, 115)
    ax.set_ylabel('Uso del procesador de la tarjeta (%)', fontsize=7.2, color=TINTA2)
    ax.tick_params(labelsize=6.8, colors=TINTA2, length=2.5)
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    for lado in ('left', 'bottom'):
        ax.spines[lado].set_color(MODULO_BORDE)
    ax.grid(axis='y', color=MODULO_BORDE, lw=0.5, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    destino = IMAGENES / 'red_carga.png'
    fig.savefig(destino, dpi=300)
    plt.close(fig)
    return destino


if __name__ == '__main__':
    for destino in (topologia(), carga()):
        if SITIO.is_dir():
            shutil.copy(destino, SITIO / destino.name)
        print(destino.relative_to(RAIZ))
