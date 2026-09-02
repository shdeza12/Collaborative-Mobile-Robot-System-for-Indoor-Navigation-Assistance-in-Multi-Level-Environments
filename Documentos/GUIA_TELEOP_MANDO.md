# Conducir el DeepRacer físico con un mando de Nintendo Switch Pro

Guía de principio a fin. Cada comando dice **en qué máquina y en qué terminal** va.
No te saltes pasos: están en este orden porque cada uno comprueba algo que el siguiente da por hecho.

El programa es [`herramientas/teleop_mando.py`](../herramientas/teleop_mando.py).

---

## Parte 0. Antes de empezar

### 0.1 Las dos máquinas

Vas a usar dos computadores, pero **no a la vez**:

- **PORTÁTIL** — tu PC, Ubuntu 22.04 con ROS 2 Humble. Solo se usa para copiar el programa al
  carro con `scp`. Después ya no hace falta para conducir.
- **CARRITO** — la tarjeta del DeepRacer, Ubuntu 24.04 con ROS 2 Jazzy. Se entra por SSH.
  **Todo lo demás corre aquí**, y todo **como `root`**.

Al final vas a tener **tres sesiones SSH al carro** abiertas a la vez:

| Terminal | Máquina | Qué corre ahí |
|---|---|---|
| 1 | CARRITO (SSH, `sudo`) | `joy_node` — lee el mando y publica `/joy` |
| 2 | CARRITO (SSH, `sudo`) | Comprobaciones sueltas, y matar cosas |
| 3 | CARRITO (SSH **`-t`**, `sudo`) | `teleop_mando.py` — manda al servo |

El portátil solo se usa un momento, en la Parte 3, para copiar el programa.

### 0.2 Por qué el mando va por USB al carrito, y no por Bluetooth al portátil

**El carro no tiene Bluetooth.** Medido el 2026-09-01: `hciconfig -a` no devuelve nada,
`rfkill list` solo lista `phy0: Wireless LAN`, el servicio `bluetooth` está inactivo y `dmesg`
no tiene ni una línea de HCI. No es que esté apagado — no hay radio. Emparejar el mando al
carro **no es una opción**, y por eso el «plan B: emparejar el mando al carrito» que traían
versiones anteriores de esta guía se ha borrado: describía algo imposible.

Queda emparejarlo al portátil y cruzar `/joy` por wifi, o **enchufarlo por USB al carro**. Se
usa el USB, por tres razones:

1. **No depende del wifi.** Si el `/joy` viaja por red y la red se cae, el hombre muerto salta y
   el carro para — correcto, pero significa que el carro se para solo cada vez que el wifi
   parpadea. Por USB eso no puede pasar.
2. **No depende de que Humble y Jazzy se hablen.** Nunca se comprobó en este proyecto, y el día
   de la prueba no es el día de averiguarlo.
3. **`joy_node` en el carro reconoce el Pro Controller por USB sin instalar nada.** Comprobado:
   `sudo apt install ros-jazzy-joy` y el mando aparece como `/dev/input/js0`.

`teleop_mando.py` corre **siempre en el carrito** de todos modos, porque es lo que le da órdenes
al motor. Si corriera en el portátil y se cayera el wifi, el carro se quedaría con la última
orden recibida: acelerando y sin nadie al mando.

> **Enchufa el mando ANTES de que el carro arranque su pila, o con la pila parada.**
> Enchufar cualquier cosa por USB con `deepracer-core` corriendo **mata el LiDAR en silencio**:
> el bus se re-enumera, el nodo de `/dev/ttyUSB0` se borra y se vuelve a crear, y
> `rplidar_node` se queda con un descriptor abierto a `/dev/ttyUSB0 (deleted)` publicando nada.
> `systemctl` sigue diciendo `active (running)`. Pasó el 2026-09-01 al conectar el mando.
> Es la **tercera vez** que un `active` miente en este proyecto (ver la tabla de la Parte 8).

### 0.2 bis — Regla que no se negocia: **nunca reinicies el carro**

El 2026-09-01 se reinició la tarjeta y **se quedó en GRUB pidiendo qué sistema arrancar**. Sin
monitor y teclado enchufados al carro no hay forma de contestar, y por SSH no se llega porque
todavía no hay sistema. Hubo que ir físicamente a resolverlo.

En el pasillo, el día del G2, no vas a tener monitor. **Un `sudo reboot` allí termina la
sesión.** Si algo se cuelga, se reinicia el servicio (`sudo systemctl restart deepracer-core`),
nunca la máquina.

### 0.2 ter — Todo en el carro va con `sudo`, y sin `sudo` falla **sin decir nada**

