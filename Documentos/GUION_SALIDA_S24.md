# Guion de la salida del 2026-09-23 — cuatro pruebas en una sesión

**Este es el documento que se lleva al campo.** El razonamiento de por qué la
recta se mide en dos sitios, qué umbrales usa el comprobador y de dónde salen,
está en [`GUION_RECTA_PELDANO2.md`](GUION_RECTA_PELDANO2.md); aquí están las
órdenes y los criterios, que es lo que hace falta con el carro delante.

**Vehículo de la sesión: `amss-ez9n` (192.168.0.102), y solo ése.** Es el que
tiene la dirección calibrada y va recto, y es el que produjo la tabla de
tracción del 22-sep; cambiar de carro a mitad de sesión invalida la comparación.

> ## Regla que no se negocia: **`amss-jgm9` (.101) APAGADO**
>
> No basta con dejarlo quieto. Encendido, su LiDAR entra en el bag de `.102`
> **intercalado** con el propio, y el bag resultante parece sano: frecuencia
> correcta, número de mensajes correcto, ningún aviso. Así se perdieron los
> cinco bags del 28-ago y no se descubrió hasta cuatro días después.
>
> Medido el 23-sep: **no existe ninguna comprobación en vivo que lo detecte.**
> `Publisher count` dice 1 durante los primeros ~5 s de cualquier proceso y 2
> después, y aun diciendo 2 los datos pueden no estar cruzando. La única defensa
> es apagar el otro carro **y comprobar cada bag después de grabarlo**.
>
> Los bloques C y D no graban bag, así que a ellos no les afecta.

---

## 0. Antes de salir — ya está hecho, esto es solo la comprobación

Todo lo verificable por red se verificó el 23-sep entre las 17:30 y las 18:10.
**No hay que preparar nada**; esta tabla existe para que, si algo falla en
campo, sepas que ya funcionó y el problema es de ese momento.

| Qué | Estado comprobado |
|---|---|
| `.102` vivo, 19 GB libres | ✅ |
| `deepracer-core` activo | ✅ |
| `comprobar_movimiento_bag.py` en el carro | ✅ probado bajo Jazzy, mismas cifras que en el portátil |
| `sostener_traccion.py` en el carro | ✅ |
| Puente `cmdvel_to_servo_node` compilado | ✅ |
| El puente arranca **como `root`** y suscribe `/cmd_vel` | ✅ `Subscription count: 1` |
| `/set_max_speed` responde en caliente | ✅ `error=0` con `throttle: 0.9` |
| `sudo` sin contraseña en el carro | ✅ |
| La orden de grabación, literal | ✅ ensayada, 58 mensajes en 6,2 s |

**Lo único que hay que llevar:** flexómetro, cinta de marcar, cronómetro
(teléfono), papel y lápiz. Y la batería del carro, que en la última lectura
estaba en `level=9`.

---

## 1. Orden de los bloques, y por qué ése

| | Bloque | Dónde | Empuja o rueda | Tiempo |
|---|---|---|---|---|
| 1º | **A · recta de control** | sitio con estructura a la vista | empujado a mano | ~20 min |
| 2º | **B · recta del pasillo** | el pasillo | empujado a mano | ~20 min |
| 3º | **D · `/cmd_vel`** | donde haya ~5 m libres | **rueda solo** | ~10 min |
| 4º | **C · rampa** | donde haya **20 m** | **rueda solo, rápido** | ~10 min |

**El orden importa y no es el obvio.** A y B son la ruta crítica (G-2) y no
tienen ningún riesgo: el carro va empujado. C lanza el vehículo a 0,80 y la
corrida 13 del 22-sep acabó **a 70 cm** de agotar los 20 m. Si C se corriera
primero y algo se rompiera, se habría perdido G-2 por hacer antes lo barato.

