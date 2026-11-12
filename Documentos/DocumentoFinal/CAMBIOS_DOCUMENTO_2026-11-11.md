# Cambios al documento entregado al director

Todas las correcciones del 11 de noviembre de 2026, de las dos tandas, sobre el documento que se le entregó al director Armando: `main_objetivos.pdf`, versión del commit `8fa9f2a`, con 59 hojas y 45 numeradas. Las páginas son las que trae impreso ese PDF. El detalle de cada corrección, con la frase original del director, está en `CORRECCIONES_2026-11-11.md`.

**Estado:** todo aplicado en `main_objetivos.tex`, sin commit, salvo lo que es de la presentación. El PDF quedó en 62 hojas, 48 numeradas. La discusión va como capítulo aparte, por decisión de los autores, que aceptan que la extensión crezca si el documento queda bien.

## 1. Cambios en el orden del documento

| Página | Corrección | Cambio | Estado |
|---|---|---|---|
| Nota de aceptación | Mes en minúscula | «noviembre de 2026» → «Noviembre de 2026» | Hecho |
| vi–vii, Resumen y abstract | «written» y «before»; «of ten randomised»; redactarlo en inglés | «a protocol defined prior to instrumenting the system»; «Nine out of ten randomised missions… were completed»; el abstract se escribió primero y el resumen es su traducción; 249 y 231 palabras | Hecho |
| viii, Glosario | Agente debe ser más general | «Sistema que percibe su entorno por medio de sensores y actúa sobre él de forma autónoma…»; entra «entorno estructurado» | Hecho |
| viii, Abreviaturas | Conceptos de ingeniería, no términos técnicos | Salen AWS, DDS, JSON y Nav2, que se explican en el texto la primera vez; quedan AMCL, GED, HRI, IMU, ROS y SLAM | Hecho |
| 1, Introducción | Entorno estructurado; «desde hace años»; «encarecer» | «Un edificio es un entorno estructurado…»; «tiene base teórica desde 2004, cuando Gerkey y Matarić…»; «aumentan los requerimientos tecnológicos de la plataforma, y con ellos los costos»; «se cargó software libre en dos agentes de la plataforma AWS DeepRacer» | Hecho |
| 2, Planteamiento del problema | «Encarecer» | «sin aumentar los requerimientos tecnológicos, y con ello los costos, ni modificar el edificio» | Hecho |
| 4–5, Antecedentes | No hay estado del arte | La sección 2.1 pasa a «Estado del arte», y la tabla 2.1 compara uno por uno los 21 trabajos (qué propone cada uno y su relación con este proyecto); ocupa dos hojas | Hecho |
| 6, Marco conceptual | HRI como en el glosario | «La interacción humano-robot toma aquí…» → «La HRI toma aquí…»; además, DDS y JSON quedan definidos en su primer uso | Hecho |
| 13, Escenarios | «No dio» | «no entregó un mapa utilizable» | Hecho |
| 16, 3.1.5 | Reglas en viñetas | Las tres reglas de comunicación van en una lista | Hecho |
| 17–18, plataforma y figura 3.6 | «Construidos» → «cargados» | «El sistema se cargó en dos agentes…»; pie: «Los dos agentes físicos, con el sistema cargado en la plataforma AWS DeepRacer» | Hecho |
| 19, 3.2.1 | «No se actualiza desde hace años»; «la universidad ya tenía dos» | Se quitó la frase de DonkeyCar, porque es falsa: hubo versiones en marzo y agosto de 2026. «el laboratorio de robótica de la universidad ya contaba con dos» | Hecho |
| 21–23, 3.2.5 | «Contradiría»; falta el trabajo de 5 GHz; «52 y el 63 %»; las MAC sobran; ¿por qué 2 Hz? | Ver la lista debajo de la tabla | Hecho |
| 25, tabla 3.8 | «No dio» | «no entregó» | Hecho |
| 27, figura de la interfaz | Fecha irrelevante | «durante las pruebas del 23 de octubre» → «durante las pruebas con los agentes físicos» | Hecho |
| 29, 3.4 | «del 16 de octubre» | Se quitó | Hecho |
| 33, 4.3 | «El 16 de octubre»; los autores no se nombran como usuarios | «El sistema completo funcionó…»; «Cada misión se pidió desde la interfaz web en un teléfono, y desde la misma interfaz se validó el cambio de piso en cada relevo» | Hecho |
| 34, 4.3.1 | Porcentaje sin símbolo | «del 70,1 % al 100 %» | Hecho |
| 36, 4.3.3 | Reducir texto con tablas | La primera oración del criterio queda como texto. Las incidencias pasan a una tabla de cinco filas: ocho intentos de la misión 1, primer intento de la misión 1, primer intento de la misión 2, ascensor equivocado y misión 10 | Hecho (tabla 4.5) |
| 36, 4.4 | Reducir texto con tablas | Una oración de entrada y una tabla de dos filas: continuidad del servicio y umbral del mapa simulado | Hecho (tabla 4.6) |
| — | Discusión | Explicar lo que se hizo, de lo general a lo técnico, a partir de las explicaciones que hoy están en las conclusiones y comparándolo con el estado del arte | Hecho: capítulo 5, «Discusión» |
| 37, Conclusiones | Responder a los objetivos sin explicaciones | Un párrafo por objetivo con lo que se hizo y el resultado general más relevante; las causas pasan a la discusión | Hecho |
| 38, Trabajos futuros | Son mejoras más que trabajo futuro | Un párrafo y una tabla con las seis mejoras, y párrafos nuevos desde la literatura: más de dos pisos con optimización multiagente y MARL, y varios agentes en el mismo piso con MARL. El «54 % y el 59 %» ya está corregido | Hecho (tabla 5.1 y tres párrafos) |

