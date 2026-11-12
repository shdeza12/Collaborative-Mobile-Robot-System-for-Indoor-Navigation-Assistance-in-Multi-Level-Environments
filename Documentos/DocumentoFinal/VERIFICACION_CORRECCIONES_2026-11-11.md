# Verificación de las correcciones del director

Comparación del documento entregado al director (`main_objetivos.pdf` del commit `8fa9f2a`, 59 hojas) con el corregido (`main_objetivos.pdf` actual, 62 hojas, sin commit), hecha el 11 de noviembre de 2026.

**Cómo se comprobó:** no se usaron las notas de trabajo de las correcciones. Se usaron estas fuentes:
- **Los dos PDF:** el texto extraído del PDF entregado y del corregido.
- **El repositorio:** la evidencia de campo (`Documentos/Evidencia/`), el código del coordinador y de la interfaz, `REQUISITOS.md`, `RUNBOOK_CAMPANA.md` y los parámetros de Nav2 de los agentes.
- **Fuentes externas:** los resúmenes de los trabajos citados, en Crossref y Semantic Scholar, y las versiones publicadas de DonkeyCar en GitHub.
- **Documentos de referencia:** la plantilla de la USTA, el anteproyecto y dos tesis USTA (Castiblanco, 2024; Corredor, 2023).
- **Otros documentos del proyecto:** el sitio, la presentación y la versión integrada.

## 1. Resultado por corrección

