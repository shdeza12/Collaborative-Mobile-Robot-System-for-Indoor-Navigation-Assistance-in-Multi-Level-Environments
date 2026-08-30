#!/usr/bin/env python3
"""P1 — un proceso, dos contextos rclpy, dos ROS_DOMAIN_ID.

Pregunta que decide la opcion D del bloqueo de dominios: ¿puede UN proceso
-el coordinador- hablar con robot1 (dominio 0) y robot2 (dominio 2) a la vez?

La prueba es autocontenida A PROPOSITO: no necesita Gazebo ni las dos pilas
levantadas, porque cada contexto publica lo suyo y escucha los DOS topicos.
Eso permite comprobar dos cosas y no una:

  1. Cada contexto recibe lo que se publica EN SU dominio.
  2. Cada contexto NO recibe lo del otro.

La 2 no es adorno. Si los dos contextos acabaran en el mismo dominio -por
ejemplo porque 'domain_id' se ignorase en silencio-, la prueba 1 pasaria
igual y la conclusion seria falsa. La fuga cruzada es lo que distingue
'funciona' de 'parece que funciona'.

Se usa nav_msgs/Odometry sobre /robotN/odom, que son el tipo y los nombres
reales, no un topico de juguete.
"""
import threading
import time

import rclpy
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from nav_msgs.msg import Odometry

DOMINIOS = {0: "robot1", 2: "robot2"}
ESPERA_DESCUBRIMIENTO_S = 3.0
DURACION_PUBLICACION_S = 3.0
PERIODO_S = 0.1

recibido = {}
_lock = threading.Lock()


def _contar(dominio_receptor, topico):
    with _lock:
        clave = (dominio_receptor, topico)
        recibido[clave] = recibido.get(clave, 0) + 1


def construir(dominio, ns_propio):
    ctx = Context()
    ctx.init(domain_id=dominio)
    nodo = rclpy.create_node(f"p1_dom{dominio}", context=ctx)

    pub = nodo.create_publisher(Odometry, f"/{ns_propio}/odom", 10)

    # Se suscribe a los DOS, incluido el propio: asi la fuga cruzada se ve.
    for ns_otro in DOMINIOS.values():
        nodo.create_subscription(
            Odometry, f"/{ns_otro}/odom",
            lambda msg, d=dominio, t=ns_otro: _contar(d, t), 10)

    ejecutor = SingleThreadedExecutor(context=ctx)
    ejecutor.add_node(nodo)
    return ctx, nodo, pub, ejecutor


def main():
    piezas = {}
    for dominio, ns in DOMINIOS.items():
        piezas[dominio] = construir(dominio, ns)
        ctx = piezas[dominio][0]
        leido = (ctx.get_domain_id()
                 if hasattr(ctx, "get_domain_id") else "sin API")
        print(f"contexto creado: pedido domain_id={dominio}, "
              f"el contexto declara {leido}")

    hilos = []
    for dominio in DOMINIOS:
        ejecutor = piezas[dominio][3]
        h = threading.Thread(target=ejecutor.spin, daemon=True)
        h.start()
        hilos.append(h)

    print(f"\nesperando {ESPERA_DESCUBRIMIENTO_S} s de descubrimiento...")
    time.sleep(ESPERA_DESCUBRIMIENTO_S)

    print(f"publicando {DURACION_PUBLICACION_S} s en los dos dominios...")
    enviados = {d: 0 for d in DOMINIOS}
    fin = time.time() + DURACION_PUBLICACION_S
    while time.time() < fin:
        for dominio in DOMINIOS:
            msg = Odometry()
            msg.header.frame_id = f"dom{dominio}"
            piezas[dominio][2].publish(msg)
            enviados[dominio] += 1
        time.sleep(PERIODO_S)

    time.sleep(1.0)

    print("\n--- recibido ---")
    print(f"{'receptor':<12} {'topico':<16} {'mensajes':>9}  veredicto")
    fallos = []
    for dominio, ns_propio in DOMINIOS.items():
        for ns_otro in DOMINIOS.values():
            n = recibido.get((dominio, ns_otro), 0)
            propio = (ns_otro == ns_propio)
            if propio:
                ok = n > 0
                esperado = "propio: debe llegar"
            else:
                ok = n == 0
                esperado = "ajeno: NO debe llegar"
            if not ok:
                fallos.append((dominio, ns_otro, n, esperado))
            print(f"dominio {dominio:<4} /{ns_otro}/odom{'':<4} {n:>9}  "
                  f"{'OK ' if ok else 'MAL'} ({esperado})")

    print(f"\nenviados: {enviados}")

    # EL ORDEN DE CIERRE NO ES INDIFERENTE. La primera version hacia
    # shutdown() del ejecutor, destroy_node() y try_shutdown() del contexto,
    # con los hilos de spin todavia vivos, y abortaba con
    # 'terminate called without an active exception' DESPUES de imprimir el
    # veredicto. Un aborto tardio es peor que uno temprano: no invalida el
    # resultado y por eso es facil ignorarlo, pero en el coordinador
    # significaria que Ctrl-C revienta el proceso en vez de cerrarlo.
    # Orden correcto: apagar el contexto -eso hace que spin() retorne-, juntar
    # los hilos, y solo entonces destruir los nodos.
    for dominio in DOMINIOS:
        piezas[dominio][0].try_shutdown()
    for h in hilos:
        h.join(timeout=5.0)
    hilos_vivos = [h for h in hilos if h.is_alive()]
    for dominio in DOMINIOS:
        piezas[dominio][1].destroy_node()

    if hilos_vivos:
        print(f"AVISO: {len(hilos_vivos)} hilo(s) de spin no terminaron en 5 s")

    print()
    if fallos:
        print("P1 FALLA. La opcion D no se sostiene tal cual:")
        for d, t, n, esperado in fallos:
            print(f"  dominio {d} vio {n} de /{t}/odom — {esperado}")
        return 1
    print("P1 PASA: un proceso habla en los dos dominios y no hay fuga cruzada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
