# El piso 2 tampoco: 5,9 % medido, y la predicción que lo esperaba mejor falló

**Fecha:** 2026-09-18 · **Semana:** S23 · **Objetivo:** OE2 (localización sobre el vehículo) ·
**Riesgo:** R3 · **Bag:** `~/tesis_evidencia/S23_info_piso2b` (1.418 barridos + 2.115 de `/odom`,
141,9 s)

Este registro continúa [`S23_informacion_avance_piso1.md`](S23_informacion_avance_piso1.md), que
cerró la pregunta de R3 sobre el primer piso con un 5,1 % y dejó anotado que el segundo era «la
comparación natural, dentro del mismo edificio y con la misma cadena». Se corrió. **Sale 5,9 %:
mejor que piso 1 por ocho décimas, y aun así por debajo del 6,8 % del pasillo cuyo mapa se
rechazó.**

Lo que este documento aporta además del número es que **la predicción se falsificó**, y de los dos
errores que la produjeron sale una corrección al modelo geométrico que el proyecto venía usando.

---

## 1. Procedencia del modelo

`mundo_definitivo_piso2` se midió en sitio y se construyó a imagen y semejanza del segundo piso
real de la USTA, igual que el de piso 1 (procedencia declarada por Santiago Hernández, autor del
modelado, 2026-09-18). El mapa que se carga
(`deepracer_bringup/maps/mundo_definitivo_piso2.yaml`) lo dibujó
[`generar_mapa_desde_mundo.py`](../../herramientas/generar_mapa_desde_mundo.py) de esa geometría
—el método de R10, que pasó `verificar_mapa.py` con 99,7 %—, así que no arrastra error de
construcción.

---

## 2. La geometría, medida sobre el contorno del espacio libre

Se usó desde el principio el método bueno —el contorno de lo que el LiDAR sí ve—, no la
proyección de todas las paredes que en piso 1 dio un resultado falso.

| Magnitud | Piso 2 | Piso 1 |
|---|---|---|
| Rupturas del contorno dentro del pasillo | **4** (x = −14,22 · 8,37 · 18,63 · 21,54) | 2 |
| Tramo más largo sin ruptura | **22,59 m** | 34,77 m |
| Ancho del tubo | 2,34 m | 1,98 – 2,04 m |

Sobre el papel piso 2 está mejor condicionado: la mitad de tramo ciego y el doble de accidentes.
De ahí salió la predicción, y de ahí salió el error.

---

## 3. La predicción, registrada antes de correr

> Con alcance de 10 m, dentro del tramo de 22,59 m el vehículo solo queda sin ninguna ruptura en
> alcance entre x ≈ −4,2 y x ≈ −1,6. Mediana global **entre 8 % y 14 %**; el perfil mostrará **un
> hundimiento en el centro y recuperación a los dos lados**, con el fondo entre 4,5 y 7 %. Si sale
> plano, o si el fondo cae por debajo del 5,1 % de piso 1, el modelo de las rupturas es falso.

**Salió plano. El modelo de las rupturas era falso.**

---

## 4. Dos corridas, y qué enseñó la que se perdió

### 4.1 La primera se encajó contra un muro

`~/tesis_evidencia/S23_info_piso2` (865 barridos, 86,5 s). Arranque en `x = −16,0`, que **está en
el hall**, donde la franja libre mide 10,08 m. El perfil del bag lo cuenta solo:

| t | rango a 0° | ±90° | mínimo |
|---|---|---|---|
| 0 s | 1,39 m | 6,65 / 3,48 | 1,37 m |
| 15 – 30 s | 3,5 → 7,35 m | 1,2 / 1,1 | 1,03 m |
| 30 – 85 s | **7,33 m congelado** | 1,35→2,10 / 1,05→**0,31** | 0,15 m |

Cincuenta y cinco segundos con el rango frontal quieto en dos centímetros mientras el lateral se
come 74 cm: no avanzó, se escoró. Entró al pasillo de 2,34 m desde espacio abierto con el error de
rumbo del arranque, y `conducir_recta.py` fija `angular.z = 0,0` pero **no cierra lazo de rumbo**,
así que nada lo corrigió. Se encajó en x ≈ −10. El mundo no tiene parte: sus 52 muros miden 2,5 m
de alto y ninguno está cerca de ahí.

