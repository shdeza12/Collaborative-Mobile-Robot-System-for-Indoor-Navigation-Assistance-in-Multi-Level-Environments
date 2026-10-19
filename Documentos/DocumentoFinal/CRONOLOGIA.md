# Cronología del trabajo, semana a semana

Fuente para el capítulo de desarrollo del documento final y para el sitio del proyecto. Reúne lo
que se hizo cada semana según los entregables (`Documentos/Entregables/`, semanas 10 a 27) y el
historial del repositorio (391 commits entre el 29 de abril y el 19 de octubre de 2026: 353 de
Santiago y 38 de Jonny). Las capturas citadas están en `Documentos/Evidencia/` y su catálogo, en
`Evidencia/CAPTURAS_POR_FASE.md`.

Las semanas son las del cronograma. El primer semestre (S1 a S16) va de febrero a junio, y los
entregables de S10 a S15 están fechados en abril y mayo. El segundo semestre empieza el 3 de agosto:
S17 es del 3 al 9 de agosto, y cada semana siguiente avanza siete días (S27, del 12 al 18 de octubre).

Cada semana dice qué se hizo, qué se decidió y qué se corrigió, con su cifra cuando la hay. Las
correcciones de semanas anteriores se anotan en la semana en que se descubrieron.

---

## Primer semestre: planteamiento, requisitos, diseño y primeros desarrollos

### S1 a S9 (febrero a marzo): planteamiento y requisitos

No hay entregables de estas semanas en el repositorio. Según el cronograma del anteproyecto, S1 a S7
fueron la fase de planteamiento (problema, pregunta, literatura, documento y sustentación del
anteproyecto), y S8 a S11, el levantamiento de requisitos y el análisis del entorno.

El anteproyecto proponía dos vehículos «tipo DonkeyCar» con Raspberry Pi 4, simulación en
CoppeliaSim, OpenCV y una aplicación móvil. Su propia lista de herramientas (§7.2) ya nombraba el
AWS DeepRacer, la Raspberry Pi 4 y la Jetson Nano como hardware, y la «ingeniería inversa sobre los
vehículos AWS DeepRacer» como técnica.

### S10 (abril): limitaciones de la plataforma DonkeyCar

- Se instaló y se manejó el simulador de DonkeyCar: un entorno de Unity con una pista exterior,
  conducido desde la interfaz web del propio DonkeyCar, con la imagen de la cámara del vehículo
  (`S10_donkeycar_simulador.jpg`, 8 de abril).
- El análisis encontró tres limitaciones. El ecosistema DonkeyCar no se actualiza desde hace años y
  no es compatible con las versiones recientes de ROS 2. Su simulador no se integra con ROS 2, de modo
  que no permite probar mapeo, localización ni planificación. Y sin ROS 2 en el simulador no se puede
  montar la comunicación entre robots ni la coordinación central.
- Conclusión de la semana: el hardware DonkeyCar o DeepRacer sigue siendo posible, pero la
  simulación tiene que salir del ecosistema DonkeyCar hacia un simulador compatible con ROS 2.
- Se fijaron los criterios para elegir simulador: ROS 2 Humble o posterior, vehículos con
  dirección Ackermann, entornos interiores, SLAM y navegación. Candidatos: CoppeliaSim (el del
  anteproyecto), Gazebo y RViz como visualizador.
- Se mantuvo ROS 2 Humble sobre Ubuntu 22.04 como base, y la restricción de no intervenir el
  edificio.

Fuente: Entregable S10.

### S11 (abril): modelo propio del DonkeyCar y primera arquitectura

- Se empezó un modelo propio del DonkeyCar para ROS 2 (paquete `donkeycar_description`): el chasis,
  las cuatro ruedas y la dirección en RViz, con su árbol de transformaciones
  (`S11_urdf_donkeycar_rviz.png`, `S11_arbol_tf_donkeycar.png`, `S11_urdf_donkeycar_ruedas.png`,
  16 y 17 de abril).
- Se probó el simulador de F1TENTH con RViz como alternativa (`S11_f1tenth_gym_rviz.png`).
- Decisión de la semana: mantener el chasis tipo DonkeyCar con dirección Ackermann. Como el cambio de
  piso es por escalera y cada robot atiende un piso, el vehículo no tiene que entrar a un ascensor.
- La maniobra de regreso del vehículo se dejó a planificadores con restricciones de automóvil (TEB o
  Smac), capaces de dar la vuelta en varios tiempos dentro del pasillo.
