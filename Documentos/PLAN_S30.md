# Plan de la semana 30 (2 al 8 de noviembre)

Actividad del cronograma en las semanas 30 y 31: redacción completa del documento, con las observaciones del jurado, y
justificación escrita de las desviaciones. El criterio de cierre, en la semana 31, es el borrador completo entregado al
director. La entrega del documento es el viernes 13 de noviembre.

Fuera del cronograma, esta semana están la reunión con el director, la presustentación, todavía sin fecha, y la sesión de
una hora con los jurados.

## 0. La semana de un vistazo

| Día | Qué se hace | Vehículos | Al terminar el día |
|---|---|---|---|
| Lun 2 (festivo) | Hecho: guion de la sesión, simulación en los pisos 3 y 4, clips en la presentación | no | Todo publicado |
| Mar 3 | Reunión con el director (§1). Fijar la sesión con los jurados (§2). Justificar el corrimiento del cronograma (§3). Baterías a cargar en la noche | no | Fechas de la sesión y del ensayo, y decisión sobre la versión del documento |
| Mié 4 | Ensayo en Catalayud (§4) | los dos | Recorrido cronometrado, guion corregido y evidencia |
| Jue 5 | Sesión, si esa es la fecha (§5). Si no, observaciones del documento (§3) | los dos, si hay sesión | Evidencia de la sesión |
| Vie 6 | Sesión, si esa es la fecha. Pendientes de los vehículos, solo después de la sesión (§6). Corte de la semana en la noche (§8) | los dos, si hay sesión o pendientes | Entregable 30, tablero y sitio |
| Sáb 7 y dom 8 | Fundir la versión recortada y dejar listo el borrador (§3). Sin vehículos | no | Borrador listo para entregarlo el lunes 9 |

El ensayo va un día hábil antes de la sesión. Si la sesión cae el miércoles 4, el ensayo pasa al martes 3, después de la
reunión. Si un jurado solo puede la semana siguiente, el ensayo se mantiene esta semana y el día de la sesión se repite el
calentamiento.

## 1. Reunión con el director (martes 3)

Objetivo: salir con fechas y con la versión del documento decidida.

| Tema | Qué preguntar | Lo que propone el equipo |
|---|---|---|
| Versión del documento | ¿La versión recortada, de 79 páginas, es la que se entrega? Pidió entre 60 y 80 | Sí, y se funde como versión vigente |
| Borrador | ¿Cuándo quiere recibir el borrador completo, antes de la entrega del 13? | Lunes 9 de noviembre |
| Presustentación | ¿Qué día, a qué hora y en qué sala? ¿Cuánto debe durar? ¿La sala tiene PowerPoint? | 19 min 20 s, sin demostración, con dos clips |
| Sesión con los jurados | ¿Asiste? ¿Hace falta avisar o pedir permiso para usar los pisos 3 y 4 de Catalayud? | Una hora, sin clases en esos pisos |
| Contenido | ¿Tiene observaciones sobre el documento? | Se incorporan esta semana |

Cierre: respuestas anotadas, y este plan corregido si cambia alguna fecha.

## 2. Fecha de la sesión con los jurados

1. Pedirle la disponibilidad al jurado que falta.
2. Cruzarla con la del otro jurado y con las horas sin clases en los pisos 3 y 4. Las pruebas del 16 y el 23 de octubre
   empezaron después de las 17:00.
3. Confirmarles el día, la hora y el punto de encuentro: piso 4, frente al Salón 403.

Cierre: los dos jurados confirmaron, y el ensayo queda fijado un día hábil antes.

## 3. Documento final

