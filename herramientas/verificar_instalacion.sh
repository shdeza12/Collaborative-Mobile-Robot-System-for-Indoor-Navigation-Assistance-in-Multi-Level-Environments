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

# 'pwd -P' y no 'pwd': la ruta FISICA, sin enlaces. Desde el 2026-10-06 el
# repositorio se abre tambien por una segunda ruta que es un enlace a la primera, y
# con la ruta logica cada comparacion de abajo daba por distintas dos rutas que
# son la misma carpeta.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
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
#   - el valor va entre comillas dobles, para que una ruta con espacios no acabe
#     en 'not a valid identifier' al abrir la siguiente terminal;
#   - lo que se anade va entre comillas simples, para que '$GAZEBO_MODEL_PATH' se
#     escriba literal en ~/.bashrc y se expanda alli, no aqui;
#   - la guarda pregunta si ALGUNA linea activa de ~/.bashrc mete ya esta raiz en
#     GAZEBO_MODEL_PATH; NO si existe una linea identica, caracter a caracter, a
#     la que emitimos. La version anterior comparaba la linea entera con
#     'grep -qxF', asi que cualquier forma equivalente escrita a mano -sin
#     comillas, con otro espaciado- no coincidia y la orden anadia una SEGUNDA
#     copia de la misma ruta. No es hipotetico: el ~/.bashrc de este equipo tenia
#     la version sin comillas desde el 11-ago, y al pegar el consejo se duplicaba.
#   - '-F' compara literal, para que una ruta con corchetes o puntos no se lea
#     como expresion regular y la guarda deje de proteger sin dar ningun error;
#   - '^[[:space:]]*#' descarta las lineas comentadas, y la comprobacion de abajo
#     descarta las mismas. Si las dos no miraran igual, una linea comentada
#     dejaria a la guarda sin anadir nada y al consejo afirmando que ya esta:
#     el verificador seguiria fallando sin que nada de lo que dice lo explique.
# Los mundos y sus modelos viven en simulacion/ desde el 2026-10-24 (antes, en la raiz).
MODELOS="$REPO/simulacion"
CMD_GZP="grep -v '^[[:space:]]*#' ~/.bashrc 2>/dev/null | grep -F GAZEBO_MODEL_PATH | grep -qF '$MODELOS' || echo 'export GAZEBO_MODEL_PATH=\"\$GAZEBO_MODEL_PATH:$MODELOS\"' >> ~/.bashrc"

# ¿Alguna ruta de esta lista (separada por ':') es la carpeta simulacion/ del repositorio?
# Compara rutas RESUELTAS, no texto: '$HOME/<clon>', la misma ruta escrita entera y un
# enlace que apunte ahi son la misma carpeta. Comparar texto dio el 2026-10-06 un
# fallo falso con la variable bien puesta, y un consejo que habria anadido una
# cuarta linea duplicada a un ~/.bashrc que ya tenia tres.
contiene_repo() {
  local IFS=':' p
  for p in $1; do
    [[ -n "$p" && "$(readlink -f "$p" 2>/dev/null)" == "$MODELOS" ]] && return 0
  done
  return 1
}

# ¿Alguna linea activa de ~/.bashrc mete ya esta raiz en GAZEBO_MODEL_PATH? Se
# expanden $HOME, ${HOME} y ~ antes de resolver, que es lo que hara bash al abrir
# la terminal. Si dice que si, consejo_gzp no muestra CMD_GZP (aconseja recargar),
# asi que la guarda literal de CMD_GZP solo actua cuando la linea no existe en
# ninguna forma y no puede duplicarla.
bashrc_declara_raiz() {
  local linea
  while IFS= read -r linea; do
    linea="${linea//\$\{HOME\}/$HOME}"; linea="${linea//\$HOME/$HOME}"
    linea="${linea//\~/$HOME}"; linea="${linea//\"/}"; linea="${linea//\'/}"
    linea="${linea#*GAZEBO_MODEL_PATH=}"
    contiene_repo "$linea" && return 0
  done < <(grep -v '^[[:space:]]*#' "$HOME/.bashrc" 2>/dev/null | grep -F 'GAZEBO_MODEL_PATH=')
  return 1
}

