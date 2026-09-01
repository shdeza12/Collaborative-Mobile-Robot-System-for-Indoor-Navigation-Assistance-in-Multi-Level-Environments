#!/usr/bin/env python3
"""Hace legible en Humble un bag grabado en la tarjeta Jazzy del vehiculo.

POR QUE EXISTE
--------------
La tarjeta del DeepRacer corre Ubuntu 24.04 con ROS 2 Jazzy; el PC donde se
analiza corre Humble. Un bag grabado alli no se abre aqui, y falla por el sitio
menos evidente: no por el `.mcap`, que es autodescriptivo y no cambio, sino por
el `metadata.yaml` que lo acompana.

    RuntimeError: Exception on parsing info file:
    yaml-cpp: error at line 15, column 11: bad conversion

Jazzy escribe la metadata en **version 9**, donde `offered_qos_profiles` es una
secuencia YAML anidada y los enums de QoS van como texto (`reliable`,
`volatile`). Humble espera en ese mismo sitio una **cadena** con el YAML dentro
y los enums como **enteros** de `rmw/types.h`. Su `yaml-cpp` intenta convertir
secuencia -> string y aborta. La linea 15 columna 11 del mensaje es exactamente
el guion del primer elemento de la secuencia.

Se descubrio el 2026-09-01 comprobando, tres dias antes, si el bag del G2 del
viernes se iba a poder analizar. Los cinco bags del 28-ago estaban en esa
situacion desde que se grabaron y nadie lo habia intentado.

QUE HACE, Y QUE NO
------------------
Traduce la metadata y deja el bag adaptado en otra carpeta, con **enlaces
simbolicos** a los `.mcap` originales: la evidencia del carro no se toca ni se
duplica. No convierte el `.mcap`, porque no hace falta.

**Esto NO basta por si solo.** Humble ademas necesita el plugin de
almacenamiento, que no viene de serie:

    sudo apt install ros-humble-rosbag2-storage-mcap

Son dos bloqueos independientes y hay que quitar los dos. Este guion quita el
primero; el segundo pide una contrasena y no se puede automatizar aqui.

LIMITACION
----------
Un bag SIN `metadata.yaml` -- `bag_mapa_1456` es uno -- no se puede adaptar:
toda la informacion que falta esta dentro del `.mcap` y leerla exige el propio
lector que aun no hay. Se avisa y se sale, en vez de copiar la metadata de un
bag hermano, que seria fabricar evidencia.
"""

import argparse
import copy
import os
import sys

import yaml

# La metadata que escribe Humble 22.04. Se comprobo contra
# ~/tesis_evidencia/S21_dominio_unico_001/metadata.yaml, grabada por este PC.
VERSION_HUMBLE = 5

# rmw/types.h. Van explicitos y no derivados de un ejemplo porque un entero
# equivocado aqui no da error: da un bag que se abre y miente sobre su QoS.
ENUMS_QOS = {
    "history": {"system_default": 0, "keep_last": 1, "keep_all": 2,
                "unknown": 3},
    "reliability": {"system_default": 0, "reliable": 1, "best_effort": 2,
                    "unknown": 3},
    "durability": {"system_default": 0, "transient_local": 1, "volatile": 2,
                   "unknown": 3},
    "liveliness": {"system_default": 0, "automatic": 1, "manual_by_topic": 3,
                   "unknown": 4},
}

# Claves que Jazzy anade y Humble no conoce. Se quitan en vez de dejarlas: el
# parser de Humble las ignoraria, pero dejarlas haria creer que se leyeron.
SOBRAN_RAIZ = ("ros_distro", "custom_data")
SOBRAN_TOPICO = ("type_description_hash",)


class ErrorAdaptacion(Exception):
    """Algo impide adaptar el bag. Se aborta antes que producir metadata falsa."""


def qos_a_humble(perfiles):
    """La secuencia de QoS de Jazzy, como la cadena que Humble espera.

    Devuelve una CADENA, no una lista: en la version 5 el campo
    'offered_qos_profiles' es un string que contiene YAML, no YAML anidado.
    """
    if isinstance(perfiles, str):
        raise ErrorAdaptacion(
            "'offered_qos_profiles' ya es una cadena: esta metadata no viene "
            "de Jazzy, o ya se adapto. Convertirla otra vez envolveria la "
            "cadena dentro de otra cadena")
    if perfiles is None:
        return ""

    traducidos = []
    for perfil in perfiles:
        nuevo = {}
        for clave, valor in perfil.items():
            tabla = ENUMS_QOS.get(clave)
            if tabla is None:
                nuevo[clave] = valor
                continue
            if isinstance(valor, int):
                nuevo[clave] = valor
                continue
            if valor not in tabla:
                raise ErrorAdaptacion(
                    f"QoS '{clave}' vale {valor!r}, que no esta en la tabla de "
                    f"rmw/types.h ({sorted(tabla)}). No se inventa un entero: "
                    "seria falsear la metadata de una evidencia fisica")
            nuevo[clave] = tabla[valor]
        traducidos.append(nuevo)

    return yaml.safe_dump(traducidos, default_flow_style=False,
                          sort_keys=False).strip()


