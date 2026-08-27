# Plan de implementación del registro de misión (RF-25)

> Implementa [`ESQUEMA_REGISTRO_MISION.md`](ESQUEMA_REGISTRO_MISION.md), congelado el 2026-08-26 en
> la versión `1.0.0`. Ese documento dice **qué** se guarda y por qué; éste dice **en qué orden se
> construye y qué se sacrifica si el tiempo no alcanza**.

**Objetivo:** que cada misión de guiado deje un archivo JSON validado, compuesto desde un bag, con
las mismas marcas y el mismo veredicto tanto en simulación como en el vehículo físico.

**Arquitectura:** el registro no se escribe durante la misión. La misión graba un bag con una lista
fija de tópicos; después, `herramientas/componer_registro.py` lee ese bag y produce el JSON, que se
valida contra `Documentos/esquema_registro_mision.json` antes de escribirse. El coordinador solo
cambia en lo mínimo para que las marcas sean medibles: un reloj único, un identificador propio y una
publicación extraordinaria en cada cambio de etapa.

**Tecnologías:** Python 3.10 · ROS 2 Humble (`rosbag2_py`, `rosidl_runtime_py`) · `python3-jsonschema`
3.2.0 (JSON Schema draft-07, de los repos de Ubuntu 22.04) · `ros2 bag record`.

---

## Restricciones globales

Aplican a todas las tareas. Están copiadas de donde mandan; no reinterpretar.

- **Idioma español** en código, comentarios, docstrings, mensajes y commits. Identificadores ROS en
  inglés cuando el ecosistema lo exige (`odom`, `cmd_vel`).
- **Sin acentos ni eñes en el código fuente `.py` y `.sh`** — es la convención del repo (ver
  `verificar_contrato.py`, `planificador.py`). Los documentos `.md` sí llevan acentos.
- **Las pruebas del repo son guiones sueltos `prueba_*.py`, no `pytest`.** Siguen el patrón de
  `Robot/aws-deepracer/coordinacion/test/prueba_planificador.py`: función `check(nombre, ok, detalle)`,
  lista `fallos`, salida `0` si todo pasa y `1` si algo falla. No introducir `pytest` en este plan.
- **Las herramientas viven en `herramientas/`**, con `#!/usr/bin/env python3`, docstring de uso al
  principio, y deducen la raíz del repositorio en vez de llevar rutas absolutas. Lo comprueba
  `herramientas/verificar_repositorio.sh`, que debe seguir dando **12 de 12**.
- **Tolerancia de llegada: `0,25 m`.** Ya está en `coordinador.py:50` como `TOLERANCIA_LLEGADA_M`.
  No declarar otra constante; importarla.
- **Umbral de primer movimiento: `|v| ≥ 0,02 m/s` sostenido en tres muestras consecutivas**
  (§3.5 del esquema).
- **Versión del esquema: `1.0.0`.** Cualquier cambio sigue las reglas de la §7 del esquema.
- **Commits sin `Co-Authored-By`.** Mensajes en español, describiendo el cambio.
- **No comitear nada sin que Santiago lo pida.** Los pasos «Commit» de este plan indican el punto de
  corte natural; ejecutarlos requiere luz verde.

---

## Reparto en el tiempo, que es lo que manda

Queda **jueves 27 y viernes 28 de agosto**. El viernes por la noche es el corte semanal, así que el
tiempo real de implementación es el jueves y la mañana del viernes está comprometida con el frente B
(mapa del laboratorio, corrida de ≥ 20 m, `rplidar_composition`, compilar `coordinacion_msgs` en la
tarjeta Jazzy).

**El orden de las tareas no es el orden lógico de construcción, es el orden del riesgo irreversible.**

| Tarea | Cuándo | Por qué en ese orden |
|---|---|---|
| **1** — coordinador: reloj, `mision_id`, marca extraordinaria | jue 27 a primera hora | Sin esto, el bag de la corrida del jueves nace con marcas de 1 s de resolución y con `mision_id` repetido. **Es el dato el que se pierde, y el dato no se puede recomponer después** |
| **2** — `grabar_mision.sh` | jue 27, seguida | Misma razón: si el jueves no se graba con la lista fija, la corrida no sirve de banco de pruebas y hay que repetirla |
| **— corrida de extremo a extremo con destino de nivel 2 —** | jue 27, media mañana | Es la actividad que ya estaba en `PLAN_S20.md`. Produce el primer bag completo y de paso la comparación de cúspides de **R12** |
| **3** — esquema JSON + validador | jue 27, tarde | No toca datos. Si se retrasa, no se pierde nada |
| **4** — compositor: funciones puras de marcas | jue 27, tarde | ídem |
| **5** — compositor: lectura de bag y ensamblado | jue 27 tarde / se puede desbordar | ídem |
| **6** — comprobación de integración sobre el bag real | vie 28 o después | Necesita que 1–5 estén hechas y que exista el bag del jueves |

**Criterio de aborto, decidido antes de empezar:** si a las **tareas 1 y 2 les llega el mediodía del
jueves sin estar cerradas**, se paran las tareas 3–6 y se hace la corrida igualmente con lo que haya,
porque una corrida grabada a medias vale más que un compositor perfecto sin datos.

**Qué se puede desbordar a S21 sin tocar el cronograma:** las tareas 3, 4, 5 y 6. La campaña de S24
es lo que fija el plazo real del compositor, y hasta ella hay tres semanas. **Lo que no se puede
desbordar es la 1 y la 2**, porque cada corrida que se haga sin ellas es una corrida que habrá que
repetir.

---

## Estructura de archivos

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg` | Contrato del estado. Se le añaden `origen_id` y `destino_id` | Modificar |
| `Robot/aws-deepracer/coordinacion/coordinacion/planificador.py` | Funciones puras de decisión. Se le añaden `condicion_de()` y `generar_mision_id()` | Modificar |
| `Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py` | Cableado ROS. Reloj único, id propio, marca extraordinaria | Modificar |
| `Robot/aws-deepracer/coordinacion/test/prueba_planificador.py` | Prueba sin ROS del módulo puro | Modificar |
| `herramientas/grabar_mision.sh` | Un bag por misión con lista fija de tópicos | Crear |
| `Documentos/esquema_registro_mision.json` | El esquema congelado, en JSON Schema draft-07 | Crear |
| `herramientas/componer_registro.py` | Bag → JSON validado. Contiene tanto las funciones puras de marcas como la lectura del bag | Crear |
| `herramientas/prueba_componer_registro.py` | Bag sintético + las seis comprobaciones de §5 del esquema | Crear |

`componer_registro.py` se queda en un solo archivo a propósito: las funciones puras y el lector de
bag son unas 300 líneas en total y separarlos obligaría a un paquete nuevo para nada. Si pasara de
~500 líneas, entonces sí conviene partirlo.

---

## Tarea 1: el coordinador deja marcas medibles

**Archivos:**
- Modificar: `Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg`
- Modificar: `Documentos/CONTRATO_INTERFACES.md` §5
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/planificador.py` (añadir al final del
  bloque de funciones auxiliares, antes de `planificar`)
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py:63-66, 91, 153-154, 158-216`
- Prueba: `Robot/aws-deepracer/coordinacion/test/prueba_planificador.py`

> **Un agujero que apareció al escribir este plan, y por qué se tapa aquí.**
>
> El bloque `solicitud` del esquema (§3.4) pide `origen_id` y `destino_id`. Los dos existen hoy
> **solo en el goal de `GuiarUsuario.action`** (líneas 12-13), y un goal de acción viaja por un
> servicio: **`ros2 bag` no graba servicios**. `EstadoMision` publica `destino_actual`, que en un
> tramo intermedio es el punto de transferencia y no el destino de la misión, y **el origen no se
> publica en ningún sitio**.
>
> O sea que el bloque `solicitud` no se podía componer desde el bag. Se tapa añadiendo dos campos
> `string` a `EstadoMision`. Se hace **en esta tarea y no más tarde** por lo mismo que la tarea 1 va
> primero: el viernes se compila `coordinacion_msgs` en la tarjeta Jazzy del carro, y cambiar el
> mensaje después obliga a recompilar las dos máquinas otra vez.
>
> Esto **no cambia el esquema del registro** — ni un campo, ni un tipo — así que la versión sigue
> siendo `1.0.0` y la §7 del esquema no aplica. Cambia de dónde sale un dato, no cuál.

**Interfaces:**
- Consume: `catalogo` (lista de dicts con `id`, `nivel`, `pose`), tal como lo carga hoy
  `_cargar_catalogo()`.
- Produce:
  - `condicion_de(catalogo, origen_id, destino_id) -> str` — devuelve `"A"`, `"B"` o `"X"`.
  - `generar_mision_id(prefijo: str, condicion: str, ahora: datetime) -> str`.
  - En el bag: `/coordinacion/estado_mision` con `mision_id` único y una publicación en el instante
    exacto de cada cambio de etapa.

> **Dos decisiones que refinan la §2.1 del esquema, y por qué.**
>
> La §2.1 propone `<campana>_<condicion><nnn>`, p. ej. `S24_B007`. Un consecutivo en memoria **no
> funciona**: la §6.4 del protocolo manda un `gzserver` nuevo por corrida, así que el contador se
> reinicia en cada una y las treinta misiones de S24 se llamarían todas `001`. Se sustituye el
> consecutivo por una marca de tiempo, que es única sin necesidad de que nadie lleve la cuenta.
>
> El parámetro del coordinador se llama **`prefijo_mision`**, no `campana`, para que no se confunda
> con el campo `campana` del registro, que lo pone el compositor desde su línea de órdenes.

- [ ] **Paso 1: escribir las comprobaciones que fallan**

En `prueba_planificador.py`, añadir al final de `main()` antes del resumen de fallos:

```python
    # --- Identificador de mision y condicion experimental --------------------
    # Ver Documentos/ESQUEMA_REGISTRO_MISION.md §2.1 y §3.2.
    from coordinacion.planificador import condicion_de, generar_mision_id
    import datetime

    check("condicion_de: intra-nivel es A",
          condicion_de(catalogo, "piso1_escalera", "piso1_bano") == "A")
    check("condicion_de: inter-nivel es B",
          condicion_de(catalogo, "piso1_escalera", "piso2_escalera") == "B")
    check("condicion_de: id desconocido no revienta, devuelve X",
          condicion_de(catalogo, "no_existe", "piso1_bano") == "X")

    t = datetime.datetime(2026, 8, 27, 14, 30, 52)
    check("mision_id con prefijo lleva campana, condicion y sello",
          generar_mision_id("S24", "B", t) == "S24_B_20260827_143052")
    check("mision_id sin prefijo es una corrida suelta",
          generar_mision_id("", "A", t) == "manual_20260827_143052")

    # El invariante que de verdad importa: dos misiones del mismo par origen /
    # destino en corridas distintas NO comparten identificador. Es justo lo que
    # fallaba al publicar pet.origen_id.
    t2 = datetime.datetime(2026, 8, 27, 14, 30, 53)
    check("dos misiones del mismo par no comparten id",
          generar_mision_id("S24", "B", t) != generar_mision_id("S24", "B", t2))
