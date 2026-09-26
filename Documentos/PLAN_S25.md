# Plan de la Semana 25 — del carro que navega solo al sistema real

**Semana:** lunes 28 de septiembre a viernes 2 de octubre de 2026. **Redactado:** 2026-09-25.
**En una frase:** asegurar el corte C-1 del viernes —G-2 y G-3— y, a la vez, **quitar lo que hoy
impide que el sistema real corra**: que los dos carros no se pisen, que la pila lleve espacios de
nombres, que el mapa del edificio esté validado, y que el coordinador y la interfaz funcionen en un
carro.

**Por qué este orden y no otro.** G-2 y G-3 tienen fecha dura: si el viernes 2 no están, el acta
revierte a NO-GO y RF-27 se declara no alcanzable. Pero son **compuertas**, no el objetivo: el
objetivo es el sistema real —dos carros, coordinador y relevo entre pisos—, que es G-5 y RF-27, con
corte el **viernes 16 de octubre**. Esta semana hay que hacer las dos cosas, y la segunda es la que
lleva más riesgo.

---

## 0. La semana de un vistazo

| Día | Bloque | Qué | Quién (propuesta) | ¿Carros? |
|---|---|---|---|---|
| **Lun 28** | **F** | Las tres decisiones a los directores, por escrito | Santiago | no |
| **Lun 28** | **A** | Aislar los dos carros: partición DDS en cada uno | Santiago y Jonny | **los dos** |
| Lun 28 – mar 29 | **C** | La pila con espacio de nombres, en el escritorio | Santiago | no |
| Lun 28 – mié 30 | **D** | Validar el modelo del edificio con cinta; red entre pisos | Jonny | uno, para la red |
| **Mar 29** | **B** | **Sesión de compuertas G-2 y G-3** (miércoles de reserva) | Santiago | uno |
| Mié 30 | **C** | Un carro navega con espacio de nombres | Santiago | uno |
| Jue 1 | **C + E** | Los dos carros a la vez; coordinador e interfaz en un carro | los dos | **los dos** |
| **Vie 2** | — | **Corte C-1**, y corte semanal | los dos | no |

**Lo que no se hace esta semana, y por qué:**

| Qué | Por qué no |
|---|---|
| La campaña de RF-27 | Pide el **protocolo completo** —dos carros y relevo entre pisos—, que es G-5. Va en S27, después de tener el sistema |
| Más corridas de un solo carro que las tres de G-2 y G-3 | **No cuentan para RF-27.** Una versión anterior de la guía decía que sí; era falso |
| El guion de mapeo de 6 m de piso 2 | Innecesario: el mapa existe y admite corridas de 5 m |
| Ver los carros en vivo | No hace falta para nada de esto; RViz sobre el bag basta |

---

## 1. Bloque A — aislar los dos carros (lunes)

**Por qué primero:** con los dos carros encendidos, una orden mueve los dos y la odometría de cada uno
recibe el láser del otro. Sin esto no hay sistema real. El diseño y su justificación están en
[`DISENO_AISLAMIENTO_DOS_CARROS.md`](DISENO_AISLAMIENTO_DOS_CARROS.md); el mecanismo ya pasó **9 de 9**
en el portátil. Falta confirmarlo en Jazzy y con el servicio de AWS.

**Regla de seguridad del bloque: ruedas en el aire** —el carro sobre una caja— en todo lo que
publique en los servos. Y las pruebas de servos solo mueven la **dirección** (`throttle: 0.0`), que no
puede desplazar el carro.

### A1 · La prueba en el vehículo, sin tocar nada de AWS (10 min)

| | |
|---|---|
| **Objetivo** | Que el Fast DDS de Jazzy respete los perfiles igual que el de Humble. |
| **Comando** | `scp herramientas/prueba_particion_carros.sh Robot/aws-deepracer/deepracer_bringup/config/particion_amss-ez9n.xml Robot/aws-deepracer/deepracer_bringup/config/particion_amss-jgm9.xml deepracer@192.168.0.102:~/tesis/` y después `ssh deepracer@192.168.0.102 "bash ~/tesis/prueba_particion_carros.sh"` |
| **Esperado** | `ROS jazzy` en la primera línea, **9 filas `ok`** y `PASA`. Corre en el dominio 87, así que no toca nada del carro. |
| **Si falla** | **Parar el bloque.** El mecanismo no vale en Jazzy tal cual: pasar al plan B del §7 del diseño y avisar, porque cambia el calendario. |
| **Cierre** | `PASA` en **los dos** vehículos (repetir con `192.168.0.101`). |

