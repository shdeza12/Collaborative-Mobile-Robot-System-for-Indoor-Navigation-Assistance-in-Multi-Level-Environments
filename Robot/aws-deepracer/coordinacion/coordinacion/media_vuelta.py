"""Media vuelta del vehiculo por tiempos, protegida por el LiDAR y por el mapa.

POR QUE EXISTE
--------------
El DeepRacer tiene direccion de automovil (Ackermann): no gira sobre si mismo.
En la salida del piso 4, de 2,5 m de ancho, la media vuelta de Nav2 aborto dos
veces contra la pared (p4r_11 y p4r_11b, 2026-10-07): el planificador supone un
radio de 0,35 m que el vehiculo no alcanza, y replanifica cada segundo con una
maniobra distinta. Una media vuelta en dos tiempos fijos funciono (p4r_11c),
pero el radio de racey no es el mismo hacia cada lado (calibracion del servo
1,30 / 1,40 / 1,70 ms) y no se va a medir: desde la escalera del piso 4, el
lado debil lo habria llevado contra la pared oeste.

QUE HACE
--------
Alterna reversa y avance con la direccion a tope, girando siempre en el mismo
sentido, hasta acumular el giro pedido (180 grados por defecto). Cada tiempo se
corta cuando, en el sentido de la marcha, la huella del vehiculo se acercaria a
menos de un margen de un punto del LiDAR o de una celda ocupada del mapa. El
mapa importa por la escalera: su vano esta cerrado con una lamina en el mapa, y
un LiDAR plano no ve un borde que baja. Si hay espacio, sale en dos tiempos; si
no, en mas. No necesita conocer el radio: se corta por espacio y por angulo, y
el angulo lo mide el filtro con la IMU.

El primer tiempo, en reversa, va hacia el costado con mas espacio segun el
mapa: girando a la izquierda (antihorario) la reversa abre el vehiculo hacia su
derecha, y girando a la derecha, hacia su izquierda.

Se detiene y avisa si no hay espacio en ningun sentido, si dos tiempos seguidos
no avanzan, si pasa de MAX_TIEMPOS o de TOPE_TOTAL_S.

Este modulo no importa ROS: la logica se prueba sin simulador
(herramientas/prueba_media_vuelta.py). La conexion con los topicos esta en
ConexionMediaVuelta, al final, y la usan el agente y herramientas/media_vuelta.py.
"""

import math
import time

import numpy as np

#: Huella del vehiculo, la de Nav2 (nav2_params_jazzy.yaml): 0,28 x 0,19 m
#: centrada en base_link.
LARGO_MEDIO = 0.14
ANCHO_MEDIO = 0.095

#: |linear.x| y |angular.z| de cada tiempo. El puente da el escalon mas bajo de
#: acelerador a cualquier orden por debajo de 1,2 m/s, y con |v| = 0,4 un
#: |angular.z| de 1,5 se convierte en direccion a tope.
V = 0.4
W = 1.5

#: Recorrido por delante que se revisa en cada ciclo, y su paso. Cubre lo que
#: el vehiculo rueda al soltar (de 0,1 a 0,3 m segun la velocidad).
HORIZONTE_M = 0.40
PASO_M = 0.05

#: Distancia minima entre la huella y un obstaculo en ese recorrido.
MARGEN_LIDAR_M = 0.10
MARGEN_MAPA_M = 0.10

#: Radios con los que se predice el recorrido: el arco mas cerrado medido (0,5 m)
#: y la recta. El real de cada lado queda entre los dos.
RADIOS_PREDICCION = (0.5, math.inf)

#: Solo cuentan los obstaculos a menos de esto del centro del vehiculo.
ALCANCE_M = 1.5

GIRO_POR_DEFECTO = math.pi
TOLERANCIA_FINAL = math.radians(20.0)
AVANCE_MINIMO = math.radians(4.0)
MAX_TIEMPOS = 9
TOPE_TIEMPO_S = 8.0
TOPE_TOTAL_S = 90.0
PAUSA_S = 0.4
PERIODO_S = 0.05


def normalizar(a):
    return math.atan2(math.sin(a), math.cos(a))


def holgura(puntos):
    """Distancia minima de los puntos (N x 2, marco del vehiculo) a la huella.

    0 si alguno cae dentro. inf si no hay puntos.
    """
    if len(puntos) == 0:
        return math.inf
    dx = np.maximum(np.abs(puntos[:, 0]) - LARGO_MEDIO, 0.0)
    dy = np.maximum(np.abs(puntos[:, 1]) - ANCHO_MEDIO, 0.0)
    return float(np.min(np.hypot(dx, dy)))


