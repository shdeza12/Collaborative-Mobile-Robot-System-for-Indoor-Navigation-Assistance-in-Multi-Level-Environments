# Hoja de campo — la llegada del segundo DeepRacer

**Para la sesión con el segundo vehículo.** Escrita el **2026-09-11 por la mañana**, antes de que
el codirector Néstor lo traiga, con todo lo que ya costó una sesión en las tres salidas anteriores
de hardware ya incorporado.

**La ventana con los dos carros es el recurso escaso de este proyecto.** Lleva abierto desde el
2026-08-14 el riesgo **R11** —el segundo vehículo en intervención— y de él cuelga el **único rojo
de OE2**. Esta hoja existe para que la sesión no se gaste improvisando comandos.

| Documento | Qué cubre |
|---|---|
| [`Evidencia/S19_spike_p1_p2_hardware.md`](Evidencia/S19_spike_p1_p2_hardware.md) | El cortafuegos, el cruce Humble↔Jazzy, y las tres trampas de la tarjeta |
| [`Evidencia/S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md) | La jornada con **un** vehículo: LiDAR, odometría láser, teleoperación |
| [`HOJA_CAMPO_G2.md`](HOJA_CAMPO_G2.md) | La regla de dueños, las baterías, y cómo se graba en la tarjeta |
| [`REQUISITOS.md`](REQUISITOS.md) | Las celdas de OE2: RF-11 a RF-16 |

Si hay contradicción entre esta hoja y una de esas, **manda la otra**, y se corrige esta.

---

## 1. Qué se trae de vuelta

Si la sesión produce esto, valió:

1. **La declaración de R11 por escrito** (§3). Cinco líneas. Es lo más barato de la lista y lo
   único que nadie más puede reconstruir después.
2. **Tres ficheros JSON de latencia** (§5): portátil↔carro A, portátil↔carro B, y **carro A↔carro
   B**, que es la medida que RF-15 nombra literalmente.
3. **El inventario del segundo vehículo** (§4), rellenado en la tabla del §8.

**El mínimo irrenunciable, si la tarde se tuerce:** la declaración de R11 y **el JSON de carro
A↔carro B**. Con eso RF-15 sale de rojo o se sabe por qué no. Sin el tercer JSON, los otros dos no
cierran el requisito: *«medida de ida y vuelta entre los dos vehículos»* dice el criterio, y el
portátil no es un vehículo.

---

## 2. Lo que ya está hecho, y no hay que repetir

- **El medidor existe, está probado y no depende de nada del proyecto.**
  `herramientas/medir_latencia_red.py` usa solo `rclpy` y `std_msgs`, que están en
  `/opt/ros/<distro>/` en las dos distribuciones. Su banco
  (`herramientas/prueba_medir_latencia_red.py`) pasa **27 de 27** y está validado mutando el
  código: tres mutaciones, tres detecciones. Probado además en bucle sobre el portátil bajo
  Humble el 2026-09-11: 150 de 150 pongs, mediana **0,786 ms**, y **veredicto `MEDIDA_LOCAL`
  negándose a dar cifra** porque el eco estaba en la misma máquina. Que se niegue ahí es el
  resultado que se buscaba.
- **El cruce Humble↔Jazzy por DDS ya está comprobado** (S19 §3.2): multidifusión en los dos
  sentidos, `std_msgs/String` en los dos sentidos, y `ros2 topic list` desde Humble viendo un
  tópico de Jazzy. Lo que **no** está medido es cuánto tarda, y eso es exactamente RF-15.
- **`coordinacion_msgs` compila y pasa 19/19 en Jazzy** sobre la tarjeta del **primer** carro
  (2026-09-07, `~/tesis_ws/`). En el segundo no hay nada: dalo por vacío.

---

## 3. Lo primero de todo: la declaración de R11. Cinco líneas, cinco minutos

**Esto se hace mientras Néstor todavía está delante**, porque son datos que solo él y Jonny
tienen, y porque en cuanto se vaya dejan de estar disponibles.

El cronograma pide literalmente *«qué vehículo está intervenido, qué se le intervino y en qué
fecha vuelve a estar operativo»* ([`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md), S19). La fecha
ya es hoy, así que la tercera línea se convierte en su gemela útil: **qué quedó sin arreglar**.

Se copia el bloque del §8.1 en un fichero de evidencia y se rellena. **No vale «ya está
arreglado»**: R11 ha estado abierto veintiocho días y se cierra con un dato, no con una
impresión.

