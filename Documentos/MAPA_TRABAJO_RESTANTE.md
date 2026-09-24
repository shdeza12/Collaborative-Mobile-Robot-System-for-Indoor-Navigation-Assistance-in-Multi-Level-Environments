# Mapa del trabajo restante y plan hasta la sustentación

**Emitido el 2026-09-18 (viernes, S23 de 32), el mismo día que se congela la implementación con el
tag `v0.4-implementacion-congelada`.** Cinco semanas hasta la ventana 1 de sustentación
(S28, 19–25 oct).

**Para qué sirve.** Acotar —cerrar, no enumerar— todo lo que queda por hacer, y decir en qué orden,
porque el orden es la parte que este proyecto ha pagado caro dos veces. Sustituye a la lista mental
y a los «pendientes» dispersos en la bitácora de [`ESTADO.md`](../ESTADO.md).

**Qué NO es.** No es un cronograma nuevo: el vigente es
[`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md) y manda sobre este documento en fechas. No es un
protocolo: el vigente es [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) y manda en
criterios y métricas. Este documento solo ordena el trabajo entre ambos.

**Cómo se mantiene.** Se edita en sitio. Cada bloque del §8 se marca cerrado con la fecha y el
fichero de evidencia que lo cierra. Si un bloque se declara imposible, se escribe por qué y se deja:
un bloque tachado con razón vale más que un bloque borrado.

---

## 1. La lectura de una frase

Hay **una sola ruta crítica**, y no es la campaña experimental: es publicar el TF
`odom → base_link` en el vehículo real. Los seis requisitos que siguen abiertos son todos de
hardware y cinco de ellos son esa cadena. Todo lo demás o cuelga de ella, o es independiente y se
puede adelantar sin decidir nada.

---

## 2. El espinazo

### 2.1 Los seis requisitos abiertos, y de qué cuelgan

De los 29 requisitos funcionales de [`REQUISITOS.md`](REQUISITOS.md), 23 están verificados. Los 6
restantes son de vehículo físico:

| Requisito | Qué le falta | Bloqueado por |
|---|---|---|
| **RF-11** locomoción por `/<ns>/cmd_vel` | recorrido medido sobre el carro | nada |
| **RF-12** `/<ns>/scan` utilizable | segunda mitad: mapa de costos local | RF-13 |
| **RF-13** odometría en `/<ns>/odom` | ~~no hay fuente en el vehículo~~ **hay fuente desde el 2026-09-24**: `rf2o` publica y mide, 3/3 dentro del ±10 % sobre 3,00 m ([`S24_peldano2_odometria_hardware.md`](Evidencia/S24_peldano2_odometria_hardware.md)). Falta la medida sobre **≥ 5 m** que pide G-2, y el espacio de nombres `/<ns>/` | el sitio de ≥ 5 m (segmento encajonado) |
| **RF-14** comando desde ROS 2 | campo: rampa, escalones, vídeo | batería medida |
| **RF-16** mismo código en los dos destinos | ~~compilar en Jazzy, nunca intentado~~ **hecho el 2026-09-22 en los dos carros**: 22 ficheros de fuente con el mismo md5, `stderr` de 0 bytes, cinco baterías en los tres destinos. Falta la **segunda mitad** del criterio, una misión en cada mundo | **G-3** |
| **RF-27** demostración física N = 5–10 | todo lo anterior | los cinco de arriba |

Dos de los seis —RF-11 y RF-16— **no están bloqueados por nada**. Eso es lo que permite trabajar en
paralelo mientras se desempata la decisión del §3.5.

**Actualización del 2026-09-22.** Esa vía en paralelo se recorrió: a RF-16 se le cerró la mitad que
no dependía de nadie, y lo que le queda ya sí cuelga de G-3. **RF-11 es ahora el único de los seis
sin bloqueo**, y su pendiente está acotado: el recorrido del 28-ago se mandó por
`/ctrl_pkg/servo_msg` y el requisito pide `/<ns>/cmd_vel`, un puente que nunca se ha ejercitado
sobre hardware.

**Segunda actualización del 2026-09-22, la misma tarde.** Al preparar el guion de ese puente
apareció que **la prueba, tal como estaba redactada, no puede pasar**. Análisis completo en
[`S24_analisis_previo_RF11.md`](Evidencia/S24_analisis_previo_RF11.md). En corto:

1. `cmdvel_to_servo_pkg` **no está en ningún carro** — sólo los 17 paquetes de fábrica de AWS. La
   tarea es desplegar y compilar, no correr.
2. Con las constantes actuales, `desired_linear_vel = 0,50 m/s` de Nav2 produce un `throttle` de
   **0,4247**, y el `0,50` publicado directo **no arrancó ninguna de cinco veces** sobre el suelo
   ([`S23_campo_traccion_RF14.md`](Evidencia/S23_campo_traccion_RF14.md) §4). La otra configuración,
   `max_vel_x = 0,26`, produce un **cero exacto**.
3. Lo que desbloquea es **una sola medida**: la curva `throttle → velocidad real` de 0,60 a 1,00.
   Su procedimiento ya existe —Bloque 7 de [`HOJA_CAMPO_G2.md`](HOJA_CAMPO_G2.md) §10— y **no
   necesita G-2**: con flexómetro y cronómetro basta.

Así que RF-11 sigue sin bloqueo *de otro requisito*, pero **tiene una precondición propia**, y es la
misma medida que cierra el pendiente de RF-14.

**Y la mitad que no dependía de esa decisión se hizo el mismo día.** El puente está **desplegado y
compilado en los dos carros**, con el mismo md5 que el repositorio, y **arranca**: `/cmd_vel` con un
suscriptor y `/set_max_speed` en el grafo. Hizo falta un arreglo de compatibilidad —el
`deepracer_interfaces_pkg` del vehículo no trae `SetMaxSpeedSrv`, así que el nodo cae en
`NavThrottleSrv`, que es idéntico campo a campo—, y **ese fallo no lo detecta `colcon`**: compiló
limpio y murió al arrancar. Queda pendiente sólo la parte que exige mover el vehículo.

**Y esa parte ya tiene guion, con un defecto de método corregido por el camino.** El punto 3 de
arriba daba por bueno sustituir rf2o por «flexómetro y cronómetro». Al escribir los comandos se vio
que `sostener_traccion.py` **no frena** —publica ceros y el carro rueda por inercia—, de modo que la
distancia hasta donde el carro queda quieto incluye un término desconocido que crece con la
velocidad; y que su `--rampa` encadena tramos sin quietud entre ellos, así que sin odometría no se
puede atribuir distancia a cada escalón. **Se mide cada escalón dos veces, con 2 s y con 4 s**, y la
resta cancela arranque e inercia. Las trece corridas, el plan de parada y los criterios están en el
**§10.3-ter** de [`HOJA_CAMPO_G2.md`](HOJA_CAMPO_G2.md): **menos de cuatro minutos de vehículo**, el
resto es flexómetro. El carro de la curva es el **`amss-ez9n`**, que es el que va recto, y por eso
dos de esas trece corridas vuelven a medir el `0.50`: el umbral de arranque en que se apoya el punto
2 de arriba se midió sobre el otro vehículo.

**Corrido el 2026-09-22, y la curva no salió**
([`S24_campo_traccion_ez9n.md`](Evidencia/S24_campo_traccion_ez9n.md)). Las trece corridas se
hicieron enteras, y **la corrida de control refutó el supuesto del método**: a `throttle 1,00` el
vehículo seguía acelerando en el segundo 4, así que las restas no dan velocidades. Queda medido el
umbral en este carro —el `0.50` lo mueve, apenas— y queda **refutado** el `0,60 → menos de 0,25 m/s`
sobre el que se apoyaba el punto 2 de arriba: son 4,20 m en 4 s, factor tres. Tres corridas de
`--marcha 6` a 0,60 · 0,70 · 0,80 validarían la mitad baja de la curva; el escalón de 1,00 **no cabe
en la recta de 20 m** y necesita otro instrumento.

### 2.2 Las cinco piezas de la cadena, en orden de dependencia

1. **`base_link`, y `base_link → laser`. — CERRADA el 2026-09-21; versionada el 2026-09-24.**
   Este párrafo estaba desactualizado: decía que no corre `robot_state_publisher` en la tarjeta,
   y sí corre desde el 21-sep (`Evidencia/S24_tf_hardware_peldano_1.md`). Se cerró generando el
   URDF plano del xacro de simulación con una línea de `xacro` y copiándolo a las dos tarjetas
   como `~/deepracer_hw.urdf`. `tf2_echo base_link laser` responde `[0.029, 0.000, 0.185]`,
   RPY −180°, en los dos carros.
   Lo que faltaba, y se hizo el 24-sep, es que **ese archivo no estaba versionado**: vivía solo en
   el home de cada tarjeta, y reproducirlo exigía recordar la invocación exacta de `xacro`. Ahora
   está en `deepracer_description/models/urdf/deepracer_hardware.urdf`, reducido a los tres
   eslabones que el hardware realmente tiene —`base_link → chassis → laser`, todos fijos—, y se
   carga con `deepracer_bringup/launch/hardware_description.launch.py`, que acepta `urdf:=` para
   correr en la tarjeta sin compilar el paquete allí. Mismo resultado en `tf2_echo`, ahora
   revisable.
   **Dos correcciones de cifra.**
   *(a)* Este documento decía que el sensor real da *1328 muestras y 16 m*. Eso es la hoja de
   datos y lo que se le pasó a `xacro` el 21-sep; no es lo que publica el driver. Medido sobre el
   bag `S24_mapa_cuarto/mapa_cuarto_3`, `/rplidar_ros/scan` entrega **360 muestras, incremento de
   1,00°, de −179,00° a 180,00°, alcance 0,15–12,00 m, a 15,26 Hz**, con `frame_id: laser`. Da
   igual para la TF —en hardware el bloque `<gazebo><sensor>` es inerte, como ya señalaba la
   evidencia del 21-sep— pero queda escrito.
   *(b)* `S24_tf_hardware_peldano_1.md` §4 afirma que «los trece joints del URDF son fijos». Son
   siete fijos y **seis `continuous`**: las cuatro ruedas y las dos bisagras de dirección
   (`grep -c 'type="continuous"'` sobre el xacro). La conclusión de aquel día no cambia, porque la
   rama `base_link → chassis → laser` sí es fija y viaja por `/tf_static`; pero el árbol que está
   cargado en las tarjetas arrastra seis juntas que nadie puede publicar, porque el vehículo no
   tiene encoders y nadie emite `/joint_states`. El URDF nuevo no las declara.
   Nota: `config/static_tf.yaml` sigue siendo un cascarón, solo trae `use_sim_time: false`.
2. **`odom → base_link`.** El nudo. Detalle de arquitectura que conviene no confundir: **AMCL
   publica `map → odom`, no `map → base_link`**; da por hecho que otro sostiene
   `odom → base_link`. Sin esa pieza AMCL no se degrada, no arranca. *Dificultad alta, y no es de
   programación: ver §3.5.*
3. **Remapeo y espacios de nombres.** Bajo `deepracer-core` el sensor publica en
   `/rplidar_ros/scan`; Nav2 y `slam_toolbox` esperan `/<ns>/scan`, con el marco TF prefijado a
   `<ns>/laser`. El lanzador ya acepta `namespace:=robotN`; falta ejercitarlo sobre el vehículo.
   *Dificultad media, mecánica.*
4. **Compilar en Jazzy** (riesgo R8). `deepracer_bringup` nunca se ha compilado en la tarjeta. La
   simulación es Humble y el vehículo Jazzy; `NavigateToPose` y varios parámetros de Nav2 difieren.
   Cierra RF-16. *Dificultad desconocida: es el segundo riesgo sin acotar del proyecto.*
5. **`map_server` + AMCL sobre el vehículo.** Cargar el mapa y localizar. Es el último peldaño, no
   el primero.

### 2.3 Por qué el orden no es negociable

La *First-Time Robot Setup Guide* de Nav2 define una escalera en la que cada peldaño solo es
diagnosticable si el anterior está sano: **(1) TF completo → (2) odometría publicada y validada
sola → (3) `/scan` → (4) mapa → (5) localización → (6) mapas de costos → (7) planificador y
controlador**. Saltarse el 2 hace que el síntoma aparezca en el 7, y ahí se pierden semanas
afinando un controlador que no tiene la culpa. La guía de sintonía de Nav2 lo dice explícitamente:
ante un síntoma, primero ciclo de vida, TF, localización, mapa y costos; los parámetros del
planificador, al final.

Estado por peldaño:

| # | Peldaño | Simulación | Vehículo real |
|---|---|---|---|
| 1 | TF `map → odom → base_link → laser` | ✅ | ⚠️ `base_link → laser` de pie en **los dos carros** — `[0.029, 0.000, 0.185]`, RPY −180°, del mismo URDF (md5 `ccd781f4…`): `.101` el 21-sep, `.102` el 23-sep. Falta `map → odom → base_link`, que cuelga del peldaño 2 |
| 2 | odometría publicada y validada sola | ✅ verdad del motor de física | ✅ **2026-09-24: `rf2o` publica y MIDE.** Tres pasadas de 3,00 m contra flexómetro en el cuarto del extintor: razones **0,963 · 1,019 · 0,966**, media 0,982, σ 0,032 — **las tres dentro del ±10 %** del criterio M1. Sin deriva en parado (6–19 mm en 20–24 s). Detalle y salvedades en [`S24_peldano2_odometria_hardware.md`](Evidencia/S24_peldano2_odometria_hardware.md) |
| 3 | `/scan` con marco y estampas correctas | ✅ | ✅ 1,0228 m contra 1,000 m de flexómetro, 10/10 barridos, σ 2,8 mm |
| 4 | mapa | ✅ | ⚠️ el mapa existe; nunca se ha cargado en el carro |
| 5 | localización (AMCL) | ✅ | ❌ nunca ejecutado |
| 6 | mapas de costos | ✅ | ❌ imposible sin 1 y 2 |
| 7 | planificador y controlador | ✅ | ❌ |

El proyecto midió el peldaño 3 con rigor de laboratorio y caracterizó el 4 con herramientas propias,
y **nunca construyó el 1 ni el 2**. No fue desorden: el 2 resultó ser un problema de física y se
descubrió tarde. Todo el trabajo de S22 y S23 fue, sin saberlo, la investigación del peldaño 2.

*Actualización 2026-09-23.* La mitad baja del peldaño 1 ya está construida en los dos vehículos
(fila 1 de la tabla). Lo que sigue faltando del peldaño 1 es justo lo que produce el peldaño 2, así
que **la escalera sigue cortada en el mismo sitio**: el 2 es el que manda.

*Actualización 2026-09-24 — **la escalera deja de estar cortada en el 2**.* `rf2o` publica
`odom → base_link` en el vehículo y el desplazamiento que registra **pasa el criterio**: tres
pasadas de 3,00 m con razones 0,963 · 1,019 · 0,966 (media 0,982, σ 0,032), las tres dentro del
±10 %. Con el peldaño 2 de pie, el 1 queda completo y los peldaños 4–7 dejan de estar bloqueados
*por esta causa*. **Lo que esto no mueve, y hay que leerlo junto:** la medida es de 3 m —G-2 exige
≥ 5— y se tomó en un cuarto de 3,50 × 1,20 m con estructura encarada por los cuatro lados, o sea la
geometría buena. **No dice nada sobre el pasillo**, que sigue en 5,1 % y 5,9 % de información de
avance. El §5 de [`S24_peldano2_odometria_hardware.md`](Evidencia/S24_peldano2_odometria_hardware.md)
enumera las cuatro cosas que el resultado NO demuestra.

*Lección de método que se cobró la misma tarde, y que afecta a cómo se mide de aquí en adelante:*
con empujones de **1 m** las razones salían 0,883 y 0,828 —fallando el criterio— y parecían un
defecto del vehículo. No lo eran: el déficit es **fijo** (~0,10–0,15 m, del orden de media
carrocería) y no escala con la distancia, así que sobre 1 m vale el 15 % y sobre 3 m el 3 %.
**La longitud de la prueba es parte del instrumento**, y una pasada de 1 m no puede validar esta
cadena.

---

## 3. Las cinco decisiones que van por escrito ANTES de correr

El §3 de [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) prohíbe mover criterios después
de ver resultados. Estas cinco están pendientes, y cada corrida que se ejecute sin resolverlas
queda contaminada.

> **Resuelto el 2026-09-21 en [`ACTA_GO_NOGO.md`](ACTA_GO_NOGO.md):** el punto de decisión GO/NO-GO
> se cerró con **GO pleno** —la demostración se intenta con los dos vehículos reales—, con seis
> criterios de fallo escritos de antemano y cuatro puntos de corte con fecha, el último el
> **16 de octubre**, después del cual no se toman más datos. El acta **no** resuelve las decisiones
> 1 y 3 de esta lista: el sitio de la etapa 3 y el N de RF-27 son de directores, y el acta los
> traslada con la medición de por medio. Hasta que eso esté por escrito no se corre la etapa 3.

1. **El sitio de la etapa 3.** RF-27 y [`ENTORNO_DE_EVALUACION.md`](ENTORNO_DE_EVALUACION.md) §6
   dicen «el pasillo real de la USTA, en dos plantas». Está medido que **ninguno de los dos pisos
   contiene la información de avance**: 5,1 % en piso 1 y 5,9 % en piso 2, los dos por debajo del
   6,8 % del pasillo simulado cuyo mapa se rechazó
   ([`S23_informacion_avance_piso1.md`](Evidencia/S23_informacion_avance_piso1.md),
   [`S23_informacion_avance_piso2.md`](Evidencia/S23_informacion_avance_piso2.md)).
   **Decisión de directores, por escrito.**
2. **El criterio de llegada de 0,25 m.** Está por debajo de 1σ en misiones largas: σx crece de 0,08
   a 0,40 m en 40 m de recorrido. Parte de las corridas fallará por construcción y chocará con el
   techo de descarte del 20 %. O se cambia el criterio con justificación previa, o se acepta el
   fallo como resultado.
3. **N = 5 o N = 10.** ASTM F3244-21 da respaldo numérico al 10 —cero fallos en 10 repeticiones
   ⇒ 80 % de fiabilidad con 85 % de confianza— y ninguno al 5. Cambiar la decisión D1 es de
   directores.
4. **Verdad de terreno en movimiento: se mide, o se declara no medible.** Marca en el suelo con el
   robot detenido da 5–10 mm y cumple el factor 10× de sobra, pero solo en puntos discretos. ATE y
   RPE continuos exigen marcadores fiduciales. Si no se montan, se declara por escrito que las
   métricas de trayectoria continua no se miden en hardware.
5. **Qué publica `odom → base_link`.** Tres opciones, desempatadas por el Bloque 0 del §8:
   - **A. Marcadores fiduciales (AprilTag) como puntos de control + EKF de `robot_localization`.**
     Cada detección de un tag de posición conocida es una observación *absoluta* de posición, que
     es justo lo que el pasillo liso le niega al LiDAR: rompe la degeneración geométrica en vez de
     intentar estimarla mejor. Exactitud publicada 15–35 mm contra *laser tracker* en 4,5 × 4,5 m.
     Coste: papel y calibración intrínseca. **Sirve además de verdad de terreno**, o sea que cierra
     la decisión 4 con la misma infraestructura. Riesgos reales: degrada con distancia y ángulo, y
     medir y colocar los tags a mano es el cuello de botella —en PennCOSYVIO una red sobre 150 m
     dio ~10 cm, dominado por el error de colocación, no de detección—.
   - **B. Odometría visual estéreo con la cámara ya montada.** Aporta la componente que falta
     porque la textura sí varía con el avance. **Descartada por riesgo de CPU sin acotar:** las
     cifras publicadas son de plataformas superiores (filtros ~60 % de un núcleo; optimización
     150–240 % en Jetson Xavier) y **no existe cifra publicada para cámara estéreo en la tarjeta
     Atom del DeepRacer**. Además es relativa: deriva, así que probablemente necesitaría los tags
     de todas formas.
   - **C. No insistir en el pasillo recto.** Cambiar el sitio, no el sistema. Hay un régimen medido
     en el que la cadena completa sí funciona: la caja cerrada de 7,70 × 2,70 m dio 13,8 % de rayos
     informativos y produjo **el único mapa que este proyecto ha aceptado con SLAM** (98,1 % de
     cobertura, 0 obstáculos inventados); y el hall del piso 2 abre de 2,34 m a 10,08 m. **Solo es
     legítima si se declara antes de correr**, con la medición como justificación. Es la única de
     las tres garantizada a caber en el calendario, porque no exige construir nada en el peldaño 2.

   **Recomendación:** A, con C como red de seguridad si los marcadores no llegan a tiempo.

---

## 4. Qué se espera de las pruebas

### 4.1 El orden de las pruebas atómicas

Antes de cualquier misión, cada prueba aísla un peldaño. **Ninguna de estas existe todavía.**

| Prueba | Qué aísla | Qué se compara |
|---|---|---|
| Recta de N m | peldaño 2, escala longitudinal | avance reportado contra flexómetro |
| Giro puro de 360° | rumbo | deriva angular acumulada |
| Cuadrado cerrado | 1 + 2 integrados | error de cierre de bucle |
| Parada ante obstáculo | peldaños 3 y 6 | distancia de parada |
| Paso estrecho | 6 y 7 | pasa / no pasa, holgura mínima |
| Punto a punto | 7 | error final de posición |
| Misión multipiso completa | sistema | las cuatro métricas de OE4 |

La prueba de recta ya se intentó una vez, el 28-ago, y dio **+2,9 % de error de escala sin poder
discriminar sensor de posicionamiento**. Repetirla con verdad de terreno es parte del Bloque 3.

### 4.2 Las exigencias cuantitativas, con fuente

| Exigencia | Valor | Fuente |
|---|---|---|
| Verdad de terreno **≥10× más exacta** que el sistema bajo prueba | criterio 0,25 m ⇒ verdad **≤ 2,5 cm** | NIST / ASTM F3244-21 |
| Repeticiones contra fiabilidad | **0 fallos en 10** ⇒ 80 % de fiabilidad al 85 % de confianza; 1 en 20; 3 en 30 | ASTM F3244-21 |
| Marcado de inicio y fin del recorrido | línea de 5 cm | ASTM F3244-21 |
| Métricas de trayectoria | **ATE** (absoluto, alineado por Umeyama, RMSE global) y **RPE** (relativo sobre intervalo fijo, deriva local en m/m) | práctica establecida |
| Herramienta | **`evo`** (`evo_ape`, `evo_rpe`, `evo_traj`), que lee **rosbag2 directamente** —`nav_msgs/Odometry`, `PoseStamped`, TF— sin conversión de formato | evo |
| Reporte | media, **σ y máximo**; no solo la media | práctica académica |
| Norma de alcance | **ISO 18646-2:2024** (navegación de robots de servicio: exactitud y repetibilidad de pose, evasión, desviación de trayectoria, paso estrecho, exactitud del mapa; solo interiores). De pago: se cita por alcance y estructura, **no** por sus tolerancias | ISO |
| Formato de mapa citable | **IEEE 1873-2015** (representación de datos de mapa para navegación). No mide desempeño; aplicarlo cuesta cero | IEEE |

Consecuencia práctica de la fila de `evo`: **grabar `/odom`, `/tf` y el tópico de verdad de terreno
en el mismo bag** es todo lo que hace falta para poder calcular ATE y RPE después. No hay que
inventar formato.

El protocolo del proyecto ya tenía bien elegida la mitad de esto: *«la verdad de terreno de la
campaña física se toma con medición externa —cinta métrica sobre marcas fijas en el piso,
fotografiadas»* ([`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md), §1). Lo que no cubre es
la trayectoria en movimiento.

