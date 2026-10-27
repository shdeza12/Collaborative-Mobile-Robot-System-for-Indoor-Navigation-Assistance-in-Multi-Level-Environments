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
| Lun 28 | F | Hecho: las tres decisiones, acordadas con el director Armando Mateus (acta §6.1) | Santiago | no |
| Lun 28 | A | Hecho: los dos carros aislados, A1 a A5 en verde ([registro](../Evidencia/S25_aislamiento_dos_carros.md)) | Santiago y Jonny | los dos |
| Lun 28 – mar 29 | **C** | Hecho (C1): la pila con espacio de nombres, en el escritorio, con su prueba | Santiago | no |
| Lun 28 – mié 30 | **D** | Red entre pisos, con un carro en cada piso | Jonny | los dos |
| Mar 29, mañana | **B0** | Ensayo en el laboratorio. Hecho a medias: L2 y L3 con `amss-jgm9`; L1 y el L2 de `amss-ez9n` pendientes, sin batería de tracción ([registro](../Evidencia/S25_ensayo_laboratorio.md)) | Santiago y Jonny | los dos, uno cada vez |
| **Mar 29, noche** | **B** | **Sesión de compuertas G-2 y G-3**: intentada con `amss-ez9n`, sin cerrar ([registro](../Evidencia/S25_campana_c1_deepy.md)); se repite el miércoles | Santiago | uno |
| Mié 30, noche | **B-bis** | G-2 y G-3 en el hall del extremo oeste del piso 2, con `amss-jgm9`: sin cerrar; dos llegadas medidas a 1,43 y 1,26 m ([registro](../Evidencia/S25_pasillo_piso2_amss-jgm9.md)) | Santiago | uno |
| Mar 29 – mié 30 | **B2** | Pasillo liso con los dos carros: odometría contra cinta, como caracterización | Santiago y Jonny | **los dos** |
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

> **Direcciones de los carros.** Las asigna el DHCP y cambian: el 28-sep `amss-ez9n` estaba en la
> 192.168.0.102 y `amss-jgm9` en la 192.168.0.104 (hasta el viernes, la .101). Antes de cada sesión,
> buscarlos por su MAC:
> `for i in $(seq 1 254); do (ping -c1 -W1 192.168.0.$i >/dev/null 2>&1 &); done; sleep 3; ip neigh | grep -iE '80:91:33:ed:8c:f3|80:91:33:f3:e6:ab'`
> (`ed:8c:f3` es `amss-ez9n` y `f3:e6:ab` es `amss-jgm9`). Los comandos de este plan usan las del 28-sep.

---

## 1. Bloque A — aislar los dos carros (lunes; cerrado el 28-sep)

**Cerrado el lunes 28:** A1 a A5 en verde en los dos carros. Registro en
[`S25_aislamiento_dos_carros.md`](../Evidencia/S25_aislamiento_dos_carros.md).

**Por qué primero:** con los dos carros encendidos, una orden mueve los dos y la odometría de cada uno
recibe el láser del otro. Sin esto no hay sistema real. El diseño y su justificación están en
[`DISENO_AISLAMIENTO_DOS_CARROS.md`](../DISENO_AISLAMIENTO_DOS_CARROS.md); el mecanismo ya pasó **9 de 9**
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
| **Cierre** | `PASA` en **los dos** vehículos (repetir con `192.168.0.104`). |

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
| **Comando, desde `amss-jgm9`** | `scp herramientas/sonda_direccion.py deepracer@192.168.0.104:~/tesis/` y `ssh deepracer@192.168.0.104 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml && python3 ~deepracer/tesis/sonda_direccion.py'"`. La sonda publica sin parar a 20 Hz y dice cuántos suscriptores encontró; `ros2 topic pub` lanzado por posiciones no sirve (tarda 2 o 3 s en emparejarse). |
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

### B0 · Ensayo en el laboratorio, antes del pasillo (martes por la mañana, 1 h)

