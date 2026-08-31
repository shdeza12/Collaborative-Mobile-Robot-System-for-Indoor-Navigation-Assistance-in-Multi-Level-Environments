#!/usr/bin/env python3
"""Prueba del analizador de campana. Sin ROS, sin Gazebo, sin bags.

    python3 herramientas/prueba_analizar_campana.py

Los registros de entrada se fabrican aqui mismo como diccionarios: el analizador
no lee bags, lee los JSON que ya compuso componer_registro.py, asi que para
probarlo basta con inventar los JSON. Tarda menos de un segundo.

Lo que se comprueba es que el analizador no deja pasar las tres maneras de
corromper una campana que el §8 del protocolo enumera: descartar sin causa
admisible, contar como no-fallo una corrida fallida, y agregar en una sola tasa
cosas que el §6.1 manda reportar por separado.
"""

import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from analizar_campana import (  # noqa: E402
    CAUSAS_ADMITIDAS, TECHO_DESCARTE, TICK_CLOCK_S,
    analizar, hueco_de, resumen_continuo, t_asignacion_de, t_respuesta_de,
    wilson,
)

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def cerca(a, b, tol=5e-3):
    return a is not None and b is not None and abs(a - b) <= tol


# --------------------------------------------------------------------------
# Fabrica de registros sinteticos
# --------------------------------------------------------------------------

def reg(n=1, exito=True, condicion="A", descartada=False, causa=None,
        banco="simulacion", campana="S24_campana", piloto=False,
        t_solicitud=100.0, t_robot_activo=100.0, t_movimiento=101.4,
        t_fin_tramo1=None, t_inicio_tramo2=None, t_completada=160.0,
        error_m=0.08, entre_niveles=None, version="1.1.0", continua=True):
    """Un registro minimo con la forma del esquema 1.0.0.

    Solo lleva los campos que el analizador mira. No valida contra el esquema
    JSON a proposito: aqui se prueba el analizador, no el compositor -de eso ya
    se encarga prueba_componer_registro.py-.
    """
    if entre_niveles is None:
        entre_niveles = condicion == "B"
    cont = {"continua": continua if entre_niveles else None,
            "ventana": [t_robot_activo, t_completada] if entre_niveles else None,
            "instantes_inactiva": [],
            "instantes_sin_agente": [] if continua else [t_solicitud + 40.0],
            "motivo": ""}
    veredicto = {"exito": exito, "c1_posicion": exito,
                 "c2_completada_sin_fallida": exito, "c3_relevo": None,
                 "motivo_fallo": "" if exito else "c1_posicion"}
    if version != "1.0.0":
        veredicto["continuidad"] = cont
    return {
        "esquema_version": version,
        "mision": {"mision_id": f"M{n:02d}", "campana": campana,
                   "banco": banco, "condicion": condicion,
                   "semilla": 20260822, "es_piloto": piloto},
        "solicitud": {"origen_id": "p_a", "destino_id": "p_b",
                      "nivel_origen": 1, "nivel_destino": 2 if entre_niveles else 1,
                      "entre_niveles": entre_niveles, "tramos": []},
        "marcas": {"reloj": "/clock", "t_solicitud": t_solicitud,
                   "t_robot_activo": t_robot_activo,
                   "t_primer_movimiento": t_movimiento,
                   "t_fin_tramo1": t_fin_tramo1,
                   "t_inicio_tramo2": t_inicio_tramo2,
                   "t_completada": t_completada},
        "verdad_de_terreno": {"error_posicion_m": error_m},
        "veredicto": veredicto,
        "descriptivas": {"distancia_recorrida_m": 40.0, "tiempo_total_s": 60.0},
        "salud_del_banco": {"rtf": 0.999, "controladores_activos": {},
                            "gzserver_vivo_al_final": True,
                            "descartada": descartada, "causa_descarte": causa},
    }


