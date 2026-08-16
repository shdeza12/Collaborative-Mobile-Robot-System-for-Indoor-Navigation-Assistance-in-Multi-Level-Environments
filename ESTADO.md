# Estado del proyecto — tablero de trazabilidad

> Fuente única de verdad del avance. Se actualiza **al cerrar cada sesión de trabajo**, antes del commit.
> Documento de referencia: `Documentos/Anteproyecto_Jonny_Santi.pdf` (cronograma en Cap. 8).

| | |
|---|---|
| **Semana del cronograma** | S18 de 32 |
| **Fecha de corte** | 2026-08-15 |
| **Fases activas** | Fase 4 — Desarrollo (cerrando) · Fase 5 — Integración (S18–S23) |
| **Semanas restantes** | 15 (sustentación S28–S29, documento final S29–S32) |
| **Último entregable formal** | Semana 17 |
| **Entregables pendientes** | S16 |
| **Acta de directores** | ✅ *Actividad 1 – Corte 1* revisada y firmada por **Armando Mateus** el 2026-08-14 ([PDF](Documentos/Entregables/Actividad_1_Corte_1_Cronograma_2026-2_firmado.pdf)) |
| **Planificación vigente** | [`Documentos/CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md) |

---

## 1. Avance por objetivo específico

| ID | Objetivo específico (anteproyecto §4.2) | Avance | Evidencia verificable | Responsable |
|----|------------------------------------------|--------|------------------------|-------------|
| **OE1** | Modelar arquitectura funcional: requisitos, escenarios multipiso, asignación de tareas, esquema de comunicación | 🟡 40 % | `Documentos/Evidencia/arquitectura.png` (diagrama completo con protocolo de relevo). **Falta:** documento de requisitos funcionales numerados y matriz de trazabilidad | — |
| **OE2** | Plataforma robótica con **dos** vehículos: locomoción, sensado, procesamiento y **comunicación** | 🟡 40 % | Un robot en Gazebo, `deepracer_sim.launch.py`, stack de sensores validado (S14), SLAM 2D (S15). **Hardware (2026-08-05):** `deepracer-custom-car` instalado en Raspberry Pi 4 y en la tarjeta original del DeepRacer, **ambas sobre Ubuntu Server 24.04 con ROS 2 Jazzy** (confirmado 2026-08-14); acceso por red a ambas; locomoción verificada desde la interfaz web. **La simulación es Humble: el desajuste de distribución es un hecho, no una hipótesis — ver R8.** **Falta:** sensado con LiDAR físico, control desde ROS 2 en vez de la web, namespaces, servidor de coordinación, comunicación inter-robot | — |
| **OE3** | Interfaz HRI web responsiva (selección origen–destino) | 🔴 0 % | Ninguna | — |
| **OE4** | Evaluación con métricas: tiempo de respuesta, tiempo de asignación, tasa de éxito, continuidad entre niveles | 🔴 0 % | Ninguna. No existe instrumentación ni protocolo experimental | — |

**Lectura:** a S18 de 32 (56 % del calendario) el avance técnico agregado está cerca del 25 %. El aporte declarado del proyecto —coordinación inter-robot y protocolo de relevo— aún no tiene implementación. La planificación de S17–S32 lo sitúa entre S20 y S22.

---

## 2. Camino crítico

Ordenado por dependencia. Nada de lo que sigue puede saltarse. La columna *Semana* remite al [cronograma vigente](Documentos/CRONOGRAMA_S17_S32.md).

| # | Hito | Bloquea a | Semana | Estado |
|---|------|-----------|--------|--------|
| 1 | **Contrato de interfaces ROS 2** (namespaces, acciones, tópicos) | Todo el desarrollo posterior | S17 | 🟢 Verificado en simulación el 2026-08-14: dos robots navegan bajo namespace con mando aislado ([`S17_nav2_namespaces.md`](Documentos/Evidencia/S17_nav2_namespaces.md), resultado 4) |
| 2 | **Entorno de dos niveles en Gazebo** con zona de transición vertical | Mapas, navegación, relevo | S18 | 🟢 Cerrado 2026-08-14: `primer_piso_dos_niveles.world` ([`S18_entorno_dos_niveles.md`](Documentos/Evidencia/S18_entorno_dos_niveles.md)) |
| 3 | **Navegación autónoma punto a punto** con restricción Ackermann | Guiado, relevo, métricas | S19 | 🟢 Validada también en el nivel 2: 4,79 m sobre un objetivo de 5,0 m, con z constante a 1,9 µm |
| 4 | **Segundo agente + servidor de coordinación** | OE2, protocolo de relevo | S19–S20 | 🔴 No iniciado |
| 5 | **Protocolo de relevo** (máquina de estados) | OE4, núcleo del aporte | S21 | 🔴 No iniciado |
| 6 | **Interfaz HRI** web sobre `rosbridge_suite` | OE3 | S22 | 🔴 No iniciado |
| 7 | **Instrumentación de métricas** | OE4, Fase 6 | S20–S21 | 🔴 No iniciado |
| 8 | **Bring-up de los dos DeepRacers** y despliegue del stack | Demostración física de OE2 | S21–S22 | 🟡 Custom car instalado; falta ROS 2 y LiDAR |

El hito 2 decía «réplica del laboratorio GED, dividida en dos zonas». [`ENTORNO_DE_EVALUACION.md`](Documentos/ENTORNO_DE_EVALUACION.md) §5 descartó el laboratorio como entorno de evaluación —16 m² en un solo nivel, sin discontinuidad vertical: la pregunta de investigación no se puede plantear ahí— y adoptó `primer_piso` replicado en dos niveles. El laboratorio sigue en el escalamiento como **etapa 2** (validación de hardware), no como entorno de evaluación.

---

## 3. Decisión de alcance vigente

**Estrategia adoptada (2026-08-05): la simulación produce la evidencia estadística; el hardware produce la demostración.** Sustituye a la versión del 2026-08-03. Desarrollo completo en [`Documentos/CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md) §4.

