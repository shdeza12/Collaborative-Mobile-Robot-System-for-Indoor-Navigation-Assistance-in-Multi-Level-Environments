# Guion de la sesión con los jurados

Objetivo: que los jurados vean funcionar el sistema con los dos vehículos, en una hora.

| | |
|---|---|
| Fecha | Por acordar. A 3 de noviembre los jurados no han respondido |
| Ensayo | Miércoles 4 de noviembre, sin esperar la fecha de la sesión (sección 3). Si la sesión cae después, ese día se repite el calentamiento |
| Sitio | Edificio Catalayud, pisos 3 y 4: deepy en el 3 y racey en el 4 |
| Horario | Sin clases en esos pisos. Las pruebas de campo del 16 y el 23 de octubre empezaron después de las 17:00 |
| Equipo | Los dos autores, uno por piso. Se reparten antes del ensayo |
| Estado | Escrito el 1 de noviembre, sin ensayar. Lo que salga del ensayo se corrige aquí |

## 1. Recorrido de la sesión

Cuatro misiones en este orden, sin reubicar los vehículos entre una y otra. Las referencias salen de los
[registros del 23 de octubre](Evidencia/campo_20261023/registros/); los tiempos del ensayo las reemplazan, porque
en la sesión los vehículos no salen de su escalera.

| Orden | Misión | Qué se ve | Usuario | Requisito | Referencia |
|---|---|---|---|---|---|
| 1 | Salón 403 → Salón 303, con relevo | racey guía hasta la escalera. Mientras el usuario baja, deepy va a la escalera del piso 3. El usuario confirma en el teléfono y deepy lo lleva al salón | Un autor | RF-07, RF-28 | Completada en 69,4 s, llegada a 0,483 m |
| 2 | Salón 301 → Salón 401, con relevo | El mismo relevo de subida | Un jurado | RF-07, RF-28 | Completada en 99,3 s, llegada a 0,079 m |
| 3 | Salón 403 → Salón 401 | Origen y destino en el mismo piso: un solo vehículo, sin relevo. Se graba en racey para verla después en RViz | Un jurado | RF-06 | Completada en 34,6 y 54,3 s, saliendo de la escalera |
| 4 | Salón 401 → Salón 303, cancelada en el segundo tramo | Se pulsa «Cancelar» con deepy en camino al salón. deepy vuelve a su escalera y la misión cierra como cancelada | Un jurado | RF-29 | Cierre a los 81,0 s, deepy a 0,337 m de su escalera |

Si sobra tiempo al final, se corre la misión que pida un jurado, entre los diez destinos del catálogo.

## 2. Reglas de la sesión

1. **Un solo teléfono con la página abierta durante las misiones: el del usuario de turno.** El coordinador no
   rechaza una segunda misión. Desde otro teléfono con la página abierta, «Iniciar guiado» lanza otra. En la prueba, con la
   primera esperando la confirmación, el vehículo recibió la meta nueva de inmediato, y la primera falló a los 120 s
   sin dejar registro. «Ya estoy en el piso N» también aparece en todos los teléfonos. Prueba en
   [`S30_segunda_mision_y_cancelacion.md`](Evidencia/S30_segunda_mision_y_cancelacion.md).
2. Si la página se recarga a mitad de misión, «Cancelar» queda desactivado e «Iniciar guiado» activo
   ([`app.js`](../interfaz_web/js/app.js), función `refrescarBotonIr`). «Iniciar guiado» no se pulsa. Para cancelar
   en ese caso se usa la orden de la sección 6.
3. Los jurados caminan detrás del usuario, a 2 m o más. Nadie se para delante del vehículo ni en el tramo estrecho
   del piso 4 (2,16 m de ancho). Las pruebas se hicieron con los pasillos despejados y solo con los dos autores
   (RNF-03), y la evasión de personas queda en los trabajos futuros del documento.
4. Cada autor se queda en su piso, junto a su vehículo durante la media vuelta.
5. El portátil va enchufado a la corriente: se apagó por batería dos veces el 16 de octubre
   ([`S27_campana_rf27.md`](Evidencia/S27_campana_rf27.md)).
