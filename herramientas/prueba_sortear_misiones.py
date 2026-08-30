#!/usr/bin/env python3
"""Prueba de sortear_misiones.py.

    python3 herramientas/prueba_sortear_misiones.py

NO necesita ROS, ni el workspace sourceado, ni Gazebo, y no es una casualidad:
el sorteo entero es una funcion pura, asi que TODO lo que puede salir mal aqui
se puede comprobar sin encender nada. Lo unico que queda fuera es que el CSV se
escriba donde se dijo, que se ve mirando el archivo.

La ultima seccion es la que mas vale y la que menos parece una prueba: coge el
catalogo DE VERDAD, sortea las 30 misiones de la campana y comprueba que las
treinta se pueden planificar. Un listado con una mision impianificable no daria
ningun error hasta el dia de la campana, y para entonces habria quemado una
corrida de las 30.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(
    REPO, "Robot", "aws-deepracer", "coordinacion"))

from sortear_misiones import (  # noqa: E402
    CATALOGO_POR_DEFECTO, cargar_catalogo, elegibles, sortear)

# planificador.py no importa rclpy -solo math-, asi que se puede cargar aqui sin
# tener el workspace compilado. Si algun dia importa ROS, esta prueba deja de
# correr en seco y hay que enterarse: por eso el import va arriba y sin try.
from coordinacion.planificador import (  # noqa: E402
    ErrorPlanificacion, condicion_de, planificar)

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def catalogo_falso():
    """Cinco destinos por nivel y una escalera en cada uno.

    Cinco y no dos: con dos, 'todos los pares posibles' son tan pocos que una
    prueba de no-repeticion pasaria por falta de alternativas y no por que el
    sorteo funcione.
    """
    p = []
    for i in range(5):
        p.append({"id": f"p1_{i}", "nombre": f"Uno {i}", "nivel": 1,
                  "es_transferencia": False})
        p.append({"id": f"p2_{i}", "nombre": f"Dos {i}", "nivel": 2,
                  "es_transferencia": False})
    p.append({"id": "p1_esc", "nombre": "Escalera 1", "nivel": 1,
              "es_transferencia": True})
    p.append({"id": "p2_esc", "nombre": "Escalera 2", "nivel": 2,
              "es_transferencia": True})
    return p


def pruebas_de_elegibles():
    cat = catalogo_falso()
    e1 = elegibles(cat, 1)
    check("deja fuera el punto de transferencia del nivel",
          "p1_esc" not in e1, f"-> {e1}")
    check("devuelve los cinco destinos del nivel 1", len(e1) == 5)
    check("no mezcla niveles", all(i.startswith("p1_") for i in e1))

    # El orden del YAML no puede cambiar el sorteo: si 'elegibles' devolviera la
    # lista en el orden del archivo, reordenar puntos_interes.yaml sin tocar un
    # solo punto daria misiones distintas con la misma semilla.
    check("es independiente del orden del catalogo",
          elegibles(list(reversed(cat)), 1) == e1)


def pruebas_de_reparto():
    cat = catalogo_falso()
    m = sortear(cat, 30, semilla=20260822)
    nivel = {p["id"]: p["nivel"] for p in cat}

    check("devuelve exactamente las N pedidas", len(m) == 30, f"-> {len(m)}")
    a = [x for x in m if x["condicion"] == "A"]
    b = [x for x in m if x["condicion"] == "B"]
    check("mitad y mitad entre las dos condiciones (§6.2)",
          len(a) == 15 and len(b) == 15, f"-> A={len(a)} B={len(b)}")
    check("la condicion A no sale del piso 1",
          all(nivel[x["origen_id"]] == 1 and nivel[x["destino_id"]] == 1
              for x in a))
    check("la condicion B va del piso 1 al piso 2",
          all(nivel[x["origen_id"]] == 1 and nivel[x["destino_id"]] == 2
              for x in b))
    check("ninguna mision empieza donde termina",
          all(x["origen_id"] != x["destino_id"] for x in m))
    check("ningun punto de transferencia se sortea",
          all("esc" not in x["origen_id"] and "esc" not in x["destino_id"]
              for x in m))
    check("las 30 son pares distintos (decision 2)",
          len({(x["origen_id"], x["destino_id"]) for x in m}) == 30)
    check("la numeracion va de 1 a N sin huecos",
          [x["n"] for x in m] == list(range(1, 31)))


def pruebas_de_orden():
    """Decision 3: el orden del archivo es el orden temporal de la campana."""
    m = sortear(catalogo_falso(), 30, semilla=20260822)
    condiciones = [x["condicion"] for x in m]
    bloques = ["A"] * 15 + ["B"] * 15
    check("las dos condiciones van mezcladas, no en dos bloques",
          condiciones != bloques and condiciones != list(reversed(bloques)))
    # Un bloque de 15 seguidas seria el caso degenerado que el barajado evita.
    seguidas = maximo_seguidas(condiciones)
    check("ninguna condicion aparece 15 veces seguidas", seguidas < 15,
          f"-> racha maxima {seguidas}")


def maximo_seguidas(seq):
    mejor = actual = 1
    for i in range(1, len(seq)):
        actual = actual + 1 if seq[i] == seq[i - 1] else 1
        mejor = max(mejor, actual)
    return mejor


def pruebas_de_reproducibilidad():
    cat = catalogo_falso()
    uno = sortear(cat, 30, semilla=20260822)
    otro = sortear(cat, 30, semilla=20260822)
    check("la misma semilla da exactamente las mismas misiones", uno == otro)
    distinta = sortear(cat, 30, semilla=7)
    check("una semilla distinta da un sorteo distinto", uno != distinta)


def pruebas_de_negativas():
    cat = catalogo_falso()
    try:
        sortear(cat, 31, semilla=1)
        check("un N impar se rechaza", False, "-> no lanzo nada")
    except ValueError as e:
        check("un N impar se rechaza", "par" in str(e))

    # Cinco destinos por nivel dan 20 pares A y 25 B: pedir 60 (30 por
    # condicion) no cabe en A. Tiene que fallar diciendolo, no completar
    # repitiendo en silencio.
    try:
        sortear(cat, 60, semilla=1)
        check("un N que no cabe en el catalogo se rechaza", False,
              "-> no lanzo nada")
    except ValueError as e:
        check("un N que no cabe en el catalogo se rechaza",
              "catalogo" in str(e) and "20" in str(e))


def pruebas_sobre_el_catalogo_real():
    """Lo caro de descubrir tarde: que una mision sorteada no se pueda planificar."""
    ruta = os.path.join(REPO, CATALOGO_POR_DEFECTO)
    cat = cargar_catalogo(ruta)
    check("el catalogo del repositorio se lee", len(cat) > 0, f"-> {len(cat)} puntos")

    m = sortear(cat, 30, semilla=20260822)

    impianificables = []
    for x in m:
        try:
            planificar(cat, x["origen_id"], x["destino_id"])
        except ErrorPlanificacion as e:
            impianificables.append(f"{x['origen_id']}->{x['destino_id']}: {e}")
    check("las 30 misiones sorteadas se pueden planificar",
          not impianificables, f"-> {impianificables[:2]}")

    # El sorteo etiqueta la condicion por su cuenta; el coordinador la vuelve a
    # calcular con condicion_de al aceptar el goal. Si las dos se desincronizan,
    # el CSV diria una cosa y los registros de la campana otra.
    discrepan = [x for x in m
                 if condicion_de(cat, x["origen_id"], x["destino_id"])
                 != x["condicion"]]
    check("la condicion del CSV coincide con la que calculara el coordinador",
          not discrepan, f"-> {len(discrepan)} discrepancias")

    relevos = {x["condicion"]: planificar(
        cat, x["origen_id"], x["destino_id"])[1] for x in m}
    check("las de condicion A no llevan relevo", relevos.get("A") == 0,
          f"-> {relevos.get('A')}")
    check("las de condicion B llevan exactamente uno", relevos.get("B") == 1,
          f"-> {relevos.get('B')}")


print("Elegibles")
pruebas_de_elegibles()
print("Reparto entre condiciones")
pruebas_de_reparto()
print("Orden de ejecucion")
pruebas_de_orden()
print("Reproducibilidad")
pruebas_de_reproducibilidad()
print("Lo que tiene que rechazar")
pruebas_de_negativas()
print("Sobre el catalogo real del repositorio")
pruebas_sobre_el_catalogo_real()

print()
if fallos:
    print(f"{len(fallos)} FALLAN: {', '.join(fallos)}")
    sys.exit(1)
print("Todo pasa.")
