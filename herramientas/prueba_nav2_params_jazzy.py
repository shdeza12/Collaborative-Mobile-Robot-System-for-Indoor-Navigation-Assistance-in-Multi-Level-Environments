#!/usr/bin/env python3
"""Los parametros de Nav2 para el vehiculo (Jazzy) no divergen de los de Humble.

POR QUE EXISTE
--------------
El vehiculo corre ROS 2 Jazzy y la simulacion Humble, y la configuracion de
Nav2 de Humble no arranca en Jazzy (Evidencia/S19_spike_p4_humble_jazzy.md §3).
Por eso hay dos archivos:

    config/nav2_params.yaml        Humble, la fuente, lo usa la simulacion
    config/nav2_params_jazzy.yaml  Jazzy, derivado, lo usa nav2_hardware.launch.py

Dos copias de una configuracion divergen en silencio: alguien retoca una
tolerancia en una y no en la otra, y una corrida da un resultado distinto segun
el vehiculo o el simulador. Esta prueba lo impide, y comprueba tres cosas:

  1. NO DIVERGENCIA. Se aplica al archivo de Humble la derivacion documentada
     —los seis cambios de distribucion, ni uno mas— y el resultado tiene que ser
     IGUAL, clave a clave, al archivo de Jazzy. Cualquier otra diferencia falla
     y se imprime con su ruta.
  2. CADA ARCHIVO HABLA SU DISTRIBUCION. Los nombres de plugin de cada archivo
     tienen que ser los que declara su distribucion: los de Humble se leen de
     los XML instalados en este equipo; los de Jazzy estan copiados de la rama
     jazzy de ros-navigation, comprobados el 2026-09-24. Esto es lo que la
     comprobacion 1 no ve: si la derivacion y el archivo estuvieran mal los dos
     de la misma forma, coincidirian.
  3. EL LANZADOR CARGA LA DE JAZZY, Y SUS AJUSTES DE HARDWARE SE APLICAN. Se
     ejecuta nav2_hardware.launch.py de verdad sobre un LaunchContext, se
     resuelve el YAML que recibiria el controller_server y se comprueba sobre
     ese YAML ya reescrito, no sobre el archivo.

Uso, desde la raiz del repositorio y con ROS sourceado (hace falta 'launch'):

    python3 herramientas/prueba_nav2_params_jazzy.py

Admite como argumento otra ruta para el archivo de Jazzy, que es como se
comprueba que la prueba no es vacia: con una copia estropeada tiene que fallar.
"""
import copy
import importlib.util
import pathlib
import sys
import xml.etree.ElementTree as ET

import yaml

RAIZ = pathlib.Path(__file__).resolve().parents[1]
BRINGUP = RAIZ / 'Robot/aws-deepracer/deepracer_bringup'
HUMBLE = BRINGUP / 'config/nav2_params.yaml'
JAZZY = BRINGUP / 'config/nav2_params_jazzy.yaml'
LAUNCH = BRINGUP / 'launch/nav2_hardware.launch.py'
URDF = RAIZ / 'Robot/aws-deepracer/deepracer_description/models/urdf/deepracer_hardware.urdf'

# Nombres de busqueda de pluginlib en Jazzy. Sin atributo 'name' en el XML, el
# nombre de busqueda es el 'type'. Fuente, rama jazzy de ros-navigation:
#   nav2_smac_planner/smac_plugin_hybrid.xml
#   nav2_behaviors/behavior_plugin.xml
PLUGINS_JAZZY = {
    'nav2_smac_planner::SmacPlannerHybrid',
    'nav2_behaviors::Spin',
    'nav2_behaviors::BackUp',
    'nav2_behaviors::Wait',
}

# Donde estan en Humble los XML equivalentes, instalados en este equipo.
XML_HUMBLE = [
    pathlib.Path('/opt/ros/humble/share/nav2_smac_planner/smac_plugin_hybrid.xml'),
    pathlib.Path('/opt/ros/humble/share/nav2_behaviors/behavior_plugin.xml'),
]

# Lo que nav2_hardware.launch.py tiene que reescribir sobre el archivo.
SUELO_VELOCIDAD = 0.40
TOPICO_SCAN = '/rplidar_ros/scan'


def cargar_yaml(ruta):
    with open(ruta) as archivo:
        return yaml.safe_load(archivo)


