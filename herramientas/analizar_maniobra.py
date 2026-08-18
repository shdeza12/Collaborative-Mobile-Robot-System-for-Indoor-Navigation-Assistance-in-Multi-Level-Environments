#!/usr/bin/env python3
"""Metricas de una maniobra de navegacion a partir de un rosbag2 sqlite3.

Por que existe
--------------
Nav2 devuelve SUCCEEDED comparando su propia estimacion contra la meta, no la
posicion real. Este script mide contra `/odom`, que en esta simulacion es la
pose verdadera de Gazebo (`model_->WorldPose()` en el plugin Ackermann), de modo
que el error de llegada y el error de localizacion quedan separados.

Se espera un bag con /odom, /cmd_vel, /plan y /amcl_pose.

Uso:
    python3 herramientas/analizar_maniobra.py <dir_bag> <meta_x> <meta_y> [etiqueta]
"""

import math
import sqlite3
import sys
from pathlib import Path

from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from nav_msgs.msg import Odometry, Path as PathMsg
from rclpy.serialization import deserialize_message

# Distancia entre ejes y tope de direccion del DeepRacer.
WHEEL_BASE = 0.164023
MAX_STEER = 0.523599
# Radio de giro minimo fisico = WHEEL_BASE / tan(MAX_STEER).
MIN_RADIUS = WHEEL_BASE / math.tan(MAX_STEER)
# Umbral para considerar que el vehiculo se mueve, en m/s.
V_MOVIENDO = 0.01


def yaw_de(o):
    return math.atan2(2.0 * (o.w * o.z), 1.0 - 2.0 * o.z * o.z)


def abrir(directorio):
    db = sorted(Path(directorio).glob("*.db3"))
    if not db:
        raise SystemExit(f"no hay .db3 en {directorio}")
    con = sqlite3.connect(db[0])
    tid = {n: i for i, n in con.execute("select id,name from topics")}
    return con, tid


def leer(con, tid, topico, tipo):
    if topico not in tid:
        return []
    return [
        (ts, deserialize_message(bytes(d), tipo))
        for ts, d in con.execute(
            "select timestamp,data from messages where topic_id=? order by timestamp",
            (tid[topico],),
        )
    ]


def cuspides(poses):
    """Cambios de sentido de marcha: el avance deja de proyectarse sobre el rumbo."""
    n = 0
    anterior = None
    for i in range(1, len(poses)):
        a, b = poses[i - 1].pose, poses[i].pose
        h = yaw_de(a.orientation)
        d = ((b.position.x - a.position.x) * math.cos(h)
             + (b.position.y - a.position.y) * math.sin(h))
        if anterior is not None and d * anterior < 0:
            n += 1
        if abs(d) > 1e-9:
            anterior = d
    return n


def tramos_de_marcha(cmd, t0):
    """Tramos de marcha delimitados por el ultimo comando no nulo.

    Tomar el ultimo mensaje del bag como fin inventa un tramo larguisimo cuando
    la grabacion sigue corriendo despues de que el robot ya se detuvo.
    """
    moviendo = [(ts - t0) / 1e9 for ts, m in cmd if abs(m.linear.x) > V_MOVIENDO]
    if not moviendo:
        return [], 0.0, 0.0
    inicio, fin = moviendo[0], moviendo[-1]
    signo = lambda v: 1 if v > V_MOVIENDO else (-1 if v < -V_MOVIENDO else 0)
    tramos = []
    actual = desde = None
    for ts, m in cmd:
        t = (ts - t0) / 1e9
        if t > fin + 0.01:
            break
        s = signo(m.linear.x)
        if s == 0:
            continue
        if s != actual:
            if actual is not None:
                tramos.append((actual, desde, t))
            actual, desde = s, t
    tramos.append((actual, desde, fin))
    return [x for x in tramos if x[2] - x[1] > 0.05], inicio, fin


def seguimiento(odom, cmd):
    """Contrasta el giro real con el angular.z comandado.

    Se descartan las muestras con el volante al tope: ahi el vehiculo no puede
    obedecer haga lo que haga la conversion, y contaminarian la comparacion.
    """
    j = 0
    err = []
    saturadas = 0
    total = 0
    for i in range(1, len(odom)):
        dt = (odom[i][0] - odom[i - 1][0]) / 1e9
        if dt <= 0:
            continue
        dy = yaw_de(odom[i][1].pose.pose.orientation) - yaw_de(odom[i - 1][1].pose.pose.orientation)
        dy = (dy + math.pi) % (2 * math.pi) - math.pi
        w_real = dy / dt
        v = odom[i][1].twist.twist.linear.x
        while j + 1 < len(cmd) and cmd[j + 1][0] <= odom[i][0]:
            j += 1
        if abs(v) < 0.15:
            continue
        wz = cmd[j][1].angular.z
        total += 1
        if abs(wz * WHEEL_BASE / v) >= math.tan(MAX_STEER) * 0.9:
            saturadas += 1
            continue
        err.append((w_real - wz) ** 2)
    rms = math.sqrt(sum(err) / len(err)) if err else float("nan")
    return rms, saturadas, total


