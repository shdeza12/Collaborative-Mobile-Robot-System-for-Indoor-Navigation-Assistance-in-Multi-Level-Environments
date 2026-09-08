# Hoja de campo del G2 — la mañana en el pasillo

**Para quien va al pasillo.** Escrita el **2026-09-03 por la noche**, después de una salida de
prueba que falló, y con lo que se aprendió en ella ya incorporado.

**Esto es un extracto operativo, no una guía nueva.** Todo lo que hay aquí sale de dos documentos
que siguen siendo la fuente de verdad, y que hay que abrir cuando algo no cuadre:

| Documento | Qué cubre |
|---|---|
| [`GUIA_PASADA_MAPEO.md`](GUIA_PASADA_MAPEO.md) | La primera pasada: levantar el mapa |
| [`GUIA_PASADA_LOCALIZACION.md`](GUIA_PASADA_LOCALIZACION.md) | La segunda: medir M1 y M2 |
| [`GUIA_TELEOP_MANDO.md`](GUIA_TELEOP_MANDO.md) | El mando, que hace falta en la segunda |

Esta hoja te dice **el orden, los tiempos y las tres trampas**. Los porqués, las variantes y el
diagnóstico completo están allí. Si hay contradicción entre esta hoja y una guía, **manda la
guía**, y avisa para corregir esta hoja.

---

## 1. Qué se trae de vuelta

Si vuelves con esto, la mañana valió:

1. **Un bag de mapeo** con el pasillo recorrido de ida y vuelta, empujando.
2. **Seis bags de localización**, tres por sentido, conduciendo con el mando.
3. **La longitud de la recta medida con flexómetro**, con dos decimales, y una **foto de la cinta
   métrica sobre cada marca**.
4. **La hoja de anotaciones** del §6, rellenada a mano durante la mañana.

**El mínimo irrenunciable, si la mañana se tuerce:** el bag de mapeo, **un** bag de localización
por sentido, y la longitud medida. Con eso hay G2. Con cero bags no hay nada, y con seis bags sin
la longitud tampoco: la longitud es el denominador de M1 y no se puede reconstruir después.

---

## 2. Lo que ya está hecho, y no hay que repetir

La **Parte 1 de la guía de mapeo** —las comprobaciones de escritorio— se corrió entera el
**2026-09-03** y pasó:

- El plugin `ros-humble-rosbag2-storage-mcap` está instalado (`ii 0.15.16-1jammy`).
- La cadena de mapeo corre de punta a punta sobre un bag del 28-ago y produce un `.pgm`.
- La herramienta dice `NO SIRVE` sobre ese bag, que es lo correcto: es un bag malo conocido.

**No hace falta volver a correrlas.** Si aun así quieres, están en la Parte 1 de la guía de mapeo,
con los dos `source` que le faltaban ya corregidos.

**Lo que sí sigue pendiente y no es tuyo:** las **tres preguntas de umbrales firmadas por el
director** (Paso 1.3 de la guía de localización). Sin ellas los bags valen igual y se analizan
igual, pero **el G2 no se declara**. No es motivo para no salir.

---

## 3. Lo que hay que llevar

- **El carro con la batería llena, y comprobada antes de salir.** Ver el aviso de abajo.
- **El mando con su cable USB-C.** Va al carro, no al portátil.
- El portátil cargado, y algo donde apoyarlo en el pasillo.
- **Flexómetro o cinta métrica de obra.** No vale el móvil; el §4 explica por qué. *(Al
  2026-09-07 el marcado ya está hecho y las marcas fijadas en valores exactos, así que el
  flexómetro va sólo por si alguna tira se despegó o si hay que comprobar el ancho.)*
- Cinta de enmascarar y marcador. **Llévalos igual**: las tiras se levantan con el paso de la
  gente, y una marca perdida a mitad de pasillo no se puede reponer a ojo.
- Esta hoja impresa o en el móvil, y un bolígrafo.

**Y una cosa que no se lleva, se hace — con red y antes de salir.** En la tarjeta **no hay ningún
workspace del proyecto** (comprobado el 2026-09-07), así que ni el lanzador del LiDAR ni el teleop
están allí. Los dos viajan sueltos, en un solo comando, desde la raíz del repositorio:

```bash
ping -c 2 deepracer.local
```
```bash
scp Robot/aws-deepracer/deepracer_bringup/launch/lidar_vehiculo.launch.py herramientas/teleop_mando.py deepracer@<IP>:~/
```

**Esperado:** dos líneas `100%`. Si esto falla en el pasillo te quedas sin conducir; si falla en
casa, se arregla en casa. El detalle está en el **Paso 1.5** de
[`GUIA_PASADA_MAPEO.md`](GUIA_PASADA_MAPEO.md), y **el §5 trae la alternativa sin prerrequisitos**
por si aun así no llegó.

> ### La batería es el sospechoso número uno de este proyecto
>
> **Mide la batería antes de salir, y otra vez a mitad de mañana.** No es prudencia genérica: es
> el fallo que más veces ha disfrazado de avería de software lo que era una batería cayendo.
>
> - **28-ago:** «todo dejó de funcionar poco a poco». Se plantearon tres causas de software y
>   **las tres eran falsas**. Eran las baterías.
> - **2026-09-03, de madrugada:** el `/scan` empezó a dar huecos de hasta **0,464 s** con una
>   `std dev` de 0,072. El carro murió veinte minutos después. Ya recargado, el mismo sensor, la
>   misma configuración y los mismos procesos daban `max 0,177 s` y `std dev 0,008`: **nueve veces
>   más estable**.
>
> **Un `/scan` con huecos de medio segundo no construye mapas.** El bag grabado en esa ventana
> produjo un pasillo doblado que no cerró el bucle (ver §7).
>
> **Antes de dar por buena cualquier medida rara, comprueba la batería.** Desde el 2026-09-08 hay
> **medida directa** —`ros2 service call /i2c_pkg/battery_level ...`, ver §5—, que es mejor que
> cualquier proxy. El `max` no sirve, se solapa entre batería sana y muriendo. Y la `std dev` de
> `/scan` **ya no es una puerta**: sigue siendo útil, pero **una sola lectura marca sospechoso un
> sensor sano dos de cada seis veces**, así que se toman tres. Todo el detalle en el **§5**, y se
> anota por bag en el §12.

