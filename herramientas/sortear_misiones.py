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


LAS CINCO DECISIONES QUE HUBO QUE TOMAR, Y QUE EL PROTOCOLO NO FIJA
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

5. NINGUN ESTRATO SALE MAS DE TRES VECES SEGUIDAS (RACHA_MAXIMA). Barajar es
   necesario pero no suficiente para lo que pide la decision 3. El sorteo del
   2026-09-04 saco CINCO de las siete B21 consecutivas, en las misiones 15 a
   19; medido sobre esa composicion, una racha de 5 o mas sale el 3,7 % de las
   veces. Cinco bajadas pegadas caen todas en el mismo tramo de la sesion, y
   ahi el equipo lleva las mismas horas encendido, el RTF ha derivado lo mismo
   y el operador esta igual de cansado: si las bajadas salieran peor, no
   habria forma de distinguir "peor porque es una bajada" de "peor porque se
   corrio a esa hora". Es el mismo confundido que el de piso y condicion, con
   el tiempo en lugar del piso.

   La regla se declara AQUI y en el §6.3, antes de sortear, y se aplica a
   cualquier semilla: se baraja y se vuelve a barajar hasta que se cumpla. Eso
   es lo que la separa de probar semillas hasta que el resultado guste, que
   seria elegir el orden a mano -exactamente lo que el §6.3 prohibe-. No se
   elige un resultado: se elige una regla, y queda escrita.

   El limite es 3 y no 2 porque con 2 la restriccion empieza a moldear el
   sorteo de verdad: solo el 35 % de los barajados la cumple, contra el 81 %
   con 3. Cuanto mas aprieta la regla, menos aleatorio es lo que sale.
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

# Los cuatro estratos de la enmienda del 2026-09-04 al §6.2: nombre -> (nivel
# de origen, nivel de destino, condicion). Ver sortear_estratificado.
ESTRATOS = {
    "A1": (1, 1, "A"),
    "A2": (2, 2, "A"),
    "B12": (1, 2, "B"),
    "B21": (2, 1, "B"),
}

# Ningun estrato puede aparecer mas de tres veces seguidas en el orden de
# ejecucion. Es la aleatorizacion restringida del 2026-09-04; el porque esta en
# la decision 5 de la cabecera.
RACHA_MAXIMA = 3

# Cuantos barajados se prueban antes de dar la composicion por imposible. Con
# los cupos reales (4, 7, 2, 7) el 81 % de los barajados ya cumple, asi que
# esto solo se agota cuando de verdad no hay solucion -por ejemplo un cupo de
# un solo estrato- y entonces hay que decirlo en vez de girar para siempre.
INTENTOS_DE_BARAJADO = 1000


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


def maxima_racha(secuencia):
    """La tirada mas larga de elementos iguales consecutivos."""
    if not secuencia:
        return 0
    mejor = actual = 1
    for i in range(1, len(secuencia)):
        actual = actual + 1 if secuencia[i] == secuencia[i - 1] else 1
        mejor = max(mejor, actual)
    return mejor


def _cola_de(estratos_previos, racha_maxima):
    """La racha con la que termina lo ya corrido, recortada al limite.

    Se recorta porque un prefijo que YA incumple la regla no se puede arreglar
    -esas misiones ya se corrieron- y exigir que el total cumpla dejaria el
    sorteo sin solucion. Las misiones 6 a 9 de la campana son cuatro B12
    seguidas, asi que este caso no es hipotetico. Lo unico exigible al sorteo
    nuevo es que no ALARGUE la racha que se encontro.
    """
    if not estratos_previos:
        return []
    ultimo = estratos_previos[-1]
    largo = 0
    for e in reversed(estratos_previos):
        if e != ultimo:
            break
        largo += 1
    return [ultimo] * min(largo, racha_maxima)


