<!-- Glosario del sitio: pymdownx.snippets lo añade al final de cada página y la extensión abbr
     muestra la definición al pasar el cursor sobre cada código. Las compuertas G-1 a G-6 son las del
     acta de la demostración física (Documentos/ACTA_GO_NOGO.md); los requisitos, los de
     Documentos/REQUISITOS.md; los hitos, los del cronograma; los riesgos, los de ESTADO.md. -->

*[G-1]: Compuerta 1 de la demostración física: el vehículo mueve sus ruedas con órdenes de ROS 2
*[G-2]: Compuerta 2 de la demostración física: odometría con error de 10 % o menos sobre un recorrido medido
*[G-3]: Compuerta 3 de la demostración física: un vehículo navega solo de punto a punto y su llegada se verifica
*[G-4]: Compuerta 4 de la demostración física: los dos vehículos y el coordinador en la misma red ROS 2, sin choque de nombres
*[G-5]: Compuerta 5 de la demostración física: una misión con relevo, de extremo a extremo, con los dos vehículos
*[G-6]: Compuerta 6 de la demostración física: entre 5 y 10 misiones con relevo, cada una con su registro
*[G2]: Punto de decisión de hardware de la semana 21: una recta de 20 m o más con el vehículo, para medir su odometría y su localización contra cinta
*[H1]: Hito 1: contrato de interfaces ROS 2, con un espacio de nombres por robot
*[H3]: Hito 3: dos agentes navegando a la vez en niveles separados
*[R5]: Riesgo 5: las fases de requisitos y diseño no tenían un documento de requisitos verificable
*[R6]: Riesgo 6: discrepancias entre los informes y el repositorio
*[R12]: Riesgo 12: que el verificador de meta del navegador cuente como fallo llegadas que fueron buenas
*[RF-11]: Requisito: cada vehículo se desplaza con las órdenes de velocidad, con dirección tipo automóvil
*[RF-15]: Requisito: los dos vehículos y el coordinador se comunican por red con latencia mediana de 100 ms o menos
*[RF-16]: Requisito: el mismo código fuente funciona en la simulación y en los vehículos
*[RF-22]: Requisito: el sistema registra el tiempo de asignación del robot
*[RF-25]: Requisito: las métricas salen de un registro automático de cada misión
*[RF-27]: Requisito: la demostración con los vehículos ejecuta entre 5 y 10 misiones con registro
*[RF-28]: Requisito: en una misión entre pisos, el robot del piso de destino no arranca hasta que el usuario confirma el cambio de piso
*[RF-29]: Requisito: el usuario puede cancelar desde el teléfono una misión en curso
*[OE1]: Objetivo específico 1: arquitectura funcional
*[OE2]: Objetivo específico 2: plataforma robótica
*[OE3]: Objetivo específico 3: interfaz para el usuario
*[OE4]: Objetivo específico 4: evaluación experimental
*[AMCL]: Localización de Monte Carlo adaptativa: estima la posición del robot sobre un mapa conocido
*[SLAM]: Mapeo y localización simultáneos: el robot construye el mapa mientras se ubica en él
*[Nav2]: La pila de navegación de ROS 2: planifica la ruta y guía al vehículo hasta la meta
*[LiDAR]: Sensor láser que mide la distancia a su alrededor
*[IMU]: Unidad inercial: mide el giro y la aceleración del vehículo
*[RViz]: Visualizador de ROS: muestra el mapa, los sensores y la posición del robot
*[rf2o]: Odometría estimada a partir de las lecturas del LiDAR
*[URDF]: Formato que describe la forma y las articulaciones del robot
