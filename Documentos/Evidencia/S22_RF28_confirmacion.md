# RF-28 — Confirmación del usuario en la transición entre pisos

**Fecha:** 2026-09-10 (S22) · **Banco:** simulación · **Campaña:** `RF28_confirmacion` · **Commit:** `03c68c6`

Tres corridas encadenadas en la misma pila, con el mismo origen y destino —`piso1_representacion` →
`piso2_ieee`, condición B— y una sola variable: **qué hizo la persona en la etapa 7**. Las tres van
marcadas `es_piloto: true`: no son corridas de la campaña OE4 y no entran en ninguna tasa de éxito.

| | bag | lo que hizo la persona | resultado | RTF |
|---|---|---|---|---|
| A | `S22_RF28_AV3` | confirmó enseguida | COMPLETADA en 56,4 s, 1 relevo | 0,9942 (85,4 s sim / 85,9 s pared) |
| B | `S22_RF28_BV3` | esperó a la alerta y confirmó después | COMPLETADA en 122,6 s, 1 relevo | 0,9964 (136,1 s sim / 136,6 s pared) |
| C | `S22_RF28_CV3` | no confirmó nunca | FALLIDA a los 120 s | 0,9942 (179,5 s sim / 180,5 s pared) |

Registros: `Documentos/Evidencia/registros/S22_RF28_{A,B,C}V3.json`. Validan contra
`Documentos/esquema_registro_mision.json` las tres.

## 1. La línea de tiempo (paso 5 del plan)

`python3 herramientas/inspeccionar_etapas.py ~/tesis_evidencia/S22_RF28_<n>V3`

**A — confirmación inmediata**

```
     158.8  RECIBIDA               (vacio)  RF28_B_20260910_223807 Recibida la solicitud; asignando el robot.
     158.8  TRAMO_1                robot1   RF28_B_20260910_223807 El robot va hacia Representación. Espere alli.
     173.1  TRAMO_1                robot1   RF28_B_20260910_223807 Siga al robot hasta Escaleras.
     184.9  TRANSFERENCIA          robot2   RF28_B_20260910_223807 Suba al piso 2. Otro robot le espera en Escaleras.
     189.1  ESPERANDO_CONFIRMACION robot2   RF28_B_20260910_223807 ¿Ya esta en el piso 2? Confirmelo para continuar.
     201.0  TRAMO_2                robot2   RF28_B_20260910_223807 Siga al robot hasta IEEE.
     215.2  COMPLETADA             robot2   RF28_B_20260910_223807 Ha llegado a IEEE.
```

**B — con la alerta de los 60 s**

```
     258.8  TRANSFERENCIA          robot2   RF28_B_20260910_223937 Suba al piso 2. Otro robot le espera en Escaleras.
     277.0  ESPERANDO_CONFIRMACION robot2   RF28_B_20260910_223937 ¿Ya esta en el piso 2? Confirmelo para continuar.
     337.0  ESPERANDO_CONFIRMACION robot2   RF28_B_20260910_223937 Seguimos esperando su confirmacion. Quedan 60 segundos.
     350.9  TRAMO_2                robot2   RF28_B_20260910_223937 Siga al robot hasta IEEE.
     369.9  COMPLETADA             robot2   RF28_B_20260910_223937 Ha llegado a IEEE.
```

**C — sin confirmar**

```
     423.4  TRANSFERENCIA          robot2   RF28_B_20260910_224215 Suba al piso 2. Otro robot le espera en Escaleras.
     441.6  ESPERANDO_CONFIRMACION robot2   RF28_B_20260910_224215 ¿Ya esta en el piso 2? Confirmelo para continuar.
     501.6  ESPERANDO_CONFIRMACION robot2   RF28_B_20260910_224215 Seguimos esperando su confirmacion. Quedan 60 segundos.
     561.5  FALLIDA                robot2   RF28_B_20260910_224215 Mision detenida: el usuario no confirmo la llegada al piso 2 en 120 s
```

La etapa 7 queda **intercalada entre TRANSFERENCIA y TRAMO_2** en las tres, y su `robot` dice
`robot2` en todas las marcas, nunca `(vacio)`: con ese campo vacío la continuidad de RF-24 se
volvería falsa en toda misión entre niveles. Las tres salen con `continuidad` verdadera o no
aplicable, ninguna con `false`.

## 2. Las marcas de etapa 7 (paso 6 del plan)

`--etapa 7` cuenta **1** en A, **2** en B y **2** en C, y en B y C la separación entre la pregunta
y la alerta es de **60,0 s de simulación exactos** (277,0 → 337,0 y 441,6 → 501,6). Con un RTF de
0,994–0,996 eso son ~60,3 s de reloj de pared, que es lo que el `ALERTA_S` del coordinador promete.
El plazo total se cumple igual de bien en C: 441,6 → 561,5 = **119,9 s de simulación**.

## 3. La pulsación, medida en el bag

`/coordinacion/confirmacion_piso` se graba desde esta campaña, y es la única prueba de **cuándo
pulsó el usuario**; sin él, del bag solo se deduce la reacción del coordinador, no el acto.

| | mensajes en el tópico | contenido | pulsada tras la pregunta | TRAMO_2 tras la pulsación |
|---|---|---|---|---|
| A | 1 | `RF28_B_20260910_223807` | 11,9 s | **0,00 s** |
| B | 1 | `RF28_B_20260910_223937` | 73,8 s | **0,10 s** |
| C | 0 | — | — | — |