`joy_node` y `teleop_mando.py` se arrancan los dos con `sudo`. No es prudencia: sin `sudo` el
programa arranca bien, no da ningún error, publica alegremente, y **el resto del grafo de ROS
no lo ve**.

La causa está medida. El descubrimiento de Fast DDS en el dominio del carro pasa por memoria
compartida: los buzones son `/dev/shm/fastrtps_port7000` a `…7005`, que **`deepracer-core` crea
al arrancar como `root`, con permisos `-rw-r--r--`**. Un proceso que no sea `root` los puede
**leer pero no escribir**, así que no puede depositar su anuncio de participante. Para el resto
del grafo, sencillamente **nunca existió**. Ni excepción, ni aviso, ni un `WARN`.

Cómo se comprobó, con un publicador y un suscriptor de prueba y contando mensajes recibidos:

| Publicador | Suscriptor | Mensajes recibidos |
|---|---|---|
| usuario | pila (`root`) | **0** |
| `root` | pila (`root`) | **56** |
| usuario | usuario, con `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` | 55 y 33 |

La tercera fila parece contradecir a la primera y no lo hace: `LOCALHOST` fuerza el
descubrimiento por UDP contra `127.0.0.1` y **se salta `/dev/shm`** — por eso funciona entre
dos procesos de usuario, y por esa misma razón **no sirve para hablar con la pila**, que usa
memoria compartida. Y no, `lo` no tiene la bandera `MULTICAST`.

> **Lo importante no es la explicación, es el síntoma:** un teleop sin `sudo` se ve *idéntico* a
> uno que funciona hasta que das stick y el carro no se mueve. Si eso pasa, lo primero que hay
> que mirar es si lo arrancaste con `sudo`.

### 0.3 Las cuatro protecciones que tiene el programa

1. **Botón de habilitación.** El carro solo se mueve mientras mantienes pulsado **ZR**.
2. **Hombre muerto de 0,6 s.** Si `/joy` deja de llegar —mando apagado, wifi caído, `joy_node`
   muerto—, el carro para.
3. **Diez ceros al salir**, con `Ctrl-C`, con `kill`, y si se cae la sesión SSH.
4. **Límite de velocidad** al 0,35 del rango, 0,70 con turbo **por defecto**. El carro llega a
   4 m/s. La configuración con la que de verdad se condujo el 2026-09-01 fue **0,70 y 1,0**, y
   se pasa por parámetro; ver §0.3 bis.

> **La protección 3 estuvo escrita y no funcionaba, hasta el 2026-09-01.** Se midió mandando la
> señal **al proceso de Python** —no al `bash` que lo lanza, que fue el error del primer intento y
> dio un falso «sale limpio»— y contando los mensajes publicados después: con `Ctrl-C` llegaban
> **cero**. La causa es que `rclpy.init()` instala su propio manejador de `SIGINT` y `SIGTERM` que
> **cierra el contexto antes** de que corra el bloque de limpieza, así que publicar los ceros
> fallaba con `publisher's context is invalid`. El vehículo se quedaba con el último valor de
> tracción **justo en la forma documentada de apagarlo**. Corregido pidiéndole a `rclpy` que no
> toque las señales; ahora las tres —`SIGINT`, `SIGTERM`, `SIGHUP`— publican **exactamente 10**
> mensajes y salen con código 0.
>
> **`SIGHUP` importa tanto como las otras dos y es la menos evidente:** el programa se arranca por
> SSH, y si se cae la sesión —wifi, portátil suspendido, terminal cerrada— llega `SIGHUP`. **El
> hombre muerto no cubre ese caso**, y esa es exactamente la razón por la que es peligroso: el
> hombre muerto vive *dentro* del proceso, así que un proceso muerto no para nada.

### 0.3 bis — Los límites por defecto no son los que se condujeron

El fichero del repositorio trae `limite_normal=0.35` y `limite_turbo=0.70`. Con esos valores el
carro se mueve, pero al usuario le pareció lento para conducirlo de verdad, así que el
2026-09-01 se condujo con **`0.70` y `1.0`**.

El repositorio **no cambia sus valores por defecto**, a propósito: lo primero que hace cualquiera
que siga esta guía es la Parte 6 con el carro en alto, y para eso el valor conservador es el
correcto. La configuración rápida se pide explícitamente, añadiendo al comando del Paso 4.3:

```
-p limite_normal:=0.70 -p limite_turbo:=1.0
```

**Sube uno cada vez y prueba entre medias.** `limite_turbo:=1.0` es el rango completo del
vehículo: 4 m/s con ZL pulsado.

