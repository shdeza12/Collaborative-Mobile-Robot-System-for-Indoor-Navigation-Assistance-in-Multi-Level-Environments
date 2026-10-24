# Guía de estudio — Primer control de avances

**Para qué sirve esto.** Estudiar la presentación `Primera_entrega_avances_Proyecto_II.pptx` de
modo que puedas **explicar cada término que aparece en pantalla** y **defender cada cifra**. No es
un guion para leer: es el material de detrás, el que te permite contestar cuando alguien se sale
del guion.

Orden recomendado de estudio: §1 (vocabulario) → §3 (las cuatro métricas) → §4 (qué decir en cada
diapositiva) → §5 (preguntas trampa). La §6 es la única parte que hay que saber de memoria.

---

## 1. El vocabulario, explicado desde cero

### 1.1 La plomería: ROS 2 y cómo hablan las partes

**ROS 2** no es un sistema operativo ni un programa. Es un **conjunto de librerías y convenciones
para que varios programas se manden datos entre sí**. Piensa en él como el sistema nervioso: no es
ningún órgano, es lo que los conecta.

**Nodo.** Un programa que participa en la red de ROS. En este proyecto hay nodos para el LiDAR,
para la navegación, para el coordinador, para cada rueda. Un nodo hace *una* cosa.

**Tópico.** Un canal con nombre por el que fluyen datos **de forma continua y en un solo sentido**,
de quien publica a quien se suscribe. El que publica no sabe quién escucha, ni le importa.
- Ejemplo del proyecto: `/robot1/scan` — el LiDAR del robot 1 publica ahí lo que ve, unas 10 veces
  por segundo, y quien quiera lo lee.
- **Cuándo se usa:** para flujo constante. Sensores, posiciones, estado.

**Servicio.** Una llamada de ida y vuelta: pregunto, esperas, contestas. Como una función, pero
entre programas distintos.
- **Cuándo se usa:** para algo instantáneo que devuelve respuesta. «¿Cuál es el catálogo de
  puntos?»

**Acción.** Como un servicio, pero **para tareas que tardan**: puedes pedirla, recibir avisos de
progreso mientras corre, y cancelarla a mitad.
- Ejemplo del proyecto: **`navigate_to_pose`** — «ve a esta coordenada». Tarda minutos, te va
  informando, y se puede abortar.
- **Esto importa mucho:** el contrato del proyecto dice que **el coordinador manda a un robot de
  una sola forma: llamando su acción `navigate_to_pose`. Nunca le publica velocidades
  directamente.** Es lo que hace que el coordinador sea un coordinador y no un piloto.

**DDS** *(Data Distribution Service)*. Es **el mensajero que hay debajo de todo lo anterior**. ROS 2
no inventó su propia red: se apoya en DDS, un estándar industrial que ya existía. Cuando un nodo
publica en un tópico, quien realmente mueve esos bytes por la red es DDS.
- Su propiedad clave es el **descubrimiento automático**: enciendes un nodo y encuentra solo a los
  demás, sin configurar direcciones IP.
- **`ROS_DOMAIN_ID`** es un número que separa redes DDS. Dos nodos con dominios distintos **no se
  ven**, aunque estén en el mismo computador.
- **Por qué esto sale en tu proyecto:** al principio pusieron cada robot en un dominio distinto
  para que no se pisaran. Eso creó un bloqueo — **el coordinador vive en un dominio, así que no
  podía alcanzar a los dos robots a la vez**, y sin eso no hay relevo. Se levantó el 30 de agosto
  eligiendo la otra salida: **un solo dominio, y la separación se hace por nombres.**
- **Si te preguntan «¿qué es DDS?»:** «Es el middleware de comunicaciones sobre el que corre ROS 2;
  el que descubre los nodos y transporta los mensajes. Nosotros tuvimos que decidir si separábamos
  los dos robots por dominio DDS o por espacio de nombres, y elegimos lo segundo.»

