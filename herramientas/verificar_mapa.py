#!/usr/bin/env python3
"""Comprueba que un mapa de ocupacion corresponda al mundo simulado.

Hace dos preguntas distintas, y las dos hacen falta:

  1. COBERTURA. ¿El mapa abarca todo el mundo? Detecta recorridos a medias.
  2. FIDELIDAD. ¿Cada obstaculo del mapa existe de verdad en el .world?
     Detecta lo contrario: paredes que el SLAM se invento por su propia deriva.
     Este es el caso peligroso, porque no se nota al mirar el mapa: se nota
     mucho despues, cuando Nav2 aborta con 'Starting point in lethal space' o,
     peor, devuelve SUCCEEDED sobre una pose de AMCL que no es la real.

Las paredes reales del mundo las lee generar_mapa_desde_mundo.paredes_del_mundo,
que es la unica funcion del proyecto que compone la pose del modelo con la del
link, resuelve los <include> y aplica el bloque <state>. El porque de cada cosa
esta en la cabecera de aquel archivo.

Uso:
    python3 herramientas/verificar_mapa.py <mapa.yaml> <mundo.world> [altura]

La altura es la del corte horizontal, 0.30 m si no se pasa. En un mundo de
varios niveles hay que decir cual se verifica: comparar un mapa del nivel 2
contra el corte del nivel 1 mide la geometria equivocada.

Devuelve 0 si el mapa pasa los umbrales y 1 si no. Conviene ejecutarlo ANTES de
cerrar Gazebo, para poder repetir el recorrido sin perder la sesion de mapeo.
"""

import math
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow. Instalar con: pip3 install Pillow")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generar_mapa_desde_mundo import (  # noqa: E402
    DESCONOCIDO, LIBRE, OCUPADO, PREFIJO_SINTETICO, SINTETICO, paredes_del_mundo)

# Que significa cada valor del .pgm para QUIEN LO ESCRIBIO. La comprobacion de
# coherencia de abajo contrasta esta intencion con lo que map_server deduce de
# los umbrales del .yaml, que es cosa distinta y puede no coincidir.
INTENCION = {
    LIBRE: "libre",
    OCUPADO: "ocupado",
    SINTETICO: "ocupado",       # limite sintetico: solido, pero no medido
    DESCONOCIDO: "desconocido",
}

# Umbrales de aceptacion
COBERTURA_MINIMA = 0.85     # parte de la extension del mundo que debe quedar mapeada
DESCONOCIDO_MAXIMO = 0.35   # ya no decide nada; ver la nota dentro de analizar()
FRONTERA_MAXIMA = 0.01      # parte maxima de celdas libres pegadas a lo desconocido
FANTASMA_MAXIMO = 0.05      # parte maxima de obstaculos sin pared real detras
TOLERANCIA = 0.30           # m; a que distancia se acepta que un obstaculo "corresponde"


def leer_yaml_mapa(ruta):
    """Lee los campos que necesitamos del .yaml sin depender de PyYAML."""
    texto = Path(ruta).read_text()
    campos = {}
    for clave in ("image", "resolution", "origin"):
        m = re.search(rf"^{clave}\s*:\s*(.+)$", texto, re.M)
        if m:
            campos[clave] = m.group(1).strip()
    if "resolution" not in campos or "image" not in campos:
        sys.exit(f"El archivo {ruta} no declara 'resolution' e 'image'.")
    campos["resolution"] = float(campos["resolution"])
    numeros = re.findall(r"-?\d+\.?\d*", campos.get("origin", "0 0 0"))
    campos["origin"] = [float(v) for v in numeros[:3]]
    # Los '--region' de la orden que genero el mapa, si el .yaml la trae escrita
    # en su cabecera. No es un comentario decorativo: generar_mapa_desde_mundo.py
    # la escribe solo, y esos rectangulos son la ZONA QUE SE DECLARA MAPEADA. Se
    # leen aqui porque son el denominador correcto del recuento de desconocidas
    # (ver el porque en la cabecera de analizar). Un mapa de SLAM no los trae, y
    # entonces la lista queda vacia.
    campos["regiones"] = [tuple(float(v) for v in m) for m in re.findall(
        r"--region\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)", texto)]
    for clave, defecto in (("occupied_thresh", 0.65), ("free_thresh", 0.196)):
        m = re.search(rf"^{clave}\s*:\s*([\d.]+)", texto, re.M)
        campos[clave] = float(m.group(1)) if m else defecto
    return campos


