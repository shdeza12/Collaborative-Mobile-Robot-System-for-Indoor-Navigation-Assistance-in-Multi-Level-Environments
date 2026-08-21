# Spike de hardware, preguntas 1 y 2 — el LiDAR real y el mando por ROS 2

**Semana 19 · 2026-08-19.** Responde las preguntas **1** y **2** del spike de S19 y añade la
comprobación en hardware que el informe documental de la pregunta 4 dejó pendiente en su §8
([`S19_spike_p4_humble_jazzy.md`](S19_spike_p4_humble_jazzy.md)).

Las dos preguntas se responden con **un solo** vehículo, así que el riesgo **R11** —un DeepRacer en
intervención técnica— no las bloquea. Vehículo usado: `amss-ez9n`, la tarjeta de cómputo original
del DeepRacer con Ubuntu Server 24.04 y ROS 2 Jazzy (`deepracer-custom-car`). Portátil de
desarrollo: Ubuntu 22.04 con ROS 2 Humble, `192.168.0.101`; vehículo, `192.168.0.100`.

---

## 1. Pregunta 1 — ¿el LiDAR real publica un `/scan` usable, y hasta qué distancia de verdad?

### 1.1 Por qué no vale leer `range_max`

La respuesta fácil sería mirar el campo `range_max` del mensaje. No sirve: ese campo es un filtro
que el driver copia de su YAML, no una medida. El YDLidar G4 declara **16 m** en el mensaje
mientras su propio YAML dice **64 m**. Ninguno de los dos números se obtuvo midiendo nada.

### 1.2 Dos métodos descartados, y por qué

**Descartado: tomar el mínimo del barrido como «la pared».** El punto más cercano al sensor no es
la pared. Con el sensor a 1,00 m de un muro plano, la lectura mínima fue **0,166 m** en el sector
−153°…−147°: su propio soporte. Reportar eso como medida de la pared habría dado **83 % de error**.

**Descartado: buscar lecturas «cerca de 1 m».** Es circular. Encontrar lo que ya sabemos dónde está
no demuestra exactitud; demuestra que sabemos usar un filtro.

**Método adoptado: buscar superficies por su forma.** RANSAC secuencial extrae tres rectas por
barrido a partir de conjuntos de puntos colineales, **sin recibir nunca la distancia esperada**.
Solo al final se compara la superficie hallada con la cinta métrica. La herramienta está versionada
en [`herramientas/verificar_lidar.py`](../../herramientas/verificar_lidar.py) y su docstring
conserva los dos métodos descartados, que es la parte que no se puede reconstruir después.

Un primer intento con **una sola recta por barrido** dio 222,4 mm de desviación entre barridos. No
era ruido del sensor: RANSAC elegía una superficie distinta cada vez. Con tres rectas por barrido y
agrupación entre barridos, la misma pared bajó a 2,8 mm. El defecto estaba en el método de análisis,
no en el sensor.

### 1.3 Resultado

| Magnitud | Valor | Qué significa |
|---|---|---|
| Distancia hallada a la pared | **1,0228 m** | contra 1,000 m de cinta métrica |
| Diferencia | **+23 mm (2,3 %)** | **cota superior** del error, no el error |
| Presencia | **10 de 10 barridos** | una superficie real aparece en todos; el ruido no |
| Dispersión entre barridos | **2,8 mm** | repetibilidad |
| RMS de residuos | **2 – 11 mm** | planitud: el sensor ve recta una pared recta |

**Los 23 mm son una cota superior y no se pueden afinar con este montaje.** El LiDAR mide desde su
centro óptico, dentro de la carcasa; la cinta se apoya en un punto exterior. Esa diferencia de
origen es de orden centimétrico y no se puede separar de la exactitud sin un banco de calibración.
Decir «el sensor tiene 2,3 % de error» sería indefendible ante el jurado.

**Lo que sí queda demostrado y es lo que le importa a AMCL:** la misma pared devuelve el mismo
número, con 2,8 mm de dispersión, y las superficies planas se ven planas.

### 1.4 El URDF de simulación está mal en tres campos

| Campo | URDF de simulación | Sensor real |
|---|---|---|
| Apertura | 300° | **360°** |
| Muestras por barrido | 600 | **1328** |
| Alcance declarado | 10 m | **16 m** (útil observado en interior: ~5,9 m) |
| Frecuencia | — | 6,64 Hz |
| Resolución angular | 0,5° | **0,271°** |

