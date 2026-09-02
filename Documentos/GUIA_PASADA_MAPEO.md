# Levantar el mapa del pasillo: la pasada de mapeo, paso a paso

Guía de principio a fin para producir el **mapa del pasillo físico de ≥ 20 m** que el G2 necesita.
Cada comando dice **en qué máquina** va. No te saltes pasos: están en este orden porque cada uno
comprueba algo que el siguiente da por hecho.

Escrita el **2026-09-01** tras correr la cadena entera sobre los bags del 28-ago. Los números y
los avisos de esta guía salen de esa corrida, no de la documentación.

**Esta es la PRIMERA de las dos pasadas del viernes.** Produce el mapa. La segunda —conducir con
AMCL contra ese mapa y medir M1 y M2— es otra cosa y va después, y está en
[`GUIA_PASADA_LOCALIZACION.md`](GUIA_PASADA_LOCALIZACION.md). Sin el mapa, la segunda no existe.

---

## Parte 0. Lo que hay que entender antes de tocar nada

### 0.1 Qué produce esta pasada

Un par de archivos, `mapa_pasillo.pgm` + `mapa_pasillo.yaml`, que es lo que AMCL carga. Nada más.
No se mide M1 ni M2 aquí.

### 0.2 Por qué se graba en el carrito y se mapea en el portátil

Hay dos formas de levantar un mapa y **no son equivalentes**:

| | Dónde corre el SLAM | Qué hace falta |
|---|---|---|
| **A** | En el carrito, en vivo | `slam_toolbox` y `rf2o_laser_odometry` instalados y funcionando sobre **Jazzy**. Nadie lo ha comprobado |
| **B** | En el portátil, después | Que el carrito sepa grabar `/scan`. Nada más |

**Se elige B**, y por dos razones que pesan lo mismo:

1. **La cadena B está comprobada y la A no.** El 2026-09-01 se corrió entera en el portátil
   —reproducir, `rf2o`, `slam_toolbox`, `map_saver_cli`— sobre tres bags reales. Funciona. En el
   carrito, `slam_toolbox` puede no estar siquiera instalado, y descubrirlo en el pasillo con la
   cinta puesta es perder la mañana.
2. **B se puede repetir; A no.** Si el mapa sale mal por un parámetro, con B se cambia el
   parámetro y se vuelve a correr sobre el mismo bag. Con A hay que volver al pasillo.

Lo que se pierde con B es ver el mapa creciendo mientras empujas. Se compensa en la **Parte 5**:
el mapa se construye **allí mismo, antes de recoger**, con el portátil sobre una silla.

### 0.3 Las tres cosas que hundieron los bags del 28-ago

Los cinco bags del 28-ago se grabaron para esto mismo y **ninguno sirve**. Las tres causas son
independientes y esta guía neutraliza las tres. Merece la pena leerlas: son los tres pasos que uno
se salta por prisa.

**(1) El LiDAR publicaba en el tópico equivocado.** Los bags traen `/rplidar_ros/scan`, que es el
espacio de nombres del software de AWS. `rf2o` escucha `/scan` y solo `/scan`. Nunca recibió nada,
así que no hubo `/odom` ni TF, y sin TF los barridos no se pueden componer. Se evita en el **Paso
2.3** arrancando el sensor con `lidar_vehiculo.launch.py`, que lo pone sin espacio de nombres a
propósito, y se comprueba en el **Paso 2.4**.

**(2) El sensor estaba quieto el 84 % del tiempo.** Esto no estaba escrito en ninguna parte y es
lo peor de los tres. Medido el 2026-09-01:

| bag | duración | quieto | movimiento | % quieto |
|---|---|---|---|---|
| `bag_mapa_1445` | 57,9 s | 57,9 s | 0,0 s | 100,0 % |
| `bag_mapa_1447` | 87,8 s | 65,0 s | 22,7 s | 74,1 % |
| `bag_mapa_1450` | 5,1 s | 5,1 s | 0,0 s | 100,0 % |
| `bag_mapa_1451` | 257,6 s | 228,4 s | 29,2 s | 88,7 % |
| `bag_mapa_1456` | 404,4 s | 326,2 s | 78,2 s | 80,7 % |
| **TOTAL** | **812,8 s** | **682,6 s** | **130,2 s** | **84,0 %** |

