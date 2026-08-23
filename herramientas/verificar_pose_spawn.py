#!/usr/bin/env python3
"""Comprueba que cada robot nazca DENTRO de su pasillo, y en una sola tabla.

Por que existe
--------------
El 2026-08-22 robot1 aparecio en la explanada vacia entre los dos pasillos al
seguir la guia de ejecucion. La causa no fue un valor mal escrito sino una
SEGUNDA tabla de poses: 'deepracer_sim.launch.py' ya tenia la pose del mundo
vigente y 'nav_amcl_demo_sim.launch.py' seguia en (0, 0), que era correcto
cuando el mundo era 'primer_piso_v2.world'. El commit que cambio de mundo
describe el defecto en su propio mensaje y lo arreglo en un solo archivo.

Ese fallo es SILENCIOSO y por eso hace falta comprobarlo aqui: Gazebo abre, el
vehiculo aparece, los siete controladores quedan activos y nadie imprime un
error. Lo que no hay es pasillo alrededor. Si ademas la celda cae fuera del
mapa, AMCL arranca sin geometria contra la que localizar y el sintoma solo
aparece mucho despues, como una ruta imposible.

Que comprueba
-------------
  1. UNA SOLA TABLA. Ningun launch declara una pose escrita a mano; todos leen
     POSE_INICIAL de 'deepracer_raiz_repo.py'. Esta es la comprobacion que
     evita que el defecto vuelva: las otras dos solo verian el sintoma.
  2. DENTRO DEL MAPA. La pose cae en la extension del .pgm de su nivel.
  3. CELDA LIBRE Y CON HOLGURA. La celda no esta ocupada ni es desconocida, y
     dista de la pared mas cercana al menos HOLGURA_MINIMA.

Un robot cuyo nivel todavia no tiene mapa se informa como pendiente y NO cuenta
como fallo: es trabajo declarado, no una regresion.

Uso:
    python3 herramientas/verificar_pose_spawn.py

Devuelve 0 si todas las poses pasan y 1 si alguna falla.
"""

import math
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow. Instalar con: pip3 install Pillow")

RAIZ = Path(__file__).resolve().parent.parent
LAUNCH = RAIZ / "Robot/aws-deepracer/deepracer_bringup/launch"
MAPAS = RAIZ / "Robot/aws-deepracer/deepracer_bringup/maps"

sys.path.insert(0, str(LAUNCH))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from deepracer_raiz_repo import POSE_INICIAL  # noqa: E402
from verificar_mapa import leer_yaml_mapa  # noqa: E402

# Holgura minima entre el punto de nacimiento y la pared mas cercana. El
# vehiculo mide 0.164 m entre ejes y su radio de giro minimo es 0.284 m; por
# debajo de esa holgura no cabe la primera maniobra y Nav2 aborta con
# 'Starting point in lethal space', que apunta al planificador y no al spawn.
HOLGURA_MINIMA = 0.284

# Los launch que NO pueden llevar una pose escrita a mano. Se comprueban por
# separado de la geometria: aunque hoy los numeros coincidan, dos tablas acaban
# divergiendo y la que se quede vieja manda el vehiculo contra una pared.
LAUNCH_SIN_POSE_PROPIA = [
    "deepracer_sim.launch.py",
    "nav_amcl_demo_sim.launch.py",
]

# Una pose escrita a mano se ve asi:  DeclareLaunchArgument('x', default_value='-19.165')
# Se acepta cualquier cosa que no sea un numero literal (una f-string que lea
# POSE_INICIAL, por ejemplo). 'z' queda fuera: es la altura de suelta, no una
# posicion en el mapa, y 0.03 es el mismo valor para todo robot.
POSE_A_MANO = re.compile(
    r"""DeclareLaunchArgument\(\s*(?:name\s*=\s*)?['"](x|y|yaw)['"]\s*,\s*"""
    r"""default_value\s*=\s*['"]-?\d+\.?\d*['"]""",
    re.X,
)


