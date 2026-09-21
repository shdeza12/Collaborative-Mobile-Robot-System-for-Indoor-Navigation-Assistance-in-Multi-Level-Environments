# Fe de erratas del informe de la semana 15, y cierre del riesgo R6

*Tarea 1.5 del `MAPA_TRABAJO_RESTANTE.md`. 2026-09-21. Trabajo de escritorio.*

## 0. Por qué una fe de erratas y no una corrección

El riesgo **R6** —«discrepancias informe ↔ repositorio»— llevaba abierto desde el 2026-08-03 con
siete filas registradas en el §5 de `ESTADO.md`, todas del informe de la semana 15. Su acción
declarada era «corregir en el entregable de cierre de fase», y eso no se puede hacer: **S15 está
entregado, y además solo existe como PDF** —no hay fuente `.tex` que rehacer—. Reescribir un
informe entregado no cierra una discrepancia, la esconde.

Lo que cierra R6 es **publicar la corrección**: dejar por escrito, afirmación por afirmación, qué
dijo el informe, qué dice el artefacto, y cuál de los dos tiene razón. Un jurado que encuentre la
discrepancia encontrará también este documento.

**Las afirmaciones se citan del PDF, no del §5 de `ESTADO.md`.** El registro de agosto es una
transcripción hecha hace siete semanas, y una fe de erratas que copia una transcripción hereda sus
errores. Se extrajo el texto del entregable y se comprobó cada línea.

## 1. Las siete filas, resueltas

| # | Lo que afirma S15 | Lo que hay en el repositorio | Veredicto |
|---|---|---|---|
| 1 | El mapa se guardó como `primer_piso_mapa.pgm` / `.yaml` mediante el servicio `/slam_toolbox/save_map` | Los ficheros se llaman `primer_piso.pgm` / `.yaml`. **Ningún fichero con el nombre `primer_piso_mapa` ha existido nunca** en la historia del repositorio | **Errata de nombre.** El artefacto existe; el nombre publicado no |
| 2 | `resolution = 0.05` m/celda, y el análisis se apoya en «el margen de resolución de 5 cm» | `primer_piso.yaml` declara `resolution: 0.06` | **El informe se equivoca.** El artefacto manda |
| 3 | «La extensión del mapa es consistente con las dimensiones aproximadas del pasillo (44 m × 5 m)» | El `.pgm` mide **384 × 262 celdas**, que a 0,06 m son **23,04 m × 15,72 m** | **Afirmación falsa, y no por la resolución:** véase §2 |
| 4 | «Captura del quiebre en L — Satisfactorio» | No es identificable en el mapa guardado | **Retirada.** Véase §3 |
| 5 | `minimum_travel_distance = 0.5`, `minimum_travel_heading = 0.5` | En la auditoría de agosto el fichero declaraba `0.1` y `0.57`; **hoy declara `0.15` y `0.3`** | **El informe se equivoca**, y el valor correcto no es el de hoy: véase §4 |
| 6 | «Modo *online asynchronous*» | `slam_toolbox.launch.py:107` instancia `sync_slam_toolbox_node`, el nodo **síncrono**, y lo sigue haciendo hoy | **El informe se equivoca.** No es un matiz: el modo síncrono procesa cada barrido, el asíncrono descarta bajo carga |
| 7 | «Las aperturas de la pared sur explican las celdas desconocidas» | La causa incluye deriva de pose por parámetros mal dimensionados, y desde entonces se midió un mecanismo más profundo | **Análisis superado.** Véase §5 |

## 2. La fila 3 no es una errata de unidades: el mapa cubre medio pasillo y el triple de ancho

Esta es la que importa, y conviene no despacharla como un número mal copiado.

El pasillo **sí mide ~44 m**: `ENTORNO_DE_EVALUACION.md` describe tramos de pared de 44,25 m. La
cifra del informe describe correctamente **el mundo**. Lo que el informe no hizo fue **medir el
mapa** antes de declararlo consistente con el mundo.

| | Largo | Ancho |
|---|---|---|
| El pasillo | ~44 m | ~5 m |
| El mapa guardado (384 × 262 a 0,06) | **23,04 m** | **15,72 m** |
| El mapa si la resolución fuera la declarada (0,05) | 19,20 m | 13,10 m |

**Falla con las dos resoluciones**, así que el error de la fila 2 no la explica. Y el patrón tiene
forma reconocible: **falta la mitad del largo y sobra el triple del ancho**. Un mapa que se ensancha
sobre un pasillo recto mientras se queda corto no es un mapa incompleto, es un mapa **deformado**,
y la deformación es de pose, no de geometría.

Eso importa porque el proyecto midió ese mecanismo tres meses después y por otro camino: la
**inobservabilidad longitudinal del pasillo** —el sensor no tiene con qué estimar el avance a lo
largo del eje— que el 2026-09-08 produjo un mapa de 1166 m sobre una recta de 20 m. **El fallo de
S15 y el de S22 son el mismo fallo**, y S15 lo tenía delante sin saberlo, con el mapa ya en disco.

