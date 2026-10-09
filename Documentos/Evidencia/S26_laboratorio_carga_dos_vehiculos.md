# Carga y ajustes del sistema completo con los dos vehículos en el laboratorio (9 de octubre, noche)

Sesión en el laboratorio, no en los pasillos, con `amss-ez9n` (deepy, `robot1`, piso 3) y
`amss-jgm9` (racey, `robot2`, piso 4). El objetivo era medir la carga de las tarjetas con el sistema
completo antes de volver al campo, y reducir lo que alarga las pruebas allí. Es la primera vez que
corre todo a la vez con la topología del 9-oct: el coordinador y el grabador en el portátil, en un
contenedor con ROS 2 Jazzy, y cada vehículo con el portátil como único par conocido. Las cadenas se
lanzaron con los mapas de los pisos 3 y 4 y la pose de la salida de cada piso: AMCL no corresponde al
sitio, lo que no importa para medir carga. Santiago y Jonny pusieron los vehículos con las ruedas en
el aire y pidieron las misiones desde el teléfono; Claude lanzó las cadenas por SSH, midió y
analizó.

Los datos quedan en el portátil:

- `~/tesis_evidencia/lab_2026-10-09/`: el registro de cada arranque (`arranque_*.log`) y los
  registros de carga de las tarjetas (`carga_*.csv`, de `registrar_carga.py`, una fila cada 5 s);
- `~/tesis_evidencia/mision_LAB_carga_01` y `mision_LAB_nav_01`: las dos grabaciones del portátil;
- `~/tesis_evidencia/registros/mision_manual_20261009_230541.json` y `..._230750.json`: los
  registros que escribió el coordinador de las dos misiones.

## Resultado

1. El portátil ve la acción de navegación, el servicio de media vuelta y el estado de los dos
   vehículos, y los vehículos no se descubren entre sí. Es lo que el 8-oct no funcionó.
2. La página de la interfaz no habría funcionado en campo: `rosbridge` no arrancaba. Se corrigió
   (`c8c7a0d`) y las misiones se pidieron desde el teléfono; la página mostró el fallo de cada una.
3. Con todo el sistema en reposo la tarjeta está al 54 % (deepy) y al 59 % (racey). Navegando, con
   las ruedas en el aire, al 68 % y al 74 %. El controlador de Nav2 se atrasó 1 y 5 veces respecto a
   sus 10 Hz, sin bajar de 5,5 Hz.
4. El planificador se configura en 19 s (deepy) y 23 s (racey) con la tabla de 10 m, frente a 81 s
   con la de 20 m, y la ruta más larga del piso 4 sale en 0,31 s.
5. El guion de arranque deja las dos cadenas listas en 4 min 4 s (deepy) y 4 min 22 s (racey),
   con Nav2 activo, frente a 4 min 45 s y el planificador todavía configurándose.

## 1. Topología de comunicación

Con las dos cadenas, los dos agentes y el coordinador en marcha, un proceso de prueba dentro del
contenedor del portátil buscó lo que el coordinador usa de cada vehículo:

| Desde el portátil | robot1 (deepy) | robot2 (racey) |
|---|---|---|
| Acción `navigate_to_pose` | sí | sí |
| Servicio `media_vuelta` | sí | sí |
| `/robotN/estado`, con la pose en el mapa | (22,04, 1,24) en `robot1/map` | (24,46, 1,29) en `robot2/map` |

Las dos poses están junto a la pose inicial dada a cada uno. Cada vehículo tenía en
`/tmp/nav2_campo/pares.sh` el par `192.168.0.105`, el portátil, que el guion de arranque detecta
solo. La grabación de 5 minutos en el portátil (`mision_LAB_carga_01`, 299,1 s) trae 597 mensajes
del estado de cada robot (2,0 Hz), 4468 y 4462 de su odometría (14,9 Hz) y 299 del estado de la
misión (1,0 Hz). `/tf` llega vacío: la pose de los dos viaja en `/robotN/estado`.

## 2. La interfaz

`coordinador_portatil.sh interfaz` dejaba solo el servidor de la página. El guion corre con
`set -u`, y el `setup.bash` de ROS lee variables sin definir: con esa opción aborta en la línea 8
(`AMENT_TRACE_SETUP_FILES: unbound variable`), así que `rosbridge` y `rosapi` no llegaban a
lanzarse. Tampoco se paraba el demonio de `ros2`, por la misma causa. Además, los procesos en segundo
plano se lanzaban de una forma que dejaba un proceso intermedio con la salida de quien llamaba al
guion, y cuando esa salida iba a una tubería el guion no terminaba. Con el arreglo, cada proceso
corre en su propia sesión, con su registro, y el guion termina en 9 s con `rosbridge` en el puerto
9090 y la página en el 8000.

