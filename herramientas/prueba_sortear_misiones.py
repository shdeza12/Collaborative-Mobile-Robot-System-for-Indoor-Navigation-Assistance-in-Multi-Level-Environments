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
    CATALOGO_POR_DEFECTO, ESTRATOS, RACHA_MAXIMA, cargar_catalogo, elegibles,
    estrato_de, leer_csv, maxima_racha, sortear, sortear_estratificado)

# planificador.py no importa rclpy -solo math-, asi que se puede cargar aqui sin
# tener el workspace compilado. Si algun dia importa ROS, esta prueba deja de
# correr en seco y hay que enterarse: por eso el import va arriba y sin try.
from coordinacion.planificador import (  # noqa: E402
    ErrorPlanificacion, condicion_de, planificar)

fallos = []

# Las 10 misiones ya corridas el 2026-09-04, copiadas de
# Documentos/Evidencia/campana_oe4_misiones.csv. Sus pares estan gastados: el
# resorteo de las 20 que faltan no puede volver a sacar ninguno.
YA_CORRIDAS = [
    ("piso1_etm2", "piso1_etm11"), ("piso1_etm7", "piso2_aula_306"),
    ("piso1_etm9", "piso1_etm6"), ("piso1_etm6", "piso2_ieee"),
    ("piso1_etm6", "piso1_representacion"),
    ("piso1_etm10", "piso2_aula_303"), ("piso1_etm8", "piso2_aula_309"),
    ("piso1_etm2", "piso2_lab_312"), ("piso1_etm3", "piso2_aula_302"),
    ("piso1_etm8", "piso1_etm11")]


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


def pruebas_de_estratos():
    """El sorteo estratificado que enmienda el §6.2 el 2026-09-04.

    El sorteo original solo generaba A dentro del piso 1 y B de 1 a 2, asi que
    la condicion B se diferenciaba de la A en DOS cosas a la vez -llevar relevo
    y pisar el piso 2- y ninguna medida podia separarlas. Los cuatro estratos
    cruzan condicion con piso: A1, A2, B12 y B21.
    """
    cat = catalogo_falso()
    nivel = {p["id"]: p["nivel"] for p in cat}

    cupos = {"A1": 4, "A2": 3, "B12": 4, "B21": 3}
    m = sortear_estratificado(cat, cupos, semilla=20260904)

    check("devuelve la suma de los cupos", len(m) == 14, f"-> {len(m)}")
    for nombre, cupo in cupos.items():
        hay = [x for x in m if x["estrato"] == nombre]
        check(f"el estrato {nombre} aporta exactamente {cupo}",
              len(hay) == cupo, f"-> {len(hay)}")

    for nombre, (n_origen, n_destino, condicion) in ESTRATOS.items():
        hay = [x for x in m if x["estrato"] == nombre]
        check(f"{nombre} va del piso {n_origen} al {n_destino}",
              all(nivel[x["origen_id"]] == n_origen
                  and nivel[x["destino_id"]] == n_destino for x in hay))
        check(f"{nombre} lleva condicion {condicion}",
              all(x["condicion"] == condicion for x in hay))

    check("ninguna mision empieza donde termina",
          all(x["origen_id"] != x["destino_id"] for x in m))
    check("ningun punto de transferencia se sortea",
          all("esc" not in x["origen_id"] and "esc" not in x["destino_id"]
              for x in m))
    check("todos los pares son distintos entre si",
          len({(x["origen_id"], x["destino_id"]) for x in m}) == len(m))


