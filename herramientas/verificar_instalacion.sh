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

# El comando que corrige el fallo va SOLO en su linea, con el rotulo aparte. Si
# se imprime 'Ejecutar: <comando>' todo seguido, al seleccionar la linea (triple
# clic) se arrastra la palabra 'Ejecutar:' delante del comando; bash falla al
# ejecutarla y, en una orden con '||', ese fallo se confunde con "la linea no
# estaba" y la parte de la derecha se ejecuta igual, una vez por cada intento.
cmd()    { printf '         Ejecutar:\n           %s\n' "$1"; }

# Orden que anade GAZEBO_MODEL_PATH a ~/.bashrc sin poder duplicarla ni romperla.
# Se emite en los dos sitios que la piden, identica, y esta construida asi:
#   - la ruta aparece UNA sola vez, dentro de una variable: la orden se acorta en
#     una copia entera de la ruta, y asi el ajuste de linea del terminal (tmux,
#     screen, less) tiene menos ocasiones de partirla con un salto real;
#   - el valor va entre comillas dobles, para que una ruta con espacios no acabe
#     en 'not a valid identifier' al abrir la siguiente terminal;
#   - la asignacion va entre comillas simples, para que '$GAZEBO_MODEL_PATH' se
#     escriba literal en ~/.bashrc y se expanda alli, no aqui;
#   - 'grep -qxF' compara la LINEA ENTERA de forma LITERAL: -F evita que una ruta
#     con corchetes o puntos se interprete como expresion regular, y -x evita que
#     una linea ya corrupta que contenga el texto de al lado cuente como acierto.
CMD_GZP="LINEA='export GAZEBO_MODEL_PATH=\"\$GAZEBO_MODEL_PATH:$REPO\"'; grep -qxF \"\$LINEA\" ~/.bashrc || echo \"\$LINEA\" >> ~/.bashrc"

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
else
  mal 'falta Gazebo Classic 11'
  cmd 'sudo apt install gazebo libgazebo-dev'
fi

paso 'colcon'
if command -v colcon >/dev/null; then bien
else
  mal 'falta colcon, la herramienta que compila el workspace'
  cmd 'sudo apt install python3-colcon-common-extensions'
fi

# ------------------------------------------------------------- 2. workspace
titulo '2. Workspace compilado'

paso 'el workspace existe y esta compilado'
if [ -f "$WS/install/setup.bash" ]; then bien
else
  mal "no existe $WS/install/setup.bash"
  cmd "cd $WS && colcon build --symlink-install"
  echo; echo "Sin workspace compilado no se puede seguir."; exit 1
fi

paso 'src/aws-deepracer es un enlace al repositorio'
if [ -L "$WS/src/aws-deepracer" ]; then bien
else
  mal "es una COPIA, no un enlace. El codigo que se ejecuta dejara de ser el versionado y divergiran en silencio"
  cmd "rm -rf $WS/src/aws-deepracer && ln -s $REPO/Robot/aws-deepracer $WS/src/aws-deepracer && cd $WS && colcon build --symlink-install"
fi

# shellcheck disable=SC1090,SC1091
source /opt/ros/humble/setup.bash >/dev/null 2>&1
# shellcheck disable=SC1090,SC1091
source "$WS/install/setup.bash" >/dev/null 2>&1

titulo '3. Los seis paquetes'
for p in deepracer_bringup deepracer_description deepracer_drive_plugin \
         deepracer_interfaces_pkg cmdvel_to_servo_pkg enable_deepracer_nav_pkg; do
  paso "$p"
  if ros2 pkg prefix "$p" >/dev/null 2>&1; then bien
  else
    mal "no lo encuentra ROS: hay que recompilar el workspace"
    cmd "cd $WS && colcon build --symlink-install"
  fi
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
else
  mal "xacro fallo; probarlo a mano para ver el error"
  cmd "xacro $XACRO"
fi

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
  else
    mal "no parsea; el error completo sale al lanzarlo a mano"
    cmd "ros2 launch deepracer_bringup $l --show-args"
  fi
done

# ------------------------------------------------------------- 7. escenarios
titulo '7. Mundos y modelos de Gazebo'

paso 'GAZEBO_MODEL_PATH incluye la raiz del repositorio'
if [[ ":${GAZEBO_MODEL_PATH:-}:" == *":$REPO:"* ]]; then bien
else
  mal "sin esto, los mundos con model://pasillo_usta y model://pasillo_grande cargan vacios"
  cmd "$CMD_GZP"
fi

for w in primer_piso.world primer_piso_v2.world pasillo_grande.world; do
  paso "$w"
  if [ -f "$REPO/$w" ]; then bien
  else mal "no esta en la raiz del repositorio"; fi
done

# Que la variable este exportada no prueba que sirva. Los mundos con 'model://'
# se resuelven igual sin ella SI se lanza desde la raiz del repositorio, porque
# Gazebo tambien mira el directorio actual: por eso el fallo nunca aparece en el
# equipo de quien escribio las instrucciones. Aqui se resuelve desde /tmp, a
# proposito, para reproducir la situacion de quien lanza desde otra carpeta.
# Gazebo no aborta en ese caso -devuelve 0 y carga el mundo incompleto-, asi que
# lo que se inspecciona es su stderr.
paso 'los model:// externos resuelven desde otra carpeta'
if [ ! -f "$REPO/pasillo_grande.world" ]; then
  mal 'falta pasillo_grande.world, no se puede comprobar'
elif ! command -v gz >/dev/null; then
  aviso 'no esta la herramienta gz; se omite'
else
  SDF_ERR=$(cd /tmp && gz sdf -p "$REPO/pasillo_grande.world" 2>&1 >/dev/null)
  if echo "$SDF_ERR" | grep -q 'Unable to find uri'; then
    mal "$(echo "$SDF_ERR" | grep -m1 'Unable to find uri')"
    cmd "$CMD_GZP"
  else bien; fi
fi

# ---------------------------------------------------------------- resultado
titulo 'Resultado'
echo "  $OK comprobaciones pasan, $FALLOS fallan."
if [ "$FALLOS" -eq 0 ]; then
  cat <<FIN

  La instalacion esta completa. Siguiente paso, en una terminal:

    source $WS/install/setup.bash
    ros2 launch deepracer_bringup deepracer_sim.launch.py

  Esperado: Gazebo abre con el vehiculo visible, y en el log los 7
  controladores quedan en estado 'active'.

  El mundo por defecto sale de ESTE repositorio ($REPO),
  el mismo del que se compilo el codigo. Para usar otro:  world:=<ruta al .world>
FIN
  exit 0
else
  echo
  echo "  Corregir los fallos de arriba y volver a ejecutar este script."
  exit 1
fi