**Espacio de nombres** *(namespace)*. Un prefijo que se le pone a todo lo de un robot para que no
choque con el otro: `/robot1/scan` y `/robot2/scan` son dos tópicos distintos aunque los dos sean
«el láser». **Es la solución que reemplazó a los dos dominios.**

**TF / marcos de referencia.** Un sistema que mantiene, en todo momento, **dónde está cada cosa
respecto a cada otra**. Los tres marcos que tienes que saber:
- **`map`** — el mundo fijo. El origen del mapa.
- **`odom`** — un marco que se mueve suavemente pero **acumula error**.
- **`base_link`** — el robot mismo.
- La transformada **`map → odom` es la corrección que aplica la localización**. Cuando en el
  registro ves `deriva_map_odom_m`, eso es *cuánto tuvo que corregir el sistema*, o sea una medida
  de cuánto se había equivocado la odometría.

**Bag** *(rosbag)*. Una grabación de todo lo que pasó por los tópicos durante una corrida. Es la
caja negra: se graba la misión y después se analiza en frío, sin volver a correr nada. **Todas las
cifras de la campaña salen de bags, no de mirar la pantalla.**

**rosbridge.** Un puente que expone ROS por **WebSocket**, que es el protocolo que un navegador sí
entiende. Es lo que permite que **una página web hable con el robot sin instalar nada**. Es la base
técnica de la HRI.

### 1.2 Navegación

**LiDAR.** Sensor que gira y mide distancias con láser. Devuelve un «barrido»: cientos de
distancias, una por ángulo. Se publica en el tópico **`/scan`**.

**Odometría (`/odom`).** La estimación que el robot hace de cuánto se ha movido, a partir de sus
propios sensores. **Se equivoca acumulativamente**: cuanto más recorre, más se desvía.
- Detalle del proyecto: el DeepRacer real **no tiene encoders en las ruedas**, así que la odometría
  se calcula comparando barridos consecutivos del láser (*odometría láser*, `rf2o`).

**SLAM.** *Localización y mapeo simultáneos*: construir el mapa mientras te ubicas en él. Es como
se produjo el mapa del entorno. **En este proyecto el mapa es un insumo, no un producto**: se hace
una vez y después las misiones lo usan ya hecho (eso es la restricción RNF-07).

**AMCL.** *Localización de Monte Carlo adaptativa*. Ya con el mapa hecho, es lo que responde «¿en
qué punto del mapa estoy?». Funciona lanzando muchas hipótesis (partículas) sobre dónde podría
estar el robot y descartando las que no cuadran con lo que ve el láser.

**Nav2.** La pila de navegación de ROS 2: recibe «ve a este punto», planifica una ruta, la sigue,
esquiva obstáculos y avisa si llega o falla. **El coordinador le habla a Nav2, no a los motores.**

**Mapa de costos** *(costmap)*. Una rejilla donde cada celda dice lo cara que es de pisar. Los
obstáculos valen infinito; sus alrededores valen mucho. El **local** es una ventana pequeña que
sigue al robot y sirve para esquivar lo que aparece.

**Cinemática Ackermann.** La dirección de un carro de verdad: ruedas delanteras que giran, tracción
detrás. **Consecuencia crítica: no puede girar sobre su propio eje y tiene un radio mínimo de
giro.** Un robot diferencial (como un Roomba) sí puede. Esto restringe todas las trayectorias y por
eso es una restricción declarada (RNF-05).

**Gazebo.** El simulador. `gzserver` es la parte que calcula la física.

**RTF** *(factor de tiempo real)*. Cuántos segundos de simulación pasan por cada segundo real. **Si
el RTF cae por debajo de 1, la simulación va lenta y todas las medidas de tiempo quedan
distorsionadas.** Por eso el proyecto exige RTF ≥ 0,99 (RNF-06) y lo registra en cada misión: es lo
que hace que las métricas temporales sean creíbles.

