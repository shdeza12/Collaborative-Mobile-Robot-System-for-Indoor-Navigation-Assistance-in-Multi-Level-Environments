# Taller 2 — Corte 1 · Del anteproyecto al documento final

**Estudiantes:** Santiago Hernández Ávila · Jonny (co-autor)
**Título:** *Collaborative Mobile Robot System for Indoor Navigation Assistance in Multi-Level Environments*
**Fecha de diligenciamiento:** 2026-08-31 (S21 de 32)

> **Nota de forma.** Las tablas del taller traen tres objetivos específicos. El anteproyecto
> aprobado (§4.2) define **cuatro**. Se agrega la fila OE4 en todas las matrices en lugar de
> omitirla: OE4 es el objetivo de evaluación y es donde vive la evidencia que el jurado va a pedir.

---

## ACTIVIDAD 1 · Auditoría de las secciones heredadas

### Hallazgos iniciales

| Aspecto que ya no representa con precisión el proyecto | Aspecto que requiere revisión con el director |
|---|---|
| **1. La plataforma.** §4.2 y §4.3 dicen *«dos vehículos tipo DonkeyCar»* y *«plataforma de bajo costo DonkeyCar»*. Se trabaja con **AWS DeepRacer**. **El anteproyecto ya se contradecía a sí mismo**: su propio §7.2 lista como hardware *«AWS Deepracer»* y *«Raspberry PI 4»*, no DonkeyCar | **Sí — R.** Cambia una plataforma nombrada en un objetivo específico. No se puede corregir de forma unilateral aunque el §7.2 del mismo documento ya nombre el DeepRacer |
| **2. La interfaz.** §4.3 promete *«una aplicación móvil»*. Lo aprobado con los directores es una **interfaz web responsiva** a la que el usuario llega escaneando un **QR** desde el navegador del teléfono, sin instalar nada. El §7.2 ya declaraba la pila web («JavaScript, PHP, HTML» + «dispositivos móviles») | **Sí — R.** Es el producto entregable nombrado en el alcance. El objetivo OE3 dice «interfaz móvil», que la web cumple; el alcance dice «aplicación», que no |
| **3. Las métricas de validación.** §7.4 propone *«número de guías exitosas, tiempo por fuera de rutas preestablecidas»*. Las métricas que se instrumentaron son las **cuatro del OE4** (tiempo de respuesta, tiempo de asignación, tasa de éxito, continuidad entre niveles). *«Tiempo por fuera de rutas preestablecidas»* nunca se midió ni se va a medir | **Sí — R.** El §7.4 y el §4.2 del propio anteproyecto piden cosas distintas. Prevalece el objetivo específico; hay que dejarlo avalado por escrito |

### Auditoría por sección

| Sección | ¿Qué establece el anteproyecto? | ¿Qué ocurrió durante el desarrollo? | Estado | Acción requerida |
|---|---|---|---|---|
| **Problema** (§2.1) | Desorientación en interiores multipiso; superar la discontinuidad vertical con un agente único exige hardware caro o intervenir ascensores; propone un **relevo entre robots dedicados a un nivel**, coordinados por servidor | Es exactamente lo construido. El relevo se ejecutó el 2026-08-30 con los dos robots vivos y ningún robot cruzó de nivel. No hay afirmación en el planteamiento que exceda lo demostrable | **C** | Conservar. Añadir al final una frase que ancle el planteamiento al resultado del 30-ago |
| **Justificación** (cap. 3) | Aporte técnico = continuidad de asistencia entre pisos vía comunicación inter-robot y asignación dinámica, con *«robots tipo DonkeyCar»* | El aporte se sostiene y ya tiene evidencia. La mención a DonkeyCar es falsa | **A** | Sustituir DonkeyCar → AWS DeepRacer. Separar explícitamente *lo demostrado* (relevo funcional, n = 1) de *lo potencial* (impacto en accesibilidad, que **no se mide**) |
| **Objetivo general** (§4.1) | Sistema colaborativo de dos robots para guía coordinada «y eficiente» mediante comunicación inter-robot, asignación dinámica e interfaz móvil | Los tres mecanismos existen o están planificados. **«Eficiente» no está operacionalizado** en ninguna parte del anteproyecto | **F** | Conservar la redacción; en el documento final declarar que «eficiente» se operacionaliza mediante las cuatro métricas del OE4, y decirlo en el capítulo de metodología |
| **OE1** — modelar arquitectura funcional | Requerimientos, escenarios multipiso, estrategia de asignación y esquema de comunicación | **Cumplido y excedido.** 34 requisitos trazados (`REQUISITOS.md`), contrato de interfaces verificado en simulación, 992 planes origen–destino verificados sin simulador, catálogo de 16 destinos por nivel, `coordinacion_msgs` con round-trip real por DDS (18/18) | **F** | Conservar. Falta redactar el capítulo que lo presente y citar la clasificación **ST–SR–IA** (Gerkey & Matarić) del algoritmo, que hoy solo está en un anexo del repositorio |
| **OE2** — plataforma con **dos** vehículos | *«dos vehículos tipo DonkeyCar»*, con locomoción, sensado, procesamiento y comunicación | AWS DeepRacer. Un vehículo instrumentado (LiDAR conviviendo con la pila, teleoperación por `/ctrl_pkg/servo_msg`); **el segundo está en intervención técnica desde el acta del 2026-08-14 y sigue sin caracterizar** (R11). Distribución real Ubuntu 24.04 + ROS 2 Jazzy, no Raspbian | **R** | Aval del director sobre (a) el cambio de plataforma y (b) si «dos vehículos» se demuestra en simulación cuando el segundo carro físico no esté disponible |
| **OE3** — interfaz móvil HRI origen–destino | Programar interfaz móvil para selección origen–destino | **0 % ejecutado.** Se construye en S22 (7–13 sep); Jonny la toma en paralelo. El diseño avalado por los directores es web + QR + avisos visuales de estado | **A** | Actualizar «aplicación móvil» → «interfaz web responsiva accesible desde el navegador del teléfono». Es la única barra completa que queda sin empezar |
| **OE4** — evaluar con cuatro métricas | Tiempo de respuesta, tiempo de asignación, tasa de éxito, continuidad entre niveles, en entorno interior controlado | Las cuatro están definidas operacionalmente en `PROTOCOLO_EXPERIMENTAL.md` (escrito **antes** de instrumentar) y la cadena de medida está completa. **La campaña no se ha ejecutado: 0 de 30 misiones** | **C** | Conservar literal. Es la sección mejor alineada del anteproyecto |
| **Alcance** (§4.3) | Prueba de concepto; dos agentes DonkeyCar; **aplicación móvil**; pruebas *«en un entorno interior con multiples pisos»*; sin manipulación, sin botones de ascensor, sin exteriores | Los límites negativos se respetan íntegros. Las tres desviaciones son: plataforma, tipo de interfaz, y que **la campaña de N = 30 con dos niveles corre en simulación** mientras la parte física ocurre en un solo piso (no hay forma de subir un DeepRacer por una escalera) | **R** | Aval del director sobre el reparto simulación / físico. Argumento técnico a favor: como **ningún robot cruza de nivel por diseño**, una campaña física de un solo piso ejercita el protocolo completo salvo el traslado vertical, que el diseño no contempla |
| **Marco referencial** (cap. 5–6) | MRS, cobot, HRI, navegación (localización, planificación, control), zona de transición, asignación de tareas, ROS; CONPES 3975 y 4069 | Los conceptos sí se usan. **Sobran** los apartados de *visión computacional* (no se usa: la percepción es LiDAR + AMCL) y las políticas CONPES, que no informan ninguna decisión técnica. **Faltan** la taxonomía de asignación multi-robot y el intervalo de Wilson usado para la tasa de éxito | **F** | Añadir Gerkey & Matarić (taxonomía ST–SR–IA) y la justificación del intervalo de confianza. Podar visión computacional o declararla explícitamente fuera de uso |
| **Metodología** (cap. 7) | 7 fases; §7.2 lista CoppeliaSim, OpenCV, Jetson Nano, Raspbian, ROS 2 «Humble o Jazzy»; §7.3 «simulación en software de representación 2D»; §7.4 métricas distintas a las del OE4 | Las **fases se cumplieron**. Las **tecnologías no**: Gazebo Classic 11 (no CoppeliaSim), simulación 3D (no 2D), sin OpenCV, sin Jetson Nano, Ubuntu (no Raspbian). ROS 2 **Humble** en simulación y **Jazzy** en el vehículo — la ambigüedad del anteproyecto se volvió un problema real (R8: 6 diferencias, 37 líneas de YAML, 2 árboles de comportamiento BT.CPP v3→v4, y `nav2_msgs/NavigateToPose` con **distinta definición** entre distribuciones) | **A** | Reescribir §7.2 y §7.3 con lo realmente usado y **justificar cada sustitución**. Cerrar la ambigüedad Humble/Jazzy declarando las dos distribuciones y el desajuste como limitación |

