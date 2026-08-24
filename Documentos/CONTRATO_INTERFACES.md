# Contrato de interfaces ROS 2 — sistema colaborativo multi-robot

**Hito H1 · Semana 17 (3–9 ago 2026)**
Documento normativo. Todo lo que se escriba de S18 en adelante —nodo de coordinación, HRI web, bring-up físico— se escribe **contra estos nombres**, no contra lo que exista en el código en ese momento.

Referencia: `Documentos/CRONOGRAMA_S17_S32.md` (decisión **D6**: se escribe el código una sola vez contra un contrato de interfaces y se despliega sobre dos backends, simulación y hardware).

---

## 1. Regla general

Cada robot vive dentro de un **namespace propio**: `/robot1` y `/robot2`.
El nodo de coordinación y la HRI viven en `/coordinacion`.

**Nada fuera de esos tres namespaces.** No hay tópicos en la raíz salvo `/tf`, `/tf_static`, `/clock` y `/rosout`, que son globales por definición de ROS 2.

Consecuencia práctica: `/robot1` puede ser un robot simulado y `/robot2` uno físico, o los dos simulados, o los dos físicos. El nodo de coordinación no distingue. Ese es todo el punto de D6.

---

## 2. Interfaz de cada robot

`<ns>` es `robot1` o `robot2`.

| Nombre | Tipo | Dirección | Notas |
|---|---|---|---|
| `/<ns>/cmd_vel` | `geometry_msgs/Twist` | entra al robot | ya es relativo en el plugin |
| `/<ns>/odom` | `nav_msgs/Odometry` | sale del robot | ya es relativo en el plugin |
| `/<ns>/scan` | `sensor_msgs/LaserScan` | sale del robot | ya es relativo (`~/out:=scan`) |
| `/<ns>/joint_states` | `sensor_msgs/JointState` | sale del robot | vía `joint_state_broadcaster` |
| `/<ns>/navigate_to_pose` | acción `nav2_msgs/NavigateToPose` | **el coordinador la llama** | interfaz única de mando |
| `/<ns>/estado` | `coordinacion_msgs/EstadoRobot` | sale del robot | 2 Hz |
| `/<ns>/initialpose` | `geometry_msgs/PoseWithCovarianceStamped` | entra | inicialización de AMCL |

**El coordinador manda a un robot de una sola forma: llamando su acción `navigate_to_pose`.** No publica `cmd_vel`. No llama servicios internos de Nav2. Si algo no se puede expresar como "ve a esta pose", no entra en la coordinación.

Esto es lo que hace que un robot físico sea intercambiable con uno simulado sin tocar el coordinador.

> ⚠️ **Refutado el 2026-08-18, y se deja escrito en vez de borrarlo.** La frase anterior es cierta
> **dentro de una distribución** y falsa entre ellas. `nav2_msgs/NavigateToPose` —la única vía de
> mando que este contrato admite— **cambia de definición entre Humble y Jazzy**: en Humble el
> resultado es `std_msgs/Empty`; en Jazzy es `uint16 error_code` y `string error_msg`. Como la
> simulación es Humble y los dos vehículos son Jazzy, un coordinador no puede mandar **a la vez** a
> un robot simulado y a uno físico: no es un desajuste de parámetros, son dos tipos distintos con
> el mismo nombre, y el fallo esperable es que el cliente de acción **no encuentre servidor**, sin
> mensaje de error.
>
> Lo que el contrato sí garantiza, y sigue siendo su razón de ser: **las otras seis interfaces de
> la tabla son idénticas en las dos distribuciones** —comprobado archivo a archivo—, así que el
> mismo **código fuente** del coordinador sirve para los dos destinos. Lo que no puede es servirlos
> simultáneamente. Método y fuentes en
> [`Evidencia/S19_spike_p4_humble_jazzy.md`](Evidencia/S19_spike_p4_humble_jazzy.md); la decisión
> **D6** quedó precisada en consecuencia en [`ESTADO.md`](../ESTADO.md) §3.

---

## 3. Marcos TF

**Todos los marcos de cada robot llevan el prefijo del namespace, incluido `map`.**

```
robot1/map ── robot1/odom ── robot1/base_link ── robot1/laser
                                              └─ robot1/camera_link

robot2/map ── robot2/odom ── robot2/base_link ── robot2/laser
                                              └─ robot2/camera_link
```