De 813 s grabados solo hay **130 s de sensor moviéndose**, y fragmentados. **Aunque se hubiera
grabado la TF, el mapa no existiría**: un sensor que no se traslada no da de dónde triangular
estructura. Pasando `bag_mapa_1451` por la cadena sale esto —un disco radial de 11,3 × 10,9 m sin
una sola pared, en vez de un pasillo—:

```
mapa de bag_mapa_1451:  226 x 218 px = 11,30 x 10,90 m
                        ocupado 1168 px   libre 48100 px
```

Se evita en el **Paso 4.3**, que lo mide antes de que recojas.

**(3) `bag_mapa_1456` se cortó de golpe.** Le falta la `metadata.yaml` entera, porque el índice y
la metadata se escriben **al cerrar limpio**. Se evita en el **Paso 3.3**.

### 0.4 Empujar o conducir: aquí se empuja

Para **esta** pasada se empuja el carro a mano, con los motores apagados. Es legítimo porque lo
único que se está grabando es el LiDAR, que no sabe si lo mueve un motor o una mano, y elimina de
un golpe el riesgo de chocarlo en un pasillo con gente.

**Ojo, y esto sí importa:** empujar despacio **favorece** al algoritmo. A 6,6 Hz, empujando a
0,5 m/s hay ~7 cm entre barridos consecutivos; conduciendo a 1,5 m/s hay ~21 cm. Más solape es más
fácil. Por eso **la segunda pasada, la de M1 y M2, hay que conducirla**: si se empujara también,
las cifras no dirían nada del vehículo.

### 0.5 Lo que necesitas a mano

- El carro, cargado, con el LiDAR conectado por USB.
- El portátil, cargado, en la misma red wifi que el carro.
- **Cinta métrica o flexómetro** de al menos 5 m.
- **Cinta de enmascarar** y marcador, para marcar el suelo.
- Una silla o mesa donde poner el portátil en el pasillo.
- El pasillo: una recta libre de **≥ 20 m**, medida, no estimada.

---

## Parte 1. En el escritorio, antes de salir

Todo esto se hace **hoy**, no el viernes. Son diez minutos que evitan media mañana.

### Paso 1.1 — Comprobar que el plugin de almacenamiento está

**[PORTÁTIL]**

```bash
dpkg -l ros-humble-rosbag2-storage-mcap | tail -1
```

**Esperado:** una línea que empieza por `ii` y dice `0.15.16-1jammy`.
**Si no sale:** `sudo apt install ros-humble-rosbag2-storage-mcap`. Pide contraseña.
**Por qué importa:** sin esto, el portátil no puede abrir ni un barrido de un bag del carro. Y
**`ros2 bag info` no lo delata**: lee la `metadata.yaml` sin abrir el `.mcap`, así que contesta con
cifras grandes en un PC incapaz de leer nada. Nunca uses `ros2 bag info` como comprobación.

### Paso 1.2 — Comprobar la cadena de mapeo con un bag que sabes que es malo

Esto valida el portátil **y** te enseña a leer la salida, usando un bag del 28-ago como conejillo.

**[PORTÁTIL]**, desde la raíz del repositorio:

```bash
python3 herramientas/adaptar_bag_jazzy.py mapas/bag_mapa_1447 -o /tmp/prueba_mapeo
```

**Esperado:** `Adaptado en /tmp/prueba_mapeo` y una línea `-> enlace al original (no se copió)`.

```bash
python3 herramientas/comprobar_movimiento_bag.py /tmp/prueba_mapeo
```

**Esperado, y esto es lo importante: tiene que decir `NO SIRVE`.**

```
  topico de barrido : /rplidar_ros/scan
      AVISO: no es '/scan'. rf2o escucha '/scan' y no recibira nada.
  barridos          : 575 a 6.55 Hz
  duracion          : 87.8 s
  sensor quieto     : 65.0 s  (74.1 %)
  sensor en movim.  : 22.7 s  (25.9 %)

  NO SIRVE para construir un mapa:
    - solo 22.7 s de movimiento, y hacen falta 60 s ...
    - 74.1 % del bag es sensor quieto, y el maximo es 40 %
```

**Si dice `SIRVE`:** algo va mal en la herramienta, no en el bag. Este bag es malo y se sabe.
**Criterio de cierre:** ves `NO SIRVE` y los dos avisos. Ya sabes reconocer un bag malo.

