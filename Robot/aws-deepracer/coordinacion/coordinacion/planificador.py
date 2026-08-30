"""Planificacion de una mision de guiado. Sin ROS, a proposito.

Este archivo es el aporte declarado del proyecto -la coordinacion y el protocolo
de relevo entre niveles- escrito como funcion pura: entra el catalogo de puntos y
un par origen/destino, sale la lista de tramos que hay que ejecutar.

POR QUE NO IMPORTA rclpy. Si el relevo viviera dentro del nodo, mezclado con
clientes de accion, la unica forma de comprobarlo seria levantar dos Gazebos y
mirar si el carro llega. Eso es lento, es fragil, y el 2026-08-12 se decidio que
un SUCCEEDED de Nav2 no se acepta como evidencia. Aqui la logica se agota en
milisegundos con pytest y sin simulador, y al nodo le queda solo el cableado.

La secuencia que implementa es la del §4 de Documentos/CONTRATO_INTERFACES.md.
"""

import math

# Nivel -> namespace del robot que lo atiende.
#
# Es un dato, no una constante de codigo: el §1 del contrato dice que el
# coordinador no distingue si un robot es simulado o fisico, y el §3 dice que el
# nivel es una IDENTIDAD del agente. Cambiar quien atiende que piso es cambiar
# este diccionario, no la logica.
ASIGNACION_POR_DEFECTO = {1: "robot1", 2: "robot2"}


class ErrorPlanificacion(Exception):
    """La mision no se puede planificar. Lleva el motivo ya redactado en espanol.

    Se distingue a proposito de un fallo de navegacion: esto ocurre ANTES de
    mover un solo robot, y el motivo va tal cual al campo motivo_fallo del
    result de GuiarUsuario.
    """


class Tramo:
    """Un movimiento de un robot a un punto. Es lo que se convierte en un goal.

    'con_usuario' distingue los dos tipos de tramo, y no es cosmetico: cuando el
    robot va a RECOGER al usuario, este todavia no lo esta siguiendo, asi que el
    mensaje que ve por pantalla tiene que ser 'espere' y no 'sigame'. Sin este
    campo la HRI le diria a alguien que siga a un robot que aun no ha llegado.
    """

    def __init__(self, robot, punto, etapa, con_usuario, mensaje_usuario):
        self.robot = robot
        self.punto = punto
        self.etapa = etapa
        self.con_usuario = con_usuario
        self.mensaje_usuario = mensaje_usuario

    def __repr__(self):
        marca = "con usuario" if self.con_usuario else "sin usuario"
        return f"<Tramo {self.robot} -> {self.punto['id']} ({marca})>"


# Etapas. Son los mismos numeros que EstadoMision.msg, repetidos aqui para no
# tener que importar coordinacion_msgs y romper la independencia de ROS.
# La prueba prueba_planificador.py comprueba que no se hayan desincronizado.
INACTIVA = 0
TRAMO_1 = 1
TRANSFERENCIA = 2
TRAMO_2 = 3
COMPLETADA = 4
FALLIDA = 5
# El estado entre 'llego la solicitud' y 'ya hay agente'. Sin el, el tiempo de
# asignacion vale cero por construccion. Ver el comentario de EstadoMision.msg.
RECIBIDA = 6


def yaw_a_cuaternion(yaw):
    """Solo z y w: el robot gira en el plano, roll y pitch son cero siempre."""
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


def _buscar(catalogo, id_punto, papel):
    for p in catalogo:
        if p["id"] == id_punto:
            return p
    conocidos = ", ".join(sorted(p["id"] for p in catalogo))
    raise ErrorPlanificacion(
        f"El {papel} '{id_punto}' no esta en el catalogo. Conocidos: {conocidos}"
    )


def _transferencia_de(catalogo, nivel):
    """El punto por el que se cambia de nivel.

    Se exige que haya EXACTAMENTE uno por nivel, y se falla ruidosamente si no.
    Hoy el edificio tiene una escalera por piso y eso se cumple. Si algun dia
    tiene dos, este es el sitio donde hay que decidir cual -presumiblemente la
    mas cercana al punto anterior-, y es mejor que reviente aqui con un mensaje
    claro a que elija una en silencio y nadie entienda por que el robot cruza el
    edificio entero para subir.
    """
    candidatos = [p for p in catalogo
                  if p.get("es_transferencia") and p["nivel"] == nivel]
    if not candidatos:
        raise ErrorPlanificacion(
            f"El nivel {nivel} no tiene punto de transferencia, asi que no se "
            f"puede entrar ni salir de el. Falta un punto con "
            f"es_transferencia: true en puntos_interes.yaml"
        )
    if len(candidatos) > 1:
        ids = ", ".join(p["id"] for p in candidatos)
        raise ErrorPlanificacion(
            f"El nivel {nivel} tiene {len(candidatos)} puntos de transferencia "
            f"({ids}) y el planificador no sabe cual elegir. Ver "
            f"_transferencia_de() en planificador.py"
        )
    return candidatos[0]


def condicion_de(catalogo, origen_id, destino_id):
    """La condicion experimental de una mision: 'A' intra-nivel, 'B' inter-nivel.

    Devuelve 'X' si alguno de los dos ids no esta en el catalogo, en vez de
    lanzar: esta funcion se llama al ACEPTAR el goal, antes de planificar, y un
    identificador de mision tiene que salir siempre -tambien para la mision que
    va a fallar, que es justamente la que la tasa de exito necesita contar-.

    Ver §3.2 de Documentos/ESQUEMA_REGISTRO_MISION.md.
    """
    niveles = {p["id"]: int(p["nivel"]) for p in catalogo}
    if origen_id not in niveles or destino_id not in niveles:
        return "X"
    return "A" if niveles[origen_id] == niveles[destino_id] else "B"


