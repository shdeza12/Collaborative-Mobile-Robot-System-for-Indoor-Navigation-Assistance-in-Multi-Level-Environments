# Topología de red para el sitio nuevo — cómo debe quedar

**Fecha:** 2026-10-05 · **revisado el 2026-10-07**
**Estado:** **montado a medias.** Los dos puntos de acceso están en puente sobre la misma subred y
cada vehículo cuelga de uno distinto, que es la forma correcta. Faltan los pasos 2 (canales), 3 y 5
(SSID por piso), 6 (reservas) y 7-8 (cable entre plantas y la medida que cierra). Los pasos siguen
en orden y son seguros: en ninguno se queda un vehículo sin acceso.

> **Al día 2026-10-07.** Lo medido en la sesión de hoy está en
> [`S26_bucle_capa2_y_red_dos_AP.md`](Evidencia/S26_bucle_capa2_y_red_dos_AP.md). Dos cosas:
>
> - **Se encontró y se resolvió un bucle de capa 2** que entregaba cada paquete hasta tres veces
>   (47 % de amplificación) y que el `ping` no delataba, porque informaba `0 % de pérdida`. Lo
>   causaba un FiberHome en **modo malla** enlazando por aire mientras estaba también cableado. **El
>   modo malla no se usa en este montaje**, justamente por eso.
> - **El enlace vehículo↔vehículo quedó en 3,75 ms de promedio con 0,51 ms de variación**, la mejor
>   cifra del proyecto. Las latencias malas que se veían antes eran del portátil, que mide su propio
>   salto en 2,4 GHz y no el de los vehículos.
>
> **Pendiente y no es de red:** `amss-ez9n` no forma grafo de ROS, ni consigo mismo. Se reinicia
> primero y se vuelve a mirar (§3.2 de esa evidencia).
**Evidencia que lo sostiene:**
[`S26_red_5ghz_regulatorio.md`](Evidencia/S26_red_5ghz_regulatorio.md)

---

## 0. La idea, en una frase

**Una sola red, un solo DHCP, un solo dominio de difusión** —que es lo que DDS necesita para
descubrir—, con **un punto de acceso por piso en 5 GHz** y los dos unidos **por cable**, no por aire.

Los SSID distintos por piso no son redes distintas: son dos radios de la misma red. Sirven para que
cada vehículo quede fijado a su planta sin ambigüedad, y eso es legítimo aquí porque **ningún robot
cambia de nivel**: cada uno tiene un punto de acceso de casa, fijo, para siempre.

## 1. Cómo debe quedar

```
                    ┌─────────────────────────────┐
                    │   TP-Link TL-WR940N         │
                    │   router + DHCP             │
                    │   192.168.0.1/24            │
                    │   SSID DEEPRACER            │
                    │   2,4 GHz ch6  ← RESPALDO   │
                    └──────────┬──────────────────┘
                               │
                 ┌─────────────┴─────────────┐
              cable LAN                  cable LAN
              (mismo piso)              (entre pisos)
                 │                           │
      ┌──────────┴──────────┐     ┌──────────┴──────────┐
      │  FiberHome  PISO 4  │     │  FiberHome  PISO 3  │
      │  puente, DHCP OFF   │     │  puente, DHCP OFF   │
      │  5 GHz · ch36 · 40M │     │  5 GHz · ch44 · 40M │
      │  SSID DEEPRACER_P4  │     │  SSID DEEPRACER_P3  │
      └──────────┬──────────┘     └──────────┬──────────┘
                 │                           │
            vehículo piso 4             vehículo piso 3
```

### Por qué el TP-Link se queda

Durante la sesión se planteó quitarlo, y el argumento era la interferencia: tres radios apiladas en
los canales 3 y 5. **Ese argumento se agotó al pasar los vehículos a 5 GHz.** El TP-Link emite en
2422 MHz y los vehículos trabajan en 5180 MHz: bandas distintas, no se tocan.

Lo que se gana conservándolo es una red de seguridad que no cuesta nada: **los vehículos mantienen
`DEEPRACER` guardada**, así que si un FiberHome falla vuelven solos al TP-Link sin que nadie
intervenga. Y cambiar el router a once días del corte C-3 obliga a rehacer reservas, revisar `ufw` y
volver a medir, sin ganar un milisegundo.

Queda por revisar después del 16 de octubre, con calma. El argumento que le sigue en contra es que
es el punto único de fallo, y eso se mitiga teniéndolo a mano, no cambiándolo ahora.

## 2. Datos

> **Nota del 6 de noviembre: así quedó el montaje final.** El FiberHome `AA` quedó en el piso 3 (canal 44; radio de 5 GHz
> `8C:5F:AD:37:AA:46`) y el `D2` en el piso 4 (canal 36; `8C:5F:AD:37:D2:16`), al revés de lo que asignan los pasos 1 a 4; las
> radios salen de las redes `DEEPRACER_P3-5G` y `DEEPRACER_P4-5G` guardadas en el portátil. El enrutador quedó en el piso 4 y el
> cable entre pisos va al punto de acceso del piso 3, como confirmaron los autores. El portátil usa la `192.168.0.105` en
> `DEEPRACER`, con la MAC `D8:80:83:5E:C1:D7`. La tabla completa está en la sección de la red del documento final.

