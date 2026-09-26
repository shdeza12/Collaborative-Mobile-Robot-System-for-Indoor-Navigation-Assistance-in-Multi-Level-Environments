# Guion de campo — navegación en el edificio de la USTA sobre mapa derivado del modelo

**Fecha de redacción:** 2026-09-25
**Para quién:** ejecutable por cualquiera de los dos, sin haber estado en la sesión
del 24-sep por la noche.
**Qué contesta:** si el vehículo puede navegar el pasillo real usando el mapa
`primer_piso_definitivo`, que se derivó de la geometría del mundo simulado.

**Por qué este guion existe.** La noche del 24-sep quedó demostrado que **Nav2 navega
sobre un mapa guardado en hardware** ([`S24_nav2_navegacion_mapa_guardado.md`](Evidencia/S24_nav2_navegacion_mapa_guardado.md)):
4,837 m recorridos con el plan consumiéndose y la dirección trabajando. Eso abre una
vía que el proyecto llevaba un mes sin poder recorrer, porque **no necesita SLAM**: si
hay un mapa válido del pasillo real, se carga y se navega.

Y puede haberlo ya. El §4 de [`ENTORNO_DE_EVALUACION.md`](ENTORNO_DE_EVALUACION.md)
afirma que `primer_piso_v2.world` *«corresponde a la primera planta del edificio de la
USTA»* y que *«el segundo piso real del edificio es idéntico al primero»*.

---

## 0. La advertencia que manda sobre todo lo demás

**Esa correspondencia es un supuesto declarado como NO VERIFICADO por el propio
proyecto.** El §10 de `ENTORNO_DE_EVALUACION.md`, palabra por palabra:

> *el mapa SLAM del primer piso real, contrastado contra el modelo `primer_piso_v2`, da
> una comprobación **en metros** de si el entorno simulado representa el edificio.
> **Hasta ahora eso era un supuesto no verificado.**"*

Lo único confirmado en campo (2026-08-14) es **topológico**: que el recinto del extremo
este del modelo es el descanso de la escalera real. Nadie ha comprobado **una sola
distancia** del modelo contra el edificio con flexómetro.

**Y la validación que estaba planeada está bloqueada:** exigía un mapa SLAM del pasillo
real, y el SLAM en pasillo abierto ha fallado todas las veces —5,1 % y 5,9 % de
información de avance, por debajo del 6,8 % del pasillo simulado cuyo mapa se rechazó.

**Por eso el Bloque 1 de este guion es una cinta métrica y no un robot.** Es barato, no
necesita batería, y decide si el resto del día tiene sentido.

---

## 1. Bloque 1 — validar el mapa contra el edificio. **Esto primero**

No se enciende ningún vehículo. Flexómetro, cinta de enmascarar y papel.

### 1.1 · Las cifras del modelo, que son las que hay que contrastar

Extraídas de `primer_piso/model.sdf` y de `primer_piso_definitivo.pgm`:

| Qué medir | Modelo dice | Medido | Δ |
|---|---|---|---|
| **Largo de la pared larga del pasillo** (`Wall_17`) | **44,25 m** | | |
| Ancho libre del pasillo, en el tercio inicial | **5,10 m** | | |
| Ancho libre, en el tercio medio | **5,04 m** | | |
| Ancho libre, en el tercio final | **5,04 m** | | |
| Ancho del paso hacia el descanso de escalera | **1,86 m** | | |
| Tramo `Wall_7` | 12,25 m | | |
| Tramo `Wall_5` | 10,50 m | | |
| Tramo `Wall_11` | 5,50 m | | |
| Tramo `Wall_9` | 4,00 m | | |
| Espesor de pared | 0,15 m | | |

El mapa abarca **44,16 × 6,12 m**, con `x ∈ [−1,20 · 42,96]` e `y ∈ [−1,60 · 4,52]`, a
**0,06 m/celda**. El descanso de la escalera está en **(41,40 · 3,03)**.

### 1.2 · El criterio, fijado antes de medir

> **La discrepancia relativa de cada medida debe ser ≤ 2 %.**

Sobre los 44,25 m de la pared larga eso son **0,88 m**. Sobre los 5,04 m de ancho, **10 cm**.

**Por qué 2 % y no 10 %.** Esto no es G-2: no se mide un estimador, se comprueba si un
mapa sirve para localizar. AMCL corrige deriva de odometría contra el mapa, pero **no
puede corregir un mapa que está mal**: un error de escala del 5 % sobre 40 m son 2 m de
sesgo sistemático, y el filtro converge a una posición equivocada con alta confianza,
que es el peor fallo posible porque no se parece a un fallo.

