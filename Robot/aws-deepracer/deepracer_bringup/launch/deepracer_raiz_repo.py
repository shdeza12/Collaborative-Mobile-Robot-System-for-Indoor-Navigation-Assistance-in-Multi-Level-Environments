"""Deduce la raiz del repositorio a partir de la ubicacion real de este archivo.

Para que existe: los mundos y los modelos SDF viven en la raiz del repositorio,
FUERA del paquete ROS, asi que ningun launch puede encontrarlos con
get_package_share_directory. Antes cada launch resolvia eso a su manera -o no lo
resolvia y exigia escribir la ruta absoluta a mano-, y las dos formas del error
eran silenciosas:

  - Ruta fija ('~/Documents/Tesis'): en un equipo que clonara en otro sitio, el
    launch entregaba a Gazebo la ruta de un .world inexistente y el simulador
    abria un mundo VACIO, sin mensaje de error y con codigo de salida 0.
  - Ruta escrita a mano en cada lanzamiento: si existe otra copia del repositorio
    en el equipo -y suele existir-, basta una tecla para mapear contra la
    geometria de un clon distinto del que se esta ejecutando.

Como funciona: con 'colcon build --symlink-install' el archivo instalado bajo
install/.../share/deepracer_bringup/launch/ es un ENLACE al del repositorio, de
modo que os.path.realpath(__file__) cae en

    <repo>/Robot/aws-deepracer/deepracer_bringup/launch/

y subiendo cuatro niveles se llega a la raiz de ESE clon. Es la unica forma de
garantizar que los mundos que se cargan salen del mismo checkout que el codigo
que los carga.

Se puede sobreescribir con la variable de entorno TESIS_WORLDS_DIR (util para
apuntar a otro checkout) o, en cada lanzamiento, con world:=<ruta>.

No hay candidatos de respaldo bajo $HOME: adivinar rutas es justamente lo que
hacia que se cargaran en silencio los mundos de otro clon. Si la raiz deducida no
contiene el mundo, el fallo debe ser ruidoso.
"""

import os
import sys

# El mundo vigente, el mismo que declara el README. Sirve de testigo para
# confirmar que la carpeta deducida es de verdad la raiz del repositorio.
# 'herramientas/verificar_repositorio.sh' comprueba que este nombre y el del
# README sigan siendo el mismo.
MUNDO_VIGENTE = 'mundo_definitivo.world'

# Donde nace cada robot en el mundo vigente. ESTA ES LA UNICA TABLA DE POSES DEL
# PROYECTO: la leen los launch y 'herramientas/robot.sh'.
#
# Por que esta aqui y no en cada launch. Hasta el 2026-08-22 la pose vivia en
# tres sitios que no se hablaban: la tabla de robot.sh, los defectos de
# deepracer_sim.launch.py y los de nav_amcl_demo_sim.launch.py. Al pasar de
# 'primer_piso_v2.world' a 'mundo_definitivo.world' se actualizaron dos de los
# tres, y el que se quedo viejo -nav_amcl, en (0, 0)- hacia nacer al vehiculo en
# la explanada vacia ENTRE los dos pasillos. El fallo no es ruidoso: Gazebo abre,
# el vehiculo aparece y los siete controladores quedan activos; lo que no hay es
# pasillo alrededor, y (0, 0) ni siquiera es una celda del mapa, de modo que AMCL
# arranca sin geometria contra la que localizar.
#
# Las poses estan MEDIDAS sobre el SDF de mundo_Definitivo y comprobadas con el
# LiDAR: el ancho de pasillo medido concuerda con el del modelo dentro de 56 mm.
# 'herramientas/verificar_pose_spawn.py' comprueba en cada corte que cada una
# sigue cayendo en celda libre de su mapa y con holgura suficiente.
#
# 'mapa' es el par del nivel: mundo y mapa van juntos, y localizar contra el mapa
# del otro nivel converge SIN dar error contra la geometria equivocada. 'None'
# significa que ese nivel todavia no tiene mapa generado.
POSE_INICIAL = {
    'robot1': {
        'x': -19.165, 'y': 7.292, 'z': 0.03, 'yaw': 1.5708,   # tramo norte-sur
        'nivel': 1, 'mapa': 'mundo_definitivo_piso1.yaml',
    },
    'robot2': {
        'x': -21.889, 'y': -8.379, 'z': 0.03, 'yaw': 0.0,     # canal oeste
        'nivel': 2, 'mapa': None,
    },
}

# Con 'namespace' vacio -un solo robot- se usa esta fila. Es la que ven los
# launch cuando nadie pasa x:=/y:=/yaw:=.
ROBOT_POR_DEFECTO = 'robot1'


def pose_por_defecto(robot=ROBOT_POR_DEFECTO):
    """Fila de POSE_INICIAL de un robot. Falla ruidosamente si no existe."""
    if robot not in POSE_INICIAL:
        raise KeyError(
            "No hay pose para '{}'. Conocidos: {}. Anadirlo a POSE_INICIAL en "
            'este archivo, nunca en el launch.'.format(
                robot, ', '.join(sorted(POSE_INICIAL))))
    return POSE_INICIAL[robot]


def pose_texto(clave, robot=ROBOT_POR_DEFECTO):
    """Un componente de la pose como cadena, que es lo que exige
    DeclareLaunchArgument: no acepta numeros."""
    return str(pose_por_defecto(robot)[clave])


def raiz_repositorio():
    """Carpeta raiz del repositorio, o None si no se pudo confirmar."""
    deducida = os.path.abspath(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..'))
    candidatos = [os.environ['TESIS_WORLDS_DIR']] if os.environ.get('TESIS_WORLDS_DIR') \
        else [deducida]
    return next(
        (d for d in candidatos if os.path.isfile(os.path.join(d, MUNDO_VIGENTE))),
        None)


def mundo_por_defecto(nombre=MUNDO_VIGENTE):
    """Ruta absoluta al mundo por defecto.

    Aborta con un mensaje accionable si no se encuentra, SALVO que quien lanza
    haya pasado world:= explicitamente: en ese caso el valor por defecto no se
    usa y no hay motivo para impedir el lanzamiento.
    """
    raiz = raiz_repositorio()
    if raiz is None:
        if not any(a.startswith('world:=') for a in sys.argv):
            raise RuntimeError(
                'No se encontro {} en la raiz deducida del repositorio. '
                'Exportar TESIS_WORLDS_DIR con la raiz del repositorio, '
                'o pasar world:=<ruta absoluta al mundo>.'.format(nombre))
        raiz = os.path.abspath(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..'))
    return os.path.join(raiz, nombre)
