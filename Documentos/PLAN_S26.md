# Plan de la semana 26 (5 al 9 de octubre)

La meta de la semana es llegar al viernes con la misión con relevo entre los pisos 3 y 4 sobre los
dos vehículos (compuerta G-5). La toma de datos se cierra el viernes 16, en el corte C-3 del
[acta](ACTA_GO_NOGO.md). Para llegar hay que dejar los vehículos estables (carga, escala, cámaras),
cerrar G-3 e integrar la IMU de la tarjeta. Las pruebas de esta semana son más estrictas que las
anteriores. El vehículo encadena misiones sin que nadie lo reubique ni le vuelva a dar la pose
inicial. Entre una misión y la siguiente no vuelve a su escalera: el coordinador lo envía a recoger
al usuario desde donde quedó (§6.2 del [acta](ACTA_GO_NOGO.md)). Lo que se hizo la semana anterior
está en [`Entregable_semana_25.md`](Entregables/Entregable_semana_25.md).

Vehículos: `amss-ez9n` (deepy, 192.168.0.102) va en el piso 3 como `robot1`; `amss-jgm9` (racey,
192.168.0.104) va en el piso 4 como `robot2` y lleva el coordinador. Todas las órdenes se lanzan
desde la raíz del repositorio en el portátil.

## 0. La semana de un vistazo

| Día | Qué se hace | Quién | Vehículos | Al terminar el día |
|---|---|---|---|---|
| Lun 5, mañana | Acta: cambio de sitio y corte C-1. Correcciones de las herramientas de campo | Santiago y Claude | no | Acta al día; herramientas corregidas y probadas en simulación |
| Lun 5, tarde | Desactivar las cámaras, comprobar la IMU, copiar grabaciones, nivelar los dos vehículos | Santiago y Jonny | los dos | Se sabe si hay IMU; vehículos nivelados |
| Mar 6 | IMU y EKF en los dos vehículos (hecho el 5-oct en la noche; queda la posición de deepy, §2.3). Red entre los pisos 3 y 4 | Santiago y Claude; Jonny la red | los dos | La IMU publica y el EKF gira bien en los dos vehículos; la red llega a los dos pisos |
| Mié 7 | Radio de giro. Misiones encadenadas en el piso 4 sin tocar el vehículo, con y sin IMU. Media vuelta para ir a recoger a un usuario | Santiago y Jonny | uno cada vez | G-3 evaluada; se sabe si el vehículo da media vuelta solo |
| Jue 8 | Coordinador en el vehículo, agentes en los dos, interfaz desde el teléfono; una misión en un solo piso | los dos | los dos | Misión en un piso pedida desde el teléfono, con registro |
| Vie 9 | G-5: misión del piso 3 al piso 4 con relevo, y una segunda misión encadenada sin tocar los vehículos. Corte semanal en la noche | los dos | los dos | G-5 intentada con registro; entregable de S26 |

Reglas de toda la semana:

- Los dos vehículos se tocan a la vez: lo que se instale en uno se instala en el otro el mismo día.
- No se navega hacia el borde de una escalera.
- Las medias vueltas solo se piden en los tramos anchos frente a los salones 301-302 y 401-402
  (de 3,1 a 3,2 m), con una persona junto al vehículo.
- Después de la primera salida, el vehículo no se toca ni se reubica entre misiones. Cada llegada se
  marca en el piso, junto al vehículo, y se mide desde esa marca.
- Cada llegada se mide con flexómetro antes de tocar el vehículo.
- Las grabaciones y registros se copian al portátil, a `~/tesis_evidencia/`, al terminar cada corrida.
- Cada prueba se fotografía y se graba según [`HOJA_CAPTURA_S26.md`](HOJA_CAPTURA_S26.md): la llegada
  con la cinta en el cuadro, el id de la corrida en el primer cuadro de cada video.
- No se actualizan los paquetes de ROS del portátil de campo antes del corte C-3. El 6-oct una
  actualización de 452 paquetes coincidió con que la simulación dejara de completar el relevo, y la
  causa no está aislada ([`S26_simulacion_tras_actualizacion_ros.md`](Evidencia/S26_simulacion_tras_actualizacion_ros.md)).

---

## 1. Lunes 5

### 1.1 · Acta: cambio de sitio y corte C-1 (hecho)

Santiago habló con los directores el 5-oct. Sus respuestas están en el §6.2 del
[acta](ACTA_GO_NOGO.md), y G-2 (alcanzada) y G-3 (abierta) en su §4.1.

| Pregunta | Respuesta |
|---|---|
| Sitio | Se acepta el cambio a los pisos 3 y 4; los directores lo trataron también con los evaluadores |
| (1) a (3) Corte C-1 | Sin fecha nueva y sin NO-GO: organizar el trabajo para presentar a tiempo. La demostración con los vehículos sigue, G-3 queda abierta con 0,5 m y C-2 y C-3 no cambian |
| (4) Regreso automático | Solo al cancelar (RF-29), como hoy. Entre misiones el vehículo no vuelve: el coordinador lo envía a recoger al usuario desde donde quedó. El regreso tras una misión completada es opcional y sin prioridad |

### 1.2 · Correcciones de las herramientas de campo (mañana, Claude)

| Tarea | Qué se corrige | Por qué |
|---|---|---|
| a | `corrida_nav2.py` publica velocidad cero antes de cerrar cuando se interrumpe | El 30-sep, al interrumpir una corrida, la orden de parada no salió (`publisher's context is invalid`) |
| b | `corrida_nav2.py` espera la confirmación de la meta como mucho 30 s | El 30-sep y el 2-oct la corrida se quedó esperando 10 min |
| c | `corrida_nav2.py` guarda la pose de AMCL en el instante en que Nav2 termina, antes de refrescarla | El 30-sep el refresco hizo saltar la pose 7,5 m y el informe dio una llegada falsa |
| d | `corrida_nav2.py` deja de imprimir «tolerancia de Nav2: 0,25» | Es un texto fijo; el margen real es 1,0 m |
| e | `lanzar_bag.inc` cierra el grabador con una interrupción y espera 10 s antes de matarlo | Con `SIGKILL` se pierde el final de la grabación (2-oct) |
| f | `nav2_mapa_guardado.sh` admite `ESCALA` (por defecto 0,9) y apaga `camera_node` y `sensor_fusion_node` antes de Nav2 | Con 0,9 racey no arranca y deepy va a 1,58 m/s; con la cámara y la fusión encendidas Nav2 se cayó (2-oct) |
| g | `corrida_nav2.py --sin-pose-inicial`: no publica la pose inicial y toma como salida la pose actual de AMCL | Para encadenar misiones sin volver a decirle a AMCL dónde está el vehículo, como en la operación real |

