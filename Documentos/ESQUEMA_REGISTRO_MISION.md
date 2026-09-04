# Esquema del registro de misión (RF-25)

> **Congelado el 2026-08-26**, versión `1.0.0`. Este documento define qué se guarda de cada misión
> y por qué. Es el artefacto que el §9.4 de
> [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) llama *«registrador de misión»* y que la
> §2.3 de [`PLAN_S20.md`](PLAN_S20.md) exigía congelar **antes** de tomar la primera métrica.
>
> Cambiar un campo después de la campaña de S24 invalida la comparación de S26. Cómo se cambia sin
> romperla está en la §7.
>
> El orden en que se construye, con sus plazos y su criterio de aborto, está en
> [`PLAN_RF25.md`](PLAN_RF25.md).

---

## 1. Por qué se congela ahora y no cuando haga falta

S26 es *«análisis comparativo simulación contra físico sobre la misma geometría»*. Eso existe solo
si las 30 corridas simuladas de S24 y las 5–10 físicas de S25 producen registros **con el mismo
esquema**. Y no son la misma condición experimental: en simulación hay RTF y en hardware no; en
simulación la verdad de terreno es una cosa y en hardware es otra.

Si el registrador se escribe métrica a métrica según haga falta, en S26 hay dos conjuntos de datos
que no se cruzan y **no queda semana para repetir ninguna campaña**.

**Y hay una razón para congelarlo hoy y no ayer.** El 2026-08-26 se midió que en simulación `/odom`
no es una estimación sino la pose exacta del motor de Gazebo —`model_->WorldPose()`,
`gazebo_ros_deepracer_drive.cpp:229`—, mientras que en el vehículo físico la única odometría es
`rf2o_laser_odometry`, que en el pasillo simulado registra el 5,7 % del desplazamiento real. Un
esquema congelado el día antes habría llamado a ese campo `error_contra_odom`, y ese nombre **es
falso en el banco físico**. Por eso el bloque se llama `verdad_de_terreno` y lleva su `fuente`
explícita. Ver la bitácora del 26-ago en [`ESTADO.md`](../ESTADO.md) §7 y **R3**.

---

## 2. Arquitectura: cuatro piezas

La decisión de fondo es que **el registro no se escribe durante la misión, se compone después a
partir del bag**. Las alternativas consideradas y por qué se descartaron están en la §6.

```
simulación:  Gazebo + Nav2 + coordinador ─► tópicos ─► bag ─► componer_registro.py ─► JSON
físico:      carro   + Nav2 + coordinador ─► tópicos ─► bag ─► componer_registro.py ─► JSON
                                                                        ▲
                                                            medida de cinta (a mano)
```

El compositor **no sabe de dónde salió el bag**: lee tópicos. Eso es lo que hace posible S26.

### 2.1 `coordinacion/coordinador.py` — cuatro cambios acotados

| Qué | Por qué |
|---|---|
| `time.time()` → `self.get_clock().now()` en las líneas 160, 175, 182, 200 y 210 | §3 del protocolo: *«todas las marcas temporales salen del mismo reloj: `/clock` del simulador»*. `time.time()` ignora `use_sim_time`; el mismo archivo ya usa `get_clock()` en las líneas 149 y 317, así que hoy conviven las dos formas. Con RNF-06 pidiendo RTF ≥ 0,99, las dos difieren hasta un 1 %: sobre `t_respuesta` eso no es ruido, es sesgo sistemático |
| **Marca extraordinaria**: llamar a `_publicar_estado()` justo después de cada `_marcar()`, sin quitar el temporizador de 1 Hz de la línea 91 | §3.2: *«`estado_mision` se publica a 1 Hz, así que esta métrica tiene una resolución de 1 s y eso es demasiado grosero para un evento que se espera en milisegundos»*. La HRI conserva su latido; la métrica gana resolución |
| **`mision_id` propio**, generado al aceptar el goal | Hoy se publica `pet.origen_id` (líneas 172, 186, 194, 205), o sea el ID del punto de origen. Dos misiones que salgan de ETM1 llevan el mismo identificador, y con N = 30 y pares sorteados eso hace imposible saber qué registro es de qué corrida |
| **`origen_id` y `destino_id` en `EstadoMision`** | Los dos existen hoy solo en el goal de `GuiarUsuario.action`, y un goal de acción viaja por un servicio: **`ros2 bag` no graba servicios**. `destino_actual` no sirve de sustituto, porque en el tramo 1 de una misión inter-nivel es el punto de transferencia y no el destino. Sin estos dos campos, el bloque `solicitud` de la §3.4 no se puede componer desde el bag |

