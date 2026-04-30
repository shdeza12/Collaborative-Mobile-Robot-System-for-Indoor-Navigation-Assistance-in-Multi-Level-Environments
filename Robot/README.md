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

## Resultados validados en simulación (Semana 12)

- Los 6 paquetes del repositorio compilan sin errores en ROS 2 Humble.
- El plugin Ackermann personalizado (`deepracer_drive_plugin`) funciona en
  Gazebo Classic 11.
- Los 7 controladores de `ros2_control` se cargan en estado activo:
  `joint_state_broadcaster`, controladores de las 4 ruedas y los 2 hinges
  de dirección.
- Sensores publicando: cámaras estéreo (`/zed_camera_*`), LiDAR (`/scan`).
- Movimiento físico verificado mediante `/cmd_vel` y odometría coherente
  publicada en `/odom`.

## Entorno de compilación

- Ubuntu 22.04 LTS
- ROS 2 Humble Hawksbill
- Gazebo Classic 11.10.2
- `ros2_control` y `ros2_controllers` en sus versiones para Humble

## Compilación

```bash
# Crear workspace y mover los paquetes
mkdir -p ~/deepracer_sim_ws/src
cp -r aws-deepracer ~/deepracer_sim_ws/src/

# Resolver dependencias
cd ~/deepracer_sim_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y

# Compilar
colcon build --symlink-install
source install/setup.bash
```

## Lanzamiento de la simulación

```bash
ros2 launch deepracer_bringup deepracer_sim.launch.py \
    world:=/usr/share/gazebo-11/worlds/empty.world
```

## Estructura de la carpeta

- `aws-deepracer/` — código del repositorio AWS con las modificaciones aplicadas.
- `README.md` — este archivo.

## Trabajo pendiente

- Modelado del entorno de la Universidad Santo Tomás en Gazebo (mundo SDF).
- Replicación del vehículo con namespaces (`/robot1`, `/robot2`) para el
  esquema colaborativo de relevo entre pisos.
- Integración del nodo de coordinación con el servidor central y el panel
  HRI vía `rosbridge_suite`.

## Referencias

- AWS DeepRacer repository: <https://github.com/aws-deepracer/aws-deepracer>
- ROS 2 Humble documentation: <https://docs.ros.org/en/humble/>
- ros2_control documentation: <https://control.ros.org/humble/>
