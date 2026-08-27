#!/usr/bin/env bash
# Graba UN bag por mision, con la lista de topicos fija de la §2.2 de
# Documentos/ESQUEMA_REGISTRO_MISION.md.
#
# LA LISTA ES FIJA A PROPOSITO. Si cada corrida graba lo que le parece, el
# conjunto de datos no es homogeneo y la comparacion de S26 -simulacion contra
# fisico sobre la misma geometria- no se puede hacer. No es una precaucion
# teorica: los bags del 26-ago no traen /clock ni /coordinacion/estado_mision,
# que son justo los dos topicos de los que salen TODAS las marcas temporales, y
# por eso sirvieron para medir trayectoria pero no para componer un registro.
#
# UN BAG POR MISION, no uno por sesion. Lo autoriza el §6.4 del protocolo: cada
# corrida arranca con un gzserver nuevo, asi que la frontera entre misiones ya
# es una frontera entre procesos.
#
# Uso:
#     herramientas/grabar_mision.sh <nombre_bag> [robot1 robot2 ...]
#
# Ejemplo:
#     herramientas/grabar_mision.sh S24_B_001 robot1 robot2
#
# Corta con Ctrl-C cuando la mision termine.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Uso: $0 <nombre_bag> [robot1 robot2 ...]" >&2
    exit 1
fi

NOMBRE="$1"; shift
ROBOTS=("$@")
if [ ${#ROBOTS[@]} -eq 0 ]; then ROBOTS=(robot1 robot2); fi

DESTINO="${TESIS_EVIDENCIA:-$HOME/tesis_evidencia}/$NOMBRE"
if [ -e "$DESTINO" ]; then
    echo "Ya existe $DESTINO." >&2
    echo "Un bag por mision: elige otro nombre o borra ese." >&2
    exit 1
fi

# /coordinacion/estado_mision y /clock son de donde salen las marcas. Si falta
# uno de los dos, el registro no se puede componer y la corrida no vale.
IMPRESCINDIBLES=(/clock /coordinacion/estado_mision)
TOPICOS=("${IMPRESCINDIBLES[@]}" /coordinacion/puntos_interes /tf /tf_static)
for NS in "${ROBOTS[@]}"; do
    TOPICOS+=("/$NS/odom" "/$NS/amcl_pose" "/$NS/scan" "/$NS/cmd_vel" "/$NS/plan")
done

# Se avisa de los que no aparecen todavia, pero solo se aborta por los dos
# imprescindibles: un robot puede no haber arrancado aun y 'ros2 bag record' lo
# recoge cuando aparezca, pero sin /clock o sin estado_mision se estaria
# grabando una corrida que ya se sabe que habra que repetir.
#
# '-t' anade el tipo entre corchetes. Sale del GRAFO, asi que aparece aunque
# este proceso no tenga el paquete que lo define: por eso sirve para detectar
# justo ese caso unas lineas mas abajo.
VIVOS="$(ros2 topic list -t)"
for T in "${TOPICOS[@]}"; do
    if ! grep -q "^$T \[" <<< "$VIVOS"; then
        echo "AVISO: $T no aparece en el grafo ahora mismo." >&2
    fi
done

# --- Guarda 1: ¿esta el sistema arriba? -------------------------------------
# Para los imprescindibles NO basta con que el topico este en la lista.
# 'ros2 topic list' incluye los topicos que solo tienen SUSCRIPTORES, y eso
# convierte la guarda en decorativa justo en el caso que importa: si Gazebo se
# murio pero Nav2 sigue vivo con use_sim_time, /clock aparece en la lista -por
# los suscriptores- y se grabaria una corrida sin una sola marca temporal.
# Se comprobo el 2026-08-26 con solo el coordinador arriba: /robot1/odom salia
# listado con Publisher count 0 y Subscription count 3.
# Por eso aqui se cuentan PUBLICADORES, que es la pregunta real.
FALTAN=()
for I in "${IMPRESCINDIBLES[@]}"; do
    # El '|| true' no es adorno: 'ros2 topic info' sale con 1 si el topico no
    # existe, y con 'set -e' + pipefail eso mataba el script en esta linea, sin
    # llegar a imprimir por que no se graba. Aqui un topico ausente no es un
    # error del script: es justo el caso que hay que reportar.
    PUBS="$(ros2 topic info "$I" 2>/dev/null \
            | sed -n 's/^Publisher count: //p' || true)"
    if [ "${PUBS:-0}" -eq 0 ] 2>/dev/null; then
        FALTAN+=("$I")
    fi
done

if [ ${#FALTAN[@]} -gt 0 ]; then
    echo "" >&2
    echo "No se graba: nadie publica ${FALTAN[*]}, de donde salen las" >&2
    echo "marcas temporales. Sin ellas el registro no se puede componer." >&2
    echo "Si falta /clock, comprobar que Gazebo corre y que los nodos llevan" >&2
    echo "use_sim_time: true. Ver §2.2 de ESQUEMA_REGISTRO_MISION.md." >&2
    exit 1
fi

# --- Guarda 2: ¿puedo grabar lo que esta arriba? ----------------------------
# Que el topico este en el aire no basta: 'ros2 bag record' solo graba los
# tipos que puede resolver, y si no puede se limita a un WARN por consola y
# sigue grabando los demas. El bag queda con /clock y sin estado_mision, que es
# exactamente un bag inservible con pinta de bag bueno.
#
# Pasa por algo tan tonto como abrir la terminal y sourcear solo
# /opt/ros/humble/setup.bash olvidando el overlay del workspace. Se reprodujo
# el 2026-08-26: 97 mensajes grabados, los 97 de /clock, cero de
# /coordinacion/estado_mision. Es el mismo agujero de los bags del 26-ago
# entrando por otra puerta.
TIPOS="$(for T in "${TOPICOS[@]}"; do
             sed -n "s|^$T \[\(.*\)\]\$|\1|p" <<< "$VIVOS"
         done | sort -u)"

NO_RESOLUBLES=()
for TIPO in $TIPOS; do
    if ! ros2 interface show "$TIPO" > /dev/null 2>&1; then
        NO_RESOLUBLES+=("$TIPO")
    fi
done

if [ ${#NO_RESOLUBLES[@]} -gt 0 ]; then
    echo "" >&2
    echo "No se graba: este proceso no puede resolver los tipos" >&2
    printf '  %s\n' "${NO_RESOLUBLES[@]}" >&2
    echo "y 'ros2 bag record' los descartaria en silencio, con un WARN que se" >&2
    echo "pierde entre el resto de la salida. El bag pareceria correcto." >&2
    echo "Casi siempre falta sourcear el workspace:" >&2
    echo "  source ~/deepracer_sim_ws/install/setup.bash" >&2
    exit 1
fi

echo "Grabando en $DESTINO"
echo "Robots: ${ROBOTS[*]}   Topicos: ${#TOPICOS[@]}"
echo "Ctrl-C para cerrar el bag."
mkdir -p "$(dirname "$DESTINO")"
exec ros2 bag record -o "$DESTINO" "${TOPICOS[@]}"