**Si la sesión se acorta, el orden de sacrificio es: C, luego D, luego B.** A no
se sacrifica nunca: sin control, un fallo en el pasillo no se puede interpretar
—no se sabría si rf2o está roto o si el pasillo es inobservable— y la salida no
habría decidido nada.

---

## 2. Bloque A y Bloque B — la recta de G-2

Los dos bloques son **el mismo procedimiento** en dos sitios distintos.

### 2.0 · Para qué existe el sitio A, que es lo que decide cómo elegirlo

El Bloque B graba el pasillo. Si sale mal, hay **dos explicaciones y ningún modo
de distinguirlas**: que el pasillo no le dé información de avance a rf2o —que es
el hallazgo—, o que la cadena de medida esté rota. Solo con el bag del pasillo,
un resultado malo **no decide nada**. Ya ocurrió: hasta el 2026-09-08 no existía
ningún mapa aceptado con esta cadena, y esa ausencia hacía indistinguible un
fallo del sitio de un fallo del instrumento.

El sitio A es el sitio donde la cadena **tiene que** acertar.

| A | B | Qué se concluye |
|---|---|---|
| bien | mal | **El pasillo es la causa.** Es el resultado que se busca |
| bien | bien | La cadena sirve también en el pasillo. También es resultado |
| mal | — | **El instrumento está roto.** B no dice nada; arreglar antes de seguir |

Por eso el Bloque A **no se sacrifica nunca** (§1): sin él, el Bloque B no vale
para nada aunque esté impecablemente grabado.

| | Sitio A (control) | Sitio B (pasillo) |
|---|---|---|
| Qué es | **un cuarto, no un pasillo**: un espacio que se cierra, con superficies **a menos de ~6 m durante toda la pasada**. El molde es la referencia medida: caja cerrada de **7,70 × 2,70 m**, índice 13,8 %, el único mapa que este proyecto ha aceptado con SLAM. Un **salón vacío** es mejor que un hall —cerrado por los cuatro lados y con pupitres—; el hall del piso 2 sirve **sin alejarse de él** | el pasillo |
| Qué contesta | ¿la cadena rf2o funciona? Aquí **debe** acertar | ¿cuánto se degrada en el sitio real? |
| Nombres de los bags | `recta_control_1` … `_3` | `recta_pasillo_1` … `_3` |

**Medidas que hay que tomar con flexómetro antes de grabar nada en el sitio A:**

| Qué | Medida | Cómo se comprueba allí mismo |
|---|---|---|
| Recta libre para empujar | **6–8 m** | entre las dos cintas |
| Pared, puerta o mueble **de frente** al llegar | **≤ 6 m** desde la marca de llegada | desde la cinta de llegada hacia delante |
| Lo mismo **al salir**, a la espalda | **≤ 6 m** desde la marca de salida | desde la cinta de salida hacia atrás |
| Ancho | no manda; entre 2,5 y 5 m está bien | a ojo |
| Gente moviéndose | **ninguna** | mirar |

> **Por qué las dos filas del medio son las que deciden.** Lo que informa del
> avance son **superficies encaradas a la marcha**: al avanzar, su distancia
> cambia. Las paredes laterales **no** cambian de distancia porque avances, y
> por eso un pasillo falla. Un espacio abierto sin nada delante falla por la
> misma razón aunque sea enorme.

### 2.1 · Marcar la recta

Marca con cinta un punto de salida y uno de llegada **en línea recta** y mide la
separación con flexómetro. Anota la longitud con dos decimales. **La longitud
buena no es la misma en los dos sitios, y en el A conviene que sea corta:**

| | Sitio A (control) | Sitio B (pasillo) |
|---|---|---|
| Longitud | **6–8 m** | **15–20 m** si el sitio lo permite |
| Por qué | la recta tiene que **quedarse dentro** de la zona con estructura. El efecto de un hall **muere entre los 5 y los 6 m** —medido el 17-sep en piso 2: 17,5 % a 2,2 m, 9,2 % a 4,2 m, 5,9 % pasados los 6,2 m, que es ya el fondo del pasillo—. Una recta larga que se aleja del hall **graba pasillo en su segunda mitad** y el bag de control deja de ser control | aquí interesa justo lo contrario: el tubo liso, que es lo que se quiere caracterizar |

