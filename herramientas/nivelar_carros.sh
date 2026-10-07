#!/usr/bin/env bash
# Compara y nivela los dos vehiculos contra el repositorio, en una sola orden.
#
# POR QUE EXISTE
# --------------
# La regla del proyecto es que los dos vehiculos se tocan a la vez: lo que se
# instala en uno se instala en el otro el mismo dia (CLAUDE.md). Hasta ahora la
# comprobacion se hacia a mano, archivo por archivo, y el 2-oct `amss-ez9n` tenia
# cinco archivos distintos del repositorio sin que nadie lo hubiera visto.
#
# QUE HACE
# --------
#   nivelar_carros.sh            compara (no toca nada)
#   nivelar_carros.sh --copiar   compara, copia lo que falte o difiera y vuelve a comparar
#   nivelar_carros.sh --imu      lee el registro 0 del BMI160 (bus I2C 1, 0x68):
#                                0xd1 si la tarjeta tiene la IMU. No instala nada
#
# Compara, en cada vehiculo, los archivos de ~/tesis que usan los guiones de
# campo (lista ARCHIVOS, abajo), el codigo del coordinador y del agente en
# ~/coordinacion_ws/src (todo lo que git sigue de coordinacion y
# coordinacion_msgs; con --copiar se copia y se recompila), el fuente de rf2o con el parche del proyecto
# (herramientas/parches/LEEME.md) y la particion instalada en /etc contra la del
# repositorio, y si las camaras estan desactivadas por la regla de udev
# config/90-tesis-camaras-desactivadas.rules (conectadas, sin /dev/video). La
# particion, el parche y la regla solo se informan: se instalan con su propio
# procedimiento (DISENO_AISLAMIENTO_DOS_CARROS.md, parches/LEEME.md y la §1.3 de
# PLAN_S26.md).
#
# Los vehiculos se toman de CARROS, «IP:nombre» separados por espacios; el
# nombre se comprueba contra 'hostname' antes de tocar nada.
#
# USO
#     herramientas/nivelar_carros.sh [--copiar | --imu]
#     CARROS="192.168.0.102:amss-ez9n" herramientas/nivelar_carros.sh --copiar

set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CARROS="${CARROS:-192.168.0.102:amss-ez9n 192.168.0.104:amss-jgm9}"
MODO="${1:-comprobar}"
MD5_RF2O_PARCHE=06cbdbe6c275
B=Robot/aws-deepracer/deepracer_bringup

# Archivo del repositorio -> nombre en ~/tesis del vehiculo.
ARCHIVOS=(
  "$B/launch/nav2_hardware.launch.py"
  "$B/config/nav2_params_jazzy.yaml"
  "$B/config/slam_toolbox.yaml"
  "$B/config/slam_toolbox_carro.yaml"
  "$B/config/puntos_interes_pisos34.yaml"
  "Robot/aws-deepracer/deepracer_description/models/urdf/deepracer_hardware.urdf"
  "$B/behavior_trees/ackermann_navigate_to_pose.xml"
  "$B/behavior_trees/ackermann_navigate_through_poses.xml"
  "$B/maps/piso3.yaml" "$B/maps/piso3.pgm"
  "$B/maps/piso4.yaml" "$B/maps/piso4.pgm"
  "$B/maps/mundo_definitivo_piso2.yaml" "$B/maps/mundo_definitivo_piso2.pgm"
  "herramientas/corrida_nav2.py"
  "herramientas/correr_corrida_nav2.sh"
  "herramientas/grabar_mision_vehiculo.sh"
  "herramientas/lanzar_bag.inc"
  "herramientas/zona_libre_mapa.py"
  "herramientas/mapear_conduciendo.sh"
  "herramientas/avanzar_y_detener.py"
  "herramientas/extraer_mapa.py"
  "herramientas/probar_imu.py"
  "herramientas/medir_odom_imu.py"
  "herramientas/registrar_carga.py"
  "$B/scripts/imu_bmi160.py"
)

# Coordinador y agente: corren desde ~/coordinacion_ws del vehiculo, compilado
# con --symlink-install. Hasta el 2026-10-05 nadie lo comparaba, y los dos
# vehiculos tenian el coordinador del 13-sep, sin la tolerancia de llegada del
# 28-sep.
mapfile -t COORD < <(git -C "$REPO" ls-files Robot/aws-deepracer/coordinacion Robot/aws-deepracer/coordinacion_msgs)
destino_coord() { echo "${1#Robot/aws-deepracer/}"; }