def generar_mision_id(prefijo, condicion, ahora):
    """Identificador unico de mision. Ver §2.1 del esquema de registro (RF-25).

    Lleva marca de tiempo y no un consecutivo porque la §6.4 del protocolo manda
    un gzserver nuevo por corrida: un contador en memoria se reiniciaria en cada
    una y las treinta misiones de S24 se llamarian todas igual.

    Hasta el 2026-08-26 el coordinador publicaba pet.origen_id como mision_id,
    o sea el ID del punto de PARTIDA. Dos misiones que salieran del mismo sitio
    llevaban el mismo identificador, y con N = 30 y pares sorteados eso hace
    imposible saber que registro es de que corrida.

    'ahora' entra como argumento y no se lee aqui dentro para que la prueba sea
    determinista.
    """
    sello = ahora.strftime("%Y%m%d_%H%M%S")
    return f"{prefijo}_{condicion}_{sello}" if prefijo else f"manual_{sello}"


def _colapsar(tramos):
    """Funde tramos consecutivos del mismo robot al mismo punto.

    HACE FALTA, y se descubrio el 2026-08-24 imprimiendo un plan, no con la
    prueba: cuando el origen o el destino ES el punto de transferencia de su
    nivel, el plan salia con el mismo robot mandado dos veces a la misma pose.
    El segundo goal es un desplazamiento de cero metros, y peor, el texto decia
    'siga al robot hasta Escaleras' a alguien que ya estaba en las escaleras.

    No es un caso raro: hoy el piso 2 tiene UN punto y es el de transferencia,
    asi que las 30 misiones con relevo del catalogo real caen aqui.

    Se conserva el tramo ANTERIOR entero -su mensaje y su con_usuario son los
    correctos: el robot se mueve hacia el usuario, no al reves- y se descarta el
    posterior, que no requiere movimiento.
    """
    salida = []
    for t in tramos:
        if salida and salida[-1].robot == t.robot \
                and salida[-1].punto["id"] == t.punto["id"]:
            continue
        salida.append(t)
    return salida


def planificar(catalogo, origen_id, destino_id, asignacion=None):
    """Devuelve (tramos, num_relevos). Lanza ErrorPlanificacion si no se puede.

    catalogo: lista de dicts con id, nombre, nivel, es_transferencia, pose.
    """
    asignacion = asignacion or ASIGNACION_POR_DEFECTO

    if not catalogo:
        raise ErrorPlanificacion("El catalogo de puntos esta vacio")

    origen = _buscar(catalogo, origen_id, "origen")
    destino = _buscar(catalogo, destino_id, "destino")

    if origen_id == destino_id:
        raise ErrorPlanificacion(
            f"El origen y el destino son el mismo punto ('{origen_id}'). "
            f"No hay nada que guiar"
        )

    for punto, papel in ((origen, "origen"), (destino, "destino")):
        if punto["nivel"] not in asignacion:
            raise ErrorPlanificacion(
                f"El {papel} '{punto['id']}' esta en el nivel {punto['nivel']}, "
                f"y no hay ningun robot asignado a ese nivel"
            )

    robot_origen = asignacion[origen["nivel"]]
    robot_destino = asignacion[destino["nivel"]]

    # --- Mismo nivel: un solo robot, cero relevos. -----------------------
    # El §4 del contrato lo pide sin ramas especiales en la HRI, y por eso la
    # forma de la salida es identica: una lista de tramos. La HRI no pregunta
    # cuantos hay, los va mostrando.
    if origen["nivel"] == destino["nivel"]:
        return (_colapsar([
            Tramo(robot_origen, origen, TRAMO_1, False,
                  f"El robot va hacia {origen['nombre']}. Espere alli."),
            Tramo(robot_origen, destino, TRAMO_1, True,
                  f"Siga al robot hasta {destino['nombre']}."),
        ]), 0)

    # --- Niveles distintos: relevo. ---------------------------------------
    transf_origen = _transferencia_de(catalogo, origen["nivel"])
    transf_destino = _transferencia_de(catalogo, destino["nivel"])

    if robot_origen == robot_destino:
        raise ErrorPlanificacion(
            f"Los niveles {origen['nivel']} y {destino['nivel']} estan "
            f"asignados al mismo robot ('{robot_origen}'), y ningun robot "
            f"cruza de nivel (decision D2). La asignacion es incoherente"
        )

    return (_colapsar([
        Tramo(robot_origen, origen, TRAMO_1, False,
              f"El robot va hacia {origen['nombre']}. Espere alli."),
        Tramo(robot_origen, transf_origen, TRAMO_1, True,
              f"Siga al robot hasta {transf_origen['nombre']}."),
        # El usuario cambia de nivel por su cuenta: ningun robot cruza (D2).
        # 'Suba' o 'Baje' segun el sentido: decirle a alguien que suba al piso 1
        # desde el 2 es de las cosas que nadie revisa y todo el mundo nota.
        Tramo(robot_destino, transf_destino, TRANSFERENCIA, False,
              f"{'Suba' if destino['nivel'] > origen['nivel'] else 'Baje'} al "
              f"piso {destino['nivel']}. Otro robot le espera en "
              f"{transf_destino['nombre']}."),
        Tramo(robot_destino, destino, TRAMO_2, True,
              f"Siga al robot hasta {destino['nombre']}."),
    ]), 1)
