# Guion de campo — Nav2 sobre el vehículo real

**Fecha de redacción:** 2026-09-24
**Qué aísla:** los peldaños 4 a 7 de la escalera de Nav2 sobre hardware —mapa,
localización, planificador y control—, subiendo uno por uno.
**Qué contesta:** si la cadena completa arranca en el carro y si el vehículo
**obedece** un destino de Nav2.

**Qué NO es esto.** No es la medida de G-2. G-2 exige error de desplazamiento
≤ 10 % sobre un recorrido conocido de ≥ 5 m, y eso se mide **empujando el carro a
mano y grabando barridos**, sin motor y sin Nav2 — está en
`GUION_RECTA_PELDANO2.md` y es independiente de este documento. Mezclar las dos
cosas en una sola salida es la forma más rápida de no poder explicar ninguna de
las dos.

---

## 0. El orden del día, y por qué es ese

| | Qué | Por qué primero |
|---|---|---|
| **1º** | La recta de G-2, empujando a mano (`GUION_RECTA_PELDANO2.md`) | Es la compuerta C-1 del viernes 2 de octubre. No necesita motor, ni Nav2, ni software nuevo: solo grabar. La probabilidad de volver con datos usables es alta y el análisis se hace en el escritorio, cuando los carros ya no están |
| **2º** | Este guion | Software escrito hoy y **nunca ejecutado contra un carro**. Puede consumir la tarde entera y no dejar nada. Vale la pena intentarlo, pero después de asegurar lo primero |

> ### La objeción que hay que resolver antes de salir: el pasillo solo no concluye nada
>
> `GUION_SALIDA_S24.md` §2.0 lo fija y no ha cambiado: si el desplazamiento sale
> corto en el pasillo hay **dos explicaciones opuestas** —que el pasillo no da
> información de avance, que es el hallazgo; o que la cadena de medida está
> rota— y con un solo sitio **no se distinguen**.
>
> El mapa del cuarto de hoy (1,60 × 0,80 m medidos contra 1,60 × 0,76 m de
> cinta, en los dos carros) valida la cadena de **SLAM**. No valida la de
> **desplazamiento de rf2o sobre 5 m**: son instrumentos distintos y el cuarto
> no da los metros.
>
> **La salida es encajonar el propio pasillo.** Se cierra un segmento de
> **6,5 m** con cajas en los dos extremos y se corren ahí los 5 m de G-2.
> Corriendo 5 m dentro de 6,5, ninguna de las dos paredes de cajas queda nunca a
> más de **5,5 m**, que es el criterio de «superficie encarada a menos de 6 m por
> delante y por detrás». Es la misma geometría de la referencia aceptada —caja
> cerrada de 7,70 m, 13,8 %—.
>
> **Y esto hace algo más que dar un control: desatasca el §6.1 del acta.** Allí
> la disyuntiva era «cambiar el sitio con la medición como justificación, o
> aceptar correr donde está medido que el estimador falla», y nada de la etapa 3
> corre hasta que eso esté por escrito. Encajonar es una tercera vía que el acta
> no contempló: **el mismo pasillo real que exige D3**, con el defecto medido
> corregido por construcción. Eso es lo que se lleva a los directores.
>
> **Y el sitio no se decide discutiendo, se decide con el número.** Sobre el bag
> ya grabado:
>
> ```
> python3 herramientas/medir_informacion_avance.py <bag> /rplidar_ros/scan
> ```
>
> Referencias ya medidas: caja cerrada de 7,70 m → **13,8 %**, mapa aceptado;
> pasillo simulado → **6,8 %**, rechazado; pasillos reales de piso 1 y 2 →
> **5,1 %** y **5,9 %**; sitio interior real (bag `sin_caparazon`) → **34,7 %**.
> Si el sitio de control sale por debajo de ~10 %, **no era un control, era un
> segundo pasillo**, y el bloque pierde su función.
>
> **Se mide sobre la primera pasada, antes de gastar las otras dos.** Si el
> segmento encajonado no sube del ~10 %, no era un control y hay que mover las
> cajas; saberlo tras una pasada cuesta cinco minutos, saberlo en el escritorio
> cuesta otra salida.
>
> **Lo que el encajonado NO arregla son los 20 m.** Esos son otro criterio —RF-13,
> umbrales M1 y M2, **no** la compuerta C-1— y cerrar solo los dos extremos de un
> pasillo de 20 m no da información en el medio: desde el punto medio cada
> extremo queda a **10 m**, por encima del `max_laser_range: 9.5` de
> `slam_toolbox` y en el borde ruidoso del sensor (12,0 m). Las cajas alumbran
> los primeros ~6 m y los últimos ~6 m; los ~8 m centrales siguen siendo el
> pasillo inobservable de siempre.

