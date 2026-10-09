#!/usr/bin/env python3
"""El lanzador del vehiculo admite espacio de nombres sin cambiar el modo sin el.

POR QUE EXISTE
--------------
El bloque C de Documentos/PLAN_S25.md pone la pila del vehiculo bajo `/robotN`,
que es como la manda el coordinador. Su criterio de cierre en el escritorio es:
con `namespace:=robot2`, todos los nodos bajo `/robot2` y todos los marcos con
prefijo, y el modo sin espacio de nombres identico al de antes. Un marco sin
prefijar no da error en ninguna parte: el costmap se queda vacio o el
planificador no transforma la meta, y se ve en el pasillo, no aqui.

QUE COMPRUEBA
-------------
Ejecuta nav2_hardware.launch.py sobre un LaunchContext con slam y nav
encendidos, y lee lo que recibiria cada nodo: espacio de nombres, argumentos y
el contenido de sus ficheros de parametros.

  1. SIN ESPACIO DE NOMBRES, IGUAL QUE ANTES. Se lanza tambien la version del
     commit REFERENCIA, anterior al bloque C, y los dos lanzamientos tienen que
     coincidir nodo a nodo y parametro a parametro.
  2. CON `robot2`: todos los nodos bajo `/robot2`; los YAML anidados bajo
     `robot2`; las nueve claves de marco de Nav2 y las tres de slam_toolbox con
     prefijo, y ningun marco de Nav2 sin el; rf2o en `/robot2/odom` con marcos
     prefijados; `frame_prefix` en robot_state_publisher; la TF identidad
     `robot2/laser -> laser`, y el gestor con nombres relativos.
  3. CON `imu:=true`, sin espacio de nombres y con `robot2`: el nodo de la IMU
     publica en `imu_link` (prefijado); rf2o pasa a `odom_rf2o` y deja la TF; el
     EKF publica `odom` y la TF, toma de rf2o solo x e y como diferencias y de la
     IMU solo la velocidad de giro en z, con los marcos prefijados. La URDF tiene
     `imu_link` con la orientacion medida el 2026-10-05: en el sensor, adelante
     es y, izquierda es x y arriba es -z. Sin la ruta del nodo, el lanzador
     aborta con un mensaje que se entiende.
  4. `margen_llegada:=0.5` llega a todos los `xy_goal_tolerance` de Nav2.

Uso, desde la raiz del repositorio y con ROS y el workspace sourceados:

    python3 herramientas/prueba_nav2_hardware_ns.py [ruta_al_lanzador]

Con la ruta de otro lanzador se comprueba que la prueba no es vacia: con la
version de REFERENCIA la parte 2 tiene que fallar.
"""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile

import yaml

RAIZ = pathlib.Path(__file__).resolve().parents[1]
BRINGUP = RAIZ / 'Robot/aws-deepracer/deepracer_bringup'
LAUNCH = BRINGUP / 'launch/nav2_hardware.launch.py'
URDF = RAIZ / 'Robot/aws-deepracer/deepracer_description/models/urdf/deepracer_hardware.urdf'
# Ultimo commit con el lanzador anterior al bloque C.
REFERENCIA = '6ef1642'
NS = 'robot2'
TOPICO_SCAN = '/rplidar_ros/scan'

MARCOS_NAV2 = {
    ('bt_navigator', 'global_frame'): 'map',
    ('bt_navigator', 'robot_base_frame'): 'base_link',
    ('local_costmap.local_costmap', 'global_frame'): 'odom',
    ('local_costmap.local_costmap', 'robot_base_frame'): 'base_link',
    ('global_costmap.global_costmap', 'global_frame'): 'map',
    ('global_costmap.global_costmap', 'robot_base_frame'): 'base_link',
    ('behavior_server', 'local_frame'): 'odom',
    ('behavior_server', 'global_frame'): 'map',
    ('behavior_server', 'robot_base_frame'): 'base_link',
}
MARCOS_SLAM = {'odom_frame': 'odom', 'map_frame': 'map', 'base_frame': 'base_link'}
NODOS_NAV2 = {'controller_server', 'planner_server', 'behavior_server', 'bt_navigator'}
# Ajustes de hardware posteriores a REFERENCIA. Cambian el modo sin espacio de
# nombres a proposito, asi que se comprueban aparte y se quitan antes de comparar.
# 'default_server_timeout' es el ajuste 6 del lanzador (2026-09-29, noche); el
# retraso de rf2o, el 7, y el margen de llegada de Nav2, el 8 (2026-09-30).
# 'GridBased.lookup_table_size' es el ajuste 10 (2026-10-09).
AJUSTES_POSTERIORES = {'bt_navigator': {'default_server_timeout': 1000},
                       'planner_server': {'GridBased.lookup_table_size': 10.0}}