No es cosmético. La campaña de OE4 compara simulación contra hardware; si el sensor simulado ve un
sector distinto con menos de la mitad de muestras, la comparación mide la diferencia de modelos
además de la del entorno. **Alinear el URDF entra en el backlog antes de instrumentar OE4.**

---

## 2. Pregunta 2 — ¿se puede comandar el vehículo desde ROS 2 sin la interfaz web?

### 2.1 Respuesta

**Sí.** Publicando `deepracer_interfaces_pkg/ServoCtrlMsg` en `/ctrl_pkg/servo_msg` con las cuatro
ruedas en el aire:

- **Dirección: proporcional.** Con consignas de 0,2 · 0,4 · 0,6 se observaron **tres posiciones
  angulares distintas**, y el signo invierte el sentido.
- **Tracción: proporcional.** Arranca alrededor de **0,42** en vacío —cota inferior, sin carga— y la
  velocidad crece progresivamente con la consigna.
- **Diferencial sano.** Con las ruedas en el aire solo giraba una. Se comprobó girando a mano una
  rueda trasera: la otra contragira. Es un diferencial abierto, no una avería.

### 2.2 Consecuencia sobre nuestro código: la cuantización es defecto nuestro, no del vehículo

Como la capa de servo resultó proporcional en los dos ejes, la cuantización que produce
`cmdvel_to_servo_node.py` es un defecto **reparable de software**. Se midió ejecutando el código
real del repositorio sobre un barrido de `/cmd_vel` —no una reimplementación— y da:

| Salida | Valores que el nodo puede emitir |
|---|---|
| Tracción | **{0 · 0,7341}** — binaria |
| Dirección | **{−1 · 0 · +1}** — ternaria |
| Umbral de arranque | **v = 0,400 m/s** |

La causa es orden de comparación en `get_mapped_throttle` y `get_mapped_steering`:
`MAX_THROTTLE_RATIO = 0.1` se evalúa **primero** y `MIN_THROTTLE_RATIO = 0.5` **último**, así que la
primera rama se lo traga todo y las dos `elif` son código muerto.

**Y esto choca de frente con Nav2.** Con `nav2_params_nav_amcl_sim_demo.yaml`:

| Parámetro de Nav2 | Velocidad | Tracción resultante |
|---|---|---|
| `desired_linear_vel` (recta) | 0,50 m/s | 0,7341 → **avanza** |
| `regulated_linear_scaling_min_speed` (curva) | 0,25 m/s | 0 → **no se mueve** |
| `min_approach_linear_velocity` (llegada) | 0,05 m/s | 0 → **no se mueve** |

El vehículo real se detendría **en cada curva** y **antes de cada meta**, sin dar error. Es
exactamente el patrón de fallo silencioso que este proyecto ya pagó tres veces.

### 2.3 La cadena de tópicos no está conectada

`servo_pkg` se suscribe a `/ctrl_pkg/servo_msg`. El launch de nuestro nodo lleva
`namespace='cmdvel_to_servo_pkg'`, así que publica en **`/cmdvel_to_servo_pkg/servo_msg`**. Nadie
escucha ahí. La cadena `/cmd_vel` → servo está rota en un punto que no tiene nada que ver con la
conversión. Se detectó leyendo el código, sin gastar sesión de hardware en ello.

### 2.4 `ServoCtrlMsg` no es igual en el repositorio y en el vehículo

Comprobado el 2026-08-19 con `ros2 interface show`: la versión del vehículo añade un tercer campo,
`builtin_interfaces/Time source_stamp`, que la de este repositorio no tiene.

No estorba para lo que necesitamos —`cmdvel_to_servo_node.py` solo escribe `angle` y `throttle`, y
el campo extra queda a cero—, y por tanto **nuestro paquete se compila en el vehículo sin migrar
código**: es `ament_python` puro y sus otras dos dependencias, `rclpy` y `geometry_msgs`, no cambian.
Es la portabilidad de código fuente que afirma **D6**, aquí sin salir de una sola distribución.

**La condición es compilar contra el `deepracer_interfaces_pkg` del vehículo.** Subir el nuestro
crearía dos definiciones distintas del mismo tipo, y ese fallo sería silencioso. Es un cuarto tipo
que difiere entre los dos mundos, después de `nav2_msgs/NavigateToPose`.

### 2.5 Anomalía anotada y no perseguida

El servicio `/servo_pkg/servo_gpio` se queda colgado en `making request` y no retorna. Pero las
ruedas se movieron igualmente, o sea que el GPIO ya estaba habilitado en el arranque. Queda anotado;
no se persigue porque no bloquea nada.

