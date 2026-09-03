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
| **RF-01** | El sistema opera con **exactamente dos agentes**, cada uno dedicado a un nivel | Inventario de nodos por dominio: dos pilas completas, una por agente | ✅ | S18 |
| **RF-02** | Cada agente es **direccionable de forma independiente**: una orden a uno no altera al otro | `ros2 topic list --no-daemon --spin-time 8` por dominio: ningún tópico cruzado. Ordenar a robot1 y leer `/robot2/odom` | ✅ | S18 |
| **RF-03** | El coordinador manda a un agente **únicamente** mediante la acción `navigate_to_pose` | Inspección de suscriptores de `/robotN/cmd_vel`: ningún publicador fuera de la pila del propio agente | ✅ | S18 |
| **RF-04** | El sistema conoce un **conjunto de localizaciones de interés**, cada una con nivel y pose | Existe `puntos_interes.yaml`; el coordinador lo republica *latched* y `ros2 topic echo` lo devuelve completo | 🔴 | S20 |
| **RF-05** | El coordinador **asigna la misión al agente del nivel de origen** (asignación dinámica de tareas) | Una solicitud con origen en el nivel 1 activa a robot1 y no a robot2; y a la inversa | 🔴 | S20 |
| **RF-06** | Si origen y destino están en el **mismo nivel**, la misión se resuelve con **un solo agente y cero relevos**, sin ramas especiales en la HRI | `result.num_relevos == 0` y el segundo agente permanece en estado `LIBRE` | 🔴 | S20 |
| **RF-07** | Si origen y destino están en **niveles distintos**, se ejecuta el **protocolo de relevo**: guiado al punto de transferencia, publicación del relevo, activación del segundo agente, reanudación | Una misión entre niveles recorre las etapas `TRAMO_1 → TRANSFERENCIA → TRAMO_2 → COMPLETADA` y `result.num_relevos == 1` | 🔴 | **S21** |
| **RF-08** | Cada agente **publica su estado** (nivel, pose, situación) a 2 Hz | `ros2 topic hz /robotN/estado` devuelve 2 Hz y el campo `estado` cambia al iniciar una misión | 🔴 | S20 |
| **RF-09** | El entorno de operación tiene **dos niveles con un punto de transición vertical** | El mundo carga los dos niveles; se navega en el superior con la altura constante | ✅ | S18 |
| **RF-10** | La **comunicación inter-robot** ocurre a través del coordinador, no directamente entre agentes | Ningún agente se suscribe a tópicos del otro (se sigue de RF-02) | ✅ | S18 |

**Lectura de OE1.** De diez requisitos, cinco están verificados. Los cinco pendientes son el nodo
de coordinación (RF-04 a RF-06, RF-08) y el protocolo de relevo (RF-07). **RF-07 es el aporte
declarado del proyecto.**

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
| **RF-11** | Cada vehículo ejecuta **locomoción** comandada por `/<ns>/cmd_vel`, con cinemática Ackermann | El vehículo se desplaza; recorrido medido contra `/odom` | 🟡 sim ✅ / físico vía web | S19–S21 |
| **RF-12** | Cada vehículo publica **`/<ns>/scan`** utilizable para localización y evasión | El LiDAR publica a su frecuencia nominal y el mapa de costos local registra los obstáculos | 🟡 sim ✅ / físico 🔴 | **S19** (spike, pregunta 1) |
| **RF-13** | Cada vehículo publica **odometría** en `/<ns>/odom` | Lectura antes y después de un desplazamiento conocido | 🟡 sim ✅ **contra un oráculo**, no verificado (ver §7.4) / físico 🔴, se mide en la corrida de ≥ 20 m de S20 | S19 |
| **RF-14** | Cada vehículo se comanda **desde ROS 2**, sin pasar por la interfaz web del fabricante | Publicar en `/<ns>/cmd_vel` desde otra máquina de la red mueve el vehículo | 🔴 | **S19** (spike, pregunta 2) |
| **RF-15** | Los dos vehículos y el coordinador se **alcanzan por red** con latencia acotada | Medida de ida y vuelta entre los dos vehículos | 🔴 bloqueado por **R11** | S19+ |
| **RF-16** | El **mismo código fuente** se despliega en los dos destinos, simulado y físico (decisión D6) | Compilar el coordinador sin cambios en las dos distribuciones y completar una misión **en cada mundo por separado** | 🟡 **verificado con resultado condicionado** (2026-08-18) | S22 |
| ~~RF-16b~~ | ~~Una misión con robot1 **simulado** y robot2 **físico** a la vez~~ | ~~Misión mixta completada sin recompilar~~ | ❌ **imposible sin trabajo nuevo** (2026-08-18) | — |