EJECUTABLE_RETRASADO = 'rf2o_laser_odometry_node'
# xy_goal_tolerance: valor del YAML (el de REFERENCIA) y valor del ajuste 8.
MARGEN_YAML, MARGEN_AJUSTE = 0.25, 1.0
# bond_timeout del gestor: el de REFERENCIA (20 s) y el del 2026-10-08 (60 s), con
# el que racey ya no aborta el arranque a carga 22.
BOND_REFERENCIA, BOND_AJUSTE = 20.0, 60.0
# Ajuste 9 (2026-10-09): rf2o solo escribe errores; llenaba el registro de la cadena.
ARGS_RF2O = ['--ros-args', '--log-level', 'error']


def cargar(ruta):
    # launch_ros escribe las listas de los diccionarios como tuplas de Python.
    with open(ruta) as f:
        return yaml.load(f, Loader=yaml.UnsafeLoader)


def lanzar(ruta_launch, ns, extra=None):
    """Devuelve {nombre completo: {ejecutable, ns, args, params}} de cada nodo."""
    from launch import LaunchContext
    from launch.actions import DeclareLaunchArgument, TimerAction

    spec = importlib.util.spec_from_file_location('lanzador', ruta_launch)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    ld = modulo.generate_launch_description()
    contexto = LaunchContext()
    for entidad in ld.entities:
        if isinstance(entidad, DeclareLaunchArgument):
            entidad.execute(contexto)
    contexto.launch_configurations.update({
        'urdf': str(URDF),
        'params': str(BRINGUP / 'config/nav2_params_jazzy.yaml'),
        'slam_params': str(BRINGUP / 'config/slam_toolbox.yaml'),
        'behavior_trees': str(BRINGUP / 'behavior_trees'),
        'slam': 'true',
        'nav': 'true',
        'namespace': ns,
        **(extra or {}),
    })
    # Un nodo dentro de un TimerAction (rf2o, ajuste 7) se lanza igual, mas tarde.
    acciones = []
    for accion in ld.entities[-1].execute(contexto):
        if isinstance(accion, TimerAction):
            acciones += [(a, True) for a in accion.actions]
        else:
            acciones.append((accion, False))
    nodos = {}
    for accion, retrasado in acciones:
        accion._perform_substitutions(contexto)
        ficheros = [cargar(p) for p, es in (accion._Node__expanded_parameter_arguments or [])
                    if es]
        nodos[accion.node_name] = {
            'ejecutable': accion.node_executable,
            'ns': accion.expanded_node_namespace,
            'args': accion._Node__arguments,
            'params': ficheros,
            'remap': accion._Node__expanded_remappings or [],
            'retrasado': retrasado,
        }
    return nodos


def margenes(arbol):
    """Devuelve las rutas de cada 'xy_goal_tolerance' de un arbol de parametros."""
    if not isinstance(arbol, dict):
        return []
    rutas = [(arbol, 'xy_goal_tolerance')] if 'xy_goal_tolerance' in arbol else []
    for valor in arbol.values():
        rutas += margenes(valor)
    return rutas


