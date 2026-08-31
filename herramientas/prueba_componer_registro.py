#!/usr/bin/env python3
"""Prueba del compositor de registros de mision. Sin Gazebo y sin nodos vivos.

    source /opt/ros/humble/setup.bash
    source ~/deepracer_sim_ws/install/setup.bash
    python3 herramientas/prueba_componer_registro.py

Comprueba las restricciones cruzadas de la §4.3 de
Documentos/ESQUEMA_REGISTRO_MISION.md y compone un registro completo a partir de
un bag sintetico que se escribe aqui mismo. Tarda segundos, asi que no hay
excusa para no correrlo antes de cada campana.

Hace falta el workspace sourceado -no un ROS corriendo- porque el lector de bags
y coordinacion_msgs viven ahi. Solo la ultima tanda lo necesita: el modulo
componer_registro se importa sin ROS a proposito.
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
    continuidad_de, marcas_de, marcas_en_orden, primer_movimiento, veredicto_de,
    INACTIVA, TRAMO_1, TRANSFERENCIA, TRAMO_2, COMPLETADA, FALLIDA, RECIBIDA,
)

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def registro_valido():
    """Un registro de condicion B en simulacion, con exito. Base de los casos."""
    return {
        "esquema_version": "1.1.0",
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
            "continuidad": {
                "continua": True, "ventana": [10.2, 95.0],
                "instantes_inactiva": [], "instantes_sin_agente": [],
                "motivo": "",
            },
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

    # Versionado del esquema. 1.1.0 anadio veredicto.continuidad el 2026-08-31 y
    # el cambio tiene que cortar en los dos sentidos: obligatorio en adelante,
    # inofensivo hacia atras. Si solo se comprobara lo primero, exigirlo en el
    # 'required' base habria invalidado los tres registros de S20, que son
    # evidencia ya entregada; si solo lo segundo, RF-24 -la variable de
    # respuesta principal- podria volver a quedarse sin medir por un olvido.
    r = registro_valido(); del r["veredicto"]["continuidad"]
    check("un registro 1.1.0 SIN continuidad se rechaza", not valida(r, esquema),
          _por_que(r, esquema))
    r["esquema_version"] = "1.0.0"
    check("el mismo registro marcado 1.0.0 sigue siendo valido",
          valida(r, esquema), _por_que(r, esquema))

    # La continuidad NO puede entrar en el AND del exito. Si alguien la anade a
    # las condiciones del §3.3 mas adelante, esta prueba lo delata: un registro
    # discontinuo y exitoso a la vez tiene que ser representable, porque es
    # justo el caso interesante -relevo con bache pero mision cumplida-.
    r = registro_valido()
    r["veredicto"]["continuidad"] = {
        "continua": False, "ventana": [10.2, 95.0], "instantes_inactiva": [],
        "instantes_sin_agente": [40.5],
        "motivo": "la mision se quedo sin nadie a cargo: robot_activo vacio en t=40.500"}
    check("exito true con continuidad false es representable",
          valida(r, esquema), _por_que(r, esquema))

    # En condicion A el §3.4 no define la metrica: null, no un false inventado.
    r = registro_valido()
    r["veredicto"]["continuidad"] = {
        "continua": None, "ventana": None, "instantes_inactiva": [],
        "instantes_sin_agente": [], "motivo": "no aplica: la mision es intra-nivel"}
    check("continuidad null con ventana null es valida",
          valida(r, esquema), _por_que(r, esquema))

    r = registro_valido()
    r["veredicto"]["continuidad"]["ventana"] = [10.2]
    check("una ventana de un solo extremo se rechaza", not valida(r, esquema))

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

    # El defecto que destapo el piloto del 2026-08-29, escrito como prueba para
    # que no pueda volver sin avisar. Si el coordinador no publica nada entre
    # 'llego la solicitud' y 'ya hay agente elegido', las dos marcas caen en el
    # MISMO mensaje y el tiempo de asignacion -una de las cuatro metricas de
    # OE4- vale cero se ejecute lo que se ejecute. No es falta de resolucion:
    # es que el estado intermedio no existia.
    quieto_y_luego_anda = {"robot1": [(11.0, 0.3, 0.0)] * 3}
    sin_recibida = [(10.0, INACTIVA, "", ""), (10.2, TRAMO_1, "robot1", "m3"),
                    (60.0, COMPLETADA, "robot1", "m3")]
    msr = marcas_de(sin_recibida, quieto_y_luego_anda, "A")
    check("sin RECIBIDA el tiempo de asignacion vale cero: es el defecto",
          msr["t_robot_activo"] - msr["t_solicitud"] == 0.0,
          f"-> {msr['t_solicitud']} y {msr['t_robot_activo']}")

    # Con el estado intermedio, t_solicitud pasa a ser lo que la §3.5 del
    # esquema siempre dijo -el instante en que el servidor ACEPTA el goal- y la
    # metrica deja de ser identicamente cero.
    con_recibida = [(10.0, INACTIVA, "", ""), (10.15, RECIBIDA, "", "m3"),
                    (10.2, TRAMO_1, "robot1", "m3"),
                    (60.0, COMPLETADA, "robot1", "m3")]
    mcr = marcas_de(con_recibida, quieto_y_luego_anda, "A")
    check("t_solicitud es el RECIBIDA y no el TRAMO_1",
          abs(mcr["t_solicitud"] - 10.15) < 1e-9, f"-> {mcr['t_solicitud']}")
    check("el tiempo de asignacion es positivo y medible",
          mcr["t_robot_activo"] - mcr["t_solicitud"] > 0,
          f"-> {mcr['t_robot_activo'] - mcr['t_solicitud']:.3f} s")
    check("las marcas siguen en orden creciente", marcas_en_orden(mcr))
    # Los bags viejos -los dos pilotos de S20- no traen RECIBIDA y tienen que
    # seguir componiendose: la constante es nueva, el formato del mensaje no.
    check("un bag sin RECIBIDA se sigue componiendo",
          msr["t_solicitud"] == 10.2 and msr["t_completada"] == 60.0)

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


def bag_sintetico(ruta):
    """Escribe un bag minimo de condicion B. Sin Gazebo y sin simulacion.

    Es lo que permite probar el compositor de forma determinista: los bags de
    ~/tesis_evidencia/S20_localizacion/ no traen /clock ni estado_mision, asi
    que no sirven de banco completo.
    """
    import rclpy.serialization
    import rosbag2_py
    from coordinacion_msgs.msg import EstadoMision
    from nav_msgs.msg import Odometry
    from rosgraph_msgs.msg import Clock

    escritor = rosbag2_py.SequentialWriter()
    escritor.open(
        rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
        rosbag2_py.ConverterOptions("", ""))
    for nombre, tipo in [("/coordinacion/estado_mision", "coordinacion_msgs/msg/EstadoMision"),
                         ("/clock", "rosgraph_msgs/msg/Clock"),
                         ("/robot1/odom", "nav_msgs/msg/Odometry"),
                         ("/robot2/odom", "nav_msgs/msg/Odometry")]:
        escritor.create_topic(rosbag2_py.TopicMetadata(
            name=nombre, type=tipo, serialization_format="cdr"))

    def estado(t, etapa, robot):
        m = EstadoMision()
        m.mision_id, m.etapa, m.robot_activo = "S24_B_prueba", etapa, robot
        # Los dos ids que ros2 bag no podria sacar del goal. Han de ser puntos
        # REALES del catalogo: _solicitud les busca el nivel alli.
        m.origen_id, m.destino_id = "piso1_escalera", "piso2_escalera"
        escritor.write("/coordinacion/estado_mision",
                       rclpy.serialization.serialize_message(m), int(t * 1e9))

    def odom(topico, t, vx, x=0.0, y=0.0):
        m = Odometry()
        m.twist.twist.linear.x = vx
        m.pose.pose.position.x = x
        m.pose.pose.position.y = y
        escritor.write(topico, rclpy.serialization.serialize_message(m),
                       int(t * 1e9))

    escritor.write("/clock", rclpy.serialization.serialize_message(Clock()), 0)
    estado(10.0, INACTIVA, "")
    estado(10.2, TRAMO_1, "robot1")
    for i in range(6):
        odom("/robot1/odom", 10.3 + i * 0.1, 0.0 if i < 6 - 3 else 0.3)
    estado(40.0, TRANSFERENCIA, "robot1")
    estado(41.0, TRAMO_2, "robot2")
    # El destino de la mision es 'piso2_escalera', que el catalogo pone en
    # (-21.5, -9.03). El robot para a 0,19 m de el: es la cifra que la prueba
    # espera ver calculada sola, sin pasarla por la linea de ordenes.
    for i in range(3):
        odom("/robot2/odom", 41.5 + i * 0.1, 0.3, -21.31, -9.03)
    estado(95.0, COMPLETADA, "robot2")
    # Una muestra DESPUES de COMPLETADA y lejos del punto. El bag sigue grabando
    # hasta que el operador corta, asi que la ultima muestra no es la llegada: si
    # el error se midiera con ella saldria 5 m y dependeria de cuando se pulso
    # Ctrl-C, que es justo lo que no puede pasar entre las 30 corridas de S24.
    odom("/robot2/odom", 120.0, 0.0, -16.31, -9.03)
    # Y robot1 sigue publicando desde el punto de transferencia del piso 1, mas
    # tarde que la ultima muestra buena de robot2. Quien llego es el robot ACTIVO
    # al final, no el que publico el ultimo mensaje del bag.
    odom("/robot1/odom", 121.0, 0.0, -19.43, 5.91)
    del escritor


def pruebas_de_continuidad():
    """RF-24, la variable de respuesta principal del §2 del protocolo.

    Anadida el 2026-08-31. Hasta entonces el esquema no tenia el campo y la
    metrica no se podia calcular desde el registro: el analizador la declaraba
    NO MEDIBLE, que para la variable principal del experimento no es una
    situacion en la que se pueda llegar a S24.
    """
    # Un relevo limpio: nunca falta agente ni se cae a INACTIVA.
    limpia = [
        (10.0, INACTIVA, "", ""), (10.15, RECIBIDA, "", "m1"),
        (10.2, TRAMO_1, "robot1", "m1"), (40.0, TRANSFERENCIA, "robot1", "m1"),
        (41.0, TRAMO_2, "robot2", "m1"), (95.0, COMPLETADA, "robot2", "m1"),
        (105.0, INACTIVA, "", ""),
    ]
    marcas = {"t_solicitud": 10.15, "t_robot_activo": 10.2, "t_completada": 95.0}
    c = continuidad_de(limpia, marcas, "B")
    check("un relevo limpio da continuidad true", c["continua"] is True, f"-> {c}")
    check("la ventana evaluada es [t_robot_activo, t_completada]",
          c["ventana"] == [10.2, 95.0], f"-> {c['ventana']}")

    # El INACTIVA posterior a COMPLETADA es el reposo normal del coordinador y
    # NO puede contar como discontinuidad: si contara, ninguna mision del mundo
    # seria continua.
    check("el INACTIVA posterior a COMPLETADA no cuenta",
          c["instantes_inactiva"] == [], f"-> {c['instantes_inactiva']}")

    # Y el preludio RECIBIDA tiene robot_activo vacio POR DISENO -§3.2 lo exige
    # asi-, de modo que evaluar desde t_solicitud haria que toda mision saliera
    # discontinua por construccion. Es el mismo defecto estructural que tuvo el
    # tiempo de asignacion en agosto, y se evita empezando en t_robot_activo.
    check("el preludio RECIBIDA, con robot_activo vacio, no cuenta",
          c["instantes_sin_agente"] == [], f"-> {c['instantes_sin_agente']}")

    # La discontinuidad que RF-24 existe para detectar: la mision se queda sin
    # nadie a cargo en mitad del relevo.
    rota = [
        (10.15, RECIBIDA, "", "m1"), (10.2, TRAMO_1, "robot1", "m1"),
        (40.0, TRANSFERENCIA, "robot1", "m1"), (40.5, TRANSFERENCIA, "", "m1"),
        (41.0, TRAMO_2, "robot2", "m1"), (95.0, COMPLETADA, "robot2", "m1"),
    ]
    c = continuidad_de(rota, marcas, "B")
    check("quedarse sin agente en mitad del relevo rompe la continuidad",
          c["continua"] is False and c["instantes_sin_agente"] == [40.5],
          f"-> {c}")

    # Caerse a INACTIVA dentro de la ventana tambien la rompe, aunque haya
    # agente: la mision dejo de estar en curso.
    caida = [
        (10.15, RECIBIDA, "", "m1"), (10.2, TRAMO_1, "robot1", "m1"),
        (50.0, INACTIVA, "robot1", "m1"), (60.0, TRAMO_2, "robot2", "m1"),
        (95.0, COMPLETADA, "robot2", "m1"),
    ]
    c = continuidad_de(caida, marcas, "B")
    check("caer a INACTIVA dentro de la ventana rompe la continuidad",
          c["continua"] is False and c["instantes_inactiva"] == [50.0], f"-> {c}")

    # Sin COMPLETADA la ventana no esta cerrada. Decir 'false' seria confundir
    # 'se quedo sin agente' con 'no termino', que son dos fallos distintos y el
    # segundo ya lo cuenta c2.
    c = continuidad_de(limpia[:4], {"t_solicitud": 10.15, "t_robot_activo": 10.2,
                                    "t_completada": None}, "B")
    check("sin t_completada la continuidad es null, no false",
          c["continua"] is None and "ventana" in c["motivo"], f"-> {c}")

    # §3.4: "Solo aplica a misiones cuyo origen y destino estan en niveles
    # distintos".
    c = continuidad_de(limpia, marcas, "A")
    check("en condicion A la continuidad es null y lo dice",
          c["continua"] is None and "intra-nivel" in c["motivo"], f"-> {c}")

    # La continuidad NO decide el exito: el §3.3 lista tres condiciones y esta
    # no es una de ellas. Es la variable de respuesta, que es otra cosa.
    mov = {"robot1": [(10.9, 0.3, 0.0)] * 3, "robot2": [(41.5, 0.3, 0.0)] * 3}
    v = veredicto_de(marcas_de(rota, mov, "B"), rota, 0.19, "B", 1)
    check("una mision discontinua puede seguir siendo un exito del §3.3",
          v["exito"] is True, f"-> {v}")


def pruebas_de_bag(esquema):
    import shutil
    import tempfile
    from componer_registro import componer, leer_bag

    tmp = tempfile.mkdtemp(prefix="prueba_rf25_")
    try:
        ruta = os.path.join(tmp, "bag_b")
        bag_sintetico(ruta)

        topicos = leer_bag(ruta)
        check("el bag sintetico trae estado_mision",
              len(topicos.get("/coordinacion/estado_mision", [])) == 5)

        reg = componer(ruta, banco="simulacion", campana="prueba",
                       error_posicion_m=0.19, rtf=0.995)
        check("el registro compuesto valida contra el esquema",
              valida(reg, esquema), _por_que(reg, esquema))
        check("saca la condicion B del propio bag",
              reg["mision"]["condicion"] == "B")
        check("t_inicio_tramo2 sale del odom del segundo robot",
              abs(reg["marcas"]["t_inicio_tramo2"] - 41.5) < 1e-6,
              f"-> {reg['marcas']['t_inicio_tramo2']}")
        check("el mision_id sale del bag, no del nombre del directorio",
              reg["mision"]["mision_id"] == "S24_B_prueba")
        check("origen y destino salen de EstadoMision, que el goal no graba",
              reg["solicitud"]["origen_id"] == "piso1_escalera"
              and reg["solicitud"]["nivel_destino"] == 2)

        # --- El error de llegada se calcula solo en simulacion --------------
        # En simulacion hay oraculo: /odom es la WorldPose de Gazebo. Dejar este
        # campo en null obligaba a teclear a mano la cifra que el bag ya trae, y
        # sin el campo el veredicto entero sale null: c1_posicion es el criterio
        # que decide el exito de la mision (§3.3 del protocolo).
        auto = componer(ruta, banco="simulacion", campana="prueba", rtf=0.995)
        e = auto["verdad_de_terreno"]["error_posicion_m"]
        check("en simulacion el error de llegada se calcula sin pasarlo",
              e is not None and abs(e - 0.19) < 1e-6, f"-> {e}")
        check("y con el, el veredicto deja de salir en null",
              auto["veredicto"]["c1_posicion"] is True
              and auto["veredicto"]["exito"] is True,
              f"-> {auto['veredicto']}")
        check("la pose de llegada es la del instante de COMPLETADA, "
              "no la ultima muestra del bag",
              abs(auto["verdad_de_terreno"]["pose_final"]["x"] + 21.31) < 1e-6,
              f"-> {auto['verdad_de_terreno']['pose_final']}")
        check("y es la del robot ACTIVO al final, no la del que publico ultimo",
              abs(auto["verdad_de_terreno"]["pose_final"]["y"] + 9.03) < 1e-6,
              f"-> {auto['verdad_de_terreno']['pose_final']}")
        check("el registro con el error calculado sigue validando",
              valida(auto, esquema), _por_que(auto, esquema))

        # Pasarlo a mano gana: permite rehacer un registro con una medida
        # revisada sin tocar el bag.
        manual = componer(ruta, banco="simulacion", campana="prueba",
                          error_posicion_m=1.5, rtf=0.995)
        check("un error pasado a mano no lo pisa el calculado",
              manual["verdad_de_terreno"]["error_posicion_m"] == 1.5,
              f"-> {manual['verdad_de_terreno']['error_posicion_m']}")

        # En el carro NO hay oraculo: la unica odometria es rf2o, que el 26-ago
        # registro el 5,7 % del desplazamiento real. Calcular el error con ella
        # seria llamar verdad de terreno a rf2o, que es lo que §4.4 prohibe.
        fisico = componer(ruta, banco="fisico", campana="prueba", rtf=0.995)
        check("en fisico el error sigue pendiente de cinta",
              fisico["verdad_de_terreno"]["error_posicion_m"] is None
              and fisico["veredicto"]["c1_posicion"] is None,
              f"-> {fisico['verdad_de_terreno']['error_posicion_m']}")

        # La condicion es la variable independiente del experimento y NO puede
        # salir de las etapas que llegaron a ocurrir: una mision entre pisos que
        # falla antes de planificar no tiene TRANSFERENCIA ni TRAMO_2 en el bag,
        # y contarla como A fallida falsea las dos tasas de exito a la vez.
        ruta_corta = os.path.join(tmp, "bag_b_truncado")
        bag_sintetico_truncado(ruta_corta)
        corto = componer(ruta_corta, banco="simulacion", campana="prueba",
                         error_posicion_m=None, rtf=0.995)
        check("una B que falla antes del relevo sigue siendo B",
              corto["mision"]["condicion"] == "B",
              f"-> {corto['mision']['condicion']}")
        check("y su registro tambien valida", valida(corto, esquema),
              _por_que(corto, esquema))

        # RF-24 de extremo a extremo: del bag al campo del registro, sin que
        # nadie lo rellene a mano. Es lo que el esquema 1.0.0 no tenia.
        c = auto["veredicto"]["continuidad"]
        check("el registro compuesto trae la continuidad calculada",
              c["continua"] is True and c["ventana"] is not None, f"-> {c}")
        check("la continuidad no toco el exito, que se decide con el §3.3",
              auto["veredicto"]["exito"] is True)
        check("el compositor escribe la version 1.1.0",
              auto["esquema_version"] == "1.1.0",
              f"-> {auto['esquema_version']}")
        # La B truncada no llega a COMPLETADA: la ventana no se cierra y la
        # continuidad es null. Es el caso que distingue 'no termino' de 'se
        # quedo sin nadie a cargo'; el primero ya lo cuenta c2, y contarlo dos
        # veces inflaria el recuento de discontinuidades de RF-24.
        cc = corto["veredicto"]["continuidad"]
        check("una B que no llega a COMPLETADA da continuidad null, no false",
              cc["continua"] is None and cc["motivo"] != "", f"-> {cc}")
        check("y esa mision si es un fallo por c2, que es lo que la describe",
              corto["veredicto"]["c2_completada_sin_fallida"] is False)

        # --- El residuo de la mision anterior no puede firmar este registro ---
        # El coordinador republica a 1 Hz el estado TERMINAL de la mision previa
        # hasta que llega una solicitud nueva, asi que el bag de una mision
        # empieza legitimamente con mensajes de OTRA. Esos van PRIMEROS en el
        # tiempo, que es de donde el compositor saca origen, destino y
        # t_solicitud.
        #
        # Esta prueba existe por dos defectos reales, no por precaucion:
        #   - 2026-08-29, componiendo S20_A_M2: sin filtrar, el registro se
        #     llevaba el origen y el destino de M1 y habria VALIDADO siendo
        #     falso.
        #   - 2026-08-29, recomponiendo el mismo bag: el mision_id salia de
        #     'ids.pop()' sobre el conjunto sin filtrar, y '.pop()' de un set
        #     devuelve un elemento ARBITRARIO. La misma orden escribia un id u
        #     otro segun el orden de iteracion, con las marcas siempre las de
        #     M2: un registro incoherente, no repetible, y que validaba.
        ruta_res = os.path.join(tmp, "bag_con_residuo")
        bag_con_residuo(ruta_res)
        res = componer(ruta_res, banco="simulacion", campana="prueba",
                       rtf=0.995)
        check("el mision_id es el de la mision del bag, no el del residuo",
              res["mision"]["mision_id"] == "S20_actual",
              f"-> {res['mision']['mision_id']}")
        check("origen y destino tampoco los pone el residuo",
              res["solicitud"]["origen_id"] == "piso1_representacion"
              and res["solicitud"]["destino_id"] == "piso1_etm2",
              f"-> {res['solicitud']['origen_id']} -> "
              f"{res['solicitud']['destino_id']}")
        check("t_solicitud es de esta mision, no de la anterior",
              res["marcas"]["t_solicitud"] is not None
              and res["marcas"]["t_solicitud"] > 100.0,
              f"-> {res['marcas']['t_solicitud']}")
        check("y el registro con residuo valida", valida(res, esquema),
              _por_que(res, esquema))

        # §4.2: el compositor falla ruidosamente, nunca inventa. Un bag ilegible
        # y una mision sin eventos NO pueden verse igual.
        vacio = os.path.join(tmp, "no_es_un_bag")
        os.makedirs(vacio)
        try:
            leer_bag(vacio)
            ok = False
        except Exception:
            ok = True
        check("un bag ilegible levanta excepcion en vez de devolver vacio", ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def bag_sintetico_truncado(ruta):
    """La misma mision entre pisos, cortada en el tramo 1 por un FALLIDA.

    Nunca llega a TRANSFERENCIA ni a TRAMO_2, que es justo el caso en el que
    clasificar por etapas la llamaria condicion A.
    """
    import rclpy.serialization
    import rosbag2_py
    from coordinacion_msgs.msg import EstadoMision
    from rosgraph_msgs.msg import Clock

    escritor = rosbag2_py.SequentialWriter()
    escritor.open(
        rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
        rosbag2_py.ConverterOptions("", ""))
    for nombre, tipo in [("/coordinacion/estado_mision", "coordinacion_msgs/msg/EstadoMision"),
                         ("/clock", "rosgraph_msgs/msg/Clock")]:
        escritor.create_topic(rosbag2_py.TopicMetadata(
            name=nombre, type=tipo, serialization_format="cdr"))
    escritor.write("/clock", rclpy.serialization.serialize_message(Clock()), 0)
    for t, etapa, robot in [(10.0, INACTIVA, ""), (10.2, TRAMO_1, "robot1"),
                            (22.0, FALLIDA, "robot1")]:
        m = EstadoMision()
        m.mision_id, m.etapa, m.robot_activo = "S24_B_truncada", etapa, robot
        m.origen_id, m.destino_id = "piso1_escalera", "piso2_escalera"
        escritor.write("/coordinacion/estado_mision",
                       rclpy.serialization.serialize_message(m), int(t * 1e9))
    del escritor


def bag_con_residuo(ruta):
    """Un bag que empieza con la cola TERMINAL de la mision anterior.

    Reproduce la forma exacta de S20_A_M2: once republicaciones de una
    'S20_previa' ya COMPLETADA, con SU origen y SU destino, y solo despues la
    mision que este bag si contiene. Los dos pares origen/destino son distintos
    a proposito: si el residuo se colara, se veria en el campo, no solo en el id.
    """
    import rclpy.serialization
    import rosbag2_py
    from coordinacion_msgs.msg import EstadoMision
    from rosgraph_msgs.msg import Clock

    escritor = rosbag2_py.SequentialWriter()
    escritor.open(
        rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
        rosbag2_py.ConverterOptions("", ""))
    for nombre, tipo in [("/coordinacion/estado_mision", "coordinacion_msgs/msg/EstadoMision"),
                         ("/clock", "rosgraph_msgs/msg/Clock")]:
        escritor.create_topic(rosbag2_py.TopicMetadata(
            name=nombre, type=tipo, serialization_format="cdr"))
    escritor.write("/clock", rclpy.serialization.serialize_message(Clock()), 0)

    def estado(t, mid, etapa, robot, origen, destino):
        m = EstadoMision()
        m.mision_id, m.etapa, m.robot_activo = mid, etapa, robot
        m.origen_id, m.destino_id = origen, destino
        escritor.write("/coordinacion/estado_mision",
                       rclpy.serialization.serialize_message(m), int(t * 1e9))

    # El residuo: la mision anterior, ya terminada, republicada a 1 Hz.
    for i in range(11):
        estado(10.0 + i, "S20_previa", COMPLETADA, "robot2",
               "piso2_ieee", "piso2_lab_313")
    # Y la mision de este bag, con otro origen, otro destino y otro robot.
    estado(120.0, "", INACTIVA, "", "", "")
    estado(120.5, "S20_actual", TRAMO_1, "robot1",
           "piso1_representacion", "piso1_etm2")
    estado(140.0, "S20_actual", FALLIDA, "robot1",
           "piso1_representacion", "piso1_etm2")
    del escritor


def _por_que(registro, esquema):
    """El motivo del rechazo, para no tener que adivinarlo desde un 'FALLA'."""
    try:
        jsonschema.validate(registro, esquema)
        return ""
    except jsonschema.ValidationError as e:
        return f"-> {'/'.join(str(p) for p in e.absolute_path)}: {e.message}"


def main():
    with open(ESQUEMA, encoding="utf-8") as f:
        esquema = json.load(f)
    print("Esquema del registro de mision")
    pruebas_de_esquema(esquema)
    print("Orden de las marcas (no cabe en draft-07)")
    pruebas_de_orden()
    print("Marcas y veredicto")
    pruebas_de_marcas()
    print("Continuidad entre niveles (RF-24)")
    pruebas_de_continuidad()
    print("Lectura del bag y ensamblado (necesita el workspace sourceado)")
    pruebas_de_bag(esquema)
    print(f"\n{len(fallos)} fallo(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