---

## ACTIVIDAD 2 · Matriz objetivo–evidencia

| OE | ¿Qué prometía? | ¿Qué se hizo? | Evidencia disponible | Evidencia faltante | Métrica / criterio | Ubicación en la tesis | Clasificación |
|---|---|---|---|---|---|---|---|
| **OE1** | Modelar la arquitectura funcional: requisitos, escenarios multipiso, asignación de tareas, comunicación inter-robot | Matriz de 34 requisitos con fuente citable; contrato de interfaces ROS 2; nodo de coordinación con el relevo escrito como función pura; catálogo de 16 destinos por nivel | `REQUISITOS.md` (34 RF/RNF, ninguno huérfano); `CONTRATO_INTERFACES.md` verificado en simulación; **992 planes** origen–destino verificados sin simulador; round-trip DDS **18/18** sobre los 16 puntos reales; `arquitectura.png`; asignación por nivel ejecutada (2 solicitudes → 2 agentes distintos) | Nombres definitivos de las salas del piso 2; `coordinacion_msgs` compilado en la tarjeta Jazzy del carro | Cobertura RF↔OE = 100 % (0 objetivos huérfanos); planes verificados 992/992; round-trip 18/18 | Cap. Desarrollo §Arquitectura y §Requisitos | 🟢 **VERDE** |
| **OE2** | Plataforma con **dos** vehículos: locomoción, sensado, procesamiento y comunicación | Un vehículo con pila propia instrumentada; simulación completa de dos agentes; sensado real medido | LiDAR real: repetibilidad de pared **2,8 mm**; `/scan` a **6,80 Hz**, 360 muestras / 360°; convivencia con la pila a un coste medido de **−6,6 %** (6,80 → 6,35 Hz); teleoperación por `/ctrl_pkg/servo_msg` con hombre muerto de 0,6 s; dos agentes navegando bajo namespace aislado en simulación | **El segundo vehículo físico** (R11, en intervención técnica desde el 14-ago, sin caracterizar); cadena `/cmd_vel` real; cámaras publicando en ROS; medida de latencia inter-vehículo | Repetibilidad LiDAR (mm); frecuencia de barrido (Hz); degradación por convivencia (%); error de seguimiento de comando | Cap. Desarrollo §Plataforma física + §Limitaciones | 🟡 **AMARILLO** |
| **OE3** | Interfaz móvil HRI con selección origen–destino | **Nada aún.** Se construye en S22 | Ninguna | Toda: la interfaz, las pruebas RF-17 a RF-20, y una prueba de usabilidad si se decide medirla | Pendiente de definir. Mínimo: RF-17 (selección origen+destino) y RF-18 (`mensaje_usuario` mostrado **literal**) verificados sobre un teléfono real | Cap. Desarrollo §Interfaz de usuario | 🔴 **ROJO** |
| **OE4** | Evaluar con tiempo de respuesta, tiempo de asignación, tasa de éxito y continuidad entre niveles | Protocolo experimental escrito antes de instrumentar; cadena completa sorteo → corrida → bag → registro JSON validado → métricas con intervalo de confianza; **una** misión de relevo ejecutada | Relevo del 2026-08-30: `exito: true`, **1 relevo**, **47,6 s**, llegadas de **0,128 m** y **0,077 m** contra `/odom` (criterio 0,25 m), **373 y 580** mensajes en los `cmd_vel` de cada robot; banco de tiempo de asignación: **mediana 154–175 µs, máximo 306,4 µs** en 4 corridas × 30 misiones; registros JSON validados contra esquema versionado (1.1.0) | **La campaña: 0 de 30 misiones sorteadas ejecutadas.** Sin ella no hay tasa de éxito, ni intervalo de confianza, ni continuidad agregada | Tasa de éxito con **intervalo de Wilson al 95 %**; llegada ≤ **0,25 m** contra `/odom` (nunca contra el `SUCCEEDED` de Nav2); tiempo de asignación como **cota superior < 100 ms** más caracterización en banco; continuidad booleana por misión; techo de descartes **20 %** | Cap. Resultados §Campaña OE4 | 🟡 **AMARILLO** |