- Arquitectura: servidor central, y panel web en HTML y JavaScript que habla con ROS 2 por
  `rosbridge`.
- Se empezó a modelar el pasillo de la universidad con el editor de edificios de Gazebo, para
  comprobar en simulación que el radio de giro alcanza.

Fuente: Entregable S11.

### S12 (abril): adopción del modelo AWS DeepRacer y migración a ROS 2 Humble

- Se cambió el modelo de simulación al AWS DeepRacer por tres razones: no existía un modelo del
  DonkeyCar para Gazebo con Ackermann, mantenido y funcional en Humble; el DeepRacer es un vehículo
  Ackermann a escala 1:18 con LiDAR y cámaras; y AWS publicó en código abierto su descripción del
  vehículo, el complemento de cinemática Ackermann para Gazebo y la configuración de Gazebo Classic.
- Plan de entonces: conservar el chasis del DeepRacer y cambiar su tarjeta Intel por una Raspberry
  Pi 4 con Humble.
- Migración de Foxy (Ubuntu 20.04) a Humble (Ubuntu 22.04), paquete por paquete. Tres cambios por la
  evolución de `ros2_control`: `--set-state start` pasa a `active` en dos lanzadores, y
  `joint_state_controller` pasa a `joint_state_broadcaster`. Los seis paquetes compilaron sin errores,
  con avisos por una cabecera obsoleta en el complemento Ackermann.
- Validación sobre un mundo vacío: el vehículo aparece con el LiDAR y la cámara publicando, a 62 FPS
  y con factor de tiempo real 1,00; los siete controladores quedan activos (publicador de estado,
  cuatro ruedas y dos articulaciones de dirección); el vehículo responde a las órdenes de velocidad;
  y la odometría da 0,40 m/s para 0,5 m/s ordenados.
- Cierre de la fase de diseño: diagrama de arquitectura, tabla de módulos (percepción, localización,
  planificación, control, locomoción, comunicación, coordinación e interfaz) y el escenario de relevo
  en siete pasos. Los dos robots se distinguirían por espacio de nombres (`/robot1`, `/robot2`).
- Primer commit con el código: «Add Robot/: AWS DeepRacer migrated to ROS 2 Humble» (30 de abril).

Fuente: Entregable S12; commit `484e1e5`.

### S13 (mayo): primeros entornos y seguidor de paredes

- Pasillo de la universidad en Gazebo, de 7 × 3 m, hecho con el editor de edificios; después uno
  ampliado de 15 × 5 m. El DeepRacer migrado se probó dentro, teleoperado.
- Seguidor de paredes, sugerido por la dirección como ejercicio de integración entre el LiDAR y la
  cinemática Ackermann. Primero con control proporcional-derivativo sobre un rayo lateral, que
  saturaba y no veía la orientación respecto a la pared. Después con la técnica de dos rayos del curso
  F1TENTH (objetivo 0,5 m de la pared, anticipación de 1,0 m, 0,5 m/s).
- Resultado: en el pasillo de 7 × 3 m no se estabilizó con ninguna sintonía (giros saturados,
  círculos y choques), porque el radio de giro deja poco margen en 3 m de ancho. En el de 15 × 5 m
  convergió por tramos, alrededor de 0,76 m de la pared, y se perdía en los extremos.
- Conclusión: un comportamiento reactivo no anticipa las restricciones de un vehículo Ackermann en
  espacios estrechos. El trabajo pasa a la navegación con mapa (SLAM, AMCL, puntos de interés y un
  planificador para automóvil).
- Se evaluó `deepracer-custom-car`, de la comunidad del DeepRacer, sugerido por la codirección: lleva
  el software del vehículo a Raspberry Pi 4 (Humble) o Pi 5 (Jazzy), con soporte del LiDAR, y no trae
  nada de simulación. Quedó para la fase física.

Fuente: Entregable S13; commit `d02ba77`.

### S14 (mayo): sensores en el modelo del primer piso

- Mundo del primer piso del bloque de pruebas: pasillo de unos 44 m (pared norte de 44,25 m) por unos
  5 m, con la pared sur en tramos y las puertas de los salones abiertas.
- Con RViz configurado a mano se comprobaron el LiDAR, la cámara estéreo, la odometría y el árbol de
  transformaciones, quietos y teleoperando (video de la semana).
