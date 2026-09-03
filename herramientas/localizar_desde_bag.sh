#!/bin/bash
# Localiza con AMCL, fuera de linea, sobre un bag que solo trae barridos, y
# vuelca la trayectoria a un CSV del que medir_g2.py saca M1 y M2.
#
# POR QUE EXISTE
# --------------
# Es la segunda mitad del G2. La primera -mapear_desde_bag.sh- construye el
# mapa; esta se localiza contra el. Son la misma cadena con distinto final:
#
#   mapeo         bag /scan -> rf2o -> slam_toolbox        -> mapa.pgm
#   localizacion  bag /scan -> rf2o -> map_server + AMCL   -> trayectoria.csv
#
# El carro graba solo '/scan' -no publica '/odom', '/tf' ni '/tf_static',
# comprobado el 2026-09-01 contra la lista estable de 22 topicos- asi que todo
# lo demas se fabrica aqui. La ventaja que decide es la misma que en el mapeo:
# se puede repetir sobre el mismo bag sin volver al pasillo, y AMCL es
# estocastico, asi que repetir no es un lujo (Paso 5.3 de la guia).
#
# LO QUE ESTO CONCEDE, Y HAY QUE DECLARARLO
# -----------------------------------------
# AMCL sobre un bag reproducido no es identico a AMCL en vivo. El portatil es
# mas rapido que la tarjeta del carro, asi que aqui nunca se queda sin ciclos:
# la cifra que sale es una COTA OPTIMISTA del rendimiento en tiempo real. Y rf2o
# deduce '/odom' de los mismos barridos con los que AMCL se localiza, de modo que
# odometria y observacion comparten sensor. Eso ultimo no lo introduce el ir
# fuera de linea: el DeepRacer no lleva encoders, asi que en el carro pasa igual.
#
# UPDATE_MIN_D BAJA DE 0,25 A 0,05, Y SE DECLARA
# ----------------------------------------------
# Por defecto AMCL solo actualiza cuando el robot se ha movido 0,25 m, asi que la
# ultima pose publicada podria ser de hasta 25 cm antes de la marca de llegada:
# la mitad del umbral de M2, metida por un parametro y no por el algoritmo. Se
# baja a 0,05 m. Favorece ligeramente a AMCL al reducir el error de
# discretizacion del punto final, y no fabrica informacion: en un pasillo
# longitudinalmente inobservable, actualizar mas veces no da de donde triangular.
#
# EL RESTO DE PARAMETROS SALEN DEL REPOSITORIO, NO DE AQUI
# --------------------------------------------------------
# Se leen de config/nav2_params_nav_amcl_sim_demo.yaml para que esta corrida use
# los mismos que la campana en simulacion. En particular los alpha, que estan en
# 0,01 y NO se tocan. Copiarlos aqui a mano los dejaria divergir en silencio.
#
# LA POSE INICIAL SALE GRATIS SI EL MAPEO ARRANCO BIEN
# ----------------------------------------------------
# slam_toolbox pone el (0,0,0) del mapa donde estaba 'base_link' al arrancar el
# SLAM. Si la pasada de mapeo arranco sobre la marca de 0 m mirando al fondo
# -Paso 3.1 de GUIA_PASADA_MAPEO.md-, entonces (0,0,0) ES esa marca y la ida no
# necesita '--pose-inicial'. La vuelta si: arranca en el otro extremo.
#
#     ida     (no hace falta)          -> 0, 0, 0
#     vuelta  --pose-inicial L,0,3.1416
#
# USO
#     herramientas/localizar_desde_bag.sh <bag> <mapa.yaml> <salida>
#                                         [--pose-inicial X,Y,YAW] [--topico T]
#
#     <bag>        CARPETA del bag, legible por Humble. Si viene de Jazzy,
#                  adaptala antes con adaptar_bag_jazzy.py
#     <mapa.yaml>  el mapa de la primera pasada
#     <salida>     se crea; ahi quedan trayectoria.csv y los logs
#     --topico     por defecto '/scan'. Pon '/rplidar_ros/scan' si el bag se
#                  grabo con el LiDAR bajo el espacio de nombres de AWS, que es
#                  lo que le pasa a los cinco bags del 28-ago
#
# Tarda lo que dure el bag: se reproduce a velocidad real a proposito, porque
# acelerarlo cambia cuantas actualizaciones hace AMCL y con ellas el resultado.

set -e

