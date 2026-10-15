# Capturas del proyecto, por fase

Catálogo de las capturas de pantalla del equipo que sostienen el desarrollo del proyecto, ordenadas
por fase y con el lugar del documento final donde servirían. Se tomaron de la carpeta de capturas
del portátil el 15 de octubre de 2026: de 261 capturas que no estaban en el repositorio entraron 44.
Las demás quedaron fuera porque no son del proyecto (otras materias, cursos, juegos, configuración
del equipo) o porque muestran datos personales o contraseñas.

Cada archivo sigue la convención de [`README.md`](README.md): `SNN_descripcion`, con la semana del
cronograma. En abril y mayo la semana sale del tema de cada entregable; desde agosto, de la tabla
de [`CRONOGRAMA_S17_S32.md`](../CRONOGRAMA_S17_S32.md). Las de más de 600 KB se guardaron en JPG.

## Exploración de plataformas y modelado del vehículo (semanas 10 a 12, abril)

### Simulador de DonkeyCar con su interfaz web de conducción

![Simulador de DonkeyCar con su interfaz web de conducción](S10_donkeycar_simulador.jpg)

`S10_donkeycar_simulador.jpg`, captura del 2026-04-08. Uso en el documento final: §3.2.1, por qué DeepRacer y no DonkeyCar.

### Primer modelo URDF del DonkeyCar en RViz

![Primer modelo URDF del DonkeyCar en RViz](S11_urdf_donkeycar_rviz.png)

`S11_urdf_donkeycar_rviz.png`, captura del 2026-04-16. Uso en el documento final: §3.2.1.

### Árbol de transformaciones (view_frames) del modelo del DonkeyCar

![Árbol de transformaciones (view_frames) del modelo del DonkeyCar](S11_arbol_tf_donkeycar.png)

`S11_arbol_tf_donkeycar.png`, captura del 2026-04-16. Uso en el documento final: §3.2.3, orden de puesta en marcha.

### Modelo del DonkeyCar con ruedas y dirección en RViz

![Modelo del DonkeyCar con ruedas y dirección en RViz](S11_urdf_donkeycar_ruedas.png)

`S11_urdf_donkeycar_ruedas.png`, captura del 2026-04-17. Uso en el documento final: §3.2.1.

### Simulador F1TENTH (gym_ros) en RViz, evaluado como alternativa

![Simulador F1TENTH (gym_ros) en RViz, evaluado como alternativa](S11_f1tenth_gym_rviz.png)

`S11_f1tenth_gym_rviz.png`, captura del 2026-04-17. Uso en el documento final: Marco referencial, simuladores.

### Cronograma por fases del primer semestre (febrero a junio)

![Cronograma por fases del primer semestre (febrero a junio)](S11_cronograma_semestre1.png)

`S11_cronograma_semestre1.png`, captura del 2026-04-17. Uso en el documento final: Anexo de cronograma.

### Vehículo de prueba en un entorno de pasillos en Gazebo

![Vehículo de prueba en un entorno de pasillos en Gazebo](S12_sim_car_gazebo.png)

`S12_sim_car_gazebo.png`, captura del 2026-04-22. Uso en el documento final: Marco referencial, simuladores.

## Entorno virtual: pasillos y primer piso (semana 13, mayo)

### Editor de edificios de Gazebo con el primer muro del pasillo

![Editor de edificios de Gazebo con el primer muro del pasillo](S13_building_editor_pasillo.png)

`S13_building_editor_pasillo.png`, captura del 2026-05-05. Uso en el documento final: §3.2.5, mapas derivados de medidas.

### Modelo del pasillo USTA con el barrido del LiDAR del vehículo

![Modelo del pasillo USTA con el barrido del LiDAR del vehículo](S13_pasillo_usta_lidar.png)

`S13_pasillo_usta_lidar.png`, captura del 2026-05-05. Uso en el documento final: §3.2.4, odometría y entorno.

### DeepRacer en el pasillo USTA simulado, con su LiDAR

![DeepRacer en el pasillo USTA simulado, con su LiDAR](S13_pasillo_usta_deepracer.png)

`S13_pasillo_usta_deepracer.png`, captura del 2026-05-07. Uso en el documento final: §3.2.4.

### Pasillo grande (15 x 5 m) con texturas y el LiDAR del vehículo

![Pasillo grande (15 x 5 m) con texturas y el LiDAR del vehículo](S13_pasillo_grande_lidar.jpg)

`S13_pasillo_grande_lidar.jpg`, captura del 2026-05-07. Uso en el documento final: §3.2.4.

### Primer piso con muros de ladrillo y el vehículo en Gazebo

![Primer piso con muros de ladrillo y el vehículo en Gazebo](S13_primer_piso_gazebo.jpg)

`S13_primer_piso_gazebo.jpg`, captura del 2026-05-09. Uso en el documento final: §3.2.5.

## Simuladores alternativos y entorno de desarrollo (semanas 15 y 16, mayo y junio)

### Simulador CARLA con control manual, evaluado como alternativa

![Simulador CARLA con control manual, evaluado como alternativa](S15_carla_control_manual.jpg)

