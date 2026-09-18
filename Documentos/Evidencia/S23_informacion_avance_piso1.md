# El pasillo real no le da a rf2o de dónde sacar el avance: 5,1 % medido

**Fecha:** 2026-09-17 · **Semana:** S23 · **Objetivo:** OE2 (localización sobre el vehículo) ·
**Riesgo:** R3 · **Bag:** `~/tesis_evidencia/S23_info_piso1` (1.259 barridos, 125,9 s)

Esta medida contesta la pregunta que R3 tenía abierta desde el 2026-08-26 y que
[`S22_mapeo_pasillo_fallido.md`](S22_mapeo_pasillo_fallido.md) §9.5 dejó escrita con estas
palabras: *«la pregunta correcta es si el pasillo real cumple la condición del §8.6 —estructura no
uniforme dentro de los 12 m del LiDAR a lo largo de todo el recorrido—, y eso está sin medir»*.

**Ya está medida. No la cumple.**

---

## 1. La predicción se registró antes de correr

Esto importa porque el proyecto ya se equivocó una vez por leer el dato y construir la explicación
después. La predicción quedó escrita en la conversación antes de lanzar la simulación:

> El índice de rayos informativos en `mundo_definitivo_piso1` saldrá entre **5 % y 8 %**, o sea
> junto al 6,8 % del pasillo que falló y lejos del 13,8 % de la caja que se aceptó. Si sale por
> encima del 10 %, el modelo de la geometría es falso y hay que rehacer el análisis.

**Resultado: 5,5 % global, 5,1 % en el tramo uniforme.** La predicción se cumple por el lado bajo.

---

## 2. De dónde sale la geometría, y por qué esto habla del edificio

`mundo_definitivo_piso1` **no es un dibujo aproximado**: se midió en sitio y se construyó a imagen
y semejanza del pasillo real de la USTA (procedencia declarada por Santiago Hernández, autor del
modelado, 2026-09-17). Esta procedencia no estaba escrita en ningún documento del repositorio
hasta hoy, y es lo único que sostiene que una medida hecha en simulación diga algo del edificio.

La firma del trazado lo respalda: **41 paredes** con largos como `5,68966`, `0,459773`, `3,11204`
—cotas de plano, no números tecleados a ojo—, frente a las **13** paredes de números redondos del
modelo antiguo `primer_piso`.

El mapa que se carga (`deepracer_bringup/maps/mundo_definitivo_piso1.yaml`) lo dibujó
[`generar_mapa_desde_mundo.py`](../../herramientas/generar_mapa_desde_mundo.py) de esa geometría,
que es el método de R10 —el que pasó `verificar_mapa.py` con 99,7 %—, así que **no arrastra error
de construcción**.

---

## 3. La geometría, medida sobre el mapa que se va a cargar

Un primer intento de caracterizarla **falló, y el fallo enseña cuál es la medida buena.** Se
contaron las esquinas de las 41 paredes proyectadas sobre el eje del pasillo: salieron 70 rupturas
y un tramo ciego máximo de 6,13 m, del que se concluyó —en voz alta y por escrito— que el pasillo
estaba bien condicionado. **Es falso.** La mayoría de esas paredes son de salones que el vehículo
nunca ve desde dentro del pasillo, y contarlas es contar información que el sensor no recibe.

La medida correcta es el contorno del **espacio libre**, que es lo que el LiDAR sí ve:

| Magnitud | Valor |
|---|---|
| Rupturas del contorno dentro del pasillo | **2** (en x = −17,67 y x = +17,10) |
| Tramo más largo sin ninguna ruptura | **34,77 m** |
| Variación de la pared superior en 34,5 m | **0,06 m** (una celda) |
| Variación de la pared inferior en 34,5 m | **0,06 m** |
| Ancho | 1,98 – 2,04 m |

O sea: **un tubo liso de 2,0 m de ancho y casi 35 m sin un solo accidente.** Para comparar, el
modelo antiguo `primer_piso` —el que produjo todos los fracasos de mapeo— tenía un tramo ciego de
12,25 m. **El definitivo, bien medido, es casi tres veces peor.**

---

## 4. La corrida

Simulación en el portátil, sin ningún vehículo físico.

```
herramientas/lanzar_sim.sh mundo_definitivo_piso1.world x:=-17.0 y:=10.0 yaw:=0
ros2 bag record -o ~/tesis_evidencia/S23_info_piso1 /scan
herramientas/conducir_recta.py 0.33 0.0 30.0 1
```

Velocidad **0,33 m/s** y `angular.z` literalmente 0,0, que es la condición de uso obligatoria de la
herramienta: el índice **solo compara recorridos que se muevan igual**, y las dos referencias
—6,8 % y 13,8 %— se midieron así. Sensor simulado: 600 muestras, [−150°, +150°], alcance 10,0 m.