> ### Un solo carro encendido. Esto arruina la salida entera y no avisa
>
> Los dos vehículos publican `/rplidar_ros/scan` con el mismo nombre, sin
> espacio de nombres, y ninguno define `ROS_DOMAIN_ID`: los dos caen en el
> dominio 0. Con los dos encendidos, la grabación de uno recoge **también** los
> barridos del otro, intercalados, y el bag queda inservible.
>
> No es hipótesis: le pasó al bag `bag_ez9n` del 23-sep, con los dos carros
> quietos sobre la mesa y un análisis que contestó «59,1 % de movimiento» y una
> trayectoria de 11 m. Y el cruce es **intermitente**: no se puede predecir
> mirando, ni comprobar en vivo. La única defensa es apagar el otro carro, y la
> única comprobación es `comprobar_movimiento_bag.py` sobre el bag ya grabado.
>
> La nivelación de los dos carros ya está hecha (24-sep): mismo Nav2 1.3.13,
> mismo `slam_toolbox` 2.8.5, `rf2o` compilado en los dos, `~/tesis/` con los
> mismos md5. **Da igual cuál se use.** Enciende uno.
>
> **Salvo un archivo, añadido después:** `nav2_params_jazzy.yaml` (24-sep por la
> tarde). Hasta entonces el guion copiaba `nav2_params.yaml`, que es la
> configuración de **Humble** y en Jazzy no arranca: el planificador y los
> comportamientos se declaran con «::» y no con «/», y `plugin_lib_names` repite
> nodos que Jazzy ya carga, con lo que el `bt_navigator` no configura. Nunca se
> vio porque hasta hoy no se había lanzado `nav:=true` en un carro. La copia del
> §1 lo lleva ya, **a los dos carros**.

---

## 1. Antes de salir — preparación desde el escritorio

Nada de esto se hace en campo. Son cinco archivos a la tarjeta, porque
`deepracer_bringup` **no está compilado** allí y no tiene sentido compilarlo:
arrastra `gazebo_ros_pkgs`.

| | |
|---|---|
| **Objetivo** | Que `~/tesis/` del carro tenga la cadena completa. |
| **Comando** (desde la raíz del repositorio, con `NN` = 101 o 102) | `scp Robot/aws-deepracer/deepracer_description/models/urdf/deepracer_hardware.urdf Robot/aws-deepracer/deepracer_bringup/launch/nav2_hardware.launch.py Robot/aws-deepracer/deepracer_bringup/launch/hardware_description.launch.py Robot/aws-deepracer/deepracer_bringup/config/nav2_params_jazzy.yaml Robot/aws-deepracer/deepracer_bringup/config/slam_toolbox.yaml deepracer@192.168.0.NN:~/tesis/ && scp -r Robot/aws-deepracer/deepracer_bringup/behavior_trees deepracer@192.168.0.NN:~/tesis/` |
| **Esperado** | En `~/tesis/` del carro: cinco archivos y la carpeta `behavior_trees` con sus dos XML. |
| **Si falla** | `Permission denied` → la carpeta no existe: `ssh deepracer@192.168.0.NN "mkdir -p ~/tesis"`. |
| **Cierre** | **A los dos carros, en la misma sesión.** Es la regla de `CLAUDE.md`: si el segundo está apagado, queda anotado como pendiente explícito y se cierra en cuanto se encienda. |

