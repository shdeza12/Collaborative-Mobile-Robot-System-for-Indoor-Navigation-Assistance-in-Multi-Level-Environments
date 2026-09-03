# Medir M1 y M2: la pasada de localización, paso a paso

Guía de principio a fin para producir las **dos cifras que deciden el G2**: M1 —cuánto
desplazamiento registra la odometría frente al que mide la cinta— y M2 —cuánto se equivoca AMCL
en la marca de llegada—.

Escrita el **2026-09-02**, antes de salir al pasillo, y a propósito: el §6.3 del protocolo
experimental prohíbe fijar el procedimiento y los umbrales después de ver el dato.

**Esta es la SEGUNDA de las dos pasadas.** La primera —[`GUIA_PASADA_MAPEO.md`](GUIA_PASADA_MAPEO.md)—
produce el mapa. Sin ese mapa, esta pasada no existe: AMCL no tiene contra qué localizarse.

---

## Parte 0. Lo que hay que entender antes de tocar nada

### 0.1 Qué produce esta pasada

Seis bags de `/scan` —tres por sentido— y, de cada uno, dos números:

| | Qué es | Cómo sale |
|---|---|---|
| **M1** | Desplazamiento que registra `/odom` ÷ desplazamiento real medido con cinta | `rf2o` fuera de línea sobre el bag, entre las dos paradas |
| **M2** | Error de `/amcl_pose` contra la marca de cinta al final de la recta | AMCL fuera de línea contra el mapa de la primera pasada |

Nada más. Aquí no se navega de forma autónoma: **eso es el G1 y es otra prueba**. El G2 mide
localización, que es lo que el laboratorio de 4 × 4 m no puede decidir.

### 0.2 Por qué el carro sigue grabando solo `/scan`

Es la misma **cadena B** de la primera pasada, y por las mismas dos razones: está comprobada de
extremo a extremo en el portátil, y se puede repetir sobre el mismo bag sin volver al pasillo.

Lo que cambia respecto a la primera pasada es solo qué se le pone al final de la cadena:

```
primera pasada:   bag /scan  ->  rf2o  ->  slam_toolbox  ->  mapa.pgm
segunda pasada:   bag /scan  ->  rf2o  ->  AMCL + mapa.pgm  ->  /odom y /amcl_pose
```

El carro no publica `/odom`, `/tf` ni `/tf_static` —comprobado el 2026-09-01 contra la lista
estable de 22 tópicos—, así que grabarlos no es una opción que se esté descartando: **no existe**.

> **Lo que esto sí concede, y hay que declararlo en el informe.** AMCL fuera de línea sobre un bag
> reproducido **no es idéntico** a AMCL en vivo:
>
> 1. El portátil es más rápido que la tarjeta del carro, así que fuera de línea AMCL nunca se queda
>    sin ciclos. **La cifra que sale es una cota optimista** del rendimiento en tiempo real.
> 2. El filtro de partículas es estocástico: dos corridas sobre el mismo bag dan resultados
>    parecidos, no iguales. Por eso el Paso 5.3 lo corre **tres veces** y se queda con la mediana.
> 3. `rf2o` deduce `/odom` de los mismos barridos con los que AMCL se localiza, de modo que la
>    «odometría» y la «observación» comparten sensor y sus errores están correlacionados. **Esto no
>    lo introduce el ir fuera de línea**: el DeepRacer no lleva encoders de rueda, así que en el
>    carro pasa exactamente igual. Es una propiedad de la plataforma y se declara como limitación.

### 0.3 Aquí se conduce, y no se empuja

Al revés que en la primera pasada. El §0.4 de la guía de mapeo lo deja dicho y la razón es medible:
a 6,6 Hz, empujando a 0,5 m/s hay ~7 cm entre barridos consecutivos, y conduciendo a 1,5 m/s hay
~21 cm. **Más solape es más fácil para el algoritmo.** Si esta pasada se empujara, M1 y M2 no
dirían nada del vehículo: dirían lo que rinde el algoritmo con un sensor movido a mano.

Se conduce con el mando por USB, siguiendo [`GUIA_TELEOP_MANDO.md`](GUIA_TELEOP_MANDO.md). Todo
como `root`, por lo del `/dev/shm` que esa guía explica en su §0.2 ter.

### 0.4 Por qué van los dos sentidos, y no uno

Porque el error no es simétrico y está medido. El 2026-08-26, `rf2o` corrido fuera de línea contra
la verdad de terreno de Gazebo sobre el mismo pasillo simulado:

| Sentido | Real | Registrado por `rf2o` | Error |
|---|---|---|---|
| Este | 29,94 m | 28,23 m | **5,7 %** |
| Oeste | 24,98 m | 24,65 m | **1,3 %** |