| Tarea | Quién | Cómo | Cierre |
|---|---|---|---|
| Observaciones de los autores | Santiago y Jonny las pasan; Claude las aplica | Sobre `main_recorte.pdf`, 79 páginas | Todas aplicadas y compilado sin errores |
| Autoridades | Los autores | Completar [`00-autoridades.tex`](DocumentoFinal/capitulos/00-autoridades.tex), que todavía dice «NOMBRES COMPLETOS» | Sin marcadores en el PDF |
| Justificar las desviaciones | Claude redacta; los autores aprueban | Las técnicas ya están en el documento: DonkeyCar y DeepRacer, CoppeliaSim y Gazebo, aplicación y página web, Humble y Jazzy. Falta el corrimiento de 2 a 4 semanas de la parte técnica ([`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md), §5) | Cada desviación tiene su lugar en el documento |
| Fundir la versión recortada | Claude, después del visto bueno del director | Pasar `capitulos_recorte/` a `capitulos/`, compilar y actualizar la página de documentos del sitio | `main.pdf` es la versión recortada |
| Entregar el borrador | Los autores | En la fecha que acuerden con el director | Criterio de cierre de la semana 31 |

## 4. Ensayo

Todo está en la sección 3 de [`GUION_SESION_JURADOS.md`](GUION_SESION_JURADOS.md): nivelar los vehículos, arrancar, correr
las cuatro misiones y hacer las pruebas de la tabla. Lleva unas dos horas, con los dos autores y las baterías cargadas la
noche anterior.

Prueba opcional, si el equipo quiere mostrar lo que ve un vehículo. RViz en vivo no funciona desde el portátil. Humble no
decodifica el láser de Jazzy ([`S25_ensayo_laboratorio.md`](Evidencia/S25_ensayo_laboratorio.md)), y desde el 8 de octubre lo
interno de cada vehículo no sale de él. Lo probado es grabar en el vehículo, traer la grabación y verla en RViz con `herramientas/ver_bag_rviz.sh`, que muestra
el mapa, el láser, el plan y la pose ([`GUIA_CAMPANA_NAV2_HARDWARE.md`](historial/GUIA_CAMPANA_NAV2_HARDWARE.md), §6.1). En
simulación sí se ve en vivo, con `herramientas/robot.sh robot1 rviz`.

Cierre: el de la sección 3.3 del guion.

## 5. Sesión con los jurados

Las secciones 4 a 7 de [`GUION_SESION_JURADOS.md`](GUION_SESION_JURADOS.md). Cierre: evidencia escrita el mismo día, con su
fila en [`Evidencia/README.md`](Evidencia/README.md).

## 6. Pendientes de los vehículos

Solo después de la sesión, para no cambiar lo ensayado, y siempre en los dos vehículos.

| Pendiente | Cómo | Cierre |
|---|---|---|
| La etapa de cancelación sale como `8` en el registro | Corregir el nombre en el código y correr `prueba_coordinador_vehiculo.py` | La prueba pasa y el registro dice `CANCELANDO` |
| Imagen del coordinador | `bash herramientas/coordinador_portatil.sh construir`, con internet | `arrancar` y `comprobar` dan lo esperado |
| Copiar lo que haya cambiado | `bash herramientas/nivelar_carros.sh --copiar`, con los dos encendidos | `Los vehiculos estan nivelados con el repositorio.` |

Las rutas en comentarios de siete archivos se copian antes, al empezar el ensayo.

## 7. Preparación de la presentación (fuera del cronograma)

| Qué | Quién | Cierre |
|---|---|---|
| Revisar la presentación y acordar el reparto del guion | Santiago y Jonny | Observaciones aplicadas |
| Ensayo oral con cronómetro | Santiago y Jonny | Dentro de 15 a 20 min |
| Probar los dos clips en el computador de la sala | Santiago o Jonny | Se reproducen con un clic |
| Guía de preguntas de la sustentación, en la guía de estudio | Claude | Publicada antes de la presustentación |

## 8. Corte del viernes 6

1. Entregable 30, en `.md` y `.tex`, con la reunión, el ensayo y la sesión si ya ocurrieron.
2. [`ESTADO.md`](../ESTADO.md): semana en curso, fecha de corte y pendientes 1 y 2. Las autoridades las ponen los autores, y la
   presentación tiene 42 diapositivas y 19 min 20 s.
3. Cronología y sitio: `python3 sitio/generar_semanas.py`, restaurar `s21_1.jpg` y `s27_1.jpg`, y publicar.

Cierre: verificador en 13 de 13 con todo preparado para el commit, y la página de la semana 30 con sus conclusiones publicada.
