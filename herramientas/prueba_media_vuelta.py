#!/usr/bin/env python3
"""La media vuelta por tiempos completa el giro sin tocar paredes, o se detiene sin tocarlas.

POR QUE EXISTE
--------------
coordinacion/media_vuelta.py mueve el vehiculo sin Nav2, al lado de la escalera.
Un error de signo en la prediccion del recorrido, o un tiempo que no se corta a
tiempo, no da ningun error: el vehiculo simplemente se va contra la pared o
hacia el vano. Aqui se prueba con un vehiculo simulado como racey: radio de
0,6 m hacia un lado y 1,5 m hacia el otro (la calibracion del servo no es
simetrica), mas lento en reversa y rodando un poco al soltar, en la geometria
de la salida del piso 4 (paredes y lamina de la escalera del mapa).

QUE COMPRUEBA
-------------
  1. Geometria: la holgura de la huella; la prediccion del recorrido con el
     signo correcto en los cuatro casos de marcha y giro.
  2. Desde el waypoint de la escalera del piso 4, mirando al sur: elige el giro
     cuya reversa se aleja de la escalera, completa al menos 160 grados y la
     huella nunca toca una pared ni la lamina.
  2b. Lo mismo con una reversa a 1,0 m/s que rueda 0,9 s al soltar, como deepy
     el 2026-10-08 (rodo 0,8 m tras la orden de parar).
  3. Lo mismo con un vehiculo simetrico (0,8 m): menos tiempos.
  4. Desde la salida (1,56 m de la pared oeste), como en p4r_11c.
  5. En un pasillo de 1,2 m con 1,5 m de radio no cabe: se detiene sin tocar nada.
  6. Una caja detras del vehiculo: completa o se detiene, pero no la toca.

Uso, desde la raiz del repositorio (no necesita ROS):

    python3 herramientas/prueba_media_vuelta.py
"""
import importlib.util
import math
import pathlib
import sys

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'media_vuelta', RAIZ / 'Robot/aws-deepracer/coordinacion/coordinacion/media_vuelta.py')
mv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mv)


def pared(x0, y0, x1, y1, paso=0.03):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / paso) + 1)
    return np.column_stack((np.linspace(x0, x1, n), np.linspace(y0, y1, n)))


def salida_piso4():
    """Salida del piso 4 en el marco del mapa: oeste y = -0,07 con la lamina de la
    escalera (x 23,6 a 25,2), este y = 2,46, sur x = 25,45, y la pared oeste del
    pasillo (y = 0,11) al norte de la escalera."""
    return np.vstack([pared(19.0, 0.11, 23.6, 0.11), pared(23.6, -0.07, 25.45, -0.07),
                      pared(23.6, 0.11, 23.6, -0.07), pared(19.0, 2.46, 25.45, 2.46),
                      pared(25.45, -0.07, 25.45, 2.46)])


class Vehiculo:
    """Bicicleta con radio por lado, retardo al arrancar y rodadura al soltar."""

    def __init__(self, x, y, yaw, r_izq, r_der, v_ade=0.65, v_rev=0.45, rodada_s=0.3):
        self.x, self.y, self.yaw = x, y, yaw
        self.r_izq, self.r_der = r_izq, r_der
        self.v_ade, self.v_rev = v_ade, v_rev
        self.rodada_s = rodada_s
        self.v = 0.0
        self.orden = (0.0, 0.0)

    def mandar(self, v, w):
        self.orden = (v, w)

    def avanzar(self, dt):
        v_cmd, w_cmd = self.orden
        objetivo = 0.0 if v_cmd == 0 else (self.v_ade if v_cmd > 0 else -self.v_rev)
        # Arranca en 0,2 s y para en 0,3 s: rueda de 0,07 a 0,1 m al soltar.
        tasa = (abs(objetivo) / 0.2) if objetivo else (max(self.v_ade, self.v_rev) / self.rodada_s)
        self.v += max(-tasa * dt, min(tasa * dt, objetivo - self.v))
        if v_cmd != 0 and w_cmd != 0:
            # Lado de la direccion como en el puente: signo de w / v.
            self.lado = 1 if (w_cmd / v_cmd) > 0 else -1
        elif v_cmd == 0:
            self.lado = 0      # con la orden cero el puente centra la direccion: rueda recto
        lado = getattr(self, 'lado', 0)
        if lado:
            r = self.r_izq if lado > 0 else self.r_der
            self.yaw += self.v / r * lado * dt
        self.x += self.v * math.cos(self.yaw) * dt
        self.y += self.v * math.sin(self.yaw) * dt


def correr(paredes, vehiculo, giro=None):
    """Corre la maniobra con un reloj simulado. Devuelve (ok, mensaje, holgura minima)."""
    estado = {'t': 0.0, 'holgura_min': math.inf}

    def leer_obstaculos():
        p = mv.a_marco(paredes, vehiculo.x, vehiculo.y, vehiculo.yaw)
        return p, p                       # el LiDAR y el mapa ven lo mismo

    def dormir(dt):
        for _ in range(5):
            vehiculo.avanzar(dt / 5)
            p = mv.a_marco(paredes, vehiculo.x, vehiculo.y, vehiculo.yaw)
            estado['holgura_min'] = min(estado['holgura_min'], mv.holgura(p))
        estado['t'] += dt

    ok, msg = mv.ejecutar(lambda: vehiculo.yaw, leer_obstaculos, vehiculo.mandar, giro=giro,
                          reloj=lambda: estado['t'], dormir=dormir, log=lambda *_: None,
                          leer_velocidad=lambda: vehiculo.v)
    for _ in range(20):                    # lo que rueda despues de terminar
        dormir(0.05)
    return ok, msg, estado['holgura_min']


