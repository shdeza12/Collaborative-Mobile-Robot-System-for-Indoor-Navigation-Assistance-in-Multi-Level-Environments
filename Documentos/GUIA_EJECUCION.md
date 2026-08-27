# Guía de ejecución y visualización

Cómo levantar cada escenario vigente del proyecto y **cómo verlo**. Existe porque los
comandos estaban repartidos entre los informes de evidencia de S17 y S18, y reconstruirlos
desde ahí antes de una demostración cuesta más que hacerla.

Se limita a lo que ya está comprobado en este repositorio. El escenario de SLAM está en §5;
para el recorrido de mapeo y la verificación de cobertura del mapa,
[`guia_simulacion_slam.md`](guia_simulacion_slam.md); para el detalle de la pila Nav2,
[`guia_navegacion_nav2.md`](guia_navegacion_nav2.md).

**Regla que se aplica a todos los comandos:** cada terminal nueva necesita su propio
`cd ~/deepracer_sim_ws && source install/setup.bash`. El workspace no se sourcea solo.

**Dónde está el repositorio.** Los comandos que llaman a `herramientas/…` empiezan por
`cd "$TESIS"`. Define esa variable una vez por terminal, con la ruta de **tu** clon:

```bash
echo 'export TESIS=$HOME/Tesis' >> ~/.bashrc && source ~/.bashrc        # ← cámbialo si clonaste en otro sitio
```

Se escribe en `~/.bashrc`, y no sólo en la terminal actual, porque esta guía abre **tres o
cuatro terminales a la vez** y la variable no se hereda entre ellas. Si en una terminal se
queda sin definir, `cd "$TESIS"` no va a ninguna parte —`cd ""` no es un error para bash— y lo
que falla es el `herramientas/…` siguiente, con un `No such file or directory` que señala al
script y no a la variable. Ante esa duda, `echo $TESIS`: si sale una línea vacía, es esto.

Es la única ruta del proyecto que depende de tu equipo. Va como variable, y no escrita en cada
comando, por dos motivos: así solo hay un sitio que corregir, y así la guía no afirma dónde
clonaste. Aquí hubo una **ruta fija** con el `Documents/` de un equipo concreto incrustado, que
es la forma más traicionera del error porque lleva `$HOME` y parece portable;
`herramientas/verificar_repositorio.sh` la rechaza por eso.

El `cd` sí hace falta, aunque parezca ruido: `herramientas/…` a secas solo funciona si ya
estabas dentro del repositorio, y el error que da —`No such file or directory`— no dice cuál
era el problema.

**Atajo:** [`herramientas/robot.sh`](../herramientas/robot.sh) hace todo eso —el `source`, el
dominio, el puerto de Gazebo, la pose de spawn y el `GAZEBO_MODEL_PATH`— desde una sola tabla,
y carga **el mismo mundo** que los escenarios de esta guía. Los comandos largos siguen siendo la
referencia de lo que ocurre por debajo; el script es para no teclearlos. Está descrito en el §9.

---

## 0. Antes de empezar: dejar el equipo limpio

Un `gzserver` anterior ocupa el puerto 11345 y el siguiente lanzamiento falla de una forma
que no se parece a un conflicto de puertos. Comprobar y, si hay algo vivo, cerrarlo:

```bash
pgrep -af "gzserver|gzclient|rviz2"
```

La forma recomendada es dejar que el script lo haga, una vez por robot. Filtra por
`ROS_DOMAIN_ID` y se salta los shells, así que no puede cerrarte la terminal:

```bash
cd "$TESIS" && herramientas/robot.sh robot1 parar && herramientas/robot.sh robot2 parar
```

A mano, si hace falta —mata **los dos** dominios de golpe, no lo uses con un compañero
trabajando en el otro robot:

```bash
pkill -f "ros2 launch deepracer_bringup" ; pkill -x gzserver ; pkill -x gzclient ; pkill -x rviz2 ; sleep 4 ; ros2 daemon stop ; ros2 daemon start
```

**El `pkill` del `ros2 launch` va primero y es imprescindible.** Matar sólo `gzserver` deja
un estado zombi difícil de diagnosticar: el `ros2 launch` sigue vivo con los nodos de Nav2
levantados, pero sin Gazebo no hay `/clock` ni `controller_manager`, AMCL acaba cayendo y el
árbol TF se parte en dos. El síntoma que se ve es **`Fixed Frame: Frame [map] does not
exist`** en RViz, que parece un problema de RViz y no lo es. En el log del launch aparece
`CRITICAL FAILURE: SERVER amcl IS DOWN` y `Tf has two or more unconnected trees`.

Si tras el `pkill` siguen quedando nodos, se matan por PID:

```bash
pgrep -af "gzserver|gzclient|rviz2|nav2|amcl|deepracer" | grep -v "bin/bash"
```

**`pkill -f rviz2` mata también la terminal que lo ejecuta** si el comando escrito contiene
la cadena `rviz2`. Por eso arriba va `pkill -x rviz2`, que casa el nombre exacto del proceso.

El `ros2 daemon` no es adorno: tras matar Gazebo el daemon queda corrupto y los
`ros2 control load_controller` posteriores fallan con `!rclpy.ok()`.

---

## 1. Escenario A — un robot, con mapa y RViz

Es el escenario por defecto y el que sirve para enseñar el sistema a alguien. Levanta la
simulación, Nav2, AMCL y el servidor de mapas de una vez.

### Terminal 1 — simulación + navegación + localización

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1
```

No hace falta pasar `world:=`, `map:=` ni la pose: los tres valores por defecto salen de
**este mismo clon** del repositorio (`mundo_definitivo_piso1.world`, `mundo_definitivo_piso1.yaml`
y la fila `robot1` de `POSE_INICIAL`). Mundo y mapa van en pareja; cambiar uno solo hace que
AMCL localice contra una geometría distinta de la simulada, y el síntoma —deriva creciente—
no se parece a un error de configuración.

> **Esta línea estuvo rota entre el 20 y el 22 de agosto** y conviene saber por qué, porque el
> fallo no era visible. Este launch declaraba su propia pose por defecto en `(0, 0)`, que era
> correcta cuando el mundo era `primer_piso_v2.world` pero en el mundo de entonces cae en la
> explanada vacía **entre** los dos pasillos. Gazebo abría, el vehículo aparecía, los siete
> controladores quedaban activos y no había un solo mensaje de error: lo que no había era
> pasillo alrededor. Hoy la pose sale de una sola tabla y
> [`herramientas/verificar_pose_spawn.py`](../herramientas/verificar_pose_spawn.py) comprueba en
> cada corte que siga cayendo en celda libre del mapa.

**Esperar** a leer en el log `Starting gazebo_ros2_control plugin in namespace: /robot1`.
El plugin tarda, y juzgar el lanzamiento antes de esa línea lleva a reiniciar sin motivo.

### Terminal 2 — verificación (hacerla siempre antes de enseñar nada)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 control list_controllers -c /robot1/controller_manager
```

