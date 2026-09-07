#!/usr/bin/env python3
"""Agota la maquina de estado del agente (RF-08). Sin ROS y sin simulador.

    python3 src/aws-deepracer/coordinacion/test/prueba_agente.py

RF-08 pide que cada agente publique su estado en /<ns>/estado a 2 Hz y que el
campo 'estado' cambie al iniciar una mision. Una prueba que solo comprobara
"el topico existe" seria una prueba que no puede fallar -la misma clase de
defecto que se encontro en RF-22-, asi que aqui se comprueban las dos mitades
del requisito por separado:

  FRECUENCIA  el periodo del temporizador da 2 Hz exactos, y ademas coincide
              con lo que declara la tabla normativa de CONTRATO_INTERFACES.md.
  VALOR       la maquina de estado devuelve estados DISTINTOS ante entradas
              distintas, incluida la transicion LIBRE -> NAVEGANDO -> LIBRE
              que es literalmente lo que pide el criterio de aceptacion.

Y dos comprobaciones estaticas que fijan por escrito las dos decisiones de
diseno del 2026-09-07, para que nadie las deshaga sin que esto lo diga:

  ANTICIRCULARIDAD  el agente no puede sacar su estado de /coordinacion/
                    estado_mision. Si lo hiciera, la prueba de RF-06 ("el
                    segundo agente permanece LIBRE") seria el coordinador
                    dandose la razon a si mismo. El estado sale del status de
                    la propia accion navigate_to_pose, que publica Nav2.
  POSE CADUCADA     el agente no puede leer /<ns>/amcl_pose: es TRANSIENT_LOCAL
                    y con el robot quieto entrega la ultima muestra caducada
                    sin dar ningun error (medido el 2026-08-24: 0 mensajes en
                    10 s parado, 12 en movimiento). Lo dice el propio
                    EstadoRobot.msg. Se lee la TF map -> <ns>/odom.
"""

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coordinacion.estado_agente import (  # noqa: E402
    ACEPTADA, ABORTADA, CANCELADA, CANCELANDO, DESCONOCIDA, EJECUTANDO,
    EXITOSA, FRECUENCIA_HZ, PERIODO_S, TOPICO_ESTADO, TOPICO_STATUS_ACCION,
    MaquinaEstado)

AQUI = Path(__file__).resolve()
PAQUETE = AQUI.parents[1]                    # .../coordinacion
FUENTE_AGENTE = PAQUETE / "coordinacion" / "agente.py"
MSG = AQUI.parents[2] / "coordinacion_msgs" / "msg" / "EstadoRobot.msg"

OK = FALLOS = OMITIDAS = 0


def comprueba(titulo, condicion, detalle=""):
    global OK, FALLOS
    if condicion:
        OK += 1
        print(f"  [OK ] {titulo} {detalle}")
    else:
        FALLOS += 1
        print(f"  [MAL] {titulo} {detalle}")


def omite(titulo, motivo):
    global OMITIDAS
    OMITIDAS += 1
    print(f"  [OMI] {titulo} -- {motivo}")


def buscar_contrato():
    """Sube por el arbol hasta encontrar Documentos/CONTRATO_INTERFACES.md.

    En el repositorio esta; en ~/deepracer_sim_ws (que solo copia src/) no.
    Si no aparece, la comprobacion se OMITE en voz alta -nunca se da por
    buena en silencio, que es como se cuelan las pruebas que no fallan.
    """
    for base in AQUI.parents:
        candidato = base / "Documentos" / "CONTRATO_INTERFACES.md"
        if candidato.is_file():
            return candidato
    return None


# ------------------------------------------- 1. las constantes no se inventan
print("\n1. Las constantes de estado salen de EstadoRobot.msg, no de la cabeza")

