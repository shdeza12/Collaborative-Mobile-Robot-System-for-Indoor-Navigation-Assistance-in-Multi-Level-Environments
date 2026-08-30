# Guía operativa — Simulación + SLAM + Teleop + RViz

Procedimiento para mapear un mundo Gazebo con `slam_toolbox` sobre la sim del DeepRacer y prepararlo para AMCL/Nav2. Cuatro terminales independientes. **Cada terminal nueva** necesita sourcear `~/deepracer_sim_ws/install/setup.bash`.

Requiere el proyecto instalado y verificado según los seis pasos del
[`README`](../README.md#instalación). Los comandos que empiezan por `herramientas/…` se ejecutan
**desde la raíz del repositorio**, esté donde esté tu clon; los que empiezan por `ros2 …`, desde
`~/deepracer_sim_ws` con el `source install/setup.bash` hecho.

> Mundo vigente: `primer_piso_v2.world`, el que declara el README y el que cargan los
> launch por defecto —de este mismo repositorio—. Para otro mundo: `world:=<ruta>`.
> El mapa que se obtenga se acepta **solo** si
> `herramientas/verificar_mapa.py` devuelve 0: los mapas actuales de `primer_piso` no
> pasan esa verificación (riesgo R10 de [`ESTADO.md`](../ESTADO.md)).

---

## Terminal A — Gazebo + spawn del robot

```bash
cd ~/deepracer_sim_ws
source install/setup.bash
ros2 launch deepracer_bringup deepracer_sim.launch.py
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

Las URIs `package://` de las mallas estaban mal formadas y RViz no las resolvía; **corregido el 2026-08-11**. `herramientas/verificar_instalacion.sh` comprueba que todas resuelvan en disco.

#### Ver al robot cuando está lejos del origen

Si el robot se spawnea lejos del origen `odom` (en pruebas reales aparece a ~30 m), la cámara por defecto no lo enmarca. Opciones:

- Click en el viewport y presionar la tecla **`f`** (focus).
- Panel **Views** (derecha) → tipo `Orbit` → **Target Frame** = `base_link`. Así la cámara sigue al robot mientras se mapea.

#### Guardar la configuración

Una vez funcionando, **`Ctrl+S`** en RViz para guardarla en:

```
~/Tesis/Robot/aws-deepracer/deepracer_bringup/config/slam_view.rviz
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

> **Mundo de trabajo actual: `primer_piso_v2.world`** (58,2 m × 6,7 m). El recorrido debe cubrir
> el pasillo completo de extremo a extremo, no solo el primer tramo.

### Paso obligatorio: verificar antes de dar el mapa por bueno

Guardar primero a un archivo temporal y validarlo. **Con Gazebo y slam_toolbox todavía
corriendo**, para poder completar el recorrido sin perder la sesión si el mapa no pasa:

Desde la terminal del workspace:

```bash
ros2 run nav2_map_server map_saver_cli -f /tmp/mapa_candidato --ros-args -p use_sim_time:=true
```

Y desde la **raíz del repositorio** —las dos rutas van relativas a ella, así que el comando
funciona clones donde clones:

```bash
python3 herramientas/verificar_mapa.py /tmp/mapa_candidato.yaml primer_piso_v2.world
```

El script compara la extensión realmente mapeada contra la geometría del `.world` y rechaza
el mapa si la cobertura es insuficiente o si detecta deriva de pose (el pasillo "abriéndose"
más de lo que mide en realidad). Si sale `RECHAZADO`, **no guardar como definitivo**: seguir
recorriendo los tramos faltantes y repetir la verificación.

Los dos mapas que hay en el repositorio están rechazados por esta vía. Medido el 2026-08-11:
`primer_piso` da 34,0 % de cobertura en X y 14,1 m de anchura aparente; `primer_piso_v2`,
35,5 % y 15,0 m. El mundo mide 5,3 m de ancho. Es el riesgo R10 de `ESTADO.md`.

### Guardado definitivo

Solo cuando la verificación salga `ACEPTADO`, **antes de cerrar nada**, ejecutar en una
terminal nueva (sourceada):

**Formato Nav2 / AMCL (`.pgm` + `.yaml`):**

```bash
ros2 run nav2_map_server map_saver_cli -f ~/Tesis/Robot/aws-deepracer/deepracer_bringup/maps/primer_piso_v2 --ros-args -p use_sim_time:=true
```

**Formato slam_toolbox (`.posegraph` + `.data`) — opcional, para retomar mapeo después:**

```bash
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '$HOME/Tesis/Robot/aws-deepracer/deepracer_bringup/maps/primer_piso_v2'}"
```

Verificar que los archivos aparecen en `Robot/aws-deepracer/deepracer_bringup/maps/`. Recién entonces cerrar Gazebo, slam_toolbox y RViz.

---

## Orden recomendado al cerrar la sesión

1. Guardar mapa (comandos de arriba).
2. Guardar config de RViz (`Ctrl+S` si se cambió algo).
3. `Ctrl+C` en cada terminal (Gazebo, slam_toolbox, teleop, rviz2) en cualquier orden.
4. Si Gazebo deja procesos zombis: `pkill -f gzserver; pkill -f gzclient`.
