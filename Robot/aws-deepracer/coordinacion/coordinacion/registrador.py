#!/usr/bin/env python3
"""Registro estructurado de una mision (RF-25). Sin ROS y sin simulador.

POR QUE ESTA SEPARADO DEL COORDINADOR
-------------------------------------
Por la misma razon que 'planificador.py': lo que decide y lo que calcula no
importa rclpy, asi que se puede agotar con datos sinteticos en milisegundos en
vez de a base de levantar Gazebo. El coordinador solo lo alimenta con marcas y
muestras; todas las metricas del §3 del protocolo se derivan aqui.

EL ESQUEMA ESTA CONGELADO, Y ESO ES EL PUNTO
--------------------------------------------
'Documentos/PLAN_S20.md' §2.3 lo pide antes de la primera metrica y explica por
que: S26 es el analisis comparativo simulacion contra fisico, y eso solo existe
si las 30 corridas simuladas y las 5-10 fisicas producen registros con el MISMO
esquema. Si el registrador se va escribiendo metrica a metrica segun haga falta,
en S26 hay dos conjuntos de datos que no se cruzan y no queda semana para
repetir ninguna campana.

Por eso el esquema prevé los campos de hardware aunque en simulacion vayan a
'null': en simulacion la verdad de terreno es /odom y hay RTF; en hardware la
verdad es medicion externa y no hay RTF. Los dos casos caben en la misma forma.

Subir ESQUEMA_VERSION es un acto deliberado: obliga al analizador de campana a
saber que hay dos formas de registro en juego. No se sube por anadir un campo
opcional; se sube cuando un campo existente cambia de significado.

LO QUE ESTE REGISTRADOR NO PUEDE ARREGLAR: LA RESOLUCION DEL RELOJ
------------------------------------------------------------------
Medido el 2026-08-26 sobre una mision real: '/clock' se publica a 9,8 Hz, luego
el reloj de simulacion avanza a saltos de 0,1 s y NINGUNA marca temporal puede
ser mas fina que eso. En la corrida de prueba salio t_asignacion = 0.0 s y
t_respuesta = 0.1 s, que es exactamente un tick.

Importa porque el §3.2 del protocolo dice que t_asignacion "se espera en
milisegundos" y justifica la marca extraordinaria con que 1 Hz es demasiado
grueso. La marca extraordinaria mejora la resolucion de 1 s a 0,1 s -diez
veces-, pero la premisa de los milisegundos NO se sostiene: para llegar ahi hay
que subir la frecuencia de '/clock' en el plugin de Gazebo, y eso es
configuracion congelada (§5 del protocolo), o sea una decision y no un arreglo.

Mientras no se decida, t_asignacion solo puede afirmarse como "por debajo de
0,1 s". Es suficiente para lo que el protocolo quiere concluir -que asignar es
mucho mas rapido que moverse- pero no para dar una cifra.

QUE NO HACE
-----------
No decide si una corrida se descarta. El §8 del protocolo tiene una lista
cerrada de causas y exige evidencia por escrito; aqui solo se deja el hueco
('descarte') para que quien lo decida lo anote sobre el mismo archivo. Un
registrador que se auto-descarta seria juez y parte.
"""

import json
import math
from pathlib import Path

ESQUEMA_VERSION = "1.0"

# §3.1: primera muestra con |v| >= UMBRAL y las dos siguientes tambien. Las tres
# consecutivas estan para no disparar con un pico de ruido.
UMBRAL_MOVIMIENTO_MS = 0.02
MUESTRAS_CONSECUTIVAS = 3

# §3.3: la misma xy_goal_tolerance que Nav2 declara. El criterio de exito es "el
# sistema hizo lo que se le pidio con la precision que dice tener".
TOLERANCIA_LLEGADA_M = 0.25

ETAPAS = {0: "INACTIVA", 1: "TRAMO_1", 2: "TRANSFERENCIA", 3: "TRAMO_2",
          4: "COMPLETADA", 5: "FALLIDA"}


