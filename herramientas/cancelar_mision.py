#!/usr/bin/env python3
"""Lanza una mision y la cancela cuando el robot ya esta LEJOS de su escalera.

Es el disparador de la corrida de RF-29, no su instrumento de analisis: las
cuatro condiciones del requisito se comprueban despues, sobre el bag. Lo unico
que hace este script es poner la cancelacion en un instante REPRODUCIBLE.

POR QUE NO SE CANCELA A OJO
---------------------------
La alternativa era 'ros2 action send_goal -f' y un Ctrl-C cuando pareciera buen
momento. No sirve, y no por comodidad: robot1 nace en (-19.165, 7.292), a 1.41 m
de 'piso1_escalera' (-19.43, 5.91). Si la cancelacion llega temprano, el robot
"vuelve a casa" sin haberse ido nunca y la condicion (2) de RF-29 -quedar a
0.25 m del punto de transferencia- se cumple SOLA. La prueba diria que si
midiendo nada.

Por eso el disparo no es por tiempo sino por DISTANCIA: se espera a que /odom
situe al robot a mas de --umbral metros de su escalera, y solo entonces se
cancela. Asi el regreso es un desplazamiento real y la condicion (2) es falsable.

POR QUE ESTO VALE COMO "EL USUARIO CANCELA DESDE LA INTERFAZ"
------------------------------------------------------------
La HRI manda 'cancel_action_goal' por rosbridge (interfaz_web/js/rosbridge.js),
y rosbridge lo traduce al servicio '<accion>/_action/cancel_goal'. Un
'cancel_goal_async()' de rclpy llama a ESE MISMO servicio. El camino que recorre
el coordinador es identico; lo unico distinto es quien aprieta el boton. La
comprobacion de que el boton de la HRI llega hasta aqui es aparte y no la cubre
este script.

Uso:
    source ~/deepracer_sim_ws/install/setup.bash
    python3 herramientas/cancelar_mision.py --origen piso1_etm6 --destino piso1_etm9

    # corrida de CONTROL: la misma mision sin cancelar nunca
    python3 herramientas/cancelar_mision.py --origen piso1_etm6 --destino piso1_etm9 --sin-cancelar

Imprime, y esto es lo que hay que anotar en la hoja de campo:
  - el instante y la distancia a la escalera EN EL MOMENTO de cancelar,
  - el resultado de la accion: exito, motivo_fallo, relevos, tiempo.
"""
import argparse
import math
import sys
from pathlib import Path

import rclpy
import yaml
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node

from coordinacion_msgs.action import GuiarUsuario

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml"


def _puntos():
    """Los 31 puntos del catalogo, aplanados. Mismo archivo que lee el coordinador."""
    def walk(o):
        if isinstance(o, dict):
            if "id" in o and "nivel" in o:
                yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    return list(walk(yaml.safe_load(CATALOGO.read_text())))


def escalera_de(nivel):
    """El punto de transferencia de un nivel: a donde RF-29 dice que hay que volver."""
    for p in _puntos():
        if p.get("nivel") == nivel and p.get("es_transferencia"):
            return p
    raise SystemExit(f"El catalogo no tiene punto de transferencia en el nivel {nivel}")


class Disparador(Node):
    def __init__(self, robot, nivel, umbral, sin_cancelar):
        super().__init__("cancelar_mision")
        self.umbral = umbral
        self.sin_cancelar = sin_cancelar
        self.esc = escalera_de(nivel)
        self.ex, self.ey = self.esc["pose"]["x"], self.esc["pose"]["y"]
        self.pose = None
        self.pedida = False
        self.meta = None
        self.cliente = ActionClient(self, GuiarUsuario, "/coordinacion/guiar_usuario")
        self.create_subscription(Odometry, f"/{robot}/odom", self._odom, 10)
        self.create_timer(0.2, self._vigilar)

    def _odom(self, m):
        p = m.pose.pose.position
        self.pose = (p.x, p.y)

    def distancia(self):
        if self.pose is None:
            return None
        return math.hypot(self.pose[0] - self.ex, self.pose[1] - self.ey)

    def _vigilar(self):
        """Cancela en cuanto el robot supera el umbral. Una sola vez."""
        if self.pedida or self.meta is None or self.sin_cancelar:
            return
        d = self.distancia()
        if d is None:
            return
        if d > self.umbral:
            self.pedida = True
            t = self.get_clock().now().nanoseconds / 1e9
            print(f"\n>>> CANCELANDO en t={t:.3f} s, con el robot a {d:.2f} m "
                  f"de {self.esc['id']} (umbral {self.umbral} m)", flush=True)
            self.meta.cancel_goal_async()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--origen", required=True)
    p.add_argument("--destino", required=True)
    p.add_argument("--robot", default="robot1")
    p.add_argument("--nivel", type=int, default=1)
    p.add_argument("--umbral", type=float, default=8.0,
                   help="metros desde la escalera a partir de los cuales se cancela")
    p.add_argument("--sin-cancelar", action="store_true",
                   help="corrida de CONTROL: lanza la mision y no la cancela nunca")
    a = p.parse_args()

    rclpy.init()
    n = Disparador(a.robot, a.nivel, a.umbral, a.sin_cancelar)
    print(f"Escalera del nivel {a.nivel}: {n.esc['id']} ({n.ex}, {n.ey})")
    print("Esperando al servidor /coordinacion/guiar_usuario ...", flush=True)
    if not n.cliente.wait_for_server(timeout_sec=30.0):
        raise SystemExit("No hay servidor de accion. Arranca el coordinador (T3).")

    meta = GuiarUsuario.Goal(origen_id=a.origen, destino_id=a.destino)
    fut = n.cliente.send_goal_async(meta)
    rclpy.spin_until_future_complete(n, fut)
    n.meta = fut.result()
    if not n.meta.accepted:
        raise SystemExit("El coordinador RECHAZO la meta.")
    print(f"Meta aceptada. {a.origen} -> {a.destino}"
          + ("  [CONTROL: no se cancelara]" if a.sin_cancelar else
             f"  [se cancelara al pasar de {a.umbral} m]"), flush=True)

    res = n.meta.get_result_async()
    rclpy.spin_until_future_complete(n, res)
    r = res.result().result
    print("\n=== RESULTADO ===")
    print(f"  exito          : {r.exito}")
    print(f"  motivo_fallo   : '{r.motivo_fallo}'")
    print(f"  num_relevos    : {r.num_relevos}")
    print(f"  tiempo_total_s : {r.tiempo_total_s:.2f}")
    d = n.distancia()
    print(f"  distancia final a {n.esc['id']}: "
          + (f"{d:.3f} m" if d is not None else "(sin /odom)"))
    print("Corta la grabadora (T4) AHORA y anota estas cifras.")
    n.destroy_node()
    rclpy.shutdown()
    return 0 if not r.exito or a.sin_cancelar else 0


if __name__ == "__main__":
    sys.exit(main())