**Por qué:** en el pasillo, Nav2 correría por primera vez con la partición instalada y con el script de
arranque. Si algo falla, mejor verlo aquí. Hace falta un tramo recto de unos 4 m. La pila del proyecto
corre en un carro cada vez; el otro puede quedar encendido.

> **Estado, 29-sep.** L2 y L3 se hicieron con `amss-jgm9`; `amss-ez9n` no tenía batería de tracción.
> L3 dejó tres arreglos (la banda muerta del puente, el controlador a 10 Hz y el latido del gestor a
> 20 s) y un límite: con el mapa de una sola pasada, AMCL no se localizó. L1 queda para cuando los dos
> carros tengan batería. Registro: [`S25_ensayo_laboratorio.md`](../Evidencia/S25_ensayo_laboratorio.md).

**L1 · La interferencia de la pila, medida (10 min, ruedas en el aire)**

| | |
|---|---|
| **Objetivo** | Medir que hoy la pila de un carro llega al otro: sin espacios de nombres, `/cmd_vel` es común a los dos. |
| **Preparación** | Los dos sobre cajas, con las ruedas en el aire y una persona mirando cada uno. |
| **Comando** | El puente en los dos, `.102` y `.104`: `ssh deepracer@192.168.0.102 "sudo -n bash -c 'export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml; source /opt/ros/jazzy/setup.bash && source ~deepracer/coordinacion_ws/install/setup.bash && timeout 60 ros2 run cmdvel_to_servo_pkg cmdvel_to_servo_node'"`. Después, solo en `amss-jgm9`: `ssh deepracer@192.168.0.104 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 12 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \"{linear: {x: 0.2}, angular: {z: 1.0}}\"'"` y la misma orden en cero. |
| **Esperado** | La dirección va al tope y, con el puente del 29-sep, la tracción también gira: 0,2 m/s ya no da cero, sube al escalón más bajo. **Hoy deben girar las ruedas de los dos carros.** |
| **Cierre** | Anotado qué carros giraron. Es la prueba de control del bloque C: con espacios de nombres, la misma orden debe mover solo a `amss-jgm9`. |

**L2 · Mapeo de cada carro con el otro encendido (15 min por carro)**

| | |
|---|---|
| **Objetivo** | Que el mapeo de un carro no se mezcle con el otro encendido y sin pila. |
| **Comando** | `ssh deepracer@192.168.0.102 "sudo -n bash ~/tesis/mapear_conduciendo.sh 3.0 0.5 30"`, con `amss-jgm9` encendido y sin pila; después al revés, con `192.168.0.104`. |
| **Esperado** | `motivo de parada : DISTANCIA ALCANZADA`. En la grabación, el LiDAR a unos 7 Hz y no a 14, y la odometría con una sola trayectoria, sin saltos. El mapa, con paredes únicas. |
| **Si falla** | LiDAR a 14 Hz o dos trayectorias mezcladas: la pila del otro carro sigue viva. Pararla y repetir. |
| **Cierre** | Las dos grabaciones revisadas y los dos mapas guardados en `~deepracer/mapeo_<hora>/`. |

**L3 · Nav2 sobre ese mapa (20 min, `amss-ez9n`)**

| | |
|---|---|
| **Objetivo** | La cadena del pasillo, en pequeño: partición, script de arranque y herramienta de corrida. |
| **Comando** | `CARRO=192.168.0.102 MAPA=<mapa.yaml de L2, con su ruta absoluta en el carro> POSE_X=0.0 bash herramientas/nav2_mapa_guardado.sh`; velocidad a 0,68; comprobación del planificador (§4.3 de la guía); una corrida: `correr_corrida_nav2.sh l3_01 --salida 0.0 0.0 0.0 --avance 2.0` con ese mapa y `--csv ~deepracer/ensayo_l3.csv`. |
| **Esperado** | `CADENA LISTA`; el planificador llega a la meta; la corrida termina con el carro parado cerca de 2 m y su fila en el CSV; la grabación trae LiDAR y transformadas. |
| **Si falla** | El script dice en qué paso. Se corrige aquí, antes de ir al pasillo. |
| **Cierre** | Una corrida completa. Si queda tiempo, lo mismo con `amss-jgm9`. Al terminar, `nav2_mapa_guardado.sh --parar`. |