Formato del identificador: `<prefijo>_<condicion>_<fecha>_<hhmmss>`, p. ej.
`S24_B_20260827_143052`. Para corridas sueltas fuera de campaña, `manual_<fecha>_<hhmmss>`.

> **Marca de tiempo y no un consecutivo.** La §6.4 del protocolo manda un `gzserver` nuevo por
> corrida, así que un contador en memoria se reiniciaría en cada una y las treinta misiones de S24
> se llamarían todas `001`. El prefijo lo pone quien lanza la campaña, y es un parámetro distinto
> del campo `campana` del registro, que lo pone el compositor.

### 2.2 `herramientas/grabar_mision.sh` — un bag por misión, lista de tópicos fija

Lista mínima obligatoria:

```
/clock
/coordinacion/estado_mision
/<ns>/odom          (de cada robot registrado)
/<ns>/amcl_pose
/<ns>/scan
/<ns>/cmd_vel
/<ns>/plan
/tf  /tf_static
```

**La lista es fija a propósito.** Si cada corrida graba lo que le parece, el conjunto de datos no es
homogéneo y S26 no compara. Y no es una precaución teórica: los bags del 26-ago
(`~/tesis_evidencia/S20_localizacion/mision1..3`) **no contienen `/clock` ni
`/coordinacion/estado_mision`**, que son justo los dos tópicos de los que salen las marcas
temporales. Sirven para analizar trayectoria y localización —de hecho de ahí salió toda la medición
de rf2o— pero no para componer un registro.

**Un bag por misión**, no uno por sesión. Lo autoriza §6.4: cada corrida arranca con un `gzserver`
nuevo, así que la frontera entre misiones ya es una frontera entre procesos.

### 2.3 `herramientas/componer_registro.py` — bag → JSON

Lee el bag después de la corrida y produce un archivo por misión. **No corre durante la misión**,
que es lo que impide que la instrumentación sesgue lo instrumentado: RNF-06 exige RTF ≥ 0,99 y un
registrador serializando a 50 Hz compite por la CPU con dos Gazebo en el mismo equipo.

### 2.4 `Documentos/esquema_registro_mision.json` — el esquema en JSON Schema

Esta pieza es la que hace que «congelado» signifique algo. Sin un artefacto verificable, congelar es
una promesa. El compositor **valida antes de escribir** y falla si no cuadra.

---

## 3. El esquema, campo por campo

Nueve bloques.

```json
{
  "esquema_version": "1.0.0",
  "mision":            { ... },
  "procedencia":       { ... },
  "solicitud":         { ... },
  "marcas":            { ... },
  "verdad_de_terreno": { ... },
  "veredicto":         { ... },
  "descriptivas":      { ... },
  "salud_del_banco":   { ... },
  "traza":             { ... }
}
```

### 3.1 `esquema_version`

Cadena semver. El analizador de campaña **rechaza mezclar versiones mayores distintas**. Si se añade
un campo, sube la menor y los registros viejos siguen valiendo; si cambia el *significado* de un
campo, sube la mayor y esos datos se reportan aparte o se repiten. Ver §7.

### 3.2 `mision`

| Campo | Tipo | Notas |
|---|---|---|
| `mision_id` | string | único; formato de §2.1 |
| `campana` | string | `"S24_simulacion"`, `"S25_fisico"`, `"piloto"` |
| `banco` | enum | `"simulacion"` \| `"fisico"` |
| `condicion` | enum | `"A"` (intra-nivel) \| `"B"` (inter-nivel), §6.2 |
| `semilla` | int \| null | la de `sortear_misiones.py`; `null` fuera de campaña |
| `es_piloto` | bool | |

> `es_piloto` va como booleano y **no se deduce del nombre de la campaña**. §7 del protocolo excluye
> a propósito los datos del pilotaje, y una exclusión que depende de leer bien una cadena de texto
> se equivoca alguna vez.

### 3.3 `procedencia`

`commit` · `etiqueta` · `repositorio_limpio` (bool) · `distro` (`"humble"` \| `"jazzy"`) · `mundo` ·
`mapa` · `catalogo_puntos` · `catalogo_sha256` · `bag` · `fecha_utc`

> **`repositorio_limpio`**: una medida tomada con cambios sin comitear no se puede reproducir. Que
> lo diga el registro es mejor que descubrirlo en S26.
>
> **`catalogo_sha256`**: las poses de `puntos_interes.yaml` se movieron tres veces en agosto (24-ago
> al añadir el piso 2, y dos veces el 26-ago al escribir los dieciséis destinos y al redimensionar
> los paneles). Un registro que no fije el catálogo no se puede comparar con otro, porque «ETM1»
> puede no ser el mismo punto.