# Ruta dentro de ~/tesis: los arboles van en su carpeta, el resto suelto.
destino() {
  case "$1" in
    */behavior_trees/*) echo "behavior_trees/$(basename "$1")" ;;
    *) basename "$1" ;;
  esac
}

verde() { printf '\033[32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[31m%s\033[0m\n' "$*"; }

en_carro() {
  ssh -o BatchMode=yes -o ConnectTimeout=10 "deepracer@$1" "$2" 2>/dev/null
}

comparar() {
  local ip="$1" nombre="$2" remoto lista distintos=0 f d esperado actual
  lista=""
  for f in "${ARCHIVOS[@]}"; do lista+=" ~/tesis/$(destino "$f")"; done
  remoto=$(en_carro "$ip" "md5sum $lista 2>/dev/null; echo RF2O \$(md5sum ~/nav_ws/src/rf2o_laser_odometry/src/CLaserOdometry2DNode.cpp 2>/dev/null | cut -c1-12); echo PART \$(sudo -n md5sum /etc/deepracer-tesis/particion.xml 2>/dev/null | cut -c1-32); echo CAMS \$(md5sum /etc/udev/rules.d/90-tesis-camaras-desactivadas.rules 2>/dev/null | cut -c1-32) \$(ls /dev/video* 2>/dev/null | wc -l); echo AWSENV \$(grep -c opt/aws/deepracer/lib ~/coordinacion_ws/install/setup.bash 2>/dev/null)")
  FALTAN=()
  for f in "${ARCHIVOS[@]}"; do
    d=$(destino "$f")
    esperado=$(md5sum "$REPO/$f" | cut -d' ' -f1)
    # md5sum escribe la ruta ya expandida en el vehiculo: se compara lo que va tras 'tesis/'.
    actual=$(echo "$remoto" | awk -v d="$d" '{r = $2; sub(/.*\/tesis\//, "", r)} r == d {print $1; exit}')
    if [ "$actual" != "$esperado" ]; then
      distintos=$((distintos + 1))
      FALTAN+=("$f")
      if [ -z "$actual" ]; then rojo "   falta      $d"; else rojo "   distinto   $d"; fi
    fi
  done
  [ "$distintos" -eq 0 ] && verde "   ~/tesis: los ${#ARCHIVOS[@]} archivos iguales al repositorio"
  # Coordinador y agente.
  lista=""
  for f in "${COORD[@]}"; do lista+=" ~/coordinacion_ws/src/$(destino_coord "$f")"; done
  remoto_c=$(en_carro "$ip" "md5sum $lista 2>/dev/null")
  FALTAN_C=()
  for f in "${COORD[@]}"; do
    d=$(destino_coord "$f")
    esperado=$(md5sum "$REPO/$f" | cut -d' ' -f1)
    actual=$(echo "$remoto_c" | awk -v d="$d" '{r = $2; sub(/.*\/coordinacion_ws\/src\//, "", r)} r == d {print $1; exit}')
    if [ "$actual" != "$esperado" ]; then
      FALTAN_C+=("$f")
      if [ -z "$actual" ]; then rojo "   falta      coordinacion_ws/src/$d"; else rojo "   distinto   coordinacion_ws/src/$d"; fi
    fi
  done
  distintos=$((distintos + ${#FALTAN_C[@]}))
  [ "${#FALTAN_C[@]}" -eq 0 ] && verde "   coordinacion_ws: los ${#COORD[@]} archivos del coordinador y del agente iguales al repositorio"
  actual=$(echo "$remoto" | awk '$1 == "RF2O" {print $2}')
  if [ "$actual" = "$MD5_RF2O_PARCHE" ]; then verde "   rf2o: con el parche"
  else rojo "   rf2o: SIN el parche (md5 ${actual:-desconocido}); ver herramientas/parches/LEEME.md"; AVISOS=$((AVISOS + 1)); fi
  esperado=$(md5sum "$REPO/$B/config/particion_$nombre.xml" | cut -d' ' -f1)
  actual=$(echo "$remoto" | awk '$1 == "PART" {print $2}')
  if [ "$actual" = "$esperado" ]; then verde "   particion en /etc: igual a particion_$nombre.xml"
  else rojo "   particion en /etc: DISTINTA de particion_$nombre.xml (${actual:-no se pudo leer})"; AVISOS=$((AVISOS + 1)); fi
  # Camaras conectadas pero desactivadas por la regla de udev del repositorio.
  esperado=$(md5sum "$REPO/$B/config/90-tesis-camaras-desactivadas.rules" | cut -d' ' -f1)
  actual=$(echo "$remoto" | awk '$1 == "CAMS" {print $2, $3}')
  if [ "$actual" = "$esperado 0" ]; then verde "   camaras: desactivadas por la regla de udev (ningun /dev/video)"
  else rojo "   camaras: regla de udev ausente o distinta, o hay /dev/video (${actual:-no se pudo leer})"; AVISOS=$((AVISOS + 1)); fi
  # El workspace del puente tiene que encadenar el entorno de AWS (ver copiar()).
  actual=$(echo "$remoto" | awk '$1 == "AWSENV" {print $2}')
  if [ "${actual:-0}" -ge 1 ]; then verde "   coordinacion_ws: encadena el entorno de AWS (el puente encuentra sus mensajes)"
  else rojo "   coordinacion_ws: NO encadena /opt/aws/deepracer/lib; el puente no arranca. Recompilar con: source /opt/aws/deepracer/lib/setup.bash"; AVISOS=$((AVISOS + 1)); fi
  return "$distintos"
}

copiar() {
  local ip="$1" f d paquetes
  if [ "${#FALTAN[@]}" -gt 0 ]; then
    en_carro "$ip" "mkdir -p ~/tesis/behavior_trees"
    for f in "${FALTAN[@]}"; do
      scp -q -o BatchMode=yes -o ConnectTimeout=10 "$REPO/$f" "deepracer@$ip:~/tesis/$(destino "$f")" \
        && echo "   copiado    $(destino "$f")" || rojo "   NO se copio $(destino "$f")"
    done
  fi
  [ "${#FALTAN_C[@]}" -eq 0 ] && return 0
  for f in "${FALTAN_C[@]}"; do
    d=$(destino_coord "$f")
    en_carro "$ip" "mkdir -p ~/coordinacion_ws/src/$(dirname "$d")"
    scp -q -o BatchMode=yes -o ConnectTimeout=10 "$REPO/$f" "deepracer@$ip:~/coordinacion_ws/src/$d" \
      && echo "   copiado    coordinacion_ws/src/$d" || rojo "   NO se copio coordinacion_ws/src/$d"
  done
  # Con --symlink-install el Python ya queda al dia; los mensajes y el setup.py
  # necesitan compilar. Se compila siempre: es un minuto y evita adivinar.
  paquetes="coordinacion"
  printf '%s\n' "${FALTAN_C[@]}" | grep -q 'coordinacion_msgs/' && paquetes="coordinacion_msgs coordinacion"
  echo "   compilando $paquetes en el vehiculo..."
  # Con el entorno de AWS, no solo el de ROS: el puente (cmdvel_to_servo_pkg) usa
  # los mensajes de deepracer_interfaces_pkg, que viven en /opt/aws/deepracer/lib,
  # y colcon reescribe install/setup.bash con los entornos cargados al compilar.
  # Compilado solo con /opt/ros/jazzy, el puente moria con «No module named
  # 'deepracer_interfaces_pkg'» y el vehiculo no se movia (2026-10-07).
  en_carro "$ip" "cd ~/coordinacion_ws && source /opt/aws/deepracer/lib/setup.bash && colcon build --symlink-install --packages-select $paquetes 2>&1 | tail -1"
}

imu() {
  local ip="$1" r
  # Escribe la direccion de registro 0 y lee un byte: en el BMI160 es su chip id.
  # 0x0703 es I2C_SLAVE; si otro programa usa el bus, se reintenta con
  # I2C_SLAVE_FORCE (0x0706).
  r=$(en_carro "$ip" "ls /dev/i2c-* 2>/dev/null | tr '\n' ' '; echo; for op in 0x0703 0x0706; do sudo -n python3 -c \"import fcntl,os; f=os.open('/dev/i2c-1',os.O_RDWR); fcntl.ioctl(f,\$op,0x68); os.write(f,bytes([0])); print(hex(os.read(f,1)[0]))\" 2>&1 && break; done")
  echo "   buses: $(echo "$r" | head -1)"
  if echo "$r" | grep -q '^0xd1$'; then verde "   IMU: el registro 0 en 0x68 vale 0xd1 (BMI160)"
  else rojo "   IMU: no responde 0xd1 en el bus 1, direccion 0x68: $(echo "$r" | tail -1)"; fi
}

total=0
AVISOS=0
for c in $CARROS; do
  ip="${c%%:*}"; nombre="${c#*:}"
  echo "== $nombre ($ip)"
  real=$(en_carro "$ip" hostname)
  if [ -z "$real" ]; then rojo "   no responde: queda PENDIENTE (la regla es tocar los dos el mismo dia)"; total=$((total + 1)); continue; fi
  if [ "$real" != "$nombre" ]; then rojo "   en $ip esta '$real', no '$nombre': no se toca"; total=$((total + 1)); continue; fi
  case "$MODO" in
    --imu) imu "$ip" ;;
    --copiar)
      comparar "$ip" "$nombre" >/dev/null
      AVISOS=0
      copiar "$ip"
      comparar "$ip" "$nombre" || total=$((total + 1)) ;;
    *) comparar "$ip" "$nombre" || total=$((total + 1)) ;;
  esac
done
[ "$MODO" = "--imu" ] && exit 0
echo
if [ "$total" -eq 0 ] && [ "$AVISOS" -eq 0 ]; then verde "Los vehiculos estan nivelados con el repositorio."
elif [ "$total" -eq 0 ]; then rojo "~/tesis esta nivelado, pero hay $AVISOS aviso(s) de rf2o o de la particion: ver arriba."
else rojo "Hay $total vehiculo(s) con diferencias en ~/tesis o sin respuesta."; fi
exit $((total + AVISOS))
