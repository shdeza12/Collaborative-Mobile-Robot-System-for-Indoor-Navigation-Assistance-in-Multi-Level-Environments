#!/usr/bin/env python3
"""Un segundo coordinador no puede arrancar si ya hay uno sirviendo.

POR QUE EXISTE ESTA PRUEBA. El 2026-09-04 se perdio la campana de OE4 con dos
misiones caidas en 'Nav2 termino con estado 6'. La causa quedo medida ese mismo
dia con herramientas/diagnosticar_aborto_nav2.py:

  - 20 goals directos a /robot1/navigate_to_pose, en limpio: 0 abortos. Nav2 no
    aborta por su cuenta.
  - 8 pares de goals seguidos al MISMO servidor: 8 de 8 abortos del goal
    desplazado, entre 9 y 13 ms del segundo envio. navigate_to_pose atiende un
    goal a la vez y al desplazado lo termina en ABORTED.

Y aquel dia hubo dos coordinadores vivos a la vez -lo dejo escrito el propio
ROS 2 con 'There may be more than one action server'-, cada uno mandando su goal
al mismo Nav2. coordinador.py tiene un solo send_goal_async y ningun reintento,
asi que un coordinador no se pisa a si mismo: se pisaban dos.

De ahi el guardian. Y de ahi que esta prueba tenga DOS casos: uno que comprueba
que el segundo NO arranca, y otro que comprueba que el primero SI. Sin el
segundo caso, un guardian que se negara siempre pasaria por bueno.

No necesita Gazebo ni Nav2: el coordinador arranca solo -comprobado el
2026-09-04- porque sus clientes de navigate_to_pose no esperan a nadie hasta que
hay mision.

Uso, con el overlay ya sourceado:
    herramientas/prueba_guardian_coordinador.py
"""
import os
import signal
import subprocess
import sys
import tempfile
import time

ORDEN = ["ros2", "run", "coordinacion", "coordinador", "--ros-args",
         "-p", "use_sim_time:=true", "-p", "prefijo_mision:=PRUEBAGUARDIAN"]

# Lo que imprime el coordinador cuando ya esta sirviendo su accion.
SENAL_LISTO = "Coordinador listo"

PLAZO_ARRANQUE_S = 30.0
PLAZO_GUARDIAN_S = 30.0


def lanzar():
    log = tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False)
    p = subprocess.Popen(
        ORDEN, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        env=dict(os.environ, PYTHONUNBUFFERED="1"))
    return p, log.name


def leer(ruta):
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def esperar_listo(proc, ruta, plazo_s):
    fin = time.monotonic() + plazo_s
    while time.monotonic() < fin:
        if SENAL_LISTO in leer(ruta):
            return True
        if proc.poll() is not None:
            return False
        time.sleep(0.2)
    return False


def esperar_salida(proc, plazo_s):
    """Devuelve el codigo de salida, o None si sigue vivo pasado el plazo."""
    try:
        return proc.wait(timeout=plazo_s)
    except subprocess.TimeoutExpired:
        return None


def matar(proc):
    """Se mata al GRUPO, no al proceso.

    'ros2 run' no hace exec: deja un hijo. Un terminate() sobre el padre lo
    devuelve al init y el coordinador sigue sirviendo, invisible para quien crea
    haberlo parado. Es la misma trampa que dejo vivo al coordinador de las 14:10
    del 2026-09-04, y si esta prueba cayera en ella iria dejando coordinadores
    sueltos que harian fallar la corrida siguiente.
    """
    if proc is None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)


def coordinadores_vivos():
    """PIDs de los coordinadores en marcha.

    EL PATRON VA CON BARRA. 'ros2 run' hace exec a la ruta instalada, asi que el
    proceso vivo es '.../lib/coordinacion/coordinador --ros-args ...'. El patron
    con ESPACIO -'coordinacion coordinador'- no encuentra nada aunque haya tres
    corriendo: comprobado el 2026-09-04, con el coordinador de las 14:10 vivo y
    el pgrep devolviendo vacio. Los corchetes evitan que pgrep se encuentre a si
    mismo.
    """
    r = subprocess.run(["pgrep", "-f", "coordinacion[/]coordinador"],
                       capture_output=True, text=True)
    return [l for l in r.stdout.split() if l]


