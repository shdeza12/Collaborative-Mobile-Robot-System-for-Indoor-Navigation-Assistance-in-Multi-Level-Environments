# S18 — Entorno de dos niveles: construcción y validación

**Fecha:** 2026-08-14. **Código base:** `dae9f9a`.
**Cubre:** tareas 11, 12, 13 y 14 de `PLAN_S17_S18.md`.

Objetivo: que exista un entorno de evaluación con dos niveles, porque la cuarta métrica del
objetivo específico 4 es *continuidad del servicio entre niveles*. Sin un nivel 2 navegable
esa métrica no se puede medir, solo declarar.

---

## Resultado 1 — la planta es un modelo reutilizable

`primer_piso_v2.world` traía la planta como un `<model>` en línea, imposible de instanciar dos
veces. Se extrajo a `primer_piso/model.sdf` + `primer_piso/model.config`.

**El plan partía de una premisa falsa.** Decía extraer el bloque `<model>` y no tocar el
`<state>`, dando por hecho que las poses de los dos bloques se contradecían en ~21 m (así se
había registrado en `35c47da`). No se contradicen: **las de `<state>` son absolutas y las de
`<model>` son relativas al modelo.** Restando la pose del modelo en `<state>`
(20,9036 · 1,43563) se recuperan exactamente las relativas, en los doce muros:

| Enlace | Residuo (m) | Enlace | Residuo (m) |
|---|---|---|---|
| `Wall_5` | (−3·10⁻⁵ · 0) | `Wall_15` | (0 · 0) |
| `Wall_7` | (−3·10⁻⁵ · 0) | `Wall_17` | (−8·10⁻⁵ · 0) |
| `Wall_9` | (−4·10⁻⁵ · 0) | `Wall_19` | (0 · 0) |
| `Wall_11` | (0 · 0) | `Wall_Gap1` | (3·10⁻⁵ · 3·10⁻⁵) |
| `Wall_13` | (0 · 0) | `Wall_Gap2`–`Gap4` | ≤ 3·10⁻⁵ |

Todos por debajo de 0,1 mm, que es el redondeo del `.world`. **El desplazamiento de 21 m era
del bloque entero, no de la geometría.** La extracción fue por tanto una copia literal
—`diff` sobre el contenido, ignorando sangría, da idéntico— y la pose se trasladó al
`<include>` del mundo. La pose del propio modelo quedó en cero, para que la posición la fije
quien lo instancia y no haya dos poses componiéndose en silencio.

**Comprobación cruzada independiente:** los muros del modelo extraído abarcan
`x ∈ [−1,24 · 43,05]`; el mapa vigente `primer_piso_definitivo.yaml` abarca
`x ∈ [−1,20 · 43,00]`. Coinciden, luego la extracción quedó donde el mapa ya esperaba.

## Resultado 2 — el mundo de dos niveles carga

`primer_piso_dos_niveles.world`: dos `<include>` de `model://primer_piso` (z = 0 y z = 3,0) y
una losa estática, porque `ground_plane` solo existe en z = 0. Ambos archivos pasan
`gz sdf -k`. Gazebo carga los cinco modelos: `ground_plane`, `primer_piso_n1`,
`losa_nivel_2`, `primer_piso_n2` y `robot1`. Evidencia: `S18_gazebo_dos_niveles.png`.

**Se corrigió un número del plan.** Proponía la losa en `10 0 2.95`, que con 50 m de lado
llegaría hasta x = 35; los muros llegan a x = 43,05. Se centró en `22.5 1.5 2.95`, mismo
tamaño, cubriendo `x ∈ [−2,5 · 47,5]`.

**Queda un hueco de 0,4 m** entre el techo de los muros (z = 2,5) y la cara inferior de la
losa (z = 2,9). No afecta a la simulación —ningún cuerpo ocupa esa franja— pero visualmente
la losa flota. Se deja así para respetar los 3,0 m de separación entre plantas, que es la
cota realista.

## Resultado 3 — un robot navega en el nivel 2

`nav_amcl_demo_sim.launch.py` no declaraba `z`, así que no había forma de pedir el nivel 2.
Se añadió, y se propaga **solo a Gazebo, no a AMCL**: la pose inicial de AMCL es 2D (x, y,
yaw) y el nivel se elige con el mapa, no con la altura.

```
ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py world:=<repo>/primer_piso_dos_niveles.world namespace:=robot1 z:=3.03
```

Objetivo enviado por acción a `x = 5,0`, `y = 0,0` en el marco `map`:

| | x | y | **z** |
|---|---|---|---|
| `/robot1/odom` antes | −0,00095 | −0,00977 | **2,9929972** |
| `/robot1/odom` después | 4,78854 | 0,07895 | **2,9929953** |
| Δ | 4,78949 | 0,08872 | **−1,9·10⁻⁶** |

Recorrido real **4,79 m** sobre un objetivo de 5,0 m, con `SUCCEEDED`. En H1, sobre el mismo
objetivo en el nivel 1, se midieron 4,89 m y 4,96 m: el nivel 2 se comporta igual.

**La columna que importa es la z.** Varió 1,9 micras en toda la corrida: el vehículo se apoya
en la losa y no la atraviesa. Esta medición era necesaria porque **el LiDAR no puede
distinguir los dos niveles** —las plantas son idénticas, así que un robot caído al nivel 1
daría exactamente el mismo `/scan`—. Solo la altura lo discrimina.