### A2 · Instalar la partición en cada vehículo (15 min por carro)

| | |
|---|---|
| **Objetivo** | Que el servicio de AWS cargue el perfil de su carro. |
| **Comando** | `ssh deepracer@192.168.0.102 "sudo -n install -D -m 644 ~/tesis/particion_amss-ez9n.xml /etc/deepracer-tesis/particion.xml && sudo -n mkdir -p /etc/systemd/system/deepracer-core.service.d && printf '[Service]\nEnvironment=FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml\n' \| sudo -n tee /etc/systemd/system/deepracer-core.service.d/particion.conf > /dev/null && sudo -n systemctl daemon-reload && sudo -n systemctl restart deepracer-core && echo INSTALADO"` — y en `amss-jgm9` lo mismo con `particion_amss-jgm9.xml` |
| **Comprobación** | Pasados 30 s: `ssh deepracer@192.168.0.102 "sudo -n cat /proc/\$(pgrep -x servo_node \| head -1)/environ \| tr '\0' '\n' \| grep FASTRTPS"` |
| **Esperado** | `INSTALADO`, y la comprobación devuelve `FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml`. |
| **Si falla** | Si la comprobación sale vacía, el servicio no tomó la variable: `ssh deepracer@192.168.0.102 "systemctl cat deepracer-core"` debe mostrar el `particion.conf` al final. |
| **Para deshacerlo** | `ssh deepracer@192.168.0.102 "sudo -n rm -f /etc/systemd/system/deepracer-core.service.d/particion.conf && sudo -n systemctl daemon-reload && sudo -n systemctl restart deepracer-core"` |
| **Cierre** | Los **dos** carros con la variable en el proceso de servos. **Uno solo no vale**: la regla es tocar los dos a la vez. |

> **Desde este momento, todo lo que se lance en el carro tiene que cargar el perfil**, o no verá el
> láser ni llegará a los servos, y no dará error. Los scripts del repo ya lo hacen solos
> (`nav2_mapa_guardado.sh`, `correr_corrida_nav2.sh`, `mapear_conduciendo.sh`, `lanzar_bag.inc`);
> **las órdenes a mano que lean `/rplidar_ros/scan` o `/tf` tienen que llevar
> `export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml`**.

### A3 · El láser solo se ve con el perfil (5 min)

| | |
|---|---|
| **Comando** | `ssh deepracer@192.168.0.102 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml && timeout 12 ros2 topic hz /rplidar_ros/scan'"` y la misma orden **sin** el `export` |
| **Esperado** | Con el perfil, `average rate` en torno a **7 Hz**. Sin él, **nada**. |
| **Cierre** | Las dos cosas, en los dos carros. |

### A4 · Una orden solo mueve su carro (15 min, los dos encendidos, ruedas en el aire)

| | |
|---|---|
| **Comando, desde `amss-jgm9`** | `ssh deepracer@192.168.0.101 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml && timeout 5 ros2 topic pub -r 10 /ctrl_pkg/servo_msg deepracer_interfaces_pkg/msg/ServoCtrlMsg \"{angle: 0.6, throttle: 0.0}\"; timeout 4 ros2 topic pub -r 10 /ctrl_pkg/servo_msg deepracer_interfaces_pkg/msg/ServoCtrlMsg \"{angle: 0.0, throttle: 0.0}\"'"` |
| **Esperado** | **Giran las ruedas delanteras de `amss-jgm9` y vuelven; las de `amss-ez9n` no se mueven.** |
| **Después** | La misma orden desde `amss-ez9n` (`192.168.0.102`): solo se mueve ese. Y la misma orden desde cualquiera **sin** el `export`: **no se mueve ninguno**. Esa última es la propiedad de seguridad que importa. |
| **Si falla** | Si se mueven los dos, la partición no está en el servicio de AWS: volver a A2. |
| **Cierre** | Las tres observaciones anotadas en papel, por carro. |

### A5 · Cada odometría ve solo su láser (5 min, los dos encendidos)

| | |
|---|---|
| **Comando** | La de A3, con el `export`, en los dos carros a la vez. |
| **Esperado** | **~7 Hz en cada uno.** El 23-sep, sin partición y con los dos encendidos, se midieron **14,68 Hz**: los dos láseres mezclados. |
| **Cierre del bloque A** | A1–A5 en verde. **Con eso, los dos carros pueden estar encendidos a la vez por primera vez.** |

---

