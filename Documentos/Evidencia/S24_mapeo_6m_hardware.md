# El vehículo se conduce solo seis metros y construye el mapa mientras lo hace

*Carro `amss-ez9n` (`.102`), 2026-09-24, noche. Primer mapa que este proyecto
construye con SLAM sobre **hardware real recorriendo un tramo largo bajo su propio
motor**. Los anteriores fueron de simulación (caja de 7,70 m, 2026-09-08) o de un
cuarto de 1,60 m empujando a mano (2026-09-24, mañana).*

---

## 1. Qué se corrió, y qué salió

La cadena entera a bordo, sin portátil en el lazo:

```
rplidar_node (deepracer-core)  -->  /rplidar_ros/scan
static_transform_publisher     -->  TF base_link -> laser   (yaw = pi)
rf2o_laser_odometry            -->  /odom y TF odom -> base_link
sync_slam_toolbox_node         -->  /map y TF map -> odom
cmdvel_to_servo_node           -->  /cmd_vel a /ctrl_pkg/servo_msg
avanzar_y_detener.py           -->  manda tracción y para al llegar
```

Tres corridas, todas con `throttle 0,4247` en el servo —comprobado en el log de
`cmdvel_to_servo_node`: **3227 mensajes** con ese valor y 155 en cero—:

| # | Pedido | Recorrido según rf2o | Marcha | Velocidad media | Desenlace |
|---|---|---|---|---|---|
| A | 3,00 m | **3,138 m** | 22,50 s | 0,139 m/s | alcanzó y paró |
| B | 6,00 m | **6,093 m** | 23,35 s | 0,261 m/s | alcanzó; sin mapa (defecto 1) |
| C | 6,00 m | **6,032 m** | 40,51 s | 0,149 m/s | alcanzó, **con mapa** |

El mapa de la corrida C está en
[`S24_mapa_pasillo6m_HARDWARE.pgm`](S24_mapa_pasillo6m_HARDWARE.pgm): 447 × 108
celdas a 5 cm, 1017 ocupadas y 12 638 libres, con una zona explorada de
**21,75 × 4,65 m**. Esa extensión **no es lo que anduvo el vehículo**: son los
6 m recorridos más lo que el LiDAR alcanzó a ver desde ellos. Se distinguen las
dos paredes del pasillo casi paralelas y los abanicos abiertos en los extremos,
donde el láser se escapa más allá del tramo mapeado.

**Deriva de rf2o en reposo, medida antes de cada arranque:** 0,025 m · 0,006 m ·
0,001 m en ventanas de 6 s. Ese es el suelo de ruido contra el que hay que leer
los metros de arriba, y es **tres órdenes de magnitud menor**.

---

## 2. Lo que este documento NO establece

