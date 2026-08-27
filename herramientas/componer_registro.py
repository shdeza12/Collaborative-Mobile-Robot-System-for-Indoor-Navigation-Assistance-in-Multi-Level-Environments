#!/usr/bin/env python3
"""Compone el registro de una mision a partir de su bag. Ver
Documentos/ESQUEMA_REGISTRO_MISION.md.

No corre durante la mision, y eso es deliberado: RNF-06 exige RTF >= 0,99 y un
registrador serializando a 50 Hz compite por la CPU con dos Gazebo en el mismo
equipo. El bag sigue siendo la fuente; esto solo lo lee.

Este archivo no importa rclpy ni coordinacion_msgs a proposito, por la misma
razon que planificador.py: las reglas que convierten un bag en un veredicto se
agotan con pytest en milisegundos, y quien analice los datos en octubre no
deberia necesitar el workspace compilado para releerlos.
"""

import math

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
    exito = None if c1 is None else all(condiciones)

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
