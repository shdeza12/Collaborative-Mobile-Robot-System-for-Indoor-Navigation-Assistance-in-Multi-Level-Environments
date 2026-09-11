# Requisitos del sistema — matriz RF ↔ OE ↔ prueba

**Semana 19 · 2026-08-18.** Cierra el riesgo **R5** de [`../ESTADO.md`](../ESTADO.md) §4.

Documento normativo. Cada requisito tiene un número, un objetivo específico al que responde y
**una prueba que lo declara cumplido o no**. Un requisito sin prueba no es un requisito: es una
intención.

---

## 0. Por qué este documento se escribe en S19 y no en S3

**El anteproyecto nunca enumeró los requisitos.** Su §7.4 exige dos cosas que no se pueden hacer
sin ellos:

> *«Comparación con requisitos: validar que cada especificación inicial se cumpla.»*
> *«Verificación de la implementación: verificar que el sistema cumpla los requerimientos técnicos
> establecidos.»*

No existe en el documento ninguna lista de especificaciones iniciales ni de requerimientos
técnicos. La Fase 2 del cronograma (S9–S11) contemplaba la actividad de análisis, pero no produjo
un artefacto enumerado.

**Esto no es una recuperación, es una reconstrucción**, y se declara como tal. Los requisitos de
abajo se derivan de tres fuentes, todas ellas anteriores a este documento y citables:

| Fuente | Qué aporta |
|---|---|
| Anteproyecto §4.2 — objetivos específicos | Qué debe hacer el sistema |
| Anteproyecto §4.3 — alcance | Qué **no** debe hacer, y bajo qué condiciones opera |
| [`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md) | Cómo se expresa cada capacidad en interfaces concretas |

Ningún requisito se inventa. Cada uno cita de dónde sale. Si un requisito no se puede rastrear a
una de esas tres fuentes, sobra y se elimina.

---

## 1. Cómo leer las tablas

- **RF** = requisito funcional (qué hace el sistema). **RNF** = requisito no funcional o
  restricción (condiciones y límites que el alcance impone).
- **Prueba:** cómo se demuestra. Se prefiere una comprobación ejecutable a una afirmación. Cuando
  ya existe la herramienta, se nombra.
- **Estado:** ✅ verificado · 🟡 parcial · 🔴 pendiente.
- **Semana:** en qué semana se construye lo que falta. Es lo que convierte esta matriz en la
  especificación de S20–S22 y no en un trámite.

---

## 2. OE1 — Arquitectura funcional

> *«Modelar la arquitectura funcional del sistema colaborativo de dos robots móviles, definiendo
> requerimientos, escenarios de operación con múltiples pisos, estrategia de asignación de tareas
> y esquema de comunicación inter-robot.»*

| ID | Requisito | Prueba | Estado | Semana |
|---|---|---|---|---|
| **RF-01** | El sistema opera con **exactamente dos agentes**, cada uno dedicado a un nivel | Inventario de nodos: dos pilas completas, una por agente | ✅ **S18, re-anclado el 2026-09-05.** La prueba original decía «por dominio» y esa arquitectura ya no existe: el 30-ago se eligió la **opción B —un dominio, dos `gzserver`, separación por espacios de nombres**— ([`S21_bloqueo_dominios.md`](Evidencia/S21_bloqueo_dominios.md) §3). El requisito se sostiene igual y con más datos: las 30 misiones de la campaña corrieron con las dos pilas vivas en un solo grafo | S18 |
| **RF-02** | Cada agente es **direccionable de forma independiente**: una orden a uno no altera al otro | `ros2 topic list --no-daemon --spin-time 8`: ningún tópico cruzado entre espacios de nombres. Ordenar a robot1 y leer `/robot2/odom` | ✅ **S18, re-anclado el 2026-09-05.** Misma corrección que RF-01: la separación ya no la da el `ROS_DOMAIN_ID` sino el prefijo `/robotN`. La evidencia fuerte es la campaña: sobre las trazas de las **15 misiones de condición B** —las únicas donde los dos agentes aparecen— no hay **ni un solo instante** con los dos por encima de 0,05 m/s. Se mueven en relevo, nunca a la vez, que es justo lo que no pasaría si una orden alcanzara a los dos | S18 |
| **RF-03** | El coordinador manda a un agente **únicamente** mediante la acción `navigate_to_pose` | Inspección de suscriptores de `/robotN/cmd_vel`: ningún publicador fuera de la pila del propio agente | ✅ | S18 |
| **RF-04** | El sistema conoce un **conjunto de localizaciones de interés**, cada una con nivel y pose | Existe `puntos_interes.yaml`; el coordinador lo republica *latched* y `ros2 topic echo` lo devuelve completo | 🟢 **Verificado el 2026-09-02 y confirmado sobre la campaña.** La HRI cargó los **31 puntos** del catálogo real desde `/coordinacion/puntos_interes` con QoS `transient_local` —que es la forma ROS 2 de *latched*—, o sea que un suscriptor tardío lo recibe completo. Y las **30** misiones de la campaña llevan `procedencia.catalogo_sha256 = 849ecee96258…`, idéntico al `sha256` del `puntos_interes.yaml` versionado: no es que el coordinador conociera *un* catálogo, es que conoció **este**, byte a byte | S20 |
| **RF-05** | El coordinador **asigna la misión al agente del nivel de origen** (asignación dinámica de tareas) | Una solicitud con origen en el nivel 1 activa a robot1 y no a robot2; y a la inversa | 🟢 **Verificado el 2026-08-29 y ejercitado 30 veces.** Dos solicitudes con destino en niveles distintos produjeron **dos agentes distintos** ([`S20_asignacion_por_nivel.md`](Evidencia/S20_asignacion_por_nivel.md)), que es lo que separa «eligió bien» de «siempre responde lo mismo». En la campaña, las **15 misiones intra-nivel** —donde origen y destino coinciden y la prueba es directa— asignaron el agente de ese nivel sin excepción: 8 de 1→1 a robot1 y 7 de 2→2 a robot2. En las 15 entre niveles el agente del nivel de destino cierra la misión y hubo relevo, lo que implica que el primer tramo lo llevó el otro | S20 |
| **RF-06** | Si origen y destino están en el **mismo nivel**, la misión se resuelve con **un solo agente y cero relevos**, sin ramas especiales en la HRI | `result.num_relevos == 0` y el segundo agente permanece en estado `LIBRE` | 🟢 **Verificado sobre las 15 misiones de condición A de la campaña (2026-09-04/05).** Las 15 tienen `t_fin_tramo1` y `t_inicio_tramo2` en `null`: no hubo etapa de transferencia, luego no hubo relevo. La HRI no tiene rama por condición —lanza la misión igual y el coordinador decide—, verificado al inspeccionar `interfaz_web/` para RF-19. **Salvedad declarada:** el registro **no guarda un campo `num_relevos`**, así que lo probado es «no ocurrió transferencia», no la igualdad literal `num_relevos == 0`; y `estado: LIBRE` del segundo agente **no se comprobó sobre la campaña**, porque `/<ns>/estado` no existía cuando se corrió. Desde el 2026-09-07 el tópico existe y publica `LIBRE` (ver RF-08), pero eso es una capacidad nueva, no una relectura de las 15 misiones: **la campaña no se vuelve a correr** (S22 es semana de integración, no de medición). La comprobación directa entra con la corrida de extremo a extremo del miércoles 9 | S20 |
| **RF-07** | Si origen y destino están en **niveles distintos**, se ejecuta el **protocolo de relevo**: guiado al punto de transferencia, publicación del relevo, activación del segundo agente, reanudación | Una misión entre niveles recorre las etapas `TRAMO_1 → TRANSFERENCIA → TRAMO_2 → COMPLETADA` y `result.num_relevos == 1` | 🟢 **Ejecutado el 2026-08-30 y medido 15 veces el 2026-09-04/05. Es el aporte declarado del proyecto y ya no es n = 1.** Las **15 misiones de condición B** de la campaña sorteada tienen las cuatro marcas de tramo pobladas y `veredicto.c3_relevo: true`, que el compositor calcula como `num_relevos == 1` —ni cero ni dos—. De ellas, **14 aciertos (93,3 %)** y **continuidad entre niveles 14/14 (100 %)**, con salto de relevo de mediana **0,100 s**, un solo tic de `/clock`. La 15.ª (misión 27) falló por llegada corta, no por el relevo. Primera ejecución con los dos robots vivos en [`S21_relevo_ejecutado.md`](Evidencia/S21_relevo_ejecutado.md) | **S21** |
| **RF-08** | Cada agente **publica su estado** (nivel, pose, situación) a 2 Hz | `ros2 topic hz /robotN/estado` devuelve 2 Hz y el campo `estado` cambia al iniciar una misión | 🟢 **Verificado el 2026-09-07.** El nodo `coordinacion/agente` publica `/robot1/estado` a **2,000 Hz** (mín. 0,499 s, máx. 0,502 s, desviación típica 0,00057 s). Y el campo cambia en los dos sentidos, inyectando un `GoalStatusArray` real por DDS: sin meta → `0 LIBRE`; `EJECUTANDO` → **`1 NAVEGANDO`**; `EXITOSA` → `0 LIBRE`; `ABORTADA` → **`3 ERROR`**. Medida en [`logs/S22_RF08_estado_2hz.txt`](Evidencia/logs/S22_RF08_estado_2hz.txt). **El estado no se copia de `/coordinacion/estado_mision`** —eso sería el coordinador dándose la razón a sí mismo y dejaría sin valor la prueba de RF-06— sino que se deduce del *status* de la propia acción `navigate_to_pose`, que publica Nav2 en el robot. Prueba fuera de línea `prueba_agente.py`, **39/39**, validada mutando el código: tres mutaciones, tres detecciones. **Dos salvedades declaradas**, ninguna afecta al criterio de aceptación: (a) el campo `pose` se midió sin simulador, luego sin TF —el nodo lo declara en `detalle` en vez de mandar ceros callando—, y queda por comprobar contra la simulación viva; (b) `EN_TRANSFERENCIA` está implementado y probado en la máquina de estado pero **no cableado**: ningún tópico alimenta `declarar_relevo()`, porque el robot no puede saber por sí solo si su meta es un punto de relevo o el destino final. Requiere una fila nueva en `CONTRATO_INTERFACES.md` §4 y se decide con el relevo integrado | **S22** |
| **RF-09** | El entorno de operación tiene **dos niveles con un punto de transición vertical** | El mundo carga los dos niveles; se navega en el superior con la altura constante | ✅ | S18 |
| **RF-10** | La **comunicación inter-robot** ocurre a través del coordinador, no directamente entre agentes | Ningún agente se suscribe a tópicos del otro (se sigue de RF-02) | ✅ | S18 |

**Lectura de OE1, reescrita el 2026-09-07.** De diez requisitos, **los diez están verificados**.
RF-08 era el último y se cerró el lunes 7 de septiembre; **RF-07 —el aporte declarado del proyecto—
pasó de 🔴 a 🟢 con quince repeticiones sorteadas**, no con una demostración. OE1 queda cerrado
como objetivo, con las dos salvedades de RF-08 anotadas en su celda: la `pose` contra simulador
vivo y el cableado de `EN_TRANSFERENCIA`. Ninguna de las dos afecta a un criterio de aceptación
escrito, y las dos se resuelven en la integración del miércoles 9.

*Esta tabla llevaba a RF-04, RF-05, RF-06 y RF-07 en 🔴 mientras el resto del repositorio los daba
por ejecutados desde el 29 y el 30 de agosto. La contradicción se detectó al preparar el balance de
objetivos del 5 de septiembre y se resolvió **contra los treinta registros de la campaña**, no
contra lo que decía [`ESTADO.md`](../ESTADO.md): el `sha256` del catálogo, las marcas de tramo y el
agente de cada misión salen de los archivos JSON versionados. La lección operativa es que cuando se
actualiza el estado de un objetivo hay que revisar las tablas de **todos** los objetivos que la
misma evidencia toca: la campaña de OE4 ejercitó de paso cuatro requisitos de OE1.*

**Lo que RF-08 desbloqueó, y lo que no.** Bloqueaba la mitad de la prueba de RF-06 —el segundo
agente debe permanecer en `LIBRE`, y eso no se podía leer: la misión se sabía entera, el robot no
se sabía—. Desde el 2026-09-07 se lee. Pero conviene no estirarlo: **las 15 misiones de la campaña
no se releen**, porque el tópico no existía cuando se corrieron y la campaña no se repite. Lo que
hay es la capacidad, verificada aislada; la comprobación sobre una misión real entra el miércoles 9.

**Y una decisión de diseño que conviene poder defender.** El estado podría haberse copiado de
`/coordinacion/estado_mision`, que ya existía y habría costado media hora menos. No se hizo porque
entonces «el segundo agente permanece `LIBRE`» sería el coordinador afirmando algo sobre el robot a
partir de lo que el propio coordinador decidió: un eco, no una medida. El estado se deduce del
*status* de la acción `navigate_to_pose` del propio robot, que publica su Nav2. La prueba
`prueba_agente.py` fija esa decisión por escrito y falla si alguien la deshace.

**Qué algoritmo de coordinación implementan RF-05 y RF-07** está clasificado formalmente en
[`ANEXO_ALGORITMO_COORDINACION.md`](ANEXO_ALGORITMO_COORDINACION.md): la asignación es ST–SR–IA
en la taxonomía de Gerkey y Matarić (2004) y coincide con el óptimo del método húngaro porque
la restricción de nivel deja un solo candidato admisible por tarea; el relevo, en cambio, tiene
dependencias entre agendas y cae en la categoría XD de la taxonomía de Korsah, Stentz y Dias
(2013). El anexo incluye las alternativas descartadas y por qué.

---

## 3. OE2 — Plataforma robótica

> *«Desarrollar una plataforma robótica móvil basada en dos vehículos […], integrando los módulos
> de locomoción, sensado, procesamiento y comunicación necesarios para la operación colaborativa
> en entornos interiores.»*

| ID | Requisito | Prueba | Estado | Semana |
|---|---|---|---|---|
| **RF-11** | Cada vehículo ejecuta **locomoción** comandada por `/<ns>/cmd_vel`, con cinemática Ackermann | El vehículo se desplaza; recorrido medido contra `/odom` | 🟡 sim ✅ / **físico parcial, y ya no «vía web»** (revisado el 2026-09-05). El 2026-08-28 el vehículo se desplazó **mandado desde ROS 2, sin la interfaz del fabricante** ([`S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md) §6), de ida y vuelta tres veces sobre una recta de 3,000 m. **Lo que falta son las dos mitades de la prueba tal como está escrita:** el mando fue `ServoCtrlMsg` en `/ctrl_pkg/servo_msg`, **no `/<ns>/cmd_vel`** —eso es RF-14, y su pendiente es de escala—, y el recorrido se leyó de `map → base_link`, **no de `/odom`** —eso es RF-13— | S19–S21 |
| **RF-12** | Cada vehículo publica **`/<ns>/scan`** utilizable para localización y evasión | El LiDAR publica a su frecuencia nominal y el mapa de costos local registra los obstáculos | 🟡 sim ✅ / **físico: primera mitad verificada, segunda mitad pendiente** (revisado el 2026-09-05, estaba en 🔴 sin serlo). El LiDAR real publica un `/scan` **utilizable y medido contra referencia externa**: RANSAC secuencial —que nunca recibe la distancia esperada— sitúa la pared en **1,0228 m** contra 1,000 m de flexómetro, en **10 de 10 barridos**, con **2,8 mm** de dispersión y residuos de 2–11 mm ([`S19_spike_p1_p2_hardware.md`](Evidencia/S19_spike_p1_p2_hardware.md) §1.3). Y desde el 28-ago **convive con la pila completa del vehículo**, a **6,35 Hz** frente a 6,80 Hz aislado, −6,6 %. **Falta la segunda mitad —el mapa de costos local— porque Nav2 no se ha ejecutado nunca sobre el carro**, y ahí el bloqueo quedó **medido, no supuesto, el 2026-09-08**: la tarjeta **no publica ningún árbol TF** —`/tf` y `/tf_static` responden «does not appear to be published yet», y entre los 9 nodos de `deepracer-core` no hay `robot_state_publisher`— ni `/odom` (eso es RF-13). Sin TF no hay mapa de costos posible, así que la segunda mitad no está esperando esfuerzo de Nav2 sino la cadena de RF-13. **El espacio de nombres: resuelto en el lanzador el 2026-09-08, sin verificar todavía sobre el vehículo.** `lidar_vehiculo.launch.py` acepta `namespace:=robotN` y publica en `/<ns>/scan` prefijando **también el marco TF** a `<ns>/laser` —dejarlo en `laser` daría separación aparente con los dos árboles pisándose, que es el fallo que costó una misión el 2026-08-24—; el defecto sin argumento no cambia y sigue siendo `/scan`. Comprobado fuera de línea por [`prueba_namespace_lidar.py`](../herramientas/prueba_namespace_lidar.py), que ejercita el lanzador de verdad sobre un `LaunchContext` en vez de reimplementar su lógica, **validada mutando el código: tres mutaciones, tres detecciones**. **Lo que no se ha hecho, y por qué:** sobre el vehículo el tópico **sigue siendo `/rplidar_ros/scan`**, porque `deepracer-core` arranca el sensor por su cuenta y el PID 713 tiene tomado `/dev/ttyUSB0`; ejercitarlo exige rearrancar el servicio con `rplidar:=False`, sobre hardware compartido. **Divergencia anotada el 2026-09-08:** en la tarjeta hay un enlace `rplidar_node -> rplidar_composition` en `/opt/ros/jazzy/lib/rplidar_ros/` con fecha 28-ago, que es exactamente la **opción A** que el propio lanzador documenta haber descartado —modifica ficheros del sistema y no sobrevive a una actualización de AWS—. **Riesgo anotado para S26:** el URDF simulado declara 300°, 600 muestras y 10 m donde el sensor real da **360°, 1328 muestras y 16 m**; comparar simulación contra hardware sin alinearlo mediría la diferencia de modelos además de la del entorno | **S19** (spike, pregunta 1) |
| **RF-13** | Cada vehículo publica **odometría** en `/<ns>/odom` | Lectura antes y después de un desplazamiento conocido | 🟡 sim ✅ **contra un oráculo**, no verificado (ver §7.4) / **físico: el desplazamiento conocido ya se midió, pero no sobre `/odom`** (revisado el 2026-09-05; la celda decía «se mide en la corrida de ≥ 20 m de S20» y esa corrida ya ocurrió). El 2026-08-28 se recorrió una recta de **3,000 m** de flexómetro con cinco estimaciones —media **3,088 m**, σ 0,025 m, **error sistemático de +2,9 %**— y una deriva de cierre de **0,18 % sobre ~18,4 m**. Dos cosas hay que decir enteras: **(a)** la lectura salió de `map → base_link`, o sea de la **odometría láser**, no del `/<ns>/odom` que el requisito nombra; **(b)** el +2,9 % tiene **dos causas sin discriminar** —escala del sensor o colocación del vehículo en cada extremo— y hay una prueba definida que las separa: medir un tramo de pared con flexómetro y contra el `.pgm` del mapa. La deriva de cierre **no** desmiente el 2,9 %: un error de escala se cancela al volver | S19 |
| **RF-14** | Cada vehículo se comanda **desde ROS 2**, sin pasar por la interfaz web del fabricante | Publicar en `/<ns>/cmd_vel` desde otra máquina de la red mueve el vehículo | 🟡 **El requisito se cumple; la prueba tal como está escrita, no —y por dos razones distintas—.** *Cumplido:* el 2026-08-28 el vehículo se condujo desde ROS 2 sin la interfaz web ([`S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md) §6), publicando `ServoCtrlMsg` en `/ctrl_pkg/servo_msg`, con hombre muerto de 0,6 s. *Lo que falta, (a) por calibrar:* eso es un **puente**, no la cadena `/cmd_vel`. Sus dos defectos **sí están corregidos** desde `f0fa40c` (2026-08-27) —tópico de publicación absoluto y ramas de tracción ordenadas de umbral mayor a menor— con 19 comprobaciones en `prueba_mapeo_servo.py`; pero la propia prueba deja escrito que **el escalón más bajo cae en 0,40 m/s** mientras Nav2 pide 0,25 en curva y 0,05 en la aproximación, así que **la cadena sigue devolviendo cero justo donde Nav2 la usa**. Es un problema de **escala**, no de mapeo, y la cadena **nunca se ha ejercitado sobre el vehículo**. *(b) por decidir:* la cláusula «desde otra máquina de la red» **choca con una decisión de seguridad documentada** —§6.3 de la misma evidencia: el teleoperador corre *en* el vehículo a propósito, porque si el wifi cae, `servo_pkg` se queda con el último valor y queda un vehículo acelerando sin nadie al mando—. No se reescribe la prueba para que pase: eso es una decisión de protocolo, igual que la del §5.4 de esa evidencia | **S19** (spike, pregunta 2) |
| **RF-15** | Los dos vehículos y el coordinador se **alcanzan por red** con latencia acotada | Medida de ida y vuelta entre los dos vehículos | 🔴 bloqueado por **R11** | S19+ |
| **RF-16** | El **mismo código fuente** se despliega en los dos destinos, simulado y físico (decisión D6) | Compilar el coordinador sin cambios en las dos distribuciones y completar una misión **en cada mundo por separado** | 🟡 **verificado con resultado condicionado** (2026-08-18) | S22 |
| ~~RF-16b~~ | ~~Una misión con robot1 **simulado** y robot2 **físico** a la vez~~ | ~~Misión mixta completada sin recompilar~~ | ❌ **imposible sin trabajo nuevo** (2026-08-18) | — |

**Lectura de OE2, reescrita el 2026-09-05.** El cuello de botella sigue siendo el acceso al
hardware, pero **estaba peor descrito que la realidad**. Al revisar las cinco celdas contra las
evidencias del 19 y el 28 de agosto —no contra la bitácora— resulta que **de un solo vehículo ya
se sacó más de lo que la tabla reconocía**: RF-12 tenía el LiDAR real medido contra flexómetro y
conviviendo con la pila, y aparecía en 🔴; RF-13 tenía la corrida de desplazamiento conocido hecha,
y la celda seguía anunciándola como futura; RF-11 decía «vía web» cuando el carro se conduce desde
ROS 2 desde el 28-ago. **Lo que de verdad falta en OE2 son tres cosas concretas y ninguna es un
misterio:** el mapa de costos local sobre el carro (RF-12, exige Nav2 a bordo), la lectura sobre
`/<ns>/odom` en vez de `map → base_link` (RF-13), y la escala de la cadena `/cmd_vel` (RF-14).
**Solo RF-15 exige los dos vehículos y solo él está bloqueado por R11.**

*Revisión del 2026-09-05 sobre RF-14.* Pasa de 🔴 a 🟡 tras comprobarlo en el código y no en la
bitácora. **Dos afirmaciones que este repositorio venía repitiendo eran falsas:** que la cadena
`/cmd_vel` «sigue con sus dos defectos» —están corregidos desde el 27-ago, con prueba— y, por el
otro lado, la tentación simétrica de darla por buena, porque `prueba_mapeo_servo.py` deja escrito
que **el escalón más bajo cae en 0,40 m/s y Nav2 pide 0,25 y 0,05**. O sea: el mapeo está
arreglado y la **escala** no, y eso es calibración contra el vehículo, que sigue sin hacerse.
**Lo que esto cambia en el plan:** RF-14 **no** está bloqueado por R11 —le basta el vehículo que sí
está disponible—, así que es trabajo ejecutable en S22–S23 y no una espera. Su parte irreducible no
es técnica sino de protocolo: decidir si la prueba se reescribe sin la cláusula «desde otra máquina
de la red», que contradice la decisión de seguridad del §6.3 de
[`S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md).

**RF-16 era el requisito de mayor riesgo del proyecto** —la simulación corre sobre ROS 2 Humble y
las dos unidades de cómputo de los vehículos sobre Jazzy— y **se midió el 2026-08-18** con la
pregunta 4 del spike, sin encender hardware:
[`Evidencia/S19_spike_p4_humble_jazzy.md`](Evidencia/S19_spike_p4_humble_jazzy.md).

Resultado en una línea: **el código fuente sí es portable; la configuración no, y los dos mundos no
pueden mezclarse.** El desajuste de configuración está acotado —6 diferencias, 37 líneas de YAML y
2 árboles de comportamiento que convertir de BT.CPP v3 a v4—, pero la acción
`nav2_msgs/NavigateToPose`, que es **la única vía de mando que fija el contrato de interfaces**,
tiene distinta definición en las dos distribuciones. Por eso RF-16 se reescribió en términos de
código fuente y la parte que sí se cayó quedó tachada arriba como RF-16b, en vez de borrarla: un
requisito que se descubre imposible es información, y borrarlo la pierde.

**Consecuencia sobre el plan de contingencia:** el tercer escalón de la escalera de recortes (§8)
proponía justamente esa misión mixta. Ya no es una salida.

---

## 4. OE3 — Interfaz humano–robot

> *«Programar una interfaz móvil para interacción humano-robot (HRI) basada en la selección de
> localizaciones de interés de origen-destino.»*

| ID | Requisito | Prueba | Estado | Semana |
|---|---|---|---|---|
| **RF-17** | La HRI permite **seleccionar un origen y un destino** de entre las localizaciones de interés | Dos listas pobladas desde `/coordinacion/puntos_interes`; la selección lanza una misión | 🟢 **Verificado el 2026-09-02.** Catálogo real de 31 puntos cargado con QoS `transient_local` explícito; seleccionar origen y destino y pulsar "Iniciar guiado" llama `/coordinacion/guiar_usuario` y el coordinador procesa la misión (`interfaz_web/`, rama `interfaz-hri-web`) | S22 |
| **RF-18** | La HRI **muestra el estado de la misión** al usuario en texto legible | El campo `mensaje_usuario` se muestra literal y cambia en cada etapa | 🟢 **Verificado el 2026-09-02.** El panel se repinta en cada mensaje de `/coordinacion/estado_mision` (1 Hz) y muestra `mensaje_usuario` sin reescribirlo; probado hasta el ciclo RECIBIDA→TRAMO_1→FALLIDA con el motivo real del coordinador | S22 |
| **RF-19** | La HRI se comunica **solo con `/coordinacion`**, nunca con los agentes | Inspección de la superficie expuesta por `rosbridge`: ningún tópico `/robotN/*` | 🟢 **Verificado el 2026-09-02.** El código de `interfaz_web/` no referencia ningún tópico `/robotN/*`; solo suscribe `/coordinacion/puntos_interes` y `/coordinacion/estado_mision`, y llama `/coordinacion/guiar_usuario` | S22 |
| **RF-20** | La HRI es accesible desde el **navegador de un teléfono**, sin instalación | Carga y operación completa desde un móvil en la misma red | 🟢 **Verificado el 2026-09-10** en un teléfono real, SSID `DEEPRACER`, y con las dos mitades del criterio: **carga** (la página se sirvió y el led se puso verde, o sea WebSocket establecido contra `rosbridge`, no solo HTML entregado) y **operación** —desde el móvil se eligió `piso1_etm2` → `piso2_aula_302` y la misión se completó con relevo—. Sin dependencias externas ni CDN. La evidencia no es la pantalla sino el registro validado [`S22_RF20_telefono_C_02.json`](Evidencia/registros/S22_RF20_telefono_C_02.json): veredicto `exito: true`, `c3_relevo: true`, RTF 0,9949. Hizo falta abrir 8000 y 9090 en `ufw` acotados a la subred ([`RUNBOOK_CAMPANA.md`](RUNBOOK_CAMPANA.md) §4.1) | S22 |
| **RF-28** | En una misión entre niveles, el tramo del piso de destino **no inicia hasta que el usuario confirma** el cambio de piso desde la interfaz. Se avisa a los 60 s y la misión falla a los 120 s sin confirmación | Registro de una misión B con marcas de `ESPERANDO_CONFIRMACION`, más las tres corridas del §7 de [`DISENO_CONFIRMACION_PISO.md`](DISENO_CONFIRMACION_PISO.md) | 🔴 | S22 |

**Lectura de OE3 al 2026-09-02.** La interfaz se adelantó del S22 (7–13 sep) al final de S21: los
cuatro requisitos tienen implementación, y tres están verificados contra un `coordinador` real (sin
robots ni Gazebo corriendo). Sigue pendiente el criterio de cierre completo de S22 — guiado con
relevo en simulación, de punta a punta, desde un teléfono real — porque eso exige los dos agentes
vivos. Ver la bitácora del 2026-09-02 en [`ESTADO.md`](../ESTADO.md).

**RF-17 es el núcleo de OE3 y se cumple íntegro con dos listas desplegables.** El anteproyecto
pide selección de origen y destino, no representación gráfica del entorno. Conviene tenerlo
presente antes de invertir tiempo en un mapa interactivo.

---

## 5. OE4 — Evaluación experimental

> *«Evaluar el desempeño del sistema mediante pruebas experimentales en un entorno interior
> controlado, utilizando métricas como tiempo de respuesta, tiempo de asignación de robot, tasa de
> éxito en la entrega de asistencia y continuidad del servicio entre niveles.»*

| ID | Requisito | Prueba | Estado | Semana |
|---|---|---|---|---|
| **RF-21** | El sistema registra el **tiempo de respuesta**: desde la solicitud hasta que el agente inicia el movimiento | El registro de la misión contiene la marca temporal de ambos eventos | 🟢 **Verificado el 2026-08-27 y medido 30 veces el 2026-09-04/05** (la celda citaba `S20_rutas_03`, n = 1). Las **30** misiones traen `t_solicitud` y `t_primer_movimiento` pobladas: **mediana 0,2 s, rango 0,1–0,4 s**. Con el matiz de instrumento dicho de una vez: los sellos del bag van cuantizados a **100 ms** por `/clock`, así que una mediana de 0,2 s son **dos tics** y la cifra no admite más de un decimal. A diferencia de RF-22, aquí la métrica **sí** queda por encima del suelo del instrumento | S20 |
| **RF-22** | El sistema registra el **tiempo de asignación de robot**: desde la solicitud hasta que un agente queda asignado | Sobre el bag la resta vale cero por construcción; la cifra sale del **banco aislado** de [`herramientas/banco_tiempo_asignacion.py`](../herramientas/banco_tiempo_asignacion.py), con `perf_counter_ns()` dentro del proceso del coordinador | 🟢 **Verificado, pero no por donde decía esta celda** (revisado el 2026-09-05). Decía «`t_solicitud` y `t_robot_activo` en el mismo registro», y esa resta vale **exactamente 0,0 s en 30 de las 30 misiones** de la campaña —comprobado—, se ejecute lo que se ejecute: `ros2 bag record --use-sim-time` sella con `/clock`, que `gazebo_ros_init` publica a 10 Hz, luego **todo sello está cuantizado a 100 ms**, y asignar son ~150 µs. Eso no mide el evento, **mide el reloj**, y una prueba que se satisface con un cero no es una prueba. La cifra real viene del banco del 2026-08-30 ([`S21_banco_tiempo_asignacion.md`](Evidencia/S21_banco_tiempo_asignacion.md)): **4 corridas sorteadas de n = 30**, mediana entre **154,3 y 175,3 µs** y máximo **306,4 µs** —**326 veces menor que un tic de `/clock`**—, alternando intra e inter-nivel para ejercitar las dos ramas de `planificar()`. **Conviene no confundir esto con el defecto de software que sí hubo:** hasta el 29-ago el coordinador fijaba `etapa` y `robot_activo` en la misma publicación y no existía marca intermedia; se corrigió con la etapa `RECIBIDA`, y fue necesario pero no suficiente | S20 |
| **RF-23** | El sistema registra el **éxito o fallo** de cada misión, con el motivo | `result.exito` y `result.motivo_fallo` quedan en el registro | 🟢 **Verificado sobre las 30 misiones de la campaña (2026-09-04/05).** Cada registro trae su veredicto calculado contra `/odom`, no contra el `SUCCEEDED` de Nav2: **26 aciertos de 30 (86,7 %)**, IC95 de Wilson **70,3–94,7 %**. Los 4 fallos quedan con su motivo y son **un solo modo** —error de llegada de 0,284 a 0,347 m contra un criterio de 0,25 m—, o sea inobservabilidad longitudinal del pasillo, **no fallo de coordinación** | S21 |
| **RF-24** | El sistema registra la **continuidad del servicio entre niveles**: que la misión atraviesa el relevo sin interrupción del guiado | Ninguna etapa queda sin agente activo entre `TRAMO_1` y `TRAMO_2` | 🟢 **Verificado el 2026-09-05: 14 de 14 (100 %)**, IC95 **78,5–100 %**, con salto de relevo de mediana **0,100 s** —un tic de `/clock`, o sea el suelo del instrumento—. Evalúa 14 y no 15 misiones entre niveles porque la 27 nunca llegó a `COMPLETADA`: medir continuidad sobre una misión fallida sería medir otra cosa. **Es la variable de respuesta principal del proyecto** y no tenía campo en el registro hasta el esquema 1.1.0 (31-ago) | S21 |
| **RF-25** | Las métricas se obtienen de un **registro estructurado y automático**, no de observación manual | Un archivo por misión, procesable sin intervención | 🟡 **Verificado el 2026-08-27 en condición A.** Esquema JSON versionado y comprobable; `herramientas/componer_registro.py` compone el registro desde el bag y lo valida contra el esquema; el veredicto se calcula contra `/odom` y nunca contra el `SUCCEEDED` de Nav2. **Probado en condición B y a escala el 2026-09-05:** 30 registros compuestos sin intervención manual, 15 de ellos de condición B, todos validados contra el esquema 1.1.0. **La campaña además puso a prueba el propio registrador y encontró un fallo silencioso:** tres bags salieron sin RTF y `grabar_mision.sh` lo tragaba saliendo con código 0, así que la corrida se perdía sin que nadie se enterara; corregido de raíz —aborta antes de grabar si falla la marca inicial, código 3 si falla la de cierre— con prueba de regresión (`herramientas/prueba_grabar_mision.py`, 12 comprobaciones sin ROS). **Sigue 🟡 y no 🟢** por un solo campo: `salud_del_banco.controladores_activos` todavía sale `{}` | S20 |
| **RF-26** | La campaña en simulación alcanza **N = 30 repeticiones** (decisión D1) | Treinta registros válidos | 🟢 **Cumplido el 2026-09-04/05, tres semanas antes de lo planificado.** 30 misiones sorteadas con semilla, corridas y compuestas en 30 registros validados contra el esquema; `analizar_campana.py` dictamina **`VALIDA`** con **0 de 30 descartes** contra un techo del 20 % | ~~S24~~ **S21** |
| **RF-27** | La demostración física ejecuta el protocolo completo con **N entre 5 y 10** (decisión D1) | Registros de las corridas físicas | 🔴 | S24–S25 |

**Lectura de OE4, revisada el 2026-09-05.** De los siete requisitos, **cinco están verificados**
(RF-21 a RF-24 y RF-26), uno queda en amarillo por un solo campo (RF-25) y el único rojo es RF-27,
que depende de hardware. El bloqueo que esta lectura describía el 27-ago —el relevo imposible de
ejecutar porque `robot1` y `robot2` vivían en dominios DDS distintos— **se levantó el 30-ago**: un
solo dominio, dos `gzserver`, separación por nombres.

**RF-24, que es la variable de respuesta principal del proyecto** —la que responde la pregunta de
investigación—, pasó de rojo a **14/14** en una campaña de N = 30 sorteada. Conviene decir de una
vez el límite, porque es de diseño y no se arregla trabajando más: **con N = 30, «la tasa de éxito
supera el 70 %» es defendible y «la tasa es del 86,7 %» no lo es**; y el contraste entre condiciones
—A 80,0 % (54,8–93,0) contra B 93,3 % (70,2–98,8)— **no sostiene ninguna conclusión**, con
intervalos solapados y apuntando además en contra de la intuición, porque la condición con relevo
salió mejor.

**RF-22 merece una advertencia aparte, porque es la métrica que puede reportarse mal sin que nadie
lo note.** El tiempo de asignación **no puede leerse del bag**: la resta `t_robot_activo −
t_solicitud` vale 0,0 s en las 30 misiones, no porque el coordinador sea infinitamente rápido sino
porque las dos marcas caen en el mismo tic de `/clock`. Quien tome esa columna del registro y
escriba «tiempo de asignación: 0 s» estará reportando el reloj, no el sistema. La cifra que se
lleva al documento final es la del banco aislado —**mediana ~155–175 µs, máximo 306 µs**— y hay que
decir con ella el método, porque un microsegundo medido dentro del proceso y un segundo medido
sobre el bag no son la misma magnitud.

Lo que queda de OE4 deja de ser *producir evidencia* y pasa a ser *redactarla*, más el campo
pendiente de RF-25 y la campaña física de RF-27.

---

## 6. Restricciones del alcance

Estas no se construyen: se respetan, y hay que **poder demostrar que se respetaron**. Salen todas
del anteproyecto §4.3.

| ID | Restricción | Cómo se demuestra | Estado |
|---|---|---|---|
| **RNF-01** | **Ningún agente cruza entre niveles.** La transición es un evento lógico del protocolo, no un desplazamiento | La coordenada vertical de cada agente es constante durante toda la misión | ✅ **medido en S18 y confirmado sobre la campaña (2026-09-05).** El registro guarda `descriptivas.desviacion_z_m` por robot: **60 medidas** —dos agentes por cada una de las 30 misiones— con un máximo de **0,0070 m**. Ningún agente subió ni bajó: la transición sigue siendo un evento del protocolo |
| **RNF-02** | Los agentes **no manipulan objetos, no transportan carga y no interactúan mecánicamente con la infraestructura** (puertas, botones de ascensor) | Por diseño: el vehículo no tiene actuadores más allá de tracción y dirección | ✅ |
| **RNF-03** | Operación **en interiores, en un espacio previamente delimitado y en condiciones controladas** | Las repeticiones se ejecutan en franjas de baja circulación; las personas se registran como observación cualitativa | 🟡 declarado |
| **RNF-04** | Plataforma **de bajo costo** | AWS DeepRacer en lugar de DonkeyCar; desviación registrada en `ESTADO.md` §6 | ✅ con desviación |
| **RNF-05** | Las trayectorias deben ser **ejecutables por cinemática Ackermann**: sin giro sobre el propio eje | Planificador con radio mínimo, árboles de comportamiento sin la primitiva de giro | ✅ **S17, y verificado sobre las trazas el 2026-09-05.** De **42 278** pares consecutivos de traza de la campaña, solo **3 (0,007 %)** muestran cambio de rumbo apreciable con menos de 1 cm de avance, y a 5 Hz de decimación eso es compatible con el temblor de la pose estimada estando quieto, no con un giro sobre el eje |
| **RNF-06** | La simulación debe correr **a tiempo real** para que las métricas temporales sean válidas | Factor de tiempo real ≥ 0,99 con las dos pilas activas | ✅ **0,996 en S18 y sostenido en las 30 misiones (2026-09-05): 30 de 30 por encima de 0,99**, mínimo **0,9917**, media **0,9973**. No es un adorno: si el RTF se hubiera caído, las cifras temporales de RF-21 y RF-24 no valdrían, así que esta restricción es lo que hace legibles las métricas de OE4 |
| **RNF-07** | El sistema **no resuelve navegación autónoma general**: opera en un entorno conocido y mapeado | El mapa es un insumo, no un producto de la misión | ✅ |

**RNF-01 merece atención especial.** Es a la vez una restricción y **el aporte del proyecto**: lo
que atraviesa el piso es la comunicación entre agentes, no el robot. Se demostró midiendo que la
altura del vehículo varió 1,9 micrómetros durante una navegación completa en el nivel superior.

---

## 7. Lo que esta matriz deja al descubierto

Escribir los requisitos obliga a mirar los huecos. Tres cosas aparecen y no estaban explícitas:

1. **Tres defectos abiertos son condición previa de OE4, y no son requisitos.** Un requisito
   describe lo que el sistema debe hacer; estos describen que el instrumento de medida no es
   fiable todavía. Están en `ESTADO.md` §8 y en
   [`Evidencia/S17_nav2_namespaces.md`](Evidencia/S17_nav2_namespaces.md): una lectura de `/odom`
   que devolvió la posición del otro agente, una desviación de hasta 18° con mando puramente
   lineal, y una competencia intermitente al cargar controladores. **RF-13, RF-21 a RF-27 no se
   pueden dar por verificados mientras sigan abiertos.**

2. **Dos artefactos que el contrato da por existentes todavía no existen:** el paquete
   `coordinacion_msgs` con sus cuatro definiciones, y `puntos_interes.yaml`. Son la primera media
   jornada de S20, y sin ellos RF-04 a RF-08 no tienen dónde apoyarse.

3. **`puntos_interes.yaml` no tiene contenido definido.** El contrato fija su formato pero nadie ha
   decidido **cuáles** son las localizaciones de interés del entorno de evaluación ni sus poses.
   Es trabajo de escritorio, se hace sobre la geometría del mundo ya construido, y bloquea RF-04,
   RF-17 y toda la campaña de OE4 —porque los orígenes y destinos de las 30 repeticiones salen de
   ahí—. **Conviene resolverlo esta semana**, junto con el protocolo experimental.

4. **El `sim ✅` de RF-13 se obtuvo contra un oráculo, y eso no es una verificación**
   *(añadido el 2026-08-26)*. En simulación, `/odom` no es una estimación: el plugin lo publica
   desde `model_->WorldPose()` —`deepracer_gazebo/src/gazebo_ros_deepracer_drive.cpp:229`—, o sea
   la pose exacta que Gazebo tiene en su motor, sin ruido ni deslizamiento. Y como
   `publish_odom_tf: true`, la transformada `odom → base_link` también es verdad de terreno.
   Comprobar «lectura antes y después de un desplazamiento conocido» sobre ese tópico es comparar
   el oráculo consigo mismo: **da bien siempre y no puede fallar**, así que no aporta información.

   El requisito solo queda verificado sobre el vehículo físico, y ahí la única fuente de odometría
   es `rf2o_laser_odometry` —`deepracer_bringup/launch/deepracer.launch.py:90`—, porque **el
   DeepRacer no lleva encoders de rueda**: su sensado es dos cámaras RGB, un LiDAR plano y una IMU.
   Medido fuera de línea el 2026-08-26, rf2o registra el **5,7 %** y el **1,3 %** del
   desplazamiento real en los dos tramos del pasillo simulado. La medición que sí verifica RF-13
   es la corrida recta de ≥ 20 m añadida al frente B de S20, con los umbrales M1 y M2 del GO / NO-GO
   de S21.

   Consecuencia sobre lo ya medido: **todo error de llegada calculado «contra `/odom`»** —los
   0,190 m de `piso2_escalera`, los 0,281 m y 0,143 m del hito H3— **es válido como verdad de
   terreno en simulación**, y de hecho es la mejor referencia posible ahí. Lo que no es válido es
   citarlos como evidencia de que *la odometría funciona*: miden el control y la localización, no
   el odómetro.

> **Los puntos 2 y 3 están caducados y se corrigen en el corte del 2026-08-28:** `coordinacion_msgs`
> existe y hace round-trip por DDS desde el 24-ago, y `puntos_interes.yaml` tiene 31 puntos —15 de
> nivel 1, 16 de nivel 2— con sus dos puntos de transferencia. Del punto 1, la lectura cruzada de
> `/odom` se declaró **no reproducible** el 25-ago y la causa era la herramienta.

---

## 8. Qué es negociable y qué no

La §9 del [cronograma](CRONOGRAMA_S17_S32.md) define una escalera de holgura. Traducida a
requisitos concretos, para que un recorte no se decida a última hora sobre lo que no se debe
recortar:

| Orden | Si falta tiempo, se recorta | Requisitos afectados |
|---|---|---|
| 1.º | El pasillo USTA como escenario secundario en simulación | Ninguno (ya fuera del camino crítico) |
| 2.º | Las repeticiones físicas bajan de 10 a 5 | RF-27 se relaja |
| ~~3.º~~ | ~~La demostración física pasa a un agente real más uno simulado~~ | ❌ **Escalón eliminado el 2026-08-18.** No es un recorte disponible: un coordinador Humble no manda a un robot Jazzy, porque `nav2_msgs/NavigateToPose` tiene distinta definición en las dos distribuciones ([spike, pregunta 4](Evidencia/S19_spike_p4_humble_jazzy.md) §2). Habilitarlo exigiría escribir un puente entre distribuciones: **trabajo nuevo en el camino crítico**, que es justo lo contrario de un recorte |
| 4.º | La HRI pasa de mapa interactivo a dos listas desplegables | Ninguno: **RF-17 se cumple igual**. Solo se pierde representación gráfica, que no la exige ningún requisito |

**No se recorta bajo ninguna circunstancia:** **RF-05, RF-07, RF-21 a RF-25**. Son el nodo de
coordinación, el protocolo de relevo y la instrumentación. Constituyen el aporte técnico declarado
del proyecto: sin ellos no hay resultado que sustentar.

---

## 9. Resumen de trazabilidad

| Objetivo | Requisitos | Verificados | Pendientes | Semana de cierre |
|---|---|---|---|---|
| OE1 | RF-01 a RF-10 | **10** | **0** | ~~S20–S21~~ ~~**S21**, salvo RF-08~~ **S22 — cerrado** |
| OE2 | RF-11 a RF-16 | 0 (**5** parciales) | **1** (RF-15) | S19–S22 |
| OE3 | RF-17 a RF-20, RF-28 | 4 | **1** (RF-28) | S22 |
| OE4 | RF-21 a RF-27 | **5** | 1 + 1 parcial | ~~S20–S25~~ **S21**, salvo RF-27 (física) |
| Restricciones | RNF-01 a RNF-07 | 6 | 1 parcial | — |
| **Total** | **35** | **24** | **3 + 8 parciales** | |

> **El total sube de 34 a 35 el 2026-09-10** con la entrada de **RF-28**, que no estaba en el
> anteproyecto: lo pidió el director como situación de experiencia de usuario. Es **funcionalidad
> añadida**, no una corrección: no modifica ninguna de las cuatro métricas de OE4 ni el
> planificador, así que **la campaña de 30 misiones no se reejecuta** (el argumento fila por fila
> está en la §5 de [`DISENO_CONFIRMACION_PISO.md`](DISENO_CONFIRMACION_PISO.md)). Los 24
> verificados no cambian; los pendientes pasan de 2 a 3.

**Veinticuatro de treinta y cinco requisitos están verificados** al 2026-09-07, y ya no son solo
los de infraestructura: los cinco que entraron por OE4 (RF-21 a RF-24 y RF-26) son **las cuatro
métricas más la campaña de N = 30**, y los cuatro que entraron por OE1 (RF-04 a RF-07) incluyen **el
protocolo de relevo**, o sea el aporte declarado. Con RF-08 cerrado el 7 de septiembre, **OE1 queda
completo: diez de diez**. **Quedan tres pendientes y ocho parciales**, y conviene mirarlos por lo
que los bloquea, no por cuántos son:

- **RF-14** (comando desde ROS 2), ya en 🟡 — falta **calibrar la escala** de la cadena `/cmd_vel`
  contra el vehículo, porque el escalón más bajo cae en 0,40 m/s y Nav2 pide 0,25 y 0,05. Le basta
  **un** vehículo, luego **no está bloqueado por R11**: es trabajo ejecutable ya.
- **RF-15** (red entre los dos vehículos) — **atado a R11**, el segundo DeepRacer en intervención
  técnica sin caracterizar desde el 14-ago. No depende de horas de trabajo.
- **RF-27** (campaña física de 5 a 10 corridas) — depende del GO/NO-GO de hardware, que **sigue
  abierto** porque G2 se detuvo por su propia regla de parada.
- **RF-28** (confirmación del cambio de piso) — entró el 2026-09-10 y **no depende de hardware
  ninguno**: es código más tres corridas en simulación. Implementado el mismo día; queda solo su
  evidencia, que es el §7 de [`DISENO_CONFIRMACION_PISO.md`](DISENO_CONFIRMACION_PISO.md).
- **RF-11, RF-12 y RF-13**, los tres parciales de OE2 — tras la revisión del 5-sep lo que les falta
  está acotado y **también le basta un vehículo**: el mapa de costos local sobre el carro, la
  lectura de `/<ns>/odom`, y discriminar el +2,9 % de escala de la odometría láser con la prueba
  del `.pgm` que ya está definida.

O sea: **dos de los tres pendientes dependen de que el hardware aparezca** —RF-15 por R11, RF-27
por el GO/NO-GO—, y el tercero, RF-28, no existía cuando se escribió este párrafo. Hasta el
2026-09-10 la frase era más fuerte: *ya no queda ningún pendiente que se resuelva solo escribiendo
código*, y era cierta —el último así fue RF-08, cerrado el 7 de septiembre—. **RF-28 la reabre, y
no por un descuido de planificación:** lo pidió el director como situación de experiencia de
usuario, no sale del anteproyecto, y es la primera de seis que él planteó. Queda escrito aquí para
que el recuento no se lea como un retroceso. Y de los ocho parciales, **los tres de OE2 no
están esperando a R11**: esperan una jornada de laboratorio con el vehículo que sí hay, igual que
la escala de RF-14.

Esa es la lectura honesta del 7 de septiembre, y **no la mejora el conteo**, que ha subido de 19 a
24 en dos semanas. Lo que la mejoraría es la salida al pasillo del martes 8: los cuatro puntos que
siguen abiertos —RF-14, RF-11, RF-12, RF-13— son todos trabajo de campo con un solo vehículo, y
salen de una misma jornada.

> *Nota sobre este §9, 2026-09-05.* Las revisiones de OE1 y de RF-14 de hoy salieron las dos de
> **leer el código y los datos en vez de la bitácora**, y las dos encontraron el documento desfasado
> en direcciones opuestas: OE1 estaba **subestimado** —cuatro requisitos ejecutados seguían en
> rojo— y la cadena `/cmd_vel` estaba **descrita como más rota de lo que está**, con dos defectos
> que llevaban corregidos desde el 27-ago. Un tablero puede equivocarse a la baja tanto como al
> alza, y las dos formas cuestan igual: la primera esconde trabajo hecho, la segunda hace planificar
> contra un problema que ya no existe.
>
> *Barrido completo del resto de la matriz, mismo día.* Se revisaron las veinte celdas restantes con
> el mismo método y **ninguna cambió de color**, pero **nueve estaban mal escritas**, en tres clases
> distintas que conviene separar porque se corrigen de forma distinta:
> **(1) prueba obsoleta** — RF-01 y RF-02 se probaban «por dominio» y esa arquitectura se sustituyó
> el 30-ago por un dominio con dos `gzserver`; la prueba se reescribió y se re-ancló a la campaña.
> **(2) evidencia subestimada** — RF-11, RF-12 y RF-13 daban por futuro o por rojo lo que se midió
> el 19 y el 28 de agosto con un solo vehículo; RF-21 citaba n = 1 teniendo n = 30; RNF-01 y RNF-06
> citaban S18 teniendo 60 y 30 medidas de la campaña.
> **(3) prueba que se satisface con un cero** — el caso grave es **RF-22**: su prueba era «el
> registro contiene las dos marcas», y esa resta vale 0,0 s en 30 de 30 **por construcción del
> instrumento**. Estaba en verde por una comprobación que no puede fallar. Se reescribió contra el
> banco aislado, que es de donde sale la cifra publicable.
>
> La clase (3) es la que hay que buscar en el resto del documento antes de la sustentación: **una
> prueba que no puede fallar no es una prueba**, y no se distingue de una buena mirando el color.

> *Corrección aritmética, 2026-09-05:* este párrafo decía «once de treinta y cuatro» mientras su
> propia tabla sumaba catorce. Se recalcula contra la tabla, que es la fuente. El texto llevaba
> desde el 27-ago desfasado respecto a las filas que lo sostienen.

*Actualizado el 2026-08-18: RF-16 pasa de pendiente a parcial tras la pregunta 4 del spike, y se
registra RF-16b como requisito descartado por imposible.*

---

## 10. Criterio de cierre de este documento

R5 se declara cerrado cuando esta matriz existe, cada requisito cita su fuente y su prueba, y
`ESTADO.md` la enlaza. **Se declara cerrado el 2026-08-18.**

Lo que R5 no cierra: los requisitos pendientes siguen pendientes. Esta matriz no construye nada;
lo que hace es que a partir de ahora se pueda responder, para cualquier semana, qué falta y cómo
se demostrará que se hizo.
