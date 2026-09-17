#!/usr/bin/env python3
"""Sostiene un 'throttle' FIJO el tiempo que se le diga. Calibra la escala (RF-14).

Se ejecuta EN EL VEHICULO, igual que teleop_mando.py y por la misma razon de
seguridad (§6.3 de S20_frente_b_hardware.md): si esto corriera por red y el wifi
cayera, 'servo_pkg' se quedaria con el ultimo valor y quedaria un vehiculo
acelerando sin nadie al mando.

    scp herramientas/sostener_traccion.py deepracer@<IP>:~/      # desde el portatil
    sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~deepracer/sostener_traccion.py --throttle 0.15'

QUE PROBLEMA RESUELVE
---------------------
El Bloque 7 de HOJA_CAMPO_G2.md mide cuanta velocidad real da un 'throttle'
dado, que es lo unico que mantiene RF-14 en amarillo: los tres umbrales de
'cmdvel_to_servo_pkg/constants.py' cuelgan de un 'MAX_SPEED = 4,0 m/s' heredado
de AWS, y si el carro real no hace 4 m/s la tabla entera esta corrida.

Pero el §10.3 de esa hoja dice, textualmente, que con el mando sale una NUBE y
no una tabla: 'teleop_mando.py' escala el gatillo de forma continua, asi que
sostener un valor a mano es imposible. Y lo remata: "la tabla fina de escalones
sostenidos necesita un nodo que publique un valor fijo con hombre muerto, y eso
es codigo que hoy no existe". Esto es ese codigo.

LA FORMA DE LA CORRIDA, Y POR QUE ES ESA
----------------------------------------
    quietud | tramo | tramo | ... | quietud

Las dos ventanas de quietud son las mismas que usa 'medir_g2.py' para decidir
quieto/movido, asi que el analisis ya sabe leerlas sin tocar nada. En medio van
uno o varios tramos de 'throttle' constante.

Con un solo '--throttle' sale un escalon. Con '--rampa' salen muchos, y ese es
el modo que contesta la pregunta que la hoja declara mas importante de todas
-"si solo da tiempo a una cosa, que sea el punto 1"-: DONDE EMPIEZA A MOVERSE EL
CARRO. Se lanza la rampa, se mira el carro, y el valor que estaba en pantalla
cuando arranco es la respuesta. Ese numero decide si 0,05 m/s es siquiera
alcanzable, y hoy no existe en ningun documento.

EL ANGULO ES SIEMPRE CERO, Y NO ES UN OLVIDO
--------------------------------------------
El mensurando es velocidad sobre una recta. Un angulo distinto de cero curva la
trayectoria y contamina justo lo que se mide, asi que no se ofrece la opcion.

LO QUE ESTE PROGRAMA NO PUEDE PROTEGER
--------------------------------------
El hombre muerto de 'teleop_mando.py' existe porque alli hay una fuente externa
-el mando- que puede callarse. Aqui la fuente es el reloj, y no se calla: cada
tick recalcula la salida desde 'time.monotonic()', asi que un tick tardio se
corrige solo y la corrida no puede durar mas de lo pedido.

Lo que queda fuera del alcance de cualquier codigo: si el proceso se detiene
-SIGSTOP, la maquina se atasca- nadie publica y 'servo_pkg' conserva el ultimo
valor. Por eso los topes de '--tope' y de duracion son duros, y por eso la
parada real sigue siendo el interruptor del vehiculo.

USO
    python3 sostener_traccion.py --throttle 0.15 [--marcha 6] [--quietud 5]
    python3 sostener_traccion.py --rampa 0.04:0.30:0.02 [--marcha 2]

La logica sin ROS se prueba en el portatil con 'prueba_sostener_traccion.py'.
"""

import argparse
import math
import signal
import sys
import time
from typing import NamedTuple

try:
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from rclpy.signals import SignalHandlerOptions

    from deepracer_interfaces_pkg.msg import ServoCtrlMsg

    HAY_ROS = True
    FALLO_ROS = None
except ImportError as e:  # pragma: no cover - depende del entorno
    HAY_ROS = False
    FALLO_ROS = e
    Node = object

    class ExternalShutdownException(Exception):
        pass


TOPICO_SERVO = "/ctrl_pkg/servo_msg"

# El mismo techo que 'teleop_mando.py' llama 'limite_normal', y no es un numero
# elegido aqui: es el recorrido util con el que se condujo el vehiculo el
# 2026-09-01. Subirlo a mano en un barrido de calibracion es como se lanza un
# carro contra una pared.
TOPE_POR_DEFECTO = 0.35
# Un tramo no puede durar mas que esto. A 0,5 m/s son 10 m, y la recta de ensayo
# mide 20 m: de sobra para varias ventanas de 1 s sin salirse de las marcas.
TOPE_TRAMO_S = 20.0
# Ni la suma de todos. Cota dura contra un '--rampa' con el paso mal puesto, que
# es el error de dedo que deja al carro rodando minutos.
TOPE_MARCHA_TOTAL_S = 60.0


