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


def como_decimal(context, nombre):
    """Lee un argumento numerico del launch y lo devuelve como texto decimal.

    Existe por un detalle que rompe el arranque de AMCL de forma muy poco obvia.
    RewrittenYaml se construye con 'convert_types=True', asi que convierte cada
    valor mirando si el texto lleva un punto: con punto lo pasa a float, sin
    punto a int (rewritten_yaml.py:179). Los argumentos del spawn traen '0' por
    defecto, luego llegarian al YAML como el entero 0. Y 'initial_pose.x' esta
    declarado como double: recibir un entero aborta el nodo con un error de tipo
    de parametro, no con un mensaje sobre la pose.

    Pasarlo por float() y de vuelta a texto garantiza el punto: '0' -> '0.0'.
    """
    texto = LaunchConfiguration(nombre).perform(context)
    try:
        return repr(float(texto))
    except ValueError:
        raise RuntimeError(
            f"El argumento {nombre}:={texto} no es un numero. "
            "x, y e yaw son la pose de spawn del robot, en metros y radianes.")


def pose_inicial(context):
    """Le dice a AMCL en que pose nace el robot.

    Sin esto AMCL siempre empieza creyendose en el origen. Para un robot que
    nace en el origen da igual; para uno lanzado con 'y:=2.0' significa arrancar
    con dos metros de error, y AMCL no lo corrige de golpe: va arrastrando la
    nube de particulas mientras el robot se mueve, asi que el sintoma no es un
    error claro sino un robot que navega de forma rara los primeros metros.

    Se reescribe SIEMPRE, tambien sin namespace, porque la pose de spawn es una
    propiedad del robot y no del namespace. Con los valores por defecto (0, 0, 0)
    el resultado es identico a lo que AMCL usaba antes; comprobado con
    'ros2 param get /amcl initial_pose.x' -> 0.0.
    """
    return {
        'amcl.ros__parameters.initial_pose.x': como_decimal(context, 'x'),
        'amcl.ros__parameters.initial_pose.y': como_decimal(context, 'y'),
        'amcl.ros__parameters.initial_pose.yaw': como_decimal(context, 'yaw'),
    }


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
    param_substitutions.update(pose_inicial(context))

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

        # Los mismos nombres que usa deepracer_spawn.launch.py, para que quien
        # lanza escriba 'y:=2.0' una sola vez y valga para el robot y para AMCL.
        DeclareLaunchArgument('x', default_value='0',
                              description='Pose de spawn del robot, en metros'),
        DeclareLaunchArgument('y', default_value='0',
                              description='Pose de spawn del robot, en metros'),
        DeclareLaunchArgument('yaw', default_value='0',
                              description='Orientacion de spawn, en radianes'),

        OpaqueFunction(function=acciones),
    ])