| Resultado | Qué significa |
|---|---|
| 7 controladores en `active` | Correcto: `joint_state_broadcaster` + 4 ruedas + 2 hinges de dirección |
| Alguno en `unconfigured` | Carrera de carga conocida. Recuperable, ver abajo |
| `Unknown state 'start'` | Regresión de la migración Foxy→Humble en `agent_control.yaml` |

Recuperar un controlador que quedó atrás:

```bash
ros2 control set_controller_state <nombre> inactive -c /robot1/controller_manager && ros2 control set_controller_state <nombre> active -c /robot1/controller_manager
```

### Terminal 3 — RViz

**Antes de abrir RViz, comprobar que el frame `map` existe.** Abrirlo antes es la causa más
común del `Frame [map] does not exist`:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && timeout 10 ros2 run tf2_ros tf2_echo map robot1/base_link
```

Cuando imprima una traslación, RViz:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && rviz2 -d $(ros2 pkg prefix deepracer_description)/share/deepracer_description/rviz/robot1_completo.rviz --ros-args -r __ns:=/robot1 -p use_sim_time:=true
```

**Si RViz abre con un único display `Grid` y el título termina en `*`, la ruta del `-d` no
existe.** RViz no avisa: cuando el archivo falta cae a la configuración vacía y deja el
nombre pedido en el título. Pasa cada vez que se añade un `.rviz` nuevo al repositorio y no
se recompila `deepracer_description`, porque `--symlink-install` enlaza archivo por archivo
en tiempo de compilación y un archivo nuevo no existe en `install/` hasta entonces. Se
arregla con `colcon build --symlink-install --packages-select deepracer_description`.

**Usar `robot1_completo.rviz`, no `nav2_robot1_view.rviz`.** El segundo sólo trae Grid,
RobotModel, TF y Map: **no tiene LaserScan, ni costmaps, ni el plan**, así que con él no se
ve nada de lo que interesa. El primero se derivó de `nav2_default_view.rviz` prefijando todos
los tópicos con `/robot1` y corrigiendo tres cosas que venían mal en el original: el
`RobotModel` estaba en `Enabled: false`, el `TF Prefix` vacío —con lo que buscaba `base_link`
en vez de `robot1/base_link`— y las partículas de AMCL apagadas. Los displays de la Realsense
y del bumper, que este vehículo no tiene, quedaron desactivados para que no salgan en rojo.

**El `-r __ns:=/robot1` es obligatorio.** Sin él, el botón *Nav2 Goal* de la barra publica en
`/goal_pose` sin prefijo, el `bt_navigator` nunca lo recibe y el panel lateral repite
`navigate_to_pose action server is not available`. Con el namespace puesto, el log dice
`NavigateToPose will be called using the BT Navigator's default behavior tree`, que es la
señal de que el panel quedó conectado.

**`use_sim_time:=true` importa.** Sin él RViz sella con el reloj de pared mientras todo lo
demás usa el de Gazebo, y los mensajes se descartan por antigüedad: el síntoma es un RViz
vacío con los tópicos publicando correctamente.

Qué se debe ver: la planta en gris (el mapa), el modelo del vehículo, el abanico del LiDAR
y los costmaps. Si el robot no queda encuadrado, clic en el viewport y tecla **`f`**; para
que la cámara lo siga, panel *Views* → `Orbit` → *Target Frame* = `robot1/base_link`.

### Comprobar que RViz está realmente funcional

RViz **no falla ruidosamente**: si un display no puede dibujar, se pone en rojo en el panel
lateral y el resto de la escena sigue apareciendo normal. Conviene verificar por fuera.

**1. Que el árbol TF llega del mapa al vehículo.** Es lo que sostiene toda la escena:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && timeout 10 ros2 run tf2_ros tf2_echo map robot1/base_link
```

Debe imprimir una traslación. Los primeros mensajes `Invalid frame ID "map"` y
`Lookup would require extrapolation into the past` son normales durante los primeros
segundos: AMCL aún no ha publicado `map → robot1/odom`. Si persisten pasado medio minuto, el
problema es AMCL, no RViz.

**2. Que el `RobotModel` tiene sus mallas.** El error clásico es
`Could not load resource package://deepracer_description/meshes/...`, que deja al vehículo
invisible o reducido a los ejes. El URDF publicado referencia cinco mallas
—`deepracer.STL`, `laser.STL`, `left_steering_hinge.STL`, `right_steering_hinge.STL`,
`zed_camera_link.STL`— y la comprobación de que todas resuelven en disco está automatizada:

```bash
cd "$TESIS" && bash herramientas/verificar_instalacion.sh
```

**Esperado: `32 comprobaciones pasan, 0 fallan`.**

Si salen 2 fallos de `GAZEBO_MODEL_PATH` y de `los model:// externos resuelven`, **no es un
problema del modelo**: es que esa terminal no cargó `~/.bashrc`, donde está la línea. Se
arregla con `exec bash` y se vuelve a ejecutar. Afecta a los mundos que usan `model://`
—**entre ellos `mundo_definitivo_piso1.world`, que es el que se carga por defecto**—, que abrirían
**vacíos y sin dar error**.

