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

Sobre una **recta de ensayo** medida de **20,08 m** —hoy 20,000 m exactos, remedidos con
flexómetro el 7-sep—. Es el tramo origen-destino que se marcó con cinta para medir odometría y
mapeo, **no el largo del pasillo**, que es bastante mayor y sigue sin medir. La distinción importa:
lo que condiciona a rf2o no es cuánto recorre el carro sino qué tiene el sensor delante mientras
lo recorre (§8.6).

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

El primero se leyó como un fallo de **deserialización CDR** —mensajes mal formados dentro de
`/scan`, del orden de **25 por bag**—, y **eso quedó refutado el mismo día**. Corriendo la cadena
sobre un bag de **simulación** aparece **23 veces, y en los cuatro logs a la vez**: `slam.log`,
`rf2o.log`, `play.log` y **`tf.log`**. El publicador de TF estática **no se suscribe a `/scan`**,
así que el mensaje no puede venir del contenido del barrido. Es el aviso cosmético de
descubrimiento de Fast-DDS ya documentado el 2026-08-19, lo emite cada nodo al arrancar, y **no
es un defecto de este proyecto**. Se deja escrito porque la lectura equivocada estuvo a punto de
abrir una línea de trabajo sobre un sensor sano.

Lo que **sí** es real es lo segundo y lo tercero: barridos descartados por cola llena, y los
barridos de 54 y 85 muestras, que slam_toolbox rechaza explícitamente
(`LaserRangeScan contains 54 range readings, expected 360`).

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

## 7. El experimento de control: la cadena falla también en simulación

*Añadido la misma tarde del 2026-09-08, de escritorio, sin volver al pasillo.*

El §8 de abajo listaba como **primer** experimento montar la cadena contra un bag de simulación,
porque mientras no exista **un** mapa aceptado no se puede distinguir un fallo del pasillo de un
fallo de la cadena. Se montó, y el resultado cambia el diagnóstico entero.

### 7.1 El banco

Bag **`S21_piloto_bajada_01`** de la campaña de OE4: 2896 barridos de `/robot2/scan` en 289,6 s,
con `robot2` recorriendo **43,932 m en X** de un pasillo de 46,8 m. Es el banco correcto por tres
razones y conviene decirlas:

- El barrido simulado es de **600 muestras sobre 300°** —medido en el bag, coincide con el URDF—,
  o sea **el mismo hueco al frente** que el vehículo real.
- La verdad de terreno es **exacta**: en simulación `/robot2/odom` sale de `model_->WorldPose()`,
  no de una estimación. Y el mapa de referencia `mundo_definitivo_piso2.yaml` ya está **aceptado**
  por `verificar_mapa.py` (cobertura 100,2 % X × 100,9 % Y, 0 de 7608 obstáculos falsos).
- La TF `base_link → laser` del guion **es la del URDF de ese mismo robot**, luego es correcta por
  construcción. Aquí no hay discrepancia de montaje que valga.

Se construyó un bag derivado con **solo `/scan` y marco `laser`** —la forma exacta de un bag de
campo— para que `mapear_desde_bag.sh` corriera **sin tocar una línea**: lo único que cambia entre
esta corrida y las del pasillo es la entrada.

**Criterio fijado antes de correr**, y no inventado para la ocasión: es la corrección de M1 que ya
propuso [`S21_preparacion_G2.md`](S21_preparacion_G2.md) §4 —`|mapa ÷ verdad − 1| ≤ 0,10`, de dos
lados— contra la extensión del mapa ya aceptado, **46,9 m X × 10,6 m Y**.

### 7.2 El resultado

| | X | Y |
|---|---|---|
| verdad (mapa aceptado) | 46,9 m | 10,6 m |
| **mapa reconstruido** | **17,90 m** | 10,25 m |
| desviación | **−61,8 % · NO PASA** | −3,3 % · pasa |

**La cadena falla también en simulación**, con datos perfectos, TF correcta y verdad conocida. Pero
**falla al revés que en el pasillo**: allí el mapa reventaba a 1166 m, aquí **se encoge**. Imagen:
[`S22_mapa_simulacion_encogido.png`](S22_mapa_simulacion_encogido.png).

### 7.3 De quién es el encogimiento: se grabó la odometría de rf2o

Se repitió la corrida grabando `/odom`. **2852 poses de rf2o contra una verdad de 43,932 m en X y
90,82 m de camino:**

| | rf2o | verdad | registro |
|---|---|---|---|
| extensión en X | 16,646 m | 43,932 m | **37,9 %** |
| camino recorrido | 45,51 m | 90,82 m | **50,1 %** |