| ID | Decisión |
|----|----------|
| D1 | Las cuatro métricas de OE4 se miden en **simulación con N = 30**. Los vehículos físicos ejecutan el protocolo con N de 5 a 10, como demostración funcional. *Razón:* una tasa de éxito exige N. Con 5 corridas y 4 aciertos el IC del 95 % va de 38 % a 96 %; con 30 y 27 aciertos va de 80 % a 97 % |
| D2 | **Un piso es una región navegable con mapa y agente propios; la transición es un evento lógico.** En el esquema de relevo ningún robot cruza entre niveles, luego la frontera no necesita ser vertical. Se declara como simplificación explícita en el documento final |
| D3 | **Escalamiento en tres etapas.** (1) Simulación sobre `primer_piso_dos_niveles.world`: aporta la evidencia estadística. (2) **Laboratorio GED**: puerta de validación del hardware —los vehículos deben andar ahí antes de salir—, no entorno de evaluación. (3) **Pasillo real del primer piso USTA**: produce la evidencia física, porque es la geometría que el mundo simulado replica. *Revisado 2026-08-14* |
| D4 | El mundo simulado replica el **primer piso real del edificio**, no el laboratorio. Es lo que hace comparables los dos conjuntos de datos. El nivel 2 no es una licencia: el segundo piso real es idéntico al primero y la zona de transición derivada de la geometría resultó ser el descanso de la escalera real. *Revisado 2026-08-14* |
| D5 | La interfaz HRI es **web responsiva** sobre `rosbridge_suite`, accedida desde un teléfono. No es un recorte: §7.2 del anteproyecto lista "JavaScript, PHP, HTML" y "dispositivos móviles" |
| D6 | El código se escribe **una vez contra un contrato de interfaces ROS 2** y se despliega en dos destinos. Coordinación, relevo, HRI e instrumentación operan contra `/robot1/...` y `/robot2/...` sin conocer el backend |

> ✅ **Presentadas y en acta.** El entregable *Actividad 1 – Corte 1* —cronograma S17–S32, matriz
> objetivo–evidencia, hitos y desviaciones— lleva **constancia de revisión firmada por Armando
> Mateus con fecha 2026-08-14**, dentro del plazo (antes de S19). Su observación literal:
> *«Se ha desarrolla un buen avance. Uno de los DeepRacers está esta semana en intervención
> técnica.»* Archivo:
> [`Actividad_1_Corte_1_Cronograma_2026-2_firmado.pdf`](Documentos/Entregables/Actividad_1_Corte_1_Cronograma_2026-2_firmado.pdf).
>
> **Alcance exacto de lo firmado:** la constancia recoge **un solo director**. Ospina y Gélvez no
> firman este documento, y las decisiones D1–D6 no aparecen enumeradas en la constancia: lo que
> está avalado es el cronograma replanificado y la matriz objetivo–evidencia, que son el vehículo
> de esas decisiones. No se debe citar como aprobación de los tres directores.
>
> ⚠️ **El acta se firmó sobre una versión anterior del entorno.** Su fecha de corte es el 13 de
> agosto y el entorno de dos niveles se adoptó el 14. En consecuencia la actividad 12 del
> cronograma firmado dice «medir el laboratorio GED y modelar su planta en SDF», y la matriz
> objetivo–evidencia de OE1 cita `laboratorio_ged.world`. **Eso quedó superado por D3 y D4
> revisadas**: el entorno de evaluación es `primer_piso_dos_niveles.world`. No es un
> incumplimiento —el producto verificable existe y es mejor que el prometido— pero **debe
> comunicarse a los directores en el próximo corte**, no darse por sabido.

---

## 4. Riesgos abiertos

