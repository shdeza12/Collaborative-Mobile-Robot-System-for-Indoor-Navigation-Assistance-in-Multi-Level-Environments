#!/usr/bin/env python3
"""Reproduce y localiza el 'Nav2 termino con estado 6' del 2026-09-04.

QUE SE OBSERVO, y de donde sale cada dato:

  - 'estado 6' es STATUS_ABORTED (action_msgs.msg.GoalStatus).
  - El goal fue ACEPTADO y luego abortado: para llegar a la linea que emite ese
    mensaje, coordinador.py:458 ya paso el 'gh.accepted'.
  - Abortó a los 103 ms y a los 111 ms de enviarlo (marcas del log de consola).
  - El MISMO origen y el MISMO destino funcionaron 8 s despues.
  - Los dos fallos tuvieron origen distinto: uno a 2,88 m del destino y otro a
    26,13 m. No es geometria.
  - El antecedente documentado de ABORTED (GUIA_EJECUCION.md:297-306) era un
    frame_id sin prefijo. Queda descartado: coordinador.py:439 usa '<robot>/map'.

LO QUE FALTA, y por que hace falta esto: el dato que nombra la causa es que nodo
del arbol de comportamiento fallo, y eso solo lo dice el log de bt_navigator. Ese
log va a la terminal y no a disco -los ~/.ros/log/*/launch.log son contabilidad
del launch-, asi que hay que reproducirlo capturandolo.

QUE AISLA:

  1. Manda los goals DIRECTAMENTE a /<robot>/navigate_to_pose, sin coordinador.
     Si aborta igual, el coordinador queda descartado. Si no aborta nunca en N
     intentos, el sospechoso es el coordinador y hay que repetir con el.
  2. Por cada intento anota la pose REAL al enviar, si fue aceptado, el estado
     final y los milisegundos hasta el resultado.
  3. Si a los --umbral-s sigue EXECUTING, cancela y cuenta 'no aborto'. Asi cada
     intento cuesta unos segundos en vez de una travesia completa: lo que se mide
     es el aborto inmediato, no si el robot llega.
  4. En cada intento captura EXACTAMENTE lo que la pila escribio en su log
     mientras duraba, leyendo desde el offset del archivo justo antes de enviar.
     Sin parsear marcas de tiempo, sin ventanas aproximadas.

EL GOAL ES EL MISMO QUE MANDA EL COORDINADOR, a proposito: frame_id '<robot>/map',
stamp del reloj del nodo con use_sim_time, y el yaw del catalogo. Ver
coordinador.py:435-446. Si se construyera 'parecido' no se estaria reproduciendo.

Un solo proceso es dueño de todo -levanta la pila y manda los goals- porque los
buzones de FastDDS en /dev/shm son de un solo dueño y mezclarlos falla en silencio.

    python3 herramientas/diagnosticar_aborto_nav2.py --intentos 20
"""

import argparse
import math
import os
import subprocess
import sys
import time

import yaml

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(
    RAIZ, "Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml")

NOMBRE_ESTADO = {v: n for n, v in vars(GoalStatus).items()
                 if n.startswith("STATUS_")}

# Los nodos cuya salida decide donde falla. 'bt_navigator' dice que rama del
# arbol se cayo; 'planner_server' y 'controller_server', por que.
NODOS_DE_INTERES = ("bt_navigator", "planner_server", "controller_server",
                    "behavior_server", "smoother_server", "amcl",
                    "global_costmap", "local_costmap")


def cargar_punto(punto_id):
    with open(CATALOGO, encoding="utf-8") as f:
        puntos = yaml.safe_load(f)["puntos"]
    for p in puntos:
        if p["id"] == punto_id:
            return p
    ids = ", ".join(sorted(p["id"] for p in puntos))
    raise SystemExit(f"'{punto_id}' no esta en el catalogo. Hay: {ids}")


def yaw_a_cuaternion(yaw):
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def yaw_de(orientacion):
    z, w = orientacion.z, orientacion.w
    return math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)