**No cierra G-2.** La compuerta pide error ≤ 10 % sobre un recorrido conocido de
≥ 5 m ([`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md):104). Los 6 m cumplen la longitud
—es la primera vez—, pero **falta el otro término de la división**: nadie midió
con flexómetro cuánto avanzó el vehículo de verdad. Sin verdad de terreno,
«6,032 m» es lo que rf2o *dice*, no lo que el carro *hizo*, y G-2 pregunta
exactamente por la diferencia entre esas dos cosas.

Esa medida es lo único que le falta a esta corrida para ser una medida de G-2, y
es la razón de ser del guion de campo que acompaña a este registro.

**No valida la geometría del mapa.** El cuarto de 1,60 m se pudo contrastar
contra un flexómetro y dio 1,55 × 0,80 m frente a 1,60 × 0,76 m, una celda de
error. Aquí no hay contraste: el ancho entre paredes que da el mapa —unos 2,8 m
en el tramo central— no se ha comparado con el pasillo.

---

## 3. La cifra que cierra media pregunta de RF-14

[`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10.4 fija, **antes de medir**, qué
significaría cada resultado de la escala de tracción, y dice que falta un solo
dato: qué velocidad real produce un `throttle` dado. Estas tres corridas lo dan.

| Lo medido | |
|---|---|
| `throttle` en el servo | **0,4247** (constante en las tres corridas) |
| Velocidad real resultante | **0,139 · 0,261 · 0,149 m/s** |

Contra la tabla del §10.4, esto cae por debajo de su primera fila —«a 0,35 de
`throttle`, ~0,5 m/s»— y con holgura. El `MAX_SPEED` implícito es bastante menor
que los 4,0 m/s que la cadena supone, lo que **refuerza la vía de cerrar RF-14
calibrando** en vez de declararlo limitación física.

Y hay una consecuencia favorable que conviene no pasar por alto. El escalón más
bajo que la cadena sabe mandar —0,40 m/s de `/cmd_vel`, que es lo que produce ese
`throttle 0,4247`— se traduce en **0,14 a 0,26 m/s reales**. Nav2 quiere circular
a 0,26 m/s. Es decir: **la velocidad que Nav2 necesita sí está dentro de lo que el
motor puede dar**; lo que está roto es la *escala del mando*, no el motor. Eso es
la tercera fila del §10.4 resuelta en el sentido bueno.

> **Dos cautelas, y las dos importan.** La primera: estas velocidades salen de
> rf2o, que es justo el instrumento que G-2 pone a prueba. Si rf2o exagera, las
> tres cifras bajan en el mismo factor. *Atenuante medido esa misma tarde sobre
> `amss-jgm9`* ([`S24_peldano2_odometria_hardware.md`](S24_peldano2_odometria_hardware.md)):
> tres pasadas de 3 m contra flexómetro dieron razones **0,963 · 1,019 · 0,966**,
> media 0,982 y σ 0,032. Es otro vehículo y empujado a mano, pero acota el sesgo
> esperable en torno al 2 %, no en un factor. La segunda: **no son repetibles entre sí**
> —0,261 m/s en la corrida B contra 0,149 m/s en la C, con el mismo `throttle` y
> el mismo pedido—. Un factor de 1,75 sin explicación. Candidatos a comprobar:
> nivel de batería, pendiente del piso, o la propia dispersión de rf2o. **Hasta
> que eso se explique, la cifra de velocidad se cita como rango y no como valor.**

---

## 4. Cuatro defectos encontrados, y qué los delataba

Los cuatro son **fallos silenciosos**: ninguno produce un mensaje de error, y los
cuatro se manifiestan como «no pasó nada».

### 4.1 · `slam_toolbox` en Jazzy no se autoactiva

Es un nodo de **ciclo de vida** y nace `unconfigured`. Anuncia `/map`, no publica
nunca, y su log se queda en una sola línea (`Node using stack size 40000000`). La
corrida B recorrió sus 6 m enteros y no había mapa que guardar.

En Humble **no** es lifecycle, y por eso `mapear_desde_bag.sh` funciona en el
portátil sin hacer nada de esto. Es una diferencia Humble↔Jazzy, no un fallo.

Ya estaba escrito en [`GUION_NAV2_HARDWARE.md`](../GUION_NAV2_HARDWARE.md) §3, del
mismo día. **Se volvió a descubrir por no haberlo leído**, y eso costó una corrida
de campo entera. Queda anotado como lo que es: un fallo de método, no de software.

Arreglo: `ros2 lifecycle set /slam_toolbox configure` y luego `activate`, y
**verificar que responde `active` antes de mover el vehículo**.

### 4.2 · `map_saver_cli` se rinde a los 2 segundos

`[ERROR] Failed to spin map subscription`, exactamente 2,03 s después de arrancar.
Ese es su plazo por defecto, y `slam_toolbox` deja de publicar `/map` en cuanto el
vehículo se detiene —solo actualiza tras 0,15 m o 0,3 rad de movimiento—. El mapa
estaba perfectamente construido y el guardado falló igual.

Arreglo: no usar `map_saver_cli`. Se graba `/map` en el bag y se extrae después
con [`extraer_mapa.py`](../../herramientas/extraer_mapa.py), que además **hace el
mapa repetible**: si hay que cambiar un umbral, se cambia en el escritorio y no se
repite la salida. Así se recuperó el mapa de la corrida C sin volver a conducir.

### 4.3 · Los bags no cerraban, y quedaban ilegibles

Dos corridas dejaron un `.mcap` sin `metadata.yaml`. Un bag así no se puede
reproducir ni leer: los datos están y son inalcanzables.

La causa: un shell **no interactivo** pone SIGINT en `SIG_IGN` a todo lo que
lanza en segundo plano, y esa disposición sobrevive al `exec`. El grabador nacía
sordo a la señal. `kill -INT` no hacía nada.

`trap - INT` **no lo arregla** —fue el primer intento y falló—: `trap -` restaura
la disposición *heredada*, que es precisamente `SIG_IGN`. Lo que sirve es
`set -m`: con control de trabajos activo, cada proceso de fondo nace en su propio
grupo y con las disposiciones por defecto. Queda encapsulado en
[`lanzar_bag.inc`](../../herramientas/lanzar_bag.inc).

Explica de paso por qué `timeout -s INT` sí funcionaba: allí el grabador corre en
primer plano, donde el shell no toca las disposiciones.

### 4.4 · rf2o miente más de un metro en sus primeros segundos

Con el vehículo **inmóvil y velocidad mandada cero**, rf2o declaró **1,281 m en
1,53 s**. Tomando el origen en el primer `/odom` que llega, el guion habría dado
los 3 m por alcanzados sin que el carro se moviera.

Arreglo, en [`avanzar_y_detener.py`](../../herramientas/avanzar_y_detener.py): se
descartan los primeros 4 s, y después se observa quieto 6 s **midiendo la deriva**,
que se imprime junto al resultado. Si la deriva iguala la distancia pedida, aborta
en vez de dar un número que no distingue avance de ruido. Con esa fase, la deriva
bajó a 1–25 mm.

---

## 5. Un quinto defecto, este de método

La primera versión del guion comprobaba el láser **dentro** del bucle de marcha.
En el cuarto de 1,60 m la pared estaba a 0,36 m, el bucle cortó en la primera
iteración sin publicar nada, y el informe salió con `tiempo 1,12 s` —que era el
que tardan los cuarenta mensajes de parada— y un recorrido de 3,5 cm. **Parecía
que había avanzado y frenado.** Solo el log del servo, con sus 27 mensajes todos
en cero, permitió ver que el vehículo nunca recibió una orden de movimiento.

Arreglo: la comprobación va **antes** del bucle y aborta diciéndolo; y el tiempo
de marcha se reporta aparte del de parada, junto al número de órdenes de tracción
efectivamente enviadas. Un cero ahí es inequívoco.

---

## 6. Qué queda abierto

| | Qué falta | Dónde se cierra |
|---|---|---|
| 1 | **Flexómetro contra los 6 m.** Sin verdad de terreno no hay G-2 | guion de campo de piso 2 |
| 2 | El ancho del pasillo que da el mapa, contrastado con el sitio | ídem |
| 3 | La velocidad no es repetible: 0,261 contra 0,149 m/s | ídem, con batería anotada |
| 4 | Nav2 no puede navegar todavía: cuatro defectos de configuración | `nav2_slam_params.yaml`, sin tocar aún |
| 5 | `amss-jgm9` (`.101`) **no tiene** Nav2, `slam_toolbox` ni rf2o | pendiente explícito de nivelación |

El punto 5 incumple la regla de `CLAUDE.md` de tocar los dos carros en la misma
sesión. No se hizo porque el `.101` estaba **en uso por Jonny** esa noche, y
cambiar paquetes por debajo de alguien que trabaja es peor que la divergencia.
Queda anotado para cerrarse en cuanto el vehículo esté libre.

Sobre el punto 4, los cuatro defectos de `nav2_slam_params.yaml`, medidos y no
corregidos:

| Línea | Qué dice | Por qué rompe en el vehículo |
|---|---|---|
| `max_vel_x: 0.26` | velocidad máxima | se traduce en `throttle` **0,0**: el carro no se mueve nunca |
| `dwb_core::DWBLocalPlanner` | controlador local | es de robot diferencial; supone giro sobre sí mismo |
| `nav2_navfn_planner` | planificador | traza rutas sin radio de giro mínimo; un Ackermann no puede seguirlas |
| `nav2_behaviors/Spin` | recuperación | el vehículo **físicamente no puede** girar en el sitio |