> **Por qué a `~/tesis/` y no a `/tmp`.** `/tmp` se vacía al reiniciar. El URDF
> del 21-sep se perdió así una vez y hubo que acordarse de la invocación de
> `xacro` que lo produjo.

---

## 2. Peldaños 1–3 — TF del vehículo y odometría

**Estrenado en el escritorio el 24-sep sobre el `.101`, y pasa.** Se temía que
fuera el punto de fallo de la salida —`rf2o` se compiló el 24-sep pero nunca
había corrido en vivo en una tarjeta, solo en el portátil sobre un bag—. Corrió,
y las tres comprobaciones dieron lo esperado. Se deja el peldaño en el guion
porque hay que rehacerlo en campo, no porque siga en duda.

**Terminal 0 — limpia el grafo antes de lanzar. Esto no es ceremonia.**

```
ssh deepracer@192.168.0.NN "ps -eo user,pid,cmd | grep -E '[r]f2o|[r]obot_state_publisher'"
```

Si sale algo, es un resto de una sesión anterior. Medido el 24-sep en el `.101`:
un `robot_state_publisher` lanzado a mano a las 15:21 seguía vivo como `root`
hora y media después, con **el mismo nombre de nodo** que el que arranca este
launch. Dos nodos con un nombre es comportamiento indefinido en ROS 2, y aquí se
manifestó como `ros2 node list` mostrando uno solo. No hay ningún servicio de
`systemd` que lo levante: si aparece, lo dejó una terminal olvidada.

**Y aparece sola, porque matar el launch no lo mata.** Ocurrió dos veces
seguidas ese día: se mata el `ros2 launch` y el `robot_state_publisher` hijo
sobrevive huérfano. Hay que comprobar siempre después de cerrar, no solo antes de
abrir.

**Mátalo por PID, nunca con `pkill -f`.** `sudo -n pkill -f robot_state_publisher`
**falla**: el patrón coincide también con la propia línea de `sudo`, así que
`pkill` se mata a sí mismo antes de llegar al objetivo. Es la misma trampa ya
anotada para `pgrep -f`. Lo que funciona:

```
ssh deepracer@192.168.0.NN "sudo -n kill <PID>"
```

