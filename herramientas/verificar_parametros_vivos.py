#!/usr/bin/env python3
"""Comprueba que la pila VIVA lleve los parametros que dice el YAML del repo.

POR QUE EXISTE
--------------
El 2026-08-27 se perdio una mision entera por esto. Se editaron los alpha de
AMCL y xy_goal_tolerance en
Robot/aws-deepracer/deepracer_bringup/config/nav2_params_nav_amcl_sim_demo.yaml,
se corrio la mision, y se analizo el bag como si midiera el cambio. No lo
media: el gzserver llevaba 1278 s vivo, o sea que se habia lanzado ANTES de la
edicion. Los parametros vivos seguian siendo los antiguos:

    /robot1/controller_server goal_checker.xy_goal_tolerance  0.25  (YAML: 0.15)
    /robot1/amcl alpha1                                       0.2   (YAML: 0.01)

Y el error es invisible desde fuera. Con --symlink-install el fichero del
install/ es un enlace al del repo, asi que editarlo "ya esta aplicado" en el
sentido de que no hace falta compilar; pero los parametros se leen UNA VEZ, al
arrancar el nodo. Un YAML nuevo y una pila vieja se ven exactamente igual en la
terminal, y el bag que sale tiene la misma pinta que el bueno.

QUE COMPRUEBA, Y POR QUE SOLO ESTOS
-----------------------------------
La lista es corta a proposito. No se trata de auditar los ~200 parametros de
Nav2, sino los pocos que deciden el resultado de la medida y que por eso son
los que se tocan entre corrida y corrida. Si se ajusta otro parametro y se va a
medir su efecto, se anade aqui: el coste de anadirlo es una linea y el coste de
olvidarlo es una tarde.

Uso:
    python3 herramientas/verificar_parametros_vivos.py robot1

Codigos de salida:
    0  la pila viva coincide con el YAML
    1  algun parametro vivo es DISTINTO del YAML
    2  algun parametro no se pudo leer, que no es lo mismo que ser distinto

El 2 existe desde el 2026-09-04. Ese dia el Piloto 3 aborto con "la pila corre
con parametros distintos" por UNA lectura de alpha2 que se agoto, mientras el
mismo nodo contestaba los otros cuatro alpha. Con la pila aun viva se leyo
despues: 0.01, igual que el YAML. Decir "distinto" cuando lo que paso es "no
pude leer" manda a repetir una corrida sana.
"""

import os
import re
import subprocess
import sys
import time

import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_NAV2 = os.path.join(
    RAIZ, "Robot", "aws-deepracer", "deepracer_bringup", "config",
    "nav2_params_nav_amcl_sim_demo.yaml")

# (nodo, parametro vivo, ruta dentro del YAML). El nodo se antepone con el
# namespace del robot en tiempo de ejecucion.
VIGILADOS = [
    ("controller_server", "goal_checker.xy_goal_tolerance",
     ["controller_server", "ros__parameters", "goal_checker",
      "xy_goal_tolerance"]),
    ("controller_server", "goal_checker.yaw_goal_tolerance",
     ["controller_server", "ros__parameters", "goal_checker",
      "yaw_goal_tolerance"]),
    ("controller_server", "goal_checker.stateful",
     ["controller_server", "ros__parameters", "goal_checker", "stateful"]),
    ("amcl", "alpha1", ["amcl", "ros__parameters", "alpha1"]),
    ("amcl", "alpha2", ["amcl", "ros__parameters", "alpha2"]),
    ("amcl", "alpha3", ["amcl", "ros__parameters", "alpha3"]),
    ("amcl", "alpha4", ["amcl", "ros__parameters", "alpha4"]),
    ("amcl", "alpha5", ["amcl", "ros__parameters", "alpha5"]),
]


def _en_yaml(doc, ruta):
    nodo = doc
    for clave in ruta:
        if not isinstance(nodo, dict) or clave not in nodo:
            return None
        nodo = nodo[clave]
    return nodo


def _leer_una_vez(nodo, parametro):
    """Una llamada a 'ros2 param get'. Devuelve el valor o None.

    'ros2 param get' contesta con frases tipo 'Double value is: 0.01' o
    'Boolean value is: False'; se extrae lo de despues de los dos puntos.
    """
    try:
        salida = subprocess.run(
            ["ros2", "param", "get", nodo, parametro],
            capture_output=True, text=True, timeout=15).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    m = re.search(r"value is:\s*(.+)", salida)
    return m.group(1).strip() if m else None


