# Runbook de una corrida — cómo se ejecuta una misión del listado sorteado

**Escrito el 2026-08-30.** Es el procedimiento que hay que repetir **una vez por misión** del
[listado sorteado](Evidencia/campana_oe4_misiones.csv), y está escrito para ejecutarse sin pensar:
cada paso trae su comando, lo que tiene que salir, qué hacer si no sale, y cuándo se da por
cerrado.

Está separado de [`GUIA_EJECUCION.md`](GUIA_EJECUCION.md) a propósito. Aquella explica cómo
levantar y depurar el sistema; ésta es una lista de verificación que se sigue con la simulación ya
entendida. Mezclarlas haría que el día de la campaña haya que leer treinta páginas para ejecutar
seis comandos.

El listado y su semilla salen de la §6.3 del [protocolo](PROTOCOLO_EXPERIMENTAL.md); el
aislamiento entre corridas, de la §6.4; el pilotaje, de la §7.

---

## 0. Qué es la primera corrida, y qué NO es

**La primera corrida es un PILOTO, no la misión 1 de la campaña.** Conviene decirlo porque el
2026-08-30 se afirmó lo contrario en una conversación y era falso: la §7 del protocolo exige cinco
corridas de pilotaje **antes** de la campaña, y sus datos **no forman parte de ella**.

Las tres razones por las que ésta no puede contar como corrida de campaña:

1. **El analizador de campaña no existe todavía.** Una de las cuatro preguntas que la §7 manda
   responder en el pilotaje es *«¿el registro se escribe completo y es procesable sin tocarlo a
   mano?»*, y sin analizador esa pregunta no se puede contestar.
2. **La campaña es S24.** Ejecutarla antes de tener el instrumento validado es exactamente lo que
   el pilotaje existe para evitar.
3. ~~**Hay dos productores del mismo registro y nadie los ha comparado nunca**~~ **Comparados el
   2026-09-01** (§6 de aquí abajo). No producen el mismo registro y no hay dos verdades que
   conciliar: el del bag es el autoritativo y el vivo queda fuera de la campaña.

Que sea un piloto **no** lo hace desechable: usa el par sorteado de verdad, se compone con
`--piloto`, y si todo pasa, la misión 1 se vuelve a correr en S24 como corrida de campaña. Repetir
el par no es un problema; los datos de piloto se guardan aparte y marcados.

**Misión de esta primera corrida**, fila 1 del listado:

| | |
|---|---|
| Condición | **A** (intra-nivel, entera en el piso 1) |
| Origen | `piso1_etm2` — ETM2 |
| Destino | `piso1_etm11` — ETM11 |
| Relevos esperados | **0** |
| Robot que la ejecuta | `robot1` |

### 0.1 De dónde se ejecuta cada comando

Una corrida abre **cuatro terminales**, y cada una empieza en tu carpeta personal. Antes del primer
comando de cada terminal hay que dejarla donde toca. Sólo hay dos sitios:

| Comandos que empiezan por… | Se ejecutan desde |
|---|---|
| `herramientas/…`, `python3 herramientas/…` | la **raíz del repositorio** (tu clon) |
| `ros2 …` a secas | `~/deepracer_sim_ws`, con `source install/setup.bash` hecho |

Este runbook no escribe la ruta de tu clon en ningún sitio, porque no la sabe: puede colgar de
`~`, de `~/Documents` o de un disco externo. Para confirmar que la terminal está en el sitio antes
de empezar:

```bash
ls herramientas/robot.sh
```

**Esperado:** imprime `herramientas/robot.sh`.

**Si falla** con `No such file or directory`, no estás en el repositorio: `cd` a tu clon y repite.
Ese mensaje es el diagnóstico correcto y no hay que buscar más lejos.

> **Por qué se dice esto y no «define una variable con la ruta».** Del 22 al 30 de agosto este
> proyecto pedía exactamente eso: una variable `TESIS`, y los comandos escritos como
> `cd "$TESIS" && herramientas/…`. El 2026-08-30 la primera orden de este runbook murió así:
>
> ```
> bash: herramientas/robot.sh: No such file or directory
> ```
>
> `TESIS` no estaba definida, y `cd ""` **no es un error para bash**: devuelve 0 sin moverse. La
> terminal se quedó en su sitio y el fallo salió un eslabón más tarde, acusando a un script que
> estaba perfectamente. Quitar la variable no es un rodeo: es lo que hace que ese mensaje vuelva a
> decir la verdad. Es además la forma que usa el resto del repositorio.

