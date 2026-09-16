# Los 46 registros se rehacen desde los bags y dan lo mismo

**Fecha:** 2026-09-16 · **Cierre de la acción 6 de [`S22_barrido_criterios_infalsables.md`](S22_barrido_criterios_infalsables.md)**

## 0. La pregunta que había que contestar antes de tocar los registros

La acción 6 del barrido añadió `hueco_relevo_s` a las descriptivas. El barrido dejó abierto qué
hacer con los registros ya entregados —*«obligan a recomponer registros desde los bags conservados;
a trece días del congelamiento eso se decide con el cronograma delante, no aquí»*— y la respuesta
por defecto parecía obvia: recomponerlos todos y que ninguno quede sin la cifra.

Antes de hacerlo se recompuso **uno solo**, a un archivo temporal, para ver qué cambiaba. Cambiaba
`procedencia.commit`. Ese hallazgo obligó a hacer el experimento completo, y el experimento
terminó recomendando **lo contrario** de lo que se iba a hacer.

## 1. Qué se hizo

Se recompusieron **los 46 registros** de
[`Documentos/Evidencia/registros/`](registros/) desde sus bags conservados en
`~/tesis_evidencia/` (2,2 GB, 33 directorios de bag), con el código de hoy —commit `38be2da`,
esquema `1.3.0`— escribiendo a `/tmp` para no tocar el repositorio. Las banderas de cada
recomposición (`--banco`, `--campana`, `--semilla`, `--piloto`) se sacaron del propio registro
entregado, no de la memoria de nadie.

**Recompuestos: 44. Fallaron: 2.** Los dos que fallan son `S20_A_M1` y `S20_A_M2`, bags anteriores
al 2026-08-29 que no traen `rtf.json`; el compositor se niega a inventarles un RTF y lo dice con
todas las letras. Es la limitación que su propia ayuda ya documenta, no un defecto nuevo.

## 2. Qué salió

| Comprobación sobre los 44 | Resultado |
|---|---|
| Mismo `veredicto.exito` | **44 / 44** |
| Bloque `marcas` idéntico, campo a campo | **44 / 44** |
| Bloque `descriptivas` idéntico, quitando el campo nuevo | **44 / 44** |
| `hueco_relevo_s` compuesto vs. resta de las marcas del registro entregado | **23 huecos, discrepancia máxima 0,0** |

Ni un veredicto, ni una marca, ni una descriptiva se movió. La cadena bag → registro es
**reproducible**: el mismo dato crudo, pasado por un compositor que ha cambiado cuatro veces de
versión de esquema desde que se grabaron, devuelve exactamente los mismos números.

Esto no estaba comprobado hasta hoy. Es la evidencia de que los 30 resultados de OE4 no dependen
del estado en que estuviera el portátil el 5 de septiembre.

## 3. Qué sí cambia al recomponer, y por qué eso decide el asunto

| Campo | Registros afectados | Qué pasa |
|---|---|---|
| `descriptivas.hueco_relevo_s` | 44 | Aparece; es el campo nuevo |
| `esquema_version` | 44 | `1.1.0`/`1.2.0` → `1.3.0` |
| `procedencia.commit` | **44** | El commit de la corrida se sustituye por el de hoy |
| `procedencia.repositorio_limpio` | 8 | `true` → `false` |
| Campos de `1.1.0` en un registro `1.0.0` | 1 (`S20_RECIBIDA_01`) | Gana `continuidad` y `escenario_por_robot` |

La tercera fila es la que manda. `S21_OE4_15` se corrió con el commit `0e2b46c`; recomponerlo hoy
le escribe `38be2da`, que es **código que no existía el día de la corrida**. El campo dejaría de
decir «con este código se midió esto» para decir «con este código se leyó aquello», que es otra
afirmación y además una falsa, porque el lector razonable entiende la primera. La cuarta fila es
del mismo tipo: `repositorio_limpio` pasaría a describir el árbol de trabajo de hoy y no el del día
de la medida.

El propio compositor ya lo avisa en su código, desde antes de este experimento:

> *«LIMITACION, y hay que tenerla presente al recomponer bags viejos: esto lee el árbol de trabajo
> ACTUAL, no el del momento de la corrida. Componer poco después de correr es honesto; recomponer
> un bag de hace un mes con la configuración de hoy puede mentir.»*

## 4. Decisión: los registros entregados no se recomponen

**No se recompone ninguno.** Se argumenta hacia adelante, no se editan los artefactos entregados.

Lo que hace que la decisión sea barata es la última fila de la tabla del §2: los 23 huecos
compuestos coinciden con la resta de las marcas del registro entregado con **discrepancia 0,0** —no
«dentro de tolerancia»: exactamente el mismo número—. La razón es estructural: el compositor calcula
`t_inicio_tramo2 − t_fin_tramo1` sobre las mismas marcas que el registro publica. De modo que la
cifra **ya está** en los 46 registros, escrita como dos marcas en vez de como una resta, y
`analizar_campana.py` la lee así con `hueco_de()`, que no usa el campo nuevo. **No se pierde
ninguna evidencia por no recomponer.**

Consecuencias:

1. `hueco_relevo_s` rige **desde `1.3.0` hacia adelante**: lo traerá todo registro compuesto a
   partir de hoy. Los anteriores se quedan como están, en `1.1.0` y `1.2.0`.
2. Conviven dos poblaciones —con campo y sin campo— y el analizador lee las dos, porque saca el
   hueco de las marcas en ambos casos.
3. Como ahora hay dos fuentes para un mismo número, se añadió a `clasificar()` una comprobación de
   integridad: si un registro trae el campo y no cuadra con sus propias marcas (tolerancia 1 µs,
   frente a los 100 ms del tick de `/clock`), se declara error y **no se cuenta en ningún sitio**.
   Dos fuentes pueden separarse; separarse en silencio, no.

## 5. Trazabilidad

| Afirmación | De dónde sale |
|---|---|
| 44 recompuestos, 2 fallos por falta de `rtf.json` | Recomposición de los 46 registros a `/tmp/recompuestos`, 2026-09-16 |
| veredictos, marcas y descriptivas idénticos | Comparación campo a campo entre `Documentos/Evidencia/registros/` y los recompuestos |
| discrepancia 0,0 en los 23 huecos | `hueco_relevo_s` recompuesto vs. `t_inicio_tramo2 − t_fin_tramo1` del registro entregado |
| `S21_OE4_15` se corrió en `0e2b46c` | `procedencia.commit` del registro entregado |
| el compositor avisa de la limitación | `herramientas/componer_registro.py`, docstring de la procedencia |
| el analizador no necesita el campo | `herramientas/analizar_campana.py`, `hueco_de()` |
| la comprobación de contradicción | `analizar_campana.py`, `clasificar()`; pruebas en `prueba_analizar_campana.py`, «Coherencia del hueco de relevo» |
