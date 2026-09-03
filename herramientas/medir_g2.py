#!/usr/bin/env python3
"""Saca M1 y M2 del G2 a partir de la trayectoria de una pasada.

QUE SON M1 Y M2
---------------
Las dos cifras con las que se decide el G2, definidas en la enmienda del
2026-08-26 de CRONOGRAMA_S17_S32.md:

    M1  desplazamiento que registra /odom  /  desplazamiento real medido con cinta
    M2  error de /amcl_pose contra la marca de cinta al final de la recta

El procedimiento entero esta en Documentos/GUIA_PASADA_LOCALIZACION.md. Esta
herramienta es su Paso 5.

DE DONDE SALEN LAS DOS PARADAS
------------------------------
El procedimiento manda parar 5 s quieto al empezar y 5 s quieto al llegar, con
la grabacion corriendo. Esas dos ventanas son las referencias:

    M1 = |mediana de /odom en la llegada - mediana de /odom en la salida| / largo
    M2 = distancia de la mediana de /amcl_pose en la llegada a la marca

Se toma la MEDIANA y no el ultimo mensaje porque un solo mensaje es ruido; con
la ventana entera el ruido se promedia y el resultado deja de depender de en que
instante exacto se cerro la grabacion.

POR QUE LA QUIETUD SE DETECTA SOBRE /odom Y NO SOBRE LOS BARRIDOS
-----------------------------------------------------------------
comprobar_movimiento_bag.py detecta quietud sobre los rayos del LiDAR. Aqui se
detecta sobre las poses, que es lo que hay en el CSV, y a primera vista es
circular: si rf2o se congela, un carro en marcha podria parecer quieto.

Medido, no lo es. El 2026-08-26 rf2o registro 28,23 m de 29,94 m reales: se
queda corto un 5,7 %, no se para. Sobre una ventana de 1 s a 0,5 m/s eso son
0,47 m registrados en vez de 0,50 m, diez veces por encima del umbral de 0,05 m.
El fallo de rf2o es una acumulacion lenta, no un atasco, asi que nunca convierte
un tramo conducido en una ventana de parada.

El umbral de 0,05 m es el mismo que usa comprobar_movimiento_bag.py, y por la
misma razon: es el ruido del propio sensor.

USO
    python3 herramientas/medir_g2.py <trayectoria.csv> --largo L
                                     [--sentido auto|ida|vuelta]
                                     [--estacion 20.0]
                                     [--json salida.json]

    <trayectoria.csv>  lo que produce localizar_desde_bag.sh
    --largo            longitud real de la recta, medida con cinta, en metros
    --sentido          por defecto se deduce de la primera pose de AMCL
    --estacion         evalua tambien en la marca intermedia (x del mapa, en m)

NO DEVUELVE UN NUMERO INVENTADO
-------------------------------
Falla ruidosamente si no encuentra dos ventanas de parada, si /amcl_pose esta
vacio, o si el largo no es positivo. Un G2 con una cifra fabricada es peor que
un G2 sin cifra.
"""

import argparse
import bisect
import csv
import io
import json
import math
import statistics
import sys

# Mismo umbral que comprobar_movimiento_bag.py: es el ruido del sensor.
UMBRAL_QUIETO_M = 0.05
# Ventana sobre la que se mide el desplazamiento para decidir quieto/movido.
VENTANA_S = 1.0
# El procedimiento manda paradas de 5 s. Se aceptan desde 2 s por si la del
# viernes sale corta; por debajo no hay de donde sacar una mediana creible.
PARADA_MINIMA_S = 2.0


class Fallo(Exception):
    """Algo impide dar una cifra honesta. Se aborta en vez de inventarla."""


# ------------------------------------------------------------------- lectura


def leer_csv(texto):
    """Reparte el CSV en {'odom': [(t,x,y,yaw)], 'amcl': [...]}, ordenado."""
    pistas = {"odom": [], "amcl": []}
    lector = csv.DictReader(io.StringIO(texto))
    esperadas = {"t", "fuente", "x", "y", "yaw"}
    if not lector.fieldnames or not esperadas.issubset(lector.fieldnames):
        raise Fallo(f"el CSV no tiene las columnas {sorted(esperadas)}; "
                    f"tiene {lector.fieldnames}")
    for fila in lector:
        f = (fila["fuente"] or "").strip()
        if f not in pistas:
            continue
        try:
            pistas[f].append((float(fila["t"]), float(fila["x"]),
                              float(fila["y"]), float(fila["yaw"])))
        except (TypeError, ValueError):
            continue
    for f in pistas:
        pistas[f].sort()
    return pistas


# ------------------------------------------------------- ventanas de parada


