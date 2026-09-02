#!/usr/bin/env python3
"""Teleoperacion del DeepRacer fisico con un mando (Nintendo Switch Pro).

Se ejecuta EN EL VEHICULO. Ver GUIA_TELEOP_MANDO.md.

POR QUE LA LOGICA ESTA EN FUNCIONES SUELTAS
-------------------------------------------
`escalar`, `decidir` y `salida` no tocan ROS ni el nodo: reciben numeros y
devuelven numeros. Eso permite probarlas con `prueba_teleop_mando.py`, que corre
sin ROS, sin mando y sin carro -y por tanto tambien corre EN el carro-.

No es cosmetica. `salida` es el hombre muerto, y el hombre muerto es lo unico
que separa "se solto el mando" de "un vehiculo de 4 m/s acelerando solo en un
pasillo con gente". Comprobarlo empujando el carro en alto (Parte 6 de la guia)
prueba UNA vez el caso facil; la prueba cubre los bordes -el instante justo del
vencimiento, el arranque en frio, el gatillo sin estrenar- que a mano no se
reproducen.

El programa se copia al carro con un solo `scp`, asi que todo vive en este
fichero a proposito: partirlo en dos obligaria a copiar dos y fallaria con un
`ImportError` en el sitio menos oportuno.
"""

import signal
import sys
import time
from typing import NamedTuple

# ROS se importa de forma tolerante para que las funciones puras de abajo se
# puedan importar y probar en una maquina sin ROS. `main` comprueba de verdad
# que este, y si falta lo dice con los dos `source` que hacen falta en vez de
# soltar un traceback.
try:
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from rclpy.signals import SignalHandlerOptions
    from sensor_msgs.msg import Joy

    from deepracer_interfaces_pkg.msg import ServoCtrlMsg

    HAY_ROS = True
    FALLO_ROS = None
except ImportError as e:  # pragma: no cover - depende del entorno
    HAY_ROS = False
    FALLO_ROS = e
    Node = object

    class ExternalShutdownException(Exception):
        pass


class SalidaSolicitada(Exception):
    """Alguien pidio parar con una senal.

    Existe para que `rclpy.spin` se desenrede y el `finally` corra CON EL
    CONTEXTO DE ROS TODAVIA VIVO. Si en vez de esto se dejara morir el proceso,
    los diez ceros de despedida no llegarian a publicarse.
    """


def _atender_senal(numero, _marco):  # pragma: no cover - necesita proceso real
    raise SalidaSolicitada(signal.Signals(numero).name)

TOPICO_SERVO = "/ctrl_pkg/servo_msg"
TOPICO_JOY = "/joy"


class Ajustes(NamedTuple):
    """Todo lo que cambia el comportamiento, en un solo sitio.

    Los valores por defecto son los del Switch Pro tal como lo publica
    `joy_node`. ZR y ZL no llegan como botones sino como ejes analogicos: +1.0
    en reposo, -1.0 pulsados a fondo. Un gatillo que no se ha tocado desde que
    arranco `joy_node` puede leerse 0.0, y con el umbral NEGATIVO eso cuenta
    como "sin pulsar", que es el lado seguro.

    Los cuatro indices y las dos banderas estan MEDIDOS sobre el vehiculo el
    2026-09-01, no supuestos: el mando por USB al carro, `joy_node` como root,
    y un control a la vez. El gatillo sin estrenar leyendose 0.0 no es una
    hipotesis defensiva; ocurrio en esa misma medicion.

    `invertir_traccion` esta en False porque se comprobo que throttle POSITIVO
    mueve el vehiculo hacia adelante, publicando valores conocidos sin el mando
    de por medio y con las ruedas en el aire. Con la bandera en True el stick
    hacia adelante daba marcha atras.
    """

    eje_traccion: int = 1
    eje_direccion: int = 2
    eje_habilitar: int = 5
    eje_turbo: int = 4
    umbral_gatillo: float = -0.5
    limite_normal: float = 0.35
    limite_turbo: float = 0.70
    limite_direccion: float = 1.0
    zona_muerta: float = 0.12
    invertir_traccion: bool = False
    invertir_direccion: bool = False