---

## 1. Las dos pilas se levantan siempre, también en condición A

Aunque la condición A no toca al `robot2`, **se levantan las dos**. No es celo:

La condición A es el **control** contra el que se compara la B (§6.2 del protocolo). Si las
misiones de A corrieran con un `gzserver` y las de B con dos, la diferencia de tiempos entre
condiciones llevaría dentro la diferencia de carga de la máquina, y no habría forma de separarlas
después. La comparación quedaría confundida justo en la variable que la tesis quiere medir.

El coste es real —arrancar la segunda pila— y se paga. El RTF con las dos pilas y los dos Nav2
arriba se midió en **0,9981** el 2026-08-30, por encima del 0,99 que exige RNF-06, así que la
carga extra no invalida nada ([`S21_relevo_ejecutado.md`](Evidencia/S21_relevo_ejecutado.md) §2.2).

> **Salvedad honesta:** esa medida de RTF **contradice** otra del 26-ago que dio 0,955 y 0,811 con
> las dos pilas. Las dos no se han conciliado y la sospecha —sin anotar en ninguna de las dos— es
> la GUI de Gazebo. Por eso el paso 5 de abajo manda mirar el RTF de **cada** corrida y descartarla
> si baja de 0,99, en vez de dar por buena la cifra del 30-ago.

---

## 2. Limpieza y arranque

Un `gzserver` **nuevo** por misión, sin excepción (§6.4). Encadenar misiones sobre la misma
simulación ya costó una corrida: `S20_piloto_02` arrancó a (−17,097, 10,452) por reusar el
`gzserver` anterior y salió FALLIDA a 0,573 m.

Cuatro terminales. **Ninguna exporta `ROS_DOMAIN_ID`**: desde el 2026-08-30 los dos robots viven en
el dominio 0, y exportar algo es lo que rompe.

**Terminal 1 y 2 — parar lo anterior y levantar las dos pilas.** Las dos, **desde la raíz del
repositorio** (§0.1):

```bash
herramientas/robot.sh robot1 parar && herramientas/robot.sh robot1 nav2
```

```bash
herramientas/robot.sh robot2 parar && herramientas/robot.sh robot2 nav2
```

**Esperado:** cada uno termina anunciando su puerto libre y arranca Gazebo y Nav2. Tardan 28–35 s.

**Si falla:** si `parar` avisa de procesos «que no lanzó `robot.sh`», mátalos a mano con `kill -9`
y repite — no los toca a propósito, porque no sabe de quién son. Si el puerto sigue ocupado tras
10 s, el script sale con error y no hay que seguir adelante.

---

## 3. La compuerta: nada se mide sobre una pila que no está lista

Estos dos comandos existen porque las dos comprobaciones se venían haciendo a ojo y un día no se
hicieron: el bag `S20_piloto_01` tiene **cero** mensajes en `cmd_vel`, `amcl_pose` y `plan`. Se
grabó una misión entera contra una pila muerta y no se notó hasta abrir el bag.

**Terminal 4, desde la raíz del repositorio:**

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/esperar_nav2.sh robot1 && herramientas/esperar_nav2.sh robot2
```

**Esperado:** `LISTA. Nav2, controladores, parametros y condicion inicial.` dos veces, y código de
salida 0. Comprueba los siete nodos de ciclo de vida en `active` y los siete controladores.

**Si falla:** el propio script dice cuál de las dos cosas falta. Si faltan **controladores**, suele
ser el spawner corriendo antes que `gazebo_ros2_control`: relanzar esa pila. Si faltan **nodos de
Nav2**, es la carrera entre los dos `lifecycle_manager`: relanzar suele bastar.

**Terminal 4, desde la raíz del repositorio:**

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/verificar_condicion_inicial.py robot1 && python3 herramientas/verificar_condicion_inicial.py robot2
```

