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

Los tres ajustes de hardware, y por que son justo estos tres
-----------------------------------------------------------
`nav2_params.yaml` se usa tal cual: es la configuracion Ackermann buena —RPP con
`use_rotate_to_heading: false` y Smac Hibrido con `minimum_turning_radius: 0.35`—
y no se duplica. El propio archivo advierte en su cabecera que dos copias que
divergen hacen que una corrida de un resultado distinto segun quien la lance.
Aqui se reescriben unas pocas claves con `RewrittenYaml`, sobre la misma fuente:

1. `min_approach_linear_velocity` 0,05 -> 0,40
2. `regulated_linear_scaling_min_speed` 0,25 -> 0,40

   Las dos por la **banda muerta del acelerador**, que solo existe en hardware.
   `get_mapped_throttle` calcula `pct = |v| / MAX_SPEED` con `MAX_SPEED = 4.0` y
   su umbral mas bajo es 0,1, asi que **todo `linear.x` por debajo de 0,40 m/s
   sale como throttle 0,0000 exacto**. Con los valores de simulacion, RPP frena
   a 0,05 en los ultimos 0,6 m antes de la meta y a 0,25 en toda curva de radio
   menor que 0,9 m: en los dos casos el carro se detiene, el mando publicado es
   valido, y ningun log dice nada. Subirlos a 0,40 no acelera al vehiculo, solo
   impide que RPP pida velocidades que fisicamente significan «parado».

3. `topic` y `scan_topic` -> `/rplidar_ros/scan`

   El driver de fabrica no publica en `/scan`. Se cambia por parametro y no por
   remapeo para que quede una sola forma de decirlo, y porque la capa de
   obstaculos del costmap toma su topico de un parametro, no de un remapeo.

`use_sim_time` pasa a falso en todo el arbol, que es lo que separa esta corrida
de una de Gazebo.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


# Suelo de velocidad que el puente traduce a traccion distinta de cero.
# Por debajo de esto, 'get_mapped_throttle' devuelve 0,0000 exacto.
VELOCIDAD_MINIMA_UTIL = '0.40'

TOPICO_SCAN = '/rplidar_ros/scan'


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


def _exigir(ruta, que, argumento):
    if not ruta:
        raise RuntimeError(
            'No encuentro %s y no se indico ruta. Pase %s:=/ruta/al/archivo'
            % (que, argumento))
    if not os.path.isfile(ruta):
        raise RuntimeError('%s no existe: %s' % (que, ruta))
    return ruta


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

    reescritos = RewrittenYaml(
        source_file=nav_params,
        param_rewrites={
            'use_sim_time': 'False',
            'min_approach_linear_velocity': VELOCIDAD_MINIMA_UTIL,
            'regulated_linear_scaling_min_speed': VELOCIDAD_MINIMA_UTIL,
            'topic': TOPICO_SCAN,
            # Vacios en el YAML a proposito: sin rellenarlos, `bt_navigator`
            # carga el arbol por defecto de Nav2, que recupera con <Spin> —una
            # vuelta sobre el propio eje que un Ackermann no puede hacer—. El
            # vehiculo se quedaria girando las ruedas sin avanzar hasta agotar
            # los reintentos.
            'default_nav_to_pose_bt_xml': bt_a_pose,
            'default_nav_through_poses_bt_xml': bt_por_poses,
        },
        convert_types=True)

    slam_reescrito = RewrittenYaml(
        source_file=slam_params,
        param_rewrites={'use_sim_time': 'False', 'scan_topic': TOPICO_SCAN},
        convert_types=True)

    hay_slam = IfCondition(LaunchConfiguration('slam'))
    hay_nav = IfCondition(LaunchConfiguration('nav'))

    nodos_nav2 = [
        ('nav2_controller', 'controller_server'),
        ('nav2_planner', 'planner_server'),
        ('nav2_behaviors', 'behavior_server'),
        ('nav2_bt_navigator', 'bt_navigator'),
    ]

    acciones = [
        # Peldano 1 - TF del vehiculo.
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': descripcion,
                          'use_sim_time': False}]),

        # Peldanos 2-3 - odometria deducida de los propios barridos. El carro no
        # lleva encoders: esta es su unica fuente de 'odom -> base_link', y sin
        # ella ni AMCL ni Nav2 arrancan.
        Node(package='rf2o_laser_odometry', executable='rf2o_laser_odometry_node',
             name='rf2o_laser_odometry', output='screen',
             parameters=[{'laser_scan_topic': TOPICO_SCAN,
                          'odom_topic': '/odom',
                          'publish_tf': True,
                          'base_frame_id': 'base_link',
                          'odom_frame_id': 'odom',
                          'init_pose_from_topic': '',
                          'freq': 20.0,
                          'use_sim_time': False}]),

        # Peldanos 4-5 - mapa y localizacion en una sola pieza. Se usa SLAM en
        # vivo y no mapa guardado + AMCL porque AMCL exige una pose inicial que
        # aqui habria que acertar a ojo, y una pose inicial mal puesta se
        # manifiesta como «Nav2 no planifica», que es indistinguible de media
        # docena de fallos distintos.
        Node(package='slam_toolbox', executable='sync_slam_toolbox_node',
             name='slam_toolbox', output='screen',
             parameters=[slam_reescrito], condition=hay_slam),
    ]

    # Peldanos 6-7 - planificador y control.
    for paquete, ejecutable in nodos_nav2:
        acciones.append(Node(package=paquete, executable=ejecutable,
                             name=ejecutable, output='screen',
                             parameters=[reescritos], condition=hay_nav))

    acciones.append(
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_navigation', output='screen',
             parameters=[{'use_sim_time': False, 'autostart': True,
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
                                           'nav2_params.yaml'),
            description='YAML de Nav2. Obligatorio en la tarjeta.'),
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
            'nav', default_value='false',
            description='Arranca planificador y control (peldanos 6-7). '
                        'Exige slam:=true.'),
        OpaqueFunction(function=_lanzar),
    ])