Se hace el martes y no el viernes para que, si algo falla, quede **un día de reserva antes del corte**.

**El procedimiento es el de [`GUIA_CAMPANA_NAV2_HARDWARE.md`](GUIA_CAMPANA_NAV2_HARDWARE.md)**, en el
tramo encajonado del piso 2, con `amss-jgm9` (`amss-ez9n` sin batería de tracción el 29-sep). Resumido:

1. Sitio: cajas y cinta como en el §2 de la guía; **salida y meta separadas 5,00 m, medidos**.
2. Arranque: `nav2_mapa_guardado.sh` (§4.1 de la guía). Escala en **0,9**, la que fija el script: con
   0,68 `amss-jgm9` suena y no arranca (29-sep). Nav2 tarda de 3 a 5 min en quedar activo.
3. Las dos comprobaciones sin mover el carro (§4.3): el planificador llega a la meta, y los costmaps
   escuchan el láser.
4. **Tres corridas**: `correr_corrida_nav2.sh c1_01 … c1_03` con `--avance 5.0` (§5).
5. Cinta en cada una, antes de tocar el carro (§5.3).
6. Análisis en el escritorio, el mismo día: `analizar_campana_nav2.py` (§7).

| Compuerta | Qué la cierra | Depende de |
|---|---|---|
| **G-2** | Las tres corridas con la razón `/odom` ÷ cinta dentro del ±10 % | nada |
| **G-3** | Llegada verificada contra `/odom` y cinta, a 0,5 m o menos de la meta | nada: la tolerancia se fijó el 28-sep (acta §6.1) |

> La tolerancia de 0,5 m la fijó el director el 28-sep, antes de estas corridas, y
> `analizar_campana_nav2.py` ya la usa por defecto. No se cambia viendo los resultados.

> Con la escala en 0,9, la navegación del 24-sep paró a 0,412 m de la meta, dentro de 0,5 m. La idea
> de bajar a 0,68 para reducir ese error no se puede aplicar: el 29-sep `amss-jgm9` no arrancó con
> 0,68 ni con 0,80, así que las corridas van con 0,9. Si alguna pasa de 0,5 m, se reporta con su causa.

> **Estado, 29-sep noche.** Cuatro corridas con `amss-ez9n` (`amss-jgm9` se quedó sin batería de
> la computadora): una llegó pero se pasó 1,134 m según `/odom`, dos abortaron antes de moverse por
> dos defectos corregidos esa noche (el plazo de `bt_navigator` y la pose inicial de
> `corrida_nav2.py`), y la cuarta no se detuvo por un salto de la odometría. Ninguna tiene medida de
> flexómetro. Se repite el miércoles 30. Registro: [`S25_campana_c1_deepy.md`](../Evidencia/S25_campana_c1_deepy.md).

### B-bis · G-2 y G-3 en el pasillo real del piso 2, con el mapa del modelo (miércoles 30)

**Por qué cambia el sitio.** La sesión del 29-sep corrió sobre el mapa S24 en un pasillo que no era
el de ese mapa y no vale ([`S25_campana_c1_deepy.md`](../Evidencia/S25_campana_c1_deepy.md)). El 29-sep
se decidió hacer G-2 y G-3 en los pasillos reales del modelo, que es además el sitio que fijó el
director (acta §6.1), navegando sobre `mundo_definitivo_piso2`, que tiene las medidas del edificio.
Los vehículos no han estado todavía en esos pasillos: esta es la primera vez.

