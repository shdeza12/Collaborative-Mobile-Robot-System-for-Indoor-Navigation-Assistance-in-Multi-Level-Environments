# Aplicación del contrato de interfaces — bitácora de trabajo

**Fecha:** 2026-08-05 · **Semana:** S17 · **Hito:** H1

Registro de la aplicación de [`CONTRATO_INTERFACES.md`](../CONTRATO_INTERFACES.md) §6 sobre el código.
Estado de partida: [`S17_linea_base.md`](S17_linea_base.md). Criterio de cierre: §8 del contrato.

## Método de trabajo

Acordado con el director de facto del ritmo (Santiago) tras la observación *"cómo puedo comprobar
la funcionalidad de lo que haces"*:

1. Cada cambio se entrega **con la orden que lo desmentiría**, no con una afirmación.
2. Los cambios van **de uno en uno**, no en lote.
3. Lo que se pueda probar sin Gazebo (compilar, renderizar xacro, parsear el launch) se prueba
   antes de entregarlo. Solo llega a Santiago lo que exige una ventana de simulación viva.
4. **Principio del cambio nulo**: todo paso de namespaceado se introduce con valor por defecto
   vacío y se demuestra primero que *no cambia nada*. Así se separa el error de mecánica del
   error de diseño: si con el defecto vacío algo se rompe, es la mecánica.

Instrumento de verificación: [`herramientas/verificar_contrato.py`](../../herramientas/verificar_contrato.py).
Herramienta de relanzamiento limpio: [`herramientas/lanzar_sim.sh`](../../herramientas/lanzar_sim.sh).

---

## Paso 0 — Conflicto de `camera_link` (cerrado)

El marco `camera_link` tenía **dos padres**: el URDF lo colgaba de `zed_camera_link` y un
`static_transform_publisher` de `deepracer_spawn.launch.py` lo colgaba de `base_link`. En TF2 un
marco admite un solo padre; el ganador dependía del orden de llegada.

Composición de la cadena del URDF (`base_link`→`chassis`→`zed_camera_link`→`camera_link`) frente a
la transformada del launch:

| Origen | Traslación respecto a `base_link` |
|---|---|
| URDF | `(0,145294, 0, 0,130326)` |
| `static_transform_publisher` | `(0,136966, 0, 0,143272)` |

**15,39 mm de diferencia**, rotaciones idénticas. No era redundancia inocua.

**Resuelto** eliminando el `static_transform_publisher` del launch de simulación: en simulación
Gazebo coloca el sensor a partir del URDF, así que el URDF *es* la realidad física.
`deepracer.launch.py` (robot físico) queda intacto: ahí no hay URDF y esa transformada es la única
fuente.

---

## Paso A — `frame_prefix` en los xacro (cerrado)

De los 13 marcos, `robot_state_publisher` puede prefijar los que declara el URDF mediante su
parámetro `frame_prefix`. **Tres no**, porque los escriben plugins de Gazebo, que ignoran ese
parámetro. Hay que pasárselos por dentro del xacro.

| Archivo | Antes | Después |
|---|---|---|
| `control/deepracer_ros_control.xacro:40` | `<odometry_frame>odom</odometry_frame>` | `$(arg frame_prefix)odom` |
| `control/deepracer_ros_control.xacro:41` | `<robot_base_frame>base_link</robot_base_frame>` | `$(arg frame_prefix)base_link` |
| `sensor/deepracer_gazebo_lidar.xacro:52` | `<frame_name>laser</frame_name>` | `$(arg frame_prefix)laser` |

Declaración en `deepracer/deepracer.xacro`: `<xacro:arg name="frame_prefix" default="" />`.
Es el único punto de entrada que incluye esos dos archivos, así que ningún otro render se queda
sin el argumento.

**Pruebas ejecutadas:**