> **Corolario que ahorra una discusión en campo:** el sitio A no se elige a ojo
> ni se defiende con argumentos. `medir_informacion_avance.py` da un número
> sobre el bag ya grabado, y hay referencias: caja cerrada de 7,70 m **13,8 %**
> → mapa aceptado; pasillo simulado **6,8 %** → rechazado; pasillos reales de
> piso 1 y 2, **5,1 %** y **5,9 %**. Si el sitio A sale por debajo de ~10 %
> **no era un control, era un segundo pasillo**, y el Bloque A pierde su
> función: ya no puede decir «la cadena funciona». Los dos bloques son
> comparables entre sí porque los dos son recta pura, que es la única
> condición de uso que tiene la herramienta.

El mínimo de G-2 son 5 m, pero lo que manda no son los metros:

> **Cada pasada tiene que durar 60 s de movimiento**, porque el comprobador
> rechaza por debajo de eso. **20 m empujados a 0,5 m/s son 40 s y los rechaza
> igual.**
>
> | Recta | Velocidad máxima | Cómo se siente |
> |---|---|---|
> | 20 m | 0,33 m/s | paso lento |
> | 15 m | 0,25 m/s | paso muy lento |
> | 10 m | 0,17 m/s | casi arrastrando |
> | 6 m | 0,10 m/s | 60 s para 6 m, incómodo pero válido |
>
> **No midas velocidad: mide tiempo.** Cronómetro al empezar a empujar; si
> llegas antes de **70 s**, la pasada no sirve y se repite más despacio.

### 2.2 · Cada pasada, paso a paso

1. Eje delantero sobre la marca de salida.
2. Lanza la grabación (orden abajo) y **espera 15 s quieto**, no 5.
3. Empuja **despacio y parejo** hasta la llegada: **no menos de 70 s**.
4. **Espera 5 s quieto** en la llegada.
5. **No cortes nada.** Se corta sola a los 100 s. Espera a ver `Recording stopped`.

> **Por qué 15 s y no 5.** El grabador **no escribe nada durante los primeros
> ~5,5 s**, aunque ya haya dicho `Subscribed to topic`. Medido dos veces el
> 23-sep: 8 s de reloj dieron 2,46 s de bag, y 12 s dieron 6,57 s. Con 5 s de
> espera, el tramo quieto inicial —el que sirve para separar la deriva del
> avance real— **no existiría**.

> **Por qué no se corta a mano.** `Ctrl-C` sobre un `ssh host "orden"` no llega
> al grabador: muere el cliente en el portátil y el grabador queda **huérfano y
> grabando**. En disco quedaría un `.mcap` de **0 bytes sin `metadata.yaml`**,
> ilegible, y la pasada siguiente caería dentro del mismo bag.

### 2.3 · Las órdenes

**Grabar** (cambia el nombre en cada pasada):

```
ssh deepracer@192.168.0.102 "source /opt/ros/jazzy/setup.bash && cd ~ && timeout -s INT 100 ros2 bag record -s mcap -o recta_control_1 /rplidar_ros/scan"
```

**Comprobar, en el propio carro, antes de seguir:**

```
ssh deepracer@192.168.0.102 "source /opt/ros/jazzy/setup.bash && python3 ~/comprobar_movimiento_bag.py ~/recta_control_1"
```

