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

  1. Sacar del .world el rectangulo que ocupa cada pared, a la altura de corte.
  2. Crear una cuadricula donde TODO empieza como desconocido.
  3. Pintar de ocupado las celdas que toca cada rectangulo.
  4. Rellenar de libre desde donde arranca el robot, avanzando celda a celda
     sin atravesar ocupado. Lo que el relleno no alcanza se queda desconocido.

Tres detalles que no son obvios
-------------------------------
EL BLOQUE <state>. Cuando un .world se guarda desde la ventana de Gazebo queda
al final un bloque <state> con la posicion de cada pared. Gazebo aplica ese
bloque al cargar, asi que manda sobre las posiciones escritas en <model>.

Los dos bloques no estan en el mismo marco, y por eso se leen distinto: la pose
de <state> es ABSOLUTA, referida al mundo, mientras que la de un <link> dentro
de <model> es RELATIVA al origen de su modelo. Para comparar hay que componer,
que es lo que hace el paso 1a sumando la pose del modelo a la del enlace. Sin
esa suma, un modelo colocado lejos del origen aparenta una discrepancia igual a
su propia pose: en primer_piso_v2.world son 21 metros. No los hay. Compuestas,
las doce paredes coinciden en los dos bloques con residuo menor a 0,1 mm.

Se sigue leyendo <state> porque es lo que Gazebo aplica —si alguien mueve una
pared en la ventana y guarda, ahi queda—, no porque contradiga a <model>.

EL PASILLO ESTA ABIERTO. No tiene pared de fondo en ninguno de sus dos
extremos, asi que el relleno del paso 4 se sale del edificio y marca libre el
mundo entero. Por eso existe --region: pone un limite explicito a la zona que
se declara mapeada. Fuera de ahi queda desconocido, que es lo que tendria un
robot real que nunca fue a mirar.

UN MAPA 2D ES UN CORTE, NO UNA SOMBRA. Mientras el mundo tuvo un solo nivel la
distincion daba igual: proyectar todas las cajas al plano o cortarlas a la
altura del LiDAR daba el mismo dibujo. Con dos niveles deja de darlo. En
primer_piso_dos_niveles.world la losa del nivel 2 es una caja de 50 x 20 m a
z=2,95: proyectada, tapa el mapa entero de ocupado; cortada a la altura del
LiDAR, no aparece, que es justo lo que ve el robot. Por eso el paso 1 descarta
toda caja cuyo tramo vertical no cruce --altura.

Y por eso el mismo mundo produce un mapa distinto segun donde se corte:
--altura 0.30 da el nivel 1 y --altura 3.30 da el nivel 2. Que los dos salgan
identicos no es casualidad ni error, es la comprobacion de que las dos plantas
son la misma geometria, que es lo que permite navegar los dos niveles con un
solo mapa.

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


def paredes_del_mundo(ruta, altura):
    """Devuelve una lista de paredes, cada una como sus cuatro vertices en metros."""
    mundo = ET.parse(ruta).getroot().find('world')
    if mundo is None:
        sys.exit(f"{ruta} no contiene un elemento <world>.")

    # Paso 1a: tamano y posicion de cada pared, mirando tanto los <model>
    # escritos en el propio .world como los que entran por <include>.
    tamano = {}
    posicion = {}
    grosor = {}
    for nombre, (mx, my, mz, myaw), elemento in modelos_del_mundo(mundo, ruta):
        for link in elemento.findall('link'):
            # Solo <collision>: una pared es lo que el LiDAR choca, no lo que se
            # dibuja. Los enlaces con visual pero sin colision -como la marca de
            # la zona de transicion- no son obstaculos y no deben salir al mapa.
            caja = next((c for col in link.findall('collision')
                         for c in col.iter('box')), None)
            if caja is None:
                continue                      # ese link no es una pared
            if abs(myaw) > 0.02:
                sys.exit(f"El modelo '{nombre}' esta girado {math.degrees(myaw):.1f} grados. "
                         "Este programa suma la pose del modelo a la del enlace, no compone "
                         "rotaciones, asi que dibujaria las paredes en el sitio equivocado.")
            clave = (nombre, link.get('name'))
            ancho, largo, alto = [float(v) for v in caja.find('size').text.split()][:3]
            tamano[clave] = (ancho, largo)
            grosor[clave] = alto
            lx, ly, lz, lyaw = leer_pose(link)
            posicion[clave] = (mx + lx, my + ly, mz + lz, lyaw)

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

    # Paso 1c: quedarse solo con lo que cruza la altura de corte (ver cabecera).
    dentro = [c for c in tamano
              if posicion[c][2] - grosor[c] / 2 <= altura <= posicion[c][2] + grosor[c] / 2]
    fuera = len(tamano) - len(dentro)

    print(f"  paredes encontradas      : {len(tamano)}")
    print(f"  posiciones desde <state> : {corregidas}"
          + ("" if corregidas else "   (el .world no trae bloque <state>)"))
    print(f"  cortando a z = {altura:.2f} m    : {len(dentro)} paredes"
          + (f"   ({fuera} fuera del corte)" if fuera else ""))

    return [rectangulo(posicion[c], tamano[c]) for c in dentro]


