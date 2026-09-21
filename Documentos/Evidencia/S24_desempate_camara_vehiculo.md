# La tarjeta sí publica imagen, pero a 160 × 120 y sin calibrar

**Fecha:** 2026-09-21 · **Cierre del Bloque 0 de [`MAPA_TRABAJO_RESTANTE.md`](../MAPA_TRABAJO_RESTANTE.md)**

## 0. La pregunta que decidía tres semanas

El §3.5 del mapa dejaba abierto **qué publica `odom → base_link`** en el vehículo real, con tres
opciones. Las dos primeras —A, marcadores AprilTag con EKF; B, odometría visual estéreo— dependen
las dos de que la tarjeta entregue imagen, y **ningún documento de este proyecto nombraba un tópico
de cámara del vehículo real**: lo medido hasta hoy era una lista de tópicos de la que solo se citaban
por nombre `/ctrl_pkg/servo_msg` y `/rplidar_ros/scan`. Que la pila de fábrica del DeepRacer incluya
un `camera_pkg` era conocimiento general de la plataforma, no evidencia propia.

El bloque se planteó como un desempate binario: si no hay imagen, A y B se caen y C —cambiar de
sitio, no de sistema— pasa de red de seguridad a plan. **La respuesta no salió binaria**, y eso es
lo que este registro documenta.

## 1. Las dos máquinas, identificadas antes de medir nada

Ambos vehículos, encendidos a la vez en la red del laboratorio:

| Carro | IP | Hostname | MAC de `mlan0` | Sistema |
|---|---|---|---|---|
| A | `192.168.0.101` | `amss-jgm9` | `80:91:33:f3:e6:ab` | Ubuntu 24.04.4 LTS · 6.8.0-117-lowlatency · ROS 2 Jazzy |
| B | `192.168.0.102` | `amss-ez9n` | `80:91:33:ed:8c:f3` | Ubuntu 24.04.4 LTS · 6.8.0-117-lowlatency · ROS 2 Jazzy |

**Los dos comparten `machine-id`** (`8073d1af74f2489e8cdad97c5020b886`) y las MAC de `usb0`/`usb1`
(`12:34:56:78:90:11` y `…:21`). Son clones de la misma imagen, así que **el único identificador
fiable en terminal es el hostname**; la IP la reparte el DHCP y ya cambió respecto al 2026-09-07.
No se ha comprobado que la identidad compartida cause daño —Fast DDS deriva la identidad de sus
participantes principalmente de la MAC, y esas sí difieren— pero queda anotada como primera
hipótesis a revisar si el descubrimiento entre vehículos falla de forma inexplicable.

