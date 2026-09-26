#!/bin/bash
# Una corrida de campana en el VEHICULO: graba el bag y corre corrida_nav2.py.
#
# USO (en el vehiculo, como root, con el launch ya activo)
#     correr_corrida_nav2.sh <id> <argumentos de corrida_nav2.py>
#
# Ejemplo, la segunda corrida de la campana 'c1':
#     correr_corrida_nav2.sh c1_02 --salida 0.60 0.0 0.0 --avance 5.0 \
#         --mapa ~deepracer/tesis/mapa.yaml --csv ~deepracer/campana_c1.csv
#
# Todo lo que no es el <id> pasa tal cual a corrida_nav2.py. El bag queda en
# ~deepracer/campana_<id>/ y la fila en el --csv que se indique.
#
# POR QUE UN BAG POR CORRIDA Y NO UNO POR CAMPANA
# -----------------------------------------------
# Entre corrida y corrida el vehiculo se devuelve a mano a la marca de salida.
# En un bag unico ese traslado aparece como un desplazamiento que nadie mando,
# y cualquier analisis posterior tendria que adivinar donde empieza cada
# corrida. Uno por corrida hace el corte obvio y deja que una corrida mala se
# descarte sin tocar las demas.
#
# POR QUE ROOT
# ------------
# 'deepracer-core' corre como root, y ni el grabador ni la herramienta reciben
# nada si corren como 'deepracer': Fast DDS no empareja por memoria compartida
# entre usuarios distintos, y no avisa.

AQUI="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 2 ]; then
    sed -n '/^# USO/,/^# Todo lo/p' "$0" | sed 's/^# \?//'
    exit 2
fi

ID="$1"; shift

source /opt/ros/jazzy/setup.bash
source "$AQUI/lanzar_bag.inc"

DESTINO=~deepracer/campana_$ID
if [ -e "$DESTINO" ]; then
    echo "ABORTA: ya existe $DESTINO. Cada corrida lleva un id distinto."
    exit 2
fi

echo "== grabando $DESTINO =="
# /map se graba para poder dibujar la corrida sobre el mapa sin el vehiculo.
# /plan y /amcl_pose son los que distinguen una navegacion de un empujon.
arrancar_bag "$DESTINO" /rplidar_ros/scan /odom /tf /tf_static /cmd_vel \
    /plan /amcl_pose /initialpose /map

python3 "$AQUI/corrida_nav2.py" --corrida "$ID" "$@"
ESTADO=$?

cerrar_bag
exit $ESTADO