`S15_carla_control_manual.jpg`, captura del 2026-05-14. Uso en el documento final: Marco referencial, simuladores.

### Trayectoria de un vehículo en CARLA trazada desde Python

![Trayectoria de un vehículo en CARLA trazada desde Python](S15_carla_trayectoria.png)

`S15_carla_trayectoria.png`, captura del 2026-05-25. Uso en el documento final: Marco referencial, simuladores.

### Características del portátil de desarrollo (Ubuntu 22.04.5, Ryzen 5 PRO 5650U, 16 GB)

![Características del portátil de desarrollo (Ubuntu 22.04.5, Ryzen 5 PRO 5650U, 16 GB)](S16_portatil_especificaciones.png)

`S16_portatil_especificaciones.png`, captura del 2026-06-09. Uso en el documento final: §3.2, entorno de desarrollo.

## Dos robots en simulación y primeras pruebas sobre el vehículo (semanas 17 a 20, agosto)

### Mundo primer_piso_v2 en Gazebo para el simulador multi-robot

![Mundo primer_piso_v2 en Gazebo para el simulador multi-robot](S17_gazebo_primer_piso_v2.png)

`S17_gazebo_primer_piso_v2.png`, captura del 2026-08-04. Uso en el documento final: §3.2.5.

### lsusb con el puente CP210x del LiDAR conectado

![lsusb con el puente CP210x del LiDAR conectado](S17_lsusb_lidar_cp210x.png)

`S17_lsusb_lidar_cp210x.png`, captura del 2026-08-04. Uso en el documento final: §3.2, hardware.

### Grabación de Ubuntu Server 24.04 con Raspberry Pi Imager, antes de saber que la tarjeta es Intel

![Grabación de Ubuntu Server 24.04 con Raspberry Pi Imager, antes de saber que la tarjeta es Intel](S17_raspberry_pi_imager.png)

`S17_raspberry_pi_imager.png`, captura del 2026-08-04. Uso en el documento final: §3.2.1, plataforma.

### RViz con el mapa y Nav2 en la simulación

![RViz con el mapa y Nav2 en la simulación](S18_rviz_nav2_mapa.png)

`S18_rviz_nav2_mapa.png`, captura del 2026-08-10. Uso en el documento final: §3.2.2, Nav2.

### Mapa de costos de Nav2 alrededor del vehículo simulado

![Mapa de costos de Nav2 alrededor del vehículo simulado](S18_rviz_costmap.jpg)

`S18_rviz_costmap.jpg`, captura del 2026-08-10. Uso en el documento final: §3.2.2.

### robot1 en RViz con sus marcos con prefijo y su mapa de costos

![robot1 en RViz con sus marcos con prefijo y su mapa de costos](S18_rviz_robot1_espacio_nombres.png)

`S18_rviz_robot1_espacio_nombres.png`, captura del 2026-08-12. Uso en el documento final: §3.1, dos agentes.

### Dos vehículos en el mismo mundo de Gazebo

![Dos vehículos en el mismo mundo de Gazebo](S18_gazebo_dos_robots.png)

`S18_gazebo_dos_robots.png`, captura del 2026-08-12. Uso en el documento final: §3.1.

### Metas NavigateToPose a robot1 y robot2 terminadas en SUCCEEDED

![Metas NavigateToPose a robot1 y robot2 terminadas en SUCCEEDED](S18_navigate_to_pose_dos_robots.png)

`S18_navigate_to_pose_dos_robots.png`, captura del 2026-08-12. Uso en el documento final: §3.1, RF-02 y RF-03.

### cmd_vel y odom de robot1 y robot2 por separado

![cmd_vel y odom de robot1 y robot2 por separado](S18_cmd_vel_odom_dos_robots.png)

`S18_cmd_vel_odom_dos_robots.png`, captura del 2026-08-14. Uso en el documento final: §3.1, RF-02.

### Pasillo con muros de ladrillo y el LiDAR del vehículo

![Pasillo con muros de ladrillo y el LiDAR del vehículo](S18_gazebo_pasillo_lidar.png)

`S18_gazebo_pasillo_lidar.png`, captura del 2026-08-14. Uso en el documento final: §3.2.4.

### Maniobra en RViz y Gazebo a la vez

![Maniobra en RViz y Gazebo a la vez](S19_rviz_gazebo_maniobra.jpg)

`S19_rviz_gazebo_maniobra.jpg`, captura del 2026-08-18. Uso en el documento final: §3.2.2, maniobras Ackermann.

### Órdenes de servo publicadas en amss-ez9n desde ROS 2

![Órdenes de servo publicadas en amss-ez9n desde ROS 2](S19_servo_ctrl_amss_ez9n.png)

`S19_servo_ctrl_amss_ez9n.png`, captura del 2026-08-19. Uso en el documento final: RF-14, primera actuación.

### Barrido de tracción en amss-ez9n para encontrar el umbral de arranque

![Barrido de tracción en amss-ez9n para encontrar el umbral de arranque](S19_barrido_throttle_amss_ez9n.png)

`S19_barrido_throttle_amss_ez9n.png`, captura del 2026-08-19. Uso en el documento final: §3.2.6, banda muerta.

