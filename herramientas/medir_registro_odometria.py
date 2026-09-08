#!/usr/bin/env python3
"""Mide cuanto del movimiento real registra rf2o, separado por componente.

POR QUE EXISTE
--------------
Hasta el 2026-09-08 el fallo de mapeo se media por su sintoma: el mapa sale
corto. Eso no distingue entre dos causas que piden arreglos opuestos:

  - un FACTOR DE ESCALA -reloj, unidades, un parametro de frecuencia- que
    encoge todo el movimiento por igual, y que se corrige con un numero;
  - una INOBSERVABILIDAD DIRECCIONAL, en la que el sensor no puede ver una
    componente del movimiento, y que no se corrige con ningun numero.

La medida que las separa es descomponer el desplazamiento EN EL MARCO DEL
ROBOT -longitudinal, lateral, rotacion- y comparar cada componente contra la
verdad de terreno. Un factor de escala afecta a las tres por igual. Una
inobservabilidad no: deja bien las que el sensor si ve.

Sobre 'S21_piloto_bajada_01' este guion dio longitudinal 0,388, lateral 1,143
y rotacion 1,055. O sea: el giro y el desplazamiento lateral se estiman bien y
solo se pierde el avance. Con eso cayeron a la vez todas las hipotesis de
escala, incluido el 'freq' de rf2o -que ademas vale 1,0 fijo en el fuente,
CLaserOdometry2D.cpp:153, y se cancela entre las lineas 507 y 898-.

Los cortes por franja de velocidad, por recta/giro y por bloques de 30 s estan
para distinguir una PERDIDA CONSTANTE de un INTERRUPTOR. Salio interruptor: la
razon por bloques salta entre 0,997 y 0,068 sin pasar por los valores del
medio. Esa forma es la que llevo a mirar que tenia el sensor delante en cada
bloque, que es lo que hace 'medir_visibilidad_frontal.py'.

COMO SE CONSIGUE LA VERDAD DE TERRENO
-------------------------------------
En simulacion, '/robotN/odom' lo publica el plugin desde 'model_->WorldPose()'
y es exacta al milimetro. En el carro fisico NO existe verdad de terreno: el
DeepRacer no lleva encoders, y por eso este guion solo se puede correr sobre
bags de simulacion. Para campo, la referencia es la recta medida con
flexometro, que es otra medida y otro guion.

COMO SE OBTIENE EL BAG DE rf2o
------------------------------
No sale del bag original: hay que reproducirlo con rf2o corriendo y grabar su
salida. En una terminal, con el bag de barridos reproduciendose como en
'mapear_desde_bag.sh', y en otra:

    ros2 bag record -o /tmp/odom_rf2o /odom

USO
    herramientas/medir_registro_odometria.py <bag_rf2o> <bag_verdad>
                                             [topico_rf2o] [topico_verdad]

    <bag_rf2o>      bag con el '/odom' que produjo rf2o
    <bag_verdad>    bag de simulacion con la odometria exacta del plugin
    topico_rf2o     por defecto '/odom'
    topico_verdad   por defecto '/robot2/odom'
"""
import math
import sys

from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry

VENTANA = 1.0   # s; agrega para que el ruido por pose no domine la razon


def leer_odom(ruta, topico):
    lector = SequentialReader()
    almacen = 'mcap' if ruta.endswith('.mcap') else 'sqlite3'
    lector.open(StorageOptions(uri=ruta, storage_id=almacen),
                ConverterOptions('', ''))
    salida = []
    while lector.has_next():
        top, datos, _ = lector.read_next()
        if top != topico:
            continue
        m = deserialize_message(datos, Odometry)
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        p = m.pose.pose.position
        q = m.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        salida.append((t, p.x, p.y, yaw))
    return salida


def interpolar(serie, t):
    """Pose de la verdad de terreno en el instante t."""
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


def local(a, b):
    """Desplazamiento de a hasta b expresado en el marco del robot en a."""
    dx, dy = b[1] - a[1], b[2] - a[2]
    c, s = math.cos(a[3]), math.sin(a[3])
    return (c * dx + s * dy, -s * dx + c * dy,
            math.atan2(math.sin(b[3] - a[3]), math.cos(b[3] - a[3])))


