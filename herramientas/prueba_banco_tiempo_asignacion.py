#!/usr/bin/env python3
"""Prueba de la parte pura del banco del tiempo de asignacion.

    python3 herramientas/prueba_banco_tiempo_asignacion.py

NO necesita ROS, ni el workspace sourceado, ni Gazebo. Eso es a proposito: lo
que se comprueba aqui -el sorteo de pares y la estadistica- es justo lo que no
depende de que haya un robot, y por tanto lo unico que se puede equivocar en
silencio. El cableado con rclpy se valida ejecutando el banco de verdad.

Lo que NO se prueba aqui, y conviene saberlo: que el instante que mide el banco
sea el correcto. Eso depende del monkey-patch sobre '_publicar_estado' del
coordinador y solo se puede comprobar corriendo el banco contra el nodo real.
"""

import os
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from banco_tiempo_asignacion import (  # noqa: E402
    pares_alternados, resumen, sha256_de, MINIMO_REPETICIONES)

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def catalogo_falso():
    """Dos niveles con puntos de sobra y su punto de transferencia."""
    p = []
    for i in range(4):
        p.append({"id": f"n1_{i}", "nombre": f"N1 {i}", "nivel": 1,
                  "es_transferencia": False, "pose": {"x": float(i), "y": 0.0}})
        p.append({"id": f"n2_{i}", "nombre": f"N2 {i}", "nivel": 2,
                  "es_transferencia": False, "pose": {"x": float(i), "y": 9.0}})
    p.append({"id": "n1_esc", "nombre": "Esc 1", "nivel": 1,
              "es_transferencia": True, "pose": {"x": 0.0, "y": 5.0}})
    p.append({"id": "n2_esc", "nombre": "Esc 2", "nivel": 2,
              "es_transferencia": True, "pose": {"x": 0.0, "y": 6.0}})
    return p


def pruebas_de_sorteo():
    cat = catalogo_falso()
    nivel = {q["id"]: q["nivel"] for q in cat}

    pares = pares_alternados(cat, 30, semilla=7)
    check("devuelve exactamente las repeticiones pedidas", len(pares) == 30,
          f"-> {len(pares)}")
    check("ningun par tiene origen igual a destino",
          all(o != d for o, d in pares))
    check("todos los ids salen del catalogo",
          all(o in nivel and d in nivel for o, d in pares))

    # La §3.2.2 pide "alternando pares intra-nivel e inter-nivel". Alternar de
    # verdad importa: planificar() recorre dos ramas distintas -la intra-nivel
    # devuelve 2 tramos y la inter-nivel 4, y ademas busca los puntos de
    # transferencia-, asi que medir solo una rama caracterizaria media funcion.
    tipos = ["intra" if nivel[o] == nivel[d] else "inter" for o, d in pares]
    check("alterna intra e inter en posiciones consecutivas",
          all(a != b for a, b in zip(tipos, tipos[1:])),
          f"-> {''.join(t[0] for t in tipos[:8])}...")
    check("hay pares de los dos tipos",
          tipos.count("intra") > 0 and tipos.count("inter") > 0,
          f"-> {tipos.count('intra')} intra / {tipos.count('inter')} inter")

    check("la misma semilla da el mismo sorteo",
          pares_alternados(cat, 30, semilla=7) == pares)
    check("semillas distintas dan sorteos distintos",
          pares_alternados(cat, 30, semilla=8) != pares)

    # Un catalogo de un solo nivel no puede dar pares inter-nivel. Que devuelva
    # una lista a medias sin avisar seria el fallo silencioso de siempre.
    solo1 = [q for q in cat if q["nivel"] == 1]
    try:
        pares_alternados(solo1, 30, semilla=7)
        check("con un solo nivel falla ruidosamente", False, "-> no lanzo")
    except ValueError as e:
        check("con un solo nivel falla ruidosamente", True, f"-> {e}")


def pruebas_de_estadistica():
    # La §3.2.2 dice "mediana y maximo, no la media: la distribucion tiene cola
    # por el planificador de Python". La cola de este caso es deliberada.
    muestras = [10.0] * 29 + [900.0]
    r = resumen(muestras)
    check("reporta la mediana, no la media",
          r["mediana_us"] == 10.0 and abs(statistics.mean(muestras) - 10.0) > 1,
          f"-> mediana {r['mediana_us']}, media {statistics.mean(muestras):.1f}")
    check("reporta el maximo", r["maximo_us"] == 900.0)
    check("reporta el minimo", r["minimo_us"] == 10.0)
    check("reporta cuantas muestras hay", r["n"] == 30)

    # El protocolo exige >= 30 repeticiones. Resumir 29 y publicarlo como si
    # cumpliera es exactamente el numero que no vale.
    try:
        resumen([1.0] * (MINIMO_REPETICIONES - 1))
        check("menos de 30 muestras falla ruidosamente", False, "-> no lanzo")
    except ValueError as e:
        check("menos de 30 muestras falla ruidosamente", True, f"-> {e}")

    # Un cero significa que el banco esta midiendo con el reloj equivocado: es
    # el sintoma exacto que el banco existe para no repetir.
    try:
        resumen([0.0] * 30)
        check("una muestra en cero falla ruidosamente", False, "-> no lanzo")
    except ValueError as e:
        check("una muestra en cero falla ruidosamente", True, f"-> {e}")


def pruebas_de_huella():
    # El SHA-256 del catalogo va en el informe: la cifra solo vale para el
    # catalogo con el que se midio, y sin huella nadie puede comprobarlo.
    ruta = os.path.join(AQUI, "prueba_banco_tiempo_asignacion.py")
    h = sha256_de(ruta)
    check("el sha256 tiene 64 hex", len(h) == 64 and all(
        c in "0123456789abcdef" for c in h), f"-> {h[:16]}...")
    check("el sha256 es estable", sha256_de(ruta) == h)


def main():
    print("Sorteo de pares")
    pruebas_de_sorteo()
    print("Estadistica")
    pruebas_de_estadistica()
    print("Huella del catalogo")
    pruebas_de_huella()
    print(f"\n{len(fallos)} fallo(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