- Se anotó que la odometría simulada no tiene deriva, a diferencia de la real, y que el LiDAR del
  modelo simulado cubre 300°. El LiDAR real resultó ser de 360° (S19).
- Se fijó el papel de cada sensor: el LiDAR para el mapa y la localización; la cámara quedó
  disponible, y al final el sistema no la usó.

Fuente: Entregable S14; commit `3016db8`.

### S15 (mayo): primer mapa con SLAM

- Primer mapa del primer piso con `slam_toolbox`, recorriendo el pasillo teleoperado de ida y vuelta.
  El informe lo dio por bueno.
- Corrección publicada el 21 de septiembre (fe de erratas): el mapa guardado mide 23,04 × 15,72 m,
  la mitad del largo y el triple del ancho del pasillo, y su resolución es 0,06 m, no 0,05. El nodo
  era el síncrono. El mapa estaba deformado por la deriva de la pose. Fue la primera manifestación,
  sin diagnóstico entonces, de la falta de información de avance en un pasillo recto, que se midió en
  septiembre (S22).

Fuente: Entregable S15; `Evidencia/S24_fe_de_erratas_S15.md`; commit `2ac2513`.

### S16 (junio) y receso

- No se emitió entregable; el 16 de agosto se decidió cerrarlo sin emitir. Lo técnico de esas semanas
  quedó en el repositorio: dos correcciones de compilación del complemento Ackermann para Humble
  (cabecera de `tf2_geometry_msgs` y una opción de compilador incompatible, 14 de junio) y la causa de
  un parámetro del mapeo (`max_laser_range` de 12,0 m contra un LiDAR simulado de 10,0 m).
- Receso de mitad de año entre junio y agosto.

Fuente: `ESTADO.md` (16-ago); commits `a0c98c5`, `ca34b3f`.

---

## Segundo semestre: integración y pruebas

### S17 (3 al 9 de agosto): vehículo físico liberado y Nav2 en Humble

- Cronograma replanificado de S17 a S32, con criterio de cierre por semana; firmado por el director el
  14 de agosto.
- Vehículo físico: se instaló `deepracer-custom-car` en una Raspberry Pi 4 y en la tarjeta original
  del DeepRacer, y se probó la marcha (avance, reversa y giro) desde la interfaz web del vehículo
  (video). La tarjeta original quedó con Ubuntu Server 24.04 y ROS 2 Jazzy.
- Nav2 y AMCL, desarrollados en el primer semestre sin publicar, se migraron de Foxy a Humble (cinco
  cambios de nombres y parámetros) y se adaptaron a Ackermann: árboles de comportamiento sin giro en el
  sitio, sin rotación hacia el rumbo en el controlador, huella corregida de 0,17 × 0,17 m a
  0,28 × 0,19 m y planificador Smac con radio mínimo de 0,35 m (el geométrico del modelo es 0,284 m).
- Contrato de interfaces: todo cuelga de un espacio de nombres por robot; el coordinador manda solo
  por la acción de navegación; la interfaz habla solo con el coordinador.
- Herramienta que verifica el contrato sobre el sistema en marcha; en su primera ejecución encontró
  que `camera_link` tenía dos padres.
- Corrección: el espacio de trabajo de compilación era una copia del repositorio del fabricante, no
  un enlace al del proyecto. Los ajustes de SLAM de semanas anteriores nunca se habían ejecutado y el
  mapa previo quedó invalidado.
- Selección del entorno de evaluación y pregunta de investigación escritas.

Fuente: Entregable S17; commits `1242651`, `cd6b993`, `afd0594`.

### S18 (10 al 16 de agosto): dos agentes aislados y entorno de dos niveles

- Dos robots en simulación: en un solo Gazebo no es posible, porque la integración de Gazebo con
  ROS 2 en Humble aplica a todos los complementos el espacio de nombres del primer modelo. Se pasó a
  un simulador por vehículo.
- Nav2 y AMCL bajo espacio de nombres, con los marcos prefijados. Aislamiento de mando comprobado con
  cuatro evidencias independientes.
- Entorno de dos niveles: la planta del primer piso extraída como modelo reutilizable, dos instancias
  a 3,0 m de separación vertical, una losa para el nivel superior y una marca de transición de
  1,5 × 1,5 m en las mismas coordenadas de los dos niveles. Navegación autónoma en el nivel superior.
