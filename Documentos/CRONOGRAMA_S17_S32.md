# Cronograma actualizado — Proyecto de Grado 2 (S17–S32)

**Proyecto:** Sistema colaborativo de robots móviles para asistencia de orientación en entornos interiores con múltiples pisos
**Autores:** Santiago Hernández Ávila · Jonny Alejandro Mejía León
**Directores:** Ing. Armando Mateus Rojas, Msc. · Ing. Nestor Ivan Ospina, Msc. · Ing. Oscar Mauricio Gélvez Lizarazo, Msc.
**Documento de referencia:** `Anteproyecto_Jonny_Santi.pdf`, Cap. 8 (cronograma a 32 semanas)
**Fecha de corte:** 2026-08-05 (S17)

---

## 1. Propósito

Este documento actualiza el cronograma del anteproyecto para el segundo periodo académico del
proyecto. Registra lo ejecutado hasta S17, replanifica S17–S32 sobre el estado real, y justifica
por escrito cada desviación respecto a lo planeado en marzo.

El cronograma original se estructuró a 32 semanas continuas. En la práctica se reparte en dos
periodos académicos separados por el receso de mitad de año:

| Periodo | Semanas | Calendario |
|---|---|---|
| Proyecto de Grado 1 | S1–S16 | febrero – mayo de 2026 |
| Proyecto de Grado 2 | S17–S32 | agosto – noviembre de 2026 |

---

## 2. Calendario de referencia

| Semana | Fechas | Semana | Fechas |
|---|---|---|---|
| S17 | 3 – 9 ago | S25 | 28 sep – 4 oct |
| S18 | 10 – 16 ago | S26 | 5 – 11 oct |
| S19 | 17 – 23 ago | S27 | 12 – 18 oct |
| S20 | 24 – 30 ago | **S28** | **19 – 25 oct** |
| S21 | 31 ago – 6 sep | **S29** | **26 oct – 1 nov** |
| S22 | 7 – 13 sep | S30 | 2 – 8 nov |
| S23 | 14 – 20 sep | S31 | 9 – 15 nov |
| S24 | 21 – 27 sep | S32 | 16 – 22 nov |

La sustentación se prevé a finales de octubre, es decir **S28–S29**. El documento final se entrega
después de la sustentación, para incorporar las observaciones del jurado.

---

## 3. Estado al iniciar la replanificación (S17)

Tomado de `ESTADO.md`, tablero de trazabilidad del proyecto.

| ID | Objetivo específico | Avance | Falta |
|---|---|---|---|
| OE1 | Arquitectura funcional: requisitos, escenarios multipiso, asignación de tareas, comunicación | 🟡 40 % | Documento de requisitos numerados y matriz de trazabilidad |
| OE2 | Plataforma con dos vehículos: locomoción, sensado, procesamiento, comunicación | 🟡 40 % | Sensado sobre vehículo real, control desde ROS 2, comunicación entre agentes |
| OE3 | Interfaz de interacción humano–robot | 🔴 0 % | Todo |
| OE4 | Evaluación con métricas | 🔴 0 % | Instrumentación y protocolo experimental |

**Ejecutado en S17:**

- Consolidación y publicación del stack Nav2 + AMCL adecuado a cinemática Ackermann y migrado de
  ROS 2 Foxy a Humble (rama `integracion-nav2`).
- Instalación de `deepracer-custom-car` sobre Raspberry Pi 4 y sobre la tarjeta de cómputo original
  del AWS DeepRacer.
- Acceso por red a ambas tarjetas y verificación de locomoción del vehículo desde su interfaz web.

Este último punto eleva OE2 del 25 % al 40 %: cubre locomoción, procesamiento y acceso por red
sobre hardware real. Quedan pendientes el sensado con el LiDAR físico y el control desde ROS 2.

---

## 4. Decisiones de alcance que rigen esta planificación

Adoptadas el 2026-08-05. Deben presentarse a los directores y quedar en acta.

**D1 — La simulación produce la evidencia estadística; el hardware produce la demostración.**
Las cuatro métricas de OE4 se miden en simulación con N = 30 repeticiones. Los vehículos físicos
ejecutan el protocolo completo con N entre 5 y 10, como demostración funcional. *Motivo:* una tasa
de éxito exige N. Con 5 corridas y 4 aciertos, el intervalo de confianza del 95 % va de 38 % a
96 %, que no sostiene una afirmación; con 30 corridas y 27 aciertos va de 80 % a 97 %. Además, las
corridas físicas fallan por causas ajenas al aporte (deriva de localización, latencia de red,
descarga de batería) que contaminan la métrica.

