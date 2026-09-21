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
| **RF-13** odometría en `/<ns>/odom` | **no hay fuente en el vehículo** | decisión §3.5 |
| **RF-14** comando desde ROS 2 | campo: rampa, escalones, vídeo | batería medida |
| **RF-16** mismo código en los dos destinos | compilar en Jazzy, nunca intentado | nada |
| **RF-27** demostración física N = 5–10 | todo lo anterior | los cinco de arriba |

Dos de los seis —RF-11 y RF-16— **no están bloqueados por nada**. Eso es lo que permite trabajar en
paralelo mientras se desempata la decisión del §3.5.

### 2.2 Las cinco piezas de la cadena, en orden de dependencia

1. **`base_link`, y `base_link → laser`.** No corre `robot_state_publisher` en la tarjeta, así que
   no hay URDF cargado y nadie declara dónde está el sensor respecto al chasis. Hace falta una
   **variante de hardware del URDF**, no el de simulación: el sensor real da **360°, 1328 muestras
   y 16 m** donde `deepracer.xacro` declara 300°, 600 y 10 m, y el `hokuyo_joint` va montado con
   `rpy="0 0 3.1416"` —girado π, con la cuña ciega de 60° apuntando a la dirección de avance—.
   Nota: `config/static_tf.yaml` existe pero es un cascarón, solo trae `use_sim_time: false`.
   *Dificultad baja. No espera ninguna decisión.*
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
| 1 | TF `map → odom → base_link → laser` | ✅ | ❌ no existe ningún TF |
| 2 | odometría publicada y validada sola | ✅ verdad del motor de física | ❌ sin fuente |
| 3 | `/scan` con marco y estampas correctas | ✅ | ✅ 1,0228 m contra 1,000 m de flexómetro, 10/10 barridos, σ 2,8 mm |
| 4 | mapa | ✅ | ⚠️ el mapa existe; nunca se ha cargado en el carro |
| 5 | localización (AMCL) | ✅ | ❌ nunca ejecutado |
| 6 | mapas de costos | ✅ | ❌ imposible sin 1 y 2 |
| 7 | planificador y controlador | ✅ | ❌ |

El proyecto midió el peldaño 3 con rigor de laboratorio y caracterizó el 4 con herramientas propias,
y **nunca construyó el 1 ni el 2**. No fue desorden: el 2 resultó ser un problema de física y se
descubrió tarde. Todo el trabajo de S22 y S23 fue, sin saberlo, la investigación del peldaño 2.

---

## 3. Las cinco decisiones que van por escrito ANTES de correr

El §3 de [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) prohíbe mover criterios después
de ver resultados. Estas cinco están pendientes, y cada corrida que se ejecute sin resolverlas
queda contaminada.

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
6. **`ros2 node list` entre máquinas** y la **declaración escrita de R11**.
7. **Espacios de nombres `/robot1` y `/robot2` sobre hardware**, nunca ejercitados fuera de
   simulación.

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

- **R6 🔴** discrepancias entre informes y repositorio. Impacto declarado: *credibilidad de la
  evidencia ante el jurado*. El riesgo más barato de cerrar y el más caro de dejar.
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

**1.2 · Compilar `deepracer_bringup` en Jazzy.** Cierra RF-16 y acota el riesgo R8.

- *Comando:* `colcon build --symlink-install --packages-select deepracer_bringup` en la tarjeta,
  tras copiar la fuente.
- *Esperado:* compila, o produce una lista finita de incompatibilidades.
- *Si falla:* anotar cada incompatibilidad con su fichero y línea. **El objetivo del bloque es
  acotar el riesgo, no necesariamente resolverlo**: una lista cerrada de diez fallos conocidos vale
  más que un riesgo abierto.
- *Cierre:* RF-16 en verde, o un fichero de evidencia con la lista completa de lo que no compila.

**1.3 · RF-11: recorrido medido por `/cmd_vel`.** Es el único requisito de hardware que no depende
de nada, y su verificación no necesita ni mapa ni TF: basta publicar en `/<ns>/cmd_vel` y medir con
flexómetro.

**1.4 · Consolidar y versionar el conjunto de datos de las 30 corridas.** Criterio de cierre de
S24. Trabajo de escritorio, sin vehículos, sin decisiones pendientes.

**1.5 · Cerrar R6** —las discrepancias informe ↔ repositorio— y **actualizar el libro del
cronograma en sitio**.

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