def poses_predichas(marcha, giro, horizonte=HORIZONTE_M, paso=PASO_M,
                    radios=RADIOS_PREDICCION):
    """Poses (dx, dy, dyaw) por delante del vehiculo, en su marco actual.

    marcha: +1 adelante, -1 reversa. giro: +1 antihorario, -1 horario.
    """
    poses = []
    pasos = max(1, int(round(horizonte / paso)))
    for r in radios:
        for i in range(1, pasos + 1):
            s = i * paso * marcha                 # recorrido con signo
            if math.isinf(r):
                poses.append((s, 0.0, 0.0))
            else:
                # El rumbo cambia en el sentido del giro tanto adelante como
                # atras (en reversa el mismo giro pide la direccion contraria),
                # y el desplazamiento lateral cambia de lado con la marcha: la
                # reversa con giro antihorario abre hacia la derecha (y < 0).
                th = giro * abs(s) / r
                poses.append((marcha * r * math.sin(abs(th)),
                              giro * marcha * r * (1.0 - math.cos(th)), th))
    return poses


def a_marco(puntos, x, y, yaw):
    """Puntos (N x 2) de un marco al de una pose (x, y, yaw) dada en ese marco."""
    if len(puntos) == 0:
        return puntos
    c, s = math.cos(yaw), math.sin(yaw)
    d = puntos - np.array([x, y])
    return np.column_stack((c * d[:, 0] + s * d[:, 1], -s * d[:, 0] + c * d[:, 1]))


def cercanos(puntos, alcance=ALCANCE_M):
    if len(puntos) == 0:
        return puntos
    return puntos[np.hypot(puntos[:, 0], puntos[:, 1]) <= alcance]


def holgura_por_delante(puntos, marcha, giro):
    """La menor holgura de la huella en el recorrido que viene (puntos en el marco del vehiculo)."""
    puntos = cercanos(puntos)
    if len(puntos) == 0:
        return math.inf
    return min(holgura(a_marco(puntos, x, y, th))
               for x, y, th in poses_predichas(marcha, giro))


def elegir_giro(puntos_mapa):
    """+1 (antihorario) o -1 (horario), segun el costado con mas espacio.

    La reversa con giro antihorario abre el vehiculo hacia su derecha (y < 0);
    con giro horario, hacia su izquierda. Se mira la franja de 1,2 m a lo largo.
    """
    p = cercanos(puntos_mapa, 3.0)
    franja = p[np.abs(p[:, 0]) <= 0.6] if len(p) else p
    izq = franja[franja[:, 1] > 0, 1] if len(franja) else franja
    der = -franja[franja[:, 1] < 0, 1] if len(franja) else franja
    libre_izq = float(np.min(izq)) if len(izq) else math.inf
    libre_der = float(np.min(der)) if len(der) else math.inf
    return (1 if libre_der > libre_izq else -1), libre_izq, libre_der


class Maniobra:
    """Decide que mandar en cada ciclo. Sin ROS y sin reloj propio: se le pasa t.

    paso() devuelve (v, w, estado): estado es 'en_curso', 'terminada' o
    'abortada: <motivo>'.
    """

    def __init__(self, giro, objetivo=GIRO_POR_DEFECTO):
        self.giro = giro
        self.objetivo = objetivo
        self.marcha = -1                 # el primer tiempo es en reversa
        self.tiempos = 0
        self.sin_avance = 0
        self.t_tiempo = None
        self.t_inicio = None
        self.pausa_hasta = None
        self.giro_al_empezar_tiempo = 0.0
        self.motivo_fin_tiempo = ''
        self.registro = []               # (marcha, grados, motivo) de cada tiempo

    def _cerrar_tiempo(self, t, girado, motivo):
        avance = abs(girado - self.giro_al_empezar_tiempo)
        self.registro.append((self.marcha, math.degrees(avance), motivo))
        self.sin_avance = self.sin_avance + 1 if avance < AVANCE_MINIMO else 0
        self.marcha = -self.marcha
        self.t_tiempo = None
        self.pausa_hasta = t + PAUSA_S

    def paso(self, t, girado, bloqueado):
        """t: segundos. girado: giro acumulado en el sentido pedido (rad).

        bloqueado: None si el recorrido que viene esta libre, o el motivo.
        """
        if self.t_inicio is None:
            self.t_inicio = t
        if girado >= self.objetivo - TOLERANCIA_FINAL:
            if self.t_tiempo is not None:
                self.registro.append((self.marcha, math.degrees(
                    abs(girado - self.giro_al_empezar_tiempo)), 'completa el giro'))
                self.t_tiempo = None
            return 0.0, 0.0, 'terminada'
        if t - self.t_inicio > TOPE_TOTAL_S:
            return 0.0, 0.0, f'abortada: mas de {TOPE_TOTAL_S:.0f} s sin completar el giro'
        if self.pausa_hasta is not None:
            if t < self.pausa_hasta:
                return 0.0, 0.0, 'en_curso'
            self.pausa_hasta = None
        if self.sin_avance >= 2:
            return 0.0, 0.0, 'abortada: dos tiempos seguidos sin avanzar el giro'
        if self.t_tiempo is None:
            # Empieza un tiempo nuevo. Si ni siquiera puede arrancar, se prueba
            # el otro sentido; si ese tampoco pudo, no hay salida.
            if bloqueado is not None:
                otro_tampoco = bool(self.registro) and self.registro[-1][2].startswith('sin espacio')
                self.registro.append((self.marcha, 0.0, f'sin espacio al empezar: {bloqueado}'))
                if otro_tampoco:
                    return 0.0, 0.0, f'abortada: sin espacio en ningun sentido ({bloqueado})'
                self.marcha = -self.marcha
                return 0.0, 0.0, 'en_curso'
            if self.tiempos >= MAX_TIEMPOS:
                return 0.0, 0.0, f'abortada: {MAX_TIEMPOS} tiempos sin completar el giro'
            self.tiempos += 1
            self.t_tiempo = t
            self.giro_al_empezar_tiempo = girado
        else:
            if bloqueado is not None:
                self._cerrar_tiempo(t, girado, f'corta: {bloqueado}')
                return 0.0, 0.0, 'en_curso'
            if t - self.t_tiempo > TOPE_TIEMPO_S:
                self._cerrar_tiempo(t, girado, 'corta: tope de tiempo')
                return 0.0, 0.0, 'en_curso'
        return self.marcha * V, self.giro * W, 'en_curso'


