#!/usr/bin/env python3
"""Fija como se resuelve el servicio de velocidad maxima en cada destino.

    python3 src/aws-deepracer/deepracer_nodes/cmdvel_to_servo_pkg/test/prueba_servicio_velocidad.py

POR QUE EXISTE
--------------
El 2026-09-22, al desplegar por primera vez 'cmdvel_to_servo_pkg' sobre los dos
vehiculos, el nodo NO ARRANCO:

    ImportError: cannot import name 'SetMaxSpeedSrv' from
    'deepracer_interfaces_pkg.srv'

El 'deepracer_interfaces_pkg' que viene de fabrica en la tarjeta declara 30
servicios y 'SetMaxSpeedSrv' no es ninguno de ellos. El del repositorio si lo
tiene, por eso en simulacion nunca se noto. Es el mismo genero de diferencia que
'S19_spike_p1_p2_hardware.md' seccion 2.4 ya habia registrado para
'ServoCtrlMsg', y la regla que de alli se deduce es la misma: NO se superpone
nuestro 'deepracer_interfaces_pkg' al del vehiculo -'servo_pkg' esta compilado
contra el suyo-, asi que el nodo tiene que apanarselas con lo que hay.

Lo que hay es 'NavThrottleSrv', que el vehiculo si trae y que es
ESTRUCTURALMENTE IDENTICO: un 'float32' de entrada y un 'int32 error' de salida.
Solo cambia el nombre del campo -'throttle' en vez de 'max_speed_pct'-, y su
comentario en el .srv dice literalmente "Throttle percentage scale value", que
es lo que el nodo necesita.

De ahi 'resolver_servicio_velocidad': prefiere 'SetMaxSpeedSrv' cuando existe
-para no cambiar nada en simulacion- y cae en 'NavThrottleSrv' cuando no. Si no
hubiera ninguno de los dos, el nodo debe seguir arrancando SIN el servicio: la
conversion de /cmd_vel es lo esencial y el ajuste en caliente es un extra.

POR QUE LA FUNCION RECIBE EL MODULO
-----------------------------------
Para poder probar los tres casos desde el portatil, donde los dos servicios
existen. Pasando un objeto falso se reproduce el vehiculo sin vehiculo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cmdvel_to_servo_pkg.cmdvel_to_servo_node import (            # noqa: E402
    resolver_servicio_velocidad,
)

OK = FALLOS = 0


def comprueba(titulo, obtenido, esperado):
    global OK, FALLOS
    if obtenido == esperado:
        OK += 1
        print(f"  [OK ] {titulo}  -> {obtenido}")
    else:
        FALLOS += 1
        print(f"  [MAL] {titulo}  -> {obtenido}, esperaba {esperado}")


class ModuloFalso:
    """Un 'deepracer_interfaces_pkg.srv' de mentira con los servicios que se le den."""

    def __init__(self, **servicios):
        for nombre, valor in servicios.items():
            setattr(self, nombre, valor)


print("\n1. El portatil: estan los dos, y gana el nuestro")
tipo, campo = resolver_servicio_velocidad(
    ModuloFalso(SetMaxSpeedSrv="TIPO_NUESTRO", NavThrottleSrv="TIPO_DEL_CARRO"))
comprueba("con los dos disponibles se elige SetMaxSpeedSrv", tipo, "TIPO_NUESTRO")
comprueba("y el campo que se lee es max_speed_pct", campo, "max_speed_pct")

print("\n2. El vehiculo: solo esta NavThrottleSrv")
tipo, campo = resolver_servicio_velocidad(ModuloFalso(NavThrottleSrv="TIPO_DEL_CARRO"))
comprueba("sin SetMaxSpeedSrv se cae en NavThrottleSrv", tipo, "TIPO_DEL_CARRO")
comprueba("y el campo que se lee es throttle", campo, "throttle")

print("\n3. Ninguno de los dos: el nodo no puede reventar")
tipo, campo = resolver_servicio_velocidad(ModuloFalso())
comprueba("sin ningun servicio compatible no hay tipo", tipo, None)
comprueba("y tampoco campo", campo, None)

print("\n4. Los dos tipos reales son intercambiables, no solo de nombre")
try:
    from deepracer_interfaces_pkg.srv import NavThrottleSrv, SetMaxSpeedSrv

    peticion_nuestra = SetMaxSpeedSrv.Request.get_fields_and_field_types()
    peticion_carro = NavThrottleSrv.Request.get_fields_and_field_types()
    respuesta_nuestra = SetMaxSpeedSrv.Response.get_fields_and_field_types()
    respuesta_carro = NavThrottleSrv.Response.get_fields_and_field_types()

    comprueba("la peticion de los dos tiene un solo campo",
              (len(peticion_nuestra), len(peticion_carro)), (1, 1))
    comprueba("y en los dos es float",
              (list(peticion_nuestra.values()), list(peticion_carro.values())),
              (["float"], ["float"]))
    comprueba("la respuesta de los dos es identica campo a campo",
              respuesta_nuestra, respuesta_carro)
    comprueba("el campo que devuelve resolver_servicio_velocidad existe de verdad",
              (resolver_servicio_velocidad(
                  ModuloFalso(SetMaxSpeedSrv=SetMaxSpeedSrv))[1] in peticion_nuestra,
               resolver_servicio_velocidad(
                   ModuloFalso(NavThrottleSrv=NavThrottleSrv))[1] in peticion_carro),
              (True, True))
except ImportError as ex:
    print(f"  [OMITIDA] no hay deepracer_interfaces_pkg instalado: {ex}")

print(f"\n{OK} comprobaciones pasan, {FALLOS} fallan.")
sys.exit(1 if FALLOS else 0)
