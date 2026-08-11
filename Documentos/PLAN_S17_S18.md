# Plan de trabajo — cierre de S17 y S18

**Periodo:** jueves 6 de agosto – viernes 14 de agosto de 2026
**Especificación de referencia:** `Documentos/ENTORNO_DE_EVALUACION.md`
**Contrato vigente:** `Documentos/CONTRATO_INTERFACES.md`
**Bitácora de H1:** `Documentos/Evidencia/S17_aplicacion_contrato.md`

**Objetivo del periodo:** cerrar el hito H1 (dos robots coexistiendo bajo espacios de
nombres independientes), dejar el entorno de evaluación de dos niveles cargando en el
simulador, y emitir los documentos de S17.

---

## Para qué sirve cada tarea

Este periodo no produce ninguna funcionalidad que se vea en la sustentación. Produce la
**condición de posibilidad** de todo lo que sí se ve. Conviene tenerlo escrito, porque desde
dentro se parece demasiado a estar arreglando launches.

La cadena es corta y no tiene atajos:

> Un solo robot navega hoy. Para que **dos** naveguen hacen falta dos grafos ROS que no se
> pisen (9b) y dos pilas Nav2 que no se pisen (9c). Sin eso no hay dos agentes; sin dos
> agentes no hay relevo; sin relevo no hay nada que medir ni nada que mostrar en la interfaz.

| Tarea | Objetivo específico | Qué desbloquea | Si no se hace |
|---|---|---|---|
| 4–7 · `robot_namespace` en xacro, plugin y controladores | OE2 | Que el vehículo entero (URDF, control, sensores) sea instanciable más de una vez | Un segundo vehículo comparte controladores con el primero |
| 8 · Regresión con defecto vacío | — | Que el trabajo de un robot siga siendo válido | Se pierde la línea base; ningún resultado anterior es comparable |
| 9 · Un robot bajo espacio de nombres | OE2 | Primera instancia aislada y verificable | — |
| **9b · Dos simuladores** | **OE2, OE4** | Los dos agentes del sistema colaborativo, y la constancia de que el hardware los sostiene a tiempo real | Las métricas de tiempo de OE4 saldrían contaminadas por falta de cómputo y no serían defendibles |
| **9c · Nav2 y AMCL con namespace** | **OE2** | Que los dos agentes *naveguen*, no solo que coexistan | Dos robots quietos: H3 (S19) queda sin base |
| 9d · URIs de los meshes | — | Evidencia gráfica en los dos visores | El entregable de S17 va sin capturas del modelo |
| 10, 10b · Regresión y cierre de H1 | OE1, OE2 | El hito que el cronograma sitúa en S17 | H3 arranca sobre una base no verificada |
| 11–13 · Entorno de dos niveles | OE1, OE4 | El escenario multipiso donde ocurre el relevo | No hay dónde ejecutar el experimento |
| 14 · Mapa del nivel 2 | OE2 | Localización en el nivel superior | El segundo agente no sabe dónde está |
| Diagnóstico de hardware (viernes) | OE2 | El punto de decisión de S21 sobre el segundo vehículo | Se descubre en S21 que un vehículo no responde, sin margen para reaccionar |

**Dónde queda OE3.** La interfaz humano–robot está al 0 % y no se toca en este periodo, a
propósito: la interfaz muestra el estado de dos agentes y les asigna destinos. Construirla
antes de que existan dos agentes sería programar contra una maqueta.

**Dónde queda OE4.** Igual: las métricas se miden sobre el relevo. Lo que sí aporta este
periodo a OE4 es negativo y vale mucho — quedó demostrado (9b) que las dos simulaciones corren
a RTF ≈ 1,0, así que las medidas de tiempo no estarán falseadas por el equipo.

**Trazabilidad con el cronograma.** H1 («contrato de interfaces ROS 2 definido», S17) es
prerrequisito declarado de *todo el desarrollo posterior*, y H3 («dos agentes navegando en
niveles separados», S19) depende directamente de las tareas 9b y 9c. El riesgo de S17–S18 no
es llegar tarde a H1: es darlo por cerrado sin evidencia y descubrir el hueco en S19, cuando
ya no haya margen.

---

## Calendario real

No se trabaja fines de semana. Festivos colombianos dentro del periodo S17–S32:

| Fecha | Festivo | Semana afectada |
|---|---|---|
| viernes 7 de agosto | Batalla de Boyacá (fecha fija, no se traslada) | S17 |
| lunes 17 de agosto | Asunción (trasladado desde el sábado 15) | S19 |
| lunes 12 de octubre | Día de la Raza | S27 |
| lunes 2 de noviembre | Todos los Santos (trasladado desde el domingo 1) | S30 |
| lunes 16 de noviembre | Independencia de Cartagena (trasladado desde el miércoles 11) | S32 |

**Días hábiles de este periodo:**

| Semana | Días |
|---|---|
| S17 | jueves 6 — **es el último día de S17** |
| S18 | lunes 10, martes 11, miércoles 12, jueves 13, viernes 14 |

Seis días, no diez. El presupuesto total del proyecto entre S17 y S32 es de **75 días
hábiles**, no de 16 semanas: 80 días laborales menos 5 festivos.

---

## Cómo se reparte el trabajo

La restricción real de este plan no son los días: es **tu tiempo frente a la terminal**.
Todo lo que se puede hacer sin Gazebo lo dejo listo antes, y tú ejecutas solo lo que
requiere el simulador, el hardware o tu criterio.

| Yo, sin tu terminal | Tú |
|---|---|
| Editar xacro, launch, YAML, SDF y LaTeX | `colcon build` y lanzar la simulación |
| Renderizar el URDF y probar el cambio nulo | Mirar el visor de Gazebo |
| Parsear los launch, validar los YAML | Correr `verificar_contrato.py` |
| Redactar y compilar los documentos | Revisar el contenido de los documentos |
| — | Todo el diagnóstico de hardware |

