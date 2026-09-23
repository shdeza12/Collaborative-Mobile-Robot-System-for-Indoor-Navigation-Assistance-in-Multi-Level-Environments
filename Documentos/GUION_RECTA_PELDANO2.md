# Guion de campo — la recta del peldaño 2

**Fecha de redacción:** 2026-09-23
**Qué aísla:** el peldaño 2 de la escalera Nav2 — *odometría publicada y validada sola*.
**Por qué ahora:** es el único peldaño que nunca se ha construido sobre hardware, y
es el que bloquea G-2. No necesita la decisión de los directores, porque esto **no
es la medida oficial de G-2** sino el ensayo que dice si la cadena produce algo
usable. Ellos deciden *dónde* se toma la oficial, no si el método funciona.

**Qué NO es esto:** no es una misión, no hay Nav2, no hay motor. El carro se
empuja a mano. Cualquier cosa que añada variables antes de tener la odometría
sola es la trampa que el mapa §2.3 lleva advirtiendo desde S23.

---

## 0. Antes de salir — dos cosas que cambiaron hoy

**0.1 · Se quitó el caparazón.** Los 175 mm del URDF se midieron el 2026-09-21
**con el caparazón puesto**. Si el soporte del LiDAR se apoyaba en él, la
geometría cambió y el URDF describe un carro que ya no existe. **Hay que
re-medir los dos carros antes de grabar nada.** Sin esto, todo lo que se grabe
hoy queda contaminado y no se puede defender.

**0.2 · Se graba `/rplidar_ros/scan`, no `/scan`.** Lo publica el driver de
fábrica que arranca solo con `deepracer-core`. No hay que pararlo ni disputar
`/dev/ttyUSB0`. Son **360 muestras y 12 m**, no las 1328 y 16 m del driver del
proyecto; ese es justamente uno de los desconocidos que esta prueba resuelve.

---

## 1. Bloque A — re-medir la geometría (los dos carros)

| | |
|---|---|
| **Objetivo** | Saber si quitar el caparazón movió el LiDAR respecto al URDF. |
| **Cómo** | Flexómetro desde el piso hasta la **ranura por donde sale el haz**. No la cara superior de la carcasa: eso da 189–190 mm y es el error que ya costó una medida el 21-sep (`Evidencia/S24_tf_hardware_peldano_1.md` §5). |
| **Esperado** | **175 mm ± 3 mm** en los dos carros. |
| **Si falla** | Anota el valor real de cada carro y **para aquí**. Hay que regenerar el URDF con la altura nueva antes de grabar; si no, rf2o trabajará sobre una geometría falsa. Avísame con los dos números y lo regenero. |
| **Cierre** | Dos números anotados, con el nombre del carro al lado. |

Mira también, sin instrumento, si el LiDAR quedó **asentado igual en los dos**:
el montaje es invertido (yaw −180°). Es un sí/no visual y es el parámetro que
más pesa — un error de yaw rota *todos* los barridos, y el flexómetro no lo ve.

---

## 2. Bloque B — preparar la recta

| | |
|---|---|
| **Objetivo** | Tener una verdad de terreno que no dependa del robot. |
| **Cómo** | Marca en el piso un punto de salida y uno de llegada, **en línea recta**, y mide la separación con flexómetro. Marca con cinta, no a ojo. |
| **Longitud** | **6 m.** G-2 pide ≥ 5 m; 6 da margen para que un error de 10 % siga siendo medible. |
| **Si no cabe** | Anota la longitud real que sí cupo. Cualquier recta ≥ 5 m sirve; lo que no sirve es no saber cuánto mide. |
| **Cierre** | Longitud anotada en metros con dos decimales. |

### 2.1 · Dónde, y por qué en dos sitios

**Esto es lo más importante del guion.** Si solo se corre en el pasillo y sale
mal, no se podrá saber si rf2o está roto o si el pasillo es inobservable — y son
conclusiones opuestas. Es el mismo error que invalidó la rampa de tracción del
22-sep: sin control, no se mide nada.

