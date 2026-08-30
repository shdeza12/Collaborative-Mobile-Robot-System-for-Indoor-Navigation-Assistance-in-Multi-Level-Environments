#!/usr/bin/env python3
"""Banco del tiempo de asignacion (RF-22). Es el pendiente 7 de la §9 del
protocolo y la unica forma de dar la cifra de una de las cuatro metricas de OE4.

    source /opt/ros/humble/setup.bash
    source ~/deepracer_sim_ws/install/setup.bash
    python3 herramientas/banco_tiempo_asignacion.py

NO se lanza Gazebo, ni Nav2, ni ningun robot. Si hay una simulacion corriendo,
apagarla o cambiar de ROS_DOMAIN_ID: este banco quiere el coordinador SOLO.


POR QUE ESTE BANCO EXISTE
-------------------------
El protocolo define

    t_asignacion = t_robot_activo - t_solicitud

sobre dos mensajes de '/coordinacion/estado_mision' leidos del bag. Y del bag esa
resta vale CERO siempre, se ejecute lo que se ejecute. No es un fallo del
coordinador: es el instrumento.

  - 'ros2 bag record --use-sim-time' sella cada mensaje con el reloj de
    simulacion.
  - el reloj de simulacion solo avanza cuando llega un mensaje de '/clock', y
    'gazebo_ros_init' lo publica a 10 Hz.
  - luego TODO sello del bag esta cuantizado a 100 ms.
  - y asignar es una busqueda en memoria sobre 31 puntos, tres ordenes de
    magnitud por debajo de un tick.

Las dos marcas caen en el mismo tick y la resta da 0,0 s. Eso no mide el evento:
mide el reloj. Se comprobo dos veces, en misiones distintas y con meses de
codigo distinto en medio -247,6000 s las dos marcas el 29-ago; los seis
intervalos de la mision del 30-ago, todos multiplos exactos de 0,1 s-.

HUBO UN PRIMER DEFECTO, DISTINTO DE ESTE, Y CONVIENE NO CONFUNDIRLOS. Hasta el
29-ago el coordinador fijaba 'etapa' y 'robot_activo' en la misma llamada y
publicaba UNA vez, asi que no existia ningun mensaje entre "llego la solicitud"
y "ya hay agente". Aquello si era de software y se corrigio con la marca
RECIBIDA. Este banco existe porque corregirlo fue necesario pero NO suficiente:
las dos marcas ya son dos mensajes, y siguen cayendo en el mismo tick.

Subir la frecuencia de '/clock' no es la salida. Para resolver el evento en dos
digitos harian falta unos 10 kHz, y eso compite por CPU con la simulacion justo
donde RNF-06 exige RTF >= 0,99: se cambiaria una metrica inmedible por dos
metricas sesgadas.


QUE MIDE, EXACTAMENTE
---------------------
El reloj es 'time.perf_counter_ns()' -monotono, resolucion de nanosegundos- y se
lee DENTRO del proceso del coordinador, envolviendo su metodo '_marcar'. Se
envuelve '_marcar' y no '_publicar_estado' a proposito: '_publicar_estado' lo
llama tambien el latido de 1 Hz, y contar latidos como marcas mezclaria dos
cosas distintas.

La lectura se toma AL VOLVER de '_marcar', que es cuando el mensaje ya se ha
publicado. Asi el intervalo medido es exactamente el que define el protocolo:
del instante en que se publica RECIBIDA al instante en que se publica la primera
etapa con 'robot_activo' no vacio.

Queda DENTRO de la medida todo lo que el coordinador hace entre las dos marcas:
la publicacion del feedback, 'planificar()' entera -que es el aporte declarado
del proyecto- y el armado del mensaje de la primera etapa. Queda FUERA el
transporte DDS, y debe quedar fuera: cuanto tarda un mensaje en llegar a un
suscriptor no es tiempo de asignacion.

La mision aborta despues, al no encontrar 'navigate_to_pose'. No afecta a lo
medido, porque las dos marcas se publican antes de tocar ningun robot. Por eso
el banco baja 'espera_servidor_s' a 0,05 s: solo sirve para que el ciclo pase
rapido al siguiente par.
"""

import hashlib
import json
import os
import random
import statistics
import sys
import time

# La §3.2.2 fija ">= 30 invocaciones". Resumir 29 y publicarlo como si cumpliera
# es exactamente el numero que no vale, asi que 'resumen' se niega.
MINIMO_REPETICIONES = 30

# Con esto 'wait_for_server' desiste enseguida y el banco pasa al siguiente par.
# No entra en la medida: va despues de la segunda marca.
ESPERA_SERVIDOR_S = 0.05