**`/clock`.** En simulación el tiempo no lo da el reloj del computador sino un tópico, `/clock`,
que Gazebo publica **10 veces por segundo**. Consecuencia: **el reloj de la simulación avanza a
saltos de 100 ms.** Esto explica un resultado importante de la §3.

### 1.3 El vocabulario propio del proyecto

**OE — Objetivo específico.** Los cuatro compromisos del anteproyecto. Son la unidad en la que se
mide el avance y **es lo que el jurado va a evaluar**.
| | |
|---|---|
| **OE1** | Modelar la arquitectura funcional |
| **OE2** | Construir la plataforma con dos vehículos |
| **OE3** | Programar la interfaz humano–robot |
| **OE4** | Evaluar el desempeño con métricas |

**RF — Requisito funcional.** *Qué debe hacer el sistema*, escrito de forma que se pueda comprobar.
Están numerados RF-01 a RF-27 en `REQUISITOS.md`, y **cada uno está amarrado a un objetivo**:
RF-01…RF-10 son de OE1, RF-11…RF-16 de OE2, RF-17…RF-20 de OE3, RF-21…RF-27 de OE4.
- Cada RF tiene cuatro cosas: el **requisito**, la **prueba** que lo demuestra, el **estado**
  (verificado / parcial / pendiente) y la **semana** en que se cierra.
- **Por qué existe esta matriz:** convierte «el proyecto va bien» en «23 de 34 requisitos están
  verificados, y estos son los que faltan y por qué». Es lo que hace defendible un porcentaje.
- **Si te preguntan «¿qué es un RF?»:** «Un requisito funcional: una capacidad concreta y
  comprobable que el sistema debe tener. Los trazamos todos contra los objetivos del anteproyecto,
  para que ningún objetivo quede sin requisitos y ningún requisito esté inventado.»

**RNF — Requisito no funcional, o restricción.** No son cosas que el sistema *haga*, sino
**condiciones y límites** bajo los que opera, y **hay que poder demostrar que se respetaron**.
Ejemplos: ningún robot cruza entre pisos (RNF-01), las trayectorias son Ackermann (RNF-05), la
simulación corre a tiempo real (RNF-06).

**Coordinador.** El nodo central. Recibe la solicitud del usuario, **decide qué robot la atiende**,
la parte en tramos y va publicando el estado. No conduce: manda por `navigate_to_pose`.

**Relevo.** El aporte del proyecto. Si origen y destino están en pisos distintos, el robot del piso
de origen guía hasta el **punto de transferencia** (el descanso de la escalera), y ahí **el robot
del otro piso toma la misión y la continúa**. El usuario sube solo; los robots no.

**Punto de transferencia.** El lugar físico donde ocurre el relevo. Cada piso tiene el suyo.

**Catálogo de puntos de interés.** El archivo `puntos_interes.yaml` con los **31 destinos**, cada
uno con su nombre, su piso y su coordenada. Es lo que la interfaz muestra en las dos listas.

**Condición A y condición B.** Los dos tipos de misión de la campaña:
- **A** — origen y destino en el mismo piso. **Sin relevo.** Es el *control*.
- **B** — origen y destino en pisos distintos. **Con relevo.** Es lo que se quiere probar.
- 15 misiones de cada una. **Sin la condición A no se puede afirmar nada sobre la B**: es la que
  dice cómo se comporta el sistema cuando el aporte no interviene.

---

## 2. Los porcentajes de la diapositiva 2, y de dónde salen

Cada porcentaje sale de `ESTADO.md` y refleja cuántos requisitos del objetivo están verificados y
cuánto pesa lo que falta. **Los cuatro están verificados contra el repositorio.**

