#!/usr/bin/env python3
"""Tarjeta de acceso para el jurado: códigos QR para unirse a la red y abrir la página del sistema.

Genera una página PDF con tres códigos:
  1. la red Wi-Fi de los agentes, en el formato «WIFI:» que leen las cámaras de Android y de iPhone
     (el teléfono se une a la red sin escribir la clave);
  2. la página del sistema, http://<IP del portátil>:8000/, la que sirve servir_interfaz.py (la
     página encuentra sola a rosbridge en el puerto 9090 del mismo equipo);
  3. el repositorio del proyecto.

La IP del portátil la reparte el router y puede cambiar entre sesiones, así que la tarjeta se genera
el día de la prueba, con el portátil ya conectado a la red. La clave de la red no se guarda en el
repositorio: se pide al ejecutar, o se lee de la variable CLAVE_WIFI, y el PDF va a un archivo que
git ignora.

Uso, desde la raíz del repositorio, con el portátil en la red DEEPRACER:
    python3 herramientas/tarjeta_jurado.py
    python3 herramientas/tarjeta_jurado.py --ip 192.168.0.105        # para fijar la IP a mano
Escribe Documentos/acceso_jurado.pdf. Si está OpenCV, lee los tres códigos del PDF y comprueba que
dicen lo esperado.
"""
import argparse
import getpass
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPOSITORIO = ('https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-'
               'Navigation-Assistance-in-Multi-Level-Environments')


def ip_en_la_red():
    """La IP del portátil en 192.168.0.0/24, la subred de la red de los agentes."""
    salida = subprocess.run(['hostname', '-I'], capture_output=True, text=True).stdout.split()
    candidatas = [ip for ip in salida if re.fullmatch(r'192\.168\.0\.(\d+)', ip) and ip != '192.168.0.1']
    return candidatas[0] if candidatas else None


def escapar_wifi(texto):
    """El formato WIFI: reserva \\ ; , : y " y los escapa con una barra invertida."""
    return re.sub(r'([\\;,:"])', r'\\\1', texto)


def escapar_tex(texto):
    """Los caracteres especiales de TeX que el paquete qrcode admite escapados."""
    return ''.join('\\' + c if c in '\\{}#$%&_^~' else c for c in texto)


def texto_tex(texto):
    """El mismo texto, para imprimirlo en la página."""
    reemplazos = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '#': r'\#', '$': r'\$',
                  '%': r'\%', '&': r'\&', '_': r'\_', '^': r'\textasciicircum{}',
                  '~': r'\textasciitilde{}'}
    return ''.join(reemplazos.get(c, c) for c in texto)


def documento(red, clave, url_pagina):
    wifi = f'WIFI:T:WPA;S:{escapar_wifi(red)};P:{escapar_wifi(clave)};;'
    return wifi, rf"""\documentclass[11pt]{{article}}
\usepackage[T1]{{fontenc}}
\usepackage[utf8]{{inputenc}}
\usepackage[spanish]{{babel}}
\usepackage[letterpaper,margin=2cm]{{geometry}}
\usepackage{{helvet}}
\renewcommand{{\familydefault}}{{\sfdefault}}
\usepackage{{qrcode}}
\usepackage[hidelinks]{{hyperref}}
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\begin{{document}}
\begin{{center}}
{{\LARGE\bfseries Acceso al sistema}}\\[4pt]
{{\large Sistema colaborativo de robots móviles para asistencia de orientación\\
en entornos interiores con múltiples pisos}}
\end{{center}}
\vspace{{10mm}}
\begin{{minipage}}[t]{{0.48\textwidth}}\centering
{{\Large\bfseries 1. Conéctese a la red}}\\[5mm]
\qrcode[height=5.5cm]{{{escapar_tex(wifi)}}}\\[4mm]
Red: \textbf{{{texto_tex(red)}}}\\
Clave: \texttt{{{texto_tex(clave)}}}
\end{{minipage}}\hfill
\begin{{minipage}}[t]{{0.48\textwidth}}\centering
{{\Large\bfseries 2. Abra la página}}\\[5mm]
\qrcode[height=5.5cm]{{{escapar_tex(url_pagina)}}}\\[4mm]
\texttt{{{texto_tex(url_pagina)}}}
\end{{minipage}}
\vspace{{14mm}}

\begin{{minipage}}[t]{{0.62\textwidth}}
\textbf{{Si el teléfono avisa que la red no tiene internet}}, elija mantener la conexión: el
sistema funciona sin internet, dentro de la red de los agentes.\\[3mm]
\textbf{{Si la cámara abre el enlace en otra aplicación}}, ábralo en el navegador del teléfono
(Chrome o Safari).\\[3mm]
\textbf{{En la página}} elija el origen y el destino, siga al agente y, al llegar al otro piso,
confirme el cambio de piso con el botón.
\end{{minipage}}\hfill
\begin{{minipage}}[t]{{0.33\textwidth}}\centering
\qrcode[height=3.2cm]{{{escapar_tex(REPOSITORIO)}}}\\[2mm]
{{\small Repositorio del proyecto,\\ con toda su trazabilidad}}
\end{{minipage}}
\end{{document}}
"""