Y el mapa mide 17,90 m contra los 16,65 m que abarca rf2o, o sea rf2o **más la huella del sensor**:
**slam_toolbox no corrige prácticamente nada.** El mapa *es* el error de rf2o hecho visible.

**Es el tercer punto de R3, y el más limpio.** Los dos anteriores, sobre el bag `mision3`, daban
**5,7 %** y **1,3 %**. Tres medidas independientes, tres veces muy por debajo de 100.

### 7.4 Tres hipótesis refutadas con datos, incluidas dos propias

1. **«Se movió demasiado rápido»** — refutada en el §2: la pasada más suave dio el peor mapa.
2. **«Hay mensajes CDR mal formados en `/scan`»** — refutada en el §5: aparecen 23 veces en
   `tf.log`, y el publicador de TF estática no se suscribe a `/scan`.
3. **«La discrepancia de 180° del URDF explica la fuga»** — refutada aquí. Se corrió el **mismo**
   bag con la TF girada 180° a propósito:

   | corrida | TF | mapa en X |
   |---|---|---|
   | `mapa_sim` | yaw = π (la del guion) | 17,90 m |
   | `mapa_sim2` | yaw = π, repetición | **17,90 m** |
   | `mapa_sim_yaw0` | yaw = 0 (mal 180°) | 17,80 m |

   **10 cm de diferencia sobre 17,9 m.** Y tiene sentido a posteriori: una rotación pura de π con
   el sensor casi sobre el eje **gira** la trayectoria, no la deforma. Las dos repeticiones con
   yaw = π dan la misma cifra al centímetro, así que esto no es ruido: es un resultado.

   La discrepancia de 180° **sigue siendo real y hay que arreglarla** —importa para que AMCL se
   localice después sobre un mapa con la orientación que espera—, pero **no es la causa del fallo
   de mapeo** y arreglarla no daría un mapa aceptado.

### 7.5 Lo que esto decide

**La cadena rf2o + slam_toolbox no puede mapear este pasillo**, ni el simulado ni el real. No es la
batería, no es el mando, no es el CDR, no es el montaje del sensor. Es la inobservabilidad
longitudinal del §3, ahora medida **sobre la cadena de mapeo** y no inferida del error de llegada.

**Consecuencia de planificación, que es lo que importa a cuatro días de la congelación de código:
volver al pasillo no arregla esto.** Con la TF corregida y la batería llena el mapa seguiría
saliendo corto, porque sale corto en simulación con datos perfectos.

---

## 8. La causa raíz, medida: rf2o no es el problema, el pasillo uniforme sí

El §7 dejó dicho que la cadena falla también en simulación, y de ahí se concluyó que el fallo era
«de la cadena». **Esa conclusión era prematura y aquí se corrige.** El §7 midió el síntoma; faltaba
preguntar por qué.

### 8.1 Dónde se pierde el movimiento

Se comparó, ventana a ventana de 1 s, el desplazamiento que estima rf2o contra la verdad de terreno
del bag de simulación, **descompuesto en el marco del robot**. Esa descomposición es la que decide,
porque un factor de escala afecta a todo por igual y una inobservabilidad no.

> **Cómo se repite.** [`herramientas/medir_registro_odometria.py`](../../herramientas/medir_registro_odometria.py),
> pasándole el bag con el `/odom` de rf2o y el bag de simulación con la odometría exacta. El `/odom`
> de rf2o no está en el bag original: hay que reproducirlo con rf2o corriendo —como en
> `mapear_desde_bag.sh`— y grabarlo aparte con `ros2 bag record -o /tmp/odom_rf2o /odom`.

| componente | rf2o | verdad | razón |
|---|---|---|---|
| **longitudinal** | 34,94 m | 90,02 m | **0,388** |
| lateral | 3,51 m | 3,08 m | 1,143 |
| rotación | 11,22 rad | 10,64 rad | 1,055 |

**Lo lateral y la rotación se estiman bien. Solo se pierde el avance.** No es un factor de escala,
y descarta de golpe cualquier explicación que afecte al barrido entero: ni el reloj, ni la TF, ni
la deserialización, ni el `freq` de rf2o —que además vale 1,0 fijo en el fuente
(`CLaserOdometry2D.cpp:153`) y se cancela entre el `dt(u) = fps*(...)` de la línea 507 y el
`incrx = kai_loc_fil(0)/fps` de la 898—.

### 8.2 El interruptor

La pérdida no es constante: por bloques de 30 s la razón salta entre 0,997 / 0,999 / 0,817 y
0,068 / 0,085 / 0,111. Agrupando por lo que el sensor tiene delante:

| estructura al frente | ventanas | razón longitudinal |
|---|---|---|
| menos de 6 m | 16 | **0,998** |
| 6–9 m | 76 | **0,255** |

En las ventanas ciegas el alcance frontal está **clavado en 7,40 m mientras el robot avanza 1,00 m**.
No es saturación: el sensor simulado llega a 10,0 m. Es la pared lateral vista por el borde del
sector, a distancia invariante.

> **Cómo se repite, y para qué sirve de aquí en adelante.**
> [`herramientas/medir_visibilidad_frontal.py`](../../herramientas/medir_visibilidad_frontal.py)
> produce esa tabla. Su uso previsto ya no es diagnóstico sino **preventivo**: correrlo sobre un bag
> de reconocimiento dice, antes de comprometer una campaña, si el sitio aporta la estructura que la
> cadena necesita.

### 8.3 El mecanismo

rf2o estima el movimiento **solo** del cambio entre barridos consecutivos. En un pasillo recto y
uniforme cada rango queda determinado por la posición lateral y el rumbo, y **no depende de la
posición longitudinal**: el robot avanza y el barrido siguiente es idéntico al anterior. rf2o
devuelve casi cero, y *acierta* —desde el punto de vista del sensor no ha pasado nada—. Lo lateral
y la rotación sí cambian el barrido, y por eso sí se estiman.

**No es un defecto del algoritmo ni un parámetro mal puesto: la información no está en el dato.**
Es el §3 —inobservabilidad longitudinal— medido por fin sobre la cadena de mapeo.

### 8.4 El ensayo controlado que lo confirma

Criterio y predicción fijados **antes** de correr, como exige el §6.3 del protocolo: el mismo
`|mapa ÷ verdad − 1| ≤ 0,10` de `S21_preparacion_G2.md`, y razón longitudinal **≥ 0,90**.

Entorno: `pasillo_test.world`, el modelo `pasillo_usta`, una caja **cerrada** de 7,70 × 2,70 m
interiores. Desde cualquier punto las dos paredes de los extremos entran en los 10 m del sensor, así
que el avance sí es observable. Movimiento: **recta pura de ida y vuelta**, 4 travesías de 5,6 m,
22,4 m en total a 0,33 m/s —la misma velocidad de `S21_piloto_bajada_01` y sin un solo giro—,
conducido por [`herramientas/conducir_recta.py`](../../herramientas/conducir_recta.py), que fija el
movimiento para que la única variable del ensayo sea la geometría del entorno. La
única variable que cambia respecto al pasillo largo es la geometría del entorno.

| | pasillo de 46,9 m | caja cerrada de 7,7 m |
|---|---|---|
| razón longitudinal | 0,388 (0,209 en recta) | **1,010** |
| por bloques de 30 s | 0,068 … 0,999 | 1,015 / 1,008 / 0,997 |
| cobertura del mapa | 38,2 % X — **NO PASA** | **98,1 % X, 95,0 % Y — pasa** |
| obstáculos inventados | — | **0 de 755 (0,0 %)** |
| veredicto de `verificar_mapa.py` | RECHAZADO | **ACEPTADO** |

**Es el primer mapa que este proyecto acepta con SLAM.** Queda en
`Documentos/Evidencia/S22_mapa_caja_SIMULACION_aceptado.{pgm,yaml,png}` y vuelve a verificar desde ahí.

### 8.5 Dos defectos reales que salieron del ensayo

El mapa de la caja salió **rechazado en el primer intento**, y por dos motivos que no tenían nada que
ver con SLAM. Los dos se arreglaron y los dos afectan a cualquier mapa que produzca esta cadena.

1. **`map_saver_cli` escribe `free_thresh: 0.25` y el valor 205 para «desconocido».** 205 son 0,196
   de ocupación, por debajo de 0,25, así que **map_server lee como LIBRE cada celda que el mapa
   declara desconocida** y Nav2 planifica por donde nadie ha mirado. Los mapas vigentes del
   repositorio traen 0,1, que es el valor bueno; los que salían de esta cadena, no.
   `mapear_desde_bag.sh` ya lo corrige al guardar.
2. **El origen del `.yaml` está en el marco `map`, que slam_toolbox sitúa donde arrancó el
   vehículo, no en el origen del mundo.** El robot nació en x = −3,0 y el mapa salió corrido 3 m;
   `verificar_mapa.py` leyó **el 47 % de los obstáculos como inventados**. Restado el corrimiento,
   **0,0 %**. El guion ahora lo avisa al terminar. Es una trampa seria: el mapa es correcto y el
   informe dice que está lleno de paredes falsas.