### 3.4 `solicitud`

`origen_id` · `destino_id` · `nivel_origen` · `nivel_destino` · `entre_niveles` (bool) ·
`tramos[]` de `{orden, robot, punto_id, etapa}`

`entre_niveles` es derivable de los dos niveles y se guarda igual: el analizador no debe rederivar
la variable independiente del experimento.

> `origen_id` y `destino_id` salen de `EstadoMision`, no del goal de la acción. Ver la §2.1: los
> goals viajan por un servicio y `ros2 bag` no graba servicios.

### 3.5 `marcas` — todas en segundos, del mismo reloj

`reloj` (`"/clock"` \| `"pared"`) · `t_solicitud` · `t_robot_activo` · `t_primer_movimiento` ·
`t_fin_tramo1` · `t_inicio_tramo2` · `t_completada`

Definiciones operativas, literales del §3 del protocolo:

- **`t_solicitud`** — instante en que el servidor de `/coordinacion/guiar_usuario` **acepta** el
  goal. No cuando la HRI lo envía: la latencia del navegador no es del sistema robótico. Su
  observable en el bag es el primer `estado_mision` con `etapa = RECIBIDA`, que el coordinador
  publica antes de planificar y con `robot_activo` vacío. **Hasta el 2026-08-29 ese mensaje no se
  emitía**, y la marca caía sobre el `TRAMO_1`, es decir, sobre el mismo mensaje que
  `t_robot_activo`: el tiempo de asignación valía cero por construcción. Los bags anteriores a esa
  fecha se siguen componiendo, pero su tiempo de asignación **no es una medida**.
- **`t_primer_movimiento`** — primera muestra de `/<ns>/odom` del robot asignado con
  `|v| ≥ 0,02 m/s` **y las dos siguientes también**.
- **`t_robot_activo`** — primer `estado_mision` con `etapa = TRAMO_1` y `robot_activo` no vacío.
- **`t_fin_tramo1`** — primer `estado_mision` con `etapa = TRANSFERENCIA`. Es decir, lo marca el
  coordinador cuando da por alcanzado el punto de transferencia, no un umbral geométrico calculado
  aparte: si el coordinador y el analizador discreparan, el hueco de relevo mediría otra cosa.
- **`t_inicio_tramo2`** — primer movimiento del robot del segundo nivel, criterio de `t_primer_movimiento`.
- **`t_completada`** — primer `estado_mision` con `etapa = COMPLETADA`. Si la misión termina en
  `FALLIDA`, va `null` y el instante del fallo queda en la traza y en `motivo_fallo`.

**Una marca va `null` cuando el evento no ocurrió**, sea porque la condición no lo contempla
(condición A no tiene relevo) o porque la misión terminó antes de llegar a él. Los dos casos se
distinguen leyendo `condicion` y `veredicto`, no la marca.

> **`reloj` se graba precisamente porque el valor correcto es uno solo.** Si alguien lanza el
> coordinador sin `use_sim_time`, el registro lo delata en vez de producir números sesgados en
> silencio. En el banco físico `"pared"` es legítimo: no hay `/clock`. La restricción cruzada está
> en §4.3.

**Las cuatro métricas de OE4 no se guardan**: son `t_respuesta = t_primer_movimiento − t_solicitud`,
`t_asignacion = t_robot_activo − t_solicitud` y `hueco = t_inicio_tramo2 − t_fin_tramo1`, todas
derivables de las marcas. Guardar el dato y su derivada invita a que se contradigan. El analizador
las calcula.

### 3.6 `verdad_de_terreno`

| Campo | Tipo | Simulación | Físico |
|---|---|---|---|
| `fuente` | enum | `"gazebo_worldpose_via_odom"` | `"cinta_metrica"` |
| `error_posicion_m` | float \| null | calculado de `/odom` contra la pose del catálogo | leído de la cinta |
| `pose_final` | objeto \| null | `{x, y, yaw}` | `null` |
| `incertidumbre_m` | float | `0.0` | `~0.01` |
| `medido_por` | string | `"automatico"` | nombre de quien midió |
| `nota` | string | | |

> **`error_posicion_m` es el único campo que decide el éxito, y se llena igual en los dos bancos.**
> Por eso el criterio de §3.3 del protocolo no necesita una rama por banco. Lo que cambia es la
> `fuente` y la `incertidumbre_m`: 0,0 en simulación porque es un oráculo, ~1 cm en físico porque es
> una cinta leída por una persona.
>
> **`pose_final` va `null` en físico** porque la cinta da una *distancia*, no una pose. Rellenarla
> con `/odom` sería volver a llamar verdad de terreno a rf2o, que es el error que este documento
> existe para no cometer.
>
> Las cintas se pegan **en las coordenadas del catálogo**, no «donde parezca»: los mundos se
> midieron del edificio real, así que `puntos_interes.yaml` contiene coordenadas del edificio y los
> dos bancos comparten sistema de referencia. Lo que falta para poder hacerlo está en §8.