**El tramo.** Sobre el eje del pasillo (`y = −4,5`, a 1,30 m de cada pared) el mapa está libre de
`x = −17,28` a `x = 23,16` en todo el ancho del carro (`zona_libre_mapa.py --y -4.5`). Salida en
`x = −12,0`, meta en `x = −7,0`: 5 m de avance que empiezan 2 m al este de la apertura al hall
(`x = −14,1`), donde el láser todavía ve el hall detrás. Figura:
[`S25_mapa_piso2_salida_A.png`](../Evidencia/S25_mapa_piso2_salida_A.png).

| Paso | Qué | Comando o acción | Esperado | Si falla | Cierre |
|---|---|---|---|---|---|
| 0 | Confirmar el sitio | Santiago y Jonny confirman que están en el pasillo del piso 2 que modela `mundo_definitivo_piso2` y que reconocen la apertura al hall del extremo oeste | Sitio confirmado de palabra, antes de encender nada | Si no es ese pasillo, no se navega con este mapa: se para y se decide | Confirmación registrada en la evidencia |
| 1 | Red | El router junto al tramo; el portátil por cable al router | Los dos vehículos responden al ping en menos de 30 ms | Acercar el router; comprobar la batería de la computadora de cada carro | Los dos en la red |
| 2 | Nivelar `amss-jgm9` | Copiar `nav2_hardware.launch.py` y `corrida_nav2.py` (pendientes del 29-sep) | md5 iguales al repositorio en los dos | Si no responde, queda pendiente y se sigue con `amss-ez9n` | Los dos vehículos con los mismos archivos |
| 3 | Marcar el tramo | Línea del hall en `x = −14,1`, donde terminan las paredes del pasillo; **línea de salida a 2,24 m de ella** (la defensa delantera va 0,14 m por delante del punto que Nav2 lleva a la meta); **línea de meta a 5,00 m de la salida, medidos con flexómetro**; eje en el centro del pasillo | Tres cintas en el suelo y la separación anotada con la cifra del flexómetro | — | Cintas puestas y cifra anotada |
| 4 | Arrancar Nav2 en `amss-ez9n` | `CARRO=192.168.0.102 MAPA=/home/deepracer/tesis/mundo_definitivo_piso2.yaml POSE_X=-12.0 POSE_Y=-4.5 bash herramientas/nav2_mapa_guardado.sh` | `Managed nodes are active` en `/tmp/nav2_campo/launch.log`, de 3 a 5 min | El §8 de la guía | Nav2 activo (la ruta del mapa es la ruta fija del vehículo) |
| 5 | Comprobar sin mover | Pose inicial en (−12,0, −4,5); ruta a (−7,0, −4,5) con `compute_path_to_pose`; `ros2 param get /bt_navigator default_server_timeout` | `SUCCEEDED` y `1000` | `Start occupied`: la pose no coincide con el sitio; recolocar el carro | Las dos comprobaciones |
| 6 | Tres corridas | `ssh deepracer@192.168.0.102 "sudo -n bash ~deepracer/tesis/correr_corrida_nav2.sh p2d_01 --salida -12.0 -4.5 0.0 --avance 5.0 --mapa /home/deepracer/tesis/mundo_definitivo_piso2.yaml --csv ~deepracer/campana_p2_deepy.csv"`, y `p2d_02`, `p2d_03` | Fila en el CSV por corrida | Una corrida que aborta antes de moverse se repite con otro id | **Flexómetro antes de tocar el carro**: avance real, error longitudinal con signo y desvío lateral (ruta fija del vehículo en `--mapa`) |
| 7 | El otro carro | `--parar` en `amss-ez9n` y los pasos 4 a 6 en `192.168.0.104`, ids `p2r_01…03` y CSV `campana_p2_racey.csv` | Igual | — | Tres corridas medidas por carro |

La escala es 0,9 en los dos: con menos, `amss-jgm9` no arranca (29-sep). Si una corrida se pasa de
0,5 m, se reporta con su causa; no se cambia la escala a mitad de serie.