**Defecto de la corrida, y quién lo cometió.** El guion se lanzó con límites `0.0 / 30.0` cuando
`/odom` publica en coordenadas de mundo y el vehículo nacía en `x = −17,0`. El error es de quien
redactó los pasos, no de quien los ejecutó: el paso anterior preveía justamente los dos casos y se
eligió el equivocado. Con esos límites el objetivo quedó en x = 30, catorce metros más allá del
final del pasillo, y el vehículo **se estrelló contra la puerta del ETM10 y siguió empujando**.

**No se repitió la corrida, y la razón no es la prisa:** esta herramienta es geométrica y de un
solo barrido —no compara instantes, no usa el movimiento—, así que un tramo empujando contra una
pared no falsea el índice de los demás barridos. Lo que hace es sesgar la muestra, y eso se trata
mirando el perfil en el tiempo en vez del agregado. Hecho eso, **el choque resultó ser el mejor
control que esta medida ha tenido.**

---

## 5. El resultado

### Agregado de los 1.259 barridos

```
mediana      5,5 %
media       11,9 %
p10 / p90    5,0 / 27,4 %
```

La media al doble de la mediana y un p90 de 27,4 % avisan de que la muestra tiene dos poblaciones.
El perfil temporal las separa:

| Ventana | Mediana | Qué mira el sensor |
|---|---|---|
| t = 0 – 10 s | **27,2 %** | Arranque junto al vano de x = −17,67 y al hall de 6,30 m |
| t = 10 – 20 s | 12,0 % | Alejándose de esa estructura |
| **t = 20 – 90 s** | **4,8 – 5,3 %** | **El tubo liso — 70 s, unos 23 m** |
| t = 90 – 110 s | 7,0 → 13,2 % | Entra en alcance el fondo del pasillo |
| t = 110 – 120 s | 21,2 % | Aproximación a la puerta |
| t = 120 – 130 s | **48,8 %** | Detenido pegado a la puerta del ETM10 (ver §8.1) |

### La meseta, que es la cifra del pasillo

```
n = 700 barridos    mediana 5,1 %    p10 5,0 %    p90 5,6 %    max 8,3 %
```

Entre el p10 y el p90 hay **seis décimas de punto** a lo largo de 23 m. El pasillo no es
*mayoritariamente* pobre en información: es **uniformemente** pobre, que es exactamente lo que
predice un tubo cuyas paredes varían 0,06 m.

### Contra las referencias ya registradas

| Entorno | Índice | Desenlace conocido |
|---|---|---|
| Caja cerrada 7,70 × 2,70 m | **13,8 %** | Mapa **ACEPTADO** (98,1 % X, 0 obstáculos inventados) |
| Pasillo simulado 46,9 m | **6,8 %** | Mapa **RECHAZADO**, rf2o registró el 37,9 % |
| **Pasillo real, piso 1** | **5,1 %** | — |

**El pasillo real no queda cerca del caso que falló: queda por debajo de él.**

---

## 6. El control interno, que vale más que la comparación entre bags

La validación original de la herramienta apoyaba su conclusión en una separación de **2,03×** entre
dos bags distintos, y esa comparación siempre carga con la sospecha de que algo más cambió entre
ellos.

Aquí no. **Mismo bag, mismo sensor, misma velocidad, mismo movimiento recto, con 100 s de
diferencia:**

```
tubo liso ................  5,1 %
pegado a la puerta ......  48,8 %      ->  separación 9,6x
```

No hay diferencia de conducción, de configuración ni de sensor a la que atribuirlo. Es la
geometría del sitio y nada más. **El choque, que fue un error de ejecución, produjo el experimento
de control que la medida necesitaba.**

---

## 7. Un hallazgo que no se buscaba: los extremos sí informan

Los 27 % del arranque y los 21–48 % del final no son ruido: son el hall de 6,30 m y el fondo del
pasillo entrando en alcance. **Lo ciego son los ~23 m centrales, no el edificio entero.**

Esto no salva la travesía completa —una localización que se pierde en el medio ya no se recupera
sola—, pero sí dice dónde **sí** se puede medir sobre el vehículo real sin repetir el 7 de
septiembre: zonas con estructura a la vista, no el tramo central.

---

## 8. Dos matices hacia el carro físico, y no se compensan

| | Simulado | Real |
|---|---|---|
| Alcance | 10,0 m | **12 m** — los extremos entran antes: a favor |
| Sector ciego | 60° | **90°** ([`S22`](S22_mapeo_pasillo_fallido.md) §3) — en contra |