def esperar_sin_coordinadores(plazo_s):
    """Espera a que no quede ninguno. Devuelve los que sobrevivan al plazo."""
    fin = time.monotonic() + plazo_s
    while True:
        vivos = coordinadores_vivos()
        if not vivos or time.monotonic() >= fin:
            return vivos
        time.sleep(0.3)


def main():
    a = b = None
    log_a = log_b = None
    fallos = []

    sobrantes = coordinadores_vivos()
    if sobrantes:
        print(f"No se puede probar: ya hay {len(sobrantes)} coordinador(es) "
              f"vivo(s), PID {', '.join(sobrantes)}.\n"
              f"El caso 1 exige la maquina limpia. Paralos con:\n"
              f'    pkill -f "coordinacion[/]coordinador"', file=sys.stderr)
        return 2

    try:
        # --- Caso 1: el primero arranca. Sin esto, un guardian que se negara
        # --- siempre pasaria la prueba.
        print("Caso 1: un coordinador solo tiene que arrancar.")
        a, log_a = lanzar()
        if not esperar_listo(a, log_a, PLAZO_ARRANQUE_S):
            fallos.append(
                f"CASO 1: el primer coordinador no llego a '{SENAL_LISTO}' en "
                f"{PLAZO_ARRANQUE_S:.0f} s. Su salida:\n{leer(log_a)}")
            print("  FALLA\n")
            return 1
        print("  pasa: el primero esta sirviendo.\n")

        # --- Caso 2: el segundo, con el primero vivo, tiene que negarse.
        print("Caso 2: un segundo coordinador tiene que negarse a arrancar.")
        b, log_b = lanzar()
        codigo = esperar_salida(b, PLAZO_GUARDIAN_S)
        salida_b = leer(log_b)

        if codigo is None:
            fallos.append(
                f"CASO 2: el segundo coordinador SIGUE VIVO {PLAZO_GUARDIAN_S:.0f} s "
                f"despues. Con dos sirviendo, los goals se desplazan entre si y "
                f"Nav2 devuelve ABORTED. Su salida:\n{salida_b}")
        elif codigo == 0:
            fallos.append(
                f"CASO 2: el segundo coordinador salio con codigo 0. Tiene que "
                f"salir con codigo distinto de 0 para que quien lo lance se "
                f"entere. Su salida:\n{salida_b}")
        else:
            print(f"  pasa: el segundo salio con codigo {codigo}.")

        # El guardian no vale si para lograrlo se lleva por delante al que ya
        # estaba: eso convertiria un arranque de mas en una campana perdida.
        if a.poll() is not None:
            fallos.append(
                "CASO 2: el PRIMER coordinador murio. El guardian tiene que "
                "detener al recien llegado, nunca al que ya estaba sirviendo.")
        else:
            print("  pasa: el primero sigue vivo.")

        if not any(f.startswith("CASO 2") for f in fallos):
            # Que se niegue no basta: tiene que decir por que, o el operador
            # perdera el tiempo buscandolo donde no esta.
            if "guardian" not in salida_b.lower() and \
               "ya hay" not in salida_b.lower():
                fallos.append(
                    f"CASO 2: se nego, pero sin explicar por que. La salida "
                    f"tiene que nombrar al coordinador que ya estaba. "
                    f"Salida:\n{salida_b}")
            else:
                print("  pasa: explica el motivo.")
    finally:
        matar(b)
        matar(a)
        for r in (log_a, log_b):
            if r and os.path.exists(r):
                os.unlink(r)

    # Una prueba que deja coordinadores sueltos sabotea la corrida siguiente, que
    # es justo el fallo que se esta arreglando.
    #
    # Se sondea en vez de mirar una sola vez: proc.wait() vuelve cuando muere el
    # 'ros2 run', y su hijo tarda unas decimas mas en irse detras. Mirar al vuelo
    # daba un fallo de limpieza que no era tal.
    quedan = esperar_sin_coordinadores(10.0)
    if quedan:
        fallos.append(
            f"LIMPIEZA: quedaron {len(quedan)} coordinador(es) vivo(s) al "
            f"terminar, PID {', '.join(quedan)}. La prueba tiene que dejar la "
            f"maquina como la encontro.")

    print("\n--- veredicto ---")
    if fallos:
        for f in fallos:
            print(f"\n{f}")
        print("\nLA PRUEBA FALLA.")
        return 1
    print("PASA: el guardian deja arrancar al primero y detiene al segundo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
