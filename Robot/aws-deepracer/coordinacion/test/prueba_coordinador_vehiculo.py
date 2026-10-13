#!/usr/bin/env python3
"""El coordinador con condicion:=hardware: pose en el mapa, pisos 3 y 4 y misiones encadenadas.

    source ~/deepracer_sim_ws/install/setup.bash
    ROS_DOMAIN_ID=93 ROS_LOCALHOST_ONLY=1 python3 Robot/aws-deepracer/coordinacion/test/prueba_coordinador_vehiculo.py

POR QUE EXISTE
--------------
En el vehiculo /<ns>/odom empieza en (0, 0) donde arranca rf2o, no en la salida
del mapa, y el coordinador comparaba esa odometria con las coordenadas del
catalogo, que estan en el mapa. Habria rechazado llegadas buenas a 10 m de
distancia aparente (Documentos/PLAN_S26.md §4.1). Desde el 2026-10-05, con
condicion:=hardware lee la pose que cada agente publica en /<ns>/estado, en el
marco del mapa. En simulacion no se nota nada de esto, porque alli /odom es la
pose de Gazebo en el mundo; por eso hace falta una prueba con robots falsos
cuya odometria no coincide con el mapa, como en el vehiculo.

QUE MONTA
---------
El nodo Coordinador real, con el catalogo de los pisos 3 y 4, robot_nivel_3 =
robot1 y robot_nivel_4 = robot2, y dos robots falsos. Cada robot falso:

- sirve /<ns>/navigate_to_pose: se mueve hacia la meta y se queda 0,20 m corto,
  y atiende la cancelacion;
- publica /<ns>/odom con origen en su salida, como rf2o: en (0, 0) y rumbo 0
  donde arranca, aunque en el mapa la salida sea otra;
- publica /<ns>/estado a 2 Hz con su pose en <ns>/map, como el agente.

Salidas, las del vehiculo: robot1 en la escalera del piso 3 (22,10, 1,06) y
robot2 en la del piso 4 (24,45, 1,21), los dos mirando al norte (rumbo pi).

QUE COMPRUEBA
-------------
  1. Mision entre pisos, Salon 302 -> Salon 402: un relevo, con la confirmacion
     de piso; las llegadas se aceptan a 0,20 m, y el rumbo de cada meta sigue
     la direccion de llegada en el mapa (pi hacia el norte, 0 hacia el sur).
  2. Segunda mision encadenada, sin reubicar: Salon 403 -> Salon 401. robot2
     sale de donde quedo (en el 402) y va al sur a buscar al usuario.
  3. Los registros de las dos misiones: exito, error de llegada de 0,20 m (en
     el marco del mapa) y la asignacion con los niveles 3 y 4.
  4. Cancelacion: robot2 vuelve a la escalera del piso 4, aunque tenga
     asignados los niveles 2 y 4.
  5. Si el agente deja de publicar, la llegada no se acepta: sin pose, no hay
     verificacion.
  6. Control: el mismo escenario con condicion:=simulacion, que lee /odom,
     rechaza la llegada. Es el fallo que la opcion B corrige, y prueba que el
     montaje distingue los dos marcos.

Con la ruta de otro coordinador.py como argumento se comprueba que la prueba
no es vacia: la version anterior al 2026-10-05 tiene que fallar.

En el vehiculo, donde el catalogo esta en ~/tesis y no en el repositorio:

    CATALOGO=/home/deepracer/tesis/puntos_interes_pisos34.yaml ROS_DOMAIN_ID=93 ROS_LOCALHOST_ONLY=1 python3 ~/coordinacion_ws/src/coordinacion/test/prueba_coordinador_vehiculo.py   # ruta fija del vehiculo
"""

import importlib.util
import json
import math
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

PAQUETE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAQUETE))
RAIZ = PAQUETE.parents[2]
CATALOGO = Path(os.environ.get(
    "CATALOGO", RAIZ / "Robot/aws-deepracer/deepracer_bringup/config/puntos_interes_pisos34.yaml"))

import rclpy  # noqa: E402
from action_msgs.msg import GoalStatus  # noqa: E402
from coordinacion_msgs.action import GuiarUsuario  # noqa: E402
from coordinacion_msgs.msg import EstadoMision, EstadoRobot  # noqa: E402
from nav2_msgs.action import NavigateToPose  # noqa: E402
from nav_msgs.msg import Odometry  # noqa: E402
from rclpy.action import ActionClient, ActionServer, CancelResponse  # noqa: E402
from rclpy.callback_groups import ReentrantCallbackGroup  # noqa: E402
from rclpy.executors import MultiThreadedExecutor  # noqa: E402
from rclpy.node import Node  # noqa: E402
from std_msgs.msg import String  # noqa: E402
from std_srvs.srv import Trigger  # noqa: E402

