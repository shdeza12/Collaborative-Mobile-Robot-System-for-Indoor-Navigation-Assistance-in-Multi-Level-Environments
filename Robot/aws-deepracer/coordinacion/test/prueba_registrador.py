#!/usr/bin/env python3
"""Agota el registrador de mision con datos sinteticos. Sin ROS y sin simulador.

    python3 src/aws-deepracer/coordinacion/test/prueba_registrador.py

Por que con datos sinteticos y no con una corrida real: porque una corrida real
da UN caso, y el que salga. Aqui se construyen a mano los casos que importan
-el relevo, la mision de un solo nivel, la fallida, el ruido en reposo- y se
comprueba que cada metrica del §3 del protocolo sale del valor que se le puso.
Si alguien cambia el umbral de movimiento o la tolerancia de llegada, esto lo
dice antes de que lo diga una campana de 30 corridas.
"""

import json
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coordinacion.registrador import (  # noqa: E402
    ESQUEMA_VERSION, TOLERANCIA_LLEGADA_M, UMBRAL_MOVIMIENTO_MS,
    RegistroMision, entorno_hardware, entorno_simulacion)

OK = FALLOS = 0


def comprueba(titulo, condicion, detalle=""):
    global OK, FALLOS
    if condicion:
        OK += 1
        print(f"  [OK ] {titulo} {detalle}")
    else:
        FALLOS += 1
        print(f"  [MAL] {titulo} {detalle}")


def traza(reg, robot, t0, dt, velocidades, x0=0.0):
    """Genera muestras con las velocidades dadas, avanzando en x."""
    x = x0
    for i, v in enumerate(velocidades):
        x += v * dt
        reg.muestra(t0 + i * dt, robot, x, 0.0, 0.03, v, 0.0)


# --------------------------------------------------------------- 1. relevo
print("\n1. Mision entre niveles: las cuatro metricas")
reg = RegistroMision("m001", "piso1_etm1", "piso2_aula_307",
                     {"1": "robot1", "2": "robot2"}, t_solicitud=100.0)
reg.marca(100.25, 1, "robot1", "piso1_etm1")          # asignacion a 0.25 s
# robot1 quieto medio segundo y luego arranca: el primer movimiento es 100.6
traza(reg, "robot1", 100.0, 0.02, [0.0] * 30 + [0.3] * 200)
reg.marca(110.0, 2, "robot1", "piso1_escalera")        # transferencia
reg.marca(112.0, 3, "robot2", "piso2_aula_307")
# robot2 arranca 1.5 s despues de la transferencia
traza(reg, "robot2", 110.0, 0.02, [0.0] * 75 + [0.4] * 200, x0=15.0)
reg.marca(140.0, 4, "robot2", "piso2_aula_307")
reg.cerrar(140.0, True, "", 1, {"x": 15.0 + 0.4 * 0.02 * 200, "y": 0.0})
reg.entorno = entorno_simulacion("mundo_definitivo_piso1.world",
                                 "mundo_definitivo_piso1.yaml", 0.99,
                                 {"robot1": 7, "robot2": 7})
met = reg.metricas()
comprueba("t_asignacion sale del instante de la marca TRAMO_1",
          abs(met["t_asignacion_s"] - 0.25) < 1e-6, f"{met['t_asignacion_s']} s")
comprueba("t_respuesta usa la PRIMERA de las tres muestras seguidas",
          abs(met["t_respuesta_s"] - 0.60) < 1e-6, f"{met['t_respuesta_s']} s")
comprueba("el hueco del relevo se mide desde la transferencia",
          abs(met["hueco_relevo_s"] - 1.50) < 1e-6, f"{met['hueco_relevo_s']} s")
comprueba("t_asignacion es mucho menor que t_respuesta (§3.2)",
          met["t_asignacion_s"] < met["t_respuesta_s"])
comprueba("la mision entre niveles con un relevo es exitosa", met["exito"] is True)
comprueba("continuidad cumplida", met["continuidad"] is True)

# ---------------------------------------------- 2. el ruido no dispara nada
print("\n2. El ruido en reposo no cuenta como movimiento")
reg2 = RegistroMision("m002", "a", "b", {"1": "robot1"}, t_solicitud=0.0)
reg2.marca(0.1, 1, "robot1", "b")
# picos aislados por encima del umbral, nunca tres seguidos
traza(reg2, "robot1", 0.0, 0.02,
      [0.0, 0.05, 0.0, 0.05, 0.0, 0.05, 0.0] * 5)
comprueba("picos sueltos sobre el umbral no disparan t_respuesta",
          reg2.metricas()["t_respuesta_s"] is None)
reg2.muestra(10.0, "robot1", 0, 0, 0, 0.05, 0)
reg2.muestra(10.02, "robot1", 0, 0, 0, 0.05, 0)
reg2.muestra(10.04, "robot1", 0, 0, 0, 0.05, 0)
comprueba("tres seguidas si lo disparan",
          abs(reg2.metricas()["t_respuesta_s"] - 10.0) < 1e-6)