```
xacro .../deepracer.xacro > /tmp/urdf_despues.urdf
diff /tmp/urdf_antes.urdf /tmp/urdf_despues.urdf     -> idéntico
xacro .../deepracer.xacro frame_prefix:=robot1/ | grep -E "odometry_frame|robot_base_frame|frame_name"
  -> robot1/odom, robot1/base_link, robot1/laser
```

No requirió relanzar Gazebo: el launch invoca `xacro` sin argumentos y ese render salió idéntico
al de antes. Un archivo idéntico no puede comportarse distinto.

---

## Paso B — `namespace` y pose inicial en los launch (cerrado)

`deepracer_spawn.launch.py` reescrito con `OpaqueFunction`. Razón: el namespace hay que
componerlo como texto (`/robot1/controller_manager`) y con namespace vacío hay que **omitir**
partes, no concatenar cadenas vacías — `//controller_manager` no es un nombre válido. Las
sustituciones de launch no saben omitir; Python sí.

Argumentos nuevos, en `deepracer_spawn.launch.py` y propagados desde `deepracer_sim.launch.py`:
`namespace` (defecto `''`), `x` (`0`), `y` (`0`), `z` (`0.03`), `yaw` (`0`).

Con `namespace` vacío:

| Elemento | Comportamiento |
|---|---|
| `robot_state_publisher` | `namespace=None`, `frame_prefix=''` (su valor por defecto) |
| `xacro` | no recibe `frame_prefix:=` |
| `spawn_entity` | `-entity deepracer`, `-topic robot_description`, `-Y 0` |
| carga de controladores | sin `-c`: el defecto ya es `/controller_manager` |

**Dos suposiciones mías resultaron falsas** y se corrigieron antes de entregar:

1. `frame_prefix:=` sin valor **no** es un argumento válido de xacro. Por eso con prefijo vacío
   el argumento no se pasa en absoluto.
2. `namespace=''` en `launch_ros` **no** significa "sin namespace". `make_namespace_absolute('')`
   devuelve `'/'` y `Node` añade `__ns:=/` a la orden. Semánticamente es la raíz igual, pero no es
   *idéntico*. Se pasa `None`, que sí omite el argumento.

**Pruebas ejecutadas:**

```
ros2 launch deepracer_bringup deepracer_sim.launch.py --show-args   -> declara los 5 argumentos
```

Orden de carga de controladores resuelta en los dos modos:

```
sin namespace : ros2 control load_controller --set-state active joint_state_broadcaster
con robot1    : ros2 control load_controller --set-state active joint_state_broadcaster -c /robot1/controller_manager
```

**Regresión en simulación (Santiago, 2026-08-05):** `Las 3 comprobaciones pasan` — 6/6 tópicos,
7/7 controladores `active`, 12 marcos con un solo padre. Idéntico a la línea base.

---

## Paso C — `gazebo_ros2_control` y parámetros bajo namespace (2026-08-10)

Escrito y probado en frío. Falta la única prueba que exige Gazebo: la regresión con un robot y el
lanzamiento con `namespace:=robot1`.

### C.1 — Namespace del plugin

`gazebo_ros2_control` **no** es un plugin `gazebo_ros`: no hereda el `-robot_namespace` que
`spawn_entity.py` propaga. Crea su propio nodo y lee `<ros><namespace>` de su propio bloque SDF.
Confirmado sobre el binario:

```
strings .../libgazebo_ros2_control.so | grep -E "^__ns|remapping|robot_param"
  -> __ns:=  remapping  --ros-args  robot_param  robot_param_node
```

Se declara el argumento en `deepracer/deepracer.xacro` y se emite el bloque **solo si trae valor**,
en `control/deepracer_ros_control.xacro`:

```xml
<xacro:if value="${'$(arg robot_namespace)' != ''}">
  <ros><namespace>$(arg robot_namespace)</namespace></ros>
</xacro:if>
```

Sin barra final, al revés que `frame_prefix`: el primero se concatena con el nombre del marco
(`robot1/base_link`); el segundo es un namespace ROS 2 y la barra la pone el middleware.

**Pruebas ejecutadas:**

