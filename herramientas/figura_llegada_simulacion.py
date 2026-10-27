#!/usr/bin/env python3
"""Figura del documento final: error de llegada de las treinta misiones de la campaña en simulación.

Un punto por misión, en dos filas: las quince de un mismo piso, sin relevo, y las quince entre pisos,
con relevo. La línea discontinua es la tolerancia de 0,25 m; los puntos naranja son las cuatro
misiones fallidas, todas por quedar cortas del destino. La marca vertical de cada fila es su mediana.

Lee los registros versionados de la campaña (Documentos/Evidencia/registros/S21_OE4_*.json). Cada
registro trae la condición de la misión (A: un piso, B: dos pisos), el error de llegada contra la
pose del simulador y el veredicto.

Uso, desde la raíz del repositorio:
    python3 herramientas/figura_llegada_simulacion.py
"""
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
REGISTROS = sorted((RAIZ / 'Documentos/Evidencia/registros').glob('S21_OE4_*.json'))
SALIDA = RAIZ / 'Documentos/DocumentoFinal/imagenes/llegada_simulacion.png'

TINTA, TINTA2, GRIS = '#0b0b0b', '#52514e', '#8a8984'
AZUL, NARANJA = '#2a78d6', '#eb6834'
TOLERANCIA = 0.25
FILAS = [('B', 'Entre pisos, con relevo'), ('A', 'Mismo piso, sin relevo')]


def coma(v, dec=2):
    return f'{v:.{dec}f}'.replace('.', ',')


def main():
    misiones = []
    for f in REGISTROS:
        d = json.loads(f.read_text(encoding='utf-8'))
        misiones.append((d['mision']['condicion'], d['verdad_de_terreno']['error_posicion_m'],
                         d['veredicto']['exito']))
    assert len(misiones) == 30, len(misiones)

    fig, ax = plt.subplots(figsize=(6.5, 1.9))
    fig.subplots_adjust(left=0.24, right=0.97, bottom=0.27, top=0.95)
    for y, (condicion, nombre) in enumerate(FILAS):
        errores = sorted(e for c, e, _ in misiones if c == condicion)
        exitos = {e: ok for c, e, ok in misiones if c == condicion}
        # Desplazamiento vertical fijo y alterno para que los puntos cercanos no se tapen.
        for k, e in enumerate(errores):
            dy = (k % 3 - 1) * 0.11
            ax.scatter(e, y + dy, s=17, color=AZUL if exitos[e] else NARANJA, edgecolor='white',
                       linewidth=0.6, zorder=3)
        mediana = statistics.median(errores)
        ax.plot([mediana, mediana], [y - 0.3, y + 0.3], color=TINTA, lw=1.1, zorder=4)
        ax.text(mediana, y + 0.36, f'mediana {coma(mediana, 3)} m', fontsize=6.4, color=TINTA2,
                ha='center', va='bottom')
        n_ok = sum(exitos.values())
        ax.text(-0.012, y, f'{nombre}\n{n_ok} de {len(errores)} dentro', fontsize=6.8, color=TINTA,
                ha='right', va='center', transform=ax.get_yaxis_transform())

    ax.axvline(TOLERANCIA, color=GRIS, lw=0.8, ls=(0, (4, 2)), zorder=2)
    ax.text(TOLERANCIA + 0.004, 1.48, 'tolerancia de 0,25 m', fontsize=6.4, color=TINTA2, va='top')
    ax.set_xlim(0, 0.38)
    ax.set_ylim(-0.55, 1.55)
    ax.set_yticks([])
    ax.set_xticks([0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35])
    ax.set_xticklabels([coma(v) for v in ax.get_xticks()], fontsize=6.8, color=TINTA2)
    ax.set_xlabel('Error de llegada (m)', fontsize=7, color=TINTA2)
    for lado in ('top', 'right', 'left'):
        ax.spines[lado].set_visible(False)
    ax.spines['bottom'].set_color(GRIS)
    ax.tick_params(axis='x', color=GRIS, length=3)
    ax.grid(axis='x', color='#e6e5e1', lw=0.5, zorder=0)
    fig.savefig(SALIDA, dpi=300)
    print(SALIDA.relative_to(RAIZ))


if __name__ == '__main__':
    main()
