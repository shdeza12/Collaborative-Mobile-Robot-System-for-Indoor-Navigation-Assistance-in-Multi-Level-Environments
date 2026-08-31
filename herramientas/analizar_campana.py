#!/usr/bin/env python3
"""Analizador de campana: agrega los registros de mision y da las metricas de OE4.

    python3 herramientas/analizar_campana.py Documentos/Evidencia/registros
    python3 herramientas/analizar_campana.py <dir> --json Evidencia/S24_metricas.json

Lee los JSON que compone componer_registro.py -esquema 1.0.0- y produce las
cuatro metricas del §2 del PROTOCOLO_EXPERIMENTAL con su dispersion, mas la
contabilidad de descartes contra el techo del 20 % del §8. No abre bags, no
necesita ROS y no necesita el workspace sourceado: si los registros existen,
esto corre en cualquier maquina.

Es deliberadamente desconfiado. El §8 dice que una campana se corrompe por tres
sitios -descartar sin causa admisible, dejar de contar una corrida fallida, y
agregar en una sola tasa cosas que no son la misma condicion experimental- y los
tres se comprueban antes de calcular nada. Si algo no cuadra, el veredicto es
INVALIDA y las metricas se imprimen igual, marcadas, para poder diagnosticar.

Lo que este analizador NO puede dar, y conviene saberlo antes de leer su salida:

  - La continuidad binaria de RF-24. El esquema 1.0.0 no tiene el campo. Se
    calcula el hueco del relevo, que si sale de las marcas, y la parte binaria
    se declara no medible en vez de inventarla.
  - Un valor por mision del tiempo de asignacion. Por el §3.2.2 se reporta como
    cota superior de un tick de /clock. Un valor > 0 no es una medida mejor: es
    un hallazgo grave, y se lista aparte.
"""

import argparse
import glob
import json
import math
import os
import statistics
import sys

# El enumerado cerrado del §8 del protocolo, replicado aqui a proposito: el
# esquema JSON lo impone al escribir y esto lo vuelve a imponer al leer. Un
# registro escrito a mano que se salte el validador no se cuela por aqui.
CAUSAS_ADMITIDAS = {"caida_gazebo", "controladores_incompletos",
                    "rtf_bajo", "fallo_anfitrion"}

# §8: "Si los descartes superan el 20 % de las corridas, la campana no es
# valida". "Superan" es estricto: el 20 % justo pasa.
TECHO_DESCARTE = 0.20

# §3.2.1: /clock lo publica gazebo_ros_init a 10 Hz, asi que todo sello del bag
# esta cuantizado a 100 ms. Es el suelo de resolucion, no un parametro.
TICK_CLOCK_S = 0.1

# §3.3: el criterio de exito posicional. Aqui no decide nada -el veredicto ya
# viene resuelto en el registro-; solo sirve para contar cuantas llegadas caen
# por encima, que es el dato que hace falta para la decision del criterio.
UMBRAL_LLEGADA_M = 0.25

# RF-26 / §6.1.
N_SIMULACION = 30

# Las dos versiones del registro que este analizador entiende. 1.1.0 anadio
# veredicto.continuidad el 2026-08-31; 1.0.0 se sigue leyendo porque los tres
# registros de S20 son evidencia entregada y no se reescribe la historia. Lo que
# NO se hace es tratar su ausencia de continuidad como continuidad: las misiones
# 1.0.0 salen del denominador de RF-24 y se listan.
VERSIONES_LEIBLES = {"1.0.0", "1.1.0"}

# t de Student de dos colas al 95 %. Sin scipy a proposito: el analizador tiene
# que correr en el portatil, en el carro y en la maquina del jurado.
T_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101,
        19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064,
        25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
        40: 2.021, 60: 2.000, 120: 1.980}
Z_95 = 1.959963985


def t_critica(df):
    if df in T_95:
        return T_95[df]
    if df < 1:
        return None
    for corte in (40, 60, 120):
        if df <= corte:
            return T_95[corte]
    return Z_95


# --------------------------------------------------------------------------
# Estadistica
# --------------------------------------------------------------------------

