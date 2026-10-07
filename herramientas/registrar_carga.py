#!/usr/bin/env python3
"""Registra cada pocos segundos cuanto se llena la tarjeta del vehiculo con toda la cadena.

Uso, en el vehiculo (no hace falta root ni instalar nada: lee /proc):

    python3 ~/tesis/registrar_carga.py ~/carga_p4r_04.csv                 # hasta Ctrl-C
    python3 ~/tesis/registrar_carga.py ~/carga_p4r_04.csv --cada 5 --segundos 3600

Y para resumir un registro, en el vehiculo o en el portatil:

    python3 herramientas/registrar_carga.py --resumen ~/tesis_evidencia/carga_p4r_04.csv

POR QUE EXISTE
--------------
La tarjeta tiene dos nucleos (Intel Atom E3930) y ya se quedo corta: el
2026-09-29 el controlador de Nav2 no sostenia 20 Hz, y el 2026-10-05 la IMU y el
filtro tuvieron que bajar de frecuencia (S26_integracion_imu_vehiculos.md). htop
muestra el momento; esto deja la serie entera de una corrida, con lo que gasta
cada pieza, para saber cuanto margen queda con Nav2, AMCL, rf2o, la IMU, el
filtro, el puente y el grabador a la vez.

QUE ANOTA
---------
Una fila cada --cada segundos: la carga media de 1 minuto, el procesador total
(en % de toda la tarjeta: 100 = los dos nucleos llenos), la memoria usada, la
temperatura mas alta de la tarjeta y, por grupo de procesos, su procesador en %
de UN nucleo (como htop: 100 = un nucleo entero). Los grupos estan en GRUPOS.
"""
import argparse
import csv
import glob
import os
import signal
import statistics
import sys
import time

# Grupo -> fragmentos que se buscan en el nombre o la orden del proceso. El
# primero que coincide se queda con el proceso; lo que no coincide va a 'resto'.
GRUPOS = [
    ('nav2', ('controller_server', 'planner_server', 'bt_navigator', 'behavior_server',
              'lifecycle_manager', 'waypoint_follower', 'velocity_smoother')),
    ('amcl', ('amcl',)),
    ('map_server', ('map_server',)),
    ('rf2o', ('rf2o_laser_odom',)),
    ('filtro', ('ekf_node',)),
    ('imu', ('imu_bmi160',)),
    ('tf_robot', ('robot_state_publisher', 'static_transform_publisher')),
    ('puente', ('cmdvel_to_servo',)),
    ('lidar', ('rplidar',)),
    ('grabador', ('ros2 bag', 'rosbag2')),
    ('corrida', ('corrida_nav2',)),
    ('coordinacion', ('coordinacion/agente', 'coordinacion/coordinador')),
    ('ros2_cli', ('/ros2 ', 'ros2 launch', 'ros2 topic', 'ros2 service', 'ros2 run')),
    ('aws', ('/opt/aws/',)),
]
NOMBRES = [g for g, _ in GRUPOS] + ['resto']
CLK = os.sysconf('SC_CLK_TCK')


def cpu_total():
    """(ocupado, total) en ticks, de la linea 'cpu' de /proc/stat."""
    with open('/proc/stat') as f:
        campos = [int(v) for v in f.readline().split()[1:]]
    inactivo = campos[3] + campos[4]           # idle + iowait
    return sum(campos) - inactivo, sum(campos)


def procesos():
    """{pid: (grupo, ticks de cpu)} de todos los procesos."""
    yo = os.getpid()
    salida = {}
    for d in glob.glob('/proc/[0-9]*'):
        pid = int(d[6:])
        if pid == yo:
            continue
        try:
            with open(d + '/stat') as f:
                stat = f.read()
            with open(d + '/cmdline', 'rb') as f:
                orden = f.read().replace(b'\0', b' ').decode('utf-8', 'replace')
        except OSError:
            continue                            # termino entre el glob y la lectura
        nombre = stat[stat.index('(') + 1:stat.rindex(')')]
        campos = stat[stat.rindex(')') + 2:].split()
        ticks = int(campos[11]) + int(campos[12])   # utime + stime
        texto = f'{nombre} {orden}'
        grupo = next((g for g, claves in GRUPOS if any(c in texto for c in claves)), 'resto')
        salida[pid] = (grupo, ticks)
    return salida


def memoria_mb():
    datos = {}
    with open('/proc/meminfo') as f:
        for linea in f:
            clave, valor = linea.split(':')
            datos[clave] = int(valor.split()[0])
    return (datos['MemTotal'] - datos['MemAvailable']) / 1024, datos['MemTotal'] / 1024


def temperatura_c():
    valores = []
    for ruta in glob.glob('/sys/class/thermal/thermal_zone*/temp'):
        try:
            with open(ruta) as f:
                valores.append(int(f.read()) / 1000)
        except (OSError, ValueError):
            pass
    return max(valores) if valores else None