| ID | Riesgo | Impacto | Mitigación | Estado |
|----|--------|---------|------------|--------|
| R1 | **Ningún mapa obtenido es utilizable.** Mejor resultado: 41,9 % de cobertura en X y una extensión en Y de 16,5 m contra los 5,3 m reales del pasillo | **Degradado el 2026-08-05:** ya no bloquea. Afecta solo al pasillo USTA, que pasó a escenario secundario | **Causa raíz confirmada:** `max_laser_range` de slam_toolbox estaba en 12,0 m, por encima del alcance físico del LiDAR (10,0 m). Los rayos sin retorno volvían como 10,0 m, quedaban bajo el umbral y se rasterizaban como paredes fantasma en arcos de 10 m de radio. Corregido a 9,5 m el 2026-08-03 | 🟢 Fuera del camino crítico |
| R7 | **El código que se ejecuta no es el que está versionado.** `~/deepracer_sim_ws/src/aws-deepracer` era una copia independiente del repositorio, no un enlace | Las correcciones no surten efecto; hay trabajo que nunca llega al historial | **Se dio por cerrado el 2026-08-03 sin estarlo.** La verificación de entonces comprobó que `install/` resolvía a `src/` —cierto— pero no que `src/` fuera a su vez una copia. Lo era: un clon de `aws-deepracer/aws-deepracer.git` con cambios locales. Cerrado de verdad el 2026-08-05 sustituyendo la copia por un enlace simbólico al repositorio, con `colcon build` limpio (7/7) y comprobando que `readlink -f` de un archivo instalado apunta a la raíz del repositorio | ✅ Cerrado (2026-08-05) |
| R2 | **Ackermann vs. Nav2.** El controlador por defecto (DWB) asume tracción diferencial; el DeepRacer no gira sobre su eje | Trayectorias inejecutables | Resuelto en el stack publicado en `integracion-nav2`: Smac Hybrid-A\*, árboles de comportamiento propios sin `<Spin>`, `use_rotate_to_heading: false`, footprint real 0,28 × 0,19 m. **Sin verificar:** el cambio a `REEDS_SHEPP` + `allow_reversing` que se hizo tras abortar el goal (−5, 1.5) con "Resulting plan has 0 poses" | 🟡 Mitigado, verificación pendiente |
| R3 | **Ambigüedad de localización.** Pasillo largo de paredes lisas y repetitivas → AMCL propenso a divergir | Falsos negativos en las métricas de OE4 | Evaluar landmarks en el mundo o fusión con odometría visual | 🟡 Identificado |
| R4 | **Pared sur abierta en el SDF** deja celdas desconocidas | Afecta planificación, no solo el mapa | Cerrar la geometría en `primer_piso_v2.world` | 🟡 Identificado (desde S14) |
| R5 | **Fases 2 y 3 sin artefacto verificable.** No existe documento de requisitos | Imposibilita §7.4 del anteproyecto ("comparación con requisitos") | Reconstruir la matriz RF↔OE↔prueba. **Programado para S18; no se hizo, pasa a S19** | 🔴 Abierto |
| R6 | **Discrepancias informe ↔ repositorio** (ver §5) | Credibilidad de la evidencia ante el jurado | Corregir en el entregable de cierre de fase | 🔴 Abierto |
| R8 | **Desajuste de distribución.** El stack de simulación es ROS 2 Humble; `deepracer-custom-car` sobre Ubuntu 24.04 es Jazzy. Los parámetros de Nav2 y varias API cambian entre ambas | Puede invalidar el supuesto de D6: que el mismo código se despliega en los dos destinos sin cambios | Caracterizarlo en el spike, pregunta 4. Si el desajuste es grande, mantener una variante de configuración por distribución | 🔴 **Confirmado 2026-08-14** (los dos vehículos son Jazzy), sin caracterizar. Programado para S18, **el spike no se corrió**: pasa a S19 |
| R10 | **El mapa por defecto de Nav2 no pasa la verificación del propio proyecto.** `herramientas/verificar_mapa.py` **rechaza** los dos mapas de `primer_piso` contra su `.world`: cobertura en X del 35,5 % (mínimo 85 %), extensión en Y de 15,0 m contra los 5,3 m reales y 62,8 % de celdas desconocidas | La instalación queda verificada y compila, pero cualquier métrica de navegación obtenida sobre este mapa es discutible ante el jurado. No bloquea el bring-up ni la capa de coordinación | Resuelto por otra vía que la prevista: en vez de rehacer el SLAM, `herramientas/generar_mapa_desde_mundo.py` deriva el mapa de la geometría del `.world` (commit `35c47da`). El mapa vigente es `primer_piso_definitivo`, y `python3 herramientas/verificar_mapa.py Robot/aws-deepracer/deepracer_bringup/maps/primer_piso_definitivo.yaml primer_piso_v2.world` devuelve **0**: cobertura 99,7 % en X y 100,8 % en Y, 14,5 % de celdas desconocidas y **0 de 5149 obstáculos sin pared real** a menos de 0,30 m. El entorno que importa para OE4 es ahora `primer_piso_dos_niveles.world` (hito 2), y **no necesita un mapa propio**: los dos niveles son la misma planta en las mismas x-y, así que `primer_piso_definitivo.yaml` sirve para ambos, y así se validó el 2026-08-14 | 🟢 Cerrado 2026-08-14 (detectado 2026-08-11) |
| R11 | **Uno de los dos DeepRacers está en intervención técnica.** Consta por escrito en la observación del director en el acta del 2026-08-14: *«Uno de los DeepRacers está esta semana en intervención técnica»*. No se sabe cuál vehículo, qué falla ni cuánto dura | Bloquea la **pregunta 3 del spike** (latencia de ida y vuelta entre los dos vehículos, exige los dos encendidos en la misma red) y la actividad de **paridad entre vehículos** de S19. No bloquea las preguntas 1, 2 y 4, que se responden con **un solo** vehículo | Reordenar el spike: correr primero las preguntas 1, 2 y 4 sobre el vehículo disponible y dejar la 3 supeditada a la reparación. Jonny debe declarar por escrito qué vehículo es, qué se intervino y en qué fecha vuelve a estar operativo | 🔴 **Abierto (2026-08-14)**, sin caracterizar |
| R9 | **Capacidad insuficiente.** El trabajo pendiente suma 9–10 semanas-persona y el calendario ofrece 7 | Se llega a octubre sin capa de coordinación, que es el aporte declarado | Reparto en dos frentes entre S18 y S21, y escalera de recortes en §9 del cronograma. Punto de decisión go/no-go en S21 | 🟡 Mitigado por planificación |

