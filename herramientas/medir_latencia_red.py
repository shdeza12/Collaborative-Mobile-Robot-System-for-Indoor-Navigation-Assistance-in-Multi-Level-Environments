#!/usr/bin/env python3
"""RF-15: mide la latencia de ida y vuelta entre dos maquinas de la red.

POR QUE ESTO EXISTE, Y POR QUE ES DE IDA Y VUELTA
=================================================
RF-15 pide "los dos vehiculos y el coordinador se alcanzan por red con latencia
acotada", y su criterio dice literalmente "medida de ida y vuelta entre los dos
vehiculos". La ida y vuelta no es una comodidad: es la unica forma de medir esto
sin sincronizar relojes. El emisor pone SU marca de tiempo, el eco la devuelve
intacta, y el emisor resta contra SU propio reloj. El reloj de la otra maquina no
entra en la cuenta en ningun momento. Una medida de un solo sentido entre el
portatil (Humble) y la tarjeta del carro (Jazzy) mediria sobre todo el desfase
entre los dos relojes, que nadie ha sincronizado.

QUE NO NECESITA
===============
Nada del proyecto. Solo rclpy y std_msgs, que estan en /opt/ros/<distro>/ en las
dos distribuciones. Se copia el fichero suelto a la tarjeta y corre:

    scp herramientas/medir_latencia_red.py deepracer@<IP>:~/

Esto es deliberado. El segundo DeepRacer llega sin ningun workspace del proyecto
-el primero tampoco lo tenia el 2026-09-07- y compilar coordinacion_msgs en el
sitio para poder medir la red seria empezar la casa por el tejado.

COMO SE USA -- dos terminales, una en cada maquina
==================================================
En la maquina que responde (el eco):

    source /opt/ros/jazzy/setup.bash && python3 medir_latencia_red.py --rol eco

En la maquina que mide (el emisor):

    source /opt/ros/humble/setup.bash && python3 herramientas/medir_latencia_red.py \
        --rol emisor --n 600 --hz 10 --salida /tmp/rf15_portatil_robot1.json

El emisor termina solo. El eco se para con Ctrl-C.

LAS DOS MAQUINAS TIENEN QUE COMPARTIR ROS_DOMAIN_ID. Si una lo lleva puesto y la
otra no, no se ven, y el sintoma es cero pongs -indistinguible de un cortafuegos-.

LA TRAMPA QUE ESTA HERRAMIENTA SI DETECTA
=========================================
Que las dos mitades acaben en la MISMA maquina. Un `--rol eco` olvidado en una
pestaña del portatil hace que la medida salga preciosa -decimas de milisegundo,
memoria compartida- y no mida ninguna red. El eco anade su `hostname` al
`frame_id` antes de devolverlo, y el emisor compara: si el eco responde desde su
propio host, la salida dice MEDIDA_LOCAL y NO da veredicto.

LO QUE NO PRUEBA
================
Que un tipo del proyecto viaje bien -eso es coordinacion_msgs/test/prueba_round_trip.py-
ni que las acciones de Nav2 crucen entre distribuciones -eso sigue siendo R8-.
Mide el transporte: cuanto tarda y cuanto se pierde.
"""
import argparse
import json
import socket
import statistics
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header

TOPICO_PING = "/rf15/ping"
TOPICO_PONG = "/rf15/pong"

# El mismo perfil que usa coordinacion/agente.py para /<ns>/estado:
# create_publisher(EstadoRobot, TOPICO_ESTADO, 10) -> RELIABLE, KEEP_LAST(10).
# Medir con BEST_EFFORT daria numeros mas bonitos y no diria nada del trafico
# que el sistema manda de verdad.
PROFUNDIDAD = 10

# Relleno por omision. Un EstadoRobot serializado -robot_id, nivel, estado,
# detalle y una PoseWithCovarianceStamped completa- ronda los 300 bytes; una
# Header pelada no llega a 60. Se rellena para que el paquete se parezca al que
# de verdad circula, porque por debajo de la MTU el tamaño casi no pesa pero
# por encima si, y conviene saber de que lado estamos.
RELLENO_BYTES = 240