## 3. Carga en reposo

Promedio de una ventana de 5 minutos con las dos cadenas, los agentes, el coordinador, `rosbridge`,
`rosapi` y el grabador en marcha. El procesador total está en % de la tarjeta (100 = los dos
núcleos llenos); cada grupo, en % de un núcleo.

| | deepy | racey |
|---|---|---|
| Procesador de la tarjeta | 53,6 % | 59,2 % |
| Carga media de 1 minuto | 2,6 | 3,1 |
| Servidores de Nav2 | 32,2 % | 34,9 % |
| rf2o | 19,3 % | 19,2 % |
| Controlador del LiDAR (AWS) | 10,1 % | 10,8 % |
| Resto de procesos de AWS | 8,7 % | 13,7 % |
| IMU | 6,2 % | 6,3 % |
| AMCL | 5,7 % | 6,0 % |
| Filtro EKF | 5,0 % | 5,1 % |
| `map_server` | 3,8 % | 3,9 % |
| Proceso de `ros2 launch` | 3,4 % | 3,5 % |
| Otros (incluido el agente) | 9,1 % | 10,6 % |
| Memoria | 1142 MB | 1147 MB |
| Temperatura | 35,9 °C | 36,6 °C |

El agente gasta un 7,5 % de núcleo según `top`. En el registro de carga queda en «otros»: el grupo
`coordinacion` de `registrar_carga.py` marca 0 % (§7). El 8-oct, con las dos cadenas por difusión,
racey llegó a carga 22–33.

## 4. Carga navegando, con las ruedas en el aire

Con los dos vehículos sobre una base, sin que las ruedas tocaran el suelo, se pidieron dos misiones
desde el teléfono. Nav2 planifica y manda órdenes como en campo; el vehículo no avanza, así que Nav2
detecta que no progresa, recorre sus recuperaciones (espera y retroceso) y aborta. El LiDAR veía
además los objetos del laboratorio delante del vehículo, que no están en el mapa, y el controlador
avisó varias veces «collision ahead». Ninguna misión pidió media vuelta: los salones quedan a menos
de 11° del rumbo de la salida.

| Misión | Vehículo en marcha | Duración hasta el aborto |
|---|---|---|
| Salón 301 → Salón 401 | deepy, hacia el 301 (15,9 m) | 75,6 s |
| Salón 401 → Salón 403 | racey, hacia el 401 (18,3 m) | 145,8 s |

| | deepy | racey |
|---|---|---|
| Procesador de la tarjeta, media (máximo) | 68,4 % (71,6 %) | 74,5 % (79,3 %) |
| Servidores de Nav2, media (máximo) | 47,5 % (51,3 %) | 50,7 % (57,1 %) |
| rf2o | 19,3 % | 21,3 % |
| AMCL | 5,6 % | 5,9 % |
| Resto de procesos de AWS | 9,3 % | 14,4 % |
| Temperatura | 40,2 °C | 42,0 °C |
| Avisos de lazo de control atrasado | 1 (5,8 Hz) | 5 (mínimo 5,5 Hz) |

El controlador ya corre a 10 Hz en el vehículo (ajuste 4 de `nav2_hardware.launch.py`, del 29-sep,
cuando el lazo daba entre 1 y 6 Hz). AMCL no procesa barridos con el vehículo quieto: navegando de
verdad, el 7-oct en racey la tarjeta llegó al 83 % como máximo
([`S26_piso4_cadena_media_vuelta.md`](S26_piso4_cadena_media_vuelta.md)).

## 5. Ajustes y su efecto

### 5.1 rf2o solo escribe errores (ajuste 9)

El registro de la cadena de deepy tenía 43 638 líneas tras unos 22 minutos (unas 33 por segundo).
De las últimas 20 000, 19 993 eran de rf2o: cuatro líneas INFO por barrido y el aviso «Waiting for
laser_scans», porque su lazo va a 20 Hz y el LiDAR a unos 7. Con `--log-level error` (`1e2ffc4`) el
registro dejó de crecer.

| En reposo, 3 minutos | deepy antes | deepy después | racey antes | racey después |
|---|---|---|---|---|
| Procesador de la tarjeta | 53,6 % | 52,9 % | 59,2 % | 56,8 % |
| rf2o | 19,3 % | 19,3 % | 19,2 % | 20,4 % |
| Proceso de `ros2 launch` | 3,4 % | 0,0 % | 3,5 % | 0,0 % |

