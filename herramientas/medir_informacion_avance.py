#!/usr/bin/env python3
"""Dice, SOLO con '/scan', si un sitio le da a rf2o la informacion de avance.

POR QUE EXISTE
--------------
El 2026-09-08 quedo medido que rf2o pierde el avance -y solo el avance- cuando
no hay estructura perpendicular a la marcha dentro del alcance del LiDAR. La
consecuencia practica es que se puede saber ANTES DE SALIR si un sitio se
puede mapear con esta cadena. Falta una herramienta que lo diga, y las dos que
salieron de aquel analisis no sirven aqui: 'medir_registro_odometria.py' y
'medir_visibilidad_frontal.py' necesitan verdad de terreno, y en el carro no
existe -el DeepRacer no lleva encoders-.

Esta si funciona sobre un bag real, porque no usa el movimiento para nada.

LA TRAMPA QUE ESTE GUION EVITA A PROPOSITO
------------------------------------------
El primer intento de medir esto sobre bags reales fue una metrica de "cuanto
cambia el barrido entre instantes consecutivos", y hubo que retractarla el
mismo dia: un sensor QUIETO da exactamente el mismo resultado que un entorno
SIN INFORMACION, y sobre los bags de agosto solo estaba redetectando que el
carro no se movia. Cualquier metrica que mire la diferencia entre barridos
tiene ese defecto.

Por eso aqui la medida es GEOMETRICA y de UN SOLO BARRIDO. No compara
instantes, no necesita que el carro se mueva y no puede confundirse por eso.

QUE SE MIDE, Y POR QUE NO ES "HAY PARED DE FRENTE, SI O NO"
-----------------------------------------------------------
La primera version de este guion preguntaba si existia un plano perpendicular
en un sector fijo de +-30 grados. Fallo, y el fallo enseña cual es la pregunta
buena. Este es el perfil real de un barrido del pasillo de 46,9 m:

    theta  -10..+10   r*cos(theta) = 7,32 .. 7,33   <- pared frontal REAL
    theta   |>10|     r*cos(theta) = 1,3  .. 5,7    <- paredes laterales

Si habia pared de frente. Pero en un pasillo estrecho una pared lejana
subtiende muy poco angulo -aqui +-10 grados, o sea unos 40 rayos de 600-, y el
sector fijo mezclaba las dos superficies. Peor: contestaba "si hay plano" en un
48 % de los barridos de un recorrido donde rf2o registro el 21 % del avance.

Lo que decide no es si existe una superficie perpendicular, sino CUANTA de la
que el sensor ve puede informar del avance. rf2o resuelve un ajuste sobre todos
los rayos a la vez: cuarenta rayos que llevan informacion longitudinal contra
quinientos sesenta que no llevan ninguna se pierden en el promedio.

Asi que la medida es, por rayo, la orientacion de la superficie sobre la que
cae. Un desplazamiento hacia delante cambia el rango de un rayo en proporcion a
la componente de la NORMAL de la superficie en la direccion de la marcha: una
pared perpendicular tiene normal alineada con el avance y su rango cambia; una
pared lateral tiene normal transversal y su rango no cambia por avanzar. La
normal se estima ajustando una recta a los puntos vecinos en cartesianas, sin
usar el movimiento para nada.

El indice es la fraccion de rayos validos cuya normal cae a menos de 45 grados
del eje de marcha. Es una cantidad continua, no un si/no, que es lo que hacia
falta.

VALIDACION, Y LA CONDICION DE USO QUE SALIO DE ELLA
---------------------------------------------------
Contrastado el 2026-09-09 sobre geometria sintetica exacta y sobre dos bags de
simulacion cuyo resultado ya se conocia por otra via, con la prediccion escrita
antes de correr (§6.3 del protocolo). Numeros completos en
'S22_mapeo_pasillo_fallido.md' §8.7.

La primera prediccion FALLO, y de ese fallo sale la unica condicion de uso que
tiene esta herramienta. Comparando bag contra bag sin mas, el pasillo malo dio
26,7 % y la caja buena 14,5 %: al reves de lo esperado. La causa no es un
defecto de la medida sino que los dos recorridos NO SE MOVIAN IGUAL. El bag del
pasillo es un piloto con giros, y durante un giro las paredes laterales quedan
oblicuas al eje del robot, con lo que su rango SI cambia al avanzar. El indice
subia porque de verdad habia informacion, no por error.

Restringiendo los dos bags a recta pura -misma condicion de movimiento- la
separacion aparece y coincide con la sintetica:

    entorno                 sintetico   bag real (recta pura)
    caja cerrada 7,70 m       12,5 %         13,8 %
    pasillo 46,9 m             5,2 %          6,8 %
    separacion                 2,4x           2,03x

CONDICION DE USO: el numero solo es comparable entre recorridos con movimiento
parecido. Para un bag de reconocimiento en linea recta -que es el caso de
campo- la mediana vale. Para un bag con giros, mirar el decil inferior, que es
donde estan los tramos sin informacion; el mapa se encoge en esos, no en el
promedio.

COMO SE LEE EL RESULTADO
------------------------
Es la fraccion de lo que el sensor ve que puede informar del avance. No
garantiza que el mapa salga bien, pero un valor bajo sostenido si garantiza que
saldra corto, y eso es lo que se necesita para decidir antes de gastar una
campana.

USO
    herramientas/medir_informacion_avance.py <bag> [topico_scan]

    <bag>          carpeta del bag, o un .mcap suelto
    topico_scan    por defecto '/scan'
"""
import math
import statistics
import sys