> **Pregunta obligatoria — «Si un jurado solo revisara estas evidencias, ¿podría afirmar que el
> objetivo fue cumplido?»**
> OE1: sí. OE2: solo en simulación; en físico afirmaría *sensado y locomoción*, no *sistema de dos
> vehículos*. OE3: no. OE4: hoy afirmaría que **el mecanismo funciona** (n = 1) pero **no** que
> funciona con una tasa determinada, que es lo que el objetivo pide. Esa brecha se cierra
> ejecutando la campaña en S24 y no de otra forma.

---

## ACTIVIDAD 3 · Metodología proyectada vs. ejecutada

| Aspecto | Lo planteado (anteproyecto) | Lo ejecutado | ¿Qué cambió y por qué? | Evidencia que debe quedar en la tesis |
|---|---|---|---|---|
| **Requisitos** | §7.1.2: «identificación de requerimientos funcionales» sin documento asociado | 34 requisitos numerados (RF-01…RF-27, RNF-01…RNF-07), cada uno con fuente citable, prueba y semana | El anteproyecto **nunca enumeró requisitos**, así que su propio §7.4 («comparación con requisitos») era inejecutable. Se reconstruyeron el 2026-08-18. Se declara **reconstrucción, no recuperación** | `REQUISITOS.md` completo como anexo, con el estado de verificación (11 verificados, 4 parciales, 19 pendientes al 31-ago) |
| **Arquitectura** | §7.1.3: módulos, representaciones conceptuales, estrategias preliminares | Contrato de interfaces ROS 2 explícito (namespaces, acciones, tópicos, 5 definiciones de mensaje) verificado en ejecución | Se elevó de «representación conceptual» a **contrato verificable**, porque dos personas trabajando en paralelo necesitan una frontera que el compilador pueda comprobar | `CONTRATO_INTERFACES.md` + diagrama + evidencia del round-trip DDS |
| **Componentes / tecnologías** | CoppeliaSim, OpenCV, Jetson Nano, Raspbian, ROS 2 «Humble o Jazzy», DonkeyCar | Gazebo Classic 11, sin OpenCV, sin Jetson, Ubuntu 22.04 (Humble, simulación) y Ubuntu Server 24.04 (Jazzy, vehículo), AWS DeepRacer | Gazebo por integración nativa con ROS 2 y `ros2_control`; sin visión porque la percepción necesaria es geométrica (LiDAR + AMCL) y añadir visión no servía a ningún requisito; DeepRacer porque es el hardware disponible en el grupo GED — y el §7.2 del propio anteproyecto ya lo nombraba | Tabla de sustituciones tecnológicas con justificación una a una, en §Metodología ejecutada |
| **Modelado** | «Simulación en software de representación 2D»; «definición de rutas mediante grafo» | Mundos SDF **3D** del pasillo real USTA; grafo de puntos de interés implementado (`puntos_interes.yaml`, 16 destinos por nivel) | El 2D no permite modelar el LiDAR ni la cinemática Ackermann, que son las dos restricciones que dominan el problema. El grafo sí se cumplió | `mundo_definitivo.world`, mapa `primer_piso_definitivo` verificado (cobertura 99,7 % en X, 14,5 % de celdas desconocidas, 0/5149 obstáculos sin pared real) |
| **Cálculos** | «Estimación de variables de navegación» | Radio mínimo de giro y footprint real (0,28 × 0,19 m); conversión `angular.z` → ángulo de dirección Ackermann; dimensionamiento de `max_laser_range` contra el alcance físico del sensor | Se hicieron los cálculos que las fallas obligaron a hacer. Dos son resultado de depuración, no de diseño previo | Deducción de la conversión Ackermann con su verificación: RMS del giro real contra el comandado **0,298 → 0,111 rad/s** |
| **Simulación** | Fase 4, «evaluación preliminar del comportamiento» | Dos `gzserver` simultáneos (uno por nivel), navegación Nav2 con **Smac Hybrid-A\*** y `REEDS_SHEPP`, árboles de comportamiento propios sin `<Spin>` | El planificador por defecto (DWB) asume tracción diferencial; el DeepRacer no gira sobre su eje. Cambio **forzado por la cinemática**, no por preferencia | Gráficas de plan vs. trayectoria ejecutada desde el bag (`graficar_plan.py`), mostrando la maniobra de volteo propuesta y ejecutada |
| **Implementación** | §7.1.4, «desarrollo gradual de los componentes» | Paquete `coordinacion` con planificador (función pura), coordinador (máquina de estados) y registrador; 992 planes verificados sin simulador | Se separó la lógica de coordinación de ROS para poder verificarla **sin simulador**. Es lo que permitió detectar defectos antes de gastar corridas | Estructura del paquete + resultados de las pruebas unitarias que no requieren ROS |
| **Integración** | §7.1.5, «integración progresiva y verificación conjunta» | Dos agentes + coordinador en un solo dominio DDS con separación por nombres; relevo completo ejecutado | El bloqueo inicial fue de **dominios DDS**: dos dominios separados impedían que el coordinador hablara con ambos agentes. Se resolvió el 2026-08-30 | `S21_bloqueo_dominios.md` y `S21_relevo_ejecutado.md`, con la secuencia de etapas `RECIBIDA → TRAMO_1 → TRAMO_1 → TRANSFERENCIA → TRAMO_2 → COMPLETADA` |
| **Procedimiento experimental** | §7.1.6, «ejecución de pruebas» y «recolección de información», sin protocolo | `PROTOCOLO_EXPERIMENTAL.md`: definiciones operativas, N = 30 con **sorteo por semilla**, lista **cerrada** de causas de descarte con techo del 20 %, registro JSON automático por misión validado contra esquema | Escrito **antes** de instrumentar, deliberadamente, para que el criterio no se ajustara al resultado. El sorteo elimina la selección de misiones convenientes | El protocolo completo como anexo + el esquema `esquema_registro_mision.json` v1.1.0 |
| **Validación** | §7.4: pruebas funcionales, de desempeño («número de guías exitosas, tiempo por fuera de rutas preestablecidas»), comparación con requisitos y verificación | Las **cuatro métricas del OE4**; éxito decidido por **posición contra `/odom`**, no por el `SUCCEEDED` de Nav2; tasa de éxito con intervalo de Wilson al 95 % | Dos cambios de fondo: (1) «tiempo por fuera de rutas» se descartó por no responder a ningún objetivo; (2) el `SUCCEEDED` de Nav2 **no es evidencia** — el verificador de meta daba por fallidas llegadas buenas por no cerrar el rumbo, cosa que un Ackermann no puede hacer girando sobre su eje | Evidencia del defecto con las **dos cifras de la misma llegada**: posición 0,413 m (fuera de tolerancia) y rumbo 0,200 rad (dentro). Es lo que justifica cambiar el criterio |

