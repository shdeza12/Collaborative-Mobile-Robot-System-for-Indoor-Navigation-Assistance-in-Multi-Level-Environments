# Banco del tiempo de asignación (RF-22) — la cifra que el bag no puede dar

**Semana 21 · 2026-08-30.** Cierra el pendiente 7 de la [§9 del
protocolo](../PROTOCOLO_EXPERIMENTAL.md) y da por primera vez un número para el **tiempo de
asignación**, que es una de las cuatro métricas del objetivo específico 4 y hasta hoy no tenía
forma de reportarse.

Herramienta: [`herramientas/banco_tiempo_asignacion.py`](../../herramientas/banco_tiempo_asignacion.py).
Prueba de su parte pura: [`herramientas/prueba_banco_tiempo_asignacion.py`](../../herramientas/prueba_banco_tiempo_asignacion.py).
Registros: [`s20260830`](registros/S21_banco_asignacion_s20260830.json),
[`s99`](registros/S21_banco_asignacion_s99.json),
[`s7`](registros/S21_banco_asignacion_s7.json) y
[`s555`](registros/S21_banco_asignacion_s555.json) —este último posterior a la fusión de las ramas
de Jonny, ver §3.

---

## 1. Por qué hace falta un banco y no basta la campaña

El protocolo define la métrica sobre dos mensajes del bag:

```
t_asignacion = t_robot_activo − t_solicitud
```

y del bag esa resta vale **cero siempre**, se ejecute lo que se ejecute. La cadena es corta y no
tiene ningún eslabón discutible:

1. `ros2 bag record --use-sim-time` sella cada mensaje con el reloj de simulación.
2. El reloj de simulación solo avanza cuando llega un mensaje de `/clock`.
3. `gazebo_ros_init` publica `/clock` a 10 Hz.
4. Luego **todo sello del bag está cuantizado a 100 ms**.

Y asignar es una búsqueda en memoria sobre 31 puntos: como se mide más abajo, unos 150 µs, tres
órdenes de magnitud por debajo de un tick. Las dos marcas caen en el mismo tick y la resta da
`0,0 s`. Eso no mide el evento, **mide el reloj**.

### 1.1 Dos defectos distintos que conviene no confundir

El §3.2.1 del protocolo ya los separa, y aquí se confirman los dos con datos nuevos.

**El primero era de software y está corregido.** Hasta el 2026-08-29 el coordinador fijaba `etapa` y
`robot_activo` en la misma llamada y publicaba **una** vez, así que no existía ningún mensaje entre
«llegó la solicitud» y «ya hay agente». Se corrigió con la marca `RECIBIDA`.

**El segundo no es de software y sigue ahí.** Corregido lo anterior, las dos marcas ya son dos
mensajes distintos —y siguen cayendo en el mismo tick—. El arreglo del 29-ago era necesario pero
**no suficiente**.

### 1.2 Confirmación independiente sobre la misión del 30-ago

La misión de dos niveles `piso1_representacion → piso2_lab_313`
([bag `S21_dominio_unico_001`](S21_bloqueo_dominios.md)) da los seis intervalos entre marcas
consecutivas:

| transición | intervalo |
|---|---|
| `INACTIVA → RECIBIDA` | 253,4000 s |
| `RECIBIDA → TRAMO_1` | **0,0000 s** |
| `TRAMO_1 → TRAMO_1` | 8,5000 s |
| `TRAMO_1 → TRANSFERENCIA` | 10,1000 s |
| `TRANSFERENCIA → TRAMO_2` | 3,9000 s |
| `TRAMO_2 → COMPLETADA` | 25,1000 s |

**Los seis son múltiplos exactos de 0,1 s.** Eso generaliza lo que el 29-ago se había observado
sobre un solo par de marcas: la cuantización no afecta al tiempo de asignación en particular, sino a
**toda la cadena de marcas del registro**. Para los otros intervalos —de segundos— 100 ms de
resolución es aceptable; para éste no.

---

## 2. Qué mide el banco, exactamente

