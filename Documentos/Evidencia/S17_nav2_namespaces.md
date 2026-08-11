# Nav2 con namespaces — dos robots navegando a la vez

**Fecha:** 2026-08-10 · **Semana:** S17 · **Hito:** H1

Cierre del hallazgo colateral nº1 de `S17_dos_simuladores.md`: `nav_amcl_demo_sim.launch.py` no
soportaba namespaces y el `global_costmap` fallaba en bucle con
`Invalid frame ID "map" ... frame does not exist`. Era el trabajo bloqueante: sin esto los dos
robots del sistema colaborativo no navegan.

## Qué se cambió

| Archivo | Cambio |
|---|---|
| `deepracer_navigation_sim.launch.py` | Argumento `namespace`; los 6 nodos de Nav2 cuelgan de él; marcos del robot prefijados; YAML anidado bajo la clave del namespace |
| `deepracer_localization_sim.launch.py` | **Nuevo.** Reemplaza a `nav2_bringup/localization_launch.py` para map_server + AMCL |
| `nav_amcl_demo_sim.launch.py` | Argumento `namespace` propagado a los tres launches incluidos |

### Por qué un launch de localización propio

`nav2_bringup/localization_launch.py` no sirve para esta topología, y falla **en silencio** por dos
razones independientes:

1. Sus nodos no llevan `namespace=`. El argumento `namespace` solo se usa como `root_key` del YAML;
   quien namespacea los nodos es el `PushRosNamespace` de `bringup_launch.py`. Incluirlo tal cual
   deja `/amcl` y `/map_server` en la raíz leyendo un YAML anidado bajo `robot1:`, es decir, sin
   parámetros y con los valores por defecto del código.
2. Remapea `('/tf', 'tf')` de forma fija (`localization_launch.py:52-53`). Bajo un namespace eso
   manda la transformada `map -> odom` a `/robot1/tf`, mientras `robot_state_publisher` y Gazebo
   publican en `/tf` absoluto. El árbol TF quedaría partido en dos.

Aquí cada robot vive en su propio `ROS_DOMAIN_ID`, así que el `/tf` de cada dominio ya está aislado
y **no se remapea nada**. Lo que sí se prefija son los marcos, porque así los publica el URDF.

### Por qué rutas completas y no claves sueltas

`RewrittenYaml` sustituye primero por clave hoja y después por ruta completa
(`rewritten_yaml.py:108-122`). La clave `global_frame` aparece dos veces en el YAML con valores
distintos: `map` en el costmap global y `odom` en el local. Reescribir por clave suelta igualaría
las dos y rompería el costmap local **sin dar ningún error**. Por eso se usan rutas del tipo
`local_costmap.local_costmap.ros__parameters.global_frame`.

Los marcos globales (`map`) no se prefijan: no pertenecen al robot, los publica el `map_server` y
son el punto de anclaje común.

## Resultado 1 — principio de cambio nulo

Con `namespace` vacío el YAML que llega a los nodos se comparó parámetro a parámetro contra el de
disco. Las únicas diferencias son las que el launch original ya inyectaba: `use_sim_time`, las dos
rutas de árboles de comportamiento y `yaml_filename` del mapa. **Ningún marco cambia y ninguna
clave se anida.** El comportamiento con un solo robot es el de siempre.

Lanzado sin namespace: los 6 nodos de Nav2 y los 2 de localización llegan a `active`, cero
apariciones de `Invalid frame ID`, TF `map -> base_link` resuelve.

## Resultado 2 — un robot con namespace

`ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py gui:=false namespace:=robot1`

| Comprobación | Resultado |
|---|---|
| `Invalid frame ID` en el log | **0** (antes: en bucle) |
| Líneas `[ERROR]` | 0 |
| Parámetros efectivos | `global_costmap...robot_base_frame = robot1/base_link`, `local_costmap...global_frame = robot1/odom`, `amcl base_frame_id = robot1/base_link`, `amcl odom_frame_id = robot1/odom` |
| TF `map -> robot1/base_link` | resuelve |
| Costmap global publicado | 384 × 262 @ 0.06 m/celda, `frame_id: map` |
| Controladores | 7 `active` |
| `NavigateToPose` a (2.0, 0.0) | **SUCCEEDED** — `SmacPlannerHybrid` planificó y el controlador siguió la ruta |