**Esperado:** los dos dentro de **0,15 m** de su pose declarada.

**Si falla:** relanzar la pila que se salga. **No se corrige a mano y no se sigue igualmente.** Las
pilas derivan ~17 mm/min en reposo, así que una simulación que lleva rato encendida arranca
contaminada: la corrida del 30-ago empezó con **0,535 m y 0,745 m** de error inicial hasta que se
relanzaron las dos, que las dejó en 0,020 m. Medir un error de llegada sobre una pose contaminada
mide el tiempo que el simulador llevaba encendido, no el sistema.

---

## 4. El coordinador

**Terminal 3.** Es la única que trabaja desde el workspace, y el propio comando hace ese `cd`:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p use_sim_time:=true -p prefijo_mision:=S21P
```

**`ruta_registros` ya no va, ni en el piloto.** Existía para la comparación del §6, que el
2026-09-01 se hizo y se cerró: el registrador en vivo no produce el registro de la campaña, así que
encenderlo solo gasta CPU contra dos Gazebo justo donde RNF-06 exige RTF ≥ 0,99. Si alguien lo
enciende igual, lo que escriba no es un registro válido y no debe mezclarse con los de
`Documentos/Evidencia/registros/`.

**Esperado:** `Coordinador listo. 31 puntos, asignacion {...}`. Los 31 puntos son el catálogo con
el que se sorteó — si dice otro número, el sorteo y la corrida no son del mismo catálogo y hay que
parar.

**`use_sim_time:=true` no es opcional.** El §3 del protocolo define `t_solicitud` sobre el reloj de
simulación, que es el mismo que sella el bag. Sin él, el coordinador marcaría con reloj de pared y
con RTF ≥ 0,99 las dos formas difieren hasta un 1 %: sobre `t_respuesta` eso no es ruido, es sesgo.

---

## 5. Grabar

**Terminal 4, desde la raíz del repositorio.** El nombre del bag lleva el piloto, la condición y el número de la fila del listado:

```bash
source ~/deepracer_sim_ws/install/setup.bash && herramientas/grabar_mision.sh S21_piloto_A_01 robot1 robot2
```

**Esperado:** `Grabando en ...` con el recuento de tópicos, y ni un `AVISO`.

**Si falla:** el script se niega a grabar antes que grabar mal, y dice por qué. Los dos casos
frecuentes: nadie publica `/clock` o `/coordinacion/estado_mision` —de ahí salen **todas** las
marcas temporales—, o la terminal no tiene el workspace sourceado y `ros2 bag record` descartaría
`coordinacion_msgs` en silencio dejando un bag con pinta de bueno. Los dos se han dado.

El script deja también el `rtf.json` junto al bag, con marcas de `/clock` antes y después. Eso es lo
único que puede dar el RTF: con `--use-sim-time` el bag sella *todo* en tiempo de simulación,
incluidos `starting_time` y `duration`, así que sim/pared vale 1 por construcción.

Y deja el `condicion_inicial.json`, que es el **criterio 1** del §8 medido en el instante en que
empieza la corrida —los otros cuatro salen del bag; éste no puede—. El grabador avisa si la pose
está fuera de tolerancia, pero no aborta: la decisión de descartar se toma al componer el registro.
Los dos archivos existen por la misma razón: **si no se escribe en el momento, no se escribe nunca.**

---

## 6. Lanzar la misión, y la comprobación que nadie ha hecho nunca

**Terminal 5** —o la 4 cuando el grabador ya esté corriendo en segundo plano—. Trabaja desde el
workspace, y el comando hace el `cd`:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_etm2', destino_id: 'piso1_etm11'}"
```

**Esperado:** `exito: true`, **`relevos: 0`** por ser condición A, y la secuencia de etapas
`RECIBIDA → TRAMO_1 → TRAMO_1 → COMPLETADA`. La segunda `TRAMO_1` no es un error: los dos tramos de
una misión intra-nivel comparten etapa y lo único que cambia es el destino.

Cuando termine, **Ctrl-C en la terminal 4** para cerrar el bag. En ese orden: cortar antes deja la
misión sin su última marca.

