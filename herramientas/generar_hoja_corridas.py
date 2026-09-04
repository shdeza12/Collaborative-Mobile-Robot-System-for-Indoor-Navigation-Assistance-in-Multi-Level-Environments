#!/usr/bin/env python3
"""Genera Documentos/HOJA_CORRIDAS_OE4.md desde el sorteo.

POR QUE SE GENERA Y NO SE ESCRIBE A MANO. La primera version llevaba
marcadores tipo '<BAG>' y el 2026-09-04 costo la campana: '<BAG>' es una
redireccion valida en bash, asi que la shell no la rechaza, la ejecuta. La
segunda version puso los nombres literales pero dejo cada mision reducida a dos
ordenes -grabar y lanzar-, y entonces una mision parecia caber en una terminal:
se encadenaron misiones sobre el mismo gzserver y los robots acabaron a 23 m de
su pose declarada.

De ahi la regla de esta hoja: CADA MISION ES UN BLOQUE COMPLETO, con las cinco
terminales y en orden. Se repite mucho a proposito. Un bloque que remite a otro
sitio es un bloque que alguien va a saltarse a las once de la noche en la
mision 24.

    python3 herramientas/generar_hoja_corridas.py
"""
import csv
import io
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CSV = RAIZ / "Documentos/Evidencia/campana_oe4_misiones.csv"
SALIDA = RAIZ / "Documentos/HOJA_CORRIDAS_OE4.md"

PREFIJO_MISION = "S21C"

PILOTOS = [
    ("Piloto 1", "B", "ETM7", "Aula 306", "S21_piloto_B_02",
     "piso1_etm7", "piso2_aula_306", 1),
    ("Piloto 2", "A", "ETM9", "ETM6", "S21_piloto_A_03",
     "piso1_etm9", "piso1_etm6", 0),
    ("Piloto 3", "B", "ETM6", "IEEE", "S21_piloto_B_03",
     "piso1_etm6", "piso2_ieee", 1),
]


def leer_misiones():
    texto = CSV.read_text(encoding="utf-8")
    sin_comentarios = "".join(
        l for l in texto.splitlines(keepends=True) if not l.startswith("#"))
    return list(csv.DictReader(io.StringIO(sin_comentarios)))


def bloque(titulo, condicion, origen, destino, bag, origen_id, destino_id,
           relevos):
    return f"""#### {titulo} — {condicion} · {origen} → {destino}  ·  relevos esperados: {relevos}

Bag: `{bag}`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:={PREFIJO_MISION}
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh {bag} robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{{origen_id: '{origen_id}', destino_id: '{destino_id}'}}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

"""


