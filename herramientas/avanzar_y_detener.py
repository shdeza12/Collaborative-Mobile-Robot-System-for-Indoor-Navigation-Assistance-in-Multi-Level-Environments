#!/usr/bin/env python3
"""Avanza una distancia dada y se detiene, midiendo con la odometria de rf2o.

    avanzar_y_detener.py <metros> [m/s] [tope_segundos]

QUE MIDE Y CON QUE
------------------
El DeepRacer no tiene encoders: la unica fuente de desplazamiento es
'rf2o_laser_odometry', que lo deduce de los propios barridos. Este guion lee
'/odom' y para cuando la distancia recorrida alcanza la pedida. Es exactamente
la magnitud que exige G-2 del ACTA_GO_NOGO: 'odom -> base_link' publicando
desplazamiento con error menor o igual al 10 % sobre ruta conocida.

TRES PARADAS, NO UNA
--------------------
1. Por distancia: el criterio de exito.
2. Por tope de tiempo: si rf2o no acumula -pasillo liso, escaso avance- el
   guion no se queda mandando traccion para siempre.
3. Por laser: si aparece algo delante mas cerca del umbral, para en el acto.

Y en 'finally' se emiten cuarenta mensajes en cero pase lo que pase, porque
'servo_pkg' conserva el ultimo valor recibido: sin eso, morir el proceso deja
el carro andando.

LA CUNA CIEGA MIRA HACIA ADELANTE
---------------------------------
El LiDAR va montado girado pi ('hokuyo_joint', rpy="0 0 3.1416"), asi que un
rayo a angulo 'a' en el marco del sensor apunta a 'a + pi' en el marco del
vehiculo. El cono frontal se calcula con esa correccion. Si la cuna ciega de
60 grados deja el cono sin rayos, el guion lo dice al arrancar en vez de correr
sin proteccion y aparentar que la tiene.

EL UMBRAL DE 0,40 m/s
---------------------
'cmdvel_to_servo_node' traduce con |v|/4,0 y descarta por debajo de 0,1, asi
que toda velocidad menor de 0,40 m/s sale como throttle CERO y el carro no se
mueve. Medido el 2026-09-24. Por eso la velocidad por defecto es 0,50 m/s y el
guion avisa si se le pide menos.

POR QUE HAY UNA FASE DE REPOSO ANTES DE ARRANCAR
------------------------------------------------
En la primera pasada en seco del 2026-09-24, con velocidad CERO y el carro
inmovil, rf2o declaro 1,281 m en 1,53 s. Tomar el origen en el primer '/odom'
que llega deja la medida a merced de ese transitorio: el guion daria la
distancia por alcanzada sin que el vehiculo se hubiera movido.

Asi que antes de mandar nada se hacen dos cosas. Se descartan los primeros
segundos, y despues se observa quieto durante un rato midiendo cuanto se
mueve el origen. Esa cifra -la deriva en reposo- se imprime junto al
resultado, porque un recorrido de 3 m no significa lo mismo si el suelo de
ruido es 1 cm que si es 1 m.
"""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import (QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy)
from sensor_msgs.msg import LaserScan

VELOCIDAD_MINIMA_UTIL = 0.40   # por debajo, el throttle sale 0,0
CONO_FRONTAL_RAD = math.radians(20.0)
PARADA_LASER_M = 0.45
ASENTAMIENTO_S = 4.0           # se tira lo que rf2o diga al arrancar
REPOSO_S = 6.0                 # observacion quieto para medir la deriva


