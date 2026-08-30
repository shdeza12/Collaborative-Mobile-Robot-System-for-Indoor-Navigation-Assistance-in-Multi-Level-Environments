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
# marcados como propios del robot pedido, leyendo DEEPRACER_ROBOT de
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
#   - El PUERTO de Gazebo es transporte puro. Solo lo usa este script, para
#     saber a que gzserver conectar y que puerto vigilar al parar. Se queda aqui.
#   - Pose, mapa, mundo y RELOJ se comparten con los launch y con el grabador.
#     Salen de deepracer_raiz_repo.py. Ya no se copian aqui: hasta el 2026-08-22
#     esta tabla era la tercera copia de la pose, y al cambiar de mundo se
#     actualizaron dos de las tres. La que se quedo vieja hacia nacer al
#     vehiculo fuera del pasillo sin dar ningun error.
#
# El reloj estuvo un rato escrito aqui, con los puertos, mientras parecia
# transporte. Dejo de serlo en cuanto el grabador tuvo que saber en que base de
# tiempo viene cada robot, asi que se mudo a la tabla compartida antes de tener
# dos copias.
case "$robot" in
  robot1) PUERTO=11345 ;;
  robot2) PUERTO=11346 ;;
  *) echo "ERROR: robot desconocido '$robot' (robot1 o robot2)" >&2; uso ;;
esac

# UN SOLO DOMINIO PARA LOS DOS ROBOTS, desde el 2026-08-30.
#
# Hasta esa fecha robot1 iba en el dominio 0 y robot2 en el 2. Aquello aislaba
# las dos pilas de maravilla, y ese era justamente el problema: el coordinador
# de S22 tiene que hablar con las dos, y a traves de un limite de dominio no se
# ve nada. La alternativa -un proceso con dos contextos rclpy- funciona (se
# midio, P1b) pero mete complejidad permanente en el coordinador para resolver
# algo que aqui se arregla con una linea.
#
# Lo que separa a las dos pilas ya no es el dominio, son los NOMBRES: cada robot
# vive bajo su namespace, cada marco TF lleva su prefijo -incluido 'map'- y cada
# gzserver tiene su puerto y su reloj. Se verifico con las dos pilas completas
# corriendo a la vez: 14 controladores activos, cero cruce de datos, y robot2
# sobrevive a la muerte de robot1 (Evidencia/S21_bloqueo_dominios.md §6).
#
# El dominio 0 no es arbitrario: es el defecto de ROS 2, asi que una terminal
# sin exportar nada ve la mision entera.
DOMINIO=0

# DESPLIEGUE EN DOS MAQUINAS. La variable viene de la rama camara-y-dominio y se
# conserva porque la idea de fondo sigue en pie: repartiendo un robot por host,
# la separacion la da la red -cada Gazebo con su GAZEBO_MASTER_URI- y sigue
# interesando que los dos compartan dominio para que el coordinador los alcance.
#
#   Maquina A:  DOMINIO_FORZADO=7 herramientas/robot.sh robot1 nav2
#   Maquina B:  DOMINIO_FORZADO=7 herramientas/robot.sh robot2 nav2
#   Coordinador en cualquiera de las dos, con ROS_DOMAIN_ID=7
#
# DOS COSAS QUE DECIA ESTA NOTA Y HAY QUE CORREGIR, porque se escribio el 26-ago
# cuando cada robot iba en su dominio:
#
# 1. Decia que "el relevo no se puede demostrar de extremo a extremo en un solo
#    equipo". Ya no es cierto, y no por un argumento sino por una corrida: el
#    2026-08-30 la mision piso1_representacion -> piso2_lab_313 se completo en
#    un solo PC con un relevo, exito true, 47,6 s (Evidencia/S21_bloqueo_
#    dominios.md). Dos maquinas es una MEJORA de holgura, no un requisito.
#
# 2. Decia que con los dos robots en un portatil el RTF cae a 0,955 y 0,811, por
#    debajo del minimo de RNF-06. Esa misma corrida del 30-ago midio RTF 0,9981
#    con las dos pilas y Nav2 arriba. Las dos medidas no se han conciliado; la
#    sospecha es que la de agosto llevaba la GUI de Gazebo abierta y esta no,
#    pero NADIE lo anoto, asi que es una sospecha. Hasta que se repita con la
#    GUI declarada, ninguna de las dos cifras sirve para justificar el reparto.
#
# NO ESTA PROBADO EN DOS MAQUINAS: aqui solo hay una. Lo que si esta comprobado
# es que la variable cambia el dominio de verdad. Falta que el descubrimiento
# DDS funcione entre los dos hosts, que suele fallar por multicast bloqueado en
# la red o por aislamiento de clientes en el punto de acceso wifi.
if [[ -n "${DOMINIO_FORZADO:-}" ]]; then
  DOMINIO="$DOMINIO_FORZADO"
  echo "   AVISO: dominio forzado a $DOMINIO (despliegue en varias maquinas)"