**3. Que el `RobotModel` recibió la descripción.** El tópico se publica con durabilidad
`Transient Local`; un `ros2 topic echo` normal se queda esperando para siempre y parece que
no publica nadie:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic echo /robot1/robot_description --once --full-length --qos-durability transient_local --qos-reliability reliable | grep -oE "package://[^\"]+" | sort -u
```

Debe listar las cinco mallas.

> **Comprobado el 2026-08-20** sobre este escenario: 7 controladores `active`, `map →
> robot1/base_link` resuelve, las 5 mallas existen en disco (`deepracer.STL` son 773 KB
> reales), el log de RViz sale limpio —solo `Stereo is NOT SUPPORTED`, que es informativo— y
> `verificar_instalacion.sh` da 31/31.

**Un detalle que engaña al verificar mallas a mano:** bajo `--symlink-install` los archivos
del `install/` son enlaces simbólicos al repositorio. `stat -c%s` devuelve entonces la
longitud del enlace (~90 bytes) y parece que los STL están vacíos o son punteros de Git LFS.
Hay que usar `stat -Lc%s`, que sigue el enlace.

---

## 2. Escenario B — teleoperación

Con el escenario A corriendo, en una terminal aparte:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

Sin namespace el remapeo sobra: `teleop_twist_keyboard` ya publica en `/cmd_vel`.

| Tecla | Efecto |
|---|---|
| `i` / `,` | adelante / atrás |
| `j` / `l` | giro izquierda / derecha |
| `k` | **detener** |
| `z` / `x` | bajar / subir velocidad lineal |

**Frenar siempre con `k` antes de soltar el foco del teclado.** `cmd_vel` es velocidad, no
distancia: el vehículo sigue rodando con el último comando recibido, y eso contamina
cualquier medición posterior.

**No teleoperar con un objetivo de Nav2 activo.** `controller_server` publica en el mismo
`/robot1/cmd_vel` y los dos comandos se pisan; el vehículo parece poseído y no hay error en
ningún log.

Cerrar el lazo, en otra terminal:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic echo /robot1/odom --once
```

---

## 3. Escenario C — enviar un objetivo de navegación

Dos vías. La visual, desde RViz: botón **2D Pose Estimate** si AMCL no ha convergido, y
luego **Nav2 Goal** para clicar el destino.

La reproducible, desde consola —es la que se usa para medir, porque deja constancia escrita
del objetivo:

El destino es **ETM1**, una de las quince localizaciones de
[`puntos_interes.yaml`](../Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml).
Conviene usar destinos de ese archivo y no coordenadas inventadas: son puertas reales del
pasillo, con su holgura medida, y son las mismas que verá la HRI.

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: robot1/map}, pose: {position: {x: -15.92, y: 10.59, z: 0.0}, orientation: {w: 1.0}}}}"
```

El marco es **`robot1/map`, con prefijo**. Aquí estuvo escrito lo contrario —«el marco es `map`
sin prefijo, es el ancla común a los dos robots, con `robot1/map` la meta se rechaza»— y era
falso en las dos mitades: el 2026-08-24 se prefijó también `map`, y con la meta en `map` a secas
el marco no existe, el planificador no puede transformarla y Nav2 acaba en `ABORTED`. `map` no
era un ancla común sino **dos mapas distintos con el mismo nombre**, que hoy no chocan solo
porque cada robot vive en su propio dominio DDS. El razonamiento completo está en el comentario
de `deepracer_localization_sim.launch.py`. Sin namespace —un solo robot— el marco sí es `map` a
secas, que es el caso de los ejemplos del `README.md`.

**`SUCCEEDED` no significa que el vehículo llegó**, solo que el árbol de comportamiento
terminó. La comprobación válida es leer `/robot1/odom` al terminar y comparar contra el
objetivo, porque el controlador se mide contra AMCL y no contra la verdad del simulador:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic echo /robot1/odom --once
```

Lo medido el 21-ago sobre este mundo, con los tres destinos probados, fue **0,177 – 0,296 m**
de error. El del medio, ETM13, quedó **fuera** de la `xy_goal_tolerance` de 0,25 m y aun así
Nav2 devolvió `SUCCEEDED`: por eso esta comprobación no es opcional.

---

## 4. Escenario D — la maniobra de giro (retorno en el pasillo)

El detalle completo está en
[`Evidencia/S19_conversion_cmdvel_ackermann.md`](Evidencia/S19_conversion_cmdvel_ackermann.md).
Aquí va lo justo para **reproducirla y saber qué mirar**.

### Qué es y por qué importa

Un DeepRacer es Ackermann: **no gira sobre su eje**. Para volver por donde vino tiene que
hacer una maniobra de dos medios círculos —un arco en reversa, una cúspide, y un arco hacia
adelante—, que es la que planteó el director. Sin ella no hay recorrido de ida y vuelta, y
sin ida y vuelta el objetivo específico 4 no se puede medir.

**No hubo que programar nada.** `nav2_params_nav_amcl_sim_demo.yaml` ya traía
`motion_model_for_search: "REEDS_SHEPP"` y `allow_reversing: true`. Lo que faltaba era
probarlo: hasta S18 todas las metas validadas quedaban **por delante** del vehículo, así que
la maniobra nunca se ejercitó.

Lo medido: arco en reversa de 46°, cúspide, arco adelante de 102° — **148° de giro en 4 s
dentro de una caja de 1,0 × 0,4 m**.

> Esas cifras se tomaron el 18-ago **sobre `primer_piso_v2.world`**, con la pose de arranque
> `x:=25.0 y:=1.45` que ya no existe en el mundo vigente. El procedimiento sigue valiendo y la
> maniobra sigue estando en los parámetros; los grados y los segundos hay que volver a medirlos
> en `mundo_definitivo.world` con los comandos de abajo. **No citar los 148° como resultado de
> este escenario hasta repetirlo.**

### Cómo lanzarla

El arranque por defecto ya sirve: `robot1` nace en el tramo norte-sur mirando **al norte**
(`yaw = 1,5708`), y el destino **Escaleras** queda 1,4 m **detrás**, además con rumbo de
llegada opuesto (`yaw = −1,5708`). No hay que pasar pose:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1
```

Grabar antes de mandar la meta, en otra terminal:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 bag record -o /tmp/v_p1 /robot1/plan /robot1/odom /robot1/cmd_vel /robot1/amcl_pose
```

