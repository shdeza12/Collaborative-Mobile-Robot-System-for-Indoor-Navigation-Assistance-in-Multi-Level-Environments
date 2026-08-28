#!/usr/bin/env python3
"""Explica POR QUE una mision llego donde llego, leyendo su bag.

El coordinador dice "0.316 m, FALLIDA" y ahi se acaba. Ese numero no distingue
entre causas que piden arreglos opuestos, y el 2026-08-27 se perdio una tarde
justamente por eso: se dieron por buenas tres explicaciones seguidas -que el
planificador truncaba el camino, que AMCL iba mal al llegar, que el carro
retrocedia tras parar- y las tres eran falsas. Ninguna se habia medido.

Este script descompone el error de llegada en las tres piezas que lo forman, que
se arreglan en sitios distintos:

  1. CONDICION INICIAL. Si el robot no arranco donde dice la tabla, todo lo
     demas lleva ese sesgo dentro. Se arregla con verificar_condicion_inicial.py
     ANTES de grabar, no despues.

  2. DERIVA DE AMCL. En un pasillo recto el laser fija la posicion lateral y no
     dice nada de la longitudinal, asi que el ruido del modelo de movimiento se
     acumula sobre el eje largo. Se ve en que el error crece con el RECORRIDO y
     esta casi todo en una componente. Se arregla con los alpha de amcl.

  3. UMBRAL DE PARADA. Nav2 para cuando SU ESTIMACION baja de
     xy_goal_tolerance; el criterio de exito se mide contra /odom, que es la
     verdad. Si los dos numeros son iguales el margen es cero y la mision falla
     por construccion. Se ve en que, en el instante de la decision, la distancia
     creida esta dentro y la real fuera. Se arregla con xy_goal_tolerance.

     ESTA PIEZA ESTUVO MAL MEDIDA hasta el 2026-08-27 por la tarde, y conviene
     dejarlo escrito. Tomaba como "lo que creia Nav2" la distancia entre los dos
     extremos del ultimo /plan publicado. Eso no es una creencia: es la LONGITUD
     de ese plan, y Hybrid-A* la deja siempre igual. Medido en los tres bags de
     ese dia -S20_rutas_01, 02 y 03- daba 0.240 m en los tres. O sea que el
     aviso "paro creyendo que habia llegado" saltaba comparando una constante
     del planificador contra un umbral, y no informaba de nada.

     Se mide bien con /tf, que el bag ya graba: la creencia de Nav2 es
     <ns>/map -> <ns>/odom (la correccion de AMCL) compuesta con
     <ns>/odom -> <ns>/base_link. Y hay que sacarla de ahi y no de /amcl_pose
     porque amcl_pose se publica a saltos -solo al cruzar update_min_d o
     update_min_a- mientras que la transformada va continua: en S20_rutas_03 la
     ultima muestra de amcl_pose es 8.3 s anterior al final del bag, y leerla
     como si fuera la pose de la parada da 0.390 m donde la transformada da
     0.032 m de error.

En simulacion /odom NO es odometria: es la pose del mundo de Gazebo
(gazebo_ros_deepracer_drive.cpp:229), o sea verdad de terreno. Todo este script
depende de eso, y por eso se niega a opinar sobre un bag sin /clock.

Uso:
    python3 herramientas/diagnosticar_llegada.py ~/tesis_evidencia/S20_rutas_01
    python3 herramientas/diagnosticar_llegada.py <bag> --robot robot1

Codigo de salida: 0 si la llegada cumple el criterio, 1 si no o si no se puede
decidir.
"""

import argparse
import math
import os
import sys

import rosbag2_py
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, Path
from rclpy.serialization import deserialize_message
from tf2_msgs.msg import TFMessage

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Robot", "aws-deepracer", "deepracer_bringup", "launch"))
from deepracer_raiz_repo import pose_por_defecto  # noqa: E402

