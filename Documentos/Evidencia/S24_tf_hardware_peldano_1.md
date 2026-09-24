# El vehículo publica TF por primera vez: `base_link → laser` medido contra flexómetro

*Tarea 1.1 del `MAPA_TRABAJO_RESTANTE.md`. Carro `.101` (`amss-jgm9`), 2026-09-21.*

## 0. La pregunta

La escalera de Nav2 tiene siete peldaños y el primero es TF. Hasta hoy nadie había comprobado
si la tarjeta del vehículo podía siquiera subir ese peldaño. La pregunta no era si el URDF de
simulación es correcto —eso ya se sabe—, sino si **describe el carro que está sobre la mesa**,
y si la tarjeta tiene con qué publicarlo.

## 1. Lo que faltaba: la imagen de Jazzy no trae TF

La instalación de ROS 2 de la tarjeta es mínima. `/opt/ros/jazzy/share` contiene **194
paquetes**, y entre ellos no están ni `robot_state_publisher` ni `tf2_ros`:

```
$ ros2 pkg prefix robot_state_publisher
Package not found
$ ros2 pkg prefix tf2_ros
Package not found
```

Esto no es un detalle de instalación: es el riesgo **R8** haciéndose concreto. El mapa preveía
que compilar `deepracer_bringup` fallaría por incompatibilidades de código; el primer fallo real
es más simple y más barato de arreglar — **faltan paquetes base**. Conviene anotarlo porque
cambia lo que hay que esperar de la tarea 1.2.

## 2. La instalación, y por qué era segura

El peligro en un dispositivo de producción no es instalar paquetes nuevos: es que `apt`
**actualice** un `rclcpp` o un `rcl` contra el que `deepracer-core` está compilado. Por eso se
pidió una simulación antes de tocar nada, y la línea que la cierra es inequívoca:

```
0 upgraded, 14 newly installed, 0 to remove and 325 not upgraded.
```

Cero actualizados. La instalación es **puramente aditiva y reversible** con `apt remove`. Los
325 pendientes se dejan deliberadamente donde están.

Apareció, eso sí, un bloqueo que no estaba en el mapa: **el disco**. La tarjeta estaba al 98 %
con 151 MB libres sobre 7,7 GB. El desglose localizó la causa y resultó ser basura, no sistema:

| Directorio | Ocupa | ¿Recuperable? |
|---|---|---|
| `/var/cache/apt/archives` | **939 MB** | Sí, son `.deb` ya instalados |
| `/opt/aws/deepracer/logs` | 3,4 MB | Irrelevante |
| El home del usuario `deepracer` | 262 MB | No sin revisar |

Un `apt-get clean` llevó el disco de 151 MB a **1,2 GB libres** (98 % → 85 %), contra los
**17,1 MB** que pedía la instalación. El bloqueo era caché muerta.

> **Pendiente:** el carro `.102` no se ha tocado. Se deja intacto como clon de control, para
> tener una máquina sana con la que comparar si algo se estropea en `.101`. Antes de grabar
> bags con los dos habrá que repetir limpieza e instalación allí.

## 3. El URDF se genera en el portátil, no en la tarjeta

El mapa proponía procesar el xacro en el vehículo. Eso obliga a instalar `deepracer_description`
allí, con sus mallas y sus dependencias de Gazebo. **No hace falta:** `robot_state_publisher`
no abre mallas, solo lee la cinemática. Generando el URDF plano en el portátil y copiándolo, la
tarea 1.1 deja de depender de la 1.2.

```
xacro $(ros2 pkg prefix deepracer_description)/share/deepracer_description/models/xacro/deepracer/deepracer.xacro sensor_type:=stereo_cameras_and_lidar lidar_360_degree_sample:=1328 lidar_360_degree_min_angle:=-3.14159 lidar_360_degree_max_angle:=3.14159 lidar_360_degree_max_range:=16.0 > /tmp/deepracer_hw.urdf
```

Resultado: 565 líneas, **14 links, 13 joints, 20 bloques `<gazebo>`**. Copiado a la tarjeta con
`scp` como `~/deepracer_hw.urdf` en el home del usuario `deepracer` de la tarjeta.

**Corrección al mapa.** El mapa pedía pasar los parámetros del LiDAR real «para cerrar el
peldaño 1». Leyendo el xacro se ve que no es así: `lidar_360_degree_*` aterriza dentro de
`<gazebo><sensor>`, y **en hardware ese bloque es inerte** — lo lee Gazebo, nadie más. Lo que
coloca el sensor es `hokuyo_joint`, que está escrito a mano en el xacro y no depende de ningún
argumento. Pasar los parámetros sigue valiendo la pena por fidelidad del modelo, pero **no es
lo que cierra el peldaño**.

## 4. La medida del árbol TF

Con `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` para dejar fuera al otro carro y al PC:

```
$ ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat ~/deepracer_hw.urdf)" &
$ ros2 run tf2_ros tf2_echo base_link laser
At time 0.0
- Translation: [0.029, 0.000, 0.185]
- Rotation: in RPY (degree) [0.000, -0.000, -180.000]
```

Contra el cálculo a mano sobre el xacro:

| Componente | Origen en el xacro | Aporte en Z |
|---|---|---|
| `base_link_joint` (`base_link → chassis`) | `xyz="0 0 0.023249"` | 0,023249 m |
| `hokuyo_joint` (`chassis → laser`) | `xyz="0.02913 0 0.16145"`, `rpy="0 0 3.1416"` | 0,161450 m |
| **Total `base_link → laser`** | | **0,184699 m** |

Coincide con los 0,185 publicados, y el `yaw` de π explica los −180°: **el LiDAR está montado
mirando hacia atrás**, algo que el número solo confirma pero que el xacro ya declaraba.

