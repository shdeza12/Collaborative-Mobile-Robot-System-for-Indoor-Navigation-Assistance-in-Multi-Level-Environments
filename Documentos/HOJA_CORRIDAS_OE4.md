# Hoja de corridas — campaña OE4 (simulación)

Hoja operativa para ejecutar a mano. El procedimiento normativo es
`RUNBOOK_CAMPANA.md`; esta hoja lo ordena para copiar y pegar, y **se separa de él en los
puntos declarados en el §6**.

Generada por `herramientas/generar_hoja_corridas.py` desde
`Documentos/Evidencia/campana_oe4_misiones.csv`. No se edita a mano: se regenera.

---

## 1. Tres cosas que rompen en silencio

**Cada terminal necesita su `source`.** Un shell nuevo de esta máquina **no** trae entorno ROS:
`ROS_DISTRO`, `PYTHONPATH` y `AMENT_PREFIX_PATH` salen vacíos y solo el binario `ros2` está en
`PATH`. Sin `source ~/deepracer_sim_ws/install/setup.bash`, `grabar_mision.sh` muere con
`PackageNotFoundError: ros2cli`, y en el caso peor `ros2 bag record` descarta `coordinacion_msgs`
sin decir nada y deja un bag con pinta de bueno. Los comandos de abajo llevan el `source` incluido.

**Un solo dueño para todo.** Los buzones de FastDDS en `/dev/shm` son `-rw-r--r--`, así que quien
levanta las pilas tiene que ser quien graba. Si dos usuarios distintos tocan la misma corrida, la
grabación sale vacía y no avisa. **Las cinco terminales, el mismo usuario.**

**Para parar el coordinador, el patrón va con BARRA.** `ros2 run` hace `exec` a la ruta instalada,
así que el proceso vivo se llama `.../lib/coordinacion/coordinador --ros-args ...`. El patrón con
espacio —`pkill -f "coordinacion coordinador"`— **no encuentra nada aunque haya tres corriendo**, y
quien lo lanza se queda creyendo que ya no hay ninguno. Así sobrevivió el coordinador de las 14:10
del 2026-09-04, que seguía sirviendo una hora después y arruinó la campaña (§5). El correcto:

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

Los corchetes tampoco sobran: sin ellos, `pkill` encuentra la propia orden que lo invoca y se mata
a sí mismo.

Y lo de siempre: **ninguna terminal exporta `ROS_DOMAIN_ID`**.

---

## 2. La ventana real es de 2,6 minutos

Medido el 2026-09-04 sobre las dos pilas en reposo, sin un solo `/cmd_vel`:

| | deriva lineal | deriva de yaw |
|---|---|---|
| robot1 | 19,1 mm/min | 3,7 °/min |
| robot2 | 18,9 mm/min | 4,0 °/min |
| tolerancia | 0,15 m | 10° |
| **se cruza a los** | **7,9 min** | **2,6 min** |

**Manda el yaw, no la posición.** El texto de diagnóstico de `verificar_condicion_inicial.py`
dice «a los ~9 min ya se sale de los 0,15 m» porque solo mira la componente lineal: engaña por un
factor de tres. Lo que hay que cumplir es **del spawn al `send_goal`, menos de 2,6 min**.

Por eso el §3 del runbook, ejecutado en serie, **no cabe**. Cronometrado en el intento fallido:

| hito | en serie | reordenado |
|---|---|---|
| amcl arriba | +14 s | +14 s |
| portón de los dos robots | +120 s | +70 s |
| coordinador listo | +157 s | +58 s (en paralelo) |
| `send_goal` | **+175 s — fuera** | **~+95 s — dentro** |

Los 58 s del coordinador incluyen los 3,0 s del guardián del §5, medidos.

---

## 3. Las cinco terminales

Las cinco desde la raíz del repositorio (`~/Documents/Tesis`), salvo donde el comando hace su
propio `cd`. Comprobación de que estás donde toca: `ls herramientas/robot.sh`.

| | para qué | trabaja desde |
|---|---|---|
| T1 | pila de robot1 | raíz del repo |
| T2 | pila de robot2 | raíz del repo |
| T3 | parar y arrancar el coordinador | workspace (el comando hace el `cd`) |
| T4 | portón, grabadora | raíz del repo |
| T5 | `send_goal` | workspace (el comando hace el `cd`) |

---

## 4. Cómo se usa esta hoja

**Cada misión del §7 y del §8 es un bloque completo**: lleva las cinco terminales, en orden, con el
nombre del bag y los identificadores ya puestos. No hay nada que sustituir y no hay que volver a
subir a esta sección. Se hace el bloque entero, de arriba abajo, y se pasa al siguiente.