---

## ACTIVIDAD 4 · Evidencia crítica de validación

**Objetivo seleccionado: OE4 — continuidad del servicio entre niveles.**
Es la *variable de respuesta principal* del protocolo: mide el aporte declarado del proyecto (que la
asistencia no se interrumpe en la transición vertical). Si esta prueba no se sostiene, no hay tesis.

| Elemento | Definición para el proyecto |
|---|---|
| **Objetivo asociado** | OE4 · requisito RF-24 (continuidad del servicio entre niveles) |
| **Variable o parámetro a evaluar** | `continuidad`: booleano por misión. Es **verdadero** si durante toda la ventana de servicio existe en todo momento un robot activo asignado a la misión — es decir, si el usuario nunca queda sin agente responsable durante el relevo entre niveles |
| **Referencia o valor esperado** | Continuidad verdadera en toda misión que además cumpla las tres condiciones de éxito. Valor esperado del proyecto: **≥ 90 %** de las misiones válidas con `continuidad = true` |
| **Instrumento / herramienta** | Registro automático de misión (RF-25): `grabar_mision.sh` sella el bag con tiempo de simulación; `componer_registro.py` compone un JSON validado contra `esquema_registro_mision.json` **v1.1.0**; `analizar_campana.py` agrega la campaña. Sin intervención manual en ningún paso |
| **Condiciones de prueba** | Simulación Gazebo Classic 11 + ROS 2 Humble. `mundo_definitivo.world`: dos pasillos que representan el piso 1 y el piso 2, un `gzserver` y un agente Nav2 por nivel, un solo dominio DDS con separación por nombres. Mapa `primer_piso_definitivo`. AMCL con `alpha = 0.01`. Catálogo de 16 destinos por nivel. RTF registrado por misión |
| **Número de repeticiones** | **N = 30** misiones, con pares origen–destino **sorteados por semilla** (`sortear_misiones.py`), no elegidos. Las misiones piloto se marcan `es_piloto` y **quedan excluidas** del cómputo |
| **Métrica a calcular** | (a) Proporción de misiones con `continuidad = true` sobre las misiones válidas; (b) su **intervalo de confianza de Wilson al 95 %**; (c) `hueco_relevo_s`, la duración del intervalo sin robot activo cuando lo hay |
| **Origen del criterio de aceptación** | El objetivo específico 4 del anteproyecto aprobado (§4.2), que nombra literalmente *«continuidad del servicio entre niveles»* como métrica. La operacionalización está en `PROTOCOLO_EXPERIMENTAL.md` §3.4, redactado **antes** de instrumentar |
| **Criterio de aceptación** | ≥ 90 % de misiones válidas con `continuidad = true`, **y** que la campaña sea válida: descartes ≤ 20 % del total, con causa dentro de la lista cerrada (`caida_gazebo`, `controladores_incompletos`, `rtf_bajo`, `fallo_anfitrion`). Superado el techo de descartes, la campaña se invalida completa |
| **Resultado a reportar** | La proporción **con su intervalo de Wilson**, nunca el porcentaje solo. Ejemplo de la forma exacta: *«27 de 30 misiones mantuvieron la continuidad (90,0 %; IC 95 % de Wilson: 74,4 % – 96,5 %)»*. Se reporta además el número y la causa de cada descarte |
| **Figura / tabla prevista** | **Tabla:** una fila por misión (id, semilla, origen, destino, relevos, `continuidad`, `exito`, error de llegada, RTF). **Figura:** línea de tiempo de una misión representativa con las etapas `RECIBIDA → TRAMO_1 → TRANSFERENCIA → TRAMO_2 → COMPLETADA` y el robot activo en cada instante, que es la forma visual de la continuidad |
| **Reproducibilidad** | **Sí.** Otro grupo puede repetir la campaña con: el repositorio en el commit de congelación (S23), la semilla del sorteo, `RUNBOOK_CAMPANA.md` y el protocolo. El sorteo es determinista dada la semilla, los registros se validan contra un esquema versionado, y `analizar_campana.py` produce el informe sin decisiones manuales. **Limitación de reproducibilidad honesta:** el RTF depende de la máquina anfitriona, por lo que se registra por misión y `rtf_bajo` es causa legítima de descarte |

