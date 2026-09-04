#!/usr/bin/env python3
"""Comprueba que AMCL sepa AHORA MISMO donde esta el robot.

No es lo mismo que verificar_pose_spawn.py, y la diferencia importa. Aquel
comprueba en frio que la pose CONFIGURADA caiga en sitio libre del mapa; este
comprueba en vivo que la CREENCIA del robot coincida con donde esta. Una pose
configurada impecable y un robot que no sabe donde esta son perfectamente
compatibles, y es lo que pasa.

POR QUE EXISTE
--------------
Dos veces en un dia se conduzco una mision desde una condicion inicial que no
era la declarada.

  - El 2026-08-26, S20_piloto_02 arranco en (-17.097, 10.452) por reusar el
    gzserver de una corrida anterior. El §6.4 del protocolo pide un gzserver
    nuevo por mision justo para esto. Salio FALLIDA a 0.573 m.

  - El 2026-08-27, con gzserver NUEVO y sin que nadie tocase el robot, robot1
    quedo a 0.669 m y 46.4 grados de POSE_INICIAL. Medido a tres bandas: Gazebo
    daba (-19.802, 7.067, 43.6 grados), /odom coincidia, y la tabla decia
    (-19.165, 7.292, 90 grados). Cero mensajes en /cmd_vel: nadie lo movio.

LA CAUSA, MEDIDA
----------------
La primera explicacion que se dio por buena fue que el carro rodaba suelto
durante los 63 s que tardan en activar los controladores de rueda ('Failed
getting a result from calling list_controllers in 60.0' en el log). ERA FALSA,
y conviene dejarlo escrito para que nadie vuelva a ese callejon. Se descarto
midiendo 60 s con los SIETE controladores en active y nadie publicando cmd_vel:

    x    -20.0022 -> -20.0105     (-8.3 mm)
    y      7.10322 ->   7.11829   (+15.1 mm)
    yaw    0.84435 ->   0.86865   (+1.39 grados)

Son 17 mm/min, 0.29 mm/s, constantes. A ese ritmo los 63 s del arranque dan
18 mm, no 0.669 m. El carro no rodo al arrancar y se detuvo: SIGUE resbalando.

Que es un deslizamiento y no un rodaje se ve en tres sitios:
  - la direccion esta sujeta en 5e-5 rad, o sea que el controlador de posicion
    manda y las ruedas no estan caidas;
  - las ruedas giran a 0.008-0.047 rad/s con comando CERO, y asimetricas
    -las derechas cuatro veces mas rapido-, que es de donde sale el giro;
  - el desplazamiento va en rumbo 118.8 grados mientras el carro apunta a 48.4.
    Son 70 grados de diferencia: un vehiculo con ruedas no puede avanzar asi.
El modelo esta ademas hundido a z=-0.007 y cabeceado -1.39 grados, constantes.
Es un artefacto de contacto de ODE, no un problema de arranque.

POR QUE NO ES UN DETALLE
------------------------
Por si solo, 17 mm/min no asustaria. Lo que lo vuelve grave es que AMCL NO SE
ENTERA. Con update_min_d: 0.25 y update_min_a: 0.2 el filtro solo corrige
cuando acumula 25 cm o 11.5 grados, y a esta velocidad eso tarda 14 y 8
minutos. Entre actualizacion y actualizacion el robot se va y la estimacion se
queda. Medido el 2026-08-27 sobre una pila con ~48 min de reposo:

    Gazebo (verdad)     (-20.0344, 7.16372, 46.5 grados)
    /robot1/amcl_pose   (-19.4076, 7.02101, 56.3 grados)

0.643 m y 9.8 grados de error con el robot PARADO -2.6 veces la tolerancia de
llegada de 0.25 m-. Y la x de amcl_pose era identica hasta el quinto decimal a
la medida media hora antes: el filtro no habia publicado ni una actualizacion
mientras el carro se deslizaba 0.6 m.

QUE SE MIDE, Y POR QUE NO ES LA DISTANCIA AL SPAWN
--------------------------------------------------
Hasta el 2026-09-04 esta compuerta comparaba la pose real contra la TABLA DE
SPAWN. Estaba mal, y lo demostro una corrida sana: S21_piloto_A_03 fue
rechazada con robot1 a 1.19 m y robot2 a 43.92 m "de su pose declarada", cuando
su error de localizacion al arrancar era de 0.032 m -mejor que el del piloto
que si paso, 0.040 m- y llego a 0.068 m del destino, la mejor llegada del dia.
Lo unico que pasaba es que los robots venian de una mision anterior.

La magnitud que hace dano es la de arriba: que la CREENCIA de AMCL se separe de
la VERDAD. La distancia a la tabla era un SUSTITUTO de esa magnitud, y solo
vale mientras el robot no se haya movido a proposito, porque AMCL se siembra
con la pose declarada. Comprobado en los bags de los dos pilotos del
2026-09-04, leyendo /amcl_pose contra /odom:

                        desvio vs tabla   error AMCL vs verdad
  piloto 1 (pila nueva)      0.0396 m           0.040 m   <- iguales
  piloto 2 (encadenada)      1.1919 m           0.032 m   <- divergen

En pila nueva los dos numeros son el MISMO por construccion, asi que el
criterio nuevo no afloja nada: subsume al viejo. En cuanto el robot navega, el
sustituto pasa a medir la mision en vez del resbalon. Y hay un motivo que
remata: en el banco fisico no se puede respawnear nada, asi que un criterio de
"estar en la pose de spawn" es inaplicable donde esto tiene que acabar.

La creencia se lee de /<robot>/amcl_pose y NO de la composicion de /tf. Se
probaron las dos: la composicion (map->odom) o pose_odom da 0.0007 m al
arrancar, no 0.040 m, porque AMCL todavia no ha corregido -la correccion es la
identidad- y /odom ya es la verdad, asi que el resultado sigue a la verdad por
construccion y la compuerta aprobaria siempre. Solo convergen las dos fuentes
cuando el robot ya lleva rato navegando (medido: 0.0469 vs 0.0465 a los 134 s).

LA CONSECUENCIA OPERATIVA, QUE ES LO QUE HAY QUE RECORDAR
---------------------------------------------------------
El error no depende de la mision: depende del TIEMPO QUE EL ROBOT LLEVA QUIETO,
porque quieto es justo cuando resbala sin que AMCL lo corrija. Con la
tolerancia de 0.15 m de aqui abajo, una pila recien levantada la respeta y a
los ~9 minutos ya no. Asi que esta comprobacion NO se hace una vez tras el
lanzamiento y se da por buena para toda la tarde: se hace JUSTO ANTES de cada
mision. Dos misiones "identicas" lanzadas con diez minutos de diferencia no
parten de la misma condicion inicial. Se vio en el piloto 2: robot1, que acababa
de navegar, iba a 0.032 m, y robot2, que llevaba la mision entera parado, a
0.132 m -dentro de tolerancia, pero cuatro veces peor-.

Esto es tambien del mismo orden de magnitud que los errores de llegada que se
venian atribuyendo a la observabilidad del pasillo (sigma_x 0.704 m contra
sigma_y 0.186 m), asi que mientras no se descarte NO se puede afirmar cual de
las dos causas manda.

Uso:
    python3 herramientas/verificar_condicion_inicial.py robot1
    python3 herramientas/verificar_condicion_inicial.py --json robot1 robot2

Codigo de salida: 0 si TODOS los robots saben donde estan, 1 si no.

El JSON lleva un campo "criterio": "localizacion" que los de antes del
2026-09-04 no tienen. Sin el, un condicion_inicial.json viejo y uno nuevo son
indistinguibles y su "dentro" no significa lo mismo.

Con --json escribe el veredicto en una linea de JSON por la salida estandar y
calla el resto. Es lo que grabar_mision.sh deja en <bag>/condicion_inicial.json
justo antes de abrir el bag, y de ahi lo recoge componer_registro.py. Existe
porque el criterio 1 de los cinco del §8 del runbook es el unico que NO se
puede comprobar a posteriori -es una compuerta previa- y hasta el 2026-09-04 su
unico rastro era esta salida en la terminal, que se pierde al cerrarla. Es el
mismo modo de fallo que ya destruyo el RTF de tres corridas del 30-ago: si no
se escribe en el momento, no se escribe nunca.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Robot", "aws-deepracer", "deepracer_bringup", "launch"))

from deepracer_raiz_repo import pose_por_defecto

# En simulacion /odom NO es odometria: el plugin publica la pose del mundo de
# Gazebo (gazebo_ros_deepracer_drive.cpp:229), asi que es verdad de terreno y
# no acumula deriva. En el carro fisico esto no vale y por eso el script se
# niega a opinar si no hay /clock.
TOLERANCIA_M = 0.15
TOLERANCIA_YAW_GRADOS = 10.0


def _yaw(q):
    return math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)


def _normalizar_grados(a):
    return (a + 180.0) % 360.0 - 180.0


def evaluar_desvios(esperada, real, creida):
    """Decide si la condicion inicial vale. Poses como (x, y, yaw_rad).

    Es funcion PURA y vive separada de la lectura de topicos a proposito: el
    criterio es lo que se equivoco el 2026-09-04, y lo que se equivoca hay que
    poder probarlo sin levantar la simulacion. La prueba esta al lado, en
    prueba_verificar_condicion_inicial.py.

      esperada  la de la tabla de spawn. Solo informativa desde el 2026-09-04.
      real      donde esta el robot (verdad de terreno).
      creida    donde cree AMCL que esta. None si no se pudo leer.

    'dentro' sale de la CREENCIA contra la VERDAD, no del desvio contra la
    tabla. Con creida None sale None, que no es aprobar: significa que no se
    pudo medir, y el §8 manda descartar cuando el criterio 1 no se cumple.
    """
    ex, ey, eyaw = esperada
    rx, ry, ryaw = real
    d = math.hypot(rx - ex, ry - ey)
    dyaw = abs(_normalizar_grados(math.degrees(ryaw - eyaw)))

    salida = {"criterio": "localizacion",
              "desviacion_m": round(d, 4),
              "desviacion_yaw_grados": round(dyaw, 2),
              "error_localizacion_m": None,
              "error_localizacion_yaw_grados": None,
              "dentro": None}
    if creida is None:
        return salida

    cx, cy, cyaw = creida
    e = math.hypot(cx - rx, cy - ry)
    eyaw_g = abs(_normalizar_grados(math.degrees(cyaw - ryaw)))
    salida["error_localizacion_m"] = round(e, 4)
    salida["error_localizacion_yaw_grados"] = round(eyaw_g, 2)
    salida["dentro"] = e <= TOLERANCIA_M and eyaw_g <= TOLERANCIA_YAW_GRADOS
    return salida


def leer_estado(robots, segundos=5.0):
    """Devuelve {robot: (verdad o None, creencia o None, hay_clock)}.

    Los robots se escuchan A LA VEZ, con un solo nodo, y no uno detras de otro.
    No es por elegancia: el error crece ~17 mm/min con el robot quieto, asi que
    medir robot2 cinco segundos despues que robot1 seria medir dos instantes
    distintos y llamarlos la misma condicion inicial.

    /amcl_pose se ofrece TRANSIENT_LOCAL y RELIABLE -leido del
    offered_qos_profiles del bag S21_piloto_B_02: durability 1, reliability 1,
    frente al durability 2 (VOLATILE) de /odom-. Hay que pedirlo igual por dos
    motivos: con un perfil por defecto (volatil) el emparejamiento ni siquiera
    se produce y no llegaria NADA, y aun emparejando, AMCL solo publica cuando
    cruza update_min_d, asi que con el robot parado pueden pasar minutos sin un
    mensaje nuevo. TRANSIENT_LOCAL es justo lo que hace que un suscriptor
    tardio reciba la ultima pose publicada, que es la que interesa.

    'hay_clock' cuenta PUBLICADORES, no suscriptores: 'ros2 topic list' lista
    /clock aunque solo lo escuchen los nodos con use_sim_time, asi que la
    pregunta util es si alguien lo escribe. Es la misma trampa que ya se
    documento en grabar_mision.sh (guarda 1).
    """
    import rclpy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from nav_msgs.msg import Odometry
    from rclpy.node import Node
    from rclpy.qos import (DurabilityPolicy, QoSProfile, ReliabilityPolicy)

    creencia_qos = QoSProfile(depth=1,
                              durability=DurabilityPolicy.TRANSIENT_LOCAL,
                              reliability=ReliabilityPolicy.RELIABLE)

    rclpy.init()
    nodo = Node("verificador_de_condicion_inicial")
    muestras = {r: [] for r in robots}
    creencias = {r: [] for r in robots}
    for r in robots:
        nodo.create_subscription(
            Odometry, f"/{r}/odom",
            lambda m, r=r: muestras[r].append(m), 10)
        nodo.create_subscription(
            PoseWithCovarianceStamped, f"/{r}/amcl_pose",
            lambda m, r=r: creencias[r].append(m), creencia_qos)
    fin = nodo.get_clock().now().nanoseconds * 1e-9 + segundos
    while rclpy.ok() and nodo.get_clock().now().nanoseconds * 1e-9 < fin:
        rclpy.spin_once(nodo, timeout_sec=0.1)
        if all(len(muestras[r]) > 20 and creencias[r] for r in robots):
            break
    # EL RELOJ DE ESTE ROBOT PUEDE NO SER '/clock'. Desde el 2026-08-30 los dos
    # robots comparten dominio y se distinguen por el topico de reloj: robot1 se
    # queda en '/clock' -es el de referencia de la mision- y robot2 publica en
    # '/robot2/clock'. Mirar solo '/clock' daria dos veredictos falsos:
    #
    #   - con solo robot2 arriba, diria "esto no parece simulacion" y se callaria
    #     teniendo delante una simulacion perfectamente valida;
    #   - con los dos arriba, diria que si hay reloj aunque el de robot2 estuviera
    #     muerto, porque estaria viendo el de robot1.
    #
    # Por eso se pregunta primero por el propio y solo despues por el comun.
    salida = {}
    for r in robots:
        reloj = f"/{r}/clock"
        if nodo.count_publishers(reloj) == 0:
            reloj = "/clock"
        salida[r] = (muestras[r][-1] if muestras[r] else None,
                     creencias[r][-1] if creencias[r] else None,
                     nodo.count_publishers(reloj) > 0)
    nodo.destroy_node()
    rclpy.shutdown()
    return salida


def _evaluar(robot, od, am, hay_clock):
    """Devuelve (entrada del registro, lineas para la persona).

    'dentro' en None significa NO SE PUDO MEDIR, y no es lo mismo que estar en
    su sitio: el §8 manda descartar la corrida cuando el criterio 1 no se
    cumple, y un hueco que se leyera como aprobado la colaria.
    """
    ni_idea = {"criterio": "localizacion",
               "desviacion_m": None, "desviacion_yaw_grados": None,
               "error_localizacion_m": None,
               "error_localizacion_yaw_grados": None, "dentro": None}

    try:
        esperada = pose_por_defecto(robot)
    except Exception as e:
        return ni_idea, [f"No hay pose declarada para '{robot}': {e}"]

    if od is None:
        return ni_idea, [
            f"No llego ni una muestra de /{robot}/odom.",
            "O la simulacion no esta arriba, o este proceso esta en otro "
            "ROS_DOMAIN_ID. Desde el 2026-08-30 los dos robots comparten el "
            "dominio 0, que es el defecto de ROS 2: una terminal sin exportar "
            "nada deberia verlos a los dos."]

    # Sin /clock esto no es simulacion, y entonces /odom SI es odometria: lleva
    # deriva acumulada y comparar su valor absoluto contra una pose de mundo no
    # significa nada. El script prefiere callarse a dar un veredicto falso.
    if not hay_clock:
        return ni_idea, [
            f"Nadie publica /{robot}/clock ni /clock: esto no parece "
            "simulacion.",
            f"En el carro fisico /{robot}/odom es odometria de verdad, con "
            "deriva acumulada,",
            "y compararla contra una pose de mundo no mide la condicion "
            "inicial. No opino."]

    real = (od.pose.pose.position.x, od.pose.pose.position.y,
            _yaw(od.pose.pose.orientation))
    creida = None
    if am is not None:
        creida = (am.pose.pose.position.x, am.pose.pose.position.y,
                  _yaw(am.pose.pose.orientation))

    r = evaluar_desvios(
        (float(esperada["x"]), float(esperada["y"]), float(esperada["yaw"])),
        real, creida)

    lineas = [
        f"Condicion inicial de {robot}",
        f"  declarada (POSE_INICIAL) : ({esperada['x']:.3f}, "
        f"{esperada['y']:.3f}, {math.degrees(float(esperada['yaw'])):.1f} "
        f"grados)",
        f"  real (/{robot}/odom)     : ({real[0]:.3f}, {real[1]:.3f}, "
        f"{math.degrees(real[2]):.1f} grados)"]

    if creida is None:
        lineas += [
            f"  creida (/{robot}/amcl_pose): no llego ninguna.",
            "",
            "NO OPINO. Sin la creencia de AMCL no se puede medir el error de",
            "localizacion, que es lo que decide el criterio 1. Comprobar que",
            f"amcl este vivo: ros2 topic info /{robot}/amcl_pose -v",
            "",
            f"Solo como dato: el robot esta a {r['desviacion_m']:.3f} m y "
            f"{r['desviacion_yaw_grados']:.1f} grados de la tabla de spawn,",
            "que NO es el criterio (ver la cabecera de este archivo)."]
        return r, lineas

    lineas += [
        f"  creida (/{robot}/amcl_pose): ({creida[0]:.3f}, {creida[1]:.3f}, "
        f"{math.degrees(creida[2]):.1f} grados)",
        f"  error de localizacion    : {r['error_localizacion_m']:.3f} m, "
        f"{r['error_localizacion_yaw_grados']:.1f} grados   <- el criterio",
        f"  desvio vs tabla de spawn : {r['desviacion_m']:.3f} m, "
        f"{r['desviacion_yaw_grados']:.1f} grados   (informativo)"]

    if r["dentro"]:
        lineas.append(f"\nOK: AMCL sabe donde esta el robot dentro de "
                      f"{TOLERANCIA_M} m y {TOLERANCIA_YAW_GRADOS} grados.")
    else:
        lineas += [
            f"\nCONDICION INICIAL CONTAMINADA "
            f"(limite {TOLERANCIA_M} m / {TOLERANCIA_YAW_GRADOS} grados).",
            f"AMCL se cree a {r['error_localizacion_m']:.3f} m y "
            f"{r['error_localizacion_yaw_grados']:.1f} grados de donde el robot",
            "esta de verdad. Cualquier error de llegada medido asi lleva dentro",
            "este sesgo y no se puede atribuir ni al controlador ni al pasillo.",
            "",
            "Que mirar, en este orden:",
            "  1. CUANTO LLEVA ESTE ROBOT QUIETO. Es la causa habitual: resbala",
            "     ~17 mm/min aunque nadie lo mande y AMCL no lo corrige hasta",
            "     acumular 25 cm, asi que a los ~9 min ya se sale de los "
            f"{TOLERANCIA_M} m.",
            "     Relanzar y correr la mision enseguida, sin dejarlo reposando.",
            "  2. Si acaba de arrancar y ya sale desviado, entonces es el spawn:",
            "     en pila nueva AMCL se siembra con la declarada, asi que este",
            "     error y el desvio vs tabla son el mismo numero. Comprobar que",
            "     no se reuso el gzserver (§6.4 pide uno nuevo por mision) y",
            "     revisar verificar_pose_spawn.py.",
            "  3. Si el robot viene de otra mision, esto NO es motivo de descarte",
            "     por si solo: lo que importa es el numero de arriba, no lo lejos",
            "     que haya acabado del spawn."]

    return r, lineas


def main():
    argumentos = [a for a in sys.argv[1:] if a != "--json"]
    como_json = "--json" in sys.argv[1:]
    robots = argumentos or ["robot1"]

    lecturas = leer_estado(robots)

    por_robot = {}
    informe = []
    for r in robots:
        od, am, hay_clock = lecturas[r]
        por_robot[r], lineas = _evaluar(r, od, am, hay_clock)
        informe.append("\n".join(lineas))

    # El criterio 1 pide los DOS dentro. Un solo robot fuera basta para que la
    # corrida haya que descartarla, asi que el codigo de salida es el AND.
    todos_dentro = all(e["dentro"] is True for e in por_robot.values())

    if como_json:
        # 'criterio' describe al registro entero, no a cada robot, asi que se
        # saca de las entradas y se escribe una sola vez. La funcion pura si lo
        # devuelve por robot -es lo que ella aplica-, pero repetirlo N veces en
        # el archivo seria decir N veces lo mismo, y el esquema tiene
        # additionalProperties:false en la entrada por robot.
        for e in por_robot.values():
            e.pop("criterio", None)
        json.dump({"criterio": "localizacion",
                   "tolerancia_m": TOLERANCIA_M,
                   "tolerancia_yaw_grados": TOLERANCIA_YAW_GRADOS,
                   "por_robot": por_robot}, sys.stdout)
        sys.stdout.write("\n")
    else:
        print("\n\n".join(informe))

    return 0 if todos_dentro else 1


if __name__ == "__main__":
    sys.exit(main())