El ahorro está en el proceso de `ros2 launch`, que reenviaba esas líneas, y no en rf2o: su 19 % es
el costo del cálculo.

### 5.2 Tabla del planificador de 10 m (ajuste 10)

El planificador Smac calcula al configurarse una tabla de distancias Reeds-Shepp de 20 m alrededor
del vehículo (valor por defecto). En racey eso tomó 81 s de los 115 s que tardaba Nav2 en quedar
activo. Con 10 m (`1e2ffc4`) tomó 19 s en deepy y 23 s en racey. Más allá de la tabla la distancia
se calcula al planificar; se comprobó con las rutas más largas desde la salida, sin mover los
vehículos (`compute_path_to_pose`):

| Ruta | Resultado | Poses | Tiempo de planificación |
|---|---|---|---|
| deepy, salida → Salón 301 | encontrada | 198 | 0,09 s |
| racey, salida → Salón 401 | encontrada | 208 | 0,31 s |

El plazo del planificador es de 2,0 s.

### 5.3 Guion de arranque

`nav2_mapa_guardado.sh` (`303b36c`) espera ahora a que el gestor de Nav2 escriba «Managed nodes are
active», con un tope de 300 s, en vez de dormir 55 s. El estado de los seis nodos se consulta en una
sola llamada de Python, que reemplaza seis llamadas a `ros2 service call`, y cada paso lleva su hora.

| Arranque de las dos cadenas a la vez | Hasta que terminaron los dos | deepy | racey | Planificador al terminar |
|---|---|---|---|---|
| Primero (17:39) | 4 min 14 s | no se midió | no se midió | `inactive` en deepy; racey sin respuesta |
| Con el ajuste de rf2o (18:11) | 4 min 51 s | no se midió | no se midió | `inactive` en racey; deepy sin respuesta |
| Con la tabla de 10 m (18:21) | 4 min 45 s | 4 min 45 s | 4 min 41 s | activo en los dos |
| Con el guion nuevo (18:29) | 4 min 22 s | 4 min 4 s | 4 min 22 s | activo en los dos |

El primer arranque fue con los vehículos recién encendidos. Duración de cada paso con el guion nuevo,
en deepy:

| Paso | Duración |
|---|---|
| 0 a 2 · limpieza, LiDAR y puente | 31 s |
| 3 · `map_server` | 31 s |
| 4 · AMCL | 37 s |
| 5 · Nav2 hasta activo | 68 s |
| 6 · pose inicial y comprobaciones | 77 s |

Los pasos 3, 4 y 6 son esperas fijas y llamadas a la herramienta `ros2`, que tarda varios segundos
en arrancar en la tarjeta. Juntarlas como las seis consultas de estado ahorraría unos 30 a 40 s más;
no se hizo.

## 6. Red

En reposo, durante 60 s, con el grabador en marcha:

| | Recibe | Envía |
|---|---|---|
| Portátil | 565 paquetes/s (197 KiB/s) | 296 paquetes/s (48 KiB/s) |
| deepy | 99 paquetes/s (18 KiB/s) | 435 paquetes/s (131 KiB/s) |
| racey | 413 paquetes/s (73 KiB/s) | 336 paquetes/s (108 KiB/s) |

Deepy estaba en `DEEPRACER_P3-5G` (canal 44, −13 dBm) y racey en `DEEPRACER_P4-5G` (canal 36,
−39 dBm). Con 30 `ping` a cada uno desde el portátil: sin pérdidas y sin duplicados, con 6,9 ms y
5,7 ms de promedio. El bucle de capa 2 del 7-oct
([`S26_bucle_capa2_y_red_dos_AP.md`](S26_bucle_capa2_y_red_dos_AP.md)) no volvió. Por TCP solo había
la sesión SSH del portátil en cada vehículo.

## 7. Puntos abiertos

- Racey recibe cuatro veces los paquetes de deepy (413 frente a 99 por segundo) y el portátil solo
  envía 296 en total. No son duplicados; el origen del resto no se identificó.
- El grupo `coordinacion` de `registrar_carga.py` no reconoce el proceso del agente: su consumo
  queda en «otros».
- La carga navegando se midió sin AMCL actualizando ni movimiento real: la medida de referencia en
  campo sigue siendo la del 7-oct.
- Los datos de deepy del 8-oct (el CSV de la campaña y las grabaciones `campana_p3d_0*` y
  `mv_p3d_0*`) siguen en el vehículo: los dos se apagaron al terminar, antes de copiarlos.
