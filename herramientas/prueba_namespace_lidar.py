#!/usr/bin/env python3
"""El LiDAR del vehiculo fisico es direccionable por espacio de nombres.

QUE SE COMPRUEBA Y POR QUE ASI
------------------------------
'lidar_vehiculo.launch.py' llevaba 'namespace=' escrito en el codigo. Con un
solo vehiculo era correcto; con dos en el dominio 0 los dos publicarian en
'/scan'. RF-02 exige que cada agente sea direccionable por separado y RF-12
pide literalmente '/<ns>/scan'.

La prueba NO se limita a mirar que con 'robot1' salga '/robot1'. Eso pasaria
igual aunque el prefijado estuviera roto en la direccion que importa. Se
comprueban tres cosas, y las dos ultimas son las que pueden delatar el fallo:

  1. El defecto no cambia: sin argumento, el nodo sigue sin espacio de nombres
     y el sensor sigue publicando en '/scan'. Un cambio que rompa el caso de
     un vehiculo no sirve.
  2. robot1 y robot2 no comparten NADA: ni espacio de nombres ni marco TF. Si
     el marco se quedara en 'laser' para los dos -que es el error facil, porque
     los topicos ya no chocarian y pareceria resuelto- los dos arboles TF se
     pisarian sobre el '/tf' compartido. Es el mismo fallo que costo una mision
     abortada con el marco 'map' el 2026-08-24
     (Evidencia/S20_marco_map_prefijado.md).
  3. La forma del argumento no cambia el resultado: 'robot1', '/robot1' y
     '/robot1/' tienen que dar lo mismo.

Se ejercita el launch de verdad -se genera la descripcion y se ejecuta la
OpaqueFunction sobre un LaunchContext-, no una copia de la logica.

    python3 herramientas/prueba_namespace_lidar.py
"""
import importlib.util
import pathlib

from launch import LaunchContext
from launch.actions import DeclareLaunchArgument

LAUNCH = (pathlib.Path(__file__).resolve().parents[1]
          / 'Robot/aws-deepracer/deepracer_bringup/launch/lidar_vehiculo.launch.py')

# Lo que launch_ros pone cuando el namespace es None, es decir cuando el nodo
# se queda en la raiz y el sensor publica en '/scan'.
SIN_ESPACIO = '<node_namespace_unspecified>'


def cargar():
    spec = importlib.util.spec_from_file_location('lidar_vehiculo', LAUNCH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def resolver(modulo, **argumentos):
    """Genera la descripcion, la ejecuta y devuelve (espacio, marco)."""
    ld = modulo.generate_launch_description()
    contexto = LaunchContext()
    for entidad in ld.entities:
        if isinstance(entidad, DeclareLaunchArgument):
            entidad.execute(contexto)
    contexto.launch_configurations.update(argumentos)

    acciones = ld.entities[-1].execute(contexto)
    nodo = acciones[0]
    nodo._perform_substitutions(contexto)

    _, marco = modulo.resolver_espacio(argumentos.get('namespace', ''),
                                       argumentos.get('frame_id', '').strip())
    return nodo.expanded_node_namespace, marco


def main():
    modulo = cargar()
    fallos = []

    def exigir(condicion, mensaje):
        if not condicion:
            fallos.append(mensaje)

    # 1. El defecto no cambia.
    espacio, marco = resolver(modulo)
    exigir(espacio == SIN_ESPACIO,
           f"sin argumento el nodo deberia quedar sin espacio de nombres, y quedo en {espacio!r}")
    exigir(marco == 'laser', f"sin argumento el marco deberia ser 'laser', y es {marco!r}")

    # 2. robot1 y robot2 no comparten nada.
    espacio1, marco1 = resolver(modulo, namespace='robot1')
    espacio2, marco2 = resolver(modulo, namespace='robot2')
    exigir(espacio1 == '/robot1', f"robot1 quedo en {espacio1!r}")
    exigir(espacio2 == '/robot2', f"robot2 quedo en {espacio2!r}")
    exigir(espacio1 != espacio2, 'los dos vehiculos comparten espacio de nombres')
    exigir(marco1 == 'robot1/laser', f"el marco de robot1 es {marco1!r}")
    exigir(marco2 == 'robot2/laser', f"el marco de robot2 es {marco2!r}")
    exigir(marco1 != marco2,
           f"los dos vehiculos comparten el marco {marco1!r}: los arboles TF se pisan "
           'aunque los topicos ya no choquen')

    # 3. La forma del argumento no cambia el resultado.
    for forma in ('/robot1', 'robot1/', '/robot1/'):
        espacio, marco = resolver(modulo, namespace=forma)
        exigir((espacio, marco) == (espacio1, marco1),
               f"{forma!r} dio {(espacio, marco)} en vez de {(espacio1, marco1)}")

    # 4. Un marco explicito manda sobre el prefijado automatico.
    _, marco = resolver(modulo, namespace='robot1', frame_id='laser_frame')
    exigir(marco == 'laser_frame', f"el marco explicito se ignoro y quedo {marco!r}")

    print()
    if fallos:
        print(f"FALLA — {len(fallos)} comprobacion(es):")
        for mensaje in fallos:
            print(f"  {mensaje}")
        return 1
    print('PASA: el LiDAR del vehiculo es direccionable por espacio de nombres,')
    print('      el caso de un solo vehiculo no cambia, y dos vehiculos no')
    print('      comparten ni topico ni marco TF.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
