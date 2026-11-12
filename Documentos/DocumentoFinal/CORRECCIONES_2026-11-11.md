# Correcciones al documento final, 11 de noviembre de 2026

Primera tanda, dictada por los autores el 11 de noviembre de 2026 sobre `main_objetivos.pdf`, la versión que se envió al director Armando. Las páginas, secciones, figuras y tablas son las de ese PDF; las líneas, las de `capitulos_objetivos/` y de los capítulos comunes que usa `main_objetivos.tex`. Cada corrección vale también para `main_integrada`, salvo donde se dice otra cosa.

**Estado:** aplicado el 11 de noviembre en `main_objetivos.tex`, que quedó en 60 hojas, 46 numeradas. Las preguntas de 5.1, 5.3 y 5.4 no cambian el documento. El resumen para Jonny está en `Correcciones_2026-11-11_Jonny.pdf`. Falta la segunda tanda, que el director envió el mismo 11 de noviembre.

Respuestas de los autores a la sección 7: (1) la redacción en inglés se la sugirió el director pensando que a la IA le resulta más fácil, y se aplicó al resumen y al abstract; (2) se preguntó si estado del arte y antecedentes son lo mismo, y la sección pasó a «Estado del arte», con una tabla de comparación por trabajo; (3) la lectura de 1.6 es la correcta; (4) la figura de la red se regeneró sin las MAC. Los 2 Hz se explicaron como propone 5.2. La tabla 3.8 y el comité de ética quedan sin cambio en el documento.

## 1. Preliminares

### 1.1 Mes en minúscula

- En autoridades académicas no hay ninguna fecha. La fecha está en la hoja siguiente, la nota de aceptación, donde se lee «noviembre de 2026» al comienzo de una línea, debajo de «Colombia».
- Sale de `\ustames{noviembre}` en cada `main*.tex`.
- Cambio: `\ustames{Noviembre}`. Dentro de una oración el mes va en minúscula, pero aquí empieza la línea.

### 1.2 ¿«Web» va en mayúscula?

No. En «página web» e «interfaz web» es un adjetivo común y va en minúscula. La mayúscula solo cabe en «la Web» como nombre propio de la red mundial, y el documento no la usa así. «Amazon Web Services» es nombre de marca y queda igual. Sin cambio.

### 1.3 HRI en lugar del término completo

- En la versión enviada no aparece «human-robot interface». Aparece «interacción humano-robot», escrita completa, en el marco conceptual (`06-marco-referencial.tex:47`, en negrita) y en las palabras clave.
- La plantilla pide definir cada abreviatura en su primer uso. En el cuerpo, ese uso es el tercer objetivo específico, que ya dice «interacción humano-robot (HRI)» y no se toca porque es texto oficial. Desde ahí se usaría «HRI», como en el glosario. En el marco conceptual quedaría «La HRI toma aquí la forma de una interfaz web…».
- Las palabras clave conservan el término completo.
- Si el director lo vio en otra página, falta saber cuál.

### 1.4 Resumen y abstract

- «a protocol written before instrumenting the system» → «a protocol defined prior to instrumenting the system» («written» por «defined», y «before» por «prior to»). En el resumen, para que digan lo mismo: «un protocolo definido antes de instrumentar el sistema».
- «Of ten randomised missions with the physical agents, one per floor, nine were completed with a handover» → «Nine out of ten randomised missions with the physical agents, one per floor, were completed with a handover».
- Sugerencia del director: redactarlo en inglés y pasarlo de ahí al español. Hoy los dos no son traducción exacta; por ejemplo, el resumen dice «La principal limitación está en la plataforma…» y el abstract empieza la frase por «Traction does not respond…». Se propone escribir primero el abstract y derivar de él el resumen.
- Pregunta abierta: si la sugerencia es solo para el resumen o para todo el documento.

### 1.5 Definición de agente

