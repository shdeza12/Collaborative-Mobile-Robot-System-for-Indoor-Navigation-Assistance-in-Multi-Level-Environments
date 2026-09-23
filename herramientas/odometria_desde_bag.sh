#!/bin/bash
# Saca la odometria de rf2o desde un bag que solo trae barridos, y nada mas.
#
# POR QUE EXISTE, HABIENDO YA 'mapear_desde_bag.sh'
# -------------------------------------------------
# Para el peldano 2 de la escalera Nav2 hay que responder una sola pregunta:
# **la odometria sola, sin mapa y sin localizacion, ¿mide el avance?**. Si se
# responde con 'mapear_desde_bag.sh', encima de rf2o corre slam_toolbox, y un
# resultado malo ya no dice cual de los dos fallo. Por eso aqui no hay SLAM: la
# salida es la trayectoria cruda de rf2o en un CSV.
#
# Tampoco sirven las otras dos herramientas cercanas:
#
#   - 'medir_registro_odometria.py' compara rf2o contra la verdad, pero exige
#     que el bag YA traiga '/odom'. Los bags del vehiculo no lo traen: el carro
#     solo graba barridos.
#   - 'medir_g2.py' mide G-2 completo, y para eso necesita '/amcl_pose', o sea
#     mapa y localizacion. Eso es el peldano 5, no el 2.
#
# USO
# ---
#     bash herramientas/odometria_desde_bag.sh <bag> <carpeta_salida> [topico]
#
# El topico por defecto es '/rplidar_ros/scan', que es el que publica el driver
# de fabrica del vehiculo -el de 'deepracer-core', 360 muestras y 12 m-. Si el
# bag se grabo con el driver del proyecto, pasa '/scan'.
#
# El bag tiene que ser una carpeta que Humble sepa abrir. Uno grabado en la
# tarjeta Jazzy del vehiculo hay que pasarlo antes por:
#
#     python3 herramientas/adaptar_bag_jazzy.py <bag> -o <bag>_humble
#
# LAS TRES TRAMPAS, HEREDADAS DE 'mapear_desde_bag.sh'
# ----------------------------------------------------
# Son las mismas y estan documentadas alla con detalle. En resumen:
#
#   1. '--clock' al reproducir y 'use_sim_time: true' en todos los nodos. Las
#      marcas del bag son del dia de la grabacion; contra el reloj de pared tf2
#      las da por pasado remoto y descarta cada barrido **en silencio**.
#   2. "init_pose_from_topic: ''" tiene que ir en un fichero YAML. En la linea
#      de ordenes el nodo no sabe parsear el valor vacio y aborta.
#   3. Hay que matar los nodos de corridas anteriores, o habra dos publicadores
#      de '/clock' y el tiempo saltara hacia atras sin parar.
#
# LA CUARTA TRAMPA, MEDIDA EL 2026-09-23 Y PROPIA DE ESTE PROYECTO
# ----------------------------------------------------------------
# Con los dos vehiculos encendidos en la misma red, el portatil los descubre y
# **todos** los nodos de Humble empiezan a soltar
#
#     sequence size exceeds remaining buffer
#
# sin recibir un solo mensaje. Es la incompatibilidad de serializacion entre
# Humble y Jazzy: la hipotesis que 'S24_tf_hardware_peldano_1.md' §6 dejo sin
# confirmar, y que aqui quedo confirmada.
#
# Se corta con 'ROS_LOCALHOST_ONLY=1'. **No con 'ROS_AUTOMATIC_DISCOVERY_RANGE'**,
# que es de Iron en adelante: en Humble esa variable no existe, no da error, y
# deja el problema intacto mientras aparenta haberlo resuelto.
#
# LA TF ESTATICA NO SE COPIA DEL XACRO
# ------------------------------------
# El URDF cuelga el sensor de 'chassis', no de 'base_link'. Copiar el 0.16145
# del xacro deja el laser 23 mm bajo. El valor de abajo es el compuesto, y el
# yaw de 180 grados -qz=1, qw=0- es el montaje invertido del soporte: omitirlo
# no da error, da una trayectoria girada media vuelta.
#
# QUE COMPROBAR ANTES, Y POR QUE NO ES OPCIONAL
# ----------------------------------------------
#     python3 herramientas/comprobar_movimiento_bag.py <bag>
#
# Tiene que decir que SIRVE. Dos cosas distintas se detectan ahi y las dos
# producen aqui una trayectoria con pinta de buena:
#
#   - un bag de sensor quieto, cuya trayectoria es deriva, no avance;
#   - un bag CONTAMINADO por el LiDAR del otro vehiculo, cuya trayectoria es el
#     salto entre dos sitios.
#
# Medido el 2026-09-23 sobre los dos bags de 'S24_verificacion_carros':
#
#   | bag            | estado       | dos corridas seguidas dan          |
#   |----------------|--------------|------------------------------------|
#   | bag_ez9n       | contaminado  | 1,04 / 1,83 / 3,14 m, sin relacion |
#   | sin_caparazon  | limpio       | 0,0042 m las dos, identico         |
#
# La leccion: con entrada sana esta cadena es DETERMINISTA, y dos corridas
# tienen que dar el mismo numero. Si no lo dan, el problema es el bag, no rf2o.
# Correrla dos veces es la comprobacion mas barata que hay.
BAG="$1"
SALIDA="$2"
TOPICO="${3:-/rplidar_ros/scan}"