Y la meta, en una tercera:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: robot1/map}, pose: {position: {x: -19.43, y: 5.91}, orientation: {z: -0.7071, w: 0.7071}}}}"
```

La `orientation` de aquí **no** es la identidad como en el escenario C: es el cuaternión de
`yaw = −π/2`, que es lo que obliga a la maniobra. Con `w: 1.0` el vehículo llegaría al mismo
punto mirando al norte y no habría nada que medir.

**Manda la meta dentro de los primeros 30 s tras el arranque.** Con el robot parado más
tiempo, la deriva en reposo introduce un desvío inicial que confunde el diagnóstico.

Medir después:

```bash
cd "$TESIS" && python3 herramientas/analizar_maniobra.py /tmp/v_p1 -19.43 5.91
```

> Las seis corridas de referencia del 18-ago se grabaron **sin namespace** y contra el mundo
> anterior, así que sus bags llevan `/odom` y `/plan` a secas. Los comandos de arriba usan
> `robot1` porque es lo que hace el resto de la guía; si vuelves a abrir uno de aquellos bags,
> los nombres de tópico son los de entonces.

### Qué mirar en RViz

La maniobra **no se ve** en una captura del pasillo entero: ocupa un metro de dieciséis. Por
eso la evidencia son gráficas (`herramientas/graficar_plan.py`,
`herramientas/graficar_seguimiento.py`) y no una pantalla de RViz. En vivo, sube el zoom
sobre el vehículo y mira el display **Path** del plan global: la cúspide es el punto donde la
línea se dobla sobre sí misma.

### El defecto que apareció midiéndola, y que ya está corregido

`geometry_msgs/Twist` define `angular.z` como **velocidad angular en rad/s**. El plugin de
Gazebo lo tomaba como **ángulo de dirección**: lo saturaba contra `max_steer_` y lo metía en
`tan()`. El mismo error estaba en `cmdvel_to_servo_node.py` del robot real —lo único
afortunado, porque no había divergencia sim/hardware que reconciliar.

La ganancia efectiva del volante salía **v / 0,164**, o sea que variaba por un factor de 4 a
lo largo del rango de velocidad y el controlador no lo sabía: a 0,5 m/s giraba 3,05 veces más
cerrado de lo pedido; a 0,12 m/s, un 27 % menos.

Corregido con el modelo de bicicleta despejado, `δ = atan(wz · L / v)`:

| métrica | antes → después (P1) | antes → después (P2) |
|---|---|---|
| Giro real vs comandado (RMS) | 0,298 → **0,111** rad/s | 0,256 → **0,130** rad/s |
| Error real de llegada | 0,255 → **0,091** m | 0,152 → **0,124** m |
| Error de localización (mediana) | 0,224 → **0,121** m | 0,090 → **0,045** m |

**Criterio para saber si una corrida nueva está sana:** el RMS de giro real contra comandado
debe quedar por debajo de 0,15 rad/s. Si vuelve a superar 0,25 rad/s, la corrección se
rompió.

### Dos cosas que hay que decir al enseñar esto

**`SUCCEEDED` no basta, y hay un defecto abierto en la llegada.** El verificador de meta está
en `stateful: True`: cuando cumple la tolerancia de posición la da por buena y deja de
comprobarla, y a partir de ahí solo exige el rumbo. Como un Ackermann no gira sobre su eje,
se pone a maniobrar en el sitio y nunca cierra los últimos grados. Hay dos corridas que
terminaron en `ABORTED` y `CANCELED` con **80 cúspides ejecutadas contra 2 planificadas**.
**Es el siguiente defecto a atacar** y bloquea la campaña de OE4, porque una tasa de éxito
medida con este verificador cuenta como fallos maniobras que llegaron bien.

**La maniobra de dos medios círculos no siempre aparece, y eso es correcto.** Si el rumbo de
salida y el de llegada coinciden, Reeds-Shepp resuelve sin cúspide retrocediendo en S. La
cúspide sólo hace falta cuando hay que voltear el vehículo. Antes de la corrección, las 6
cúspides de la prueba 2 no eran la maniobra: eran el síntoma de que el vehículo se salía del
plan y el controlador improvisaba para recuperarse.

**Y las métricas de llegada se reportan contra `/odom`, no contra Nav2.** En simulación
`/odom` es la pose verdadera de Gazebo. En una corrida, Nav2 midió 0,144 m de error cuando el
error real era 0,230 m: la localización se equivocaba más que la tolerancia que decía estar
cumpliendo. En un pasillo recto el LiDAR casi no observa la posición a lo largo del pasillo
—todos los puntos se ven iguales—, y eso es una limitación del entorno, no de la
configuración.

---

## 5. Escenario E — SLAM: construir el mapa en vez de cargarlo

Los escenarios A a D **cargan** un mapa ya hecho y localizan contra él con AMCL. Este lo
construye: `slam_toolbox` publica `map` a partir del LiDAR y la odometría.

**No se puede montar encima del escenario A.** AMCL y `slam_toolbox` publican los dos el
marco `map` y la transformada `map → odom`. Si coexisten, el árbol TF tiene dos padres para
`odom` y la pose salta entre ambas estimaciones. Antes de lanzar SLAM hay que bajar el
escenario A con la limpieza de §0.

### Terminal 1 — simulación base, sin Nav2

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup deepracer_sim.launch.py namespace:=robot1
```

### Terminal 2 — slam_toolbox

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup slam_toolbox.launch.py namespace:=robot1
```

### Terminal 3 — RViz

La misma configuración del escenario A. El display *Map* apunta a `/robot1/map`, que es
donde publica tanto `map_server` como `slam_toolbox`:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && rviz2 -d $(ros2 pkg prefix deepracer_description)/share/deepracer_description/rviz/robot1_completo.rviz --ros-args -r __ns:=/robot1 -p use_sim_time:=true
```

Los displays de Nav2 —*Global Planner*, *Controller*, *Amcl Particle Swarm*— se quedan
vacíos, y es correcto: esos nodos no están corriendo. Lo que tiene que verse es el mapa
creciendo, el LiDAR y el modelo del vehículo.

### Verificación: comprobar que el YAML se anidó bajo el namespace

Este es el paso que no se puede saltar. `slam_toolbox.yaml` tiene la clave de primer nivel
`slam_toolbox:`, que solo casa con un nodo llamado `/slam_toolbox`. Bajo namespace el nodo
pasa a ser `/robot1/slam_toolbox`, la clave deja de casar y el nodo **arranca con todos los
valores por defecto del código, sin ningún ajuste de este repositorio**. El fallo es
silencioso: SLAM levanta y mapea, solo que con parámetros dimensionados para una pista de
carreras pequeña, y el mapa del pasillo sale sin enlazar. El launch lo evita anidando el
YAML con `root_key`, y esto lo comprueba:

```bash
ros2 param get /robot1/slam_toolbox max_laser_range ; ros2 param get /robot1/slam_toolbox loop_search_maximum_distance ; ros2 param get /robot1/slam_toolbox scan_topic
```

Esperado **9.5**, **8.0** y **/robot1/scan**. Son valores propios del repositorio, ajustados
al pasillo de 58,2 m; los del upstream son otros. Si salen distintos, el anidado falló y el
mapa que se produzca no sirve.