| | % | Qué está hecho | Qué falta, dicho con precisión |
|---|---|---|---|
| **OE1** | 80 % | Arquitectura, 34 requisitos trazados, contrato de interfaces, coordinador funcionando | **RF-08**: cada robot debe publicar su propio estado a 2 Hz y **no existe el nodo que lo publique**. Además, compilar los mensajes en la tarjeta del carro |
| **OE2** | 55 % | Un DeepRacer instrumentado: LiDAR real medido, control desde ROS 2, mapeo de servo probado | **El segundo vehículo, en reparación (R11)**; y calibrar la escala de velocidad |
| **OE3** | 35 % | Interfaz construida y probada en vivo contra el coordinador real | Probarla desde un teléfono físico y hacer un guiado completo con relevo desde ella |
| **OE4** | 85 % | Campaña de 30 misiones sorteada, ejecutada y analizada | La campaña **física** (N = 5–10) y redactar el capítulo |

**63,75 %** = (80 + 55 + 35 + 85) ÷ 4. Promedio simple, sin ponderar. **65,6 %** = 21 semanas de 32.
El mensaje es que van casi parejos: **2 puntos de diferencia**.

> **Por qué OE3 está en 35 % si la interfaz ya funciona.** Porque el objetivo no es «tener una
> interfaz», es tener el guiado operando desde ella de punta a punta. Está construida y verificada
> contra el coordinador, pero **todavía no ha guiado una misión real con relevo**. Si te preguntan
> por qué tan bajo, esa es la respuesta — y es a favor tuyo, porque demuestra que no inflaron el
> número.

---

## 3. Las cuatro métricas de OE4, una por una

El objetivo 4 del anteproyecto nombra literalmente cuatro métricas. **Cada una tiene su requisito y
su definición operativa escrita antes de medir**, en `PROTOCOLO_EXPERIMENTAL.md` §3.

### RF-21 · Tiempo de respuesta
**Qué es:** desde que el usuario pide el guiado hasta que el robot **se mueve por primera vez**.
**Resultado:** mediana **0,2 s** sobre las 30 misiones (rango 0,1–0,4 s).
**El matiz:** el reloj de simulación avanza de 100 ms en 100 ms, así que 0,2 s son **dos tics** y la
cifra no admite más de un decimal.

### RF-22 · Tiempo de asignación — *la que tiene truco*
**Qué es:** desde la solicitud hasta que el coordinador **ha decidido qué robot la atiende**.
**El problema:** medida sobre el bag, esta resta da **exactamente 0,0 s en las 30 misiones**. No
porque el sistema sea infinitamente rápido, sino porque **decidir tarda unos 150 microsegundos y el
reloj solo avanza cada 100 milisegundos**: las dos marcas caen en el mismo tic. *Eso no mide el
evento, mide el reloj.*
**La solución:** se montó un **banco aislado** que corre solo el coordinador y cronometra por
dentro con un reloj de nanosegundos. Cuatro corridas de 30 repeticiones cada una.
**Resultado:** mediana **entre 154 y 175 µs**, máximo **306 µs** — unas **326 veces menor que un tic
del reloj**.
**Por qué contarlo:** es el ejemplo más fuerte de rigor que tienes. Detectaste que **tu propio
instrumento no podía medir una de tus métricas** y construiste otro. Si te preguntan por el rigor
del trabajo, esta es la historia que hay que contar.

### RF-23 · Tasa de éxito
**Qué es:** cuántas misiones terminaron bien. **«Bien» estaba definido antes de medir:** llegar a
**menos de 0,25 m** del destino, medido **contra la posición real del robot y no contra el
`SUCCEEDED` que devuelve Nav2** — porque Nav2 puede darse por bueno a sí mismo.
**Resultado:** **26 de 30 = 86,7 %**, IC95 **70,3–94,7 %**.
**Los 4 fallos:** todos del mismo tipo, llegadas cortas entre 0,284 y 0,347 m. **Ninguno falló por
la coordinación ni por el relevo.**