- Hoy (`capitulos_60/03-glosario-abreviaturas.tex:10`): «Cada uno de los dos robots móviles del sistema, construidos sobre AWS DeepRacer y dedicados cada uno a un piso». Define a los robots del proyecto, no el concepto.
- Propuesta: «Agente. Sistema que percibe su entorno por medio de sensores y actúa sobre él de forma autónoma para cumplir una tarea. En este trabajo, cada uno de los dos robots móviles terrestres del sistema, uno por piso.»
- La parte general sigue las definiciones clásicas de Russell y Norvig (percibe con sensores y actúa sobre el entorno) y de Wooldridge (actúa con autonomía para cumplir sus objetivos). Si se citan, son referencias antiguas, que se admiten solo por ser muy relevantes.
- En la integrada está en `capitulos/03-glosario-abreviaturas.tex:22`.

### 1.6 Conceptos y técnicas de ingeniería en lugar de términos técnicos

- AMCL y HRI quedan como están, según la corrección.
- Lectura de la corrección: las listas deben recoger conceptos y técnicas de ingeniería, no nombres de herramientas o de formatos.

| Abreviatura | Qué es | Propuesta |
|---|---|---|
| AMCL, SLAM | Técnicas de localización y mapeo | Se quedan |
| HRI, IMU | Campo de estudio y componente | Se quedan |
| ROS | Base de todo el sistema | Se queda |
| GED | Grupo de investigación | Se queda |
| AWS, DDS, JSON, Nav2 | Marca, protocolo, formato y paquete | Salen de la lista y se explican en el texto la primera vez |

- El glosario enviado ya tiene casi solo conceptos. Podría entrar «entorno estructurado» (sección 2.1).
- La integrada tiene 30 términos y habría que revisar además mapa de costos, middleware robótico, banda muerta, PID, PWM y CONPES.
- Falta confirmar que esta es la lectura correcta.

## 2. Introducción y contextualización

### 2.1 Entorno estructurado

- Párrafo: `04-introduccion.tex:8-16`, el primero de la introducción.
- Propuesta: «Un edificio es un entorno estructurado: sus pasillos, salones y escaleras siguen un orden fijo. Aun así, quien entra por primera vez a un edificio grande construye un mapa mental con información parcial…».

### 2.2 «Desde hace años»

- `04-introduccion.tex:17`. La oración ya cita a Gerkey y Matarić (2004).
- Propuesta: «La robótica móvil colaborativa resuelve tareas parecidas, y el reparto de trabajo entre varios robots tiene base teórica desde 2004, cuando \textcite{gerkey2004taxonomy} formalizaron la asignación de tareas en sistemas multirrobot.»

### 2.3 «Encarecer»

- `04-introduccion.tex:25`: «En todos los casos se encarece la plataforma o se interviene la infraestructura» → «En todos los casos aumentan los requerimientos tecnológicos de la plataforma, y con ellos los costos, o se interviene la infraestructura».
- `05-contextualizacion.tex:25`: «sin encarecer la plataforma ni modificar el edificio» → «sin aumentar los requerimientos tecnológicos, y con ello los costos, ni modificar el edificio».
- Opcional, para que el resumen diga lo mismo: «dos opciones costosas» y «Both are expensive».

## 3. Marco referencial

### 3.1 Estado del arte

- Hoy el marco empieza con «Antecedentes»: cinco párrafos y la tabla 2.1, que agrupa por líneas de trabajo. No hay estado del arte ni una comparación trabajo por trabajo.
- La plantilla no lo pide con ese nombre: pide marco conceptual, teórico, legal y ambiental. Aun así, la corrección lo pide.
- La integrada tiene antecedentes más completos: cinco subsecciones (robots guía, navegación en interiores, coordinación, movilidad entre pisos y distribución del cómputo) y el aporte frente a ellas.
- Propuesta: convertir «Antecedentes» en «Estado del arte», con el texto de la integrada.
- Se añadiría una tabla comparativa de los trabajos citados, con autor y año, problema, cómo resuelve el cambio de piso, plataforma y tipo de evaluación. Las referencias serían de 2021 en adelante.
- Suma hojas, así que depende de la extensión que acepte el director.

## 4. Desarrollo

### 4.1 Reglas de comunicación en viñetas (3.1.5, pág. 16)