def ejes_necesarios(aj):
    """Cuantos ejes tiene que publicar el mando para esta configuracion."""
    return max(aj.eje_traccion, aj.eje_direccion,
               aj.eje_habilitar, aj.eje_turbo) + 1


def escalar(valor, zona_muerta):
    """Aplica zona muerta y reescala para que el recorrido util sea continuo.

    Sin el reescalado el mando saltaria de 0 al valor de la zona muerta en
    cuanto se supera el umbral, que en un vehiculo de 4 m/s es un tiron.
    """
    if abs(valor) < zona_muerta:
        return 0.0
    signo = 1.0 if valor > 0 else -1.0
    return signo * (abs(valor) - zona_muerta) / (1.0 - zona_muerta)


def decidir(ejes, aj):
    """De la lista de ejes del mando a (habilitado, angulo, traccion).

    Devuelve ceros -y `habilitado` en falso- ante cualquier duda: mando que
    publica menos ejes de los que hacen falta, o gatillo de habilitacion sin
    pulsar. Nunca conserva el valor anterior.
    """
    if len(ejes) < ejes_necesarios(aj):
        return False, 0.0, 0.0

    if not ejes[aj.eje_habilitar] < aj.umbral_gatillo:
        return False, 0.0, 0.0

    turbo = ejes[aj.eje_turbo] < aj.umbral_gatillo
    limite = aj.limite_turbo if turbo else aj.limite_normal

    traccion = escalar(ejes[aj.eje_traccion], aj.zona_muerta)
    direccion = escalar(ejes[aj.eje_direccion], aj.zona_muerta)

    if aj.invertir_traccion:
        traccion = -traccion
    if aj.invertir_direccion:
        direccion = -direccion

    return (True,
            max(-1.0, min(1.0, direccion * aj.limite_direccion)),
            max(-1.0, min(1.0, traccion * limite)))


def salida(habilitado, angulo, traccion, t_ahora, t_ultimo_joy, timeout_s):
    """Lo que se publica de verdad. Aqui vive el hombre muerto.

    La parada por vencimiento tiene que decidirse en el temporizador y NO al
    recibir un `/joy`: si `/joy` deja de llegar -mando apagado, wifi caido,
    `joy_node` muerto- nadie ejecutaria el callback, y el vehiculo conservaria
    el ultimo valor. O sea que el caso peligroso es justo aquel en el que el
    codigo del callback no corre.

    Arrancar con `t_ultimo_joy = 0.0` deja esto vencido desde el primer
    instante, porque `time.monotonic()` cuenta desde el arranque de la maquina:
    hasta que llegue el primer mensaje del mando se publican ceros.
    """
    if not habilitado or (t_ahora - t_ultimo_joy) > timeout_s:
        return 0.0, 0.0
    return angulo, traccion


