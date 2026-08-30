#!/usr/bin/env python3
"""Sorteo de las misiones de la campana de OE4. Es el pendiente 5 de la §9 del
protocolo y lo que separa n = 1 de N = 30.

    python3 herramientas/sortear_misiones.py --semilla 20260822 --n 30 \\
        --salida Documentos/Evidencia/campana_oe4_misiones.csv

NO necesita ROS, ni el workspace sourceado, ni Gazebo: entra un YAML y sale un
CSV. Se corre una vez, ANTES de la primera corrida, y el archivo se versiona.


POR QUE EXISTE
--------------
La §6.3 del protocolo lo dice sin rodeos: "elegir los pares a mano el dia de la
campana es la puerta de entrada al sesgo de seleccion". Un operador que elige
tiende, sin querer, a las misiones que sabe que salen bien. Con semilla fija el
sorteo es del protocolo y no del operador, y cualquiera puede reproducirlo.

La semilla sola no basta para reproducirlo: el mismo numero sobre un catalogo
distinto da misiones distintas. Por eso el archivo lleva tambien el SHA-256 del
catalogo. Si alguien anade un destino y vuelve a sortear con la misma semilla,
la huella cambia y se ve.


LAS CUATRO DECISIONES QUE HUBO QUE TOMAR, Y QUE EL PROTOCOLO NO FIJA
--------------------------------------------------------------------
El §6.2 fija las condiciones -A: ambos en el piso 1, 15 misiones; B: piso 1 ->
piso 2, 15 misiones- y el §6.3 fija que hay sorteo con semilla. Lo demas hubo
que decidirlo aqui, asi que se escribe para que se pueda discutir:

1. LOS PUNTOS DE TRANSFERENCIA NO SE SORTEAN, ni como origen ni como destino.
   'piso1_escalera' y 'piso2_escalera' llevan 'es_transferencia: true' y el
   propio catalogo dice de ellos que son "punto de transferencia, no destino".
   El motivo no es de nomenclatura: una mision de condicion B con destino
   'piso2_escalera' tendria un segundo tramo de longitud cero, porque el relevo
   ocurre justamente ahi. Contaria como exito sin haber navegado, y arrastraria
   el tiempo total de la condicion B hacia abajo. Lo mismo por el otro lado con
   'piso1_escalera' como origen. Quedan 14 puntos elegibles en el piso 1 y 15
   en el piso 2.

2. SIN REPETICION: las 30 misiones son 30 pares DISTINTOS. Hay 14x13 = 182
   pares posibles de condicion A y 14x15 = 210 de condicion B, asi que sobra
   sitio. Con reposicion, sortear 15 de 182 repite algun par mas o menos la
   mitad de las veces, y una repeticion gasta una de las 30 corridas sin
   cubrir un destino nuevo. No es que repetir estuviera mal: es que sale mas
   caro que no repetir.

3. EL ORDEN DEL ARCHIVO MEZCLA LAS DOS CONDICIONES. La §6.3 manda ejecutar en
   el orden del archivo "sin reordenar", asi que el orden del archivo ES el
   orden temporal de la campana. Si fuera 15 de A y luego 15 de B, cualquier
   deriva a lo largo de la sesion -la pila lleva horas encendida, el equipo se
   calienta- quedaria confundida con la diferencia entre condiciones, que es
   justo lo que la campana quiere medir. Se barajan las 30 juntas.

4. SE NIEGA A SOBRESCRIBIR, y la comprobacion va ANTES de sortear nada. Esto
   es una leccion ya pagada: el banco de RF-22 escribia a un nombre fijo y su
   segunda corrida piso a la primera sin decir nada (§4 de
   Evidencia/S21_banco_tiempo_asignacion.md). Aqui seria peor: pisar el
   listado con otra semilla a mitad de campana dejaria unas corridas contra un
   listado y otras contra otro, y nada en los registros lo delataria.
"""

import argparse
import csv
import datetime
import hashlib
import os
import random
import sys

import yaml

# El catalogo del repositorio, no el de install/. Es el que se versiona junto al
# CSV que sale de aqui, y por tanto el unico par que se puede auditar despues.
# Si install/ tuviera otro, el aviso de _avisar_si_install_difiere lo dice.
CATALOGO_POR_DEFECTO = os.path.join(
    "Robot", "aws-deepracer", "deepracer_bringup", "config", "puntos_interes.yaml")

