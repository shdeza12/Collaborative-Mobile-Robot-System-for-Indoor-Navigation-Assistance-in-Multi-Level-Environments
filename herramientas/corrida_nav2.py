#!/usr/bin/env python3
"""Una corrida de una campana de navegacion: pose inicial, meta, espera, registro.

    corrida_nav2.py --avance D [--salida X Y YAW] [opciones]
    corrida_nav2.py --meta X Y YAW [--salida X Y YAW] [opciones]

Se corre en el VEHICULO y como root, con 'nav2_hardware.launch.py mapa:=...
nav:=true' ya activo. Tambien corre en la simulacion, con --ns y --marco.

QUE HACE, EN ORDEN
------------------
1. Si se da --salida, publica '/initialpose' ahi. HACE FALTA EN CADA CORRIDA
   MENOS LA PRIMERA: al devolver el carro a la marca de salida a mano, AMCL
   sigue creyendo que esta donde paro la corrida anterior.
2. Espera a que AMCL publique una pose con incertidumbre por debajo de
   --sigma-max. Si no converge, NO manda la meta: una localizacion mala se
   manifiesta como «Nav2 no planifica», que es indistinguible de otros cinco
   fallos.
3. Toma esa pose como salida real y fija la meta:
     --avance D     meta = D metros por delante en el eje x del mapa, con la
                    misma y que la salida... salvo que se de --y-meta. Es el
                    modo de la campana: el eje x del mapa es el del pasillo,
                    porque el vehiculo lo recorrio en recta al mapear.
     --meta X Y YAW meta absoluta en el marco del mapa.
4. Comprueba, si se da --mapa, que la meta cae en celda LIBRE. El 2026-09-24
   una meta a x = 8,0 cayo en lo desconocido y Nav2 aborto sin decir por que.
5. Manda la meta a NavigateToPose y espera, con tope de --tope segundos.
6. Con el vehiculo parado, fuerza a AMCL a actualizarse, lee AMCL y /odom y
   escribe una fila en --csv.

POR QUE SE FUERZA A AMCL AL LLEGAR
----------------------------------
AMCL solo corrige su pose cada 0,25 m o 0,2 rad de movimiento ('update_min_d',
'update_min_a'). Al parar, la ultima correccion puede ser de hasta 25 cm antes:
la pose que publica esta ATRASADA. En la primera prueba de esta herramienta, en
Gazebo el 2026-09-25, Nav2 dijo SUCCEEDED, AMCL daba 0,309 m de error de
llegada y /odom decia que el carro se habia quedado 0,10 m corto. Mismo patron
que los cuatro fallos de la campana OE4. Por eso, parado el vehiculo, se llama
varias veces a 'request_nomotion_update', que obliga a AMCL a corregir sin
moverse, y solo entonces se lee su pose.

Y por eso tambien se da el error segun /odom: G-3 pide verificar la llegada
contra /odom y no contra el SUCCEEDED de Nav2. En recta, el error longitudinal
segun /odom es avance_odom - avance_pedido.

LO QUE ESTA HERRAMIENTA NO SABE, Y POR ESO PIDE EL FLEXOMETRO
-------------------------------------------------------------
Las cifras de AMCL y de /odom son lo que se pone a prueba, no la verdad. G-2
pregunta cuanto se equivoca /odom contra un recorrido medido, y G-3 que la
llegada se verifique contra /odom y no contra el SUCCEEDED de Nav2. Por eso,
al terminar, imprime exactamente que hay que medir con cinta, y deja las
columnas vacias en el CSV para anotarlo.

POR QUE COMO ROOT
-----------------
'deepracer-core' corre como root, y Fast DDS no empareja por memoria
compartida entre usuarios distintos: como 'deepracer', este proceso veria el
servidor de acciones y no recibiria nada, sin dar error.

PARADA GARANTIZADA
------------------
Si el proceso se interrumpe o supera el tope, cancela la meta y publica ceros
en /cmd_vel. El puente al servo conserva el ultimo valor recibido: sin esto, el
carro seguiria con la ultima orden de Nav2.
"""
import argparse
import csv
import math
import os
import sys
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_srvs.srv import Empty

# Media longitud del vehiculo: la huella del YAML de Nav2 va de -0,140 a +0,140
# en x, centrada en base_link. La defensa delantera esta 0,14 m por delante del
# punto que Nav2 lleva a la meta.
DEFENSA_A_BASE = 0.14

