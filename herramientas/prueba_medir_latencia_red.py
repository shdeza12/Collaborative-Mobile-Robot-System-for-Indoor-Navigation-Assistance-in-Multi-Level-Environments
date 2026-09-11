#!/usr/bin/env python3
"""Banco de medir_latencia_red.py. No necesita ROS ni red.

Lo que se comprueba aqui es el JUICIO, que es la parte que puede equivocarse en
silencio: el percentil, el conteo de perdidas, y sobre todo las cuatro razones
para NO dar veredicto. Un medidor que da un numero bonito cuando el eco corre en
la misma maquina es peor que ninguno, porque nadie lo mira dos veces.

    python3 herramientas/prueba_medir_latencia_red.py
"""
import importlib.util
import os
import sys
from types import SimpleNamespace

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "medir_latencia_red.py")

# El modulo importa rclpy y std_msgs en la cabecera. En el portatil estan, pero
# esta prueba tiene que poder correr sin sourcear nada, asi que se ponen dobles
# minimos si faltan. No se parchea nada mas: lo que se ejercita es codigo real.
for nombre, atributos in (("rclpy", ["init", "shutdown", "spin", "spin_once", "ok"]),
                          ("rclpy.node", ["Node"]),
                          ("std_msgs.msg", ["Header"]),
                          ("std_msgs", [])):
    if nombre in sys.modules:
        continue
    try:
        importlib.import_module(nombre)
    except ImportError:
        mod = SimpleNamespace(**{a: (object if a == "Node" or a == "Header"
                                     else (lambda *a, **k: None))
                                 for a in atributos})
        sys.modules[nombre] = mod

_spec = importlib.util.spec_from_file_location("medir_latencia_red", RUTA)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def nodo_falso(rtts, enviados=None, host="portatil", ecos=("robot2",),
               duplicados=0, desconocidos=0):
    """Un doble del Emisor con solo lo que analizar() lee."""
    rtt = {i + 1: v for i, v in enumerate(rtts)}
    return SimpleNamespace(
        rtt_ms=rtt,
        seq=enviados if enviados is not None else len(rtts),
        host=host,
        ecos=set(ecos),
        duplicados=duplicados,
        desconocidos=desconocidos,
    )


ARGS = SimpleNamespace(hz=10.0, relleno=240, etiqueta="prueba", n=600,
                       salida=None)