**Terminal 1 — deja esto corriendo:**

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'D=~deepracer/tesis; source /opt/ros/jazzy/setup.bash && source ~deepracer/nav_ws/install/setup.bash && ros2 launch \$D/nav2_hardware.launch.py urdf:=\$D/deepracer_hardware.urdf params:=\$D/nav2_params_jazzy.yaml slam_params:=\$D/slam_toolbox.yaml behavior_trees:=\$D/behavior_trees'"
```

Sin `slam:=` ni `nav:=`, o sea los dos en `false`: arranca solo
`robot_state_publisher` y `rf2o`. Es lo que se quiere.

> **Por qué `D=~deepracer/tesis` y no `$HOME/tesis`.** Bajo `sudo`, `$HOME` vale
> `/root`, y sin `sudo`, dentro de las comillas dobles del `ssh`, lo expande **el
> portátil** antes de enviarlo. `~deepracer` no depende de ninguna de las dos
> cosas: lo resuelve `bash` en el carro contra `/etc/passwd`. Va en una variable
> porque la tilde **solo se expande al principio de una palabra o tras el `=` de
> una asignación**: escrita como `urdf:=~deepracer/...` viaja literal y el launch
> recibe una ruta que no existe. El `\$` va escapado para que lo resuelva el
> carro, no el portátil.

> **Arranca como `root`, y no es opcional.** La regla dura de este carro
> —«ninguna comprobación de datos vale si quien mira no tiene el mismo dueño que
> quien publica»— **sí se aplica a `/rplidar_ros/scan`**, que publica
> `rplidar_node` como `root`. Medido en el `.101` el 24-sep, en el mismo minuto:
> como `deepracer`, **cero** scans en 20 s, un `ros2 bag record` de 198 s con **un
> solo mensaje** —el `/tf_static` retenido— y `rf2o` clavado en 115 scans con
> 19 287 avisos de `Waiting for laser_scans....`; como `root`, **7,7 Hz** y la
> cadena entera viva.
>
> La causa está en `/dev/shm`: los segmentos `fastrtps_*` son
> `-rw-r--r-- root root` y FastDDS necesita **escribir** en ellos para cerrar el
> canal de memoria compartida. El suscriptor no-root no completa el enlace y se
> queda mudo **sin un solo error** — ni en su log ni en el del driver, que sigue
> anunciando salud `0` y leyendo del puerto de verdad (`rchar` en
> `/proc/<pid>/io` crece a ~10,5 KB/s). Es el fallo más caro de diagnosticar del
> carro, porque todo *parece* sano: proceso vivo, `/dev/ttyUSB0` presente, cabeza
> del LiDAR girando y el tópico anunciado en `ros2 topic list`.
>
> Antes ese mismo día se midió 7,9 Hz como `deepracer` y se escribió aquí lo
> contrario. **Una medición de que «esta vez sí se vio» no refuta una regla de
> permisos:** el canal SHM se renegocia cada vez que reinicia cualquiera de los
> dos extremos, así que el mismo comando da distinto según cuándo arrancó el
> publicador. Vale el caso malo, y el caso malo es el silencio.

**Terminal 2 — las tres comprobaciones, en este orden:**

| # | Comando | Esperado |
|---|---|---|
| 2.1 | `ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 20 ros2 run tf2_ros tf2_echo base_link laser'"` | `Translation: [0.029, 0.000, 0.185]`, `Rotation` con RPY ≈ `[0, 0, -180]` grados |
| 2.2 | `ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 20 ros2 run tf2_ros tf2_echo odom base_link'"` | Una transformada que **existe** y cuyos números **cambian** si mueves el carro a mano |
| 2.3 | `ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 20 ros2 topic hz /odom'"` | **7–8 Hz**, el ritmo real del LiDAR, nunca 0. Medido 7,72 Hz el 24-sep |

> **Las comprobaciones también van con `sudo -n bash -c`, y con `timeout 20`.**
> Lo primero por el recuadro del §2: un observador `deepracer` no ve lo que
> publica un proceso `root`, y calla en vez de fallar. Lo segundo porque el
> descubrimiento tarda: el 24-sep, con la cadena sana, `ros2 topic hz /odom` a los
> 10 s contestó `does not appear to be published yet` y a los 20 s dio dato. **Un
> silencio a los 5 s no es evidencia de nada.**

| | |
|---|---|
| **Si 2.1 falla** | El URDF no se cargó. Mira la terminal 1: si dice `Couldn't parse parameter override rule`, alguien está usando `-p robot_description:=` en vez del launch. El valor de un `-p` se interpreta como **YAML**, y los comentarios en castellano del URDF llevan `algo: algo` y ` #` dentro, que abren un mapa y un comentario. Aislado por bisección el 24-sep. Usa el launch. |
| **Si 2.2 falla** | `rf2o` no está publicando TF. Comprueba que le llegan barridos: `ros2 topic hz /rplidar_ros/scan` debe dar **7–10 Hz**. Si da 0, el driver de fábrica no está vivo: `systemctl status deepracer-core`. Si los barridos llegan y aun así no hay TF, **para aquí y anótalo**: es el hallazgo del día y no tiene sentido subir peldaños encima. |
| **Si 2.3 da mucho menos de 20 Hz** | No es un fallo: `rf2o` no puede ir más rápido que su entrada, y el sensor da 7–10 Hz. Anota la cifra real; es dato. |
| **`Waiting for laser_scans....` en la terminal 1 no es un fallo** | Está en `CLaserOdometry2DNode.cpp:179`. El bucle corre a los 20 Hz que le pide el launch y el sensor da 7,9: ~60 % de las iteraciones no tienen barrido nuevo y avisan. Aparece intercalado con los `Laser odom [x,y,yaw]` buenos. |

