#!/usr/bin/env python3
"""Figura del documento final: duración de cada etapa en las nueve misiones de la
campaña con los dos vehículos (16 de octubre, pisos 3 y 4).

Lee los registros del coordinador (marcas de etapa con el reloj del portátil) y
dibuja una barra apilada por misión:

  recoger    TRAMO_1 (al origen)          -> TRAMO_1 (a la escalera)
  guiar 1    TRAMO_1 (a la escalera)      -> TRANSFERENCIA
  traslado   TRANSFERENCIA                -> ESPERANDO_CONFIRMACION
  espera     ESPERANDO_CONFIRMACION       -> TRAMO_2
  guiar 2    TRAMO_2                      -> COMPLETADA

Uso, desde la raíz del repositorio:
    python3 herramientas/figura_campana_vehiculos.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

RAIZ = Path(__file__).resolve().parent.parent
REGISTROS = RAIZ / 'Documentos/Evidencia/campo_20261016/registros'
SALIDA = RAIZ / 'Documentos/DocumentoFinal/imagenes/campana_vehiculos_etapas.png'

# Misiones 1 a 9 del sorteo, en orden: el registro del intento que se completó.
MISIONES = ['001041', '001324', '001606', '001837', '002056',
            '002259', '002517', '002659', '002909']

NOMBRE = {
    'piso3_ascensor': 'Ascensor (piso 3)', 'piso4_ascensor': 'Ascensor (piso 4)',
    'piso3_salon_301': 'Salón 301', 'piso3_salon_302': 'Salón 302',
    'piso3_salon_303': 'Salón 303', 'piso4_salon_401': 'Salón 401',
    'piso4_salon_402': 'Salón 402', 'piso4_salon_403': 'Salón 403',
}

TINTA, TINTA2, GRIS = '#0b0b0b', '#52514e', '#8a8984'
ETAPAS = [
    ('Primer vehículo: va a recoger al usuario', '#a9c9ef', None),
    ('Primer vehículo: guía hasta la escalera', '#2a78d6', None),
    ('Segundo vehículo: va a su escalera', '#f6b89d', None),
    ('Espera de la confirmación del usuario', '#d9d8d3', '////'),
    ('Segundo vehículo: guía hasta el destino', '#eb6834', None),
]


def duraciones(reg):
    t0 = reg['solicitud']['t_solicitud']
    marcas = [(m['etapa'], m['t'] - t0) for m in reg['marcas']]
    tramo1 = [t for e, t in marcas if e == 'TRAMO_1']
    t = {e: t for e, t in marcas if e != 'TRAMO_1'}
    cortes = [tramo1[0], tramo1[1], t['TRANSFERENCIA'],
              t['ESPERANDO_CONFIRMACION'], t['TRAMO_2'], t['COMPLETADA']]
    return [b - a for a, b in zip(cortes, cortes[1:])], cortes[-1]


def main():
    filas = []
    for n, sufijo in enumerate(MISIONES, 1):
        reg = json.loads((REGISTROS / f'mision_manual_20261017_{sufijo}.json').read_text())
        s = reg['solicitud']
        tramos, total = duraciones(reg)
        etiqueta = f"{n}.  {NOMBRE[s['origen_id']]} → {NOMBRE[s['destino_id']]}"
        filas.append((etiqueta, tramos, total))

    plt.rcParams.update({'font.size': 10, 'axes.edgecolor': GRIS,
                         'axes.labelcolor': TINTA2, 'xtick.color': TINTA2,
                         'ytick.color': TINTA2})
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    for i, (_, tramos, total) in enumerate(filas):
        izq = 0.0
        for (nombre, color, trama), d in zip(ETAPAS, tramos):
            ax.barh(i, d, left=izq, height=0.62, color=color, hatch=trama,
                    edgecolor='white', linewidth=1.5)
            izq += d
        ax.text(total + 1.2, i, f'{total:.1f} s'.replace('.', ','),
                va='center', fontsize=9, color=TINTA)

    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([f[0] for f in filas], fontsize=9.5, color=TINTA)
    ax.invert_yaxis()
    ax.set_xlim(0, 118)
    ax.set_xlabel('Tiempo desde la solicitud (s)')
    ax.grid(axis='x', color='#e6e5e0', lw=0.8)
    ax.set_axisbelow(True)
    for lado in ('top', 'right', 'left'):
        ax.spines[lado].set_visible(False)
    ax.tick_params(axis='y', length=0)

    leyenda = [Patch(facecolor=c, hatch=h, edgecolor='white', label=n)
               for n, c, h in ETAPAS]
    fig.legend(handles=leyenda, loc='upper center', ncol=2, fontsize=8.8,
               frameon=False, bbox_to_anchor=(0.56, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.85))
    fig.savefig(SALIDA, dpi=200)
    print(f'escrita {SALIDA.relative_to(RAIZ)}')


if __name__ == '__main__':
    main()