class TeleopMando(Node):
    def __init__(self):
        super().__init__("teleop_mando")

        por_defecto = Ajustes()
        for campo, valor in por_defecto._asdict().items():
            self.declare_parameter(campo, valor)
        self.declare_parameter("timeout_s", 0.6)
        self.declare_parameter("frecuencia_hz", 20.0)

        self.aj = Ajustes(**{campo: self.get_parameter(campo).value
                             for campo in por_defecto._asdict()})
        self.timeout_s = self.get_parameter("timeout_s").value
        frecuencia = self.get_parameter("frecuencia_hz").value

        self.pub = self.create_publisher(ServoCtrlMsg, TOPICO_SERVO, 1)
        self.create_subscription(Joy, TOPICO_JOY, self._al_recibir_joy, 1)

        self.angulo = 0.0
        self.traccion = 0.0
        self.habilitado = False
        self.t_ultimo_joy = 0.0
        self.aviso_dado = False

        self.create_timer(1.0 / frecuencia, self._publicar)

        self.get_logger().info(
            f"Teleop de mando activo. Manten pulsado el gatillo del eje "
            f"{self.aj.eje_habilitar} (ZR) para conducir; el eje "
            f"{self.aj.eje_turbo} (ZL) es turbo. "
            f"Limites: {self.aj.limite_normal} / {self.aj.limite_turbo}.")

    def _al_recibir_joy(self, msg):
        self.t_ultimo_joy = time.monotonic()

        if len(msg.axes) < ejes_necesarios(self.aj) and not self.aviso_dado:
            self.get_logger().error(
                f"El mando publica {len(msg.axes)} ejes, insuficientes para la "
                f"configuracion actual, que necesita al menos "
                f"{ejes_necesarios(self.aj)}. Revisa los indices con "
                f"'ros2 topic echo /joy'.")
            self.aviso_dado = True

        self.habilitado, self.angulo, self.traccion = decidir(
            list(msg.axes), self.aj)

    def _publicar(self):
        angulo, traccion = salida(self.habilitado, self.angulo, self.traccion,
                                  time.monotonic(), self.t_ultimo_joy,
                                  self.timeout_s)
        msg = ServoCtrlMsg()
        msg.angle = float(angulo)
        msg.throttle = float(traccion)
        self.pub.publish(msg)

    def parar(self):
        """Diez ceros de despedida. Devuelve si de verdad salieron.

        Diez y no uno porque un solo mensaje se puede perder: el perfil de QoS
        es BEST_EFFORT y la profundidad de cola 1.

        No puede lanzar excepcion. Si el contexto de ROS ya esta cerrado
        -pasa cuando la parada viene de fuera- publicar revienta con
        `RCLError: publisher's context is invalid`, y un traceback aqui es la
        peor respuesta posible: oculta que el vehiculo puede haberse quedado
        con el ultimo valor de traccion. Se avisa en castellano y se sigue.
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


def main():
    if not HAY_ROS:
        print(f"ERROR: no se pudo importar ROS o los mensajes del DeepRacer:",
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

    # POR QUE SE LE QUITAN LAS SENALES A rclpy
    # ----------------------------------------
    # Los diez ceros de despedida son la proteccion 3 de la guia. NO FUNCIONABAN
    # en la salida normal, y se midio el 2026-09-01 mandando la senal al proceso
    # de Python -no al bash que lo lanza, que fue el error del primer intento-:
    # con Ctrl-C llegaban CERO mensajes despues de la senal.
    #
    # La causa: `rclpy.init()` instala su propio manejador de SIGINT y SIGTERM a
    # nivel de C, que cierra el contexto ANTES de que el `finally` de aqui corra.
    # Para cuando se llama a `parar`, publicar revienta con
    # `publisher's context is invalid`. O sea que el vehiculo se quedaba con el
    # ultimo valor de traccion justo en la forma documentada de apagarlo.
    #
    # Con NO, las senales son nuestras: el manejador desenreda `spin`, el
    # `finally` corre con el contexto vivo, y los ceros salen de verdad.
    #
    # SIGHUP entra en la lista porque el programa se arranca por SSH (Terminal 3
    # de la guia): si la sesion se cae -wifi, portatil suspendido, terminal
    # cerrada- llega SIGHUP. Y el hombre muerto NO cubre ese caso, que es justo
    # lo que lo hace peligroso: el hombre muerto vive DENTRO del proceso, asi
    # que un proceso muerto no para nada.
    for senal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(senal, _atender_senal)

    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    nodo = TeleopMando()
    codigo = 0
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, SalidaSolicitada):
        pass
    except ExternalShutdownException:
        # El contexto ya esta cerrado desde fuera: `parar` no podra publicar y
        # lo dira. Se marca la salida como anormal para que no pase por buena.
        codigo = 1
    finally:
        if not nodo.parar():
            codigo = 1
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