### 3.7 `veredicto` — las tres condiciones de §3.3, por separado

`exito` (bool) · `c1_posicion` · `c2_completada_sin_fallida` · `c3_relevo` (`null` en condición A) ·
`motivo_fallo`

- `c1_posicion` — `error_posicion_m ≤ 0,25 m`
- `c2_completada_sin_fallida` — la misión llegó a `COMPLETADA` sin pasar por `FALLIDA`
- `c3_relevo` — en condición B, `num_relevos == 1`

`exito = c1 ∧ c2 ∧ (c3 si aplica)`.

> **No basta con guardar el AND.** Si la tasa de éxito sale baja hay que poder decir *cuál*
> condición falló. En el caso de **R3** —que hoy sabemos que va a ocurrir— fallaría `c1` con `c2` y
> `c3` en verde, y eso es un diagnóstico. Un `exito: false` suelto no lo es.
>
> **El rumbo de llegada no entra aquí.** Se mide y se reporta como descriptiva (§3.8). La razón está
> en el §4 del protocolo y en R12.

#### 3.7.1 `continuidad` — RF-24, y por qué está aquí sin decidir nada

*Añadido en la versión 1.1.0 del esquema, el 2026-08-31.* Hasta esa fecha el campo no existía, y la
consecuencia salió a la luz al escribir el analizador: **RF-24, que el §2 del protocolo llama «la
variable de respuesta principal», no se podía calcular desde el registro.** Las marcas daban el
`hueco` del relevo, pero la condición binaria del §3.4 —que `etapa` nunca valga `INACTIVA` y
`robot_activo` nunca quede vacío— se comprueba sobre la secuencia de `estado_mision`, que vive en el
bag y no llegaba al JSON. Llegar a S24 así habría significado ejecutar treinta corridas sin medir la
variable que el experimento existe para medir.

| Campo | Tipo | Notas |
|---|---|---|
| `continua` | bool \| null | `null` en condición A y cuando la ventana no se puede cerrar |
| `ventana` | `[t0, t1]` \| null | el intervalo realmente recorrido |
| `instantes_inactiva` | número[] | los `t` en que `etapa` valía `INACTIVA` dentro de la ventana |
| `instantes_sin_agente` | número[] | los `t` en que `robot_activo` estaba vacío |
| `motivo` | string | por qué es `null`, o qué se rompió |

Tres decisiones que no son obvias:

**Está dentro de `veredicto` pero fuera del AND que decide `exito`.** El §3.3 del protocolo lista
tres condiciones y ésta no es ninguna. Una misión puede llegar a 4 cm del destino, sin `FALLIDA` y
con su único relevo, y aun así haber tenido un bache de coordinación en medio: eso es exactamente lo
que RF-24 existe para detectar. Metiéndola en el éxito quedaría escondida dentro de un
`exito: false` que ya vendría dado por otra causa, y RF-23 y RF-24 dejarían de ser dos variables.

**La ventana es `[t_robot_activo, t_completada]`, no `[t_solicitud, t_completada]`.** Es una
precisión necesaria del §3.4, no una licencia. Entre las dos primeras marcas está el estado
`RECIBIDA`, que el §3.2 **obliga** a publicar con `robot_activo` vacío —es el instante en que el
servidor acepta el goal y todavía no ha planificado—. Con el intervalo literal, ese vacío deliberado
haría que **toda** misión saliera discontinua, incluida una perfecta, y RF-24 valdría 0 % por
construcción. Es el mismo defecto estructural que tuvo el tiempo de asignación hasta el 2026-08-29:
una definición que da siempre el mismo número no está midiendo el sistema, está midiendo la
definición. El tramo excluido no queda sin vigilar —es justo lo que mide RF-22, acotado a menos de
un tick de `/clock`—. El cierre es `t_completada` **inclusive**: después el coordinador vuelve a
`INACTIVA`, que es su reposo normal, y contarlo sería el mismo error por el otro extremo.

**`null` no es `false`.** Sin `t_completada` la ventana no se puede recorrer, y decir «discontinua»
confundiría *no terminó* con *se quedó sin nadie a cargo*. Son dos fallos distintos, el primero ya
lo cuenta `c2_completada_sin_fallida`, y duplicarlo aquí inflaría el recuento de discontinuidades
con misiones que nunca llegaron a relevar. El analizador saca esas misiones del denominador y las
lista; **lo que no hace nunca es dar por continua una misión que nadie miró.**

