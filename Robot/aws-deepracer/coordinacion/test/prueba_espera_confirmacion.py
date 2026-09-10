#!/usr/bin/env python3
"""Agota la politica de plazos y el enganche de RF-28. Sin ROS y sin simulador.

    python3 src/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py

Por que existe. Los dos fallos que esta logica puede tener son invisibles en una
corrida suelta: una alerta que se reemite en cada tick del bucle -y llena el bag
de marcas- y una confirmacion que llega antes de que nadie escuche -y deja al
usuario esperando 120 s un plazo que ya cumplio-. Ninguno de los dos da error.
Aqui se fuerzan los dos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coordinacion.espera_confirmacion import (  # noqa: E402
    ALERTA_S, PLAZO_S, Enganche, fase)

OK = FALLOS = 0


def comprueba(titulo, condicion, detalle=""):
    global OK, FALLOS
    if condicion:
        OK += 1
        print(f"  [OK ] {titulo} {detalle}")
    else:
        FALLOS += 1
        print(f"  [MAL] {titulo} {detalle}")


def main():
    print("\n1. Los plazos son los que pidio el director")
    comprueba("la alerta es a los 60 s", ALERTA_S == 60.0, f"-> {ALERTA_S}")
    comprueba("el plazo maximo es 120 s", PLAZO_S == 120.0, f"-> {PLAZO_S}")

    print("\n2. Las tres fases, y sus bordes exactos")
    comprueba("en 0 s se espera", fase(0.0) == "esperando")
    comprueba("en 59,9 s todavia se espera", fase(59.9) == "esperando")
    comprueba("en 60,0 s exactos ya hay alerta", fase(60.0) == "alerta")
    comprueba("en 119,9 s sigue en alerta", fase(119.9) == "alerta")
    comprueba("en 120,0 s exactos se agota", fase(120.0) == "agotada")
    comprueba("en 120,1 s sigue agotada", fase(120.1) == "agotada")

    print("\n3. Un tiempo negativo no inventa una fase")
    # Puede pasar si el reloj da un salto atras. Mejor 'esperando' que 'agotada':
    # un salto de reloj no debe matar una mision en curso.
    comprueba("un transcurrido negativo se trata como espera",
              fase(-5.0) == "esperando")

    print("\n4. Los plazos se pueden estrechar para probar sin esperar 2 minutos")
    comprueba("con plazos cortos, 1,5 s ya es alerta",
              fase(1.5, alerta_s=1.0, plazo_s=3.0) == "alerta")
    comprueba("con plazos cortos, 3,0 s ya es agotada",
              fase(3.0, alerta_s=1.0, plazo_s=3.0) == "agotada")

    print("\n5. El enganche solo honra la mision en curso")
    e = Enganche()
    e.reiniciar("m1")
    comprueba("sin confirmacion no hay nada que consumir",
              e.consumir("m1") is False)

    e.recibir("m1")
    comprueba("una confirmacion de la mision en curso se consume",
              e.consumir("m1") is True)
    comprueba("y no se puede consumir dos veces",
              e.consumir("m1") is False)

    print("\n6. Una confirmacion de otra mision se ignora")
    e = Enganche()
    e.reiniciar("m2")
    e.recibir("m1")
    comprueba("llega 'm1' mientras corre 'm2': no sirve",
              e.consumir("m2") is False)

    print("\n7. Una pulsacion vieja no auto-confirma la mision siguiente")
    # El caso real: el usuario pulsa confirmar al final de la mision anterior y
    # ese mensaje queda guardado. Sin reiniciar(), la mision siguiente arrancaria
    # el tramo 2 sin preguntar a nadie.
    e = Enganche()
    e.reiniciar("m1")
    e.recibir("m1")
    e.reiniciar("m2")
    comprueba("tras reiniciar, la confirmacion anterior no vale",
              e.consumir("m2") is False)

    print("\n8. La confirmacion temprana se engancha y se honra")
    # El usuario sube rapido y pulsa mientras robot2 todavia va hacia su
    # escalera. Si esto no funcionara, esperaria los 120 s completos.
    e = Enganche()
    e.reiniciar("m1")
    e.recibir("m1")          # llega durante TRANSFERENCIA, nadie espera aun
    comprueba("la confirmacion adelantada sigue valida al llegar la espera",
              e.consumir("m1") is True)

    print("\n9. Un mision_id vacio no confirma nada")
    # Un mensaje mal formado, o el tick de una HRI recien cargada.
    e = Enganche()
    e.reiniciar("m1")
    e.recibir("")
    comprueba("una confirmacion sin mision_id se ignora",
              e.consumir("m1") is False)

    print("\n" + "=" * 62)
    print(f"{OK} comprobaciones pasan, {FALLOS} fallan.")
    print("=" * 62)
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
