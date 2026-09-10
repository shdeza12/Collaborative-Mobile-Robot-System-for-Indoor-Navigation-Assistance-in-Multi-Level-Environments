#!/usr/bin/env python3
"""Politica de plazos y enganche de la confirmacion de piso (RF-28).

Sin ROS a proposito, igual que planificador.py: asi se prueba en un segundo con
test/prueba_espera_confirmacion.py y no hace falta Gazebo para saber si los
plazos estan bien. El cableado -el topico, las marcas, el bucle- vive en
coordinador.py.

Ver Documentos/DISENO_CONFIRMACION_PISO.md.
"""

# Los dos plazos, en segundos de RELOJ DE PARED. Decididos el 2026-09-10 con el
# director: aviso al minuto, corte a los dos minutos.
#
# De pared y no de simulacion, y esto no es un detalle: quien sube las escaleras
# es una persona real en los dos bancos, asi que su paciencia se mide en
# segundos reales. Con RTF 0,5 estos 120 s de simulacion serian 240 s de espera
# real. Y si Gazebo muere durante la espera, /clock se detiene y un plazo medido
# en tiempo de simulacion no venceria NUNCA: el coordinador se colgaria justo en
# el caso para el que existe el plazo. Es el mismo razonamiento del docstring de
# _esperar() en coordinador.py.
ALERTA_S = 60.0
PLAZO_S = 120.0


def fase(transcurrido_s, alerta_s=ALERTA_S, plazo_s=PLAZO_S):
    """En que fase esta una espera que lleva 'transcurrido_s' segundos.

    Devuelve "esperando", "alerta" o "agotada". Los limites son cerrados por
    abajo: a los 60,0 s exactos ya es "alerta", y a los 120,0 s ya es "agotada".

    Un 'transcurrido_s' negativo devuelve "esperando". Solo puede venir de un
    salto del reloj hacia atras, y ante eso es mejor seguir esperando que matar
    una mision en curso.
    """
    if transcurrido_s >= plazo_s:
        return "agotada"
    if transcurrido_s >= alerta_s:
        return "alerta"
    return "esperando"


class Enganche:
    """Retiene la confirmacion del usuario hasta que alguien la consuma.

    EL FALLO QUE ESTO IMPIDE. El usuario puede subir mas rapido que el robot del
    piso de destino y pulsar 'ya estoy arriba' mientras ese robot todavia va
    hacia su escalera, es decir antes de que exista la espera. Sin enganche ese
    mensaje no lo recoge nadie y el usuario agota los 120 s completos habiendo
    cumplido su parte en 10 s.

    Y EL FALLO QUE IMPIDE AL REVES. Una confirmacion de una mision anterior no
    puede servir para la siguiente, o la siguiente arrancaria su tramo 2 sin
    preguntarle nada a nadie. De ahi que se guarde el mision_id y que
    reiniciar() lo borre al empezar cada mision.
    """

    def __init__(self):
        self._mision = None        # la mision en curso, o None
        self._confirmada = None    # la mision cuya confirmacion esta retenida

    def reiniciar(self, mision_id):
        """Empieza una mision. Descarta cualquier confirmacion retenida."""
        self._mision = mision_id
        self._confirmada = None

    def recibir(self, mision_id):
        """Llego un mensaje al topico. Se retiene solo si es de esta mision."""
        if mision_id and mision_id == self._mision:
            self._confirmada = mision_id

    def consumir(self, mision_id):
        """¿Hay confirmacion para 'mision_id'? La gasta si la hay."""
        if self._confirmada is not None and self._confirmada == mision_id:
            self._confirmada = None
            return True
        return False