def wilson(exitos, n, z=Z_95):
    """Intervalo de Wilson al 95 % para una proporcion.

    Es el metodo que ya usa el protocolo: el §6.1 afirma que con 4 aciertos de 5
    el intervalo va del 38 % al 96 %, y eso es Wilson (37,6-96,4). Clopper-Pearson
    daria 28-99 y Wald 45-100. Se replica el mismo metodo para que los numeros
    del informe cuadren con los que el protocolo ya dejo escritos.
    """
    if n <= 0:
        return (None, None)
    p = exitos / n
    d = 1.0 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    semi = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centro - semi), min(1.0, centro + semi))


def resumen_continuo(valores):
    """n, mediana, media, desviacion, rango e IC del 95 % de la media.

    Se dan mediana y media juntas a proposito. Con N=30 y colas -que es lo que
    dio el pilotaje- la mediana describe mejor el caso tipico y la media es la
    que lleva IC; enfrentarlas en la misma linea deja ver si la distribucion
    esta sesgada sin tener que graficarla.
    """
    v = sorted(x for x in valores if x is not None)
    n = len(v)
    base = {"n": n, "mediana": None, "media": None, "sd": None, "ee": None,
            "min": None, "max": None, "p90": None, "ic95": (None, None)}
    if n == 0:
        return base
    base["mediana"] = statistics.median(v)
    base["media"] = statistics.fmean(v)
    base["min"], base["max"] = v[0], v[-1]
    base["p90"] = v[min(n - 1, int(math.ceil(0.90 * n)) - 1)]
    if n < 2:
        return base
    base["sd"] = statistics.stdev(v)
    base["ee"] = base["sd"] / math.sqrt(n)
    t = t_critica(n - 1)
    base["ic95"] = (base["media"] - t * base["ee"],
                    base["media"] + t * base["ee"])
    return base


# --------------------------------------------------------------------------
# Las restas del §3, sacadas de las marcas
# --------------------------------------------------------------------------

def _resta(marcas, fin, ini):
    a, b = marcas.get(fin), marcas.get(ini)
    if a is None or b is None:
        return None
    return a - b


def t_respuesta_de(registro):
    """§3.1: t_primer_movimiento - t_solicitud."""
    return _resta(registro.get("marcas", {}), "t_primer_movimiento",
                  "t_solicitud")


def t_asignacion_de(registro):
    """§3.2: t_robot_activo - t_solicitud. Cuantizado a un tick de /clock."""
    return _resta(registro.get("marcas", {}), "t_robot_activo", "t_solicitud")


def hueco_de(registro):
    """§3.4: t_inicio_tramo2 - t_fin_tramo1. None si la mision es intra-nivel."""
    if not registro.get("solicitud", {}).get("entre_niveles"):
        return None
    return _resta(registro.get("marcas", {}), "t_inicio_tramo2", "t_fin_tramo1")


def _id(registro):
    return registro.get("mision", {}).get("mision_id", "?")


# --------------------------------------------------------------------------
# Clasificacion: antes de calcular, comprobar
# --------------------------------------------------------------------------

def clasificar(registros, incluir_pilotos=False):
    """Separa validas, descartadas y pilotos, y recoge los errores del §8.

    Un registro con un error NO se cuenta en ningun sitio: ni como exito, ni
    como fallo, ni como descarte. Que desaparezca de los tres sitios a la vez es
    lo que hace que el N no cuadre y que el error sea imposible de ignorar.
    """
    errores, validas, descartadas, pilotos = [], [], [], []

    bancos = {r.get("mision", {}).get("banco") for r in registros}
    if len(bancos) > 1:
        errores.append(
            f"Hay mas de un banco en el lote ({sorted(str(b) for b in bancos)}). "
            "El §6.1 manda reportar simulacion y fisico por separado y no "
            "agregarlos nunca en una sola tasa. Analizar cada uno aparte.")

    campanas = {r.get("mision", {}).get("campana") for r in registros}
    if len(campanas) > 1:
        errores.append(
            f"Hay mas de una campana en el lote ({sorted(str(c) for c in campanas)}). "
            "Agregar dos campanas en una tasa mezcla condiciones distintas.")

    for r in registros:
        mid = _id(r)
        salud = r.get("salud_del_banco", {})
        descartada = bool(salud.get("descartada"))
        causa = salud.get("causa_descarte")
        exito = r.get("veredicto", {}).get("exito")

        if descartada and causa is None:
            errores.append(f"{mid}: descartada=true sin causa. El §8 exige "
                           "causa demostrable; sin ella la corrida cuenta.")
            continue
        if descartada and causa not in CAUSAS_ADMITIDAS:
            errores.append(
                f"{mid}: causa de descarte '{causa}' fuera del enumerado del §8 "
                f"({sorted(CAUSAS_ADMITIDAS)}). Los modos de fallo de "
                "navegacion son lo que el experimento existe para cuantificar, "
                "no una excusa para descartar.")
            continue
        if not descartada and causa is not None:
            errores.append(f"{mid}: tiene causa '{causa}' con descartada=false. "
                           "O se descarta o no; el registro se contradice.")
            continue

        if descartada:
            descartadas.append(r)
            continue

        if exito is None:
            errores.append(f"{mid}: exito es null y la corrida no esta "
                           "descartada. Una corrida sin veredicto no se puede "
                           "agregar; el §8 dice que por defecto cuenta como fallo, "
                           "y eso hay que escribirlo en el registro, no suponerlo.")
            continue

        if r.get("mision", {}).get("es_piloto") and not incluir_pilotos:
            pilotos.append(r)
            continue

        validas.append(r)

    return validas, descartadas, pilotos, errores