| N.º | Corrección | Estado | Cómo se cumple | Con qué se comprobó |
|---|---|---|---|---|
| 1 | ¿«Web» con mayúscula? | Cumplida, sin cambio | Las 18 apariciones están en minúscula («página web», «interfaz web»). «Web» solo aparece en «Amazon Web Services», que es una marca | Criterio de la RAE (sustantivo y adjetivo comunes en minúscula). Las dos tesis USTA escriben «web» en minúscula |
| 2 | HRI en vez de «interacción humano-robot» | Cumplida | El marco conceptual pasó a «La HRI toma aquí…». El término completo queda solo en las palabras clave, en la definición del glosario y en el tercer objetivo, que es texto oficial y define la sigla | PDF corregido: 3 apariciones del término completo, todas en esos lugares |
| 3 | Redactar en inglés y pasar al español | Parcial | Se aplicó al resumen y al abstract. Los dos tienen ahora las mismas 9 oraciones, en el mismo orden, con 250 y 232 palabras (la plantilla pide de 150 a 250). El resto del documento no se tradujo | Comparación oración por oración en el PDF |
| 4 | «noviembre» en minúscula | Cumplida | La nota de aceptación dice «Noviembre de 2026». En autoridades académicas no hay ninguna fecha | PDF, hoja 4. La mayúscula se justifica porque el mes abre la línea; dentro de una oración iría en minúscula |
| 5 | «written» → «defined», y lo mismo con «before» | Cumplida | «a protocol defined prior to instrumenting the system» | PDF, abstract |
| 6 | «nine out of ten missions» | Cumplida | «Nine out of ten randomised missions… were completed with a handover» | Evidencia: `S27_metricas_rf27.json` (9 misiones válidas, 9 éxitos; la décima no terminó) |
| 7 | Definición de agente más general | Cumplida | «Sistema que percibe su entorno por medio de sensores y actúa sobre él de forma autónoma para cumplir una tarea», seguida del sentido en este trabajo | Coincide con las definiciones clásicas (Russell y Norvig; Wooldridge). La plantilla pide evitar definiciones genéricas, y por eso se conservó la segunda oración |
| 8 | Abreviaturas: conceptos de ingeniería, no términos técnicos | Parcial | Salieron AWS, DDS, JSON y Nav2, y cada una se explica en su primer uso en el cuerpo. **Falta:** la plantilla pide definir cada abreviatura en su primer uso, y AMCL (estado del arte, pág. 4) y SLAM (3.1.2) aparecen sin definir. IMU está en la lista y no se usa en el cuerpo, que dice «unidad de medición inercial». MPPI aparece sin definir en la tabla 5.1 | Búsqueda del primer uso de cada sigla en el PDF corregido |
| 9 | Agregar «entorno estructurado» | Cumplida | Abre la introducción y entra al glosario | PDF, pág. 1 y glosario |
| 10 | «Desde hace años» es ambiguo | Cumplida | 0 apariciones (había 2). La introducción dice «desde 2004, cuando Gerkey y Matarić…» | Año de la ficha de Gerkey y Matarić en la bibliografía |
| 11 | «Encarecer» | Cumplida | 0 apariciones (había 2). «Requerimientos tecnológicos… y con ellos los costos» aparece en la introducción, la contextualización y el resumen | PDF corregido |
| 12 | No hay estado del arte | Cumplida | La sección 2.1 pasó a «Estado del arte», con la tabla 2.1, que compara uno por uno los 21 trabajos | De los 21 trabajos, 20 coinciden con su resumen real (Crossref o Semantic Scholar). Nair et al. no tiene resumen disponible, y su título es coherente con lo que se le atribuye. Piguave y Ronquillo figuran como coautores del artículo de Yumbla, así que se sostiene que el artículo publica su proyecto. Precedentes: Castiblanco (USTA, 2024) tiene un capítulo «Estado del arte», y el anteproyecto separaba «Revisión del estado del arte» (cap. 5) de «Antecedentes» (6.1, normativos) |
| 13 | «no dio» → «no entregó» | Cumplida | 2 apariciones cambiadas, en 3.1.2 y en la tabla 3.8 | PDF corregido |
| 14 | ¿Qué puerto usa la interfaz? ¿8080? | Respondida; no cambia el documento | La página se sirve por HTTP en el 8000 y habla con ROS 2 por rosbridge en el 9090. No es el 8080 | `herramientas/servir_interfaz.py`, `interfaz_web/js/app.js:30`, `RUNBOOK_CAMPANA.md:260-293` |
| 15 | Reglas en viñetas (3.1.5) | Cumplida | Lista de tres viñetas | PDF corregido |
| 16 | «construidos» → «cargados» (figura 3.6) | Cumplida en el documento | Cambió el pie y, con el mismo criterio, la introducción y el comienzo de 3.2. «Construido» queda solo en «otro mapa construido con SLAM», donde es correcto. **Fuera del documento:** el sitio todavía dice «construidos» (`index.md` y glosario de `proyecto.md`) | PDF y sitio |
| 17 | «No se actualiza desde hace años» → «No se ha actualizado» | Cumplida con un cambio frente a lo pedido | Se quitó la frase en lugar de usar la redacción propuesta, porque las dos son falsas: DonkeyCar publicó la versión 5.3.0 el 29-mar-2026 y la 5.4.0 el 22-ago-2026, y su último cambio es del 2-nov-2026. Queda la limitación que sí es cierta: su simulador no se comunica con ROS 2. **Fuera del documento:** la frase falsa sigue en el sitio (`semanas/s10.md`) y en `CRONOLOGIA.md` | Versiones publicadas de `autorope/donkeycar` y `tawnkramer/gym-donkeycar` en GitHub |
| 18 | «el laboratorio de robótica de la universidad ya contaba con dos» | Cumplida, tal como se dictó | Texto cambiado | El nombre oficial del laboratorio no aparece en el repositorio ni en el anteproyecto: conviene confirmarlo |
| 19 | «Contradiría»; falta el trabajo de 5 GHz | Cumplida | «Contradiría» desapareció. El párrafo nuevo dice que faltaba la base regulatoria, que las 31 frecuencias estaban en solo escucha y que, tras instalar la base y un servicio que fija el dominio en cada arranque y reiniciar, quedaron 13 canales utilizables (del 36 al 48 a 23 dBm) y el enlace pasó de 802.11n a 802.11ac | `Evidencia/S26_red_5ghz_regulatorio.md`: todas las cifras coinciden. El texto no dice que la tarjeta opere bajo el dominio colombiano, siguiendo la salvedad de esa evidencia. Jonny debe revisarlo |
| 20 | «52 y el 63 %» sin % | Cumplida | 0 rangos sin símbolo (había 4) | Cifras contra la evidencia: 52-63 % y 95 % en `S26_piso3_deepy_y_saturacion.md`; 68 % y 74 %, y 54 % y 59 %, en `S26_laboratorio_carga_dos_vehiculos.md` |
| 21 | Las MAC no son necesarias | Cumplida en el documento | 0 apariciones de «MAC» (había 5). La tabla 3.6 queda sin la columna, y la figura 3.8 se regeneró. **Fuera del documento:** la presentación lleva todavía la figura vieja, porque su imagen es idéntica a la versión con MAC | Comparación de la imagen de la presentación (`image71.png`) con la figura del commit entregado |
| 22 | ¿Por qué 2 Hz? | Cumplida, explicada en el texto | Se explica cómo salen las cotas de la red de los 2 Hz y por qué esa frecuencia alcanza | Coincide con `REQUISITOS.md` RF-15 (periodo de 500 ms, techo de 1000 ms, márgenes de 10 y de 4); con `nav2_params_jazzy.yaml` (velocidad de 0,5 m/s); y con el coordinador, que toma el rumbo del agente para la media vuelta y espera 1,5 s para verificar la llegada. **Observación:** el texto justifica que la frecuencia alcanza; por qué se eligió el 10 de agosto no quedó escrito en ninguna parte |
| 23 | ¿La tabla 3.8 sigue una metodología sim2real? | No aplicada; pregunta abierta | La tabla registra lo que hubo que cambiar; no sigue un método de la literatura | Falta decidir si se dice así en el documento o si se busca una referencia |
| 24 | ¿Hasta qué punto la interfaz queda fuera del comité de ética? | No aplicada; pregunta abierta | La página no guarda datos de quien la usa, y el registro de cada misión no tiene datos personales | `interfaz_web/` sin cookies ni almacenamiento local; campos de `Evidencia/registros/G5_01.json`. Falta confirmar la norma de la universidad. Si se escribe, debe hacerse sin nombrar a los autores como usuarios (corrección 26) |
| 25 | «del 16 de octubre» es irrelevante | Cumplida | 0 fechas «de octubre» en el cuerpo (había 4: dos del 16 de octubre y el 23 de octubre, en el pie y en la lista de figuras). Las fechas del anexo A se mantienen, porque son el registro de cada video | PDF corregido |
| 26 | No decir que los autores hicieron de usuario | Cumplida | «…y desde la misma interfaz se validó el cambio de piso en cada relevo» | PDF: 0 apariciones de «hicieron de usuario». Era la única |
| 27 | Reducir texto con tablas | Cumplida | La prosa de 4.3.3 y 4.4 bajó de 393 a 78 palabras. El contenido pasó a las tablas 4.5 y 4.6, sin perder cifras | Conteo en las fuentes y comparación de cifras: solo sale el «16» de la fecha |
| 28 | Discusión aparte; conclusiones sin explicaciones | Cumplida, con dos observaciones | El capítulo 5, «Discusión», tiene 881 palabras y 10 citas, en cuatro secciones: coordinación, alcance de la evaluación, plataforma e interfaz, y aspectos técnicos. Las conclusiones pasaron de 459 a 316 palabras, sin conectores de causa; las entregadas tenían «contribuyó», «lo que permitió» y «por lo que» | (a) La plantilla no tiene capítulo de discusión, y el director pidió preguntar; Corredor (USTA, 2023) usa «Resultados y Discusión», así que el capítulo aparte es decisión de los autores y conviene confirmarlo con el director. (b) **Imprecisión encontrada:** la discusión dice que Kayukawa et al. usaron el teléfono «para guiar visitantes»; según su resumen, guía el robot, y el teléfono sirve para consultar explicaciones |
| 29 | Trabajos futuros: mejoras en un párrafo y una tabla, y trabajos futuros desde la literatura | Cumplida | Tabla 5.1 con las cinco mejoras y tres párrafos: más de dos pisos con MARL, varios agentes por piso con MARL o subasta, y el ascensor para usuarios que no pueden usar la escalera | Los resúmenes de Xu et al. (2026), Orr y Dutta (2023) y Luo et al. (2025) sostienen lo que se les atribuye; Quinton et al. (2023) es una revisión de los métodos de mercado. **Observación:** la tabla sale numerada 5.1 dentro de un capítulo sin número |
| 30 | Conclusiones con íconos de nivel en la presentación | No aplicada | Es de la presentación, que no se ha tocado | Presentación de Katherin, diapositivas 37 a 39 |