### 0.4 Lo que necesitas a mano

- El mando **y su cable USB-C**. Por USB el mando se alimenta del carro, así que la carga da
  igual. El cable tiene que llegar desde el carro hasta donde vayas a estar tú: es la única
  limitación real de conducir por cable.
- El carro encendido y en la misma red wifi que el portátil (para el SSH; el `/joy` ya no viaja
  por ahí).
- Algo para levantar el carro y dejar **las ruedas al aire** (una caja, un libro grueso).
  No es opcional: la Parte 6 se hace así.
- **Un cable USB libre.** Si tienes que desenchufar algo para meter el mando, mira antes qué
  estás desenchufando: el 2026-09-01 se metió un teclado y desplazó el LiDAR y una de las
  cámaras.

### 0.5 Antes de tocar el carro: pasa la prueba de escritorio

**[PORTÁTIL — Terminal 1]**

```bash
python3 herramientas/prueba_teleop_mando.py
```

**Esperado:** `Todas las comprobaciones pasan.` Son 30 comprobaciones de la lógica de decisión y
del hombre muerto, y **no necesitan ROS, ni mando, ni carro** — así que también se pueden correr
*en* el carro si hay dudas de que llegara la versión correcta.

Cubren lo que la Parte 6 no puede reproducir a mano: el instante exacto del vencimiento, el
arranque en frío antes del primer `/joy`, un mando que publica menos ejes de los pedidos, y el
gatillo sin estrenar que lee `0.0`. **Si esto falla, no sigas:** la Parte 6 comprueba una vez el
caso fácil, con el vehículo delante.

---

## Parte 1. Conectar el mando al carrito por USB

### Paso 1.1 — Enchufar el mando

**Con la pila del carro parada.** Si está corriendo, párala antes (§0.2 explica por qué):

**[CARRITO — Terminal 1]**

```bash
sudo systemctl stop deepracer-core
```

Enchufa ahora el mando al carro con el cable USB-C. Se enciende solo y se queda con **un LED
fijo**. Vuelve a arrancar la pila:

```bash
sudo systemctl start deepracer-core
```

### Paso 1.2 — Comprobar que el sistema lo ve

**[CARRITO — Terminal 1]**

```bash
ls /dev/input/js*
```

**Esperado:** `/dev/input/js0`.
**Si no sale nada:** el mando no está enchufado, o el cable es solo de carga y no de datos.
Prueba otro cable antes de dar por muerto nada.

> **En el carro sí sale `js0`, y en el portátil por Bluetooth no.** No es contradicción: son
> dos caminos distintos del kernel. Por eso esta comprobación vale aquí y no valdría en el
> Anexo B.

### Paso 1.3 — Instalar el nodo `joy` en el carro

**[CARRITO — Terminal 1]**

```bash
sudo apt install -y ros-jazzy-joy
```

**Esperado:** o lo instala, o dice `ros-jazzy-joy is already the newest version`. Las dos cosas
están bien.

**Criterio de cierre de la Parte 1:** existe `/dev/input/js0` y `ros-jazzy-joy` está instalado.

---

## Parte 1 bis. Arrancar `joy_node` en el carro

**[CARRITO — Terminal 1]**

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0 -p deadzone:=0.0'
```

**Esperado:** una línea `Opened joystick: Nintendo Switch Pro Controller`. Se queda ahí sin
devolver el prompt: es lo correcto. **Deja esta terminal corriendo el resto de la guía.**

> **El `sudo` no es opcional.** Sin él `joy_node` arranca igual, no da error, y `/joy` no llega
> a ningún sitio. Vuelve a leer §0.2 ter si te lo saltaste.

> **Los dos parámetros importan, no los quites.**
> `autorepeat_rate:=20.0` hace que `joy_node` siga publicando aunque no muevas nada. Sin él,
> mantener el stick quieto deja de generar mensajes, el hombre muerto salta a los 0,6 s y **el
> carro se para solo mientras conduces**.
> `deadzone:=0.0` evita encadenar dos zonas muertas, porque el programa ya tiene la suya.

---

## Parte 2. Averiguar qué número tiene cada control

Los números de eje y de botón que trae el programa por defecto son los habituales, pero
**cambian entre versiones del kernel**. Comprobarlo cuesta un minuto. Descubrirlo con el carro
en marcha, no.

`joy_node` ya está corriendo desde la Parte 1 bis. Aquí solo se mira lo que publica.

### Paso 2.1 — Ver qué publica el mando

Abre una **segunda sesión SSH al carro** sin cerrar la anterior.

**[CARRITO — Terminal 2]**

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /joy'
```