> ### Da a cada comprobación 20 segundos, no 5. También hay silencios falsos
>
> La regla conocida de este carro es «el fallo es silencio, no error». Tiene una
> segunda cara que costó media hora el 24-sep: **el silencio también miente al
> revés**. Con la cadena funcionando perfectamente, `ros2 topic hz /odom` contestó
> `topic [/odom] does not appear to be published yet` y `ros2 topic echo /tf` salió
> vacío — las dos por descubrimiento lento, no por avería. Repetidas con 20 s en
> vez de 5, las dos dieron dato.
>
> Así que: **antes de declarar rota una capa, repite la medida con 20 s.** Dar por
> muerto lo que funciona cuesta la tarde igual que lo contrario.
| **Cierre** | Las tres respuestas anotadas. **Sin 2.2 no se sigue.** |

> ### La deriva en parado está medida y no amenaza a G-2
>
> Medido en el `.101` el 24-sep, con el carro **quieto** sobre el suelo y el grafo
> limpio, muestreando `/odom` cada 15 s durante dos minutos: la posición pasó de
> `x −0,007 / y −0,001` a `x −0,033 / y −0,015`. Son **3,6 cm en 105 s**, o sea
> **~0,34 mm/s**, lentos y acumulando.
>
> Puesto en el presupuesto de G-2: una corrida de 5 m empujada a ~0,33 m/s dura
> unos 15 s, y a ese ritmo la deriva aporta **medio centímetro**, el 0,1 % del
> recorrido, contra un margen del 10 %. **No es el problema.**
>
> **Y no confundir esto con lo que G-2 sí mide.** La deriva en parado dice que el
> estimador no inventa movimiento cuando no lo hay. El fallo que preocupa es el
> contrario y no se ve aquí: que con el carro **moviéndose** por un pasillo sin
> estructura encarada, rf2o registre solo una fracción del avance real —el 5,7 %
> y el 1,3 % medidos fuera de línea el 26-ago—. Eso es error de **escala**, no de
> deriva, y solo lo destapa el segmento encajonado del §0.

---

## 3. Peldaños 4–5 — el mapa en vivo

Corta la terminal 1 con `Ctrl-C` y relánzala con `slam:=true`:

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'D=~deepracer/tesis; source /opt/ros/jazzy/setup.bash && source ~deepracer/nav_ws/install/setup.bash && ros2 launch \$D/nav2_hardware.launch.py slam:=true urdf:=\$D/deepracer_hardware.urdf params:=\$D/nav2_params_jazzy.yaml slam_params:=\$D/slam_toolbox.yaml behavior_trees:=\$D/behavior_trees'"
```

**Y en cuanto arranque, actívalo a mano.** `sync_slam_toolbox_node` es en Jazzy un
nodo de **ciclo de vida** y **no se autoactiva**: se queda en `unconfigured` para
siempre, anunciando `/map` sin publicar nunca nada. El
`lifecycle_manager_navigation` del launch gestiona los cuatro servidores de Nav2 y
**no** a `slam_toolbox`. Dos llamadas, en este orden:

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && ros2 service call /slam_toolbox/change_state lifecycle_msgs/srv/ChangeState \"{transition: {id: 1}}\" && ros2 service call /slam_toolbox/change_state lifecycle_msgs/srv/ChangeState \"{transition: {id: 3}}\" && ros2 service call /slam_toolbox/get_state lifecycle_msgs/srv/GetState \"{}\"'"
```

La última debe contestar `id=3, label='active'`. Transición 1 es *configure* y 3 es
*activate*. En la terminal 1 verás `Configuring`, `Using solver plugin
solver_plugins::CeresSolver`, `CeresSolver: Using SCHUR_JACOBI preconditioner.` y
`Activating`. **Diagnóstico si dudas:** `ros2 service list | grep slam` — si solo
salen servicios de ciclo de vida y ninguno de `slam_toolbox` propio, es que sigue
sin configurar.

