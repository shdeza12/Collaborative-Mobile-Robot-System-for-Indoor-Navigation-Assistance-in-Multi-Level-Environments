# S24 — Dejar los dos carros listos para la pasada de odometría

**Fecha:** 2026-09-23 (miércoles, S24 de 32)
**Vehículos:** `amss-jgm9` (192.168.0.101) y `amss-ez9n` (192.168.0.102)
**Motivo:** los carros solo están disponibles entre semana. En vez de preparar uno
y volver otro día por el segundo, se dejan los dos en el mismo estado, de forma
que el día que llegue la decisión de sitio (§6 del acta) se salga a medir sin
preparar nada.

---

## 1. Qué se cierra y qué no

| Punto | `.101` | `.102` | Cómo se comprobó |
|---|---|---|---|
| Peldaño 1 — `base_link → laser` | cerrado | **cerrado hoy** | `tf2_echo base_link laser` |
| `/rplidar_ros/scan` publica con datos | sí | sí | suscriptor `rclpy`, §3 |
| Graba un `.mcap` no vacío | sí (516 208 B) | sí (578 935 B) | tamaño ≫ 5123 B de mcap vacío |
| El bag se lee en el PC Humble | — | **sí**, §4 | `SequentialReader.read_next()` |
| Batería | nivel 9 | nivel 9 | `/i2c_pkg/battery_level` |
| Flexómetro contra el URDF | hecho 21-sep, **caducado** | pendiente | ver el recuadro de §2.1 |

El criterio de cierre de la sesión se da por cumplido en todo lo que depende del
software. La geometría, en cambio, **volvió a quedar abierta el mismo día**: se
retiró el caparazón de los vehículos, lo que caduca la medida del 21-sep y obliga
a re-medir los dos carros. El recuadro al final de §2.1 lo explica.

Si se hace: piso → la **ranura por donde sale el haz**, esperado
**175 mm ± 3 mm**. No es la cara superior de la carcasa (189–190 mm); esa
confusión ya costó una medida el 21-sep y está anotada en
`S24_tf_hardware_peldano_1.md` §5.

---

## 2. Las dos tarjetas no son clones

Se creía que los dos vehículos eran instalaciones idénticas. No lo son.

| | `.101` `amss-jgm9` | `.102` `amss-ez9n` |
|---|---|---|
| Disco | 7,7 GB al 89 % (883 MB libres) | 29 GB al 33 % |
| Paquetes ROS | 208 | 222 |
| `robot_state_publisher`, `tf2_ros` | hubo que instalarlos (21-sep) | ya venían |

**Por qué importa.** RF-16 pide «el mismo código en los dos destinos». El código
sí es el mismo — el URDF generado en el PC tiene md5 `ccd781f4e4b519c1de721ccbae21ba20`
y es byte a byte el que está en las dos tarjetas —, pero el **entorno** no lo es.
Cualquier procedimiento que dependa de un paquete presente se cumplirá en `.102`
y fallará en `.101`, y los 883 MB libres de `.101` son además un margen que se
está estrechando solo (1,2 GB el 21-sep).

`base_link → laser` sale igual en los dos: `[0.029, 0.000, 0.185]`, RPY −180°.

**La divergencia es solo de instalación de software.** El hardware es el mismo
en los dos vehículos —mismas cámaras, ruedas, motores, baterías—, según el
tesista, que los tiene en mano. Eso acota el hallazgo: lo que difiere es lo que
se instaló encima, no la máquina.

### 2.1 · Por qué el flexómetro en `.102` no es una compuerta

El TF sale idéntico en los dos carros **por construcción, no por medición**: es
el mismo URDF copiado a las dos tarjetas. Que `tf2_echo` conteste
`[0.029, 0.000, 0.185]` en `.102` no dice nada de ese carro; dice que lee el
mismo archivo. La única medida física que existe —175 mm— se tomó en `.101`.

Con las piezas iguales, lo único expuesto es el **montaje**. Y los tres números
del URDF no pesan lo mismo:

| Parámetro | Lo comprueba | Cuánto pesa |
|---|---|---|
| z = 0,185 m | el flexómetro | **poco**: el plano del láser es horizontal; unos mm no mueven un SLAM 2D |
| x = 0,029 m | flexómetro, lateral | poco, mismo motivo |
| yaw = −180° | **nada de lo que había planeado** | **mucho**: un error de yaw rota *todos* los barridos |

O sea que el flexómetro comprueba el parámetro que menos importa, y el que sí
importa no estaba en la lista de nadie.

Aun así el riesgo de yaw es bajo, por una razón concreta: **el LiDAR va sobre un
soporte fijo atornillado**. No admite un ángulo arbitrario — o está asentado o
no. El fallo realista no es «rotado 7°» sino «montado al revés», que es discreto,
se ve a simple vista y saltaría en el primer mapa.

Dos indicios más en la misma dirección, medidos hoy: los dos carros devuelven
`angle_min` −3,124 y `angle_max` 3,1416 con 360 muestras, idénticos. Eso no
prueba el montaje físico, pero sí que los dos drivers están configurados igual,
que era el otro sitio por donde podía entrar una asimetría.

**Decisión:** la comprobación de verdad llega gratis con la primera pasada. Si el
barrido de `.102` en un pasillo conocido sale rotado respecto al de `.101`, se
nota de inmediato. Hasta entonces no se gasta una salida de campo en esto.

> **REVERTIDO el mismo 2026-09-23, horas después.** Se decidió **retirar el
> caparazón** de los vehículos para que el LiDAR lea los 360° sin obstrucción.
> Eso cambia la premisa entera de este apartado: los 175 mm se midieron **con el
> caparazón puesto**, así que si el soporte del LiDAR se apoyaba en él, el URDF
> describe una configuración que ya no existe.
>
> El flexómetro vuelve a ser **obligatorio, y en los dos carros**, no solo en el
> `.102`. Procedimiento en `GUION_RECTA_PELDANO2.md` §1.
>
> Lo que sigue valiendo de este apartado es el orden de importancia de los tres
> parámetros —el yaw pesa mucho más que la altura y el flexómetro no lo ve— y la
> observación de que el soporte atornillado hace el fallo discreto. Lo que ya no
> vale es la conclusión de no gastar una salida en medirlo.

### 2.2 · Se intentó medir el efecto del caparazón, y no se pudo concluir

> **RETIRADO ENTERO — ver §5.3.** El «antes» de esta comparación es el bag
> `bag_ez9n`, que resultó estar **contaminado por el LiDAR del otro vehículo**.
> El 71,1 % no es la fracción de rayos válidos del `.102`: es la de los dos
> carros mezclados. La conclusión de abajo —*no concluyente*— sigue siendo
> correcta, pero por una razón más grave que la que se escribió, y ninguna de
> las cifras del párrafo siguiente se puede citar.

Retirar el caparazón debería aumentar los rayos válidos. Se intentó cuantificar
comparando el barrido de antes (191 barridos) con uno nuevo de después (71), los
dos en el `.102`.

En bruto sube: **71,1 % → 74,7 %** de rayos válidos. **Ese número no vale.** Entre
las dos grabaciones el carro se movió a un sitio más cerrado —la mediana pasó de
2,2 m a 1,47 m y el alcance máximo de 12 m a 7,1 m—, y un espacio estrecho sube
la fracción de válidos por sí solo.

La distribución angular tampoco discrimina. Un bloqueo retirado daría uno o dos
sectores contiguos cayendo fuerte y el resto casi quieto; lo que hay son deltas
en los dos sentidos (−20,8 en −120..−90, pero +10,7 en −30..0 y +10,2 en 90..120),
que es la firma de un cambio de escena. El −20,8 aislado y rodeado de subidas se
explica mejor por una pared más cercana que por desbloqueo.

**Conclusión: no concluyente.** No se afirma que quitar el caparazón mejore la
lectura; se afirma que la medición hecha no puede decidirlo. El experimento
limpio —mismo carro, misma posición, con y sin caparazón— se propuso y se
descartó por tiempo.

Esto no bloquea nada: la fracción de rayos con **información de avance**, que es
la cifra que decide G-2, se re-mide igual en la recta del peldaño 2. Queda
escrito para que el cambio de hardware a mitad de campaña no aparezca como un
supuesto sin respaldo.