class SalidaSolicitada(Exception):
    """Alguien pidio parar con una senal. Igual que en teleop_mando.py: existe
    para que el 'finally' corra con el contexto de ROS todavia vivo, que es lo
    unico que permite publicar los ceros de despedida."""


def _atender_senal(numero, _marco):  # pragma: no cover - necesita proceso real
    raise SalidaSolicitada(signal.Signals(numero).name)


class Plan(NamedTuple):
    throttles: tuple
    marcha_s: float
    quietud_s: float


def rampa(desde, hasta, paso):
    """Los valores de una rampa, incluido el extremo si cae justo.

    Se construye sumando enteros y no acumulando flotantes: acumular hace que
    0,04 + 0,02 siete veces no de 0,18 exacto, y entonces el valor que sale por
    pantalla no es el que se publica -que es precisamente el numero que esta
    corrida va a buscar-.

    Se trunca hacia abajo, no se redondea. Con 'round' una rampa cuyo paso no
    divide al intervalo se pasa del extremo pedido -0,10:0,25:0,04 publicaba
    0,26-, y el extremo lo escribe el operador como su techo. Truncar deja el
    ultimo tramo por debajo, que es el lado seguro. El 1e-9 es para que un
    intervalo que SI divide justo no se coma su ultimo valor por el error de
    coma flotante de la division.
    """
    if paso <= 0:
        return ()
    cuantos = math.floor((hasta - desde) / paso + 1e-9)
    return tuple(round(desde + i * paso, 6) for i in range(cuantos + 1))


def validar(throttles, marcha_s, quietud_s, tope):
    """Todo lo que impide sacar el carro, en una lista. Vacia es que se puede."""
    problemas = []
    if not throttles:
        problemas.append("no hay ningun tramo que publicar")
    for th in throttles:
        if th <= 0:
            problemas.append(
                f"throttle {th}: solo se calibra hacia adelante, y un valor "
                "nulo o negativo no mide nada")
            break
    altos = [th for th in throttles if th > tope]
    if altos:
        problemas.append(
            f"throttle {max(altos)} pasa del tope {tope}. Si de verdad hace "
            "falta, subelo a conciencia con --tope")
    if not 0 < marcha_s <= TOPE_TRAMO_S:
        problemas.append(
            f"--marcha {marcha_s} fuera de (0, {TOPE_TRAMO_S}] s")
    if quietud_s < 0:
        problemas.append(f"--quietud {quietud_s} no puede ser negativa")
    total = marcha_s * len(throttles)
    if total > TOPE_MARCHA_TOTAL_S:
        problemas.append(
            f"la corrida mueve el carro {total:.0f} s en total, y el tope son "
            f"{TOPE_MARCHA_TOTAL_S:.0f} s. Parte el barrido en dos")
    return problemas


def segmentos(plan):
    """La corrida entera como [(duracion, throttle, fase)], en orden."""
    segs = [(plan.quietud_s, 0.0, "quieto_inicial")]
    for th in plan.throttles:
        segs.append((plan.marcha_s, th, "marcha"))
    segs.append((plan.quietud_s, 0.0, "quieto_final"))
    return segs


def salida(segs, t_rel):
    """Lo que se publica en el instante t_rel, contado desde que arranca la corrida.

    Antes de empezar y despues de terminar devuelve cero. Que el caso 'fin' sea
    cero y no 'el ultimo valor' es lo que hace que un tick tardio, o un reloj
    que salta, no dejen el carro acelerando.
    """
    if t_rel < 0:
        return 0.0, "cuenta_atras"
    acumulado = 0.0
    for duracion, throttle, fase in segs:
        acumulado += duracion
        if t_rel < acumulado:
            return throttle, fase
    return 0.0, "fin"


class SostenerTraccion(Node):
    def __init__(self, plan, cuenta_atras_s, frecuencia_hz=20.0):
        super().__init__("sostener_traccion")
        self.segs = segmentos(plan)
        self.pub = self.create_publisher(ServoCtrlMsg, TOPICO_SERVO, 1)
        self.t_cero = time.monotonic() + cuenta_atras_s
        self.fase_anterior = None
        self.terminado = False
        self.create_timer(1.0 / frecuencia_hz, self._publicar)

    def _publicar(self):
        throttle, fase = salida(self.segs, time.monotonic() - self.t_cero)

        if fase != self.fase_anterior:
            # El sello es time.time() -no monotonic- porque es el reloj con el
            # que rosbag2 fecha los mensajes: asi esta traza y el bag de servo
            # se emparejan aunque uno de los dos se pierda.
            print(f"[{time.time():.3f}] {fase:15s} throttle={throttle:.3f}",
                  flush=True)
            self.fase_anterior = fase

        msg = ServoCtrlMsg()
        msg.angle = 0.0
        msg.throttle = float(throttle)
        self.pub.publish(msg)

        if fase == "fin":
            self.terminado = True
            raise SalidaSolicitada("corrida completa")

    def parar(self):
        """Diez ceros de despedida. Devuelve si de verdad salieron.

        Copiado a proposito de teleop_mando.py, incluido el tragarse la
        excepcion: un traceback aqui ocultaria que el vehiculo puede haberse
        quedado con el ultimo valor de traccion.
        """
        msg = ServoCtrlMsg()
        msg.angle = 0.0
        msg.throttle = 0.0
        for _ in range(10):
            try:
                self.pub.publish(msg)
            except Exception as e:  # noqa: BLE001 - aqui tragar es lo correcto
                print("", file=sys.stderr)
                print("AVISO: NO se pudieron publicar los ceros de parada.",
                      file=sys.stderr)
                print(f"       {type(e).__name__}: {e}", file=sys.stderr)
                print("       El vehiculo puede haberse quedado con el ultimo",
                      file=sys.stderr)
                print("       valor de traccion. APAGALO con el interruptor.",
                      file=sys.stderr)
                return False
            time.sleep(0.02)
        return True


