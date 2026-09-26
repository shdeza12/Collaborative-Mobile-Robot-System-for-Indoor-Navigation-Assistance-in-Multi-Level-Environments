#!/bin/bash
# Reproduce en RViz, en el portatil, el bag de una corrida del vehiculo real.
#
# USO
#     herramientas/ver_bag_rviz.sh <carpeta_del_bag> [marco_fijo] [velocidad]
#
#     carpeta_del_bag   la del bag, tal como se trajo del vehiculo
#     marco_fijo        por defecto 'map'. Si el bag no trae /tf -un bag de
#                       solo barridos-, pon el marco del sensor: 'laser'
#     velocidad         factor de reproduccion, por defecto 1.0
#
# POR QUE SE MIRA EL BAG Y NO EL VEHICULO EN VIVO
# -----------------------------------------------
# Porque en vivo NO funciona, y esta medido. El portatil corre Humble y el
# vehiculo Jazzy: se DESCUBREN -'ros2 topic list' en el portatil lista los
# topicos del carro- pero no intercambian datos. 'ros2 topic echo' no recibe un
# solo mensaje y el portatil imprime 'sequence size exceeds remaining buffer'.
# Comprobado el 2026-09-23 y el 2026-09-24. RViz del portatil apuntado al carro
# se queda en blanco sin dar un error que se entienda.
#
# La via para ver en vivo esta descrita, sin validar, en el par. 6 de
# Documentos/GUIA_CAMPANA_NAV2_HARDWARE.md.
#
# LO QUE HACE
#   1. Si el bag es de Jazzy (metadata version 9), lo adapta a Humble en /tmp
#      con adaptar_bag_jazzy.py, sin tocar el original.
#   2. Abre RViz con la vista de campana y con use_sim_time.
#   3. Reproduce el bag con --clock, para que RViz use el tiempo del bag.
#
# LA TRAMPA DE LOS DOS RELOJES
# ----------------------------
# Si queda un 'ros2 bag play' de antes, hay dos publicadores de /clock y el
# tiempo salta hacia atras sin parar: RViz vacia su buffer de TF una y otra vez
# y no dibuja nada. Por eso se mata cualquier reproduccion previa al empezar.

set -e

if [ $# -lt 1 ]; then
    sed -n '/^# USO/,/^# POR QUE/p' "$0" | sed '$d' | sed 's/^# \?//'
    exit 2
fi

BAG="$(cd "$1" && pwd)"
MARCO="${2:-map}"
RITMO="${3:-1.0}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VISTA="$REPO/Robot/aws-deepracer/deepracer_description/rviz/campana_nav2_hardware.rviz"

if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "ERROR: $BAG no tiene metadata.yaml." >&2
    echo "       Un bag sin ella no se puede reproducir: el grabador no se cerro" >&2
    echo "       limpiamente. Ver herramientas/lanzar_bag.inc." >&2
    exit 2
fi

set +u
source /opt/ros/humble/setup.bash
set -e

if grep -q '^ *version: 9' "$BAG/metadata.yaml"; then
    ADAPTADO="/tmp/$(basename "$BAG")_humble"
    rm -rf "$ADAPTADO"
    echo "== el bag es de Jazzy: adaptandolo a Humble en $ADAPTADO =="
    python3 "$REPO/herramientas/adaptar_bag_jazzy.py" "$BAG" -o "$ADAPTADO"
    BAG="$ADAPTADO"
fi

echo "== limpiando reproducciones anteriores =="
pkill -f "ros2 bag play" 2>/dev/null || true
sleep 1

echo "== abriendo RViz (marco fijo: $MARCO) =="
rviz2 -d "$VISTA" -f "$MARCO" --ros-args -p use_sim_time:=true \
    > /tmp/ver_bag_rviz.log 2>&1 &
sleep 5

echo "== reproduciendo a x$RITMO; cierra RViz cuando termines =="
ros2 bag play "$BAG" --clock 100 --rate "$RITMO"

echo
echo "Reproduccion terminada. RViz sigue abierto con el ultimo estado."
echo "Para volver a verlo: vuelve a lanzar esta orden."
