# Replicar el proyecto

Todo el código es abierto. La forma más directa de ver el sistema funcionando es en **simulación**: dos agentes en Gazebo, uno por piso, con el coordinador y la página del teléfono. Con los **agentes físicos** hacen falta dos AWS DeepRacer y una red local.

!!! info "Qué se necesita"
    Ubuntu 22.04, ROS 2 Humble y Gazebo Classic 11. Un computador con 16 GB de memoria corre los dos procesos de simulación a tiempo real.

=== "En simulación"

    **1. Dependencias.** Instalar [ROS 2 Humble](https://docs.ros.org/en/humble/Installation.html) y luego:

    ```bash
    sudo apt install -y gazebo libgazebo-dev ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox ros-humble-xacro ros-humble-rviz2 ros-humble-rosbridge-suite ros-humble-rosbag2-storage-mcap python3-colcon-common-extensions python3-rosdep
    ```

    **2. Código y espacio de trabajo.** El espacio de trabajo *enlaza* los paquetes del repositorio; no los copia.

    ```bash
    git clone https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments.git ~/Tesis
    cd ~/Tesis
    mkdir -p ~/deepracer_sim_ws/src && ln -s "$(pwd)/Robot/aws-deepracer" ~/deepracer_sim_ws/src/aws-deepracer
    ```

    **3. Compilar.**

    ```bash
    cd ~/deepracer_sim_ws
    rosdep update && rosdep install --from-paths src --ignore-src -r -y
    colcon build --symlink-install
    ```

    **4. Variables de entorno**, una sola vez, desde la carpeta del repositorio:

    ```bash
    cd ~/Tesis
    echo 'source ~/deepracer_sim_ws/install/setup.bash' >> ~/.bashrc
    echo "export GAZEBO_MODEL_PATH=\"\$GAZEBO_MODEL_PATH:$(pwd -P)/simulacion\"" >> ~/.bashrc
    exec bash
    ```

    **5. Comprobar la instalación.** Revisa el enlace, la compilación, las variables y los mundos, y dice qué falta.

    ```bash
    herramientas/verificar_instalacion.sh
    ```

    **6. Dos agentes, uno por piso**, cada uno en su terminal:

    ```bash
    herramientas/robot.sh robot1 nav2
    ```

    ```bash
    herramientas/robot.sh robot2 nav2
    ```

    El coordinador, la página del teléfono y una misión con relevo siguen la [guía de arranque](https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments/blob/main/Documentos/GUIA_ARRANQUE.md), paso a paso.

    **7. Los pisos 3 y 4 de Catalayud, en simulación.** Cada agente con el mundo y el mapa de su piso:

    ```bash
    MUNDO=$PWD/simulacion/piso3.world herramientas/robot.sh robot1 nav2 map:=$PWD/Robot/aws-deepracer/deepracer_bringup/maps/piso3.yaml x:=22.10 y:=1.06 yaw:=3.1416 nivel:=3
    ```

    ```bash
    MUNDO=$PWD/simulacion/piso4.world herramientas/robot.sh robot2 nav2 map:=$PWD/Robot/aws-deepracer/deepracer_bringup/maps/piso4.yaml x:=24.45 y:=1.21 yaw:=3.1416 nivel:=4
    ```

    El coordinador con el catálogo de esos pisos y los demás pasos están en la sección 8 de [GUIA_PISOS_3_Y_4.md](https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments/blob/main/Documentos/GUIA_PISOS_3_Y_4.md). Sirve para ver el sistema, no para medir.

=== "Con los agentes físicos"

    Cada agente usa su tarjeta original con Ubuntu 24.04, ROS 2 Jazzy y el software comunitario [deepracer-custom-car](https://github.com/aws-deepracer-community/deepracer-custom-car). El coordinador corre en un portátil con Humble, dentro de un contenedor con Jazzy.

    | Paso | Qué hace | Herramienta |
    |---|---|---|
    | Llevar el código a los dos agentes | Copia y compila lo mismo en los dos | `herramientas/nivelar_carros.sh` |
    | Navegación sobre el mapa del piso | Arranca Nav2 en el orden correcto y pone la pose de salida | `herramientas/nav2_mapa_guardado.sh` |
    | Coordinador y página | Contenedor del coordinador, puente web y página | `herramientas/coordinador_portatil.sh` |

    Los mapas de los pisos 3 y 4 salen de medidas con flexómetro, no de SLAM. La guía de esos pisos explica cómo se levantaron y dónde va cada agente al arrancar: [GUIA_PISOS_3_Y_4.md](https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments/blob/main/Documentos/GUIA_PISOS_3_Y_4.md).

??? question "Si algo no funciona"
    - **Gazebo abre un mundo vacío y no da error** al abrir un mundo a mano: falta la variable `GAZEBO_MODEL_PATH` del paso 4, que apunta a la carpeta `simulacion/`. El lanzador del proyecto la agrega por su cuenta.
    - **Los controladores no quedan activos**: el código se migró de ROS 2 Foxy a Humble; en Humble los controladores se activan con el estado `active`.
    - **La página del teléfono se queda con una versión vieja**: sírvala con `herramientas/servir_interfaz.py`, que obliga al navegador a pedir los archivos nuevos.
