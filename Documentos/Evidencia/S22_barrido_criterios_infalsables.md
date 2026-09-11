# Barrido del protocolo: qué criterios no pueden fallar

**Fecha:** 2026-09-11 · **Tarea 3 de [`PLAN_S22.md`](../PLAN_S22.md)** · pendiente declarado el 2026-09-05

## 0. Por qué se hace este barrido

Dos veces en tres semanas apareció el mismo defecto por caminos distintos: **una comprobación
escrita de forma que no puede dar «no»**.

- **RF-22, el tiempo de asignación.** Hasta el 29-ago el coordinador fijaba `etapa` y
  `robot_activo` en la misma publicación, así que la resta de las dos marcas valía cero se
  ejecutara lo que se ejecutara. No era una medida del sistema: era una medida de la definición
  (§3.2.1 del protocolo).
- **La puerta M1 de la campaña.** Aceptaba la corrida comprobando cosas que el propio arranque
  garantizaba.

Un criterio que no puede fallar no es una comprobación laxa: es **una comprobación ausente
disfrazada de verde**. Y en una campaña de 30 corridas se lee exactamente igual que un sistema
que funciona.

Este documento recorre **cada §3.x y el §4** del
[`PROTOCOLO_EXPERIMENTAL.md`](../PROTOCOLO_EXPERIMENTAL.md) y responde una sola pregunta por
sección: **¿existe alguna ejecución del sistema que haga que este criterio dé «no»?** Si la
respuesta es no, el criterio no está midiendo nada.

Todo lo que sigue está medido sobre los 30 registros de la campaña de OE4
(`Documentos/Evidencia/registros/S21_OE4_*.json`) y sobre el bag `S21_OE4_09`, más la lectura del
código que los produce. Ningún resultado de la campaña cambia: lo que se revisa es el método, no
los datos.

## 1. Tabla de resultados

| § | Criterio | ¿Puede fallar? | Evidencia |
|---|---|---|---|
| 3.1 | RF-21, tiempo de respuesta | **Apenas** | 4 valores posibles observados, todos múltiplos del tick |
| 3.2 | RF-22, cota `< 100 ms` | **Sí** | ya saneado el 29-ago; la cota se sostuvo 30/30 |
| 3.3 c1 | posición ≤ 0,25 m | **Sí, y falló** | 4 misiones fuera: 0,295 / 0,284 / 0,311 / 0,347 m |
| 3.3 c2 | `COMPLETADA` sin `FALLIDA` | **Sí, y falló** | las mismas 4, nunca por separado de c1 |
| 3.3 c3 | `num_relevos == 1` | **En la práctica no** | 15/15 en verde, incluida la misión que falló |
| 3.4 | RF-24, binario de continuidad | **NO, por construcción** | 0 incumplimientos de 0 posibles |
| 3.4 | `hueco` del relevo | mide, pero no se reporta | ausente de `descriptivas`; vale 1–2 ticks |
| 3.4 | RNF-01, constancia de `z` | **NO: no hay umbral** | 7,012 mm, 3690× la referencia que el propio § cita |
| 4 | el rumbo se reporta siempre | **no se reporta** | `error_rumbo_rad` es `null` en 30 de 30 |

Dos hallazgos son de la misma familia que RF-22 —criterios imposibles de incumplir— y dos son
promesas del protocolo que la instrumentación no cumple. Se detallan por orden de gravedad.

## 2. §3.4 — RF-24 no puede dar «no», y es la variable de respuesta principal

### 2.1 Qué dice el criterio

> La continuidad **se cumple** si durante todo el intervalo `[t_robot_activo, t_completada]` el
> campo `etapa` de `estado_mision` nunca vale `INACTIVA`, y `robot_activo` nunca queda vacío.

### 2.2 Quién produce esos dos valores

Los únicos dos productores están en `coordinacion/coordinador.py`, y **los dos quedan fuera de la
ventana por delante**:

| Valor | Dónde se produce | Cuándo, respecto de la ventana |
|---|---|---|
| `etapa = INACTIVA` | `coordinador.py:116`, en el **constructor** del nodo | antes de la primera misión, y **nunca se restaura** |
| `robot_activo` vacío | `_marcar(RECIBIDA, "", …)` y `_marcar(FALLIDA, "", …)` del fallo de planificación | antes de `t_robot_activo`, que es donde la ventana **abre** |

`INACTIVA` aparece exactamente dos veces en el fichero: en el `import` y en esa línea del
constructor. **El coordinador no vuelve a publicarla nunca**, ni al terminar una misión. Dentro
del bucle de tramos, cada `_marcar` recibe `tramo.robot` o `tramos[-1].robot`, ambos llenos; la
espera de RF-28 publica `ESPERANDO_CONFIRMACION` también con el robot lleno; y una cancelación
sale por `goal_handle.canceled()` sin marcar nada, dejando el último estado intacto.

**No existe ruta de ejecución que publique `INACTIVA` o un `robot_activo` vacío entre `TRAMO_1` y
`COMPLETADA`.**

### 2.3 Comprobado sobre el bag, no solo leído

Bag `S21_OE4_09`, tópico `/coordinacion/estado_mision`, 144 mensajes:

| etapa | 0 `INACTIVA` | 1 `TRAMO_1` | 2 `TRANSFERENCIA` | 3 `TRAMO_2` | 4 `COMPLETADA` | 6 `RECIBIDA` |
|---|---|---|---|---|---|---|
| mensajes | 6 | 67 | 33 | 32 | 5 | 1 |

Los **7 mensajes con `robot_activo` vacío** son los 6 `INACTIVA` —de 89,0 a 94,0 s— más el
`RECIBIDA`. La ventana evaluada de esta misión es **[94,7 · 222,6]**. Los siete caen antes de que
abra. Al final la etapa se queda en `COMPLETADA` y ya no cambia.

En las 30 misiones de la campaña: **`instantes_inactiva` suma 0 y `instantes_sin_agente` suma 0**.
Cero incumplimientos de cero posibles.

### 2.4 La enmienda del 31-ago cambió una degeneración por la contraria

La versión congelada el 22-ago abría la ventana en `t_solicitud`, y por eso era **vacuamente
falsa**: el estado `RECIBIDA` vive ahí con el agente vacío a propósito, así que RF-24 habría dado
0 % para toda misión, incluida una perfecta. La enmienda movió el inicio a `t_robot_activo`.

Eso corrigió el signo, pero no el problema: al mover el inicio justo detrás del único productor de
valores vacíos, el criterio pasó de no poder dar «sí» a **no poder dar «no»**. La enmienda se
argumentó con el mismo párrafo que aquí se aplica —«una definición que da siempre el mismo número
no está midiendo el sistema, está midiendo la definición»— y aun así el resultado volvió a ser un
número fijo, esta vez favorable. Que el número fijo sea el bueno es justamente lo que hace que no
se note.

### 2.5 Además, el §3.4 afirma algo que el código no hace

> El cierre es `t_completada` **inclusive**. Después el coordinador vuelve a `INACTIVA`, que es su
> reposo normal, y contarlo sería el mismo error por el otro extremo.

El coordinador **no vuelve a `INACTIVA`**. Se queda en `COMPLETADA` hasta la siguiente solicitud.
El razonamiento del cierre por el extremo derecho se apoya, pues, en un comportamiento inexistente.
La conclusión —cerrar en `t_completada`— sigue siendo la correcta por otra razón: después de
`COMPLETADA` no hay misión que vigilar. Pero el motivo escrito hay que corregirlo.

### 2.6 Y el `hueco`, que debía rescatarlo, ni se reporta ni discrimina

El propio §3.4 anticipa la objeción:

> `hueco` se reporta aunque la continuidad se cumpla: un relevo correcto pero de 40 s es un mal
> resultado que la variable binaria escondería.

