# Localizacion (map_server + AMCL) con soporte de namespace.
#
# POR QUE ESTE ARCHIVO EXISTE en vez de incluir nav2_bringup/localization_launch.py
# ---------------------------------------------------------------------------
# El launch de nav2_bringup no sirve para esta topologia por dos razones, y las
# dos son silenciosas (no dan error, simplemente no funciona la navegacion):
#
#   1. Sus nodos NO llevan 'namespace='. El argumento 'namespace' solo se usa
#      como root_key del YAML. Quien namespacea los nodos es el PushRosNamespace
#      de bringup_launch.py, que aqui no se usa. Incluirlo tal cual dejaria a
#      /amcl y /map_server en la raiz leyendo un YAML anidado bajo 'robot1:',
#      es decir, sin parametros y con los valores por defecto del codigo.
#
#   2. Remapea ('/tf', 'tf') de forma fija (localization_launch.py:52-53). Bajo
#      un namespace eso manda la transformada map->odom a /robot1/tf, mientras
#      que robot_state_publisher y Gazebo publican en /tf absoluto. El arbol TF
#      quedaria partido en dos.
#
# Aqui cada robot vive en su propio ROS_DOMAIN_ID y su propio gzserver (ver
# Documentos/Evidencia/S17_dos_simuladores.md), asi que el /tf de cada dominio
# ya esta aislado y no hay nada que remapear. Los marcos si van prefijados
# ('robot1/base_link'), porque asi los publica el URDF.

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, OpaqueFunction,
                            SetEnvironmentVariable)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml

LIFECYCLE_NODES = ['map_server', 'amcl']


def acciones(context, *args, **kwargs):
    ns = LaunchConfiguration('namespace').perform(context).strip('/')

    # launch_ros distingue None (sin namespace) de '' (que traduce a '__ns:=/').
    ns_nodo = ns if ns else None
    prefijo = f'{ns}/' if ns else ''

    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params')
    map_yaml = LaunchConfiguration('map')

    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml,
    }

    if prefijo:
        # 'global_frame_id' NO se toca: 'map' lo publica el map_server y es el
        # ancla comun. Se usan rutas completas por coherencia con el launch de
        # navegacion, donde la clave suelta seria ambigua.
        param_substitutions.update({
            'amcl.ros__parameters.base_frame_id': f'{prefijo}base_link',
            'amcl.ros__parameters.odom_frame_id': f'{prefijo}odom',
        })

    # root_key: el YAML tiene claves de primer nivel sueltas ('amcl:'), que solo
    # casan con el nodo '/amcl'. Con namespace hay que anidarlas.
    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=ns_nodo,
        param_rewrites=param_substitutions,
        convert_types=True)

    comunes = dict(output='screen',
                   namespace=ns_nodo,
                   parameters=[configured_params])

    return [
        Node(package='nav2_map_server', executable='map_server',
             name='map_server', **comunes),
        Node(package='nav2_amcl', executable='amcl',
             name='amcl', **comunes),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_localization', output='screen',
             namespace=ns_nodo,
             parameters=[{'use_sim_time': use_sim_time},
                         {'autostart': autostart},
                         {'node_names': LIFECYCLE_NODES}]),
    ]


def generate_launch_description():
    return LaunchDescription([
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        DeclareLaunchArgument(
            'namespace', default_value='',
            description="Namespace del robot, p.ej. 'robot1'. "
                        'Vacio = un solo robot, sin prefijos.'),

        DeclareLaunchArgument(
            'map', description='Ruta completa al YAML del mapa'),

        DeclareLaunchArgument(
            'params', description='Ruta completa al YAML de parametros Nav2'),

        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Usar el reloj de Gazebo'),

        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Arrancar automaticamente el ciclo de vida'),

        OpaqueFunction(function=acciones),
    ])
