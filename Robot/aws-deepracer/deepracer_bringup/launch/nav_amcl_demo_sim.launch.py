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

def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')

    # Los mundos y modelos SDF viven en la raiz del repositorio, fuera del paquete.
    # Se puede sobreescribir con la variable de entorno TESIS_WORLDS_DIR o con world:=<ruta>.
    #
    # El candidato principal se DEDUCE de la ubicacion real de este archivo, no de una
    # ruta fija ni del $HOME. Con `colcon build --symlink-install` el launch instalado
    # es un enlace al del repositorio, asi que realpath() cae en
    #   <repo>/Robot/aws-deepracer/deepracer_bringup/launch/
    # y subiendo cuatro niveles se obtiene la raiz de ESE clon. Es la unica forma de
    # garantizar que los mundos que se cargan salen del mismo checkout que el codigo
    # que se ejecuta.
    #
    # Antes habia una ruta fija ('~/Documents/Tesis'). Eso fallaba de dos maneras: en
    # un equipo que clonara en otro sitio, el launch entregaba a Gazebo la ruta de un
    # .world inexistente y el simulador abria un mundo VACIO sin mensaje de error; y
    # si por casualidad existia otra copia del repositorio en la ruta adivinada, se
    # cargaban en silencio los mundos de la copia equivocada.
    _raiz_repo = os.path.abspath(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..'))
    _candidatos = [os.environ['TESIS_WORLDS_DIR']] if os.environ.get('TESIS_WORLDS_DIR') else [
        _raiz_repo,
        os.path.join(os.path.expanduser('~'), 'Documents', 'Tesis'),
        os.path.join(os.path.expanduser('~'), 'Tesis'),
    ]
    worlds_dir = next(
        (d for d in _candidatos if os.path.isfile(os.path.join(d, 'primer_piso.world'))),
        None)
    if worlds_dir is None:
        # Si el usuario pasa world:= explicitamente, el valor por defecto no se usa
        # y no hay motivo para abortar.
        if not any(a.startswith('world:=') for a in sys.argv):
            raise RuntimeError(
                'No se encontro primer_piso.world. Se busco en: '
                + ', '.join(_candidatos)
                + '. Exportar TESIS_WORLDS_DIR con la raiz del repositorio, '
                  'o pasar world:=<ruta absoluta al .world>.')
        worlds_dir = _candidatos[0]
    default_world = os.path.join(worlds_dir, 'primer_piso.world')
    default_map = os.path.join(deepracer_bringup_dir, 'maps', 'primer_piso.yaml')
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