## 2. Resumen

- Cumplidas: 25.
  - Dos no cambian el texto: la 1 y la 14.
  - Tres siguen con el mismo problema fuera del documento, en el sitio o en la presentación: la 16, la 17 y la 21.
- Parciales: 2 (3 y 8).
- No aplicadas: 3 (23, 24 y 30).

En total son 30.

## 3. Lo que hay que corregir todavía

En el documento:
1. Definir AMCL y SLAM en su primer uso. Decidir si IMU sale de la lista o se usa en el texto. Definir MPPI en la tabla 5.1.
2. Precisar la frase de Kayukawa et al. en la discusión: el teléfono como canal de consulta, no de guiado.
3. Si el director quiere, cambiar el número de la tabla de trabajos futuros.
4. Responder en el texto, si se decide hacerlo, las preguntas de sim2real y del comité de ética.

Fuera del documento:
5. Presentación: la figura de la red sin las MAC, las conclusiones con íconos de nivel y los trabajos futuros nuevos.
6. Sitio: «construidos» en `index.md` y `proyecto.md`, y la frase falsa de DonkeyCar en `semanas/s10.md` (y en `CRONOLOGIA.md`).
7. Versión integrada: comparte con esta el resumen y la contextualización corregidos, pero sus capítulos propios siguen sin estas correcciones.

