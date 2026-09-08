#!/usr/bin/env python3
"""Correlaciona la perdida de avance de rf2o con lo que el sensor ve delante.

POR QUE EXISTE
--------------
'medir_registro_odometria.py' deja establecido QUE rf2o pierde el avance y no
el giro. No dice POR QUE, y sin el porque no se sabe si volver al pasillo con
mejor conduccion arregla algo. Este guion contesta esa pregunta.

La hipotesis que comprueba es geometrica: rf2o estima el movimiento SOLO del
cambio entre barridos consecutivos. En un pasillo recto y uniforme cada rango
queda determinado por la posicion lateral y el rumbo, y NO por la longitudinal
-el robot avanza y el barrido siguiente es identico al anterior-. Si eso es
cierto, la razon longitudinal tiene que depender de si hay estructura
perpendicular al movimiento dentro del alcance del LiDAR, y no de la velocidad
ni de lo suave que sea la conduccion.

Lo que salio sobre 'S21_piloto_bajada_01', agrupando por alcance frontal medio:

    estructura a menos de 6 m   n=16   razon 0,998
    estructura entre 6 y 9 m    n=76   razon 0,255

Es un interruptor, no una deriva. En las ventanas ciegas el alcance frontal
esta clavado en 7,40 m mientras el robot avanza 1,00 m, y no es saturacion
porque el sensor simulado llega a 10,0 m: es la pared lateral vista por el
borde del sector, a distancia invariante.

LA CONSECUENCIA, QUE ES EL MOTIVO DE CONSERVAR ESTE GUION
---------------------------------------------------------
rf2o devuelve casi cero y ACIERTA: desde el punto de vista del sensor no ha
pasado nada. La informacion no esta en el dato, asi que no hay parametro que
lo arregle. Y al reves: la condicion para que la cadena funcione pasa a ser
MEDIBLE ANTES DE SALIR A CAMPO -hace falta estructura no uniforme dentro del
alcance del sensor a lo largo de todo el recorrido-, que es justamente lo que
este guion mide. Ese es su uso previsto de aqui en adelante: correrlo sobre un
bag de reconocimiento antes de comprometer una campana.

El ensayo de control esta en 'S22_mapeo_pasillo_fallido.md' §8.4: el mismo
movimiento y la misma velocidad en una caja cerrada de 7,70 m -donde las dos
paredes de los extremos se ven siempre- suben la razon de 0,209 a 1,010.

USO
    herramientas/medir_visibilidad_frontal.py <bag_verdad> <bag_rf2o>
                                              [topico_odom] [topico_scan]

    <bag_verdad>   bag de simulacion, con la odometria exacta y los barridos
    <bag_rf2o>     bag con el '/odom' que produjo rf2o (ver el guion hermano)
    topico_odom    por defecto '/robot2/odom'
    topico_scan    por defecto '/robot2/scan'
"""
import math
import sys

from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

VENTANA = 2.0     # s
SECTOR = 15       # muestras a cada lado del frente; +-15 al paso tipico
AVANCE_MIN = 0.20  # m; por debajo no hay avance que medir y la razon es ruido


def abrir(ruta):
    lector = SequentialReader()
    almacen = 'mcap' if ruta.endswith('.mcap') else 'sqlite3'
    lector.open(StorageOptions(uri=ruta, storage_id=almacen),
                ConverterOptions('', ''))
    return lector


def yaw_de(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y),
                      1 - 2 * (q.y * q.y + q.z * q.z))


def leer_odom(ruta, topico):
    lector = abrir(ruta)
    salida = []
    while lector.has_next():
        top, datos, _ = lector.read_next()
        if top != topico:
            continue
        m = deserialize_message(datos, Odometry)
        salida.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9,
                       m.pose.pose.position.x, m.pose.pose.position.y,
                       yaw_de(m.pose.pose.orientation)))
    return salida


