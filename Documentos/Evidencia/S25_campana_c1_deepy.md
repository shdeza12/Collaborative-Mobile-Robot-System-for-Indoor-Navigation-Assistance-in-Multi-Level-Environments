# Sesión de compuertas G-2 y G-3 con `amss-ez9n` (29 de septiembre, noche)

Registro del bloque B de [`PLAN_S25.md`](../historial/PLAN_S25.md), siguiendo
[`GUIA_CAMPANA_NAV2_HARDWARE.md`](../historial/GUIA_CAMPANA_NAV2_HARDWARE.md), en el escenario de las dos cajas
armado según el §2 de la guía y sobre el mapa [`S24_mapa_pasillo6m_HARDWARE`](S24_mapa_pasillo6m_HARDWARE.yaml).
No fue en los pasillos del modelo de simulación: los vehículos todavía no han estado en ellos. La
ejecutó Claude por SSH desde el portátil; Santiago y Jonny armaron el sitio y acompañaron el vehículo.
Las horas del vehículo van en UTC y las del portátil en la hora local, cinco horas menos.

## Corrección: el mapa no correspondía al sitio

El escenario de las dos cajas es un pasillo que no tiene relación con el sitio donde se hizo el mapa
`S24_mapa_pasillo6m_HARDWARE` el 24-sep, ni con los pasillos del modelo de simulación. Aun así, la
sesión se preparó y se corrió sobre ese mapa. Se pidió armar el sitio con las medidas del §2 de la
guía y se arrancó Nav2 con el mapa S24, sin confirmar antes que el pasillo fuera el mismo. Fue un
error de preparación de Claude. AMCL comparó el láser con paredes que no estaban donde el mapa las
pone.

Por eso las cuatro corridas no valen para G-2 ni G-3, ni para juzgar la navegación: las cifras de
AMCL y el comportamiento de Nav2 de este registro están afectados por un mapa equivocado. Sí siguen
valiendo los dos defectos de software del §2.2 y el §2.3, que no dependen del mapa, y queda por
revisar el salto de rf2o del §2.4, que tampoco depende de él.

## Resultado

G-2 y G-3 no quedan cerradas. De cuatro corridas, una llegó según Nav2 pero se pasó de la meta, dos
abortaron antes de mover el vehículo por dos defectos que se corrigieron en la misma sesión, y la
cuarta se perdió y no se detuvo. Ninguna tiene medida con flexómetro, que es la que exigen las dos
compuertas. La sesión se repite el miércoles 30, día de reserva del plan.

## 1. Preparación

- Los dos vehículos quedaron con los mismos 15 archivos del §3.1 de la guía, más
  `mapear_conduciendo.sh`, `avanzar_y_detener.py` y `extraer_mapa.py`, con el md5 del repositorio.
- El portátil llegó a los vehículos por cable: un adaptador USB-Ethernet conectado al router, con la
  dirección 192.168.0.100, mientras el WiFi seguía en la red de la universidad.
- `amss-jgm9` perdió el WiFi al llevarlo al sitio, lejos del router. Se acercó el router al tramo y
  `amss-jgm9` no volvió: se había descargado la batería de su computadora. La sesión siguió con
  `amss-ez9n`.
- En `amss-ez9n` se detuvieron la cámara y `sensor_fusion_node`, que el proyecto no usa, para dejar
  el procesador a Nav2.

Nav2 quedó activo en unos 4 min; configurar el planificador tomó 119 s. Antes de mover el vehículo,
AMCL lo situaba en (0,693, 0,002), el planificador trazó la ruta a la meta (5,70, 0) con resultado
`SUCCEEDED`, y los dos mapas de costos, AMCL y rf2o aparecían suscritos a `/rplidar_ros/scan`.

## 2. Las corridas

`correr_corrida_nav2.sh c1d_0N --salida 0.70 0.0 0.0 --avance 5.0`, escala 0,9, filas en
`~deepracer/campana_c1_deepy.csv` y grabación en `~deepracer/campana_c1d_0N/` de `amss-ez9n`.

| Corrida | Resultado de Nav2 | Tiempo | Avance según AMCL | Avance según `/odom` | Error según `/odom` | Flexómetro |
|---|---|---|---|---|---|---|
| `c1d_01` | `SUCCEEDED`, 0 recuperaciones | 5,9 s | 5,526 m | 6,134 m | +1,134 m | no se midió |
| `c1d_02` | `ABORTED` sin moverse, 4 recuperaciones | 0,5 s | 0,064 m | 0,000 m | −5,000 m | no aplica |
| `c1d_03` | abortada por la herramienta antes de mandar la meta | — | — | — | — | no aplica |
| `c1d_04` | `ABORTED`, 20 recuperaciones | 26,8 s | 2,108 m | 10,971 m | +5,971 m | no se midió |

