#!/usr/bin/env python3
"""Mapas de navegación de los pisos de Gregorio y Catalayud para la propuesta del capítulo de desarrollo.

Dibuja cada mapa tal como lo usa Nav2 (libre en blanco, ocupado en negro, desconocido en gris), con el
estilo del mapa del piso 4 que ya está en el documento, y marca los puntos del catálogo. En Catalayud
los puntos se colocan sobre la pared, en la abscisa que da el levantamiento; en Gregorio, en la pose
del catálogo.
Uso: python3 herramientas/figura_mapas_entornos.py . Documentos/DocumentoFinal/imagenes
"""
import sys, yaml
from PIL import Image, ImageDraw, ImageFont

RAIZ, SAL = sys.argv[1], sys.argv[2]
MAPAS = RAIZ + '/Robot/aws-deepracer/deepracer_bringup/maps/'
LETRA = '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'
GRIS, NEGRO, BLANCO = (205, 205, 205), (0, 0, 0), (255, 255, 255)
COLOR = {'salon': (192, 96, 16), 'casilleros': (16, 104, 176), 'ascensor': (208, 0, 0),
         'papelera': (0, 128, 0), 'escalera': (192, 0, 160), 'texto': (60, 60, 60)}


def cargar(nombre):
    meta = yaml.safe_load(open(MAPAS + nombre + '.yaml', encoding='utf-8'))
    im = Image.open(MAPAS + meta['image']).convert('L')
    return im, meta['resolution'], meta['origin'][:2]


