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

**Atajo:** [`herramientas/robot.sh`](../herramientas/robot.sh) hace todo eso —el `source`, el
dominio, el puerto de Gazebo, la pose de spawn y el `GAZEBO_MODEL_PATH`— desde una sola tabla.
Los comandos largos de esta guía siguen siendo la referencia de lo que ocurre por debajo; el
script es para no teclearlos. Está descrito en el §9, junto con el mundo que carga, que **no
es el de los escenarios A a F**.

---

## 0. Antes de empezar: dejar el equipo limpio

Un `gzserver` anterior ocupa el puerto 11345 y el siguiente lanzamiento falla de una forma
que no se parece a un conflicto de puertos. Comprobar y, si hay algo vivo, cerrarlo:

```bash
pgrep -af "gzserver|gzclient|rviz2"
```

```bash
pkill -f "ros2 launch deepracer_bringup" ; pkill -f gzserver ; pkill -f gzclient ; pkill -x rviz2 ; sleep 4 ; ros2 daemon stop ; ros2 daemon start
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

No hace falta pasar `world:=` ni `map:=`: los valores por defecto salen de **este mismo
clon** del repositorio (`mundo_definitivo.world` y `mundo_definitivo_piso1.yaml`). Mundo y
mapa van en pareja; cambiar uno solo hace que AMCL localice contra una geometría distinta
de la simulada, y el síntoma —deriva creciente— no se parece a un error de configuración.

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
cd ~/Tesis && bash herramientas/verificar_instalacion.sh
```

**Esperado: `32 comprobaciones pasan, 0 fallan`.**

Si salen 2 fallos de `GAZEBO_MODEL_PATH` y de `los model:// externos resuelven`, **no es un
problema del modelo**: es que esa terminal no cargó `~/.bashrc`, donde está la línea. Se
arregla con `exec bash` y se vuelve a ejecutar. Afecta a los mundos que usan `model://`
—**entre ellos `mundo_definitivo.world`, que es el que se carga por defecto**—, que abrirían
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

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 5.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

**`SUCCEEDED` no significa que el vehículo llegó**, solo que el árbol de comportamiento
terminó. La comprobación válida es medir `/robot1/odom` antes y después y comparar el
desplazamiento contra el objetivo. En las corridas de H1 y S18, sobre un objetivo de 5,0 m,
lo medido fue 4,79 – 4,96 m.

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

### Cómo lanzarla

Arranca el vehículo en el pasillo abierto mirando al este, con la meta **detrás**:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py x:=25.0 y:=1.45 yaw:=0.0
```

Grabar antes de mandar la meta, en otra terminal:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 bag record -o /tmp/v_p1 /plan /odom /cmd_vel /amcl_pose
```

Y la meta, en una tercera:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 10.60, y: 1.45}, orientation: {w: 1.0}}}}"
```

**Manda la meta dentro de los primeros 30 s tras el arranque.** Con el robot parado más
tiempo, la deriva en reposo introduce un desvío inicial que confunde el diagnóstico.

Medir después:

```bash
cd ~/Tesis && python3 herramientas/analizar_maniobra.py /tmp/v_p1 10.60 1.45
```

> Los comandos anteriores van **sin namespace**, que es como se grabaron las seis corridas de
> referencia. Con `namespace:=robot1` hay que prefijar la acción y los tópicos del bag.

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

Los dos publican el marco `map` sin prefijar, y no chocan porque viven en dominios ROS
distintos. Es el mismo criterio que en el launch de localización: los marcos del vehículo
se prefijan (`robot1/odom`, `robot1/base_link`) porque así los publica el URDF, pero `map`
es el ancla común.

**El tópico sí se prefija.** `slam_toolbox` crea el publicador del mapa con el nombre
absoluto `/map`, de modo que el namespace del nodo no lo alcanza. El launch añade un remap
a `/robot1/map` para que la misma configuración de RViz sirva para mapear y para navegar.
Sin ese remap el mapa aparece vacío en RViz y no hay ningún error que lo explique.

### Guardar el mapa

El procedimiento y la verificación de cobertura están en
[`guia_simulacion_slam.md`](guia_simulacion_slam.md). Bajo namespace hay que redirigir el
tópico, porque `map_saver_cli` escucha `/map`:

```bash
ros2 run nav2_map_server map_saver_cli -f /tmp/mapa_candidato --ros-args -p use_sim_time:=true -r map:=/robot1/map
```

---

## 6. Escenario F — dos robots, dos niveles

La topología adoptada es **un `gzserver` por robot**, porque `gazebo_ros` de Humble aplica a
todos los plugins el namespace del primer modelo cargado y dentro de un mismo simulador los
dos robots no se pueden aislar. Los dos procesos cargan el **mismo** mundo, cada uno con un
solo vehículo: así hay una sola geometría canónica.

No hace falta `world:=`: el mundo por defecto es `mundo_definitivo.world` y sale del mismo
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

> **Estas poses no se teclean a ojo.** Salen de la tabla de
> [`herramientas/robot.sh`](../herramientas/robot.sh), que es la única del proyecto: están
> medidas sobre el SDF de `mundo_Definitivo` y comprobadas con el LiDAR. Si se van a escribir
> a mano, copiarlas de ahí. Mejor todavía, no escribirlas: `robot.sh robot2 sim` hace lo mismo
> sin teclear ninguna.

> **Por qué `x:=`/`y:=` y ya no `z:=3.03`.** Hasta el 2026-08-20 el escenario corría sobre
> `primer_piso_dos_niveles.world`, donde el piso 2 era la misma planta elevada a z = 3,0 y el
> robot2 nacía en z = 3,03 para asentarse en 2,993. En `mundo_definitivo.world` los dos pisos
> son **pasillos distintos, uno al lado del otro en Y**. Pasar `z:=3.03` aquí haría caer al
> vehículo desde tres metros sobre el pasillo equivocado.

En Gazebo deben aparecer tres modelos: `ground_plane`, `mundo_definitivo` y el vehículo.

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

```bash
pkill -f "ros2 launch deepracer_bringup" ; pkill -x gzserver ; pkill -x gzclient ; pkill -x rviz2 ; sleep 4 ; ros2 daemon stop ; ros2 daemon start
```

Dejar el daemon reiniciado evita heredar el problema en la siguiente sesión.

---

## 9. El mundo definitivo, su mapa y sus destinos

Desde el 2026-08-20 `mundo_definitivo.world` **es** el mundo vigente y el valor por defecto de
los launch, junto con `mundo_definitivo_piso1.yaml`. Ya no hay que pasar `world:=` ni `map:=`
a mano.

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
herramientas/robot.sh robot1 sim
```

