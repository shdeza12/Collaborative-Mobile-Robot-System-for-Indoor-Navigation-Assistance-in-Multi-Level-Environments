#!/usr/bin/env python3
"""Verifica un LiDAR real contra una distancia medida con cinta metrica.

Por que existe
--------------
El entregable tiene que decir hasta que distancia mide el sensor DE VERDAD, y
con que error. Leer `range_max` del mensaje no contesta ninguna de las dos
cosas: ese campo es un filtro que el driver copia de su YAML, no una medida. El
YDLidar G4 declara 16 m en el mensaje mientras su YAML dice 64 m; ninguno de los
dos numeros se obtuvo midiendo nada.

Por que no se toma el minimo
----------------------------
El primer intento buscaba la pared como "el punto mas cercano". El sensor
devolvio 0,166 m en el sector -153..-147 deg: su propio soporte. Contra una
pared a 1,00 m eso habria dado 83 % de error. El punto mas cercano al sensor no
es la pared.

Por que no se buscan lecturas "cerca de 1 m"
--------------------------------------------
Porque seria circular: encontrar lo que ya sabemos donde esta no demuestra
exactitud. El programa nunca recibe la distancia esperada. Busca superficies por
su FORMA -conjuntos de puntos colineales, via RANSAC- y solo al final se compara
la distancia hallada con la cinta.

Que hay que mirar en la salida
------------------------------
- Una superficie real aparece en TODOS los barridos. Si sale en 3 de 10, es ruido.
- La dispersion entre barridos es la REPETIBILIDAD, que es lo que le importa a
  AMCL: que la misma pared devuelva el mismo numero.
- El RMS de los residuos es la PLANITUD: si el sensor ve recta una pared recta.
- La diferencia contra la cinta es una COTA SUPERIOR del error, no el error: el
  LiDAR mide desde su centro optico, dentro de la carcasa, y la cinta se apoya en
  algun punto exterior. Esa diferencia de origen es de orden centimetrico y no se
  puede separar de la exactitud con este montaje. Decir "el sensor tiene X % de
  error" a partir de aqui seria indefendible.

Uso:
    python3 herramientas/verificar_lidar.py [distancia_cinta_m]

Con el sensor quieto frente a una pared plana, y esa pared entre las superficies
mas cercanas (por defecto se consideran las que estan a menos de 3 m).
"""

import math
import sys
from collections import defaultdict

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

DESCARTAR = 5      # el motor aun se estabiliza en los primeros barridos
BARRIDOS = 10
CERCANIA = 3.0     # m; mas alla empieza el resto de la sala
TOLERANCIA = 0.02  # m; un punto pertenece a la recta si dista menos de 2 cm
ITERACIONES = 400
MIN_PUNTOS = 25
RECTAS = 3         # cuantas superficies se extraen por barrido


def una_recta(pts, rng):
    """RANSAC: la recta con mas puntos a menos de TOLERANCIA."""
    mejor = (0, None, None)
    for _ in range(ITERACIONES):
        i, j = rng.choice(len(pts), 2, replace=False)
        d = pts[j] - pts[i]
        norma = math.hypot(*d)
        if norma < 0.10:      # dos puntos casi pegados no definen bien la recta
            continue
        nrm = np.array([-d[1], d[0]]) / norma
        c = float(nrm @ pts[i])
        inl = np.abs(pts @ nrm - c) < TOLERANCIA
        if inl.sum() > mejor[0]:
            mejor = (int(inl.sum()), nrm, inl)
    if mejor[1] is None or mejor[0] < MIN_PUNTOS:
        return None
    # refinado por minimos cuadrados totales sobre los inliers
    sel = pts[mejor[2]]
    centro = sel.mean(axis=0)
    nrm = np.linalg.svd(sel - centro)[2][1]
    c = float(nrm @ centro)
    if c < 0:
        nrm, c = -nrm, -c
    return c, nrm, mejor[2]


