# Dos simuladores aislados — validación de factibilidad de H1

**Fecha:** 2026-08-10 · **Semana:** S17 · **Hito:** H1

Cierre del bloqueo descrito en `S17_aplicacion_contrato.md` §E.2: dos robots dentro de un mismo
`gzserver` no se pueden aislar por namespace, porque `gazebo_ros` de Humble aplica a todos los
plugins el namespace del primer modelo cargado.

La solución no es un parche al código, sino un cambio de topología: **un proceso `gzserver` por
robot**, cada uno en su propio `ROS_DOMAIN_ID` y su propio `GAZEBO_MASTER_URI`.

Este documento registra las mediciones que demuestran que esa topología es viable en el hardware
disponible, y las pruebas funcionales que demuestran que resuelve el aislamiento.

## Por qué esta topología y no otra

El anteproyecto (cap. 2 y 4.3) nunca exige que los dos agentes compartan espacio físico. Dice lo
contrario: *"cada robot opere de forma dedicada en un nivel específico"*, y coordinándose
*"a través de un servidor"*. El relevo está definido en el glosario (6.3.4) como
*"transferencia secuencial de responsabilidad entre agentes en puntos definidos"* — un evento
lógico, no un encuentro físico.

Simular cada nivel en un proceso separado es por tanto la traducción fiel del alcance, no un rodeo
para esquivar la limitación de `gazebo_ros`. Además mapea 1:1 al despliegue final previsto: cada
DeepRacer con su propia Raspberry Pi 4 y su propio dominio ROS.

## Entorno de medición

| | |
|---|---|
| CPU | AMD Ryzen 5 PRO 5650U (6 núcleos / 12 hilos, 15 W) |
| RAM | 13 GiB (8.9 GiB disponibles en reposo) |
| GPU | Radeon integrada (Cezanne), 2048 MiB de VRAM compartida |
| SO / ROS | Ubuntu 22.04 · ROS 2 Humble · `rmw_fastrtps_cpp` |
| Gazebo | Classic 11.10.2 |
| Mundo | `primer_piso.world` en ambas instancias |

## Cómo se lanzan dos instancias

Instancia 1 (dominio por defecto, puerto 11345):

```
herramientas/lanzar_sim.sh primer_piso.world namespace:=robot1
```

Instancia 2 — las dos variables de entorno son lo único que cambia:

```
GAZEBO_MASTER_URI=http://localhost:11346 ROS_DOMAIN_ID=2 ros2 launch deepracer_bringup deepracer_sim.launch.py world:=$HOME/Documents/Tesis/primer_piso.world namespace:=robot2 y:=2.0
```

`GAZEBO_MASTER_URI` separa los dos Gazebo; `ROS_DOMAIN_ID` separa los dos grafos ROS.
No hizo falta ningún cambio en el código ni en los `.xacro`.

## Resultado 1 — aislamiento del grafo ROS

`ros2 node list --no-daemon` en cada dominio (el flag es obligatorio: el daemon conserva nodos
fantasma, ver `S17_aplicacion_contrato.md` §E.3).

| Dominio 0 | Dominio 2 |
|---|---|
| 14 nodos, todos bajo `/robot1` | 14 nodos, todos bajo `/robot2` |
| `/robot1/scan`, `/robot1/odom`, `/robot1/cmd_vel` | `/robot2/scan`, `/robot2/odom`, `/robot2/cmd_vel` |
| 7 controladores `active` | 7 controladores `active` |

Ningún dominio ve un solo tópico del otro. Con un `gzserver` único, en cambio, ambos robots
compartían un único `/scan` y un único `/odom`, y la prueba de aislamiento ni siquiera podía
plantearse.

Los 7 controladores del robot2 los cargó su propio launch sin intervención manual, mientras el
robot1 ya estaba corriendo: los dos `controller_manager` son independientes.

## Resultado 2 — movimiento independiente

Prueba: publicar `cmd_vel` a un robot y leer la odometría de ambos antes y después.
`cmd_vel` es velocidad, no distancia, así que hay que **detener explícitamente** cada robot antes
de medir; si no, sigue rodando con el último comando y contamina la lectura del testigo.

| Prueba | Robot comandado | Testigo |
|---|---|---|
| `cmd_vel` a `/robot1/cmd_vel` (dominio 0) | robot1 avanzó **3.34 m** | robot2 se movió **6 mm** |
| `cmd_vel` a `/robot2/cmd_vel` (dominio 2) | robot2 avanzó **2.73 m** | robot1 se movió **1 mm** |