def estrato_de(catalogo, origen_id, destino_id):
    """El estrato al que pertenece una mision, deducido de los niveles.

    Se deduce y no se anota porque las 10 primeras misiones de la campana se
    sortearon antes de que los estratos existieran y su CSV no lleva la
    columna. Una columna escrita a mano se desincroniza; esta no puede.
    """
    nivel = {p["id"]: int(p["nivel"]) for p in catalogo}
    for punto in (origen_id, destino_id):
        if punto not in nivel:
            raise ValueError(
                f"'{punto}' no esta en el catalogo, asi que no se le puede "
                f"asignar un estrato.")
    par = (nivel[origen_id], nivel[destino_id])
    for nombre, (n_origen, n_destino, _) in ESTRATOS.items():
        if (n_origen, n_destino) == par:
            return nombre
    raise ValueError(
        f"La mision {origen_id} -> {destino_id} va del piso {par[0]} al "
        f"{par[1]} y ningun estrato cubre ese caso. El edificio del §6.1 solo "
        f"tiene dos pisos.")


def leer_csv(ruta):
    """Devuelve (metadatos, filas) de un listado ya escrito por escribir_csv.

    Hace falta para continuar una campana empezada: los pares de las misiones
    ya corridas son justamente los que no se pueden volver a sortear, y la
    unica fuente fiable de cuales fueron es el archivo que se versiono antes de
    la primera corrida.
    """
    meta, lineas = {}, []
    with open(ruta) as f:
        for linea in f:
            if linea.startswith("#"):
                clave, _, valor = linea[1:].partition(":")
                meta[clave.strip()] = valor.strip()
            else:
                lineas.append(linea)
    filas = list(csv.DictReader(lineas))
    for fila in filas:
        fila["n"] = int(fila["n"])
    return meta, filas


def pares_del_estrato(catalogo, estrato, excluidos=()):
    """Todos los pares (origen, destino) posibles de un estrato, menos los gastados.

    Devuelve la lista ORDENADA, por el mismo motivo que 'elegibles': el sorteo
    no puede depender del orden del YAML.
    """
    if estrato not in ESTRATOS:
        raise ValueError(
            f"El estrato '{estrato}' no existe. Los definidos son "
            f"{', '.join(sorted(ESTRATOS))}.")
    n_origen, n_destino, _ = ESTRATOS[estrato]
    fuera = {tuple(p) for p in excluidos}
    return sorted(
        (o, d)
        for o in elegibles(catalogo, n_origen)
        for d in elegibles(catalogo, n_destino)
        if o != d and (o, d) not in fuera)