class AvanzarYDetener(Node):

    def __init__(self, distancia, velocidad, tope):
        super().__init__('avanzar_y_detener')
        self.distancia = distancia
        self.velocidad = velocidad
        self.tope = tope

        self.x = None          # ultima pose publicada por rf2o
        self.y = None
        self.x0 = None         # origen, fijado a mano tras el asentamiento
        self.y0 = None
        self.obstaculo = None
        self.rayos_en_cono = None

        mejor_esfuerzo = QoSProfile(reliability=QoSReliabilityPolicy.BEST_EFFORT,
                                    history=QoSHistoryPolicy.KEEP_LAST, depth=1)
        self.pub = self.create_publisher(Twist, '/cmd_vel', mejor_esfuerzo)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_subscription(LaserScan, '/rplidar_ros/scan',
                                 self.on_scan, mejor_esfuerzo)

    def on_odom(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

    def fijar_origen(self):
        self.x0, self.y0 = self.x, self.y

    @property
    def recorrido(self):
        if self.x0 is None or self.x is None:
            return 0.0
        return math.hypot(self.x - self.x0, self.y - self.y0)

    def girar(self, segundos):
        """Deja pasar el tiempo atendiendo callbacks, sin mandar nada."""
        fin = time.time() + segundos
        while time.time() < fin:
            rclpy.spin_once(self, timeout_sec=0.05)

    def on_scan(self, msg):
        # Marco del sensor -> marco del vehiculo: sumar pi y volver a (-pi, pi].
        cerca = None
        en_cono = 0
        for i, r in enumerate(msg.ranges):
            if r != r or not (msg.range_min <= r <= msg.range_max):
                continue
            a = msg.angle_min + i * msg.angle_increment + math.pi
            a = (a + math.pi) % (2.0 * math.pi) - math.pi
            if abs(a) > CONO_FRONTAL_RAD:
                continue
            en_cono += 1
            if cerca is None or r < cerca:
                cerca = r
        self.rayos_en_cono = en_cono
        self.obstaculo = cerca


def main():
    distancia = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    velocidad = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    tope = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0

    if velocidad < VELOCIDAD_MINIMA_UTIL:
        print('AVISO: %.2f m/s se traduce en throttle 0,0 y el carro NO se '
              'movera. Minimo util: %.2f m/s' % (velocidad, VELOCIDAD_MINIMA_UTIL))

    rclpy.init()
    nodo = AvanzarYDetener(distancia, velocidad, tope)

    # Esperar a que /cmd_vel tenga quien escuche Y a que rf2o publique /odom.
    # Sin lo primero los mensajes se pierden sin dar error -el emparejamiento
    # DDS tarda uno o dos segundos-; sin lo segundo no hay con que medir.
    limite = time.time() + 20.0
    while time.time() < limite:
        rclpy.spin_once(nodo, timeout_sec=0.1)
        if nodo.pub.get_subscription_count() > 0 and nodo.x is not None:
            break
    if nodo.pub.get_subscription_count() == 0:
        print('ERROR: nadie escucha /cmd_vel. Falta cmdvel_to_servo_node')
        return 1
    if nodo.x is None:
        print('ERROR: /odom no publica. Falta rf2o')
        return 1

    print('suscriptores en /cmd_vel: %d' % nodo.pub.get_subscription_count())
    if nodo.rayos_en_cono is not None:
        print('rayos en el cono frontal de %.0f grados: %d%s'
              % (math.degrees(CONO_FRONTAL_RAD) * 2, nodo.rayos_en_cono,
                 '   SIN PROTECCION POR LASER' if nodo.rayos_en_cono == 0 else ''))

    print('== asentando rf2o (%.0f s, sin mandar nada) ==' % ASENTAMIENTO_S)
    nodo.girar(ASENTAMIENTO_S)

    print('== reposo: midiendo la deriva (%.0f s, el carro NO se toca) ==' % REPOSO_S)
    nodo.fijar_origen()
    deriva = 0.0
    fin_reposo = time.time() + REPOSO_S
    while time.time() < fin_reposo:
        rclpy.spin_once(nodo, timeout_sec=0.05)
        deriva = max(deriva, nodo.recorrido)
    print('   deriva en reposo: %.3f m en %.0f s' % (deriva, REPOSO_S))
    if deriva >= distancia:
        print()
        print('ABORTA: la deriva en reposo (%.3f m) iguala o supera la distancia'
              % deriva)
        print('pedida (%.2f m). La medida no distinguiria avance de ruido.' % distancia)
        return 2

    # Comprobar el laser ANTES del bucle. Si no, el guion arranca, corta en la
    # primera iteracion sin publicar nada, y el informe sale con un tiempo de
    # marcha que en realidad es el de la parada: parece que avanzo y no lo
    # hizo. Paso el 2026-09-24 en el cuarto de 1,60 m.
    if nodo.obstaculo is not None and nodo.obstaculo < PARADA_LASER_M:
        print()
        print('NO ARRANCA: hay algo a %.2f m delante, por debajo del umbral de'
              % nodo.obstaculo)
        print('parada (%.2f m). Hacen falta al menos %.1f m de recta libre para'
              % (PARADA_LASER_M, distancia + 1.0))
        print('pedir %.2f m. El carro no ha recibido ninguna orden.' % distancia)
        return 3

    nodo.fijar_origen()
    print('== objetivo %.2f m a %.2f m/s, tope %.0f s ==' % (distancia, velocidad, tope))

    orden = Twist()
    arranque = time.time()
    marcha = 0.0            # solo la fase en que se manda traccion
    motivo = 'tope de tiempo'
    ordenes = 0
    try:
        while time.time() - arranque < tope:
            rclpy.spin_once(nodo, timeout_sec=0.02)
            if nodo.recorrido >= distancia:
                motivo = 'DISTANCIA ALCANZADA'
                break
            if nodo.obstaculo is not None and nodo.obstaculo < PARADA_LASER_M:
                motivo = 'obstaculo a %.2f m' % nodo.obstaculo
                break
            orden.linear.x = velocidad
            orden.angular.z = 0.0
            nodo.pub.publish(orden)
            ordenes += 1
            marcha = time.time() - arranque
    finally:
        orden.linear.x = 0.0
        orden.angular.z = 0.0
        for _ in range(40):
            nodo.pub.publish(orden)
            rclpy.spin_once(nodo, timeout_sec=0.0)
            time.sleep(0.025)

    # 'marcha' es el tiempo en que se mando traccion, no el total: el bloque de
    # parada tarda un segundo largo en emitir sus cuarenta ceros, y contarlo
    # inflaba el tiempo y hundia la velocidad media.
    # Dejar que rf2o acabe de integrar los ultimos barridos antes de leer.
    fin = time.time() + 2.0
    while time.time() < fin:
        rclpy.spin_once(nodo, timeout_sec=0.05)

    print()
    print('motivo de parada : %s' % motivo)
    print('deriva en reposo : %.3f m en %.0f s   <- suelo de ruido' % (deriva, REPOSO_S))
    print('recorrido rf2o   : %.3f m  (pedido %.2f m)' % (nodo.recorrido, distancia))
    print('tiempo de marcha : %.2f s   en %d ordenes de traccion' % (marcha, ordenes))
    if ordenes == 0:
        print()
        print('EL CARRO NO RECIBIO NINGUNA ORDEN DE MOVIMIENTO. Lo que se lee')
        print('arriba como recorrido es deriva de rf2o, no desplazamiento.')
    elif marcha > 0:
        print('velocidad media  : %.3f m/s  (mandada %.2f m/s)'
              % (nodo.recorrido / marcha, velocidad))
    print()
    print('MIDE CON FLEXOMETRO LO QUE DE VERDAD AVANZO. La cifra de rf2o es lo')
    print('que se pone a prueba, no la verdad de terreno.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