| | |
|---|---|
| **Esperado** | `sensor en movim.` por encima de **60 s**, `sensor quieto` por debajo del **40 %**, y **ningún** aviso de contaminación |
| **Si falla por tiempo** | Repite **esa** pasada más despacio. No sigas con las otras dos: saldrían con el mismo defecto |
| **Si falla por contaminación** | El otro carro está encendido. Apágalo y repite. No se salva en análisis |
| **Si sale `.mcap` de 0 bytes** | Se cortó a mano. Mata el huérfano con `ssh deepracer@192.168.0.102 "pkill -f 'ros2 bag record'"` — al morir vuelca lo grabado. **Mátalo antes de repetir, no después** |
| **Cierre** | Una pasada aceptada. A partir de ahí, las otras dos con el mismo ritmo |

**Pásale el comprobador a las seis, no solo a la primera.** Cuesta veinte
segundos por bag y es la única defensa real contra la contaminación.

El aviso `no es '/scan'` que saldrá **es esperado**: rf2o escucha `/scan` y el
remapeo se hace al reproducir, en el escritorio.

### 2.4 · Un resultado que parece fallo y no lo es

Si el bag **de control** sale con buen porcentaje de movimiento y el **del
pasillo** sale «quieto» con el mismo empuje y la misma duración, **no repitas la
pasada buscando que pase.** Anótalo tal cual: el detector mide la mediana del
cambio entre rayos, y en un pasillo largo los rayos laterales no cambian al
avanzar. Eso es la inobservabilidad longitudinal, medida por otro instrumento, y
es material para el documento — no un fallo de grabación.

---

## 3. Bloque D — que el carro se mueva mandado por `/cmd_vel`

**Qué cierra:** la primera mitad de RF-11, abierta desde S19. La tanda del
22-sep fue directa a `/ctrl_pkg/servo_msg`, sin pasar por el reescalado, y por
eso el requisito siguió en 🟡.

> ### Sin este ajuste, D falla — y parecería que el puente está roto
>
> La escalera del puente, calculada el 23-sep desde el código y coincidente con
> la tabla medida el 22-sep:
>
> | `linear.x` | throttle con `max_speed_pct` 0,68 | con 0,90 | con 1,00 |
> |---|---|---|---|
> | 0,25 y 0,26 | **0,0000** | **0,0000** | **0,0000** |
> | 0,40 – 1,19 | 0,4247 | **0,6327** | 0,8000 |
> | 1,20 – 1,99 | 0,6242 | — | 0,9920 |
>
> Dos cosas. **(1)** Los valores que Nav2 tiene configurados —0,26 y 0,05— dan
> **cero exacto**, y sin error. **(2)** Con el `max_speed_pct` de fábrica, 0,68,
> un `linear.x` de 0,50 da throttle **0,4247**, y el umbral de arranque medido de
> este carro está **justo en 0,50**: el carro no se movería, y no por culpa del
> puente.
>
> Por eso D fija `max_speed_pct = 0,90`, que deja el throttle en **0,6327** —
> junto al escalón 0,60, el único cuyo comportamiento está medido (4,20 m en 4 s).
> Se ajusta **en caliente**, sin recompilar. Probado el 23-sep: `error=0`.

**1 · Arranca el puente como `root`** y déjalo corriendo en esta terminal:

```
ssh deepracer@192.168.0.102 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && source ~deepracer/coordinacion_ws/install/setup.bash && ros2 run cmdvel_to_servo_pkg cmdvel_to_servo_node'"
```

> **Tiene que ser `root`.** Como `deepracer` el nodo arranca igual y suscribe
> igual, pero **el carro no se mueve**: `servo_pkg` corre como `root` y Fast DDS
> no empareja entre usuarios distintos. No da error, se queda callado.

**2 · Ajusta la escala**, en otra terminal:

```
ssh deepracer@192.168.0.102 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && source ~deepracer/coordinacion_ws/install/setup.bash && ros2 service call /set_max_speed deepracer_interfaces_pkg/srv/NavThrottleSrv \"{throttle: 0.9}\"'"
```

Esperado: `NavThrottleSrv_Response(error=0)`.

