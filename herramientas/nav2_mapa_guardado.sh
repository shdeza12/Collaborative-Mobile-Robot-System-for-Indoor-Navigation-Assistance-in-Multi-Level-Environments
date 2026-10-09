#!/usr/bin/env bash
# Levanta Nav2 sobre un MAPA GUARDADO en el vehiculo y lo deja listo para navegar.
#
# POR QUE EXISTE Y POR QUE EL ORDEN IMPORTA
# -----------------------------------------
# Los costmaps de Nav2 leen /map **al configurarse**. Si map_server no esta
# ACTIVO en ese instante, la capa estatica queda vacia y el planificador aborta
# con "Start occupied" en CUALQUIER meta, apuntando al punto de partida en vez
# de a la causa. Costo la noche del 2026-09-24 encontrarlo. Ver el §3.1 de
# Documentos/GUION_NAVEGACION_USTA.md.
#
# El orden que este guion impone, y que no es negociable:
#   1. puente cmdvel_to_servo   (el launch NO lo arranca; sin el, Nav2
#                                planifica y el carro no se mueve, sin error)
#   2. set_max_speed $ESCALA    (0.9 por defecto; con 0.68 de fabrica, linear.x
#                                0.50 sale a throttle 0.4247 y el carro no
#                                arranca. Va por vehiculo: el 2-oct, con 0.9,
#                                amss-jgm9 no arranco y amss-ez9n llego a 1,58 m/s)
#   3. map_server + ACTIVAR     (antes del paso 5, o el paso 5 no sirve)
#   4. amcl + ACTIVAR + pose
#   5. el launch con slam:=false nav:=true
#
# TRES PARAMETROS QUE HAY QUE SOBREESCRIBIR
# -----------------------------------------
# El bloque amcl de nav2_params_jazzy.yaml se conserva -lo dice su propio
# comentario- solo para que la prueba de no divergencia compare los dos
# archivos enteros, asi que trae valores de simulacion:
#   use_sim_time  True -> false            (no hay /clock en el vehiculo)
#   yaml_filename mapa de simulacion -> el mapa real
#   scan_topic    'scan' -> /rplidar_ros/scan
# Ninguno da error si se deja mal: AMCL calla y el planificador aborta.
#
# LO QUE NO HACE, A PROPOSITO
# ---------------------------
# NO manda la meta. Ese es el instante en que el vehiculo se mueve solo, y lo
# dispara una persona mirando el carro. Al terminar imprime el comando.
#
# USO
#     CARRO=192.168.0.102 MAPA=/home/deepracer/tesis/mapa.yaml bash nav2_mapa_guardado.sh   (ruta fija del vehiculo)
#     NS=robot2 CARRO=192.168.0.102 MAPA=... bash nav2_mapa_guardado.sh   (bloque C: todo bajo /robot2)
#     POSE_X=24.45 POSE_Y=1.21 POSE_YAW=3.1416 CARRO=... MAPA=... bash nav2_mapa_guardado.sh
#         (salida del vehiculo en el mapa; POSE_YAW en radianes, 0 por defecto)
#     ESCALA=1.0 CARRO=... MAPA=... bash nav2_mapa_guardado.sh   (escala del puente; por defecto, la de cada vehiculo: racey 0.9, deepy 0.85; ESCALA_REVERSA=, solo marcha atras: 0.75 en los dos)
#     MARGEN=0.5 CARRO=... MAPA=... bash nav2_mapa_guardado.sh   (margen de llegada de Nav2; 1.0 por defecto)
#     IMU=true CARRO=... MAPA=... bash nav2_mapa_guardado.sh
#
# Desde el 2026-10-07 cada arranque deja, ademas, un registro de la carga de la
# tarjeta en /home/deepracer/carga_<fecha>_<hora>.csv (ruta fija del vehiculo; registrar_carga.py, una
# fila cada 5 s); --parar lo cierra. Se resume con
#     python3 herramientas/registrar_carga.py --resumen <csv>
#         (IMU de la tarjeta + EKF, imu:=true en el lanzador; false por defecto.
#          El vehiculo no se toca durante el arranque: el nodo mide el sesgo del
#          giroscopio. El paso 6 comprueba que imu/data y odom publiquen)
#
# Antes de arrancar para los procesos de la pila de AWS que el proyecto no usa
# (AWS_SOBRANTES): con la camara y la fusion encendidas la tarjeta llego a carga
# 22 y el gestor desactivo Nav2 (amss-jgm9, 2-oct), y sin los doce de la lista la
# tarjeta pasa del 21-34 % al 8-10 % en reposo (2026-10-07).
#
# Si se cambia la IP del vehiculo despues de encenderlo, hay que reiniciar su
# pila ('sudo systemctl restart deepracer-core'): sus nodos siguen anunciandose
# con la IP vieja, se descubren pero no entregan datos, y el paso 1 lo detecta
# como «el laser NO publica» (amss-ez9n, 2026-10-07).
#     bash nav2_mapa_guardado.sh --estado
#     bash nav2_mapa_guardado.sh --parar
#
# REQUISITO: clave SSH instalada (ssh-copy-id deepracer@<IP>).

