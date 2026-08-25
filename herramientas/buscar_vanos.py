#!/usr/bin/env python3
"""Encuentra los vanos de un mundo y decide cuales hay que tapar.

POR QUE EXISTE
--------------
generar_mapa_desde_mundo.py pinta las paredes y rellena el interior desde una
semilla. Si el mundo tiene un vano abierto -una puerta sin hoja, un extremo de
pasillo sin cerrar- el relleno se escapa por ahi y declara LIBRE medio plano.
Eso se tapaba pasando opciones --region, que recortan el resultado a mano: el
mapa sale bien pero el mundo sigue abierto, y cualquier cosa que no sea ese
recorte -Gazebo, el LiDAR, un relleno desde otra semilla- ve los agujeros.

La cura es sellar el mundo de verdad, con paneles sinteticos. Este script dice
donde van. El criterio de cierre luego es regenerar el mapa SIN ninguna
--region: si el mundo esta sellado, el relleno se contiene solo.

COMO DECIDE QUE ES UN VANO
--------------------------
Se empareja cada punta suelta de pared con la pared que tiene enfrente. De ahi
salen muchos falsos: la seccion transversal de un pasillo tambien es un hueco
entre dos paredes. Se filtra con tres condiciones geometricas.

1. COLINEALIDAD. Un vano real es una INTERRUPCION de una linea de pared: el
   hueco prolonga el eje de la pared que lo abre. Una seccion de pasillo es
   perpendicular a ella. En el piso 2 la separacion fue tajante -todo vano
   real dio |cos| >= 0,92 y toda transversal <= 0,71-, sin zona gris.

2. ORTOGONALIDAD CON LA OTRA. El hueco llega a la segunda pared de frente
   (empalme en T) o de canto (interrupcion colineal), nunca en diagonal. Sin
   esto, una punta dispara rayos oblicuos a traves de una sala entera.

3. LINEA DE VISION, por punto-dentro-de-caja y no por distancia al eje. Esa
   distincion importa: el rayo SALE de la punta de una pared y MUERE en la
   cara de otra, asi que rozarlas es legitimo y solo atravesar el cuerpo
   invalida el hueco. Midiendo contra el eje, las muestras junto a la punta
   caen dentro del umbral y declaran bloqueado todo vano en T.

CUAL SE TAPA Y CUAL NO
----------------------
La geometria dice donde hay huecos; no dice cual es puerta y cual es paso. Eso
lo deciden las --region, que declaran la red navegable: si los dos lados del
hueco caen dentro de la red, es paso y se deja abierto. Es el unico uso legitimo
que les queda a las --region, y por eso el script las pide.

OJO. Sin --region todo sale a sellar, incluidos los pasos. Un paso tapado no da
ningun error: deja una zona incomunicada y en silencio.
"""
import argparse
import math
import sys
import xml.etree.ElementTree as ET

from generar_mapa_desde_mundo import modelos_del_mundo, leer_pose

GROSOR_PANEL = 0.15   # m, el mismo de las paredes de los mundos del proyecto
ALTO_PANEL = 2.5      # m
SOLAPE = 0.05         # m por lado. Sin solape queda una rendija de menos de una
                      # celda por la que el relleno se cuela igual.
EMPALME = 0.16        # por debajo de esto la punta esta pegada: no hay hueco
COLINEAL = 0.85       # |cos| minimo con el eje de la pared que abre el hueco
ORTOGONAL = 0.15      # |cos| maximo para aceptar que llega de frente
DEDUP = 0.30          # m entre centros para considerar que es el mismo sitio
MUESTREO = 0.03       # m entre muestras de la linea de vision


