# El mapa del pasillo no sale, y la causa no es cómo se mueve el carro

**Fecha de la salida:** martes 2026-09-08, 20:00–21:00, pasillo USTA.
**Qué se buscaba:** el Bloque 3 del G2 —la primera pasada, la que produce el mapa contra el que se
miden M1 y M2—. **Resultado: cuatro bags, cuatro mapas rechazados.** El Bloque 5 y las seis pasadas
de localización **no se ejecutaron**, por la regla preinscrita del §7 de
[`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md): sin mapa aceptado no hay contra qué localizarse.

Este documento existe porque el fallo **no es el que se esperaba**, y la hipótesis que traíamos
—«se movió demasiado rápido»— quedó refutada por la propia medida.

---

## 1. Lo que se grabó

Todos los bags son de `/scan`, grabados como usuario `deepracer` con el LiDAR arrancado a mano
(`rplidar_composition`, cinco parámetros del Paso 2.3), sin `sudo`, con la regla de dueños
respetada. Ninguno es un bag vacío: los cuatro pasan `comprobar_movimiento_bag.py`.

| bag | hora | barridos | duración | en movimiento | cómo se movió |
|---|---|---|---|---|---|
| `mapa_pasillo_2009` | 20:11 | 809 | 117,6 s | 89,8 % | conducido con el mando |
| `mapa_pasillo_2029` | 20:31 | 719 | 103,4 s | 89,4 % | conducido con el mando |
| `mapa_pasillo_2046` | 20:49 | 1224 | 178,8 s | 68,2 % | **empujado**, motores apagados |
| `mapa_pasillo_0012` | 4-sep | 918 | 141,3 s | — | **empujado**, batería muriendo |

---

## 2. La medida que refuta la hipótesis del movimiento

Se alineó cada barrido con el siguiente buscando el desplazamiento angular que minimiza la
diferencia mediana de rangos. Da dos cifras por bag: cuánto gira el sensor entre barridos, y cuánto
residuo queda **después** de alinear —o sea, cuánto ha cambiado la geometría por avance—.

| bag | \|yaw\| mediana | pares > 30 °/s | residuo mediana | residuo p90 | rayos válidos | **mapa resultante** |
|---|---|---|---|---|---|---|
| `2046` empujado | **0,0 °/s** | **13 %** | **0,037 m** | — | 152/360 | **1166 × 267 m** |
| `0012` empujado | 0,0 °/s | 19 % | 0,035 m | 0,157 m | 185/360 | 47,5 × 29,1 m |
| `2029` conducido | 13,9 °/s | 40 % | 0,085 m | 0,620 m | 143/360 | 95 × 36 m |
| `2009` conducido | 20,8 °/s | 41 % | 0,099 m | 0,438 m | 158/360 | 62 × 52 m |

Sobre una recta medida de **20,08 m**.

**El orden se rompe.** Conducir sí degrada el dato —el residuo entre barridos se triplica—, pero
**la pasada más suave de las cuatro produjo el peor mapa, por un factor de veinte**. Si el
movimiento fuera la causa, `2046` sería el mejor. Con el movimiento cubriendo todo el rango de
suave a brusco y el fallo presente en los cuatro casos, **más pasadas no aportan información**: por
eso la salida se cerró en vez de repetir.

Imágenes: [`S22_mapa_2046_fallido.png`](S22_mapa_2046_fallido.png) —dos manchas separadas más de un
kilómetro—, [`S22_mapa_2029_fallido.png`](S22_mapa_2029_fallido.png) y
[`S22_mapa_2009_fallido.png`](S22_mapa_2009_fallido.png). Ninguno dibuja una pared.

---

## 3. El sector ciego: 90° medidos, no 60°

Perfil angular de `2046` (fracción de barridos con retorno, rango típico y desviación temporal del
rango, por sectores de 15°):

| sector (marco `laser`) | % con retorno | rango típico | std temporal |
|---|---|---|---|
| **315°–44°** | **0,01–0,08** | — | — |
| 60°–119° | 0,66–0,71 | 1,2 m | 0,40–0,63 |
| 165°–209° | 0,27–0,42 | 4,5–5,6 m | **3,2–4,3** |
| 240°–299° | 0,58–0,68 | 1,6 m | **0,30–0,34** |

El tesista aportó el dato de hardware: **el chasis tapa el LiDAR hacia el frente**, donde van las
cámaras. La medida lo confirma y lo corrige en tamaño: **el hueco mide ~90°, no los 60° supuestos**.

Y explica la geometría del problema. El eje del pasillo es la línea 0°–180°: el sector **165°–209°**
es el extremo abierto —rangos de 4,5–5,6 m con std de 3–4 m, el único sitio donde la geometría
cambia al avanzar— y **el otro extremo del mismo eje es justo el sector ciego**. Los laterales, que
sí se ven, están a 1,2–1,6 m con **std de 0,30**: paredes rectas que no cambian al avanzar.

Para estimar el avance, rf2o dispone de: nada en un sentido del eje, nada útil en los laterales, y
un solo sector parcial —27–42 % de retornos— en el otro sentido. **Es la inobservabilidad
longitudinal del pasillo, medida directamente sobre el sensor** en vez de inferida del error de
llegada.

---

## 4. La discrepancia de 180° entre el URDF y el vehículo

El URDF de la simulación —el mismo modelo de carro— declara en
`deepracer_description/models/xacro/deepracer/deepracer.xacro:46-47`:

    lidar_360_degree_min_angle = -2.61799
    lidar_360_degree_max_angle = +2.61799

que son **exactamente 300°**, con 60° ciegos, y la junta `hokuyo_joint`
(`deepracer_stereo_cameras_and_lidar_urdf.xacro:491-503`) monta el sensor con `rpy = 0 0 3.1416`.
Con ese giro de π, el hueco del modelo cae **hacia el frente del carro**, que es lo que describe el
hardware.

**Pero el dato real no lo cumple.** En los bags el sector ciego está alrededor del **0° del marco
`laser`**; con el giro de π del URDF debería aparecer alrededor de **180°**. Son **180° de
discrepancia**, y no es cosmética: `herramientas/mapear_desde_bag.sh:155-158` publica la TF
`base_link → laser` con ese giro (`qz=1, qw=0`). Si el sensor físico va montado al revés que el
URDF, rf2o entrega el avance con el signo cambiado y slam_toolbox arranca cada emparejamiento con
una estimación que apunta al lado contrario — mecanismo suficiente para producir la fuga de 1166 m.

**Prueba preliminar, no concluyente:** se reconstruyó `2046` con `qz=0, qw=1` (giro nulo) y
slam_toolbox **no llegó a publicar `/map`** (`map_saver`: `Failed to spin map subscription`). No
absuelve ni condena a la hipótesis; queda como primera línea de trabajo de escritorio.

---

## 5. Defectos nuevos, vistos en los registros de las cuatro corridas

Nunca se habían mirado los `slam.log`. Los cuatro traen lo mismo:

| | `2046` | `2029` | `2009` |
|---|---|---|---|
| `sequence size exceeds remaining buffer` | 23 | 23 | 28 |
| barridos descartados por cola llena | 24 | 15 | 9 |
| barridos con longitud distinta de 360 | 54 y 85 muestras | — | — |

El primero es un fallo de **deserialización CDR**: hay mensajes mal formados dentro de `/scan`, del
orden de **25 por bag**. No es la causa principal —25 de 1200— pero es un defecto del sensor o de
la grabación que no estaba documentado. Los barridos de 54 y 85 muestras los rechaza slam_toolbox
explícitamente (`LaserRangeScan contains 54 range readings, expected 360`).

---

## 6. Lo que sí quedó medido y sirve

- **Batería:** apertura `level=8`, cierre `level=7` en ~40 min. Y la dispersión de `/scan` la sigue:
  `level 10 → std 0,003` (8-sep), `level 8 → 0,023`, `level 7 → 0,035`, con la media clavada en
  6,84–6,95 Hz. **Tres puntos monótonos.** Sigue siendo anotación y no puerta —el 8-sep se demostró
  que la `std dev` marca sospechoso un sensor sano 2 de cada 6 veces—, pero la correlación
  batería ↔ dispersión que el §5 de la hoja de campo dejaba abierta ya tiene tres puntos.
- **El lanzador por ruta necesita que el fichero esté en la tarjeta.** `ros2 launch ~/fichero.py`
  falla con `ValueError: '<ruta>' is not a valid package name` cuando el fichero **no existe**:
  ros2launch cae a la rama de nombre de paquete. El síntoma se lee como «no se admiten rutas» y
  significa «no lo copiaste». Costó el arranque de esta salida.
- **Cuenta de tópicos: 24, no 22.** Estable en tres lecturas. Los dos de más respecto al 1-sep son
  `/joy` y `/joy/set_feedback`. El fallo del demonio es **subcontar**, así que sobrecontar no es esa
  avería.

---

## 7. Qué queda abierto, y dónde se resuelve

Todo lo que sigue es **de escritorio, sobre estos cuatro bags**, sin volver al pasillo:

1. **Resolver la discrepancia de 180°** entre el URDF y el montaje real, y corregir la TF de
   `mapear_desde_bag.sh` o el URDF, según cuál esté mal.
2. **Decidir si rf2o puede funcionar en este pasillo.** Con el sector ciego apuntando al eje y
   paredes de std 0,30, puede que la respuesta sea que no, y entonces hace falta otra fuente de
   odometría o mapear con otra técnica.
3. **Los mensajes mal formados de `/scan`**: de dónde salen y si se pueden filtrar.
4. **Nadie ha aceptado nunca un mapa en este proyecto.** La cadena rf2o + slam_toolbox no ha
   producido todavía un mapa válido; hasta que lo haga, no se puede distinguir un fallo del pasillo
   de un fallo de la cadena. **Ese es el primer experimento a montar**, y se puede hacer contra un
   bag de simulación, donde la verdad del terreno se conoce.

**Los cuatro bags se conservan en la tarjeta y copiados en el portátil.** Son la evidencia con la
que se repite el diagnóstico las veces que haga falta.