Decisiones de los autores:
8. Confirmar con el director el capítulo de discusión aparte y el nombre oficial del laboratorio.

## 4. Actualización del 11 de noviembre, después de la verificación

Resuelto a pedido de los autores:
- **Corrección 8:** AMCL y SLAM se definen en su primer uso, en el estado del arte. IMU se define en el marco conceptual. LiDAR y MARL entran en abreviaturas, y MPPI va definido en el glosario.
- **Corrección 28, Kayukawa et al.:** las tres menciones (estado del arte, tabla 2.1 y discusión) dicen ahora lo que dice su artículo. El robot lleva a los visitantes ciegos a las exhibiciones que eligen, con audio en la ruta; el teléfono sirve para consultar explicaciones y llamar al personal; y el estudio se hizo con el museo abierto al público.
- **Corrección 28, conclusiones:** parten de las que aprobaron los autores.
  - Cada párrafo empieza por lo que se hizo para su objetivo.
  - Se quitaron solo las causas, que ya están en la discusión: la planificación sin ROS 2, la falta de codificadores, la banda muerta como causa de la tolerancia, la tarjeta de dos núcleos y lo que la instrumentación habría registrado sin la confirmación.
  - Entra el tiempo total mediano de 87,6 s.
- **Estado del arte:** reescrito por ideas.

Documento final: `main_objetivos.pdf`, 62 hojas y 48 numeradas, sin errores, sin referencias rotas y con 52 citas.

## 5. Revisión completa del documento compilado (11 de noviembre, segunda lectura)

Lectura de las 62 hojas contra el repositorio. Errores encontrados en el texto nuevo, ya corregidos:

- **Trabajos futuros, «Más de dos pisos»:** decía que un tercer piso «supone más de un relevo por misión». El planificador usa la transferencia del piso de origen y la del piso de destino, así que el relevo sigue siendo uno. Ahora dice que lo que cambia es la competencia por los agentes cuando hay varias solicitudes.
- **Sección 3.2.5, 2 Hz:** el argumento de que el agente avanza 0,25 m entre publicaciones usaba la velocidad pedida, 0,5 m/s; la medida es 0,74 m/s (`S26_piso4_cadena_media_vuelta.md`). Se quitó. Queda cómo salen las cotas de la red y que la llegada se verifica con el agente detenido.
- **Discusión, punto único de fallo:** párrafo nuevo sobre el portátil del coordinador, con los dos apagados de la campaña y Zhang et al. La fila de Zhang et al. en la tabla 2.1 ya tiene su relación.
- **Discusión, alcance de la evaluación:** las dos tasas no son comparables, porque la tolerancia es de 0,25 m en simulación y de 0,5 m con los agentes físicos; con 0,25 m, cinco de las nueve llegadas físicas habrían quedado dentro (tabla 4.4). También se aclara en 4.3.1.
- **Menores:** la introducción dice que el sistema se desarrolló con software libre y se cargó en los agentes; la fila 32 de la tabla 3.1 ya no nombra a los autores; se partió la frase de la red móvil; MPPI «admite» vehículos tipo automóvil; los agradecimientos ya no dicen «se construyeron».

Sin cambiar: la tabla de mejoras sigue numerada 5.1, porque LaTeX numera por capítulo y Trabajos futuros no tiene número; no hay otra tabla 5.1.

Documento: `main_objetivos.pdf`, 63 hojas y 49 numeradas, sin errores, sin referencias rotas y con 52 citas.