**3 · Marca el punto de salida, aparta a todo el mundo, y publica 2 s:**

```
ssh deepracer@192.168.0.102 "sudo -n bash -c 'source /opt/ros/jazzy/setup.bash && timeout 2 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \"{linear: {x: 0.5}, angular: {z: 0.0}}\"'"
```

**4 · Mide con flexómetro** desde la marca hasta donde quedó el carro.

| | |
|---|---|
| **Esperado** | El carro **se desplaza**, del orden de 1–2 m. La cifra exacta no es el resultado: el resultado es que se movió mandado por `/cmd_vel` |
| **Si no se mueve** | Comprueba en este orden: ¿el puente corre como `root`? ¿el servicio devolvió `error=0`? ¿`/cmd_vel` tiene `Subscription count: 1`? Los tres están verificados desde el portátil, así que un fallo aquí es de esta sesión |
| **Si se pasa de frenada** | Normal: al acabar el `timeout` el puente publica ceros y el carro **rueda por inercia**. La inercia es parte de la distancia; anótala como tal |
| **Cierre** | Dos corridas con la distancia anotada. Con eso RF-11 tiene su mitad de mando |

**Repite una segunda vez** para tener dos medidas, y **para el puente con
`Ctrl-C`** al terminar. Saldrá un `RCLError: rcl_shutdown already called`: es un
defecto conocido de la plantilla de AWS al recibir `SIGTERM`, **no es un fallo**.

---

## 4. Bloque C — la rampa de tracción

**Qué cierra:** el pendiente de escala de RF-14, y con él la envolvente real que
Nav2 necesita para G-3.

**Qué falta exactamente.** El 22-sep se midieron trece corridas y la de control
las invalidó *como velocidad*: a throttle 1,00 la ventana [4 s, 6 s] dio
**4,250 m/s** contra **2,900 m/s** de la [2 s, 4 s], o sea que el carro **seguía
acelerando en el segundo 4** y el supuesto del método era falso. Ya existen `d₂`
y `d₄` para cada escalón; **falta `d₆`**, y con él se comprueba si

`(d₆ − d₄)/2 ≈ (d₄ − d₂)/2`

Si se cumple, esas filas **sí** son velocidades y el documento entrega media
curva medida. Si no, no lo son, y eso también es un resultado.

> ### Antes de la primera corrida, tres reglas
>
> 1. **`--tope 1.0` es obligatorio.** Sin él la herramienta rechaza cualquier
>    valor por encima de 0,35. La propia herramienta avisa de que subirlo «es
>    como se lanza un carro contra una pared»: **el aviso es correcto**, y lo que
>    lo hace admisible es que 0,60–1,00 *es justo lo que se está midiendo*.
> 2. **`Ctrl-C` no frena**, solo suelta el acelerador. Lo único que para un
>    DeepRacer lanzado es la distancia que tenga delante. Despeja la recta entera
>    antes de empezar, y ponte **a un lado**, nunca al final.
> 3. **Si una corrida pasa de la mitad de la recta, no subas de escalón.** Esta
>    regla ya se saltó una vez, el 22-sep, y la corrida 13 acabó a 70 cm del
>    final de los 20 m.

**Tres corridas, en este orden y no en otro:**

| # | throttle | `d₆` esperada | ¿cabe en 20 m? |
|---|---|---|---|
| 1 | 0,60 | ≈ 6,6 m | sí, holgado |
| 2 | 0,70 | ≈ 10 m | sí |
| 3 | 0,80 | ≈ 11,6 m | sí, pero ya pasa de la mitad |

**No corras 0,90 ni 1,00.** A 0,90 la estimación son ≈ 14 m, y 1,00 ya se midió
en 19,30 m: no cabe. El escalón de 1,00 necesita otro instrumento —tiempo de
paso entre dos marcas, con vídeo— y **no se improvisa**.

**La orden** (cambia el `--throttle` en cada corrida):

