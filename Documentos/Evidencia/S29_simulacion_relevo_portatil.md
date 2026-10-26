# La simulación de dos robots en el portátil, 26 de octubre

Sesión del 26 de octubre en el portátil del equipo (AMD Ryzen 5 PRO 5650U), para saber si la falla
del 6 de octubre ([`S26_simulacion_tras_actualizacion_ros.md`](S26_simulacion_tras_actualizacion_ros.md))
se repetía aquí. En este portátil la simulación no se corría desde el 14 de septiembre, y desde
entonces recibió dos actualizaciones de ROS: 302 paquetes el 16 de septiembre y 98 el 15 de octubre.
Extractos de consola: [`logs/S29_simulacion_relevo_portatil.txt`](logs/S29_simulacion_relevo_portatil.txt).
Los registros completos de las pilas y del coordinador están en `~/tesis_evidencia/sim_2026-10-26/`.

## Resultado

Tres misiones con relevo de la guía de arranque (`piso1_representacion → piso2_ieee`), cada una con
las dos pilas recién levantadas, sin ventana de Gazebo y con la confirmación de cambio de piso
publicada al llegar a `ESPERANDO_CONFIRMACION`. Las tres se completaron.

| Corrida | Tiempo total | Relevos | Llegadas verificadas contra `/odom` | Avisos de transformadas |
|---|---|---|---|---|
| 1 | 37,6 s | 1 | 0,185 · 0,125 · 0,173 · 0,115 m | 1, al arrancar |
| 2 | 37,6 s | 1 | 0,187 · 0,137 · 0,174 · 0,113 m | 1, al arrancar |
| 3 | 43,9 s | 1 | 0,210 · 0,144 · 0,185 · 0,126 m | 1, al arrancar |

Todas las llegadas quedaron dentro de la tolerancia de 0,25 m de la simulación. En las tres corridas,
la compuerta dio `LISTA` para los dos robots y la condición inicial quedó entre 0,030 y 0,039 m.

El único aviso de cada corrida es del agente al arrancar (`TF robot*/map -> robot*/base_link no
disponible: Lookup would require extrapolation into the past`), en el primer segundo de reloj de
simulación, antes de que AMCL publique. No es la firma del 6 de octubre, que era el controlador de
Nav2 repitiendo `Transform data too old` o `extrapolation into the past` durante la misión.

## Lo que esto dice y lo que no

- En el portátil, con las versiones instaladas hoy, la simulación de dos robots completa el relevo:
  `rclcpp` 16.0.21, `message_filters` 4.3.20, `tf2` y `tf2_ros` 0.25.24, `nav2_amcl` y
  `nav2_controller` 1.1.20, `rmw_fastrtps_cpp` 6.2.10.
- La causa de la falla del 6 de octubre sigue sin aislarse. Aquí `tf2` está en 0.25.24, una versión
  posterior a la que tenía el otro equipo ese día (0.25.23), pero no está demostrado que esa sea la
  diferencia.
- Las tres corridas son una comprobación de funcionamiento, no misiones de la campaña: no se
  grabaron con `grabar_mision.sh` ni se compusieron registros.
