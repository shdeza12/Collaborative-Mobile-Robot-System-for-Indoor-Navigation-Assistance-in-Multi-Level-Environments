# Plan de la semana 27 (12 al 16 de octubre)

Última semana de toma de datos. El corte C-3 del viernes 16
([`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md)) pide G-5, una misión con relevo entre los dos vehículos, y
G-6, las repeticiones de RF-27. Después del viernes no se toman más datos: se reporta lo corrido con
su n real. El campo estaba previsto el jueves 15 y el viernes 16 (decisión del equipo, 13-oct). El
15-oct el equipo aplazó el jueves: G-5, G-6 y el cierre de datos se hacen el viernes 16, en un solo
día. El resto de la semana es preparación y documentación.

Desde la semana 26 la cadena completa con los dos vehículos funciona en el laboratorio, con el
coordinador en el portátil
([`S26_laboratorio_carga_dos_vehiculos.md`](../Evidencia/S26_laboratorio_carga_dos_vehiculos.md)), y G-3
está alcanzada. Las misiones de G-6 están sorteadas
([`campana_rf27_misiones.csv`](../Evidencia/campana_rf27_misiones.csv), `7a41815`).

## 0. La semana de un vistazo

| Día | Qué se hace | Vehículos | Al terminar el día |
|---|---|---|---|
| Mar 13 | Sorteo de G-6 (hecho). Este plan. Arreglos de `componer_registro.py` y `analizar_campana.py` para el banco físico (§1.2). Subcomando `comprobar` (§1.3) | no | Herramientas listas y probadas en el portátil |
| Mié 14 | Evidencia del 8-oct (§5). Documento final, capítulos 7 y 8 (§5). Revisión de la matriz de requisitos (§5, decisión del equipo). Baterías cargadas (§1.4) | no | Todo cargado y la documentación de la semana 26 cerrada |
| Jue 15 | Campo aplazado. Revisión de la matriz de OE2 (§5), capturas al índice de evidencias (§5) y este plan ajustado a un día. Baterías cargadas en la noche (§1.4) | no | OE2 cerrado en la matriz; todo cargado |
| Vie 16 | Marcas de los destinos (§2.1), arranque (§2.2), G-5 (§2.3), G-6 desde la misión 1 (§2.4), datos de deepy del 8-oct (§2.5), cierre de datos (§3.2). Corte semanal en la noche (§3.3) | los dos | G-5 y G-6 con registro y los datos cerrados; acta, `ESTADO.md` y análisis al día |

Reglas de toda la semana, además de las de [`PLAN_S26.md`](PLAN_S26.md) §0:

- Las misiones de G-6 se corren en el orden del listado, sin saltar ni repetir ninguna. Una misión
  que falla se registra con su causa y se sigue con la siguiente.
- Los vehículos no se reubican entre misiones (acta §6.2). Si hay que mover uno por seguridad, se
  anota en la hoja como «reubicado» con la razón, y la misión cuenta como fallida.
- Una grabación por misión: `componer_registro.py` rechaza una grabación con dos misiones.
- Cada llegada final se mide con flexómetro antes de tocar el vehículo o pedir la misión siguiente.
- Una persona junto a cada vehículo durante sus medias vueltas. La secuencia sorteada pide unas tres
  por misión, y 15 de las 31 caen en la zona de la escalera (2,52 a 2,58 m de ancho).
- En el portátil, como máximo cuatro procesos ROS durante las misiones: coordinador, `rosbridge`,
  `rosapi` y grabador. Nada de `ros2 topic` mientras una misión corre.

## 1. Antes del campo

### 1.1 · Sorteo de las misiones de G-6 (hecho el 13-oct)

Semilla 20261013, 5 misiones del piso 3 al 4 y 5 del 4 al 3, entre los salones y el ascensor de cada
piso. Las escaleras son el punto de relevo y no entran al sorteo. El listado se subió antes de
cualquier corrida, que es lo que pide el §6.3 del protocolo.

| # | Origen | Destino | # | Origen | Destino |
|---|---|---|---|---|---|
| 1 | Ascensor, piso 3 | Salón 403 | 6 | Salón 301 | Salón 401 |
| 2 | Salón 302 | Salón 401 | 7 | Ascensor, piso 4 | Salón 301 |
| 3 | Salón 401 | Salón 302 | 8 | Salón 302 | Salón 403 |
| 4 | Salón 403 | Salón 303 | 9 | Salón 303 | Salón 402 |
| 5 | Salón 402 | Salón 301 | 10 | Salón 403 | Ascensor, piso 3 |

Simulada la secuencia completa, G-5 incluida y sin reubicar los vehículos: 383 m entre los dos y 31
medias vueltas en las 11 misiones. En 1000 sorteos con otras semillas salen entre 21 y 35 (mediana 29): el número viene
de la operación del acta §6.2.

### 1.2 · La cadena de registro con datos del banco físico

Probada el 13-oct en el portátil con una misión grabada por el contenedor, sin vehículos: el
adaptador y el compositor funcionan y el registro valida. Antes de componer los
registros de G-6 hay que corregir esto:

| Herramienta | Defecto | Arreglo |
|---|---|---|
| `componer_registro.py` | `escenario_por_robot` sale de la configuración de la simulación (`mundo_definitivo_piso1`) | En el banco físico, el mapa de cada robot es el de su piso (`maps/piso3.yaml`, `maps/piso4.yaml`) |
| `componer_registro.py` | `catalogo_puntos` dice siempre `puntos_interes.yaml` | El nombre del catálogo que se pasa con `--catalogo` |
| `componer_registro.py` | `marcas.reloj` dice `/clock` | En el banco físico, el reloj del grabador (hora de recepción) |
| `analizar_campana.py` | Escribe la tolerancia de simulación (0,25 m) en el encabezado de RF-23 y en el error de llegada | La del banco del registro: 0,5 m en el físico |
| `analizar_campana.py` | Alerta de «tiempo de asignación > 0» como hallazgo grave | En el banco físico el reloj es continuo: se informa el valor, sin alerta |

Cierre: `prueba_componer_registro.py` y `prueba_analizar_campana.py` con comprobaciones nuevas para el
banco físico, y un registro de prueba que diga `piso3.yaml`, `piso4.yaml` y
`puntos_interes_pisos34.yaml`.

Estado del 13-oct: hecho. El escenario de cada robot sale del piso del punto al que lo mandó el
coordinador. Con la grabación de prueba, el registro dice `piso3.world`, `piso3.yaml`,
`puntos_interes_pisos34.yaml` y reloj `pared`, y el analizador escribe 0,50 m. Las dos pruebas
suman 6 comprobaciones del banco físico.

### 1.3 · Comprobación de la topología desde el portátil

`coordinador_portatil.sh comprobar`: desde el contenedor, busca `/robotN/navigate_to_pose`,
`/robotN/media_vuelta` y `/robotN/estado` de los dos robots y escribe la pose de cada uno. Es lo que se
hizo a mano el 9-oct. Ocupa un proceso ROS mientras corre, así que va antes de `interfaz`.

Estado del 13-oct: hecho, y probado sin vehículos: tarda hasta 40 s, informa lo que falta y sale
con error si falta algo.

### 1.5 · La verificación de llegada del coordinador (hecho el 13-oct)

Ninguna misión coordinada había llegado a destino con los vehículos. Al reconstruir la pose del mapa de
las llegadas de racey del 7-oct (TF de sus grabaciones), el vehículo estaba a 0,53-0,62 m de la meta
en la última orden de avance de Nav2 y a 0,09-0,53 m un segundo después, ya quieto. El coordinador
verificaba la llegada al recibir `SUCCEEDED`, con la última pose del agente (2 Hz): habría visto 0,53
a 0,96 m y rechazado las cuatro llegadas.

| Llegada del 7-oct | Cinta | Pose del mapa al parar | Un segundo después |
|---|---|---|---|
| Salón 403 | sin medir | 0,62 m | 0,23 m |
| Salón 402 | 0,45 m | 0,53 m | 0,53 m |
| Salón 401 | 0,06 m | 0,58 m | 0,09 m |
| Salida | 0,34 m | 0,57 m | 0,18 m |

Arreglo en `coordinador.py`: con `condicion:=hardware`, tras `SUCCEEDED` espera una pose del agente
recibida 1,5 s después (`ASENTAR_LLEGADA_S`) y entonces mide. `prueba_coordinador_vehiculo.py` tiene
un escenario con inercia (`SUCCEEDED` a 0,65 m y 0,45 m más rodando): falla con el código anterior y
pasa con el nuevo, 16 de 16, en Humble y en el contenedor con Jazzy. La imagen del contenedor está
reconstruida. El viernes, el paso 3 del arranque copia el coordinador nuevo a los vehículos.

Queda abierto: la llegada al 402 se habría rechazado igual (0,53 m según la pose del mapa, 0,45 m
con cinta). Es el error de AMCL, no el momento de medir.

### 1.6 · La media vuelta pedida por el coordinador (probada el 13-oct)

La cadena completa no había corrido nunca: ninguna prueba ofrecía el servicio `media_vuelta`, en el
laboratorio las metas quedaban al frente y el 8-oct la maniobra se lanzó a mano con
`herramientas/media_vuelta.py`. `prueba_coordinador_vehiculo.py` tiene ahora robots falsos que ofrecen
el servicio. En G-5, robot1 recibe la meta al 302 sin maniobra, la media vuelta y la meta a la
escalera, y robot2 no recibe ninguna. Pasa 19 de 19 en Humble y en el contenedor con Jazzy; con el
coordinador anterior a la media vuelta (`dbd29d9^`) falla. En el campo, la primera media vuelta
pedida por el coordinador es la de deepy en el Salón 302, dentro de G-5.

### 1.4 · Baterías y material

- [ ] Batería de la tarjeta y de tracción de los dos vehículos, cargadas el jueves en la noche.
- [ ] Flexómetro, cinta de enmascarar y marcador.
- [ ] Dos teléfonos con la grabación de pantalla probada, uno por piso ([`HOJA_CAPTURA_S26.md`](HOJA_CAPTURA_S26.md), fila de G-5).
- [ ] La hoja de la campaña impresa (§4).

## 2. Viernes 16: campo

Reparto propuesto, que confirma el equipo: Santiago en el piso 3 con el portátil y Jonny en el piso 4.
El usuario de cada misión es la persona del piso de origen. Pide la misión desde el teléfono, sigue al
vehículo hasta la escalera, sube o baja, y confirma en la página la llegada al otro piso.

### 2.1 · Marcas de los destinos

Una cruz de cinta en cada destino, con las coordenadas del catálogo
([`GUIA_PISOS_3_Y_4.md`](../GUIA_PISOS_3_Y_4.md) §3): x a lo largo del pasillo desde la pared norte, y
desde la pared oeste. La distancia a la pared sur sale de la salida de cada piso. En el piso 3 la salida
(x = 22,10) está a 3,23 m de la pared sur; en el piso 4 (x = 24,45), a 1,00 m. Se mide desde la pared más cercana.

| Destino | Desde la pared norte | Desde la pared sur | Desde la pared oeste |
|---|---|---|---|
| Salón 301 | 6,20 m | — | 2,00 m |
| Salón 302 | 9,31 m | — | 2,21 m |
| Ascensor, piso 3 | — | 8,79 m | 1,30 m |
| Salón 303 | — | 8,11 m | 2,00 m |
| Salón 401 | 6,20 m | — | 2,03 m |
| Salón 402 | 9,31 m | — | 2,15 m |
| Ascensor, piso 4 | — | 9,06 m | 1,36 m |
| Salón 403 | — | 8,23 m | 2,06 m |

Cierre: ocho cruces, cada una fotografiada con la cinta en el cuadro.

### 2.2 · Arranque

| Paso | Qué | Comando o acción | Esperado | Si falla |
|---|---|---|---|---|
| 1 | Confirmar el sitio | Deepy en la salida del piso 3, racey en la del piso 4, los dos mirando al norte | Los dos en su marca de salida | No se arranca con un mapa que no es del sitio |
| 2 | Red | `ping -c 3 192.168.0.102` y `ping -c 3 192.168.0.104`; el portátil en `192.168.0.105` | Respuesta de los dos, sin duplicados | [`TOPOLOGIA_RED.md`](../TOPOLOGIA_RED.md) |
| 3 | Vehículos iguales al repositorio | `bash herramientas/nivelar_carros.sh` | `Los vehiculos estan nivelados con el repositorio.` | `--copiar` |
| 4 | Las dos cadenas, a la vez | deepy: `NS=robot1 IMU=true MARGEN=0.5 CARRO=192.168.0.102 MAPA=/home/deepracer/tesis/piso3.yaml POSE_X=22.10 POSE_Y=1.06 POSE_YAW=3.1416 bash herramientas/nav2_mapa_guardado.sh`; racey: `NS=robot2 IMU=true MARGEN=0.5 CARRO=192.168.0.104 MAPA=/home/deepracer/tesis/piso4.yaml POSE_X=24.45 POSE_Y=1.21 POSE_YAW=3.1416 bash herramientas/nav2_mapa_guardado.sh` (ruta fija del vehículo) | `CADENA LISTA` en los dos en unos 4 a 4,5 min, con los seis nodos `active` | El aviso en rojo dice la pieza. LiDAR sin barridos: `sudo systemctl restart deepracer-core` en el vehículo y repetir |
| 5 | Un agente en cada vehículo | La orden de [`PLAN_S26.md`](PLAN_S26.md) §4.2, paso 3, en los dos | `/tmp/agente.log` con `publicando estado a 2.0 Hz` y el mapa de la media vuelta cargado | Revisar que `/tmp/nav2_campo/pares.sh` tenga la IP del portátil |
| 6 | Coordinador | `bash herramientas/coordinador_portatil.sh arrancar` | `coordinador listo`, con `3: 'robot1'` y `4: 'robot2'` en la asignación | `bash herramientas/coordinador_portatil.sh registro` |
| 7 | Topología | `bash herramientas/coordinador_portatil.sh comprobar` | Los dos robots con `navigate_to_pose`, `media_vuelta` y estado, con la pose junto a su salida | Si falta un robot: su cadena o su agente no cruzaron la red (pasos 4 y 5) |
| 8 | Interfaz | `bash herramientas/coordinador_portatil.sh interfaz` y la página en los dos teléfonos, `http://192.168.0.105:8000/` | Los destinos de los pisos 3 y 4 en la página | `/tmp/rosbridge.log`; recargar la página |

### 2.3 · G-5: misión del Salón 302 al Salón 402

La misión fija de [`PLAN_S26.md`](PLAN_S26.md) §5.1, variante A.

| Paso | Qué | Esperado | Cierre |
|---|---|---|---|
| 1 | `bash herramientas/coordinador_portatil.sh grabar G5_01` | `grabando .../mision_G5_01` | — |
| 2 | Desde el teléfono del piso 3: origen Salón 302, destino Salón 402 | Deepy va al 302, da media vuelta y guía hasta la escalera; la página pide subir; tras confirmar, racey guía hasta el 402. Mientras uno navega, el otro no se mueve | Video en cada piso, según la hoja de captura |
| 3 | Al terminar, Enter en la terminal del paso 1 | `== listo: .../mision_G5_01` | — |
| 4 | Medir la llegada de racey a la cruz del 402 | Distancia en metros, anotada en la hoja (§4) | Foto con la cinta |
| 5 | Componer el registro (§4.1) | `Registro escrito en ...` | G-5 alcanzada si la misión completa con relevo y la llegada medida queda en 0,5 m o menos |

### 2.4 · G-6: misiones del listado

Cada misión repite los pasos 1 a 5 de G-5, con el nombre `G6_NN` y el origen y el destino del
listado (§1.1), sin reubicar los vehículos. Entre una misión y la siguiente:

1. Anotar en la hoja la medida, la duración que muestra la página y cualquier incidencia. Entre las
   incidencias van las personas que pasaron por el pasillo durante la misión: RNF-03 las registra
   como observación cualitativa.
2. Revisar la batería de los dos vehículos. Con menos de un tercio, parar (§2.6), cargar y reanudar
   el mismo día desde la misión siguiente (§3.1).

G-6 necesita al menos cinco misiones con registro (acta §4, decisión D1). Se corren en el orden del
listado, hasta la décima, mientras haya batería y tiempo. Una misión que falla cuenta en el n igual
que una que llega: se registra con su causa y se sigue con la siguiente.

### 2.5 · Datos del 8-oct de deepy

Con deepy encendido, antes o después de las misiones:

`scp deepracer@192.168.0.102:campana_s26_deepy.csv ~/tesis_evidencia/campo_2026-10-08/` y
`scp -r 'deepracer@192.168.0.102:campana_p3d_0*' 'deepracer@192.168.0.102:mv_p3d_0*' ~/tesis_evidencia/campo_2026-10-08/`

Cierre: el CSV y las grabaciones `campana_p3d_01` a `05` y `mv_p3d_04`, `04b` y `05` en el portátil.

### 2.6 · Parar

1. `bash herramientas/coordinador_portatil.sh parar`.
2. `NS=robot1 CARRO=192.168.0.102 bash herramientas/nav2_mapa_guardado.sh --parar`, y lo mismo con
   `robot2` y `192.168.0.104`.
3. Los agentes, en los dos (`.102` y `.104`): `ssh deepracer@192.168.0.102 "sudo -n pkill -f '[c]oordinacion/agente'"`.
4. `mkdir -p ~/tesis_evidencia/campo_2026-10-16` y copiar los registros de carga de los dos:
   `scp 'deepracer@192.168.0.102:carga_*.csv' ~/tesis_evidencia/campo_2026-10-16/` (y `.104`).
5. Marcar en el piso la posición y el rumbo de cada vehículo antes de recogerlo (§3.1).

## 3. Viernes 16: reanudar y cerrar

### 3.1 · Reanudar después de cargar las baterías

Solo si hubo que parar por batería (§2.4). Arranque como en el §2.2, con cada vehículo en el destino
donde terminó y con el rumbo con que llegó: antes de recogerlo se marca su posición (§2.6, paso 5) y
después se pone en esa marca. La pose inicial del paso 4 es la de ese destino en el catálogo (§2.1). El rumbo es `POSE_YAW=3.1416`
si llegó yendo hacia el norte y `POSE_YAW=0.0` si llegó yendo hacia el sur. Se sigue el listado desde la misión
siguiente a la última corrida.

### 3.2 · Cierre de datos (corte C-3)

Después de la última misión del viernes no se corre ninguna más, aunque queden misiones del listado.
El n de G-6 es el número de misiones corridas del listado, con su resultado.

| Paso | Comando | Esperado |
|---|---|---|
| 1 | Componer los registros que falten (§4.1) | Un JSON por misión en `Documentos/Evidencia/registros/` |
| 2 | `python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana RF27 --json Documentos/Evidencia/S27_metricas_rf27.json` | `VEREDICTO: VALIDA` y las cuatro métricas del banco físico |
| 3 | Acta: estado de G-5 y G-6 con su n real ([`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md) §4.1, resultados declarados) | — |

### 3.3 · Corte semanal

Evidencia de la campaña (`Evidencia/S27_campana_rf27.md`), `ESTADO.md` y entregable de la semana 27
en `.md` y `.tex`, con la batería completa antes del push.

## 4. Hoja de la campaña

Una fila por misión, en papel y después en `~/tesis_evidencia/campana_rf27.csv`:

| Misión | Hora | Origen → destino | Resultado en la página | Llegada medida (m) | Medias vueltas | Incidencias | Medido por |
|---|---|---|---|---|---|---|---|
| G5_01 | | Salón 302 → Salón 402 | | | | | |
| G6_01 | | Ascensor 3 → Salón 403 | | | | | |
| … | | | | | | | |

### 4.1 · Registro de cada misión

En el portátil, desde la raíz del repositorio, con `source ~/deepracer_sim_ws/install/setup.bash`:

1. `python3 herramientas/adaptar_bag_jazzy.py ~/tesis_evidencia/mision_G6_01 -o ~/tesis_evidencia/mision_G6_01_humble`
2. `python3 herramientas/componer_registro.py ~/tesis_evidencia/mision_G6_01_humble --banco fisico --campana RF27 --distro jazzy --catalogo Robot/aws-deepracer/deepracer_bringup/config/puntos_interes_pisos34.yaml --error-posicion-m <medida> --medido-por <quien> --salida Documentos/Evidencia/registros/RF27_G6_01.json`

G-5 usa el mismo comando con `mision_G5_01` y `RF27_G5_01.json`. Esperado: `Registro escrito en ...`.
Si el compositor dice que la grabación tiene dos misiones, el grabador no se cerró entre una y otra.
La misión se anota en la hoja y su registro queda pendiente.

## 5. Documentación de la semana

| Qué | Dónde | Estado |
|---|---|---|
| Evidencia del 8-oct: piso 3 con deepy (cinco corridas), primeras medias vueltas del agente (160° y 167°) e intento de G-5 con la saturación de las tarjetas | [`S26_piso3_deepy_y_saturacion.md`](../Evidencia/S26_piso3_deepy_y_saturacion.md) | Hecha el 13-oct con los registros del portátil; las grabaciones de deepy se agregan el viernes |
| Estado del 8-oct en `PLAN_S26.md` §3.4 | `PLAN_S26.md` | Hecho el 13-oct |
| Videos del 7-oct | `S26_piso4_cadena_media_vuelta.md`, punto 4 | Los sube el equipo |
| Documento final: capítulo 7 (IMU, media vuelta, coordinador en el portátil, aislamiento) y capítulo 8 (G-2 con el filtro, G-3, carga de las tarjetas) | `DocumentoFinal/capitulos/` | Hecho el 13-oct (`3edf3a3`), sin compilar; G-5 y G-6 después del viernes |
| Matriz de requisitos: RF-11 a RF-14 y RF-16 con la evidencia de campo de G-2, G-3 y del laboratorio del 9-oct | [`REQUISITOS.md`](../REQUISITOS.md), revisión del 15 de octubre en el §3 | Hecha el 15-oct: los cinco verificados y OE2 en 100 %, con dos decisiones del equipo (RF-12 y RF-14) |
| Capturas de las semanas 10 a 25, con su uso en el documento final | [`CAPTURAS_POR_FASE.md`](../Evidencia/CAPTURAS_POR_FASE.md) | Hecho el 15-oct (`766186d`) |
| Conclusiones y presentación (cronograma de S27) | `DocumentoFinal/capitulos/09-conclusiones.tex` | Después del corte C-3 |

## 6. Riesgos y salidas

| Riesgo | Señal | Qué hacer |
|---|---|---|
| La media vuelta no completa | El agente devuelve fallo; el coordinador sigue con Nav2 | Dejar que Nav2 lo intente. Si aborta, la misión falla con esa causa y se sigue con la siguiente |
| Vehículo atascado o cerca del vano de la escalera | La persona junto al vehículo lo ve | Cancelar la misión desde la página: el vehículo vuelve a la escalera (RF-29). Anotar la causa |
| El LiDAR deja de publicar | `CADENA LISTA` no llega o el paso 1 del guion falla | `sudo systemctl restart deepracer-core` en el vehículo, esperar 30 s y relanzar su cadena |
| La página pierde la conexión | Se queda en «conectando» | Recargar; si sigue, `bash herramientas/coordinador_portatil.sh interfaz` |
| La batería no alcanza | Menos de un tercio entre misiones | Parar (§2.6), cargar y reanudar el mismo día (§3.1) |
| G-5 no completa | La misión 302 → 402 falla | Se registra con su causa y se sigue con G-6, sin repetirla. El criterio de G-5 en el acta (§4) es una misión con relevo de extremo a extremo sobre los dos vehículos, con su registro compuesto: lo cumple también una misión de G-6 que complete |
| No se alcanzan las diez misiones | Viernes en la tarde | Se reporta el n real (acta, C-3). Con menos de cinco, G-6 queda no alcanzada |
