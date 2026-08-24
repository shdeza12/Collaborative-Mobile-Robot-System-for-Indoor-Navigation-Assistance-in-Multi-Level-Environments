#!/usr/bin/env python3
"""Round-trip real de coordinacion_msgs: se publica, se recibe y se compara.

No basta con que compile. Esto comprueba que los cuatro tipos viajan por DDS
con los valores intactos, incluida la accion completa (goal, feedback, result).

Se ejecuta a mano, no con colcon test, porque necesita un grafo ROS vivo:

    cd ~/deepracer_sim_ws && source install/setup.bash
    python3 src/aws-deepracer/coordinacion_msgs/test/prueba_round_trip.py

La razon de que esto exista y no sea un colcon test: el paquete tiene que
compilar y funcionar en DOS distribuciones -Humble en el PC, Jazzy en la tarjeta
del carro-. Cuando se compile en Jazzy hay que volver a correr este archivo:
que genere los headers no prueba que rmw los transporte igual en las dos.

Ultima ejecucion en Humble: 2026-08-24, 18 de 18 comprobaciones OK, con los 16
puntos reales de puntos_interes.yaml.
"""
import os
import threading
import time

import rclpy
import yaml
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy

from coordinacion_msgs.msg import (
    EstadoRobot, PuntoInteres, ListaPuntosInteres, EstadoMision,
)
from coordinacion_msgs.action import GuiarUsuario

# El YAML real del proyecto, no uno inventado: la prueba del catalogo carga los
# destinos que de verdad se van a publicar.
YAML_PUNTOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "deepracer_bringup", "config", "puntos_interes.yaml",
)

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def punto_ejemplo():
    p = PuntoInteres()
    p.id = "piso2_escalera"
    p.nombre = "Escaleras"
    p.nivel = 2
    p.es_transferencia = True
    p.pose.position.x = -21.50
    p.pose.position.y = -9.03
    p.pose.orientation.z = 1.0   # yaw = pi
    p.pose.orientation.w = 0.0
    return p