Se guardan los instantes y no sólo el booleano porque un `false` suelto no se diagnostica: con el
`t` exacto se va al bag y se ve qué pasó.

### 3.8 `descriptivas` — se miden y se reportan, no deciden

`error_rumbo_rad` · `desviacion_z_m` (por robot) · `distancia_recorrida_m` · `num_cuspides` ·
`tiempo_total_s` · `deriva_map_odom_m` (`null` en físico)

> **`error_rumbo_rad`** está porque §3.3 lo exige explícitamente como variable descriptiva.
>
> **`desviacion_z_m`** verifica **RNF-01** en la misma corrida: ningún robot cruza de nivel, lo que
> cruza es el mensaje. En S18 fue de 1,9 µm.
>
> **`num_cuspides`** convierte en rutina la comparación que **R12** lleva pendiente desde el 18-ago.
> En vez de una medición puntual contra el registro del 21-ago, cada misión la aporta.
>
> **`deriva_map_odom_m`** es la cifra que el 26-ago delató a AMCL: 1,977 m de deriva en una
> transformada que, con `/odom` publicado desde `WorldPose()`, debería ser constante. Grabarla en
> cada misión hace que la campaña **cuantifique R3** en vez de solo padecerlo. Va `null` en físico,
> donde `map→odom` no es un error medible contra nada.

### 3.9 `salud_del_banco` — para que un descarte sea demostrable

`rtf` (`null` en físico) · `controladores_activos` por robot · `condicion_inicial` (opcional) ·
`gzserver_vivo_al_final` (`null` en físico) · `descartada` (bool) · `causa_descarte`

**`causa_descarte` es un enumerado cerrado**, y son exactamente las cuatro causas admitidas del §8:

```
"caida_gazebo" | "controladores_incompletos" | "rtf_bajo" | "fallo_anfitrion" | null
```

> Así *«la lista es cerrada»* deja de ser una frase del documento y pasa a ser algo que el archivo
> no permite violar. Si alguien quiere descartar una corrida porque «AMCL se perdió» o «el
> planificador no encontró ruta», el validador lo rechaza — y con razón: §8 dice que ésos *«son
> precisamente los modos de fallo que el experimento existe para cuantificar»*. Es el sitio exacto
> por donde una campaña se corrompe, y conviene que esté cerrado con llave y no con buena voluntad.
>
> `rtf` y `gzserver_vivo_al_final` van `null` en el banco físico: no existe RTF en hardware real.
> Son dos de los campos asimétricos que la §2.3 del plan pedía prever.

`controladores_activos` guarda `"7/7"` o lo que hubiera. Sigue siendo obligatorio comprobarlo antes
de medir: la carrera del `controller_manager` se cerró el 26-ago, pero cero fallos en 18 arranques
no es una garantía y el fallo es silencioso.

#### `condicion_inicial` — el criterio que no sobrevivía al bag (añadido el 2026-09-04)

De los cinco criterios de validez del §8 del runbook, cuatro se comprueban *a posteriori* sobre el
bag. El primero no: **que el robot sepa dónde está, dentro de 0,15 m, es una compuerta previa**, y
hasta esta fecha su resultado se quedaba en la terminal del paso 3 y se perdía al cerrarla. Las
corridas del 30-ago sólo pueden darse por buenas **4 de 5**, y es irreconstruible.

```json
"condicion_inicial": {
  "criterio": "localizacion",
  "tolerancia_m": 0.15, "tolerancia_yaw_grados": 10.0,
  "por_robot": {"robot1": {
    "desviacion_m": 0.031, "desviacion_yaw_grados": 1.2,
    "error_localizacion_m": 0.031, "error_localizacion_yaw_grados": 1.2,
    "dentro": true}}
}
```

Lo escribe `grabar_mision.sh` en `<bag>/condicion_inicial.json` **justo antes de abrir el bag**, y de
ahí lo lee el compositor. El momento no es negociable: el error no depende de la misión sino del
tiempo que el robot lleve **quieto** —resbala ~17 mm/min aunque nadie lo mande y AMCL no lo corrige
hasta acumular 25 cm—, así que medirlo en otro instante mide otra cosa.

