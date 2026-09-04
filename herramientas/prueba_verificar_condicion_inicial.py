#!/usr/bin/env python3
"""La compuerta previa mide localizacion, no aparcamiento.

POR QUE EXISTE ESTA PRUEBA. El 2026-09-04, el piloto S21_piloto_A_03 fue
rechazado por la compuerta con robot1 a 1,19 m y robot2 a 43,92 m "de su pose
declarada". La corrida era sana: el error de AMCL contra la verdad al arrancar
era de 0,032 m -mejor que el del piloto que SI paso, 0,040 m- y llego a 0,068 m
del destino, la mejor llegada del dia. Lo unico que pasaba es que los robots
venian de una mision anterior y no se habian vuelto a spawnear.

EL ERROR ERA DEL CRITERIO, NO DE LA CORRIDA. La compuerta existe por un fallo
medido: el carro resbala ~17 mm/min en Gazebo y AMCL no se entera, porque con
update_min_d 0.25 solo corrige al acumular 25 cm. El dano es que la CREENCIA de
AMCL se separa de la VERDAD; el 2026-08-27 se midieron 0,643 m con el robot
parado. Esa es la magnitud que importa.

La distancia a la tabla de spawn era un SUSTITUTO de esa magnitud, y solo vale
mientras el robot no se haya movido a proposito: AMCL se siembra con la pose
declarada, asi que en una pila recien levantada "distancia a la tabla" y "error
de localizacion" son el MISMO numero. En cuanto el robot navega, AMCL converge
a donde esta de verdad y el sustituto pasa a medir la mision, no el resbalon.

Comprobado en los dos pilotos del 2026-09-04:

                        desvio vs tabla   error AMCL vs verdad
  piloto 1 (pila nueva)      0,0396 m           0,040 m   <- iguales
  piloto 2 (encadenada)      1,1919 m           0,032 m   <- divergen

Y hay un motivo que remata: en el banco fisico no se puede respawnear nada, asi
que un criterio de "estar en la pose de spawn" es inaplicable donde esto tiene
que acabar.

Uso:
    python3 herramientas/prueba_verificar_condicion_inicial.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verificar_condicion_inicial import (TOLERANCIA_M, TOLERANCIA_YAW_GRADOS,
                                         evaluar_desvios)

fallos = []


def caso(nombre, esperada, real, creida, dentro, **campos):
    r = evaluar_desvios(esperada, real, creida)
    if r["dentro"] is not dentro:
        fallos.append(f"{nombre}: dentro={r['dentro']!r}, se esperaba "
                      f"{dentro!r}. Evaluacion completa: {r}")
        return
    for k, v in campos.items():
        if r[k] is None or abs(r[k] - v) > 0.005:
            fallos.append(f"{nombre}: {k}={r[k]!r}, se esperaba ~{v}")
            return
    print(f"  pasa: {nombre}")


# La pose declarada de robot1, la de verdad, para que los numeros de abajo sean
# los del banco y no unos inventados.
DECL = (-19.165, 7.292, math.radians(90.0))

print("1. Pila recien levantada: el sustituto y la magnitud coinciden.")
# AMCL se sembro en la declarada y el carro lleva 40 min resbalando: cree estar
# en la declarada y esta 0,6 m mas alla. Las dos lecturas dan 0,6 m.
caso("resbalon de 0,60 m con AMCL sembrada en la declarada",
     DECL, (-19.165, 6.692, math.radians(90.0)), DECL,
     dentro=False, desviacion_m=0.600, error_localizacion_m=0.600)

caso("pila recien levantada y quieta: todo en su sitio",
     DECL, (-19.205, 7.299, math.radians(94.7)), DECL,
     dentro=True, desviacion_m=0.041, error_localizacion_m=0.041)

print("\n2. Mision encadenada: es aqui donde el criterio viejo se equivocaba.")
# EL CASO QUE HOY FALLA. El robot viene de una mision, esta a 43,9 m de su
# spawn, y AMCL sabe perfectamente donde esta. La corrida es sana.
lejos = (21.835, -4.286, math.radians(4.7))
caso("robot2 a 43,9 m del spawn pero bien localizado",
     (-21.889, -8.379, math.radians(0.0)), lejos, lejos,
     dentro=True, desviacion_m=43.915, error_localizacion_m=0.0)

caso("robot1 a 1,19 m del spawn y AMCL a 0,032 m de la verdad",
     DECL, (-19.300, 6.108, math.radians(90.0)),
     (-19.300 + 0.032, 6.108, math.radians(90.0)),
     dentro=True, error_localizacion_m=0.032)

print("\n3. Lo que la compuerta si tiene que seguir atrapando.")
# Estar aparcado en la pose declarada no salva a una corrida cuya AMCL se
# perdio. El criterio viejo la dejaba pasar; el nuevo no.
caso("en la pose declarada pero AMCL perdida 0,50 m",
     DECL, DECL, (-19.165 + 0.50, 7.292, math.radians(90.0)),
     dentro=False, desviacion_m=0.0, error_localizacion_m=0.500)

caso("bien en posicion y AMCL girada 15 grados",
     DECL, DECL, (-19.165, 7.292, math.radians(105.0)),
     dentro=False, error_localizacion_yaw_grados=15.0)

print("\n4. Sin creencia no hay veredicto, y eso no es aprobar.")
r = evaluar_desvios(DECL, DECL, None)
if r["dentro"] is not None:
    fallos.append(f"sin creencia: dentro={r['dentro']!r}, se esperaba None. "
                  f"Un hueco que se lea como aprobado cuela la corrida.")
elif r["desviacion_m"] is None:
    fallos.append("sin creencia: se perdio tambien el desvio contra la tabla, "
                  "que si se puede medir y es informativo.")
else:
    print("  pasa: sin creencia, dentro=None y el desvio se sigue reportando")

print("\n5. El criterio queda nombrado en la salida.")
r = evaluar_desvios(DECL, DECL, DECL)
if r.get("criterio") != "localizacion":
    fallos.append(f"falta el campo 'criterio' con valor 'localizacion': "
                  f"{r.get('criterio')!r}. Sin el, un condicion_inicial.json "
                  f"viejo y uno nuevo son indistinguibles y 'dentro' no "
                  f"significa lo mismo en los dos.")
else:
    print("  pasa: criterio='localizacion'")

print("\n6. Las tolerancias no se movieron.")
if (TOLERANCIA_M, TOLERANCIA_YAW_GRADOS) != (0.15, 10.0):
    fallos.append(f"las tolerancias cambiaron a {TOLERANCIA_M} / "
                  f"{TOLERANCIA_YAW_GRADOS}. Este arreglo cambia QUE se mide, "
                  f"no CUANTO se tolera.")
else:
    print("  pasa: 0,15 m y 10 grados")

print("\n--- veredicto ---")
if fallos:
    for f in fallos:
        print(f"\n{f}")
    print("\nLA PRUEBA FALLA.")
    sys.exit(1)
print("PASA: la compuerta mide localizacion y no aparcamiento.")