---

## Restricciones globales

- **Principio del cambio nulo.** Todo lo que se namespacea entra con defecto vacío y se
  demuestra primero que con el defecto no cambia nada.
- **Un cambio a la vez**, cada uno con la orden que lo desmentiría.
- **Lo que se pueda probar sin Gazebo se prueba antes de lanzarlo.**
- **Comunicación y commits en español.** Sin `Co-Authored-By`.
- **Rama de trabajo:** `integracion-nav2`. No se toca `main` en este periodo.
- **El repositorio y el workspace son el mismo árbol** — `~/deepracer_sim_ws/src/aws-deepracer`
  es un enlace simbólico —, pero hay que recompilar.

---

## Mapa de archivos del periodo

| Archivo | Estado | Responsabilidad |
|---|---|---|
| `Documentos/Entregables/Cronograma_S17_S32.tex` | Modificar | Cronograma; §11 de la especificación |
| `Documentos/Entregables/Entregable_semana_17.tex` | Modificar | Entregable de S17; §1, §9 y §11 |
| `.../xacro/deepracer/deepracer.xacro` | Modificar | Declarar el argumento `robot_namespace` |
| `.../xacro/control/deepracer_ros_control.xacro:91-97` | Modificar | Bloque `<ros>` del plugin `gazebo_ros2_control` |
| `deepracer_bringup/config/agent_control.yaml` | Modificar | Claves de nodo a comodín `/**/` |
| `deepracer_bringup/launch/deepracer_spawn.launch.py` | Modificar | Pasar `robot_namespace` al xacro |
| `deepracer_bringup/launch/deepracer_navigation_sim.launch.py` | ✔ Modificado 10 ago | Argumento `namespace` en los 6 nodos de Nav2 |
| `deepracer_bringup/launch/deepracer_localization_sim.launch.py` | ✔ Creado 10 ago | Sustituye a `nav2_bringup/localization_launch.py` |
| `deepracer_bringup/launch/nav_amcl_demo_sim.launch.py` | ✔ Modificado 10 ago | Propagar `namespace` a los tres launches incluidos |
| `deepracer_description/models/xacro/urdf/*.xacro` (4) | ✔ Modificado 10 ago | 26 URIs `package://` con nombre de paquete |
| `deepracer_description/package.xml` | ✔ Modificado 10 ago | Exportar también `${prefix}/..` a `GAZEBO_MODEL_PATH` |
| `primer_piso/model.config` | Crear | Metadatos del modelo Gazebo |
| `primer_piso/model.sdf` | Crear | Geometría de la planta, extraída del `.world` |
| `primer_piso_dos_niveles.world` | Crear | Mundo con las dos plantas y la losa del nivel 2 |
| `Documentos/Evidencia/S18_diagnostico_hardware.md` | Crear | Resultados del diagnóstico |

---

# Jueves 6 de agosto — Documentos de S17

**Es hoy o no es.** El entregable vence el domingo 9 y mañana es festivo.

Todo este día lo hago yo. Tú revisas el resultado.

### Tarea 1: Ajustar el cronograma

**Archivo:** `Documentos/Entregables/Cronograma_S17_S32.tex`

- [ ] **Paso 1.** Línea 210. Sustituir la actividad del frente A en S18:

  De: `Medir el laboratorio y modelar su planta, duplicada en dos niveles con separación vertical`

  A: `Replicar la planta \texttt{primer\_piso\_v2} en dos niveles con separación vertical y zona de transición señalizada en cada planta`

- [ ] **Paso 2.** Línea 215. Criterio de cierre de S18:

  De: `el mundo del laboratorio carga en el simulador con sus dos niveles`

  A: `el mundo de dos niveles carga en el simulador y el vehículo navega sobre el nivel superior`

- [ ] **Paso 3.** Línea 245. Actividad del frente B en S20:

  De: `Mapear el laboratorio con el vehículo físico`

  A: `Mapear con el vehículo físico las dos plantas del pasillo y contrastar el mapa resultante contra el modelo \texttt{primer\_piso\_v2}`

- [ ] **Paso 4.** Líneas 261 y 267. Cambiar el objeto del punto de decisión de S21: el acceso
  al pasillo está confirmado, así que la incógnita es otra.

  > Esta semana concentra el \textbf{punto de decisión} sobre el segundo vehículo. Si los dos vehículos quedan operativos, el relevo físico se demuestra con un vehículo por planta; en caso contrario, se demuestra con un vehículo real y uno simulado, y así se declara. En ninguno de los dos casos se modifican las fechas del cronograma ni se compromete la evidencia del relevo, que está cubierta por las pruebas en simulación.

- [ ] **Paso 5.** Líneas 294 y 324. Sustituir `laboratorio` por `pasillo` en las actividades
  de ensayo y de repeticiones físicas. El laboratorio conserva solo el papel de puesta en
  marcha, en S21.

- [ ] **Paso 6.** Añadir en S21 la compuerta de habilitación (§6 de la especificación), que
  hoy no está escrita en ninguna parte:

  > \textbf{Criterio de habilitación:} las pruebas en el pasillo se habilitan cuando un vehículo navegue punto a punto de forma autónoma en el laboratorio con localización estable. El relevo completo entre dos vehículos no es criterio de habilitación: es el núcleo del cumplimiento del proyecto, y condicionar el avance a su logro previo bloquearía la secuencia.

- [ ] **Paso 7.** Añadir el calendario de festivos a la sección de calendario, y la nota de
  que el presupuesto real es de 75 días hábiles. Un cronograma que cuenta semanas y no días
  hábiles esconde cinco días de trabajo que no existen, uno de ellos en la semana de entrega
  final.

