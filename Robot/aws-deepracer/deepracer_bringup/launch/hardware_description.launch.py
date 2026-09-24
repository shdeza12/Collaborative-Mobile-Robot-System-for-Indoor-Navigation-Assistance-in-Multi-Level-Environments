"""Publica la TF del vehiculo REAL a partir de `deepracer_hardware.urdf`.

Para que sirve
--------------
Sostener `base_link -> laser` en el vehiculo real de forma reproducible y
versionada. El peldano 1 de la escalera de Nav2 ya se cerro el 2026-09-21
(`Documentos/Evidencia/S24_tf_hardware_peldano_1.md`), pero se cerro con un URDF
generado a mano del xacro de simulacion, copiado a las dos tarjetas y **nunca
versionado**: si se pierde el archivo hay que acordarse de la linea de `xacro`
que lo produjo. Esto lo fija en el repositorio. Cubre eso y nada mas: no arranca
el driver del LiDAR ni la odometria.

Por que un launch y no `ros2 run ... -p robot_description:=...`
---------------------------------------------------------------
Porque el valor de un `-p` se interpreta como **YAML**. Cualquier `algo: algo` o
` #` dentro del archivo abre un mapa o un comentario y el nodo aborta con
`Couldn't parse parameter override rule`. No es culpa del XML multilinea —un
URDF sin comentarios pasa sin problema, y por eso el metodo del 21-sep
funcionaba—, es culpa de los comentarios en castellano que lleva dentro
`deepracer_hardware.urdf`. Aislado por biseccion el 2026-09-24. El launch lee el
archivo en Python y entrega el texto ya tipado, asi que el problema desaparece y
los comentarios se conservan.

Uso
---
En el portatil, con el workspace compilado::

    ros2 launch deepracer_bringup hardware_description.launch.py

En la tarjeta, donde este paquete NO esta compilado, copiando los dos archivos
sueltos y apuntando al URDF por ruta absoluta::

    ros2 launch /tmp/hardware_description.launch.py urdf:=/tmp/deepracer_hardware.urdf

El argumento `urdf` existe justamente para ese segundo caso: sin el habria que
instalar `deepracer_description` a bordo, que arrastra `gazebo_ros_pkgs` y no
tiene sentido en hardware.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _urdf_por_defecto():
    """Ruta del URDF dentro del paquete, o cadena vacia si no esta instalado.

    En la tarjeta `deepracer_description` no existe y `get_package_share_directory`
    lanza excepcion. Si esa excepcion subiera, el launch no se podria ni construir
    aunque el usuario pasara `urdf:=...`, porque el valor por defecto se evalua
    siempre. Por eso se atrapa y se deja vacio: el fallo se reporta despues, con
    un mensaje que se entiende.
    """
    try:
        return os.path.join(
            get_package_share_directory('deepracer_description'),
            'models', 'urdf', 'deepracer_hardware.urdf')
    except Exception:
        return ''


def _lanzar(context, *args, **kwargs):
    ruta = LaunchConfiguration('urdf').perform(context)
    if not ruta:
        raise RuntimeError(
            'No se encontro el paquete deepracer_description y no se indico '
            'otra ruta. Pase urdf:=/ruta/a/deepracer_hardware.urdf')
    if not os.path.isfile(ruta):
        raise RuntimeError('El URDF no existe: %s' % ruta)
    with open(ruta, 'r') as archivo:
        descripcion = archivo.read()

    return [Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        # use_sim_time en falso: esto corre contra el reloj del vehiculo.
        # Al reproducir un bag con --clock hay que pasarlo en verdadero.
        parameters=[{'robot_description': descripcion,
                     'use_sim_time': LaunchConfiguration('use_sim_time')}],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'urdf', default_value=_urdf_por_defecto(),
            description='Ruta del URDF de hardware. Necesaria en la tarjeta, '
                        'donde deepracer_description no esta instalado.'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Verdadero solo al reproducir un bag con --clock.'),
        OpaqueFunction(function=_lanzar),
    ])
