# Video de la campaña con los dos vehículos, sincronizado con la pantalla del teléfono (19 y 20 de octubre)

Edición del material grabado el 16 de octubre por el equipo: el POV de quien hizo de usuario en cada
misión, la grabación de la pantalla de su teléfono durante toda la sesión y, en las misiones 4, 5 y 9,
el POV del carro del otro piso mientras iba a su escalera. Los videos no se versionan (`VIDEOS/` está en
`.gitignore`); quedan en la carpeta `VIDEOS/` del equipo.

## Resultado

- `VIDEOS/editado/campana_dos_vehiculos_v2.mp4`: 12 min 40 s (759,6 s), 1920×1080, 30 fps, sin audio,
  a tiempo real. A la izquierda el POV del usuario, a la derecha la pantalla del teléfono en el mismo
  instante; abajo, la etapa de la misión según las marcas del coordinador y el tiempo desde la
  solicitud. En los relevos de las misiones 4, 5 y 9 se ven los dos POV lado a lado. La misión 10
  termina con la desconexión del coordinador. No incluye los primeros intentos fallidos de las
  misiones 1 y 2 (decisión del equipo).
- `VIDEOS/editado/proyecto_shotcut/campana_dos_vehiculos.mlt`: el mismo montaje como proyecto de
  Shotcut, en cinco pistas, para retocarlo a mano. Verificado renderizando cuadros con `melt` 7.4.
- Herramientas, fuera del repositorio, en `~/tesis_evidencia/video_campana/`: `preparar.py` (videos
  recortados y alineados por tramo), `remotion/` (composición `CampanaSobria`), `proyecto_shotcut.py` y
  `generar_todo.sh`.

![Relevo de la misión 4 en el video](S28_video_campana_relevo.jpg)

## Sincronización

1. Pantalla del teléfono contra el coordinador: UTC = t_pantalla + 616,6 s. Se midió con el primer cuadro
   de «Hemos llegado» en las nueve misiones y en el intento con destino equivocado, contra la marca
   COMPLETADA de cada registro del coordinador: dispersión de ±0,3 s. La grabación de la pantalla tiene
   cuadros solo cuando cambia algo (6449 cuadros en 2899 s), así que el cuadro de cada instante es el
   último anterior a él.
2. POV de cada misión: la hora guardada en el archivo es la de fin de la grabación, y el reloj del
   teléfono coincide con el del portátil. Se comprobó con el teléfono visible dentro del POV en las
   misiones 4, 5 y 9: muestra la misma etapa que la grabación de la pantalla en el mismo instante.
3. Las misiones 2, 3, 8 y 9 tienen la escalera recortada en el video original, con un corte duro en
   22,9 s, 39,0 s, 48,2 s y 39,6 s. Cada una va en dos partes. La primera se ubicó por la pulsación de
   «Pedir guía», visible en la misión 8 entre 6,50 s y 6,75 s, y por la media vuelta y la salida del
   carro (registros de los agentes, con el mismo reloj que el coordinador). La segunda, por la hora de
   fin del archivo y el teléfono visible en el POV.
4. La misión 1 llegó en dos archivos ya recortados; se ubicaron por el movimiento del carro.
5. Los POV del otro piso (sin hora en el archivo) se ubicaron por la llegada del carro a su escalera y
   el arranque del tramo 2.

| Misión | Pieza | Inicio de la pieza (s desde la solicitud) | Cómo se ubicó |
|---|---|---|---|
| 1 | piso 3 / piso 4 | +2,5 / +40,0 | Llegada a la escalera / arranque del tramo 2 |
| 2 | 1.ª / 2.ª | +2,5 / +58,0 | Fin de la media vuelta y salida / hora de fin |
| 3 | 1.ª / 2.ª | 0,0 / +64,8 | Media vuelta y salida a 12,1 s / hora de fin |
| 4 | completa | −0,1 | Hora de fin; teléfono visible a 37 s, 40 s y 66 s |
| 5 | completa | −0,2 | Hora de fin; teléfono visible a 60 s y 78 s |
| 6 | completa | +2,3 | Hora de fin |
| 7 | completa | −2,9 | Hora de fin |
| 8 | 1.ª / 2.ª | −6,7 / +51,6 | Pulsación de «Pedir guía» / «¿Ya subió?» visible a 48,4 s y 50,0 s |
| 9 | 1.ª / 2.ª | −0,5 / +50,0 | Media vuelta y llegada a la escalera / teléfono visible a 81 s |
| 10 | completa | +25,7 | Hora de fin |
| 4, 5, 9 (otro piso) | completa | +2,0, +26,0, +7,0 | Llegada a la escalera y arranque del tramo 2 |

La primera versión del video sincronizaba las misiones 2, 3, 8 y 9 con un solo desfase y dejaba la
primera parte corrida entre 10 s y 33 s; el equipo lo detectó al verla y se corrigió en la segunda.

## Misión 10

Sin registro del coordinador: el portátil se apagó antes de escribirlo. En la pantalla del teléfono la
misión empieza hacia las 19:35:10, la página pasa a «Sígueme» a los 9,2 s, a «Cambia de piso» a los 28,6 s
(con racey ya en su escalera) y a «Buscando el coordinador…» a los 30,2 s. La cifra de 18 s que se
publicó en la semana 27 salía del final de la grabación de datos, que pierde su último bloque al
cortarse; queda corregida en `S27_campana_rf27.md`, resultado 4.