Prueba de cierre: `python3 herramientas/prueba_corrida_nav2.py`, que corre la herramienta contra un
Nav2 de mentira, sin Gazebo (el ensayo en Gazebo tumbó el portátil el 5-oct). Comprueba la corrida
normal, la encadenada, la interrupción con `SIGINT` y con `SIGTERM` y el límite de la confirmación.

> Estado, 5-oct: hecho. Las siete correcciones están en las herramientas, la prueba da 21 de 21 con la
> versión nueva y 15 fallos con la anterior (la interrupción reproduce el defecto del 30-sep), y el
> grabador cierra limpio con la interrupción. La versión nueva del CSV añade columnas: cada serie va
> en un fichero nuevo, `campana_s26_racey.csv` y `campana_s26_deepy.csv`.

### 1.3 · Desactivar las cámaras (tarde, en los dos vehículos)

Las cámaras se quedan conectadas, porque sin ellas el vehículo pierde su aspecto, y se desactivan por
software con una regla de `udev`: el sistema no autoriza los dispositivos `29fe:4d53` (GEO Semi
Condor), así que no crea los `/dev/video*` y la pila de AWS no las abre. La regla está en
[`config/90-tesis-camaras-desactivadas.rules`](../Robot/aws-deepracer/deepracer_bringup/config/90-tesis-camaras-desactivadas.rules),
sobrevive a los reinicios y se deshace borrando el archivo y reiniciando.

| Paso | Comando | Esperado |
|---|---|---|
| 1. Identificar | `ssh deepracer@192.168.0.104 "lsusb"` | Dos `29fe:4d53 GEO Semi Condor` (cámaras) y un `10c4:ea60 Silicon Labs CP210x` (LiDAR) |
| 2. Instalar la regla | `scp Robot/aws-deepracer/deepracer_bringup/config/90-tesis-camaras-desactivadas.rules deepracer@192.168.0.104:/tmp/` y `ssh deepracer@192.168.0.104 "sudo -n cp /tmp/90-tesis-camaras-desactivadas.rules /etc/udev/rules.d/"` | Sin salida |
| 3. Aplicarla sin reiniciar | `ssh deepracer@192.168.0.104 "sudo -n udevadm control --reload-rules && sudo -n udevadm trigger --action=add --subsystem-match=usb --attr-match=idVendor=29fe"` | Sin salida |
| 4. Comprobar | `ssh deepracer@192.168.0.104 "ls /dev/video*"` y la autorización en `/sys/bus/usb/devices/<puerto>/authorized` | Ningún `/dev/video`; `0` en los puertos de las cámaras y `1` en el del LiDAR |
| 5. El LiDAR sigue | `ros2 topic hz /rplidar_ros/scan`, como root y con la partición | Unos 7 Hz |

`lsusb` sigue mostrando las cámaras: están conectadas, pero sin autorizar. `nivelar_carros.sh`
informa del estado en cada vehículo.

> Estado, 5-oct: hecho en `amss-ez9n`. Antes, `/dev/video0` a `/dev/video7`; después, ninguno;
> autorización `0 0 1` (cámaras en los puertos 1-4 y 1-6, LiDAR en el 1-3); LiDAR a 6,90 Hz. En
> `amss-jgm9`, lo mismo: las cámaras en los mismos puertos, `0 0 1` y LiDAR a 6,82 Hz.

### 1.4 · Comprobar la IMU (tarde, en los dos vehículos)

La documentación de AWS dice que la tarjeta trae acelerómetro y giroscopio; el paquete de la
comunidad lo lee como un Bosch BMI160 en el bus I2C 1, dirección 0x68. La orden lee el registro 0 del
sensor, que en el BMI160 vale `0xd1`, sin instalar nada en el vehículo.

| | |
|---|---|
| Comando | `bash herramientas/nivelar_carros.sh --imu` (los dos vehículos; si el bus está ocupado, reintenta solo con `I2C_SLAVE_FORCE`) |
| Esperado | En cada vehículo, la lista de buses con `/dev/i2c-1` y `IMU: el registro 0 en 0x68 vale 0xd1 (BMI160)` |
| Si falla | Probar a mano la dirección `0x69` y los otros buses de la lista, con la orden de la función `imu` del guion. Si ninguno responde `0xd1`, la tarjeta no tiene ese sensor accesible: la IMU pasa a trabajos futuros y el martes se dedica a G-5 |
| Cierre | `0xd1` en los dos vehículos, con el bus y la dirección anotados |

> Estado, 5-oct: hecho. Los dos vehículos tienen la BMI160 (`0xd1` en I2C 1, 0x68) y pasaron las
> pruebas de [`PRUEBAS_IMU.md`](PRUEBAS_IMU.md); solo el módulo de la aceleración de `amss-jgm9` queda
> fuera de su criterio, sin efecto en el giroscopio
> ([`S26_pruebas_imu.md`](Evidencia/S26_pruebas_imu.md)).

Si responde `0xd1`, se comprueba que el sensor mide bien con las siete pruebas de
[`PRUEBAS_IMU.md`](PRUEBAS_IMU.md) (identidad, gravedad, ruido, orientación de los ejes, giros de
90° y 360° y deriva), antes de integrarlo en la navegación.

### 1.5 · Copiar las grabaciones pendientes (tarde)