def pruebas_de_exclusion():
    """Las 10 misiones ya corridas no se pueden repetir en el resorteo.

    Es el motivo de que esta funcion exista y no baste con volver a llamar a
    sortear(): las 10 primeras de la campana ya estan grabadas y su par queda
    gastado. Repetir uno gastaria una corrida sin cubrir un destino nuevo.
    """
    cat = catalogo_falso()

    # Se gastan TODOS los pares A1 que salen de p1_0: si la exclusion no se
    # respetara, con cupo 4 sobre 20 pares la coincidencia seria probable pero
    # no segura, y la prueba pasaria a veces.
    # Un solo estrato: aqui se mira la exclusion y nada mas, asi que la regla
    # de la racha se apaga. Ocho A1 seguidas la incumplen por construccion y
    # ese caso tiene su propia prueba mas abajo.
    gastados = [("p1_0", f"p1_{i}") for i in range(1, 5)]
    m = sortear_estratificado(cat, {"A1": 8}, semilla=1, excluidos=gastados,
                              racha_maxima=None)
    check("ninguno de los pares excluidos vuelve a salir",
          not [x for x in m
               if (x["origen_id"], x["destino_id"]) in set(gastados)])
    check("el cupo se completa igual pese a la exclusion", len(m) == 8,
          f"-> {len(m)}")

    # 20 pares A1 en el catalogo falso; excluidos 4, quedan 16.
    try:
        sortear_estratificado(cat, {"A1": 17}, semilla=1, excluidos=gastados)
        check("un cupo que no cabe tras excluir se rechaza", False,
              "-> no lanzo nada")
    except ValueError as e:
        check("un cupo que no cabe tras excluir se rechaza",
              "16" in str(e) and "A1" in str(e), f"-> {e}")


def pruebas_de_numeracion():
    """La numeracion continua donde acabo la parte ya corrida de la campana.

    Las 10 primeras son la 1 a la 10 y siguen valiendo; el resorteo tiene que
    entregar la 11 a la 30 o el CSV tendria dos misiones con el mismo numero.
    """
    cat = catalogo_falso()
    m = sortear_estratificado(cat, {"A1": 4, "A2": 3, "B12": 4, "B21": 3},
                              semilla=20260904, desde=11)
    check("la numeracion arranca en el 'desde' pedido",
          [x["n"] for x in m] == list(range(11, 25)),
          f"-> {m[0]['n']}..{m[-1]['n']}")

    check("por defecto arranca en 1",
          sortear_estratificado(cat, {"A1": 2}, semilla=1)[0]["n"] == 1)


def pruebas_de_mezcla_y_reproducibilidad():
    cat = catalogo_falso()
    cupos = {"A1": 4, "A2": 3, "B12": 4, "B21": 3}

    uno = sortear_estratificado(cat, cupos, semilla=20260904)
    otro = sortear_estratificado(cat, cupos, semilla=20260904)
    check("la misma semilla da exactamente las mismas misiones", uno == otro)
    check("una semilla distinta da un sorteo distinto",
          uno != sortear_estratificado(cat, cupos, semilla=7))

    # Decision 3 de la cabecera, ahora con cuatro estratos en vez de dos: si el
    # archivo saliera ordenado por estrato, la deriva de la sesion quedaria
    # confundida con el estrato igual que antes lo estaba con la condicion.
    estratos = [x["estrato"] for x in uno]
    por_bloques = ["A1"] * 4 + ["A2"] * 3 + ["B12"] * 4 + ["B21"] * 3
    check("los cuatro estratos van mezclados, no en bloques",
          estratos != por_bloques)
    check("ningun estrato aparece entero seguido",
          maximo_seguidas(estratos) < 3, f"-> racha maxima "
          f"{maximo_seguidas(estratos)}")


def pruebas_de_negativas_estratificadas():
    cat = catalogo_falso()
    try:
        sortear_estratificado(cat, {"A3": 2}, semilla=1)
        check("un estrato que no existe se rechaza", False, "-> no lanzo nada")
    except ValueError as e:
        check("un estrato que no existe se rechaza",
              "A3" in str(e) and "A1" in str(e), f"-> {e}")

    try:
        sortear_estratificado(cat, {}, semilla=1)
        check("unos cupos vacios se rechazan", False, "-> no lanzo nada")
    except ValueError as e:
        check("unos cupos vacios se rechazan", "cupo" in str(e).lower())


