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

import os
import sys

from ament_index_python.packages import get_package_share_directory
import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource

# El modulo vive junto a este archivo, dentro del propio paquete instalado.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from deepracer_raiz_repo import mundo_por_defecto  # noqa: E402


def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')

    # ros gazebo launcher
    gazebo_dir = get_package_share_directory('gazebo_ros')
    world_cfg = launch.substitutions.LaunchConfiguration('world')

    gazebo_server_launcher = IncludeLaunchDescription(
        launch_description_source=PythonLaunchDescriptionSource(
            launch_file_path=gazebo_dir + '/launch/gzserver.launch.py'),
            launch_arguments={'world': world_cfg,
                              'pause': 'false',
                              'record': 'false',
                              'verbose': 'false',
                              'physics': 'ode'}.items())
    # 'gui' se declaraba pero no se conectaba a nada, asi que gui:=false abria la
    # ventana igual. Importa al medir con dos simulaciones: el cuello de botella
    # es la VRAM de la GPU integrada, y cada gzclient cuesta unos 170 MB.
    gazebo_client_launcher = IncludeLaunchDescription(
        launch_description_source=PythonLaunchDescriptionSource(
            launch_file_path=gazebo_dir + '/launch/gzclient.launch.py'),
        launch_arguments={'verbose': 'false'}.items(),
        condition=IfCondition(launch.substitutions.LaunchConfiguration('gui')))

    # Los argumentos de namespace y pose se pasan tal cual al launch de spawn:
    # este archivo solo levanta Gazebo, quien decide donde y con que nombre
    # nace el robot es deepracer_spawn.launch.py.
    spawn_deepracer = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(deepracer_bringup_dir, 'launch', 'deepracer_spawn.launch.py')),
        launch_arguments={
            'namespace': launch.substitutions.LaunchConfiguration('namespace'),
            'x': launch.substitutions.LaunchConfiguration('x'),
            'y': launch.substitutions.LaunchConfiguration('y'),
            'z': launch.substitutions.LaunchConfiguration('z'),
            'yaw': launch.substitutions.LaunchConfiguration('yaw'),
        }.items()
    )

    # 'world' tenia que escribirse a mano en cada lanzamiento, con la ruta absoluta
    # del clon. Eso hacia trivial mapear contra la geometria de OTRA copia del
    # repositorio sin enterarse. Ahora el defecto sale del mismo checkout que este
    # archivo; world:= sigue disponible para cambiar de mundo.
    return LaunchDescription([DeclareLaunchArgument(
          'world',
          default_value=mundo_por_defecto(),
          description='SDF world file'),
        DeclareLaunchArgument(
            name='gui',
            default_value='true'
        ),
        DeclareLaunchArgument(
            name='use_sim_time',
            default_value='true'
        ),
        DeclareLaunchArgument(
            name='namespace',
            default_value='',
            description="Namespace del robot, p.ej. 'robot1'. "
                        'Vacio = comportamiento original de un solo robot.'
        ),
        # La pose por defecto es el EJE DEL PASILLO DEL PISO 1 del mundo vigente,
        # no el origen del mundo. Mientras el mundo fue 'primer_piso_v2.world' el
        # origen caia dentro del pasillo y (0, 0) servia; en
        # 'mundo_definitivo.world' los dos pasillos estan corridos en Y -piso 1 en
        # y = +10.02, piso 2 en y = -4.48- y (0, 0) queda en la explanada vacia
        # ENTRE los dos. El fallo no se ve al lanzar: Gazebo abre, el vehiculo
        # aparece y los 7 controladores quedan activos; lo que no hay es pasillo
        # alrededor, y (0, 0) ni siquiera es una celda del mapa del piso 1, de modo
        # que AMCL arranca fuera del mapa.
        # y = 10.05 deja 1.08 m de holgura al obstaculo mas cercano, medido por
        # transformada de distancia sobre maps/mundo_definitivo_piso1.pgm.
        DeclareLaunchArgument(name='x', default_value='0'),
        DeclareLaunchArgument(name='y', default_value='10.05'),
        DeclareLaunchArgument(name='z', default_value='0.03'),
        DeclareLaunchArgument(name='yaw', default_value='0'),
        gazebo_server_launcher,
        gazebo_client_launcher,
        spawn_deepracer
    ])


if __name__ == '__main__':
    generate_launch_description()