Dos detalles de lectura que conviene dejar escritos para no perder tiempo la próxima vez:

- El `Invalid frame ID "base_link"` de la primera línea es una carrera de arranque, no un fallo:
  `tf2_echo` se suscribió antes de que llegara `/tf_static`. Se resuelve solo.
- `At time 0.0` es la firma de una transformada **estática**. ~~Los trece joints del URDF son
  fijos~~, así que todo viaja por `/tf_static` y nada depende de `joint_states` — que la tarjeta
  no publica. Es justo lo que permite cerrar 1.1 sin ruedas girando.

  > **Corrección del 2026-09-24: la afirmación tachada es falsa, y la conclusión se sostiene
  > igual.** De los trece joints, **siete son `fixed` y seis son `continuous`** —las cuatro ruedas
  > y las dos bisagras de dirección: `left/right_rear_wheel_joint`,
  > `left/right_front_wheel_joint`, `left/right_steering_hinge_joint`—. Se comprueba contando
  > `type="continuous"` en `deepracer_stereo_cameras_and_lidar_urdf.xacro`, que es el xacro del
  > que se generó este URDF plano. **Lo que no cambia es el cierre del peldaño 1**, porque la
  > rama que se midió —`base_link → chassis → laser`— sí es enteramente fija y sí viaja por
  > `/tf_static`; el `At time 0.0` que se observó es correcto y significa lo que dice. **Lo que
  > sí cambia es el diagnóstico del árbol completo:** las seis juntas móviles quedan sin publicar
  > para siempre, porque el vehículo no tiene encoders y nadie emite `/joint_states`. Por eso el
  > URDF versionado el 24-sep —`deepracer_hardware.urdf`— **no las declara**: declara solo los
  > tres eslabones y las dos juntas fijas que el hardware realmente tiene.

## 5. El flexómetro, y un error de instrucción que casi se atribuye al robot

La primera medida dio **189–190 mm** contra los **175,7 mm** calculados: +13 mm, fuera de la
tolerancia de ±3 mm fijada de antemano. Antes de corregir el xacro se descompuso la medida en
dos partes comprobables por separado, y resultó que el error estaba en la instrucción:

| Medida | Esperado | Medido | Veredicto |
|---|---|---|---|
| Diámetro de rueda | 60,0 mm | 59–60 mm | El radio de 0,03 m del xacro acierta |
| Piso → ranura del rayo láser | 175,7 mm | **175 mm** | Coincide, 0,7 mm de diferencia |
| Piso → punto más alto del carro | (no aplica) | 189–190 mm | **Era esto lo que se midió primero** |

Los 175,7 mm esperados salen de restar a los 184,699 mm del sensor sobre `base_link` los
8,999 mm que `base_link` queda sobre el piso: eje de rueda a 0,023249 + 0,01575 = 0,038999 m,
menos el radio de 0,03 m.

El instrumento no mintió y el robot tampoco: **la instrucción pedía medir «a la cara superior
del disco», que es la altura total del vehículo, no el plano óptico**. Se anota porque el modo
de fallo —una discrepancia real de 13 mm atribuida al modelo cuando venía del procedimiento—
es exactamente el que produce correcciones espurias en un URDF.

## 6. Hallazgo colateral: el error de deserialización viene de la red

El viernes, `tf2_echo` en el PC producía `sequence size exceeds remaining buffer` de forma
repetida y sin explicación. Hoy, con `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` en la tarjeta,
**el error no apareció ni una vez** en once lecturas consecutivas.

Eso es evidencia, no ausencia de evidencia: aislando la máquina el error desaparece, luego el
mensaje malformado **venía de la red** —el PC con Humble o el otro carro con Jazzy—, no de la
máquina local. La hipótesis de incompatibilidad DDS Humble↔Jazzy sobre el dominio 0 compartido
gana peso, pero **sigue sin confirmarse**: falta la prueba desde el PC. Importa porque toca el
núcleo del sistema colaborativo, donde el coordinador y los vehículos tienen que hablarse.

## 7. Qué queda cerrado y qué no

**Cerrado.** El peldaño 1 de la escalera de Nav2 está de pie en hardware: la tarjeta publica un
árbol TF con `base_link` y `laser`, y la transformada entre ellos coincide con el vehículo
físico dentro de 1 mm. El URDF de simulación describe el carro real.

**No cerrado.** El peldaño 2 —odometría— sigue sin existir en hardware, y es el que la tarea
1.3 empieza a atacar. El árbol de hoy es estático: no hay `odom → base_link` porque no hay quien
lo publique.

## 8. Trazabilidad

| Afirmación | Fuente |
|---|---|
| La imagen de Jazzy no trae `robot_state_publisher` ni `tf2_ros` | `ros2 pkg prefix`, 2026-09-21 |
| 194 paquetes en la instalación de la tarjeta | `ls /opt/ros/jazzy/share \| wc -l` |
| La instalación no actualiza nada del stack de fábrica | `apt-get install -s`, línea `0 upgraded` |
| 939 MB recuperables en la caché de apt | `du -sh /var/cache/apt/archives` |
| Disco de 151 MB a 1,2 GB libres | `df -h /` antes y después de `apt-get clean` |
| `base_link → laser` = `[0.029, 0.000, 0.185]`, yaw −180° | `tf2_echo`, carro `.101` |
| Los parámetros del LiDAR son inertes en hardware | `deepracer.xacro` y el bloque `<gazebo><sensor>` |
| Altura real del plano del láser: 175 mm | Flexómetro, carro `.101` |
| Diámetro real de rueda: 59–60 mm | Flexómetro, carro `.101` |
| El error de buffer desaparece bajo aislamiento | Once lecturas de `tf2_echo` sin incidencia |