```
xacro deepracer.xacro > /tmp/despues.urdf
diff <(grep -v '^ *<!--' /tmp/antes.urdf) <(grep -v '^ *<!--' /tmp/despues.urdf)   -> IDÉNTICO
xacro deepracer.xacro robot_namespace:=robot1 frame_prefix:=robot1/ | grep -A2 '<ros>'
  -> <ros><namespace>robot1</namespace></ros>
  -> robot1/odom, robot1/base_link, robot1/laser
```

### C.2 — Propagación desde el launch

`deepracer_spawn.launch.py` pasa ahora los dos argumentos juntos. La condición se movió de
`if prefijo:` a `if ns:` (equivalentes: `prefijo` es no vacío si y solo si `ns` lo es).

Verificado ejecutando `acciones()` contra un `LaunchContext` sintético, sin abrir Gazebo:

| `namespace` | orden a `xacro` | `-entity` | `namespace` del nodo |
|---|---|---|---|
| `''` | `xacro <ruta>` | `deepracer` | `None` |
| `'robot1'` | `xacro <ruta> frame_prefix:=robot1/ robot_namespace:=robot1` | `robot1` | `'robot1'` |

Con un robot la orden es literalmente la de siempre, y `None` (no `''`) evita que `launch_ros`
añada `__ns:=/`.

### C.3 — Comodín en `agent_control.yaml`

Las 7 claves de primer nivel pasan de `controller_manager:` a `/**/controller_manager:`. En ROS 2
`/**` casa **cero o más** niveles de namespace, así que un solo archivo sirve a los dos agentes.

Probado sin Gazebo, con un nodo `rclpy` que toma el nombre del `controller_manager` y de un
controlador y lee el archivo con `--params-file`:

| Archivo | Sin namespace | Con `__ns:=/robot1` |
|---|---|---|
| nuevo (con `/**/`) | `update_rate=60`, `joints=['left_rear_wheel_joint']` | `update_rate=60`, `joints=['left_rear_wheel_joint']` |
| anterior (sin `/**/`) | `joints=['left_rear_wheel_joint']` | **`ParameterNotDeclaredException`** |

La fila de abajo es la que importa: demuestra a la vez que el cambio era **necesario** (el archivo
viejo no alimenta a un controlador namespaceado) y que es **nulo** para el caso de un robot.

### Lo que queda de este paso

- **Regresión con un robot** y **lanzamiento con `namespace:=robot1`** en Gazebo. Todo lo anterior
  es mecánica demostrada en frío; el comportamiento vivo no.
- `<robot_param_node>robot_state_publisher</robot_param_node>` es un nombre relativo. La hipótesis
  es que se resuelve contra el namespace del propio nodo del plugin y por tanto apunta solo a
  `/robot1/robot_state_publisher`. **Sin verificar**: si al lanzar con `robot1` el plugin no
  encuentra la descripción del robot, este es el primer sospechoso.
- Los parámetros de Nav2 necesitarán `nav2_common.launch.RewrittenYaml`. Fuera de H1.

**Trampa prevista, aún no abordada:** `/tf` y `/tf_static` son globales por contrato (§3), pero un
nodo bajo namespace publica en `/robot1/tf` salvo que se remapee explícitamente. Afecta a
`robot_state_publisher` y al `deepracer_drive_plugin` (`<publish_odom_tf>true</publish_odom_tf>`).
Si al lanzar con `robot1` el verificador reporta "no se recibió ninguna transformada", esta es la
primera hipótesis a revisar. Orden que la resuelve: `ros2 topic list | grep -c "robot1/tf"`, que
debe dar `0`.

### Nota operativa

`~/deepracer_sim_ws/install/**` son **enlaces simbólicos** al repositorio para los `.xacro`,
`.launch.py` y `.yaml`. Editarlos surte efecto sin `colcon build`; solo el código compilado
(el plugin C++) exige recompilar.

---

## Paso D — el robot partido en dos mitades (2026-08-10)

