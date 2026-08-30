#################################################################################
#   Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.          #
#                                                                               #
#   Licensed under the Apache License, Version 2.0 (the "License").             #
#   You may not use this file except in compliance with the License.            #
#   You may obtain a copy of the License at                                     #
#                                                                               #
#       http://www.apache.org/licenses/LICENSE-2.0                              #
#                                                                               #
#   Unless required by applicable law or agreed to in writing, software         #
#   distributed under the License is distributed on an "AS IS" BASIS,           #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    #
#   See the License for the specific language governing permissions and         #
#   limitations under the License.                                              #
#################################################################################

# Modificado para el sistema colaborativo (Documentos/CONTRATO_INTERFACES.md §6).
#
# Cambios respecto al original de AWS:
#   - Argumento 'namespace': vacio (por defecto) deja el lanzamiento identico al
#     original; con 'robot1' los seis nodos de Nav2 cuelgan de /robot1.
#   - Los marcos que Nav2 lee del YAML se prefijan ('robot1/base_link'), porque
#     el URDF los publica prefijados via 'frame_prefix' de robot_state_publisher.
#     Sin esto el costmap global falla en bucle con
#     'Invalid frame ID "map" ... frame does not exist'.
#
# Se usa OpaqueFunction por la misma razon que en deepracer_spawn.launch.py: el
# prefijo hay que componerlo como texto y, con namespace vacio, hay que OMITIRLO
# en vez de concatenar cadenas vacias. Las sustituciones de launch no saben
# omitir; Python si.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, OpaqueFunction,
                            SetEnvironmentVariable)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml

LIFECYCLE_NODES = ['controller_server',
                   'planner_server',
                   'behavior_server',
                   'bt_navigator',
                   'waypoint_follower']


def marcos_prefijados(prefijo):
    """Rutas del YAML de Nav2 cuyo valor es un marco del robot.

    Se usan rutas COMPLETAS ('a.b.c.clave') y no la clave suelta a proposito.
    RewrittenYaml sustituye primero por clave hoja, y 'global_frame' aparece dos
    veces con valores distintos: 'map' en el costmap global y 'odom' en el local.
    Reescribir por clave suelta igualaria los dos y romperia el costmap local en
    silencio, que es de los fallos mas caros de diagnosticar.

    'map' SI se prefija, desde el 2026-08-24. Aqui estuvo escrito que no -"no
    pertenece al robot, lo publica el map_server"- y ese parrafo costo una
    mision abortada: el coordinador mandaba el goal en 'robot1/map' siguiendo el
    §3 del contrato, el marco no existia, el planner no podia transformarlo y
    Nav2 terminaba en ABORTED tras un BackUp de 0,41 m sin haber avanzado nunca.
    No hay un 'map' comun: hay DOS mapas distintos que se llamaban igual, y solo
    convivian porque cada robot esta en su propio dominio DDS. Diagnostico en
    Evidencia/S20_marco_map_prefijado.md.
    """
    if not prefijo:
        # Sin namespace no se reescribe NADA: el YAML llega al nodo tal cual
        # esta en disco, byte a byte igual que en el original.
        return {}

    base = f'{prefijo}base_link'
    odom = f'{prefijo}odom'
    mapa = f'{prefijo}map'
    return {
        'bt_navigator.ros__parameters.global_frame': mapa,
        'bt_navigator.ros__parameters.robot_base_frame': base,

        'local_costmap.local_costmap.ros__parameters.global_frame': odom,
        'local_costmap.local_costmap.ros__parameters.robot_base_frame': base,

        'global_costmap.global_costmap.ros__parameters.global_frame': mapa,
        'global_costmap.global_costmap.ros__parameters.robot_base_frame': base,

        'behavior_server.ros__parameters.global_frame': odom,
        'behavior_server.ros__parameters.robot_base_frame': base,
    }


