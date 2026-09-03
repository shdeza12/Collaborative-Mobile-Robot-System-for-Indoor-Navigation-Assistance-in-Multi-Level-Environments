#!/usr/bin/env python3
"""Pruebas de medir_g2.py. No necesitan ROS, ni un bag, ni el pasillo.

medir_g2.py solo lee un CSV de texto -t,fuente,x,y,yaw- asi que se puede probar
entero con trayectorias de mentira. Lo que necesita ROS es unicamente producir
ese CSV, y de eso se encarga localizar_desde_bag.sh.

El caso que mas importa es `prueba_sesgo_medido`: reproduce el sesgo de +2,9 %
que se midio en simulacion el 2026-08-26 y comprueba que de M1 = 1,029 y
M2 = 0,58 m sobre 20 m. Es el numero que el §4 de S21_preparacion_G2.md predice
para el viernes, y si la herramienta no lo reproduce, la prediccion no se puede
contrastar con nada.

Uso:  python3 herramientas/prueba_medir_g2.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medir_g2 import Fallo, medir, ventanas_quietas

FALLOS = []


def comprobar(nombre, condicion, detalle=""):
    if condicion:
        print(f"  ok   {nombre}")
    else:
        print(f"  FALLO {nombre} {detalle}")
        FALLOS.append(nombre)


def casi(a, b, tol=1e-3):
    return abs(a - b) <= tol


# ---------------------------------------------------------------- generadores


def tramo(t0, dur, x0, x1, fuente, y=0.0, hz=20.0):
    """Muestras de una fuente moviendose linealmente de x0 a x1."""
    n = max(2, int(round(dur * hz)))
    out = []
    for i in range(n):
        f = i / (n - 1)
        out.append((t0 + i / hz, fuente, x0 + (x1 - x0) * f, y, 0.0))
    return out


def corrida(x_ini, x_fin, x_odom_fin=None, quieto=5.0, viaje=40.0,
            con_amcl=True, quieto_final=5.0, parada_en=None):
    """Una pasada completa: quieto, viaje, quieto.

    `x_ini` y `x_fin` son las poses de AMCL, en el marco del mapa.
    `x_odom_fin` es lo que registra la odometria, que arranca siempre en 0.
    `parada_en` mete una parada intermedia a esa x de AMCL.
    """
    if x_odom_fin is None:
        x_odom_fin = abs(x_fin - x_ini)
    filas = []

    piernas = [(x_ini, x_fin)] if parada_en is None else [(x_ini, parada_en),
                                                          (parada_en, x_fin)]
    # La odometria recorre lo mismo, escalada a x_odom_fin.
    total = sum(abs(b - a) for a, b in piernas) or 1.0
    o = 0.0
    t = 0.0

    def añadir(dur, a_amcl, b_amcl, a_odom, b_odom):
        nonlocal t
        filas.extend(tramo(t, dur, a_odom, b_odom, "odom"))
        if con_amcl:
            filas.extend(tramo(t, dur, a_amcl, b_amcl, "amcl"))
        t += dur

    añadir(quieto, x_ini, x_ini, 0.0, 0.0)
    for a, b in piernas:
        d = abs(b - a) / total
        o_sig = o + d * x_odom_fin
        añadir(viaje * d, a, b, o, o_sig)
        o = o_sig
        if parada_en is not None and b == parada_en:
            añadir(quieto, b, b, o, o)
    if quieto_final > 0:
        añadir(quieto_final, x_fin, x_fin, o, o)
    return filas


def csv_de(filas):
    salida = ["t,fuente,x,y,yaw"]
    for t, f, x, y, yaw in sorted(filas, key=lambda r: (r[0], r[1])):
        salida.append(f"{t:.4f},{f},{x:.5f},{y:.5f},{yaw:.5f}")
    return "\n".join(salida) + "\n"


# ------------------------------------------------------------------- pruebas


def prueba_ventanas_quietas():
    """Una pasada con dos paradas de 5 s da exactamente dos ventanas."""
    pista = [(t, x, y) for t, f, x, y, _ in corrida(0.0, 20.0) if f == "odom"]
    v = ventanas_quietas(pista)
    comprobar("ventanas: encuentra dos", len(v) == 2, f"encontro {len(v)}")
    if len(v) == 2:
        comprobar("ventanas: la primera arranca en 0 s", casi(v[0][0], 0.0, 0.1),
                  f"{v[0]}")
        comprobar("ventanas: la ultima acaba al final", casi(v[1][1], 50.0, 0.6),
                  f"{v[1]}")


def prueba_caso_limpio():
    """Odometria perfecta y AMCL perfecto: M1 = 1,000 y M2 = 0,00 m."""
    r = medir(csv_de(corrida(0.0, 20.0)), largo=20.0)
    comprobar("limpio: M1 = 1,000", casi(r["m1"], 1.0), f"m1={r['m1']}")
    comprobar("limpio: M2 = 0,00 m", casi(r["m2"], 0.0), f"m2={r['m2']}")
    comprobar("limpio: sentido ida", r["sentido"] == "ida", r["sentido"])


def prueba_sesgo_medido():
    """El sesgo de +2,9 % del 26-ago: M1 = 1,029 y M2 = 0,58 m sobre 20 m.

    Es el numero que el §4 de S21_preparacion_G2.md predice para el viernes.
    """
    filas = corrida(0.0, 20.58, x_odom_fin=20.58)
    r = medir(csv_de(filas), largo=20.0)
    comprobar("sesgo: M1 = 1,029", casi(r["m1"], 1.029), f"m1={r['m1']}")
    comprobar("sesgo: M2 = 0,58 m", casi(r["m2"], 0.58, 5e-3), f"m2={r['m2']}")
    comprobar("sesgo: el error es longitudinal",
              casi(r["m2_longitudinal"], 0.58, 5e-3) and casi(r["m2_lateral"], 0.0),
              f"long={r['m2_longitudinal']} lat={r['m2_lateral']}")


def prueba_sentido_vuelta():
    """De L a 0: la marca de llegada es el 0 m, no el L."""
    r = medir(csv_de(corrida(20.0, 0.0)), largo=20.0)
    comprobar("vuelta: sentido detectado", r["sentido"] == "vuelta", r["sentido"])
    comprobar("vuelta: M2 = 0,00 m", casi(r["m2"], 0.0), f"m2={r['m2']}")
    comprobar("vuelta: M1 = 1,000", casi(r["m1"], 1.0), f"m1={r['m1']}")


def prueba_sin_ventana_de_llegada():
    """Si no hay parada al final, falla y no devuelve un numero inventado."""
    filas = corrida(0.0, 20.0, quieto_final=0.0)
    try:
        medir(csv_de(filas), largo=20.0)
        comprobar("sin llegada: falla", False, "devolvio un resultado")
    except Fallo as e:
        comprobar("sin llegada: falla", True)
        comprobar("sin llegada: dice por que", "parada" in str(e).lower(), str(e))


def prueba_amcl_vacio():
    """Sin /amcl_pose no hay M2, y eso es un fallo ruidoso."""
    filas = corrida(0.0, 20.0, con_amcl=False)
    try:
        medir(csv_de(filas), largo=20.0)
        comprobar("amcl vacio: falla", False, "devolvio un resultado")
    except Fallo as e:
        comprobar("amcl vacio: falla", True)
        comprobar("amcl vacio: dice por que", "amcl" in str(e).lower(), str(e))


def prueba_estacion_intermedia():
    """Con parada a los 20 m de una recta de 30 m salen las dos evaluaciones."""
    filas = corrida(0.0, 30.0, parada_en=20.0)
    r = medir(csv_de(filas), largo=30.0, estacion=20.0)
    comprobar("estacion: hay resultado a 20 m", r.get("estacion") is not None)
    if r.get("estacion"):
        e = r["estacion"]
        comprobar("estacion: M1 a 20 m = 1,000", casi(e["m1"], 1.0), f"{e['m1']}")
        comprobar("estacion: M2 a 20 m = 0,00 m", casi(e["m2"], 0.0), f"{e['m2']}")
    comprobar("estacion: M1 al final sigue siendo 1,000", casi(r["m1"], 1.0),
              f"{r['m1']}")


def prueba_largo_invalido():
    """Un largo de cero no puede dividir a nadie."""
    try:
        medir(csv_de(corrida(0.0, 20.0)), largo=0.0)
        comprobar("largo cero: falla", False, "devolvio un resultado")
    except Fallo:
        comprobar("largo cero: falla", True)


def main():
    print("Pruebas de medir_g2.py")
    for f in (prueba_ventanas_quietas, prueba_caso_limpio, prueba_sesgo_medido,
              prueba_sentido_vuelta, prueba_sin_ventana_de_llegada,
              prueba_amcl_vacio, prueba_estacion_intermedia,
              prueba_largo_invalido):
        print(f"\n{f.__doc__.splitlines()[0]}")
        f()
    print()
    if FALLOS:
        print(f"FALLAN {len(FALLOS)}: {', '.join(FALLOS)}")
        return 1
    print("Todas pasan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