- [ ] **Paso 8.** Compilar:

  ```bash
  cd Documentos/Entregables && pdflatex -interaction=nonstopmode Cronograma_S17_S32.tex
  ```

  Esperado: `Output written on Cronograma_S17_S32.pdf` sin ningún `! LaTeX Error`.

### Tarea 2: Ajustar el entregable de S17

**Archivo:** `Documentos/Entregables/Entregable_semana_17.tex`

- [ ] **Paso 1.** Línea 336. Sustituir `Modelado del laboratorio GED en formato SDF,
  duplicado en dos niveles` por la réplica de `primer_piso_v2`, con la redacción del paso 1
  de la tarea anterior.

- [ ] **Paso 2.** Añadir, antes de las conclusiones, la formulación explícita de la pregunta
  de investigación (§1 de la especificación), con la constancia de que el anteproyecto la
  programó en S3 pero no la dejó escrita.

- [ ] **Paso 3.** Añadir un párrafo que registre la selección del entorno de evaluación como
  resultado de la actividad *Análisis del entorno de evaluación* del propio anteproyecto,
  citando `ENTORNO_DE_EVALUACION.md`.

- [ ] **Paso 4.** Añadir las cuatro limitaciones declaradas (§9 de la especificación): las
  franjas de baja circulación, que el laboratorio no representa el entorno de operación, que
  los vehículos no atraviesan el punto de transición —consecuencia deliberada del esquema de
  relevo, no carencia— y la invalidación de la cartografía anterior al 5 de agosto.

- [ ] **Paso 5.** Compilar:

  ```bash
  cd Documentos/Entregables && pdflatex -interaction=nonstopmode Entregable_semana_17.tex
  ```

- [ ] **Paso 6.** Commit:

  ```bash
  git add Documentos/ENTORNO_DE_EVALUACION.md Documentos/PLAN_S17_S18.md Documentos/Entregables/Cronograma_S17_S32.tex Documentos/Entregables/Entregable_semana_17.tex
  git commit -m "Add: especificacion del entorno de evaluacion y ajuste de los documentos de S17"
  ```

**Criterio de cierre:** los dos PDF compilan sin errores y el entregable contiene la pregunta
de investigación escrita.

---

# Lunes 10 de agosto — H1: un robot bajo espacio de nombres

Antes de que llegues, dejo hechas las tareas 4, 5, 6 y 7 con sus comprobaciones de cambio
nulo. Tu parte empieza en la tarea 8.

### Tarea 3: Commitear el avance de H1 que está sin versionar

Seis archivos modificados y cuatro sin seguimiento llevan días fuera de git. Si algo se
rompe, no hay a dónde volver.

- [ ] **Paso 1.** Confirmar que el árbol no se movió: `git diff --stat`

- [ ] **Paso 2.** Commit:

  ```bash
  git add Robot/aws-deepracer/deepracer_bringup/launch/deepracer_sim.launch.py Robot/aws-deepracer/deepracer_bringup/launch/deepracer_spawn.launch.py Robot/aws-deepracer/deepracer_description/models/xacro/deepracer/deepracer.xacro Robot/aws-deepracer/deepracer_description/models/xacro/control/deepracer_ros_control.xacro Robot/aws-deepracer/deepracer_description/models/xacro/sensor/deepracer_gazebo_lidar.xacro herramientas/verificar_contrato.py herramientas/lanzar_sim.sh Documentos/CONTRATO_INTERFACES.md Documentos/Evidencia/S17_linea_base.md Documentos/Evidencia/S17_aplicacion_contrato.md ESTADO.md
  git commit -m "Add: contrato de interfaces ROS 2 y namespaceado de marcos y nodos con defecto vacio"
  ```

### Tarea 4: Declarar el argumento `robot_namespace`  ✔ hecho 2026-08-10

**Archivo:** `.../xacro/deepracer/deepracer.xacro`

`frame_prefix` vale `robot1/` con barra final; el espacio de nombres vale `robot1` sin barra.
Derivar uno del otro con manipulación de cadenas en xacro es frágil: se declara un segundo
argumento y el launch pasa los dos.

- [x] **Paso 1.** Añadir después de la declaración de `frame_prefix`:

  ```xml
  <!-- Espacio de nombres del robot (CONTRATO_INTERFACES.md §2). Vacio por defecto: con
       un solo robot el URDF generado es identico al original. Sin barra final, a
       diferencia de frame_prefix. Lo consume el bloque <ros> del plugin
       gazebo_ros2_control, que no hereda el -robot_namespace de spawn_entity porque no
       es un plugin de gazebo_ros. -->
  <xacro:arg name="robot_namespace" default="" />
  ```

- [x] **Paso 2.** Comprobar el cambio nulo:

  ```bash
  cd ~/Documents/Tesis/Robot/aws-deepracer/deepracer_description/models/xacro/deepracer && xacro deepracer.xacro > /tmp/nuevo.urdf && git stash && xacro deepracer.xacro > /tmp/viejo.urdf && git stash pop && diff <(grep -v '^ *<!--' /tmp/viejo.urdf) <(grep -v '^ *<!--' /tmp/nuevo.urdf) && echo "IDENTICO"
  ```

  Esperado: `IDENTICO`.

### Tarea 5: Bloque `<ros>` en el plugin `gazebo_ros2_control`  ✔ hecho 2026-08-10

**Archivo:** `.../xacro/control/deepracer_ros_control.xacro`, líneas 91-97.

`gazebo_ros2_control` no está construido sobre `gazebo_ros::Node::Get(_sdf)`, así que no
hereda el `-robot_namespace` que `spawn_entity.py` sí propaga al plugin de tracción. Hay que
inyectárselo. El binario confirma que lo soporta: `strings` sobre `libgazebo_ros2_control.so`
contiene `__ns:=`, `remapping` y `--ros-args`.