---

## 4. Bloque 1 — Medir y marcar (~~25 min~~ **HECHO el 2026-09-07; el martes son ~5 min de repaso**)

**Antes de encender nada.** Este número es la verdad de terreno de todo lo demás.

**Puede que las marcas de la salida anterior sigan puestas.** Si es así, **no las des por buenas
sin medirlas otra vez**: se hicieron con el móvil y eso no sirve como referencia, por la razón de
abajo.

> **HECHO el 2026-09-07 por la noche. Este bloque ya no se ejecuta el martes 8.** La recta se
> midió con **flexómetro de instrumentación**, dejando una tira de cinta cada **5 m**, y las
> marcas se **fijaron en valores exactos**: 0 · 5 · 10 · 15 · 20 m.
>
> **Consecuencia, y es la que importa: el mensurando pasa a ser 20,000 m exactos.** Los
> **20,08 m** que aparecen más abajo en «el caso plátano» eran la medida del móvil y **dejan de
> ser la referencia**; se conservan ahí porque son el registro de lo que pasó el 4-sep, no un
> valor vigente. Ninguna cifra nueva se compara ya contra ellos.
>
> **Lo que este cambio NO hace:** no vuelve la incertidumbre cero. Quedan el encadenado de los
> cuatro tramos de 5 m, la colocación de cada marca y el ancho de la propia tira de cinta. Pero
> todo eso vive en los milímetros y centímetros, contra un presupuesto de error de **0,50 m**
> para M2 — o sea, **la medición deja de ser el término que limita**, y el que manda pasa a ser
> AMCL, que es donde tiene que estar. Sobre M1 el efecto es menor todavía: cambiar el
> denominador de 20,08 a 20,000 mueve la razón un **0,4 %**, contra una compuerta de ±10 %. No
> cambia ningún veredicto; cambia de qué se puede presumir.
>
> **Dos cosas que hay que anotar en el §12 antes de salir, porque no se deducen del número:**
> 1. **La clase y la marca del flexómetro.** «De instrumentación» sin clase declarada es un
>    adjetivo; con la clase (I o II) es una incertidumbre que otro puede verificar, y es lo que
>    de verdad sostiene el presupuesto de M2.
> 2. **Qué borde de la tira de cinta es la marca** — el de dentro o el de fuera. Una tira mide
>    2–5 cm de ancho; si el arranque usa un borde y el cierre el otro, se cuela un sesgo
>    sistemático de hasta 5 cm. Es pequeño frente a 0,50 m, pero es **gratis** eliminarlo si se
>    decide ahora y se usa igual en las dos pasadas.

1. Elige la recta más larga y despejada. Tiene que dar **≥ 20 m**.
2. Marca el **0 m** con cinta.
3. Mide con el flexómetro, tramo a tramo, y marca cada **5 m** hasta el final.
4. **Anota la longitud total con dos decimales** y **haz una foto de la cinta métrica apoyada
   sobre cada marca**, con el número legible.
5. Mide el **ancho** en tres puntos y anótalos.
6. **En los dos extremos la marca es una CRUZ, no una raya.** Cinta a lo ancho *y* ~60 cm de cinta
   a lo largo, cruzándose. La cruz define un **punto**; una raya solo define una coordenada, y M2
   se mide contra un punto.
7. **Comprueba que el eje longitudinal está a la misma distancia de la pared en los dos
   extremos.** Si en un extremo el trazo largo va a 1,1 m de la pared izquierda y en el otro a
   1,4 m, la recta que estás midiendo no es la que va a recorrer el carro.

> **Por qué el flexómetro y no el móvil.** El protocolo experimental lo tiene escrito en su §1:
> la verdad de terreno del hardware es *«cinta métrica sobre marcas fijas en el piso,
> fotografiadas»*. Y los números lo respaldan: una medida de móvil vale **±0,20 m**, que sobre una
> recta de ~20 m es **±1,0 %**. El umbral de M2 es 0,50 m, o sea el **2,5 %** — medir con el móvil
> se come el 40 % del presupuesto de error **antes de que el carro se mueva**. El flexómetro vale
> ±0,01 m: el 0,05 %.
>
> Y hay una segunda razón, que es la que de verdad decide: la cinta **rompe el modo común**.
> Compara contra un patrón físico independiente. Cualquier estimación integrada —el móvil, la
> odometría— comparte familia de errores con lo que se está midiendo.

**Criterio de cierre:** longitud anotada con dos decimales, fotos hechas, dos cruces puestas.

---

## 5. Bloque 2 — Arrancar el LiDAR y comprobar que publica (~10 min)

Guía de mapeo, **Pasos 2.2 a 2.5**. Resumen de lo que no se puede saltar:

1. SSH al carro. La IP **cambia entre sesiones**: sácala con `ping -c 2 deepracer.local`.
2. Arranca el LiDAR (Paso 2.3). **Sin `sudo`.** En la tarjeta **no hay workspace del proyecto**, así
   que `ros2 launch deepracer_bringup ...` **no funciona**: o el lanzador por ruta, si lo copiaste
   con el Paso 1.5, o el nodo a pelo, que no tiene prerrequisitos.

       source /opt/ros/jazzy/setup.bash && ros2 launch ~/lidar_vehiculo.launch.py

       source /opt/ros/jazzy/setup.bash && ros2 run rplidar_ros rplidar_composition --ros-args -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=115200 -p frame_id:=laser -p inverted:=false -p angle_compensate:=true
3. **Comprueba que publica de verdad**, con `ros2 topic hz /scan`. Esperado: **~6,6 Hz**.
4. **Comprueba que es `/scan` y no `/rplidar_ros/scan`.** Si sale el segundo, arrancaste por la vía
   de AWS: párala y vuelve al Paso 2.3. Es exactamente el error que hundió los bags del 28-ago.