---

## ACTIVIDAD 5 · Proyección del capítulo de desarrollo

| Pregunta de ingeniería | Evidencia o sección que debe aparecer en el documento |
|---|---|
| ¿Qué debía cumplir la solución? | §Requisitos: los 34 RF/RNF con su trazabilidad a los cuatro objetivos (`REQUISITOS.md` §9). Ningún objetivo sin requisitos, ningún requisito sin objetivo |
| ¿Cuáles fueron los requisitos y restricciones? | Restricciones duras a declarar de frente: **cinemática Ackermann** (el vehículo no gira sobre su eje), **ningún robot cruza de nivel** (decisión de diseño D2), y el LiDAR simulado barre 300° con el cono ciego sobre el morro |
| ¿Qué arquitectura se definió? | §Arquitectura: diagrama de nodos y tópicos; coordinador central con dos agentes bajo namespace; contrato de interfaces con las cinco definiciones de mensaje; frontera declarada de que la HRI habla **solo** con `/coordinacion`, nunca con los agentes (RF-19) |
| ¿Qué alternativas se consideraron? | (1) Un robot con hardware de transición vertical o intervención del ascensor — descartado por costo e invasividad, ya argumentado en el planteamiento. (2) Wall-follower clásico PD — **medido e inestable** en el pasillo real por la restricción de radio mínimo. (3) DWB vs. Smac Hybrid-A\*. (4) Interfaz nativa vs. web |
| ¿Cómo se seleccionó la solución? | Criterios explícitos con la medida que los sustenta: el wall-follower se abandonó por evidencia de no convergencia en pasillo angosto, no por preferencia; DWB se abandonó porque asume tracción diferencial; la interfaz web se eligió porque RF-20 pide acceso sin instalación |
| ¿Qué cálculos sustentan el diseño? | Footprint real 0,28 × 0,19 m y radio mínimo de giro; conversión `angular.z` → ángulo de dirección; dimensionamiento de `max_laser_range` a 9,5 m contra un alcance físico de 10,0 m; cálculo del intervalo de Wilson |
| ¿Qué simulaciones fueron realizadas? | Navegación punto a punto en ambos niveles; 992 planes origen–destino verificados sin simulador; asignación por nivel; relevo completo; 4 corridas × 30 misiones del banco de tiempo de asignación |
| ¿Cómo se implementó? | §Implementación: paquete `coordinacion` (planificador como función pura, coordinador como máquina de estados, registrador); paquetes del vehículo; herramientas de medida. Justificar la separación lógica-pura / ROS: es lo que hace verificable la coordinación sin simulador |
| ¿Cómo se integraron los subsistemas? | Integración progresiva documentada: contrato → dos agentes bajo namespace → coordinador → relevo. Incluir el **bloqueo de dominios DDS** y su resolución, porque es una decisión de integración no trivial |
| ¿Qué dificultades técnicas aparecieron? | Las cinco que importan: (1) **inobservabilidad longitudinal** del pasillo; (2) el **verificador de meta de Nav2** contando como fallo llegadas buenas; (3) el **tiempo de asignación medía cero por construcción**; (4) el **desajuste Humble/Jazzy**; (5) el bloqueo de dominios DDS |
| ¿Qué modificaciones fueron necesarias? | Reconstrucción de la matriz de requisitos; `stateful: False` + `yaw_goal_tolerance ≈ π` en el goal checker; etapa `RECIBIDA` publicada antes de planificar; `alpha` de AMCL de 0,2 a 0,01; esquema del registro de 1.0.0 a 1.1.0 para dar campo a RF-24 |
| ¿Cómo se verificó cada subsistema? | Tabla de verificación por requisito. Pruebas sin simulador para la lógica de coordinación; verificación sobre bag para la instrumentación; medida contra `/odom` para la navegación; medida sobre el vehículo para el sensado |
| ¿Cómo se validó el sistema completo? | La campaña de N = 30 del OE4 (S24), con el protocolo de la Actividad 4. Es el único artefacto que valida el sistema **completo**; todo lo anterior valida subsistemas |

---

## ACTIVIDAD 6 · Proyección del capítulo de resultados y discusión

**Objetivo específico seleccionado: OE4 — evaluación del desempeño del sistema.**

### 6.1 Condiciones de prueba

| ¿Qué se evaluó? | ¿Bajo qué condiciones? |
|---|---|
| Tiempo de respuesta, tiempo de asignación, tasa de éxito y continuidad entre niveles, sobre misiones completas origen→destino con cambio de nivel | Simulación Gazebo Classic 11 + ROS 2 Humble sobre `mundo_definitivo.world` (dos niveles, un `gzserver` y un agente Nav2 por nivel, un solo dominio DDS). N = 30 pares origen–destino **sorteados por semilla** sobre un catálogo de 16 destinos por nivel. Éxito medido contra `/odom`, tolerancia 0,25 m. RTF registrado por misión; descartes limitados a una lista cerrada con techo del 20 % |
| Caracterización del tiempo de asignación fuera de la misión | Banco dedicado, 4 corridas × 30 misiones, midiendo directamente la función de asignación sin pasar por el bag |
| Comportamiento del relevo entre niveles | Misión de dos tramos con los dos robots vivos, verificando que **ambos fueron conducidos** (conteo de mensajes en cada `cmd_vel`) y no meramente notificados |

### 6.2 Evidencias previstas

☑ Tabla ☑ Gráfica ☑ Curva experimental ☐ Fotografía técnica ☑ Simulación ☐ Esquemático ☑ Comparación
☑ Otra: **registro JSON por misión validado contra esquema versionado** (la evidencia primaria; las tablas y gráficas se derivan de él).

