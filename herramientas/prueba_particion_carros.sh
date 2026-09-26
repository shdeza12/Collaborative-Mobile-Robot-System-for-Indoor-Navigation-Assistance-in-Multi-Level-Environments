#!/bin/bash
# Comprueba que las particiones de los dos vehiculos aislan lo que deben aislar.
#
# USO
#     herramientas/prueba_particion_carros.sh          (en el portatil)
#     bash ~/tesis/prueba_particion_carros.sh          (en un vehiculo, con los dos
#                                                      particion_*.xml al lado)
#
# Corre igual en el portatil (Humble) y en un vehiculo (Jazzy): elige la
# distribucion que haya instalada. En el portatil prueba los ficheros; en el
# vehiculo prueba ademas que el rmw de Jazzy los respeta, que es lo que el
# 2026-09-25 quedo sin comprobar.
#
# QUE COMPRUEBA
# -------------
# Con los dos perfiles del repositorio, particion_amss-ez9n.xml y
# particion_amss-jgm9.xml, para cada topico aislado:
#   mismo vehiculo           -> RECIBE
#   el otro vehiculo         -> no recibe
#   un proceso sin perfil    -> no recibe   (nadie mueve un carro por olvido)
# y, como control, que un topico NO aislado (/robot1/estado) SI cruza de un
# vehiculo al otro: si eso fallara, la particion estaria rompiendo el grafo
# comun que necesitan el coordinador, G-4 y RF-15.
#
# POR QUE NUNCA EN EL DOMINIO 0
# -----------------------------
# El dominio 0 es el de los vehiculos. Publicar alli en /ctrl_pkg/servo_msg
# llega al 'servo_pkg' de verdad. El tipo de prueba es std_msgs/String y no
# coincidiria con ServoCtrlMsg, pero no se apuesta el carro a eso: la prueba se
# niega a correr en el dominio 0 y usa el 87 si no se le dice otro.
#
# Codigo de salida: 0 si todo sale como se espera, 1 si algo no.

# Los perfiles se buscan primero JUNTO A ESTE SCRIPT -en el vehiculo se copian
# los tres ficheros a ~/tesis/ y no hay repositorio- y si no, en el repositorio.
AQUI="$(cd "$(dirname "$0")" && pwd)"
CONF="$(cd "$AQUI/.." && pwd)/Robot/aws-deepracer/deepracer_bringup/config"
[ -f "$AQUI/particion_amss-ez9n.xml" ] && CONF="$AQUI"
A="$CONF/particion_amss-ez9n.xml"
B="$CONF/particion_amss-jgm9.xml"
for p in "$A" "$B"; do
    [ -f "$p" ] || { echo "ABORTA: no encuentro $p"; exit 2; }
done

export ROS_DOMAIN_ID="${DOMINIO_PRUEBA:-87}"
if [ "$ROS_DOMAIN_ID" = "0" ]; then
    echo "ABORTA: dominio 0 es el de los vehiculos. Usa DOMINIO_PRUEBA=<otro>."
    exit 2
fi

set +u
if [ -f /opt/ros/jazzy/setup.bash ]; then source /opt/ros/jazzy/setup.bash
elif [ -f /opt/ros/humble/setup.bash ]; then source /opt/ros/humble/setup.bash
else echo "ABORTA: no hay ROS 2 instalado"; exit 2; fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FALLOS=0

perfil() { case "$1" in A) echo "$A";; B) echo "$B";; *) echo "";; esac; }

topico() {   # topico, perfil suscriptor, perfil publicador, esperado (si|no)
    local top=$1 sub=$2 pub=$3 esp=$4 f="$TMP/eco.txt" r
    rm -f "$f"
    FASTRTPS_DEFAULT_PROFILES_FILE=$(perfil "$sub") timeout 14 \
        ros2 topic echo --once "$top" std_msgs/msg/String > "$f" 2>&1 &
    local E=$!
    sleep 3
    FASTRTPS_DEFAULT_PROFILES_FILE=$(perfil "$pub") timeout 9 \
        ros2 topic pub -r 5 "$top" std_msgs/msg/String "{data: prueba}" > /dev/null 2>&1
    wait $E 2>/dev/null
    grep -q "prueba" "$f" && r=si || r=no
    informe "$top" "$sub" "$pub" "$esp" "$r"
}

tf_estatica() {   # perfil que publica, perfil que busca, esperado (si|no)
    FASTRTPS_DEFAULT_PROFILES_FILE=$(perfil "$1") \
        ros2 run tf2_ros static_transform_publisher --x 1 \
        --frame-id base_link --child-frame-id laser > /dev/null 2>&1 &
    local P=$! r
    sleep 3
    if FASTRTPS_DEFAULT_PROFILES_FILE=$(perfil "$2") timeout 6 \
        ros2 run tf2_ros tf2_echo base_link laser 2>&1 | grep -q "Translation"; then r=si; else r=no; fi
    kill $P 2>/dev/null; wait $P 2>/dev/null; sleep 1
    informe /tf_static "$2" "$1" "$3" "$r"
}

informe() {   # topico, sub, pub, esperado, obtenido
    local marca="ok"
    [ "$4" = "$5" ] || { marca="FALLO"; FALLOS=$((FALLOS + 1)); }
    printf "  %-22s  lee %-3s publica %-3s  espera %-2s  obtiene %-2s  %s\n" \
        "$1" "$2" "$3" "$4" "$5" "$marca"
}

echo "ROS $ROS_DISTRO, dominio de prueba $ROS_DOMAIN_ID"
echo "A = amss-ez9n   B = amss-jgm9   -- = sin perfil"
echo
for t in /ctrl_pkg/servo_msg /rplidar_ros/scan; do
    topico "$t" A A si
    topico "$t" A B no
    topico "$t" A -- no
done
tf_estatica A A si
tf_estatica A B no
topico /robot1/estado A B si

echo
if [ "$FALLOS" -eq 0 ]; then
    echo "PASA: cada vehiculo solo ve sus topicos de hardware, y el grafo comun cruza."
    exit 0
fi
echo "FALLA: $FALLOS casos no salen como se espera. No uses las particiones asi."
exit 1
