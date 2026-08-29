#!/usr/bin/env python3
"""Compone el registro de una mision a partir de su bag. Ver
Documentos/ESQUEMA_REGISTRO_MISION.md.

No corre durante la mision, y eso es deliberado: RNF-06 exige RTF >= 0,99 y un
registrador serializando a 50 Hz compite por la CPU con dos Gazebo en el mismo
equipo. El bag sigue siendo la fuente; esto solo lo lee.

Este archivo no importa rclpy ni coordinacion_msgs a proposito, por la misma
razon que planificador.py: las reglas que convierten un bag en un veredicto se
agotan con pytest en milisegundos.

PERO OJO, Y AQUI ESTE ENCABEZADO MENTIA: no importarlos ARRIBA no es lo mismo
que no necesitarlos. Deserializar el bag pasa por rosidl_runtime_py, que
importa coordinacion_msgs de forma dinamica, asi que EJECUTAR esto si exige el
workspace compilado y sourceado aunque LEER el codigo no lo sugiera. Se
comprobo el 2026-08-29: con solo /opt/ros/humble sourceado, la herramienta
muere con 'ModuleNotFoundError: No module named coordinacion_msgs'. Lo que si
es cierto es que las funciones puras -las que deciden marcas y veredicto- se
prueban sin nada de eso, y eso es lo que cubre prueba_componer_registro.py.

    source ~/deepracer_sim_ws/install/setup.bash
"""

import argparse
import json
import math
import os
import sys

# Constantes de EstadoMision.msg. Se copian a proposito en vez de importar
# coordinacion_msgs: esta herramienta tiene que poder correr sobre un bag sin
# el workspace compilado.
INACTIVA, TRAMO_1, TRANSFERENCIA, TRAMO_2, COMPLETADA, FALLIDA = 0, 1, 2, 3, 4, 5

UMBRAL_MOVIMIENTO_MS = 0.02
MUESTRAS_CONSECUTIVAS = 3
TOLERANCIA_LLEGADA_M = 0.25   # la misma de coordinador.py y del §5 del protocolo
ESQUEMA_VERSION = "1.0.0"


def primer_movimiento(muestras, umbral=UMBRAL_MOVIMIENTO_MS,
                      consecutivas=MUESTRAS_CONSECUTIVAS):
    """Instante del primer movimiento sostenido, o None si el robot nunca arranco.

    'muestras' es una lista de (t, vx, vy) ordenada por t.

    Se exigen TRES muestras seguidas por encima del umbral, y se devuelve el
    instante de la PRIMERA de las tres. Un pico aislado de ruido del estimador
    adelantaria la marca y t_respuesta saldria mas corto de lo que fue.
    """
    seguidas = 0
    for i, (t, vx, vy) in enumerate(muestras):
        if math.hypot(vx, vy) >= umbral:
            seguidas += 1
            if seguidas == consecutivas:
                return muestras[i - consecutivas + 1][0]
        else:
            seguidas = 0
    return None


def desde(muestras, t0):
    """Las muestras a partir de t0. Sin t0, todas.

    HACE FALTA, y no es una precaucion teorica. El bag empieza a grabar ANTES de
    que se pida la mision: primero se lanza grabar_mision.sh y despues se pide
    el destino por la HRI. Cualquier movimiento del robot durante esa puesta a
    punto -recolocarlo, un empujon, ruido de rf2o en el banco fisico- daria un
    t_primer_movimiento ANTERIOR a t_solicitud, y t_respuesta, que es
    't_primer_movimiento - t_solicitud' y es una metrica de OE4, saldria
    negativa.

    Lo mismo con el segundo robot y el hueco de relevo: robot2 esta parado
    durante todo el tramo 1, pero sus muestras de /odom se graban igual.
    """
    if t0 is None:
        return list(muestras)
    return [m for m in muestras if m[0] >= t0]


def _primero(estados, predicado):
    """Instante del primer estado que cumple el predicado, o None."""
    for t, etapa, robot, _ in estados:
        if predicado(etapa, robot):
            return t
    return None