Un factor de cuatro entre una dirección y la otra. **Con una sola pasada sacas uno de esos dos
números y no sabes cuál te tocó.** Van los dos sentidos, y se informan por separado; no se
promedian, porque promediar los borra.

### 0.5 Por qué van tres por sentido

Con una sola pasada por sentido no se distingue «5,7 % siempre» de «a veces 1 %, a veces 10 %», y
esa distinción es justo la que decide si el umbral significa algo. Tres da un rango, no una
desviación típica creíble, pero separa esas dos historias, y cuesta menos de cinco minutos de
conducción.

**Regla dura:** no se recoge la cinta con menos de **un bag válido por sentido**. Si la mañana se
va, se va con dos bags, no con cero.

### 0.6 Se usa la recta entera, no 20 m recortados

El criterio del G2 dice «≥ 20 m». Eso es un **mínimo**, no un objetivo. Se corre sobre la recta
completa que dé el pasillo.

Esto merece una frase de honestidad, porque va en contra del resultado: **cuanto más larga es la
recta, más difícil es pasar M2.** Al 2,9 % de sesgo medido, 20 m dan 0,58 m de error y 40 m dan
1,16 m. Recortar a 20 m sabiendo eso sería elegir la geometría para que la prueba salga mejor, que
es la misma falta que fijar el umbral después de ver el dato. Se corre sobre lo que hay, y si sale
mal se anota que salió mal.

> **Estación intermedia de 20 m.** Si la recta mide **≥ 25 m**, se marca además el punto de 20 m y
> el carro **para 5 s ahí** en cada pasada. Sale gratis y del mismo bag salen M1 y M2 evaluados a
> 20 m **y** a la longitud completa, lo que permite comparar contra el criterio tal como está
> escrito sin dejar de correr sobre la recta entera.

### 0.7 Lo que necesitas a mano

- Todo lo de la primera pasada, que se hace justo antes y el mismo día.
- **El mapa de la primera pasada, ya aceptado.** Sin él esta pasada no arranca.
- **El mando**, con su cable USB-C, ya conectado al carro desde la primera pasada.
- Cinta de enmascarar y marcador. Las marcas son distintas de las de la primera pasada: ver Paso 2.1.
- El carro con batería. Seis pasadas de conducción, no de empuje.

---

## Parte 1. En el escritorio, antes de salir

### Paso 1.1 — Comprobar que las herramientas de esta pasada existen

**[PORTÁTIL]**, desde la raíz del repositorio:

```bash
ls -1 herramientas/localizar_desde_bag.sh herramientas/medir_g2.py
```

**Esperado:** las dos rutas, sin `No such file`.

**Si falta alguna:** no salgas al pasillo. Son las que convierten el bag en M1 y M2, y sin ellas
vuelves con seis carpetas y ningún número. Están descritas en el **Apéndice B** de esta guía.

Aprovecha y corre la prueba pura de la segunda, que no necesita ROS ni bag y tarda un segundo:

```bash
python3 herramientas/prueba_medir_g2.py
```

**Esperado:** `Todas pasan.` tras 21 comprobaciones.

### Paso 1.2 — Comprobar la cadena de localización contra el mapa simulado

**El equivalente del Paso 1.2 de la guía de mapeo: correr la cadena entera sobre algo que ya
tienes, antes de que dependa de ella la mañana.**

```bash
herramientas/localizar_desde_bag.sh /tmp/mapeo /tmp/mapa_pasillo/mapa.yaml /tmp/loc_prueba --topico /rplidar_ros/scan
```

**Esperado:** termina con `Trayectoria en /tmp/loc_prueba/trayectoria.csv` y un recuento de poses
de `/amcl_pose` mayor que cero.

> **Mira en qué tópico publica tu bag antes de lanzarlo**, con
> `ros2 bag info /tmp/mapeo | grep -i scan`. Los bags del 28-ago traen `/rplidar_ros/scan`; si el
> tuyo trae `/scan` a secas, quita el `--topico`. Puesto al revés, rf2o se queda esperando un
> barrido que nunca llega y la corrida sale entera sin una sola pose.

**Por qué se hace con el bag de mapeo:** es el único bag real del pasillo que tendrás antes de la
primera pasada del viernes. No sirve para el G2 —se empujó, no se condujo— pero **sirve para
comprobar que la cadena no aborta**, que es de lo que trata este paso.

**Si `/amcl_pose` sale vacío:** AMCL no recibió barridos o no arrancó su ciclo de vida. Mira
`amcl.log`. Es exactamente el fallo que esta guía existe para que no descubras en el pasillo.