Con `namespace:=robot1`, los 7 controladores arrancaban bajo `/robot1/controller_manager` (correcto)
pero el coche **no se movía** y el verificador fallaba «Raíz limpia» por seis tópicos sueltos:

```
/left_front_wheel_velocity_controller/commands
/right_front_wheel_velocity_controller/commands
/left_rear_wheel_velocity_controller/commands
/right_rear_wheel_velocity_controller/commands
/left_steering_hinge_position_controller/commands
/right_steering_hinge_position_controller/commands
```

Un solo defecto explicaba ambas cosas. `ros2 topic info` sobre uno de esos tópicos lo delató:

```
Publisher count: 2
  Node namespace: /robot1     <-- el plugin, publicando en la RAÍZ
  Node namespace: /
```

**Causa raíz.** `deepracer_drive_plugin` creaba sus seis publicadores con nombres **absolutos**
(`"/left_front_wheel_velocity_controller/commands"`). En ROS 2, un nombre que empieza por `/`
**ignora el namespace del nodo**. El plugin vivía en `/robot1` pero publicaba en la raíz, mientras
los controladores de `/robot1` escuchaban en `/robot1/.../commands`. Las órdenes salían y nadie las
recogía: el robot quedaba partido en dos mitades que no se hablaban.

**Arreglo.** Quitar la barra inicial en los seis publicadores
(`gazebo_ros_deepracer_drive.cpp:247-262`). Sin namespace, un nombre relativo se resuelve a
`/left_front_wheel_velocity_controller/commands` — exactamente el nombre de siempre, así que el
cambio es nulo para un robot. Con namespace se resuelve a `/robot1/...`, que es lo que hace falta.

Tras recompilar, los seis tópicos sueltos desaparecen y **el coche se mueve** con
`ros2 topic pub --once /robot1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"`.
La cadena `/robot1/cmd_vel → plugin → /robot1/.../commands → controladores → ruedas` queda cerrada.

### Dos aclaraciones que costaron un ciclo de prueba cada una

**El directorio no es el paquete.** La carpeta se llama `deepracer_gazebo/` pero el paquete es
`deepracer_drive_plugin`. `colcon build --packages-select deepracer_gazebo` no compila nada y *no
falla*: Gazebo sigue cargando el binario viejo. Comprobación obligatoria antes de dar por buena una
recompilación —
`stat -c '%y %n' ~/deepracer_sim_ws/build/deepracer_drive_plugin/libgazebo_ros_deepracer_drive.so`
debe dar una fecha posterior a la del `.cpp`.

**`cmd_vel` es velocidad, no distancia.** `linear.x: 0.5` significa 0,5 m/s sostenidos, y el plugin
retiene la última orden sin temporizador. Que el coche «no pare» es el comportamiento correcto. Para
detenerlo: `ros2 topic pub --once /robot1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}}"`.

### Hipótesis descartada: fantasmas del daemon

Con el verificador reportando tópicos de Nav2/RViz en la raíz sin procesos aparentes, se sospechó de
la caché del daemon de ROS 2 (`pkill -9` mata participantes sin darlos de baja en DDS). **Falso.**
`ros2 topic list` y `ros2 topic list --no-daemon` devuelven listas idénticas, y el `/cmd_vel`
residual tenía un publicador vivo (`teleop_twist_keyboard`, namespace `/`). La contaminación era
**real**: procesos huérfanos de lanzamientos anteriores. `verificar_contrato.py` no necesita cambio;
`lanzar_sim.sh` sí lo necesitaba, y por eso su lista de muerte ahora incluye Nav2, RViz y
`component_container`.

**Consecuencia operativa:** el verificador mide el grafo entero. Cualquier nodo abierto en otra
terminal —un `teleop_twist_keyboard` en la raíz, por ejemplo— cuenta como incumplimiento del
contrato. Para conducir a `robot1` hay que lanzar el teleop **dentro del namespace**:
`ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r __ns:=/robot1`.

---

## Paso E — H1 bloqueado por una limitación de `gazebo_ros` (2026-08-11)