**Lectura de OE2.** El cuello de botella no es el software sino el acceso al hardware. RF-12 y
RF-14 son las preguntas 1 y 2 del spike de esta semana y **se responden con un solo vehículo**.
RF-15 exige los dos y está bloqueado por R11.

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
| **RF-20** | La HRI es accesible desde el **navegador de un teléfono**, sin instalación | Carga y operación completa desde un móvil en la misma red | 🟡 Implementada sin dependencias externas ni CDN (funciona sin salida a internet) y probada en emulación móvil (375×812). **Falta** la prueba desde un teléfono físico real en la red del edificio | S22 |

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
| **RF-21** | El sistema registra el **tiempo de respuesta**: desde la solicitud hasta que el agente inicia el movimiento | El registro de la misión contiene la marca temporal de ambos eventos | 🟢 **Verificado el 2026-08-27.** El registro de `S20_rutas_03` trae `t_solicitud: 87.9` y `t_primer_movimiento: 88.1`, ambas leídas de `/clock` | S20 |
| **RF-22** | El sistema registra el **tiempo de asignación de robot**: desde la solicitud hasta que un agente queda asignado | Ídem | 🟢 **Verificado el 2026-08-27.** `t_solicitud` y `t_robot_activo` en el mismo registro | S20 |
| **RF-23** | El sistema registra el **éxito o fallo** de cada misión, con el motivo | `result.exito` y `result.motivo_fallo` quedan en el registro | 🔴 | S21 |
| **RF-24** | El sistema registra la **continuidad del servicio entre niveles**: que la misión atraviesa el relevo sin interrupción del guiado | Ninguna etapa queda sin agente activo entre `TRAMO_1` y `TRAMO_2` | 🔴 | S21 |
| **RF-25** | Las métricas se obtienen de un **registro estructurado y automático**, no de observación manual | Un archivo por misión, procesable sin intervención | 🟡 **Verificado el 2026-08-27 en condición A.** Esquema JSON versionado y comprobable; `herramientas/componer_registro.py` compone el registro desde el bag y lo valida contra el esquema; el veredicto se calcula contra `/odom` y nunca contra el `SUCCEEDED` de Nav2. **Falta** cerrar cuatro campos que hoy salen vacíos o escritos a mano —los dos marcadores de cambio de tramo, el RTF, la procedencia del mundo y del mapa, y los controladores activos— y probarlo en condición B | S20 |
| **RF-26** | La campaña en simulación alcanza **N = 30 repeticiones** (decisión D1) | Treinta registros válidos | 🔴 | S24–S25 |
| **RF-27** | La demostración física ejecuta el protocolo completo con **N entre 5 y 10** (decisión D1) | Registros de las corridas físicas | 🔴 | S24–S25 |

**Lectura de OE4, revisada el 2026-08-27.** La mitad instrumental está construida y verificada:
RF-21, RF-22 y RF-25 sobre misiones de condición A. Lo que sigue en rojo depende todo de lo mismo,
**el relevo**, y el relevo está escrito y probado como función pura pero **no se puede ejecutar**:
`robot1` y `robot2` corren en dominios DDS distintos con un `gzserver` cada uno —impuesto por
`gazebo_ros` de Humble— y un nodo de ROS 2 vive en un solo dominio, así que el coordinador no
alcanza a los dos. **RF-24 es la variable de respuesta principal** del proyecto —es la que responde
la pregunta de investigación— y hoy su único bloqueo es ese. Está anotado como séptimo
prerrequisito en el §10 de [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md).

---

## 6. Restricciones del alcance

Estas no se construyen: se respetan, y hay que **poder demostrar que se respetaron**. Salen todas
del anteproyecto §4.3.

| ID | Restricción | Cómo se demuestra | Estado |
|---|---|---|---|
| **RNF-01** | **Ningún agente cruza entre niveles.** La transición es un evento lógico del protocolo, no un desplazamiento | La coordenada vertical de cada agente es constante durante toda la misión | ✅ medido en S18 |
| **RNF-02** | Los agentes **no manipulan objetos, no transportan carga y no interactúan mecánicamente con la infraestructura** (puertas, botones de ascensor) | Por diseño: el vehículo no tiene actuadores más allá de tracción y dirección | ✅ |
| **RNF-03** | Operación **en interiores, en un espacio previamente delimitado y en condiciones controladas** | Las repeticiones se ejecutan en franjas de baja circulación; las personas se registran como observación cualitativa | 🟡 declarado |
| **RNF-04** | Plataforma **de bajo costo** | AWS DeepRacer en lugar de DonkeyCar; desviación registrada en `ESTADO.md` §6 | ✅ con desviación |
| **RNF-05** | Las trayectorias deben ser **ejecutables por cinemática Ackermann**: sin giro sobre el propio eje | Planificador con radio mínimo, árboles de comportamiento sin la primitiva de giro | ✅ S17 |
| **RNF-06** | La simulación debe correr **a tiempo real** para que las métricas temporales sean válidas | Factor de tiempo real ≥ 0,99 con las dos pilas activas | ✅ 0,996 medido en S18 |
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
| OE1 | RF-01 a RF-10 | 5 | 5 | S20–S21 |
| OE2 | RF-11 a RF-16 | 0 (4 parciales) | 2 | S19–S22 |
| OE3 | RF-17 a RF-20 | 3 | 1 parcial | S22 |
| OE4 | RF-21 a RF-27 | 0 | 7 | S20–S25 |
| Restricciones | RNF-01 a RNF-07 | 6 | 1 parcial | — |
| **Total** | **34** | **14** | **14 + 6 parciales** | |

**Once de treinta y cuatro requisitos están verificados**, y son los que sostienen la
infraestructura. Los dieciocho pendientes se concentran en cuatro semanas de construcción
(S20–S22) más la campaña experimental (S24–S25).

*Actualizado el 2026-08-18: RF-16 pasa de pendiente a parcial tras la pregunta 4 del spike, y se
registra RF-16b como requisito descartado por imposible.*

---

## 10. Criterio de cierre de este documento

R5 se declara cerrado cuando esta matriz existe, cada requisito cita su fuente y su prueba, y
`ESTADO.md` la enlaza. **Se declara cerrado el 2026-08-18.**

Lo que R5 no cierra: los requisitos pendientes siguen pendientes. Esta matriz no construye nada;
lo que hace es que a partir de ahora se pueda responder, para cualquier semana, qué falta y cómo
se demostrará que se hizo.
