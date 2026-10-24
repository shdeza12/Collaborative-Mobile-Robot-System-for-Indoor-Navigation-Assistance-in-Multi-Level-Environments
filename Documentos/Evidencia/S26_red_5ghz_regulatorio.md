# La WiFi de los dos vehículos no podía transmitir en 5 GHz (5 de octubre)

Sesión de red con Jonny, desde el portátil y por SSH a los dos vehículos. El objetivo era decidir
cómo montar la WiFi para el sitio nuevo —dos pisos, un punto de acceso por planta— y de paso
entender por qué en una sesión anterior un vehículo no respondía al `ping` **estando al lado del
punto de acceso**.

## Resultado

**Los dos vehículos tenían cero canales de 5 GHz utilizables**, y no por falta de hardware: la
tarjeta los soporta. Faltaba `/lib/firmware/regulatory.db`, así que el kernel se quedaba sin reglas
de ningún país y dejaba las 31 frecuencias de 5 GHz en `no IR` —la radio escucha y no transmite—.

Es un defecto de la imagen del DeepRacer, no algo que el equipo rompiera. Y es **mudo**: el vehículo
ve las redes de 5 GHz en el barrido, las lista, y al intentar conectarse falla sin decir por qué.

Instalada la base y reiniciado, los dos pasaron a **13 canales utilizables**, con el 36, 40, 44 y 48
a 23 dBm. Con eso se midió RF-15 entre los dos vehículos sobre 5 GHz: **`CUMPLE`, con el p95 a la
mitad** del de septiembre.

---

## 1. El hallazgo

### 1.1 Lo que se veía

El síntoma inicial lo describió Jonny: en pruebas anteriores un vehículo no daba `ping` aunque
estuviera cerca del punto de acceso. Y hay un descarte que ahorra tiempo y conviene dejar escrito:

> **No era `ufw`.** La firma del cortafuegos en este proyecto está documentada y es la contraria
> —*«`ping` al 100 % y grafo ROS vacío»*, porque `ufw` deja pasar ICMP y bloquea lo demás
> ([`S19_spike_p1_p2_hardware.md`](S19_spike_p1_p2_hardware.md) §3.1)—. **Si no hay `ping`, el
> cortafuegos no es el culpable.**

### 1.2 La primera comprobación, que estuvo mal hecha

Se comprobó si las tarjetas soportaban 5 GHz contando las frecuencias que lista `iw phy`:

```
frecuencias de 5 GHz disponibles: 31
```

**Esa cuenta era insuficiente y dio una conclusión falsa.** Al mirar las banderas de cada frecuencia
en vez del total:

```
* 5180.0 MHz [36] (20.0 dBm) (no IR)
* 5200.0 MHz [40] (20.0 dBm) (no IR)
* 5220.0 MHz [44] (20.0 dBm) (no IR)
* 5240.0 MHz [48] (20.0 dBm) (no IR)
```

Las 31 estaban en `no IR` —*no Initiating Radiation*—, y 4 además `disabled`. **Canales utilizables:
cero.** Montar la red de 5 GHz confiando en el primer dato habría producido exactamente el fallo
mudo que se buscaba evitar.

La lección es de método y es la de siempre en este proyecto: **contar no es comprobar**. El dato que
decide no era cuántas frecuencias lista la tarjeta sino cuántas tiene habilitadas.

### 1.3 La causa, y estaba escrita en el arranque

```
[    6.860583] platform regulatory.0: Direct firmware load for regulatory.db failed with error -2
[    6.860610] cfg80211: failed to load regulatory.db
```

`/lib/firmware/regulatory.db` **no existía en ninguno de los dos vehículos**. Sin esa base el kernel
no tiene reglas de ningún país, cae al dominio mundial `00` y deja todo el 5 GHz en solo escucha.
Por eso `iw reg set CO` tampoco hacía nada: no había reglas que aplicar.

## 2. El arreglo, y su comprobación

Se copió la base desde el portátil a `/lib/firmware/` de cada vehículo. **`cfg80211` solo la lee al
arrancar**, así que recargar el módulo de la tarjeta no basta: hace falta reiniciar.

| | `amss-ez9n` | `amss-jgm9` |
|---|---|---|
| `regulatory.db` antes | ausente | ausente |
| Error en el arranque | sí | sí |
| **Canales de 5 GHz utilizables, antes** | **0 de 31** | **0 de 31** |
| **Canales de 5 GHz utilizables, después** | **13 de 31** | **13 de 31** |
| Canal 36 | `no IR` → **23 dBm** | `no IR` → **23 dBm** |
| Canales 40, 44, 48 | `no IR` → **23 dBm** | `no IR` → **23 dBm** |
| Persiste tras reiniciar | ✅ comprobado | ✅ comprobado |

Se instaló además `dominio-regulatorio.service` en los dos, porque `iw reg set` no sobrevive al
reinicio. El arreglo completo está en
[`herramientas/arreglar_regulatorio_wifi.sh`](../../herramientas/arreglar_regulatorio_wifi.sh), para
que no haya que redescubrirlo si se reinstala un vehículo.

### 2.1 Una salvedad sobre el dominio

La tarjeta (`mwifiex`) es **autogestionada**: `iw reg get` informa `country US` para el `phy#0`,
no `CO`, y manda el firmware. El servicio que fija `CO` queda de refuerzo del dominio global.

Para la banda baja de 5 GHz esto no cambia nada —es la menos restringida en todas partes y Colombia
sigue las reglas de la FCC en ella— pero **conviene no afirmar que el vehículo opera bajo dominio
colombiano**, porque no es lo que reporta.

