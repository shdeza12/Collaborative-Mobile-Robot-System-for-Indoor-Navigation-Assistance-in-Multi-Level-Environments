# Evidencia

Índice de todo lo que esta carpeta contiene: qué muestra cada archivo, de cuándo es y qué
afirmación sostiene.

Existe porque una captura sin pie de foto no es evidencia. A los seis meses nadie recuerda
qué demostraba, y ante un jurado no se puede citar lo que no se puede explicar. Diez de
estas imágenes llevaban meses en el repositorio sin que ningún documento las mencionara:
estaban guardadas, no documentadas. La diferencia importa.

**La regla:** toda evidencia nueva entra con su fila en este índice, en el mismo commit.

---

## Semana 12 — el vehículo aparece, obedece y publica odometría (abril 2026)

Primera validación del stack en simulación: que el modelo cargue, que el LiDAR emita y que
el lazo `/cmd_vel` → movimiento → `/odom` esté cerrado.

![El DeepRacer en Gazebo con el barrido del LiDAR](gazebo_spawn.png)

`gazebo_spawn.png` — el vehículo instanciado sobre el plano de suelo, con el abanico azul
del LiDAR desplegado. Sostiene que el modelo carga con su geometría y que el plugin del
sensor está activo, no solo declarado.

![Vista cercana del vehículo y el abanico del LiDAR](S12_gazebo_lidar_vehiculo.png)

`S12_gazebo_lidar_vehiculo.png` — la misma escena de cerca: se distingue el chasis y los
rayos saliendo del sensor. Es la que muestra que el LiDAR está montado donde debe, no en el
origen del mundo.

![Terminal publicando en /cmd_vel](cmdvel_publish.png)

`cmdvel_publish.png` — `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist` en repetición. El
lado del mando: se está ordenando movimiento.

![Terminal con ros2 topic echo /odom](odom_echo.png)

`odom_echo.png` — `ros2 topic echo /odom` con `twist.linear.x = 0.4045 m/s` y
`y = 0.1089 m/s`. El lado de la respuesta. Las dos juntas cierran el lazo: se ordena y el
simulador contesta con movimiento medido, que es lo que ninguna de las dos prueba por
separado.

![Barrido del LiDAR en una grabación de pantalla](S12_lidar_screencast.png)

`S12_lidar_screencast.png` — el barrido del LiDAR en movimiento. **Es una foto de un
reproductor de vídeo**, no una captura directa de Gazebo: procede del screencast
`04-29-2026 07:52:24 PM.webm`, que no está versionado. Se conserva porque el barrido
dinámico no se aprecia en una imagen fija, pero conviene saber que es una copia de segunda
mano.

---

## Semana 13 — wall-follower en el pasillo (mayo 2026)

Inicio de la Fase 4: modelado del entorno y primer controlador reactivo.

![El vehículo dentro del modelo del pasillo](deepracer_pasillo.png)

`deepracer_pasillo.png` — el vehículo dentro del pasillo modelado, con el LiDAR chocando
contra las paredes. Sostiene que el mundo propio del proyecto carga y que el sensor lo ve.

![Registro de convergencia del wall-follower](logs_convergencia.png)

`logs_convergencia.png` — el nodo `wall_follower` (técnica F1TENTH de dos rayos) imprimiendo
`D_fut`, error y consigna angular en cada iteración. Es la evidencia numérica del
comportamiento descrito en el entregable S13: converge parcialmente en pasillo amplio y es
inestable en el pasillo estrecho por el radio mínimo de giro Ackermann. Ese resultado es el
que llevó a abandonar el wall-follower puro y pasar a navegación basada en mapa.

---

## Semana 14 — validación del stack de sensores (mayo 2026)

![El vehículo en el modelo del primer piso](deepracer_primer_piso.png)

`deepracer_primer_piso.png` — el vehículo en el modelo del primer piso USTA, con las paredes
de ladrillo y el barrido del LiDAR sobre ellas.

![RViz mostrando el LaserScan](rviz_configuracion.png)

`rviz_configuracion.png` — RViz con el `LaserScan` dibujado como nube de puntos, marco fijo
`base_link`. Sostiene que el `/scan` llega a RViz con marco válido.

