#!/usr/bin/env python3
"""Pruebas de comprobar_movimiento_bag.py. No necesitan ROS ni un bag.

Las funciones que deciden -diferencia, repartir, veredicto- solo tocan la lista
`ranges`, asi que se prueban con barridos de mentira. Lo que necesita ROS es
unicamente la lectura del bag, y eso ya se comprueba corriendo la herramienta
contra los bags reales.

Uso:  python3 herramientas/prueba_comprobar_movimiento_bag.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprobar_movimiento_bag import (MOVIMIENTO_MINIMO_S, QUIETO_MAXIMO_FRAC,
                                      diferencia, repartir, veredicto)

FALLOS = []


def comprobar(nombre, condicion, detalle=""):
    if condicion:
        print(f"  ok   {nombre}")
    else:
        print(f"  FALLO {nombre} {detalle}")
        FALLOS.append(nombre)


class Barrido:
    """Lo minimo que miran las funciones bajo prueba."""

    def __init__(self, ranges):
        self.ranges = list(ranges)


def serie(valores_por_barrido, hz=7.0):
    """Convierte una lista de listas en [(t, Barrido)] a la frecuencia dada."""
    return [(i / hz, Barrido(v)) for i, v in enumerate(valores_por_barrido)]


# --- diferencia -------------------------------------------------------------
print("diferencia()")

comprobar("dos barridos identicos dan 0",
          diferencia(Barrido([1.0, 2.0, 3.0]), Barrido([1.0, 2.0, 3.0])) == 0.0)

comprobar("un desplazamiento uniforme de 0,5 m da 0,5",
          diferencia(Barrido([1.0, 2.0, 3.0]), Barrido([1.5, 2.5, 3.5])) == 0.5)

# El primer rayo es inf en uno de los dos: si contara, arrastraria la mediana.
# Los tres validos difieren 0,4 m cada uno, asi que la mediana tiene que ser 0,4.
comprobar("los inf se ignoran, no arrastran la mediana",
          abs(diferencia(Barrido([math.inf, 2.0, 3.0, 4.0]),
                         Barrido([9.0, 2.4, 3.4, 4.4])) - 0.4) < 1e-9,
          f"-> {diferencia(Barrido([math.inf, 2.0, 3.0, 4.0]), Barrido([9.0, 2.4, 3.4, 4.4]))}")

comprobar("sin ningun rayo valido en ambos devuelve nan",
          math.isnan(diferencia(Barrido([math.inf, 1.0]),
                                Barrido([1.0, math.inf]))))

# La razon de usar mediana y no media: una persona cruzando el pasillo mueve
# unos pocos rayos muchisimo. Con media esto daria 1,0 y se leeria como
# movimiento del sensor; con mediana da 0.
quieto = [5.0] * 20
cruza = [5.0] * 18 + [0.5, 0.5]
comprobar("una persona cruzando no se confunde con movimiento (mediana)",
          diferencia(Barrido(quieto), Barrido(cruza)) == 0.0,
          f"-> {diferencia(Barrido(quieto), Barrido(cruza))}")

# --- repartir ---------------------------------------------------------------
print("repartir()")

# 70 barridos a 7 Hz = 10 s, todos iguales: quieto entero.
dur, q, m, hz = repartir(serie([[5.0] * 10] * 70))
comprobar("un sensor quieto da 100 % quieto", m == 0.0 and q == dur,
          f"-> quieto {q:.1f} de {dur:.1f}")
comprobar("la frecuencia sale bien", abs(hz - 7.0) < 0.2, f"-> {hz:.2f} Hz")

# 70 barridos donde cada uno se aleja 10 cm: 0,7 m/s, siempre en movimiento.
dur, q, m, _ = repartir(serie([[5.0 + 0.1 * i] * 10 for i in range(70)]))
comprobar("un sensor que avanza 0,7 m/s da 100 % movimiento",
          q == 0.0 and m == dur, f"-> movim {m:.1f} de {dur:.1f}")

# Mitad y mitad: 35 barridos quieto, 35 avanzando.
mitad = [[5.0] * 10] * 35 + [[5.0 + 0.1 * i] * 10 for i in range(35)]
dur, q, m, _ = repartir(serie(mitad))
comprobar("mitad y mitad reparte a partes parecidas",
          abs(q - m) < 0.25 * dur, f"-> quieto {q:.1f}, movim {m:.1f}")

comprobar("quieto + movimiento reconstruye la duracion",
          abs((q + m) - dur) < 1e-6)

# Un avance de 1 cm/barrido son 7 cm/s: por debajo del umbral a 1 s vista
# quedaria como quieto, y a 7 cm en 1 s queda justo por encima. Se comprueba
# que el umbral se aplica sobre barridos separados 1 s y no consecutivos.
dur, q, m, _ = repartir(serie([[5.0 + 0.01 * i] * 10 for i in range(70)]))
comprobar("el umbral se mide a 1 s vista, no entre barridos consecutivos",
          m == dur, f"-> movim {m:.1f} de {dur:.1f}")

# --- veredicto --------------------------------------------------------------
print("veredicto()")

sirve, motivos = veredicto(200.0, 60.0, 140.0)
comprobar("140 s de movimiento sobre 200 s sirve", sirve and not motivos)

sirve, motivos = veredicto(257.6, 228.4, 29.2)
comprobar("bag_mapa_1451 real (88,7 % quieto) se rechaza", not sirve)
comprobar("y se rechaza por los dos motivos", len(motivos) == 2, f"-> {motivos}")

sirve, motivos = veredicto(404.4, 326.2, 78.2)
comprobar("bag_mapa_1456 real (80,7 % quieto) se rechaza pese a 78 s de movim.",
          not sirve and len(motivos) == 1, f"-> {motivos}")

sirve, _ = veredicto(57.9, 57.9, 0.0)
comprobar("bag_mapa_1445 real (quieto entero) se rechaza", not sirve)

# Justo en el borde de cada regla, por separado.
sirve, motivos = veredicto(100.0, 100.0 * QUIETO_MAXIMO_FRAC,
                           MOVIMIENTO_MINIMO_S)
comprobar("justo en los dos limites, pasa", sirve, f"-> {motivos}")

sirve, _ = veredicto(100.0, 100.0 * QUIETO_MAXIMO_FRAC,
                     MOVIMIENTO_MINIMO_S - 0.1)
comprobar("un decimo de segundo por debajo del minimo, falla", not sirve)

sirve, _ = veredicto(100.0, 100.0 * QUIETO_MAXIMO_FRAC + 0.1,
                     MOVIMIENTO_MINIMO_S)
comprobar("una decima por encima del maximo de quieto, falla", not sirve)

sirve, motivos = veredicto(10.0, float("nan"), float("nan"))
comprobar("sin pares comparables no sirve y lo dice",
          not sirve and len(motivos) == 1)

print()
if FALLOS:
    print(f"{len(FALLOS)} FALLO(S): {', '.join(FALLOS)}")
    sys.exit(1)
print("Todas las comprobaciones pasan.")
