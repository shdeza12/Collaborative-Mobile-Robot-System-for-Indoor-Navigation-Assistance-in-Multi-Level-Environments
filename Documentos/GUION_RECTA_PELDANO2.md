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

**La regla es apagar el otro carro. No hay comprobación en vivo que la
sustituya**, y esto se midió con los dos carros encendidos el mismo 23-sep:

| Lo que se probó | Resultado | Por qué no sirve |
|---|---|---|
| `ros2 topic info … \| grep 'Publisher count'` | Dice **1** los primeros ~5 s de cualquier proceso recién arrancado, y **2** después | El descubrimiento DDS tarda. Leerlo rápido da un 1 tranquilizador y falso |
| El mismo comando, ya asentado | Dice **2** aunque no esté entrando ni un dato del otro carro | Sobre-avisa: descubrir no es recibir. Los dos carros veían 2 publicadores y cada uno recibía 7,4–7,7 Hz, o sea **un** sensor |
| `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` al grabar | El bag sale con **0 barridos** | Existe en Jazzy y aísla de verdad — tanto que bloquea también el driver del propio carro, que anuncia por la interfaz de red y no por *loopback* |

Lo peor del caso es que **el cruce de datos es intermitente**: esta mañana un bag
grabado en `.102` salió a 14,68 Hz con los dos sensores dentro, y por la tarde
los dos carros se descubrían y **ninguno** recibía los datos del otro. No se
puede predecir mirando.

**Por eso la comprobación no es antes, es después, y sobre el bag ya grabado:**

```
python3 ~/comprobar_movimiento_bag.py ~/<bag>
```

Se corre **en el propio carro**, sobre el bag nativo y sin adaptarlo — probado
bajo Jazzy el 23-sep, con las mismas cifras que en el portátil. Si dice
`el bag esta contaminado por un segundo sensor`, esa pasada se repite. El
comprobador ya está copiado en los dos vehículos.

**0.2 · Se graba `/rplidar_ros/scan`, no `/scan`.** Lo publica el driver de
fábrica que arranca solo con `deepracer-core`. No hay que pararlo ni disputar
`/dev/ttyUSB0`. Son **360 muestras y 12 m**, no las 1328 y 16 m del driver del
proyecto; ese es justamente uno de los desconocidos que esta prueba resuelve.

---

## 1. Bloque A — el yaw, que es lo único que queda abierto

**La altura ya está cerrada, no la vuelvas a medir.** Salió 190 mm de altura
total en los dos carros, el mismo número que con el caparazón puesto el 21-sep
(§0.1). Lo que queda es un sí/no mirando, sin instrumento:

| | |
|---|---|
| **Objetivo** | Que el LiDAR esté asentado **igual de invertido en los dos carros**. El montaje es a 180° (`qz=1, qw=0` en la TF). |
| **Cómo** | Míralos uno al lado del otro. El soporte es atornillado: no admite un ángulo arbitrario, o está asentado o no. El fallo realista no es «rotado 7°», es «montado al revés», y es discreto. |
| **Esperado** | Los dos iguales. |
| **Si falla** | **Para y corrígelo antes de grabar.** Esto sí es compuerta: un error de yaw rota *todos* los barridos y la trayectoria sale girada, no desplazada — y nada de lo que se grabe después se puede salvar en análisis. |
| **Cierre** | «Iguales» anotado, con la fecha. |

> **Por qué el yaw sí y la altura no.** En `CLaserOdometry2D.cpp` el incremento
> de movimiento solo escribe las componentes de traslación 0 y 1 (líneas
> 955–956): la altura entra como desplazamiento constante en `robot_pose_` y **no
> toca el desplazamiento estimado**, que es la cifra de G-2. El yaw, en cambio,
> rota cada barrido antes de compararlo con el anterior. El flexómetro mide
> precisamente el parámetro que no pesa, y no ve el que sí.