| | |
|---|---|
| Qué | De racey: `campana_p2r_01` a `campana_p2r_08`, `campana_p4r_01`, `campana_p4r_02`, los CSV `campana_p2_racey.csv` y `campana_p4_racey.csv`. De deepy: `campana_p4d_02` y `campana_p4_deepy.csv` |
| Comando | `ssh deepracer@192.168.0.104 "cd ~ && tar czf - campana_p2r_0* campana_p4r_0* campana_p*_racey.csv p2r_0*.log p4r_0*.log" > ~/tesis_evidencia/racey_2026-10-05.tgz`, y el equivalente con la .102 |
| Esperado | Un archivo de varios MB por vehículo, que se abre con `tar tzf` |
| Cierre | Los dos archivos en `~/tesis_evidencia/` |

> Estado, 5-oct (noche), según la bitácora de `ESTADO.md`: **racey hecho.** Sus 11 grabaciones
> (p2r_01 a p2r_08 del 30-sep y p4r_01 a p4r_03 del 2-oct), los 2 CSV y los registros quedaron en
> `~/tesis_evidencia/copia_carros_2026-10-05/` del portátil de campo. **De deepy no consta la
> copia** de `campana_p4d_02` ni de `campana_p4_deepy.csv`: comprobar en ese portátil antes de dar
> la tarea por cerrada.

### 1.6 · Nivelar los dos vehículos (tarde)

| | |
|---|---|
| Qué | Copiar a `~/tesis/` de los dos lo corregido en la §1.2 (`corrida_nav2.py`, `correr_corrida_nav2.sh`, `lanzar_bag.inc`), los mapas y el catálogo de los pisos 3 y 4, y el mapa corregido del piso 2 |
| Comando | `bash herramientas/nivelar_carros.sh --copiar`. Compara 21 archivos de `~/tesis/` con el md5 del repositorio, copia los que falten o difieran y vuelve a comparar. Informa además del parche de rf2o y de la partición instalada en `/etc` |
| Comprobación | `Los vehiculos estan nivelados con el repositorio.` Si avisa de la partición en `/etc`, se reinstala con el procedimiento del bloque A ([`DISENO_AISLAMIENTO_DOS_CARROS.md`](DISENO_AISLAMIENTO_DOS_CARROS.md)), no copiándola a mano |
| Si falla | Si un vehículo no responde, queda anotado y se cierra en cuanto vuelva a la red |
| Cierre | Ningún archivo distinto del repositorio en ninguno de los dos |

> Estado, 5-oct: **hecho en los dos.** `nivelar_carros.sh --copiar` dio 21 de 21 en racey, con el
> parche de rf2o y la partición bien (bitácora de `ESTADO.md`, 5-oct noche), y esa misma noche los
> dos quedaron nivelados también con el coordinador nuevo: 15 de 15 en Jazzy (`b40738f`).

---

## 2. Martes 6

### 2.1 · El controlador de la IMU (hecho en el portátil el 5-oct)

Se usa un nodo propio, `imu_bmi160.py`, y no el paquete de la comunidad. Lee el sensor igual que
`probar_imu.py`, que ya funcionó en los dos vehículos, y no necesita `smbus2` ni `BMI160-i2c`, que
habría que instalar sin internet. El filtro es el EKF de `robot_localization` 3.8.3, que ya está en
`amss-jgm9`; en `amss-ez9n` se comprueba en el paso 1 de la §2.3.

| Pieza | Archivo | Prueba en el portátil |
|---|---|---|
| Nodo de la IMU: publica `imu/data` a 25 Hz con el sesgo medido al arrancar (a 50 Hz cargaba demasiado la tarjeta, §2.3) | `deepracer_bringup/scripts/imu_bmi160.py` | [`prueba_imu_bmi160.py`](../herramientas/prueba_imu_bmi160.py), 18 de 18 |
| Marco `imu_link` con la orientación medida | `deepracer_hardware.urdf` | `prueba_nav2_hardware_ns.py`, parte 3 |
| `imu:=true` en el lanzador: IMU, EKF, y rf2o en `odom_rf2o` sin TF | `nav2_hardware.launch.py` | `prueba_nav2_hardware_ns.py`, 102 de 102; sin IMU, igual que antes |
| El EKF toma el avance de rf2o y el rumbo de la IMU | `parametros_ekf` en el lanzador | [`prueba_ekf_imu.py`](../herramientas/prueba_ekf_imu.py), 9 de 9: con rf2o diciendo «recta» y la IMU un giro de 90°, el filtro da 89,4° a 90,0° |
| `IMU=true` en el arranque, con comprobación de `imu/data` y `odom` | `nav2_mapa_guardado.sh` | — |
| Cada corrida graba `imu/data` y `odom_rf2o` | `correr_corrida_nav2.sh` | — |
| Copia del nodo y de `probar_imu.py` | `nivelar_carros.sh` | — |

`prueba_ekf_imu.py` muestra también por qué el filtro no toma el rumbo de rf2o: rf2o publica
covarianza cero, y con su rumbo dentro el mismo giro de 90° queda en 71°.

### 2.2 · Orientación de los ejes y calibración (hecho el 5-oct)

Está en [`S26_pruebas_imu.md`](Evidencia/S26_pruebas_imu.md). Los ejes del sensor son x a la
izquierda, y hacia adelante y z hacia abajo, igual en los dos vehículos. El sesgo en z es de
0,65 °/s en `amss-ez9n` y 0,47 °/s en `amss-jgm9`, estable en la sesión. El nodo lo mide en cada arranque.

### 2.3 · La IMU y el EKF en los vehículos (hecho el 5-oct en la noche)

