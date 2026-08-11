#!/usr/bin/env bash
# Verifica que una instalacion nueva del proyecto esta completa y es utilizable,
# SIN levantar Gazebo ni ningun nodo.
#
# Para que existe: las instrucciones de instalacion se prueban una sola vez, en
# el equipo de quien las escribio, donde todo ya funcionaba. Este script las
# vuelve comprobables en cualquier equipo. Cada fallo dice que hacer.
#
# Uso:  herramientas/verificar_instalacion.sh [ruta_del_workspace]
# Por defecto el workspace es ~/deepracer_sim_ws
#
# Devuelve 0 si todo pasa, 1 si algo falla: se puede encadenar en scripts.

# A proposito SIN 'set -u' ni 'set -o pipefail':
#   - 'set -u' mata el script al hacer source de los setup.bash de ROS, que usan
#     variables sin definir.
#   - 'pipefail' marca como fallida cualquier tuberia que termine en 'grep -q',
#     porque grep sale al primer acierto y el productor recibe SIGPIPE.
# Un verificador debe llegar hasta el final y contar los fallos, no abortar.

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="${1:-$HOME/deepracer_sim_ws}"

OK=0
FALLOS=0

paso()   { printf '  %-52s' "$1"; }
bien()   { printf '\033[32m[ OK ]\033[0m\n';   OK=$((OK+1)); }
mal()    { printf '\033[31m[FALLO]\033[0m\n'; FALLOS=$((FALLOS+1)); [ -n "${1:-}" ] && printf '         -> %s\n' "$1"; }
aviso()  { printf '\033[33m[AVISO]\033[0m\n'; [ -n "${1:-}" ] && printf '         -> %s\n' "$1"; }
titulo() { printf '\n\033[1m%s\033[0m\n' "$1"; }

echo "Repositorio: $REPO"
echo "Workspace:   $WS"

# ---------------------------------------------------------------- 1. entorno
titulo '1. Entorno del sistema'

paso 'Ubuntu 22.04'
if grep -q '22.04' /etc/os-release 2>/dev/null; then bien
else aviso "se esperaba Ubuntu 22.04; otras versiones no estan probadas"; fi

paso 'ROS 2 Humble instalado'
if [ -f /opt/ros/humble/setup.bash ]; then bien
else mal 'falta /opt/ros/humble/setup.bash. Instalar ROS 2 Humble (docs.ros.org/en/humble)'; fi

paso 'Gazebo Classic 11'
if command -v gzserver >/dev/null && gzserver --version 2>&1 | grep -q 'version 11'; then bien
else mal 'falta Gazebo 11. sudo apt install gazebo libgazebo-dev'; fi

paso 'colcon'
if command -v colcon >/dev/null; then bien
else mal 'sudo apt install python3-colcon-common-extensions'; fi

# ------------------------------------------------------------- 2. workspace
titulo '2. Workspace compilado'

paso 'el workspace existe y esta compilado'
if [ -f "$WS/install/setup.bash" ]; then bien
else
  mal "no existe $WS/install/setup.bash. Ejecutar: cd $WS && colcon build --symlink-install"
  echo; echo "Sin workspace compilado no se puede seguir."; exit 1
fi

paso 'src/aws-deepracer es un enlace al repositorio'
if [ -L "$WS/src/aws-deepracer" ]; then bien
else mal "es una COPIA, no un enlace. El codigo que se ejecuta dejara de ser el versionado y divergiran en silencio. Corregir: rm -rf $WS/src/aws-deepracer && ln -s $REPO/Robot/aws-deepracer $WS/src/aws-deepracer && cd $WS && colcon build --symlink-install"; fi

# shellcheck disable=SC1090,SC1091
source /opt/ros/humble/setup.bash >/dev/null 2>&1
# shellcheck disable=SC1090,SC1091
source "$WS/install/setup.bash" >/dev/null 2>&1

titulo '3. Los seis paquetes'
for p in deepracer_bringup deepracer_description deepracer_drive_plugin \
         deepracer_interfaces_pkg cmdvel_to_servo_pkg enable_deepracer_nav_pkg; do
  paso "$p"
  if ros2 pkg prefix "$p" >/dev/null 2>&1; then bien
  else mal "no lo encuentra ROS. Recompilar: cd $WS && colcon build --symlink-install"; fi