# --------------------------------------------------------------------------
# Analisis
# --------------------------------------------------------------------------

def analizar(registros, incluir_pilotos=False):
    validas, descartadas, pilotos, errores = clasificar(registros,
                                                        incluir_pilotos)
    alertas = []
    banco = next(iter({r.get("mision", {}).get("banco")
                       for r in registros}), None) if registros else None

    # --- RF-23: tasa de exito -------------------------------------------
    n = len(validas)
    exitos = sum(1 for r in validas if r["veredicto"]["exito"])
    lo, hi = wilson(exitos, n)
    tasa = {"n": n, "exitos": exitos, "fallos": n - exitos,
            "tasa": (exitos / n) if n else None, "ic95": (lo, hi),
            "metodo": "Wilson 95 %"}

    fallos_por_motivo = {}
    for r in validas:
        if not r["veredicto"]["exito"]:
            motivo = r["veredicto"].get("motivo_fallo") or "(sin motivo)"
            fallos_por_motivo[motivo] = fallos_por_motivo.get(motivo, 0) + 1
    tasa["motivos"] = fallos_por_motivo

    # --- §8: descartes ---------------------------------------------------
    total = n + len(descartadas)
    fraccion = (len(descartadas) / total) if total else 0.0
    por_causa = {}
    for r in descartadas:
        c = r["salud_del_banco"]["causa_descarte"]
        por_causa[c] = por_causa.get(c, 0) + 1
    desc = {"n": len(descartadas), "sobre": total, "fraccion": fraccion,
            "techo": TECHO_DESCARTE, "por_causa": por_causa,
            "valida": fraccion <= TECHO_DESCARTE}
    if not desc["valida"]:
        alertas.append(
            f"Los descartes son el {fraccion:.1%} de las corridas y superan el "
            f"{TECHO_DESCARTE:.0%} del §8: la campana NO es valida.")

    # --- RF-21: tiempo de respuesta --------------------------------------
    respuestas = [t_respuesta_de(r) for r in validas]
    sin_respuesta = [_id(r) for r, v in zip(validas, respuestas) if v is None]
    respuesta = resumen_continuo(respuestas)
    respuesta["sin_marca"] = sin_respuesta
    if sin_respuesta:
        alertas.append(
            f"{len(sin_respuesta)} mision(es) sin marca de primer movimiento "
            f"({', '.join(sin_respuesta[:5])}): cuentan para la tasa de exito "
            "pero no para el tiempo de respuesta, asi que los dos N difieren.")

    # --- RF-22: cota, no valor -------------------------------------------
    asign = [(_id(r), t_asignacion_de(r)) for r in validas]
    altos = [m for m, v in asign if v is not None and v > 0.0]
    asignacion = {"cota_s": TICK_CLOCK_S, "media": None, "mediana": None,
                  "n": sum(1 for _, v in asign if v is not None),
                  "por_encima_del_tick": altos,
                  "nota": ("§3.2.2: no se reporta un valor por mision. Se "
                           "afirma que la asignacion tarda menos de un tick de "
                           "/clock (< 100 ms) en las N misiones. El valor "
                           "puntual sale del banco de banco_tiempo_asignacion.py.")}
    if altos:
        alertas.append(
            f"Tiempo de asignacion > 0 en {len(altos)} mision(es) "
            f"({', '.join(altos[:5])}). Por el §3.2.2 eso significa mas de "
            "100 ms asignando, y hay que investigarlo ANTES de agregar nada.")

    # --- RF-24: continuidad ----------------------------------------------
    entre = [r for r in validas if r.get("solicitud", {}).get("entre_niveles")]
    huecos = [hueco_de(r) for r in entre]
    sin_hueco = [_id(r) for r, v in zip(entre, huecos) if v is None]
    hueco = resumen_continuo(huecos)
    hueco["sin_marca"] = sin_hueco

    # La parte binaria existe desde el esquema 1.1.0. Los registros anteriores
    # no traen el campo, y la ausencia NO se interpreta como continuidad: se
    # cuentan aparte y se avisa. Dar por continua una mision que nadie miro es
    # justo el sesgo que la §8 persigue en los descartes, aplicado a la variable
    # de respuesta.
    binaria = {"medible": False, "n": 0, "continuas": 0, "tasa": None,
               "ic95": (None, None), "discontinuas": [], "sin_campo": [],
               "motivo": ""}
    for r in entre:
        c = r.get("veredicto", {}).get("continuidad")
        if not isinstance(c, dict) or "continua" not in c:
            binaria["sin_campo"].append(_id(r))
            continue
        if c["continua"] is None:
            continue
        binaria["n"] += 1
        if c["continua"]:
            binaria["continuas"] += 1
        else:
            binaria["discontinuas"].append(_id(r))
    if binaria["n"]:
        binaria["medible"] = True
        binaria["tasa"] = binaria["continuas"] / binaria["n"]
        binaria["ic95"] = wilson(binaria["continuas"], binaria["n"])
    elif binaria["sin_campo"]:
        binaria["motivo"] = (
            "Ninguna mision entre niveles trae veredicto.continuidad. Ese campo "
            "es del esquema 1.1.0; los registros anteriores hay que recomponerlos "
            "con componer_registro.py para poder medir RF-24.")

    continuidad = {"misiones_entre_niveles": len(entre), "hueco": hueco,
                   "binaria": binaria}

    if binaria["sin_campo"]:
        alertas.append(
            f"RF-24 -la variable de respuesta principal del §2- no es medible en "
            f"{len(binaria['sin_campo'])} mision(es) "
            f"({', '.join(binaria['sin_campo'][:5])}): el registro es anterior al "
            "esquema 1.1.0 y no trae el campo de continuidad. NO se cuentan como "
            "continuas; hay que recomponerlas desde el bag.")
    if binaria["discontinuas"]:
        alertas.append(
            f"Continuidad rota en {len(binaria['discontinuas'])} mision(es) "
            f"({', '.join(binaria['discontinuas'][:5])}). Es la variable de "
            "respuesta principal, asi que esto es el resultado, no una "
            "incidencia: los instantes exactos estan en el registro, en "
            "veredicto.continuidad.")
    if sin_hueco:
        alertas.append(
            f"{len(sin_hueco)} mision(es) entre niveles sin marcas de relevo "
            f"({', '.join(sin_hueco[:5])}): el hueco no se puede calcular.")

    # --- Error de llegada, como distribucion -----------------------------
    errs = [r.get("verdad_de_terreno", {}).get("error_posicion_m")
            for r in validas]
    llegada = resumen_continuo(errs)
    llegada["umbral_m"] = UMBRAL_LLEGADA_M
    llegada["por_encima_de_025"] = sum(1 for e in errs
                                       if e is not None and e > UMBRAL_LLEGADA_M)

    # --- Tamano de muestra ------------------------------------------------
    if banco == "simulacion" and total and total != N_SIMULACION:
        alertas.append(
            f"RF-26 pide N = {N_SIMULACION} corridas en simulacion y el lote "
            f"tiene {total}. Con N menor los intervalos se ensanchan y las "
            "afirmaciones del informe tienen que caber en ese ancho.")

    if errores:
        alertas.append(f"{len(errores)} registro(s) con errores de integridad; "
                       "no se cuentan en ningun sitio, asi que el N de arriba "
                       "no cuadra con los archivos leidos.")

    # Un lote sin ninguna corrida valida NO puede salir VALIDA. El runbook
    # corre este guion despues de cada mision y encadena con su codigo de
    # salida; si un filtro mal escrito o un directorio equivocado dejan el
    # lote vacio, responder "VALIDA" seria emitir la senal mas fuerte que
    # este programa tiene desde cero evidencia. Una campana vacia no es
    # buena ni mala: es que no hay campana, y eso se dice.
    if n == 0:
        alertas.append(
            "No queda ninguna corrida que contar: 0 validas de "
            f"{len(registros)} registro(s) leidos ({len(pilotos)} piloto(s), "
            f"{len(descartadas)} descartada(s), {len(errores)} con errores). "
            "Comprueba el directorio y el filtro --campana antes de leer "
            "nada de lo de arriba.")

    veredicto = "VALIDA"
    if errores or not desc["valida"] or n == 0:
        veredicto = "INVALIDA"

    return {"veredicto": veredicto, "banco": banco,
            "campana": next(iter({r.get("mision", {}).get("campana")
                                  for r in registros}), None) if registros else None,
            "leidos": len(registros), "pilotos": len(pilotos),
            "exito": tasa, "descartes": desc, "respuesta": respuesta,
            "asignacion": asignacion, "continuidad": continuidad,
            "llegada": llegada, "errores": errores, "alertas": alertas}