ESTADOS = {
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
    GoalStatus.STATUS_CANCELED: 'CANCELED',
}

COLUMNAS = [
    'corrida', 'hora', 'estado', 'tiempo_s', 'recuperaciones',
    'salida_amcl_x', 'salida_amcl_y', 'salida_amcl_yaw', 'sigma_salida_m',
    'meta_x', 'meta_y', 'meta_yaw', 'avance_pedido_m',
    'llegada_amcl_x', 'llegada_amcl_y', 'error_llegada_amcl_m',
    'avance_amcl_m', 'avance_odom_m', 'error_long_odom_m',
    'cmdvel_n', 'cmdvel_bajo_040_n', 'linx_max', 'angz_min', 'angz_max',
    # Las tres ultimas las rellena la persona, con flexometro.
    'CINTA_avance_real_m', 'CINTA_error_longitudinal_m', 'CINTA_desvio_lateral_m',
]


def yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def cuaternio(yaw):
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def celda_libre(ruta_yaml, x, y):
    """True/False si la celda (x, y) del mapa es libre; None si no se puede saber."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, aqui)
    try:
        from zona_libre_mapa import leer_pgm, leer_yaml_mapa
    except ImportError:
        return None
    meta = leer_yaml_mapa(ruta_yaml)
    ancho, alto, filas = leer_pgm(meta['imagen'])
    res = meta['resolucion']
    col = int(math.floor((x - meta['origen'][0]) / res))
    fila = (alto - 1) - int(math.floor((y - meta['origen'][1]) / res))
    if not (0 <= col < ancho and 0 <= fila < alto):
        return False
    gris = filas[fila][col]
    if meta['negate']:
        gris = 255 - gris
    return gris >= 255.0 * (1.0 - meta['free_thresh'])


class Corrida(Node):

    def __init__(self, ns, marco):
        super().__init__('corrida_nav2')
        self.marco = marco
        pre = ns.rstrip('/')
        self.amcl = None
        self.sigma = None
        self.odom = None
        self.cmd = []
        self.recuperaciones = 0
        self.meta_en_curso = None      # meta en curso, para poder cancelarla

        # AMCL publica /amcl_pose con durabilidad TRANSIENT_LOCAL: sin pedirla
        # asi, un suscriptor que llega tarde no recibe la ultima pose.
        amcl_qos = QoSProfile(depth=1,
                              durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                              reliability=QoSReliabilityPolicy.RELIABLE)
        self.create_subscription(PoseWithCovarianceStamped, pre + '/amcl_pose',
                                 self.on_amcl, amcl_qos)
        self.create_subscription(Odometry, pre + '/odom', self.on_odom, 10)
        self.create_subscription(Twist, pre + '/cmd_vel', self.on_cmd, 10)
        self.pub_ini = self.create_publisher(PoseWithCovarianceStamped,
                                             pre + '/initialpose', 10)
        self.pub_cmd = self.create_publisher(Twist, pre + '/cmd_vel', 10)
        self.cliente = ActionClient(self, NavigateToPose, pre + '/navigate_to_pose')
        self.nomotion = self.create_client(Empty, pre + '/request_nomotion_update')

    def on_amcl(self, m):
        p = m.pose.pose
        self.amcl = (p.position.x, p.position.y, yaw_de(p.orientation))
        c = m.pose.covariance
        self.sigma = math.sqrt(max(c[0], 0.0) + max(c[7], 0.0))
        self.t_amcl = time.time()

    def on_odom(self, m):
        p = m.pose.pose.position
        self.odom = (p.x, p.y)

    def on_cmd(self, m):
        self.cmd.append((m.linear.x, m.angular.z))

    def girar(self, s):
        fin = time.time() + s
        while time.time() < fin:
            rclpy.spin_once(self, timeout_sec=0.05)

    def poner_salida(self, x, y, yaw):
        m = PoseWithCovarianceStamped()
        m.header.frame_id = self.marco
        m.pose.pose.position.x = x
        m.pose.pose.position.y = y
        (m.pose.pose.orientation.x, m.pose.pose.orientation.y,
         m.pose.pose.orientation.z, m.pose.pose.orientation.w) = cuaternio(yaw)
        # 0,10 m y 0,05 rad de desviacion: lo que se acierta poniendo el carro
        # a mano sobre una marca de cinta. Con 0,25 m, que fue la primera
        # version, la incertidumbre de partida ya superaba el umbral de
        # arranque y la corrida abortaba siempre sin haber empezado.
        m.pose.covariance[0] = 0.10 ** 2
        m.pose.covariance[7] = 0.10 ** 2
        m.pose.covariance[35] = 0.05 ** 2
        for _ in range(3):
            m.header.stamp = self.get_clock().now().to_msg()
            self.pub_ini.publish(m)
            self.girar(0.5)

    def refrescar_amcl(self, veces=5):
        """Obliga a AMCL a corregir su pose sin moverse. Devuelve si pudo."""
        if not self.nomotion.wait_for_service(timeout_sec=3.0):
            return False
        for _ in range(veces):
            f = self.nomotion.call_async(Empty.Request())
            fin = time.time() + 2.0
            while not f.done() and time.time() < fin:
                rclpy.spin_once(self, timeout_sec=0.05)
            # La correccion se aplica con el siguiente barrido: a 7 Hz en el
            # vehiculo, medio segundo cubre tres.
            self.girar(0.5)
        return True

    def parar(self):
        # Primero cancelar: mientras la meta siga viva, el controlador de Nav2
        # vuelve a publicar velocidad encima de los ceros de abajo.
        if self.meta_en_curso is not None:
            c = self.meta_en_curso.cancel_goal_async()
            fin = time.time() + 3.0
            while not c.done() and time.time() < fin:
                rclpy.spin_once(self, timeout_sec=0.1)
            self.meta_en_curso = None
        cero = Twist()
        for _ in range(40):
            self.pub_cmd.publish(cero)
            time.sleep(0.025)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--avance', type=float, metavar='D',
                   help='meta D metros por delante de la salida, en el eje x del mapa')
    g.add_argument('--meta', type=float, nargs=3, metavar=('X', 'Y', 'YAW'),
                   help='meta absoluta en el marco del mapa')
    ap.add_argument('--salida', type=float, nargs=3, metavar=('X', 'Y', 'YAW'),
                    help='publica /initialpose ahi antes de empezar')
    ap.add_argument('--y-meta', type=float, default=None,
                    help='con --avance: y de la meta (por defecto, la de la salida)')
    ap.add_argument('--mapa', help='YAML del mapa, para comprobar que la meta es libre')
    ap.add_argument('--csv', default='campana_nav2.csv',
                    help='fichero de la campana; se anade una fila por corrida')
    ap.add_argument('--corrida', default='', help='identificador de la corrida')
    ap.add_argument('--tope', type=float, default=120.0, help='segundos antes de cancelar')
    ap.add_argument('--sigma-max', type=float, default=0.20,
                    help='incertidumbre de AMCL maxima para arrancar, en m. Es un '
                         'control de cordura -que AMCL vive y no diverge-, NO '
                         'prueba de buena localizacion: eso lo dice RViz y la cinta')
    ap.add_argument('--ns', default='', help='espacio de nombres (simulacion: /robot1)')
    ap.add_argument('--marco', default='map', help='marco del mapa (simulacion: robot1/map)')
    # Los argumentos de ROS pasan intactos a rclpy. En la simulacion hace falta
    # '--ros-args -p use_sim_time:=true': las marcas de tiempo de la pose
    # inicial tienen que estar en el reloj de Gazebo, no en el de pared.
    a = ap.parse_args(rclpy.utilities.remove_ros_args(sys.argv)[1:])

    # La cabecera del CSV se comprueba ANTES de mover nada. Anadir filas con
    # otras columnas a un fichero existente las desalinea sin ningun aviso: las
    # cifras de cinta acabarian bajo el nombre equivocado. Paso en la prueba en
    # Gazebo del 2026-09-25 al cambiar la herramienta entre dos corridas.
    if os.path.exists(a.csv):
        with open(a.csv, newline='') as f:
            cabecera = next(csv.reader(f), [])
        if cabecera != COLUMNAS:
            print('ABORTA: %s tiene otras columnas que las de esta version.' % a.csv)
            print('        Usa otro --csv para esta campana. Nada se ha movido.')
            return 7

    rclpy.init(args=sys.argv)
    n = Corrida(a.ns, a.marco)
    try:
        return correr(n, a)
    except KeyboardInterrupt:
        print('\nINTERRUMPIDO: cancelando y parando el vehiculo')
        return 130
    finally:
        n.parar()
        n.destroy_node()
        rclpy.try_shutdown()


def correr(n, a):
    if a.salida:
        print('== pose inicial: x=%.2f y=%.2f yaw=%.2f ==' % tuple(a.salida))
        n.amcl = None
        n.poner_salida(*a.salida)

    print('== esperando a AMCL (sigma < %.2f m) y a /odom ==' % a.sigma_max)
    # Se espera a LAS DOS cosas en el mismo bucle. La primera version salia en
    # cuanto AMCL convergia y miraba /odom una sola vez: la pose de AMCL llega al
    # instante -es TRANSIENT_LOCAL- y el primer /odom todavia no, asi que
    # abortaba con «¿esta rf2o vivo?» con rf2o perfectamente vivo. Encontrado
    # probando en Gazebo el 2026-09-25.
    limite = time.time() + 30.0
    while time.time() < limite:
        n.girar(0.5)
        if (n.amcl is not None and n.sigma is not None and n.sigma < a.sigma_max
                and n.odom is not None):
            break
    if n.amcl is None:
        print('ABORTA: AMCL no publica %s/amcl_pose. ¿Esta el launch con mapa:=?' % a.ns)
        return 3
    if n.sigma >= a.sigma_max:
        print('ABORTA: AMCL no converge: sigma %.2f m, maximo %.2f.' % (n.sigma, a.sigma_max))
        print('        Revisa en RViz que el barrido encaje con el mapa, o pasa')
        print('        --salida con una pose mas cercana a la real.')
        return 4
    if n.odom is None:
        print('ABORTA: no llega %s/odom. ¿Esta rf2o vivo?' % a.ns)
        return 3

    sx, sy, syaw = n.amcl
    sigma0 = n.sigma
    odom0 = n.odom
    print('   salida AMCL: x=%.3f y=%.3f yaw=%.3f  (sigma %.3f m)' % (sx, sy, syaw, sigma0))

    if a.avance is not None:
        mx = sx + a.avance
        my = sy if a.y_meta is None else a.y_meta
        myaw = 0.0
    else:
        mx, my, myaw = a.meta
    pedido = math.hypot(mx - sx, my - sy)

    if a.mapa:
        libre = celda_libre(a.mapa, mx, my)
        if libre is False:
            print('ABORTA: la meta (%.2f, %.2f) no cae en celda libre del mapa.' % (mx, my))
            print('        Mide el tramo util con zona_libre_mapa.py y elige otra.')
            return 5
        if libre is None:
            print('   (no se pudo comprobar la meta contra el mapa)')

    if not n.cliente.wait_for_server(timeout_sec=15.0):
        print('ABORTA: no hay servidor %s/navigate_to_pose. ¿Nav2 activo?' % a.ns)
        return 3

    meta = NavigateToPose.Goal()
    meta.pose.header.frame_id = a.marco
    meta.pose.header.stamp = n.get_clock().now().to_msg()
    meta.pose.pose.position.x = mx
    meta.pose.pose.position.y = my
    (meta.pose.pose.orientation.x, meta.pose.pose.orientation.y,
     meta.pose.pose.orientation.z, meta.pose.pose.orientation.w) = cuaternio(myaw)

    def al_feedback(f):
        n.recuperaciones = max(n.recuperaciones, f.feedback.number_of_recoveries)

    print('== meta: x=%.3f y=%.3f yaw=%.2f  (avance pedido %.3f m, tope %.1f s) =='
          % (mx, my, myaw, pedido, a.tope))
    n.cmd = []
    t0 = time.time()
    fut = n.cliente.send_goal_async(meta, feedback_callback=al_feedback)
    while not fut.done():
        rclpy.spin_once(n, timeout_sec=0.1)
    handle = fut.result()
    if not handle.accepted:
        print('ABORTA: Nav2 rechazo la meta.')
        return 6
    n.meta_en_curso = handle

    res_fut = handle.get_result_async()
    estado = None
    while time.time() - t0 < a.tope:
        rclpy.spin_once(n, timeout_sec=0.1)
        if res_fut.done():
            estado = ESTADOS.get(res_fut.result().status, str(res_fut.result().status))
            break
    if estado is None:
        estado = 'TOPE'
        print('   tope de %.1f s: cancelando' % a.tope)
    else:
        n.meta_en_curso = None         # terminada: no hay nada que cancelar
    tiempo = time.time() - t0
    # Copia ANTES de parar: la herramienta escucha /cmd_vel y oiria sus propios
    # cuarenta ceros, que no son ordenes de Nav2.
    cmd = list(n.cmd)

    n.parar()
    print('== comprobando que el vehiculo esta quieto ==')
    n.girar(1.0)
    antes = n.odom
    n.girar(2.0)
    deriva = math.hypot(n.odom[0] - antes[0], n.odom[1] - antes[1])
    if deriva > 0.02:
        print('   AVISO: /odom se ha movido %.3f m en 2 s con la meta terminada.' % deriva)
        print('   El vehiculo NO esta quieto, o rf2o deriva. Detenlo a mano si')
        print('   rueda, y no te fies de las cifras de llegada de esta corrida.')
    else:
        print('   quieto: %.3f m en 2 s' % deriva)
    print('== forzando a AMCL a corregir su pose antes de leerla ==')
    if not n.refrescar_amcl():
        print('   AVISO: no hay %s/request_nomotion_update; la pose de AMCL puede'
              % a.ns)
        print('   estar atrasada hasta 0,25 m. Fiate de /odom y de la cinta.')
    lx, ly, _ = n.amcl
    err = math.hypot(lx - mx, ly - my)
    av_amcl = math.hypot(lx - sx, ly - sy)
    av_odom = math.hypot(n.odom[0] - odom0[0], n.odom[1] - odom0[1])
    err_odom = av_odom - pedido
    avan = [c for c in cmd if c[0] > 0.0]
    bajos = sum(1 for c in avan if c[0] < 0.40)
    linx = max((c[0] for c in cmd), default=0.0)
    angs = [c[1] for c in cmd] or [0.0]

    fila = {
        'corrida': a.corrida, 'hora': time.strftime('%H:%M:%S'), 'estado': estado,
        'tiempo_s': '%.1f' % tiempo, 'recuperaciones': n.recuperaciones,
        'salida_amcl_x': '%.3f' % sx, 'salida_amcl_y': '%.3f' % sy,
        'salida_amcl_yaw': '%.3f' % syaw, 'sigma_salida_m': '%.3f' % sigma0,
        'meta_x': '%.3f' % mx, 'meta_y': '%.3f' % my, 'meta_yaw': '%.3f' % myaw,
        'avance_pedido_m': '%.3f' % pedido,
        'llegada_amcl_x': '%.3f' % lx, 'llegada_amcl_y': '%.3f' % ly,
        'error_llegada_amcl_m': '%.3f' % err,
        'avance_amcl_m': '%.3f' % av_amcl, 'avance_odom_m': '%.3f' % av_odom,
        'error_long_odom_m': '%+.3f' % err_odom,
        'cmdvel_n': len(cmd), 'cmdvel_bajo_040_n': bajos,
        'linx_max': '%.3f' % linx, 'angz_min': '%.3f' % min(angs),
        'angz_max': '%.3f' % max(angs),
        'CINTA_avance_real_m': '', 'CINTA_error_longitudinal_m': '',
        'CINTA_desvio_lateral_m': '',
    }
    nuevo = not os.path.exists(a.csv)
    with open(a.csv, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)

    print()
    print('estado Nav2          : %s   (%.1f s, %d recuperaciones)'
          % (estado, tiempo, n.recuperaciones))
    print('avance pedido        : %.3f m' % pedido)
    print('avance segun AMCL    : %.3f m' % av_amcl)
    print('avance segun /odom   : %.3f m' % av_odom)
    print('error de llegada AMCL: %.3f m   (tolerancia de Nav2: 0,25)' % err)
    print('error longitudinal segun /odom: %+.3f m   (+ se paso, - se quedo corto)'
          % err_odom)
    print('/cmd_vel             : %d mensajes, %d de avance por debajo de 0,40, '
          'linear.x max %.2f, angular.z %.2f a %.2f'
          % (len(cmd), bajos, linx, min(angs), max(angs)))
    print('fila escrita en      : %s' % a.csv)
    print()
    print('AHORA, CON FLEXOMETRO Y SIN MOVER EL CARRO:')
    print('  1. avance real: de la linea de salida a la defensa delantera')
    print('  2. error longitudinal: de la defensa a la linea de meta')
    print('     (positivo si la paso, negativo si se quedo corto)')
    print('  3. desvio lateral: del centro del carro a la linea central')
    print('  Anotalo en las columnas CINTA_* de la fila de esta corrida.')
    print('  La defensa esta %.2f m por delante del punto que Nav2 lleva a la meta.'
          % DEFENSA_A_BASE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