Van a salir mensajes en bucle, con dos listas: `axes` (los sticks y gatillos) y `buttons` (los
botones, 0 o 1).

**Mueve un control cada vez** y mira qué posición de la lista `axes` cambia. Las posiciones se
cuentan **empezando en 0**. Anota los cuatro:

| Mueve esto | Parámetro del programa | Valor **medido el 2026-09-01, mando por USB al carro** |
|---|---|---|
| Stick **izquierdo**, arriba y abajo | `eje_traccion` | `1` |
| Stick **derecho**, izquierda y derecha | `eje_direccion` | `2` |
| Gatillo **ZR** (el de atrás, derecha) | `eje_habilitar` | `5` |
| Gatillo **ZL** (el de atrás, izquierda) | `eje_turbo` | `4` |

Estos cuatro son los que trae el programa por defecto, y son los que se midieron **en esta
configuración exacta** —mando por USB al carro, `joy_node` como `root`, un solo mando
conectado—. Coinciden con el orden estándar de SDL (`LEFTX, LEFTY, RIGHTX, RIGHTY,
TRIGGERLEFT, TRIGGERRIGHT`).

> **ZR y ZL son ejes, no botones.** Aunque en el mando se sienten como botones, SDL los reporta
> como gatillos analógicos: valen **`+1.0` sueltos** y **`-1.0` pulsados a fondo**, y van en la
> lista `axes`, no en `buttons`. El programa los lee así, con umbral en `-0.5`.

> **El gatillo sin estrenar leyéndose `0.0` no es una hipótesis: pasó.** En la medición del
> 2026-09-01, ZR y ZL valían `0.0` —no `+1.0`— hasta que se tocaron por primera vez. Con el
> umbral en `-0.5` eso cuenta como *sin pulsar*, que es el lado seguro. Si el umbral fuera
> positivo, **el carro habría arrancado habilitado él solo**. La prueba de escritorio cubre
> este caso desde antes de que ocurriera.

**Si te salen 1, 2, 5 y 4**, no tienes que pasar nada al programa: son los que trae.
**Si alguno sale distinto**, apúntalo. En el Paso 4.3 hay que pasarlos.

Cierra este `ros2 topic echo` con `Ctrl-C` cuando termines. **La Terminal 1 sigue corriendo.**

> **Si `ros2 topic echo /joy` no saca nada**, no es el mando: es el `sudo`. Comprueba que
> `joy_node` **y** este `echo` van los dos con `sudo` (§0.2 ter). Un `echo` sin `sudo` tampoco
> ve al `joy_node` que sí lo tiene.

**Criterio de cierre de la Parte 2:** tienes anotados los cuatro números.

---

## Parte 3. Llevar el programa al carrito

### Paso 3.1 — Averiguar la IP del carro

La IP la reparte el router y **cambia entre sesiones** (el 19-ago era `192.168.0.101`, el
21-ago ya era `.102`). No la des por sabida.

**[PORTÁTIL — Terminal 2]**

```bash
ping -c 2 deepracer.local
```

**Esperado:** dos respuestas, y en ellas la IP entre paréntesis. Anótala.
**Si no responde:** busca la IP en la página de administración del router.

De aquí en adelante, donde ponga `<IP>` escribe esa dirección.

### Paso 3.2 — Copiar el programa

**[PORTÁTIL — Terminal 2]**, desde la **raíz del repositorio** —esté donde esté tu clon—:

```bash
scp herramientas/teleop_mando.py deepracer@<IP>:~/
```

**Esperado:** te pide la contraseña del carro y luego muestra `teleop_mando.py 100%`.

---

## Parte 4. Arrancar

### Paso 4.1 — Comprobar que `/joy` se publica de verdad

**[CARRITO — Terminal 2]**

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && timeout 5 ros2 topic hz /joy'
```

**Esperado:** líneas con `average rate: 20.0` más o menos.
**Si dice que no recibe nada:** el `sudo`. Ver §0.2 ter y el aviso del final de la Parte 2.

### Paso 4.2 — Entrar al carrito con `ssh -t`

Si vas a arrancar el teleop desde una sesión nueva, **usa `-t`**:

**[PORTÁTIL]**

```bash
ssh -t deepracer@<IP>
```

> **`-t` no es opcional para el teleop.** Sin él la sesión SSH no reserva un terminal, y
> **`Ctrl-C` nunca llega al proceso de Python**: el programa sigue vivo con la última orden y
> tú creyendo que lo cerraste. Con `-t` funciona.

### Paso 4.3 — Arrancar el programa

Hacen falta **dos `source`**, no uno. El primero es ROS. El segundo es el de AWS, que es donde
vive `deepracer_interfaces_pkg` —el paquete que define `ServoCtrlMsg`—, y que **no** está en
`/opt/ros/jazzy`. Sin el segundo, el programa muere con
`ModuleNotFoundError: No module named 'deepracer_interfaces_pkg'`.

Si en la Parte 2 te salieron **1, 2, 5 y 4**:

**[CARRITO — Terminal 3]**

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~deepracer/teleop_mando.py'
```