### Paso 1.3 — Dejar decididos M1 y M2 **por escrito**

**Este paso no es opcional y no es de código.** El §6.3 del protocolo prohíbe fijar umbrales
después de ver el dato, y en este caso el dato ya se puede predecir, lo que agrava la cosa. El §4
de [`Evidencia/S21_preparacion_G2.md`](Evidencia/S21_preparacion_G2.md) demuestra dos cosas:

1. **M1, tal como está escrito, no puede fallar.** Es un umbral de un solo lado —`≥ 0,90`— que
   tolera un 10 % cuando el peor error jamás medido es 5,7 %. Y el sesgo del carro es **+2,9 %
   largo**, o sea que pasa por construcción; pasaría igual con un +50 %.
2. **El resultado de M2 ya está calculado.** 0,029 × 20 m = **0,58 m > 0,50 m**.

Hay que llevar contestadas estas tres preguntas, y llevarlas **firmadas por el director**:

| | Pregunta | Propuesta que se lleva |
|---|---|---|
| **a** | ¿M1 pasa a dos lados? | Sí: `\|registrado ÷ real − 1\| ≤ 0,10`. Es el mismo 10 % de tolerancia, aplicado también al exceso |
| **b** | Si M2 falla, ¿sobre qué ramifica el GO/NO-GO? | Que M2 falle **no** para el proyecto: R3 ya está documentado y ya se decidió no construir la corrección ahora. Debe ramificar sobre qué se declara verificado, no sobre si se sigue |
| **c** | ¿M2 sigue siendo puerta, o pasa a ser medida? | La pregunta abierta de verdad es **cuánto recupera AMCL con geometría real** frente al pasillo simulado, que es una extrusión perfecta. Como puerta con veredicto conocido no gatea nada; como medida contesta algo que nadie sabe |

**Criterio de cierre:** las tres contestadas y escritas en el repositorio **antes** de salir. Si no
lo están, la pasada se toma igual —los bags valen— pero el G2 **no se declara**.

---

## Parte 2. En el pasillo: las marcas

La primera pasada ya midió y marcó. Esta añade lo que M1 y M2 necesitan y aquella no.

### Paso 2.1 — Convertir las marcas de línea en marcas de punto

**Por qué hace falta.** Las marcas de la primera pasada son **estaciones longitudinales**: dicen a
cuántos metros estás. M2 mide un error en **2D**, así que el carro tiene que parar en un **punto**
repetible, no en una línea.

En cada extremo de la recta —el 0 m y el final— marca una **cruz**:

1. **El trazo transversal** es la marca de metros que ya tienes.
2. **El trazo longitudinal** son ~60 cm de cinta a lo largo del eje del pasillo, cruzando el
   anterior. Sirve para dos cosas a la vez: dice dónde para el carro **a lo ancho**, y da la línea
   con la que alinear el chasis a ojo.
3. **Céntrala.** Mide del muro a la cruz en los dos extremos y **anota los dos números**. Si no
   coinciden, la recta que vas a conducir está en diagonal respecto al pasillo, y eso mete un error
   lateral que se le va a cargar a AMCL sin ser suyo.

Si la recta mide ≥ 25 m, marca la **tercera cruz a los 20,00 m** exactos desde el 0 m.

**Anota la longitud total con dos decimales.** Es el denominador de M1 y el punto de referencia de
M2; todo lo demás se puede repetir y este número no.

### Paso 2.2 — Comprobar que el mapa y las marcas hablan del mismo sitio

El mapa de `slam_toolbox` nace con su origen **donde arrancó el SLAM**, y AMCL trae
`set_initial_pose: True` con `(0, 0, 0)` en
`config/nav2_params_nav_amcl_sim_demo.yaml`.

**Si la primera pasada arrancó sobre la cruz de 0 m mirando al fondo del pasillo**, entonces el
`(0, 0, 0)` del mapa **es** esa cruz, con la x apuntando pasillo abajo, y la pose inicial de AMCL
sale correcta sin tocar nada.

Compruébalo antes de conducir:

```bash
grep origin /tmp/mapa_pasillo/mapa.yaml
```

y ábrelo:

```bash
eog /tmp/mapa_pasillo/mapa.pgm
```

**Esperado:** el pasillo se ve como un tubo largo, y el extremo por el que empezaste queda hacia el
lado del origen.

**Si la primera pasada no arrancó en la cruz:** no repitas nada. Anota la pose de arranque real
—dónde estaba el carro respecto a la cruz de 0 m— y pásala como `--pose-inicial` en el Paso 5.2.
Es un desplazamiento constante, se resta y ya está. Lo que no se puede es **no saberlo**.

