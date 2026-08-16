# Robot — Plataforma de simulación AWS DeepRacer (ROS 2 Humble)

Esta carpeta contiene el código fuente de la plataforma robótica utilizada en el
proyecto, basada en el repositorio open source de AWS DeepRacer y migrada a
**ROS 2 Humble** sobre **Ubuntu 22.04**.

## Contexto

El anteproyecto plantea inicialmente el uso de plataformas tipo DonkeyCar como
base experimental. Durante las semanas S10–S11 se identificó que el ecosistema
de simulación de DonkeyCar no es compatible con ROS 2 ni con Gazebo Classic,
lo cual impedía cumplir los requisitos de simulación previa a las pruebas
físicas. Como respuesta a esta limitación, se adoptó el modelo del vehículo
**AWS DeepRacer**, manteniendo la cinemática Ackermann y el espíritu de bajo
costo y código abierto del proyecto original. La unidad de cómputo se
reemplazará por una Raspberry Pi 4 en la fase de implementación física.

## Origen del código

- Repositorio fuente: <https://github.com/aws-deepracer/aws-deepracer>
- Licencia: Apache 2.0 (se conserva el archivo `LICENSE` y `NOTICE` originales)
- Versión ROS 2 original: Foxy
- Versión ROS 2 destino: Humble

## Modificaciones realizadas (migración Foxy → Humble)

### 1. Sintaxis de carga de controladores

- **Archivos:** `deepracer_bringup/launch/deepracer_spawn.launch.py`,
  `deepracer_bringup/launch/teleop_test_launch.py`
- **Cambio:** `'--set-state', 'start'` → `'--set-state', 'active'`
- **Razón:** `ros2_control` en Humble cambió las opciones válidas; el estado
  `start` fue reemplazado por `active`.

### 2. Renombrado del controlador joint state

- **Archivos:** los dos launch files anteriores y
  `deepracer_bringup/config/agent_control.yaml`
- **Cambios:**
  - `joint_state_controller` → `joint_state_broadcaster`
  - `joint_state_controller/JointStateController` →
    `joint_state_broadcaster/JointStateBroadcaster`
- **Razón:** el paquete `joint_state_controller` fue deprecado y reemplazado
  por `joint_state_broadcaster` en `ros2_controllers` desde Humble.

## Resultados validados en simulación

**Semana 12 — la migración funciona:**

- Los 6 paquetes del repositorio compilan sin errores en ROS 2 Humble.
- El plugin Ackermann personalizado (`deepracer_drive_plugin`) funciona en
  Gazebo Classic 11.
- Los 7 controladores de `ros2_control` se cargan en estado activo:
  `joint_state_broadcaster`, controladores de las 4 ruedas y los 2 hinges
  de dirección.
- Sensores publicando: cámaras estéreo (`/zed_camera_*`), LiDAR (`/scan`).
- Movimiento físico verificado mediante `/cmd_vel` y odometría coherente
  publicada en `/odom`.

**Semana 15 — SLAM 2D** con `slam_toolbox` sobre el mundo del primer piso.
Procedimiento en [`Documentos/guia_simulacion_slam.md`](../Documentos/guia_simulacion_slam.md).
El mapa resultante **no** pasa `herramientas/verificar_mapa.py`: es el riesgo R10
de [`ESTADO.md`](../ESTADO.md), abierto.

**Semana 17 — navegación autónoma y dos agentes:** AMCL y la pila Nav2 con
planificador Smac Hybrid-A\* y árboles de comportamiento sin `<Spin>`, por la
restricción Ackermann; y `namespace:=robotN`, que aísla nodos, tópicos y marcos
TF de cada agente. Con `namespace` vacío el comportamiento es el de un solo robot,
sin prefijos. Evidencia en
[`Documentos/Evidencia/S17_nav2_namespaces.md`](../Documentos/Evidencia/S17_nav2_namespaces.md).

## Entorno de compilación

- Ubuntu 22.04 LTS
- ROS 2 Humble Hawksbill
- Gazebo Classic 11.10.2
- `ros2_control` y `ros2_controllers` en sus versiones para Humble

## Compilación

El procedimiento completo —dependencias, variables de entorno y verificación— está en el
[`README.md` de la raíz](../README.md). Deliberadamente **no se duplica aquí**: dos copias de
unas instrucciones divergen, y quien instala acaba siguiendo la equivocada.

> **Nunca copiar esta carpeta al workspace.** La versión anterior de este archivo decía
> `cp -r aws-deepracer ~/deepracer_sim_ws/src/`, y eso provocó el incidente registrado como R7:
> durante semanas se compiló una copia mientras se editaba el repositorio, de modo que los
> arreglos de SLAM nunca llegaron a ejecutarse y toda la cartografía tomada en ese periodo quedó
> invalidada. El workspace **enlaza** la carpeta con `ln -s`; no la copia.

## Lanzamiento de la simulación

Los comandos de uso —mapeo, navegación y modo de dos robots— están en el
[`README.md` de la raíz](../README.md#uso), por el mismo motivo que la instalación:
una sola copia. Para comprobar solo que el vehículo aparece y se mueve, basta el
mundo vacío que trae Gazebo:

```bash
ros2 launch deepracer_bringup deepracer_sim.launch.py \
    world:=/usr/share/gazebo-11/worlds/empty.world
```

### Configuraciones de RViz

Están versionadas en `deepracer_description/rviz/` y se instalan con el paquete, de modo
que se abren por su ruta en `share` sin depender de dónde se clonó el repositorio:

| Archivo | Para qué | Marco fijo |
|---|---|---|
| `urdf_config.rviz` | Ver el modelo del vehículo y su árbol TF, **sin mapa y sin navegación**: sirve para comprobar que el URDF carga y que las 7 articulaciones están donde deben. Escucha `/robot_description` sin espacio de nombres | `base_link` |
| `nav2_robot1_view.rviz` | El vehículo sobre el mapa bajo el espacio de nombres `robot1`. Es la configuración con la que se tomó la evidencia de S17; el detalle está en [`S17_nav2_namespaces.md`](../Documentos/Evidencia/S17_nav2_namespaces.md) | `map` |

```bash
rviz2 -d "$(ros2 pkg prefix deepracer_description)/share/deepracer_description/rviz/urdf_config.rviz"
```

Un modelo que no se ve no siempre es un modelo que no cargó: `urdf_config.rviz` distingue
los dos casos antes de meter Nav2 de por medio.

## Estructura de la carpeta

- `aws-deepracer/` — código del repositorio AWS con las modificaciones aplicadas.
- `README.md` — este archivo.

## Trabajo pendiente

El estado vigente, con avance por objetivo y riesgos abiertos, está en
[`ESTADO.md`](../ESTADO.md); esta lista solo recoge lo que falta **en el código
del robot**:

- Nodo de coordinación contra el servidor central, según
  [`Documentos/CONTRATO_INTERFACES.md`](../Documentos/CONTRATO_INTERFACES.md).
- Panel HRI web vía `rosbridge_suite`.
- Instrumentación de las métricas de OE4.
- Bring-up sobre los DeepRacer físicos (`deepracer-custom-car`), pendiente de
  resolver el desajuste Humble ↔ Jazzy (riesgo R8).

## Referencias

- AWS DeepRacer repository: <https://github.com/aws-deepracer/aws-deepracer>
- ROS 2 Humble documentation: <https://docs.ros.org/en/humble/>
- ros2_control documentation: <https://control.ros.org/humble/>