# §6.2: la condicion A vive entera en el piso 1 y la B va del 1 al 2. No es
# simetrico y no puede serlo: solo hay un usuario y empieza donde esta.
NIVEL_A = 1
NIVEL_B_ORIGEN = 1
NIVEL_B_DESTINO = 2


def sha256_de(ruta):
    """Huella de un archivo.

    Esta escrita aqui y no importada de banco_tiempo_asignacion.py a proposito:
    aquel importa rclpy y esta herramienta tiene que correr sin ROS. Seis lineas
    duplicadas cuestan menos que ese acoplamiento.
    """
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(65536), b""):
            h.update(trozo)
    return h.hexdigest()


def cargar_catalogo(ruta):
    with open(ruta) as f:
        return yaml.safe_load(f)["puntos"]


def elegibles(catalogo, nivel):
    """Ids del nivel pedido que pueden ser origen o destino de una mision.

    Deja fuera los puntos de transferencia por el motivo 1 de la cabecera.
    Devuelve la lista ORDENADA: el sorteo tiene que ser reproducible, y
    random.sample sobre una lista cuyo orden dependa del YAML daria misiones
    distintas si alguien reordena el archivo sin cambiar ningun punto.
    """
    return sorted(p["id"] for p in catalogo
                  if int(p["nivel"]) == nivel and not p.get("es_transferencia"))


def sortear(catalogo, n, semilla):
    """N misiones, mitad condicion A y mitad B, barajadas entre si.

    Devuelve una lista de dicts con n, condicion, origen_id y destino_id, en el
    orden en que hay que ejecutarlas.
    """
    if n % 2 != 0:
        raise ValueError(
            f"N tiene que ser par para repartirlo entre las dos condiciones, y "
            f"se pidio {n}. La §6.2 fija 15 y 15 sobre N = 30; con un N impar "
            f"habria que decidir a que condicion se le da la corrida de mas, y "
            f"esa decision no es de un programa.")

    por_condicion = n // 2
    a1 = elegibles(catalogo, NIVEL_A)
    b_origen = elegibles(catalogo, NIVEL_B_ORIGEN)
    b_destino = elegibles(catalogo, NIVEL_B_DESTINO)

    pares_a = [(o, d) for o in a1 for d in a1 if o != d]
    pares_b = [(o, d) for o in b_origen for d in b_destino]

    for etiqueta, pares in (("A", pares_a), ("B", pares_b)):
        if len(pares) < por_condicion:
            raise ValueError(
                f"Se piden {por_condicion} misiones distintas de condicion "
                f"{etiqueta} y el catalogo solo permite {len(pares)} pares. "
                f"Sortear con reposicion las completaria repitiendo, que es lo "
                f"que la decision 2 de la cabecera descarta; hay que ampliar el "
                f"catalogo o bajar N.")

    # UN SOLO Random para todo el sorteo. Con uno por condicion, dos semillas
    # distintas podrian dar la misma mitad A por casualidad y nadie lo notaria.
    rnd = random.Random(semilla)
    misiones = (
        [{"condicion": "A", "origen_id": o, "destino_id": d}
         for o, d in rnd.sample(pares_a, por_condicion)]
        + [{"condicion": "B", "origen_id": o, "destino_id": d}
           for o, d in rnd.sample(pares_b, por_condicion)])

    # Decision 3: el orden del archivo es el orden temporal de la campana.
    rnd.shuffle(misiones)
    for i, m in enumerate(misiones, start=1):
        m["n"] = i
    return misiones


def escribir_csv(ruta, misiones, catalogo, meta):
    """Escribe el listado. La cabecera '#' lleva lo que hace falta para repetirlo.

    Las lineas de metadatos van dentro del propio CSV y no en un archivo aparte
    porque una semilla guardada aparte se separa de sus datos en cuanto alguien
    copia uno de los dos. Para leerlo con csv basta filtrar las lineas que
    empiezan por '#'; con pandas, read_csv(..., comment='#').
    """
    nombres = {p["id"]: p["nombre"] for p in catalogo}
    with open(ruta, "w", newline="") as f:
        for clave, valor in meta.items():
            f.write(f"# {clave}: {valor}\n")
        w = csv.writer(f)
        w.writerow(["n", "condicion", "origen_id", "destino_id",
                    "origen_nombre", "destino_nombre"])
        for m in misiones:
            w.writerow([m["n"], m["condicion"], m["origen_id"], m["destino_id"],
                        nombres[m["origen_id"]], nombres[m["destino_id"]]])