Las acciones son `sim`, `rviz`, `slam`, `nav2`, `teleop`, `lidar`, `estado` y `parar`. Todo
argumento con `:=` se reenvía tal cual a `ros2 launch`, así que
`herramientas/robot.sh robot1 sim gui:=false` funciona.

No reemplaza a `lanzar_sim.sh`: aquel mata **todo** lo que huela a ROS o Gazebo antes de
arrancar, lo que con dos robots simultáneos tumba al compañero. Éste limita la limpieza a los
procesos cuyo `ROS_DOMAIN_ID` coincide con el del robot pedido.

### El mundo y el mapa del piso 1

`mundo_definitivo.world` tiene las dos plantas en el mismo mundo, separadas en Y: el piso 1
al norte y el piso 2 al sur. Cada planta lleva **su propio mapa**, y eso es deliberado: un
mapa único dejaría a Nav2 planificar una ruta de un nivel al otro por el vacío que los separa,
que es justo lo que RNF-01 prohíbe.

Hasta ahora sólo está el del piso 1, en
[`maps/mundo_definitivo_piso1.yaml`](../Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso1.yaml).
No se levantó con SLAM: se dibujó leyendo la geometría declarada del `.world` con
`herramientas/generar_mapa_desde_mundo.py`. El `.yaml` lleva escrita en un comentario la orden
completa que lo generó, con sus dos `--region`, porque esos rectángulos son una decisión y no
algo que se deduzca del mundo: sin ellos el mapa no se puede rehacer.

**Los `--region` no son un adorno.** El pasillo tiene una quincena de puertas a habitaciones
que nadie modeló, y por cada una el relleno de espacio libre se escapa a un vacío donde no hay
nada que lo detenga. Sin ese límite el mapa salía 94 % libre y Nav2 atajaba en línea recta por
fuera del pasillo.

### El verificador lo rechaza, y está bien

```bash
python3 herramientas/verificar_mapa.py Robot/aws-deepracer/deepracer_bringup/maps/mundo_definitivo_piso1.yaml mundo_definitivo.world
```

Sale `RECHAZADO` por dos motivos, y los dos son artefactos de la pregunta, no defectos del
mapa:

- **Cobertura en Y del 29,7 %.** Compara los 6,7 m del piso 1 contra los 22,6 m que ocupan las
  dos plantas juntas. Un mapa de una sola planta no puede pasar esa prueba por definición.
- **58,5 % de celdas desconocidas.** El verificador da por hecho que un mapa llena su caja
  envolvente. Una planta en L no la llena.

Lo que sí mide de verdad es la fidelidad, y ahí sale perfecto: **0 de 4725 celdas ocupadas
carecen de pared real detrás**. Ése es el caso peligroso —paredes que el mapa se inventa—
porque no se ve mirando el mapa, sino mucho después, cuando el planificador aborta rutas por
zonas que en realidad están libres.

**Advertencia que no cubre esa cifra:** «0 obstáculos falsos» certifica las **paredes**, no el
espacio libre. El espacio libre declarado son sólo los pasillos, y es a propósito más
restrictivo que el mundo de Gazebo, donde el vehículo sí puede cruzar una puerta y salir al
vacío. Si en simulación el robot atraviesa un vano y desaparece del mapa, eso es lo que está
pasando.

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