---

## 3. `/rplidar_ros/scan` no está vacío — corrección a la hoja de campo

`HOJA_CAMPO_G2.md:185` afirma que `/rplidar_ros/scan` «va a aparecer en la lista
de tópicos, **y está vacío**», y la línea 190 recomienda no perder tiempo
intentando grabarlo. **Las dos afirmaciones son falsas** y hoy se comprobaron en
los dos vehículos.

El tópico publica a **7,6–9,9 Hz** con datos reales:

| | `.101` | `.102` |
|---|---|---|
| `frame_id` | `laser` | `laser` |
| Muestras por barrido | 360 | 360 |
| Apertura | 359° | 359° |
| Rango declarado | 0,15 – 12,0 m | 0,15 – 12,0 m |
| Rayos válidos | 248 (68,9 %) | 256 (71,1 %) |
| Mediana | ≈ 2,2 m | ≈ 2,2 m |

El puerto lo tiene abierto el PID 717 `rplidar_node`, que es el driver de fábrica
de AWS y arranca con `deepracer-core`.

**Consecuencia buena:** la pasada de odometría **no necesita disputar el puerto
serie ni parar `deepracer-core`**. Se graba lo que ya está publicando.

**Consecuencia mala, y hay que tenerla presente al leer los resultados:** son
**360 muestras y 12 m**, no las **1328 muestras y 16 m** del driver del proyecto.
Son **3,7× menos resolución angular** y 4 m menos de alcance. Eso afecta a rf2o y
afecta a los índices de información de avance de `S23_informacion_avance_piso2.md`,
que se calcularon con la geometría densa. Un índice medido sobre este barrido no
es comparable sin más con el 5,1 % / 5,9 % / 17,5 % ya publicados.

---

## 4. El bag de Jazzy se lee en Humble — el problema ya estaba resuelto

Al copiar el bag de `.102` al PC, `ros2 bag info` falló:

    Exception on parsing info file: yaml-cpp: error at line 15, column 11: bad conversion

Es la incompatibilidad de `metadata.yaml` entre Jazzy (versión 9) y Humble
(versión 5): `offered_qos_profiles` es una secuencia YAML allá y una cadena acá.
**Esto ya estaba diagnosticado y resuelto desde el 2026-09-01** en
`herramientas/adaptar_bag_jazzy.py`. No hacía falta volver a diagnosticarlo; se
perdió tiempo por no consultar primero la herramienta que ya existía.

Lo que sí aporta hoy es la comprobación de que la cadena sigue viva con un bag
nuevo, y hecha como el propio guion exige — leyendo un mensaje, no con
`ros2 bag info`:

```
python3 herramientas/adaptar_bag_jazzy.py bag_ez9n -o bag_ez9n_humble
```

`SequentialReader.read_next()` sobre el resultado devuelve
`/rplidar_ros/scan`, `frame_id: laser`, 360 muestras, 249 válidas, 0,15–12,00 m.
El `.mcap` no se copia: el adaptador deja un enlace simbólico al original, así
que la evidencia del carro no se duplica ni se toca.

**El campo que el traductor borra.** De cada tópico quita `type_description_hash`,
que es justamente el que Jazzy añadió para detectar que la definición de un
mensaje divergió entre distros. Al quitarlo se pierde esa red: un tipo divergente
daría un bag que se abre y **deserializa mal en silencio**. No se puede conservar
—Humble no conoce el campo—, así que la comprobación se hizo hoy a mano contra
`.102`, comparando las definiciones de campos:

| Tipo | Humble vs Jazzy |
|---|---|
| `sensor_msgs/msg/LaserScan` | idéntico |
| `nav_msgs/msg/Odometry` | idéntico |
| `geometry_msgs/msg/Twist` | idéntico |
| `tf2_msgs/msg/TFMessage` | idéntico |

Son los cuatro tipos que este proyecto graba. Queda anotado en el propio
`adaptar_bag_jazzy.py`, con el comando y la trampa de los comentarios indentados
que hizo salir `TFMessage` falsamente distinto en la primera pasada.

---

