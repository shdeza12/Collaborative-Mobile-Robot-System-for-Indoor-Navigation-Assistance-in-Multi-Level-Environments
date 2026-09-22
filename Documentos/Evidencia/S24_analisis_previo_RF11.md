# RF-11 · análisis previo al campo: la cadena `/cmd_vel` no puede mover el carro a las velocidades que Nav2 tiene configuradas

**Fecha:** martes 2026-09-22, trabajo de escritorio.
**Vehículos consultados:** `amss-jgm9` (192.168.0.101) y `amss-ez9n` (192.168.0.102), sólo lectura.
**Naturaleza:** análisis de código y de configuración cruzado con medidas ya existentes en el
repositorio. **No se movió ningún vehículo y no se modificó ninguna constante.**

---

## 0. Por qué se escribe esto antes de salir a campo

[`MAPA_TRABAJO_RESTANTE.md`](../MAPA_TRABAJO_RESTANTE.md):51 dejó a **RF-11 como el único de los
seis requisitos abiertos sin bloqueo**, con el pendiente acotado: el recorrido del 28-ago se mandó
por `/ctrl_pkg/servo_msg` y el requisito pide `/<ns>/cmd_vel`, *un puente que nunca se ha ejercitado
sobre hardware*.

La intención de hoy era escribir el guion de campo de ese puente. Al preparar el guion aparecieron
tres cosas que **invalidan la prueba tal como estaba redactada**, y las tres se pueden establecer
sin gastar una sesión de vehículo. Ése es el único motivo de este documento: **una sesión de campo
con los carros cuesta más que una tarde de lectura, y esta lectura ya sabe que la prueba habría
fallado.**

---

## 1. El puente no está en ningún vehículo

Medido hoy sobre las dos tarjetas:

| Comprobación | `amss-jgm9` | `amss-ez9n` |
|---|---|---|
| `cmdvel_to_servo_pkg` en `/opt/aws/deepracer/lib/` | **No** | **No** |
| `~/deepracer_ws` | **No existe** | **No existe** |
| `~/coordinacion_ws/src` | `coordinacion`, `coordinacion_msgs`, `deepracer_bringup` | ídem |

En `/opt/aws/deepracer/lib/` sólo hay los 17 paquetes de fábrica de AWS (`camera_pkg`, `ctrl_pkg`,
`servo_pkg`, `deepracer_interfaces_pkg`, …). El paquete que traduce `/cmd_vel` a `ServoCtrlMsg`
**nunca ha pisado un vehículo**.

Esto por sí solo ya cambia la naturaleza de la tarea: RF-11 sobre hardware **no es «correr una
prueba», es desplegar y compilar un paquete nuevo** en el mismo `~/coordinacion_ws` que se usó para
RF-16 el 2026-09-22.

### 1.1 Y hay que compilarlo contra el `deepracer_interfaces_pkg` del vehículo, no contra el nuestro