> **Por qué importa más de lo que parece.** Si el vehículo vuelve con una batería distinta, un
> LiDAR distinto o la tarjeta reinstalada, cualquier número que se mida hoy y se compare con los
> del **28-ago** —los 6,35 Hz de barrido, el +2,9 % de escala— estará comparando dos vehículos
> distintos sin saberlo. Anotar qué cambió es lo que permite decidir después si una medida vieja
> sigue valiendo.

---

## 4. Bloque 1 — Qué hay en el segundo vehículo (~15 min)

**No enciendas nada más hasta acabar esto.** Se responde por SSH y a ojo.

1. **La IP.** No hay ninguna reservada por DHCP, así que cambia entre sesiones. El primer carro
   estaba en `192.168.0.102` el 2026-09-07.

       ping -c 2 deepracer.local

   **Con los dos carros en la red, `deepracer.local` es ambiguo.** Es muy probable que los dos
   anuncien el mismo nombre mDNS. Saca las dos IP del punto de acceso o con
   `ip neigh | grep 192.168.0.` desde el portátil, y **apunta cuál es cuál**, con una pegatina
   física en cada carro si hace falta. Media sesión se puede ir midiendo dos veces el mismo carro.

2. **Distribución y sistema**, para saber si es gemelo del primero:

       ssh deepracer@<IP> 'lsb_release -ds; uname -r; ls /opt/ros/'

   **Esperado:** `Ubuntu 24.04`, kernel `6.8.x-lowlatency`, y `jazzy`. Cualquier cosa distinta se
   anota y **no se corrige hoy**: la paridad entre vehículos es trabajo de otra sesión.

3. **El cortafuegos, antes de que engañe a nadie.** Esta es *la* trampa de esta sesión.

       ssh deepracer@<IP> 'sudo ufw status'

   `ufw` **permite ICMP y deniega el resto**: el `ping` sale perfecto al 100 % y el grafo ROS sale
   vacío. Costó una sesión entera el 2026-08-21. Si está `active`, se abre **por IP de origen en
   las dos máquinas**, nunca por rango de puertos —los puertos de DDS se calculan a partir del
   dominio y del índice de participante, y no son fijos—:

       sudo ufw allow from 192.168.0.0/24 comment 'DDS tesis'

   Y **en el portátil, lo mismo**, que es la mitad que se olvida.

   > **Y después de tocar `ufw`, reinicia `deepracer-core` en el carro.** Es regla operativa desde
   > S19 §4.3: un servicio arrancado antes de abrir el cortafuegos **parece aislado sin estarlo**.
   > No hace falta para el medidor de latencia —que se lanza a mano—, pero sí para cualquier cosa
   > que se mire de `deepracer-core`.

4. **El dominio.** Los dos extremos tienen que compartir `ROS_DOMAIN_ID`, y si uno lo lleva puesto
   y el otro no, no se ven. El síntoma es cero pongs, **indistinguible de un cortafuegos**.

       echo "portatil: ${ROS_DOMAIN_ID:-(sin poner, = 0)}"
       ssh deepracer@<IP> 'echo "carro: ${ROS_DOMAIN_ID:-(sin poner, = 0)}"'

5. **La batería, medida y no supuesta.** Es el sospechoso número uno de este proyecto: el 28-ago
   y el 3-sep se plantearon seis causas de software entre las dos y **las seis eran falsas**.

       ssh deepracer@<IP> "sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && ros2 service call /i2c_pkg/battery_level deepracer_interfaces_pkg/srv/BatteryLevelSrv \"{}\"'"

   Devuelve `level=N`; recién cargado dio **10** el 8-sep. **Va con `sudo`**: quien sirve ese
   servicio es `deepracer-core`, que es de `root`, y sin `sudo` el fallo esperado es **que se
   quede colgado**, no un error.

**Criterio de cierre del bloque:** las dos IP anotadas y distinguidas, `ufw` conocido en las tres
máquinas, el dominio igual en todas, y las dos baterías anotadas.

---

## 5. Bloque 2 — RF-15: la medida de ida y vuelta (~30 min)

Esta es la **pregunta 3 del spike de S19**, que quedó fuera del criterio de cierre de aquella
semana *«y no por conveniencia: depende de una reparación cuya fecha no controlamos»*. Hoy se
cierra.

### 5.1 Copiar el medidor a los dos carros