> **Estado, 30-sep noche.** El tramo del pasillo largo no se usó: `amss-jgm9` perdía el WiFi lejos
> del router, que estaba en el IEEE, y el equipo limitó la prueba a los destinos IEEE, Lab. 313 y
> Escaleras, en el hall del extremo oeste. Ocho corridas con `amss-jgm9` (p2r_01 a p2r_08);
> `amss-ez9n` se apagó sin correr. Las dos llegadas medidas con flexómetro, ambas hacia las
> escaleras, quedaron a 1,43 m y 1,26 m del destino, y rf2o registró el 73 % del avance medido.
> G-2 y G-3 siguen abiertas. Se corrigieron la odometría invertida de rf2o (parche), el margen de
> llegada de Nav2 (1,0 m) y el ancho del hall en el modelo (3,40 m). No se navega hacia la escalera
> hasta resolver el error longitudinal de AMCL en el hall (2,62 m en p2r_05). El sitio de la próxima
> sesión está por decidir ([registro](../Evidencia/S25_pasillo_piso2_amss-jgm9.md)).

### B2 · El pasillo liso, con los dos carros (martes después de B, o miércoles)

**Por qué:** las misiones van a recorrer el pasillo abierto, donde la información de avance es 5,1 %
(piso 1) y 5,9 % (piso 2), y el tramo de la sesión de compuertas tiene cajas en los dos extremos, que
le dan a rf2o la estructura que necesita. Esto mide la odometría donde va a operar el sistema, y con
los dos carros. **Se declara antes de correr como caracterización:** no cuenta para G-2 ni cambia su
resultado.

| | |
|---|---|
| **Objetivo** | La razón odometría ÷ cinta de cada carro en el tramo liso del pasillo, con su grabación. |
| **Sitio** | Tramo liso, a más de 6 m del hall y lejos de puertas abiertas, con **11 m libres** por delante y la salida marcada con cinta. Cada carro en el pasillo del piso donde va a operar: `amss-jgm9` (robot1) en el piso 1 y `amss-ez9n` (robot2) en el piso 2. |
| **Copia** | La del §2 de [`GUION_CAMPO_PISO2.md`](GUION_CAMPO_PISO2.md) (`mapear_conduciendo.sh`, `avanzar_y_detener.py`, `lanzar_bag.inc`, `slam_toolbox_carro.yaml`), **en los dos carros**. |
| **Comando** | `ssh deepracer@192.168.0.104 "sudo -n bash ~/tesis/mapear_conduciendo.sh 5.0 0.5 40"`, y lo mismo con `192.168.0.102`. **Uno después del otro, nunca a la vez**: la partición no cubre `/cmd_vel` ni `/odom`, y el avance de un carro movería al otro. El otro carro puede quedar encendido. |
| **Esperado** | Si rf2o ve el avance: `motivo de parada : DISTANCIA ALCANZADA`, con la cinta cerca de 5 m. Si no lo ve: `tope de tiempo`, con más metros por cinta que por rf2o. Las dos salidas son resultado. |
| **Seguridad** | El tope de 40 s limita el recorrido a unos 10 m (0,26 m/s es la velocidad máxima medida). Una persona camina al lado, lista para levantar el carro. |
| **Después** | Cinta desde la raya de salida hasta el eje delantero, **antes de tocar el carro**. La grabación queda en `~deepracer/mapeo_<hora>/`: copiarla al portátil y medir su información de avance con `python3 herramientas/medir_informacion_avance.py <carpeta del bag> /rplidar_ros/scan`. |
| **Cierre** | Por carro: metros por cinta, metros por rf2o, motivo de parada y la grabación en `~/tesis_evidencia/`. |

---

## 3. Bloque C — la pila con espacio de nombres

**Por qué:** el coordinador llama a `/robotN/navigate_to_pose` y lee `/robotN/odom`, con metas en el
marco `robotN/map`. Toda la navegación de esta semana corrió **sin** espacio de nombres. Es trabajo de
**despliegue** —lanzadores y parámetros—, no funcionalidad nueva, así que no rompe la congelación.