### 8.6 Lo que esto cambia

- **La cadena rf2o + slam_toolbox funciona.** Lo que no funciona es pedirle que mapee un pasillo
  recto y uniforme más largo que el alcance del sensor. Volver al pasillo con la misma cadena y
  mejor conducción no arregla nada, porque el dato no contiene la información.
- **El criterio pasa a ser medible antes de salir a campo:** hace falta estructura no uniforme
  dentro del alcance del sensor a lo largo de todo el recorrido.
- **El largo del pasillo real no se conoce, y es el dato que decide.** *(Corregido el 2026-09-08,
  el mismo día: una versión anterior de este párrafo daba el pasillo por 20,08 m y concluía que
  está mejor condicionado que el simulado de 46,9 m. **Es falso, y la conclusión que colgaba de
  ahí se retira.**)* Los 20,08 m —hoy **20,000 m** exactos, remedidos con flexómetro el 7-sep— son
  el **largo de la recta de ensayo**, marcada con cinta cada 5 m entre un origen y un destino que
  se eligieron para medir odometría y mapeo. Es el mensurando de M1, no la geometría del edificio.
  **El pasillo es bastante más largo que eso** y nadie lo ha medido.
- **Y la corrección no es neutra: apunta al lado malo.** Lo que el §8.3 mide no es el largo total
  sino si el sensor tiene estructura no uniforme delante. Una recta de 20 m **contenida dentro de
  un pasillo uniforme mucho más largo** es exactamente la geometría que falla: los extremos nunca
  entran en los 12 m del LiDAR y, entre ellos, cada barrido es igual al anterior. Es el caso del
  pasillo simulado de 46,9 m, no el de la caja cerrada de 7,7 m donde las dos paredes de los
  extremos se ven siempre. **Así que el pasillo real podría estar peor condicionado, no mejor.**
- **Nada de esto está medido todavía**, y hacen falta dos cosas, ninguna cara: *(a)* los bags de la
  campaña del 2026-09-07, que están solo en la tarjeta —los de agosto no sirven,
  `comprobar_movimiento_bag.py` los da quietos el 100 %, 74 %, 100 % y 89 % del tiempo—; *(b)* el
  **largo real del pasillo y dónde están sus rupturas** —puertas, columnas, cruces, cambios de
  ancho—, que es un dato de flexómetro y libreta, no de robot, y que se puede tomar en la misma
  visita en la que se recojan los bags.

---

### 8.7 Una medida que sí sirve sobre bags reales, y la predicción que falló primero

Las dos herramientas del §8.1 y §8.2 exigen verdad de terreno, y **en el carro no la hay**: el
DeepRacer no lleva encoders, así que su `/odom` *es* la estimación de rf2o y usarla como referencia
sería circular. Hacía falta algo que decidiera con `/scan` y nada más.

**Qué mide.** Por cada rayo se estima la normal de la superficie sobre la que cae, ajustando una
recta por mínimos cuadrados totales a los 7 puntos cartesianos vecinos y descartando los saltos de
rango, que son bordes y no superficies. El índice es la fracción de rayos cuya normal queda a menos
de 45° del eje de marcha: son los únicos cuyo rango cambia al avanzar. Un solo barrido basta; **no
compara instantes**, y por eso no puede confundir un sensor quieto con un entorno sin información,
que es el defecto por el que hubo que retractar la primera métrica del 2026-09-08.
Herramienta: [`herramientas/medir_informacion_avance.py`](../../herramientas/medir_informacion_avance.py).

**La primera predicción falló, y conviene que conste.** Fijada antes de correr (§6.3): caja ≥ 10 %,
pasillo ≤ 5 %, separación ≥ 2×. Medido: **caja 14,5 %, pasillo 26,7 %** — al revés. La tentación era
retocar umbrales; en vez de eso se buscó la causa, y no era un defecto de la medida: **los dos bags
no se mueven igual.** `S21_piloto_bajada_01` es un piloto con giros, y durante un giro las paredes
laterales quedan oblicuas al eje del robot, con lo que su rango sí cambia al avanzar. El índice subía
porque de verdad había información. Confirma el mecanismo el propio bag: rf2o registró 0,388 del
avance en todo el recorrido pero solo 0,209 en las rectas.

