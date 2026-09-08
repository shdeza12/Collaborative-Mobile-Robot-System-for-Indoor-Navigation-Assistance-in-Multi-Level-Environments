#!/usr/bin/env python3
"""Empareja el 'throttle' mandado con la velocidad que el carro hizo de verdad.

QUE PREGUNTA RESPONDE, Y POR QUE HACE FALTA
-------------------------------------------
'cmdvel_to_servo_node.py' convierte /cmd_vel en ServoCtrlMsg por escalones, y
los tres umbrales salen de dividir por 'MAX_SPEED = 4,0 m/s'
(cmdvel_to_servo_pkg/constants.py):

    < 0,40 m/s        -> throttle 0,0   (nada)
    0,40 - 1,20 m/s   -> throttle 0,5
    1,20 - 2,00 m/s   -> throttle 0,8
    >= 2,00 m/s       -> throttle 1,0

Nav2 pide 0,25 m/s en curva y 0,05 en la aproximacion. Las dos caen en la
primera fila, o sea que la cadena devuelve CERO justo donde Nav2 la usa. Eso es
lo que mantiene RF-14 en amarillo.

Ese 'MAX_SPEED = 4,0 m/s' es una SUPOSICION heredada de AWS, y de ella cuelgan
los tres umbrales. Si el carro real no hace 4 m/s, la tabla entera esta corrida
y el arreglo es recalcular la escala, no tocar el mapeo -que ya se corrigio el
27-ago, con 19 comprobaciones en prueba_mapeo_servo.py-.

Esta herramienta es el Paso de analisis del Bloque 7 de HOJA_CAMPO_G2.md.

POR QUE SON DOS FICHEROS DE ENTRADA Y NO UN BAG
-----------------------------------------------
En el carro '/scan' lo publica el LiDAR arrancado sin 'sudo' y
'/ctrl_pkg/servo_msg' lo publica el teleoperador, que va con 'sudo'. Son dueños
distintos, y por la regla de los dos extremos -§6.2 de la hoja de campo- un
solo 'ros2 bag record' se lleva uno de los dos y CERO mensajes del otro, sin
decir una palabra. Por eso el procedimiento graba dos bags en paralelo, y por
eso aqui entran por separado y se emparejan por reloj.

POR QUE SE DESEMPAQUETA EL CDR A MANO
-------------------------------------
'ServoCtrlMsg' vive en 'deepracer_interfaces_pkg', que solo esta instalado en
la tarjeta (overlay /opt/aws/deepracer). Deserializar con el tipo obligaria a
analizar en el carro. El mensaje son dos 'float32' -angle y throttle- y su CDR
son doce bytes con cabecera de encapsulado: leerlo directamente cuesta cinco
lineas y deja el analisis en el portatil, que es donde estan las herramientas.

TRES SALVEDADES QUE HAY QUE LEER ANTES DE CREERSE EL NUMERO
-----------------------------------------------------------
1. La velocidad sale de la trayectoria de rf2o, que el 2026-08-26 registro
   28,23 m de 29,94 m reales: se queda CORTO un 5,7 %. O sea que las
   velocidades de aqui son ~5 % bajas. No cambia el veredicto -la pregunta es
   si hay un factor de tres- pero cualquier cifra que se publique lleva esa
   correccion o lleva la salvedad.
2. Los dos relojes no son el mismo instante. La trayectoria usa el 'stamp' de
   cabecera del barrido; ServoCtrlMsg NO TIENE cabecera, asi que su unico
   reloj es cuando el bag lo escribio. Los dos son el reloj de la tarjeta, y la
   diferencia es la latencia del transporte: milisegundos contra tramos de
   segundos. Por eso se mide sobre ventanas y no muestra a muestra.
3. Con el mando esto es una NUBE, no una curva de calibracion. El teleoperador
   escala el gatillo de forma continua hasta 'limite_normal = 0,35': no hay
   escalones sostenidos. La nube basta para decidir si MAX_SPEED se parece a la
   realidad; no basta para publicar una tabla de calibracion.

USO
    python3 herramientas/medir_escala_traccion.py <trayectoria.csv> <bag_servo>
                                                  [--ventana 1.0]
                                                  [--bin 0.05]
                                                  [--giro-max 0.2]
                                                  [--v-arranque 0.05]
                                                  [--json salida.json]

    <trayectoria.csv>  lo que produce localizar_desde_bag.sh sobre el bag de /scan
    <bag_servo>        el directorio del bag de /ctrl_pkg/servo_msg, o el .mcap

Si el bag viene de la tarjeta Jazzy y rosbag2 se queja de la 'metadata.yaml',
pasa antes 'adaptar_bag_jazzy.py', o apunta directamente al fichero .mcap.
"""

import argparse
import bisect
import csv
import io
import json
import math
import statistics
import struct
import sys

