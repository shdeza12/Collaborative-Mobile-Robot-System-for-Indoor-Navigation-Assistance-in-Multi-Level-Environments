# Protocolo experimental de OE4

> **Criterio de cierre de este documento:** otra persona puede repetir la campaña completa sin
> preguntarnos nada. Si al leerlo queda una decisión por tomar en el momento de medir, el protocolo
> no está terminado — porque esa decisión se tomará mirando los datos.

Fija, **antes de instrumentar nada**, qué se mide, cómo, cuántas veces, con qué criterio de éxito
y qué se hace con una corrida fallida.

Que se escriba antes no es formalismo. Un protocolo redactado después de ver los resultados se
acomoda sin querer a lo que salió: se elige el umbral que deja fuera justo las tres corridas malas,
se decide que aquel cuelgue «no contaba», y la campaña deja de poder refutar nada. La fecha de este
archivo en el historial de git es parte de la evidencia.

Objetivo específico 4 del anteproyecto §4.2:

> *«Evaluar el desempeño del sistema mediante pruebas experimentales en un entorno interior
> controlado, utilizando métricas como tiempo de respuesta, tiempo de asignación de robot, tasa de
> éxito en la entrega de asistencia y continuidad del servicio entre niveles.»*

---

## 1. La regla de oro: la verdad es `/odom`, nunca `SUCCEEDED`

**Un `SUCCEEDED` de Nav2 no es evidencia de nada.** Se adoptó como regla del proyecto el
2026-08-12 y es la base de todo lo que sigue.

`Reached the goal!` lo emite el controlador comparando la meta contra **la pose que le da AMCL**.
Si AMCL está mal localizado, Nav2 declara éxito sobre una pose que no es la real: con el mapa
inventado de agosto llegó a devolver `SUCCEEDED` sin que el vehículo se hubiera movido. El
resultado de Nav2 y el error de Nav2 salen de la misma fuente, así que uno no puede auditar al
otro.

`/odom` lo calcula el plugin de Gazebo con `model_->WorldPose()`: es la posición **real** del modelo
en el simulador, y no depende de nada de lo que se está midiendo.

La medición del 2026-08-21 muestra por qué importa:

| Destino | Nav2 dijo | Error real contra `/odom` |
|---|---|---|
| ETM1 (−15,92 · 10,59) | SUCCEEDED | 0,2092 m ✅ |
| ETM13 (−7,25 · 9,51) | SUCCEEDED | **0,2960 m — fuera de la tolerancia de 0,25** |
| Escaleras (−19,43 · 5,91) | SUCCEEDED | 0,1769 m · rumbo 5,65° ✅ |

Los tres dijeron `SUCCEEDED`; uno de los tres no había llegado. Sin contrastar contra `/odom`, la
tasa de éxito de esa muestra habría sido 100 % en vez de 67 %.

> **En hardware no hay `/odom` de simulador.** La verdad de terreno de la campaña física se toma
> con medición externa —cinta métrica sobre marcas fijas en el piso, fotografiadas—, no con la
> odometría de las ruedas, que patina y deriva. Se define en §10.

---

## 2. Qué se mide

Las cuatro métricas del anteproyecto, con el requisito que las formaliza en
[`REQUISITOS.md`](REQUISITOS.md) §5:

| Métrica | Requisito | Variable |
|---|---|---|
| Tiempo de respuesta | RF-21 | continua, segundos |
| Tiempo de asignación de robot | RF-22 | continua, segundos |
| Tasa de éxito en la entrega | RF-23 | proporción sobre N |
| Continuidad del servicio entre niveles | RF-24 | binaria por misión + hueco en segundos |

**RF-24 es la variable de respuesta principal.** Es la que responde la pregunta de investigación;
las otras tres caracterizan el sistema. Si hay que recortar, se recorta en las otras tres.

---

## 3. Definiciones operativas

Una métrica sin un evento de inicio y uno de fin **medibles por una máquina** no es una métrica, es
una intención. Todas las marcas temporales salen del mismo reloj: `/clock` del simulador, con
`use_sim_time: true` en todos los nodos.

### 3.1 Tiempo de respuesta (RF-21)

```
t_respuesta = t_primer_movimiento − t_solicitud
```

- **`t_solicitud`**: instante en que el servidor de la acción `/coordinacion/guiar_usuario`
  **acepta** el goal. No el instante en que la HRI lo envía: la latencia del navegador no es del
  sistema robótico y no se puede medir desde dentro.
- **`t_primer_movimiento`**: primera muestra de `/<ns>/odom` del robot asignado en la que
  `|v| ≥ 0,02 m/s` **y las dos muestras siguientes también**. Las tres muestras consecutivas están
  para no disparar con un pico de ruido; a 50 Hz cuestan 60 ms, muy por debajo de la resolución que
  interesa.

> El umbral de 0,02 m/s no es arbitrario: es dos órdenes de magnitud menor que la velocidad de
> crucero configurada (`desired_linear_vel: 0.5`) y mayor que el ruido en reposo observado. Si al
> pilotar (§7) resulta que el ruido en reposo lo supera, **se cambia el umbral en este documento y
> se vuelve a pilotar**, no se ajusta a mitad de campaña.