def registrar(ruta, cada, segundos):
    with open(ruta, 'w', newline='') as f:
        esc = csv.writer(f)
        esc.writerow(['t_s', 'hora', 'carga_1min', 'cpu_total_pct', 'mem_usada_mb',
                      'mem_total_mb', 'temp_c'] + [f'{g}_pct' for g in NOMBRES])
        t0 = time.monotonic()
        ocupado0, total0 = cpu_total()
        antes = procesos()
        momento0 = time.monotonic()
        print(f'registrando en {ruta} cada {cada:.0f} s (Ctrl-C para terminar)', flush=True)
        try:
            while segundos is None or time.monotonic() - t0 < segundos:
                time.sleep(cada)
                ahora = procesos()
                momento = time.monotonic()
                ocupado, total = cpu_total()
                dt = momento - momento0
                por_grupo = dict.fromkeys(NOMBRES, 0.0)
                for pid, (grupo, ticks) in ahora.items():
                    previo = antes.get(pid)
                    # Un proceso nuevo cuenta desde cero: arranco en este intervalo.
                    delta = ticks - (previo[1] if previo else 0)
                    if previo is None and ticks / CLK > dt:
                        delta = 0                # ya existia y no se vio: no se le atribuye todo
                    por_grupo[grupo] += 100.0 * delta / CLK / dt
                cpu = 100.0 * (ocupado - ocupado0) / max(1, total - total0)
                usada, total_mb = memoria_mb()
                temp = temperatura_c()
                with open('/proc/loadavg') as fc:
                    carga = float(fc.read().split()[0])
                esc.writerow([round(momento - t0, 1), time.strftime('%H:%M:%S'), carga,
                              round(cpu, 1), round(usada), round(total_mb),
                              '' if temp is None else round(temp, 1)]
                             + [round(por_grupo[g], 1) for g in NOMBRES])
                f.flush()
                antes, momento0, ocupado0, total0 = ahora, momento, ocupado, total
        except KeyboardInterrupt:
            pass
    print(f'listo: {ruta}')


def resumir(ruta):
    with open(ruta, newline='') as f:
        filas = list(csv.DictReader(f))
    if not filas:
        print(f'{ruta}: sin filas')
        return 1
    dur = float(filas[-1]['t_s'])
    print(f'{ruta}: {len(filas)} muestras en {dur / 60:.1f} min')

    def serie(col):
        return [float(r[col]) for r in filas if r.get(col) not in ('', None)]

    def p95(v):
        return sorted(v)[max(0, int(round(0.95 * len(v))) - 1)]

    print(f'{"":22}{"media":>8}{"p95":>8}{"maximo":>8}')
    for col, nombre in (('cpu_total_pct', 'procesador total, %'), ('carga_1min', 'carga (1 min)'),
                        ('mem_usada_mb', 'memoria usada, MB'), ('temp_c', 'temperatura, C')):
        v = serie(col)
        if v:
            print(f'{nombre:22}{statistics.fmean(v):8.1f}{p95(v):8.1f}{max(v):8.1f}')
    pico = max(filas, key=lambda r: float(r['cpu_total_pct']))
    print(f'pico de procesador: {pico["cpu_total_pct"]} % a las {pico["hora"]}')
    print('\npor grupo, en % de un nucleo (100 = un nucleo entero):')
    grupos = [(g, serie(f'{g}_pct')) for g in NOMBRES]
    for g, v in sorted(grupos, key=lambda x: -statistics.fmean(x[1]) if x[1] else 0):
        if v and max(v) > 0:
            print(f'  {g:20}{statistics.fmean(v):8.1f}{p95(v):8.1f}{max(v):8.1f}')
    return 0


def terminar(*_):
    raise KeyboardInterrupt


def main():
    p = argparse.ArgumentParser(description='Registra la carga de la tarjeta del vehiculo.')
    p.add_argument('ruta', nargs='?', help='CSV de salida')
    p.add_argument('--cada', type=float, default=5.0, help='segundos entre muestras')
    p.add_argument('--segundos', type=float, default=None, help='duracion; sin ella, hasta Ctrl-C')
    p.add_argument('--resumen', metavar='CSV', help='resume un registro ya hecho')
    a = p.parse_args()
    if a.resumen:
        return resumir(a.resumen)
    if not a.ruta:
        p.error('falta la ruta del CSV')
    # nav2_mapa_guardado.sh --parar lo cierra con SIGTERM: lanzado en segundo
    # plano desde un shell no interactivo, SIGINT le llega ignorado.
    signal.signal(signal.SIGTERM, terminar)
    registrar(a.ruta, a.cada, a.segundos)
    return 0


if __name__ == '__main__':
    sys.exit(main())