### 2.1 Sobrepaso de la meta en `c1d_01`

Nav2 dio la meta por alcanzada, pero el vehículo siguió rodando: `/odom` lo sitúa 1,134 m más allá de
la meta, y AMCL 0,536 m. Recorrió los 5 m en 5,9 s. Las dos cifras superan los 0,5 m de tolerancia
de llegada del vehículo real. El vehículo se devolvió a la salida antes de medirlo con flexómetro, así
que la corrida no cuenta para G-2 ni para G-3.

### 2.2 Plazo de confirmación del planificador en `c1d_02`

El árbol de comportamiento pidió la ruta y el planificador no confirmó la petición dentro del plazo
de `bt_navigator`, que Jazzy fija por defecto en 20 ms (`Timed out while waiting for action server to
acknowledge goal request for compute_path_to_pose`). El árbol lo trató como fallo y lanzó las
recuperaciones: las dos limpiezas de los mapas de costos también se pasaron de plazo, y el retroceso
se negó (`Collision Ahead`) porque detrás del vehículo está la caja de salida.

Arreglo, ajuste 6 de `nav2_hardware.launch.py`: `default_server_timeout` de 20 a 1000 ms, pasado como
parámetro propio de `bt_navigator`, porque la clave no está en el YAML y `RewrittenYaml` no añade claves
nuevas. Tras relanzar Nav2, `ros2 param get /bt_navigator default_server_timeout`
devolvió 1000.

### 2.3 Pose inicial perdida en `c1d_03`

`corrida_nav2.py` aborta si AMCL no baja de 0,20 m de incertidumbre, y AMCL estaba en 0,66 m, que es
la incertidumbre de la pose que envía el script de arranque. La herramienta publicaba la pose inicial
tres veces en 1,5 s sin esperar a que AMCL estuviera suscrito, y con Nav2 recién reiniciado los
mensajes se perdieron.

Arreglo en `corrida_nav2.py`: espera hasta 10 s a emparejarse con AMCL antes de publicar. En
`c1d_04` AMCL convergió a 0,133 m.

### 2.4 Salto de la odometría en `c1d_04`

Nav2 abortó a los 26,8 s y los observadores vieron que el vehículo pasó de los 6 m sin detenerse.
`/odom` dice 10,971 m, que en un tramo de 6 m entre cajas es imposible: la odometría de rf2o saltó. El
registro de Nav2 de esa corrida tiene 6 `Start occupied`, 3 «colisión por delante», 2 retrocesos (uno
completado y uno fallido), 2 esperas y el controlador a 4,5 Hz de media. Con el mapa de otro sitio,
es lo esperable que AMCL se perdiera y que el planificador situara al vehículo dentro de un
obstáculo. El salto de `/odom` viene de rf2o, que no usa el mapa, y es lo que hay que revisar en la
grabación.

La grabación no se pudo leer esa noche: el portátil salió de la red de los vehículos. Queda en
`~deepracer/campana_c1d_04/` de `amss-ez9n`.

## 3. Cambios de la sesión

| Archivo | Cambio | En `amss-ez9n` | En `amss-jgm9` |
|---|---|---|---|
| `nav2_hardware.launch.py` | Ajuste 6: `default_server_timeout` 1000 ms | copiado, md5 igual | pendiente (sin batería) |
| `corrida_nav2.py` | Espera a AMCL antes de publicar la pose inicial | copiado, md5 igual | pendiente (sin batería) |

## 4. Pendiente para el miércoles 30

0. Antes de nada, fijar el sitio de G-2 y G-3 y confirmar que hay un mapa de ese sitio. Si el sitio
   es el pasillo de las dos cajas, hay que mapearlo primero con `mapear_conduciendo.sh`, de ida y
   vuelta, y calcular salida y meta con `zona_libre_mapa.py` sobre el mapa nuevo.
1. Copiar de `amss-ez9n` al portátil las cuatro grabaciones, sus registros y el CSV, y analizar
   `c1d_04`: dónde saltó `/odom`, qué hizo AMCL y por qué el controlador siguió mandando avance.
2. Copiar a `amss-jgm9` los dos archivos del §3.
3. Decidir con esos datos la escala de la próxima serie. Con 0,9 `c1d_01` se pasó 1,134 m según
   `/odom`; la guía proponía 0,68 para `amss-ez9n`, y cambiar la escala abre una serie nueva con su
   propio CSV.
4. Repetir las tres corridas con medida de flexómetro en cada una, antes de tocar el vehículo.
