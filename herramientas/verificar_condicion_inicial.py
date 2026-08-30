#!/usr/bin/env python3
"""Comprueba que el robot este AHORA MISMO donde dice la tabla de spawn.

No es lo mismo que verificar_pose_spawn.py, y la diferencia importa. Aquel
comprueba en frio que la pose CONFIGURADA caiga en sitio libre del mapa; este
comprueba en vivo que el vehiculo ESTE ahi. Una pose configurada impecable y un
robot que no esta en ella son perfectamente compatibles, y es lo que pasa.

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

LA CONSECUENCIA OPERATIVA, QUE ES LO QUE HAY QUE RECORDAR
---------------------------------------------------------
La desviacion no depende de la mision: depende del TIEMPO QUE LA PILA LLEVA
QUIETA. Con la tolerancia de 0.15 m de aqui abajo, una pila recien levantada la
respeta y a los ~9 minutos ya no. Asi que esta comprobacion NO se hace una vez
tras el lanzamiento y se da por buena para toda la tarde: se hace JUSTO ANTES
de cada mision, y entre que la pila esta lista y la mision arranca se pierde el
menor tiempo posible. Dos misiones "identicas" lanzadas con diez minutos de
diferencia no parten de la misma condicion inicial.

Esto es tambien del mismo orden de magnitud que los errores de llegada que se
venian atribuyendo a la observabilidad del pasillo (sigma_x 0.704 m contra
sigma_y 0.186 m), asi que mientras no se descarte NO se puede afirmar cual de
las dos causas manda.

Uso:
    python3 herramientas/verificar_condicion_inicial.py robot1

Codigo de salida: 0 si el robot esta en su pose declarada, 1 si no.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Robot", "aws-deepracer", "deepracer_bringup", "launch"))

import rclpy
from deepracer_raiz_repo import pose_por_defecto
from nav_msgs.msg import Odometry
from rclpy.node import Node

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


def leer_odom(robot, segundos=5.0):
    """Devuelve (ultima muestra de /<robot>/odom o None, hay_clock).

    'hay_clock' cuenta PUBLICADORES, no suscriptores: 'ros2 topic list' lista
    /clock aunque solo lo escuchen los nodos con use_sim_time, asi que la
    pregunta util es si alguien lo escribe. Es la misma trampa que ya se
    documento en grabar_mision.sh (guarda 1).
    """
    rclpy.init()
    nodo = Node("verificador_de_condicion_inicial")
    muestras = []
    nodo.create_subscription(
        Odometry, f"/{robot}/odom", lambda m: muestras.append(m), 10)
    fin = nodo.get_clock().now().nanoseconds * 1e-9 + segundos
    while rclpy.ok() and nodo.get_clock().now().nanoseconds * 1e-9 < fin:
        rclpy.spin_once(nodo, timeout_sec=0.1)
        if len(muestras) > 20:
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
    reloj = f"/{robot}/clock"
    if nodo.count_publishers(reloj) == 0:
        reloj = "/clock"
    hay_clock = nodo.count_publishers(reloj) > 0
    nodo.destroy_node()
    rclpy.shutdown()
    return (muestras[-1] if muestras else None), hay_clock


def main():
    robot = sys.argv[1] if len(sys.argv) > 1 else "robot1"

    try:
        esperada = pose_por_defecto(robot)
    except Exception as e:
        print(f"No hay pose declarada para '{robot}': {e}")
        return 1

    od, hay_clock = leer_odom(robot)
    if od is None:
        print(f"No llego ni una muestra de /{robot}/odom.")
        print("O la simulacion no esta arriba, o este proceso esta en otro "
              "ROS_DOMAIN_ID. Desde el 2026-08-30 los dos robots comparten el "
              "dominio 0, que es el defecto de ROS 2: una terminal sin exportar "
              "nada deberia verlos a los dos.")
        return 1

    # Sin /clock esto no es simulacion, y entonces /odom SI es odometria: lleva
    # deriva acumulada y comparar su valor absoluto contra una pose de mundo no
    # significa nada. El script prefiere callarse a dar un veredicto falso.
    if not hay_clock:
        print(f"Nadie publica /{robot}/clock ni /clock: esto no parece "
              "simulacion.")
        print(f"En el carro fisico /{robot}/odom es odometria de verdad, con "
              "deriva acumulada,")
        print("y compararla contra una pose de mundo no mide la condicion "
              "inicial. No opino.")
        return 1

    real_x = od.pose.pose.position.x
    real_y = od.pose.pose.position.y
    real_yaw = math.degrees(_yaw(od.pose.pose.orientation))
    esp_yaw = math.degrees(float(esperada["yaw"]))

    d = math.hypot(real_x - float(esperada["x"]), real_y - float(esperada["y"]))
    dyaw = abs(_normalizar_grados(real_yaw - esp_yaw))

    print(f"Condicion inicial de {robot}")
    print(f"  declarada (POSE_INICIAL): ({esperada['x']:.3f}, "
          f"{esperada['y']:.3f}, {esp_yaw:.1f} grados)")
    print(f"  real (/{robot}/odom)     : ({real_x:.3f}, {real_y:.3f}, "
          f"{real_yaw:.1f} grados)")
    print(f"  desviacion               : {d:.3f} m, {dyaw:.1f} grados")

    ok_pos = d <= TOLERANCIA_M
    ok_yaw = dyaw <= TOLERANCIA_YAW_GRADOS
    if ok_pos and ok_yaw:
        print(f"\nOK: dentro de {TOLERANCIA_M} m y {TOLERANCIA_YAW_GRADOS} "
              f"grados. AMCL nace sembrada donde el robot esta.")
        return 0

    print(f"\nCONDICION INICIAL CONTAMINADA "
          f"(limite {TOLERANCIA_M} m / {TOLERANCIA_YAW_GRADOS} grados).")
    print("AMCL se siembra con la pose DECLARADA, no con la real, asi que")
    print(f"nace creyendose a {d:.3f} m y {dyaw:.1f} grados de donde esta.")
    print("Cualquier error de llegada medido asi lleva dentro este sesgo y no")
    print("se puede atribuir ni al controlador ni al pasillo.")
    print("")
    print("Que mirar, en este orden:")
    print("  1. CUANTO LLEVA LA PILA LEVANTADA. Es la causa habitual: el carro")
    print(f"     resbala ~17 mm/min aunque nadie lo mande, asi que a los ~9 min")
    print(f"     ya se sale de los {TOLERANCIA_M} m. Relanzar y correr la mision")
    print("     enseguida, sin dejar la simulacion reposando.")
    print("  2. Si acaba de arrancar y ya sale desviado, entonces si es el")
    print("     spawn: comprobar que no se reuso el gzserver de otra corrida")
    print("     (§6.4 pide uno nuevo por mision) y revisar verificar_pose_spawn.py.")
    print("")
    print(f"Nota: {d:.3f} m / {dyaw:.1f} grados es la desviacion REAL del carro.")
    print("El error que ve Nav2 puede ser aun mayor, porque AMCL solo corrige")
    print("cada 0.25 m o 0.2 rad y una deriva tan lenta no cruza ese umbral.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
