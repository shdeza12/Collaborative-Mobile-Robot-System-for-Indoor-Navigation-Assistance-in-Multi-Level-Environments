#!/usr/bin/env python3
"""Arma cambios_recorte.pdf: solo los capítulos recortados, con los cambios marcados.

Compara main.tex con main_recorte.tex con latexdiff, compila el resultado
completo (para que las remisiones y las citas queden con su número real) y
extrae las páginas de los capítulos que tienen versión en capitulos_recorte/.
Lo quitado sale en rojo tachado y lo nuevo en azul subrayado.

Uso, desde Documentos/DocumentoFinal:  python3 cambios_recorte.py
"""
import glob, os, re, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)

# Archivo de capitulos_recorte/ -> títulos de capítulo que ocupa en el índice.
CAPITULOS = {
    '02-resumen-abstract': ['Resumen', 'Abstract'],
    '03-glosario-abreviaturas': ['Glosario', 'Abreviaturas'],
    '04-introduccion': ['INTRODUCCIÓN'],
    '05-contextualizacion': ['Contextualización'],
    '06-marco-referencial': ['Marco referencial'],
    '07-desarrollo': ['Desarrollo'],
    '08-resultados': ['Resultados'],
    '09-conclusiones': ['CONCLUSIONES'],
    '10-trabajos-futuros': ['TRABAJOS FUTUROS'],
}


def correr(*cmd):
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def texto_pagina(pdf, p):
    r = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), pdf, '-'], capture_output=True, text=True)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]


def titulo_de(resto):
    """Título de una entrada del índice: el primer grupo entre llaves, sin el número."""
    nivel, fin = 1, 0
    for i, c in enumerate(resto):
        nivel += (c == '{') - (c == '}')
        if nivel == 0:
            fin = i
            break
    t = re.sub(r'\\numberline\s*\{[^}]*\}', '', resto[:fin])
    return re.sub(r'[{}]', '', t).strip()


def main():
    with open('main_diff.tex', 'w', encoding='utf-8') as f:
        subprocess.run(['latexdiff', '--flatten', '--encoding=utf8', '--math-markup=whole',
                        'main.tex', 'main_recorte.tex'], stdout=f, stderr=subprocess.DEVNULL, check=True)
    for paso in (['pdflatex', '-interaction=nonstopmode', 'main_diff'], ['biber', 'main_diff'],
                 ['pdflatex', '-interaction=nonstopmode', 'main_diff'],
                 ['pdflatex', '-interaction=nonstopmode', 'main_diff']):
        correr(*paso)

    # Orden de los capítulos según el índice, para saber dónde termina cada uno.
    orden = []
    for linea in open('main_diff.toc', encoding='utf-8'):
        if linea.startswith('\\contentsline {chapter}{'):
            orden.append(titulo_de(linea[len('\\contentsline {chapter}{'):]))

    total = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', 'main_diff.pdf'],
                                                             capture_output=True, text=True).stdout).group(1))
    # Página física en que empieza cada capítulo: la primera cuyo encabezado es su título.
    inicio = {}
    for p in range(1, total + 1):
        lineas = texto_pagina('main_diff.pdf', p)[:3]
        for titulo in orden:
            if titulo not in inicio and any(re.sub(r'^\d+\.\s*', '', l).upper() == titulo.upper() for l in lineas):
                inicio[titulo] = p
                break

    tramos = []
    for archivo in sorted(glob.glob('capitulos_recorte/*.tex')):
        clave = os.path.splitext(os.path.basename(archivo))[0]
        for titulo in CAPITULOS.get(clave, []):
            if titulo not in inicio:
                sys.exit(f'No encontré la página de «{titulo}» en main_diff.pdf')
            siguientes = [inicio[t] for t in orden[orden.index(titulo) + 1:] if t in inicio]
            tramos.append((inicio[titulo], (min(siguientes) - 1) if siguientes else total))

    with tempfile.TemporaryDirectory() as tmp:
        paginas = []
        for a, b in tramos:
            subprocess.run(['pdfseparate', '-f', str(a), '-l', str(b), 'main_diff.pdf',
                            os.path.join(tmp, 'p%04d.pdf')], check=True, stderr=subprocess.DEVNULL)
            paginas += [os.path.join(tmp, f'p{p:04d}.pdf') for p in range(a, b + 1)]
        subprocess.run(['pdfunite', *paginas, 'cambios_recorte.pdf'], check=True, stderr=subprocess.DEVNULL)

    for ext in ('aux', 'bbl', 'bcf', 'blg', 'lof', 'log', 'lot', 'out', 'run.xml', 'toc', 'pdf', 'tex'):
        if os.path.exists(f'main_diff.{ext}'):
            os.remove(f'main_diff.{ext}')
    print('cambios_recorte.pdf:', ', '.join(f'págs. {a}-{b} del documento con cambios' for a, b in tramos))


if __name__ == '__main__':
    main()
