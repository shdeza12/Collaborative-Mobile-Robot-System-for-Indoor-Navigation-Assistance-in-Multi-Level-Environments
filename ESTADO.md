# Estado del proyecto — tablero de trazabilidad

> Fuente única de verdad del avance. Se actualiza **al cerrar cada sesión de trabajo**, antes del commit.
> Documento de referencia: `Documentos/Anteproyecto_Jonny_Santi.pdf` (cronograma en Cap. 8).

| | |
|---|---|
| **Semana del cronograma** | S17 de 32 |
| **Fecha de corte** | 2026-08-05 |
| **Fases activas** | Fase 4 — Desarrollo (cerrando) · Fase 5 — Integración (S18–S23) |
| **Semanas restantes** | 15 (sustentación S28–S29, documento final S29–S32) |
| **Último entregable formal** | Semana 15 |
| **Entregables pendientes** | S16, S17 |
| **Planificación vigente** | [`Documentos/CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md) |

---

## 1. Avance por objetivo específico

| ID | Objetivo específico (anteproyecto §4.2) | Avance | Evidencia verificable | Responsable |
|----|------------------------------------------|--------|------------------------|-------------|
| **OE1** | Modelar arquitectura funcional: requisitos, escenarios multipiso, asignación de tareas, esquema de comunicación | 🟡 40 % | `Documentos/Evidencia/arquitectura.png` (diagrama completo con protocolo de relevo). **Falta:** documento de requisitos funcionales numerados y matriz de trazabilidad | — |
| **OE2** | Plataforma robótica con **dos** vehículos: locomoción, sensado, procesamiento y **comunicación** | 🟡 40 % | Un robot en Gazebo, `deepracer_sim.launch.py`, stack de sensores validado (S14), SLAM 2D (S15). **Hardware (2026-08-05):** `deepracer-custom-car` instalado en Raspberry Pi 4 y en la tarjeta original del DeepRacer; acceso por red a ambas; locomoción verificada desde la interfaz web. **Falta:** sensado con LiDAR físico, control desde ROS 2 en vez de la web, namespaces, servidor de coordinación, comunicación inter-robot | — |
| **OE3** | Interfaz HRI web responsiva (selección origen–destino) | 🔴 0 % | Ninguna | — |
| **OE4** | Evaluación con métricas: tiempo de respuesta, tiempo de asignación, tasa de éxito, continuidad entre niveles | 🔴 0 % | Ninguna. No existe instrumentación ni protocolo experimental | — |

**Lectura:** a S17 de 32 (53 % del calendario) el avance técnico agregado está cerca del 25 %. El aporte declarado del proyecto —coordinación inter-robot y protocolo de relevo— aún no tiene implementación. La planificación de S17–S32 lo sitúa entre S20 y S22.

---

## 2. Camino crítico

Ordenado por dependencia. Nada de lo que sigue puede saltarse. La columna *Semana* remite al [cronograma vigente](Documentos/CRONOGRAMA_S17_S32.md).

| # | Hito | Bloquea a | Semana | Estado |
|---|------|-----------|--------|--------|
| 1 | **Contrato de interfaces ROS 2** (namespaces, acciones, tópicos) | Todo el desarrollo posterior | S17 | 🟡 Redactado en [`CONTRATO_INTERFACES.md`](Documentos/CONTRATO_INTERFACES.md); falta verificarlo en simulación (§8 del contrato) |
| 2 | **Réplica del laboratorio GED en Gazebo**, dividida en dos zonas | Mapas, navegación, relevo | S18 | 🔴 No existe |
| 3 | **Navegación autónoma punto a punto** con restricción Ackermann | Guiado, relevo, métricas | S19 | 🟡 Validada en el mundo del pasillo; falta sobre la réplica |
| 4 | **Segundo agente + servidor de coordinación** | OE2, protocolo de relevo | S19–S20 | 🔴 No iniciado |
| 5 | **Protocolo de relevo** (máquina de estados) | OE4, núcleo del aporte | S21 | 🔴 No iniciado |
| 6 | **Interfaz HRI** web sobre `rosbridge_suite` | OE3 | S22 | 🔴 No iniciado |
| 7 | **Instrumentación de métricas** | OE4, Fase 6 | S20–S21 | 🔴 No iniciado |
| 8 | **Bring-up de los dos DeepRacers** y despliegue del stack | Demostración física de OE2 | S21–S22 | 🟡 Custom car instalado; falta ROS 2 y LiDAR |

El mapa del pasillo USTA (riesgo R1) **salió del camino crítico** al adoptarse el laboratorio GED como entorno experimental. Permanece como escenario secundario opcional.

---

## 3. Decisión de alcance vigente

**Estrategia adoptada (2026-08-05): la simulación produce la evidencia estadística; el hardware produce la demostración.** Sustituye a la versión del 2026-08-03. Desarrollo completo en [`Documentos/CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md) §4.

