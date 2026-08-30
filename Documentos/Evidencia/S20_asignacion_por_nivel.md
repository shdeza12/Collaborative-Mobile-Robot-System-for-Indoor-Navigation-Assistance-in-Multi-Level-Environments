# Asignación del agente por nivel — primera ejecución completa de RF-25

**Semana 20 · 2026-08-29.** Primer uso de extremo a extremo de la cadena de RF-25: una solicitud
origen–destino entra por la acción `GuiarUsuario`, el coordinador elige agente, se graba un bag por
misión y `herramientas/componer_registro.py` produce un registro JSON validado contra el esquema
congelado.

Cubre la **mitad de software** del criterio de cierre de S20: *«una solicitud origen–destino produce
la asignación del agente correcto y deja registrados los dos tiempos en un log estructurado»*. La
mitad de hardware está en [`S20_frente_b_hardware.md`](S20_frente_b_hardware.md).

Registros: [`registros/S20_A_M1.json`](registros/S20_A_M1.json) y
[`registros/S20_A_M2.json`](registros/S20_A_M2.json).

---

## 1. Diseño: dos misiones, y la segunda es el control

Una sola misión exitosa **no demuestra que la asignación discrimine**. Si solo se lanza una petición
del piso 2 y el coordinador responde `robot2`, no se puede distinguir entre *«eligió bien»* y
*«siempre responde lo mismo»*.

Por eso se lanzaron **dos** peticiones en la misma sesión, contra el mismo nodo, con destinos en
niveles distintos:

| | Origen → destino | Nivel | Agente asignado |
|---|---|---|---|
| **M1** | `piso2_ieee` → `piso2_lab_313` | 2 | **`robot2`** |
| **M2** | `piso1_representacion` → `piso1_etm2` | 1 | **`robot1`** |

Las dos asignaciones son correctas y son **distintas**. Eso es lo que convierte a M1 en evidencia.

Esta comprobación solo es posible desde el 24-ago, cuando `puntos_interes.yaml` dejó de tener sus
quince destinos todos en `nivel: 1`. Con un solo nivel poblado, la asignación habría acertado por no
tener alternativa.

## 2. Resultado de M1 — éxito medido contra `/odom`

| Magnitud | Valor |
|---|---|
| Veredicto | `exito: true` |
| Error de llegada contra `/odom` | **0,036 m** (tolerancia 0,25 m) |
| `t_respuesta` (solicitud → primer movimiento) | **0,1 s** |
| Tiempo total | 38,9 s |
| Distancia recorrida | 16,55 m |
| Cúspides | 8 |
| Deriva `map → odom` | 0,457 m |
| Desviación en z | 7,0 mm |

El veredicto **no** usa el `SUCCEEDED` de Nav2. Se calcula contra `/odom`, como exige el §3.3 del
protocolo, por el defecto medido el 21-ago: Nav2 devolvió `SUCCEEDED` estando a 0,296 m del destino
porque mide contra la pose de AMCL y no contra la verdad del simulador.

**Los 0,457 m de deriva `map → odom` merecen atención.** Es la corrección acumulada que AMCL aplica
sobre la odometría; no invalida el resultado —el veredicto se toma contra `/odom`— pero es un orden
de magnitud mayor que el error de llegada, y conviene vigilarlo en la campaña.

## 3. Resultado de M2 — fallo limpio, y es información

`robot1` fue asignado correctamente, pero **no estaba alcanzable**: vive en `ROS_DOMAIN_ID=0` y la
sesión corría en el 2. El servidor de acción nunca apareció, la misión abortó a los 20 s y el
vehículo recorrió 0,023 m, es decir, no se movió.

`exito: false`, con motivo *«la misión no llegó a COMPLETADA sin pasar por FALLIDA»*.

**No es una corrida perdida.** Es el control de la §1 y, además, es la primera manifestación
*medida* del bloqueo de dominios que gobierna S21–S23.

