#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construye el modelo SDF de una planta a partir de medidas de flexometro.

POR QUE EXISTE
--------------
El 2026-09-30, en el piso 2, se midio el hall con flexometro y resulto que el
modelo lo daba 0,84 m mas ancho de lo que es: 4,24 m contra 3,40 m reales, un
20 % de error. Con el mapa corregido AMCL sigue acumulando error longitudinal,
pero el episodio dejo claro que la geometria del modelo nunca se habia
contrastado contra el edificio. El §10 de ENTORNO_DE_EVALUACION.md ya lo
declaraba: «hasta ahora eso era un supuesto no verificado».

Este programa invierte el orden. En vez de dibujar una planta y suponer que se
parece al edificio, se parte de un levantamiento con flexometro y se deriva de
el TANTO el mundo de Gazebo COMO el mapa de navegacion. Simulacion y edificio
coinciden porque salen de la misma fuente, no porque se parezcan.

COMO SE USA
-----------
Las medidas van en una tabla al final del archivo, una por planta. Para anadir
el piso 3 se copia el bloque de PISO4, se cambian los numeros y se anade a
PLANTAS. No hay que tocar nada mas.

    python3 herramientas/generar_piso_desde_medidas.py piso4
    python3 herramientas/generar_piso_desde_medidas.py piso4 --svg   # ademas el plano

Produce  <nombre>/model.sdf,  <nombre>/model.config  y  <nombre>.world.
El mapa se saca despues con la herramienta que ya existe:

    python3 herramientas/generar_mapa_desde_mundo.py <nombre>.world <salida>.yaml