Los milímetros del testigo son deriva numérica del solver, no movimiento comandado.
**El aislamiento exigido por H1 queda demostrado en ambos sentidos.**

## Resultado 3 — rendimiento

El *real-time factor* se midió comparando el avance de `/clock` contra el reloj de pared
(`herramientas/medir_rtf.py`), no con `gz stats`: con dos instancias es fácil que `gz stats`
apunte al master equivocado.

| Escenario | RTF | Carga (de 12 hilos) | RAM añadida | GPU | VRAM |
|---|---|---|---|---|---|
| 1 simulación + ventana | 0.999 | — | 490 MB | — | — |
| **2 simulaciones + 2 ventanas** | **0.998 / 0.998** | 4.7 | 955 MB | 67 % | 1168 / 2048 MB |
| 2 simulaciones sin ventanas | — | 4.6 | 640 MB | **22 %** | 821 MB |
| Añadir Nav2 (una instancia) | — | +1.13 núcleos | +349 MB | 51 % | 1035 MB |

El *swap* no se tocó en ningún momento (0 MB de 2048 MB).

**Conclusión de rendimiento:** las dos simulaciones corren a tiempo real simultáneamente. Las
métricas de tiempo del objetivo 4 no quedan contaminadas por falta de cómputo.

**El cuello de botella no es la CPU sino la VRAM de la GPU integrada.** Con las dos ventanas de
Gazebo abiertas se consume más de la mitad de la VRAM disponible; añadir dos RViz agotaría el
margen. La operación por defecto debe ser *headless*, que baja el uso de GPU del 67 % al 22 %.

## Resultado 4 — el remapeo de `/clock` funciona (dato de reserva)

Se evaluó también la alternativa de un **único** `ROS_DOMAIN_ID` con dos `gzserver`. El obstáculo
sería `/clock`, que Gazebo publica en la raíz absoluta y que ambos simuladores disputarían.

Prueba: con un reloj falso publicado en `/robot9/clock` a partir de t=5000 s, y Gazebo publicando
su reloj real en `/clock`:

| Nodo | Lectura de `get_clock().now()` |
|---|---|
| `use_sim_time:=true -r /clock:=/robot9/clock` | **5010.76 s** (el reloj remapeado) |
| `use_sim_time:=true` sin remapeo | 645.45 s (el reloj de Gazebo) |

El remapeo de `/clock` **sí** es respetado por `rclpy`. La opción de dominio único es por tanto
viable, pero se descarta: con dominios separados no hace falta remapear nada en ningún nodo.
Se deja registrado por si en el futuro se necesita que ambos robots compartan grafo.

## Hallazgos colaterales

1. **`nav_amcl_demo_sim.launch.py` no soporta namespaces.** Cero apariciones de `namespace` en el
   archivo. Al lanzarlo, `global_costmap` falla en bucle con
   `Invalid frame ID "map" ... frame does not exist`, porque busca `base_link` y `map` sin prefijo
   mientras el robot publica `robot1/base_link`. **Es el siguiente trabajo bloqueante:** sin esto
   los dos robots no navegan.

2. **`herramientas/lanzar_sim.sh` asume una sola instancia.** Mata todos los `gzserver` al arrancar
   y solo comprueba el puerto 11345. Necesita aceptar puerto y dominio como parámetros.

3. **El daemon de ROS 2 vuelve a corromperse tras `pkill -9`.** Los `ros2 control load_controller`
   fallaron con `xmlrpc.client.Fault: <class 'RuntimeError'>:!rclpy.ok()`. Se resuelve con
   `ros2 daemon stop && ros2 daemon start`. Refuerza lo ya documentado en §E.3.

4. **`rosbridge_suite` y `domain_bridge` están disponibles en apt pero no instalados**
   (`ros-humble-rosbridge-suite` 2.0.7, `ros-humble-domain-bridge` 0.5.0). El primero es la vía
   prevista para el servidor coordinador, coherente con las herramientas que lista el anteproyecto
   (7.2: *JavaScript, PHP, HTML*).

## Criterio de cierre

Cumplido. Dos robots simulados de forma independiente, con grafos ROS disjuntos, movimiento
mutuamente aislado y ambos a tiempo real en el hardware disponible. H1 deja de estar bloqueado.

## Cómo refutar este resultado

Si alguien sospecha que el aislamiento es aparente, basta con esto: lanzar las dos instancias,
publicar `cmd_vel` solo en `/robot1/cmd_vel` y comprobar `/robot2/odom`. Si el robot2 se desplaza
más de unos milímetros, el aislamiento es falso y este documento está equivocado.