- [x] **Paso 1.** Sustituir el bloque completo por:

  ```xml
  <gazebo>
    <plugin filename="libgazebo_ros2_control.so" name="gazebo_ros2_control">
      <xacro:if value="${'$(arg robot_namespace)' != ''}">
        <ros>
          <namespace>$(arg robot_namespace)</namespace>
        </ros>
      </xacro:if>
      <robot_param>robot_description</robot_param>
      <robot_param_node>robot_state_publisher</robot_param_node>
      <parameters>$(find deepracer_bringup)/config/agent_control.yaml</parameters>
    </plugin>
  </gazebo>
  ```

  El bloque `<ros>` va dentro de un condicional, no con valor vacío: un
  `<namespace></namespace>` vacío emitiría `__ns:=`, que no es lo mismo que no emitir nada.
  Esa distinción ya nos mordió con `Node(namespace='')` en launch_ros.

  `<robot_param_node>` se deja en nombre relativo a propósito. `AsyncParametersClient`
  resuelve los relativos contra el espacio de nombres del nodo que lo crea, así que bajo
  `robot1` debería resolver solo a `/robot1/robot_state_publisher`. Es una hipótesis; se
  verifica en la tarea 9 y se corrige entonces, no antes.

- [x] **Paso 2.** Comprobar el cambio nulo con el comando del paso 2 de la tarea 4.
  Esperado: `IDENTICO`.

- [x] **Paso 3.** Comprobar que con espacio de nombres sí aparece:

  ```bash
  cd ~/Documents/Tesis/Robot/aws-deepracer/deepracer_description/models/xacro/deepracer && xacro deepracer.xacro robot_namespace:=robot1 | grep -A2 "<ros>"
  ```

  Esperado: `<namespace>robot1</namespace>`.

### Tarea 6: Pasar `robot_namespace` desde el launch  ✔ hecho 2026-08-10

**Archivo:** `deepracer_bringup/launch/deepracer_spawn.launch.py`

- [x] **Paso 1.** En `acciones()`, donde se arma `orden_xacro`:

  ```python
  orden_xacro = ['xacro ', modelo]
  if prefijo:
      orden_xacro += [' frame_prefix:=', prefijo, ' robot_namespace:=', ns]
  ```

  Sigue siendo una sola rama: sin espacio de nombres no se pasa ninguno de los dos, y `xacro`
  no recibe argumentos sin valor —el error que ya nos costó una entrega—.

- [x] **Paso 2.** Comprobar que el launch parsea:

  ```bash
  cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup deepracer_spawn.launch.py --show-args
  ```

### Tarea 7: Comodín en los parámetros de los controladores  ✔ hecho 2026-08-10

**Archivo:** `deepracer_bringup/config/agent_control.yaml`

`controller_manager:` solo aplica a `/controller_manager`. Bajo espacio de nombres el gestor
se llama `/robot1/controller_manager` y no encontraría sus parámetros.

- [x] **Paso 1.** Anteponer `/**/` a las siete claves de primer nivel: `controller_manager` y
  los seis controladores. Ejemplo:

  ```yaml
  /**/controller_manager:
    ros__parameters:
      update_rate: 60  # Hz
  ```

  `/**` casa con cero o más segmentos, así que la misma clave sirve para
  `/controller_manager` y para `/robot1/controller_manager`.

- [x] **Paso 2.** Validar el YAML antes de lanzar nada:

  ```bash
  python3 -c "import yaml; d=yaml.safe_load(open('Robot/aws-deepracer/deepracer_bringup/config/agent_control.yaml')); print(list(d.keys()))"
  ```

  Esperado: siete claves, todas empezando por `/**/`.

### Tarea 8: Regresión con defecto vacío — *tu terminal* — ✔ hecho 2026-08-10

Antes de probar el espacio de nombres hay que demostrar que el comodín no rompió el caso de
un robot.

- [x] **Paso 1.** `cd ~/deepracer_sim_ws && colcon build --symlink-install --packages-select deepracer_bringup deepracer_description`
- [x] **Paso 2.** `./herramientas/lanzar_sim.sh`
- [x] **Paso 3.** `python3 herramientas/verificar_contrato.py`

  Esperado: `Las 3 comprobaciones pasan`. Si los controladores no salen activos, el comodín
  no está casando: parar aquí y revisar la sintaxis.

### Tarea 9: Un robot bajo espacio de nombres — *tu terminal* — ✔ hecho 2026-08-10

La expectativa **no** es que pase a la primera: es ver cómo falla. No pasó a la primera: el
plugin de tracción publicaba con nombres **absolutos** y el robot quedaba partido en dos
mitades. Causa raíz y arreglo en `S17_aplicacion_contrato.md`, «Paso D».

- [x] **Paso 1.** `./herramientas/lanzar_sim.sh namespace:=robot1`

- [x] **Paso 2.** `ros2 control list_controllers -c /robot1/controller_manager`

  Esperado: siete controladores `active`. Si el gestor no aparece, el bloque `<ros>` no llegó
  al plugin.

- [x] **Paso 3.** `ros2 topic list | grep -E "robot1|^/tf"`

  Esperado: `/robot1/cmd_vel`, `/robot1/scan`, `/robot1/odom`, `/robot1/robot_description`.