**Si no pasa:** el mapa derivado del modelo **no sirve** para navegar en el edificio, y
hay que decirlo así en el documento final. El §4 de `ENTORNO_DE_EVALUACION.md` pierde su
*«argumento más fuerte»* y la etapa 3 necesita otra vía. **No se ajusta el criterio para
que pase.**

**Si pasa:** queda validado lo que el proyecto llevaba desde agosto dando por supuesto,
se puede navegar el pasillo real sin resolver el SLAM, y el hallazgo vale por sí mismo.

### 1.3 · Anotar también lo que el modelo NO tiene

El modelo son ocho paredes y nada más. El pasillo real tiene **marcos de puerta,
columnas, mobiliario, extintores**. Eso **no invalida el mapa** —la capa de obstáculos
los ve en vivo— y además es lo que le da a la localización la estructura que el pasillo
simulado no tiene. Anota **dónde están y cuántos son**: es el dato que explicará si AMCL
se localiza mejor en el pasillo real que en el simulado, que es una pregunta abierta
desde R3.

---

## 2. Antes de salir — dos correcciones de escritorio, obligatorias

### 2.1 · El mapa lee como libre lo que declara desconocido

**Medido el 2026-09-25 sobre `primer_piso_definitivo.pgm`:**

| Valor | Ocupación | Celdas |
|---|---|---|
| 0 (ocupado) | 1,000 | 5 149 |
| **205 (desconocido)** | **0,196** | **10 908** |
| 254 (libre) | 0,004 | 59 015 |

El `.yaml` trae **`free_thresh: 0.25`**, y `map_server` marca libre todo lo que esté por
debajo de ese umbral. **0,196 < 0,25**, así que las **10 908 celdas desconocidas
—39,3 m²— se leen como espacio libre** y el planificador traza rutas por ellas.

Es **el mismo defecto que el proyecto ya documentó** para `map_saver_cli` el 2026-09-08
y corrigió en `mapear_desde_bag.sh` —el mapa del pasillo de anoche lleva
`free_thresh: 0.10`, correcto—. **No se aplicó a `generar_mapa_desde_mundo.py`.**

En simulación es casi inocuo: el mundo es conocido y las 30 misiones de la campaña
corrieron bien. **En el edificio real no lo es**, porque esas 39 m² son sitio que el
modelo no describe y que en la realidad puede ser muro, mobiliario o el hueco de la
escalera.

**Corrección aplicada el 2026-09-25:** `free_thresh: 0.10` en el `.yaml`. **El generador
ya estaba bien** —lo arregló `1c8657a` el 2026-08-24, con veinte líneas de comentario
explicando exactamente este cálculo—: lo que estaba mal era **el artefacto en disco**,
generado el 2026-08-12 y nunca regenerado después del arreglo.

### 2.1 bis · Y eso alcanza a la campaña de OE4. Hay que decirlo

| Fecha | Qué |
|---|---|
| 2026-08-12 | se comitea `primer_piso_definitivo.yaml` con `free_thresh: 0.25` (`35c47da`) |
| 2026-08-24 | se **arregla el generador** (`1c8657a`) |
| 2026-08-30 → 09-05 | **corre la campaña de OE4**, 30 misiones |
| 2026-09-25 | se corrige el artefacto |

**Las 30 misiones de la campaña corrieron sobre un mapa cuyas 10 908 celdas desconocidas
se leían como libres.** En palabras del propio generador, `allow_unknown: false` del Smac
y `track_unknown_space: true` del costmap global *«estaban BIEN puestos y no servían de
nada, porque para cuando llegaban a mirar ya no quedaba ninguna celda desconocida que
rechazar»*.

**Alcance de la afirmación, y no más:** esto **no** invalida el veredicto de la campaña
por sí solo. Los cuatro fallos fueron de **precisión de llegada** (0,295–0,347 m), no de
trazado, y el pasillo por donde se navegó está mapeado como libre de verdad. Lo que **no
se sabe** es si alguna trayectoria cruzó una de esas celdas fantasma, y **es comprobable**:
los planes están en los bags conservados.

**Decisión pendiente, y es de las que un revisor externo encuentra en diez minutos:** o
se comprueba sobre los bags que ningún plan cruzó espacio desconocido, o se declara la
limitación por escrito en el capítulo de resultados. Las dos son defendibles; callarlo no.

### 2.1 ter · Dos mapas más con el mismo umbral