La afirmación se retira. Lo que la sustituye es más útil que una corrección de cifras: **el mapa de
S15 fue la primera manifestación, no diagnosticada, del problema central del proyecto.**

## 3. Sobre la fila 4: qué se puede decir y qué no

La acción registrada era «reevaluar tras repetir el mapeo». El mapeo se repitió muchas veces desde
entonces, pero **no sobre este mundo ni sobre este mapa**: el entorno vigente es
`mundo_definitivo_piso1.world` con su propio mapa generado por geometría, no por SLAM.

Por tanto la afirmación **no se puede reevaluar: se retira.** Declararla «confirmada» exigiría un
mapa que ya no se produce, y declararla «falsa» exigiría una comprobación que nadie hizo. Se deja
retirada, que es lo único que la evidencia sostiene.

## 4. Sobre la fila 5: por qué el valor de hoy tampoco corrige el informe

La tentación era sustituir `0.5 / 0.5` por los valores actuales, `0.15 / 0.3`. **Sería otra
errata.** Los parámetros han cambiado al menos dos veces desde S15 —en la auditoría de agosto
declaraban `0.1` y `0.57`—, así que los de hoy no son los que corrían cuando se midió S15.

Lo correcto es lo que dice esta fe de erratas: **la tabla del informe no describe la configuración
con la que se produjo su propio mapa**, y cuál era exactamente esa configuración ya no es
recuperable. No se inventa.

## 5. Sobre la fila 7, y lo que S15 sí acertó

La pared sur abierta **existe** —es el riesgo **R4**, identificado desde S14 y todavía abierto—,
así que la explicación de S15 no era inventada: era **insuficiente**. Atribuía a la geometría del
mundo lo que la instrumentación y la observabilidad del sensor explican mejor. El análisis del
§3.4 queda superado por §2 de este documento.

Y una fila en la que **el informe tenía razón y el registro interno no**: S15 declara
`max_laser_range = 12.0`, y esa es exactamente la configuración que el simulador estaba
ejecutando. La bitácora del 2026-08-03 afirmaba haberlo bajado a 9,5 —lo que se corrigió el
2026-08-05 al descubrir que el arreglo vivía solo en el repositorio—. **El informe describía la
realidad y la bitácora describía una intención.** Se anota porque R6 se enuncia como si el informe
fuera siempre la parte equivocada, y no lo es.

## 6. Hallazgo colateral, y una corrección de una línea

`nav2_params_nav_amcl_dr_demo.yaml:152` comenta que la resolución del costmap global «debe
coincidir con la resolucion del mapa (`primer_piso.yaml`)», citando un mapa que ya no es el
vigente. **El valor es correcto** —`mundo_definitivo_piso1.yaml` también declara 0,06—, así que no
hay defecto de comportamiento; lo que hay es una referencia rancia que apunta al artefacto de S15.
Se actualiza el comentario. El `yaml_filename: primer_piso.yaml` de la línea 323 **no se toca**: su
propio comentario advierte que el argumento `map:=` del launch lo sobreescribe, y el launch declara
por defecto `mundo_definitivo_piso1.yaml`.

## 7. Qué queda cerrado y qué no

**R6 queda cerrado.** Las siete discrepancias tienen veredicto publicado: tres erratas del informe
(1, 2, 6), una afirmación falsa con mecanismo explicado (3), dos retiradas por no ser reevaluables
o estar superadas (4, 7) y una precisión sobre qué valor es el correcto (5). Ninguna queda con
acción pendiente.

**Lo que no cierra.** **R4 sigue abierto**: la pared sur del SDF sigue sin cerrar. Y este documento
no rehace el mapeo de S15 ni lo pretende — el mapa de aquel informe no vuelve a usarse.

## 8. Trazabilidad

| Afirmación | Fuente |
|---|---|
| Las siete afirmaciones de S15, textuales | `Entregable_semana_15.pdf`, texto extraído el 2026-09-21 |
| S15 solo existe como PDF, sin fuente `.tex` | `git ls-files Documentos/Entregables/` |
| `primer_piso_mapa` nunca existió en el repositorio | `git log --all --diff-filter=A`, 0 coincidencias |
| `primer_piso.yaml` declara `resolution: 0.06` | El propio fichero |
| El mapa mide 384 × 262 celdas | Cabecera del `.pgm` |
| El pasillo mide ~44 m | `ENTORNO_DE_EVALUACION.md` |
| El launch instancia el nodo síncrono | `slam_toolbox.launch.py:107` |
| Hoy `minimum_travel_distance: 0.15`, `minimum_travel_heading: 0.3` | `config/slam_toolbox.yaml:42-43` |
| La inobservabilidad longitudinal está medida | `S22_mapeo_pasillo_fallido.md` |
| R4 sigue abierto desde S14 | Tabla de riesgos de `ESTADO.md` |