def campana(n_exitos, n_fallos=0, descartes=(), **kw):
    """Una lista de registros: exitos, luego fallos, luego descartes."""
    lote = []
    i = 0
    for _ in range(n_exitos):
        i += 1
        lote.append(reg(n=i, exito=True, **kw))
    for _ in range(n_fallos):
        i += 1
        lote.append(reg(n=i, exito=False, **kw))
    for causa in descartes:
        i += 1
        lote.append(reg(n=i, exito=None, descartada=True, causa=causa, **kw))
    return lote


# --------------------------------------------------------------------------
# 1. Wilson: el metodo tiene que ser el que el protocolo ya uso
# --------------------------------------------------------------------------

def pruebas_de_wilson():
    """El §6.1 dice: 'con 5 corridas y 4 aciertos el IC del 95 % va del 38 % al
    96 %'. Wilson da 37,6-96,4. Ninguna otra construccion habitual da eso
    -Clopper-Pearson da 28-99, Wald da 45-100-, asi que el metodo del protocolo
    es Wilson y el analizador tiene que usar el mismo o los numeros del informe
    dejarian de cuadrar con los del protocolo.
    """
    lo, hi = wilson(4, 5)
    check("Wilson 4/5 reproduce el 38-96 % del §6.1",
          cerca(lo, 0.376) and cerca(hi, 0.964), f"-> {lo:.3f}-{hi:.3f}")

    lo, hi = wilson(30, 30)
    check("Wilson 30/30 no se sale de [0,1]",
          lo > 0.88 and hi <= 1.0, f"-> {lo:.3f}-{hi:.3f}")

    lo, hi = wilson(0, 30)
    check("Wilson 0/30 no se sale de [0,1]",
          lo >= 0.0 and hi < 0.12, f"-> {lo:.3f}-{hi:.3f}")

    check("Wilson con n=0 devuelve None", wilson(0, 0) == (None, None))


# --------------------------------------------------------------------------
# 2. Marcas: las tres restas del §3
# --------------------------------------------------------------------------

def pruebas_de_marcas():
    r = reg(t_solicitud=100.0, t_movimiento=101.4, t_robot_activo=100.0,
            t_fin_tramo1=None, t_inicio_tramo2=None)
    check("t_respuesta = t_primer_movimiento - t_solicitud (§3.1)",
          cerca(t_respuesta_de(r), 1.4), f"-> {t_respuesta_de(r)}")
    check("t_asignacion = t_robot_activo - t_solicitud (§3.2)",
          cerca(t_asignacion_de(r), 0.0), f"-> {t_asignacion_de(r)}")
    check("hueco es None en mision intra-nivel (§3.4)", hueco_de(r) is None)

    b = reg(condicion="B", t_fin_tramo1=200.0, t_inicio_tramo2=203.5)
    check("hueco = t_inicio_tramo2 - t_fin_tramo1 (§3.4)",
          cerca(hueco_de(b), 3.5), f"-> {hueco_de(b)}")

    sin = reg(t_movimiento=None)
    check("marca ausente da None, no una excepcion",
          t_respuesta_de(sin) is None)


# --------------------------------------------------------------------------
# 3. Resumen continuo
# --------------------------------------------------------------------------

def pruebas_de_resumen():
    r = resumen_continuo([1.0, 2.0, 3.0, 4.0])
    check("resumen continuo: n, mediana, media",
          r["n"] == 4 and cerca(r["mediana"], 2.5) and cerca(r["media"], 2.5))
    check("resumen continuo: min y max",
          cerca(r["min"], 1.0) and cerca(r["max"], 4.0))
    check("resumen continuo: IC de t con df=3 es mas ancho que el normal",
          r["ic95"][0] < 2.5 - 1.96 * r["ee"], f"-> {r['ic95']}")
    check("resumen continuo de lista vacia no revienta",
          resumen_continuo([])["n"] == 0)
    check("resumen continuo de un solo valor no inventa IC",
          resumen_continuo([7.0])["ic95"] == (None, None))


# --------------------------------------------------------------------------
# 4. Descartes: el §8, que es por donde una campana se corrompe
# --------------------------------------------------------------------------