> **`/rplidar_ros/scan` va a aparecer en la lista de tópicos, y está vacío.** Es el driver de
> `deepracer-core`, que arranca solo con el carro. Comprobado el 2026-09-04 **como `root`**, para
> que el negativo valga: tiene `/dev/ttyUSB0` abierto y **no publica ni un barrido**. Los dos
> drivers acaban con el mismo puerto serie abierto a la vez, cosa fea que nadie ha resuelto, pero
> **no impide grabar**: el del Paso 2.3 arranca igual, anuncia `current scan mode: Express` y
> publica a ~6 Hz. **No pierdas tiempo intentando grabar `/rplidar_ros/scan`.**
5. Levanta el demonio (Paso 2.5) y comprueba que `ros2 topic list | wc -l` da **22 tres veces
   seguidas**.

> **Sobre los huecos en `hz`.** Es normal ver la frecuencia caer un momento y recuperarse; se
> midieron parones de hasta **~600 ms**. Por eso el Bloque 3 dice que empujes **despacio**: con un
> hueco de 600 ms, a 0,5 m/s te quedan 30 cm sin barrido, y a 0,4 m/s, 24 cm. No es una avería,
> es una razón para ir lento.

> ### El `max` no sirve para juzgar la batería. La `std dev` sí
>
> **Anotado el 2026-09-07, antes de la salida, para que sea criterio y no explicación.**
>
> Los dos párrafos de arriba se contradicen si se leen con prisa: el §3 usa un `max` de **0,464 s**
> como la señal de la batería muriendo, y este §5 dice que parones de **~600 ms son normales**. Los
> dos son ciertos, y por eso **`max` no discrimina**: el hueco sano y el hueco enfermo caen en el
> mismo rango, así que un `max` alto no prueba nada en ninguna dirección.
>
> Lo que sí separó los dos casos del 3-sep fue la **dispersión**, con el mismo sensor, la misma
> configuración y los mismos procesos:
>
> | | `std dev` | `max` |
> |---|---|---|
> | Batería cayendo (murió 20 min después) | **0,072 s** | 0,464 s |
> | La misma, recargada | **0,008 s** | 0,177 s |
>
> Un `max` que se solapa; una `std dev` **nueve veces mayor**. La batería no rompe el `/scan`, lo
> vuelve irregular.
>
> **CRITERIO, fijado antes de tener el dato delante, como pide el §7 del protocolo experimental:**
> se anota la `std dev` de `ros2 topic hz /scan` **al abrir y al cerrar cada bag** (columnas
> `std ini` / `std fin` del §12). Un bag cuya `std dev` llegue a **≥ 0,020 s** se marca
> **SOSPECHOSO** y no entra en el cálculo de M1 sin repetirse con la batería cambiada.
>
> El 0,020 no es redondeo: está **2,5 veces por encima** del valor sano medido y **3,6 veces por
> debajo** del degradado, o sea en el hueco vacío entre los dos casos conocidos. Cuesta diez
> segundos por bag y es lo único que delató el caso plátano —aquel día no hubo ni un error, y el
> mapa de 47 m sobre un pasillo de 20 m parecía normal hasta que alguien miró el `/scan`—.
>
> ### REVISADO EL 2026-09-08: seis medidas en vez de una, y el criterio no aguanta como puerta
>
> El criterio de arriba se fijó con **una** lectura sana y **una** degradada. El 8-sep se midió
> seis veces seguidas el mismo sensor **sano**, en cinco minutos, sobre el vehículo:
>
> | Lectura | `std dev` final | `min` | Veredicto del criterio de arriba |
> |---|---|---|---|
> | 1 | 0,070 s | 0,001 s | **SOSPECHOSO** |
> | 2 | 0,0033 s | 0,135 s | sano |
> | 3 | 0,0035 s | 0,133 s | sano |
> | 4 | 0,043 s | 0,005 s | **SOSPECHOSO** |
> | 5 | 0,0031 s | 0,135 s | sano |
> | 6 | 0,0034 s | 0,134 s | sano |
>
> **Dos de seis lecturas marcan SOSPECHOSO un sensor sano.** Con siete bags, marcar mal al menos
> uno es prácticamente seguro. Lo que **no** se deduce es que el criterio sea falso: la medida del
> 3-sep tiene corroboración independiente —el carro murió veinte minutos después—, o sea que
> acierta cuando hay problema. Es **sensible y poco específico**.
>
> **Qué cambia, y solo esto:**
>
> 1. La `std dev` **deja de ser una puerta y pasa a ser una anotación**. No repitas una pasada en
>    el pasillo por una sola lectura alta. El 8-sep eso habría costado la tarde entera con el
>    sensor sano.
> 2. **Tres lecturas de `hz`, no una**, y se anotan las tres. Con 2 artefactos de cada 6, la
>    mediana de tres acierta ~93 % de las veces. Dato que ayuda a leerlas: la **media** se mantuvo
>    en ~7 Hz **también en las lecturas malas**. El artefacto dispersa, no pierde muestras; una
>    media que cae sí es señal de verdad.
> 3. Se añade una **medida directa de batería**, que hasta el 8-sep se creía inexistente:
>
>        sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && ros2 service call /i2c_pkg/battery_level deepracer_interfaces_pkg/srv/BatteryLevelSrv "{}"'
>
>    **Va con `sudo`, y no es un adorno.** Quien sirve `/i2c_pkg/battery_level` es `deepracer-core`,
>    que es de `root`, así que la regla de dueños del §6.2 aplica igual que a un tópico. Sin `sudo`
>    el fallo esperado es **que se quede colgado**, no un error. El 8-sep se midió `level=10` pero
>    **no quedó anotado con qué usuario**, así que se escribe la forma que la regla predice, no la
>    que se supone que se usó.
>
>    Devuelve `level=N` (el 8-sep, con el carro recién cargado, dio **10**). Se anota al abrir y
>    al cerrar cada bag. **Salvedad declarada:** el DeepRacer lleva **dos** baterías —tracción y
>    cómputo— y este servicio lee la del bus I2C. El LiDAR cuelga por USB de la tarjeta, así que
>    puede estar midiendo la que no es. Se anota igual: un número real vale más que ninguno, y
>    comparar `level` contra `std dev` a lo largo de la salida es lo que dirá si sirve.
>
> **HIPÓTESIS PREINSCRITA para esta salida — no es criterio todavía.** En las seis lecturas el
> `min` separa los dos casos sin solaparse: **0,133–0,137 s** sano frente a **0,001–0,005 s** en
> los artefactos. Un `min` muy por debajo del período nominal (0,143 s a 7 Hz) significa mensajes
> llegando en ráfaga, que es algo que el sensor no puede producir. **No se adopta hoy**, porque
> estaría elegido después de ver los datos, que es lo que prohíbe el §6.3 del protocolo. Se anota
> el `min` junto a la `std dev` en las tres lecturas; si vuelve a separarlos con los datos de esta
> salida, sustituye a la `std dev` con derecho.
>
> **Aviso que costó una vuelta el 8-sep:** el mensaje `WARNING: topic ... does not appear to be
> published yet` **no predice nada**. Salió en lecturas buenas y faltó en otras buenas. Ignóralo.

