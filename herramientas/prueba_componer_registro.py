#!/usr/bin/env python3
"""Prueba del compositor de registros de mision. Sin ROS corriendo y sin Gazebo.

    python3 herramientas/prueba_componer_registro.py

Comprueba las restricciones cruzadas de la §4.3 de
Documentos/ESQUEMA_REGISTRO_MISION.md. Tarda segundos, asi que no hay excusa
para no correrlo antes de cada campana.
"""

import json
import os
import sys

try:
    import jsonschema
except ImportError:
    sys.exit("Falta jsonschema. Instalar con:\n"
             "    sudo apt install -y python3-jsonschema\n"
             "Solo hace falta en el PC, que es quien compone: el carro graba el\n"
             "bag y no valida nada.")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESQUEMA = os.path.join(RAIZ, "Documentos", "esquema_registro_mision.json")

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def registro_valido():
    """Un registro de condicion B en simulacion, con exito. Base de los casos."""
    return {
        "esquema_version": "1.0.0",
        "mision": {
            "mision_id": "S24_B_20260827_143052",
            "campana": "S24_simulacion",
            "banco": "simulacion",
            "condicion": "B",
            "semilla": 1234,
            "es_piloto": False,
        },
        "procedencia": {
            "commit": "abc1234", "etiqueta": "", "repositorio_limpio": True,
            "distro": "humble", "mundo": "mundo_definitivo_piso1.world",
            "mapa": "mapa_piso1.yaml", "catalogo_puntos": "puntos_interes.yaml",
            "catalogo_sha256": "0" * 64, "bag": "S24_B_001",
            "fecha_utc": "2026-08-27T14:30:52Z",
        },
        "solicitud": {
            "origen_id": "piso1_escalera", "destino_id": "piso2_escalera",
            "nivel_origen": 1, "nivel_destino": 2, "entre_niveles": True,
            "tramos": [],
        },
        "marcas": {
            "reloj": "/clock", "t_solicitud": 0.0, "t_robot_activo": 0.2,
            "t_primer_movimiento": 0.9, "t_fin_tramo1": 40.0,
            "t_inicio_tramo2": 41.5, "t_completada": 95.0,
        },
        "verdad_de_terreno": {
            "fuente": "gazebo_worldpose_via_odom", "error_posicion_m": 0.19,
            "pose_final": {"x": -19.4, "y": 5.9, "yaw": -1.57},
            "incertidumbre_m": 0.0, "medido_por": "automatico", "nota": "",
        },
        "veredicto": {
            "exito": True, "c1_posicion": True,
            "c2_completada_sin_fallida": True, "c3_relevo": True,
            "motivo_fallo": "",
        },
        "descriptivas": {
            "error_rumbo_rad": 0.05, "desviacion_z_m": {"robot1": 1.9e-06},
            "distancia_recorrida_m": 31.2, "num_cuspides": 0,
            "tiempo_total_s": 95.0, "deriva_map_odom_m": 1.977,
        },
        "salud_del_banco": {
            "rtf": 0.995, "controladores_activos": {"robot1": "7/7"},
            "gzserver_vivo_al_final": True, "descartada": False,
            "causa_descarte": None,
        },
        "traza": {"bag": "S24_B_001", "decimada_hz": 5.0, "puntos": []},
    }


def valida(registro, esquema):
    """True si el registro cumple el esquema."""
    try:
        jsonschema.validate(registro, esquema)
        return True
    except jsonschema.ValidationError:
        return False


