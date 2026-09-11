#!/usr/bin/env python3
"""Lista los cambios de etapa de una mision leyendolos del BAG.

Por que existe, y por que no se usa otra cosa:

'componer_registro.py' produce el registro de la campana, y su bloque 'marcas'
es un diccionario de los siete instantes de la §3.5 con 'additionalProperties:
false'. Esos siete instantes no incluyen la etapa 7 de RF-28 ni podrian
incluirla: ESPERANDO_CONFIRMACION puede marcarse DOS veces en una sola mision
-la pregunta y la alerta de los 60 s-, y un diccionario de instantes unicos no
representa eso. Contar las marcas de etapa 7 pide una lista, no un diccionario.

El registrador en vivo ('ruta_registros' del coordinador) si escribe una lista,
pero el §4 de Documentos/RUNBOOK_CAMPANA.md lo prohibe desde el 2026-09-01: el
registrador serializando a 50 Hz compite por la CPU contra dos Gazebo justo
donde RNF-06 exige RTF >= 0,99, y lo que escribe no es un registro valido de la
campana. Encenderlo para medir RF-28 cambiaria la condicion del banco para
medir una funcionalidad que no tiene nada que ver con la carga de CPU.

Queda el bag, que es la fuente de todo lo demas en este proyecto. Trae
'/coordinacion/estado_mision' completo, asi que trae cada cambio de etapa, el
'robot_activo' de cada uno y -esto es lo que ningun registro guarda- el
'mensaje_usuario' literal con el que el coordinador hablo al usuario. Por eso
esta herramienta tambien sustituye al 'ros2 topic echo --field mensaje_usuario'
en un cuarto terminal: el texto ya estaba grabado.

Uso:
    source ~/deepracer_sim_ws/install/setup.bash
    python3 herramientas/inspeccionar_etapas.py ~/tesis_evidencia/S22_RF28_A

    # solo las marcas de una etapa, con su separacion:
    python3 herramientas/inspeccionar_etapas.py ~/tesis_evidencia/S22_RF28_A --etapa 7

Necesita el 'source' porque lee el bag con rosbag2 y deserializa
coordinacion_msgs. Sin el overlay, 'leer_bag' aborta diciendolo.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from componer_registro import leer_bag  # noqa: E402

TOPICO = "/coordinacion/estado_mision"

# Los mismos nombres que registrador.ETAPAS. No se importa de alli porque ese
# modulo vive en el paquete 'coordinacion' y esta herramienta se ejecuta desde
# el repositorio, igual que componer_registro.py y por el mismo motivo.
ETAPAS = {0: "INACTIVA", 1: "TRAMO_1", 2: "TRANSFERENCIA", 3: "TRAMO_2",
          4: "COMPLETADA", 5: "FALLIDA", 6: "RECIBIDA",
          7: "ESPERANDO_CONFIRMACION"}


def transiciones(muestras):
    """[(t, etapa_num, robot_activo, mision_id, mensaje_usuario), ...].

    Solo los CAMBIOS. El coordinador republica su estado a 1 Hz, asi que sin
    esto una mision de cinco minutos daria trescientas filas identicas.

    Cambio significa etapa distinta o texto distinto: la alerta de los 60 s de
    RF-28 repite la etapa 7 y cambia solo el texto, y es justamente la fila que
    hay que ver. Comparar solo la etapa la haria invisible.
    """
    salida, previo = [], None
    for t, m in muestras:
        actual = (m.etapa, m.mensaje_usuario)
        if actual != previo:
            salida.append((t, m.etapa, m.robot_activo, m.mision_id,
                           m.mensaje_usuario))
            previo = actual
    return salida


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("bag", help="carpeta del bag")
    p.add_argument("--etapa", type=int, default=None,
                   help="filtra por numero de etapa y mide la separacion")
    a = p.parse_args()

    topicos = leer_bag(a.bag)
    if TOPICO not in topicos:
        raise SystemExit(
            f"El bag no trae {TOPICO}, asi que no contiene ni una sola etapa.\n"
            f"Topicos que si trae: {', '.join(sorted(topicos)) or '(ninguno)'}\n"
            f"Es el fallo que describe la guarda 2 de grabar_mision.sh: casi "
            f"siempre es el overlay sin sourcear al GRABAR, no al leer.")

    filas = transiciones(topicos[TOPICO])
    if a.etapa is not None:
        filas = [f for f in filas if f[1] == a.etapa]

    print(f"{'t_sim (s)':>10}  {'etapa':<22} {'robot':<8} {'mision':<16} texto")
    print("-" * 100)
    for t, etapa, robot, mid, texto in filas:
        nombre = ETAPAS.get(etapa, f"desconocida({etapa})")
        print(f"{t:10.1f}  {nombre:<22} {robot or '(vacio)':<8} "
              f"{mid or '(vacio)':<16} {texto}")

    print("-" * 100)
    print(f"{len(filas)} marca(s).")

    if a.etapa is not None and len(filas) >= 2:
        # La separacion va en tiempo de SIMULACION, que es lo que sella el bag.
        # Los plazos de RF-28 son de reloj de pared, asi que para compararlos
        # hay que dividir por el RTF de la corrida: 60 s de pared son 60 x RTF
        # segundos de simulacion. El RTF esta en rtf.json, junto al bag.
        for (t1, *_), (t2, *_) in zip(filas, filas[1:]):
            print(f"separacion: {t2 - t1:.1f} s de simulacion "
                  f"(= 60 s de pared si el RTF vale {(t2 - t1) / 60:.4f})")


if __name__ == "__main__":
    main()