TOPICO_SERVO = '/ctrl_pkg/servo_msg'

# La misma ventana que usa medir_g2.py para decidir quieto/movido. Sobre 1 s a
# 0,5 m/s hay medio metro, diez veces el ruido del sensor.
VENTANA_S = 1.0
# Ancho de las cajas de throttle. 0,05 sobre un recorrido util de 0,35 deja
# siete cajas: suficiente para ver la forma, y bastante ancho para que cada una
# junte muestras de sobra.
BIN = 0.05
# Por debajo de esta velocidad se considera que el carro no se mueve. Es el
# mismo criterio de quietud de medir_g2.py -0,05 m sobre una ventana de 1 s-.
V_ARRANQUE = 0.05
# Cuantas muestras hacen falta en una caja para que su mediana signifique algo.
MINIMO_POR_CAJA = 5


class Fallo(Exception):
    """Algo impide dar una cifra honesta. Se aborta en vez de inventarla."""


# ------------------------------------------------------------------- lectura


def leer_trayectoria(texto, fuente='odom'):
    """Saca de un CSV de localizar_desde_bag.sh la pista [(t, x, y)] ordenada.

    Se usa 'odom' -la odometria laser- y no 'amcl', a proposito: AMCL da
    saltos cuando reconverge, y un salto sobre una ventana de 1 s se lee como
    una velocidad enorme que no ocurrio.
    """
    lector = csv.DictReader(io.StringIO(texto))
    esperadas = {'t', 'fuente', 'x', 'y'}
    if not lector.fieldnames or not esperadas.issubset(lector.fieldnames):
        raise Fallo(f'el CSV no tiene las columnas {sorted(esperadas)}; '
                    f'tiene {lector.fieldnames}')
    pista = []
    for fila in lector:
        if (fila['fuente'] or '').strip() != fuente:
            continue
        try:
            pista.append((float(fila['t']), float(fila['x']), float(fila['y'])))
        except (TypeError, ValueError):
            continue
    if len(pista) < 2:
        raise Fallo(f"la trayectoria trae {len(pista)} poses de '{fuente}': "
                    'sin dos poses no hay desplazamiento que medir')
    pista.sort()
    return pista


def desempaquetar_servo(datos):
    """Devuelve (angle, throttle) de un ServoCtrlMsg serializado en CDR.

    Los cuatro primeros bytes son el encapsulado: los dos primeros dicen la
    representacion -0x0001 es CDR little-endian, 0x0000 big-endian- y los dos
    siguientes son opciones. Detras van los dos float32 del mensaje.

    Se comprueba la longitud en vez de confiar: si algun dia el mensaje cambia,
    esto tiene que reventar y no devolver dos numeros creibles y falsos.
    """
    if len(datos) != 12:
        raise Fallo(f'un ServoCtrlMsg deberia ocupar 12 bytes en CDR y este '
                    f'ocupa {len(datos)}. O el bag no es de {TOPICO_SERVO}, o '
                    'la definicion del mensaje cambio')
    orden = '<' if datos[1] == 1 else '>'
    return struct.unpack(orden + 'ff', datos[4:12])


def leer_bag_servo(ruta, topico=TOPICO_SERVO):
    """Devuelve [(t_segundos, angle, throttle)] del bag, ordenado.

    'rosbag2_py' se importa aqui dentro y no arriba para que las funciones
    puras de este modulo -y su prueba- no necesiten ROS.
    """
    try:
        import rosbag2_py
    except ImportError as e:
        raise Fallo("falta 'rosbag2_py': carga el entorno con "
                    "'source /opt/ros/humble/setup.bash'") from e

    lector = rosbag2_py.SequentialReader()
    almacen = 'mcap' if str(ruta).endswith('.mcap') else ''
    try:
        lector.open(
            rosbag2_py.StorageOptions(uri=str(ruta), storage_id=almacen),
            rosbag2_py.ConverterOptions(input_serialization_format='cdr',
                                        output_serialization_format='cdr'))
    except Exception as e:
        raise Fallo(f'rosbag2 no pudo abrir {ruta}: {e}\n'
                    'Si el bag viene de la tarjeta Jazzy, pasa antes '
                    "'adaptar_bag_jazzy.py', o apunta directamente al .mcap") from e

    muestras = []
    while lector.has_next():
        nombre, datos, t_ns = lector.read_next()
        if nombre != topico:
            continue
        angle, throttle = desempaquetar_servo(datos)
        muestras.append((t_ns * 1e-9, angle, throttle))

    if not muestras:
        raise Fallo(
            f'el bag no trae un solo mensaje de {topico}.\n'
            'Antes de buscar un mando averiado, descarta la trampa de dueños '
            '(§10.2 de HOJA_CAMPO_G2.md): el teleoperador publica como root, y '
            'un bag grabado como usuario se queda vacio SIN DAR ERROR.')
    muestras.sort()
    return muestras


