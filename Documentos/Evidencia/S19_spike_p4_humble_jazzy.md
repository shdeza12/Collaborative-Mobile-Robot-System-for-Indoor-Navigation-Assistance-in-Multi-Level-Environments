# Spike de hardware, pregunta 4 — ¿qué cambia entre ROS 2 Humble y Jazzy?

**Semana 19 · 2026-08-18.** Caracteriza el riesgo **R8** de [`../../ESTADO.md`](../../ESTADO.md) §4 y
verifica el requisito **RF-16** de [`../REQUISITOS.md`](../REQUISITOS.md) §3.

La simulación corre sobre **ROS 2 Humble** (Ubuntu 22.04, Gazebo Classic 11). Los dos DeepRacers
corren `deepracer-custom-car` sobre **Ubuntu Server 24.04 con ROS 2 Jazzy** (confirmado
2026-08-14). El desajuste es un hecho desde entonces; lo que faltaba era **medir su tamaño**,
porque de eso depende la decisión **D6**: *«el código se escribe una vez contra un contrato de
interfaces ROS 2 y se despliega en dos destinos»*.

Esta pregunta se eligió primero, de las cuatro del spike, por dos razones: **no necesita hardware
encendido** —así que el riesgo R11 (un vehículo en intervención técnica) no la bloquea— y es la
única que puede invalidar una decisión de arquitectura ya tomada.

---

## 1. Método

No se instaló Jazzy ni se encendió ningún vehículo. El método es comparar, elemento por elemento,
**lo que este repositorio usa de verdad** contra **las fuentes oficiales de cada distribución**.
Solo se comparó lo que el proyecto emplea: una lista de diferencias entre distribuciones sin
filtrar por uso propio es un catálogo, no un diagnóstico.

Fuentes, todas públicas y citables:

| Fuente | Para qué |
|---|---|
| `docs.nav2.org/migration/Humble.rst` (Humble → Iron) y `Iron.rst` (Iron → Jazzy) | Cambios declarados por los propios mantenedores |
| Rama `jazzy` de `ros-navigation/navigation2` | Comprobar en el código, no en la guía, qué parámetros existen |
| Rama `jazzy` de `ros-controls/ros2_control` | Argumentos de `ros2 control load_controller` |
| `ros/rosdistro`, `humble/distribution.yaml` y `jazzy/distribution.yaml` | Qué paquetes están liberados en cada distro y en qué versión |
| `ros2/common_interfaces`, ramas `humble` y `jazzy` | Si los tipos de mensaje del contrato cambian |
| `BehaviorTree.CPP` v4.5.1 | Comportamiento ante registro duplicado de nodos |

Reproducible con:

```bash
curl -sSL -o /tmp/Humble.rst https://raw.githubusercontent.com/ros-navigation/docs.nav2.org/master/migration/Humble.rst
curl -sSL -o /tmp/Iron.rst https://raw.githubusercontent.com/ros-navigation/docs.nav2.org/master/migration/Iron.rst
curl -sSL -o /tmp/NavigateToPose_humble.action https://raw.githubusercontent.com/ros-navigation/navigation2/humble/nav2_msgs/action/NavigateToPose.action
curl -sSL -o /tmp/NavigateToPose_jazzy.action https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_msgs/action/NavigateToPose.action
diff /tmp/NavigateToPose_humble.action /tmp/NavigateToPose_jazzy.action
```

> Nota sobre los nombres de archivo de la guía de migración: `Humble.rst` contiene *«Humble to
> Iron»* e `Iron.rst` contiene *«Iron to Jazzy»*. El archivo lleva el nombre de la distribución
> **de origen**. Confundirlos hace leer la guía equivocada.

---

## 2. El hallazgo que decide la pregunta

**La única interfaz de mando del contrato cambia de definición entre las dos distribuciones.**

`CONTRATO_INTERFACES.md` §2 fija siete interfaces por robot y establece que *«el coordinador manda
a un robot de una sola forma: llamando su acción `navigate_to_pose`»*. De esas siete:

| Interfaz | Tipo | ¿Idéntica en Humble y Jazzy? |
|---|---|---|
| `/<ns>/cmd_vel` | `geometry_msgs/Twist` | ✅ idéntica |
| `/<ns>/odom` | `nav_msgs/Odometry` | ✅ idéntica |
| `/<ns>/scan` | `sensor_msgs/LaserScan` | ✅ idéntica |
| `/<ns>/joint_states` | `sensor_msgs/JointState` | ✅ idéntica |
| `/<ns>/initialpose` | `geometry_msgs/PoseWithCovarianceStamped` | ✅ idéntica |
| `/<ns>/estado` | `coordinacion_msgs/EstadoRobot` | propio del proyecto: idéntico por construcción |
| **`/<ns>/navigate_to_pose`** | **`nav2_msgs/NavigateToPose`** | ❌ **difiere** |

Las cinco de `common_interfaces` se compararon archivo a archivo y son byte a byte iguales en las
ramas `humble` y `jazzy`. La séptima, la de mando, no:

```
#result definition                #result definition
                                  # Error codes
std_msgs/Empty result       →     uint16 NONE=0
                                  uint16 error_code
                                  string error_msg
```

El cambio viene de `PR #3251` (Humble → Iron, códigos de error) y `PR #3693` (Iron → Jazzy, mover
las enumeraciones del *goal* al *result*). La sección de objetivo y la de realimentación **no**
cambian; la de resultado sí.

**Consecuencia.** Un coordinador compilado en Humble y un robot corriendo Jazzy **no comparten la
interfaz por la que el contrato dice que se mandan**. No es una diferencia de parámetros que se
arregle editando un YAML: son dos tipos distintos con el mismo nombre. ROS 2 no garantiza
interoperabilidad entre distribuciones, y el modo de fallo esperable es el peor de los dos
posibles: **el cliente de acción sencillamente no encuentra servidor**, sin mensaje de error, igual
que pasó con `/robot1/scan` sin suscriptores el 12 de agosto.

**Esto refuta una frase concreta del contrato**, la que cierra su §2:

> *«Esto es lo que hace que un robot físico sea intercambiable con uno simulado sin tocar el
> coordinador.»*

No lo son, mientras el robot simulado sea Humble y el físico sea Jazzy. La intercambiabilidad que
el contrato promete es real **dentro de una distribución** y falsa entre ellas.

---

## 3. Lo que hay que cambiar en la configuración, con cuentas

Suponiendo que se despliegue Nav2 en el vehículo Jazzy con la configuración de este repositorio,
esto es lo que no sirve tal cual. Las cuatro columnas de la derecha son las cuentas exactas sobre
los cuatro YAML de Nav2 (`nav2_params.yaml`, `nav2_params_nav_amcl_sim_demo.yaml`,
`nav2_params_nav_amcl_dr_demo.yaml`, `nav2_slam_params.yaml`).

| # | Qué cambia | Cómo falla | Líneas |
|---|---|---|---|
| 1 | **Nombres de plugin con `/` pasan a `::`** (`PR #4220`): `nav2_smac_planner/SmacPlannerHybrid` → `nav2_smac_planner::SmacPlannerHybrid`; `nav2_behaviors/Spin\|BackUp\|Wait` → `nav2_behaviors::…`; `nav2_navfn_planner/NavfnPlanner` → `nav2_navfn_planner::…`; `dwb_core::DWBLocalPlanner` → `nav2_dwb_controller::DWBLocalPlanner` | **Ruidoso.** El servidor no encuentra la clase y no arranca | **17** |
| 2 | **`progress_checker_plugin` → `progress_checker_plugins`**, y el tipo pasa de `string` a lista (`PR #3555`, declarado *breaking change* en la guía) | **Silencioso.** El parámetro viejo se ignora y entra el *progress checker* por defecto | **4** |
| 3 | **`plugin_lib_names` ya incluye implícitamente todos los nodos BT de Nav2**; solo debe listar plugins propios | **Ruidoso, y por partida doble.** Los 22 nombres de la lista existen todavía en Jazzy —se comprobaron uno a uno contra el `CMakeLists.txt` de `nav2_behavior_tree`—, así que cada uno se registraría **dos veces**, y `BehaviorTreeFactory::registerBuilder` lanza `ID [...] already registered` (BT.CPP 4.5.1, `src/bt_factory.cpp:144`). El `bt_navigator` no configura | **4 listas** |
| 4 | **`enable_groot_monitoring`, `groot_zmq_publisher_port`, `groot_zmq_server_port` ya no existen** en el `bt_navigator` de Jazzy | **Silencioso.** El nodo declara `automatically_declare_parameters_from_overrides(true)`, así que los acepta y no hace nada con ellos: líneas muertas | **12** |
| 5 | **`behavior_server` separa `global_frame` de `local_frame`** (`PR #3255`). En Humble había un solo `global_frame`, con valor por defecto `odom`; en Jazzy `local_frame` vale `odom` y `global_frame` vale `map` | **Silencioso y del peor tipo:** la línea `global_frame: odom` del repositorio sigue siendo válida, pero **significa otra cosa** | **4** |
| 6 | **BehaviorTree.CPP pasa de 3.8 a 4.5+.** Los XML deben convertirse (`convert_v3_to_v4.py`) | **Ruidoso.** Los dos árboles Ackermann del proyecto están en formato v3 —`<root main_tree_to_execute="MainTree">`, sin `BTCPP_format="4"`— y no cargan | **2 archivos** |