**Criterio de cierre:** `/scan` a ~6,6 Hz, `frame_id: laser`, y 22 tópicos tres veces.

> **Cuidado con contar tópicos, anotado el 2026-09-08.** En el vehículo se vio **dos veces** que la
> introspección no ve un tópico que está vivo: `ros2 topic list` dejó fuera `/rplidar_ros/scan`
> mientras publicaba a 6,99 Hz, y `ros2 topic info` dijo `Publisher count: 0` del mismo tópico. Si
> falta uno, **compruébalo con `ros2 topic hz` antes de darlo por caído**: el conteo puede mentir,
> el `hz` no.

---

## 6. Bloque 3 — La primera pasada: el mapa (~15 min)

Guía de mapeo, **Parte 3**. Esta pasada **se empuja, con los motores apagados**. Es legítimo:
lo único que se graba es el LiDAR, y al LiDAR le da igual quién lo mueve.

### 6.1 Colocar el carro

**El LiDAR va encima de la cruz del 0 m.** No el eje trasero, no el centro del chasis: **el
sensor**.

> Son **11,1 cm** de diferencia entre el eje trasero y el LiDAR, y son **el 22 % del presupuesto
> de M2**, regalados por un detalle de colocación. Pero la razón de peso es otra: `slam_toolbox`
> pone el `(0,0,0)` del mapa donde esté el robot al arrancar, y AMCL arranca asumiendo ese
> `(0,0,0)`. Si el mapa nace aquí, la segunda pasada sale bien sin tocar un parámetro.

Mirando al fondo de la recta. **Anota hacia dónde mira.**

### 6.2 Grabar — y aquí está la trampa que costó la salida anterior

**Mira primero con qué usuario publica `/scan`.** No con `head -1`: hay varios procesos con
`rplidar` en la línea de comandos y el más viejo es el de AWS, que **no** publica `/scan`.

```bash
pgrep -af rplidar | grep -v "__ns:=/rplidar_ros" | grep -v "deepracer_launcher"
```

De las líneas que salgan, coge el PID del `rplidar_composition` —el hijo, no el
`python3 .../ros2 run`— y pregunta `ps -o user= -p <PID>`.

Si dice **`deepracer`** —que es lo normal, porque el Paso 2.3 no lleva `sudo`— **graba como
usuario, sin `sudo`**:

```bash
source /opt/ros/jazzy/setup.bash && cd ~ && ros2 bag record /scan -o mapa_pasillo_$(date +%H%M)
```

Si dice **`root`**, graba con `sudo -i` (el comando exacto está en el Paso 3.1 de la guía).

> **La regla es «los dos extremos con el mismo dueño».** No es «graba como root», que es lo que
> decía la guía hasta anoche. El transporte de este dominio pasa por buzones en `/dev/shm` con
> permisos `-rw-r--r--`, y el publicador tiene que poder **escribir** en el buzón del suscriptor.
> Si los dueños no coinciden, el descubrimiento funciona —el log dice `Recording...` y hasta
> `Subscribed to topic '/scan'`— pero **no llega un solo dato**. Medido:
>
> | Publica `/scan` | Graba | Mensajes |
> |---|---|---|
> | `root` | usuario | **0** |
> | `deepracer` | `root` | **0** |
> | `deepracer` | usuario | **60 en 9 s** |
>
> La fila del medio es la que pasó el 2026-09-03: dos bags perdidos, uno de 22 s y otro de 166 s,
> los dos de **5123 bytes exactos**. El primer bag bueno del proyecto, esa misma noche, pesó
> **2,7 MB para 141 s**. Esa es tu referencia de tamaño.
>
> **Y la regla es más grande que este paso:** en este carro **ninguna comprobación de datos vale
> si quien mira no tiene el mismo dueño que quien publica**. Vale igual para `ros2 topic hz` y
> `ros2 topic echo`. El fallo siempre es **silencio, no error**. Si un tópico parece mudo, repite
> la medida con el dueño correcto antes de creértelo.
>
> **Segunda causa del mismo silencio, medida el 2026-09-08:** el `ros2-daemon` se rompe y **no
> muere, responde mal** — devuelve `!rclpy.ok()` por XMLRPC y `ros2 topic echo` sale *al instante*,
> que sobre la terminal se lee exactamente igual que un tópico mudo. Distinguirlo no cuesta nada:
> **cronometra**. Si `echo` vuelve antes de agotar su `timeout`, no midió nada.
>
> **La regla, resuelta el 2026-09-08 porque estos dos párrafos se contradecían.** El Paso 2.5 de la
> guía de mapeo midió el 1-sep que **con** demonio salen 22 tópicos las tres veces y **sin** él salen
> 2, 10 y 17: `--no-daemon` no es «la versión honesta», es la que **subcuenta**. Y este párrafo midió
> el 8-sep que el demonio puede romperse y mentir. Las dos cosas son ciertas, así que el orden es:
>
> 1. **Trabaja con demonio.** Es el que da la cuenta estable.
> 2. **Compruébalo antes de grabar** con el `22` tres veces del Paso 2.5.
> 3. **Si la cuenta baila, o si `echo` vuelve al instante**, el demonio está roto: reinícialo con
>    `ros2 daemon stop && ros2 daemon start && sleep 3`, y repite la comprobación.
> 4. **`--no-daemon` solo como desempate**, para una consulta suelta, sabiendo que subcuenta. **No
>    se graba** con esa cuenta como única evidencia.

