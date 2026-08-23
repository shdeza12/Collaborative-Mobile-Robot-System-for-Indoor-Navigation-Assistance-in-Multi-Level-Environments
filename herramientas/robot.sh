#!/usr/bin/env bash
# Punto de entrada unico para levantar cualquier pieza de un robot.
#
# Por que existe
# --------------
# Cada escenario de GUIA_EJECUCION.md pide teclear a mano el dominio ROS, el
# puerto de Gazebo, la pose de spawn, la ruta absoluta del mundo y el
# GAZEBO_MODEL_PATH. Olvidar el ultimo NO da error: gzserver se pasa 77 s
# consultando models.gazebosim.org, no resuelve el model:// y el fallo aparece
# mucho despues como "Service /spawn_entity unavailable", que apunta al sitio
# equivocado. Aqui esos cinco datos van en una sola tabla.
#
# Por que no se reutiliza lanzar_sim.sh
# -------------------------------------
# Aquel mata TODO lo que huela a ROS o Gazebo antes de arrancar. Con dos robots
# simultaneos eso tumba al companero. Este limita la limpieza a los procesos
# cuyo ROS_DOMAIN_ID coincide con el del robot pedido, leyendolo de
# /proc/<pid>/environ.
#
# Uso:
#   herramientas/robot.sh robot1 sim          # Gazebo + spawn
#   herramientas/robot.sh robot1 rviz         # RViz con el namespace correcto
#   herramientas/robot.sh robot1 slam         # slam_toolbox
#   herramientas/robot.sh robot2 nav2         # Nav2 + AMCL (levanta su Gazebo)
#   herramientas/robot.sh robot2 teleop       # teclado -> /robot2/cmd_vel
#   herramientas/robot.sh robot2 lidar        # medir paredes con el LiDAR
#   herramientas/robot.sh robot1 estado       # controladores, odom, scan
#   herramientas/robot.sh robot1 parar        # matar solo esta pila
#
# Todo argumento con ':=' se reenvia tal cual a 'ros2 launch', y sobreescribe lo
# que ponga la tabla:
#   herramientas/robot.sh robot1 sim gui:=false x:=-15.0

# Sin 'set -u': los setup.bash de ROS leen variables no definidas y abortarian.
set -eo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="${DEEPRACER_WS:-$HOME/deepracer_sim_ws}"
RVIZ_DIR="$REPO/Robot/aws-deepracer/deepracer_description/rviz"

uso() {
  sed -n '/^# Uso:/,/^$/p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
  exit 1
}

robot="${1:-}"
accion="${2:-}"
[[ -z "$robot" || -z "$accion" ]] && uso
shift 2
extras=("$@")

# Lo que distingue a un robot de otro se reparte en dos sitios, a proposito:
#
#   - Dominio y puerto son TRANSPORTE. Solo los usa este script, para aislar las
#     dos pilas entre si, y nunca han divergido de nada. Se quedan aqui.
#   - Pose y mapa son GEOMETRIA, y se comparten con los launch. Salen de
#     POSE_INICIAL, en deepracer_raiz_repo.py. Ya no se copian aqui: hasta el
#     2026-08-22 esta tabla era la tercera copia de la pose, y al cambiar de
#     mundo se actualizaron dos de las tres. La que se quedo vieja hacia nacer al
#     vehiculo fuera del pasillo sin dar ningun error.
case "$robot" in
  robot1) DOMINIO=0; PUERTO=11345 ;;
  robot2) DOMINIO=2; PUERTO=11346 ;;
  *) echo "ERROR: robot desconocido '$robot' (robot1 o robot2)" >&2; uso ;;
esac

