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

USO
---
En el vehiculo, con deepracer-core ya corriendo sin LiDAR:

    ros2 launch deepracer_bringup lidar_vehiculo.launch.py

Comprobar que publica de verdad, y no solo que el topico aparece en la lista
-que no significa nada, ver §2 del informe del 21-ago-:

    ros2 topic info /scan --verbose
    ros2 topic hz /scan
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port', default_value='/dev/ttyUSB0',
            description='Puerto del puente USB-serie CP210x del sensor'),
        DeclareLaunchArgument(
            'frame_id', default_value='laser',
            description='Marco del sensor; el URDF del vehiculo lo llama asi'),

        Node(
            # 'rplidar_ros' y 'rplidar_composition' son los nombres que existen
            # de verdad en la tarjeta (Jazzy). No 'rplidar_ros2' ni
            # 'rplidar_scan_publisher', que es lo que pedia deepracer.launch.py
            # y no existe ahi, ni 'rplidar_node', que es lo que pide AWS y
            # tampoco.
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_composition',
            # SIN espacio de nombres, a proposito: asi publica en '/scan', que
            # es donde miran Nav2 y slam_toolbox. Bajo 'rplidar_ros' publicaria
            # en '/rplidar_ros/scan' y haria falta un remapeo, que es
            # exactamente el punto 6 del backlog del spike de S19.
            namespace='',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'serial_baudrate': 115200,
                'frame_id': LaunchConfiguration('frame_id'),
                'inverted': False,
                'angle_compensate': True,
            }],
        ),
    ])
