# El bloqueo de dominios DDS: no es estructural, y hay dos salidas medidas

**S21 · trabajo adelantado al domingo 2026-08-30.** El bloqueo que impide ejecutar la condición B
—la misión con relevo, que es el aporte declarado del proyecto— queda **acotado con medida** y con
dos caminos verificados en banco, uno de ellos hasta la pila real montada sobre los mundos del
proyecto. **Ninguna prueba de este documento necesitó tocar código de producción**, y eso es
deliberado: el punto de retorno queda limpio.

El bloqueo, tal como estaba escrito el 27-ago: `robot1` corre en `ROS_DOMAIN_ID=0` y `robot2` en el
2, con un `gzserver` cada uno; un nodo de ROS 2 vive en **un** dominio, luego el coordinador alcanza
a uno de los dos y nunca a los dos.

Guiones: [`herramientas/prueba_dos_dominios.py`](../../herramientas/prueba_dos_dominios.py) y
[`herramientas/prueba_dos_dominios_accion.py`](../../herramientas/prueba_dos_dominios_accion.py).

---

## 1. Lo primero: la salida ya estaba escrita, y se descartó por comodidad

Antes de probar nada se releyó lo que había. [`S17_dos_simuladores.md`](S17_dos_simuladores.md)
§4, del 14-ago, dice literalmente:

> «Se evaluó también la alternativa de un **único** `ROS_DOMAIN_ID` con dos `gzserver`. El remapeo
> de `/clock` **sí** es respetado por `rclpy`. La opción de dominio único es por tanto viable, pero
> se descarta: con dominios separados no hace falta remapear nada en ningún nodo. **Se deja
> registrado por si en el futuro se necesita que ambos robots compartan grafo.**»

Lo que hay, entonces, **no es un muro sino una decisión de comodidad con salida documentada**. Se
anota así y no de forma más favorable: el 24-ago ya se había advertido que el aislamiento por
dominio *«no hacía correcto el marco sin prefijar, solo aplazaba la colisión al punto del proyecto
donde más caro sale»*. El punto era este, y llegó.

La separación vive en **dos líneas** de `herramientas/robot.sh`, y su propio comentario admite que
son transporte y nada más:

```
robot1) DOMINIO=0; PUERTO=11345 ;;
robot2) DOMINIO=2; PUERTO=11346 ;;
```

Lo que **sí** es estructural es tener **dos `gzserver`**, no dos dominios: `gazebo_ros` de Humble
aplica a todos los plugins el namespace del primer modelo cargado, y además los dos pisos en una
sola escena hacen que el LiDAR de 10 m de `robot1` mida paredes del piso 2, que están a 5,44 m
(medido el 23-ago). Los dos simuladores se quedan; lo que se discute es el dominio.

## 2. Las cuatro opciones sobre la mesa

| | Qué es | Estado tras las pruebas |
|---|---|---|
| **A** | Un solo `gzserver` con los dos modelos | **Descartada.** Obligaría a reseparar los mundos en Y para que el LiDAR no cruce, y eso **invalida los mapas y las poses de spawn**. A tres semanas de la congelación no se paga |
| **B** | **Un dominio, dos `gzserver`, reloj remapeado** | **Elegida.** Verificada en §4 y hasta la pila real en §6. Estado final más limpio: un grafo, un grabador, un bag |
| **C** | `domain_bridge` (paquete apt Humble, 0.5.0 disponible) | **Ya no hace falta.** Queda en reserva. Puentea tópicos bien; una **acción** habría que armarla a mano con sus cinco primitivas |
| **D** | **Coordinador de dos contextos** `rclpy` | **Viable, verificada en §3.** Solo cambia `coordinador.py`; robots, mundos, mapas y poses intactos. Es el **plan de repliegue** si la implementación de B se atasca |

## 3. P1 y P1b — la opción D queda verificada

`rclpy` de Humble admite `domain_id` en la creación del contexto, lo que permite que **un proceso**
tenga dos:

```
rclpy.init  : (*, args, context, domain_id, signal_handler_options) -> None
Context.init: (self, args, *, initialize_logging, domain_id)
```

