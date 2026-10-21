#!/usr/bin/env python3
"""Genera las páginas «semana a semana» del sitio (sitio/paginas/semanas/).

Una página por semana, de la 10 (el primer entregable del repositorio) a la última, con lo que se hizo
(de Documentos/DocumentoFinal/CRONOLOGIA.md), el avance de los cuatro objetivos al cierre de la semana,
las figuras del entregable o de las capturas de la semana, lo que se concluyó (la sección de
conclusiones del entregable, en .md, .tex o .pdf) y los enlaces al informe completo y a la evidencia.
También escribe el índice de semanas, la cuadrícula de la portada y la entrada del menú.

Uso, desde cualquier carpeta:  python3 sitio/generar_semanas.py
Necesita Pillow y, para los entregables que solo existen en PDF, pdftotext (poppler-utils).
"""
import glob, os, re, shutil, subprocess, tempfile, unicodedata
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(RAIZ, 'Documentos')
EVI = os.path.join(DOC, 'Evidencia')
ENT = os.path.join(DOC, 'Entregables')
SITIO = os.path.join(RAIZ, 'sitio')
SALIDA = os.path.join(SITIO, 'paginas', 'semanas')
IMG = os.path.join(SALIDA, 'img')
GITHUB = ('https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-'
          'Assistance-in-Multi-Level-Environments/blob/main/')
PRIMERA = 10          # primera semana con entregable en el repositorio
MAX_FIGURAS = 6
EXCLUIR = re.compile(r'/S15_|logo', re.I)   # capturas de la semana 15 (otro simulador, ajeno al proyecto) y logotipos
TEMPORAL = tempfile.mkdtemp(prefix='semanas_')

# Fase de cada semana, como la declara su entregable.
FASES = [
    ('Fases 2 y 3 · requisitos y diseño conceptual', range(10, 13)),
    ('Fase 4 · desarrollo progresivo de la solución', range(13, 17)),
    ('Fase 5 · integración del sistema y pruebas', range(17, 27)),
    ('Fase 6 · campaña, análisis y escritura', range(27, 33)),
]
OBJETIVOS = ['Arquitectura', 'Plataforma robótica', 'Interfaz', 'Evaluación']
# Miniatura de la tarjeta cuando la primera figura no es la más representativa de la semana.
PORTADA = {17: 'S17_dos_objetivos_succeeded', 19: 'S19_rviz_gazebo_maniobra', 22: 'S22_hri_mision_sigueme'}


def fase(n):
    return next(nombre for nombre, semanas in FASES if n in semanas)


def leer(ruta):
    with open(ruta, encoding='utf-8', errors='replace') as f:
        return f.read()


def informe_de(n, ext):
    ruta = os.path.join(ENT, f'Entregable_semana_{n}.{ext}')
    return ruta if os.path.exists(ruta) else None


# ------------------------------------------------------------------ cronología
def limpiar_vineta(v):
    # Las referencias a archivos de captura sobran en el sitio: la imagen ya se muestra.
    v = re.sub(r'\s*\(`[^`]+\.(?:png|jpe?g)`[^)]*\)', '', v)
    v = re.sub(r'\s*\(commits? [^)]*\)', '', v)
    return v


def semanas_de_cronologia():
    texto = leer(os.path.join(DOC, 'DocumentoFinal', 'CRONOLOGIA.md'))
    semanas = {}
    for bloque in re.split(r'\n(?=### )', texto):
        m = re.match(r'### S(\d+) \(([^)]*)\)( y receso)?:? ?([^\n]*)', bloque)
        if not m:
            continue
        n, fechas = int(m.group(1)), m.group(2)
        titulo = m.group(4).strip() or ('receso de mitad de año' if m.group(3) else '')
        cuerpo = bloque.split('\n', 1)[1]
        cuerpo = re.split(r'\nFuente: |\n---', cuerpo)[0]
        vinetas, actual = [], None
        for linea in cuerpo.splitlines():
            if linea.startswith('- '):
                if actual:
                    vinetas.append(actual)
                actual = linea[2:].strip()
            elif linea.startswith('  ') and actual is not None:
                actual += ' ' + linea.strip()
        if actual:
            vinetas.append(actual)
        semanas[n] = {'fechas': fechas, 'titulo': titulo[0].upper() + titulo[1:],
                      'hecho': [limpiar_vineta(v) for v in vinetas]}
    return semanas