### 3.2 Tiempo de asignación (RF-22)

```
t_asignacion = t_robot_activo − t_solicitud
```

- **`t_solicitud`**: primer mensaje en `/coordinacion/estado_mision` con `etapa = RECIBIDA`, que el
  coordinador publica al aceptar el goal y **antes de planificar**, con `robot_activo` vacío. Es la
  §3.1 literal —«el instante en que el servidor acepta el goal»— hecha observable.
- **`t_robot_activo`**: primer mensaje en `/coordinacion/estado_mision` con `etapa = TRAMO_1` y
  `robot_activo` no vacío.

Se espera que sea mucho menor que el tiempo de respuesta, porque asignar es una decisión de
escritorio del coordinador y moverse no. **Si sale del mismo orden, es un hallazgo**, no un error de
medida: significaría que el coordinador está esperando algo.

**Esta métrica no se reporta como un valor por misión. Se reporta como una cota superior por misión
más una caracterización única en banco.** Lo que sigue dice por qué, y es una enmienda del
2026-08-29 a un documento congelado el 22-ago.

#### 3.2.1 Por qué el bag no puede dar este número

Dos defectos distintos, encontrados en ese orden, y solo el primero era de software.

**El primero era estructural.** Hasta el 2026-08-29 el coordinador fijaba `etapa` y `robot_activo` en
la misma llamada y publicaba **una** vez, así que no existía ningún mensaje entre «llegó la
solicitud» y «ya hay agente»: las dos marcas caían sobre el mismo mensaje y la resta valía cero
fuera cual fuera la corrida. Corregido con `EstadoMision/RECIBIDA`, verificado en
`Evidencia/registros/S20_RECIBIDA_01.json`.

**El segundo no lo es, y no tiene arreglo dentro del banco.** Corregido lo anterior, las dos marcas
siguen cayendo en el **mismo instante**: 247,6000 s las dos en la traza del bag de esa misma misión.
`/clock` lo publica `gazebo_ros_init` a **10 Hz**, y `ros2 bag record --use-sim-time` sella cada
mensaje con ese reloj, así que **todo sello del bag está cuantizado a 100 ms**. La asignación es una
búsqueda en una lista de 31 puntos y dura tres órdenes de magnitud menos que un tick. La resta de
dos sellos que caen en el mismo tick vale 0,0 s, y eso no es una medida del evento: es una medida
del reloj.

Subir la frecuencia de `/clock` no es la salida. Para resolver un evento de esa duración en dos
dígitos harían falta unos 10 kHz, y publicar `/clock` a 10 kHz compite con la simulación por CPU
justo donde RNF-06 exige RTF ≥ 0,99. Se cambiaría una métrica inmedible por dos métricas sesgadas.

#### 3.2.2 Lo que sí se reporta

**En la campaña (§6), por misión:** `t_solicitud` y `t_robot_activo` se registran igual que hasta
ahora, y de ellas se reporta la afirmación que los datos sí sostienen:

> el tiempo de asignación es **menor que un tick de `/clock`, es decir < 100 ms**, en las N misiones.

Una cota superior verificada en las 30 corridas es un resultado legítimo de OE4. Un cero repetido 30
veces no lo es. **Si alguna misión diera `t_asignacion > 0`, eso sí es un dato**, y de los graves:
significaría que la asignación tardó más de 100 ms, y hay que investigarlo antes de agregarlo.

**Una sola vez, en banco, fuera de la campaña:** el valor puntual se caracteriza con el coordinador
solo, **sin Gazebo y sobre reloj de pared**, que tiene resolución de nanosegundos. Es válido porque
las dos marcas se publican antes de tocar ningún robot: la asignación no depende de que la
simulación exista. La misión aborta después, al no encontrar `navigate_to_pose`, y eso no afecta a
lo medido.

Condiciones del banco, que hay que declarar al reportarlo:

| | |
|---|---|
| Reloj | de pared, `time.perf_counter_ns()`, dentro del proceso del coordinador |
| Entorno | coordinador aislado, sin Gazebo ni Nav2; `use_sim_time: false` |
| Catálogo | el `puntos_interes.yaml` vigente, con su SHA-256 anotado |
| Repeticiones | ≥ 30 invocaciones, alternando pares intra-nivel e inter-nivel |
| Se reporta | mediana y máximo, no la media: la distribución tiene cola por el planificador de Python |

El resultado va a `Documentos/Evidencia/`, **no a este documento**: aquí se fija el método, no la
cifra.

> **Qué se pierde al hacerlo así, dicho sin adornos.** El tiempo de asignación deja de ser una
> variable medida en cada corrida y pasa a ser una constante caracterizada aparte. Se pierde toda
> posibilidad de estudiar cómo varía con la condición, con el par origen–destino o con la carga del
> equipo. Es una degradación real frente a lo que este protocolo prometía el 22-ago, y se acepta
> porque la alternativa —reportar treinta ceros— es peor.