## 5. Los dos carros se graban el uno al otro

Es el hallazgo mayor del día y lo detectó el usuario, no la instrumentación: al
ver una trayectoria de 11 m en un bag grabado con los dos vehículos **quietos
sobre la mesa**, preguntó si no se habrían solapado los dos carros. Sí se
solaparon.

### 5.1 · El mecanismo

Los dos vehículos publican `/rplidar_ros/scan` —el mismo nombre, sin namespace—
y ninguno define `ROS_DOMAIN_ID`, así que los dos caen en el dominio 0. El
`ros2 bag record` lanzado en el `.102` grabó **también el LiDAR del `.101`**. El
bag resultante alterna entre dos sensores situados en sitios distintos.

Es la manifestación concreta del pendiente de namespaces (`/robot1`, `/robot2`)
que el `README` de `Robot/` arrastra desde el planteamiento colaborativo. Hasta
hoy era un requisito de diseño; ahora es un defecto que produce evidencia falsa.

### 5.2 · La medida que lo demuestra

Comparar barridos **consecutivos** contra **alternos**:

| comparación | `bag_ez9n` | `sin_caparazon` |
|---|---|---|
| barrido *i* con *i+1* | **0,9210 m** | 0,0030 m |
| barrido *i* con *i+2* | **0,0050 m** | 0,0030 m |

En `bag_ez9n` los alternos coinciden en 5 mm y los consecutivos discrepan casi
un metro: el bag va y viene entre dos sitios. Ningún movimiento real produce
eso —con el sensor en marcha los alternos discrepan **más** que los
consecutivos, porque media más tiempo—. Los 5 mm entre alternos dicen además que
cada uno de los dos sensores estaba quieto, que es lo que el usuario afirmaba.

Tres confirmaciones independientes en el mismo bag: **14,68 Hz** cuando un
RPLidar da 7–10 Hz; intervalo mínimo entre mensajes de **0,0000 s**, imposible
con un solo publicador; y los primeros intervalos a 7,7 Hz antes de duplicarse.
Segmentado en ventanas de 2 s, la firma aparece desde el segundo 2 y se mantiene
hasta el final; en los primeros 2 s no discrimina porque los dos carros estaban
juntos y veían casi la misma escena.

### 5.3 · Qué queda retirado

| Afirmación de hoy | Estado |
|---|---|
| «rf2o converge con 360 muestras y 12 m» (151 poses) | **Retirada.** Las 151 poses salieron del bag contaminado. rf2o *corrió*, pero no se demostró nada sobre 360 muestras |
| «el desplazamiento de 1,66 m es real, no deriva» | **Retirada.** Se apoyó en el 59,1 % de movimiento, que es el falso positivo |
| «rf2o no es reproducible: 1,04 / 1,83 / 3,14 m sobre el mismo bag» | **Retirada como propiedad de rf2o.** Es la contaminación. Sobre el bag limpio, dos corridas dan **0,0042 m las dos, idéntico** |
| 71,1 % de rayos válidos del §2.2 | **Retirada.** Sale del mismo bag contaminado, y mezcla los dos vehículos |

Lo que **sí** queda en pie, medido sobre el bag limpio `sin_caparazon`: la cadena
de análisis es **determinista** —dos corridas idénticas al milímetro— y un
sensor quieto durante 8 s acumula **4 mm** de deriva. Es poco tiempo para
concluir sobre deriva, pero descarta que rf2o invente avance sobre una escena
estática y sana.

### 5.4 · Lo que se cambió para que no vuelva a pasar

1. **`comprobar_movimiento_bag.py` ahora lo detecta.** Es la barrera del
   proyecto contra el desastre del 28-ago y se dejó engañar: contestó «59,1 % de
   movimiento» sobre dos sensores quietos. Se le añadió `detectar_intercalado()`
   con el contraste consecutivos/alternos, un factor de 10 —medido: 184 en el
   bag contaminado, 1,0 en el limpio—, y seis casos de prueba.
2. **`GUION_RECTA_PELDANO2.md` §0.1 bis** exige un solo carro encendido y la
   comprobación `ros2 topic info /rplidar_ros/scan --verbose` → `Publisher
   count: 1` antes de cada grabación.
