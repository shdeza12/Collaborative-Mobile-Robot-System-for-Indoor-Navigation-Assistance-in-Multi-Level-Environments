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

# HAY QUE GRABAR EL RELOJ DE CADA ROBOT, no solo '/clock'.
#
# Desde el 2026-08-30 los dos robots comparten ROS_DOMAIN_ID y cada gzserver
# publica su reloj con nombre propio: robot1 en '/clock' -es el de referencia,
# porque 'ros2 bag record --use-sim-time' esta cableado ahi- y robot2 en
# '/robot2/clock'.
#
# Sin esta linea el bag quedaria asi: los mensajes de robot2 sellados en la
# hora de SU simulador, los del bag sellados en la de robot1, y ni una sola
# pista de cuanto se llevan. Y se llevan mucho: los dos gzserver arrancan en
# momentos distintos, y en las corridas del 2026-08-30 el desfase medido fue de
# 16 s en un caso y de 143 s en otro. No es un sesgo constante que se pueda
# despejar despues; depende de cuando se lanzo cada pila. Grabando los dos
# relojes, la correspondencia entre las dos lineas de tiempo queda en el bag y
# se reconstruye; sin ellos, los datos de robot2 no se pueden situar en la
# mision y la corrida solo sirve para mirar trayectorias sueltas.
#
# La tabla de relojes vive en deepracer_raiz_repo.py, junto a las poses, y NO se
# copia aqui: es el mismo motivo por el que la pose dejo de estar en tres sitios.
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCH_DIR="$RAIZ/Robot/aws-deepracer/deepracer_bringup/launch"

