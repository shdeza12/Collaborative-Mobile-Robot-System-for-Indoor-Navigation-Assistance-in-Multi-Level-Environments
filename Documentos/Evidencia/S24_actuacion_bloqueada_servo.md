# RF-11 no se mide por `/cmd_vel`: el vehículo no tiene ese tópico, y `servo_pkg` dejó de atender

*Tarea 1.3 del `MAPA_TRABAJO_RESTANTE.md`. Carro `.101` (`amss-jgm9`), 2026-09-21.
Este documento **no cierra la tarea**: la deja acotada y deja una anomalía abierta con nombre.*

## 0. La pregunta y lo que la respondió

La tarea 1.3 decía que RF-11 «no depende de nada»: publicar en `/<ns>/cmd_vel`, medir con
flexómetro, cerrar. La primera comprobación la desmontó. **El vehículo no publica ni escucha
`/cmd_vel`.** De los 21 tópicos que expone `deepracer-core`, los que mandan sobre los actuadores
son otros dos:

| Tópico | Tipo | Quién publica | Quién escucha |
|---|---|---|---|
| `/ctrl_pkg/servo_msg` | `deepracer_interfaces_pkg/msg/ServoCtrlMsg` | `ctrl_pkg` | `servo_pkg` |
| `/ctrl_pkg/raw_pwm` | `ServoCtrlMsg` | `ctrl_pkg` | `servo_pkg` |

`ros2 topic info /ctrl_pkg/servo_msg` da `Publisher count: 2` y `Subscription count: 1`. El 2 no
es un error: son los **dos carros encendidos viéndose en el dominio 0**, el mismo solapamiento que
el Bloque 0 ya había anotado. Cualquier medida tomada con ambos encendidos está contaminada
mientras no haya espacios de nombres.

## 1. El mensaje no habla en unidades físicas

```
$ ros2 interface show deepracer_interfaces_pkg/msg/ServoCtrlMsg
float32 angle
float32 throttle
builtin_interfaces/Time source_stamp
```

`angle` y `throttle` son **razones**, no radianes ni metros por segundo: se interpretan contra los
límites guardados en el fichero de calibración del vehículo. Esto tiene una consecuencia directa
sobre RF-11 que el mapa no preveía: **el recorrido medido depende de la calibración almacenada**,
así que la calibración es parte del dato, no del entorno. La única lectura que conseguimos
—`servo_pkg` respondió una sola vez en toda la sesión— fue la de dirección:

```
max=1700000  mid=1450000  min=1300000  polarity=1
```

## 2. Cómo hablarle a la API de AWS sin cegar la CLI

`deepracer_interfaces_pkg` vive fuera de `/opt/ros/jazzy`, en el árbol de AWS. Hacer `source` de
`/opt/aws/deepracer/lib/setup.bash` funciona pero arrastra un entorno que dejó al demonio de
descubrimiento sin ver nada. La receta mínima, con tres variables y sin `source`, es:

```
AMENT_PREFIX_PATH=/opt/aws/deepracer/lib/deepracer_interfaces_pkg:$AMENT_PREFIX_PATH
LD_LIBRARY_PATH=/opt/aws/deepracer/lib/deepracer_interfaces_pkg/lib:$LD_LIBRARY_PATH
PYTHONPATH=/opt/aws/deepracer/lib/deepracer_interfaces_pkg/lib/python3.12/site-packages:$PYTHONPATH
```

Con matiz, porque costó dos pasos averiguarlo: `ros2 interface show` se conforma con `AMENT`
—solo lee el `share/`—, pero `ros2 service call` **necesita además el módulo de Python**, y sin
`PYTHONPATH` falla con `The passed service type is invalid`, que es un mensaje que no apunta a su
causa. Conviene dejarlo escrito para no volver a perseguirlo.

## 3. Quién contesta y quién no

Se interrogó a los tres paquetes por sus propios servicios, con el carro recién arrancado y el
grafo sano. `SALIDA=124` es el código de `timeout`: la llamada se quedó esperando.

| Paquete | Servicio probado | Resultado |
|---|---|---|
| `i2c_pkg` | `battery_level` | **`level=7`, `SALIDA=0`** |
| `servo_pkg` | `get_calibration` | Una vez `SALIDA=0`; **después, siempre `SALIDA=124`** |
| `ctrl_pkg` | `get_ctrl_modes`, `vehicle_state`, y sus servicios de parámetros | **Siempre `SALIDA=124`** |

Dos lecturas que importan:

- **`ctrl_node` no contesta ni a sus servicios de parámetros.** Eso no es un nodo ocupado: los
  servicios de parámetros los sirve `rclpy` en el mismo ejecutor. Un nodo que no responde a
  `param get` tiene el ejecutor tomado, no la lógica ocupada.
- **`i2c_pkg` sí contesta, y se recupera solo.** Es el control que impide culpar al bus I²C o al
  entorno: por el mismo camino, con las mismas variables, una llamada vuelve y las otras no.

## 4. La publicación llega y las ruedas no se mueven

Con las variables puestas y `servo_pkg` suscrito, se publicaron **ocho mensajes** en
`/ctrl_pkg/servo_msg`. `ros2 topic pub` los contó y los dio por enviados. El veredicto del usuario,
mirando el carro, fue el mismo las tres veces que se intentó: **«no giraron las ruedas»**.

El fallo, por tanto, no está en el tópico ni en el tipo ni en el entorno: está **detrás del
suscriptor**. `servo_pkg` recibe y no actúa, y tampoco atiende a sus propios servicios.

