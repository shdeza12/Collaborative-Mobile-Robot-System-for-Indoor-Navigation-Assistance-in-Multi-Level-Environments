#!/usr/bin/env bash
# Limpia Gazebo y lanza la simulacion del DeepRacer.
#
# Existe porque relanzar sobre un gzserver huerfano hace que el nuevo muera con
# codigo 255 sin explicar por que: el viejo sigue agarrado al puerto 11345.
# Ctrl-C sobre 'ros2 launch' no siempre mata a gzserver.
#
# Uso:
#   herramientas/lanzar_sim.sh                     # mundo vacio
#   herramientas/lanzar_sim.sh primer_piso.world   # mundo del proyecto
#   herramientas/lanzar_sim.sh /ruta/absoluta.world
#
# Cualquier argumento con ':=' se pasa tal cual a 'ros2 launch'. El orden no
# importa y se pueden combinar:
#   herramientas/lanzar_sim.sh namespace:=robot1
#   herramientas/lanzar_sim.sh primer_piso.world namespace:=robot1 x:=2.0

# Sin 'set -u': los setup.bash de ROS referencian variables no definidas
# (AMENT_TRACE_SETUP_FILES entre otras) y abortarian el script al sourcearlos.
set -eo pipefail

WS="$HOME/deepracer_sim_ws"
MUNDOS="$HOME/Documents/Tesis"
PUERTO_GAZEBO=11345

# Se separa por FORMA, no por posicion: lo que lleva ':=' es un argumento de
# launch, lo demas es el mundo. Asi 'lanzar_sim.sh namespace:=robot1' funciona
# sin tener que escribir el mundo por defecto solo para llegar al segundo hueco.
mundo=""
extras=()
for arg in "$@"; do
  case "$arg" in
    *:=*) extras+=("$arg") ;;
    *)    mundo="$arg" ;;
  esac
done

mundo="${mundo:-/usr/share/gazebo-11/worlds/empty.world}"
# Si no es ruta absoluta, se busca en el directorio de mundos del proyecto.
[[ "$mundo" != /* ]] && mundo="$MUNDOS/$mundo"

if [[ ! -f "$mundo" ]]; then
  echo "ERROR: no existe el mundo '$mundo'" >&2
  exit 1
fi

echo "== Limpiando lanzamientos anteriores =="
# Ctrl-C sobre 'ros2 launch' no mata a sus hijos: quedan huerfanos y siguen
# publicando. Los static_transform_publisher huerfanos son especialmente
# daninos porque /tf_static es latched y contaminan el arbol TF del
# lanzamiento nuevo.
#
# Se usa 'pkill -f' (linea de comando completa) y no 'pkill -x' (nombre exacto)
# porque el nombre de proceso se trunca a 15 caracteres:
# 'static_transform_publisher' nunca coincidiria.
#
# 'pkill -f' es seguro AQUI, dentro de un script: pkill nunca se mata a si
# mismo, y la linea de comando del script no contiene estos patrones. Escrito
# a mano en la terminal si es peligroso, porque coincide con el shell padre.
#
# La lista incluye Nav2, RViz y el contenedor de componentes porque un
# 'nav_amcl_demo_sim.launch.py' abandonado deja /amcl, /map_server y compania
# vivos en la RAIZ. Con el robot bajo namespace eso produce nodos duplicados
# ('nodes in the graph that share an exact name') y ensucia toda verificacion.
for patron in "ros2 launch deepracer" gzserver gzclient \
              robot_state_publisher static_transform_publisher spawn_entity.py \
              rviz2 component_container nav2 slam_toolbox \
              amcl map_server controller_server planner_server bt_navigator \
              behavior_server smoother_server velocity_smoother \
              waypoint_follower lifecycle_manager; do
  pkill -9 -f "$patron" 2>/dev/null || true
done
sleep 1

for patron in gzserver robot_state_publisher static_transform_publisher; do
  # 'pgrep -c' YA imprime 0 cuando no encuentra nada, pero ademas sale con
  # codigo 1. Un '|| echo 0' anadiria un segundo 0 y la variable quedaria con
  # dos lineas ("0\n0"), que rompe la comparacion aritmetica. La asignacion de
  # respaldo va fuera de la sustitucion.
  vivos=$(pgrep -cf "$patron" 2>/dev/null) || vivos=0
  [[ "$vivos" -gt 0 ]] && echo "   AVISO: quedan $vivos procesos '$patron'"
done

# La comprobacion buena es el PUERTO, no 'pgrep': los procesos muertos quedan
# como zombis (<defunct>) y siguen apareciendo en pgrep aunque ya no estorben.
for intento in $(seq 1 10); do
  if ! ss -ltn 2>/dev/null | grep -q ":$PUERTO_GAZEBO "; then
    echo "   puerto $PUERTO_GAZEBO libre"
    break
  fi
  if [[ $intento -eq 10 ]]; then
    echo "ERROR: el puerto $PUERTO_GAZEBO sigue ocupado tras 10 s." >&2
    ss -ltnp 2>/dev/null | grep ":$PUERTO_GAZEBO " >&2 || true
    exit 1
  fi
  sleep 1
done

echo "== Preparando entorno =="
source /opt/ros/humble/setup.bash
if [[ ! -f "$WS/install/setup.bash" ]]; then
  echo "ERROR: no hay workspace compilado en $WS" >&2
  echo "       compila con: cd $WS && colcon build --symlink-install" >&2
  exit 1
fi
source "$WS/install/setup.bash"

echo "== Lanzando: $(basename "$mundo") ${extras[*]} =="
echo "   (para verificar, en otra terminal: python3 herramientas/verificar_contrato.py)"
exec ros2 launch deepracer_bringup deepracer_sim.launch.py world:="$mundo" "${extras[@]}"
