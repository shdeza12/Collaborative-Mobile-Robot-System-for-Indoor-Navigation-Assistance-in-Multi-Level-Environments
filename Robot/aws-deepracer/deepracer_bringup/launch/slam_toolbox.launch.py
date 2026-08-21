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
#
# SLAM (slam_toolbox) con soporte de namespace.
#
# Sigue el mismo patron que deepracer_localization_sim.launch.py, y por los
# mismos motivos: el YAML tiene la clave de primer nivel 'slam_toolbox:', que
# solo casa con el nodo '/slam_toolbox'. Bajo namespace el nodo pasa a llamarse
# '/robot1/slam_toolbox' y esa clave deja de casar, de modo que el nodo arranca
# con TODOS los valores por defecto del codigo y ninguno de los ajustes de este
# repositorio. El fallo es silencioso: slam_toolbox levanta y mapea, solo que
# con los parametros del upstream -dimensionados para una pista de carreras
# pequena- y el mapa del pasillo sale sin enlazar. Por eso se anida el YAML con
# root_key.
#
# Los marcos SI van prefijados ('robot1/odom', 'robot1/base_link'), porque asi
# los publica el URDF. 'map_frame' NO se prefija: es el ancla comun, igual que
# en el launch de localizacion. Cada robot vive en su propio ROS_DOMAIN_ID, asi
# que dos 'map' simultaneos no colisionan.

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def acciones(context, *args, **kwargs):
    ns = LaunchConfiguration('namespace').perform(context).strip('/')

    # launch_ros distingue None (sin namespace) de '' (que traduce a '__ns:=/').
    ns_nodo = ns if ns else None
    prefijo = f'{ns}/' if ns else ''

    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params')

    param_substitutions = {'use_sim_time': use_sim_time}

    if prefijo:
        param_substitutions.update({
            'slam_toolbox.ros__parameters.odom_frame': f'{prefijo}odom',
            'slam_toolbox.ros__parameters.base_frame': f'{prefijo}base_link',
            # El nodo esta namespaceado, luego 'scan' relativo bastaria; se deja
            # absoluto para que 'ros2 param get ... scan_topic' diga a que se
            # suscribe de verdad y no haya que resolverlo mentalmente.
            'slam_toolbox.ros__parameters.scan_topic': f'/{prefijo}scan',
        })

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=ns_nodo,
        param_rewrites=param_substitutions,
        convert_types=True)

    # slam_toolbox crea el publicador del mapa con el nombre absoluto '/map', de
    # modo que el namespace del nodo no lo alcanza. El resto del sistema -y la
    # config de RViz- espera '/robot1/map', que es donde publica map_server en
    # el escenario con AMCL. Sin este remap la misma config de RViz sirve para
    # navegar pero no para mapear, y el mapa aparece vacio sin ningun error.
    remapeos = []
    if prefijo:
        remapeos = [('/map', f'/{prefijo}map'),
                    ('/map_metadata', f'/{prefijo}map_metadata')]

    return [
        Node(package='slam_toolbox',
             executable='sync_slam_toolbox_node',
             name='slam_toolbox',
             namespace=ns_nodo,
             parameters=[configured_params],
             remappings=remapeos,
             output='screen'),
    ]


def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='',
            description="Namespace del robot, p.ej. 'robot1'. "
                        'Vacio = un solo robot, sin prefijos.'),

        DeclareLaunchArgument(
            'params',
            default_value=deepracer_bringup_dir + '/config/slam_toolbox.yaml',
            description='Ruta completa al YAML de parametros de slam_toolbox'),

        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Usar el reloj de Gazebo'),

        OpaqueFunction(function=acciones),
    ])


if __name__ == '__main__':
    generate_launch_description()