# Que falte la variable tiene dos causas distintas, con arreglos distintos, y el
# consejo equivocado no es inofensivo. Si la linea NO esta en ~/.bashrc, hay que
# anadirla. Si SI esta, anadirla otra vez no arregla nada: escribir en ~/.bashrc
# no cambia una terminal que ya estaba abierta, de modo que el verificador vuelve
# a fallar exactamente igual y quien lo lee pega la orden una y otra vez sin que
# nada mejore. Lo que falta ahi es cargar el archivo, no volver a escribirlo.
consejo_gzp() {
  if bashrc_declara_raiz; then
    printf '         -> la linea YA esta en ~/.bashrc; falta que ESTA terminal la cargue\n'
    cmd 'exec bash'
  else
    cmd "$CMD_GZP"
  fi
}

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

paso 'src/aws-deepracer es un enlace a ESTE repositorio'
# Ser un enlace no basta: uno que apunte a otro clon -una descarga vieja, otra
# carpeta- pasa '-L' y compila un codigo distinto del que se esta editando. Es el
# incidente R7 por otra puerta.
if [ -L "$WS/src/aws-deepracer" ] \
   && [ "$(readlink -f "$WS/src/aws-deepracer")" == "$REPO/Robot/aws-deepracer" ]; then bien
elif [ -L "$WS/src/aws-deepracer" ]; then
  mal "es un enlace, pero a OTRA carpeta: $(readlink -f "$WS/src/aws-deepracer"). Se compila un codigo distinto del de este repositorio"
  cmd "rm $WS/src/aws-deepracer && ln -s $REPO/Robot/aws-deepracer $WS/src/aws-deepracer && cd $WS && colcon build --symlink-install"
else
  mal "es una COPIA, no un enlace. El codigo que se ejecuta dejara de ser el versionado y divergiran en silencio"
  cmd "rm -rf $WS/src/aws-deepracer && ln -s $REPO/Robot/aws-deepracer $WS/src/aws-deepracer && cd $WS && colcon build --symlink-install"
fi

paso 'el workspace esta al dia con el codigo'
# Que exista un workspace compilado no dice que corresponda al codigo de hoy. El
# 2026-10-06, tras un 'git pull', 'robot.sh robot1 nav2' murio con «executable
# 'agente' not found»: el ejecutable entro el 7-sep y el workspace era del 4-sep.
# Todas las comprobaciones de este script pasaban.
if DESFASE=$(python3 "$REPO/herramientas/comprobar_workspace.py" --ws "$WS" --silencioso 2>&1); then bien
else
  mal "hay que recompilar; el codigo cambio despues de la ultima compilacion:"
  # Solo los paquetes y sus motivos: la orden va aparte, bajo 'Ejecutar', como en
  # el resto del script.
  printf '%s\n' "$DESFASE" | grep -E '^  ([A-Za-z0-9_]+:|  - )' | sed 's/^/       /'
  cmd "cd $WS && colcon build --symlink-install"
fi

# shellcheck disable=SC1090,SC1091
source /opt/ros/humble/setup.bash >/dev/null 2>&1
# shellcheck disable=SC1090,SC1091
source "$WS/install/setup.bash" >/dev/null 2>&1

