# S20 — Hito H3: los dos agentes navegan a la vez, cada uno sobre su piso

**Fecha:** 2026-08-25. **Código base:** `d1d5157`.
**Cubre:** actividad 15 del cronograma (Hito H3). Cierra el hallazgo colateral nº4 de
[`S17_nav2_namespaces.md`](S17_nav2_namespaces.md) y abre dos defectos nuevos.

Lo que le faltaba al hito no era el aislamiento —eso quedó demostrado en S17— ni que cada robot
navegara sobre el mapa de su nivel —`robot1` el 21-ago, `robot2` el 24-ago—, sino **la corrida
con los dos a la vez**, que es la condición del hito. Y estaba bloqueada por un defecto que
habría contaminado el objetivo 4: una lectura de `/odom` que devolvió el desplazamiento del
otro robot.

Los dos agentes navegaron simultáneamente y llegaron. El `/odom` cruzado no se reprodujo, y la
razón por la que no se reproduce es concluyente. Midiendo la corrida aparecieron dos defectos
que no se conocían.

---

## Procedimiento

| | robot1 | robot2 |
|---|---|---|
| dominio ROS / puerto Gazebo | 0 / 11345 | 2 / 11346 |
| mundo | `mundo_definitivo_piso1.world` | `mundo_definitivo_piso2.world` |
| mapa | `mundo_definitivo_piso1.yaml` | `mundo_definitivo_piso2.yaml` |
| arranque declarado | (−19,165, +7,292) yaw 1,5708 | (−21,889, −8,379) yaw 0,0 |
| meta | `piso1_escalera` (−19,43, +5,91) | `piso2_escalera` (−21,50, −9,03) |

Las dos pilas se levantaron con `herramientas/robot.sh <robot> nav2`. Un `ros2 bag` por robot
—`/plan`, `/odom`, `/cmd_vel`, `/amcl_pose`, todos con su prefijo— arrancado **antes** de mandar
nada. Las dos metas salieron en paralelo desde una sola orden, cada una con su `ROS_DOMAIN_ID`,
de modo que los dos vehículos se movieron a la vez y no uno detrás de otro.

Las metas son **los dos puntos de transferencia**, que es el escenario colaborativo real: cada
robot espera en su escalera, y el relevo ocurre ahí. No son dos destinos escogidos por
comodidad.

Los dos devolvieron `SUCCEEDED`. Eso no se usa como resultado —regla del 12-ago—; lo que sigue
está medido contra `/odom`, que en esta simulación es la pose verdadera de Gazebo.

## Resultado 1 — los dos agentes navegan simultáneamente, y la concurrencia no degrada la navegación

| | robot1 (piso 1) | robot2 (piso 2) |
|---|---|---|
| error real de llegada | 0,281 m | **0,143 m** |
| recorrido / tiempo en movimiento | 1,67 m / 7,6 s | 1,75 m / 6,9 s |
| cúspides planificadas → ejecutadas | 1 → **3** | 1 → 1 |
| giro real contra comandado (RMS) | 0,178 rad/s | 0,140 rad/s |
| volante al tope | 43 de 105 (41 %) | 23 de 89 (26 %) |
| deriva en reposo | 0,0412 °/s | 0,0176 °/s |

La comparación que decide el hito es la de `robot2` contra su propia corrida de control, la del
24-ago, cuando corrió **solo**:

| `robot2` → `piso2_escalera` | solo (24-ago) | concurrente (25-ago) |
|---|---|---|
| error real de llegada | 0,190 m | **0,143 m** |

**Correr las dos pilas a la vez en la misma máquina no degradó la navegación**: el error bajó,
no subió. Con una corrida por condición esto no es una medida de efecto —la diferencia cabe
holgadamente en la variación entre corridas—, pero sí descarta la degradación gruesa que era la
preocupación: dos `gzserver`, dos Nav2 y dos AMCL compitiendo por CPU no dejaron al vehículo sin
control.

`robot1` gasta más volante y ejecuta **tres** cúspides donde el plan preveía una. Eso no es
concurrencia: es la maniobra Reeds-Shepp de R12, que ya estaba caracterizada. Su meta queda
detrás del arranque y con rumbo opuesto, así que el vehículo tiene que darse la vuelta; el
seguidor añade dos cúspides que el planificador no pidió. Es el trabajo del miércoles, no de
este hito.

## Resultado 2 — el `/odom` cruzado no se reproduce, y la causa era la herramienta, no la publicación