### RF-24 · Continuidad entre niveles — *la principal*
**Qué es:** que durante toda la misión **nunca haya un instante sin robot activo**. Es lo que
distingue un relevo de una interrupción.
**Resultado:** **14 de 14 = 100 %**, IC95 78,5–100 %. El salto en el momento del relevo tiene una
mediana de **0,100 s**, que es **un solo tic del reloj**, o sea el mínimo que el instrumento puede
distinguir.
**Por qué evalúa 14 y no 15:** una de las 15 misiones con relevo nunca llegó a completarse, y medir
continuidad sobre una misión fallida sería medir otra cosa.
**Esta es la variable que responde la pregunta de investigación.** Si solo te dejaran decir un
número, es este.

---

## 4. Qué decir en cada diapositiva

### Diapositiva 1 — Portada
**Menciona:** que son dos vehículos, uno por piso, que se turnan la guía; que **ningún robot sube
escaleras**, la transición es del protocolo.
**Señala el diagrama:** el punto naranja entrega al verde en el descanso.
**Cierra con los dos números juntos:** 65,6 % de calendario contra 63,75 % de avance. *«Vamos
parejos con el cronograma.»*

### Diapositiva 2 — Objetivos
**No leas las doce líneas.** Di la estructura una vez —«cada tarjeta trae resultado, evidencia y lo
que falta»— y después **dedica el tiempo a OE4 (85 %) y a OE2 (55 %)**, que son el punto alto y el
punto bajo.
**La frase que amarra:** *«El objetivo más avanzado es el de evaluación, y el menos avanzado es el
de plataforma, porque depende de un vehículo que está en reparación. No es un problema de trabajo
pendiente, es de disponibilidad.»*

### Diapositiva 3 — Resultados ⭐ *la importante*
Orden sugerido:
1. **Qué se hizo:** 30 misiones sorteadas al azar, ejecutadas los días 4 y 5 de septiembre, **0
   descartes**.
2. **El número principal: continuidad 100 %.** No empieces por el 86,7 %; empieza por la variable
   que responde la pregunta.
3. **Después la tasa de éxito, dicha con su intervalo:** *«86,7 %, con un intervalo de confianza
   del 95 % entre 70 y 95 por ciento.»* Nunca el punto solo.
4. **El recuadro de Wilson:** explícalo como método, no como fórmula. *«Elegimos el intervalo de
   Wilson porque con 30 datos el método clásico falla. Y está escrito en el protocolo desde antes
   de medir, así que no elegimos la estadística después de ver el resultado.»* **Esa última frase
   es la que más peso tiene de toda la presentación.**
5. La interfaz y el video, breves.

### Diapositiva 4 — Documento final
**Lo importante son las tres desviaciones de la columna derecha.** Preséntalas tú, con naturalidad:
*«Hay tres cosas en las que nos apartamos del anteproyecto, las identificamos por escrito y venimos
a pedir aval.»*
- **DonkeyCar → AWS DeepRacer:** justifica con que era la plataforma disponible y cumple lo mismo.
- **App móvil → web responsiva por QR:** el requisito era seleccionar origen y destino sin
  instalar nada; la web lo cumple **mejor**, porque no exige instalación.
- **Campaña de dos niveles en simulación:** es la consecuencia del segundo vehículo averiado.

### Diapositiva 5 — Riesgo
**Un solo mensaje:** el riesgo es de hardware, no de esfuerzo. **R11 no bloquea esta semana pero sí
bloquea S23.** Di la fecha: sin caracterizar desde el 14 de agosto.

### Diapositiva 6 — Compromiso
Léela casi literal: las dos frases del recuadro están redactadas para contestar exactamente lo que
se pregunta en un control de avances.

---

## 5. Preguntas trampa y cómo se contestan

**«¿Su sistema funciona el 86,7 % de las veces?»**
No como cifra firme. **Con 30 repeticiones lo defendible es "la tasa supera el 70 %"**; el 86,7 % es
el centro de un intervalo que llega hasta 95. *Esto ya está escrito así en el repositorio* — si lo
dices tú antes de que te lo señalen, suma.

