#!/usr/bin/env python3
"""Dice si un bag de LiDAR sirve para construir un mapa, ANTES de intentarlo.

POR QUE EXISTE
--------------
El 28-ago se grabaron cinco bags en el pasillo para levantar el mapa. Los cinco
se dieron por buenos porque `ros2 bag info` contestaba con cifras grandes -813 s
y 5340 barridos entre todos-. El 2026-09-01, al pasarlos por la cadena de mapeo,
salio un disco radial sin paredes en vez de un pasillo.

La razon no era la que estaba escrita. Se creia que el problema era el unico
topico grabado -sin `/tf` ni `/odom` no hay como componer los barridos-. Al
medirlo resulto haber una razon anterior y peor:

    bag         duracion   quieto   movimiento   % quieto
    1445           57,9 s   57,9 s        0,0 s     100,0
    1447           87,8 s   65,0 s       22,7 s      74,1
    1450            5,1 s    5,1 s        0,0 s     100,0
    1451          257,6 s  228,4 s       29,2 s      88,7
    1456          404,4 s  326,2 s       78,2 s      80,7
    TOTAL         812,8 s  682,6 s      130,2 s      84,0

**El 84 % de la grabacion es un LiDAR quieto en el suelo.** Aunque se hubiera
grabado la TF, el mapa no existiria: no hay desplazamiento del que triangular
estructura. Un sensor que no se mueve produce una rosa de rayos, no un plano.

Nada de esto se veia desde el escritorio, y ninguna herramienta del proyecto lo
preguntaba. Esta si.

COMO LO MIDE, Y POR QUE ASI
---------------------------
No usa odometria. Si la usara, seria circular: rf2o es justo lo que se quiere
poder creer despues, y en un pasillo uniforme se congela (R3). Se mira solo lo
que el sensor ve.

Se comparan dos barridos separados **1 s** y se toma la **mediana** de la
diferencia entre rayos validos en ambos. Mediana y no media: una persona que
cruza el pasillo mueve unos pocos rayos muchisimo, y la media lo confundiria con
movimiento del sensor.

    mediana < UMBRAL  ->  el sensor estaba quieto en ese segundo
    mediana >= UMBRAL ->  el sensor se movio

UMBRAL = 0,05 m. Sale del ruido del propio sensor: en los tramos planos de los
bags del 28-ago la mediana se queda por debajo de 0,02 m, y empujando el carro a
0,5 m/s la separacion entre barridos consecutivos a 7 Hz es de 7 cm.

EL CRITERIO DE ACEPTACION, Y DE DONDE SALE
------------------------------------------
Se fija por la geometria de la prueba, no por el dato:

- **>= 60 s de movimiento.** Una recta de 20 m empujada a ~0,5 m/s son 40 s de
  ida; ida y vuelta, 80 s. Por debajo de 60 s no se recorrio la recta entera.
- **<= 40 % de tiempo quieto.** Deja sitio para las paradas de los extremos y
  para el arranque, y nada mas.

Un bag que no cumple las dos NO se lleva a la cadena de mapeo: el mapa saldria
malo y costaria media hora descubrir por que.

USO
---
    python3 herramientas/comprobar_movimiento_bag.py mapas/bag_mapa_1451
    python3 herramientas/comprobar_movimiento_bag.py ruta/al/bag_0.mcap

Acepta la carpeta del bag o el `.mcap` suelto. El `.mcap` suelto es la via para
un bag al que le falte la `metadata.yaml`, como `bag_mapa_1456`.

Codigo de salida 0 si el bag sirve, 1 si no, 2 si no se pudo leer.
"""

import argparse
import math
import os
import statistics
import sys

# El sensor se considera quieto si la mediana de la diferencia entre dos
# barridos separados 1 s se queda por debajo de esto. Ver el encabezado.
UMBRAL_QUIETO_M = 0.05

# Criterio de aceptacion. Derivado de la geometria de G2, no del dato.
MOVIMIENTO_MINIMO_S = 60.0
QUIETO_MAXIMO_FRAC = 0.40


class ErrorLectura(Exception):
    """El bag no se pudo abrir o no trae barridos."""


def _abrir(ruta):
    """Devuelve un SequentialReader abierto sobre carpeta o .mcap suelto."""
    import rosbag2_py

    if ruta.endswith(".mcap"):
        opciones = rosbag2_py.StorageOptions(uri=ruta, storage_id="mcap")
    else:
        opciones = rosbag2_py.StorageOptions(uri=ruta)
    lector = rosbag2_py.SequentialReader()
    try:
        lector.open(opciones, rosbag2_py.ConverterOptions("", ""))
    except RuntimeError as e:
        raise ErrorLectura(
            f"no se pudo abrir {ruta}: {e}\n"
            "  Si es un bag de Jazzy, adaptalo antes:\n"
            "    python3 herramientas/adaptar_bag_jazzy.py <bag> -o /tmp/<bag>\n"
            "  Si falta el plugin de almacenamiento:\n"
            "    sudo apt install ros-humble-rosbag2-storage-mcap") from e
    return lector


