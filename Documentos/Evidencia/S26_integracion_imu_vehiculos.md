# Integración de la IMU en los dos vehículos y ensayo del coordinador (5 de octubre, noche)

Primera sesión con la IMU dentro de la navegación de los vehículos: el nodo `imu_bmi160.py`, el
filtro EKF de `robot_localization` y rf2o, arrancados con `nav2_hardware.launch.py imu:=true`, sin
Nav2 y sin mover los vehículos salvo los giros a mano (§2.3 de [`PLAN_S26.md`](../historial/PLAN_S26.md)).
Después, un ensayo sin movimiento de la cadena del jueves: agente, coordinador y `rosbridge`
(§4.2 del plan). Las pruebas del sensor solo están en [`S26_pruebas_imu.md`](S26_pruebas_imu.md);
aquí se prueba el software que va encima.

Santiago corrió parte de las pruebas y colocó y giró los vehículos; Claude corrió el resto por SSH y
analizó las salidas. Las mediciones salen de
[`herramientas/medir_odom_imu.py`](../../herramientas/medir_odom_imu.py), escrita en la misma sesión.

## Resultado

La IMU queda aprobada para el rumbo en los dos vehículos. En un giro de 90° hecho a mano contra una
línea del piso, el filtro midió +90,17° en `amss-jgm9` (racey) y +88,38° en `amss-ez9n` (deepy). Con
el vehículo quieto, el rumbo del filtro se movió 0,3° o menos por minuto. rf2o solo, en las mismas
ventanas, derivó hasta 5,9° por minuto, y en el giro de deepy registró 19,1° de los 90°.

La posición no mejora con la IMU, y no se esperaba que mejorara: el filtro la toma de rf2o. Con el
vehículo quieto deriva de 0,8 a 5,0 cm por minuto en racey, del orden de rf2o solo (0,9 a 3,2 cm). En deepy, en cambio, la del
filtro se movió 12,5 cm en 90 s cuando la de rf2o se movió 2,1 cm. Queda como punto abierto (§6).

El portátil, en Humble, se comunica con un vehículo, en Jazzy, en los dos sentidos: recibe el estado
del agente completo y pide una misión al coordinador por acción, con su respuesta y sus etapas. La
interfaz web conecta con `rosbridge` en el portátil. Falta comprobarla desde el teléfono.

## 1. Configuración ajustada por la carga de la tarjeta

La configuración probada en el portátil llevaba la IMU a 50 Hz y el filtro a 20 Hz. Con ella, la
tarjeta de racey estaba a carga 5,2 sobre dos núcleos, la IMU no pasaba de 31,6 Hz y el filtro daba
avisos `Failed to meet update rate` de hasta 0,30 s. Se cambió:

| | Antes | Después | Por qué |
|---|---|---|---|
| Frecuencia de la IMU | 50 Hz | 25 Hz | El vehículo gira a unas decenas de grados por segundo; el filtro va a 15 Hz |
| Mensaje de la IMU | uno nuevo por publicación | se arma una vez y se reutiliza | Crear el mensaje y convertir las covarianzas era la mayor parte del costo |
| Frecuencia del filtro | 20 Hz | 15 Hz | El controlador de Nav2 va a 10 Hz y rf2o a unos 7,5 Hz |
| Diagnósticos del filtro | activados | desactivados | Un tópico que nadie lee |

| Proceso (porcentaje de un núcleo) | Antes | Después |
|---|---|---|
| Nodo de la IMU | 11,9 a 13,7 % | 6,2 a 6,5 % |
| Filtro | 5,3 a 7,1 % | 4,0 a 5,5 % |
| rf2o | 19,8 a 22,6 % | 20,4 a 22,6 % |

La tarjeta queda con un 65 a 72 % libre, sin Nav2. Los avisos del filtro aparecen solo en el
arranque, cuando ocho procesos arrancan a la vez, y cuando se lanza una orden `ros2` del CLI, que
ocupa un núcleo un par de segundos. Por eso las mediciones se hacen con un solo proceso de
`medir_odom_imu.py` y no con `ros2 topic echo` ni `ros2 topic hz`.

## 2. Arranque y sesgo del giroscopio

El nodo mide el sesgo al arrancar y repite la medida si el vehículo se mueve.

| Vehículo | Sesgo en z medido por el nodo | En las pruebas del sensor de la mañana |
|---|---|---|
| racey | 0,449; 0,459; 0,451 °/s | 0,47 °/s |
| deepy | 0,706; 0,709 °/s | 0,65 °/s |

En un arranque de deepy el nodo detectó movimiento, repitió la calibración y siguió: el
comportamiento previsto.

## 3. Deriva con el vehículo quieto

| Vehículo y modo | Ventana | Rumbo, filtro | Rumbo, rf2o solo | Posición, filtro | Posición, rf2o solo |
|---|---|---|---|---|---|
| racey, sin espacio de nombres | 60 s | −0,05° | — | 5,0 cm | — |
| racey, sin espacio de nombres | 60 s | −0,13° | +1,81° | 2,0 cm | 0,9 cm |
| racey, `/robot2` | 60 s | −0,25° | — | 0,8 cm | — |
| racey, `/robot2` | 60 s | −0,27° | +5,90° | 3,3 cm | 3,2 cm |
| deepy, `/robot1` | 60 s | −0,31° | −0,63° | 1,9 cm | 0,8 cm |
| deepy, `/robot1`, desde el arranque | 90 s | +0,13° | +5,20° | 12,5 cm | 2,1 cm |

