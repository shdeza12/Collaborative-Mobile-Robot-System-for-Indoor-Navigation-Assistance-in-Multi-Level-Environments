#!/bin/bash
# Graba una mision coordinada en el VEHICULO que lleva el coordinador (racey).
#
# USO (en el vehiculo, como root, antes de pedir la mision desde la interfaz)
#     ssh -t deepracer@192.168.0.104 "sudo -n bash /home/deepracer/tesis/grabar_mision_vehiculo.sh G5_01"   # ruta fija del vehiculo
#
# Se pulsa Enter cuando la mision termina (completada, fallida o cancelada), o
# Ctrl-C, que tambien cierra la grabacion. Queda en ~deepracer/mision_<nombre>/,
# y se copia al portatil con:
#     scp -r deepracer@192.168.0.104:mision_G5_01 ~/tesis_evidencia/
# Se compone con herramientas/adaptar_bag_jazzy.py y despues
# herramientas/componer_registro.py --banco fisico --catalogo ... (§4.3 de
# Documentos/PLAN_S26.md).
#
# POR QUE NO grabar_mision.sh
# ---------------------------
# Aquel es de la simulacion: exige /clock, que en el vehiculo no existe, y graba
# el reloj de cada gzserver. Aqui todo va con el reloj del vehiculo.
#
# POR QUE EN EL VEHICULO DEL COORDINADOR
# --------------------------------------
# Las marcas de la mision salen del instante en que se graba cada mensaje, y
# las tarjetas no tienen la hora sincronizada entre si. Grabando todo en una
# sola maquina, la del coordinador, todas las marcas comparten reloj. Los
# topicos del otro vehiculo llegan por la particion comun. La /tf y el laser son
# privados de cada vehiculo (Documentos/DISENO_AISLAMIENTO_DOS_CARROS.md): aqui
# solo entran los de este, y la pose en el mapa de los dos va en /robotN/estado.
#
# LA LISTA ES FIJA, por la misma razon que en grabar_mision.sh: si cada mision
# graba lo que le parece, las misiones no se pueden comparar.

AQUI="$(cd "$(dirname "$0")" && pwd)"

if [ $# -ne 1 ]; then
    sed -n '/^# USO/,/^# POR QUE NO/p' "$0" | sed '$d' | sed 's/^# \?//'
    exit 2
fi

NOMBRE="$1"
DESTINO=~deepracer/mision_$NOMBRE
if [ -e "$DESTINO" ]; then
    echo "ABORTA: ya existe $DESTINO. Una grabacion por mision, con nombre distinto."
    exit 2
fi

source /opt/ros/jazzy/setup.bash
# Descubrimiento normal, por la red (2026-10-08): graba lo de deepy (/robot1/...),
# como el coordinador. Lo interno de cada vehiculo se descubre solo dentro de el.
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
# Sin el workspace del coordinador, 'ros2 bag record' no conoce EstadoMision ni
# EstadoRobot y no los graba: justo los topicos de los que salen las marcas.
source ~deepracer/coordinacion_ws/install/setup.bash
source "$AQUI/lanzar_bag.inc"     # carga tambien la particion del vehiculo

TOPICOS=(/coordinacion/estado_mision /coordinacion/puntos_interes
         /coordinacion/confirmacion_piso /tf /tf_static)
for NS in robot1 robot2; do
    TOPICOS+=("/$NS/odom" "/$NS/estado" "/$NS/amcl_pose" "/$NS/cmd_vel" "/$NS/plan"
              "/$NS/imu/data" "/$NS/odom_rf2o")
done

# Sin /coordinacion/estado_mision no hay marcas y la mision no se puede componer.
# 'ros2 topic list' tambien lista topicos que solo tienen suscriptores, asi que
# se exige un publicador.
if ! timeout 15 ros2 topic info /coordinacion/estado_mision 2>/dev/null \
        | grep -q 'Publisher count: [1-9]'; then
    echo "ABORTA: nadie publica /coordinacion/estado_mision. ¿Esta el coordinador vivo?"
    echo "  (paso 4 de la §4.2 de Documentos/PLAN_S26.md)"
    exit 1
fi

arrancar_bag "$DESTINO" "${TOPICOS[@]}"
trap 'echo; echo "cerrando la grabacion..."; cerrar_bag; chown -R deepracer:deepracer "$DESTINO"; exit 130' INT TERM HUP
echo "== grabando $DESTINO (${#TOPICOS[@]} topicos)"
echo "   Pida la mision desde la interfaz. Pulse Enter cuando termine."
read -r _
cerrar_bag
trap - INT TERM HUP
chown -R deepracer:deepracer "$DESTINO"
if [ -f "$DESTINO/metadata.yaml" ]; then
    echo "== listo: $DESTINO"
    echo "   Al portatil: scp -r deepracer@$(hostname -I | cut -d' ' -f1):mision_$NOMBRE ~/tesis_evidencia/"
else
    echo "AVISO: $DESTINO no tiene metadata.yaml; mire /tmp/bag.log"
    exit 1
fi