from coordinacion.planificador import ESPERANDO_CONFIRMACION  # noqa: E402

ERROR_LLEGADA_M = 0.20      # lo que se queda corto cada robot falso
# 2026-10-13: racey, el 7-oct, seguia rodando 0,3 a 0,5 m durante el segundo
# siguiente a la ultima orden de avance de Nav2, que ya habia dicho SUCCEEDED.
INERCIA_M = 0.45
VELOCIDAD_FALSA = 10.0      # m/s: la prueba no espera lo que tardaria el vehiculo
SALIDAS = {"robot1": (22.10, 1.06, math.pi), "robot2": (24.45, 1.21, math.pi)}
NIVELES = {"robot1": 3, "robot2": 4}

OK = 0
FALLOS = []


def comprueba(titulo, condicion, detalle=""):
    global OK
    if condicion:
        OK += 1
        print(f"  [OK ] {titulo} {detalle}")
    else:
        FALLOS.append(titulo)
        print(f"  [MAL] {titulo} {detalle}")


def normalizar(a):
    return math.atan2(math.sin(a), math.cos(a))


def yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class RobotFalso(Node):
    """Nav2, rf2o y el agente de un vehiculo, reducidos a lo que el coordinador mira."""

    def __init__(self, ns, con_media_vuelta=False):
        super().__init__(f"falso_{ns}")
        self.ns = ns
        self.salida = SALIDAS[ns]
        self.x, self.y, self.yaw = self.salida
        self.v = 0.0
        self.mudo = False
        self.inercia_m = 0.0          # >0: SUCCEEDED con el vehiculo aun rodando
        self.metas = []                 # (x, y, yaw) pedidos, en orden
        self.eventos = []               # 'meta' y 'media_vuelta', en el orden en que llegan
        self.meta_recibida = threading.Event()
        grupo = ReentrantCallbackGroup()
        self.pub_odom = self.create_publisher(Odometry, f"/{ns}/odom", 10)
        self.pub_estado = self.create_publisher(EstadoRobot, f"/{ns}/estado", 10)
        self.create_timer(0.1, self._odom, callback_group=grupo)
        self.create_timer(0.5, self._estado, callback_group=grupo)
        self.servidor = ActionServer(
            self, NavigateToPose, f"/{ns}/navigate_to_pose", self._navegar,
            cancel_callback=lambda _gh: CancelResponse.ACCEPT, callback_group=grupo)
        if con_media_vuelta:
            # El servicio del agente (coordinacion/media_vuelta.py), reducido a girar.
            self.create_service(Trigger, f"/{ns}/media_vuelta", self._media_vuelta,
                                callback_group=grupo)

    def _media_vuelta(self, _peticion, respuesta):
        self.eventos.append("media_vuelta")
        time.sleep(0.3)
        self.yaw = normalizar(self.yaw + math.pi)
        respuesta.success, respuesta.message = True, "media vuelta: 180 grados (falsa)"
        return respuesta

    def _odom(self):
        # Como rf2o: origen y rumbo 0 en la salida, sea cual sea la salida en el mapa.
        x0, y0, a0 = self.salida
        dx, dy = self.x - x0, self.y - y0
        m = Odometry()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id, m.child_frame_id = f"{self.ns}/odom", f"{self.ns}/base_link"
        m.pose.pose.position.x = math.cos(a0) * dx + math.sin(a0) * dy
        m.pose.pose.position.y = -math.sin(a0) * dx + math.cos(a0) * dy
        a = normalizar(self.yaw - a0)
        m.pose.pose.orientation.z, m.pose.pose.orientation.w = math.sin(a / 2), math.cos(a / 2)
        m.twist.twist.linear.x = self.v
        self.pub_odom.publish(m)

    def _estado(self):
        if self.mudo:
            return
        m = EstadoRobot()
        m.robot_id, m.nivel = self.ns, NIVELES[self.ns]
        m.pose.header.stamp = self.get_clock().now().to_msg()
        m.pose.header.frame_id = f"{self.ns}/map"
        m.pose.pose.position.x, m.pose.pose.position.y = self.x, self.y
        m.pose.pose.orientation.z = math.sin(self.yaw / 2)
        m.pose.pose.orientation.w = math.cos(self.yaw / 2)
        m.stamp = m.pose.header.stamp
        self.pub_estado.publish(m)

    def _navegar(self, goal_handle):
        p = goal_handle.request.pose.pose
        self.metas.append((p.position.x, p.position.y, yaw_de(p.orientation)))
        self.eventos.append("meta")
        self.meta_recibida.set()
        dx, dy = p.position.x - self.x, p.position.y - self.y
        d = math.hypot(dx, dy)
        recorrido = max(0.0, d - ERROR_LLEGADA_M - self.inercia_m)
        ux, uy = (dx / d, dy / d) if d > 0 else (0.0, 0.0)
        if recorrido > 0:
            self.yaw = math.atan2(uy, ux)
            x0, y0 = self.x, self.y
            pasos = max(1, int(recorrido / VELOCIDAD_FALSA / 0.05))
            self.v = VELOCIDAD_FALSA
            for i in range(1, pasos + 1):
                if goal_handle.is_cancel_requested:
                    self.v = 0.0
                    goal_handle.canceled()
                    return NavigateToPose.Result()
                time.sleep(0.05)
                self.x = x0 + ux * recorrido * i / pasos
                self.y = y0 + uy * recorrido * i / pasos
            self.v = 0.0
        if self.inercia_m > 0:
            # Como Nav2 en el vehiculo: SUCCEEDED en cuanto entra en su margen, y
            # el vehiculo sigue rodando hasta asentarse.
            goal_handle.succeed()
            threading.Thread(target=self._rodar, args=(ux, uy), daemon=True).start()
            return NavigateToPose.Result()
        time.sleep(0.6)     # que llegue al menos una pose del agente ya parado
        goal_handle.succeed()
        return NavigateToPose.Result()


    def _rodar(self, ux, uy):
        x0, y0 = self.x, self.y
        for i in range(1, 17):         # 0,8 s
            time.sleep(0.05)
            self.x = x0 + ux * self.inercia_m * i / 16
            self.y = y0 + uy * self.inercia_m * i / 16