El hallazgo colateral nº4 de S17 dejaba dos causas candidatas: **el daemon de `ros2cli`
sirviendo datos de otro dominio**, o algo en la publicación de `/odom` bajo espacio de nombres.
La distinción importa porque la segunda contaminaría todas las métricas de OE4 y la primera solo
afecta a quien mide desde la línea de órdenes.

Con los dos robots quietos, cada uno en su dominio, y tras matar el daemon con `pkill -9`
—`SIGTERM` no lo mata, cosa que también hubo que descubrir—:

| | lectura de `/odom` | arranque declarado | distancia |
|---|---|---|---|
| robot1, dominio 0 | (−19,295, +7,174) | (−19,165, +7,292) | 0,175 m |
| robot2, dominio 2 | (−21,960, −8,244) | (−21,889, −8,379) | 0,153 m |

Cada uno sobre su propio arranque, con los dos puntos a **15,7 m** uno del otro: un cruce se
vería a simple vista y no está. Y el descubrimiento de tópicos lo confirma por el otro lado: el
dominio 0 no lista **ningún** tópico `/robot2/*` y el dominio 2 ninguno `/robot1/*`.

**Si los tópicos del otro robot no son visibles desde este dominio, ninguna lectura correcta
puede devolver sus datos.** La publicación de `/odom` bajo espacio de nombres queda descartada
como causa, y lo que queda es la capa de herramienta: el daemon. El hallazgo nº4 se cierra con
esa conclusión, y la mitigación provisional —leer con `--no-daemon`— se sustituye por la regla
más simple: **matar el daemon con `pkill -9` al cambiar de dominio**, o no usar `ros2 topic echo`
para medir. Las métricas de OE4 se calculan sobre bags, que no pasan por el daemon.

Las 17,5 y 15,3 cm de separación entre lo declarado y lo leído **no son deriva de odometría**:
son el asentamiento del modelo al nacer. Los dos robots reposan a `z = −0,007` y los dos se
desplazan una cantidad parecida. AMCL no lo sabe, porque su pose inicial es la declarada; se ve
en el Resultado 4.

## Resultado 3 — defecto nuevo: el vehículo sale de tolerancia después de haber llegado

En el instante en que la acción devolvió `SUCCEEDED`, `robot1` estaba a **0,243 m** de la meta.
El bag, cerrado más tarde, lo deja en **0,281 m**. Entre las dos lecturas no se publicó un solo
comando: el último `/cmd_vel` no nulo del bag cae en t = 132,0 s y la grabación llega a t = 225,1 s,
o sea **93 s sin ninguna orden**, durante los cuales el vehículo recorrió **4,0 cm**.

La `xy_goal_tolerance` es 0,25 m. O sea que el vehículo **cumplió la tolerancia al llegar y la
incumplió estando parado**, sin que nadie mandara nada y sin ningún aviso.

La causa es el mismo arrastre en reposo que aparece en la tabla del Resultado 1 y que ya se había
visto sin nombrarlo: entre dos lecturas separadas por unas horas, `robot1` se desplazó 8,7 cm
inmóvil. No es odometría que deriva —es el modelo de Gazebo que se mueve de verdad, y `/odom`
lo reporta bien.

**Por qué importa, y no es cosmético.** La tasa de éxito es una de las cuatro métricas de OE4, y
se define contra una tolerancia. Si el instante de la medición cambia el veredicto, la métrica no
está bien definida. Hay que fijar **cuándo** se lee la pose de llegada: en el instante del
resultado de la acción, o tras un tiempo de asentamiento declarado. Es una decisión de protocolo
—`PROTOCOLO_EXPERIMENTAL.md`— y hay que tomarla antes de la campaña de N = 30, no después.

Que `robot2` no lo sufra no es suerte: su deriva en reposo es 0,0176 °/s contra 0,0412 °/s, menos
de la mitad, y su margen a la tolerancia es de 10 cm en vez de 7 mm.

## Resultado 4 — AMCL se vuelve más seguro y más equivocado en la aproximación de `robot2`

El error de localización se mide como la distancia entre lo que cree AMCL y lo que dice `/odom`,
muestra a muestra:

| | robot1 | robot2 |
|---|---|---|
| primera muestra | 0,197 m (cov<sub>xx</sub> 0,70) | 0,102 m (cov<sub>xx</sub> 0,20) |
| mejor muestra | 0,007 m | 0,022 m (cov<sub>xx</sub> 0,15) |
| **última muestra** | **0,028 m** (cov<sub>xx</sub> 0,05) | **0,108 m** (cov<sub>xx</sub> 0,11) |
| peor tras converger | — | 0,152 m (cov<sub>xx</sub> 0,04) |

`robot1` hace lo que se espera de un filtro sano: el error baja de forma monótona mientras baja
la covarianza, de 0,197 m a 0,028 m.

`robot2` no. Converge bien hasta 0,022 m a media ruta y **desde ahí el error crece hasta 0,152 m
mientras la covarianza sigue cayendo**. El filtro se vuelve más confiado y más equivocado al
mismo tiempo, y eso ocurre exactamente en la aproximación final: de frente contra
`Barrera_Escalera`, con `yaw = π`, que es donde el cono ciego de 60° de **R13** apunta a la única
superficie nueva de esa zona del mapa.

Dos advertencias para no sobreinterpretar esto:

- **Es una corrida.** El 24-ago, en solitario y por la misma ruta, la descomposición con la TF
  `map → odom` dio 3,6 cm de error de localización. Hoy da 10,8 cm. La diferencia puede ser
  concurrencia, variación entre corridas, o que las dos cifras no midan lo mismo —la de ayer se
  obtuvo descomponiendo la TF y la de hoy comparando `amcl_pose` con `/odom`—. Hay que
  reconciliar las dos formas de medir antes de citar ninguna.
- **La mediana no sirve aquí.** `analizar_maniobra.py` imprimió 0,102 m de mediana para `robot2`
  y 0,101 m para `robot1`, dos cifras casi idénticas que sugieren un error común y no lo hay: la
  serie de `robot1` es decreciente y la de `robot2` tiene forma de U. La mediana de una serie no
  estacionaria esconde justo lo que interesa. **Para la campaña hay que reportar el error en la
  llegada, no la mediana del trayecto.**

Esto **no reabre R13** —sigue en 🟡, acotado— pero le da un segundo indicio en el mismo sitio y
con la misma geometría. Si la campaña de S24 va a exigir cerrada la pose de `piso2_escalera`,
esta es la medición que hay que repetir.

## Resultado 5 — defecto nuevo: el arranque en paralelo de los controladores pierde una activación

`robot2` levantó con **6 de 7** controladores. El faltante,
`right_steering_hinge_position_controller` —una de las dos bisagras de dirección—, aparecía en la
lista pero en estado `unconfigured`. `robot1`, lanzado con el mismo archivo y la misma
configuración, levantó 7 de 7.

Mismo lanzador y mismo resultado distinto: no es un error de configuración, es una carrera. La
causa está en `deepracer_spawn.launch.py`: el `joint_state_broadcaster` se carga solo y en orden
—eso está bien—, pero después los **seis controladores restantes se lanzan en paralelo**, seis
`ros2 control load_controller --set-state active` simultáneos contra un solo
`controller_manager`. El controlador queda **cargado**, por eso sale en la lista, pero la
activación se pierde.

Aparece ahora y no antes porque hoy es la primera vez que dos Gazebo y dos pilas Nav2 compiten
por la CPU: la carrera siempre estuvo, pero había margen para ganarla.

Se recupera en caliente respetando el ciclo de vida —desde `unconfigured` no se puede saltar a
`active`, hay que pasar por `inactive`, que es la transición que hace el `configure`—:

```bash
ROS_DOMAIN_ID=2 ros2 control set_controller_state right_steering_hinge_position_controller inactive -c /robot2/controller_manager && ROS_DOMAIN_ID=2 ros2 control set_controller_state right_steering_hinge_position_controller active -c /robot2/controller_manager
```

Las dos transiciones pasaron a la primera y `robot2` quedó en 7 de 7, lo que confirma el
diagnóstico: en secuencia funciona, en paralelo se pierde.

**La cura de fondo —secuenciar los seis spawners en el lanzador— no se aplicó**, porque
`deepracer_spawn.launch.py` lo usan los dos robots y todos los escenarios de la guía, y tocarlo
el día del hito habría metido una variable nueva en la medición. Queda como decisión pendiente.

