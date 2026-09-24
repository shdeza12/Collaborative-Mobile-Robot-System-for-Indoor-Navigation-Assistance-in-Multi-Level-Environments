# Peldaño 2 sobre hardware: la odometría publica Y mide

**Fecha:** 2026-09-24 (S24), sesión de tarde.
**Vehículo:** `amss-jgm9` — el `.101` de los documentos; esa tarde el DHCP le dio
**192.168.0.104**. Se identifica por hostname y no por IP a propósito: la IP cambió
entre sesiones y el otro carro estuvo apagado todo el tiempo.
**Sitio:** el cuarto del extintor. Mapa `mapa_extintor.yaml`, **70 × 24 celdas a
0,05 m = 3,50 × 1,20 m**.
**Qué aísla:** el peldaño 2 de la escalera de Nav2 —*odometría publicada y validada
sola*—, sin SLAM, sin localización, sin Nav2 y **sin motor**. El carro se empuja a mano.

---

## 0. Por qué esta medición era la que mandaba

El §1 de [`MAPA_TRABAJO_RESTANTE.md`](../MAPA_TRABAJO_RESTANTE.md) lo dice en una frase:

> *Hay una sola ruta crítica, y no es la campaña experimental: es publicar el TF
> `odom → base_link` en el vehículo real.*

La tabla del §2.3 tenía el peldaño 2 en **❌ sin fuente** desde que se escribió. Todo
el trabajo de S22 y S23 fue, sin saberlo, la investigación de ese peldaño. Esta sesión
es la primera vez que se construye.

**Criterio, fijado antes de correr** (es el M1 corregido del §4 de
[`S21_preparacion_G2.md`](S21_preparacion_G2.md), de dos lados):

> **|registrado ÷ real − 1| ≤ 0,10**

---

## 1. Montaje

Un solo lanzamiento, sin SLAM y sin Nav2 —o sea `robot_state_publisher` + `rf2o`
solamente—:

```
ros2 launch $D/nav2_hardware.launch.py urdf:=$D/deepracer_hardware.urdf \
    params:=$D/nav2_params.yaml slam_params:=$D/slam_toolbox.yaml \
    behavior_trees:=$D/behavior_trees
```

**Todo como `root`.** Es la regla del dueño ya documentada: los segmentos
`/dev/shm/fastrtps_*` son de `root` y un suscriptor no-root se queda mudo sin un solo
error. Se respetó en el lanzamiento, en las comprobaciones y en el grabador.

**Salud de la cadena, medida sobre los bags:** `/rplidar_ros/scan` a **7,74 Hz**
(449 barridos en 58,0 s) y `/odom` a **7,53 Hz** (437 mensajes). Coincide con los
7–8 Hz esperados del LiDAR de fábrica.

**Peldaño 1, de paso:** el primer mensaje de `rf2o` sale como
`Laser odom [x,y,yaw]=[0.029130 0.000000 -3.141585]`, que es **exactamente** la TF
`base_link → laser` del URDF (`[0.029, 0.000, 0.185]`, RPY −180°). La cadena de
transformadas está bien cargada.

---

## 2. Resultado principal — tres pasadas de 3,00 m

Distancia real medida con **flexómetro y cinta marcada en el piso**.

| Pasada | Registrado | **Razón** | Error | Quietud final |
|---|---|---|---|---|
| `p2_tresmetros_01` | 2,8885 m | **0,963** | 3,7 % | 3 mm en 5 s |
| `p2_tresmetros_02` | 3,0571 m | **1,019** | 1,9 % | 3 mm en 5 s |
| `p2_tresmetros_03` | 2,8969 m | **0,966** | 3,4 % | 2 mm en 5 s |

```
RAZON media 0,982    desviacion tipica 0,032    recorrido 0,963 – 1,019
CRITERIO |razon - 1| <= 0,10   ->   CUMPLE EN LAS TRES
```