set -uo pipefail

CARRO="${CARRO:-192.168.0.102}"
USUARIO=deepracer
# Rutas del VEHICULO, no del portatil: van absolutas porque la tilde no se
# expande dentro de 'urdf:=~deepracer/...' (solo al principio de palabra).
D=/home/deepracer/tesis   # ruta fija del vehiculo
MAPA="${MAPA:-/home/deepracer/mapeo_235028/mapa.yaml}"   # ruta fija del vehiculo
POSE_X="${POSE_X:-1.0}"
POSE_Y="${POSE_Y:-0.0}"
# Escala del puente de cada vehiculo (RF-14). Con Nav2 navegando a 0,50 m/s, la
# velocidad real depende solo de ella. Se calibra en el pasillo midiendo el avance
# con flexometro y el tiempo de Nav2 de cada tramo. ESCALA= la anula.
# ESCALA_REVERSA multiplica el acelerador solo en marcha atras: con la misma orden
# el motor retrocede mas rapido de lo que avanza (parametro escala_reversa del
# puente). ESCALA_REVERSA= la anula.
case "$CARRO" in
  192.168.0.104) ESCALA_VEHICULO=0.9; REVERSA_VEHICULO=0.75 ;;   # amss-jgm9 (racey): con 1,0 iba a ~1,2 m/s y se paso de la meta; en reversa, 1,1-1,7 m/s con escala_reversa 1,0 (7-oct)
  192.168.0.102) ESCALA_VEHICULO=0.85; REVERSA_VEHICULO=0.75 ;;  # amss-ez9n (deepy): con 0,9 llego a 1,58 m/s (2-oct); reversa sin medir, la misma de racey (decision del 8-oct)
  *)             ESCALA_VEHICULO=0.9; REVERSA_VEHICULO=1.0 ;;
esac
ESCALA="${ESCALA:-$ESCALA_VEHICULO}"
ESCALA_REVERSA="${ESCALA_REVERSA:-$REVERSA_VEHICULO}"
IMU="${IMU:-false}"
MARGEN="${MARGEN:-1.0}"
# Rumbo de la salida en radianes (3.1416 = mirando hacia -x). Va en la pose
# inicial como cuaternion; sin el, AMCL arranca mirando a +x.
POSE_YAW="${POSE_YAW:-0.0}"
QZ=$(awk -v a="$POSE_YAW" 'BEGIN{printf "%.6f", sin(a/2)}')
QW=$(awk -v a="$POSE_YAW" 'BEGIN{printf "%.6f", cos(a/2)}')
LOGS=/tmp/nav2_campo
# Procesos de AWS que se paran al arrancar (ver el paso 0 de arrancar()).
AWS_SOBRANTES="camera_node sensor_fusion_n web_video_serve inference_node model_optimizer model_loader_no software_update bag_log_node_cp device_info_nod device_status_n usb_monitor_nod deepracer_navig status_led_node"

