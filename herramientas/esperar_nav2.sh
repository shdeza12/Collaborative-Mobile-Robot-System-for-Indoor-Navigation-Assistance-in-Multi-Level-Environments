#!/usr/bin/env bash
# Bloquea hasta que la pila de un robot este LISTA PARA CONDUCIR, o se rinde.
#
# POR QUE EXISTE. El bag ~/tesis_evidencia/S20_piloto_01 (2026-08-27, 11:20)
# tiene cero mensajes en cmd_vel, cero en amcl_pose y cero en plan: se grabo una
# mision entera contra una pila muerta y no se noto hasta abrir el bag. La
# comprobacion que lo habria evitado se venia haciendo A MANO, pegando un bucle
# de siete 'ros2 lifecycle get' en la terminal. Una comprobacion manual que hay
# que repetir en cada mision -y el §6.4 del protocolo exige un gzserver nuevo
# POR MISION- es una comprobacion que tarde o temprano alguien se salta.
#
# QUE ESPERA, Y POR QUE ESAS DOS COSAS.
#
# 1. Los siete nodos de ciclo de vida de Nav2 en 'active'. No es celo: los dos
#    lifecycle_manager -localization y navigation- arrancan EN PARALELO y nadie
#    garantiza el orden. Si gana navigation, nav2_costmap_2d se queda bloqueado
#    dentro de on_activate esperando la transformada <ns>/base_link -> <ns>/map,
#    que no existe hasta que AMCL active. El interbloqueo es permanente y su
#    sintoma es 'Invalid frame ID "<ns>/map"' en bucle, con bt_navigator en
#    'inactive' rechazando cada meta en unos 50 ms. Desde fuera parece que la
#    mision "fallo rapido"; en realidad nunca empezo.
#
#    Hay un SEGUNDO modo de fallo que deja la misma lista de nodos pendientes y
#    no tiene nada que ver con ese: lifecycle_manager_navigation configura sus
#    cinco nodos en orden y espera cada respuesta sin plazo, asi que si el
#    middleware pierde la respuesta de un change_state se queda clavado para
#    siempre en el primero. Se distingue por el estado: ahi los nodos de detras
#    quedan en 'unconfigured', no en 'inactive'. El diagnostico del final los
#    separa; el remedio del primero -esperar, reintentar- no sirve para el
#    segundo, que solo se arregla relanzando.
#
# 2. Los siete controladores de ros2_control en 'active'. Nav2 puede estar
#    perfecto y publicar cmd_vel impecable, y el carro no moverse ni un metro
#    porque los controladores no levantaron. El bag saldria CON cmd_vel y sin
#    desplazamiento, que es un modo de fallo peor que el anterior: parece un
#    problema de control cuando es un problema de arranque.
#
# 3. Que la pila VIVA lleve los parametros del YAML del repo. Los nodos leen su
#    configuracion UNA VEZ, al arrancar, asi que editar el YAML y no relanzar
#    deja una pila vieja con un fichero nuevo, y las dos cosas se ven igual
#    desde la terminal. El 2026-08-27 se perdio una mision entera asi: se
#    analizo su bag como si midiera los alpha corregidos y llevaba los
#    antiguos. Ver verificar_parametros_vivos.py.
#
# 4. Y una vez lista, que el robot ESTE donde dice la tabla de spawn. Este
#    tercero NO espera, y la diferencia no es un detalle de implementacion: el
#    carro resbala ~17 mm/min en Gazebo aunque nadie lo mande (ver la cabecera
#    de verificar_condicion_inicial.py), asi que esperar no arregla nada, lo
#    empeora. Por eso los dos primeros son bucles y los dos ultimos son
#    veredictos que se emiten una sola vez, al final, y por eso la compuerta
#    hay que correrla JUSTO ANTES de cada mision y no una vez por tarde.
#
# Uso:
#     herramientas/esperar_nav2.sh robot1 [segundos]
#
# Encadenado, que es para lo que se escribio:
#     herramientas/esperar_nav2.sh robot1 && herramientas/grabar_mision.sh S20_x robot1
#
# Codigo de salida: 0 si la pila esta lista, 1 si se agoto el plazo.
set -uo pipefail

ROBOT="${1:-robot1}"
PLAZO="${2:-120}"

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Los siete de Nav2. La lista sale del grafo vivo del 2026-08-27, no del launch:
# 'velocity_smoother' NO esta en esta pila aunque Nav2 de Humble lo traiga.
NODOS=(map_server amcl controller_server planner_server behavior_server
       bt_navigator waypoint_follower)