fi

# 'python3' a secas basta: el modulo no importa nada de ROS, asi que se lee antes
# de hacer 'source' de nada. Si falla, el mensaje del propio modulo dice que
# robots conoce, y se corta aqui en vez de lanzar Gazebo con una pose vacia.
LAUNCH_DIR="$REPO/Robot/aws-deepracer/deepracer_bringup/launch"
if ! POSE=$(python3 -c "
import sys
sys.path.insert(0, '$LAUNCH_DIR')
from deepracer_raiz_repo import pose_por_defecto, reloj_de
p = pose_por_defecto('$robot')
print(p['x'], p['y'], p['z'], p['yaw'], p['nivel'], p['mapa'] or '-', p['mundo'] or '-',
      reloj_de('$robot'))
" 2>&1); then
  echo "ERROR: no se pudo leer la configuracion de '$robot'" >&2
  echo "       en $LAUNCH_DIR/deepracer_raiz_repo.py" >&2
  printf '%s\n' "$POSE" | sed 's/^/       /' >&2
  exit 1
fi
# MAPA y MUNDO valen '-' cuando ese nivel todavia no tiene el archivo: la cadena
# vacia se perderia al partir la linea y NIVEL acabaria en MAPA.
read -r X Y Z YAW NIVEL MAPA MUNDO_REL RELOJ <<< "$POSE"

# EL MUNDO ES DEL NIVEL, NO DEL PROYECTO. Hasta el 2026-08-23 esta linea fijaba
# 'mundo_definitivo.world' para los dos robots, y aquel mundo traia los dos pisos
# en la misma escena: el LiDAR simulado alcanza 10.0 m y entre los dos pasillos
# hay 5.44 m, de modo que robot1 media paredes del piso 2. El porque completo, con
# las cifras, esta en la cabecera de deepracer_raiz_repo.py.
if [[ "$MUNDO_REL" == "-" ]]; then
  echo "ERROR: '$robot' no tiene mundo declarado en POSE_INICIAL" >&2
  exit 1
fi
MUNDO="${MUNDO:-$REPO/$MUNDO_REL}"

# --- procesos de ESTE robot -------------------------------------------------
# EL FILTRO ES UNA MARCA PROPIA, NO EL DOMINIO. Hasta el 2026-08-30 se leia
# ROS_DOMAIN_ID de /proc/<pid>/environ y bastaba, porque cada robot tenia el
# suyo. Con los dos en el dominio 0 ese criterio ya no distingue nada: dejarlo
# como estaba haria que 'robot2 parar' matara a robot1 y a su Gazebo, sin
# preguntar y sin dar error.
#
# Se marca con DEEPRACER_ROBOT, que 'preparar_entorno' exporta antes del 'exec'.
# Todo lo que este script lance lo hereda, incluidos los nodos que abre un
# launch varios niveles mas abajo.
#
# El modo de fallo cambia de sitio, y hacia el lado bueno: un proceso lanzado a
# mano -sin pasar por aqui- no lleva la marca y NO se mata. Antes tampoco se
# distinguia, pero el error era matar de mas; ahora es matar de menos, y eso se
# ve enseguida porque el puerto sigue ocupado. Aun asi se avisa: sin el aviso,
# 'parar' diria "no habia nada" con un gzserver vivo delante.
PATRONES='gzserver|gzclient|ros2 launch deepracer|spawn_entity|robot_state_publisher|static_transform_publisher|rviz2|slam_toolbox|ros2_control_node|controller_manager|component_container|teleop_twist|amcl|map_server|planner_server|controller_server|bt_navigator|behavior_server|smoother_server|velocity_smoother|waypoint_follower|lifecycle_manager'

# Cada linea sale clasificada: 'MIO <pid>' o 'AJENO <pid> <programa>'. La
# etiqueta no es adorno. La funcion se llama dentro de '$( )', que es una
# subshell, asi que cualquier variable que rellenara aqui se perderia al volver:
# lo unico que cruza es la salida estandar. Se intento primero con una variable
# global y el aviso no aparecia nunca.
clasificar_procesos() {
  local pid duenno prog
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
    duenno=$(tr '\0' '\n' 2>/dev/null < "/proc/$pid/environ" | sed -n 's/^DEEPRACER_ROBOT=//p' | head -1) || continue
    if [[ "$duenno" == "$robot" ]]; then
      echo "MIO $pid"
    elif [[ -z "$duenno" ]]; then
      echo "AJENO $pid $prog"
    fi
    # Un proceso marcado como del OTRO robot no se nombra siquiera: es normal
    # que este ahi y no es asunto de esta orden.
  done
  return 0
}

parar_robot() {
  local clasificados pids ajenos
  clasificados=$(clasificar_procesos)
  pids=$(awk '$1=="MIO"{print $2}' <<< "$clasificados")
  ajenos=$(awk '$1=="AJENO"{print "   " $2, $3}' <<< "$clasificados")

  if [[ -z "$pids" ]]; then
    echo "   no habia nada corriendo marcado como $robot"
  else
    echo "   matando $(echo "$pids" | wc -l) procesos de $robot"
    kill -9 $pids 2>/dev/null || true
    sleep 2
  fi
  if [[ -n "$ajenos" ]]; then
    echo "   AVISO: estos procesos son de ROS/Gazebo pero no los lanzo robot.sh," >&2
    echo "          asi que no se sabe de quien son y NO se tocan:" >&2
    printf '%s\n' "$ajenos" >&2
    echo "          Si estorban, matalos a mano (kill -9)." >&2
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
  # La marca que usa pids_del_robot(). Va aqui y no en cada rama porque tiene que
  # heredarla TODO lo que se lance, no solo Gazebo.
  export DEEPRACER_ROBOT="$robot"
  # Se exporta SIEMPRE, tambien para robot1 aunque 11345 sea el defecto de
  # Gazebo. Antes se ponia solo si el puerto no era el defecto, y eso dejaba una
  # trampa: en una terminal donde ya se hubiera lanzado robot2, la variable
  # seguia apuntando a 11346 y 'robot1 sim' se conectaba al gzserver del otro.
  # Con los dos robots en el mismo dominio ya no hay una segunda barrera que lo
  # atrape, asi que se fija a mano.
  export GAZEBO_MASTER_URI="http://localhost:$PUERTO"
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
    echo "== Limpiando lo que quedara de $robot =="
    parar_robot
    preparar_entorno
    echo "== $robot: Gazebo en $(basename "$MUNDO"), piso $NIVEL, pose ($X, $Y), reloj $RELOJ =="
    exec ros2 launch deepracer_bringup deepracer_sim.launch.py \
      world:="$MUNDO" namespace:="$robot" x:="$X" y:="$Y" z:="$Z" yaw:="$YAW" \
      clock_topic:="$RELOJ" "${extras[@]}"
    ;;

  slam)
    preparar_entorno
    echo "== $robot: slam_toolbox (reloj $RELOJ) =="
    exec ros2 launch deepracer_bringup slam_toolbox.launch.py \
      namespace:="$robot" clock_topic:="$RELOJ" "${extras[@]}"
    ;;

  nav2)
    echo "== Limpiando lo que quedara de $robot =="
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
    # Y si SI hay mapa, hay que pasarlo. El defecto del launch es el del piso 1
    # -tiene que serlo, porque un launch no sabe que robot lo invoca- y desde que
    # el piso 2 tiene mapa propio (2026-08-23) el guardian de arriba ya no salta.
    # Sin esta linea, 'robot2 nav' cargaria el mapa del piso 1 en silencio, que es
    # exactamente el fallo que aquel guardian existia para impedir.
    if [[ ! " ${extras[*]} " =~ " map:=" ]]; then
      extras+=("map:=$REPO/Robot/aws-deepracer/deepracer_bringup/maps/$MAPA")
    fi
    echo "== $robot: Nav2 + AMCL + Gazebo, piso $NIVEL, mapa $MAPA, reloj $RELOJ =="
    exec ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py \
      world:="$MUNDO" namespace:="$robot" x:="$X" y:="$Y" z:="$Z" yaw:="$YAW" \
      clock_topic:="$RELOJ" "${extras[@]}"
    ;;

  rviz)
    preparar_entorno
    cfg="$(config_rviz)"
    echo "== $robot: RViz con $(basename "$cfg") =="
    exec rviz2 -d "$cfg"
    ;;

  teleop)
    preparar_entorno
    echo "== $robot: teclado -> /$robot/cmd_vel =="
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
    echo "== $robot, reloj $RELOJ =="
    activos=$(ros2 control list_controllers -c "/$robot/controller_manager" 2>/dev/null | grep -c active || true)
    echo "   controladores activos : ${activos:-0} de 7"
    echo "   odom                  : $(frecuencia "/$robot/odom")"
    echo "   scan                  : $(frecuencia "/$robot/scan")"
    ;;

  parar)
    echo "== Parando $robot =="
    parar_robot
    ;;

  *)
    echo "ERROR: accion desconocida '$accion'" >&2
    uso
    ;;
esac