def _avisar_si_install_difiere(ruta_catalogo, huella):
    """El coordinador lee el catalogo de install/, no el del repositorio.

    Si los dos difieren, este sorteo se hizo sobre un catalogo y la campana
    correria sobre otro, con destinos que podrian ni existir. Es un aviso y no
    un error: puede que el workspace no este compilado en esta maquina, y eso no
    invalida el sorteo. Se escribe con $HOME sin expandir a proposito.
    """
    ruta = os.path.expanduser(os.path.join(
        "~", "deepracer_sim_ws", "install", "deepracer_bringup", "share",
        "deepracer_bringup", "config", os.path.basename(ruta_catalogo)))
    if not os.path.exists(ruta):
        return
    if sha256_de(ruta) != huella:
        print("   AVISO: el catalogo de install/ NO coincide con el del "
              "repositorio.", file=sys.stderr)
        print("          El coordinador lee el de install/, asi que la campana "
              "correria", file=sys.stderr)
        print("          sobre puntos distintos de los que se acaban de "
              "sortear. Recompila", file=sys.stderr)
        print("          deepracer_bringup antes de la primera corrida.",
              file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Sortea las misiones de la campana de OE4 (§6.3 del protocolo).")
    p.add_argument("--semilla", type=int, required=True,
                   help="Semilla del sorteo. Se anota en el CSV y en el informe.")
    p.add_argument("--n", type=int, default=30,
                   help="Numero de misiones, par. Por defecto 30 (RF-26).")
    p.add_argument("--salida", required=True, help="Ruta del CSV a escribir.")
    p.add_argument("--catalogo", default=CATALOGO_POR_DEFECTO,
                   help="puntos_interes.yaml. Por defecto el del repositorio.")
    args = p.parse_args(argv)

    # ANTES de sortear nada, por la decision 4 de la cabecera.
    if os.path.exists(args.salida):
        print(f"ERROR: '{args.salida}' ya existe y no se sobrescribe.",
              file=sys.stderr)
        print("       Si de verdad quieres otro sorteo, borralo a mano o cambia "
              "--salida.", file=sys.stderr)
        print("       Pisarlo a mitad de campana dejaria unas corridas contra un "
              "listado", file=sys.stderr)
        print("       y otras contra otro, sin que nada en los registros lo "
              "delatara.", file=sys.stderr)
        return 1

    if not os.path.exists(args.catalogo):
        print(f"ERROR: no encuentro el catalogo '{args.catalogo}'.",
              file=sys.stderr)
        print("       Esta herramienta se lanza desde la raiz del repositorio.",
              file=sys.stderr)
        return 1

    catalogo = cargar_catalogo(args.catalogo)
    huella = sha256_de(args.catalogo)
    misiones = sortear(catalogo, args.n, args.semilla)

    meta = {
        "campana": "OE4 - simulacion (RF-26)",
        "protocolo": "Documentos/PROTOCOLO_EXPERIMENTAL.md §6.2 y §6.3",
        "sorteado": datetime.date.today().isoformat(),
        "semilla": args.semilla,
        "n": args.n,
        "catalogo": args.catalogo,
        "catalogo_sha256": huella,
        "orden": "el de este archivo, sin reordenar (§6.3)",
    }
    escribir_csv(args.salida, misiones, catalogo, meta)

    cuenta = {"A": 0, "B": 0}
    for m in misiones:
        cuenta[m["condicion"]] += 1
    print(f"   {len(misiones)} misiones sorteadas: {cuenta['A']} de condicion A "
          f"y {cuenta['B']} de condicion B")
    print(f"   semilla {args.semilla}, catalogo sha256 {huella[:16]}...")
    print(f"   escrito en {args.salida}")
    _avisar_si_install_difiere(args.catalogo, huella)
    return 0


if __name__ == "__main__":
    sys.exit(main())
