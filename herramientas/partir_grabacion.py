#!/usr/bin/env python3
"""Parte una grabacion de varias misiones en una grabacion por mision.

    python3 herramientas/partir_grabacion.py <grabacion> <salida> \
        --mision G6_01=<registro_del_coordinador.json> [--mision ...]

El 16-oct la campaña de los vehiculos se grabo entera en una sola grabacion
(decision del equipo), y componer_registro.py exige una mision por grabacion.
Cada mision sale de la ventana [t_solicitud - 2 s, t_cierre + 5 s] que trae el
registro del coordinador (mision_manual_*.json), y queda en <salida>/mision_<nombre>.

El catalogo (/coordinacion/puntos_interes) se publica una vez al arrancar el
coordinador, asi que casi ninguna ventana lo trae. Se copia el ultimo visto
antes de cada ventana al instante en que esta empieza, para que la grabacion
partida se lea igual que una grabada por separado.

Hace falta el entorno de Humble y el del espacio de trabajo (coordinacion_msgs
no se usa, pero rosbag2_py necesita las definiciones de los tipos grabados):
    source ~/deepracer_sim_ws/install/setup.bash
"""
import argparse
import json
import os
import sys

import rosbag2_py

ANTES_S = 2.0
DESPUES_S = 5.0
CATALOGO = "/coordinacion/puntos_interes"


def ventanas(misiones):
    salida = []
    for nombre, ruta in misiones:
        with open(ruta) as f:
            r = json.load(f)
        t0 = r["solicitud"]["t_solicitud"]
        t1 = (r.get("cierre") or {}).get("t")
        if t1 is None:
            sys.exit(f"{ruta}: el registro no tiene cierre, la mision no termino")
        salida.append((nombre, int((t0 - ANTES_S) * 1e9), int((t1 + DESPUES_S) * 1e9)))
    return salida


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("grabacion")
    p.add_argument("salida")
    p.add_argument("--mision", action="append", required=True, metavar="NOMBRE=REGISTRO")
    a = p.parse_args()
    misiones = [m.split("=", 1) for m in a.mision]
    vs = ventanas(misiones)
    os.makedirs(a.salida, exist_ok=True)
    for nombre, _, _ in vs:
        if os.path.exists(os.path.join(a.salida, f"mision_{nombre}")):
            sys.exit(f"ya existe {a.salida}/mision_{nombre}: no se sobrescribe")

    lector = rosbag2_py.SequentialReader()
    lector.open(rosbag2_py.StorageOptions(uri=a.grabacion, storage_id="mcap"),
                rosbag2_py.ConverterOptions("cdr", "cdr"))
    topicos = lector.get_all_topics_and_types()

    escritores, cuenta, catalogo_puesto = {}, {}, set()
    for nombre, _, _ in vs:
        w = rosbag2_py.SequentialWriter()
        w.open(rosbag2_py.StorageOptions(
            uri=os.path.join(a.salida, f"mision_{nombre}"), storage_id="mcap"),
            rosbag2_py.ConverterOptions("cdr", "cdr"))
        for t in topicos:
            w.create_topic(t)
        escritores[nombre], cuenta[nombre] = w, 0

    ultimo_catalogo = None
    while lector.has_next():
        topico, datos, t = lector.read_next()
        if topico == CATALOGO:
            ultimo_catalogo = datos
        for nombre, ini, fin in vs:
            if not ini <= t <= fin:
                continue
            if nombre not in catalogo_puesto:
                catalogo_puesto.add(nombre)
                if topico != CATALOGO and ultimo_catalogo is not None:
                    escritores[nombre].write(CATALOGO, ultimo_catalogo, ini)
                    cuenta[nombre] += 1
            escritores[nombre].write(topico, datos, t)
            cuenta[nombre] += 1

    for nombre, ini, fin in vs:
        del escritores[nombre]   # cierra el archivo y escribe metadata.yaml
        print(f"mision_{nombre}: {cuenta[nombre]} mensajes en {(fin - ini) / 1e9:.1f} s"
              + ("" if nombre in catalogo_puesto else "  (VENTANA VACIA)"))


if __name__ == "__main__":
    main()
