# Guía operativa — Simulación + SLAM + Teleop + RViz

Procedimiento para mapear un mundo Gazebo con `slam_toolbox` sobre la sim del DeepRacer y prepararlo para AMCL/Nav2. Cuatro terminales independientes. **Cada terminal nueva** necesita sourcear `~/deepracer_sim_ws/install/setup.bash`.

> Mundo de trabajo actual (S15): `primer_piso.world`. Para otros mundos, cambiar la ruta de `world:=`.

---

## Terminal A — Gazebo + spawn del robot

```bash
cd ~/deepracer_sim_ws
source install/setup.bash
ros2 launch deepracer_bringup deepracer_sim.launch.py world:=/home/santiago/Documents/Tesis/primer_piso.world
```

Esperar a que Gazebo abra el mundo y el DeepRacer aparezca dentro. Verificar en el log que los 7 controladores (`joint_state_broadcaster` + 4 ruedas + 2 hinges de dirección) queden en estado `active`. Si alguno sale como `inactive` o aparece `Unknown state 'start'`, hay una regresión en `agent_control.yaml` que hay que corregir antes de seguir.

---

## Terminal B — slam_toolbox

```bash
cd ~/deepracer_sim_ws
source install/setup.bash
ros2 launch deepracer_bringup slam_toolbox.launch.py
```

El launch debe inyectar `use_sim_time: True` (commit `2e881df`). Verificar con:

```bash
ros2 param get /slam_toolbox use_sim_time
```

Resultado esperado: `Boolean value is: True`.

---

## Terminal C — Teleop

```bash
source /opt/ros/humble/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Por defecto publica en `/cmd_vel`, que es lo que escucha el plugin Ackermann del DeepRacer. **No agregar `--ros-args -r cmd_vel:=/cmd_vel`**: es redundante y, si el shell parte la línea, falla.

Controles:
- `i`/`,` → adelante / atrás
- `j`/`l` → giro izquierda / derecha
- `z`/`x` → bajar / subir velocidad lineal
- `c`/`v` → bajar / subir velocidad angular

Para mapear bien conviene **velocidades bajas** (ajustar con `z` varias veces antes de moverse). Giros y aceleraciones bruscas confunden a slam_toolbox.

---

## Terminal D — RViz

```bash
rviz2
```

### Configuración de displays

#### Global Options (arriba del árbol)

| Propiedad | Valor |
|-----------|-------|
| `Fixed Frame` | `map` |

Si al arrancar slam_toolbox aún no publicó el primer `/map`, RViz se queja con `No tf data`. En ese caso, dejar `Fixed Frame` en `odom` por unos segundos y volver a `map` cuando aparezca el mapa.

#### Add → By topic → `/map` → Map

Expandir el display **Map** y luego expandir su sub-propiedad **Topic**. Configurar:

**Dentro de Topic:**

| Propiedad | Valor |
|-----------|-------|
| `Topic` | `/map` |
| `Depth` | `5` |
| `History Policy` | `Keep Last` |
| `Reliability Policy` | `Reliable` |
| `Durability Policy` | **`Transient Local`** |

> El `Durability Policy = Transient Local` es **obligatorio**. slam_toolbox publica el mapa con esa política, y si RViz queda en `Volatile` (default), nunca recibe el primer mensaje y el mapa no aparece aunque el tópico esté publicando bien.

**Otras propiedades del Map (fuera de Topic):**

| Propiedad | Valor |
|-----------|-------|
| `Alpha` | `0.7` |
| `Color Scheme` | `map` |
| `Draw Behind` | `false` |

#### Add → By topic → `/scan` → LaserScan

Para ver el haz del LIDAR en vivo. Subir `Size (m)` a ~0.05 si los puntos se ven muy pequeños.

#### Add → TF

Para ver los frames moviéndose (`base_link`, `odom`, `map`). Permite confirmar visualmente que el TF tree es coherente.

#### Add → RobotModel (opcional)

Actualmente las rutas `package://meshes/...` en los xacros están mal formadas (Task #7 pendiente). El display funciona pero muestra errores en consola por meshes no encontradas. **No bloquea el mapeo.** Si molestan los errores, removerlo (clic derecho → Remove).

#### Ver al robot cuando está lejos del origen

Si el robot se spawnea lejos del origen `odom` (en pruebas reales aparece a ~30 m), la cámara por defecto no lo enmarca. Opciones:

- Click en el viewport y presionar la tecla **`f`** (focus).
- Panel **Views** (derecha) → tipo `Orbit` → **Target Frame** = `base_link`. Así la cámara sigue al robot mientras se mapea.

#### Guardar la configuración

Una vez funcionando, **`Ctrl+S`** en RViz para guardarla en:

```
~/Documents/Tesis/Robot/aws-deepracer/deepracer_bringup/config/slam_view.rviz
```

Próximas sesiones se abre con `rviz2 -d <ruta>` y no hace falta armar los displays otra vez.

---

## Comandos de diagnóstico rápido

Si el mapa no acumula en RViz pero el robot se mueve:

```bash
ros2 param get /slam_toolbox use_sim_time           # esperado: True
ros2 topic hz /map                                   # esperado: ~1 Hz
ros2 topic hz /scan                                  # esperado: ~10 Hz
ros2 run tf2_ros tf2_echo odom base_link             # debe imprimir transforms
ros2 topic info /map -v                              # confirma durability TRANSIENT_LOCAL
```

Si los 4 dan resultados sanos pero RViz se ve vacío, el problema es de visualización (Durability Policy o cámara fuera de cuadro), no de SLAM.

---

## Guardar el mapa

Mientras la sim, slam_toolbox y RViz están todavía corriendo y el mapa se ve cerrado y consistente, **antes de cerrar nada**, ejecutar en una terminal nueva (sourceada):

**Formato Nav2 / AMCL (`.pgm` + `.yaml`):**

```bash
ros2 run nav2_map_server map_saver_cli -f ~/Documents/Tesis/Robot/aws-deepracer/deepracer_bringup/maps/primer_piso
```

**Formato slam_toolbox (`.posegraph` + `.data`) — opcional, para retomar mapeo después:**

```bash
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/home/santiago/Documents/Tesis/Robot/aws-deepracer/deepracer_bringup/maps/primer_piso'}"
```

Verificar que los archivos aparecen en `Robot/aws-deepracer/deepracer_bringup/maps/`. Recién entonces cerrar Gazebo, slam_toolbox y RViz.

---

## Orden recomendado al cerrar la sesión

1. Guardar mapa (comandos de arriba).
2. Guardar config de RViz (`Ctrl+S` si se cambió algo).
3. `Ctrl+C` en cada terminal (Gazebo, slam_toolbox, teleop, rviz2) en cualquier orden.
4. Si Gazebo deja procesos zombis: `pkill -f gzserver; pkill -f gzclient`.
