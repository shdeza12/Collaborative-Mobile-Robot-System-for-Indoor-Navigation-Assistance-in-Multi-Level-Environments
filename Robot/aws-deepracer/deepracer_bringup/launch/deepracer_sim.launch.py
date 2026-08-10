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

from ament_index_python.packages import get_package_share_directory
import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

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
    gazebo_client_launcher = IncludeLaunchDescription(
        launch_description_source=PythonLaunchDescriptionSource(
            launch_file_path=gazebo_dir + '/launch/gzclient.launch.py'),
        launch_arguments={'verbose': 'false'}.items())

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

    return LaunchDescription([DeclareLaunchArgument(
          'world',
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
        DeclareLaunchArgument(name='x', default_value='0'),
        DeclareLaunchArgument(name='y', default_value='0'),
        DeclareLaunchArgument(name='z', default_value='0.03'),
        DeclareLaunchArgument(name='yaw', default_value='0'),
        gazebo_server_launcher,
        gazebo_client_launcher,
        spawn_deepracer
    ])


if __name__ == '__main__':
    generate_launch_description()