class Usuario(Node):
    """La interfaz: pide misiones, confirma el cambio de piso y cancela."""

    def __init__(self):
        super().__init__("usuario_prueba")
        self.cliente = ActionClient(self, GuiarUsuario, "/coordinacion/guiar_usuario")
        self.pub_conf = self.create_publisher(String, "/coordinacion/confirmacion_piso", 10)
        self.confirmadas = set()
        self.create_subscription(EstadoMision, "/coordinacion/estado_mision", self._estado, 10)

    def _estado(self, m):
        if m.etapa == ESPERANDO_CONFIRMACION and m.mision_id not in self.confirmadas:
            self.confirmadas.add(m.mision_id)
            self.pub_conf.publish(String(data=m.mision_id))

    def pedir(self, origen, destino, cancelar_si=None, plazo=60.0):
        """Devuelve (estado de la accion, resultado)."""
        if not self.cliente.wait_for_server(timeout_sec=10.0):
            return None, None
        meta = GuiarUsuario.Goal(origen_id=origen, destino_id=destino)
        fut = self.cliente.send_goal_async(meta)
        esperar(fut, plazo)
        gh = fut.result()
        if gh is None or not gh.accepted:
            return None, None
        if cancelar_si is not None:
            cancelar_si.wait(timeout=plazo)
            time.sleep(0.3)
            esperar(gh.cancel_goal_async(), plazo)
        fut = gh.get_result_async()
        esperar(fut, plazo)
        r = fut.result()
        return (r.status, r.result) if r else (None, None)


def esperar(fut, plazo):
    t0 = time.time()
    while not fut.done() and time.time() - t0 < plazo:
        time.sleep(0.02)