### 6.3 Recorrer

1. **5 s quieto** en el 0 m antes de moverte.
2. **Empuja los ~20 m despacio y a ritmo constante**, en torno a **0,4 m/s**: unos 50 s. Que la
   mano no tape el sensor.
3. **No pares a mitad.** Un tramo largo quieto es lo que arruinó los bags del 28-ago: de 813 s
   grabados aquel día solo había 130 s de sensor moviéndose.
4. **5 s quieto** al llegar.
5. **Vuelve empujando hacia atrás, sin dar la vuelta al carro**, hasta el 0 m. El cierre de bucle
   sobre el mismo pasillo es lo que corrige la deriva acumulada.
6. **5 s quieto** al volver.

Si pasa gente, que pase: un peatón mueve pocos rayos. Lo que arruina la pasada es **pararse a
esperar** a que despejen.

### 6.4 Cerrar y comprobar que no está vacío

**`Ctrl-C` una sola vez**, y espera a que termine solo. El índice y la `metadata.yaml` se escriben
**al cerrar**; un segundo `Ctrl-C` mata el proceso antes.

```bash
ls -la ~/mapa_pasillo_*/ && grep message_count ~/mapa_pasillo_*/metadata.yaml
```

**Esperado:** un `.mcap` y una `metadata.yaml`, y un `message_count` de **tres cifras o más**.

**Si dice `message_count: 0`, esa pasada no existe.** Vuelve al §6.2 y comprueba el usuario. Son
cinco segundos de comprobación que valen media mañana.

**Si falta `metadata.yaml`:** la grabación se cortó de golpe. Repite la pasada.

---

## 7. Bloque 4 — Construir el mapa **allí mismo** (~10 min)

Guía de mapeo, **Partes 4 y 5**. Esto se hace **con el carro todavía en el pasillo y la cinta
todavía puesta**. Es lo que convierte una mañana perdida en una repetición de cinco minutos.

Con el portátil, desde la raíz del repositorio:

1. **Traer el bag:** `scp -r deepracer@<IP>:~/mapa_pasillo_XXXX /tmp/` — sustituyendo `XXXX` por
   el nombre real que anotaste. **Este comando va en el PORTÁTIL**, no en el carro.
2. **Adaptar la metadata:** `python3 herramientas/adaptar_bag_jazzy.py ...` (Paso 4.2). El carro
   escribe metadata versión 9 y Humble solo lee la 5.
3. **Comprobar que el sensor se movió:** Paso 4.3. Tiene que decir `SIRVE`.
4. **Construir el mapa:** Paso 4.4. Tarda **lo que dure el bag**, porque se reproduce a velocidad
   real a propósito.

### Aceptar o rechazar el mapa

Míralo (Paso 5.1) y **mide el pasillo sobre el mapa** (Paso 5.2). Contra la longitud que mediste
con el flexómetro —llámala **L**:

| Longitud en el mapa | Qué se hace |
|---|---|
| **≥ L** | Se acepta |
| Entre **0,90·L** y **L** | Se acepta, **y se anota** el porcentaje que falta |
| **< 0,90·L** | **Se rechaza.** Repite la pasada |

El **ancho** medido sobre el mapa tiene que parecerse al que mediste con el flexómetro.

**Si el mapa es un borrón radial sin paredes**, es un bag sin movimiento: repite la pasada. Así se
ve un mapa malo, y conviene haberlo visto antes.

### El caso plátano, y qué hacer con él

**Esto pasó el 2026-09-04 de madrugada y hay que reconocerlo rápido.** Sobre una recta medida de
**20,08 m**, empujada de ida y vuelta sin girar el carro —o sea, con cierre de bucle perfecto por
construcción— el mapa salió así:

| | Real | En el mapa |
|---|---|---|
| Largo | 20,08 m | **47,50 m** |
| Ancho | ~2,7 m | **29,05 m** |

Un pasillo **curvado**, con las paredes dibujadas varias veces en sitios distintos —abanicos en
forma de diente de sierra— y la vuelta sin superponerse a la ida. Es el trayecto entero
**desenrollado** en vez de cerrado.

**Cómo se reconoce en diez segundos:** el mapa mide **más del doble** de lo que mediste con el
flexómetro, y tuerce.

**Qué hacer, y esto es una regla, no una sugerencia:**

1. **Comprueba la batería primero.** Es la causa más probable, y la de aquella noche: el bag se
   grabó con el `/scan` dando huecos de 0,464 s, justo antes de que el carro muriera.
2. **Si la batería está bien, repite la pasada una vez**, empujando más despacio.
3. **Si el segundo mapa también sale plátano, PARA.** No sigas al Bloque 5.

> **Por qué parar y no seguir.** Las seis pasadas de localización se miden **contra este mapa**.
> Con un mapa que se equivoca en un 240 % en el largo, M1 y M2 no medirían la localización del
> carro: medirían el mapa roto. Serían dos horas de conducción para producir seis números sin
> significado. **Vuelve con el bag de mapeo y el mapa malo** —los dos son evidencia— y se
> diagnostica en el escritorio, que es donde la cadena se puede repetir sin volver al pasillo.

**Sin mapa aceptado no se pasa al Bloque 5.** La segunda pasada no existe sin él: AMCL no tendría
contra qué localizarse.

---

## 8. Bloque 5 — Montar el mando (~20 min)

Guía de localización **Paso 2.3**, que remite a [`GUIA_TELEOP_MANDO.md`](GUIA_TELEOP_MANDO.md),
Partes 1 a 5. Lo que no se puede olvidar:

- El mando va **por USB al carro**, no por Bluetooth al portátil.
- **El teleop entero con `sudo`.** `joy_node` y `teleop_mando.py`, los dos. Sin `sudo` arranca
  todo, no da un error, y el carro no se mueve: el teleop tiene que hablar con `deepracer-core`,
  que es de `root`.