```

Comprobar antes que los ids `piso1_escalera`, `piso1_bano` y `piso2_escalera` existen en el catálogo:

```bash
python3 -c "import yaml; print([p['id'] for p in yaml.safe_load(open('Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml'))['puntos']])"
```

Si alguno no está, sustituirlo por dos ids reales del nivel 1 y uno del nivel 2 — no inventar.

- [ ] **Paso 2: correrla y ver que falla**

```bash
python3 Robot/aws-deepracer/coordinacion/test/prueba_planificador.py
```

Esperado: `ImportError: cannot import name 'condicion_de'`.

- [ ] **Paso 3: escribir las dos funciones puras**

En `planificador.py`, después de `_transferencia_de` y antes de `_colapsar`:

```python
def condicion_de(catalogo, origen_id, destino_id):
    """La condicion experimental de una mision: 'A' intra-nivel, 'B' inter-nivel.

    Devuelve 'X' si alguno de los dos ids no esta en el catalogo, en vez de
    lanzar: esta funcion se llama al ACEPTAR el goal, antes de planificar, y un
    identificador de mision tiene que salir siempre -tambien para la mision que
    va a fallar, que es justamente la que la tasa de exito necesita contar-.

    Ver §3.2 de Documentos/ESQUEMA_REGISTRO_MISION.md.
    """
    niveles = {p["id"]: int(p["nivel"]) for p in catalogo}
    if origen_id not in niveles or destino_id not in niveles:
        return "X"
    return "A" if niveles[origen_id] == niveles[destino_id] else "B"


def generar_mision_id(prefijo, condicion, ahora):
    """Identificador unico de mision. Refina la §2.1 del esquema de registro.

    Lleva marca de tiempo y no un consecutivo porque la §6.4 del protocolo manda
    un gzserver nuevo por corrida: un contador en memoria se reiniciaria en cada
    una y las treinta misiones de S24 se llamarian todas igual.

    'ahora' entra como argumento y no se lee aqui dentro para que la prueba sea
    determinista.
    """
    sello = ahora.strftime("%Y%m%d_%H%M%S")
    return f"{prefijo}_{condicion}_{sello}" if prefijo else f"manual_{sello}"
```

Y añadir `import datetime` a la cabecera del módulo si no está.

- [ ] **Paso 4: correrla y ver que pasa**

```bash
python3 Robot/aws-deepracer/coordinacion/test/prueba_planificador.py
```

Esperado: todas en `[OK ]`, incluidas las 240 combinaciones que ya había, y salida `0`.

- [ ] **Paso 5: añadir origen y destino al mensaje de estado**

En `Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg`, después de `string mision_id`:

```
string origen_id                # el punto de partida que pidio el usuario
string destino_id               # el destino FINAL, no el del tramo en curso
```

y debajo del bloque de campos, esta nota:

```
# 'destino_id' no es lo mismo que 'destino_actual.id': en una mision entre
# niveles, durante el tramo 1 el destino ACTUAL es el punto de transferencia y
# el destino de la MISION sigue siendo el del otro piso. Los dos hacen falta:
# uno para lo que la HRI muestra ahora, otro para saber que se pidio.
#
# Estan aqui, y no solo en el goal de GuiarUsuario.action, porque un goal de
# accion viaja por un servicio y 'ros2 bag' no graba servicios. Sin esto, el
# bloque 'solicitud' del registro de mision (RF-25) no se puede componer desde
# el bag. Ver §3.4 de Documentos/ESQUEMA_REGISTRO_MISION.md.
```

Reflejar los dos campos nuevos en la tabla de `EstadoMision` de
`Documentos/CONTRATO_INTERFACES.md` §5, con la misma razón en una línea.

- [ ] **Paso 6: cablearlas en el coordinador**

Tres ediciones en `coordinador.py`.

**(a) Parámetro nuevo.** Después de la línea 66 (`self.declare_parameter("espera_servidor_s", 20.0)`):

```python
        # Prefijo del identificador de mision. Lo pone quien lanza la campana;
        # vacio significa corrida suelta. Ver §2.1 de ESQUEMA_REGISTRO_MISION.md.
        self.declare_parameter("prefijo_mision", "")
        self.prefijo_mision = self.get_parameter("prefijo_mision").value
```

**(b) Marca extraordinaria.** Sustituir `_publicar_estado` y `_marcar` (líneas 153-154 y 218-224) por:

```python
    def _publicar_estado(self):
        self.pub_mision.publish(self.estado)

    def _marcar(self, etapa, robot, punto, mensaje, mision_id):
        self.estado.mision_id = mision_id
        self.estado.etapa = etapa
        self.estado.robot_activo = robot
        self.estado.destino_actual = self._a_msg(punto) if punto else PuntoInteres()
        self.estado.mensaje_usuario = mensaje
        self.estado.distancia_restante = self._distancia(robot, punto) if punto else 0.0
        # Marca extraordinaria: el latido de 1 Hz de la linea 91 sigue vivo para
        # la HRI, pero el cambio de etapa se publica en el instante en que ocurre.
        # El §3.2 del protocolo lo exige: 1 s de resolucion es demasiado grosero
        # para el hueco de relevo, que se espera en milisegundos.
        self._publicar_estado()
```

**(c) Reloj único e id propio.** En `_ejecutar`, sustituir las líneas 158-160 por:

```python
    def _ejecutar(self, goal_handle):
        pet = goal_handle.request
        # El mismo reloj que /clock cuando use_sim_time esta puesto. time.time()
        # lo ignora, y con RTF >= 0,99 las dos formas difieren hasta un 1 %: sobre
        # t_respuesta eso no es ruido, es sesgo. Ver §3 del protocolo.
        t0 = self.get_clock().now()
        condicion = condicion_de(self.catalogo, pet.origen_id, pet.destino_id)
        mision_id = generar_mision_id(
            self.prefijo_mision, condicion, datetime.datetime.now())
        # Se fijan una vez y no cambian en toda la mision. El destino ACTUAL si
        # cambia, y lo pone _marcar; estos dos son lo que se pidio.
        self.estado.origen_id = pet.origen_id
        self.estado.destino_id = pet.destino_id
        res = GuiarUsuario.Result()
```

Sustituir **las cuatro** apariciones de `res.tiempo_total_s = time.time() - t0` (líneas 175, 182,
200 y 210) por:

```python
            res.tiempo_total_s = (self.get_clock().now() - t0).nanoseconds * 1e-9