done

# ------------------------------------------------------------ 4. contenido
titulo '4. Recursos instalados'
SHARE="$(ros2 pkg prefix deepracer_bringup 2>/dev/null)/share/deepracer_bringup"
for d in launch config maps behavior_trees; do
  paso "deepracer_bringup/$d"
  if [ -d "$SHARE/$d" ]; then bien
  else mal "no se instalo. Revisar install(DIRECTORY ...) en deepracer_bringup/CMakeLists.txt"; fi
done

# --------------------------------------------------------------- 5. el URDF
titulo '5. Descripcion del vehiculo'
XACRO="$(ros2 pkg prefix deepracer_description 2>/dev/null)/share/deepracer_description/models/xacro/deepracer/deepracer.xacro"
URDF=$(mktemp)

paso 'el URDF se genera desde el xacro'
if xacro "$XACRO" > "$URDF" 2>/dev/null; then bien
else mal "xacro fallo. Probar a mano para ver el error: xacro $XACRO"; fi

paso 'tiene los 12 enlaces esperados'
N=$(grep -c '<link' "$URDF" 2>/dev/null || echo 0)
if [ "$N" -eq 12 ]; then bien
else mal "salieron $N enlaces en vez de 12"; fi

# Las URIs package:// son el punto historico de fallo: RViz las resuelve por
# indice ament y Gazebo por GAZEBO_MODEL_PATH, y una URI mal formada solo falla
# en uno de los dos.
paso 'las mallas (package://) existen en disco'
FALTAN=''
while read -r uri; do
  pkg="${uri%%/*}"; rel="${uri#*/}"
  pref=$(ros2 pkg prefix "$pkg" 2>/dev/null) || { FALTAN="$FALTAN $uri"; continue; }
  [ -f "$pref/share/$pkg/$rel" ] || FALTAN="$FALTAN $uri"
done < <(grep -o 'package://[^"]*' "$URDF" | sed 's|package://||' | sort -u)
if [ -z "$FALTAN" ]; then bien
else mal "no resuelven:$FALTAN . La sintaxis correcta es package://<paquete>/<ruta>"; fi
rm -f "$URDF"

# ------------------------------------------------------------- 6. launchers
titulo '6. Los archivos de lanzamiento parsean'
for l in deepracer_sim.launch.py deepracer_spawn.launch.py slam_toolbox.launch.py \
         nav_amcl_demo_sim.launch.py deepracer_navigation_sim.launch.py \
         deepracer_localization_sim.launch.py; do
  paso "$l"
  if ros2 launch deepracer_bringup "$l" --show-args >/dev/null 2>&1; then bien
  else mal "no parsea. Ver el error con: ros2 launch deepracer_bringup $l --show-args"; fi
done

# ------------------------------------------------------------- 7. escenarios
titulo '7. Mundos y modelos de Gazebo'

paso 'GAZEBO_MODEL_PATH incluye la raiz del repositorio'
if [[ ":${GAZEBO_MODEL_PATH:-}:" == *":$REPO:"* ]]; then bien
else mal "anadir a ~/.bashrc:  export GAZEBO_MODEL_PATH=\$GAZEBO_MODEL_PATH:$REPO   (sin esto, los mundos que usan model://pasillo_usta y model://pasillo_grande cargan vacios)"; fi

for w in primer_piso.world primer_piso_v2.world pasillo_grande.world; do
  paso "$w"
  if [ -f "$REPO/$w" ]; then bien
  else mal "no esta en la raiz del repositorio"; fi
done

# ---------------------------------------------------------------- resultado
titulo 'Resultado'
echo "  $OK comprobaciones pasan, $FALLOS fallan."
if [ "$FALLOS" -eq 0 ]; then
  cat <<FIN

  La instalacion esta completa. Siguiente paso, en una terminal:

    source $WS/install/setup.bash
    ros2 launch deepracer_bringup deepracer_sim.launch.py world:=$REPO/primer_piso.world

  Esperado: Gazebo abre con el vehiculo visible, y en el log los 7
  controladores quedan en estado 'active'.
FIN
  exit 0
else
  echo
  echo "  Corregir los fallos de arriba y volver a ejecutar este script."
  exit 1
fi