# Espacio de nombres (bloque C de Documentos/PLAN_S25.md). Vacio, que es el valor
# por defecto, deja cada orden exactamente como antes: los tres prefijos de abajo
# se reducen a la cadena vacia. Con NS=robot2 todo cuelga de /robot2 y los marcos
# propios llevan 'robot2/'; el lanzador hace lo mismo con 'namespace:=robot2'.
NS="${NS:-}"
NS="${NS#/}"
P="${NS:+/$NS}"                          # prefijo de topicos y servicios: /robot2
F="${NS:+$NS/}"                          # prefijo de marcos: robot2/
ARGS_NS="${NS:+-r __ns:=/$NS}"           # para 'ros2 run'

# Los tres 'source' que hacen falta, en una sola cadena reutilizable.
# La particion del vehiculo, si esta instalada: sin ella, tras aplicar
# Documentos/DISENO_AISLAMIENTO_DOS_CARROS.md, nada de lo que se lanza ve el laser
# ni llega a los servos. Si no esta, no hace nada.
FUENTES='[ -f /etc/deepracer-tesis/particion.xml ] && export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash && source /home/deepracer/nav_ws/install/setup.bash'   # ruta fija del vehiculo
FUENTES_PUENTE='[ -f /etc/deepracer-tesis/particion.xml ] && export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash && source /home/deepracer/coordinacion_ws/install/setup.bash'   # ruta fija del vehiculo

rojo()  { printf '\033[31m%s\033[0m\n' "$*"; }
verde() { printf '\033[32m%s\033[0m\n' "$*"; }
info()  { printf '\033[36m==\033[0m %s\n' "$*"; }

# Ejecuta una orden en el carro, como root y con ROS cargado.
en_carro() {
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$USUARIO@$CARRO" "sudo -n bash -s" <<< "$1" 2>&1
}

# Lanza algo en segundo plano en el carro, que sobreviva al cierre del ssh.
lanzar_en_carro() {
  local nombre="$1" orden="$2"
  ssh -o BatchMode=yes "$USUARIO@$CARRO" "sudo -n bash -s" <<ORDEN >/dev/null 2>&1
mkdir -p $LOGS
setsid nohup bash -c '$orden' > $LOGS/$nombre.log 2>&1 < /dev/null &
ORDEN
}

comprobar_acceso() {
  if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "$USUARIO@$CARRO" true 2>/dev/null; then
    rojo "No hay acceso sin contrasena a $USUARIO@$CARRO."
    echo "   Instala la clave una sola vez:"
    echo "     ssh-keygen -t ed25519 -N \"\" -f ~/.ssh/id_ed25519 2>/dev/null; ssh-copy-id $USUARIO@$CARRO"
    exit 1
  fi
}

# ---------------------------------------------------------------- estado ---
estado() {
  info "procesos en el carro"
  en_carro "ps -eo user,pid,cmd | grep -E '[c]mdvel_to_servo|[r]f2o|[s]lam_toolbox|[c]ontroller_server|[p]lanner_server|[r]obot_state_publisher|[e]kf_node|[i]mu_bmi160' || echo '  (nada vivo)'"
  echo
  info "quien escucha $P/cmd_vel"
  en_carro "$FUENTES && timeout 15 ros2 topic info $P/cmd_vel --verbose 2>/dev/null | grep -E 'Publisher count|Subscription count' || echo '  (sin respuesta)'"
  echo
  info "estado de slam_toolbox"
  en_carro "$FUENTES && timeout 15 ros2 service call $P/slam_toolbox/get_state lifecycle_msgs/srv/GetState \"{}\" 2>/dev/null | tail -2 || echo '  (sin respuesta)'"
}

# ----------------------------------------------------------------- parar ---
parar() {
  info "matando la cadena"
  # Por nombre de ejecutable, NUNCA con 'pkill -f' sobre el patron completo:
  # el patron coincide tambien con la propia linea de sudo y se mata a si mismo.
  en_carro "for p in cmdvel_to_serv rf2o_laser_odom sync_slam_toolb robot_state_pub controller_serv planner_server bt_navigator behavior_server waypoint_follow lifecycle_manag map_server amcl ekf_node; do pkill -9 \$p 2>/dev/null; done; pkill -9 -f nav2_hardware.launch 2>/dev/null; pkill -9 -f imu_bmi160.py 2>/dev/null; pkill -f registrar_carga.py 2>/dev/null; true"
  sleep 2
  verde "listo. Comprueba con: bash $0 --estado"
}

