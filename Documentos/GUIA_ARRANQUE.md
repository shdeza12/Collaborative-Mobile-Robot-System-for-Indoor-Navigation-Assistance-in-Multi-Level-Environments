# Guía de arranque — correr el sistema completo, de cero a una misión medida

**Escrita el 2026-09-14**, en la semana de congelamiento de código (S23). Es la secuencia
**única** para levantar el sistema tal como quedó, lanzar una misión de cualquiera de las tres
clases que hoy soporta y dejar la evidencia compuesta. Está pensada para que alguien que no
estuvo en el desarrollo pueda replicarlo leyendo un solo documento.

## Por qué existe, y qué NO sustituye

Hasta hoy esta secuencia vivía repartida en tres sitios y ninguno la tenía entera:

| documento | qué cubre | por qué no basta |
|---|---|---|
| [`README.md`](../README.md) | instalación, compilación, un robot con SLAM o Nav2 | llega hasta «dos robots levantados». No sabe qué es una misión |
| [`RUNBOOK_CAMPANA.md`](RUNBOOK_CAMPANA.md) | la corrida de campaña OE4, paso a paso | escrito el 2026-08-30, **antes de RF-28 y RF-29**. Es una lista de verificación de campaña, no una guía de arranque |
| [`GUIA_EJECUCION.md`](GUIA_EJECUCION.md) | levantar y depurar piezas sueltas | es de diagnóstico. Explica cómo mirar dentro, no en qué orden arrancar |

**Los tres siguen vigentes y ninguno se toca.** Esta guía los encadena. Donde una cifra o una
regla ya vive en otro documento, aquí se cita en vez de copiarse: la lección de la pose de spawn
—que llegó a estar en tres sitios y se actualizaron dos— vale igual para la prosa.

**Lo que esta guía NO cubre:** el banco físico. Todo lo de abajo es simulación. La campaña de
hardware (RF-27) tiene otras condiciones iniciales y otra verdad de terreno, y su runbook no está
escrito (§9.2 del runbook de campaña).

## Antes de empezar

Se da por hecho que la instalación del [`README.md`](../README.md) está hecha: repositorio
clonado, workspace en `~/deepracer_sim_ws` con los paquetes enlazados, `colcon build` sin errores
y `herramientas/verificar_instalacion.sh` en verde. Si algo de eso falta, esta guía no es el sitio.

### De dónde se ejecuta cada comando

Hay **dos** sitios y solo dos:

| comandos que empiezan por… | se ejecutan desde |
|---|---|
| `herramientas/…`, `python3 herramientas/…`, `python3 -m http.server` | la **raíz del clon** |
| `ros2 …` a secas | `~/deepracer_sim_ws`, con `source install/setup.bash` hecho |

Para confirmar que una terminal está en la raíz del clon antes del primer comando:

```bash
ls herramientas/robot.sh
```

**Esperado:** imprime `herramientas/robot.sh`. **Si dice `No such file or directory`**, no estás
en el repositorio: `cd` a tu clon y repite. Ese mensaje es el diagnóstico correcto y no hay que
buscar más lejos.

> **Por qué no se define una variable con la ruta del clon.** Del 22 al 30 de agosto este
> proyecto pedía exactamente eso, y la primera orden del runbook murió con
> `bash: herramientas/robot.sh: No such file or directory` porque la variable no estaba definida
> y `cd ""` **no es un error para bash**: devuelve 0 sin moverse. El fallo salió un eslabón más
> tarde, acusando a un script que estaba perfectamente.

### Ninguna terminal exporta `ROS_DOMAIN_ID`