### 3.1 P1 — pub/sub, y la comprobación que la hace válida

Dos contextos en un proceso, dominios 0 y 2, cada uno publicando en `/robotN/odom` y **suscrito a
los dos** tópicos.

| Receptor | Tópico | Mensajes | Esperado |
|---|---|---|---|
| dominio 0 | `/robot1/odom` | **30** | propio: debe llegar ✅ |
| dominio 0 | `/robot2/odom` | **0** | ajeno: NO debe llegar ✅ |
| dominio 2 | `/robot1/odom` | **0** | ajeno: NO debe llegar ✅ |
| dominio 2 | `/robot2/odom` | **30** | propio: debe llegar ✅ |

**La mitad que importa es la de los ceros.** Si los dos contextos hubieran acabado en el mismo
dominio —porque `domain_id` se ignorase en silencio—, la prueba de que «llegan los mensajes»
pasaría igual y la conclusión sería falsa. La ausencia de fuga cruzada es lo que distingue
*funciona* de *parece que funciona*.

### 3.2 P1b — acciones, que es lo que el coordinador hace de verdad

P1 no decidía nada por sí sola: **una acción no es un tópico**. Son cinco primitivas —tres
servicios y dos tópicos— con QoS propios y una negociación de goal, feedback y resultado. Que
`/odom` cruce el límite de dominio no dice nada de si `NavigateToPose` lo cruza.

Se reprodujo la topología exacta de `coordinador.py`: dos servidores falsos de `NavigateToPose`,
uno por dominio, y un cliente bi-contexto que **además sirve** su propia acción en el dominio 0
—porque el coordinador no solo llama, también atiende a la HRI—.

| Dominio | Servidor visible | Goal aceptado | Resultado | Tiempo |
|---|---|---|---|---|
| 0 / `robot1` | sí | sí | `status=4` (SUCCEEDED) | 1,05 s |
| 2 / `robot2` | sí | sí | `status=4` (SUCCEEDED) | 1,06 s |

**Servir y llamar en contextos distintos del mismo proceso no se estorban.**

### 3.3 Un defecto que la prueba destapó en sí misma, y que hay que llevarse al coordinador

La primera versión de P1 abortaba con `terminate called without an active exception` **después** de
imprimir el veredicto. **Un aborto tardío es más peligroso que uno temprano:** no invalida el
resultado, y por eso se ignora.

La causa era el orden de cierre —apagar el ejecutor y destruir nodos con los hilos de `spin`
todavía vivos—. El orden correcto es:

1. `context.try_shutdown()` — hace que `spin()` retorne
2. `join()` de los hilos
3. `destroy_node()`

**Por qué esto no es trivia:** si el coordinador cerrara mal, **Ctrl-C lo reventaría en vez de
cerrarlo**, y `grabar_mision.sh` cerraría el bag contra un proceso ya muerto. Queda escrito en el
comentario de los dos guiones para que no se vuelva a perder.

## 4. P2 — la opción B queda verificada, con tres sorpresas

Cuatro variantes sobre `gzserver` con `libgazebo_ros_init.so`, mundo vacío, dominio 0.

| # | Argumentos | Resultado |
|---|---|---|
| **a** | `-r __ns:=/robot2` | Nodo `/robot2/gazebo` ✅ · `/robot2/spawn_entity` y `/robot2/delete_entity` ✅ · **`/clock` sigue siendo `/clock`** ❌ |
| **b** | `-r __ns:=... -r /clock:=...` | **`Error. Invalid arguments`**, gzserver aborta con código 255 |
| **c** | `--remap __ns:=... --remap /clock:=...` | **`/robot2/clock`, 1 publicador**; `/clock` deja de existir ✅ |
| **e** | **Dos gzserver**, puertos 11345 y 11346, **mismo dominio** | Ver tabla siguiente |

Resultado de la variante **e**, que es la que decide:

| Recurso | Estado |
|---|---|
| Nodos | `/robot1/gazebo` y `/robot2/gazebo` — sin colisión de nombres |
| Relojes | `/robot1/clock` y `/robot2/clock`, **1 publicador cada uno** |
| Spawn | `/robot1/spawn_entity` y `/robot2/spawn_entity` — sin ambigüedad |
| `/clock` a secas | **0 publicadores**, no existe |

**Dos `gzserver` conviven en un solo dominio sin pisarse en nada.** El bloqueo se puede eliminar
entero.

### 4.1 `-r` es una trampa, y de la peor clase: la que funciona

`-r` es flag propio de **gzserver** (`--record`). En la variante **a**, `-r __ns:=/robot2` **sí
aplicó el namespace** —así que la prueba «pasaba»— mientras Gazebo arrancaba **en silencio una
grabación de estado** en `~/.gazebo/log/2026-08-30T104332.193779`. Se encontró porque se fue a
buscar, no porque avisara.

En una campaña de 30 corridas eso escribe a disco de forma continua y **compite por CPU justo donde
el RNF-06 exige RTF ≥ 0,99**. Y en la variante **b**, con dos `-r`, el parser de Gazebo ve tres
argumentos posicionales donde solo cabe un mundo y aborta.

**Regla:** en la línea de `gzserver` se usa `--remap`, forma larga, siempre. Nunca `-r`.

### 4.2 El namespace no arrastra a `/clock`

`gazebo_ros_init` publica `/clock` con **nombre absoluto**, así que `__ns:=` no lo toca. Hacen falta
**los dos** remapeos, y por motivos independientes:

- `--remap __ns:=/robotN` — evita que dos nodos se llamen `gazebo` y que `/spawn_entity` sea
  ambiguo. **Sin esto, un spawn podría irse al simulador equivocado en silencio**, que es la clase
  de fallo que costó tres bags entre el 26 y el 27 de agosto.
- `--remap /clock:=/robotN/clock` — evita que dos relojes se pisen.

### 4.3 Los 98 segundos

Con los dos simuladores vivos, leídos en el mismo instante:

| Reloj | Valor |
|---|---|
| `/robot1/clock` | 49,4 s |
| `/robot2/clock` | 147,4 s |
| **Desfase** | **98,0 s** |

**No es la deriva de RTF del 0,2 % que se anticipó: es un desfase constante y grande**, puro orden
de arranque. Cada `gzserver` cuenta desde su propio cero.

No hace daño mientras **todas** las marcas de una misión salgan del **mismo** reloj —en una resta el
desfase se cancela—, pero sería catastrófico si se mezclaran: 98 s de error sobre un `t_respuesta`
cuyo valor medido es de **0,1 s**.

**Consecuencia concreta, y es trabajo, no una nota:** `grabar_mision.sh` graba hoy `/clock`, en su
lista de imprescindibles, y con este cambio **`/clock` deja de existir**. La guarda 1 —que cuenta
publicadores— se negaría a grabar, que al menos es un fallo ruidoso y no silencioso. Hay que decirle
qué reloj graba, y **el registro de misión tiene que declarar cuál fue**, porque el esquema hoy no
tiene dónde anotarlo.

## 5. P3 (parcial) — el diseño tiene que ser asimétrico, y no por elegancia

P3 completa es «la pila entera bajo reloj remapeado». Aquí van las **dos mitades baratas**, que se
corrieron primero porque concentran el riesgo. Las dos cambiaron el diseño.

### 5.1 `ros2 bag record` no se puede remapear — esto tumba el remapeo simétrico

Su `--use-sim-time` está **cableado a `/clock`**. El CLI ni siquiera acepta `--ros-args`:

```
ros2: error: unrecognized arguments: --ros-args --remap /clock:=/robot1/clock
```

Y la ayuda lo dice: *«subscribing to the /clock topic. Until first /clock message is received, no
messages will be written to bag»*. **No se dio por bueno el texto: se midió.** Grabando con
`--use-sim-time` existiendo solo `/robot1/clock`:

| Campo del `metadata.yaml` | Valor |
|---|---|
| `message_count` | **0** |
| `starting_time.nanoseconds_since_epoch` | **9223372036854775807** (INT64_MAX: nunca se fijó) |
| `duration.nanoseconds` | 0 |