print("\n3. Dos muestras identicas no confunden el instante")
reg3 = RegistroMision("m003", "a", "b", {"1": "robot1"}, t_solicitud=0.0)
reg3.marca(0.0, 1, "robot1", "b")
for t in (0.0, 0.1):                       # dos filas byte a byte iguales
    reg3.muestra(t, "robot1", 1.0, 2.0, 0.03, 0.0, 0.5)
for i, t in enumerate((0.2, 0.3, 0.4)):
    reg3.muestra(t, "robot1", 1.0, 2.0, 0.03, 0.5, 0.5)
comprueba("el instante es 0.2 y no 0.0",
          abs(reg3.metricas()["t_respuesta_s"] - 0.2) < 1e-6,
          f"{reg3.metricas()['t_respuesta_s']}")

# ------------------------------------------------------ 4. criterios de exito
print("\n4. Los tres criterios del §3.3, uno a uno")
def mision_simple(error_m, completada=True, fallida=False, relevos=0):
    r = RegistroMision("mx", "a", "b", {"1": "robot1"}, t_solicitud=0.0)
    r.marca(0.1, 1, "robot1", "b")
    traza(r, "robot1", 0.0, 0.02, [0.5] * 10)
    if fallida:
        r.marca(5.0, 5, "robot1", "b")
    if completada:
        r.marca(6.0, 4, "robot1", "b")
    ultimo = r.trazas["robot1"][-1]
    r.cerrar(6.0, True, "", relevos, {"x": ultimo[1] + error_m, "y": 0.0})
    return r.metricas()

m = mision_simple(0.10)
comprueba("llegada dentro de tolerancia -> exito", m["exito"] is True, f"{m['error_llegada_m']} m")
m = mision_simple(0.30)
comprueba("llegada fuera de tolerancia -> fallo", m["exito"] is False, f"{m['error_llegada_m']} m")
comprueba("y el criterio que falla es el de llegada",
          m["criterios_exito"]["llegada_a_025_m"] is False
          and m["criterios_exito"]["completada_sin_fallida"] is True)
m = mision_simple(0.10, fallida=True)
comprueba("si paso por FALLIDA no hay exito aunque llegue", m["exito"] is False)
m = mision_simple(0.10, completada=False)
comprueba("sin COMPLETADA no hay exito", m["exito"] is False)
comprueba("el umbral es exactamente la xy_goal_tolerance de Nav2",
          abs(TOLERANCIA_LLEGADA_M - 0.25) < 1e-9)
comprueba("el umbral de movimiento es el del §3.1",
          abs(UMBRAL_MOVIMIENTO_MS - 0.02) < 1e-9)

# ------------------------------------------------- 5. el esquema es el mismo
print("\n5. El esquema no cambia entre simulacion y hardware (§2.3 del plan)")
sim = entorno_simulacion("m.world", "m.yaml", 0.99, {"robot1": 7})
hw = entorno_hardware("m.yaml", {"robot1": 7}, "deepracer-02", "jazzy", 0.31)
comprueba("las dos condiciones tienen las MISMAS claves",
          set(sim) == set(hw), f"{len(sim)} claves")
comprueba("en simulacion la verdad es odom y hay rtf",
          sim["verdad_terreno"] == "odom" and sim["rtf"] == 0.99)
comprueba("en hardware la verdad es medicion externa y el rtf va vacio",
          hw["verdad_terreno"] == "medicion_externa" and hw["rtf"] is None)
comprueba("los campos de hardware existen en simulacion, vacios",
          sim["vehiculo_id"] is None and sim["medicion_externa_m"] is None)

# ---------------------------------------------------------- 6. el archivo
print("\n6. Un archivo por mision, procesable sin intervencion (RF-25)")
with tempfile.TemporaryDirectory() as d:
    ruta = reg.guardar(d)
    comprueba("el nombre lleva el id de la mision", ruta.name == "mision_m001.json")
    datos = json.loads(ruta.read_text())
    comprueba("es JSON valido y declara version de esquema",
              datos["esquema"] == ESQUEMA_VERSION, datos["esquema"])
    for clave in ("mision_id", "condicion", "solicitud", "asignacion", "marcas",
                  "metricas", "cierre", "trazas", "entorno", "descarte"):
        comprueba(f"lleva '{clave}'", clave in datos)
    comprueba("la traza declara su formato",
              datos["trazas"]["formato"] == ["t", "x", "y", "z", "v", "yaw"])
    comprueba("el hueco de descarte queda ABIERTO, no decidido aqui",
              datos["descarte"] == {"descartada": False, "causa": None,
                                    "evidencia": None})
    comprueba("las marcas distinguen la extraordinaria del tick de 1 Hz",
              all("extraordinaria" in x for x in datos["marcas"]))

print("\n" + "=" * 62)
if FALLOS:
    print(f"{FALLOS} comprobaciones FALLAN de {OK + FALLOS}")
    print("=" * 62)
    sys.exit(1)
print(f"Todas las comprobaciones pasan ({OK}).")
print("=" * 62)
