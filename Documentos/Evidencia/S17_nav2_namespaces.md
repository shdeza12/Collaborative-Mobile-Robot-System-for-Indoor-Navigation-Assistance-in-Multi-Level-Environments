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

> **Vigencia de los resultados 1 a 3.** Se tomaron antes de los cambios de visualización descritos
> más abajo (hallazgos nº2 y nº3), que tocan los mismos `.xacro` del vehículo. **Repetidos el
> 2026-08-14 sobre el código de `d7d8387`, con el mismo resultado**; ver «Resultado 4». La
> advertencia queda anulada.

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

**Estado: corregido y comprobado** el 2026-08-14. El mismo modelo se ve a la vez en Gazebo
(`S17_gazebo_robot1_modelo.png`) y en RViz con `TF Prefix: robot1`
(`S17_rviz_robot1_robotmodel.png`), que era justamente el conflicto: una sola URI sirviendo a los
dos resolvedores.

La configuración con la que se tomó esa captura está versionada en
`Robot/aws-deepracer/deepracer_description/rviz/nav2_robot1_view.rviz`, para que la evidencia sea
reproducible y no dependa de reconstruir el panel a mano:

```bash
rviz2 -d ~/deepracer_sim_ws/src/aws-deepracer/deepracer_description/rviz/nav2_robot1_view.rviz
```

Sus herramientas publican en `/robot1/initialpose` y `/robot1/goal_pose`, no en los tópicos
globales. Nacieron sin prefijo —RViz los escribe así por defecto— y en esa forma los clics de
*2D Pose Estimate* y *2D Nav Goal* salían a un tópico que bajo namespace no escucha nadie: se ven
publicados y no pasa nada. El contrato de interfaces fija `/<ns>/initialpose`
(`Documentos/CONTRATO_INTERFACES.md`), así que se corrigieron antes de versionar el archivo.

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

## Resultado 4 — repetición sobre el código corregido (2026-08-14)

Repetición de los resultados 1 a 3 sobre `d7d8387`, es decir **después** de la corrección de los
meshes y de la del mapa y AMCL (`35c47da`). Dos instancias, separadas por `ROS_DOMAIN_ID` y
`GAZEBO_MASTER_URI`; robot2 aparece en `y = 2.0`.

**Navegación.** Un objetivo a cada robot, y el desplazamiento medido contra `/odom` —no contra la
estimación de AMCL, que es lo que evalúa el propio Nav2 al declarar `SUCCEEDED`:

| | `/odom` antes | `/odom` después | Recorrido real | Objetivo (5,0 m) |
|---|---|---|---|---|
| robot1 | (−0,099 · 0,113) | (4,790 · 0,097) | **4,89 m** | `SUCCEEDED` |
| robot2 | (−0,064 · 2,130) | (4,893 · 2,062) | **4,96 m** | `SUCCEEDED` |

Los dos vehículos se desplazaron de verdad. El residuo (11 cm y 4 cm) cae dentro de la tolerancia
de llegada configurada.

**Aislamiento de mando.** Cuatro evidencias independientes, ninguna de ellas de desplazamiento:

1. `ros2 topic list` en cada dominio: **62 tópicos en cada uno**, y **ninguno** cruzado —cero
   `/robot2/*` desde el dominio 0, cero `/robot1/*` desde el dominio 2
   (`logs/S17_topicos_dominio0.txt`, `logs/S17_topicos_dominio2.txt`). Es una prueba de
   imposibilidad: no existe el canal por el que un mensaje podría cruzar.

   Hay que listar con `--no-daemon --spin-time 8`. Con la ventana de descubrimiento por defecto
   (~1 s) el listado sale **incompleto y asimétrico** —una toma dio 6 tópicos y otra 50, con la
   pila entera arriba en ambos casos—, lo que parece un nodo faltante y no lo es.
2. `ros2 topic info /robot1/cmd_vel --verbose`: **una sola suscripción**,
   `gazebo_ros_deepracer_drive_robot1`, en el espacio `/robot1`. Los cuatro publicadores son el
   propio Nav2 de robot1 (`controller_server`, `behavior_server`), todos dentro de `/robot1`.
   Ver `logs/S17_aislamiento_mando.txt`.
3. `pgrep -a gzserver`: dos procesos independientes (PID 11680 y 12375).
4. Comprobación visual: al comandar `/robot1/cmd_vel` en el dominio 0, el vehículo de robot2 **no
   se mueve** en su visor.

**Alcance de lo que esto demuestra.** El aislamiento está garantizado por construcción —dominios
ROS y servidores de Gazebo separados—, así que estas pruebas verifican que la construcción es la
que se cree, no descubren un aislamiento inesperado. Los dos robots no comparten espacio físico:
es una limitación declarada del alcance (§8 de `CONTRATO_INTERFACES.md`), no un resultado.

## Hallazgo colateral nº4 — abierto

**Una lectura de `/odom` reportó un desplazamiento que no ocurrió.** Midiendo el aislamiento con
`ros2 topic echo /robot2/odom` a través del daemon, robot2 informó 4,51 m de avance mientras
permanecía inmóvil en su visor. Lo leído era la posición de robot1 desplazada 2,0 m en `y`, que es
exactamente el offset de spawn de robot2:

```
robot2_después − robot1_después = (−0,001 · 2,016)
robot2_antes   − robot1_antes   = ( 0,007 · 1,988)
```

No afecta a H1 —el aislamiento se demuestra por los cuatro puntos anteriores, ninguno de los cuales
depende de `/odom`—, pero **sí bloquea el objetivo 4**: las cuatro métricas (tiempo de respuesta,
tiempo de asignación, tasa de éxito, continuidad entre niveles) se calculan sobre odometría. Antes
de instrumentar OE4 hay que establecer si la causa es el daemon de ROS 2 sirviendo datos de otro
dominio o algo en la publicación de `/odom` bajo espacio de nombres. Mientras tanto, **leer con
`--no-daemon`**.

## Hallazgo colateral nº5 — abierto

**Los vehículos se desvían con `angular.z = 0`.** Bajo un comando puramente lineal, el desplazamiento
resultante no es paralelo al eje del pasillo: se midieron desviaciones de 9,5°, 15° y ~18° en
distintas corridas. Puede ser que las articulaciones de dirección no nazcan en cero, o un sesgo del
plugin Ackermann; también puede ser simplemente la orientación en que Nav2 dejó al vehículo al
terminar el objetivo anterior. **No está determinado.** Importa por lo mismo que el nº4: falsea
cualquier medida de trayectoria de OE4.

## Criterio de cierre

**Cumplido (2026-08-14).** Dos robots con pila Nav2 completa, cada uno bajo su namespace, alcanzan
objetivos de navegación simultáneamente, a tiempo real, con desplazamiento verificado contra
`/odom`, y sin ningún canal de mando compartido. Con namespace vacío nada cambia respecto al
comportamiento anterior.

Quedan abiertos los hallazgos nº1, nº4 y nº5, todos ellos condiciones previas para instrumentar el
objetivo 4, ninguno de ellos condición de H1.

## Cómo refutar este resultado

```
ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1
ros2 param get /robot1/global_costmap/global_costmap robot_base_frame
ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0}, orientation: {w: 1.0}}}}"
```

Si el parámetro devuelve `base_link` sin prefijo, el anidado del YAML no está funcionando. Si el
objetivo no termina en `SUCCEEDED` o el log muestra `Invalid frame ID`, este documento está
equivocado.