6. Durante una misión no se corre nada de ROS en el portátil, ni `ros2 topic` ni `comprobar`: el límite es de cuatro
   procesos (cabecera de `herramientas/coordinador_portatil.sh`). No se usa `grabar`: el registro de cada misión es
   automático. La grabación de la misión 3 corre en racey, no en el portátil, y RViz se abre entre misiones, en otro
   dominio de ROS (sección 5).
7. Entre misiones los vehículos no se tocan, no se reubican y no se les da pose. Si hubo que levantar uno, se
   reinicia su cadena (sección 6).
8. Entre misiones se revisa la batería de los dos vehículos. Con menos de un tercio, se pasa al plan alternativo.
9. Del cierre del ensayo a la sesión no se cambia código, configuración ni mapas. El día de la sesión no se usa
   `nivelar_carros.sh --copiar`.

## 3. Ensayo

Objetivo: correr la sesión completa con cronómetro, para fijar la hora de llegada y probar lo que no se ha probado
en campo. Se hace con los dos autores, a la misma hora que la sesión si se puede.

Material: baterías de tarjeta y de tracción de los dos vehículos, cargadas la noche anterior; portátil con cargador
y extensión; los dos puntos de acceso; dos teléfonos; cronómetro.

### 3.1 Nivelar los vehículos (solo en el ensayo)

Primero se compara:

```bash
bash herramientas/nivelar_carros.sh
```

Desde el 23 de octubre solo deberían diferir comentarios y rutas de documentación. Para ver cada archivo que reporte:

```bash
git diff d25e45e HEAD -- <archivo>
```

Si es así, se copia a los dos:

```bash
bash herramientas/nivelar_carros.sh --copiar
```

- Esperado: `Los vehiculos estan nivelados con el repositorio.`
- Si un archivo tiene un cambio de comportamiento, no se copia: se revisa antes de seguir.
- Cierre: los dos vehículos corren lo mismo que correrán en la sesión.

### 3.2 Pruebas

Primero el arranque de la sección 4, con su calentamiento, y después:

| Prueba | Por qué se hace | Qué decide el resultado | Dónde está escrito |
|---|---|---|---|
| Arranque completo con cronómetro | No se ha cronometrado entero, y la sesión necesita una hora de llegada | La hora de llegada: lo medido más 30 min | [`PLAN_S27.md`](historial/PLAN_S27.md) §2.2 |
| Las cuatro misiones en orden, con cronómetro | Cada una corrió el 23 de octubre, pero no en esta secuencia. Ese día fallaron 3 de las 8 misiones no canceladas a propósito: una por la red, una por llegar a 0,52 m con tolerancia de 0,50 m y una por la media vuelta, ya corregida | Si una falla dos veces, se cambia por otra que complete y se corrige la sección 1 | [`S28_campo_pagina_cancelacion.md`](Evidencia/S28_campo_pagina_cancelacion.md) |
| En cada misión, cronómetro desde que el vehículo para hasta que la página muestra el final | El 23 de octubre la página tardó 46,00, 35,66 y 10,47 s en tres misiones, sin causa establecida. Del último movimiento a `COMPLETADA` pasan de 0,01 a 4,66 s | Con más de 5 s, se siguen corriendo misiones hasta que desaparezca, y eso fija cuántas misiones de calentamiento se hacen antes de la sesión | [`S28_campo_pagina_cancelacion.md`](Evidencia/S28_campo_pagina_cancelacion.md), «Retraso de la página frente al coordinador» |
| Grabar en racey la misión 3 con el nombre `vista_ensayo` y verla en RViz (órdenes de la sección 5) | Se probó con una grabación del 8 de octubre, no grabando con la cadena completa y el coordinador en el portátil, con la tarjeta entre el 68 y el 74 % | Si la misión se completa y la grabación se ve, en la sesión se graba otra. Si estorba a la misión o no se ve, en la sesión no se graba y se muestra `vista_ensayo`, o se quita RViz si tampoco se ve | [`S30_grabacion_en_rviz.md`](Evidencia/S30_grabacion_en_rviz.md) |
| Salón 403 → Salón 401 con los dos autores caminando detrás de racey, y otra con uno de pie a un lado del pasillo | En la campaña solo estuvieron en el pasillo los dos autores, y la sesión suma a los jurados | Si racey se detiene o la misión falla, los jurados ven las misiones desde un punto fijo, sin caminar detrás | [`REQUISITOS.md`](REQUISITOS.md), RNF-03 |
| Recargar la página a mitad de una misión con relevo y confirmar el piso desde ella | Por el código, el estado vuelve en 1 s y la confirmación sigue funcionando, pero no se ha visto en campo | Si la confirmación no funciona, la regla 2 pasa a «no recargar; si se pierde la conexión, cancelar desde el portátil» | [`app.js`](../interfaz_web/js/app.js) |
| Cancelar desde el portátil una misión en curso (orden de la sección 6) | Es la salida con la página recargada. Se probó con robots falsos y en el contenedor, no con los vehículos | Si el vehículo no vuelve a su escalera, se quita de la sección 6 y la salida es parar su cadena | [`S30_segunda_mision_y_cancelacion.md`](Evidencia/S30_segunda_mision_y_cancelacion.md) |
| Generar la tarjeta y entrar a la página con un Android y un iPhone, si hay | La tarjeta no tiene uso registrado en campo, y la red no tiene internet: un teléfono puede preferir sus datos móviles | Si falla, el usuario de turno usa el teléfono del equipo | [`tarjeta_jurado.py`](../herramientas/tarjeta_jurado.py) |
| Anotar la batería de los dos vehículos al arrancar y al terminar | No hay medida de autonomía, y la sesión los tiene encendidos cerca de dos horas | Si baja de un tercio antes del final, se arranca más tarde o se lleva repuesto | [`PLAN_S27.md`](historial/PLAN_S27.md) §1.4 |
| Abrir en el portátil, sin internet, los videos del plan alternativo | Es la salida si el sistema no arranca | Si no abren, se resuelve antes de la sesión | Sección 6 |
| Pasar a la simulación: parar lo de los vehículos, levantar los dos pisos en Gazebo y correr Salón 403 → Salón 303, con cronómetro | Es la salida en vivo si fallan los vehículos o la red. Corrió el 2 de noviembre en casa, no en el sitio ni después de una cadena de los vehículos | Si tarda más de 10 min, o si los vehículos interfieren aunque estén parados, el plan alternativo queda solo en los videos | [`S30_simulacion_catalayud.md`](Evidencia/S30_simulacion_catalayud.md) |

Para la tarjeta, con el portátil en `DEEPRACER` (pide la clave y escribe `Documentos/acceso_jurado.pdf`, que git ignora):

```bash
python3 herramientas/tarjeta_jurado.py --ip 192.168.0.105
```

### 3.3 Cierre del ensayo

- Las cuatro misiones corrieron seguidas, con sus tiempos anotados, y cada fila de la tabla tiene resultado.
- `vista_ensayo` queda en `~/tesis_evidencia/`, como respaldo de la grabación de la sesión.
- Lo que cambie se corrige en esta guía el mismo día, y los registros se guardan como en la sección 7.
- Si el recorrido no se completa, se repite el ensayo antes de la sesión. Si la fecha no da, se mueve la sesión.

## 4. Arranque

Igual en el ensayo y en la sesión. Todo se corre en el portátil, desde la raíz del repositorio.

1. Confirmar el sitio. deepy en la salida del piso 3 y racey en la salida del piso 4, los dos mirando al norte.
   Los mapas son los de esos pisos. Cierre: los dos autores lo confirman antes de lanzar nada.

2. Comprobar la red. Los dos puntos de acceso encendidos, sin modo malla ([`TOPOLOGIA_RED.md`](TOPOLOGIA_RED.md)), y el
   portátil en `DEEPRACER` con la IP `192.168.0.105`.

   ```bash
   ping -c 3 192.168.0.102
   ```

   ```bash
   ping -c 3 192.168.0.104
   ```

   - Esperado: 0 % de pérdida en los dos.
   - Si falla: esperar 3 min sin tocar nada (el 23 de octubre racey estuvo unos dos minutos sin responder y volvió
     solo). Si sigue, revisar el punto de acceso de ese piso.

