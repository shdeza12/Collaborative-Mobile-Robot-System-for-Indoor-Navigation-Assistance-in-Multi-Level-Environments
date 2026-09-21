# El conjunto de datos de OE4, consolidado: 30 corridas que regeneran sus propias métricas

*Tarea 1.4 del `MAPA_TRABAJO_RESTANTE.md` y criterio de cierre de S24. 2026-09-21.
Trabajo de escritorio: no se tocó ningún vehículo ni se repitió ninguna corrida.*

## 0. Qué significaba «consolidar», y qué se comprobó

El cronograma de S24 pedía «consolidar y versionar el conjunto de datos». Versionado ya estaba;
lo que no se había comprobado nunca es lo que hace que un conjunto de datos sirva: **que un
tercero, con solo el repositorio, llegue de los registros a las cifras publicadas**.

La cadena tiene dos tramos y hasta hoy solo uno estaba verificado:

| Tramo | Qué lo verifica | Estado |
|---|---|---|
| bag → registro | `componer_registro.py` | ✅ verificado el 2026-09-16, `S23_reproducibilidad_de_los_registros.md`: 44 de 44 sin mover un veredicto |
| registro → métricas | `analizar_campana.py` | ✅ **verificado hoy**, y encontró un hueco |

## 1. El inventario

51 ficheros en [`registros/`](registros/). De ellos, **46 son registros de misión**; los otros
cinco son bancos de asignación y el registro de red de RF-15, que tienen otra forma.

| Campaña | Oficiales | Pilotos |
|---|---|---|
| **`OE4_simulacion`** | **30** | 6 |
| `RF28_confirmacion` | — | 3 |
| `S20_pilotaje_asignacion` | — | 2 |
| `S20_verificacion_RECIBIDA` | — | 1 |
| `S21_relevo_demostracion` | — | 1 |
| `S22_verificacion_RF20` | 1 | — |
| `S23_RF29` | — | 2 |

**Las 30 corridas de OE4 están completas y son las de siempre.** Los pilotos quedan fuera del
agregado salvo que se pidan con `--incluir-pilotos`, que es lo que impide inflar la tasa de éxito
con ensayos.

Los registros conviven en **tres versiones de esquema** —1.0.0 (3), 1.1.0 (41), 1.2.0 (2)— porque
en S23 se decidió, con evidencia, **no recomponerlos**: recomponer reescribe
`procedencia.commit` y sustituye el commit con el que se grabó por el commit del día, que es
perder la trazabilidad a cambio de uniformidad cosmética. La decisión se mantiene.

## 2. El hueco que encontró la comprobación

Regenerar las métricas desde los 30 registros y compararlas con el artefacto versionado
`S21_metricas_campana_oe4.json` da:

| Comprobación | Resultado |
|---|---|
| Bloques publicados que cambian de valor | **0 de 13** |
| Bloques idénticos campo a campo | **13 de 13** |
| Bloques que la herramienta produce y el artefacto no tiene | **1: `rnf01`** |
| Veredicto | `VALIDA`, sin alertas |

**Ninguna cifra publicada se mueve.** Lo que faltaba es un bloque entero: la constancia de `z` de
RNF-01, que `analizar_campana.py` no calculaba cuando se congeló el JSON de S21 y sí calcula hoy.

El detalle incómodo es que **RNF-01 ya se citaba en dos documentos** con cifras que el artefacto
versionado no contenía:

| Documento | Lo que afirma | El bloque `rnf01` regenerado |
|---|---|---|
| `REQUISITOS.md` | 60 medidas, máximo 0,0070 m | `n = 60`, `max = 0,0070134 m` |
| `RESULTADOS_OE4_SIMULACION.md` | 60 parejas, mediana 7,012 mm, máx 7,013 mm, umbral 0,05 m | mediana `0,0070119`, máx `0,0070134`, `umbral_m = 0,05` |

Coinciden exactamente. No había error en el texto: había una **afirmación sin artefacto detrás**.
Un lector que descargara el repositorio y abriera el JSON no encontraba los números que el
capítulo de resultados le citaba. Eso es precisamente lo que una consolidación existe para
detectar.

## 3. Lo que se hizo

Se añade `S24_metricas_campana_oe4.json`, regenerado con la herramienta de hoy sobre los mismos 30
registros.

**`S21_metricas_campana_oe4.json` no se toca.** Es un artefacto entregado y se queda como se
entregó; el nuevo no lo corrige, lo completa —13 bloques bit a bit iguales más el que faltaba—.
Sustituirlo habría borrado la prueba de que nada cambió.

El comando que lo reproduce, desde la raíz del repositorio y sin ROS, sin `colcon` y sin bags:

```
python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana OE4_simulacion --json /tmp/comprobacion.json
```

## 4. Lo que el repositorio NO trae, dicho con todas las letras

**Los bags no están versionados.** Los 2,2 GB y 33 directorios de bag viven en `~/tesis_evidencia/`
en la máquina de trabajo, fuera del repositorio y sin copia pública.

La consecuencia hay que asumirla sin adornos: un tercero puede **reproducir el tramo
registro → métricas** entero, y no puede reproducir el tramo **bag → registro**. Ese tramo queda
avalado por la comprobación de S23 y por el `sha256` del catálogo de puntos que cada registro
guarda en `procedencia`, no por la posibilidad de rehacerlo. Es una limitación real del conjunto
de datos y se declara aquí para que no haya que descubrirla en la sustentación.

## 5. Qué queda cerrado

**La tarea 1.4 queda cerrada.** El conjunto de datos de OE4 está versionado, inventariado, y es
**autorregenerable en su tramo público**: los 30 registros producen, con una orden y sin
dependencias, las métricas que el capítulo de resultados cita —ahora incluidas las de RNF-01—.

Queda anotado para el Bloque 5: cuando la campaña física produzca sus registros, la comparación
simulación ↔ físico tiene que correr **el mismo analizador sobre los dos conjuntos**, para que la
diferencia mida el entorno y no la instrumentación.

## 6. Trazabilidad

| Afirmación | Fuente |
|---|---|
| 51 ficheros, 46 registros de misión, 30 oficiales de OE4 | Recuento sobre `Documentos/Evidencia/registros/` |
| Tres versiones de esquema conviviendo (1.0.0, 1.1.0, 1.2.0) | Campo `esquema_version` de cada registro |
| 13 de 13 bloques idénticos, 0 cambios de valor | Comparación `S21_metricas_campana_oe4.json` ↔ regenerado |
| El bloque `rnf01` falta en el artefacto de S21 | Diferencia de claves entre ambos JSON |
| Las cifras de RNF-01 citadas coinciden con el bloque | `REQUISITOS.md`, `RESULTADOS_OE4_SIMULACION.md` y el JSON nuevo |
| Veredicto `VALIDA`, sin alertas, 36 leídos y 6 pilotos | Salida de `analizar_campana.py`, 2026-09-21 |
| El tramo bag → registro no es reproducible desde el repositorio | Los bags viven fuera, `S23_reproducibilidad_de_los_registros.md` |
