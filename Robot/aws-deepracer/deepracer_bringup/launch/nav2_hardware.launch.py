"""Levanta la cadena de navegacion sobre el vehiculo REAL, por peldanos.

Que es esto
-----------
El unico arranque de Nav2 pensado para hardware. Los demas launch del paquete
suponen Gazebo, o suponen que `deepracer_bringup` esta instalado; en la tarjeta
no se cumple ninguna de las dos cosas, asi que aqui todas las rutas son
argumentos y el archivo se puede copiar suelto a `~/tesis/`.

Se sube por peldanos, no de un golpe. Los argumentos `slam` y `nav` existen para
eso y siguen la escalera de Nav2:

    slam:=false nav:=false   ->  TF del vehiculo + odometria (peldanos 1-3)
    slam:=true  nav:=false   ->  + mapa en vivo             (peldanos 4-5)
    slam:=true  nav:=true    ->  + planificador y control   (peldanos 6-7)

Cada peldano se comprueba antes de subir al siguiente. Arrancarlo todo de una
vez y mirar si el carro se mueve es exactamente lo que este proyecto lleva
pagando desde S19: cuando falla, no se sabe cual de las siete capas fallo.

Lo que este launch NO arranca, a proposito
------------------------------------------
**El puente `cmdvel_to_servo_node`.** Tiene que correr como `root` —`servo_pkg`
es de `root` y Fast DDS no empareja entre usuarios distintos; como `deepracer`
el nodo arranca, suscribe, no da error y el carro no se mueve—. Meterlo aqui
obligaria a lanzar toda la cadena como `root`, y entonces los bags y los logs
quedarian con propietario equivocado. Va aparte, en su propia terminal:

    sudo -n bash -c 'source /opt/ros/jazzy/setup.bash &&
      source ~deepracer/coordinacion_ws/install/setup.bash &&
      ros2 run cmdvel_to_servo_pkg cmdvel_to_servo_node'

Y con el puente vivo hay que subir la escala **antes** de mandar nada, porque el
umbral de arranque medido de este carro esta justo en 0,50 y con el
`max_speed_pct` de fabrica (0,68) un `linear.x` de 0,50 sale a 0,4247:

    ros2 service call /set_max_speed \
      deepracer_interfaces_pkg/srv/NavThrottleSrv "{throttle: 0.9}"

**El driver del LiDAR.** Lo arranca `deepracer-core` al encender y publica en
`/rplidar_ros/scan`. No hay que pararlo ni disputarle `/dev/ttyUSB0`.

Los parametros: la variante de Jazzy, no la de Humble
-----------------------------------------------------
El vehiculo corre Jazzy, y `nav2_params.yaml` es la configuracion de Humble: en
Jazzy no arranca —el planificador y los comportamientos se declaran con «::» y no
con «/», y la lista `plugin_lib_names` repite nodos que Jazzy ya carga, con lo que
el `bt_navigator` no configura—. Por eso el valor por defecto de `params` es
`nav2_params_jazzy.yaml`, derivado del de Humble con solo esos cambios de
distribucion y ningun otro. Que no diverjan en nada mas lo exige
`herramientas/prueba_nav2_params_jazzy.py`; la lista de cambios, con su fuente,
esta en la cabecera del propio archivo.

Los arboles de `behavior_trees/` se usan los mismos que en simulacion. En Jazzy
imprimen un aviso por no llevar `BTCPP_format="4"`: es esperado y no impide
cargarlos (BT.CPP 4.6.2 solo avisa).

Los ajustes de hardware
-----------------------
Lo que es propio del vehiculo, y no de la distribucion, no va en el YAML: se
reescribe aqui con `RewrittenYaml`, sobre el archivo de Jazzy:

1. `min_approach_linear_velocity` 0,05 -> 0,40
2. `regulated_linear_scaling_min_speed` 0,25 -> 0,40

   Las dos por la **banda muerta del acelerador**. `get_mapped_throttle` calcula
   `pct = |v| / MAX_SPEED` con `MAX_SPEED = 4.0` y su umbral mas bajo es 0,1, asi
   que hasta el 2026-09-29 todo `linear.x` por debajo de 0,40 m/s salia como
   throttle 0,0000 exacto y el carro se detenia sin que ningun log lo dijera.
   Desde ese dia el puente sube esa franja a su escalon mas bajo (el que da
   0,40), asi que estos dos valores ya no hacen falta para que el carro se
   mueva; se conservan porque describen lo que el vehiculo hace de verdad: por
   debajo de 0,40 no va mas despacio.

3. `topic` y `scan_topic` -> `/rplidar_ros/scan`

   El driver de fabrica no publica en `/scan`. Se cambia por parametro y no por
   remapeo para que quede una sola forma de decirlo, y porque la capa de
   obstaculos del costmap toma su topico de un parametro, no de un remapeo.

4. `controller_frequency` 20 -> 10

   La tarjeta de 2 nucleos no sostiene 20 Hz: el 2026-09-29, en `amss-jgm9`, el
   lazo corrio entre 1 y 6 Hz con `Control loop missed its desired rate`.

5. `bond_timeout` del gestor del ciclo de vida, 4 -> 60 s (20 s hasta el 2026-10-08)

   No esta en el YAML sino en los parametros del gestor, abajo. Con la tarjeta a
   carga 18, el latido de `controller_server` no llego en 4 s y el gestor
   desactivo todo Nav2 35 s despues de activarlo (2026-09-29).

6. `default_server_timeout` de `bt_navigator`, 20 ms -> 1000 ms

   Es el plazo para que el planificador o el controlador confirmen una peticion
   del arbol. Con la tarjeta cargada no llegaban a tiempo: la corrida c1d_02 del
   2026-09-29 aborto en 0,5 s, con cuatro recuperaciones, sin mover el carro.

7. rf2o arranca 8 s despues de `robot_state_publisher`

   rf2o lee `base_link -> laser` una sola vez, con el primer barrido. Si no esta
   todavia, toma el laser como si no estuviera girado y, montado a 180 grados,
   mide el movimiento al reves. Paso el 2026-09-29 en los dos carros. El retraso
   no basta: el 2026-09-30, con la tarjeta cargada, el primer barrido llego 30 s
   despues y la TF seguia sin estar. El arreglo de fondo es el parche
   `herramientas/parches/rf2o_esperar_tf_laser.patch`, que hace que rf2o descarte
   los barridos hasta tener la TF; el retraso se conserva como margen.

8. `xy_goal_tolerance` 0,25 -> 1,0 m

   Distancia a la que Nav2 da la meta por alcanzada. Con 0,25 el Ackermann
   llegaba cerca de la meta, no podia corregir en tan poco espacio y retrocedia
   buscando la meta (corrida p2r_01, 2026-09-30). El criterio de G-3 sigue siendo
   0,5 m (acta 6.1), medido con flexometro. Se cambia sin editar el archivo con
   `margen_llegada:=0.5`, para comparar con la IMU sin desnivelar los vehiculos.

9. rf2o solo escribe errores (`--log-level error`)

   rf2o escribe cuatro lineas INFO por barrido y, como su lazo va a 20 Hz y el
   LiDAR a unos 7, un WARN «Waiting for laser_scans» unas 13 veces por segundo.
   El 2026-10-09, en el laboratorio, eran 19 993 de las ultimas 20 000 lineas del
   registro de la cadena, y cada una pasa por el proceso de `ros2 launch`. No cambia ningun
   calculo: el arranque ya comprueba que rf2o publique.

10. `lookup_table_size` del planificador Smac, 20 -> 10 m

   Es la ventana de distancias Reeds-Shepp que el planificador calcula por
   adelantado al configurarse. Con 20 m (el valor por defecto) la configuracion
   tardo 81 s en racey (2026-10-09, laboratorio), de los 115 que tardaba Nav2 en
   quedar activo. Mas alla de la ventana la distancia se calcula al planificar,
   asi que las rutas largas del pasillo (hasta 18 m) siguen siendo posibles.
   Va aparte, como el 6, porque la clave no esta en el YAML.

`use_sim_time` pasa a falso en todo el arbol, que es lo que separa esta corrida
de una de Gazebo.

Espacio de nombres (bloque C de Documentos/PLAN_S25.md)
-------------------------------------------------------
El coordinador llama a `/robotN/navigate_to_pose`, lee `/robotN/odom` y manda las
metas en `robotN/map`. Con `namespace:=robot2`:

- todos los nodos cuelgan de `/robot2`, y el YAML se anida con `root_key`, como
  en `deepracer_navigation_sim.launch.py`;
- los marcos propios llevan prefijo (`robot2/map`, `robot2/odom`,
  `robot2/base_link` y los de la URDF, por `frame_prefix`), y Nav2 los lee de
  las nueve claves de `marcos_prefijados`;
- rf2o publica `/robot2/odom`;
- una TF estatica identidad `robot2/laser -> laser` enlaza el marco `laser`, que
  pone el driver de AWS en cada barrido y no se puede cambiar. `/tf` va en la
  particion de cada carro, asi que ese `laser` sin prefijo no choca con el del
  otro;
- `/tf` no se remapea: como en la simulacion, lo que separa los arboles es el
  prefijo.

`map_server`, `amcl` y el puente los arranca `herramientas/nav2_mapa_guardado.sh`
con `NS=robot2`. Sin `namespace` (el valor por defecto) el lanzamiento es el mismo
de antes: ni un parametro, nodo o reescritura de mas. Lo comprueba
`herramientas/prueba_nav2_hardware_ns.py`.

Con la IMU de la tarjeta (imu:=true, Documentos/PLAN_S26.md §2.3)
-----------------------------------------------------------------
La tarjeta lleva una IMU Bosch BMI160, probada en los dos vehiculos el
2026-10-05 (Documentos/Evidencia/S26_pruebas_imu.md). Con `imu:=true`:

- `imu_bmi160.py` (`imu_nodo`) publica `imu/data` en `imu_link`, con el sesgo del
  giroscopio medido al arrancar. El vehiculo tiene que estar quieto los
  primeros segundos;
- rf2o publica en `odom_rf2o` y deja de publicar la TF `odom -> base_link`;
- un EKF de `robot_localization` toma de rf2o el avance y de la IMU el rumbo,
  publica `odom` y la TF `odom -> base_link`. Que toma de cada uno, y por que,
  esta en `parametros_ekf`.

El resto del arbol no cambia: AMCL, Nav2 y el coordinador siguen leyendo `odom`.
Con `imu:=false`, el valor por defecto, el lanzamiento es el de antes. Lo
comprueba `herramientas/prueba_nav2_hardware_ns.py`, y el filtro con datos
sinteticos `herramientas/prueba_ekf_imu.py`.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


# Inicio del escalon mas bajo del puente. Hasta el 2026-09-29, por debajo de esto
# 'get_mapped_throttle' devolvia 0,0000 exacto; desde entonces devuelve ese mismo
# escalon, asi que pedir menos no hace ir mas despacio.
VELOCIDAD_MINIMA_UTIL = '0.40'
# Frecuencia del controlador que la tarjeta de 2 nucleos si sostiene (ajuste 4).
FRECUENCIA_CONTROL = '10.0'
# Espera antes de arrancar rf2o, para que robot_state_publisher ya publique
# base_link -> laser (ajuste 7).
RETARDO_RF2O_S = 8.0
# Distancia a la que Nav2 da la meta por alcanzada en el vehiculo (ajuste 8).
MARGEN_LLEGADA_NAV2_M = '1.0'
# Plazo para que un servidor de Nav2 confirme una peticion del arbol (ajuste 6).
PLAZO_SERVIDOR_MS = 1000
# Ventana que el planificador Smac calcula por adelantado al configurarse (ajuste 10).
TABLA_PLANIFICADOR_M = 10.0

TOPICO_SCAN = '/rplidar_ros/scan'

# Con imu:=true (ver la cabecera). El EKF corre a 15 Hz: rf2o publica al ritmo
# del laser, unos 7,5 Hz, la IMU a 25 y el controlador de Nav2 va a 10. A 20 Hz,
# el 2026-10-05 en amss-jgm9, el filtro no llegaba a tiempo cada vez que otro
# proceso arrancaba ('Failed to meet update rate', hasta 0,30 s por ciclo).
TOPICO_ODOM_RF2O = 'odom_rf2o'
FRECUENCIA_EKF = 15.0
NODO_IMU = 'imu_bmi160.py'

# Parametros de Nav2 para Jazzy. El de Humble ('nav2_params.yaml') no arranca en
# el vehiculo; ver la cabecera de este modulo.
PARAMS_JAZZY = 'nav2_params_jazzy.yaml'


def _ruta_en_paquete(paquete, *partes):
    """Ruta dentro de un paquete instalado, o cadena vacia si no lo esta.

    En la tarjeta no hay `deepracer_bringup` ni `deepracer_description`, y
    `get_package_share_directory` lanza excepcion. Si esa excepcion subiera, el
    launch no se podria ni construir aunque el usuario pasara la ruta a mano,
    porque los valores por defecto se evaluan siempre. Se atrapa y se deja
    vacio; el fallo se reporta luego, con un mensaje que se entiende.
    """
    try:
        return os.path.join(get_package_share_directory(paquete), *partes)
    except Exception:
        return ''


def _junto_al_lanzador(nombre):
    """Ruta de un archivo que viaja con el lanzador, o cadena vacia.

    En la tarjeta los dos van sueltos en ~/tesis; en el repositorio el archivo
    esta en `scripts/`, al lado de `launch/`.
    """
    aqui = os.path.dirname(os.path.realpath(__file__))
    for ruta in (os.path.join(aqui, nombre), os.path.join(aqui, '..', 'scripts', nombre)):
        if os.path.isfile(ruta):
            return os.path.normpath(ruta)
    return ''


def _exigir(ruta, que, argumento):
    if not ruta:
        raise RuntimeError(
            'No encuentro %s y no se indico ruta. Pase %s:=/ruta/al/archivo'
            % (que, argumento))
    if not os.path.isfile(ruta):
        raise RuntimeError('%s no existe: %s' % (que, ruta))
    return ruta


def marcos_prefijados(prefijo):
    """Claves del YAML de Nav2 cuyo valor es un marco del robot, ya prefijadas.

    Rutas completas y no la clave suelta: `global_frame` vale `map` en el costmap
    global y `odom` en el local, y reescribirla por clave hoja igualaria los dos
    (la misma razon que en deepracer_navigation_sim.launch.py). Sin prefijo no se
    reescribe nada. Las de `amcl` y `map_server` no van aqui: esos nodos los
    arranca nav2_mapa_guardado.sh, no este lanzador.
    """
    if not prefijo:
        return {}
    base, odom, mapa = (f'{prefijo}base_link', f'{prefijo}odom', f'{prefijo}map')
    return {
        'bt_navigator.ros__parameters.global_frame': mapa,
        'bt_navigator.ros__parameters.robot_base_frame': base,
        'local_costmap.local_costmap.ros__parameters.global_frame': odom,
        'local_costmap.local_costmap.ros__parameters.robot_base_frame': base,
        'global_costmap.global_costmap.ros__parameters.global_frame': mapa,
        'global_costmap.global_costmap.ros__parameters.robot_base_frame': base,
        # Jazzy separa el marco local y el global (diferencia 6 del YAML).
        'behavior_server.ros__parameters.local_frame': odom,
        'behavior_server.ros__parameters.global_frame': mapa,
        'behavior_server.ros__parameters.robot_base_frame': base,
    }


def marcos_slam(prefijo):
    """Los tres marcos de slam_toolbox, prefijados; vacio sin prefijo."""
    if not prefijo:
        return {}
    return {
        'slam_toolbox.ros__parameters.odom_frame': f'{prefijo}odom',
        'slam_toolbox.ros__parameters.map_frame': f'{prefijo}map',
        'slam_toolbox.ros__parameters.base_frame': f'{prefijo}base_link',
    }


def parametros_ekf(prefijo, ns):
    """Parametros del EKF de `robot_localization` para imu:=true.

    Toma de cada fuente solo lo que esa fuente mide bien:

    - de rf2o, x e y como diferencias (`odom0_differential`). El filtro convierte
      cada diferencia en una velocidad en `base_link` y la integra con su propio
      rumbo. El rumbo de rf2o no se toma: rf2o publica covarianza cero, y el
      filtro lo tomaria como exacto y la IMU no pesaria nada;
    - de la IMU, solo la velocidad de giro en z (posicion 11 de `imu0_config`).
      La aceleracion no se usa: integrada da posicion con un error que crece con
      el cuadrado del tiempo.

    No se toma la velocidad que publica rf2o: sale con el signo cambiado.
    """
    def topico(nombre):
        return f'/{ns}/{nombre}' if ns else f'/{nombre}'

    odom0 = [False] * 15
    odom0[0] = odom0[1] = True
    imu0 = [False] * 15
    imu0[11] = True
    return {
        'use_sim_time': False,
        'frequency': FRECUENCIA_EKF,
        'two_d_mode': True,
        'publish_tf': True,
        # Los diagnosticos son un topico mas que nadie lee, en una tarjeta justa.
        'print_diagnostics': False,
        'map_frame': f'{prefijo}map',
        'odom_frame': f'{prefijo}odom',
        'base_link_frame': f'{prefijo}base_link',
        'world_frame': f'{prefijo}odom',
        'odom0': topico(TOPICO_ODOM_RF2O),
        'odom0_config': odom0,
        'odom0_differential': True,
        'imu0': topico('imu/data'),
        'imu0_config': imu0,
        'imu0_differential': False,
    }


def _lanzar(context, *args, **kwargs):
    urdf = _exigir(LaunchConfiguration('urdf').perform(context),
                   'el URDF de hardware', 'urdf')
    nav_params = _exigir(LaunchConfiguration('params').perform(context),
                         'el YAML de Nav2', 'params')
    slam_params = _exigir(LaunchConfiguration('slam_params').perform(context),
                          'el YAML de slam_toolbox', 'slam_params')

    arboles = LaunchConfiguration('behavior_trees').perform(context)
    if not arboles:
        raise RuntimeError(
            'No encuentro la carpeta de arboles de comportamiento y no se '
            'indico ruta. Pase behavior_trees:=/ruta/a/behavior_trees')
    bt_a_pose = _exigir(os.path.join(arboles, 'ackermann_navigate_to_pose.xml'),
                        'el arbol NavigateToPose', 'behavior_trees')
    bt_por_poses = _exigir(
        os.path.join(arboles, 'ackermann_navigate_through_poses.xml'),
        'el arbol NavigateThroughPoses', 'behavior_trees')

    with open(urdf, 'r') as archivo:
        descripcion = archivo.read()

    ns = LaunchConfiguration('namespace').perform(context).strip('/')
    # launch_ros distingue None (sin espacio de nombres) de '' (que traduce a
    # '__ns:=/'). Solo None deja la orden igual que antes del bloque C.
    ns_nodo = ns if ns else None
    prefijo = f'{ns}/' if ns else ''
    con_imu = IfCondition(LaunchConfiguration('imu')).evaluate(context)
    odom_rf2o = TOPICO_ODOM_RF2O if con_imu else 'odom'

    reescritos = RewrittenYaml(
        source_file=nav_params,
        param_rewrites={
            'use_sim_time': 'False',
            'min_approach_linear_velocity': VELOCIDAD_MINIMA_UTIL,
            'regulated_linear_scaling_min_speed': VELOCIDAD_MINIMA_UTIL,
            # 10 Hz y no los 20 de simulacion: la tarjeta de 2 nucleos no los
            # sostiene. El 2026-09-29, en amss-jgm9, el lazo corrio entre 1 y 6 Hz
            # con «Control loop missed its desired rate» en cada meta.
            'controller_frequency': FRECUENCIA_CONTROL,
            # Ajuste 8: Nav2 da la meta por alcanzada a 1 m y no a 0,25. Con 0,25
            # el Ackermann llegaba cerca de la meta, no podia corregir en tan poco espacio
            # y retrocedia buscando la meta (corrida p2r_01, 2026-09-30). El criterio
            # de G-3 sigue siendo 0,5 m (acta 6.1), medido con flexometro.
            'xy_goal_tolerance': LaunchConfiguration('margen_llegada').perform(context),
            'topic': TOPICO_SCAN,
            # Vacios en el YAML a proposito: sin rellenarlos, `bt_navigator`
            # carga el arbol por defecto de Nav2, que recupera con <Spin> —una
            # vuelta sobre el propio eje que un Ackermann no puede hacer—. El
            # vehiculo se quedaria girando las ruedas sin avanzar hasta agotar
            # los reintentos.
            'default_nav_to_pose_bt_xml': bt_a_pose,
            'default_nav_through_poses_bt_xml': bt_por_poses,
            **marcos_prefijados(prefijo),
        },
        # Con espacio de nombres el YAML se anida bajo el: sus claves sueltas
        # ('controller_server:') solo casan con el nodo '/controller_server'.
        root_key=ns_nodo,
        convert_types=True)

    slam_reescrito = RewrittenYaml(
        source_file=slam_params,
        param_rewrites={'use_sim_time': 'False', 'scan_topic': TOPICO_SCAN,
                        **marcos_slam(prefijo)},
        root_key=ns_nodo,
        convert_types=True)

    hay_slam = IfCondition(LaunchConfiguration('slam'))
    hay_nav = IfCondition(LaunchConfiguration('nav'))

    # Descubrimiento (2026-10-08). nav2_mapa_guardado.sh lanza todo con
    # descubrimiento local (ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST): con las dos
    # cadenas anunciandose por difusion en el WiFi, racey llego a carga 33 y su
    # WiFi a ~2000 paquetes/s. Solo cruzan la red los nodos que la topologia
    # necesita desde fuera: los que llama el coordinador (navegacion y limpieza de
    # costmaps) y los que graba la mision (odometria). Desde el 2026-10-09 el
    # coordinador y el grabador corren en el portatil: esos nodos lo tienen como
    # unico par conocido (ROS_STATIC_PEERS) y los vehiculos nunca se descubren
    # entre si. Fast DDS solo se anuncia a los participantes 0 a 3 de la maquina
    # par; el portatil tiene cuatro procesos ROS (herramientas/coordinador_portatil.sh).
    # Entre dos vehiculos, con ~15 procesos cada uno, eso no alcanzo (8-oct).
    #   'false' o vacio: sin cambios.   'subnet': descubrimiento normal, por la red.
    #   IP (o varias, con comas): esas, como pares conocidos.
    cruce = LaunchConfiguration('cruzan_la_red').perform(context).strip().lower()
    if cruce in ('', 'false'):
        red = {}
    elif cruce in ('true', 'subnet'):
        red = {'ROS_AUTOMATIC_DISCOVERY_RANGE': 'SUBNET'}
    else:
        red = {'ROS_STATIC_PEERS': cruce.replace(',', ';')}
    CRUZAN_LA_RED = ('bt_navigator', 'planner_server', 'controller_server')

    nodos_nav2 = [
        ('nav2_controller', 'controller_server'),
        ('nav2_planner', 'planner_server'),
        ('nav2_behaviors', 'behavior_server'),
        ('nav2_bt_navigator', 'bt_navigator'),
    ]

    acciones = [
        # Peldano 1 - TF del vehiculo.
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen', namespace=ns_nodo,
             parameters=[{'robot_description': descripcion,
                          'use_sim_time': False,
                          **({'frame_prefix': prefijo} if prefijo else {})}]),

        # Peldanos 2-3 - odometria deducida de los propios barridos. El carro no
        # lleva encoders: esta es su unica fuente de 'odom -> base_link', y sin
        # ella ni AMCL ni Nav2 arrancan.
        # Ajuste 7: rf2o arranca RETARDO_RF2O_S despues. Lee base_link -> laser una
        # sola vez, al arrancar; si robot_state_publisher todavia no lo publica, da
        # «"base_link" passed to lookupTransform argument target_frame does not
        # exist», toma el laser como si estuviera sin girar, y como esta montado a
        # 180 grados mide todo el movimiento al reves. Paso el 29-sep en los dos
        # carros: Nav2 mandaba avanzar, /odom decia que retrocedia y el carro no se
        # detuvo en la meta. mapear_conduciendo.sh no lo sufre porque publica la TF
        # 5 s antes de arrancar rf2o. El retraso solo no basta (30-sep): hace falta
        # el parche herramientas/parches/rf2o_esperar_tf_laser.patch en el carro.
        TimerAction(period=RETARDO_RF2O_S, actions=[
            Node(package='rf2o_laser_odometry', executable='rf2o_laser_odometry_node',
                 name='rf2o_laser_odometry', output='screen', namespace=ns_nodo,
                 parameters=[{'laser_scan_topic': TOPICO_SCAN,
                              'odom_topic': f'/{ns}/{odom_rf2o}' if ns else f'/{odom_rf2o}',
                              # Con la IMU la TF la publica el EKF.
                              'publish_tf': not con_imu,
                              'base_frame_id': f'{prefijo}base_link',
                              'odom_frame_id': f'{prefijo}odom',
                              'init_pose_from_topic': '',
                              'freq': 20.0,
                              'use_sim_time': False}],
                 # Ajuste 9: solo errores; sus INFO y WARN llenaban el registro.
                 arguments=['--ros-args', '--log-level', 'error'],
                 # Sin la IMU, rf2o publica /<ns>/odom, que se graba desde racey.
                 additional_env={} if con_imu else red)]),

        # Peldanos 4-5 - mapa y localizacion en una sola pieza. Se usa SLAM en
        # vivo y no mapa guardado + AMCL porque AMCL exige una pose inicial que
        # aqui habria que acertar a ojo, y una pose inicial mal puesta se
        # manifiesta como «Nav2 no planifica», que es indistinguible de media
        # docena de fallos distintos.
        Node(package='slam_toolbox', executable='sync_slam_toolbox_node',
             name='slam_toolbox', output='screen', namespace=ns_nodo,
             parameters=[slam_reescrito], condition=hay_slam),
    ]

    if con_imu:
        nodo_imu = _exigir(LaunchConfiguration('imu_nodo').perform(context),
                           'el nodo de la IMU', 'imu_nodo')
        acciones += [
            Node(executable='python3', arguments=[nodo_imu],
                 name='imu_bmi160', output='screen', namespace=ns_nodo,
                 parameters=[{'frame_id': f'{prefijo}imu_link', 'use_sim_time': False}]),
            Node(package='robot_localization', executable='ekf_node',
                 name='ekf_filter_node', output='screen', namespace=ns_nodo,
                 additional_env=red,           # publica /<ns>/odom
                 parameters=[parametros_ekf(prefijo, ns)],
                 remappings=[('odometry/filtered', 'odom')]),
        ]

    if prefijo:
        # El driver de AWS sella cada barrido en 'laser', sin prefijo, y no se
        # puede cambiar. Esta identidad lo cuelga del arbol del robot.
        acciones.append(
            Node(package='tf2_ros', executable='static_transform_publisher',
                 name='laser_aws', output='screen', namespace=ns_nodo,
                 arguments=['--x', '0', '--y', '0', '--z', '0',
                            '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
                            '--frame-id', f'{prefijo}laser',
                            '--child-frame-id', 'laser']))

    # Peldanos 6-7 - planificador y control.
    for paquete, ejecutable in nodos_nav2:
        parametros = [reescritos]
        if ejecutable == 'bt_navigator':
            # Ajuste 6. Va aparte y no en la reescritura porque la clave no esta
            # en el YAML, y RewrittenYaml solo cambia claves que ya existen.
            parametros.append({'default_server_timeout': PLAZO_SERVIDOR_MS})
        elif ejecutable == 'planner_server':
            # Ajuste 10, aparte por lo mismo: la clave no esta en el YAML.
            parametros.append({'GridBased.lookup_table_size': TABLA_PLANIFICADOR_M})
        acciones.append(Node(package=paquete, executable=ejecutable,
                             name=ejecutable, output='screen', namespace=ns_nodo,
                             parameters=parametros, condition=hay_nav,
                             additional_env=red if ejecutable in CRUZAN_LA_RED else {}))

    acciones.append(
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_navigation', output='screen',
             namespace=ns_nodo,
             # bond_timeout 60 s y no los 4 de fabrica: con la tarjeta de 2 nucleos a
             # carga 18, el latido de controller_server no llego en 4 s y el gestor
             # desactivo todo Nav2 35 s despues de activarlo (amss-jgm9, 2026-09-29).
             # Con 20 s tampoco alcanzo el 2026-10-08, con los dos vehiculos en la
             # red: carga 22, 271 s para configurar planner_server, y el arranque se
             # aborto al activar controller_server.
             parameters=[{'use_sim_time': False, 'autostart': True,
                          'bond_timeout': 60.0,
                          'node_names': [n for _, n in nodos_nav2]}],
             condition=hay_nav))

    return acciones


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'urdf',
            default_value=_ruta_en_paquete('deepracer_description',
                                           'models', 'urdf',
                                           'deepracer_hardware.urdf'),
            description='URDF de hardware. Obligatorio en la tarjeta.'),
        DeclareLaunchArgument(
            'params',
            default_value=_ruta_en_paquete('deepracer_bringup', 'config',
                                           PARAMS_JAZZY),
            description='YAML de Nav2 para Jazzy. Obligatorio en la tarjeta.'),
        DeclareLaunchArgument(
            'slam_params',
            default_value=_ruta_en_paquete('deepracer_bringup', 'config',
                                           'slam_toolbox.yaml'),
            description='YAML de slam_toolbox. Obligatorio en la tarjeta.'),
        DeclareLaunchArgument(
            'behavior_trees',
            default_value=_ruta_en_paquete('deepracer_bringup',
                                           'behavior_trees'),
            description='Carpeta con los dos arboles Ackermann. '
                        'Obligatoria en la tarjeta.'),
        DeclareLaunchArgument(
            'slam', default_value='false',
            description='Arranca slam_toolbox (peldanos 4-5).'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description="Espacio de nombres del robot ('robot1' o 'robot2'). "
                        'Vacio deja el lanzamiento como antes del bloque C.'),
        DeclareLaunchArgument(
            'margen_llegada', default_value=MARGEN_LLEGADA_NAV2_M,
            description='Distancia en m a la que Nav2 da la meta por alcanzada '
                        '(ajuste 8).'),
        DeclareLaunchArgument(
            'imu', default_value='false',
            description='Arranca la IMU y el EKF que la combina con rf2o. '
                        'El vehiculo tiene que estar quieto al arrancar.'),
        DeclareLaunchArgument(
            'imu_nodo', default_value=_junto_al_lanzador(NODO_IMU),
            description='Ruta de imu_bmi160.py. Por defecto, junto al lanzador.'),
        DeclareLaunchArgument(
            'cruzan_la_red', default_value='false',
            description="Nodos que se usan desde fuera del vehiculo: 'false' sin "
                        "cambios; 'subnet' descubrimiento por la red; una IP (o varias, "
                        'con comas), pares conocidos: la del portatil.'),
        DeclareLaunchArgument(
            'nav', default_value='false',
            description='Arranca planificador y control (peldanos 6-7). '
                        'Exige slam:=true.'),
        OpaqueFunction(function=_lanzar),
    ])