Que los parámetros efectivos salgan prefijados demuestra que el anidado bajo `root_key` funciona:
si no, los nodos habrían arrancado con los valores por defecto del código y `ros2 param get` habría
devuelto `base_link` a secas.

## Resultado 3 — los dos robots navegando a la vez

Dos instancias completas (Gazebo + Nav2 + AMCL), en dominios y `GAZEBO_MASTER_URI` distintos, con
objetivo enviado **simultáneamente** a ambos:

| | robot1 (dominio 0) | robot2 (dominio 2) |
|---|---|---|
| Nodos gestionados activos | sí (navegación y localización) | sí (navegación y localización) |
| `Invalid frame ID` / `[ERROR]` | 0 / 0 | 0 / 0 |
| Resultado de `NavigateToPose` (2.0, 0.0) | **SUCCEEDED** | **SUCCEEDED** |
| Odometría final | x = 1.76, y = 0.01 | x = 1.72, y = 0.02 |
| RTF durante la navegación | **0.996** | **0.996** |

Carga: 7.9 de 12 hilos en el pico de arranque; 5.9 GiB de 13.8 GiB de RAM, 7.3 GiB disponibles.
Las dos pilas de navegación caben con margen y **siguen a tiempo real**, que es la condición para
que las métricas de tiempo del objetivo 4 sean válidas.

> **Vigencia de los resultados 1 a 3.** Se tomaron **antes** de los cambios de visualización
> descritos más abajo (hallazgos nº2 y nº3), que tocan los mismos `.xacro` que describen el
> vehículo. Lo que demuestran —propagación del namespace, anidado del YAML, marcos prefijados,
> objetivos alcanzados— no depende de la geometría de los meshes, pero **la corrida completa hay
> que repetirla** antes de dar H1 por cerrado. Queda como paso 1 del martes 11.

## Hallazgo colateral nº1

**Carrera al cargar controladores.** En una de las corridas, `left_rear_wheel_velocity_controller`
quedó en `unconfigured`: el `ros2 control load_controller` del launch agota su espera de 10 s,
reintenta, y el segundo intento muere con `A controller named ... was already loaded` antes de
llegar a `--set-state active`. El resultado es un robot con una rueda motriz sin actuar.

Es **anterior a este cambio** (está en la secuencia de carga de `deepracer_sim.launch.py`, que no se
tocó) e intermitente. Se recupera a mano con:

```
ros2 control set_controller_state left_rear_wheel_velocity_controller inactive && ros2 control set_controller_state left_rear_wheel_velocity_controller active
```

Conviene arreglar la carrera antes de tomar medidas de tiempo, porque falsea la dinámica del robot.

## Hallazgo colateral nº2

**Las URIs `package://` de los meshes estaban malformadas, y arreglarlas rompió Gazebo.**

Al activar `RobotModel` en RViz para tomar la evidencia visual, los 12 enlaces fallaban. La causa
no era el namespace: la sintaxis de la URI es `package://<paquete>/<ruta>` y los cuatro `.xacro`
del vehículo escribían `package://meshes/...`, es decir, **sin nombre de paquete**. RViz resuelve
por índice ament y buscaba un paquete llamado `meshes`, que no existe. Se corrigieron 26
ocurrencias a `package://deepracer_description/meshes/...` y RViz pasó a cargar el modelo.

Eso **rompió la visualización en Gazebo**, que resuelve la misma URI de otra forma: busca el resto
de la cadena dentro de cada entrada de `GAZEBO_MODEL_PATH`, y la única que aporta este paquete es
la que declara su propio `package.xml` (`gazebo_model_path="${prefix}"`, o sea
`.../share/deepracer_description`).