Si te salió **algún número distinto**, pásalos todos (cambia los valores por los tuyos):

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~deepracer/teleop_mando.py --ros-args -p eje_traccion:=1 -p eje_direccion:=2 -p eje_habilitar:=5 -p eje_turbo:=4'
```

> **La ruta va completa, no `~/`.** Con `sudo -i` el `~` es `/root`, no el del usuario `deepracer`, y el
> fichero no está ahí.

**Esperado:** una línea de registro que dice qué botón habilita, cuál es el turbo y qué límites
tiene. Se queda ahí, sin devolverte el prompt. Es lo correcto.

**Deja esta terminal corriendo.**

**Criterio de cierre de la Parte 4:** `/joy` va a ~20 Hz y el teleop está arrancado sin errores.

---

## Parte 5. Los controles

| Control | Qué hace |
|---|---|
| **ZR** (mantener pulsado) | Habilita. Sin esto el carro no se mueve, pase lo que pase |
| Stick **izquierdo** arriba / abajo | Adelante / atrás |
| Stick **derecho** izquierda / derecha | Girar |
| **ZL** (mantener, a la vez que ZR) | Turbo: sube el límite de 0,35 a 0,70 |
| Soltar **ZR** | Para |
| `Ctrl-C` en la Terminal 3 | Sale del programa y manda diez ceros |

---

## Parte 6. Prueba de seguridad, con el carro en alto

**Levanta el carro y déjalo con las ruedas al aire.** Los seis puntos, en este orden:

1. **Sin tocar nada:** las ruedas **no** giran.

2. **Pulsa ZR sin tocar los sticks:** las ruedas **no** giran.

3. **ZR + stick izquierdo hacia arriba:** las ruedas giran **hacia adelante**.
   - *Si giran hacia atrás:* `Ctrl-C` en la Terminal 3 y vuelve a arrancar añadiendo
     `-p invertir_traccion:=true` al final del comando del Paso 4.3.

   > **Esto ya se midió, y el valor por defecto cambió por ello.** El 2026-09-01, con
   > `invertir_traccion` en `True` —lo que traía el programa—, el stick hacia adelante daba
   > **marcha atrás**, y hacia atrás daba adelante y con muy poca fuerza. Se comprobó sin el
   > mando de por medio, publicando valores de tracción conocidos y mirando las ruedas en el
   > aire: **`throttle` positivo mueve el vehículo hacia adelante**. Con eso, la bandera
   > correcta es `False`, que es la que trae ahora el programa.
   >
   > La asimetría que se sintió —"hacia atrás giraban muy poco, como si se quedaran sin
   > fuerza"— **es real y no está resuelta**: con el signo invertido, la dirección que en el
   > mando parecía "atrás" era la buena y aun así arrancaba floja. Queda como observación, no
   > como defecto diagnosticado.

4. **ZR + stick derecho hacia la derecha:** las ruedas de dirección giran **a la derecha**.
   - *Si giran a la izquierda:* `Ctrl-C` y vuelve a arrancar añadiendo
     `-p invertir_direccion:=true`.
   - Medido el 2026-09-01: la dirección responde correctamente con el valor por defecto
     (`invertir_direccion=False`). No hubo que tocarla.

5. **Con ZR pulsado y el stick de tracción dado, mata `joy_node`.** Las ruedas tienen que
   **parar en menos de un segundo**.

   Por USB el mando **no se puede apagar** —se alimenta del carro, el botón Home no lo apaga— y
   **desenchufarlo está prohibido con la pila corriendo** (§0.2: mata el LiDAR). Así que el
   corte de `/joy` se provoca desde el teclado, en la otra sesión:

   **[CARRITO — Terminal 2]**

   ```bash
   sudo pkill -x joy_node
   ```

   > **Usa `-x`, no `-f`.** Con `-f` el patrón casa también con **la línea de comandos del
   > propio `bash` que lo lanza**, y `pkill` se mata a sí mismo o a la sesión. Este falso
   > positivo apareció **tres veces** el 2026-09-01. Si necesitas mirar antes qué hay,
   > `pgrep -af joy_node` y **lee las líneas**, no cuentes PIDs.

   Después de esta comprobación, vuelve a arrancar `joy_node` (Parte 1 bis) antes de seguir.

6. **`Ctrl-C` en la Terminal 3:** las ruedas quedan quietas.

7. **Cierra la Terminal 3 de golpe** (la `X` de la ventana, o `exit` mientras el programa corre)
   con ZR pulsado y stick dado. Las ruedas tienen que **parar**.
   - *Esto es la caída de la sesión SSH.* Hasta el 2026-09-01 **no paraba**, y era el único de
     los siete puntos que fallaba.

> **Los puntos 5 y 7 son las dos comprobaciones que de verdad importan**, y prueban cosas
> distintas: el 5 es el hombre muerto —el programa sigue vivo y deja de recibir `/joy`—, el 7 es
> la muerte del programa entero, que el hombre muerto **no** cubre.
> **Si falla cualquiera de los dos, no bajes el carro al suelo.**

Vuelve a arrancar `joy_node` y el programa antes de seguir.

---

## Parte 7. Conducir

Baja el carro al suelo, en un espacio despejado. Mantén **ZR** y da poco stick al principio: el
carro llega a 4 m/s y el límite normal ya está al 0,35 justamente por eso.

**Cuidado con el cable.** El mando va enchufado al carro, así que el carro se lleva el cable
consigo. Si el cable se tensa y se sale, `/joy` deja de llegar y el hombre muerto para el carro
—correcto— pero **el LiDAR se muere en silencio** (§0.2) y no te enteras hasta que intentas
grabar. Después de cualquier tirón, comprueba el LiDAR antes de dar nada por bueno.

Si te parece rápido, arráncalo más suave:

**[CARRITO — Terminal 3]**

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~deepracer/teleop_mando.py --ros-args -p limite_normal:=0.20 -p limite_turbo:=0.40'
```