# ------------------------------------------------------------------ pies de foto
def pies_de_foto():
    pies = {}
    for linea in leer(os.path.join(EVI, 'README.md')).splitlines():
        m = re.match(r'\| `([^`]+\.(?:png|jpe?g))` \| ([^|]+)\|', linea)
        if m:
            pies[m.group(1)] = m.group(2).strip()
    texto = leer(os.path.join(EVI, 'CAPTURAS_POR_FASE.md'))
    for m in re.finditer(r'### ([^\n]+)\n\n!\[[^\]]*\]\(([^)]+)\)', texto):
        pies[os.path.basename(m.group(2))] = m.group(1).strip()
    # Lo demás, del texto alternativo con que la cita su documento de evidencia.
    for ruta in glob.glob(os.path.join(EVI, '*.md')):
        for m in re.finditer(r'!\[([^\]]+)\]\(([^)\s]+)\)', leer(ruta)):
            pies.setdefault(os.path.basename(m.group(2)), m.group(1).strip())
    return pies


# ------------------------------------------------------------------ texto de LaTeX y de PDF
def llaves(s, i):
    """Contenido entre la llave que abre en s[i] y su pareja."""
    prof = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            prof += 1
        elif s[j] == '}':
            prof -= 1
            if prof == 0:
                return s[i + 1:j]
    return s[i + 1:]


def tex_a_texto(s):
    s = re.sub(r'(?<!\\)%.*', '', s)
    s = s.replace('~', ' ').replace('\\,', ' ').replace('---', '—').replace('--', '–')
    s = re.sub(r"``|''", '"', s)
    s = re.sub(r'\\(?:cite|ref|label|autoref|eqref)\{[^}]*\}', '', s)
    s = re.sub(r'\\(?:begin|end)\{[^}]*\}', '', s)
    s = s.replace('$\\pm$', '±').replace('$\\rightarrow$', '→').replace('\\rightarrow', '→')
    s = s.replace('$\\times$', '×').replace('\\times', '×').replace('$\\approx$', '≈')
    s = re.sub(r'\$([^$]*)\$', r'\1', s)
    s = s.replace('\\%', '%').replace('\\_', '_').replace('\\&', '&').replace('\\#', '#')
    s = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', '', s)
    s = s.replace('{', '').replace('}', '').replace('\\', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r' ([,.;:)])', r'\1', s)


def pdf_a_texto(ruta):
    t = subprocess.run(['pdftotext', ruta, '-'], capture_output=True, text=True).stdout
    t = t.replace('ı́', 'í').replace('ı', 'i').replace('\f', '\n')
    return unicodedata.normalize('NFC', t)


# ------------------------------------------------------------------ conclusiones
def conclusiones(n):
    md, tex, pdf = (informe_de(n, e) for e in ('md', 'tex', 'pdf'))
    if md:
        m = re.search(r'\n## (?:\d+\.\s*)?Conclusiones[^\n]*\n(.*?)(?=\n## |\Z)', leer(md), re.S)
        if m:
            items = re.split(r'\n(?=\d+\.\s)', '\n' + m.group(1).strip())
            return [re.sub(r'\s+', ' ', re.sub(r'^\d+\.\s*', '', i)).strip() for i in items if i.strip()]
    if tex:
        m = re.search(r'\\section\*?\{Conclusiones[^}]*\}(.*?)(?=\\section|\\begin\{thebibliography\}|'
                      r'\\printbibliography|\\end\{document\})', leer(tex), re.S)
        if m:
            cuerpo = m.group(1)
            partes = re.split(r'\\item', cuerpo)[1:] if '\\item' in cuerpo else re.split(r'\n\s*\n', cuerpo)
            return [t for t in (tex_a_texto(p) for p in partes) if len(t) > 20]
    if pdf:
        m = re.search(r'Conclusiones de la Semana\s*\n(.*?)(?=\nReferencias|\Z)', pdf_a_texto(pdf), re.S)
        if m:
            salida = []
            for p in re.split(r'\n\s*\n', m.group(1)):
                p = re.sub(r'-\n(?=[a-záéíóúñ])', '', p)
                p = re.sub(r'\s+', ' ', p).strip()
                if salida and p[:1].islower():      # párrafo partido por un cambio de página
                    salida[-1] += ' ' + p
                elif len(p) > 60:
                    salida.append(p)
            return salida
    return []