---

## 5. Trabajo de campo pendiente, con los vehículos delante

Ordenado por dependencia:

1. **Batería de los dos vehículos, primero y siempre** (§4.5 de
   [`HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](HOJA_CAMPO_SEGUNDO_DEEPRACER.md)). El 28-ago unas baterías
   cayendo se disfrazaron de software degradándose: el LiDAR baja de 6,8 Hz a ~2 Hz y parece que el
   componente se degrada.
2. **RF-14:** rampa `--rampa 0.04:0.30:0.02 --marcha 3` mirando el vehículo; luego escalones
   sostenidos con `herramientas/sostener_traccion.py`; dos bags; y **vídeo contra las marcas de
   flexómetro**. Sin encóders, un bag de «0 m/s a todos los *throttle*» no distingue *el carro no
   se movió* de *rf2o no lo vio*; si las dos columnas discrepan, manda el vídeo
   ([`HOJA_CAMPO_G2.md`](HOJA_CAMPO_G2.md) §10.3-bis).
3. **Techo de tracción a `throttle` 1,0.** Cuatro intentos, ninguno salió.
4. **M1 y M2:** la pasada de localización. La guía completa ya existe
   ([`GUIA_PASADA_LOCALIZACION.md`](GUIA_PASADA_LOCALIZACION.md), 680 líneas) pero corre la cadena
   **en el escritorio desde un bag**, no a bordo: sigue siendo válida y sigue sin ejecutarse.
5. **Las pruebas atómicas del §4.1.**
6. ~~**`ros2 node list` entre máquinas**~~ **medido el 2026-09-22, con respuesta negativa:**
   `ros2 node list` **no es utilizable** como instrumento aquí —devolvió 21, 15, 10, 0 y «un nodo
   habiendo tres» en corridas sucesivas del mismo día—. Lo fiable es `ros2 topic info --verbose`,
   que nombra nodo y espacio de nombres de cada extremo. **La declaración escrita de R11 sigue
   pendiente**, pero ya tiene con qué escribirse.
7. ~~**Espacios de nombres `/robot1` y `/robot2` sobre hardware**~~ **ejercitados el 2026-09-22**:
   es lo que mide la compuerta G-4 ([`Evidencia/S24_compuerta_G4_dos_en_el_grafo.md`](Evidencia/S24_compuerta_G4_dos_en_el_grafo.md)),
   con dos nodos llamados igual conviviendo por espacio de nombres.

---

## 6. Campaña y entregables, semana por semana

| Semana | Qué exige el cronograma | Situación |
|---|---|---|
| **S24** 21–27 sep | Consolidar y versionar el conjunto de datos · capítulo de resultados · entregable S23 | Las 30 corridas están hechas desde el 2026-09-05 y **no se repiten**: repetir una campaña válida sin razón declarada de antemano es cocinar los datos. Esto es trabajo de escritorio y cabe |
| **S25** 28 sep – 4 oct | **RF-27:** 5–10 corridas físicas en el pasillo, dos plantas · vídeo de la demostración · entregable S24 | **En riesgo.** Depende del espinazo completo y de la decisión §3.1 |
| **S26** 5–11 oct | Análisis comparativo simulación ↔ físico · tabla de cumplimiento requisito por requisito · entregable S25 | Depende de que S25 produzca datos |
| **S27** 12–18 oct | Conclusiones · armar la presentación | |
| **S28** 19–25 oct | **Sustentación, ventana 1** | |
| **S30–S32** 2–22 nov | Documento final y entrega | |

---

## 7. Deuda abierta que muerde al final

- **R6 ✅ cerrado el 2026-09-21** con `S24_fe_de_erratas_S15.md`: las siete discrepancias tienen
  veredicto publicado. No se corrigió el informe —está entregado y solo existe como PDF—, se
  publicó la corrección. Una de las siete no era errata: el mapa de S15 medía 23,04 × 15,72 m
  contra los «44 × 5» declarados, y esa deformación **era la inobservabilidad longitudinal tres
  meses antes de que se midiera**.
- **R4 🟡** pared sur abierta en el SDF, deja celdas desconocidas. Abierto desde S14.
- **Tres correcciones retroactivas del 2026-09-17/18**, que hay que aplicar antes de citar
  documentos anteriores: el criterio de estructura visible es **~6 m y no 12 m**; las rupturas de
  contorno **hay que pesarlas por su escalón**, contarlas como eventos binarios no caracteriza un
  pasillo; y el **LiDAR está montado girado π** con la cuña ciega mirando hacia adelante.
- **El libro del cronograma** (`Entregables/Actividad_1_Corte_1_Cronograma_2026-2.xlsx`) se edita
  **en sitio** y lleva sin actualizar desde antes de S23.
- **Dos etiquetas espurias en el remoto** (`antes-de-dominio-unico`, `respaldo-pre-rf2o`),
  arrastradas por `git push --follow-tags`. Son puntos de retorno, no versiones.
- **R9, capacidad.** El trabajo pendiente se estimó en 9–10 semanas-persona contra 7 de calendario,
  y esa cuenta es de **antes** de que apareciera el espinazo.

---

## 8. El plan

Formato de cada tarea: **objetivo · comando · resultado esperado · si falla · criterio de cierre.**
Donde el comando exacto todavía no se conoce, se dice así en vez de inventarlo.

### Bloque 0 — El desempate (30 segundos, y decide tres semanas)

**Objetivo.** Saber si la tarjeta del vehículo publica imagen. Las opciones A y B del §3.5 dependen
las dos de eso, y **ningún documento del proyecto nombra un tópico de cámara del vehículo real**:
lo medido es una lista de 19 tópicos que pasó a 22, y de ellos solo se citan por nombre
`/ctrl_pkg/servo_msg` y `/rplidar_ros/scan`. La pila de fábrica del DeepRacer incluye un
`camera_pkg`, pero eso es conocimiento general de la plataforma, **no evidencia de este proyecto**.

**Comando** — en el vehículo, con `deepracer-core` activo:

```
ros2 topic list | grep -i -e camera -e image -e mjpeg
```

**Resultado esperado.** Uno o más tópicos, presumiblemente `/camera_pkg/video_mjpeg` y
`/camera_pkg/display_mjpeg`.

**Si no sale nada.** No se insiste: **A y B se caen las dos**, C pasa de red de seguridad a plan, la
decisión §3.4 se resuelve como «no medible en hardware, con la razón escrita», y el Bloque 2 cambia
de contenido.

**Si sale algo.** Segunda comprobación antes de dar A por viable —un MJPEG a tasa baja detecta
marcadores, pero mal—: `ros2 topic hz <tópico>` y `ros2 topic echo <tópico> --once --no-arr` para
resolución y frecuencia.

**Cierre.** La salida de los comandos pegada en un fichero de evidencia, y la decisión del §3.5
escrita con su razón.

**🟢 Resuelto el 2026-09-21 — y no salió binario.**
Registro: [`S24_desempate_camara_vehiculo.md`](Evidencia/S24_desempate_camara_vehiculo.md).
**Hay imagen**, `/camera_pkg/display_mjpeg` en los dos vehículos, así que **A no se cae y C no pasa
a ser el plan**. Pero la pila de fábrica la expone a **160 × 120** —insuficiente para marcadores— y
`camera_info` viene **entero en ceros**, sin intrínsecos. El sensor sí admite 640 × 480 a 30 fps y
hasta 1280 × 640, luego los 160 × 120 son elección de AWS, no techo del hardware.

**Y esa elección está localizada en el fuente.** `deepracer-core` arranca por `start_ros.sh`, que
lanza `deepracer_launcher.py` con `camera_mode:=modern` —el nodo real es `camera_ros`, no el
`camera_pkg` de Foxy—, y allí `resolution = resize_images and [160, 120] or [640, 480]` depende del
argumento `camera_resize`, cuyo defecto es `True`. Consecuencia para la opción A, con los precios ya
medidos y no supuestos: **640 × 480 cuesta una palabra** (`camera_resize:=False`); **la calibración
cuesta editar el launch**, porque `camera_info_url` es de solo lectura y no es argumento; y **elegir
cuál de las dos cámaras Condor se usa no funciona hoy** —el bloque de detección de `libcamera` no
llegó a ejecutarse—, que es lo que hay que arreglar antes de imprimir el primer marcador.

Advertencia que sale del mismo fuente: los remapeos del nodo de cámara son **absolutos**
(`/camera_pkg/camera_info`, `/camera_pkg/display_mjpeg`), así que **envolver el launch en un
namespace de robot no separa los dos vehículos**. La pieza 3 del §2.2 exige tocar esos remapeos o
lanzar `camera_ros` por nuestra cuenta.

Hallazgo colateral: `ros2 topic info` devolvió **`Publisher count: 2`** sobre una cámara por carro,
y `ros2 node list` lo confirma con el aviso propio de ROS sobre **nodos que comparten nombre
exacto**, repitiendo cada nodo de `deepracer-core`. Los dos vehículos publican en el mismo nombre
absoluto y se ven entre sí: es la primera evidencia en hardware de lo que la pieza 3 del §2.2
anotaba como nunca ejercitado, y **contamina cualquier medida tomada con los dos encendidos** —la
tasa de fotogramas y las listas de tópicos de hoy, entre ellas—. Mientras no haya namespaces, medir
exige `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` tras `ros2 daemon stop`, que es como se desambiguó
la batería.

---

### Bloque 1 — Lo que no espera a nadie (se puede arrancar el lunes en paralelo)

**1.1 · Variante de hardware del URDF y `base_link` en el vehículo.** Cierra el peldaño 1.

- *Comando:* procesar `Robot/aws-deepracer/deepracer_description/models/xacro/deepracer/deepracer.xacro`
  con los parámetros del sensor **real** —360°, 1328 muestras, 16 m, `yaw` π— y levantar
  `robot_state_publisher` en la tarjeta. El argumento exacto de xacro **hay que determinarlo**
  leyendo el xacro: no está resuelto y no se inventa aquí.
- *Esperado:* `ros2 run tf2_tools view_frames` produce un árbol con `base_link` y `laser`.
- *Si falla:* el modo de fallo previsible es que el xacro arrastre dependencias de
  `gazebo_ros2_control` que en la tarjeta no existen. En ese caso, URDF mínimo de dos marcos
  —`base_link` y `laser`— en vez de pelearse con el xacro completo.
- *Cierre:* árbol TF con los dos marcos, y la transformada `base_link → laser` comprobada contra
  flexómetro (el sensor está a `x = 0,02913`, `z = 0,16145`, `yaw` π respecto al chasis).

> **CERRADA el 2026-09-21.** Evidencia en `S24_tf_hardware_peldano_1.md`. `tf2_echo` en el carro
> `.101` publica `base_link → laser` = `[0.029, 0.000, 0.185]` con `yaw` −180°, y el flexómetro
> mide el plano del láser a 175 mm del piso contra 175,7 calculados: **el URDF de simulación
> describe el vehículo real dentro de 1 mm**. El peldaño 1 está de pie en hardware.
>
> Tres correcciones a lo que esta tarea daba por supuesto:
>
> 1. **El xacro no se procesa en la tarjeta.** El URDF plano se genera en el portátil y se copia;
>    `robot_state_publisher` no abre mallas. Así 1.1 deja de depender de 1.2.
> 2. **Los parámetros del LiDAR real no cierran el peldaño.** Aterrizan dentro de
>    `<gazebo><sensor>` y en hardware son inertes. Lo que coloca el sensor es `hokuyo_joint`,
>    escrito a mano en el xacro.
> 3. **Faltaban paquetes base en la tarjeta** —ni `robot_state_publisher` ni `tf2_ros` en una
>    instalación de 194 paquetes—. Instalarlos resultó aditivo (`0 upgraded`) y exigió liberar
>    939 MB de caché muerta de apt. **Esto adelanta el riesgo R8 y cambia lo que hay que esperar
>    de 1.2:** el primer fallo previsible no es de código, es de dependencias ausentes. El carro
>    `.102` sigue sin tocar, como clon de control; habrá que repetir allí antes de grabar bags.

**1.2 · Compilar `deepracer_bringup` en Jazzy.** Cierra RF-16 y acota el riesgo R8.

- *Comando:* `colcon build --symlink-install --packages-select deepracer_bringup` en la tarjeta,
  tras copiar la fuente.
- *Esperado:* compila, o produce una lista finita de incompatibilidades.
- *Si falla:* anotar cada incompatibilidad con su fichero y línea. **El objetivo del bloque es
  acotar el riesgo, no necesariamente resolverlo**: una lista cerrada de diez fallos conocidos vale
  más que un riesgo abierto.
- *Cierre:* RF-16 en verde, o un fichero de evidencia con la lista completa de lo que no compila.

**1.3 · RF-11: recorrido medido.** ~~Basta publicar en `/<ns>/cmd_vel` y medir con flexómetro.~~

> **CORREGIDA y BLOQUEADA el 2026-09-21.** Evidencia en `S24_actuacion_bloqueada_servo.md`.
>
> 1. **`/cmd_vel` no existe en el vehículo.** De los 21 tópicos de `deepracer-core`, la cadena
>    real es `ctrl_pkg` → `/ctrl_pkg/servo_msg` (`ServoCtrlMsg`) → `servo_pkg`. La tarea tal como
>    estaba redactada **no es ejecutable**.
> 2. **`ServoCtrlMsg` habla en razones, no en unidades físicas**, contra los límites de
>    calibración guardados. La calibración pasa a ser parte del dato de RF-11, no del entorno.
> 3. **Bloqueada por una anomalía abierta:** desde una pérdida de alimentación de tracción,
>    `servo_pkg` no atiende sus servicios ni actúa sobre los mensajes que recibe, y el fallo
>    sobrevive a `systemctl restart`, a `reboot` y a reasentar la batería, con el diario de
>    systemd limpio. `i2c_pkg`, por el mismo camino, sí responde.
> 4. **Lo siguiente es el carro `.102`**, intacto: si allí `servo_pkg` contesta, el fallo es de
>    estado del `.101` y RF-11 se mide en el `.102` sin esperar a entender el `.101`.
> 5. Hallazgo de método con alcance más amplio: **`ros2 node list` no es fiable en las tarjetas**
>    —osciló entre 21 y 0 con el grafo sano—. La salud del grafo se mide contando tópicos o
>    servicios. `GUIA_PASADA_MAPEO.md` §2.5 queda corregida.

**1.4 · Consolidar y versionar el conjunto de datos de las 30 corridas.** Criterio de cierre de
S24. Trabajo de escritorio, sin vehículos, sin decisiones pendientes.

> **CERRADA el 2026-09-21.** Evidencia en `S24_consolidacion_datos_oe4.md`. Los 30 registros
> regeneran las métricas publicadas con una sola orden, sin ROS y sin bags: **13 de 13 bloques
> idénticos, ninguna cifra publicada se mueve**, veredicto `VALIDA` sin alertas.
>
> La comprobación encontró un hueco real: **el artefacto versionado de S21 no contenía el bloque
> `rnf01`**, que `REQUISITOS.md` y `RESULTADOS_OE4_SIMULACION.md` ya citaban. Se añade
> `S24_metricas_campana_oe4.json` con los 13 bloques intactos más el que faltaba; el JSON de S21
> **no se toca**, porque es artefacto entregado y es la prueba de que nada cambió.
>
> Queda declarada una limitación del conjunto: **los bags no están versionados** —2,2 GB fuera del
> repositorio—, así que el tramo bag → registro no es reproducible por un tercero. Lo avalan la
> comprobación de S23 y el `sha256` del catálogo que cada registro guarda.

**1.5 · Cerrar R6** —las discrepancias informe ↔ repositorio— y **actualizar el libro del
cronograma en sitio**.

> **R6 CERRADO el 2026-09-21.** Evidencia en `S24_fe_de_erratas_S15.md`. Las siete filas del §5
> de `ESTADO.md` quedan con veredicto: tres erratas del informe, una afirmación falsa con
> mecanismo explicado, dos retiradas y una precisión. La corrección se **publica**, no se aplica
> al entregable: S15 está entregado y solo existe como PDF.
>
> **Pendiente de 1.5:** el libro del cronograma
> (`Entregables/Actividad_1_Corte_1_Cronograma_2026-2.xlsx`), que se edita en sitio y lleva sin
> actualizar desde antes de S23.

---

### Bloque 2 — La cadena, después del desempate

Contenido condicionado al Bloque 0. Si sale **A**: imprimir y colocar los marcadores con posiciones
medidas, calibrar la cámara, montar `apriltag_ros`, y configurar el EKF de `robot_localization` con
`world_frame=odom` para que publique `odom → base_link` fusionando las correcciones absolutas de los
tags con lo que rf2o sí observa (lateral y rumbo). Si sale **C**: no se construye nada aquí; se
escribe la declaración de alcance y se pasa al Bloque 3 en el hall.

Cierra, en este orden: peldaño 2 → RF-13 → remapeo y espacios de nombres → `map_server` + AMCL
→ peldaño 6 → RF-12 segunda mitad.

---

### Bloque 3 — Las pruebas atómicas (§4.1)

Las siete de la tabla, en ese orden, cada una con su verdad de terreno y con `/odom`, `/tf` y el
tópico de verdad en el mismo bag para poder correr `evo` después. **Ninguna misión completa antes de
que las seis primeras pasen.**

---

### Bloque 4 — RF-27, la campaña física

N según la decisión §3.3. Inicio y fin marcados con línea de 5 cm. Misma instrumentación que en
simulación, para que la comparación de S26 mida el entorno y no la instrumentación. Vídeo de la
demostración.

---

### Bloque 5 — Análisis y escritura

**5.1 — Capítulo de resultados de la campaña en simulación. 🟢 Hecho el 2026-09-19:**
[`RESULTADOS_OE4_SIMULACION.md`](RESULTADOS_OE4_SIMULACION.md). No dependía de los vehículos, así
que se adelantó a su semana (S24). Deja dos encargos para el resto del bloque: el modo de fallo
único queda atribuido al término de estimación de pose del presupuesto de error, y el campo que
cerraría la atribución —la distancia entre pose estimada y verdad de terreno en el instante de
parada— existe hoy solo como texto libre dentro de `mensaje_usuario`.

**5.2 y siguientes.** Análisis comparativo simulación ↔ físico sobre la misma geometría; tabla de
cumplimiento requisito por requisito (§7.4 del anteproyecto); conclusiones; presentación; documento
final.

---

## 9. Lo que este documento no dice

- **No dice que el sistema no funcione.** La cadena completa está verificada en simulación con 30
  corridas, veredicto `VALIDA` y 0 descartes de 30. Lo que falta es cobertura en hardware.
- **No dice que las pruebas anteriores estuvieran mal hechas.** Los *spikes* de S19–S20 están bien
  medidos y respondieron las preguntas que se les hicieron. Lo que no hicieron —porque no era su
  objetivo— es probar el sistema navegando.
- **No dice que el pasillo sea inservible**, solo que no aporta información de avance al LiDAR. Es
  un resultado sobre un sensor y una geometría, no sobre el edificio.
- **No fija fechas.** Las fija [`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md).

---

## 10. Trazabilidad

Cifras internas: `REQUISITOS.md` (requisitos y estados), `PROTOCOLO_EXPERIMENTAL.md` (métricas,
verdad de terreno declarada, N, techo de descartes), `ENTORNO_DE_EVALUACION.md` §5–§6 (etapas),
`CRONOGRAMA_S17_S32.md` (semanas), `ESTADO.md` §2 y §4 (camino crítico y riesgos),
`Evidencia/S19_spike_p1_p2_hardware.md` (LiDAR real, 19 tópicos), `Evidencia/S20_frente_b_hardware.md`
(convivencia a 6,35 Hz), `Evidencia/S23_informacion_avance_piso1.md` y `..._piso2.md` (5,1 % y
5,9 %), `GUIA_PASADA_LOCALIZACION.md` y `GUIA_PASADA_MAPEO.md` (ausencia de `/odom`, `/tf` y
`/tf_static` en el vehículo, comprobada el 2026-09-01),
`deepracer_description/models/xacro/urdf/deepracer_stereo_cameras_and_lidar_urdf.xacro` (el
`hokuyo_joint` girado π).

Fuentes externas:

- Nav2 — First-Time Robot Setup Guide: <https://docs.nav2.org/setup_guides/index.html>
- Nav2 — Setting Up Odometry: <https://docs.nav2.org/setup_guides/odom/setup_odom.html>
- Nav2 — Smoothing Odometry using `robot_localization`: <https://docs.nav2.org/setup_guides/odom/setup_robot_localization.html>
- Nav2 — Tuning Guide: <https://docs.nav2.org/tuning/index.html>
- ISO 18646-2:2024, *Robotics — Performance criteria and related test methods for service robots — Part 2: Navigation*: <https://www.iso.org/standard/82643.html>
- ASTM F3244-21, *Standard Test Method for Navigation: Defined Area*: <https://store.astm.org/f3244-21.html>
- NIST, *Navigation Performance Evaluation for Automatic Guided Vehicles*: <https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=918241>
- IEEE 1873-2015, *Robot Map Data Representation for Navigation*: <https://standards.ieee.org/standard/1873-2015.html>
- `evo` — evaluación de odometría y SLAM: <https://michaelgrupp.github.io/evo/>
- Kikkeri et al., *An Inexpensive Method for Evaluating the Localization Performance of a Mobile Robot Navigation System* (ICRA 2014): <https://www.microsoft.com/en-us/research/publication/an-inexpensive-method-for-evaluating-the-localization-performance-of-a-mobile-robot-navigation-system/>
- PennCOSYVIO — benchmark con red de marcadores fiduciales: <https://www.cis.upenn.edu/~kostas/mypub.dir/pfrommer17icra.pdf>
- *Task-driven SLAM Benchmarking for Robot Navigation*: <https://arxiv.org/html/2409.16573v2>
- *Combining vision and range sensors for AMCL localization in corridor environments*: <https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1652251/full>