def marcas_de(estados, movimientos, condicion):
    """Las siete marcas de la §3.5, en segundos del mismo reloj.

    'estados'     lista de (t, etapa, robot_activo, mision_id) ordenada por t.
    'movimientos' {robot: [(t, vx, vy), ...]}.
    'condicion'   'A' o 'B'.

    Una marca va None cuando el evento no ocurrio, sea porque la condicion no lo
    contempla o porque la mision termino antes de llegar a el. Los dos casos se
    distinguen leyendo 'condicion' y el veredicto, no la marca.
    """
    t_solicitud = _primero(estados, lambda e, r: e != INACTIVA)
    t_robot_activo = _primero(estados, lambda e, r: e == TRAMO_1 and r)

    robot_1 = next((r for _, e, r, _ in estados if e == TRAMO_1 and r), None)
    robot_2 = next((r for _, e, r, _ in estados if e == TRAMO_2 and r), None)

    m = {
        "reloj": "/clock",
        "t_solicitud": t_solicitud,
        "t_robot_activo": t_robot_activo,
        # Solo cuenta el movimiento posterior a la solicitud. Ver desde().
        "t_primer_movimiento": primer_movimiento(
            desde(movimientos.get(robot_1, []), t_solicitud)),
        "t_fin_tramo1": None,
        "t_inicio_tramo2": None,
        "t_completada": _primero(estados, lambda e, r: e == COMPLETADA),
    }
    if condicion == "B":
        t_fin_tramo1 = _primero(estados, lambda e, r: e == TRANSFERENCIA)
        m["t_fin_tramo1"] = t_fin_tramo1
        # Y aqui, solo el movimiento posterior al fin del tramo 1: si no, el
        # hueco de relevo podria salir negativo.
        m["t_inicio_tramo2"] = primer_movimiento(
            desde(movimientos.get(robot_2, []), t_fin_tramo1))
    return m


def marcas_en_orden(marcas):
    """True si las marcas presentes van en orden creciente.

    JSON Schema draft-07 NO puede comparar dos campos entre si, asi que la regla
    't_fin_tramo1 <= t_inicio_tramo2' de la §4.3 no cabe en el esquema y hay que
    comprobarla aparte. Las marcas ausentes se saltan: una condicion A valida
    tiene dos huecos en mitad de la secuencia.
    """
    secuencia = ["t_solicitud", "t_robot_activo", "t_primer_movimiento",
                 "t_fin_tramo1", "t_inicio_tramo2", "t_completada"]
    vistos = [marcas[k] for k in secuencia if marcas.get(k) is not None]
    return all(a <= b for a, b in zip(vistos, vistos[1:]))


def veredicto_de(marcas, estados, error_posicion_m, condicion, num_relevos):
    """Las tres condiciones del §3.3 del protocolo, por separado.

    Se guardan sueltas y no solo su AND porque si la tasa de exito sale baja hay
    que poder decir CUAL fallo. Con R3 abierto se espera exactamente eso: c1 en
    rojo con c2 y c3 en verde, que es un diagnostico. Un 'exito: false' suelto
    no lo es.

    error_posicion_m None significa 'pendiente de medir' (§4.4, banco fisico):
    entonces c1 y exito van None y el analizador rechaza el registro. No se
    inventa un veredicto.
    """
    c1 = None if error_posicion_m is None else error_posicion_m <= TOLERANCIA_LLEGADA_M
    hubo_fallida = any(e == FALLIDA for _, e, _, _ in estados)
    c2 = marcas["t_completada"] is not None and not hubo_fallida
    c3 = (num_relevos == 1) if condicion == "B" else None

    condiciones = [c1, c2] + ([c3] if condicion == "B" else [])

    # Logica de tres valores, no 'si c1 es None todo es None'. La version
    # anterior colapsaba dos situaciones que no son la misma:
    #
    #   - banco fisico, falta pasar la cinta -> c1 desconocido, y el veredicto
    #     tiene que esperar. Ese es el caso que la §4.4 quiere proteger.
    #   - la mision nunca llego -> c1 es None porque NO HAY pose de llegada que
    #     medir, no porque este pendiente. Aqui c2 ya es False.
    #
    # En el segundo caso 'None' es un veredicto equivocado: falso Y desconocido
    # es falso, se mida lo que se mida despues. Salio el 2026-08-29 con la
    # mision S20_A_M2, que aborto sin moverse: el coordinador devolvio
    # exito=false y el registro decia null, que es peor que un error, porque un
    # fallo limpio se contaba como dato incompleto.
    #
    # Un desconocido solo sobrevive si NADA es falso.
    if any(c is False for c in condiciones):
        exito = False
    elif any(c is None for c in condiciones):
        exito = None
    else:
        exito = True

    motivo = ""
    if exito is False:
        partes = []
        if c1 is False:
            partes.append(f"llegada a {error_posicion_m:.3f} m, fuera de "
                          f"{TOLERANCIA_LLEGADA_M} m")
        if not c2:
            partes.append("la mision no llego a COMPLETADA sin pasar por FALLIDA")
        if condicion == "B" and c3 is False:
            partes.append(f"{num_relevos} relevo(s), se esperaba 1")
        motivo = "; ".join(partes)

    return {"exito": exito, "c1_posicion": c1, "c2_completada_sin_fallida": c2,
            "c3_relevo": c3, "motivo_fallo": motivo}