> **Esto obliga a un cambio en la primera pasada.** El Paso 3.1 de
> [`GUIA_PASADA_MAPEO.md`](GUIA_PASADA_MAPEO.md) dice «coloca el carro» sin decir dónde. A partir
> de esta guía dice: **sobre la cruz de 0 m, mirando al fondo de la recta**. No cuesta nada y
> ahorra tener que estimar una pose inicial después.

### Paso 2.3 — Montar el mando y comprobar que el carro obedece

Sigue [`GUIA_TELEOP_MANDO.md`](GUIA_TELEOP_MANDO.md), Partes 1 a 5. Resumen de lo que no se puede
olvidar:

- El mando va **por USB al carro**, no por Bluetooth al portátil.
- **Todo con `sudo`.** Sin él arranca todo, no da ni un error, y el carro no se mueve.
- **No desconectes ni conectes el USB con la pila arrancada**: el bus se re-enumera, `/dev/ttyUSB0`
  se borra y se vuelve a crear, y `rplidar_node` se queda con un descriptor a un fichero borrado.
  `systemctl` sigue diciendo `active (running)`. Es la tercera vez que el `active` miente.
- **Nunca reinicies el carro.** Se queda en GRUB esperando que alguien elija sistema, y en el
  pasillo no hay monitor.

**Criterio de cierre:** el carro avanza, retrocede y gira con el mando, y el LiDAR sigue publicando
en `/scan` después de haberlo comprobado.

---

## Parte 3. Las pasadas

Seis, en este orden: **ida, vuelta, ida, vuelta, ida, vuelta**. Alternar los sentidos en vez de
hacer tres seguidas de cada uno reparte el efecto de la batería, que baja a lo largo de la mañana,
entre los dos sentidos en vez de castigar solo al segundo.

### Paso 3.1 — Colocar el carro

Sobre la cruz de salida, con **el LiDAR encima del cruce de los dos trazos** y el chasis alineado
con el trazo longitudinal.

> **Por qué el LiDAR y no las ruedas.** La TF compuesta `base_link → laser` es
> `x = 0,02913, z = 0,184699, yaw = π`: el sensor está **2,9 cm** delante del origen del robot.
> Frente a un umbral de 0,50 m eso es despreciable, así que alinear el sensor a ojo desde arriba es
> más que suficiente y evita tener que saber dónde cae `base_link` sobre el chasis.

La alineación de rumbo a ojo sale a **±3°**, y es tolerable: AMCL corrige el rumbo bien —2,8° de
error final en la corrida del 26-ago— y M1 mide una **magnitud** de desplazamiento, que no depende
del rumbo inicial.

### Paso 3.2 — Empezar a grabar, y esperar quieto

**[CARRITO — SSH]**

```bash
sudo -i bash -c "source /opt/ros/jazzy/setup.bash && cd ~deepracer && ros2 bag record /scan -o g2_SENTIDO_N"
```

Sustituye `SENTIDO` por `ida` o `vuelta` y `N` por 1, 2 o 3. Anota el nombre.

**Esperado:** `Recording...` y `Subscribed to topic '/scan'`.

**Con el `sudo` no se negocia**, y no es la misma razón que en el teleop: es que sin él el
participante no puede escribir en `/dev/shm/fastrtps_port700*`, nunca existe para el resto del
grafo, y `ros2 bag record` imprime `Recording...` igual mientras graba un fichero vacío.

**Ahora espera 5 segundos con el carro completamente quieto.** No es una formalidad:

> **Para qué sirven los 5 s.** Son la **ventana de referencia** de la que se leen el origen de M1 y
> la pose inicial. Sin una parada declarada, el análisis tiene que adivinar en qué mensaje empieza
> la pasada, y ahí se cuelan decímetros. Con la parada, el Paso 5.2 la detecta sola: la misma
> heurística de `comprobar_movimiento_bag.py` que ya distingue sensor quieto de sensor en
> movimiento.

### Paso 3.3 — Conducir

Con el gatillo, hasta la cruz del otro extremo.

- **Velocidad constante y sin turbo.** Con `limite_normal` en 0,35 basta. Lo que importa no es ir
  rápido, es que las tres pasadas del mismo sentido se parezcan entre sí.
- **Sin paradas** salvo la de los 20 m, si la marcaste.
- **No corrijas a lo bruto.** Un volantazo mete rotación que rf2o sí observa bien, pero también
  mete deslizamiento del Ackermann que no.
- **Si estás a punto de chocar, suelta el gatillo y anota que la pasada se abortó.** Un bag abortado
  cuesta 40 segundos. Un carro roto cuesta el proyecto.

**Si marcaste los 20 m:** para 5 s justo encima de la cruz intermedia y sigue.