def paredes(ruta, altura):
    """Devuelve [nombre, x, y, yaw, largo] de cada caja que cruza la altura."""
    mundo = ET.parse(ruta).getroot().find('world')
    out = []
    for _, (mx, my, _, _), el in modelos_del_mundo(mundo, ruta):
        for link in el.findall('link'):
            caja = next((c for col in link.findall('collision')
                         for c in col.iter('box')), None)
            if caja is None:
                continue
            largo, _, alto = [float(v) for v in caja.find('size').text.split()][:3]
            lx, ly, lz, lyaw = leer_pose(link)
            cz = lz + float(caja.find('../../pose').text.split()[2]) \
                if caja.find('../../pose') is not None else lz
            if not (cz - alto / 2 <= altura <= cz + alto / 2):
                continue
            out.append([link.get('name'), mx + lx, my + ly, lyaw, largo])
    # el bloque <state> del world manda sobre la pose declarada en el model.sdf
    est = mundo.find('state')
    if est is not None:
        pos = {lk.get('name'): leer_pose(lk)
               for m in est.findall('model') for lk in m.findall('link')}
        for p in out:
            if p[0] in pos:
                p[1], p[2], p[3] = pos[p[0]][0], pos[p[0]][1], pos[p[0]][3]
    return out


def buscar(P, max_vano):
    yaws = {p[0]: p[3] for p in P}
    cajas = {p[0]: (p[1], p[2], p[3], p[4] / 2, GROSOR_PANEL / 2) for p in P}
    seg = {}
    for n, x, y, yaw, L in P:
        dx, dy = math.cos(yaw) * L / 2, math.sin(yaw) * L / 2
        seg[n] = ((x - dx, y - dy), (x + dx, y + dy))

    def proy(px, py, a, b):
        ax, ay = a
        vx, vy = b[0] - ax, b[1] - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L2))
        return math.hypot(px - (ax + t * vx), py - (ay + t * vy)), (ax + t * vx, ay + t * vy)

    def en_caja(px, py, nombre, margen=0.01):
        cx, cy, yaw, hl, hw = cajas[nombre]
        dx, dy = px - cx, py - cy
        u = dx * math.cos(yaw) + dy * math.sin(yaw)
        v = -dx * math.sin(yaw) + dy * math.cos(yaw)
        return abs(u) < hl - margen and abs(v) < hw - margen

    def libre(p, q):
        """El hueco no atraviesa el CUERPO de ninguna pared.

        Se corta el ultimo medio grosor: el rayo muere sobre el eje de la
        segunda pared, y sin ese recorte las ultimas muestras caen dentro de
        ella y declararian bloqueado todo empalme en T.
        """
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
        t = MUESTREO
        while t < d - GROSOR_PANEL / 2 - 0.025:
            x, y = p[0] + ux * t, p[1] + uy * t
            if any(en_caja(x, y, k) for k in cajas):
                return False
            t += MUESTREO
        return True

    cand = {}
    for n, (a, b) in seg.items():
        for punta in (a, b):
            for k in seg:
                if k == n:
                    continue
                d, q = proy(punta[0], punta[1], *seg[k])
                if d <= EMPALME or d > max_vano:
                    continue
                rumbo = math.atan2(q[1] - punta[1], q[0] - punta[0])
                if abs(math.cos(rumbo - yaws[n])) < COLINEAL:
                    continue                      # diagonal a traves de una sala
                ck = abs(math.cos(rumbo - yaws[k]))
                if not (ck >= COLINEAL or ck <= ORTOGONAL):
                    continue                      # ni de frente ni de canto
                if not libre(punta, q):
                    continue
                clave = tuple(sorted([(round(punta[0], 2), round(punta[1], 2)),
                                      (round(q[0], 2), round(q[1], 2))]))
                if clave not in cand or d < cand[clave][0]:
                    cand[clave] = (d, n, k)

    final = []
    for clave, (d, n, k) in sorted(cand.items(), key=lambda kv: -kv[1][0]):
        (x0, y0), (x1, y1) = clave
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if any(math.hypot(cx - f[1], cy - f[2]) < DEDUP for f in final):
            continue
        final.append((d, cx, cy, math.atan2(y1 - y0, x1 - x0), n, k))
    return final