### 6.3 Métricas y comparación

| Elemento | Definición |
|---|---|
| **Métrica o indicador** | (1) Tiempo de respuesta [s]; (2) tiempo de asignación [s], reportado como **cota superior por misión** más caracterización en banco [µs]; (3) tasa de éxito [%] con IC de Wilson al 95 %; (4) continuidad entre niveles [booleano por misión → %] |
| **Comparación principal** | ☑ **Requisito** (principal) · ☑ Estado del arte (secundaria, para la discusión) |
| **Criterio de aceptación** | Llegada ≤ **0,25 m** contra `/odom`; tasa de éxito ≥ 90 % con la **cota inferior** del intervalo declarada explícitamente; continuidad ≥ 90 %; tiempo de asignación **< 100 ms**; campaña válida solo si los descartes no superan el 20 % |
| **Origen del criterio** | Objetivo específico 4 del anteproyecto aprobado (§4.2) y `PROTOCOLO_EXPERIMENTAL.md` §3, redactado antes de instrumentar. El umbral de 0,25 m proviene de la tolerancia de meta configurada en Nav2 y del tamaño del vehículo (0,28 × 0,19 m) |

### 6.4 Discusión — guion de lo que hay que responder

- **¿Por qué se obtuvo este comportamiento?** El relevo funciona porque ningún robot cruza de nivel: la transición es un **traspaso de responsabilidad**, no un desplazamiento. Eso elimina de raíz el problema que hace caro el enfoque de agente único.
- **¿Coincide con lo esperado?** En el mecanismo, sí. En la **precisión de llegada**, no del todo: hay un error residual documentado que el diseño no anticipaba.
- **¿Qué explica las diferencias?** La **inobservabilidad longitudinal** del pasillo. En un tubo uniforme la posición lateral está perfectamente restringida y la longitudinal no lo está: σx = **1,325 m** frente a σy = **0,213 m**, con una deriva de `map → odom` de **1,977 m** donde debía ser constante. Esto no es un fallo de AMCL sino una propiedad geométrica del entorno, y afecta por igual a la localización y a la odometría (`rf2o` registró solo el **5,7 %** y el **1,3 %** del desplazamiento real en los dos tramos). Mitigado en simulación bajando los `alpha` de AMCL de 0,2 a 0,01 (deriva de 0,0343 a 0,0049 m por metro recorrido, ~7×), **pero la degeneración sigue intacta**: lo que se quitó fue el ruido que la explotaba.
- **¿Cómo se relaciona con el diseño?** El criterio de éxito se decidió **contra `/odom` y no contra el `SUCCEEDED` de Nav2** precisamente porque se midió que el planificador declara fallos donde hubo llegadas buenas. Es una decisión de diseño experimental sostenida por evidencia, y hay que presentarla así.
- **¿Cómo se compara con literatura?** El algoritmo de asignación se clasifica como **ST–SR–IA** en la taxonomía de Gerkey & Matarić, con relevo en zona de transición. La comparación honesta es contra trabajos de coordinación multi-robot en 2D: el aporte no es el algoritmo sino su aplicación al eje vertical sin hardware de transición.
- **¿Qué limitaciones presenta?** Cuatro, y conviene decirlas antes de que las pregunten: (1) la campaña de dos niveles corre **en simulación**; (2) el tiempo de asignación **no es medible por misión** porque `/clock` late a 10 Hz y la asignación tarda ~0,15 ms — tres órdenes de magnitud por debajo de un tic, por eso se reporta como cota más banco; (3) **N = 30** produce intervalos anchos (27/30 da 74,4–96,5 %, no un número); (4) el LiDAR simulado (300°, cono ciego al morro, 600 muestras) **no es comparable** con el real (360°, 360 muestras), lo que limita la validez externa.

### 6.5 Juicio preliminar de cumplimiento

**Resultado obtenido / disponible:** una misión de relevo entre niveles completa y verificada
(`exito: true`, 1 relevo, 47,6 s, llegadas a 0,128 m y 0,077 m contra un criterio de 0,25 m, con 373
y 580 mensajes de mando en cada robot que prueban que ambos fueron conducidos), más la
caracterización del tiempo de asignación (mediana 154–175 µs, máximo 306,4 µs). **Cero de las 30
misiones de la campaña ejecutadas.**

☐ Cumple ☑ **Cumple parcialmente** ☐ No cumple todavía ☐ No existe evidencia suficiente

*Justificación del marcaje:* el mecanismo está demostrado y la instrumentación está completa y
verificada; lo que falta es la **evidencia estadística**, que es exactamente lo que el objetivo pide
al decir «evaluar el desempeño… utilizando métricas». n = 1 demuestra que funciona, no cuán bien.

---

## ACTIVIDAD 7 · De los resultados a las conclusiones

### Prueba preliminar de cierre

| Objetivo | Conclusión preliminar sustentable **hoy** | Evidencia que aún falta |
|---|---|---|
| **OE1** | «La arquitectura funcional del sistema colaborativo quedó especificada en 34 requisitos trazados a los cuatro objetivos y en un contrato de interfaces ROS 2 verificado en ejecución, cuya estrategia de asignación se validó sobre 992 planes origen–destino calculados sin simulador y se ejecutó de extremo a extremo el 2026-08-29, cuando dos solicitudes con destinos en niveles distintos produjeron dos agentes distintos.» | Ninguna esencial. Faltan los nombres definitivos de las salas del piso 2 |
| **OE2** | «La plataforma se instrumentó sobre AWS DeepRacer, verificando el sensado con una repetibilidad de pared de 2,8 mm y una frecuencia de barrido de 6,35 Hz una vez el LiDAR convive con la pila del vehículo (−6,6 % respecto a los 6,80 Hz de fábrica), y el control desde ROS 2 mediante `/ctrl_pkg/servo_msg`.» | **El segundo vehículo físico** y la comunicación inter-robot sobre hardware. Sin eso, la conclusión no puede decir «dos vehículos» en físico |
| **OE3** | **No formulable hoy.** Cualquier frase sería vaga | Todo: la interfaz, y la verificación de RF-17 a RF-20 sobre un teléfono real |
| **OE4** | «El relevo entre niveles se ejecutó de forma completa y verificada, manteniendo la continuidad del servicio en una misión de dos tramos con llegadas de 0,128 m y 0,077 m contra un criterio de 0,25 m medido sobre `/odom`, y el tiempo de asignación se caracterizó en banco con una mediana de 154–175 µs y un máximo de 306,4 µs.» **Lo que NO puede afirmarse aún:** ninguna tasa | **La campaña de N = 30.** Es el único faltante, y es el que convierte «funciona» en «funciona el X % de las veces» |

