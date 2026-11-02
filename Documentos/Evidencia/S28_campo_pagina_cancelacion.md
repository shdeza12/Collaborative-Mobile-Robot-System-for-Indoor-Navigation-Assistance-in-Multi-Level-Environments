# Página y cancelación con los dos vehículos (23 de octubre)

Pisos 3 y 4: deepy en el 3 y racey en el 4, arrancados en su salida frente a la escalera. Los dos
vehículos, nivelados con el repositorio antes de empezar. Datos: [`campo_20261023/registros/`](campo_20261023/registros/)
(18 misiones) y [`campo_20261023/coordinador.log`](campo_20261023/coordinador.log). Las grabaciones
(`mision_prueba_20261023_01` a `_04`, 56 min en total) quedan fuera del repositorio, en `~/tesis_evidencia/`.
Video de las pruebas: <https://youtu.be/31oNn04qLoU> ([`S29_video_pagina_cancelacion.md`](S29_video_pagina_cancelacion.md)).

## Resultado

1. **Ajustes de la página.** En una misión de bajada (Salón 403 → Salón 303) y una de subida (Salón 301 →
   Salón 401), el equipo vio en el teléfono el título de la confirmación según el sentido y las
   indicaciones correctas. Las dos se completaron con relevo, en 69,4 s y 99,3 s. El nombre del ascensor
   con su piso no se anotó por separado.
2. **Confirmación de la llegada.** El equipo la notó lenta. En el coordinador, del último movimiento del
   vehículo a `COMPLETADA` pasaron 2,03 s y 2,27 s, frente a una mediana de 1,46 s (de 0,01 a 4,66 s) en las
   13 misiones completadas del 16 de octubre; la espera de 1,5 s antes de verificar es a propósito y no
   cambia. La demora que vio el equipo estaba en la página, que mostró «Hemos llegado» 46,0 s y 35,7 s después
   de esa marca (ver «Retraso de la página frente al coordinador»). Este punto atribuía antes la lentitud a la
   espera de 1,5 s; se corrigió el 1 de noviembre, al revisar las grabaciones de la pantalla del teléfono.
3. **Media vuelta rechazada después de cancelar.** Tras cada cancelación o tramo fallido, el agente
   respondía «el robot no esta libre (estado 3)». Nav2 guarda varios minutos las metas terminadas; con una
   `CANCELADA` o `ABORTADA` en la lista el agente marcaba el robot en ERROR, y la media vuelta exigía LIBRE.
   Sin ella, Nav2 intentaba girar solo en el pasillo y oscilaba: una misión abortó y una vuelta a casa falló
   tras tres intentos. Arreglo en el commit `d25e45e`: la media vuelta se rechaza solo con una meta viva.
   Pruebas: 50 de 50 del agente y 19 de 19 del coordinador con vehículos simulados. Copiado a los dos
   vehículos. Medias vueltas antes del arreglo: 7 hechas y 8 rechazadas; después: 10 hechas, 0 rechazadas.
4. **Cancelación (RF-29) en los vehículos.** Después del arreglo se cancelaron seis misiones, una o más
   en cada etapa, y en las seis el vehículo volvió a su escalera, dentro de la tolerancia de 0,5 m:

   | Misión | Etapa al cancelar | Vuelve | Distancia a su escalera |
   |---|---|---|---|
   | Salón 302 → Salón 402 | Primer tramo, yendo a recoger | deepy | 0,173 m (2.º intento; el 1.º, 0,578 m) |
   | Salón 303 → Ascensor (piso 3) | Primer tramo | deepy | 0,337 m |
   | Escalera (piso 3) → Salón 402 | Transferencia | racey | 0,074 m |
   | Escalera (piso 3) → Salón 401 | Esperando confirmación | racey | 0,302 m |
   | Salón 401 → Salón 303 | Segundo tramo | deepy | 0,337 m |
   | Ascensor (piso 3) → Salón 401 | Segundo tramo | racey | 0,328 m |

## Retraso de la página frente al coordinador

