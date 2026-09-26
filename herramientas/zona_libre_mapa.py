#!/usr/bin/env python3
"""Dice en que tramo de un mapa se puede pedir una meta, ANTES de pedirla.

    zona_libre_mapa.py <mapa.yaml> [--y Y] [--margen M]

POR QUE EXISTE
--------------
El 2026-09-24 una meta a x = 8,0 cayo en celdas desconocidas del mapa y Nav2
aborto sin decir por que. El planificador corre con 'allow_unknown: false', asi
que solo planifica por celdas LIBRES, y en el mapa del pasillo de 6 m eran el
26,2 %: el resto es gris. Que un punto se vea «dentro del pasillo» en la imagen
no quiere decir que Nav2 pueda llegar a el.

Esta herramienta recorre la linea y = Y del mapa (por defecto el eje del
pasillo, y = 0, que es por donde condujo el vehiculo al mapearlo) y dice que
tramo continuo de celdas libres contiene, y cuanto avance cabe dentro.

Corre igual en el portatil y en el vehiculo: no usa ROS, ni PIL, ni numpy.

QUE CUENTA COMO LIBRE
---------------------
Lo mismo que para map_server con el YAML del mapa: una celda es libre si su
ocupacion queda por debajo de 'free_thresh'. Con 'free_thresh: 0.1' eso es un
valor de gris de 230 o mas. El gris 205 es DESCONOCIDO y no cuenta como libre:
confundirlo fue el error que el 2026-09-24 hizo pasar el lienzo de un mapa por
las medidas del cuarto.

UNA FRANJA, NO UNA LINEA
------------------------
La primera version miraba una sola fila de celdas, como si el vehiculo no
tuviera ancho, y en el mapa del pasillo de 6 m dio el tramo util hasta
x = 6,21. Falso: la caja del fondo empieza en y = 0,05, pegada al eje, y el
carro mide 0,19 m de ancho, asi que la rozaria desde x = 6,16. Ahora una
columna solo cuenta como libre si lo son TODAS sus celdas en la franja
y +- ancho/2. Por defecto 0,30 m: el ancho del carro y 5 cm por lado.

EL MARGEN
---------
Por defecto 0,30 m a cada lado del tramo. El costmap infla los obstaculos y el
vehiculo mide 0,28 m de largo; una meta pegada al borde del espacio libre es
una meta que el planificador puede rechazar o que el carro sobrepasa. La meta
de la navegacion del 24-sep estaba a 0,5 m del borde y el carro paro encima de
el.
"""
import argparse
import math
import os
import sys


def leer_pgm(ruta):
    """Lee un PGM binario (P5) o de texto (P2). Devuelve (ancho, alto, filas)."""
    with open(ruta, 'rb') as f:
        datos = f.read()
    tokens = []
    i = 0
    while len(tokens) < 4:
        while datos[i:i + 1].isspace():
            i += 1
        if datos[i:i + 1] == b'#':
            while datos[i:i + 1] not in (b'\n', b''):
                i += 1
            continue
        j = i
        while not datos[j:j + 1].isspace():
            j += 1
        tokens.append(datos[i:j])
        i = j
    magico, ancho, alto, maximo = tokens[0], int(tokens[1]), int(tokens[2]), int(tokens[3])
    if maximo > 255:
        raise ValueError('PGM de 16 bits no soportado')
    i += 1  # un solo separador tras el maximo
    if magico == b'P5':
        cuerpo = datos[i:i + ancho * alto]
        valores = list(cuerpo)
    elif magico == b'P2':
        valores = [int(t) for t in datos[i:].split()][:ancho * alto]
    else:
        raise ValueError('no es un PGM: %r' % magico)
    filas = [valores[f * ancho:(f + 1) * ancho] for f in range(alto)]
    return ancho, alto, filas


