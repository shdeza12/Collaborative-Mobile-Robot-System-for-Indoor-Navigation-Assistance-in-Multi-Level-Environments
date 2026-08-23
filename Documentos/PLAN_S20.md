# Plan de la semana 20 — del lunes 24 al domingo 30 de agosto de 2026

Se escribe el 2026-08-22, el sábado anterior, y no el lunes por la mañana. La diferencia importa:
[`PLAN_S19.md`](PLAN_S19.md) nació el miércoles por la noche, después de que dos días se fueran sin
plan, y su propia §1 tuvo que dedicar un párrafo a explicar por qué el miércoles se desvió. Con el
plan escrito antes, esa conversación no hace falta.

Manda el [cronograma S17–S32](CRONOGRAMA_S17_S32.md) §S20. Este documento **no lo reinterpreta**:
reordena la semana dentro de él y añade dos tareas que el cronograma no nombra, porque son
prerrequisito de lo que sí nombra. El motivo de cada una está escrito en §2.

---

## 1. Dónde estamos al empezar

El cronograma fija para S20 este criterio de cierre:

> *«Una solicitud origen–destino produce la asignación del agente correcto y deja registrados los dos
> tiempos en un log estructurado. El mapa real del laboratorio queda guardado y verificado con
> `herramientas/verificar_mapa.py`.»*

Y S20 hereda de S19 un **arrastre declarado**: los dos agentes navegando simultáneamente, cada uno
en su nivel (**H3**).

| Lo que ya está | Lo que no |
|---|---|
| [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md): las cuatro métricas definidas antes de instrumentar | `coordinacion_msgs` **no existe**; `Robot/aws-deepracer/` no tiene el paquete |
| [`REQUISITOS.md`](REQUISITOS.md): 34 requisitos con OE y prueba | El nodo de coordinación no existe |
| 15 destinos del piso 1, con holgura verificada | El piso 2 no tiene mapa **ni un solo destino** |
| Navegación punto a punto validada en los dos niveles | H3: los dos a la vez, sin hacer |
| El LiDAR del kit mide y publica (RPLIDAR A1M8-R5) | El lanzador pide `rplidar_node` y el ejecutable se llama `rplidar_composition` |

**Faltan 12 semanas de 32, y la congelación de código es del 14 al 20 de septiembre: cuatro
semanas.** En ellas caben `coordinacion_msgs`, el coordinador, la máquina de estados del relevo, la
HRI web, el registrador, el analizador de campaña, el piso 2 completo y el despliegue físico. Esa
aritmética es la que ordena esta semana.

---

## 2. Por qué la semana va en este orden

Tres razones, y las tres son de dependencia, no de preferencia.

### 2.1 El piso 2 bloquea el propio criterio de cierre de S20

El criterio pide que una solicitud produzca *«la asignación del **agente correcto**»*. Asignar por
nivel solo se puede **probar** si existe algo a lo que mandar al agente del nivel 2, y hoy
`puntos_interes.yaml` tiene 15 destinos, los 15 en `nivel: 1`. Con un solo nivel poblado, la lógica
de asignación no se ejercita: acierta siempre porque no hay otra opción.

Además hay **un solo** punto de transferencia en todo el sistema, `piso1_escalera`. El relevo del
contrato §4 necesita uno **en cada nivel**, así que sin el del piso 2 no hay relevo, no hay etapa
`TRANSFERENCIA` y no hay **RF-24**, que es la variable de respuesta principal del proyecto.

**Y lo que bloquea el piso 2 no son los nombres de las salas.** Están aparcados a la espera de
confirmarlos, y eso sigue en pie, pero los nombres solo hacen falta para la *variedad de destinos*
de la condición B de la campaña, en S24. Lo que la ruta crítica necesita ahora es geométrico:

| Cosa | ¿Necesita los nombres? | ¿Cuándo se necesita? |
|---|---|---|
| El **mapa** del piso 2 | No. Depende del corte oeste (A/B/C, final de [`mapa_destinos.txt`](mapa_destinos.txt)) | Ya: sin él `robot2` no localiza |
| El **punto de transferencia** | No. Es una pose | Ya: sin él no hay relevo |
| Los otros 17 destinos | Sí | S24 |

### 2.2 `coordinacion_msgs` tiene que compilar en las dos distribuciones el día que se escribe

**R8** está caracterizado: `nav2_msgs/NavigateToPose` cambia de definición entre Humble y Jazzy, y
lo que el contrato garantiza es que el **mismo código fuente** sirve para los dos destinos, no que
un coordinador pueda servirlos a la vez. Esa garantía deja de valer en cuanto alguien escriba el
paquete y lo pruebe solo en Humble.

