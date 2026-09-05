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

# Los siete de ros2_control. Migrados en S12: el estado es 'active', no 'start'.
CONTROLADORES=(joint_state_broadcaster
               left_rear_wheel_velocity_controller
               right_rear_wheel_velocity_controller
               left_front_wheel_velocity_controller
               right_front_wheel_velocity_controller
               left_steering_hinge_position_controller
               right_steering_hinge_position_controller)

# 'ros2 control list_controllers' colorea su salida, y en ANSI "active" es
# "\x1b[92mactive\x1b[0m". Sin limpiarlo, la comparacion no casa nunca.
ANSI='s/\x1b\[[0-9;]*m//g'

echo "Esperando a que la pila de $ROBOT este lista (plazo ${PLAZO} s)."
echo "Compuerta: 7 nodos de Nav2 en active + 7 controladores en active."

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
        echo "Los 7 nodos de Nav2 y los 7 controladores estan en active."
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
            echo "Faltan nodos de NAV2: es la carrera entre los dos" >&2
            echo "lifecycle_manager. Relanzar suele bastar; si se repite, mirar" >&2
            echo "si hay 'Invalid frame ID \"$ROBOT/map\"' en el log del launch." >&2
        fi
        exit 1
    fi

    sleep 2
done