def quitar_ajustes(nodos, exigir):
    """Comprueba los ajustes posteriores a REFERENCIA y los quita para comparar."""
    for nodo in nodos.values():
        # Ajuste 7: solo rf2o arranca con retraso.
        exigir(nodo['retrasado'] == (nodo['ejecutable'] == EJECUTABLE_RETRASADO),
               f"{nodo['ejecutable']}: retraso de arranque inesperado o ausente")
        nodo['retrasado'] = False
        # Ajuste 9: solo rf2o lleva el nivel de registro en error.
        if nodo['ejecutable'] == EJECUTABLE_RETRASADO:
            exigir(list(nodo['args'] or []) == ARGS_RF2O,
                   f"rf2o: argumentos {nodo['args']!r}, se esperaba {ARGS_RF2O!r}")
            nodo['args'] = None
        # Ajuste 8: el YAML de Nav2 llega con el margen de llegada a 1 m.
        for fichero in nodo['params']:
            for padre, clave in margenes(fichero):
                exigir(padre[clave] == MARGEN_AJUSTE,
                       f"{nodo['ejecutable']}: xy_goal_tolerance vale {padre[clave]!r}")
                padre[clave] = MARGEN_YAML
        # El plazo del latido del gestor, 20 -> 60 s.
        for fichero in nodo['params']:
            for v in fichero.values():
                rp = v.get('ros__parameters') if isinstance(v, dict) else None
                if isinstance(rp, dict) and 'bond_timeout' in rp:
                    exigir(rp['bond_timeout'] == BOND_AJUSTE,
                           f"{nodo['ejecutable']}: bond_timeout vale {rp['bond_timeout']!r}")
                    rp['bond_timeout'] = BOND_REFERENCIA
        esperado = AJUSTES_POSTERIORES.get(nodo['ejecutable'])
        if not esperado:
            continue
        extra = [f for f in nodo['params']
                 if len(f) == 1 and list(f.values())[0].get('ros__parameters') == esperado]
        exigir(len(extra) == 1,
               f"{nodo['ejecutable']} no recibe su ajuste posterior {esperado}")
        nodo['params'] = [f for f in nodo['params'] if f not in extra]
    return nodos


def del_nodo(ficheros):
    """Parametros de un nodo lanzado con un diccionario (clave '/ns/nombre')."""
    assert len(ficheros) == 1
    return list(ficheros[0].values())[0]['ros__parameters']


def bajar(arbol, ruta):
    for clave in ruta.split('.'):
        arbol = arbol[clave]
    return arbol