Si te parece lento —al usuario se lo pareció el 2026-09-01—, la configuración que se condujo de
verdad fue:

```bash
sudo -i bash -c 'source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~deepracer/teleop_mando.py --ros-args -p limite_normal:=0.70 -p limite_turbo:=1.0'
```

**Criterio de cierre de toda la guía:** conduces el carro por el suelo con ZR, para al soltar
ZR, y para al matar `joy_node`. **Alcanzado el 2026-09-01.**

---

## Parte 8. Si algo falla

| Lo que ves | Causa probable | Qué hacer |
|---|---|---|
| **Todo arranca bien, ningún error, y el carro no se mueve** | **Te faltó el `sudo`.** Es el fallo número uno y no avisa de nada | §0.2 ter. Mata todo y relanza con `sudo -i bash -c '...'` |
| `ros2 topic echo /joy` no saca nada, pero `joy_node` corre | Uno de los dos va sin `sudo`. Tienen que ir **los dos** | Relanza los dos con `sudo` |
| No sale `/dev/input/js0` | El mando no está enchufado, o el cable es solo de carga | Paso 1.2. Prueba otro cable antes de nada |
| **El carro se para solo cada segundo mientras conduces** | Arrancaste `joy_node` sin `autorepeat_rate` | Repite la Parte 1 bis con el comando completo |
| `/joy` publica pero el carro no responde a ZR | El número de `eje_habilitar` está mal | Repite la Parte 2 mirando qué cambia al pulsar ZR |
| El programa avisa de que hay pocos ejes | El mando conectado no es el que crees | Repite la Parte 2 |
| `ModuleNotFoundError: No module named 'deepracer_interfaces_pkg'` | Te faltó el segundo `source`, el de AWS | Comando completo del Paso 4.3, con `source /opt/aws/deepracer/lib/setup.bash` |
| `python3: can't open file '/root/teleop_mando.py'` | Con `sudo -i` el `~` es `/root` | Usa `~deepracer/teleop_mando.py` |
| Va atrás cuando pides adelante | Signo de la tracción | `-p invertir_traccion:=true`. Medido el 01-sep: el correcto es `false` |
| **`Ctrl-C` no cierra el teleop** | Entraste por SSH **sin `-t`**, y la señal no llega al proceso de Python | Paso 4.2. Mientras tanto, mátalo desde la otra sesión con `sudo pkill -x -f teleop_mando` |
| `pkill`/`pgrep` te dicen que hay procesos que no existen | **El patrón casa con la línea de comandos del propio `bash`/`ssh` que lo lanza** | `pgrep -af` y **lee las líneas**. Pasó tres veces el 01-sep |
| **El LiDAR deja de publicar y `systemctl` dice `active`** | **Enchufaste o desenchufaste algo por USB con la pila corriendo.** El nodo se queda con un descriptor a `/dev/ttyUSB0 (deleted)` | Para la pila, enchufa, arranca la pila. §0.2 |
| **Todo «deja de funcionar» poco a poco** | **Se están descargando las baterías.** Ya pasó el 28-ago: se plantearon tres causas de software y las tres eran falsas | Mide las baterías **antes** de depurar nada |
| **El carro deja de responder de golpe** | `deepracer-core` se reinició solo. `systemctl` sigue diciendo `active (running)` y no lo delata | Compruébalo por los **GID de los publicadores** del tópico, no por `systemctl`. Ha pasado dos veces |
| Se te ocurre reiniciar el carro | — | **No.** §0.2 bis. Se queda en GRUB y hay que ir físicamente |