def ventanas_quietas(pista, umbral=UMBRAL_QUIETO_M, ventana_s=VENTANA_S,
                     minima_s=PARADA_MINIMA_S):
    """Devuelve [(t_inicio, t_fin)] de los tramos en que la pose no se mueve.

    Para cada muestra mira las que caen a menos de media ventana por delante y
    por detras, y la marca quieta si entre la primera y la ultima de ese grupo
    hay menos de `umbral` metros. Ventana centrada para que las muestras de los
    dos extremos del CSV se clasifiquen igual de bien que las de en medio.
    """
    if len(pista) < 2:
        return []
    ts = [p[0] for p in pista]
    media = ventana_s / 2.0
    marcas = []
    for i in range(len(pista)):
        lo = bisect.bisect_left(ts, ts[i] - media)
        hi = bisect.bisect_right(ts, ts[i] + media) - 1
        d = math.dist(pista[lo][1:3], pista[hi][1:3])
        marcas.append(d < umbral)

    ventanas = []
    ini = None
    for i, quieto in enumerate(marcas):
        if quieto and ini is None:
            ini = i
        elif not quieto and ini is not None:
            ventanas.append((ini, i - 1))
            ini = None
    if ini is not None:
        ventanas.append((ini, len(marcas) - 1))

    return [(ts[a], ts[b]) for a, b in ventanas if ts[b] - ts[a] >= minima_s]


def mediana_en(pista, t0, t1):
    """Mediana de (x, y) de las muestras cuyo tiempo cae en [t0, t1]."""
    xs = [p[1] for p in pista if t0 <= p[0] <= t1]
    ys = [p[2] for p in pista if t0 <= p[0] <= t1]
    if not xs:
        return None
    return (statistics.median(xs), statistics.median(ys))


# --------------------------------------------------------------- la medicion


def _m2(amcl_xy, marca):
    dx = amcl_xy[0] - marca[0]
    dy = amcl_xy[1] - marca[1]
    return math.hypot(dx, dy), abs(dx), abs(dy)


def medir(texto_csv, largo, sentido="auto", estacion=None):
    """Devuelve el diccionario con M1, M2 y sus componentes.

    Lanza Fallo si no hay con que medir.
    """
    if not largo or largo <= 0:
        raise Fallo(f"el largo de la recta tiene que ser positivo, y es {largo}")

    pistas = leer_csv(texto_csv)
    odom, amcl = pistas["odom"], pistas["amcl"]
    if len(odom) < 2:
        raise Fallo("el CSV no trae odometria: sin /odom no hay M1")
    if not amcl:
        raise Fallo("el CSV no trae ni una pose de amcl: sin /amcl_pose no hay "
                    "M2. Mira amcl.log; si no dice 'Received a X x Y map', el "
                    "map_server no publico")

    ventanas = ventanas_quietas([(t, x, y) for t, x, y, _ in odom])
    if len(ventanas) < 2:
        raise Fallo(
            f"encuentro {len(ventanas)} ventana(s) de parada y hacen falta dos, "
            f"la de salida y la de llegada. El procedimiento manda parar 5 s "
            f"quieto en cada extremo con la grabacion corriendo "
            f"(GUIA_PASADA_LOCALIZACION.md, Pasos 3.2 y 3.4)")

    salida, llegada = ventanas[0], ventanas[-1]

    if sentido == "auto":
        x0 = amcl[0][1]
        sentido = "ida" if abs(x0) <= abs(x0 - largo) else "vuelta"
    if sentido not in ("ida", "vuelta"):
        raise Fallo(f"sentido desconocido: {sentido}")

    marca_salida = (0.0, 0.0) if sentido == "ida" else (largo, 0.0)
    marca_llegada = (largo, 0.0) if sentido == "ida" else (0.0, 0.0)

    o_ini = mediana_en(odom, *salida)
    o_fin = mediana_en(odom, *llegada)
    recorrido = math.dist(o_ini, o_fin)

    a_fin = mediana_en(amcl, *llegada)
    if a_fin is None:
        raise Fallo("no hay ni una pose de amcl dentro de la ventana de "
                    "llegada. Baja update_min_d, o alarga la parada final")
    m2, m2_long, m2_lat = _m2(a_fin, marca_llegada)

    r = {
        "sentido": sentido,
        "largo_real_m": largo,
        "ventana_salida_s": list(salida),
        "ventana_llegada_s": list(llegada),
        "odom_recorrido_m": recorrido,
        "m1": recorrido / largo,
        "amcl_llegada": list(a_fin),
        "marca_llegada": list(marca_llegada),
        "m2": m2,
        "m2_longitudinal": m2_long,
        "m2_lateral": m2_lat,
        "estacion": None,
    }

    duracion = llegada[0] - salida[1]
    r["velocidad_media_m_s"] = largo / duracion if duracion > 0 else float("nan")

    if estacion is not None:
        r["estacion"] = _medir_estacion(odom, amcl, ventanas, o_ini, estacion,
                                        marca_salida)
    return r