def ejecutar(leer_yaw, leer_obstaculos, mandar, giro=None, objetivo=GIRO_POR_DEFECTO,
             reloj=time.monotonic, dormir=time.sleep, log=print):
    """Ejecuta la media vuelta. Devuelve (ok, mensaje).

    leer_yaw() -> rumbo actual (rad) o None. leer_obstaculos() -> (lidar, mapa),
    dos arrays N x 2 en el marco del vehiculo (el mapa puede venir vacio si no
    hay mapa: entonces solo protege el LiDAR, y se avisa). mandar(v, w) publica.
    giro: +1, -1 o None para elegirlo con el mapa (o el LiDAR si no hay mapa).
    """
    lidar, mapa = leer_obstaculos()
    if lidar is None:
        return False, 'sin LiDAR: no se mueve'
    if mapa is None or len(mapa) == 0:
        log('AVISO: sin mapa; la escalera solo esta protegida por el mapa, asi que '
            'solo se protege de lo que ve el LiDAR')
        mapa = np.zeros((0, 2))
    if giro is None:
        giro, izq, der = elegir_giro(mapa if len(mapa) else lidar)
        log(f'espacio libre: {izq:.2f} m a la izquierda, {der:.2f} m a la derecha; '
            f'giro {"antihorario" if giro > 0 else "horario"}: la reversa abre hacia la '
            f'{"derecha" if giro > 0 else "izquierda"}')
    yaw0 = leer_yaw()
    if yaw0 is None:
        return False, 'sin odometria: no se mueve'
    m = Maniobra(giro, objetivo)
    acumulado, previo = 0.0, yaw0
    try:
        while True:
            yaw = leer_yaw()
            if yaw is not None:
                acumulado += normalizar(yaw - previo)
                previo = yaw
            lidar, mapa = leer_obstaculos()
            bloqueado = None
            marcha = m.marcha
            if lidar is None:
                bloqueado = 'LiDAR sin datos'
            else:
                h = holgura_por_delante(lidar, marcha, giro)
                if h < MARGEN_LIDAR_M:
                    bloqueado = f'LiDAR a {h:.2f} m'
                elif mapa is not None and len(mapa):
                    hm = holgura_por_delante(mapa, marcha, giro)
                    if hm < MARGEN_MAPA_M:
                        bloqueado = f'mapa a {hm:.2f} m'
            v, w, estado = m.paso(reloj(), giro * acumulado, bloqueado)
            mandar(v, w)
            if estado != 'en_curso':
                break
            dormir(PERIODO_S)
    finally:
        for _ in range(3):
            mandar(0.0, 0.0)
    resumen = '; '.join(f'{"reversa" if mr < 0 else "avance"} {g:.0f} grados ({mo})'
                        for mr, g, mo in m.registro)
    girado = math.degrees(giro * acumulado)
    if estado == 'terminada':
        tiempos = f'{m.tiempos} tiempo' + ('' if m.tiempos == 1 else 's')
        return True, f'media vuelta: {girado:.0f} grados en {tiempos}. {resumen}'
    return False, f'{estado}. Girado {girado:.0f} grados. {resumen}'