## 4. Salud del banco

RTF = **0,999**, con RNF-06 exigiendo ≥ 0,99. Ninguna de las dos corridas se descarta.

**Procedencia del dato, que hay que decir:** el RTF es **posterior** a las misiones. Se midió sobre
el mismo proceso `gzserver` —nunca reiniciado entre las misiones y la medición— y **bajo carga real
de navegación**, no con la simulación ociosa: se envió a `robot2` a un destino a 6,3 m verificados
contra `amcl_pose`, y `/clock` avanzó 24,10 s en 24,12 s de reloj de pared.

Se midió después porque **el bag no lo puede dar**: con `--use-sim-time`, `ros2 bag record` sella en
tiempo de simulación también `starting_time` y `duration`, así que la razón sim/pared vale 1 por
construcción. El esquema no tiene campo para anotar esta procedencia, y por eso queda escrita aquí.

Corregido para el futuro: `grabar_mision.sh` toma ahora una marca de `/clock` antes de grabar y otra
al cerrar, y escribe `rtf.json` junto al bag.

## 5. Las dos misiones van marcadas como piloto

`es_piloto: true` en ambos registros. Son el primer ejercicio de la cadena, no corridas de campaña, y
el §7 del protocolo excluye el pilotaje del análisis. Marcarlo es lo que impide que en octubre se
mezclen con los datos buenos.

## 6. Cuatro defectos que esta corrida destapó

Es lo que un piloto tiene que producir. Los cuatro se encontraron *porque* se ejecutó, no leyendo
código.

### 6.1 El *tiempo de asignación* es estructuralmente inmedible — el más grave

`t_solicitud` y `t_robot_activo` salieron **idénticos** (189,6 s en M1). No es falta de resolución:
`_marcar()` en `coordinador.py` fija `etapa` y `robot_activo` en la misma llamada y publica **una**
vez, así que **nunca existe un estado intermedio** entre «llegó la solicitud» y «ya hay agente
elegido».

Consecuencia: el *tiempo de asignación*, que es **una de las cuatro métricas de OE4**, valdrá
exactamente cero en las 30 corridas de la campaña, se ejecute lo que se ejecute. Un cero no es una
medida.

La corrección es acotada —publicar el estado al recibir la solicitud, antes de planificar, y otra vez
al tener el agente— pero hay que hacerla **antes** de S24, no después.

### 6.2 `distancia_restante` sale `NaN`

En la realimentación de M2, con el robot sin publicar odometría, el campo salió `.nan`. Ese campo
alimenta la HRI de S22, donde se le mostraría al usuario un «NaN». Es un defecto de OE3 detectado
antes de que OE3 exista.

### 6.3 El mensaje de fallo omite la causa más frecuente

El texto apunta al desajuste Humble/Jazzy, pero no menciona *«`robot1` no estaba lanzado»*, que es lo
que pasó y es lo que pasará casi siempre.

### 6.4 El bag de una misión arrastra la cola de la anterior

El coordinador sigue publicando el estado terminal de la misión previa hasta que llega una nueva
solicitud, así que el bag de M2 contenía 11 mensajes de M1, todos en `COMPLETADA`. Como van
**primeros** en el tiempo, sin filtrar se llevaban por delante `origen`, `destino` y `t_solicitud`
del registro de M2: habría validado contra el esquema **siendo falso**.

Lo detectó la guarda que se negó a componer. `componer_registro.py` distingue ahora misión en curso
de residuo terminal; dos misiones **en curso** siguen siendo un procedimiento roto.

## 7. Nota de reproducibilidad

Los dos registros llevan `repositorio_limpio: false`, y es cierto: las herramientas se corrigieron
el mismo día. Conviene saber que `procedencia` se calcula **al componer**, no al grabar, así que ese
campo describe el árbol en el momento del análisis y no en el de la medida. Para la campaña de S24
hay que componer con el árbol limpio.