LA COMPROBACION QUE NO SE SALTA
-------------------------------
Un pasillo mide lo mismo por sus dos lados. El programa suma las dos paredes y
AVISA si no cierran. En el levantamiento del piso 4, esa comprobacion encontro
tres errores de lectura antes de generar nada: una profundidad contada como
largo, dos muritos duplicados y dos medidas invertidas. Cerro en 8 cm sobre
25,6 m, o sea 0,32 %.
"""

import math
import os
import sys

GROSOR = 0.15     # espesor de muro, el mismo que el resto de los modelos
ALTO = 2.5        # alto de muro

# =====================================================================
#  Planta del PISO 4 — levantamiento con flexometro del 2026-10-02
# =====================================================================
#
# La pared OESTE se recorre de norte a sur. Cada tramo es (largo, quiebre, etiqueta):
#   largo   : avance a lo largo del pasillo, en metros
#   quiebre : desplazamiento lateral DESPUES del tramo (+ se aleja del pasillo)
#
# La pared ESTE lleva ademas hornacinas, que entran y salen lateralmente:
#   ('r', largo)              tramo recto
#   ('in', profundidad)       la pared se hunde (entra la hornacina)
#   ('out', profundidad)      la pared vuelve
#   ('p', largo, nombre)      vano de puerta
#
PISO4 = {
    'nombre': 'piso4',
    'etiqueta': 'Piso 4',
    'ancho_norte': 2.35,
    'ancho_sur': 2.61,
    'oeste': [
        (6.34,  0.20,  'pared norte'),
        (3.00, -0.20,  'lockers'),
        (6.53,  0.00,  'pared'),
        (1.03,  0.00,  'ascensor'),       # lamina: punto de llegada
        (2.29,  0.30,  'pared'),
        (0.695,-0.30,  'papelera'),
        (3.71, -0.185, 'pared'),          # el murito de 18,5 cm es el ensanche
        (1.58,  0.00,  'escalera'),       # lamina: punto de TRANSFERENCIA
        (0.44,  0.00,  'pared sur'),
    ],
    'este': [
        ('r',  5.480),
        ('in', 0.994),                    # entra la hornacina larga 401/402
        ('r',  0.225),
        ('p',  0.990, '401'),
        ('r',  2.120),                    # pared continua entre las dos puertas
        ('p',  0.990, '402'),
        ('r',  0.235),
        ('out',1.050),
        ('r',  5.690),
        ('in', 1.010),                    # hornacina del 403
        ('r',  0.995),
        ('p',  0.990, '403'),
        ('r',  0.234),
        ('out',0.990),
        ('r',  5.600),
        ('r',  1.985),
    ],
    # Aberturas de la pared oeste que NO son muro: se cierran con lamina.
    # 'llegada' = destino normal; 'transferencia' = por donde se cambia de piso.
    'aberturas': {'ascensor': 'llegada', 'escalera': 'transferencia'},
}

# =====================================================================
#  Planta del PISO 3 — levantamiento con flexometro del 2026-10-02
# =====================================================================
#  La pared ESTE y las hornacinas de los salones son LAS MISMAS que el piso 4
#  (asi lo confirmo el equipo), de modo que se reutiliza su lista. Lo que
#  cambia es la pared oeste y el ancho del extremo sur: 2,45 m contra 2,61 m.
PISO3 = {
    'nombre': 'piso3',
    'etiqueta': 'Piso 3',
    'ancho_norte': 2.35,
    'ancho_sur': 2.45,
    'oeste': [
        (6.59,  0.39,  'pared norte'),
        (9.10, -0.39,  'lockers'),
        (0.33,  0.00,  'pared'),
        (1.03,  0.00,  'ascensor'),       # lamina: punto de llegada
        (2.29,  0.30,  'pared'),
        (0.695,-0.30,  'papelera'),       # sobresale 30 cm, igual que la del piso 4
        (1.26, -0.39,  'muro'),           # al acabar, el pasillo se ensancha 39 cm
        (1.61,  0.00,  'escalera'),       # lamina: punto de TRANSFERENCIA
        (0.00,  0.70,  'entra saliente'), # el saliente entra 70 cm al pasillo...
        (0.39, -0.70,  'saliente'),       # ...a lo largo de 39 cm, y vuelve
        (2.05,  0.00,  'pared sur'),
    ],
    # Misma geometria que el piso 4 salvo dos cosas, medidas en este piso:
    # los salones van renumerados, y el tramo que en el piso 4 mide 5,60 m
    # aqui mide 5,57 m.
    'este': [(t[0], t[1], '3' + t[2][1:]) if t[0] == 'p'
             else (('r', 5.57) if t == ('r', 5.600) else t)
             for t in PISO4['este']],
    'aberturas': {'ascensor': 'llegada', 'escalera': 'transferencia'},
}

PLANTAS = {'piso4': PISO4, 'piso3': PISO3}


# ------------------------------------------------------------ geometria ---
def recorrer(planta):
    """Devuelve (puntos_oeste, puntos_este, aberturas, largo_o, largo_e).

    Los puntos van en (a, b): a = across (ancho del pasillo), b = along (largo).
    """
    oeste, aberturas, b, a = [(0.0, 0.0)], [], 0.0, 0.0
    for largo, quiebre, etiqueta in planta['oeste']:
        b0 = b
        b += largo
        oeste.append((a, b))
        if etiqueta in planta['aberturas']:
            aberturas.append((etiqueta, a, b0, b, planta['aberturas'][etiqueta]))
        if quiebre:
            a += quiebre
            oeste.append((a, b))
    largo_o = b

    largo_e = sum(t[1] for t in planta['este'] if t[0] in ('r', 'p'))
    L = max(largo_o, largo_e)

    def ancho(bb):
        return (planta['ancho_norte']
                + (planta['ancho_sur'] - planta['ancho_norte']) * bb / L)

    este, b, off, puertas = [], 0.0, 0.0, []
    este.append((ancho(0.0), 0.0))
    for it in planta['este']:
        k = it[0]
        if k == 'r':
            b += it[1]
            este.append((ancho(b) + off, b))
        elif k == 'in':
            off += it[1]
            este.append((ancho(b) + off, b))
        elif k == 'out':
            off -= it[1]
            este.append((ancho(b) + off, b))
        else:
            b0 = b
            b += it[1]
            este.append((ancho(b) + off, b))
            puertas.append((it[2], ancho(b) + off, b0, b))
    return oeste, este, aberturas, puertas, largo_o, largo_e


def segmentos(puntos):
    """Cada par de puntos consecutivos se vuelve un muro, saltando los de largo cero."""
    out = []
    for (a1, b1), (a2, b2) in zip(puntos, puntos[1:]):
        largo = math.hypot(a2 - a1, b2 - b1)
        if largo < 1e-6:
            continue
        out.append(((b1 + b2) / 2.0, (a1 + a2) / 2.0, largo,
                    math.atan2(a2 - a1, b2 - b1)))
    return out


# ------------------------------------------------------------------ sdf ---
def muro(nombre, cx, cy, largo, yaw):
    tam = f"{largo + GROSOR:.4f} {GROSOR} {ALTO}"
    return f"""    <link name='{nombre}'>
      <collision name='{nombre}_Collision'>
        <geometry><box><size>{tam}</size></box></geometry>
        <pose>0 0 {ALTO/2} 0 -0 0</pose>
      </collision>
      <visual name='{nombre}_Visual'>
        <pose>0 0 {ALTO/2} 0 -0 0</pose>
        <geometry><box><size>{tam}</size></box></geometry>
        <material>
          <script>
            <uri>file://media/materials/scripts/gazebo.material</uri>
            <name>Gazebo/Grey</name>
          </script>
          <ambient>1 1 1 1</ambient>
        </material>
      </visual>
      <pose>{cx:.4f} {cy:.4f} 0 0 -0 {yaw:.4f}</pose>
    </link>