class Verificador(Node):
    def __init__(self, cinta):
        super().__init__("verificar_lidar")
        self.cinta = cinta
        self.n = self.b = 0
        self.rng = np.random.default_rng(0)
        self.acum = defaultdict(list)
        self.cab = None
        # El driver publica /scan como BEST_EFFORT. Un suscriptor por defecto es
        # RELIABLE y no recibe nada: QoS incompatible, sin error visible.
        self.create_subscription(LaserScan, "/scan", self.cb, qos_profile_sensor_data)

    def cb(self, m):
        self.n += 1
        if self.n <= DESCARTAR:
            return
        if self.cab is None:
            self.cab = m
        ang, rad = [], []
        for i, r in enumerate(m.ranges):
            if math.isfinite(r) and m.range_min < r < CERCANIA:
                ang.append(m.angle_min + i * m.angle_increment)
                rad.append(r)
        if len(rad) < 40:
            return
        ang, rad = np.array(ang), np.array(rad)
        pts = np.stack([rad * np.cos(ang), rad * np.sin(ang)], axis=1)
        libres = np.ones(len(pts), bool)
        self.b += 1
        print(f"\nbarrido {self.b}  ({len(pts)} puntos a menos de {CERCANIA} m)")
        for k in range(RECTAS):
            idx = np.flatnonzero(libres)
            if len(idx) < MIN_PUNTOS:
                break
            sal = una_recta(pts[idx], self.rng)
            if sal is None:
                break
            c, nrm, inl = sal
            gl = idx[inl]
            a = np.degrees(ang[gl])
            largo = np.ptp((pts[gl] - nrm * c) @ np.array([-nrm[1], nrm[0]]))
            rms = math.sqrt((np.abs(pts[gl] @ nrm - c) ** 2).mean()) * 1000
            print(f"  recta {k+1}: d={c:6.3f} m  n={len(gl):4d}  largo={largo:5.2f} m  "
                  f"rms={rms:4.1f} mm  sector {a.min():+7.1f}..{a.max():+7.1f} deg  "
                  f"normal {math.degrees(math.atan2(nrm[1], nrm[0])):+6.1f} deg")
            self.acum[round(c, 1)].append(c)
            libres[gl] = False
        if self.b >= BARRIDOS:
            raise SystemExit


def informe(nodo):
    m = nodo.cab
    print("\n=== lo que declara el sensor ===")
    print(f"  muestras por barrido : {len(m.ranges)}")
    print(f"  barrido angular      : {math.degrees(m.angle_max - m.angle_min):.1f} deg")
    print(f"  resolucion angular   : {math.degrees(m.angle_increment):.3f} deg")
    print(f"  rango declarado      : {m.range_min:.2f} .. {m.range_max:.2f} m")
    print("  (estos son campos del mensaje: filtros del driver, no medidas)")

    print("\n=== superficies halladas por su forma ===")
    for k in sorted(nodo.acum):
        v = nodo.acum[k]
        med = sorted(v)[len(v) // 2]
        print(f"  ~{k:.1f} m : en {len(v):2d}/{nodo.b} barridos  mediana {med:.4f} m  "
              f"dispersion {(max(v)-min(v))*1000:5.1f} mm")

    if nodo.cinta is None:
        return
    # Se compara con la superficie cuya mediana esta mas cerca de la cinta. Esto
    # NO es circular: la superficie ya fue hallada sin conocer la cinta; aqui
    # solo se decide cual de las halladas es la que el operador midio.
    cand = [(abs(sorted(v)[len(v) // 2] - nodo.cinta), sorted(v)[len(v) // 2], len(v))
            for v in nodo.acum.values()]
    err, med, apar = min(cand)
    print(f"\n=== contra la cinta ({nodo.cinta:.3f} m) ===")
    print(f"  superficie elegida : {med:.4f} m  (presente en {apar}/{nodo.b} barridos)")
    print(f"  diferencia         : {(med - nodo.cinta)*1000:+.0f} mm  "
          f"({abs(med - nodo.cinta)/nodo.cinta*100:.2f} %)")
    print("  COTA SUPERIOR del error: incluye la diferencia entre el centro optico")
    print("  del sensor y el punto donde se apoyo la cinta.")


def main():
    cinta = float(sys.argv[1]) if len(sys.argv) > 1 else None
    rclpy.init()
    nodo = Verificador(cinta)
    try:
        rclpy.spin(nodo)
    except SystemExit:
        pass
    if nodo.cab is None:
        print("no llego ningun barrido. Comprobar que el driver publica en /scan.")
        return
    informe(nodo)


main()