# --- Lectura del bag --------------------------------------------------------

def leer_bag(ruta):
    """{topico: [(t_segundos, mensaje), ...]} de todo el bag.

    Levanta excepcion si el bag no se puede abrir. No devuelve un diccionario
    vacio: un bag ilegible y una mision sin eventos se verian igual, y §4.2 dice
    que el compositor falla ruidosamente antes que inventar.

    Los import de ROS estan DENTRO de la funcion, no arriba: asi las pruebas de
    las marcas y del esquema siguen corriendo sin el workspace sourceado.
    """
    import rclpy.serialization
    import rosbag2_py
    from rosidl_runtime_py.utilities import get_message

    lector = rosbag2_py.SequentialReader()
    lector.open(rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
                rosbag2_py.ConverterOptions("", ""))
    tipos = {t.name: t.type for t in lector.get_all_topics_and_types()}

    salida = {}
    while lector.has_next():
        topico, datos, t_ns = lector.read_next()
        try:
            clase = get_message(tipos[topico])
        except (ImportError, ModuleNotFoundError) as e:
            # El traceback crudo de aqui apunta a importlib y no dice nada util:
            # el lector cree que su bag esta corrupto cuando lo unico que pasa
            # es que falta el overlay. Los tipos propios del proyecto no estan
            # en /opt/ros, asi que este es el fallo mas probable de todos.
            raise SystemExit(
                f"No se puede resolver el tipo '{tipos[topico]}' del topico "
                f"{topico} ({e}).\n"
                f"El bag esta bien; lo que falta es el workspace donde vive ese "
                f"mensaje. Sourcearlo y repetir:\n"
                f"  source ~/deepracer_sim_ws/install/setup.bash")
        msg = rclpy.serialization.deserialize_message(datos, clase)
        salida.setdefault(topico, []).append((t_ns * 1e-9, msg))
    return salida


def _condicion(nivel_origen, nivel_destino, etapas):
    """'A' dentro de un nivel, 'B' entre niveles. Es la §3.1.

    Sale de los NIVELES del catalogo, no de las etapas que llegaron a ocurrir.
    Una mision entre pisos que falla antes de planificar no tiene TRANSFERENCIA
    ni TRAMO_2 en el bag: clasificarla por etapas la contaria como una A
    fallida, y eso falsea las DOS tasas de exito a la vez -A pierde una que no
    era suya, B se guarda su peor caso-. La condicion es la variable
    independiente del experimento; se decide por lo que se PIDIO.

    Las etapas quedan de reserva para cuando alguno de los dos puntos no este en
    el catalogo, que es el unico caso en el que no hay niveles que comparar.
    """
    if nivel_origen is not None and nivel_destino is not None:
        return "B" if nivel_origen != nivel_destino else "A"
    return "B" if (TRANSFERENCIA in etapas or TRAMO_2 in etapas) else "A"