PIEZA = """    <!-- vano de {d:.3f} m entre {n} y {k} -->
    <link name='{nom}'>
      <collision name='{nom}_Collision'>
        <geometry>
          <box>
            <size>{L:.5f} {g} {h}</size>
          </box>
        </geometry>
        <pose>0 0 {mitad} 0 -0 0</pose>
      </collision>
      <visual name='{nom}_Visual'>
        <pose>0 0 {mitad} 0 -0 0</pose>
        <geometry>
          <box>
            <size>{L:.5f} {g} {h}</size>
          </box>
        </geometry>
        <material>
          <script>
            <uri>file://media/materials/scripts/gazebo.material</uri>
            <name>Gazebo/Orange</name>
          </script>
          <ambient>1 0.5 0 1</ambient>
        </material>
        <meta>
          <layer>0</layer>
        </meta>
      </visual>
      <pose>{cx:.5f} {cy:.5f} 0 0 -0 {yaw:.5f}</pose>
    </link>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mundo')
    ap.add_argument('--altura', type=float, default=0.30,
                    help='altura del corte horizontal (por defecto 0.30)')
    ap.add_argument('--region', nargs=4, type=float, action='append',
                    metavar=('X0', 'Y0', 'X1', 'Y1'),
                    help='rectangulo de la red navegable; repetible. Un hueco '
                         'con los dos lados dentro de la red es PASO y se deja '
                         'abierto. Sin ninguna --region todo sale a sellar.')
    ap.add_argument('--max-vano', type=float, default=3.0,
                    help='mas ancho que esto no es una puerta (por defecto 3.0)')
    ap.add_argument('--xml', metavar='PREFIJO',
                    help='emitir por stdout los links de los vanos a sellar, '
                         'nombrados PREFIJO01, PREFIJO02... El prefijo debe '
                         'empezar por Limite_ para que el generador de mapas '
                         'los pinte como sinteticos.')
    args = ap.parse_args()

    P = paredes(args.mundo, args.altura)
    if not P:
        sys.exit(f"Ninguna pared cruza z = {args.altura:.2f} m. Revisar --altura.")
    print(f"{len(P)} paredes a z = {args.altura:.2f} m", file=sys.stderr)

    reg = args.region or []

    def dentro(x, y):
        return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in reg)

    final = buscar(P, args.max_vano)
    sellar = []
    print(f"\n{'ancho':>6} {'x':>9} {'y':>9} {'rumbo':>8}  veredicto  entre", file=sys.stderr)
    for d, cx, cy, yaw, n, k in final:
        nx, ny = -math.sin(yaw), math.cos(yaw)
        paso = dentro(cx + nx * 0.35, cy + ny * 0.35) and dentro(cx - nx * 0.35, cy - ny * 0.35)
        if not paso:
            sellar.append((d, cx, cy, yaw, n, k))
        print(f"{d:6.3f} {cx:9.3f} {cy:9.3f} {math.degrees(yaw):8.2f}  "
              f"{'PASO  ' if paso else 'SELLAR'}     {n} <-> {k}", file=sys.stderr)
    print(f"\n{len(final)} vanos -> {len(sellar)} a sellar, "
          f"{len(final) - len(sellar)} pasos", file=sys.stderr)
    if not reg:
        print("AVISO: sin --region no se distingue puerta de paso.", file=sys.stderr)

    if args.xml:
        for i, (d, cx, cy, yaw, n, k) in enumerate(sorted(sellar, key=lambda s: (s[1], s[2])), 1):
            sys.stdout.write(PIEZA.format(nom=f'{args.xml}{i:02d}', d=d, n=n, k=k,
                                          L=d + 2 * SOLAPE, cx=cx, cy=cy, yaw=yaw,
                                          g=GROSOR_PANEL, h=ALTO_PANEL,
                                          mitad=ALTO_PANEL / 2))


if __name__ == '__main__':
    main()