def sortear_estratificado(catalogo, cupos, semilla, excluidos=(), desde=1,
                          racha_maxima=RACHA_MAXIMA, estratos_previos=()):
    """Misiones repartidas entre los cuatro estratos de ESTRATOS.

    'cupos' es {estrato: cuantas}, 'excluidos' los pares ya gastados y 'desde'
    el numero de la primera mision. Devuelve la misma forma que sortear() mas
    la clave 'estrato'.

    'racha_maxima' es la decision 5: ningun estrato mas de esas veces seguidas.
    Con None se desactiva, y eso solo vale para comprobar en una prueba que la
    regla cambia algo; una campana no se sortea sin ella. 'estratos_previos'
    son los estratos de las misiones ya fijadas antes de esta tanda, para que
    la racha se cuente tambien en la frontera: la campana se corre del 1 al 30
    seguido, asi que una racha a caballo entre lo viejo y lo nuevo es una
    racha igual.

    POR QUE NO BASTA CON sortear()
    ------------------------------
    El §6.2 original hacia la condicion A entera en el piso 1 y la B del 1 al
    2. Asi la B se diferencia de la A en DOS cosas a la vez -llevar relevo y
    pisar el piso 2- y ninguna medida las separa: si la B sale peor, no se
    puede decir si es por el relevo o porque el piso 2 es mas dificil, que es
    exactamente lo que la campana pretende medir. Los cuatro estratos cruzan
    condicion con piso y dejan el contraste A-contra-B en 15 y 15.

    'excluidos' existe porque las 10 primeras misiones YA se corrieron con el
    sorteo antiguo. Sus pares estan gastados: repetir uno quemaria una de las
    30 corridas sin cubrir un destino nuevo (decision 2 de la cabecera).
    """
    if not cupos:
        raise ValueError(
            "No se pidio ningun cupo. Hay que decir cuantas misiones lleva "
            f"cada estrato, por ejemplo {{'A1': 4, 'A2': 7}}. Estratos "
            f"definidos: {', '.join(sorted(ESTRATOS))}.")

    disponibles = {}
    for estrato, cupo in cupos.items():
        pares = pares_del_estrato(catalogo, estrato, excluidos)
        if cupo > len(pares):
            raise ValueError(
                f"Se piden {cupo} misiones distintas del estrato {estrato} y "
                f"solo quedan {len(pares)} pares tras descontar los "
                f"{len(list(excluidos))} ya gastados. Hay que ampliar el "
                f"catalogo o bajar el cupo; completar repitiendo es lo que la "
                f"decision 2 de la cabecera descarta.")
        disponibles[estrato] = pares

    # UN SOLO Random, y los estratos recorridos en orden alfabetico: si se
    # recorrieran en el orden del dict, cambiar el orden de los argumentos
    # daria misiones distintas con la misma semilla.
    rnd = random.Random(semilla)
    misiones = []
    for estrato in sorted(cupos):
        condicion = ESTRATOS[estrato][2]
        for o, d in rnd.sample(disponibles[estrato], cupos[estrato]):
            misiones.append({"condicion": condicion, "estrato": estrato,
                             "origen_id": o, "destino_id": d})

    # Decisiones 3 y 5 de la cabecera: el orden del archivo es el orden
    # temporal, asi que dejarlo por estratos confundiria la deriva de la sesion
    # con el estrato, y una racha larga hace lo mismo en pequeno.
    if racha_maxima is None:
        rnd.shuffle(misiones)
    else:
        cola = _cola_de(list(estratos_previos), racha_maxima)
        for _ in range(INTENTOS_DE_BARAJADO):
            rnd.shuffle(misiones)
            if maxima_racha(cola + [m["estrato"] for m in misiones]) \
                    <= racha_maxima:
                break
        else:
            raise ValueError(
                f"Ningun barajado de estos cupos cumple la racha maxima de "
                f"{racha_maxima} en {INTENTOS_DE_BARAJADO} intentos, asi que "
                f"casi seguro no existe: con {dict(cupos)} no hay bastantes "
                f"estratos distintos para intercalarlos. Hay que repartir el "
                f"cupo entre mas estratos o subir racha_maxima, y si se sube "
                f"hay que escribir por que.")

    for i, m in enumerate(misiones, start=desde):
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
        w.writerow(["n", "condicion", "estrato", "origen_id", "destino_id",
                    "origen_nombre", "destino_nombre"])
        for m in misiones:
            # El estrato se recalcula aqui y no se copia del dict: asi las
            # misiones sorteadas antes de que los estratos existieran salen con
            # la columna puesta y nadie tiene que rellenarla a mano.
            w.writerow([m["n"], m["condicion"],
                        estrato_de(catalogo, m["origen_id"], m["destino_id"]),
                        m["origen_id"], m["destino_id"],
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


def parsear_cupos(texto):
    """'A1=4,A2=7,B12=2,B21=7' -> {'A1': 4, 'A2': 7, 'B12': 2, 'B21': 7}."""
    cupos = {}
    for trozo in texto.split(","):
        nombre, _, valor = trozo.strip().partition("=")
        if not valor.strip().isdigit():
            raise ValueError(
                f"No entiendo el cupo '{trozo.strip()}'. El formato es "
                f"ESTRATO=CUANTAS, por ejemplo A1=4. Estratos definidos: "
                f"{', '.join(sorted(ESTRATOS))}.")
        cupos[nombre.strip()] = int(valor)
    return cupos


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
    p.add_argument("--estratos",
                   help="Cupos por estrato, 'A1=4,A2=7,B12=2,B21=7'. Con esto "
                        "se usa el sorteo estratificado y se ignora --n.")
    p.add_argument("--continuar-de", dest="continuar_de",
                   help="CSV de una campana ya empezada. Sus primeras "
                        "--conservar misiones se copian tal cual y sus pares "
                        "quedan excluidos del sorteo nuevo.")
    p.add_argument("--conservar", type=int, default=0,
                   help="Cuantas misiones de --continuar-de ya se corrieron.")
    args = p.parse_args(argv)

    if args.continuar_de and not args.estratos:
        print("ERROR: --continuar-de solo tiene sentido con --estratos.",
              file=sys.stderr)
        print("       Continuar una campana con el sorteo antiguo daria otra "
              "vez", file=sys.stderr)
        print("       misiones de un solo estrato, que es lo que la enmienda "
              "del", file=sys.stderr)
        print("       §6.2 corrige.", file=sys.stderr)
        return 1

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

    meta = {
        "campana": "OE4 - simulacion (RF-26)",
        "protocolo": "Documentos/PROTOCOLO_EXPERIMENTAL.md §6.2 y §6.3",
        "sorteado": datetime.date.today().isoformat(),
        "semilla": args.semilla,
        "catalogo": args.catalogo,
        "catalogo_sha256": huella,
        "orden": "el de este archivo, sin reordenar (§6.3)",
    }

    conservadas = []
    if args.continuar_de:
        meta_previa, filas = leer_csv(args.continuar_de)
        if args.conservar > len(filas):
            print(f"ERROR: se piden conservar {args.conservar} misiones y "
                  f"'{args.continuar_de}' solo tiene {len(filas)}.",
                  file=sys.stderr)
            return 1
        if meta_previa.get("catalogo_sha256") != huella:
            print("ERROR: el listado que se continua se sorteo sobre otro "
                  "catalogo.", file=sys.stderr)
            print("       Las misiones conservadas podrian apuntar a destinos "
                  "que ya no", file=sys.stderr)
            print("       existen, y los pares excluidos no serian los que se "
                  "corrieron.", file=sys.stderr)
            return 1
        conservadas = [{"n": f["n"], "condicion": f["condicion"],
                        "origen_id": f["origen_id"],
                        "destino_id": f["destino_id"]}
                       for f in filas[:args.conservar]]
        meta["continua"] = (f"{args.continuar_de}, misiones 1-{args.conservar} "
                            f"conservadas con su sorteo original")
        meta["semilla_previa"] = meta_previa.get("semilla", "?")

    if args.estratos:
        try:
            cupos = parsear_cupos(args.estratos)
            nuevas = sortear_estratificado(
                catalogo, cupos, args.semilla,
                excluidos=[(m["origen_id"], m["destino_id"])
                           for m in conservadas],
                desde=len(conservadas) + 1,
                estratos_previos=[
                    estrato_de(catalogo, m["origen_id"], m["destino_id"])
                    for m in conservadas])
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        meta["estratos"] = ", ".join(f"{k}={cupos[k]}" for k in sorted(cupos))
        meta["racha_maxima"] = (
            f"{RACHA_MAXIMA} misiones seguidas del mismo estrato "
            f"(§6.3, decision 5)")
    else:
        nuevas = sortear(catalogo, args.n, args.semilla)

    misiones = conservadas + nuevas
    meta["n"] = len(misiones)
    escribir_csv(args.salida, misiones, catalogo, meta)

    cuenta = {"A": 0, "B": 0}
    por_estrato = {}
    for m in misiones:
        cuenta[m["condicion"]] += 1
        e = estrato_de(catalogo, m["origen_id"], m["destino_id"])
        por_estrato[e] = por_estrato.get(e, 0) + 1
    print(f"   {len(misiones)} misiones: {cuenta['A']} de condicion A "
          f"y {cuenta['B']} de condicion B")
    print("   por estrato: "
          + ", ".join(f"{k}={por_estrato[k]}" for k in sorted(por_estrato)))
    if conservadas:
        print(f"   {len(conservadas)} conservadas de {args.continuar_de} "
              f"y {len(nuevas)} sorteadas de nuevo")
    print(f"   semilla {args.semilla}, catalogo sha256 {huella[:16]}...")
    print(f"   escrito en {args.salida}")
    _avisar_si_install_difiere(args.catalogo, huella)
    return 0


if __name__ == "__main__":
    sys.exit(main())
