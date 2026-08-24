#!/usr/bin/env python3
"""
Verifica que el sistema en ejecucion cumpla Documentos/CONTRATO_INTERFACES.md

Requiere una simulacion (o robot real) corriendo. No modifica nada.

Uso:
    # Modo linea base: un robot, sin namespaces. Comprueba salud, no contrato.
    python3 herramientas/verificar_contrato.py

    # Modo contrato: comprueba que robot1 y robot2 conviven segun el contrato.
    python3 herramientas/verificar_contrato.py --robots robot1 robot2

Codigo de salida: 0 si todo pasa, 1 si algo falla.
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict

# 'ros2 control list_controllers' colorea su salida con secuencias ANSI. En la
# terminal no se ven, pero al parsear convierten "active" en "\x1b[92mactive\x1b[0m".
ANSI = re.compile(r"\x1b\[[0-9;]*m")

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from tf2_msgs.msg import TFMessage

# --- Lo que el contrato exige (§2) -------------------------------------------

TOPICOS_ROBOT = [
    "cmd_vel",
    "odom",
    "scan",
    "joint_states",
    "robot_description",
    "dynamic_joint_states",
]

CONTROLADORES = [
    "joint_state_broadcaster",
    "left_rear_wheel_velocity_controller",
    "right_rear_wheel_velocity_controller",
    "left_front_wheel_velocity_controller",
    "right_front_wheel_velocity_controller",
    "left_steering_hinge_position_controller",
    "right_steering_hinge_position_controller",
]

# Tópicos que por definicion de ROS 2 viven en la raiz y no se namespacean.
GLOBALES = {
    "/clock",
    "/tf",
    "/tf_static",
    "/rosout",
    "/parameter_events",
    "/performance_metrics",
}

# --- Reporte -----------------------------------------------------------------

resultados = []


def ok(titulo, detalle=""):
    resultados.append(True)
    print(f"[OK]    {titulo}" + (f" — {detalle}" if detalle else ""))


def falla(titulo, detalle=""):
    resultados.append(False)
    print(f"[FALLA] {titulo}" + (f" — {detalle}" if detalle else ""))


def info(titulo, detalle=""):
    print(f"[--]    {titulo}" + (f" — {detalle}" if detalle else ""))


# --- Recoleccion -------------------------------------------------------------


def listar_topicos():
    salida = subprocess.run(
        ["ros2", "topic", "list"], capture_output=True, text=True, timeout=30
    )
    return [t.strip() for t in salida.stdout.splitlines() if t.strip()]


def listar_controladores(namespace=None):
    cmd = ["ros2", "control", "list_controllers"]
    if namespace:
        cmd += ["-c", f"/{namespace}/controller_manager"]
    try:
        salida = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        return {}
    activos = {}
    for linea in salida.stdout.splitlines():
        linea = ANSI.sub("", linea)
        # Las lineas de log ("[INFO] ... waiting for service ...") salen por
        # stdout y tienen mas de 3 campos: si no se filtran, se cuelan como si
        # fueran controladores y el diagnostico sale al reves.
        if linea.startswith("["):
            continue
        campos = linea.split()
        if len(campos) >= 3:
            activos[campos[0]] = campos[-1]
    return activos


class EscuchaTF(Node):
    """Recoge pares (hijo -> padre) de /tf y /tf_static durante unos segundos.

    El contrato no se puede verificar solo con la lista de marcos: si dos
    emisores reclaman el mismo hijo, view_frames muestra un unico padre (el
    ultimo que llego) y el conflicto queda invisible. Guardando el CONJUNTO de
    padres por hijo, cualquier hijo con mas de un padre es un conflicto real.
    """

    def __init__(self):
        super().__init__("verificar_contrato")
        self.padres = defaultdict(set)

        qos_static = QoSProfile(
            depth=100,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self.create_subscription(TFMessage, "/tf_static", self._cb, qos_static)
        self.create_subscription(TFMessage, "/tf", self._cb, 100)

    def _cb(self, msg):
        for t in msg.transforms:
            self.padres[t.child_frame_id].add(t.header.frame_id)


def recoger_tf(segundos=5.0):
    rclpy.init()
    nodo = EscuchaTF()
    fin = nodo.get_clock().now().nanoseconds + segundos * 1e9
    while rclpy.ok() and nodo.get_clock().now().nanoseconds < fin:
        rclpy.spin_once(nodo, timeout_sec=0.1)
    padres = dict(nodo.padres)
    nodo.destroy_node()
    rclpy.shutdown()
    return padres


# --- Comprobaciones ----------------------------------------------------------


def revisar_topicos(topicos, robots):
    if not robots:
        faltan = [t for t in TOPICOS_ROBOT if f"/{t}" not in topicos]
        if faltan:
            falla("Tópicos del robot presentes", f"faltan {', '.join(faltan)}")
        else:
            ok("Tópicos del robot presentes", f"{len(TOPICOS_ROBOT)}/{len(TOPICOS_ROBOT)}")
        info("Namespaces", "modo línea base: no se exigen")
        return

    for ns in robots:
        faltan = [t for t in TOPICOS_ROBOT if f"/{ns}/{t}" not in topicos]
        if faltan:
            falla(f"Tópicos bajo /{ns}", f"faltan {', '.join(faltan)}")
        else:
            ok(f"Tópicos bajo /{ns}", f"{len(TOPICOS_ROBOT)}/{len(TOPICOS_ROBOT)}")

    # Contrato §1: nada del robot puede quedar suelto en la raiz.
    sueltos = [
        t
        for t in topicos
        if t not in GLOBALES and not any(t.startswith(f"/{ns}/") for ns in robots)
    ]
    if sueltos:
        falla("Raíz limpia", f"{len(sueltos)} tópicos sin namespace: {', '.join(sueltos[:5])}")
    else:
        ok("Raíz limpia", "solo tópicos globales")


def revisar_controladores(robots):
    objetivos = robots if robots else [None]
    for ns in objetivos:
        etiqueta = f"/{ns}" if ns else "raíz"
        activos = listar_controladores(ns)
        if not activos:
            falla(f"Controladores en {etiqueta}", "controller_manager no responde")
            continue
        malos = [c for c in CONTROLADORES if activos.get(c) != "active"]
        if malos:
            falla(f"Controladores en {etiqueta}", f"no activos: {', '.join(malos)}")
        else:
            ok(f"Controladores en {etiqueta}", f"{len(CONTROLADORES)}/{len(CONTROLADORES)} active")


def revisar_tf(padres, robots):
    if not padres:
        falla("Árbol TF", "no se recibió ninguna transformada")
        return

    # Esta comprobacion vale en los dos modos: un hijo con dos padres siempre
    # es un defecto, haya namespaces o no.
    conflictos = {h: p for h, p in padres.items() if len(p) > 1}
    if conflictos:
        for hijo, ps in sorted(conflictos.items()):
            falla("Marco con más de un padre", f"'{hijo}' ← {', '.join(sorted(ps))}")
    else:
        ok("Cada marco tiene un solo padre", f"{len(padres)} marcos revisados")

    if not robots:
        info("Prefijos TF", f"modo línea base: {len(padres)} marcos sin prefijo")
        return

    todos = set(padres) | {p for ps in padres.values() for p in ps}
    sin_prefijo = sorted(f for f in todos if not any(f.startswith(f"{ns}/") for ns in robots))
    if sin_prefijo:
        falla(
            "Marcos prefijados",
            f"{len(sin_prefijo)} sin prefijo: {', '.join(sin_prefijo[:6])}",
        )
    else:
        ok("Marcos prefijados", f"{len(todos)} marcos, todos bajo un namespace")

    # Esta comprobación era un 'info' con la excusa «normal si no hay AMCL/SLAM
    # levantado», y esa excusa tapó el fallo del 2026-08-24: los launch dejaban
    # el marco global sin prefijar, así que '<ns>/map' NO existía ni con AMCL
    # levantada, y aquí salía la misma línea tranquilizadora. El coordinador
    # mandaba el goal a un marco inexistente y Nav2 abortaba sin explicar nada.
    #
    # Ahora se distingue: si hay 'odom' del robot en el árbol, la localización
    # está publicando y la falta de '<ns>/map' es un FALLO, no una circunstancia.
    for ns in robots:
        raiz = f"{ns}/map"
        if raiz in todos:
            ok(f"Raíz de {ns}", raiz)
        elif f"{ns}/odom" in todos:
            falla(
                f"Raíz de {ns}",
                f"hay '{ns}/odom' pero no '{raiz}': el marco global se quedó "
                f"sin prefijar y un goal en '{raiz}' no se puede transformar",
            )
        else:
            info(f"Raíz de {ns}", f"no existe '{raiz}' (no hay AMCL/SLAM levantado)")


# --- Principal ---------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--robots",
        nargs="*",
        default=[],
        metavar="NS",
        help="namespaces a verificar, p.ej. --robots robot1 robot2. "
        "Sin este argumento se verifica la línea base de un robot.",
    )
    ap.add_argument("--segundos-tf", type=float, default=5.0)
    args = ap.parse_args()

    modo = f"contrato ({', '.join(args.robots)})" if args.robots else "línea base"
    print(f"\nVerificación del contrato de interfaces — modo: {modo}\n" + "-" * 62)

    topicos = listar_topicos()
    if len(topicos) <= 2:
        print("\nNo hay nada corriendo: solo se ven tópicos del sistema.")
        print("Lanza la simulación primero y vuelve a ejecutar.\n")
        return 1

    # Antes de juzgar el contrato hay que descartar que Gazebo este caido: si
    # no, el reporte culpa al contrato de una simulacion que nunca arranco.
    gz = subprocess.run(["pgrep", "-c", "gzserver"], capture_output=True, text=True)
    if gz.stdout.strip() in ("", "0"):
        print("\nGazebo no está corriendo (no hay proceso gzserver).")
        print("Nada de lo que sigue tendría sentido. Revisa la terminal del launch.\n")
        return 1
    if "/clock" not in topicos:
        print("\nGazebo corre pero no publica /clock: es un gzserver zombi.")
        print("Límpialo con:  pkill -9 gzserver gzclient")
        print("y vuelve a lanzar la simulación.\n")
        return 1

    revisar_topicos(topicos, args.robots)
    revisar_controladores(args.robots)
    revisar_tf(recoger_tf(args.segundos_tf), args.robots)

    print("-" * 62)
    fallos = resultados.count(False)
    if fallos:
        print(f"{fallos} de {len(resultados)} comprobaciones FALLAN\n")
        return 1
    print(f"Las {len(resultados)} comprobaciones pasan\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