### C1 · En el escritorio (lunes y martes, Santiago)

> **Estado, 29-sep: hecho.** `nav2_hardware.launch.py` admite `namespace:=robotN`,
> `nav2_mapa_guardado.sh` admite `NS=robotN` y `correr_corrida_nav2.sh` graba los tópicos del `--ns`
> que recibe. [`prueba_nav2_hardware_ns.py`](../../herramientas/prueba_nav2_hardware_ns.py) lanza el
> lanzador en el portátil: con `robot2`, todos los nodos bajo `/robot2`, los YAML anidados y los
> marcos prefijados; sin espacio de nombres, cada nodo y cada parámetro igual que en el commit
> `6ef1642` (39 comprobaciones; con el lanzador de `6ef1642` fallan 10). El script de arranque, corrido
> con un `ssh` simulado, manda sin `NS` las mismas 23 órdenes que antes. `amcl` bajo `/robot2` lee el
> YAML anidado (comprobado en el portátil con un valor centinela). Falta C2 en el vehículo.

Lo que hay que cambiar, en [`nav2_hardware.launch.py`](../../Robot/aws-deepracer/deepracer_bringup/launch/nav2_hardware.launch.py)
y en [`nav2_mapa_guardado.sh`](../../herramientas/nav2_mapa_guardado.sh):

- Un argumento `namespace`, que meta todos los nodos bajo `/robotN`.
- **Prefijo `robotN/` en los marcos** que son nuestros —`map`, `odom`, `base_link`— y en los de la
  URDF, como hace la simulación.
- Una **TF estática identidad `robotN/laser → laser`**: el driver de AWS pone el barrido en `laser` y
  no se puede cambiar. En la TF privada de cada carro no choca con el otro.
- El puente de servos, con espacio de nombres y `-r /cmd_vel:=/robotN/cmd_vel`: su suscripción es
  absoluta y, sin el remapeo, los dos puentes escucharían el mismo `/cmd_vel`.
- [`correr_corrida_nav2.sh`](../../herramientas/correr_corrida_nav2.sh) graba `/odom`, `/cmd_vel`, `/plan`,
  `/amcl_pose`… **sin** espacio de nombres: con `/robot2` el bag saldría sin ellos y sin avisar. Tiene
  que grabar los del espacio de nombres que se le pase.

**Se prueba sin carro**, como el 25-sep: construyendo el lanzamiento en el portátil y leyendo los
parámetros efectivos de cada nodo. **Cierre:** con `namespace:=robot2`, todos los nodos bajo
`/robot2`, todos los marcos con prefijo, y el modo sin espacio de nombres idéntico al de ahora.

### C2 · Un carro con espacio de nombres (miércoles, `amss-ez9n`)

| | |
|---|---|
| **Objetivo** | Que el carro navegue exactamente como lo va a mandar el coordinador. |
| **Comando** | Arranque con `NS=robot2` (con `amss-jgm9`, `NS=robot1`), y una meta con la herramienta de campaña, que ya admite espacio de nombres: `correr_corrida_nav2.sh c2_01 --ns /robot2 --marco robot2/map --salida 0.70 0.0 0.0 --avance 3.0 --mapa …` |
| **Esperado** | La misma navegación de las corridas del martes, con todo bajo `/robot2`. |
| **Cierre** | Una corrida con plan consumido y llegada, y `tf2_echo robot2/map robot2/base_link` resolviendo **con el perfil cargado**. |

### C3 · Los dos carros a la vez (jueves, en el laboratorio)

| | |
|---|---|
| **Objetivo** | Lo que hoy no se puede: los dos encendidos, cada uno navegando lo suyo. |
| **Esperado** | Cada carro llega a su meta; ninguno se mueve con las órdenes del otro; cada odometría a ~7 Hz de láser. |
| **Cierre** | Una meta cumplida en cada carro con el otro encendido y navegando. **Es la primera vez que los dos se mueven a la vez.** |