def marcas_en_orden(registro):
    """True si las marcas presentes van en orden creciente.

    JSON Schema draft-07 NO puede comparar dos campos entre si, asi que esta
    regla de la §4.3 -'t_fin_tramo1 <= t_inicio_tramo2'- no cabe en el esquema y
    hay que comprobarla aparte. No es un detalle: el hueco de relevo es
    't_inicio_tramo2 - t_fin_tramo1', y si el orden se invierte OE4 reporta un
    tiempo negativo sin que nada chille.

    La tarea 4 mueve esta funcion a componer_registro.py, que es quien la
    necesita en produccion; aqui vive mientras tanto para que la regla no quede
    sin comprobar entre una tarea y la siguiente.
    """
    m = registro["marcas"]
    secuencia = ["t_solicitud", "t_robot_activo", "t_primer_movimiento",
                 "t_fin_tramo1", "t_inicio_tramo2", "t_completada"]
    vistos = [m[k] for k in secuencia if m[k] is not None]
    return all(a <= b for a, b in zip(vistos, vistos[1:]))


def pruebas_de_esquema(esquema):
    check("el registro de referencia es valido", valida(registro_valido(), esquema))

    # Un campo mal escrito tiene que reventar, no colarse: si 'additionalProperties'
    # se quedara en true, un typo del compositor produciria registros que validan y
    # a los que les falta justo el campo que se creia estar escribiendo.
    r = registro_valido(); r["marcas"]["t_completadaa"] = 95.0
    check("un campo con el nombre mal escrito se rechaza", not valida(r, esquema))

    # §4.3, restriccion 1: simulacion exige /clock, oraculo y RTF.
    r = registro_valido(); r["marcas"]["reloj"] = "pared"
    check("simulacion con reloj de pared se rechaza", not valida(r, esquema))
    r = registro_valido(); r["salud_del_banco"]["rtf"] = None
    check("simulacion sin RTF se rechaza", not valida(r, esquema))

    # §4.3, restriccion 2: el banco fisico no tiene oraculo ni RTF.
    r = registro_valido()
    r["mision"]["banco"] = "fisico"
    r["marcas"]["reloj"] = "pared"
    r["verdad_de_terreno"]["fuente"] = "cinta_metrica"
    r["verdad_de_terreno"]["pose_final"] = None
    r["verdad_de_terreno"]["incertidumbre_m"] = 0.01
    r["verdad_de_terreno"]["medido_por"] = "Santiago"
    r["salud_del_banco"]["rtf"] = None
    r["salud_del_banco"]["gzserver_vivo_al_final"] = None
    r["descriptivas"]["deriva_map_odom_m"] = None
    check("el registro fisico equivalente es valido", valida(r, esquema))
    r["verdad_de_terreno"]["pose_final"] = {"x": 0.0, "y": 0.0, "yaw": 0.0}
    check("fisico con pose_final se rechaza (seria llamar verdad a rf2o)",
          not valida(r, esquema))

    # §4.3, restriccion 3: condicion A no tiene relevo.
    r = registro_valido()
    r["mision"]["condicion"] = "A"
    r["solicitud"]["entre_niveles"] = False
    r["marcas"]["t_fin_tramo1"] = None
    r["marcas"]["t_inicio_tramo2"] = None
    r["veredicto"]["c3_relevo"] = None
    check("el registro de condicion A es valido", valida(r, esquema))
    r["marcas"]["t_fin_tramo1"] = 40.0
    check("condicion A con marca de relevo se rechaza", not valida(r, esquema))

    # §4.3, restriccion 4: un exito no puede tener marcas incompletas.
    r = registro_valido(); r["marcas"]["t_completada"] = None
    check("exito sin t_completada se rechaza", not valida(r, esquema))

    # §4.3: una mision fallida SI puede no tener t_completada. Es el caso que la
    # tasa de exito necesita contar, asi que el esquema no puede prohibirlo.
    r = registro_valido()
    r["veredicto"]["exito"] = False
    r["veredicto"]["c1_posicion"] = False
    r["veredicto"]["motivo_fallo"] = "el destino no esta en el catalogo"
    r["marcas"]["t_completada"] = None
    r["verdad_de_terreno"]["error_posicion_m"] = None
    check("el registro de una mision fallida es valido", valida(r, esquema))

    # §4.3: condicion B exige c3_relevo DECIDIDO, aunque las marcas puedan faltar.
    r = registro_valido(); r["veredicto"]["c3_relevo"] = None
    check("condicion B sin c3_relevo se rechaza", not valida(r, esquema))

    # §4.3: una mision B que falla ANTES de la transferencia no produce las dos
    # marcas de relevo, y el esquema no puede obligar a inventarlas.
    r = registro_valido()
    r["veredicto"]["exito"] = False
    r["veredicto"]["c1_posicion"] = False
    r["veredicto"]["c3_relevo"] = False
    r["veredicto"]["motivo_fallo"] = "fallo antes de llegar a la transferencia"
    r["marcas"]["t_fin_tramo1"] = None
    r["marcas"]["t_inicio_tramo2"] = None
    r["marcas"]["t_completada"] = None
    r["verdad_de_terreno"]["error_posicion_m"] = None
    check("B que falla antes del relevo, sin marcas de relevo, es valido",
          valida(r, esquema))

    # ...pero un EXITO en B con esas marcas vacias es un error del compositor.
    r = registro_valido()
    r["marcas"]["t_fin_tramo1"] = None
    r["marcas"]["t_inicio_tramo2"] = None
    check("exito en B sin marcas de relevo se rechaza", not valida(r, esquema))

    # §4.3: si hay t_inicio_tramo2 tiene que haber t_fin_tramo1. Un tramo 2 que
    # arranca sin que el tramo 1 haya terminado deja el hueco de relevo sin
    # definir, que es justo la metrica de OE4.
    r = registro_valido()
    r["veredicto"]["exito"] = False
    r["veredicto"]["c1_posicion"] = False
    r["veredicto"]["c3_relevo"] = False
    r["veredicto"]["motivo_fallo"] = "x"
    r["marcas"]["t_completada"] = None
    r["marcas"]["t_fin_tramo1"] = None
    check("t_inicio_tramo2 sin t_fin_tramo1 se rechaza", not valida(r, esquema))

    # §4.3, restriccion 6, el sentido que se olvida: una corrida NO descartada
    # no puede arrastrar una causa de descarte. Si no se comprueba, un registro
    # puede decir a la vez que vale y por que no vale.
    r = registro_valido(); r["salud_del_banco"]["causa_descarte"] = "rtf_bajo"
    check("no descartada con causa de descarte se rechaza", not valida(r, esquema))

    # §4.3, restriccion 5, y §3.9: la lista de descartes es cerrada.
    r = registro_valido()
    r["salud_del_banco"]["descartada"] = True
    r["salud_del_banco"]["causa_descarte"] = "rtf_bajo"
    check("descarte por una causa del §8 es valido", valida(r, esquema))
    r["salud_del_banco"]["causa_descarte"] = "amcl_se_perdio"
    check("descarte por 'amcl se perdio' se rechaza (§8: eso es lo que se mide)",
          not valida(r, esquema))
    r = registro_valido(); r["salud_del_banco"]["descartada"] = True
    check("descarte sin causa se rechaza", not valida(r, esquema))


def pruebas_de_orden():
    check("el registro de referencia tiene las marcas en orden",
          marcas_en_orden(registro_valido()))

    r = registro_valido()
    r["marcas"]["t_inicio_tramo2"] = 39.0     # antes de t_fin_tramo1 = 40.0
    check("un hueco de relevo negativo se detecta", not marcas_en_orden(r))

    # Las marcas ausentes no rompen el orden: se saltan, no se comparan contra
    # None. Una condicion A valida tiene dos huecos en mitad de la secuencia.
    r = registro_valido()
    r["marcas"]["t_fin_tramo1"] = None
    r["marcas"]["t_inicio_tramo2"] = None
    check("las marcas null no cuentan como desorden", marcas_en_orden(r))


def main():
    with open(ESQUEMA, encoding="utf-8") as f:
        esquema = json.load(f)
    print("Esquema del registro de mision")
    pruebas_de_esquema(esquema)
    print("Orden de las marcas (no cabe en draft-07)")
    pruebas_de_orden()
    print(f"\n{len(fallos)} fallo(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