`gzserver` **nuevo por misión, sin excepción** (§6.4 del runbook). Encadenar misiones sobre la misma
simulación ya costó una corrida: los robots acabaron a 23 m de su pose declarada y las llegadas
salieron perfectas igual, porque se miden contra `/odom`, que es continuo.

Lo que se espera en cada paso:

- **T1 y T2** tardan 28–35 s. Si `parar` avisa de procesos «que no lanzó `robot.sh`», mátalos con
  `kill -9` y repite.
- **T3** tiene que decir `Coordinador listo. 31 puntos, asignacion {1: 'robot1', 2: 'robot2'}`. Si
  dice un número distinto de 31, **para**: el sorteo y la corrida no son del mismo catálogo. El
  aviso de que `piso2_escalera` es provisional es normal y no bloquea. `ruta_registros` no va, ni
  en el piloto.
- **T4 portón**: `LISTA. Nav2, controladores, parametros y condicion inicial.` en los dos, con la
  desviación por debajo de 0,15 m y 10°. **Si uno se sale, relanza esa pila y empieza el bloque de
  nuevo. No se corrige a mano y no se sigue igual.** Si faltan controladores suele ser el spawner
  adelantándose a `gazebo_ros2_control`; si faltan nodos de Nav2, la carrera entre los dos
  `lifecycle_manager`. En los dos casos, relanzar basta.
- **T4 grabar**: `Grabando en ...` con el recuento de tópicos, y **ni un `AVISO`**. Déjala en primer
  plano. Deja tres cosas junto al bag: `rtf.json`, `condicion_inicial.json` y el bag; los dos
  primeros existen porque si no se escriben en el momento, no se escriben nunca.
- **T5**: `exito: true`, y `relevos: 0` en condición A, `relevos: 1` en B.

Un portón que falla **no es un descarte**: no se grabó nada, así que se repite el montaje. Una
misión que falla **sí es un resultado** y se registra; la lista de descartes del §8 del protocolo
está cerrada (`caida_gazebo`, `controladores_incompletos`, `rtf_bajo`, `fallo_anfitrion`) y un
fallo de navegación no está en ella.

---

## 5. Por qué hay un paso para parar el coordinador

El 2026-09-04 se perdieron dos misiones con `Nav2 termino con estado 6`. El estado 6 es `ABORTED`, y
la causa quedó medida ese mismo día con `herramientas/diagnosticar_aborto_nav2.py`:

| prueba | resultado |
|---|---|
| 20 goals directos a `/robot1/navigate_to_pose`, en limpio | **0 abortos** |
| 8 pares de goals seguidos al mismo servidor | **8 abortos** del desplazado, 9–13 ms |

`navigate_to_pose` atiende un goal a la vez: al desplazado lo termina en `ABORTED`. Y aquel día
había dos coordinadores vivos —el de las 14:10 seguía sirviendo a las 15:15— porque el comando que
se usaba para pararlos no coincidía con nada (§1).

Nav2 no tiene defecto y el coordinador tampoco: tiene un solo `send_goal_async` y ningún reintento,
así que uno no se pisa a sí mismo. Se pisaban dos.

Desde entonces el coordinador lleva un **guardián**: sondea `/coordinacion/guiar_usuario` antes de
construirse y, si ya hay alguien sirviendo, **se niega a arrancar** y sale con código 1 explicando
qué parar. Cuesta 3,0 s de arranque, medidos, y se desactiva con `-p espera_guardian_s:=0.0`.
Cubierto por `herramientas/prueba_guardian_coordinador.py`.

Si ves el mensaje del guardián, no es un fallo de la corrida: es el paso de parar el coordinador,
que se saltó. Párala, y repite el bloque desde el principio.

---

## 6. Dónde esta hoja se separa del runbook

Declaradas, para que la desviación quede en el papel y no en la costumbre:

1. **Los dos `esperar_nav2.sh` van en paralelo**, no encadenados con `&&` como pide el §3. No
   cambia ninguna comprobación —cada uno mira su robot— y ahorra ~50 s de los 156 que dura la
   ventana. Además es más correcto de medir: la desviación depende del tiempo que la pila lleva
   quieta, así que medir un robot después del otro sesga al segundo.

2. **No se repite `verificar_condicion_inicial.py` como paso suelto** después del portón, como
   pide el §3. `esperar_nav2.sh` ya lo invoca para su robot e imprime su salida entera; repetirlo
   no añade información y gasta ~8 s de ventana. Queda como herramienta de diagnóstico:
   `source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/verificar_condicion_inicial.py robot1 robot2`

