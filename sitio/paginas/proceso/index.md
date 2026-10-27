# El proceso, de principio a fin

El proyecto se hizo en dos semestres de 2026. Esta línea de tiempo reúne los momentos que cambiaron el rumbo: las **decisiones**, los **problemas** que obligaron a corregir, los **cambios** de plataforma o de entorno y las **pruebas** que se superaron. Cada decisión tiene su explicación en [Decisiones y cambios de rumbo](decisiones.md), y cada prueba en [Pruebas de verificación](pruebas.md).

<p class="leyenda-tipos">Tipos: <span class="tipo decision">decisión</span> <span class="tipo problema">problema</span> <span class="tipo cambio">cambio</span> <span class="tipo prueba">prueba superada</span></p>

<div class="linea">

<div class="fase">Primer semestre · formulación, requisitos y diseño</div>

<div class="hito cambio"><div class="cuando">Marzo y abril</div><div class="titulo">De DonkeyCar a AWS DeepRacer <span class="tipo cambio">cambio</span></div><div class="texto">El ecosistema DonkeyCar no era compatible con ROS 2 reciente ni tenía un modelo mantenido para Gazebo. El DeepRacer es la misma clase de vehículo, tiene su modelo de simulación abierto y la universidad ya tenía dos. El modelo se migró de ROS 2 Foxy a Humble.</div></div>

<div class="hito problema"><div class="cuando">Mayo y junio</div><div class="titulo">El seguidor de paredes no se estabiliza <span class="tipo problema">problema</span></div><div class="texto">En el pasillo simulado de la universidad, con su radio de giro, el vehículo oscilaba. El proyecto pasó a la navegación con mapa.</div></div>

<div class="fase">Segundo semestre · integración</div>

<div class="hito decision"><div class="cuando">5 de agosto</div><div class="titulo">Contrato de interfaces antes del código <span class="tipo decision">decisión</span></div><div class="texto">Se fijó qué pieza habla con cuál y en qué formato, antes de escribir el coordinador. El mismo día los dos vehículos recibieron el software comunitario de ROS 2 sobre su tarjeta original.</div></div>

<div class="hito decision"><div class="cuando">14 de agosto</div><div class="titulo">Cronograma y alcance firmados con el director <span class="tipo decision">decisión</span></div><div class="texto">El director aprobó el cronograma replanificado del segundo semestre y las decisiones de alcance.</div></div>

<div class="hito problema"><div class="cuando">21 de agosto</div><div class="titulo">«Llegué», pero no había llegado <span class="tipo problema">problema</span></div><div class="texto">En la primera navegación por el edificio simulado, una de tres metas devolvió éxito con el vehículo a 0,296 m, fuera de la tolerancia. Desde entonces el éxito se mide con la posición del vehículo y nunca con lo que dice la navegación.</div></div>

<div class="hito decision"><div class="cuando">22 de agosto</div><div class="titulo">El protocolo de evaluación se escribe antes de medir <span class="tipo decision">decisión</span></div><div class="texto">Métricas, criterio de éxito, tamaño de muestra y causas de descarte quedaron fijados antes de instrumentar, para que los datos no pudieran acomodar el criterio.</div></div>

<div class="hito cambio"><div class="cuando">Agosto</div><div class="titulo">Un mundo de simulación por piso <span class="tipo cambio">cambio</span></div><div class="texto">Con los dos pisos en un mismo mundo, el láser simulado veía paredes del otro piso en 61 de 1701 posiciones. Cada piso pasó a ser un mundo con su propio proceso.</div></div>

<div class="hito prueba"><div class="cuando">2 de septiembre</div><div class="titulo">La interfaz web, contra el coordinador real <span class="tipo prueba">prueba</span></div><div class="texto">La página se verificó contra el coordinador, no contra un simulacro: catálogo, misión, etapas y botón.</div></div>

<div class="hito prueba"><div class="cuando">4 y 5 de septiembre</div><div class="titulo">Treinta misiones en simulación <span class="tipo prueba">prueba</span></div><div class="texto">Campaña válida, sin descartes: 26 de 30 misiones completadas. Los cuatro fallos se quedaron cortos por precisión de llegada; ninguno fue de coordinación.</div></div>

