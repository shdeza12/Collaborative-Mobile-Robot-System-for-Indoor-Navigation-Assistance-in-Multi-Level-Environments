#!/bin/bash
# Mapea conduciendo: el vehiculo avanza una distancia y construye el mapa a la vez.
#
# USO (en el VEHICULO, y como root — ver abajo por que)
#     mapear_conduciendo.sh <metros> [m/s] [tope_segundos]
#
#     metros          distancia objetivo, medida contra la odometria de rf2o
#     m/s             velocidad mandada. Por defecto 0,5. POR DEBAJO DE 0,40 NO
#                     SE MUEVE: 'cmdvel_to_servo_node' convierte con |v|/4,0 y
#                     descarta lo que quede por debajo de 0,1, asi que 0,26 m/s
#                     -lo que pide Nav2- sale como throttle CERO sin dar error
#     tope_segundos   corte duro. A la velocidad real medida el 2026-09-24
#                     (0,15 a 0,26 m/s) seis metros tardan entre 25 y 45 s
#
# ANTES DE CORRER ESTO hay que haber copiado al vehiculo, EN EL MISMO
# DIRECTORIO que este guion, otros tres ficheros:
#     avanzar_y_detener.py   lanzar_bag.inc   slam_toolbox_carro.yaml
# Y ese directorio NO puede ser /tmp, que se vacia al reiniciar —el vehiculo
# reinicio solo en mitad de la sesion del 2026-09-24 y se llevo los guiones—.
# El guion de campo detalla la copia.
#
# POR QUE A BORDO Y NO SOBRE UN BAG
# ---------------------------------
# La via offline -grabar y levantar el mapa en el portatil con
# 'mapear_desde_bag.sh'- esta probada y es la que hay que preferir cuando el
# mapa se necesita en el escritorio. Aqui no sirve: el mapa hace falta EN EL
# VEHICULO para que Nav2 lo use acto seguido, y el portatil no puede
# mandarselo. Humble y Jazzy se descubren pero no intercambian datos: el
# 2026-09-24 el portatil listaba los topicos del carro y 'ros2 topic echo' no
# recibia un solo mensaje.
#
# Se graba el bag igualmente, con '/map' incluido, para poder rehacer el mapa
# despues sin volver al sitio.
#
# TODO CORRE COMO ROOT, Y NO ES OPCIONAL
# --------------------------------------
# 'deepracer-core.service' declara User=root, asi que 'rplidar_node' publica
# como root y 'servo_pkg' escucha como root. Los segmentos de memoria
# compartida de Fast DDS son de root con permisos 0644: un proceso que corra
# como 'deepracer' DESCUBRE pero no recibe, y no da ningun error —se queda
# esperando—. Medido el 2026-09-22 y confirmado el 2026-09-24.
#
# LA CADENA
#   rplidar_node (deepracer-core)  --> /rplidar_ros/scan
#   static_transform_publisher     --> TF base_link -> laser
#   rf2o_laser_odometry            --> /odom y TF odom -> base_link
#   sync_slam_toolbox_node         --> /map y TF map -> odom
#   cmdvel_to_servo_node           --> /cmd_vel a /ctrl_pkg/servo_msg
#   avanzar_y_detener.py           --> conduce y mide
#   extraer_mapa.py                --> mapa.pgm + mapa.yaml, desde el bag

# Sin 'set -u': los setup.bash de ROS leen variables no definidas y abortarian.
AQUI="$(cd "$(dirname "$0")" && pwd)"

source /opt/ros/jazzy/setup.bash
source /opt/aws/deepracer/lib/setup.bash
source ~deepracer/coordinacion_ws/install/setup.bash
source ~deepracer/nav_ws/install/setup.bash
source "$AQUI/lanzar_bag.inc"

METROS="${1:-6.0}"
VELOCIDAD="${2:-0.5}"
TOPE="${3:-90}"
SALIDA=~deepracer/mapeo_$(date +%H%M%S)

mkdir -p "$SALIDA"

limpiar() {
    pkill -9 -f rf2o_laser_odometry 2>/dev/null
    pkill -9 -f static_transform_publisher 2>/dev/null
    pkill -9 -f sync_slam_toolbox_node 2>/dev/null
    sleep 1
}
trap limpiar EXIT

echo "== limpiando restos =="
limpiar

# Sin barridos no hay odometria, ni mapa, ni parada por laser: mas vale no
# arrancar. Lo publica 'deepracer-core', pero una corrida anterior pudo
# dejarlo tocado.
echo "== comprobando el LiDAR =="
if ! timeout 15 ros2 topic echo /rplidar_ros/scan --field header.frame_id \
        --qos-reliability best_effort --once > /tmp/frame.txt 2>&1; then
    echo "ABORTA: /rplidar_ros/scan no publica. Revisa deepracer-core."
    cat /tmp/frame.txt
    exit 5