def main():
    ok_n, fallos = 0, []

    def exigir(cond, mensaje):
        nonlocal ok_n
        if cond:
            ok_n += 1
            print('  [OK ]', mensaje)
        else:
            fallos.append(mensaje)
            print('  [MAL]', mensaje)

    print('1. Geometria')
    exigir(mv.holgura(np.array([[0.0, 0.0]])) == 0.0, 'un punto dentro de la huella tiene holgura 0')
    exigir(abs(mv.holgura(np.array([[0.34, 0.0]])) - 0.20) < 1e-9,
           'un punto a 0,20 m de la defensa delantera tiene holgura 0,20')
    for marcha, giro, sx, sy in ((1, 1, 1, 1), (1, -1, 1, -1), (-1, 1, -1, -1), (-1, -1, -1, 1)):
        x, y, th = mv.poses_predichas(marcha, giro, radios=(0.5,))[-1]
        exigir(np.sign(x) == sx and np.sign(y) == sy and np.sign(th) == giro,
               f'marcha {marcha:+d}, giro {giro:+d}: termina en x {x:+.2f}, y {y:+.2f}, '
               f'rumbo {math.degrees(th):+.0f} grados')

    paredes = salida_piso4()

    def caso(titulo, vehiculo, minimo_grados=160.0, debe_completar=True, giro=None, max_tiempos=None):
        yaw0 = vehiculo.yaw
        ok, msg, hmin = correr(paredes_caso[0], vehiculo, giro)
        girado = math.degrees(abs(mv.normalizar(vehiculo.yaw - yaw0)))
        print(f'  {titulo}: {msg}')
        exigir(hmin > 0.0, f'{titulo}: la huella nunca toca nada (holgura minima {hmin:.2f} m)')
        if debe_completar is None:
            pass
        elif debe_completar:
            exigir(ok and girado >= minimo_grados, f'{titulo}: completa ({girado:.0f} grados)')
        else:
            exigir(not ok, f'{titulo}: se detiene y lo dice')

    paredes_caso = [paredes]
    print('2. Escalera del piso 4, mirando al sur, como racey (0,6 m / 1,5 m)')
    caso('racey en la escalera', Vehiculo(24.39, 0.82, 0.0, 0.6, 1.5))
    g, izq, der = mv.elegir_giro(mv.a_marco(paredes, 24.39, 0.82, 0.0))
    exigir(g == -1, f'elige el giro horario: la reversa abre hacia el este ({izq:.2f} m) '
                    f'y no hacia la escalera ({der:.2f} m)')
    print('   Con el lado debil al reves (1,5 m / 0,6 m)')
    caso('lado debil al reves', Vehiculo(24.39, 0.82, 0.0, 1.5, 0.6))

    print('2b. Como deepy el 8-oct: reversa a 1,0 m/s que rueda 0,9 s al soltar, junto a la escalera')
    caso('rodada larga en la escalera', Vehiculo(24.39, 0.82, 0.0, 0.6, 1.5, v_rev=1.0, rodada_s=0.9))
    caso('rodada larga, lado debil al reves', Vehiculo(24.39, 0.82, 0.0, 1.5, 0.6, v_rev=1.0, rodada_s=0.9))
    caso('rodada larga desde la salida', Vehiculo(24.25, 1.49, 0.0, 0.6, 1.5, v_rev=1.0, rodada_s=0.9))

    print('3. Vehiculo simetrico (0,8 m)')
    caso('simetrico', Vehiculo(24.39, 0.82, 0.0, 0.8, 0.8))

    print('4. Desde la salida, a 1,56 m de la pared oeste (p4r_11c)')
    caso('salida', Vehiculo(24.25, 1.49, 0.0, 0.6, 1.5))

    print('5. Pasillo de 1,2 m con 1,5 m de radio: no cabe')
    paredes_caso[0] = np.vstack([pared(0, 0, 8, 0), pared(0, 1.2, 8, 1.2)])
    caso('angosto', Vehiculo(4.0, 0.6, 0.0, 1.5, 1.5), debe_completar=False)

    print('6. Una caja 0,5 m detras de la defensa trasera: completa o se detiene, pero no la toca')
    paredes_caso[0] = np.vstack([paredes, pared(23.75, 0.6, 23.75, 1.1), pared(23.75, 1.1, 23.55, 1.1)])
    caso('caja detras', Vehiculo(24.39, 0.82, 0.0, 0.6, 1.5), debe_completar=None)

    print('=' * 62)
    if fallos:
        print(f'{len(fallos)} comprobaciones FALLAN de {ok_n + len(fallos)}')
        return 1
    print(f'Todas las comprobaciones pasan ({ok_n}).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