Los dos árboles son `deepracer_bringup/behavior_trees/ackermann_navigate_to_pose.xml` y
`ackermann_navigate_through_poses.xml`. No son accesorios: son la adecuación Ackermann que quita
`<Spin>` del ciclo de recuperación, que es la mitigación de **R2**.

**Lectura de la tabla.** Los puntos 2, 4 y 5 son los peligrosos. No dan error: el sistema arranca,
navega y devuelve `SUCCEEDED`, con un *progress checker* que no es el configurado y un marco global
que no es el que se cree. Es exactamente el patrón que este proyecto ya ha pagado tres veces
—`initial_pose` como lista muerta, `/scan` absoluto bajo namespace, `--set-state start`— y por eso
existe la regla del 12 de agosto de no aceptar un `SUCCEEDED` como evidencia.

---

## 4. Lo que **no** cambia

Igual de importante, porque acota el trabajo:

- **`ros2 control load_controller --set-state active` sigue siendo válido** en Jazzy: el verbo
  declara `choices=["inactive", "active"]` (`ros2controlcli/verb/load_controller.py`). Los siete
  controladores se cargan igual. La migración Foxy → Humble no hay que volver a hacerla.
- **`geometry_msgs/Twist` sigue siendo el tipo por defecto de `cmd_vel`.** Jazzy añade
  `enable_stamped_cmd_vel`, pero **por defecto es `false`**. La suscripción de
  `cmdvel_to_servo_node.py` y la del plugin `deepracer_drive_plugin` siguen funcionando.
  ⚠️ Los mantenedores anuncian que `TwistStamped` pasará a ser el comportamiento por defecto: es
  una bomba de relojería para cualquier distribución posterior, no para Jazzy.
- **AMCL y las capas de costmap no tienen cambios de ruptura.** `nav2_costmap_2d::InflationLayer`,
  `::ObstacleLayer` y `::VoxelLayer` ya se escriben con `::` en este repositorio y siguen igual.
- **Los cinco tipos de `common_interfaces` del contrato son idénticos**, comprobado por resumen del
  archivo `.msg` en las dos ramas.

---

## 5. La simulación no puede migrar a Jazzy

La salida obvia al desajuste sería unificar: subir la simulación a Jazzy y acabar con el problema.
**No se puede**, y la razón está en `rosdistro`, no en una opinión:

| Paquete | Humble | Jazzy |
|---|---|---|
| `navigation2` | 1.1.20-1 | 1.3.12-1 |
| `slam_toolbox` | 2.6.10-1 | 2.8.5-1 |
| `ros2_control` | 2.54.0-1 | 4.47.0-1 |
| `ros2_controllers` | 2.54.0-1 | 4.42.1-1 |
| `robot_localization` | 3.5.4-1 | 3.8.3-1 |
| `rosbridge_suite` | 2.0.8-1 | 2.7.1-1 |
| `gazebo_ros_pkgs` | 3.9.0-1 | 3.8.0-1 *(más viejo que en Humble)* |
| **`gazebo_ros2_control`** | 0.4.10-1 | **no liberado** |

`gazebo_ros2_control` es el puente entre Gazebo Classic y `ros2_control`: es lo que hace que los
siete controladores del DeepRacer existan en simulación. **No está liberado para Jazzy**, y la
tabla de compatibilidad oficial de Gazebo empareja Jazzy con **Harmonic**, no con Classic. Migrar
la simulación significaría además portar el plugin propio `deepracer_drive_plugin` —cinemática
Ackermann, escrito contra la API de Gazebo Classic— a otro simulador.