| Vehículo | MAC de `mlan0` | IP que debe tener |
|---|---|---|
| `amss-ez9n` | `80:91:33:ed:8c:f3` | `192.168.0.102` |
| `amss-jgm9` | `80:91:33:f3:e6:ab` | `192.168.0.104` |

| Equipo | MAC base | Papel |
|---|---|---|
| TP-Link TL-WR940N | `60:32:B1:77:FB:CC` | router + DHCP + respaldo 2,4 GHz |
| FiberHome | `8C:5F:AD:37:AA:xx` | punto de acceso, un piso |
| FiberHome | `8C:5F:AD:37:D2:xx` | punto de acceso, el otro piso |

**La subred tiene que seguir siendo `192.168.0.0/24`.** No es estética: las reglas de `ufw` de los
vehículos están abiertas por rango (`sudo ufw allow from 192.168.0.0/24`). Si la subred cambia, el
cortafuegos bloquea DDS y deja la firma engañosa de *ping perfecto, grafo ROS vacío*.

## 3. Pasos, en este orden

### Paso 1 · Reiniciar el FiberHome `DEEPRACER PRO`

El `8C:5F:AD:37:D2:xx`. Su configuración es resto del montaje de malla que no funcionó, y
**probablemente tiene su propia red** —no se pudo verificar, el intento de conexión se agotó—.

Botón de reinicio, 10 s. Queda como `CLARO_WIFI…`. Ningún vehículo está en él, así que no rompe nada.

> El otro FiberHome ya se reinició el 5 de octubre y **levantó usable, sin quedarse esperando
> aprovisionamiento de Claro.** Ese era el riesgo y quedó descartado.

### Paso 2 · Ese equipo pasa a ser el punto de acceso del piso 3

Entrar a `192.168.10.1` con las credenciales de la etiqueta:

| Ajuste | Valor |
|---|---|
| Modo | **punto de acceso / puente** |
| DHCP | **apagado** |
| SSID 5 GHz | `DEEPRACER_P3` |
| Canal 5 GHz | **44**, fijo |
| Ancho | **40 MHz** |
| 2,4 GHz | apagada |
| Aislamiento de clientes | **apagado** |

Cable desde su puerto **LAN** a un puerto **LAN** del TP-Link. Nunca al WAN.

**Comprobar:** debe aparecer con una IP `192.168.0.x`. Si sale con otra subred, el DHCP no quedó
apagado.

> **El indicador verde no se va a encender, y está bien.** El LED sigue el puerto WAN, que en modo
> puente queda sin usar. Mide algo que aquí no se quiere.

### Paso 3 · Pasar el vehículo del piso 3 a su red

Añadirle `DEEPRACER_P3` **sin borrar `DEEPRACER`**, y comprobar con un reinicio que levanta solo.

### Paso 4 · El otro FiberHome, punto de acceso del piso 4

El `8C:5F:AD:37:AA:xx`, que ya está en puente y funcionando:

| Ajuste | Valor |
|---|---|
| SSID 5 GHz | `DEEPRACER_P4` |
| Canal 5 GHz | **36**, fijo |
| Ancho | **40 MHz** |
| 2,4 GHz | apagada |
| Aislamiento de clientes | **apagado** |
| DHCP | sigue apagado |

> Al cambiarle el SSID los vehículos se caen de la red actual. **No pasa nada:** tienen `DEEPRACER`
> guardada y vuelven solos al TP-Link.

### Paso 5 · Pasar el vehículo del piso 4

Igual que el paso 3, con `DEEPRACER_P4`.

### Paso 6 · Reservas de DHCP en el TP-Link

En `192.168.0.1`, fijar por MAC las dos direcciones de la tabla del §2.

Esto evita que los vehículos se muevan de IP —ya pasó: las guías dicen `.100` y `.102`, hoy están en
`.102` y `.104`— y mata la trampa del `deepracer.local` ambiguo con dos vehículos en la red.

De paso, mover su 2,4 GHz del canal 3 al **6**, que estaba menos cargado.

### Paso 7 · El cable entre pisos

Puerto **LAN** del FiberHome del piso 3 a un puerto **LAN** del TP-Link.

**Prueba:** desconectar ese cable. El punto de acceso del piso 3 debe quedarse sin red. Si sigue
funcionando, está enlazando por aire y hay que forzar el cableado.

### Paso 8 · Medir en el sitio real

Con cada vehículo en su piso, `medir_latencia_red.py` entre los dos. No se hizo, y por decisión de
los autores del 3 de noviembre no se repite: RF-15 queda con la medida del 5 de octubre, con los dos
en el mismo punto de acceso y en la misma sala, y con uno en cada piso quedan las medidas de
[`S26_red_campo_topologia_final.md`](Evidencia/S26_red_campo_topologia_final.md).