### Paso 1.3 — Comprobar el guion de mapeo entero

**[PORTÁTIL]**

```bash
herramientas/mapear_desde_bag.sh /tmp/prueba_mapeo /tmp/prueba_mapa /rplidar_ros/scan
```

**Esperado:** cinco líneas `==`, y al final `Mapa en /tmp/prueba_mapa/mapa.pgm`. Tarda **lo que
dure el bag** —88 s aquí— porque se reproduce a velocidad real a propósito.

```bash
eog /tmp/prueba_mapa/mapa.pgm
```

**Esperado:** un borrón radial sin paredes. **Así se ve un mapa que no sirve.** Míralo bien: es lo
que tienes que NO ver el viernes.

**Si sale `AVISO GRAVE: hubo saltos de tiempo hacia atrás`:** había otro `ros2 bag play` corriendo.
Mata todo y repite:

```bash
pkill -9 -f "ros2 bag play"; pkill -9 -f rf2o_laser; pkill -9 -f slam_toolbox
```

**Criterio de cierre:** el guion termina sin error y el `.pgm` existe.

### Paso 1.4 — Decidir los umbrales de M1 y M2 antes de salir

No es de esta pasada, pero es del viernes y **hay que dejarlo escrito antes**, no después de ver
el dato. El §6.3 del protocolo experimental lo prohíbe expresamente. Está discutido en
[`Evidencia/S21_preparacion_G2.md`](Evidencia/S21_preparacion_G2.md) §4, y las tres preguntas que
hay que llevar contestadas —y firmadas por el director— están en el **Paso 1.3** de
[`GUIA_PASADA_LOCALIZACION.md`](GUIA_PASADA_LOCALIZACION.md).

**Si no están contestadas, sal igual:** los bags de las dos pasadas valen y se pueden analizar
después. Lo que no se puede es **declarar el G2** con unos umbrales elegidos al ver el número.

---

## Parte 2. En el pasillo: montar y medir

### Paso 2.1 — Medir la recta con cinta y marcarla

Antes de encender nada. **Este número es la verdad de terreno de todo lo que viene después**, y no
se puede reconstruir luego.

1. Elige la recta más larga y despejada del pasillo.
2. Marca con cinta de enmascarar el **0 m** en el suelo.
3. Mide con el flexómetro y marca cada **5 m**, hasta el final.
4. **Anota la longitud total con dos decimales.** Ejemplo: `22,40 m`.
5. Mide también el **ancho** del pasillo en tres puntos y anótalos.
6. **En los dos extremos, la marca es una cruz, no una raya.** Añade ~60 cm de cinta **a lo largo**
   del eje del pasillo, cruzando la marca de metros. Céntrala: mide del muro a la cruz en los dos
   extremos y **anota los dos números**.
7. **Si la recta mide ≥ 25 m, marca además una cruz a los 20,00 m exactos** desde el 0 m.

> **Por qué cruces y no rayas, y por qué se hacen ahora.** Una raya dice a cuántos metros estás;
> M2 mide un error en **2D**, así que el carro tiene que parar en un **punto** repetible. El trazo
> longitudinal sirve además para alinear el chasis a ojo, que es de donde sale el rumbo inicial.
>
> Se hacen en esta pasada porque **el pasillo no se vuelve a marcar**: cuando llegue la segunda,
> el carro, el portátil y la silla ya están puestos y hay gente pasando. Y la cruz de los 20 m
> permite sacar M1 y M2 **también a exactamente 20 m** del mismo bag, que es la longitud sobre la
> que está escrito el criterio, sin dejar de correr sobre la recta entera.

**Todo esto se puede hacer sin el carro y sin el portátil.** Si tienes acceso al pasillo antes del
viernes, hazlo antes: es lo único de la mañana que no depende de nada más, y si la recta no llega
a 20 m, saberlo el jueves vale mucho más que saberlo el viernes.

**Esperado:** una longitud **≥ 20 m**. Si la recta más larga da menos de 20 m, el G2 no se puede
tomar en ese pasillo y hay que buscar otro; anótalo y díselo al director, no lo maquilles.

### Paso 2.2 — Encender el carro y entrar por SSH

**[PORTÁTIL]**

```bash
ping -c 2 deepracer.local
```