def main():
    ruta_launch = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else LAUNCH
    ok, fallos = 0, []

    def exigir(condicion, mensaje):
        nonlocal ok
        if condicion:
            ok += 1
        else:
            fallos.append(mensaje)

    # 1. Sin espacio de nombres, igual que la version de referencia.
    try:
        texto = subprocess.run(
            ['git', 'show', f'{REFERENCIA}:{LAUNCH.relative_to(RAIZ)}'], cwd=RAIZ,
            capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print(f'[OMI] no se pudo leer {REFERENCIA} con git: no se compara con la referencia')
    else:
        with tempfile.NamedTemporaryFile('w', suffix='.launch.py', delete=False) as f:
            f.write(texto)
        antes, ahora = lanzar(f.name, ''), quitar_ajustes(lanzar(ruta_launch, ''), exigir)
        exigir(set(antes) == set(ahora),
               f'sin espacio de nombres cambian los nodos: {sorted(set(antes) ^ set(ahora))}')
        for nombre in sorted(set(antes) & set(ahora)):
            exigir(antes[nombre] == ahora[nombre],
                   f'sin espacio de nombres cambia {nombre}')
        # launch_ros marca asi un nodo sin espacio de nombres: no le pasa '__ns'.
        from launch_ros.actions import Node
        exigir(all(n['ns'] == Node.UNSPECIFIED_NODE_NAMESPACE for n in ahora.values()),
               'sin espacio de nombres algun nodo recibe uno')

    # 2. Con espacio de nombres.
    try:
        con_ns(quitar_ajustes(lanzar(ruta_launch, NS), exigir), exigir)
    except (KeyError, IndexError, ValueError, TypeError) as error:
        fallos.append(f'con {NS} la estructura no es la esperada ({error!r})')

    # 3. Con IMU, sin espacio de nombres y con el.
    for ns in ('', NS):
        try:
            con_imu(lanzar(ruta_launch, ns, {'imu': 'true'}), ns, exigir)
        except (KeyError, IndexError, ValueError, TypeError, AttributeError) as error:
            fallos.append(f"con imu:=true y ns {ns!r} la estructura no es la esperada ({error!r})")
    try:
        lanzar(ruta_launch, '', {'imu': 'true', 'imu_nodo': '/no/existe/imu_bmi160.py'})
        exigir(False, 'con imu:=true y un nodo que no existe, el lanzador no aborta')
    except RuntimeError as error:
        exigir('imu_bmi160.py' in str(error), f'mensaje poco claro sin el nodo: {error}')
    except Exception as error:  # noqa: BLE001 - la version sin IMU falla de otra forma
        exigir(False, f'sin el nodo de la IMU el lanzador falla con {error!r}')
    urdf_imu(exigir)

    # 4. El margen de llegada como argumento.
    try:
        vistos = [padre[clave] for n in lanzar(ruta_launch, '', {'margen_llegada': '0.5'}).values()
                  for f in n['params'] for padre, clave in margenes(f)]
        exigir(vistos and all(v == 0.5 for v in vistos),
               f'margen_llegada:=0.5 no llega a Nav2: {vistos}')
    except Exception as error:  # noqa: BLE001 - la version sin el argumento falla de otra forma
        exigir(False, f'margen_llegada:=0.5 no se acepta ({error!r})')

    print('=' * 62)
    if fallos:
        for f in fallos:
            print('  [MAL]', f)
        print(f'{len(fallos)} comprobaciones FALLAN de {ok + len(fallos)}')
        return 1
    print(f'Todas las comprobaciones pasan ({ok}).')
    return 0


def con_ns(nodos, exigir):
    """Comprobaciones de la parte 2 sobre los nodos lanzados con NS."""
    exigir(all(n['ns'] == f'/{NS}' for n in nodos.values()),
           f"nodos fuera de /{NS}: {[k for k, n in nodos.items() if n['ns'] != '/' + NS]}")

    por_ejecutable = {n['ejecutable']: n for n in nodos.values()}
    rsp = del_nodo(por_ejecutable['robot_state_publisher']['params'])
    exigir(rsp.get('frame_prefix') == f'{NS}/', f"frame_prefix es {rsp.get('frame_prefix')!r}")

    rf2o = del_nodo(por_ejecutable['rf2o_laser_odometry_node']['params'])
    exigir(rf2o['odom_topic'] == f'/{NS}/odom', f"rf2o publica en {rf2o['odom_topic']!r}")
    exigir(rf2o['base_frame_id'] == f'{NS}/base_link' and rf2o['odom_frame_id'] == f'{NS}/odom',
           'rf2o sin marcos prefijados')
    exigir(rf2o['laser_scan_topic'] == TOPICO_SCAN, f"rf2o lee {rf2o['laser_scan_topic']!r}")

    tf = por_ejecutable.get('static_transform_publisher')
    exigir(tf is not None, 'falta la TF identidad del laser')
    if tf:
        args = tf['args']
        exigir(args[args.index('--frame-id') + 1] == f'{NS}/laser' and
               args[args.index('--child-frame-id') + 1] == 'laser',
               f'la TF identidad no es {NS}/laser -> laser: {args}')

    for ejecutable in NODOS_NAV2:
        (yaml_nav2,) = por_ejecutable[ejecutable]['params']
        exigir(list(yaml_nav2) == [NS], f'el YAML de {ejecutable} no esta anidado bajo {NS}')
    arbol = por_ejecutable['controller_server']['params'][0][NS]
    for (nodo, clave), marco in MARCOS_NAV2.items():
        valor = bajar(arbol, nodo)['ros__parameters'][clave]
        exigir(valor == f'{NS}/{marco}', f'{nodo}.{clave} vale {valor!r}')
    sueltos = [f'{nodo}.{clave}' for nodo in ('bt_navigator', 'behavior_server',
                                              'local_costmap.local_costmap',
                                              'global_costmap.global_costmap')
               for clave, valor in bajar(arbol, nodo)['ros__parameters'].items()
               if 'frame' in clave and valor in ('map', 'odom', 'base_link')]
    exigir(not sueltos, f'marcos de Nav2 sin prefijo: {sueltos}')
    for capa in ('local_costmap.local_costmap.ros__parameters.voxel_layer',
                 'global_costmap.global_costmap.ros__parameters.obstacle_layer'):
        exigir(bajar(arbol, capa)['scan']['topic'] == TOPICO_SCAN, f'{capa} no lee el laser')
    exigir(arbol['controller_server']['ros__parameters']['controller_frequency'] == 10.0,
           'el controlador no quedo a 10 Hz')

    (yaml_slam,) = por_ejecutable['sync_slam_toolbox_node']['params']
    slam = yaml_slam.get(NS, {}).get('slam_toolbox', {}).get('ros__parameters', {})
    for clave, marco in MARCOS_SLAM.items():
        exigir(slam.get(clave) == f'{NS}/{marco}', f'slam_toolbox.{clave} vale {slam.get(clave)!r}')

    gestor = del_nodo(por_ejecutable['lifecycle_manager']['params'])
    exigir(all(not n.startswith('/') for n in gestor['node_names']),
           'el gestor lleva nombres absolutos: no encontraria los nodos del espacio de nombres')
    # bond_timeout: lo comprueba quitar_ajustes(), en los dos modos, antes de llegar aqui.


def con_imu(nodos, ns, exigir):
    """Comprobaciones de la parte 3 sobre los nodos lanzados con imu:=true."""
    pre = f'{ns}/' if ns else ''
    topico = (lambda t: f'/{ns}/{t}') if ns else (lambda t: f'/{t}')
    por_nombre = {n.rsplit('/', 1)[-1]: v for n, v in nodos.items()}
    exigir('imu_bmi160' in por_nombre and 'ekf_filter_node' in por_nombre,
           f'con imu:=true faltan nodos: {sorted(por_nombre)}')
    if ns:
        exigir(all(n['ns'] == f'/{ns}' for n in nodos.values()),
               f'con imu:=true hay nodos fuera de /{ns}')

    imu = por_nombre['imu_bmi160']
    exigir(imu['ejecutable'] == 'python3' and str(imu['args'][0]).endswith('imu_bmi160.py')
           and pathlib.Path(str(imu['args'][0])).is_file(),
           f"el nodo de la IMU no arranca imu_bmi160.py: {imu['ejecutable']} {imu['args']}")
    exigir(del_nodo(imu['params'])['frame_id'] == f'{pre}imu_link',
           f"la IMU publica en {del_nodo(imu['params'])['frame_id']!r}")

    rf2o = del_nodo(next(n for n in nodos.values()
                         if n['ejecutable'] == 'rf2o_laser_odometry_node')['params'])
    exigir(rf2o['odom_topic'] == topico('odom_rf2o'), f"rf2o publica en {rf2o['odom_topic']!r}")
    exigir(rf2o['publish_tf'] is False, 'con la IMU rf2o sigue publicando la TF')

    ekf = por_nombre['ekf_filter_node']
    exigir(ekf['ejecutable'] == 'ekf_node', f"el EKF es {ekf['ejecutable']!r}")
    exigir(('odometry/filtered', 'odom') in ekf['remap'] or
           ((f'/{ns}/odometry/filtered' if ns else '/odometry/filtered'),
            (f'/{ns}/odom' if ns else '/odom')) in ekf['remap'],
           f"el EKF no publica en odom: {ekf['remap']}")
    p = del_nodo(ekf['params'])
    for clave, marco in (('map_frame', 'map'), ('odom_frame', 'odom'),
                         ('base_link_frame', 'base_link'), ('world_frame', 'odom')):
        exigir(p[clave] == f'{pre}{marco}', f'EKF {clave} vale {p[clave]!r}')
    exigir(p['two_d_mode'] is True and p['publish_tf'] is True and
           p['use_sim_time'] is False, 'EKF sin two_d_mode, sin TF o con tiempo simulado')
    exigir(p['odom0'] == topico('odom_rf2o') and p['imu0'] == topico('imu/data'),
           f"el EKF lee {p['odom0']!r} y {p['imu0']!r}")
    exigir([i for i, v in enumerate(p['odom0_config']) if v] == [0, 1] and
           p['odom0_differential'] is True,
           f"de rf2o el EKF toma {p['odom0_config']} (differential {p['odom0_differential']})")
    exigir([i for i, v in enumerate(p['imu0_config']) if v] == [11],
           f"de la IMU el EKF toma {p['imu0_config']}")


def urdf_imu(exigir):
    """imu_link en la URDF, con la orientacion medida (S26_pruebas_imu.md, seccion 2)."""
    import math
    import xml.etree.ElementTree as ET
    juntas = {j.find('child').get('link'): j for j in ET.parse(URDF).getroot().iter('joint')}
    junta = juntas.get('imu_link')
    exigir(junta is not None and junta.find('parent').get('link') == 'base_link',
           'la URDF no cuelga imu_link de base_link')
    if junta is None:
        return
    r, p, y = (float(v) for v in junta.find('origin').get('rpy').split())
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    # Matriz de imu_link en base_link: Rz(y) Ry(p) Rx(r), convencion de URDF.
    m = [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
         [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
         [-sp, cp * sr, cp * cr]]
    # Un eje de base_link expresado en el sensor es la fila de m (m traspuesta).
    for nombre, eje_base, eje_sensor in (('adelante', 0, (0, 1, 0)), ('izquierda', 1, (1, 0, 0)),
                                         ('arriba', 2, (0, 0, -1))):
        visto = tuple(round(m[eje_base][j], 3) for j in range(3))
        exigir(visto == tuple(float(v) for v in eje_sensor),
               f'{nombre} del vehiculo sale {visto} en el sensor; medido {eje_sensor}')


if __name__ == '__main__':
    sys.exit(main())