> **Si algún día hay que volver a medir la altura, el punto de referencia.** Con
> el caparazón puesto se midieron **175 mm** a la ranura del haz y **189–190 mm**
> a la cara superior del disco: la cara superior va **14–15 mm por encima** de la
> ranura, y esa distancia es del sensor, no del caparazón. Mide las dos cosas y
> apunta las dos; si la diferencia sale 14–15 mm, sabes cuál es cuál sin
> discutirlo. Esa confusión ya costó una medida el 21-sep
> (`Evidencia/S24_tf_hardware_peldano_1.md` §5).

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
2. Arranca la grabación (comando abajo) y **espera 15 s quieto**, no 5. Diez de
   esos quince son puro descarte: el grabador **no escribe nada durante los
   primeros ~5,5 s**, aunque ya haya dicho `Subscribed to topic`. Medido dos
   veces el 23-sep sobre `.102`: 8 s de reloj dieron 2,46 s de bag, y 12 s
   dieron 6,57 s. Los otros cinco son el tramo quieto de verdad, el que el §5
   usa para medir la deriva. Con los 5 s de antes, el tramo quieto no habría
   existido: se lo habría comido el arranque.
3. Empuja el carro **despacio y a velocidad pareja** hasta la marca de llegada,
   con el cronómetro corriendo: **no menos de 70 s**. Despacio importa dos
   veces: por el umbral de los 60 s del recuadro anterior, y porque la hoja de
   campo midió parones de hasta ~600 ms en la frecuencia del LiDAR, y a empujón
   rápido esos huecos se comen el movimiento.
4. **Espera 5 s quieto** en la llegada.
5. **No cortes nada.** La grabación se corta sola a los 100 s. Si terminas
   antes, quédate quieto hasta que la consola diga `Recording stopped`.

Los dos tramos quietos no son adorno: **enmarcan el movimiento**. Con ellos se
puede separar la deriva del sensor parado del avance real, que es exactamente lo
que distingue «rf2o no sirve» de «el sitio no se deja medir».

| | |
|---|---|
| **Comando** (en el carro, por SSH) | `ssh deepracer@192.168.0.102 "source /opt/ros/jazzy/setup.bash && cd ~ && timeout -s INT 100 ros2 bag record -s mcap -o recta_control_1 /rplidar_ros/scan"` |
| **El `timeout -s INT` no es un adorno: sin él no hay bag** | Ensayado el 23-sep. Con `Ctrl-C` sobre un `ssh host "orden"` —sin `-t`, que es como está escrito— **la señal no llega al grabador**: muere el cliente de `ssh` en el portátil y el grabador sigue vivo en el carro, huérfano. Lo que queda en disco es un `.mcap` de **0 bytes y sin `metadata.yaml`**, o sea ilegible; y el huérfano sigue grabando, así que la pasada siguiente se le mezcla dentro. Con `timeout -s INT` la señal sí llega: sale `Recording stopped`, se escribe el `metadata.yaml` y no queda ningún proceso vivo. |
| **La cuenta de los 100 s** | ~6 de arranque en vacío + 5 quieto + 70 de empuje + 5 quieto ≈ 86, y el resto es holgura. Sobra tiempo a propósito: si la grabación se corta antes de que llegues, la pasada no sirve, mientras que unos segundos quietos de más al final no estorban. |
| **Esperado** | `ros2 bag info` en el carro debe dar **más de 100 mensajes**. A los 7–10 Hz medidos, 100 s de reloj son ~700 mensajes y una duración de bag de ~94 s, no de 100. |
| **Si falla** | Si sale 0 mensajes, comprueba que `deepracer-core` está vivo: `ros2 topic hz /rplidar_ros/scan` debe dar 7–10 Hz. Si sale un `.mcap` de 0 bytes y sin `metadata.yaml`, es que se cortó a mano: queda un grabador huérfano y se mata con `pkill -f 'ros2 bag record'` —al morir, vuelca lo grabado y escribe el `metadata.yaml`, así que **mátalo antes de repetir**, no después. |
| **Dónde graba** | En el **home** del carro, no en `/tmp`. Es donde ya viven los bags de las campañas anteriores y donde el §3.1 y el Bloque D los buscan. `.102` tiene 19 GB libres; una pasada de 70 s pesa ~1,6 MB, así que las seis son ~10 MB. |
| **Cierre** | Tres carpetas por sitio, con nombres que digan sitio y número: `recta_control_1..3`, `recta_pasillo_1..3`. |

### 3.1 · Revisa la primera pasada antes de hacer las otras cinco

Esto es lo que faltó el 28-ago: los cinco bags se dieron por buenos en el sitio
y el desastre se descubrió cuatro días después, en el escritorio, cuando ya no
había forma de repetirlos. El comprobador **corre en el propio carro**, sobre el
bag nativo, sin traerlo ni adaptarlo — verificado hoy contra `~/prueba_scan` del
`.102`, y da las mismas cifras que en el portátil.