| | |
|---|---|
| **Objetivo** | Que exista `map → odom`, que es lo que Nav2 necesita para planificar. |
| **Comprobación** | `ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 25 ros2 topic echo /map --once --field info'"` y lo mismo con `timeout 20 ros2 run tf2_ros tf2_echo map base_link` |
| **Esperado** | `/map` publicando, y la cadena `map → odom → base_link` completa. `slam_toolbox` solo actualiza el mapa cuando el carro se ha movido **0,15 m o 0,3 rad** (`minimum_travel_distance` / `_heading`): con el carro quieto, `/map` casi no publica y **eso es correcto**. Empuja el carro un metro y vuelve a mirar. |
| **Si falla** | Por orden de probabilidad, medido el 24-sep: **(1)** `slam_toolbox` sigue en `unconfigured` — mira arriba; **(2)** nadie le llegan barridos porque el observador o el launch no van como `root` — recuadro del §2; **(3)** el tópico: el driver publica en `/rplidar_ros/scan` y `slam_toolbox` escucha `/scan` por defecto. El launch lo reescribe; se confirma mirando `Subscription count` de `ros2 topic info /rplidar_ros/scan --verbose`, que debe ser **2** (`rf2o` y `slam_toolbox`). |
| **Cierre** | `map → base_link` resuelto, y el mapa creciendo al empujar. |

> **Un detalle que no es fallo.** `max_laser_range` está en **9,5 m** y el sensor
> real alcanza **12,0 m**. Se dimensionó contra un sensor simulado de 10 m. Es
> conservador —descarta los rayos más largos, que son los más ruidosos— y no se
> toca hoy: cambiarlo a la vez que se estrena la cadena impediría saber a qué
> atribuir un resultado.

> ### Para guardar el mapa, `map_saver_cli` no sirve — añadido el 24-sep, noche
>
> Se rinde a los **2,03 s** con `Failed to spin map subscription`, y ese es su
> plazo por defecto. La causa no es el guardado sino el §3 de más arriba:
> `slam_toolbox` solo publica `/map` tras 0,15 m o 0,3 rad de movimiento, así que
> **con el vehículo detenido no llega ningún mensaje nuevo** y el suscriptor
> expira. El mapa está construido y el guardado falla igual.
>
> La vía que sí funciona es grabar `/map` en el bag y extraerlo después con
> [`extraer_mapa.py`](../herramientas/extraer_mapa.py). Además lo hace repetible:
> si hay que cambiar un umbral se cambia en el escritorio, sin repetir la salida.
> Así se recuperó el mapa de 6 m del 24-sep después de que el guardado fallara.
>
> Todo ello, junto con otros tres fallos silenciosos de la misma noche, en
> [`S24_mapeo_6m_hardware.md`](Evidencia/S24_mapeo_6m_hardware.md). Y el
> procedimiento de campo ya corregido, en
> [`GUION_CAMPO_PISO2.md`](GUION_CAMPO_PISO2.md).

---

## 4. Peldaños 6–7 — que el carro obedezca un destino

**Hasta aquí no ha habido motor. A partir de aquí sí. Aparta a todo el mundo.**

### 4.1 · El puente, que va aparte y como `root`

**Terminal 3:**

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && source ~deepracer/coordinacion_ws/install/setup.bash && ros2 run cmdvel_to_servo_pkg cmdvel_to_servo_node'"
```

> **Tiene que ser `root`.** `servo_pkg` corre como `root` y Fast DDS no empareja
> entre usuarios distintos. Como `deepracer` el nodo arranca, suscribe, **no da
> ningún error y el carro no se mueve**.

**Terminal 4 — sube la escala antes de mandar nada:**

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && source ~deepracer/coordinacion_ws/install/setup.bash && ros2 service call /set_max_speed deepracer_interfaces_pkg/srv/NavThrottleSrv \"{throttle: 0.9}\"'"
```

Esperado: `NavThrottleSrv_Response(error=0)`.

> **Por qué 0,9 y no el 0,68 de fábrica.** El umbral de arranque medido de este
> carro está **justo en 0,50**. Con `max_speed_pct` 0,68 un `linear.x` de 0,50
> sale a throttle **0,4247** y el carro no arranca — y parecería que el puente
> está roto. Con 0,90 sale **0,6327**, junto al escalón 0,60, el único cuyo
> comportamiento está medido (4,20 m en 4 s).