**Esperado:** dos respuestas, con la IP entre paréntesis. Anótala. **La IP cambia entre sesiones**
—el 19-ago era `.101` y el 21-ago ya era `.102`—, no la des por sabida.

```bash
ssh deepracer@<IP>
```

### Paso 2.3 — Arrancar el LiDAR con el nombre correcto

**[CARRITO — SSH]**

```bash
source /opt/ros/jazzy/setup.bash && source ~/deepracer_ws/install/setup.bash && ros2 launch deepracer_bringup lidar_vehiculo.launch.py
```

**Esperado:** el driver anuncia `RPLIDAR S/N`, `Hardware Rev: 5` y arranca el escaneo.

**Si dice `Package 'deepracer_bringup' not found`:** el paquete no está compilado en el carro. No
pierdas tiempo compilándolo en el pasillo — arranca el nodo a pelo, con **los mismos parámetros**
que el launch:

```bash
source /opt/ros/jazzy/setup.bash && ros2 run rplidar_ros rplidar_composition --ros-args -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=115200 -p frame_id:=laser -p inverted:=false -p angle_compensate:=true
```

Sin espacio de nombres, publica en `/scan`, que es lo que hace falta.

**Si dice que no encuentra `/dev/ttyUSB0`:** el sensor no está conectado o el puerto es otro.
Compruébalo con `ls /dev/ttyUSB*`.

### Paso 2.4 — Comprobar que publica de verdad, y en `/scan`

**Este es el paso que faltó el 28-ago.** Que el tópico salga en la lista no significa nada.

**[CARRITO — segunda terminal SSH]**

```bash
source /opt/ros/jazzy/setup.bash && ros2 topic hz /scan
```

**Esperado:** `average rate: 6.6` aproximadamente, con `std dev` por debajo de 0,01 s.

```bash
source /opt/ros/jazzy/setup.bash && ros2 topic echo /scan --once --field header.frame_id
```

**Esperado:** `laser`.

**Si `ros2 topic hz /scan` dice `no new messages`:** el sensor está publicando en otro sitio.
Compruébalo:

```bash
source /opt/ros/jazzy/setup.bash && ros2 topic list | grep scan
```

Si aparece `/rplidar_ros/scan`, arrancaste el LiDAR por la vía de AWS. **Párala y vuelve al Paso
2.3.** Se puede salvar después con un remapeo, pero es exactamente el error del 28-ago y no hay
razón para repetirlo teniendo el carro delante.

**Criterio de cierre:** `/scan` a ~6,6 Hz con `frame_id: laser`.

### Paso 2.5 — Levantar el demonio de descubrimiento **antes** de grabar

**Este paso es nuevo desde el 2026-09-01 y es el más importante de la Parte 2.** No lo saltes
porque parezca burocracia: es el candidato más fuerte a explicar por qué los bags del 28-ago
salieron con un solo tópico y uno de ellos sin `metadata.yaml`.