Dos problemas:

1. **No está en `descriptivas` de ningún registro.** Se calcula —`registrador.py:186` lo deja en
   `marcas` como `hueco_relevo_s`, y `analizar_campana.py:159` lo agrega—, pero el bloque que un
   lector del registro consulta no lo trae.
2. **Vale uno o dos ticks.** En las 15 misiones entre niveles: **0,1 s en 10 y 0,2 s en 5**.
   Mínimo 0,100, mediana 0,100, máximo 0,200. El relevo de 40 s que la binaria escondería no
   existe; lo que hay es un relevo que el reloj no resuelve.

Así que RF-24 se apoya hoy en **una binaria que no puede fallar más una continua que está en el
suelo de `/clock` y no se publica donde se lee**.

### 2.7 Qué hacer, y qué no

**No se toca la campaña.** Los 30 registros valen, la tasa de éxito vale y el veredicto `VALIDA`
vale: RF-24 no entra en el criterio de éxito (el §3.4 lo dice expresamente) y la binaria en verde
no infló ningún resultado, porque no decidió ninguno.

Lo que hay que corregir es **cómo se reporta RF-24 en el documento de grado**, y admite una
redacción honesta sin repetir corridas:

- Declarar la binaria por lo que es: **un invariante estructural**, no una medida. Se sostiene
  porque el coordinador no tiene ninguna ruta que suelte la misión, y eso es un resultado de
  diseño verificable leyendo el código —que es como se ha verificado aquí—, no un resultado
  experimental de 30 corridas.
- Poner el `hueco` como la evidencia cuantitativa de RF-24, con su límite dicho: **≤ 200 ms, es
  decir ≤ 2 ticks de `/clock`**, que es la misma clase de afirmación —una cota superior— que el
  §3.2.2 ya acepta para RF-22, y por la misma razón.
- Añadir `hueco_relevo_s` a `descriptivas` para que el registro se lea solo.

La alternativa —inventar una ruta de fallo para que la binaria pueda dar «no»— sería instrumentar
el experimento para que salga interesante. No.

## 3. §4 y §3.3 — el rumbo se argumenta como «medido y reportado», y no se reporta

El §3.3 dice, y el §4 entero se apoya en ello:

> **El rumbo de llegada NO es criterio de éxito.** Se mide y se reporta siempre, como variable
> descriptiva, pero no decide.

**`error_rumbo_rad` vale `null` en los 30 registros.** El motivo está escrito en
`componer_registro.py:879`:

> *Presente y sin llenar en 1.0.0 a proposito: para calcularlo hace falta el yaw del punto del
> catalogo, y el §3.7 dice que el rumbo NO decide mientras R12 siga abierto. Llenarlo despues es
> una version menor.*

La condición que lo justificaba **dejó de valer hoy**: R12 quedó cerrado el 2026-09-11. Y el dato
se puede calcular desde los bags conservados sin repetir una sola corrida, porque los dos
ingredientes ya están: la pose de llegada —que es la misma con la que se calcula
`error_posicion_m`— y el `yaw` del punto de `puntos_interes.yaml`.

**Hacerlo no viola el §6.3.** Esa regla prohíbe cambiar el análisis después de ver los datos; el
rumbo es una variable descriptiva que no entra en ningún criterio, así que rellenarla no puede
mover ningún veredicto. Se rellena, o se borra la frase del §3.3 que promete reportarlo. Lo que no
se puede es sostener un argumento de diseño experimental sobre un campo vacío.

## 4. §3.4 — RNF-01 se «verifica» sin umbral, y ya se pasó por alto un valor 3690 veces mayor

> **RNF-01 se verifica en la misma corrida:** la coordenada `z` de cada agente debe permanecer
> constante durante toda la misión. […] Se comprueba con la desviación de `z` en `/odom`, que en
> S18 fue de 1,9 µm.