def pintar(nombre, escala, margen_m, puntos, rotulo, letra):
    FUENTE = ImageFont.truetype(LETRA, letra)
    FUENTE_PISO = ImageFont.truetype(LETRA, round(letra * 1.15))
    im, res, (ox, oy) = cargar(nombre)
    # Borde gris para que el recorte con margen nunca salga de la imagen.
    B = 60
    fondo = Image.new('L', (im.size[0] + 2 * B, im.size[1] + 2 * B), 205)
    fondo.paste(im, (B, B)); im = fondo; ox -= B * res; oy -= B * res
    W, H = im.size
    px = im.load()
    conocidos = [(x, y) for y in range(H) for x in range(W) if px[x, y] != 205]
    x0 = min(p[0] for p in conocidos); x1 = max(p[0] for p in conocidos)
    y0 = min(p[1] for p in conocidos); y1 = max(p[1] for p in conocidos)
    m = round(margen_m / res)
    caja = (x0 - m, y0 - m - round(letra * 1.4 / escala), x1 + m + 1, y1 + m + 1)
    color = Image.new('RGB', (W, H))
    cp = color.load()
    for y in range(H):
        for x in range(W):
            v = px[x, y]
            cp[x, y] = NEGRO if v < 100 else (BLANCO if v > 230 else GRIS)
    rec = color.crop(caja)
    rec = rec.resize((rec.size[0] * escala, rec.size[1] * escala), Image.NEAREST)
    d = ImageDraw.Draw(rec)

    def a_pixel(xm, ym):
        i = (xm - ox) / res
        j = H - (ym - oy) / res
        return (i - caja[0]) * escala, (j - caja[1]) * escala

    def libre(i, j):
        return px[int(i), int(j)] > 230

    for p in puntos:
        if p.get('pared'):
            # Se recorre la columna desde el centro del pasillo hasta la primera celda ocupada.
            i = int((p['x'] - ox) / res)
            j = int(H - (1.2 - oy) / res)
            paso = -1 if p['pared'] == 'este' else 1
            while 0 < j < H - 1 and libre(i, j + paso):
                j += paso
            j += paso * 0.6
            u, v = (i + 0.5 - caja[0]) * escala, (j + 0.5 - caja[1]) * escala
        else:
            u, v = a_pixel(p['x'], p['y'])
        c = COLOR[p['tipo']]
        r = 9
        d.ellipse((u - r - 2, v - r - 2, u + r + 2, v + r + 2), fill=BLANCO)
        d.ellipse((u - r, v - r, u + r, v + r), fill=c)
        ancho = d.textlength(p['texto'], font=FUENTE)
        abajo = p.get('rotulo_abajo', p.get('pared') == 'este')
        alto = letra * 1.15
        ty = v + r + 6 if abajo else v - r - 6 - alto
        # El rótulo se acomoda dentro del espacio libre, sin pisar paredes: se busca, alejándose del
        # punto, la primera altura en la que todo el recuadro del texto cae sobre celdas libres.
        col = int(u) // escala + caja[0]
        def tramo(fila):
            if not libre(col, fila):
                return None
            izq = der = col
            while izq > 0 and libre(izq - 1, fila): izq -= 1
            while der < W - 1 and libre(der + 1, fila): der += 1
            return izq, der
        tx = u - ancho / 2
        for paso in range(0, 40):
            yy = ty + (paso * 4 if abajo else -paso * 4)
            filas = range(int(yy) // escala + caja[1], int(yy + alto) // escala + caja[1] + 1)
            tramos = [tramo(f) for f in filas]
            if None in tramos:
                continue
            lo = (max(t[0] for t in tramos) - caja[0]) * escala + 3
            hi = (min(t[1] for t in tramos) + 1 - caja[0]) * escala - 3
            if hi - lo >= ancho:
                tx = min(max(u - ancho / 2, lo), hi - ancho); ty = yy
                break
        if p.get('fuera'):
            # Rótulo a la derecha, pasada la pared más cercana, cuando el recinto es más angosto que el texto.
            i = int(u) // escala + caja[0]; j = int(v) // escala + caja[1]
            while i < W - 1 and px[i, j] > 100: i += 1
            while i < W - 1 and px[i, j] <= 100: i += 1
            tx = (i - caja[0]) * escala + 12; ty = v - alto / 2
        d.text((tx, ty), p['texto'], font=FUENTE, fill=c)
    d.text((12, 6), rotulo, font=FUENTE_PISO, fill=COLOR['texto'])
    return rec


def apilar(imagenes, salida, sep=18):
    W = max(i.size[0] for i in imagenes)
    H = sum(i.size[1] for i in imagenes) + sep * (len(imagenes) - 1)
    lienzo = Image.new('RGB', (W, H), BLANCO)
    y = 0
    for i in imagenes:
        lienzo.paste(i, (0, y)); y += i.size[1] + sep
    lienzo.save(salida, optimize=True)
    print(salida, lienzo.size)


# ------------------------------------------------------------ Catalayud ---
# Abscisas desde el extremo norte, tomadas del levantamiento (generar_piso_desde_medidas.py)
# y del catálogo puntos_interes_pisos34.yaml.
def catalayud(piso, salones, casilleros, ascensor, papelera, escalera):
    pts = [dict(x=x, pared='este', tipo='salon', texto=f'Salón {n}') for n, x in salones]
    pts += [dict(x=casilleros, pared='oeste', tipo='casilleros', texto='Casilleros'),
            dict(x=ascensor, pared='oeste', tipo='ascensor', texto='Ascensor'),
            dict(x=papelera, pared='oeste', tipo='papelera', texto='Papelera'),
            dict(x=escalera, pared='oeste', tipo='escalera', texto='Escalera')]
    return pintar(f'piso{piso}', 4, 0.5, pts, f'Piso {piso}', 27)

p3 = catalayud(3, [(301, 6.20), (302, 9.31), (303, 17.22)], 6.59 + 9.10 / 2, 16.535,
               6.59 + 9.10 + 0.33 + 1.03 + 2.29 + 0.695 / 2, 22.10)
p4 = catalayud(4, [(401, 6.20), (402, 9.31), (403, 17.22)], 6.34 + 3.00 / 2, 16.385,
               6.34 + 3.00 + 6.53 + 1.03 + 2.29 + 0.695 / 2, 24.385)
apilar([p3, p4], SAL + '/mapas_catalayud.png')

# ------------------------------------------------------------- Gregorio ---
cat = yaml.safe_load(open(RAIZ + '/Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml', encoding='utf-8'))['puntos']
def pose(nivel, nombre):
    p = next(q for q in cat if q['nivel'] == nivel and q['nombre'] == nombre)['pose']
    return p['x'], p['y']
g2 = pintar('mundo_definitivo_piso1', 3, 0.6,
            [dict(zip(('x', 'y'), pose(1, 'Escaleras')), tipo='escalera', texto='Escalera', fuera=True)], 'Piso 2', 36)
g3 = pintar('mundo_definitivo_piso2', 3, 0.6,
            [dict(zip(('x', 'y'), pose(2, 'Escaleras')), tipo='escalera', texto='Escalera', rotulo_abajo=False),
             dict(zip(('x', 'y'), pose(2, 'IEEE')), tipo='salon', texto='IEEE', rotulo_abajo=False),
             dict(zip(('x', 'y'), pose(2, 'Lab. Sistemas 313')), tipo='salon', texto='Lab. Sistemas 313', fuera=True)],
            'Piso 3', 36)
apilar([g2, g3], SAL + '/mapas_gregorio.png')