**[CARRITO — segunda terminal SSH]**

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && ros2 daemon start && sleep 3 && ros2 topic list | wc -l'
```

**Esperado:** `22`. Repítelo dos veces más: tiene que dar **22 las tres veces**.

**Si da números distintos entre corridas, no grabes todavía.** Espera y repite hasta que se
estabilice.

> **Por qué.** El descubrimiento de ROS 2 en este carro **no es determinista para un participante
> recién nacido**. Medido el 2026-09-01 contra un grafo que no cambiaba:
>
> | Comando | Corrida 1 | Corrida 2 | Corrida 3 |
> |---|---|---|---|
> | `ros2 topic list --no-daemon` | **2** | **10** | **17** |
> | `ros2 topic list` (con demonio) | 22 | 22 | 22 |
>
> Sin demonio, el proceso nace, escucha unos milisegundos, y publica **lo que le dio tiempo a
> oír**. Con demonio hay un participante de larga vida que ya conoce el grafo entero.
>
> **`ros2 bag record` es exactamente un participante recién nacido.** Si lo lanzas antes de que
> el descubrimiento haya cuajado, se suscribe a lo que alcanzó a ver: puede grabar un subconjunto,
> o **nada**, y en los dos casos dice `Recording...` igual de contento. Levantar el demonio antes
> no garantiza nada por sí solo, pero al menos te da una lectura estable con la que decidir.

**Criterio de cierre de la Parte 2:** `/scan` a ~6,6 Hz con `frame_id: laser`, y `ros2 topic
list` devolviendo **el mismo número tres veces seguidas**.

---

## Parte 3. La pasada

### Paso 3.1 — Colocar el carro y empezar a grabar

Pon el carro en el suelo **con el LiDAR justo encima de la marca de 0 m**, mirando al fondo de la
recta. Anota hacia dónde mira: te hará falta para interpretar el mapa.

> **El punto de referencia es el LiDAR, y esto cambió el 2026-09-02.** Antes esta guía decía «el
> centro del eje trasero», y está mal por dos razones que se suman.
>
> **Primera: son 11,1 cm de sesgo.** En el URDF, respecto a `chassis`, el eje trasero está en
> `x = −0,081663` y el LiDAR en `x = +0,02913`. Colocar uno donde va el otro desplaza todo lo que
> venga después **11,1 cm**, siempre en el mismo sentido. Frente al umbral de 0,50 m de M2 eso es
> el 22 % del presupuesto, regalado por un detalle de colocación.
>
> **Segunda, y es la que decide: aquí nace el origen del mapa.** `slam_toolbox` pone el `(0, 0, 0)`
> del mapa donde estaba `base_link` al arrancar el SLAM, y AMCL trae `set_initial_pose: True` con
> `(0, 0, 0)` en `nav2_params_nav_amcl_sim_demo.yaml`. Si arrancas **aquí**, sobre la marca y
> mirando al fondo, la pose inicial de AMCL en la segunda pasada sale correcta sin tocar un
> parámetro. Si arrancas en otro sitio, hay que medir el desplazamiento y restarlo a mano.
>
> `base_link` está en `x = 0` de `chassis`, así que el LiDAR queda 2,9 cm por delante de él.
> Despreciable: alinéalo a ojo desde arriba. Lo que no es despreciable son los 11,1 cm.
>
> Lo explica entero el Paso 2.2 de [`GUIA_PASADA_LOCALIZACION.md`](GUIA_PASADA_LOCALIZACION.md).

**[CARRITO — segunda terminal SSH]**

```bash
sudo -i bash -c "source /opt/ros/jazzy/setup.bash && cd ~deepracer && ros2 bag record /scan -o mapa_pasillo_$(date +%H%M)"
```

**Esperado:** `Recording...`, el nombre de la carpeta, y **una línea por cada tópico suscrito**.
**Anota el nombre de la carpeta.**

> **El `sudo` no es opcional, y la razón es la misma que en el teleop.** El descubrimiento de
> este dominio pasa por `/dev/shm/fastrtps_port70NN`, buzones que `deepracer-core` crea como
> `root` con permisos `-rw-r--r--`. Un `ros2 bag record` lanzado como usuario **puede leerlos
> pero no escribir su anuncio**, así que para la pila no existe — y graba un fichero vacío
> diciendo `Recording...` sin una sola queja. Medido el 2026-09-01: publicador de usuario contra
> suscriptor de la pila, **0 mensajes**; publicador `root`, **56**.
>
> **Honestidad sobre el 28-ago:** el bag de aquel día sí capturó `/rplidar_ros/scan`, así que o
> se lanzó como `root` o el mecanismo no explica *aquel* fallo entero. Se documenta como lo que
> es: una condición necesaria comprobada, no un diagnóstico cerrado de aquel bag.

> **La ruta va explícita.** Con `sudo -i` el `~` es `/root`, no el del usuario `deepracer`, y luego el
> `scp` del Paso 4.1 no encontraría nada. El bag quedará **con dueño `root`**; si el `scp` falla
> por permisos, `sudo chown -R deepracer:deepracer ~deepracer/mapa_pasillo_*` en el carro.

**Por qué solo `/scan`:** es lo único que el carro tiene que aportar. `/odom` y la TF se generan
después en el portátil, con `rf2o`, que es exactamente lo que haría el carro en vivo. Grabar menos
es grabar menos cosas que pueden fallar.

> **El carro no publica `/odom`, `/tf` ni `/tf_static`.** Comprobado el 2026-09-01 contra la
> lista estable de 22 tópicos. No es una avería: es la razón por la que esta guía eligió la
> cadena B en §0.2. **Si algún documento del proyecto te pide grabar `/odom`, `/tf` o
> `/amcl_pose` en esta pasada, ese documento está equivocado** — no hay nada que grabar.

### Paso 3.2 — Recorrer el pasillo

Con los **motores apagados**, empujando el carro por el chasis. Que la mano no tape el sensor.

1. **Espera 5 segundos quieto** en el 0 m antes de moverte. Da a `slam_toolbox` un primer barrido
   limpio del que partir.
2. **Recorre los 20+ m a paso lento y constante**, ~0,5 m/s: unos 40 s. Cuenta mentalmente los
   segundos entre marcas de 5 m; deberían salirte ~10 s por tramo.
3. **No pares a mitad.** Un tramo largo quieto es lo que arruinó los bags del 28-ago.
4. **No gires el carro sobre sí mismo.** Va recto.
5. Al llegar al final, **espera 5 segundos quieto**.
6. **Vuelve empujando hacia atrás**, sin dar la vuelta al carro, hasta el 0 m. El cierre de bucle
   sobre el mismo pasillo es lo que corrige la deriva acumulada.
7. **Espera 5 segundos quieto** al volver al 0 m.

**Esperado:** unos **90-100 s** en total, de los cuales ~80 s de movimiento.

**Si el pasillo tiene gente:** que pase. Un peatón mueve pocos rayos y la herramienta del Paso 4.3
usa la mediana justamente para no confundirlo con movimiento del sensor. Lo que sí arruina la
pasada es **pararse a esperar** a que despejen: eso es tiempo quieto.

### Paso 3.3 — Cerrar la grabación limpiamente

**[CARRITO — segunda terminal SSH]** — **`Ctrl-C` una sola vez**, y espera.

**Esperado:** el proceso tarda un par de segundos y termina solo.
**No des `Ctrl-C` dos veces ni cierres la terminal.** El índice del `.mcap` y la `metadata.yaml`
se escriben **al cerrar**. `bag_mapa_1456` perdió los suyos así y hubo que recuperarlo a mano.

```bash
ls -la ~/mapa_pasillo_*/
```

**Esperado:** dos archivos, `metadata.yaml` **y** un `.mcap`.
**Si falta `metadata.yaml`:** la grabación se cortó de golpe. **Repite la pasada.** El bag se
puede leer con la API, pero **no se puede reproducir**, y sin reproducirlo no hay mapa.

---

## Parte 4. Comprobar en el sitio, antes de recoger

Todo lo de esta parte se hace **con el carro todavía en el pasillo y la cinta todavía puesta**. Es
lo que convierte una mañana perdida en una repetición de cinco minutos.

### Paso 4.1 — Traer el bag al portátil

**[PORTÁTIL]**

```bash
scp -r deepracer@<IP>:~/mapa_pasillo_HHMM /tmp/
```

Sustituye `HHMM` por el nombre real que anotaste.

### Paso 4.2 — Adaptar la metadata de Jazzy a Humble

**[PORTÁTIL]**, desde la raíz del repositorio:

```bash
python3 herramientas/adaptar_bag_jazzy.py /tmp/mapa_pasillo_HHMM -o /tmp/mapeo
```

**Esperado:** `Adaptado en /tmp/mapeo` y `metadata.yaml reescrita a version 5`.
**Por qué hace falta:** el carro escribe la metadata en versión 9 y Humble solo lee la 5. Sin esto
el portátil aborta con `yaml-cpp: error at line 15, column 11: bad conversion`.
**Si dice que ya está en versión 5:** el bag ya se adaptó; usa el que ya tienes.

### Paso 4.3 — Comprobar que el sensor se movió

**El paso que decide si recoges o repites.**

```bash
python3 herramientas/comprobar_movimiento_bag.py /tmp/mapeo
```

**Esperado:**

```
  topico de barrido : /scan
  barridos          : ~630 a 6.6 Hz
  duracion          : ~95 s
  sensor quieto     : ~17 s  (18 %)
  sensor en movim.  : ~78 s  (82 %)

  SIRVE para construir un mapa.