Con `robot1` correcto, al añadir `robot2` al mismo `gzserver` aparecieron **dos** defectos
encadenados. El primero es nuestro y está resuelto; el segundo es de `gazebo_ros` y bloquea H1.

### E.1 — Colisión de nombres de nodo (resuelto)

Síntoma: `ros2 topic pub /robot2/cmd_vel` respondía *"Waiting for at least 1 matching
subscription"*. `ros2 node list` mostraba que `robot2` solo tenía `controller_manager` y sus 7
controladores: **ninguno** de los cuatro nodos de plugin (`gazebo_ros_deepracer_drive`, `rp_lidar`,
`camera_controller`, `gazebo_ros2_control`).

`gazebo_ros` lleva un registro **estático y global** de nombres de nodo
(`/opt/ros/humble/include/gazebo_ros/node.hpp:150`, `static_existing_nodes_`) y guarda el nombre
**pelado**, sin namespace. El nombre sale del atributo `name` del `<plugin>`, idéntico en los dos
URDF. Al cargar el segundo robot, `gazebo_ros::Node::Get()` encontraba el nombre ocupado y devolvía
el nodo del primero. El propio `libgazebo_ros_node.so` lo dice:

> *"Found multiple nodes with same name... Try changing one of the plugin names or use a different
> ROS namespace."*

Cambiar el namespace **no** basta, porque el registro no lo mira.

**Arreglo:** propiedad `sufijo_ns` en `deepracer.xacro`, que añade `_robot1` / `_robot2` al atributo
`name` de los cuatro plugins. Vacía sin namespace, así que con un robot los nombres quedan
idénticos a los originales. Verificado renderizando el URDF en los tres casos.

### E.2 — El namespace del primer modelo se impone a todos (sin resolver)

Con nombres únicos, `robot2` ya crea sus **propios** nodos... pero en el namespace de `robot1`:

```
/robot1/gazebo_ros_deepracer_drive_robot2
/robot1/rp_lidar_robot2
[robot1.gazebo_ros_deepracer_drive_robot2]: Subscribed to [/robot1/cmd_vel]
```

Descartado que sea culpa nuestra:

| Comprobación | Resultado |
|---|---|
| URDF renderizado de `robot2` | `<namespace>robot2</namespace>` en los 4 plugins |
| SDF que Gazebo tiene cargado (`gz model -m robot2 -i`) | `innerxml` con `<namespace>robot2</namespace>` |
| Variables de entorno de `gzserver` | sin `ROS_NAMESPACE` |
| Línea de comandos de `gzserver` | sin argumentos ROS globales |
| `spawn_entity.py -robot_namespace robot2` | **no cambia nada** |

**Prueba decisiva — se invirtió el orden de carga.** Lanzando `robot2` primero y `robot1` después:

```
/robot2/gazebo_ros_deepracer_drive_robot1
[robot2.gazebo_ros_deepracer_drive_robot1]: Subscribed to [/robot2/cmd_vel]
```

El efecto es **simétrico**: manda el primer modelo que se carga, sea cual sea. No es un problema de
`robot1` ni de nuestro plugin — afecta igual al LiDAR y a la cámara, que son binarios de `gazebo_ros`
que no hemos tocado. Es una limitación de `gazebo_ros` en Humble: **el namespace del primer nodo
creado en el proceso `gzserver` se aplica a todos los nodos de plugin posteriores.**

Consecuencia medida con `ros2 topic list --no-daemon`, con los dos robots vivos:

```
/robot2/odom
/robot2/scan
```

Un solo `odom` y un solo `scan` para los dos robots. Los sensores y la odometría son
**indistinguibles**, y la prueba de aislamiento de mando de H1 no se puede ni plantear.

### E.3 — Corrección de una afirmación anterior