Medido el 2026-08-20 **sobre `primer_piso_dos_niveles.world`**, que era el escenario de
entonces; de ahí que el robot2 aparezca a z ≈ 3 y no en el pasillo de y = −4,48. En robot1:
los nueve parámetros consultados salieron con los valores
del repositorio, y el mapa pasó de 263 × 218 a 352 × 225 celdas mientras el vehículo
avanzaba hasta x = 7,06 m. En robot2, sobre el dominio 2, los mismos parámetros y un mapa
de 155 × 103 a 268 × 119 con el vehículo en x = 7,55 m y z = 2,993, es decir sin caerse al
nivel 1.

**Anomalía anotada el 2026-08-20, sin resolver.** En robot2 el mapa medía 363 celdas de
ancho con el vehículo parado en el origen y **263** después de avanzar 7,3 m: el borde
trasero pasó de −9 m a −3,7 m, es decir el mapa se recortó por detrás en vez de crecer. En
robot1 el crecimiento fue limpio y monótono (263 → 352 → 373). No bloquea el escenario
—SLAM construye el mapa en los dos robots— pero cae del lado del **riesgo R10**, que ya
tiene los dos mapas del repositorio rechazados por cobertura insuficiente. Conviene medirlo
con `herramientas/verificar_mapa.py` antes de dar por bueno cualquier mapa nuevo.

### Los dos robots a la vez

Igual que en el escenario F: el segundo robot va en su propio `GAZEBO_MASTER_URI` y su
propio `ROS_DOMAIN_ID`, y cada uno lleva su `slam_toolbox`.

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && GAZEBO_MASTER_URI=http://localhost:11346 ROS_DOMAIN_ID=2 ros2 launch deepracer_bringup deepracer_sim.launch.py namespace:=robot2 x:=-21.889 y:=-8.379 yaw:=0
```

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ROS_DOMAIN_ID=2 ros2 launch deepracer_bringup slam_toolbox.launch.py namespace:=robot2
```

Comprobado el 2026-08-20 con los dos SLAM simultáneos: moviendo **solo** robot2, este
avanzó 7,34 m y robot1 se desplazó 4,9 mm, del mismo orden que los 6 mm de deriva numérica
medidos en S17. El aislamiento se mantiene con `slam_toolbox` corriendo en los dos.

Los dos publican el marco **`robotN/map`, prefijado**, igual que el resto de los marcos del
vehículo (`robot1/odom`, `robot1/base_link`). Este párrafo decía que `map` iba sin prefijar
«porque es el ancla común y los dominios ROS evitan la colisión»; desde el 2026-08-24
`map_frame` se prefija también, aquí y en el launch de localización. Confiar en el aislamiento
por dominio era temporal por definición: el relevo del hito H3 exige que los dos robots
compartan grafo, y ese día dos `map` con geometrías distintas sí colisionan.

**El tópico sí se prefija.** `slam_toolbox` crea el publicador del mapa con el nombre
absoluto `/map`, de modo que el namespace del nodo no lo alcanza. El launch añade un remap
a `/robot1/map` para que la misma configuración de RViz sirva para mapear y para navegar.
Sin ese remap el mapa aparece vacío en RViz y no hay ningún error que lo explique.

### Guardar el mapa

El procedimiento y la verificación de cobertura están en
[`guia_simulacion_slam.md`](guia_simulacion_slam.md). Bajo namespace hay que redirigir el
tópico, porque `map_saver_cli` escucha `/map`:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run nav2_map_server map_saver_cli -f /tmp/mapa_candidato --ros-args -p use_sim_time:=true -r map:=/robot1/map
```

---

## 6. Escenario F — dos robots, dos niveles

La topología adoptada es **un `gzserver` por robot**, porque `gazebo_ros` de Humble aplica a
todos los plugins el namespace del primer modelo cargado y dentro de un mismo simulador los
dos robots no se pueden aislar. Cada proceso carga **el mundo de su piso**, con un solo
vehículo dentro.

> **Hasta el 2026-08-23 los dos cargaban el mismo mundo**, `mundo_definitivo.world`, con el
> argumento de que así había «una sola geometría canónica». El argumento se cayó al medirlo:
> aquel mundo traía los dos pasillos en la **misma escena** de Gazebo, y aislar el grafo de ROS
> con `ROS_DOMAIN_ID` no aísla la escena. El LiDAR simulado alcanza 10,0 m y entre los dos
> pasillos hay 5,44 m, así que desde 61 posiciones libres del piso 1 los rayos llegaban a
> paredes del piso 2 y volvían con distancia —justo en el tramo norte-sur donde nace `robot1` y
> donde está el punto de transferencia—. Partir el mundo fue una **extracción pura**: 25 paredes
> al piso 1 y 34 al piso 2, con los rectángulos idénticos antes y después y el `.pgm` del mapa
> del piso 1 igual byte a byte.

No hace falta `world:=`: cada robot toma el mundo de su fila en `POSE_INICIAL`, y sale del mismo
repositorio del que se compiló el código.

### Terminal 1 — robot1, piso 1, dominio 0

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup deepracer_sim.launch.py namespace:=robot1
```

### Terminal 2 — robot2, piso 2, dominio 2

Lo único que cambia son las dos variables de entorno y la **ordenada** de nacimiento:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && GAZEBO_MASTER_URI=http://localhost:11346 ROS_DOMAIN_ID=2 ros2 launch deepracer_bringup deepracer_sim.launch.py namespace:=robot2 x:=-21.889 y:=-8.379 yaw:=0
```

`GAZEBO_MASTER_URI` separa los dos Gazebo; `ROS_DOMAIN_ID` separa los dos grafos ROS. No
hace falta ningún cambio en el código ni en los `.xacro`.

> **Estas poses no se teclean a ojo, y escritas aquí son una copia.** La original es
> `POSE_INICIAL`, en
> [`deepracer_raiz_repo.py`](../Robot/aws-deepracer/deepracer_bringup/launch/deepracer_raiz_repo.py):
> la única tabla de poses del proyecto, medida sobre el SDF de `mundo_Definitivo` y comprobada
> con el LiDAR. Estas dos líneas están escritas enteras a propósito, porque el escenario existe
> para enseñar **lo que ocurre por debajo**; el precio es que son las únicas del repositorio que
> pueden quedarse viejas sin que nadie avise. Antes de fiarte de ellas, contrástalas:
>
> ```bash
> cd "$TESIS" && herramientas/robot.sh robot2 sim
> ```
>
> hace exactamente esto mismo, leyendo la pose de la tabla, y no hay nada que teclear.

> **Por qué `x:=`/`y:=` y ya no `z:=3.03`.** Hasta el 2026-08-20 el escenario corría sobre
> `primer_piso_dos_niveles.world`, donde el piso 2 era la misma planta elevada a z = 3,0 y el
> robot2 nacía en z = 3,03 para asentarse en 2,993. Ahora los dos pisos son **pasillos distintos,
> uno al lado del otro en Y**, cada uno en su propio mundo. Pasar `z:=3.03` aquí haría caer al
> vehículo desde tres metros sobre el pasillo equivocado.

En Gazebo deben aparecer tres modelos: `ground_plane`, `mundo_definitivo_piso1` o
`mundo_definitivo_piso2` según el robot, y el vehículo.

### RViz de cada uno

Cada robot tiene su propia configuración, con todos los tópicos prefijados con su namespace.
La de robot2 **hay que abrirla con `ROS_DOMAIN_ID=2`**: sin eso RViz se conecta al dominio 0,
no encuentra nada y se queda con los displays en gris, sin decir por qué.

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && rviz2 -d $(ros2 pkg prefix deepracer_description)/share/deepracer_description/rviz/robot1_completo.rviz --ros-args -r __ns:=/robot1 -p use_sim_time:=true
```

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && export ROS_DOMAIN_ID=2 && rviz2 -d $(ros2 pkg prefix deepracer_description)/share/deepracer_description/rviz/robot2_completo.rviz --ros-args -r __ns:=/robot2 -p use_sim_time:=true
```

### Teleop de cada uno

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && export ROS_DOMAIN_ID=2 && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot2/cmd_vel
```