### Paso 3.4 — Parar en la cruz, esperar quieto, y cerrar

1. Para con **el LiDAR encima del cruce**. Ajústalo empujando a mano si hace falta: lo que se mide
   es dónde cree AMCL que está, no lo bien que conduces.
2. **Espera 5 segundos quieto**, con la grabación todavía corriendo. Es la ventana de llegada, de
   donde salen los dos números.
3. Cierra con **`Ctrl-C` una sola vez** y espera a que devuelva el prompt.

> **Por qué una sola vez.** El índice y la `metadata.yaml` se escriben **al cerrar limpio**. A
> `bag_mapa_1456`, del 28-ago, le falta la metadata entera por esto, y sin ella el bag no se puede
> reproducir. Un segundo `Ctrl-C` mata el proceso antes de que termine de escribirla.

### Paso 3.5 — Anotar la pasada

En papel o en el móvil, según se hace. Una línea por pasada:

```
g2_ida_1     sentido: 0 m -> 24,80 m    salida 10:14    abortada: no    incidencias: -
```

Las incidencias importan: alguien cruzándose, una rueda que se subió a un zócalo, una pausa. En el
análisis, un valor raro con una nota al lado es un dato; sin la nota es basura.

---

## Parte 4. Comprobar en el sitio, antes de recoger

Igual que en la primera pasada: **con el carro todavía en el pasillo y la cinta todavía puesta**.

Se hace **después de la primera ida y la primera vuelta**, no al final. Si algo está mal, lo
descubres con dos bags perdidos y no con seis.

### Paso 4.1 — Traer los dos primeros bags y adaptarlos

**[PORTÁTIL]**

```bash
scp -r deepracer@<IP>:~/g2_ida_1 deepracer@<IP>:~/g2_vuelta_1 /tmp/
```

> **El bag lo escribió `root`, y lo copia el usuario `deepracer`.** Funciona porque `root` crea la
> carpeta con permisos `755`, legibles por todos — es el mismo mecanismo que hizo que los buzones
> de `/dev/shm` fueran legibles pero no escribibles, visto del otro lado. **Si `scp` responde
> `Permission denied`**, no pelees con los permisos en el pasillo: en el carro,
> `sudo chown -R deepracer ~deepracer/g2_ida_1` y vuelve a intentarlo. Cambia el dueño en sitio, sin
> copiar nada.

```bash
python3 herramientas/adaptar_bag_jazzy.py /tmp/g2_ida_1 -o /tmp/g2i1 && python3 herramientas/adaptar_bag_jazzy.py /tmp/g2_vuelta_1 -o /tmp/g2v1
```

**Esperado:** `metadata.yaml reescrita a version 5` en los dos. El carro escribe la metadata en
versión 9 y Humble solo lee la 5.

### Paso 4.2 — Comprobar que el sensor se movió, y que las dos paradas están

```bash
python3 herramientas/comprobar_movimiento_bag.py /tmp/g2i1
```

**Esperado:** `SIRVE`, tópico `/scan`, y un porcentaje de quieto **bajo pero no cero**. Cero quieto
significa que te faltaron las paradas de 5 s, y sin ellas el Paso 5.2 no tiene de dónde leer.

| Lo que dice | Qué pasó | Qué hacer |
|---|---|---|
| `NO SIRVE` | El sensor no se trasladó | Repite. Probablemente grabaste sin conducir |
| `0 %` quieto | Faltan las ventanas de referencia | Repite con las dos paradas de 5 s |
| `AVISO: no es '/scan'` | El LiDAR arrancó por la vía de AWS | Paso 2.3 de la guía de mapeo |
| Duración muy corta | Cerraste antes de la parada de llegada | Repite |

### Paso 4.3 — Sacar M1 y M2 de esos dos, allí mismo

```bash
herramientas/localizar_desde_bag.sh /tmp/g2i1 /tmp/mapa_pasillo/mapa.yaml /tmp/loc_i1 && python3 herramientas/medir_g2.py /tmp/loc_i1/trayectoria.csv --largo 24.80
```

**Esperado:** dos cifras con sus componentes, del estilo:

```
  ventana de salida : 0,0 - 5,2 s     (28 barridos quietos)
  ventana de llegada: 41,8 - 47,1 s   (35 barridos quietos)

  M1  desplazamiento odom 25,52 m / real 24,80 m  =  1,029
  M2  amcl (25,38 , 0,11)  vs  marca (24,80 , 0,00)  =  0,59 m
      componente longitudinal 0,58 m   lateral 0,11 m
```

**Este paso no decide si repites.** Decide si la **cadena** funciona. Un M2 alto es un resultado,
no un fallo de procedimiento; que el guion no encuentre las ventanas, o que `/amcl_pose` salga
vacío, sí lo es.

