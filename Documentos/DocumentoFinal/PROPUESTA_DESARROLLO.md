# Propuesta de orden para el capítulo de desarrollo (5 de noviembre)

Copia aparte del capítulo 3 para leerla junto a la versión vigente. `main.tex`, `capitulos/` y `main.pdf` no cambian.

- Capítulo propuesto: [`capitulos_propuesta/07-desarrollo.tex`](capitulos_propuesta/07-desarrollo.tex)
- Documento completo con ese capítulo: `main_propuesta.tex` y `main_propuesta.pdf` (los demás capítulos son los de `capitulos/`)
- Figuras nuevas: `imagenes/mapas_gregorio.png` e `imagenes/mapas_catalayud.png`, generadas con
  [`herramientas/figura_mapas_entornos.py`](../../herramientas/figura_mapas_entornos.py) a partir de los mapas de Nav2, el catálogo de
  puntos y el levantamiento con flexómetro

## Por qué

Al leer el desarrollo, el capítulo no seguía un orden y los lugares quedaban sin especificar. La plantilla de la universidad pide armar el
desarrollo «según la metodología planteada en el proyecto de grado I», con las etapas o el diagrama de bloques como punto de partida. Las
dos tesis USTA de 2024 que se revisaron siguen un solo criterio: Castiblanco va fase por fase; Corredor, por bloques del sistema, con un
apartado propio de escenarios de prueba. El capítulo vigente mezclaba tres criterios (cronológico, por bloques y de método), contaba el
paso de Gregorio a Catalayud en cuatro sitios y no describía los entornos en ninguno: de 21 oraciones con «piso N», 12 no decían el
edificio, y «piso 3» era unas veces de Gregorio y otras de Catalayud.

## Estructura

| Propuesta | Contenido | Sale de la versión vigente |
|---|---|---|
| Inicio y tabla 3.1 | Fases del anteproyecto | Igual |
| 3.1 Recorrido del trabajo | DonkeyCar, DeepRacer, primeros entornos, integración y agentes físicos | 3.1, con el cambio de edificio en una sola frase |
| 3.2 Entornos de prueba | **Nueva.** Tabla de los cuatro pisos; Gregorio con sus mapas, la prueba del 30 de septiembre y la razón del cambio; Catalayud con el criterio, la planta, el levantamiento y los mapas de los dos pisos | 3.1.5, 3.3.3, 3.3.4 y datos nuevos |
| 3.3 Arquitectura funcional | Requisitos, contrato, planificador y asignación | 3.2.1 a 3.2.4 |
| 3.4 Plataforma robótica | Componentes, Nav2, odometría, banda muerta, unidad inercial, media vuelta | 3.3, sin la subsección de mapas |
| 3.5 La red | Igual | 3.4 |
| 3.6 Interfaz | Igual | 3.5 |
| 3.7 Integración del sistema | Un proceso de Gazebo por piso (incluida la comprobación en Catalayud del 2 de noviembre); de la simulación a los agentes físicos | 3.2.5, 3.2.6 y 3.1.5 |
| 3.8 Protocolo e instrumentación | Igual | 3.6 |

Corresponde a las fases del anteproyecto: 3.3 es el diseño conceptual; 3.4 a 3.6, el desarrollo de cada bloque; 3.7, la integración; y
3.8, la validación.

## Lo nuevo y de dónde sale cada dato

| Dato | Fuente |
|---|---|
| 15 y 16 puntos de interés de Gregorio, con sus nombres | `Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml` |
| 41,0 y 46,9 m de extensión de los mapas de Gregorio | Mapas `mundo_definitivo_piso1` y `piso2` (6 cm por celda); 46,9 m ya estaba en la tabla de odometría |
| Hall al oeste del piso 3 de Gregorio, con la escalera, la rama IEEE y el laboratorio 313 | `Evidencia/S25_pasillo_piso2_amss-jgm9.md` |
| Largo de 25,3 a 25,6 m, ancho de 2,35 a 2,61 m, hornacinas de 0,99 y 1,01 m, pared este igual en los dos pisos | Levantamiento en `herramientas/generar_piso_desde_medidas.py` |
| Escalera a 22,1 y 24,4 m del extremo norte; cinco puntos por piso; el ascensor como destino | `Robot/aws-deepracer/deepracer_bringup/config/puntos_interes_pisos34.yaml` |

## Lo que cambió de redacción

- Cada mención de un piso dice su edificio. Quedan sin edificio solo los rótulos literales de la página, como «Ascensor (piso 3)».
- La prueba del 30 de septiembre, el modelo mal medido y la razón del cambio de edificio se cuentan una vez, en 3.2.1.
- La odometría (3.4.3) conserva la medida y añade cómo se pierde el avance en un pasillo uniforme; el resultado en Catalayud queda en una frase.
- Los pies nuevos describen la figura; el de la red nombra los pisos 3 y 4 de Catalayud.

## Comprobaciones

- Ninguna cifra sale del capítulo; entran las de la tabla de entornos.
- Figuras de 14 a 15 y tablas de 7 a 8; el mapa del piso 4 se reemplaza por los mapas de los dos pisos de Catalayud. Salen las etiquetas
  `fig:mapa4` y `sec:mapas`, que nadie citaba.
- Toda figura y tabla va después del párrafo que la cita, con `[H]`.
- Párrafos con «piso N» sin el edificio: de 8 a 1, el de los rótulos de la página.
- Oraciones de más de 60 palabras: 2, las mismas que en la versión vigente.
- Compila sin errores ni referencias sin definir: 80 hojas y 63 páginas numeradas, frente a 78 y 61.

Tamaños que cambian para no dejar huecos: mapas de Gregorio al 80 % del ancho y de Catalayud al 90 %; arquitectura en simulación al 86 %;
nodos al 90 %; misión con relevo al 56 %; instrumentación al 76 %; la tabla de etapas va antes que la del contrato; la tabla de cambios,
antes de la figura de la arquitectura física; las tablas de métricas y de pruebas, en letra menor.

## Si se adopta

1. Copiar `capitulos_propuesta/07-desarrollo.tex` sobre `capitulos/07-desarrollo.tex` y compilar `main.tex`.
2. Revisar los rótulos de los mapas de Gregorio: «Representación» es el nombre del catálogo y conviene confirmar qué es.
3. Ajustar la numeración de secciones en la guía de estudio (3.2 pasa a 3.3, y así hasta 3.8) y llevar la tabla de entornos al sitio.