**Segunda predicción, fijada antes de correr y cumplida.** Restringiendo los dos bags a recta pura
—`|giro| ≤ 0,05 rad/s` y `v ≥ 0,10 m/s`, medidos con la verdad de simulación usada *solo para
seleccionar* barridos comparables, nunca para calcular el índice—: mediana del pasillo ≤ 8 % y
separación ≥ 1,8×.

| entorno | sintético exacto | bag real, todo | bag real, **recta pura** |
|---|---|---|---|
| caja cerrada de 7,70 m | 12,5 % | 14,5 % | **13,8 %** (p10 10,0) |
| pasillo de 46,9 m | 5,2 % | 26,7 % | **6,8 %** (p10 5,7) |
| separación | 2,4× | 0,54× ✗ | **2,03× ✓** |

La columna sintética es geometría analítica sin robot —dos paredes paralelas y sus tapas— y sirve de
patrón: el estimador reproduce el valor exacto, y con el ruido del LiDAR simulado (σ = 0,01 m,
`deepracer.xacro:52`) no se mueve. A σ = 0,02 m sí empieza a inflarse, y eso acota su uso.

**Condición de uso, que es el resultado más importante de esta sección.** El índice es instantáneo y
correcto por barrido, pero **solo es comparable entre recorridos con movimiento parecido**. Para un
bag de reconocimiento en línea recta —el caso de campo— vale la mediana. Para uno con giros hay que
mirar el decil inferior, que es donde están los tramos sin información: el mapa se encoge en esos, no
en el promedio.

**Nota de método.** El bag de control de la caja se había grabado en `/tmp` y se perdió al limpiarse
el directorio. Se regeneró el 2026-09-09 con el mismo procedimiento del §8.4 —`conducir_recta.py`,
0,33 m/s, 4 travesías de 5,6 m— y quedó en `~/tesis_evidencia/S22_caja_control_02`. Que se pudiera
rehacer sin discutir nada es el argumento a favor de haber guardado el conductor como herramienta; que
hubiera que rehacerlo es el argumento contra grabar en `/tmp`.

---

## 9. Qué queda abierto, y dónde se resuelve

1. ~~**Resolver la discrepancia de 180°**~~ **Sigue abierta pero baja de prioridad** (§7.4): es
   real y hay que arreglarla para AMCL, pero no causa el fallo de mapeo.
2. ~~**Decidir si rf2o puede funcionar en este pasillo.**~~ **Decidido con datos el 2026-09-08:
   no.** 37,9 % de registro en simulación, 5,7 % y 1,3 % en las medidas de agosto.
3. ~~**Los mensajes mal formados de `/scan`**: de dónde salen y si se pueden filtrar.~~
   **Cerrado el mismo 2026-09-08, y en falso:** no son mensajes mal formados, es el aviso de
   descubrimiento de Fast-DDS. Ver el §5 corregido.
4. ~~**Nadie ha aceptado nunca un mapa en este proyecto.**~~ **Cerrado el 2026-09-08 (§8.4): la
   cadena produjo un mapa ACEPTADO en la caja cerrada, con 98,1 % de cobertura y 0 obstáculos
   inventados.** La conclusión que el §7 sacó —«el fallo es de la cadena»— **queda corregida**: la
   cadena funciona; lo que falla es pedirle un pasillo uniforme más largo que el sensor.
5. ~~**De dónde sale el mapa del pasillo real, si no de SLAM.**~~ **Replanteado con el §8:** ya no
   hace falta renunciar a SLAM por principio. La pregunta correcta es si el pasillo real cumple la
   condición del §8.6 —estructura no uniforme dentro de los 12 m del LiDAR a lo largo de todo el
   recorrido—, **y eso está sin medir**: los 20,000 m son la recta de ensayo, no el pasillo, que es
   bastante más largo. Sigue disponible el precedente de R10 —`generar_mapa_desde_mundo.py` derivó
   el mapa de la geometría y pasó `verificar_mapa.py` con 99,7 %— como salida segura si la medida
   dice que no, y hoy esa vía es **más** probable que ayer, no menos.
6. **Traer al portátil los bags de la campaña del 2026-09-07, y medir el pasillo.** Los bags están
   solo en la tarjeta, y sin ellos no se puede aplicar al pasillo real la medida del §8.7 —la del
   §8.1 no sirve allí, porque exige verdad de terreno y el carro no la tiene—. El largo
   del pasillo y la posición de sus rupturas —puertas, columnas, cruces— se toman con flexómetro en
   la misma visita. Las dos cosas juntas deciden entre las dos vías del punto anterior; ninguna
   necesita conducir el carro.

**Los cuatro bags se conservan en la tarjeta.** Son la evidencia con la que se repite el
diagnóstico las veces que haga falta.