| | |
|---|---|
| **Antes de salir** | Nada. El comprobador **ya está en los dos carros**, copiado el 23-sep en `~/comprobar_movimiento_bag.py`. |
| **Tras la primera pasada** | `ssh deepracer@192.168.0.102 "source /opt/ros/jazzy/setup.bash && python3 ~/comprobar_movimiento_bag.py ~/recta_control_1"` |
| **Esperado** | `sensor en movim.` por encima de **60 s**, `sensor quieto` por debajo del **40 %**, y **ningún** aviso de contaminación. |
| **Si falla por tiempo** | Repite **esa** pasada más despacio antes de grabar las demás. No sigas con las otras dos: saldrían con el mismo defecto. |
| **Si falla por contaminación** | El otro carro está encendido. Apágalo y repite la pasada. No se salva en análisis. |
| **Cierre** | Una pasada que el comprobador acepta. A partir de ahí, las otras dos con el mismo ritmo. |

**Y pásale el comprobador a las otras cinco también.** Cuesta veinte segundos por
bag y es la única defensa real contra la contaminación, que es intermitente y no
avisa (§0.1 bis).

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
| **Comando** | `mkdir -p ~/tesis_evidencia/S24_recta_peldano2 && scp -r deepracer@192.168.0.102:recta_\* ~/tesis_evidencia/S24_recta_peldano2/` |
| **Por qué así, y no más corto** | Tres detalles, los tres comprobados contra el carro el 23-sep. **(1)** Los bags están en el **home** del carro, no en `/tmp`: es donde los deja el Bloque C. **(2)** El `mkdir -p` no sobra: con varios orígenes, `scp` exige que el destino ya exista; si no, aborta y **no copia nada**. **(3)** El `\*` va escapado para que el comodín lo resuelva el **carro**. Sin escapar lo resuelve el portátil, que busca `recta_*` en tu directorio actual y no lo encuentra. |
| **Esperado** | Cada carpeta con su `metadata.yaml` y su `.mcap` de bastante más de 5123 B. |
| **Si falla** | El mensaje será `No such file or directory` en los dos casos posibles, así que **no basta con leerlo**. Si acaba en `/`, falta el destino: relanza con el `mkdir -p`. Si no, los bags no están donde el Bloque C dijo, y se comprueba con `ssh deepracer@192.168.0.102 "ls -d ~/recta_*"`. **No borres nada del carro hasta que los seis estén en el portátil y abiertos.** |
| **Después** | Los bags vienen en formato Jazzy y no se abren en el PC tal cual. Se adaptan con `python3 herramientas/adaptar_bag_jazzy.py <carpeta> -o <carpeta>_humble`. Eso lo hago yo. |
| **Cierre** | Los bags en el portátil. A partir de aquí ya es trabajo de escritorio y se puede hacer de noche o el fin de semana. |

---

## 5. Qué se hace con esto después (no es trabajo de campo)

1. Correr rf2o sobre cada bag y sacar el desplazamiento integrado.
2. Compararlo con la longitud del flexómetro. **Criterio de G-2: error ≤ 10 %.**
3. Medir la deriva en los dos tramos quietos. Si un sensor parado acumula
   avance, eso es un hallazgo mayor y hay que escribirlo aparte.
4. Medir la información de avance **del sitio de la recta**, con el bag ya
   grabado:

   ```
   python3 herramientas/medir_informacion_avance.py <bag> /rplidar_ros/scan
   ```

   Los valores contra los que se lee, todos ya medidos:

   | referencia | muestras | índice |
   |---|---|---|
   | pasillo de 46,9 m, donde el mapa salió corto (sim.) | 1328 | 5–7 % |
   | caja cerrada de 7,70 m, control bueno (sim.) | 1328 | 12,5–13,8 % |
   | sitio interior real, bag `sin_caparazon` | 360 | 34,7 % |

   Si el sitio de la recta cae cerca del 5–7 %, el desplazamiento medido va a
   salir corto y eso **no** será un fallo de la grabación. El 5,1 % / 5,9 % /
   17,5 % de `Evidencia/S23_informacion_avance_piso2.md` es de geometría densa y
   simulada: no es comparable y no se cita como si lo fuera.

---

## 6. Criterio de cierre del guion completo

Tres bags por sitio, en el portátil, con la longitud de la recta anotada y el
yaw comprobado a ojo en los dos carros. Con eso, el análisis no necesita volver a
tocar un carro — que es el objetivo, porque los carros solo están entre semana y
el análisis no.
