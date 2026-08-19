#!/usr/bin/env python3
"""Dibuja el plan de Nav2 sobre el mapa, marcando las cuspides.

Por que existe
--------------
La captura de pantalla de RViz es fragil: el plan solo esta dibujado unos
segundos y quien mira la imagen no puede comprobar nada. El plan viaja en el
bag, asi que se puede volver a dibujar cuantas veces haga falta, con las
cuspides senaladas y sobre el mismo mapa contra el que se planifico.

Una cuspide es un cambio de sentido de marcha: el avance deja de proyectarse
sobre el rumbo del vehiculo. Un Ackermann no gira sobre su eje, asi que la
cuspide es como resuelve una inversion de rumbo cuando la vuelta en U no le sale
a cuenta.

Por que no le sale a cuenta AQUI es una pregunta abierta, y conviene no darla por
contestada: el pasillo tiene 4,98 m libres en la zona de la maniobra y el
planificador usa minimum_turning_radius 0,35 m, de modo que la vuelta en U cabe
con holgura. La causa apunta al gradiente de la capa de inflacion (0,55 m) frente
al reverse_penalty (2,1), no a la geometria. Sin medirlo es solo una hipotesis.

Uso:
    python3 herramientas/graficar_plan.py <dir_bag> <mapa.yaml> <salida.png>
"""

import math
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import yaml

from nav_msgs.msg import Odometry, Path as PathMsg
from rclpy.serialization import deserialize_message


def yaw_de(o):
    return math.atan2(2.0 * (o.w * o.z), 1.0 - 2.0 * o.z * o.z)


def leer(directorio, topico, tipo):
    db = sorted(Path(directorio).glob("*.db3"))
    if not db:
        raise SystemExit(f"no hay .db3 en {directorio}")
    con = sqlite3.connect(db[0])
    tid = {n: i for i, n in con.execute("select id,name from topics")}
    if topico not in tid:
        raise SystemExit(f"{directorio}: no contiene {topico}")
    return [
        (ts, deserialize_message(bytes(d), tipo))
        for ts, d in con.execute(
            "select timestamp,data from messages where topic_id=? order by timestamp",
            (tid[topico],),
        )
    ]


def cuspides(poses):
    """Indices de los puntos donde el plan invierte el sentido de marcha."""
    idx = []
    anterior = None
    for i in range(1, len(poses)):
        a, b = poses[i - 1].pose, poses[i].pose
        h = yaw_de(a.orientation)
        d = ((b.position.x - a.position.x) * math.cos(h)
             + (b.position.y - a.position.y) * math.sin(h))
        if anterior is not None and d * anterior < 0:
            idx.append(i - 1)
        if abs(d) > 1e-9:
            anterior = d
    return idx


def main(directorio, mapa_yaml, salida):
    planes = leer(directorio, "/plan", PathMsg)
    odom = leer(directorio, "/odom", Odometry)
    con_poses = [(ts, m) for ts, m in planes if m.poses]
    if not con_poses:
        raise SystemExit(f"{directorio}: ningun /plan trae poses")

    # El primero es el que interesa: el que el planificador propuso antes de que
    # el vehiculo se moviera. Los siguientes son el mismo plan ya consumido.
    _, plan = con_poses[0]
    px = [p.pose.position.x for p in plan.poses]
    py = [p.pose.position.y for p in plan.poses]
    idx = cuspides(plan.poses)

    meta = yaml.safe_load(open(mapa_yaml))
    img = mpimg.imread(str(Path(mapa_yaml).parent / meta["image"]))
    res, (ox, oy) = meta["resolution"], meta["origin"][:2]
    extent = [ox, ox + img.shape[1] * res, oy, oy + img.shape[0] * res]

    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.imshow(img, cmap="gray", extent=extent, origin="upper", vmin=0, vmax=255)
    ox_real = [m.pose.pose.position.x for _, m in odom]
    oy_real = [m.pose.pose.position.y for _, m in odom]
    ax.plot(ox_real, oy_real, color="tab:orange", lw=1.0, alpha=0.8,
            label="recorrido real")
    ax.plot(px, py, color="tab:green", lw=2.0, label="plan de Nav2")
    if idx:
        ax.plot([px[i] for i in idx], [py[i] for i in idx], "*", color="red",
                ms=16, label=f"cuspide ({len(idx)})")
    ax.plot(px[0], py[0], "o", color="black", ms=7, label="inicio")
    ax.plot(px[-1], py[-1], "s", color="tab:blue", ms=7, label="meta")

    # Se recorta en x -el mapa mide 44 m y el plan solo usa un tramo- pero NO en
    # y: las paredes del pasillo estan en los bordes del mapa y recortarlas
    # dejaria el plan flotando sobre un fondo blanco, sin el entorno que le da
    # sentido.
    ax.set_xlim(min(px) - 1.5, max(px) + 1.5)
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend(fontsize=8, loc="upper right", ncol=5)

    # A escala del pasillo entero la maniobra ocupa un metro de dieciseis y no
    # se distingue. La ampliacion es la figura: lo demas es el contexto.
    if idx:
        cx, cy = px[idx[0]], py[idx[0]]
        lupa = ax.inset_axes([0.30, 0.50, 0.20, 0.44])
        lupa.imshow(img, cmap="gray", extent=extent, origin="upper", vmin=0, vmax=255)
        lupa.plot(ox_real, oy_real, color="tab:orange", lw=1.6)
        lupa.plot(px, py, color="tab:green", lw=2.4)
        lupa.plot([px[i] for i in idx], [py[i] for i in idx], "*", color="red", ms=11)
        lupa.set_xlim(cx - 1.2, cx + 1.2)
        lupa.set_ylim(cy - 1.2, cy + 1.2)
        lupa.set_aspect("equal")
        lupa.set_xticks([])
        lupa.set_yticks([])
        lupa.set_title("ampliacion de la maniobra", fontsize=8, pad=3)
        ax.indicate_inset_zoom(lupa, edgecolor="black")

    fig.tight_layout()
    fig.savefig(salida, dpi=150)
    print(f"escrito {salida}  ({len(plan.poses)} poses, {len(idx)} cuspides)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