**Las tres rodean el 1,0, y una se pasa (1,019).** Eso es lo que convierte el
resultado en creíble: si hubiera un sesgo sistemático a la baja —que es lo que el
proyecto venía temiendo desde agosto— las tres caerían del mismo lado. Es ruido en
torno al valor correcto.

El perfil de las tres tiene la forma que se exigía: **meseta en el origen → rampa →
meseta estable**. La `01`, con el marco limpio, mantiene la meseta final 16 s
(2,8880 · 2,8895 · 2,8894 · 2,8866).

**Con esto el peldaño 2 pasa de ❌ a ✅ sobre hardware.**

---

## 3. Lo que hubo que descartar por el camino, y por qué se cuenta

### 3.1 · Las pasadas de 1 m no sirven, y no por el sensor

Se empezó con empujones de 1,00 m. Dieron razones de **0,883** y **0,828**, que
fallan el criterio. Durante un rato pareció el hallazgo de la tarde.

No lo era. Los déficits **absolutos** lo destapan:

| Recorrido | Déficit |
|---|---|
| 1 m | 0,117 m · 0,172 m |
| 3 m | 0,112 m · −0,057 m · 0,103 m |

**El déficit no crece con la distancia.** Un error de escala del 15 % habría dado
45 cm de déficit sobre 3 m; dio 11. Es un **desplazamiento aproximadamente fijo** de
~0,10–0,15 m, que sobre 1 m vale el 12–17 % y sobre 3 m el 3–4 %.

Su origen más probable es de **alineación**, no de sensor: 13 cm es casi media
carrocería (el vehículo mide 0,28 m de largo), y basta referir la marca de salida y
la de llegada a puntos distintos del carro para perderlos.

**Consecuencia de método, y es la lección de la tarde:** una medida de 1 m no puede
validar esta cadena, porque el error de referencia domina. **La longitud de la
prueba es parte del instrumento.**

### 3.2 · Tres bags con el origen contaminado

Las tres primeras grabaciones (`peldano2_1m_01..03`) arrancan con el carro ya
desplazado —x ≈ −0,98, −0,97, −1,07— porque `rf2o` venía corriendo de antes y su
origen no estaba donde se creía. Se reconstruyó el recorrido por inferencia y salieron
razones de 0,84 · 0,78 · 0,58, con una dispersión de 0,31 que apuntaba al fallo de
interruptor.

**Esa dispersión era del método, no del sensor.** Al relanzar el nodo antes de cada
pasada —origen verificado en `[0.000000 0.000000 0.000000]`— la dispersión cayó a
**0,032**. Queda anotado porque es exactamente la clase de conclusión que, sin
repetir, habría entrado en el documento final como un defecto del vehículo.

### 3.3 · Una pasada truncada

`p2_origen0_01` acabó con el carro todavía en movimiento (t=38,4 → −0,763; t=41,4 →
−0,794; t=42,3 → −0,801, y ahí cortó el grabador). Su 0,804 es una **cota inferior**,
no una medida. Se descarta.

A partir de ahí el analizador comprueba el desplazamiento de los últimos 5 s y marca
la pasada como truncada por encima de 20 mm, en vez de dejarlo al ojo.

### 3.4 · La columna «lateral» de `02` y `03` no significa nada

El analizador calculaba el desvío lateral como |Δy|, lo cual **solo vale si el carro
avanza a lo largo del eje x del odom**. En `02` y `03` no se relanzó el nodo, así que
el marco traía orientación acumulada: `03` va de (0,24; −0,17) a (1,39; **+2,48**), o
sea mayormente en +y. Los «38 cm» y «266 cm» de esas filas son un artefacto.

**Las razones siguen siendo válidas**: la magnitud del desplazamiento entre dos puntos
no depende de la orientación del marco. Pero el único dato lateral utilizable es el de
`p2_tresmetros_01`, que sí arrancó con el marco limpio: **9,5 cm sobre 2,89 m = 3,3 %**.