**Remapear los dos relojes rompe el grabador**, y lo rompe de la peor manera: deja un bag creado,
con el nombre correcto y cero mensajes. El aviso existe —`waiting for /clock before starting
recording...`— pero es una línea INFO entre veinte. Es la misma familia de fallo que costó tres bags
entre el 26 y el 27 de agosto.

### 5.2 Los nodos C++ sí respetan el remapeo

Era la duda de fondo: el 14-ago solo se verificó **`rclpy`**, y Nav2 es **C++**. La pregunta no se
respondió mirando sellos de tiempo sino mirando **a qué reloj se suscribe el nodo**, que no admite
interpretación:

```
/robot1/clock   Publisher count: 1        (gazebo)
                Subscription count: 2
                  static_transform_publisher_...    <- nodo C++
                  gazebo
/clock          no existe
```

`rclcpp` aplica el remapeo a la suscripción que crea `use_sim_time`. **El riesgo grande de la
opción B queda descartado.**

**Un falso positivo que se descartó de camino:** el sello de `/tf_static` salió `sec: 0`, que parece
fallo y no lo es. `static_transform_publisher` publica **una sola vez al arrancar**, antes de
recibir el primer `/clock`, y con `use_sim_time` eso da 0 tanto si el remapeo funciona como si no.
El sello era una prueba incapaz de distinguir los dos casos; la suscripción sí.

### 5.3 El diseño que sale de las dos

El remapeo simétrico —los dos relojes fuera de `/clock`— **no es viable** por 5.1. Lo que lo arregla
ya estaba en la variante **a** del §4: `__ns:=` **no** arrastra a `/clock`, así que las dos cosas se
pueden separar.

| | `robot1` | `robot2` |
|---|---|---|
| gzserver | `--remap __ns:=/robot1` | `--remap __ns:=/robot2 --remap /clock:=/robot2/clock` |
| Reloj resultante | **`/clock`** — el de referencia | `/robot2/clock` |
| Nodos Nav2 / AMCL | sin cambios | `-r /clock:=/robot2/clock` |
| `grabar_mision.sh` | `--use-sim-time` tal cual, sobre `/clock` | — |

Los dos `gzserver` dejan de colisionar en nombres de nodo y en `spawn_entity`, el grabador sigue
funcionando **sin tocarlo**, y **todas las marcas de una misión salen forzosamente del mismo
reloj** — que es exactamente la regla que imponían los 98 s del §4.3.

**La asimetría no es un parche estético: es lo que obliga la restricción del grabador.** Conviene
decirlo así en la sustentación, porque un diseño asimétrico sin justificación parece descuido.

## 6. P4 — la pila real, montada, con el mundo real

Hasta aquí todo era mundo vacío y servidores falsos. P4 monta el vehículo entero —URDF,
`gazebo_ros2_control`, los siete controladores, LiDAR y cámara— sobre los mundos de verdad
(`mundo_definitivo_piso1.world` y `..._piso2.world`) y las poses reales de `POSE_INICIAL`.

Se hizo **sin editar ni un launch**, descomponiendo lo que hace `robot.sh`: `gzserver` a mano con
los remapeos, y `deepracer_spawn.launch.py` aparte.

### 6.1 P4-a — la sospecha del namespace duplicado era falsa

El §6 anterior de este documento daba por probable que `gazebo_ros2_control`, al correr **dentro**
de gzserver, heredara su `__ns:=/robot1` **además** del que el propio modelo aplica por
`<ros><namespace>`, y saliera `/robot1/robot1/...`. Se midió y **no ocurre**:

| Comprobación | Resultado |
|---|---|
| Nodos | 14, todos bajo `/robot1/…`; **`/robot1/controller_manager`**, no `/robot1/robot1/…` |
| Controladores | **7 de 7 `active`** |
| `/robot1/odom` | 14,90 Hz · `frame_id: robot1/odom` · `child_frame_id: robot1/base_link` |
| `/robot1/scan` | 9,98 Hz |
| `/clock` | 1 publicador, **13 suscriptores** — la pila entera colgada del reloj |
| Sello de `odom` | `sec: 671` — tiempo simulado, no de pared |