if [ $# -lt 3 ]; then
    sed -n '/^# USO/,/^$/p' "$0" | sed 's/^# \?//'
    exit 2
fi

BAG="$1"
MAPA="$2"
SALIDA="$3"
shift 3

POSE_X=0.0; POSE_Y=0.0; POSE_YAW=0.0; TOPICO="/scan"
while [ $# -gt 0 ]; do
    case "$1" in
        --pose-inicial)
            IFS=',' read -r POSE_X POSE_Y POSE_YAW <<< "$2"
            if [ -z "$POSE_YAW" ]; then
                echo "ERROR: --pose-inicial quiere X,Y,YAW (sin espacios)" >&2
                exit 2
            fi
            shift 2 ;;
        --topico) TOPICO="$2"; shift 2 ;;
        *) echo "ERROR: opcion desconocida '$1'" >&2; exit 2 ;;
    esac
done

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$RAIZ/Robot/aws-deepracer/deepracer_bringup/config/nav2_params_nav_amcl_sim_demo.yaml"

if [ ! -e "$BAG" ]; then
    echo "ERROR: no existe '$BAG'" >&2
    exit 2
fi
case "$BAG" in *.mcap)
    echo "ERROR: '$BAG' es un .mcap suelto y 'ros2 bag play' no sabe" >&2
    echo "       reproducirlo (muere con 'yaml-cpp: bad conversion')." >&2
    echo "       Pasa la CARPETA del bag. Si viene de Jazzy, adaptala antes:" >&2
    echo "         python3 herramientas/adaptar_bag_jazzy.py <bag> -o /tmp/g2" >&2
    exit 2
    ;;
esac
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "ERROR: '$BAG' no tiene metadata.yaml, y sin ella no se puede" >&2
    echo "       reproducir. Le pasa a los bags cuya grabacion se corto de" >&2
    echo "       golpe: el indice se escribe al cerrar limpio (Paso 3.4)." >&2
    exit 2
fi
if [ ! -f "$MAPA" ]; then
    echo "ERROR: no encuentro el mapa '$MAPA'. Es el que produce la primera" >&2
    echo "       pasada; sin el, AMCL no tiene contra que localizarse." >&2
    exit 2
fi
if [ ! -f "$CONFIG" ]; then
    echo "ERROR: no encuentro $CONFIG" >&2
    exit 2
fi

mkdir -p "$SALIDA"
SALIDA="$(cd "$SALIDA" && pwd)"
MAPA="$(cd "$(dirname "$MAPA")" && pwd)/$(basename "$MAPA")"

set +u
source /opt/ros/humble/setup.bash
[ -f "$HOME/deepracer_sim_ws/install/setup.bash" ] && source "$HOME/deepracer_sim_ws/install/setup.bash"
set -e

# Parametros de rf2o: los mismos que usa mapear_desde_bag.sh, para que M1 mida
# la misma odometria con la que se construyo el mapa.
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

# AMCL: se parte del fichero del repositorio y solo se cambia lo que esta
# justificado arriba. Asi los alpha y el modelo de sensor no pueden divergir.
python3 - "$CONFIG" "$SALIDA/amcl.yaml" "$MAPA" "$POSE_X" "$POSE_Y" "$POSE_YAW" <<'PY'
import sys, yaml
origen, destino, mapa, px, py, pyaw = sys.argv[1:7]
d = yaml.safe_load(open(origen))
a = d["amcl"]["ros__parameters"]
a["use_sim_time"] = True
a["set_initial_pose"] = True
a["initial_pose"] = {"x": float(px), "y": float(py), "z": 0.0,
                     "yaw": float(pyaw)}
# Ver la cabecera del guion: 0,25 m dejaria la ultima pose hasta 25 cm antes de
# la marca, la mitad del umbral de M2.
a["update_min_d"] = 0.05
a["update_min_a"] = 0.05
salida = {
    "amcl": {"ros__parameters": a},
    "map_server": {"ros__parameters": {"use_sim_time": True,
                                       "yaml_filename": mapa}},
}
yaml.safe_dump(salida, open(destino, "w"), default_flow_style=False)
print(f"  AMCL: modelo {a['robot_model_type']}, alpha1 {a['alpha1']}, "
      f"update_min_d {a['update_min_d']}, pose inicial "
      f"({px}, {py}, {pyaw})")
PY

# Volcador de la trayectoria. Se escribe aqui, junto a los logs, por la misma
# razon que rf2o.yaml: queda con la corrida que lo produjo.
cat > "$SALIDA/volcar.py" <<'PY'
"""Suscribe /odom y /amcl_pose y los vuelca a trayectoria.csv.

El tiempo se normaliza al primer mensaje recibido: las marcas del bag son
epoch del dia de la grabacion y en el informe se leen mucho mejor relativas.
medir_g2.py solo mira diferencias, asi que el origen le da igual.
"""
import math, sys
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.parameter import Parameter
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped


def yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class Volcador(Node):
    def __init__(self, ruta):
        # use_sim_time NO se declara: rclpy ya lo declara solo en Node.__init__,
        # y volver a declararlo aborta el nodo con ParameterAlreadyDeclared.
        # Se fija por parameter_overrides, que es la via que si admite. Pasa
        # que su valor por defecto es False, asi que omitirlo tampoco vale:
        # dejaria a este nodo en reloj de pared mientras el resto de la cadena
        # va en tiempo simulado.
        super().__init__(
            "volcar_trayectoria",
            parameter_overrides=[Parameter("use_sim_time",
                                           Parameter.Type.BOOL, True)])
        self.f = open(ruta, "w", buffering=1)
        self.f.write("t,fuente,x,y,yaw\n")
        self.t0 = None
        self.n = {"odom": 0, "amcl": 0}
        self.create_subscription(Odometry, "/odom", self.odom, 50)
        self.create_subscription(PoseWithCovarianceStamped, "/amcl_pose",
                                 self.amcl, 50)

    def escribir(self, stamp, fuente, pose):
        t = stamp.sec + stamp.nanosec * 1e-9
        if self.t0 is None:
            self.t0 = t
        p, o = pose.position, pose.orientation
        self.f.write(f"{t - self.t0:.4f},{fuente},{p.x:.5f},{p.y:.5f},"
                     f"{yaw_de(o):.5f}\n")
        self.n[fuente] += 1

    def odom(self, m):
        self.escribir(m.header.stamp, "odom", m.pose.pose)

    def amcl(self, m):
        self.escribir(m.header.stamp, "amcl", m.pose.pose)


def main():
    rclpy.init()
    n = Volcador(sys.argv[1])
    try:
        rclpy.spin(n)
    # El script lo para con 'kill -INT', y ante esa senal rclpy no lanza
    # KeyboardInterrupt sino ExternalShutdownException. Sin cazarla el volcado
    # sale bien igual -el fichero va sin buffer y finally lo cierra- pero deja
    # un traceback en volcar.log, y entonces un log sano parece una averia.
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        n.f.close()
        print(f"odom={n.n['odom']} amcl={n.n['amcl']}", flush=True)


main()
PY

limpiar() {
    pkill -9 -f "ros2 bag play" 2>/dev/null || true
    pkill -9 -f rf2o_laser_odometry 2>/dev/null || true
    pkill -9 -f "amcl --ros-args" 2>/dev/null || true
    pkill -9 -f "map_server --ros-args" 2>/dev/null || true
    pkill -9 -f lifecycle_manager 2>/dev/null || true
    pkill -9 -f static_transform_publisher 2>/dev/null || true
    pkill -9 -f "volcar.py" 2>/dev/null || true
    sleep 2
}

echo "== Limpiando nodos de corridas anteriores =="
limpiar
trap limpiar EXIT

# base_link -> laser, con los numeros del VEHICULO REAL. Identica a la del
# mapeo, y tiene que serlo: si esta cadena compone el sensor distinto que
# aquella, AMCL se localiza contra un mapa que no encaja y nada dice por que.
# El yaw = pi no es opcional; en cuaternio es (x,y,z,w) = (0, 0, 1, 0).
echo "== Arrancando la TF del sensor, rf2o, el mapa y AMCL =="
ros2 run tf2_ros static_transform_publisher \
    --x 0.02913 --y 0 --z 0.184699 --qx 0 --qy 0 --qz 1 --qw 0 \
    --frame-id base_link --child-frame-id laser \
    --ros-args -p use_sim_time:=true > "$SALIDA/tf.log" 2>&1 < /dev/null &

ros2 run rf2o_laser_odometry rf2o_laser_odometry_node \
    --ros-args --params-file "$SALIDA/rf2o.yaml" \
    > "$SALIDA/rf2o.log" 2>&1 < /dev/null &

ros2 run nav2_map_server map_server \
    --ros-args --params-file "$SALIDA/amcl.yaml" \
    > "$SALIDA/map_server.log" 2>&1 < /dev/null &

ros2 run nav2_amcl amcl \
    --ros-args --params-file "$SALIDA/amcl.yaml" \
    > "$SALIDA/amcl.log" 2>&1 < /dev/null &