fi
echo "   frame del barrido: $(head -1 /tmp/frame.txt)"

cat > /tmp/rf2o.yaml <<'YAML'
/**:
  ros__parameters:
    laser_scan_topic: /rplidar_ros/scan
    odom_topic: /odom
    publish_tf: true
    base_frame_id: base_link
    odom_frame_id: odom
    init_pose_from_topic: ''
    freq: 20.0
    use_sim_time: false
YAML

# base_link -> laser compuesto del vehiculo real: el URDF cuelga el sensor de
# 'chassis', no de 'base_link', y hay que componer los dos saltos.
#   base_link -> chassis  z = 0,023249
#   chassis   -> laser    xyz = 0,02913  0  0,16145   rpy = 0 0 3,1416
# Compuesto da x = 0,02913, z = 0,184699, yaw = pi. yaw = pi en cuaternio es
# (x,y,z,w) = (0,0,1,0). Copiar el 0,16145 del xacro sin componer el chassis
# deja el sensor 23 mm bajo, y olvidar el yaw construye el mapa 180 grados
# girado respecto al que AMCL vera despues: el emparejamiento no cerraria y
# nada diria por que.
echo "== TF del sensor, rf2o y slam_toolbox =="
nohup ros2 run tf2_ros static_transform_publisher \
    --x 0.02913 --y 0 --z 0.184699 --qx 0 --qy 0 --qz 1 --qw 0 \
    --frame-id base_link --child-frame-id laser > "$SALIDA/tf.log" 2>&1 &
nohup ros2 run rf2o_laser_odometry rf2o_laser_odometry_node \
    --ros-args --params-file /tmp/rf2o.yaml > "$SALIDA/rf2o.log" 2>&1 &
sleep 5
nohup ros2 run slam_toolbox sync_slam_toolbox_node \
    --ros-args --params-file "$AQUI/slam_toolbox_carro.yaml" > "$SALIDA/slam.log" 2>&1 &
sleep 8

# EN JAZZY slam_toolbox ES UN NODO DE CICLO DE VIDA y nace 'unconfigured': no
# publica /map, no construye nada, y su log se queda en una sola linea. No da
# ningun error. En Humble no lo es, y por eso 'mapear_desde_bag.sh' funciona en
# el portatil sin hacer nada de esto. Ya estaba anotado en GUION_NAV2_HARDWARE
# §3; costo una corrida entera de mapeo el 2026-09-24 por no haberlo leido.
echo "== activando slam_toolbox (ciclo de vida) =="
ros2 lifecycle set /slam_toolbox configure > /dev/null 2>&1
sleep 3
ros2 lifecycle set /slam_toolbox activate > /dev/null 2>&1
sleep 3
ESTADO_SLAM="$(ros2 lifecycle get /slam_toolbox 2>&1 | head -1)"
echo "   estado: $ESTADO_SLAM"
case "$ESTADO_SLAM" in
    active*) ;;
    *) echo "ABORTA: slam_toolbox no quedo activo, no habria mapa que guardar."
       echo "        El vehiculo no se ha movido."
       exit 4 ;;
esac

# Este nodo no lo arranca nadie: no es parte de deepracer-core. Y si el
# vehiculo reinicia, desaparece. Sin el no hay '/cmd_vel' que valga.
if ! ps -eo args | grep -q '[c]mdvel_to_servo_pkg/cmdvel_to_servo_node'; then
    echo "== arrancando cmdvel_to_servo_node =="
    nohup ros2 run cmdvel_to_servo_pkg cmdvel_to_servo_node \
        > /tmp/cmdvel.log 2>&1 &
    sleep 6
fi

echo "== grabando bag =="
arrancar_bag "$SALIDA/bag" /rplidar_ros/scan /odom /map

echo "== conduciendo $METROS m =="
python3 "$AQUI/avanzar_y_detener.py" "$METROS" "$VELOCIDAD" "$TOPE"
ESTADO=$?

echo "== dejando cerrar el ultimo barrido =="
sleep 8

cerrar_bag

# NO se usa 'map_saver_cli'. Se rinde a los 2 s -su plazo por defecto- y
# slam_toolbox deja de publicar /map en cuanto el vehiculo se detiene, asi que
# el guardado falla con 'Failed to spin map subscription' aunque el mapa este
# perfectamente construido. Paso el 2026-09-24 con una corrida de 6 m ya hecha.
# El mapa se saca del bag, que ademas lo hace repetible sin volver al sitio.
echo "== extrayendo el mapa del bag =="
python3 "$AQUI/extraer_mapa.py" "$SALIDA/bag" "$SALIDA/mapa"

chown -R deepracer:deepracer "$SALIDA" 2>/dev/null

echo "== resultado en $SALIDA =="
ls -la "$SALIDA"

exit $ESTADO