def cabecera():
    return f"""# Hoja de corridas — campaña OE4 (simulación)

Hoja operativa para ejecutar a mano. El procedimiento normativo es
`RUNBOOK_CAMPANA.md`; esta hoja lo ordena para copiar y pegar, y **se separa de él en los
puntos declarados en el §6**.

Generada por `herramientas/generar_hoja_corridas.py` desde
`Documentos/Evidencia/campana_oe4_misiones.csv`. No se edita a mano: se regenera.

---

## 1. Tres cosas que rompen en silencio

**Cada terminal necesita su `source`.** Un shell nuevo de esta máquina **no** trae entorno ROS:
`ROS_DISTRO`, `PYTHONPATH` y `AMENT_PREFIX_PATH` salen vacíos y solo el binario `ros2` está en
`PATH`. Sin `source ~/deepracer_sim_ws/install/setup.bash`, `grabar_mision.sh` muere con
`PackageNotFoundError: ros2cli`, y en el caso peor `ros2 bag record` descarta `coordinacion_msgs`
sin decir nada y deja un bag con pinta de bueno. Los comandos de abajo llevan el `source` incluido.

**Un solo dueño para todo.** Los buzones de FastDDS en `/dev/shm` son `-rw-r--r--`, así que quien
levanta las pilas tiene que ser quien graba. Si dos usuarios distintos tocan la misma corrida, la
grabación sale vacía y no avisa. **Las cinco terminales, el mismo usuario.**

**Para parar el coordinador, el patrón va con BARRA.** `ros2 run` hace `exec` a la ruta instalada,
así que el proceso vivo se llama `.../lib/coordinacion/coordinador --ros-args ...`. El patrón con
espacio —`pkill -f "coordinacion coordinador"`— **no encuentra nada aunque haya tres corriendo**, y
quien lo lanza se queda creyendo que ya no hay ninguno. Así sobrevivió el coordinador de las 14:10
del 2026-09-04, que seguía sirviendo una hora después y arruinó la campaña (§5). El correcto:

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

Los corchetes tampoco sobran: sin ellos, `pkill` encuentra la propia orden que lo invoca y se mata
a sí mismo.

Y lo de siempre: **ninguna terminal exporta `ROS_DOMAIN_ID`**.

---

## 2. La ventana real es de 2,6 minutos

Medido el 2026-09-04 sobre las dos pilas en reposo, sin un solo `/cmd_vel`:

| | deriva lineal | deriva de yaw |
|---|---|---|
| robot1 | 19,1 mm/min | 3,7 °/min |
| robot2 | 18,9 mm/min | 4,0 °/min |
| tolerancia | 0,15 m | 10° |
| **se cruza a los** | **7,9 min** | **2,6 min** |

**Manda el yaw, no la posición.** El texto de diagnóstico de `verificar_condicion_inicial.py`
dice «a los ~9 min ya se sale de los 0,15 m» porque solo mira la componente lineal: engaña por un
factor de tres. Lo que hay que cumplir es **del spawn al `send_goal`, menos de 2,6 min**.

Por eso el §3 del runbook, ejecutado en serie, **no cabe**. Cronometrado en el intento fallido:

| hito | en serie | reordenado |
|---|---|---|
| amcl arriba | +14 s | +14 s |
| portón de los dos robots | +120 s | +70 s |
| coordinador listo | +157 s | +58 s (en paralelo) |
| `send_goal` | **+175 s — fuera** | **~+95 s — dentro** |

Los 58 s del coordinador incluyen los 3,0 s del guardián del §5, medidos.

---

## 3. Las cinco terminales

Las cinco desde la raíz del repositorio, salvo donde el comando hace su propio `cd`. Comprobación
de que estás donde toca: `ls herramientas/robot.sh`.

| | para qué | trabaja desde |
|---|---|---|
| T1 | pila de robot1 | raíz del repo |
| T2 | pila de robot2 | raíz del repo |
| T3 | parar y arrancar el coordinador | workspace (el comando hace el `cd`) |
| T4 | portón, grabadora | raíz del repo |
| T5 | `send_goal` | workspace (el comando hace el `cd`) |

---

## 4. Cómo se usa esta hoja

**Cada misión del §7 y del §8 es un bloque completo**: lleva las cinco terminales, en orden, con el
nombre del bag y los identificadores ya puestos. No hay nada que sustituir y no hay que volver a
subir a esta sección. Se hace el bloque entero, de arriba abajo, y se pasa al siguiente.

`gzserver` **nuevo por misión, sin excepción** (§6.4 del runbook). Encadenar misiones sobre la misma
simulación ya costó una corrida: los robots acabaron a 23 m de su pose declarada y las llegadas
salieron perfectas igual, porque se miden contra `/odom`, que es continuo.

Lo que se espera en cada paso:

- **T1 y T2** tardan 28–35 s. Si `parar` avisa de procesos «que no lanzó `robot.sh`», mátalos con
  `kill -9` y repite.
- **T3** tiene que decir `Coordinador listo. 31 puntos, asignacion {{1: 'robot1', 2: 'robot2'}}`. Si
  dice un número distinto de 31, **para**: el sorteo y la corrida no son del mismo catálogo. El
  aviso de que `piso2_escalera` es provisional es normal y no bloquea. `ruta_registros` no va, ni
  en el piloto.
- **T4 portón**: `LISTA. Nav2, controladores, parametros y condicion inicial.` en los dos, con la
  desviación por debajo de 0,15 m y 10°. **Si uno se sale, relanza esa pila y empieza el bloque de
  nuevo. No se corrige a mano y no se sigue igual.** Si faltan controladores suele ser el spawner
  adelantándose a `gazebo_ros2_control`; si faltan nodos de Nav2, la carrera entre los dos
  `lifecycle_manager`. En los dos casos, relanzar basta.
- **T4 grabar**: `Grabando en ...` con el recuento de tópicos, y **ni un `AVISO`**. Déjala en primer
  plano. Deja tres cosas junto al bag: `rtf.json`, `condicion_inicial.json` y el bag; los dos
  primeros existen porque si no se escriben en el momento, no se escriben nunca.
- **T5**: `exito: true`, y `relevos: 0` en condición A, `relevos: 1` en B.

Un portón que falla **no es un descarte**: no se grabó nada, así que se repite el montaje. Una
misión que falla **sí es un resultado** y se registra; la lista de descartes del §8 del protocolo
está cerrada (`caida_gazebo`, `controladores_incompletos`, `rtf_bajo`, `fallo_anfitrion`) y un
fallo de navegación no está en ella.

---

## 5. Por qué hay un paso para parar el coordinador

El 2026-09-04 se perdieron dos misiones con `Nav2 termino con estado 6`. El estado 6 es `ABORTED`, y
la causa quedó medida ese mismo día con `herramientas/diagnosticar_aborto_nav2.py`:

| prueba | resultado |
|---|---|
| 20 goals directos a `/robot1/navigate_to_pose`, en limpio | **0 abortos** |
| 8 pares de goals seguidos al mismo servidor | **8 abortos** del desplazado, 9–13 ms |

`navigate_to_pose` atiende un goal a la vez: al desplazado lo termina en `ABORTED`. Y aquel día
había dos coordinadores vivos —el de las 14:10 seguía sirviendo a las 15:15— porque el comando que
se usaba para pararlos no coincidía con nada (§1).

Nav2 no tiene defecto y el coordinador tampoco: tiene un solo `send_goal_async` y ningún reintento,
así que uno no se pisa a sí mismo. Se pisaban dos.

Desde entonces el coordinador lleva un **guardián**: sondea `/coordinacion/guiar_usuario` antes de
construirse y, si ya hay alguien sirviendo, **se niega a arrancar** y sale con código 1 explicando
qué parar. Cuesta 3,0 s de arranque, medidos, y se desactiva con `-p espera_guardian_s:=0.0`.
Cubierto por `herramientas/prueba_guardian_coordinador.py`.

Si ves el mensaje del guardián, no es un fallo de la corrida: es el paso de parar el coordinador,
que se saltó. Párala, y repite el bloque desde el principio.

---

## 6. Dónde esta hoja se separa del runbook

Declaradas, para que la desviación quede en el papel y no en la costumbre:

1. **Los dos `esperar_nav2.sh` van en paralelo**, no encadenados con `&&` como pide el §3. No
   cambia ninguna comprobación —cada uno mira su robot— y ahorra ~50 s de los 156 que dura la
   ventana. Además es más correcto de medir: la desviación depende del tiempo que la pila lleva
   quieta, así que medir un robot después del otro sesga al segundo.

2. **No se repite `verificar_condicion_inicial.py` como paso suelto** después del portón, como
   pide el §3. `esperar_nav2.sh` ya lo invoca para su robot e imprime su salida entera; repetirlo
   no añade información y gasta ~8 s de ventana. Queda como herramienta de diagnóstico:
   `source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/verificar_condicion_inicial.py robot1 robot2`

3. **El coordinador arranca en paralelo con el portón**, no después. El §4 lo pone detrás del §3
   por orden de lectura, no por dependencia: el coordinador solo necesita `/clock` y el catálogo.

Pendiente: llevar los puntos 1 y 3, la ventana de 2,6 min y el patrón de `pkill` al propio
`RUNBOOK_CAMPANA.md`.

---

## 7. Pilotaje — tres corridas antes de la campaña

El protocolo pide **cinco** corridas de piloto; hay dos (`S21_piloto_A_02`, `S21_piloto_B_01`).
Faltan tres. Además, el bloque que escribe `condicion_inicial.json` se commiteó el 2026-09-04
(`cca442f`) y hasta ese día nunca había corrido contra un Gazebo vivo. Las dos cosas se cierran con
lo mismo.

Dos en B y una en A, para estrenar el relevo. Itinerarios tomados de las filas 2, 3 y 4 del
sorteo; el piloto no consume la fila, que se vuelve a correr en la campaña.

"""