Un solo fichero, sin dependencias del proyecto. Desde la raíz del repositorio, en el portátil:

```bash
scp herramientas/medir_latencia_red.py deepracer@<IP_A>:~/ && scp herramientas/medir_latencia_red.py deepracer@<IP_B>:~/
```

**Esperado:** dos líneas `100%`.

### 5.2 Por qué es de ida y vuelta, y no de un solo sentido

**Nadie ha sincronizado los relojes de estas tres máquinas.** Una medida de un solo sentido entre
el portátil y una tarjeta mediría sobre todo el desfase entre los dos relojes, que puede ser de
segundos. En la ida y vuelta el emisor pone **su** marca, el eco la devuelve intacta, y el emisor
resta contra **su propio** reloj: el reloj de la otra máquina no entra en la cuenta en ningún
momento. Por eso el criterio de RF-15 está escrito así y no de otra forma.

### 5.3 Las tres parejas, en este orden

El orden no es caprichoso: **se empieza por la pareja que ya se sabe que funcionaba**
(portátil↔carro A, cruzada con éxito el 2026-08-21), de modo que si esa falla el problema es de
hoy y no del carro nuevo.

| # | Emisor (mide) | Eco (responde) | Para qué |
|---|---|---|---|
| 1 | portátil | carro **A** | Referencia conocida. Si esta falla, es la red de hoy |
| 2 | portátil | carro **B** | El carro nuevo alcanza al coordinador |
| 3 | carro **A** | carro **B** | **La que RF-15 nombra.** Sin esta no hay requisito |

En cada una, **dos terminales**. En la máquina del eco:

```bash
source /opt/ros/jazzy/setup.bash && python3 ~/medir_latencia_red.py --rol eco
```

En la máquina que mide (desde la raíz del repo si es el portátil; desde `~` si es un carro):

```bash
python3 herramientas/medir_latencia_red.py --rol emisor --n 600 --hz 10 --etiqueta "portatil<->carroA" --salida /tmp/rf15_portatil_carroA.json
```

Son **600 pings a 10 Hz = 60 s**. El emisor termina solo; el eco se para con `Ctrl-C`.

> **Se mide a 10 Hz aunque el tráfico real vaya a 2 Hz.** Es a propósito, y hace la prueba **más
> dura, no más blanda**: cinco veces más paquetes por segundo sobre el mismo enlace. Con 2 Hz
> durante un minuto saldrían 120 muestras y el p95 sería seis de ellas; con 600, es un percentil
> de verdad. Si alguien prefiere el ritmo real, que alargue: `--n 600 --hz 2` son 5 minutos.

**Para la pareja 3 hay que llevarse el fichero al portátil al terminar:**

```bash
scp deepracer@<IP_A>:/tmp/rf15_carroA_carroB.json Documentos/Evidencia/registros/
```

### 5.4 El criterio, y está fijado antes de ver el primer dato

**Esto se escribe aquí, el 2026-09-11, antes de medir**, que es lo que exige el §6.3 del protocolo
experimental. Está codificado en el propio medidor (`UMBRAL_MEDIANA_MS`, `UMBRAL_P95_MS`) y su
banco lo comprueba, para que relajarlo después obligue a tocar una prueba y no solo un párrafo.

**RF-15 no traía ningún número.** Decía *«latencia acotada»* y en todo el repositorio no había una
cota. La que se adopta sale de la única magnitud del sistema que la fija de verdad:

> **RF-08 exige que cada agente publique su estado a 2 Hz**, y se midió a 2,000 Hz el 2026-09-07.
> Son **500 ms de período**. Si la latencia de **un sentido** llegara a 500 ms, cada mensaje
> llegaría cuando ya se publicó el siguiente, y la imagen que el coordinador tiene del robot
> estaría desfasada una muestra **por construcción**. Ese es el techo duro: **500 ms de ida = 1000
> ms de ida y vuelta.** Un criterio necesita margen sobre el techo, no rozarlo.

| Magnitud | Cota | Qué margen deja |
|---|---|---|
| **Mediana** de ida y vuelta | **≤ 100 ms** | factor **10** sobre el techo |
| **p95** de ida y vuelta | **≤ 250 ms** | factor **4** sobre la cola |
| **Pérdida** | **= 0 %** | ninguno, y es a propósito |

