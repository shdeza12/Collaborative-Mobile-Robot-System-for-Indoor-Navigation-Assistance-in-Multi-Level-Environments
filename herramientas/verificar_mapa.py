#!/usr/bin/env python3
"""Verifica que un mapa de ocupacion cubra el mundo simulado antes de darlo por bueno.

Compara la extension realmente mapeada (celdas conocidas del .pgm) contra la
extension geometrica del mundo .world de Gazebo, y reporta la deriva aparente.

Uso:
    python3 herramientas/verificar_mapa.py <mapa.yaml> <mundo.world>

Codigo de salida 0 si el mapa supera los umbrales de aceptacion, 1 si no.
Pensado para ejecutarse ANTES de cerrar Gazebo, para poder repetir el recorrido
sin perder la sesion de mapeo.
"""

import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow. Instalar con: pip3 install Pillow")

# Umbrales de aceptacion
COBERTURA_MINIMA = 0.85   # fraccion de la extension del mundo que debe quedar mapeada
DESCONOCIDO_MAXIMO = 0.35  # fraccion maxima de celdas desconocidas dentro del area mapeada


def leer_yaml_mapa(ruta):
    """Lee los campos que necesitamos del .yaml sin depender de PyYAML."""
    texto = Path(ruta).read_text()
    campos = {}
    for clave in ("image", "resolution", "origin", "negate"):
        m = re.search(rf"^{clave}\s*:\s*(.+)$", texto, re.M)
        if m:
            campos[clave] = m.group(1).strip()
    if "resolution" not in campos or "image" not in campos:
        sys.exit(f"El archivo {ruta} no declara 'resolution' e 'image'.")
    campos["resolution"] = float(campos["resolution"])
    origen = re.findall(r"-?\d+\.?\d*", campos.get("origin", "0 0 0"))
    campos["origin"] = [float(v) for v in origen[:3]]
    return campos


def extension_mundo(ruta):
    """Extension en X e Y de las poses declaradas en el .world."""
    texto = Path(ruta).read_text()
    poses = re.findall(r"<pose[^>]*>([^<]+)</pose>", texto)
    xs, ys = [], []
    for p in poses:
        partes = p.split()
        if len(partes) >= 2:
            try:
                xs.append(float(partes[0]))
                ys.append(float(partes[1]))
            except ValueError:
                continue
    if not xs:
        sys.exit(f"No se encontraron poses en {ruta}.")
    return max(xs) - min(xs), max(ys) - min(ys)


def analizar(ruta_yaml, ruta_world):
    meta = leer_yaml_mapa(ruta_yaml)
    ruta_pgm = Path(ruta_yaml).parent / meta["image"]
    if not ruta_pgm.exists():
        sys.exit(f"No existe la imagen del mapa: {ruta_pgm}")

    img = Image.open(ruta_pgm).convert("L")
    ancho, alto = img.size
    res = meta["resolution"]
    pixeles = img.load()

    # En un .pgm de nav2_map_server: 254 = libre, 0 = ocupado, 205 = desconocido.
    min_x = min_y = None
    max_x = max_y = None
    conocidas = desconocidas = 0
    for y in range(alto):
        for x in range(ancho):
            v = pixeles[x, y]
            if 200 <= v <= 210:
                desconocidas += 1
                continue
            conocidas += 1
            min_x = x if min_x is None else min(min_x, x)
            max_x = x if max_x is None else max(max_x, x)
            min_y = y if min_y is None else min(min_y, y)
            max_y = y if max_y is None else max(max_y, y)

    if not conocidas:
        sys.exit("El mapa no contiene ninguna celda conocida.")

    mapeado_x = (max_x - min_x + 1) * res
    mapeado_y = (max_y - min_y + 1) * res
    mundo_x, mundo_y = extension_mundo(ruta_world)

    cobertura_x = mapeado_x / mundo_x if mundo_x else 0.0
    cobertura_y = mapeado_y / mundo_y if mundo_y else 0.0
    frac_desconocido = desconocidas / (conocidas + desconocidas)

    print(f"Mapa           : {ruta_pgm.name}  ({ancho}x{alto} px @ {res} m/celda)")
    print(f"Mundo          : {Path(ruta_world).name}")
    print(f"Extension mundo: {mundo_x:6.1f} m X  x {mundo_y:5.1f} m Y")
    print(f"Extension mapa : {mapeado_x:6.1f} m X  x {mapeado_y:5.1f} m Y")
    print(f"Cobertura      : {cobertura_x:6.1%} X  x {cobertura_y:5.1%} Y")
    print(f"Celdas desconocidas: {frac_desconocido:.1%}")
    print()

    fallos = []
    if cobertura_x < COBERTURA_MINIMA:
        fallos.append(
            f"Cobertura en X del {cobertura_x:.1%} (minimo {COBERTURA_MINIMA:.0%}). "
            "Faltan tramos del recorrido."
        )
    if cobertura_y < COBERTURA_MINIMA:
        fallos.append(
            f"Cobertura en Y del {cobertura_y:.1%} (minimo {COBERTURA_MINIMA:.0%})."
        )
    if mapeado_y > mundo_y * 1.5:
        fallos.append(
            f"El mapa mide {mapeado_y:.1f} m en Y y el mundo solo {mundo_y:.1f} m. "
            "Sintoma de deriva de pose: el corredor se esta 'abriendo'."
        )
    if frac_desconocido > DESCONOCIDO_MAXIMO:
        fallos.append(
            f"{frac_desconocido:.1%} de celdas desconocidas "
            f"(maximo {DESCONOCIDO_MAXIMO:.0%})."
        )

    if fallos:
        print("RECHAZADO -- no guardar este mapa como definitivo:")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("ACEPTADO -- el mapa cubre el mundo dentro de los umbrales.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(analizar(sys.argv[1], sys.argv[2]))