Resultado, en [`S26_integracion_imu_vehiculos.md`](Evidencia/S26_integracion_imu_vehiculos.md): la
IMU queda aprobada para el rumbo en los dos. En el giro de 90° contra una línea del piso, el filtro
midió +90,17° en racey y +88,38° en deepy; quieto, el rumbo se mueve 0,3° o menos por minuto,
mientras rf2o solo deriva hasta 5,9°. Por la carga de la tarjeta, la IMU quedó a 25 Hz y el filtro
a 15 Hz. La posición quieta deriva como la de rf2o, y el criterio de 1 cm del paso 6 estaba mal
puesto, porque la IMU no corrige la posición. Queda abierto que en deepy la posición del filtro se
movió 12,5 cm en 90 s, frente a 2,1 cm de rf2o: lo decide la cadena del miércoles (§3.2).

Para repetir las mediciones de los pasos 5 a 7 se usa
`python3 /home/deepracer/tesis/medir_odom_imu.py 60 --ns robotN` en el vehículo (ruta fija del vehículo), que mide filtro, rf2o e
IMU en un solo proceso; `ros2 topic echo` y `ros2 topic hz` cargan la tarjeta y fallan si el
tópico aún no está descubierto. Con los dos vehículos encendidos, la cadena se arranca siempre con
`namespace:=robot1` o `namespace:=robot2`: sin espacio de nombres, `/odom` e `/imu/data` de los dos
se mezclan.

Los pasos, tal como se escribieron antes de correrlos:

Se hace en los dos, con el vehículo en el suelo y sin Nav2 (sin mapa, en cualquier sitio). Las
órdenes son para racey; para deepy se cambia `192.168.0.104` por `192.168.0.102`. Santiago las corre y
Claude revisa las salidas.

| Paso | Qué | Comando | Esperado | Si falla |
|---|---|---|---|---|
| 1 | `robot_localization` en deepy | `ssh deepracer@192.168.0.102 "ls -d /opt/ros/jazzy/share/robot_localization"` | La ruta | Parar: sin internet hay que traer el paquete de Ubuntu 24.04, y el `apt` del portátil (22.04) no sirve. Se decide con Claude |
| 2 | Copiar a los dos | `herramientas/nivelar_carros.sh --copiar` | 23 archivos iguales en los dos | Repetir; si un vehículo no responde, queda pendiente |
| 3 | El nodo solo, 20 s, vehículo quieto | `ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; timeout -s INT 20 python3 /home/deepracer/tesis/imu_bmi160.py & sleep 8; timeout -s INT 8 ros2 topic hz /imu/data'"` (ruta fija del vehículo) | `sesgo del giroscopio ... z=` cerca de 0,47 (racey) o 0,65 (deepy), y `average rate` cerca de 50 | Sin sesgo: el vehículo se movió o el sensor no responde (correr `probar_imu.py identidad`) |
| 4 | IMU, rf2o y EKF, sin Nav2 | `ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; source /home/deepracer/nav_ws/install/setup.bash; setsid nohup ros2 launch /home/deepracer/tesis/nav2_hardware.launch.py imu:=true urdf:=/home/deepracer/tesis/deepracer_hardware.urdf params:=/home/deepracer/tesis/nav2_params_jazzy.yaml slam_params:=/home/deepracer/tesis/slam_toolbox.yaml behavior_trees:=/home/deepracer/tesis/behavior_trees > /tmp/imu_ekf.log 2>&1 &'"` (ruta fija del vehículo), esperar 20 s sin tocar el vehículo | Nada en pantalla; el registro en `/tmp/imu_ekf.log` del vehículo | Leer el registro: `ssh deepracer@192.168.0.104 "sudo -n tail -30 /tmp/imu_ekf.log"` |
| 5 | Frecuencias | `ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; timeout -s INT 8 ros2 topic hz /imu/data; timeout -s INT 8 ros2 topic hz /odom'"` | `imu/data` cerca de 50 Hz y `odom` cerca de 20 Hz | `odom` sin datos: el EKF no arrancó o no recibe; leer el registro |
| 6 | Deriva en 60 s, quieto | `ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; ros2 topic echo --once /odom --field pose.pose; sleep 60; ros2 topic echo --once /odom --field pose.pose'"` | Entre las dos lecturas, x e y cambian menos de 0,01 m y la orientación `z` menos de 0,009 (1°) | Si deriva el rumbo, el sesgo cambió: anotar la temperatura y repetir el paso 3 |
| 7 | Giro de 90° a la izquierda, a mano | La orden del paso 6, girando el vehículo sobre el suelo durante el `sleep 60` y dejándolo quieto antes de la segunda lectura | La orientación pasa de `z` cerca de 0 a cerca de +0,71 (`w` cerca de 0,71); x e y cambian menos de 0,2 m | `z` negativo: el signo está al revés (revisar `imu_joint` en la URDF) |
| 8 | Parar | `CARRO=192.168.0.104 bash herramientas/nav2_mapa_guardado.sh --parar` | `listo` | — |

Cierre: los pasos 3 a 7 pasan en los dos vehículos. Si en uno fallan y no se resuelve en 2 h, el
miércoles se corre sin IMU (`IMU=false`, el valor por defecto) y la IMU queda como trabajo
futuro.

### 2.4 · Red entre los pisos 3 y 4 (Jonny)