# --------------------------------------------------------------- velocidades


def velocidad_en(pista, t, ventana_s=VENTANA_S):
    """Velocidad media alrededor de 't', o None si la ventana no esta cubierta.

    Ventana centrada: se toma la pose mas antigua dentro de [t-w/2, t] y la mas
    reciente dentro de [t, t+w/2], y se divide la distancia entre ellas por el
    tiempo que las separa.

    Devuelve None -y no cero- cuando 't' cae fuera de la trayectoria o la
    ventana se queda con una sola pose. Un cero ahi seria una parada inventada,
    y las paradas son justo lo que se esta midiendo.
    """
    media = ventana_s / 2.0
    ts = [p[0] for p in pista]
    lo = bisect.bisect_left(ts, t - media)
    hi = bisect.bisect_right(ts, t + media) - 1
    if lo >= len(ts) or hi < 0 or hi <= lo:
        return None
    if not (ts[lo] <= t <= ts[hi]):
        return None
    dt = ts[hi] - ts[lo]
    if dt <= 0:
        return None
    return math.dist(pista[lo][1:3], pista[hi][1:3]) / dt


def emparejar(pista, servo, ventana_s=VENTANA_S, giro_max=None):
    """Devuelve [(throttle, velocidad)] con una entrada por muestra de servo.

    'giro_max' descarta las muestras con el volante muy girado: en una curva la
    velocidad cae por el giro y no por el throttle, y mezclarlas ensucia la
    relacion que se busca. Con None no se filtra nada.
    """
    pares = []
    for t, angle, throttle in servo:
        if giro_max is not None and abs(angle) > giro_max:
            continue
        v = velocidad_en(pista, t, ventana_s)
        if v is not None:
            pares.append((throttle, v))
    if not pares:
        raise Fallo(
            'ninguna muestra de servo cae dentro de la trayectoria.\n'
            'Los dos bags no se solapan en el tiempo: comprueba que son del '
            'mismo tramo y que los dos se grabaron a la vez. Un desfase entero '
            'suele ser que uno de los dos se arranco despues de recorrer.')
    return pares


def agrupar(pares, ancho=BIN, minimo=MINIMO_POR_CAJA):
    """Junta los pares en cajas de throttle y resume cada una.

    Se usa la MEDIANA y no la media porque la nube del mando trae transitorios
    -acelerones y frenadas- que arrastran la media y no la mediana.
    """
    if ancho <= 0:
        raise Fallo('el ancho de caja tiene que ser positivo')
    cajas = {}
    for throttle, v in pares:
        cajas.setdefault(int(abs(throttle) / ancho), []).append((throttle, v))
    filas = []
    for indice in sorted(cajas):
        grupo = cajas[indice]
        velocidades = sorted(v for _, v in grupo)
        filas.append({
            'throttle_desde': round(indice * ancho, 4),
            'throttle_hasta': round((indice + 1) * ancho, 4),
            'throttle_mediana': round(statistics.median(
                abs(t) for t, _ in grupo), 4),
            'n': len(grupo),
            'suficiente': len(grupo) >= minimo,
            'v_mediana': round(statistics.median(velocidades), 4),
            'v_min': round(velocidades[0], 4),
            'v_max': round(velocidades[-1], 4),
        })
    return filas


def umbral_arranque(filas, v_arranque=V_ARRANQUE):
    """Menor caja con muestras suficientes cuya mediana supera 'v_arranque'.

    Es el numero del dia: por debajo de ahi el carro no se mueve, asi que si
    ese umbral queda por encima de los 0,25 m/s que pide Nav2 en curva, RF-14
    NO se cierra calibrando y hay que decirlo asi.

    Devuelve None si ninguna caja llega, que tambien es un resultado: significa
    que en todo el barrido el carro nunca supero el umbral de movimiento.
    """
    for fila in filas:
        if fila['suficiente'] and fila['v_mediana'] > v_arranque:
            return fila
    return None


def max_speed_implicito(filas, minimo=MINIMO_POR_CAJA):
    """Que 'MAX_SPEED' haria falta para que la caja mas rapida cuadre.

    El mapeo de AWS es una escalera sobre 'velocidad / MAX_SPEED', asi que la
    razon velocidad_medida / throttle es el MAX_SPEED que el codigo esta
    suponiendo. No es una calibracion -la escalera no es lineal- pero situa el
    orden de magnitud, que es lo que decide si hay un factor de tres.

    Devuelve None si no hay ninguna caja con throttle util y muestras de sobra.
    """
    utiles = [f for f in filas if f['suficiente'] and f['throttle_mediana'] > 0]
    if not utiles:
        return None
    rapida = max(utiles, key=lambda f: f['throttle_mediana'])
    return round(rapida['v_mediana'] / rapida['throttle_mediana'], 3)


