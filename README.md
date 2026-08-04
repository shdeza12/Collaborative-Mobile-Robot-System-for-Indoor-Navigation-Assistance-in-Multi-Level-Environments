# Sistema Robótico Colaborativo para Asistencia en Navegación en Interiores Multinivel

> Trabajo de grado — Ingeniería Electrónica
> Universidad Santo Tomás · Facultad de Ingeniería Electrónica
> GED (Grupo de Estudio y Desarrollo en Robótica)

Sistema colaborativo de dos robots móviles terrestres para la guía coordinada de visitantes
en entornos interiores con múltiples pisos. Cada agente opera en un nivel dedicado y un
servidor central asigna tareas dinámicamente, ejecutando un protocolo de relevo en la zona
de transición vertical. El usuario solicita su destino desde una interfaz móvil.

El aporte del proyecto es la **arquitectura de coordinación entre agentes**, no la locomoción.

El estado de avance detallado se mantiene en [`ESTADO.md`](ESTADO.md).

---

## Requisitos

| Componente | Versión |
|------------|---------|
| Sistema operativo | Ubuntu 22.04 LTS |
| Middleware | ROS 2 Humble Hawksbill |
| Simulador | Gazebo Classic 11 |
| Python | 3.10 |

Instalar ROS 2 Humble siguiendo la [guía oficial](https://docs.ros.org/en/humble/Installation.html),
y luego las dependencias de simulación:

```bash
sudo apt update && sudo apt install -y \
  gazebo libgazebo-dev \
  ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-teleop-twist-keyboard ros-humble-xacro ros-humble-rviz2 \
  python3-colcon-common-extensions python3-rosdep python3-pil
```

---

## Instalación

Los paquetes ROS 2 viven en `Robot/aws-deepracer/`. Para compilarlos se crea un workspace
de colcon que **enlaza** esa carpeta, de modo que el código compilado sea exactamente el
código versionado.

```bash
# 1. Clonar el repositorio
git clone https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments.git ~/Tesis

# 2. Crear el workspace y enlazar los paquetes
mkdir -p ~/deepracer_sim_ws/src
ln -s ~/Tesis/Robot/aws-deepracer ~/deepracer_sim_ws/src/aws-deepracer

# 3. Resolver dependencias
cd ~/deepracer_sim_ws
sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 4. Compilar
colcon build --symlink-install
source install/setup.bash
```

> **Importante:** usar un enlace simbólico y no una copia. Si se copia la carpeta, el código
> que se ejecuta deja de ser el que está bajo control de versiones y ambos divergen en
> silencio.

Cada terminal nueva necesita:

```bash
source ~/deepracer_sim_ws/install/setup.bash
```

---

## Uso

El procedimiento completo de mapeo está en
[`Documentos/guia_simulacion_slam.md`](Documentos/guia_simulacion_slam.md). Resumen de las
cuatro terminales:

**Terminal A — Gazebo y spawn del robot**

```bash
ros2 launch deepracer_bringup deepracer_sim.launch.py world:=$HOME/Tesis/primer_piso_v2.world
```

Verificar en el log que los **7 controladores** (`joint_state_broadcaster`, 4 ruedas y
2 hinges de dirección) queden en estado `active`.

**Terminal B — SLAM**

```bash
ros2 launch deepracer_bringup slam_toolbox.launch.py
```

**Terminal C — Teleoperación**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Terminal D — Visualización**

```bash
rviz2
```

En RViz: `Fixed Frame` = `map`, y en el display `Map` la propiedad
`Durability Policy` = `Transient Local` (con `Volatile` el mapa nunca llega).

---

## Guardar y verificar un mapa

En simulación, `map_saver_cli` requiere `use_sim_time`, de lo contrario agota su espera
antes de recibir el mapa:

```bash
ros2 run nav2_map_server map_saver_cli -f /tmp/mapa_candidato \
  --ros-args -p use_sim_time:=true
```

Antes de aceptar un mapa como definitivo, validarlo contra la geometría del mundo:

```bash
python3 herramientas/verificar_mapa.py /tmp/mapa_candidato.yaml primer_piso_v2.world
```

La herramienta compara la extensión mapeada con la del archivo `.world` y rechaza el mapa
si la cobertura es insuficiente. Devuelve código de salida distinto de cero cuando falla,
por lo que puede encadenarse en scripts.

---

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| `Robot/aws-deepracer/` | Paquetes ROS 2 del robot (ver [`Robot/README.md`](Robot/README.md)) |
| `Documentos/` | Anteproyecto, entregables semanales y guías operativas |
| `Documentos/Evidencia/` | Capturas y diagramas citados en los informes |
| `herramientas/` | Utilidades de verificación del proyecto |
| `*.world` | Mundos de Gazebo. El vigente es `primer_piso_v2.world` |
| `USTA_WORLD/`, `pasillo_grande/`, `pasillo_usta/` | Modelos SDF de entornos |
| `ESTADO.md` | Tablero de avance, riesgos y decisiones |

---

## Plataforma robótica

El modelo de vehículo proviene del proyecto open source
[AWS DeepRacer](https://github.com/aws-deepracer/aws-deepracer), migrado de ROS 2 Foxy a
Humble. Las modificaciones realizadas y la justificación del cambio de plataforma respecto
al anteproyecto están documentadas en [`Robot/README.md`](Robot/README.md).

El código de terceros conserva su licencia original Apache 2.0, junto con los archivos
`LICENSE` y `NOTICE`.

---

## Autores

- Santiago Hernández Ávila
- Jonny Alejandro Mejía León

**Directores:** Ing. Armando Mateus Rojas, MSc. · Ing. Nestor Ivan Ospina, MSc. ·
Ing. Oscar Mauricio Gélvez Lizarazo, MSc.