# El .msg es el contrato. Si alguien cambia alli LIBRE=0 y aqui no, esto lo dice.
declaradas = dict(re.findall(r"^uint8\s+([A-Z_]+)\s*=\s*(\d+)\s*$",
                             MSG.read_text(encoding="utf-8"), re.MULTILINE))
comprueba("EstadoRobot.msg declara las cuatro constantes",
          set(declaradas) == {"LIBRE", "NAVEGANDO", "EN_TRANSFERENCIA", "ERROR"},
          f"-> {sorted(declaradas)}")

from coordinacion.estado_agente import (  # noqa: E402
    EN_TRANSFERENCIA, ERROR, LIBRE, NAVEGANDO)

for nombre, valor_py in (("LIBRE", LIBRE), ("NAVEGANDO", NAVEGANDO),
                         ("EN_TRANSFERENCIA", EN_TRANSFERENCIA),
                         ("ERROR", ERROR)):
    comprueba(f"{nombre} vale lo mismo en Python y en el .msg",
              str(valor_py) == declaradas.get(nombre),
              f"(py={valor_py} msg={declaradas.get(nombre)})")


# ------------------------------------------------------- 2. la mitad FRECUENCIA
print("\n2. Frecuencia: el periodo da 2 Hz y coincide con el contrato")

comprueba("PERIODO_S produce exactamente FRECUENCIA_HZ",
          abs(1.0 / PERIODO_S - FRECUENCIA_HZ) < 1e-9,
          f"(1/{PERIODO_S} = {1.0 / PERIODO_S})")
comprueba("FRECUENCIA_HZ es 2 Hz, que es lo que pide RF-08",
          FRECUENCIA_HZ == 2.0, f"-> {FRECUENCIA_HZ} Hz")
comprueba("El topico es relativo, para que el namespace lo cuelgue de /<ns>/",
          not TOPICO_ESTADO.startswith("/"), f"-> '{TOPICO_ESTADO}'")
comprueba("El topico se llama 'estado'", TOPICO_ESTADO == "estado",
          f"-> '{TOPICO_ESTADO}'")

contrato = buscar_contrato()
if contrato is None:
    omite("La fila de EstadoRobot en CONTRATO_INTERFACES.md",
          "no hay Documentos/ por encima; se corre fuera del repositorio")
else:
    fila = [ln for ln in contrato.read_text(encoding="utf-8").splitlines()
            if ln.startswith("|") and "EstadoRobot" in ln]
    comprueba("CONTRATO_INTERFACES.md tiene una sola fila para EstadoRobot",
              len(fila) == 1, f"-> {len(fila)} filas")
    if len(fila) == 1:
        comprueba("El contrato declara /<ns>/estado, no otro nombre",
                  f"/<ns>/{TOPICO_ESTADO}" in fila[0], f"-> {fila[0].strip()}")
        comprueba("El contrato declara 2 Hz para esa fila",
                  re.search(r"\b2\s*Hz\b", fila[0]) is not None)

# NADIE VUELVE A ESCRIBIR EL NOMBRE VIEJO. El tópico se llamó 'estado_robot' en
# la cabecera de EstadoRobot.msg y en prueba_round_trip.py hasta el 2026-09-07,
# mientras la tabla normativa del contrato y el criterio de RF-08 decian
# /<ns>/estado. La contradiccion sobrevivio meses porque la prueba que usaba el
# nombre viejo PUBLICA Y ESCUCHA EL MISMO NOMBRE: una ida y vuelta pasa con
# cualquier cadena, asi que no podia fallar. Esta comprobacion si puede.
VIEJO = "estado" + "_robot"          # partido: si no, se encuentra a si mismo
culpables = sorted(
    str(f.relative_to(MSG.parents[2]))
    for carpeta in (PAQUETE, MSG.parents[1])
    for f in carpeta.rglob("*")
    if f.is_file() and f.suffix in (".py", ".msg", ".action", ".xml")
    and f.resolve() != AQUI and VIEJO in f.read_text(encoding="utf-8", errors="ignore"))
