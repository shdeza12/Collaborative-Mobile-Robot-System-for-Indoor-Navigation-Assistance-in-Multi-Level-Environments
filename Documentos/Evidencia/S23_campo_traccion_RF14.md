# La escala de tracción, medida sobre el carro: dos defectos en vez de uno

**Fecha de la salida:** jueves 2026-09-17, tarde y noche, con el `amss-jgm9` (192.168.0.100).
**Qué se buscaba:** el §10 de [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) — la tabla `throttle` →
velocidad de RF-14, con al menos un punto por debajo de 0,25 m/s, usando
[`sostener_traccion.py`](../../herramientas/sostener_traccion.py), escrito y empujado esa misma
mañana en `e7139d4`.

**Resultado: el punto bajo está medido, el techo no.** Y la salida dejó **siete hallazgos que no se
buscaban**, cuatro de ellos sobre el procedimiento y no sobre el vehículo — incluido un incidente
de seguridad (§7). Este documento existe porque **RF-14 no tiene un defecto, tiene dos**, y porque
tres de las horas de campo se perdieron por una regla que el propio repositorio ya tenía escrita,
pero enunciada para el caso contrario.

---

## 1. El carro no arrancaba a ningún `throttle`, y no era la escala

El primer síntoma fue el peor posible para lo que se venía a medir: el vehículo no se movía con
ningún valor, ni con los altos. La cadena de diagnóstico, de fuera hacia dentro:

| Comprobación | Resultado |
|---|---|
| ¿El nodo publica? | Sí — `marcha throttle=0.050` en pantalla |
| ¿GPIO del servo exportado? | **No** (síntoma de que la pila no arrancó; ver §6: no es un habilitador) |
| `/servo_pkg/servo_gpio`, `/ctrl_pkg/enable_state` | se cuelgan sin responder |
| `/ctrl_pkg/vehicle_state` | responde `error=0` |
| `systemctl is-active deepracer-core` | **`failed`** |

`journalctl` dio la causa en una línea:

```
[ERROR] [launch]: executable 'rplidar_node' not found on the libexec directory
'/opt/ros/jazzy/lib/rplidar_ros'
```

Sin ese ejecutable el lanzamiento **aborta entero**, así que `servo_pkg` y `ctrl_pkg` nunca
arrancan y nadie exporta el GPIO del motor. El paquete apt
(`ros-jazzy-rplidar-ros 2.1.0-4noble.20260412.050633`, idéntico en los dos carros) solo instala
`rplidar_composition`.

**Lo importante es que esto ya estaba resuelto en el otro carro y nadie lo sabía.** El `amss-ez9n`
(192.168.0.102) tiene desde el 2026-08-28 un enlace simbólico `rplidar_node` → `rplidar_composition`,
creado en el frente B de S20 ([`S20_frente_b_hardware.md`](S20_frente_b_hardware.md)) y documentado
en [`GUIA_EJECUCION.md`](../GUIA_EJECUCION.md):895. Se creó como solución al LiDAR; resultó ser
**condición de arranque de toda la pila de control**. El segundo vehículo llegó el 14-sep sin él.

Corregido replicando el enlace, no editando `/opt/aws/deepracer/` — misma razón que en agosto: que
una actualización de AWS no lo revierta en silencio. Verificado por el dato, no por `systemctl`:
nueve GPIO exportados, los mismos que el `.102`.

> **Para la puesta a punto de cualquier carro nuevo:** el enlace simbólico de `rplidar_node` no es
> del LiDAR, es del arranque. Sin él no hay tracción.

---

## 2. La regla de dueños vale también para publicar, y en esa dirección no avisa

El repositorio ya enuncia la regla, y con precisión: **«el mismo dueño a los dos lados», no «todo
con `sudo`»** ([`GUIA_PASADA_MAPEO.md`](../GUIA_PASADA_MAPEO.md):463,
[`GUIA_PASADA_LOCALIZACION.md`](../GUIA_PASADA_LOCALIZACION.md):324–334). Pero está escrita para el
lado de **leer**: `ros2 bag record`, `topic hz`, `topic echo`. El aviso dice que un tópico mudo
puede ser un falso negativo de permisos.

Hoy se comprobó en el lado de **publicar**, contra los nodos de `deepracer-core`, que corren como
`root`. Y ahí el fallo es peor, porque **no hay ningún síntoma**:

```
[1789674504.259] marcha          throttle=1.000      <- ejecutado como 'deepracer': el carro NO se mueve
[1789674536.448] marcha          throttle=0.600      <- ejecutado con sudo -i:      el carro SÍ se mueve
```

El programa imprime sus cinco fases con total normalidad en los dos casos. `ros2 topic info`
informa de un suscriptor en los dos casos. El mensaje simplemente no cruza. Un operador que no
conozca la regla concluirá «el carro no arranca a `1.0`» y lo anotará como medida.

**Coste real:** todas las corridas de la tarde ejecutadas sin `sudo` **no midieron nada**, y se
interpretaron como fallos del vehículo. Se persiguieron por turno la batería del motor, la
calibración y el GPIO antes de dar con esto.

> **Regla ampliada:** *ningún* extremo de un tópico vale si no comparte dueño con el otro — ni
> leyendo ni publicando. Contra `deepracer-core` el dueño es `root`, así que el patrón obligatorio
> es `ssh -t … "sudo -i bash -c '…'"`. **Publicar con el dueño equivocado no da error: da silencio.**

---

## 3. Lo que el servo recibe no es lo que la tabla del mapeo dice

El análisis que llevó RF-14 de 🔴 a 🟡 el 2026-09-05 se hizo sobre `get_mapped_throttle`, cuyos
tres escalones son `0.5`, `0.8` y `1.0`
([`constants.py`](../../Robot/aws-deepracer/deepracer_nodes/cmdvel_to_servo_pkg/cmdvel_to_servo_pkg/constants.py):65–67).
Pero en [`cmdvel_to_servo_node.py`](../../Robot/aws-deepracer/deepracer_nodes/cmdvel_to_servo_pkg/cmdvel_to_servo_pkg/cmdvel_to_servo_node.py):235
hay **un segundo paso después del mapeo** que nadie había contado:

```python
throttle = self.get_rescaled_manual_speed(target_throttle_signed, self.max_speed_pct)
```

Con `MAX_SPEED_PCT = 0.68` (`constants.py`:82), ejecutando la función real:

| Escalón nominal | Lo que llega al servo |
|---|---|
| `0.5` | **0,4247** |
| `0.8` | **0,6242** |
| `1.0` | **0,7341** |

Ni siquiera el escalón máximo llega al tope: la cadena nunca pide al vehículo más del 73 % de su
recorrido de tracción.

---

## 4. El umbral de arranque, medido sobre el suelo

Con el vehículo operativo, `--tope 1.0` y el dueño correcto, publicando directamente a
`/ctrl_pkg/servo_msg` (camino que **no** pasa por el reescalado del §3, así que el valor pedido es
el que recibe `servo_pkg`):

| `throttle` | Arranques | Recorrido |
|---|---|---|
| `0.30` | empieza a moverse **en el aire** | — |
| `0.50` | **0 de 5** | 0 m |
| `0.60` | siempre | **menos de 1 m en 4 s** (< 0,25 m/s) |
| `1.00` | — | **sin medir** |

La tanda de `0.5` y `0.6` es válida a pesar del §2: dentro de la misma tanda el `0.6` sí movió el
carro, lo que prueba que los mensajes llegaban.

**Cruzando esta tabla con la del §3, el resultado es el que importa:**

- El escalón bajo de la cadena vale **0,4247** — por debajo del `0.5` que **no arrancó ninguna de
  cinco veces**. *En este vehículo, el escalón bajo de `/cmd_vel` no puede mover el carro.*
- El escalón medio vale **0,6242**, apenas **0,02 por encima** del primer valor que arranca de
  forma fiable. No hay margen.

---

## 5. La dirección de este carro nunca se centró

El carro se va a la izquierda de forma constante. La hipótesis en campo fue «no estamos
controlando la dirección», y el código dice lo contrario:
[`sostener_traccion.py`](../../herramientas/sostener_traccion.py):219 publica `msg.angle = 0.0` en
**cada** mensaje. La dirección sí se controla; el problema es dónde cae ese cero.

`servo_pkg` traduce `angle = 0.0` al `mid` de calibración. Y el `mid` de este vehículo es:

| | min | mid | max |
|---|---|---|---|
| Servo (dirección) | 1 200 000 | **1 450 000** | 1 700 000 |
| Motor (tracción) | 1 311 000 | 1 446 000 | 1 603 500 |

`(1 200 000 + 1 700 000) / 2 = 1 450 000` — **exactamente** el `mid`. Es el valor simétrico de
fábrica, no un centro medido contra las ruedas. El de tracción, en cambio, no cae en su punto
medio geométrico (1 457 250), de modo que ese sí fue tocado alguna vez.

**El cero del control no coincide con el recto físico del vehículo.** No es un defecto del
software y no se arregla en el repositorio: se calibra desde la consola web del DeepRacer.

**Corregido la misma noche, 20:17.** El centro de dirección se recalibró desde la consola, y el
cambio es grande:

| Servo | Antes | Después |
|---|---|---|
| min | 1 200 000 | 1 000 000 |
| **mid** | **1 450 000** | **1 290 000** |
| max | 1 700 000 | 2 000 000 |

El centro se desplazó **−160 µs**, y el nuevo `mid` ya **no** cae en el punto medio geométrico del
recorrido (1 500 000): es un centro medido contra las ruedas. Comprobado en las dos capas que
pueden discrepar —`calibration.json` con fecha nueva, y el `servo_node` vivo registrando
`Min: 1000000, Mid: 1290000, Max: 2000000`—, porque una calibración que se guarda en disco sin
llegar al nodo que gobierna el PWM no cambia nada. Un primer intento, media hora antes, no quedó
guardado: el disco conservaba la fecha de marzo y el nodo seguía diciendo `1450000`.

> **La consola de calibración deja el GPIO del motor en `0`.** Al salir de ella hay que rehabilitar
> con `servo_gpio {enable: 1}`, o el carro no arranca y parece un fallo de tracción.

*(Nota metodológica: `/ctrl_pkg/get_car_cal` devuelve ceros en los dos `cal_type`, con
`Calibration information not available in manual mode` en el log. La fuente válida es
`/servo_pkg/get_calibration`, que es quien gobierna el PWM, y coincide con
`/opt/aws/deepracer/calibration.json`.)*

---

## 6. Dos servicios que actúan sin responder