Los dos robots viven en el **dominio 0** desde el 2026-08-30, y exportar algo es lo que rompe. Lo
que separa a las dos pilas no es el dominio sino los nombres: namespace por robot, prefijo en cada
marco TF —incluido `map`— y puerto de `gzserver` propio. Hay bitácoras anteriores a esa fecha que
dan por vigente el reparto en dominios 0 y 2; ya no lo es, y el motivo está en el
[`README.md`](../README.md#dos-robots): un nodo de ROS 2 vive en **un** dominio, así que el
coordinador nunca alcanzaba a los dos a la vez y el relevo entre pisos no se podía ejecutar.

---

## 1. Las dos pilas

Se levantan **siempre las dos**, aunque la misión no salga del piso 1. No es celo: la condición A
(intra-nivel) es el control contra el que se compara la B (entre pisos), y si A corriera con un
`gzserver` y B con dos, la diferencia de tiempos entre condiciones llevaría dentro la diferencia
de carga de la máquina y no habría forma de separarlas después (§6.2 del
[protocolo](PROTOCOLO_EXPERIMENTAL.md)).

Cada robot tiene **su propio mundo y su propio mapa**, que van juntos: `robot1` navega
`mundo_definitivo_piso1.world` contra `mundo_definitivo_piso1.yaml`, y `robot2` los del piso 2.
Localizar contra el mapa del otro nivel **converge sin dar error** contra la geometría equivocada,
así que el par no se mezcla nunca. Los tres datos —pose, mundo y mapa— salen de una sola tabla,
`POSE_INICIAL` en `deepracer_raiz_repo.py`.

**Terminal 1**, desde la raíz del clon:

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**Terminal 2**, desde la raíz del clon:

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**Esperado:** cada una anuncia su puerto libre y arranca Gazebo y Nav2. Tardan 28–35 s.

**Si falla:**
- Si `parar` avisa de procesos «que no lanzó `robot.sh`», mátalos a mano con `kill -9` y repite.
  No los toca a propósito, porque no sabe de quién son.
- Si el puerto sigue ocupado tras 10 s, el script sale con error y **no hay que seguir adelante**.

> **Un `gzserver` nuevo por misión, sin excepción** (§6.4 del protocolo). Encadenar misiones sobre
> la misma simulación ya costó una corrida: `S20_piloto_02` arrancó a (−17,097; 10,452) por reusar
> el `gzserver` anterior y salió FALLIDA a 0,573 m.

---

## 2. La compuerta

Nada se mide sobre una pila que no está lista. **Terminal 3**, desde la raíz del clon:

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/esperar_nav2.sh robot1 && herramientas/esperar_nav2.sh robot2
```

**Esperado:** `LISTA. Nav2, controladores, parametros y condicion inicial.` dos veces, y código de
salida 0. Comprueba los siete nodos de ciclo de vida en `active` y los siete controladores.

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/verificar_condicion_inicial.py robot1 robot2
```

**Esperado:** los dos dentro de **0,15 m**.

> El §3 del [runbook](RUNBOOK_CAMPANA.md) lo invoca dos veces, una por robot, y también vale. Aquí
> van juntos porque la herramienta ya acepta varios y **su código de salida es el AND de todos**:
> el criterio 1 del §8 pide los dos dentro, así que un solo robot fuera basta para descartar la
> corrida. Encadenado con `&&`, el segundo ni se ejecutaría si el primero falla y no se vería
> cuánto se salía.

**Si falla:** relanzar **solo** la pila que se sale, no las dos. No se corrige a mano y no se sigue
igualmente. El detalle de los dos modos de fallo de Nav2 —el gestor de ciclo de vida bloqueado
frente a la carrera entre los dos `lifecycle_manager`— está en el §3 del
[runbook](RUNBOOK_CAMPANA.md), y `esperar_nav2.sh` los distingue solo desde el 2026-09-10.

> **Estos dos comandos existen porque las comprobaciones se venían haciendo a ojo y un día no se
> hicieron.** El bag `S20_piloto_01` tiene **cero** mensajes en `cmd_vel`, `amcl_pose` y `plan`: se
> grabó una misión entera contra una pila muerta y no se notó hasta abrirlo. Y las pilas derivan
> ~17 mm/min en reposo, así que una simulación que lleva rato encendida arranca contaminada —la
> corrida del 30-ago empezó con 0,535 m y 0,745 m de error hasta que se relanzaron—. Medir un error
> de llegada sobre una pose contaminada mide el tiempo que el simulador llevaba encendido, no el
> sistema.

---

## 3. El coordinador

**Terminal 4**, desde el workspace —el comando hace el `cd`:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S23
```

**Esperado:** `Coordinador listo. 31 puntos, asignacion {...}`. **Si dice un número distinto de
31**, el catálogo no es el mismo con el que se sortearon las misiones y hay que parar.

**`use_sim_time:=true` no es opcional.** El §3 del [protocolo](PROTOCOLO_EXPERIMENTAL.md) define
`t_solicitud` sobre el reloj de simulación, que es el mismo que sella el bag. Sin él el
coordinador marcaría con reloj de pared, y con RTF ≥ 0,99 las dos formas difieren hasta un 1 %:
sobre `t_respuesta` eso no es ruido, es sesgo.

**`ruta_registros` no se pone.** Existía para comparar el registrador en vivo con el compositor del
bag, comparación que se hizo el 2026-09-01 y se cerró: **no producen el mismo documento** —de las
10 claves de primer nivel que el esquema exige, el vivo trae 2— y el autoritativo es el del bag.
Encenderlo solo gasta CPU serializando a 50 Hz contra dos Gazebo, justo donde RNF-06 exige
RTF ≥ 0,99. Si alguien lo enciende igual, lo que escriba **no es un registro válido** y no debe
mezclarse con los de `Evidencia/registros/`.

`prefijo_mision` entra en el identificador de cada misión, que queda
`<prefijo>_<condicion>_<AAAAMMDD_HHMMSS>` — por ejemplo `S23_B_20260914_143022`. Sin prefijo, el
identificador empieza por `manual_`. Hace falta saberlo para confirmar una transición de piso
(§5.2).

---

## 4. La interfaz de usuario

Solo hace falta si la misión se pide desde el teléfono, que es lo que verifican RF-17 a RF-20 y lo
que hace falta para las situaciones de usuario (RF-28, RF-29). Una misión lanzada con
`ros2 action send_goal` no necesita nada de esta sección.

Son **dos procesos** y van después del coordinador, porque los dos hablan con él.

**Terminal 5 — el puente.** Desde el workspace, porque sin `coordinacion_msgs` sourceado el puente
no sabe serializar la acción:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch rosbridge_server rosbridge_websocket_launch.xml send_action_goals_in_new_thread:=true
```

**Esperado:** `Sending action goals in new thread` y
`Rosbridge WebSocket server started on port 9090`.

> **El argumento no es opcional y no es cosmético.** Por omisión vale `false`, y entonces
> `rosbridge` atiende la meta de `guiar_usuario` **en el mismo hilo que lee el WebSocket**:
> `SendActionGoal.send_action_goal` llama a `ActionClientHandler.run()` en línea, y ese `run()` no
> vuelve hasta que la misión termina. Mientras tanto el puente no procesa **ni un solo mensaje
> entrante más de ese cliente**. El tráfico de salida sí sigue —lo emite el ejecutor de ROS—, así
> que el panel se actualiza con normalidad y todo parece bien; lo que se queda encolado es lo que
> el usuario pulsa. Medido el 2026-09-10 con una misión que tarda 20 s en fallar: el `publish`
> salió del navegador a los 3,06 s y llegó al coordinador **2 ms después de terminar la misión**,
> 17 s tarde. Con el argumento puesto, llegó a los 3,06 s. Afecta por igual a la confirmación de
> piso y a la cancelación, así que se queda puesto siempre.

**Terminal 6 — servir los archivos.** Desde la raíz del clon:

```bash
python3 -m http.server 8000 --directory interfaz_web
```

**Esperado:** `Serving HTTP on 0.0.0.0 port 8000`.

La dirección que se teclea en el teléfono sale de:

```bash
hostname -I
```

y se abre como `http://<esa_ip>:8000/`. No hay que configurar nada más en la página:
`interfaz_web/js/app.js` deriva la dirección del WebSocket de `location.hostname`, así que el
teléfono habla con el mismo equipo del que descargó la página. Para apuntar a otro,
`http://<ip>:8000/?ws=<host>:9090`.

**`localhost` no vale desde el teléfono**, y es el error que más tiempo cuesta porque la página
carga y solo falla la conexión: el led se queda rojo con «sin conexion, reintentando…».

### El cortafuegos

El portátil tiene `ufw` activo y con la política por omisión el teléfono no llega a ninguno de los
dos puertos. Una sola vez:

```bash
sudo ufw allow from 192.168.0.0/24 to any port 8000 proto tcp comment 'HRI web tesis' && sudo ufw allow from 192.168.0.0/24 to any port 9090 proto tcp comment 'rosbridge tesis'
```

**Acotada a la subred, y no `allow 9090` a secas.** `rosbridge` **no tiene autenticación**: quien
alcance el 9090 puede publicar en cualquier tópico y llamar a cualquier servicio, incluido conducir
los robots. Escrita así, la misma máquina en otra red —la del edificio— queda cerrada sin tener que
acordarse de borrar nada. Comprobar con `sudo ufw status numbered`.

---

## 5. Grabar y lanzar la misión

### 5.1 Grabar va ANTES de lanzar

**Terminal 7**, desde la raíz del clon:

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S23_demo_01 robot1 robot2
```

**Esperado:** `Grabando en ...` con el recuento de tópicos, y ni un `AVISO`.

**Si falla:** el script se niega a grabar antes que grabar mal, y dice por qué. Los dos casos
frecuentes: nadie publica `/clock` o `/coordinacion/estado_mision` —de ahí salen **todas** las
marcas temporales—, o la terminal no tiene el workspace sourceado y `ros2 bag record` descartaría
`coordinacion_msgs` en silencio dejando un bag con pinta de bueno. Los dos se han dado.

Deja junto al bag dos archivos que **no se pueden reconstruir después**:

- `rtf.json`, con marcas de `/clock` antes y después. Es lo único que puede dar el RTF: con
  `--use-sim-time` el bag sella *todo* en tiempo de simulación, así que sim/pared vale 1 por
  construcción.
- `condicion_inicial.json`, el criterio 1 del §8 medido en el instante en que empieza la corrida.

**Si no se escriben en el momento, no se escriben nunca.** Tres bags de la campaña (misiones 13, 22
y 28) salieron sin RTF, el guion lo tragaba saliendo con código 0, y cuando se fue a componer
`gzserver` ya estaba cerrado: **el RTF era irrecuperable**. Está corregido —aborta antes de grabar
si falla la marca inicial y sale con código 3 si falla la de cierre—, pero la lección operativa no
la arregla el código: **el registro se compone al terminar cada misión, no al final de la tanda.**

### 5.2 Las tres clases de misión que el sistema soporta hoy

**(a) Intra-nivel, condición A.** Desde el workspace:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm2', destino_id: 'piso1_etm11'}"
```

**Esperado:** `exito: true`, **`relevos: 0`**, y las etapas
`RECIBIDA → TRAMO_1 → TRAMO_1 → COMPLETADA`. La segunda `TRAMO_1` **no es un error**: una misión
tiene siempre dos tramos —el robot va primero al **origen** y después al destino—, y en una misión
intra-nivel los dos comparten etapa; lo único que cambia es el destino.

**(b) Entre pisos con confirmación del usuario, condición B — RF-28.** Desde el workspace:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_representacion', destino_id: 'piso2_ieee'}"
```

**Esperado:** `exito: true`, **`relevos: 1`**. Al llegar a la escalera el coordinador entra en
`ESPERANDO_CONFIRMACION` y **se detiene ahí hasta que el usuario diga que ya cambió de piso**:
aviso a los **60 s**, corte a los **120 s**.

**Los dos plazos son de reloj de PARED, no de simulación**, y no es un detalle: quien sube las
escaleras es una persona real en los dos bancos, así que su paciencia se mide en segundos reales.
Con RTF 0,5 estos 120 s de simulación serían 240 s de espera real; y si Gazebo muriera durante la
espera, `/clock` se detendría y un plazo medido en tiempo de simulación **no vencería nunca** —el
coordinador se colgaría justo en el caso para el que existe el plazo—.

Desde el teléfono, la confirmación es el botón «Ya estoy en el otro piso». Desde terminal hay que
publicar el **`mision_id`**, no un texto libre: el enganche descarta cualquier otra cosa, y eso es
deliberado —una confirmación de la misión anterior no puede desbloquear la de ahora—. Primero se
lee el identificador vivo:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic echo --once --field mision_id /coordinacion/estado_mision
```

y se publica ese mismo valor:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic pub --once /coordinacion/confirmacion_piso std_msgs/msg/String "{data: 'S23_B_20260914_143022'}"
```

**(c) Cancelación del usuario — RF-29.** Desde la raíz del clon:

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/cancelar_mision.py --origen piso1_etm6 --destino piso1_etm9
```

y su **corrida de control**, que es la que hace falsable la prueba:

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/cancelar_mision.py --origen piso1_etm6 --destino piso1_etm9 --sin-cancelar
```

**Esperado:** la cancelada cierra en `FALLIDA` con `exito: false` después de que el robot **regrese
al punto de transferencia de su propio nivel**; la de control cierra en `COMPLETADA` y produce
**cero** marcas de etapa `CANCELANDO`.

**La cancelación se dispara por DISTANCIA (8 m) y no por tiempo**, y de eso depende que la prueba
mida algo: `robot1` nace a **1,41 m** de `piso1_escalera`, así que una cancelación temprana
satisfaría el criterio «queda a 0,25 m del punto de transferencia» **sin que el robot se hubiera
movido**. El script espera a que `/odom` lo sitúe más allá del umbral y solo entonces cancela.

Que esto valga como «el usuario cancela desde la interfaz» no es una analogía: la HRI manda
`cancel_action_goal` por rosbridge y rosbridge lo traduce al servicio
`<accion>/_action/cancel_goal`, **el mismo** que llama `cancel_goal_async()`. Cambia quién aprieta
el botón, no el camino que recorre el coordinador.

### 5.3 Cerrar el bag

Cuando la misión termine, **Ctrl-C en la terminal 7**. En ese orden: cortar antes deja la misión
sin su última marca.

---

## 6. Componer la evidencia, después de CADA misión

**Ver las etapas, que es lo primero que se mira.** Desde la raíz del clon:

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/inspeccionar_etapas.py ~/tesis_evidencia/S23_demo_01
```

Imprime cada cambio de etapa con su robot, su destino y el **texto literal con el que el
coordinador habló al usuario** —que ningún registro guarda—. La columna `destino_actual` es donde
una cancelación se lee de un vistazo: la fila donde el destino salta de `piso1_etm6` a
`piso1_escalera` **es** la prueba de que el robot dio media vuelta.

Con `--etapa 7` filtra las marcas de `ESPERANDO_CONFIRMACION` y mide su separación. Hace falta
porque el bloque `marcas` del registro es un diccionario de instantes únicos y **no puede
representar** que la etapa 7 se marque dos veces en una misión —la pregunta y la alerta de los
60 s—.

**Dictaminar la llegada.** Desde la raíz del clon:

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/diagnosticar_llegada.py ~/tesis_evidencia/S23_demo_01 --robot robot1
```

**El veredicto de llegada se juzga contra `/odom`, nunca contra el `SUCCEEDED` de Nav2.** Es la
regla del 2026-08-12 y la razón de que exista el riesgo R12. Criterio: **≤ 0,25 m**.

**Componer el registro.** Desde la raíz del clon —la ruta de `--salida` es relativa a ella:

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/componer_registro.py ~/tesis_evidencia/S23_demo_01 --banco simulacion --campana S23_demo --piloto --salida Documentos/Evidencia/registros/S23_demo_01.json
```

**Esperado:** un JSON validado contra [el esquema](ESQUEMA_REGISTRO_MISION.md), sin ningún campo
que haya que rellenar a mano. **`--piloto` es obligatorio** mientras no sea una corrida de campaña
sorteada: sin él, el registro entra como dato de campaña.

**Agregar.** Desde la raíz del clon, **sin sourcear nada** —el analizador no abre bags:

```bash
python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana S23_demo
```

**Esperado:** el informe con las cuatro métricas y `VEREDICTO: VALIDA`. Se corre **después de cada
corrida**, no solo al final: es la única forma de enterarse de que algo se está registrando mal en
la corrida 2 y no en la 30. Sale con código 0 solo si el veredicto es `VALIDA`, y `VALIDA` exige
que quede al menos una corrida que contar — un informe con `Registros leidos: 0` y veredicto
favorable sería la señal más fuerte del programa emitida desde ninguna evidencia, y por eso no
existe.

### Dos trampas al componer

1. **Compón con el árbol de git limpio.** `procedencia.repositorio_limpio` es
   `git status --porcelain == ""` y eso **cuenta los archivos sin seguimiento**, así que componer
   un registro ensucia el árbol para el siguiente. Si vas a componer varios, mándalos a `/tmp` con
   `--salida` y muévelos después. Pasó el 2026-09-14: el primero salió con `true` y el segundo con
   `false` sin que hubiera cambiado nada del código.
2. **Una misión cancelada no se mide contra el destino pedido.** El compositor lo resuelve solo
   desde el 2026-09-14 —lee el punto de referencia de la última marca `CANCELANDO` del bag—, pero
   un registro compuesto con una versión anterior que tenga una marca de etapa 8 y una cifra de
   decenas de metros está **mal etiquetado** y hay que rehacerlo. El §8 del
   [protocolo](PROTOCOLO_EXPERIMENTAL.md) lo dice con más detalle.

---

## 7. Cuándo una corrida vale

Las cinco condiciones del §8 del [protocolo](PROTOCOLO_EXPERIMENTAL.md). **Si falla una, la corrida
se descarta y se repite**, y el descarte se anota — el techo es el 20 %.

| | criterio | de dónde sale |
|---|---|---|
| 1 | **error de localización** de los dos dentro de **0,15 m** | §2 de aquí, y `condicion_inicial.json` del bag |
| 2 | **RTF ≥ 0,99** | `rtf.json` del bag |
| 3 | error de llegada **≤ 0,25 m** contra `/odom` | §6 de aquí |
| 4 | el registro se compone **sin tocar un campo a mano** y el analizador lo agrega sin errores de integridad | §6 de aquí |
| 5 | número de relevos = **0** en condición A, **1** en B | resultado de la acción |

A los que se suma, desde el 2026-09-14, la causa de descarte `cancelacion_usuario`: una misión
cancelada cierra con `exito: false`, así que **sin esa causa se contaría como fallo** contra la
tasa de éxito de RF-23. Se comprueba **contra el bag** —el `mensaje_usuario` de la marca
`FALLIDA`— y no contra el registro, y esa distinción es deliberada: una comprobación que se apoye
en el derivado deja de detectar que el derivado se rompió, que es exactamente lo que pasó ese día.

**Que un robot no esté en su spawn no es motivo de descarte.** El criterio 1 mide `/amcl_pose`
contra `/odom`, no contra la tabla de spawn: en el banco físico no se puede respawnear nada, y
encadenar misiones es el comportamiento que hay que validar. Lo que se descarta es que el robot
**no sepa dónde está**.

---

## 8. Parar todo

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot2 parar
```

Y Ctrl-C en las terminales del coordinador, el puente y el servidor web. `robot.sh parar` limita la
limpieza a los procesos marcados como propios del robot pedido —lee `DEEPRACER_ROBOT` de
`/proc/<pid>/environ`—, así que no tumba al compañero. `herramientas/lanzar_sim.sh` sí mata todo lo
que huela a ROS o Gazebo, y por eso no se usa con dos robots.