def componer(ruta_bag, banco, campana, error_posicion_m=None, rtf=None,
             semilla=None, es_piloto=False, medido_por="automatico",
             distro=None, mundo=None, mapa=None):
    """Construye el registro completo. Ver la §3 del esquema."""
    topicos = leer_bag(ruta_bag)

    crudos = topicos.get("/coordinacion/estado_mision", [])
    if not crudos:
        raise SystemExit(
            f"{ruta_bag} no contiene /coordinacion/estado_mision. Sin el no hay "
            f"marcas, y un registro con marcas en null seria indistinguible de "
            f"una mision que fallo. Grabar con herramientas/grabar_mision.sh.")

    # --- De que mision es este bag ------------------------------------------
    # Un bag puede traer mensajes de DOS misiones sin que el procedimiento se
    # haya roto. El coordinador no se calla al terminar: sigue publicando el
    # estado terminal de la mision anterior hasta que llega una nueva
    # solicitud, asi que si dos misiones comparten sesion, el bag de la segunda
    # arranca con la cola de la primera. Medido el 2026-08-29 en S20_A_M2: 11
    # mensajes de la mision de las 18:13, TODOS en etapa COMPLETADA, antes de
    # los 34 propios.
    #
    # Y NO ES COSMETICO. Esos 11 mensajes van PRIMERO en el tiempo, asi que sin
    # filtrar se llevaban por delante el registro entero: 'origen' y 'destino'
    # se resuelven con el primer mensaje que los traiga -habrian salido los de
    # la mision anterior- y t_solicitud es el primer estado distinto de
    # INACTIVA, que habria caido diez segundos antes de que esta mision
    # existiera. El registro habria validado contra el esquema y habria sido
    # falso.
    #
    # La distincion que se usa: una mision de la que solo hay estados
    # TERMINALES no ocurrio dentro de este bag, es un residuo. Una con algun
    # estado en curso si. Dos en curso siguen siendo un procedimiento roto.
    TERMINALES = (COMPLETADA, FALLIDA)
    en_curso = {m.mision_id for _, m in crudos
                if m.mision_id and m.etapa not in TERMINALES}
    ids = {m.mision_id for _, m in crudos if m.mision_id}

    if len(en_curso) > 1:
        raise SystemExit(
            f"{ruta_bag} contiene {len(en_curso)} misiones en curso: "
            f"{sorted(en_curso)}. El §6.4 del protocolo manda un gzserver por "
            f"corrida, asi que esto significa que el procedimiento no se siguio.")
    if not en_curso and len(ids) > 1:
        raise SystemExit(
            f"{ruta_bag} solo trae estados terminales, de {len(ids)} misiones: "
            f"{sorted(ids)}. La grabacion empezo despues de que terminaran y no "
            f"hay ninguna marca que componer.")

    mision_del_bag = next(iter(en_curso), next(iter(ids), ""))
    residuo = sorted(ids - {mision_del_bag})
    if residuo:
        print(f"AVISO: se descartan los estados residuales de {residuo}, que "
              f"terminaron antes de que empezara este bag. La mision de "
              f"{ruta_bag} es {mision_del_bag}.", file=sys.stderr)
        # El mision_id vacio es el preludio INACTIVA del coordinador, y se
        # conserva: de el sale que la mision no empezo antes de la solicitud.
        crudos = [(t, m) for t, m in crudos
                  if m.mision_id in ("", mision_del_bag)]

    if banco == "simulacion" and "/clock" not in topicos:
        raise SystemExit(f"{ruta_bag} no trae /clock y el banco es simulacion.")

    estados = [(t, m.etapa, m.robot_activo, m.mision_id) for t, m in crudos]
    etapas = {e for _, e, _, _ in estados}

    niveles = _niveles_del_catalogo()
    origen = next((m.origen_id for _, m in crudos if m.origen_id), "")
    destino = next((m.destino_id for _, m in crudos if m.destino_id), "")
    condicion = _condicion(niveles.get(origen), niveles.get(destino), etapas)

    # Dos vistas del mismo /odom: 'movimientos' es lo que decide las marcas y
    # 'poses' lo que va a la verdad de terreno y a la traza.
    movimientos, poses = {}, {}
    for topico, muestras in topicos.items():
        if topico.endswith("/odom"):
            ns = topico.strip("/").split("/")[0]
            movimientos[ns] = [(t, m.twist.twist.linear.x, m.twist.twist.linear.y)
                               for t, m in muestras]
            poses[ns] = [(t, m.pose.pose.position.x, m.pose.pose.position.y,
                          _yaw_de(m.pose.pose.orientation)) for t, m in muestras]

    marcas = marcas_de(estados, movimientos, condicion)
    # 'is not None' y no truthiness: un t_inicio_tramo2 de 0,0 s es una marca
    # valida, y con 'if marcas[...]' contaria como que no hubo relevo.
    relevos = 1 if condicion == "B" and marcas["t_inicio_tramo2"] is not None else 0

    # En simulacion el error de llegada NO se teclea: /odom es la WorldPose de
    # Gazebo y el catalogo da el punto, asi que el bag ya lo contiene. Dejarlo en
    # null obligaba a copiarlo a mano de la consola del coordinador -o a
    # olvidarlo, que es lo que paso con S20_piloto_03- y sin el campo el
    # veredicto entero sale null: c1_posicion es el criterio que decide el exito.
    #
    # Se respeta el valor pasado a mano. En el banco fisico es la lectura de
    # cinta y no hay alternativa; en simulacion permite rehacer un registro con
    # una medida revisada sin tener que tocar el bag.
    pose_llegada, nota = _pose_llegada(poses, _robot_final(estados),
                                       marcas["t_completada"])
    if banco == "simulacion" and error_posicion_m is None:
        error_posicion_m = _error_de_llegada(pose_llegada, destino)

    veredicto = veredicto_de(marcas, estados, error_posicion_m, condicion, relevos)

    return {
        "esquema_version": ESQUEMA_VERSION,
        "mision": {
            "mision_id": ids.pop() if ids else os.path.basename(ruta_bag),
            "campana": campana, "banco": banco, "condicion": condicion,
            "semilla": semilla, "es_piloto": es_piloto,
        },
        "procedencia": _procedencia(ruta_bag, distro, mundo, mapa),
        "solicitud": _solicitud(crudos, condicion, niveles, origen, destino),
        "marcas": marcas,
        "verdad_de_terreno": _verdad(banco, error_posicion_m, pose_llegada,
                                     medido_por, nota),
        "veredicto": veredicto,
        "descriptivas": _descriptivas(banco, topicos, poses, marcas),
        "salud_del_banco": _salud(banco, rtf),
        "traza": _traza(ruta_bag, poses),
    }