**Por qué no se puede dejar así:** una bisagra de dirección inactiva no da error. El vehículo
arranca, Gazebo abre, Nav2 planifica y el carro se mueve; lo que cambia es la cinemática, en
silencio. Es el mismo patrón del mapa equivocado del 21-ago y de la pose de spawn del 20-ago:
falla sin ruido. Mientras el lanzador no lo arregle, **`robot.sh <robot> estado` y su «7 de 7» es
obligatorio antes de cualquier medición**, no una comprobación opcional.

## Correcciones de camino

Tres cosas que estaban mal y se vieron preparando esta corrida:

1. **`herramientas/analizar_maniobra.py` no leía bags con espacio de nombres.** Tenía los nombres
   de tópico escritos sin prefijo mientras la receta de `GUIA_EJECUCION.md` graba con él, así que
   abortaba con «sin mensajes en /odom» señalando al bag cuando el problema era el nombre. Ahora
   **deduce el prefijo del propio bag** mirando quién publica odometría, y rechaza con un mensaje
   explícito el bag que trae los dos robots mezclados —que no se puede analizar, porque no se sabe
   cuál llegó a la meta—. Probado contra cuatro bags sintéticos: con prefijo, sin prefijo, con dos
   robots y sin odometría.

2. **La receta de `GUIA_EJECUCION.md` manda la meta con `frame_id: map`**, y el marco real es
   `robot1/map`: los marcos globales llevan el prefijo del namespace desde el commit `25ec8fb`,
   como manda el contrato. La receta quedó atrás. **Pendiente de corregir en la guía.**

3. **Las dos holguras del piso 2 se contradicen solo en apariencia, y conviene dejarlo escrito**
   porque ya costó una falsa alarma. `puntos_interes.yaml` dice **1,50 m** y `ESTADO.md` dice
   **1,08 m**; parece que una de las dos quedó atrás y no es así: **son puntos distintos**. Los
   1,50 m son la **parada** `piso2_escalera` en (−21,50, −9,03), y los 1,08 m son el **arranque**
   de `robot2` en (−21,889, −8,379). Verificado con el criterio de
   `herramientas/verificar_pose_spawn.py` —celda ocupada = píxel < 65, distancia de centro a
   centro— sobre el `.pgm` regenerado del 24-ago: 1,500 m y 1,080 m respectivamente, las dos
   celdas libres. **No hay nada que corregir en ninguno de los dos archivos.**

## Qué queda abierto

- Decidir **cuándo se lee la pose de llegada** (Resultado 3). Bloquea la definición de la tasa de
  éxito de OE4.
- Reconciliar las dos formas de medir el error de localización —descomposición de la TF contra
  `amcl_pose` frente a `/odom`— y repetir la aproximación a `piso2_escalera` (Resultado 4).
- Decidir si se secuencian los seis spawners en `deepracer_spawn.launch.py` (Resultado 5).
- Corregir el `frame_id` de las metas en `GUIA_EJECUCION.md` (corrección 2).

## Reproducción

```bash
# Terminal 1 y 2: las dos pilas
herramientas/robot.sh robot1 nav2
herramientas/robot.sh robot2 nav2

# Comprobar 7 de 7 en las dos ANTES de medir
herramientas/robot.sh robot1 estado
herramientas/robot.sh robot2 estado

# Terminal 3 y 4: un bag por robot
cd ~/deepracer_sim_ws && source install/setup.bash && ROS_DOMAIN_ID=0 ros2 bag record -o /tmp/h3_robot1 /robot1/plan /robot1/odom /robot1/cmd_vel /robot1/amcl_pose
cd ~/deepracer_sim_ws && source install/setup.bash && ROS_DOMAIN_ID=2 ros2 bag record -o /tmp/h3_robot2 /robot2/plan /robot2/odom /robot2/cmd_vel /robot2/amcl_pose

# Terminal 5: las dos metas en paralelo
cd ~/deepracer_sim_ws && source install/setup.bash && { ROS_DOMAIN_ID=0 ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: robot1/map}, pose: {position: {x: -19.43, y: 5.91}, orientation: {z: -0.7071, w: 0.7071}}}}" & ROS_DOMAIN_ID=2 ros2 action send_goal /robot2/navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: robot2/map}, pose: {position: {x: -21.50, y: -9.03}, orientation: {z: 1.0, w: 0.0}}}}" & wait; }

# Ctrl-C en las dos grabaciones, y medir
python3 herramientas/analizar_maniobra.py /tmp/h3_robot1 -19.43 5.91
python3 herramientas/analizar_maniobra.py /tmp/h3_robot2 -21.50 -9.03
```