`/servo_pkg/servo_gpio` y `/ctrl_pkg/enable_state` **no devuelven respuesta nunca**: se quedan en
`making request`. Ya estaba anotado como anomalía no perseguida en
[`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md):140 — *«se queda colgado […] pero las
ruedas se movieron igualmente»*. Hoy se comprobó que **sí actúan**: el log de `servo_node` registra
la escritura y el valor del campo `enable` aparece literalmente en el GPIO.

`/ctrl_pkg/vehicle_state {state: 0}` deja el GPIO 514 en `0`, y `servo_gpio {enable: 1}` lo vuelve
a `1`: el campo del servicio aparece literalmente en el archivo del GPIO. Eso es todo lo que está
medido.

**Lo que ese GPIO *no* hace es cortar la tracción.** Durante la sesión se escribió `0` en el GPIO
514 del `.102`, se verificó leyendo `/sys/class/gpio/gpio514/value` que efectivamente valía `0`, y
al publicar tracción **el vehículo se movió igual**. La hipótesis de que ese GPIO fuera un
habilitador del motor queda **refutada por medición**, y con ella la explicación que durante unas
horas se le dio al arranque del `.100`: lo que hizo arrancar aquel carro fue el `sudo` de §2 y el
enlace de `rplidar_node` de §1, no el estado del GPIO.

Queda sin determinar qué gobierna realmente ese pin. No se persigue: para lo que falta de S23 no
hace falta saberlo, y suponerlo fue precisamente el error.

> El efecto de los servicios se verifica leyendo `/sys/class/gpio/gpio514/value`, no esperando la
> respuesta del servicio. Pero leer `0` ahí **no autoriza a acercarse al vehículo**.

---

## 7. Un comando de tracción mueve **los dos** carros a la vez

Con los dos vehículos encendidos en la misma red, un único comando dirigido por `ssh` al `.100`
**puso en marcha también al `.102`**. Es el primer incidente físico de la sesión y no es un fallo
del instrumento.

La causa está medida, no supuesta:

```
$ ssh deepracer@192.168.0.100 'echo "[${ROS_DOMAIN_ID}]"'
[]                     <- vacío, como usuario y como root, y nada lo fija en ningún perfil
```

Vacío significa **dominio 0**, el de por defecto, en los dos carros. DDS se descubre por multicast
dentro de la LAN, y `sostener_traccion.py` publica en `/ctrl_pkg/servo_msg` **sin namespace**: los
dos `servo_node` están suscritos al mismo tópico. Un publicador, dos vehículos.

**Esto es el pendiente «namespaces `/robot1` y `/robot2`» de OE2**, que hasta hoy figuraba como
limitación de diseño para el esquema colaborativo. Se ha manifestado como **riesgo de seguridad**:
cualquier prueba de tracción con los dos carros encendidos mueve el que no se está midiendo, que
puede estar sobre una mesa o sin nadie delante.

**Lo que no se debe hacer para arreglarlo:** separar los `ROS_DOMAIN_ID`. Eso aislaría los carros y
rompería la comunicación carro↔carro de RF-15 —600 de 600 mensajes, mediana 7,61 ms—, que costó
levantar un bloqueo de dominios el 2026-08-30 y una regla de `ufw` el 14-sep. La solución correcta
es la que ya estaba en la lista: **namespaces**.

Se intentó mitigarlo por software y **no funcionó**: se puso el GPIO 514 del `.102` en `0`, se
verificó leyendo el archivo que valía `0`, y el carro se movió igual (§6). La mitigación por GPIO
está descartada por medición.

> **Regla de campo, mientras no haya namespaces:** solo puede haber **un vehículo encendido** en la
> red durante una prueba de tracción o de navegación. El otro se apaga físicamente, o se le detiene
> la pila con `systemctl stop deepracer-core` **comprobando que ya no hay suscriptor** en
> `ros2 topic info /ctrl_pkg/servo_msg` (`Subscription count: 1`, no 2). Ninguna escritura de GPIO
> sustituye esa comprobación.

---

## 8. Lo que no se midió, y por qué no se insiste

**Falta el techo: `throttle = 1.0` sobre el suelo, con distancia.** Se intentó cuatro veces. Las
tres primeras, sin `sudo`, no publicaron (§2). Para la cuarta el vehículo ya había perdido la red.

No se fuerza una quinta, y la razón es del §5 más que de la logística: **un carro cuya dirección no
está centrada arrastra las ruedas, y cualquier distancia medida con él subestima la velocidad por
una cantidad desconocida.** Medir el techo antes de calibrar produciría una cifra que habría que
retirar después. La calibración de dirección es prerrequisito de la tabla, no un arreglo aparte.

Queda también anotada, sin perseguir, una anomalía: `/i2c_pkg/battery_level` respondía `level=9` y
dejó de responder durante la sesión, sin que el nivel hubiera bajado antes.

---

## 9. Qué significa esto para RF-14

**El criterio de cierre del §10 pedía al menos un punto por debajo de 0,25 m/s, y está medido:**
`throttle 0.6`, menos de 1 m en 4 s. Eso ya no es una declaración.

Lo que cambia es **qué se puede afirmar con la tabla**, y conviene decirlo entero antes de
redactar el capítulo de resultados:

1. **RF-14 tiene dos defectos independientes, no uno.** El conocido es *lógico*: `MAX_SPEED = 4.0`
   m/s divide la escala de forma que el escalón más bajo cae en 0,40 m/s mientras Nav2 pide 0,25 en
   curva y 0,05 en aproximación. El nuevo es *físico*: el reescalado del §3 comprime los tres
   escalones, y el más bajo queda por debajo del umbral de arranque medido del vehículo.
2. **Subir `MAX_SPEED_PCT` no cierra RF-14.** Llevarlo a ≈0,90 pondría el escalón bajo en 0,6327 y
   lo haría arrancar, pero acelera los tres escalones por igual y no toca el defecto lógico. El
   problema de fondo es que **cuatro escalones no cubren el rango que Nav2 usa** — que es lo que ya
   decía la fila 2 del §10.4.
3. **La tabla que se publique hoy documenta el extremo inferior de un vehículo con la dirección sin
   calibrar**, no la escala del sistema. Se reporta así, con esa limitación escrita. El criterio no
   se ajusta para que pase.