- **Esto no cambia lo del §6.2.** El grabador va con el dueño del LiDAR; el teleop va con `root`.
  Son dos parejas distintas de procesos y la misma regla da resultados distintos.
- **No conectes ni desconectes nada por USB con la pila arrancada.** El bus se re-enumera,
  `/dev/ttyUSB0` se borra y se crea de nuevo, y el nodo del LiDAR se queda con un descriptor a un
  fichero borrado. `systemctl` seguirá diciendo `active (running)`. Miente.
- **Nunca reinicies el carro.** Se queda en GRUB esperando que alguien elija sistema, y en el
  pasillo no hay monitor.

**Criterio de cierre:** el carro avanza, retrocede y gira con el mando, **y `/scan` sigue
publicando** después de haberlo comprobado.

---

## 9. Bloque 6 — Las seis pasadas (~40 min)

Guía de localización, **Parte 3**. **Aquí se conduce, no se empuja.**

> **Por qué.** Empujar despacio le pone las cosas fáciles al algoritmo: a 0,4 m/s hay ~6 cm entre
> barridos, y conduciendo hay ~20 cm. Si esta pasada se empujara, M1 y M2 no dirían nada del
> vehículo: dirían lo que rinde el algoritmo con un sensor movido a mano.

**Seis pasadas, en este orden: ida, vuelta, ida, vuelta, ida, vuelta.** Alternar reparte el efecto
de la batería, que baja a lo largo de la mañana, entre los dos sentidos.

> **Por qué los dos sentidos.** El error no es simétrico y está medido: sobre el mismo pasillo
> simulado, `rf2o` se equivocó **5,7 % hacia el este y 1,3 % hacia el oeste**. Un factor de cuatro.
> Con un solo sentido sacas uno de esos dos números y no sabes cuál te tocó. **No se promedian.**

Cada pasada, en este orden:

1. **Colocar** con el LiDAR encima del cruce de la cruz, chasis alineado con el trazo largo. El
   rumbo a ojo, ±3°, es tolerable.
2. **Empezar a grabar** — mismo comando y misma comprobación de usuario que en el §6.2, cambiando
   el nombre a `g2_ida_1`, `g2_vuelta_1`, etc.
3. **5 s quieto.** Es la ventana de referencia de la que sale el origen de M1. Sin ella, el
   análisis tiene que adivinar dónde empieza la pasada, y ahí se cuelan decímetros.
4. **Conducir** hasta la cruz del otro extremo: velocidad constante, sin turbo, sin paradas, sin
   volantazos. Si vas a chocar, suelta el gatillo y **anota que la pasada se abortó**. Un bag
   abortado cuesta 40 segundos; un carro roto cuesta el proyecto.
5. **Parar con el LiDAR encima del cruce.** Ajústalo empujando a mano si hace falta: lo que se
   mide es dónde cree AMCL que está, no lo bien que conduces.
6. **5 s quieto.** Ventana de llegada.
7. **`Ctrl-C` una vez**, y **`grep message_count`**.
8. **Anotar la pasada** en la tabla del §12.

**Regla dura: no se recoge la cinta con menos de un bag válido por sentido.** Si la mañana se va,
se va con dos bags, no con cero.

**Después de la primera ida y la primera vuelta, para y comprueba** (Parte 4 de la guía de
localización). Si algo está mal, lo descubres con dos bags perdidos y no con seis.

---

## 10. Bloque 7 — La escala de tracción (RF-14). **Solo si el G2 ya está cerrado**

**Esto no es G2 y no compite con él.** El §1 no cambia: si vuelves sin este bloque, la mañana valió
igual. Se hace **únicamente** cuando el mínimo irrenunciable ya está grabado —el bag de mapeo, un
bag de localización por sentido y la longitud medida—. Si el G2 se torció, recoge y vete: esto
tiene su propia sesión.

**Por qué aquí, entonces.** Porque el vehículo, el mando y una recta medida con flexómetro solo
coinciden hoy, y RF-14 lleva desde el 28-ago esperando exactamente eso. Está en el
[`PLAN_S22.md`](PLAN_S22.md) como la primera tarea de holgura del martes.

### 10.1 Qué falta, con los números del código y no de memoria

`cmdvel_to_servo_node.py` convierte `/cmd_vel` en `ServoCtrlMsg` por escalones, y los tres
umbrales salen de dividir por `MAX_SPEED = 4,0 m/s` (`cmdvel_to_servo_pkg/constants.py`):

| Velocidad pedida en `/cmd_vel` | `throttle` que sale |
|---|---|
| **< 0,40 m/s** | **0,0 — nada** |
| 0,40 – 1,20 m/s | 0,5 |
| 1,20 – 2,00 m/s | 0,8 |
| ≥ 2,00 m/s | 1,0 |

Nav2 pide **0,25 m/s en curva y 0,05 en la aproximación**. Las dos caen en la primera fila, así que
**la cadena devuelve cero justo donde Nav2 la usa**.

Los dos defectos de **mapeo** están corregidos desde el 27-ago, con 19 comprobaciones en
`prueba_mapeo_servo.py`. Lo que queda es la **escala**, y no se arregla leyendo código:
`MAX_SPEED = 4,0 m/s` es una **suposición heredada de AWS** y de ella cuelgan los tres umbrales.
Si el carro real no hace 4 m/s, la tabla entera está corrida.

**La pregunta de hoy, y solo esa:** ¿cuánta velocidad real da un `throttle` dado?

**Criterio de cierre**, tomado del `PLAN_S22.md`: una tabla de `throttle` contra velocidad medida,
**con al menos un punto por debajo de 0,25 m/s**.

### 10.2 La trampa de dueños muerde aquí de otra forma

`/scan` lo publica el LiDAR del Paso 2.3, **sin `sudo`** — usuario `deepracer`.
`/ctrl_pkg/servo_msg` lo publica `teleop_mando.py`, que va **con `sudo`** — usuario `root`. Por la
regla de los dos extremos del §6.2, **un solo `ros2 bag record` no puede traerse los dos**: el que
grabe como usuario se llevará `/scan` y **cero** mensajes de servo, y no dirá una palabra.