Cambios en 3.2.5, páginas 21 a 23:
- «contradiría» se reescribió como «y también una red móvil, ya que el sistema está diseñado para funcionar sin salida a internet».
- Hay un párrafo nuevo sobre cómo se habilitó la banda de 5 GHz: base regulatoria instalada, de 0 a 13 canales utilizables y de 802.11n a 802.11ac.
- Los rangos de porcentaje llevan el símbolo en los dos números: «52 % y el 63 %» y «68 % y el 74 %».
- La tabla 3.6 y la figura 3.8 quedaron sin las MAC; la figura se regeneró.
- Se explica que de los 2 Hz salen las cotas de la red y por qué esa frecuencia alcanza.

Fuera del documento:
- En la presentación, las conclusiones van con ícono por nivel (brazo para ingeniería, engranajes para técnica), y hay que cambiar a mano la figura de la red y los trabajos futuros.
- En el sitio, la página de la semana 10 todavía dice que DonkeyCar no se actualiza.

## 2. Dónde se cruzan las correcciones

1. **Conclusiones por objetivo (3) y por nivel (4).** La plantilla y la corrección 3 piden un párrafo por objetivo; la presentación de Katherin las agrupa por nivel. Propuesta:
   - en el documento, la discusión va de lo general a lo técnico y las conclusiones, por objetivo;
   - en la presentación, cada conclusión lleva el ícono de su nivel;
   - para que haya de los dos niveles, la del segundo objetivo se parte en dos: la plataforma, como ingeniería, y la odometría, la tracción y la tarjeta, como técnica;
   - la general, con el ícono de la cabeza, responde la pregunta problema.
2. **Tablas (2) y discusión (3).** Las limitaciones quedan en la tabla de 4.4 con sus cifras, y la discusión explica las causas sin repetirlas. Si la discusión va al final de Resultados, el orden es 4.4 Limitaciones y 4.5 Discusión.
3. **Trabajos futuros (5) y estado del arte (primera tanda).** Los trabajos con aprendizaje por refuerzo ya están en la tabla 2.1: Xu et al. (2026) usa MARL para asignar tareas entre robots, y Luo et al. (2025) elige entre ascensor y escalera. Los trabajos futuros se apoyan en ellos, y la única referencia nueva sería Orr y Dutta (2023), que hay que leer antes de citarla.
4. **Conclusiones (3) y la regla del 4 de noviembre.** Esa regla pedía lo obtenido, su causa y lo que implica. Ahora la causa pasa a la discusión y la conclusión queda sin explicación. Al aplicar el cambio hay que actualizar la guía de redacción.
5. **Tablas (2) y lo que alargó la primera tanda.** Los párrafos de 5 GHz y de 2 Hz alargaron 3.2.5. Con el criterio de la corrección 2, el antes y el después de 5 GHz (canales, estándar del enlace y percentil 95 de la latencia) caben en una tabla corta. Es opcional.
6. **Autores como usuarios (1) y comité de ética.** El documento ya no dice quién hizo de usuario. Si se escribe algo sobre ética, tiene que decirse sin nombrar a los autores como usuarios, por ejemplo: «las pruebas no incluyeron participantes externos ni registraron datos personales».
7. **Extensión.** Hoy son 60 hojas, una más que la entregada, por la tabla del estado del arte.
   - Las tablas de 4.3.3 y 4.4 ocupan más o menos lo mismo que el texto que reemplazan.
   - La discusión suma entre una y dos hojas, y los trabajos futuros media.
   - Se puede esperar entre 61 y 63 hojas, por encima de las 60 que sugirió el director.

## 3. Decisiones pendientes

1. Discusión: decidido, capítulo aparte (el 5).
2. Orr y Dutta (2023): se leyó el resumen, se comprobó en Crossref y se cita en trabajos futuros.
3. Tabla 3.8 (sim2real) y comité de ética: se respondieron como preguntas y el documento no cambia, salvo que se decida otra cosa.
4. El puerto de la interfaz (8000 la página, 9090 rosbridge) no está en el documento.
5. La versión integrada no tiene estas correcciones en sus capítulos propios.