### Tabla de cierre

| Objetivo | Resultado principal | Evidencia cuantitativa | ¿Qué puede concluirse? | Limitación identificada |
|---|---|---|---|---|
| **OE1** | Arquitectura especificada y asignación por nivel ejecutada | 34 requisitos trazados; 992 planes verificados; round-trip DDS 18/18; 2 solicitudes → 2 agentes distintos | Que la arquitectura es **especificable, verificable y ejecutable**, no solo conceptual | Verificada en simulación; el nodo de coordinación aún no compila en la tarjeta Jazzy del vehículo |
| **OE2** | Plataforma física instrumentada (un vehículo) | 2,8 mm de repetibilidad; 6,80 → 6,35 Hz (−6,6 %); respuesta proporcional en dirección y tracción | Que el sensado y la locomoción del DeepRacer son adecuados para la tarea | **Un solo vehículo operativo**; el segundo en intervención técnica sin caracterizar desde el 2026-08-14. Desajuste Humble/Jazzy sin resolver |
| **OE3** | Ninguno | Ninguna | Nada aún | Objetivo no iniciado; se construye en S22 (7–13 sep) |
| **OE4** | Relevo entre niveles ejecutado y medido | `exito: true`; 1 relevo; 47,6 s; 0,128 m y 0,077 m contra 0,25 m; 373 y 580 mensajes de mando; asignación 154–175 µs | Que el mecanismo de relevo **funciona y es medible**, y que la instrumentación produce evidencia auditable | **n = 1 y sin sortear.** El protocolo pide N = 30. Además, la campaña de dos niveles es en simulación, y el tiempo de asignación no es medible por misión (`/clock` a 10 Hz) |

---

## ACTIVIDAD 8 · Revisión entre pares — jurado técnico

**Objetivo revisado: OE4.** Autoevaluación anticipando el interrogatorio del jurado.

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | ¿Dónde está la evidencia? | En los registros JSON por misión (`Documentos/Evidencia/registros/`), validados contra `esquema_registro_mision.json` v1.1.0, y en las actas de evidencia `S21_relevo_ejecutado.md` y `S21_banco_tiempo_asignacion.md` |
| 2 | ¿Qué variable demuestra el resultado? | Cuatro: tiempo de respuesta, tiempo de asignación, éxito de llegada (posición contra `/odom`) y continuidad entre niveles |
| 3 | ¿Cuál es la métrica? | Distancia euclídea al punto objetivo [m]; duración [s]; proporción de éxitos con intervalo de Wilson al 95 %; booleano de continuidad por misión |
| 4 | ¿Cuál es el criterio de aceptación? | Llegada ≤ 0,25 m; tasa de éxito y continuidad ≥ 90 %; asignación < 100 ms; descartes ≤ 20 % |
| 5 | ¿De dónde proviene el criterio? | Del objetivo específico 4 del anteproyecto aprobado y de `PROTOCOLO_EXPERIMENTAL.md` §3, **escrito antes de instrumentar**. El umbral de 0,25 m viene de la tolerancia de meta de Nav2 y del tamaño del vehículo |
| 6 | ¿Bajo qué condiciones se obtuvo? | Simulación Gazebo Classic 11 + ROS 2 Humble, `mundo_definitivo.world`, dos `gzserver`, un agente Nav2 por nivel, AMCL con `alpha = 0.01`, mapa `primer_piso_definitivo` |
| 7 | ¿El procedimiento puede reproducirse? | Sí: `RUNBOOK_CAMPANA.md` + la semilla del sorteo + el commit de congelación. El sorteo es determinista y el análisis no admite decisiones manuales |
| 8 | ¿Qué conclusión puede formularse? | Que el relevo entre niveles funciona y es medible. **No** que funcione con una tasa determinada |
| 9 | ¿Qué limitaciones presenta? | n = 1 y sin sortear; campaña de dos niveles en simulación; asignación no medible por misión; LiDAR simulado no comparable con el real |

**Dictamen:** ☐ DEMOSTRADO ☑ **PARCIALMENTE DEMOSTRADO** ☐ AÚN NO DEMOSTRABLE

**Observación principal del grupo revisor (autoevaluación):** *la instrumentación es más sólida que
el resultado. Existe una cadena de medida completa, auditable y con criterio escrito antes de medir
—lo cual es inusual y debe destacarse en la defensa— pero solo una corrida la ha atravesado. El
riesgo no es que la campaña salga mal, sino que no se ejecute a tiempo: la congelación de código es
S23 y la campaña es S24, sin holgura detrás.*

---

## PRODUCTO FINAL · Matriz de transición del anteproyecto al documento final

| Parte | Dónde queda resuelta |
|---|---|
| **A. Auditoría de secciones heredadas** | Actividad 1. Tres hallazgos que exigen aval del director (plataforma, tipo de interfaz, métricas de validación); 9 secciones clasificadas C/A/F/R |
| **B. Matriz objetivo-evidencia** | Actividad 2. Cuatro objetivos con evidencia, faltantes, métrica y ubicación. Semáforo: OE1 🟢, OE2 🟡, OE3 🔴, OE4 🟡 |
| **C. Metodología ejecutada** | Actividad 3. Diez aspectos con la decisión técnica que justifica cada desviación |
| **D. Proyección del documento final** | Actividades 4, 5, 6 y 7. Protocolo de la evidencia crítica, capítulo de desarrollo, capítulo de resultados y conclusiones sustentables |
| **E. Plan inmediato de trabajo** | §6 de este documento |