def leer_barridos(ruta):
    """Devuelve (nombre_topico, [(t_segundos, LaserScan)], otros_topicos)."""
    from rclpy.serialization import deserialize_message
    from sensor_msgs.msg import LaserScan

    lector = _abrir(ruta)
    tipos = {t.name: t.type for t in lector.get_all_topics_and_types()}
    laser = [n for n, t in tipos.items() if t == "sensor_msgs/msg/LaserScan"]
    if not laser:
        raise ErrorLectura(
            f"{ruta} no trae ningun topico de tipo sensor_msgs/msg/LaserScan. "
            f"Trae: {', '.join(sorted(tipos)) or '(ninguno)'}")
    topico = laser[0]

    barridos = []
    while lector.has_next():
        nombre, datos, t = lector.read_next()
        if nombre == topico:
            barridos.append((t * 1e-9, deserialize_message(datos, LaserScan)))
    if len(barridos) < 2:
        raise ErrorLectura(f"{ruta} solo trae {len(barridos)} barrido(s)")
    return topico, barridos, sorted(n for n in tipos if n != topico)


def diferencia(a, b):
    """Mediana de |a-b| sobre los rayos validos en AMBOS barridos.

    Mediana y no media: una persona cruzando mueve pocos rayos muchisimo.
    Devuelve nan si no hay ningun rayo comparable.
    """
    d = [abs(x - y) for x, y in zip(a.ranges, b.ranges)
         if math.isfinite(x) and math.isfinite(y)]
    return statistics.median(d) if d else float("nan")


def repartir(barridos, umbral=UMBRAL_QUIETO_M):
    """Reparte la duracion del bag en segundos quieto y en movimiento.

    Devuelve (duracion_s, quieto_s, movimiento_s, hz).
    """
    duracion = barridos[-1][0] - barridos[0][0]
    hz = (len(barridos) - 1) / duracion if duracion > 0 else float("nan")
    salto = max(1, round(hz))  # dos barridos separados ~1 s
    quietos = movidos = 0
    for i in range(len(barridos) - salto):
        d = diferencia(barridos[i][1], barridos[i + salto][1])
        if math.isnan(d):
            continue
        if d < umbral:
            quietos += 1
        else:
            movidos += 1
    total = quietos + movidos
    if total == 0:
        return duracion, float("nan"), float("nan"), hz
    escala = duracion / total
    return duracion, quietos * escala, movidos * escala, hz


def veredicto(duracion, quieto, movimiento):
    """Devuelve (sirve, [motivos]). Los motivos explican el NO."""
    motivos = []
    if math.isnan(movimiento):
        return False, ["no hubo ningun par de barridos comparable"]
    if movimiento < MOVIMIENTO_MINIMO_S:
        motivos.append(
            f"solo {movimiento:.1f} s de movimiento, y hacen falta "
            f"{MOVIMIENTO_MINIMO_S:.0f} s -una recta de 20 m empujada a 0,5 m/s "
            "son 40 s de ida y 80 s de ida y vuelta-")
    if duracion > 0 and quieto / duracion > QUIETO_MAXIMO_FRAC:
        motivos.append(
            f"{100 * quieto / duracion:.1f} % del bag es sensor quieto, y el "
            f"maximo es {100 * QUIETO_MAXIMO_FRAC:.0f} %")
    return not motivos, motivos


def informe(ruta):
    """Imprime el informe y devuelve el codigo de salida."""
    try:
        topico, barridos, otros = leer_barridos(ruta)
    except ErrorLectura as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    duracion, quieto, movimiento, hz = repartir(barridos)
    sirve, motivos = veredicto(duracion, quieto, movimiento)

    print(f"{ruta}")
    print(f"  topico de barrido : {topico}")
    if topico != "/scan":
        print("      AVISO: no es '/scan'. rf2o escucha '/scan' y no recibira "
              "nada.")
        print("      En el carrito, arranca el LiDAR con "
              "lidar_vehiculo.launch.py,")
        print("      o remapea al reproducir: "
              f"--remap {topico}:=/scan")
    print(f"  otros topicos     : {', '.join(otros) if otros else '(ninguno)'}")
    if not any(t.endswith("/odom") for t in otros):
        print("      AVISO: sin '/odom'. Para mapear habra que generarlo fuera "
              "de linea con rf2o.")
    print(f"  barridos          : {len(barridos)} a {hz:.2f} Hz")
    print(f"  duracion          : {duracion:.1f} s")
    print(f"  sensor quieto     : {quieto:.1f} s  "
          f"({100 * quieto / duracion:.1f} %)")
    print(f"  sensor en movim.  : {movimiento:.1f} s  "
          f"({100 * movimiento / duracion:.1f} %)")
    print()
    if sirve:
        print("  SIRVE para construir un mapa.")
        return 0
    print("  NO SIRVE para construir un mapa:")
    for m in motivos:
        print(f"    - {m}")
    return 1


def main():
    p = argparse.ArgumentParser(
        description="Dice si un bag de LiDAR sirve para construir un mapa.")
    p.add_argument("bag", nargs="+",
                   help="carpeta del bag, o el .mcap suelto")
    args = p.parse_args()

    peor = 0
    for i, ruta in enumerate(args.bag):
        if i:
            print()
        peor = max(peor, informe(os.path.abspath(ruta.rstrip("/"))))
    return peor


if __name__ == "__main__":
    sys.exit(main())