def celdas_ocupadas(ruta_yaml):
    """Devuelve (ocupadas, libres, resolucion, origen, ancho, alto) en celdas."""
    campos = leer_yaml_mapa(ruta_yaml)
    imagen = Image.open(Path(ruta_yaml).parent / campos["image"]).convert("L")
    ancho, alto = imagen.size
    pixeles = imagen.load()
    ocupadas, libres = set(), set()
    for j in range(alto):
        for i in range(ancho):
            v = pixeles[i, j]
            # Convenio de map_server en modo trinary: 0 = ocupado, 254 = libre,
            # 205 = desconocido. El eje Y del .pgm crece hacia abajo y el del
            # mapa hacia arriba, asi que la fila se invierte.
            if v < 65:
                ocupadas.add((i, alto - 1 - j))
            elif v > 250:
                libres.add((i, alto - 1 - j))
    return ocupadas, libres, campos["resolution"], campos["origin"], ancho, alto


def revisar_pose(nombre, datos):
    """Comprueba una fila de POSE_INICIAL. Devuelve (estado, mensaje)."""
    mapa = datos.get("mapa")
    if not mapa:
        return "pendiente", f"el nivel {datos['nivel']} todavia no tiene mapa"

    ruta_yaml = MAPAS / mapa
    if not ruta_yaml.is_file():
        return "fallo", f"POSE_INICIAL['{nombre}'] cita '{mapa}', que no existe"

    ocupadas, libres, res, (ox, oy, _), ancho, alto = celdas_ocupadas(ruta_yaml)
    x, y = datos["x"], datos["y"]
    i = int((x - ox) / res)
    j = int((y - oy) / res)

    if not (0 <= i < ancho and 0 <= j < alto):
        return "fallo", (
            f"({x}, {y}) cae FUERA del mapa, que abarca "
            f"x {ox:.2f}..{ox + ancho * res:.2f} · y {oy:.2f}..{oy + alto * res:.2f}"
        )
    if (i, j) in ocupadas:
        return "fallo", f"({x}, {y}) cae sobre una pared"
    if (i, j) not in libres:
        return "fallo", f"({x}, {y}) cae en una celda DESCONOCIDA del mapa"

    holgura = res * min(math.hypot(i - oi, j - oj) for oi, oj in ocupadas)
    if holgura < HOLGURA_MINIMA:
        return "fallo", (
            f"({x}, {y}) tiene {holgura:.3f} m hasta la pared mas cercana, "
            f"por debajo del minimo de {HOLGURA_MINIMA} m"
        )
    return "ok", f"({x}, {y}) libre, holgura {holgura:.2f} m en '{mapa}'"


def revisar_tabla_unica():
    """Ningun launch puede traer su propia pose escrita a mano."""
    problemas = []
    for archivo in LAUNCH_SIN_POSE_PROPIA:
        ruta = LAUNCH / archivo
        if not ruta.is_file():
            problemas.append(f"{archivo}: no existe")
            continue
        for m in POSE_A_MANO.finditer(ruta.read_text()):
            problemas.append(
                f"{archivo}: declara '{m.group(1)}' con un numero escrito a mano; "
                f"tiene que salir de POSE_INICIAL"
            )
    return problemas


def main():
    fallos = 0

    print("Una sola tabla de poses")
    problemas = revisar_tabla_unica()
    if problemas:
        fallos += len(problemas)
        for p in problemas:
            print(f"  [FALLO] {p}")
    else:
        print(f"  [ OK ]  ningun launch trae pose propia "
              f"({len(LAUNCH_SIN_POSE_PROPIA)} revisados)")

    print("\nCada robot nace dentro de su pasillo")
    for nombre in sorted(POSE_INICIAL):
        estado, mensaje = revisar_pose(nombre, POSE_INICIAL[nombre])
        etiqueta = {"ok": "[ OK ] ", "fallo": "[FALLO]", "pendiente": "[ -- ] "}[estado]
        print(f"  {etiqueta} {nombre}: {mensaje}")
        if estado == "fallo":
            fallos += 1

    print()
    if fallos:
        print(f"{fallos} problema(s). La pose de spawn NO es de fiar.")
        return 1
    print("Todas las poses de spawn son validas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