> **Nota histórica.** La versión congelada el 22-ago ya anticipaba una parte de esto: advertía de que
> `estado_mision` va a 1 Hz y exigía un mensaje **extraordinario** en cada cambio de etapa. Ese
> mensaje se construyó y funciona; es lo que hace que hoy la resolución sea de 100 ms y no de 1 s.
> Lo que la nota no vio es que por debajo del mensaje extraordinario sigue habiendo un reloj
> cuantizado, y que ese es el suelo de verdad.

### 3.3 Tasa de éxito (RF-23)

```
tasa = misiones_con_exito / N
```

Una misión es **exitosa** si y solo si se cumplen las tres:

1. La pose final del robot en `/<ns>/odom` está a **≤ 0,25 m** del destino declarado en
   `puntos_interes.yaml`, en distancia euclídea sobre el plano.
2. La misión llegó a `etapa = COMPLETADA` sin pasar por `FALLIDA`.
3. En una misión entre niveles, hubo relevo: `num_relevos = 1`.

**El rumbo de llegada NO es criterio de éxito.** Se mide y se reporta siempre, como variable
descriptiva, pero no decide. La razón está en §4.

**Los 0,25 m no se tocan, y desde el 2026-08-27 ya no coinciden con la `xy_goal_tolerance` de
Nav2.** Hasta ese día eran el mismo número, con esta justificación: «el sistema hizo lo que se le
pidió con la precisión que declara tener». La justificación era buena; igualar los números, no,
porque los dos umbrales miden cosas distintas. La tolerancia decide cuándo Nav2 **para**, y lo hace
contra lo que **cree** AMCL; este criterio decide cuándo la llegada se **acepta**, y se mide contra
`/<ns>/odom`, que es la verdad. Igualarlos dejaba margen cero para el error de localización, y eso
costó una llegada medida: el vehículo paró creyéndose a 0,240 m —dentro— estando a 0,297 m —fuera—.

La tolerancia de parada bajó entonces a 0,15 m, y el presupuesto que la sostiene está escrito en
`nav2_params_nav_amcl_sim_demo.yaml`: 0,150 de parada + 0,065 de error de AMCL previsto a 42 m +
0,023 de desfase del fin del plan = 0,238 m, que cabe en estos 0,25. **El criterio de éxito no
cambió**, ni debe cambiar: bajarlo a 0,15 destruiría ese presupuesto y declararía fallidas llegadas
que el protocolo aceptaba antes de que hubiera resultados a la vista.

### 3.4 Continuidad entre niveles (RF-24)

Solo aplica a misiones cuyo origen y destino están en niveles distintos.

```
hueco = t_inicio_tramo2 − t_fin_tramo1
```

- **`t_fin_tramo1`**: el robot del nivel de origen alcanza su punto de transferencia (criterio de
  §3.3.1 aplicado a ese punto).
- **`t_inicio_tramo2`**: primer movimiento del robot del segundo nivel, con el criterio de §3.1.

La continuidad **se cumple** si durante todo el intervalo `[t_solicitud, t_completada]` el campo
`etapa` de `estado_mision` nunca vale `INACTIVA`, y `robot_activo` nunca queda vacío. Es decir: en
ningún momento la misión se queda sin nadie a cargo.

`hueco` se reporta aunque la continuidad se cumpla: un relevo correcto pero de 40 s es un mal
resultado que la variable binaria escondería.

> **RNF-01 se verifica en la misma corrida:** la coordenada `z` de cada agente debe permanecer
> constante durante toda la misión. Ningún robot cruza de nivel; lo que cruza es el mensaje. Se
> comprueba con la desviación de `z` en `/odom`, que en S18 fue de 1,9 µm.

---

## 4. Por qué el rumbo no decide el éxito

Es la decisión de diseño experimental menos obvia del protocolo, y conviene dejarla argumentada
porque afecta al resultado principal.

El `SimpleGoalChecker` está configurado con `stateful: True`. Con esa opción, en cuanto se cumple la
tolerancia de **posición** la engancha y a partir de ahí **solo exige rumbo**. Un vehículo Ackermann
no puede girar sobre su propio eje —es RNF-05, y por eso se quitó la primitiva `<Spin>` del árbol de
comportamiento—, así que para corregir unos grados tiene que maniobrar hacia adelante y hacia atrás.
Se llegaron a observar **80 cúspides contra 2 planificadas**, hasta que el progress checker aborta.

Lo que hace esto peligroso para una campaña es que **es intermitente**: el 21-ago se predijo que
Escaleras fallaría y cerró en 5,65°. Un fallo aleatorio en 30 repeticiones no es reproducible, y la
tasa de éxito acabaría midiendo el goal checker en lugar del sistema.

**Se ataca por los dos lados:**

1. **`stateful: False`** en `nav2_params_nav_amcl_sim_demo.yaml`. Sin el enganche, el verificador
   reevalúa posición y rumbo en cada ciclo y desaparece el mecanismo que produce la maniobra
   patológica.