def derivar(humble):
    """Los seis cambios de distribucion, y ninguno mas.

    Es la especificacion de nav2_params_jazzy.yaml: si alguien cambia ese
    archivo por otra razon, deja de coincidir con esto y la prueba falla.
    """
    d = copy.deepcopy(humble)

    bt = d['bt_navigator']['ros__parameters']
    bt.pop('plugin_lib_names')                                   # 1
    for clave in ('enable_groot_monitoring', 'groot_zmq_publisher_port',
                  'groot_zmq_server_port'):                      # 2
        bt.pop(clave)

    cs = d['controller_server']['ros__parameters']
    cs['progress_checker_plugins'] = [cs.pop('progress_checker_plugin')]  # 3

    gb = d['planner_server']['ros__parameters']['GridBased']
    gb['plugin'] = gb['plugin'].replace('/', '::')              # 4

    bs = d['behavior_server']['ros__parameters']
    for ident in bs['behavior_plugins']:                         # 5
        bs[ident]['plugin'] = bs[ident]['plugin'].replace('/', '::')
    bs['local_costmap_topic'] = bs.pop('costmap_topic')          # 6
    bs['local_footprint_topic'] = bs.pop('footprint_topic')
    bs['local_frame'] = bs.pop('global_frame')
    bs['global_frame'] = 'map'
    return d


def diferencias(a, b, ruta=''):
    """Rutas de clave donde a y b no coinciden."""
    if isinstance(a, dict) and isinstance(b, dict):
        salida = []
        for clave in sorted(set(a) | set(b), key=str):
            sub = f'{ruta}.{clave}' if ruta else str(clave)
            if clave not in a:
                salida.append(f'{sub}: solo en el archivo de Jazzy')
            elif clave not in b:
                salida.append(f'{sub}: falta en el archivo de Jazzy')
            else:
                salida.extend(diferencias(a[clave], b[clave], sub))
        return salida
    return [] if a == b else [f'{ruta}: esperado {a!r}, hay {b!r}']


def plugins(arbol):
    """Todos los valores de las claves 'plugin', con su ruta."""
    if isinstance(arbol, dict):
        for clave, valor in arbol.items():
            if clave == 'plugin' and isinstance(valor, str):
                yield valor
            else:
                yield from plugins(valor)


def plugins_distribucion(params):
    """Los plugins de planificador y comportamientos, que son los que cambian."""
    gb = params['planner_server']['ros__parameters']['GridBased']['plugin']
    bs = params['behavior_server']['ros__parameters']
    return {gb} | {bs[i]['plugin'] for i in bs['behavior_plugins']}


def nombres_humble_instalados():
    nombres = set()
    for ruta in XML_HUMBLE:
        if not ruta.is_file():
            return None
        for clase in ET.parse(ruta).getroot().iter('class'):
            nombres.add(clase.get('name') or clase.get('type'))
    return nombres


