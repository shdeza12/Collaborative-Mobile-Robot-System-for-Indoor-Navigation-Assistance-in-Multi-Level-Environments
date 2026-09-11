# R12 — La misión de 85 cúspides, explicada

**Fecha:** 2026-09-11 (S22) · **Bag:** `~/tesis_evidencia/S21_OE4_09` · **Registro:**
[`registros/S21_OE4_09.json`](registros/S21_OE4_09.json) · **Commit de partida:** `929e1e0`

La campaña de OE4 del 2026-09-05 dejó una anomalía anotada y deliberadamente sin tocar: una misión
del estrato B12 con **85 cúspides** contra una mediana de 7 y un máximo de 13 en las otras 29. El
§6.3 del protocolo prohíbe investigar dentro de la campaña, así que se anotó con el bag conservado.
La campaña está cerrada y analizada desde el 05-sep; explicarla ahora ya no es tocar datos después
de verlos, es rendir cuentas de una anomalía declarada.

**Conclusión:** no es un fallo de la coordinación ni del planificador, y la misión **fue un éxito**
(`exito: true`, error de llegada 0,0554 m). Es una interacción entre tres cosas que sólo coinciden
al final de un tramo corto: una cúspide que el planificador coloca a milímetros del vehículo,
`allow_reversing: true`, y la guarda `carrot_dist2 > 0.001` del controlador, que a menos de
**3,16 cm** del punto de persecución anula la dirección. El vehículo quedó **22 s** dando marcha
adelante y atrás con las ruedas rectas, a 0,19 m de una meta con tolerancia de 0,15 m.

---

## 1. Dónde están las 85

`num_cuspides` suma **todos** los tópicos `*/cmd_vel` del bag, así que en condición B el número es
robot1 + robot2. El reparto:

| | cúspides | cuándo |
|---|---|---|
| robot1 | 8 | una ráfaga de 3,5 s, entre 122,7 y 126,2 s, dentro del tramo 1 |
| robot2 | **77** | todas entre 159,3 y 191,7 s |
| | **85** | |

Y dentro de robot2, por ventanas de 4 s de simulación:

```
 ventana   n   wz==0   cuspides   |vx| medio
 159-163   80      2       5        0.287     <- se acerca a la escalera, normal
 163-167   80      4       1        0.136
 167-171   80     13       7        0.101
 171-175   80     78      15        0.158   \
 175-179   79     74      14        0.152    |  59 cuspides en 16 s
 179-183   80     80      15        0.160    |  308 de 320 muestras con wz == 0
 183-187   80     76      15        0.156   /
 187-191   64      1       4        0.078     <- vuelve a haber direccion
 191-195   80      1       1        0.419     <- meta nueva
 195-223  ...      0       0        0.500     <- 31 s hasta el destino, CERO cuspides
```

**59 de las 77 cúspides de robot2 caben en 16 segundos**, y en esos 16 segundos el 96 % de los
comandos llevan `angular.z` exactamente cero. Los 31 s siguientes, con la misma pila, el mismo
vehículo y el mismo controlador, no producen ni una.

## 2. Qué estaba haciendo el vehículo

Las marcas del coordinador en `/coordinacion/estado_mision`:

| t (sim) | etapa |
|---|---|
| 150,0 | 1 — TRAMO_1 |
| **159,0** | **2 — TRANSFERENCIA** |
| **191,7** | 3 — TRAMO_2 |

La etapa 2 duró **32,7 s**. En la transferencia el segundo robot conduce hasta su propia escalera
mientras el usuario sube, tal como está descrito en la §5 de
[`S22_RF28_confirmacion.md`](S22_RF28_confirmacion.md). El destino de esa etapa se lee directamente
del último punto de cada plan: **`(−21,479, −9,027)`**, que es `piso2_escalera`
(`puntos_interes.yaml:438`, `pose: {x: -21.50, y: -9.03}`). A partir de 191,7 el último punto pasa a
`(−7,500, −4,947)` = `piso2_aula_302`, el destino real de la misión.

Distancia de robot2 a `piso2_escalera`, según `/robot2/amcl_pose`:

| t | pose | distancia |
|---|---|---|
| 159,2 | (−21,944, −8,323) | 0,835 m |
| 163,1 | (−21,493, −8,685) | 0,345 m |
| **164,9** | (−21,353, −8,933) | **0,176 m** ← máximo acercamiento |
| 167,3 | (−21,304, −9,005) | 0,198 m |
| 169,3 | (−21,296, −9,017) | 0,205 m |
| *(18 s sin una sola publicación de AMCL)* | | |
| 187,4 | (−21,318, −8,993) | 0,185 m |
| 191,5 | (−21,354, −8,951) | 0,166 m |

`xy_goal_tolerance` vale **0,15 m**. El vehículo **nunca entró**, y se quedó rondando entre 0,166 y
0,205 m durante 27 s. El hueco de 18 s sin `amcl_pose` no es una pérdida de datos: AMCL publica
cuando el movimiento supera sus umbrales, y aquí no los superó.

## 3. El mecanismo, leído en el código que se ejecutó

El controlador es `RegulatedPurePursuitController`, versión instalada **1.1.20**
(`/opt/ros/humble/share/nav2_regulated_pure_pursuit_controller/package.xml`). Lo que sigue no es una
reconstrucción de memoria: es el fuente de esa etiqueta exacta.

### 3.1 El plan trae una cúspide, y a 6,5 mm del vehículo

De 170,3 a 185,7 el planificador devuelve **el mismo plan de 4 poses, idéntico segundo a segundo**:

```
   0  ( -21.2995,  -9.0269)  yaw = -30.0
   1  ( -21.2992,  -9.0334)  yaw = -15.0     <- 6,5 mm por debajo de la 0
   2  ( -21.3889,  -9.0212)  yaw =   0.0     <- 90,5 mm al oeste de la 1
   3  ( -21.4795,  -9.0269)  yaw =   0.0
```

`SmacPlannerHybrid` planifica en SE(2) con primitivas Reeds-Shepp, así que una cúspide en el plan es
legítima: es «retrocede un pelo y luego sal hacia el oeste». El vector 0→1 y el vector 1→2 forman un
producto escalar **−1,035 × 10⁻⁴ < 0**. Eso es exactamente lo que busca `findVelocitySignChange`
(`regulated_pure_pursuit_controller.cpp:767`).

Se replicó esa función sobre **los 63 planes** de robot2 del bag: **todos** los de la ventana
159,0–191,4 tienen cúspide, y **ninguno** de los 32 planes posteriores a 191,7 la tiene. La
correlación con las cúspides ejecutadas es total.

### 3.2 La cúspide encoge la distancia de persecución

```cpp
// linea 303
if (allow_reversing_) {
  double dist_to_cusp = findVelocitySignChange(transformed_plan);
  if (dist_to_cusp < lookahead_dist) {
    lookahead_dist = dist_to_cusp;          // 0.600 -> 0.0165
  }
}
```

Este bloque **sólo existe cuando `allow_reversing` es true**, que es como está el fichero
(`nav2_params_nav_amcl_sim_demo.yaml:149`) y como tiene que estar: con `use_rotate_to_heading: false`
—obligado por la cinemática Ackermann— es la única forma de que el vehículo ejecute las marchas atrás
que el planificador sí sabe trazar.

Con la pose de AMCL de 169,3 s, las cuatro poses del plan quedan a **10,3 · 16,5 · 93,4 · 184,2 mm**
del vehículo. La cúspide es la pose 1, a **16,5 mm**, así que `lookahead_dist` pasa de 0,600 m a
**0,0165 m**.

### 3.3 A esa distancia el controlador apaga la dirección

```cpp
// lineas 321-334
const double carrot_dist2 = carrot.x*carrot.x + carrot.y*carrot.y;
double curvature = 0.0;
if (carrot_dist2 > 0.001) {                 // 0.001 m2  =  3,16 cm
  curvature = 2.0 * carrot.y / carrot_dist2;
}
double sign = 1.0;
if (allow_reversing_) {
  sign = carrot.x >= 0.0 ? 1.0 : -1.0;
}
...
angular_vel = linear_vel * curvature;       // linea 353
```