2. **El criterio de éxito mira solo posición**, contra `/odom`. Así la métrica no depende de una
   garantía que la plataforma no da.

El rumbo **no se esconde**: se registra en cada corrida y se reporta su distribución. Si resulta que
el sistema cierra el rumbo bien casi siempre, eso es un resultado a favor y estará en los datos.

> **El cambio de `stateful` todavía no está hecho, y no se da por bueno hasta medirlo.** Es el paso
> 1 de §9. Cambiar la línea es trivial; demostrar que quita las cúspides exige repetir los tres
> destinos del 21-ago y comparar el número de cúspides con
> [`herramientas/analizar_maniobra.py`](../herramientas/analizar_maniobra.py).

---

## 5. Configuración congelada

Durante toda la campaña, estos valores **no se tocan**. Si alguno cambia, las corridas anteriores no
son comparables con las posteriores y la campaña se reinicia.

| Parámetro | Valor | Dónde |
|---|---|---|
| `xy_goal_tolerance` | **0,15 m** (era 0,25 hasta el 2026-08-27, ver §3.3) | `nav2_params_nav_amcl_sim_demo.yaml` |
| `yaw_goal_tolerance` | **3,15 rad (~π)** — el rumbo final no se impone, ver §4 | ídem |
| `alpha1`…`alpha5` de AMCL | **0,01** (eran 0,2 hasta el 2026-08-27) | ídem |
| `stateful` | **False** | ídem |
| `desired_linear_vel` | 0,5 m/s | ídem |
| `required_movement_radius` | 0,5 m | progress checker |
| `movement_time_allowance` | 10,0 s | progress checker |
| `allow_reversing` | true (Reeds-Shepp) | planificador |
| Mundo piso 1 | `mundo_definitivo_piso1.world` | raíz del repositorio |
| Mundo piso 2 | `mundo_definitivo_piso2.world` | ídem |
| Mapa piso 1 | `mundo_definitivo_piso1.yaml` | `deepracer_bringup/maps/` |
| Mapa piso 2 | `mundo_definitivo_piso2.yaml` | ídem |
| Radio mínimo de giro | 0,284 m (derivado: `max_steer` 0,5236 rad, batalla 0,164 m) | URDF |
| Factor de tiempo real | ≥ 0,99 (RNF-06) | se verifica en cada corrida |

**Tres de estos valores cambiaron el 2026-08-27, y la regla de arriba se aplica.** La
`xy_goal_tolerance` y los cinco `alpha` de AMCL se movieron después de medir por qué fallaban las
llegadas (§3.3), y el `yaw_goal_tolerance` de la tabla estaba desactualizado desde antes. La
consecuencia es la que anuncia el párrafo de entrada, sin excepción: **la campaña de la condición A
empieza el 2026-08-27**, y los bags anteriores a esa fecha —`S20_piloto_*`, `S20_rutas_01`,
`S20_rutas_02`, `S20_localizacion`— no son comparables con los posteriores. Se conservan, y se usan,
pero solo como **control de la configuración vieja**: es contra ellos como se atribuye la mejora.
Los primeros de la campaña nueva son `S20_rutas_03`, `S20_rutas_04` y `S20_p2_01`.

**El RTF se comprueba en cada corrida y no es un adorno.** Con las dos pilas activas se midió 0,996
en S18. Si en una corrida baja de 0,99, sus tiempos no son válidos: esa corrida se descarta por
causa externa (§8) y se repite.

---

## 6. Diseño de la campaña

### 6.1 Tamaño de muestra

**N = 30 en simulación** (RF-26), **N entre 5 y 10 en hardware** (RF-27). Sale de la decisión D1 del
2026-08-05, y la razón es que una proporción exige N: con 5 corridas y 4 aciertos el intervalo de
confianza del 95 % va del 38 % al 96 %, que no permite afirmar nada; con 30 y 27 va del 80 % al
97 %.

Los vehículos físicos ejecutan el protocolo **como demostración funcional**, no como fuente de la
estadística. Las dos cosas se reportan por separado y nunca se agregan en una sola tasa.

### 6.2 Condiciones

La variable independiente es el **tipo de misión**:

| Condición | Origen y destino | Relevos | N |
|---|---|---|---|
| **A** — intra-nivel | ambos en el piso 1 | 0 | 15 |
| **B** — inter-nivel | piso 1 → piso 2 | 1 | 15 |

La condición B es la que responde la pregunta de investigación. La A es el control: da la línea base
de tiempo de respuesta y tasa de éxito **sin** relevo, y sin ella no se puede afirmar que el relevo
no degrada el servicio.

### 6.3 Selección de pares origen–destino

Los pares salen de `puntos_interes.yaml`, que es la fuente de verdad de los destinos. Se sortean
**con semilla fija** para que la campaña sea reproducible:

```bash
cd "$TESIS" && python3 herramientas/sortear_misiones.py --semilla 20260822 --n 30 --salida Documentos/Evidencia/campana_oe4_misiones.csv
```