def revisar_umbrales(ruta_yaml, meta, valores):
    """¿map_server leera cada valor del .pgm como quien lo escribio pretendia?

    ESTA COMPROBACION EXISTE POR UN FALLO CONCRETO (2026-08-24). El .yaml decia
    'free_thresh: 0.25' -copiado del ejemplo de nav2- mientras el .pgm escribia
    205 para 'desconocido'. map_server calcula ocupacion = (255 - valor) / 255,
    o sea 0.196 para el 205, y llama LIBRE a todo lo que baje del umbral: 0.196
    < 0.25, luego CADA CELDA DESCONOCIDA SE CARGABA COMO LIBRE. En el mapa del
    piso 1 eran 44697 celdas, el 58,5 % del mapa, de espacio que no existe.

    Nadie lo vio porque los dos archivos son correctos por separado y solo se
    contradicen al leerlos juntos, que es justo lo que nunca se hacia. El
    sintoma llego mucho despues y disfrazado: Nav2 trazando una diagonal de 38 m
    por fuera del edificio y abortando a los 137 s.

    'allow_unknown: false' del Smac y 'track_unknown_space: true' del costmap
    global estaban BIEN puestos y no sirvieron de nada: para cuando miraban, ya
    no quedaba ninguna celda desconocida que rechazar.
    """
    problemas = []
    for v in sorted(valores):
        ocupacion = (255 - v) / 255
        if ocupacion > meta["occupied_thresh"]:
            leido = "ocupado"
        elif ocupacion < meta["free_thresh"]:
            leido = "libre"
        else:
            leido = "desconocido"
        esperado = INTENCION.get(v)
        if esperado is None:
            problemas.append(
                f"el .pgm contiene el valor {v}, que no escribe "
                f"generar_mapa_desde_mundo.py; map_server lo leera como '{leido}'")
        elif leido != esperado:
            problemas.append(
                f"el valor {v} se escribio para decir '{esperado}' y map_server lo "
                f"leera como '{leido}' (ocupacion {ocupacion:.3f} frente a "
                f"free_thresh {meta['free_thresh']} y occupied_thresh "
                f"{meta['occupied_thresh']})")
    return problemas


def extension_mundo(paredes):
    """Cuanto mide el mundo en X y en Y, de pared a pared."""
    xs = [x for pared, _ in paredes for x, _ in pared]
    ys = [y for pared, _ in paredes for _, y in pared]
    return max(xs) - min(xs), max(ys) - min(ys)


def distancia_a_pared(x, y, pared):
    """Distancia de un punto al rectangulo de una pared; 0 si esta dentro.

    Cada pared llega como sus cuatro vertices en sentido antihorario, no como
    una caja alineada con los ejes: mundo_Definitivo trae paredes en diagonal, y
    medir contra su caja envolvente daria por buena una celda ocupada que esta
    hasta 15 cm fuera de la pared de verdad.
    """
    dentro = True
    mejor = float('inf')
    for i in range(len(pared)):
        x1, y1 = pared[i]
        x2, y2 = pared[(i + 1) % len(pared)]
        ex, ey = x2 - x1, y2 - y1
        if ex * (y - y1) - ey * (x - x1) < 0:
            dentro = False                # el punto queda por fuera de ese lado
        t = ((x - x1) * ex + (y - y1) * ey) / (ex * ex + ey * ey)
        t = min(1.0, max(0.0, t))
        mejor = min(mejor, math.hypot(x - (x1 + t * ex), y - (y1 + t * ey)))
    return 0.0 if dentro else mejor