| | |
|---|---|
| Reloj | `time.perf_counter_ns()`, monótono, resolución de nanosegundos |
| Dónde se lee | **dentro** del proceso del coordinador, envolviendo su método `_marcar` |
| Entorno | coordinador aislado: sin Gazebo, sin Nav2, sin ningún robot, `use_sim_time: false` |
| Catálogo | `puntos_interes.yaml`, 31 puntos, SHA-256 `849ecee96258f753…8dcd` |
| Repeticiones | 30 por corrida, alternando pares intra-nivel e inter-nivel, con semilla anotada |
| Se reporta | mediana y máximo, **no la media** |

Se envuelve `_marcar` y no `_publicar_estado` **a propósito**: `_publicar_estado` lo llama también el
latido de 1 Hz, y contar latidos como marcas mezclaría dos cosas distintas. La lectura se toma al
volver de `_marcar`, que es cuando el mensaje ya se publicó.

**Queda dentro de la medida** todo lo que el coordinador hace entre las dos marcas: la publicación
del feedback, `planificar()` entera —que es el aporte declarado del proyecto— y el armado del mensaje
de la primera etapa. **Queda fuera** el transporte DDS, y debe quedar fuera: cuánto tarda un mensaje
en llegar a un suscriptor no es tiempo de asignación.

La misión aborta después, al no encontrar `navigate_to_pose`. No afecta a lo medido, porque las dos
marcas se publican antes de tocar ningún robot.

---

## 3. Resultado

Cuatro corridas de 30 misiones, con semillas distintas, sobre el mismo catálogo.

| | semilla 20260830 | semilla 99 | semilla 7 | semilla 555 |
|---|---|---|---|---|
| n | 30 | 30 | 30 | 30 |
| **mediana** | **160,9 µs** | **154,3 µs** | **173,4 µs** | **175,3 µs** |
| **máximo** | **283,8 µs** | **223,8 µs** | **272,0 µs** | **306,4 µs** |
| mínimo | 127,5 µs | 127,2 µs | 143,3 µs | 129,1 µs |
| intra-nivel (n=15) | mediana 157,6 · máx 235,1 | mediana 150,5 · máx 223,8 | mediana 180,4 · máx 246,5 | mediana 156,5 · máx 306,4 |
| inter-nivel (n=15) | mediana 168,8 · máx 283,8 | mediana 168,6 · máx 186,4 | mediana 166,7 · máx 272,0 | mediana 178,9 · máx 269,8 |

La cuarta se corrió el mismo día, **después de fusionar la rama `registrador-mision`**, y ese era su
motivo: el banco envuelve `_marcar` del coordinador, así que una fusión que tocara ese método lo
dejaría midiendo otra cosa sin avisar. Sigue midiendo, y en el mismo rango.

**La cota del protocolo se cumple con holgura de dos órdenes y medio.** El máximo de las cuatro
corridas, 306,4 µs, es **326 veces menor que un tick de `/clock`**. La afirmación que la campaña
puede sostener —*«el tiempo de asignación es menor que 100 ms en las N misiones»*— no solo es cierta:
lo es por un margen que hace imposible que una corrida la incumpla por ruido.

Esa es **toda** la conclusión que estos datos sostienen. Lo que sigue explica por qué no dan para
más.

### 3.1 Lo que parecía un efecto de rama y no lo es

Con las tres primeras corridas disponibles, la mediana inter-nivel salía por encima de la
intra-nivel, y la explicación era tentadora: `planificar()` devuelve 2 tramos en la rama intra-nivel
y 4 en la inter-nivel, además de buscar los dos puntos de transferencia. Se llegó a escribir en este
mismo documento que el coste medido «sigue a la estructura del código».

**La corrida con semilla 7 lo desmiente**: intra 180,4 µs contra inter 166,7 µs, invertido. El
recuento honesto es 5 de 6 corridas a favor y una en contra, que no es un efecto, es una moneda con
sesgo sin demostrar.

La razón de fondo se ve comparando las dos escalas:

| | rango |
|---|---|
| diferencia intra↔inter dentro de una corrida | ~10 µs, salvo la semilla 555 con ~22 µs |
| variación de la mediana global **entre** corridas | 154,3 → 175,3 µs, es decir ~21 µs |

**La variación entre corridas es mayor que el efecto que se pretendía medir.** Este banco corre sobre
un PC con planificador de propósito general y sin fijar afinidad de CPU ni prioridad; la carga de la
máquina entra en la medida y domina. Separar las dos ramas exigiría un diseño distinto —pares
emparejados dentro de la misma corrida, y muchas más repeticiones—, y **no hace falta para RF-22**,
que pide una cifra y una cota, no un modelo de coste del planificador.

Se deja escrito porque el error estuvo a punto de publicarse: tres corridas coincidentes bastaron
para redactar una explicación causal convincente de algo que la cuarta borró.

Lo que sí justifica que el sorteo **alterne** las dos ramas es otra cosa, y se mantiene: si solo se
midiera una, se estaría caracterizando media función y reportándola como si fuera la entera.

---

## 4. Un fallo del propio banco, encontrado y corregido durante la sesión

Las dos primeras corridas escribían a un nombre fijo, `S21_banco_asignacion.json`, y **la segunda
pisó a la primera sin decir nada**. Es exactamente el fallo silencioso que este repositorio persigue:
una replicación se pierde en el acto mismo de hacerla.

Corregido en dos pasos, y el primero estaba mal:

1. Se metió la semilla en el nombre y se añadió una negativa a sobrescribir. Pero la comprobación
   quedó **al final**, así que el banco corría las 30 misiones enteras para luego negarse a escribir,
   y además tenía que salir con el ejecutor girando: `terminate called without an active exception` y
   volcado de núcleo.
2. La comprobación se movió **antes de levantar ROS**. Ahora falla en 0,43 s y sin volcado.

Las cifras de las dos corridas perdidas —medianas 154,8 µs y 153,5 µs— se anotan aquí solo como
testigo de reproducibilidad. Contando las seis corridas del día, **las medianas caen entre 153,5 y
175,3 µs**, un rango del 14 %, que es la variabilidad que hay que tener en mente al leer la §3.1.

---

## 5. Qué se pierde, dicho sin adornos

Lo que ya advertía el §3.2.2 del protocolo, y que este banco no arregla: el tiempo de asignación deja
de ser una variable medida en cada corrida y pasa a ser **una constante caracterizada aparte**. Se
pierde toda posibilidad de estudiar cómo varía con la condición experimental, con el par
origen–destino o con la carga del equipo. Es una degradación real frente a lo que el protocolo
prometía el 22-ago, y se acepta porque la alternativa —reportar treinta ceros— es peor.

Lo único que la campaña seguirá aportando sobre esta métrica es la **cota superior verificada** en
las 30 corridas. Si alguna diera `t_asignacion > 0`, eso sí sería un dato, y de los graves:
significaría que la asignación tardó más de 100 ms, es decir **más de 350 veces lo medido aquí**, y
habría que investigarlo antes de agregarlo.

---

## 6. Lo que este banco NO prueba

1. **No prueba nada sobre el carro físico.** Está medido en el PC, con Humble y con este catálogo. La
   tarjeta del vehículo corre Jazzy y ni siquiera tiene `coordinacion_msgs` compilado todavía.
2. **No caracteriza el crecimiento con el tamaño del catálogo.** Los 31 puntos son los de hoy. Si el
   catálogo creciera un orden de magnitud habría que repetirlo; el margen de 326× deja sitio de
   sobra, pero eso es una previsión, no una medida.
3. **No mide la latencia extremo a extremo que percibe el usuario.** Deja fuera el transporte DDS a
   propósito (§2). Quien quiera esa cifra necesita otra medición, y no es RF-22.
4. **No sustituye a la campaña.** Da la cifra puntual de RF-22; la cota por misión y las otras tres
   métricas de OE4 siguen saliendo de los bags.