comprueba(f"Ningun fichero de los dos paquetes escribe '{VIEJO}'",
          not culpables, f"-> {culpables}" if culpables else "")


# ----------------------------------------------------------- 3. la mitad VALOR
print("\n3. Valor: entradas distintas dan estados distintos")

m = MaquinaEstado()
comprueba("Recien arrancado, sin ninguna meta, esta LIBRE",
          m.estado == LIBRE, f"-> {m.estado}")

comprueba("Un status vacio lo deja LIBRE",
          m.actualizar([]) == LIBRE)
comprueba("Una meta ACEPTADA ya es NAVEGANDO",
          m.actualizar([ACEPTADA]) == NAVEGANDO)
comprueba("Una meta EJECUTANDO es NAVEGANDO",
          m.actualizar([EJECUTANDO]) == NAVEGANDO)
comprueba("Terminada con exito, vuelve a LIBRE",
          m.actualizar([EXITOSA]) == LIBRE)
comprueba("Una meta ABORTADA es ERROR",
          m.actualizar([ABORTADA]) == ERROR)
comprueba("Una meta CANCELADA es ERROR",
          MaquinaEstado().actualizar([CANCELADA]) == ERROR)
comprueba("CANCELANDO todavia cuenta como actividad, no como LIBRE",
          MaquinaEstado().actualizar([CANCELANDO]) != LIBRE)
comprueba("Un status DESCONOCIDA no arrastra el ERROR anterior",
          MaquinaEstado().actualizar([DESCONOCIDA]) == LIBRE)

# Nav2 deja varias metas en el array: manda la que sigue viva, no la ultima.
comprueba("Con una meta vieja EXITOSA y una viva EJECUTANDO, gana NAVEGANDO",
          MaquinaEstado().actualizar([EXITOSA, EJECUTANDO]) == NAVEGANDO)
comprueba("Con una vieja ABORTADA y una viva EJECUTANDO, gana NAVEGANDO",
          MaquinaEstado().actualizar([ABORTADA, EJECUTANDO]) == NAVEGANDO)

# El criterio de aceptacion literal de RF-08.
m = MaquinaEstado()
antes = m.estado
m.actualizar([EJECUTANDO])
durante = m.estado
m.actualizar([EXITOSA])
despues = m.estado
comprueba("RF-08 literal: el campo 'estado' CAMBIA al iniciar la mision",
          antes != durante, f"({antes} -> {durante})")
comprueba("Y vuelve al terminar, asi que no se queda pegado",
          durante != despues and despues == antes,
          f"({durante} -> {despues})")


# ------------------------------------------- 4. EN_TRANSFERENCIA es del mando
print("\n4. EN_TRANSFERENCIA: lo declara el mando, lo confirma la accion")

# El robot no puede saber por si solo si la meta que ejecuta es un punto de
# relevo o el destino final: eso es informacion de la mision. Se la da el
# coordinador AL MANDAR el tramo. Eso no es circular -el coordinador aporta su
# intencion, no su opinion sobre el estado del robot-, pero solo se cree si la
# accion propia confirma que hay actividad.
m = MaquinaEstado()
m.declarar_relevo(True)
comprueba("Marcado como relevo pero sin meta viva, sigue LIBRE",
          m.actualizar([]) == LIBRE, "(la marca sola no basta)")
comprueba("Marcado como relevo y con meta viva, es EN_TRANSFERENCIA",
          m.actualizar([EJECUTANDO]) == EN_TRANSFERENCIA)
comprueba("Sin la marca, la misma meta viva es NAVEGANDO",
          MaquinaEstado().actualizar([EJECUTANDO]) == NAVEGANDO)

m = MaquinaEstado()
m.declarar_relevo(True)
m.actualizar([EJECUTANDO])
m.declarar_relevo(False)
comprueba("Retirada la marca, deja de ser EN_TRANSFERENCIA",
          m.actualizar([EJECUTANDO]) == NAVEGANDO)