# ------------------------------------------------------------------ avance de los objetivos
def avance(n):
    """[(antes, despues)] de los cuatro objetivos, si el entregable trae la tabla de avance."""
    md, tex = informe_de(n, 'md'), informe_de(n, 'tex')
    filas = {}
    if md:
        for m in re.finditer(r'^\| ?OE([1-4]) ?\| ([^|]+)\|', leer(md), re.M):
            filas.setdefault(int(m.group(1)), m.group(2))
    elif tex:
        for m in re.finditer(r'^\s*OE([1-4]) & ([^&]+)&', leer(tex), re.M):
            filas.setdefault(int(m.group(1)), m.group(2))
    if len(filas) < 4:
        return None
    salida = []
    for k in range(1, 5):
        cifras = [int(x) for x in re.findall(r'(\d+)\s*\\?%', filas[k])]
        if not cifras:
            return None
        salida.append((cifras[0], cifras[-1]))
    return salida


# ------------------------------------------------------------------ figuras
def buscar_imagen(nombre):
    for base in (EVI, ENT, os.path.join(DOC, 'DocumentoFinal', 'imagenes'), DOC):
        for candidato in (nombre, os.path.basename(nombre)):
            ruta = os.path.normpath(os.path.join(base, candidato))
            for ext in ('', '.png', '.jpg', '.jpeg'):
                if os.path.isfile(ruta + ext):
                    return ruta + ext
    return None


def capturas_del_indice():
    """Capturas que el índice de Evidencia agrupa bajo «## Semana N», con su texto alternativo."""
    por_semana, n = {}, None
    for linea in leer(os.path.join(EVI, 'README.md')).splitlines():
        if linea.startswith('## '):
            m = re.match(r'## Semana (\d+)', linea)
            n = int(m.group(1)) if m else None
        elif n is not None:
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', linea)
            if m and (ruta := buscar_imagen(m.group(2))):
                por_semana.setdefault(n, []).append((ruta, m.group(1)))
    return por_semana


# Figuras de semanas cuyo informe no trae imágenes. «git:» lee el archivo de la versión actual del
# repositorio cuando no está en la copia de trabajo (Robot/aws-deepracer es un enlace al espacio de trabajo).
EXTRA = {
    15: [('git:Robot/aws-deepracer/deepracer_bringup/maps/primer_piso.pgm',
          'Primer mapa del primer piso con SLAM (23 de mayo). En la semana 17 se invalidó: los ajustes '
          'del mapeo de esas semanas nunca se habían ejecutado')],
    21: [('Documentos/DocumentoFinal/imagenes/corrida_simulacion.png',
          'Una misión de la campaña en simulación: el primer plan del navegador, la pose estimada y la '
          'odometría cruda, cuya separación es la deriva que la localización corrige contra el mapa')],
    27: [('Documentos/DocumentoFinal/imagenes/campana_vehiculos_etapas.png',
          'Duración de cada etapa en las nueve misiones con los dos vehículos, según las marcas del coordinador')],
}


def extra(n):
    salida = []
    for origen, pie in EXTRA.get(n, []):
        if origen.startswith('git:'):
            destino = os.path.join(TEMPORAL, os.path.basename(origen[4:]))
            with open(destino, 'wb') as f:
                f.write(subprocess.run(['git', '-C', RAIZ, 'show', 'HEAD:' + origen[4:]],
                                       capture_output=True, check=True).stdout)
            salida.append((destino, pie))
        else:
            salida.append((os.path.join(RAIZ, origen), pie))
    return salida