def pruebas_de_descartes():
    inf = analizar(campana(27, 3))
    check("una corrida fallida y no descartada cuenta como fallo (§8)",
          inf["exito"]["n"] == 30 and inf["exito"]["exitos"] == 27,
          f"-> {inf['exito']['exitos']}/{inf['exito']['n']}")

    inf = analizar(campana(27, 0, descartes=["rtf_bajo", "caida_gazebo",
                                             "fallo_anfitrion"]))
    check("los descartes con causa admisible salen de N",
          inf["exito"]["n"] == 27 and inf["descartes"]["n"] == 3,
          f"-> N={inf['exito']['n']}")

    malo = reg(exito=None, descartada=True, causa="amcl_perdido")
    inf = analizar(campana(29) + [malo])
    check("una causa fuera del enumerado es un error, no un descarte",
          any("amcl_perdido" in e for e in inf["errores"]),
          f"-> {inf['errores']}")

    huerfano = reg(exito=None, descartada=True, causa=None)
    inf = analizar(campana(29) + [huerfano])
    check("descartada=true sin causa es un error",
          any("sin causa" in e for e in inf["errores"]), f"-> {inf['errores']}")

    fantasma = reg(exito=True, descartada=False, causa="rtf_bajo")
    inf = analizar(campana(29) + [fantasma])
    check("causa con descartada=false es un error",
          any("descartada=false" in e for e in inf["errores"]),
          f"-> {inf['errores']}")

    nulo = reg(exito=None, descartada=False)
    inf = analizar(campana(29) + [nulo])
    check("exito=null sin descarte es un error: no se puede agregar",
          any("exito" in e and "null" in e for e in inf["errores"]),
          f"-> {inf['errores']}")

    check("el enumerado cerrado tiene exactamente las cuatro causas del §8",
          CAUSAS_ADMITIDAS == {"caida_gazebo", "controladores_incompletos",
                               "rtf_bajo", "fallo_anfitrion"})


# --------------------------------------------------------------------------
# 5. El techo del 20 %
# --------------------------------------------------------------------------

def pruebas_de_techo():
    check("el techo es el 20 % del §8", cerca(TECHO_DESCARTE, 0.20))

    seis = ["rtf_bajo"] * 6
    inf = analizar(campana(24, 0, descartes=seis))
    check("6 descartes de 30 son el 20 % justo y NO invalidan (§8 dice 'superan')",
          inf["descartes"]["valida"] is True,
          f"-> {inf['descartes']['fraccion']:.3f}")

    siete = ["rtf_bajo"] * 7
    inf = analizar(campana(23, 0, descartes=siete))
    check("7 descartes de 30 superan el 20 % e invalidan la campana",
          inf["descartes"]["valida"] is False,
          f"-> {inf['descartes']['fraccion']:.3f}")
    check("la campana invalida se dice en el veredicto, no solo en un numero",
          inf["veredicto"] == "INVALIDA", f"-> {inf['veredicto']}")

    # Cero corridas validas NO puede dar VALIDA. El runbook corre este guion
    # despues de cada mision y lee su codigo de salida: si un filtro mal
    # escrito deja el lote vacio, decir "VALIDA" es la senal mas fuerte
    # posible emitida desde ninguna evidencia. La campana vacia no es buena
    # ni mala: es que no hay campana.
    inf = analizar([])
    check("una campana sin ninguna corrida valida NO se declara VALIDA",
          inf["veredicto"] == "INVALIDA", f"-> {inf['veredicto']}")

    # Y el caso real que lo destapo: todos los registros del lote eran
    # pilotos, asi que quedaron excluidos y no sobro ninguno que contar.
    solo_pilotos = campana(2, piloto=True)
    inf = analizar(solo_pilotos)
    check("un lote que es todo pilotos deja n=0 y tampoco es VALIDA",
          inf["veredicto"] == "INVALIDA", f"-> {inf['veredicto']}")


# --------------------------------------------------------------------------
# 6. Lo que el §6.1 prohibe agregar
# --------------------------------------------------------------------------