«Constante» no es un criterio: no hay número contra el que comparar, y
`analizar_campana.py` ni menciona RNF-01, así que **nada evalúa este campo**. Solo se escribe.

Lo que se escribió en la campaña, sobre las 60 parejas robot–misión:

| | valor |
|---|---|
| mínimo | 7,010 mm |
| mediana | 7,012 mm |
| máximo | 7,013 mm |
| referencia citada en el § (S18) | 0,0019 mm |
| factor | **≈ 3690×** |

**No es una violación de RNF-01**, y conviene decirlo antes que nada: cambiar de piso son metros,
no milímetros, y la dispersión entre las 60 medidas es de **3 µm**, o sea que los 7 mm son un
**desplazamiento fijo**, no una deriva —compatible con la altura de reposo del vehículo sobre la
suspensión simulada, no con un robot subiendo una escalera—.

El hallazgo es el otro: **una cifra 3690 veces mayor que la que el propio protocolo cita como
referencia atravesó 30 corridas sin que nada la señalara**, porque el criterio no tiene umbral ni
evaluador. Si algún día `z` sí se moviera, este mecanismo tampoco lo diría.

Corrección propuesta, barata: fijar el umbral en el documento —**`σ(z) < 0,05 m` por robot y por
misión**, dos órdenes de magnitud por debajo de cualquier cambio de nivel real y dos por encima
del valor observado— y hacer que `analizar_campana.py` lo agregue y lo reporte como las demás.

## 5. §3.1 — RF-21 mide en cuatro escalones de reloj

El tiempo de respuesta **sí varía**, que es más de lo que se podía decir de RF-22. Pero su rango
entero son cuatro valores:

| t_respuesta | 0,1 s | 0,2 s | 0,3 s | 0,4 s |
|---|---|---|---|---|
| misiones | 10 | 15 | 4 | 1 |

Todos múltiplos exactos de 100 ms, que es el tick de `/clock` (§3.2.1). La resolución del
instrumento es del orden de la magnitud medida: entre 25 % y 100 % del valor. La mediana de 0,2 s
significa «uno o dos ticks», no «doscientos milisegundos».

No es el caso de RF-22 —aquí sí hay señal, y la cota que importa para un usuario, «el robot
arranca en menos de medio segundo», se sostiene con holgura—, pero **reportar media y desviación
sugeriría una precisión que el reloj no da**. Se reporta la distribución de escalones, o se
reporta como cota.

**Y hay una frase del §3.1 que es falsa en la base de tiempo del bag:**

> Las tres muestras consecutivas están para no disparar con un pico de ruido; a 50 Hz cuestan
> 60 ms, muy por debajo de la resolución que interesa.

Con `/clock` a 10 Hz, `ros2 bag record --use-sim-time` sella las tres muestras con el mismo tick o
con dos: **cuestan 0 ms o 100 ms**, nunca 60. La conclusión —que el filtro antirruido no estropea
la medida— sigue siendo cierta, porque un coste de 0 o 100 ms sigue estando dentro de un escalón.
Pero el número hay que corregirlo.

## 6. §3.3 c3 — el relevo comprueba el plan, no la ejecución

`c3 = (num_relevos == 1)` para condición B, y `num_relevos` sale de `res.num_relevos = relevos`,
que es **lo que devolvió `planificar()`**, no lo que hizo el sistema. Con dos pisos, un par entre
niveles siempre planifica exactamente un relevo. Luego:

- si la planificación tuvo éxito, **c3 es verdadero siempre**;
- si falló, `c2` ya es falso porque se publicó `FALLIDA`.

**c3 no puede cambiar el veredicto.** Medido: verdadero en las 15 misiones de condición B,
**incluida la 27, que falló** por posición. Es una comprobación del planificador, que la prueba
exhaustiva de S20 ya cubrió sobre las 240 combinaciones.