def leer_yaml_mapa(ruta):
    """Lectura minima del YAML de map_server, sin depender de PyYAML."""
    campos = {}
    with open(ruta) as f:
        for linea in f:
            linea = linea.split('#', 1)[0].strip()
            if ':' not in linea:
                continue
            clave, valor = linea.split(':', 1)
            campos[clave.strip()] = valor.strip()
    origen = [float(x) for x in campos['origin'].strip('[]').split(',')]
    imagen = campos['image'].strip('\'"')
    if not os.path.isabs(imagen):
        imagen = os.path.join(os.path.dirname(os.path.abspath(ruta)), imagen)
    return {
        'imagen': imagen,
        'resolucion': float(campos['resolution']),
        'origen': origen,
        'negate': int(campos.get('negate', '0')),
        'free_thresh': float(campos.get('free_thresh', '0.196')),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('mapa', help='YAML del mapa, el mismo que se le pasa a map_server')
    ap.add_argument('--y', type=float, default=0.0,
                    help='linea del mapa a recorrer, en m (defecto 0: el eje del pasillo)')
    ap.add_argument('--margen', type=float, default=0.30,
                    help='margen a cada lado del tramo libre, en m (defecto 0,30)')
    ap.add_argument('--ancho', type=float, default=0.30,
                    help='ancho de la franja que tiene que estar libre, en m '
                         '(defecto 0,30: el carro mide 0,19)')
    a = ap.parse_args()

    meta = leer_yaml_mapa(a.mapa)
    ancho, alto, filas = leer_pgm(meta['imagen'])
    res = meta['resolucion']
    ox, oy = meta['origen'][0], meta['origen'][1]

    # Filas del PGM que cubren la franja. La primera fila del PGM es la de
    # ARRIBA del mapa, y el eje y del marco 'map' crece hacia arriba.
    def fila_de(y):
        return (alto - 1) - int(math.floor((y - oy) / res))
    f_arriba = fila_de(a.y + a.ancho / 2.0)
    f_abajo = fila_de(a.y - a.ancho / 2.0)
    if not (0 <= f_arriba < alto and 0 <= f_abajo < alto):
        print('ERROR: la franja y = %.2f +- %.2f se sale del mapa (y de %.2f a %.2f)'
              % (a.y, a.ancho / 2.0, oy, oy + alto * res))
        return 2
    franja = range(min(f_arriba, f_abajo), max(f_arriba, f_abajo) + 1)

    # Umbral en gris: ocupacion = (255 - gris) / 255 sin 'negate'.
    umbral = 255.0 * (1.0 - meta['free_thresh'])

    def libre(gris):
        g = 255 - gris if meta['negate'] else gris
        return g >= umbral

    libres = [all(libre(filas[f][col]) for f in franja) for col in range(ancho)]

    tramos = []
    inicio = None
    for col, es_libre in enumerate(libres + [False]):
        if es_libre and inicio is None:
            inicio = col
        elif not es_libre and inicio is not None:
            tramos.append((inicio, col - 1))
            inicio = None
    if not tramos:
        print('En la franja y = %.2f +- %.2f no hay ningun tramo libre.'
              % (a.y, a.ancho / 2.0))
        return 1

    x_de = lambda c: ox + (c + 0.5) * res
    print('mapa   %s' % a.mapa)
    print('franja y = %.2f +- %.2f m   (%d x %d celdas a %.3f m)'
          % (a.y, a.ancho / 2.0, ancho, alto, res))
    print()
    print('tramos libres en esa franja:')
    for c0, c1 in tramos:
        print('   x = %6.2f  a  %6.2f   (%.2f m)'
              % (x_de(c0), x_de(c1), (c1 - c0 + 1) * res))

    c0, c1 = max(tramos, key=lambda t: t[1] - t[0])
    x0, x1 = x_de(c0) + a.margen, x_de(c1) - a.margen
    print()
    print('TRAMO UTIL (el mas largo, menos %.2f m a cada lado):' % a.margen)
    print('   salida no antes de x = %.2f' % x0)
    print('   meta no despues de x = %.2f' % x1)
    print('   AVANCE MAXIMO: %.2f m' % max(0.0, x1 - x0))
    if x1 - x0 < 5.0:
        print()
        print('AVISO: menos de 5 m. G-2 exige un recorrido de 5 m o mas, asi que')
        print('en este mapa una corrida NO puede servir de medida de G-2. Hace')
        print('falta mapear un tramo mas largo antes de la campana.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