Son **dos árboles TF independientes y desconectados**. No hay transformación entre `robot1/map` y `robot2/map`, y no hace falta que la haya.

**Por qué**, y esto conecta con la decisión **D2** del cronograma: cada robot opera en un nivel distinto y **ningún robot cruza nunca entre niveles**. La transición entre pisos es un evento lógico del protocolo de relevo, no un movimiento físico. Un marco global compartido resolvería un problema que el sistema no tiene, a cambio de complicar el bring-up.

**Alternativa descartada:** un `map` único con dos `map_piso1`/`map_piso2` colgando. **Se mantiene descartada, con otro motivo — el original caducó el 2026-08-14.**

> El argumento que estuvo escrito aquí decía que la relación métrica entre pisos «en el laboratorio GED es una ficción, porque D2 los aplana a dos zonas coplanares». Eso dejó de ser cierto cuando el entorno de evaluación pasó a `primer_piso_dos_niveles.world`: los dos niveles son la misma planta desplazada **3,0 m exactos en z**, así que la relación métrica no solo existe, es exacta y conocida. Un argumento correcto sobre un mundo que ya no se usa es un argumento falso.

Los motivos que sí se sostienen sobre el entorno vigente son tres:

1. **No compra nada.** Ningún robot cruza de nivel (D2), así que **ninguna consulta del sistema pide jamás una transformada entre los dos mapas**. Un marco que nadie consulta es solo coste de mantenimiento.
2. **Acopla lo que costó aislar.** Con un árbol compartido, la divergencia de `map`→`odom` de un AMCL entra en el árbol que consume el otro robot. Con dos árboles desconectados el aislamiento es **verificable**, y así se verificó en S17: 62 tópicos por dominio, ninguno cruzado.
3. **Las dos plantas son geométricamente idénticas y el LiDAR no las distingue** — un robot caído al nivel 1 daría el mismo `/scan`. Con marcos separados el nivel es una **identidad** del agente, no una coordenada que se pueda confundir. Esa distinción es la que obligó a comprobar la altitud del nivel 2 (z constante a 1,9 micrómetros) en vez de darla por buena.

**Relación entre niveles:** vive en datos, no en TF. Ver §5.

---

## 4. Interfaz de coordinación

| Nombre | Tipo | Quién llama / escucha |
|---|---|---|
| `/coordinacion/guiar_usuario` | acción `coordinacion_msgs/GuiarUsuario` | la HRI la llama |
| `/coordinacion/estado_mision` | `coordinacion_msgs/EstadoMision` | la HRI la escucha, 1 Hz |
| `/coordinacion/puntos_interes` | `coordinacion_msgs/ListaPuntosInteres` (latched) | la HRI la escucha al cargar |

> **Corregido el 2026-08-24.** Esta fila decía `coordinacion_msgs/PuntoInteres[]`, y **ese tipo no se puede publicar**: un tópico de ROS 2 transporta un mensaje, no un arreglo — `PuntoInteres[]` es sintaxis válida para un *campo*, no para un tipo. Salió al construir el paquete, no al escribir el contrato, y afectaba también al §5, que cerraba con «cuatro definiciones, nada más». El envoltorio `ListaPuntosInteres` es la quinta. *Latched* aquí sí es lo correcto —el catálogo no caduca y la HRI se conecta mucho después de que arranque el coordinador—, al revés que en `amcl_pose`, donde el mismo QoS engañó dos veces ese mismo día porque una pose vieja sí parece actual. **La regla que separa los dos casos: se retienen catálogos, nunca medidas.**

La HRI **no habla con los robots**. Solo con `/coordinacion`. Eso mantiene el `rosbridge` con una superficie mínima y permite cambiar la asignación de robots sin tocar el frontend.

### Flujo completo de una misión

1. La HRI llama `guiar_usuario(origen_id, destino_id)`.
2. El coordinador determina el nivel de origen y el de destino desde `puntos_interes.yaml`.
3. Envía el robot del nivel de origen al punto de origen (`navigate_to_pose`).
4. Lo envía al **punto de transferencia** de su nivel.
5. Al llegar, publica el relevo en `estado_mision` y envía el robot del segundo nivel al punto de transferencia de *su* nivel.
6. Segundo tramo hasta el destino.
7. `result`: éxito, tiempo total, número de relevos.