**La pérdida es dura a propósito.** El perfil del medidor es `RELIABLE` con profundidad 10 —el
mismo que `coordinacion/agente.py` usa para `/<ns>/estado`—, o sea que DDS ya reintenta. Un pong
que aun así no vuelve no es un paquete con mala suerte: es un enlace que no sostiene el tráfico.

**Lo que el medidor hace y conviene saber antes de leer su salida:**

| Veredicto | Qué significa |
|---|---|
| `CUMPLE` | Las tres cotas dentro |
| `NO_CUMPLE` | Alguna fuera, y dice cuál con el número |
| `MEDIDA_LOCAL` | **El eco respondió desde la misma máquina que mide.** No atravesó la red. No da cifra |
| `SIN_DATOS` | Cero pongs. Mira, en este orden: el eco corriendo, el mismo dominio, `ufw` en **las dos** |
| `SIN_VEREDICTO` | Menos de 100 muestras, o pongs sin firma de eco |

`MEDIDA_LOCAL` está ahí porque un `--rol eco` olvidado en otra pestaña del portátil da **décimas
de milisegundo** por memoria compartida y parece un éxito rotundo. Se comprobó que funciona: la
prueba en bucle del 2026-09-11 dio 0,786 ms de mediana y **se negó a dar veredicto**.

### 5.5 Qué significa cada resultado, decidido antes de medir

| Lo que salga | Qué quiere decir |
|---|---|
| Las tres parejas `CUMPLE` | **RF-15 pasa a 🟢** y OE2 se queda sin rojos. Es el desenlace esperado en una LAN de un salto |
| 1 y 2 `CUMPLE`, 3 `NO_CUMPLE` | El enlace carro↔carro es el débil. Anótalo y **mira si los dos están en el mismo punto de acceso**: dos saltos por un repetidor explican decenas de ms |
| Alguna `SIN_DATOS` | Casi seguro `ufw` o el dominio. Vuelve al §4.3 y §4.4. **No es un hallazgo**, es la trampa conocida |
| `NO_CUMPLE` por p95 con mediana sana | Cola larga: wifi con interferencia o ahorro de energía en la tarjeta. **Se anota y se repite una vez.** Si se repite, es un hallazgo real y va al informe |
| `NO_CUMPLE` por pérdida | El más serio de todos, porque el perfil es `RELIABLE`. No se maquilla bajando la cota |

**No se ajusta el criterio para que salga bien.** Es el reproche que este proyecto ya se hizo el
26-ago, y la razón por la que las cotas están escritas arriba y codificadas en el medidor antes de
la sesión.

---

## 6. Lo que NO se hace hoy, y por qué

Esta lista es tan importante como la de arriba. Con dos carros delante la tentación es hacerlo
todo, y el resultado histórico de eso es media sesión de cada cosa y ninguna cerrada.

- **RF-27 y la campaña física NO se tocan.** Está planificada para **S24–S25**, y necesita mapa
  del entorno real, Nav2 a bordo y protocolo instrumentado. Nada de eso existe hoy.
- **La paridad entre vehículos NO se persigue.** Dejar el segundo carro al nivel del primero es una
  tarea propia, con su sesión. Hoy solo se **inventaría** qué le falta.
- **RF-11, RF-12, RF-13 y RF-14 NO son de hoy.** Los cuatro parciales de OE2 **necesitan un solo
  vehículo** —revisado el 2026-09-05— así que no compiten por esta ventana. Gastarla en ellos es
  gastar el recurso escaso en lo que se puede hacer cualquier otro día.
- **No conectes ni desconectes nada por USB con la pila arrancada.** El bus se re-enumera,
  `/dev/ttyUSB0` desaparece, y `systemctl` seguirá diciendo `active (running)`. Miente.
- **Nunca reinicies un carro.** Se queda en GRUB esperando que alguien elija sistema, y no hay
  monitor.

**Si sobra tiempo después del §5**, lo que más rinde es el **inventario del §4 hecho con calma**
sobre el carro nuevo: qué sensores enumera, qué publica `deepracer-core`, y si el LiDAR está o no.
Es información que hace planificable la sesión de paridad, y no necesita que nada funcione.

---

## 7. Las trampas de esta sesión, en una tabla

