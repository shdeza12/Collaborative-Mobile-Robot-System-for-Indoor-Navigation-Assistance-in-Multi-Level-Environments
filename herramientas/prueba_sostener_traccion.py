#!/usr/bin/env python3
"""Pruebas de sostener_traccion.py. No necesitan ROS, ni carro, ni recta.

POR QUE ESTA PRUEBA EXISTE
--------------------------
Este programa mueve un vehiculo sin que nadie tenga la mano encima: no hay
mando que soltar ni gatillo que dejar de pulsar, solo un reloj. Lo unico que
para el carro es que 'salida()' devuelva cero en el instante correcto.

A mano, en la recta, se comprueba una vez el caso facil -arranca, rueda, para-.
Lo que a mano no se reproduce, y es donde el fallo se traduce en un carro que
sigue rodando: el instante exacto de cada frontera, un tick que llega tarde, el
final de la corrida, y una rampa cuyo paso no divide al intervalo. Todo eso se
comprueba aqui.

Corre igual en el portatil y en el carro, porque no importa nada de ROS.

Uso:  python3 herramientas/prueba_sostener_traccion.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sostener_traccion import (TOPE_MARCHA_TOTAL_S, TOPE_TRAMO_S, Plan, rampa,
                               salida, segmentos, validar)

FALLOS = []


def comprobar(nombre, condicion, detalle=""):
    if condicion:
        print(f"  ok   {nombre}")
    else:
        print(f"  FALLO {nombre} {detalle}")
        FALLOS.append(nombre)


# --- rampa() ----------------------------------------------------------------
print("rampa()  -- los valores que se van a publicar")

comprobar("una rampa corta da los valores exactos",
          rampa(0.10, 0.20, 0.05) == (0.10, 0.15, 0.20),
          f"-> {rampa(0.10, 0.20, 0.05)}")

# Acumular flotantes daria 0.18000000000000002 y similares. Importa de verdad:
# el numero que sale por pantalla es el que el operador va a anotar como
# 'aqui empezo a moverse', asi que tiene que ser el que se publica.
comprobar("no acumula error de coma flotante",
          rampa(0.04, 0.30, 0.02)[7] == 0.18,
          f"-> {rampa(0.04, 0.30, 0.02)[7]!r}")

comprobar("incluye el extremo superior",
          rampa(0.04, 0.30, 0.02)[-1] == 0.30)

comprobar("un paso que no divide justo no se pasa del extremo",
          max(rampa(0.10, 0.25, 0.04)) <= 0.25 + 1e-9,
          f"-> {rampa(0.10, 0.25, 0.04)}")

comprobar("paso cero no genera tramos, en vez de colgarse",
          rampa(0.10, 0.20, 0.0) == ())

# --- validar() --------------------------------------------------------------
print("validar()  -- lo que impide sacar el carro")

comprobar("una corrida normal no tiene pegas",
          validar((0.15,), 6.0, 5.0, 0.35) == [])

comprobar("throttle negativo se rechaza",
          validar((-0.15,), 6.0, 5.0, 0.35) != [])

comprobar("throttle cero se rechaza: no mide nada",
          validar((0.0,), 6.0, 5.0, 0.35) != [])

comprobar("pasarse del tope se rechaza",
          validar((0.90,), 6.0, 5.0, 0.35) != [])

comprobar("el tope se puede subir a conciencia",
          validar((0.90,), 6.0, 5.0, 0.95) == [])

comprobar("un tramo mas largo que el tope se rechaza",
          validar((0.15,), TOPE_TRAMO_S + 1, 5.0, 0.35) != [])

comprobar("marcha cero se rechaza",
          validar((0.15,), 0.0, 5.0, 0.35) != [])

comprobar("quietud negativa se rechaza",
          validar((0.15,), 6.0, -1.0, 0.35) != [])

# El error de dedo que esto ataja: '--rampa 0.04:0.30:0.002' son 131 tramos, y a
# 6 s cada uno el carro rueda trece minutos seguidos.
largo = rampa(0.04, 0.30, 0.002)
comprobar("una rampa con el paso mal puesto se rechaza por duracion total",
          validar(largo, 6.0, 5.0, 0.35) != [],
          f"-> {len(largo)} tramos")

comprobar("la misma rampa cabe si cada tramo es corto",
          validar(rampa(0.04, 0.30, 0.02), 4.0, 5.0, 0.35) == [],
          f"-> {len(rampa(0.04, 0.30, 0.02))} tramos, "
          f"{len(rampa(0.04, 0.30, 0.02)) * 4.0:g} s")

comprobar("una corrida que da justo el tope total se acepta",
          validar((0.1, 0.15, 0.2, 0.25), TOPE_MARCHA_TOTAL_S / 4, 5.0, 0.35) == [])

comprobar("un pelo por encima del tope total se rechaza",
          validar((0.1, 0.15, 0.2, 0.25), TOPE_MARCHA_TOTAL_S / 4 + 0.1, 5.0, 0.35) != [])

comprobar("sin tramos se rechaza",
          validar((), 6.0, 5.0, 0.35) != [])

# --- segmentos() y salida() -------------------------------------------------
print("salida()  -- que se publica en cada instante")

PLAN = Plan(throttles=(0.20,), marcha_s=6.0, quietud_s=5.0)
SEGS = segmentos(PLAN)

comprobar("la corrida son quietud + tramos + quietud",
          [f for _, _, f in SEGS] == ["quieto_inicial", "marcha",
                                      "quieto_final"])

comprobar("antes de arrancar se publica cero",
          salida(SEGS, -3.0) == (0.0, "cuenta_atras"))

comprobar("en la quietud inicial se publica cero",
          salida(SEGS, 2.0) == (0.0, "quieto_inicial"))

comprobar("el instante justo en que empieza la marcha ya va con throttle",
          salida(SEGS, 5.0) == (0.20, "marcha"))

comprobar("un pelo antes todavia es cero",
          salida(SEGS, 4.999) == (0.0, "quieto_inicial"))

comprobar("a mitad del tramo sigue el mismo valor sostenido",
          salida(SEGS, 8.0) == (0.20, "marcha"))

comprobar("el instante justo en que acaba la marcha ya es cero",
          salida(SEGS, 11.0) == (0.0, "quieto_final"))

comprobar("un pelo antes todavia tira",
          salida(SEGS, 10.999) == (0.20, "marcha"))

# Esta es LA comprobacion de seguridad. Si 'fin' devolviera el ultimo valor -o
# si el bucle se saliera por el final sin decidir- el carro se quedaria rodando
# justo cuando el programa cree haber terminado.
comprobar("pasado el final se publica cero, no el ultimo valor",
          salida(SEGS, 100.0) == (0.0, "fin"))

comprobar("muchisimo despues sigue siendo cero",
          salida(SEGS, 86400.0) == (0.0, "fin"))

# Un tick tardio no se salta la parada: la salida se decide por reloj, no
# contando ticks. Se comprueba saltando la ventana de quietud final entera.
comprobar("un tick que llega tarde y se salta la quietud final para igual",
          salida(SEGS, 16.5) == (0.0, "fin"))

# --- la corrida entera, barrida ---------------------------------------------
print("la corrida completa  -- barrido de principio a fin")

RAMPA = rampa(0.04, 0.12, 0.02)
PLAN_R = Plan(throttles=RAMPA, marcha_s=2.0, quietud_s=5.0)
SEGS_R = segmentos(PLAN_R)
DURACION = 2 * PLAN_R.quietud_s + PLAN_R.marcha_s * len(RAMPA)

muestras = [salida(SEGS_R, t / 100.0) for t in range(-500, int(DURACION * 100) + 500)]
valores = {th for th, _ in muestras}

comprobar("nunca se publica un valor que no se pidio",
          valores <= set(RAMPA) | {0.0},
          f"-> {sorted(valores)}")

comprobar("todos los tramos de la rampa llegan a publicarse",
          set(RAMPA) <= valores)

comprobar("fuera de 'marcha' el throttle es siempre cero",
          all(th == 0.0 for th, fase in muestras if fase != "marcha"))

comprobar("dentro de 'marcha' el throttle nunca es cero",
          all(th > 0.0 for th, fase in muestras if fase == "marcha"))

# Cada tramo tiene que durar lo pedido: si durase menos, la ventana de 1 s de
# medir_escala_traccion.py se comeria dos escalones y la tabla saldria mezclada.
for objetivo in RAMPA:
    cuantas = sum(1 for th, _ in muestras if th == objetivo)
    comprobar(f"el tramo {objetivo:g} dura los {PLAN_R.marcha_s:g} s pedidos",
              abs(cuantas / 100.0 - PLAN_R.marcha_s) < 0.02,
              f"-> {cuantas / 100.0:g} s")

comprobar("la corrida entera dura lo anunciado",
          sum(d for d, _, _ in SEGS_R) == DURACION,
          f"-> {sum(d for d, _, _ in SEGS_R)} contra {DURACION}")

comprobar("una corrida sin quietud sigue siendo valida",
          salida(segmentos(Plan((0.2,), 3.0, 0.0)), 0.0) == (0.2, "marcha"))

print()
if FALLOS:
    print(f"{len(FALLOS)} FALLO(S): {', '.join(FALLOS)}")
    sys.exit(1)
print(f"Todas las comprobaciones pasan ({len(muestras)} instantes barridos).")