def main():
    rclpy.init()
    n = Node("prueba_coordinacion")

    print("\n1. Constantes declaradas en los .msg")
    check("EstadoRobot LIBRE/NAVEGANDO/EN_TRANSFERENCIA/ERROR = 0/1/2/3",
          (EstadoRobot.LIBRE, EstadoRobot.NAVEGANDO,
           EstadoRobot.EN_TRANSFERENCIA, EstadoRobot.ERROR) == (0, 1, 2, 3))
    check("EstadoMision INACTIVA..FALLIDA = 0..5",
          (EstadoMision.INACTIVA, EstadoMision.TRAMO_1, EstadoMision.TRANSFERENCIA,
           EstadoMision.TRAMO_2, EstadoMision.COMPLETADA, EstadoMision.FALLIDA)
          == (0, 1, 2, 3, 4, 5))

    print("\n2. EstadoRobot por DDS")
    recibido = {}
    n.create_subscription(EstadoRobot, "/robot2/estado_robot",
                          lambda m: recibido.setdefault("er", m), 10)
    pub = n.create_publisher(EstadoRobot, "/robot2/estado_robot", 10)
    m = EstadoRobot()
    m.robot_id = "robot2"
    m.nivel = 2
    m.estado = EstadoRobot.EN_TRANSFERENCIA
    m.detalle = "en la escalera del piso 2"
    m.pose.header.frame_id = "robot2/map"
    m.pose.pose.position.x = -21.651215
    m.pose.pose.position.y = -9.144906
    m.stamp = n.get_clock().now().to_msg()

    t0 = time.time()
    while "er" not in recibido and time.time() - t0 < 5.0:
        pub.publish(m)
        rclpy.spin_once(n, timeout_sec=0.1)
    r = recibido.get("er")
    check("llega el mensaje", r is not None)
    if r:
        check("robot_id, nivel, estado intactos",
              (r.robot_id, r.nivel, r.estado) == ("robot2", 2, 2))
        check("pose con frame_id y float64 sin perdida",
              r.pose.header.frame_id == "robot2/map"
              and r.pose.pose.position.x == -21.651215,
              f"x={r.pose.pose.position.x!r}")

    print("\n3. EstadoMision con PuntoInteres anidado")
    rec2 = {}
    n.create_subscription(EstadoMision, "/estado_mision",
                          lambda mm: rec2.setdefault("em", mm), 10)
    pub2 = n.create_publisher(EstadoMision, "/estado_mision", 10)
    em = EstadoMision()
    em.mision_id = "m-001"
    em.etapa = EstadoMision.TRANSFERENCIA
    em.robot_activo = "robot2"
    em.destino_actual = punto_ejemplo()
    em.distancia_restante = 1.344
    # Con acentos y n-tilde a proposito: el texto va tal cual a la HRI, y un
    # problema de codificacion en DDS tiene que aparecer aqui, no en la demo.
    em.mensaje_usuario = "Espere aquí, el robot del piso 1 está en camino. Señalice."

    t0 = time.time()
    while "em" not in rec2 and time.time() - t0 < 5.0:
        pub2.publish(em)
        rclpy.spin_once(n, timeout_sec=0.1)
    r2 = rec2.get("em")
    check("llega el mensaje", r2 is not None)
    if r2:
        check("PuntoInteres anidado sobrevive",
              r2.destino_actual.id == "piso2_escalera"
              and r2.destino_actual.es_transferencia is True
              and abs(r2.destino_actual.pose.position.x + 21.50) < 1e-9)
        check("texto en espanol con acentos y n-tilde",
              r2.mensaje_usuario == em.mensaje_usuario,
              repr(r2.mensaje_usuario))

    print("\n4. ListaPuntosInteres: el catalogo real, y latched de verdad")
    # Lo que importa aqui no es que el arreglo viaje, sino que un suscriptor que
    # se conecta DESPUES de la unica publicacion reciba el catalogo igual. Ese es
    # el caso real: el coordinador arranca con la simulacion, y la HRI aparece
    # cuando el usuario abre el navegador, minutos mas tarde. Si el latching no
    # funciona, la HRI se queda con los desplegables vacios y nadie se entera
    # hasta la demostracion.
    with open(YAML_PUNTOS, encoding="utf-8") as f:
        datos = yaml.safe_load(f)["puntos"]

    lista = ListaPuntosInteres()
    lista.origen = "deepracer_bringup/config/puntos_interes.yaml"
    lista.stamp = n.get_clock().now().to_msg()
    for d in datos:
        p = PuntoInteres()
        p.id = d["id"]
        p.nombre = d["nombre"]
        p.nivel = int(d["nivel"])
        p.es_transferencia = bool(d.get("es_transferencia", False))
        p.pose.position.x = float(d["pose"]["x"])
        p.pose.position.y = float(d["pose"]["y"])
        lista.puntos.append(p)
    print(f"      catalogo cargado del YAML: {len(lista.puntos)} puntos")

    qos_latched = QoSProfile(depth=1,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             history=HistoryPolicy.KEEP_LAST)
    pub3 = n.create_publisher(ListaPuntosInteres, "/coordinacion/puntos_interes",
                              qos_latched)
    pub3.publish(lista)          # UNA sola vez, y antes de que exista el suscriptor
    for _ in range(10):
        rclpy.spin_once(n, timeout_sec=0.05)

    # El suscriptor nace ahora, tarde y a proposito.
    rec3 = {}
    n.create_subscription(ListaPuntosInteres, "/coordinacion/puntos_interes",
                          lambda mm: rec3.setdefault("lp", mm), qos_latched)
    t0 = time.time()
    while "lp" not in rec3 and time.time() - t0 < 5.0:
        rclpy.spin_once(n, timeout_sec=0.1)
    r3 = rec3.get("lp")

    check("un suscriptor tardio recibe el catalogo sin republicar", r3 is not None)
    if r3:
        check("llegan los puntos completos",
              len(r3.puntos) == len(lista.puntos),
              f"{len(r3.puntos)} de {len(lista.puntos)}")
        check("los ids sobreviven en orden",
              [p.id for p in r3.puntos] == [p.id for p in lista.puntos])
        transf = [p.id for p in r3.puntos if p.es_transferencia]
        check("los puntos de transferencia siguen marcados", len(transf) >= 1,
              str(transf))
        niveles = sorted({p.nivel for p in r3.puntos})
        check("hay destinos de los dos niveles", niveles == [1, 2], str(niveles))

    print("\n5. GuiarUsuario: goal -> feedback -> result")
    feedbacks = []

    def ejecutar(goal_handle):
        fb = GuiarUsuario.Feedback()
        fb.estado = EstadoMision()
        fb.estado.mision_id = "m-002"
        fb.estado.etapa = EstadoMision.TRAMO_1
        fb.estado.destino_actual = punto_ejemplo()
        fb.estado.mensaje_usuario = "Siguiendo al robot 1."
        goal_handle.publish_feedback(fb)
        time.sleep(0.3)
        goal_handle.succeed()
        res = GuiarUsuario.Result()
        res.exito = True
        res.tiempo_total_s = 42.5
        res.num_relevos = 1
        res.motivo_fallo = ""
        return res

    servidor_node = Node("servidor_prueba")
    ActionServer(servidor_node, GuiarUsuario, "guiar_usuario", ejecutar)
    cliente = ActionClient(n, GuiarUsuario, "guiar_usuario")

    ex = rclpy.executors.MultiThreadedExecutor()
    ex.add_node(n)
    ex.add_node(servidor_node)
    hilo = threading.Thread(target=ex.spin, daemon=True)
    hilo.start()

    check("el servidor de accion aparece", cliente.wait_for_server(timeout_sec=5.0))

    goal = GuiarUsuario.Goal()
    goal.origen_id = "piso1_entrada"
    goal.destino_id = "piso2_escalera"
    fut = cliente.send_goal_async(goal, feedback_callback=lambda f: feedbacks.append(f))
    t0 = time.time()
    while not fut.done() and time.time() - t0 < 8.0:
        time.sleep(0.05)
    gh = fut.result() if fut.done() else None
    check("el goal es aceptado", gh is not None and gh.accepted)

    if gh and gh.accepted:
        rf = gh.get_result_async()
        t0 = time.time()
        while not rf.done() and time.time() - t0 < 8.0:
            time.sleep(0.05)
        check("llega el result", rf.done())
        if rf.done():
            res = rf.result().result
            check("result: exito, 42.5 s, 1 relevo",
                  res.exito is True and abs(res.tiempo_total_s - 42.5) < 1e-6
                  and res.num_relevos == 1,
                  f"({res.exito}, {res.tiempo_total_s}, {res.num_relevos})")
        check("llego feedback con EstadoMision dentro",
              len(feedbacks) >= 1
              and feedbacks[0].feedback.estado.destino_actual.id == "piso2_escalera",
              f"{len(feedbacks)} feedback(s)")

    ex.shutdown(timeout_sec=1.0)
    print("\n" + "=" * 60)
    if fallos:
        print(f"FALLAN {len(fallos)}: {fallos}")
    else:
        print("Todas las comprobaciones pasan.")
    print("=" * 60)


main()
