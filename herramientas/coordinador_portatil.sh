#!/bin/bash
# Coordinador, grabador de misiones e interfaz en el PORTATIL. El coordinador y el
# grabador corren en un contenedor con ROS 2 Jazzy; rosbridge y la pagina, en el
# portatil (Humble).
#
# USO (en el portatil, desde la raiz del repositorio)
#     bash herramientas/coordinador_portatil.sh construir     # con internet; y tras cambiar coordinacion
#     bash herramientas/coordinador_portatil.sh arrancar      # 1.º el coordinador
#     bash herramientas/coordinador_portatil.sh interfaz      # 2.º rosbridge y la pagina (puerto 8000)
#     bash herramientas/coordinador_portatil.sh grabar G5_01  # 3.º antes de pedir la mision; Enter al terminar
#     bash herramientas/coordinador_portatil.sh registro      # ultimas lineas del coordinador
#     bash herramientas/coordinador_portatil.sh parar         # todo lo de arriba
#
# POR QUE EN EL PORTATIL (2026-10-09)
# -----------------------------------
# La decision D6 ponia el coordinador en un vehiculo, porque NavigateToPose no es la
# misma accion en Humble y en Jazzy (R8). El 8-oct, con el coordinador y el grabador
# en racey y las dos cadenas en la red, las tarjetas llegaron a carga 22-33 y G-5 no
# se pudo correr. Con Jazzy en un contenedor, el coordinador corre en el portatil,
# el servidor central del anteproyecto, y cada vehiculo habla solo con el.
#
# CUATRO PROCESOS ROS COMO MAXIMO EN EL PORTATIL, Y ESTOS PRIMERO
# ---------------------------------------------------------------
# Cada vehiculo tiene al portatil como unico par conocido (ROS_STATIC_PEERS, en
# nav2_mapa_guardado.sh), y Fast DDS solo se anuncia a los participantes 0 a 3 de
# esa maquina: es el 'maxInitialPeersRange' de 4 del transporte UDP. Por eso en el
# portatil solo pueden correr el coordinador, el grabador, rosbridge_websocket y
# rosapi, y en ese orden de arranque. Nada de 'ros2 topic ...' en el portatil
# durante una mision: ocuparia uno de los cuatro. Este guion para el demonio de ros2.
#
# El grabador graba la misma lista fija que grabar_mision_vehiculo.sh. La /tf, la
# IMU y rf2o de cada vehiculo no llegan al portatil (son internos del vehiculo);
# la pose en el mapa de los dos va en /robotN/estado.

set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGEN=coordinador_jazzy
EVIDENCIA="${EVIDENCIA:-$HOME/tesis_evidencia}"
CATALOGO="$REPO/Robot/aws-deepracer/deepracer_bringup/config"
ENTORNO='source /opt/ros/jazzy/setup.bash && source /coordinacion_ws/install/setup.bash'

rojo()  { printf '\033[31m%s\033[0m\n' "$*"; }
verde() { printf '\033[32m%s\033[0m\n' "$*"; }
info()  { printf '\033[36m==\033[0m %s\n' "$*"; }

parar_demonio() {
  # El demonio de ros2 del portatil es un participante mas: fuera.
  (source /opt/ros/humble/setup.bash 2>/dev/null && ros2 daemon stop >/dev/null 2>&1) || true
}

construir() {
  info "construyendo $IMAGEN (Jazzy, coordinacion y coordinacion_msgs)"
  docker build -t "$IMAGEN" -f "$REPO/Robot/docker/coordinador_jazzy/Dockerfile" "$REPO/Robot/aws-deepracer"
}

arrancar() {
  docker image inspect "$IMAGEN" >/dev/null 2>&1 || { rojo "falta la imagen: bash $0 construir"; exit 1; }
  parar_demonio
  docker rm -f coordinador >/dev/null 2>&1
  mkdir -p "$EVIDENCIA/registros"
  info "coordinador en el contenedor (condicion hardware, pisos 3 y 4)"
  # --user: lo que escriba queda a nombre del usuario del portatil.
  docker run -d --name coordinador --network host --user "$(id -u):$(id -g)" \
      -e HOME=/tmp -e ROS_LOG_DIR=/tmp/ros_log \
      -v "$CATALOGO:/catalogo:ro" -v "$EVIDENCIA:/evidencia" "$IMAGEN" \
      bash -c "$ENTORNO && exec ros2 run coordinacion coordinador --ros-args \
          -p condicion:=hardware -p ruta_puntos:=/catalogo/puntos_interes_pisos34.yaml \
          -p robot_nivel_3:=robot1 -p robot_nivel_4:=robot2 -p ruta_registros:=/evidencia/registros" >/dev/null
  local i
  for i in $(seq 60); do
    docker logs coordinador 2>&1 | grep -q 'Coordinador listo' && break
    sleep 1
  done
  docker logs coordinador 2>&1 | grep -E 'condicion|media vuelta|Coordinador listo|GUARDIAN|Traceback|Error' | grep -v RTPS_TRANSPORT_SHM
  docker logs coordinador 2>&1 | grep -q 'Coordinador listo' && verde "   coordinador listo" || { rojo "   el coordinador no arranco: bash $0 registro"; exit 1; }
}