3. **El coordinador arranca en paralelo con el portón**, no después. El §4 lo pone detrás del §3
   por orden de lectura, no por dependencia: el coordinador solo necesita `/clock` y el catálogo.

Pendiente: llevar los puntos 1 y 3, la ventana de 2,6 min y el patrón de `pkill` al propio
`RUNBOOK_CAMPANA.md`.

---

## 7. Pilotaje — tres corridas antes de la campaña

El protocolo pide **cinco** corridas de piloto; hay dos (`S21_piloto_A_02`, `S21_piloto_B_01`).
Faltan tres. Además, el bloque que escribe `condicion_inicial.json` se commiteó el 2026-09-04
(`cca442f`) y hasta ese día nunca había corrido contra un Gazebo vivo. Las dos cosas se cierran con
lo mismo.

Dos en B y una en A, para estrenar el relevo. Itinerarios tomados de las filas 2, 3 y 4 del
sorteo; el piloto no consume la fila, que se vuelve a correr en la campaña.

#### Piloto 1 — B · ETM7 → Aula 306  ·  relevos esperados: 1

Bag: `S21_piloto_B_02`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_piloto_B_02 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm7', destino_id: 'piso2_aula_306'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### Piloto 2 — A · ETM9 → ETM6  ·  relevos esperados: 0

Bag: `S21_piloto_A_03`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_piloto_A_03 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm9', destino_id: 'piso1_etm6'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### Piloto 3 — B · ETM6 → IEEE  ·  relevos esperados: 1

Bag: `S21_piloto_B_03`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_piloto_B_03 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm6', destino_id: 'piso2_ieee'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

---

## 8. Las 30 misiones

#### 1 — A · ETM2 → ETM11  ·  relevos esperados: 0

Bag: `S21_OE4_01`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_01 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm2', destino_id: 'piso1_etm11'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 2 — B · ETM7 → Aula 306  ·  relevos esperados: 1

Bag: `S21_OE4_02`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_02 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm7', destino_id: 'piso2_aula_306'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 3 — A · ETM9 → ETM6  ·  relevos esperados: 0

Bag: `S21_OE4_03`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_03 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm9', destino_id: 'piso1_etm6'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 4 — B · ETM6 → IEEE  ·  relevos esperados: 1

Bag: `S21_OE4_04`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_04 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm6', destino_id: 'piso2_ieee'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 5 — A · ETM6 → Representación  ·  relevos esperados: 0

Bag: `S21_OE4_05`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_05 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm6', destino_id: 'piso1_representacion'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 6 — B · ETM10 → Aula 303  ·  relevos esperados: 1

Bag: `S21_OE4_06`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_06 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm10', destino_id: 'piso2_aula_303'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 7 — B · ETM8 → Aula 309  ·  relevos esperados: 1

Bag: `S21_OE4_07`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_07 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm8', destino_id: 'piso2_aula_309'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 8 — B · ETM2 → Lab. Sistemas 312  ·  relevos esperados: 1

Bag: `S21_OE4_08`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_08 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm2', destino_id: 'piso2_lab_312'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 9 — B · ETM3 → Aula 302  ·  relevos esperados: 1

Bag: `S21_OE4_09`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_09 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm3', destino_id: 'piso2_aula_302'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 10 — A · ETM8 → ETM11  ·  relevos esperados: 0

Bag: `S21_OE4_10`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_10 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm8', destino_id: 'piso1_etm11'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 11 — B · Almacén ETM → IEEE  ·  relevos esperados: 1

Bag: `S21_OE4_11`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_11 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_almacen', destino_id: 'piso2_ieee'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 12 — B · ETM5 → Aula 311  ·  relevos esperados: 1

Bag: `S21_OE4_12`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_12 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm5', destino_id: 'piso2_aula_311'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 13 — B · ETM7 → Sala de Docentes Fac. Ing. Civil  ·  relevos esperados: 1

Bag: `S21_OE4_13`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_13 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm7', destino_id: 'piso2_sala_docentes_civil'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 14 — B · ETM13 → Aula 305  ·  relevos esperados: 1

Bag: `S21_OE4_14`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_14 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm13', destino_id: 'piso2_aula_305'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 15 — A · ETM3 → ETM7  ·  relevos esperados: 0

Bag: `S21_OE4_15`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_15 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm3', destino_id: 'piso1_etm7'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 16 — A · ETM10 → ETM4  ·  relevos esperados: 0

Bag: `S21_OE4_16`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_16 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm10', destino_id: 'piso1_etm4'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 17 — B · ETM1 → IEEE  ·  relevos esperados: 1

Bag: `S21_OE4_17`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_17 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm1', destino_id: 'piso2_ieee'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 18 — A · Representación → ETM6  ·  relevos esperados: 0