# --------------------------------------------------------------------------
# Salida
# --------------------------------------------------------------------------

def _f(v, d=3, suf=""):
    return "--" if v is None else f"{v:.{d}f}{suf}"


def _linea_continua(nombre, r, unidad="s"):
    if r["n"] == 0:
        return f"  {nombre:<24} sin datos"
    ic = (f"[{_f(r['ic95'][0])}, {_f(r['ic95'][1])}]"
          if r["ic95"][0] is not None else "IC no calculable con n<2")
    return (f"  {nombre:<24} n={r['n']:<3} mediana={_f(r['mediana'])} {unidad}"
            f"   media={_f(r['media'])} {unidad}  IC95 {ic}\n"
            f"  {'':<24} sd={_f(r['sd'])}  rango [{_f(r['min'])}, "
            f"{_f(r['max'])}]  p90={_f(r['p90'])}")


def formatear(inf):
    L = []
    L.append("=" * 78)
    L.append(f"ANALISIS DE CAMPANA  ·  {inf['campana']}  ·  banco: {inf['banco']}")
    L.append(f"Registros leidos: {inf['leidos']}   "
             f"pilotos excluidos: {inf['pilotos']}   "
             f"VEREDICTO: {inf['veredicto']}")
    L.append("=" * 78)

    t = inf["exito"]
    L.append("\nRF-23 · Tasa de exito  (§3.3: posicion <= 0,25 m + COMPLETADA "
             "sin FALLIDA + relevo)")
    if t["n"]:
        L.append(f"  {t['exitos']}/{t['n']} = {t['tasa']:.1%}"
                 f"   IC95 {t['ic95'][0]:.1%} - {t['ic95'][1]:.1%}  ({t['metodo']})")
        defendible = t["ic95"][0]
        L.append(f"  Lo defendible con estos datos: «la tasa supera el "
                 f"{math.floor(defendible * 100)} %». Nada mas estrecho.")
        for motivo, k in sorted(t["motivos"].items(), key=lambda x: -x[1]):
            L.append(f"    fallo x{k}: {motivo}")
    else:
        L.append("  sin corridas validas")

    d = inf["descartes"]
    L.append(f"\n§8 · Descartes: {d['n']}/{d['sobre']} = {d['fraccion']:.1%}"
             f"   techo {d['techo']:.0%}   "
             f"{'dentro' if d['valida'] else 'SUPERADO -> campana no valida'}")
    for c, k in sorted(d["por_causa"].items(), key=lambda x: -x[1]):
        L.append(f"    {c}: {k}")

    L.append("\nRF-21 · Tiempo de respuesta (§3.1)")
    L.append(_linea_continua("t_respuesta", inf["respuesta"]))

    a = inf["asignacion"]
    L.append("\nRF-22 · Tiempo de asignacion (§3.2.2: cota, no valor)")
    L.append(f"  < {a['cota_s'] * 1000:.0f} ms en las {a['n']} misiones "
             f"con marcas completas")
    if a["por_encima_del_tick"]:
        L.append(f"  POR ENCIMA DEL TICK: {', '.join(a['por_encima_del_tick'])}")
    L.append("  El valor puntual se caracteriza en banco, no aqui "
             "(banco_tiempo_asignacion.py).")

    c = inf["continuidad"]
    b = c["binaria"]
    L.append(f"\nRF-24 · Continuidad entre niveles (§3.4)  ·  "
             f"{c['misiones_entre_niveles']} mision(es) entre niveles")
    if b["medible"]:
        L.append(f"  continuas: {b['continuas']}/{b['n']} = {b['tasa']:.1%}"
                 f"   IC95 {b['ic95'][0]:.1%} - {b['ic95'][1]:.1%}  (Wilson 95 %)")
        if b["discontinuas"]:
            L.append(f"  ROTAS: {', '.join(b['discontinuas'])}")
    elif c["misiones_entre_niveles"]:
        L.append(f"  binaria: NO MEDIBLE. {b['motivo']}")
    else:
        L.append("  binaria: no aplica, no hay misiones entre niveles")
    if b["sin_campo"]:
        L.append(f"  sin el campo (esquema < 1.1.0): {len(b['sin_campo'])} "
                 f"mision(es), excluidas del denominador")
    L.append(_linea_continua("hueco de relevo", c["hueco"]))

    g = inf["llegada"]
    L.append("\nDescriptiva · Error de llegada (no decide nada aqui; el "
             "veredicto ya viene resuelto)")
    L.append(_linea_continua("error_posicion_m", g, unidad="m"))
    if g["n"]:
        L.append(f"  por encima de {g['umbral_m']} m: "
                 f"{g['por_encima_de_025']}/{g['n']}")

    if inf["errores"]:
        L.append("\nERRORES DE INTEGRIDAD (estos registros no se cuentan en "
                 "ningun sitio)")
        for e in inf["errores"]:
            L.append(f"  · {e}")

    if inf["alertas"]:
        L.append("\nALERTAS")
        for x in inf["alertas"]:
            L.append(f"  · {x}")

    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------