**Criterio de cierre para recoger la cinta:** al menos un bag por sentido que pase el Paso 4.2, y
la cadena del 4.3 corriendo de principio a fin sobre uno de ellos.

---

## Parte 5. En el escritorio: los seis bags

### Paso 5.1 — Traerlos todos y adaptarlos

```bash
for b in ida_1 ida_2 ida_3 vuelta_1 vuelta_2 vuelta_3; do scp -r deepracer@<IP>:~/g2_$b /tmp/ && python3 herramientas/adaptar_bag_jazzy.py /tmp/g2_$b -o /tmp/adap_$b; done
```

### Paso 5.2 — Correr la cadena sobre cada uno

**Las idas y las vueltas no se lanzan igual**, y por eso son dos bucles y no uno:

```bash
for b in ida_1 ida_2 ida_3; do herramientas/localizar_desde_bag.sh /tmp/adap_$b /tmp/mapa_pasillo/mapa.yaml /tmp/loc_$b; done
```

```bash
for b in vuelta_1 vuelta_2 vuelta_3; do herramientas/localizar_desde_bag.sh /tmp/adap_$b /tmp/mapa_pasillo/mapa.yaml /tmp/loc_$b --pose-inicial <L>,0,3.1416; done
```

> **Sustituye `<L>` por el largo real medido con cinta.** Las idas no necesitan `--pose-inicial`
> porque el origen del mapa está en la marca de 0 m mirando al fondo, que es exactamente donde
> arrancan: la pose inicial que el fichero de parámetros ya trae, `(0, 0, 0)`, les vale. Las
> vueltas arrancan en el **otro extremo y mirando al revés**, así que hay que decírselo. Si se te
> olvida, AMCL empieza convencido de estar a `L` metros de donde está y **no da error**: da un M2
> enorme que parece un resultado.

Tarda **lo que duraron las pasadas**, sumadas. Se reproduce a velocidad real a propósito: acelerar
con `--rate` hace que AMCL vea menos actualizaciones y el resultado cambia.

> **La trampa que costó una corrida el 2026-09-01 sigue viva aquí, pero cuenta los saltos antes de
> tirar nada.** Si queda un `ros2 bag play` de antes, hay **dos publicadores de `/clock`**, el
> tiempo salta hacia atrás y `tf2` vacía su búfer **una y otra vez** durante toda la corrida. Eso
> sí la invalida. Lo que **no** la invalida es **un solo** `Detected jump back in time` justo al
> arrancar la reproducción: ese es inevitable y sale siempre, porque hasta ese instante los nodos
> van con la hora de pared y el primer `/clock` del bag los manda a la hora en que se **grabó**,
> que es anterior. El guion ya distingue los dos casos y te lo dice; si aun así quieres mirarlo a
> mano, lo que importa es el **recuento**, no la presencia:
>
> ```bash
> grep -c "jump back in time" /tmp/loc_ida_1/*.log
> ```
>
> Uno por log es sano. Decenas, no.
>
> ```bash
> pkill -9 -f "ros2 bag play"; pkill -9 -f rf2o_laser; pkill -9 -f amcl; pkill -9 -f map_server
> ```

### Paso 5.3 — Repetir cada uno tres veces y quedarse con la mediana

AMCL es un filtro de partículas: es estocástico. Dos corridas sobre el mismo bag no dan lo mismo.

```bash
for i in 1 2 3; do herramientas/localizar_desde_bag.sh /tmp/adap_ida_1 /tmp/mapa_pasillo/mapa.yaml /tmp/loc_ida_1_r$i; done
```

**Se informa la mediana de las tres, y también el rango.** Si el rango entre la mejor y la peor de
las tres es comparable al propio umbral, eso **es el resultado**: significa que la localización no
es repetible, y esa es una conclusión más fuerte que cualquier valor puntual.

### Paso 5.4 — La tabla

Una fila por pasada. Esto es lo que va al entregable:

| Bag | Sentido | Real (m) | Odom (m) | **M1** | AMCL llegada | **M2 (m)** | Rango M2 |
|---|---|---|---|---|---|---|---|
| `g2_ida_1` | 0 → L | | | | | | |
| `g2_ida_2` | 0 → L | | | | | | |
| `g2_ida_3` | 0 → L | | | | | | |
| `g2_vuelta_1` | L → 0 | | | | | | |
| `g2_vuelta_2` | L → 0 | | | | | | |
| `g2_vuelta_3` | L → 0 | | | | | | |

**No se promedian los dos sentidos.** El 26-ago hay un factor de cuatro entre uno y otro; el
promedio lo escondería.