# Los paquetes se DESCUBREN en el repositorio, no se escriben a mano. La lista fija
# decia «los seis paquetes» y el proyecto tiene ocho desde que entraron
# coordinacion y coordinacion_msgs: los dos que llevan el aporte del proyecto eran
# justo los que este script no miraba. Es la misma regla que ya sigue la seccion 7
# con los mundos.
PAQUETES=$(python3 -c "
import sys; sys.path.insert(0, '$REPO/herramientas')
from comprobar_workspace import paquetes, PAQUETES_DIR
print(' '.join(sorted(n for n, _, _ in paquetes(PAQUETES_DIR))))")
titulo "3. Los $(wc -w <<< "$PAQUETES") paquetes del repositorio"
for p in $PAQUETES; do
  paso "$p"
  if ros2 pkg prefix "$p" >/dev/null 2>&1; then bien
  else
    mal "no lo encuentra ROS: hay que recompilar el workspace"
    cmd "cd $WS && colcon build --symlink-install"
  fi
done

# Dos dependencias que 'rosdep install' NO trae, porque ningun package.xml puede
# declararlas: la interfaz web no es un paquete ROS, y el formato de los bags es
# del sistema, no de un nodo. Las dos se descubrieron faltando en un equipo con el
# resto en verde (2026-10-06): sin rosbridge, el §4 de GUIA_ARRANQUE.md no arranca
# la interfaz del telefono; sin mcap, componer_registro.py no lee los bags que
# graban los vehiculos en Jazzy.
paso 'rosbridge_server (interfaz web, OE3)'
if ros2 pkg prefix rosbridge_server >/dev/null 2>&1; then bien
else
  mal "sin el, la interfaz del telefono no puede hablar con el coordinador (GUIA_ARRANQUE.md §4)"
  cmd 'sudo apt install ros-humble-rosbridge-suite'
fi

paso 'lectura de bags mcap (los que graban los vehiculos)'
if ros2 bag list storage 2>/dev/null | grep -qx mcap; then bien
else
  mal "componer_registro.py no podra leer los bags grabados en los vehiculos"
  cmd 'sudo apt install ros-humble-rosbag2-storage-mcap'
fi

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

paso 'GAZEBO_MODEL_PATH incluye la carpeta simulacion/ del repositorio'
if contiene_repo "${GAZEBO_MODEL_PATH:-}"; then bien
else
  mal "sin esto, todo mundo que use model:// carga vacio y sin dar error"
  consejo_gzp
fi

for w in mundo_definitivo_piso1.world mundo_definitivo_piso2.world mundo_definitivo.world primer_piso.world primer_piso_v2.world primer_piso_dos_niveles.world pasillo_grande.world; do
  paso "$w"
  if [ -f "$MODELOS/$w" ]; then bien
  else mal "no esta en simulacion/"; fi
done

# Que la variable este exportada no prueba que sirva. Los mundos con 'model://'
# se resuelven igual sin ella SI se lanza desde la raiz del repositorio, porque
# Gazebo tambien mira el directorio actual: por eso el fallo nunca aparece en el
# equipo de quien escribio las instrucciones. Aqui se resuelve desde /tmp, a
# proposito, para reproducir la situacion de quien lanza desde otra carpeta.
# Gazebo no aborta en ese caso -devuelve 0 y carga el mundo incompleto-, asi que
# lo que se inspecciona es su stderr.
#
# Los mundos a comprobar NO se escriben a mano: se descubren buscando 'model://'
# en la raiz. Una lista fija solo cubre los mundos que existian el dia que se
# escribio, y el que se anade despues -que es el que nadie ha probado todavia-
# se queda justo fuera de la unica guarda que lo protegia. Paso: se anadio
# 'primer_piso_dos_niveles.world', el unico de su familia que usa model://, y la
# comprobacion siguio mirando solo 'pasillo_grande.world'.
# 'GAZEBO_MODEL_DATABASE_URI' se vacia a proposito. Cuando Gazebo no encuentra un
# 'model://' en disco, lo BUSCA EN INTERNET antes de rendirse: sin esto la
# comprobacion tarda unos dos minutos y parece colgada, justo en el unico caso
# que importa -clon recien bajado, sin GAZEBO_MODEL_PATH- y justo para la persona
# que menos margen tiene para saber que hay que esperar. El 'timeout' es la
# segunda linea: si algun dia la variable deja de bastar, el script falla en 20 s
# con un motivo, en vez de quedarse quieto sin decir nada.
paso 'los model:// externos resuelven desde otra carpeta'
MUNDOS_URI=$(grep -l 'model://' "$MODELOS"/*.world 2>/dev/null || true)
if [ -z "$MUNDOS_URI" ]; then
  mal 'ningun .world de simulacion/ usa model://, no se puede comprobar'
elif ! command -v gz >/dev/null; then
  aviso 'no esta la herramienta gz; se omite'
else
  URI_ROTOS=()
  for w in $MUNDOS_URI; do
    SDF_ERR=$(cd /tmp && GAZEBO_MODEL_DATABASE_URI='' timeout 20 gz sdf -p "$w" 2>&1 >/dev/null) || true
    if echo "$SDF_ERR" | grep -q 'Unable to find uri'; then
      URI_ROTOS+=("$(basename "$w"): $(echo "$SDF_ERR" | grep -m1 -o 'Unable to find uri\[[^]]*\]')")
    fi
  done
  if [ ${#URI_ROTOS[@]} -gt 0 ]; then
    # Una linea por mundo, todas sangradas igual: 'mal' solo sangra la primera.
    mal "${URI_ROTOS[0]}"
    for i in "${URI_ROTOS[@]:1}"; do printf '         -> %s\n' "$i"; done
    consejo_gzp
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