### 4.2 · La comprobación barata, antes de Nav2

Dos segundos de `/cmd_vel` a mano. Si esto no mueve el carro, Nav2 tampoco lo
moverá, y aquí el fallo tiene cuatro causas posibles en vez de cuarenta.

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 2 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \"{linear: {x: 0.5}, angular: {z: 0.0}}\"'"
```

| | |
|---|---|
| **Esperado** | El carro **se desplaza**, del orden de 1–2 m. La cifra exacta no es el resultado; el resultado es que se movió. |
| **Si no se mueve** | En este orden: ¿el puente corre como `root`? ¿el servicio devolvió `error=0`? ¿`ros2 topic info /cmd_vel` da `Subscription count: 1`? |
| **Si se pasa de largo** | Normal: al acabar el `timeout` el puente publica ceros y el carro **rueda por inercia**. Es parte de la distancia; anótalo así. |
| **Cierre** | Una corrida con distancia anotada. |

### 4.3 · Ahora sí, Nav2

Relanza la terminal 1 con `slam:=true nav:=true`:

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'D=~deepracer/tesis; source /opt/ros/jazzy/setup.bash && source ~deepracer/nav_ws/install/setup.bash && ros2 launch \$D/nav2_hardware.launch.py slam:=true nav:=true urdf:=\$D/deepracer_hardware.urdf params:=\$D/nav2_params_jazzy.yaml slam_params:=\$D/slam_toolbox.yaml behavior_trees:=\$D/behavior_trees'"
```