> Se nombra aquí para fijar que el sorteo es del protocolo y no del operador: elegir los pares a
> mano el día de la campaña es la puerta de entrada al sesgo de selección.
>
> **Existe desde el 2026-08-30**, y hasta esa fecha esta nota decía «todavía no existe». Ese
> mismo día se ejecutó el comando de arriba tal cual está escrito y el listado quedó versionado en
> [`campana_oe4_misiones.csv`](Evidencia/campana_oe4_misiones.csv).

El listado sorteado se versiona **antes** de ejecutar la primera corrida. El orden de ejecución es
el del archivo, sin reordenar.

**Cuatro decisiones que este documento no fijaba y hubo que tomar al escribir la herramienta.** Se
listan aquí, y no solo en el código, porque son de diseño experimental:

1. **Los puntos de transferencia no se sortean**, ni como origen ni como destino. Una misión de
   condición B con destino `piso2_escalera` tendría un segundo tramo de longitud cero —el relevo
   ocurre justo ahí—, contaría como éxito sin haber navegado y tiraría del tiempo total de la
   condición B hacia abajo. Quedan **14 puntos elegibles en el piso 1 y 15 en el piso 2**.
2. **Sin reposición:** las 30 misiones son 30 pares distintos. Hay 182 pares posibles de condición A
   y 210 de condición B, así que no hace falta repetir, y una repetición gastaría una de las 30
   corridas sin cubrir un destino nuevo.
3. **El orden del archivo mezcla las dos condiciones.** Como el orden del archivo *es* el orden
   temporal de la campaña, ejecutar 15 de A y luego 15 de B confundiría cualquier deriva de la
   sesión con la diferencia entre condiciones, que es lo que se quiere medir.
4. **La herramienta se niega a sobrescribir un listado existente**, y comprueba antes de sortear.
   Pisar el listado a mitad de campaña dejaría unas corridas contra un listado y otras contra otro
   sin que nada en los registros lo delatara.

> **El sorteo no cubre el catálogo entero, y no pretende hacerlo.** Con la semilla 20260822 quedan
> cubiertos 10 de los 15 destinos del piso 2 y 9 de los 14 del piso 1. Es lo que da un sorteo
> aleatorio de 30 sobre 392 pares posibles. Si algún día se quiere cobertura garantizada, eso es un
> diseño **estratificado** y hay que decidirlo aquí antes de ejecutar, no ajustando la semilla
> hasta que salga bonito.

> **La misión del 2026-08-30 —`piso1_representacion → piso2_lab_313`— no está en el listado**, y
> por tanto no es la corrida 1 de la campaña ni puede agregarse a ella. Sigue siendo lo que dice
> [`S21_relevo_ejecutado.md`](Evidencia/S21_relevo_ejecutado.md): una demostración de que el
> relevo se ejecuta, con n = 1.

### 6.4 Aislamiento entre corridas

**Cada corrida arranca con un `gzserver` nuevo.** No se encadenan misiones sobre la misma
simulación: la carrera conocida al cargar controladores y la corrupción del daemon de ROS 2 dejan
estado que se arrastra, y un arrastre sistemático es exactamente lo que una campaña no puede tener.

El procedimiento de limpieza es el de la [guía de ejecución](GUIA_EJECUCION.md) §0.

**El procedimiento completo de una corrida —los seis comandos, lo que tiene que salir en cada uno,
qué hacer si no sale y las cinco condiciones que la hacen válida— está en
[`RUNBOOK_CAMPANA.md`](RUNBOOK_CAMPANA.md)**, escrito el 2026-08-30 para repetirse una vez por
misión sin tener que releer este documento.

Ahí se toma además una decisión que este protocolo no fijaba: **las dos pilas se levantan también
en las misiones de condición A**, aunque el `robot2` no participe. Si A corriera con un `gzserver`
y B con dos, la diferencia de tiempos entre condiciones llevaría dentro la diferencia de carga de
la máquina, y A dejaría de ser una línea base comparable.

---

## 7. Pilotaje antes de la campaña

**Cinco corridas de pilotaje, cuyos datos NO forman parte de la campaña** y se guardan aparte,
marcados como piloto.

Sirven para validar el instrumento, no el sistema. Se pilota para responder:

- ¿El umbral de 0,02 m/s de §3.1 dispara con el ruido en reposo?
- ¿El registro se escribe completo y es procesable sin tocarlo a mano (RF-25)?
- ¿La marca extraordinaria de cambio de etapa (§3.2) llega con la resolución necesaria?
- ¿El RTF se sostiene por encima de 0,99 con la instrumentación añadida?

**Si el pilotaje obliga a cambiar un umbral, se edita este documento, se registra el cambio en el
historial y se vuelve a pilotar.** Lo que no se hace nunca es cambiar un umbral con la campaña
empezada.

---

## 8. Qué se hace con una corrida fallida