def sha256_de(ruta):
    """Huella de un archivo. La cifra del banco solo vale para el catalogo con
    el que se midio, y sin huella nadie puede comprobar cual fue."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(65536), b""):
            h.update(trozo)
    return h.hexdigest()


def pares_alternados(catalogo, repeticiones, semilla=0):
    """Pares (origen_id, destino_id) alternando intra-nivel e inter-nivel.

    La §3.2.2 pide alternar, y no es cosmetica: 'planificar()' tiene dos ramas
    -la intra-nivel devuelve 2 tramos, la inter-nivel 4 y ademas busca los dos
    puntos de transferencia-. Medir una sola rama caracterizaria media funcion y
    se reportaria como si fuera la entera.

    El sorteo va con semilla para que el banco se pueda repetir. La semilla se
    anota en el informe.
    """
    por_nivel = {}
    for p in catalogo:
        por_nivel.setdefault(p["nivel"], []).append(p["id"])

    niveles = sorted(n for n, ids in por_nivel.items() if len(ids) >= 2)
    if len(niveles) < 2:
        raise ValueError(
            "Hacen falta al menos dos niveles con dos puntos cada uno para "
            "alternar pares intra e inter-nivel; el catalogo tiene "
            f"{len(niveles)}: {niveles}. Sin pares inter-nivel el banco medi"
            "ria solo la rama corta de planificar() y lo reportaria como el "
            "tiempo de asignacion entero.")

    rnd = random.Random(semilla)
    pares = []
    for i in range(repeticiones):
        if i % 2 == 0:                                    # intra-nivel
            nivel = niveles[(i // 2) % len(niveles)]      # y alternando nivel
            o, d = rnd.sample(por_nivel[nivel], 2)
        else:                                             # inter-nivel
            a, b = rnd.sample(niveles, 2)
            o = rnd.choice(por_nivel[a])
            d = rnd.choice(por_nivel[b])
        pares.append((o, d))
    return pares


def resumen(muestras_us):
    """Mediana, maximo y minimo en microsegundos.

    NO devuelve la media, y la ausencia es deliberada: la §3.2.2 la prohibe
    porque la distribucion tiene cola por el planificador de Python. Una media
    arrastrada por un solo valor atipico describiria una asignacion que no
    ocurre casi nunca.
    """
    if len(muestras_us) < MINIMO_REPETICIONES:
        raise ValueError(
            f"Solo hay {len(muestras_us)} muestras y la §3.2.2 exige "
            f"{MINIMO_REPETICIONES}. Una cifra con menos no cumple el "
            "protocolo, y publicarla como si cumpliera es peor que no tenerla.")
    if any(m <= 0.0 for m in muestras_us):
        raise ValueError(
            "Hay muestras en cero o negativas. Un cero es justo el sintoma que "
            "este banco existe para no repetir: significa que se esta midiendo "
            "con un reloj cuantizado y no con 'perf_counter_ns'. No se resume.")
    return {
        "n": len(muestras_us),
        "mediana_us": statistics.median(muestras_us),
        "maximo_us": max(muestras_us),
        "minimo_us": min(muestras_us),
    }


# --------------------------------------------------------------------- el banco
# Todo lo de abajo necesita ROS. Se importa dentro de main() para que la parte
# pura de arriba se pueda probar sin el workspace sourceado.

def main():
    import rclpy
    from rclpy.action import ActionClient
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    import threading

    from coordinacion.coordinador import Coordinador
    from coordinacion_msgs.action import GuiarUsuario
    from coordinacion_msgs.msg import EstadoMision

    repeticiones = int(sys.argv[1]) if len(sys.argv) > 1 else MINIMO_REPETICIONES
    semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 20260830

    # LA SEMILLA VA EN EL NOMBRE. Con un nombre fijo, la segunda corrida pisa la
    # primera sin decir nada, y una replicacion -que es justo lo que da valor a
    # este banco- se pierde en el acto de hacerla. Paso el 2026-08-30 con las dos
    # primeras corridas y por eso esta escrito asi.
    #
    # Y SE COMPRUEBA AQUI, ANTES DE LEVANTAR NADA. Comprobarlo al final -que fue
    # el primer intento- hace correr las 30 misiones enteras para luego negarse a
    # escribir, y ademas obliga a salir con el ejecutor girando, que termina en
    # 'terminate called without an active exception' y un volcado de nucleo.
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destino_json = os.path.join(raiz, "Documentos", "Evidencia", "registros",
                                f"S21_banco_asignacion_s{semilla}.json")
    if os.path.exists(destino_json):
        sys.exit(f"Ya existe {destino_json}. Se niega a pisar una medida "
                 f"anterior: borrarla a mano si de verdad sobra, o correr el "
                 f"banco con otra semilla.")

    rclpy.init(args=[
        "--ros-args",
        "-p", f"espera_servidor_s:={ESPERA_SERVIDOR_S}",
        "-p", "use_sim_time:=false",
        "-p", "prefijo_mision:=banco",
    ])
    coordinador = Coordinador()

    # Salvaguarda: si alguien deja una simulacion viva, el nodo tomaria el
    # tiempo de '/clock' y volveriamos al cero cuantizado sin enterarnos.
    if coordinador.get_parameter("use_sim_time").value:
        sys.exit("use_sim_time esta en true: el banco mide sobre reloj de pared.")

    # ---- la instrumentacion, envolviendo '_marcar' (ver cabecera) ----
    marcas = []
    _marcar_original = coordinador._marcar

    def _marcar_cronometrado(etapa, robot, punto, mensaje, mision_id):
        _marcar_original(etapa, robot, punto, mensaje, mision_id)
        marcas.append((time.perf_counter_ns(), mision_id, etapa, robot))

    coordinador._marcar = _marcar_cronometrado

    ejecutor = MultiThreadedExecutor()
    ejecutor.add_node(coordinador)
    hilo = threading.Thread(target=ejecutor.spin, daemon=True)
    hilo.start()

    cliente_nodo = Node("banco_tiempo_asignacion")
    cliente = ActionClient(cliente_nodo, GuiarUsuario,
                           "/coordinacion/guiar_usuario")
    ejecutor.add_node(cliente_nodo)
    if not cliente.wait_for_server(timeout_sec=10.0):
        sys.exit("El coordinador no ofrece guiar_usuario.")

    catalogo = coordinador.catalogo
    nivel_de = {p["id"]: p["nivel"] for p in catalogo}
    pares = pares_alternados(catalogo, repeticiones, semilla)

    print(f"Banco del tiempo de asignacion: {repeticiones} misiones, "
          f"semilla {semilla}, reloj de pared.\n")

    filas = []
    for i, (origen, destino) in enumerate(pares, 1):
        antes = len(marcas)
        meta = GuiarUsuario.Goal()
        meta.origen_id, meta.destino_id = origen, destino
        fut = cliente.send_goal_async(meta)
        while not fut.done():
            time.sleep(0.005)
        gh = fut.result()
        if not gh.accepted:
            sys.exit(f"El coordinador rechazo el goal {origen} -> {destino}.")
        fut_res = gh.get_result_async()
        while not fut_res.done():
            time.sleep(0.005)

        nuevas = marcas[antes:]
        t_sol = next((t for t, _, e, _ in nuevas if e == EstadoMision.RECIBIDA),
                     None)
        t_act = next((t for t, _, e, r in nuevas
                      if e != EstadoMision.RECIBIDA and r), None)
        if t_sol is None or t_act is None:
            sys.exit(f"Faltan marcas en la mision {origen} -> {destino}: "
                     f"{[(e, r) for _, _, e, r in nuevas]}")

        us = (t_act - t_sol) / 1000.0
        tipo = "intra" if nivel_de[origen] == nivel_de[destino] else "inter"
        filas.append({"i": i, "origen": origen, "destino": destino,
                      "tipo": tipo, "t_asignacion_us": us})
        print(f"  {i:3d}/{repeticiones}  {tipo}  {us:9.1f} us   "
              f"{origen} -> {destino}")

    todas = [f["t_asignacion_us"] for f in filas]
    r = resumen(todas)
    por_tipo = {}
    for t in ("intra", "inter"):
        m = [f["t_asignacion_us"] for f in filas if f["tipo"] == t]
        if m:
            por_tipo[t] = {"n": len(m), "mediana_us": statistics.median(m),
                           "maximo_us": max(m)}

    informe = {
        "banco": "tiempo de asignacion (RF-22), protocolo §3.2.2",
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reloj": "time.perf_counter_ns(), dentro del proceso del coordinador",
        "entorno": "coordinador aislado, sin Gazebo ni Nav2, use_sim_time=false",
        "catalogo": coordinador.ruta_puntos,
        "catalogo_sha256": sha256_de(coordinador.ruta_puntos),
        "puntos_en_catalogo": len(catalogo),
        "semilla": semilla,
        "resumen_us": r,
        "por_tipo_us": por_tipo,
        "misiones": filas,
    }
    os.makedirs(os.path.dirname(destino_json), exist_ok=True)
    with open(destino_json, "w", encoding="utf-8") as f:
        json.dump(informe, f, indent=2, ensure_ascii=False)

    print(f"\n  n        {r['n']}")
    print(f"  mediana  {r['mediana_us']:.1f} us")
    print(f"  maximo   {r['maximo_us']:.1f} us")
    print(f"  minimo   {r['minimo_us']:.1f} us")
    for t, v in por_tipo.items():
        print(f"  {t}: mediana {v['mediana_us']:.1f} us, "
              f"maximo {v['maximo_us']:.1f} us ({v['n']})")
    tick_us = 100_000.0
    print(f"\n  El maximo es {tick_us / r['maximo_us']:.0f} veces menor que un "
          f"tick de /clock (100 ms).")
    print(f"  -> {destino_json}")

    ejecutor.shutdown()
    coordinador.destroy_node()
    cliente_nodo.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