def cierre(n_misiones):
    return f"""La condición A/B y los relevos que encabezan cada bloque son **lo esperado, no lo que se
declara**: el compositor deriva la condición de los niveles de origen y destino, y cuenta los
relevos desde `t_inicio_tramo2`. Si lo observado no coincide con el encabezado, eso *es* un
resultado y hay que mirarlo, no corregirlo.

---

## 9. Lo que me pasas a mí

Nada más que **los bags en `~/tesis_evidencia/`** y la nota de cada bloque. Yo corro, por cada uno:

```bash
python3 herramientas/diagnosticar_llegada.py ~/tesis_evidencia/S21_OE4_01 --robot robot1
python3 herramientas/componer_registro.py ~/tesis_evidencia/S21_OE4_01 --banco simulacion --campana OE4_simulacion --semilla 20260822 --salida Documentos/Evidencia/registros/S21_OE4_01.json
python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana OE4_simulacion
```

`analizar_campana.py` va **después de cada corrida**, no solo al final: es la única forma de
enterarse de que algo se registra mal en la corrida 2 y no en la 30. Si sale un error de
integridad, te aviso antes de que sigas.

Los pilotos llevan además `--piloto`; las {n_misiones} de la campaña **no** lo llevan.
"""


def main():
    misiones = leer_misiones()

    partes = [cabecera()]
    for titulo, cond, origen, destino, bag, oid, did, rel in PILOTOS:
        partes.append(bloque(titulo, cond, origen, destino, bag, oid, did, rel))

    partes.append(f"---\n\n## 8. Las {len(misiones)} misiones\n\n")
    for f in misiones:
        n = int(f["n"])
        cond = f["condicion"]
        partes.append(bloque(
            str(n), cond, f["origen_nombre"], f["destino_nombre"],
            f"S21_OE4_{n:02d}", f["origen_id"], f["destino_id"],
            1 if cond == "B" else 0))

    partes.append(cierre(len(misiones)))
    SALIDA.write_text("".join(partes), encoding="utf-8")
    print(f"Escrita {SALIDA.relative_to(RAIZ)}: "
          f"{len(PILOTOS)} pilotos + {len(misiones)} misiones de campaña.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
