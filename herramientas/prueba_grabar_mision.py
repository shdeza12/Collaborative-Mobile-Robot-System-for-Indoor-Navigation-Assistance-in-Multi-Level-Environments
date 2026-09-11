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

import json
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
control)
    # 'list_controllers' es un SERVICIO: su respuesta nunca esta en el bag, y de
    # ahi que 'controladores_activos' saliera '{}' hasta el 2026-09-10. Se imita
    # aqui -con el color ANSI incluido, que es lo que rompia la comparacion- para
    # comprobar que el grabador lo captura EN EL MOMENTO y lo deja junto al bag.
    # Con ROS2_CONTROL_MUDO se calla, que es lo que hace un controller_manager
    # que no esta o no responde dentro del plazo.
    [ -n "$ROS2_CONTROL_MUDO" ] && exit 0
    # Los mismos nombres que declara el doble del modulo compartido, y solo
    # esos: el grabador tiene que contar contra la lista que lee, no contra una
    # copia suya.
    for C in controlador_de_prueba_1 controlador_de_prueba_2; do
        printf '%s tipo/Tipo \\033[92mactive\\033[0m\\n' "$C"
    done
    ;;
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
#
# LAS DOS MARCAS BUENAS TIENEN QUE AVANZAR. Devolviendo la misma marca dos veces
# -que es lo que hacia este doble- la ventana de pared sale de cero segundos,
# grabar_mision.sh se protege de esa division y NO escribe rtf.json. La prueba
# de la corrida sana pasaba igual porque no miraba el archivo, asi que la rama
# que calcula el RTF y lo deja en disco -el motivo por el que existe todo este
# archivo- nunca se llego a ejecutar en ninguna prueba.
#
# 100 s de simulacion por cada 100 s de pared son RTF 1,0: una corrida sana, por
# encima del 0,99 que exige RNF-06, de modo que el aviso de 'rtf_bajo' tampoco
# se dispara.
MEDIR_RTF_FALSO = """#!/usr/bin/env python3
import os, sys
contador = os.environ["CONTADOR_MARCAS"]
n = int(open(contador).read()) if os.path.exists(contador) else 0
open(contador, "w").write(str(n + 1))
if n < int(os.environ["MARCAS_BUENAS"]):
    print("{:.6f} {:.6f}".format(100.0 + 100 * n, 200.0 + 100 * n))
    sys.exit(0)
print("SIN DATOS en /clock tras 10 s.", file=sys.stderr)
sys.exit(1)
"""

COND_INICIAL_FALSA = """#!/usr/bin/env python3
print('{"criterio": "falso", "por_robot": {}}')
"""

# El doble del modulo compartido. Trae los controladores ADEMAS del reloj porque
# el grabador ya no lleva la lista escrita a mano: la lee de aqui, que es el
# mismo sitio del que la lee el launch que los carga. La lista del doble es
# corta y con nombres inventados a proposito: si el grabador volviera a contar
# contra una lista propia, el '2/2' saldria '0/7' y la prueba lo veria.
RELOJ_FALSO = """
def reloj_de(ns):
    return '/clock' if ns == 'robot1' else f'/{ns}/clock'


CONTROLADORES = ['controlador_de_prueba_1', 'controlador_de_prueba_2']
"""


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


def correr(marcas_buenas, ros2_control=True):
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        script, entorno = montar(tmp, marcas_buenas)
        if not ros2_control:
            entorno["ROS2_CONTROL_MUDO"] = "1"
        r = subprocess.run(["bash", str(script), "mision_de_prueba", "robot1"],
                           capture_output=True, text=True, env=entorno,
                           timeout=60)
        return {
            "codigo": r.returncode,
            "salida": r.stdout + r.stderr,
            "se_grabo": (tmp / "se_grabo.txt").exists(),
            "hay_bag": (tmp / "evidencia" / "mision_de_prueba").exists(),
            "controladores": _leer_json(
                tmp / "evidencia" / "mision_de_prueba" / "controladores.json"),
            "rtf": _leer_json(
                tmp / "evidencia" / "mision_de_prueba" / "rtf.json"),
        }


def _leer_json(ruta):
    """None si no existe: 'no se escribio' y 'se escribio vacio' no son lo
    mismo, y la prueba tiene que poder distinguirlos."""
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text())


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
    # Y no se inventa un RTF con la unica marca que tiene: sin ventana no hay
    # RTF, y un rtf.json a medias seria peor que ninguno.
    check("no escribe un rtf.json a medias", r["rtf"] is None, f"-> {r['rtf']}")


def prueba_de_la_corrida_sana():
    print("\nCon las dos marcas buenas, la corrida termina normal")
    r = correr(marcas_buenas=2)
    check("sale con codigo 0", r["codigo"] == 0, f"codigo {r['codigo']}")
    check("grabo el bag", r["se_grabo"])
    check("no avisa de nada roto", "se resuelve AHORA" not in r["salida"])
    # El campo que estuvo vacio en los 30 registros de la campana OE4. Se
    # comprueba aqui, en la mitad que MIDE, porque la otra mitad -que el
    # compositor lo lea- ya la cubre prueba_componer_registro.py. Las dos juntas
    # cierran el camino entero: servicio vivo -> fichero junto al bag -> registro.
    check("deja los controladores junto al bag", r["controladores"] is not None,
          "sin controladores.json el compositor vuelve a escribir {}")
    # '2/2' y no '7/7': el doble del modulo compartido declara dos controladores
    # inventados. Que salga '2/2' prueba que el grabador cuenta contra la lista
    # que LEE del modulo, no contra una copia suya escrita a mano -que era el
    # defecto: una copia no se entera de que la otra cambio-.
    check("y contra la lista que declara el modulo, no contra una copia suya",
          (r["controladores"] or {}).get("robot1") == "2/2",
          f"-> {r['controladores']}")
    # La razon de ser del script. Hasta que el doble de medir_rtf.py devolvio
    # marcas que AVANZAN, la ventana de pared era de cero segundos y esta rama
    # no se ejecutaba en ninguna prueba.
    check("calcula el RTF y lo deja junto al bag", r["rtf"] is not None,
          "sin rtf.json la corrida no se puede registrar y el dato es "
          "irrecuperable con el gzserver cerrado")
    check("con el RTF de la ventana, no con el valor de una marca suelta",
          (r["rtf"] or {}).get("rtf") == 1.0, f"-> {r['rtf']}")
    check("y deja ver de que ventana salio",
          (r["rtf"] or {}).get("sim_s") == 100.0
          and (r["rtf"] or {}).get("pared_s") == 100.0, f"-> {r['rtf']}")


def prueba_de_los_controladores_mudos():
    print("\nSi el controller_manager no contesta, se dice, no se aprueba")
    # 'no lo se' y 'estaban los siete' no pueden verse igual en el registro: un
    # '7/7' inventado convertiria una corrida sin banco en una corrida sana.
    r = correr(marcas_buenas=2, ros2_control=False)
    check("el bag se graba igual: esto no es una compuerta", r["se_grabo"])
    check("y el robot mudo se declara 'sin respuesta'",
          (r["controladores"] or {}).get("robot1") == "sin respuesta",
          f"-> {r['controladores']}")


def main():
    if not GRABAR.exists():
        print(f"No esta {GRABAR}")
        return 1
    pruebas_de_la_marca_inicial()
    pruebas_de_la_marca_final()
    prueba_de_la_corrida_sana()
    prueba_de_los_controladores_mudos()
    print()
    if FALLOS:
        print(f"{len(FALLOS)} fallan.")
        return 1
    print("Todo pasa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