La razón es de `rclcpp` y conviene dejarla escrita: el `<ros><namespace>` del plugin llega como
**argumento local del nodo**, y los argumentos locales **ganan** a los globales del proceso. No se
concatenan. **La objeción más cara contra la opción B se cae.**

### 6.2 Dos trampas nuevas, las dos silenciosas

**`extra_gazebo_args` no sirve para pasar remapeos.** Es el camino natural —reenviarlo desde
`deepracer_sim.launch.py` a `gzserver.launch.py`— y **no funciona**. Es un único
`LaunchConfiguration` dentro de la lista `cmd`, así que `"--remap __ns:=/robot1"` llega a gzserver
como **un solo argumento**. Verificado leyendo `/proc/<pid>/cmdline` separado por NUL: un token, no
dos. Gazebo lo descarta sin decir nada y el nodo se queda en `/gazebo`.

Contraste, misma bandera:

| Forma | Nodo resultante |
|---|---|
| `extra_gazebo_args:="--remap __ns:=/robot1"` (un token) | `/gazebo` ❌ **sin aviso** |
| `--remap` `__ns:=/robot1` (dos tokens, gzserver a mano) | `/robot1/gazebo` ✅ |

Consecuencia de diseño: hay que **sustituir el `IncludeLaunchDescription` de `gzserver.launch.py`
por un `ExecuteProcess` propio**, con los remapeos como elementos separados de la lista.

**`spawn_entity.py` pide `/spawn_entity` absoluto.** No lo relativiza al namespace de su nodo: lo
compone con su propio argumento `-gazebo_namespace`, cuyo defecto es la cadena vacía. Con el
gzserver remapeado el spawn muere a los 30 s con

```
Service /spawn_entity unavailable. Was Gazebo started with GazeboRosFactory?
```

que apunta al sitio equivocado —Gazebo **sí** tenía el factory cargado— y es exactamente el patrón
que ya denuncia la cabecera de `robot.sh`. Con `-gazebo_namespace /robotN` spawnea a la primera.

### 6.3 P4-b — las dos pilas completas en un solo dominio

La prueba que decide. Dominio 0 para los dos, puertos 11345 y 11346, mundos y poses reales:

| | `robot1` | `robot2` |
|---|---|---|
| `gzserver` | `--remap __ns:=/robot1` | `--remap __ns:=/robot2 --remap /clock:=/robot2/clock` |
| Controladores | **7/7 `active`** | **7/7 `active`** |
| Reloj | `/clock`, 1 pub | `/robot2/clock`, 1 pub |
| `odom` | 14,90 Hz | 14,90 Hz |
| `scan` | — | 9,99 Hz |
| Sello de `odom` **contra su reloj** | 929,9 vs 926,8 | 77,6 vs 74,9 |

**Catorce controladores activos en un solo dominio, y cada pila sellando contra su propio reloj.**
El desfase entre los dos volvió a salir grande —unos 852 s— y otra vez solo por orden de arranque,
lo que confirma los 98 s del §4.3 como fenómeno y no como número.

### 6.4 Una falsa alarma que valió la pena perseguir

En el grafo, el `controller_manager` de `robot2` y sus **siete** controladores aparecen suscritos a
`/clock` —el de robot1— y no a `/robot2/clock`. Parece contaminación grave. En los datos no lo es:

| Tópico | Sello |
|---|---|
| `/robot2/joint_states` | **242** |
| `/robot2/clock` | 244 |
| `/clock` | 1096 |

Los controladores toman el tiempo del argumento que `gazebo_ros2_control` les pasa en `update()`,
que sale directo del motor de Gazebo. La suscripción es solo el `TimeSource` que crea
`use_sim_time`, y está **inerte**.