### Demostrar que están aislados

Mover **solo** robot1 y leer la odometría del otro:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ROS_DOMAIN_ID=2 ros2 topic echo /robot2/odom --once
```

Lo medido en S17: el robot comandado avanzó 3,34 m y el testigo se movió 6 mm, que es deriva
numérica del solver. **Si el testigo se desplaza más que unos milímetros, el aislamiento es
falso** y el resultado de H1 estaría equivocado.

La columna a vigilar en robot2 es la **z**. Si cae de 2,99 a ~0 se pasó al nivel 1, y el
LiDAR no lo delataría: las dos plantas son idénticas, así que un robot caído produciría
exactamente el mismo `/scan`. Solo la altura discrimina el nivel.

### Coste de tener dos ventanas abiertas

| Escenario | RTF | RAM añadida | GPU | VRAM |
|---|---|---|---|---|
| 2 simulaciones + 2 ventanas | 0,998 / 0,998 | 955 MB | 67 % | 1168 / 2048 MB |
| 2 simulaciones sin ventanas | — | 640 MB | 22 % | 821 MB |

El cuello de botella no es la CPU sino la **VRAM de la GPU integrada**: con las dos ventanas
abiertas se consume más de la mitad, y **añadir dos RViz agota el margen**. Para medir, la
operación por defecto debe ser sin ventanas.

---

## 7. Diagnóstico rápido

| Síntoma | Causa comprobada | Qué hacer |
|---|---|---|
| RViz vacío con los tópicos publicando | RViz sin `use_sim_time` | Relanzarlo con `--ros-args -p use_sim_time:=true` |
| El mapa no aparece en RViz | QoS `Volatile`; el mapa se publica `Transient Local` | Poner *Durability Policy* = `Transient Local` en el display |
| `!rclpy.ok()` al cargar controladores | Daemon corrupto tras matar Gazebo | `ros2 daemon stop && ros2 daemon start` |
| El vehículo se mueve solo | Objetivo de Nav2 activo peleando con el teleop | Cancelar el objetivo o no teleoperar durante la navegación |
| Gazebo abre un mundo vacío sin error | Ruta de `.world` inexistente | Comprobar la ruta; el defecto ya sale del clon en ejecución |
| Nodos fantasma en `ros2 node list` | Caché del daemon | Añadir `--no-daemon` |
| `Invalid frame ID "map"` en bucle | Frames sin prefijar bajo namespace | Comprobar que el launch recibió `namespace:=` |
| **`Fixed Frame: Frame [map] does not exist`** | AMCL caído o RViz abierto antes de que publicara | Comprobar con `tf2_echo map robot1/base_link`. Si no resuelve, revisar el log por `SERVER amcl IS DOWN` y relanzar desde §0 |
| RViz abre pero sin displays útiles | Se usó `nav2_robot1_view.rviz`, que no trae LaserScan ni costmaps | Usar `robot1_completo.rviz` |
| **RViz abre solo con `Grid` y el título lleva `*`** | La ruta del `-d` no existe. RViz **no avisa**: cae a la configuración vacía y conserva el nombre en el título | Comprobar que el archivo está en el árbol instalado: `ls ~/deepracer_sim_ws/install/deepracer_description/share/deepracer_description/rviz/`. Si falta, `colcon build --symlink-install --packages-select deepracer_description` |
| Un `.rviz`, `.yaml` o malla nueva no aparece pese a estar en el repo | `--symlink-install` enlaza archivo por archivo **en tiempo de compilación**; un archivo nuevo no existe en `install/` hasta recompilar su paquete | Recompilar el paquete que lo instala, no solo el que se editó |
| El mapa de SLAM no se ve pero `/map` sí publica | `slam_toolbox` publica en `/map` absoluto; RViz escucha `/robot1/map` | Comprobar que el launch aplicó el remap: `ros2 topic list \| grep map` |
| La pose salta entre dos estimaciones | AMCL y `slam_toolbox` corriendo a la vez, los dos publican `map → odom` | Bajar uno de los dos; ver §5 |
| `navigate_to_pose action server is not available` | RViz lanzado fuera del namespace | Añadir `-r __ns:=/robot1` |
| `GLSL link result: active samplers...` | Aviso del driver Mesa al pintar el mapa | Cosmético, el mapa se dibuja igual |
| El vehículo no se dibuja, solo los ejes | Las mallas `package://` no resuelven | `bash herramientas/verificar_instalacion.sh`, esperado 31/31 |
| `robot_description` parece no publicarse | Se publica `Transient Local` | Añadir `--qos-durability transient_local` al `echo` |
| Los STL parecen de 90 bytes | `stat` mide el enlace, no el archivo | Usar `stat -Lc%s` |
| El robot maniobra en el sitio y aborta | Verificador de meta `stateful: True` contra la restricción Ackermann | **Defecto abierto**, ver §4 |

---

## 8. Apagado

Es el mismo procedimiento del §0 y por el mismo motivo, así que se usan los mismos dos
comandos. Por robot:

```bash
cd "$TESIS" && herramientas/robot.sh robot1 parar && herramientas/robot.sh robot2 parar
```