Medido el 1 de noviembre con las cuatro grabaciones de la pantalla del teléfono. Para cada misión grabada se
compara la marca final del coordinador con el primer cuadro en que el panel de la página muestra ese estado:
verde para «Hemos llegado» y rojo para «No se pudo completar». La hora de cada cuadro sale de alinear los
cambios de título del panel con las marcas del coordinador. Se comprobó con el reloj del teléfono: en las
cuatro grabaciones, el minuto de la barra de estado cambia entre 0,03 y 0,18 s después del segundo 0. Datos en
[`campo_20261023/sincronia/`](campo_20261023/sincronia/); método y programas en
[`S29_video_pagina_cancelacion.md`](S29_video_pagina_cancelacion.md).

| Solicitud | Misión | Cierre | Marca del coordinador | En la página | Retraso |
|---|---|---|---|---|---|
| 17:18:08 | Salón 403 → Salón 303, con relevo | Completada | 17:19:16,97 | 17:20:02,98 | 46,00 s |
| 17:20:56 | Salón 301 → Salón 401, con relevo | Completada | 17:22:35,70 | 17:23:11,36 | 35,66 s |
| 17:33:17 | Salón 302 → Salón 402, con relevo | Cancelada | 17:36:02,65 | 17:36:13,11 | 10,47 s |
| 17:54:21 | Salón 302 → Salón 402 | Cancelada | 17:54:42,50 | 17:54:42,76 | 0,26 s |
| 17:55:48 | Salón 401 → Salón 303, con relevo | Cancelada | 17:57:09,85 | 17:57:09,95 | 0,11 s |
| 17:57:31 | Escaleras (piso 3) → Salón 401 | Cancelada | 17:57:41,85 | 17:57:41,91 | 0,05 s |
| 17:58:07 | Ascensor (piso 3) → Salón 401, con relevo | Cancelada | 17:59:28,37 | 17:59:30,37 | 2,00 s |
| 18:00:03 | Salón 403 → Salón 401 | Completada | 18:00:38,45 | 18:00:38,45 | 0,00 s |
| 18:00:49 | Salón 303 → Salón 301 | Completada | 18:01:36,42 | 18:01:36,40 | −0,02 s |
| 18:06:46 | Salón 303 → Ascensor (piso 3) | Cancelada | 18:07:37,42 | 18:07:37,46 | 0,04 s |
| 18:08:04 | Escaleras (piso 3) → Salón 402 | Cancelada | 18:08:38,58 | 18:08:38,54 | −0,04 s |

- Los tres retrasos largos ocurrieron antes de las 17:54, en misiones con relevo. Desde las 17:54 el retraso fue
  de 2,00 s o menos. Las misiones de las 17:30 a las 17:32 y de las 17:36 a las 17:46 no tienen grabación de
  pantalla.
- En las misiones de las 17:18 y las 17:20 el panel siguió en «Sígueme» y la página indicó «conectado» hasta
  que apareció «Hemos llegado». El estado final y el resultado de la acción llegaron juntos: 17 ms de diferencia en la
  primera misión.
- Las etapas anteriores de esas mismas misiones sí llegaron a tiempo: el segundo tramo apareció entre 0,10 y
  0,31 s después de su marca, y la cancelación de las 17:35:45, a los 0,08 s.
- La causa no se estableció y no se intentó reproducir. El requisito RF-18 (la interfaz muestra el estado de la
  misión) no fija un límite de tiempo, así que su estado no cambia. Por decisión de los autores (1 de noviembre), el documento final no lo declara como
  limitación.

## Incidencias

- Red: racey estuvo unos dos minutos sin responder durante el arranque y volvió sin reiniciar nada. Una
  misión falló porque el coordinador dejó de ver la navegación de deepy 20 s.
- Una llegada al origen quedó a 0,521 m, fuera de la tolerancia de 0,5 m.
- Tras aplicar el arreglo, el equipo puso cada vehículo a mano en su salida y se le dio de nuevo la pose
  inicial (decisión del equipo).
- En el registro, la marca de cancelación sale como `8` y no como `CANCELANDO`: el registrador no la tiene
  en su tabla de nombres. Queda pendiente.
