# Guia de Navegacion - Simulacion DeepRacer

## Requisitos previos

```bash
# Compilar (solo la primera vez o despues de cambios)
rsync -av --exclude='.git' \
  /home/santiago/Documents/Tesis/Robot/aws-deepracer/deepracer_bringup/ \
  /home/santiago/deepracer_sim_ws/src/aws-deepracer/deepracer_bringup/
cd /home/santiago/deepracer_sim_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select deepracer_bringup
```

---

## Paso 1: Lanzar la simulacion

Abrir **Terminal 1**:

```bash
source /opt/ros/humble/setup.bash
source /home/santiago/deepracer_sim_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py
```

### Que deberias ver:

**Segundo 0-5:** La terminal muestra los procesos arrancando:
```
[gzserver-1]: process started with pid [XXXXX]
[gzclient-2]: process started with pid [XXXXX]
[robot_state_publisher-3]: process started with pid [XXXXX]
[rp_lidar-5]: process started with pid [XXXXX]
```

**Segundo 5-10:** Se abre la ventana de **Gazebo**. Veras:
- Un piso gris con lineas que representan las paredes del primer piso USTA
- En el centro del piso, un robot azul oscuro (el DeepRacer)
- El robot esta parado, quieto

**Segundo 10-20:** AMCL y el mapa se cargan:
```
[amcl]: Subscribed to map topic.
[amcl]: Received a 384 X 262 map @ 0.060 m/pix
[lifecycle_manager_localization]: Activating amcl
[lifecycle_manager_localization]: Managed nodes are active    <-- LOCALIZACION LISTA
```

**Segundo 20-25:** AMCL auto-publica la pose inicial en (0,0):
```
[amcl]: initialPoseReceived
[amcl]: Setting pose (0.000000): 0.000 0.000 0.000
```
Esto significa que AMCL sabe donde esta el robot: en la posicion (0, 0) del mapa.

**Segundo 25-35:** Los servidores Nav2 arrancan uno por uno:
```
[lifecycle_manager_navigation]: Configuring controller_server
[lifecycle_manager_navigation]: Configuring planner_server
[lifecycle_manager_navigation]: Configuring behavior_server
[lifecycle_manager_navigation]: Configuring bt_navigator
[lifecycle_manager_navigation]: Configuring waypoint_follower
[lifecycle_manager_navigation]: Activating controller_server
[lifecycle_manager_navigation]: Activating planner_server
[lifecycle_manager_navigation]: Activating bt_navigator
[lifecycle_manager_navigation]: Managed nodes are active       <-- NAVEGACION LISTA
```

**Estado final:** La terminal queda quieta, solo mostrando warnings periodicos como:
```
[global_costmap.global_costmap]: Timed out waiting for transform from base_link to map
```
Estos warnings son normales, no son errores. Significa que el costmap esta verificando
la posicion del robot continuamente.

### Si ves error "Failed to bring up all requested nodes":
Significa que algun nodo no pudo activarse. Revisa la linea anterior al error para ver
cual fallo. La causa mas comun es que `bt_navigator` no pudo cargar el XML del Behavior Tree.

---

## Paso 2: Enviar un goal de navegacion

Abrir **Terminal 2** (dejar Terminal 1 corriendo):

```bash
source /opt/ros/humble/setup.bash
source /home/santiago/deepracer_sim_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
ros2 action send_goal -f /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 3.0, y: 0.0}, orientation: {w: 1.0}}}}"
```

### Que deberias ver:

**En Terminal 2** (instantaneamente):
```
Waiting for the action server to connect...
Goal accepted with ID: ...
```

**En Terminal 1** (la de Nav2), aparecen nuevos mensajes:
```
[bt_navigator]: Begin navigating from current location (0.00, 0.04) to (3.00, 0.00)
[controller_server]: Received a goal, begin computing control effort.
[controller_server]: Passing new path to controller.
```

**En Gazebo** (la ventana visual):
- El robot empieza a girar ligeramente para orientarse hacia el punto (3.0, 0.0)
- Luego avanza en linea recta hacia la derecha del mapa
- Se mueve despacio y con cuidado (velocidad ~0.5 m/s)
- Cada segundo mas o menos ajusta ligeramente su trayectoria

**En Terminal 1** (cada ~1 segundo, el robot replanifica):
```
[controller_server]: Passing new path to controller.
[controller_server]: Passing new path to controller.
```

**Cuando el robot llega al destino** (~5-10 segundos):
```
[controller_server]: Reached the goal!
[bt_navigator]: Goal succeeded
```

**En Gazebo:** El robot se detiene en la posicion (3.0, 0.0).

**En Terminal 2:**
```
...
Result:
  status: 4
```
El status 4 significa "SUCCEEDED".

---

## Paso 3: Enviar otro goal mas lejano

En **Terminal 2** (mismo comando, diferente destino):

```bash
ros2 action send_goal -f /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: -3.0, y: -2.0}, orientation: {w: 1.0}}}}"
```

### Que deberias ver:

**En Gazebo:** El robot gira y empieza a recorrer el mapa hacia la posicion (-3.0, -2.0),
que esta en la zona opuesta. Navega esquivando las paredes que encuentra en el camino.

**En Terminal 1:**
```
[bt_navigator]: Begin navigating from current location (2.98, 0.02) to (-3.00, -2.00)
```

Si el camino esta bloqueado por una pared, el planner calcula una ruta que la esquive.
El robot podria hacer giros amplios para rodear obstaculos.

---

## Paso 4: Verificar la localizacion

En **Terminal 3**:

```bash
source /opt/ros/humble/setup.bash
source /home/santiago/deepracer_sim_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
ros2 run tf2_ros tf2_echo map base_link
```

### Que deberias ver:

La posicion en tiempo real del robot en el mapa:
```
At time 612.345000000
- Translation: [-2.87, -1.95, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.707, 0.707]
```

Los valores de Translation van cambiando a medida que el robot se mueve.
El primer valor es X, el segundo es Y. Deberian ser cercanos al goal que enviaste.

Para detener esta visualizacion: `Ctrl+C`.

---

## Paso 5: Ver el arbol TF

```bash
ros2 run tf2_tools view_frames
```

### Que deberias ver:

```
[INFO] [view_frames]: Generating TF tree PDF...
```

Se genera un archivo PDF en `/tmp/frames.pdf`. Abrirlo con un visor de PDF.
Deberias ver un diagrama con estas conexiones:

```
map --> odom --> base_link --> chassis --> laser
                          |--> left_front_wheel
                          |--> right_front_wheel
                          |--> left_rear_wheel
                          |--> right_rear_wheel
                          |--> left_steering_hinge
                          |--> right_steering_hinge
                          |--> zed_camera_link
```

- **map → odom**: Lo publica AMCL (cambia cuando el robot se mueve)
- **odom → base_link**: Lo publica Gazebo (cambia cuando el robot se mueve)
- **base_link → chassis → laser**: Estaticos del URDF (no cambian nunca)

---

## Paso 6: Ver el mapa de AMCL

Abrir **Terminal 4**:

```bash
source /opt/ros/humble/setup.bash
source /home/santiago/deepracer_sim_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
ros2 topic echo /amcl_pose --once
```

### Que deberias ver:

```yaml
header:
  stamp:
    sec: 615
    nanosec: 123000000
  frame_id: map
pose:
  covariance: [0.25, ...]
  pose:
    position:
      x: -2.87      # Posicion X del robot en el mapa
      y: -1.95      # Posicion Y del robot en el mapa
    orientation:
      z: 0.707      # Orientacion del robot
      w: 0.707
```

Los valores de `x` e `y` deben ser parecidos a los que viste en el `tf2_echo`.

---

## Paso 7: Ver RViz (opcional pero util)

```bash
source /opt/ros/humble/setup.bash
source /home/santiago/deepracer_sim_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
rviz2
```

### Configuracion rapida:

1. En el panel izquierdo, cambiar **Fixed Frame** de `map` a `map` (deberia estar ya)
2. Click en **Add** → **By topic** → seleccionar:
   - `/map` → Veras el mapa gris del primer piso
   - `/scan` → Veras puntos naranjas que representan las lecturas del LIDAR
   - `/tf` → Veras flechas de colores representando las transformaciones
   - `/particlecloud` → Veras puntos azules que son las particulas de AMCL
   - `/global_costmap/costmap` → Veras una capa azul semitransparente sobre el mapa
3. En la barra superior, usar:
   - **"2D Pose Estimate"**: Clic en el mapa para decirle a AMCL donde esta el robot
   - **"2D Nav Goal"**: Clic en el mapa para enviar al robot a un punto

---

## Limites del mapa

El mapa del primer piso tiene estos limites. Los goals deben estar dentro:

```
X: de -12.20 a 10.84 metros
Y: de  -8.89 a  6.83 metros
```

**Goals validos:** `(0, 0)`, `(5, 0)`, `(-5, -3)`, `(8, 5)`, `(-10, 2)`
**Goals invalidos:** `(15, 0)` (fuera del mapa), `(0, 10)` (fuera del mapa)

---

## Compilar despues de cambios

Si modificas archivos en `Robot/aws-deepracer/deepracer_bringup/`, siempre:

```bash
# 1. Sincronizar al workspace
rsync -av --exclude='.git' \
  /home/santiago/Documents/Tesis/Robot/aws-deepracer/deepracer_bringup/ \
  /home/santiago/deepracer_sim_ws/src/aws-deepracer/deepracer_bringup/

# 2. Compilar
cd /home/santiago/deepracer_sim_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select deepracer_bringup
```

Despues de compilar, hay que relanzar la simulacion (matar la anterior primero).

---

## Matar la simulacion

Si necesitas parar todo:

```bash
killall -9 gzserver gzclient controller_server planner_server \
  behavior_server bt_navigator waypoint_follower lifecycle_manager \
  amcl map_server robot_state_publisher 2>/dev/null
```