**Por defecto, una corrida fallida cuenta como fallo** y entra en el denominador y no en el
numerador de la tasa de éxito. Repetirla hasta que salga bien daría una tasa del 100 % por
construcción, y la tasa de éxito es una de las cuatro métricas que exige OE4.

**Se descarta y se repite solo si la causa es demostrablemente ajena al sistema medido**, está en la
lista cerrada de abajo, y queda **registrada por escrito con su evidencia** en el informe de la
campaña.

| Causa admitida para descarte | Cómo se demuestra |
|---|---|
| Caída de `gzserver` o `gzclient` | el proceso no existe al terminar; log con el fallo |
| Uno o más de los 7 controladores no llegó a `active` | `ros2 control list_controllers` al arrancar la corrida |
| RTF por debajo de 0,99 (RNF-06) | medida de RTF de la corrida |
| Fallo de la máquina anfitriona ajeno al experimento | corte de energía, OOM del sistema, con su log |

**La lista es cerrada y está escrita antes de la campaña.** Cualquier otra cosa —el robot se
atascó, AMCL se perdió, el goal checker maniobró hasta abortar, el planificador no encontró ruta—
**es un fallo del sistema y cuenta como tal**. Son precisamente los modos de fallo que el
experimento existe para cuantificar.

Un descarte no es gratis: se documenta en la tabla de descartes del informe, con la corrida, la
causa y la evidencia. **Si los descartes superan el 20 % de las corridas, la campaña no es válida**
y hay que arreglar el banco de pruebas antes de repetirla — un instrumento que falla una de cada
cinco veces no mide.

---

## 9. Instrumentación: lo que hay que construir

En orden. **Escrito el 22-ago, cuando nada de esto existía; el estado es del 2026-08-29.**

1. **PENDIENTE — `stateful: False`** en el YAML, y **repetir los tres destinos del 21-ago**
   comparando el número de cúspides contra el registro de aquella corrida. Sin esa comparación el
   cambio es una creencia. Es el riesgo R12 y sigue abierto.