| | |
|---|---|
| Montaje | El de [`TOPOLOGIA_RED.md`](TOPOLOGIA_RED.md), pasos 1 a 8: un punto de acceso de 5 GHz por piso (canal 44 en el 3 y 36 en el 4, ancho de 40 MHz), los dos en puente, con DHCP apagado y unidos por cable al router, que sigue de respaldo en 2,4 GHz. *Este renglón decía «repetidores… canales 1, 6 y 11», el diseño en 2,4 GHz que se descartó el 5-oct al encontrar que los vehículos no podían transmitir en 5 GHz ([`S26_red_5ghz_regulatorio.md`](Evidencia/S26_red_5ghz_regulatorio.md))* |
| Prueba | El procedimiento de RF-15 de [`HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](HOJA_CAMPO_SEGUNDO_DEEPRACER.md), con un vehículo en cada piso, en los puntos de salida |
| Esperado | `CUMPLE` del medidor, y los dos vehículos responden al ping desde cualquier punto de su pasillo |
| Si falla | Acercar o mover los repetidores; si no hay cobertura en todo el pasillo, se eligen rutas dentro de la cobertura |
| Cierre | `CUMPLE` con los vehículos en pisos distintos |

> **Estado, 7-oct: montado a medias, cierre pendiente.** Los dos puntos de acceso están en puente
> sobre la misma subred y cada vehículo cuelga de uno distinto, que es la forma correcta. Se encontró
> y se resolvió **un bucle de capa 2** que duplicaba el 47 % del tráfico sin que el `ping` lo
> delatara, y con él fuera el enlace vehículo↔vehículo quedó en **3,75 ms de promedio con 0,51 de
> variación**, la mejor cifra del proyecto. Se corrigieron además los perfiles de red de los dos
> vehículos. **Falta**: separar los canales (los dos están en el 36), sacar los FiberHome de modo
> malla, los SSID por piso, las reservas de DHCP, el cable entre plantas, y **repetir RF-15 con un
> vehículo en cada piso**, que es lo único que cierra esta tarea. Lista completa en el §3.bis de
> [`TOPOLOGIA_RED.md`](TOPOLOGIA_RED.md); lo medido, en
> [`S26_bucle_capa2_y_red_dos_AP.md`](Evidencia/S26_bucle_capa2_y_red_dos_AP.md).
>
> Estado, 6-oct: **prerrequisito resuelto, cierre pendiente.** El 5-oct se encontró y arregló que a
> los dos vehículos les faltaba `regulatory.db` y no podían transmitir en 5 GHz; con eso, RF-15
> dio `CUMPLE` sobre 5 GHz (p95 de 11,12 ms). Esa medida se tomó con los dos vehículos **en la
> misma sala y el mismo punto de acceso**, así que sirve de línea base y no cierra esta tarea. Falta
> montar la topología y repetir RF-15 con cada vehículo en su piso, y probar el cable entre pisos
> (paso 7 de `TOPOLOGIA_RED.md`).

---

## 3. Miércoles 7

### 3.1 · Radio de giro de los dos vehículos

| | |
|---|---|
| Objetivo | Darle al planificador el radio de giro real (hoy supone 0,35 m) |
| Cómo | Con el control manual de la consola web del vehículo, dirección a tope y avance lento hasta cerrar un círculo; marcar el centro de las ruedas traseras en dos puntos opuestos y medir el diámetro. Se mide girando a la izquierda y a la derecha, en cada vehículo |
| Después | Poner el mayor de los radios en `minimum_turning_radius` de `nav2_params_jazzy.yaml` |
| Cierre | Cuatro medidas anotadas y el valor en el YAML |

### 3.2 · Misiones encadenadas en el piso 4, sin tocar el vehículo

El vehículo sale una vez de la salida medida y recorre tres tramos seguidos hacia el norte, sin media
vuelta. Entre un tramo y el siguiente nadie lo toca ni le vuelve a dar la pose inicial. Así se mide
lo mismo que el 2-oct (avance y llegada), y además si el error se acumula de una misión a la
siguiente.

| Tramo | De | A | Distancia |
|---|---|---|---|
| 1 | Salida frente a las escaleras (24,45, 1,21) | Salón 403 (17,22, 2,06) | 7,23 m |
| 2 | Llegada del tramo 1 | Salón 402 (9,31, 2,15) | 7,91 m |
| 3 | Llegada del tramo 2 | Salón 401 (6,20, 2,03) | 3,11 m |

| Paso | Qué | Comando o acción | Esperado | Cierre |
|---|---|---|---|---|
| 1 | Colocar el vehículo | Centro a 1,00 m de la pared sur y a 1,25 m de la pared este, mirando al norte | — | Vehículo en la salida |
| 2 | Arrancar Nav2 en racey, con IMU y margen de 0,5 m. No tocar el vehículo durante el arranque: la IMU mide su sesgo | `IMU=true MARGEN=0.5 CARRO=192.168.0.104 MAPA=/home/deepracer/tesis/piso4.yaml POSE_X=24.45 POSE_Y=1.21 POSE_YAW=3.1416 ESCALA=1.0 bash herramientas/nav2_mapa_guardado.sh   # ruta fija del vehiculo` | `CADENA LISTA`, con `imu/data` y `odom` publicando, y `registrando la carga de la tarjeta en /home/deepracer/carga_...csv` | Nav2 activo |
| 2b | Carga en vivo, en otra terminal, mientras dura la cadena | `ssh -t deepracer@192.168.0.104 htop` | La tarjeta, con todo cargado | Ver el porcentaje de cada núcleo y qué procesos lo ocupan |
| 3 | Comprobar las rutas sin mover el vehículo | `compute_path_to_pose` a los tres salones (§4.3 de [`GUIA_PISOS_3_Y_4.md`](GUIA_PISOS_3_Y_4.md)) | `SUCCEEDED` | Tres rutas |
| 4 | Tramo 1, con la pose inicial | `ssh deepracer@192.168.0.104 "sudo -n bash ~deepracer/tesis/correr_corrida_nav2.sh p4r_04 --salida 24.45 1.21 3.1416 --meta 17.22 2.06 3.1416 --mapa /home/deepracer/tesis/piso4.yaml --csv ~deepracer/campana_s26_racey.csv"` (ruta fija del vehículo) | Fila en el CSV | Marca en el piso junto al centro del vehículo; avance desde la salida y distancia a la pared oeste |
| 5 | Tramo 2, sin pose inicial | La misma orden con `p4r_05`, `--sin-pose-inicial` en lugar de `--salida` y `--meta 9.31 2.15 3.1416` | Fila en el CSV; AMCL no se reinicia | Marca nueva; avance medido de marca a marca y distancia a la pared oeste |
| 6 | Tramo 3, sin pose inicial | Igual, `p4r_06` y `--meta 6.20 2.03 3.1416` | Igual | Igual |
| 7 | Parar y copiar | `CARRO=192.168.0.104 bash herramientas/nav2_mapa_guardado.sh --parar`; después `scp deepracer@192.168.0.104:campana_s26_racey.csv ~/tesis_evidencia/`, `scp 'deepracer@192.168.0.104:carga_*.csv' ~/tesis_evidencia/` y `scp -r 'deepracer@192.168.0.104:campana_p4r_0*' ~/tesis_evidencia/` | El CSV de la campaña, el de la carga y las grabaciones en el portátil | `python3 herramientas/registrar_carga.py --resumen ~/tesis_evidencia/carga_<fecha>.csv` |
| 8 | La misma cadena con deepy | `CARRO=192.168.0.102`, `ESCALA=0.85`, ids `p4d_03` a `p4d_05` y `campana_s26_deepy.csv` | Igual | Igual |

Decisión del 7-oct: la cadena se corre directamente con IMU y margen de 0,5 m, una sola vez por
vehículo, que es como funcionará el sistema. La referencia sin IMU son las corridas del piso 4 del
2-oct (+3,3 % y −4,6 % de error de avance, llegadas a 0,57 m y 0,62 m con margen de 1,0 m;
[`S25_pisos34_campo.md`](Evidencia/S25_pisos34_campo.md)). Durante la cadena se mide cuánto se llena
la tarjeta con todo cargado: Nav2, AMCL, rf2o, IMU, filtro, puente y grabador. Se mira en vivo con
`htop` (paso 2b), y queda el registro que deja `nav2_mapa_guardado.sh` en
`/home/deepracer/carga_<fecha>_<hora>.csv` (ruta fija del vehículo): una fila cada 5 s con el procesador por proceso, la carga,
la memoria y la temperatura.

Un vehículo cada vez: si los dos están encendidos, solo uno corre la cadena (sin espacio de nombres
se mezclarían sus `/odom` e `/imu/data`).

Odometría: error de 10 % o menos en los tramos de 5 m o más (tramos 1 y 2), medido de marca a
marca. G-2 ya está alcanzada; esto la confirma en misiones encadenadas. Cierre de G-3: llegada a
0,5 m o menos. Se anota además si el error de llegada crece del tramo 1 al 3.

Punto de decisión a las 12:00. Se vuelve a `IMU=false` y al margen de 1,0 m en dos casos: si con
IMU y margen de 0,5 m las llegadas no mejoran respecto al 2-oct, o si la tarjeta no sostiene la
carga (Nav2 desactivado por el gestor, o el controlador fuera de su frecuencia). G-3 se reporta con su cifra.

### 3.3 · Media vuelta para ir a recoger a un usuario

Con el radio de giro real ya en el planificador (§3.1), el vehículo va del Salón 401, donde terminó
la cadena, a la salida frente a las escaleras. Es lo que pasa cuando el coordinador lo envía a
recoger a un usuario que está al sur. Para eso da media vuelta en el tramo ancho frente a los salones
401 y 402 (de 3,1 a 3,2 m).

| Paso | Qué | Comando o acción | Esperado | Cierre |
|---|---|---|---|---|
| 1 | Pedir la meta al sur, sin tocar el vehículo | La orden del tramo 2 con `p4r_10`, `--sin-pose-inicial` y `--meta 24.45 1.21 0.0` | Nav2 traza una maniobra con marcha atrás en el tramo ancho y vuelve hacia el sur | Una persona junto al vehículo durante la maniobra |
| 2 | Si no gira | Una meta intermedia en el tramo ancho mirando al sur: `--meta 8.00 1.70 0.0`, y después la de la escalera | El vehículo queda mirando al sur | — |
| 3 | Medir | Del centro del vehículo a la pared sur y a la pared este | Cerca de 1,00 m y 1,25 m | Número de maniobras, recuperaciones, tiempo y error de llegada anotados |

Si la media vuelta no sale ni con la meta intermedia, queda como limitación declarada de un
vehículo Ackermann en pasillos de 2,3 m. En ese caso G-5 se hace en la variante sin media vuelta
(§5.1).

### 3.4 · Una corrida en el piso 3 con deepy

Salida: frente a las escaleras y mirando al norte, con el centro del vehículo a 3,23 m de la pared sur
y a 1,26 m de la pared este. En el mapa es (22,10, 1,06). Meta: Salón 302 (9,31, 2,21). Es la primera
vez que un vehículo navega en el piso 3; sirve para comprobar el mapa antes de G-5.

---

## 4. Jueves 8

### 4.1 · El coordinador en los pisos 3 y 4 (hecho el 5-oct)

El equipo aprobó el 5-oct dos cambios en `coordinador.py`:

| Cambio | Qué hace | Por qué |
|---|---|---|
| Niveles 3 y 4 | Parámetros `robot_nivel_3` y `robot_nivel_4`, vacíos por defecto. La vuelta a la escalera al cancelar busca entre todos los niveles del robot. El agente admite `nivel:=3` y `nivel:=4` | Sin ellos el catálogo de los pisos 3 y 4 no tiene robot y la misión no se planifica. En simulación la asignación sigue siendo `{1: robot1, 2: robot2}` |
| Pose en el mapa (opción B) | Con `condicion:=hardware`, el rumbo de llegada, la verificación de llegada y el registro usan la pose que el agente de cada vehículo publica en `/robotN/estado`, en el marco del mapa. Una pose de más de 2 s no vale, y sin pose la llegada no se acepta | En el vehículo, `/robotN/odom` empieza en (0, 0) y no en la salida del mapa. Un vehículo en el Salón 403 queda en `/odom` a unos 10 m de las coordenadas del catálogo, y el coordinador habría rechazado la llegada. La TF del mapa es privada de cada vehículo, y por eso la pose llega por el agente |

Se descartó la opción A (arrancar la odometría en la salida del mapa): su deriva se acumula entre
misiones encadenadas, y con +3,3 % en 14,57 m ya son 0,48 m.

[`prueba_coordinador_vehiculo.py`](../Robot/aws-deepracer/coordinacion/test/prueba_coordinador_vehiculo.py)
corre el coordinador real con dos robots falsos cuya `/odom` empieza en su salida, como rf2o: 15 de
15. Prueba una misión del Salón 302 al 402 con relevo, otra encadenada sin reubicar, la cancelación
y el agente callado. Como control, el mismo escenario leyendo `/odom` rechaza la llegada. Con el
coordinador anterior fallan 13 de 14.

El coordinador juzga ahora la llegada con la pose de AMCL, que el 2-oct erró 0,42 y 0,43 m. La
llegada real se sigue midiendo con flexómetro, como en G-3.

Con `condicion:=hardware` el coordinador acepta la llegada a 0,5 m o menos, y Nav2 se detiene al
cruzar su margen: con 1,0 m, una llegada entre 0,5 y 1,0 m se rechaza y la misión falla. Las
misiones coordinadas (§4.3 y G-5) necesitan `MARGEN=0.5`, que es lo que se prueba el miércoles con
la IMU (§3.2).

### 4.2 · Coordinador, agentes e interfaz en los vehículos

Ensayado el 5-oct en la noche con deepy, sin Nav2
([`S26_integracion_imu_vehiculos.md`](Evidencia/S26_integracion_imu_vehiculos.md) §5): el portátil
recibe el estado de los agentes y pide misiones al coordinador por acción, y la interfaz conecta con
`rosbridge` en el portátil. Falta verlo desde el teléfono. Para el paso 3, `ros2 topic echo` necesita
el tipo: `ros2 topic echo --once /robot2/estado coordinacion_msgs/msg/EstadoRobot`; sin él abandona si
aún no descubrió el tópico. Cada mensaje de Jazzy imprime en el portátil `sequence size exceeds
remaining buffer`, sin perderse ninguno.

`rosbridge_server` no está instalado en los vehículos, y sin internet no se puede instalar allí. Va
en el portátil, que lo tiene (Humble). Según el estudio de S19, los mensajes de `coordinacion_msgs` son los mismos
en Humble y en Jazzy. Lo único distinto es la acción de Nav2, y esa la llama el coordinador, que
corre en racey. El paso 3 comprueba que el portátil reciba los mensajes de los vehículos.

| Paso | Qué | Comando | Esperado | Si falla |
|---|---|---|---|---|
| 1 | Coordinador y agente iguales al repositorio en los dos | `herramientas/nivelar_carros.sh` | `coordinacion_ws: los ... archivos del coordinador y del agente iguales al repositorio` en los dos | `herramientas/nivelar_carros.sh --copiar`, que copia y recompila |
| 2 | Nav2 con espacio de nombres en los dos | deepy: `NS=robot1 IMU=true MARGEN=0.5 CARRO=192.168.0.102 MAPA=/home/deepracer/tesis/piso3.yaml POSE_X=22.10 POSE_Y=1.06 POSE_YAW=3.1416 ESCALA=0.85 bash herramientas/nav2_mapa_guardado.sh` (ruta fija del vehículo). racey: `NS=robot2 IMU=true MARGEN=0.5 CARRO=192.168.0.104 MAPA=/home/deepracer/tesis/piso4.yaml POSE_X=24.45 POSE_Y=1.21 POSE_YAW=3.1416 ESCALA=1.0 bash herramientas/nav2_mapa_guardado.sh` (ruta fija del vehículo) | `CADENA LISTA` en los dos, con `imu/data` y `odom` publicando | El aviso en rojo del guion dice qué pieza falló |
| 3 | Un agente en cada vehículo | racey: `ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; source /home/deepracer/coordinacion_ws/install/setup.bash; setsid nohup ros2 run coordinacion agente --ros-args -r __ns:=/robot2 -p nivel:=4 > /tmp/agente.log 2>&1 &'"` (ruta fija del vehículo). deepy: lo mismo con `192.168.0.102`, `/robot1` y `nivel:=3`. En el portátil: `ros2 topic echo --once /robot2/estado --field pose` | La pose cerca de la salida del mapa, (24,45, 1,21) en racey y (22,10, 1,06) en deepy, con `frame_id: robot2/map`. Que llegue al portátil confirma que Humble recibe los mensajes de Jazzy | Pose en (0, 0): es `odom`, no el mapa; revisar AMCL. Nada en el portátil: probar el mismo `echo` dentro de racey; si allí llega, es la comunicación entre distribuciones, y `rosbridge` tendría que ir en racey (traer el paquete sin internet) |
| 4 | Coordinador en racey | `ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; source /home/deepracer/coordinacion_ws/install/setup.bash; mkdir -p /home/deepracer/registros; setsid nohup ros2 run coordinacion coordinador --ros-args -p condicion:=hardware -p ruta_puntos:=/home/deepracer/tesis/puntos_interes_pisos34.yaml -p robot_nivel_3:=robot1 -p robot_nivel_4:=robot2 -p ruta_registros:=/home/deepracer/registros > /tmp/coordinador.log 2>&1 &'"` (ruta fija del vehículo), y `ssh deepracer@192.168.0.104 "sudo -n grep -E 'condicion|listo' /tmp/coordinador.log"` | `condicion 'hardware': la llegada se acepta a 0.5 m o menos` y `Coordinador listo`, con la asignación de los niveles 3 y 4 | `GUARDIAN`: ya hay otro coordinador; pararlo con `sudo -n pkill -f "coordinacion[/]coordinador"` |
| 5 | `rosbridge` y la interfaz en el portátil | En una terminal, `ros2 launch rosbridge_server rosbridge_websocket_launch.xml send_action_goals_in_new_thread:=true`; en otra, `python3 -m http.server 8000 --directory interfaz_web` | `Rosbridge WebSocket server started on port 9090` | — |
| 6 | La interfaz desde el teléfono | El teléfono en la red de los vehículos, `http://192.168.0.105:8000/` | La lista de destinos de los pisos 3 y 4 y los dos robots | Sin destinos: el portátil no recibe `/coordinacion/puntos_interes`; volver al paso 3 |

### 4.3 · Una misión dentro de un solo piso

| | |
|---|---|
| Qué | Desde el teléfono, una misión en el piso 4: de las escaleras al Salón 402. El vehículo sale de donde quedó, sin reubicarlo: el coordinador primero lo manda al origen («El robot va hacia… Espere allí») |
| Esperado | racey llega; la interfaz muestra el avance y el final |
| Cierre | El registro de la misión, compuesto como dice la tabla de abajo |

Cada misión coordinada se graba en racey, que lleva el coordinador: así todas las marcas salen de un
mismo reloj, porque las tarjetas no tienen la hora sincronizada. `grabar_mision.sh` no sirve en el
vehículo, porque exige `/clock`.

| Paso | Comando | Esperado |
|---|---|---|
| 1. Antes de pedir la misión | `ssh -t deepracer@192.168.0.104 "sudo -n bash /home/deepracer/tesis/grabar_mision_vehiculo.sh P4_01"` (ruta fija del vehículo) | `== grabando /home/deepracer/mision_P4_01 (19 topicos)`. Si dice `ABORTA: nadie publica /coordinacion/estado_mision`, el coordinador no está vivo (§4.2, paso 4) |
| 2. Pedir la misión desde el teléfono y, al terminar, pulsar Enter en esa terminal | — | `== listo` |
| 3. Medir la llegada con flexómetro, desde la marca en el piso | — | La distancia al destino, anotada |
| 4. Copiar al portátil | `scp -r deepracer@192.168.0.104:mision_P4_01 ~/tesis_evidencia/` | La carpeta con el `.mcap` y `metadata.yaml` |
| 5. Hacerla legible en Humble | `python3 herramientas/adaptar_bag_jazzy.py ~/tesis_evidencia/mision_P4_01 -o ~/tesis_evidencia/mision_P4_01_humble` | La copia adaptada |
| 6. Componer el registro | `python3 herramientas/componer_registro.py ~/tesis_evidencia/mision_P4_01_humble --banco fisico --campana S26 --distro jazzy --catalogo Robot/aws-deepracer/deepracer_bringup/config/puntos_interes_pisos34.yaml --error-posicion-m <medida> --medido-por Santiago --salida Documentos/Evidencia/registros/P4_01.json` | `Registro escrito en ...` |

La cadena se probó el 5-oct con una grabación hecha en racey en un dominio aislado: el registro sale
con la condición B, los niveles 3 y 4 y la verdad de terreno de la cinta.

---

## 5. Viernes 9

### 5.1 · G-5: misión del piso 3 al piso 4 con relevo

Cada misión empieza con el robot del origen yendo, desde donde esté, hasta el salón de origen. Si va
hacia el norte, después tiene que dar media vuelta para guiar al usuario hacia las escaleras. Por eso
hay dos variantes, y la que se corre depende del resultado del miércoles (§3.3).

| Variante | Disposición inicial | Cuándo |
|---|---|---|
| A, con regreso | deepy en su escalera del piso 3, mirando al norte; racey en su escalera del piso 4, mirando al norte | Si la media vuelta funcionó el miércoles |
| B, sin media vuelta | deepy al norte del salón de origen, mirando al sur; racey en su escalera del piso 4, mirando al norte | Si la media vuelta no funcionó |

| | |
|---|---|
| Misión | Desde el teléfono: origen el Salón 302 y destino el Salón 402 |
| Esperado | deepy va al origen y guía hasta las escaleras del piso 3; la interfaz pide subir y confirmar la llegada al piso 4; racey guía desde las escaleras del piso 4 hasta el Salón 402 |
| Segunda misión | Sin tocar los vehículos, otra misión desde el teléfono; cada robot sale de donde quedó (§6.2 del acta). En la variante B, una que no pide media vuelta: en el piso 4, del Salón 402 al Salón 401. En la variante A, la que el equipo elija con lo medido el miércoles |
| Medidas | Llegada de cada vehículo con flexómetro, desde marcas en el piso; una grabación por misión con `grabar_mision_vehiculo.sh` en racey (§4.3) |
| Si falla | Anotar en qué fase falló y por qué; se repite el lunes 12 |
| Cierre | Los registros de las dos misiones compuestos como en la §4.3 y validados: G-5 alcanzada |

### 5.2 · Corte semanal (noche)

`ESTADO.md` al día, entregable de S26 en `.md` y `.tex`, y commit, con la batería completa antes del
push.

---

## 6. Lo que no se hace esta semana

| Qué | Por qué |
|---|---|
| Medias vueltas fuera de los tramos anchos | Con 2,3 m de pasillo no caben con la configuración actual (2-oct) |
| Regreso automático tras una misión completada | Opcional y sin prioridad (§6.2 del acta). Entre misiones el vehículo no vuelve a su escalera |
| Navegar hacia el borde de una escalera | Se suspendió el 30-sep; las metas de las escaleras quedan centradas en el pasillo |
| La campaña de RF-27 | Necesita G-5. Va en la semana 27, con cierre de datos el viernes 16 |
| La IMU en la simulación | Solo si sobra tiempo; si no, queda como limitación declarada |

## 7. Riesgos y salidas

| Si pasa | Qué se hace |
|---|---|
| La IMU o el EKF no funcionan en un vehículo el martes | Se sigue sin ella (`IMU=false`) y el martes pasa a preparar G-5 |
| El miércoles la IMU no permite bajar el margen de Nav2 a 0,5 m | El coordinador rechazaría las llegadas entre 0,5 y 1,0 m (§4.1): decidirlo con los resultados del miércoles, antes de la §4.3 |
| La red no cubre los dos pisos | Rutas dentro de la cobertura; el coordinador sigue en racey |
| La media vuelta no sale ni con la meta intermedia | G-5 en la variante B; el regreso automático queda como limitación declarada |
| G-5 no sale el viernes | Se repite el lunes 12. Si tampoco sale, el cronograma prevé bajar a un vehículo real y uno simulado (sección 9 de [`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md)) |
| Un vehículo se queda sin batería | Cargar las dos baterías (cómputo y tracción) cada noche; llevar el cargador a la sesión |