---

## 3. Comprobación en hardware de la pregunta 4

El informe documental de la pregunta 4 dejó tres afirmaciones para confirmar con vehículo. Hoy se
atacó la primera y **el resultado obliga a matizarla, no a retirarla**.

### 3.1 Antes de nada, un cortafuegos

`ros2 node list` desde el portátil salía vacío mientras el `ping` funcionaba al 100 %. La causa era
**`ufw` activo en el vehículo**, que permite ICMP por defecto y deniega el resto: firma engañosa
—pings perfectos, grafo vacío— que apunta a cualquier sitio menos al cortafuegos. Se abrió por **IP
de origen** en las dos máquinas, no por rango de puertos, porque los puertos de DDS se calculan a
partir del dominio y del índice de participante y no son fijos.

*(En el camino se escribió un perfil de Fast DDS por unidifusión, `~/fastdds_unicast.xml`, sobre la
hipótesis equivocada de que el punto de acceso filtraba multidifusión. Resultó innecesario. Se
conserva porque documenta el descarte, y porque sirve de plan B si la red de la demostración sí
filtra multidifusión.)*

### 3.2 Lo que sí cruza entre Humble y Jazzy

Con el cortafuegos abierto, y con nodos lanzados a mano en las dos máquinas:

| Comprobación | Resultado |
|---|---|
| Multidifusión UDP en los dos sentidos | ✅ |
| `std_msgs/String` de Humble → Jazzy | ✅ recibido |
| `std_msgs/String` de Jazzy → Humble | ✅ recibido |
| `ros2 topic list` desde Humble ve un tópico publicado en Jazzy | ✅ |

Aparece de forma reproducible el aviso **`sequence size exceeds remaining buffer`** en el lado
Humble. No impide nada: los datos llegan íntegros. Es coherente con que el canal interno de grafo
(`rmw_dds_common`) cambiara de definición entre distribuciones, igual que cambió
`nav2_msgs/NavigateToPose`. Queda anotado como aviso cosmético con causa probable, no verificada.

### 3.3 Lo que esto **no** dice

**El veredicto de la pregunta 4 no cambia.** Que el transporte DDS cruce era la precondición más
básica; el hallazgo del informe documental es de otra capa: `nav2_msgs/NavigateToPose` tiene
distinta definición en las dos distribuciones, y hoy **no se probó ninguna acción**. Lo correcto es
decir que hoy se retiró el riesgo de que ni siquiera el transporte funcionara, y que la
incompatibilidad de la interfaz de mando sigue en pie tal como está escrita.

---

## 4. Tres hallazgos que nadie había planificado

### 4.1 Conectar el LiDAR al vehículo lo deja sin pila de control

Con el LiDAR enchufado a la tarjeta del DeepRacer, `deepracer-core` entra en bucle de reinicio y a
los cinco intentos systemd se rinde: `Start request repeated too quickly`. El vehículo queda **sin
ningún nodo de control**.

Comprobado con causa presente y causa ausente: con el sensor conectado el contador `NRestarts` sube
hasta que systemd abandona; desconectado, el servicio arranca y el contador se queda en 0.

Son tres capas apiladas:

1. **`start_ros.sh` decide que hay un RPLidar porque ve un chip CP210x**, que es el mismo puente
   USB-serie que lleva el YDLidar G4. La detección es por chip, no por sensor. El log dice
   literalmente `RPLIDAR / UART Bridge found!`, un mensaje que apunta al sitio equivocado.
2. **El ejecutable que el launch pide no existe.** `executable 'rplidar_node' not found on the
   libexec directory '/opt/ros/jazzy/lib/rplidar_ros'`. Lo instalado se llama
   **`rplidar_composition`**. El port de la comunidad dejó desalineado el nombre.
3. **Aunque el nombre coincidiera, el protocolo serie del RPLidar no es el del G4.** Corregir el
   nombre solo movería el fallo un paso más allá.

**Consecuencia operativa inmediata:** no conectar el LiDAR al vehículo hasta instalar el driver del
YDLidar para Jazzy y corregir la detección. Es trabajo nuevo, no previsto, y está en el camino
crítico de S20, que pide *«mapear el laboratorio real con el DeepRacer físico»*.

### 4.2 El tópico no es `/scan`

Bajo `deepracer-core` el LiDAR publicaría en **`/rplidar_ros/scan`**. Nav2 y `slam_toolbox` esperan
`/scan`. Hace falta remapeo, y con namespaces por robot habrá que revisarlo dos veces: es la misma
clase de defecto que costó S17 entera.