def pruebas_estratificadas_sobre_el_catalogo_real():
    """Las 20 que faltan, sobre el catalogo de verdad y con la reparticion real.

    Es la unica prueba que ejercita el sorteo que se va a usar. Las 10 ya
    corridas fueron 4 de A1 y 6 de B12, asi que faltan 4 de A1, 7 de A2, 2 de
    B12 y 7 de B21 para llegar a 8/7/8/7.
    """
    cat = cargar_catalogo(os.path.join(REPO, CATALOGO_POR_DEFECTO))
    cupos = {"A1": 4, "A2": 7, "B12": 2, "B21": 7}
    m = sortear_estratificado(cat, cupos, semilla=20260904, desde=11,
                              excluidos=YA_CORRIDAS)

    check("salen las 20 que faltan para las 30", len(m) == 20, f"-> {len(m)}")
    check("numeradas de la 11 a la 30",
          [x["n"] for x in m] == list(range(11, 31)))

    a = [x for x in m if x["condicion"] == "A"]
    b = [x for x in m if x["condicion"] == "B"]
    check("11 de A y 9 de B, que con las 10 hechas dan 15 y 15 (§6.2)",
          len(a) == 11 and len(b) == 9, f"-> A={len(a)} B={len(b)}")

    impianificables = []
    for x in m:
        try:
            planificar(cat, x["origen_id"], x["destino_id"])
        except ErrorPlanificacion as e:
            impianificables.append(f"{x['origen_id']}->{x['destino_id']}: {e}")
    check("las 20 se pueden planificar", not impianificables,
          f"-> {impianificables[:2]}")

    discrepan = [x for x in m
                 if condicion_de(cat, x["origen_id"], x["destino_id"])
                 != x["condicion"]]
    check("la condicion del CSV coincide con la del coordinador",
          not discrepan, f"-> {len(discrepan)} discrepancias")

    # La bajada es la novedad del diseno: el coordinador nunca la ejecuto en la
    # campana. Que planifique con UN relevo, igual que la subida, es lo que
    # permite comparar B12 con B21 sin cambiar de instrumento.
    relevos = {x["estrato"]: planificar(
        cat, x["origen_id"], x["destino_id"])[1] for x in m}
    check("A1 y A2 no llevan relevo",
          relevos.get("A1") == 0 and relevos.get("A2") == 0,
          f"-> A1={relevos.get('A1')} A2={relevos.get('A2')}")
    check("B12 y B21 llevan exactamente uno",
          relevos.get("B12") == 1 and relevos.get("B21") == 1,
          f"-> B12={relevos.get('B12')} B21={relevos.get('B21')}")

    repetidos = [x for x in m
                 if (x["origen_id"], x["destino_id"]) in set(YA_CORRIDAS)]
    check("no repite ninguno de los 10 pares ya corridos", not repetidos,
          f"-> {[(x['origen_id'], x['destino_id']) for x in repetidos]}")


def pruebas_de_estrato_de():
    """El estrato de una mision se deduce de los niveles, no se anota a mano.

    Hace falta para las 10 ya corridas: se sortearon antes de que existieran
    los estratos y su CSV no lleva la columna, asi que hay que reconstruirla.
    """
    cat = catalogo_falso()
    check("mismo piso 1 -> A1", estrato_de(cat, "p1_0", "p1_1") == "A1")
    check("mismo piso 2 -> A2", estrato_de(cat, "p2_0", "p2_1") == "A2")
    check("subida -> B12", estrato_de(cat, "p1_0", "p2_1") == "B12")
    check("bajada -> B21", estrato_de(cat, "p2_0", "p1_1") == "B21")

    # Las 10 ya corridas tienen que caer en A1 y B12 y en ningun otro sitio:
    # si alguna cayera en A2 o B21 el reparto de cupos estaria mal calculado.
    real = cargar_catalogo(os.path.join(REPO, CATALOGO_POR_DEFECTO))
    hechas = [estrato_de(real, o, d) for o, d in YA_CORRIDAS]
    check("las 10 ya corridas son 4 de A1 y 6 de B12",
          hechas.count("A1") == 4 and hechas.count("B12") == 6
          and len(set(hechas)) == 2, f"-> {sorted(set(hechas))}")

    try:
        estrato_de(cat, "p1_0", "no_existe")
        check("un punto que no esta en el catalogo se rechaza", False,
              "-> no lanzo nada")
    except ValueError as e:
        check("un punto que no esta en el catalogo se rechaza",
              "no_existe" in str(e), f"-> {e}")