| Trampa | Cómo se ve | Cómo se evita |
|---|---|---|
| **`ufw` activo** | `ping` al 100 % y grafo ROS vacío | `sudo ufw status` en **las tres** máquinas, antes de nada (§4.3) |
| **`ROS_DOMAIN_ID` distinto** | Cero pongs, igual que un cortafuegos | Comprobarlo en los dos extremos (§4.4) |
| **`deepracer.local` ambiguo con dos carros** | Se mide dos veces el mismo vehículo | Sacar las dos IP y **pegar una etiqueta física** en cada carro (§4.1) |
| **El eco en la misma máquina que mide** | Décimas de ms y un éxito aparente | El medidor lo detecta solo: `MEDIDA_LOCAL` |
| **`deepracer-core` sin reiniciar tras tocar `ufw`** | El servicio parece aislado sin estarlo | Reiniciarlo (S19 §4.3) |
| **La batería cayendo** | Software que se degrada poco a poco y candidatos plausibles | Medir `level` al empezar y al acabar (§4.5) |

Y la regla que las resume: **`systemctl status` y `ros2 topic list` no demuestran nada.**
`systemctl` ha dicho `active` con el LiDAR muerto y con `deepracer-core` reiniciado por su cuenta;
`ros2 topic list` ha dejado fuera un tópico que publicaba a 6,99 Hz. **Comprueba por el dato que
sale.**

---

## 8. Hoja de anotaciones

### 8.1 La declaración de R11

```
R11 -- declarado por: ____________________   fecha: 2026-09-__

1. que vehiculo estuvo intervenido (cual de los dos, como se distingue):
   ______________________________________________________________

2. que se le intervino exactamente:
   ______________________________________________________________
   ______________________________________________________________

3. que piezas se cambiaron -bateria, LiDAR, tarjeta, chasis-:
   ______________________________________________________________

4. se reinstalo el sistema de la tarjeta?   SI / NO
   si SI: que distribucion quedo: ______________

5. que quedo SIN arreglar, o con reserva:
   ______________________________________________________________

6. las medidas del 2026-08-28 (6,35 Hz de barrido, +2,9 % de escala)
   se tomaron sobre el vehiculo: A / B / no se sabe
```

### 8.2 Inventario de los dos vehículos

```
                                 carro A              carro B
etiqueta fisica pegada    :  ______________      ______________
IP                        :  192.168.0.___       192.168.0.___
lsb_release -ds           :  ______________      ______________
kernel                    :  ______________      ______________
/opt/ros/                 :  ______________      ______________
ufw status                :  active / inactive   active / inactive
ROS_DOMAIN_ID             :  ______              ______
battery level al empezar  :  ______              ______
battery level al acabar   :  ______              ______
LiDAR conectado?          :  SI / NO             SI / NO
~/tesis_ws/ existe?       :  SI / NO             SI / NO
```

Portátil: `ROS_DOMAIN_ID` = `______`  ·  `ufw status` = `______`

### 8.3 Las tres medidas de RF-15

```
#  emisor      eco         hora   env  rec  perd  min    mediana  p95    max    veredicto
------------------------------------------------------------------------------------------
1  portatil    carro A     ____   600  ___  ____  ____   _______  ____   ____   __________
2  portatil    carro B     ____   600  ___  ____  ____   _______  ____   ____   __________
3  carro A     carro B     ____   600  ___  ____  ____   _______  ____   ____   __________
```

Todos los tiempos en **ms de ida y vuelta**. Cotas: mediana ≤ 100 · p95 ≤ 250 · pérdida = 0 %.

**Los tres JSON se guardan en `Documentos/Evidencia/registros/`.** La tabla de arriba es para
leerla en el sitio; el JSON es la evidencia, porque lleva además el `hostname` de los dos
extremos, el ritmo, el relleno y los umbrales con los que se juzgó.

**Incidencias, y anótalas aunque parezcan tonterías:**

```
______________________________________________________________________
______________________________________________________________________
______________________________________________________________________
```

Un valor raro **con una nota al lado es un dato**; sin la nota es basura.

---

## 9. Antes de que se vaya el segundo carro

- ¿Está rellenada la declaración de R11 del §8.1, **con quien la declara y la fecha**?
- ¿Están los **tres** JSON, y en particular el de carro A↔carro B?
- ¿Está el inventario del §8.2 con las dos IP y las dos etiquetas físicas?
- ¿Se anotaron los `level` de batería al acabar?

**Si las cuatro son que sí, RF-15 se resuelve esta misma noche en el escritorio** y R11 se cierra
con un dato. Si alguna es que no, dilo en el corte semanal tal cual: un requisito que se queda en
rojo con la razón escrita vale más que uno verde sin evidencia.
