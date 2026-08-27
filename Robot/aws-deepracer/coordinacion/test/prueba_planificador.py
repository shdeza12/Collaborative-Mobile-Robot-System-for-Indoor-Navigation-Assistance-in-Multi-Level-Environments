#!/usr/bin/env python3
"""Agota el planificador sobre el catalogo real. Sin ROS y sin simulador.

    python3 src/aws-deepracer/coordinacion/test/prueba_planificador.py

Con 16 puntos hay 16x15 = 240 pares ordenados origen/destino. Se planifican los
240 y se comprueban invariantes sobre TODOS, en vez de mirar tres ejemplos
escogidos a mano. Tarda milisegundos, asi que no hay excusa para no correrlo.

El invariante que de verdad importa es el 5: ningun robot recibe jamas un goal
en un nivel que no es el suyo. Esa es la decision D2 -ningun robot cruza entre
niveles- convertida en algo comprobable. Si alguien 'arregla' el planificador y
rompe D2, esta prueba lo dice; la simulacion no, porque el robot obedeceria el
goal tan campante y se iria contra una pared.
"""

import itertools
import os
import sys

import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))

from coordinacion.planificador import (  # noqa: E402
    ASIGNACION_POR_DEFECTO, ErrorPlanificacion, Tramo, planificar,
    yaw_a_cuaternion, TRAMO_1, TRANSFERENCIA, TRAMO_2,
)