def modelos_del_mundo(mundo, ruta_world):
    """Cada modelo del mundo como (nombre, pose absoluta, elemento <model>).

    Un .world puede traer los modelos escritos dentro o referirlos con
    <include><uri>model://x</uri></include>. Gazebo trata las dos formas igual;
    leer solo la primera es el motivo de que este programa encontrara 1 pared
    en vez de 12 en el mundo de dos niveles, donde la planta entra por
    <include> e instanciada dos veces.
    """
    for modelo in mundo.findall('model'):
        yield modelo.get('name'), leer_pose(modelo), modelo

    for inc in mundo.findall('include'):
        uri = (inc.findtext('uri') or '').strip()
        carpeta = carpeta_del_modelo(uri, ruta_world)
        if carpeta is None:
            sys.exit(f"No se pudo resolver {uri!r}, incluido por {ruta_world}.\n"
                     "Se busca en la carpeta del propio .world, en GAZEBO_MODEL_PATH y en "
                     "~/.gazebo/models.\nSi el modelo esta en otro sitio, anadirlo a "
                     "GAZEBO_MODEL_PATH antes de ejecutar.")
        archivo = sdf_del_modelo(carpeta)
        if archivo is None:
            sys.exit(f"{carpeta} no contiene un .sdf utilizable (ni el que declara "
                     "model.config ni model.sdf).")
        modelo = ET.parse(archivo).getroot().find('model')
        if modelo is None:
            sys.exit(f"{archivo} no contiene un elemento <model>.")
        # El <pose> de un <include> SUSTITUYE a la que trae el modelo incluido,
        # no se suma a ella. Sumarlas no dio problema mientras el unico modelo
        # incluido fue primer_piso, cuya pose propia es 0 0 0. mundo_Definitivo
        # declara 0.752962 -0.165006 y ahi el mapa salia corrido tres cuartos de
        # metro en x; se detecto porque el LiDAR situaba las paredes del pasillo
        # 0.75 m al oeste de donde las ponia el mapa.
        if inc.find('pose') is not None:
            pose = leer_pose(inc)
        else:
            pose = leer_pose(modelo)
        nombre = (inc.findtext('name') or modelo.get('name') or uri)
        yield nombre.strip(), pose, modelo


def carpeta_del_modelo(uri, ruta_world):
    """Carpeta de un 'model://nombre', o None si no aparece por ningun lado.

    Se mira primero junto al .world: asi un repositorio recien clonado funciona
    sin exportar nada, que es cuando menos se sabe que hay que exportar algo.
    """
    if not uri.startswith('model://'):
        return None
    nombre = uri[len('model://'):].strip('/')
    bases = [os.path.dirname(os.path.abspath(ruta_world))]
    bases += [d for d in os.environ.get('GAZEBO_MODEL_PATH', '').split(':') if d]
    bases.append(os.path.expanduser('~/.gazebo/models'))
    for base in bases:
        carpeta = os.path.join(base, nombre)
        if os.path.isdir(carpeta):
            return carpeta
    return None


def sdf_del_modelo(carpeta):
    """El .sdf que declara model.config; si no lo declara, model.sdf."""
    config = os.path.join(carpeta, 'model.config')
    if os.path.isfile(config):
        declarado = ET.parse(config).getroot().findtext('sdf')
        if declarado:
            ruta = os.path.join(carpeta, declarado.strip())
            if os.path.isfile(ruta):
                return ruta
    ruta = os.path.join(carpeta, 'model.sdf')
    return ruta if os.path.isfile(ruta) else None


