# Conducir el DeepRacer físico con un mando de Nintendo Switch Pro

Guía de principio a fin. Cada comando dice **en qué máquina y en qué terminal** va.
No te saltes pasos: están en este orden porque cada uno comprueba algo que el siguiente da por hecho.

El programa es [`herramientas/teleop_mando.py`](../herramientas/teleop_mando.py).

---

## Parte 0. Antes de empezar

### 0.1 Las dos máquinas

Vas a usar dos computadores a la vez. A lo largo de la guía se llaman así:

- **PORTÁTIL** — tu PC, Ubuntu 22.04 con ROS 2 Humble. Aquí se empareja el mando.
- **CARRITO** — la tarjeta del DeepRacer, Ubuntu 24.04 con ROS 2 Jazzy. Se entra por SSH.

Al final vas a tener **cuatro terminales abiertas**:

| Terminal | Máquina | Qué corre ahí |
|---|---|---|
| 1 | PORTÁTIL | `joy_node` — lee el mando y publica `/joy` |
| 2 | PORTÁTIL | Comprobaciones sueltas |
| 3 | CARRITO (SSH) | `teleop_mando.py` — manda al servo |
| 4 | CARRITO (SSH) | Comprobaciones sueltas |

### 0.2 Por qué el mando se empareja al portátil y no al carrito

`teleop_mando.py` corre **siempre en el carrito**, porque es lo que le da órdenes al motor.
Si corriera en el portátil y se cayera el wifi, el carro se quedaría con la última orden
recibida: acelerando y sin nadie al mando.

`joy_node` da igual dónde corra. Si se cae el wifi, `/joy` deja de llegar y el hombre muerto
salta **dentro del carrito**, que para solo. Por eso emparejamos al portátil: su Bluetooth ya
está comprobado y el de la tarjeta del DeepRacer no.

### 0.3 Las cuatro protecciones que tiene el programa

1. **Botón de habilitación.** El carro solo se mueve mientras mantienes pulsado **ZR**.
2. **Hombre muerto de 0,6 s.** Si `/joy` deja de llegar —mando apagado, wifi caído, `joy_node`
   muerto—, el carro para.
3. **Diez ceros al salir**, tanto con `Ctrl-C` como si el programa revienta.
4. **Límite de velocidad** al 0,35 del rango, 0,70 con turbo. El carro llega a 4 m/s.

### 0.4 Lo que necesitas a mano

- El mando, cargado.
- El carro encendido y en la misma red wifi que el portátil.
- Algo para levantar el carro y dejar **las ruedas al aire** (una caja, un libro grueso).
  No es opcional: la Parte 6 se hace así.

---

## Parte 1. Emparejar el mando al portátil

### Paso 1.1 — Comprobar que el portátil tiene lo necesario

**[PORTÁTIL — Terminal 2]**

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
**Si no sale nada:** el portátil no tiene Bluetooth usable, vete al Anexo A.

### Paso 1.2 — Poner el mando en modo emparejamiento

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

### Paso 1.3 — Buscar el mando

**Con los LED corriendo**, en el portátil:

**[PORTÁTIL — Terminal 2]**

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

### Paso 1.4 — Emparejar

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

### Paso 1.5 — Comprobar que salió bien

Dos comprobaciones, y las dos tienen que dar bien:

1. **En el mando:** queda **un solo LED encendido y fijo** (el primero). Ya no corren.

2. **[PORTÁTIL — Terminal 2]**

```bash
grep -A5 "Pro Controller" /proc/bus/input/devices
```

**Esperado:** dos bloques, `Pro Controller` y `Pro Controller (IMU)`, cada uno con una línea
`Handlers=eventNN`.
**Si no sale nada:** el emparejado se hizo pero el kernel no lo tomó. Vete al Anexo A.

> **No compruebes esto con `ls /dev/input/js*`.** En este portátil el mando **no** crea un nodo
> `js`, y aun así funciona: el nodo `joy` de Humble usa SDL2, que lee `/dev/input/event*`.
> Buscar `js0` te haría creer que el emparejado falló cuando está perfecto.

**Criterio de cierre de la Parte 1:** el mando aparece en `/proc/bus/input/devices` con un
`Handlers=eventNN`, y tiene un LED fijo.

---

## Parte 2. Averiguar qué número tiene cada control

Los números de eje y de botón que trae el programa por defecto son los habituales, pero
**cambian entre versiones del kernel**. Comprobarlo cuesta un minuto. Descubrirlo con el carro
en marcha, no.

### Paso 2.1 — Arrancar `joy_node`

**[PORTÁTIL — Terminal 1]**

```bash
source /opt/ros/humble/setup.bash && ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0 -p deadzone:=0.0
```

**Deja esta terminal corriendo el resto de la guía.** No la cierres.