```

**Si dice `NO SIRVE`:** **repite la pasada ahora mismo**, sin recoger. Lee el motivo:

| Motivo | Qué pasó | Qué hacer |
|---|---|---|
| `solo N s de movimiento` | La pasada fue corta o hubo paradas largas | Repite recorriendo ida y vuelta sin pararte |
| `% del bag es sensor quieto` | Grabaste antes de empezar a empujar, o después de terminar | Repite, y arranca la grabación justo antes de moverte |
| `AVISO: no es '/scan'` | Arrancaste el LiDAR por la vía de AWS | Vuelve al Paso 2.3. El bag se salva con remapeo, pero repítelo bien |

**Criterio de cierre:** `SIRVE`, y el tópico es `/scan`.

### Paso 4.4 — Construir el mapa allí mismo

```bash
herramientas/mapear_desde_bag.sh /tmp/mapeo /tmp/mapa_pasillo
```

**Esperado:** tarda lo que duró la pasada, ~95 s, y termina con `Mapa en
/tmp/mapa_pasillo/mapa.pgm`.

**Si sale `AVISO GRAVE: hubo saltos de tiempo hacia atrás`:** el mapa no vale. Mata todo y repite
el guion —el bag está bien, el problema es del portátil—:

```bash
pkill -9 -f "ros2 bag play"; pkill -9 -f rf2o_laser; pkill -9 -f slam_toolbox
```

---

## Parte 5. Aceptar o rechazar el mapa

### Paso 5.1 — Mirarlo

```bash
eog /tmp/mapa_pasillo/mapa.pgm
```

**Esperado:** un pasillo. Dos paredes largas, negras, **paralelas**, con blanco entre ellas.

**Lo que descalifica el mapa, mirándolo:**

- **Un borrón radial sin paredes** → el sensor no se movió lo suficiente. Es lo que sale de los
  bags del 28-ago. Repite la pasada.
- **Paredes dobles o el pasillo dibujado dos veces desplazado** → la vuelta no cerró sobre la ida;
  `rf2o` acumuló deriva. Repite empujando más despacio.
- **El pasillo se dobla o se curva** cuando en la realidad es recto → error de `yaw` acumulado.
  Repite.

### Paso 5.2 — Medirlo contra la cinta

Mirarlo no basta: **un pasillo comprimido se ve perfectamente bien.** Es justo el fallo que R3
predice —en un tubo uniforme el eje longitudinal no es observable y `rf2o` se congela, con **1,71 m
registrados de 29,94 m reales (5,7 %)** medidos en simulación el 26-ago—. Si pasa aquí, el mapa
saldrá bonito y corto.

```bash
python3 - <<'PY'
# Mide el rectangulo de espacio conocido del mapa y lo compara con la cinta.
# No es el largo del pasillo exacto -incluye lo que el sensor vio mas alla de
# las marcas- pero un mapa comprimido no puede pasar esta prueba.
from PIL import Image
im = Image.open('/tmp/mapa_pasillo/mapa.pgm')
px = im.load(); w, h = im.size
xs = [x for x in range(w) for y in range(h) if px[x, y] < 50 or px[x, y] > 200]
ys = [y for x in range(w) for y in range(h) if px[x, y] < 50 or px[x, y] > 200]
print(f"conocido: {(max(xs)-min(xs))*0.05:.2f} x {(max(ys)-min(ys))*0.05:.2f} m")
PY
```

**Esperado:** el lado largo tiene que ser **al menos tan largo como la recta que mediste con
cinta**, más el alcance del sensor por los extremos.

**Criterio de aceptación, y decídelo con la cinta en la mano:**

| Lado largo del mapa | Veredicto |
|---|---|
| ≥ la longitud de cinta | **Sirve.** Sigue a la Parte 6 |
| entre el 90 % y el 100 % | **Sirve, pero anótalo.** Es deriva longitudinal, y es el dato que R3 predice |
| < 90 % de la cinta | **No sirve.** `rf2o` se congeló. Repite empujando más despacio |

**Si falla dos veces por lo mismo, para y anótalo.** Que `rf2o` se congele en el pasillo real es un
**hallazgo**, no un fallo de la pasada: significa que el mapa físico no se puede levantar así, y
eso hay que documentarlo, no seguir repitiendo. Enlaza directamente con R3.

### Paso 5.3 — Comprobar el ancho

El pasillo del mapa tiene que medir lo que mediste con el flexómetro en el Paso 2.1. Si el mapa
dice 3 m donde la cinta dice 2,10 m, hay un factor de escala mal y el mapa no vale para AMCL.

---

## Parte 6. Guardar en el repositorio

Solo si el mapa pasó la Parte 5.

**[PORTÁTIL]**, desde la raíz del repositorio:

```bash
cp /tmp/mapa_pasillo/mapa.pgm mapas/mapa_pasillo.pgm && cp /tmp/mapa_pasillo/mapa.yaml mapas/mapa_pasillo.yaml
```

El `.yaml` lleva dentro `image: mapa.pgm`; **cámbialo a `mapa_pasillo.pgm`** o AMCL no encontrará
la imagen.

Guarda también, en `Documentos/Evidencia/`:

- La **longitud de cinta** y el **ancho** del Paso 2.1, con dos decimales.
- La salida entera de `comprobar_movimiento_bag.py` del Paso 4.3.
- El lado largo medido en el Paso 5.2 y la comparación contra la cinta.
- El bag original, o su ruta si es grande.

**Lo que NO se puede escribir:** que el mapa «se verificó». `herramientas/verificar_mapa.py` **no
sirve para un mapa físico** —exige un `.world` de Gazebo contra el que comparar— y su umbral de
frontera del 1 % dio 15,00 % sobre el mapa del laboratorio. Lo que se verifica aquí es lo de la
Parte 5 y nada más.

---

## Parte 7. Si algo va mal

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `yaml-cpp: error at line 15, column 11: bad conversion` | Bag de Jazzy sin adaptar | Paso 4.2 |
| `yaml-cpp: error at line 1, column 12: bad conversion` | Le pasaste un `.mcap` suelto a `ros2 bag play` | Pásale la **carpeta**. El `.mcap` suelto se puede leer con la API pero **no reproducir** |
| `Could not load/open plugin with storage id 'mcap'` | Falta el plugin | Paso 1.1 |
| `Detected jump back in time. Clearing TF buffer.` | Hay otro `ros2 bag play` publicando `/clock` | `pkill -9 -f "ros2 bag play"` y repite. **El mapa de esa corrida no vale** |
| `Package 'deepracer_bringup' not found` en el carro | No está compilado ahí | Arranca `rplidar_composition` a pelo, Paso 2.3 |
| `ros2 topic hz /scan` dice `no new messages` | El LiDAR publica en `/rplidar_ros/scan` | Paso 2.3, vía correcta |
| El bag no tiene `metadata.yaml` | La grabación se cortó de golpe | Repite la pasada. Paso 3.3 |
| El mapa sale vacío y `saver.log` no dice nada | `slam_toolbox` no recibió barridos | Mira `slam.log`. Si no dice `Registering sensor`, el tópico no llegó |
| `ros2 bag info` dice que todo está bien | **No demuestra nada.** Lee la metadata sin abrir el `.mcap` | Usa el Paso 4.3, que sí lee mensajes |

---

## Apéndice. Qué hace exactamente la cadena de mapeo

Lo que corre `herramientas/mapear_desde_bag.sh`:

```
ros2 bag play --clock    -->  /scan  y  /clock
        rf2o             -->  /odom  y  TF odom -> base_link
   static_transform      -->  TF base_link -> laser
      slam_toolbox       -->  /map   y  TF map -> odom
     map_saver_cli       -->  mapa.pgm + mapa.yaml
```

Tres cosas del montaje que no son obvias y que costaron encontrar:

1. **`--clock` y `use_sim_time:=true` no son opcionales.** Las marcas de tiempo del bag son del día
   de la grabación; contra el reloj de pared de hoy, `tf2` las da por caducadas y descarta todos
   los barridos sin construir nada ni quejarse.

2. **La TF `base_link → laser` lleva un giro de 180°.** El URDF cuelga el sensor de `chassis`, no
   de `base_link`: `base_link → chassis` (z = 0,023249) y `chassis → laser`
   (xyz = 0,02913 0 0,16145, **rpy = 0 0 π**). Compuesto da x = 0,02913, z = 0,184699, yaw = π, que
   es la TF estática que `deepracer.launch.py` publica en el carro. Copiar el 0,16145 del xacro sin
   componer el chasis deja el sensor 23 mm bajo, y **olvidar el yaw = π construye el mapa girado
   180° respecto al que AMCL verá después**, sin que nada avise.

3. **Se reproduce a velocidad real.** Acelerar con `--rate` hace que `slam_toolbox` descarte
   barridos y el mapa cambia. El bag dura lo que dura.