Si el desajuste aparece en S22, cuando toca desplegar sobre los vehículos, cae **dentro de la
congelación de código de S23**. Compilarlo en la tarjeta Jazzy del carro cuesta minutos esta
semana y una renegociación del cronograma dentro de tres.

### 2.3 El esquema del registro se congela antes de la primera métrica

S26 es *«análisis comparativo simulación contra físico sobre la misma geometría»*. Eso existe solo
si las 30 corridas simuladas (S24) y las 5–10 físicas (S25) producen registros **con el mismo
esquema**, y no son la misma condición experimental: en simulación la verdad de terreno es `/odom`
y hay RTF; en hardware la verdad es medición externa y no hay RTF.

Si el registrador se va escribiendo métrica a métrica según haga falta, en S26 hay dos conjuntos de
datos que no se cruzan y **no queda semana para repetir ninguna campaña**. El esquema tiene que
prever los campos de hardware aunque en simulación vayan vacíos.

---

## 3. Día a día

### Lunes 24 — desbloquear el piso 2 · *frente A*

> **Los puntos 1 a 3 se adelantaron el domingo 23-ago.** Se dejan escritos porque el criterio de
> cierre del día era suyo y conviene poder comprobarlo, no para volver a hacerlos.

1. ✅ **Corte oeste: opción A**, a ras en x = −23,39. No modifica ni un byte del `.world`: solo
   declara hasta dónde llega el mapa.
2. ✅ **`mundo_definitivo_piso2` generado.** Hicieron falta **cinco `--region`**, no uno: el piso 2
   es una S —ala oeste, tramo norte-sur, pasillo largo y ramal sur al este— y un solo rectángulo
   deja que el relleno se escape por los vanos de ~0,9 m, que es lo que dio el 95,1 % libre del
   21-ago. La receta queda escrita dentro del `.yaml`, como en el piso 1.
3. ✅ **Verificado** contra `mundo_definitivo_piso2.world` —cada piso tiene ya **su propio mundo**,
   partido el 23-ago por el cruce de LiDAR entre pasillos—: `ACEPTADO`, 0 de 6096 obstáculos sin
   pared real y 0,1 % de celdas desconocidas dentro de sus regiones.
4. **Punto de transferencia del piso 2** en `puntos_interes.yaml`, con `es_transferencia: true` y
   marcado **`provisional: true`** mientras no se confirme cuál es el hueco de la escalera. **Es lo
   único del lunes que queda**, y es lo único del piso 2 que está en la ruta crítica.

> **Provisional no contamina la campaña, y hay que dejarlo escrito.** Sirve para construir e
> integrar el relevo, que es lo que ocupa S20–S23. La campaña de S24 exige la pose real: si se
> midiera sobre una inventada, los números describirían una geometría que no es la del edificio.
> Es el mismo papel que juegan las cinco corridas piloto del §7 del protocolo, cuyos datos se
> excluyen a propósito.

**Criterio de cierre del día:** `herramientas/verificar_pose_spawn.py` deja de imprimir `[ -- ]`
para `robot2`, y `robot2` arranca con Nav2 localizando contra **su** mapa. La primera mitad está
cumplida desde el 23-ago —`robot2: (-21.889, -8.379) libre, holgura 1.50 m`—; la segunda pide
lanzarlo, y se comprueba el lunes.

### Martes 25 — H3 y el `/odom` cruzado · *frente A*

1. **Los dos agentes navegando a la vez**, cada uno en su nivel. Es el arrastre de S19 y ahora sí
   tiene con qué: `robot2` ya tiene mapa y un destino.
2. **Reproducir y cerrar el `/odom` cruzado** en la misma corrida. No es una tarea aparte: dos
   robots corriendo simultáneamente **es** la condición en que apareció la lectura que devolvió la
   posición del otro agente. Es el primer prerrequisito del §10 del protocolo porque las cuatro
   métricas salen de odometría; instrumentar encima produce números que hay que tirar.

**Criterio de cierre del día:** H3 cerrado con evidencia de los dos robots contrastada contra
`/odom` —no contra `SUCCEEDED`, regla del 12-ago— y el cruce de `/odom` reproducido y explicado, o
declarado no reproducible con el número de intentos escrito.

### Miércoles 26 — las dos decisiones que condicionan todo lo que se mida · *frente A*

1. **`coordinacion_msgs`** con las cuatro definiciones del
   [contrato §5](CONTRATO_INTERFACES.md). Compilarlo en Humble **y en la tarjeta Jazzy del carro el
   mismo día** (§2.2). Nada más: solo los mensajes.
2. **Congelar el esquema del registro de misión** (RF-25), con los campos de hardware previstos
   (§2.3). Un archivo por misión, procesable sin intervención manual.