## 5. La anomalía, con su historia

El corte es datable. `servo_pkg` respondió mientras el carro tenía **alimentación de tracción**.
El DeepRacer tiene dos alimentaciones independientes:

| Alimentación | Qué sostiene | Qué pasa si falta |
|---|---|---|
| Cómputo | `ssh`, `deepracer-core`, el grafo ROS | Nada de esto se vio caer |
| Tracción | Servo y motor, y el bus I²C que los manda | Los nodos dependientes del bus expiran |

Durante la sesión se perdió la alimentación de tracción —el carro se apagó sin querer y hubo que
reasentar la batería—. Desde ese momento:

- `i2c_pkg` **se recuperó solo** en cuanto volvió la corriente.
- `servo_pkg` **no**, y no lo hizo tras `systemctl restart deepracer-core`, ni tras un
  `sudo reboot` completo, ni tras reasentar la batería de tracción.

Lo que el sistema dice de sí mismo no ayuda: el servicio está `active`, con **`NRestarts=0` desde
el 2026-09-17**, los ocho procesos de nodo están en `ps`, y el diario de systemd está
**completamente limpio** —Intel Atom E3930, 4 GB, CPU entre 15 % y 65 %, 41–42 °C, disco al 14 %—.
No hay traza, ni excepción, ni reinicio. El fallo es silencioso.

**Esto se anota como anomalía abierta, no como diagnóstico.** Sabemos cuándo empezó y qué no lo
arregla; no sabemos por qué. Y tiene una consecuencia de diseño que va más allá de RF-11: **si
perder la tracción a mitad de sesión deja el vehículo inservible hasta algo más que un reinicio de
servicio, las corridas largas con dos carros del Bloque 2 necesitan un procedimiento de batería, no
buena suerte.**

## 6. Hallazgo de método: `ros2 node list` no es fiable en las tarjetas

En la misma sesión, `ros2 node list` devolvió **0** mientras `ros2 service list -t` devolvía sus
**186** entradas completas y correctas, y en llamadas consecutivas osciló entre **21 y 0** sin que
cambiara nada en el vehículo. Es la misma familia de fallo que `GUIA_PASADA_MAPEO.md` §2.5 ya
documentaba para el demonio —«puede romperse sin morir, y entonces miente»—, pero afecta a un
comando que esa sección todavía daba por bueno.

La regla operativa que se deriva: **contar nodos no sirve como métrica de salud del grafo en estas
tarjetas. Se cuentan tópicos o servicios.** La guía queda corregida en consecuencia.

Esto costó caro en la sesión: tres hipótesis se persiguieron sobre una comparación inválida —un
recuento de tópicos leído como si fuera de nodos—. Se anota porque el modo de fallo no es del
robot, es de la instrumentación con la que se le mira.

## 7. Qué queda cerrado y qué no

**Cerrado.** La cadena de actuación real está mapeada y es trazable: `ctrl_pkg` →
`/ctrl_pkg/servo_msg` (`ServoCtrlMsg`, razones) → `servo_pkg` → servo. La receta de entorno para
hablarle está escrita. La calibración de dirección está leída. Y **la redacción de la tarea 1.3
queda corregida: RF-11 no se mide por `/cmd_vel`, porque ese tópico no existe en el vehículo.**

**No cerrado.** RF-11 no se ha medido. El recorrido no puede medirse mientras `servo_pkg` no
atienda, y eso no depende de lo que publiquemos. Queda además sin confirmar la hipótesis de
incompatibilidad DDS Humble↔Jazzy sobre el dominio 0 compartido: falta la prueba desde el PC.

**Lo siguiente, en este orden.** Repetir la interrogación en el carro `.102`, intacto: si allí
`servo_pkg` contesta, el fallo es de estado del `.101` y no de la imagen, y RF-11 se mide en el
`.102` sin esperar a entender el `.101`. Es la única prueba que separa las dos explicaciones, y no
requiere tocar nada.

## 8. Trazabilidad

| Afirmación | Fuente |
|---|---|
| El vehículo no tiene `/cmd_vel`; expone 21 tópicos | `ros2 topic list`, carro `.101`, 2026-09-21 |
| La cadena real es `/ctrl_pkg/servo_msg` → `servo_pkg` | `ros2 topic info`, `ros2 service list -t` |
| `ServoCtrlMsg` son razones, no unidades físicas | `ros2 interface show deepracer_interfaces_pkg/msg/ServoCtrlMsg` |
| Dos publicadores sobre un tópico de un solo carro | `ros2 topic info /ctrl_pkg/servo_msg`, con los dos carros encendidos |
| `service call` necesita `PYTHONPATH`; `interface show` no | Dos llamadas idénticas salvo esa variable |
| Calibración de dirección `1300000 / 1450000 / 1700000`, polaridad 1 | `get_calibration`, única respuesta de `servo_pkg` |
| `i2c_pkg` responde (`level=7`) con el mismo entorno | `battery_level`, `SALIDA=0` |
| `ctrl_pkg` no responde ni a `param get` | `SALIDA=124` repetido |
| Ocho mensajes publicados sin movimiento | `ros2 topic pub` y observación directa del vehículo |
| El fallo sobrevive a `restart`, `reboot` y reasentar batería | Tres intentos, carro `.101` |
| Servicio `active`, `NRestarts=0`, diario limpio | `systemctl show`, `journalctl` |
| `ros2 node list` devuelve 0 y 21 alternadamente | Llamadas consecutivas contra `service list -t` estable en 186 |