class Sonda(Node):
    def __init__(self, robot):
        super().__init__(
            "sonda_de_aborto",
            parameter_overrides=[
                Parameter("use_sim_time", Parameter.Type.BOOL, True)])
        self.robot = robot
        self.odom = None
        self.create_subscription(
            Odometry, f"/{robot}/odom", self._odom, 10)
        self.cliente = ActionClient(
            self, NavigateToPose, f"/{robot}/navigate_to_pose")

    def _odom(self, msg):
        self.odom = msg

    def esperar_reloj(self, segundos=30.0):
        """Sin /clock, get_clock().now() vale 0 y el stamp del goal seria basura."""
        fin = time.monotonic() + segundos
        while time.monotonic() < fin:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self.get_clock().now().nanoseconds > 0:
                return True
        return False

    def esperar_odom(self, segundos=30.0):
        fin = time.monotonic() + segundos
        while time.monotonic() < fin and self.odom is None:
            rclpy.spin_once(self, timeout_sec=0.2)
        return self.odom is not None

    def pose_actual(self):
        self.odom = None
        self.esperar_odom(5.0)
        if self.odom is None:
            return None
        p = self.odom.pose.pose
        return p.position.x, p.position.y, math.degrees(yaw_de(p.orientation))

    def _girar(self, futuro, segundos):
        fin = time.monotonic() + segundos
        while time.monotonic() < fin and not futuro.done():
            rclpy.spin_once(self, timeout_sec=0.05)
        return futuro.done()

    def _construir(self, punto):
        objetivo = NavigateToPose.Goal()
        objetivo.pose = PoseStamped()
        objetivo.pose.header.frame_id = f"{self.robot}/map"
        objetivo.pose.header.stamp = self.get_clock().now().to_msg()
        objetivo.pose.pose.position.x = float(punto["pose"]["x"])
        objetivo.pose.pose.position.y = float(punto["pose"]["y"])
        qz, qw = yaw_a_cuaternion(float(punto["pose"].get("yaw", 0.0)))
        objetivo.pose.pose.orientation.z = qz
        objetivo.pose.pose.orientation.w = qw
        return objetivo

    def intentar_doble(self, punto, retardo_s, umbral_s):
        """Dos goals seguidos al MISMO servidor, como dos coordinadores vivos.

        navigate_to_pose atiende un goal a la vez. Si el segundo desplaza al
        primero, el primero termina en ABORTED en milisegundos, y eso es
        exactamente lo que se observo el 2026-09-04. Aqui se mide el desenlace
        del PRIMERO; el segundo se cancela despues para dejar el banco quieto.
        """
        r = {"pose": self.pose_actual(), "aceptado": None, "estado": None,
             "ms": None, "cancelado": False, "nota": "", "estado_b": None}

        t0 = time.monotonic()
        fut_a = self.cliente.send_goal_async(self._construir(punto))
        if not self._girar(fut_a, 10.0):
            r["nota"] = "el primer goal no obtuvo respuesta en 10 s"
            return r
        gh_a = fut_a.result()
        r["aceptado"] = bool(gh_a.accepted)
        if not gh_a.accepted:
            r["nota"] = "el primer goal fue RECHAZADO"
            return r
        res_a = gh_a.get_result_async()

        fin = time.monotonic() + retardo_s
        while time.monotonic() < fin:
            rclpy.spin_once(self, timeout_sec=0.02)

        t_b = time.monotonic()
        fut_b = self.cliente.send_goal_async(self._construir(punto))
        self._girar(fut_b, 10.0)

        # Desde el envio del SEGUNDO, porque es esa la latencia que importa.
        if self._girar(res_a, umbral_s):
            r["estado"] = res_a.result().status
            r["ms"] = round((time.monotonic() - t_b) * 1000)
        else:
            r["nota"] = f"el primero seguia vivo {umbral_s:.0f} s despues del segundo"
            self._girar(gh_a.cancel_goal_async(), 5.0)
            r["cancelado"] = True

        if fut_b.done() and fut_b.result().accepted:
            gh_b = fut_b.result()
            res_b = gh_b.get_result_async()
            self._girar(gh_b.cancel_goal_async(), 5.0)
            self._girar(res_b, 5.0)
            r["estado_b"] = res_b.result().status if res_b.done() else None
        return r

    def intentar(self, punto, umbral_s):
        """Un intento. Devuelve un dict con todo lo medido."""
        r = {"pose": self.pose_actual(), "aceptado": None,
             "estado": None, "ms": None, "cancelado": False, "nota": ""}

        objetivo = self._construir(punto)
        t0 = time.monotonic()
        fut = self.cliente.send_goal_async(objetivo)
        if not self._girar(fut, 10.0):
            r["nota"] = "sin respuesta al envio en 10 s"
            return r
        gh = fut.result()
        r["aceptado"] = bool(gh.accepted)
        if not gh.accepted:
            r["ms"] = round((time.monotonic() - t0) * 1000)
            r["nota"] = "el servidor RECHAZO el goal (no es el caso observado)"
            return r

        fut_res = gh.get_result_async()
        if self._girar(fut_res, umbral_s):
            r["ms"] = round((time.monotonic() - t0) * 1000)
            r["estado"] = fut_res.result().status
            return r

        # Sigue navegando: no es el fallo que buscamos. Se cancela para que el
        # robot no se vaya al otro extremo del pasillo y falsee el intento
        # siguiente, cuyo origen quedaria a 20 m de este.
        self._girar(gh.cancel_goal_async(), 5.0)
        self._girar(fut_res, 5.0)
        r["cancelado"] = True
        r["ms"] = round((time.monotonic() - t0) * 1000)
        r["estado"] = fut_res.result().status if fut_res.done() else None
        return r


