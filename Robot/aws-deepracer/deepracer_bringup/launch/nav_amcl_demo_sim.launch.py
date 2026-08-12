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
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

# El modulo vive junto a este archivo, dentro del propio paquete instalado.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from deepracer_raiz_repo import mundo_por_defecto  # noqa: E402


def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')

    # La raiz del repositorio se deduce de la ubicacion real del archivo; el porque
    # esta en la cabecera de 'deepracer_raiz_repo.py'. La logica vive alli y no
    # duplicada aqui: dos copias de la misma regla divergen sin avisar.
    #
    # Mundo y mapa van EN PAREJA: el .yaml se construyo mapeando ese .world. Cambiar
    # uno solo hace que AMCL localice contra una geometria distinta de la simulada,
    # y el sintoma -deriva que crece- no se parece a un error de configuracion.
    # El mundo vigente lo declara el README; 'herramientas/verificar_repositorio.sh'
    # comprueba que este default y el del README sigan siendo el mismo.
    default_world = mundo_por_defecto()
    default_map = os.path.join(deepracer_bringup_dir, 'maps', 'primer_piso_v2.yaml')
    nav_params = os.path.join(deepracer_bringup_dir, 'config', 'nav2_params_nav_amcl_sim_demo.yaml')

    world_cfg = LaunchConfiguration('world')
    map_cfg = LaunchConfiguration('map')
    params_cfg = LaunchConfiguration('params')
    # Namespace del robot. Vacio = comportamiento original de un solo robot.
    # Se propaga tal cual a los tres launches incluidos; cada uno sabe que con
    # cadena vacia no debe namespacear ni prefijar marcos.
    ns_cfg = LaunchConfiguration('namespace')

    declare_world_arg = DeclareLaunchArgument('world', default_value=default_world, description='SDF world file')
    declare_map_arg = DeclareLaunchArgument('map', default_value=default_map, description='map file')
    declare_params_arg = DeclareLaunchArgument('params', default_value=nav_params, description='params file')
    declare_ns_arg = DeclareLaunchArgument(
        'namespace', default_value='',
        description="Namespace del robot, p.ej. 'robot1'. Vacio = un solo robot.")

    include_files = GroupAction([
        # start deepracer simulation
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([deepracer_bringup_dir, '/launch/deepracer_sim.launch.py']),
            launch_arguments = {'world': world_cfg,
                                'namespace': ns_cfg}.items()
         ),
        # start navigation planner and controller
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([deepracer_bringup_dir, '/launch/deepracer_navigation_sim.launch.py']),
            launch_arguments = {'params': params_cfg,
                                'namespace': ns_cfg,
                                'use_sim_time': 'true'}.items()
        ),
        # start localization (amcl) and map_server
        #
        # Se usa el launch propio y NO nav2_bringup/localization_launch.py: aquel
        # no namespacea sus nodos (solo anida el YAML) y remapea /tf de forma
        # fija, lo que parte el arbol TF bajo un namespace. El motivo largo esta
        # en la cabecera de deepracer_localization_sim.launch.py.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([deepracer_bringup_dir, '/launch/deepracer_localization_sim.launch.py']),
            launch_arguments={'map': map_cfg,
                              'params': params_cfg,
                              'namespace': ns_cfg,
                              'use_sim_time': 'true'}.items()),
    ])

    ld = LaunchDescription()
    ld.add_action(declare_world_arg)
    ld.add_action(declare_map_arg)
    ld.add_action(declare_params_arg)
    ld.add_action(declare_ns_arg)
    ld.add_action(include_files)

    return ld