# CRITERIO PREINSCRITO -- fijado el 2026-09-11, ANTES de tener el primer dato,
# que es lo que exige el §6.3 del protocolo experimental.
#
# De donde sale el numero, y no es de la intuicion: el trafico periodico mas
# rapido del sistema es /robotN/estado, que RF-08 fija en 2 Hz y que se midio a
# 2,000 Hz el 2026-09-07. Son 500 ms de periodo. Si la latencia de UN SENTIDO
# llegara a 500 ms, cada mensaje llegaria cuando ya se publico el siguiente y la
# imagen que el coordinador tiene del robot estaria desfasada una muestra por
# construccion. Ese es el techo duro: 500 ms de ida = 1000 ms de ida y vuelta.
#
# Un criterio necesita margen sobre el techo, no rozarlo:
#   - mediana <= 100 ms de ida y vuelta  -> factor 10 sobre el techo
#   - p95     <= 250 ms de ida y vuelta  -> factor 4 sobre la cola
#   - perdida == 0 %
#
# La perdida es dura a proposito. El perfil es RELIABLE, o sea que DDS ya
# reintenta; un pong que aun asi no vuelve no es un paquete con mala suerte, es
# un enlace que no sostiene el trafico.
UMBRAL_MEDIANA_MS = 100.0
UMBRAL_P95_MS = 250.0

# Por debajo de esto no se da veredicto. Con 20 muestras el p95 es una sola
# muestra y llamarlo percentil es un adorno.
MINIMO_MUESTRAS = 100