## 2. Bloque B — la sesión de compuertas G-2 y G-3 (martes; miércoles de reserva)

Se hace el martes y no el viernes para que, si algo falla, quede **un día de reserva antes del corte**.

**El procedimiento es el de [`GUIA_CAMPANA_NAV2_HARDWARE.md`](GUIA_CAMPANA_NAV2_HARDWARE.md)**, en el
tramo encajonado del piso 2, con `amss-ez9n`. Resumido:

1. Sitio: cajas y cinta como en el §2 de la guía; **salida y meta separadas 5,00 m, medidos**.
2. Arranque: `nav2_mapa_guardado.sh` (§4.1 de la guía). Escala en **0,68** (§4.2).
3. Las dos comprobaciones sin mover el carro (§4.3): el planificador llega a la meta, y los costmaps
   escuchan el láser.
4. **Tres corridas**: `correr_corrida_nav2.sh c1_01 … c1_03` con `--avance 5.0` (§5).
5. Cinta en cada una, antes de tocar el carro (§5.3).
6. Análisis en el escritorio, el mismo día: `analizar_campana_nav2.py` (§7).

| Compuerta | Qué la cierra | Depende de |
|---|---|---|
| **G-2** | Las tres corridas con la razón `/odom` ÷ cinta dentro del ±10 % | nada: se puede correr aunque falte la tolerancia |
| **G-3** | Llegada verificada contra `/odom` y cinta, dentro de la tolerancia | **la tolerancia escrita por los directores** (bloque F) |

> **Si el martes no ha contestado nadie sobre la tolerancia, se corre igual y se analiza solo G-2.**
> G-3 se analiza con los mismos datos cuando llegue la respuesta —los datos no cambian—, pero la
> tolerancia **no se fija viendo los resultados**. Si el viernes sigue sin respuesta, G-3 se reporta
> contra 0,25 m y se dice que la tolerancia estaba pendiente.

> **El riesgo de G-3 es real.** Con la escala en 0,9, la navegación del 24-sep se pasó 0,412 m. Ir
> a 0,68 **debería** reducir el error, y es lo que se mide. Si con 0,68 tampoco entra en 0,25, el
> resultado es el hallazgo y se lleva a los directores con el mecanismo medido.

---

## 3. Bloque C — la pila con espacio de nombres

**Por qué:** el coordinador llama a `/robotN/navigate_to_pose` y lee `/robotN/odom`, con metas en el
marco `robotN/map`. Toda la navegación de esta semana corrió **sin** espacio de nombres. Es trabajo de
**despliegue** —lanzadores y parámetros—, no funcionalidad nueva, así que no rompe la congelación.

### C1 · En el escritorio (lunes y martes, Santiago)

Lo que hay que cambiar, en [`nav2_hardware.launch.py`](../Robot/aws-deepracer/deepracer_bringup/launch/nav2_hardware.launch.py)
y en [`nav2_mapa_guardado.sh`](../herramientas/nav2_mapa_guardado.sh):

- Un argumento `namespace`, que meta todos los nodos bajo `/robotN`.
- **Prefijo `robotN/` en los marcos** que son nuestros —`map`, `odom`, `base_link`— y en los de la
  URDF, como hace la simulación.
- Una **TF estática identidad `robotN/laser → laser`**: el driver de AWS pone el barrido en `laser` y
  no se puede cambiar. En la TF privada de cada carro no choca con el otro.
- El puente de servos, con espacio de nombres y `-r /cmd_vel:=/robotN/cmd_vel`: su suscripción es
  absoluta y, sin el remapeo, los dos puentes escucharían el mismo `/cmd_vel`.
- [`correr_corrida_nav2.sh`](../herramientas/correr_corrida_nav2.sh) graba `/odom`, `/cmd_vel`, `/plan`,
  `/amcl_pose`… **sin** espacio de nombres: con `/robot2` el bag saldría sin ellos y sin avisar. Tiene
  que grabar los del espacio de nombres que se le pase.

**Se prueba sin carro**, como el 25-sep: construyendo el lanzamiento en el portátil y leyendo los
parámetros efectivos de cada nodo. **Cierre:** con `namespace:=robot2`, todos los nodos bajo
`/robot2`, todos los marcos con prefijo, y el modo sin espacio de nombres idéntico al de ahora.

### C2 · Un carro con espacio de nombres (miércoles, `amss-ez9n`)