def lanzar_pila(robot, ruta_log):
    log = open(ruta_log, "wb")
    p = subprocess.Popen(
        [os.path.join(RAIZ, "herramientas/robot.sh"), robot, "nav2"],
        stdout=log, stderr=subprocess.STDOUT, cwd=RAIZ, start_new_session=True)
    return p, log


def portones(robot):
    """El porton del §3 del runbook, tal cual, sin reimplementarlo aqui."""
    return subprocess.run(
        [os.path.join(RAIZ, "herramientas/esperar_nav2.sh"), robot],
        cwd=RAIZ).returncode == 0


def parar_pila(robot):
    subprocess.run([os.path.join(RAIZ, "herramientas/robot.sh"), robot, "parar"],
                   cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def log_desde(ruta, desde):
    """Lo que la pila escribio entre 'desde' y ahora, filtrado a lo que importa."""
    if not os.path.exists(ruta):
        return [], desde
    with open(ruta, "rb") as f:
        f.seek(desde)
        crudo = f.read().decode("utf-8", "replace")
    fin = os.path.getsize(ruta)
    lineas = [l for l in crudo.splitlines()
              if any(n in l for n in NODOS_DE_INTERES)
              and ("[ERROR]" in l or "[WARN]" in l or "abort" in l.lower()
                   or "fail" in l.lower() or "invalid" in l.lower())]
    return lineas, fin


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--robot", default="robot1")
    ap.add_argument("--destino", default="piso1_etm7")
    ap.add_argument("--intentos", type=int, default=20)
    ap.add_argument("--umbral-s", type=float, default=3.0,
                    help="si sigue navegando pasado esto, no es un aborto "
                         "inmediato: se cancela y se cuenta como 'no aborto'")
    ap.add_argument("--pausa-s", type=float, default=1.0,
                    help="espera entre intentos; se anota, porque el fallo del "
                         "14:36 desaparecio 8 s despues")
    ap.add_argument("--doble-goal", action="store_true",
                    help="manda DOS goals seguidos al mismo servidor, como los "
                         "dos coordinadores vivos del 2026-09-04, y mide el "
                         "desenlace del primero")
    ap.add_argument("--retardo-b-s", type=float, default=0.3,
                    help="separacion entre los dos goals de --doble-goal")
    ap.add_argument("--log", default="/tmp/pila_diagnostico.log")
    ap.add_argument("--sin-levantar", action="store_true",
                    help="usa la pila que ya este arriba; entonces --log tiene "
                         "que apuntar al archivo donde se redirigio robot.sh")
    args = ap.parse_args()

    punto = cargar_punto(args.destino)
    print(f"Destino: {args.destino} "
          f"({punto['pose']['x']}, {punto['pose']['y']}), "
          f"yaw {math.degrees(float(punto['pose'].get('yaw', 0.0))):.0f} grados")

    proc = handle = None
    try:
        if not args.sin_levantar:
            print(f"Levantando la pila de {args.robot}; log en {args.log}")
            proc, handle = lanzar_pila(args.robot, args.log)

        print("Porton del §3...")
        if not portones(args.robot):
            print("\nEl porton NO paso. No se diagnostica sobre una pila que no "
                  "esta lista: seria medir otra cosa.", file=sys.stderr)
            return 2

        rclpy.init()
        sonda = Sonda(args.robot)
        if not sonda.esperar_reloj():
            print("No llega /clock. Con use_sim_time el stamp del goal seria 0.",
                  file=sys.stderr)
            return 2
        if not sonda.cliente.wait_for_server(timeout_sec=20.0):
            print(f"/{args.robot}/navigate_to_pose no aparece.", file=sys.stderr)
            return 2
        if not sonda.esperar_odom():
            print(f"/{args.robot}/odom no publica.", file=sys.stderr)
            return 2

        offset = os.path.getsize(args.log) if os.path.exists(args.log) else 0
        filas = []
        print(f"\n{'#':>3} {'pose al enviar':>28} {'acep':>5} "
              f"{'estado':>17} {'ms':>7}  nota")
        print("-" * 88)
        for i in range(1, args.intentos + 1):
            r = (sonda.intentar_doble(punto, args.retardo_b_s, args.umbral_s)
                 if args.doble_goal else sonda.intentar(punto, args.umbral_s))
            lineas, offset = log_desde(args.log, offset)
            r["log"] = lineas
            filas.append(r)

            pose = ("  sin /odom" if r["pose"] is None else
                    f"({r['pose'][0]:7.3f},{r['pose'][1]:7.3f}) "
                    f"{r['pose'][2]:6.1f}d")
            estado = NOMBRE_ESTADO.get(r["estado"], "-")
            nota = r["nota"] or (
                f"seguia navegando a los {args.umbral_s:.0f} s: cancelado"
                if r["cancelado"] else "")
            if args.doble_goal:
                nota = (f"{nota}  [2do goal: "
                        f"{NOMBRE_ESTADO.get(r.get('estado_b'), '-')}]").strip()
            print(f"{i:>3} {pose:>28} {str(r['aceptado']):>5} "
                  f"{estado:>17} {str(r['ms']):>7}  {nota}")
            for l in lineas:
                print(f"      | {l[:150]}")
            time.sleep(args.pausa_s)

        abortos = [f for f in filas
                   if f["estado"] == GoalStatus.STATUS_ABORTED
                   and not f["cancelado"]]
        print("\n" + "=" * 88)
        print(f"Intentos: {len(filas)}   abortos inmediatos: {len(abortos)}")
        if args.doble_goal:
            print(f"Modo doble goal: el segundo salio {args.retardo_b_s:.2f} s "
                  f"despues del primero; los ms se cuentan desde ese segundo "
                  f"envio.")
            if abortos:
                ms = [f["ms"] for f in abortos]
                print(f"\nCONFIRMADO: el goal desplazado termina en ABORTED "
                      f"({len(abortos)}/{len(filas)}), entre {min(ms)} y "
                      f"{max(ms)} ms del segundo envio. Compararlo con los 103 y "
                      f"111 ms del 2026-09-04. La causa es que hubo DOS emisores "
                      f"contra un servidor de un solo goal, no un fallo de Nav2.")
            else:
                print("\nEl primer goal NO aborto pese al segundo. La hipotesis de "
                      "los dos coordinadores queda descartada y hay que volver a "
                      "la fase 1 con las diferencias que quedan: la pila de robot2 "
                      "arriba y el coordinador en medio.")
            return 0
        if abortos:
            ms = [f["ms"] for f in abortos]
            print(f"ms hasta el aborto: min {min(ms)}, max {max(ms)}")
            print("\nEl coordinador QUEDA DESCARTADO: el aborto sale mandando el "
                  "goal directo a Nav2.")
            con_log = [f for f in abortos if f["log"]]
            if con_log:
                print("Lineas de la pila en el intento que aborto:")
                for l in con_log[0]["log"]:
                    print(f"  {l}")
            else:
                print("\nOJO: la pila no escribio NADA en esos intentos. Un aborto "
                      "sin una linea de bt_navigator apunta a que el goal no llego "
                      "a ejecutarse; repetir con --ros-args --log-level debug.")
        else:
            print("\nNO se reprodujo mandando el goal directo. El sospechoso pasa "
                  "a ser el coordinador: repetir la prueba con el en medio antes "
                  "de tocar nada de Nav2.")
        return 0
    finally:
        try:
            rclpy.try_shutdown()
        except Exception:
            pass
        if proc is not None:
            print(f"\nBajando la pila de {args.robot}...")
            parar_pila(args.robot)
            if handle:
                handle.close()


if __name__ == "__main__":
    sys.exit(main())
