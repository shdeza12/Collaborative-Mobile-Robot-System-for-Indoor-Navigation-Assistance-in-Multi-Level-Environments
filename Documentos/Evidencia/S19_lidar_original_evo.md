# El LiDAR original del kit Evo — el bloqueante de S20 era un nombre mal escrito

**Semana 19 · 2026-08-21.** Sesión sobre el vehículo físico `amss-ez9n` (tarjeta de cómputo
original del DeepRacer, Ubuntu Server 24.04, ROS 2 Jazzy) con el **kit Evo completo y original
montado**: LiDAR de fábrica y las dos cámaras. Acceso por `ssh deepracer@192.168.0.100`.

Corrige y acota lo que el spike de las preguntas 1 y 2
([`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md)) dejó escrito dos días antes. **No lo
contradice:** mide otro sensor.

> **Dato de red que conviene registrar:** el portátil de desarrollo es hoy `192.168.0.102`. El
> 19-ago era `192.168.0.101`. Las direcciones están escritas a mano en varios sitios y ya cambiaron
> una vez en dos días — es exactamente el punto 8 del backlog del spike, y acaba de dejar de ser
> hipotético.

---

## 1. El sensor no es el mismo que el del 19-ago

El informe del 19-ago identifica un **YDLidar G4**. El de hoy es un **RPLIDAR A1M8-R5**. No hay
error en ninguno de los dos: **son sensores distintos**. El del 19-ago era una unidad **externa**;
la de hoy es la que viene con el kit Evo, recuperada junto con la cobertura y la cámara estéreo
doble.

Esto importa más de lo que parece, porque **cada conclusión de aquel informe sobre el LiDAR hay que
releerla preguntando de qué sensor hablaba**. La §6 de este documento lo hace.

---

## 2. Línea base: con el LiDAR desconectado, el vehículo está sano

Se establece primero, y a propósito. Con el sensor conectado el servicio de control cae, y entonces
*todo* parece averiado; sin una línea base no hay forma de distinguir un fallo real del efecto de la
caída.

| Comprobación | Resultado |
|---|---|
| `systemctl restart deepracer-core` → `systemctl status` | `Active: active (running)` |
| `systemctl show deepracer-core -p NRestarts` | `NRestarts=0` |
| Carga del servicio | `Tasks: 292`, `Memory: 496.5M` |
| Argumento del launcher | `rplidar:=False` |
| `ros2 topic list` | **19 tópicos** |

El `rplidar:=False` es útil como instrumento: es `start_ros.sh` diciendo por escrito que no detectó
sensor. Al conectarlo debe pasar a `True`, y ahí empieza el problema.

### 2.1 Dos falsos positivos que hay que conocer antes de creerse nada

**`/rplidar_ros/scan` aparece en `ros2 topic list` con el sensor desenchufado.** No es que lo
reconozca: `ros2 topic list` incluye los tópicos que alguien solo *escucha*, y `sensor_fusion_pkg`
está suscrito ahí. Quien compruebe «¿está el tópico?» tras conectar el LiDAR obtendrá un sí que no
significa nada. La comprobación que no miente es `ros2 topic info /rplidar_ros/scan --verbose` y
leer **`Publisher count`**.

**`ros2 topic pub` sobre `/ctrl_pkg/servo_msg` respondió `The passed message type is invalid`, y no
era el hardware.** Era la terminal: tenía `/opt/ros/jazzy` sourceado pero no la capa de AWS, así que
`deepracer_interfaces_pkg` no existía para `ros2`. Se resuelve sourceando lo que sourcea el propio
servicio, que se averigua con `grep -n source /opt/aws/deepracer/start_ros.sh`. Se registra porque
el síntoma —«el vehículo no acepta comandos»— apunta al sitio equivocado.

---

## 3. Con el LiDAR conectado el fallo se reproduce, y el servicio llega a mentir

`journalctl -u deepracer-core`, cinco veces seguidas:

```
start_ros.sh[3698]: RPLIDAR / UART Bridge found!
start_ros.sh[3732]: [ERROR] [launch]: Caught exception in launch (see debug for traceback):
                    executable 'rplidar_node' not found on the libexec directory
                    '/opt/ros/jazzy/lib/rplidar_ros'
```

`NRestarts` subió 1 → 3 → 4 y systemd terminó dejándolo en `failed`. El vehículo queda **sin ningún
nodo de control**, igual que el 19-ago.

**Hay un instante que engaña y conviene documentar.** A las 18:48:45 UTC el servicio llegó a
`Active: active (running)`, con `rplidar:=True` en la línea del launcher. Pero:

| | Arranque sano (§2) | El «running» de 18:48:45 |
|---|---|---|
| `Tasks` | 292 | **109** |
| `Memory` | 496,5 MB | **147,9 MB** |
| `ros2 topic list` | 19 tópicos | **2** — solo `/parameter_events` y `/rosout` |

Es decir: systemd lo daba por vivo mientras el `ros2 launch` de dentro ya había muerto. **Un
`is-active` que devuelve `active` no prueba que el grafo ROS exista.** Quien mire solo el estado del
servicio concluirá que arrancó. Es la misma familia de fallo silencioso que ya costó
`initial_pose`, `/scan` bajo namespace y `--set-state start`.

---

## 4. Causa raíz: una capa, no tres

El spike del 19-ago describió el fallo como **tres capas apiladas**. Sobre el sensor de fábrica, dos
de las tres dejan de ser fallos:

| Capa según el spike | Sobre el A1M8-R5 |
|---|---|
| 1. `start_ros.sh` concluye «hay un RPLidar» porque ve un chip CP210x — detección por puente USB-serie, no por sensor | **Está acertando.** Sí hay un RPLidar. El razonamiento sigue siendo frágil, pero el resultado es correcto |
| 2. El launch pide `rplidar_node`; lo instalado se llama `rplidar_composition` | **Es el fallo, y es el único** |
| 3. Aunque el nombre coincidiera, el protocolo serie del RPLidar no es el del G4 | **No aplica.** `rplidar_ros` es precisamente el driver de este sensor |

Comprobado con una sola orden:

```
$ ls /opt/ros/jazzy/lib/rplidar_ros/
rplidar_composition
```

El binario está instalado y funciona; lo que no existe es el nombre que el launch invoca. El port de
la comunidad dejó desalineados el launch y el ejecutable.

**Consecuencia de planificación.** El punto 1 del backlog del spike decía *«Driver del YDLidar G4
para Jazzy… Bloquea S20»*. Sobre este montaje **no hay driver que instalar**. S20 —mapear el
laboratorio real con el DeepRacer físico— deja de estar bloqueado por el LiDAR.

---

## 5. Identidad y parámetros del sensor, medidos

Driver lanzado a mano, **sin modificar nada en disco**, para separar la demostración de la
reparación:

```
ros2 run rplidar_ros rplidar_composition --ros-args \
  -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=115200 \
  -p frame_id:=laser -p angle_compensate:=true
```

Lo que el propio sensor declara al arrancar:

```
SDK Version: '1.12.0'
RPLIDAR S/N: 77F69A87C5E392D3A5E49EF0E7233D65
Firmware Ver: 1.25      Hardware Rev: 5
RPLidar health status : '0'
current scan mode: Express, max_distance: 12.0 m, Point number: 4.0K,
                   angle_compensate: 1, flip_x_axis 0
```

`health status: '0'` es sano. `Hardware Rev: 5` y 12,0 m corresponden al **RPLIDAR A1M8-R5**, el
sensor de fábrica del Evo.

Y lo que publica de verdad, sobre `/scan`:

| Campo | Valor medido | Traducción |
|---|---|---|
| `angle_min` | −3,1241393089 rad | −179,0° |
| `angle_max` | +3,1415927410 rad | +180,0° |
| Apertura | — | **360°** |
| `angle_increment` | 0,0174532924 rad | **1,000°** exacto |
| Muestras por barrido | — | **360** |
| `range_min` … `range_max` | 0,15 … **12,0 m** | |
| `scan_time` | 0,143643 s | 6,96 Hz |
| Frecuencia observada | **6,80 Hz** | `min 0,144 s · max 0,152 s · σ 0,0039 s · ventana 50` |

> **`ros2 topic echo` necesita `--full-length`.** Sin él recorta los arreglos a 128 elementos y
> devuelve un barrido falso. Ya invalidó un análisis anterior de este proyecto, en el que las
> direcciones reportadas correspondían a un sector del barrido distinto del que se creía.

---

## 6. El punto 5 del backlog apuntaba al sensor equivocado

Aquel punto pedía alinear el URDF de simulación a **1328 muestras, 16 m y 0,271°**. Esos son los
números del **G4 externo**. Contra el sensor que el vehículo lleva de verdad, la corrección es otra:

| Campo | URDF de simulación | A1M8-R5 real | |
|---|---|---|---|
| Apertura | 300° | **360°** | corregir |
| Alcance | 10 m | **12 m** | corregir |
| Muestras por barrido | 600 | **360** | corregir — **la simulación ve más rayos que el carro** |
| Resolución angular | 0,5° | **1,0°** | corregir |

El tercero es el que menos se espera: **el modelo simulado es más rico que el hardware**, no más
pobre. Si la campaña de OE4 se corriera así, parte de la diferencia medida entre simulación y
realidad sería la diferencia entre los dos modelos de sensor, no entre los dos entornos.

**Decisión abierta, que se registra sin resolver:** los 360 rayos son una elección del *driver*, no
un límite del sensor. Con `angle_compensate:=true` reparte las muestras crudas en una rejilla fija
de 360 casillas de 1°; en modo Express a 4 K muestras por segundo y 6,80 Hz, el sensor entrega unos
**588 puntos por vuelta**, de los que se publican 360. Caben dos salidas —bajar la simulación a 360
rayos, o subir la resolución del driver real— y las dos son defendibles. Lo que no es defendible es
elegir sin advertirlo.

---

## 7. Las dos cámaras: enumeradas, no verificadas

`lsusb` muestra **dos** dispositivos `29fe:4d53 GEO Semi Condor` (bus 001, dispositivos 006 y 011).
A nivel USB el estéreo del Evo está completo.

**No se verificó a nivel ROS, y no se afirma.** En el arranque sano corría un **único**
`camera_node` (`camera_ros/camera_node`, con `camera_mode:=modern`) publicando un solo flujo,
`/camera_pkg/display_mjpeg`. Queda por comprobar si el segundo ojo viaja dentro de
`/sensor_fusion_pkg/sensor_msg` o si sencillamente no se está usando. Entra en el backlog.

---

## 8. Una predicción fallida, y por qué se deja escrita

Antes de medir se predijo, a partir de los 4 K puntos por segundo del modo Express, **unas 720
muestras por barrido con `angle_increment` cerca de 0,5°**. Salieron **360 a 1,000°**.

El error estuvo en razonar desde la tasa de muestreo del sensor e ignorar que `angle_compensate`
impone la rejilla de salida. Se registra porque la predicción es lo que hizo interpretable el
resultado: sin ella, 360 rayos habrían pasado por dato sin más, y la brecha entre los 588 puntos
crudos y los 360 publicados —que es la decisión abierta de la §6— no se habría notado.

---

## 9. Estado en que queda el vehículo

- **`deepracer-core` queda en `failed`** mientras el LiDAR esté conectado.
- Se recupera desenchufando el sensor y `sudo systemctl restart deepracer-core`.
- **El arreglo permanente se aplaza a propósito.** Está identificado y es de una línea, pero
  modifica ficheros del sistema en hardware compartido. Hay dos formas y **no son equivalentes**:
  un enlace simbólico `rplidar_node` → `rplidar_composition` en `/opt/ros/jazzy/lib/rplidar_ros/`
  (reversible con un `rm`, y sobrevive a una actualización del software de AWS), o editar el launch
  bajo `/opt/aws/deepracer/` (más honesto sobre dónde está el defecto, pero una actualización lo
  pisa). Se aplique la que se aplique, hay que dejar registrado que es un parche sobre un defecto
  del port de la comunidad, no una configuración del proyecto.

---

## 10. Backlog, actualizado

| # | Estado tras esta sesión |
|---|---|
| 1 | ~~Driver del YDLidar G4 para Jazzy~~ → **reemplazado.** No falta driver. Falta corregir el nombre `rplidar_node` → `rplidar_composition`. **Deja de bloquear S20** |
| 5 | ~~Alinear el URDF a 1328 muestras, 16 m, 0,271°~~ → **rehacer** contra el A1M8-R5: 360°, 12 m, 360 muestras, 1,0° (§6) |
| 6 | Remapear `/rplidar_ros/scan` → `/scan`. Sigue vigente: el driver a mano publica en `/scan`, pero bajo `deepracer-core` el tópico es `/rplidar_ros/scan` |
| 8 | Reserva DHCP. **Sube de prioridad:** el portátil pasó de `.101` a `.102` en dos días |
| **nuevo** | Verificar a nivel ROS si se usan las dos cámaras o solo una (§7) |
| **nuevo** | Decidir y documentar la resolución del LiDAR: 360 rayos publicados contra ~588 crudos (§6) |
