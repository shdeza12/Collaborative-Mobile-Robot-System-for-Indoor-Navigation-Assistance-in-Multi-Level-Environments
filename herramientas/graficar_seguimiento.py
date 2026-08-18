#!/usr/bin/env python3
"""Figura de seguimiento angular y trayectoria a partir de rosbags2 sqlite3.

Por que existe
--------------
Las metricas de `analizar_maniobra.py` son numeros; ante un jurado hace falta
ver la curva. Esta herramienta dibuja, para una pareja de corridas, el giro
comandado contra el giro real y la trayectoria seguida, de modo que el efecto
de un cambio en el control se aprecie sin leer una tabla.

Uso:
    python3 herramientas/graficar_seguimiento.py <salida.png> \
        <dir_bag> <etiqueta> <dir_bag> <etiqueta> [...]
"""

import math
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.serialization import deserialize_message

# Velocidad por debajo de la cual el giro comandado no es interpretable.
V_MINIMA = 0.05


def yaw_de(o):
    return math.atan2(2.0 * (o.w * o.z), 1.0 - 2.0 * o.z * o.z)


def leer(directorio):
    db = sorted(Path(directorio).glob("*.db3"))
    if not db:
        raise SystemExit(f"no hay .db3 en {directorio}")
    con = sqlite3.connect(db[0])
    tid = {n: i for i, n in con.execute("select id,name from topics")}

    def topico(nombre, tipo):
        return [
            (ts, deserialize_message(bytes(d), tipo))
            for ts, d in con.execute(
                "select timestamp,data from messages where topic_id=? order by timestamp",
                (tid[nombre],),
            )
        ]

    return topico("/odom", Odometry), topico("/cmd_vel", Twist)


def series(odom, cmd):
    """Devuelve (t, wz comandado, wz real) solo mientras el vehiculo avanza."""
    t0 = odom[0][0]
    j = 0
    t, comandado, real = [], [], []
    for i in range(1, len(odom)):
        dt = (odom[i][0] - odom[i - 1][0]) / 1e9
        if dt <= 0:
            continue
        if abs(odom[i][1].twist.twist.linear.x) < V_MINIMA:
            continue
        dy = (yaw_de(odom[i][1].pose.pose.orientation)
              - yaw_de(odom[i - 1][1].pose.pose.orientation))
        dy = (dy + math.pi) % (2 * math.pi) - math.pi
        while j + 1 < len(cmd) and cmd[j + 1][0] <= odom[i][0]:
            j += 1
        t.append((odom[i][0] - t0) / 1e9)
        comandado.append(cmd[j][1].angular.z)
        real.append(dy / dt)
    return t, comandado, real


def trayectoria(odom):
    return ([m.pose.pose.position.x for _, m in odom],
            [m.pose.pose.position.y for _, m in odom])


def main(salida, corridas):
    n = len(corridas)
    fig, ejes = plt.subplots(2, n, figsize=(6.0 * n, 7.0))
    if n == 1:
        ejes = [[ejes[0]], [ejes[1]]]

    datos = []
    for directorio, etiqueta in corridas:
        odom, cmd = leer(directorio)
        datos.append((etiqueta, series(odom, cmd), trayectoria(odom)))

    # Escala comun: un limite por panel dejaria fuera los picos del peor caso y
    # haria parecer que las dos corridas se mueven en el mismo rango.
    tope = 1.05 * max(abs(v) for _, (_, c, r), _ in datos for v in c + r)

    for k, (etiqueta, (t, comandado, real), (x, y)) in enumerate(datos):
        ax = ejes[0][k]
        ax.plot(t, comandado, color="tab:blue", lw=1.2, label="comandado por Nav2 (angular.z)")
        ax.plot(t, real, color="tab:red", lw=1.0, alpha=0.85, label="giro real medido")
        ax.set_title(etiqueta)
        ax.set_xlabel("t (s)")
        ax.set_ylabel("velocidad angular (rad/s)")
        ax.set_ylim(-tope, tope)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper right")

        ax = ejes[1][k]
        ax.plot(x, y, color="tab:green", lw=1.4)
        ax.plot(x[0], y[0], "o", color="black", ms=6, label="inicio")
        ax.plot(x[-1], y[-1], "s", color="tab:orange", ms=6, label="fin")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(salida, dpi=140)
    print(f"escrito {salida}")


if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) % 2 != 0:
        raise SystemExit(__doc__)
    args = sys.argv[2:]
    main(sys.argv[1], list(zip(args[0::2], args[1::2])))
