#!/usr/bin/env python3
"""
Barre TODOS los pares ordenados de puntos de un nivel y le pregunta al
planificador global de Nav2 si existe camino entre ellos.

POR QUE ESTO Y NO 210 MISIONES. En el nivel 1 hay 15 puntos, o sea 210 pares
ordenados. Conducirlos de verdad son unas dos horas de simulacion, y ademas el
§6.4 del protocolo exige un gzserver nuevo por mision, asi que no seria una
tanda: serian 210 arranques. Esta herramienta no sustituye a conducir, hace de
CRIBA: descarta de golpe los pares que ni siquiera tienen camino y senala los
sospechosos para conducirlos despues.

QUE PRUEBA Y QUE NO PRUEBA. Se le pregunta a 'compute_path_to_pose' con
use_start:=true, asi que el robot NO se mueve y la respuesta sale del
planificador y del costmap global. El planificador es SmacPlannerHybrid, que
respeta el radio de giro minimo, asi que un camino devuelto ya es
cinematicamente admisible para el Ackermann. Lo que NO dice es que el
controlador sepa seguirlo, ni que AMCL llegue dentro de la tolerancia: eso solo
lo dice una mision conducida. Un camino calculable es condicion necesaria, no
suficiente.

Se mide por par:
  - si hay camino,
  - la longitud del camino,
  - el rodeo = longitud / distancia en linea recta (delata desvios raros),
  - las cuspides, contadas con el MISMO criterio que componer_registro.py:
    cambio de signo de la proyeccion del avance sobre el rumbo. R12 sigue
    abierto y las cuspides son justo su sintoma,
  - los metros recorridos MARCHA ATRAS, que no son lo mismo: un camino hecho
    entero en reversa no cambia de marcha ni una vez y sale con 0 cuspides.
    Ver la nota de medir_camino().

Uso:
    python3 herramientas/barrer_rutas.py                      # robot1, nivel 1
    python3 herramientas/barrer_rutas.py --nivel 2 --robot robot2
    python3 herramientas/barrer_rutas.py --salida /tmp/rutas_p1.csv

Requiere la pila de Nav2 arriba y ACTIVA (los 7 nodos de ciclo de vida en
active). Si el servidor de accion no aparece, se sale sin escribir nada.

Codigo de salida: 0 si todos los pares tienen camino, 1 si alguno no.
"""

import argparse
import csv
import math
import os
import sys
import time

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient
from rclpy.node import Node

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(
    RAIZ, "Robot", "aws-deepracer", "deepracer_bringup", "config",
    "puntos_interes.yaml")

# Umbral de rodeo a partir del cual el par se marca para conducirlo. No es un
# criterio de fallo: un rodeo alto puede ser la geometria real del pasillo. Es
# el corte que decide a que pares se les gasta una mision.
RODEO_SOSPECHOSO = 1.6


def puntos_del_nivel(ruta, nivel):
    with open(ruta, encoding="utf-8") as f:
        catalogo = yaml.safe_load(f)
    return [p for p in catalogo["puntos"] if int(p["nivel"]) == nivel]


def pose_stamped(nodo, punto, marco, yaw=None):
    p = PoseStamped()
    p.header.frame_id = marco
    p.header.stamp = nodo.get_clock().now().to_msg()
    p.pose.position.x = float(punto["pose"]["x"])
    p.pose.position.y = float(punto["pose"]["y"])
    if yaw is None:
        yaw = float(punto["pose"]["yaw"])
    p.pose.orientation.z = math.sin(yaw / 2.0)
    p.pose.orientation.w = math.cos(yaw / 2.0)
    return p


def rumbo_natural(origen, destino):
    """El rumbo que lleva de origen a destino en linea recta."""
    return math.atan2(float(destino["pose"]["y"]) - float(origen["pose"]["y"]),
                      float(destino["pose"]["x"]) - float(origen["pose"]["x"]))


def _normalizar(a):
    return math.atan2(math.sin(a), math.cos(a))