El vehículo nace en z = 3,03 y se asienta en 2,993: los mismos 3,7 cm que se asienta a nivel
del suelo. Confirma además, por tercera vez, que `/odom` se ancla en el origen del mundo y no
en el punto de spawn (ver hallazgo nº4 de `S17_nav2_namespaces.md`).

## Resultado 4 — la Tarea 14 no hacía falta

El plan pedía mapear el nivel 2 con SLAM. **No es necesario:** el nivel 2 es la misma planta
en las mismas coordenadas x-y, así que `primer_piso_definitivo.yaml` sirve para los dos
niveles, y así se acaba de usar en el Resultado 3. Se ahorra una jornada de mapeo y se evita
introducir un segundo mapa que podría divergir del primero.

Esto vale **mientras las dos plantas sean idénticas**, que es el caso real del edificio
(§4 de `ENTORNO_DE_EVALUACION.md`). Si alguna vez se diferencian, vuelve a hacer falta.

## Resultado 5 — zona de transición

Marca de 1,5 × 1,5 m centrada en **(41,40 · 3,03)**, dentro de `primer_piso/model.sdf` para
que caiga en las mismas x-y de las dos plantas. **Sin `<collision>`**: es una señal, no un
obstáculo. Las coordenadas se derivaron de la geometría, no a ojo; el razonamiento está en
§4 de `ENTORNO_DE_EVALUACION.md`.

**Confirmado el 2026-08-14** por Santiago: ese recinto es el descanso de la escalera real.
La derivación geométrica coincidió con la planta del edificio sin haberla consultado.

Comprobación visual: dos marcas naranjas en el mundo, una por planta, en las mismas x-y
(`S18_gazebo_dos_niveles.png`). El modelo declara un solo enlace `zona_transicion`, así que
dos es el resultado correcto de instanciarlo dos veces.

---

## Hallazgo colateral — `generar_mapa_desde_mundo.py` contaba visuales como paredes

La línea 72 tomaba el primer `<box>` del enlace **fuera cual fuera su contenedor**, de modo
que un enlace con visual pero sin colisión —exactamente la zona de transición— habría salido
como obstáculo en el mapa. Un obstáculo fantasma en el mapa no da ningún error: AMCL converge
igual y Nav2 acepta objetivos igual; el síntoma aparece después como una ruta que rodea algo
que no existe.

Corregido: ahora solo lee cajas dentro de `<collision>`. Comprobado que no altera el mapa
vigente — sobre `primer_piso_v2.world` sigue encontrando **12 paredes**, las mismas 12
posiciones desde `<state>`, y la misma cobertura.

## Limitación conocida del generador de mapas

Solo lee `<model>` en línea; **ignora los `<include>`**. Sobre
`primer_piso_dos_niveles.world` no encontraría ninguna pared. No bloquea nada hoy, porque el
mapa vigente sirve para los dos niveles (Resultado 4), pero hay que arreglarlo antes de
generar un mapa de control de este mundo.

---

## Decisión de arquitectura registrada

Se planteó si el mundo de dos niveles no contradice el resultado de H1 —que dos robots **no**
pueden compartir un `gzserver`—. No lo contradice, y conviene dejar escrito por qué:

- Lo que H1 descartó fue compartir `gzserver`, por un fallo de `gazebo_ros` en Humble que
  aplica a todos los plugins el namespace del primer modelo cargado.
- Los dos robots **sí interactúan, pero por mensajes, no por física**: el nodo de coordinación
  asigna robot y el relevo en la zona de transición es un evento de mensajería. Ninguno de los
  cuatro indicadores del objetivo 4 exige física compartida.
- Por diseño robot1 está en el nivel 1 y robot2 en el nivel 2: nunca coinciden en el espacio.

**Topología adoptada:** un `gzserver` por robot, y **los dos cargan el mismo mundo de dos
niveles**, cada uno con un solo vehículo. Se prefiere a tener dos mundos de un nivel porque
mantiene una sola geometría canónica y una sola definición de la zona de transición; el
sobrecosto es despreciable, ya que los muros añadidos son estáticos.

**El dominio ROS compartido ya está resuelto y no requiere pruebas nuevas.** El «Resultado 4»
de `S17_dos_simuladores.md` midió que `rclpy` respeta el remapeo de `/clock` (5010,76 s con
remapeo frente a 645,45 s sin él). Cuando llegue el nodo de coordinación: un solo
`ROS_DOMAIN_ID`, dos `GAZEBO_MASTER_URI`, y cada robot con `-r /clock:=/robotN/clock`. Cabo
suelto para entonces: **quién publica en `/robotN/clock`**, porque Gazebo publica en `/clock`
absoluto.

---

## Criterio de cierre

Tareas 11, 12, 13 y 14 **cerradas**. El entorno de dos niveles existe, carga, y se navega
sobre el nivel 2 con recorrido medido contra `/odom`.

Del criterio de cierre de S18 —«H1 cerrado; el mundo de dos niveles carga y se navega sobre
él; el diagnóstico responde las cuatro preguntas»— quedan cumplidos los dos primeros. **El
diagnóstico de hardware sigue sin empezar.**