def pruebas_de_agregacion():
    mixto = campana(15) + campana(10, banco="fisico")
    inf = analizar(mixto)
    check("mezclar simulacion y fisico es un error (§6.1)",
          any("banco" in e for e in inf["errores"]), f"-> {inf['errores']}")

    dos = campana(15) + campana(10, campana="S20_pilotaje")
    inf = analizar(dos)
    check("mezclar dos campanas es un error",
          any("campana" in e for e in inf["errores"]), f"-> {inf['errores']}")

    con_piloto = campana(29) + [reg(n=30, piloto=True)]
    inf = analizar(con_piloto)
    check("los pilotos no entran en la tasa por defecto",
          inf["exito"]["n"] == 29 and inf["pilotos"] == 1,
          f"-> N={inf['exito']['n']}, pilotos={inf['pilotos']}")
    inf = analizar(con_piloto, incluir_pilotos=True)
    check("...salvo que se pidan expresamente",
          inf["exito"]["n"] == 30, f"-> N={inf['exito']['n']}")


# --------------------------------------------------------------------------
# 7. RF-22: cota superior, no treinta ceros
# --------------------------------------------------------------------------

def pruebas_de_asignacion():
    check("el tick de /clock son 100 ms (§3.2.1)", cerca(TICK_CLOCK_S, 0.1))

    inf = analizar(campana(30))
    a = inf["asignacion"]
    check("con todo a cero se reporta la cota, no la media (§3.2.2)",
          a["cota_s"] == TICK_CLOCK_S and a["media"] is None,
          f"-> {a}")
    check("cero misiones por encima del tick",
          a["por_encima_del_tick"] == [], f"-> {a['por_encima_del_tick']}")

    lento = reg(n=99, t_solicitud=100.0, t_robot_activo=100.3)
    inf = analizar(campana(29) + [lento])
    check("una asignacion > 0 se marca como hallazgo grave (§3.2.2)",
          inf["asignacion"]["por_encima_del_tick"] == ["M99"],
          f"-> {inf['asignacion']['por_encima_del_tick']}")
    check("...y sale en las alertas, no enterrada en un campo",
          any("asignacion" in x.lower() for x in inf["alertas"]),
          f"-> {inf['alertas']}")


# --------------------------------------------------------------------------
# 8. RF-24: lo que el esquema 1.0.0 no permite medir
# --------------------------------------------------------------------------