### 4.3 Los tópicos de `deepracer-core` sí salen a la red, pero hay que reiniciarlo tras tocar el cortafuegos

Durante buena parte de la sesión, el portátil no veía **ninguno** de los 19 tópicos del servicio,
mientras que un nodo lanzado a mano en el mismo vehículo sí se veía. Eso apuntaba a un aislamiento
del servicio y se llegó a dar por hallazgo. **Era falso**, y se corrige aquí porque el error importa
tanto como el resultado.

Al final de la sesión, tras varios reinicios de `deepracer-core`, el portátil pasó a listar los 19
tópicos, incluidos `/ctrl_pkg/servo_msg` y `/rplidar_ros/scan`. Lo que cambió no fue una variable
sino el **orden**: el servicio llevaba arrancado desde antes de que se abriera `ufw`, y solo tras
relanzarlo con el cortafuegos ya abierto volvió a anunciarse.

Las hipótesis que se barajaban quedan descartadas con evidencia, no por abandono:

| Hipótesis | Comprobación | Resultado |
|---|---|---|
| El servicio fija `ROS_LOCALHOST_ONLY`, `ROS_DOMAIN_ID` o `RMW_IMPLEMENTATION` | `grep` sobre `start_ros.sh` y `setup.bash`; `systemctl show -p Environment` | ❌ No aparece ninguna; `Environment=` vacío |
| El entorno del proceso las trae de otro sitio | `sudo cat /proc/<pid>/environ` sobre `servo_node` | ❌ Solo `ROS_VERSION`, `ROS_PYTHON_VERSION`, `ROS_DISTRO` y **`ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET`**, que es el valor **permisivo** de Jazzy |
| Correr como `root` aísla al servicio | Publicar un tópico como root en el vehículo y listarlo desde el portátil | ❌ Se ve sin problema |

**Regla operativa que queda:** después de tocar el cortafuegos hay que **reiniciar
`deepracer-core`**, o parecerá aislado sin estarlo. Es un fallo silencioso más de la misma familia
que el resto de este informe.

**Consecuencia de planificación, y es buena:** el vehículo **sí es alcanzable** desde otra máquina de
la red. S20 —mapear el laboratorio real— no está bloqueado por esto.

---

## 5. Backlog que deja este spike

| # | Qué | Por qué importa | Cuándo |
|---|---|---|---|
| 1 | Driver del YDLidar G4 para Jazzy, y corregir la detección de `start_ros.sh` | Sin esto el vehículo no puede usar su LiDAR **y se queda sin control al conectarlo** | Bloquea S20 |
| 2 | ~~Averiguar por qué `deepracer-core` no publica a la red~~ | **Resuelto la misma noche:** sí publica; hay que reiniciarlo tras tocar `ufw` (§4.3) | ✅ Cerrado |
| 3 | Invertir el orden de comparación en `get_mapped_throttle` y `get_mapped_steering` | El vehículo se pararía en cada curva y antes de cada meta | Antes de la demostración física |
| 4 | Resolver `/cmdvel_to_servo_pkg/servo_msg` contra `/ctrl_pkg/servo_msg` | La cadena de mando está rota | Antes de la demostración física |
| 5 | Alinear el URDF del LiDAR: 300°→360°, 600→1328, 10→16 m, 0,5°→0,271° | La campaña de OE4 compara simulación contra hardware | Antes de instrumentar OE4 |
| 6 | Remapear `/rplidar_ros/scan` → `/scan` | Nav2 y `slam_toolbox` no lo encuentran | Con el punto 1 |
| 7 | Cambiar las credenciales por defecto del vehículo | Van a llevarlo a la USTA | Antes de salir del laboratorio |
| 8 | Reserva DHCP para las dos máquinas, o servidor de descubrimiento de Fast DDS | Las IP están escritas a mano; si el router reparte otras, todo deja de funcionar sin avisar | Antes de la demostración |

---

## 6. Lo que queda por comprobar

- Un cliente de acción Humble contra un servidor `navigate_to_pose` en Jazzy. Hoy se demostró que el
  transporte cruza; **falta la acción**, que es donde el informe documental predice el fallo.
- Que Nav2 arranca en Jazzy con la configuración corregida de §3 de aquel informe.
- La **pregunta 3** del spike —latencia de ida y vuelta entre los dos vehículos— sigue supeditada a
  la reparación (**R11**) y está fuera del criterio de cierre de S19.