3. Comprobar que los vehículos están nivelados.

   ```bash
   bash herramientas/nivelar_carros.sh
   ```

   - Esperado: `Los vehiculos estan nivelados con el repositorio.`
   - Si reporta diferencias el día de la sesión: no se copia nada, se sigue con lo ensayado y se anota.

4. Lanzar la cadena de cada vehículo, una terminal por vehículo. Los vehículos no se tocan mientras arranca: el nodo de la
   IMU mide el sesgo del giroscopio.

   ```bash
   NS=robot1 IMU=true MARGEN=0.5 CARRO=192.168.0.102 MAPA=/home/deepracer/tesis/piso3.yaml POSE_X=22.10 POSE_Y=1.06 POSE_YAW=3.1416 bash herramientas/nav2_mapa_guardado.sh  # ruta fija del vehículo
   ```

   ```bash
   NS=robot2 IMU=true MARGEN=0.5 CARRO=192.168.0.104 MAPA=/home/deepracer/tesis/piso4.yaml POSE_X=24.45 POSE_Y=1.21 POSE_YAW=3.1416 bash herramientas/nav2_mapa_guardado.sh  # ruta fija del vehículo
   ```

   - Esperado: `CADENA LISTA` en 4 a 4,5 min, con seis nodos `active`.
   - Si el LiDAR no publica: `sudo systemctl restart deepracer-core` en ese vehículo, esperar 30 s y repetir su orden.

5. Lanzar el agente en cada vehículo.

   ```bash
   ssh deepracer@192.168.0.102 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; source /home/deepracer/coordinacion_ws/install/setup.bash; export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; source /tmp/nav2_campo/pares.sh; setsid nohup ros2 run coordinacion agente --ros-args -r __ns:=/robot1 -p nivel:=3 -p topico_scan:=/rplidar_ros/scan > /tmp/agente.log 2>&1 &'"  # ruta fija del vehículo
   ```

   ```bash
   ssh deepracer@192.168.0.104 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash; source /home/deepracer/coordinacion_ws/install/setup.bash; export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; source /tmp/nav2_campo/pares.sh; setsid nohup ros2 run coordinacion agente --ros-args -r __ns:=/robot2 -p nivel:=4 -p topico_scan:=/rplidar_ros/scan > /tmp/agente.log 2>&1 &'"  # ruta fija del vehículo
   ```

   Para comprobarlo:

   ```bash
   ssh deepracer@192.168.0.102 "sudo -n tail -5 /tmp/agente.log"
   ```

   ```bash
   ssh deepracer@192.168.0.104 "sudo -n tail -5 /tmp/agente.log"
   ```

   - Esperado: `publicando estado a 2.0 Hz` y el mapa de la media vuelta cargado.
   - Si falla: `/tmp/nav2_campo/pares.sh` del vehículo tiene que tener la IP del portátil.

6. Arrancar el coordinador.

   ```bash
   bash herramientas/coordinador_portatil.sh arrancar
   ```

   - Esperado: `la llegada se acepta a 0.5 m o menos`, `coordinador listo` y la asignación con `3: 'robot1'` y
     `4: 'robot2'`.
   - Si falla: `bash herramientas/coordinador_portatil.sh registro`.

7. Comprobar lo que el portátil ve de los vehículos (hasta 40 s, antes de la interfaz).

   ```bash
   bash herramientas/coordinador_portatil.sh comprobar
   ```

   - Esperado: `el coordinador ve los dos robots`.
   - Si falla: la cadena o el agente de ese vehículo no cruzan la red. Volver a sus pasos 4 y 5.

8. Arrancar la interfaz.

   ```bash
   bash herramientas/coordinador_portatil.sh interfaz
   ```

   - Esperado: `rosbridge en el puerto 9090` y `la pagina en http://192.168.0.105:8000/`.
   - Si falla: `/tmp/rosbridge.log`.

9. Abrir la página en el teléfono, en la red `DEEPRACER`: `http://192.168.0.105:8000/`.

   - Esperado: `conectado` y los destinos de los pisos 3 y 4.
   - Sin destinos: el portátil no recibe `/coordinacion/puntos_interes`. Repetir los pasos 6 a 8.