def cargar(rutas):
    registros, malos = [], []
    for ruta in rutas:
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            malos.append(f"{os.path.basename(ruta)}: {e}")
            continue
        if d.get("esquema_version") not in VERSIONES_LEIBLES:
            malos.append(f"{os.path.basename(ruta)}: esquema_version="
                         f"{d.get('esquema_version')!r}, se esperaba una de "
                         f"{sorted(VERSIONES_LEIBLES)}. Los registros del "
                         "registrador en vivo tienen otra forma y no se "
                         "analizan aqui.")
            continue
        registros.append(d)
    return registros, malos


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("directorio", help="carpeta con los registros .json")
    p.add_argument("--campana", help="analizar solo los de esta campana")
    p.add_argument("--incluir-pilotos", action="store_true",
                   help="cuenta los es_piloto=true en la tasa (por defecto no)")
    p.add_argument("--json", help="ademas del texto, vuelca el informe a este archivo")
    args = p.parse_args()

    rutas = sorted(glob.glob(os.path.join(args.directorio, "*.json")))
    if not rutas:
        sys.exit(f"No hay ningun .json en {args.directorio}")

    registros, malos = cargar(rutas)
    for m in malos:
        print(f"  omitido -> {m}", file=sys.stderr)

    if args.campana:
        registros = [r for r in registros
                     if r.get("mision", {}).get("campana") == args.campana]
    if not registros:
        sys.exit("Ningun registro analizable tras filtrar. "
                 "Revisar --campana y el esquema_version de los archivos.")

    inf = analizar(registros, incluir_pilotos=args.incluir_pilotos)
    print(formatear(inf))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(inf, f, indent=2, ensure_ascii=False)
        print(f"Informe en {args.json}")

    return 0 if inf["veredicto"] == "VALIDA" else 1


if __name__ == "__main__":
    sys.exit(main())