El criterio de la §2.3 del plan pedía menos de 1° de rumbo y menos de 1 cm de posición en 60 s. El
rumbo lo cumple con margen. El de posición estaba mal puesto: la posición del filtro sale de rf2o, y
la IMU no la corrige. Cuando el vehículo se mueve, AMCL corrige la posición contra el mapa.

## 4. Giro de 90° a mano

| Prueba | Filtro | Estable después | rf2o solo | IMU integrada por la herramienta |
|---|---|---|---|---|
| racey, sin referencia (el giro real fue de unos 70°) | +71,3° | +71,1° → +71,3° en 100 s | +72,1°, y +16,5° de deriva después | −68,4° y −73,7° (integradas con la hora de llegada, ver §6) |
| racey, contra una línea del piso | **+90,17°** | +90,4° → +90,2° en 45 s | +83,6°, y bajando | −89,92° |
| deepy, contra una línea del piso | **+88,38°** | +88,0° → +88,3° en 40 s | +19,1° | −29,80° (con huecos, ver §6) |

El signo es el correcto en los dos: un giro a la izquierda sale positivo en `/odom` y negativo en el
eje z del sensor, que apunta hacia abajo. Con eso queda comprobada en el vehículo la orientación de
`imu_link` en la URDF.

## 5. Ensayo de la cadena del jueves, sin mover nada

Racey dejó de responder al `ping` a mitad del ensayo, y el coordinador se corrió en deepy. El código
del coordinador es el mismo en los dos. No había Nav2 ni el puente de motores.

| Comprobación | Resultado |
|---|---|
| El portátil recibe `/robot1/estado` del agente de deepy | 24 mensajes en 12 s, los 2 Hz del agente, con `robot_id: robot1` y `nivel: 3` |
| El coordinador arranca con los pisos 3 y 4 | `condicion 'hardware': la llegada se acepta a 0.5 m o menos` y `asignacion {1: 'robot1', 2: 'robot2', 3: 'robot1', 4: 'robot2'}` |
| El portátil pide una misión por acción (Salón 302 → Salón 301) | Aceptada; etapas recibida, «El robot va hacia Salón 302. Espere allí» y fallida, porque no había Nav2 (`no ofrece navigate_to_pose despues de 20 s`); el coordinador escribe su registro |
| `rosbridge` en el portátil | Arranca en el puerto 9090 y acepta conexiones desde la IP de la red (`curl` desde la terminal) |
| La página en el navegador de la aplicación | Con `http://192.168.0.105:8000/` no conecta: ese navegador no abre WebSockets hacia la IP de la red. Con `http://localhost:8000/?ws=localhost:9090` conecta y muestra el estado de la misión en vivo |

Cada mensaje que llega de Jazzy al portátil imprime `sequence size exceeds remaining buffer`. Los
mensajes llegan completos y con el contenido correcto, así que es un aviso de la capa DDS entre las
dos versiones; aparecerá también en la consola de `rosbridge`.

## 6. Incidencias

1. Se arrancaron las cadenas de los dos vehículos a la vez y sin espacio de nombres. `/odom`,
   `/odom_rf2o` e `/imu/data` van en la partición común, así que cada filtro recibió las dos IMU y
   los dos rf2o: frecuencias duplicadas y 1251 m de desplazamiento con el vehículo quieto. La medida
   se descartó. Regla: con los dos vehículos encendidos, la cadena se arranca con `namespace:=`.
2. El arranque de deepy se lanzó dos veces, desde dos terminales: dos IMU, dos rf2o y dos filtros
   bajo `/robot1`, con `/robot1/odom` a 30 Hz. Se descartó. Regla: antes de leer resultados, mirar
   que `/robotN/odom` salga cerca de 15 Hz y no de 30. En el ensayo del coordinador también quedaron
   dos agentes en deepy, por la misma causa.
3. Dos procesos de medición simultáneos en la misma tarjeta tardaron más de 15 s en descubrir los
   tópicos y abortaron. `medir_odom_imu.py` mide ahora filtro, rf2o e IMU en un solo proceso y
   espera hasta 30 s.
4. La herramienta integraba la IMU con la hora de llegada de cada mensaje: dos mediciones
   simultáneas del mismo giro diferían en 5°. Ahora integra con el sello del mensaje y avisa de los
   huecos de más de 0,2 s. En el giro de deepy perdió mensajes y dio −29,8°; el filtro, con los
   mismos datos, dio +88,4°.
5. `ros2 topic echo --once` abandona al instante con `Could not determine the type` si aún no
   descubrió el tópico. Hay que darle el tipo: `ros2 topic echo --once /robot1/estado
   coordinacion_msgs/msg/EstadoRobot`.
6. Después de la incidencia 1, el filtro de deepy marcaba un rumbo de +97,6° sin que el vehículo se
   hubiera girado tanto. Desde un arranque limpio no se reprodujo (+0,05° al empezar, ±0,2° en
   90 s). No está explicado.
7. Esa misma noche Jonny instaló el dominio regulatorio del WiFi en los dos vehículos y los
   reinició ([`S26_red_5ghz_regulatorio.md`](S26_red_5ghz_regulatorio.md)). No está confirmado si
   eso explica que racey no respondiera al empezar la sesión y que se cayera durante el ensayo.

## 7. Pendiente

1. Desde el teléfono: la lista de destinos de los pisos 3 y 4 y una misión pedida desde allí
   (§4.2 del plan, paso 6).
2. La posición del filtro en deepy (12,5 cm en 90 s quieto, frente a 2,1 cm de rf2o). La medida que
   decide es el avance en movimiento, con IMU y sin ella, contra el flexómetro (§3.2 del plan).
3. Revisar por qué racey dejó de responder: batería o red.