10. Correr el calentamiento: Salón 403 → Salón 303 y Salón 301 → Salón 401, con los dos autores y cronómetro. En la
    sesión termina 15 min antes de la hora.

    - Esperado: las dos se completan y la página muestra el final a tiempo.
    - Si falla: sección 6, sin prisa, que todavía no hay jurados.

Cierre del arranque: dos misiones completas y las baterías por encima de un tercio. racey queda en el Salón 401 y
deepy en su escalera.

## 5. La hora con los jurados

Lo que se les dice va entre comillas y usa «agente», la palabra del documento.

| Minuto | Qué pasa | Qué se dice |
|---|---|---|
| 0–5 | Recibirlos en el piso 4, frente al Salón 403 | «Son dos agentes, uno por piso, y un servidor central en el portátil que les reparte los tramos. El usuario solo usa la página del teléfono. Por favor caminen detrás del usuario y no se paren delante del agente: las pruebas se hicieron con el pasillo despejado.» |
| 5–15 | Misión 1, con un autor de usuario. Todos bajan con él | «Mientras el usuario baja, el agente del piso 3 ya va hacia la escalera. Su tramo no arranca hasta que el usuario confirma en el teléfono.» |
| 15–25 | Misión 2, con un jurado de usuario y el teléfono del equipo. Todos suben con él | «El mismo relevo de subida. La página pregunta según el sentido.» |
| 25–32 | Misión 3, grabándola en racey (orden abajo) | «Origen y destino en el mismo piso: un solo agente y ningún relevo, con la misma página.» |
| 32–42 | Misión 4. El autor del piso 3 dice cuándo pulsar «Cancelar», con deepy a unos metros de su escalera | «El agente vuelve a su escalera antes de que la misión cierre, y queda listo para la siguiente.» |
| 42–50 | En el portátil, la misión 3 en RViz, el registro de la última misión y los clips, si los piden (órdenes abajo) | «Esto es lo que vio el agente en la misión 3: el láser en rojo sobre el mapa, el plan en verde y su pose estimada en azul. Se grabó en el agente y se trajo al portátil.» «Cada misión deja además un registro automático con sus tiempos, la llegada y el relevo.» |
| 50–60 | Preguntas. Si sobra tiempo, la misión que pida un jurado | |

Si un jurado quiere usar su propio teléfono, escanea la tarjeta y se cierra la página en el teléfono del equipo.

La misión 3 en RViz. En el ensayo la carpeta se llama `vista_ensayo`, como en estas órdenes; en la sesión se cambia por
`vista_sesion` en las tres, porque el grabador no sobrescribe una carpeta que ya existe.

Antes de pedir la misión, desde el portátil. Graba 120 s y termina sola:

```bash
ssh -t deepracer@192.168.0.104 "sudo -n bash -c 'export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; [ -f /etc/deepracer-tesis/particion.xml ] && export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash && source /home/deepracer/nav_ws/install/setup.bash && cd ~deepracer && timeout -s INT 120 ros2 bag record -s mcap -o vista_ensayo /rplidar_ros/scan /robot2/odom /tf /tf_static /robot2/plan /robot2/map /robot2/amcl_pose; chown -R deepracer:deepracer ~deepracer/vista_ensayo'"  # ruta fija del vehículo
```

- Esperado: una línea `Subscribed to topic` por cada tópico. Se pide la misión al verlas.
- Si falla: la misión se corre igual, sin grabar, y después se muestra `vista_ensayo`.

Después de la misión 4, sin ninguna misión en curso:

```bash
scp -r deepracer@192.168.0.104:vista_ensayo ~/tesis_evidencia/
```

```bash
ROBOT=robot2 herramientas/ver_bag_rviz.sh ~/tesis_evidencia/vista_ensayo
```

- Esperado: `Global Status: Ok`, el pasillo del piso 4 completo y el láser sobre sus paredes. La grabación corre a
  velocidad real, así que la misión se ve después de la espera inicial. RViz se cierra con su ventana.
- Se reproduce en el dominio 77, de modo que no se cruza con los vehículos aunque sigan encendidos: la grabación no lleva
  `cmd_vel`, y el dominio aísla el resto.
- Si falla: se sigue con el registro de la misión, sin diagnosticar delante de los jurados.