Espera a que el gestor de ciclo de vida diga `Managed nodes are active`. Por el
camino saldrá dos veces `Warnings: The first tag of the XML (<root>) should
contain the attribute [BTCPP_format="4"]`: **es esperado**. Los árboles son los
mismos de la simulación, en formato de BT.CPP 3, y BT.CPP 4 solo avisa; todos sus
nodos existen en Jazzy. Si en vez de eso sale `Failed to bring up all requested
nodes`, busca más arriba qué nodo no configuró: con `nav2_params.yaml` en lugar
de `nav2_params_jazzy.yaml` serían el `planner_server`, el `behavior_server` y el
`bt_navigator`. Luego,
**terminal 2**, un destino a **4 m por delante** del carro, en línea recta:

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \"{pose: {header: {frame_id: map}, pose: {position: {x: 4.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}\"'"
```

> **Por qué 4 m y en recta.** El marco `map` lo sitúa `slam_toolbox` **donde
> arrancó el vehículo**, con el eje x hacia delante, así que `x: 4.0, y: 0.0` es
> «cuatro metros al frente». En recta porque Smac Híbrido planifica con
> `motion_model_for_search: REEDS_SHEPP`, que **incluye primitivas de marcha
> atrás**: un destino que obligue a maniobrar puede producir un plan con tramos
> en reversa, y la reversa **no está probada en este hardware**. Si el plan sale
> con reversa, anótalo y no insistas: es material, no un fallo.

| | |
|---|---|
| **Esperado** | El vehículo **avanza siguiendo el plan**. Llegar a la meta sería excelente, pero **no es el criterio**: el criterio es que planifique y que se mueva mandado por el planificador. |
| **Si planifica pero no se mueve** | Mira `ros2 topic echo /cmd_vel`. Si `linear.x` sale **por debajo de 0,40**, es la banda muerta: el puente traduce a throttle **0,0000** exacto y nada lo reporta. El launch ya sube `min_approach_linear_velocity` y `regulated_linear_scaling_min_speed` a 0,40 por esto; si aun así aparece un valor menor, **anota cuál** — hay un tercer camino que no conocemos y ese es el hallazgo. |
| **Si no planifica** | `ros2 topic echo /plan` vacío. Causas por probabilidad: (a) la meta cae fuera del mapa que SLAM ha construido —empuja el carro primero para que el mapa cubra los 4 m—; (b) `allow_unknown: false` en el planificador impide planificar sobre celdas no exploradas, que es exactamente el caso anterior. Prueba (a) primero: es gratis. **Lo que no es causa:** que el costmap global esté configurado a 0,06 y el mapa de SLAM llegue a 0,05. La capa estática redimensiona el costmap a la resolución del mapa que recibe (`static_layer.cpp:199-213`, rama jazzy) y lo anuncia con `StaticLayer: Resizing costmap to ... at 0.050000 m/pix`. |
| **Si se planta a ~0,6 m de la meta** | Sería la banda muerta de aproximación otra vez. Anota el `linear.x` que se estaba publicando. |
| **Cierre** | El vídeo del intento, el `linear.x` observado, y el bag (§5). |

---

## 5. Grabar el intento, que es lo único que sobrevive a la tarde

Los carros solo están entre semana; el análisis, no. **Terminal 5**, antes de
lanzar el destino:

```
ssh deepracer@192.168.0.NN "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && cd ~deepracer && timeout -s INT 180 ros2 bag record -s mcap -o nav2_intento_1 /rplidar_ros/scan /odom /cmd_vel /tf /tf_static /plan /map; chown -R deepracer:deepracer ~deepracer/nav2_intento_1'"
```

| | |
|---|---|
| **El `timeout -s INT` no es adorno** | `Ctrl-C` sobre `ssh host "orden"` **no llega** al grabador: muere el cliente en el portátil y el grabador queda huérfano y grabando. En disco queda un `.mcap` de **0 bytes sin `metadata.yaml`**, ilegible, y la pasada siguiente cae dentro. |
| **Comprobación inmediata** | `ssh deepracer@192.168.0.NN "source /opt/ros/jazzy/setup.bash && ros2 bag info ~/nav2_intento_1"` → `Count` **muy por encima de 0** en `/rplidar_ros/scan` y en `/cmd_vel`. Leer el bag sí vale como `deepracer`: es un fichero, no el grafo. |
| **Por qué se comprueba siempre** | El grabador es un participante recién nacido y **pierde los primeros ~5 s** de la ventana mientras descubre al publicador. Medido en el `.101` el 24-sep, con el carro parado: `timeout -s INT 8` → **2,6 s de datos**, 31 mensajes; `timeout -s INT 20` → **12,5 s**, 107. Es decir, **los 180 s de arriba son ~172 s reales**. El bag se crea y parece plausible aunque salga casi vacío: el fallo es silencioso. |
| **El grabador SÍ necesita `root`** | Y es la trampa más cara del carro. Como `deepracer`, una pasada de **198 s** el 24-sep dejó un bag con **un solo mensaje**: el `/tf_static` retenido, y **cero** en `/rplidar_ros/scan`, `/odom` y `/map` — aunque el grabador anunció en su log «Subscribed to topic» en los cinco. No es la pérdida de arranque de la fila de arriba: es la regla del dueño, explicada en el recuadro del §2. El `chown` del final está para poder traerse el bag luego por `scp` sin `sudo`. |
| **Traer los bags** | `mkdir -p ~/tesis_evidencia/S24_nav2_hardware && scp -r deepracer@192.168.0.NN:nav2_intento_\* ~/tesis_evidencia/S24_nav2_hardware/` |
| **Cierre** | Los bags en el portátil, con `message_count` distinto de cero. |

> El `\*` va escapado para que el comodín lo resuelva **el carro**. Sin escapar
> lo resuelve el portátil, que busca `nav2_intento_*` en tu directorio actual y
> no lo encuentra.

Anota en papel, por cada intento: **peldaño alcanzado, qué se vio, y el
`linear.x` observado**. Un intento fallido con la causa anotada vale; un intento
fallido sin ella no se puede volver a mirar.

---

## 6. Criterio de cierre del guion

No es «el carro llegó a la meta». Es **saber en qué peldaño se quedó la
cadena y por qué**, con el bag que lo demuestre. Los siete peldaños andando
sería el mejor desenlace posible; quedarse en el 2 con `rf2o` sin publicar TF y
el bag que lo prueba también cierra el guion, porque dice exactamente qué hay
que arreglar el martes.

Lo que **no** cierra el guion es volver sin bags.