[`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md) §2.4 dejó comprobado que el
`ServoCtrlMsg` del vehículo tiene un tercer campo, `builtin_interfaces/Time source_stamp`, que el
del repositorio no tiene. `servo_pkg` está compilado contra la versión del vehículo.

`~/coordinacion_ws/src` **no** contiene `deepracer_interfaces_pkg` (comprobado hoy), así que basta
con sourcear `/opt/aws/deepracer/lib/setup.bash` **por debajo** del workspace antes de compilar. Si
alguien copiase nuestro `deepracer_interfaces_pkg` al workspace, la superposición ganaría y el
mensaje dejaría de cruzar — otra vez sin error, sólo silencio.

---

## 2. El hallazgo que importa: la escalera de tracción, cruzada con la configuración real de Nav2

### 2.1 Lo que el nodo emite de verdad

La salida no es la de la tabla de `constants.py`. Hay **dos pasos**:

1. `get_mapped_throttle`
   ([`cmdvel_to_servo_node.py`](../../Robot/aws-deepracer/deepracer_nodes/cmdvel_to_servo_pkg/cmdvel_to_servo_pkg/cmdvel_to_servo_node.py):188–196)
   categoriza `|v| / MAX_SPEED` con `MAX_SPEED = 4.0` (`constants.py`:40) en cuatro escalones.
2. `get_rescaled_manual_speed` (línea 235) reescala con `MAX_SPEED_PCT = 0.68` (`constants.py`:82).

Ejecutando las dos funciones reales, la escalera completa en función de la velocidad pedida:

| `linear.x` pedido | `\|v\| / MAX_SPEED` | Escalón nominal | **Lo que recibe `servo_pkg`** |
|---|---|---|---|
| < 0,400 m/s | < 0,100 | — | **0,0000** |
| 0,400 – 1,199 m/s | 0,100 – 0,299 | 0,5 | **0,4247** |
| 1,200 – 1,999 m/s | 0,300 – 0,499 | 0,8 | **0,6242** |
| ≥ 2,000 m/s | ≥ 0,500 | 1,0 | **0,7341** |

El reescalado ya estaba escrito en [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §3.
Lo que **no** estaba escrito es sobre qué escalón cae la velocidad de crucero de Nav2, ni qué pasa
al cruzarlo con el umbral medido sobre el suelo.

> **Dos documentos del repositorio dan aquí la escalera equivocada.**
> [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10.1 y el encabezado de
> [`medir_escala_traccion.py`](../../herramientas/medir_escala_traccion.py) tabulan **0,5 · 0,8 ·
> 1,0**, que son los escalones *nominales*: los dos omiten el reescalado por `MAX_SPEED_PCT`. Los
> valores que el servo recibe de verdad son **0,4247 · 0,6242 · 0,7341**, un 15 % más bajos.
> **Corregidos los dos el mismo día**; el argumento de fondo de ambos —que `MAX_SPEED = 4,0 m/s` es una
> suposición heredada de AWS y de ella cuelga toda la tabla— **es correcto y anterior a este
> documento**, y este análisis lo confirma en lugar de descubrirlo.

### 2.2 El umbral mecánico, medido sobre el suelo

[`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §4, con el `amss-jgm9` sobre el suelo,
publicando directo a `/ctrl_pkg/servo_msg` (camino que **no** pasa por el reescalado, así que el
valor pedido es el que recibe el servo):

| `throttle` | Arranques | Recorrido |
|---|---|---|
| 0,30 | sólo **en el aire** | — |
| **0,50** | **0 de 5** | 0 m |
| **0,60** | **siempre** | < 1 m en 4 s (< 0,25 m/s) |
| 1,00 | — | sin medir |

### 2.3 El cruce

| Parámetro de Nav2 | Fichero | Velocidad | Escalón | Recibe el servo | Umbral 0,50–0,60 | Resultado |
|---|---|---|---|---|---|---|
| `desired_linear_vel` | [`nav2_params.yaml`](../../Robot/aws-deepracer/deepracer_bringup/config/nav2_params.yaml):78 y [`nav2_params_nav_amcl_dr_demo.yaml`](../../Robot/aws-deepracer/deepracer_bringup/config/nav2_params_nav_amcl_dr_demo.yaml):63 | 0,50 m/s | bajo | **0,4247** | por **debajo** del 0,50 que no arrancó ninguna de cinco veces | **no se mueve** |
| `max_vel_x` | [`nav2_slam_params.yaml`](../../Robot/aws-deepracer/deepracer_bringup/config/nav2_slam_params.yaml):70 | 0,26 m/s | — | **0,0000** | — | **no se mueve, y el nodo publica un cero explícito** |

**Las dos configuraciones de Nav2 que hay en el repositorio producen un vehículo inmóvil.** Ninguna
de las dos emite error: una publica 0,4247 y el variador no rompe inercia; la otra publica un cero
perfectamente válido.

### 2.4 Y la corrección del mapeo, que era correcta, es lo que dejó la cadena por debajo del umbral

Esto merece quedar escrito porque es contraintuitivo.

[`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md) §2.2 diagnosticó que
`get_mapped_throttle` comparaba **de umbral menor a mayor**, así que la primera rama se lo tragaba
todo y las dos `elif` eran código muerto: la salida era **binaria, {0 · 0,7341}**, con umbral en
`v = 0,400 m/s`. Con ese defecto, `desired_linear_vel = 0,50` caía en **0,7341 → avanza**.

El defecto se corrigió —el orden es ahora de mayor a menor, y los comentarios de las líneas 181–187
y 206–209 lo documentan—. La corrección es **correcta**: restituye los cuatro escalones que las
constantes declaran. Pero al restituirlos, la misma velocidad de 0,50 m/s bajó de **0,7341 a
0,4247**, es decir, **de un valor que mueve el carro a uno que no lo mueve**.

> **Arreglar el código empeoró el comportamiento en campo.** No porque el arreglo esté mal, sino
> porque las constantes que el arreglo hizo efectivas nunca se ajustaron a este vehículo. Un
> requisito no se verifica leyendo el código: se verifica contra el hardware.

---

## 3. `/cmd_vel` es absoluto, y los dos carros comparten dominio

`CMDVEL_TOPIC = "/cmd_vel"` (`constants.py`:32) lleva barra inicial, igual que
`ACTION_PUBLISH_TOPIC` (:29). Para el lado del servo la barra es deliberada y necesaria —el
`namespace='cmdvel_to_servo_pkg'` del launch habría publicado en `/cmdvel_to_servo_pkg/servo_msg`,
donde no escucha nadie, que es el defecto de `S19` §2.3—. Para el lado de `/cmd_vel` la misma barra
tiene dos consecuencias:

1. **El criterio de RF-11 pide `/<ns>/cmd_vel`** y el nodo escucharía en `/cmd_vel`.
2. **Los dos vehículos comparten dominio 0.** Un solo `/cmd_vel` movería **los dos carros a la vez**.

No hace falta tocar el código congelado: un remapeo en el lanzamiento resuelve las dos
(`--ros-args -r /cmd_vel:=/robot1/cmd_vel`). Queda anotado para que nadie lo descubra con los dos
carros rodando.

---

## 4. Qué haría falta para que la cadena funcione, con los números

Sólo dos constantes gobiernan la escalera. Calculado ejecutando las funciones reales:

| `MAX_SPEED` | `MAX_SPEED_PCT` | Escalera (bajo · medio · alto) | 0,26 m/s | 0,50 m/s |
|---|---|---|---|---|
| **4,0** | **0,68** *(actual)* | 0,425 · 0,624 · 0,734 | **0,000** | **0,425** |
| 4,0 | 1,00 | 0,800 · 0,992 · 1,000 | **0,000** | 0,800 |
| 1,0 | 0,68 | 0,425 · 0,624 · 0,734 | **0,425** | 0,734 |
| 1,0 | 0,90 | 0,633 · 0,865 · 0,959 | 0,633 | 0,959 |
| **1,0** | **1,00** | 0,800 · 0,992 · 1,000 | **0,800** | **1,000** |

`MAX_SPEED_PCT` **se puede cambiar en caliente**: el nodo expone el servicio `set_max_speed`
(`cmdvel_to_servo_node.py`:68–70), así que no exige recompilar. `MAX_SPEED` sí es constante de
código.

**Pero la tabla no basta para decidir**, y conviene ser explícito sobre por qué:

- El único punto de la curva `throttle → velocidad real` que existe es **0,60 → menos de 0,25 m/s**.
  De 0,70 en adelante **no hay ninguna medida**; el 1,00 figura literalmente como «sin medir».
- Bajar `MAX_SPEED` a 1,0 significa declarar que el vehículo no pasa de 1 m/s en interiores. Es
  probablemente cierto, pero **hoy no está medido**, y una constante del repositorio no debería
  fijarse sobre una suposición.
- La escalera tiene **cuatro escalones**. Nav2 manda una velocidad continua. Ninguna elección de
  constantes hace que la tracción *siga* la velocidad pedida; lo máximo alcanzable es que los
  escalones caigan en sitios útiles. Para **RF-11**, que sólo pide que el vehículo **se desplace**
  mandado por `/<ns>/cmd_vel`, eso es suficiente. Para **G-3** (navegación completa) es una
  pregunta abierta que este documento no resuelve.

---

## 5. La medida que decide, y por qué es una sola

Falta **una** curva: `throttle → velocidad real sobre el suelo`, de 0,60 a 1,00.

Esa única rampa:

| Alimenta | Qué decide |
|---|---|
| **RF-11** | Qué par (`MAX_SPEED`, `MAX_SPEED_PCT`) deja todos los escalones no nulos por encima del umbral, con margen |
| **RF-14** | Su pendiente declarado en `MAPA`:43 es exactamente «campo: rampa, escalones, vídeo» |
| **G-3** | La envolvente de velocidad real que Nav2 puede pedir sin mentirse |

Tres pendientes con una salida de campo. Por eso se propone ésta y no la prueba de `/cmd_vel`: **la
prueba de `/cmd_vel` no puede pasar hasta que esta curva exista**, porque sin ella no hay forma no
arbitraria de elegir las constantes.

### 5.1 El procedimiento ya está escrito, y no hace falta reescribirlo

No se redacta un guion nuevo. La rampa es el **Bloque 7** de
[`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10, con su herramienta de campo
(`herramientas/sostener_traccion.py --rampa DESDE:HASTA:PASO`, con hombre muerto, tope duro de
`--tope` y cuenta atrás) y su herramienta de análisis
([`medir_escala_traccion.py`](../../herramientas/medir_escala_traccion.py)). Su criterio de cierre
—«una tabla de `throttle` contra velocidad medida, con al menos un punto por debajo de 0,25 m/s»—
sigue valiendo tal cual.

Lo que este análisis le cambia son **tres cosas**, y las tres lo abaratan. **Aplicadas al Bloque 7
el mismo 2026-09-22** —§10.1 con la tabla real y el aviso de corrección, §10.1.1 nuevo con el
levantamiento del candado de G2 y el barrido desde 0,60—:

| Lo que dice el Bloque 7 hoy | Lo que hay que cambiarle | Por qué |
|---|---|---|
| «**Solo si el G2 ya está cerrado**», porque la velocidad la calcula `medir_escala_traccion.py` desde la trayectoria de rf2o | **La rampa no necesita G-2.** Una recta medida con flexómetro y un cronómetro da la misma tabla | El criterio de cierre pide «velocidad medida», no «velocidad estimada por rf2o». El §1.3 de `MAPA` ya aceptaba el flexómetro para RF-11 |
| El barrido sugerido arranca por debajo, buscando el umbral | **Arrancar en 0,60**, el primer valor que rompe inercia siempre, y subir a 0,70 · 0,80 · 0,90 · 1,00 | El umbral ya está medido (§2.2). Lo que falta no es dónde arranca, es **cuánta velocidad da cada escalón por encima** |
| La tabla de escalones del §10.1 | Sustituirla por la del §2.1 de este documento | Los valores nominales no son los que recibe el servo |

Con eso, la rampa deja de depender del camino crítico y **se puede correr el primer día que haya
carro y pasillo**, sin esperar a la decisión de odometría.

---

## 6. Veredictos preinscritos

Escritos **antes** de correr. No se ajustan después.

| Si ocurre | Entonces se declara | Y la consecuencia es |
|---|---|---|
| A 0,80 el carro se desplaza ≥ 1 m en 4 s de forma repetible | El escalón bajo de `(1,0 · 1,00)` es utilizable | Se fijan las constantes y se pasa a la prueba de `/cmd_vel` |
| A 0,80 no arranca de forma fiable | El umbral sobre el suelo está por encima de 0,80 | Sólo el escalón alto sirve; la tracción queda binaria y **se declara así por escrito**, sin maquillarlo |
| La velocidad a 1,00 supera 0,6 m/s | El vehículo es más rápido de lo que Nav2 supone | `MAX_SPEED = 1,0` es defendible; se fija con la medida al lado |
| La velocidad a 1,00 no llega a 0,3 m/s | El vehículo nunca alcanza `desired_linear_vel` | **Se baja `desired_linear_vel` en Nav2**, no se sube el throttle; y RF-14 se cierra con esa cota |
| Los dos carros dan curvas distintas en más de un 25 % | La calibración de tracción no es común | Cada vehículo lleva sus constantes, y RF-27 debe declararlo |

---

## 7. Lo que este documento **no** establece

- **No mide nada.** Todo lo del §2 es lectura de código y de configuración cruzada con medidas
  ajenas, todas del `amss-jgm9`. El `amss-ez9n` sólo tiene el dato de banco (0,60 rompe inercia con
  las ruedas en el aire, [`S24_sonda_actuacion_amss_ez9n.md`](S24_sonda_actuacion_amss_ez9n.md) §4.4).
- **No cambia el estado de RF-11**, que sigue 🟡.
- **No toca ninguna constante.** La elección del §4 es una decisión con consecuencias sobre RF-14 y
  sobre Nav2, y se toma con la curva del §5 delante, no antes.

### 7.1 Una discrepancia que se deja anotada, no corregida

[`REQUISITOS.md`](../REQUISITOS.md):114 escribe el criterio de RF-11 como «recorrido medido contra
`/odom`». [`MAPA_TRABAJO_RESTANTE.md`](../MAPA_TRABAJO_RESTANTE.md):40 lo escribe como «recorrido
medido sobre el carro», y §1.3 como «medir con flexómetro», dejando `/odom` para **RF-13**, que la
propia celda de `REQUISITOS.md`:114 ya señala como requisito distinto.

Las dos lecturas no dan el mismo trabajo: con la primera, RF-11 queda bloqueado por G-2 —la
odometría, que es el camino crítico— y **la afirmación de `MAPA`:51 de que RF-11 no tiene bloqueo
sería falsa**. Se deja anotado para que lo resuelvan los dos autores, sin editar ninguno de los dos
documentos.

---

## 8. Trazabilidad

| Afirmación | Dónde comprobarla |
|---|---|
| El puente no está en ningún carro | `ls /opt/aws/deepracer/lib/` en `.101` y `.102`, 2026-09-22 (§1) |
| El workspace no trae `deepracer_interfaces_pkg` | `ls ~/coordinacion_ws/src/` en `.101`, 2026-09-22 |
| La escalera real es 0,425 · 0,624 · 0,734 | `get_mapped_throttle` + `get_rescaled_manual_speed`, ejecutadas con `MAX_SPEED_PCT = 0.68` |
| El umbral sobre el suelo | [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §4 |
| El reescalado ya estaba descrito | [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §3 |
| El mapeo era binario antes de la corrección | [`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md) §2.2 |
| `ServoCtrlMsg` difiere entre repositorio y vehículo | [`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md) §2.4 |
| Las velocidades de Nav2 | `nav2_params.yaml`:78, `nav2_params_nav_amcl_dr_demo.yaml`:63, `nav2_slam_params.yaml`:70 |
| El procedimiento de rampa ya existe | [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10, `herramientas/sostener_traccion.py`, `herramientas/medir_escala_traccion.py` |
| Los dos documentos que tabulan los escalones nominales | `HOJA_CAMPO_G2.md`:548–553 y el encabezado de `medir_escala_traccion.py` |