```

respetando la sangría de cada una.

Sustituir **las cuatro** apariciones de `pet.origen_id` como último argumento de `self._marcar(...)`
(líneas 172, 186, 194 y 206) por `mision_id`.

Añadir `import datetime` a la cabecera y ampliar la importación desde `planificador`:

```python
from coordinacion.planificador import (
    ASIGNACION_POR_DEFECTO, COMPLETADA, ErrorPlanificacion, FALLIDA, INACTIVA,
    condicion_de, generar_mision_id, planificar, yaw_a_cuaternion,
)
```

> **No tocar las líneas 361-365.** Ese `time.time()` con `time.sleep(0.05)` es un perro guardián que
> espera al servidor de acción, no una medida. Un guardián debe contar segundos de reloj de pared:
> si el simulador se congela, `/clock` se congela con él y la espera no vencería nunca.

- [ ] **Paso 7: comprobar que compila y arranca**

`coordinacion_msgs` cambió, así que hay que recompilarlo a él primero:

```bash
cd ~/deepracer_sim_ws && colcon build --symlink-install --packages-select coordinacion_msgs coordinacion && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p prefijo_mision:=prueba
```

Esperado: la línea `Coordinador listo. 31 puntos, asignacion {...}`. Cortar con Ctrl-C.

Si sale `ModuleNotFoundError: coordinacion_msgs`, falta `source install/setup.bash`. Si sale
`Unknown state 'start'`, alguien revirtió la migración a Humble (ver `Robot/README.md`).

Comprobar además que los campos nuevos viajan. Con el coordinador corriendo, en otra terminal:

```bash
ros2 interface show coordinacion_msgs/msg/EstadoMision | grep -n "origen_id\|destino_id"
```

Esperado: las dos líneas. Si no salen, `coordinacion_msgs` no se recompiló: repetir el `colcon build`.

- [ ] **Paso 8: commit**

```bash
git add Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg Documentos/CONTRATO_INTERFACES.md Robot/aws-deepracer/coordinacion/coordinacion/planificador.py Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py Robot/aws-deepracer/coordinacion/test/prueba_planificador.py
git commit -m "coordinador: reloj de simulacion, identificador de mision propio, marca extraordinaria de etapa y origen/destino en EstadoMision (RF-25)"
```

---

## Tarea 2: un bag por misión, con lista fija de tópicos

**Archivos:**
- Crear: `herramientas/grabar_mision.sh`

**Interfaces:**
- Consume: nada del código anterior; solo el grafo ROS vivo.
- Produce: un directorio de bag en `~/tesis_evidencia/<campana>/<nombre>/` que contiene, como mínimo,
  `/clock` y `/coordinacion/estado_mision`. La tarea 5 lo lee.

- [ ] **Paso 1: escribir el guion**

```bash
#!/usr/bin/env bash
# Graba UN bag por mision, con la lista de topicos fija de la §2.2 de
# Documentos/ESQUEMA_REGISTRO_MISION.md.
#
# La lista es fija a proposito: si cada corrida graba lo que le parece, el
# conjunto de datos no es homogeneo y la comparacion de S26 no se puede hacer.
# No es una precaucion teorica -los bags del 26-ago no traen /clock ni
# /coordinacion/estado_mision, que son justo los dos topicos de los que salen
# las marcas temporales, y por eso no sirven para componer un registro-.
#
# Uso:
#     herramientas/grabar_mision.sh <nombre_bag> [robot1 robot2 ...]
#
# Ejemplo:
#     herramientas/grabar_mision.sh S24_B_001 robot1 robot2
#
# Corta con Ctrl-C cuando la mision termine. Un bag por mision, no uno por
# sesion: la §6.4 del protocolo manda un gzserver nuevo por corrida, asi que la
# frontera entre misiones ya es una frontera entre procesos.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Uso: $0 <nombre_bag> [robot1 robot2 ...]" >&2
    exit 1
fi