def leer_pose(elemento):
    """(x, y, z, yaw) de un <pose>; (0, 0, 0, 0) si el elemento no lo declara."""
    pose = elemento.find('pose')
    if pose is None:
        return (0.0, 0.0, 0.0, 0.0)
    v = [float(k) for k in pose.text.split()]
    return (v[0], v[1], v[2], v[5])


def rectangulo(pos, tam):
    """Convierte pared (centro + giro + tamano) en sus cuatro vertices.

    Antes esto devolvia un rectangulo alineado con los ejes y abortaba ante
    cualquier pared en diagonal, porque en primer_piso las 12 paredes estaban a
    0, 90, 180 o 270 grados. mundo_Definitivo trae dos que no lo estan -Wall_154
    a 177,53 y Wall_69 a -91,43 grados-, asi que hay que girarlas de verdad:
    aproximarlas al angulo recto mas cercano desplazaria su extremo lejano
    varios centimetros.
    """
    cx, cy, _, yaw = pos
    ancho, largo = tam
    ca, sa = math.cos(yaw), math.sin(yaw)
    return [(cx + ca * u - sa * v, cy + sa * u + ca * v)
            for u, v in ((-ancho / 2, -largo / 2), (ancho / 2, -largo / 2),
                         (ancho / 2, largo / 2), (-ancho / 2, largo / 2))]


def se_tocan(a, b):
    """Si dos rectangulos convexos comparten area, por el teorema del eje separador.

    Basta con probar las normales de los lados de ambos: si en alguna de ellas
    las proyecciones no se solapan, los rectangulos no se tocan. Se usa '<=' a
    proposito, de modo que rozarse por el borde NO cuenta como tocarse: una
    pared cuyo canto cae justo en la linea entre dos celdas no debe pintar la
    celda de al lado. Ese criterio -area compartida mayor que cero- es
    exactamente el que daba el floor/ceil de la version anterior, y por eso los
    mapas de mundos en angulo recto salen identicos byte a byte.
    """
    for poligono in (a, b):
        for i in range(len(poligono)):
            x1, y1 = poligono[i]
            x2, y2 = poligono[(i + 1) % len(poligono)]
            ex, ey = -(y2 - y1), x2 - x1          # normal del lado
            pa = [ex * x + ey * y for x, y in a]
            pb = [ex * x + ey * y for x, y in b]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def crear_cuadricula(paredes, res, regiones, margen):
    """Cuadricula llena de DESCONOCIDO, y la esquina (x, y) a la que corresponde."""
    if regiones:
        x0 = min(r[0] for r in regiones)
        y0 = min(r[1] for r in regiones)
        x1 = max(r[2] for r in regiones)
        y1 = max(r[3] for r in regiones)
    else:
        xs = [x for pared in paredes for x, _ in pared]
        ys = [y for pared in paredes for _, y in pared]
        x0, x1 = min(xs) - margen, max(xs) + margen
        y0, y1 = min(ys) - margen, max(ys) + margen
    columnas = int(math.ceil((x1 - x0) / res))
    filas = int(math.ceil((y1 - y0) / res))
    rejilla = [bytearray([DESCONOCIDO]) * columnas for _ in range(filas)]
    return rejilla, x0, y0


def pintar_paredes(rejilla, paredes, x0, y0, res):
    """Marca OCUPADO toda celda que una pared toque, aunque sea en parte.

    Se pinta cualquier celda con area compartida, por pequena que sea, nunca
    solo las que quedan cubiertas del todo: una pared de 0.15 m no llena tres
    celdas de 0.06 m, y si se exigiera cobertura completa el planificador
    encontraria rendijas por donde colar una ruta a traves de la pared.
    """
    filas, columnas = len(rejilla), len(rejilla[0])
    for pared in paredes:
        # La caja que envuelve a la pared acota que celdas hay que mirar. Para
        # una pared en angulo recto la caja es la pared misma y la prueba de
        # abajo acierta siempre; para una en diagonal sobran celdas en las
        # esquinas, y de esas se encarga se_tocan().
        xs = [x for x, _ in pared]
        ys = [y for _, y in pared]
        c_ini = max(0, int(math.floor((min(xs) - x0) / res)))
        c_fin = min(columnas, int(math.ceil((max(xs) - x0) / res)))
        f_ini = max(0, int(math.floor((min(ys) - y0) / res)))
        f_fin = min(filas, int(math.ceil((max(ys) - y0) / res)))
        for fila in range(f_ini, f_fin):
            cy = y0 + fila * res
            for col in range(c_ini, c_fin):
                if rejilla[fila][col] == OCUPADO:
                    continue
                cx = x0 + col * res
                celda = [(cx, cy), (cx + res, cy), (cx + res, cy + res), (cx, cy + res)]
                if se_tocan(celda, pared):
                    rejilla[fila][col] = OCUPADO