- Corrección del mapa de navegación: cubría el 35,5 % del largo, medía 15,0 m de ancho contra 5,3 m
  reales, y 2688 de sus 3618 celdas ocupadas (74 %) no tenían pared detrás. Se reemplazó por un mapa
  derivado de la geometría del mundo (`generar_mapa_desde_mundo.py`). Un mapa 2D es un corte del
  mundo, así que el del nivel superior es igual y no hubo que levantarlo.
- Norma adoptada: el éxito que informa Nav2 no es evidencia, porque compara contra su propia
  localización.
- Reproducibilidad: verificador de instalación y verificador de coherencia del repositorio.

Fuente: Entregable S18; commits `cd1c915`, `ee10a9a`, `dae9f9a`, `741421f`, `35c47da`.

### S19 (17 al 23 de agosto): diagnóstico del vehículo y protocolo

- Vehículo físico, con la tarjeta original: el LiDAR repite una pared con 2,8 mm de dispersión (23 mm
  contra la cinta, como cota). La dirección y la tracción responden a órdenes publicadas desde ROS 2.
- El LiDAR del kit es otro modelo que el diagnosticado al principio (360°, 360 muestras, 0,15 a
  12 m, 6,80 Hz). El servicio del vehículo se reiniciaba en bucle porque el lanzador llamaba a un
  ejecutable con otro nombre, y el servicio informaba estar activo sin estarlo.
- Dos distribuciones: cinco tipos de mensaje idénticos entre Humble y Jazzy y la acción de navegación
  distinta. La configuración de Nav2 difiere en seis puntos, tres de ellos silenciosos. La simulación
  no puede pasar a Jazzy porque la integración de Gazebo con `ros2_control` no está publicada allí: las
  dos distribuciones son una condición permanente del proyecto.
- Corrección de fondo: el complemento de simulación y el nodo del vehículo trataban la velocidad
  angular como un ángulo de volante. Se corrigió con el modelo de bicicleta (ángulo = arctan(ω·L/v));
  el error de seguimiento bajó a la mitad.
- Matriz de requisitos (34 en ese momento) y protocolo experimental del cuarto objetivo, escrito antes
  de instrumentar.
- Mundo definitivo de dos pisos con quince destinos (20 de agosto), y luego un mundo por piso: el
  LiDAR de un piso veía paredes del otro en 61 de 1701 posiciones (23 de agosto).
- Los dos agentes navegaron a la vez el 25 de agosto, hacia sus puntos de transferencia.

Fuente: Entregable S19; commits `cc7859c`, `8615161`, y el del 23 de agosto «Un mundo por piso».

### S20 (24 al 30 de agosto): coordinador, primera misión y relevo en simulación

- El mapa del nivel inferior dejaba escapar el espacio libre por los 16 vanos de las puertas (el
  planificador trazó una diagonal de 38 m a través de paredes). Se sellaron los vanos. El nivel
  superior, una planta en S de 35 paredes, recibió sus dieciséis destinos (Jonny).
- Paquete de mensajes propios (estado de robot, punto de interés, estado de misión y acción de
  guiado) y coordinador en dos piezas: el planificador sin ROS y el nodo.
- La prueba exhaustiva del planificador pasaba con treinta planes que mandaban al mismo robot dos
  veces al mismo punto; se corrigió.
- Defectos de llegada: el rumbo final dejaba la llegada a 0,413 m; la media vuelta salía del
  planificador que busca una pose; el ruido de odometría declarado a AMCL era 0,2; la tolerancia de
  parada tenía margen cero; un desfase de AMCL de 1,473 m a lo largo del pasillo.
- Registro de misión en cuatro piezas: esquema comprobable por máquina, marcas y veredicto como
  funciones puras, grabación sellada con el reloj de simulación y error de llegada calculado contra la
  odometría del robot que llegó. El tiempo de asignación medía cero: marcas idénticas con el reloj de
  simulación.
- 26 de agosto: el fallo al cargar controladores era un reintento sobre una operación no idempotente;
  con `spawner` y 60 s, 18 arranques dobles sin fallo (Jonny).
- 29 de agosto: primera misión de extremo a extremo, con una segunda de control. 30 de agosto: primera
  misión con relevo entre los dos pisos, llegadas a 0,128 y 0,077 m.
- Vehículo, 28 de agosto: el LiDAR ya convive con el software del fabricante (enlace al ejecutable
  correcto, sin tocar los archivos del fabricante); odometría láser en tres idas y vueltas; primer
  mando desde ROS 2 por el tópico de servos; mapa del laboratorio de 8,45 × 6,90 m.