<div class="hito decision"><div class="cuando">10 y 14 de septiembre</div><div class="titulo">Confirmación de piso y cancelación <span class="tipo decision">decisión</span></div><div class="texto">A pedido del director: la misión espera que la persona confirme el cambio de piso, y el botón de cancelar devuelve el robot a su escalera. El botón existía pero no hacía nada, y nadie lo había notado.</div></div>

<div class="hito prueba"><div class="cuando">14 de septiembre</div><div class="titulo">Llega el segundo vehículo <span class="tipo prueba">prueba</span></div><div class="texto">Después de 31 días en reparación. La latencia entre los dos vehículos se midió con 600 mensajes, sin pérdidas.</div></div>

<div class="hito problema"><div class="cuando">22 de septiembre</div><div class="titulo">La «avería» que no era del vehículo <span class="tipo problema">problema</span></div><div class="texto">Durante tres semanas un fallo se atribuyó al vehículo. Era un problema de permisos de la memoria compartida entre procesos. Ese mismo día se superaron las pruebas de actuación y de coexistencia de los dos vehículos.</div></div>

<div class="hito prueba"><div class="cuando">25 de septiembre</div><div class="titulo">Nav2 navega el vehículo real por primera vez <span class="tipo prueba">prueba</span></div><div class="texto">Un recorrido de 4,8 m con mapa guardado y localización.</div></div>

<div class="hito decision"><div class="cuando">28 de septiembre</div><div class="titulo">Tolerancia de 0,5 m en los vehículos <span class="tipo decision">decisión</span></div><div class="texto">El director la fijó para los vehículos reales; la simulación conserva 0,25 m.</div></div>

<div class="hito problema"><div class="cuando">30 de septiembre</div><div class="titulo">El pasillo uniforme no deja medir el avance <span class="tipo problema">problema</span></div><div class="texto">En el hall del piso 2 la odometría registró el 73 % del avance real y la localización se desvió más de 2 m. Además, el modelo del hall tenía una pared 0,84 m fuera de sitio.</div></div>

<div class="fase">Octubre · validación con los vehículos</div>

<div class="hito cambio"><div class="cuando">2 de octubre</div><div class="titulo">Pisos 3 y 4: un pasillo con estructura <span class="tipo cambio">cambio</span></div><div class="texto">Con salones, casilleros, ascensor y escalera a la vista, la misma odometría midió +3,3 % y −4,6 %. Prueba de odometría superada; el director aceptó el cambio de sitio el 5 de octubre.</div></div>

<div class="hito cambio"><div class="cuando">5 de octubre</div><div class="titulo">La unidad inercial de la tarjeta <span class="tipo cambio">cambio</span></div><div class="texto">La tarjeta traía un giroscopio que nadie usaba. Integrado con un filtro, el rumbo dejó de derivar, y el margen de llegada bajó de 1,0 a 0,5 m.</div></div>

<div class="hito prueba"><div class="cuando">7 de octubre</div><div class="titulo">Navegación de un vehículo <span class="tipo prueba">prueba</span></div><div class="texto">Tres tramos encadenados en el piso 4 sin tocar el vehículo, con llegadas medidas a 0,06 m y 0,45 m.</div></div>

<div class="hito problema"><div class="cuando">8 de octubre</div><div class="titulo">Las tarjetas se saturan con los dos vehículos <span class="tipo problema">problema</span></div><div class="texto">Con unos cuarenta procesos anunciándose por la red, la carga de una tarjeta pasó de 6 a entre 17 y 33.</div></div>

<div class="hito decision"><div class="cuando">9 de octubre</div><div class="titulo">Coordinador en el portátil y topología en estrella <span class="tipo decision">decisión</span></div><div class="texto">Cada vehículo solo se anuncia al portátil. Las tarjetas bajaron al 54 % y 59 % en reposo.</div></div>

<div class="hito decision"><div class="cuando">13 de octubre</div><div class="titulo">Sorteo de las misiones y llegada verificada <span class="tipo decision">decisión</span></div><div class="texto">Diez misiones entre pisos, sorteadas con semilla antes de correr. El coordinador verifica cada llegada 1,5 s después de que el vehículo se detiene.</div></div>

<div class="hito prueba"><div class="cuando">16 de octubre</div><div class="titulo">El sistema completo en el edificio <span class="tipo prueba">prueba</span></div><div class="texto">Nueve misiones del sorteo completadas con relevo entre los pisos 3 y 4. Fin de la toma de datos.</div></div>

</div>