`07-desarrollo.tex:158`: hoy las tres reglas van en una sola oración separada por punto y coma. Pasan a una lista de tres viñetas. La integrada ya las tiene en lista numerada; se dejan iguales en las dos versiones.

### 4.2 «No dio» → «no entregó»

- `07-desarrollo.tex:109`: «El mapeo con SLAM en los propios agentes no entregó un mapa utilizable…».
- La celda «Mapa» de la tabla 3.8 (`:372`) dice lo mismo y se cambia igual.
- La integrada tiene las mismas dos.

### 4.3 Pie de la figura 3.6 (pág. 18)

- Hoy: «Los dos agentes físicos, construidos sobre la plataforma AWS DeepRacer.»
- La corrección pide «cargados», en el sentido de *uploaded*: el sistema se cargó en vehículos comerciales, que no se construyeron.
- Propuesta: «Los dos agentes físicos, con el sistema cargado en la plataforma AWS DeepRacer.»
- El mismo «construidos» está en la definición de agente (1.5). En la integrada también está en la abreviatura AWS, «sobre la que se construyeron los agentes».

### 4.4 DonkeyCar: «no se actualiza desde hace años» (3.2.1, pág. 18)

- Ubicación: `07-desarrollo.tex:240`. La corrección propone «No se ha actualizado».
- La afirmación es falsa en las dos formas. Se comprobó el 11 de noviembre en GitHub:
  - DonkeyCar publicó la versión 5.3.0 el 29 de marzo de 2026 y la 5.4.0 el 22 de agosto de 2026, y su último cambio es del 2 de noviembre de 2026.
  - Su simulador, gym-donkeycar, publicó una versión el 6 de octubre de 2025.
- La frase viene del entregable de la semana 10 (`CRONOLOGIA.md:36`) y no se verificó entonces. También está en `sitio/paginas/semanas/s10.md:20`.
- Sí se sostiene la limitación con ROS 2: el simulador no se comunica con ROS 2, y no existía un modelo para Gazebo con dirección Ackermann que funcionara en Humble.
- Propuesta: quitar lo de la actualización y empezar por esa limitación, que sí se puede verificar. Hay que explicar por qué no se usa la redacción propuesta.

### 4.5 «La universidad ya tenía dos» (3.2.1)

`07-desarrollo.tex:244` → «el laboratorio de robótica de la universidad ya contaba con dos».

### 4.6 Comunicación (3.2.5, págs. 21 a 23)

a) «Contradiría». En `:287` dice «una red móvil contradiría el diseño, que funciona sin salida a internet». Propuesta: «y una red móvil se descartó, ya que el sistema está diseñado para funcionar sin salida a internet».

b) El trabajo para habilitar 5 GHz en los agentes. Hoy hay una sola oración (`:305`). Los datos están en `Evidencia/S26_red_5ghz_regulatorio.md`, de la sesión del 5 de octubre con Jonny:
- A las tarjetas de los dos agentes les faltaba la base de datos regulatoria del sistema operativo, y el núcleo dejaba las 31 frecuencias de 5 GHz en solo escucha: veían las redes, pero no podían transmitir, y no aparecía ningún mensaje de error.
- Se instaló la base en los dos agentes, con un servicio que fija el dominio regulatorio en cada arranque, y se reiniciaron, porque la base solo se lee al arrancar.
- Cada agente pasó de 0 a 13 canales utilizables, con los canales 36 a 48 a 23 dBm, y el enlace pasó de 802.11n a 802.11ac.
- Con eso se midió la latencia entre los dos agentes sobre 5 GHz: el percentil 95 bajó de 20,76 a 11,12 ms.
- Salvedad de la misma evidencia: la tarjeta informa el dominio de Estados Unidos y no el de Colombia, así que no debe escribirse que opera bajo el dominio colombiano.
- Propuesta: un párrafo propio con esos datos, antes del párrafo sobre el descubrimiento entre procesos.

c) Porcentajes. «entre el 52 y el 63 %» → «entre el 52 % y el 63 %». Con el mismo criterio cambian:
- «68 % y el 74 %», en el mismo párrafo;
- «54 % y el 59 %», en `10-trabajos-futuros.tex:24`;
- «70,1 % al 100 %», en `08-resultados.tex:102`.