### 2.2 Un paso que se hizo mal y salió bien

Al intentar que la base se leyera sin reiniciar se descargó el módulo `mwifiex_pcie` **estando
conectado por SSH sobre esa misma tarjeta**. El vehículo se quedó sin red hasta que
`NetworkManager` reasoció sola, unos segundos después.

Salió bien y pudo no salir. Queda anotado: **no se descarga el driver de la radio por la que se está
conectado.** Si hubiera hecho falta recuperar el vehículo, habría requerido acceso físico.

## 3. La medida: RF-15 sobre 5 GHz

Con los dos vehículos asociados al mismo punto de acceso en el canal 36, y el protocolo tal como lo
fija [`HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](../historial/HOJA_CAMPO_SEGUNDO_DEEPRACER.md) —600 mensajes, cotas
inscritas antes de medir—:

| | Septiembre, 2,4 GHz | **5 de octubre, 5 GHz** | |
|---|---|---|---|
| Enviados / recibidos | 600 / 600 | 600 / 600 | = |
| Pérdida | 0 % | 0 % | = |
| Mínimo | 4,74 ms | 4,54 ms | = |
| **Mediana** | 7,61 ms | **5,99 ms** | −21 % |
| **p95** | 20,76 ms | **11,12 ms** | **−46 %** |
| Máximo | 58,61 ms | 32,77 ms | −44 % |
| Veredicto | `CUMPLE` | **`CUMPLE`** | |

Registro: [`S26_RF15_5GHz_carroA_carroB.json`](registros/S26_RF15_5GHz_carroA_carroB.json).

**Lo que mejoró es la cola, no la mediana.** La mediana ya estaba sana. El p95 es lo que la
interferencia estropea, y es la fila que la hoja de campo señala como el modo de fallo a vigilar.

El enlace también cambió de categoría: de 802.11n a 40 MHz (121 / 300 Mbit/s) a **802.11ac a 80 MHz
con dos flujos (585 / 780 Mbit/s)**. El proyecto no necesita ese caudal —su tráfico son mensajes de
control y un barrido de LiDAR— pero sirve de indicador de la calidad del enlace.

> **Esta medida NO es la de la topología final.** Los dos vehículos estaban en el mismo punto de
> acceso y en la misma sala. En el montaje real van en pisos distintos, en puntos de acceso
> distintos, unidos por cable. **Hay que repetirla allá**, y es esa la que vale para el documento.
> Esta sirve de línea base y de prueba de que el 5 GHz funciona.

## 4. El entorno de radio, medido

Barrido desde el portátil en el sitio de trabajo:

| Banda | Redes | Zona libre |
|---|---|---|
| 2,4 GHz | **33** | ninguna |
| 5 GHz | 19 | **canales 36 a 48 casi vacíos** |

En 5 GHz bajo solo estaban los propios FiberHome y una red oculta débil; el tráfico ajeno se
concentra en los canales 108, 136 y 157.

### 4.1 Tres radios apiladas

Lo que veía el vehículo antes del cambio:

| Red | Equipo | Frecuencia | Señal |
|---|---|---|---|
| `DEEPRACER` | TP-Link | 2422 MHz · canal 3 | −27 dBm |
| `DEEPRACER PRO` | FiberHome #1 | 2432 MHz · canal 5 | −30 dBm |
| `DEEPRACER PRO` | FiberHome #2 | 2432 MHz · canal 5 | −30 dBm |

**Tres radios a 10 MHz entre sí, las tres a potencia de contacto**, y el TP-Link emitiendo en 40 MHz
de ancho, que en 2,4 GHz ocupa de hecho del canal 1 al 7.

Eso explica el síntoma inicial: **−27 dBm es señal excelente, así que el problema nunca fue
cobertura sino interferencia.** Estar cerca del equipo no ayuda cuando otras dos radios martillean el
mismo canal con la misma potencia.

### 4.2 El indicador verde del FiberHome

Jonny observó que el equipo conectado por LAN nunca pone su indicador en verde aunque haya internet.

**El LED sigue el puerto WAN.** Con el cable de subida en un puerto LAN, el WAN queda sin usar y el
LED no se enciende. **Es el comportamiento correcto para lo que el proyecto necesita**: así el
FiberHome trabaja como punto de acceso en puente. La prueba es que toma dirección del DHCP del
TP-Link y los clientes quedan en la misma subred.

El LED mide algo que aquí no se quiere.

## 5. Lo que queda abierto

1. **La topología final no está montada.** El plan está en
   [`TOPOLOGIA_RED.md`](../TOPOLOGIA_RED.md), con los pasos en orden.
2. **Falta repetir RF-15 en los pisos 3 y 4**, con cada vehículo en su planta y el cable entre
   ellas. Es la medida que vale.
3. **Los dos FiberHome están hoy en el mismo canal 36.** Hay que separarlos a 36 y 44, con ancho de
   40 MHz: con 80 MHz un canal en el 36 ocupa del 36 al 48 y se pisarían enteros.
4. **No se pudo verificar si `DEEPRACER PRO` es una red separada.** El intento de conexión desde el
   portátil se agotó. Se va a reiniciar ese equipo de todos modos, así que queda sin resolver y sin
   consecuencias.
5. **Los vehículos se movieron de IP**: las guías dicen `.100` y `.102`, hoy están en `.102` y
   `.104`. Lo arreglan las reservas por MAC del §6 de `TOPOLOGIA_RED.md`.
