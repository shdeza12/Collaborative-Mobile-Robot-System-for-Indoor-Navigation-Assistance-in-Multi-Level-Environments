#!/usr/bin/env python3
"""Pruebas de adaptar_bag_jazzy.py. No necesitan ROS ni el plugin de mcap.

Lo que se comprueba es la TRADUCCION de la metadata, que es lo unico que este
guion hace. Que el bag resultante se pueda abrir depende ademas de que el PC
tenga 'ros-humble-rosbag2-storage-mcap', y eso no es cosa de estas pruebas.
"""

import os
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptar_bag_jazzy import (VERSION_HUMBLE, ErrorAdaptacion, adaptar,
                               leer_metadata, qos_a_humble)

OK = 0
FALLOS = 0


def comprueba(descripcion, condicion):
    global OK, FALLOS
    if condicion:
        OK += 1
        print(f"  ok   {descripcion}")
    else:
        FALLOS += 1
        print(f"  FALLA {descripcion}")


def levanta(descripcion, fn):
    global OK, FALLOS
    try:
        fn()
    except ErrorAdaptacion:
        OK += 1
        print(f"  ok   {descripcion}")
        return
    except Exception as e:
        FALLOS += 1
        print(f"  FALLA {descripcion} (levanto {type(e).__name__}, no ErrorAdaptacion)")
        return
    FALLOS += 1
    print(f"  FALLA {descripcion} (no levanto nada)")


QOS_JAZZY = [{
    "history": "unknown", "depth": 0,
    "reliability": "reliable", "durability": "volatile",
    "deadline": {"sec": 9223372036, "nsec": 854775807},
    "lifespan": {"sec": 9223372036, "nsec": 854775807},
    "liveliness": "automatic",
    "liveliness_lease_duration": {"sec": 9223372036, "nsec": 854775807},
    "avoid_ros_namespace_conventions": False,
}]


def metadata_jazzy():
    return {"rosbag2_bagfile_information": {
        "version": 9,
        "storage_identifier": "mcap",
        "duration": {"nanoseconds": 257643054054},
        "starting_time": {"nanoseconds_since_epoch": 1787928672517521231},
        "message_count": 1703,
        "topics_with_message_count": [{
            "topic_metadata": {
                "name": "/rplidar_ros/scan",
                "type": "sensor_msgs/msg/LaserScan",
                "serialization_format": "cdr",
                "offered_qos_profiles": QOS_JAZZY,
                "type_description_hash": "RIHS01_64c1913980",
            },
            "message_count": 1703,
        }],
        "compression_format": "", "compression_mode": "",
        "relative_file_paths": ["bag_mapa_1451_0.mcap"],
        "files": [{"path": "bag_mapa_1451_0.mcap",
                   "starting_time": {"nanoseconds_since_epoch": 1787928672517521231},
                   "duration": {"nanoseconds": 257643054054},
                   "message_count": 1703}],
        "custom_data": None,
        "ros_distro": "jazzy",
    }}


print("=" * 62)
print("1. Los enums de QoS se traducen de texto a entero")
# Los valores salen de rmw/types.h, no de mirar un ejemplo: Humble los escribe
# como el entero del enum y Jazzy como su nombre.
s = qos_a_humble(QOS_JAZZY)
comprueba("devuelve una cadena, que es lo que Humble espera ahi",
          isinstance(s, str))
perfil = yaml.safe_load(s)[0]
comprueba("history 'unknown' -> 3", perfil["history"] == 3)
comprueba("reliability 'reliable' -> 1", perfil["reliability"] == 1)
comprueba("durability 'volatile' -> 2", perfil["durability"] == 2)
comprueba("liveliness 'automatic' -> 1", perfil["liveliness"] == 1)
comprueba("lo que no es enum se copia tal cual",
          perfil["deadline"] == {"sec": 9223372036, "nsec": 854775807}
          and perfil["avoid_ros_namespace_conventions"] is False)

print("\n2. Un enum desconocido se rechaza, no se adivina")
# Inventar un numero aqui es fabricar metadata de una evidencia fisica.
levanta("un valor de reliability que no esta en la tabla levanta",
        lambda: qos_a_humble([dict(QOS_JAZZY[0], reliability="telepatica")]))

print("\n3. La conversion de la metadata completa")
salida = adaptar(metadata_jazzy())
b = salida["rosbag2_bagfile_information"]
comprueba(f"la version baja a {VERSION_HUMBLE}", b["version"] == VERSION_HUMBLE)
comprueba("desaparece 'ros_distro'", "ros_distro" not in b)
comprueba("desaparece 'custom_data'", "custom_data" not in b)
tm = b["topics_with_message_count"][0]["topic_metadata"]
comprueba("desaparece 'type_description_hash', que Humble no conoce",
          "type_description_hash" not in tm)
comprueba("'offered_qos_profiles' ya es cadena",
          isinstance(tm["offered_qos_profiles"], str))

print("\n4. Nada del contenido se pierde ni se altera")
comprueba("el nombre del topico se conserva", tm["name"] == "/rplidar_ros/scan")
comprueba("el tipo se conserva", tm["type"] == "sensor_msgs/msg/LaserScan")
comprueba("el recuento por topico se conserva",
          b["topics_with_message_count"][0]["message_count"] == 1703)
comprueba("el recuento total se conserva", b["message_count"] == 1703)
comprueba("la duracion se conserva al nanosegundo",
          b["duration"]["nanoseconds"] == 257643054054)
comprueba("el instante de inicio se conserva",
          b["starting_time"]["nanoseconds_since_epoch"] == 1787928672517521231)
comprueba("los ficheros referenciados se conservan",
          b["relative_file_paths"] == ["bag_mapa_1451_0.mcap"])

print("\n5. El original no se toca")
original = metadata_jazzy()
adaptar(original)
comprueba("adaptar() no muta su argumento",
          original["rosbag2_bagfile_information"]["version"] == 9)

print("\n6. Una metadata que ya es de Humble se rechaza")
# Convertir dos veces romperia el QoS: la cadena volveria a envolverse.
ya = metadata_jazzy()
ya["rosbag2_bagfile_information"]["version"] = 5
levanta("una metadata en version 5 no se vuelve a convertir",
        lambda: adaptar(ya))

print("\n7. Contra la metadata REAL del carro, si esta a mano")
real = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "mapas", "bag_mapa_1451", "metadata.yaml")
if os.path.exists(real):
    b2 = adaptar(leer_metadata(real))["rosbag2_bagfile_information"]
    comprueba("la del 28-ago convierte sin excepciones",
              b2["version"] == VERSION_HUMBLE)
    comprueba("conserva los 1703 barridos", b2["message_count"] == 1703)
    comprueba("el resultado se serializa a YAML valido",
              yaml.safe_load(yaml.safe_dump(b2)) == b2)
else:
    print("  (no esta mapas/bag_mapa_1451/metadata.yaml, se omite)")

print("\n" + "=" * 62)
if FALLOS:
    print(f"{FALLOS} comprobaciones FALLAN de {OK + FALLOS}")
    sys.exit(1)
print(f"{OK} comprobaciones pasan, 0 fallan.")