from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import LaserScan

VECINOS = 3                 # rayos a cada lado para ajustar la recta local
SALTO_MAX = 0.10            # m entre rayos contiguos; mas es un borde, no una
                            # superficie, y su normal no significaria nada
ALINEACION = math.radians(45)   # tolerancia de la normal respecto al avance
MARGEN_ALCANCE = 0.95       # por debajo de esto del range_max para que cuente


def fraccion_informativa(m):
    """(fraccion, n_con_normal, n_validos) del barrido, o None.

    'None' si no hay ni un solo rayo con normal estimable.
    """
    n = len(m.ranges)
    # 1. Validez rayo a rayo. Un rayo que vuelve al alcance maximo no toca
    #    nada: no aporta superficie, y por eso no entra ni en el numerador ni
    #    en el denominador. Es justo lo que pasa mirando el fondo de un
    #    pasillo largo.
    ok = [False] * n
    xs = [0.0] * n
    ys = [0.0] * n
    for i, r in enumerate(m.ranges):
        if not math.isfinite(r) or r <= m.range_min:
            continue
        if r >= m.range_max * MARGEN_ALCANCE:
            continue
        theta = m.angle_min + i * m.angle_increment
        ok[i] = True
        xs[i] = r * math.cos(theta)
        ys[i] = r * math.sin(theta)

    n_validos = sum(ok)
    n_normal = 0
    n_informa = 0
    for i in range(VECINOS, n - VECINOS):
        if not ok[i]:
            continue
        # 2. La ventana ha de caer entera sobre UNA superficie continua.
        ventana = range(i - VECINOS, i + VECINOS + 1)
        if not all(ok[j] for j in ventana):
            continue
        if any(abs(m.ranges[j + 1] - m.ranges[j]) > SALTO_MAX
               for j in range(i - VECINOS, i + VECINOS)):
            continue
        # 3. Recta por minimos cuadrados TOTALES sobre los puntos cartesianos.
        #    Totales y no ordinarios: una pared paralela al eje x tiene
        #    pendiente infinita en y(x) y un ajuste ordinario la perderia.
        k = 2 * VECINOS + 1
        mx = sum(xs[j] for j in ventana) / k
        my = sum(ys[j] for j in ventana) / k
        cxx = cyy = cxy = 0.0
        for j in ventana:
            dx, dy = xs[j] - mx, ys[j] - my
            cxx += dx * dx
            cyy += dy * dy
            cxy += dx * dy
        if cxx + cyy <= 1e-12:
            continue
        n_normal += 1
        # Direccion del eje mayor de la nube; la normal es su perpendicular.
        ang = 0.5 * math.atan2(2.0 * cxy, cxx - cyy)
        # normal = (-sin ang, cos ang), luego su componente sobre el eje de
        # marcha vale -sin(ang). El signo no importa: informa igual una pared
        # de delante que una de detras.
        if abs(math.sin(ang)) >= math.cos(ALINEACION):
            n_informa += 1

    if n_normal == 0:
        return None
    return (n_informa / n_normal, n_normal, n_validos)