### Paso 5.5 — Un número que sale gratis y hacía falta

Del mismo dato sale la **velocidad real** de la pasada: la longitud de la recta dividida por el
tiempo entre las dos ventanas de parada. Es el primer punto medido de la curva
`gatillo → m/s`, que hasta ahora no existe y que hace falta para saber cuánto solape hay entre
barridos consecutivos. Anótalo con el valor de `limite_normal` que usaste.

---

## Parte 6. Guardar en el repositorio

1. Los seis bags **no** van al repositorio: pesan. Van a `~/tesis_evidencia/S21_G2/`, y en el repo
   queda su ruta y su tamaño.
2. Los seis `trayectoria.csv` **sí** van: son texto y son el dato.
3. La tabla del Paso 5.4, en `Documentos/Evidencia/S21_G2_resultados.md`, con la longitud medida,
   los anchos, la hora, y las incidencias del Paso 3.5.
4. **El veredicto, contra los umbrales del Paso 1.3 y no contra otros.**

> **Si M2 falla, se escribe que falla.** Está previsto: el §4 de `S21_preparacion_G2.md` lo
> anticipa desde el 1 de septiembre, R3 está documentado, y ya se decidió no construir la
> corrección ahora. Lo que **no** se puede hacer es mover el umbral al ver el número. Un G2 que
> pasa porque se le movió la vara no informa nada y el §6.3 lo prohíbe.

---

## Parte 7. Si algo va mal

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `/amcl_pose` sale vacío | AMCL no arrancó su ciclo de vida, o no le llegó el mapa | Mira `amcl.log`. Si no dice `Received a X x Y map`, el `map_server` no publicó |
| AMCL «salta» al principio y luego se estabiliza | La pose inicial `(0,0,0)` no era la cruz de 0 m | Paso 2.2. Pásala con `--pose-inicial` |
| `Detected jump back in time` **una vez** por log, al arrancar la reproducción | **No es un fallo.** El reloj pasa de la hora de pared a la hora en que se grabó el bag, que es anterior | Nada. La corrida vale |
| `Detected jump back in time` **repetido** durante toda la corrida | Otro `ros2 bag play` publicando `/clock` | `pkill` y repite. **Esa corrida no vale** |
| El mapa carga girado 180° | Se compuso mal la TF `base_link → laser` | El `yaw = π` no es opcional. Apéndice de la guía de mapeo, punto 2 |
| M1 sale ~1,00 y M2 sale enorme | Es el resultado esperado, no un fallo | La odometría acierta la **magnitud** y AMCL falla el **eje longitudinal**. Es la inobservabilidad del pasillo |
| M2 cambia mucho entre corridas del mismo bag | El filtro de partículas no converge | Paso 5.3. **Informa el rango**: es el resultado |
| `ros2 bag info` dice que todo está bien | **No demuestra nada.** Lee la metadata sin abrir el `.mcap` | Usa `comprobar_movimiento_bag.py` |
| Todo arranca, ningún error, y el carro no se mueve | Te faltó el `sudo` | `GUIA_TELEOP_MANDO.md` §0.2 ter |
| `rf2o.log` lleno de `Waiting for laser_scans....` | **No es un fallo.** El temporizador de rf2o va a 20 Hz y el LiDAR a ~10 Hz, así que la mitad de los ticks no tienen barrido nuevo y avisan | Comprueba que **también** haya líneas `Robot-base odom [x,y,yaw]=`. Si las hay, rf2o está funcionando |
| La cadena entera corre sin quejarse y no aparece `trayectoria.csv` | El volcador murió al arrancar y nadie más lo nota | El guion ya lo caza y sale con error. Lee `volcar.log`, que es donde está el motivo |

---

## Apéndice A. Qué hace exactamente la cadena de localización

```
ros2 bag play --clock    -->  /scan  y  /clock
        rf2o             -->  /odom  y  TF odom -> base_link
   static_transform      -->  TF base_link -> laser
      map_server         -->  /map   (el mapa de la primera pasada)
        AMCL             -->  /amcl_pose  y  TF map -> odom
```

Es la cadena de mapeo con `slam_toolbox` sustituido por `map_server` + `amcl`, y con dos nodos de
ciclo de vida en vez de uno normal, lo que obliga a un `lifecycle_manager` que los active.

Tres cosas que se heredan de la cadena de mapeo y **no** se pueden cambiar:

1. **`--clock` y `use_sim_time:=true`.** Sin ellos, `tf2` da los barridos por caducados frente al
   reloj de pared y los descarta todos sin quejarse.
2. **La TF `base_link → laser` lleva `yaw = π`.** `x = 0,02913, z = 0,184699`. Olvidar el giro
   localiza contra un mapa girado 180° y nada avisa.