Si origen y destino están en el mismo nivel, los pasos 4–6 se omiten: **un solo robot, cero relevos**. El coordinador debe manejar ese caso sin ramas especiales en la HRI.

---

## 5. Mensajes propios

Paquete **`coordinacion_msgs`** (en `Robot/aws-deepracer/`). Cinco definiciones, nada más.

**Existe desde el 2026-08-24**, compilado en Humble y verificado con un round-trip real por DDS —`coordinacion_msgs/test/prueba_round_trip.py`, 18 de 18—, no solo con que compile: el paquete tiene que correr también en la tarjeta Jazzy del carro, y generar los headers no prueba que `rmw` transporte igual en las dos distribuciones. Las constantes (`LIBRE=0`…, `INACTIVA=0`…) se declaran en los `.msg` para que ningún nodo escriba el número suelto.

```
# EstadoRobot.msg
string robot_id                 # "robot1" | "robot2"
uint8 nivel                     # 1 | 2
geometry_msgs/PoseStamped pose  # en el marco <ns>/map
uint8 estado                    # LIBRE=0 NAVEGANDO=1 EN_TRANSFERENCIA=2 ERROR=3
string detalle                  # texto libre para diagnóstico
builtin_interfaces/Time stamp
```

```
# PuntoInteres.msg
string id                       # "piso1_escalera"
string nombre                   # "Escalera del primer piso"  <- lo que ve el usuario
uint8 nivel                     # 1  <- el ejemplo es la zona de transicion, en (41,40 . 3,03)
bool es_transferencia           # true en este caso; false en un destino corriente
geometry_msgs/Pose pose         # en el marco robotN/map del nivel correspondiente
```

```
# ListaPuntosInteres.msg  <- el catalogo entero, en UN mensaje publicable
string origen                   # ruta del YAML del que salio, para diagnostico
builtin_interfaces/Time stamp   # cuando se cargo
PuntoInteres[] puntos
```

```
# EstadoMision.msg
string mision_id
uint8 etapa                     # INACTIVA=0 TRAMO_1=1 TRANSFERENCIA=2 TRAMO_2=3 COMPLETADA=4 FALLIDA=5
string robot_activo
PuntoInteres destino_actual
float32 distancia_restante
string mensaje_usuario          # texto ya redactado en español para mostrar tal cual
```

```
# GuiarUsuario.action
string origen_id
string destino_id
---
bool exito
float32 tiempo_total_s
uint8 num_relevos
string motivo_fallo
---
EstadoMision estado
```

**`mensaje_usuario` va redactado desde el coordinador**, no desde el navegador. La HRI lo muestra literal. Evita duplicar lógica de presentación en JavaScript y mantiene el frontend tonto — que es lo que conviene con el tiempo que hay.

**Fuente de verdad de los puntos:** `deepracer_bringup/config/puntos_interes.yaml`. El coordinador lo carga y lo republica latched. La HRI arma sus dos listas desplegables (origen y destino) desde ahí. Eso cumple el requisito de **OE3 origen-destino** sin escribir un selector de mapa.

---

## 6. Qué hay que cambiar en el código para cumplir esto

Inventario real, hecho sobre el árbol actual. Lo bueno primero:

**Ya cumple, no se toca:**
- `deepracer_gazebo/src/gazebo_ros_deepracer_drive.cpp` — usa nombres **relativos** (`cmd_vel`, `odom`). Hereda el namespace solo.
- `deepracer_gazebo_lidar.xacro` línea 49 — `<argument>~/out:=scan</argument>`, también relativo.
- `deepracer.xacro` — ya declara `<xacro:arg name="agent_name" default="agent"/>`. Es el gancho que se necesita.

**Hay que tocar:**

| Archivo | Cambio |
|---|---|
| `deepracer_ros_control.xacro:40-41` | `odom` → `$(arg frame_prefix)odom`, `base_link` → `$(arg frame_prefix)base_link` |
| `deepracer_gazebo_lidar.xacro:52` | `<frame_name>laser</frame_name>` → `$(arg frame_prefix)laser` |
| `deepracer_spawn.launch.py` | aceptar `namespace` y pose inicial (hoy `-x 0 -y 0 -z 0.03` está fijo, línea 78); `PushRosNamespace`; `frame_prefix` en `robot_state_publisher`; prefijar los dos marcos del `static_transform_publisher` (línea 104) |
| `agent_control.yaml:17` | `controller_manager:` → `/**:` (comodín), porque bajo namespace la clave deja de coincidir |
| `deepracer_spawn.launch.py:40-74` | los 7 `load_controller` necesitan `-c /<ns>/controller_manager` |
| `nav2_params*.yaml` | `base_link`/`odom`/`map` → prefijados. **No editar a mano**: usar `nav2_common.launch.RewrittenYaml` en el launch, que es exactamente para esto |