## 3.bis · Lo hecho el 2026-10-07, y lo que queda para el laboratorio

### Hecho sobre los vehículos

| Vehículo | Cambio |
|---|---|
| `amss-jgm9` (racey) | Borrado el perfil ajeno **`Nicolas Internet`**, que tenía autoconexión y podía llevarse el vehículo fuera de la red del proyecto en plena prueba |
| `amss-jgm9` | Prioridades: `DEEPRACER PRO-5G` 100 · `CLARO_WIFIA40` 50 · `DEEPRACER PRO` 10 |
| `amss-ez9n` (deepy) | Prioridad `CLARO_WIFIA40` 100 |
| `amss-ez9n` | **Corregido el SSID del respaldo**: el perfil decía `Deepracer` y el TP-Link emite `DEEPRACER`. Los SSID distinguen mayúsculas, así que ese respaldo no habría enganchado nunca. Tenía la contraseña guardada, así que bastó corregir el nombre |

Ninguno de los dos perdió la conexión al hacerlo.

**Ya estaba bien y no hubo que tocarlo:** el ahorro de energía de la WiFi está **apagado** en los
dos, y la ambigüedad de `deepracer.local` está resuelta porque los nombres de equipo son distintos.

### Lo que queda, para la sesión de laboratorio

**Del lado de los puntos de acceso:**

1. **Separar los canales: 36 y 44**, ancho 40 MHz. Hoy los dos están en el 36.
2. **Sacar los dos FiberHome de modo malla.** Los dos vuelven a anunciar `fhmesh_…`. Hoy no hay
   bucle —comprobado, 0 duplicados— porque anunciar no es emparejarse, pero es un riesgo latente: si
   llegan a enlazarse por aire estando los dos cableados, el bucle del 7-oct vuelve.
3. **SSID por piso** (`DEEPRACER_P3` / `DEEPRACER_P4`).
4. **Reservas de DHCP por MAC.** Hoy las direcciones se mantienen solo porque el TP-Link entrega
   concesiones infinitas (`dhcp_lease_time = 4294967295`), que es suerte, no diseño.
5. **Cable entre pisos**, con la prueba de desconectarlo.

**Del lado de los vehículos:**

6. **Reiniciar `amss-ez9n`** y volver a mirar `ros2 node list`. Sigue sin formar grafo ni consigo
   mismo (§3.2 de [`S26_bucle_capa2_y_red_dos_AP.md`](Evidencia/S26_bucle_capa2_y_red_dos_AP.md)).
7. **Crear el respaldo de `amss-jgm9`**, que no tiene ninguno hacia el TP-Link. Necesita que alguien
   escriba la contraseña.
8. **Rehacer las prioridades** cuando cambien los SSID del paso 3.

**Lo que cierra la tarea §2.4 del plan:**

9. **RF-15 con un vehículo en cada piso**, con el cable puesto. La medida de hoy —3,75 ms de
   promedio— se tomó con los dos en la misma planta. **No se repite, por decisión de los autores del
   3 de noviembre:** con uno en cada piso quedan las medidas de
   [`S26_red_campo_topologia_final.md`](Evidencia/S26_red_campo_topologia_final.md).

### Y una comprobación de seguridad que sigue pendiente

El aislamiento por particiones **está montado y activo en los dos vehículos**, con nombres distintos,
verificado el 7-oct leyendo el entorno del proceso de servos. Pero **el efecto nunca se ha probado
sobre los vehículos**: que una orden a uno no mueva al otro. Está en el §6 de
[`DISENO_AISLAMIENTO_DOS_CARROS.md`](DISENO_AISLAMIENTO_DOS_CARROS.md), puntos 2 y 3, pendiente desde
el 25 de septiembre.

**Es barata y conviene hacerla antes de encender los motores de los dos a la vez:** un vehículo con
las ruedas en el aire, una orden desde el otro, y mirar si se mueve.

## 4. Por qué 40 MHz y no 80

El enlace de prueba negoció **80 MHz**. Un canal de 80 MHz en el 36 ocupa **del 36 al 48 completo**,
así que el segundo punto de acceso en el 44 quedaría dentro del primero y se pisarían enteros.

Con 40 MHz, el 36 cubre 36-40 y el 44 cubre 44-48: separación limpia. No se pierde nada que importe
—40 MHz son unos 400 Mbit/s y el tráfico del proyecto son mensajes de control más un barrido de
LiDAR—. **Separación limpia vale más que caudal que no se va a usar.**

## 5. Por qué el orden es ese

**En ningún paso se queda un vehículo sin red**, porque `DEEPRACER` sigue guardada en los dos de
principio a fin. Si algo sale mal, el TP-Link los recupera solo.

Es la misma disciplina del resto del proyecto: no se sierra la rama donde uno está sentado, y el plan
B se deja montado antes de necesitarlo.