> **La comprobación que faltaba, hecha el 2026-09-01. Ya no hay nada que ejecutar aquí.**
>
> Este paso mandaba un `diff` entre el registro que `registrador.py` escribe en vivo dentro del
> coordinador y el que `componer_registro.py` compone desde el bag, partiendo de que *«los dos
> declaran el mismo esquema congelado»*. **Esa premisa era falsa**, y el `diff` habría impreso el
> archivo entero sin decir nada útil. Se comprobó validando la salida de `a_dict()` contra
> `esquema_registro_mision.json`: **15 errores**, y de las **10 claves de primer nivel que el
> esquema exige, el vivo trae 2** (`solicitud` y `marcas`). No son dos versiones de un documento;
> son dos documentos.
>
> | | registrador vivo | compositor del bag |
> |---|---|---|
> | versión | `esquema: "1.0"` | `esquema_version: "1.1.0"` |
> | `condicion` | `"simulacion"` — es el **banco** | `mision.condicion` es **A/B**; el banco va en `mision.banco` |
> | veredicto | `metricas.criterios_exito` | `veredicto.c1_posicion` / `c2_…` / `c3_relevo` |
> | condición A/B | se **infiere** de si hubo transferencia | se **declara** desde el listado sorteado |
> | desconocido | `bool(c1 and c2 and c3)` lo vuelve `False` | lógica de tres valores, `exito` puede ser `None` |
> | continuidad (RF-24) | recorre las ~6 marcas de cambio de etapa | recorre los ~339 mensajes publicados |
>
> **La fila que decide es la última.** El coordinador publica el estado a 1 Hz, pero solo llama a
> `registro.marca()` desde `_cambiar_etapa`. Si `robot_activo` se vaciara *entre* dos transiciones,
> el tick lo publicaría y el bag lo guardaría, y el registrador vivo no anotaría nada. RF-24 es la
> variable de respuesta principal del OE4 y el productor vivo es ciego, por construcción, al modo de
> fallo que existe para detectar.
>
> **Decisión: autoritativo el del bag**, que además sobrevive a un coordinador caído. No se pierde
> nada por el camino: `num_relevos` el compositor lo deriva de `t_inicio_tramo2`, la pose de destino
> la lee de `puntos_interes.yaml`, y `punto_id` viaja en `EstadoMision.destino_actual`. El único dato
> que solo el vivo tenía —el resultado de la acción, que va por servicio y `ros2 bag` no graba— es
> justamente el que el §3.3 prohíbe usar como evidencia.
>
> **Pendiente, no bloqueante:** `metricas()` de `registrador.py` queda como código muerto que aún
> calcula un `continuidad` y un `exito` con el mismo nombre y distinta semántica. Retirarlo es
> limpieza, no urgencia — pero nadie debe citar esos números.

---

## 7. Componer el registro y dictaminar la llegada