def analizar_argumentos(argv=None):
    p = argparse.ArgumentParser(
        description="Sostiene un throttle fijo para calibrar la escala (RF-14).")
    grupo = p.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--throttle", type=float,
                       help="un solo escalon, p. ej. 0.15")
    grupo.add_argument("--rampa", type=str, metavar="DESDE:HASTA:PASO",
                       help="barrido, p. ej. 0.04:0.30:0.02")
    p.add_argument("--marcha", type=float, default=6.0,
                   help="segundos por tramo (por defecto 6; con --rampa pon 2)")
    p.add_argument("--quietud", type=float, default=5.0,
                   help="segundos quieto antes y despues (por defecto 5)")
    p.add_argument("--cuenta-atras", type=float, default=5.0,
                   help="segundos para apartarse antes de empezar")
    p.add_argument("--tope", type=float, default=TOPE_POR_DEFECTO,
                   help=f"throttle maximo admitido (por defecto {TOPE_POR_DEFECTO})")
    return p.parse_args(argv)


def main(argv=None):
    args = analizar_argumentos(argv)

    if args.rampa:
        try:
            desde, hasta, paso = (float(x) for x in args.rampa.split(":"))
        except ValueError:
            print("ERROR: --rampa se escribe DESDE:HASTA:PASO, con tres numeros.",
                  file=sys.stderr)
            return 2
        throttles = rampa(desde, hasta, paso)
    else:
        throttles = (args.throttle,)

    problemas = validar(throttles, args.marcha, args.quietud, args.tope)
    if problemas:
        print("ERROR: la corrida no sale por:", file=sys.stderr)
        for problema in problemas:
            print(f"  - {problema}", file=sys.stderr)
        return 2

    # El resumen se imprime ANTES de comprobar ROS a proposito: asi el barrido
    # se puede ensayar en el portatil -que no tiene ServoCtrlMsg- y ver cuanto
    # dura y que valores publica, en vez de descubrirlo en la recta.
    total = args.cuenta_atras + 2 * args.quietud + args.marcha * len(throttles)
    print(f"{len(throttles)} tramo(s) de {args.marcha:g} s: "
          f"{', '.join(f'{t:g}' for t in throttles)}")
    print(f"Quietud {args.quietud:g} s a cada lado. "
          f"Empieza en {args.cuenta_atras:g} s, dura {total:g} s en total.")

    if not HAY_ROS:
        print("", file=sys.stderr)
        print("ERROR: no se pudo importar ROS o los mensajes del DeepRacer:",
              file=sys.stderr)
        print(f"       {FALLO_ROS}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Este programa se ejecuta EN EL VEHICULO, y hacen falta DOS",
              file=sys.stderr)
        print("'source', no uno. El segundo es el que trae ServoCtrlMsg:",
              file=sys.stderr)
        print("  source /opt/ros/jazzy/setup.bash", file=sys.stderr)
        print("  source /opt/aws/deepracer/lib/setup.bash", file=sys.stderr)
        return 2

    plan = Plan(throttles, args.marcha, args.quietud)
    print("APARTATE DE LA RECTA. Ctrl-C para en el sitio.", flush=True)

    # Las senales son nuestras por la misma razon medida el 2026-09-01 en
    # teleop_mando.py: con el manejador de rclpy, el contexto se cierra antes de
    # que corra el 'finally' y los ceros de despedida NO se publican. SIGHUP
    # entra porque esto se arranca por SSH.
    for senal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(senal, _atender_senal)

    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    nodo = SostenerTraccion(plan, args.cuenta_atras)
    codigo = 0
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, SalidaSolicitada):
        pass
    except ExternalShutdownException:
        codigo = 1
    finally:
        if not nodo.parar():
            codigo = 1
        if not nodo.terminado:
            print("Corrida INTERRUMPIDA antes de tiempo: el bag vale, pero el "
                  "ultimo tramo esta incompleto.", file=sys.stderr)
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
