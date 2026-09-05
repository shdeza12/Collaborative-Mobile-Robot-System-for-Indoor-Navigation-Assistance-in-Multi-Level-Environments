#!/usr/bin/env python3
"""Prueba de la compuerta de parametros vivos.

POR QUE EXISTE
--------------
El 2026-09-04, en el Piloto 3, el porton de robot2 aborto con

    amcl/alpha2: NO SE PUDO LEER
    ...
    NO GRABES: la pila corre con parametros distintos de los del repositorio.

y las dos cosas eran falsas. El mismo nodo /robot2/amcl contesto alpha1,
alpha3, alpha4 y alpha5 en esa misma tanda, asi que ni "la pila no esta
arriba" ni "otro ROS_DOMAIN_ID" podian ser ciertas; fallo UNA llamada. Con la
pila todavia viva se leyo alpha2 despues: 0.01, igual que el YAML.

Dos defectos, y esta prueba cubre los dos:

  1. una lectura que se agota no se reintentaba, y con la ventana de 2,6 min
     de la condicion inicial un timeout suelto cuesta la corrida entera;
  2. "no pude leer" se contaba como "es distinto", que es una afirmacion
     mucho mas fuerte y en este caso falsa.

El doble de lectura sustituye a _leer_una_vez, cuyo contrato es devolver el
valor YA extraido ('0.01') o None; el 'Double value is:' lo deshace esa
funcion y no llega hasta aqui.

Se ejecuta sin workspace sourceado a proposito: no importa rclpy.

    python3 herramientas/prueba_verificar_parametros_vivos.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verificar_parametros_vivos as v  # noqa: E402

fallos = []


def comprobar(condicion, titulo):
    print(f"  {'ok  ' if condicion else 'FALLA'}  {titulo}")
    if not condicion:
        fallos.append(titulo)


print("1. una lectura que falla y luego contesta")

llamadas = []


def lector_intermitente(nodo, parametro):
    llamadas.append(parametro)
    if len(llamadas) == 1:
        return None
    return "0.01"


vivo = v._param_vivo("/robot2/amcl", "alpha2", intentos=3, pausa_s=0.0,
                     lector=lector_intermitente)
comprobar(vivo == "0.01", "el caso alpha2 del 2026-09-04 se recupera")
comprobar(len(llamadas) == 2, "reintenta una sola vez si la segunda contesta")

print("2. una lectura que nunca contesta")

intentos = []


def lector_mudo(nodo, parametro):
    intentos.append(parametro)
    return None


vivo = v._param_vivo("/robot2/amcl", "alpha2", intentos=3, pausa_s=0.0,
                     lector=lector_mudo)
comprobar(vivo is None, "tras agotar los intentos devuelve None")
comprobar(len(intentos) == 3, "hace exactamente los 3 intentos, ni mas ni menos")

print("3. una lectura buena no se repite")

buenas = []


def lector_sano(nodo, parametro):
    buenas.append(parametro)
    return "0.15"


vivo = v._param_vivo("/robot1/controller_server",
                     "goal_checker.xy_goal_tolerance",
                     intentos=3, pausa_s=0.0, lector=lector_sano)
comprobar(vivo == "0.15", "devuelve el valor a la primera")
comprobar(len(buenas) == 1, "no gasta reintentos cuando no hace falta")

print("4. no leer y ser distinto son dos cosas distintas")

comprobar(v.codigo_de_salida([], []) == 0,
          "todo coincide -> 0")
comprobar(v.codigo_de_salida([], ["/robot2/amcl alpha2"]) == 2,
          "solo ilegibles -> 2, que NO es el codigo del desajuste")
comprobar(v.codigo_de_salida([("amcl", "alpha1", "0.2", 0.01)], []) == 1,
          "desajuste real -> 1")
comprobar(v.codigo_de_salida([("amcl", "alpha1", "0.2", 0.01)],
                             ["/robot2/amcl alpha2"]) == 1,
          "con desajuste real manda el desajuste, no el ilegible")

print("5. lo que ya funcionaba sigue funcionando")

comprobar(v._igual("0.15", 0.150), "0.15 y 0.150 son el mismo numero")
comprobar(v._igual("False", False), "False de ros2 y false del YAML coinciden")
comprobar(not v._igual("0.25", 0.15), "0.25 contra 0.15 sigue siendo distinto")

print("")
if fallos:
    print(f"FALLAN {len(fallos)} comprobaciones:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("Todas las comprobaciones pasan.")