**Batería medida, no supuesta** (§4.5 de [`HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](../HOJA_CAMPO_SEGUNDO_DEEPRACER.md)):
`level = 7` en los dos, frente al 10 que dio uno recién cargado el 2026-09-08. Suficiente para esta
sesión, que no mueve motores ni exige LiDAR.

Esa cifra se midió dos veces, y la segunda vez por un motivo que aparece en el §4: con los dos
carros encendidos en el mismo dominio hay **dos servidores del servicio `/i2c_pkg/battery_level`**,
así que el cliente pudo haber respondido desde el mismo vehículo las dos veces. La repetición se
hizo con descubrimiento confinado a la tarjeta:

```
ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; ros2 daemon stop; ros2 service call /i2c_pkg/battery_level …
```

**`level = 7` en los dos otra vez**, ahora atribuible con certeza a cada carro. La lectura ambigua
resultó correcta, pero eso se sabe *después* de desambiguarla, no antes.

Al terminar la sesión, la lectura de cierre que pide la hoja de campo: **`level = 7` en los dos,
igual que al empezar.** La sesión no gastó carga medible, lo que es coherente con que no movió
motores ni encendió el LiDAR.

## 2. El grafo, estabilizado antes de preguntarle

`ros2 topic list` **no es determinista** para un proceso recién nacido: el 2026-09-01 dio 2, 10 y 17
contra un grafo que no cambiaba. Preguntar por la cámara sin estabilizar el demonio arriesgaba un
**falso negativo** que habría decidido tres semanas en falso.

Con el demonio levantado, tres lecturas seguidas por carro: **21, 21, 21 en los dos.** Estable, que
es el criterio; pero **21 y no los 22** documentados en [`GUIA_PASADA_MAPEO.md`](../GUIA_PASADA_MAPEO.md)
§2.5. La lista de hoy no contiene `/camera_pkg/video_mjpeg`, que el Bloque 0 preveía encontrar; no
se ha establecido si ese es el tópico que falta respecto a la medición anterior, y no se supone.

Las dos listas de 21 salen **idénticas entre carros**, campo a campo — y el §4 explica por qué eso
no significa lo que parece.

## 3. Qué hay de cámara

Tres tópicos, en los dos vehículos:

```
/camera_pkg/camera_info
/camera_pkg/display_mjpeg
/camera_pkg/display_mjpeg/compressed
```

**`camera_info` viene hueco.** No es que traiga una calibración mala: no trae ninguna.

| Campo | Valor |
|---|---|
| `height` / `width` | `0` / `0` |
| `distortion_model` | `''` |
| `d` | `[]` |
| `k`, `r`, `p` | todo `0.0` |
| `frame_id` | `camera` |

Lo único con contenido es el `header` con su marca de tiempo. **Sin intrínsecos, AprilTag detecta el
marcador en píxeles pero no puede devolver pose métrica**, que es justamente lo que la opción A
necesita.

**`display_mjpeg` es `sensor_msgs/msg/Image` de 160 × 120, `rgb8`, `step` 480.** Esa resolución es
insuficiente para marcadores a distancia útil: un tag solo da pose fiable si ocupa decenas de
píxeles de lado, y a 160 × 120 un marcador de tamaño razonable a dos metros cae en el orden de media
docena.

**Pero 160 × 120 no es el techo del sensor.** `v4l2-ctl` sobre `/dev/video0` —hay ocho nodos,
`/dev/video0` a `/dev/video7`— enumera en MJPG, todos de 1 a 30 fps:

| Resoluciones disponibles |
|---|
| 160×96 · 160×120 · 176×128 · 320×160 · 320×192 · 320×240 · 432×240 |
| **624×352 · 640×320 · 640×360 · 640×480** |
| **960×720 · 1280×640** |

Los 160 × 120 son **una elección de la pila de AWS** —coinciden con el tamaño de entrada del modelo
de inferencia del DeepRacer—, no una limitación del hardware.

**Los ocho `/dev/video*` son dos cámaras, no ocho.** `v4l2-ctl --list-devices` las agrupa por
puerto USB físico:

| Cámara | Ruta USB | Nodos |
|---|---|---|
| Condor | `usb-…15.0-6` | `/dev/video0` … `/dev/video3` |
| Condor | `usb-…15.0-4` | `/dev/video4` … `/dev/video7` |

Cuatro nodos por cámara es el reparto normal de UVC en kernels recientes —captura y metadatos por
separado—, no cuatro sensores. **Las dos cámaras del par estéreo están, y las dos son el mismo
modelo**, que es la condición para calibrarlas con el mismo procedimiento. Cuál de las dos ruta USB
es la izquierda y cuál la derecha no se ha establecido: exige taparlas de una en una y mirar la
imagen.

## 4. Un hallazgo colateral que importa más que la cámara

`ros2 topic info /camera_pkg/display_mjpeg` devolvió **`Publisher count: 2`**.

Hay una cámara por carro. Dos publicadores en un tópico significa que **los dos vehículos están
publicando en el mismo nombre absoluto y se ven entre sí**: comparten dominio DDS y la pila de
fábrica no usa espacios de nombres. Es la primera evidencia **en hardware** de un problema que el
mapa listaba como pieza 3 de la cadena y anotaba como «nunca ejercitado fuera de simulación».

**No hay que deducirlo: ROS lo dice.** `ros2 node list` encabeza su salida con

```
WARNING: Be aware that there are nodes in the graph that share an exact name,
this can have unintended side effects.
```

y a continuación lista **cada nodo de `deepracer-core` repetido**, sin excepción. No es solo que
los tópicos colisionen: colisionan los nodos, y con ellos sus servicios y sus parámetros.

Tres consecuencias:

1. **La frecuencia medida hoy no caracteriza al sensor.** `ros2 topic hz` dio una media creciente en
   torno a 53 Hz, pero con dos publicadores esa cifra es la suma de las dos cámaras. **No se anota
   como tasa de fotogramas del vehículo.**
2. **La salida no es separar dominios.** Se evaluó y se descarta: el 2026-08-30 el proyecto invirtió
   esa decisión y puso los dos robots en el dominio 0 precisamente porque dominios distintos aíslan
   de verdad, y ese aislamiento impediría que el coordinador hable con los dos vehículos a la vez,
   que es el núcleo del sistema colaborativo. La separación es por **namespaces**, y los tópicos de
   `deepracer-core` son absolutos, así que exigen remapeo explícito.
3. **Cualquier medida tomada con los dos encendidos es ambigua mientras no se aísle.** Vale para el
   servicio de batería —que por eso se repitió— y valdrá para todo lo que venga. El aislamiento no
   exige apagar un carro: `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` confina el descubrimiento a la
   propia tarjeta. **Es el procedimiento por defecto para medir en adelante**, hasta que los
   namespaces estén puestos.

   Con una trampa que costó una medición: **no basta con parar el demonio, hay que volver a
   arrancarlo** ya con la variable exportada —la hereda—. Parándolo y nada más, `ros2 node list`
   devolvió **4 nodos**, mientras `ros2 param list`, unos segundos después en la misma sesión,
   listaba **veinte**. Es la subcuenta sin demonio que `GUIA_PASADA_MAPEO.md` §2.5 ya tenía tabulada
   (2, 10 y 17 contra un grafo quieto). Con `ros2 daemon stop; ros2 daemon start` bajo la variable,
   la misma pregunta dio **21 nodos**, que sí es la cuenta de un vehículo solo.

   Y una segunda trampa, de shell y no de ROS: **`sudo -i` no respeta el entrecomillado**. Dos
   comandos de esta sesión perdieron sus variables —un `for n in $(…)` que quedó vacío y cinco
   `ros2 param get` que llegaron sin el segundo argumento— porque `sudo -i` rearma la orden para el
   shell de login. Con `sudo -i`, los comandos se escriben repetidos: nada de variables ni de
   sustitución de comandos.

Y una relectura hacia atrás, dentro de esta misma sesión: **las dos listas de 21 tópicos no eran
«idénticas entre carros» en el sentido que sugiere el §2.** Eran idénticas porque son *la misma
lista* —la unión del grafo, vista dos veces—. Lo que la sesión midió no fue el grafo de cada
vehículo, sino el grafo común. Que no aparezca `/camera_pkg/video_mjpeg` sigue siendo cierto; que
cada carro publique 21 tópicos propios, no se ha comprobado.

## 5. El fuente del arranque, que responde lo que los parámetros solo insinuaban

`width` y `height` existen como parámetros, pero `ros2 param describe` los da **`Read only: true`**,
y a `camera_info_url` también. Ninguno se cambia en caliente: los tres se fijan al nacer el nodo. La
pregunta pasó entonces a ser *dónde nace*, y la cadena es corta:

```
deepracer-core.service → ExecStart=/opt/aws/deepracer/start_ros.sh
                       → ros2 launch deepracer_launcher deepracer_launcher.py … camera_mode:=modern
```

`camera_mode` lo decide el propio script con un condicional sobre el distro: `legacy` si Foxy,
**`modern` en cualquier otro caso**. La tarjeta corre Jazzy, así que siempre entra por `modern`.
Eso confirma en el fuente lo que el juego de parámetros solo sugería: **el nodo de cámara no es el
`camera_pkg` de fábrica, sino `camera_ros`** —basado en libcamera—, con `camera_pkg` conservado
únicamente como namespace.

Dentro del launch, la resolución es dos líneas:

```python
resize_images = str2bool(LaunchConfiguration('camera_resize').perform(context))
resolution = resize_images and [160, 120] or [640, 480]
```

**Los 160 × 120 son el valor por defecto de un argumento de launch**, `camera_resize:="True"`. No
hay nada que reescribir: `camera_resize:=False` da 640 × 480.

El fuente explica además tres cosas que llevábamos la sesión entera suponiendo:

| Observación | Explicación en el fuente |
|---|---|
| `camera_info` en ceros | `camera_params` **nunca incluye `camera_info_url`**; `camera_ros` publica el mensaje vacío mientras no reciba un YAML |
| Falta `/camera_pkg/video_mjpeg` | la rama `modern` remapea `image_raw` a `display_mjpeg`; `video_mjpeg` es nombre de la rama `legacy`, que en Jazzy no se toma nunca |
| `camera` sale «Parameter not set» | solo se fija dentro del `try` de `libcamera`; que no esté puesto **prueba que ese bloque no se ejecutó**, y por tanto que hoy no se elige cuál de las dos cámaras usa el nodo |

## 6. Qué decide todo esto sobre el §3.5

**A no se cae, y C no pasa a ser el plan.** A sigue sumando trabajo que el mapa no contemplaba,
pero ya no en bloque: cada pieza tiene precio distinto y los tres precios están medidos.

| Tarea | Cómo entra | Coste |
|---|---|---|
| Publicar a 640 × 480 | argumento `camera_resize:=False` | una palabra en `start_ros.sh` |
| Instalar la calibración | `camera_info_url` **no es argumento**: hay que añadirlo a `camera_params` | editar `deepracer_launcher.py` en las dos tarjetas |
| Calibración intrínseca de las dos cámaras | procedimiento estándar `camera_calibration` → YAML | una sesión de tablero por cámara |
| Elegir cuál de las dos cámaras | argumento `camera_index` | **existe pero hoy no funciona**; hay que arreglar la detección libcamera primero |

Y un obstáculo que aparece aquí por primera vez identificado en el fuente, no como sospecha. Los
remapeos del nodo de cámara son **absolutos**:

```python
remappings=[('/camera_pkg/camera/camera_info', '/camera_pkg/camera_info'),
            ('/camera_pkg/camera/image_raw',   '/camera_pkg/display_mjpeg'), …]
```

Envolver el launch en un namespace de robot **no los mueve**: los dos carros seguirían colisionando.
La pieza 3 del §2.2 no se resuelve con `push_ros_namespace`; exige tocar estos remapeos o lanzar
`camera_ros` por nuestra cuenta.

## 6 bis. Lo que queda abierto, dicho como tal

- **Por qué falló la detección de libcamera** en el contexto del launch, que es lo que bloquea
  `camera_index` y con él la elección de cámara del par estéreo.
- **Cuál de las dos cámaras es la izquierda y cuál la derecha.** Se sabe que son dos y que son el
  mismo modelo; el reparto entre las dos rutas USB, no.
- **La tasa real de fotogramas de una sola cámara**, y **la lista de tópicos propia de cada carro**.
  Las dos exigen lo mismo: repetir la medición aislada, con el demonio rearrancado.
- **Si `camera_resize:=False` sobrevive a un reinicio del servicio** sin romper la inferencia, que
  espera 160 × 120 a la entrada del modelo. No se probó: exige reiniciar `deepracer-core`, y esta
  sesión era de solo lectura a propósito.

## 7. Trazabilidad

| Afirmación | De dónde sale |
|---|---|
| Identidad y sistema de los dos carros | `lsb_release -ds; uname -r; ls /opt/ros/` por SSH, 2026-09-21 |
| `machine-id` y MAC compartidas | `cat /etc/machine-id; ip -br link` en los dos |
| `level = 7` en ambos | `ros2 service call /i2c_pkg/battery_level` con `sudo -i` |
| `level = 7` **atribuible**, repetición aislada | lo mismo con `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` tras `ros2 daemon stop` |
| 21 tópicos estables, listas idénticas | `ros2 daemon start` y tres `ros2 topic list \| wc -l` por carro |
| `camera_info` en ceros | `ros2 topic echo /camera_pkg/camera_info --once` |
| 160 × 120, `rgb8`, dos publicadores | `ros2 topic info` y `ros2 topic echo --no-arr` de `/camera_pkg/display_mjpeg` |
| Resoluciones del sensor | `v4l2-ctl --list-formats-ext -d /dev/video0` |
| Dos cámaras Condor, cuatro nodos cada una | `v4l2-ctl --list-devices`, agrupado por ruta USB |
| Nodos duplicados y aviso de ROS | `ros2 node list` con los dos carros encendidos |
| 4 nodos sin demonio vs. 21 con demonio rearrancado | dos corridas de `ros2 node list` bajo `LOCALHOST`, la segunda con `ros2 daemon start` |
| `width`/`height`/`camera_info_url` de solo lectura | `ros2 param describe /camera_pkg/camera …` |
| Cadena de arranque hasta el launch | `systemctl cat deepracer-core.service` y `cat /opt/aws/deepracer/start_ros.sh` |
| `camera_resize`, remapeos absolutos, bloque libcamera | `deepracer_launcher.py`, hallado con `find /opt -name 'deepracer_launcher.py'` |
| Batería de cierre `level = 7` en ambos | mismo servicio aislado, al terminar la sesión |
| Dominio 0 y separación por namespaces | [`GUIA_EJECUCION.md`](../GUIA_EJECUCION.md) §«RViz de cada uno», decisión del 2026-08-30 |
| Indeterminismo de `topic list` sin demonio | [`GUIA_PASADA_MAPEO.md`](../GUIA_PASADA_MAPEO.md) §2.5, tabla de 2, 10 y 17 |