**Nota sobre `robot_state_publisher`:** en Humble tiene parámetro `frame_prefix`, que prefija todos los marcos de los enlaces del URDF de un golpe. Eso cubre la mitad del trabajo. Los plugins de Gazebo publican sus propios marcos y **no** lo respetan — por eso las dos primeras filas de la tabla siguen siendo necesarias.

---

## 7. Qué NO cambia

Para que quede escrito y no se reabra:

- La cinemática Ackermann y el `deepracer_drive_plugin` — no se tocan.
- Los 7 controladores `ros2_control` en estado `active` — la migración de S12 se respeta.
- La configuración de Nav2 validada (Smac Hybrid-A*, árboles sin `<Spin>`, huella 0,28×0,19 m) — solo cambian nombres de marcos.
- El wall-follower — queda como evidencia de Fase 4, fuera del camino crítico.

---

## 8. Criterio de cierre de H1

> **Revisado el 2026-08-11.** La redacción original de esta sección daba por hecho que los dos
> robots compartirían un `gzserver` y un grafo ROS. Eso resultó **imposible**: `gazebo_ros` de
> Humble aplica a todos los plugins el namespace del primer modelo cargado
> (`Evidencia/S17_dos_simuladores.md`). La topología adoptada es un `gzserver` por robot, cada uno
> con su `ROS_DOMAIN_ID` y su `GAZEBO_MASTER_URI`, que además es la traducción fiel del alcance del
> anteproyecto —cada robot dedicado a un nivel, coordinación por servidor— y mapea 1:1 al
> despliegue final, una Raspberry Pi por vehículo. Las comprobaciones se reescriben en
> consecuencia: **cada una se ejecuta dos veces, una por dominio.**

El contrato se declara cumplido cuando, en simulación:

1. `ros2 topic list --no-daemon` en el dominio 0 muestra los tópicos de §2 bajo `/robot1` y
   **ninguno de `/robot2`**; y a la inversa en el dominio 2. El flag es obligatorio: el daemon
   conserva nodos fantasma (§E.3 de `S17_aplicacion_contrato.md`).
2. `ros2 run tf2_tools view_frames` en cada dominio produce **un árbol de 12 marcos**, todos con
   el prefijo de su robot y raíz `map`, sin advertencias de marco repetido y **sin un solo marco
   del otro robot**.
3. Los 7 controladores de cada `controller_manager` reportan `active`, en los dos dominios.
4. Una llamada manual a `/robot1/navigate_to_pose` mueve a `robot1`, y la odometría de `robot2`
   —leída desde su propio dominio— no se altera más allá de la deriva numérica del solver.

Los puntos 1–4 son la prueba de que dos robots conviven. Sin eso, no se empieza el nodo de
coordinación.

**Qué no se demuestra aquí, y por qué no hace falta.** Los dos vehículos no comparten espacio
físico: están en procesos de simulación distintos y no pueden colisionar ni siquiera en principio.
Eso no es una carencia de la prueba sino el diseño: el anteproyecto define el relevo (6.3.4) como
*"transferencia secuencial de responsabilidad entre agentes en puntos definidos"* —un evento
lógico— y sitúa a cada robot *"de forma dedicada en un nivel específico"*. La ausencia de
interacción física es por tanto una **limitación declarada y deliberada**, no un resultado
pendiente de medir. Lo que sí hay que demostrar, y es el punto 4, es el **aislamiento de mando**:
que ordenar a uno no mueva al otro.

---

## 9. Trazabilidad

| Elemento del contrato | Objetivo específico | Actividad Cap. 8 |
|---|---|---|
| Namespaces + TF prefijados | OE1, OE2 | Integración del sistema |
| `navigate_to_pose` como mando único | OE1 | Navegación autónoma |
| `GuiarUsuario` + protocolo de relevo | OE1 | Coordinación multi-robot |
| `PuntoInteres` + listas origen-destino | OE3 | Interfaz de usuario |
| D6 / dos backends | OE2, OE4 | Pruebas en entorno controlado |