def _param_vivo(nodo, parametro, intentos=3, pausa_s=1.0, lector=None):
    """Devuelve el valor vivo, o None si no se pudo leer en 'intentos' tiradas.

    Reintenta porque el fallo observado es intermitente: una sola llamada de
    ocho se agoto contra un nodo que respondia todas las demas. Y la compuerta
    corre dentro de la ventana de 2,6 min que dura la condicion inicial, asi
    que un timeout suelto no puede costar la corrida.
    """
    lector = lector or _leer_una_vez
    for i in range(intentos):
        valor = lector(nodo, parametro)
        if valor is not None:
            return valor
        if i + 1 < intentos and pausa_s:
            time.sleep(pausa_s)
    return None


def _igual(vivo, esperado):
    """Compara sin exigir que la representacion en texto coincida.

    'ros2 param get' imprime 0.15 y el YAML puede traer 0.150; y para booleanos
    imprime 'True'/'False' con mayuscula, que es lo mismo que el true/false del
    YAML pero no la misma cadena.
    """
    if isinstance(esperado, bool):
        return vivo.strip().lower() == str(esperado).lower()
    try:
        return abs(float(vivo) - float(esperado)) < 1e-9
    except (TypeError, ValueError):
        return vivo.strip() == str(esperado).strip()


def codigo_de_salida(desajustes, ilegibles):
    """0 todo bien, 1 hay un valor distinto, 2 hay un valor que no se leyo.

    El desajuste manda sobre el ilegible: si ya sabemos que un parametro no es
    el del YAML, esa es la noticia y el remedio es relanzar; que ademas otro no
    se dejara leer no cambia nada.
    """
    if desajustes:
        return 1
    if ilegibles:
        return 2
    return 0


def main():
    robot = sys.argv[1] if len(sys.argv) > 1 else "robot1"

    if not os.path.exists(YAML_NAV2):
        print(f"No encuentro el YAML de Nav2 en {YAML_NAV2}.")
        return 1
    with open(YAML_NAV2) as f:
        doc = yaml.safe_load(f)

    print(f"Parametros vivos de {robot} contra "
          f"{os.path.basename(YAML_NAV2)}")

    desajustes, ilegibles = [], []
    for nodo_corto, parametro, ruta in VIGILADOS:
        esperado = _en_yaml(doc, ruta)
        if esperado is None:
            print(f"  {nodo_corto}/{parametro}: no esta en el YAML, se salta")
            continue
        nodo = f"/{robot}/{nodo_corto}"
        vivo = _param_vivo(nodo, parametro)
        if vivo is None:
            ilegibles.append(f"{nodo} {parametro}")
            print(f"  {nodo_corto}/{parametro}: NO SE PUDO LEER (3 intentos)")
            continue
        ok = _igual(vivo, esperado)
        print(f"  {nodo_corto}/{parametro}: vivo {vivo}  YAML {esperado}  "
              f"{'ok' if ok else '<-- DISTINTO'}")
        if not ok:
            desajustes.append((nodo_corto, parametro, vivo, esperado))

    codigo = codigo_de_salida(desajustes, ilegibles)

    if codigo == 1:
        print("")
        print("LA PILA VIVA NO ES LA DEL YAML. Los nodos leyeron su")
        print("configuracion al arrancar, y el YAML se edito despues.")
        print("Una mision grabada asi NO mide el cambio: repite la anterior.")
        print("")
        print("Matar la simulacion y relanzarla. Con --symlink-install NO hace")
        print("falta compilar; hace falta RELANZAR.")
        return 1

    if codigo == 2:
        print("")
        print(f"NO SE PUDIERON LEER {len(ilegibles)} de {len(VIGILADOS)} "
              f"parametros tras 3 intentos:")
        for i in ilegibles:
            print(f"  {i}")
        print("")
        print("Esto NO dice que la pila sea distinta del YAML: ningun valor")
        print("leido salio distinto. Dice que la compuerta no pudo comprobarlo,")
        print("y una compuerta que no puede comprobar no da paso.")
        print("")
        print("Si fallaron TODOS, la pila no esta arriba o este proceso esta")
        print("en otro ROS_DOMAIN_ID. Si fallaron unos pocos contra un nodo")
        print("que contesto los demas, es una lectura perdida: repite este")
        print("mismo comando antes de dar por mala la pila.")
        return 2

    print("")
    print("La pila viva lleva los valores del YAML.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
