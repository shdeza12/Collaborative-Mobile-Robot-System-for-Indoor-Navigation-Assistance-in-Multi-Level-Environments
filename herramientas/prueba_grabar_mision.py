#!/usr/bin/env python3
"""Pruebas de las guardas de RTF de grabar_mision.sh.

    python3 herramientas/prueba_grabar_mision.py

NO necesita ROS ni Gazebo: monta un 'ros2' falso en el PATH y sustituye
medir_rtf.py por un doble que falla cuando se le pide. Lo que se comprueba es
el CONTRATO del script, no la simulacion.


QUE SE ESTA PROTEGIENDO
-----------------------
El 2026-09-05 se perdieron tres de las veinte misiones de la campana -la 13, la
22 y la 28- porque la marca de RTF fallo y el script siguio como si nada:
la linea era '... --marca 2>/dev/null || true'. El aviso del final existia pero
se perdio entre la salida de veinte corridas seguidas, y el codigo de salida
decia 0, asi que el operador encadeno la siguiente mision sin enterarse. Cuando
se compusieron los registros dos horas despues, el gzserver ya estaba cerrado y
el RTF de esas tres corridas era irrecuperable.

De ahi las dos guardas que se prueban aqui:

  1. Si la marca INICIAL falla, no se graba nada. Es antes de la corrida, asi
     que no se pierden cuatro minutos grabando un bag que despues no se podra
     registrar.
  2. Si la marca FINAL falla, el bag ya esta hecho y no se deshace, pero el
     script sale con codigo 3. La simulacion todavia esta viva en ese instante:
     es la ultima ventana para salvar la corrida, y con salida 0 se cerraba sin
     que nadie la viera.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GRABAR = RAIZ / "herramientas" / "grabar_mision.sh"

FALLOS = []


def check(descripcion, condicion, detalle=""):
    print(f"  {'ok  ' if condicion else 'FALLA'}  {descripcion}")
    if not condicion:
        if detalle:
            print(f"          {detalle}")
        FALLOS.append(descripcion)


ROS2_FALSO = """#!/bin/bash
# 'ros2' de mentira: contesta lo justo para que las guardas 1 y 2 pasen.
case "$1" in
topic)
    case "$2" in
    list)
        echo "/clock [rosgraph_msgs/msg/Clock]"
        echo "/coordinacion/estado_mision [std_msgs/msg/String]"
        ;;
    info)
        echo "Type: std_msgs/msg/String"
        echo "Publisher count: 1"
        echo "Subscription count: 0"
        ;;
    esac
    ;;