# map_server y amcl son nodos de ciclo de vida: nacen 'unconfigured' y no
# publican nada hasta que alguien los activa. Sin este gestor, la corrida sale
# entera sin un solo /amcl_pose y los logs no se quejan.
ros2 run nav2_lifecycle_manager lifecycle_manager \
    --ros-args -p use_sim_time:=true -p autostart:=true \
    -p "node_names:=[map_server, amcl]" \
    > "$SALIDA/lifecycle.log" 2>&1 < /dev/null &

python3 "$SALIDA/volcar.py" "$SALIDA/trayectoria.csv" \
    > "$SALIDA/volcar.log" 2>&1 < /dev/null &
VOLCADOR=$!

disown -a

echo "== Esperando a que AMCL se active =="
sleep 12

if ! grep -q "Received a .* map" "$SALIDA/amcl.log" 2>/dev/null; then
    echo "AVISO: AMCL no dice haber recibido el mapa. Si la corrida sale sin"
    echo "       /amcl_pose, mira $SALIDA/map_server.log y $SALIDA/lifecycle.log"
fi

REMAPEO=()
[ "$TOPICO" != "/scan" ] && REMAPEO=(--remap "$TOPICO:=/scan")

echo "== Reproduciendo $BAG (velocidad real; espera a que termine) =="
if ! ros2 bag play "$BAG" --clock 100 --rate 1 "${REMAPEO[@]}" \
        > "$SALIDA/play.log" 2>&1 < /dev/null; then
    echo "ERROR: la reproduccion fallo. Ultimas lineas de play.log:" >&2
    tail -5 "$SALIDA/play.log" >&2
    exit 1
fi

echo "== Dejando cerrar la ultima actualizacion =="
sleep 8
kill -INT "$VOLCADOR" 2>/dev/null || true
sleep 3

# Los saltos de reloj se CUENTAN, no se buscan. Un salto hacia atras al
# arrancar la reproduccion es normal e inevitable: hasta ese momento los nodos
# van con la hora de pared, y en cuanto llega el primer /clock del bag el reloj
# retrocede a la hora en que se GRABO, que es anterior. Sale una vez por nodo
# con buffer de TF y no invalida nada. La averia del 2026-09-01 es otra cosa:
# dos publicadores de /clock peleando producen saltos REPETIDOS durante toda la
# corrida. Buscar la cadena sin contarla marcaba como invalida cualquier
# corrida sana.
MAX_SALTOS=0
for L in "$SALIDA"/*.log; do
    [ -f "$L" ] || continue
    N=$(grep -c "jump back in time" "$L" 2>/dev/null || true)
    [ "$N" -gt "$MAX_SALTOS" ] && MAX_SALTOS=$N
done

if [ "$MAX_SALTOS" -ge 2 ]; then
    echo
    echo "AVISO GRAVE: $MAX_SALTOS saltos de reloj hacia atras en un mismo log."
    echo "Hay otro publicador de /clock corriendo. ESTA CORRIDA NO VALE:"
    echo "mata todo y repite:"
    echo "  pkill -9 -f 'ros2 bag play'; pkill -9 -f rf2o_laser; pkill -9 -f amcl"
elif [ "$MAX_SALTOS" -eq 1 ]; then
    echo "(Un salto de reloj al empezar la reproduccion. Es lo normal: el bag se"
    echo " grabo antes de hoy. NO invalida la corrida.)"
fi

if [ ! -s "$SALIDA/trayectoria.csv" ]; then
    echo "ERROR: no se escribio la trayectoria. Mira $SALIDA/volcar.log" >&2
    exit 1
fi

N_ODOM=$(grep -c ',odom,' "$SALIDA/trayectoria.csv" || true)
N_AMCL=$(grep -c ',amcl,' "$SALIDA/trayectoria.csv" || true)

echo
echo "Trayectoria en $SALIDA/trayectoria.csv"
echo "  poses de odom : $N_ODOM"
echo "  poses de amcl : $N_AMCL"

if [ "$N_AMCL" -eq 0 ]; then
    echo
    echo "ERROR: ni una pose de /amcl_pose. Sin ellas no hay M2." >&2
    echo "       Mira $SALIDA/amcl.log. Si no dice 'Received a X x Y map', el" >&2
    echo "       problema es el map_server o el gestor de ciclo de vida." >&2
    exit 1
fi

echo
echo "Saca M1 y M2 con:"
echo "  python3 herramientas/medir_g2.py $SALIDA/trayectoria.csv --largo <L>"
