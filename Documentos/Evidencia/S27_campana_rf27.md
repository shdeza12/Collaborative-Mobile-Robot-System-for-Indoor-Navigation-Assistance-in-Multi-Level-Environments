# Campaña del sistema completo con los dos vehículos, pisos 3 y 4 (16 de octubre)

Prueba del protocolo completo en los vehículos. Cada misión se pidió desde la página y la asignó el
coordinador del portátil; la guió el vehículo del piso de origen hasta la escalera, el usuario
confirmó el cambio de piso y la terminó el vehículo del piso de destino. deepy (`amss-ez9n`) fue
`robot1` en el piso 3 y racey (`amss-jgm9`) fue `robot2` en el piso 4. El plan del día es el
[`PLAN_S27.md`](../historial/PLAN_S27.md) §2; el sorteo de las diez misiones, [`campana_rf27_misiones.csv`](campana_rf27_misiones.csv).

Hubo dos sesiones: la primera (17:38 a 17:56) corrió doce misiones elegidas a criterio por el
equipo, sin seguir el sorteo, y queda como sesión exploratoria; de ella sale la prueba G-5. La
segunda (18:30 a 19:35) corrió las misiones del sorteo en su orden, y es la campaña de G-6 y del
requisito RF-27 (demostración física del protocolo con N entre 5 y 10 repeticiones).

## Resultado

1. Las misiones 1 a 9 del sorteo corrieron y se completaron, las nueve con relevo entre pisos. El
   análisis da `VEREDICTO: VALIDA`, 9 de 9 éxitos (IC95 de Wilson del 70,1 % al 100 %) y 9 de 9
   misiones con continuidad en el relevo ([`S27_metricas_rf27.json`](S27_metricas_rf27.json)).
2. Tiempo total de la misión: mediana 87,6 s, de 52,3 s a 105,4 s. Tiempo de respuesta (de la
   solicitud al primer movimiento): mediana 0,87 s, de 0,27 s a 3,90 s. Asignación: 0,3 ms con el
   reloj de pared. Espera en el relevo: mediana 1,22 s, de 0,68 s a 27,48 s, según cuánto tardó la
   persona en confirmar.
3. Error de llegada: mediana 0,234 m, de 0,143 m a 0,435 m, las nueve por debajo de los 0,5 m. Es el
   error de la pose del agente contra el punto del catálogo, el mismo que verificó el coordinador
   1,5 s después de que Nav2 diera la meta por alcanzada. No hubo medida con cinta (ver abajo).
4. La misión 10 (Salón 403 → Ascensor del piso 3) empezó a las 19:35:10 y no terminó: el portátil se
   apagó por batería unos 30 s después, cuando racey ya había llegado a su escalera. Queda fuera del
   conteo. Corrección del 20 de octubre: la primera versión decía «a los 18 s», que es donde termina la
   grabación de datos, y el grabador pierde su último bloque cuando se corta de golpe. La grabación de la
   pantalla del teléfono, sincronizada con el coordinador (desfase de 616,6 s, comprobado con las diez
   llegadas), muestra la página en «Cambia de piso» a los 28,6 s, con racey en su escalera, y
   «Buscando el coordinador…» a los 30,2 s. El video no se versiona; está en `VIDEOS/` del equipo.
5. G-5 se cumplió en la primera sesión: la misión del Salón 302 al Salón 402, con relevo, se
   completó en 132,5 s con un error de llegada de 0,444 m y 61,1 s de espera en el relevo
   ([`registros/G5_01.json`](registros/G5_01.json)).

| N.º | Origen → destino | Tiempo total (s) | Respuesta (s) | Espera en el relevo (s) | Error de llegada (m) |
|---|---|---|---|---|---|
| 1 | Ascensor (piso 3) → Salón 403 | 52,3 | 0,51 | 21,06 | 0,435 |
| 2 | Salón 302 → Salón 401 | 90,1 | 0,27 | 0,85 | 0,202 |
| 3 | Salón 401 → Salón 302 | 87,6 | 3,90 | 12,92 | 0,143 |
| 4 | Salón 403 → Salón 303 | 78,9 | 1,25 | 0,71 | 0,420 |
| 5 | Salón 402 → Salón 301 | 105,4 | 0,66 | 0,68 | 0,285 |
| 6 | Salón 301 → Salón 401 | 89,8 | 2,97 | 27,48 | 0,226 |
| 7 | Ascensor (piso 4) → Salón 301 | 81,7 | 0,87 | 1,22 | 0,234 |
| 8 | Salón 302 → Salón 403 | 81,8 | 0,95 | 26,76 | 0,214 |
| 9 | Salón 303 → Salón 402 | 92,6 | 0,63 | 0,73 | 0,299 |

Los registros de las nueve misiones son [`registros/RF27_G6_01.json`](registros/RF27_G6_01.json) a
`RF27_G6_09.json`.

## Criterio de conteo

Decisión del equipo del 18 de octubre: entran en la campaña las misiones del sorteo que corrieron y
se completaron, una por misión, que son nueve.

Las misiones 1 y 2 se completaron en un segundo intento. El primer intento de la 1 (19:10:15)
terminó con deepy a 0,526 m del Ascensor, fuera de la tolerancia de 0,5 m. El de la 2 (19:12:45)
terminó sin pose del agente para verificar la llegada al Salón 302. Antes de las 19:10 hubo ocho
intentos más de la misión 1 con la navegación trabada (ver Incidencias). El §8 del protocolo cuenta
un intento fallido como fallo; por la decisión del equipo, esos intentos no entran en la tasa y se
declaran aquí. Sus registros del coordinador están en [`campo_20261016/registros/`](campo_20261016/registros/).