---

## 4. Resultado secundario: no hay deriva en parado

Medido sobre las mesetas de los tres primeros bags, con el carro quieto:

| Bag | Ventana | Deriva |
|---|---|---|
| `peldano2_1m_01` | 24 s | **6 mm** |
| `peldano2_1m_02` | 24 s | **9 mm** |
| `peldano2_1m_03` | 20 s | **19 mm** |

Confirma con bag y por triplicado lo que el 24-sep se midió una sola vez en vivo
(~0,34 mm/s): **el estimador no inventa movimiento cuando no lo hay.** Es la propiedad
complementaria de la del §2 —no inventar y no perder son fallos distintos— y las dos
hacen falta.

---

## 5. Lo que esto NO dice

Se escribe aparte y con el mismo énfasis, porque es donde este resultado se puede
sobre-leer:

1. **No es G-2.** G-2 exige **≥ 5 m** sobre un recorrido conocido. Aquí son 3 m, y
   en el cuarto del extintor no caben más. La compuerta C-1 sigue pendiente.
2. **No prueba el pasillo.** El cuarto mide 3,50 × 1,20 m y tiene estructura encarada
   por los cuatro lados dentro del alcance del sensor: es la geometría **buena**, la
   misma clase que la caja cerrada aceptada en simulación. Los pasillos reales miden
   **5,1 %** y **5,9 %** de información de avance
   ([`S23_informacion_avance_piso1.md`](S23_informacion_avance_piso1.md),
   [`S23_informacion_avance_piso2.md`](S23_informacion_avance_piso2.md)), por debajo
   del 6,8 % del pasillo simulado cuyo mapa se rechazó. **Nada de lo medido hoy
   contradice eso**, y la vía sigue siendo el segmento encajonado del §0 de
   [`GUION_NAV2_HARDWARE.md`](../GUION_NAV2_HARDWARE.md).
3. **No hay peldaños 6–7.** No se intentó mover el carro con motor, porque en este
   vehículo `servo_pkg` está bloqueado desde la pérdida de potencia documentada en
   [`S24_actuacion_bloqueada_servo.md`](S24_actuacion_bloqueada_servo.md) y recogida en
   el §3.2 del [`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md).
4. **n = 3.** Suficiente para una razón con desviación típica, no para una cota
   estadística.

---

## 6. Qué se abre

- **La proyección a 5 m es favorable y es lo único que aquí se extrapola:** con un
  déficit fijo de ~0,05–0,13 m, a 5 m eso son **1–3 %** de error contra un criterio del
  10 %. No sustituye a correr los 5 m; dice que vale la pena correrlos.
- **El signo del eje x.** En la primera pasada en vivo el avance salió **positivo** y
  en varias posteriores **negativo**. Lo más probable es que sea el sentido del
  empujón, pero toca la discrepancia de 180° entre el URDF y el montaje real del LiDAR
  que **R13** tiene abierta. Se anota sin resolver: hace falta una pasada con el
  sentido de empuje registrado en papel.
- **El desvío lateral de 3,3 %** no tiene criterio asignado. Para G-2 no manda —la
  métrica es el avance—, pero para navegación sí, y hoy nadie lo evalúa.

---

## 7. Datos

Los bags **no se versionan** (viven en `~/tesis_evidencia/S24_peldano2/`). Siete
grabaciones, todas con `message_count` distinto de cero:

| Bag | Qué es |
|---|---|
| `peldano2_1m_01..03` | 1 m, origen contaminado. Solo válidos para la deriva en parado (§4) |
| `p2_origen0_01` | 1 m, **truncada**, se descarta |
| `p2_origen0_02..03` | 1 m, origen limpio. Razones 0,883 y 0,828 (§3.1) |
| `p2_tresmetros_01..03` | **3 m, el resultado del §2** |

Tópicos grabados en todos: `/rplidar_ros/scan`, `/odom`, `/tf`, `/tf_static`.