def adaptar(metadata):
    """Metadata version 9 (Jazzy) -> version 5 (Humble). No muta la entrada."""
    if "rosbag2_bagfile_information" not in metadata:
        raise ErrorAdaptacion(
            "el YAML no tiene 'rosbag2_bagfile_information': no es la metadata "
            "de un bag de rosbag2")

    salida = copy.deepcopy(metadata)
    b = salida["rosbag2_bagfile_information"]

    version = b.get("version")
    if not isinstance(version, int):
        raise ErrorAdaptacion(f"la metadata declara version {version!r}, que no "
                              "es un entero")
    if version <= VERSION_HUMBLE:
        raise ErrorAdaptacion(
            f"la metadata ya esta en version {version}, que Humble lee. No hay "
            "nada que adaptar, y convertirla igual romperia el QoS")

    b["version"] = VERSION_HUMBLE
    for clave in SOBRAN_RAIZ:
        b.pop(clave, None)

    for entrada in b.get("topics_with_message_count", []):
        tm = entrada.get("topic_metadata", {})
        for clave in SOBRAN_TOPICO:
            tm.pop(clave, None)
        tm["offered_qos_profiles"] = qos_a_humble(tm.get("offered_qos_profiles"))

    # Humble exige las dos, y Jazzy podria omitirlas si no hubo compresion.
    b.setdefault("compression_format", "")
    b.setdefault("compression_mode", "")
    return salida


def leer_metadata(ruta):
    with open(ruta) as f:
        return yaml.safe_load(f)


def adaptar_carpeta(origen, destino):
    """Escribe en 'destino' la metadata adaptada y enlaces a los .mcap.

    Devuelve la lista de ficheros enlazados. No escribe nada en 'origen'.
    """
    ruta_meta = os.path.join(origen, "metadata.yaml")
    if not os.path.exists(ruta_meta):
        sueltos = [f for f in sorted(os.listdir(origen)) if f.endswith(".mcap")]
        raise ErrorAdaptacion(
            f"{origen} no tiene metadata.yaml"
            + (f" (si tiene {', '.join(sueltos)})." if sueltos else ".")
            + " Todo lo que falta esta dentro del .mcap, y leerlo exige el "
              "lector que todavia no hay. No se copia la de un bag hermano: "
              "los recuentos y los instantes serian de otra corrida")

    salida = adaptar(leer_metadata(ruta_meta))
    b = salida["rosbag2_bagfile_information"]

    os.makedirs(destino, exist_ok=True)
    enlazados = []
    for rel in b.get("relative_file_paths", []):
        fuente = os.path.abspath(os.path.join(origen, rel))
        if not os.path.exists(fuente):
            raise ErrorAdaptacion(
                f"la metadata cita '{rel}' y ese fichero no esta en {origen}")
        enlace = os.path.join(destino, rel)
        if os.path.lexists(enlace):
            os.remove(enlace)
        os.symlink(fuente, enlace)
        enlazados.append(rel)

    with open(os.path.join(destino, "metadata.yaml"), "w") as f:
        yaml.safe_dump(salida, f, default_flow_style=False, sort_keys=False)
    return enlazados


def main():
    p = argparse.ArgumentParser(
        description="Adapta un bag grabado en Jazzy para leerlo en Humble.")
    p.add_argument("bag", help="carpeta del bag original (no se modifica)")
    p.add_argument("-o", "--destino",
                   help="carpeta de salida (por defecto: <bag>_humble)")
    args = p.parse_args()

    origen = os.path.abspath(args.bag.rstrip("/"))
    destino = os.path.abspath(args.destino or origen + "_humble")
    if destino == origen:
        print("ERROR: el destino no puede ser el propio bag. La evidencia del "
              "carro no se sobrescribe.", file=sys.stderr)
        return 2

    try:
        enlazados = adaptar_carpeta(origen, destino)
    except ErrorAdaptacion as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Adaptado en {destino}")
    print(f"  metadata.yaml reescrita a version {VERSION_HUMBLE}")
    for f in enlazados:
        print(f"  {f} -> enlace al original (no se copio)")
    print("\nFalta el plugin de almacenamiento si aun no esta:")
    print("  sudo apt install ros-humble-rosbag2-storage-mcap")
    print(f"Y despues:  ros2 bag info {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