> **Los dos parámetros importan, no los quites.**
> `autorepeat_rate:=20.0` hace que `joy_node` siga publicando aunque no muevas nada. Sin él,
> mantener el stick quieto deja de generar mensajes, el hombre muerto salta a los 0,6 s y **el
> carro se para solo mientras conduces**.
> `deadzone:=0.0` evita encadenar dos zonas muertas, porque el programa ya tiene la suya.

### Paso 2.2 — Ver qué publica el mando

**[PORTÁTIL — Terminal 2]**

```bash
source /opt/ros/humble/setup.bash && ros2 topic echo /joy
```

Van a salir mensajes en bucle, con dos listas: `axes` (los sticks y gatillos) y `buttons` (los
botones, 0 o 1).

**Mueve un control cada vez** y mira qué posición de la lista `axes` cambia. Las posiciones se
cuentan **empezando en 0**. Anota los cuatro:

| Mueve esto | Parámetro del programa | Valor medido el 31-ago |
|---|---|---|
| Stick **izquierdo**, arriba y abajo | `eje_traccion` | `1` |
| Stick **derecho**, izquierda y derecha | `eje_direccion` | `2` |
| Gatillo **ZR** (el de atrás, derecha) | `eje_habilitar` | `5` |
| Gatillo **ZL** (el de atrás, izquierda) | `eje_turbo` | `4` |

> **ZR y ZL son ejes, no botones.** Aunque en el mando se sienten como botones, SDL los reporta
> como gatillos analógicos: valen **`+1.0` sueltos** y **`-1.0` pulsados a fondo**, y van en la
> lista `axes`, no en `buttons`. El programa los lee así, con umbral en `-0.5`. Si un gatillo no
> se ha tocado nunca desde que arrancó `joy_node` puede leerse `0.0`, que con ese umbral cuenta
> como *sin pulsar* — el lado seguro.

Los cuatro son los del orden estándar de SDL (`LEFTX, LEFTY, RIGHTX, RIGHTY, TRIGGERLEFT,
TRIGGERRIGHT`), así que lo más probable es que te salgan iguales.

**Si te salen 1, 2, 5 y 4**, no tienes que pasar nada al programa: son los que trae.
**Si alguno sale distinto**, apúntalo. En el Paso 4.2 hay que pasarlos.

Cierra este `ros2 topic echo` con `Ctrl-C` cuando termines. **La Terminal 1 sigue corriendo.**

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

### Paso 4.1 — Entrar al carrito

**[CARRITO — Terminal 3]**

```bash
ssh deepracer@<IP>
```

### Paso 4.2 — Arrancar el programa

Hacen falta **dos `source`**, no uno. El primero es ROS. El segundo es el de AWS, que es donde
vive `deepracer_interfaces_pkg` —el paquete que define `ServoCtrlMsg`—, y que **no** está en
`/opt/ros/jazzy`. Sin el segundo, el programa muere con
`ModuleNotFoundError: No module named 'deepracer_interfaces_pkg'`.

Si en la Parte 2 te salieron **1, 2, 5 y 4**:

**[CARRITO — Terminal 3]**

```bash
source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~/teleop_mando.py
```

Si te salió **algún número distinto**, pásalos todos (cambia los valores por los tuyos):

```bash
source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~/teleop_mando.py --ros-args -p eje_traccion:=1 -p eje_direccion:=2 -p eje_habilitar:=5 -p eje_turbo:=4
```

**Esperado:** una línea de registro que dice qué botón habilita, cuál es el turbo y qué límites
tiene. Se queda ahí, sin devolverte el prompt. Es lo correcto.

**Deja esta terminal corriendo.**

### Paso 4.3 — Comprobar que `/joy` llega desde el portátil al carrito

**Este paso es el que más probable es que falle**, porque el portátil es Humble y el carrito es
Jazzy, y nunca hemos comprobado en este proyecto que se hablen entre sí.

Abre una **segunda sesión SSH**, sin cerrar la anterior:

**[CARRITO — Terminal 4]**

```bash
ssh deepracer@<IP>
```

```bash
source /opt/ros/jazzy/setup.bash && ros2 topic hz /joy
```

**Esperado:** líneas con `average rate: 20.0` más o menos.

**Si dice que no recibe nada:**

1. Comprueba que las dos máquinas están en la misma red wifi.
2. Comprueba que **ninguna** de las dos tiene `ROS_DOMAIN_ID` exportado. En cada una:
   `echo $ROS_DOMAIN_ID` tiene que salir vacío.
3. Si sigue sin llegar, las dos distribuciones no se están hablando. **Vete al Anexo B**, que
   empareja el mando directamente al carrito y evita el problema.

Cierra el `ros2 topic hz` con `Ctrl-C`. **Deja la Terminal 4 abierta**, la vas a necesitar.