def comprobar(pdf, esperados):
    """Lee los códigos del PDF con OpenCV y compara con lo que se quiso escribir."""
    try:
        import cv2
    except ImportError:
        print('   OpenCV no está instalado: no se comprobó la lectura de los códigos')
        return True
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['pdftoppm', '-r', '200', '-png', str(pdf), f'{tmp}/p'], check=True)
        imagen = cv2.imread(sorted(Path(tmp).glob('p*.png'))[0].as_posix())
    ok, datos, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(imagen)
    leidos = sorted(d for d in datos if d) if ok else []
    faltan = sorted(set(esperados) - set(leidos))
    if faltan:
        print(f'   ATENCIÓN: {len(faltan)} de {len(esperados)} códigos no se leyeron como se esperaba')
        return False
    print(f'   los {len(esperados)} códigos se leen y dicen lo esperado')
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--red', default='DEEPRACER', help='nombre de la red Wi-Fi (SSID)')
    ap.add_argument('--ip', help='IP del portátil en la red; por omisión, la que tenga ahora')
    ap.add_argument('--puerto', type=int, default=8000, help='puerto de servir_interfaz.py')
    ap.add_argument('--salida', default=str(RAIZ / 'Documentos/acceso_jurado.pdf'))
    args = ap.parse_args()

    ip = args.ip or ip_en_la_red()
    if not ip:
        sys.exit('El portátil no tiene una IP 192.168.0.x: conéctelo a la red de los agentes o pase --ip.')
    clave = os.environ.get('CLAVE_WIFI') or getpass.getpass(f'Clave de la red {args.red}: ')
    if not clave:
        sys.exit('Sin clave no se puede armar el código de la red.')
    # El paquete qrcode de LaTeX codifica bien los signos de ASCII, pero no letras como la ñ o las
    # vocales con tilde (probado el 2026-10-27: la ñ salía como «~n»). Mejor avisar que imprimir un
    # código que no conecta.
    if any(not (32 <= ord(c) < 127) for c in clave + args.red):
        sys.exit('La clave o el nombre de la red tienen letras fuera de ASCII (ñ, tildes): el código QR '
                 'saldría mal. El jurado tendría que escribir la clave a mano.')
    url = f'http://{ip}:{args.puerto}/'
    wifi, tex = documento(args.red, clave, url)

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / 'tarjeta.tex').write_text(tex, encoding='utf-8')
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'tarjeta.tex'], cwd=tmp,
                           capture_output=True, text=True)
        if r.returncode != 0 or not (Path(tmp) / 'tarjeta.pdf').exists():
            sys.exit('pdflatex no pudo armar la tarjeta:\n' + r.stdout[-1500:])
        Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(tmp) / 'tarjeta.pdf', args.salida)

    print(f'Tarjeta en {args.salida}')
    print(f'   red {args.red}, página {url}')
    if not comprobar(args.salida, [wifi, url, REPOSITORIO]):
        sys.exit(1)


if __name__ == '__main__':
    main()
