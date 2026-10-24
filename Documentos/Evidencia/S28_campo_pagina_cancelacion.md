# Página y cancelación con los dos vehículos (23 de octubre)

Pisos 3 y 4: deepy en el 3 y racey en el 4, arrancados en su salida frente a la escalera. Los dos
vehículos, nivelados con el repositorio antes de empezar. Datos: [`campo_20261023/registros/`](campo_20261023/registros/)
(18 misiones) y [`campo_20261023/coordinador.log`](campo_20261023/coordinador.log). Las grabaciones
(`mision_prueba_20261023_01` a `_04`, 56 min en total) quedan fuera del repositorio, en `~/tesis_evidencia/`.

## Resultado

1. **Ajustes de la página.** En una misión de bajada (Salón 403 → Salón 303) y una de subida (Salón 301 →
   Salón 401), el equipo vio en el teléfono el título de la confirmación según el sentido y las
   indicaciones correctas. Las dos se completaron con relevo, en 69,4 s y 99,3 s. El nombre del ascensor
   con su piso no se anotó por separado.
2. **Confirmación de la llegada.** El equipo la notó lenta. Del último movimiento del vehículo a
   `COMPLETADA` pasaron 2,03 s y 2,27 s, frente a una mediana de 1,46 s (de 0,01 a 4,66 s) en las 13
   misiones completadas del 16 de octubre. No hay cambio: la espera de 1,5 s antes de verificar es a propósito.
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

## Incidencias

- Red: racey estuvo unos dos minutos sin responder durante el arranque y volvió sin reiniciar nada. Una
  misión falló porque el coordinador dejó de ver la navegación de deepy 20 s.
- Una llegada al origen quedó a 0,521 m, fuera de la tolerancia de 0,5 m.
- Tras aplicar el arreglo, el equipo puso cada vehículo a mano en su salida y se le dio de nuevo la pose
  inicial (decisión del equipo).
- En el registro, la marca de cancelación sale como `8` y no como `CANCELANDO`: el registrador no la tiene
  en su tabla de nombres. Queda pendiente.