**Terminal 4, desde la raíz del repositorio:**

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/diagnosticar_llegada.py ~/tesis_evidencia/S21_piloto_A_01 --robot robot1
```

**El veredicto de llegada se juzga contra `/odom`, nunca contra el `SUCCEEDED` de Nav2.** Es la
regla del 12-ago y la razón de que exista el riesgo R12. Criterio: **≤ 0,25 m**.

**Cuidado con `--spawn`:** su valor por defecto es la pose de `robot1`. Pasarlo mal con
`--robot robot2` acusó **15,868 m** de desvío en una corrida que había arrancado a 0,039 m.

**Terminal 4, desde la raíz del repositorio** —la ruta de `--salida` es relativa a ella:

```bash
source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/componer_registro.py ~/tesis_evidencia/S21_piloto_A_01 --banco simulacion --campana OE4_simulacion --piloto --semilla 20260822 --salida Documentos/Evidencia/registros/S21_piloto_A_01.json
```

**Esperado:** un JSON validado contra el esquema, sin ningún campo que haya que rellenar a mano.
`--piloto` es obligatorio aquí: sin él el registro entraría como dato de campaña.

**Terminal 4, sin sourcear nada** —el analizador no abre bags y no necesita ROS:

```bash
python3 herramientas/analizar_campana.py Documentos/Evidencia/registros --campana OE4_simulacion
```

**Esperado:** el informe con las cuatro métricas, y `VEREDICTO: VALIDA`. Se corre **después de cada
corrida**, no sólo al final de las 30: es lo que convierte «el registro es procesable» de una
afirmación en una comprobación, y es la única forma de enterarse de que algo se está registrando mal
en la corrida 2 y no en la 30.

El guion **sale con código 0 sólo si el veredicto es `VALIDA`**, así que se puede encadenar. Y `VALIDA`
exige que quede **al menos una corrida que contar**: si el `--campana` está mal escrito o el
directorio es el que no era, el lote queda vacío y responde `INVALIDA` diciendo de qué se compone el
cero. Un informe con `Registros leidos: 0` y veredicto favorable sería la señal más fuerte del
programa emitida desde ninguna evidencia; por eso no existe.

**Qué mirar, en este orden:**

1. **`ERRORES DE INTEGRIDAD`** — si aparece alguno, el registro se contradice y no se cuenta en
   ningún sitio. Arreglar antes de seguir; nunca «ya lo veremos al final».
2. **El N de la tasa de éxito** — tiene que coincidir con las corridas hechas. Si no coincide, hay
   un registro descartado en silencio o con error.
3. **`ALERTAS`** — cada una nombra las misiones afectadas. Una asignación por encima del tick de
   `/clock` o una continuidad rota **no se anotan y se sigue**: son resultados, y hay que ir al bag
   por los instantes que el registro ya guarda.

Con una sola corrida los intervalos salen enormes y saltará la alerta de RF-26. Es correcto: con
n = 1 no se afirma nada, y el analizador lo dice en vez de dejar que el número parezca un resultado.

---

## 8. Cuándo la corrida vale

Las cinco condiciones. **Si falla una, la corrida se descarta y se repite** (§8 del protocolo), y
el descarte se anota — el techo es el 20 %.

| | criterio | de dónde sale |
|---|---|---|
| 1 | **error de localización** de los dos dentro de **0,15 m** | paso 3, y `condicion_inicial.json` que el paso 5 deja en el bag |
| 2 | **RTF ≥ 0,99** | `rtf.json` del bag |
| 3 | error de llegada **≤ 0,25 m** contra `/odom` | paso 7 |
| 4 | el registro se compone **sin tocar un campo a mano** y `analizar_campana.py` lo agrega sin errores de integridad | paso 7 |
| 5 | número de relevos = **0** en condición A, **1** en B | resultado de la acción |

**El criterio 1 mide `/amcl_pose` contra `/odom`, no contra la tabla de spawn.** Hasta el
2026-09-04 medía la distancia al spawn, y eso rechazó una corrida sana: `S21_piloto_A_03` salió a
1,19 m y 43,92 m «de su pose declarada» sólo porque los robots venían de la misión anterior,
cuando su error de localización era de 0,032 m — mejor que el del piloto que sí pasó, 0,040 m — y
llegó a 0,068 m del destino. **Que un robot no esté en su spawn no es motivo de descarte:** en el
banco físico no se puede respawnear nada, y encadenar misiones es el comportamiento que hay que
validar. Lo que se descarta es que el robot no sepa dónde está.

En pila recién levantada los dos números son idénticos por construcción, porque AMCL se siembra
con la pose declarada (medido: 0,0401 y 0,0401 en `S21_piloto_B_02`), así que el criterio nuevo no
afloja nada respecto del viejo. El campo `criterio: "localizacion"` del JSON distingue los
`condicion_inicial.json` nuevos de los de antes del 2026-09-04, cuyo `dentro` no significa lo mismo.

**Criterio de cierre del piloto:** las cinco pasan, y los dos registros del §6 coinciden o se sabe
por qué no.

---

## 9. Lo que este runbook todavía no cubre

1. ~~**La comprobación 4 no se puede cerrar hasta que exista el analizador de campaña.**~~
   **Resuelto el 2026-08-31.** El analizador es `herramientas/analizar_campana.py` y ya está en el
   paso 7. La comprobación 4 se cierra sola: si el registro no es procesable sin intervención
   manual, el analizador lo dice y devuelve error.

   Escribirlo destapó dos cosas que no se sabían, y las dos habrían sido irreparables en S24:
   **RF-24 no tenía campo en el esquema** —la variable de respuesta principal del §2 del protocolo
   no se podía calcular desde el registro—, resuelto en la versión `1.1.0`; y **el intervalo de
   confianza citado en el §6.1 del protocolo no reproducía** (decía 80–97 % para 27 de 30, y Wilson
   da 74–97 %). Ninguna de las dos se habría notado ejecutando corridas: sólo agregándolas.
2. **No dice nada del banco físico.** Es el procedimiento de simulación. La campaña de hardware
   (RF-27) tiene otras condiciones iniciales y otra verdad de terreno, y su runbook no está escrito.
3. ~~**Las cinco corridas de pilotaje que pide la §7 no están planificadas una por una.**~~
   **Parcialmente resuelto el 2026-09-03, y no ejecutando nada: mirando lo que ya había.** En
   `~/tesis_evidencia/` había **cinco grabaciones del 30-ago** (16:35–17:45) que no se citaban en
   ningún documento y que nunca se compusieron. Dos son aprovechables:

   | bag | condición | ruta | RTF | error de llegada | veredicto |
   |---|---|---|---|---|---|
   | `S21_piloto_A_02` | **A** | `piso1_etm2 → piso1_etm11` | 0,9988 | **0,215 m** | `exito: true` |
   | `S21_piloto_B_01` | **B** | `piso1_representacion → piso2_ieee` | 0,9915 | **0,120 m** | `exito: true`, `c3_relevo: true`, continuidad íntegra |

   Con eso **el pilotaje ya no valida el instrumento sobre media función**: hay una condición A y
   una condición B con relevo real de tres tramos. `S21_piloto_A_02` es además **la fila 1 del
   listado sorteado**, así que la misión 1 no hay que volver a correrla para el piloto.

   **Las otras tres (`A_01`, `C_01`, `C_02`) no son recuperables como pilotos**, y por una razón
   que conviene no repetir: **les falta `rtf.json`**. El bag no puede suplirlo — con
   `--use-sim-time` sella *todo* en tiempo de simulación, así que sim/pared vale 1 por
   construcción — y la simulación que las grabó ya se cerró. El RTF de esas tres se perdió para
   siempre. Es exactamente el criterio 2 del §8, y es la razón por la que el paso 5 deja el
   `rtf.json` junto al bag: **si no se escribe en el momento, no se escribe nunca.**

4. ~~**El criterio 1 no sobrevive al bag, y eso afecta también a las 30 corridas de S24.**~~
   **Resuelto el 2026-09-04, antes de correr la campaña y no después.** Los cinco criterios del §8
   se comprueban a posteriori salvo el primero: el error de localización dentro de 0,15 m es una
   compuerta **previa**, y su resultado se quedaba en la terminal del paso 3, que se pierde al
   cerrarla.

   Ahora `grabar_mision.sh` mide la condición inicial de todos los robots **justo antes de abrir el
   bag** y deja el veredicto en `<bag>/condicion_inicial.json`; `componer_registro.py` lo recoge en
   `salud_del_banco.condicion_inicial`. Se guarda la desviación medida, no sólo el sí/no, para poder
   rehacer el veredicto si la tolerancia cambia. El campo es opcional en el esquema a propósito: los
   registros ya compuestos —entre ellos los dos pilotos del §9.3— siguen siendo válidos.

   **Se mide dentro del grabador y no en el paso 3** porque la desviación no depende de la misión
   sino del tiempo que la pila lleve quieta (~17 mm/min de deslizamiento), así que la única medida
   que describe la corrida es la tomada en el instante en que empieza. El paso 3 sigue siendo la
   compuerta que decide si se lanza; esto es la constancia de que se cumplió.

   Como con el RTF bajo, **el grabador avisa pero no aborta**: descartar una corrida es una decisión
   del §8 del protocolo y se toma al componer el registro, con la cifra delante.

   **Lo que no arregla:** las dos corridas del 30-ago siguen siendo irreconstruibles —sólo se pueden
   dar por buenas **4 de 5**—, y `salud_del_banco.controladores_activos` sigue saliendo `{}`, que es
   la causa de descarte `controladores_incompletos` sin instrumentar.