def yaml_del_controller(ruta_jazzy):
    """Ejecuta el lanzador y devuelve el YAML que recibiria el controller_server."""
    from launch import LaunchContext
    from launch.actions import DeclareLaunchArgument

    spec = importlib.util.spec_from_file_location('nav2_hardware', LAUNCH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    ld = modulo.generate_launch_description()
    contexto = LaunchContext()
    defecto_params = None
    for entidad in ld.entities:
        if isinstance(entidad, DeclareLaunchArgument):
            entidad.execute(contexto)
            if entidad.name == 'params':
                defecto_params = contexto.launch_configurations.get('params', '')
    contexto.launch_configurations.update({
        'urdf': str(URDF),
        'params': str(ruta_jazzy),
        'slam_params': str(BRINGUP / 'config/slam_toolbox.yaml'),
        'behavior_trees': str(BRINGUP / 'behavior_trees'),
        'slam': 'true',
        'nav': 'true',
    })
    acciones = ld.entities[-1].execute(contexto)
    controller = [a for a in acciones
                  if getattr(a, 'node_executable', None) == 'controller_server']
    if len(controller) != 1:
        raise RuntimeError(f'se esperaba un controller_server y hay {len(controller)}')
    nodo = controller[0]
    nodo._perform_substitutions(contexto)
    ficheros = [ruta for ruta, es_fichero in nodo._Node__expanded_parameter_arguments
                if es_fichero]
    if len(ficheros) != 1:
        raise RuntimeError(f'se esperaba un fichero de parametros y hay {len(ficheros)}')
    return modulo, defecto_params, cargar_yaml(ficheros[0])


def main():
    ruta_jazzy = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else JAZZY
    humble = cargar_yaml(HUMBLE)
    jazzy = cargar_yaml(ruta_jazzy)
    fallos = []

    def exigir(condicion, mensaje):
        if not condicion:
            fallos.append(mensaje)

    # 1. No divergencia.
    for linea in diferencias(derivar(humble), jazzy):
        fallos.append(f'divergencia fuera de los cambios de distribucion: {linea}')

    # 2. Cada archivo habla su distribucion.
    exigir(plugins_distribucion(jazzy) <= PLUGINS_JAZZY,
           f'plugins que Jazzy no declara: {sorted(plugins_distribucion(jazzy) - PLUGINS_JAZZY)}')
    con_barra = sorted(p for p in plugins(jazzy) if '/' in p)
    exigir(not con_barra, f'plugins con «/», que Jazzy no encuentra: {con_barra}')
    bt = jazzy['bt_navigator']['ros__parameters']
    exigir('plugin_lib_names' not in bt,
           'bt_navigator lleva plugin_lib_names: en Jazzy repite los nodos que ya '
           'carga y el nodo no configura')
    exigir(not [k for k in bt if 'groot' in k], 'quedan parametros de Groot en bt_navigator')
    cs = jazzy['controller_server']['ros__parameters']
    exigir('progress_checker_plugin' not in cs and
           cs.get('progress_checker_plugins') == ['progress_checker'],
           'el progress checker no esta declarado como Jazzy lo lee')
    bs = jazzy['behavior_server']['ros__parameters']
    exigir(bs.get('local_frame') == 'odom' and bs.get('global_frame') == 'map',
           f"behavior_server: local_frame={bs.get('local_frame')!r}, "
           f"global_frame={bs.get('global_frame')!r}")

    instalados = nombres_humble_instalados()
    if instalados is None:
        print('[OMI] No hay Nav2 de Humble instalado aqui: no se contrastan sus nombres')
    else:
        exigir(plugins_distribucion(humble) <= instalados,
               'el archivo de Humble usa plugins que Humble no declara: '
               f'{sorted(plugins_distribucion(humble) - instalados)}')

    # 3. El lanzador carga la variante de Jazzy y aplica los ajustes de hardware.
    try:
        modulo, defecto, final = yaml_del_controller(ruta_jazzy)
    except ImportError as error:
        fallos.append(f'no se pudo ejecutar el lanzador ({error}); sourcea ROS antes')
    else:
        exigir(modulo.PARAMS_JAZZY == JAZZY.name,
               f'el lanzador apunta a {modulo.PARAMS_JAZZY!r}, no a {JAZZY.name!r}')
        if defecto:
            exigir(defecto.endswith(JAZZY.name),
                   f'el valor por defecto de params es {defecto!r}')
        else:
            print('[OMI] deepracer_bringup no esta instalado: no se comprueba el '
                  'valor por defecto de params, solo la constante del lanzador')
        cs_final = final['controller_server']['ros__parameters']
        fp = cs_final['FollowPath']
        exigir(fp['min_approach_linear_velocity'] == SUELO_VELOCIDAD and
               fp['regulated_linear_scaling_min_speed'] == SUELO_VELOCIDAD,
               'el lanzador no subio las velocidades minimas al suelo del puente')
        exigir(cs_final['use_sim_time'] is False, 'use_sim_time sigue en verdadero')
        exigir(cs_final.get('progress_checker_plugins') == ['progress_checker'],
               'la reescritura del lanzador perdio el progress checker de Jazzy')
        voxel = final['local_costmap']['local_costmap']['ros__parameters']['voxel_layer']
        exigir(voxel['scan']['topic'] == TOPICO_SCAN,
               f"el costmap local escucha {voxel['scan']['topic']!r}")
        exigir(plugins_distribucion(final) <= PLUGINS_JAZZY,
               'tras la reescritura del lanzador los plugins ya no son los de Jazzy')
        bt_final = final['bt_navigator']['ros__parameters']
        exigir(pathlib.Path(bt_final['default_nav_to_pose_bt_xml']).is_file(),
               'el arbol NavigateToPose que recibe el bt_navigator no existe')

    print()
    if fallos:
        print(f'FALLA — {len(fallos)} comprobacion(es):')
        for mensaje in fallos:
            print(f'  {mensaje}')
        return 1
    print('PASA: la variante de Jazzy solo difiere de la de Humble en los seis cambios')
    print('      de distribucion, cada archivo usa los nombres de plugin de su')
    print('      distribucion, y el lanzador de hardware la carga con sus ajustes.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