**Qué decide `dentro`: `error_localizacion_m`, no `desviacion_m`.** Es el cambio del 2026-09-04 y
tiene una razón medida. `desviacion_m` es la distancia a la tabla de spawn, y como criterio rechazó
una corrida sana: `S21_piloto_A_03` salió a 1,19 m y 43,92 m «de su pose declarada» sólo porque los
robots venían de la misión anterior, cuando su error de localización era de 0,032 m —mejor que el
del piloto que sí pasó, 0,040 m— y llegó a 0,068 m del destino, la mejor llegada del día. La
magnitud que hace daño es que la **creencia** de AMCL se separe de la **verdad**; la distancia al
spawn sólo era un sustituto de ella, válido mientras el robot no se hubiese movido a propósito.
Y en el banco físico no se puede respawnear nada, así que un criterio de «estar en la pose de
spawn» es inaplicable donde esto tiene que acabar.

`desviacion_m` se sigue guardando porque en pila recién levantada **coincide** con el error de
localización —AMCL se siembra con la pose declarada, así que son el mismo número por construcción:
0,0401 y 0,0401 en `S21_piloto_B_02`—, y esa coincidencia es la prueba de que el criterio nuevo
subsume al viejo en vez de aflojarlo.

La creencia se lee de `/<robot>/amcl_pose` y **no** de la composición de `/tf`. Se probaron las dos:
la composición `(map→odom) ∘ pose_odom` da 0,0007 m al arrancar en vez de 0,040 m, porque AMCL aún
no ha corregido y `/odom` ya es la verdad, de modo que sigue a la verdad por construcción y la
compuerta aprobaría siempre. `/amcl_pose` se ofrece TRANSIENT_LOCAL —`durability: 1` en el
`offered_qos_profiles` del bag, frente al `2` (VOLATILE) de `/odom`—, así que un suscriptor tardío
recibe la última pose aunque AMCL lleve minutos sin publicar. Hay que pedirlo con ese perfil: con el
de por defecto el emparejamiento ni siquiera se produce.

Se guarda **la medida además del sí/no**, para poder rehacer el veredicto si la tolerancia cambia y
para poder mirar la distribución de las 30 corridas. `dentro: null` significa **no se pudo medir**,
que no es lo mismo que estar en su sitio: el §8 manda descartar la corrida cuando el criterio 1 no
se cumple, y un hueco silencioso la colaría.

> El campo es **opcional**, igual que `escenario_por_robot`: los registros compuestos antes del
> 2026-09-04 —entre ellos los dos pilotos del §9.3 del runbook, que son evidencia entregada— no
> pueden invalidarse por un campo que no existía cuando se grabaron. Por eso no hay salto de versión
> del esquema.
>
> Por el mismo motivo `criterio` tampoco es obligatorio, y **su ausencia es informativa**: un
> `condicion_inicial` sin él es del criterio viejo y su `dentro` no significa lo mismo. Sin ese
> campo, un registro de antes y uno de después serían indistinguibles.

### 3.10 `traza`

`bag` · `decimada_hz` (5,0) · `puntos[]` de `{t, robot, x, y, yaw}`

Decimada a 5 Hz para que el JSON sirva por sí solo para graficar sin reabrir el bag: unos 1200
puntos en una misión de 120 s con dos robots, ~50 KB.

**El bag sigue siendo la fuente.** Esto es una copia de conveniencia, y la distinción importa: el
26-ago la medición de rf2o se obtuvo metiéndole el `/scan` de `mision3` a un nodo que nunca corrió
en esa misión. Ninguna traza decimada habría permitido eso. Cuando alguien pregunte en octubre algo
que hoy no previmos, la respuesta está en el bag.

---

## 4. Casos límite y errores

### 4.1 Toda misión solicitada produce un registro

Incluidas las que fallan antes de mover un robot. Si `planificar()` lanza `ErrorPlanificacion`
(línea 169 del coordinador), el registro se escribe con `t_primer_movimiento` y `t_completada` en
`null`, `veredicto.exito = false` y `motivo_fallo` con el texto. **Una misión sin registro se
contaría como no ocurrida, y eso infla la tasa de éxito por omisión.**

### 4.2 El compositor falla ruidosamente, nunca inventa

| Situación | Qué hace `componer_registro.py` |
|---|---|
| El bag no tiene `/coordinacion/estado_mision` | Sale con código distinto de cero y lo dice. No escribe un registro con marcas en `null`: eso sería indistinguible de una misión que falló |
| El bag contiene más de un `mision_id` | Sale con error. §6.4 manda un `gzserver` por corrida; dos misiones en un bag significa que el procedimiento no se siguió |
| El bag no tiene `/clock` y `banco = simulacion` | Sale con error (ver §4.3) |
| Falta un tópico de la lista de §2.2 | Advertencia, no error, salvo que sea uno del que salga una marca |

### 4.3 Restricciones cruzadas que el JSON Schema hace cumplir

