# Desarrollo Nav2 + AMCL — Registro de Sesiones

> ## ⛔ Documento cerrado — registro histórico
>
> **Cubre del inicio de Nav2 al 17 de julio de 2026** (sesiones 1 y 3; no hubo sesión 2
> registrada). **No se actualiza más.** El estado vigente del proyecto está en
> [`ESTADO.md`](../ESTADO.md), que es la fuente única de verdad, y la bitácora de
> decisiones vive ahí.
>
> Se conserva porque documenta cómo se levantó el stack Nav2 + AMCL y por qué cada
> parámetro quedó como quedó: eso no está registrado en ningún otro sitio. Pero **parte de
> lo que afirma se refutó después**, así que no sirve como referencia de configuración.
> Antes de copiar nada de aquí:
>
> | Dice este documento | Estado real | Dónde está la corrección |
> |---|---|---|
> | §1.3: mundo por defecto `primer_piso.world` | El vigente es `primer_piso_v2.world` desde el 2026-08-11, y el entorno de evaluación de OE4 es `primer_piso_dos_niveles.world` desde el 14-ago | `README.md`, y la constante `MUNDO_VIGENTE` de `deepracer_raiz_repo.py` |
> | §3.2: *«AMCL soporta `set_initial_pose` + `initial_pose` (x, y, yaw)»*, con `initial_pose: [0.0, 0.0, 0.0]` | **Falso.** Es una línea muerta: AMCL declara `initial_pose.x/.y/.z/.yaw` por separado y ROS descarta la lista en silencio. Un robot lanzado con `y:=2.0` arrancaba con 2 m de error | `ESTADO.md`, bitácora del 2026-08-12 |
> | §1 y §3, *«navegación autónoma verificada: alcanza el goal (3,0)»* | Un `SUCCEEDED` de Nav2 **no** se acepta como evidencia desde el 2026-08-12: lo emite el controlador contra la pose que le da AMCL, no contra la real. Toda medida se contrasta con `/odom` | `ESTADO.md`, bitácora del 2026-08-12 |
> | La fórmula del final publica en `/initialpose` | Correcto para un solo robot; bajo espacio de nombres hay que usar `/<ns>/initialpose` o no lo escucha nadie | [`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md) |
>
> Las «Notas para próxima sesión» de la sesión 1 quedaron sin cerrar aquí; si alguna sigue
> viva, su sitio es el tablero de riesgos de `ESTADO.md`, no este archivo.

---

## Contexto del Proyecto

- **Título:** Sistema Robótico Colaborativo para Asistencia en Navegación en Interiores Multinivel
- **Autores:** Santiago Hernández Ávila, Jonny Alejandro Mejía León
- **Stack:** Ubuntu 22.04, ROS 2 Humble, Gazebo, AWS DeepRacer (1:18)
- **Entorno principal:** Primer piso del edificio USTA
- **Robot real:** DeepRacer operativo con LIDAR (RPLiDAR) y cámara

## Arquitectura del Sistema

```
Simulación:
  Gazebo (gzserver + gzclient)
    → deepracer_spawn (robot_state_publisher + ros2_control)
      → gazebo_ros_deepracer_drive plugin (/cmd_vel → /odom + TF)
        → Nav2 (controller_server, planner_server, recoveries_server, bt_navigator, waypoint_follower)
          → Localización: AMCL (con mapa) o SLAM Toolbox (mapeando)

Robot Real:
  Hardware (LIDAR + cámara + servos)
    → rplidar_ros2 (/scan)
    → rf2o_laser_odometry (/odom)
    → cmdvel_to_servo (/cmd_vel → ServoCtrlMsg)
      → Nav2 (mismos componentes)
```

## Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `launch/deepracer_sim.launch.py` | Gazebo + spawn del robot |
| `launch/deepracer_spawn.launch.py` | Robot State Publisher + controladores + TFs |
| `launch/deepracer.launch.py` | Robot real (sensores + odometría) |
| `launch/deepracer_navigation_sim.launch.py` | Nav2 stack para simulación |
| `launch/deepracer_navigation_dr.launch.py` | Nav2 stack para robot real |
| `launch/nav_amcl_demo_sim.launch.py` | Demo completa AMCL en simulación |
| `launch/slam_toolbox.launch.py` | SLAM Toolbox |
| `config/nav2_params_nav_amcl_sim_demo.yaml` | Params Nav2 + AMCL para sim |
| `config/nav2_params_nav_amcl_dr_demo.yaml` | Params Nav2 + AMCL para robot real |
| `config/nav2_slam_params.yaml` | Params Nav2 para SLAM (sin AMCL) |
| `config/slam_toolbox.yaml` | Params SLAM Toolbox |
| `maps/primer_piso.yaml` + `.pgm` | Mapa del primer piso (resolución 0.06m) |

## TF Tree

```
URDF (fuente de verdad):
  base_link → chassis (z=0.023249) → laser (z=0.16145, yaw=π)
  base_link → chassis → zed_camera_link → camera_link

Robot real (static TF):
  base_link → laser: x=0.02913, z=0.184699, yaw=π
  base_link → camera_link: x=0.137, z=0.143, pitch=0.262

Frames:
  map → odom → base_link → laser (LIDAR)
                                → camera_link (cámara)
```

---

## Sesión 1 — Fase 1: Corrección de Bugs Críticos
**Fecha:** 2026-07-17
**Objetivo:** Que el stack Nav2 funcione sin errores en simulación.

### Problemas Identificados

1. **TF redundante del láser en sim:** `deepracer_spawn.launch.py` publica una TF estática base_link→laser que duplica lo que el URDF ya define vía `hokuyo_joint`. Además, z=0.885m es incorrecto (URDF dice z=0.185m).

2. **Frame del láser inconsistente:** Robot real usa `laser_frame`, URDF define `laser`, AMCL/Nav2 esperan `laser`.

3. **Launch AMCL apunta a bookstore:** `nav_amcl_demo_sim.launch.py` usa el mundo bookstore de AWS como default en vez de primer_piso.

4. **nav2_params.yaml no existe:** `deepracer_navigation_sim.launch.py` busca este archivo como default pero no existe.

5. **recoveries_server sin params:** Los launches pasan solo `use_sim_time` al recoveries_server en vez de `configured_params`.

6. **world argument no se reenvía:** `deepracer_sim.launch.py` declara `world` pero no lo pasa a gzserver.

7. **maps/ no se instala:** CMakeLists.txt no instala el directorio maps/.

8. **package.xml incompleto:** Faltan dependencias de Nav2, SLAM Toolbox, etc.

### Cambios Realizados

#### 1.1 — Eliminar TF redundante del láser en sim
- **Archivo:** `launch/deepracer_spawn.launch.py`
- **Cambio:** Eliminado el segundo `static_transform_publisher` (base_link→laser, líneas 109-117)
- **Razón:** El URDF ya define `hokuyo_joint` (chassis→laser). `robot_state_publisher` publica esta TF. La estática era redundante y creaba conflicto.

#### 1.2 — Unificar frame del láser en robot real
- **Archivo:** `launch/deepracer.launch.py`
- **Cambios:**
  - Línea 39: `laser_frame` → `laser` (static_transform_publisher)
  - Línea 62: `frame_id: 'laser_frame'` → `frame_id: 'laser'` (rplidar_scan_publisher)
- **Razón:** El URDF define el link como `laser`. AMCL/Nav2 esperan `/scan` en frame `laser`.

#### 1.3 — Corregir defaults de nav_amcl_demo_sim.launch.py
- **Archivo:** `launch/nav_amcl_demo_sim.launch.py`
- **Cambios:**
  - Eliminada dependencia de `aws_robomaker_bookstore_world`
  - Default world → `primer_piso.world` en la raiz del repositorio
    (en su momento se escribio una ruta absoluta; **superado en S17**: ahora la
    raiz se deduce de la ubicacion real del propio launch, ver la cabecera de
    `nav_amcl_demo_sim.launch.py`)
  - Default map → ruta absoluta a `maps/primer_piso.yaml`
- **Razón:** El launch apuntaba al mundo bookstore de AWS, no al primer piso del USTA.

#### 1.4 — Crear nav2_params.yaml
- **Archivo:** `config/nav2_params.yaml` (nuevo)
- **Cambio:** Copia de `nav2_params_nav_amcl_sim_demo.yaml` con `yaml_filename` corregido a ruta absoluta del mapa
- **Razón:** `deepracer_navigation_sim.launch.py` busca este archivo como default.

#### 1.5 — Corregir recoveries_server params
- **Archivos:** `launch/deepracer_navigation_sim.launch.py`, `launch/deepracer_navigation_dr.launch.py`
- **Cambio:** Línea 102: `[{'use_sim_time': use_sim_time}]` → `[configured_params]`
- **Razón:** El recoveries_server ignoraba todos los params del YAML (spin, backup, wait).

#### 1.6 — Corregir forward del argumento world
- **Archivo:** `launch/deepracer_sim.launch.py`
- **Cambio:** Agregado `'world': world_cfg` al `launch_arguments` del gzserver
- **Razón:** El argumento se declaraba pero nunca se reenviaba a Gazebo.

#### 1.7 — Instalar maps/ en CMakeLists.txt
- **Archivo:** `CMakeLists.txt`
- **Cambio:** `install(DIRECTORY launch config` → `install(DIRECTORY launch config maps`
- **Razón:** El mapa no se instalaba, causando errores al usar `get_package_share_directory`.

#### 1.8 — Actualizar package.xml
- **Archivo:** `package.xml`
- **Cambio:** Agregadas dependencias: nav2_bringup, nav2_controller, nav2_planner, nav2_bt_navigator, nav2_recoveries, nav2_waypoint_follower, nav2_lifecycle_manager, slam_toolbox, robot_state_publisher, tf2_ros, gazebo_ros
- **Razón:** Dependencias faltantes para build limpio.

### Verificación Post-Cambios

- [x] Compilar workspace: `cd ~/deepracer_sim_ws && colcon build --packages-select deepracer_bringup`
- [x] AMCL+Nav2 stack completo funciona en simulación
- [x] Navegación autónoma verificada: goal (3,0) alcanzado desde (0,0)

### Notas para Próxima Sesión

- La resolución del mapa (0.06m) no coincide con las costmaps Nav2 (0.05m) — resolver en Fase 2
- Falta crear launches compuestos para SLAM+Nav y AMCL+Nav en robot real — Fase 3
- El parámetro `scan_buffer_maximum_scan_distance: 0.5` en slam_toolbox.yaml parece bajo para un LIDAR de 10m de alcance — ajustar en Fase 4

---

## Sesión 3 — 17 julio 2026

### Problemas Resueltos

#### 3.1 — bt_navigator fallaba: "Node not recognized: RemovePassedGoals"
- **Archivo:** `config/nav2_params.yaml`, `config/nav2_params_nav_amcl_sim_demo.yaml`
- **Problema:** El bt_navigator carga DOS XMLs: `navigate_to_pose_w_replanning_and_recovery.xml` y `navigate_through_poses_w_replanning_and_recovery.xml`. Este último usa `RemovePassedGoals` y `ComputePathThroughPoses`.
- **Cambios:**
  - `default_bt_xml_filename: "default_bt_xml_filename"` → `"navigate_w_replanning_and_recovery.xml"`
  - Agregados a `plugin_lib_names`:
    - `nav2_remove_passed_goals_action_bt_node`
    - `nav2_compute_path_through_poses_action_bt_node`
    - `nav2_navigate_through_poses_action_bt_node`
- **Razón:** bt_navigator siempre carga el BT de NavigateThroughPoses además del NavigateToPose.

#### 3.2 — Planner server no activaba: falta frame `map`
- **Archivo:** `config/nav2_params_nav_amcl_sim_demo.yaml`, `config/nav2_params.yaml`
- **Problema:** El `global_costmap` necesita el TF `map → base_link` para activarse, pero AMCL no publica `map` hasta recibir un initial pose.
- **Cambios:** Agregados parámetros AMCL:
  ```yaml
  set_initial_pose: true
  initial_pose: [0.0, 0.0, 0.0]
  ```
- **Razón:** AMCL soporta `set_initial_pose` + `initial_pose` (x, y, yaw) para publicar el TF `map → odom` inmediatamente al activarse.

#### 3.3 — AMCL no recibía `/initialpose`: QoS incompatible
- **Problema:** AMCL se suscribe a `/initialpose` con `BEST_EFFORT + VOLATILE` QoS. Los scripts Python anteriores publicaban con `RELIABLE + TRANSIENT_LOCAL`.
- **Solución:** Usar la misma QoS que AMCL:
  ```python
  QoSProfile(depth=10, durability=DurabilityPolicy.VOLATILE, reliability=ReliabilityPolicy.BEST_EFFORT)
  ```
- **Razón:** FastDDS no acepta publishers RELIABLE para suscriptores BEST_EFFORT.

#### 3.4 — AMCL rechazaba initial pose: error de timestamp (wall clock vs sim time)
- **Problema:** `get_clock().now()` retorna tiempo de pared cuando `use_sim_time=False` en el nodo publicador. AMCL requiere tiempo de simulación.
- **Solución:** Obtener sim time del topic `/clock` (con QoS BEST_EFFORT) y usarlo como `stamp`:
  ```python
  msg.header.stamp = sim_time[0]  # sim_time del /clock
  ```
- **Razón:** AMCL intenta hacer lookup de TF al tiempo del mensaje; si es futuro vs datos disponibles, falla.

#### 3.5 — Gazebo /clock requiere BEST_EFFORT QoS
- **Problema:** El plugin `gazebo_ros_init` publica `/clock` con `BEST_EFFORT`. Nodos con `use_sim_time=True` intentan suscribirse con `RELIABLE` y reciben "incompatible QoS" warning.
- **Solución:** Para scripts Python, usar QoS `BEST_EFFORT` al suscribirse a `/clock`.

#### 3.6 — use_sim_time no se propagaba a localization_launch
- **Archivo:** `launch/nav_amcl_demo_sim.launch.py`
- **Problema:** `localization_launch.py` declara `use_sim_time` con default `'false'`. Nuestro launch no lo pasaba.
- **Cambios:** Agregado `'use_sim_time': 'true'` a los `launch_arguments` del `localization_launch.py` y del `deepracer_navigation_sim.launch.py`.

### Estado Final Sesión 3

- [x] Nav2 stack completo funciona en simulación (AMCL + Nav2)
- [x] Navegación autónoma verificada: robot navega de (0,0) a (3,0) y alcanza el goal
- [x] TF tree completa: `map → odom → base_link → chassis → laser`
- [x] AMCL localiza correctamente con `set_initial_pose`

### Fórmula para publicar initial pose (scripts Python)
```python
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rosgraph_msgs.msg import Clock
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

rclpy.init()
node = Node('init_pose_pub')
qos_be = QoSProfile(depth=10, durability=DurabilityPolicy.VOLATILE, reliability=ReliabilityPolicy.BEST_EFFORT)

# Obtener sim time del /clock
sim_time = [None]
def clock_cb(msg): sim_time[0] = msg.clock
node.create_subscription(Clock, '/clock', clock_cb, qos_be)
# spin hasta tener sim_time

# Publicar initial pose
pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', qos_be)
msg = PoseWithCovarianceStamped()
msg.header.frame_id = 'map'
msg.header.stamp = sim_time[0]
msg.pose.pose.position.x = X
msg.pose.pose.position.y = Y
msg.pose.pose.orientation.w = 1.0
msg.pose.covariance[0] = 0.25
msg.pose.covariance[7] = 0.25
msg.pose.covariance[35] = 0.07
pub.publish(msg)
```

---

*Cerrado el 2026-08-16. La última entrada es del 17 de julio de 2026. El registro de
sesiones continúa en la bitácora de decisiones de [`ESTADO.md`](../ESTADO.md).*