Que `gazebo_ros_pkgs` esté en Jazzy en una versión **anterior** a la de Humble confirma el
diagnóstico: el soporte de Classic ahí es mantenimiento, no desarrollo.

**Conclusión: la simulación se queda en Humble.** Deja de ser una preferencia y pasa a ser una
restricción con fuente.

---

## 6. Veredicto sobre D6 y RF-16

**D6 no se cumple como está escrita, y tampoco se cae. Hay que precisarla.**

D6 dice hoy: *«El código se escribe una vez contra un contrato de interfaces ROS 2 y se despliega en
dos destinos. Coordinación, relevo, HRI e instrumentación operan contra `/robot1/...` y
`/robot2/...` sin conocer el backend.»*

Lo que este spike establece:

1. **Como portabilidad de código fuente, D6 se sostiene.** El coordinador, el protocolo de relevo y
   la instrumentación se escriben una vez y compilan en las dos distribuciones. Los tipos propios
   (`coordinacion_msgs`) son idénticos por construcción y cinco de las siete interfaces del contrato
   no cambian.
2. **Como interoperabilidad en un mismo grafo ROS, D6 es falsa.** Un coordinador Humble y un robot
   Jazzy no se hablan por `navigate_to_pose`, que es la única vía de mando que el contrato admite.
3. **El despliegue son dos mundos cerrados**, y el proyecto ya estaba organizado así sin haberlo
   dicho: **D1** manda la campaña de N=30 a simulación (todo Humble) y deja al hardware la
   demostración funcional con N de 5 a 10 (todo Jazzy). Los dos mundos nunca necesitan hablarse.
   Lo que hay que escribir es que **no pueden**, no solo que no hace falta.

**RF-16 queda verificado con resultado condicionado:** el mismo *código fuente* se despliega en los
dos destinos; la *misma configuración* no. Hace falta un juego de parámetros por distribución —seis
diferencias, 37 líneas y 2 archivos XML— y los dos destinos no pueden coexistir en un grafo.

---

## 7. Consecuencias de planificación

- **Desaparece un respaldo que nadie había verificado.** Con un DeepRacer en intervención técnica
  (**R11**), la salida natural sería demostrar el relevo con **un robot físico y uno simulado**. Ese
  montaje **no funciona** por lo dicho en §2, y conviene saberlo ahora y no la semana de la
  demostración. Si se quisiera, exigiría un puente que traduzca la acción entre distribuciones:
  trabajo nuevo, no previsto, y en el camino crítico.
- **El contrato de interfaces necesita una corrección.** La frase de su §2 sobre intercambiabilidad
  quedó refutada. Es un documento interno del repositorio, no un entregable firmado: se corrige,
  con nota fechada. *(Lo que no se toca es el PDF entregado ni el acta; eso se comunica en el
  corte.)*
- **La configuración de Nav2 se bifurca.** No se mantiene un YAML que sirva a las dos: se mantiene
  el de Humble como fuente y se deriva el de Jazzy, con las seis diferencias de §3 aplicadas y
  anotadas. Un solo archivo intentando servir a dos distribuciones es la misma clase de error que
  una sola URI sirviendo a dos resolvedores, que costó S17 entera.
- **El coste está acotado y es pequeño**, y esa es la buena noticia del spike: 37 líneas de YAML,
  dos XML convertidos con un script que los propios mantenedores publican, y ninguna reescritura de
  código. Lo caro no era el desajuste: era no saber su tamaño.

---

## 8. Lo que queda por comprobar con hardware

Este spike es documental por diseño. Tres afirmaciones suyas deben confirmarse cuando haya un
vehículo disponible, y ninguna de las tres cambia el veredicto:

1. Que un cliente de acción Humble frente a un servidor Jazzy **no encuentra servidor** (frente a la
   alternativa peor: que se conecten y deserialicen mal el resultado). Se comprueba con
   `ros2 action list` y un cliente mínimo, en 10 minutos, en cuanto haya un vehículo encendido.
2. Que Nav2 en Jazzy arranca con la configuración corregida de §3.
3. Que `deepracer-custom-car` no impone además su propia versión de alguno de los paquetes de la
   tabla de §5.

Las preguntas 1 y 2 del spike (`/scan` con el LiDAR real, `/cmd_vel` desde ROS 2) siguen
pendientes y se responden con **un solo** vehículo. La pregunta 3 (latencia entre vehículos) sigue
supeditada a la reparación (**R11**).