d) Las direcciones MAC salen.
- Tabla 3.6 (pág. 22): se quita la columna, el pie pasa a «Direcciones IP de los equipos de la red…» y «reservada por su MAC» pasa a «reservada en el enrutador».
- Figura 3.8 (pág. 23): se regenera `herramientas/figura_red.py` sin las MAC y se quita «y MAC» del pie.
- La tabla y la figura también están en el sitio (`sitio/paginas/como-funciona.md:60-71`), y la figura en la presentación. Hay que actualizar los dos.

e) Los 2 Hz (`:318`): ver 5.2.

### 4.7 Fecha del 16 de octubre

- `07-desarrollo.tex:449`: «La campaña con los agentes físicos, del 16 de octubre, en los pisos 3 y 4…» → se quita la fecha.
- `08-resultados.tex:96`: «El 16 de octubre, el sistema completo funcionó…» → «El sistema completo funcionó…».
- Con el mismo criterio, el pie de la figura de la interfaz (`07-desarrollo.tex:409`) cambia de «durante las pruebas del 23 de octubre» a «durante las pruebas con los agentes físicos».
- Las fechas de la tabla de videos del anexo A se quedan, porque son el registro de cada video.

## 5. Preguntas, con lo que dice el repositorio

### 5.1 ¿Qué puerto usa la interfaz web? ¿El 8080?

- No. El portátil sirve la página por HTTP en el puerto 8000 (`herramientas/servir_interfaz.py`).
- La página habla con ROS 2 por el WebSocket de rosbridge en el puerto 9090, el que trae por omisión (`interfaz_web/js/app.js:30`, `herramientas/coordinador_portatil.sh:134`).
- ROS 2 no tiene un puerto fijo: DDS calcula los puertos a partir del número de dominio y del orden de cada participante (`REQUISITOS.md`, RF-15).
- El documento hoy no da ningún puerto. Si se quiere, cabe una oración en 3.2.5 o en el tercer objetivo.

### 5.2 ¿Por qué 2 Hz?

- El valor se fijó en el contrato de interfaces el 10 de agosto de 2026 (commit `8624a08`) y pasó a requisito sin una justificación escrita.
- Sí está escrito cómo salen de él las cotas de la red (`REQUISITOS.md`, RF-15):
  - a 2 Hz, el periodo es de 500 ms;
  - con una latencia de ida de ese orden, la posición del agente que ve el coordinador quedaría atrasada una muestra;
  - el techo es entonces de 1000 ms de ida y vuelta, y las cotas de 100 ms en la mediana y 250 ms en el percentil 95 dejan márgenes de 10 y de 4.
- Nada de eso está en el documento: la oración de la página 23 dice «a partir de los 2 Hz» sin explicar cómo.
- Argumento que se puede añadir sobre el valor mismo, con datos del repositorio:
  - a la velocidad deseada de los agentes físicos, 0,5 m/s (`nav2_params_jazzy.yaml`), el agente avanza 0,25 m entre dos estados, la mitad de la tolerancia de llegada de 0,5 m;
  - la llegada se verifica con una pose tomada 1,5 s después de que Nav2 da la meta por alcanzada, así que la frecuencia no limita la verificación;
  - el estado sirve para la página y para el coordinador. El control del movimiento corre a bordo de cada agente, con su propia frecuencia.
- Ese argumento se arma ahora, no cuando se fijó el valor. Hay que decidir si se escribe así.

### 5.3 ¿La tabla 3.8 se basa en alguna metodología sim2real?

- No. Registra lo que hubo que cambiar al pasar de la simulación a los agentes, a partir de la evidencia de campo. No sigue un método de la literatura y el documento no cita ninguno.
- Casi toda la literatura sim2real trata de controladores aprendidos, por ejemplo con aprendizaje por refuerzo, y el proyecto no los usa.
- Opción a: decir en el párrafo que presenta la tabla que es una comparación de la implementación, sin método sim2real. Se recomienda esta.
- Opción b: enmarcarla con una referencia sobre la brecha entre simulación y realidad.
  - Candidata, con la ficha comprobada en Crossref y todavía sin leer: Höfer et al., «Sim2Real in Robotics and Automation: Applications and Challenges», *IEEE Transactions on Automation Science and Engineering* 18(2), 398-400, 2021, DOI 10.1109/TASE.2021.3064065.
  - Son tres páginas, y hay que leerlas antes de citarlas.

