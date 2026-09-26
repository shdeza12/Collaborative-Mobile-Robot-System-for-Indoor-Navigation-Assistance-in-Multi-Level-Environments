#!/usr/bin/env python3
"""Saca G-2, G-3 y la tasa de exito de una campana del vehiculo real.

    analizar_campana_nav2.py <campana.csv> [--tolerancia 0.25] [--minimo 5.0]

El CSV es el que escribe corrida_nav2.py, una fila por corrida, CON LAS TRES
COLUMNAS CINTA_* RELLENADAS A MANO con lo medido con flexometro. Corre en el
portatil; no necesita ROS.

QUE CALCULA, Y CONTRA QUE CRITERIO
----------------------------------
G-2 (ACTA_GO_NOGO.md:104): 'odom -> base_link' publica desplazamiento con error
    <= 10 % sobre un recorrido CONOCIDO de >= 5 m. Por corrida:
        razon = avance segun /odom / avance medido con cinta
    y la corrida pasa si |razon - 1| <= 0,10 y la cinta midio >= 5 m. Una
    corrida sin cinta NO CUENTA: es exactamente lo que G-2 pregunta.

G-3 (ACTA_GO_NOGO.md:105): llegada verificada contra /odom, no contra el
    SUCCEEDED de Nav2. Se dan las dos llegadas -la de /odom que calcula la
    herramienta y la de cinta- y se cuenta como llegada la que cae dentro de
    la tolerancia SEGUN LA CINTA.

RF-27: N entre 5 y 10 repeticiones con registro. Se informa el N con cinta.

LO QUE NO HACE
--------------
No cambia el criterio. La tolerancia de 0,25 m esta cuestionada -la navegacion
del 24-sep se paso 0,412 m por la banda muerta, y la campana OE4 se quedo
corta 0,28-0,35 m-, y decidirla es de los directores, antes de correr y por
escrito. '--tolerancia' existe para poder mostrar la sensibilidad, no para
elegir la que salga bien. Si se usa otra, el informe lo dice en la cabecera.
"""
import argparse
import csv
import math
import statistics
import sys

TOLERANCIA_ACTA = 0.25


def numero(texto):
    texto = (texto or '').strip().replace(',', '.')
    return float(texto) if texto else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('csv')
    ap.add_argument('--tolerancia', type=float, default=TOLERANCIA_ACTA,
                    help='tolerancia de llegada en m (la del acta: 0,25)')
    ap.add_argument('--minimo', type=float, default=5.0,
                    help='recorrido minimo para G-2, en m (el del acta: 5,0)')
    a = ap.parse_args()

    with open(a.csv, newline='') as f:
        filas = list(csv.DictReader(f))
    if not filas:
        print('El CSV no tiene corridas.')
        return 1

    con_cinta, sin_cinta = [], []
    for r in filas:
        cinta = numero(r.get('CINTA_avance_real_m'))
        (con_cinta if cinta else sin_cinta).append(r)

    print('# Campana %s' % a.csv)
    print()
    if a.tolerancia != TOLERANCIA_ACTA:
        print('> **Tolerancia de llegada distinta de la del acta: %.2f m en vez de %.2f.**'
              % (a.tolerancia, TOLERANCIA_ACTA))
        print('> Esto es un analisis de sensibilidad, no el resultado de G-3.')
        print()
    print('%d corridas en el fichero, %d con medida de cinta.' % (len(filas), len(con_cinta)))
    if sin_cinta:
        print('Sin cinta, y por tanto fuera del computo: %s.'
              % ', '.join(r['corrida'] or '(sin id)' for r in sin_cinta))
    print()
    if not con_cinta:
        print('Nada que analizar: rellena las columnas CINTA_* primero.')
        return 1

    print('| Corrida | Nav2 | Pedido | Cinta | /odom | Razón /odom | G-2 | '
          'Error cinta | Error /odom | Llega |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    errores, llegadas, g2_ok = [], 0, 0
    for r in con_cinta:
        cinta = numero(r['CINTA_avance_real_m'])
        odom = numero(r['avance_odom_m'])
        pedido = numero(r['avance_pedido_m'])
        e_long = numero(r.get('CINTA_error_longitudinal_m'))
        e_lat = numero(r.get('CINTA_desvio_lateral_m'))
        e_odom = numero(r.get('error_long_odom_m'))
        razon = odom / cinta
        cuenta_g2 = cinta >= a.minimo
        pasa_g2 = cuenta_g2 and abs(razon - 1.0) <= 0.10
        g2_ok += pasa_g2
        if e_long is None:
            e_cinta = None
        else:
            e_cinta = math.hypot(e_long, e_lat or 0.0)
            errores.append(e_cinta)
        llega = e_cinta is not None and e_cinta <= a.tolerancia
        llegadas += llega
        print('| %s | %s | %.3f | %.3f | %.3f | %.3f | %s | %s | %s | %s |' % (
            r['corrida'], r['estado'], pedido, cinta, odom, razon,
            ('sí' if pasa_g2 else 'no') if cuenta_g2 else '< %.0f m' % a.minimo,
            '%.3f' % e_cinta if e_cinta is not None else '—',
            '%+.3f' % e_odom if e_odom is not None else '—',
            'sí' if llega else 'no'))
    print()

    n = len(con_cinta)
    print('## G-2 — odometría contra cinta')
    print()
    validas = [r for r in con_cinta if numero(r['CINTA_avance_real_m']) >= a.minimo]
    print('- Corridas de %.0f m o más: **%d** de %d.' % (a.minimo, len(validas), n))
    print('- Dentro del ±10 %%: **%d** de %d.' % (g2_ok, len(validas)))
    # Solo las de >= minimo: una corrida corta tiene su razon, pero no es una
    # medida de G-2 y no entra en su media.
    r_validas = [numero(r['avance_odom_m']) / numero(r['CINTA_avance_real_m'])
                 for r in validas]
    if len(r_validas) >= 2:
        print('- Razón /odom ÷ cinta en esas corridas: media **%.3f**, σ %.3f, '
              'de %.3f a %.3f.' % (statistics.mean(r_validas),
                                   statistics.stdev(r_validas),
                                   min(r_validas), max(r_validas)))
    elif r_validas:
        print('- Razón /odom ÷ cinta: **%.3f** (una sola corrida).' % r_validas[0])
    print()
    print('## G-3 — llegada')
    print()
    if errores:
        print('- Error de llegada por cinta: media **%.3f m**, máximo %.3f m.'
              % (statistics.mean(errores), max(errores)))
    print('- Dentro de %.2f m según la cinta: **%d** de %d.' % (a.tolerancia, llegadas, n))
    exitos = sum(1 for r in con_cinta if r['estado'] == 'SUCCEEDED')
    print('- Nav2 declaró SUCCEEDED en %d de %d. **No es el criterio**: G-3 pide'
          ' verificar la llegada, no creer a Nav2.' % (exitos, n))
    print()
    print('## RF-27')
    print()
    print('- N con registro y cinta: **%d** (el requisito pide entre 5 y 10).' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
