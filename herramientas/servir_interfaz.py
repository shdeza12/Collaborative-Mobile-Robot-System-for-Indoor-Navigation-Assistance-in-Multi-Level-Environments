#!/usr/bin/env python3
"""Sirve interfaz_web/ para el telefono, sin que el navegador se quede con una version vieja.

    python3 herramientas/servir_interfaz.py [puerto]      # 8000 por defecto

Sustituye a 'python3 -m http.server 8000 --directory interfaz_web'. Ese
servidor solo manda Last-Modified, y con eso el navegador guarda la pagina y
sus scripts por dias sin volver a preguntar: el 16-oct, en campo, el telefono
siguio con el app.js anterior despues de corregirlo, y recargar solo
revalidaba index.html (reproducido el 18-oct; ver prueba_servir_interfaz.py).

La unica diferencia es 'Cache-Control: no-cache' en todas las respuestas: el
navegador puede guardar la copia, pero pregunta antes de usarla. Si el
archivo no cambio, la respuesta es un 304 sin cuerpo.
"""
import functools
import http.server
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SinCopiaVieja(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    manejador = functools.partial(SinCopiaVieja,
                                  directory=os.path.join(RAIZ, "interfaz_web"))
    with http.server.ThreadingHTTPServer(("0.0.0.0", puerto), manejador) as srv:
        print(f"interfaz_web en el puerto {puerto}, con Cache-Control: no-cache", flush=True)
        srv.serve_forever()


if __name__ == "__main__":
    main()