| | |
|---|---|
| **Objetivo** | Que el carro navegue exactamente como lo va a mandar el coordinador. |
| **Comando** | Arranque con `NS=robot2`, y una meta con la herramienta de campaña, que ya admite espacio de nombres: `correr_corrida_nav2.sh c2_01 --ns /robot2 --marco robot2/map --salida 0.70 0.0 0.0 --avance 3.0 --mapa …` |
| **Esperado** | La misma navegación de las corridas del martes, con todo bajo `/robot2`. |
| **Cierre** | Una corrida con plan consumido y llegada, y `tf2_echo robot2/map robot2/base_link` resolviendo **con el perfil cargado**. |

### C3 · Los dos carros a la vez (jueves, en el laboratorio)

| | |
|---|---|
| **Objetivo** | Lo que hoy no se puede: los dos encendidos, cada uno navegando lo suyo. |
| **Esperado** | Cada carro llega a su meta; ninguno se mueve con las órdenes del otro; cada odometría a ~7 Hz de láser. |
| **Cierre** | Una meta cumplida en cada carro con el otro encendido y navegando. **Es la primera vez que los dos se mueven a la vez.** |

---

## 4. Bloque D — el edificio (lunes a miércoles, Jonny)

### D1 · El modelo contra el edificio, con cinta y sin robot

El sistema real navega el edificio sobre los mapas del modelo de Gazebo. Si el modelo no se parece al
edificio, AMCL se localiza **con confianza en el sitio equivocado**, y eso no lo corrige nada.
Procedimiento: el Bloque 1 de [`GUION_NAVEGACION_USTA.md`](GUION_NAVEGACION_USTA.md) —diez medidas
del modelo, criterio ≤ 2 % fijado antes de medir—.

**Cierre:** la tabla de las diez medidas. **Decide qué mapa usa el sistema en cada piso**: si pasa,
el del modelo; si no, hay que decir cuál y por qué, y eso va a los directores con el sitio.

### D2 · La red entre pisos