def topicos_prefijados(ns):
    """Rutas del YAML de Nav2 cuyo valor es un topic que publica ESTE robot.

    Nav2 en Humble NO resuelve namespaces en los topics de las capas del
    costmap: usa el nombre del YAML tal cual, sea absoluto o no. Lo demuestra el
    propio nav2_bringup, que para multi-robot no recurre a nombres relativos
    sino que escribe el namespace a mano en un YAML por robot
    (nav2_multirobot_params_1.yaml:200 dice '/robot1/scan'). Aqui se hace lo
    mismo, pero desde el launch, para no acabar con un YAML por cada robot.

    Poner el nombre RELATIVO ('scan') tampoco funcionaria, y es la trampa facil:
    el nodo del costmap no se llama '/robot1' sino
    '/robot1/global_costmap/global_costmap', asi que 'scan' se resolveria a
    '/robot1/global_costmap/scan', que no publica nadie.

    Y suscribirse a un topic sin publicador NO da error. La capa se queda vacia,
    el costmap solo contiene lo que venia del mapa estatico, y el robot atraviesa
    tan tranquilo cualquier obstaculo que no estuviera ya en el mapa.

    Cuidado con el nombre de la capa: en el costmap local es 'voxel_layer' y en
    el global 'obstacle_layer'. Son distintas y no son intercambiables.
    """
    if not ns:
        # Sin namespace el LiDAR publica en '/scan', que es justo lo que el YAML
        # ya dice. No se reescribe nada.
        return {}

    scan = f'/{ns}/scan'
    return {
        'local_costmap.local_costmap.ros__parameters.voxel_layer.scan.topic': scan,
        'global_costmap.global_costmap.ros__parameters.obstacle_layer.scan.topic': scan,
    }


def acciones(context, *args, **kwargs):
    ns = LaunchConfiguration('namespace').perform(context).strip('/')

    # launch_ros distingue None (sin namespace) de '' (que traduce a '__ns:=/').
    # Solo None deja la orden de ejecucion identica a la original.
    ns_nodo = ns if ns else None

    # El prefijo de marcos lleva '/' final: 'robot1/base_link'. Es la convencion
    # de robot_state_publisher, que concatena sin separador.
    prefijo = f'{ns}/' if ns else ''

    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params')
    nav_to_pose_bt_xml = LaunchConfiguration('nav_to_pose_bt_xml')
    nav_through_poses_bt_xml = LaunchConfiguration('nav_through_poses_bt_xml')

    param_substitutions = {
        'use_sim_time': use_sim_time,
        'default_nav_to_pose_bt_xml': nav_to_pose_bt_xml,
        'default_nav_through_poses_bt_xml': nav_through_poses_bt_xml,
        'autostart': autostart,
    }
    param_substitutions.update(marcos_prefijados(prefijo))
    param_substitutions.update(topicos_prefijados(ns))

    # root_key anida TODO el YAML bajo la clave del namespace. Es obligatorio:
    # el archivo tiene claves de primer nivel sueltas ('bt_navigator:'), que ROS
    # solo asocia al nodo '/bt_navigator'. Con namespace el nodo pasa a llamarse
    # '/robot1/bt_navigator' y dejaria de leer sus parametros EN SILENCIO, con
    # los valores por defecto del codigo. Anidando queda 'robot1: bt_navigator:',
    # que si corresponde al nombre completo.
    #
    # El anidado ocurre DESPUES de las sustituciones (ver rewritten_yaml.py:89-94),
    # asi que las rutas de 'marcos_prefijados' se escriben sin el prefijo de ns.
    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=ns_nodo,
        param_rewrites=param_substitutions,
        convert_types=True)

    # NO se remapea /tf ni /tf_static, a diferencia de lo que hace nav2_bringup
    # para multi-robot.
    #
    # OJO AL MOTIVO, QUE CAMBIO EL 2026-08-30. Hasta esa fecha aqui decia que
    # cada robot vivia en su propio ROS_DOMAIN_ID y que por eso el arbol TF ya
    # estaba aislado. Eso ya no es cierto: los dos robots comparten el dominio 0
    # y comparten, por tanto, el topico /tf.
    #
    # La conclusion sobrevive pero por otra razon, y es una que ya estaba pagada:
    # TODOS los marcos van prefijados con el namespace, incluido 'map' desde el
    # 2026-08-24 (Evidencia/S20_marco_map_prefijado.md). Dos arboles con marcos
    # 'robot1/...' y 'robot2/...' conviven en un mismo /tf sin tocarse, porque no
    # comparten ni un solo nombre de marco. Lo que se comparte es el topico, no
    # el arbol.
    #
    # Lo que se paga es ancho de banda y memoria: el buffer TF de cada robot
    # guarda tambien las transformadas del otro. Es el precio de no remapear, y
    # remapear costaria tocar el robot_state_publisher y los plugins de Gazebo,
    # que publican en /tf absoluto.
    remappings = []

    # El reloj SI hay que remapearlo, y aqui esta la parte que Gazebo no cubre:
    # estos nodos corren FUERA de gzserver, asi que no heredan su '--remap'. Con
    # use_sim_time, rclcpp se suscribe a '/clock' con nombre absoluto, de modo
    # que el namespace tampoco los alcanza. Sin esta linea, la pila de robot2
    # planifica y controla con el tiempo del simulador de robot1: no hay error,
    # hay extrapolacion de TF y una trayectoria que no corresponde a lo medido.
    #
    # Solo se remapea cuando no es '/clock', para dejar al robot de referencia
    # exactamente como estaba (Evidencia/S21_bloqueo_dominios.md §5.3).
    reloj = LaunchConfiguration('clock_topic').perform(context).strip()
    if reloj and reloj != '/clock':
        remappings.append(('/clock', reloj))

    comunes = dict(output='screen',
                   namespace=ns_nodo,
                   parameters=[configured_params],
                   remappings=remappings)

    return [
        Node(package='nav2_controller', executable='controller_server',
             **comunes),
        Node(package='nav2_planner', executable='planner_server',
             name='planner_server', **comunes),
        Node(package='nav2_behaviors', executable='behavior_server',
             name='behavior_server', **comunes),
        Node(package='nav2_bt_navigator', executable='bt_navigator',
             name='bt_navigator', **comunes),
        Node(package='nav2_waypoint_follower', executable='waypoint_follower',
             name='waypoint_follower', **comunes),

        # El gestor de ciclo de vida no lee el YAML: sus nombres de nodo son
        # relativos y se resuelven dentro del mismo namespace.
        #
        # Lleva 'remappings' aunque no use 'comunes' porque tambien declara
        # use_sim_time, y por tanto tambien se suscribe a '/clock'. Sin el
        # remapeo se quedaria esperando el reloj del otro simulador y sus
        # temporizadores de transicion contarian mal.
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_navigation', output='screen',
             namespace=ns_nodo,
             remappings=remappings,
             parameters=[{'use_sim_time': use_sim_time},
                         {'autostart': autostart},
                         {'node_names': LIFECYCLE_NODES}]),
    ]


