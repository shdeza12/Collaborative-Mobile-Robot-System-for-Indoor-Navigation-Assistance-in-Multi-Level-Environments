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

sys.path.insert(0, AQUI)
from componer_registro import (  # noqa: E402
    marcas_de, marcas_en_orden, primer_movimiento, veredicto_de,
    INACTIVA, TRAMO_1, TRANSFERENCIA, TRAMO_2, COMPLETADA, FALLIDA,
)

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
          marcas_en_orden(registro_valido()["marcas"]))

    m = registro_valido()["marcas"]
    m["t_inicio_tramo2"] = 39.0     # antes de t_fin_tramo1 = 40.0
    check("un hueco de relevo negativo se detecta", not marcas_en_orden(m))

    # Las marcas ausentes no rompen el orden: se saltan, no se comparan contra
    # None. Una condicion A valida tiene dos huecos en mitad de la secuencia.
    m = registro_valido()["marcas"]
    m["t_fin_tramo1"] = None
    m["t_inicio_tramo2"] = None
    check("las marcas null no cuentan como desorden", marcas_en_orden(m))


def pruebas_de_marcas():
    # §3.5: |v| >= 0,02 m/s en TRES muestras consecutivas. Un pico aislado de
    # ruido del estimador no puede disparar t_primer_movimiento: adelantaria la
    # marca y t_respuesta saldria mas corto de lo real.
    ruido = [(0.0, 0.0, 0.0), (0.1, 0.5, 0.0), (0.2, 0.0, 0.0),
             (0.3, 0.0, 0.0), (0.4, 0.1, 0.0), (0.5, 0.1, 0.0),
             (0.6, 0.1, 0.0)]
    check("un pico aislado NO dispara el primer movimiento",
          primer_movimiento(ruido) == 0.4, f"-> {primer_movimiento(ruido)}")
    check("robot quieto no tiene primer movimiento",
          primer_movimiento([(0.0, 0.0, 0.0), (0.1, 0.001, 0.0)]) is None)
    check("velocidad puramente lateral tambien cuenta",
          primer_movimiento([(0.0, 0.0, 0.1)] * 3) == 0.0)

    # Condicion B completa.
    estados_b = [
        (10.0, INACTIVA, "", "m1"), (10.2, TRAMO_1, "robot1", "m1"),
        (40.0, TRANSFERENCIA, "robot1", "m1"), (41.0, TRAMO_2, "robot2", "m1"),
        (95.0, COMPLETADA, "robot2", "m1"),
    ]
    mov = {
        "robot1": [(10.9, 0.3, 0.0), (11.0, 0.3, 0.0), (11.1, 0.3, 0.0)],
        "robot2": [(41.5, 0.3, 0.0), (41.6, 0.3, 0.0), (41.7, 0.3, 0.0)],
    }
    m = marcas_de(estados_b, mov, "B")
    check("t_solicitud es el primer estado no INACTIVA", m["t_solicitud"] == 10.2)
    check("t_fin_tramo1 es el primer TRANSFERENCIA", m["t_fin_tramo1"] == 40.0)
    check("t_inicio_tramo2 es el primer movimiento del segundo robot",
          m["t_inicio_tramo2"] == 41.5)
    check("t_completada es el primer COMPLETADA", m["t_completada"] == 95.0)

    # El bag empieza a grabar ANTES de que se pida la mision. Si el robot se
    # movio durante la puesta a punto, ese movimiento no es la respuesta a nada:
    # contarlo daria t_respuesta negativo. Ver desde() en componer_registro.py.
    mov_antes = dict(mov)
    mov_antes["robot1"] = ([(2.0, 0.4, 0.0), (2.1, 0.4, 0.0), (2.2, 0.4, 0.0)]
                           + mov["robot1"])
    m2 = marcas_de(estados_b, mov_antes, "B")
    check("el movimiento anterior a la solicitud no cuenta",
          m2["t_primer_movimiento"] == 10.9, f"-> {m2['t_primer_movimiento']}")
    check("y por tanto t_respuesta no sale negativo",
          m2["t_primer_movimiento"] - m2["t_solicitud"] > 0)

    # Lo mismo con el segundo robot: sus muestras se graban durante todo el
    # tramo 1, y un empujon o ruido de rf2o daria un hueco de relevo negativo.
    mov_ruido2 = dict(mov)
    mov_ruido2["robot2"] = ([(12.0, 0.3, 0.0), (12.1, 0.3, 0.0), (12.2, 0.3, 0.0)]
                            + mov["robot2"])
    m3 = marcas_de(estados_b, mov_ruido2, "B")
    check("el movimiento del segundo robot antes del relevo no cuenta",
          m3["t_inicio_tramo2"] == 41.5, f"-> {m3['t_inicio_tramo2']}")
    check("y el hueco de relevo no sale negativo", marcas_en_orden(m3))

    # Condicion A: los campos de relevo van null, no cero.
    estados_a = [(5.0, TRAMO_1, "robot1", "m2"), (30.0, COMPLETADA, "robot1", "m2")]
    ma = marcas_de(estados_a, {"robot1": [(5.5, 0.3, 0.0)] * 3}, "A")
    check("condicion A deja las dos marcas de relevo en null",
          ma["t_fin_tramo1"] is None and ma["t_inicio_tramo2"] is None)

    # Una mision que pasa por FALLIDA no es exito, aunque despues llegue
    # COMPLETADA: es el caso del reintento manual.
    estados_f = estados_b[:3] + [(50.0, FALLIDA, "robot1", "m1"),
                                 (95.0, COMPLETADA, "robot2", "m1")]
    v = veredicto_de(marcas_de(estados_f, mov, "B"), estados_f, 0.19, "B", 1)
    check("pasar por FALLIDA pone c2 en false", v["c2_completada_sin_fallida"] is False)
    check("y el exito es false aunque c1 y c3 esten en verde", v["exito"] is False)

    # R3: fallar por posicion tiene que quedar distinguible de fallar por otra cosa.
    v = veredicto_de(marcas_de(estados_b, mov, "B"), estados_b, 1.98, "B", 1)
    check("llegada fuera de tolerancia pone c1 en false y solo c1",
          v["c1_posicion"] is False and v["c2_completada_sin_fallida"] is True
          and v["c3_relevo"] is True)
    check("y el motivo_fallo dice la cifra, no solo que fallo",
          "1.980" in v["motivo_fallo"], f"-> {v['motivo_fallo']}")

    # Sin medida de cinta todavia (§4.4): el veredicto no se inventa.
    v = veredicto_de(marcas_de(estados_b, mov, "B"), estados_b, None, "B", 1)
    check("sin error medido, c1 y exito van null", v["c1_posicion"] is None
          and v["exito"] is None)


def main():
    with open(ESQUEMA, encoding="utf-8") as f:
        esquema = json.load(f)
    print("Esquema del registro de mision")
    pruebas_de_esquema(esquema)
    print("Orden de las marcas (no cabe en draft-07)")
    pruebas_de_orden()
    print("Marcas y veredicto")
    pruebas_de_marcas()
    print(f"\n{len(fallos)} fallo(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