Así que **dos bags a la vez, uno por dueño**. Se emparejan luego por reloj, que es el mismo porque
los dos salen de la misma tarjeta.

Terminal de usuario:

```bash
source /opt/ros/jazzy/setup.bash && cd ~ && ros2 bag record /scan -o escala_N
```

Terminal de `root`:

```bash
sudo -i bash -c "source /opt/ros/jazzy/setup.bash && cd ~deepracer && ros2 bag record /ctrl_pkg/servo_msg -o escala_N_servo"
```

**Comprueba los dos `message_count` al cerrar.** Un `escala_N_servo` con 0 mensajes es la trampa de
dueños otra vez, no un mando averiado.

> **Si no te distrae, arranca también el bag de servo durante las seis pasadas del §9.** Es gratis
> para el G2 —va en su propio bag, y si falla no toca el de `/scan`— y da datos de conducción real
> además de los del barrido. Si te añade carga mental en el bloque que produce lo irremplazable,
> **sáltatelo**: el G2 manda.

### 10.3 El barrido, y por qué sale una nube y no una tabla limpia

El mando es **analógico**: `teleop_mando.py` escala el gatillo hasta `limite_normal = 0,35`, y
hasta `0,70` con turbo. **No hay escalones**, así que sostener un valor a mano da una nube.

Se acepta a propósito, porque la nube ya responde la pregunta del §10.1 con margen de sobra: si a
0,35 de `throttle` el carro hace medio metro por segundo, `MAX_SPEED = 4,0` está mal por un factor
de tres, y eso se ve sin ninguna precisión. La tabla fina de escalones sostenidos necesita un nodo
que publique un valor fijo con hombre muerto, y eso es código que hoy no existe.

Cuatro tramos sobre la recta ya marcada, **sin turbo**, en este orden:

1. Gatillo **al mínimo con el que el carro se mueva**. Búscalo con paciencia.
2. Gatillo a **un cuarto** de recorrido, sostenido hasta el otro extremo.
3. Gatillo a **medio** recorrido.
4. Gatillo **a fondo** — que sigue siendo 0,35, porque el turbo no se usa.

En cada tramo: **5 s quieto, recorrer sosteniendo el gatillo, 5 s quieto.** Son las mismas dos
ventanas de quietud que usa `medir_g2.py`, así que el análisis ya sabe leerlas.

**Si solo da tiempo a una cosa, que sea el punto 1.** Dónde empieza a moverse el carro es el número
que decide si 0,05 m/s es siquiera alcanzable, y hoy no existe en ningún documento.

### 10.4 Qué significa cada resultado, decidido antes de medir

| Lo que salga | Qué quiere decir |
|---|---|
| A 0,35 de `throttle`, **~0,5 m/s** | `MAX_SPEED` real ≈ 1,4 m/s y no 4,0. Se recalculan los tres umbrales y el escalón bajo cae donde Nav2 lo usa. RF-14 se cierra calibrando |
| A 0,35 de `throttle`, **~1,4 m/s o más** | La escala no está lejos; entonces el problema es la **resolución** —cuatro escalones— y no el factor. Decisión aparte, no se improvisa en el pasillo |
| Por debajo de cierto gatillo **no se mueve nada** | Ese es el suelo físico del motor. Si queda por encima de 0,25 m/s, **RF-14 no se cierra calibrando**: es una limitación medida y Nav2 necesita otra estrategia de aproximación |

La tercera fila es un resultado **válido**, y hay que traerla escrita si es lo que pasa. **No se
ajusta el criterio para que salga bien**, que es el reproche que este proyecto ya se hizo el 26-ago.

### 10.5 Al volver: qué se corre con los dos bags

Nada de esto se hace en el pasillo. Por cada tramo, en el portátil:

```bash
python3 herramientas/adaptar_bag_jazzy.py /tmp/escala_N
bash herramientas/localizar_desde_bag.sh /tmp/escala_N_humble <mapa>.yaml /tmp/salida_escala_N
python3 herramientas/medir_escala_traccion.py /tmp/salida_escala_N/trayectoria.csv /tmp/escala_N_servo/escala_N_servo_0.mcap
```

`<mapa>.yaml` es el mismo mapa que aceptaste en el §7: la barrida se hace en el pasillo que ya
mapeaste, así que no hace falta uno nuevo. Al bag de **servo** no se le pasa
`adaptar_bag_jazzy.py`: se apunta directo a su `.mcap` y rosbag2 saca los tópicos del propio
archivo, que es la salida que ya se usó con `bag_mapa_1456` el 2026-09-01.

[`medir_escala_traccion.py`](../herramientas/medir_escala_traccion.py) empareja el `throttle` con
la velocidad que salió de la odometría, saca el **umbral de arranque** y el **`MAX_SPEED`
implícito**, y decide entre las tres filas del §10.4 sin que nadie tenga que interpretarlas.

**Lee el CDR del `ServoCtrlMsg` a mano y no necesita el tipo de AWS**, así que el análisis se hace
en el portátil y no en la tarjeta. Y **se niega a dar cifra** —no da una aproximada— si los dos
bags no se solapan en el tiempo, si el de servo está vacío, o si una muestra cae en un hueco de la
odometría.

---

## 11. Las tres trampas, en una tabla

Cada una de estas costó una salida. Ninguna avisa.

| Trampa | Cómo se ve | Cómo se evita |
|---|---|---|
| **Grabador con distinto dueño que el LiDAR** | `Recording...`, `Subscribed to topic '/scan'`, y un `.mcap` de 5123 bytes | Averiguar el dueño real con el `pgrep -af ... \| grep -v` de §6.2 —**nunca con `head -1`**, que devuelve el proceso de AWS— y grabar con ese mismo dueño |
| **LiDAR en `/rplidar_ros/scan`** | Todo parece bien; el mapa sale vacío en el portátil | `ros2 topic hz /scan` en el sitio (§5) |
| **Sensor quieto la mayor parte del bag** | El mapa es un borrón radial sin paredes | Empujar sin parar, y comprobar con la herramienta del Paso 4.3 **antes de recoger** |
| **La batería cayendo** | El `hz` de `/scan` se vuelve irregular, y el mapa sale doblado | Medirla antes de salir y a mitad de mañana (§3) |

