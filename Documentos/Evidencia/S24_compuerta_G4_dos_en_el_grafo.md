# Compuerta G-4: los dos vehículos y el coordinador en el mismo grafo

*2026-09-22. Hardware real, los dos carros. Adelanto sobre el corte C-2 (vie 9 oct).*

## 0. Qué pide la compuerta, y por qué se adelanta

El §4 del `ACTA_GO_NOGO.md` enuncia G-4 así:

> «Los dos vehículos y el coordinador coexisten sin colisión de nombres, y el coordinador
> registra a los dos agentes.»

Su corte es **C-2, viernes 9 de octubre**, y si no se alcanza *«el GO pleno no es alcanzable; se
revierte a un vehículo real»*. Se adelanta diecisiete días porque **no depende de G-2 ni de G-3**:
el `agente` publica su estado aunque la TF falle —está documentado en su propio docstring— y el
coordinador crea sus clientes de navegación sin necesidad de que exista un servidor al otro lado.
Es decir, G-4 es comprobable hoy, sin odometría y sin Nav2, y comprobarla ahora quita de la ruta
crítica la única compuerta que puede tumbar el GO pleno por una razón de arquitectura y no de
sensor.

## 1. Montaje

| Pieza | Máquina | Orden |
|---|---|---|
| `agente` en `/robot1` | `amss-jgm9` (192.168.0.101) | `ros2 run coordinacion agente --ros-args -r __ns:=/robot1` |
| `agente` en `/robot2` | `amss-ez9n` (192.168.0.102) | `ros2 run coordinacion agente --ros-args -r __ns:=/robot2` |
| `coordinador` | `amss-jgm9` (192.168.0.101) | `ros2 run coordinacion coordinador --ros-args -p ruta_puntos:=…/puntos_interes.yaml` |

Los tres corren bajo **ROS 2 Jazzy**, sobre el `~/coordinacion_ws` compilado en cada carro. El
coordinador va en una máquina Jazzy y no en el portátil por la **decisión D6** del acta:
`nav2_msgs/NavigateToPose` no es el mismo tipo en Humble y en Jazzy, así que lo que se porta es el
código fuente, no la interoperabilidad del grafo.

## 2. Las medidas

Cada fila se tomó **desde las dos máquinas**, no desde la que aloja el nodo: una comprobación que
solo pasa en `localhost` no dice nada sobre un sistema de dos vehículos.

| Qué se mide | Por qué | Resultado | Qué decide |
|---|---|---|---|
| `/robot1/estado` y `/robot2/estado` | Los dos agentes tienen que estar vivos y a la frecuencia que pide RF-08 | **2,004 Hz** y **2,027 Hz** desde `.101`; **2,002 Hz** y **4,054 Hz** desde `.102` (véase §4) | Los dos agentes publican y se ven a través de la red |
| Nombre y espacio de nombres del publicador de cada `estado` | Es la prueba literal de «sin colisión de nombres» | `agente` en `/robot1` y `agente` en `/robot2` | Dos nodos con **el mismo nombre** conviven porque el espacio de nombres los separa. Es lo que la compuerta pregunta |
| Suscripción del coordinador a `/robot1/odom` y `/robot2/odom` | Es la forma en que el coordinador «registra» a un agente: una suscripción de odometría por espacio de nombres | `Subscription count: 1`, `Node name: coordinador` en **los dos** tópicos, con `Publisher count: 0` | El coordinador registró a los dos agentes |
| Clientes de acción de navegación | El otro medio de registro: un `ActionClient` por robot | `/robot1/navigate_to_pose` y `/robot2/navigate_to_pose` en `ros2 action list`, con sus tres servicios `_action/` cada uno | El coordinador tiene enganche de navegación a los dos, a la espera de servidor |
| `/coordinacion/estado_mision` | El coordinador debe latir a 1 Hz, como fija el §4 del acta | **1,002 Hz** desde `.101`, **1,062 Hz** desde `.102` | El coordinador publica y **cruza de máquina** |
| `/coordinacion/puntos_interes` | Catálogo *latched*: lo que consumirá la HRI, que se conecta mucho después | **31 identificadores** recibidos en `.102`, coincidiendo con el `Coordinador listo. 31 puntos` del log en `.101` | El *latch* funciona entre máquinas distintas |
| `/coordinacion/guiar_usuario` | El servidor de acción por el que entra una misión | Visible desde `.101` y desde `.102` | La interfaz de entrada del sistema existe en el grafo compartido |

Log de arranque del coordinador, textual:

```
[WARN]  1 puntos son PROVISIONALES y no valen para la campana de OE4: piso2_escalera
[INFO]  Coordinador listo. 31 puntos, asignacion {1: 'robot1', 2: 'robot2'}
```

**La compuerta G-4 queda ALCANZADA.** Es la segunda de las seis, tras G-1, y la primera que se
cierra antes de su corte por un margen de semanas.

## 3. Requisito de despliegue descubierto: el catálogo no se encuentra solo

El primer arranque del coordinador **murió**:

```
PackageNotFoundError: "package 'deepracer_bringup' not found"
```

`_cargar_catalogo` recurre a `get_package_share_directory("deepracer_bringup")` cuando el parámetro
`ruta_puntos` viene vacío. En los carros, `deepracer_bringup` se copió como **carpeta de
configuración sin `package.xml`**, así que colcon la ignoró y no existe como paquete instalado.