Fuente: Entregable S20; commits de Jonny del 25 al 27 de agosto.

### S21 (31 de agosto al 6 de septiembre): campaña de treinta misiones

- Campaña en simulación adelantada tres semanas: treinta misiones sorteadas con semilla fija en cuatro
  estratos, corridas el 4 y el 5 de septiembre. Veredicto válido, cero descartes, 26 de 30 éxitos;
  error de llegada mediano 0,106 m; los cuatro fallos se quedaron cortos (0,284 a 0,347 m).
- Tres grabaciones salieron sin factor de tiempo real y se regrabaron (instrumento, no resultado).
- Desbloqueos: dos coordinadores vivos se robaban la meta; la comprobación previa medía la posición
  de aparición en vez de la localización; un remapeo de reloj no llegaba a los controladores.
- Vehículo: pasillo de pruebas de 20,08 m medido y marcado; la primera pasada de mapeo dio un mapa
  curvo y se detuvo; las grabaciones salían vacías porque el grabador y los programas del fabricante tenían dueños
  distintos, y la memoria compartida exige el mismo dueño en los dos extremos.
- Interfaz web empezada el 2 de septiembre por Jonny, en JavaScript sin bibliotecas sobre `rosbridge`
  (`roslib.js` descartado por implementar las acciones de ROS 1).

Fuente: Entregable S21; commits de Jonny del 2 de septiembre.

### S22 (7 al 13 de septiembre): interfaz en el teléfono e información de avance

- La interfaz operó una misión desde un teléfono real en la red de los vehículos, con los puertos de
  la página y del puente abiertos solo a esa subred.
- Confirmación de cambio de piso, a partir de las cinco situaciones de usuario que planteó el
  director: el segundo tramo arrancaba con el usuario todavía en el otro piso.
- La cancelación no funcionaba (sin función de respuesta en el servidor de acción).
- 8 de septiembre: cuatro mapas del pasillo rechazados. Se midió el mecanismo: en un pasillo recto el
  avance no está en el dato del LiDAR. En una caja cerrada simulada de 7,70 × 2,70 m el mapa salió
  bien (98,1 % en X, 95,0 % en Y): el primer mapa aceptado del proyecto, y la condición pasa a ser
  medible (estructura dentro del alcance del sensor).
- Revisión del protocolo: el criterio binario de continuidad no puede fallar; se reformula como
  invariante con el intervalo del relevo como medida.
- El primer objetivo quedó completo (10 de 10).

Fuente: Entregable S22.

### S23 (14 al 20 de septiembre): segundo vehículo y congelación del código

- Cancelación corregida por Jonny (13 de septiembre): el vehículo vuelve a su escalera. Verificada
  con una corrida cancelada y una de control.
- 14 de septiembre: llega el segundo vehículo, en intervención técnica desde agosto. Comunicación
  entre los dos vehículos: 600 de 600 mensajes, ida y vuelta de 7,61 ms de mediana y 20,76 ms de
  percentil 95. El cortafuegos de los vehículos bloqueaba el tráfico entre ellos.
- Información de avance medida en los pasillos reales de los pisos 1 y 2: insuficiente.
- 17 de septiembre: banda muerta de tracción, toda orden por debajo de 0,40 m/s daba potencia cero.
  Una orden movió los dos vehículos (el tópico de servos no tiene espacio de nombres): desde entonces
  se enciende uno a la vez hasta aislarlos.
- 18 de septiembre: código congelado (`v0.4-implementacion-congelada`) y mapa del trabajo restante,
  con una sola ruta crítica: la odometría en el vehículo.

Fuente: Entregable S23.

### S24 (21 al 27 de septiembre): decisión de la demostración física y navegación real

- 21 de septiembre: se decide intentar la demostración física con los dos vehículos. El acta fija
  seis pruebas de verificación con criterio, fecha y reversión.
- La «avería» del segundo vehículo era de permisos: los programas del fabricante corren como
  administrador y la memoria compartida no deja intercambiar datos con otro usuario.
- Con los dos vehículos encendidos, cada grabación recogía el LiDAR del otro: se retiraron las cinco
  grabaciones del 28 de agosto.