interface) exit 0 ;;
bag)
    # Deja constancia de que se llego a grabar, y crea el directorio como
    # haria el grabador de verdad.
    echo "$@" >> "$MARCADOR_BAG"
    for ((i=1; i<=$#; i++)); do
        if [ "${!i}" = "-o" ]; then j=$((i+1)); mkdir -p "${!j}"; fi
    done
    ;;
esac
exit 0
"""

# Primera llamada bien, la segunda falla: asi se prueba el caso en que el bag
# ya esta grabado y lo que se pierde es la marca de cierre.
MEDIR_RTF_FALSO = """#!/usr/bin/env python3
import os, sys
contador = os.environ["CONTADOR_MARCAS"]
n = int(open(contador).read()) if os.path.exists(contador) else 0
open(contador, "w").write(str(n + 1))
if n < int(os.environ["MARCAS_BUENAS"]):
    print("100.000000 200.000000")
    sys.exit(0)
print("SIN DATOS en /clock tras 10 s.", file=sys.stderr)
sys.exit(1)
"""

COND_INICIAL_FALSA = """#!/usr/bin/env python3
print('{"criterio": "falso", "por_robot": {}}')
"""

RELOJ_FALSO = "def reloj_de(ns):\n    return '/clock' if ns == 'robot1' else f'/{ns}/clock'\n"


def montar(tmp, marcas_buenas):
    """Arma un arbol minimo donde grabar_mision.sh puede correr sin ROS."""
    herr = tmp / "herramientas"
    herr.mkdir(parents=True)
    shutil.copy(GRABAR, herr / "grabar_mision.sh")

    (herr / "medir_rtf.py").write_text(MEDIR_RTF_FALSO)
    (herr / "verificar_condicion_inicial.py").write_text(COND_INICIAL_FALSA)

    launch = tmp / "Robot/aws-deepracer/deepracer_bringup/launch"
    launch.mkdir(parents=True)
    (launch / "deepracer_raiz_repo.py").write_text(RELOJ_FALSO)

    binfalso = tmp / "bin"
    binfalso.mkdir()
    ros2 = binfalso / "ros2"
    ros2.write_text(ROS2_FALSO)
    ros2.chmod(0o755)

    entorno = dict(os.environ)
    entorno["PATH"] = f"{binfalso}:{entorno['PATH']}"
    entorno["TESIS_EVIDENCIA"] = str(tmp / "evidencia")
    entorno["MARCADOR_BAG"] = str(tmp / "se_grabo.txt")
    entorno["CONTADOR_MARCAS"] = str(tmp / "contador.txt")
    entorno["MARCAS_BUENAS"] = str(marcas_buenas)
    return herr / "grabar_mision.sh", entorno


def correr(marcas_buenas):
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        script, entorno = montar(tmp, marcas_buenas)
        r = subprocess.run(["bash", str(script), "mision_de_prueba", "robot1"],
                           capture_output=True, text=True, env=entorno,
                           timeout=60)
        return {
            "codigo": r.returncode,
            "salida": r.stdout + r.stderr,
            "se_grabo": (tmp / "se_grabo.txt").exists(),
            "hay_bag": (tmp / "evidencia" / "mision_de_prueba").exists(),
        }


def pruebas_de_la_marca_inicial():
    print("\nSi la marca inicial de RTF falla, no se graba nada")
    r = correr(marcas_buenas=0)
    check("aborta con codigo 1", r["codigo"] == 1, f"codigo {r['codigo']}")
    check("NO llega a invocar 'ros2 bag record'", not r["se_grabo"])
    check("no deja un bag a medias", not r["hay_bag"])
    check("dice por que no se graba",
          "no se pudo tomar la marca inicial de RTF" in r["salida"])
    check("deja ver el error real de medir_rtf.py, no lo esconde",
          "SIN DATOS en /clock" in r["salida"],
          "el stderr de medir_rtf.py tiene que llegar al terminal")


def pruebas_de_la_marca_final():
    print("\nSi falla la marca de cierre, el bag queda pero el fallo se ve")
    r = correr(marcas_buenas=1)
    check("sale con codigo 3, no con 0", r["codigo"] == 3,
          f"codigo {r['codigo']}; con 0 el operador encadena la siguiente")
    check("el bag si se grabo", r["se_grabo"])
    check("avisa de que hay que medirlo AHORA",
          "se resuelve AHORA" in r["salida"])
    check("da el comando de rescate",
          "medir_rtf.py --segundos" in r["salida"])


def prueba_de_la_corrida_sana():
    print("\nCon las dos marcas buenas, la corrida termina normal")
    r = correr(marcas_buenas=2)
    check("sale con codigo 0", r["codigo"] == 0, f"codigo {r['codigo']}")
    check("grabo el bag", r["se_grabo"])
    check("no avisa de nada roto", "se resuelve AHORA" not in r["salida"])


def main():
    if not GRABAR.exists():
        print(f"No esta {GRABAR}")
        return 1
    pruebas_de_la_marca_inicial()
    pruebas_de_la_marca_final()
    prueba_de_la_corrida_sana()
    print()
    if FALLOS:
        print(f"{len(FALLOS)} fallan.")
        return 1
    print("Todo pasa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
