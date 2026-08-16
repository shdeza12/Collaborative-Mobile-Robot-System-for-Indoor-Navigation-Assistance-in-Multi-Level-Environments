#!/usr/bin/env python3
"""Dibuja un mapa de ocupacion exacto a partir de las paredes de un .world.

Por que existe
--------------
Un mapa hecho con SLAM arrastra el error del propio robot: paredes dobles,
manchas donde el laser no devolvio nada, tramos sin cerrar. Ese mapa no da
ningun error al usarlo: AMCL converge igual y Nav2 acepta objetivos igual. El
sintoma aparece mucho despues, como 'Starting point in lethal space', o peor,
como un SUCCEEDED sobre una pose que no es la real.

Este mapa se dibuja de la geometria declarada en el .world, asi que no tiene
error por construccion. No sustituye al mapa de SLAM: sirve para medir cuanto
se desvia aquel, y como mapa de control para poder afirmar que un fallo de
navegacion NO viene del mapa.

Como funciona
-------------
Son cuatro pasos, en este orden:

  1. Sacar del .world el rectangulo que ocupa cada pared.
  2. Crear una cuadricula donde TODO empieza como desconocido.
  3. Pintar de ocupado las celdas que toca cada rectangulo.
  4. Rellenar de libre desde donde arranca el robot, avanzando celda a celda
     sin atravesar ocupado. Lo que el relleno no alcanza se queda desconocido.

Dos detalles que no son obvios
------------------------------
EL BLOQUE <state>. Cuando un .world se guarda desde la ventana de Gazebo queda
al final un bloque <state> con la posicion de cada pared. Gazebo aplica ese
bloque al cargar, asi que manda sobre las posiciones escritas en <model>. En
primer_piso_v2.world las dos difieren en 21 metros: leyendo solo <model> se
obtiene una geometria que no es la que se simula.

EL PASILLO ESTA ABIERTO. No tiene pared de fondo en ninguno de sus dos
extremos, asi que el relleno del paso 4 se sale del edificio y marca libre el
mundo entero. Por eso existe --region: pone un limite explicito a la zona que
se declara mapeada. Fuera de ahi queda desconocido, que es lo que tendria un
robot real que nunca fue a mirar.

Uso
---
    python3 herramientas/generar_mapa_desde_mundo.py primer_piso_v2.world \\
        Robot/aws-deepracer/deepracer_bringup/maps/primer_piso_definitivo \\
        --region -1.20 -1.60 42.95 4.50
"""

import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET

# Valores que espera nav2_map_server dentro del .pgm
LIBRE = 254
OCUPADO = 0
DESCONOCIDO = 205


def paredes_del_mundo(ruta):
    """Devuelve una lista de rectangulos (x_min, y_min, x_max, y_max) en metros."""
    mundo = ET.parse(ruta).getroot().find('world')
    if mundo is None:
        sys.exit(f"{ruta} no contiene un elemento <world>.")

    # Paso 1a: tamano y posicion de cada pared segun el bloque <model>.
    tamano = {}
    posicion = {}
    for modelo in mundo.findall('model'):
        mx, my = leer_pose(modelo)[:2]
        for link in modelo.findall('link'):
            # Solo <collision>: una pared es lo que el LiDAR choca, no lo que se
            # dibuja. Los enlaces con visual pero sin colision -como la marca de
            # la zona de transicion- no son obstaculos y no deben salir al mapa.
            caja = next((c for col in link.findall('collision')
                         for c in col.iter('box')), None)
            if caja is None:
                continue                      # ese link no es una pared
            clave = (modelo.get('name'), link.get('name'))
            ancho, largo = [float(v) for v in caja.find('size').text.split()][:2]
            tamano[clave] = (ancho, largo)
            lx, ly, lyaw = leer_pose(link)
            posicion[clave] = (mx + lx, my + ly, lyaw)

    # Paso 1b: si hay bloque <state>, sus posiciones mandan (ver cabecera).
    estado = mundo.find('state')
    corregidas = 0
    if estado is not None:
        for modelo in estado.findall('model'):
            for link in modelo.findall('link'):
                clave = (modelo.get('name'), link.get('name'))
                if clave in posicion:
                    posicion[clave] = leer_pose(link)
                    corregidas += 1

    print(f"  paredes encontradas      : {len(tamano)}")
    print(f"  posiciones desde <state> : {corregidas}"
          + ("" if corregidas else "   (el .world no trae bloque <state>)"))

    return [rectangulo(posicion[c], tamano[c]) for c in tamano]


