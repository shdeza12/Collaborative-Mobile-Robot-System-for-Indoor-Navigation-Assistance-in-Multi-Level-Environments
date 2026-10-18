#!/usr/bin/env python3
"""Prueba de servir_interfaz.py: la pagina no se queda vieja en el telefono.

    python3 herramientas/prueba_servir_interfaz.py

El 16-oct, en campo, el telefono siguio mostrando el app.js anterior despues
de corregirlo: 'python3 -m http.server' solo manda Last-Modified, y con eso el
navegador guarda la pagina y sus scripts por dias (el 10 % de su antiguedad)
sin volver a preguntar. Al recargar solo revalidaba index.html. Reproducido el
18-oct en el navegador del portatil.

Lo que se comprueba aqui es lo que lo evita: todas las respuestas llevan
'Cache-Control: no-cache', que obliga a preguntar al servidor antes de usar la
copia guardada, y la pregunta sigue siendo barata (304 sin cuerpo si el
archivo no cambio). No necesita ROS.
"""
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "herramientas", "servir_interfaz.py")
fallos = 0


def check(nombre, ok, detalle=""):
    global fallos
    fallos += not ok
    print(f"  [{'OK ' if ok else 'MAL'}] {nombre} {detalle}")


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pedir(url, cabeceras=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cabeceras or {})) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), b""


def main():
    if not os.path.exists(SERVIDOR):
        check("existe herramientas/servir_interfaz.py", False)
        sys.exit(1)
    puerto = puerto_libre()
    proc = subprocess.Popen([sys.executable, SERVIDOR, str(puerto)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{puerto}"
        for _ in range(50):
            try:
                pedir(base + "/")
                break
            except OSError:
                time.sleep(0.1)
        for ruta in ["/", "/js/app.js", "/js/rosbridge.js", "/css/estilo.css"]:
            estado, cab, cuerpo = pedir(base + ruta)
            cc = cab.get("Cache-Control", "")
            check(f"{ruta} responde 200 con 'Cache-Control: no-cache'",
                  estado == 200 and "no-cache" in cc and len(cuerpo) > 0,
                  f"-> {estado}, Cache-Control={cc!r}")
        _, cab, _ = pedir(base + "/js/app.js")
        estado, cab2, cuerpo = pedir(base + "/js/app.js",
                                     {"If-Modified-Since": cab.get("Last-Modified", "")})
        check("la revalidacion de un archivo sin cambios es un 304 sin cuerpo",
              estado == 304 and not cuerpo, f"-> {estado}, {len(cuerpo)} bytes")
        with open(os.path.join(RAIZ, "interfaz_web", "js", "app.js"), "rb") as f:
            check("sirve el app.js del repositorio",
                  pedir(base + "/js/app.js")[2] == f.read())
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    print(f"\n{fallos} fallo(s).")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