Bag: `S21_OE4_18`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_18 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_representacion', destino_id: 'piso1_etm6'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 19 — A · ETM9 → ETM2  ·  relevos esperados: 0

Bag: `S21_OE4_19`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_19 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm9', destino_id: 'piso1_etm2'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 20 — B · Almacén ETM → Aula 306  ·  relevos esperados: 1

Bag: `S21_OE4_20`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_20 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_almacen', destino_id: 'piso2_aula_306'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 21 — A · ETM1 → ETM3  ·  relevos esperados: 0

Bag: `S21_OE4_21`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_21 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm1', destino_id: 'piso1_etm3'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 22 — A · Almacén ETM → ETM1  ·  relevos esperados: 0

Bag: `S21_OE4_22`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_22 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_almacen', destino_id: 'piso1_etm1'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 23 — B · ETM3 → Aula 307  ·  relevos esperados: 1

Bag: `S21_OE4_23`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_23 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm3', destino_id: 'piso2_aula_307'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 24 — A · ETM10 → ETM8  ·  relevos esperados: 0

Bag: `S21_OE4_24`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_24 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm10', destino_id: 'piso1_etm8'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 25 — A · ETM10 → ETM1  ·  relevos esperados: 0

Bag: `S21_OE4_25`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_25 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm10', destino_id: 'piso1_etm1'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 26 — B · Representación → Sala de Docentes Fac. Ing. Civil  ·  relevos esperados: 1

Bag: `S21_OE4_26`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_26 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_representacion', destino_id: 'piso2_sala_docentes_civil'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 27 — A · ETM13 → ETM4  ·  relevos esperados: 0

Bag: `S21_OE4_27`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_27 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm13', destino_id: 'piso1_etm4'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 28 — B · Representación → Aula 311  ·  relevos esperados: 1

Bag: `S21_OE4_28`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_28 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_representacion', destino_id: 'piso2_aula_311'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 29 — A · ETM6 → ETM7  ·  relevos esperados: 0

Bag: `S21_OE4_29`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_29 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm6', destino_id: 'piso1_etm7'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

#### 30 — A · ETM7 → ETM2  ·  relevos esperados: 0

Bag: `S21_OE4_30`

**T3 — parar el coordinador de la misión anterior** (t = 0)

```bash
pkill -f "coordinacion[/]coordinador"; sleep 2; pgrep -f "coordinacion[/]coordinador" || echo "sin coordinadores vivos"
```

**T1 — pila de robot1** (t = 0)

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

**T2 — pila de robot2** (t = 0, lo más seguido que puedas tras T1)

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**T3 — coordinador** (~t+15 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21C
```

**T4 — portón, a la vez que T3** (~t+15 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && (herramientas/esperar_nav2.sh robot1 >/tmp/g1.log 2>&1 & herramientas/esperar_nav2.sh robot2 >/tmp/g2.log 2>&1 & wait); tail -n 9 /tmp/g1.log /tmp/g2.log
```

**T4 — grabar** (~t+75 s)

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_OE4_30 robot1 robot2
```

**T5 — lanzar** (~t+95 s)

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm7', destino_id: 'piso1_etm2'}"
```

**Al acabar:** Ctrl-C en **T4** primero, que cierra el bag; después Ctrl-C en **T3**. En ese orden:
cortar T4 antes de que la misión termine deja la misión sin su última marca. Anota número, hora,
`exito`, `relevos` y cualquier `AVISO`.

La condición A/B y los relevos que encabezan cada bloque son **lo esperado, no lo que se
declara**: el compositor deriva la condición de los niveles de origen y destino, y cuenta los
relevos desde `t_inicio_tramo2`. Si lo observado no coincide con el encabezado, eso *es* un
resultado y hay que mirarlo, no corregirlo.

---

## 9. Lo que me pasas a mí

Nada más que **los bags en `~/tesis_evidencia/`** y la nota de cada bloque. Yo corro, por cada uno:

```bash
python3 herramientas/diagnosticar_llegada.py ~/tesis_evidencia/S21_OE4_01 --robot robot1
python3 herramientas/componer_registro.py ~/tesis_evidencia/S21_OE4_01 --banco simulacion --campana OE4_simulacion --semilla 20260822 --salida Documentos/Evidencia/registros/S21_OE4_01.json
python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana OE4_simulacion
```

`analizar_campana.py` va **después de cada corrida**, no solo al final: es la única forma de
enterarse de que algo se registra mal en la corrida 2 y no en la 30. Si sale un error de
integridad, te aviso antes de que sigas.

Los pilotos llevan además `--piloto`; las 30 de la campaña **no** lo llevan.