def leer_pose(elemento):
    """(x, y, yaw) de un <pose>; (0, 0, 0) si el elemento no lo declara."""
    pose = elemento.find('pose')
    if pose is None:
        return (0.0, 0.0, 0.0)
    v = [float(k) for k in pose.text.split()]
    return (v[0], v[1], v[5])


def rectangulo(pos, tam):
    """Convierte pared (centro + giro + tamano) en su rectangulo en el plano.

    Las paredes de estos mundos estan giradas 0, 90, 180 o 270 grados. Con eso
    basta con intercambiar ancho y largo cuando el giro es de 90 o 270, y no
    hace falta rotar coordenadas. Si algun dia hay una pared en diagonal el
    programa avisa en vez de dibujarla mal en silencio.
    """
    cx, cy, yaw = pos
    ancho, largo = tam
    cuartos = round(yaw / (math.pi / 2))
    if abs(yaw - cuartos * math.pi / 2) > 0.02:
        sys.exit(f"Hay una pared girada {math.degrees(yaw):.1f} grados en ({cx:.2f}, {cy:.2f}). "
                 "Este programa solo sabe dibujar paredes en angulo recto.")
    if cuartos % 2:                            # girada 90 o 270 grados
        ancho, largo = largo, ancho
    return (cx - ancho / 2, cy - largo / 2, cx + ancho / 2, cy + largo / 2)


def crear_cuadricula(paredes, res, region, margen):
    """Cuadricula llena de DESCONOCIDO, y la esquina (x, y) a la que corresponde."""
    if region:
        x0, y0, x1, y1 = region
    else:
        x0 = min(p[0] for p in paredes) - margen
        y0 = min(p[1] for p in paredes) - margen
        x1 = max(p[2] for p in paredes) + margen
        y1 = max(p[3] for p in paredes) + margen
    columnas = int(math.ceil((x1 - x0) / res))
    filas = int(math.ceil((y1 - y0) / res))
    rejilla = [bytearray([DESCONOCIDO]) * columnas for _ in range(filas)]
    return rejilla, x0, y0


def pintar_paredes(rejilla, paredes, x0, y0, res):
    """Marca OCUPADO toda celda que una pared toque, aunque sea en parte."""
    filas, columnas = len(rejilla), len(rejilla[0])
    for px0, py0, px1, py1 in paredes:
        # Rango de celdas que cubre el rectangulo. Se redondea hacia afuera para
        # no dejar huecos: una pared de 0.15 m mide 2.5 celdas de 0.06 m, y si se
        # redondea hacia adentro el planificador encuentra rendijas por donde
        # colar una ruta a traves de la pared.
        c_ini = int(math.floor((px0 - x0) / res))
        c_fin = int(math.ceil((px1 - x0) / res))
        f_ini = int(math.floor((py0 - y0) / res))
        f_fin = int(math.ceil((py1 - y0) / res))
        for fila in range(max(0, f_ini), min(filas, f_fin)):
            for col in range(max(0, c_ini), min(columnas, c_fin)):
                rejilla[fila][col] = OCUPADO


def rellenar_libre(rejilla, x0, y0, res, semilla):
    """Marca LIBRE lo alcanzable desde la semilla sin atravesar una pared."""
    filas, columnas = len(rejilla), len(rejilla[0])
    col = int((semilla[0] - x0) / res)
    fila = int((semilla[1] - y0) / res)
    if not (0 <= col < columnas and 0 <= fila < filas):
        sys.exit(f"El punto de arranque {semilla} cae fuera de la zona del mapa.")
    if rejilla[fila][col] == OCUPADO:
        sys.exit(f"El punto de arranque {semilla} cae DENTRO de una pared. "
                 "Revisar la pose de spawn del robot, o pasar --semilla.")

    rejilla[fila][col] = LIBRE
    pendientes = [(fila, col)]
    while pendientes:
        f, c = pendientes.pop()
        for vf, vc in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
            if 0 <= vf < filas and 0 <= vc < columnas and rejilla[vf][vc] == DESCONOCIDO:
                rejilla[vf][vc] = LIBRE
                pendientes.append((vf, vc))