# El criterio de llegada del protocolo. NO se toca desde aqui: se fijo en
# PROTOCOLO_EXPERIMENTAL.md antes de instrumentar, justamente para que ningun
# umbral se eligiera despues de ver resultados.
#
# NO es la 'xy_goal_tolerance' de Nav2, aunque hasta el 2026-08-27 valian lo
# mismo. La tolerancia dice cuando Nav2 PARA, y se midio contra el /odom del
# bag; este numero dice cuando la llegada se acepta. Separarlos fue el arreglo
# de ese dia: parar en 0.15 es lo que deja margen para cumplir 0.25.
TOLERANCIA_LLEGADA_M = 0.25


def _yaw(q):
    return math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)


def _d(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def leer_bag(ruta, robot):
    """Saca de un bag lo justo para el diagnostico.

    Devuelve (odom, amcl, planes, correccion, meta, hay_clock). 'meta' sale de
    /coordinacion/estado_mision, que es la unica fuente que dice a que punto se
    iba de verdad; sin el no se puede medir un error de llegada y el script lo
    dice en vez de inventarse una meta.
    """
    lector = rosbag2_py.SequentialReader()
    lector.open(rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
                rosbag2_py.ConverterOptions("", ""))
    tipos = {t.name: t.type for t in lector.get_all_topics_and_types()}

    t_odom = f"/{robot}/odom"
    t_amcl = f"/{robot}/amcl_pose"
    t_plan = f"/{robot}/plan"

    odom, amcl, planes, correccion = [], [], [], []
    meta = None
    hay_clock = "/clock" in tipos

    while lector.has_next():
        topico, datos, t = lector.read_next()
        if topico == "/tf":
            # <ns>/map -> <ns>/odom es la correccion de AMCL, y es lo que
            # convierte la pose de /odom en la pose que Nav2 CREE. Se publica
            # continua, a diferencia de /amcl_pose. Ver la pieza 3 de la
            # cabecera.
            for tr in deserialize_message(datos, TFMessage).transforms:
                if (tr.header.frame_id == f"{robot}/map"
                        and tr.child_frame_id == f"{robot}/odom"):
                    correccion.append((t * 1e-9,
                                       tr.transform.translation.x,
                                       tr.transform.translation.y,
                                       _yaw(tr.transform.rotation)))
        elif topico == t_odom:
            p = deserialize_message(datos, Odometry).pose.pose
            odom.append((t * 1e-9, p.position.x, p.position.y,
                         _yaw(p.orientation)))
        elif topico == t_amcl:
            p = deserialize_message(datos, PoseWithCovarianceStamped).pose.pose
            amcl.append((t * 1e-9, p.position.x, p.position.y))
        elif topico == t_plan:
            m = deserialize_message(datos, Path)
            if m.poses:
                planes.append((t * 1e-9,
                               m.poses[0].pose.position,
                               m.poses[-1].pose.position))
        elif topico == "/coordinacion/estado_mision":
            # El tipo es propio del proyecto. Si este proceso no lo puede
            # resolver es que falta sourcear el workspace, y conviene decirlo
            # con esas palabras en vez de reventar con un ImportError.
            try:
                from coordinacion_msgs.msg import EstadoMision
            except ImportError:
                continue
            m = deserialize_message(datos, EstadoMision)
            if m.destino_actual.id:
                meta = (m.destino_actual.id,
                        m.destino_actual.pose.position.x,
                        m.destino_actual.pose.position.y)

    return odom, amcl, planes, correccion, meta, hay_clock


def recorrido_acumulado(odom):
    """Distancia recorrida de verdad hasta cada muestra."""
    acc, rec = 0.0, [0.0]
    for i in range(1, len(odom)):
        acc += _d(odom[i][1], odom[i][2], odom[i - 1][1], odom[i - 1][2])
        rec.append(acc)
    return rec


def mas_cercana(odom, t):
    return min(range(len(odom)), key=lambda k: abs(odom[k][0] - t))


def creencia(correccion, muestra_odom):
    """Donde CREE Nav2 que esta el robot, en el marco del mapa.

    Compone la ultima correccion de AMCL vigente (<ns>/map -> <ns>/odom) con la
    pose de /odom. Devuelve (x, y, antiguedad de la correccion en segundos), o
    None si no hay ninguna correccion anterior a esa muestra.
    """
    t, x, y = muestra_odom[0], muestra_odom[1], muestra_odom[2]
    previas = [c for c in correccion if c[0] <= t]
    if not previas:
        return None
    tc, cx, cy, ca = previas[-1]
    return (cx + x * math.cos(ca) - y * math.sin(ca),
            cy + x * math.sin(ca) + y * math.cos(ca),
            t - tc)


def instante_de_parada(odom, umbral_v=0.02):
    """Indice de la ultima muestra en que el robot aun se movia.

    No se usa /cmd_vel: el mando puede seguir publicandose despues de que el
    vehiculo se haya detenido, y lo que interesa es cuando dejo de moverse de
    verdad. El umbral es 0.02 m/s, muy por encima de los 0.0003 m/s del
    deslizamiento de ODE (ver verificar_condicion_inicial.py) y muy por debajo
    del desired_linear_vel de 0.5.
    """
    for i in range(len(odom) - 1, 0, -1):
        dt = odom[i][0] - odom[i - 1][0]
        if dt <= 0:
            continue
        v = _d(odom[i][1], odom[i][2], odom[i - 1][1], odom[i - 1][2]) / dt
        if v > umbral_v:
            return i
    return len(odom) - 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bag")
    ap.add_argument("--robot", default="robot1")
    # Sin '--spawn' se toma la fila del robot pedido, no una constante. Estuvo
    # fijada a la de robot1 hasta el 2026-08-27, y con '--robot robot2' el
    # informe acusaba 15.868 m de desvio en una corrida que arranco a 0.039 m de
    # su pose declarada: la pieza 1 comparaba contra el spawn del otro robot.
    ap.add_argument("--spawn", nargs=2, type=float, metavar=("X", "Y"),
                    default=None,
                    help="pose declarada de spawn, para la pieza 1; por defecto "
                         "la de POSE_INICIAL para --robot")
    args = ap.parse_args()
    if args.spawn is None:
        fila = pose_por_defecto(args.robot)
        args.spawn = [fila["x"], fila["y"]]

    if not os.path.exists(os.path.join(args.bag, "metadata.yaml")):
        print(f"No parece un bag: {args.bag}")
        return 1

    odom, amcl, planes, correccion, meta, hay_clock = leer_bag(
        args.bag, args.robot)

    if not odom:
        print(f"El bag no trae /{args.robot}/odom. Sin verdad de terreno no hay")
        print("nada que diagnosticar.")
        return 1
    if not hay_clock:
        print("El bag no trae /clock, asi que no se grabo con --use-sim-time o")
        print("no venia de simulacion. Fuera de simulacion /odom es odometria")
        print("de verdad, con deriva, y este diagnostico no vale. No opino.")
        return 1

    rec = recorrido_acumulado(odom)
    print(f"Diagnostico de llegada: {os.path.basename(args.bag)} ({args.robot})")
    print(f"  muestras: {len(odom)} de odom, {len(amcl)} de amcl_pose, "
          f"{len(planes)} planes")
    print(f"  recorrido real: {rec[-1]:.2f} m")

    # ---- pieza 1: condicion inicial -------------------------------------
    d0 = _d(odom[0][1], odom[0][2], args.spawn[0], args.spawn[1])
    print(f"\n1. CONDICION INICIAL")
    print(f"   arranco en ({odom[0][1]:.3f}, {odom[0][2]:.3f}), "
          f"declarada ({args.spawn[0]:.3f}, {args.spawn[1]:.3f})")
    print(f"   desvio: {d0:.3f} m", end="")
    print("   <-- ya arranca sesgado" if d0 > 0.15 else "   ok")

    # ---- pieza 2: deriva de AMCL ----------------------------------------
    print(f"\n2. DERIVA DE AMCL (error contra la verdad, segun el recorrido)")
    if not amcl:
        print("   sin amcl_pose en el bag: no se puede separar esta pieza.")
        peor = None
    else:
        filas, peor = [], 0.0
        for ta, xa, ya in amcl:
            i = mas_cercana(odom, ta)
            if abs(odom[i][0] - ta) > 0.3:
                continue
            ex, ey = xa - odom[i][1], ya - odom[i][2]
            e = math.hypot(ex, ey)
            peor = max(peor, e)
            filas.append((rec[i], e, ex, ey))
        paso = max(1, len(filas) // 10)
        print("     recorrido   error     ex       ey")
        for r, e, ex, ey in filas[::paso]:
            print(f"     {r:7.2f} m  {e:6.3f}  {ex:+7.3f} {ey:+7.3f}")
        print(f"   peor error de AMCL en toda la mision: {peor:.3f} m")
        if filas and rec[-1] > 1.0:
            tasa = peor / max(rec[-1], 1e-9)
            print(f"   tasa: {tasa:.4f} m por metro recorrido")
            if filas:
                sx = sum(abs(f[2]) for f in filas)
                sy = sum(abs(f[3]) for f in filas)
                if sx + sy > 0 and max(sx, sy) / (sx + sy) > 0.8:
                    eje = "X" if sx > sy else "Y"
                    print(f"   el error esta casi todo en {eje}: es la firma del")
                    print(f"   pasillo sin rasgos, no un fallo del filtro.")

    # ---- pieza 3: umbral de parada --------------------------------------
    print(f"\n3. UMBRAL DE PARADA (instante en que Nav2 se dio por llegado)")
    if not planes:
        print("   sin /plan en el bag: no se sabe a que pose se apuntaba.")
    elif not correccion:
        print(f"   el bag no trae la transformada {args.robot}/map -> "
              f"{args.robot}/odom:")
        print("   sin ella no se puede saber que creia Nav2. Grabar /tf.")
    else:
        # La meta que perseguia Nav2 es el extremo del ultimo plan, ya en el
        # marco del mapa. La distancia entre los dos extremos del plan NO sirve
        # para nada aqui: es su longitud. Ver la pieza 3 de la cabecera.
        _, _, fin = planes[-1]
        i = instante_de_parada(odom)
        cr = creencia(correccion, odom[i])
        real = _d(odom[i][1], odom[i][2], fin.x, fin.y)
        print(f"   dejo de moverse en t+{odom[i][0] - odom[0][0]:.1f} s")
        if cr is None:
            print("   no hay correccion de AMCL anterior a ese instante.")
        else:
            creida = _d(cr[0], cr[1], fin.x, fin.y)
            print(f"   Nav2 se creia a  {creida:.3f} m de la meta")
            print(f"   estaba de verdad a {real:.3f} m")
            print(f"   error de localizacion en ese instante: "
                  f"{_d(cr[0], cr[1], odom[i][1], odom[i][2]):.3f} m")
            print(f"   (correccion de AMCL vigente, publicada {cr[2]:.2f} s "
                  f"antes)")
            if creida < TOLERANCIA_LLEGADA_M <= real:
                print("   <-- paro creyendo que habia llegado, sin haber "
                      "llegado.")
                print("       Margen cero: bajar xy_goal_tolerance.")

    # ---- veredicto -------------------------------------------------------
    print(f"\nVEREDICTO")
    if meta is None:
        print("  El bag no dice a que punto se iba (falta")
        print("  /coordinacion/estado_mision, o falta sourcear el workspace")
        print("  para poder deserializarlo). Las tres piezas de arriba valen;")
        print("  el error de llegada no se puede calcular.")
        return 1

    nombre, mx, my = meta
    err = _d(odom[-1][1], odom[-1][2], mx, my)
    print(f"  destino {nombre} en ({mx:.3f}, {my:.3f})")
    print(f"  el robot acabo en ({odom[-1][1]:.3f}, {odom[-1][2]:.3f})")
    print(f"  error de llegada: {err:.3f} m   (criterio {TOLERANCIA_LLEGADA_M} m)")
    if err <= TOLERANCIA_LLEGADA_M:
        print("  CUMPLE.")
        return 0
    print("  NO CUMPLE. Mirar cual de las tres piezas de arriba lo explica")
    print("  antes de tocar nada: se arreglan en sitios distintos.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