```
ssh -t deepracer@192.168.0.102 "sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~deepracer/sostener_traccion.py --throttle 0.60 --marcha 6 --tope 1.0 --cuenta-atras 5'"
```

| | |
|---|---|
| **Esperado** | Cuenta atrás de 5 s, 5 s quieto, 6 s de marcha, 5 s quieto. El carro recorre del orden de la tabla |
| **Qué anotar** | La distancia con flexómetro desde la marca de salida, con dos decimales, **y si tocó frenar** |
| **Si pasa de la mitad de la recta** | Para la serie ahí. Lo medido vale; lo que falta se anota como no medido |
| **Si no arranca** | El puente del bloque D puede seguir vivo publicando ceros. Párale antes: `ssh deepracer@192.168.0.102 "sudo -n pkill -f cmdvel_to_servo"` |
| **Cierre** | Tres distancias anotadas, o las que se hayan podido correr con la regla de parada respetada |

---

## 5. Recogida de los bags

```
mkdir -p ~/tesis_evidencia/S24_recta_peldano2 && scp -r deepracer@192.168.0.102:recta_\* ~/tesis_evidencia/S24_recta_peldano2/
```

| | |
|---|---|
| **Esperado** | Seis carpetas, cada una con su `metadata.yaml` y su `.mcap` de bastante más de 5123 B |
| **Si falla** | El mensaje será `No such file or directory` en los dos casos posibles. Si acaba en `/`, falta el destino: relanza con el `mkdir -p`. Si no, los bags no están donde se grabaron: `ssh deepracer@192.168.0.102 "ls -d ~/recta_*"` |
| **Regla** | **No borres nada del carro** hasta que los seis estén en el portátil y abiertos |

Los bags vienen en formato Jazzy y se adaptan en el escritorio con
`adaptar_bag_jazzy.py`. Eso ya no es trabajo de campo.

---

## 6. Qué anotar en papel — y por qué en papel

Por cada pasada de A y B: **sitio, número, longitud medida, segundos que
tardaste, y cualquier cosa rara** (que el carro se torció, que alguien pasó por
delante, que se enganchó una rueda).

Por cada corrida de C y D: **throttle, distancia medida, y si hubo que frenar.**

Una pasada con una incidencia anotada sirve. Una pasada limpia en apariencia
pero con una incidencia no anotada **envenena el promedio**, y en el escritorio
ya no hay forma de saberlo.

---

## 7. Criterio de cierre de la salida

| Bloque | Cerrado cuando |
|---|---|
| **A** | Tres bags de control aceptados por el comprobador |
| **B** | Tres bags de pasillo aceptados, **o** el hallazgo de que el pasillo sale «quieto» con el mismo empuje que el control, anotado como tal |
| **D** | Dos distancias anotadas con el carro movido desde `/cmd_vel` |
| **C** | Las `d₆` que la regla de parada haya permitido |

**La salida no decide G-2.** G-2 se decide en el escritorio, corriendo rf2o
sobre los bags y comparando contra el flexómetro. Lo que la salida tiene que
garantizar es que **los bags sean interpretables**: con control, sin
contaminación, y con el tiempo de movimiento suficiente.

---

## 8. Nota de alcance sobre el Bloque B

El [acta GO/NO-GO](ACTA_GO_NOGO.md) §6 dice que **no se corre nada de la etapa 3
hasta que el sitio esté decidido por escrito**, y la etapa 3 es el pasillo real.

**B no es etapa 3.** La etapa 3 es *«la que produce la evidencia»*: la campaña de
RF-27, con los dos vehículos y N repeticiones. B es una pasada diagnóstica con el
carro empujado a mano, sin autonomía y sin protocolo. **Se corre como insumo del
propio §6**, porque el acta pide decidir *«con la medición como justificación»* y
sin medir el pasillo los directores no tienen con qué decidir.

Queda escrito aquí para que la distinción sea deliberada y no un descuido.