El registro de la última misión, que solo lee un archivo y no ocupa un proceso ROS:

```bash
python3 -c "import json,glob,os; f=max(glob.glob(os.path.expanduser('~/tesis_evidencia/registros/*.json')),key=os.path.getmtime); j=json.load(open(f)); s=j['solicitud']; m=j['metricas']; print(s['origen_id'],'->',s['destino_id'],'| exito:',m['exito'],'| total:',round(j['cierre']['t']-s['t_solicitud'],1),'s | llegada a',m['error_llegada_m'],'m, tolerancia',m['tolerancia_llegada_m'],'m | relevo:',m['hueco_relevo_s'],'s')"
```

Preguntas que pueden salir de lo que ven:

| Pregunta | Respuesta |
|---|---|
| ¿Qué pasa si dos personas piden el servicio a la vez? | El sistema atiende una misión a la vez, sin cola ni noción de agente ocupado. Una segunda solicitud no está controlada, y se plantea en los trabajos futuros |
| ¿Y si hay gente en el pasillo? | Las pruebas se hicieron con los pasillos despejados. Esquivar personas en movimiento es trabajo futuro y el paso previo a operar en horario de clases |
| ¿Por qué hay que confirmar el cambio de piso? | El sistema no observa al usuario en la escalera. Avisa a los 60 s, y sin confirmación la misión falla a los 120 s |
| ¿La simulación está al nivel de los agentes físicos? | En funciones, sí: el mismo coordinador corre en Gazebo en los pisos 3 y 4, con los mismos mapas y destinos, la misma página, y la media vuelta y la llegada de los agentes. Lo físico no: la odometría real, la banda muerta, el radio de giro y la red. La campaña de 30 misiones se hizo en el edificio Gregorio |
| ¿Se puede ver en vivo lo que ve el agente? | Con los agentes físicos, no. El láser y las transformadas se quedan dentro de cada agente para no saturar la red, y el portátil corre otra versión de ROS 2, que no decodifica el láser del agente. Por eso se graba en el agente y se reproduce después. En simulación sí se ve en vivo |
| ¿Por qué tardó la página? (solo si pasa) | Se dice lo medido: el 23 de octubre la página mostró el final entre 10 y 46 s tarde en tres misiones, mientras el agente y el coordinador terminaban a tiempo. La causa no se estableció |
| ¿Por qué falló esa misión? (solo si pasa) | Se lee el motivo que muestra la página y se repite la misión |

## 6. Contingencia

Delante de los jurados no se diagnostica más de 5 min. Una falla se explica con el motivo que da la página, y se
repite la misión o se pasa al plan alternativo.

| Señal | Qué hacer | Si no se resuelve |
|---|---|---|
| La misión termina sin éxito | Leer el motivo y pedir la misma misión: el vehículo sale de donde quedó | Dos fallos seguidos por la misma causa: plan alternativo |
| Vehículo atascado o cerca del vano de la escalera | Cancelar desde la página: vuelve a su escalera | La fila siguiente |
| El vehículo va a tocar algo o a alguien | Quien esté a su lado lo levanta del suelo. Desde el portátil se le quita la tracción con la orden de abajo | Su pose ya no vale. Parar su cadena y su agente (sección 7), llevarlo a la salida, repetir sus pasos 4 y 5, y después los pasos 6 a 8 |
| La media vuelta no completa | Dejar que Nav2 lo intente. Si aborta, la misión falla y se repite | Plan alternativo |
| La página sigue en «Sígueme» con el vehículo parado | No recargar. Comprobar en el portátil con `bash herramientas/coordinador_portatil.sh registro`, que debe decir `Mision completada` | Esperar hasta 60 s (el máximo medido es de 46 s) y recargar |
| `sin conexion, reintentando...` | Esperar 20 s y recargar | `bash herramientas/coordinador_portatil.sh interfaz` |
| Hay que cancelar con la página recargada | La orden de abajo | Parar la cadena de ese vehículo |
| `CADENA LISTA` no llega | `sudo systemctl restart deepracer-core` en ese vehículo, esperar 30 s y repetir su paso 4 | Plan alternativo |
| Un vehículo no responde | Esperar 3 min sin tocar nada | Plan alternativo |
| Batería por debajo de un tercio | Parar ese vehículo | Plan alternativo |