`getLookAheadPoint(0,0165)` devuelve la primera pose a esa distancia o más: **la pose 1, a 16,5 mm**.
Entonces `carrot_dist2 = 2,71 × 10⁻⁴`, por debajo del umbral `0.001`, y **`curvature` se queda en
`0.0` exacto**. La guarda existe para no dividir por casi cero; el efecto lateral es que
«persigue un punto a 1,6 cm» se convierte en «no gires nada».

De ahí sale la huella que se ve en el bag y que no admite otra lectura: `angular.z` no es pequeño,
es **exactamente cero, y con el signo de `linear.x`** —porque `linear_vel × (+0.0)` conserva el signo
del cero—:

```
   175.000  vx= -0.167322  wz= -0.000000000
   175.100  vx= +0.158700  wz= +0.000000000
   175.300  vx= -0.164996  wz= -0.000000000
   175.600  vx= -0.161246  wz= -0.000000000
```

Y el sentido de la marcha lo decide `sign = carrot.x >= 0`: **el signo de la coordenada x de un punto
que está a 1,6 cm del vehículo**. Basta con que el carro avance dos centímetros para que ese punto le
quede detrás y el comando se invierta; al retroceder, vuelve a quedarle delante. Ciclo límite a
~2,5 Hz.

### 3.4 Hasta la magnitud cuadra

`applyApproachVelocityScaling` (línea 618) se activa porque el plan entero mide 0,188 m < 0,6 m, y
escala por la distancia a la **última** pose:

```
|v| = desired_linear_vel × dist_ultima_pose / approach_velocity_scaling_dist
    = 0,5 × 0,184 / 0,6
    = 0,153 m/s
```

Medido en el bag: **0,146 a 0,173 m/s**. La dirección la da la cúspide a 1,6 cm; la magnitud, la meta
a 18 cm. Las dos predicciones salen del mismo código y las dos coinciden.

### 3.5 Por qué no podía salir solo

Los tres ingredientes se realimentan: sin dirección no puede acercarse a la meta; a 0,19 m de la meta
el plan sigue midiendo 0,19 m; un plan de 0,19 m obliga al planificador a meter la cúspide en las
primeras celdas; y la cúspide a milímetros vuelve a anular la dirección. El `SimpleProgressChecker`
(0,5 m en 10 s) sí aborta el `FollowPath`, pero el árbol
[`ackermann_navigate_to_pose.xml`](../../Robot/aws-deepracer/deepracer_bringup/behavior_trees/ackermann_navigate_to_pose.xml)
reintenta limpiando el costmap y el ciclo se reanuda idéntico. Salió a los 22 s porque el plan cambió
—en 186,8 la cúspide se aleja a 19,9 mm y en 187,8 a 90,9 mm—, con la dirección viva el carro
maniobró los últimos 4 cm, y a 191,7 el coordinador dio la etapa por cerrada.

## 4. La prueba que discrimina: robot1, en el mismo bag

Las 8 cúspides de robot1 no son ruido, son el **control** del experimento. Ocurren entre 122,7 y
126,2 s, justo mientras sus planes llevan cúspide — y la llevan **a 91,4 mm**, no a 6,5:

| | cúspide del plan | `lookahead_dist` | `carrot_dist2` | ¿supera 0,001? | resultado |
|---|---|---|---|---|---|
| robot1 | 91,4 mm | 0,091 m | 8,4 × 10⁻³ | **sí** | curvatura ≠ 0, dirección viva, **1 de 191** muestras con `wz` cero, maniobra resuelta en 3,5 s y 8 cúspides |
| robot2 | 6,5 mm | 0,0165 m | 2,7 × 10⁻⁴ | **no** | curvatura = 0 exacta, dirección muerta, **308 de 320** muestras con `wz` cero, 59 cúspides en 16 s |

Mismo bag, misma versión del controlador, misma configuración, mismo tipo de vehículo. Lo único que
cambia es **si la cúspide cae dentro o fuera de los 3,16 cm**. Eso convierte la explicación en algo
falsable: con la cúspide lejos, RPP hace lo que debe —ejecuta la marcha atrás planificada y sigue—;
con la cúspide dentro de la guarda, se queda encerrado.

