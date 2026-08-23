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

- **`t_robot_activo`**: primer mensaje en `/coordinacion/estado_mision` con `etapa = TRAMO_1` y
  `robot_activo` no vacío.

Se espera que sea mucho menor que el tiempo de respuesta, porque asignar es una decisión de
escritorio del coordinador y moverse no. **Si sale del mismo orden, es un hallazgo**, no un error de
medida: significaría que el coordinador está esperando algo.

> `estado_mision` se publica a 1 Hz, así que esta métrica tiene una **resolución de 1 s** y eso es
> demasiado grosero para un evento que se espera en milisegundos. La instrumentación debe publicar
> un mensaje **extraordinario** en el instante del cambio de etapa, además del periódico. Queda
> anotado aquí porque es un requisito sobre el coordinador que sale del protocolo, no al revés.

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

Los 0,25 m son la `xy_goal_tolerance` configurada en Nav2. Se usa el mismo número a propósito: el
criterio de éxito es «el sistema hizo lo que se le pidió con la precisión que declara tener».

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
| `xy_goal_tolerance` | 0,25 m | `nav2_params_nav_amcl_sim_demo.yaml` |
| `yaw_goal_tolerance` | 0,25 rad (14,32°) | ídem |
| `stateful` | **False** (hoy `True`, ver §4) | ídem |
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

> Esa herramienta **todavía no existe**; es parte de la instrumentación (§9). Se nombra aquí para
> fijar que el sorteo es del protocolo y no del operador: elegir los pares a mano el día de la
> campaña es la puerta de entrada al sesgo de selección.

El listado sorteado se versiona **antes** de ejecutar la primera corrida. El orden de ejecución es
el del archivo, sin reordenar.

### 6.4 Aislamiento entre corridas

**Cada corrida arranca con un `gzserver` nuevo.** No se encadenan misiones sobre la misma
simulación: la carrera conocida al cargar controladores y la corrupción del daemon de ROS 2 dejan
estado que se arrastra, y un arrastre sistemático es exactamente lo que una campaña no puede tener.

El procedimiento de limpieza es el de la [guía de ejecución](GUIA_EJECUCION.md) §0.

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

En orden. Nada de esto existe hoy.

1. **`stateful: False`** en el YAML, y **repetir los tres destinos del 21-ago** comparando el número
   de cúspides contra el registro de aquella corrida. Sin esa comparación el cambio es una creencia.
2. **Paquete `coordinacion_msgs`** con sus cuatro definiciones
   ([`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md) §5). Sin él no hay `estado_mision`, y sin
   `estado_mision` no hay RF-22 ni RF-24.
3. **Nodo de coordinación** que sirva `/coordinacion/guiar_usuario` y publique `estado_mision`,
   incluida la marca extraordinaria de cambio de etapa (§3.2).
4. **Registrador de misión** (RF-25): un archivo por misión, estructurado, con todas las marcas
   temporales, la traza de `/odom` de cada robot y el RTF. Procesable sin intervención manual.
5. **`herramientas/sortear_misiones.py`** (§6.3).
6. **Analizador de campaña**: lee los N registros y produce las cuatro métricas con sus intervalos
   de confianza.

---

## 10. Prerrequisitos que hoy NO se cumplen

**La campaña no puede empezar mientras alguno siga abierto.** Se listan porque un protocolo que
calla sus condiciones previas se ejecuta igual y produce números que no valen.

| Prerrequisito | Estado al 2026-08-22 |
|---|---|
| **`/odom` cruzado** — una lectura devolvió la posición del otro agente | 🔴 ABIERTO. Las cuatro métricas salen de odometría; con esto abierto, ninguna es fiable. Entretanto, leer con `--no-daemon` |
| **Carrera al cargar controladores** — un controlador puede quedar `unconfigured` | 🔴 ABIERTA. Hoy es causa de descarte (§8); si es frecuente, se come la cuota del 20 % |
| **Mapa del piso 2** | 🟢 CERRADO el 2026-08-23. `maps/mundo_definitivo_piso2.{pgm,yaml}`, generado contra `mundo_definitivo_piso2.world` y `ACEPTADO`: 0 de 6096 obstáculos sin pared real, 0,1 % de celdas desconocidas dentro de sus cinco regiones |
| **Destinos del piso 2 en `puntos_interes.yaml`** | 🔴 Los 18 vanos están detectados pero sin nombrar. Ver la sección PISO 2 de [`mapa_destinos.txt`](mapa_destinos.txt) |
| **Los dos agentes navegando simultáneamente** (H3) | 🔴 Arrastre de S19 a S20 |
| **Segundo vehículo físico** (R11) | 🔴 Administrativo. Bloquea solo la campaña física (RF-27), no la de simulación |

**La condición A se puede pilotar en cuanto se cierren los dos primeros.** A la condición B ya solo
le faltan los **nombres** del piso 2: el mapa se cerró el 23-ago.

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