class RegistroMision:
    """Acumula lo ocurrido en una mision y derivadas las cuatro metricas."""

    def __init__(self, mision_id, origen_id, destino_id, asignacion,
                 t_solicitud, condicion="simulacion"):
        if condicion not in ("simulacion", "hardware"):
            raise ValueError(
                f"condicion debe ser 'simulacion' o 'hardware', no {condicion!r}")
        self.mision_id = mision_id
        self.origen_id = origen_id
        self.destino_id = destino_id
        self.asignacion = dict(asignacion)
        self.condicion = condicion
        # t_solicitud es el instante en que el servidor ACEPTA el goal (§3.1), no
        # el envio de la HRI: la latencia del navegador no es del sistema
        # robotico y no se puede medir desde dentro.
        self.t_solicitud = float(t_solicitud)
        self.marcas = []
        self.trazas = {}
        self.cierre = None
        self.entorno = {}
        self.descarte = {"descartada": False, "causa": None, "evidencia": None}

    # ------------------------------------------------------------- ingesta

    def marca(self, t, etapa, robot, punto_id=None, extraordinaria=True):
        """Un cambio de etapa. 'extraordinaria' distingue la publicacion del
        instante del cambio (§3.2) del tick periodico de 1 Hz."""
        self.marcas.append({
            "t": float(t),
            "etapa": ETAPAS.get(etapa, str(etapa)),
            "etapa_num": int(etapa),
            "robot": robot or "",
            "punto_id": punto_id,
            "extraordinaria": bool(extraordinaria),
        })

    def muestra(self, t, robot, x, y, z, v, yaw):
        """Una muestra de /<ns>/odom. 'v' es la velocidad lineal, ya en modulo."""
        self.trazas.setdefault(robot, []).append(
            [round(float(t), 4), round(float(x), 4), round(float(y), 4),
             round(float(z), 6), round(float(v), 4), round(float(yaw), 4)])

    def cerrar(self, t, exito, motivo, num_relevos, destino_pose):
        self.cierre = {
            "t": float(t),
            "exito_declarado": bool(exito),
            "motivo_fallo": motivo or "",
            "num_relevos": int(num_relevos),
            "destino_pose": {"x": float(destino_pose["x"]),
                             "y": float(destino_pose["y"]),
                             "yaw": float(destino_pose.get("yaw", 0.0))},
        }

    # ------------------------------------------------------------- derivadas

    def _primer_movimiento(self, robot, desde=None):
        """§3.1. Devuelve None si el robot nunca supero el umbral."""
        muestras = self.trazas.get(robot, [])
        seguidas = 0
        for i, (t, _x, _y, _z, v, _yaw) in enumerate(muestras):
            if desde is not None and t < desde:
                seguidas = 0
                continue
            if abs(v) >= UMBRAL_MOVIMIENTO_MS:
                seguidas += 1
                if seguidas >= MUESTRAS_CONSECUTIVAS:
                    # El instante que cuenta es el de la PRIMERA de las tres, no
                    # el de la tercera: las otras dos solo confirman que no fue
                    # un pico de ruido. Se busca por INDICE y no por valor
                    # -muestras.index(fila)- porque dos muestras identicas son
                    # perfectamente posibles con el robot casi quieto, y el
                    # index() devolveria el instante de la primera de ellas.
                    return muestras[i - (MUESTRAS_CONSECUTIVAS - 1)][0]
            else:
                seguidas = 0
        return None

    def _marca_de(self, etapa_num, con_robot=True):
        for m in self.marcas:
            if m["etapa_num"] == etapa_num and (not con_robot or m["robot"]):
                return m
        return None

    def _pose_final(self, robot):
        tr = self.trazas.get(robot, [])
        return tr[-1] if tr else None

    def metricas(self):
        """Las cuatro del §3, mas las descriptivas. None = no medible."""
        m = {"t_respuesta_s": None, "t_asignacion_s": None,
             "hueco_relevo_s": None, "continuidad": None,
             "error_llegada_m": None, "rumbo_llegada_rad": None,
             "exito": False, "criterios_exito": {}}

        tramo1 = self._marca_de(1)
        if tramo1:
            # §3.2: t_robot_activo es la primera marca TRAMO_1 con robot no vacio
            m["t_asignacion_s"] = round(tramo1["t"] - self.t_solicitud, 4)
            pm = self._primer_movimiento(tramo1["robot"], desde=self.t_solicitud)
            if pm is not None:
                m["t_respuesta_s"] = round(pm - self.t_solicitud, 4)

        # §3.4, solo en misiones entre niveles
        transferencia = self._marca_de(2, con_robot=False)
        tramo2 = self._marca_de(3)
        if transferencia and tramo2:
            pm2 = self._primer_movimiento(tramo2["robot"], desde=transferencia["t"])
            if pm2 is not None:
                m["hueco_relevo_s"] = round(pm2 - transferencia["t"], 4)
            # continuidad: ninguna marca INACTIVA ni robot vacio en el intervalo
            m["continuidad"] = all(
                x["etapa_num"] != 0 and x["robot"]
                for x in self.marcas
                if self.t_solicitud <= x["t"] <= (self.cierre or {}).get("t", math.inf)
                and x["etapa_num"] not in (4,)
            )

        if self.cierre:
            ultimo = self.marcas[-1] if self.marcas else None
            robot_final = ultimo["robot"] if ultimo else ""
            pf = self._pose_final(robot_final)
            if pf:
                d = self.cierre["destino_pose"]
                m["error_llegada_m"] = round(
                    math.hypot(pf[1] - d["x"], pf[2] - d["y"]), 4)
                m["rumbo_llegada_rad"] = pf[5]

            # §3.3: las tres condiciones, y ninguna es el SUCCEEDED de Nav2
            c1 = (m["error_llegada_m"] is not None
                  and m["error_llegada_m"] <= TOLERANCIA_LLEGADA_M)
            c2 = (any(x["etapa_num"] == 4 for x in self.marcas)
                  and not any(x["etapa_num"] == 5 for x in self.marcas))
            entre_niveles = transferencia is not None
            c3 = (self.cierre["num_relevos"] == 1) if entre_niveles else True
            m["criterios_exito"] = {
                "llegada_a_025_m": c1, "completada_sin_fallida": c2,
                "relevo_si_entre_niveles": c3}
            m["exito"] = bool(c1 and c2 and c3)
        return m

    # ------------------------------------------------------------- salida

    def a_dict(self):
        return {
            "esquema": ESQUEMA_VERSION,
            "mision_id": self.mision_id,
            "condicion": self.condicion,
            "solicitud": {
                "origen_id": self.origen_id,
                "destino_id": self.destino_id,
                "t_solicitud": self.t_solicitud,
            },
            "asignacion": self.asignacion,
            "marcas": self.marcas,
            "metricas": self.metricas(),
            "cierre": self.cierre,
            "trazas": {
                "formato": ["t", "x", "y", "z", "v", "yaw"],
                "muestras": self.trazas,
            },
            "entorno": self.entorno,
            "descarte": self.descarte,
        }

    def guardar(self, carpeta):
        """Un archivo por mision, con el id en el nombre. Devuelve la ruta."""
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = carpeta / f"mision_{self.mision_id}.json"
        ruta.write_text(json.dumps(self.a_dict(), indent=2, ensure_ascii=False))
        return ruta


def entorno_simulacion(mundo, mapa, rtf, controladores):
    """Los campos de entorno de una corrida simulada. Los de hardware van a
    None a proposito: el esquema es el mismo en las dos condiciones (§2.3 del
    plan de S20) y el analizador distingue por 'condicion', no por que falten
    claves."""
    return {
        "verdad_terreno": "odom",
        "mundo": mundo,
        "mapa": mapa,
        "rtf": rtf,
        "controladores_activos": dict(controladores),
        "vehiculo_id": None,
        "distro": None,
        "medicion_externa_m": None,
    }


def entorno_hardware(mapa, controladores, vehiculo_id, distro,
                     medicion_externa_m=None):
    """El espejo del anterior. 'rtf' y 'mundo' van a None porque en hardware no
    existen, y 'verdad_terreno' cambia: la posicion de llegada se mide fuera."""
    return {
        "verdad_terreno": "medicion_externa",
        "mundo": None,
        "mapa": mapa,
        "rtf": None,
        "controladores_activos": dict(controladores),
        "vehiculo_id": vehiculo_id,
        "distro": distro,
        "medicion_externa_m": medicion_externa_m,
    }
