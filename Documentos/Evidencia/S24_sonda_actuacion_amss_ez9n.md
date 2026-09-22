# Sonda de actuación sobre `amss-ez9n`: ¿la avería del nodo de servos es de un vehículo o de la plataforma?

**Fecha de la sesión:** martes 2026-09-22.
**Vehículo medido:** `amss-ez9n`. **Vehículo apagado por interruptor:** `amss-jgm9`.
**Plantilla escrita antes de correr**, a propósito: los veredictos del §5 están preinscritos y no se
ajustan después de ver un resultado.

> **Corrección posterior a la corrida.** Dos supuestos de esta cabecera resultaron falsos y se dejan
> tachados a la vista en vez de reescribirlos: (a) el interruptor **no apaga** la tarjeta de cómputo,
> sólo la tracción, de modo que `amss-jgm9` estuvo encendido y en red durante la primera mitad de la
> sesión; (b) el primer bloque de medidas se atribuyó a `amss-ez9n` cuando en realidad ese vehículo
> estaba apagado y lo que se midió fue `amss-jgm9`. La causa de (b) es que `ros2 topic info` consulta
> **el dominio entero**, no el vehículo al que uno se conectó por `ssh`. El desenlace de la sesión
> está en el §7, y **ninguno de los ocho veredictos preinscritos del §5 lo anticipaba**.

---

## 1. Qué se decide hoy, y por qué hoy

