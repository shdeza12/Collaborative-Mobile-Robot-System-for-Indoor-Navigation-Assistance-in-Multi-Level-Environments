# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
"""Arranca el LiDAR de fabrica del kit Evo en el vehiculo fisico.

POR QUE ESTE ARCHIVO EXISTE, EN VEZ DE PARCHEAR EL SOFTWARE DE AWS
------------------------------------------------------------------
Con el LiDAR conectado, 'deepracer-core' se queda en 'failed' y el vehiculo se
queda SIN NINGUN NODO DE CONTROL. La causa esta medida el 2026-08-21
(Documentos/Evidencia/S19_lidar_original_evo.md): su lanzador invoca el
ejecutable 'rplidar_node', y en '/opt/ros/jazzy/lib/rplidar_ros/' lo unico que
hay es 'rplidar_composition'. El binario esta instalado y funciona; lo que no
existe es el nombre que el launch llama.

Habia dos formas de arreglarlo y NO son equivalentes:

  A. Enlazar 'rplidar_node' -> 'rplidar_composition' en /opt/ros/jazzy, o editar
     el launch bajo /opt/aws/deepracer/. Las dos MODIFICAN FICHEROS DEL SISTEMA
     en hardware compartido, y la segunda no sobrevive a una actualizacion del
     software de AWS. Ademas el sensor queda bajo el espacio de nombres de AWS,
     publicando en '/rplidar_ros/scan', que no es donde Nav2 ni slam_toolbox
     miran, asi que hace falta ademas un remapeo.

  B. Dejar que 'deepracer-core' arranque SIN el LiDAR -su lanzador ya acepta
     'rplidar:=False'- y arrancar el sensor nosotros, con el nombre correcto.
     No se toca nada del sistema, sobrevive a las actualizaciones, y el sensor
     publica directamente en '/scan'.

Se elige B, y este archivo es la B. El servicio deepracer-core queda sano -que
es de donde sale el mando de los servos- y el LiDAR queda en un proceso aparte
que se puede parar y arrancar sin tumbar el control del vehiculo.

LOS PARAMETROS NO SON INVENTADOS
--------------------------------
Son los de la orden que ya se ejecuto a mano sobre el vehiculo el 2026-08-21 y
que arranco el sensor a la primera. El propio RPLIDAR declaro entonces
'Hardware Rev: 5' y 12,0 m de alcance, que es el A1M8-R5 de fabrica del Evo, y
publico 360 muestras sobre 360 grados a 6,80 Hz.

ESPACIO DE NOMBRES: POR QUE SE ANADIO EL 2026-09-08
---------------------------------------------------
Hasta hoy el nodo llevaba 'namespace=' escrito en el codigo, con el argumento
-correcto para UN vehiculo- de que asi publica en '/scan', que es donde miran
Nav2 y slam_toolbox. Con DOS vehiculos en el dominio 0 eso deja de valer: los
dos publicarian en '/scan' y no serian direccionables por separado, que es
justo lo que exige RF-02. Y RF-12 pide literalmente '/<ns>/scan'.

El defecto por defecto NO cambia: sin argumento, el nodo sigue sin espacio de
nombres y sigue publicando en '/scan'.

El marco del sensor se prefija junto con el topico, y no es un adorno. La
simulacion lleva desde el 2026-08-24 prefijando TODOS los marcos
(Evidencia/S20_marco_map_prefijado.md, y el comentario largo de
deepracer_navigation_sim.launch.py): es lo que permite que dos robots
compartan el topico '/tf' sin compartir el arbol. Dejar el marco en 'laser'
mientras el topico pasa a '/robot1/scan' daria una separacion aparente -los
topicos no chocan- con los dos arboles TF pisandose por el nombre del marco.

Medido en el vehiculo el 2026-09-08, y por eso el cambio es seguro hoy: la
tarjeta NO publica ningun arbol TF. 'ros2 topic echo /tf' y '/tf_static'
responden 'does not appear to be published yet', y entre los 9 nodos de
deepracer-core no hay 'robot_state_publisher'. Es decir que no hay nada que
romper, y tampoco hay nada sobre lo que Nav2 pueda correr todavia: eso es la
segunda mitad pendiente de RF-12 y se trata aparte.

USO: POR RUTA, PORQUE EN LA TARJETA NO HAY WORKSPACE
----------------------------------------------------
Comprobado el 2026-09-07 (Documentos/PLAN_S22.md §5.2): la tarjeta NO tiene
ningun workspace del proyecto. Solo existe '~/tesis_ws/', creado ese dia, y
dentro unicamente 'coordinacion_msgs' y un YAML. 'deepracer_bringup' NUNCA ha
estado alli, asi que invocarlo por paquete falla con
'Package deepracer_bringup not found'. Paso el 2026-09-08 y costo el arranque
de una salida de campo.

Este fichero se copia suelto y se invoca por ruta. Funciona porque no depende
de su paquete: importa solo 'launch' y 'launch_ros' -los dos en /opt/ros/jazzy-
y no llama a 'get_package_share_directory'.

    scp .../launch/lidar_vehiculo.launch.py deepracer@<IP>:~/

En el vehiculo, con deepracer-core ya corriendo sin LiDAR:

    ros2 launch ~/lidar_vehiculo.launch.py
    ros2 launch ~/lidar_vehiculo.launch.py namespace:=robot1

Sin haberlo copiado, el equivalente exacto -mismos cinco parametros, sin
espacio de nombres- es:

    ros2 run rplidar_ros rplidar_composition --ros-args
        -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=115200
        -p frame_id:=laser -p inverted:=false -p angle_compensate:=true

En simulacion, o en un equipo donde el paquete SI este construido, la forma por
paquete sigue valiendo:

    ros2 launch deepracer_bringup lidar_vehiculo.launch.py

Comprobar que publica de verdad, y no solo que el topico aparece en la lista
-que no significa nada, ver §2 del informe del 21-ago-:

    ros2 topic info /scan --verbose
    ros2 topic hz /scan
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def resolver_espacio(namespace, frame_id):
    """Traduce el argumento 'namespace' a lo que necesita launch_ros.

    Devuelve (ns_nodo, frame_id). Esta fuera de 'acciones' para que la prueba
    pueda llamarla sin montar un LaunchContext.

    Dos detalles que no son obvios:

      - launch_ros distingue None -sin espacio de nombres- de la cadena vacia,
        que traduce a '__ns:=/' y NO es lo mismo. Mismo criterio que
        deepracer_localization_sim.launch.py:83.
      - un 'frame_id' explicito manda: si alguien lo pasa a mano se respeta tal
        cual, prefijado o no. El prefijado automatico es solo el defecto.
    """
    ns = namespace.strip('/')
    ns_nodo = ns if ns else None
    if frame_id:
        return ns_nodo, frame_id
    return ns_nodo, f'{ns}/laser' if ns else 'laser'


def acciones(context, *args, **kwargs):
    ns_nodo, frame_id = resolver_espacio(
        LaunchConfiguration('namespace').perform(context),
        LaunchConfiguration('frame_id').perform(context).strip(),
    )

    return [Node(
            # 'rplidar_ros' y 'rplidar_composition' son los nombres que existen
            # de verdad en la tarjeta (Jazzy). No 'rplidar_ros2' ni
            # 'rplidar_scan_publisher', que es lo que pedia deepracer.launch.py
            # y no existe ahi, ni 'rplidar_node', que es lo que pide AWS y
            # tampoco.
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_composition',
            # Sin argumento esto es None y el sensor publica en '/scan', que es
            # donde miran Nav2 y slam_toolbox con un solo vehiculo. Con
            # 'namespace:=robot1' pasa a '/robot1/scan', que es lo que pide
            # RF-12. Lo que NO se hace nunca es dejarlo bajo el espacio de AWS
            # ('/rplidar_ros/scan'), que obligaria a un remapeo: ese es el punto
            # 6 del backlog del spike de S19.
            namespace=ns_nodo,
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'serial_baudrate': 115200,
                'frame_id': frame_id,
                'inverted': False,
                'angle_compensate': True,
            }],
        )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port', default_value='/dev/ttyUSB0',
            description='Puerto del puente USB-serie CP210x del sensor'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Espacio de nombres del vehiculo (robot1, robot2). '
                        'Vacio deja el sensor en /scan, como hasta el 2026-09-08'),
        DeclareLaunchArgument(
            'frame_id', default_value='',
            description='Marco del sensor. Vacio lo deriva del namespace: '
                        "'laser' sin namespace, '<ns>/laser' con el"),
        OpaqueFunction(function=acciones),
    ])