Ninguno de los dos toca los 23 m centrales, que es donde está el problema. La cifra del carro real
podría moverse algunas décimas; el veredicto no.

### 8.1 Dónde apunta ese sector ciego, que no es donde se creía

Al preparar la corrida de piso 2 el mismo día salió un dato que obliga a matizar la tabla de arriba
y la palabra *«de frente»* que antes tenía §5. El LiDAR **no mira hacia adelante**:

```
deepracer_description/models/xacro/urdf/deepracer_stereo_cameras_and_lidar_urdf.xacro:493
  <joint name="hokuyo_joint" type="fixed">
    <origin xyz="0.02913 0 0.16145" rpy="0 0 3.1416" />
```

Está montado girado **π respecto del chasis**. Como el campo es [−150°, +150°], la cuña ciega de 60°
queda centrada en los 180° del sensor, **o sea justo en la dirección de avance**. El vehículo es
ciego en un cono de 60° hacia donde va, y por eso los dos barridos finales de las corridas de piso 1
y piso 2 terminan iguales: `0°` despejado a 7,33 m y los rayos de `±150°` a 0,16 m, el mínimo del
sensor. Lo que golpearon quedó detrás del cero del LiDAR. Es el mismo `yaw π` y el mismo desfase
`x = 0,02913` que ya estaban calculados para el carro físico; lo nuevo es verlo en simulación.

**Esto no toca ninguna de las cifras de este documento.** El índice prueba `|sin(ang)| ≥ cos 45°`
sobre la recta ajustada a los vecinos, y un giro de π lleva `ang → ang + π`, que deja `|sin|`
idéntico: la medida es ciega al sentido, como dice su propio código —*«el signo no importa: informa
igual una pared de delante que una de detrás»*—. Lo que sí cambia es la redacción: el vehículo
quedó **pegado** a la puerta, no *de frente* a ella, y el control de §6 vale exactamente igual.

---

## 9. Qué decide esto

1. **R3 deja de tener una pregunta abierta.** *«Si el pasillo real aporta esa estructura sigue sin
   saberse»* — se sabe: **no la aporta**, 5,1 % contra el 6,8 % que ya fracasó.

2. **La pasada de localización a lo largo del pasillo no se hace.** Llevar el vehículo a recorrer
   esos 35 m con AMCL es repetir el 2026-09-07 con la predicción por escrito. Se ahorra la salida.

3. **Cargar el mapa sigue siendo correcto, y sigue sin bastar.** La sugerencia de dirección —cargar
   el mapa en vez de mapear— elimina la dependencia de SLAM en vivo, que es una ganancia real y ya
   está implementada ([`deepracer_localization_sim.launch.py`](../../Robot/aws-deepracer/deepracer_bringup/launch/deepracer_localization_sim.launch.py)).
   Pero AMCL necesita `odom → base_link`, el DeepRacer **no lleva encoders**, y su única odometría
   es rf2o, que es justo lo que este 5,1 % declara inviable aquí. **El mapa no sustituye al
   odómetro.**

4. **La otra sugerencia de dirección —asistir la odometría con las cámaras— pasa de idea razonable
   a única vía con respaldo medido.** Ya no hay que argumentarla en abstracto: hay una cifra, un
   control interno de 9,6× y una geometría medida que explica por qué.

---

## 10. Lo que esta medida NO dice

- **No dice que el edificio sea inmapeable.** Dice que *este* tramo, con *este* sensor y *esta*
  cadena, no da información de avance. Los extremos dan 27 % y 48 %.
- **No mide el error de AMCL.** M1 y M2 siguen sin medirse, y con esta cifra ya no tiene sentido
  medirlos en el tramo central.
- **No se ha corrido sobre el vehículo real.** Es simulación sobre geometría declarada fiel al
  edificio; §2 dice de quién es esa declaración y §8 qué cambiaría en el carro.
- **No cubre el piso 2.** Se midió al día siguiente y tiene registro propio:
  [`S23_informacion_avance_piso2.md`](S23_informacion_avance_piso2.md). Sale **5,9 %**, también por
  debajo del 6,8 % que fracasó. (El «tramo ciego de 4,63 m» que aquí se anotó primero salía del
  método de proyección de paredes que §3 retracta; medido sobre el contorno del espacio libre son
  **22,59 m**.)
- **El criterio de distancia que usa §8 quedó corregido después.** El piso 2 midió el decaimiento
  con la distancia y la influencia de una ruptura muere a los ~6 m, no a los 10 del alcance
  nominal; ver [`S23_informacion_avance_piso2.md`](S23_informacion_avance_piso2.md) §6.1. Eso no
  cambia el 5,1 % —el tubo de aquí no tiene nada dentro de 6 m ni de 10— pero sí endurece el
  veredicto.