> Vale la pena mirar el panel *Displays* de esta captura: `RobotModel` aparece **en rojo**
> mientras el `LaserScan` se dibuja bien. Coincide con el defecto que se explicó mucho
> después, en el [hallazgo colateral nº2 de S17](S17_nav2_namespaces.md): las URIs
> `package://meshes/...` estaban sin nombre de paquete, así que RViz no encontraba las
> mallas aunque Gazebo sí. Si es el mismo, llevaba visible en pantalla desde mayo. Una
> captura archivada y no leída no avisa de nada.

![RViz, Gazebo y teleoperación por teclado a la vez](rviz_teleoperacion.png)

`rviz_teleoperacion.png` — las tres ventanas a la vez: RViz, Gazebo y
`teleop_twist_keyboard`. Sostiene que el operador manda por teclado y el efecto se ve
simultáneamente en el simulador y en la visualización, es decir, que los tres procesos
comparten el mismo estado.

---

## Semana 17 — dos robots aislados por espacio de nombres (agosto 2026)

Estas ya estaban citadas desde sus informes; se listan para que el índice esté completo.

| Archivo | Qué muestra | Informe que la cita |
|---|---|---|
| `S17_dos_gazebo_lado_a_lado.png` | Dos simuladores independientes en paralelo | [`PLAN_S17_S18.md`](../PLAN_S17_S18.md) |
| `S17_dos_objetivos_succeeded.png` | Los dos robots alcanzando objetivos distintos | [`PLAN_S17_S18.md`](../PLAN_S17_S18.md) |
| `S17_gazebo_robot1_modelo.png` | `robot1` con geometría en Gazebo | [`S17_nav2_namespaces.md`](S17_nav2_namespaces.md) |
| `S17_rviz_robot1_robotmodel.png` | El mismo modelo en RViz con `TF Prefix: robot1` | [`S17_nav2_namespaces.md`](S17_nav2_namespaces.md) |

Las dos últimas van juntas a propósito: eran las dos mitades del conflicto de una sola URI
sirviendo a dos resolvedores distintos. La configuración con la que se tomó la de RViz está
versionada en `Robot/aws-deepracer/deepracer_description/rviz/nav2_robot1_view.rviz`.

## Semana 18 — entorno de dos niveles

| Archivo | Qué muestra | Informe que la cita |
|---|---|---|
| `S18_gazebo_dos_niveles.png` | Las dos plantas separadas 3,0 m en vertical | [`S18_entorno_dos_niveles.md`](S18_entorno_dos_niveles.md) |

## Semana 19 — spike de hardware, pregunta 4 (agosto 2026)

Sin capturas: el spike es documental por diseño —compara fuentes oficiales y el propio
repositorio, sin encender ningún vehículo— y su evidencia son los archivos que compara, no una
pantalla. Los comandos que lo reproducen están en el §1 del informe.

| Archivo | Qué sostiene | Dónde se cita |
|---|---|---|
| [`S19_spike_p4_humble_jazzy.md`](S19_spike_p4_humble_jazzy.md) | Que `nav2_msgs/NavigateToPose` **difiere** entre Humble y Jazzy, y que por tanto un coordinador Humble no manda a un robot Jazzy | [`ESTADO.md`](../../ESTADO.md) §4 (R8), [`REQUISITOS.md`](../REQUISITOS.md) §3 (RF-16) |

## Semana 19 — la maniobra de retorno y el defecto de conversión de `cmd_vel` (agosto 2026)

![Giro comandado contra giro real, antes y después de la corrección](S19_seguimiento_antes_despues.png)

`S19_seguimiento_antes_despues.png` — la misma maniobra de retorno, antes (izquierda) y después
(derecha) de corregir la conversión de `angular.z`. **Fila superior:** en azul lo que Nav2 pide y
en rojo lo que el vehículo hace. A la izquierda el rojo se pasa del azul de forma sistemática y
entre t = 50 s y t = 58 s entra en una oscilación que no está en el comando; a la derecha lo
sigue. Es el mismo hecho que la tabla del informe cifra como RMS 0,298 → 0,111 rad/s, pero
visible sin leer números. **Fila inferior:** la trayectoria de cada corrida. Están para descartar
la objeción de que se comparan recorridos distintos: los dos son la misma travesía del pasillo
con el volteo al extremo este.