def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')

    return LaunchDescription([
        # Set env var to print messages to stdout immediately
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        DeclareLaunchArgument(
            'namespace', default_value='',
            description="Namespace del robot, p.ej. 'robot1'. "
                        'Vacio = comportamiento original de un solo robot.'),

        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            'clock_topic', default_value='/clock',
            description='Topico de reloj del gzserver de este robot. Con dos '
                        'simuladores en el mismo dominio, uno se queda en '
                        "/clock -el de referencia- y el otro usa '/robotN/clock'."),

        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically startup the nav2 stack'),

        DeclareLaunchArgument(
            'params',
            default_value=[deepracer_bringup_dir, '/config/nav2_params.yaml'],
            description='Full path to the ROS2 parameters file to use'),

        # Arboles de comportamiento adecuados a cinematica Ackermann:
        # excluyen la maniobra <Spin> del ciclo de recuperacion.
        DeclareLaunchArgument(
            'nav_to_pose_bt_xml',
            default_value=os.path.join(
                deepracer_bringup_dir,
                'behavior_trees', 'ackermann_navigate_to_pose.xml'),
            description='Behavior tree para NavigateToPose'),

        DeclareLaunchArgument(
            'nav_through_poses_bt_xml',
            default_value=os.path.join(
                deepracer_bringup_dir,
                'behavior_trees', 'ackermann_navigate_through_poses.xml'),
            description='Behavior tree para NavigateThroughPoses'),

        OpaqueFunction(function=acciones),
    ])