class ConexionMediaVuelta:
    """Los topicos que necesita la media vuelta, en un nodo ya creado.

    Lo usan el agente (servicio media_vuelta) y herramientas/media_vuelta.py.
    Las suscripciones van en el grupo que se pase: el agente las pone aparte del
    servicio, que bloquea mientras dura la maniobra.
    """

    def __init__(self, nodo, buffer_tf, marco_mapa, marco_base, topico_scan='scan',
                 topico_odom='odom', topico_mapa='map', topico_cmd='cmd_vel', grupo=None):
        from geometry_msgs.msg import Twist
        from nav_msgs.msg import OccupancyGrid, Odometry
        from rclpy.qos import (QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy,
                               qos_profile_sensor_data)
        from sensor_msgs.msg import LaserScan
        self.nodo, self.tf = nodo, buffer_tf
        self.marco_mapa, self.marco_base = marco_mapa, marco_base
        self.Twist = Twist
        self.yaw = None
        self.scan = None
        self.celdas = None              # celdas ocupadas del mapa, en el marco del mapa
        self.pub = nodo.create_publisher(Twist, topico_cmd, 10)
        nodo.create_subscription(Odometry, topico_odom, self._odom, 20, callback_group=grupo)
        nodo.create_subscription(LaserScan, topico_scan, self._scan,
                                 qos_profile_sensor_data, callback_group=grupo)
        nodo.create_subscription(
            OccupancyGrid, topico_mapa, self._mapa,
            QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                       reliability=QoSReliabilityPolicy.RELIABLE), callback_group=grupo)

    def _odom(self, m):
        q = m.pose.pose.orientation
        self.yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))

    def _scan(self, m):
        self.scan = m

    def _mapa(self, m):
        # Ocupado: 65 o mas, o desconocido (-1). La escalera es una lamina
        # ocupada; lo desconocido queda detras de las paredes.
        datos = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
        filas, cols = np.nonzero((datos >= 65) | (datos < 0))
        r = m.info.resolution
        o = m.info.origin.position
        q = m.info.origin.orientation
        th = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        xs, ys = (cols + 0.5) * r, (filas + 0.5) * r
        c, s = math.cos(th), math.sin(th)
        self.celdas = np.column_stack((o.x + c * xs - s * ys, o.y + s * xs + c * ys))
        self.nodo.get_logger().info(f'media vuelta: mapa con {len(self.celdas)} celdas ocupadas')

    def _transformada(self, destino, origen):
        import rclpy.time
        t = self.tf.lookup_transform(destino, origen, rclpy.time.Time())
        q = t.transform.rotation
        return (t.transform.translation.x, t.transform.translation.y,
                math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z)))

    def obstaculos(self):
        """(lidar, mapa) en el marco del vehiculo; None donde no hay dato."""
        lidar = mapa = None
        m = self.scan
        if m is not None:
            try:
                x, y, th = self._transformada(self.marco_base, m.header.frame_id)
                r = np.array(m.ranges, dtype=float)
                a = m.angle_min + np.arange(len(r)) * m.angle_increment
                ok = np.isfinite(r) & (r >= max(m.range_min, 0.05)) & (r <= m.range_max)
                px, py = r[ok] * np.cos(a[ok]), r[ok] * np.sin(a[ok])
                c, s = math.cos(th), math.sin(th)
                lidar = np.column_stack((x + c * px - s * py, y + s * px + c * py))
            except Exception as e:  # TF todavia no disponible
                self.nodo.get_logger().warn(f'media vuelta: sin TF del LiDAR ({e})')
        if self.celdas is not None:
            try:
                x, y, th = self._transformada(self.marco_mapa, self.marco_base)
                cerca = self.celdas[np.hypot(self.celdas[:, 0] - x, self.celdas[:, 1] - y) <= ALCANCE_M + 0.5]
                mapa = a_marco(cerca, x, y, th)
            except Exception as e:
                self.nodo.get_logger().warn(f'media vuelta: sin TF del mapa ({e})')
        return lidar, mapa

    def mandar(self, v, w):
        t = self.Twist()
        t.linear.x, t.angular.z = float(v), float(w)
        self.pub.publish(t)

    def ejecutar(self, giro=None, objetivo=GIRO_POR_DEFECTO):
        log = self.nodo.get_logger().info
        return ejecutar(lambda: self.yaw, self.obstaculos, self.mandar, giro=giro,
                        objetivo=objetivo, log=log)