La auditoría del 2026-09-25 sobre los ocho `.yaml` de mapa del repositorio:

| Mapa | `free_thresh` | Estado |
|---|---|---|
| `primer_piso_definitivo.yaml` | ~~0.25~~ → **0.10** | corregido hoy; **es el que se usa** |
| `primer_piso_v2.yaml` | **0.25** | defectuoso, pero es un mapa ya **rechazado** por R10 |
| `primer_piso.yaml` | **0.25** | ídem |
| `mundo_definitivo_piso1/2.yaml` | 0.1 | correctos |
| `S24_mapa_pasillo6m_HARDWARE.yaml` | 0.10 | correcto |
| `S22_mapa_caja_SIMULACION_aceptado.yaml`, `mapa_laboratorio.yaml` | 0.196 | correctos, pero **justo en el borde**: 0,196 < 0,196 es falso por un pelo |

Los dos de `0.25` están superados por `primer_piso_definitivo` y la limitación 4 del §9
de `ENTORNO_DE_EVALUACION.md` ya mandaba rehacerlos. **No se borran: se dejan con su
umbral malo anotado**, porque un mapa rechazado con su defecto escrito vale más que un
mapa borrado. Pero **nadie debe cargarlos por descuido.**

### 2.2 · La capa de obstáculos escucha el tópico equivocado

En `nav2_params_jazzy.yaml` la capa de obstáculos del costmap global declara
`Subscribed to Topics: scan`, y el vehículo publica en **`/rplidar_ros/scan`**. El
launch reescribe `topic`, pero **en la corrida del 24-sep el costmap global no vio un
solo obstáculo nuevo**.

En un tramo despejado no importó. **En un pasillo con gente sí importa, y es condición
de seguridad, no de precisión.** Verificar antes de correr:

```
ros2 topic info /rplidar_ros/scan --verbose | grep -c "Subscription"
```

---

## 3. Bloque 2 — la navegación, con la cadena que ya está probada

Solo si el Bloque 1 pasó. **Un solo vehículo encendido**, el otro con el interruptor
apagado: un comando movió los dos a la vez el 23-sep, y apagar el GPIO no lo impide.

### 3.1 · El orden de arranque, que es lo que costó la noche del 24-sep

**El orden no es preferencia: es la causa de un fallo que no dice su nombre.** Los
costmaps leen `/map` **al configurarse**. Si `map_server` no está **activo** en ese
momento, la capa estática queda vacía y el planificador aborta con **`"Start occupied"`**
en cualquier meta, apuntando al punto de partida en vez de a la causa.

| # | Qué | Por qué en ese orden |
|---|---|---|
| 1 | Puente `cmdvel_to_servo_node` | el launch **no** lo arranca; sin él Nav2 planifica y el carro no se mueve, sin error |
| 2 | `set_max_speed` a **0,9** | con 0,68 de fábrica, `linear.x` 0,50 sale a `throttle` 0,4247 y no arranca |
| 3 | `map_server` + **activar** | tiene que estar activo **antes** del paso 5 |
| 4 | `amcl` + activar + pose inicial | |
| 5 | El launch con `slam:=false nav:=true` | ahora sus costmaps sí encuentran `/map` |

**Los tres parámetros que hay que sobreescribir**, porque el YAML los trae para
simulación y el propio archivo declara que su bloque de AMCL se conserva solo *«para que
la prueba de no divergencia pueda comparar los dos archivos enteros»*:

| Parámetro | YAML dice | Hay que poner |
|---|---|---|
| `use_sim_time` | `True` | **`false`** — no hay `/clock` en el vehículo |
| `yaml_filename` | `primer_piso_definitivo.yaml` | la **ruta absoluta** al mapa en la tarjeta |
| `scan_topic` (amcl) | `scan` | **`/rplidar_ros/scan`** |

La herramienta [`herramientas/nav2_mapa_guardado.sh`](../herramientas/nav2_mapa_guardado.sh)
automatiza los cinco pasos en ese orden y deja el sistema listo sin mandar la meta.

### 3.2 · La pose inicial, y por qué aquí NO se adivina

El §2.2 del launch descartó AMCL porque *«exige una pose inicial que aquí habría que
acertar a ojo»*. Con un mapa del edificio eso deja de ser cierto: **el mapa tiene
coordenadas del edificio**, así que se coloca el vehículo en un punto identificable
—una esquina, un marco de puerta, la marca del descanso— se lee su coordenada en el
mapa, y se publica.