if [ -z "$BAG" ] || [ -z "$SALIDA" ]; then
    echo "uso: bash herramientas/odometria_desde_bag.sh <bag> <salida> [topico]" >&2
    exit 2
fi
if [ ! -d "$BAG" ]; then
    echo "ERROR: '$BAG' no es una carpeta de bag." >&2
    exit 2
fi

source /opt/ros/humble/setup.bash
source ~/deepracer_sim_ws/install/setup.bash
export ROS_LOCALHOST_ONLY=1

mkdir -p "$SALIDA"

limpiar() {
    pkill -9 -f "ros2 bag play" 2>/dev/null || true
    pkill -9 -f rf2o_laser_odometry 2>/dev/null || true
    pkill -9 -f static_transform_publisher 2>/dev/null || true
    sleep 2
}
limpiar
trap limpiar EXIT

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

ros2 run tf2_ros static_transform_publisher \
    --x 0.02913 --y 0 --z 0.184699 --qx 0 --qy 0 --qz 1 --qw 0 \
    --frame-id base_link --child-frame-id laser \
    --ros-args -p use_sim_time:=true > "$SALIDA/tf.log" 2>&1 < /dev/null &

ros2 run rf2o_laser_odometry rf2o_laser_odometry_node \
    --ros-args --params-file "$SALIDA/rf2o.yaml" > "$SALIDA/rf2o.log" 2>&1 < /dev/null &

sleep 4

python3 - "$SALIDA/odom.csv" <<'PY' > "$SALIDA/captura.log" 2>&1 &
import sys, rclpy
from nav_msgs.msg import Odometry
rclpy.init()
n = rclpy.create_node('captura_odom')
n.set_parameters([rclpy.parameter.Parameter('use_sim_time', value=True)])
f = open(sys.argv[1], 'w')
f.write('t,x,y\n')
def cb(m):
    f.write('%.6f,%.6f,%.6f\n' % (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9,
                                  m.pose.pose.position.x, m.pose.pose.position.y))
    f.flush()
n.create_subscription(Odometry, '/odom', cb, 50)
rclpy.spin(n)
PY
PID_CAP=$!

sleep 3
ros2 bag play "$BAG" --clock --remap "$TOPICO":=/scan > "$SALIDA/play.log" 2>&1
sleep 4

kill $PID_CAP 2>/dev/null
sleep 1

if grep -q "jump back in time" "$SALIDA"/*.log 2>/dev/null; then
    echo "ABORTA: hubo un salto hacia atras en el tiempo. Quedaban nodos vivos." >&2
    echo "La corrida no vale. Vuelve a lanzarla." >&2
    exit 1
fi

python3 - "$SALIDA/odom.csv" <<'PY'
import math, sys
filas = [l.split(',') for l in open(sys.argv[1]).read().splitlines()[1:] if l]
if len(filas) < 2:
    print("SIN POSES. Mira rf2o.log y play.log.")
    print("Lo mas probable: el topico del bag no es el que se paso al remapeo.")
    raise SystemExit(1)
p = [(float(t), float(x), float(y)) for t, x, y in filas]
camino = sum(math.dist(p[i][1:], p[i-1][1:]) for i in range(1, len(p)))
neto = math.dist(p[-1][1:], p[0][1:])
print("poses            : %d" % len(p))
print("duracion         : %.2f s" % (p[-1][0] - p[0][0]))
print("pose inicial     : (%.4f, %.4f)" % p[0][1:])
print("pose final       : (%.4f, %.4f)" % p[-1][1:])
print("desplazamiento   : %.4f m   <- contra el flexometro, criterio G-2 <= 10 %%" % neto)
print("camino recorrido : %.4f m" % camino)
# El piso de 1 m evita el aviso en un bag de sensor quieto, donde el camino son
# unos milimetros de ruido y la razon no significa nada.
if camino > 1.0 and neto / camino < 0.5:
    print("AVISO: el camino casi duplica al desplazamiento. O hubo ida y vuelta,")
    print("       o rf2o esta serpenteando y el desplazamiento no es comparable.")
PY