### Reglas de ufw y prueba de multidifusión entre el portátil y el vehículo

![Reglas de ufw y prueba de multidifusión entre el portátil y el vehículo](S19_ufw_multicast_portatil_carro.png)

`S19_ufw_multicast_portatil_carro.png`, captura del 2026-08-19. Uso en el documento final: §3.2.8, red.

### Mensajes de ROS 2 entre el portátil y el vehículo en los dos sentidos

![Mensajes de ROS 2 entre el portátil y el vehículo en los dos sentidos](S19_ros2_portatil_carro.png)

`S19_ros2_portatil_carro.png`, captura del 2026-08-19. Uso en el documento final: §3.2.8, RF-15.

### Vista superior del mundo de dos pisos en Gazebo

![Vista superior del mundo de dos pisos en Gazebo](S19_mundo_definitivo_gazebo.png)

`S19_mundo_definitivo_gazebo.png`, captura del 2026-08-20. Uso en el documento final: §3.2.5.

### Un mundo de Gazebo por nivel, uno para cada robot

![Un mundo de Gazebo por nivel, uno para cada robot](S19_gazebo_mundo_por_nivel.png)

`S19_gazebo_mundo_por_nivel.png`, captura del 2026-08-23. Uso en el documento final: §3.1, RNF-01.

### Vehículo en el pasillo simulado con su LiDAR

![Vehículo en el pasillo simulado con su LiDAR](S20_gazebo_robot_pasillo.png)

`S20_gazebo_robot_pasillo.png`, captura del 2026-08-26. Uso en el documento final: §4.1.

### Cargador de balance de la batería de tracción del vehículo

![Cargador de balance de la batería de tracción del vehículo](S20_cargador_bateria.png)

`S20_cargador_bateria.png`, captura del 2026-08-28. Uso en el documento final: §3.2, hardware.

### Misión con relevo en los dos mundos, terminada con exito: true y un relevo

![Misión con relevo en los dos mundos, terminada con exito: true y un relevo](S20_mision_relevo_simulacion.png)

`S20_mision_relevo_simulacion.png`, captura del 2026-08-30. Uso en el documento final: §4.1, RF-07.

## Campaña en simulación, interfaz y planificación (semanas 22 a 24, septiembre)

### Cálculo del intervalo de Wilson de la tasa de éxito (26 de 30)

![Cálculo del intervalo de Wilson de la tasa de éxito (26 de 30)](S22_intervalo_wilson.png)

`S22_intervalo_wilson.png`, captura del 2026-09-07. Uso en el documento final: §4.1.1 y presentación.

### Cronograma en Gantt de los dos semestres con el estado de cada actividad

![Cronograma en Gantt de los dos semestres con el estado de cada actividad](S22_cronograma_gantt.png)

`S22_cronograma_gantt.png`, captura del 2026-09-07. Uso en el documento final: Anexo de cronograma.

### Interfaz web durante una misión: tramo 1, «Sígueme»

![Interfaz web durante una misión: tramo 1, «Sígueme»](S22_hri_mision_sigueme.png)

`S22_hri_mision_sigueme.png`, captura del 2026-09-09. Uso en el documento final: §3.3.2, OE3.

### Interfaz web pidiendo confirmar el cambio de piso («¿Ya subió?»)

![Interfaz web pidiendo confirmar el cambio de piso («¿Ya subió?»)](S22_hri_confirmacion_piso.png)

`S22_hri_confirmacion_piso.png`, captura del 2026-09-10. Uso en el documento final: §3.3.2, RF-28.

### Interfaz web con una misión fallida y su motivo («Camino bloqueado»)

![Interfaz web con una misión fallida y su motivo («Camino bloqueado»)](S22_hri_camino_bloqueado.png)

`S22_hri_camino_bloqueado.png`, captura del 2026-09-10. Uso en el documento final: §3.3.2, RF-18.

### Vista superior del pasillo simulado con el LiDAR

![Vista superior del pasillo simulado con el LiDAR](S23_gazebo_pasillo_superior.png)

`S23_gazebo_pasillo_superior.png`, captura del 2026-09-18. Uso en el documento final: §4.1.

### Mapa del cuarto construido por el vehículo, en RViz

![Mapa del cuarto construido por el vehículo, en RViz](S24_rviz_mapa_cuarto.png)

`S24_rviz_mapa_cuarto.png`, captura del 2026-09-23. Uso en el documento final: §3.2.5, SLAM en hardware.

## Red de los pisos 3 y 4 (semana 25, octubre)

### Red DEEPRACER-PRO configurada en el punto de acceso del piso

![Red DEEPRACER-PRO configurada en el punto de acceso del piso](S25_fiberhome_red_deepracer.png)

`S25_fiberhome_red_deepracer.png`, captura del 2026-10-02. Uso en el documento final: §3.2.8, red.

### Ajustes de 5 GHz del punto de acceso

![Ajustes de 5 GHz del punto de acceso](S25_fiberhome_5ghz.png)

`S25_fiberhome_5ghz.png`, captura del 2026-10-02. Uso en el documento final: §3.2.8, red.