No se fabricó un `package.xml` para tapar esto: el nodo ya declara `ruta_puntos` precisamente para
que la ruta pueda darse explícita, y en el carro **esa es la forma correcta**, porque instalar el
paquete entero de *bringup* arrastraría launch files de Humble que allí no se usan.

**Queda como requisito de despliegue:** en hardware, el coordinador se lanza **siempre** con
`ruta_puntos` apuntando al `puntos_interes.yaml` en disco. El respaldo por paquete solo vale en el
portátil.

## 4. Dos instrumentos que volvieron a mentir, y un error mío

Se anotan porque hoy ya costaron tiempo dos veces y conviene que no cuesten una tercera.

| Síntoma | Qué era en realidad | Cómo se detectó |
|---|---|---|
| `/robot2/estado` daba **SIN DATOS** desde `.101` mientras el agente de `.102` corría y registraba | El **demonio `ros2` de `.101` servía una vista rancia**. Tras `ros2 daemon stop` el tópico apareció a 2,027 Hz | Medir el mismo tópico desde la máquina que lo publica |
| `ros2 node list --no-daemon` devolvió **un solo nodo** habiendo tres | La introspección de nodos con este transporte es incompleta. Es el mismo instrumento que hoy devolvió 21, 15, 10 y 0 en corridas sucesivas | Contraste con `ros2 topic info --verbose`, que sí nombró a los tres |
| «`/robot2/estado`: SIN DATOS» medido **en la propia `.102`** | **Error mío:** `--no-daemon` no es argumento válido de `ros2 topic hz`; el comando abortó con código 2 y mi `grep` leyó el mensaje de uso como ausencia de datos | Volver a correr sin filtrar la salida |

**La regla que se consolida:** para decidir si un tópico está vivo, `ros2 topic info --verbose` y
`ros2 topic hz` son fiables; `ros2 node list` no lo es. Y ninguna salida filtrada por `grep` vale
como medida si no se ha mirado antes el código de salida del comando.

### La frecuencia doble

`/robot2/estado` midió **4,054 Hz** en la primera pasada, exactamente el doble de lo esperado.
La causa era que yo había lanzado el `agente` **dos veces** en `.102`; `ps` mostró dos procesos con
la misma línea de órdenes. Al matar uno, la frecuencia volvió a 2,027 Hz.

Importa más de lo que parece: **dos instancias del mismo agente no producen ningún error, ni en el
log ni en el grafo** —solo duplican la tasa de un tópico—. En la campaña de OE4 eso falsearía
cualquier métrica basada en el estado del robot sin dejar rastro. El único indicio es la
frecuencia, así que **medir `ros2 topic hz` antes de cada corrida es control de calidad, no
trámite**.

## 5. Qué NO prueba esta compuerta

Conviene decirlo, porque la tentación de leer G-4 como más de lo que es resulta evidente:

- **No hay odometría.** Los dos agentes registran `TF robotN/map -> robotN/base_link no disponible`
  cada diez segundos. Eso es **G-2**, y su corte es C-1, viernes 2 de octubre.
- **No hay navegación.** `Publisher count: 0` en los dos `/odom` y cero servidores detrás de los
  `navigate_to_pose`: el coordinador tiene los clientes creados y nadie al otro lado. Eso es **G-3**.
- **No hay relevo.** Ningún robot entregó una misión a otro. Eso es **G-5**.

G-4 responde una sola pregunta —¿caben los tres en un grafo y se reconocen?— y la responde que sí.

## 6. Discrepancia menor detectada al verificar

La celda de **RF-15** en `REQUISITOS.md:118` sitúa a `amss-jgm9` en **192.168.0.100**. Hoy ese
carro responde en **192.168.0.101**, comprobado con `ssh … hostname` contra las dos IP. La medida
de latencia de RF-15 no queda invalidada —se hizo carro↔carro y el veredicto no depende del último
octeto—, pero **el dato publicado no describe la red de hoy**. Se anota aquí en vez de editar la
celda en silencio, que es exactamente la práctica que abrió el riesgo R6.

## 7. Trazabilidad

| Afirmación | Fuente |
|---|---|
| Enunciado y corte de G-4 | `ACTA_GO_NOGO.md`, §4 fila G-4 y §5 fila C-2 |
| El coordinador debe correr en una máquina Jazzy | Decisión **D6** del acta: portabilidad de fuente, no del grafo |
| El agente publica aunque la TF falle | Docstring de `Robot/aws-deepracer/coordinacion/coordinacion/agente.py` |
| El coordinador crea un `ActionClient` y una suscripción a `/odom` por espacio de nombres | `coordinador.py:139-146` |
| `estado_mision` a 1 Hz es exigencia del acta | `coordinador.py:134`, comentario `# 1 Hz, como pide el §4` |
| El catálogo se busca en `deepracer_bringup` si `ruta_puntos` va vacío | `coordinador.py:195-204` |
| Frecuencia de `/robotN/estado` exigida por RF-08 | `REQUISITOS.md:65` |
| `amss-jgm9` responde en 192.168.0.101 | `ssh deepracer@192.168.0.101 hostname`, hoy |
| El demonio `ros2` ya había servido vistas rancias hoy | `S24_sonda_actuacion_amss_ez9n.md`, §9.2 |
| G-1 alcanzada en los dos carros | `S24_sonda_actuacion_amss_ez9n.md`, §9.3 |