def cargar_coordinador(ruta):
    if ruta is None:
        from coordinacion.coordinador import Coordinador
        return Coordinador
    spec = importlib.util.spec_from_file_location("coordinador_alternativo", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.Coordinador


def montar(condicion, registros, clase, con_media_vuelta=False):
    rclpy.init(args=[
        "--ros-args", "-p", f"ruta_puntos:={CATALOGO}", "-p", "robot_nivel_3:=robot1",
        "-p", "robot_nivel_4:=robot2", "-p", f"condicion:={condicion}",
        "-p", f"ruta_registros:={registros}", "-p", "espera_servidor_s:=5.0"])
    robots = {ns: RobotFalso(ns, con_media_vuelta) for ns in SALIDAS}
    usuario = Usuario()
    coordinador = clase()
    ejecutor = MultiThreadedExecutor(num_threads=12)
    for n in (coordinador, usuario, *robots.values()):
        ejecutor.add_node(n)
    hilo = threading.Thread(target=ejecutor.spin, daemon=True)
    hilo.start()
    time.sleep(2.0)     # descubrimiento y primeras poses
    return robots, usuario, coordinador, ejecutor


def desmontar(ejecutor):
    ejecutor.shutdown()
    rclpy.shutdown()


def comprobar_rumbos(titulo, metas, esperados):
    pedidos = [round(math.degrees(m[2])) for m in metas]
    bien = len(metas) == len(esperados) and all(
        abs(normalizar(m[2] - e)) < 0.01 for m, e in zip(metas, esperados))
    comprueba(titulo, bien, f"(pedidos {pedidos} grados)")


def registros_de(carpeta):
    return [json.loads(p.read_text()) for p in sorted(Path(carpeta).glob("mision_*.json"),
                                                       key=lambda p: p.stat().st_mtime)]


def con_hardware(clase):
    with tempfile.TemporaryDirectory() as registros:
        robots, usuario, _coord, ejecutor = montar("hardware", registros, clase)
        r1, r2 = robots["robot1"], robots["robot2"]
        try:
            print("1. Salon 302 (piso 3) -> Salon 402 (piso 4), con relevo")
            estado, res = usuario.pedir("piso3_salon_302", "piso4_salon_402")
            comprueba("la mision se completa", estado == GoalStatus.STATUS_SUCCEEDED
                      and res is not None and res.exito,
                      f"(estado {estado}, motivo {res.motivo_fallo if res else None!r})")
            comprueba("con un relevo", res is not None and res.num_relevos == 1)
            comprobar_rumbos("robot1: Salon 302 hacia el norte (pi) y escalera hacia el sur (0)",
                             r1.metas, [math.pi, 0.0])
            comprobar_rumbos("robot2: escalera (ya estaba encima, rumbo del catalogo) y Salon 402 "
                             "hacia el norte", r2.metas, [0.0, math.pi])

            print("2. Encadenada, sin reubicar: Salon 403 -> Salon 401")
            n2 = len(r2.metas)
            estado, res = usuario.pedir("piso4_salon_403", "piso4_salon_401")
            comprueba("la mision se completa", estado == GoalStatus.STATUS_SUCCEEDED
                      and res is not None and res.exito,
                      f"(motivo {res.motivo_fallo if res else None!r})")
            comprobar_rumbos("robot2 sale del 402 al sur, a buscar al usuario al 403, y vuelve "
                             "al norte al 401", r2.metas[n2:], [0.0, math.pi])

            print("3. Los registros")
            regs = registros_de(registros)
            comprueba("hay un registro por mision", len(regs) == 2, f"({len(regs)})")
            for reg in regs[:2]:
                m = reg["metricas"]
                comprueba(f"{reg['solicitud']['destino_id']}: exito y llegada de 0,20 m",
                          m["exito"] and m["error_llegada_m"] is not None
                          and abs(m["error_llegada_m"] - ERROR_LLEGADA_M) < 0.05,
                          f"(error {m['error_llegada_m']}, tolerancia {m['tolerancia_llegada_m']})")
            comprueba("la asignacion del registro lleva los niveles 3 y 4",
                      bool(regs) and regs[0]["asignacion"].get("3") == "robot1"
                      and regs[0]["asignacion"].get("4") == "robot2",
                      f"({regs[0]['asignacion'] if regs else None})")

            print("4. Cancelacion: robot2 vuelve a la escalera del piso 4")
            n2 = len(r2.metas)
            r2.meta_recibida.clear()
            # Se cancela cuando robot2 recibe la segunda meta (la del 403).
            evento = threading.Event()

            def vigilar():
                while len(r2.metas) < n2 + 2:
                    time.sleep(0.01)
                evento.set()
            threading.Thread(target=vigilar, daemon=True).start()
            estado, res = usuario.pedir("piso4_salon_401", "piso4_salon_403", cancelar_si=evento)
            comprueba("la mision termina cancelada", estado == GoalStatus.STATUS_CANCELED,
                      f"(estado {estado})")
            ultima = r2.metas[-1] if len(r2.metas) > n2 else None
            comprueba("la ultima meta de robot2 es su escalera (24,39, 0,82)",
                      ultima is not None and math.hypot(ultima[0] - 24.39, ultima[1] - 0.82) < 1e-6,
                      f"({ultima})")

            print("5. Sin pose del agente no se acepta la llegada")
            r1.mudo = True
            time.sleep(2.5)
            estado, res = usuario.pedir("piso3_salon_301", "piso3_salon_302")
            comprueba("la mision falla", res is not None and not res.exito,
                      f"(motivo {res.motivo_fallo if res else None!r})")
            comprueba("y dice que no hay pose del agente",
                      res is not None and "no hay la pose del agente" in res.motivo_fallo)
            r1.mudo = False
        finally:
            desmontar(ejecutor)


def con_simulacion(clase):
    with tempfile.TemporaryDirectory() as registros:
        robots, usuario, _coord, ejecutor = montar("simulacion", registros, clase)
        try:
            print("6. Control: el mismo escenario con condicion:=simulacion, que lee /odom")
            estado, res = usuario.pedir("piso3_salon_302", "piso4_salon_402")
            comprueba("con /odom en otro marco, la llegada al Salon 302 se rechaza",
                      res is not None and not res.exito and "/odom lo situa a" in res.motivo_fallo,
                      f"(motivo {res.motivo_fallo if res else None!r})")
        finally:
            desmontar(ejecutor)


def con_inercia(clase):
    """Nav2 responde SUCCEEDED con el vehiculo aun rodando (2026-10-13).

    Con la pose del agente a 2 Hz, verificar la llegada en el instante de
    SUCCEEDED es mirar el vehiculo 0,5 a 1 m antes de donde se para.
    """
    with tempfile.TemporaryDirectory() as registros:
        robots, usuario, _coord, ejecutor = montar("hardware", registros, clase)
        for r in robots.values():
            r.inercia_m = INERCIA_M
        try:
            print("7. Con inercia: SUCCEEDED a 0,65 m y 0,45 m mas rodando (racey, 7-oct)")
            estado, res = usuario.pedir("piso3_salon_302", "piso4_salon_402")
            comprueba("la llegada se verifica con el vehiculo asentado, no al recibir SUCCEEDED",
                      estado == GoalStatus.STATUS_SUCCEEDED and res is not None and res.exito,
                      f"(estado {estado}, motivo {res.motivo_fallo if res else None!r})")
        finally:
            desmontar(ejecutor)


def con_media_vuelta(clase):
    """La cadena completa: el coordinador pide la media vuelta al agente y despues navega.

    Hasta el 2026-10-13 ninguna prueba la recorria: los robots falsos no
    ofrecian el servicio, el coordinador avisaba y dejaba la vuelta a Nav2, y en
    el campo la maniobra se lanzo a mano con herramientas/media_vuelta.py.
    """
    with tempfile.TemporaryDirectory() as registros:
        robots, usuario, _coord, ejecutor = montar("hardware", registros, clase,
                                                   con_media_vuelta=True)
        r1, r2 = robots["robot1"], robots["robot2"]
        try:
            print("8. Media vuelta del agente, pedida por el coordinador: Salon 302 -> Salon 402")
            estado, res = usuario.pedir("piso3_salon_302", "piso4_salon_402")
            comprueba("la mision se completa", estado == GoalStatus.STATUS_SUCCEEDED
                      and res is not None and res.exito,
                      f"(estado {estado}, motivo {res.motivo_fallo if res else None!r})")
            comprueba("robot1: meta al 302 (al frente), media vuelta y meta a la escalera (detras)",
                      r1.eventos == ["meta", "media_vuelta", "meta"], f"({r1.eventos})")
            comprueba("robot2: sin media vuelta (escalera a 0,39 m y el 402 al frente)",
                      r2.eventos == ["meta", "meta"], f"({r2.eventos})")
        finally:
            desmontar(ejecutor)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    clase = cargar_coordinador(ruta)
    con_hardware(clase)
    con_inercia(clase)
    con_media_vuelta(clase)
    con_simulacion(clase)
    print("=" * 62)
    if FALLOS:
        print(f"{len(FALLOS)} comprobaciones FALLAN de {OK + len(FALLOS)}")
        return 1
    print(f"Todas las comprobaciones pasan ({OK}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