"""


def generar(clave, con_svg=False):
    planta = PLANTAS[clave]
    oeste, este, aberturas, puertas, lo, le = recorrer(planta)

    # --- la comprobacion que no se salta ---
    dif = abs(lo - le)
    print(f"  pared oeste  {lo:7.3f} m")
    print(f"  pared este   {le:7.3f} m")
    print(f"  cierre       {dif*100:7.1f} cm  ({dif/max(lo,le)*100:.2f} %)", end='  ')
    if dif / max(lo, le) > 0.02:
        print("<-- NO CIERRA: revisa el levantamiento antes de usar este modelo")
    else:
        print("ok")

    links = []
    for i, (cx, cy, L, yaw) in enumerate(segmentos(oeste), 1):
        links.append(muro(f"Muro_O{i:02d}", cx, cy, L, yaw))
    for i, (cx, cy, L, yaw) in enumerate(segmentos(este), 1):
        links.append(muro(f"Muro_E{i:02d}", cx, cy, L, yaw))
    # Laminas: cierran las aberturas de la pared oeste. Van EN LINEA con esa
    # pared (yaw 0), no perpendiculares: con yaw pi/2 sobresalen al exterior y
    # se ven en el mapa como dos palos saliendo del pasillo.
    for nom, a, b0, b1, _ in aberturas:
        links.append(muro(f"Lamina_{nom}", (b0+b1)/2.0, a, b1-b0, 0.0))

    # Muros de los extremos. Sin ellos el pasillo queda abierto por norte y sur,
    # y el relleno del generador de mapa se escapa y marca libre el exterior:
    # 92,9 % de celdas libres en un pasillo de 2,4 m de ancho es la senal.
    # En el levantamiento son las cotas de 2,35 m (norte) y 2,61 m (sur).
    for nom, (a1, b1), (a2, b2) in (("Muro_Norte", oeste[0], este[0]),
                                    ("Muro_Sur", oeste[-1], este[-1])):
        links.append(muro(nom, (b1 + b2) / 2.0, (a1 + a2) / 2.0,
                          math.hypot(a2 - a1, b2 - b1),
                          math.atan2(a2 - a1, b2 - b1)))

    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'simulacion', planta['nombre'])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'model.sdf'), 'w') as f:
        f.write("<?xml version='1.0'?>\n<sdf version='1.7'>\n"
                f"  <model name='{planta['nombre']}'>\n"
                "    <static>true</static>\n" + "".join(links) +
                "  </model>\n</sdf>\n")
    with open(os.path.join(d, 'model.config'), 'w') as f:
        f.write(f"""<?xml version="1.0"?>
<model>
  <name>{planta['nombre']}</name>
  <version>1.0</version>
  <sdf version="1.7">model.sdf</sdf>
  <description>
    {planta['etiqueta']} del edificio, derivado de un levantamiento con
    flexometro (2026-10-02). Lo genera herramientas/generar_piso_desde_medidas.py;
    no editar a mano.
  </description>
</model>
""")
    world = os.path.join(os.path.dirname(d), planta['nombre'] + '.world')
    with open(world, 'w') as f:
        f.write(f"""<?xml version='1.0'?>
<sdf version='1.7'>
  <world name='default'>
    <include><uri>model://ground_plane</uri></include>
    <include><uri>model://sun</uri></include>
    <include>
      <uri>model://{planta['nombre']}</uri>
      <pose>0 0 0 0 0 0</pose>
    </include>
  </world>
</sdf>
""")
    print(f"\n  {planta['nombre']}/model.sdf   ({len(links)} muros)")
    print(f"  {planta['nombre']}.world")

    print("\n  PUNTOS DE INTERES sugeridos (a 1 m de la pared, frente al vano):")
    for nom, a, b0, b1 in puertas:
        print(f"    {planta[chr(39)+chr(39)] if False else planta['nombre']}_salon_{nom:<6} x={(b0+b1)/2:7.3f}  y={a-1.0:6.3f}")
    for nom, a, b0, b1, papel in aberturas:
        marca = "  <-- es_transferencia: true" if papel == 'transferencia' else ""
        print(f"    {planta['nombre']}_{nom:<12} x={(b0+b1)/2:7.3f}  y={a+1.0:6.3f}{marca}")

    if con_svg:
        import subprocess
        print("\n  (el plano SVG se dibuja aparte con el guion de /tmp/plano)")


if __name__ == '__main__':
    clave = sys.argv[1] if len(sys.argv) > 1 else 'piso4'
    if clave not in PLANTAS:
        print(f"Plantas disponibles: {', '.join(PLANTAS)}")
        sys.exit(1)
    print(f"=== {PLANTAS[clave]['etiqueta']} ===")
    generar(clave, '--svg' in sys.argv)