**D2 — La dimensión multipiso se conserva en simulación y se simplifica solo en el laboratorio.**
El título del proyecto, el objetivo general y el planteamiento del problema giran sobre entornos de
múltiples niveles: eso no se puede diluir. Por tanto:

- **En simulación** el mundo tiene **dos niveles reales con separación vertical** y una zona de
  escaleras. Es el escenario fiel al anteproyecto y es donde se ejecuta la campaña de N = 30.
- **En el laboratorio GED** los dos niveles se representan como dos zonas del mismo plano,
  separadas por una franja de transición marcada.

Lo que legitima la simplificación física es que, en el esquema de relevo del anteproyecto, **ningún
robot cruza entre niveles** — ese es precisamente el aporte, evitar el hardware de transición
vertical. Si ningún agente atraviesa la frontera, la frontera solo necesita ser una discontinuidad
que ningún agente cruza. El protocolo se reproduce íntegro: solicitud, asignación, guiado, entrega,
notificación, espera y reanudación. *Es una simplificación del escenario físico, no del protocolo,
y se declara como tal en el documento final.*

**D3 — Las pruebas físicas se realizan en el laboratorio GED, en condiciones controladas.**
Alineado con OE4 ("entorno interior controlado") y con §4.3 del anteproyecto ("el alcance se limita
a la demostración funcional de la prueba de concepto en condiciones controladas"). Elimina la
dependencia de permisos de acceso y ventanas horarias.

**D4 — El mundo simulado replica la geometría del laboratorio, duplicada en dos niveles.**
Un solo mundo Gazebo: la planta del laboratorio GED modelada dos veces, a dos alturas, unidas por
una escalera. Cada nivel tiene entonces la **misma geometría que el laboratorio real**, lo que hace
directamente comparables los resultados de simulación y de físico, y a la vez conserva la
separación vertical que exige el anteproyecto. El costo adicional sobre modelar dos zonas contiguas
es un desplazamiento en Z y una escalera decorativa, porque los robots nunca la recorren.

**D5 — La interfaz HRI es web responsiva, servida por `rosbridge_suite`, y se accede desde el
navegador de un teléfono.** §7.2 del anteproyecto lista como software "JavaScript, PHP, HTML" y
como hardware "dispositivos móviles": la pila declarada ya era web. OE3 exige selección de origen y
destino, y eso se cumple íntegro. **Aun así constituye una desviación y se declara como tal**,
porque §4.3 habla de "una aplicación móvil" y esto no es una aplicación nativa.

**D6 — El código se escribe una vez contra un contrato de interfaces ROS 2 y se despliega en dos
destinos.** El nodo de coordinación, la máquina de estados del relevo, la HRI y la instrumentación
operan contra `/robot1/...` y `/robot2/...` sin conocer si detrás hay Gazebo o un DeepRacer.

---

## 5. Desviaciones respecto al cronograma del anteproyecto

| Actividad (Cap. 8) | Anteproyecto | Actualizado | Justificación |
|---|---|---|---|
| Ajuste progresivo de los elementos desarrollados | S15–S17 | S17–S18 | La navegación autónoma de un agente requirió migración completa de Nav2 de Foxy a Humble y adecuación a cinemática Ackermann, no previstas |
| Integración de los módulos del sistema | S16–S18 | S18–S22 | Depende de la anterior |
| Verificación del funcionamiento general | S16–S18 | S23 | Depende de la anterior |
| Pruebas en condiciones controladas | S17–S20 | S23–S25 | Corrimiento acumulado |
| Corrección de fallas o inconsistencias | S18–S20 | S23 | Se concentra en la semana de congelación de código |
| Ejecución de pruebas de evaluación | S20–S22 | S24–S25 | Corrimiento acumulado |
| Recolección de información | S21–S23 | S24–S25 | Se fusiona con la anterior mediante registro automático |
| Análisis de resultados | S22–S24 | S26 | Corrimiento acumulado |
| Elaboración de conclusiones | S23–S24 | S27 | Corrimiento acumulado |
| Preparación de la sustentación final | S30–S32 | S26–S28 | **Se adelanta:** la sustentación quedó en octubre, no en noviembre |
| Elaboración del documento final | S25–S30 | S29–S32 | **Se traslada después de la sustentación**, conforme a la norma del espacio académico |
| Registro de avances del proyecto | S8–S32 | S8–S32 | **Sin cambio.** Se materializa en los entregables semanales y en `ESTADO.md` |

El corrimiento neto de la parte técnica es de 2 a 4 semanas. Se absorbe porque la redacción del
documento salió del camino crítico.

Ninguna actividad del Cap. 8 se elimina ni se sustituye: todas conservan su identidad y su orden de
dependencia. Lo que cambia son las ventanas temporales y, en dos casos, su posición relativa.

---

## 6. Organización del trabajo

Entre S18 y S21 el trabajo se reparte en dos frentes. No es una preferencia organizativa: el
trabajo pendiente suma entre 9 y 10 semanas-persona y el calendario ofrece 7 semanas. Sin reparto
no cierra.

| Frente | Contenido | Semanas |
|---|---|---|
| **A — Coordinación en simulación** | Contrato de interfaces, réplica SDF, dos agentes, nodo de coordinación, relevo, instrumentación, HRI | S17–S23 |
| **B — Plataforma física** | Spike de diagnóstico, paridad entre vehículos, mapeo real, bring-up y despliegue | S18–S23 |
| **T — Transversal** | Requisitos, protocolo experimental, entregables semanales, `ESTADO.md` | S17–S32 |

A partir de S24 los dos frentes convergen y el trabajo vuelve a ser conjunto.

---

## 7. Cronograma detallado

Cada semana cierra con un **criterio verificable**. Una semana no se da por cumplida por actividad
realizada, sino por artefacto producido.

### S17 · 3 – 9 ago — Cierre de deuda técnica y contrato de interfaces

| Frente | Actividad | Estado |
|---|---|---|
| A | Consolidar y publicar el stack Nav2 + AMCL en el repositorio | ✅ hecho |
| B | Instalar `deepracer-custom-car` en Raspberry Pi 4 y en la tarjeta original | ✅ hecho |
| B | Acceso por red a ambas tarjetas y prueba de locomoción vía interfaz web | ✅ hecho |
| A | Definir el contrato de interfaces ROS 2: namespaces, acciones, tópicos, tipos de mensaje | pendiente |
| T | Actualizar `ESTADO.md` con el avance de hardware y las decisiones D1–D6 | pendiente |
| T | Emitir el entregable S16 (material disponible: causa raíz de `max_laser_range`) | pendiente |

**Criterio de cierre:** existe `Documentos/CONTRATO_INTERFACES.md`; `ESTADO.md` refleja OE2 al 40 %
y registra D1–D6; entregable S16 emitido.

### S18 · 10 – 16 ago — Spike de hardware, requisitos y réplica del entorno

| Frente | Actividad |
|---|---|
| B | **Spike acotado (3–4 días)**, responde cuatro preguntas y no más: (1) ¿el LiDAR real publica un `/scan` usable bajo el custom car? (2) ¿se puede comandar `/cmd_vel` desde ROS 2 sin pasar por la interfaz web? (3) ¿cuál es la latencia de ida y vuelta entre los dos vehículos sobre el Wi-Fi del laboratorio? (4) Humble contra Jazzy: ¿qué paquetes hay que reconstruir y qué parámetros de Nav2 cambian? |
| A | Medir el laboratorio GED y modelar su planta en SDF, duplicada en dos niveles con separación vertical y escalera |
| T | Construir la matriz de requisitos RF ↔ OE ↔ prueba (cierra el riesgo R5) |
| T | Emitir el entregable S17 |

**Criterio de cierre:** informe del spike con las cuatro respuestas y su impacto en el plan;
`laboratorio_ged.world` carga en Gazebo con sus dos niveles; matriz de requisitos publicada.

### S19 · 17 – 23 ago — Dos agentes en simulación

| Frente | Actividad |
|---|---|
| A | Lanzar dos agentes con namespaces `/robot1` y `/robot2` sobre la réplica |
| A | Generar el mapa de cada nivel y configurar Nav2 independiente por agente |
| B | Llevar el segundo DeepRacer al mismo estado del primero |
| B | Resolver lo que haya arrojado el spike |
| T | Definir el protocolo experimental de OE4: qué se mide, cómo, cuántas repeticiones, criterios de éxito |
| T | Emitir el entregable S18 |

**Criterio de cierre:** `ros2 action send_goal /robot1/navigate_to_pose` y su equivalente en
`/robot2` mueven a cada agente dentro de su nivel sin interferencia de TF ni de tópicos. Protocolo
experimental escrito **antes** de instrumentar.

### S20 · 24 – 30 ago — Nodo de coordinación

| Frente | Actividad |
|---|---|
| A | Servidor de coordinación: registro de agentes, recepción de solicitud, asignación por nivel |
| A | Instrumentar desde el inicio el tiempo de respuesta y el tiempo de asignación |
| B | Mapear el laboratorio real con el DeepRacer físico — primera evidencia del LiDAR real |
| T | Emitir el entregable S19 |

**Criterio de cierre:** una solicitud origen–destino produce la asignación del agente correcto y
deja registrados los dos tiempos en un log estructurado. El mapa real del laboratorio queda
guardado y verificado con `herramientas/verificar_mapa.py`.

### S21 · 31 ago – 6 sep — Protocolo de relevo · **punto de decisión**

| Frente | Actividad |
|---|---|
| A | Máquina de estados del relevo: guiado a la zona de transición, entrega, notificación al segundo agente, espera y reanudación |
| A | Instrumentar la tasa de éxito y la continuidad del servicio |
| B | Nav2 sobre un DeepRacer físico: navegación autónoma punto a punto en el laboratorio |
| T | Emitir el entregable S20 |

**Criterio de cierre:** en simulación, una solicitud que cruza niveles se completa de extremo a
extremo con relevo, y el log arroja las cuatro métricas de OE4.

> **GO / NO-GO:** ¿el DeepRacer físico navega de forma autónoma en el laboratorio?
> **Sí** → bring-up del segundo vehículo en S22; demostración con dos robots reales.
> **No** → la demostración física baja a un robot real más uno simulado, y se documenta como
> limitación. El cronograma **no** se renegocia.

### S22 · 7 – 13 sep — Interfaz HRI e integración

| Frente | Actividad |
|---|---|
| A | Interfaz web responsiva sobre `rosbridge_suite`: selección de origen y destino (OE3) |
| A | Integrar los cuatro módulos de extremo a extremo en simulación |
| B | Desplegar el stack sobre los vehículos físicos, según el resultado del go/no-go |
| T | Emitir el entregable S21 |

**Criterio de cierre:** desde un teléfono se selecciona origen y destino, y el sistema completa el
guiado con relevo en simulación sin intervención manual.

### S23 · 14 – 20 sep — Verificación y ensayo físico · **cierre de implementación**

| Frente | Actividad |
|---|---|
| A+B | Verificación del funcionamiento general y corrección de fallas |
| B | Ensayo en blanco del protocolo en el laboratorio con los vehículos reales |
| T | Congelar el código: a partir de aquí no entra funcionalidad nueva |
| T | Emitir el entregable S22 |

**Criterio de cierre:** el sistema corre de extremo a extremo en simulación y se ejecuta al menos
una corrida física completa. Repositorio etiquetado.

### S24 · 21 – 27 sep — Campaña experimental en simulación

| Actividad |
|---|
| Ejecutar N = 30 repeticiones del protocolo completo con registro automático de las cuatro métricas |
| Consolidar y versionar el conjunto de datos |
| Emitir el entregable S23 |

**Criterio de cierre:** 30 corridas registradas y conjunto de datos versionado en el repositorio.

### S25 · 28 sep – 4 oct — Campaña experimental física

| Actividad |
|---|
| Ejecutar entre 5 y 10 repeticiones en el laboratorio GED con los vehículos reales |
| Grabar y editar el video de la demostración |
| Emitir el entregable S24 |

**Criterio de cierre:** corridas físicas registradas con la misma instrumentación que en
simulación; video de la demostración listo.

### S26 · 5 – 11 oct — Análisis de resultados

| Actividad |
|---|
| Análisis comparativo simulación contra físico sobre la misma geometría |
| Verificación contra la matriz de requisitos (§7.4 del anteproyecto) |
| Iniciar el armado de la presentación |
| Emitir el entregable S25 |

**Criterio de cierre:** gráficas y tablas de las cuatro métricas; tabla de cumplimiento requisito
por requisito.

### S27 · 12 – 18 oct — Conclusiones y preparación

| Actividad |
|---|
| Elaborar las conclusiones sobre viabilidad técnica de la solución |
| Armar la presentación y ensayarla cronometrada |
| Emitir el entregable S26 |

**Criterio de cierre:** presentación completa y ensayada al menos una vez de principio a fin.

### S28 · 19 – 25 oct — **Sustentación (ventana 1)**

| Actividad |
|---|
| Ensayos finales y plan de contingencia de la demostración en vivo |
| **Sustentación** |

**Criterio de cierre:** sustentación realizada; observaciones del jurado registradas por escrito.

### S29 · 26 oct – 1 nov — Sustentación (ventana 2) e inicio del documento

| Actividad |
|---|
| Sustentación, si la fecha se corre a esta ventana |
| Definir la estructura del documento final e iniciar la redacción |

### S30–S31 · 2 – 15 nov — Documento final

| Actividad |
|---|
| Redacción completa del documento, incorporando las observaciones del jurado |
| Justificar por escrito las desviaciones registradas en §5 y en `ESTADO.md` §6 |

**Criterio de cierre (S31):** borrador completo entregado a los directores.

### S32 · 16 – 22 nov — Entrega

| Actividad |
|---|
| Incorporar las correcciones de los directores |
| Entrega final |

---

## 8. Hitos

| # | Hito | Semana | Habilita |
|---|---|---|---|
| H1 | Contrato de interfaces ROS 2 definido | S17 | Todo el desarrollo posterior |
| H2 | Riesgos de hardware caracterizados (spike) | S18 | Planificación realista del bring-up |
| H3 | Dos agentes navegando en niveles separados | S19 | Nodo de coordinación |
| H4 | Asignación dinámica de tareas funcionando | S20 | Protocolo de relevo |
| H5 | Relevo completo con métricas en simulación | S21 | Campaña experimental |
| H6 | Sistema integrado de extremo a extremo | S22 | Verificación |
| H7 | Implementación congelada | S23 | Campañas experimentales |
| H8 | Conjunto de datos completo | S25 | Análisis |
| H9 | Sustentación | S28–S29 | Documento final |

---

## 9. Gestión de la holgura

No hay semanas de reserva. La holgura está en el alcance y se consume en este orden, **sin
renegociar fechas**:

1. El pasillo USTA como escenario secundario en simulación. *Ya está fuera del camino crítico, lo
   que además retira el riesgo R1 de la ruta.*
2. Las repeticiones físicas bajan de 10 a 5.
3. La demostración física baja a un robot real más uno simulado *(es el go/no-go de S21)*.
4. La interfaz HRI pasa de mapa interactivo a **dos listas desplegables** sobre un conjunto fijo de
   localizaciones de interés. Conserva íntegra la selección de origen y destino que exige OE3; solo
   se sacrifica la representación gráfica del entorno.

**No se recorta bajo ninguna circunstancia:** el nodo de coordinación, el protocolo de relevo y la
instrumentación de métricas. Constituyen el aporte técnico declarado del proyecto; sin ellos no hay
resultado que sustentar.

Ningún nivel de esta escalera deja un objetivo específico sin cumplir. Los recortes 1 y 2 reducen
el tamaño muestral y la cobertura de escenarios; el 3 degrada la demostración de OE2 de dos
vehículos reales a uno, y en ese caso debe declararse explícitamente como limitación en el
documento final; el 4 reduce la riqueza de la interfaz sin tocar su función.

---

## 10. Trazabilidad

`ESTADO.md` sigue siendo el tablero único de avance. Este cronograma le aporta la dimensión
temporal; aquel aporta el estado por objetivo y el registro de riesgos.

Al cerrar cada semana se actualiza en `ESTADO.md`: el porcentaje de cada objetivo específico, el
estado de los riesgos abiertos, la bitácora de decisiones y el criterio de cierre alcanzado o no.
Una semana cuyo criterio de cierre no se cumpla se declara incumplida de forma explícita y su
trabajo pendiente se traslada, consumiendo holgura según §9.