No es grave y no hace falta quitarlo —documenta la intención del criterio de éxito—, pero conviene
decir en el informe que c3 **verifica el plan y no la ejecución**, para no presentarlo como
evidencia de que el relevo ocurrió. La evidencia de que ocurrió es el `hueco` y son las marcas
`t_fin_tramo1` / `t_inicio_tramo2`.

## 7. Lo que sí está sano

Conviene dejarlo escrito, porque un barrido que solo encuentra defectos no es creíble:

- **§3.3 c1** es el criterio con poder discriminante real, y lo ejerció: **4 de 30 misiones
  fallaron** por posición, a 0,295 / 0,284 / 0,311 / 0,347 m contra los 0,25 m. Es una distancia
  medida contra `/odom`, no un tiempo contra `/clock`, y por eso no sufre el problema de
  cuantización que afecta al resto.
- **§3.3 c2** puede fallar y falló en esas mismas 4. Que nunca haya fallado *sin* c1 es
  consecuencia razonable —si el robot no llega, ni completa ni queda dentro de tolerancia—, no un
  defecto de la definición.
- **§3.2** es hoy el § mejor argumentado del protocolo, precisamente porque ya pasó por esto: la
  cota `< 100 ms` **puede** fallar, y el propio § dice qué hacer si falla —«eso sí es un dato, y de
  los graves»—. Se sostuvo en las 30.

## 8. Resumen de acciones, ordenadas por coste

| # | Acción | Toca | Coste |
|---|---|---|---|
| 1 | Reescribir el §3.4: la binaria es invariante estructural; el `hueco` es la evidencia, como cota `≤ 200 ms` | `PROTOCOLO_EXPERIMENTAL.md` | redacción |
| 2 | Corregir en el §3.4 la frase «después el coordinador vuelve a `INACTIVA`» | `PROTOCOLO_EXPERIMENTAL.md` | una frase |
| 3 | Corregir en el §3.1 «a 50 Hz cuestan 60 ms» y reportar RF-21 por escalones | `PROTOCOLO_EXPERIMENTAL.md` | redacción |
| 4 | Decir en el §3.3 que c3 verifica el plan, no la ejecución | `PROTOCOLO_EXPERIMENTAL.md` | una frase |
| 5 | Fijar el umbral de RNF-01 en `σ(z) < 0,05 m` y agregarlo en el analizador | `PROTOCOLO_EXPERIMENTAL.md`, `analizar_campana.py` | pequeño |
| 6 | Añadir `hueco_relevo_s` a `descriptivas` | `componer_registro.py`, `ESQUEMA_REGISTRO_MISION.md` | pequeño |
| 7 | Rellenar `error_rumbo_rad` desde los bags conservados, o borrar la promesa del §3.3 | `componer_registro.py` | mediano |

Las cuatro primeras son de documento y no tocan ni un dato. Las tres últimas tocan herramientas y
obligan a recomponer registros desde los bags conservados; a trece días del congelamiento eso se
decide con el cronograma delante, no aquí.

**Ninguna de las siete cambia un veredicto de la campaña de OE4.**

## 9. Trazabilidad

| Afirmación | De dónde sale |
|---|---|
| ventana y ausencia de incumplimientos | `veredicto.continuidad` de los 30 `S21_OE4_*.json` |
| histograma de etapas y mensajes sin agente | bag `S21_OE4_09`, `/coordinacion/estado_mision`, 144 mensajes |
| `INACTIVA` solo en el constructor | `coordinacion/coordinador.py:116`, único uso fuera del `import` |
| c3 sale del planificador | `coordinador.py`, `res.num_relevos = relevos`; `componer_registro.py:194` |
| t_respuesta y hueco | `analizar_campana.py:t_respuesta_de`, `hueco_de` sobre los 30 registros |
| desviación de `z` | `descriptivas.desviacion_z_m`, 60 parejas robot–misión |
| `error_rumbo_rad` vacío | `descriptivas.error_rumbo_rad`, `null` en 30 de 30; motivo en `componer_registro.py:879` |