**Criterio de cierre de la Parte 4:** el carrito recibe `/joy` a ~20 Hz.

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
     `-p invertir_traccion:=false` al final del comando del Paso 4.2.

4. **ZR + stick derecho hacia la derecha:** las ruedas de dirección giran **a la derecha**.
   - *Si giran a la izquierda:* `Ctrl-C` y vuelve a arrancar añadiendo
     `-p invertir_direccion:=true`.

5. **Con ZR pulsado y el stick de tracción dado, apaga el mando** (botón Home, 3 segundos).
   Las ruedas tienen que **parar en menos de un segundo**.

6. **`Ctrl-C` en la Terminal 3:** las ruedas quedan quietas.

> **El punto 5 es la única comprobación que de verdad importa.** Prueba el hombre muerto.
> **Si el punto 5 falla, no bajes el carro al suelo.**

Vuelve a encender el mando y a arrancar el programa antes de seguir.

---

## Parte 7. Conducir

Baja el carro al suelo, en un espacio despejado. Mantén **ZR** y da poco stick al principio: el
carro llega a 4 m/s y el límite normal ya está al 0,35 justamente por eso.

Si aun así te parece rápido, arráncalo más suave:

**[CARRITO — Terminal 3]**

```bash
source /opt/ros/jazzy/setup.bash && source /opt/aws/deepracer/lib/setup.bash && python3 ~/teleop_mando.py --ros-args -p limite_normal:=0.20 -p limite_turbo:=0.40
```

**Criterio de cierre de toda la guía:** conduces el carro por el suelo con ZR, para al soltar
ZR, y para al apagar el mando.

---

## Parte 8. Si algo falla

| Lo que ves | Causa probable | Qué hacer |
|---|---|---|
| No sale `Pro Controller` al escanear | Los LED dejaron de correr, o hay una Switch cerca | Vuelve a pulsar Sync 2 s. Apaga la Switch |
| Emparejó pero no aparece en `/proc/bus/input/devices` | El kernel no lo tomó | Anexo A |
| El carrito no recibe `/joy` | Humble y Jazzy no se están hablando, o distinta red | Paso 4.3, y si no, Anexo B |
| **El carro se para solo cada segundo mientras conduces** | Arrancaste `joy_node` sin `autorepeat_rate` | Repite el Paso 2.1 con el comando completo |
| `/joy` publica pero el carro no responde a ZR | El número de `boton_habilitar` está mal | Repite la Parte 2 mirando qué cambia al pulsar ZR |
| El programa avisa de que hay pocos ejes | El mando conectado no es el que crees | Repite la Parte 2 |
| `ModuleNotFoundError: No module named 'deepracer_interfaces_pkg'` | Te faltó el segundo `source`, el de AWS | Usa el comando completo del Paso 4.2, con `source /opt/aws/deepracer/lib/setup.bash` |
| `bluetoothctl connect` falla con `br-connection-create-socket` | Estás intentando conectar desde el portátil, pero el Pro Controller es el que inicia la conexión | Pulsa **Home** en el mando. Al estar `Trusted`, reconecta solo |
| Va adelante cuando pides atrás | Signo del eje | Añade `-p invertir_traccion:=false` |
| El mando no reconecta al encenderlo | Te saltaste `trust` | `bluetoothctl` y luego `trust <MAC>` |
| **Todo «deja de funcionar» poco a poco** | **Se están descargando las baterías.** Ya pasó el 28-ago: se plantearon tres causas de software y las tres eran falsas | Mide las baterías **antes** de depurar nada |
| **El carro deja de responder de golpe** | `deepracer-core` se reinició solo. `systemctl` sigue diciendo `active (running)` y no lo delata | Compruébalo por los **GID de los publicadores** del tópico, no por `systemctl`. Ha pasado dos veces |

---

## Anexo A. Emparejó, pero el kernel no lo tomó

**[PORTÁTIL — Terminal 2]**

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

---

## Anexo B. Plan B: emparejar el mando al carrito

Solo si el Paso 4.3 falló y no conseguiste que `/joy` cruzara del portátil al carrito.

Aquí **todo** corre en el carrito, así que el mando se empareja allí.

**[CARRITO — Terminal 4]**

```bash
sudo apt install ros-jazzy-joy
```

Repite las **Partes 1 y 2 completas por SSH**, con dos cambios:

- Todos los comandos van en la Terminal 4, no en el portátil.
- Donde la guía dice `source /opt/ros/humble/setup.bash`, escribe
  `source /opt/ros/jazzy/setup.bash`.

Sigue luego desde la Parte 4. El Paso 4.3 ya no hace falta: `/joy` no cruza ninguna red.

**Si el carrito no tiene Bluetooth** (`bluetoothctl list` no devuelve nada), no hay plan C con
este mando: haría falta un adaptador USB Bluetooth, o conducir con el teleop de teclado.

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
