# Coordinador y grabador de misiones en ROS 2 Jazzy, para el portatil (Ubuntu 22.04, Humble).
#
# POR QUE (2026-10-09). La decision D6 ponia el coordinador en un vehiculo porque la
# accion NavigateToPose de Nav2 no es la misma en Humble y en Jazzy (R8), y el
# portatil solo tiene Humble. El 8-oct, con el coordinador y el grabador en racey y
# las dos cadenas en la red, las tarjetas se saturaron (carga 22-33) y G-5 no se
# pudo correr. En un contenedor con Jazzy el coordinador habla la misma accion que
# los vehiculos y corre en el portatil, que es el servidor central del anteproyecto.
#
# Se construye y se usa con herramientas/coordinador_portatil.sh, desde la raiz del
# repositorio. El contexto de construccion es Robot/aws-deepracer.
FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-nav2-msgs \
        ros-jazzy-rosbag2-storage-mcap \
        ros-jazzy-rosidl-default-generators \
        python3-colcon-common-extensions \
        python3-yaml \
        procps \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /coordinacion_ws
COPY coordinacion_msgs src/coordinacion_msgs
COPY coordinacion src/coordinacion
RUN . /opt/ros/jazzy/setup.sh && colcon build --packages-select coordinacion_msgs coordinacion \
    && rm -rf build log

# El portatil (Humble) y el contenedor (Jazzy) comparten la red del anfitrion. Sin
# memoria compartida entre las dos versiones de Fast DDS: solo UDP.
ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
RUN echo 'source /opt/ros/jazzy/setup.bash && source /coordinacion_ws/install/setup.bash' >> /root/.bashrc