**El error es de quien diseñó el ensayo: hacerlo nacer en el hall en vez de dentro del pasillo.**
En piso 1 no ocurrió porque allí nació dentro del tubo, ya alineado.

### 4.2 Lo que esa corrida perdida sí dejó: dónde mira el LiDAR

Los barridos finales de las corridas de piso 1 y de piso 2 son idénticos en su firma: **`0°`
despejado a 7,33 m y los rayos de `±150°` a 0,16 m**, el mínimo del sensor. Lo que golpearon quedó
detrás del cero del LiDAR. La causa está en el URDF:

```
deepracer_description/models/xacro/urdf/deepracer_stereo_cameras_and_lidar_urdf.xacro:493
  <joint name="hokuyo_joint" type="fixed">
    <origin xyz="0.02913 0 0.16145" rpy="0 0 3.1416" />
```

El LiDAR está montado girado **π respecto del chasis**. Con campo [−150°, +150°], la cuña ciega de
60° queda centrada en los 180° del sensor, **que es la dirección de avance**: el vehículo es ciego
en un cono de 60° hacia donde va. Es el mismo `yaw π` y el mismo `x = 0,02913` que ya estaban
calculados para el carro físico; lo nuevo es verlo en simulación. Consecuencias anotadas en
[`S23_informacion_avance_piso1.md`](S23_informacion_avance_piso1.md) §8.1: **no altera ninguna
cifra**, porque el índice prueba `|sin(ang)| ≥ cos 45°` y un giro de π deja `|sin|` idéntico.

### 4.3 La segunda corrida, dentro del pasillo

```
herramientas/lanzar_sim.sh mundo_definitivo_piso2.world x:=-12.0 y:=-4.50 yaw:=0
ros2 bag record -o ~/tesis_evidencia/S23_info_piso2b /scan /odom
herramientas/conducir_recta.py 0.33 -12.0 7.0 1
```

Tramo `x ∈ [−12, 7]`, entero dentro de los 22,59 m sin rupturas, con 1,14 m de holgura a cada lado.
Ida y vuelta completas, 38 m. Velocidad **0,33 m/s** y `angular.z` literalmente 0,0, que es la
condición de uso de la herramienta: solo compara recorridos que se muevan igual, y las referencias
de 6,8 % y 13,8 % se midieron así. Sensor: 600 muestras, [−150°, +150°], alcance 10,0 m.

**Se grabó `/odom`**, que es lo que faltó en piso 1: permite poner el índice contra la posición en
vez de contra el tiempo. El recorrido registrado va de x = −12,06 a x = 7,03, con y entre −5,05 y
−3,90 —se escoró 60 cm en 19 m, dentro de la holgura—.

---

## 5. El resultado

### Agregado de los 1.418 barridos

```
mediana      6,3 %
media        9,5 %
p10 / p90    5,8 / 19,2 %
```

### El perfil contra la posición, que es lo que decide

| x | mediana | distancia al hall (x = −14,22) |
|---|---|---|
| −12 | **17,5 %** | 2,2 – 3,2 m |
| −11 | 11,5 % | 3,2 – 4,2 m |
| −10 | 9,2 % | 4,2 – 5,2 m |
| −9 | 7,5 % | 5,2 – 6,2 m |
| **−8 … +6** | **5,9 %** | más de 6,2 m |

```
MESETA  x = [-8, +6]   n = 849   mediana 5,9 %   p10 5,7 %   p90 6,6 %   max 9,7 %
```

**Nueve décimas de punto a lo largo de catorce metros.** Igual que piso 1, el pasillo no es
mayoritariamente pobre en información: es uniformemente pobre.

### Contra las referencias ya registradas

| Entorno | Índice | Desenlace conocido |
|---|---|---|
| Caja cerrada 7,70 × 2,70 m | 13,8 % | Mapa **ACEPTADO** (98,1 % X, 0 obstáculos inventados) |
| Pasillo simulado 46,9 m | 6,8 % | Mapa **RECHAZADO**, rf2o registró el 37,9 % |
| Pasillo real, piso 1 | 5,1 % | — |
| **Pasillo real, piso 2** | **5,9 %** | — |

