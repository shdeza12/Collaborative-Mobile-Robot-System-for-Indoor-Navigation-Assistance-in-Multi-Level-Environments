#!/usr/bin/env python3
"""Maquina de estado del agente (RF-08). Sin ROS, para poder probarla sin grafo.

Mismo reparto que planificador.py / coordinador.py: la decision de QUE estado
tiene el robot vive aqui y se comprueba con prueba_agente.py sin levantar nada;
agente.py se queda solo con el cableado ROS.

DE DONDE SALE EL ESTADO, Y POR QUE DE AHI (decidido el 2026-09-07)

El coordinador manda a cada robot llamando su accion /<ns>/navigate_to_pose, de
la que Nav2 es el servidor. Ese servidor publica su propio estado en
/<ns>/navigate_to_pose/_action/status (action_msgs/GoalStatusArray). El agente
lee ESE topico, no /coordinacion/estado_mision.

La diferencia importa y no es de estilo. La prueba de RF-06 pide comprobar que
"el segundo agente permanece LIBRE" durante una mision de un solo nivel. Si el
agente dedujera su estado de lo que publica el coordinador, esa comprobacion
seria el coordinador dandose la razon a si mismo. Leyendo el status de la accion
la evidencia es independiente: el robot esta NAVEGANDO porque SU servidor de
navegacion tiene una meta viva, lo diga quien lo diga.

EN_TRANSFERENCIA es la excepcion declarada. El robot no puede saber por si solo
si la meta que ejecuta es un punto de relevo o el destino final: eso es dato de
la mision. Lo aporta el mando con declarar_relevo(), y aun asi solo se cree si
la accion propia confirma que hay actividad. El coordinador aporta su INTENCION,
no su opinion sobre el estado del robot; por eso no reintroduce la circularidad.
"""

# ---------------------------------------------------------------------------
# Estados del robot. Copiados de coordinacion_msgs/msg/EstadoRobot.msg, que es
# el contrato. prueba_agente.py parsea el .msg y compara, asi que si alguien
# cambia uno de los dos lados sin el otro, la prueba lo dice.
# ---------------------------------------------------------------------------
LIBRE = 0
NAVEGANDO = 1
EN_TRANSFERENCIA = 2
ERROR = 3

# ---------------------------------------------------------------------------
# Estados de meta de action_msgs/GoalStatus, con nombre en castellano para que
# el codigo de abajo se lea. No se importa action_msgs a proposito: este modulo
# tiene que poder correr sin ROS instalado.
# ---------------------------------------------------------------------------
DESCONOCIDA = 0   # STATUS_UNKNOWN
ACEPTADA = 1      # STATUS_ACCEPTED
EJECUTANDO = 2    # STATUS_EXECUTING
CANCELANDO = 3    # STATUS_CANCELING
EXITOSA = 4       # STATUS_SUCCEEDED
CANCELADA = 5     # STATUS_CANCELED
ABORTADA = 6      # STATUS_ABORTED

#: Una meta en cualquiera de estos estados sigue viva: el robot esta ocupado.
#: CANCELANDO entra aqui porque el robot todavia se esta deteniendo; darlo por
#: LIBRE en ese instante haria que el coordinador le mandara un tramo nuevo
#: encima de uno que aun no ha soltado.
VIVAS = (ACEPTADA, EJECUTANDO, CANCELANDO)

#: Terminales que significan que algo salio mal.
FALLIDAS = (ABORTADA, CANCELADA)

# ---------------------------------------------------------------------------
# Publicacion. El topico es RELATIVO a proposito: el nodo se lanza dentro del
# namespace del robot y ROS lo cuelga solo de /robot1/ o /robot2/. Escribirlo
# absoluto rompe la separacion por namespace que el proyecto usa desde el
# 2026-08-30. Declarado en Documentos/CONTRATO_INTERFACES.md §4.
# ---------------------------------------------------------------------------
TOPICO_ESTADO = "estado"
TOPICO_STATUS_ACCION = "navigate_to_pose/_action/status"

FRECUENCIA_HZ = 2.0                    # RF-08
PERIODO_S = 1.0 / FRECUENCIA_HZ        # 0,5 s


class MaquinaEstado:
    """Traduce el status de navigate_to_pose al estado que pide EstadoRobot.

    Se le va dando actualizar() con la lista de estados de meta que trae el
    ultimo GoalStatusArray, y devuelve el estado del robot. Guarda memoria de
    la marca de relevo, no del estado: el estado se recalcula entero en cada
    llamada para que no pueda quedarse pegado en un valor viejo.
    """

    def __init__(self):
        self._estado = LIBRE
        self._relevo = False

    @property
    def estado(self):
        """Ultimo estado calculado. LIBRE mientras no llegue ningun status."""
        return self._estado

    def declarar_relevo(self, es_relevo):
        """El mando declara que el tramo en curso termina en un relevo."""
        self._relevo = bool(es_relevo)

    def actualizar(self, estados_meta):
        """Recalcula el estado a partir de los estados de meta recibidos.

        El orden de las tres ramas no es arbitrario. Nav2 deja en el array
        metas ya terminadas junto a la viva, asi que una meta viva tiene que
        ganar a una vieja abortada: si no, un fallo antiguo dejaria al robot
        marcado en ERROR mientras navega perfectamente.
        """
        estados = list(estados_meta)

        if any(s in VIVAS for s in estados):
            self._estado = EN_TRANSFERENCIA if self._relevo else NAVEGANDO
        elif any(s in FALLIDAS for s in estados):
            self._estado = ERROR
        else:
            # Sin metas, o solo metas EXITOSA/DESCONOCIDA: no hay nada en curso.
            self._estado = LIBRE

        return self._estado
