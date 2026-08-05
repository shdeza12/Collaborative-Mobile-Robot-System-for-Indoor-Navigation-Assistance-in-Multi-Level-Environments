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

from launch import LaunchDescription
import launch.actions
import launch_ros.actions
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')
    use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time',
                                                            default='true')
    autostart = launch.substitutions.LaunchConfiguration('autostart')
    params_file = launch.substitutions.LaunchConfiguration('params')
    nav_to_pose_bt_xml = launch.substitutions.LaunchConfiguration(
        'nav_to_pose_bt_xml')
    nav_through_poses_bt_xml = launch.substitutions.LaunchConfiguration(
        'nav_through_poses_bt_xml')

    remappings = []

    # Create our own temporary YAML files that include substitutions
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'default_nav_to_pose_bt_xml': nav_to_pose_bt_xml,
        'default_nav_through_poses_bt_xml': nav_through_poses_bt_xml,
        'autostart': autostart,
    }

    lifecycle_nodes = ['controller_server',
                       'planner_server',
                       'behavior_server',
                       'bt_navigator',
                       'waypoint_follower']

    configured_params = RewrittenYaml(
        source_file=params_file,
        param_rewrites=param_substitutions,
        convert_types=True)

    return LaunchDescription([
        # Set env var to print messages to stdout immediately
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        launch.actions.DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        launch.actions.DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically startup the nav2 stack'),

        launch.actions.DeclareLaunchArgument(
            'params',
            default_value=[deepracer_bringup_dir,
                           '/config/nav2_params.yaml'],
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

        launch_ros.actions.Node(
            package='nav2_controller',
            executable='controller_server',
            output='screen',
            parameters=[configured_params],
            remappings=remappings),

        launch_ros.actions.Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params],
            remappings=remappings),


        launch_ros.actions.Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[configured_params],
            remappings=remappings),

        launch_ros.actions.Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params],
            remappings=remappings),

        launch_ros.actions.Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params],
            remappings=remappings),

        launch_ros.actions.Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': lifecycle_nodes}]),

    ])