interfaz() {
  parar_demonio
  info "rosbridge (puerto 9090) y la pagina (puerto 8000)"
  pkill -f '[r]osbridge_websocket' ; pkill -f '[r]osapi_node' ; pkill -f '[h]ttp.server 8000'
  # Con 'ros2 run' y no con 'ros2 launch': el lanzador crea un nodo propio, que
  # seria un quinto participante (ver la cabecera).
  ( source /opt/ros/humble/setup.bash && source "$HOME/deepracer_sim_ws/install/setup.bash" \
      && setsid nohup ros2 run rosbridge_server rosbridge_websocket --ros-args \
           -p send_action_goals_in_new_thread:=true > /tmp/rosbridge.log 2>&1 < /dev/null & )
  sleep 2
  ( source /opt/ros/humble/setup.bash && setsid nohup ros2 run rosapi rosapi_node > /tmp/rosapi.log 2>&1 < /dev/null & )
  ( cd "$REPO" && setsid nohup python3 -m http.server 8000 --directory interfaz_web > /tmp/http_interfaz.log 2>&1 < /dev/null & )
  sleep 6
  ss -ltn | grep -q ':9090' && verde "   rosbridge en el puerto 9090" || rojo "   rosbridge no arranco: /tmp/rosbridge.log"
  ss -ltn | grep -q ':8000' && verde "   la pagina en http://$(hostname -I | cut -d' ' -f1):8000/" || rojo "   la pagina no arranco"
}

grabar() {
  local nombre="$1" destino="/evidencia/mision_$1"
  [ -e "$EVIDENCIA/mision_$nombre" ] && { rojo "ya existe $EVIDENCIA/mision_$nombre: una grabacion por mision"; exit 2; }
  docker ps --format '{{.Names}}' | grep -qx coordinador || { rojo "el coordinador no esta corriendo: bash $0 arrancar"; exit 1; }
  local topicos="/coordinacion/estado_mision /coordinacion/puntos_interes /coordinacion/confirmacion_piso /tf /tf_static"
  local ns
  for ns in robot1 robot2; do
    topicos="$topicos /$ns/odom /$ns/estado /$ns/amcl_pose /$ns/cmd_vel /$ns/plan /$ns/imu/data /$ns/odom_rf2o"
  done
  docker exec -d coordinador bash -c "$ENTORNO && ros2 bag record -s mcap -o $destino $topicos > /tmp/bag.log 2>&1"
  sleep 4
  info "grabando $EVIDENCIA/mision_$nombre (19 topicos). Pida la mision; pulse Enter cuando termine."
  trap 'cerrar_grabacion "$nombre"; exit 130' INT TERM HUP
  read -r _
  cerrar_grabacion "$nombre"
}

cerrar_grabacion() {
  # SIGINT es el cierre limpio de rosbag2: sin el no queda metadata.yaml.
  docker exec coordinador pkill -INT -f '[b]ag record' 2>/dev/null
  local i
  for i in $(seq 25); do
    [ -f "$EVIDENCIA/mision_$1/metadata.yaml" ] && break
    sleep 1
  done
  [ -f "$EVIDENCIA/mision_$1/metadata.yaml" ] && verde "== listo: $EVIDENCIA/mision_$1" \
      || rojo "AVISO: sin metadata.yaml; mira: docker exec coordinador cat /tmp/bag.log"
}

registro() { docker logs --tail "${1:-30}" coordinador 2>&1 | grep -v RTPS_TRANSPORT_SHM; }

parar() {
  docker exec coordinador pkill -INT -f '[b]ag record' 2>/dev/null
  sleep 3
  docker rm -f coordinador >/dev/null 2>&1 && echo "coordinador detenido"
  pkill -f '[r]osbridge_websocket'; pkill -f '[r]osapi_node'; pkill -f '[h]ttp.server 8000'
  echo "rosbridge y la pagina detenidos"
}

case "${1:-}" in
  construir) construir ;;
  arrancar)  arrancar ;;
  interfaz)  interfaz ;;
  grabar)    [ $# -eq 2 ] || { echo "uso: $0 grabar NOMBRE"; exit 2; }; grabar "$2" ;;
  registro)  registro "${2:-30}" ;;
  parar)     parar ;;
  *) sed -n '/^# USO/,/^# POR QUE/p' "$0" | sed '$d' | sed 's/^# \?//'; exit 2 ;;
esac