---

## 6. Por qué falló la predicción: dos errores, los dos corregibles

### 6.1 Una ruptura informa hasta ~6 m, no hasta los 10 m del alcance

La predicción supuso que mientras una ruptura estuviera dentro del alcance del LiDAR el índice
subiría. El decaimiento de la tabla de §5 lo desmiente: el efecto del hall muere entre los 5 y los
6 m, y de ahí en adelante el índice es indistinguible del fondo.

Ese 6 m **no es un número nuevo**. Es el mismo umbral que
[`S22_mapeo_pasillo_fallido.md`](S22_mapeo_pasillo_fallido.md) dejó registrado el 2026-09-08 con
otro instrumento y otra magnitud: estructura a menos de 6 m → razón de registro 0,998; entre 6 y
9 m → 0,255. Dos medidas independientes que caen en el mismo sitio.

**Consecuencia práctica:** la condición del §8.6 no es «estructura dentro de los 12 m del LiDAR»
sino **dentro de unos 6 m**, que es la mitad. Todo tramo evaluado con el criterio antiguo queda
sobreestimado.

### 6.2 No todas las rupturas valen lo mismo

Las dos que rodean el tramo medido difieren en más de un orden de magnitud:

| ruptura | el pasillo pasa de | a | escalón |
|---|---|---|---|
| x = −14,22 | 2,34 m | **10,08 m** (el hall) | 7,74 m |
| x = +8,37 | 2,34 m | 1,74 m | **0,60 m** |

El vehículo llegó a **1,34 m** de la segunda y el índice apenas subió a 7,1 %. Un escalón de 60 cm
no aporta superficie perpendicular suficiente para mover un índice sobre 600 rayos.

Contar rupturas sin pesarlas es el mismo error de clase que el de los «6,13 m» de piso 1
([`S23_informacion_avance_piso1.md`](S23_informacion_avance_piso1.md) §3): tratar accidentes
geométricos como eventos binarios. **Un recuento de rupturas no caracteriza un pasillo; hay que
mirar el tamaño del escalón y la distancia.**

---

## 7. Qué decide esto

1. **El edificio no tiene un piso bueno.** 5,1 % en piso 1 y 5,9 % en piso 2, los dos por debajo
   del 6,8 % cuyo mapa se rechazó y muy lejos del 13,8 % del único mapa aceptado. La comparación
   natural se hizo y no rescata nada.

2. **La ventaja geométrica de piso 2 no se traduce en información.** Tiene la mitad de tramo ciego
   (22,59 m contra 34,77 m) y el doble de rupturas, y el índice sube ocho décimas. La razón está en
   §6: tres de sus cuatro rupturas son escalones pequeños, y el alcance útil es la mitad del
   nominal.

3. **Se confirma la decisión de piso 1: la pasada de localización a lo largo del pasillo no se
   hace,** en ninguno de los dos pisos.

4. **La asistencia de odometría con las cámaras queda como única vía con respaldo medido**, ahora
   con dos pisos en vez de uno.

5. **Queda una corrección que arrastra hacia atrás:** el criterio de 12 m del §8.6 debe leerse como
   ~6 m. Cualquier tramo que se haya declarado viable con el criterio antiguo hay que volver a
   mirarlo.

---

## 8. Lo que esta medida NO dice

- **No dice que el edificio sea inmapeable.** El arranque junto al hall da 17,5 %, por encima del
  6,8 % que falló. Lo ciego son los tramos rectos, no el edificio.
- **No cubre el pasillo entero de piso 2.** Se midió `x ∈ [−12, 7]`, 19 m de los 40,50 m de recta
  libre. El resto tiene las rupturas de x = 18,63 y 21,54, que son escalones —no se midieron y por
  §6.2 no hay razón para esperar que informen.
- **No mide el error de AMCL.** M1 y M2 siguen sin medirse.
- **No se ha corrido sobre el vehículo real.** Es simulación sobre geometría declarada fiel al
  edificio; §1 dice de quién es esa declaración.