```
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
 "{header: {frame_id: map}, pose: {pose: {position: {x: X, y: Y, z: 0.0}, \
 orientation: {w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, \
 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.07]}}"
```

### 3.3 · Comprobar el plan SIN mover el vehículo

**Esto es lo que más tiempo ahorra y se aprendió el 24-sep.** Antes de mandar una meta,
pedirle la ruta al planificador con una acción que no ejecuta nada:

```
ros2 action send_goal /compute_path_to_pose nav2_msgs/action/ComputePathToPose \
  "{goal: {header: {frame_id: map}, pose: {position: {x: 10.0, y: 1.0, z: 0.0}, \
  orientation: {w: 1.0}}}, use_start: false}"
```

`SUCCEEDED` = el planificador puede. `ABORTED` = no, y el log del `planner_server` dice
por qué. Separa *«el planificador no puede»* de *«el controlador no mueve»* sin
arriesgar el vehículo.

**Y comprobar que la meta cae en zona libre del mapa antes de pedirla.** El 24-sep una
meta a 8 m cayó en celdas desconocidas y abortó sin decirlo: con `allow_unknown: false`
solo se planifica sobre lo libre.

### 3.4 · La meta, y qué se mide

Con 44 m de pasillo hay sitio para metas largas. **Empezar por 5 m** y subir.

| | |
|---|---|
| **Criterio** | que planifique y que el vehículo **se mueva siguiendo el plan** |
| **NO es criterio** | llegar dentro de la tolerancia — ver §4 |
| Grabar | `/rplidar_ros/scan /odom /cmd_vel /tf /tf_static /plan /map /amcl_pose` |
| Vigilar | cúspides en el plan (la reversa **no está probada** en este hardware) |

---

## 4. Lo que va a fallar, y ya está explicado

**El vehículo va a sobrepasar la meta.** No es un defecto por descubrir: está medido y
el mecanismo cierra.

1. El vehículo **no se mueve** con `linear.x` < **0,40 m/s**: el puente traduce a
   `throttle` 0,0000 exacto y nada lo reporta.
2. Por eso el launch **sube** `min_approach_linear_velocity` de 0,05 a 0,40.
3. Consecuencia: **se aproxima a la meta a 0,40 m/s y no tiene régimen de aproximación
   fina.**
4. Con `xy_goal_tolerance: 0,25 m`, la sobrepasa **por construcción**.

El 24-sep el error fue **0,412 m** sobre una meta a 5,50 m. En simulación los cuatro
fallos de la campaña de OE4 fueron 0,295 · 0,284 · 0,311 · 0,347 m contra la misma
tolerancia: **misma métrica cuestionada desde los dos lados**.

**Anotar el error de cada corrida, no intentar arreglarlo en campo.** Las dos vías son
decisiones y no ajustes: bajar el umbral de arranque del vehículo, o subir la tolerancia
con justificación previa. La segunda es **decisión de directores**, como el criterio de
0,25 m, y va por escrito antes de la campaña de RF-27.

---

## 5. Qué anotar, por corrida

| Campo | De dónde |
|---|---|
| Hostname del vehículo y hora | el vehículo, **no la IP** — el DHCP la cambia |
| Batería antes / después | `/i2c_pkg/battery_level`. Recién cargada da 10; con 5 no arranca |
| Pose inicial publicada | la que se tecleó |
| Meta pedida | la que se tecleó |
| `SUCCEEDED`/`ABORTED` de `compute_path_to_pose` | pantalla |
| Poses del plan, primera y última | `/plan` |
| Pose final según AMCL | `/amcl_pose` |
| **Error de llegada** | calculado |
| Cúspides observadas | contando |
| Carpeta del bag | pantalla |

---

## 6. Criterio de cierre

| | Se cierra cuando | Estado |
|---|---|---|
| **Validación del modelo** | las diez medidas del §1.1 tomadas y el veredicto del §1.2 escrito | **falta** |
| `free_thresh` del mapa | corregido a 0,10 y el generador arreglado | **falta** |
| Tópico de la capa de obstáculos | verificado con suscriptor en `/rplidar_ros/scan` | **falta** |
| **Navegación en el edificio** | ≥ 1 corrida con plan seguido y bag, sobre el mapa validado | falta (depende del §1) |
| RF-27 | N = 5–10 corridas | falta |

**Lo que no cierra el guion es volver sin las medidas del §1.** Son diez números, una
cinta métrica y media hora, y deciden si el argumento central del entorno de evaluación
se sostiene. Todo lo demás del día depende de ellos.