Cancelar desde el portátil, sin el teléfono que lanzó la misión:

```bash
docker exec coordinador bash -c "source /opt/ros/jazzy/setup.bash && source /coordinacion_ws/install/setup.bash && ros2 service call /coordinacion/guiar_usuario/_action/cancel_goal action_msgs/srv/CancelGoal '{}'"
```

- Esperado: `return_code=0` y un elemento en `goals_canceling`. El vehículo vuelve a su escalera y la misión cierra
  como cancelada.

Quitarle la tracción a deepy o a racey:

```bash
ssh deepracer@192.168.0.102 "sudo -n pkill -9 cmdvel_to_serv"
```

```bash
ssh deepracer@192.168.0.104 "sudo -n pkill -9 cmdvel_to_serv"
```

`arrancar` borra el contenedor anterior: antes de repetirlo se guarda el registro del coordinador (sección 7, paso 1).

### Plan alternativo

Se pasa a él si el sistema no está listo 15 min después de la hora, con dos fallos seguidos por la misma causa, o por
batería.

1. Se les dice a los jurados qué falló y se les ofrece otra fecha para verlo con los vehículos.
2. Se corre en vivo el recorrido de la sección 1 en simulación, en los mismos pisos y con la misma página. Primero se
   para el coordinador y lo de los vehículos (sección 7, pasos 1 y 2), porque usan los mismos nombres `/robot1` y `/robot2`.
   Después se siguen las órdenes de la sección 8 de [`GUIA_PISOS_3_Y_4.md`](GUIA_PISOS_3_Y_4.md), cerca de 5 min. Se les
   aclara que es una comprobación en simulación.
3. Se muestran en el portátil los videos, que no dependen de internet ni están en el repositorio:
   `VIDEOS/editado/campana_dos_vehiculos_v2.mp4` (16 de octubre) y `VIDEOS/editado/pagina_y_cancelacion_23oct.mp4`
   (23 de octubre).
4. Se muestran los registros de [`campo_20261016/registros/`](Evidencia/campo_20261016/registros/) con la orden de la
   sección 5.

Cierre: los jurados vieron el sistema en simulación o las grabaciones, y queda acordada la fecha nueva, o la decisión de
no repetirla.

## 7. Cierre de la sesión y del ensayo

1. Guardar el registro del coordinador antes de pararlo, porque `parar` borra el contenedor (se cambia `AAAAMMDD`
   por la fecha):

   ```bash
   docker logs coordinador > ~/tesis_evidencia/coordinador_AAAAMMDD.log 2>&1
   ```

2. Parar todo:

   ```bash
   bash herramientas/coordinador_portatil.sh parar
   ```

   ```bash
   NS=robot1 CARRO=192.168.0.102 bash herramientas/nav2_mapa_guardado.sh --parar
   ```

   ```bash
   NS=robot2 CARRO=192.168.0.104 bash herramientas/nav2_mapa_guardado.sh --parar
   ```

   ```bash
   ssh deepracer@192.168.0.102 "sudo -n pkill -f '[c]oordinacion/agente'"
   ```

   ```bash
   ssh deepracer@192.168.0.104 "sudo -n pkill -f '[c]oordinacion/agente'"
   ```

3. Borrar de racey la grabación ya copiada, para que los dos vehículos queden iguales:

   ```bash
   ssh deepracer@192.168.0.104 "rm -rf vista_ensayo vista_sesion"
   ```

4. Comparar los dos vehículos, solo en el ensayo, que es cuando se copió algo:

   ```bash
   bash herramientas/nivelar_carros.sh
   ```

5. Copiar los registros de ese día de `~/tesis_evidencia/registros/` a `Documentos/Evidencia/campo_AAAAMMDD/registros/`,
   junto con el registro del coordinador.
6. Escribir la evidencia con su fila en [`Evidencia/README.md`](Evidencia/README.md): misiones, tiempos, retraso de la
   página e incidencias.

Cierre: los dos vehículos apagados y con las baterías a cargar, y la evidencia escrita el mismo día.