2. **HECHO — Paquete `coordinacion_msgs`** con sus cuatro definiciones
   ([`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md) §5). Sin él no hay `estado_mision`, y sin
   `estado_mision` no hay RF-22 ni RF-24. Falta compilarlo en la tarjeta Jazzy del carro.
3. **HECHO — Nodo de coordinación** que sirva `/coordinacion/guiar_usuario` y publique
   `estado_mision`, incluida la marca extraordinaria de cambio de etapa (§3.2), y desde el 29-ago
   la marca `RECIBIDA` que abre la ventana de asignación (§3.2.1).
4. **HECHO — Registrador de misión** (RF-25): un archivo por misión, estructurado, con todas las
   marcas temporales, la traza de `/odom` de cada robot y el RTF. Procesable sin intervención
   manual. El esquema quedó congelado el 2026-08-26 en
   [`ESQUEMA_REGISTRO_MISION.md`](ESQUEMA_REGISTRO_MISION.md), anclado a §3 y §8 de este
   protocolo, con los campos del banco físico previstos aunque en simulación vayan vacíos.
   Es `herramientas/componer_registro.py`, y compone desde el bag, después de la corrida.
5. **HECHO — `herramientas/sortear_misiones.py`** (§6.3), con su prueba en
   `herramientas/prueba_sortear_misiones.py`. Ejecutado el 2026-08-30 con semilla **20260822**
   sobre el catálogo de 31 puntos (SHA-256 `849ecee96258f753…8dcd`): las 30 misiones de la campaña
   están sorteadas y versionadas en
   [`Evidencia/campana_oe4_misiones.csv`](Evidencia/campana_oe4_misiones.csv), 15 de condición A y
   15 de B. La prueba comprueba, sobre el catálogo real, que **las 30 se pueden planificar** y que
   la condición que escribe el CSV es la misma que `condicion_de()` calculará en el coordinador; un
   listado con una misión implanificable no daría error hasta quemar una corrida.
6. **PENDIENTE — Analizador de campaña**: lee los N registros y produce las cuatro métricas con sus
   intervalos de confianza.
7. **HECHO — Banco del tiempo de asignación** (§3.2.2). Corre el coordinador aislado, sin
   Gazebo, mide sobre reloj de pared y reporta mediana y máximo. Es lo único que puede dar la cifra
   de RF-22, y no depende de la campaña. Es `herramientas/banco_tiempo_asignacion.py`, con su prueba
   en `herramientas/prueba_banco_tiempo_asignacion.py`. Ejecutado el 2026-08-30 sobre el catálogo de
   31 puntos: **mediana 154–175 µs, máximo 306,4 µs en cuatro corridas de 30 misiones**, es decir 326
   veces por debajo de un tick de `/clock`. Resultados y límites en
   [`Evidencia/S21_banco_tiempo_asignacion.md`](Evidencia/S21_banco_tiempo_asignacion.md).

---

## 10. Prerrequisitos que hoy NO se cumplen

**La campaña no puede empezar mientras alguno siga abierto.** Se listan porque un protocolo que
calla sus condiciones previas se ejecuta igual y produce números que no valen.

| Prerrequisito | Estado al 2026-08-30 |
|---|---|
| **`/odom` cruzado** — una lectura devolvió la posición del otro agente | 🟢 CERRADO el 2026-08-25 **con causa, no por no reproducirse**: el dominio 0 no lista ningún tópico `/robot2/*` ni el 2 ninguno `/robot1/*`, así que la publicación bajo espacio de nombres queda descartada y lo que quedaba era el daemon de `ros2cli`. La regla pasa a matarlo con `pkill -9` al cambiar de dominio; las métricas se calculan sobre bags, que no pasan por él ([`S20_hito_h3_dos_agentes.md`](Evidencia/S20_hito_h3_dos_agentes.md)) |
| **Carrera al cargar controladores** — un controlador puede quedar `unconfigured` | 🟢 CERRADO el 2026-08-26. La causa **no** era el arranque en paralelo sino un reintento sobre una operación no idempotente: `controller_manager_services.py` repite la petición tras 10 s sin respuesta y la segunda recibe `was already loaded`. Se pasa a `controller_manager spawner` con `--service-call-timeout 60`. Medido: de **2 fallos en 8** arranques dobles a **0 en 18**, con el arranque bajando de 37–39 s a 28–35 s. **Sigue siendo obligatorio comprobar «7 de 7» antes de medir**: cero en 18 no es garantía y el fallo es silencioso |
| **Mapa del piso 2** | 🟢 CERRADO el 2026-08-23, y **rehecho el 2026-08-26** al quitar seis paneles redundantes y redimensionar los dos del testero este: 40 760 celdas libres, 0 de frontera, cobertura 100,2 % × 100,9 %, `ACEPTADO` |
| **Destinos del piso 2 en `puntos_interes.yaml`** | 🟢 CERRADO el 2026-08-26. Los dieciséis, con nombre y parada derivada de la regla; el catálogo pasa a 32 destinos y la prueba del planificador a 992 planes |
| **Los dos agentes navegando simultáneamente** (H3) | 🟢 CERRADO el 2026-08-25 ([`S20_hito_h3_dos_agentes.md`](Evidencia/S20_hito_h3_dos_agentes.md)) |
| **Segundo vehículo físico** (R11) | 🔴 Administrativo. Bloquea solo la campaña física (RF-27), no la de simulación |
| **Un coordinador que alcance a los dos robots** *(añadido el 2026-08-27)* | 🟢 **CERRADO el 2026-08-30.** *Diagnóstico original, que se conserva porque sigue siendo correcto salvo en su conclusión:* «`robot1` corre en `ROS_DOMAIN_ID=0` y `robot2` en el 2 (`herramientas/robot.sh:62`), con un `gzserver` cada uno. La separación no es una preferencia: `gazebo_ros` de Humble aplica a todos los plugins el namespace del **primer** modelo cargado, así que un solo `gzserver` no puede llevar dos robots (§8 de [`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md)). Un nodo de ROS 2 vive en **un** dominio, luego el coordinador ve a uno de los dos y nunca a los dos.» **Lo que falló fue el último paso:** de «un nodo vive en un dominio» no se sigue que los robots necesiten dominios distintos. Lo que obliga a un `gzserver` por robot es el namespace de los plugins, no el DDS; los dos pueden compartir el dominio 0 y separarse por **nombres** —namespace, prefijo de TF incluido `map`, puerto de Gazebo y reloj propios—. Verificado con las dos pilas vivas: 94 981 transformadas y **cero** con marco hijo sin prefijo ([`S21_bloqueo_dominios.md`](Evidencia/S21_bloqueo_dominios.md)) |

**Seis de siete cerrados.** La **condición A** —misión de dos tramos dentro de un nivel— se puede
ejecutar, y se ejecutó el 2026-08-27 (`S20_rutas_03` y `S20_rutas_04`, cuatro llegadas entre 0,117
y 0,204 m). La **condición B** también, desde el 2026-08-30: la misión `piso1_representacion →
piso2_lab_313` se completó con **un relevo**, `exito: true` en 47,6 s, con llegadas de 0,128 m y
0,077 m contra `/odom` ([`S21_relevo_ejecutado.md`](Evidencia/S21_relevo_ejecutado.md)). El único
prerrequisito que queda abierto es **R11**, que es administrativo y afecta solo a la campaña física.

> **Esto NO significa que la campaña pueda empezar.** Los prerrequisitos son condiciones
> necesarias, no suficientes: la condición B tiene hoy **n = 1**, sin sorteo y sin registro
> compuesto. Lo que falta para arrancar está en el §9 —el sorteo de misiones y el analizador—, no
> en esta tabla.

**Instrumentación al 2026-08-27.** El registrador de misión (RF-25) **existe**: esquema versionado
y comprobable, `herramientas/grabar_mision.sh` sellando el bag con tiempo de simulación,
`herramientas/componer_registro.py` componiendo un registro validado contra el esquema, y
`herramientas/diagnosticar_llegada.py` dictaminando la llegada contra `/odom` y nunca contra el
`SUCCEEDED` de Nav2. **Falta el analizador de campaña**, y quedan **cuatro huecos medidos** sobre el
primer registro real:

1. `t_fin_tramo1` y `t_inicio_tramo2` salen `null` en **toda** misión de condición A, porque los dos
   tramos comparten `etapa: 1` y lo único que cambia es `destino_actual`. Hay que detectar el cambio
   de tramo por el `id` del destino, no por la etapa.
2. El **RTF no se puede recuperar** de un bag sellado con tiempo de simulación: no sobrevive
   ninguna referencia de reloj de pared. Hay que muestrearlo *durante* la corrida.
3. `procedencia.mundo` y `procedencia.mapa` se quedan vacíos.
4. `controladores_activos` sale `{}` y `gzserver_vivo_al_final` va escrito a mano.

Los cuatro se cierran con lo mismo: que `grabar_mision.sh` deje junto al bag un `condiciones.json`
con lo que solo se sabe mientras la misión corre.

---

## 11. Amenazas a la validez

Lo que puede hacer que estos números signifiquen otra cosa de la que parecen.

- **El error apunta en el sentido de la marcha.** Los tres errores del 21-ago lo hacen, lo que
  sugiere **frenado tardío** y no ruido de localización. Es una hipótesis **no verificada**. Si se
  confirma, es un sesgo sistemático y no aleatorio: no se cancela promediando, y habría que
  corregirlo antes de la campaña en vez de reportarlo como dispersión.
- **La simulación es Humble y el hardware es Jazzy** (R8). `NavigateToPose` difiere entre las dos
  distribuciones. Las corridas físicas y las simuladas **no son la misma condición experimental**, y
  por eso se reportan por separado y no se agregan.
- **N = 30 da intervalos anchos.** Con 27 aciertos, el IC del 95 % va del 80 % al 97 %. Las
  afirmaciones del informe tienen que caber en ese ancho: «la tasa supera el 80 %» es defendible,
  «la tasa es del 90 %» no lo es.
- **Un solo entorno.** Todo se mide en los dos pasillos de `mundo_definitivo_piso{1,2}.world`. Los
  resultados describen el desempeño **en ese edificio**, y así hay que enunciarlos. Generalizar a «entornos interiores» sería
  ir más allá de los datos.
- **El LiDAR simulado y el real no ven lo mismo** (R13, medido el 2026-08-23). El del simulador
  barre **300°**, con un cono ciego de 60° sobre el morro; el de fábrica del vehículo mide
  **360 muestras sobre 360°** (2026-08-21). Además la simulación lanza 600 rayos contra los 360
  reales. Cualquier diferencia sim ↔ hardware en *tasa de éxito* admite esta explicación
  alternativa, así que **no puede atribuirse sin más a la distribución** (R8) ni al controlador.
  Afecta sobre todo a los destinos que se abordan de frente, que hoy es solo `ETM10`. Mientras no
  se iguale el sensor —decisión abierta y ligada a la del número de muestras—, las dos condiciones
  se reportan por separado, como ya exige el punto anterior sobre Humble y Jazzy.
- **Una de las cuatro métricas de OE4 no la resuelve el instrumento.** El tiempo de asignación es
  ~10³ veces más corto que el tick de `/clock` (§3.2.1), así que en la campaña solo se puede acotar,
  no medir. La cifra sale de un banco aparte, sobre reloj de pared y **sin la simulación corriendo**:
  no es la misma condición experimental que el resto de las métricas y no debe presentarse junto a
  ellas como si lo fuera. En particular, el banco no incluye la contención de CPU de dos Gazebo, que
  es justo lo que podría alargar una asignación en la campaña real.
- **El operador conoce la hipótesis.** Las corridas son automáticas de principio a fin
  precisamente por eso: el sorteo con semilla y el registro sin intervención manual (RF-25) quitan
  al operador toda decisión durante la medida.

---

## 12. Trazabilidad

| Este protocolo fija | Requisito | Objetivo |
|---|---|---|
| §3.1 tiempo de respuesta | RF-21 | OE4 |
| §3.2 tiempo de asignación | RF-22 | OE4 |
| §3.3 criterio de éxito | RF-23 | OE4 |
| §3.4 continuidad entre niveles | RF-24 | OE4 — **variable principal** |
| §9.4 registro estructurado | RF-25 | OE4 |
| §6.1 N = 30 en simulación | RF-26 | OE4 |
| §6.1 N = 5–10 en hardware | RF-27 | OE4 |
| §3.4 constancia de `z` | RNF-01 | restricción de alcance |
| §5 RTF ≥ 0,99 | RNF-06 | validez de las métricas temporales |
| §4 sin giro sobre el eje | RNF-05 | restricción de alcance |

**Decisiones tomadas el 2026-08-22**, cuando se escribió este documento y antes de instrumentar:
el rumbo no decide el éxito y `stateful` pasa a `False` (§4); una corrida fallida cuenta como fallo
salvo causa externa de la lista cerrada (§8).