def figuras(n, pies, indice):
    """Figuras del entregable con su pie y, si faltan, las capturas de la semana en Evidencia."""
    figs = []
    md, tex = informe_de(n, 'md'), informe_de(n, 'tex')
    if md:
        for m in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', leer(md)):
            ruta = buscar_imagen(m.group(2))
            if ruta:
                pie = re.sub(r'^Figura \d+\.\s*', '', m.group(1))
                figs.append((ruta, pies.get(os.path.basename(ruta), pie)))
    elif tex:
        for m in re.finditer(r'\\begin\{figure\}(.*?)\\end\{figure\}', leer(tex), re.S):
            bloque = m.group(1)
            g = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', bloque)
            ruta = buscar_imagen(g.group(1)) if g else None
            if not ruta:
                continue
            c = bloque.find('\\caption{')
            pie = tex_a_texto(llaves(bloque, c + 8)) if c >= 0 else ''
            figs.append((ruta, pie))
    figs += extra(n)
    # Las capturas de la semana, en el orden del catálogo por fase (las que no están en él, al final).
    catalogo = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', leer(os.path.join(EVI, 'CAPTURAS_POR_FASE.md')))
    capturas = sorted((p for p in glob.glob(os.path.join(EVI, f'S{n}_*')) if re.search(r'\.(png|jpe?g)$', p, re.I)),
                      key=lambda p: (catalogo.index(os.path.basename(p)) if os.path.basename(p) in catalogo
                                     else len(catalogo), p))
    candidatas = indice.get(n, []) + [(r, pies.get(os.path.basename(r), '')) for r in capturas]
    for ruta, pie in candidatas:
        if any(os.path.samefile(ruta, f[0]) for f in figs):
            continue
        figs.append((ruta, pie))
    # Una captura sin pie no se publica: no se sabría qué muestra.
    return [f for f in figs if f[1] and not EXCLUIR.search(f[0])][:MAX_FIGURAS]


def copiar_imagen(ruta, destino):
    with Image.open(ruta) as im:
        im = im.convert('RGB')
        if im.width > 1400:
            im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
        im.save(destino, 'JPEG', quality=82, optimize=True)


# ------------------------------------------------------------------ enlaces
def evidencias(n):
    salida = []
    for ruta in sorted(glob.glob(os.path.join(EVI, f'S{n}_*.md'))):
        titulo = next((l for l in leer(ruta).splitlines() if l.startswith('# ')), os.path.basename(ruta))
        salida.append((titulo.lstrip('# ').strip(), os.path.relpath(ruta, RAIZ)))
    return salida


def informes(n):
    nombres = {'md': 'Informe completo', 'pdf': 'Informe en PDF', 'tex': 'Fuente en LaTeX'}
    return [(nombres[e], os.path.relpath(r, RAIZ)) for e in ('md', 'pdf', 'tex') if (r := informe_de(n, e))]


# ------------------------------------------------------------------ páginas
def bloque_avance(av, n):
    l = ['## Avance de los objetivos al cierre de la semana', '', '<div class="avance">']
    for nombre, (antes, despues) in zip(OBJETIVOS, av):
        cambio = f'<span class="sube">+{despues - antes}</span>' if despues > antes else ''
        l.append(f'<div class="objetivo"><span class="nombre">{nombre}</span>'
                 f'<span class="barra"><span class="previo" style="width:{antes}%"></span>'
                 f'<span class="nuevo" style="left:{antes}%;width:{despues - antes}%"></span></span>'
                 f'<span class="valor">{despues} %{cambio}</span></div>')
    l += ['</div>', '', '<p class="nota">En color claro, lo que avanzó esta semana. Las cifras son las del '
          f'informe de la semana {n}.</p>', '']
    return l


def pagina(n, s, figs, concl, av, evid, inf, previa, siguiente):
    l = ['---', f'title: Semana {n}', 'hide:', '  - toc', '---', '',
         '<div class="semana-cabecera" markdown>',
         f'<div class="etiqueta">{fase(n)}</div>', '',
         f'# Semana {n}: {s["titulo"]}', '',
         f'<p class="fechas">{s["fechas"].capitalize()} de 2026</p>', '</div>', '']
    if s['hecho']:
        l += ['## Lo que se hizo', '', '<div class="hechos" markdown>', '']
        l += [f'- {v}' for v in s['hecho']] + ['', '</div>', '']
    if av:
        l += bloque_avance(av, n)
    if figs:
        l += ['## En imágenes', '', '<div class="galeria" markdown>', '']
        for archivo, pie in figs:
            alt = (pie or f'Figura de la semana {n}').replace('"', "'").replace('[', '(').replace(']', ')')
            l += ['<figure markdown>', f'[![{alt}](img/{archivo}){{ loading=lazy }}](img/{archivo})']
            if pie:
                l.append(f'<figcaption>{pie}</figcaption>')
            l += ['</figure>', '']
        l += ['</div>', '']
    if concl:
        l += ['## Lo que se concluyó', '', '<div class="conclusiones" markdown>', '']
        if len(concl) == 1:
            l += [concl[0], '']
        else:
            l += [f'{i}. {c}' for i, c in enumerate(concl, 1)] + ['']
        l += ['</div>', '']
    l += ['## Para leer en detalle', '']
    if inf:
        l += [' '.join(f'[{nombre}]({GITHUB}{ruta}){{ .md-button }}' for nombre, ruta in inf), '']
    else:
        l += ['Esta semana no tiene informe en el repositorio.', '']
    if evid:
        l += ['Evidencia de la semana:', ''] + [f'- [{t}]({GITHUB}{r})' for t, r in evid] + ['']
    nav = []
    if previa:
        nav.append(f'[:material-arrow-left: Semana {previa}](s{previa:02d}.md)')
    nav.append('[Todas las semanas](index.md)')
    if siguiente:
        nav.append(f'[Semana {siguiente} :material-arrow-right:](s{siguiente:02d}.md)')
    l += ['<div class="semana-nav" markdown>', '', ' · '.join(nav), '', '</div>', '']
    return '\n'.join(l)