def deriva_en_reposo(odom, t0, hasta):
    reposo = [(ts, m) for ts, m in odom if (ts - t0) / 1e9 < hasta - 0.5]
    if len(reposo) < 20:
        return float("nan"), 0.0
    dy = yaw_de(reposo[-1][1].pose.pose.orientation) - yaw_de(reposo[0][1].pose.pose.orientation)
    dt = (reposo[-1][0] - reposo[0][0]) / 1e9
    return math.degrees(abs(dy)) / dt, dt


def analizar(directorio, meta, etiqueta):
    con, tid = abrir(directorio)
    odom = leer(con, tid, "/odom", Odometry)
    cmd = leer(con, tid, "/cmd_vel", Twist)
    planes = leer(con, tid, "/plan", PathMsg)
    amcl = leer(con, tid, "/amcl_pose", PoseWithCovarianceStamped)
    if not odom:
        raise SystemExit(f"{directorio}: sin mensajes en /odom")
    t0 = odom[0][0]

    tramos, ini, fin = tramos_de_marcha(cmd, t0)

    recorrido = 0.0
    previo = None
    for _, m in odom:
        p = m.pose.pose.position
        if previo:
            recorrido += math.hypot(p.x - previo[0], p.y - previo[1])
        previo = (p.x, p.y)

    final = odom[-1][1].pose.pose
    error_llegada = math.hypot(final.position.x - meta[0], final.position.y - meta[1])

    def verdad(t):
        for i in range(1, len(odom)):
            if odom[i][0] >= t:
                (ta, ma), (tb, mb) = odom[i - 1], odom[i]
                f = (t - ta) / (tb - ta) if tb > ta else 0.0
                pa, pb = ma.pose.pose.position, mb.pose.pose.position
                return (pa.x + f * (pb.x - pa.x), pa.y + f * (pb.y - pa.y))
        p = odom[-1][1].pose.pose.position
        return (p.x, p.y)

    err_loc = sorted(
        math.hypot(m.pose.pose.position.x - verdad(ts)[0], m.pose.pose.position.y - verdad(ts)[1])
        for ts, m in amcl
    )
    rms, saturadas, muestras = seguimiento(odom, cmd)
    deriva, ventana = deriva_en_reposo(odom, t0, ini)
    cusp_plan = max((cuspides(m.poses) for _, m in planes if m.poses), default=0)

    print(f"=== {etiqueta} ===")
    print(f"  bag                   : {directorio}")
    print(f"  meta                  : ({meta[0]:.2f}, {meta[1]:.2f})")
    print(f"  tiempo en movimiento  : {fin - ini:.1f} s")
    print(f"  recorrido             : {recorrido:.2f} m")
    print(f"  llegada real          : ({final.position.x:.3f}, {final.position.y:.3f}) "
          f"yaw {math.degrees(yaw_de(final.orientation)):.1f} deg")
    print(f"  error real de llegada : {error_llegada:.3f} m")
    print(f"  cuspides planificadas : {cusp_plan}   (maximo sobre {len(planes)} planes)")
    print(f"  cuspides ejecutadas   : {max(0, len(tramos) - 1)}   "
          + " ".join(("AD" if s > 0 else "RE") + f"{b - a:.1f}" for s, a, b in tramos))
    print(f"  giro real vs comandado: RMS {rms:.3f} rad/s sobre {muestras - saturadas} muestras")
    print(f"  volante al tope       : {saturadas} de {muestras} "
          f"({100 * saturadas / muestras:.0f}%)" if muestras else "  volante al tope       : n/d")
    if err_loc:
        print(f"  error de localizacion : mediana {err_loc[len(err_loc) // 2]:.3f} m  "
              f"maximo {err_loc[-1]:.3f} m")
    print(f"  deriva en reposo      : {deriva:.4f} deg/s  (ventana de {ventana:.0f} s)")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    analizar(sys.argv[1], (float(sys.argv[2]), float(sys.argv[3])),
             sys.argv[4] if len(sys.argv) > 4 else Path(sys.argv[1]).name)