def yaw_del_coordinador(punto, rumbo):
    """Replica coordinador.py::_yaw_de_llegada.

    Un carro ocupa el mismo sitio fisico en dos sentidos, asi que de los dos
    candidatos del eje que puso el humano en el YAML -yaw y yaw+pi- se coge el
    mas cercano al rumbo de aproximacion. Elegir entre esos dos nunca anade
    maniobra: solo puede quitarla.

    Esta funcion DUPLICA logica del coordinador a proposito, y la duplicacion
    es el precio de que el barrido no dependa de rclpy ni de un coordinador
    vivo. Si se toca alla, hay que tocarla aqui: si divergen, este barrido
    mediria una politica que nadie ejecuta, que es exactamente el error que
    cometio la primera version de esta herramienta.
    """
    yaml_yaw = float(punto["pose"].get("yaw", 0.0))
    if punto.get("yaw_estricto", False):
        return yaml_yaw
    opuesto = _normalizar(yaml_yaw + math.pi)
    if abs(_normalizar(rumbo - yaml_yaw)) <= abs(_normalizar(rumbo - opuesto)):
        return yaml_yaw
    return opuesto


def _yaw(orientacion):
    z, w = orientacion.z, orientacion.w
    return math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)


def medir_camino(camino):
    """Devuelve (longitud_m, cuspides, retroceso_m) de un nav_msgs/Path.

    LAS CUSPIDES SOLAS ENGANAN, y este barrido lo demostro. Cuentan CAMBIOS de
    sentido, asi que un camino recorrido entero marcha atras tiene signo
    constante y sale con CERO cuspides: indistinguible de ir de frente. En el
    barrido del piso 1 del 27-ago salieron 13 pares asi, hasta 4,27 m de
    reversa seguida marcados como '0 cuspides'.

    Por eso se devuelve tambien el METRAJE en reversa. Cuspides y retroceso
    responden preguntas distintas: cuantas veces cambia de marcha, y cuanto
    camino hace sin mirar hacia donde va.
    """
    poses = [p.pose for p in camino.poses]
    longitud = 0.0
    retroceso = 0.0
    signos = []
    for a, b in zip(poses, poses[1:]):
        dx = b.position.x - a.position.x
        dy = b.position.y - a.position.y
        paso = math.hypot(dx, dy)
        longitud += paso
        # Proyeccion del avance sobre el rumbo del propio tramo: negativa
        # significa marcha atras. Mismo criterio que componer_registro.py.
        rumbo = _yaw(a.orientation)
        proyeccion = dx * math.cos(rumbo) + dy * math.sin(rumbo)
        if abs(proyeccion) > 1e-9:
            signo = 1 if proyeccion > 0 else -1
            signos.append(signo)
            if signo < 0:
                retroceso += paso
    cuspides = sum(1 for a, b in zip(signos, signos[1:]) if a != b)
    return longitud, cuspides, retroceso