3. **`herramientas/odometria_desde_bag.sh`**, nueva, con la regla barata en el
   encabezado: correr la cadena **dos veces**; con entrada sana da el mismo
   número, y si no lo da el problema es el bag.

---

## 6. Errores cometidos hoy, y el cambio de método

Se registran porque el patrón importa más que los errores sueltos.

1. **Asimetría de tópicos inexistente.** Afirmé que `.101` tenía
   `/ctrl_pkg/servo_msg` y `.102` no. La lista completa muestra **25 tópicos
   idénticos** en los dos. Causa: leí una salida parcial de `ros2 topic list`
   durante una carrera de descubrimiento DDS.
2. **Acusé a las guías de estar equivocadas sobre `/scan`.** `/rplidar_ros/scan`
   es el tópico del driver de fábrica y las guías ya lo documentan. Las guías
   tenían razón.
3. **Afirmé que `/dev/ttyUSB0` estaba libre.** Mi barrido de `/proc` en línea
   tenía el entrecomillado anidado roto y no encontró nada, en silencio. Un
   script en archivo mostró el PID 717.
4. **`tf2_msgs/msg/TFMessage` distinto entre distros.** Casi lo reporto como
   hallazgo. Mi filtro `grep -v '^#'` no quitaba los comentarios **indentados**;
   la única diferencia son dos líneas `#` de documentación dentro de
   `TransformStamped`, que no tocan el formato de cable.

Los cuatro son el mismo fallo: **concluir desde una lectura parcial antes de
verificar**, y dos de ellos vienen de mandar órdenes largas por SSH en una sola
línea con comillas anidadas. A partir del tercero se cambió a **escribir el
script en un archivo y copiarlo con `scp`**, y esa clase de fallo desapareció.

A esos cuatro se suma un quinto de otra clase, el del §4: me puse a diagnosticar
desde cero un problema que el repositorio ya tenía resuelto y documentado desde
el 2026-09-01. No es lectura parcial sino **no haber mirado primero lo que ya
existe**, y se corrige igual de barato: antes de diagnosticar, `ls herramientas/`.

Y un sexto, el del §5, que es el más caro de los seis porque produjo cuatro
afirmaciones falsas encadenadas. Aquí sí verifiqué antes de reportar —pasé el
bag por `comprobar_movimiento_bag.py` en vez de fiarme de mi lectura—, y aun así
concluí mal, porque **la herramienta de verificación compartía el punto ciego**:
las dos miden diferencias entre barridos separados en el tiempo, y ninguna
preguntaba de qué sensor venía cada barrido.

La lección no es «verificar más», que ya se hacía. Es que **una verificación que
usa la misma medida que la afirmación no verifica nada**. La comprobación que
sirvió fue de otra naturaleza: contrastar la frecuencia contra la física del
sensor, y los consecutivos contra los alternos. Y la pregunta que la
desencadenó vino del usuario, que contrastó el resultado contra lo que había
visto con los ojos —el carro no se movió—. Ese contraste con el mundo es el que
ninguna herramienta trae de serie.

---

## 7. Qué queda pendiente de esta sesión

- **Flexómetro en los DOS carros** (175 mm ± 3 mm a la ranura del haz), porque
  se retiró el caparazón y la medida del 21-sep caducó. Es lo primero del
  `GUION_RECTA_PELDANO2.md`; sin esto, lo que se grabe va sobre una geometría
  que no se sabe si es cierta.
- **Re-medir la fracción de rayos con información de avance**, sin caparazón y
  con 360 muestras. El 5,1 % / 5,9 % / 17,5 % de S23 salió de geometría densa y
  simulada: no es comparable y no puede citarse como si lo fuera.
- ~~Corregir `HOJA_CAMPO_G2.md:185` y `:190`~~ — hecho el 2026-09-23.
- ~~Corregir `MAPA_TRABAJO_RESTANTE.md` §2.3~~ — hecho el 2026-09-23.
- **Decisión de los directores** sobre sitio de la etapa 3 y N de RF-27. Hasta
  que no esté por escrito no se corre la etapa 3, según §6 del acta.
