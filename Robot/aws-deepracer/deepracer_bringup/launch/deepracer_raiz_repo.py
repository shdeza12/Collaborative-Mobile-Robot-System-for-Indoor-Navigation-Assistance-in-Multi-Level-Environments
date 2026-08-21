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