- `banco = "simulacion"` ⟹ `marcas.reloj = "/clock"` **y** `verdad_de_terreno.fuente = "gazebo_worldpose_via_odom"` **y** `salud_del_banco.rtf` no es `null`.
- `banco = "fisico"` ⟹ `verdad_de_terreno.fuente = "cinta_metrica"` **y** `pose_final = null` **y** `rtf = null` **y** `deriva_map_odom_m = null`.
- `condicion = "A"` ⟹ `t_fin_tramo1 = null`, `t_inicio_tramo2 = null`, `c3_relevo = null`.
- `condicion = "B"` ⟹ `c3_relevo` no es `null`. Las dos marcas de relevo **sí pueden ir `null`**: una
  misión inter-nivel que falla antes de llegar a la transferencia nunca las produce, y exigirlas
  obligaría a inventar un número. Lo que el esquema sí impone es que si hay `t_inicio_tramo2` haya
  `t_fin_tramo1`, y que `t_fin_tramo1 ≤ t_inicio_tramo2`.
- `veredicto.exito = true` ⟹ `t_completada` no es `null`, y en condición B tampoco las dos marcas de
  relevo. Un éxito con marcas incompletas es un error del compositor, no un dato.
- `descartada = true` ⟺ `causa_descarte` no es `null`.

### 4.4 La medida de cinta llega después de la corrida

En el banco físico, el registro se compone al terminar con `verdad_de_terreno.error_posicion_m` y
`medido_por` en `null`, y una segunda pasada los rellena.

**`null` significa «pendiente de medir».** El registro es válido contra el esquema, pero **el
analizador de campaña rechaza cualquier registro con `error_posicion_m` en `null`**: sin la medida
no hay veredicto. Dos niveles distintos, a propósito: válido como captura, no listo para análisis.

### 4.5 Misión cancelada por el usuario

`goal_handle.canceled()` produce `motivo_fallo: "Cancelada por el usuario"` y **cuenta como fallo**:
no está en la lista cerrada del §8. En una campaña no debería ocurrir nunca, y si ocurre el registro
lo deja visible.

---

## 5. Cómo se verifica

**El compositor se prueba sin Gazebo.** Un bag sintético construido por el propio test —una decena
de mensajes de `estado_mision` y una trayectoria de `/odom` con velocidades conocidas— permite
comprobar de forma determinista:

1. `t_primer_movimiento` cae en la muestra correcta, incluido el caso de un pico de ruido aislado
   por encima de 0,02 m/s que **no** debe dispararlo (son tres muestras consecutivas, no una).
2. Condición A deja los tres campos de relevo en `null`; condición B no.
3. Un `estado_mision` con `etapa = FALLIDA` en medio pone `c2` en `false` aunque después llegue
   `COMPLETADA`.
4. Cada una de las restricciones cruzadas de §4.3 rechaza el registro que la viola — una prueba por
   restricción, incluida la de `exito = true` con `t_completada` en `null`.
5. Un bag con dos `mision_id` sale con error.
6. Un `causa_descarte` fuera del enumerado sale con error.

**Y una comprobación de integración, una sola vez:** la primera misión real que se grabe con
`grabar_mision.sh` se compone y se revisa a mano campo por campo. Después de eso, la prueba unitaria
es la que protege.

Los bags de `~/tesis_evidencia/S20_localizacion/` **no sirven de banco de pruebas completo** —no
tienen `/clock` ni `estado_mision`— pero sí para probar la parte de trayectoria: son datos reales,
con una llegada fuera de tolerancia que ejercita `c1_posicion = false`.

---

## 6. Alternativas descartadas

| Enfoque | Por qué no |
|---|---|
| **El coordinador escribe el registro.** Es dueño de la misión y tiene las marcas | Para `t_primer_movimiento` tendría que acumular `/odom` a 50 Hz en memoria mientras navega —hoy solo guarda la última muestra en `self.ultimo_odom`—. Y si el coordinador se cae a mitad de misión no queda registro **de la misión que falló**, que es justo la que la tasa de éxito necesita contar. Además el nodo pasaría a hacer coordinación y metrología |
| **Un nodo registrador aparte, escuchando en vivo** | Solo puede ser tan preciso como lo que oye, y `estado_mision` va a 1 Hz. Son además dos procesos que hay que lanzar en orden: si el registrador arranca tarde se pierde `t_solicitud` y la misión no tiene registro |
| **Componer desde el bag** ✅ | Único de los tres en que simulación y hardware usan el mismo código, que es lo que hace posible S26. No corre nada durante la misión que pueda sesgar el RTF. Se puede reanalizar cuando alguien pregunte algo no previsto. Y el registrador no puede tumbar la misión, porque durante la misión no existe |