# --------------------------------------------------------------- arrancar ---
# Enciende una pieza de ciclo de vida: la lanza, la configura (1) y la activa (3).
encender_lifecycle() {
  local nodo="$1" orden="$2"
  lanzar_en_carro "$nodo" "$orden"
  sleep 8
  en_carro "$FUENTES && timeout 20 ros2 service call $P/$nodo/change_state lifecycle_msgs/srv/ChangeState \"{transition: {id: 1}}\"" >/dev/null
  sleep 3
  en_carro "$FUENTES && timeout 20 ros2 service call $P/$nodo/change_state lifecycle_msgs/srv/ChangeState \"{transition: {id: 3}}\"" >/dev/null
  sleep 3
  local e
  e=$(en_carro "$FUENTES && timeout 20 ros2 service call $P/$nodo/get_state lifecycle_msgs/srv/GetState \"{}\" 2>/dev/null | tail -2")
  if echo "$e" | grep -q "id=3"; then verde "   $nodo ACTIVO"; return 0
  else rojo "   $nodo NO quedo activo. Mira $LOGS/$nodo.log"; echo "$e"; return 1; fi
}

arrancar() {
  info "0/6 · limpiando restos"
  en_carro "for p in cmdvel_to_serv rf2o_laser_odom sync_slam_toolb robot_state_pub controller_serv planner_server bt_navigator behavior_server waypoint_follow lifecycle_manag map_server amcl ekf_node; do pkill -9 \$p 2>/dev/null; done; pkill -9 -f nav2_hardware.launch 2>/dev/null; pkill -9 -f imu_bmi160.py 2>/dev/null; pkill -f registrar_carga.py 2>/dev/null; true" >/dev/null
  # Procesos de la pila de AWS que el proyecto no usa, fuera: cargan la tarjeta.
  # Por nombre de proceso (15 caracteres), nunca con 'pkill -f'. Medido el
  # 2026-10-07 en los dos vehiculos, sin nada nuestro corriendo: la tarjeta pasa
  # del 21-34 % al 8-10 % y la memoria de 1060 a 680 MB. Se quedan los que si se
  # usan o sirven para recuperar el vehiculo: rplidar_node, servo_node,
  # ctrl_node, battery_node, otg_control_nod (red por USB), network_monitor,
  # deepracer_syste y webserver_publi (la consola web). Vuelven todos al
  # reiniciar el vehiculo o con 'sudo systemctl restart deepracer-core'.
  en_carro "for p in $AWS_SOBRANTES; do pkill -x \$p; done; true" >/dev/null
  sleep 3

  info "1/6 · el laser publica?"
  local scan
  # 'average rate' sale en la linea 1 o en la 2, segun 'hz' imprima antes o no el
  # aviso «does not appear to be published yet». Tomar siempre la linea 2 aborto
  # con el laser a 9,9 Hz (amss-jgm9, 2026-09-29).
  scan=$(en_carro "$FUENTES && timeout 20 ros2 topic hz /rplidar_ros/scan 2>/dev/null | head -4 | grep -m1 'average rate'")
  if echo "$scan" | grep -q "average rate"; then verde "   $scan"
  else rojo "   el laser NO publica. sudo systemctl restart deepracer-core, espera 30 s"; exit 1; fi

  info "2/6 · el puente (el launch NO lo arranca)"
  # La suscripcion del puente es absoluta ('/cmd_vel'): el espacio de nombres no
  # la alcanza, y sin el remapeo los dos puentes escucharian el mismo topico.
  lanzar_en_carro puente "$FUENTES_PUENTE && ros2 run cmdvel_to_servo_pkg cmdvel_to_servo_node --ros-args -p escala_reversa:=$ESCALA_REVERSA${NS:+ $ARGS_NS -r /cmd_vel:=$P/cmd_vel}"
  sleep 6
  local esc
  esc=$(en_carro "$FUENTES_PUENTE && timeout 20 ros2 service call $P/set_max_speed deepracer_interfaces_pkg/srv/NavThrottleSrv \"{throttle: $ESCALA}\" 2>/dev/null | tail -2")
  echo "$esc" | grep -q "error=0" && verde "   escala $ESCALA puesta" || rojo "   la escala NO se puso; el carro no arrancara"

  info "3/6 · map_server con $MAPA (use_sim_time=false)"
  en_carro "test -f $MAPA" >/dev/null 2>&1 || { rojo "   el mapa no existe en el carro: $MAPA"; exit 1; }
  encender_lifecycle map_server "$FUENTES && ros2 run nav2_map_server map_server --ros-args${ARGS_NS:+ $ARGS_NS} -p use_sim_time:=false -p yaml_filename:=$MAPA -p frame_id:=${F}map" || exit 1

  info "4/6 · amcl (use_sim_time=false, scan_topic=/rplidar_ros/scan)"
  local params_amcl=$D/nav2_params_jazzy.yaml marcos_amcl=""
  if [ -n "$NS" ]; then
    # El YAML tiene claves sueltas ('amcl:') que solo casan con el nodo '/amcl'.
    # Bajo /robot2 hay que anidarlo, como hace 'root_key' en el lanzador.
    params_amcl=$LOGS/nav2_params_$NS.yaml
    # Se comprueba que el archivo quedo escrito: el 2026-10-08 esta orden no se
    # ejecuto en amss-jgm9 y AMCL murio con «Couldn't parse params file», sin que
    # el guion dijera por que.
    en_carro "mkdir -p $LOGS && python3 -c \"import yaml; d = yaml.safe_load(open('$D/nav2_params_jazzy.yaml')); yaml.safe_dump({'$NS': d}, open('$params_amcl', 'w'))\" && test -s $params_amcl" >/dev/null \
      || { rojo "   no se pudo escribir $params_amcl en el carro (¿se corto el ssh?); vuelve a lanzar el guion"; exit 1; }
    marcos_amcl="-p base_frame_id:=${F}base_link -p odom_frame_id:=${F}odom -p global_frame_id:=${F}map"
  fi
  encender_lifecycle amcl "$FUENTES && ros2 run nav2_amcl amcl --ros-args${ARGS_NS:+ $ARGS_NS} --params-file $params_amcl -p use_sim_time:=false -p scan_topic:=/rplidar_ros/scan${marcos_amcl:+ $marcos_amcl}" || exit 1

  info "5/6 · el launch, AHORA que /map ya esta activo (imu:=$IMU, margen $MARGEN m)"
  # Registro de carga de toda la sesion (2026-10-07): la tarjeta de dos nucleos es
  # el limite conocido, y htop solo muestra el momento.
  local carga=/home/deepracer/carga_$(date +%Y%m%d_%H%M%S).csv   # ruta fija del vehiculo
  lanzar_en_carro carga "python3 $D/registrar_carga.py $carga --cada 5"
  echo "   registrando la carga de la tarjeta en $carga"
  [ "$IMU" = true ] && echo "   no toque el vehiculo: la IMU mide el sesgo del giroscopio al arrancar"
  lanzar_en_carro launch "$FUENTES && ros2 launch $D/nav2_hardware.launch.py slam:=false nav:=true urdf:=$D/deepracer_hardware.urdf params:=$D/nav2_params_jazzy.yaml slam_params:=$D/slam_toolbox.yaml behavior_trees:=$D/behavior_trees imu:=$IMU margen_llegada:=$MARGEN${NS:+ namespace:=$NS}"
  echo "   esperando 55 s a que configuren los costmaps..."
  sleep 55

  info "6/6 · pose inicial en ($POSE_X, $POSE_Y, rumbo $POSE_YAW rad) y comprobaciones"
  en_carro "$FUENTES && timeout 15 ros2 topic pub --once $P/initialpose geometry_msgs/msg/PoseWithCovarianceStamped \"{header: {frame_id: ${F}map}, pose: {pose: {position: {x: $POSE_X, y: $POSE_Y, z: 0.0}, orientation: {z: $QZ, w: $QW}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.07]}}\"" >/dev/null
  sleep 4
  for n in map_server amcl planner_server controller_server bt_navigator behavior_server; do
    # 25 s y no 8: con la tarjeta recien arrancada la llamada tarda, y con 8 salia
    # vacio el estado de los seis (2026-10-07).
    printf "   %-20s %s\n" "$n" "$(en_carro "$FUENTES && timeout 25 ros2 service call $P/$n/get_state lifecycle_msgs/srv/GetState \"{}\" 2>/dev/null | grep -o \"label='[a-z]*'\" | tail -1")"
  done
  local subs
  subs=$(en_carro "$FUENTES && timeout 20 ros2 topic info $P/cmd_vel 2>/dev/null | grep -c 'Subscription count: 1'")
  [ "${subs:-0}" -ge 1 ] && verde "   alguien escucha $P/cmd_vel" || rojo "   NADIE escucha $P/cmd_vel"
  if [ "$IMU" = true ]; then
    # Sin imu/data el EKF no gira el rumbo, y sin odom_rf2o no avanza; ninguno de
    # los dos da error. Se mide con medir_odom_imu.py y no con 'ros2 topic hz': con
    # la tarjeta recien arrancada, 'hz' no llegaba a descubrir el topico en 15 s y
    # daba «NO publica» con los dos publicando (2026-10-07).
    local med
    med=$(en_carro "$FUENTES && python3 $D/medir_odom_imu.py 8 ${NS:+--ns $NS} 2>&1 | grep -E 'Hz|ABORTA|sin datos' | cut -c1-80")
    echo "$med" | sed 's/^/   /'
    if echo "$med" | grep -qE 'ABORTA|sin datos|imu/data: 0\.0 Hz'; then
      rojo "   la IMU, rf2o o el filtro NO publican: mira $LOGS/launch.log (imu_bmi160, rf2o, ekf_filter_node)"
    else verde "   IMU, rf2o y filtro publicando"; fi
  fi

  echo
  verde "=================== CADENA LISTA ==================="
  cat <<AYUDA

  PRUEBA EL PLAN SIN MOVER EL CARRO (esto es lo que ahorra la tarde):
    ssh $USUARIO@$CARRO "sudo -n bash -c '$FUENTES && ros2 action send_goal $P/compute_path_to_pose nav2_msgs/action/ComputePathToPose \"{goal: {header: {frame_id: ${F}map}, pose: {position: {x: 6.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}, use_start: false}\"'"

  SUCCEEDED = el planificador puede. ABORTED = mira el log del planner_server:
    ssh $USUARIO@$CARRO "sudo -n grep planner_server $LOGS/launch.log | tail -5"
  "Start occupied" = la salida cae en celda no libre: mueve el carro o corrige la pose.

  GRABA, y despues manda la meta:
    ssh $USUARIO@$CARRO "sudo -n bash -c '$FUENTES && cd ~deepracer && timeout -s INT 150 ros2 bag record -s mcap -o nav2_usta_01 /rplidar_ros/scan $P/odom $P/cmd_vel /tf /tf_static $P/plan $P/map $P/amcl_pose; chown -R deepracer:deepracer ~deepracer/nav2_usta_01'"

  LA META (el script NO la manda: la mandas tu mirando el carro):
    ssh $USUARIO@$CARRO "sudo -n bash -c '$FUENTES && ros2 action send_goal --feedback $P/navigate_to_pose nav2_msgs/action/NavigateToPose \"{pose: {header: {frame_id: ${F}map}, pose: {position: {x: 6.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}\"'"

  PARADA DE EMERGENCIA (el carro deja de recibir traccion):
    ssh $USUARIO@$CARRO "sudo -n pkill -9 cmdvel_to_serv"

  El carro VA A SOBREPASAR la meta ~0.4 m. Esta explicado y medido: la banda
  muerta obliga a aproximarse a 0.40 m/s. Anota el error, no lo ajustes.

AYUDA
}

case "${1:-}" in
  --parar)  comprobar_acceso; parar ;;
  --estado) comprobar_acceso; estado ;;
  "")       comprobar_acceso; arrancar ;;
  *)        echo "uso: $0 [--parar|--estado]"; exit 1 ;;
esac