def analizar(ruta_yaml, ruta_world, altura=0.30):
    meta = leer_yaml_mapa(ruta_yaml)
    ruta_pgm = Path(ruta_yaml).parent / meta["image"]
    if not ruta_pgm.exists():
        sys.exit(f"No existe la imagen del mapa: {ruta_pgm}")

    imagen = Image.open(ruta_pgm).convert("L")
    columnas, filas = imagen.size
    res = meta["resolution"]
    origen_x, origen_y = meta["origin"][0], meta["origin"][1]
    pixel = imagen.load()

    paredes = paredes_del_mundo(ruta_world, altura)
    if not paredes:
        # Sin esto el programa moria mas abajo con 'min() arg is an empty
        # sequence', que no dice nada sobre la unica causa que lo produce:
        # verificar un mapa del nivel 2 contra el corte del nivel 1.
        sys.exit(f"Ninguna pared del mundo cruza z = {altura:.2f} m. En un mundo de "
                 "varios niveles hay que pasar la altura del nivel que se verifica "
                 "(tercer argumento); la del nivel 2 de este proyecto es 3.30.")

    # En un .pgm de nav2_map_server: 254 = libre, 0 = ocupado, 205 = desconocido,
    # y 50 = limite sintetico (ver SINTETICO en generar_mapa_desde_mundo.py).
    # La fila 0 de la imagen es la Y mayor, de ahi el (filas - 1 - f) al pasar a metros.
    conocidas = 0
    desconocidas = 0
    ocupadas = 0
    fantasmas = []                      # obstaculos del mapa sin pared real detras
    valores = set()                     # que valores aparecen de verdad en la imagen
    col_min = col_max = fila_min = fila_max = None

    regiones = meta["regiones"]
    dentro_total = 0                    # celdas dentro de la zona declarada mapeada
    dentro_desconocidas = 0

    for f in range(filas):
        y = origen_y + (filas - 1 - f + 0.5) * res
        for c in range(columnas):
            x = origen_x + (c + 0.5) * res
            v = pixel[c, f]
            valores.add(v)
            en_region = any(rx0 <= x <= rx1 and ry0 <= y <= ry1
                            for rx0, ry0, rx1, ry1 in regiones)
            if en_region:
                dentro_total += 1
            if 200 <= v <= 210:
                desconocidas += 1
                if en_region:
                    dentro_desconocidas += 1
                continue
            conocidas += 1
            col_min = c if col_min is None else min(col_min, c)
            col_max = c if col_max is None else max(col_max, c)
            fila_min = f if fila_min is None else min(fila_min, f)
            fila_max = f if fila_max is None else max(fila_max, f)
            # '> SINTETICO', no '>= 50': un limite sintetico es tan solido como
            # un muro medido y tambien tiene que tener geometria detras. Con el
            # '>=' anterior los paneles se saltaban la prueba de fidelidad, que
            # es precisamente la que confirma que estan donde se dijo.
            if v > SINTETICO:
                continue
            ocupadas += 1
            if min(distancia_a_pared(x, y, p) for p, _ in paredes) > TOLERANCIA:
                fantasmas.append(x)

    if not conocidas:
        sys.exit("El mapa no contiene ninguna celda conocida.")

    # LA FRONTERA: celdas desconocidas pegadas a espacio libre. Es donde el mapa
    # deja de saber sin que haya una pared que lo justifique, o sea un agujero
    # por el que el planificador puede sacar una ruta del edificio.
    #
    # Sustituye a la fraccion de desconocidas como criterio de rechazo. Mide la
    # misma preocupacion -- '¿el mapa esta terminado?' -- pero sin depender de
    # ningun rectangulo declarado a mano, y ademas dice DONDE. En el mapa del
    # piso 1, antes de tapiar los dieciseis vanos, la frontera tenia 174 celdas
    # repartidas en catorce sitios; despues, cero.
    libres = set()
    frontera = []
    for f in range(filas):
        for c in range(columnas):
            if pixel[c, f] == LIBRE:
                libres.add((c, f))
    for c, f in libres:
        for vc, vf in ((c + 1, f), (c - 1, f), (c, f + 1), (c, f - 1)):
            if 0 <= vc < columnas and 0 <= vf < filas and pixel[vc, vf] == DESCONOCIDO:
                frontera.append((origen_x + (vc + 0.5) * res,
                                 origen_y + (filas - 1 - vf + 0.5) * res))
    frac_frontera = len(frontera) / len(libres) if libres else 0.0

    mapeado_x = (col_max - col_min + 1) * res
    mapeado_y = (fila_max - fila_min + 1) * res
    mundo_x, mundo_y = extension_mundo(paredes)

    cobertura_x = mapeado_x / mundo_x if mundo_x else 0.0
    cobertura_y = mapeado_y / mundo_y if mundo_y else 0.0
    # QUE SE MIDE CONTRA QUE. La pregunta es '¿quedo sin mapear algo que se
    # declaro mapeado?', y el denominador honesto es la zona declarada, no la
    # caja envolvente de la imagen. La distincion no importaba mientras la planta
    # era un pasillo recto, porque entonces las dos coinciden. Con una planta en
    # L o en S deja de coincidir y por mucho: el piso 1 daba 58.5% de
    # desconocidas y el piso 2 el 65.0%, y las dos cifras eran, casi enteras, las
    # esquinas VACIAS del rectangulo que envuelve la planta -- suelo que nunca
    # estuvo dentro del edificio y que es correcto que figure como desconocido.
    # Medido sobre las regiones declaradas, el mismo piso 1 da 1.5% y el piso 2
    # da 0.1%. Un mapa de SLAM no declara regiones; ahi se mide sobre la imagen
    # entera, que para ese caso es lo que siempre se quiso.
    #
    # DESDE EL 2026-08-24 ESTA CIFRA YA NO DECIDE NADA, y se deja solo como dato.
    # La decision la toma 'frontera' (abajo), por dos motivos. El primero es que
    # las regiones dejaron de existir: se declaraban para que el relleno por
    # inundacion no se escapara por las puertas sin modelar, y ahora las puertas
    # estan tapiadas con paneles, asi que el mapa se genera sin ellas y este
    # denominador vuelve a ser la caja envolvente -- que en una planta de 41 x 6.7
    # m dentro de un rectangulo de 43 x 8.7 da un 69% de desconocidas que es
    # enteramente correcto. El segundo es que el rectangulo declarado a mano
    # nunca fue una medida, sino una promesa; la frontera si es una medida.
    if regiones and dentro_total:
        frac_desconocido = dentro_desconocidas / dentro_total
        ambito = f"dentro de las {len(regiones)} regiones declaradas"
    else:
        frac_desconocido = desconocidas / (conocidas + desconocidas)
        ambito = "sobre la imagen entera (el mapa no declara regiones)"
    frac_fantasma = len(fantasmas) / ocupadas if ocupadas else 0.0

    print(f"Mapa           : {ruta_pgm.name}  ({columnas}x{filas} px a {res} m/celda)")
    print(f"Mundo          : {Path(ruta_world).name}")
    print(f"Extension mundo: {mundo_x:6.1f} m X  x {mundo_y:5.1f} m Y")
    print(f"Extension mapa : {mapeado_x:6.1f} m X  x {mapeado_y:5.1f} m Y")
    print(f"Cobertura      : {cobertura_x:6.1%} X  x {cobertura_y:5.1%} Y")
    print(f"Celdas desconocidas: {frac_desconocido:.1%}  {ambito}")
    print(f"Obstaculos sin pared real a menos de {TOLERANCIA:.2f} m: "
          f"{len(fantasmas)} de {ocupadas} ({frac_fantasma:.1%})")
    print(f"Frontera libre/desconocido: {len(frontera)} celdas de {len(libres)} libres "
          f"({frac_frontera:.2%})")
    if frontera:
        vistos = []
        for x, y in sorted(frontera):
            if not vistos or math.hypot(x - vistos[-1][0], y - vistos[-1][1]) > 3 * res:
                vistos.append((x, y))
        print(f"  {len(vistos)} sitios distintos; los primeros:")
        for x, y in vistos[:8]:
            print(f"     x = {x:7.2f}   y = {y:6.2f}")
    incoherencias = revisar_umbrales(ruta_yaml, meta, valores)
    print(f"Umbrales del .yaml frente a los valores del .pgm: "
          + ("coherentes" if not incoherencias else f"{len(incoherencias)} INCOHERENCIAS"))
    if fantasmas:
        print("  donde se concentran (tramos de 1 m con mas de 20 celdas):")
        for metro in range(int(math.floor(min(fantasmas))), int(math.ceil(max(fantasmas))) + 1):
            cuantas = sum(1 for x in fantasmas if metro <= x < metro + 1)
            if cuantas > 20:
                print(f"     x = [{metro:4d}, {metro + 1:4d})   {cuantas:5d} celdas")
    print()

    fallos = []
    # Va la PRIMERA a proposito. Si el .pgm y el .yaml se contradicen, todas las
    # cifras de arriba estan medidas sobre un mapa distinto del que Nav2 va a
    # cargar, y discutir su cobertura antes de arreglar eso es perder el tiempo.
    for p in incoherencias:
        fallos.append("Incoherencia entre el .pgm y sus umbrales: " + p)
    if cobertura_x < COBERTURA_MINIMA:
        fallos.append(
            f"Cobertura en X del {cobertura_x:.1%} (minimo {COBERTURA_MINIMA:.0%}). "
            "Faltan tramos del recorrido."
        )
    if cobertura_y < COBERTURA_MINIMA:
        fallos.append(
            f"Cobertura en Y del {cobertura_y:.1%} (minimo {COBERTURA_MINIMA:.0%})."
        )
    if mapeado_y > mundo_y * 1.5:
        fallos.append(
            f"El mapa mide {mapeado_y:.1f} m en Y y el mundo solo {mundo_y:.1f} m. "
            "Hay celdas ocupadas fuera de la geometria real. Dos causas posibles, "
            "y conviene distinguirlas mirando el .pgm: (a) rayos sin retorno "
            "rasterizados como pared, que dibujan arcos a distancia constante -- "
            "revisar que max_laser_range este por debajo del alcance del sensor; "
            "(b) deriva de pose, que dobla o curva las paredes del corredor."
        )
    if frac_frontera > FRONTERA_MAXIMA:
        fallos.append(
            f"{len(frontera)} celdas de frontera libre/desconocido "
            f"({frac_frontera:.2%} del espacio libre, maximo {FRONTERA_MAXIMA:.0%}). "
            "El recinto esta abierto por ahi: el espacio libre toca lo desconocido "
            "sin ninguna pared en medio. Si son puertas a salas sin modelar, "
            "tapiarlas en el .world con enlaces "
            f"'{PREFIJO_SINTETICO}*' y regenerar el mapa; si es un mapa de SLAM, "
            "falta recorrer esa zona."
        )
    if frac_fantasma > FANTASMA_MAXIMO:
        fallos.append(
            f"{frac_fantasma:.1%} de los obstaculos del mapa no tienen ninguna pared "
            f"real a menos de {TOLERANCIA:.2f} m (maximo {FANTASMA_MAXIMO:.0%}). Son "
            "paredes inventadas: el planificador las trata como espacio letal y "
            "aborta rutas por zonas que en realidad estan libres."
        )

    if fallos:
        print("RECHAZADO -- no guardar este mapa como definitivo:")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("ACEPTADO -- el mapa cubre el mundo y sus obstaculos son reales.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    sys.exit(analizar(sys.argv[1], sys.argv[2],
                      float(sys.argv[3]) if len(sys.argv) == 4 else 0.30))