class Barredor(Node):
    def __init__(self, robot, marco, espera):
        super().__init__("barredor_de_rutas")
        self.espera = espera
        self.marco = marco
        self.cliente = ActionClient(
            self, ComputePathToPose, f"/{robot}/compute_path_to_pose")

    def hay_servidor(self, segundos):
        return self.cliente.wait_for_server(timeout_sec=segundos)

    def planificar(self, origen, destino, politica="coordinador"):
        """(ok, longitud_m, cuspides, retroceso_m, motivo).

        Las tres politicas no son variantes intercambiables: acotan el problema.
          'coordinador' es la UNICA que describe misiones reales.
          'catalogo' es la cota pesimista -yaw crudo del YAML-, util solo para
            medir cuanta maniobra evita el coordinador.
          'natural' es la cota optimista inalcanzable: rumbo libre en los dos
            extremos, que ningun robot aparcado puede garantizar.

        SUPUESTO DE 'coordinador' SOBRE EL RUMBO DE SALIDA. El coordinador
        elige el rumbo de LLEGADA; el de salida es el que el robot traiga de la
        mision anterior, y un barrido de pares sueltos no lo sabe. Se supone
        que viene aparcado sobre el eje del pasillo en el sentido favorable,
        que es lo que deja la misma regla aplicada al tramo anterior. Es un
        supuesto optimista en el rumbo de salida y exacto en el de llegada.
        """
        if politica == "natural":
            yaw_ini = yaw_fin = rumbo_natural(origen, destino)
        elif politica == "catalogo":
            yaw_ini = yaw_fin = None
        else:
            rumbo = rumbo_natural(origen, destino)
            yaw_ini = yaw_del_coordinador(origen, rumbo)
            yaw_fin = yaw_del_coordinador(destino, rumbo)

        meta = ComputePathToPose.Goal()
        meta.start = pose_stamped(self, origen, self.marco, yaw_ini)
        meta.goal = pose_stamped(self, destino, self.marco, yaw_fin)
        meta.use_start = True

        envio = self.cliente.send_goal_async(meta)
        rclpy.spin_until_future_complete(self, envio, timeout_sec=self.espera)
        if not envio.done():
            return False, 0.0, 0, 0.0, "el servidor no contesto al envio"
        manejador = envio.result()
        if not manejador.accepted:
            return False, 0.0, 0, 0.0, "meta rechazada"

        resultado = manejador.get_result_async()
        rclpy.spin_until_future_complete(self, resultado, timeout_sec=self.espera)
        if not resultado.done():
            return False, 0.0, 0, 0.0, f"sin resultado en {self.espera:.0f} s"

        r = resultado.result()
        if r.status != GoalStatus.STATUS_SUCCEEDED:
            return False, 0.0, 0, 0.0, f"estado {r.status}"
        if len(r.result.path.poses) < 2:
            return False, 0.0, 0, 0.0, "camino vacio"

        longitud, cuspides, retroceso = medir_camino(r.result.path)
        return True, longitud, cuspides, retroceso, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--robot", default="robot1")
    ap.add_argument("--nivel", type=int, default=1)
    ap.add_argument("--catalogo", default=CATALOGO)
    ap.add_argument("--salida", default="")
    ap.add_argument("--espera", type=float, default=20.0,
                    help="segundos por par antes de darlo por perdido")
    # 'planner_server' publica en <ns>/plan cada camino que calcula, asi que en
    # RViz se ven pasar los 210. Sin pausa es un parpadeo; con pausa se puede
    # mirar. Es solo para observar: no cambia lo que se mide.
    ap.add_argument("--pausa", type=float, default=0.0,
                    help="segundos de espera tras cada par, para verlo en RViz")
    # 'natural' no describe ninguna mision real: es el contrafactual. El barrido
    # del 27-ago dejo 132 de 210 pares con marcha atras, y el cruce contra el
    # catalogo apunta al yaw prescrito como causa (52 de 52 pares que salen
    # contra su rumbo dan exactamente una cuspide). Repetir el barrido con
    # 'natural' mide esa causa en vez de suponerla: si la reversa se derrumba,
    # la maniobra la paga el catalogo, no el planificador.
    ap.add_argument("--rumbo", choices=("coordinador", "catalogo", "natural"),
                    default="coordinador",
                    help="'coordinador' (defecto) replica el yaw que manda de "
                         "verdad coordinador.py; 'catalogo' usa el yaw crudo "
                         "del YAML y 'natural' lo ignora del todo: esas dos son "
                         "cotas, no describen misiones")
    args = ap.parse_args()

    marco = f"{args.robot}/map"
    puntos = puntos_del_nivel(args.catalogo, args.nivel)
    if len(puntos) < 2:
        print(f"El nivel {args.nivel} tiene {len(puntos)} puntos: nada que barrer.")
        return 1
    pares = [(a, b) for a in puntos for b in puntos if a["id"] != b["id"]]
    print(f"Nivel {args.nivel}: {len(puntos)} puntos, {len(pares)} pares ordenados.")
    if args.rumbo == "coordinador":
        print("RUMBO COORDINADOR: se replica coordinador.py::_yaw_de_llegada. "
              "Esta es la politica que se ejecuta de verdad.")
    else:
        print(f"RUMBO {args.rumbo.upper()}: COTA, no describe ninguna mision. "
              "El coordinador no manda este rumbo.")
    print(f"Preguntando a /{args.robot}/compute_path_to_pose en marco '{marco}'.")

    rclpy.init()
    nodo = Barredor(args.robot, marco, args.espera)
    if not nodo.hay_servidor(10.0):
        print(f"\nNo aparece /{args.robot}/compute_path_to_pose.")
        print("La pila de Nav2 no esta arriba, o no esta activa. Lanzar:")
        print(f"  herramientas/robot.sh {args.robot} nav2 gui:=false")
        print("y esperar a que los 7 nodos de ciclo de vida esten en active [3].")
        rclpy.shutdown()
        return 1

    filas = []
    for i, (origen, destino) in enumerate(pares, 1):
        ok, longitud, cuspides, retroceso, motivo = nodo.planificar(
            origen, destino, politica=args.rumbo)
        recta = math.hypot(
            float(destino["pose"]["x"]) - float(origen["pose"]["x"]),
            float(destino["pose"]["y"]) - float(origen["pose"]["y"]))
        rodeo = (longitud / recta) if (ok and recta > 1e-6) else 0.0
        filas.append({
            "origen": origen["id"], "destino": destino["id"],
            "ok": int(ok), "recta_m": round(recta, 3),
            "camino_m": round(longitud, 3), "rodeo": round(rodeo, 3),
            "cuspides": cuspides, "retroceso_m": round(retroceso, 3),
            "motivo": motivo,
        })
        if args.pausa > 0.0:
            estado = (f"{longitud:6.2f} m, {cuspides} cusp, "
                      f"{retroceso:5.2f} m atras") if ok else f"SIN CAMINO ({motivo})"
            print(f"[{i:3d}/{len(pares)}] {origen['id']:22s} -> "
                  f"{destino['id']:22s} {estado}")
            time.sleep(args.pausa)
        else:
            sys.stdout.write("." if ok else "X")
            if i % 50 == 0:
                sys.stdout.write(f" {i}/{len(pares)}\n")
        sys.stdout.flush()
    print()
    rclpy.shutdown()

    sin_camino = [f for f in filas if not f["ok"]]
    con_cuspides = [f for f in filas if f["ok"] and f["cuspides"] > 0]
    rodeos = sorted((f for f in filas if f["ok"]),
                    key=lambda f: f["rodeo"], reverse=True)
    desviados = [f for f in rodeos if f["rodeo"] >= RODEO_SOSPECHOSO]

    print(f"\nPares con camino     : {len(filas) - len(sin_camino)}/{len(filas)}")
    print(f"Pares SIN camino     : {len(sin_camino)}")
    for f in sin_camino:
        print(f"  {f['origen']} -> {f['destino']}: {f['motivo']}")
    print(f"Pares con cuspides   : {len(con_cuspides)}")
    for f in sorted(con_cuspides, key=lambda f: f["cuspides"], reverse=True)[:10]:
        print(f"  {f['origen']} -> {f['destino']}: {f['cuspides']} cuspides, "
              f"{f['camino_m']:.2f} m")
    print(f"Rodeo >= {RODEO_SOSPECHOSO}       : {len(desviados)}")
    for f in desviados[:10]:
        print(f"  {f['origen']} -> {f['destino']}: rodeo {f['rodeo']:.2f} "
              f"({f['camino_m']:.2f} m sobre {f['recta_m']:.2f} m)")

    # El bloque que de verdad importa. Un camino con MUCHA reversa y CERO
    # cuspides pasa desapercibido en el conteo de cuspides -no cambia de marcha
    # porque no cambia nunca- y es el peor caso para un robot que guia a una
    # persona: recorre metros sin mirar hacia donde va.
    atras = sorted((f for f in filas if f["ok"] and f["retroceso_m"] > 0.0),
                   key=lambda f: f["retroceso_m"], reverse=True)
    ciegos = [f for f in atras if f["cuspides"] == 0]
    print(f"Pares con reversa    : {len(atras)}")
    print(f"  de ellos, reversa INTEGRA (0 cuspides): {len(ciegos)}")
    for f in ciegos[:10]:
        print(f"    {f['origen']} -> {f['destino']}: "
              f"{f['retroceso_m']:.2f} m de {f['camino_m']:.2f} m marcha atras")

    if args.salida:
        with open(args.salida, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"\nTabla completa en {args.salida}")

    print("\nRecordatorio: esto es una criba, no una prueba de navegacion. Un "
          "camino calculable no dice que el controlador sepa seguirlo. Los "
          "pares senalados arriba son los que hay que conducir.")
    return 1 if sin_camino else 0


if __name__ == "__main__":
    sys.exit(main())