def pruebas_de_leer_csv():
    """Releer el listado ya versionado, que es de donde salen los pares gastados.

    Se lee el archivo DE VERDAD y no uno de mentira: el formato de ese archivo
    es lo que hay que respetar, y una prueba contra un CSV inventado pasaria
    aunque el real tuviera otra forma.
    """
    meta, filas = leer_csv(os.path.join(
        REPO, "Documentos", "Evidencia", "campana_oe4_misiones.csv"))
    check("recupera las 30 filas", len(filas) == 30, f"-> {len(filas)}")
    check("recupera la semilla de la cabecera", meta.get("semilla") == "20260822",
          f"-> {meta.get('semilla')}")
    check("recupera la huella del catalogo",
          len(meta.get("catalogo_sha256", "")) == 64)
    check("la primera fila es la mision 1", filas[0]["n"] == 1)
    check("las filas llegan numeradas y en orden",
          [f["n"] for f in filas] == list(range(1, 31)))
    check("las 10 primeras son las que se corrieron",
          [(f["origen_id"], f["destino_id"]) for f in filas[:10]]
          == YA_CORRIDAS)


def pruebas_de_racha():
    """La aleatorizacion restringida del 2026-09-04.

    El motivo de barajar (decision 3) es que la deriva de la sesion no se
    confunda con el estrato: el equipo lleva horas encendido, el RTF baja y el
    operador se cansa. Si un estrato cae entero en el mismo tramo de la noche,
    ese desgaste le toca solo a el y no hay forma de separar 'sale peor porque
    es una bajada' de 'sale peor porque se corrio a las dos de la manana'.

    Barajar sin mas no lo garantiza: el sorteo del 2026-09-04 saco CINCO B21
    seguidas de las siete que hay. Medido sobre la composicion real, una racha
    de 5 o mas sale el 3,7 % de las veces; es rara, pero salio.

    La regla se declara ANTES de sortear y vale para cualquier semilla. Eso es
    lo que la separa de repetir semillas hasta que el resultado guste, que
    seria elegir el orden a mano y es justo lo que el §6.3 prohibe.
    """
    check("el limite declarado son 3 seguidas", RACHA_MAXIMA == 3,
          f"-> {RACHA_MAXIMA}")

    check("una secuencia sin repeticiones tiene racha 1",
          maxima_racha(["A1", "B12", "A2"]) == 1)
    check("cuenta la racha mas larga, no la ultima",
          maxima_racha(["A1", "A1", "A1", "B12", "A2", "A2"]) == 3)
    check("una secuencia vacia tiene racha 0", maxima_racha([]) == 0)

    cat = cargar_catalogo(os.path.join(REPO, CATALOGO_POR_DEFECTO))
    cupos = {"A1": 4, "A2": 7, "B12": 2, "B21": 7}

    # La misma semilla y los mismos cupos que dieron la racha de cinco.
    m = sortear_estratificado(cat, cupos, semilla=20260904, desde=11,
                              excluidos=YA_CORRIDAS)
    racha = maxima_racha([x["estrato"] for x in m])
    check("por defecto ningun estrato sale mas de 3 veces seguidas",
          racha <= RACHA_MAXIMA, f"-> racha maxima {racha}")

    # Sin la regla, ESTA semilla daba cinco B21 seguidas. Que el resultado
    # cambie es la prueba de que la regla hace algo y no es decorativa.
    sin_regla = sortear_estratificado(cat, cupos, semilla=20260904, desde=11,
                                      excluidos=YA_CORRIDAS,
                                      racha_maxima=None)
    check("sin la regla, esta semilla sacaba una racha mayor",
          maxima_racha([x["estrato"] for x in sin_regla]) == 5,
          f"-> {maxima_racha([x['estrato'] for x in sin_regla])}")

    # Lo que la regla NO puede cambiar: sigue siendo el mismo sorteo.
    check("la regla no altera los cupos",
          sorted(x["estrato"] for x in m)
          == sorted(x["estrato"] for x in sin_regla))
    check("la regla no reintroduce pares ya corridos",
          not [x for x in m
               if (x["origen_id"], x["destino_id"]) in set(YA_CORRIDAS)])
    check("con la regla puesta sigue siendo reproducible",
          m == sortear_estratificado(cat, cupos, semilla=20260904, desde=11,
                                     excluidos=YA_CORRIDAS))