---

## 5. Discrepancias detectadas entre informes y artefactos

Registradas el 2026-08-03 para corrección explícita:

| Informe dice | Artefacto en disco | Acción |
|---|---|---|
| S15: mapa guardado como `primer_piso_mapa.pgm/.yaml` vía servicio `/slam_toolbox/save_map` | `primer_piso.pgm/.yaml`; la guía operativa instruye `map_saver_cli` | Unificar nombre y procedimiento |
| S15 Tabla 1 y §5: `resolution = 0.05` m/celda | `primer_piso.yaml` declara `resolution: 0.06` | Corregir el informe o regenerar el mapa |
| S15 §3.4: "la extensión del mapa es consistente con las dimensiones del pasillo (44 m × 5 m)" | El mapa cubre 23,0 m × 15,7 m | Afirmación no sostenida por el artefacto |
| S15 Tabla 2: "Captura del quiebre en L — Satisfactorio" | No es identificable en el mapa guardado | Reevaluar tras repetir el mapeo |
| S15 Tabla 1: `minimum_travel_distance = 0.5`, `minimum_travel_heading = 0.5` | El archivo declaraba `0.1` y `0.57` | Corregir el informe con los valores vigentes |
| S15 §3.1: "modo *online asynchronous*" | El launch instancia `sync_slam_toolbox_node` (nodo **síncrono**) | Corregir el informe |
| S15 §3.4: las aperturas de la pared sur explican las celdas desconocidas | La causa real es deriva de pose por parámetros mal dimensionados | Rehacer el análisis de la sección |
| Bitácora 2026-08-03: `max_laser_range` 12,0 → 9,5 y buffers de SLAM reajustados al pasillo | El workspace en ejecución conservaba `max_laser_range: 12.0`, `scan_buffer_maximum_scan_distance: 0.5` y `link_scan_maximum_distance: 0.75` | Los arreglos existían **solo en el repositorio**; el simulador nunca los ejecutó (ver R7). Corregido el 2026-08-05. **Todo resultado de mapeo anterior a esa fecha se obtuvo con la configuración vieja y no puede citarse como evidencia de los parámetros corregidos** |

---

## 6. Desviaciones respecto al anteproyecto

Deben justificarse por escrito en el documento final:

| Anteproyecto | Realidad | Justificación |
|---|---|---|
| §4.3: pruebas "en un entorno interior con multiples pisos" | **En simulación no hay desviación:** `primer_piso_dos_niveles.world` tiene dos pisos reales, separados 3,0 m en vertical, con zona de transición. **La desviación queda solo en la parte física:** las corridas con vehículo real ocurren en un único piso —el pasillo del primer piso USTA— porque no hay forma de subir un DeepRacer por una escalera | Corregido el 2026-08-14; la redacción anterior («laboratorio GED, un solo nivel dividido en dos zonas») describía un entorno que se descartó. La justificación se estrecha y se refuerza: el aporte del proyecto es que **ningún robot cruza entre niveles** —la transición es un relevo, no un desplazamiento—, de modo que la campaña física de un solo piso sigue ejercitando el protocolo completo salvo el traslado vertical del vehículo, que el diseño no contempla. La campaña de N = 30 con los dos niveles reales corre en simulación (D1) |
| §4.3: "una aplicación móvil que actuará como interfaz HRI" | Interfaz web responsiva sobre `rosbridge_suite`, accedida desde el navegador de un teléfono | §7.2 lista como software del proyecto "JavaScript, PHP, HTML" y como hardware "dispositivos móviles": la pila declarada era web desde el anteproyecto. OE3 exige selección de origen y destino y eso se cumple íntegro. **Aun así es una desviación y debe declararse**: no es una aplicación nativa |
| Plataforma DonkeyCar (presupuesto: chasis, PCA9685) | AWS DeepRacer | Pendiente de redactar |
| Simulador CoppeliaSim | Gazebo Classic 11 | Pendiente de redactar |
| ROS 2 "Humble o Jazzy" | Humble | Cerrar la ambigüedad |

---