- [x] **Paso 4.** La comprobación con más dudas:

  ```bash
  ros2 topic list | grep -c "robot1/tf"
  ```

  Esperado: `0`. La predicción es que `tf2_ros::TransformBroadcaster` publica en `"/tf"`,
  nombre **absoluto**, y los absolutos no se ven afectados por el espacio de nombres. Si sale
  distinto de 0 la predicción era falsa: hay que añadir `<remapping>tf:=/tf</remapping>` al
  bloque `<ros>` del plugin de tracción y `remappings=[('/tf','/tf')]` al
  `robot_state_publisher`. **Registrar el resultado sea cual sea**, porque en la sesión
  anterior di por hecho lo contrario.

  **Resultado: `0`.** La predicción era correcta; no hizo falta ningún remapeo de `tf`.

- [ ] **Paso 5.** `ros2 run tf2_tools view_frames` — esperado: 12 marcos, todos con prefijo
  `robot1/`, un solo padre cada uno. *Se absorbe en el paso 3 de la tarea 10, que exige 24.*

- [x] **Paso 6.** Registrar en `S17_aplicacion_contrato.md` —incluidos los fallos— y
  commitear. *Registrado; el commit queda pendiente de tu autorización.*

**Criterio de cierre del día:** un robot funciona bajo `robot1` con los siete controladores
activos, o está escrito exactamente en qué punto falla. **Cumplido:** 7/7 activos,
verificador 5/5, y el coche arranca y se detiene por `/robot1/cmd_vel`.

---

## Lo que además salió el lunes 10 (no estaba en el plan)

El día se alargó porque la tarea 9 destapó un bloqueo y ese bloqueo destapó otros dos. Se
registra aquí porque cambia el contenido del martes.

### Tarea 9b: Topología de dos simuladores ✔ hecho 2026-08-10

**Evidencia:** `Documentos/Evidencia/S17_dos_simuladores.md`