def escribir(rejilla, x0, y0, res, base, mundo):
    filas, columnas = len(rejilla), len(rejilla[0])
    carpeta = os.path.dirname(os.path.abspath(base))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    with open(base + '.pgm', 'wb') as f:
        f.write(b'P5\n')
        f.write(b'# Generado por herramientas/generar_mapa_desde_mundo.py\n')
        f.write(f'# a partir de {os.path.basename(mundo)} -- no editar a mano\n'.encode())
        f.write(f'{columnas} {filas}\n255\n'.encode())
        for fila in reversed(rejilla):      # la primera fila del .pgm es la Y mayor
            f.write(bytes(fila))

    with open(base + '.yaml', 'w') as f:
        # La linea 'mundo:' no la lee Nav2 -es un comentario-, pero si la lee
        # herramientas/verificar_repositorio.sh para comprobar que el mapa por
        # defecto salio del mundo vigente. Antes esa comprobacion se hacia por
        # NOMBRE de archivo, lo que obligaba a que el mapa se llamase igual que
        # el mundo. Aqui queda escrito el hecho, que es lo que importa.
        f.write(f"# mundo: {os.path.basename(mundo)}\n")
        f.write("# Mapa exacto de ese mundo, generado leyendo su geometria.\n")
        f.write("# Regenerar con herramientas/generar_mapa_desde_mundo.py; no editar a mano.\n")
        f.write(f"image: {os.path.basename(base)}.pgm\n")
        f.write("mode: trinary\n")
        f.write(f"resolution: {res}\n")
        f.write(f"origin: [{x0:.4f}, {y0:.4f}, 0.0]\n")
        f.write("negate: 0\n")
        f.write("occupied_thresh: 0.65\n")
        f.write("free_thresh: 0.25\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mundo', help='archivo .world de Gazebo Classic')
    ap.add_argument('salida', help='ruta de salida sin extension; se crean .pgm y .yaml')
    ap.add_argument('--resolucion', type=float, default=0.06,
                    help='metros por celda (0.06 es la que usa nav2_params del proyecto)')
    ap.add_argument('--semilla', type=float, nargs=2, default=[0.0, 0.0], metavar=('X', 'Y'),
                    help='punto libre desde el que rellenar; normalmente el spawn del robot')
    ap.add_argument('--region', type=float, nargs=4, default=None,
                    metavar=('X0', 'Y0', 'X1', 'Y1'),
                    help='limite de la zona a declarar mapeada; hace falta si el recinto '
                         'esta abierto por algun extremo')
    ap.add_argument('--margen', type=float, default=1.0,
                    help='margen alrededor de las paredes cuando no se pasa --region')
    args = ap.parse_args()

    print(f"Mundo: {args.mundo}")
    paredes = paredes_del_mundo(args.mundo)
    if not paredes:
        sys.exit("No se encontro ninguna pared (<box>) en el mundo.")

    res = args.resolucion
    rejilla, x0, y0 = crear_cuadricula(paredes, res, args.region, args.margen)
    pintar_paredes(rejilla, paredes, x0, y0, res)
    rellenar_libre(rejilla, x0, y0, res, args.semilla)
    escribir(rejilla, x0, y0, res, args.salida, args.mundo)

    filas, columnas = len(rejilla), len(rejilla[0])
    cuenta = {LIBRE: 0, OCUPADO: 0, DESCONOCIDO: 0}
    for fila in rejilla:
        for v in fila:
            cuenta[v] += 1
    total = filas * columnas

    print(f"\nMapa escrito: {args.salida}.pgm   ({columnas}x{filas} celdas a {res} m)")
    print(f"              {args.salida}.yaml  origin = [{x0:.4f}, {y0:.4f}, 0.0]")
    print(f"  abarca     : x de {x0:.2f} a {x0 + columnas * res:.2f} m, "
          f"y de {y0:.2f} a {y0 + filas * res:.2f} m")
    for nombre, valor in (('libre', LIBRE), ('ocupado', OCUPADO), ('desconocido', DESCONOCIDO)):
        print(f"  {nombre:11s}: {cuenta[valor]:7d} celdas ({100 * cuenta[valor] / total:5.1f} %)")

    if cuenta[DESCONOCIDO] == 0:
        print("\nAVISO: no quedo ninguna celda desconocida. En un recinto cerrado eso es\n"
              "       normal; si el recinto esta abierto por algun extremo significa que\n"
              "       el relleno se escapo y marco libre el exterior. Acotar con --region.")


if __name__ == '__main__':
    main()