| URI | Gazebo compone | RViz (índice ament) |
|---|---|---|
| original `package://meshes/x.STL` | `share/deepracer_description/`**`meshes/x.STL`** ✓ | paquete `meshes` → no existe ✗ |
| corregida `package://deepracer_description/meshes/x.STL` | `share/deepracer_description/`**`deepracer_description/meshes/x.STL`** ✗ | ✓ |

Síntoma: en el visor de Gazebo el modelo `robot1` aparece en el árbol con sus 7 enlaces, sus 6
articulaciones y **sus dos plugins cargados**, pero sin geometría que dibujar. Un modelo sin
visuales no es un modelo que no cargó: la distinción importa porque el segundo caso sí habría
sido un fallo de namespace.

La URI corregida es la correcta —es la sintaxis estándar y la única que resuelve por índice de
paquetes—, así que lo que se ajusta es la ruta exportada:

```xml
<gazebo_ros gazebo_model_path="${prefix}:${prefix}/.." />
```

`${prefix}/..` = `.../share`, con lo que `share/` + `deepracer_description/meshes/x.STL` sí
resuelve. Se conserva `${prefix}` por compatibilidad. Comprobado sin lanzar nada: las 7 URIs
distintas del vehículo resuelven contra el `GAZEBO_MODEL_PATH` que produce `gazebo_ros_paths.py`
(`$(arg shell)` es un argumento xacro; sus dos valores posibles están en disco).

`package.xml` está enlazado por symlink al `install`, así que **no requiere `colcon build`**, pero
sí relanzar: `GAZEBO_MODEL_PATH` se calcula al arrancar.

**Estado: corregido, pendiente de comprobación visual simultánea en Gazebo y RViz.**

## Hallazgo colateral nº3

**El argumento `gui` nunca ha funcionado.** `deepracer_sim.launch.py` lo declara en la línea 63
con defecto `true`, pero añade `gazebo_client_launcher` en la línea 82 **sin `condition`**, y no
lo consume en ningún otro sitio. Se declara y no se lee.

El argumento sí se propaga, pese a que `nav_amcl_demo_sim.launch.py` no lo declare:
`ros2 launch ... --show-args` lo lista, porque recorre los launches incluidos y las
configuraciones se heredan hacia el interior de cada `IncludeLaunchDescription`. Es decir,
`gui:=false` llega hasta donde tiene que llegar y **allí no lo mira nadie**. La causa es una sola,
no dos. (Corrección de una afirmación errónea de la primera redacción de este documento; se deja
constancia porque el mismo mecanismo de herencia explica que `y:=2.0` sí funcione desde el launch
de más arriba.)

Consecuencia para la evidencia: **todas las corridas de este documento se hicieron con `gzclient`
abierto**, incluidas las de los resultados 1 a 3. Las cifras de carga y de RTF son por tanto
conservadoras —con la interfaz cerrada el margen sería mayor—, no optimistas.

No se corrige aquí. Es un cambio de dos líneas (`IfCondition` sobre `gazebo_client_launcher`),
pero no es necesario para H1 y toca un launch que en este periodo no se estaba modificando.

## Criterio de cierre

Cumplido **en lo funcional**. Dos robots con pila Nav2 completa, cada uno bajo su namespace,
alcanzan objetivos de navegación simultáneamente y a tiempo real. Con namespace vacío nada cambia
respecto al comportamiento anterior.

Queda una repetición pendiente: los hallazgos nº2 y nº3 se descubrieron después de tomar esos
resultados, y el nº2 modificó los `.xacro` del vehículo. La repetición no busca un resultado
nuevo, busca constancia de que la corrección de los meshes no alteró el comportamiento.

## Cómo refutar este resultado

```
ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1
ros2 param get /robot1/global_costmap/global_costmap robot_base_frame
ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0}, orientation: {w: 1.0}}}}"
```

Si el parámetro devuelve `base_link` sin prefijo, el anidado del YAML no está funcionando. Si el
objetivo no termina en `SUCCEEDED` o el log muestra `Invalid frame ID`, este documento está
equivocado.