| Orden | Sitio | Qué contesta |
|---|---|---|
| **1º — control** | Un sitio **con estructura a la vista**: el hall del piso 2, o cualquier espacio con esquinas, puertas y muebles a menos de 12 m | ¿La cadena funciona? Aquí rf2o *debe* acertar. Si falla aquí, el problema es la cadena, no el sitio |
| **2º — caso difícil** | El pasillo | ¿Cuánto se degrada? Este es el sitio que G-2 va a medir de verdad |

Si solo da tiempo a uno, **haz el control**. Un control bueno sin pasillo deja
un resultado interpretable; un pasillo sin control, no.

---

## 3. Bloque C — grabar

Tres pasadas por sitio. No es el N de RF-27 (eso sigue pendiente de los
directores); tres basta para ver si la dispersión es pequeña o enorme.

**Por cada pasada:**

1. Pon el carro con su eje delantero sobre la marca de salida.
2. Arranca la grabación (comando abajo) y **espera 5 s quieto**.
3. Empuja el carro **despacio y a velocidad pareja** hasta la marca de llegada.
   Despacio importa: la hoja de campo midió parones de hasta ~600 ms en la
   frecuencia del LiDAR, y a empujón rápido esos huecos se comen el movimiento.
4. **Espera 5 s quieto** en la llegada.
5. Corta la grabación con `Ctrl-C`.

Los dos tramos quietos no son adorno: **enmarcan el movimiento**. Con ellos se
puede separar la deriva del sensor parado del avance real, que es exactamente lo
que distingue «rf2o no sirve» de «el sitio no se deja medir».

| | |
|---|---|
| **Comando** (en el carro, por SSH) | `ssh deepracer@192.168.0.102 "source /opt/ros/jazzy/setup.bash && cd /tmp && ros2 bag record -s mcap -o recta_control_1 /rplidar_ros/scan"` |
| **Esperado** | Al cortar, `ros2 bag info` en el carro debe dar **más de 100 mensajes** y una duración parecida a lo que tardaste. |
| **Si falla** | Si sale 0 mensajes, comprueba que `deepracer-core` está vivo: `ros2 topic hz /rplidar_ros/scan` debe dar 7–10 Hz. |
| **Cierre** | Tres carpetas por sitio, con nombres que digan sitio y número: `recta_control_1..3`, `recta_pasillo_1..3`. |

Anota en papel, por cada pasada: **sitio, número, longitud medida, y cualquier
cosa rara** (que el carro se torció, que alguien pasó por delante, que se enganchó
una rueda). Una pasada con una incidencia anotada sirve; una pasada limpia en
apariencia pero con una incidencia no anotada envenena el promedio.

---

## 4. Bloque D — traer los bags

| | |
|---|---|
| **Comando** | `scp -r deepracer@192.168.0.102:/tmp/recta_* ~/tesis_evidencia/S24_recta_peldano2/` |
| **Esperado** | Cada carpeta con su `metadata.yaml` y su `.mcap` de bastante más de 5123 B. |
| **Después** | Los bags vienen en formato Jazzy y no se abren en el PC tal cual. Se adaptan con `python3 herramientas/adaptar_bag_jazzy.py <carpeta> -o <carpeta>_humble`. Eso lo hago yo. |
| **Cierre** | Los bags en el portátil. A partir de aquí ya es trabajo de escritorio y se puede hacer de noche o el fin de semana. |

---

## 5. Qué se hace con esto después (no es trabajo de campo)

1. Correr rf2o sobre cada bag y sacar el desplazamiento integrado.
2. Compararlo con la longitud del flexómetro. **Criterio de G-2: error ≤ 10 %.**
3. Medir la deriva en los dos tramos quietos. Si un sensor parado acumula
   avance, eso es un hallazgo mayor y hay que escribirlo aparte.
4. Re-medir la fracción de rayos con información de avance, **ahora sin
   caparazón y con 360 muestras**. El 5,1 % / 5,9 % / 17,5 % de
   `Evidencia/S23_informacion_avance_piso2.md` salió de geometría densa y
   simulada; no es comparable y no se puede citar como si lo fuera.

---

## 6. Criterio de cierre del guion completo

Tres bags por sitio, en el portátil, con la longitud de la recta anotada y la
altura del LiDAR re-medida en los dos carros. Con eso, el análisis no necesita
volver a tocar un carro — que es el objetivo, porque los carros solo están entre
semana y el análisis no.