O a mano, matando los dos dominios de golpe:

```bash
pkill -f "ros2 launch deepracer_bringup" ; pkill -x gzserver ; pkill -x gzclient ; pkill -x rviz2 ; sleep 4 ; ros2 daemon stop ; ros2 daemon start
```

Dejar el daemon reiniciado evita heredar el problema en la siguiente sesión. `robot.sh parar`
además **comprueba el puerto**, que es la señal fiable: un proceso muerto queda como zombi y
sigue saliendo en `pgrep` aunque ya no estorbe.

---

## 9. El mundo definitivo, su mapa y sus destinos

Desde el 2026-08-23 hay **un mundo por piso**: `mundo_definitivo_piso1.world` es el vigente y el
valor por defecto de los launch, junto con `mundo_definitivo_piso1.yaml`, y
`mundo_definitivo_piso2.world` va con `mundo_definitivo_piso2.yaml`. Ya no hay que pasar
`world:=` ni `map:=` a mano: `herramientas/robot.sh` toma los dos de la fila del robot.

Cuidado al leer los escenarios A a F de más arriba: sus **medidas** se tomaron sobre
`primer_piso_v2.world` y `primer_piso_dos_niveles.world`, que eran los mundos de entonces, y
las cifras concretas que citan hay que volver a tomarlas. Los procedimientos siguen valiendo;
los números, no.

### `herramientas/robot.sh`

Un solo punto de entrada. Existe porque cada escenario de arriba obliga a teclear el dominio
ROS, el puerto de Gazebo, la pose de spawn, la ruta absoluta del mundo y el
`GAZEBO_MODEL_PATH`, y **olvidar el último no da error**: `gzserver` se pasa 77 s consultando
`models.gazebosim.org`, no resuelve el `model://` y el fallo aparece mucho después como
`Service /spawn_entity unavailable`, que apunta al sitio equivocado.

```bash
cd "$TESIS" && herramientas/robot.sh robot1 sim
```

Las acciones son `sim`, `rviz`, `slam`, `nav2`, `teleop`, `lidar`, `estado` y `parar`. Todo
argumento con `:=` se reenvía tal cual a `ros2 launch` y **sobreescribe** lo que traiga el
script, así que `cd "$TESIS" && herramientas/robot.sh robot1 sim gui:=false` funciona.

El `cd` de delante hace falta: la ruta es relativa al repositorio y sin él sale
`No such file or directory`, que no dice cuál era el problema.

No reemplaza a `lanzar_sim.sh`: aquel mata **todo** lo que huela a ROS o Gazebo antes de
arrancar, lo que con dos robots simultáneos tumba al compañero. Éste limita la limpieza a los
procesos cuyo `ROS_DOMAIN_ID` coincide con el del robot pedido.

**De dónde saca la pose.** No la lleva escrita: la lee de `POSE_INICIAL`, en
[`deepracer_raiz_repo.py`](../Robot/aws-deepracer/deepracer_bringup/launch/deepracer_raiz_repo.py),
que es la única tabla de poses del proyecto y la misma que usan los launch. Antes del
2026-08-22 había tres copias y una se quedó vieja al cambiar de mundo. Lo único que el script
sigue guardando por su cuenta son el `ROS_DOMAIN_ID` y el puerto de Gazebo, que son transporte
y no los comparte con nadie.

Para añadir un `robot3` se toca `POSE_INICIAL` —pose, nivel y mapa— y la tabla de dominios de
`robot.sh`. En ningún launch.

### Los mundos y los mapas

Cada planta lleva **su propio mundo y su propio mapa**, y eso es deliberado por dos motivos
distintos. El mapa propio, porque un mapa único dejaría a Nav2 planificar una ruta de un nivel al
otro por el vacío que los separa, que es justo lo que RNF-01 prohíbe. El mundo propio, porque
mientras las dos plantas compartieron escena el LiDAR de una alcanzaba las paredes de la otra.

Están los dos:
[`maps/mundo_definitivo_piso1.yaml`](../Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso1.yaml)
y [`maps/mundo_definitivo_piso2.yaml`](../Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso2.yaml).
No se levantaron con SLAM: se dibujaron leyendo la geometría declarada del `.world` con
`herramientas/generar_mapa_desde_mundo.py`. El `.yaml` lleva escrita en un comentario la orden
completa que lo generó, y esa orden basta para rehacerlo:

```bash
python3 herramientas/generar_mapa_desde_mundo.py mundo_definitivo_piso1.world Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso1 --semilla -19.165 7.292
python3 herramientas/generar_mapa_desde_mundo.py mundo_definitivo_piso2.world Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso2 --semilla -21.889 -8.379
```

**No llevan `--region`, y que no lo lleven es el punto.** Hasta el 24-ago sí lo llevaban —dos
rectángulos el piso 1, cinco el piso 2—, porque las puertas del edificio no tienen hoja en el
`.world` y el relleno de espacio libre se escapaba por cada una hasta inundar el exterior. Pero
`--region` **recorta el resultado sin arreglar la fuga**: el mapa salía bien y el mundo seguía
abierto, así que todo lo que no fuera ese recorte —Gazebo, el LiDAR, un relleno desde otra
semilla— seguía viendo los agujeros. Ahora los vanos están tapados en los propios `.world` con
paneles sintéticos `Limite_*`, y el relleno se contiene solo.

Los paneles no se pusieron a ojo. Los elige `herramientas/buscar_vanos.py`, que empareja cada
punta suelta de pared con la que tiene enfrente y se queda solo con los huecos **colineales**
—los que prolongan el eje de la pared que los abre, frente a las secciones transversales de
pasillo, que son perpendiculares— y con línea de visión libre. Cuál dejar abierto lo deciden
los antiguos `--region`, que ya declaraban la red navegable: si los dos lados del hueco caen
dentro de la red, es paso y no se toca. Ése es el único uso que les queda:

```bash
python3 herramientas/buscar_vanos.py mundo_definitivo_piso2.world \
    --region -23.39 -11.30 -17.37 -6.76 --region -17.52 -11.30 -14.03 -0.83 \
    --region -14.20 -5.85 8.50 -3.12  --region 8.50 -5.85 23.39 -3.68 \
    --region 18.48 -9.56 21.71 -5.67  --xml Limite_p2_
```

Van en `Gazebo/Orange`, la misma convención que `Barrera_Escalera`: naranja significa «esto no
es geometría real del edificio». El generador los pinta con el valor **50**, que Nav2 lee como
ocupado igual que el 0 pero un humano distingue de una pared de verdad.