## 7. Bitácora de decisiones

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-08-03 | Se restablece el vínculo git del directorio local con el repositorio remoto | El directorio de trabajo era una copia sin historial; `primer_piso_v2.world` (18-jun) llevaba 7 semanas sin respaldo |
| 2026-08-03 | Se adopta `ESTADO.md` como tablero único de trazabilidad | Los informes semanales registraban actividad, pero no el estado agregado frente a los objetivos |
| 2026-08-03 | Alcance: validación en simulación, hardware como demostración | Ver §3 |
| 2026-08-03 | Se reajustan los parámetros de `slam_toolbox.yaml` al tamaño real del entorno | `scan_buffer_maximum_scan_distance` (0.5→10.0), `link_scan_maximum_distance` (0.75→10.0) y `loop_search_maximum_distance` (3.0→8.0) eran valores de una pista de carreras; impedían enlazar nodos y cerrar bucle en un pasillo de 58 m |
| 2026-08-03 | Se incorpora `herramientas/verificar_mapa.py` como paso obligatorio antes de guardar un mapa | Ningún mapa vuelve a declararse "satisfactorio" sin verificación objetiva de cobertura y deriva |
| 2026-08-03 | `max_laser_range` de slam_toolbox: 12,0 → 9,5 m | Debe quedar por debajo de los 10,0 m del LiDAR (`deepracer.xacro`). Con 12,0 los rayos sin retorno se tomaban como impactos válidos y generaban paredes inexistentes |
| 2026-08-03 | `map_saver_cli` requiere `--ros-args -p use_sim_time:=true` en simulación | Sin ese parámetro agota su espera de 2 s y falla con `Failed to spin map subscription`. Diagnóstico por descarte: `/map` publicaba a 2 Hz con QoS `TRANSIENT_LOCAL` correcta |
| 2026-08-03 | Se declaran en `deepracer_bringup/package.xml` las dependencias de ejecución que estaban implícitas | `slam_toolbox`, `nav2_map_server`, `gazebo_ros` y otras se lanzaban sin declararse: `rosdep install` no las instalaba en un equipo nuevo |
| 2026-08-03 | README reescrito con procedimiento de instalación reproducible | El workspace debe enlazar el repositorio, no copiarlo, para que el código compilado sea el versionado |
| 2026-08-04 | El trabajo Nav2 + AMCL se publica en la rama `integracion-nav2` (commit `1242651`) sobre `origin/main` | Siete semanas de avance vivían sin commitear. Se resolvió por rama y no sobre `main` porque el historial local diverge del remoto y la rama es compartida con Jonny |
| 2026-08-05 | `deepracer-custom-car` instalado en Raspberry Pi 4 y en la tarjeta original del DeepRacer; locomoción verificada por interfaz web | Primer avance de OE2 sobre hardware real. Sube OE2 de 25 % a 40 %. Evidencia audiovisual: <https://youtu.be/ZGfAMnC4lYY> |
| 2026-08-05 | Se replanifica S17–S32 y se emite `Documentos/CRONOGRAMA_S17_S32.md` | Entregable exigido por el espacio académico Proyecto de Grado 2. La sustentación quedó en S28–S29 y el documento final se traslada después de ella, lo que saca la redacción del camino crítico |
| 2026-08-05 | Entorno experimental: laboratorio GED en lugar del pasillo USTA de dos pisos | El anteproyecto pide "entorno interior controlado" (OE4) y "condiciones controladas" (§4.3). Elimina la dependencia de permisos de acceso y retira el riesgo R1 del camino crítico |
| 2026-08-05 | El bring-up físico completo se mantiene en S21–S22, pero se antepone un **spike acotado de 3–4 días en S18** | El beneficio de adelantar el hardware es obtener información, no avance, y eso cuesta días y no semanas. Adelantar el bring-up entero arriesga llegar a octubre con dos robots andando y sin capa de coordinación que sustentar |
| 2026-08-05 | El trabajo se reparte en dos frentes entre S18 y S21 | El trabajo pendiente suma 9–10 semanas-persona y el calendario ofrece 7 semanas. Sin reparto no cierra |
| 2026-08-05 | Se emite `Documentos/CONTRATO_INTERFACES.md` (hito H1) | Congela namespaces, marcos TF, acciones y tipos de mensaje antes de escribir el nodo de coordinación y la HRI. Materializa D6: un solo código contra dos backends |
| 2026-08-05 | Cada robot tiene su propio árbol TF con raíz `robotN/map`; **no** hay marco global compartido | Ningún robot cruza entre niveles (D2): la transición es un evento lógico del protocolo de relevo, no un movimiento. Un `map` compartido resolvería un problema que el sistema no tiene y complicaría el bring-up |
| 2026-08-05 | El coordinador manda a los robots **únicamente** por la acción `navigate_to_pose`; nunca publica `cmd_vel` | Es lo que hace intercambiable un robot físico con uno simulado sin tocar el coordinador |
| 2026-08-05 | La HRI habla solo con `/coordinacion`, nunca con los robots | Mantiene mínima la superficie de `rosbridge` y permite reasignar robots sin tocar el frontend |
| 2026-08-05 | Se elimina el `static_transform_publisher` `base_link`→`camera_link` de `deepracer_spawn.launch.py` | Disputaba el marco `camera_link` con el URDF: en TF2 un marco solo admite un padre. Las dos transformadas **no coincidían** (15,39 mm de diferencia; rotación idéntica). En simulación manda el URDF, porque es lo que Gazebo usa para colocar el sensor. Era una copia del launch del robot físico, donde sí es la única fuente de TF |
| 2026-08-05 | `~/deepracer_sim_ws/src/aws-deepracer` pasa de copia a enlace simbólico al repositorio | Cierre real de R7. La copia era un clon de `aws-deepracer/aws-deepracer.git` con cambios sin commitear, y llevaba retrasada respecto al repositorio en los 6 archivos que diferían. `colcon build` limpio, 7/7 |
| 2026-08-05 | Se instrumenta la verificación con `herramientas/verificar_contrato.py` | El criterio de cierre de H1 pasa de afirmación a comprobación ejecutable. Su primera ejecución detectó por sí sola el conflicto de `camera_link` |
| 2026-08-05 | El namespaceado se aplica por pasos, cada uno con valor por defecto vacío y prueba previa de que **no cambia nada** | Separa el error de mecánica del error de diseño: si con el defecto vacío algo se rompe, la causa es la mecánica. Bitácora de aplicación en [`Documentos/Evidencia/S17_aplicacion_contrato.md`](Documentos/Evidencia/S17_aplicacion_contrato.md) |
| 2026-08-05 | Los marcos `odom`, `base_link` y `laser` se prefijan desde el xacro y no desde `robot_state_publisher` | Los escriben plugins de Gazebo, que ignoran el parámetro `frame_prefix`. Los otros 10 marcos del URDF sí los prefija `robot_state_publisher` |
| 2026-08-10 | Nav2 y AMCL quedan bajo espacio de nombres: `deepracer_localization_sim.launch.py` propio en vez de `nav2_bringup/localization_launch.py` | El de Nav2 no namespacea sus nodos —solo anida el YAML— y remapea `/tf` de forma fija, lo que parte el árbol TF bajo namespace. Evidencia en [`Documentos/Evidencia/S17_nav2_namespaces.md`](Documentos/Evidencia/S17_nav2_namespaces.md) |
| 2026-08-11 | El trabajo de `integracion-nav2` se publica en `main` y se etiqueta `v0.1-simulacion-verificada` | Néstor (codirector) necesita una versión instalable. `main` es lo que obtiene un clon sin argumentos y por eso debe funcionar siempre; el tag fija un punto reproducible. Comprobado clonando desde GitHub en limpio: `rosdep` sin faltantes, `6 packages finished`, verificador 30/0 |
| 2026-08-11 | Se declara en `deepracer_bringup/package.xml` la dependencia real `deepracer_drive_plugin` (decía `deepracer_gazebo`, que no existe) | `rosdep install` abortaba en un equipo nuevo. El paquete se llamaba así en el proyecto original de AWS |
| 2026-08-11 | Se incorpora `herramientas/verificar_instalacion.sh` (30 comprobaciones, sin levantar Gazebo ni nodos) | Unas instrucciones de instalación se prueban una sola vez, en el equipo de quien las escribió, donde todo ya funcionaba. Cada fallo imprime el comando que lo corrige |
| 2026-08-11 | La raíz del repositorio se **deduce** de la ubicación real de cada archivo (`realpath`), y se eliminan los candidatos adivinados bajo `$HOME` | Con ruta fija, en un equipo que clonara en otro sitio Gazebo abría un mundo VACÍO sin error; y si existía otra copia en la ruta adivinada, se cargaban en silencio los mundos del clon equivocado. Pasó de verdad: el launch resolvió a una copia de `~/Tesis` del 4-ago |
| 2026-08-11 | Se incorpora `herramientas/verificar_repositorio.sh`: 10 comprobaciones sobre los **documentos**, no sobre el código | Había 30 comprobaciones sobre el código y ninguna sobre la documentación: por eso el código convergía y los documentos divergían. Detecta rutas de una máquina concreta, instrucciones que mandan copiar el workspace, archivos citados que no existen, enlaces rotos y contradicciones entre el README, los launch y `ESTADO.md` |
| 2026-08-11 | Se retiran de las guías y planes las 14 rutas con el nombre de usuario incrustado, y los dos bloques `rsync` de `guia_navegacion_nav2.md` | El `rsync` reproducía el incidente R7: sincronizar al workspace lo que ya está enlazado. Una versión descargada tiene que funcionar entera, sin depender de dónde se haya clonado |
| 2026-08-11 | `deepracer_sim.launch.py` deja de exigir `world:=` a mano y la deducción de la raíz pasa a un solo módulo, `launch/deepracer_raiz_repo.py`, que ambos launch importan | Escribir la ruta absoluta en cada lanzamiento hacía trivial mapear contra la geometría de **otra** copia del repositorio sin enterarse; pasó el 2026-08-11 con `~/Tesis`, un clon del 4-ago. La lógica va en un módulo y no copiada en cada launch: dos copias de la misma regla divergen sin avisar |
| 2026-08-11 | **Mundo vigente: `primer_piso_v2.world`**, con `primer_piso_v2.yaml` como mapa por defecto de Nav2 | El README lo declaraba vigente mientras el launch cargaba `primer_piso.world` con el mapa de v1. Mundo y mapa van en pareja: descasarlos hace que AMCL localice contra una geometría distinta de la simulada, y la deriva resultante no se parece a un error de configuración |
| 2026-08-12 | Todo consejo que modifica `~/.bashrc` se emite como **comando pegable en su propia línea**, con guarda `grep -qxF` y el valor entrecomillado | Al instalar en un segundo equipo el `~/.bashrc` quedó inservible: dos órdenes pegadas en una línea (`export ... source ...` → `not a valid identifier`) y la misma línea repetida hasta cuatro veces. Dos causas: el verificador daba el consejo como prosa dentro de un párrafo, imposible de copiar de un tirón, y el paso 5 del README no comprobaba antes de añadir. La revisión encontró además que un rótulo `Ejecutar: ` **delante** del comando reproducía el fallo —al arrastrarlo, el `||` toma el error como "no estaba" y añade igual, una vez por intento— y que un `grep -q` sin `-x` daba por buena una línea ya corrupta, de modo que **no reparaba** el archivo de quien más lo necesitaba |
| 2026-08-12 | **El mapa por defecto de Nav2 pasa a `primer_piso_definitivo.yaml`, derivado de la geometría del `.world`** con `herramientas/generar_mapa_desde_mundo.py`, en vez de un mapa construido con SLAM | `primer_piso_v2.pgm` tenía **2688 de 3618 celdas ocupadas (74 %) sin ninguna pared real detrás**: paredes que el SLAM se inventó por su propia deriva. Como el planificador trata esas celdas como espacio letal, Nav2 abortaba con `Starting point in lethal space` en tramos del pasillo que están libres. No se ve mirando el mapa; se ve mucho después y con otro nombre. El mapa nuevo pasa `verificar_mapa.py` con 99.7 % de cobertura y **0 obstáculos falsos**, y la deriva de AMCL medida contra `/odom` bajó de 0.323 m a 0.045–0.100 m |
| 2026-08-12 | Un `SUCCEEDED` de Nav2 **no** se acepta como evidencia: toda medida de navegación se contrasta con `/odom`, que el plugin calcula con `model_->WorldPose()` | `Reached the goal!` lo emite el controlador comparando contra la pose que le da AMCL. Con el mapa inventado, Nav2 devolvía `SUCCEEDED` sobre una pose que no era la real: el robot no había llegado, y en un caso ni se había movido. La verdad del simulador es lo único que no depende de lo que se está midiendo |
| 2026-08-12 | AMCL recibe la pose de spawn (`x`, `y`, `yaw`) desde el launch, y los costmaps reciben el `scan` con el namespace ya resuelto | Dos defectos que solo aparecían con namespace y ninguno daba error. (1) `initial_pose: [0.0, 0.0, 0.0]` era una **línea muerta**: AMCL declara `initial_pose.x/.y/.z/.yaw` por separado y ROS descartaba la lista en silencio (`ros2 param get /amcl initial_pose` → `Parameter not set`), así que un robot lanzado con `y:=2.0` arrancaba con 2 m de error y AMCL arrastraba la nube de partículas al avanzar. (2) `topic: /scan` es absoluto y Nav2 en Humble **no** resuelve namespaces en las capas del costmap —el propio `nav2_bringup` lo esquiva escribiendo `/robot1/scan` a mano en un YAML por robot—, de modo que los dos costmaps se suscribían a un topic sin publicador y el robot solo esquivaba lo que ya estaba en el mapa estático. Verificado: `/robot1/scan` pasó de 1 a 3 suscriptores |
| 2026-08-14 | El entorno de evaluación pasa a ser **`primer_piso_dos_niveles.world`**: `primer_piso` extraído a modelo reutilizable e instanciado dos veces, a z=0 y z=3,0, con losa propia para el nivel 2 y la zona de transición en (41,40 · 3,03) | El laboratorio GED no sirve como entorno de evaluación (16 m², un solo nivel, sin discontinuidad vertical). Replicar la planta con desplazamiento vertical **no es una simplificación**: el segundo piso real del edificio es idéntico al primero, y el recinto del que se dedujo geométricamente la zona de transición resultó ser el descanso de la escalera real. Validado navegando en el nivel 2: 4,79 m sobre un objetivo de 5,0 m con la z constante a 1,9 µm — necesario porque las dos plantas son idénticas y el LiDAR no las distingue: un robot caído al nivel 1 daría el mismo `/scan` |
| 2026-08-14 | **Se descarta mapear el nivel 2.** El mapa vigente sirve para los dos niveles | Un segundo mapa de la misma geometría solo puede divergir del primero. Vale mientras las dos plantas sean idénticas, que es el caso real del edificio |
| 2026-08-14 | `herramientas/generar_mapa_desde_mundo.py` solo cuenta como pared las cajas dentro de `<collision>` | Tomaba el primer `<box>` del enlace fuera cual fuera su contenedor, de modo que un enlace con visual y sin colisión —la zona de transición— habría salido como obstáculo en el mapa. Un obstáculo fantasma no da ningún error: AMCL converge y Nav2 acepta objetivos igual; el síntoma aparece después como una ruta que rodea algo que no existe. Comprobado que no altera el mapa vigente: mismas 12 paredes |
| 2026-08-14 | Los bloques `<model>` y `<state>` de `primer_piso_v2.world` **no se contradecían** | En `35c47da` se registró una discrepancia de ~21 m entre ambos. No la hay: las poses de `<state>` son absolutas y las de `<model>` relativas al modelo; restando la pose del modelo coinciden en los doce muros con residuo < 0,1 mm. Lo desplazado era el bloque entero, no la geometría. Importa porque de ahí salía la duda de si el mapa correspondía a lo simulado: sí corresponde |
| 2026-08-14 | **Acta firmada.** Armando Mateus emite constancia de revisión sobre *Actividad 1 – Corte 1*: cronograma S17–S32, matriz objetivo–evidencia, nueve hitos y tabla de desviaciones | Cierra el pendiente de §3 dentro del plazo (antes de S19) y cubre la actividad 5 del cronograma. Deja dos cosas registradas: que la firma es de **un** director y no de los tres, y que el documento firmado tiene fecha de corte del 13-ago, un día antes de adoptar el entorno de dos niveles — su actividad 12 y su matriz de OE1 siguen citando el laboratorio GED |
| 2026-08-14 | Se registra como riesgo **R11** que uno de los dos DeepRacers está en intervención técnica | Lo declara el director por escrito en el acta. Cambia el orden del spike de S19: las preguntas 1, 2 y 4 se responden con un solo vehículo; la 3 —latencia entre vehículos— exige los dos y queda supeditada a la reparación. Sin registrarlo, el spike se habría planificado suponiendo dos vehículos disponibles |
| 2026-08-15 | **D3 y D4 revisadas.** El laboratorio GED deja de ser el entorno de evaluación y pasa a ser la etapa 2 del escalamiento —puerta de validación del hardware—; la evidencia física la produce el pasillo real del primer piso USTA, que es la geometría que el mundo simulado replica | `ESTADO.md` §3 y §6 todavía describían el laboratorio como entorno de pruebas y como lo replicado en Gazebo, mientras `CRONOGRAMA_S17_S32.md` §4 ya decía lo contrario desde el 14-ago. Dos documentos del mismo proyecto afirmando cosas distintas sobre dónde se mide es exactamente lo que el jurado encuentra |