---

## 4. Bloque D — la red entre pisos (lunes a miércoles, Jonny)

Las medidas de los mundos de Gazebo son las del edificio real, así que el sistema navega sobre los
mapas del modelo sin validarlos aparte (aclarado por el equipo el 28-sep).

### D1 · La red entre pisos

**Por qué:** con un carro en el piso 1 y otro en el 2, el coordinador los tiene que alcanzar a los
dos. Nadie ha medido si la red llega de un piso a otro.
Procedimiento: el de RF-15 —[`HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](HOJA_CAMPO_SEGUNDO_DEEPRACER.md)—, con un
carro en cada piso, en los puntos donde van a estar durante una misión.

**Cierre:** `CUMPLE` del medidor con los carros en pisos distintos. **Si no cumple**, el relevo entre
pisos no se puede hacer así, y es lo primero que hay que llevar al director.

---

## 5. Bloque E — el coordinador y la interfaz en un carro (jueves)

**Por qué:** el coordinador **no puede correr en el portátil** —la acción de Nav2 no es compatible
entre Humble y Jazzy (decisión D6)—, así que corre en `amss-jgm9`, como en G-4. Y la interfaz del
teléfono llega a él por `rosbridge`.

| Paso | Qué | Cierre |
|---|---|---|
| E0 | Llevar a los dos carros el coordinador con la tolerancia por condición (2026-09-28). Antes, `ssh deepracer@192.168.0.104 "ls ~/coordinacion_ws/src"` debe listar `coordinacion`; si no, parar y avisar. Luego `scp -r Robot/aws-deepracer/coordinacion deepracer@192.168.0.104:~/coordinacion_ws/src/` y `ssh deepracer@192.168.0.104 "source /opt/ros/jazzy/setup.bash && cd ~/coordinacion_ws && colcon build --packages-select coordinacion"`; lo mismo con `192.168.0.102` | `md5sum` de `coordinador.py` y `registrador.py` igual en el repositorio y en los dos carros |
| E1 | ¿Está `rosbridge` en los carros? `ssh deepracer@192.168.0.104 "source /opt/ros/jazzy/setup.bash; ros2 pkg list \| grep rosbridge_server"`. Si no, `sudo -n apt-get update && sudo -n apt-get install -y ros-jazzy-rosbridge-suite` **en los dos** | el paquete en los dos |
| E2 | Coordinador y `rosbridge` en `amss-jgm9`, agentes en los dos, la interfaz desde un teléfono conectado a la red de los carros. El coordinador, **con `condicion:=hardware`**: `ssh -t deepracer@192.168.0.104 "sudo -n bash -c 'cd ~deepracer/coordinacion_ws && source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p condicion:=hardware -p ruta_puntos:=src/deepracer_bringup/config/puntos_interes.yaml'"`. Si la ruta del catálogo no existe, buscarla con `ssh deepracer@192.168.0.104 "find ~ -name puntos_interes.yaml"` | la interfaz muestra los dos robots, y el coordinador escribe al arrancar `condicion 'hardware': la llegada se acepta a 0.5 m o menos` |
| E3 | **Una misión dentro de un mismo piso, pedida desde el teléfono**, con un solo carro moviéndose | el registro de la misión, compuesto con `componer_registro.py` |

E3 es el **ensayo general de G-5 sin el relevo**. Depende de C2: si el miércoles no se cerró, E pasa
al lunes 5.

> La tolerancia de llegada depende de la condición desde el 28-sep: 0,25 m en simulación y 0,5 m en
> los vehículos. Sin `condicion:=hardware`, el coordinador aplica 0,25 m en el carro y una misión que
> pare entre 0,25 y 0,5 m se cierra como `FALLIDA`. Al componer el registro de E3, `--banco fisico`.

---

## 6. Bloque F — decisiones del director (resuelto el lunes 28)

Los tres puntos se trataron directamente con el director, Armando Mateus, el 28-sep, en lugar de
enviar el mensaje escrito. Lo acordado quedó en el §6.1 de [`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md):