### El verificador los acepta, y ésa es la prueba

```bash
python3 herramientas/verificar_mapa.py Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso1.yaml mundo_definitivo_piso1.world
python3 herramientas/verificar_mapa.py Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso2.yaml mundo_definitivo_piso2.world
```

Los dos salen `ACEPTADO`. **Hay que pasarle a cada mapa su propio mundo:** contra el
`mundo_definitivo.world` combinado la cobertura en Y se hunde al 30 % porque compara una planta
contra las dos, y eso es un artefacto de la pregunta, no un defecto del mapa.

Tres cifras, y las tres miden cosas distintas:

| | piso 1 | piso 2 | qué detecta |
|---|---|---|---|
| Obstáculos sin pared real | 0 de 6044 | 0 de 7977 | paredes que el mapa se inventa |
| Frontera libre↔desconocido | 0 de 25 946 | 0 de 40 573 | **fugas del relleno** |
| Umbrales `.yaml` frente a `.pgm` | coherentes | coherentes | el defecto del 205 |

La segunda es la que certifica el sellado, y es la que antes fallaba: el 24-ago el piso 2 daba
270 celdas de frontera en 210 sitios. Cero frontera significa que no queda ni una celda libre
tocando una desconocida, es decir, que el espacio libre está enteramente rodeado de pared.

La tercera existe por un defecto que estuvo activo hasta el 24-ago: con `free_thresh: 0.25` el
valor 205 —el que la convención de ROS reserva para *desconocido*— salía **libre**, porque
`(255−205)/255 = 0,196 < 0,25`. El `map_server` leía «aquí se puede pasar» donde el generador
había escrito «aquí no sé». Está en `0.1`, que deja el 205 del lado correcto sin mover el 254.
Los mapas antiguos que sigan en `0.25` tienen ese defecto aunque el dibujo parezca bien.

### Los destinos

[`config/puntos_interes.yaml`](../Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml)
tiene los **15 destinos del piso 1**, y sólo ésos. El piso 2 tiene mapa y vanos detectados pero
todavía no tiene nombres, y un destino sin nombre real es una coordenada, no un destino.

Los quince se detectaron sobre el mapa como los huecos por donde el espacio libre toca lo
desconocido, se dibujaron en [`mapa_destinos.txt`](mapa_destinos.txt) y se bautizaron a mano.
De los dieciséis vanos encontrados, uno se descartó por no corresponder a ninguna dependencia.

El robot **no atraviesa las puertas**: se detiene al lado y la HRI dice de qué lado queda el
destino. De ahí que el `yaw` vaya alineado con el pasillo y nunca apuntando a la puerta —el
vehículo no puede girar sobre su eje, por eso se quitó `<Spin>` del árbol de comportamiento— y
que exista el campo `lado_pared`.

Todo el razonamiento de por qué cada parada está donde está —incluida la razón por la que hubo
que apartarlas hacia su propia pared— está en la cabecera del propio `puntos_interes.yaml`.

### Lo que falta antes de que esto sea el mundo vigente

1. Los nombres del piso 2, y con ellos su mapa y sus destinos en el repositorio.
2. Cambiar los valores por defecto de los launch y del mapa de Nav2, y con ellos el `README.md`
   y `ESTADO.md`. Mientras eso no pase, `robot.sh nav2` avisa por `stderr` de que sin `map:=`
   carga el mapa de `primer_piso`, que no es el de este mundo.
3. Probar la llegada a **ETM10**, la más apretada del archivo: es el único destino al que se
   llega de frente, porque su vano está en el muro del fondo del pasillo.

---

## 10. El vehículo físico: arrancar el LiDAR sin tumbar el control

**El problema.** Con el LiDAR de fábrica conectado, `deepracer-core` se queda en `failed` y el
vehículo se queda **sin ningún nodo de control**. La causa está medida el 2026-08-21
([`S19_lidar_original_evo.md`](Evidencia/S19_lidar_original_evo.md)): el lanzador de AWS invoca el
ejecutable `rplidar_node`, y en `/opt/ros/jazzy/lib/rplidar_ros/` lo único que existe es
`rplidar_composition`. El binario está instalado y funciona; **lo que no existe es el nombre que el
launch llama**.

**La salida que se adopta: no tocar el sistema.** En vez de enlazar o editar ficheros bajo
`/opt/`, se deja que `deepracer-core` arranque **sin** el LiDAR y se arranca el sensor aparte:

```bash
ros2 launch deepracer_bringup lidar_vehiculo.launch.py
```

Tres razones, y la primera es la que importa:

1. **`deepracer-core` queda sano**, y es de donde sale el mando de los servos. Con el arreglo por
   enlace, si el nodo del LiDAR falla se lleva por delante el control del vehículo; así no.
2. No se modifican ficheros del sistema en **hardware compartido**, ni hay nada que revertir.
3. El sensor publica **directamente en `/scan`**, que es donde miran Nav2 y `slam_toolbox`. Bajo el
   espacio de nombres de AWS publicaría en `/rplidar_ros/scan` y haría falta además un remapeo.

**Comprobar que publica de verdad**, y no solo que el tópico aparece:

```bash
ros2 topic info /scan --verbose
```

> `/scan` **aparece en `ros2 topic list` con el sensor desenchufado**, así que verlo listado no
> significa nada. Lo que no miente es el número de publicadores y la frecuencia. Esperado sobre el
> A1M8-R5 de fábrica: **360 muestras sobre 360°, a 6,80 Hz**, alcance 12,0 m.

### Las direcciones IP no se escriben en ningún sitio

En el repositorio **no hay ni una IP**: ni en código ni en configuración, solo en los informes de
evidencia, que son registros fechados. Y no hace falta que las haya — en la misma red local, el
descubrimiento de DDS es por multidifusión y **no necesita direcciones**. Solo hacen falta para
`ssh`, y ahí se escriben en el momento.

Aun así conviene una **reserva DHCP** para el vehículo y el portátil: el 19-ago el portátil era
`192.168.0.101` y el 21-ago ya era `.102`. No rompe ROS, pero sí rompe el `ssh` de la sesión y hace
perder tiempo de vehículo, que es el recurso caro.

Si algún día el multicast está bloqueado en la red —es lo normal en wifi con aislamiento de
clientes—, la salida **no** es escribir IP en los launch, sino levantar un servidor de
descubrimiento de Fast DDS y apuntar los dos equipos a él con `ROS_DISCOVERY_SERVER`.