3. **Velocidad real.** Acelerar cambia cuántas actualizaciones hace AMCL, y por tanto el resultado.

Y una que es nueva de esta cadena:

4. **`update_min_d` baja de 0,25 a 0,05 para el análisis.** Por defecto AMCL solo actualiza cuando
   el robot se ha movido 0,25 m, así que la última pose publicada puede ser de **hasta 25 cm antes
   de la marca de llegada** — la mitad del umbral de M2, metida por un parámetro y no por el
   algoritmo. Se baja a 0,05 m y **se declara**. Es una decisión de análisis, favorece ligeramente a
   AMCL al reducir el error de discretización del punto final, y no fabrica información: en un
   pasillo longitudinalmente inobservable, actualizar más veces no da de dónde triangular.

---

## Apéndice B. Las dos herramientas

**Estado: escritas el miércoles 2**, un día antes de lo previsto, y probadas. No hay que escribir
nada el jueves; el Paso 1.1 solo comprueba que siguen ahí.

### `herramientas/localizar_desde_bag.sh`

```
USO
    herramientas/localizar_desde_bag.sh <bag> <mapa.yaml> <salida> [--pose-inicial X,Y,YAW] [--topico T]

    <bag>       CARPETA del bag, legible por Humble (adaptada si viene de Jazzy)
    <mapa.yaml> el mapa de la primera pasada
    <salida>    se crea; ahi quedan trayectoria.csv y los cinco logs
    --topico    por defecto '/scan'. Los bags del 28-ago publican en
                '/rplidar_ros/scan' y sin esto la cadena sale vacia
```

Copia estructural de `mapear_desde_bag.sh`: mismo `limpiar()`, mismo `trap EXIT`, mismo
`static_transform_publisher`, mismo `rf2o.yaml` generado, misma comprobación de `.mcap` suelto y de
`metadata.yaml`. Cambia el final de la cadena: `map_server` + `amcl` + `lifecycle_manager`, con
`update_min_d: 0.05`, y en vez de `map_saver_cli` un suscriptor que vuelca `/odom` y `/amcl_pose` a
`trayectoria.csv`.

Salida `trayectoria.csv`, una fila por muestra:

```
t,fuente,x,y,yaw
12.480,odom,3.214,0.019,0.004
12.500,amcl,3.198,0.031,0.006
```

### `herramientas/medir_g2.py`

```
USO
    python3 herramientas/medir_g2.py <trayectoria.csv> --largo L [--sentido auto|ida|vuelta] [--estacion 20.0] [--json salida.json]
```

1. Detecta las **ventanas de parada** de salida y llegada con el mismo umbral de 0,05 m que
   `comprobar_movimiento_bag.py`, pero aplicado a **poses y no a rayos**.
2. **M1** = |desplazamiento de `/odom` entre las medianas de las dos ventanas| ÷ `L`.
3. **M2** = distancia 2D entre la mediana de `/amcl_pose` en la ventana de llegada y la marca, con
   sus componentes longitudinal y lateral desglosadas.
4. Si hay `--estacion`, detecta la parada intermedia y da M1 y M2 también ahí.
5. **Falla ruidosamente** si no encuentra dos ventanas de parada, o si `/amcl_pose` está vacío. No
   devuelve un número inventado.

> **Detectar las paradas sobre `/odom` no es circular, aunque lo parezca.** El reparo obvio es que
> M1 mide a rf2o y las ventanas también salen de rf2o, así que un rf2o congelado se declararía a sí
> mismo quieto. No aplica, y hay dato: el 26-ago rf2o registró **28,23 m de 29,94 m reales**. Se
> queda **corto**, no se para. Sobre una ventana de 1 s a 0,5 m/s eso son 0,47 m frente a 0,50 m,
> diez veces por encima del umbral de 0,05 m. El fallo de rf2o es acumular de menos poco a poco;
> nunca convierte un tramo conducido en una ventana de parada.

Prueba pura en `herramientas/prueba_medir_g2.py`, sin ROS, sin bag y sin pasillo, sobre CSV
sintéticos: **21 comprobaciones en 8 casos** —caso limpio, sentido de vuelta, sin ventana de
llegada, con `/amcl_pose` vacío, con estación intermedia, con largo cero— y sobre todo el caso del
sesgo +2,9 %, que debe dar **M1 = 1,029 y M2 = 0,58 m sobre 20 m**. Ese último es el que importa:
es el número que el §4 de `S21_preparacion_G2.md` predice para el viernes, y si la herramienta no
lo reproduce, el resultado del viernes no se puede contrastar contra nada.

```bash
python3 herramientas/prueba_medir_g2.py
```