### 5.4 ¿Hasta qué punto la interfaz web queda fuera del comité de ética?

Lo que muestra el repositorio:
- La página no pide ni guarda datos de quien la usa: no tiene registro de usuario, ni cookies, ni almacenamiento local (revisado en `interfaz_web/`).
- El registro de cada misión guarda origen, destino, pisos y marcas de tiempo, pero ningún dato de la persona.
- En las pruebas, los autores hicieron de usuario (`08-resultados.tex:96`). No hubo participantes externos, ni encuestas, ni medidas sobre personas.
- Lo único que alcanza a terceros son los videos de los pasillos, que pueden mostrar a personas que pasaban. `PENDIENTES.md` ya tiene abierta la pregunta de si hubo personas en el pasillo durante la campaña.

Tal como se hizo, el trabajo es un desarrollo y una prueba de ingeniería sin participantes humanos. Necesitaría el aval de un comité de ética, con consentimiento informado, en tres casos:
- si se evaluara con usuarios distintos de los autores, por ejemplo en un estudio de usabilidad o de orientación con visitantes;
- si se registraran datos que identifiquen a alguien;
- si se publicaran videos con personas reconocibles, lo que toca la Ley 1581 de 2012 de protección de datos personales.

Ese límite se puede escribir en el marco legal o en trabajos futuros. Sin embargo, reabre en parte la decisión del 20 de octubre de no desarrollar datos personales en el marco legal (`PENDIENTES.md`, sección 3). Antes de afirmarlo en el documento hay que confirmar con el director cuál es la norma de la universidad.

## 6. Dónde se aplica cada cambio

| Archivo | Secciones de este documento |
|---|---|
| `main*.tex` | 1.1 |
| `capitulos/02-resumen-abstract.tex` | 1.4, 2.3 (opcional) |
| `capitulos_60/03-…` y `capitulos/03-…` (glosario) | 1.5, 1.6, 4.3 |
| `04-introduccion.tex`, en las dos versiones | 2.1, 2.2, 2.3 |
| `capitulos/05-contextualizacion.tex` | 2.3 |
| `06-marco-referencial.tex` | 1.3, 3.1 |
| `07-desarrollo.tex` | 4.1 a 4.7, 5.2, 5.3 |
| `08-resultados.tex` | 4.6 c, 4.7 |
| `capitulos/10-trabajos-futuros.tex` | 4.6 c, 5.4 si se escribe ahí |
| `herramientas/figura_red.py`, `sitio/paginas/como-funciona.md` y la presentación | 4.6 d |
| `sitio/paginas/semanas/s10.md` | 4.4 |

## 7. Decisiones pendientes

1. ¿La redacción en inglés es solo para el resumen o para todo el documento?
2. ¿Se añade el estado del arte con tabla comparativa, aunque sume hojas?
3. ¿La lectura de 1.6 sobre conceptos de ingeniería es la correcta?
4. ¿Se escribe la justificación de los 2 Hz de 5.2?
5. Tabla 3.8: ¿se dice que no sigue un método sim2real, o se busca una referencia?
6. Comité de ética: falta confirmar la norma de la universidad.
7. DonkeyCar: la redacción propuesta mantendría un dato falso; falta decidir cómo se explica.

## 8. Segunda tanda: correcciones del director

El usuario las pasa una por una. Se anotan aquí a medida que llegan y se aplican todas juntas al final, cuando se regeneran `main_objetivos.pdf` y `Correcciones_2026-11-11_Jonny.pdf`. Aplicadas el 11 de noviembre, salvo la 4, que es de la presentación: `main_objetivos.pdf` quedó en 62 hojas, 48 numeradas. Los autores decidieron la discusión como capítulo aparte y que la extensión puede crecer «siempre y cuando el documento quede bien».