---

## 6. Plan inmediato de trabajo

### Prioridades identificadas

| Prioridad 1 | Prioridad 2 | Prioridad 3 |
|---|---|---|
| **Ejecutar la campaña de N = 30 (OE4).** Es el único faltante que separa «el mecanismo funciona» de «el objetivo está cumplido», y no tiene holgura: congelación S23, campaña S24 | **Construir la interfaz HRI (OE3).** Es el único objetivo en 0 % y una semana completa (S22) que no admite compresión. Se paraleliza con Jonny | **Obtener el aval del director sobre las tres desviaciones** (plataforma DeepRacer, interfaz web, reparto simulación/físico). Sin firma, tres secciones del documento final quedan en el aire |

### Acciones

| Acción requerida | Evidencia / resultado esperado | Prioridad | Responsable | Fecha prevista |
|---|---|---|---|---|
| Llevar al director las tres desviaciones de la Actividad 1 y dejar constancia escrita del aval | Acta o correo con el pronunciamiento sobre plataforma, interfaz y reparto simulación/físico | **Alta** | Santiago + Jonny | S21 — antes del 2026-09-06 |
| Construir la interfaz HRI web (QR → navegador, selección origen–destino, avisos de estado) | RF-17 a RF-20 verificados sobre un teléfono real, con captura de cada estado de misión | **Alta** | Jonny | S22 — 7 al 13 de septiembre |
| Ejecutar la campaña de N = 30 misiones sorteadas y correr el analizador | 30 registros JSON validados + informe con las cuatro métricas y sus intervalos de confianza | **Alta** | Santiago | S24 — 21 al 27 de septiembre |
| Caracterizar el segundo DeepRacer (R11): qué vehículo es, qué se intervino, cuándo vuelve | Constancia escrita. Si no vuelve, declarar la limitación de OE2 en el documento final | **Alta** | Jonny | S22 — antes del 2026-09-13 |
| Reescribir §7.2, §7.3 y §7.4 de la metodología con las tecnologías realmente usadas y su justificación | Sección «Metodología ejecutada» del documento final, con la tabla de la Actividad 3 | **Media** | Santiago | S25–S26 |
| Cerrar la comparación de cúspides que valida el cambio del verificador de meta de Nav2 | Comparación contra el registro del 21-ago; convierte un arreglo declarado en una medida | **Media** | Santiago | S23 — antes de la congelación |
| Incorporar al marco referencial la taxonomía de asignación multi-robot y el intervalo de Wilson | Dos secciones nuevas con citas, que permitan **discutir** y no solo describir los resultados | **Media** | Santiago | S26 |
| Podar del marco referencial visión computacional y las políticas CONPES, o declararlas fuera de uso | Marco referencial donde todo concepto incluido se usa después | **Baja** | Santiago | S29–S30 |

---

## 8. Lista de verificación de calidad

| Criterio | Sí | Parcial | No | Nota |
|---|:-:|:-:|:-:|---|
| El problema continúa siendo coherente con el proyecto ejecutado | ☑ | ☐ | ☐ | El planteamiento describe exactamente el relevo que se construyó |
| La justificación no promete impactos que el proyecto no puede demostrar | ☐ | ☑ | ☐ | Menciona movilidad inclusiva y accesibilidad, que **no se miden**. Hay que separar lo demostrado de lo potencial |
| Cada objetivo posee una evidencia asociada | ☐ | ☑ | ☐ | **OE3 no tiene ninguna** |
| Las evidencias permiten evaluar y no solamente mostrar actividades | ☑ | ☐ | ☐ | Todas las cifras son medidas contra referencia, no declaraciones. El `SUCCEEDED` de Nav2 se rechazó explícitamente como evidencia |
| Existen métricas para los principales resultados | ☑ | ☐ | ☐ | Las cuatro del OE4, con definición operacional escrita antes de instrumentar |
| Se han definido criterios de aceptación cuando corresponden | ☑ | ☐ | ☐ | 0,25 m; ≥ 90 %; < 100 ms; techo de descartes 20 % |
| La metodología describe lo realmente ejecutado | ☐ | ☐ | ☑ | §7.2 y §7.3 nombran CoppeliaSim, OpenCV, Jetson Nano y Raspbian, ninguno usado. **Es el peor criterio de la lista** |
| Los cambios metodológicos se encuentran técnicamente justificados | ☐ | ☑ | ☐ | Justificados en el repositorio; **falta trasladarlos al documento** y obtener el aval del director |
| Las pruebas son suficientemente reproducibles | ☑ | ☐ | ☐ | Sorteo determinista por semilla, esquema versionado, runbook y análisis sin decisiones manuales |
| Los resultados pueden relacionarse directamente con los objetivos | ☑ | ☐ | ☐ | Las cuatro métricas del protocolo son literalmente las cuatro que nombra el OE4 |
| Existe una proyección clara del capítulo de resultados y discusión | ☑ | ☐ | ☐ | Actividad 6 de este taller |
| Las futuras conclusiones pueden sustentarse mediante evidencia | ☐ | ☑ | ☐ | Tres de cuatro sí; **OE3 no admite conclusión alguna hoy** |
| Se identificaron limitaciones técnicas reales | ☑ | ☐ | ☐ | Inobservabilidad longitudinal, desajuste Humble/Jazzy, LiDAR sim ≠ real, segundo vehículo, n = 1 |
| Se identificaron asuntos que requieren revisión con el director | ☑ | ☐ | ☐ | Tres, en la tabla de hallazgos de la Actividad 1 |