def _medir_estacion(odom, amcl, ventanas, o_ini, estacion, marca_salida):
    """M1 y M2 en la marca intermedia. Devuelve None si no hubo parada ahi."""
    intermedias = ventanas[1:-1]
    if not intermedias:
        return None
    # La parada intermedia es aquella cuya pose de amcl cae mas cerca de la marca.
    mejor, mejor_d = None, float("inf")
    for v in intermedias:
        a = mediana_en(amcl, *v)
        if a is None:
            continue
        d = abs(a[0] - estacion)
        if d < mejor_d:
            mejor, mejor_d = v, d
    if mejor is None:
        return None

    recorrido_real = abs(estacion - marca_salida[0])
    if recorrido_real <= 0:
        return None
    o_est = mediana_en(odom, *mejor)
    a_est = mediana_en(amcl, *mejor)
    m2, m2_long, m2_lat = _m2(a_est, (estacion, 0.0))
    return {
        "marca_m": estacion,
        "recorrido_real_m": recorrido_real,
        "ventana_s": list(mejor),
        "odom_recorrido_m": math.dist(o_ini, o_est),
        "m1": math.dist(o_ini, o_est) / recorrido_real,
        "amcl": list(a_est),
        "m2": m2,
        "m2_longitudinal": m2_long,
        "m2_lateral": m2_lat,
    }


# --------------------------------------------------------------------- salida


def informe(r):
    s = r["ventana_salida_s"]
    ll = r["ventana_llegada_s"]
    print()
    print(f"  sentido           : {r['sentido']}  "
          f"(recta de {r['largo_real_m']:.2f} m medida con cinta)")
    print(f"  ventana de salida : {s[0]:.1f} - {s[1]:.1f} s")
    print(f"  ventana de llegada: {ll[0]:.1f} - {ll[1]:.1f} s")
    print(f"  velocidad media   : {r['velocidad_media_m_s']:.2f} m/s")
    print()
    print(f"  M1  desplazamiento odom {r['odom_recorrido_m']:.2f} m "
          f"/ real {r['largo_real_m']:.2f} m  =  {r['m1']:.3f}")
    print(f"  M2  amcl ({r['amcl_llegada'][0]:.2f} , {r['amcl_llegada'][1]:.2f})"
          f"  vs  marca ({r['marca_llegada'][0]:.2f} , "
          f"{r['marca_llegada'][1]:.2f})  =  {r['m2']:.2f} m")
    print(f"      componente longitudinal {r['m2_longitudinal']:.2f} m   "
          f"lateral {r['m2_lateral']:.2f} m")
    e = r.get("estacion")
    if e:
        print()
        print(f"  En la marca intermedia de {e['marca_m']:.2f} m "
              f"({e['recorrido_real_m']:.2f} m recorridos):")
        print(f"  M1  {e['odom_recorrido_m']:.2f} m / "
              f"{e['recorrido_real_m']:.2f} m  =  {e['m1']:.3f}")
        print(f"  M2  {e['m2']:.2f} m   "
              f"(longitudinal {e['m2_longitudinal']:.2f} m, "
              f"lateral {e['m2_lateral']:.2f} m)")
    print()
    print("  Los umbrales NO se aplican aqui a proposito: se deciden antes de")
    print("  salir al pasillo y los firma el director. Paso 1.3 de la guia.")


def main():
    p = argparse.ArgumentParser(
        description="Saca M1 y M2 de la trayectoria de una pasada del G2.")
    p.add_argument("trayectoria", help="CSV de localizar_desde_bag.sh")
    p.add_argument("--largo", type=float, required=True,
                   help="longitud real de la recta, con cinta, en metros")
    p.add_argument("--sentido", default="auto",
                   choices=["auto", "ida", "vuelta"])
    p.add_argument("--estacion", type=float, default=None,
                   help="marca intermedia, en x del mapa (p. ej. 20.0)")
    p.add_argument("--json", default=None, help="vuelca el resultado a un JSON")
    a = p.parse_args()

    try:
        with open(a.trayectoria, encoding="utf-8") as f:
            texto = f.read()
    except OSError as e:
        print(f"ERROR: no puedo leer {a.trayectoria}: {e}", file=sys.stderr)
        return 2

    try:
        r = medir(texto, a.largo, a.sentido, a.estacion)
    except Fallo as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    informe(r)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(r, f, indent=2, ensure_ascii=False)
        print(f"\n  JSON en {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