| # | Decisión | Lo acordado |
|---|---|---|
| 1 | Sitio de la etapa 3 | Se mantienen los pasillos reales del edificio, los mismos de la simulación. Si aparecen novedades, por ejemplo en la red entre pisos, se ven cambios y adaptaciones con él |
| 2 | N de RF-27 | Sin número fijo: se elige según cómo salgan las primeras corridas del sistema completo |
| 3 | Tolerancia de llegada | 0,5 m en los vehículos reales; la simulación conserva 0,25 m. Enmienda en el §3.3 de [`PROTOCOLO_EXPERIMENTAL.md`](../PROTOCOLO_EXPERIMENTAL.md) |

---

## 7. Viernes 2 — corte C-1 y corte semanal

| | Qué | Dónde queda |
|---|---|---|
| 1 | **G-2 y G-3 declarados**, con cifras, en la tabla del §4.1 del acta | [`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md) |
| 2 | **Si alguna no se alcanzó**, se aplica lo escrito: NO-GO, RF-27 no alcanzable, la evidencia queda en la campaña de simulación. **No se reinterpreta el criterio** | ídem |
| 3 | **Decidir si S26 va con dos carros** (bloque A y C3 en verde) **o con el repliegue de uno** | [`MAPA_TRABAJO_RESTANTE.md`](MAPA_TRABAJO_RESTANTE.md) §0 |
| 4 | Corte semanal: `ESTADO.md`, entregable de S25 en `.tex` y `.md`, commit | `ESTADO.md`, `Documentos/Entregables/` |

> **Estado, 2-oct.** Las pruebas se hicieron ese día en el sitio nuevo, los pisos 3 y 4, que según el
> equipo aprobaron el director y los evaluadores. G-2 cumple en las dos corridas medidas del piso
> 4 (+3,3 % y −4,6 %); G-3 no (0,57 y 0,62 m). La declaración en el acta, el registro del cambio de
> sitio y el entregable de S25 quedan pendientes
> ([registro](../Evidencia/S25_pisos34_campo.md)).

---

## 8. Lo que viene después

| Semana | Qué | Corte |
|---|---|---|
| **S26 · 5–9 oct** | **G-5: una misión completa desde el teléfono, con relevo entre pisos, sobre los dos carros.** Es el sistema real. Primera esquina navegada en hardware, si la ruta la tiene | **C-2, vie 9**: G-4, ya alcanzada. Decidir ese día, a más tardar, el repliegue a un solo carro si hiciera falta |
| **S27 · 12–16 oct** | **G-6 / RF-27:** las misiones que se fijen tras las primeras corridas del sistema completo (acta §6.1), con registro, y el vídeo de la demostración | **C-3, vie 16**: se cierra la toma de datos, pase lo que pase |
| S28 | Sustentación | — |

---

## 9. Los riesgos de la semana, y qué se hace si salen

| Riesgo | Señal | Qué se hace |
|---|---|---|
| **La partición no funciona en Jazzy** | A1 no da `PASA` | Plan B del diseño (§7): LiDAR y servos fuera de `deepracer-core`. Retrasa C3 y E; G-2 y G-3 no se ven afectadas, que son de un carro |
| **G-3 no entra en 0,5 m** | el error por cinta pasa de 0,5 m | Es un resultado, con mecanismo medido; va al director. Si el acta obliga a revertir, se revierte |
| **La red no llega de un piso a otro** | D1 no da `CUMPLE` | Es lo más grave para S26: sin red entre pisos no hay relevo. Llevarlo al director con el sitio (F1) |
| **Batería o disponibilidad de los carros** | un carro no enciende o cae | Los dos cargados el domingo por la noche; el jueves tiene holgura |
| **Algo se lanza sin el perfil** | un proceso no ve el láser y no avisa | Los scripts lo cargan solos; a mano, el `export` del recuadro de A2 |