def main():
    if len(sys.argv) < 2:
        print(__doc__.split('\nUSO\n')[-1].replace('\n    ', '\n'))
        return 2
    ruta = sys.argv[1]
    topico = sys.argv[2] if len(sys.argv) > 2 else '/scan'

    lector = SequentialReader()
    almacen = 'mcap' if ruta.endswith('.mcap') else 'sqlite3'
    lector.open(StorageOptions(uri=ruta, storage_id=almacen),
                ConverterOptions('', ''))

    total = 0
    fracciones = []
    normales = []
    validos = []
    cabecera = None
    while lector.has_next():
        top, datos, _ = lector.read_next()
        if top != topico:
            continue
        m = deserialize_message(datos, LaserScan)
        if cabecera is None:
            cabecera = (m.angle_min, m.angle_max, m.range_min, m.range_max,
                        len(m.ranges))
        total += 1
        r = fraccion_informativa(m)
        if r is None:
            continue
        fracciones.append(r[0])
        normales.append(r[1])
        validos.append(r[2])

    if total == 0:
        print(f"ERROR: '{ruta}' no trae '{topico}'", file=sys.stderr)
        return 1
    if not fracciones:
        print(f"ERROR: ningun barrido de '{ruta}' tiene normales estimables",
              file=sys.stderr)
        return 1

    am, aM, rm, rM, nn = cabecera
    print(f'bag: {ruta}')
    print(f'barrido: {nn} muestras, [{math.degrees(am):.1f}, '
          f'{math.degrees(aM):.1f}] grados, alcance [{rm}, {rM}] m')
    print(f'barridos analizados: {total} ({len(fracciones)} con normales)')
    print()
    print(f'rayos por barrido (mediana): {statistics.median(validos):.0f} '
          f'validos de {nn}, {statistics.median(normales):.0f} con normal '
          f'estimable')
    print()

    orden = sorted(fracciones)
    def pct(q):
        return 100.0 * orden[min(len(orden) - 1, int(q * len(orden)))]
    print('fraccion de rayos que informan del avance, por barrido')
    print(f'  mediana   {100.0 * statistics.median(fracciones):>6.1f} %')
    print(f'  media     {100.0 * statistics.fmean(fracciones):>6.1f} %')
    print(f'  p10 / p90 {pct(0.10):>6.1f} / {pct(0.90):.1f} %')

    med = 100.0 * statistics.median(fracciones)
    print()
    print(f'INFORMACION DE AVANCE: {med:.1f} % DE LOS RAYOS QUE VE EL SENSOR')
    print()
    print('Lectura: de todo lo que el LiDAR ve, esa es la parte cuya geometria')
    print('cambia al avanzar, y por tanto la unica que puede decirle a rf2o que')
    print('el robot se movio. Un valor bajo no predice que el mapa falle en un')
    print('sitio concreto: predice que saldra corto, que es lo que paso en el')
    print('pasillo de 46,9 m. Ver S22_mapeo_pasillo_fallido.md §8.')
    print()
    print('AVISO: solo es comparable entre recorridos que se muevan igual. Un')
    print('giro vuelve informativas las paredes laterales y sube el indice con')
    print('razon. Si el bag tiene giros, decidir por el p10, no por la mediana.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
