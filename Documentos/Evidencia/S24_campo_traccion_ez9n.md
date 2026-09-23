# S24 · la rampa de tracción sobre el `amss-ez9n`: trece corridas, y el control que las invalida como velocidad

**Fecha:** 2026-09-22 · **Vehículo:** `amss-ez9n` (192.168.0.102) · **Recta:** la marcada de 20,000 m
(marcas a 0 · 5 · 10 · 15 · 20 m) · **Guion:** [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10.3-ter ·
**Herramienta:** `sostener_traccion.py`, publicando a `/ctrl_pkg/servo_msg` con `--tope 1.0`.

---

## 0. Lo que salió, dicho de frente

La sesión se hizo entera —trece corridas, sin incidentes— y **la corrida de control refutó el
supuesto del método**. La consecuencia es que **de aquí no sale la curva `throttle → velocidad`**
que el §5 de [`S24_analisis_previo_RF11.md`](S24_analisis_previo_RF11.md) declaraba como *la medida
que decide*.

Lo que sí sale, y no es poco:

| Queda establecido | Fuerza |
|---|---|
| El `0,50` **mueve** este vehículo | Medido, dos corridas |
| De `0,60` en adelante el vehículo se desplaza **metros**, no decímetros | Medido, diez corridas |
| El `0,60 → menos de 0,25 m/s` del §4 de [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) **no se reproduce**, por un factor de tres como mínimo | Medido, y S23 §8 ya había avisado de por qué |
| A `throttle 1,00` el vehículo **seguía acelerando en el segundo 6** | Medido, corrida de control |
| A `throttle 1,00` este vehículo **no cabe** en la recta de 20 m con este método | Deducido de los puntos medidos, §3 |

Y lo que **no** queda establecido es la cifra que se iba a buscar: la velocidad estable de cada
escalón. Se explica en el §3 y se cuantifica lo que costaría en el §8.

---

## 1. Las trece distancias, como se anotaron

`d` es la distancia de la marca de salida al punto donde el vehículo quedó parado, medida con
flexómetro. **Incluye el arranque, el tramo de acelerador y la inercia**: la herramienta no frena,
al acabar el tramo publica ceros y el carro rueda hasta pararse solo.

| # | `--throttle` | `--marcha` | `d` anotada | `d` (m) |
|---|---|---|---|---|
| 1 | 0,50 | 2 | 37 in | **0,940** |
| 2 | 0,50 | 4 | 132 cm | **1,320** |
| 3 | 0,60 | 2 | 177 cm | **1,770** |
| 4 | 0,60 | 4 | 420 cm | **4,200** |
| 5 | 0,70 | 2 | 275 cm | **2,750** |
| 6 | 0,70 | 4 | 640 cm | **6,400** |
| 7 | 0,80 | 2 | 330 cm | **3,300** |
| 8 | 0,80 | 4 | 745 cm | **7,450** |
| 9 | 0,90 | 2 | 403 cm | **4,030** |
| 10 | 0,90 | 4 | 910 cm | **9,100** |
| 11 | 1,00 | 2 | 500 cm | **5,000** |
| 12 | 1,00 | 4 | 1080 cm | **10,800** |
| 13 | 1,00 | **6** | 1930 cm | **19,300** |

Dos notas del operador, las dos pertinentes:

- **La corrida 1 se midió en pulgadas** por descuido. 37 in × 25,4 mm = **939,8 mm**. La conversión
  no introduce error apreciable: la resolución de una cinta en pulgadas enteras es peor que la del
  flexómetro, ±½ in = ±1,3 cm, irrelevante frente a los 94 cm medidos.
- **El vehículo se desvía.** Es esperable en un Ackermann y no invalida la tanda, pero **sesga
  todas las distancias hacia abajo**: la cinta mide a lo largo de la recta y el carro recorre un
  arco. El sesgo crece con la distancia, así que **aplana** la curva. Todo lo que este documento
  concluye sobre que la curva es *más* inclinada de lo esperado queda reforzado, no debilitado, por
  esta desviación.

**Control de calidad de la tanda: la monotonía es perfecta.** Las seis distancias a `--marcha 2`
crecen con el acelerador (0,94 · 1,77 · 2,75 · 3,30 · 4,03 · 5,00) y las seis a `--marcha 4`
también (1,32 · 4,20 · 6,40 · 7,45 · 9,10 · 10,80), sin una sola inversión. Doce puntos ordenados
por casualidad tienen probabilidad 1/518 400. **La tanda es coherente consigo misma**; lo que falla
no es la toma de datos, es el supuesto del método.

---

## 2. La aritmética del método diferencial

El método está derivado en el §10.3-ter del guion. En corto: `d₄ = arranque + 2 s de crucero +
inercia` y `d₂ = arranque + 0 + inercia`, de modo que **si el vehículo alcanza su velocidad estable
antes del segundo 2**, el arranque y la inercia son los mismos en las dos corridas y se cancelan al
restar:

$$v = \frac{d_4 - d_2}{2}$$

| `throttle` | `d₂` (m) | `d₄` (m) | `d₄ − d₂` (m) | `(d₄ − d₂)/2` (m/s) |
|---|---|---|---|---|
| 0,50 | 0,940 | 1,320 | 0,380 | **0,190** |
| 0,60 | 1,770 | 4,200 | 2,430 | **1,215** |
| 0,70 | 2,750 | 6,400 | 3,650 | **1,825** |
| 0,80 | 3,300 | 7,450 | 4,150 | **2,075** |
| 0,90 | 4,030 | 9,100 | 5,070 | **2,535** |
| 1,00 | 5,000 | 10,800 | 5,800 | **2,900** |

**Estas seis cifras no son velocidades.** Lo dice el propio control de la tanda, que es de lo que
trata el §3. Se dejan escritas porque son el dato crudo del que se deduce todo lo demás, no porque
valgan como resultado.

---

## 3. La corrida 13 refuta el supuesto, y por eso estaba en la tabla

La corrida 13 existe para comprobar la **única** suposición del método: que la velocidad estable se
alcanza antes de los 2 s. Si es cierta, `(d₆ − d₄)/2` tiene que dar lo mismo que `(d₄ − d₂)/2`.

| Ventana | Cálculo | Resultado |
|---|---|---|
| \[2 s, 4 s] | (10,800 − 5,000)/2 | **2,900 m/s** |
| \[4 s, 6 s] | (19,300 − 10,800)/2 | **4,250 m/s** |

**No coinciden: la segunda es un 47 % mayor.** A `throttle 1,00` el vehículo no sólo no había
alcanzado su velocidad estable en el segundo 2 — tampoco la había alcanzado en el segundo 4. Los
tres puntos (5,00 · 10,80 · 19,30) tienen segunda diferencia **+2,70 m**, es decir, la curva `d(T)`
es **convexa**: el vehículo recorre cada bloque de dos segundos más deprisa que el anterior.

### 3.1 Y el error no tiene el signo que el guion había preinscrito

El guion escribió: *«hay que anotar que las demás filas quedan **subestimadas** —sirven como cota
inferior»*. **La conclusión es defendible, pero el razonamiento que la sostenía no.** Esto merece
quedar escrito porque es el mismo tipo de descuido que el método venía a corregir.

La cancelación de la inercia al restar sólo funciona si el vehículo suelta el acelerador a la misma
velocidad en las dos corridas. Si todavía está acelerando, **suelta más rápido en la corrida larga,
rueda más lejos, y la inercia no se cancela: aporta un término positivo** a la resta. Formalmente,
llamando `C(v)` a la distancia de inercia desde la velocidad `v`:

$$\frac{d_4 - d_2}{2} = \underbrace{\bar v_{[2,4]}}_{\le\, v_\infty} + \underbrace{\frac{C(v_4) - C(v_2)}{2}}_{\ge\, 0}$$

El primer término se queda corto y el segundo se pasa. **El signo del total no está determinado por
el argumento**, al contrario de lo que decía el guion. Que en la práctica el primero domine es una
cuestión de magnitudes, no de deducción: un ajuste de coherencia con un modelo de primer orden sitúa
la inercia en el orden de **1 m** y el hueco que falta hasta la velocidad estable en bastante más,
de modo que las seis cifras del §2 **probablemente** sean cotas inferiores. *Probablemente* no es
*medido*, y así queda dicho.

> Ese mismo ajuste deja un aviso adicional: **un modelo de primer orden no reproduce la convexidad
> observada.** Un vehículo que se acerca asintóticamente a su velocidad estable da una `d(T)`
> cóncava, no convexa. Lo observado apunta a que en los primeros segundos algo limita el
> aprovechamiento del acelerador —arranque suave del variador, patinaje de rueda a fondo sobre suelo
> liso— y que la tracción efectiva mejora después. **No está medido y no se afirma**; se anota
> porque cambia qué instrumento haría falta (§8).

### 3.2 A `throttle 1,00` este vehículo no cabe en la recta

La corrida 13 acabó a **19,30 m** de la salida, sobre una recta marcada de **20,000 m**: quedaron
**70 cm**. Para repetir la comprobación un escalón más arriba haría falta `--marcha 8`, y como la
curva medida es convexa, `d(8) ≥ d(6) + (d(6) − d(4)) = 27,80 m`. **Más de siete metros por encima
de la recta disponible.** El techo de este vehículo no es caracterizable aquí con este método.

> **La regla de parada del guion se saltó, y conviene decirlo.** La regla 2 del plan de parada dice:
> *«si una corrida acaba pasada la mitad de la recta disponible, no subas al escalón siguiente»*. La
> corrida 12 acabó a 10,80 m, pasada la mitad de 20 m. La 13 se hizo igual y terminó con 70 cm de
> margen contra la última marca. Salió bien; la regla seguía teniendo razón. **No se repite.**

---

## 4. Qué queda establecido, pese a todo

### 4.1 El `0,50` mueve este vehículo — pero apenas

Dos corridas, 0,94 m y 1,32 m. **Rompe inercia.** Y la diferencia entre las dos es de sólo 38 cm
frente a **dos segundos más** de acelerador: la lectura coherente no es *«avanza a 0,19 m/s»* sino
*«da un tirón y no lo sostiene»*. Dos segundos adicionales de motor que sólo compran 38 cm no
describen un vehículo en marcha.

Esto **contradice** el `0,50 → 0 arranques de 5` del §4 de S23, que se midió sobre el `amss-jgm9`.
El guion preinscribió esta salida: *«no es un contratiempo: es un hallazgo»*. La lectura conjunta de
los dos registros es que **el umbral de arranque está justo en 0,50 y los dos vehículos caen a lados
distintos de él** — que es exactamente lo que se espera en un umbral: es donde dos unidades
nominalmente iguales dejan de comportarse igual.

### 4.2 El `0,60 → menos de 0,25 m/s` de S23 no se reproduce, y por un margen que la inercia no explica

| | S23 §4 (`amss-jgm9`, 17-sep) | Hoy (`amss-ez9n`, 22-sep) |
|---|---|---|
| Camino de publicación | `/ctrl_pkg/servo_msg` | **el mismo** |
| Herramienta | `sostener_traccion.py` | **la misma** |
| `throttle 0,60`, 4 s | **menos de 1 m** | **4,20 m** |

Y no es cuestión de la inercia, que es el término que S23 no restaba: si la velocidad sostenida a
0,60 fuera de 0,25 m/s, los 2 s de acelerador de la corrida 3 darían **0,50 m**, y un vehículo que
va a 0,25 m/s no rueda un metro más por inercia — aun con una desaceleración tan baja como
0,5 m/s², la inercia desde 0,25 m/s son **6 cm**. Cota generosa: **0,56 m**. Se midieron **1,77 m**.
**Factor tres, con el supuesto más favorable posible a S23.**

**S23 escribió por adelantado por qué esto podía pasar**, y ahí está la reconciliación. Su §8 dice,
palabra por palabra:

> *«un carro cuya dirección no está centrada arrastra las ruedas, y cualquier distancia medida con
> él subestima la velocidad por una cantidad desconocida»*

El `amss-jgm9` de aquella tarde tenía la dirección sin centrar —su §5 entero trata de eso—, y su
calibración se rehízo esa misma noche. **La sesión de hoy se hizo sobre el vehículo que va recto,
elegido por esa razón.** «Una cantidad desconocida» es precisamente lo que hoy se cifra en un factor
de tres o más.

> **Y S23 no queda en falso: queda confirmado.** Es tentador leer esto como que aquel documento se
> equivocó, y no es lo que pasó. Su §9.3 escribió, sin que nadie se lo pidiera: *«la tabla que se
> publique hoy documenta el extremo inferior de un vehículo con la dirección sin calibrar, **no la
> escala del sistema**»*. Lo de hoy **cobra esa reserva**: la cantidad desconocida era un factor de
> tres. Lo que sí decae es el uso que se le dio después — el criterio de cierre de su §10 pedía *«al
> menos un punto por debajo de 0,25 m/s»* y lo dio por medido, y ese punto describe aquel vehículo
> en aquel estado, no el techo de la plataforma. **RF-14 no cambia de color por esto**:
> [`REQUISITOS.md`](../REQUISITOS.md):117 lo tiene en 🟡 con la escala por calibrar, que es
> exactamente donde sigue.
>
> **Lo que sí se refuerza es el diagnóstico de fondo del §9.2 de S23**, y conviene verlo porque va
> en contra de la intuición. Aquel documento concluyó que *«subir `MAX_SPEED_PCT` no cierra RF-14 …
> el problema de fondo es que cuatro escalones no cubren el rango que Nav2 usa»*. Si este vehículo
> recorre 19,3 m en 6 s de acelerador, **el rango que los cuatro escalones tienen que repartir es
> aún más ancho de lo que se creía**, y por tanto el problema de resolución es **peor**, no mejor.
> El hallazgo de hoy, que a primera vista alivia —el carro corre más de lo que pensábamos—, en
> realidad agrava el defecto que de verdad bloquea RF-14.

### 4.3 La escalera de tracción es monótona y utilizable de 0,60 arriba

Las doce distancias ordenan los seis escalones sin una sola inversión (§1). Para la pregunta que
RF-11 hace de verdad —*¿se desplaza el vehículo mandado por `/<ns>/cmd_vel`?*— eso basta: **de 0,60
en adelante el vehículo recorre metros en cuatro segundos, de forma repetible y creciente.**

---

## 5. Los veredictos preinscritos: cuál se dispara

Del §6 de [`S24_analisis_previo_RF11.md`](S24_analisis_previo_RF11.md), escritos antes de correr.

| Preinscrito | ¿Se dispara? | Por qué |
|---|---|---|
| *A 0,80 el carro se desplaza ≥ 1 m en 4 s de forma repetible* → el escalón bajo de `(1,0 · 1,00)` es utilizable | **Sí** | 7,45 m en la corrida 8, y 3,30 m con sólo 2 s en la 7. Muy por encima del metro |
| *A 0,80 no arranca de forma fiable* → la tracción queda binaria | No | Refutado por lo anterior |
| *La velocidad a 1,00 supera 0,6 m/s* → `MAX_SPEED = 1,0` es defendible | **Parcialmente, y no como estaba redactado** | Se supera 0,6 m/s con enorme margen, pero **no hay una velocidad medida a 1,00** que poner al lado, que es lo que el veredicto exigía (*«se fija con la medida al lado»*). Ver §6 |
| *La velocidad a 1,00 no llega a 0,3 m/s* → bajar `desired_linear_vel` | No | Refutado sin ambigüedad: 10,80 m en 4 s |
| *Los dos carros dan curvas distintas en más de un 25 %* → cada vehículo lleva sus constantes | **No evaluable, y con un indicio en contra de la premisa** | Del `amss-jgm9` sólo existen los dos puntos de S23, tomados con la dirección descentrada. No hay dos curvas que comparar. Lo que sí hay es que **el 0,50 arranca en uno y no en el otro** |

**El veredicto que importa para RF-11 se disparó, y es favorable.** El escalón bajo de la
configuración `(MAX_SPEED = 1,0 · MAX_SPEED_PCT = 1,00)` vale **0,800**, que está muy por encima del
umbral de arranque de este vehículo.

---

## 6. Lo que este documento **no** establece

- **Ninguna velocidad.** Ni una. Las seis cifras del §2 son diferencias de distancia divididas por
  dos, con el supuesto que las convertía en velocidad refutado por la corrida 13.
- **No fija `MAX_SPEED`.** El veredicto preinscrito para `MAX_SPEED = 1,0` pedía *«se fija con la
  medida al lado»*, y la medida no está. Además, lo poco que se puede decir apunta en contra de
  bajarlo a 1,0: un vehículo que recorre 19,3 m en 6 s de acelerador **no** tiene un techo de 1 m/s,
  y `MAX_SPEED` es precisamente el techo que la escalera supone. Si algo insinúan estos datos es que
  **el 4,0 heredado de AWS no era absurdo**, lo contrario de lo que el §4 de
  [`S24_analisis_previo_RF11.md`](S24_analisis_previo_RF11.md) daba por probable. **Insinuar no es
  medir**, y la decisión sigue siendo de los autores, no de este documento.
- **No mide el 0,4247**, que es el escalón que la cadena emite hoy para `desired_linear_vel = 0,5`.
  Está **por debajo** del 0,50 que aquí apenas da un tirón. El §2.3 de
  [`S24_analisis_previo_RF11.md`](S24_analisis_previo_RF11.md) concluía *«no se mueve»* apoyado en
  el `0 de 5` del otro vehículo; ese apoyo queda **debilitado, no refutado** — el 0,50 de este carro
  tampoco sostiene la marcha. La conclusión del §2.3 sigue siendo la apuesta razonable y **sigue sin
  estar medida en este vehículo**.
- **No dice nada del `amss-jgm9`.** Todo lo de aquí es de un solo vehículo, y ahora con la dirección
  calibrada — condición que el `amss-jgm9` no cumplía cuando se le midió.
- **No se publicó nada en `/cmd_vel`.** La tanda entera fue directa a `/ctrl_pkg/servo_msg`, sin
  pasar por el reescalado. RF-11 sigue 🟡.

---

## 7. Qué falta, y cuánto cuesta

La sesión falló en un punto concreto y la reparación es barata, salvo para el escalón más alto.

| Escalón | `d(6)` esperada | ¿Cabe en 20 m? | Qué haría falta |
|---|---|---|---|
| 0,60 | ≈ 6,6 m | **sí, holgado** | Una corrida `--marcha 6` |
| 0,70 | ≈ 10 m | **sí** | Una corrida `--marcha 6` |
| 0,80 | ≈ 11,6 m | **sí** | Una corrida `--marcha 6` |
| 0,90 | ≈ 14 m | sí, pero pasada la mitad | Sólo si sobra sesión, y con la regla de parada en la mano |
| 1,00 | 19,3 m **medida** | **no**, haría falta `--marcha 8` ≳ 27,8 m | **Otro instrumento** |

**Tres corridas de trece segundos** deciden si la mitad baja de la curva es válida: si a 0,60, 0,70
y 0,80 resulta `(d₆ − d₄)/2 ≈ (d₄ − d₂)/2`, esas filas del §2 **sí** son velocidades y el documento
entrega media curva medida. Es plausible que así sea: cuanto más bajo el escalón, más cerca está la
velocidad estable y antes se alcanza. **Plausible no es medido.**

Para el escalón de 1,00 el flexómetro se acabó, y el instrumento que corresponde es el **tiempo de
paso entre dos marcas** —por ejemplo la de 5 m y la de 15 m—, que es inmune tanto al transitorio
como a la inercia porque mide el vehículo en el tramo central, ya lanzado. Eso exige un cronómetro
fiable a la décima, es decir vídeo, no pulgar. **No se improvisa**, y para la decisión que RF-11
tiene pendiente tampoco hace falta: lo que RF-11 pregunta es si los escalones superan el umbral de
arranque, y eso ya está contestado.

---

## 8. Trazabilidad

| Afirmación | Dónde comprobarla |
|---|---|
| Las trece distancias | §1 de este documento; anotadas en campo por el operador, 2026-09-22 |
| El método diferencial y su único supuesto | [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10.3-ter, «Al volver: la cuenta» |
| El control no pasa: 2,900 frente a 4,250 m/s | §3, aritmética sobre las corridas 11, 12 y 13 |
| La herramienta no frena | [`sostener_traccion.py`](../../herramientas/sostener_traccion.py):`parar()`, publica diez ceros |
| Las dos sesiones publican por el mismo camino | `TOPICO_SERVO = "/ctrl_pkg/servo_msg"` en [`sostener_traccion.py`](../../herramientas/sostener_traccion.py):90, y [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §4 |
| S23 avisó de que sus distancias subestiman | [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §8, escrito el 17-sep |
| La dirección del `amss-jgm9` no estaba centrada | [`S23_campo_traccion_RF14.md`](S23_campo_traccion_RF14.md) §5 |
| El `amss-ez9n` es el que va recto | [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md) §10.3-ter; calibración leída del vehículo el 2026-09-22 |
| Los veredictos eran previos | [`S24_analisis_previo_RF11.md`](S24_analisis_previo_RF11.md) §6 |
| La recta mide 20,000 m | [`HOJA_CAMPO_G2.md`](../HOJA_CAMPO_G2.md); medida el 2026-09-07 con flexómetro de instrumentación |
