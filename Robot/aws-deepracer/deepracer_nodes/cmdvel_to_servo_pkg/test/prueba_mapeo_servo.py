#!/usr/bin/env python3
"""Fija el mapeo de /cmd_vel a los servos del vehiculo fisico.

    python3 src/aws-deepracer/deepracer_nodes/cmdvel_to_servo_pkg/test/prueba_mapeo_servo.py

Por que existe: hasta el 2026-08-26 las dos funciones de mapeo comparaban los
umbrales de menor a mayor, de modo que la primera rama se tragaba todo y las dos
siguientes eran codigo muerto. El efecto no da error en ningun sitio -el
vehiculo simplemente se mueve mal- y solo se vio midiendo sobre hardware. Una
prueba que fije los escalones lo habria cazado en el sitio.

Las funciones no usan 'self', asi que se llaman sin instanciar el nodo y esto
corre sin rclpy.init() y sin vehiculo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cmdvel_to_servo_pkg import constants                      # noqa: E402
from cmdvel_to_servo_pkg.cmdvel_to_servo_node import CmdvelToServoNode  # noqa: E402

V = constants.VehicleNav2Dynamics
A = constants.ActionValues
OK = FALLOS = 0


def comprueba(titulo, obtenido, esperado):
    global OK, FALLOS
    if obtenido == esperado:
        OK += 1
        print(f"  [OK ] {titulo}  -> {obtenido}")
    else:
        FALLOS += 1
        print(f"  [MAL] {titulo}  -> {obtenido}, esperaba {esperado}")


throttle = CmdvelToServoNode.get_mapped_throttle
steering = CmdvelToServoNode.get_mapped_steering

print("\n1. Traccion: los cuatro escalones existen, y son monotonos")
comprueba("v = MAX_SPEED (tope)", throttle(None, V.MAX_SPEED), A.MAX_THROTTLE_OUTPUT)
comprueba("pct justo en MIN_THROTTLE_RATIO (0.5)",
          throttle(None, V.MAX_SPEED * V.MIN_THROTTLE_RATIO), A.MAX_THROTTLE_OUTPUT)
comprueba("pct justo en MID_THROTTLE_RATIO (0.3)",
          throttle(None, V.MAX_SPEED * V.MID_THROTTLE_RATIO), A.MID_THROTTLE_OUTPUT)
comprueba("pct justo en MAX_THROTTLE_RATIO (0.1)",
          throttle(None, V.MAX_SPEED * V.MAX_THROTTLE_RATIO), A.MIN_THROTTLE_OUTPUT)
comprueba("por debajo del umbral mas bajo", throttle(None, 0.0), A.DEFAULT_OUTPUT)

salidas = [throttle(None, V.MAX_SPEED * r)
           for r in (V.MAX_THROTTLE_RATIO, V.MID_THROTTLE_RATIO, V.MIN_THROTTLE_RATIO)]
comprueba("los tres escalones son DISTINTOS (no hay codigo muerto)",
          len(set(salidas)), 3)
comprueba("y crecen con la velocidad", salidas == sorted(salidas), True)

print("\n2. Direccion: mismo contrato")
comprueba("giro a tope", steering(None, V.MAX_STEER), A.MAX_STEERING_OUTPUT)
comprueba("pct justo en MIN_STEERING_RATIO (0.8)",
          steering(None, V.MAX_STEER * V.MIN_STEERING_RATIO), A.MAX_STEERING_OUTPUT)
comprueba("pct justo en MID_STEERING_RATIO (0.4)",
          steering(None, V.MAX_STEER * V.MID_STEERING_RATIO), A.MID_STEERING_OUTPUT)
comprueba("pct justo en MAX_STEERING_RATIO (0.2)",
          steering(None, V.MAX_STEER * V.MAX_STEERING_RATIO), A.MIN_STEERING_OUTPUT)
comprueba("giro despreciable", steering(None, 0.0), A.DEFAULT_OUTPUT)

giros = [steering(None, V.MAX_STEER * r)
         for r in (V.MAX_STEERING_RATIO, V.MID_STEERING_RATIO, V.MIN_STEERING_RATIO)]
comprueba("los tres escalones son DISTINTOS", len(set(giros)), 3)
comprueba("y crecen con el angulo", giros == sorted(giros), True)

print("\n3. El signo se conserva")
comprueba("marcha atras da el mismo escalon que adelante",
          throttle(None, -V.MAX_SPEED), throttle(None, V.MAX_SPEED))
comprueba("giro a la izquierda, el mismo que a la derecha",
          steering(None, -V.MAX_STEER), steering(None, V.MAX_STEER))

print("\n4. La cadena de mando publica donde el vehiculo escucha")
comprueba("el topico de publicacion es absoluto",
          constants.ACTION_PUBLISH_TOPIC.startswith("/"), True)
comprueba("y es el del servo_pkg del vehiculo",
          constants.ACTION_PUBLISH_TOPIC, "/ctrl_pkg/servo_msg")

print("\n5. LO QUE ESTA PRUEBA NO ARREGLA")
umbral = V.MAX_SPEED * V.MAX_THROTTLE_RATIO
print(f"  El escalon mas bajo esta en {umbral:.2f} m/s, porque MAX_SPEED vale {V.MAX_SPEED} m/s.")
print("  Nav2 pide 0.25 m/s en curva y 0.05 en la aproximacion, o sea que SIGUE")
print("  devolviendo cero ahi. Ordenar las comparaciones arregla el mapeo, no la")
print("  escala. Eso es calibracion contra el vehiculo y esta sin decidir.")
comprueba("y queda registrado que 0.25 m/s todavia da cero",
          throttle(None, 0.25), A.DEFAULT_OUTPUT)

print("\n" + "=" * 62)
if FALLOS:
    print(f"{FALLOS} comprobaciones FALLAN de {OK + FALLOS}")
    sys.exit(1)
print(f"Todas las comprobaciones pasan ({OK}).")
print("=" * 62)