for NS in "${ROBOTS[@]}"; do
    TOPICOS+=("/$NS/odom" "/$NS/amcl_pose" "/$NS/scan" "/$NS/cmd_vel" "/$NS/plan")

    # Si el robot no tiene reloj declarado se corta aqui. Grabar una mision con
    # un robot cuya base de tiempo se desconoce es grabar datos inservibles, y
    # eso se descubriria al analizar, con la simulacion ya apagada.
    if ! RELOJ=$(python3 -c "
import sys
sys.path.insert(0, '$LAUNCH_DIR')
from deepracer_raiz_repo import reloj_de
print(reloj_de('$NS'))
" 2>&1); then
        echo "No se graba: no hay reloj declarado para '$NS'." >&2
        printf '%s\n' "$RELOJ" | sed 's/^/  /' >&2
        exit 1
    fi
    # '/clock' ya esta en IMPRESCINDIBLES; 'ros2 bag record' con el topico
    # repetido avisa, y el aviso confunde mas que ayuda.
    if [ "$RELOJ" != "/clock" ]; then
        TOPICOS+=("$RELOJ")
    fi
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

MARCA_DIR="$(dirname "$0")"

# --- Criterio 1 del §8, antes de grabar -------------------------------------
# De los cinco criterios de validez del §8 del runbook, cuatro se comprueban
# sobre el bag y este NO: que AMCL sepa donde esta el robot dentro de 0,15 m es
# una compuerta PREVIA. Hasta el 2026-09-04 su unico rastro era la salida del
# paso 3 en la terminal, que se pierde al cerrarla, asi que los registros
# compuestos solo podian dar por buenos 4 de 5. Es el mismo modo de fallo que
# ya destruyo el RTF de A_01, C_01 y C_02 el 30-ago.
#
# Se mide AQUI y no en el paso 3 porque el error no depende de la mision sino
# del tiempo que el robot lleve quieto -resbala ~17 mm/min aunque nadie lo
# mande y AMCL no lo corrige hasta acumular 25 cm-, de modo que la unica medida
# que describe esta corrida es la tomada justo antes de abrirle el bag.
#
# Lo que se compara es /amcl_pose contra /odom, NO contra la tabla de spawn.
# Un robot que viene de otra mision no esta en su spawn y no pasa nada: el
# 2026-09-04 el criterio viejo rechazo S21_piloto_A_03 por 1,19 m y 43,92 m
# "de su pose declarada" cuando su error de localizacion era de 0,032 m.
#
# Va antes de la marca de RTF para no meterle 5 s de ventana muerta.
set +e
COND_INICIAL="$(python3 "$MARCA_DIR/verificar_condicion_inicial.py" --json "${ROBOTS[@]}")"
COND_ESTADO=$?
set -e

if [ "$COND_ESTADO" -ne 0 ]; then
    # No se aborta, por el mismo motivo que con el RTF bajo: descartar una
    # corrida es una decision del §8 del protocolo y se toma al componer el
    # registro, con la cifra delante, no aqui.
    echo "AVISO: el criterio 1 del §8 NO se cumple (AMCL no sabe donde esta" >&2
    echo "el robot, >0,15 m). Candidata a descarte. Para verlo con detalle:" >&2
    echo "  python3 herramientas/verificar_condicion_inicial.py ${ROBOTS[*]}" >&2
fi

# --- Marca de RTF, antes de grabar ------------------------------------------
# EL BAG NO PUEDE DAR EL RTF, y por eso se mide aqui. Con '--use-sim-time'
# 'ros2 bag record' sella en tiempo de simulacion tanto los mensajes como el
# 'starting_time' y la 'duration' del metadata.yaml, asi que sim/pared vale 1
# por construccion y no queda ningun ancla de reloj de pared dentro del bag.
# Se comprobo el 2026-08-29 sobre S20_A_M1 y S20_A_M2: las dos misiones se
# grabaron sin RTF y el esquema lo exige -banco simulacion => rtf numerico-,
# asi que hubo que medirlo DESPUES, sobre la sesion todavia viva. Eso salio
# bien por suerte: si el gzserver se hubiera cerrado, las dos corridas no se
# habrian podido registrar y habria que repetirlas.
#
# Medirlo aqui no compite con la simulacion: son dos lecturas de /clock, una
# antes y otra despues, no un muestreo continuo.
# --- Guarda 3: ¿se puede medir el RTF? --------------------------------------
# EL FALLO NO SE PUEDE TRAGAR, y hasta el 2026-09-05 se tragaba. La linea era
#     MARCA_INI="$(python3 .../medir_rtf.py --marca 2>/dev/null || true)"
# y ese '2>/dev/null || true' hacia dos danos a la vez: escondia POR QUE fallo
# la medida, y dejaba seguir la corrida como si nada.
#
# El 2026-09-05 costo TRES de las veinte misiones de la campana -la 13, la 22 y
# la 28-. El aviso del final existia, pero se perdio entre la salida de veinte
# corridas seguidas, el codigo de salida decia 0, y cuando se compusieron los
# registros dos horas despues el gzserver ya estaba cerrado.
#
# Y el RTF perdido NO se reconstruye. Ni del bag -con '--use-sim-time' sim y
# pared salen del mismo reloj y el cociente vale 1 por construccion-, ni de las
# marcas de tiempo de los archivos: se probo contra las 17 corridas de esa
# misma tanda que si tenian rtf.json y da 0,0000 en las 17, porque
# condicion_inicial.json y metadata.yaml se escriben AMBOS al cerrar el bag,
# con dos decimas de diferencia y en orden invertido. Perdida la ventana, la
# unica salida honesta es repetir la corrida.
#
# Por eso la marca inicial es una guarda mas y aborta ANTES de grabar: si el
# RTF no se puede medir, vale mas saberlo ahora que despues de cuatro minutos
# de corrida inservible. El stderr de medir_rtf.py va al terminal sin filtrar,
# que es donde dice si el problema fue que /clock no publica.
set +e
MARCA_INI="$(python3 "$MARCA_DIR/medir_rtf.py" --marca)"
ESTADO_MARCA=$?
set -e

if [ "$ESTADO_MARCA" -ne 0 ] || [ -z "$MARCA_INI" ]; then
    echo "" >&2
    echo "No se graba: no se pudo tomar la marca inicial de RTF, y el esquema" >&2
    echo "lo exige para el banco 'simulacion' (RNF-06 pide >= 0,99). Grabar" >&2
    echo "igual dejaria un bag que despues NO se puede registrar." >&2
    echo "Suele ser que /clock dejo de publicar: comprobar que Gazebo corre y" >&2
    echo "que no esta en pausa. Ver §2.2 de ESQUEMA_REGISTRO_MISION.md." >&2
    exit 1
fi

# '--use-sim-time' NO es opcional, y no es lo mismo que el use_sim_time de los
# nodos. Sin el, 'ros2 bag record' sella cada mensaje con el reloj de PARED, y
# de esos sellos salen TODAS las marcas de RF-25: componer_registro.py lee el
# tiempo del bag, no la cabecera del mensaje.
#
# Se comprobo el 2026-08-27 sobre ~/tesis_evidencia/S20_localizacion/mision3:
# el primer mensaje esta sellado en 1787769550 s, que es epoca Unix, no tiempo
# de simulacion. Un registro compuesto de ahi diria 'reloj: /clock' llevando
# segundos de pared, y con RNF-06 pidiendo solo RTF >= 0,99 las dos escalas
# difieren hasta un 1 %: sobre t_respuesta eso no es ruido, es sesgo.
#
# El precio de la bandera es que hasta que no llegue el primer /clock no se
# escribe nada en el bag. Aqui eso no es un riesgo anadido: la guarda 1 ya se
# nego a grabar si nadie publica /clock.
#
# YA NO ES 'exec'. Lo era, y tenia que dejar de serlo: con exec este proceso se
# reemplaza por el grabador y no queda nadie que tome la segunda marca de RTF
# al cerrar el bag. El trap de INT es lo que permite que Ctrl-C cierre la
# grabacion sin matar tambien el calculo: bash aplaza el trap hasta que el
# comando en primer plano termina, asi que el grabador recibe su SIGINT, cierra
# el bag ordenadamente, y solo entonces se sigue aqui.
trap 'echo "" ' INT
set +e
ros2 bag record --use-sim-time -o "$DESTINO" "${TOPICOS[@]}"
ESTADO_GRABACION=$?
set -e
trap - INT

# --- La condicion inicial, junto al bag -------------------------------------
# Se escribe ahora y no antes porque hasta que 'ros2 bag record' no crea el
# directorio no hay donde ponerla. La MEDIDA es la de antes de grabar; esto
# solo la deja en disco. De aqui la recoge componer_registro.py.
if [ -n "$COND_INICIAL" ] && [ -d "$DESTINO" ]; then
    printf '%s\n' "$COND_INICIAL" > "$DESTINO/condicion_inicial.json"
    echo "Condicion inicial -> $DESTINO/condicion_inicial.json"
elif [ -z "$COND_INICIAL" ]; then
    echo "AVISO: no se pudo medir la condicion inicial. El registro saldra sin" >&2
    echo "el criterio 1 del §8, y ese criterio NO se puede reconstruir despues." >&2
fi

# --- Marca de RTF, al cerrar ------------------------------------------------
# Aqui NO se aborta -el bag ya esta grabado y abortar no lo desharia-, pero el
# fallo tiene que doler: este es el ultimo instante en que la simulacion sigue
# viva, o sea la ultima oportunidad de salvar la corrida. Ver la guarda 3.
set +e
MARCA_FIN="$(python3 "$MARCA_DIR/medir_rtf.py" --marca)"
set -e

if [ -n "$MARCA_INI" ] && [ -n "$MARCA_FIN" ]; then
    python3 - "$DESTINO" "$MARCA_INI" "$MARCA_FIN" <<'PY'
import json, sys
destino, ini, fin = sys.argv[1], sys.argv[2].split(), sys.argv[3].split()
sim0, pared0 = float(ini[0]), float(ini[1])
sim1, pared1 = float(fin[0]), float(fin[1])
d_sim, d_pared = sim1 - sim0, pared1 - pared0
if d_pared <= 0:
    print("AVISO: ventana de pared no positiva, no se escribe rtf.json",
          file=sys.stderr)
    raise SystemExit(0)
rtf = d_sim / d_pared
datos = {"rtf": round(rtf, 4), "sim_s": round(d_sim, 3),
         "pared_s": round(d_pared, 3), "metodo": "marcas_clock_alrededor_del_bag"}
with open(f"{destino}/rtf.json", "w") as f:
    json.dump(datos, f, indent=2)
    f.write("\n")
print(f"RTF de la ventana grabada: {rtf:.4f} "
      f"(sim {d_sim:.1f} s / pared {d_pared:.1f} s) -> {destino}/rtf.json")
if rtf < 0.99:
    # No se aborta ni se borra nada: la decision de descartar es del §8 del
    # protocolo y se toma al componer el registro, no aqui.
    print("AVISO: RTF < 0,99. RNF-06 no se cumple y la corrida es candidata "
          "a 'rtf_bajo' en causa_descarte.", file=sys.stderr)
PY
else
    echo "" >&2
    echo "===================================================================" >&2
    echo "EL BAG QUEDO GRABADO PERO SIN RTF, y esto se resuelve AHORA." >&2
    echo "" >&2
    echo "Mientras la simulacion siga viva el RTF todavia se puede medir. Si" >&2
    echo "se cierra el gzserver se pierde para siempre y la mision hay que" >&2
    echo "repetirla entera: no se reconstruye del bag ni de los archivos." >&2
    echo "" >&2
    echo "  python3 herramientas/medir_rtf.py --segundos 20" >&2
    echo "" >&2
    echo "y al componer el registro, pasar ese valor con --rtf, anotando en" >&2
    echo "el informe que la medida es posterior a la mision." >&2
    echo "===================================================================" >&2
    SIN_RTF=1
fi

# Salida 3 = el bag se grabo bien pero se quedo sin RTF. Existe para que el
# fallo no pase inadvertido en una tanda larga: con salida 0 el operador
# encadena la siguiente mision sin enterarse, que es exactamente como se
# perdieron las corridas 13, 22 y 28 el 2026-09-05.
if [ "$ESTADO_GRABACION" -eq 0 ] && [ "${SIN_RTF:-0}" -ne 0 ]; then
    exit 3
fi

exit "$ESTADO_GRABACION"