Y una regla que resume el resto: **`ros2 bag info` y `systemctl status` no demuestran nada.**
`bag info` lee la metadata sin abrir el `.mcap`. `systemctl` ha dicho `active` con el LiDAR muerto,
con `deepracer-core` reiniciado y con nodos invisibles para el grafo. **Comprueba siempre por el
dato que sale.**

Con una excepción, que es útil: `message_count` **sí** delata un bag vacío, porque lo escribe el
propio grabador. Verde ahí no prueba nada; **rojo ahí es definitivo**.

---

## 12. Hoja de anotaciones

**El pasillo** (rellenar en el Bloque 1):

```
longitud total  : __20__ , _000_ m     (FIJADA con flexometro el 2026-09-07,
                                        marcas exactas en 0/5/10/15/20 m)
clase del flexometro (I o II)   : ____________  marca: ____________
el borde de la cinta que cuenta : DE DENTRO / DE FUERA   (el mismo en las dos pasadas)
ancho punto 1   : ______ , ____ m
ancho punto 2   : ______ , ____ m
ancho punto 3   : ______ , ____ m
eje al muro izq., extremo 0 m   : ______ , ____ m
eje al muro izq., extremo final : ______ , ____ m
fotos de las marcas hechas      : SI / NO
el carro mira hacia ____________________ en el 0 m
```

**Las pasadas** (una línea por bag):

```
nombre           sentido        hora  msgs  ab.  AL ABRIR  std/min/lvl   AL CERRAR std/min/lvl   incidencias
------------------------------------------------------------------------------------------------------------------
mapa_pasillo_    ida y vuelta   ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
g2_ida_1         0 -> final     ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
g2_vuelta_1      final -> 0     ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
g2_ida_2         0 -> final     ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
g2_vuelta_2      final -> 0     ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
g2_ida_3         0 -> final     ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
g2_vuelta_3      final -> 0     ____  ____  __   0,____ / 0,____ / __   0,____ / 0,____ / __   ________________
```

**`std` / `min` / `lvl`**, al abrir y al cerrar cada bag: la `std dev` y el `min` de
`ros2 topic hz /scan`, y el `level` de `/i2c_pkg/battery_level`.

**REGLA REVISADA EL 2026-09-08, lee el §5 antes de usarla:** se toman **tres** lecturas de `hz`
cada vez, no una, y en la casilla va la **mediana**, no la última. Una sola lectura marca
sospechoso un sensor sano dos de cada seis veces. **La `std dev` ya no es una puerta: es una
anotación.** No repitas una pasada en el pasillo por ella. El `min` se anota porque es la
hipótesis preinscrita del §5. El `max` **no** se anota: se solapa entre batería sana y batería
muriendo, así que no distingue.

**Las incidencias importan.** Alguien cruzándose, una rueda subida a un zócalo, una pausa. En el
análisis, un valor raro **con una nota al lado es un dato**; sin la nota es basura.

**El barrido de tracción del §10**, si se llega a hacer. Una línea por tramo:

```
tramo   gatillo            se movio  hora    msgs /scan  msgs servo  incidencias
-----------------------------------------------------------------------------------------
1       minimo que mueve   SI / NO   ____    ____        ____        ________________
2       un cuarto          SI / NO   ____    ____        ____        ________________
3       medio              SI / NO   ____    ____        ____        ________________
4       a fondo, sin turbo SI / NO   ____    ____        ____        ________________
```

**`msgs servo` en cero no es un mando averiado: es la trampa de dueños del §10.2.** Los dos bags
se cierran y se comprueban por separado.

---

## 13. Si algo va mal

| Síntoma | Dónde está la respuesta |
|---|---|
| El bag sale con `message_count: 0` | §6.2 de esta hoja |
| `ros2 topic hz /scan` dice `no new messages` | Guía de mapeo, Paso 2.4 |
| Sale `/rplidar_ros/scan` en vez de `/scan` | Guía de mapeo, Paso 2.3 |
| El mapa es un borrón radial | Guía de mapeo, §0.3 y Paso 4.3 |
| El carro no se mueve con el mando, y no da error | Guía del mando, §0.2 ter. Es el `sudo` |
| El carro se para solo cada segundo mientras conduces | Falta `autorepeat_rate` en `joy_node` |
| `Ctrl-C` no cierra el teleop | Entraste por SSH sin `-t` |
| El LiDAR deja de publicar y `systemctl` dice `active` | Tocaste el USB con la pila corriendo |
| Todo «deja de funcionar» poco a poco | **Mide las baterías antes de depurar nada.** El 28-ago se plantearon tres causas de software y las tres eran falsas |
| La `std dev` de `/scan` llega a 0,020 s o más | **Repítela dos veces más antes de concluir nada** (revisado el 2026-09-08: 2 de cada 6 lecturas dan eso con el sensor sano). Si la **mediana de tres** sigue alta **o la media de `hz` cae por debajo de ~7 Hz**, entonces sí: batería. Consulta `level` y anota (§5 y §12) |
| El mapa sale mucho más largo que el pasillo medido | §7, «el caso plátano». Mira primero la `std dev` anotada de ese bag |
| Se te ocurre reiniciar el carro | **No.** Se queda en GRUB |

Las tablas completas de diagnóstico están en la **Parte 7** de cada una de las dos guías.

---

## 14. Lo último, antes de recoger

- ¿El mapa está aceptado, mirado y medido? (§7)
- ¿Hay al menos un bag válido por sentido, con `message_count` comprobado?
- ¿Está anotada la longitud con dos decimales y hechas las fotos?
- ¿Está rellenada la hoja del §12, **con las dos `std dev` de cada bag**?

**El §10 no entra en esta lista a propósito.** Es extra: si no se hizo, las cuatro de arriba
siguen bastando para recoger. Si sí se hizo, comprueba que **los dos** bags de cada tramo tienen
mensajes, porque uno vacío deja el otro sin con qué emparejarse.

**Si las cuatro son que sí, recoge la cinta.** Si alguna es que no, la cinta se queda: repetir con
la cinta puesta cuesta cinco minutos, y volver otro día cuesta una mañana.