def interp(serie, t):
    if t <= serie[0][0]:
        return serie[0]
    if t >= serie[-1][0]:
        return serie[-1]
    lo, hi = 0, len(serie) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if serie[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    t0, x0, y0, a0 = serie[lo]
    t1, x1, y1, a1 = serie[hi]
    f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    da = math.atan2(math.sin(a1 - a0), math.cos(a1 - a0))
    return (t, x0 + f * (x1 - x0), y0 + f * (y1 - y0), a0 + f * da)


def avance(a, b):
    """Componente longitudinal del desplazamiento, en el marco del robot."""
    dx, dy = b[1] - a[1], b[2] - a[2]
    return math.cos(a[3]) * dx + math.sin(a[3]) * dy


def main():
    if len(sys.argv) < 3:
        print(__doc__.split('USO')[1].replace('\n    ', '\n'))
        return 2
    ruta_verdad, ruta_rf2o = sys.argv[1], sys.argv[2]
    top_odom = sys.argv[3] if len(sys.argv) > 3 else '/robot2/odom'
    top_scan = sys.argv[4] if len(sys.argv) > 4 else '/robot2/scan'

    verdad = leer_odom(ruta_verdad, top_odom)
    rf2o = leer_odom(ruta_rf2o, '/odom')
    if not verdad or not rf2o:
        print('ERROR: falta odometria en alguno de los dos bags',
              file=sys.stderr)
        return 1

    barridos = []
    cabecera = None
    lector = abrir(ruta_verdad)
    while lector.has_next():
        top, datos, _ = lector.read_next()
        if top != top_scan:
            continue
        m = deserialize_message(datos, LaserScan)
        if cabecera is None:
            cabecera = (m.angle_min, m.angle_max, m.range_min, m.range_max,
                        len(m.ranges))
        n = len(m.ranges)
        finitos = [r for r in m.ranges if math.isfinite(r) and r > m.range_min]
        i0 = int(round((0.0 - m.angle_min) / m.angle_increment))
        frente = [m.ranges[i] for i in range(max(0, i0 - SECTOR),
                                             min(n, i0 + SECTOR + 1))
                  if math.isfinite(m.ranges[i]) and m.ranges[i] > m.range_min]
        barridos.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9,
                         max(frente) if frente else float('nan'),
                         max(finitos) if finitos else float('nan'),
                         len(finitos) / n))
    if not barridos:
        print(f"ERROR: '{ruta_verdad}' no trae '{top_scan}'", file=sys.stderr)
        return 1

    am, aM, rm, rM, nn = cabecera
    print(f'barrido: {nn} muestras, [{math.degrees(am):.1f}, '
          f'{math.degrees(aM):.1f}] grados, alcance [{rm}, {rM}] m')

    filas = []
    t_ini = max(rf2o[0][0], verdad[0][0])
    t_fin = min(rf2o[-1][0], verdad[-1][0])
    t = t_ini
    while t + VENTANA <= t_fin:
        dv = avance(interp(verdad, t), interp(verdad, t + VENTANA))
        dr = avance(interp(rf2o, t), interp(rf2o, t + VENTANA))
        vent = [s for s in barridos if t <= s[0] < t + VENTANA]
        if vent and abs(dv) > AVANCE_MIN:
            filas.append((t - t_ini, dr, dv, dr / dv,
                          sum(s[1] for s in vent) / len(vent),
                          sum(s[2] for s in vent) / len(vent),
                          sum(s[3] for s in vent) / len(vent),
                          interp(verdad, t)[1]))
        t += VENTANA

    if not filas:
        print('ERROR: ninguna ventana con avance suficiente', file=sys.stderr)
        return 1

    print()
    print(f'{"t(s)":>6}{"rf2o":>8}{"verdad":>8}{"razon":>8}'
          f'{"frente":>9}{"rmax":>8}{"%valido":>9}{"x_real":>9}')
    for f in filas:
        print(f'{f[0]:6.0f}{f[1]:8.2f}{f[2]:8.2f}{f[3]:8.3f}'
              f'{f[4]:9.2f}{f[5]:8.2f}{f[6] * 100:9.1f}{f[7]:9.2f}')

    # ESTA es la tabla que decide. Si la razon cae al alejarse la estructura
    # frontal, el fallo es de geometria y no del algoritmo.
    print()
    print('razon agrupada por alcance frontal medio:')
    for lo, hi in ((0, 3), (3, 6), (6, 9), (9, 12), (12, 100)):
        sel = [f for f in filas if lo <= f[4] < hi]
        if not sel:
            continue
        r = sum(abs(x[1]) for x in sel)
        v = sum(abs(x[2]) for x in sel)
        print(f'  frente [{lo:3d},{hi:3d}) m  n={len(sel):3d}  '
              f'razon={r / v if v > 1e-9 else 0:6.3f}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