def pruebas_de_continuidad():
    lote = campana(10, condicion="B", t_fin_tramo1=200.0, t_inicio_tramo2=204.0)
    inf = analizar(lote)
    check("el hueco se agrega solo sobre las misiones entre niveles (§3.4)",
          inf["continuidad"]["hueco"]["n"] == 10,
          f"-> {inf['continuidad']['hueco']['n']}")
    check("el hueco medio sale de las marcas",
          cerca(inf["continuidad"]["hueco"]["media"], 4.0),
          f"-> {inf['continuidad']['hueco']['media']}")

    # Desde el esquema 1.1.0 la parte binaria SI se mide, y es la variable de
    # respuesta principal del §2: se reporta como proporcion con su IC, igual
    # que la tasa de exito.
    b = inf["continuidad"]["binaria"]
    check("con el esquema 1.1.0 la continuidad binaria es medible",
          b["medible"] is True, f"-> {b}")
    check("10 de 10 continuas dan tasa 1,0", cerca(b["tasa"], 1.0), f"-> {b}")
    check("y lleva intervalo de Wilson como la tasa de exito",
          b["ic95"][0] is not None and b["ic95"][0] > 0.6, f"-> {b['ic95']}")
    check("no queda alerta de RF-24 no medible",
          not any("RF-24" in x and "no es medible" in x for x in inf["alertas"]),
          f"-> {inf['alertas']}")

    # Una discontinuidad tiene que salir, y salir SEPARADA del exito: la mision
    # cumple las tres condiciones del §3.3 y aun asi tuvo un bache. Si el
    # analizador la contara como fallo, RF-23 y RF-24 dejarian de ser dos
    # variables y la del §2 se perderia dentro de la otra.
    roto = campana(9, condicion="B", t_fin_tramo1=200.0, t_inicio_tramo2=204.0)
    roto.append(reg(n=10, condicion="B", exito=True, continua=False,
                    t_fin_tramo1=200.0, t_inicio_tramo2=204.0))
    inf = analizar(roto)
    check("una mision discontinua baja la tasa de continuidad",
          inf["continuidad"]["binaria"]["continuas"] == 9,
          f"-> {inf['continuidad']['binaria']}")
    check("...y NO baja la tasa de exito, que es otra variable",
          inf["exito"]["exitos"] == 10, f"-> {inf['exito']['exitos']}/10")
    check("...y se nombran las misiones discontinuas, para poder ir al bag",
          inf["continuidad"]["binaria"]["discontinuas"] == ["M10"],
          f"-> {inf['continuidad']['binaria']['discontinuas']}")
    check("una discontinuidad es una alerta: es la variable principal",
          any("continuidad" in x.lower() for x in inf["alertas"]),
          f"-> {inf['alertas']}")

    # Compatibilidad: los tres registros de S20 son 1.0.0 y no traen el campo.
    viejo = campana(10, condicion="B", version="1.0.0",
                    t_fin_tramo1=200.0, t_inicio_tramo2=204.0)
    inf = analizar(viejo)
    check("con registros 1.0.0 la continuidad binaria sigue no siendo medible",
          inf["continuidad"]["binaria"]["medible"] is False,
          f"-> {inf['continuidad']['binaria']}")
    check("...y se avisa, en vez de contarlos como continuos",
          any("RF-24" in x for x in inf["alertas"]), f"-> {inf['alertas']}")

    solo_a = analizar(campana(10, condicion="A"))
    check("sin misiones entre niveles el hueco queda vacio, no en cero",
          solo_a["continuidad"]["hueco"]["n"] == 0)
    check("y la continuidad no se declara ni medible ni incumplida",
          solo_a["continuidad"]["binaria"]["tasa"] is None,
          f"-> {solo_a['continuidad']['binaria']}")


# --------------------------------------------------------------------------
# 9. Error de llegada: la distribucion, no el aprobado
# --------------------------------------------------------------------------

def pruebas_de_llegada():
    errores = [0.05, 0.11, 0.19, 0.27, 0.33]
    lote = [reg(n=i + 1, exito=e <= 0.25, error_m=e)
            for i, e in enumerate(errores)]
    inf = analizar(lote)
    check("el error de llegada se reporta como distribucion",
          inf["llegada"]["n"] == 5 and cerca(inf["llegada"]["mediana"], 0.19),
          f"-> {inf['llegada']}")
    check("se cuenta cuantas caen por encima de los 0,25 m",
          inf["llegada"]["por_encima_de_025"] == 2,
          f"-> {inf['llegada']['por_encima_de_025']}")


# --------------------------------------------------------------------------
# 10. N: RF-26 pide 30
# --------------------------------------------------------------------------

def pruebas_de_n():
    inf = analizar(campana(28, 2))
    check("con N=30 en simulacion no hay alerta de tamano",
          not any("RF-26" in x for x in inf["alertas"]), f"-> {inf['alertas']}")
    inf = analizar(campana(9, 1))
    check("con N<30 en simulacion se avisa de RF-26",
          any("RF-26" in x for x in inf["alertas"]), f"-> {inf['alertas']}")


def main():
    print("Intervalo de Wilson")
    pruebas_de_wilson()
    print("Marcas y restas del §3")
    pruebas_de_marcas()
    print("Resumen de variables continuas")
    pruebas_de_resumen()
    print("Descartes del §8")
    pruebas_de_descartes()
    print("Techo del 20 %")
    pruebas_de_techo()
    print("Lo que el §6.1 prohibe agregar")
    pruebas_de_agregacion()
    print("Tiempo de asignacion (RF-22)")
    pruebas_de_asignacion()
    print("Continuidad entre niveles (RF-24)")
    pruebas_de_continuidad()
    print("Error de llegada")
    pruebas_de_llegada()
    print("Tamano de muestra (RF-26)")
    pruebas_de_n()
    print(f"\n{len(fallos)} fallo(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