YAML_PUNTOS = os.path.join(
    AQUI, "..", "..", "deepracer_bringup", "config", "puntos_interes.yaml")

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def main():
    with open(YAML_PUNTOS, encoding="utf-8") as f:
        catalogo = yaml.safe_load(f)["puntos"]

    niveles = {}
    for p in catalogo:
        niveles.setdefault(p["nivel"], []).append(p["id"])
    print(f"\nCatalogo real: {len(catalogo)} puntos, "
          + ", ".join(f"nivel {n}: {len(v)}" for n, v in sorted(niveles.items())))

    print("\n1. Las 240 combinaciones se planifican sin excepcion")
    planes = {}
    errores = []
    for o, d in itertools.permutations([p["id"] for p in catalogo], 2):
        try:
            planes[(o, d)] = planificar(catalogo, o, d)
        except ErrorPlanificacion as e:
            errores.append((o, d, str(e)))
    check("ninguna combinacion valida falla",
          not errores, f"{len(planes)} planificadas, {len(errores)} fallan")
    for o, d, e in errores[:3]:
        print(f"        {o} -> {d}: {e}")

    print("\n2. NINGUN plan manda un robot dos veces seguidas al mismo punto")
    # Este invariante falto en la primera version de la prueba, y por eso las 30
    # misiones con relevo pasaron estando mal: se comprobaba la FORMA (4 tramos,
    # 2 robots) y no el SIGNIFICADO. Se vio imprimiendo un plan a mano. Un goal
    # de cero metros no falla en Nav2 -devuelve SUCCEEDED al instante-, asi que
    # la simulacion tampoco lo habria delatado.
    redundantes = []
    for (o, d), (tramos, _) in planes.items():
        for a, b in zip(tramos, tramos[1:]):
            if a.robot == b.robot and a.punto["id"] == b.punto["id"]:
                redundantes.append((o, d, a.punto["id"]))
    check("sin tramos de cero metros", not redundantes,
          f"{len(redundantes)} encontrados")
    for o, d, p in redundantes[:3]:
        print(f"        {o} -> {d}: {p} repetido")

    print("\n3. Mismo nivel: un robot, cero relevos")
    mismos = [(k, v) for k, v in planes.items()
              if _nivel(catalogo, k[0]) == _nivel(catalogo, k[1])]
    ok = all(rel == 0 and len(tr) in (1, 2) and len({t.robot for t in tr}) == 1
             for (_, (tr, rel)) in mismos)
    check("1 o 2 tramos, 1 robot, 0 relevos", ok, f"{len(mismos)} casos")

    print("\n4. Niveles distintos: relevo de dos robots")
    cruces = [(k, v) for k, v in planes.items()
              if _nivel(catalogo, k[0]) != _nivel(catalogo, k[1])]
    ok = all(rel == 1 and len({t.robot for t in tr}) == 2
             for (_, (tr, rel)) in cruces)
    check("2 robots y 1 relevo siempre", ok, f"{len(cruces)} casos")
    ok_etapas = all([t.etapa for t in tr]
                    == sorted([t.etapa for t in tr]) for (_, (tr, _)) in cruces)
    check("las etapas nunca retroceden", ok_etapas)
    # Cuantos conservan los 4 tramos y cuantos se colapsaron. Con el catalogo de
    # hoy se colapsan TODOS, porque el piso 2 solo tiene el punto de escalera.
    completos = sum(1 for (_, (tr, _)) in cruces if len(tr) == 4)
    print(f"        de {len(cruces)} cruces, {completos} tienen los 4 tramos "
          f"y {len(cruces) - completos} se colapsaron")

    print("\n5. D2: ningun robot recibe un goal fuera de su nivel")
    culpables = []
    for (o, d), (tramos, _) in planes.items():
        for t in tramos:
            if ASIGNACION_POR_DEFECTO[t.punto["nivel"]] != t.robot:
                culpables.append((o, d, t))
    check("cada tramo va al robot del nivel de su punto",
          not culpables,
          f"{sum(len(t) for t, _ in planes.values())} tramos revisados")
    for o, d, t in culpables[:3]:
        print(f"        {o} -> {d}: {t.robot} enviado a nivel {t.punto['nivel']}")

    print("\n6. Todo plan empieza en el origen y acaba en el destino")
    mal = [(o, d) for (o, d), (tr, _) in planes.items()
           if tr[0].punto["id"] != o or tr[-1].punto["id"] != d]
    check("primer tramo al origen, ultimo al destino", not mal, str(mal[:3]))
    mal2 = [(o, d) for (o, d), (tr, _) in planes.items() if tr[0].con_usuario]
    check("el primer tramo nunca va con el usuario", not mal2, str(mal2[:3]))

    # El ultimo tramo va CON el usuario, salvo cuando el destino es el punto de
    # transferencia de su nivel: ahi el robot ya esta esperando y es el usuario
    # quien llega hasta el, subiendo por su cuenta. Decir 'siga al robot' a
    # alguien que acaba de llegar donde el robot esta seria falso.
    transf = {p["id"] for p in catalogo if p.get("es_transferencia")}
    mal3 = [(o, d) for (o, d), (tr, _) in planes.items()
            if not tr[-1].con_usuario
            and not (d in transf and _nivel(catalogo, o) != _nivel(catalogo, d))]
    check("el ultimo tramo va con el usuario salvo llegada a transferencia",
          not mal3, str(mal3[:3]))

    print("\n7. Todo tramo lleva un mensaje redactado para el usuario")
    sin_texto = [t for tr, _ in planes.values() for t in tr
                 if not t.mensaje_usuario or len(t.mensaje_usuario) < 10]
    check("ningun mensaje vacio", not sin_texto)
    # El §5 del contrato dice que el texto se redacta en el coordinador y la HRI
    # lo muestra literal. Si aparece un id crudo como 'piso2_escalera' en vez de
    # un nombre, es que se colo el identificador interno a la pantalla.
    con_id = [t.mensaje_usuario for tr, _ in planes.values() for t in tr
              if "piso1_" in t.mensaje_usuario or "piso2_" in t.mensaje_usuario]
    check("no se filtran ids internos al texto del usuario", not con_id,
          str(con_id[:2]))

    print("\n8. Los errores se detectan antes de mover un robot")
    casos = [
        ("origen inexistente", "no_existe", catalogo[0]["id"]),
        ("destino inexistente", catalogo[0]["id"], "no_existe"),
        ("origen igual a destino", catalogo[0]["id"], catalogo[0]["id"]),
    ]
    for nombre, o, d in casos:
        try:
            planificar(catalogo, o, d)
            check(nombre, False, "no lanzo excepcion")
        except ErrorPlanificacion as e:
            check(nombre, len(str(e)) > 20, f"-> {str(e)[:60]}...")

    try:
        planificar([], "a", "b")
        check("catalogo vacio", False, "no lanzo excepcion")
    except ErrorPlanificacion:
        check("catalogo vacio", True)

    # Un nivel sin punto de transferencia deja el edificio incomunicado.
    sin_transf = [dict(p) for p in catalogo]
    for p in sin_transf:
        if p["nivel"] == 2:
            p["es_transferencia"] = False
    o = next(p["id"] for p in catalogo if p["nivel"] == 1)
    d = next(p["id"] for p in catalogo if p["nivel"] == 2)
    try:
        planificar(sin_transf, o, d)
        check("nivel sin transferencia", False, "no lanzo excepcion")
    except ErrorPlanificacion as e:
        check("nivel sin transferencia", "transferencia" in str(e),
              f"-> {str(e)[:60]}...")

    # Asignar los dos niveles al mismo robot viola D2.
    try:
        planificar(catalogo, o, d, asignacion={1: "robot1", 2: "robot1"})
        check("un solo robot para dos niveles", False, "no lanzo excepcion")
    except ErrorPlanificacion as e:
        check("un solo robot para dos niveles", "D2" in str(e),
              f"-> {str(e)[:60]}...")

    print("\n9. Las etapas no se han desincronizado de EstadoMision.msg")
    ruta_msg = os.path.join(AQUI, "..", "..", "coordinacion_msgs", "msg",
                            "EstadoMision.msg")
    del_msg = {}
    with open(ruta_msg, encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("uint8 ") and "=" in linea:
                nombre, valor = linea.split()[1].split("=")
                del_msg[nombre] = int(valor)
    import coordinacion.planificador as pl
    del_py = {n: getattr(pl, n) for n in del_msg}
    check("los numeros del .msg y del .py coinciden", del_msg == del_py,
          f"{del_msg} vs {del_py}")

    print("\n10. yaw -> cuaternion")
    import math
    z, w = yaw_a_cuaternion(0.0)[2:]
    check("yaw 0 da (z=0, w=1)", abs(z) < 1e-12 and abs(w - 1.0) < 1e-12)
    z, w = yaw_a_cuaternion(math.pi)[2:]
    check("yaw pi da (z=1, w=0)", abs(z - 1.0) < 1e-12 and abs(w) < 1e-12,
          f"z={z:.6f} w={w:.6f}")

    print("\n11. identificador de mision y condicion experimental")
    # Ver Documentos/ESQUEMA_REGISTRO_MISION.md §2.1 y §3.2.
    from coordinacion.planificador import condicion_de, generar_mision_id
    import datetime

    check("condicion_de: intra-nivel es A",
          condicion_de(catalogo, "piso1_escalera", "piso1_representacion") == "A")
    check("condicion_de: inter-nivel es B",
          condicion_de(catalogo, "piso1_escalera", "piso2_escalera") == "B")
    check("condicion_de: id desconocido no revienta, devuelve X",
          condicion_de(catalogo, "no_existe", "piso1_representacion") == "X")

    t = datetime.datetime(2026, 8, 27, 14, 30, 52)
    check("mision_id con prefijo lleva campana, condicion y sello",
          generar_mision_id("S24", "B", t) == "S24_B_20260827_143052",
          f"-> {generar_mision_id('S24', 'B', t)}")
    check("mision_id sin prefijo es una corrida suelta",
          generar_mision_id("", "A", t) == "manual_20260827_143052")

    # El invariante que de verdad importa: dos misiones del mismo par origen /
    # destino en corridas distintas NO comparten identificador. Es justo lo que
    # fallaba al publicar pet.origen_id.
    t2 = datetime.datetime(2026, 8, 27, 14, 30, 53)
    check("dos misiones del mismo par no comparten id",
          generar_mision_id("S24", "B", t) != generar_mision_id("S24", "B", t2))

    print("\n" + "=" * 62)
    if fallos:
        print(f"FALLAN {len(fallos)}: {fallos}")
    else:
        print(f"Todas las comprobaciones pasan ({len(planes)} planes verificados).")
    print("=" * 62)
    return 1 if fallos else 0


def _nivel(catalogo, id_punto):
    return next(p["nivel"] for p in catalogo if p["id"] == id_punto)


if __name__ == "__main__":
    sys.exit(main())
