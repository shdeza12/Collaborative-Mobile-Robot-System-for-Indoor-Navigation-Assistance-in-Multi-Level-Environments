#!/bin/bash
# Construye un mapa de ocupacion a partir de un bag que solo trae barridos.
#
# POR QUE EXISTE
# --------------
# El DeepRacer no lleva encoders de rueda: su unica fuente de odometria es
# rf2o_laser_odometry, que la deduce de los propios barridos. En el vehiculo eso
# obliga a tener rf2o y slam_toolbox corriendo a la vez que se conduce, sobre
# Jazzy, donde no se ha comprobado que esten. Aqui no hace falta: el carro solo
# graba '/scan' y el mapa se levanta despues en el portatil, donde la cadena si
# esta comprobada -corrida entera el 2026-09-01-.
#
# La ventaja que decide es que se puede repetir. Si el mapa sale mal por un
# parametro, se cambia el parametro y se vuelve a correr sobre el mismo bag, sin
# volver al pasillo.
#
# LA CADENA
# ---------
#   ros2 bag play --clock  -->  /scan  y  /clock
#            rf2o          -->  /odom  y  TF odom -> base_link
#     static_transform     -->  TF base_link -> laser   (del URDF del vehiculo)
#         slam_toolbox     -->  /map  y  TF map -> odom
#        map_saver_cli     -->  mapa.pgm + mapa.yaml
#
# POR QUE '--clock' Y 'use_sim_time'
# ----------------------------------
# Las marcas de tiempo del bag son del dia de la grabacion. Contra el reloj de
# pared de hoy, tf2 las considera del pasado remoto y descarta cada barrido sin
# construir nada. Con '--clock' el reproductor publica el tiempo del bag en
# '/clock' y todos los nodos arrancan con use_sim_time:=true para hacerle caso.
#
# LA TRAMPA QUE COSTO UNA CORRIDA EL 2026-09-01
# ---------------------------------------------
# Si queda un 'ros2 bag play' de una corrida anterior, hay DOS publicadores de
# '/clock' y el tiempo salta hacia atras sin parar:
#
#     [WARN] [tf2_buffer]: Detected jump back in time. Clearing TF buffer.
#
# El mapa sale vacio o roto y nada dice por que. Por eso el guion mata los nodos
# antes de arrancar y al terminar. Si ves ese aviso, aborta: la corrida ya no
# vale.
#
# EL BAG TIENE QUE SER UNA CARPETA QUE HUMBLE SEPA ABRIR
# ------------------------------------------------------
# Apuntar al '.mcap' suelto SI funciona para leer con la API de rosbag2_py -asi
# se recuperaron los 2649 barridos de bag_mapa_1456 el 2026-09-01- pero NO para
# reproducir. 'ros2 bag play fichero.mcap --storage mcap' muere con:
#
#     yaml-cpp: error at line 1, column 12: bad conversion
#
# El reproductor de Humble se fabrica una metadata interna y no sabe releerla.
# Comprobado el 2026-09-01 sobre 1447 y 1456, con el plugin de mcap ya
# instalado. Un bag grabado en Jazzy hay que adaptarlo antes:
#
#     python3 herramientas/adaptar_bag_jazzy.py <bag> -o /tmp/<nombre>
#
# USO
#     herramientas/mapear_desde_bag.sh <bag> <carpeta_de_salida> [topico_scan]
#
#     <bag>              CARPETA del bag, legible por Humble (ver arriba)
#     carpeta_de_salida  se crea; ahi quedan mapa.pgm, mapa.yaml y los cuatro logs
#     topico_scan        por defecto '/scan'. Pon '/rplidar_ros/scan' si el bag
#                        se grabo con el LiDAR bajo el espacio de nombres de AWS
#
# Tarda lo que dure el bag: se reproduce a velocidad real a proposito, porque
# acelerarlo hace que slam_toolbox descarte barridos y el mapa cambie.

set -e

if [ $# -lt 2 ]; then
    sed -n '/^# USO/,/^$/p' "$0" | sed 's/^# \?//'
    exit 2
fi

BAG="$1"
SALIDA="$2"
TOPICO="${3:-/scan}"
CONFIG="$(cd "$(dirname "$0")/.." && pwd)/Robot/aws-deepracer/deepracer_bringup/config/slam_toolbox.yaml"

if [ ! -e "$BAG" ]; then
    echo "ERROR: no existe '$BAG'" >&2
    exit 2
fi
case "$BAG" in *.mcap)
    echo "ERROR: '$BAG' es un .mcap suelto y 'ros2 bag play' no sabe" >&2
    echo "       reproducirlo (muere con 'yaml-cpp: bad conversion')." >&2
    echo "       Pasa la CARPETA del bag. Si viene de Jazzy, adaptala antes:" >&2
    echo "         python3 herramientas/adaptar_bag_jazzy.py <bag> -o /tmp/mapeo" >&2
    exit 2
    ;;
esac
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "ERROR: '$BAG' no tiene metadata.yaml, y sin ella no se puede" >&2
    echo "       reproducir. Es lo que le pasa a bag_mapa_1456: la grabacion" >&2
    echo "       se corto de golpe y el indice nunca se escribio." >&2
    exit 2
