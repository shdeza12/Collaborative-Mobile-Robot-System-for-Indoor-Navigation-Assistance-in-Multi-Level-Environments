#!/usr/bin/env python3
"""Pruebas de teleop_mando.py. No necesitan ROS, ni mando, ni carro.

POR QUE ESTA PRUEBA EXISTE
--------------------------
La Parte 6 de GUIA_TELEOP_MANDO.md comprueba el hombre muerto con el carro en
alto: se pulsa ZR, se da stick y se apaga el mando. Eso prueba UNA vez el caso
facil, con el vehiculo delante y a costa de subirlo a una caja.

Lo que no prueba, porque a mano no se reproduce: el instante justo del
vencimiento, el arranque en frio antes del primer mensaje, un mando que publica
menos ejes de los que se le piden, o un gatillo sin estrenar que lee 0,0. Son
los casos en los que el fallo se traduce en un vehiculo de 4 m/s que no para.

Corre igual en el portatil y en el carro, porque no importa nada de ROS.

Uso:  python3 herramientas/prueba_teleop_mando.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from teleop_mando import Ajustes, decidir, ejes_necesarios, escalar, salida

FALLOS = []


def comprobar(nombre, condicion, detalle=""):
    if condicion:
        print(f"  ok   {nombre}")
    else:
        print(f"  FALLO {nombre} {detalle}")
        FALLOS.append(nombre)


AJ = Ajustes()

# Un mando en reposo: gatillos a +1,0 (sin pulsar), sticks a 0,0.
REPOSO = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0]


def ejes(traccion=0.0, direccion=0.0, zr=1.0, zl=1.0):
    """Construye la lista de ejes tal como la publica joy_node."""
    v = list(REPOSO)
    v[AJ.eje_traccion] = traccion
    v[AJ.eje_direccion] = direccion
    v[AJ.eje_habilitar] = zr
    v[AJ.eje_turbo] = zl
    return v


PULSADO = -1.0  # gatillo a fondo

# --- escalar ----------------------------------------------------------------
print("escalar()  -- zona muerta y recorrido continuo")

comprobar("el centro exacto da 0", escalar(0.0, 0.12) == 0.0)

comprobar("dentro de la zona muerta da 0", escalar(0.11, 0.12) == 0.0)

# En el borde exacto la condicion es '<', asi que 0,12 ya no es zona muerta;
# la formula devuelve 0 de todas formas. Lo que importa es que no haya salto.
comprobar("en el borde exacto de la zona muerta sigue dando 0",
          escalar(0.12, 0.12) == 0.0, f"-> {escalar(0.12, 0.12)}")

comprobar("justo pasada la zona muerta arranca desde casi 0, no desde 0,12",
          0.0 < escalar(0.13, 0.12) < 0.02, f"-> {escalar(0.13, 0.12)}")

comprobar("a fondo da exactamente 1,0", escalar(1.0, 0.12) == 1.0)
comprobar("a fondo del otro lado da exactamente -1,0", escalar(-1.0, 0.12) == -1.0)

comprobar("es simetrico", escalar(0.7, 0.12) == -escalar(-0.7, 0.12))

# --- decidir: habilitacion --------------------------------------------------
print("decidir()  -- el gatillo de habilitacion")

hab, ang, tra = decidir(ejes(traccion=1.0, direccion=1.0), AJ)
comprobar("sin ZR no se mueve, aunque los dos sticks esten a fondo",
          (hab, ang, tra) == (False, 0.0, 0.0), f"-> {(hab, ang, tra)}")

hab, ang, tra = decidir(ejes(zr=PULSADO), AJ)
comprobar("con ZR pero sticks en reposo, habilitado pero quieto",
          hab and ang == 0.0 and tra == 0.0, f"-> {(hab, ang, tra)}")

# El caso documentado: un gatillo que nadie ha tocado desde que arranco
# joy_node puede leerse 0,0. Con umbral -0,5 eso NO es pulsado, que es el lado
# seguro. Si el umbral fuera positivo, el carro arrancaria habilitado solo.
hab, _, tra = decidir(ejes(traccion=1.0, zr=0.0), AJ)
comprobar("un gatillo sin estrenar (0,0) cuenta como SIN pulsar",
          not hab and tra == 0.0, f"-> {(hab, tra)}")

hab, _, _ = decidir(ejes(zr=-0.49), AJ)
comprobar("medio pulsado por encima del umbral todavia no habilita", not hab)

hab, _, _ = decidir(ejes(zr=-0.51), AJ)
comprobar("pasado el umbral, habilita", hab)

# --- decidir: mando incompleto ----------------------------------------------
print("decidir()  -- un mando que no publica los ejes que se le piden")

comprobar("la configuracion por defecto necesita 6 ejes",
          ejes_necesarios(AJ) == 6, f"-> {ejes_necesarios(AJ)}")

# Un mando generico de 4 ejes. Leer axes[5] reventaria con IndexError dentro de
# un callback de ROS, que lo traga y deja de publicar sin parar el vehiculo.
comprobar("con menos ejes de los necesarios devuelve ceros y no revienta",
          decidir([0.0, 1.0, 0.0, 0.0], AJ) == (False, 0.0, 0.0))

comprobar("con la lista vacia tambien", decidir([], AJ) == (False, 0.0, 0.0))

# --- decidir: limites -------------------------------------------------------
print("decidir()  -- limites de velocidad y turbo")

_, _, tra = decidir(ejes(traccion=1.0, zr=PULSADO), AJ)
comprobar("a fondo sin turbo no pasa del limite normal",
          abs(tra) == AJ.limite_normal, f"-> {tra}")

_, _, tra = decidir(ejes(traccion=1.0, zr=PULSADO, zl=PULSADO), AJ)
comprobar("a fondo con turbo llega al limite de turbo",
          abs(tra) == AJ.limite_turbo, f"-> {tra}")

comprobar("el limite de turbo es mayor que el normal, no al reves",
          AJ.limite_turbo > AJ.limite_normal)

_, ang, _ = decidir(ejes(direccion=1.0, zr=PULSADO, zl=PULSADO), AJ)
comprobar("el turbo no toca la direccion", abs(ang) == AJ.limite_direccion,
          f"-> {ang}")

# Nada de lo que salga puede excederse, pase lo que pase con los ajustes.
suelto = AJ._replace(limite_normal=5.0, limite_direccion=5.0)
_, ang, tra = decidir(ejes(traccion=1.0, direccion=1.0, zr=PULSADO), suelto)
comprobar("un limite mal configurado se recorta a [-1, 1]",
          abs(ang) <= 1.0 and abs(tra) <= 1.0, f"-> {(ang, tra)}")

# --- decidir: inversiones ---------------------------------------------------
print("decidir()  -- las banderas de inversion hacen lo que dicen")

# No se afirma hacia donde gira la rueda: eso depende del cableado y lo resuelve
# la Parte 6 de la guia. Lo que se comprueba es que la bandera invierte el signo,
# que es el contrato del que depende esa correccion.
_, _, con = decidir(ejes(traccion=1.0, zr=PULSADO), AJ)
_, _, sin_ = decidir(ejes(traccion=1.0, zr=PULSADO),
                     AJ._replace(invertir_traccion=False))
comprobar("invertir_traccion cambia el signo y nada mas", con == -sin_,
          f"-> {con} vs {sin_}")

_, con, _ = decidir(ejes(direccion=1.0, zr=PULSADO),
                    AJ._replace(invertir_direccion=True))
_, sin_, _ = decidir(ejes(direccion=1.0, zr=PULSADO), AJ)
comprobar("invertir_direccion cambia el signo y nada mas", con == -sin_,
          f"-> {con} vs {sin_}")

# --- salida: el hombre muerto -----------------------------------------------
print("salida()   -- el hombre muerto")

comprobar("habilitado y con /joy reciente, pasa los valores",
          salida(True, 0.5, 0.3, t_ahora=100.0, t_ultimo_joy=99.9,
                 timeout_s=0.6) == (0.5, 0.3))

# El caso que justifica que esto viva en el temporizador: el mando se apago, el
# callback ya no corre, y el ultimo valor conocido era acelerando.
comprobar("si /joy lleva mas del timeout sin llegar, ceros aunque acelerara",
          salida(True, 0.9, 0.7, t_ahora=100.0, t_ultimo_joy=99.0,
                 timeout_s=0.6) == (0.0, 0.0))

comprobar("justo en el limite del timeout todavia NO ha vencido",
          salida(True, 0.5, 0.3, t_ahora=100.6, t_ultimo_joy=100.0,
                 timeout_s=0.6) == (0.5, 0.3))

comprobar("un pelo pasado el timeout, ceros",
          salida(True, 0.5, 0.3, t_ahora=100.61, t_ultimo_joy=100.0,
                 timeout_s=0.6) == (0.0, 0.0))

comprobar("sin habilitar, ceros aunque /joy llegue al instante",
          salida(False, 0.9, 0.7, t_ahora=100.0, t_ultimo_joy=100.0,
                 timeout_s=0.6) == (0.0, 0.0))

# Arranque en frio: t_ultimo_joy = 0,0 y time.monotonic() cuenta desde que
# arranco la maquina, o sea un numero grande. Si esto no venciera, el nodo
# publicaria basura entre que arranca y llega el primer mensaje del mando.
comprobar("al arrancar, antes del primer /joy, ya esta vencido",
          salida(True, 0.9, 0.7, t_ahora=48213.0, t_ultimo_joy=0.0,
                 timeout_s=0.6) == (0.0, 0.0))

# --- las dos juntas ---------------------------------------------------------
print("decidir() + salida()  -- la cadena completa")

# Soltar ZR tiene que parar por dos caminos independientes: decidir() devuelve
# ceros, y salida() los vuelve a poner a cero por no estar habilitado. Que
# sobren caminos es intencionado.
hab, ang, tra = decidir(ejes(traccion=1.0, direccion=1.0), AJ)
comprobar("soltar ZR para el carro por los dos caminos a la vez",
          salida(hab, ang, tra, 100.0, 100.0, 0.6) == (0.0, 0.0))

hab, ang, tra = decidir(ejes(traccion=1.0, zr=PULSADO), AJ)
comprobar("conduciendo de verdad, la cadena deja pasar la traccion",
          salida(hab, ang, tra, 100.0, 100.0, 0.6)[1] == tra != 0.0,
          f"-> {tra}")

print()
if FALLOS:
    print(f"{len(FALLOS)} FALLO(S): {', '.join(FALLOS)}")
    sys.exit(1)
print("Todas las comprobaciones pasan.")