def pruebas_de_racha_en_la_frontera():
    """La racha se cuenta CONTRA lo ya corrido, no empezando de cero en la 11.

    La campana se corre del 1 al 30 seguido, asi que si las misiones 8, 9 y 10
    fueran del mismo estrato y la 11 tambien, serian cuatro seguidas de verdad
    aunque el sorteo nuevo solo viera una.
    """
    cat = catalogo_falso()
    m = sortear_estratificado(cat, {"A1": 5, "A2": 5}, semilla=3,
                              estratos_previos=["A2", "A1", "A1", "A1"])
    check("la primera sorteada no continua una racha ya cerrada",
          m[0]["estrato"] != "A1", f"-> {m[0]['estrato']}")

    # Con dos previas la racha admite una mas y no obliga a cambiar.
    seq = ["B12", "A1", "A1"]
    m2 = sortear_estratificado(cat, {"A1": 5, "A2": 5}, semilla=3,
                               estratos_previos=seq)
    check("la racha total, previas incluidas, respeta el limite",
          maxima_racha(seq + [x["estrato"] for x in m2]) <= RACHA_MAXIMA,
          f"-> {maxima_racha(seq + [x['estrato'] for x in m2])}")

    # El prefijo ya corrido puede violar la regla -las misiones 6 a 9 de la
    # campana son cuatro B12 seguidas- y eso NO se puede arreglar: ya se
    # corrieron. Lo unico exigible es que el sorteo nuevo no lo alargue.
    m3 = sortear_estratificado(cat, {"A1": 5, "A2": 5}, semilla=3,
                               estratos_previos=["A1"] * 9)
    check("un prefijo que ya incumple no bloquea el sorteo",
          m3[0]["estrato"] != "A1", f"-> {m3[0]['estrato']}")


def pruebas_de_racha_imposible():
    """Un cupo que no puede cumplir la regla tiene que decirlo, no colgarse."""
    cat = catalogo_falso()
    try:
        sortear_estratificado(cat, {"A1": 10}, semilla=1)
        check("un cupo de un solo estrato se rechaza", False,
              "-> no lanzo nada")
    except ValueError as e:
        check("un cupo de un solo estrato se rechaza",
              "racha" in str(e).lower() and "3" in str(e), f"-> {e}")


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
print("Estrato de una mision")
pruebas_de_estrato_de()
print("Relectura del listado ya versionado")
pruebas_de_leer_csv()
print("Sorteo estratificado: los cuatro estratos")
pruebas_de_estratos()
print("Sorteo estratificado: exclusion de lo ya corrido")
pruebas_de_exclusion()
print("Sorteo estratificado: numeracion")
pruebas_de_numeracion()
print("Sorteo estratificado: mezcla y reproducibilidad")
pruebas_de_mezcla_y_reproducibilidad()
print("Aleatorizacion restringida: ninguna racha larga")
pruebas_de_racha()
print("Aleatorizacion restringida: la frontera con lo ya corrido")
pruebas_de_racha_en_la_frontera()
print("Aleatorizacion restringida: cuando no se puede cumplir")
pruebas_de_racha_imposible()
print("Sorteo estratificado: lo que tiene que rechazar")
pruebas_de_negativas_estratificadas()
print("Sorteo estratificado sobre el catalogo real")
pruebas_estratificadas_sobre_el_catalogo_real()

print()
if fallos:
    print(f"{len(fallos)} FALLAN: {', '.join(fallos)}")
    sys.exit(1)
print("Todo pasa.")