def percentil(ordenados, p):
    """Percentil por el metodo del rango mas cercano. Sin numpy a proposito:
    la tarjeta del carro no lo tiene garantizado y esto no merece una
    dependencia."""
    if not ordenados:
        return None
    k = max(1, int(-(-p * len(ordenados) // 100)))  # ceil(p/100 * n)
    return ordenados[k - 1]


class Eco(Node):
    """Devuelve cada ping por /rf15/pong con la marca de tiempo INTACTA."""

    def __init__(self):
        super().__init__("rf15_eco")
        self.host = socket.gethostname()
        self.pub = self.create_publisher(Header, TOPICO_PONG, PROFUNDIDAD)
        self.create_subscription(Header, TOPICO_PING, self.rebotar, PROFUNDIDAD)
        self.n = 0
        self.get_logger().info(
            f"eco en '{self.host}': escuchando {TOPICO_PING}, "
            f"devolviendo por {TOPICO_PONG}. Ctrl-C para parar.")

    def rebotar(self, msg):
        salida = Header()
        # LA MARCA NO SE TOCA. Es el reloj del emisor y es lo unico que hace que
        # la medida no dependa de sincronizar relojes.
        salida.stamp = msg.stamp
        # Se firma el eco con el host, para que el emisor pueda descubrir que se
        # esta respondiendo a si mismo.
        salida.frame_id = f"{msg.frame_id}|eco={self.host}"
        self.pub.publish(salida)
        self.n += 1
        if self.n % 100 == 0:
            self.get_logger().info(f"{self.n} rebotados")


class Emisor(Node):
    def __init__(self, n, hz, relleno):
        super().__init__("rf15_emisor")
        self.host = socket.gethostname()
        self.objetivo = n
        self.periodo = 1.0 / hz
        self.relleno = "x" * relleno
        self.pub = self.create_publisher(Header, TOPICO_PING, PROFUNDIDAD)
        self.create_subscription(Header, TOPICO_PONG, self.recibir, PROFUNDIDAD)
        self.enviado_en = {}      # seq -> t_envio (reloj monotono local)
        self.rtt_ms = {}          # seq -> ida y vuelta en ms
        self.ecos = set()         # hostnames que han respondido
        self.duplicados = 0
        self.desconocidos = 0
        self.seq = 0

    def enviar_uno(self):
        self.seq += 1
        m = Header()
        ahora = self.get_clock().now()
        m.stamp = ahora.to_msg()
        m.frame_id = f"seq={self.seq}|emisor={self.host}|{self.relleno}"
        self.enviado_en[self.seq] = time.monotonic()
        self.pub.publish(m)

    def recibir(self, msg):
        llegada = time.monotonic()
        seq = None
        eco = None
        for trozo in msg.frame_id.split("|"):
            if trozo.startswith("seq="):
                try:
                    seq = int(trozo[4:])
                except ValueError:
                    return
            elif trozo.startswith("eco="):
                eco = trozo[4:]
        if seq is None or seq not in self.enviado_en:
            self.desconocidos += 1
            return
        if seq in self.rtt_ms:
            self.duplicados += 1
            return
        if eco:
            self.ecos.add(eco)
        self.rtt_ms[seq] = (llegada - self.enviado_en[seq]) * 1000.0


def correr_emisor(args):
    rclpy.init()
    nodo = Emisor(args.n, args.hz, args.relleno)

    print(f"emisor en '{nodo.host}' -> {args.n} pings a {args.hz} Hz "
          f"({args.n / args.hz:.0f} s), carga util +{args.relleno} B")
    print("esperando 2 s a que el eco aparezca en el grafo...")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 2.0:
        rclpy.spin_once(nodo, timeout_sec=0.05)

    siguiente = time.monotonic()
    while nodo.seq < args.n:
        nodo.enviar_uno()
        siguiente += nodo.periodo
        while time.monotonic() < siguiente:
            rclpy.spin_once(nodo, timeout_sec=0.005)

    # Cola de gracia: un pong puede seguir en vuelo cuando se manda el ultimo
    # ping. Sin esta espera el ultimo puñado se contaria como perdido.
    print("enviados todos; esperando 2 s a los pongs en vuelo...")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 2.0:
        rclpy.spin_once(nodo, timeout_sec=0.05)

    informe = analizar(nodo, args)
    nodo.destroy_node()
    rclpy.shutdown()

    imprimir(informe)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump(informe, f, indent=2, ensure_ascii=False)
        print(f"\nescrito {args.salida}")
    return 0 if informe["veredicto"] == "CUMPLE" else 1


def analizar(nodo, args):
    vals = sorted(nodo.rtt_ms.values())
    enviados = nodo.seq
    recibidos = len(vals)
    perdidos = enviados - recibidos

    informe = {
        "requisito": "RF-15",
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "emisor_host": nodo.host,
        "ecos_que_respondieron": sorted(nodo.ecos),
        "enviados": enviados,
        "recibidos": recibidos,
        "perdidos": perdidos,
        "perdida_pct": round(100.0 * perdidos / enviados, 3) if enviados else None,
        "duplicados": nodo.duplicados,
        "pongs_sin_ping_conocido": nodo.desconocidos,
        "hz_pedido": args.hz,
        "relleno_bytes": args.relleno,
        "umbral_mediana_ms": UMBRAL_MEDIANA_MS,
        "umbral_p95_ms": UMBRAL_P95_MS,
        "minimo_muestras": MINIMO_MUESTRAS,
        "etiqueta": args.etiqueta,
    }

    if vals:
        informe.update({
            "min_ms": round(vals[0], 3),
            "mediana_ms": round(statistics.median(vals), 3),
            "p95_ms": round(percentil(vals, 95), 3),
            "max_ms": round(vals[-1], 3),
        })
    else:
        informe.update({"min_ms": None, "mediana_ms": None,
                        "p95_ms": None, "max_ms": None})

    # El veredicto, en orden: primero las razones para NO dar veredicto.
    motivos = []
    if recibidos == 0:
        informe["veredicto"] = "SIN_DATOS"
        informe["motivo"] = ("no volvio ni un pong. Mira, en este orden: el eco "
                             "corriendo, el mismo ROS_DOMAIN_ID en las dos "
                             "maquinas, y ufw en LAS DOS")
        return informe
    if not nodo.ecos:
        informe["veredicto"] = "SIN_VEREDICTO"
        informe["motivo"] = ("volvieron pongs sin firma de eco: no es esta "
                             "herramienta la que responde, o es una version vieja")
        return informe
    if nodo.host in nodo.ecos:
        informe["veredicto"] = "MEDIDA_LOCAL"
        informe["motivo"] = (f"el eco respondio desde '{nodo.host}', la misma "
                             "maquina que mide. Esto no atravesó la red y no "
                             "vale para RF-15")
        return informe
    if recibidos < MINIMO_MUESTRAS:
        informe["veredicto"] = "SIN_VEREDICTO"
        informe["motivo"] = (f"solo {recibidos} muestras, menos de "
                             f"{MINIMO_MUESTRAS}. Con tan pocas, el p95 es una "
                             "muestra suelta")
        return informe

    if informe["mediana_ms"] > UMBRAL_MEDIANA_MS:
        motivos.append(f"mediana {informe['mediana_ms']} ms > {UMBRAL_MEDIANA_MS} ms")
    if informe["p95_ms"] > UMBRAL_P95_MS:
        motivos.append(f"p95 {informe['p95_ms']} ms > {UMBRAL_P95_MS} ms")
    if perdidos > 0:
        motivos.append(f"{perdidos} de {enviados} perdidos ({informe['perdida_pct']} %)")

    informe["veredicto"] = "CUMPLE" if not motivos else "NO_CUMPLE"
    informe["motivo"] = "; ".join(motivos) if motivos else (
        "mediana, p95 y perdida dentro del criterio preinscrito")
    return informe


def imprimir(inf):
    print("\n" + "=" * 66)
    print(f"RF-15 -- ida y vuelta  [{inf['etiqueta'] or 'sin etiqueta'}]")
    print("=" * 66)
    print(f"  emisor      : {inf['emisor_host']}")
    print(f"  eco         : {', '.join(inf['ecos_que_respondieron']) or '(ninguno)'}")
    print(f"  enviados    : {inf['enviados']}   recibidos: {inf['recibidos']}   "
          f"perdidos: {inf['perdidos']} ({inf['perdida_pct']} %)")
    if inf["duplicados"]:
        print(f"  duplicados  : {inf['duplicados']}")
    if inf["pongs_sin_ping_conocido"]:
        print(f"  pongs huerfanos: {inf['pongs_sin_ping_conocido']}")
    if inf["mediana_ms"] is not None:
        print(f"  ida y vuelta: min {inf['min_ms']} ms | mediana "
              f"{inf['mediana_ms']} ms | p95 {inf['p95_ms']} ms | max {inf['max_ms']} ms")
    print("-" * 66)
    print(f"  VEREDICTO   : {inf['veredicto']}")
    print(f"  {inf['motivo']}")
    print("=" * 66)


def main():
    ap = argparse.ArgumentParser(description="RF-15: latencia de ida y vuelta")
    ap.add_argument("--rol", required=True, choices=["eco", "emisor"])
    ap.add_argument("--n", type=int, default=600,
                    help="pings a enviar (emisor). Por omision 600")
    ap.add_argument("--hz", type=float, default=10.0,
                    help="ritmo de envio (emisor). Por omision 10")
    ap.add_argument("--relleno", type=int, default=RELLENO_BYTES,
                    help=f"bytes de relleno. Por omision {RELLENO_BYTES}")
    ap.add_argument("--salida", help="fichero JSON con el informe (emisor)")
    ap.add_argument("--etiqueta", default="",
                    help="que pareja se esta midiendo, p.ej. 'portatil<->robot2'")
    args = ap.parse_args()

    if args.rol == "eco":
        rclpy.init()
        nodo = Eco()
        try:
            rclpy.spin(nodo)
        except KeyboardInterrupt:
            print(f"\neco parado tras {nodo.n} rebotes")
        finally:
            nodo.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
        return 0

    if args.n < 1 or args.hz <= 0:
        print("--n y --hz tienen que ser positivos", file=sys.stderr)
        return 2
    return correr_emisor(args)


if __name__ == "__main__":
    sys.exit(main())
