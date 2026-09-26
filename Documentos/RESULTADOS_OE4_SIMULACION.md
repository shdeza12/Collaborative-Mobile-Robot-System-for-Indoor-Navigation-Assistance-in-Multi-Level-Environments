# Resultados de la campaña de evaluación en simulación (OE4)

**Emitido el 2026-09-19 (S23 de 32), con la implementación ya congelada en el tag
`v0.4-implementacion-congelada`.** Analiza las **30 misiones** de la campaña corrida el 2026-09-04 y
2026-09-05, cuyos registros están en [`Evidencia/registros/`](Evidencia/registros/) y cuyo agregado
es [`S21_metricas_campana_oe4.json`](Evidencia/S21_metricas_campana_oe4.json).

**Para qué sirve.** Es el capítulo de resultados del objetivo específico 4: *«evaluar el desempeño
del sistema mediante pruebas experimentales en un entorno interior controlado, utilizando métricas
como tiempo de respuesta, tiempo de asignación de robot, tasa de éxito en la entrega de asistencia y
continuidad del servicio entre niveles»*. Reporta lo que la campaña mide, con qué incertidumbre, y
—sobre todo— **qué afirmaciones sostiene y cuáles no**.

**Qué NO es.** No fija método: eso lo hace
[`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md), escrito el 2026-08-22 **antes** de
instrumentar, y manda sobre este documento en toda definición. No es el resultado del sistema: es el
resultado **en simulación**. La campaña física de RF-27 no se ha ejecutado, y el §7 dice qué tiene
que añadir.

**Cómo se mantiene.** Las cifras salen de los registros entregados, que **no se recomponen**
(decisión del 2026-09-16, [`S23_reproducibilidad_de_los_registros.md`](Evidencia/S23_reproducibilidad_de_los_registros.md)).
Si una cifra de aquí discrepa del agregado, manda el agregado.

---

## 1. Qué se midió, sobre qué, y con qué validez

### 1.1 Diseño

N = 30 misiones sorteadas con semilla, repartidas en dos condiciones de 15 y cuatro estratos que
cruzan la condición con el piso (§6.2.1 del protocolo):

| Estrato | Condición | Origen → destino | Relevos | N |
|---|---|---|---|---|
| A1 | A — control | piso 1 → piso 1 | 0 | 8 |
| A2 | A — control | piso 2 → piso 2 | 0 | 7 |
| B12 | B — inter-nivel | piso 1 → piso 2 | 1 | 8 |
| B21 | B — inter-nivel | piso 2 → piso 1 | 1 | 7 |

La condición **B es la que responde la pregunta de investigación**; la A es el control, y sin ella
no se puede afirmar que el relevo no degrade el servicio. El piso entra **como control**, no como
factor: se equilibró dentro de cada condición para que el contraste A−B no arrastrara la diferencia
entre pisos, que no es despreciable —en el piloto 3 la deriva de AMCL fue de 0,0209 m/m en el piso 2
contra 0,0036 y 0,0069 m/m en el piso 1—.

Las 10 primeras misiones se sortearon con semilla `20260822`; las 20 restantes con `20260904`, al
enmendar el diseño a mitad de campaña. El §6.2.2 del protocolo declara qué se conserva y qué no.

### 1.2 La campaña es válida

| Comprobación | Techo o criterio | Medido | Veredicto |
|---|---|---|---|
| Descartes | ≤ 20 % de N, o sea ≤ 6 | **0 de 30** | ✅ |
| RTF durante la corrida (RNF-06) | ≥ 0,99 | mín **0,9917**, mediana 0,9978 | ✅ |
| Condición inicial, posición | ≤ 0,15 m | máx **0,0684 m** en 60 comprobaciones | ✅ |
| Condición inicial, rumbo | ≤ 10° | máx **5,45°** en 60 comprobaciones | ✅ |
| Constancia de `z` (RNF-01) | ≤ 0,05 m | máx **7,013 mm** en 60 parejas | ✅ |
| Catálogo de puntos | mismo SHA-256 en las 30 | **un único** `849ecee9…` | ✅ |

`analizar_campana.py` dictamina **`VALIDA`**. Ninguna corrida se perdió por caída de Gazebo,
controladores incompletos, RTF bajo, fallo del anfitrión ni cancelación —las cinco causas de
descarte admitidas—, así que la tasa de éxito se calcula sobre las 30 sorteadas y no sobre un
subconjunto superviviente.

### 1.3 La cadena bag → registro es reproducible

El 2026-09-16 se recompusieron los 46 registros del repositorio desde sus bags conservados con
código cuatro versiones de esquema posterior. De los 44 recomponibles: **44/44 con el mismo
veredicto, 44/44 con el bloque `marcas` idéntico campo a campo, 44/44 con las `descriptivas`
idénticas**. Los 30 resultados de OE4 no dependen del estado en que estuviera el portátil el 5 de
septiembre.

Esto importa porque **28 de los 30 registros llevan `procedencia.repositorio_limpio: false`**: el
árbol de trabajo tenía cambios sin comitear cuando se compuso el registro. Visto solo, ese campo
invita a dudar de la reproducibilidad. La recomposición del 16-sep responde la duda por el camino
que vale —volviendo a computar desde el dato crudo— y no por el que no vale, que sería recomponer
los registros entregados y reescribirles el commit.

### 1.4 Dos limitaciones de trazabilidad, dichas aquí y no escondidas

**(a) Tres misiones se corrieron dos veces.** Los registros entregados de las misiones 13, 22 y 28
son `S21_OE4_13_2`, `S21_OE4_22_2` y `S21_OE4_28_2`; la hoja de corridas
([`HOJA_CORRIDAS_OE4.md`](HOJA_CORRIDAS_OE4.md)) las planificaba sin sufijo. Lo que los datos dicen
con certeza: las tres se ejecutaron **consecutivas al final de la jornada** —17:47, 17:51 y 17:55
UTC— y con un commit **distinto** al del resto de la tanda, `22c5f07` frente a `0e2b46c`. El motivo
de la repetición **no consta en el repositorio**, y ninguna de las tres quedó marcada como descarte.

La sospecha que esto levanta —haber repetido hasta obtener un éxito— es la correcta, y hay que
contestarla con el dato: **`S21_OE4_28_2` es uno de los cuatro fallos**, con el mayor error de
llegada de toda la campaña (0,347 m). Una repetición orientada al éxito no habría entregado ese
registro. Eso hace la hipótesis improbable, pero **no la descarta formalmente**, y la manera de
cerrarla no existe hoy: haría falta el registro de la primera corrida, que no se conserva.

**(b) El esquema de los 30 registros es `1.1.0`.** El campo `descriptivas.hueco_relevo_s` se añadió
en `1.3.0` el 2026-09-16 y los registros entregados no se recompusieron. No se pierde evidencia: el
analizador calcula el hueco como `t_inicio_tramo2 − t_fin_tramo1` sobre las marcas que los 30
registros sí traen, y la comprobación del 16-sep verificó que las dos fuentes coinciden con
**discrepancia exactamente 0,0** en los 23 huecos comparables.

---

## 2. Las cuatro métricas

### 2.1 Tasa de éxito en la entrega de asistencia (RF-23)

Una misión es exitosa si y solo si la pose final está a **≤ 0,25 m** del destino declarado —medido
contra `/<ns>/odom`, nunca contra el `SUCCEEDED` de Nav2— **y** la misión alcanzó
`etapa = COMPLETADA` sin pasar por `FALLIDA`.

| | n | éxitos | tasa | IC 95 % (Wilson) |
|---|---|---|---|---|
| **Campaña completa** | 30 | 26 | **86,7 %** | **70,3 – 94,7 %** |
| Condición A — control | 15 | 12 | 80,0 % | 54,8 – 93,0 % |
| Condición B — inter-nivel | 15 | 14 | 93,3 % | 70,2 – 98,8 % |

Distribución de los éxitos por estrato: A1 **6/8**, A2 **6/7**, B12 **8/8**, B21 **6/7**.

**La afirmación defendible es «la tasa de éxito supera el 70 %», no «la tasa es del 86,7 %».** Con
N = 30 el intervalo de Wilson mide 24 puntos porcentuales de ancho, y el límite es de diseño: no se
arregla trabajando más, se arreglaría con más N. El 86,7 % es el estimador puntual y se reporta como
tal, acompañado siempre de su intervalo.

### 2.2 Tiempo de respuesta (RF-21)

`t_respuesta = t_primer_movimiento − t_solicitud`, donde el primer movimiento es la primera muestra
de `/<ns>/odom` con `|v| ≥ 0,02 m/s` sostenida dos muestras más.

**Se reporta por escalones, no con media y desviación**, y la razón está en el instrumento:

| `t_respuesta` | 0,1 s | 0,2 s | 0,3 s | 0,4 s |
|---|---|---|---|---|
| misiones | 10 | 15 | 4 | 1 |

Los cuatro valores del rango entero son múltiplos exactos de 100 ms, que es el tick de `/clock`. **La
resolución del instrumento vale entre el 25 % y el 100 % de la magnitud medida.** La mediana de
0,2 s significa «uno o dos ticks», no «doscientos milisegundos». Dar media y desviación —el
analizador las calcula: 0,187 s y 0,078 s— sugeriría una precisión que el reloj no entrega; están en
la salida para comparar lotes entre sí, no para llegar al informe como si fueran la medida.

**La cota sí se sostiene, y es la que le importa a un usuario: el robot arranca en menos de medio
segundo, en las 30 corridas, con holgura.**

### 2.3 Tiempo de asignación de robot (RF-22)

**Esta es la métrica que puede reportarse mal sin que nadie lo note, y hay que decirlo antes de dar
ninguna cifra.** Sobre el bag, la resta `t_robot_activo − t_solicitud` vale **0,0 s en las 30
misiones**. No porque el coordinador sea infinitamente rápido, sino porque las dos marcas caen en el
mismo tick de `/clock`: `gazebo_ros_init` lo publica a 10 Hz y `ros2 bag record --use-sim-time` sella
cada mensaje con ese reloj, de modo que todo sello del bag está cuantizado a 100 ms. **Quien tome
esa columna del registro y escriba «tiempo de asignación: 0 s» estará reportando el reloj, no el
sistema.**

Subir la frecuencia de `/clock` no es la salida: resolver un evento de esa duración a dos cifras
exigiría unos 10 kHz, que compiten por CPU justo donde RNF-06 pide RTF ≥ 0,99. Se cambiaría una
métrica inmedible por dos métricas sesgadas.

Se reportan, en consecuencia, dos cosas distintas:

| | Qué se afirma | Evidencia |
|---|---|---|
| **En la campaña, por misión** | el tiempo de asignación es **menor que un tick, < 100 ms**, en las 30 | 30 registros con la resta en 0,0 s |
| **Una vez, en banco** | mediana **154,3 – 175,3 µs**, máximo **306,4 µs** | 4 corridas de n = 30 con semillas distintas, [`S21_banco_tiempo_asignacion.md`](Evidencia/S21_banco_tiempo_asignacion.md) |

El banco corre el coordinador **aislado, sin Gazebo ni Nav2, sobre reloj de pared**
(`time.perf_counter_ns()`, `use_sim_time: false`), y es válido porque las dos marcas se publican
antes de tocar ningún robot: la asignación no depende de que la simulación exista. El máximo global
de 306,4 µs es **326 veces menor que un tick de `/clock`**, lo que explica por qué la campaña no
puede verlo.

**Qué se pierde al hacerlo así, sin adornos.** El tiempo de asignación deja de ser una variable
medida en cada corrida y pasa a ser una constante caracterizada aparte. Se pierde toda posibilidad
de estudiar cómo varía con la condición, con el par origen–destino o con la carga del equipo. Es una
degradación real frente a lo que el protocolo prometía el 22-ago, y se acepta porque la alternativa
—reportar treinta ceros— es peor.

### 2.4 Continuidad del servicio entre niveles (RF-24)

RF-24 es **la variable de respuesta principal** del proyecto: la que responde la pregunta de
investigación. Tiene dos mitades y **solo una de ellas es un resultado experimental.**

**La mitad binaria es un invariante estructural, no una medida.** El criterio exige que entre
`t_robot_activo` y `t_completada` el campo `etapa` nunca valga `INACTIVA` y `robot_activo` nunca
quede vacío. Los dos únicos productores de esos valores están en `coordinacion/coordinador.py` y los
dos caen **fuera de la ventana por delante**: `etapa = INACTIVA` solo se publica en el constructor
del nodo, antes de la primera misión, y `robot_activo` vacío solo en `_marcar(RECIBIDA, …)` y en el
`FALLIDA` del fallo de planificación, ambos anteriores al instante en que la ventana abre. Dentro
del bucle de tramos, cada `_marcar` recibe un robot lleno. **No existe ruta de ejecución que lo
incumpla.**

El resultado —**14/14, o sea 0 incumplimientos de 0 posibles**— se reporta por tanto literalmente
así: *«ninguna misión se quedó sin agente, y no podía quedarse, porque el coordinador no publica
ninguno de los dos valores dentro de la ventana»*. Es una afirmación cierta y verificable sobre la
arquitectura. Lo que no es, es un resultado experimental. Presentarla como el fruto de 30 corridas
sería el peor error del informe; se detectó en el barrido de criterios infalsables del 2026-09-11
(riesgo R14) y se corrigió el 2026-09-16.

Evalúa 14 y no 15 misiones entre niveles porque la misión 27 nunca alcanzó `COMPLETADA`, y medir
continuidad sobre una ventana que no cierra no significa nada.

**La mitad que sí varía, y que es la evidencia real del relevo, es el hueco:**

```
hueco = t_inicio_tramo2 − t_fin_tramo1
```

| `hueco` | 0,1 s | 0,2 s |
|---|---|---|
| misiones | 10 | 5 |

n = 15, mediana 0,1 s, máximo 0,2 s. Otra vez el suelo del instrumento: el hueco tomó exactamente
**uno o dos ticks** de `/clock`, así que la mediana de 0,1 s significa «un tick», no «cien
milisegundos». **La cota es lo defendible: `hueco ≤ 200 ms` en las 15 misiones entre niveles.** Y el
hueco se reporta aunque la binaria se cumpla, precisamente porque un relevo correcto pero de 40 s
sería un mal resultado que la binaria escondería.

---

## 3. El contraste A−B, que es la pregunta de investigación

El propósito del control era poder afirmar que **el relevo no degrada el servicio**. Lo que salió:

| | Tasa de éxito | IC 95 % | Error de llegada, mediana |
|---|---|---|---|
| A — sin relevo | 80,0 % (12/15) | 54,8 – 93,0 % | 0,1225 m |
| B — con relevo | 93,3 % (14/15) | 70,2 – 98,8 % | 0,0977 m |

**Este contraste no sostiene ninguna conclusión.** Los intervalos se solapan en casi toda su
extensión, y además apuntan **en contra de la intuición**: la condición con relevo salió mejor que
el control, tanto en tasa como en error mediano de llegada. Con n = 15 por condición, esa diferencia
es indistinguible del ruido de muestreo.

Decir esto con claridad es más útil que el resultado que se buscaba. **Lo que la campaña sí permite
afirmar es que no hay ninguna señal de que el relevo degrade el servicio** —ni en tasa de éxito, ni
en error de llegada, ni en tiempo de respuesta—, y que el mecanismo de relevo se ejecuta con un
hueco acotado por 200 ms. Lo que **no** permite afirmar es que B sea mejor que A, ni cuantificar
ninguna diferencia entre las dos.

El desglose por estrato (§2.1) se reporta como **observación descriptiva y nada más**: con n ≈ 7 por
celda el intervalo de Wilson es tan ancho que no permite afirmar nada, y el piso entró en el diseño
como control, no como factor.

---

## 4. El modo de fallo

### 4.1 Los cuatro fallos son un solo modo, y el modo tiene nombre

Las cuatro misiones fallidas terminaron **cerrando en `FALLIDA`**, declaradas por el coordinador, sin
alcanzar nunca `COMPLETADA`. Y las cuatro lo hicieron por la misma razón, que el propio coordinador
publicó en `/coordinacion/estado_mision`:

> *«No se pudo completar el trayecto: 'robot1' dijo SUCCEEDED pero /odom lo situa a 0.292 m del
> punto, por encima de los 0.25 m de tolerancia»* — `S21_OE4_11`

| Misión | Condición | Estrato | Cierre | Nav2 | Distancia al declarar meta | Error en la última muestra |
|---|---|---|---|---|---|---|
| `S21_OE4_24` | A | A1 | `FALLIDA` | `SUCCEEDED` | 0,269 m | 0,2838 m |
| `S21_OE4_11` | A | A1 | `FALLIDA` | `SUCCEEDED` | 0,292 m | 0,2953 m |
| `S21_OE4_27` | B | B21 | `FALLIDA` | `SUCCEEDED` | 0,314 m | 0,3107 m |
| `S21_OE4_28_2` | A | A2 | `FALLIDA` | `SUCCEEDED` | 0,345 m | 0,3471 m |

**El modo de fallo es la discrepancia entre lo que el robot cree y dónde está.** En las cuatro, el
controlador de Nav2 declaró la meta alcanzada —`SUCCEEDED`, lo que por construcción significa que se
creía dentro de la `xy_goal_tolerance` de 0,15 m en el marco `map`— y `/odom`, que en simulación es
la pose omnisciente del motor de física, lo desmintió. El coordinador tiene su propio verificador de
llegada, no se fía del `SUCCEEDED`, y por eso la misión cierra en `FALLIDA` en vez de contarse como
un éxito silencioso.

Ninguna otra cosa falló. No hubo colisiones, ni relevos rotos —`S21_OE4_27` completó su
`TRANSFERENCIA` y su `TRAMO_2`, y falló en la llegada del segundo tramo—, ni tiempos de espera
agotados, ni caídas del banco.

Las dos últimas columnas difieren entre 2 y 15 mm porque miden instantes distintos: el coordinador
evalúa en el momento del `SUCCEEDED`, y el registro compone sobre la última muestra del bag, que es
posterior. La diferencia es de la escala del propio movimiento residual y no afecta a ningún
veredicto.

La distribución completa del error de llegada sobre las 30: mediana **0,1058 m**, media 0,1251,
σ 0,0845, mínimo **0,0195 m**, p90 0,2838, máximo 0,3471.

**Un apunte sobre el criterio, porque el motivo agregado se lee mal.** El texto que
`analizar_campana.py` compone para estos cuatro —*«llegada a 0,295 m, fuera de 0,25 m; la misión no
llegó a COMPLETADA sin pasar por FALLIDA»*— enumera los criterios C1 y C2 como si fueran dos fallos
independientes, y **no lo son**: el coordinador declara `FALLIDA` precisamente porque aplica el mismo
umbral de 0,25 m que C1. C2 no puede dar «cumple» cuando C1 da «no cumple». Es un fallo contado dos
veces. No altera ningún resultado —el veredicto es `False` con uno o con dos, y ninguna misión
cambia de bando—, pero conviene escribirlo aquí antes de que lo encuentre un lector externo. Es
pariente de los defectos que catalogó el riesgo R14: allí un criterio no podía dar «no»; aquí dos
criterios no son independientes y dan «no» a la vez por construcción.

### 4.2 Dónde se agota el presupuesto de error

El criterio de 0,25 m no es arbitrario: el §3.3 del protocolo lo sostiene con un presupuesto de tres
términos, fijado el 2026-08-27 y anotado en `nav2_params_nav_amcl_sim_demo.yaml`.

| Término | Valor |
|---|---|
| Tolerancia de parada de Nav2 (`xy_goal_tolerance`) | 0,150 m |
| Error de AMCL previsto a 42 m | 0,065 m |
| Desfase del fin del plan | 0,023 m |
| **Total presupuestado** | **0,238 m** |
| Criterio de éxito | 0,250 m |

La holgura del presupuesto son 12 mm. **Los cuatro fallos no solo exceden el criterio: exceden el
presupuesto que lo justifica**, por entre 31 y 107 mm. Ese es el hallazgo cuantitativo de la
campaña: el presupuesto de error del protocolo **se agota en 4 de cada 30 corridas**, y la tasa de
éxito del 86,7 % es, exactamente, la fracción de corridas en que alcanza.

**Y el `SUCCEEDED` permite repartir el exceso, que es lo que de verdad importa.** Que Nav2 declarara
meta alcanzada acota el primer término por construcción: el error percibido por el robot era
**≤ 0,150 m**. Por desigualdad triangular, el residuo —los otros dos términos juntos— vale al menos
la distancia verdadera menos esos 0,150 m:

| Misión | Distancia verdadera | Residuo ≥ | Presupuestado | Factor |
|---|---|---|---|---|
| `S21_OE4_24` | 0,269 m | 0,119 m | 0,088 m | 1,35 × |
| `S21_OE4_11` | 0,292 m | 0,142 m | 0,088 m | 1,61 × |
| `S21_OE4_27` | 0,314 m | 0,164 m | 0,088 m | 1,86 × |
| `S21_OE4_28_2` | 0,345 m | 0,195 m | 0,088 m | 2,22 × |

**El término que se queda corto es el de la estimación de pose, no el de la parada.** El presupuesto
le asignaba 88 mm entre el error de AMCL y el desfase del fin del plan; en estas cuatro corridas hizo
falta entre 1,35 y 2,22 veces esa cantidad. El controlador cumplió su parte —paró donde creía que
debía parar— y lo que falló fue la creencia.

Conviene nombrar con precisión qué mide ese residuo, porque no es solo AMCL: agrupa el error de
localización, el desfase entre el marco del mapa construido con SLAM y el marco del mundo de Gazebo,
y el desfase del fin del plan. La campaña no permite separarlos, y el §7 dice qué haría falta para
separarlos.

Conviene notar que el diseño del presupuesto ya evitó un error peor. Hasta el 2026-08-27 la
tolerancia de parada y el criterio de éxito eran **el mismo número**, 0,25 m, lo que dejaba margen
cero para el error de localización; eso costó una llegada medida, con el vehículo parando
creyéndose a 0,240 m —dentro— estando a 0,297 m —fuera—. Bajar la parada a 0,15 m creó el margen.
Lo que la campaña muestra es que ese margen, de 88 mm, se queda corto una de cada siete u ocho veces.

### 4.3 El proxy que el registro guarda no sirve para esto

Dado el §4.2, la pregunta siguiente es si el registro permite ver venir el fallo. El único campo que
se acerca es `descriptivas.deriva_map_odom_m`, la norma de la transformada `map → odom`, y su
distribución es del mismo orden que el error de llegada —mediana 0,1375 m, máximo 0,3580 m—, lo que
lo hace un candidato atractivo.

**No lo es.** Sobre las 30 misiones, la correlación entre el error de llegada y la deriva
`map → odom` es **Pearson r = 0,078 y Spearman ρ = −0,015**: indistinguible de cero por cualquiera de
los dos. En los cuatro fallos la deriva vale 0,0696, 0,1344, 0,1494 y 0,3019 m, frente a una mediana
de **0,1375 m en los 26 éxitos**: el fallo de mayor error sí tiene la deriva más alta, pero otro de
los cuatro —`S21_OE4_24`, con 0,0696 m— tiene la mitad de la deriva mediana de las misiones que sí
acertaron. Con la deriva baja se falla y con la deriva alta se acierta.

La explicación es que las dos magnitudes no son la misma. `deriva_map_odom_m` acumula la corrección
que AMCL aplica a lo largo de **toda** la misión y está dominada por el desfase entre el origen del
mapa y el del mundo, que es aproximadamente constante; el residuo del §4.2 es la discrepancia
**instantánea** en el punto de parada. Un offset constante grande enmascara la variación que
importa.

### 4.4 Qué queda atribuido y qué no

**Atribuido:** el modo de fallo es único, identificado, y el exceso recae sobre el término de
estimación de pose del presupuesto, no sobre el de parada (§4.2). Esto se sostiene sin suposiciones:
sale del `SUCCEEDED` de Nav2, que acota el término de parada, y de `/odom`, que en simulación es
verdad exacta.

**No atribuido:** dentro de ese término no se puede separar el error de localización propiamente
dicho del desfase mapa–mundo ni del desfase del fin del plan, porque el registro no guarda ninguno
de los tres por separado.

La consecuencia es una recomendación concreta y barata, porque **el número ya se calcula**: el
coordinador lo computa para decidir el `FALLIDA` y lo escribe en `mensaje_usuario` como texto libre
—*«/odom lo situa a 0.292 m del punto»*—. Lo que falta es que ese valor llegue al **registro
estructurado** como campo numérico, en toda misión y no solo en las fallidas. Hoy, recuperarlo exige
abrir el bag y parsear una frase en castellano; eso es exactamente lo que RF-25 existe para evitar.

---

## 5. Observaciones descriptivas

No son resultados de OE4 y no se comparan entre condiciones. Se reportan porque describen la calidad
del movimiento, que la métrica binaria de éxito no captura.

**Maniobras de retroceso (cúspides).** Mediana 5,5 por misión, máximo **85** en `S21_OE4_09` —quince
veces la mediana—. Esa misión **tuvo éxito**, con un error de llegada de 0,055 m, muy por debajo de
la mediana de la campaña: un caso limpio de trayectoria mala con resultado bueno. La causa de las 85
cúspides se investigó aparte y está cerrada en
[`S22_R12_85_cuspides.md`](Evidencia/S22_R12_85_cuspides.md).

**Deriva `map → odom`.** Mediana 0,1375 m, máximo 0,3580 m. **No covaría con el error de llegada**
(§4.3) y por tanto no sirve para anticipar el modo de fallo, pese a ser el campo del registro que
más se le parece.

**Constancia de `z` (RNF-01).** 60 parejas, mediana 7,012 mm y máximo 7,013 mm, contra un umbral de
0,05 m: **0 de 60 fuera**. La dispersión entre misiones es de un micrómetro, lo que indica un
desplazamiento vertical constante del modelo y no un comportamiento dinámico.

**Rumbo de llegada.** No se reporta. El rumbo no es criterio de éxito —`yaw_goal_tolerance` vale
3,15 rad, o sea π, que es no imponerlo— y el campo `descriptivas.error_rumbo_rad` se **retiró** del
protocolo el 2026-09-16 en vez de rellenarse, por ser una promesa que ninguna corrida podía
falsar.

---

## 6. Qué sostiene esta campaña y qué no

**Sostiene, y se puede escribir tal cual:**

1. La tasa de éxito en la entrega de asistencia **supera el 70 %** (26/30; IC 95 % de Wilson
   70,3 – 94,7 %), sobre una campaña de N = 30 sorteada con semilla y con **0 descartes**.
2. El sistema **inicia el movimiento en menos de medio segundo** tras la solicitud, en las 30
   corridas, con la distribución de escalones del §2.2.
3. La asignación de robot tarda **menos de un tick de `/clock` (< 100 ms)** en las 30 corridas, y su
   valor puntual caracterizado en banco tiene mediana de **155–175 µs** y máximo de **306 µs**.
4. El relevo entre niveles se ejecuta con un **hueco acotado por 200 ms** en las 15 misiones
   inter-nivel.
5. **Ninguna misión se quedó sin agente a cargo, y no podía quedarse**, por la estructura del
   coordinador (§2.4).
6. **No hay señal de que el relevo degrade el servicio** en ninguna de las cuatro métricas.
7. El único modo de fallo observado es **el robot para creyéndose en la meta y no estarlo**: Nav2
   declara `SUCCEEDED` y la verdad de terreno lo sitúa entre 0,269 y 0,345 m del destino. El peor
   caso de toda la campaña no llega a 1,4 veces el criterio.
8. En ese modo, **el exceso recae sobre la estimación de pose y no sobre la parada del
   controlador**, entre 1,35 y 2,22 veces lo presupuestado (§4.2).

**No sostiene, y escribirlo sería un error:**

1. Que la tasa de éxito **sea** del 86,7 %. Es el estimador puntual de un intervalo de 24 puntos.
2. Que la condición B sea **mejor** que la A, ni ninguna cuantificación de la diferencia A−B.
3. Que el tiempo de respuesta **sea** de 0,187 ± 0,078 s. La resolución del reloj vale entre el 25 %
   y el 100 % de la magnitud.
4. Que el tiempo de asignación **sea** de 0 s. Eso mide el reloj.
5. Que la continuidad del 100 % sea un **resultado experimental**. Es un invariante de diseño.
6. Cuánto de ese exceso es error de AMCL y cuánto desfase entre el mapa y el mundo. El residuo está
   acotado, pero no descompuesto (§4.4).
7. Nada sobre el **sistema físico**. Todo lo anterior es simulación, y en simulación la verdad de
   terreno sale gratis (§7).

---

## 7. Qué debe añadir la campaña física (RF-27)

RF-27 es el único requisito rojo de OE4 y pide **N entre 5 y 10** corridas con el protocolo completo
sobre los vehículos reales. Tres cosas que esta campaña deja pedidas, en orden de importancia:

1. **El campo que falta, que ya se calcula.** Llevar al registro estructurado, como campo numérico y
   en toda misión, la distancia entre la pose estimada y la verdad de terreno en el instante en que
   el controlador declara meta alcanzada. Hoy existe solo como frase dentro de `mensaje_usuario` y
   solo en las fallidas (§4.4). Sin ese campo, un fallo de llegada en hardware exige abrir el bag
   para entenderlo.
2. **La verdad de terreno deja de ser gratuita.** En simulación, `/odom` es la pose omnisciente que
   el motor de física publica —`model_->WorldPose()`—, con incertidumbre 0,0 m, y por eso el criterio
   de éxito puede medirse contra ella. En hardware no existe tal cosa, y el instrumento que la
   sustituya debe ser **al menos 10 veces más preciso que el criterio**: para 0,25 m, eso son 2,5 cm.
3. **N cambia lo que se puede afirmar.** Con N entre 5 y 10, el intervalo de Wilson es mucho más
   ancho que el de esta campaña. La afirmación defendible en hardware no será una tasa, sino una
   cota, y conviene fijarla **antes** de correr —como se hizo aquí— y no después.

El resto de lo que bloquea RF-27 no es de medición sino de plataforma, y está acotado en
[`MAPA_TRABAJO_RESTANTE.md`](MAPA_TRABAJO_RESTANTE.md): la ruta crítica es publicar `odom → base_link`
en el vehículo.

**Actualización del 2026-09-25.** Esa ruta crítica ya no lo es: `rf2o` publica y mide sobre el
vehículo desde el 24-sep, y esa misma noche Nav2 navegó el carro sobre un mapa guardado
([`S24_nav2_navegacion_mapa_guardado.md`](Evidencia/S24_nav2_navegacion_mapa_guardado.md)). El
procedimiento de las compuertas previas, G-2 y G-3, está en
[`GUIA_CAMPANA_NAV2_HARDWARE.md`](GUIA_CAMPANA_NAV2_HARDWARE.md). **No es la campaña de RF-27**, que
pide el protocolo completo sobre los dos carros y va en S27 según
[`PLAN_S25.md`](PLAN_S25.md); pero deja probadas dos de las tres cosas de arriba, que la campaña
heredará: la verdad de terreno la da el **flexómetro**, que resuelve al medio centímetro —cinco veces
más fino que los 2,5 cm que pide el punto 2—, y cada corrida deja en su registro, como columnas
numéricas, el error de llegada según AMCL, según `/odom` y según la cinta, que es el campo del
punto 1. Cada misión deja además una imagen como esta, sacada del bag por
[`dibujar_corrida_nav2.py`](../herramientas/dibujar_corrida_nav2.py):

![La misión S21_OE4_01 de esta campaña, dibujada sobre el mapa del piso 1](Evidencia/S24_dibujo_corrida_oe4_simulacion.png)

*`S21_OE4_01`: el primer plan de Nav2 en verde, AMCL en azul y `/odom` alineado en la salida en
naranja. La separación entre azul y naranja es la deriva de la odometría simulada que AMCL corrige.
Es una misión de varias metas; la X marca la última.*

---

## 8. Trazabilidad

| Afirmación | De dónde sale |
|---|---|
| tasa 26/30, IC Wilson, 0 descartes | [`S21_metricas_campana_oe4.json`](Evidencia/S21_metricas_campana_oe4.json), producido por `herramientas/analizar_campana.py` |
| las 30 misiones, campo a campo | [`Evidencia/registros/`](Evidencia/registros/), `S21_OE4_01` … `S21_OE4_30` |
| definiciones, criterios y presupuesto de error | [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) §§3.1–3.4, 6.1–6.2 |
| estado y redacción de RF-21 a RF-27 | [`REQUISITOS.md`](REQUISITOS.md) §OE4 |
| tiempo de asignación en banco | [`S21_banco_tiempo_asignacion.md`](Evidencia/S21_banco_tiempo_asignacion.md) |
| RF-24 como invariante estructural (R14) | [`S22_barrido_criterios_infalsables.md`](Evidencia/S22_barrido_criterios_infalsables.md) y §3.4.1 del protocolo |
| reproducibilidad bag → registro, 44/44 | [`S23_reproducibilidad_de_los_registros.md`](Evidencia/S23_reproducibilidad_de_los_registros.md) |
| las 85 cúspides de `S21_OE4_09` | [`S22_R12_85_cuspides.md`](Evidencia/S22_R12_85_cuspides.md) |
| tolerancias de Nav2 | `Robot/aws-deepracer/deepracer_bringup/config/nav2_params_nav_amcl_sim_demo.yaml` |
| guion de las corridas | [`HOJA_CORRIDAS_OE4.md`](HOJA_CORRIDAS_OE4.md) |
| escalones, huecos, correlaciones y desglose por estrato | recalculados sobre los 30 registros el 2026-09-19 |
| cierre en `FALLIDA`, `SUCCEEDED` y distancias del coordinador | lectura del tópico `/coordinacion/estado_mision` en los bags de `~/tesis_evidencia/`, 2026-09-19 |