def main():
    print("\n1. percentil por rango mas cercano")
    v = [float(i) for i in range(1, 101)]          # 1..100
    check("p95 de 1..100 = 95", M.percentil(v, 95) == 95.0,
          str(M.percentil(v, 95)))
    check("p100 de 1..100 = 100", M.percentil(v, 100) == 100.0)
    check("p95 de una sola muestra = esa muestra", M.percentil([7.0], 95) == 7.0)
    check("p95 de lista vacia = None", M.percentil([], 95) is None)
    # Este fija la DIRECCION del redondeo, y hace falta: con n=100 o n=20 el
    # rango sale entero y truncar hacia abajo da el mismo resultado que
    # redondear hacia arriba. Con n=10, ceil(9,5)=10 y floor(9,5)=9, o sea 10,0
    # contra 9,0. Sin esta linea, cambiar ceil por floor pasaba el banco entero:
    # detectado mutando el codigo el 2026-09-11. Hacia arriba es lo que toca —un
    # p95 nunca debe quedar por debajo del 95 % de las muestras—.
    check("p95 de 1..10 = 10, no 9 (redondea hacia arriba)",
          M.percentil([float(i) for i in range(1, 11)], 95) == 10.0,
          str(M.percentil([float(i) for i in range(1, 11)], 95)))
    # Con 20 muestras, ceil(0,95*20)=19 -> la 19a. Es exactamente por esto que
    # MINIMO_MUESTRAS existe: con pocas, el p95 es una muestra suelta.
    check("p95 de 1..20 = 19", M.percentil([float(i) for i in range(1, 21)], 95) == 19.0)

    print("\n2. el caso que cumple")
    inf = M.analizar(nodo_falso([5.0] * 150), ARGS)
    check("veredicto CUMPLE", inf["veredicto"] == "CUMPLE", inf["motivo"])
    check("perdida 0 %", inf["perdida_pct"] == 0.0)
    check("mediana 5 ms", inf["mediana_ms"] == 5.0)
    check("lleva el requisito y la etiqueta",
          inf["requisito"] == "RF-15" and inf["etiqueta"] == "prueba")
    check("deja constancia de los dos umbrales usados",
          inf["umbral_mediana_ms"] == M.UMBRAL_MEDIANA_MS
          and inf["umbral_p95_ms"] == M.UMBRAL_P95_MS)

    print("\n3. las cuatro razones para NO dar veredicto")
    inf = M.analizar(nodo_falso([], enviados=600, ecos=()), ARGS)
    check("sin un solo pong -> SIN_DATOS", inf["veredicto"] == "SIN_DATOS")
    check("y el motivo nombra ufw y el dominio",
          "ufw" in inf["motivo"] and "DOMAIN" in inf["motivo"].upper())

    inf = M.analizar(nodo_falso([5.0] * 150, ecos=()), ARGS)
    check("pongs sin firma de eco -> SIN_VEREDICTO",
          inf["veredicto"] == "SIN_VEREDICTO", inf["motivo"])

    # LA COMPROBACION QUE MAS IMPORTA. Un eco olvidado en otra pestaña del
    # portatil da 0,3 ms por memoria compartida y parece un exito rotundo.
    inf = M.analizar(nodo_falso([0.3] * 600, host="portatil", ecos=("portatil",)),
                     ARGS)
    check("el eco en la misma maquina -> MEDIDA_LOCAL",
          inf["veredicto"] == "MEDIDA_LOCAL", inf["motivo"])
    check("y NO se cuela como CUMPLE pese a 0,3 ms",
          inf["veredicto"] != "CUMPLE")

    inf = M.analizar(nodo_falso([5.0] * 99, enviados=99), ARGS)
    check("99 muestras (< 100) -> SIN_VEREDICTO",
          inf["veredicto"] == "SIN_VEREDICTO", inf["motivo"])
    inf = M.analizar(nodo_falso([5.0] * 100, enviados=100), ARGS)
    check("100 muestras justas -> ya juzga", inf["veredicto"] == "CUMPLE")

    print("\n4. los tres motivos de NO_CUMPLE, uno a uno")
    inf = M.analizar(nodo_falso([120.0] * 150), ARGS)
    check("mediana 120 ms > 100 -> NO_CUMPLE", inf["veredicto"] == "NO_CUMPLE")
    check("y el motivo dice mediana", "mediana" in inf["motivo"], inf["motivo"])

    # Mediana sana (10 ms) y cola larga: 140 a 10 ms y 10 a 900 ms. El p95 cae
    # en la cola. Este es el caso que una media aritmetica se comeria.
    inf = M.analizar(nodo_falso([10.0] * 140 + [900.0] * 10), ARGS)
    check("mediana buena pero p95 malo -> NO_CUMPLE",
          inf["veredicto"] == "NO_CUMPLE", f"p95={inf['p95_ms']}")
    check("y el motivo dice p95, no mediana",
          "p95" in inf["motivo"] and "mediana" not in inf["motivo"],
          inf["motivo"])

    inf = M.analizar(nodo_falso([5.0] * 150, enviados=151), ARGS)
    check("un solo perdido -> NO_CUMPLE", inf["veredicto"] == "NO_CUMPLE")
    check("y el motivo lo cuenta", "1 de 151" in inf["motivo"], inf["motivo"])
    check("perdida en porcentaje", inf["perdida_pct"] == 0.662,
          str(inf["perdida_pct"]))

    print("\n5. los umbrales estan donde los justifica el docstring")
    # RF-08 fija /robotN/estado en 2 Hz = 500 ms de periodo. El techo duro de un
    # sentido es ese periodo; de ida y vuelta, 1000 ms. Si alguien relaja estos
    # numeros, que sea a sabiendas y tocando esta prueba.
    check("mediana <= 100 ms es factor 10 sobre el techo de 1000 ms",
          M.UMBRAL_MEDIANA_MS == 100.0 and 1000.0 / M.UMBRAL_MEDIANA_MS == 10.0)
    check("p95 <= 250 ms es factor 4", M.UMBRAL_P95_MS == 250.0
          and 1000.0 / M.UMBRAL_P95_MS == 4.0)
    check("el perfil es RELIABLE con profundidad 10, como agente.py",
          M.PROFUNDIDAD == 10)

    print("\n6. duplicados y huerfanos se cuentan, no se tapan")
    inf = M.analizar(nodo_falso([5.0] * 150, duplicados=3, desconocidos=2), ARGS)
    check("duplicados en el informe", inf["duplicados"] == 3)
    check("pongs huerfanos en el informe", inf["pongs_sin_ping_conocido"] == 2)
    check("y no cambian el veredicto por si solos", inf["veredicto"] == "CUMPLE")

    print("\n" + "=" * 60)
    if fallos:
        print(f"FALLAN {len(fallos)}: {fallos}")
    else:
        print("Todas las comprobaciones pasan.")
    print("=" * 60)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