**Por qué:** con un carro en el piso 1 y otro en el 2, el coordinador los tiene que alcanzar a los
dos. Nadie ha medido si la red llega de un piso a otro.
Procedimiento: el de RF-15 —[`HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](HOJA_CAMPO_SEGUNDO_DEEPRACER.md)—, con un
carro en cada piso, en los puntos donde van a estar durante una misión.

**Cierre:** `CUMPLE` del medidor con los carros en pisos distintos. **Si no cumple**, el relevo entre
pisos no se puede hacer así, y es lo primero que hay que llevar a los directores.

---

## 5. Bloque E — el coordinador y la interfaz en un carro (jueves)

**Por qué:** el coordinador **no puede correr en el portátil** —la acción de Nav2 no es compatible
entre Humble y Jazzy (decisión D6)—, así que corre en `amss-jgm9`, como en G-4. Y la interfaz del
teléfono llega a él por `rosbridge`.

| Paso | Qué | Cierre |
|---|---|---|
| E1 | ¿Está `rosbridge` en los carros? `ssh deepracer@192.168.0.101 "source /opt/ros/jazzy/setup.bash; ros2 pkg list \| grep rosbridge_server"`. Si no, `sudo -n apt-get update && sudo -n apt-get install -y ros-jazzy-rosbridge-suite` **en los dos** | el paquete en los dos |
| E2 | Coordinador y `rosbridge` en `amss-jgm9`, agentes en los dos, la interfaz desde un teléfono conectado a la red de los carros | la interfaz muestra los dos robots |
| E3 | **Una misión dentro de un mismo piso, pedida desde el teléfono**, con un solo carro moviéndose | el registro de la misión, compuesto con `componer_registro.py` |

E3 es el **ensayo general de G-5 sin el relevo**. Depende de C2: si el miércoles no se cerró, E pasa
al lunes 5.

---

## 6. Bloque F — lo que decide otro, y cuándo (lunes por la mañana)

El acta tiene **dos decisiones que no son de los autores** (§6) y la campaña añade una. Y la casilla
«comunicada a los directores el» del acta **está vacía**: el acta nunca se les ha enviado.

| # | Decisión | Por qué no puede esperar |
|---|---|---|
| 1 | **El sitio de la etapa 3** | El acta dice textualmente que *no se corre nada de la etapa 3 hasta que esto esté por escrito*. El sistema real con relevo entre pisos **es** la etapa 3 (S26) |
| 2 | **N = 5 o N = 10 en RF-27** | Fija cuántas misiones hay que meter en S27 |
| 3 | **La tolerancia de llegada** | G-3 se mide el martes; si se fija después de ver resultados, los resultados dejan de valer |

**Borrador del mensaje**, para enviarlo el lunes con el acta adjunta:

> Buenos días. Les enviamos el acta de decisión GO/NO-GO de la demostración física, que resolvimos el
> 21 de septiembre como GO pleno con seis compuertas y fechas de reversión. Dos de sus compuertas ya
> están alcanzadas, y el 24 de septiembre Nav2 navegó por primera vez uno de los vehículos reales de
> forma autónoma.
>
> Necesitamos su decisión por escrito sobre tres puntos antes de seguir, y por eso se los pedimos
> ahora:
>
> 1. **El sitio de la etapa 3.** El pasillo real no da a la odometría láser la información que
>    necesita para construir el mapa recorriéndolo (medido: 5,1 % y 5,9 %). Sí se puede navegar con un
>    mapa conocido. Proponemos navegar el edificio sobre el mapa del modelo, validado antes con
>    flexómetro.
> 2. **N = 5 o N = 10 misiones en la demostración física.** La norma ASTM F3244-21 respalda
>    numéricamente 10 y no 5.
> 3. **La tolerancia de llegada.** Hoy es 0,25 m. En simulación el vehículo se queda corto entre
>    0,28 y 0,35 m, y en el vehículo real se pasó 0,41 m, por un mecanismo medido: por debajo de
>    0,40 m/s el motor no arranca, así que se aproxima a la meta sin poder frenar antes. Queremos
>    fijarla antes de medir, no después.
>
> La compuerta de navegación de un vehículo tiene corte el viernes 2 de octubre, así que nos ayudaría
> mucho tener su respuesta al punto 3 antes del martes 29.

---

## 7. Viernes 2 — corte C-1 y corte semanal

| | Qué | Dónde queda |
|---|---|---|
| 1 | **G-2 y G-3 declarados**, con cifras, en la tabla del §4.1 del acta | [`ACTA_GO_NOGO.md`](ACTA_GO_NOGO.md) |
| 2 | **Si alguna no se alcanzó**, se aplica lo escrito: NO-GO, RF-27 no alcanzable, la evidencia queda en la campaña de simulación. **No se reinterpreta el criterio** | ídem |
| 3 | **Decidir si S26 va con dos carros** (bloque A y C3 en verde) **o con el repliegue de uno** | [`MAPA_TRABAJO_RESTANTE.md`](MAPA_TRABAJO_RESTANTE.md) §0 |
| 4 | Corte semanal: `ESTADO.md`, entregable de S25 en `.tex` y `.md`, commit | `ESTADO.md`, `Documentos/Entregables/` |

---

## 8. Lo que viene después

| Semana | Qué | Corte |
|---|---|---|
| **S26 · 5–9 oct** | **G-5: una misión completa desde el teléfono, con relevo entre pisos, sobre los dos carros.** Es el sistema real. Primera esquina navegada en hardware, si la ruta la tiene | **C-2, vie 9**: G-4, ya alcanzada. Decidir ese día, a más tardar, el repliegue a un solo carro si hiciera falta |
| **S27 · 12–16 oct** | **G-6 / RF-27: entre 5 y 10 misiones** —según decidan los directores— con registro, y el vídeo de la demostración | **C-3, vie 16**: se cierra la toma de datos, pase lo que pase |
| S28 | Sustentación | — |

---

## 9. Los riesgos de la semana, y qué se hace si salen

| Riesgo | Señal | Qué se hace |
|---|---|---|
| **La partición no funciona en Jazzy** | A1 no da `PASA` | Plan B del diseño (§7): LiDAR y servos fuera de `deepracer-core`. Retrasa C3 y E; G-2 y G-3 no se ven afectadas, que son de un carro |
| **No hay respuesta sobre la tolerancia** | martes sin respuesta | G-2 se cierra igual; G-3 se analiza cuando llegue, sin mirar antes (§2) |
| **G-3 no entra en la tolerancia** | el error por cinta pasa del límite | Es un resultado, con mecanismo medido; va a los directores. Si el acta obliga a revertir, se revierte |
| **La red no llega de un piso a otro** | D2 no da `CUMPLE` | Es lo más grave para S26: sin red entre pisos no hay relevo. Llevarlo a los directores con el sitio (F1) |
| **Batería o disponibilidad de los carros** | un carro no enciende o cae | Los dos cargados el domingo por la noche; el jueves tiene holgura |
| **Algo se lanza sin el perfil** | un proceso no ve el láser y no avisa | Los scripts lo cargan solos; a mano, el `export` del recuadro de A2 |
