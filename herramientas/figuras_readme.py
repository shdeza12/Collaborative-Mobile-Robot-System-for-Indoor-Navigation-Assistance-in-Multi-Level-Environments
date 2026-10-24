#!/usr/bin/env python3
"""Figuras del README: los cuatro objetivos cumplidos y la franja que lleva al sitio del proyecto.

Cada figura sale en dos versiones, clara y oscura, para que GitHub muestre la que corresponde al tema
de quien lee (el README las elige con <picture>). La franja del sitio usa las miniaturas reales de las
páginas de cada semana, así que hay que correr antes sitio/generar_semanas.py si cambiaron.

Uso, desde la raíz del repositorio:
    python3 herramientas/figuras_readme.py
Escribe en sitio/paginas/img/: readme_objetivos_{claro,oscuro}.png y readme_sitio_{claro,oscuro}.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
IMG = RAIZ / 'sitio/paginas/img'
SEMANAS = RAIZ / 'sitio/paginas/semanas/img'

TEMAS = {
    'claro': dict(fondo='#ffffff', tarjeta='#f6f8fa', borde='#d0d7de', texto='#1f2328', suave='#59636e',
                  verde='#1a7f37', acento='#0969da'),
    'oscuro': dict(fondo='#0d1117', tarjeta='#161b22', borde='#30363d', texto='#e6edf3', suave='#9198a1',
                   verde='#3fb950', acento='#4493f8'),
}

OBJETIVOS = [
    ('Objetivo 1', 'Arquitectura funcional', '10 de 10 requisitos'),
    ('Objetivo 2', 'Plataforma robótica', '6 de 6 requisitos'),
    ('Objetivo 3', 'Interfaz para el usuario', '6 de 6 requisitos'),
    ('Objetivo 4', 'Evaluación experimental', '7 de 7 requisitos'),
]

# Una miniatura por etapa del trabajo, de la plataforma inicial a la campaña con los vehículos.
MINIATURAS = ['s10_1.jpg', 's12_1.jpg', 's13_1.jpg', 's19_3.jpg', 's22_5.jpg', 's24_1.jpg', 's26_1.jpg',
              's28_1.jpg']


def caja(ax, x, y, w, h, fondo, borde, radio=0.12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radio}',
                                facecolor=fondo, edgecolor=borde, linewidth=1.2))


def objetivos(nombre, t):
    fig = plt.figure(figsize=(12, 2.9), facecolor=t['fondo'])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 2.9)
    ax.axis('off')
    ax.text(0.2, 2.55, 'Los cuatro objetivos específicos, cumplidos', fontsize=17, fontweight='bold',
            color=t['texto'], va='center')
    for i, (num, titulo, req) in enumerate(OBJETIVOS):
        x = 0.2 + i * 2.95
        caja(ax, x, 0.2, 2.75, 1.95, t['tarjeta'], t['borde'])
        ax.add_patch(Circle((x + 0.42, 1.72), 0.2, color=t['verde']))
        ax.text(x + 0.42, 1.715, '✓', fontsize=15, fontweight='bold', color=t['fondo'], ha='center',
                va='center')
        ax.text(x + 0.75, 1.72, num, fontsize=12, color=t['suave'], va='center')
        ax.text(x + 0.25, 1.18, titulo, fontsize=11.5, fontweight='bold', color=t['texto'], va='center')
        ax.text(x + 0.25, 0.78, req, fontsize=11.5, color=t['suave'], va='center')
        ax.text(x + 0.25, 0.42, '100 %', fontsize=12, fontweight='bold', color=t['verde'], va='center')
    fig.savefig(IMG / f'readme_objetivos_{nombre}.png', dpi=150, facecolor=t['fondo'])
    plt.close(fig)


def sitio(nombre, t):
    fig = plt.figure(figsize=(12, 3.3), facecolor=t['fondo'])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.3)
    ax.axis('off')
    caja(ax, 0.1, 0.1, 11.8, 3.1, t['tarjeta'], t['borde'], 0.18)
    ax.text(0.45, 2.7, 'Sitio del proyecto: semana a semana', fontsize=18, fontweight='bold',
            color=t['texto'], va='center')
    ax.text(0.45, 2.28, 'Una página por semana, de la 10 a la 28, con lo que se hizo, sus imágenes y lo que '
            'se concluyó.', fontsize=12, color=t['suave'], va='center')
    ax.text(11.55, 2.7, 'Abrir el sitio  →', fontsize=13, fontweight='bold', color=t['acento'], ha='right',
            va='center')
    ancho, alto, sep = 1.32, 0.86, 0.11
    x0 = (12 - (len(MINIATURAS) * ancho + (len(MINIATURAS) - 1) * sep)) / 2
    for i, archivo in enumerate(MINIATURAS):
        with Image.open(SEMANAS / archivo) as im:
            im = im.convert('RGB')
            # Recorte 16:10 centrado, como las tarjetas del sitio.
            w, h = im.size
            objetivo = w / h > 1.6
            if objetivo:
                nw = int(h * 1.6)
                im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else:
                nh = int(w / 1.6)
                im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
            x = x0 + i * (ancho + sep)
            ax.imshow(im, extent=(x, x + ancho, 0.95, 0.95 + alto), zorder=2)
            ax.add_patch(FancyBboxPatch((x, 0.95), ancho, alto, boxstyle='round,pad=0,rounding_size=0.04',
                                        facecolor='none', edgecolor=t['borde'], linewidth=1, zorder=3))
        semana = archivo[1:3]
        ax.text(x + ancho / 2, 0.62, f'Semana {int(semana)}', fontsize=10.5, color=t['suave'], ha='center',
                va='center')
    ax.set_aspect('auto')
    fig.savefig(IMG / f'readme_sitio_{nombre}.png', dpi=150, facecolor=t['fondo'])
    plt.close(fig)


if __name__ == '__main__':
    for nombre, tema in TEMAS.items():
        objetivos(nombre, tema)
        sitio(nombre, tema)
        print(f'readme_objetivos_{nombre}.png y readme_sitio_{nombre}.png')