# 'python3' a secas basta: el modulo no importa nada de ROS, asi que se lee antes
# de hacer 'source' de nada. Si falla, el mensaje del propio modulo dice que
# robots conoce, y se corta aqui en vez de lanzar Gazebo con una pose vacia.
LAUNCH_DIR="$REPO/Robot/aws-deepracer/deepracer_bringup/launch"
if ! POSE=$(python3 -c "
import sys
sys.path.insert(0, '$LAUNCH_DIR')
from deepracer_raiz_repo import pose_por_defecto
p = pose_por_defecto('$robot')
print(p['x'], p['y'], p['z'], p['yaw'], p['nivel'], p['mapa'] or '-')
" 2>&1); then
  echo "ERROR: no se pudo leer la pose de '$robot' de POSE_INICIAL" >&2
  echo "       en $LAUNCH_DIR/deepracer_raiz_repo.py" >&2
  printf '%s\n' "$POSE" | sed 's/^/       /' >&2
  exit 1
fi
# MAPA vale '-' cuando ese nivel todavia no tiene mapa: la cadena vacia se
# perderia al partir la linea y NIVEL acabaria en MAPA.
read -r X Y Z YAW NIVEL MAPA <<< "$POSE"

MUNDO="${MUNDO:-$REPO/mundo_definitivo.world}"

# --- procesos de ESTE robot -------------------------------------------------
# El filtro es el ROS_DOMAIN_ID del proceso, no su nombre. Un proceso sin la
# variable esta en el dominio 0 por defecto, que es justo el de robot1, asi que
# la ausencia cuenta como cero.
PATRONES='gzserver|gzclient|ros2 launch deepracer|spawn_entity|robot_state_publisher|static_transform_publisher|rviz2|slam_toolbox|ros2_control_node|controller_manager|component_container|teleop_twist|amcl|map_server|planner_server|controller_server|bt_navigator|behavior_server|smoother_server|velocity_smoother|waypoint_follower|lifecycle_manager'

pids_del_robot() {
  local pid dom prog
  # '|| true': pgrep sale con 1 cuando no encuentra nada y set -e abortaria.
  for pid in $(pgrep -f "$PATRONES" || true); do
    [[ "$pid" == "$$" ]] && continue
    # Nunca matar un shell. 'pgrep -f' mira la linea de comando completa, asi que
    # una terminal donde se tecleo 'ros2 launch deepracer...' coincide con el
    # patron: sin este filtro, 'parar' cerraria la terminal del usuario.
    prog=$(cat "/proc/$pid/comm" 2>/dev/null) || continue
    case "$prog" in bash|sh|zsh|dash) continue ;; esac
    # El '2>/dev/null' va ANTES del '<': bash aplica las redirecciones de
    # izquierda a derecha, y si el proceso murio entre el pgrep y esta linea el
    # fallo del '<' se imprimiria antes de quedar silenciado.
    dom=$(tr '\0' '\n' 2>/dev/null < "/proc/$pid/environ" | sed -n 's/^ROS_DOMAIN_ID=//p' | head -1) || continue
    [[ "${dom:-0}" == "$DOMINIO" ]] && echo "$pid"
  done
  return 0
}

parar_robot() {
  local pids
  pids=$(pids_del_robot)
  if [[ -z "$pids" ]]; then
    echo "   no habia nada corriendo en el dominio $DOMINIO"
  else
    echo "   matando $(echo "$pids" | wc -l) procesos del dominio $DOMINIO"
    kill -9 $pids 2>/dev/null || true
    sleep 2
  fi
  # La comprobacion buena es el PUERTO: un proceso muerto queda como zombi y
  # sigue saliendo en pgrep aunque ya no estorbe.
  for intento in $(seq 1 10); do
    ss -ltn 2>/dev/null | grep -q ":$PUERTO " || { echo "   puerto $PUERTO libre"; return 0; }
    [[ $intento -eq 10 ]] && { echo "ERROR: el puerto $PUERTO sigue ocupado" >&2; return 1; }
    sleep 1
  done
}

preparar_entorno() {
  source /opt/ros/humble/setup.bash
  [[ -f "$WS/install/setup.bash" ]] || {
    echo "ERROR: no hay workspace compilado en $WS" >&2
    echo "       compila con: cd $WS && colcon build --symlink-install" >&2
    exit 1
  }
  source "$WS/install/setup.bash"
  export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$REPO"
  export ROS_DOMAIN_ID="$DOMINIO"
  [[ "$PUERTO" != 11345 ]] && export GAZEBO_MASTER_URI="http://localhost:$PUERTO"
  return 0
}

# RViz solo trae configuracion para robot1. La de robot2 es la misma con los
# topicos y el prefijo TF cambiados; se deriva una vez y queda como archivo
# editable, no se regenera en cada arranque.
config_rviz() {
  local base="$RVIZ_DIR/robot1_completo.rviz"
  [[ "$robot" == robot1 ]] && { echo "$base"; return; }
  local destino="$RVIZ_DIR/${robot}_completo.rviz"
  [[ -f "$destino" ]] || sed "s/robot1/$robot/g" "$base" > "$destino"
  echo "$destino"
}