**El riesgo del enfoque elegido, escrito:** depende de que haya bag. Si el vehículo físico no puede
grabar mientras navega, la mitad física del esquema se queda sin traza y las métricas que dependen
de ella —`t_primer_movimiento`, o sea RF-21— no se pueden calcular igual en los dos bancos. **Se
comprueba el 2026-08-28** en la misma salida del frente B. Si sale que no, hay que declararlo como
amenaza a la validez de S26 en el §11 del protocolo, no descubrirlo en la comparación.

---

## 7. Cómo se cambia esto sin romper la campaña

- **Añadir un campo opcional** → sube la versión menor (`1.1.0`). Los registros `1.0.0` siguen
  siendo válidos y el analizador los acepta.
- **Cambiar el significado o el tipo de un campo, o quitar uno** → sube la versión mayor (`2.0.0`).
  El analizador **no mezcla mayores**: esos datos se reportan aparte o la campaña se repite.
- **Después de ejecutar la primera corrida de S24, ningún cambio es gratis.** Si hace falta uno, se
  anota en la bitácora de `ESTADO.md` con la fecha, el motivo y qué corridas quedan afectadas.

### 7.1 Cambios aplicados

| Versión | Fecha | Cambio | Qué pasa con los registros anteriores |
|---|---|---|---|
| `1.0.0` | 2026-08-22 | versión congelada inicial | — |
| `1.1.0` | 2026-08-31 | se añade `veredicto.continuidad` (§3.7.1) | siguen siendo válidos; el `required` del campo está condicionado a `esquema_version == "1.1.0"` en el `allOf` del esquema |

**Se aprovechó la ventana correcta.** El cambio entra en S21, con S24 a tres semanas y cero corridas
de campaña ejecutadas: no hay ninguna que quede afectada. Si el hueco lo hubiera destapado el
analizador en S24 —que es cuando se habría notado, al ver la métrica principal en blanco— la
elección habría sido entre repetir la campaña o entregar sin RF-24.

Los tres registros de S20 (`S20_A_M1`, `S20_A_M2`, `S20_RECIBIDA_01`) **se quedan en `1.0.0` y no se
recomponen.** Son de condición A, donde la continuidad es `null` por definición del §3.4, así que
recomponerlos añadiría un campo vacío y perdería la trazabilidad de con qué versión se escribieron.
Que el esquema siga aceptándolos sin tocarlos es la prueba de que el versionado del §7 funciona: una
comprobación de `prueba_componer_registro.py` valida ese caso explícitamente, en los dos sentidos
—obligatorio hacia delante, inofensivo hacia atrás—.

---

## 8. Lo que este documento no resuelve

1. **El origen del sistema de coordenadas en el edificio real.** Las cintas van en las coordenadas
   del catálogo, pero para pegarlas hace falta una marca física de referencia: dónde está el (0, 0)
   y hacia dónde apunta la x. En simulación lo fija el `.world`; en el pasillo lo tiene que fijar
   alguien. Es trabajo del frente B y no del esquema, pero sin ello la §3.6 no se puede ejecutar.
2. **El analizador de campaña** (§9.6 del protocolo), que lee los N registros y produce las cuatro
   métricas con sus intervalos de confianza. Este documento define su entrada, no él.
3. **`herramientas/sortear_misiones.py`** (§6.3), que produce `campana` y `semilla`.
4. **Si conviene ejecutar la campaña de S24 con R3 abierto.** §8 del protocolo prohíbe descartar una
   corrida porque AMCL se perdiera, y con razón; de ahí no se sigue que convenga medir antes de
   decidir sobre R3. Es una decisión de calendario, no de esquema.

---

## 9. Trazabilidad

| Este documento | Se apoya en |
|---|---|
| §1, §3.5, §3.6, §3.7 | [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) §1, §3, §6.2 |
| §3.9, §4.5 | ídem §8 — lista cerrada de descartes |
| §2, §5 | ídem §9.4 — *«un archivo por misión, procesable sin intervención manual»* |
| §1, §3.6, §3.8 | [`ESTADO.md`](../ESTADO.md) §7 bitácora del 2026-08-26, y **R3** |
| §3.8 | **R12** (cúspides) y **RNF-01** (desviación de `z`) |
| §2.1, §3.4 | [`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md) §5 — `EstadoMision`, `GuiarUsuario` |
| §1, §6 | [`PLAN_S20.md`](PLAN_S20.md) §2.3 |

Requisito que satisface: **RF-25**. Sin él no hay **RF-21** a **RF-24**, que son las cuatro métricas
de **OE4**.