> **Tres de estas filas son la misma historia: `active` miente.** El servicio dice que corre, el
> proceso existe, y aun así no hay nadie al otro lado. En este proyecto ha pasado con
> `deepracer-core` reiniciándose solo, con el LiDAR tras el USB, y con cualquier nodo lanzado
> sin `sudo`. **Comprueba siempre por el dato que sale, nunca por el estado del servicio.**

---

## Anexo B. Emparejar el mando al portátil por Bluetooth

**Este NO es el camino de la guía.** Está aquí porque se midió el 31-ago y funciona, y porque
si algún día se conduce sin cable tendrá que ser por aquí. Tiene dos pegas sin resolver: hace
falta que `/joy` cruce de Humble a Jazzy por wifi —**nunca comprobado**— y el carro se para
solo cada vez que la red parpadea.

**No hay plan «emparejar el mando al carrito»: el carro no tiene radio Bluetooth** (§0.2). Si
este anexo tampoco sirve, las opciones son un adaptador USB Bluetooth o el teleop de teclado.

### Paso B.1 — Comprobar que el portátil tiene lo necesario

**[PORTÁTIL]**

```bash
uname -r
```

**Esperado:** `6.8.0-138-generic` o cualquier número **5.16 o superior**.
El módulo del kernel que entiende el Pro Controller (`hid-nintendo`) existe desde la 5.16, así
que no hay que instalar ningún driver.
**Si sale menos de 5.16:** para aquí. El mando emparejaría pero no aparecería como joystick.

```bash
bluetoothctl list
```

**Esperado:** `Controller D8:80:83:5E:C1:D8 SantiagoPC [default]`.
**Si no sale nada:** el portátil no tiene Bluetooth usable. No hay camino.

### Paso B.2 — Poner el mando en modo emparejamiento

Esto se hace **en el mando**, no en el teclado.

1. Enciende el mando pulsando cualquier botón.
2. En el **borde de arriba** del mando, justo al lado del hueco USB-C, hay un **botón pequeño y
   redondo**. Ese es el botón **Sync**. Es el único botón que hay en ese borde.
3. Mantenlo pulsado **2 segundos** y suéltalo.
4. Mira los **cuatro LED** de la parte de abajo del mando. Tienen que ir **corriendo de
   izquierda a derecha en bucle**, como las luces del coche fantástico.

**Si los LED están fijos o apagados:** no entró en modo emparejamiento. Repite el punto 3.

> **Dos cosas que hacen fallar este paso:**
> - El modo emparejamiento **caduca a los ~30 segundos**. Si tardas, se sale solo y hay que
>   volver a pulsar Sync.
> - Si hay una **Switch encendida cerca**, el mando se reengancha a ella antes de que puedas
>   emparejarlo. Apágala o aléjate.

> Un Pro Controller solo puede estar emparejado con **un** aparato a la vez. Si venía de una
> Switch, se desemparejará de ella. Para devolverlo a la Switch, conéctalo por cable una vez.

### Paso B.3 — Buscar el mando

**Con los LED corriendo**, en el portátil:

**[PORTÁTIL]**

```bash
bluetoothctl
```

El prompt cambia y ahora escribes **dentro** de `bluetoothctl`, una orden por línea:

```
power on
```
```
agent on
```
```
default-agent
```
```
scan on
```

Van a salir muchas líneas `[NEW] Device ...`. **Ignóralas todas menos una.** Buscas
exactamente esta, con el nombre escrito:

```
[NEW] Device 98:B6:E9:XX:XX:XX Pro Controller
```

Los dispositivos sin nombre, tipo `[NEW] Device 36:2A:7C:74:93:9C 36-2A-7C-74-93-9C`, **no son
el mando**: son relojes, audífonos o móviles de alrededor.