def rellenar_libre(rejilla, x0, y0, res, semilla, regiones):
    """Marca LIBRE lo alcanzable desde la semilla sin atravesar una pared.

    El relleno no sale de las regiones declaradas. Eso no es un adorno: el
    pasillo de mundo_Definitivo tiene una veintena de puertas de 0,65 m a
    habitaciones que nadie modelo, y por cada una el relleno se escapa a un
    vacio donde no hay nada que lo detenga. Sin este limite el mapa del piso 1
    salia 94 % libre, con Nav2 atajando en linea recta por fuera del pasillo.
    """
    filas, columnas = len(rejilla), len(rejilla[0])

    def declarada(f, c):
        if not regiones:
            return True
        cx, cy = x0 + (c + 0.5) * res, y0 + (f + 0.5) * res
        return any(rx0 <= cx <= rx1 and ry0 <= cy <= ry1
                   for rx0, ry0, rx1, ry1 in regiones)

    col = int((semilla[0] - x0) / res)
    fila = int((semilla[1] - y0) / res)
    if not (0 <= col < columnas and 0 <= fila < filas) or not declarada(fila, col):
        sys.exit(f"El punto de arranque {semilla} cae fuera de la zona del mapa.")
    if rejilla[fila][col] == OCUPADO:
        sys.exit(f"El punto de arranque {semilla} cae DENTRO de una pared. "
                 "Revisar la pose de spawn del robot, o pasar --semilla.")

    rejilla[fila][col] = LIBRE
    pendientes = [(fila, col)]
    while pendientes:
        f, c = pendientes.pop()
        for vf, vc in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
            if (0 <= vf < filas and 0 <= vc < columnas
                    and rejilla[vf][vc] == DESCONOCIDO and declarada(vf, vc)):
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
        f.write("# No editar a mano. Regenerar con esta orden, que es la que lo hizo:\n")
        # Se escribe la orden entera, no solo el nombre del programa. Una planta
        # en L pide varios '--region', y esos rectangulos son una decision, no
        # algo que se deduzca del mundo: sin dejarlos escritos aqui el mapa no
        # se puede rehacer igual, y lo que no se puede rehacer no se corrige.
        orden = ['herramientas/' + os.path.basename(sys.argv[0])] + sys.argv[1:]
        f.write("#   python3 " + " ".join(orden) + "\n")
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
    ap.add_argument('--region', type=float, nargs=4, action='append', default=None,
                    metavar=('X0', 'Y0', 'X1', 'Y1'),
                    help='limite de la zona a declarar mapeada; hace falta si el recinto '
                         'esta abierto por algun extremo. Se puede repetir, y entonces la '
                         'zona es la union: asi se describe una planta en L sin meter en '
                         'ella el vacio que queda dentro de su rectangulo envolvente')
    ap.add_argument('--margen', type=float, default=1.0,
                    help='margen alrededor de las paredes cuando no se pasa --region')
    ap.add_argument('--altura', type=float, default=0.30, metavar='Z',
                    help='altura del corte horizontal, en metros sobre el suelo del mundo '
                         '(0.30 es la del LiDAR sobre el nivel 1). En un mundo de varios '
                         'niveles, es lo que elige cual se mapea: 3.30 para el nivel 2')
    args = ap.parse_args()

    print(f"Mundo: {args.mundo}")
    paredes = paredes_del_mundo(args.mundo, args.altura)
    if not paredes:
        sys.exit(f"Ninguna pared (<box>) cruza z = {args.altura:.2f} m. Si el mundo tiene "
                 "varios niveles, revisar --altura: cada nivel se mapea por separado.")

    res = args.resolucion
    rejilla, x0, y0 = crear_cuadricula(paredes, res, args.region, args.margen)
    pintar_paredes(rejilla, paredes, x0, y0, res)
    rellenar_libre(rejilla, x0, y0, res, args.semilla, args.region)
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