fi
if [ ! -f "$CONFIG" ]; then
    echo "ERROR: no encuentro $CONFIG" >&2
    exit 2
fi

mkdir -p "$SALIDA"
SALIDA="$(cd "$SALIDA" && pwd)"

set +u
source /opt/ros/humble/setup.bash
[ -f "$HOME/deepracer_sim_ws/install/setup.bash" ] && source "$HOME/deepracer_sim_ws/install/setup.bash"
set -e

# Parametros de rf2o: los mismos que deepracer.launch.py usa en el vehiculo.
# 'init_pose_from_topic' vacio va en fichero y no en la linea de ordenes porque
# '-p init_pose_from_topic:=' no lo sabe parsear y el nodo aborta.
cat > "$SALIDA/rf2o.yaml" <<'YAML'
/**:
  ros__parameters:
    laser_scan_topic: /scan
    odom_topic: /odom
    publish_tf: true
    base_frame_id: base_link
    odom_frame_id: odom
    init_pose_from_topic: ''
    freq: 20.0
    use_sim_time: true
YAML

limpiar() {
    pkill -9 -f "ros2 bag play" 2>/dev/null || true
    pkill -9 -f rf2o_laser_odometry 2>/dev/null || true
    pkill -9 -f sync_slam_toolbox_node 2>/dev/null || true
    pkill -9 -f static_transform_publisher 2>/dev/null || true
    sleep 2
}

echo "== Limpiando nodos de corridas anteriores =="
limpiar
trap limpiar EXIT

# base_link -> laser, con los numeros del VEHICULO REAL, no los del URDF a pelo.
#
# El URDF pone el sensor colgando de 'chassis', no de 'base_link':
#   base_link -> chassis  z = 0,023249
#   chassis   -> laser    xyz = 0,02913  0  0,16145   rpy = 0 0 3,1416
# (deepracer_stereo_cameras_and_lidar_urdf.xacro, junta 'hokuyo_joint')
#
# Compuesto da x = 0,02913, z = 0,184699, yaw = pi, que es exactamente la TF
# estatica que deepracer.launch.py publica en el carro y la que documenta
# DESARROLLO_NAV2.md. Copiar el 0,16145 del xacro sin componer el chassis deja
# el sensor 23 mm bajo, y olvidar el yaw = pi construye el mapa girado 180
# grados respecto al que AMCL vera despues: el emparejamiento no cerraria y
# nada diria por que.
#
# yaw = pi en cuaternio es (x,y,z,w) = (0, 0, 1, 0).
echo "== Arrancando rf2o, slam_toolbox y la TF del sensor =="
ros2 run tf2_ros static_transform_publisher \
    --x 0.02913 --y 0 --z 0.184699 --qx 0 --qy 0 --qz 1 --qw 0 \
    --frame-id base_link --child-frame-id laser \
    --ros-args -p use_sim_time:=true > "$SALIDA/tf.log" 2>&1 < /dev/null &

ros2 run rf2o_laser_odometry rf2o_laser_odometry_node \
    --ros-args --params-file "$SALIDA/rf2o.yaml" \
    > "$SALIDA/rf2o.log" 2>&1 < /dev/null &

ros2 run slam_toolbox sync_slam_toolbox_node \
    --ros-args --params-file "$CONFIG" -p use_sim_time:=true \
    > "$SALIDA/slam.log" 2>&1 < /dev/null &

# Sin 'disown', al matarlos al final bash imprime tres 'Killed' que parecen un
# fallo y no lo son.
disown -a

sleep 6

REMAPEO=()
[ "$TOPICO" != "/scan" ] && REMAPEO=(--remap "$TOPICO:=/scan")

echo "== Reproduciendo $BAG (velocidad real; espera a que termine) =="
if ! ros2 bag play "$BAG" --clock 100 --rate 1 "${REMAPEO[@]}" \
        > "$SALIDA/play.log" 2>&1 < /dev/null; then
    echo "ERROR: la reproduccion fallo. Ultimas lineas de play.log:" >&2
    tail -5 "$SALIDA/play.log" >&2
    exit 1
fi

echo "== Dejando cerrar el ultimo barrido =="
sleep 10

echo "== Guardando el mapa =="
ros2 run nav2_map_server map_saver_cli -f "$SALIDA/mapa" \
    --ros-args -p use_sim_time:=true > "$SALIDA/saver.log" 2>&1
sleep 2

if grep -q "jump back in time" "$SALIDA/slam.log" 2>/dev/null; then
    echo
    echo "AVISO GRAVE: hubo saltos de tiempo hacia atras. Habia otro publicador"
    echo "de /clock corriendo. ESTE MAPA NO VALE: mata todo y repite."
fi

if [ -f "$SALIDA/mapa.pgm" ]; then
    echo
    echo "Mapa en $SALIDA/mapa.pgm"
    echo "Miralo antes de creertelo:  eog $SALIDA/mapa.pgm"
else
    echo
    echo "ERROR: no se escribio el mapa. Mira $SALIDA/saver.log y $SALIDA/slam.log" >&2
    exit 1
fi