def main():
    if len(sys.argv) < 3:
        print(__doc__.split('USO')[1].replace('\n    ', '\n'))
        return 2
    ruta_rf2o, ruta_verdad = sys.argv[1], sys.argv[2]
    top_rf2o = sys.argv[3] if len(sys.argv) > 3 else '/odom'
    top_verdad = sys.argv[4] if len(sys.argv) > 4 else '/robot2/odom'

    rf2o = leer_odom(ruta_rf2o, top_rf2o)
    verdad = leer_odom(ruta_verdad, top_verdad)
    if not rf2o:
        print(f"ERROR: '{ruta_rf2o}' no trae '{top_rf2o}'", file=sys.stderr)
        return 1
    if not verdad:
        print(f"ERROR: '{ruta_verdad}' no trae '{top_verdad}'", file=sys.stderr)
        return 1

    print(f'rf2o: {len(rf2o)} poses  verdad: {len(verdad)} poses')
    print(f'rf2o   t=[{rf2o[0][0]:.2f}, {rf2o[-1][0]:.2f}]')
    print(f'verdad t=[{verdad[0][0]:.2f}, {verdad[-1][0]:.2f}]')

    filas = []
    t_ini = max(rf2o[0][0], verdad[0][0])
    t_fin = min(rf2o[-1][0], verdad[-1][0])
    t = t_ini
    ir = 0
    while t + VENTANA <= t_fin:
        while ir < len(rf2o) - 1 and rf2o[ir][0] < t:
            ir += 1
        a_r = rf2o[ir]
        jr = ir
        while jr < len(rf2o) - 1 and rf2o[jr][0] < t + VENTANA:
            jr += 1
        b_r = rf2o[jr]
        filas.append((t - t_ini, local(a_r, b_r),
                      local(interpolar(verdad, a_r[0]),
                            interpolar(verdad, b_r[0]))))
        t += VENTANA

    if not filas:
        print('ERROR: los dos bags no se solapan en el tiempo', file=sys.stderr)
        return 1

    # LA MEDIDA QUE DECIDE: escala afecta a las tres por igual, la
    # inobservabilidad solo a la componente que el sensor no ve.
    print()
    print(f'{"componente":<14}{"rf2o":>12}{"verdad":>12}{"razon":>10}')
    for nom, i in (('longitudinal', 0), ('lateral', 1), ('rotacion(rad)', 2)):
        r = sum(abs(f[1][i]) for f in filas)
        v = sum(abs(f[2][i]) for f in filas)
        razon = r / v if v > 1e-9 else float('nan')
        print(f'{nom:<14}{r:>12.3f}{v:>12.3f}{razon:>10.3f}')

    print()
    print('razon longitudinal por velocidad real de avance (m/s):')
    for lo, hi in ((0.0, 0.05), (0.05, 0.15), (0.15, 0.30), (0.30, 0.50),
                   (0.50, 5.0)):
        sel = [f for f in filas if lo <= abs(f[2][0]) < hi]
        if not sel:
            continue
        r = sum(abs(f[1][0]) for f in sel)
        v = sum(abs(f[2][0]) for f in sel)
        print(f'  [{lo:.2f}, {hi:.2f})  n={len(sel):4d}  rf2o={r:8.3f}  '
              f'verdad={v:8.3f}  razon={r / v if v > 1e-9 else 0:6.3f}')

    print()
    print('razon longitudinal segun rotacion en la ventana:')
    for etiqueta, cond in (('recta  |dyaw|<0.02', lambda f: abs(f[2][2]) < 0.02),
                           ('giro   |dyaw|>=0.02', lambda f: abs(f[2][2]) >= 0.02)):
        sel = [f for f in filas if cond(f)]
        if not sel:
            continue
        r = sum(abs(f[1][0]) for f in sel)
        v = sum(abs(f[2][0]) for f in sel)
        print(f'  {etiqueta}  n={len(sel):4d}  rf2o={r:8.3f}  verdad={v:8.3f}  '
              f'razon={r / v if v > 1e-9 else 0:6.3f}')

    # Si esta serie salta entre extremos en vez de variar poco a poco, la
    # perdida es un interruptor y hay que mirar que ve el sensor en cada
    # bloque: 'medir_visibilidad_frontal.py'.
    print()
    print('razon longitudinal por bloque de 30 s:')
    for k in range(0, int(t_fin - t_ini), 30):
        sel = [f for f in filas if k <= f[0] < k + 30]
        if not sel:
            continue
        r = sum(abs(f[1][0]) for f in sel)
        v = sum(abs(f[2][0]) for f in sel)
        print(f'  t=[{k:3d},{k + 30:3d})  rf2o={r:7.3f}  verdad={v:7.3f}  '
              f'razon={r / v if v > 1e-9 else 0:6.3f}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