**«Las misiones con relevo salieron mejor (93,3 %) que las de un solo piso (80 %). ¿Por qué?»**
**No inventes una explicación.** La respuesta correcta: *«Esa diferencia no sostiene ninguna
conclusión: los intervalos de confianza se solapan y además apunta en contra de lo intuitivo. Con
este tamaño de muestra no podemos afirmar que una condición sea mejor.»*

**«¿Por qué fallaron las cuatro misiones?»**
Un solo modo de fallo: llegadas cortas, entre 0,284 y 0,347 m contra un criterio de 0,25 m. Es un
fenómeno del pasillo ya caracterizado. **Ninguna falló por la asignación ni por el relevo**, que es
lo que aporta el proyecto.

**«¿Por qué no volvieron a correr las que fallaron?»**
Porque sería sesgo de selección. Una misión que llega fuera del criterio **es un resultado**, no un
error de medición. Solo se repite una corrida si **el instrumento** falló, no si el resultado no
gustó.

**«¿Esto es simulación? ¿Sirve de algo?»**
Sí, y lo decimos abiertamente. La campaña de 30 es en simulación; la física es N = 5 a 10 y es lo
que falta. Pero el trabajo con hardware **ya empezó y está medido**: el LiDAR real verificado contra
flexómetro, el control desde ROS 2 funcionando, la odometría láser caracterizada con su error.

**«¿Qué algoritmo de coordinación usan?»**
La asignación es **de una tarea a un robot, un robot a la vez, con asignación instantánea**
(ST–SR–IA en la taxonomía de Gerkey y Matarić). Coincide con el óptimo porque la restricción de
piso deja **un solo candidato admisible**. El relevo tiene dependencias entre agendas y cae en otra
categoría (XD, de Korsah, Stentz y Dias). Está clasificado formalmente en el anexo del repositorio.

**«¿Por qué dos robots y no uno que suba?»**
Porque un vehículo Ackermann **no sube escaleras**, y el aporte del proyecto es justamente que la
continuidad del servicio se resuelve por **protocolo** y no por movilidad. Es una restricción
declarada (RNF-01), no una limitación descubierta.

**«¿Qué falta para cerrar el objetivo 1?»**
Un requisito: **RF-08**. Cada robot debe publicar su estado a 2 Hz y ese publicador no existe
todavía. Entra antes de la congelación de código.

---

## 6. Lo que hay que saber de memoria

| Cifra | Qué es |
|---|---|
| **S21 de 32 · 65,6 %** | del calendario |
| **63,75 %** | avance técnico (80 · 55 · 35 · 85) |
| **34** | requisitos trazados · **23 verificados** |
| **30** | misiones · **15 A + 15 B** · **0 descartes** |
| **86,7 %** | tasa de éxito · **IC95 70,3–94,7** |
| **100 %** | continuidad entre niveles · **14/14** |
| **31** | puntos de interés en el catálogo |
| **0,25 m** | criterio de llegada |
| **14-ago** | desde cuándo está el segundo carro sin caracterizar |
| **S23 · 14–20 sep** | congelación de código |
| **S28 · 19–25 oct** | sustentación |

---

## 7. Antes de proyectar: tres arreglos al archivo

1. **Diapositiva 3 — el video no está insertado.** El recuadro punteado contiene todavía la
   instrucción *«Espacio reservado. En PowerPoint: Insertar → Vídeo…»*. **Si no se inserta el
   video, ese texto se proyecta.**
2. **Diapositiva 4 — la fecha límite del pie es hoy.** Dice «antes del 6 de septiembre». O ya está
   entregado y conviene redactarlo en pasado, o se está anunciando vencido.
3. **Diapositiva 2 — lo que falta de OE1 está incompleto.** Dice «compilar en la tarjeta física ·
   nombres del piso 2», pero el requisito realmente abierto es **RF-08**. Vale la pena añadirlo,
   porque es la respuesta a una pregunta muy probable.
