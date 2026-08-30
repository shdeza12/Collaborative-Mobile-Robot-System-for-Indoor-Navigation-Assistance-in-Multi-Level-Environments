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
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                            IncludeLaunchDescription, OpaqueFunction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

# El modulo vive junto a este archivo, dentro del propio paquete instalado.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from deepracer_raiz_repo import mundo_por_defecto, pose_texto  # noqa: E402

# Plugins de sistema que 'gzserver.launch.py' carga por defecto. Se repiten aqui
# porque este archivo ya no lo incluye; el porque esta en 'servidor_gazebo'.
# Van pegados al '-s' a proposito: es como los escribe el launch original, y
# gzserver los acepta asi.
PLUGINS_SISTEMA = [
    '-slibgazebo_ros_init.so',
    '-slibgazebo_ros_factory.so',
    '-slibgazebo_ros_force_system.so',
]


def servidor_gazebo(context, *args, **kwargs):
    """Arranca gzserver a mano, en vez de incluir 'gzserver.launch.py'.

    NO ES POR GUSTO, y conviene que quede escrito porque el include era mas
    corto. Aquel launch mete todos los argumentos extra en UN solo elemento de
    su lista 'cmd' -'extra_gazebo_args'-, asi que todo lo que se le pase llega
    a gzserver como UN argumento. Consecuencias medidas el 2026-08-30
    (Evidencia/S21_bloqueo_dominios.md §6.2):

      - '--remap __ns:=/robot1' necesita dos tokens. Como llega pegado en uno,
        Gazebo lo DESCARTA EN SILENCIO y el nodo se queda en '/gazebo'. Sin
        error, sin aviso, sin nada. Es la escritura que sale sola por analogia
        con la linea de comando, y es la que no funciona.
      - '__ns:=/robot1' -regla desnuda- si cabe en un token y si funciona.
      - Pero es UN token: solo cabe UNA regla. robot1 necesita una y robot2
        necesita dos ('__ns:=' y '/clock:='), asi que por ahi no pasa.
      - Y la forma que de verdad hay que escribir es aun mas larga:
        '--ros-args --remap __ns:=/robot1' son tres tokens. Ni de lejos.

    Con la lista construida aqui, cada remapeo es un elemento propio y el
    problema desaparece de raiz.

    El entorno sale de GazeboRosPaths, igual que en el launch original. No es
    prescindible: de ahi salen las rutas de los plugins de gazebo_ros Y la del
    'deepracer_drive_plugin', que vive en el workspace. Sin eso el vehiculo
    nace sin traccion.
    """
    ns = LaunchConfiguration('namespace').perform(context).strip('/')
    reloj = LaunchConfiguration('clock_topic').perform(context).strip()

    orden = ['gzserver', LaunchConfiguration('world').perform(context)]
    orden += PLUGINS_SISTEMA
    orden += ['--physics', 'ode']

    # Los remapeos se juntan y se anaden AL FINAL, detras de un unico
    # '--ros-args'. Sin namespace la lista queda vacia y la orden es identica a
    # la de siempre: un solo robot no necesita ni un argumento de mas.
    remapeos = []

    if ns:
        remapeos.append(f'__ns:=/{ns}')
    # El namespace NO arrastra a '/clock': 'gazebo_ros_init' lo publica con
    # nombre absoluto (§4.2 de la evidencia). Son dos remapeos independientes
    # y por motivos independientes, y hay que pedirlos por separado.
    #
    # El defecto es '/clock' -sin remapeo- a proposito. El diseno es ASIMETRICO
    # porque 'ros2 bag record --use-sim-time' esta cableado a '/clock' y no
    # acepta '--ros-args': si se remapean los DOS relojes, el grabador escribe
    # un bag con cero mensajes y no avisa (§5.1). Alguien tiene que quedarse en
    # '/clock' y ser el reloj de referencia de la mision.
    if reloj and reloj != '/clock':
        remapeos.append(f'/clock:={reloj}')

    # '--ros-args' VA UNA SOLA VEZ Y AL FINAL, y no es cosmetica.
    #
    # La forma corta -'--remap __ns:=/robot2' suelto- tambien funciona en
    # Humble, y fue la primera que se uso. Pero el arranque dejaba esto en el
    # log, tres veces, una por regla:
    #
    #   [rcl]: Found remap rule '__ns:=/robot2'. This syntax is deprecated.
    #          Use '--ros-args --remap __ns:=/robot2' instead.
    #
    # Es decir: rcl la acepta por la via OBSOLETA. Eso no es un detalle de
    # estilo aqui, porque el carro fisico no corre Humble sino Jazzy, y una via
    # marcada como obsoleta es exactamente la que desaparece al cambiar de
    # distribucion. El fallo, ademas, seria del tipo mas caro: el remapeo
    # simplemente no se aplica, los dos robots vuelven a '/gazebo' y a '/clock'
    # compartido, y nada da error.
    #
    # Se comprobo que gzserver acepta la forma moderna -un gzserver de prueba
    # con '--ros-args --remap __ns:=/prueba --remap /clock:=/prueba/clock' dejo
    # el nodo en '/prueba/gazebo', publico '/prueba/clock' y no imprimio un solo
    # aviso- antes de escribirla aqui.
    #
    # Tiene que ir al final porque todo lo que siga a '--ros-args' se lo queda
    # ROS: '--physics ode' detras de esta linea no llegaria nunca a Gazebo.
    if remapeos:
        orden += ['--ros-args']
        for regla in remapeos:
            orden += ['--remap', regla]

    # 'scripts' es el modulo de gazebo_ros que resuelve las rutas. Se importa
    # por ruta explicita porque este archivo no vive en aquel paquete.
    sys.path.insert(
        0, os.path.join(get_package_share_directory('gazebo_ros'), 'launch'))
    from scripts import GazeboRosPaths
    modelos, plugins, medios = GazeboRosPaths.get_paths()
    if 'GAZEBO_MODEL_PATH' in os.environ:
        modelos += os.pathsep + os.environ['GAZEBO_MODEL_PATH']
    if 'GAZEBO_PLUGIN_PATH' in os.environ:
        plugins += os.pathsep + os.environ['GAZEBO_PLUGIN_PATH']
    if 'GAZEBO_RESOURCE_PATH' in os.environ:
        medios += os.pathsep + os.environ['GAZEBO_RESOURCE_PATH']

    return [ExecuteProcess(
        cmd=orden,
        output='both',
        shell=False,
        additional_env={'GAZEBO_MODEL_PATH': modelos,
                        'GAZEBO_PLUGIN_PATH': plugins,
                        'GAZEBO_RESOURCE_PATH': medios})]


