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
#   - Argumento 'namespace': con valor vacio (por defecto) el lanzamiento es
#     identico al original; con 'robot1' todo cuelga de /robot1.
#   - Argumentos x/y/z/yaw: dos robots no pueden nacer en el mismo punto.
#   - Se elimino el static_transform_publisher base_link -> camera_link, que
#     disputaba ese marco con el URDF (ver Documentos/Evidencia/S17_linea_base.md).
#
# Se usa OpaqueFunction porque el namespace hay que componerlo como texto
# ('/robot1/controller_manager') y con namespace vacio hay que OMITIR partes,
# no concatenar cadenas vacias: '//controller_manager' no es un nombre valido.
# Las sustituciones de launch no saben omitir; Python si.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                            OpaqueFunction, RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node

# El broadcaster va primero y aparte: los seis controladores de articulacion
# solo se cargan cuando el ya esta activo.
BROADCASTER = 'joint_state_broadcaster'

CONTROLADORES = [
    'left_rear_wheel_velocity_controller',
    'right_rear_wheel_velocity_controller',
    'left_front_wheel_velocity_controller',
    'right_front_wheel_velocity_controller',
    'left_steering_hinge_position_controller',
    'right_steering_hinge_position_controller',
]


# Espera del cliente por cada respuesta del controller_manager, en segundos.
# El defecto que arregla esto es un REINTENTO SOBRE UNA OPERACION QUE NO ES
# IDEMPOTENTE: 'controller_manager/controller_manager_services.py' espera
# 'call_timeout' -10 s por defecto- y, si no hay respuesta, repite la MISMA
# peticion hasta tres veces. Si la primera llego y solo tardo, la segunda
# recibe "was already loaded" y el cliente aborta con codigo 1 ANTES de
# configurar y activar. El controlador queda CARGADO -por eso sigue saliendo
# en la lista- pero en 'unconfigured'.
#
# Con dos Gazebo y dos pilas Nav2 en la misma maquina, el controller_manager
# tarda mas de 10 s en contestar cada cierto arranque, y entonces se pierde una
# activacion. Medido: 2 fallos de 8 arranques dobles.
#
# 60 s no es un numero magico: es "muy por encima del peor caso observado".
# Si algun dia el controller_manager tarda mas que esto, el sintoma vuelve.
ESPERA_SERVICIO_S = '60.0'


def cargar_controladores(nombres, namespace):
    """Un solo 'spawner' para toda la lista, en vez de un proceso por controlador.

    Se cambio de 'ros2 control load_controller' a 'controller_manager spawner'
    por una razon y no por estilo: el CLI de 'ros2 control' NO expone el
    timeout de llamada -su --help solo ofrece --spin-time, que ademas solo
    aplica sin daemon-, asi que con el no hay forma de subir los 10 s que
    provocan el reintento. El spawner si: --service-call-timeout y
    --switch-timeout.

    De paso acepta la lista entera, con lo que seis procesos pasan a ser uno.
    Sin '-u' el spawner termina al acabar, que es lo que necesitan los
    OnProcessExit de abajo.
    """
    cmd = ['ros2', 'run', 'controller_manager', 'spawner', *nombres,
           '--service-call-timeout', ESPERA_SERVICIO_S,
           '--switch-timeout', ESPERA_SERVICIO_S]
    if namespace:
        cmd += ['-c', f'/{namespace}/controller_manager']
    return ExecuteProcess(cmd=cmd, output='screen')


def acciones(context, *args, **kwargs):
    ns = LaunchConfiguration('namespace').perform(context).strip('/')

    # launch_ros distingue None (sin namespace) de '' (que traduce a '__ns:=/').
    # Las dos apuntan a la raiz, pero solo None deja la orden de ejecucion
    # identica a la original. Con un solo robot no queremos ni un argumento de mas.
    ns_nodo = ns if ns else None

    descripcion_dir = get_package_share_directory('deepracer_description')
    modelo = os.path.join(descripcion_dir, 'models/xacro/deepracer/deepracer.xacro')

    # El prefijo de marcos lleva '/' final: 'robot1/base_link'. Es la convencion
    # de robot_state_publisher, que concatena sin separador.
    prefijo = f'{ns}/' if ns else ''

    # Con namespace vacio NO se pasan argumentos a xacro: 'frame_prefix:=' sin
    # valor no es un argumento valido, y ademas asi el URDF generado es
    # literalmente el mismo de siempre.
    #
    # frame_prefix lleva '/' final y robot_namespace no: el primero se concatena
    # con el nombre del marco ('robot1/base_link'), el segundo es un namespace
    # ROS 2 y la barra la pone el propio middleware.
    orden_xacro = ['xacro ', modelo]
    if ns:
        orden_xacro += [' frame_prefix:=', prefijo, ' robot_namespace:=', ns]

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=ns_nodo,
        parameters=[{
            'robot_description': Command(orden_xacro),
            # Prefija los marcos que declara el URDF (base_link, chassis, laser,
            # las ruedas...). Los que escriben los plugins de Gazebo no pasan por
            # aqui: esos se prefijan dentro del propio xacro.
            'frame_prefix': prefijo,
        }],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        namespace=ns_nodo,
        arguments=[
            # Nombre relativo: con namespace se resuelve a /robot1/robot_description.
            '-topic', 'robot_description',
            # Gazebo exige nombres de modelo unicos: dos 'deepracer' no coexisten.
            '-entity', ns if ns else 'deepracer',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
        ],
        output='screen',
    )

    cargar_broadcaster = cargar_controladores([BROADCASTER], ns)
    cargar_resto = [cargar_controladores(CONTROLADORES, ns)]

    return [
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[cargar_broadcaster],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=cargar_broadcaster,
                on_exit=cargar_resto,
            )
        ),
        robot_state_publisher,
        spawn_entity,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='',
            description="Namespace del robot, p.ej. 'robot1'. "
                        'Vacio = comportamiento original de un solo robot.'),
        DeclareLaunchArgument('x', default_value='0',
                              description='Posicion inicial X en metros'),
        DeclareLaunchArgument('y', default_value='0',
                              description='Posicion inicial Y en metros'),
        DeclareLaunchArgument('z', default_value='0.03',
                              description='Posicion inicial Z en metros'),
        DeclareLaunchArgument('yaw', default_value='0',
                              description='Orientacion inicial en radianes'),
        OpaqueFunction(function=acciones),
    ])
