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

**0.1 · Se quitó el caparazón — y RESUELTO: no movió el LiDAR.** Se temía que el
soporte se apoyara en el caparazón y que al quitarlo cambiara la geometría, lo
que dejaría el URDF describiendo un carro que ya no existe. **No pasó.** La
medida de cierre es la altura total del vehículo:

| | con caparazón (21-sep) | sin caparazón (23-sep) |
|---|---|---|
| Piso → punto más alto del carro | 189–190 mm | **190 mm** |

El mismo número. El caparazón nunca fue el punto más alto, y el LiDAR no se
movió. **La geometría del 21-sep sigue vigente y el URDF no se toca.**

Queda una discrepancia menor, anotada y sin consecuencia: midiendo el LiDAR como
una pieza de 20 mm con el haz en su mitad, el rayo saldría a 180 mm; midiendo la
ranura directamente el 21-sep salió a **175 mm**, que es lo que el URDF dice
(175,7 mm). Las dos medidas directas de ese día —190 arriba y 175 a la ranura—
sitúan el haz a 14–15 mm de la tapa, no a 10. No se persigue: los 5 mm no entran
en el desplazamiento estimado (ver el recuadro del Bloque A).

**0.1 bis · SOLO UN CARRO ENCENDIDO. Esto arruina la prueba entera si falla.**
Los dos vehículos publican `/rplidar_ros/scan` con **el mismo nombre**, sin
namespace, y ninguno define `ROS_DOMAIN_ID`: los dos caen en el dominio 0. Si los
dos están encendidos, el `ros2 bag record` de uno graba **también el LiDAR del
otro**, intercalados, y el bag queda inservible sin que nada lo avise.

No es una hipótesis: le pasó al bag `bag_ez9n` del 23-sep. Los dos carros
quietos sobre la mesa y el análisis contestó «59,1 % de movimiento» y una
trayectoria de 11 m.

**Antes de cada grabación**, en el carro que va a grabar:

```
ros2 topic info /rplidar_ros/scan --verbose | grep 'Publisher count'
```

Tiene que decir **1**. Si dice 2, apaga el otro carro antes de seguir.

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
| **Esperado** | **175,7 mm ± 3 mm** en los dos carros. |
| **Si falla** | Anótalo y **sigue adelante**: la altura no entra en la medida (ver el recuadro). Lo que sí para la prueba es que los **dos carros discrepen entre sí**, porque eso ya no es el montaje sino un carro torcido. |
| **Cierre** | Dos números anotados, con el nombre del carro al lado. |

> **Corregido el 2026-09-23: la altura no invalida la medida.** Este guion decía
> que sin regenerar el URDF «rf2o trabajará sobre una geometría falsa».
> **Es falso.** En `CLaserOdometry2D.cpp`, el incremento de movimiento solo
> escribe x e y (líneas 955–956); la altura entra como desplazamiento constante
> en `robot_pose_` y no toca el desplazamiento estimado. Un error de z no
> cambia el resultado de G-2.
>
> Lo que sí lo cambia es el **yaw** —rota todos los barridos— y el `x` del brazo
> de palanca. La medida de altura se toma igual, porque hace falta para los
> costmaps del peldaño 6 y porque es barata, pero **no es una compuerta**.

> **Cuidado con el punto de referencia, que ya costó una medida.** Con el
> caparazón puesto se midieron **175 mm** a la ranura del haz y **189–190 mm** a
> la cara superior del disco: la cara superior va **14–15 mm por encima** de la
> ranura, y esa distancia es del sensor, no del caparazón.
>
> Si el número que sacas no cuadra, mide **las dos cosas** y apunta las dos. La
> diferencia entre ellas tiene que salir 14–15 mm; si sale eso, sabes cuál es
> cuál sin discutirlo.

Mira también, sin instrumento, si el LiDAR quedó **asentado igual en los dos**:
el montaje es invertido (yaw −180°). Es un sí/no visual y es el parámetro que
más pesa — un error de yaw rota *todos* los barridos, y el flexómetro no lo ve.

---

## 2. Bloque B — preparar la recta

| | |
|---|---|
| **Objetivo** | Tener una verdad de terreno que no dependa del robot. |
| **Cómo** | Marca en el piso un punto de salida y uno de llegada, **en línea recta**, y mide la separación con flexómetro. Marca con cinta, no a ojo. |
| **Longitud** | **15–20 m si el sitio lo permite.** El mínimo de G-2 es 5 m, pero la longitud no es lo que manda: manda el **tiempo**. Ver el recuadro. |
| **Si no cabe** | Anota la longitud real que sí cupo, y compénsalo empujando **más despacio**. Lo que no sirve es no saber cuánto mide. |
| **Cierre** | Longitud anotada en metros con dos decimales. |