def cuadricula(semanas, miniaturas, prefijo):
    """Tarjetas agrupadas por fase; prefijo es la ruta de la carpeta semanas/ desde la página."""
    l = []
    for nombre, rango in FASES:
        numeros = [n for n in sorted(semanas) if n in rango]
        if not numeros:
            continue
        l += [f'### {nombre}', '', '<div class="semanas-grid">']
        for n in numeros:
            s = semanas[n]
            mini = (f'<img src="{prefijo}img/{miniaturas[n]}" alt="" loading="lazy">' if n in miniaturas
                    else '<span class="sin-imagen"></span>')
            l.append(f'<a class="semana-tarjeta" href="{prefijo}s{n:02d}/">{mini}<span class="texto">'
                     f'<span class="num">Semana {n} · {s["fechas"]}</span>'
                     f'<span class="titulo">{s["titulo"]}</span></span></a>')
        l += ['</div>', '']
    return l


def reemplazar_entre(ruta, inicio, fin, contenido):
    texto = leer(ruta)
    a, b = texto.index(inicio) + len(inicio), texto.index(fin)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(texto[:a] + '\n' + contenido + texto[b:])


def main():
    semanas = {n: s for n, s in semanas_de_cronologia().items() if n >= PRIMERA}
    pies, indice = pies_de_foto(), capturas_del_indice()
    if os.path.isdir(SALIDA):
        shutil.rmtree(SALIDA)
    os.makedirs(IMG)
    orden = sorted(semanas)
    miniaturas = {}
    for i, n in enumerate(orden):
        copiadas = []
        for k, (ruta, pie) in enumerate(figuras(n, pies, indice), 1):
            archivo = f's{n:02d}_{k}.jpg'
            copiar_imagen(ruta, os.path.join(IMG, archivo))
            copiadas.append((archivo, pie))
            if PORTADA.get(n, '\0') in ruta:
                miniaturas[n] = archivo
        if copiadas:
            miniaturas.setdefault(n, copiadas[0][0])
        concl, av = conclusiones(n), avance(n)
        previa = orden[i - 1] if i > 0 else None
        siguiente = orden[i + 1] if i + 1 < len(orden) else None
        with open(os.path.join(SALIDA, f's{n:02d}.md'), 'w', encoding='utf-8') as f:
            f.write(pagina(n, semanas[n], copiadas, concl, av, evidencias(n), informes(n), previa, siguiente))
        print(f'S{n}: {len(semanas[n]["hecho"])} puntos, {len(copiadas)} figuras, {len(concl)} conclusiones, '
              f'avance {"sí" if av else "no"}')
    with open(os.path.join(SALIDA, 'index.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(['---', 'title: Semana a semana', 'hide:', '  - navigation', '---', '',
                           '# Semana a semana', '',
                           'Cada semana tiene su página con lo que se hizo, las imágenes y lo que se concluyó. '
                           'El detalle completo está en el informe de la semana, enlazado al final de cada página.',
                           ''] + cuadricula(semanas, miniaturas, '')))
    reemplazar_entre(os.path.join(SITIO, 'paginas', 'index.md'), '<!-- semanas:inicio -->',
                     '<!-- semanas:fin -->', '\n'.join(cuadricula(semanas, miniaturas, 'semanas/')))
    menu = ['  - Semana a semana:', '      - semanas/index.md']
    menu += [f'      - Semana {n}: semanas/s{n:02d}.md' for n in orden]
    reemplazar_entre(os.path.join(SITIO, 'mkdocs.yml'), '# semanas:inicio', '  # semanas:fin',
                     '\n'.join(menu) + '\n')


if __name__ == '__main__':
    main()