NOMBRE="$1"; shift
ROBOTS=("$@")
if [ ${#ROBOTS[@]} -eq 0 ]; then ROBOTS=(robot1 robot2); fi

DESTINO="${TESIS_EVIDENCIA:-$HOME/tesis_evidencia}/$NOMBRE"
if [ -e "$DESTINO" ]; then
    echo "Ya existe $DESTINO. Un bag por mision: elige otro nombre o borralo." >&2
    exit 1
fi

TOPICOS=(/clock /coordinacion/estado_mision /coordinacion/puntos_interes /tf /tf_static)
for NS in "${ROBOTS[@]}"; do
    TOPICOS+=("/$NS/odom" "/$NS/amcl_pose" "/$NS/scan" "/$NS/cmd_vel" "/$NS/plan")
done

# Se avisa de los que no estan publicandose, pero no se aborta: un robot puede
# no haber arrancado todavia y ros2 bag record los recoge cuando aparezcan.
VIVOS="$(ros2 topic list)"
for T in "${TOPICOS[@]}"; do
    if ! grep -qx -- "$T" <<< "$VIVOS"; then
        echo "AVISO: $T no se esta publicando ahora mismo." >&2
    fi
done

echo "Grabando en $DESTINO. Ctrl-C para cerrar el bag."
mkdir -p "$(dirname "$DESTINO")"
exec ros2 bag record -o "$DESTINO" "${TOPICOS[@]}"
```

- [ ] **Paso 2: darle permiso de ejecución y comprobar que valida sus argumentos**

```bash
chmod +x herramientas/grabar_mision.sh && herramientas/grabar_mision.sh
```

Esperado: `Uso: ...` y código de salida 1. **Esto se puede comprobar sin simulación.**

- [ ] **Paso 3: comprobar contra un grafo vivo**

Con la simulación lanzada y el coordinador corriendo, en otra terminal:

```bash
herramientas/grabar_mision.sh humo_$(date +%H%M%S) robot1
```

Esperado: ningún `AVISO` sobre `/clock` ni `/coordinacion/estado_mision`. Dejarlo 10 s, Ctrl-C, y:

```bash
ros2 bag info ~/tesis_evidencia/humo_*
```

Esperado: `/clock` y `/coordinacion/estado_mision` en la lista, con recuento mayor que cero.

Si `/clock` sale con cero mensajes, la simulación no está publicando tiempo: comprobar que Gazebo
corre y que los nodos llevan `use_sim_time: true`. **Es un fallo que hay que resolver antes de la
corrida, no después.**

- [ ] **Paso 4: commit**

```bash
git add herramientas/grabar_mision.sh
git commit -m "grabar_mision.sh: un bag por mision con la lista fija de topicos del esquema RF-25"
```

---

## — Hito: la corrida de extremo a extremo del jueves —

No es una tarea de este plan, es la actividad que ya estaba en `PLAN_S20.md`. Se anota aquí porque
las tareas 1 y 2 existen para que esta corrida produzca datos utilizables, y la tarea 6 depende de
ella.

Con la simulación lanzada, el coordinador con `prefijo_mision:=S20_piloto` y
`grabar_mision.sh S20_piloto_01 robot1 robot2` grabando, pedir **una misión inter-nivel** (condición
B) por la acción `/coordinacion/guiar_usuario`. Guardar además el número de cúspides del plan para
la comparación de **R12**.

Ese bag es el banco de pruebas de la tarea 6 y la primera evidencia de RF-24.

---

## Tarea 3: el esquema en JSON Schema, y un validador

**Archivos:**
- Crear: `Documentos/esquema_registro_mision.json`
- Crear: `herramientas/prueba_componer_registro.py` (solo la parte de validación; la tarea 5 le añade
  el resto)

**Interfaces:**
- Consume: nada.
- Produce: el archivo de esquema, y en `prueba_componer_registro.py` la función
  `registro_valido() -> dict` que devuelve un registro mínimo que pasa la validación. Las tareas 4 y
  5 parten de él para construir sus casos.

- [ ] **Paso 1: instalar la dependencia**

```bash
sudo apt install -y python3-jsonschema
```

Esperado: instala la versión 3.2.0. Comprobar con
`python3 -c "import jsonschema; print(jsonschema.__version__)"`.

3.2.0 implementa draft-07, que es el que trae `if`/`then` — las restricciones cruzadas de la §4.3 del
esquema se expresan con eso. **Se instala solo en el PC**, no en la tarjeta del carro: el carro graba
el bag y el PC compone.

- [ ] **Paso 2: escribir el registro válido de referencia y las comprobaciones que fallan**

Crear `herramientas/prueba_componer_registro.py`:

```python
#!/usr/bin/env python3
"""Prueba del compositor de registros de mision. Sin ROS corriendo y sin Gazebo.

    python3 herramientas/prueba_componer_registro.py

Comprueba las seis cosas que pide la §5 de Documentos/ESQUEMA_REGISTRO_MISION.md.
Tarda segundos, asi que no hay excusa para no correrlo antes de cada campana.
"""

import copy
import json
import os
import sys

import jsonschema

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESQUEMA = os.path.join(RAIZ, "Documentos", "esquema_registro_mision.json")

fallos = []


def check(nombre, ok, detalle=""):
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre} {detalle}")
    if not ok:
        fallos.append(nombre)


def registro_valido():
    """Un registro de condicion B en simulacion, con exito. Base de los casos."""
    return {
        "esquema_version": "1.0.0",
        "mision": {
            "mision_id": "S24_B_20260827_143052",
            "campana": "S24_simulacion",
            "banco": "simulacion",
            "condicion": "B",
            "semilla": 1234,
            "es_piloto": False,
        },
        "procedencia": {
            "commit": "abc1234", "etiqueta": "", "repositorio_limpio": True,
            "distro": "humble", "mundo": "mundo_definitivo_piso1.world",
            "mapa": "mapa_piso1.yaml", "catalogo_puntos": "puntos_interes.yaml",
            "catalogo_sha256": "0" * 64, "bag": "S24_B_001",
            "fecha_utc": "2026-08-27T14:30:52Z",
        },
        "solicitud": {
            "origen_id": "piso1_escalera", "destino_id": "piso2_escalera",
            "nivel_origen": 1, "nivel_destino": 2, "entre_niveles": True,
            "tramos": [],
        },
        "marcas": {
            "reloj": "/clock", "t_solicitud": 0.0, "t_robot_activo": 0.2,
            "t_primer_movimiento": 0.9, "t_fin_tramo1": 40.0,
            "t_inicio_tramo2": 41.5, "t_completada": 95.0,
        },
        "verdad_de_terreno": {
            "fuente": "gazebo_worldpose_via_odom", "error_posicion_m": 0.19,
            "pose_final": {"x": -19.4, "y": 5.9, "yaw": -1.57},
            "incertidumbre_m": 0.0, "medido_por": "automatico", "nota": "",
        },
        "veredicto": {
            "exito": True, "c1_posicion": True,
            "c2_completada_sin_fallida": True, "c3_relevo": True,
            "motivo_fallo": "",
        },
        "descriptivas": {
            "error_rumbo_rad": 0.05, "desviacion_z_m": {"robot1": 1.9e-06},
            "distancia_recorrida_m": 31.2, "num_cuspides": 0,
            "tiempo_total_s": 95.0, "deriva_map_odom_m": 1.977,
        },
        "salud_del_banco": {
            "rtf": 0.995, "controladores_activos": {"robot1": "7/7"},
            "gzserver_vivo_al_final": True, "descartada": False,
            "causa_descarte": None,
        },
        "traza": {"bag": "S24_B_001", "decimada_hz": 5.0, "puntos": []},
    }


def valida(registro, esquema):
    """True si el registro cumple el esquema."""
    try:
        jsonschema.validate(registro, esquema)
        return True
    except jsonschema.ValidationError:
        return False


def pruebas_de_esquema(esquema):
    check("el registro de referencia es valido", valida(registro_valido(), esquema))

    # §4.3, restriccion 1: simulacion exige /clock, oraculo y RTF.
    r = registro_valido(); r["marcas"]["reloj"] = "pared"
    check("simulacion con reloj de pared se rechaza", not valida(r, esquema))
    r = registro_valido(); r["salud_del_banco"]["rtf"] = None
    check("simulacion sin RTF se rechaza", not valida(r, esquema))

    # §4.3, restriccion 2: el banco fisico no tiene oraculo ni RTF.
    r = registro_valido()
    r["mision"]["banco"] = "fisico"
    r["marcas"]["reloj"] = "pared"
    r["verdad_de_terreno"]["fuente"] = "cinta_metrica"
    r["verdad_de_terreno"]["pose_final"] = None
    r["verdad_de_terreno"]["incertidumbre_m"] = 0.01
    r["verdad_de_terreno"]["medido_por"] = "Santiago"
    r["salud_del_banco"]["rtf"] = None
    r["salud_del_banco"]["gzserver_vivo_al_final"] = None
    r["descriptivas"]["deriva_map_odom_m"] = None
    check("el registro fisico equivalente es valido", valida(r, esquema))
    r["verdad_de_terreno"]["pose_final"] = {"x": 0.0, "y": 0.0, "yaw": 0.0}
    check("fisico con pose_final se rechaza (seria llamar verdad a rf2o)",
          not valida(r, esquema))

    # §4.3, restriccion 3: condicion A no tiene relevo.
    r = registro_valido()
    r["mision"]["condicion"] = "A"
    r["solicitud"]["entre_niveles"] = False
    r["marcas"]["t_fin_tramo1"] = None
    r["marcas"]["t_inicio_tramo2"] = None
    r["veredicto"]["c3_relevo"] = None
    check("el registro de condicion A es valido", valida(r, esquema))
    r["marcas"]["t_fin_tramo1"] = 40.0
    check("condicion A con marca de relevo se rechaza", not valida(r, esquema))

    # §4.3, restriccion 4: un exito no puede tener marcas incompletas.
    r = registro_valido(); r["marcas"]["t_completada"] = None
    check("exito sin t_completada se rechaza", not valida(r, esquema))

    # §4.3, restriccion 5, y §3.9: la lista de descartes es cerrada.
    r = registro_valido()
    r["salud_del_banco"]["descartada"] = True
    r["salud_del_banco"]["causa_descarte"] = "rtf_bajo"
    check("descarte por una causa del §8 es valido", valida(r, esquema))
    r["salud_del_banco"]["causa_descarte"] = "amcl_se_perdio"
    check("descarte por 'amcl se perdio' se rechaza (§8: eso es lo que se mide)",
          not valida(r, esquema))
    r = registro_valido(); r["salud_del_banco"]["descartada"] = True
    check("descarte sin causa se rechaza", not valida(r, esquema))


def main():
    with open(ESQUEMA, encoding="utf-8") as f:
        esquema = json.load(f)
    print("Esquema del registro de mision")
    pruebas_de_esquema(esquema)
    print(f"\n{len(fallos)} fallo(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Paso 3: correrla y ver que falla**

```bash
python3 herramientas/prueba_componer_registro.py
```

Esperado: `FileNotFoundError` sobre `Documentos/esquema_registro_mision.json`.

- [ ] **Paso 4: escribir el esquema**

Crear `Documentos/esquema_registro_mision.json`. Estructura obligatoria: `"$schema"` draft-07,
`"required"` con los nueve bloques, `"additionalProperties": false` en cada bloque (un campo con el
nombre mal escrito debe fallar, no colarse), y los cinco `if`/`then` de la §4.3. Esqueleto de las
partes que no son mecánicas:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Registro de mision (RF-25), version 1.0.0",
  "type": "object",
  "additionalProperties": false,
  "required": ["esquema_version", "mision", "procedencia", "solicitud", "marcas",
               "verdad_de_terreno", "veredicto", "descriptivas",
               "salud_del_banco", "traza"],
  "properties": {
    "esquema_version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
    "mision": {
      "type": "object", "additionalProperties": false,
      "required": ["mision_id", "campana", "banco", "condicion", "semilla", "es_piloto"],
      "properties": {
        "mision_id": {"type": "string", "minLength": 1},
        "campana": {"type": "string"},
        "banco": {"enum": ["simulacion", "fisico"]},
        "condicion": {"enum": ["A", "B"]},
        "semilla": {"type": ["integer", "null"]},
        "es_piloto": {"type": "boolean"}
      }
    },
    "salud_del_banco": {
      "type": "object", "additionalProperties": false,
      "required": ["rtf", "controladores_activos", "gzserver_vivo_al_final",
                   "descartada", "causa_descarte"],
      "properties": {
        "rtf": {"type": ["number", "null"]},
        "controladores_activos": {"type": "object"},
        "gzserver_vivo_al_final": {"type": ["boolean", "null"]},
        "descartada": {"type": "boolean"},
        "causa_descarte": {
          "comentario": "Lista CERRADA del §8 del protocolo. 'AMCL se perdio' y 'no encontro ruta' NO estan, y no es un olvido: son precisamente los modos de fallo que el experimento existe para cuantificar.",
          "enum": ["caida_gazebo", "controladores_incompletos", "rtf_bajo",
                   "fallo_anfitrion", null]
        }
      }
    }
  },
  "allOf": [
    {
      "comentario": "§4.3, restriccion 1",
      "if": {"properties": {"mision": {"properties": {"banco": {"const": "simulacion"}}}}},
      "then": {
        "properties": {
          "marcas": {"properties": {"reloj": {"const": "/clock"}}},
          "verdad_de_terreno": {
            "properties": {"fuente": {"const": "gazebo_worldpose_via_odom"}}},
          "salud_del_banco": {"properties": {"rtf": {"type": "number"}}}
        }
      }
    },
    {
      "comentario": "§4.3, restriccion 2",
      "if": {"properties": {"mision": {"properties": {"banco": {"const": "fisico"}}}}},
      "then": {
        "properties": {
          "verdad_de_terreno": {
            "properties": {"fuente": {"const": "cinta_metrica"},
                           "pose_final": {"type": "null"}}},
          "salud_del_banco": {"properties": {"rtf": {"type": "null"}}},
          "descriptivas": {"properties": {"deriva_map_odom_m": {"type": "null"}}}
        }
      }
    },
    {
      "comentario": "§4.3, restriccion 3: condicion A no tiene relevo",
      "if": {"properties": {"mision": {"properties": {"condicion": {"const": "A"}}}}},
      "then": {
        "properties": {
          "marcas": {"properties": {"t_fin_tramo1": {"type": "null"},
                                    "t_inicio_tramo2": {"type": "null"}}},
          "veredicto": {"properties": {"c3_relevo": {"type": "null"}}}
        }
      }
    },
    {
      "comentario": "§4.3, restriccion 4: un exito con marcas incompletas es un error del compositor, no un dato",
      "if": {"properties": {"veredicto": {"properties": {"exito": {"const": true}}}}},
      "then": {"properties": {"marcas": {"properties": {"t_completada": {"type": "number"}}}}}
    },
    {
      "comentario": "§4.3, restriccion 5",
      "if": {"properties": {"salud_del_banco": {"properties": {"descartada": {"const": true}}}}},
      "then": {"properties": {"salud_del_banco": {"properties": {"causa_descarte": {"type": "string"}}}}}
    }
  ]
}
```

Los bloques `procedencia`, `solicitud`, `marcas`, `verdad_de_terreno`, `veredicto`, `descriptivas` y
`traza` se completan igual, campo por campo, copiando los tipos de las tablas de la §3 del esquema.
**Qué admite `null` y qué no**, porque aquí es donde el esquema o aprieta de más o deja pasar basura:

| Campo | Tipo | Por qué |
|---|---|---|
| las siete `marcas` (salvo `reloj`) | `["number", "null"]` | una marca es `null` cuando el evento no ocurrió (§3.5) |
| `error_posicion_m` | `["number", "null"]` | §4.4: `null` es «pendiente de medir» |
| `veredicto.exito`, `c1_posicion`, `c3_relevo` | `["boolean", "null"]` | sin medida no hay veredicto, y no se inventa |
| `veredicto.c2_completada_sin_fallida` | `boolean` | siempre se puede decidir desde el bag |
| `error_rumbo_rad`, `tiempo_total_s`, `deriva_map_odom_m` | `["number", "null"]` | descriptivas que pueden no estar |
| `num_cuspides`, `distancia_recorrida_m` | `integer` / `number` | siempre salen del bag, aunque sean cero |
| `nivel_origen`, `nivel_destino` | `["integer", "null"]` | `null` si el id no está en el catálogo |
| `procedencia.etiqueta` | `string` | cadena vacía si el commit no tiene etiqueta, no `null` |

> **Cuidado con una trampa de draft-07:** dentro de un `if`, si la propiedad padre no existe la
> condición se cumple por vacío. Como todos los bloques están en `required` en la raíz, el problema
> no se da aquí, pero si se añade un bloque opcional en el futuro hay que envolver el `if` con su
> propio `required`.

- [ ] **Paso 5: correrla y ver que pasa**

```bash
python3 herramientas/prueba_componer_registro.py
```

Esperado: las trece comprobaciones en `[OK ]`, `0 fallo(s)`, salida `0`.

Si «el registro de referencia es valido» falla, hay un campo del esquema que no cuadra con
`registro_valido()`: correr a mano `jsonschema.validate` y leer el mensaje, que dice la ruta exacta.
**No relajar el esquema para que pase la prueba** — el esquema es el congelado; lo que se corrige es
el registro de referencia, salvo que el esquema esté mal transcrito de la §3.

- [ ] **Paso 6: commit**

```bash
git add Documentos/esquema_registro_mision.json herramientas/prueba_componer_registro.py
git commit -m "esquema del registro de mision en JSON Schema, con las cinco restricciones cruzadas comprobadas"
```

---

## Tarea 4: las funciones puras que sacan las marcas

**Archivos:**
- Crear: `herramientas/componer_registro.py`
- Modificar: `herramientas/prueba_componer_registro.py`

**Interfaces:**
- Consume: `registro_valido()` de la tarea 3.
- Produce, para la tarea 5:
  - `primer_movimiento(muestras) -> float | None` — `muestras` es una lista de `(t, vx, vy)` en
    segundos y m/s.
  - `marcas_de(estados, movimientos, condicion) -> dict` — `estados` es una lista de
    `(t, etapa, robot_activo, mision_id)`; `movimientos` es `{robot: [(t, vx, vy), ...]}`.
  - `veredicto_de(marcas, estados, error_posicion_m, condicion, num_relevos) -> dict`.

- [ ] **Paso 1: escribir las comprobaciones que fallan**

Añadir a `prueba_componer_registro.py`, antes de `main()`:

```python
sys.path.insert(0, AQUI)
from componer_registro import (  # noqa: E402
    marcas_de, primer_movimiento, veredicto_de,
    INACTIVA, TRAMO_1, TRANSFERENCIA, TRAMO_2, COMPLETADA, FALLIDA,
)


def pruebas_de_marcas():
    # §3.5: |v| >= 0,02 m/s en TRES muestras consecutivas. Un pico aislado de
    # ruido del estimador no puede disparar t_primer_movimiento: adelantaria la
    # marca y t_respuesta saldria mas corto de lo real.
    ruido = [(0.0, 0.0, 0.0), (0.1, 0.5, 0.0), (0.2, 0.0, 0.0),
             (0.3, 0.0, 0.0), (0.4, 0.1, 0.0), (0.5, 0.1, 0.0),
             (0.6, 0.1, 0.0)]
    check("un pico aislado NO dispara el primer movimiento",
          primer_movimiento(ruido) == 0.4, f"-> {primer_movimiento(ruido)}")
    check("robot quieto no tiene primer movimiento",
          primer_movimiento([(0.0, 0.0, 0.0), (0.1, 0.001, 0.0)]) is None)
    check("velocidad puramente lateral tambien cuenta",
          primer_movimiento([(0.0, 0.0, 0.1)] * 3) == 0.0)

    # Condicion B completa.
    estados_b = [
        (10.0, INACTIVA, "", "m1"), (10.2, TRAMO_1, "robot1", "m1"),
        (40.0, TRANSFERENCIA, "robot1", "m1"), (41.0, TRAMO_2, "robot2", "m1"),
        (95.0, COMPLETADA, "robot2", "m1"),
    ]
    mov = {"robot1": [(10.9, 0.3, 0.0)] * 3, "robot2": [(41.5, 0.3, 0.0)] * 3}
    mov["robot1"] = [(10.9, 0.3, 0.0), (11.0, 0.3, 0.0), (11.1, 0.3, 0.0)]
    mov["robot2"] = [(41.5, 0.3, 0.0), (41.6, 0.3, 0.0), (41.7, 0.3, 0.0)]
    m = marcas_de(estados_b, mov, "B")
    check("t_solicitud es el primer estado no INACTIVA", m["t_solicitud"] == 10.2)
    check("t_fin_tramo1 es el primer TRANSFERENCIA", m["t_fin_tramo1"] == 40.0)
    check("t_inicio_tramo2 es el primer movimiento del segundo robot",
          m["t_inicio_tramo2"] == 41.5)
    check("t_completada es el primer COMPLETADA", m["t_completada"] == 95.0)

    # Condicion A: los campos de relevo van null, no cero.
    estados_a = [(5.0, TRAMO_1, "robot1", "m2"), (30.0, COMPLETADA, "robot1", "m2")]
    ma = marcas_de(estados_a, {"robot1": [(5.5, 0.3, 0.0)] * 3}, "A")
    check("condicion A deja las dos marcas de relevo en null",
          ma["t_fin_tramo1"] is None and ma["t_inicio_tramo2"] is None)

    # Una mision que pasa por FALLIDA no es exito, aunque despues llegue
    # COMPLETADA: es el caso del reintento manual.
    estados_f = estados_b[:3] + [(50.0, FALLIDA, "robot1", "m1"),
                                 (95.0, COMPLETADA, "robot2", "m1")]
    v = veredicto_de(marcas_de(estados_f, mov, "B"), estados_f, 0.19, "B", 1)
    check("pasar por FALLIDA pone c2 en false", v["c2_completada_sin_fallida"] is False)
    check("y el exito es false aunque c1 y c3 esten en verde", v["exito"] is False)

    # R3: fallar por posicion tiene que quedar distinguible de fallar por otra cosa.
    v = veredicto_de(marcas_de(estados_b, mov, "B"), estados_b, 1.98, "B", 1)
    check("llegada fuera de tolerancia pone c1 en false y solo c1",
          v["c1_posicion"] is False and v["c2_completada_sin_fallida"] is True
          and v["c3_relevo"] is True)

    # Sin medida de cinta todavia (§4.4): el veredicto no se inventa.
    v = veredicto_de(marcas_de(estados_b, mov, "B"), estados_b, None, "B", 1)
    check("sin error medido, c1 y exito van null", v["c1_posicion"] is None
          and v["exito"] is None)
```

y llamarla desde `main()` con `print("\nMarcas y veredicto")` delante.

- [ ] **Paso 2: correrla y ver que falla**

```bash
python3 herramientas/prueba_componer_registro.py
```

Esperado: `ModuleNotFoundError: No module named 'componer_registro'`.

- [ ] **Paso 3: escribir las funciones puras**

Crear `herramientas/componer_registro.py`:

```python
#!/usr/bin/env python3
"""Compone el registro de una mision a partir de su bag. Ver
Documentos/ESQUEMA_REGISTRO_MISION.md.

    python3 herramientas/componer_registro.py <bag> --banco simulacion \
        --campana S24_simulacion --salida registros/S24_B_001.json

No corre durante la mision, y eso es deliberado: RNF-06 exige RTF >= 0,99 y un
registrador serializando a 50 Hz compite por la CPU con dos Gazebo en el mismo
equipo. El bag sigue siendo la fuente; esto solo lo lee.

Codigo de salida: 0 si el registro sale y valida, 1 si no. Nunca escribe un
registro a medias: un registro con marcas en null seria indistinguible de una
mision que fallo.
"""

import argparse
import json
import math
import os
import sys

# Constantes de EstadoMision.msg. Se copian a proposito en vez de importar
# coordinacion_msgs: esta herramienta tiene que poder correr sobre un bag sin
# el workspace compilado, p. ej. en el portatil de quien analice los datos.
INACTIVA, TRAMO_1, TRANSFERENCIA, TRAMO_2, COMPLETADA, FALLIDA = 0, 1, 2, 3, 4, 5

UMBRAL_MOVIMIENTO_MS = 0.02
MUESTRAS_CONSECUTIVAS = 3
TOLERANCIA_LLEGADA_M = 0.25   # la misma de coordinador.py:50 y del §5 del protocolo
ESQUEMA_VERSION = "1.0.0"


def primer_movimiento(muestras, umbral=UMBRAL_MOVIMIENTO_MS,
                      consecutivas=MUESTRAS_CONSECUTIVAS):
    """Instante del primer movimiento sostenido, o None si el robot nunca arranco.

    'muestras' es una lista de (t, vx, vy) ordenada por t.

    Se exigen TRES muestras seguidas por encima del umbral, y se devuelve el
    instante de la PRIMERA de las tres. Un pico aislado de ruido del estimador
    adelantaria la marca y t_respuesta saldria mas corto de lo que fue.
    """
    seguidas = 0
    for i, (t, vx, vy) in enumerate(muestras):
        if math.hypot(vx, vy) >= umbral:
            seguidas += 1
            if seguidas == consecutivas:
                return muestras[i - consecutivas + 1][0]
        else:
            seguidas = 0
    return None


def _primero(estados, predicado):
    """Instante del primer estado que cumple el predicado, o None."""
    for t, etapa, robot, _ in estados:
        if predicado(etapa, robot):
            return t
    return None


def marcas_de(estados, movimientos, condicion):
    """Las siete marcas de la §3.5, en segundos del mismo reloj.

    'estados'     lista de (t, etapa, robot_activo, mision_id) ordenada por t.
    'movimientos' {robot: [(t, vx, vy), ...]}.
    'condicion'   'A' o 'B'.

    Una marca va None cuando el evento no ocurrio, sea porque la condicion no lo
    contempla o porque la mision termino antes de llegar a el. Los dos casos se
    distinguen leyendo 'condicion' y el veredicto, no la marca.
    """
    t_solicitud = _primero(estados, lambda e, r: e != INACTIVA)
    t_robot_activo = _primero(estados, lambda e, r: e == TRAMO_1 and r)

    robot_1 = next((r for _, e, r, _ in estados if e == TRAMO_1 and r), None)
    robot_2 = next((r for _, e, r, _ in estados if e == TRAMO_2 and r), None)

    m = {
        "reloj": "/clock",
        "t_solicitud": t_solicitud,
        "t_robot_activo": t_robot_activo,
        "t_primer_movimiento": primer_movimiento(movimientos.get(robot_1, [])),
        "t_fin_tramo1": None,
        "t_inicio_tramo2": None,
        "t_completada": _primero(estados, lambda e, r: e == COMPLETADA),
    }
    if condicion == "B":
        m["t_fin_tramo1"] = _primero(estados, lambda e, r: e == TRANSFERENCIA)
        m["t_inicio_tramo2"] = primer_movimiento(movimientos.get(robot_2, []))
    return m


def veredicto_de(marcas, estados, error_posicion_m, condicion, num_relevos):
    """Las tres condiciones del §3.3 del protocolo, por separado.

    Se guardan sueltas y no solo su AND porque si la tasa de exito sale baja hay
    que poder decir CUAL fallo. Con R3 abierto se espera exactamente eso: c1 en
    rojo con c2 y c3 en verde, que es un diagnostico. Un 'exito: false' suelto
    no lo es.

    error_posicion_m None significa 'pendiente de medir' (§4.4, banco fisico):
    entonces c1 y exito van None y el analizador rechaza el registro. No se
    inventa un veredicto.
    """
    c1 = None if error_posicion_m is None else error_posicion_m <= TOLERANCIA_LLEGADA_M
    hubo_fallida = any(e == FALLIDA for _, e, _, _ in estados)
    c2 = marcas["t_completada"] is not None and not hubo_fallida
    c3 = (num_relevos == 1) if condicion == "B" else None

    condiciones = [c1, c2] + ([c3] if condicion == "B" else [])
    exito = None if c1 is None else all(condiciones)

    motivo = ""
    if exito is False:
        partes = []
        if c1 is False:
            partes.append(f"llegada a {error_posicion_m:.3f} m, fuera de "
                          f"{TOLERANCIA_LLEGADA_M} m")
        if not c2:
            partes.append("la mision no llego a COMPLETADA sin pasar por FALLIDA")
        if condicion == "B" and c3 is False:
            partes.append(f"{num_relevos} relevo(s), se esperaba 1")
        motivo = "; ".join(partes)

    return {"exito": exito, "c1_posicion": c1, "c2_completada_sin_fallida": c2,
            "c3_relevo": c3, "motivo_fallo": motivo}
```

- [ ] **Paso 4: correrla y ver que pasa**

```bash
python3 herramientas/prueba_componer_registro.py
```

Esperado: las trece de la tarea 3 más las once nuevas, todas en `[OK ]`, salida `0`.

Si «un pico aislado NO dispara el primer movimiento» falla devolviendo `0.1`, el bucle está
devolviendo el instante de la tercera muestra en vez del de la primera: revisar el índice
`i - consecutivas + 1`.

- [ ] **Paso 5: commit**

```bash
git add herramientas/componer_registro.py herramientas/prueba_componer_registro.py
git commit -m "componer_registro: marcas temporales y veredicto como funciones puras, probadas sin ROS"
```

---

## Tarea 5: leer el bag y ensamblar el registro

**Archivos:**
- Modificar: `herramientas/componer_registro.py`
- Modificar: `herramientas/prueba_componer_registro.py`

**Interfaces:**
- Consume: `marcas_de`, `veredicto_de`, `primer_movimiento` de la tarea 4; el esquema de la tarea 3.
- Produce: `leer_bag(ruta) -> dict[str, list[tuple[float, object]]]` y el ejecutable de línea de
  órdenes. La tarea 6 lo usa sobre el bag real.

- [ ] **Paso 1: escribir la comprobación de extremo a extremo, que falla**

Añadir a `prueba_componer_registro.py`:

```python
def bag_sintetico(ruta):
    """Escribe un bag minimo de condicion B. Sin Gazebo y sin simulacion.

    Es lo que permite probar el compositor de forma determinista: los bags de
    ~/tesis_evidencia/S20_localizacion/ no traen /clock ni estado_mision, asi
    que no sirven de banco completo.
    """
    import rclpy.serialization
    import rosbag2_py
    from coordinacion_msgs.msg import EstadoMision
    from nav_msgs.msg import Odometry

    escritor = rosbag2_py.SequentialWriter()
    escritor.open(
        rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
        rosbag2_py.ConverterOptions("", ""))
    for nombre, tipo in [("/coordinacion/estado_mision", "coordinacion_msgs/msg/EstadoMision"),
                         ("/robot1/odom", "nav_msgs/msg/Odometry"),
                         ("/robot2/odom", "nav_msgs/msg/Odometry")]:
        escritor.create_topic(rosbag2_py.TopicMetadata(
            name=nombre, type=tipo, serialization_format="cdr"))

    def estado(t, etapa, robot):
        m = EstadoMision()
        m.mision_id, m.etapa, m.robot_activo = "S24_B_prueba", etapa, robot
        # Los dos ids que ros2 bag no podria sacar del goal. Han de ser puntos
        # REALES del catalogo: _solicitud les busca el nivel alli.
        m.origen_id, m.destino_id = "piso1_escalera", "piso2_escalera"
        escritor.write("/coordinacion/estado_mision",
                       rclpy.serialization.serialize_message(m), int(t * 1e9))

    def odom(topico, t, vx):
        m = Odometry()
        m.twist.twist.linear.x = vx
        escritor.write(topico, rclpy.serialization.serialize_message(m),
                       int(t * 1e9))

    estado(10.0, INACTIVA, "")
    estado(10.2, TRAMO_1, "robot1")
    for i in range(6):
        odom("/robot1/odom", 10.3 + i * 0.1, 0.0 if i < 6 - 3 else 0.3)
    estado(40.0, TRANSFERENCIA, "robot1")
    estado(41.0, TRAMO_2, "robot2")
    for i in range(3):
        odom("/robot2/odom", 41.5 + i * 0.1, 0.3)
    estado(95.0, COMPLETADA, "robot2")
    del escritor


def pruebas_de_bag(esquema):
    import shutil
    import tempfile
    from componer_registro import componer, leer_bag

    tmp = tempfile.mkdtemp(prefix="prueba_rf25_")
    try:
        ruta = os.path.join(tmp, "bag_b")
        bag_sintetico(ruta)

        topicos = leer_bag(ruta)
        check("el bag sintetico trae estado_mision",
              len(topicos.get("/coordinacion/estado_mision", [])) == 5)

        reg = componer(ruta, banco="simulacion", campana="prueba",
                       error_posicion_m=0.19, rtf=0.995)
        check("el registro compuesto valida contra el esquema",
              valida(reg, esquema))
        check("saca la condicion B del propio bag",
              reg["mision"]["condicion"] == "B")
        check("t_inicio_tramo2 sale del odom del segundo robot",
              abs(reg["marcas"]["t_inicio_tramo2"] - 41.5) < 1e-6,
              f"-> {reg['marcas']['t_inicio_tramo2']}")
        check("el mision_id sale del bag, no del nombre del directorio",
              reg["mision"]["mision_id"] == "S24_B_prueba")
        check("origen y destino salen de EstadoMision, que el goal no graba",
              reg["solicitud"]["origen_id"] == "piso1_escalera"
              and reg["solicitud"]["nivel_destino"] == 2)

        # §4.2: el compositor falla ruidosamente, nunca inventa. Un bag ilegible
        # y una mision sin eventos NO pueden verse igual.
        vacio = os.path.join(tmp, "no_es_un_bag")
        os.makedirs(vacio)
        try:
            leer_bag(vacio)
            ok = False
        except Exception:
            ok = True
        check("un bag ilegible levanta excepcion en vez de devolver vacio", ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

y llamarla desde `main()`.

- [ ] **Paso 2: correrla y ver que falla**

```bash
source /opt/ros/humble/setup.bash && source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/prueba_componer_registro.py
```

Esperado: `ImportError: cannot import name 'componer'`.

> A partir de aquí la prueba **necesita ROS sourceado**, porque `rosbag2_py` y `coordinacion_msgs`
> viven ahí. Las de las tareas 3 y 4 siguen corriendo sin él; eso es a propósito y conviene que siga
> siendo así.

- [ ] **Paso 3: escribir el lector y el ensamblador**

Añadir a `componer_registro.py`:

```python
def leer_bag(ruta):
    """{topico: [(t_segundos, mensaje), ...]} de todo el bag.

    Levanta excepcion si el bag no se puede abrir. No devuelve un diccionario
    vacio: un bag ilegible y una mision sin eventos se verian igual, y §4.2 dice
    que el compositor falla ruidosamente antes que inventar.
    """
    import rclpy.serialization
    import rosbag2_py
    from rosidl_runtime_py.utilities import get_message

    lector = rosbag2_py.SequentialReader()
    lector.open(rosbag2_py.StorageOptions(uri=ruta, storage_id="sqlite3"),
                rosbag2_py.ConverterOptions("", ""))
    tipos = {t.name: t.type for t in lector.get_all_topics_and_types()}

    salida = {}
    while lector.has_next():
        topico, datos, t_ns = lector.read_next()
        msg = rclpy.serialization.deserialize_message(
            datos, get_message(tipos[topico]))
        salida.setdefault(topico, []).append((t_ns * 1e-9, msg))
    return salida


def componer(ruta_bag, banco, campana, error_posicion_m=None, rtf=None,
             semilla=None, es_piloto=False, medido_por="automatico"):
    """Construye el registro completo. Ver la §3 del esquema."""
    topicos = leer_bag(ruta_bag)

    crudos = topicos.get("/coordinacion/estado_mision", [])
    if not crudos:
        raise SystemExit(
            f"{ruta_bag} no contiene /coordinacion/estado_mision. Sin el no hay "
            f"marcas, y un registro con marcas en null seria indistinguible de "
            f"una mision que fallo. Grabar con herramientas/grabar_mision.sh.")

    ids = {m.mision_id for _, m in crudos if m.mision_id}
    if len(ids) > 1:
        raise SystemExit(
            f"{ruta_bag} contiene {len(ids)} misiones: {sorted(ids)}. El §6.4 del "
            f"protocolo manda un gzserver por corrida, asi que esto significa que "
            f"el procedimiento no se siguio.")

    if banco == "simulacion" and "/clock" not in topicos:
        raise SystemExit(f"{ruta_bag} no trae /clock y el banco es simulacion.")

    estados = [(t, m.etapa, m.robot_activo, m.mision_id) for t, m in crudos]
    etapas = {e for _, e, _, _ in estados}
    condicion = "B" if (TRANSFERENCIA in etapas or TRAMO_2 in etapas) else "A"

    movimientos = {}
    for topico, muestras in topicos.items():
        if topico.endswith("/odom"):
            ns = topico.strip("/").split("/")[0]
            movimientos[ns] = [(t, m.twist.twist.linear.x, m.twist.twist.linear.y)
                               for t, m in muestras]

    marcas = marcas_de(estados, movimientos, condicion)
    relevos = 1 if condicion == "B" and marcas["t_inicio_tramo2"] else 0
    veredicto = veredicto_de(marcas, estados, error_posicion_m, condicion, relevos)

    return {
        "esquema_version": ESQUEMA_VERSION,
        "mision": {
            "mision_id": ids.pop() if ids else os.path.basename(ruta_bag),
            "campana": campana, "banco": banco, "condicion": condicion,
            "semilla": semilla, "es_piloto": es_piloto,
        },
        "procedencia": _procedencia(ruta_bag),
        "solicitud": _solicitud(crudos, condicion),
        "marcas": marcas,
        "verdad_de_terreno": _verdad(banco, error_posicion_m, movimientos,
                                     medido_por),
        "veredicto": veredicto,
        "descriptivas": _descriptivas(banco, topicos, movimientos, marcas),
        "salud_del_banco": _salud(banco, rtf),
        "traza": _traza(ruta_bag, movimientos),
    }
```

Y los seis auxiliares. Ojo: `componer` les pasa `topicos` completo a los que necesitan más que
`/odom`, así que sus firmas son las de aquí.

```python
def _raiz():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(*args):
    import subprocess
    try:
        return subprocess.run(("git", "-C", _raiz()) + args, check=True,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def _procedencia(ruta_bag):
    """De donde salio esta medida. Sin esto no se puede reproducir en S26."""
    import hashlib
    cat = os.path.join(_raiz(), "Robot", "aws-deepracer", "deepracer_bringup",
                       "config", "puntos_interes.yaml")
    with open(cat, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    return {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "etiqueta": _git("describe", "--tags", "--exact-match"),
        # Una medida tomada con cambios sin comitear no se puede reproducir. Que
        # lo diga el registro es mejor que descubrirlo en S26.
        "repositorio_limpio": _git("status", "--porcelain") == "",
        "distro": os.environ.get("ROS_DISTRO", ""),
        "mundo": os.environ.get("TESIS_MUNDO", ""),
        "mapa": os.environ.get("TESIS_MAPA", ""),
        "catalogo_puntos": "puntos_interes.yaml",
        # Las poses del catalogo se movieron tres veces en agosto. Un registro
        # que no lo fije no se puede comparar con otro: 'ETM1' puede no ser el
        # mismo punto.
        "catalogo_sha256": sha,
        "bag": os.path.basename(os.path.normpath(ruta_bag)),
        "fecha_utc": _fecha_del_bag(ruta_bag),
    }


def _fecha_del_bag(ruta_bag):
    import datetime
    t = os.path.getmtime(ruta_bag)
    return datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%dT%H:%M:%SZ")


def _solicitud(crudos, condicion):
    """Que se pidio. Sale de EstadoMision, no del goal: los goals no se graban."""
    origen = next((m.origen_id for _, m in crudos if m.origen_id), "")
    destino = next((m.destino_id for _, m in crudos if m.destino_id), "")
    niveles = _niveles_del_catalogo()
    tramos = []
    vistos = set()
    for t, m in crudos:
        clave = (m.etapa, m.destino_actual.id)
        if m.etapa in (TRAMO_1, TRAMO_2) and clave not in vistos:
            vistos.add(clave)
            tramos.append({"orden": len(tramos) + 1, "robot": m.robot_activo,
                           "punto_id": m.destino_actual.id, "etapa": int(m.etapa)})
    return {
        "origen_id": origen, "destino_id": destino,
        "nivel_origen": niveles.get(origen), "nivel_destino": niveles.get(destino),
        # Derivable de los dos niveles, y se guarda igual: el analizador no debe
        # rederivar la variable independiente del experimento.
        "entre_niveles": condicion == "B",
        "tramos": tramos,
    }


def _niveles_del_catalogo():
    import yaml
    cat = os.path.join(_raiz(), "Robot", "aws-deepracer", "deepracer_bringup",
                       "config", "puntos_interes.yaml")
    with open(cat, encoding="utf-8") as f:
        return {p["id"]: int(p["nivel"]) for p in yaml.safe_load(f)["puntos"]}


def _verdad(banco, error_posicion_m, poses, medido_por):
    """De donde sale la verdad de terreno, que NO es la misma en los dos bancos.

    En simulacion /odom es la pose exacta del motor de Gazebo -WorldPose(), ver
    gazebo_ros_deepracer_drive.cpp:229-, asi que es un oraculo y la
    incertidumbre es cero. En el carro la unica odometria es rf2o, que el 26-ago
    registro el 5,7 % del desplazamiento real: rellenar pose_final con ella
    seria volver a llamar verdad de terreno a rf2o.
    """
    if banco == "fisico":
        return {"fuente": "cinta_metrica", "error_posicion_m": error_posicion_m,
                "pose_final": None, "incertidumbre_m": 0.01,
                "medido_por": medido_por, "nota": ""}
    ultima = None
    for muestras in poses.values():
        if muestras:
            t, x, y, yaw = muestras[-1]
            if ultima is None or t > ultima[0]:
                ultima = (t, x, y, yaw)
    return {
        "fuente": "gazebo_worldpose_via_odom",
        "error_posicion_m": error_posicion_m,
        "pose_final": None if ultima is None else
                      {"x": ultima[1], "y": ultima[2], "yaw": ultima[3]},
        "incertidumbre_m": 0.0, "medido_por": "automatico", "nota": "",
    }


def _descriptivas(banco, topicos, poses, marcas):
    """Se miden y se reportan; no deciden el exito. Ver §3.8 del esquema."""
    recorrido = 0.0
    desviacion = {}
    for ns, muestras in poses.items():
        for (_, x0, y0, _), (_, x1, y1, _) in zip(muestras, muestras[1:]):
            recorrido += math.hypot(x1 - x0, y1 - y0)
        # RNF-01: ningun robot cruza de nivel, lo que cruza es el mensaje.
        desviacion[ns] = max((abs(z) for z in _zetas(topicos, ns)), default=0.0)

    # R12: una cuspide es un cambio de sentido de la marcha. Se cuentan los
    # cambios de signo de cmd_vel.linear.x, ignorando el cero.
    cuspides = 0
    for topico, muestras in topicos.items():
        if topico.endswith("/cmd_vel"):
            signos = [_signo(m.linear.x) for _, m in muestras if _signo(m.linear.x)]
            cuspides += sum(1 for a, b in zip(signos, signos[1:]) if a != b)

    total = None
    if marcas["t_completada"] is not None and marcas["t_solicitud"] is not None:
        total = marcas["t_completada"] - marcas["t_solicitud"]

    return {
        "error_rumbo_rad": None,
        "desviacion_z_m": desviacion,
        "distancia_recorrida_m": recorrido,
        "num_cuspides": cuspides,
        "tiempo_total_s": total,
        # La cifra que el 26-ago delato a AMCL. Con /odom publicado desde
        # WorldPose(), map->odom deberia ser CONSTANTE; derivo 1,977 m. Grabarla
        # en cada mision hace que la campana cuantifique R3 en vez de padecerlo.
        # En fisico va null: alli map->odom no es un error medible contra nada.
        "deriva_map_odom_m": None if banco == "fisico"
                             else _deriva_map_odom(topicos),
    }


def _signo(v):
    return 0 if abs(v) < 1e-3 else (1 if v > 0 else -1)


def _zetas(topicos, ns):
    return [m.pose.pose.position.z for _, m in topicos.get(f"/{ns}/odom", [])]


def _deriva_map_odom(topicos):
    """Cuanto se movio la transformada map->odom entre el principio y el final."""
    puntos = []
    for _, msg in topicos.get("/tf", []):
        for tr in msg.transforms:
            if tr.header.frame_id.endswith("map") and tr.child_frame_id.endswith("odom"):
                puntos.append((tr.transform.translation.x, tr.transform.translation.y))
    if len(puntos) < 2:
        return None
    return math.hypot(puntos[-1][0] - puntos[0][0], puntos[-1][1] - puntos[0][1])


def _salud(banco, rtf):
    """Para que un descarte sea demostrable. La causa la pone una persona
    despues, y solo puede ser una de las cuatro del §8 del protocolo: el esquema
    rechaza cualquier otra."""
    if banco == "fisico":
        return {"rtf": None, "controladores_activos": {},
                "gzserver_vivo_al_final": None, "descartada": False,
                "causa_descarte": None}
    return {"rtf": rtf, "controladores_activos": {},
            "gzserver_vivo_al_final": True, "descartada": False,
            "causa_descarte": None}


def _traza(ruta_bag, poses, hz=5.0):
    """Copia de conveniencia para graficar sin reabrir el bag. El bag sigue
    siendo la fuente: el 26-ago la medicion de rf2o se obtuvo metiendole el
    /scan de mision3 a un nodo que nunca corrio en esa mision, y ninguna traza
    diezmada habria permitido eso."""
    paso = 1.0 / hz
    puntos = []
    for ns, muestras in poses.items():
        siguiente = None
        for t, x, y, yaw in muestras:
            if siguiente is None or t >= siguiente:
                puntos.append({"t": t, "robot": ns, "x": x, "y": y, "yaw": yaw})
                siguiente = (t if siguiente is None else siguiente) + paso
    puntos.sort(key=lambda p: p["t"])
    return {"bag": os.path.basename(os.path.normpath(ruta_bag)),
            "decimada_hz": hz, "puntos": puntos}
```

`componer` necesita entonces dos diccionarios distintos sacados de `/odom`: `movimientos` con
`(t, vx, vy)` para las marcas, y `poses` con `(t, x, y, yaw)` para la verdad de terreno y la traza.
Añadir dentro del mismo bucle:

```python
    poses = {}
    for topico, muestras in topicos.items():
        if topico.endswith("/odom"):
            ns = topico.strip("/").split("/")[0]
            movimientos[ns] = [(t, m.twist.twist.linear.x, m.twist.twist.linear.y)
                               for t, m in muestras]
            poses[ns] = [(t, m.pose.pose.position.x, m.pose.pose.position.y,
                          _yaw_de(m.pose.pose.orientation)) for t, m in muestras]


def _yaw_de(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))
```

y pasar `poses` a `_verdad`, `_descriptivas` y `_traza` tal como aparece arriba.

> **`error_rumbo_rad` sale `None` a propósito.** Para calcularlo hace falta el `yaw` del punto del
> catálogo, que sí está en `puntos_interes.yaml`, pero el §3.7 del esquema dice que el rumbo **no
> decide** y R12 sigue abierto. Se deja el campo presente y sin llenar en `1.0.0`; llenarlo después
> es una versión menor (`1.1.0`) y los registros viejos siguen valiendo.

Y el punto de entrada:

```python
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bag")
    p.add_argument("--banco", choices=["simulacion", "fisico"], required=True)
    p.add_argument("--campana", required=True)
    p.add_argument("--error-posicion-m", type=float, default=None,
                   help="En fisico, la lectura de cinta. Sin el, el registro "
                        "queda pendiente de medir (§4.4) y el analizador lo "
                        "rechaza hasta que se rellene.")
    p.add_argument("--rtf", type=float, default=None)
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--piloto", action="store_true")
    p.add_argument("--medido-por", default="automatico")
    p.add_argument("--salida", required=True)
    a = p.parse_args()

    registro = componer(a.bag, a.banco, a.campana, a.error_posicion_m, a.rtf,
                        a.semilla, a.piloto, a.medido_por)

    # Validar ANTES de escribir. Sin esto, 'congelado' es una promesa.
    import jsonschema
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(raiz, "Documentos",
                           "esquema_registro_mision.json"), encoding="utf-8") as f:
        jsonschema.validate(registro, json.load(f))

    os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
    with open(a.salida, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=2, ensure_ascii=False)
    print(f"Registro escrito en {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Paso 4: correrla y ver que pasa**

```bash
source /opt/ros/humble/setup.bash && source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/prueba_componer_registro.py
```

Esperado: todas en `[OK ]`, `0 fallo(s)`, salida `0`.

Si «el registro compuesto valida contra el esquema» falla, el mensaje de `jsonschema` dice la ruta
del campo. Lo normal es que un auxiliar devuelva `0` donde el esquema pide `null` o al revés: **la
diferencia importa**, porque `0.0` de deriva es una medida y `null` es «aquí no se mide».

- [ ] **Paso 5: commit**

```bash
git add herramientas/componer_registro.py herramientas/prueba_componer_registro.py
git commit -m "componer_registro: lectura de bag, ensamblado del registro y validacion contra el esquema"
```

---

## Tarea 6: la comprobación de integración, una sola vez

**Archivos:**
- Ninguno. Es una comprobación manual, y el resultado va a `ESTADO.md`.

**Interfaces:**
- Consume: el bag de la corrida del jueves y `componer_registro.py` completo.
- Produce: un registro real revisado a mano, y la confirmación de que RF-25 está verificado.

- [ ] **Paso 1: componer el registro del bag real**

```bash
source /opt/ros/humble/setup.bash && source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/componer_registro.py ~/tesis_evidencia/S20_piloto_01 --banco simulacion --campana piloto --piloto --rtf 0.99 --salida ~/tesis_evidencia/S20_piloto_01.json
```

Esperado: `Registro escrito en ...`.

- [ ] **Paso 2: revisarlo campo por campo contra lo que se vio**

```bash
python3 -m json.tool ~/tesis_evidencia/S20_piloto_01.json | head -60
```

Contrastar a mano, y **no dar por bueno lo que no se pueda contrastar**:

| Campo | Contra qué se contrasta |
|---|---|
| `mision.condicion` | ¿se pidió una misión inter-nivel? Debe decir `"B"` |
| `marcas.t_completada − t_solicitud` | el `tiempo_total_s` que imprimió el coordinador al terminar |
| `marcas.t_inicio_tramo2 − t_fin_tramo1` | el hueco de relevo que se vio en la HRI |
| `verdad_de_terreno.error_posicion_m` | la distancia que reportó `_distancia` al llegar |
| `descriptivas.num_cuspides` | el registro del 21-ago, que es la comparación pendiente de **R12** |
| `descriptivas.deriva_map_odom_m` | debería parecerse a los 1,977 m del 26-ago si **R3** sigue igual |
| `salud_del_banco.controladores_activos` | `ros2 control list_controllers`, que debe dar 7/7 |

- [ ] **Paso 3: anotar el resultado**

En `ESTADO.md`, entrada de bitácora con la fecha, el `mision_id` compuesto y **qué campo no cuadró,
si alguno**. Marcar RF-25 en `REQUISITOS.md` como 🟡 verificado en simulación (no ✅: el banco físico
no se ha probado hasta la corrida del viernes).

Si esta comprobación pasa, **la prueba unitaria es la que protege de aquí en adelante** y no hay que
volver a revisar registros a mano.

- [ ] **Paso 4: comprobar el repositorio y comitear**

```bash
bash herramientas/verificar_repositorio.sh
```

Esperado: **12 de 12**. Si falla «ningún documento ni configuración queda sin citar», hay que citar
`esquema_registro_mision.json` desde `ESQUEMA_REGISTRO_MISION.md` §2.4 y `PLAN_RF25.md` desde
`ESTADO.md`.

```bash
git add ESTADO.md Documentos/REQUISITOS.md
git commit -m "RF-25 verificado en simulacion: primer registro compuesto desde bag real"
```

---

## Lo que este plan deja fuera a propósito

1. **`herramientas/sortear_misiones.py`** (§6.3 del protocolo). Produce `campana` y `semilla`, que
   aquí entran por la línea de órdenes. Hace falta antes de S24, no antes del viernes.
2. **El analizador de campaña** (§9.6). Lee los N registros y saca las cuatro métricas con sus
   intervalos. Este plan define su entrada.
3. **La segunda pasada que rellena la medida de cinta** (§4.4 del esquema). Hasta que la corrida
   física no exista, `--error-posicion-m` por línea de órdenes basta.
4. **El origen del sistema de coordenadas en el edificio real** (§8.1 del esquema). Es trabajo del
   frente B.

---

## Trazabilidad

| Tarea | Implementa |
|---|---|
| 1 | §2.1 del esquema · §3 y §3.2 del protocolo · RF-21, RF-22 |
| 2 | §2.2 del esquema · §6.4 del protocolo |
| 3 | §2.4, §3.9 y §4.3 del esquema · §8 del protocolo (lista cerrada) |
| 4 | §3.5 y §3.7 del esquema · §3.3 del protocolo |
| 5 | §2.3, §3.3, §3.6, §3.8, §3.10 y §4.2 del esquema |
| 6 | §5 del esquema — la comprobación de integración |

Requisito que satisface: **RF-25**, y con él **RF-21** a **RF-24**, que son las cuatro métricas de
**OE4**.