- 24 de septiembre, siete pasos sobre el vehículo: odometría con rf2o (tres recorridos de 3,00 m con
  flexómetro, entre 96,3 y 101,9 %); SLAM a bordo en un cuarto; mapa del pasillo del piso 2 con 6,093
  y 6,032 m registrados para 6,00 m; y esa noche Jonny llevó el vehículo con Nav2 y AMCL de forma
  autónoma sobre ese mapa.
- Guía para las pruebas de odometría y de llegada, y diseño del aislamiento entre vehículos.

Fuente: Entregable S24; commits de Jonny del 24 y 25 de septiembre.

### S25 (28 de septiembre al 4 de octubre): aislamiento, piso 2 y paso a los pisos 3 y 4

- 28 de septiembre: el director fija el sitio, el número de corridas de la campaña con los vehículos y
  la tolerancia de llegada (0,5 m en los vehículos, 0,25 m en simulación). Esa noche, los dos
  vehículos aislados con una partición de comunicaciones cada uno.
- Ajustes de Nav2 en el vehículo: el puente ya no da potencia cero por debajo de 0,40 m/s; parche de
  rf2o (con la transformada del láser vacía invertía la odometría); margen de llegada de 1,0 m.
- 30 de septiembre, hall del piso 2: llegadas a 1,43 y 1,26 m, rf2o con el 73 % del avance, y el hall
  medía 3,40 m contra 4,24 m del modelo (25 % mayor). Las demás medidas del modelo nunca se habían
  comprobado.
- Cambio de sitio a los pisos 3 y 4, levantados con flexómetro por Jonny (2 de octubre), con su
  catálogo de puntos.
- 2 de octubre, piso 4: odometría con +3,3 % sobre 14,57 m y −4,6 % sobre 6,68 m; llegadas a 0,57 y
  0,62 m, cortas por el margen de 1,0 m.

Fuente: Entregable S25; commits de Jonny del 2 de octubre.

### S26 (5 al 11 de octubre): unidad inercial, red, llegada verificada y coordinador al portátil

- 5 de octubre: los directores aceptan los pisos 3 y 4; entre misiones el vehículo sale desde donde
  terminó la anterior, y vuelve a su escalera solo al cancelar.
- Unidad inercial Bosch BMI160 de la tarjeta integrada en los dos vehículos: giros de 90° medidos
  como +90,17° y +88,38°; filtro que toma el avance de rf2o y el giro de la unidad inercial.
- Red (Jonny): los vehículos no podían transmitir en 5 GHz por falta de la base regulatoria; con ella,
  ida y vuelta de 5,99 ms de mediana. Un bucle de capa 2 duplicaba el 47 % del tráfico.
- 7 de octubre, piso 4: cadena de tres tramos sin intervención, llegadas medidas a 0,06 y 0,45 m
  (prueba de llegada superada). Reversa reducida al 75 % y media vuelta en varios tiempos.
- 8 de octubre: el otro vehículo recorre el piso 3. Primer intento del relevo con los dos vehículos:
  la tarjeta llegó a cargas de 22 a 33 y Nav2 no arrancaba. Descubrimiento local en cada vehículo.
- 9 de octubre: coordinador y grabador al portátil, en un contenedor con Jazzy, con topología en
  estrella. Comprobada en el laboratorio: tarjetas al 54 y 59 % en reposo y al 68 y 74 % navegando.

Fuente: Entregable S26.

### S27 (12 al 18 de octubre): campaña con los dos vehículos

- 13 de octubre: sorteo de las diez misiones (semilla 20261013, cinco de subida y cinco de bajada).
  El coordinador pasa a verificar cada llegada 1,5 s después de que Nav2 la da por alcanzada.
- 15 de octubre: revisión de los requisitos de la plataforma contra la evidencia de campo; capítulos
  2 y 3 del documento final reescritos.
- 16 de octubre: misión con relevo del Salón 302 al Salón 402 (132,5 s) y campaña: nueve misiones
  del sorteo completadas con relevo (sección 4.3 del documento final).
- Ajustes de la página: título de la confirmación según el sentido y nombres repetidos con su piso;
  servidor sin copias en caché.
- 18 de octubre: análisis de la campaña, corte de la semana y prototipo del sitio del proyecto.

Fuente: Entregable S27; `Evidencia/S27_campana_rf27.md`.

### S28 (desde el 19 de octubre): documento final

- Los dos vehículos nivelados con el código vigente. Resultados del sistema completo, conclusiones,
  trabajos futuros y resumen redactados con la campaña.