A las 19:32 se pidió por error el Ascensor del piso 4 como destino de la misión 10. Ese intento y su
repetición no son misiones del sorteo y no se cuentan.

## Llegada sin cinta

La hoja de campaña no tiene ninguna medida de flexómetro. El protocolo toma la llegada en los
vehículos con cinta sobre marcas en el piso (§1), y sin esa medida el compositor dejaba el registro
pendiente y el analizador lo rechazaba. Se añadió una segunda fuente declarada:
`componer_registro.py --fuente-llegada localizacion_agente` escribe en el registro
`fuente = "localizacion_agente"` e `incertidumbre_m = null`, y el analizador cuenta las llegadas por
fuente y avisa cuando salen de la localización. Nunca se escriben como `cinta_metrica`. El cambio
está documentado en [`ESQUEMA_REGISTRO_MISION.md`](../ESQUEMA_REGISTRO_MISION.md) §4.4.

La única comparación de AMCL con cinta en los vehículos es la del 7 de octubre en el piso 4
([`S26_piso4_cadena_media_vuelta.md`](S26_piso4_cadena_media_vuelta.md), resultado 2): AMCL, leída
al terminar cada corrida, quedó a 0,10 m o menos de la cinta en el avance y a 5 cm o menos en lo
lateral. Sirve de referencia para leer los errores de esta campaña, que se reportan sin corregir.

## Incidencias

| Hora | Qué pasó | Qué se hizo |
|---|---|---|
| 17:58 | El portátil se apagó por batería al final de la primera sesión | Grabación recuperada con `ros2 bag reindex -s mcap` sobre una copia |
| 18:19 | racey con 50 % a 70 % de pérdida de paquetes en la red | El equipo revisó la red; volvió a 0 % en `DEEPRACER_P4-5G` |
| 18:34–18:45 | Seis intentos de la misión 1 rechazados por deepy: `Initial robot pose is not available`. El bt_navigator tenía la transformada `map → odom` detenida en las 18:21:41, aunque AMCL la seguía publicando | — |
| 18:43 | El gestor de ciclo de vida de racey apagó su Nav2: el planificador no respondió en 60 s | — |
| 18:50 | Se reiniciaron las dos cadenas y los dos agentes con la pose de salida | — |
| 18:57–18:58 | Dos intentos más de la misión 1: racey abortó el tramo hacia su escalera, con la transformada del behavior_server detenida en las 18:55:30 y el controller_server sin responder | Segundo reinicio de la cadena de racey (~19:04); no tomó la pose de salida en el arranque y se publicó a mano |
| 19:35 | El portátil se apagó por batería durante la misión 10 | Grabación recuperada con el mismo método |

La causa de las transformadas detenidas no se estableció. Coincide con cadenas que llevaban horas
encendidas, que pasaron por el apagado del portátil, y con cargas de 10 a 14 en tarjetas de dos
núcleos. Después de los reinicios, las nueve misiones corrieron sin tocar los vehículos.

La hoja no registra personas en el pasillo durante las misiones (RNF-03). Queda por confirmar con el
equipo.

## Datos y reproducción

En el repositorio, [`campo_20261016/`](campo_20261016/): los 35 registros del coordinador de las dos
sesiones, los registros compuestos y las métricas de la primera sesión, la hoja, la carga de las tarjetas,
los logs de Nav2 y del agente de los dos vehículos, los arranques y paradas de las cadenas, las
sumas sha256 de las grabaciones y las notas de campo del mismo día
([`NOTAS_campo.md`](campo_20261016/NOTAS_campo.md)). Las grabaciones no se versionan (`.gitignore`); quedan en
`~/tesis_evidencia/campo_2026-10-16/` del portátil.

La grabación de la segunda sesión se hizo entera en un solo archivo, por decisión del equipo, y se partió por
misión con [`herramientas/partir_grabacion.py`](../../herramientas/partir_grabacion.py), con la
ventana de cada registro del coordinador (2 s antes de la solicitud y 5 s después del cierre).
Desde la raíz del repositorio, con `source ~/deepracer_sim_ws/install/setup.bash`:

```bash
python3 herramientas/partir_grabacion.py ~/tesis_evidencia/campo_2026-10-16/mision_G6_campana_recuperada ~/tesis_evidencia/campo_2026-10-16/misiones_G6 --mision G6_01=Documentos/Evidencia/campo_20261016/registros/mision_manual_20261017_001041.json
```

```bash
python3 herramientas/componer_registro.py ~/tesis_evidencia/campo_2026-10-16/misiones_G6/mision_G6_01 --banco fisico --campana RF27 --distro jazzy --catalogo Robot/aws-deepracer/deepracer_bringup/config/puntos_interes_pisos34.yaml --error-posicion-m 0.4354 --medido-por coordinador --fuente-llegada localizacion_agente --salida Documentos/Evidencia/registros/RF27_G6_01.json
```

```bash
python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana RF27 --json Documentos/Evidencia/S27_metricas_rf27.json
```

Las misiones 2 a 9 usan los registros `20261017_001324`, `001606`, `001837`, `002056`, `002259`,
`002517`, `002659` y `002909`, y el error de llegada de cada uno (`metricas.error_llegada_m`). G-5 sale
de `mision_20261016_223826` con `--campana G5`.

## Pendientes

- Confirmar si hubo personas en el pasillo durante las misiones, para RNF-03.
- La causa de las transformadas detenidas en Nav2 queda abierta; no afecta a las nueve misiones.