---

## 8. Próximos pasos

La planificación completa de S17 a S32, con criterio de cierre verificable por semana, está en
[`Documentos/CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md). Arrastre de S17, al 2026-08-15:

1. ✅ **Contrato de interfaces ROS 2** (hito H1) — redactado en [`CONTRATO_INTERFACES.md`](Documentos/CONTRATO_INTERFACES.md), aplicado con bitácora en [`S17_aplicacion_contrato.md`](Documentos/Evidencia/S17_aplicacion_contrato.md) y **verificado en simulación el 2026-08-14**: `gazebo_ros2_control` y `agent_control.yaml` bajo namespace, dos árboles TF separados, controladores activos y mando aislado por robot ([`S17_nav2_namespaces.md`](Documentos/Evidencia/S17_nav2_namespaces.md), [`logs/S17_aislamiento_mando.txt`](Documentos/Evidencia/logs/S17_aislamiento_mando.txt)).
2. ✅ **Decisiones de alcance ante los directores** — en acta firmada el 2026-08-14, antes de S19 (§3). Queda por comunicar en el próximo corte la revisión de D3 y D4, posterior a la firma.
3. 🔴 **Entregable S16** — único entregable semanal atrasado. El material está completo: diagnóstico diferencial de `map_saver_cli`, causa raíz del `max_laser_range` y resultado antes/después. **Decisión pendiente de Santiago:** emitirlo tarde o absorberlo en un entregable posterior.

**Estado de S18 al 2026-08-15.** El criterio de cierre era: «H1 cerrado; el mundo de dos niveles
carga y se navega sobre él; el diagnóstico de hardware responde las cuatro preguntas». Los dos
primeros están cumplidos ([`S17_nav2_namespaces.md`](Documentos/Evidencia/S17_nav2_namespaces.md),
[`S18_entorno_dos_niveles.md`](Documentos/Evidencia/S18_entorno_dos_niveles.md)). **Falta el
tercero:** el **spike de hardware** acotado a 3–4 días, que responde cuatro preguntas y ninguna
más: `/scan` usable con el LiDAR real, `/cmd_vel` desde ROS 2, latencia entre vehículos, y qué
cambia entre Humble y Jazzy. Pasa a S19.

**El spike ya no se puede correr en el orden previsto.** Con un DeepRacer en intervención técnica
(R11), la pregunta 3 —latencia de ida y vuelta— exige los dos vehículos y queda supeditada a la
reparación. Las preguntas 1, 2 y 4 se responden con **un solo** vehículo y son las que se
ejecutan primero. La pregunta 4 (Humble ↔ Jazzy) además **no necesita hardware encendido**: el
desajuste ya está confirmado y lo que falta es medir su tamaño, comparando paquetes y parámetros
de Nav2 entre las dos distribuciones. Es el trabajo de mayor valor disponible sin depender de la
reparación.

Dos hallazgos abiertos que **bloquean OE4** y hay que resolver antes de instrumentar métricas
(detalle en [`S17_nav2_namespaces.md`](Documentos/Evidencia/S17_nav2_namespaces.md)):

- Una lectura de `/odom` reportó el desplazamiento del **otro** robot. Las cuatro métricas de OE4
  salen de odometría.
- Los vehículos se desvían hasta 18° con `angular.z = 0`, sin causa determinada.