# Los de ros2_control. Migrados en S12: el estado es 'active', no 'start'.
#
# La lista NO se copia aqui: sale de 'deepracer_raiz_repo.py', el mismo modulo
# que la usa para cargarlos. Una compuerta que espera por una lista vieja deja
# pasar una corrida a la que le falta un controlador, y eso no da error: el carro
# arranca y no se mueve. Si el modulo no se puede leer se corta, porque una
# compuerta que no sabe que exigir no es una compuerta.
#
# Se usa sustitucion de ORDEN y no 'mapfile < <(...)': mapfile devuelve 0 aunque
# el python de dentro reviente, asi que el fallo entraria en el array como texto
# de error y la compuerta esperaria por un controlador llamado 'Traceback'.
LAUNCH_DIR="$AQUI/../Robot/aws-deepracer/deepracer_bringup/launch"
if ! LISTA_CTRL=$(python3 -c "
import sys
sys.path.insert(0, '$LAUNCH_DIR')
from deepracer_raiz_repo import CONTROLADORES
print('\n'.join(CONTROLADORES))
" 2>&1); then
    echo "No pude leer la lista de controladores de deepracer_raiz_repo.py:" >&2
    printf '%s\n' "$LISTA_CTRL" | sed 's/^/  /' >&2
    exit 1
fi
read -r -d '' -a CONTROLADORES <<< "$LISTA_CTRL" || true

# 'ros2 control list_controllers' colorea su salida, y en ANSI "active" es
# "\x1b[92mactive\x1b[0m". Sin limpiarlo, la comparacion no casa nunca.
ANSI='s/\x1b\[[0-9;]*m//g'

echo "Esperando a que la pila de $ROBOT este lista (plazo ${PLAZO} s)."
echo "Compuerta: ${#NODOS[@]} nodos de Nav2 en active + ${#CONTROLADORES[@]} controladores en active."

INICIO=$SECONDS
ULTIMO=""
while true; do
    FALTAN=()

    for N in "${NODOS[@]}"; do
        # '|| true' obligatorio: 'ros2 lifecycle get' sale con codigo distinto
        # de cero cuando el nodo aun no existe, que es justo el caso normal
        # mientras se espera. Sin esto la compuerta se mata a si misma.
        #
        # 'timeout' tambien es obligatorio, y no es precaucion: el 2026-08-27 la
        # compuerta de robot2 se colgo 138 s en '/robot2/controller_server'
        # mientras ese mismo comando respondia 'active' al instante desde otra
        # terminal. Un cliente creado mientras el servidor levanta su servicio
        # puede no emparejar nunca, y 'wait_for_service' no tiene plazo: la
        # espera queda DENTRO de la sustitucion, antes de la linea que evalua el
        # plazo de la compuerta, asi que ni siquiera se rendia a los 120 s.
        # Acotar cada llamada hace que la vuelta siguiente cree un cliente nuevo,
        # que es lo que rompe la carrera. El bucle de reintento ya estaba.
        ESTADO="$(timeout 10 ros2 lifecycle get "/$ROBOT/$N" 2>/dev/null || true)"
        [[ "$ESTADO" == active* ]] || FALTAN+=("$N")
    done

    # Los controladores solo se miran cuando Nav2 ya esta entero: antes, el
    # controller_manager puede no haber arrancado y la salida seria ruido.
    if [ ${#FALTAN[@]} -eq 0 ]; then
        # Acotada por el mismo motivo que 'lifecycle get': este comando avisa por
        # stderr con 'waiting for service ... to become available' y espera sin
        # plazo. Aqui son 20 s porque la llamada trae siete controladores.
        LISTA="$(timeout 20 ros2 control list_controllers \
                 -c "/$ROBOT/controller_manager" 2>/dev/null | sed "$ANSI" || true)"
        for C in "${CONTROLADORES[@]}"; do
            grep -qE "^$C .*active" <<< "$LISTA" || FALTAN+=("ctrl:$C")
        done
    fi

    if [ ${#FALTAN[@]} -eq 0 ]; then
        echo ""
        echo "Los ${#NODOS[@]} nodos de Nav2 y los ${#CONTROLADORES[@]} controladores estan en active."
        echo "Tiempo de arranque: $((SECONDS - INICIO)) s."
        echo ""

        # Tercer chequeo: una sola pasada, sin bucle. Ver la cabecera.
        echo "Comprobando que la pila viva sea la del YAML..."
        # 1 es desajuste real y 2 es "no se pudo leer": son diagnosticos
        # distintos y llevan a acciones distintas, asi que no se confunden.
        python3 "$AQUI/verificar_parametros_vivos.py" "$ROBOT"
        CODIGO_PARAM=$?
        if [ "$CODIGO_PARAM" -eq 1 ]; then
            echo "" >&2
            echo "NO GRABES: la pila corre con parametros distintos de los del" >&2
            echo "repositorio. El bag no mediria el cambio que quieres medir." >&2
            exit 1
        elif [ "$CODIGO_PARAM" -ne 0 ]; then
            echo "" >&2
            echo "NO GRABES TODAVIA: esta compuerta no pudo comprobar la pila." >&2
            echo "No es lo mismo que decir que sea distinta. Vuelve a correr" >&2
            echo "  python3 herramientas/verificar_parametros_vivos.py $ROBOT" >&2
            echo "y solo si insiste, relanza la pila." >&2
            exit 1
        fi

        echo ""
        # Cuarto chequeo: una sola pasada, sin bucle. Ver la cabecera.
        echo "Comprobando la condicion inicial..."
        if ! python3 "$AQUI/verificar_condicion_inicial.py" "$ROBOT"; then
            echo "" >&2
            echo "NO GRABES: la pila arranco pero el robot no esta en su pose" >&2
            echo "declarada, y AMCL se siembra con la declarada. El sesgo se" >&2
            echo "colaria entero en el error de llegada." >&2
            exit 1
        fi

        echo ""
        echo "LISTA. Nav2, controladores, parametros y condicion inicial."
        echo "Arranca la mision YA: la condicion inicial se degrada ~17 mm/min."
        exit 0
    fi

    # Se imprime solo cuando la lista de pendientes CAMBIA. Un punto por segundo
    # durante dos minutos no dice nada; ver desaparecer nodos de la lista si.
    ACTUAL="${FALTAN[*]}"
    if [ "$ACTUAL" != "$ULTIMO" ]; then
        echo "  faltan (${#FALTAN[@]}): $ACTUAL"
        ULTIMO="$ACTUAL"
    fi

    if [ $((SECONDS - INICIO)) -ge "$PLAZO" ]; then
        echo "" >&2
        echo "NO ARRANCO en ${PLAZO} s. Siguen sin estar en active:" >&2
        printf '  %s\n' "${FALTAN[@]}" >&2
        echo "" >&2
        echo "NO GRABES una mision asi: saldria un bag con pinta de bag bueno y" >&2
        echo "sin una sola muestra util, como S20_piloto_01." >&2
        echo "" >&2
        # El diagnostico se separa porque las dos mitades de la compuerta fallan
        # por motivos distintos y confundirlos cuesta tiempo de depuracion.
        if printf '%s\n' "${FALTAN[@]}" | grep -q '^ctrl:'; then
            echo "Faltan CONTROLADORES: Nav2 esta bien pero el carro no se movera." >&2
            echo "  ros2 control list_controllers -c /$ROBOT/controller_manager" >&2
            echo "Si alguno sale 'unconfigured', casi siempre es el spawner que" >&2
            echo "corrio antes que gazebo_ros2_control. Relanzar." >&2
        else
            # Dos fallos distintos se ven IGUAL desde aqui -"faltan nodos de
            # Nav2"- y piden remedios opuestos. Hasta el 2026-09-10 esta rama
            # afirmaba que siempre era la carrera entre los dos
            # lifecycle_manager; ese dia el fallo era el otro y la pista costo
            # media hora de depuracion. Asi que ya no se adivina: se mira el
            # estado de los que faltan, que es lo que los separa.
            echo "Faltan nodos de NAV2. Estado real de cada uno:" >&2
            for N in "${FALTAN[@]}"; do
                printf '  %-22s %s\n' "$N" \
                    "$(timeout 10 ros2 lifecycle get "/$ROBOT/$N" 2>/dev/null || echo '(no responde)')" >&2
            done
            echo "" >&2
            # 'unconfigured' detras de uno que si llego a 'inactive' = el gestor
            # de navegacion se quedo bloqueado. Configura sus cinco nodos EN
            # ORDEN y espera la respuesta de cada change_state SIN PLAZO, asi que
            # si el middleware pierde UNA respuesta no vuelve a avanzar nunca.
            # Queda clavado en "Configuring <el primero>" y ni su propio
            # 'manage_nodes' contesta. Visto el 2026-08-10 y el 2026-09-10, las
            # dos veces en controller_server y las dos veces con este aviso en el
            # log del nodo:
            #   failed to send response to /<ns>/controller_server/change_state
            #   (timeout): client will not receive response
            # El emparejamiento DDS del canal de respuesta no estaba hecho
            # cuando la respuesta salio. No hay nada que reintentar desde fuera.
            #
            # El '-mmin -30' no es cosmetico: el mismo aviso aparece en logs de
            # hace semanas y sin acotarlo la pista senalaria una corrida vieja
            # como si fuera la de ahora, que es exactamente el error que esta
            # rama existe para no repetir.
            PERDIDA="$(find "$HOME/.ros/log" -maxdepth 1 -name '*.log' -mmin -30 \
                       -exec grep -l "failed to send response to /$ROBOT/.*change_state" {} + \
                       2>/dev/null | tail -3)"
            if [ -n "$PERDIDA" ]; then
                echo "El gestor de ciclo de vida esta BLOQUEADO, no lento: el" >&2
                echo "middleware perdio una respuesta de change_state." >&2
                printf '%s\n' "$PERDIDA" | sed 's/^/  /' >&2
                echo "Esperar mas no sirve y 'manage_nodes' tampoco responde." >&2
                echo "Unico remedio -solo este robot, el otro no se toca-:" >&2
                echo "  herramientas/robot.sh $ROBOT nav2" >&2
            else
                echo "Si TODOS los que faltan salen 'inactive', es la carrera" >&2
                echo "entre los dos lifecycle_manager: nav2_costmap_2d bloqueado" >&2
                echo "en on_activate esperando $ROBOT/map. Se reconoce por" >&2
                echo "'Invalid frame ID \"$ROBOT/map\"' en bucle en el log del" >&2
                echo "launch. Relanzar: herramientas/robot.sh $ROBOT nav2" >&2
            fi
        fi
        exit 1
    fi

    sleep 2
done