| ID | Decisión |
|----|----------|
| D1 | Las cuatro métricas de OE4 se miden en **simulación con N = 30**. Los vehículos físicos ejecutan el protocolo con N de 5 a 10, como demostración funcional. *Razón:* una tasa de éxito exige N. Con 5 corridas y 4 aciertos el IC del 95 % va de 38 % a 96 %; con 30 y 27 aciertos va de 80 % a 97 % |
| D2 | **Un piso es una región navegable con mapa y agente propios; la transición es un evento lógico.** En el esquema de relevo ningún robot cruza entre niveles, luego la frontera no necesita ser vertical. Se declara como simplificación explícita en el documento final |
| D3 | Las pruebas físicas se realizan en el **laboratorio GED**, en condiciones controladas. Alineado con OE4 y con §4.3 del anteproyecto |
| D4 | El laboratorio se **replica en Gazebo**: mismo protocolo y misma geometría en ambos entornos, lo que hace comparables los resultados |
| D5 | La interfaz HRI es **web responsiva** sobre `rosbridge_suite`, accedida desde un teléfono. No es un recorte: §7.2 del anteproyecto lista "JavaScript, PHP, HTML" y "dispositivos móviles" |
| D6 | El código se escribe **una vez contra un contrato de interfaces ROS 2** y se despliega en dos destinos. Coordinación, relevo, HRI e instrumentación operan contra `/robot1/...` y `/robot2/...` sin conocer el backend |

> ⚠️ **Pendiente:** estas decisiones deben presentarse formalmente a los directores (Mateus, Ospina, Gélvez) y quedar en acta antes de S19.

---

## 4. Riesgos abiertos