| # | Corrección del director | Dónde | Qué se hace | Estado |
|---|---|---|---|---|
| 1 | «Este párrafo y eso de que los autores hicieron de usuario no se dice, sería más bien algo como "se realizó validación del cambio de piso desde la interfaz web para móvil"» | Resultados, sistema completo, primer párrafo (`08-resultados.tex:96`); es la única mención en la versión por objetivos | «Cada misión se pidió desde la página web en un teléfono, y los autores hicieron de usuario: acompañaron a los agentes y confirmaron el cambio de piso» → «Cada misión se pidió desde la interfaz web en un teléfono, y desde la misma interfaz se validó el cambio de piso en cada relevo» | Aplicada |
| 2 | «Una forma de reducir tanto texto es poner tablas, estos párrafos me parecen mucho que aplica esto» | Resultados: 4.3.3 «Criterio de conteo e incidencias», segundo párrafo (`08-resultados.tex:145`), y 4.4 «Limitaciones de la medición», los dos párrafos (`:151` y `:153`) | **4.3.3:** se deja la primera oración del criterio («cada misión cuenta una sola vez, con el intento que se completó…») y lo demás pasa a una tabla de intentos que la tasa no cuenta, con columnas misión, qué ocurrió, causa y cómo se contó. Filas: misión 1, ocho intentos rechazados o abortados (navegación detenida tras apagarse el portátil por batería; cadenas reiniciadas con la pose de salida); misión 1, primer intento después del reinicio (llegada rechazada a 0,526 m del ascensor; completada al segundo); misión 2, primer intento (sin la pose del agente para verificar; completada al segundo); intento al ascensor del piso 4 (destino equivocado por dos ascensores con el mismo nombre en la página; no es del sorteo); misión 10 (el portátil se apagó otra vez por batería; fuera de la tasa). **4.4:** una oración de entrada y una tabla con columnas limitación, qué se encontró, efecto en el resultado y estado. Filas: continuidad del servicio (se cumple por construcción en las 30 misiones; se respalda con el intervalo del relevo, mediana 0,1 s y máximo 0,2 s); umbral de celdas libres del mapa simulado (0,25 frente a 0,196 de las desconocidas; 10 908 celdas, el 14,5 % del mapa, leídas como libres; no cambia el veredicto, porque los cuatro fallos fueron de llegada; sin verificar que ninguna trayectoria las cruzara; corregido a 0,10). Ninguna cifra sale | Aplicada |
| 3 | Sobre las conclusiones: (1) «Habría que preguntar si se puede colocar "Discusión" o modificar el capítulo para que sea "Discusión y conclusiones"». (2) «En la discusión presentas y explicas lo que se hizo siempre yendo de mayor nivel a menor nivel (de ing a tec)». (3) «En las conclusiones respondes a los objetivos pero presentando lo que se hizo para cada uno, solo los resultados generales más relevantes y sin explicaciones». Referencia del usuario: respuesta de DeepSeek sobre discusión frente a conclusiones (la discusión interpreta y dialoga con la literatura; las conclusiones cierran respondiendo a los objetivos) | `capitulos/09-conclusiones.tex` (compartido por las tres versiones) y, según lo que se decida, `08-resultados.tex` | **(1) Pregunta abierta.** La plantilla no trae capítulo de discusión: pide resultados («argumentando, analizando datos obtenidos…») y conclusiones («un párrafo que exprese lo obtenido en cumplimiento de cada objetivo específico»). Hay tres opciones: capítulo «Discusión y conclusiones» en lugar de «Conclusiones»; capítulo «Discusión» aparte; o «Discusión» como última sección de Resultados, que es la única que no cambia los capítulos de la plantilla. **(2) Discusión**, de lo general a lo técnico: primero el problema planteado como coordinación y el relevo frente a los trabajos del estado del arte (DELIVER, ascensor, escaleras); después la plataforma y la interfaz; al final lo técnico (odometría que depende de la estructura del pasillo, banda muerta y tolerancia de 0,5 m, tarjeta de dos núcleos y coordinación en el portátil, baterías, fallos de navegación y no de asignación ni de relevo). Ahí van las explicaciones que hoy están en las conclusiones. **(3) Conclusiones:** un párrafo por objetivo específico con lo que se hizo y el resultado general más relevante, sin causas ni explicaciones. Ejemplo para el primero: se diseñó una arquitectura con un coordinador y dos agentes, uno por piso, que se relevan en la escalera, y en las misiones de las dos campañas no falló la asignación ni el relevo. **Cambia una regla anterior:** desde el 4 de noviembre cada conclusión decía lo obtenido, su causa y lo que implica (regla 19 de la guía `redaccion-tesis`). Al aplicar esta corrección hay que actualizar la guía y la memoria | Aplicada: capítulo 5 «Discusión», aparte (decisión de los autores); conclusiones en `capitulos_objetivos/09-conclusiones.tex` |
| 4 | «En la presentación que te envié Katherin propone las conclusiones con un bracito para ing., con engranajes para técnicas» (`~/Downloads/Presentación_Sustentación_Tesis Katherin (1).pptx`) | Presentación: diapositiva «Conclusiones» (`herramientas/presentacion_objetivos.py`, función `conclusiones`) y, por coherencia, el orden de la discusión del documento (corrección 3) | Lo que hace Katherin (diapositivas 37 a 39): siete conclusiones numeradas, cada una con un párrafo corto, las palabras clave en negrita azul y un ícono que marca el nivel: brazo robótico sobre un monitor para las de ingeniería (diseño y decisiones), engranajes para las técnicas (herramientas y arreglos) y una cabeza con un átomo para la general, que responde al objetivo. Para la nuestra: las conclusiones se separan por nivel, ingeniería primero y técnica después, con esos dos íconos, y una general al final que responde a la pregunta problema. El ícono de engranajes ya está en `plantilla/iconos/` (`engranes_a/b.png`); el del brazo robótico hay que hacerlo con el mismo estilo. El `.pptx` tiene cambios hechos a mano (diapositivas 5, 9 y 38): o se editan esas diapositivas directo en el archivo, o se pasan los cambios al generador antes de volver a generarlo | Pendiente: es de la presentación |
| 5 | Trabajos futuros: «está orientada es a características técnicas, o sea que son más mejoras de lo que hay que propiamente trabajo futuro; no está mal, pero sería solo un párrafo y una tabla». Después, otros párrafos con trabajos futuros sacados de la literatura, por ejemplo: «La integración para 3 pisos puede requerir procesos de optimización multiagente; una alternativa que actualmente se encuentra en el estado del arte es MARL como se propone en [XX] y [XX]. Así mismo, una oportunidad identificada es la inclusión de MARL para la coordinación de varios vehículos en el escenario en que varios operen sobre el mismo piso» | `capitulos/10-trabajos-futuros.tex` (compartido por las tres versiones); también la diapositiva «Trabajos futuros» | **Mejoras:** las seis líneas de hoy (navegación más precisa, más cómputo, evasión de obstáculos, más agentes y misiones, controlador predictivo, voz) pasan a un párrafo de entrada y una tabla con columnas mejora, limitación que atiende y cómo. **Trabajo futuro desde la literatura**, párrafos nuevos: (a) más de dos pisos, con optimización multiagente y MARL; (b) varios agentes en el mismo piso, coordinados con MARL; se pueden sumar (c) cambio de piso con ascensor cuando lo haya, frente a la escalera (Luo et al., 2025) y (d) asignación por subasta cuando haya varios candidatos (Quinton et al., 2023, ya citada). Referencias para MARL: Xu et al. (2026), ya citada, un marco ROS–MARL para asignar tareas entre varios robots; candidata nueva, con la ficha comprobada en Crossref y sin leer: Orr y Dutta, «Multi-Agent Deep Reinforcement Learning for Multi-Robot Applications: A Survey», *Sensors* 23(7), 3625, 2023, DOI 10.3390/s23073625. Antes de citarla hay que leer su resumen y comprobar que sostiene la frase | Aplicada |
