#!/usr/bin/env python3
"""P1b — ¿puede UN proceso ejecutar acciones en dos ROS_DOMAIN_ID a la vez?

Es la prueba que decide si el coordinador puede hablar con robot1 (dominio 0)
y robot2 (dominio 2) sin tocar nada de las dos pilas.

POR QUE NO BASTA prueba_dos_dominios.py. Aquella comprueba pub/sub, y de ahi
no se sigue esto: una accion de ROS 2 no es un topico, son CINCO primitivas
-tres servicios y dos topicos- con perfiles de QoS propios y una negociacion
de goal, feedback y resultado. Que /odom cruce el limite de dominio no dice
nada de si NavigateToPose lo cruza.

Topologia reproducida, que es la de coordinador.py:

    servidor falso (ROS_DOMAIN_ID=0) --> /robot1/navigate_to_pose
    servidor falso (ROS_DOMAIN_ID=2) --> /robot2/navigate_to_pose
    este proceso: ctx0 -> cliente de robot1
                  ctx2 -> cliente de robot2
                  ctx0 -> SERVIDOR de la accion publica (la de la HRI)

La ultima linea no es de adorno: el coordinador no solo llama, tambien sirve.
Si servir y llamar en contextos distintos del mismo proceso se estorbaran, la
opcion de coordinador bi-contexto no vale, y mas vale saberlo antes de S24
que durante la campana.

No necesita Gazebo ni Nav2: los servidores son falsos y los lanza este mismo
guion como subprocesos, para que la prueba sea una sola orden.

Uso:
    herramientas/prueba_dos_dominios_accion.py
"""
import os
import subprocess
import sys
import tempfile
import threading
import time

import rclpy
from rclpy.action import ActionClient, ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.context import Context
from rclpy.executors import MultiThreadedExecutor
from nav2_msgs.action import NavigateToPose

DOMINIOS = {0: "robot1", 2: "robot2"}
ESPERA_SERVIDOR_S = 15.0
PLAZO_RESULTADO_S = 20.0
STATUS_SUCCEEDED = 4

SERVIDOR_FALSO = '''
import sys, time, rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose

class S(Node):
    def __init__(self, ns):
        super().__init__("nav_falso_" + ns)
        ActionServer(self, NavigateToPose,
                     "/" + ns + "/navigate_to_pose", self._ej)
    def _ej(self, gh):
        time.sleep(1.0)
        gh.succeed()
        return NavigateToPose.Result()

rclpy.init()
n = S(sys.argv[1])
try:
    rclpy.spin(n)
except KeyboardInterrupt:
    pass
'''


def esperar(futuro, plazo_s):
    """Sondeo, no spin_until_future_complete.

    El ejecutor de este contexto ya gira en su propio hilo; meter aqui un
    spin_until_future_complete pondria un segundo girador sobre el mismo
    contexto. Es el patron que usa coordinador.py.
    """
    fin = time.time() + plazo_s
    while time.time() < fin:
        if futuro.done():
            return futuro.result()
        time.sleep(0.05)
    return None


def main():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(SERVIDOR_FALSO)
        ruta_servidor = f.name

    procesos = []
    for dominio, ns in DOMINIOS.items():
        entorno = dict(os.environ, ROS_DOMAIN_ID=str(dominio))
        procesos.append(subprocess.Popen(
            [sys.executable, ruta_servidor, ns], env=entorno,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        print(f"servidor falso /{ns}/navigate_to_pose lanzado "
              f"en dominio {dominio}")

    contextos, nodos, clientes, ejecutores, hilos = {}, {}, {}, {}, []
    try:
        for dominio, ns in DOMINIOS.items():
            ctx = Context()
            ctx.init(domain_id=dominio)
            nodo = rclpy.create_node(f"p1b_dom{dominio}", context=ctx)
            clientes[ns] = ActionClient(
                nodo, NavigateToPose, f"/{ns}/navigate_to_pose",
                callback_group=ReentrantCallbackGroup())
            contextos[dominio], nodos[dominio] = ctx, nodo
            ejecutores[dominio] = MultiThreadedExecutor(context=ctx)
            ejecutores[dominio].add_node(nodo)

        # El coordinador tambien SIRVE. Se monta en el contexto del dominio 0,
        # que es donde estaria la HRI. Se usa NavigateToPose en lugar de
        # GuiarUsuario para no depender de que coordinacion_msgs este
        # compilado: lo que se prueba es que servir y llamar convivan, no el
        # tipo concreto del mensaje.
        ActionServer(
            nodos[0], NavigateToPose, "/coordinacion/prueba_publica",
            lambda gh: (gh.succeed(), NavigateToPose.Result())[1],
            callback_group=ReentrantCallbackGroup())

        for dominio in DOMINIOS:
            h = threading.Thread(target=ejecutores[dominio].spin, daemon=True)
            h.start()
            hilos.append(h)

        resultados = {}
        for dominio, ns in DOMINIOS.items():
            print(f"\n--- dominio {dominio} / {ns} ---")
            if not clientes[ns].wait_for_server(timeout_sec=ESPERA_SERVIDOR_S):
                print("el servidor de accion NO se ve")
                resultados[ns] = "NO SE VE EL SERVIDOR"
                continue
            print("servidor de accion visible")

            objetivo = NavigateToPose.Goal()
            objetivo.pose.header.frame_id = "map"
            objetivo.pose.pose.position.x = 1.0
            objetivo.pose.pose.orientation.w = 1.0

            t0 = time.perf_counter()
            gh = esperar(clientes[ns].send_goal_async(objetivo),
                         PLAZO_RESULTADO_S)
            if gh is None or not gh.accepted:
                print("goal NO aceptado")
                resultados[ns] = "GOAL NO ACEPTADO"
                continue
            print("goal aceptado")

            res = esperar(gh.get_result_async(), PLAZO_RESULTADO_S)
            if res is None:
                print("no llego el resultado")
                resultados[ns] = "SIN RESULTADO"
                continue
            dt = time.perf_counter() - t0
            print(f"resultado: status={res.status} en {dt:.2f} s")
            resultados[ns] = ("OK" if res.status == STATUS_SUCCEEDED
                              else f"status={res.status}")
    finally:
        # EL ORDEN DE CIERRE IMPORTA, y se aprendio fallando: apagar el
        # ejecutor y destruir nodos con los hilos de spin todavia vivos
        # aborta con 'terminate called without an active exception' DESPUES
        # de imprimir el veredicto. Un aborto tardio es peor que uno
        # temprano, porque no invalida el resultado y por eso se ignora.
        # En el coordinador significaria que Ctrl-C lo revienta en vez de
        # cerrarlo, y grabar_mision.sh cerraria el bag contra un muerto.
        for ctx in contextos.values():
            ctx.try_shutdown()
        for h in hilos:
            h.join(timeout=5.0)
        for nodo in nodos.values():
            nodo.destroy_node()
        for p in procesos:
            p.terminate()
        for p in procesos:
            p.wait(timeout=5)
        os.unlink(ruta_servidor)

    print("\n--- veredicto P1b ---")
    for ns, r in resultados.items():
        print(f"  {ns:<8} {r}")
    if len(resultados) == 2 and all(r == "OK" for r in resultados.values()):
        print("\nP1b PASA: un proceso ejecuta acciones en los dos dominios "
              "mientras sirve la suya.")
        return 0
    print("\nP1b FALLA: el coordinador bi-contexto no se sostiene.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