**Anota la MAC que sale junto a `Pro Controller`.** Es lo que vas a escribir en el paso
siguiente.

**Si en 30 segundos no sale `Pro Controller`:** los LED se apagaron. Sin cerrar
`bluetoothctl`, vuelve a pulsar Sync 2 segundos en el mando y sigue mirando la consola.

### Paso B.4 — Emparejar

Sigues **dentro de `bluetoothctl`**. Sustituye `98:B6:E9:XX:XX:XX` por la MAC que anotaste, en
las tres órdenes:

```
scan off
```
```
pair 98:B6:E9:XX:XX:XX
```
```
trust 98:B6:E9:XX:XX:XX
```
```
connect 98:B6:E9:XX:XX:XX
```
```
quit
```

**Esperado:** `Pairing successful` y después `Connection successful`.

`trust` es lo que hace que en adelante el mando reconecte solo con encenderlo. Si te lo saltas,
tendrás que repetir toda la Parte 1 cada vez.

### Paso B.5 — Comprobar que salió bien

Dos comprobaciones, y las dos tienen que dar bien:

1. **En el mando:** queda **un solo LED encendido y fijo** (el primero). Ya no corren.

2. **[PORTÁTIL]**

```bash
grep -A5 "Pro Controller" /proc/bus/input/devices
```

**Esperado:** dos bloques, `Pro Controller` y `Pro Controller (IMU)`, cada uno con una línea
`Handlers=eventNN`.
**Si no sale nada:** el emparejado se hizo pero el kernel no lo tomó. Vete al Paso B.6.

> **No compruebes esto con `ls /dev/input/js*`.** En este portátil el mando **no** crea un nodo
> `js`, y aun así funciona: el nodo `joy` de Humble usa SDL2, que lee `/dev/input/event*`.
> Buscar `js0` te haría creer que el emparejado falló cuando está perfecto.

**Criterio de cierre del Anexo B:** el mando aparece en `/proc/bus/input/devices` con un
`Handlers=eventNN`, y tiene un LED fijo.

---

### Paso B.6 — Emparejó, pero el kernel no lo tomó

**[PORTÁTIL]**

```bash
dmesg | tail -20
```

Busca líneas que mencionen `nintendo` o `hid`. Luego, dentro de `bluetoothctl`, desconecta y
vuelve a conectar:

```
disconnect 98:B6:E9:XX:XX:XX
```
```
connect 98:B6:E9:XX:XX:XX
```

Si sigue igual, comprueba que el módulo está cargado:

```bash
lsmod | grep nintendo
```

**Esperado:** una línea con `hid_nintendo`.
**Si no sale:** `sudo modprobe hid-nintendo` y reconecta.

### Paso B.7 — Problemas conocidos del emparejado

| Lo que ves | Causa | Qué hacer |
|---|---|---|
| No sale `Pro Controller` al escanear | Los LED dejaron de correr, o hay una Switch cerca | Vuelve a pulsar Sync 2 s. Apaga la Switch |
| `connect` falla con `br-connection-create-socket` | El Pro Controller es quien inicia la conexión, no el portátil | Pulsa **Home** en el mando. Al estar `Trusted`, reconecta solo |
| El mando no reconecta al encenderlo | Te saltaste `trust` | `bluetoothctl` y luego `trust <MAC>` |

Si consigues emparejarlo, sigue por la Parte 2 de la guía, pero con `joy_node` en el
**portátil** (`source /opt/ros/humble/setup.bash`) y comprobando con `ros2 topic hz /joy`
**en el carro** que los mensajes cruzan. Si no cruzan, mira que ninguna de las dos máquinas
tenga `ROS_DOMAIN_ID` exportado.

---

## Parte 9. Lo que esta herramienta no es

Esto **no** es la cadena `/cmd_vel` arreglada. Es el mismo puente que el teleop de teclado del
28-ago, con otro aparato de entrada.

El programa publica `ServoCtrlMsg` **directamente** en `/ctrl_pkg/servo_msg`, saltándose
`/cmd_vel` a propósito, porque esa cadena tiene dos defectos independientes ya documentados
(§6.1 de [`S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md)): el nodo publicaba
en `/cmdvel_to_servo_pkg/servo_msg` mientras `servo_pkg` escucha en `/ctrl_pkg/servo_msg`, y la
conversión de tracción tiene las ramas en un orden que hace que la primera se trague las demás.

Los dos defectos siguen abiertos, y **Nav2 sobre el carro real seguirá necesitándolos
resueltos**, porque Nav2 publica en `/cmd_vel`. Conviene no anotar esto como «control del
vehículo resuelto».