# ------------------------------------------------------------------- informe


def informe(filas, arranque, max_speed, v_arranque=V_ARRANQUE):
    """Arma el texto del resultado. Separado para que la prueba lo lea."""
    lineas = []
    lineas.append('  throttle        n   v mediana    v min    v max')
    lineas.append('  ----------------------------------------------')
    for f in filas:
        marca = ' ' if f['suficiente'] else '*'
        lineas.append(f"  {f['throttle_desde']:.2f}-{f['throttle_hasta']:.2f}"
                      f"{f['n']:6d}{marca}  {f['v_mediana']:8.3f} m/s"
                      f"{f['v_min']:9.3f}{f['v_max']:9.3f}")
    if any(not f['suficiente'] for f in filas):
        lineas.append(f'  (*) menos de {MINIMO_POR_CAJA} muestras: no se lee')
    lineas.append('')

    if arranque is None:
        lineas.append(f'ARRANQUE: en todo el barrido el carro nunca supero '
                      f'{v_arranque:.2f} m/s. No hay umbral que dar.')
    else:
        lineas.append(f"ARRANQUE: el carro empieza a moverse con throttle "
                      f"~{arranque['throttle_mediana']:.2f}, y ahi hace "
                      f"{arranque['v_mediana']:.3f} m/s.")
        if arranque['v_mediana'] > 0.25:
            lineas.append('  Esa velocidad minima esta POR ENCIMA de los 0,25 m/s '
                          'que Nav2 pide en curva.')
            lineas.append('  RF-14 NO se cierra calibrando: es una limitacion '
                          'medida del motor, y la aproximacion')
            lineas.append('  de Nav2 necesita otra estrategia. Se escribe asi, '
                          'no se ajusta el criterio.')
        else:
            lineas.append('  Esa velocidad cabe por debajo de los 0,25 m/s de '
                          'Nav2: RF-14 se cierra recalculando la escala.')

    if max_speed is not None:
        lineas.append('')
        lineas.append(f'MAX_SPEED implicito por la caja mas rapida: '
                      f'{max_speed:.2f} m/s, contra los 4,00 m/s que declara '
                      'constants.py.')
        if max_speed < 4.0 / 2:
            lineas.append('  Mas de un factor de dos: los tres umbrales de '
                          'traccion estan corridos y hay que recalcularlos.')
        else:
            lineas.append('  Del mismo orden: entonces el problema no es el '
                          'factor sino la resolucion de cuatro escalones.')

    lineas.append('')
    lineas.append('Recuerda las tres salvedades del encabezado de esta '
                  'herramienta antes de publicar cualquier cifra:')
    lineas.append('  rf2o se queda corto un ~5,7 %, los dos relojes difieren '
                  'en la latencia del transporte,')
    lineas.append('  y con el mando esto es una nube y no una curva de '
                  'calibracion.')
    return '\n'.join(lineas)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('trayectoria', help='CSV de localizar_desde_bag.sh')
    p.add_argument('bag_servo', help='bag de /ctrl_pkg/servo_msg, o su .mcap')
    p.add_argument('--ventana', type=float, default=VENTANA_S,
                   help='ventana de velocidad en segundos')
    p.add_argument('--bin', type=float, default=BIN, dest='ancho',
                   help='ancho de las cajas de throttle')
    p.add_argument('--giro-max', type=float, default=None,
                   help='descarta muestras con |angle| mayor que esto')
    p.add_argument('--v-arranque', type=float, default=V_ARRANQUE,
                   help='velocidad por encima de la cual se considera movido')
    p.add_argument('--json', help='vuelca el resultado tambien a este fichero')
    a = p.parse_args(argv)

    try:
        with open(a.trayectoria, encoding='utf-8') as f:
            pista = leer_trayectoria(f.read())
        servo = leer_bag_servo(a.bag_servo)
        pares = emparejar(pista, servo, a.ventana, a.giro_max)
        filas = agrupar(pares, a.ancho)
        arranque = umbral_arranque(filas, a.v_arranque)
        max_speed = max_speed_implicito(filas)
    except Fallo as e:
        print(f'\nNO SE PUEDE DAR UNA CIFRA:\n  {e}\n', file=sys.stderr)
        return 1

    print()
    print(f'{len(pista)} poses de odometria, {len(servo)} mensajes de servo, '
          f'{len(pares)} emparejados.')
    print()
    print(informe(filas, arranque, max_speed, a.v_arranque))
    print()

    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'cajas': filas, 'arranque': arranque,
                       'max_speed_implicito': max_speed,
                       'poses': len(pista), 'mensajes_servo': len(servo),
                       'emparejados': len(pares)}, f, indent=2)
        print(f'Escrito {a.json}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