Las dos gráficas salen de `herramientas/graficar_seguimiento.py` sobre los bags de las corridas.
**Los bags no están versionados** —viven en `/tmp` y son efímeros—, así que esta figura no se
puede regenerar a partir del repositorio: hay que volver a grabar las corridas con el
procedimiento del informe. Se conservan la herramienta y su salida, no los datos crudos.

| Archivo | Qué sostiene | Dónde se cita |
|---|---|---|
| `S19_seguimiento_antes_despues.png` | Que el vehículo obedecía mal el giro comandado, y que tras la corrección lo sigue | [`S19_conversion_cmdvel_ackermann.md`](S19_conversion_cmdvel_ackermann.md) |
| [`S19_conversion_cmdvel_ackermann.md`](S19_conversion_cmdvel_ackermann.md) | Que `angular.z` se interpretaba como ángulo de volante y no como velocidad angular, con una ganancia que variaba por un factor de 4 según la velocidad | [`ESTADO.md`](../../ESTADO.md) §4 (R2) |

## Diagrama

| Archivo | Qué muestra | Dónde se cita |
|---|---|---|
| `arquitectura.png` | Arquitectura del sistema | [`ESTADO.md`](../../ESTADO.md) |

---

## Registros de terminal

En `logs/`, en texto plano para poder buscarlos y compararlos entre corridas. Las rutas
absolutas van redactadas como `<repo>` para que no dependan de la máquina.

| Archivo | Qué registra |
|---|---|
| `S17_aislamiento_mando.txt` | Que mandar a `robot1` no mueve a `robot2` |
| `S17_controladores_robot1.txt` | Los 7 controladores de `robot1` en estado `active` |
| `S17_topicos_dominio0.txt` | Tópicos visibles en `ROS_DOMAIN_ID=0` |
| `S17_topicos_dominio2.txt` | Tópicos visibles en `ROS_DOMAIN_ID=2` |
| `S19_maniobra_metricas.txt` | Las cuatro corridas de la maniobra de retorno, antes y después de corregir la conversión de `cmd_vel` |

Los dos últimos van en pareja: por separado no dicen nada, juntos demuestran que los dos
dominios no se ven entre sí.

## Informes

Los `.md` de esta carpeta son el análisis, no la evidencia: explican qué se hizo, qué falló
y por qué. `S17_nav2_namespaces.md`, `S17_aplicacion_contrato.md`, `S17_dos_simuladores.md`,
`S17_linea_base.md`, `S18_entorno_dos_niveles.md`, `S19_spike_p4_humble_jazzy.md` y
`S19_conversion_cmdvel_ackermann.md`.

---

## Lo que no se puede rastrear

De los nueve entregables en PDF, **solo tres conservan su fuente LaTeX**
(`Entregable_semana_17.tex`, `Entregable_semana_18.tex` y `Cronograma_S17_S32.tex`). Los de las
semanas 10 a 15 existen únicamente como PDF compilado.

Consecuencia concreta: las imágenes de S12, S13 y S14 de este índice fueron casi con certeza
a esos entregables, pero **no hay forma de comprobarlo** —no queda el `.tex` que las
incluía—, así que los pies de foto de arriba se escribieron mirando las imágenes, no
recuperando su contexto original. Si un jurado pide el origen de una figura de esos
entregables, la respuesta es que no se conserva.

No tiene arreglo retroactivo. Hacia adelante, la fuente `.tex` de cada entregable se
versiona junto al PDF. **El primero que cumple la regla desde el día uno es el de la semana 18**
(`Entregable_semana_18.tex`, compilado en Overleaf y devuelto al repositorio antes de publicar el
PDF): sus tres figuras están citadas por nombre en la fuente, así que su procedencia sí se puede
rastrear.

## Convención de nombres

`SNN_descripcion_corta.png`, con la semana delante. Ordena la carpeta cronológicamente y
dice de un vistazo a qué entrega pertenece cada archivo.

Las de S12 a S14 conservan su nombre original —renombrarlas rompería la trazabilidad con los
PDF ya entregados—, salvo dos que se llamaban `Screenshot from 2026-04-29 19-40-03.png` y
`Screenshot from 2026-04-30 11-33-07.png`. Esos nombres no decían nada y además llevaban
espacios y paréntesis, que es exactamente lo que rompió cuatro enlaces del repositorio en
agosto. Como no las citaba ningún documento, renombrarlas no rompió nada.