La avería apareció el 2026-09-21 sobre `amss-jgm9`: el nodo de servos recibe publicaciones y no
actúa, no atiende a sus propios servicios, y el fallo sobrevive a reiniciar el servicio, a reiniciar
la máquina y a reasentar la batería de tracción. El registro está en
[`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §5, anotado como **anomalía
abierta, no como diagnóstico**.

`amss-ez9n` es el desempate. Si también falla, la avería es de plataforma y no de un vehículo, y eso
cambia lo que se puede prometer en la demostración física. La decisión tiene fecha: el corte del
viernes 25 de septiembre (`ACTA_GO_NOGO.md` §5).

**Lo que no se hace hoy:** provocarle a `amss-ez9n` la pérdida de alimentación de tracción que
rompió a `amss-jgm9`. Es el experimento decisivo sobre la anomalía y también la forma de quedarnos
sin vehículo antes del corte.

---

## 2. Las pruebas, con su razón

| Prueba | Por qué la hacemos | Qué hipótesis mata | Dónde está escrito |
|---|---|---|---|
| Identificar al segundo publicador del tópico de servos | El 2026-09-21 el contador marcó 2 con un solo carro encendido. Mientras no sepamos quién es el segundo, ninguna medida de actuación es defendible | «El 2 son los dos carros viéndose en el dominio compartido» | [`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §0 y §8.2 |
| Control de entorno con el nivel de batería | Si el nodo de servos expira, hay que poder demostrar que no fue la receta de entorno ni el bus | «El nodo de servos no contesta porque las variables de entorno están mal puestas» | [`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §2 y §3 |
| Sonda de vida del nodo de servos | Es la pregunta que sostiene el corte del viernes | «La avería es del vehículo `amss-jgm9`» | [`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md) §4; [`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §5 |
| Movimiento observado de las ruedas, carro en alto | Que el servicio conteste no prueba actuación: en `amss-jgm9` llegaron ocho mensajes y las ruedas no se movieron | «Si el nodo responde, el vehículo actúa» | [`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §4; [`GUIA_TELEOP_MANDO.md`](../GUIA_TELEOP_MANDO.md) Parte 6 |

---

## 3. Condiciones de la sesión

Rellenar antes de empezar. Una corrida sin estas casillas no sostiene conclusiones.

| Dato | Valor |
|---|---|
| Hora de inicio | ~14:45 (arranque de `deepracer-core` en `amss-jgm9`, PID 656) |
| Hora de cierre | ~15:25 |
| `hostname` del vehículo medido | Primera mitad: `amss-jgm9`. Segunda mitad: `amss-ez9n` |
| Dirección IP con la que respondió | `192.168.0.101` y `192.168.0.102` respectivamente |
| `amss-jgm9` apagado por interruptor (sí / no) | **No.** El interruptor corta tracción; la tarjeta siguió encendida y en red. Se apagó por `sudo shutdown -h now` a media sesión |
| Nivel de batería de tracción al empezar | Sin medir |
| Nivel de batería de tracción al cerrar | `level = -1` en `amss-ez9n`: **no hay batería de tracción conectada**. El vehículo estaba alimentado por un cargador de pared mientras se cargaban los power bank |
| Quién estuvo presente | Santiago Hernández |
| Calidad del enlace inalámbrico | Se degradó durante la sesión: de 15 ms y 0 % de pérdida a 106 ms y 50 % |

---

## 4. Anotaciones

Pegar la salida **completa**, incluido el código de salida. Una corrida cortada antes de imprimir su
informe no sostiene ninguna conclusión.

### 4.1 Quién es el segundo publicador

Los seis extremos salieron con `Node name: _NODE_NAME_UNKNOWN_`, dato que en su momento se pasó por
alto y que resultó ser el primer síntoma de la causa raíz del §7. Lo que sí discriminó fueron los
GID:

```
$ ros2 topic info /ctrl_pkg/servo_msg --verbose
Publicador 1 → GID: 01.0f.c8.0f.90.02.fa.76.00.00.00.00.00.00.28.03...
Publicador 2 → GID: 01.0f.c8.0f.90.02.fa.76.00.00.00.00.00.00.36.03...
Suscriptor   → GID: 01.0f.c8.0f.9f.02.9a.96.00.00.00.00.00.00.15.04...
```

En Fast DDS el prefijo del GID identifica al participante. **Los dos publicadores comparten el
prefijo completo**: son un único proceso con dos publicadores sobre el mismo tópico, no dos
máquinas. El suscriptor cambia los bytes de proceso y conserva los de máquina: es `servo_node`, otro
proceso del mismo vehículo.

```
$ ros2 node list
(vacío)

$ ros2 daemon stop && ros2 topic info /ctrl_pkg/servo_msg --no-daemon --verbose
sequence size exceeds remaining buffer   (×9)
Publisher count: 2      ← el contador no baja sin el demonio
```

```
$ ssh deepracer@192.168.0.101 "ps -ef | grep [c]trl"
root  656  649  0 14:45 ?  00:00:02 /opt/aws/deepracer/lib/ctrl_pkg/lib/ctrl_pkg/ctrl_node ...
```

Un único `ctrl_node`. Y el ping a `192.168.0.101` **respondió** pese a estar «apagado por
interruptor», lo que destapó que el interruptor sólo corta tracción.

**Contraprueba, con los dos vehículos encendidos:**

```
$ ros2 topic info /ctrl_pkg/servo_msg
Publisher count: 4
Subscription count: 2
```

Y tras apagar `amss-jgm9` por software, desde dentro de `amss-ez9n`: `Publisher count: 2`,
`Subscription count: 1`. Mitad exacta.

**Veredicto de esta prueba:** la hipótesis «el 2 son los dos carros viéndose en el dominio
compartido» queda **falsada por conteo**. Cada vehículo aporta dos publicadores y una suscripción;
`ctrl_pkg` registra más de un publicador sobre el mismo tópico por diseño. El `Publisher count: 2`
del 2026-09-21 no era una anomalía de aislamiento. Se corrige en consecuencia la frase «son los dos
carros» de [`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §0, y también el
recuento de 186 servicios que allí se atribuye a un solo vehículo: eran los dos.

### 4.2 Control de entorno con el nivel de batería

Ejecutado **dentro de `amss-ez9n`**, como usuario `deepracer`, con la receta de entorno de
[`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §2 exportada. Los nombres y
tipos se leyeron, no se supusieron:

```
$ ros2 service list -t | grep -iE 'servo|battery'
/i2c_pkg/battery_level       [deepracer_interfaces_pkg/srv/BatteryLevelSrv]
/servo_pkg/get_calibration   [deepracer_interfaces_pkg/srv/GetCalibrationSrv]
/servo_pkg/set_calibration   [deepracer_interfaces_pkg/srv/SetCalibrationSrv]
/servo_pkg/servo_gpio        [deepracer_interfaces_pkg/srv/ServoGPIOSrv]
(y los servicios de parámetros de battery_node, servo_node)
```

```
$ timeout 10 ros2 service call /i2c_pkg/battery_level deepracer_interfaces_pkg/srv/BatteryLevelSrv '{}'; echo SALIDA=$?
waiting for service to become available...
requester: making request: ...BatteryLevelSrv_Request()
SALIDA=124
```

El control **falló**, lo que por el §5 obligaba a parar. Pero la forma del fallo no era la esperada:
`waiting for service to become available` significa que el cliente **nunca emparejó** con el
servidor, no que el servidor respondiera mal. Un servicio listado que no se puede invocar es un
síntoma distinto de un nodo caído, y es lo que llevó al §7.

```
$ timeout 10 ros2 param list /i2c_pkg/battery_node ; echo SALIDA=$?
Node not found
SALIDA=1
```

Idéntico para `/servo_pkg/servo_node` y `/ctrl_pkg/ctrl_node`: `Node not found`, fallo **inmediato**,
no expiración. Con 171 servicios listados y dos publicadores emparejados, el grafo de **nodos**
estaba vacío mientras el de **extremos** funcionaba.

**Veredicto de esta prueba:** el control no es válido como control. No mide el entorno ni el bus:
mide el mismo defecto que iba a medir la sonda. La sesión queda suspendida aquí y se abre la
investigación del §7.

### 4.3 Sonda de vida del nodo de servos

Las peticiones, leídas antes de llamar:

```
$ ros2 interface show deepracer_interfaces_pkg/srv/BatteryLevelSrv
---
int32 level

$ ros2 interface show deepracer_interfaces_pkg/srv/GetCalibrationSrv
int32 cal_type
---
int32 max
int32 mid
int32 min
int32 polarity
int32 error
```

Repetida **como `root`** en `amss-ez9n`, tras encontrar la causa raíz del §7:

```
# ros2 service call /i2c_pkg/battery_level deepracer_interfaces_pkg/srv/BatteryLevelSrv '{}'
response: BatteryLevelSrv_Response(level=-1)
SALIDA=0

# ros2 service call /servo_pkg/get_calibration deepracer_interfaces_pkg/srv/GetCalibrationSrv '{cal_type: 0}'
response: max=1700000, mid=1450000, min=1300000, polarity=1, error=0
SALIDA=0

# ros2 service call /servo_pkg/get_calibration deepracer_interfaces_pkg/srv/GetCalibrationSrv '{cal_type: 1}'
response: max=1603500, mid=1446000, min=1311000, polarity=-1, error=0
SALIDA=0
```

**Veredicto de esta prueba:** `servo_pkg` en `amss-ez9n` está **vivo y sano**. Responde a su propio
servicio con las dos calibraciones, dirección y tracción, y `error=0` en ambas. El `level = -1`
confirma por separado que no hay batería de tracción conectada, coherente con la alimentación por
cargador de pared.

La calibración de dirección coincide exactamente con la única respuesta que `servo_pkg` había dado
nunca (`1300000 / 1450000 / 1700000`, polaridad 1). La de tracción, `1311000 / 1446000 / 1603500`
con polaridad −1, se registra aquí por primera vez.

### 4.4 Movimiento observado de las ruedas

Carro **en alto**, ruedas sin tocar el suelo, con el mando y su hombre muerto de 0,6 s
([`GUIA_TELEOP_MANDO.md`](../GUIA_TELEOP_MANDO.md) Parte 6).

Se ejecutó con el pack de tracción ya conectado y cargado. El primer intento, con el vehículo
alimentado sólo por un cargador de pared, dio `level = -1` y **no movió nada**; al conectar el pack,
el mismo servicio devolvió `level = 6`. Es decir: el sensor de batería funciona, y el `-1` era una
lectura correcta de «sin alimentación de tracción», no un fallo.

En lugar del mando se usó una sonda escrita para esta prueba, porque el mando exige un operador y
aquí hacía falta una secuencia repetible con parada garantizada. Publica en `/ctrl_pkg/servo_msg` a
20 Hz con QoS `BEST_EFFORT`, y en su bloque `finally` emite cuarenta mensajes en cero aunque el
proceso muera. Se comprobó antes que `ctrl_pkg` **no publica nada estando ocioso**, de modo que no
hay dos fuentes compitiendo por el mismo tópico.

Dirección: `/tmp/sonda_direccion.py`, secuencia centro → −0,80 → centro → +0,80 → centro, con
`throttle` fijo en 0,00. Se eligió empezar por dirección precisamente porque no puede desplazar el
vehículo aunque esté en el suelo.

Tracción: `/tmp/sonda_traccion.py`, con `angle` fijo en 0,00. Primero a ±0,30 y después a ±0,60.

| Observación | Resultado |
|---|---|
| Las ruedas de dirección giran a izquierda y derecha | **Sí** |
| El giro es proporcional al mando, no todo o nada | **Sí** |
| Las ruedas de tracción giran hacia adelante | **Sí, a razón 0,60.** A 0,30 el variador emitió su tono pero no rompió inercia |
| Las ruedas de tracción giran hacia atrás | **Sí, a 0,60. Y también a −0,30**, flojo |
| Al soltar el mando, el vehículo se detiene antes de 1 s | **Sí** |

El nivel de batería se leyó antes y después de cada corrida: `level = 6` en las dos, sin caída bajo
carga.

**Veredicto de esta prueba: la compuerta de actuación (G-1 de [`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md)
§4) queda ALCANZADA sobre `amss-ez9n`.** Un proceso ajeno a la pila de AWS publica en
`/ctrl_pkg/servo_msg` y el vehículo se mueve: dirección a los dos lados, de forma proporcional;
tracción en los dos sentidos; y parada por debajo de 1 s al volver el comando a cero.

### 4.4.1 La asimetría de 0,30, y por qué no es una avería

A razón 0,30 un sentido giró y el otro sólo hizo sonar el variador. Lo explica la calibración leída
en el §4.3, que **no es simétrica**:

| Sentido | Recorrido de PWM desde `mid = 1446000` | Desviación a razón 0,30 |
|---|---|---|
| Hacia `min = 1311000` | 135 000 | 40 500 |
| Hacia `max = 1603500` | 157 500 | 47 250 |

Un 17 % más de desviación en un sentido que en el otro para la misma razón. El umbral de arranque
del variador cae entre 40 500 y 47 250, así que 0,30 queda **a un lado y otro del umbral según el
sentido**. No es un defecto del motor: es que la razón no significa lo mismo en los dos sentidos.

Se decide no levantar la rampa fina de umbral porque el dato operativo ya existe y coincide:
**0,60 es la razón a la que rompe inercia siempre**, y de 0,60 a 1,00 es el margen de trabajo. El
mismo 0,600 figura en [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md):70 como la razón
con la que el carro sí se movió.

---

## 5. Veredictos preinscritos

Escritos **antes** de correr. No se ajustan después.

| Si ocurre | Entonces se declara | Y la consecuencia es |
|---|---|---|
| El contador baja a 1 sin el demonio de descubrimiento | El segundo publicador era un fantasma en caché | El aislamiento estaba bien. La frase «son los dos carros» del §0 se corrige por escrito |
| Los dos publicadores comparten nombre de nodo, o hay dos procesos de control | Duplicación local en la misma tarjeta | Se mata el huérfano antes de medir nada, y se anota cómo apareció |
| El nivel de batería expira con código 124 | La sesión no es concluyente | Se para. No se interpreta nada del nodo de servos |
| El nivel de batería responde y el nodo de servos expira con código 124 | La avería **no** es de entorno ni de bus | Es del nodo de servos, y ahora en dos vehículos |
| El nodo de servos responde en `amss-ez9n` | La avería es del vehículo `amss-jgm9`, no de la plataforma | La demostración física sigue viva sobre un vehículo |
| El nodo de servos responde **y** las ruedas giran | La compuerta de actuación queda **alcanzada** sobre `amss-ez9n` | Se pasa a la compuerta de odometría, que es la siguiente y la que tiene evidencia en contra |
| El nodo de servos responde **y** las ruedas **no** giran | Mismo cuadro que `amss-jgm9`: recibe y no actúa | La compuerta de actuación queda **no alcanzada**, con diagnóstico, en dos vehículos |
| El nodo de servos expira también en `amss-ez9n` | La avería es **de plataforma** | La compuerta de actuación queda **no alcanzada con diagnóstico**, que es un resultado publicable. Se activa la conversación del corte del viernes |

---

## 6. Qué queda abierto al cerrar

| Pregunta abierta | Qué haría falta para cerrarla |
|---|---|
| ~~¿La avería de `amss-jgm9` del 2026-09-21 era real, o el mismo artefacto del §7?~~ | **Cerrada el mismo día.** §8: era el artefacto. `amss-jgm9` responde |
| ~~¿Actúan de verdad los servos de `amss-ez9n`?~~ | **Cerrada el mismo día.** §4.4: dirección y tracción en los dos sentidos, parada por debajo de 1 s |
| ¿Dónde vive la regla de dueños para que no vuelva a perderse? | Está en las guías de pasada, no en el material de diagnóstico, y es la tercera vez que cuesta una tarde. Llevarla a `GUIA_EJECUCION.md` con el síntoma por delante: «`SALIDA=124` o `waiting for service to become available` ⇒ mira el dueño y el transporte» |
| ¿Puede el portátil (Humble) hablar con los carros (Jazzy) a través de la red? | Entre máquinas distintas no hay memoria compartida, así que el §7 no aplica. Pero quedan sin explicar los nueve `sequence size exceeds remaining buffer` del §4.1, que apuntan a la mezcla de distribuciones. Se prueba llamando al mismo servicio desde el portátil |
| ~~¿Por qué `ctrl_node` y `servo_node` no aparecen en `ros2 node list` ni siquiera como `root`?~~ | **Cerrada el mismo día.** §8: con el perfil solo-UDP aparecen los dos. La ausencia era un tercer síntoma de la misma causa, no un defecto de lanzamiento |
| ¿Se degrada el enlace inalámbrico de forma sistemática? | Se midió 15 ms / 0 % al empezar y 106 ms / 50 % a media sesión. Hace falta una medida repetida antes de fiarse de cualquier prueba que cruce la red |

---

## 7. Causa raíz: la orden `ros2` corría como `deepracer` y los nodos de AWS corren como `root`

Ninguno de los ocho veredictos preinscritos del §5 contemplaba este desenlace. Se deja constancia de
ello en vez de forzar el resultado dentro de una casilla que no le corresponde.

### 7.0 Esto ya estaba escrito en el repositorio, y aun así se repitió

Antes de nada, lo incómodo. [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §2 registra
exactamente el mismo fallo, con la misma pareja de corridas:

```
throttle=1.000   <- como 'deepracer': el carro NO se mueve
throttle=0.600   <- con sudo -i:      el carro SÍ se mueve
```

Y enuncia la regla: *«ningún extremo de un tópico vale si no comparte dueño con el otro — ni leyendo
ni publicando. Publicar con el dueño equivocado no da error: da silencio.»* Incluso anota el coste:
«todas las corridas de la tarde ejecutadas sin `sudo` no midieron nada, y se interpretaron como
fallos del vehículo».

La sesión del 2026-09-21 volvió a caer en ello y produjo un diagnóstico de avería sobre
`amss-jgm9`. La causa de la recaída es identificable: la regla está escrita en guías de **pasada de
mapeo y de localización**, no en el material de diagnóstico, y el vocabulario empleado —«dueño»—
no conecta con el síntoma que uno ve, que es un `SALIDA=124`.

Lo que esta sesión añade sobre S23 son dos cosas: **el mecanismo** (§7.3) y **una solución que no
exige privilegios** (§7.5). S23 dejó la regla como «hay que usar `sudo -i`»; hoy se mide que el
factor no es el usuario sino el transporte, y eso permite desplegar el nodo de coordinación sin
`root`.

### 7.1 Los síntomas, que eran uno solo

Durante dos sesiones se trataron como cinco problemas distintos:

| Síntoma | Cuándo se vio |
|---|---|
| `Node name: _NODE_NAME_UNKNOWN_` en los seis extremos del tópico | 2026-09-22, §4.1 |
| `ros2 node list` devuelve vacío, con `SALIDA=0` | 2026-09-21 y 2026-09-22 |
| `ros2 param list` responde `Node not found` de inmediato | 2026-09-22, §4.2 |
| Las llamadas a servicio se quedan en `waiting for service to become available` y expiran con 124 | 2026-09-21 y 2026-09-22 |
| `ros2 service list` y `ros2 topic info` funcionan con normalidad | Siempre |

### 7.2 La prueba que los explica todos

Misma máquina, mismo instante, mismo comando, sólo cambia el usuario:

```
$ ros2 node list --no-daemon          (usuario deepracer)
(vacío)                                SALIDA=0

# ros2 node list --no-daemon          (root)
/camera_pkg/camera
/deepracer_navigation_pkg/deepracer_navigation_node
/deepracer_systems_pkg/deepracer_systems_scripts_node
/deepracer_systems_pkg/model_loader_node
/deepracer_systems_pkg/network_monitor_node
/deepracer_systems_pkg/otg_control_node
/deepracer_systems_pkg/software_update_node
/device_info_pkg/device_info_node
/device_info_pkg/device_status_node
/i2c_pkg/battery_node
/inference_pkg/inference_node
/model_optimizer_pkg/model_optimizer_node
/rplidar_ros/rplidar_node
/sensor_fusion_pkg/sensor_fusion_node
/status_led_pkg/status_led_node
/usb_monitor_pkg/usb_monitor_node
/web_video_server/web_video_server
                                       SALIDA=0
```

Diecisiete nodos frente a cero. Y a continuación, como `root`, el control y la sonda que llevaban
dos sesiones expirando respondieron a la primera (§4.3).

### 7.3 El mecanismo, medido

```
$ ls -l /dev/shm | awk '{print $3}' | sort | uniq -c
      9 deepracer
    170 root

-rw-r--r-- 1 root root 549408 Sep 22 15:12 fastrtps_13222132fd599339
```

`deepracer-core.service` declara `User=root` (`/etc/systemd/system/deepracer-core.service`). Fast DDS
crea sus segmentos de memoria compartida con dueño `root` y permisos `0644`: el usuario `deepracer`
puede leerlos pero **no escribir en ellos**. El descubrimiento viaja por multidifusión UDP y por eso
los tópicos y los servicios se listan; el emparejamiento y la información de grafo de ROS 2 viajan
por los canales del participante, que en la misma máquina son memoria compartida, y por eso el grafo
de nodos está vacío y ningún cliente de servicio llega a emparejar.

No es una incompatibilidad de implementaciones DDS: ambos lados usan el mismo entorno
(`ROS_DISTRO=jazzy`, sin `RMW_IMPLEMENTATION`, sin `ROS_DOMAIN_ID`, sin `ROS_LOCALHOST_ONLY`, leído
de `/proc/684/environ`). Es un problema de permisos.

### 7.3.1 Confirmación del mecanismo, sin cambiar de usuario

Lo anterior es una explicación; esto es la medida que la sostiene. Se desactivó la memoria
compartida **sólo para el cliente**, dejándole únicamente transporte UDPv4, y se repitió todo como
usuario `deepracer`, sin `sudo`:

```
$ cat /tmp/udp_only.xml
<dds xmlns="http://www.eprosima.com"><profiles>
  <transport_descriptors><transport_descriptor>
    <transport_id>udp_only</transport_id><type>UDPv4</type>
  </transport_descriptor></transport_descriptors>
  <participant profile_name="p" is_default_profile="true"><rtps>
    <userTransports><transport_id>udp_only</transport_id></userTransports>
    <useBuiltinTransports>false</useBuiltinTransports>
  </rtps></participant>
</profiles></dds>

$ export FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/udp_only.xml
$ ros2 node list --no-daemon | wc -l
14                                      ← eran 0 con memoria compartida

$ ros2 service call /servo_pkg/get_calibration deepracer_interfaces_pkg/srv/GetCalibrationSrv '{cal_type: 0}'
response: max=1700000, mid=1450000, min=1300000, polarity=1, error=0
SALIDA=0                                ← expiraba con 124 con memoria compartida
```

Mismo usuario, mismo entorno, mismo comando: lo único que cambia es el transporte. Queda descartado
que el factor sea «ser `root`» y confirmado que es **el acceso a los segmentos de memoria
compartida**. Los 14 nodos frente a los 17 que ve `root` es diferencia de tiempo de descubrimiento,
no de permisos; no se ha investigado más porque no cambia la conclusión.

### 7.4 Qué queda invalidado

| Afirmación anterior | Estado |
|---|---|
| «`servo_pkg` no atiende a sus propios servicios» ([`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) §5) | **Sin sustento.** El `SALIDA=124` que la respaldaba se reproduce en un vehículo sano por el mero hecho de invocar como `deepracer` |
| «`i2c_pkg` responde con la misma receta de entorno, luego el entorno está descartado» (§8 del mismo documento) | **Invalidada como control.** Hoy `i2c_pkg` expiró igual, y respondió al cambiar de usuario |
| «`ctrl_pkg` no responde ni a `param get`» | **Sin sustento.** Mismo artefacto |
| «Ocho mensajes publicados y las ruedas no se movieron» | **Por revisar.** Si se publicaron desde el propio carro como `deepracer`, no llegaron a `servo_node`. Si se publicaron desde el portátil, el mecanismo del §7.3 no aplica y hace falta otra explicación |
| La avería de `amss-jgm9` | **Vuelve a estar abierta**, y ahora con un candidato barato que probar primero |

### 7.5 Consecuencia para el trabajo que queda

Cualquier proceso nuestro que deba hablar con la pila de AWS **en el mismo vehículo** no se
comunicará, y **no dará ningún error**: se quedará esperando indefinidamente. Esto afecta
directamente al nodo de coordinación y a cualquier cosa que publique en `/ctrl_pkg/servo_msg`.

Hay dos remedios, y **el segundo es el que adopta el proyecto**:

| Remedio | Cómo | Por qué |
|---|---|---|
| Correr como `root` | `sudo bash -c "source /opt/ros/jazzy/setup.bash; source /opt/aws/deepracer/lib/setup.bash; ros2 ..."` | Sirve para diagnosticar a mano. Como forma de desplegar nuestro código es mala: obliga a privilegios que el nodo de coordinación no necesita |
| Desactivar la memoria compartida en el cliente | `export FASTRTPS_DEFAULT_PROFILES_FILE=` apuntando al perfil del §7.3.1 | Sin privilegios, medido y reproducible. El coste es que la comunicación en la misma máquina pasa por UDP de bucle local en vez de memoria compartida, lo que penaliza el ancho de banda — irrelevante para mensajes de servo, a vigilar si alguna vez pasa imagen por ahí |

La alternativa de fondo — cambiar los permisos con que `deepracer-core` crea los segmentos — no se
toma: obligaría a modificar un servicio de AWS que se reinstala con cada actualización.

> **Corrección del mismo día, medida en el §9.2: esta tabla estaba mal.** El perfil solo-UDP sirve
> para **leer** servicios, pero **no basta para actuar**: publicando en `/ctrl_pkg/servo_msg` con el
> perfil y sin privilegios, el vehículo no se mueve, y sí lo hace con `root`. La frase de la fila
> primera —«privilegios que el nodo de coordinación no necesita»— **es falsa tal como está escrita**.
> El remedio que el proyecto adopta pasa a ser `root` para la ruta de actuación, y queda pendiente
> encontrar uno sin privilegios antes de desplegar el coordinador.

---

## 8. Contraprueba sobre `amss-jgm9`: la avería del 2026-09-21 no existe

Esta sección se añade el mismo día, tras cerrar el §7. Era la primera pregunta del §6 y resultó la
más barata de contestar: quince minutos y ningún montaje físico.

**Por qué se hace.** El 2026-09-21 se dio a `amss-jgm9` por averiado a partir de los mismos
`SALIDA=124` que el §7 acaba de explicar como artefacto de transporte. Si la causa es la misma, el
vehículo está sano y el proyecto recupera el segundo carro antes del corte del viernes. Si responde
igualmente mal con el transporte corregido, entonces sí hay algo que reparar y se sabe a tres días
del corte, no después.

**Predicción escrita antes de correr:** responde. Si no lo hubiera hecho, la avería quedaría
confirmada y el §7 no la explicaría.

### 8.1 Medición pareada, misma máquina y mismo minuto

Se instala el perfil del §7.3.1 en `/tmp/udp_only.xml` del propio vehículo y se pide la lista de
nodos dos veces, con y sin él. Todo como usuario `deepracer`, **sin `sudo`**.

| `ros2 node list` sobre `amss-jgm9` | Nodos |
|---|---|
| Sin perfil (memoria compartida) | **3** — `battery_node`, `rplidar_node`, `usb_monitor_node` |
| Con perfil solo-UDP | **21** |

Los 3 del caso degradado son justo los que en el §4.2 se habían tomado por «entorno sano»: el
control de batería del §4.2 medía uno de esos tres, y por eso no detectó nada.

**Atribución, que aquí es el punto delicado.** `ros2 node list` consulta el dominio entero, y el
`.102` estaba encendido con su pila activa — confundir eso costó la sesión del 2026-09-21. Los 21
nombres **no se repiten ni una vez**, y los dos vehículos corren la misma pila sin namespaces ni
`ROS_DOMAIN_ID`, de modo que ver a los dos produciría cada nombre duplicado. Además, `ps` sobre el
propio `.101` cuenta 24 procesos de nodo, cifra compatible con una sola pila. Los 21 son suyos.
De paso queda registrado que **desde `.101` no se ve a `.102`**, lo que apunta a las reglas `ufw`
por IP que siguen pendientes de limpieza.

### 8.2 Los dos nodos que «no aparecían» aparecen

Entre los 21 están `/ctrl_pkg/ctrl_node` y `/servo_pkg/servo_node`. La última pregunta abierta del
§6 —por qué no salían en la lista ni siquiera como `root`— **no tenía respuesta en el lanzamiento:
era un tercer síntoma de la misma causa.** Como `root` el §7.2 arregla los permisos pero sigue
usando memoria compartida; solo al quitar ese transporte aparece el grafo completo.

### 8.3 `servo_pkg` responde

```
# FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/udp_only.xml, usuario deepracer, sin sudo
# ros2 service call /servo_pkg/get_calibration ... '{cal_type: 0}'
response: max=1800000, mid=1320000, min=1200000, polarity=1, error=0
SALIDA=0

# ros2 service call /servo_pkg/get_calibration ... '{cal_type: 1}'
response: max=1603500, mid=1446000, min=1311000, polarity=-1, error=0
SALIDA=0
```

**Veredicto: `amss-jgm9` no tiene avería.** El nodo que se dio por caído responde a su propio
servicio con `error=0` en las dos calibraciones. Lo que falló el 2026-09-21 fue la medición.

El fichero `/opt/aws/deepracer/calibration.json` del vehículo confirma además la correspondencia de
`cal_type`, que hasta hoy se venía suponiendo: **`0` es `Servo` (dirección) y `1` es `Motor`
(tracción)**. Los valores del fichero coinciden exactamente con los que devuelve el servicio, luego
las etiquetas del §4.3 son correctas.

### 8.4 Una discrepancia que se deja anotada, no resuelta

La dirección de `amss-jgm9` calibra `1200000 / 1320000 / 1800000`, marcadamente asimétrica, mientras
que la de `amss-ez9n` da `1300000 / 1450000 / 1700000` (§4.3). La tracción, en cambio, es idéntica
en los dos vehículos. Ninguna de las dos cifras de dirección coincide con el
`1000000 / 1290000 / 2000000` que [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md)
registra como resultado de una recalibración. **No se interpreta aquí**: puede ser que aquella
recalibración se hiciera sobre otro vehículo, que se haya vuelto a tocar después, o que el registro
de S23 atribuyera mal la máquina, que es el error que este documento ya corrigió una vez. Antes de
usar cualquier número de dirección en una medida hay que releer la calibración del vehículo
concreto, no fiarse del documento.

### 8.5 Qué falta para cerrar la compuerta G-1 en este vehículo

Lo que el §8 prueba es que el vehículo **habla**. Que **actúe** —las cinco observaciones del §4.4—
no se ha comprobado, y no se comprueba sin el operador presente, por una razón de seguridad que ya
está documentada: `S23_campo_traccion_RF14.md` registra que **una sola orden de tracción movió los
dos carros**, porque comparten dominio y `/ctrl_pkg/servo_msg` no lleva namespace. Publicar en ese
tópico con los dos encendidos es un riesgo físico mientras no haya namespaces. La sonda sobre
`amss-jgm9` exige, por tanto: un solo vehículo encendido, carro en alto, batería de tracción
conectada y el operador delante.

---

## 9. Sonda de actuación sobre `amss-jgm9`, y la corrección que trae

Corrida el mismo día, con el operador delante, `amss-jgm9` en alto y **el `deepracer-core` del
`amss-ez9n` detenido por `systemctl`** — no apagado: el interruptor no corta la placa, y parar el
servicio quita su `servo_node` del grafo de forma reversible por `ssh`. El instrumento es el mismo
fichero que dio resultado en `amss-ez9n`, copiado y verificado por `md5sum`, no uno nuevo.

### 9.1 Cierre de la atribución, ahora sin depender de contar nombres

El §8.1 atribuyó a `amss-jgm9` sus 21 nodos contando que ningún nombre se repetía. **Ese argumento
no es fiable**, y se descubrió al repetir: `ros2 node list` devuelve 21, luego 15, luego 10 y luego
0 según la corrida, porque el descubrimiento con el perfil solo-UDP es lento y parcial, y el demonio
de `ros2` sirve además una vista caducada — hay que usar `--no-daemon`.

La atribución se rehízo con un criterio que no depende de la lista, **parando el `servo_pkg` del
otro vehículo**, de modo que solo un nodo en toda la red puede contestar:

| | Respuesta del servicio | `calibration.json` en disco |
|---|---|---|
| `amss-jgm9` | `1200000 / 1320000 / 1800000` | `1200000 / 1320000 / 1800000` ✓ |
| `amss-ez9n` | — (núcleo detenido) | `1300000 / 1450000 / 1700000` ✗ |

La respuesta coincide con el disco de `amss-jgm9` y **difiere** del de `amss-ez9n`. **Contestó
`amss-jgm9`**, y con ello el §8.3 queda confirmado por una vía mejor que la que lo escribió. De paso
se cierra la discrepancia que el §8.4 dejó anotada: los dos vehículos **tienen** calibraciones de
dirección distintas, y cada servicio devuelve la suya.

### 9.2 Cuatro corridas que separan dos factores, y desmienten un indicador

La sonda de dirección se lanzó cuatro veces variando dos cosas: el usuario y el tiempo de espera
entre crear el publicador y empezar a publicar.

| Corrida | Usuario | Espera | ¿Se movieron las ruedas? | Suscriptores que veía el publicador |
|---|---|---|---|---|
| 1 | `deepracer` + perfil solo-UDP | 2 s | **No** | 1 |
| 2 | `root` | 2 s | **No** | 1 |
| 3 | `root` | 5 s | **Sí** | 1 |
| 4 | `deepracer` + perfil solo-UDP | 5 s | **No** | 1 |

**Dos conclusiones, y la segunda es la incómoda.**

**(a) Hacen falta las dos condiciones a la vez: `root` y espera suficiente.** Ni el privilegio solo
(corrida 2) ni el tiempo solo (corrida 4) mueven el vehículo. La sonda original esperaba 2 s, que
alcanzaba en `amss-ez9n` y no aquí; se amplió a 6 s para la tracción.

**(b) `get_subscription_count()` marcó 1 en las cuatro, incluidas las tres que no movieron nada.**
Ese contador **no sirve como prueba de que el enlace funciona** — es exactamente el mismo género de
error que el §4.1 corrigió con los contadores de publicadores, reaparecido en otro contador. Se dejó
escrito antes de seguir: cualquier verificación futura del enlace tiene que observar el efecto, no
el contador.

**(c) Esto corrige el §7.5.** Allí se adoptó el perfil solo-UDP como remedio del proyecto y se
concluyó que «el factor es el transporte, no el usuario, luego el nodo de coordinación no necesitará
`root`». Para **leer servicios** eso sigue siendo cierto y está medido. Para **actuar** es falso: la
corrida 4 publica con el perfil, sin privilegios, ve su suscriptor, y el carro no se mueve.
**Mientras no aparezca otro remedio, la ruta de actuación del coordinador necesita `root`**, y eso
es un requisito de despliegue que hay que resolver antes de la demostración, no durante.

### 9.3 Las cinco observaciones, y la compuerta

Con `root` y 6 s de espera, sobre `amss-jgm9` en alto:

| # | Observación | Resultado |
|---|---|---|
| 1 | Las ruedas delanteras giran a izquierda y a derecha y vuelven al centro | **Sí** |
| 2 | Las ruedas traseras giran hacia adelante a `throttle 0,60` | **Sí** |
| 3 | Paran al recibir `0,00` | **Sí** |
| 4 | Giran hacia atrás a `throttle −0,60` | **Sí** |
| 5 | La parada final es inmediata, por debajo de 1 s | **Sí** |

**Veredicto: la compuerta G-1 de [`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md) §4 queda ALCANZADA también
sobre `amss-jgm9`.** Es la primera de las seis compuertas del GO pleno que se cierra en los **dos**
vehículos, y se cierra tres días antes del corte C-0.

### 9.4 Regla de seguridad que esta corrida ejerció

`S23_campo_traccion_RF14.md` registra que una sola orden de tracción movió los dos carros, porque
comparten dominio y `/ctrl_pkg/servo_msg` no lleva namespace. Aquí se respetó **deteniendo el
servicio del otro vehículo**, no apagándolo, y verificando por `ps` que su `servo_node` había
desaparecido antes de publicar. Al terminar se restituyó con `systemctl start` y se comprobó que
volvía a `active`. **Ese es el procedimiento mientras no existan namespaces**, y es más barato y más
reversible que apagar una placa.