**Esto invierte el criterio del §5.2 y hay que anotarlo.** Allí el conteo de suscripciones fue la
prueba decisiva; aquí habría dado un **falso positivo**. La regla que queda: el conteo de
suscripciones prueba que **un remapeo se aplicó**; no prueba **de dónde sale un sello**. Para eso
hay que mirar el sello.

### 6.5 La dependencia latente también resultó inerte

Si esos ocho nodos escuchan `/clock`, ¿qué pasa cuando `robot1` no existe? Es una pregunta real:
en una misión puede haber un solo robot, o el otro puede caerse. Se probó matando el `gzserver` de
`robot1` con `robot2` corriendo. `/clock` se queda sin publicadores y `robot2` **sigue entero**:

| | Valor |
|---|---|
| Controladores | 7/7 `active` |
| `/robot2/odom` | 14,906 Hz |
| `/robot2/scan` | 9,986 Hz |
| Línea de tiempo | `odom` 451 · `joint_states` 452 · `/robot2/clock` 453 |

**El robot del piso 2 no depende del simulador del piso 1.** La asimetría del §5.3 no introduce un
punto único de fallo.

## 7. Lo que estas pruebas NO demuestran

Se dice explícitamente para que nadie cite este documento de más:

1. **No se probó Nav2 ni AMCL.** Y son el caso que queda: corren **fuera** de gzserver, así que no
   heredan ningún remapeo y necesitan el `-r /clock:=/robot2/clock` explícito.
   `nav_amcl_demo_sim.launch.py` hoy **no tiene por dónde recibirlo**.
2. **No se midieron los sellos de `/tf`.** El `robot_state_publisher` corrió sin `use_sim_time` y
   copia la marca de `joint_states`, así que debería estar bien. *Debería* no es *medido*.
3. **No se ha ejecutado ni un solo relevo.** Quitar el bloqueo es condición necesaria y no
   suficiente: el hito 5 sigue en 🟡 hasta que haya una misión de dos tramos con relevo medida
   contra `/odom`.

**La opción B queda verificada hasta donde se puede verificar sin tocar código.** Lo que falta ya
no es prueba sino implementación, y P4-a dejó claro que no son dos líneas: hay que cambiar el
arranque de gzserver por un `ExecuteProcess` propio, pasar `-gazebo_namespace` al spawn y abrir un
argumento de reloj en el launch de Nav2. **C** —`domain_bridge`— deja de hacer falta y se queda en
reserva; **D** sigue verificada y es el plan de repliegue si la implementación de B se atasca.

## 8. Cómo se reproduce

Las dos pruebas baratas son un solo comando y no necesitan Gazebo, Nav2 ni el workspace compilado.
Salen con código 0 si pasan:

```
source /opt/ros/humble/setup.bash
herramientas/prueba_dos_dominios.py            # P1  — pub/sub y fuga cruzada
herramientas/prueba_dos_dominios_accion.py     # P1b — acciones en dos dominios
```

P2 se reproduce a mano con la línea de la variante **c** de la tabla del §4. P4 se reproduce en
tres pasos, con el workspace compilado y `ROS_DOMAIN_ID=0` en las tres terminales:

```
# 1. gzserver a mano. OJO: --remap en tokens separados, nunca por extra_gazebo_args.
gzserver <repo>/mundo_definitivo_piso1.world \
  -s libgazebo_ros_init.so -s libgazebo_ros_factory.so -s libgazebo_ros_force_system.so \
  --remap __ns:=/robot1

# 2. robot_state_publisher y la cadena de controladores
ros2 launch deepracer_bringup deepracer_spawn.launch.py \
  namespace:=robot1 x:=-19.165 y:=7.292 z:=0.03 yaw:=1.5708

# 3. el spawn, que el launch NO consigue hacer solo mientras no lleve -gazebo_namespace
ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity robot1 \
  -x -19.165 -y 7.292 -z 0.03 -Y 1.5708 -gazebo_namespace /robot1 \
  --ros-args -r __ns:=/robot1
```

Para `robot2` es igual con el mundo del piso 2, la pose de `POSE_INICIAL`,
`GAZEBO_MASTER_URI=http://localhost:11346` y el remapeo de reloj añadido en el paso 1.