Dos robots dentro de un mismo `gzserver` **no se pueden aislar**: `gazebo_ros` de Humble
aplica a todos los plugins el namespace del primer modelo cargado. La salida no es un parche
sino un cambio de topología: **un `gzserver` por robot**, cada uno con su `ROS_DOMAIN_ID` y su
`GAZEBO_MASTER_URI`. Es además la traducción fiel del alcance del anteproyecto (*"cada robot
opera de forma dedicada en un nivel específico"*) y mapea 1:1 al despliegue final, una
Raspberry Pi por vehículo.

Medido: aislamiento total del grafo, movimiento mutuamente independiente (3,34 m contra 6 mm
en el testigo) y RTF 0,998 en ambas instancias. **Esto invalida la tarea 10 tal como estaba
escrita**, que asumía un Gazebo compartido.

### Tarea 9c: Nav2 y AMCL bajo espacio de nombres ✔ hecho 2026-08-10

**Evidencia:** `Documentos/Evidencia/S17_nav2_namespaces.md`

`nav_amcl_demo_sim.launch.py` no contenía la palabra `namespace`, y el `global_costmap` fallaba
en bucle. Sin esto los dos robots coexisten pero no navegan, así que era el trabajo bloqueante.

Se modificaron dos launches y se escribió uno nuevo,
`deepracer_localization_sim.launch.py`, porque el de `nav2_bringup` falla **en silencio** bajo
namespace (sus nodos no llevan `namespace=` y remapea `/tf` de forma fija). Verificado el
cambio nulo parámetro a parámetro, y los dos robots alcanzaron objetivos `NavigateToPose`
simultáneamente a RTF 0,996.

### Tarea 9d: URIs `package://` de los meshes ✔ corregido, ⏳ sin verificar

Al preparar la evidencia visual, `RobotModel` de RViz fallaba en los 12 enlaces: los `.xacro`
escribían `package://meshes/...`, sin nombre de paquete. Se corrigieron 26 ocurrencias, RViz
pasó a cargar el modelo **y Gazebo dejó de dibujarlo**, porque cada uno resuelve la URI de
forma distinta. Arreglado en `deepracer_description/package.xml` exportando también
`${prefix}/..`. Detalle completo en el hallazgo colateral nº2 de `S17_nav2_namespaces.md`.

**Falta la comprobación visual.** Es el primer paso del martes.

---

# Martes 11 de agosto — Cerrar H1 de verdad

El estado real de H1 es: **funcionalmente demostrado, sin una corrida limpia que lo respalde de
principio a fin.** Las pruebas de aislamiento (9b) y de navegación (9c) son buenas, pero se
tomaron antes de tocar los `.xacro` en 9d. El martes no busca resultados nuevos: busca una sola
corrida reproducible que valga como evidencia del hito, y el commit que la fija.

### Tarea 10: Regresión visual tras la corrección de meshes — *tu terminal*

Es lo único que hoy está sin verificar. Va primero porque, si falla, todo lo demás se posterga.

- [ ] **Paso 1.** Un robot con espacio de nombres, con interfaz:

  ```bash
  cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1 2>&1 | tee /tmp/paso2.log
  ```

  Esperado: el vehículo **visible** en el visor de Gazebo (aleja la cámara: por defecto queda
  pegada al robot). Si sigue invisible, buscar `Unable to find file` en `/tmp/paso2.log`: ese
  mensaje trae la ruta exacta que no se encontró y cierra el diagnóstico sin adivinar.

- [ ] **Paso 2.** No cortar antes de ver estas tres líneas, que confirman que el plugin de
  control cargó dentro del espacio de nombres:

  ```
  [gzserver-1] [INFO] [gazebo_ros2_control]: Loading gazebo_ros2_control plugin
  [gzserver-1] [INFO] [gazebo_ros2_control]: Starting gazebo_ros2_control plugin in namespace: /robot1
  [gzserver-1] [INFO] [gazebo_ros2_control]: Loading controller_manager
  ```

  En la corrida fallida del lunes no aparecieron porque se interrumpió ~25 s tras el spawn.
  Sin ellas no existe `/robot1/controller_manager` y todo lo demás cae en cascada: los
  `Invalid frame ID "robot1/odom"` son consecuencia, no causa.

- [ ] **Paso 3.** `ros2 control list_controllers -c /robot1/controller_manager`

  Esperado: siete `active`. Si alguno queda `unconfigured`, es la carrera de carga documentada
  como hallazgo colateral nº1; se recupera con
  `ros2 control set_controller_state <nombre> inactive && ros2 control set_controller_state <nombre> active`.

- [ ] **Paso 4.** RViz, en el mismo espacio de nombres:

  ```bash
  rviz2 --ros-args -r __ns:=/robot1
  ```

  En `RobotModel`, poner **TF Prefix** = `robot1`. Los nombres de los enlaces del URDF van sin
  prefijo, pero `robot_state_publisher` sí prefija los marcos TF: es el diseño documentado en
  `deepracer.xacro:20-27`, no un error. El `__ns` hace además que el botón *Nav2 Goal* publique
  en `/robot1/goal_pose`, porque los plugins de Nav2 usan nombres relativos.

- [ ] **Paso 5.** Captura de Gazebo y captura de RViz, las dos con el modelo visible, a
  `Documentos/Evidencia/`. Son la evidencia gráfica de H1 para el entregable.

**Criterio de cierre:** el mismo modelo se ve en los dos visores a la vez. Es la prueba de que
la URI corregida sirve a los dos resolvedores, que era justamente el conflicto.

### Tarea 10b: Corrida completa de H1 y cierre — *tu terminal*

Repetir el resultado 3 de `S17_nav2_namespaces.md` sobre el código de hoy. **No es trabajo
nuevo**; es dejar constancia de que la corrección de meshes no alteró el comportamiento.

- [ ] **Paso 1.** Instancia 1:

  ```bash
  cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1
  ```

- [ ] **Paso 2.** Instancia 2, en otra terminal. Las dos variables de entorno son lo único que
  cambia:

  ```bash
  cd ~/deepracer_sim_ws && source install/setup.bash && GAZEBO_MASTER_URI=http://localhost:11346 ROS_DOMAIN_ID=2 ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot2 y:=2.0
  ```

- [ ] **Paso 3.** Un objetivo a cada uno, y anotar el resultado de los dos:

  ```bash
  ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0}, orientation: {w: 1.0}}}}"
  ```

  Esperado: `SUCCEEDED` en ambos. Si uno falla, **anotarlo tal cual**: un H1 con una excepción
  escrita vale más que un H1 declarado cerrado sin respaldo.

- [ ] **Paso 3b.** Aislamiento de mando, que es el punto 4 del criterio de cierre del contrato.
  **Esta es la prueba que de verdad importa**, y la única que puede fallar de forma interesante.

  Cuatro terminales. Las dos de lectura se dejan corriendo y se fotografían juntas:

  | Terminal | Orden |
  |---|---|
  | lectura robot1 (dominio 0) | `ros2 topic echo /robot1/odom --field pose.pose.position` |
  | lectura robot2 (dominio 2) | `ROS_DOMAIN_ID=2 ros2 topic echo /robot2/odom --field pose.pose.position` |
  | mando (dominio 0) | `ros2 topic pub --once /robot1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"` |
  | freno (dominio 0) | `ros2 topic pub --once /robot1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}}"` |

  `cmd_vel` es velocidad, no distancia: hay que **frenar explícitamente** antes de leer, o el robot
  sigue rodando con el último comando y contamina la medida.

  Esperado: la `x` de `robot1` cambia en metros; la de `robot2`, en milímetros. Si `robot2` se
  desplaza de verdad, hay un tópico global colándose y **H1 no está cerrado**.

  Repetir en el sentido contrario, comandando `robot2`. Un solo sentido no demuestra aislamiento:
  demuestra que un mensaje llegó a donde debía.

- [ ] **Paso 3c.** Capturas. Solo estas cuatro; el resto es decoración y ocupa repositorio:

  | Archivo | Qué debe verse |
  |---|---|
  | `S17_dos_gazebo_lado_a_lado.png` | las dos ventanas de Gazebo, cada una con su vehículo visible y su barra inferior legible (RTF, Sim Time) |
  | `S17_aislamiento_mando.png` | las dos terminales de `echo` una sobre otra, tras comandar `robot1`: metros arriba, milímetros abajo |
  | `S17_rviz_robot1_robotmodel.png` | RViz con `RobotModel` sin errores, `TF Prefix: robot1`, `Fixed Frame: map` |
  | `S17_dos_objetivos_succeeded.png` | las dos terminales de `send_goal` con `SUCCEEDED` |

  Ventana completa, sin recortar: la barra de Gazebo lleva el RTF, que es un dato de la evidencia.

  **No se fotografía «los robots no chocan».** No comparten espacio físico —procesos de simulación
  distintos—, así que esa imagen no probaría nada. La no-interacción física es una limitación
  declarada del alcance, no un resultado: ver §8 de `CONTRATO_INTERFACES.md`.

- [ ] **Paso 3d.** Evidencia textual, que es más barata y más fuerte que la fotográfica:

  ```bash
  mkdir -p Documentos/Evidencia/logs
  ros2 topic list --no-daemon > Documentos/Evidencia/logs/S17_topicos_dominio0.txt
  ROS_DOMAIN_ID=2 ros2 topic list --no-daemon > Documentos/Evidencia/logs/S17_topicos_dominio2.txt
  ros2 control list_controllers -c /robot1/controller_manager > Documentos/Evidencia/logs/S17_controladores_robot1.txt
  ros2 param get /robot1/global_costmap/global_costmap robot_base_frame >> Documentos/Evidencia/logs/S17_controladores_robot1.txt
  ros2 run tf2_tools view_frames
  ```

  `view_frames` en el dominio 0 debe dar **12 marcos con prefijo `robot1/`, raíz `map`, y ninguno
  de `robot2`**. Que no vea al otro robot es la prueba de aislamiento; es más fuerte que verlos
  juntos. El PDF que genera se pega directo al informe.

- [ ] **Paso 4.** Actualizar el criterio de cierre de `S17_nav2_namespaces.md` con la fecha de
  esta repetición, y quitar la advertencia de vigencia.

- [ ] **Paso 5.** Commit. Son once archivos y llevan días fuera de git; si algo se rompe hoy no
  hay a dónde volver.

  ```bash
  git add Robot/aws-deepracer/deepracer_bringup/launch/ Robot/aws-deepracer/deepracer_description/ Documentos/Evidencia/ Documentos/PLAN_S17_S18.md
  git commit -m "Add: Nav2 y AMCL bajo espacio de nombres, y correccion de las URIs de los meshes"
  ```

**Criterio de cierre del día:** H1 cerrado con evidencia reproducible y commiteado, o
documentado exactamente en qué punto falla.

### Si sobra tiempo

Por orden de utilidad, no de dificultad:

- [ ] `herramientas/lanzar_sim.sh` acepta puerto y dominio (hallazgo nº2 de `S17_dos_simuladores.md`).
  Hoy mata todos los `gzserver` al arrancar, lo que impide la segunda instancia.
- [ ] La carrera de carga de controladores (hallazgo nº1 de `S17_nav2_namespaces.md`).
  **Hay que arreglarla antes de medir tiempos de OE4**: un robot con una rueda motriz sin
  actuar falsea la dinámica.
- [ ] Que el argumento `gui` funcione de verdad (hallazgo nº3). Tres líneas. Importa porque la
  operación por defecto debe ser *headless*: la VRAM es el cuello de botella, no la CPU.

---

# Miércoles 12 de agosto — Entorno de dos niveles

Las tareas 11 y 12 las dejo escritas; tú cargas y miras.

### Tarea 11: Extraer `primer_piso` como modelo reutilizable

**Archivos:** `primer_piso/model.config`, `primer_piso/model.sdf`

Hoy la planta está embebida en `primer_piso_v2.world`. Para instanciarla dos veces tiene que
ser un modelo con directorio propio, como `pasillo_usta/`.

- [ ] **Paso 1.** Crear `primer_piso/model.config` con la convención de
  `pasillo_usta/model.config`:

  ```xml
  <?xml version="1.0" ?>
  <model>
      <name>primer_piso</name>
      <version>1.0</version>
      <sdf version="1.7">model.sdf</sdf>
      <author>
          <name></name>
          <email></email>
      </author>
      <description>Primera planta del edificio de la USTA. El segundo piso real es identico, de modo que el mundo de dos niveles instancia este mismo modelo dos veces.</description>
  </model>
  ```

- [ ] **Paso 2.** Extraer el bloque `<model name='primer_piso'>`, que ocupa las **líneas 236
  a 743** —la aparición de la línea 759 es la copia dentro de `<state>` y no se toca—:

  ```bash
  sed -n '236,743p' primer_piso_v2.world > /tmp/cuerpo.sdf
  ```

  y envolverlo en `<?xml version='1.0'?><sdf version='1.7'> ... </sdf>`.

  **No tocar la geometría.** Este paso es un traslado, no una edición: si algún muro se mueve
  hoy, mañana no se sabrá si el problema es del traslado o del segundo nivel.

- [ ] **Paso 3.** `gz sdf -k primer_piso/model.sdf` — esperado: sin errores.

- [ ] **Paso 4.** *Tu terminal.* Cargar el modelo solo y comprobar que los muros están donde
  estaban:

  ```bash
  cd ~/Documents/Tesis && gazebo --verbose -s libgazebo_ros_factory.so &
  ros2 run gazebo_ros spawn_entity.py -entity prueba -file primer_piso/model.sdf
  ```

### Tarea 12: Mundo de dos niveles

**Archivo:** `primer_piso_dos_niveles.world`

Los muros miden 2,5 m. La separación entre niveles se fija en **3,0 m** (2,5 de muro más 0,5
de entrepiso). El nivel superior **necesita losa de piso propia**: el `ground_plane` solo
existe en z=0 y sin losa el vehículo cae.

- [ ] **Paso 1.** Mundo con `sun`, `ground_plane` y dos instancias:

  ```xml
  <include>
    <uri>model://primer_piso</uri>
    <name>nivel_1</name>
    <pose>0 0 0 0 0 0</pose>
  </include>
  <include>
    <uri>model://primer_piso</uri>
    <name>nivel_2</name>
    <pose>0 0 3.0 0 0 0</pose>
  </include>
  ```

- [ ] **Paso 2.** Losa del nivel 2 como modelo estático. Las dimensiones cubren la huella de
  la planta, cuyos tramos de muro llegan a 44,25 m y 12,25 m:

  ```xml
  <model name='losa_nivel_2'>
    <static>true</static>
    <link name='losa'>
      <pose>10 0 2.95 0 0 0</pose>
      <collision name='losa_collision'>
        <geometry><box><size>50 20 0.1</size></box></geometry>
      </collision>
      <visual name='losa_visual'>
        <geometry><box><size>50 20 0.1</size></box></geometry>
      </visual>
    </link>
  </model>
  ```

  El centro en x=10 es una primera aproximación: la planta arranca en x≈−0,64 y se extiende
  hacia x positivo. Se ajusta tras verlo en el visor.

- [ ] **Paso 3.** *Tu terminal.* `gazebo --verbose primer_piso_dos_niveles.world` — esperado:
  dos plantas superpuestas, la de arriba con piso.

- [ ] **Paso 4.** *Tu terminal.* Comprobar que el vehículo se sostiene arriba:

  ```bash
  ./herramientas/lanzar_sim.sh world:=$HOME/Documents/Tesis/primer_piso_dos_niveles.world namespace:=robot2 z:=3.05
  ```

  Esperado: `robot2` aparece sobre la losa y no cae. Si la atraviesa, es que quedó solo el
  `<visual>` y falta el `<collision>`.

**Criterio de cierre del día:** el mundo de dos niveles carga y un vehículo se sostiene sobre
el nivel superior.

---

# Jueves 13 de agosto — Zona de transición y mapa del nivel 2

### Tarea 13: Zona de transición vertical

- [ ] **Paso 1.** Marcar en `primer_piso/model.sdf` el punto que corresponde al descanso de
  la escalera real, como un rectángulo visible **sin colisión** para que no estorbe la
  navegación. No es una escalera transitable: ningún vehículo sube. Como el modelo se
  instancia dos veces, queda automáticamente en las mismas coordenadas de las dos plantas.

  ```xml
  <link name='zona_transicion'>
    <pose>X Y 0.01 0 0 0</pose>
    <visual name='zona_transicion_visual'>
      <geometry><box><size>1.5 1.5 0.02</size></box></geometry>
      <material><ambient>0.9 0.4 0.1 1</ambient><diffuse>0.9 0.4 0.1 1</diffuse></material>
    </visual>
  </link>
  ```

  `X` e `Y` salen de mirar la planta en el visor. Es el único dato de este plan que no se
  puede fijar de antemano.

- [ ] **Paso 2.** Registrar las coordenadas en `ENTORNO_DE_EVALUACION.md`: el protocolo
  experimental las va a necesitar.

### Tarea 14: Mapa del nivel 2 — *tu terminal*

- [ ] **Paso 1.** Antes de mapear, verificar la causa raíz que invalidó toda la cartografía
  anterior al 5 de agosto:

  ```bash
  grep -n "max_laser_range" Robot/aws-deepracer/deepracer_bringup/config/slam_toolbox.yaml
  ```

  Esperado: `10.0`. Si dice `12.0`, corregir antes de mapear o se repite el error entero.

- [ ] **Paso 2.** Mapear, guardar, y comprobar la cobertura. El mapa anterior tenía 96,3 %
  libre y **0 % desconocido**, lo que significa que Nav2 planificaba por zonas que el LiDAR
  nunca vio. Un mapa correcto tiene desconocido claramente distinto de cero.

- [ ] **Paso 3.** Enviar un goal en el nivel 2 y comprobar que se alcanza.

- [ ] **Paso 4.** Commit.

**Criterio de cierre del día:** hay un mapa del nivel 2 con desconocido distinto de cero, y
un goal alcanzado sobre él.

---

# Viernes 14 de agosto — Diagnóstico de hardware

**Archivo:** `Documentos/Evidencia/S18_diagnostico_hardware.md`

Frente B, todo tuyo. Cuatro preguntas y ninguna más: es un diagnóstico acotado, no una puesta
en marcha.

- [ ] **Pregunta 1.** ¿El LiDAR real publica lecturas utilizables bajo la distribución
  instalada? Verificar `ros2 topic hz /scan` y contrastar el alcance real contra los 10,0 m
  supuestos —el número del que dependió el error de cartografía—.

- [ ] **Pregunta 2.** ¿Se puede comandar el vehículo desde ROS 2 sin pasar por la interfaz
  web? La marcha ya está verificada por la interfaz web (`https://youtu.be/ZGfAMnC4lYY`); lo
  que falta es el camino por ROS 2.

- [ ] **Pregunta 3.** ¿Cuál es la latencia de comunicación entre los dos vehículos sobre la
  red disponible? Es el número del que depende el esquema de relevo: se mide, no se supone.

- [ ] **Pregunta 4.** ¿Qué implicaría emplear ROS 2 Jazzy en lugar de Humble? El anteproyecto
  admite las dos («ROS 2 (Humble o Jazzy)»). Respuesta corta y decisión registrada; no es una
  migración.

- [ ] Cerrar el documento con las cuatro respuestas y commitear.

**Insumo para S21:** la respuesta a las preguntas 1 y 2 aplicada al *segundo* vehículo es lo
que alimenta el punto de decisión de S21. Si el segundo vehículo no responde, se sabe hoy y
no dentro de tres semanas.

**Criterio de cierre de S18:** H1 cerrado; el mundo de dos niveles carga y se navega sobre
él; el diagnóstico responde las cuatro preguntas.

---

## Lo que se corrió a S19 por los festivos

La **matriz de requisitos** estaba planeada para S18 y no cabe en cinco días. Pasa a S19
(martes 18 – viernes 21, con el lunes 17 festivo), donde ya estaba programado el protocolo
experimental. Son actividades del mismo frente T y se hacen juntas: un requisito sin prueba
asociada no es un requisito, así que la matriz y el protocolo se escriben mejor a la vez.

## Qué queda deliberadamente fuera del periodo

- El nodo de coordinación y el protocolo de relevo — S19 y S20.
- La interfaz móvil HRI — más adelante en el frente A.
- El merge de `integracion-nav2` a `main` — decisión tuya, idealmente tras revisión de Jonny.
- La limpieza de `stash@{0}` y de `~/Documents/respaldo-*` — cuando H1 esté cerrado y
  commiteado, no antes.
- Refinar Nav2. Esa línea está cerrada.

## Riesgo del periodo

Si H1 no cierra el martes 11, el entorno de dos niveles se corre al miércoles y el jueves, y
el diagnóstico de hardware sale de S18. **Lo que cede es el diagnóstico, no H1**: H1 bloquea
todo lo multi-robot, y el diagnóstico solo alimenta un punto de decisión que es de S21.
