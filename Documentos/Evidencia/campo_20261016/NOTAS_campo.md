# Campaña con los vehículos, tarde del 16-oct (notas de campo)

Notas para la documentación del fin de semana. Los datos de origen están en esta
misma carpeta; nada de lo de aquí está en el repositorio todavía.

## Qué hay y dónde

| Qué | Dónde |
|---|---|
| Grabación única de la tarde, 18:30:18 a 19:35:28 (7 archivos de 10 min) | `~/tesis_evidencia/mision_G6_campana/` (original, sin metadata) |
| Respaldo intacto con sumas sha256 (7/7 OK) | `respaldo_original_G6/` |
| Grabación recuperada con `ros2 bag reindex -s mcap` (112 529 mensajes) | `mision_G6_campana_recuperada/` |
| Registros del coordinador de la tarde (21) | `respaldo_original_G6/registros/` y `~/tesis_evidencia/registros/` |
| Carga de las tarjetas, logs de Nav2 y del agente, por vehículo | `carros/deepy/`, `carros/racey/` |
| Arranques y paradas de las cadenas de la tarde | `arranque_*_intento3.log`, `arranque_racey_intento4.log`, `parar_*` |
| Datos del 8-oct que seguían en deepy | `~/tesis_evidencia/datos_8oct_deepy/` |

Los nombres de los registros van en hora UTC (00:10 = 19:10 local).

## Misiones del sorteo (19:10 a 19:35)

Error de llegada = el que mide el coordinador con la localización, no el del
flexómetro. La espera en el relevo va desde que el robot de destino llega a su
escalera hasta que el usuario confirma.

| N.º | Origen → destino | Hora | Resultado | Tiempo (s) | Error (m) | Espera relevo (s) |
|---|---|---|---|---|---|---|
| 1 | Ascensor p3 → Salón 403 | 19:10:15 | falló: deepy paró a 0,526 m del Ascensor (tolerancia 0,5) | 11,9 | 0,53 | — |
| 1 | (repetida) | 19:10:41 | completada | 52,3 | 0,44 | 21,8 |
| 2 | Salón 302 → Salón 401 | 19:12:45 | falló: «no hay la pose del agente» tras SUCCEEDED de deepy | 36,8 | 0,43 | — |
| 2 | (repetida) | 19:13:24 | completada | 90,1 | 0,20 | 0,9 |
| 3 | Salón 401 → Salón 302 | 19:16:06 | completada | 87,6 | 0,14 | 13,1 |
| 4 | Salón 403 → Salón 303 | 19:18:37 | completada | 79,9 | 0,42 | 1,7 |
| 5 | Salón 402 → Salón 301 | 19:20:56 | completada | 105,4 | 0,28 | 0,9 |
| 6 | Salón 301 → Salón 401 | 19:22:59 | completada | 89,8 | 0,23 | 27,6 |
| 7 | Ascensor p4 → Salón 301 | 19:25:17 | completada | 81,7 | 0,23 | 1,7 |
| 8 | Salón 302 → Salón 403 | 19:26:59 | completada | 81,8 | 0,21 | 27,4 |
| 9 | Salón 303 → Salón 402 | 19:29:09 | completada | 92,6 | 0,30 | 0,8 |
| — | Salón 403 → Ascensor **p4** (destino equivocado en la página) | 19:32:13 | falló: racey a 0,506 m | 66,7 | 0,51 | — |
| — | (repetida, mismo destino equivocado) | 19:33:37 | completada, sin relevo | 13,5 | 0,42 | — |
| 10 | Salón 403 → Ascensor p3 | 19:35:10 | **interrumpida**: el portátil se apagó; la grabación acaba a las 19:35:28 con racey camino de su escalera, a 7,3 m | — | — | — |

Nueve misiones del sorteo completadas (la 1 y la 2 en el segundo intento).
Sobre esas nueve: tiempo mediano 87,6 s (52,3 a 105,4); error de llegada mediano
0,23 m (0,14 a 0,44); espera en el relevo mediana 1,7 s (0,8 a 27,6); asignación
por debajo de 3 ms.

Falta la medida del flexómetro de cada llegada (columna `llegada_medida_m` de
`~/tesis_evidencia/campana_rf27.csv`). Sin ella el analizador deja `exito` nulo.

## Incidencias antes de las misiones válidas (18:34 a 18:58)

1. 18:34–18:45, seis intentos de la misión 1, todos rechazados por deepy en
   menos de 3 s (uno no respondió en 120 s): «Initial robot pose is not
   available». El bt_navigator de deepy tenía la transformada mapa→odom
   congelada en las 18:21:41, aunque AMCL la seguía publicando.
2. 18:43, el gestor de ciclo de vida de racey apagó su navegación: el
   planificador no respondió durante 60 s.
3. 18:50, se reiniciaron las dos cadenas y los agentes con la pose de salida.
4. 18:57 y 18:58, dos intentos más de la misión 1: deepy hizo sus tramos, pero
   racey abortó el tramo hacia su escalera; su behavior_server tenía la
   transformada congelada en las 18:55:30 y el controller_server no respondía.
5. ~19:04, segundo reinicio de la cadena de racey; no tomó la pose de salida en el
   arranque y hubo que publicársela a mano. Desde ahí, todo funcionó.
6. El portátil se apagó dos veces por batería (17:58 y 19:35); el cargador estuvo
   desconectado durante la tarde.

Causa raíz de las transformadas congeladas: sin establecer. Coincide con
cadenas que llevaban horas encendidas y pasaron por el apagado del portátil, y
con cargas de 10 a 14 en tarjetas de dos núcleos.

## Desviaciones del protocolo que hay que declarar

- Una sola grabación para toda la campaña, por decisión del equipo; se parte por
  misión con los registros.
- Repeticiones de las misiones 1 y 2 tras un fallo de verificación.
- Destino equivocado en la misión 10 (Ascensor del piso 4) y misión 10 sin
  terminar por el apagado.
- Reinicio de cadenas y nueva pose inicial antes de las misiones válidas.