En el «Paso D» se descartó que el daemon de ROS 2 dejara nodos fantasma. **Era incorrecto.** En este
paso, `ros2 node list` mostraba 14 nodos `/robot1/*` de una corrida ya matada con `pkill -9`, y
`ros2 node list --no-daemon` devolvía solo los 5 reales. El daemon **sí** retiene entradas de
participantes muertos con SIGKILL; el caso del «Paso D» era un `teleop_twist_keyboard` realmente
vivo, y de ahí la conclusión equivocada. **Toda medición del grafo debe hacerse con `--no-daemon`.**

### E.4 — Trampa nueva: comentarios del URDF y el parser YAML

Un comentario añadido al xacro tumbó el lanzamiento entero con:

```
Unable to parse the value of parameter robot_description as yaml
```

`launch_ros` pasa el URDF por `yaml.safe_load`. Un comentario que contenga **dos puntos seguidos de
espacio** (`Sufijo: nombre...`) hace que YAML lo lea como clave de diccionario y aborte. Los
comentarios que sobreviven al renderizado no pueden contener ese patrón. Detectado en frío con
`xacro ... | python3 -c "import yaml; yaml.safe_load(...)"`, que conviene correr tras tocar xacro.

---

## Trampas encontradas por el camino

Registradas para no volver a pagarlas.

| Síntoma | Causa real |
|---|---|
| `gzserver` muere con código 255 sin explicación | Un `gzserver` huérfano de un lanzamiento anterior sigue agarrado al puerto 11345. Ctrl-C sobre `ros2 launch` no mata a sus hijos |
| `pgrep -a static_transform` dice que no hay ninguno, y había 7 | El nombre de proceso se trunca a 15 caracteres; `static_transform_publisher` tiene 16. Por eso `lanzar_sim.sh` usa `pkill -f` y no `pkill -x` |
| `pkill -9 -f gzserver` escrito en la terminal mata la propia terminal | `-f` casa la línea de comando completa, que incluye el shell que lo invoca. Dentro de un `.sh` es seguro; a mano no. Truco para uso manual: `'[g]zserver'` |
| `pkill -9 gzserver gzclient` no mata nada y parece exitoso | `pkill` acepta un solo patrón |
| El verificador reportaba "7 controladores no activos" con los 7 activos | (a) `ros2 control list_controllers` escribe sus líneas `[INFO]` por **stdout**, y se colaban como controladores. (b) colorea la salida con ANSI, así que `"active"` era `"\x1b[92mactive\x1b[0m"` |
| `lanzar_sim.sh` abortaba con `AMENT_TRACE_SETUP_FILES: unbound variable` | `set -u` es incompatible con los `setup.bash` de ROS |
| Los arreglos de SLAM de 2026-08-03 nunca se ejecutaron | `~/deepracer_sim_ws/src/aws-deepracer` seguía siendo una copia, no un enlace al repositorio. La verificación anterior comprobó que `install/` apuntaba a `src/` — cierto — pero no que `src/` fuese a su vez una copia |

---

## Archivos tocados hasta aquí

```
Documentos/CONTRATO_INTERFACES.md                                        (nuevo)
Documentos/Evidencia/S17_linea_base.md                                   (nuevo)
Documentos/Evidencia/S17_aplicacion_contrato.md                          (nuevo, este)
herramientas/verificar_contrato.py                                       (nuevo)
herramientas/lanzar_sim.sh                                               (nuevo)
Robot/.../deepracer_description/models/xacro/deepracer/deepracer.xacro   (arg frame_prefix)
Robot/.../deepracer_description/models/xacro/control/deepracer_ros_control.xacro
Robot/.../deepracer_description/models/xacro/sensor/deepracer_gazebo_lidar.xacro
Robot/.../deepracer_bringup/launch/deepracer_spawn.launch.py             (reescrito)
Robot/.../deepracer_bringup/launch/deepracer_sim.launch.py               (argumentos)
Robot/.../deepracer_bringup/config/agent_control.yaml                    (comodín /**/)
Robot/.../deepracer_gazebo/src/gazebo_ros_deepracer_drive.cpp            (nombres relativos)
ESTADO.md
```

Nada de esto está commiteado todavía.