3. **Aplicar `stateful: False`** y repetir los tres destinos del 21-ago **comparando el número de
   cúspides** contra aquel registro. Sin esa comparación el cambio es una creencia, no un arreglo
   — por eso no se tocó el 22-ago al decidirlo. Va esta semana y no en S24 para que las cuatro
   semanas de integración no corran contra un verificador de meta que aborta llegadas buenas de
   forma intermitente, y para que la campaña no estrene una configuración que nadie usó.

**Criterio de cierre del día:** el paquete compila en las dos distribuciones, el esquema está
versionado, y **R12** pasa a mitigado con la comparación de cúspides escrita.

### Jueves 27 — el nodo de coordinación · *frente A*

Lo que pide el cronograma: registro de agentes, recepción de la solicitud y **asignación por
nivel**, con el tiempo de respuesta y el tiempo de asignación instrumentados desde el inicio.

Dos cosas que el protocolo ya fijó y que hay que respetar aquí, no después:

- **`use_sim_time: true`** en el nodo. Todas las marcas salen de `/clock` (§3 del protocolo). Un
  coordinador con reloj de pared produce métricas silenciosamente sesgadas.
- **La marca extraordinaria de cambio de etapa.** `estado_mision` va a 1 Hz y eso es demasiado
  grueso para `t_asignacion` (§3.2). Hay que emitirla en el instante del cambio, no esperar al
  siguiente tick.

**Criterio de cierre del día — es el del cronograma:** una solicitud origen–destino produce la
asignación del agente correcto y deja los dos tiempos en un log estructurado. Se prueba **con
destino en el nivel 2**, que es lo que hace que la asignación signifique algo.

### Viernes 28 — frente B y corte semanal

**Frente B, por la mañana:** mapear el laboratorio real con el DeepRacer físico. Antes hay que
resolver el nombre del lanzador —enlace `rplidar_node` → `rplidar_composition`, o editar el
lanzador bajo `/opt/aws/deepracer/`—, que es el único defecto vivo de los tres que el spike del
19-ago culpaba. **Criterio:** el mapa guardado y verificado con `herramientas/verificar_mapa.py`.

**Corte semanal, por la noche** (regla del 18-ago):

- Actualizar [`ESTADO.md`](../ESTADO.md): OE1 y OE4, H3, R12, R8 y la bitácora.
- **Emitir el entregable de S19** — lo pide la columna T del cronograma y el último emitido es el
  de S18.
- `herramientas/verificar_repositorio.sh` en verde antes del commit.
- Commit y push. **Avisar a Jonny**: la rama es compartida.

---

## 4. Lo que este plan no resuelve

**Es más trabajo del que cabe, y conviene saber qué se cae primero.** El orden de sacrificio es:
frente B del viernes, luego el nodo de coordinación del jueves. Lo de lunes a miércoles **no se
sacrifica**: son prerrequisitos de todo lo demás, y aplazarlos no ahorra tiempo, lo mueve a una
semana donde ya no cabe.

**Una contradicción escrita que no puedo cerrar yo.** Dos documentos del proyecto dicen cosas
distintas sobre dónde corre la campaña física:

| Documento | Qué dice |
|---|---|
| [`ESTADO.md`](../ESTADO.md) §4.3 | las corridas físicas ocurren en **un único piso**, *«porque no hay forma de subir un DeepRacer por una escalera»* |
| [`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md) D3 y §S25 | la etapa que produce la evidencia es *«el pasillo real de la USTA **en dos plantas**, cuyo acceso está confirmado»* |

Si la campaña física es de un piso, **RF-24 no tiene ni una medida física** y el aporte del
proyecto descansa entero en simulación. Eso es defendible declarándolo desde ahora e indefendible
si aparece el 28 de septiembre. Hay motivo para sospechar que la frase de `ESTADO.md` está caducada
por su propio argumento: **D2** dice que ningún robot cruza de nivel, así que nadie necesita que el
vehículo suba la escalera — `robot2` lo sube una persona. Pero es una decisión de acceso al
edificio, y la toman Santiago y Jonny, no este plan.

**OE3 sigue en 0 % y sin semana propia.** Aparece en S22 dentro de *«interfaz HRI e integración»*,
compartiendo semana con la integración de extremo a extremo. Se registró en `PLAN_S19.md` §4 y no
ha cambiado.

**R11 sigue sin declaración escrita** de qué vehículo está intervenido, qué se le hizo y cuándo
vuelve. Bloquea la paridad entre vehículos y la campaña física con dos robots. Y hay una
consecuencia que el spike del 18-ago dejó demostrada y conviene no olvidar: el respaldo natural
—un robot real y uno simulado— **no funciona**, porque `NavigateToPose` difiere entre las dos
distribuciones. Si R11 no se cierra, la campaña física con dos vehículos no tiene plan B.