El `mision_id` del mensaje coincide con el de la misión en vuelo, de modo que la confirmación no
puede atribuirse a otra corrida de la misma sesión. La reanudación es inmediata: **≤ 0,1 s** entre
la pulsación y la marca de TRAMO_2. Ese número es el que quedó roto hasta el 2026-09-10 y el que
obligó a la corrección descrita en la §4.

## 4. Lo que hubo que arreglar antes de esta tanda

Tres defectos, encontrados en la tanda `V2` del mismo día y corregidos en `03c68c6`:

1. **El botón de confirmar no hacía nada** hasta recargar la página. No era la interfaz:
   `rosbridge` con `send_action_goals_in_new_thread:=false` —su valor por omisión— atiende la meta
   de acción en el **mismo hilo con el que lee el WebSocket**, así que el `publish` del botón queda
   encolado hasta que la misión termina. La salida sigue fluyendo por el ejecutor de ROS, por eso
   el panel se veía sano. Medido: con el valor por omisión la confirmación llegó **17 s tarde**,
   2 ms después de que la misión hubiera muerto; con la bandera, a los 3,06 s. La bandera es ahora
   obligatoria en la §4.1 del `RUNBOOK_CAMPANA.md`.
2. **Una misión muerta por plazo agotado dejaba la consola muda.** El desenlace solo lo anotaba la
   salida de éxito de `_ejecutar`. Se movió a `_cerrar_registro`, el único punto por el que pasan
   todas las salidas. En la corrida C el coordinador ya imprime
   `Mision terminada SIN exito tras 158.0 s: el usuario no confirmo la llegada al piso 2 en 120 s`.
3. **El bloque del botón se veía siempre**, incluso con `hidden`. `#acciones-confirmar` hereda
   `display: grid` de `.acciones`, y una declaración del origen de autor gana a la regla
   `[hidden]{display:none}` de la hoja del navegador. Se añadió `[hidden] { display: none !important }`
   en `estilo.css`.

El banco `interfaz_web/prueba_confirmacion_piso.js` pasó de 18 a **21 comprobaciones**: una guarda
estática del CSS y una sección que pulsa el botón **con una meta en vuelo**, que es la única
situación en la que el defecto 1 se manifiesta y la que faltaba.

## 5. Anomalías, dichas enteras

**La corrida C no cumple el criterio 1 del §8 del runbook.** `condicion_inicial.json` de `CV3` da
`robot2: error_localizacion_m = 0,1863`, por encima de la tolerancia de 0,15 m, y `grabar_mision.sh`
avisó al terminar: *«AMCL no sabe donde esta el robot. Candidata a descarte»*. No se descarta ni se
repite, por dos razones que conviene separar:

- **No es una corrida de campaña.** Va con `es_piloto: true` y campaña `RF28_confirmacion`; el §8
  del protocolo gobierna el denominador de la tasa de éxito de OE4, y esta corrida no está en él.
- **Su desenlace no depende de la localización.** C falla porque nadie confirmó: el temporizador
  vive en el coordinador, la marca de FALLIDA se emite a los 119,9 s de la pregunta, y el robot no
  llegó a navegar el tramo 2. Que AMCL tuviera 3,6 cm de error de más no toca ninguno de esos
  hechos.

Lo que **sí** hay que retener: si esta corrida perteneciera a OE4, el criterio 1 la haría candidata
a descarte y no serviría para tasa de éxito. Las tres se corrieron encadenadas sobre la misma pila
—por eso `desviacion_m` llega a 7,13 m en robot2, que es normal y no es motivo de descarte—, y el
error de localización se degradó a lo largo de la sesión: 0,043 m en A, 0,080 m en B, 0,186 m en C.
**Para la campaña OE4 hay que levantar la pila limpia entre corridas**, o al menos vigilar ese
número, porque encadenar tres misiones ya basta para salirse de la tolerancia.

**`t_inicio_tramo2` no mide la espera del usuario.** En B vale 259,0 s mientras que el TRAMO_2 real
arrancó a 350,9 s. No es un error: esa marca es *el primer movimiento sostenido del segundo robot
después de la transferencia*, y el tramo de transferencia ya es de robot2 —conduce hasta su escalera
mientras el usuario sube—. Sigue significando lo mismo que antes de RF-28. Pero **la diferencia
`t_inicio_tramo2 − t_fin_tramo1` no es el tiempo que el usuario tardó en subir**, y con RF-28 la
tentación de leerla así es nueva. Ese tiempo está en la §3 de este documento y en el bag, no en esa
resta.

**El error de llegada de C es 6,52 m** y su `exito` es `False` con tres motivos encadenados. Es lo
correcto: la misión no llegó, así que el robot está donde lo dejó la transferencia. `continuidad`
sale `None` con motivo *«ventana abierta: falta t_completada»*, igual que en `S21_OE4_27`.

## 6. Pendiente

Guardar en `Documentos/Evidencia/` las capturas del panel en la etapa 7 y en la alerta de los 60 s.
La captura de la corrida C —consola del coordinador y página web tras agotarse el plazo— existe pero
todavía no está en el repositorio.