def _yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


# --- Los bloques del registro, uno por funcion ------------------------------

def _raiz():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _catalogo():
    return os.path.join(_raiz(), "Robot", "aws-deepracer", "deepracer_bringup",
                        "config", "puntos_interes.yaml")


def _git(*args):
    import subprocess
    try:
        return subprocess.run(("git", "-C", _raiz()) + args, check=True,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def _procedencia(ruta_bag, distro=None, mundo=None, mapa=None):
    """De donde salio esta medida. Sin esto no se puede reproducir en S26."""
    import hashlib
    with open(_catalogo(), "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    # El bag NO guarda la distro: metadata.yaml de rosbag2 en Humble va por la
    # version 5 y no trae ese campo. Asi que se toma del entorno, con la trampa
    # de que el entorno es el de QUIEN COMPONE, no el de quien grabo: un bag del
    # carro -Jazzy- compuesto en el PC saldria etiquetado 'humble'. Para eso
    # esta --distro. Y si no hay ninguna, se para: el §4.2 dice que antes que
    # inventar, el compositor falla.
    distro = distro or os.environ.get("ROS_DISTRO", "")
    if distro not in ("humble", "jazzy"):
        raise SystemExit(
            f"ROS_DISTRO vale '{distro}', y el esquema solo admite humble o "
            f"jazzy. Sourcear ROS, o pasar --distro si se esta componiendo en "
            f"el PC un bag grabado en el carro.")

    return {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "etiqueta": _git("describe", "--tags", "--exact-match"),
        # Una medida tomada con cambios sin comitear no se puede reproducir. Que
        # lo diga el registro es mejor que descubrirlo en S26.
        "repositorio_limpio": _git("status", "--porcelain") == "",
        "distro": distro,
        # Nadie exportaba TESIS_MUNDO ni TESIS_MAPA, asi que estos dos campos
        # salian en blanco y el esquema los daba por buenos: son 'string' sin
        # minLength. Un registro sin mundo ni mapa no se puede reproducir en
        # S26, que es justo para lo que existe esta seccion. Ahora se avisa, y
        # se pueden pasar por --mundo/--mapa. Los dos primeros registros, los
        # del 2026-08-29, se compusieron leyendolos del sistema vivo:
        # 'pgrep -a gzserver' para el mundo y 'ros2 param get /<ns>/map_server
        # yaml_filename' para el mapa.
        "mundo": mundo or os.environ.get("TESIS_MUNDO", ""),
        "mapa": mapa or os.environ.get("TESIS_MAPA", ""),
        "catalogo_puntos": "puntos_interes.yaml",
        # Las poses del catalogo se movieron tres veces en agosto. Un registro
        # que no lo fije no se puede comparar con otro: 'ETM1' puede no ser el
        # mismo punto.
        "catalogo_sha256": sha,
        "bag": os.path.basename(os.path.normpath(ruta_bag)),
        "fecha_utc": _fecha_del_bag(ruta_bag),
    }


def _fecha_del_bag(ruta_bag):
    import datetime
    t = os.path.getmtime(ruta_bag)
    return datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%dT%H:%M:%SZ")


def _puntos_del_catalogo():
    import yaml
    with open(_catalogo(), encoding="utf-8") as f:
        return yaml.safe_load(f)["puntos"]


def _niveles_del_catalogo():
    return {p["id"]: int(p["nivel"]) for p in _puntos_del_catalogo()}


def _poses_del_catalogo():
    return {p["id"]: (float(p["pose"]["x"]), float(p["pose"]["y"]))
            for p in _puntos_del_catalogo()}


def _robot_final(estados):
    """Quien llevaba al usuario al final de la mision.

    En condicion B NO es el mismo que al principio, y esa es toda la razon de que
    esto exista: robot1 se queda parado en el punto de transferencia publicando
    /odom hasta que el operador corta el bag, asi que puede perfectamente ser el
    ultimo en publicar. Preguntar 'que muestra de /odom es la mas tardia' devuelve
    entonces la pose de un robot que no llego a ningun sitio.
    """
    for _, _, robot, _ in reversed(estados):
        if robot:
            return robot
    return ""


def _pose_llegada(poses, robot, t_completada):
    """La pose con la que se juzga la llegada, y el instante del que sale.

    Se toma en t_completada y NO al final del bag. El bag sigue grabando hasta
    que alguien pulsa Ctrl-C, asi que la ultima muestra puede estar minutos
    despues de la llegada y a metros de ella -si al robot lo movieron, o si
    siguio corrigiendo-. Medir alli haria que el error de llegada dependiera de
    la mano del operador, y con 15 corridas por condicion en S24 eso no es un
    detalle: es una fuente de dispersion que no esta en el experimento.

    Sin t_completada -mision fallida- no hay instante de llegada, y entonces si
    se usa la ultima muestra: es cuanto se acerco antes de rendirse.
    """
    muestras = poses.get(robot) or []
    if not muestras:
        return None, ""
    if t_completada is None:
        t, x, y, yaw = muestras[-1]
        return ({"x": x, "y": y, "yaw": yaw},
                f"mision sin t_completada: pose de la ultima muestra de {robot} "
                f"(t={t:.3f} s)")
    previas = [m for m in muestras if m[0] <= t_completada]
    t, x, y, yaw = (previas or muestras)[-1]
    return ({"x": x, "y": y, "yaw": yaw},
            f"pose de {robot} en t={t:.3f} s, la ultima antes de "
            f"t_completada={t_completada:.3f} s")


def _error_de_llegada(pose_llegada, destino_id):
    """A cuantos metros del punto pedido se quedo el robot.

    Solo tiene sentido en simulacion, donde /odom es la WorldPose de Gazebo. El
    catalogo da las coordenadas del punto en el mismo marco.
    """
    if pose_llegada is None:
        return None
    objetivo = _poses_del_catalogo().get(destino_id)
    if objetivo is None:
        return None
    return math.hypot(pose_llegada["x"] - objetivo[0],
                      pose_llegada["y"] - objetivo[1])


def _solicitud(crudos, condicion, niveles, origen, destino):
    """Que se pidio. Sale de EstadoMision, no del goal: los goals no se graban."""
    tramos = []
    vistos = set()
    for _, m in crudos:
        clave = (m.etapa, m.destino_actual.id)
        if m.etapa in (TRAMO_1, TRAMO_2) and clave not in vistos:
            vistos.add(clave)
            tramos.append({"orden": len(tramos) + 1, "robot": m.robot_activo,
                           "punto_id": m.destino_actual.id, "etapa": int(m.etapa)})
    return {
        "origen_id": origen, "destino_id": destino,
        "nivel_origen": niveles.get(origen), "nivel_destino": niveles.get(destino),
        # Derivable de los dos niveles, y se guarda igual: el analizador no debe
        # rederivar la variable independiente del experimento.
        "entre_niveles": condicion == "B",
        "tramos": tramos,
    }


def _verdad(banco, error_posicion_m, pose_llegada, medido_por, nota):
    """De donde sale la verdad de terreno, que NO es la misma en los dos bancos.

    En simulacion /odom es la pose exacta del motor de Gazebo -WorldPose(), ver
    gazebo_ros_deepracer_drive.cpp:229-, asi que es un oraculo y la
    incertidumbre es cero. En el carro la unica odometria es rf2o, que el 26-ago
    registro el 5,7 % del desplazamiento real: rellenar pose_final con ella
    seria volver a llamar verdad de terreno a rf2o.

    'nota' dice de que instante y de que robot sale la pose. Sin eso, quien lea
    el registro en octubre no puede distinguir una llegada medida en
    t_completada de una medida al final del bag, y son cifras distintas.
    """
    if banco == "fisico":
        return {"fuente": "cinta_metrica", "error_posicion_m": error_posicion_m,
                "pose_final": None, "incertidumbre_m": 0.01,
                "medido_por": medido_por, "nota": ""}
    return {
        "fuente": "gazebo_worldpose_via_odom",
        "error_posicion_m": error_posicion_m,
        "pose_final": pose_llegada,
        "incertidumbre_m": 0.0, "medido_por": "automatico", "nota": nota,
    }


def _descriptivas(banco, topicos, poses, marcas):
    """Se miden y se reportan; no deciden el exito. Ver §3.8 del esquema."""
    recorrido = 0.0
    desviacion = {}
    for ns, muestras in poses.items():
        for (_, x0, y0, _), (_, x1, y1, _) in zip(muestras, muestras[1:]):
            recorrido += math.hypot(x1 - x0, y1 - y0)
        # RNF-01: ningun robot cruza de nivel, lo que cruza es el mensaje.
        desviacion[ns] = max((abs(z) for z in _zetas(topicos, ns)), default=0.0)

    # R12: una cuspide es un cambio de sentido de la marcha. Se cuentan los
    # cambios de signo de cmd_vel.linear.x, ignorando el cero.
    cuspides = 0
    for topico, muestras in topicos.items():
        if topico.endswith("/cmd_vel"):
            signos = [_signo(m.linear.x) for _, m in muestras if _signo(m.linear.x)]
            cuspides += sum(1 for a, b in zip(signos, signos[1:]) if a != b)

    total = None
    if marcas["t_completada"] is not None and marcas["t_solicitud"] is not None:
        total = marcas["t_completada"] - marcas["t_solicitud"]

    return {
        # Presente y sin llenar en 1.0.0 a proposito: para calcularlo hace falta
        # el yaw del punto del catalogo, y el §3.7 dice que el rumbo NO decide
        # mientras R12 siga abierto. Llenarlo despues es una version menor.
        "error_rumbo_rad": None,
        "desviacion_z_m": desviacion,
        "distancia_recorrida_m": recorrido,
        "num_cuspides": cuspides,
        "tiempo_total_s": total,
        # La cifra que el 26-ago delato a AMCL. Con /odom publicado desde
        # WorldPose(), map->odom deberia ser CONSTANTE; derivo 1,977 m. Grabarla
        # en cada mision hace que la campana cuantifique R3 en vez de padecerlo.
        # En fisico va null: alli map->odom no es un error medible contra nada.
        "deriva_map_odom_m": None if banco == "fisico"
                             else _deriva_map_odom(topicos),
    }


def _signo(v):
    return 0 if abs(v) < 1e-3 else (1 if v > 0 else -1)


def _zetas(topicos, ns):
    return [m.pose.pose.position.z for _, m in topicos.get(f"/{ns}/odom", [])]


def _deriva_map_odom(topicos):
    """Cuanto se movio la transformada map->odom entre el principio y el final."""
    puntos = []
    for _, msg in topicos.get("/tf", []):
        for tr in msg.transforms:
            if tr.header.frame_id.endswith("map") and tr.child_frame_id.endswith("odom"):
                puntos.append((tr.transform.translation.x, tr.transform.translation.y))
    if len(puntos) < 2:
        return None
    return math.hypot(puntos[-1][0] - puntos[0][0], puntos[-1][1] - puntos[0][1])


def _salud(banco, rtf):
    """Para que un descarte sea demostrable. La causa la pone una persona
    despues, y solo puede ser una de las cuatro del §8 del protocolo: el esquema
    rechaza cualquier otra."""
    if banco == "fisico":
        return {"rtf": None, "controladores_activos": {},
                "gzserver_vivo_al_final": None, "descartada": False,
                "causa_descarte": None}
    return {"rtf": rtf, "controladores_activos": {},
            "gzserver_vivo_al_final": True, "descartada": False,
            "causa_descarte": None}


def _traza(ruta_bag, poses, hz=5.0):
    """Copia de conveniencia para graficar sin reabrir el bag. El bag sigue
    siendo la fuente: el 26-ago la medicion de rf2o se obtuvo metiendole el
    /scan de mision3 a un nodo que nunca corrio en esa mision, y ninguna traza
    diezmada habria permitido eso."""
    paso = 1.0 / hz
    puntos = []
    for ns, muestras in poses.items():
        siguiente = None
        for t, x, y, yaw in muestras:
            if siguiente is None or t >= siguiente:
                puntos.append({"t": t, "robot": ns, "x": x, "y": y, "yaw": yaw})
                # 't + paso' y no 'siguiente + paso': si el robot deja un hueco
                # de 30 s -esperando el relevo-, la segunda forma se queda
                # atrasada y luego cuela 150 muestras seguidas para recuperarlo.
                siguiente = t + paso
    puntos.sort(key=lambda p: p["t"])
    return {"bag": os.path.basename(os.path.normpath(ruta_bag)),
            "decimada_hz": hz, "puntos": puntos}


# --- Linea de ordenes -------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag")
    p.add_argument("--banco", choices=["simulacion", "fisico"], required=True)
    p.add_argument("--campana", required=True)
    p.add_argument("--error-posicion-m", type=float, default=None,
                   help="En fisico, la lectura de cinta. Sin el, el registro "
                        "queda pendiente de medir (§4.4) y el analizador lo "
                        "rechaza hasta que se rellene.")
    p.add_argument("--rtf", type=float, default=None,
                   help="Por omision se lee <bag>/rtf.json, que escribe "
                        "grabar_mision.sh midiendo /clock alrededor de la "
                        "ventana grabada. Pasarlo a mano solo deberia hacer "
                        "falta con bags anteriores al 2026-08-29, que no lo "
                        "traen; en ese caso el numero es de OTRA ventana y hay "
                        "que decirlo en el informe de evidencia, porque el "
                        "esquema no tiene campo para anotarlo.")
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--piloto", action="store_true")
    p.add_argument("--medido-por", default="automatico")
    p.add_argument("--distro", choices=["humble", "jazzy"], default=None,
                   help="Por omision, ROS_DISTRO. Hace falta al componer en el "
                        "PC un bag grabado en el carro.")
    p.add_argument("--mundo", default=None,
                   help="Ruta del .world. Si se omite se usa TESIS_MUNDO, y si "
                        "tampoco esta, el campo queda vacio y se avisa. Del "
                        "sistema vivo sale con 'pgrep -a gzserver'.")
    p.add_argument("--mapa", default=None,
                   help="Ruta del .yaml del mapa. Del sistema vivo sale con "
                        "'ros2 param get /<ns>/map_server yaml_filename'.")
    p.add_argument("--salida", required=True)
    a = p.parse_args()

    # El RTF sale del bag si esta ahi. Se prefiere lo medido durante la mision
    # sobre lo que se escriba en la linea de ordenes: el numero de rtf.json
    # cubre exactamente la ventana grabada, y uno tecleado a mano casi siempre
    # es de otro momento.
    rtf = a.rtf
    ruta_rtf = os.path.join(a.bag, "rtf.json")
    if os.path.exists(ruta_rtf):
        with open(ruta_rtf, encoding="utf-8") as f:
            medido = json.load(f)["rtf"]
        if a.rtf is not None and abs(a.rtf - medido) > 1e-6:
            print(f"AVISO: se ignora --rtf {a.rtf} y se usa el medido durante "
                  f"la mision, {medido} ({ruta_rtf}).", file=sys.stderr)
        rtf = medido
    elif a.banco == "simulacion" and a.rtf is None:
        raise SystemExit(
            f"Falta el RTF y el banco es 'simulacion', que el esquema exige con "
            f"RTF numerico (RNF-06 pide >= 0,99).\n"
            f"No hay {ruta_rtf}, y el bag NO puede darlo: con --use-sim-time "
            f"todos sus sellos son de tiempo de simulacion, incluidos "
            f"'starting_time' y 'duration', asi que sim/pared vale 1 por "
            f"construccion.\n"
            f"Si la simulacion que grabo este bag sigue viva, medirlo ahora con "
            f"'python3 herramientas/medir_rtf.py --segundos 20' y pasarlo con "
            f"--rtf, anotando en el informe que es posterior a la mision. "
            f"Si ya se cerro, el RTF de esa corrida se perdio.")

    registro = componer(a.bag, a.banco, a.campana, a.error_posicion_m, rtf,
                        a.semilla, a.piloto, a.medido_por, a.distro,
                        a.mundo, a.mapa)

    # El esquema acepta cadena vacia en estos dos -son 'string' a secas-, asi
    # que si no se avisa aqui el hueco no lo detecta nadie hasta S26, cuando ya
    # no se puede reconstruir de que mundo salio la medida.
    for campo in ("mundo", "mapa"):
        if not registro["procedencia"][campo]:
            print(f"AVISO: procedencia.{campo} queda vacio. El registro valida "
                  f"igual, pero no se podra reproducir. Pasarlo con --{campo}.",
                  file=sys.stderr)

    # Validar ANTES de escribir. Sin esto, 'congelado' es una promesa.
    import jsonschema
    with open(os.path.join(_raiz(), "Documentos",
                           "esquema_registro_mision.json"), encoding="utf-8") as f:
        jsonschema.validate(registro, json.load(f))

    # Y la parte de la §4.3 que el esquema NO puede comprobar, porque draft-07 no
    # sabe comparar dos campos entre si. Si no se llama aqui, marcas_en_orden()
    # existe para nada y un hueco de relevo negativo se escribe a disco tan
    # tranquilo, con el esquema dando el visto bueno.
    if not marcas_en_orden(registro["marcas"]):
        raise SystemExit(
            f"Las marcas no van en orden creciente: {registro['marcas']}\n"
            f"Un t_respuesta o un hueco de relevo negativos no son una medida, "
            f"son un sintoma. Revisar el bag antes de escribir el registro.")

    os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
    with open(a.salida, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=2, ensure_ascii=False)
    print(f"Registro escrito en {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