> **La regla que manda: cada pasada tiene que durar 60 s de movimiento.**
> `comprobar_movimiento_bag.py` rechaza un bag con menos de **60 s de
> movimiento** o más del **40 % de sensor quieto**. Esos umbrales salen del
> desastre del 28-ago, cuando cinco bags se dieron por buenos por tener «cifras
> grandes» y el 84 % resultó ser un LiDAR parado en el suelo.
>
> Los metros no bastan por sí solos, y aquí me equivoqué antes en este mismo
> guion: **20 m empujados a 0,5 m/s son 40 s, y los rechaza igual.** Lo que hay
> que cumplir es el reloj:
>
> | Longitud de la recta | Velocidad máxima | Cómo se siente |
> |---|---|---|
> | 20 m | 0,33 m/s | paso lento |
> | 15 m | 0,25 m/s | paso muy lento |
> | 10 m | 0,17 m/s | casi arrastrando |
> | 6 m | 0,10 m/s | 60 s para 6 m, incómodo pero válido |
>
> **En la práctica no midas velocidad: mide tiempo.** Cronómetro del teléfono al
> empezar a empujar; si llegas a la marca antes de **70 s**, la pasada no sirve y
> se repite más despacio. Los 70 s en vez de 60 s son el margen, porque el
> detector no cuenta como movimiento todo lo que tú sí percibes.
>
> Con 70 s de movimiento y los 5 s de parada de cada extremo, el sensor quieto
> queda en un 12 %, muy por debajo del 40 %.

> **Aviso para el pasillo: puede salir «quieto» aunque te muevas, y eso sería un
> hallazgo, no un fallo de grabación.** El detector mide la **mediana** del
> cambio entre rayos separados 1 s. En un pasillo largo, los rayos que apuntan a
> las paredes laterales no cambian al avanzar — es la inobservabilidad
> longitudinal de siempre, que es justo lo que mide el 5,9 % de rayos con
> información de avance. La mediana la fijan esos rayos inmóviles.
>
> Cómo distinguirlo: si el bag **de control** sale con buen porcentaje de
> movimiento y el **del pasillo** sale «quieto» con el mismo empuje y la misma
> duración, no repitas la pasada buscando que pase. Anótalo: el pasillo es
> inobservable incluso para el detector de movimiento, y eso es material para
> el documento.

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
3. Empuja el carro **despacio y a velocidad pareja** hasta la marca de llegada,
   con el cronómetro corriendo: **no menos de 70 s**. Despacio importa dos
   veces: por el umbral de los 60 s del recuadro anterior, y porque la hoja de
   campo midió parones de hasta ~600 ms en la frecuencia del LiDAR, y a empujón
   rápido esos huecos se comen el movimiento.
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

### 3.1 · Revisa la primera pasada antes de hacer las otras cinco

Esto es lo que faltó el 28-ago: los cinco bags se dieron por buenos en el sitio
y el desastre se descubrió cuatro días después, en el escritorio, cuando ya no
había forma de repetirlos. El comprobador **corre en el propio carro**, sobre el
bag nativo, sin traerlo ni adaptarlo — verificado hoy contra `~/prueba_scan` del
`.102`, y da las mismas cifras que en el portátil.

| | |
|---|---|
| **Antes de salir, una vez** | `scp herramientas/comprobar_movimiento_bag.py deepracer@192.168.0.102:/tmp/` |
| **Tras la primera pasada** | `ssh deepracer@192.168.0.102 "source /opt/ros/jazzy/setup.bash && python3 /tmp/comprobar_movimiento_bag.py /tmp/recta_control_1"` |
| **Esperado** | `sensor en movim.` por encima de **60 s**, y `sensor quieto` por debajo del **40 %**. |
| **Si falla** | Repite **esa** pasada más despacio antes de grabar las demás. No sigas con las otras dos: saldrían con el mismo defecto. |
| **Cierre** | Una pasada que el comprobador acepta. A partir de ahí, las otras dos con el mismo ritmo. |

El aviso `no es '/scan'` que saldrá es esperado y no es un problema: rf2o
escucha `/scan` y el remapeo se hace al reproducir, en el escritorio.

Anota en papel, por cada pasada: **sitio, número, longitud medida, segundos que
tardaste, y cualquier cosa rara** (que el carro se torció, que alguien pasó por delante, que se enganchó
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