| ID | Riesgo | Impacto | Mitigación | Estado |
|----|--------|---------|------------|--------|
| R1 | **Ningún mapa obtenido es utilizable.** Mejor resultado: 41,9 % de cobertura en X y una extensión en Y de 16,5 m contra los 5,3 m reales del pasillo | **Degradado el 2026-08-05:** ya no bloquea. Afecta solo al pasillo USTA, que pasó a escenario secundario | **Causa raíz confirmada:** `max_laser_range` de slam_toolbox estaba en 12,0 m, por encima del alcance físico del LiDAR (10,0 m). Los rayos sin retorno volvían como 10,0 m, quedaban bajo el umbral y se rasterizaban como paredes fantasma en arcos de 10 m de radio. Corregido a 9,5 m el 2026-08-03 | 🟢 Fuera del camino crítico |
| R7 | **El código que se ejecuta no es el que está versionado.** `~/deepracer_sim_ws/src/aws-deepracer` era una copia independiente del repositorio, no un enlace | Las correcciones no surten efecto; hay trabajo que nunca llega al historial | **Se dio por cerrado el 2026-08-03 sin estarlo.** La verificación de entonces comprobó que `install/` resolvía a `src/` —cierto— pero no que `src/` fuera a su vez una copia. Lo era: un clon de `aws-deepracer/aws-deepracer.git` con cambios locales. Cerrado de verdad el 2026-08-05 sustituyendo la copia por un enlace simbólico al repositorio, con `colcon build` limpio (7/7) y comprobando que `readlink -f` de un archivo instalado apunta a `~/Documents/Tesis` | ✅ Cerrado (2026-08-05) |
| R2 | **Ackermann vs. Nav2.** El controlador por defecto (DWB) asume tracción diferencial; el DeepRacer no gira sobre su eje | Trayectorias inejecutables | Resuelto en el stack publicado en `integracion-nav2`: Smac Hybrid-A\*, árboles de comportamiento propios sin `<Spin>`, `use_rotate_to_heading: false`, footprint real 0,28 × 0,19 m. **Sin verificar:** el cambio a `REEDS_SHEPP` + `allow_reversing` que se hizo tras abortar el goal (−5, 1.5) con "Resulting plan has 0 poses" | 🟡 Mitigado, verificación pendiente |
| R3 | **Ambigüedad de localización.** Pasillo largo de paredes lisas y repetitivas → AMCL propenso a divergir | Falsos negativos en las métricas de OE4 | Evaluar landmarks en el mundo o fusión con odometría visual | 🟡 Identificado |
| R4 | **Pared sur abierta en el SDF** deja celdas desconocidas | Afecta planificación, no solo el mapa | Cerrar la geometría en `primer_piso_v2.world` | 🟡 Identificado (desde S14) |
| R5 | **Fases 2 y 3 sin artefacto verificable.** No existe documento de requisitos | Imposibilita §7.4 del anteproyecto ("comparación con requisitos") | Reconstruir la matriz RF↔OE↔prueba. **Programado para S18** | 🔴 Abierto |
| R6 | **Discrepancias informe ↔ repositorio** (ver §5) | Credibilidad de la evidencia ante el jurado | Corregir en el entregable de cierre de fase | 🔴 Abierto |
| R8 | **Desajuste de distribución.** El stack de simulación es ROS 2 Humble; `deepracer-custom-car` sobre Ubuntu 24.04 es Jazzy. Los parámetros de Nav2 y varias API cambian entre ambas | Puede invalidar el supuesto de D6: que el mismo código se despliega en los dos destinos sin cambios | Caracterizarlo en el **spike de S18**, pregunta 4. Si el desajuste es grande, mantener una variante de configuración por distribución | 🔴 Abierto, sin caracterizar |
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
| §4.3: pruebas "en un entorno interior con multiples pisos" | Laboratorio GED, un solo nivel dividido en dos zonas con franja de transición | El propio §4.3 delimita el alcance a "la demostración funcional de la prueba de concepto **en condiciones controladas**", y OE4 pide "un entorno interior **controlado**". En el esquema de relevo del anteproyecto ningún robot cruza entre niveles — ese es el aporte — de modo que la frontera puede ser cualquier discontinuidad que ningún agente atraviese. **Es una simplificación del escenario físico, no del protocolo** |
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

---

## 8. Próximos pasos

La planificación completa de S17 a S32, con criterio de cierre verificable por semana, está en
[`Documentos/CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md). Pendiente inmediato de S17:

1. ~~Definir el **contrato de interfaces ROS 2**~~ → redactado en [`Documentos/CONTRATO_INTERFACES.md`](Documentos/CONTRATO_INTERFACES.md). **En aplicación**, con bitácora en [`Documentos/Evidencia/S17_aplicacion_contrato.md`](Documentos/Evidencia/S17_aplicacion_contrato.md):
   - ✅ Conflicto de doble padre en `camera_link` resuelto.
   - ✅ `frame_prefix` en los xacro (los 3 marcos que escriben plugins de Gazebo).
   - ✅ `namespace`, `x`, `y`, `z`, `yaw` en los launch. Regresión con defecto vacío: 3/3.
   - ⬜ `gazebo_ros2_control` y `agent_control.yaml` bajo namespace. Es el paso con incertidumbre real.
   - ⬜ Verificación de cierre (§8): dos árboles TF separados, 14 controladores activos, mando aislado por robot.
2. Emitir los **entregables S16 y S17** pendientes. El S16 tiene material completo: diagnóstico diferencial de `map_saver_cli`, causa raíz del `max_laser_range` y resultado antes/después.
3. Llevar las **decisiones de alcance D1–D6** a los directores, antes de S19.

Y en S18, el **spike de hardware** acotado a 3–4 días, que responde cuatro preguntas y ninguna más:
`/scan` usable con el LiDAR real, `/cmd_vel` desde ROS 2, latencia entre vehículos, y qué cambia
entre Humble y Jazzy.