## 5. Qué dice esto de la campaña

Recuento de `descriptivas.num_cuspides` sobre las 30 misiones de OE4:

| condición | n | mediana | máximo | valores |
|---|---|---|---|---|
| A (un solo piso, sin transferencia) | 15 | **0** | 6 | 0×8, 4×3, 6×4 |
| B (dos pisos, con transferencia) | 16 | **8** | **85** | 5×4, 7×4, 9×5, 13×2, 85 |

El patrón es coherente con el mecanismo y no con un fallo esporádico: la condición A, que no tiene
etapa de transferencia, tiene mediana **cero**; la condición B, que sí la tiene, no baja de 5. La
transferencia es un tramo corto que termina junto a la escalera, que es justo la situación —plan de
pocos decímetros— en la que el planificador se ve obligado a colocar la cúspide en las primeras
celdas. Las tres corridas de RF-28 (31, 24 y 21 cúspides), todas con transferencia, encajan en el
mismo sitio.

Lo que **no** cambia:

- **La misión 09 fue un éxito.** Llegó a `piso2_aula_302` con 0,0554 m de error, dentro del criterio
  de 0,25 m, y sus tres condiciones de éxito son verdaderas. El coste de la anomalía son 22 s de
  espera del usuario, no un fallo.
- **La tasa de éxito de OE4 no se toca.** Ninguna de las cuatro misiones fallidas es de este modo:
  las cuatro fallaron por **quedarse cortas** —11 a 0,295 m, 24 a 0,284, 27 a 0,311, 28 a 0,347,
  todas contra el criterio de 0,25 m—, que es la inobservabilidad longitudinal ya documentada, y sus
  cúspides valen 6, 0, 9 y 0, o sea nada llamativo. Tres son de condición A y una (la 27) de B.
- **El veredicto `VALIDA` de la campaña sigue en pie**, con 0 descartes sobre un techo del 20 %.

## 6. Qué no se cambia, y por qué

**No se toca la configuración.** Hay tres palancas concebibles y las tres se descartan hoy:

1. `allow_reversing: false` apagaría el bloque de la línea 303 y con él el ciclo límite, pero también
   toda marcha atrás. Los planes de `SmacPlannerHybrid` con primitivas Reeds-Shepp **contienen**
   marchas atrás; ejecutarlos sin poder retroceder es peor que el problema.
2. Subir `xy_goal_tolerance` por encima de 0,19 m dejaría cerrar la etapa antes de caer en la trampa,
   pero ese número está justificado con un presupuesto de error escrito en el propio YAML
   (0,150 parada + 0,065 AMCL + 0,023 rejilla = 0,238 < 0,25) y moverlo es mover lo que se le pide a
   Nav2 mirando un resultado. Es exactamente lo que el §6.3 del protocolo prohíbe.
3. La corrección de raíz está aguas arriba, en la guarda de `curvature` de Nav2, y no es del alcance
   de esta tesis parchear el controlador trece días antes del congelamiento de código.

La campaña de OE4 se corrió con esta configuración y está cerrada con veredicto `VALIDA`. Cambiarla
ahora no arreglaría ninguna misión ya medida y obligaría a discutir si las 30 siguen siendo
comparables. **El resultado de esta investigación es la explicación, no un parche.**

## 7. Lo que sí queda para la próxima campaña

`/robotN/lookahead_point` y `/robotN/received_global_plan` —los dos los publica el propio
controlador, líneas 200 y 201— **no se graban**. El punto de persecución de la §3.3 está
*reconstruido* replicando el código sobre el plan y la pose del bag, no observado. La reconstrucción
predice la magnitud medida con tres cifras y explica el cero exacto, así que se sostiene; pero si se
graban esos dos tópicos, la misma pregunta se contesta leyendo en vez de replicando. Es una línea en
la lista `TOPICOS` de `grabar_mision.sh` y no cuesta nada.

---

**Herramientas usadas:** `componer_registro.leer_bag` sobre `~/tesis_evidencia/S21_OE4_09`; fuente de
`nav2_regulated_pure_pursuit_controller` en la etiqueta `1.1.20`, la misma que declara el paquete
instalado.