def generate_launch_description():
    deepracer_bringup_dir = get_package_share_directory('deepracer_bringup')

    # ros gazebo launcher
    gazebo_dir = get_package_share_directory('gazebo_ros')

    gazebo_server_launcher = OpaqueFunction(function=servidor_gazebo)
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
        # A que topico publica el reloj ESTE simulador. Con dos gzserver en el
        # mismo dominio, dos relojes en '/clock' se pisan y la medida no vale.
        #
        # El defecto es '/clock' y el diseno es ASIMETRICO: uno de los dos
        # robots se queda en '/clock' y hace de reloj de referencia de la
        # mision. No es estetica, lo obliga el grabador: 'ros2 bag record
        # --use-sim-time' esta cableado a '/clock' y ni siquiera acepta
        # '--ros-args', asi que si se remapean los dos relojes el bag sale con
        # cero mensajes y sin un error visible (Evidencia/S21 §5.1).
        DeclareLaunchArgument(
            name='clock_topic',
            default_value='/clock',
            description='Topico de reloj de este gzserver. Con dos '
                        'simuladores, uno se queda en /clock -el de '
                        "referencia- y el otro usa '/robotN/clock'."
        ),
        # La pose por defecto NO se escribe aqui: sale de POSE_INICIAL, en
        # 'deepracer_raiz_repo.py', que es la unica tabla de poses del proyecto.
        # El porque esta en la cabecera de aquel archivo; en resumen, esta pose
        # vivio en tres sitios a la vez, uno se quedo viejo al cambiar de mundo y
        # el vehiculo nacio fuera del pasillo sin que nada diera error.
        # 'herramientas/verificar_pose_spawn.py' comprueba que siga siendo celda
        # libre del mapa y prohibe volver a escribir un numero en esta linea.
        DeclareLaunchArgument(name='x', default_value=pose_texto('x')),
        DeclareLaunchArgument(name='y', default_value=pose_texto('y')),
        DeclareLaunchArgument(name='z', default_value=pose_texto('z')),
        DeclareLaunchArgument(name='yaw', default_value=pose_texto('yaw')),
        gazebo_server_launcher,
        gazebo_client_launcher,
        spawn_deepracer
    ])


if __name__ == '__main__':
    generate_launch_description()