m.declarar_relevo(True)
comprueba("Un fallo manda sobre la marca de relevo",
          m.actualizar([ABORTADA]) == ERROR)


# ------------------------------- 5. las dos decisiones de diseno, por escrito
print("\n5. El nodo no toma los dos atajos que el proyecto ya sabe que enganan")

def solo_codigo(ruta):
    """Devuelve el fuente SIN comentarios y SIN docstrings.

    Hace falta separarlos: la cabecera de agente.py NOMBRA amcl_pose y
    estado_mision precisamente para explicar por que no se usan. Buscando en
    el texto crudo, las comprobaciones de abajo darian falsa alarma. ast.unparse
    reconstruye solo las sentencias reales.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        cuerpo = getattr(nodo, "body", None)
        if not isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)) or not cuerpo:
            continue
        primero = cuerpo[0]
        if (isinstance(primero, ast.Expr)
                and isinstance(primero.value, ast.Constant)
                and isinstance(primero.value.value, str)):
            cuerpo.pop(0)
    return ast.unparse(arbol)


comprueba("TOPICO_STATUS_ACCION apunta al status de navigate_to_pose",
          TOPICO_STATUS_ACCION == "navigate_to_pose/_action/status",
          f"-> '{TOPICO_STATUS_ACCION}'")
comprueba("Y es relativo, para que cuelgue del namespace del robot",
          not TOPICO_STATUS_ACCION.startswith("/"))

if not FUENTE_AGENTE.is_file():
    omite("Comprobaciones estaticas sobre agente.py",
          f"no existe {FUENTE_AGENTE.name} todavia")
else:
    codigo = solo_codigo(FUENTE_AGENTE)
    comprueba("No se suscribe a estado_mision (seria circular con RF-06)",
              "estado_mision" not in codigo)
    comprueba("No lee amcl_pose (TRANSIENT_LOCAL: caduca en silencio)",
              "amcl_pose" not in codigo)
    comprueba("Lee el status de su propia accion, por la constante declarada",
              "TOPICO_STATUS_ACCION" in codigo)
    comprueba("Usa PERIODO_S y no un 0.5 suelto",
              "PERIODO_S" in codigo)

    # El QoS del status es RELIABLE + TRANSIENT_LOCAL. Con el perfil por
    # defecto la suscripcion NO empareja y no hay error: el callback no se
    # llama nunca y el robot se queda LIBRE para siempre.
    #
    # Se mira el ARGUMENTO de la llamada, no si el nombre aparece en el
    # fichero. Comprobandolo por texto, un 'import' que ya no se usa bastaba
    # para dar la prueba por buena: comprobado el 2026-09-07 mutando la
    # llamada a 10 y viendo que la prueba seguia verde.
    subs = [[ast.unparse(a) for a in n.args]
            for n in ast.walk(ast.parse(FUENTE_AGENTE.read_text(encoding="utf-8")))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "create_subscription"]
    comprueba("agente.py hace exactamente una suscripcion", len(subs) == 1,
              f"-> {len(subs)}")
    if len(subs) == 1:
        args = subs[0]
        comprueba("Se suscribe al topico por su constante, no a un literal",
                  len(args) > 1 and args[1] == "TOPICO_STATUS_ACCION",
                  f"-> {args[1] if len(args) > 1 else '(falta)'}")
        comprueba("El QoS de esa llamada es qos_profile_action_status_default",
                  len(args) > 3 and args[3] == "qos_profile_action_status_default",
                  f"-> {args[3] if len(args) > 3 else '(falta)'}")


# --------------------------------------------------------------------- total
print(f"\n{OK} de {OK + FALLOS} comprobaciones pasan.", end="")
if OMITIDAS:
    print(f" {OMITIDAS} OMITIDAS -- leer arriba por que.", end="")
print()
sys.exit(1 if FALLOS else 0)