case "$accion" in
  sim)
    echo "== Limpiando el dominio $DOMINIO =="
    parar_robot
    preparar_entorno
    echo "== $robot: Gazebo en $(basename "$MUNDO"), piso $NIVEL, pose ($X, $Y), dominio $DOMINIO =="
    exec ros2 launch deepracer_bringup deepracer_sim.launch.py \
      world:="$MUNDO" namespace:="$robot" x:="$X" y:="$Y" z:="$Z" yaw:="$YAW" \
      "${extras[@]}"
    ;;

  slam)
    preparar_entorno
    echo "== $robot: slam_toolbox (dominio $DOMINIO) =="
    exec ros2 launch deepracer_bringup slam_toolbox.launch.py \
      namespace:="$robot" "${extras[@]}"
    ;;

  nav2)
    echo "== Limpiando el dominio $DOMINIO =="
    parar_robot
    preparar_entorno
    # nav_amcl_demo_sim.launch.py levanta TAMBIEN Gazebo: no se combina con 'sim'.
    #
    # Quien no tiene mapa de su nivel no puede lanzar Nav2 y ya. El mapa por
    # defecto del launch es el del piso 1, asi que un robot de otro piso
    # cargaria la geometria equivocada: AMCL no da error -converge contra las
    # paredes de otro sitio- y el sintoma aparece mucho despues como una ruta
    # imposible, que es el patron que ya costo el mapa inventado del 12-ago.
    #
    # La condicion mira el MAPA de POSE_INICIAL, no el nombre del robot. Escrita
    # como '$robot != robot1' habria que acordarse de tocarla al generar el mapa
    # del piso 2, y nadie se acuerda de eso.
    if [[ "$MAPA" == "-" && ! " ${extras[*]} " =~ " map:=" ]]; then
      echo "ERROR: $robot esta en el piso $NIVEL y no hay mapa de ese piso." >&2
      echo "       Sin 'map:=' se cargaria el del piso 1: AMCL localizaria" >&2
      echo "       contra otra geometria SIN dar error." >&2
      echo "       Generalo con herramientas/generar_mapa_desde_mundo.py y" >&2
      echo "       anotalo en POSE_INICIAL['$robot']['mapa']." >&2
      exit 1
    fi
    echo "== $robot: Nav2 + AMCL + Gazebo, piso $NIVEL (dominio $DOMINIO) =="
    exec ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py \
      world:="$MUNDO" namespace:="$robot" x:="$X" y:="$Y" z:="$Z" yaw:="$YAW" \
      "${extras[@]}"
    ;;

  rviz)
    preparar_entorno
    cfg="$(config_rviz)"
    echo "== $robot: RViz con $(basename "$cfg") (dominio $DOMINIO) =="
    exec rviz2 -d "$cfg"
    ;;

  teleop)
    preparar_entorno
    echo "== $robot: teclado -> /$robot/cmd_vel (dominio $DOMINIO) =="
    exec ros2 run teleop_twist_keyboard teleop_twist_keyboard \
      --ros-args -r /cmd_vel:="/$robot/cmd_vel"
    ;;

  lidar)
    preparar_entorno
    exec python3 "$REPO/herramientas/medir_paredes.py" "$robot"
    ;;

  estado)
    preparar_entorno
    # 'timeout' mata a 'ros2 topic hz' con SIGTERM, asi que la tuberia siempre
    # sale con codigo distinto de cero aunque haya medido bien. Por eso el
    # respaldo mira si la CADENA quedo vacia, no el codigo de salida.
    frecuencia() {
      local v
      v=$(timeout 8 ros2 topic hz "$1" 2>/dev/null | grep -m1 -o 'average rate: [0-9.]*' || true)
      echo "${v:-sin datos}"
    }
    echo "== $robot, dominio $DOMINIO =="
    activos=$(ros2 control list_controllers -c "/$robot/controller_manager" 2>/dev/null | grep -c active || true)
    echo "   controladores activos : ${activos:-0} de 7"
    echo "   odom                  : $(frecuencia "/$robot/odom")"
    echo "   scan                  : $(frecuencia "/$robot/scan")"
    ;;

  parar)
    echo "== Parando $robot (dominio $DOMINIO) =="
    parar_robot
    ;;

  *)
    echo "ERROR: accion desconocida '$accion'" >&2
    uso
    ;;
esac
