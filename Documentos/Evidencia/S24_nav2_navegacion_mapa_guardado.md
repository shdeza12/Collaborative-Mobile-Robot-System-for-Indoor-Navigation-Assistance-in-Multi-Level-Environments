# Peldaños 6 y 7: Nav2 navega el vehículo sobre un mapa guardado

**Fecha:** 2026-09-24, noche (S24).
**Vehículo:** `amss-ez9n` — esa noche el DHCP le dio **192.168.0.102**. El otro carro
apagado con el interruptor todo el tiempo, por la regla de seguridad del §7 de S23.
**Sitio:** el tramo encajonado de piso 2, con las dos cajas que acotan los 6 m.
**Mapa:** `mapeo_235028/mapa.yaml` — el mismo que el repositorio guarda como
[`S24_mapa_pasillo6m_HARDWARE.pgm`](S24_mapa_pasillo6m_HARDWARE.pgm), construido la
noche anterior en la corrida C de [`S24_mapeo_6m_hardware.md`](S24_mapeo_6m_hardware.md).

**Qué cierra:** los peldaños **6 (mapas de costos)** y **7 (planificador y
controlador)** de la escalera de Nav2, los dos últimos, sobre hardware. La tabla del
§2.3 de [`MAPA_TRABAJO_RESTANTE.md`](../MAPA_TRABAJO_RESTANTE.md) los tenía en ❌.

---

## 1. El resultado

Navegación de una sola meta, con `map_server` + AMCL sobre el mapa guardado —**no**
SLAM en vivo— y `nav2_params_jazzy.yaml`:

| | |
|---|---|
| Salida (AMCL) | `x = 1,007   y = 0,021` |
| Meta pedida | `x = 5,50   y = 0,00` |
| Llegada (AMCL) | `x = 5,837   y = −0,237` |
| **Avance real** | **4,837 m** |
| Recorrido según `/odom` | 5,037 m |
| **Error de llegada** | **0,412 m** |
| Tolerancia (`xy_goal_tolerance`) | 0,25 m → **FUERA** |

![La navegación sobre el mapa guardado: salida, meta pedida y parada](S24_nav2_navegacion_mapa_guardado.png)

*Figura añadida el 2026-09-25, dibujada sobre el mapa en metros con las cifras de la tabla. La
franja verde es el tramo útil para el ancho del carro (x = 0,61 a 6,06), medido con
`zona_libre_mapa.py`; coincide con el «libre limpio de x = 0,5 a x = 6,0» del §3.*

**La navegación funciona; la precisión de llegada no.** Las dos mitades importan y se
reportan juntas.

### Lo que demuestra que fue navegación y no un empujón

Tres cosas del bag, y ninguna se puede obtener de una corrida en recta:

1. **El plan se consume.** Los 8 mensajes de `/plan` traen
   **59 → 57 → 47 → 35 → 19 → 8 → 6 → 7** poses. El vehículo va gastando su
   trayectoria conforme avanza.
2. **La dirección trabajó.** `angular.z` recorre **−1,303 a +1,320**. Una corrida en
   recta bajo `avanzar_y_detener.py` —que es lo que se había hecho hasta ahora— deja
   ese canal en cero y no dice nada del controlador.
3. **Las órdenes salieron del planificador.** 109 de 113 mensajes de `/cmd_vel` con
   `linear.x ≠ 0`, entre **0,40 y 0,50**, y solo 2 por debajo de 0,40.

Datos crudos en `~/tesis_evidencia/S24_nav2_real/nav2_real_01` (145,6 s; 1115
barridos, 852 `/odom`, 113 `/cmd_vel`, 8 `/plan`, 17 `/amcl_pose`).

---

## 2. El hallazgo: la banda muerta y la tolerancia de llegada son incompatibles

El error de 0,412 m no es ruido ni mala suerte, y el mecanismo cierra sin huecos:

1. El vehículo **no se mueve** con `linear.x` por debajo de **0,40 m/s**: el puente
   `cmdvel_to_servo` traduce a `throttle` 0,0000 exacto y nada lo reporta.
2. Por eso `nav2_hardware.launch.py` **sube** `min_approach_linear_velocity` de 0,05
   a **0,40** — sin ese ajuste el vehículo se detendría al entrar en la fase de
   aproximación.
3. Consecuencia: **el vehículo se aproxima a la meta a 0,40 m/s y no puede ir más
   despacio.** No tiene régimen de aproximación fina.
4. Con `xy_goal_tolerance: 0,25 m`, **sobrepasa la meta por construcción**.

**No se arregla afinando el controlador.** Las vías son otras dos, y las dos son
decisiones, no ajustes: bajar el umbral de arranque del vehículo —mecánico o de
calibración de servos—, o subir la tolerancia de llegada con justificación previa.

**Coherente con lo medido en simulación.** Los cuatro fallos de la campaña de OE4
fueron 0,295 · 0,284 · 0,311 · 0,347 m contra la misma tolerancia de 0,25
([`RESULTADOS_OE4_SIMULACION.md`](../RESULTADOS_OE4_SIMULACION.md)). Mismo orden de
magnitud y misma métrica; allí el vehículo se quedaba **corto** y aquí se **pasa**,
pero el criterio de 0,25 m queda cuestionado desde los dos lados.

---

## 3. Cinco defectos silenciosos en el camino del mapa guardado

Ninguno da error. Los cinco se manifiestan como «Nav2 no planifica», que es
indistinguible de media docena de causas distintas. Se dejan escritos porque el
camino de mapa guardado **no estaba recorrido** y quien lo repita se los encuentra.

| # | Defecto | Cómo se manifiesta | Corrección aplicada |
|---|---|---|---|
| 1 | `use_sim_time: True` en los bloques `amcl:` y `map_server:` de `nav2_params_jazzy.yaml` | sin `/clock` en el vehículo, los nodos esperan un tiempo que no llega | `-p use_sim_time:=false` al arrancarlos a mano |
| 2 | `yaml_filename: primer_piso_definitivo.yaml` | apunta al mapa de **simulación**, no al del pasillo | `-p yaml_filename:=<mapa real>` |
| 3 | `scan_topic: scan` en el bloque `amcl:` | el vehículo publica en `/rplidar_ros/scan`; AMCL no recibe un solo barrido y calla | `-p scan_topic:=/rplidar_ros/scan` |
| 4 | `nav2_params_jazzy.yaml` **no estaba en la tarjeta** | el launch caía a su valor por omisión, dentro de un paquete que no está instalado allí | `scp` del archivo a `~/tesis/` |
| 5 | **Los costmaps se configuran antes que `map_server`** | la capa estática queda vacía y el planificador falla con **`"Start occupied"`** en cualquier meta | arrancar y **activar** `map_server` **antes** de lanzar los servidores de Nav2 |

El **defecto 5 es el importante**, y es de orden de arranque, no de configuración. Con
él presente el planificador aborta siempre y el mensaje apunta al punto de partida,
no a la causa. La prueba de que se resolvió está en el log:

```
[global_costmap] StaticLayer: Resizing costmap to 447 X 108 at 0.050000 m/pix
```

Los tres primeros son vestigios: el propio comentario del YAML dice que el bloque de
AMCL «se conserva igual que en Humble para que la prueba de no divergencia pueda
comparar los dos archivos enteros», o sea que **nunca estuvo pensado para ejecutarse
en hardware**. Lo están ahora.

### Un método que conviene conservar

Antes de mandar una sola meta se probó el planificador **sin mover el vehículo**, con
la acción `/compute_path_to_pose`. Eso separa «el planificador no puede» de «el
controlador no mueve» sin arriesgar el carro, y es lo que permitió encontrar el
defecto 5 en minutos en vez de con el vehículo dando vueltas.

De la misma medida salió otra cosa que ahorra salidas: el mapa tiene **71,7 % de
celdas desconocidas**, y con `allow_unknown: false` **solo el 26,2 % es navegable**.
El corte por `y = 0` da espacio libre limpio **de x = 0,5 a x = 6,0**; una primera
meta a `x = 8,0` cayó en lo desconocido y abortó sin que nada dijera por qué. **Antes
de pedir una meta, conviene medir si está en zona libre del mapa.**

---

## 4. Lo que este documento NO establece

1. **No es una campaña.** Es **una** navegación. RF-27 pide N = 5–10.
2. **No hay esquina.** El mapa es un tramo recto; la trayectoria no obligó a un
   cambio de rumbo grande. Que `angular.z` llegara a ±1,3 demuestra que la dirección
   actúa, no que el vehículo resuelva una esquina.
3. **No prueba el pasillo abierto.** El tramo está **encajonado** con cajas en los dos
   extremos, que es la geometría que da información de avance a `rf2o`. Los pasillos
   abiertos siguen midiendo 5,1 % y 5,9 %.
4. **La capa de obstáculos del costmap global escucha `scan`**, no
   `/rplidar_ros/scan`. En esta corrida no importó —se navegó sobre mapa estático en
   un tramo despejado— pero **el vehículo no estaba viendo obstáculos nuevos**, y eso
   hay que arreglarlo antes de cualquier corrida con gente cerca.
5. **Hubo recuperaciones.** El árbol ejecutó al menos un ciclo de cancelación, limpieza
   de costmaps y espera antes de la trayectoria que sí se siguió; uno de esos servicios
   dio *timeout*. No se caracterizó.

---

## 5. Qué se abre

- **Arreglar el tópico de la capa de obstáculos** (punto 4 de arriba). Es una línea y
  es condición para navegar con personas en el entorno.
- **Decidir la tolerancia de llegada**, con el §2 delante y **antes** de correr la
  campaña de RF-27. Es decisión de directores, como la del criterio de 0,25 m.
- **Medir el umbral de arranque real** con `sostener_traccion.py --rampa`. Es el dato
  que cuantifica la banda muerta y hoy no existe en ningún documento.
- **Una esquina.** Nadie ha mapeado ninguna, y es lo que falta para que la navegación
  demostrada sea la del guiado real.

---

## 6. Añadido el 2026-09-25: lo que se hizo con esto

- **Los cinco defectos del §3 quedan resueltos en código**, no en la memoria de quien arranca, en
  [`nav2_mapa_guardado.sh`](../../herramientas/nav2_mapa_guardado.sh), que Jonny escribió el 25-sep
  con la misma secuencia de esta corrida.
- **Sobre el punto 4 del §4 hay una segunda lectura, y se deja escrita.** Ejecutando en el portátil
  la reescritura que hace `nav2_hardware.launch.py`, **los dos costmaps quedan escuchando
  `/rplidar_ros/scan`**; y la línea `Subscribed to Topics: scan` **imprime el nombre de la fuente de
  observación, no el tópico** —en la simulación el YAML dice `/scan` y el log dice `scan`—. Si los
  servidores de esta corrida se arrancaron por el launch, lo esperable es que el costmap sí
  escuchara el LiDAR del carro. Lo zanja `ros2 topic info /rplidar_ros/scan --verbose` en el
  vehículo, y la guía de campaña manda hacerlo antes de mover nada.
- **Los «5 m» que se dijeron al día siguiente no son una medida**: son la distancia entre las cajas
  y la impresión de que el carro llegó cerca. La corrida sigue sin verdad de terreno.
- Todo el procedimiento para repetir esto N veces y medirlo está en
  [`GUIA_CAMPANA_NAV2_HARDWARE.md`](../GUIA_CAMPANA_NAV2_HARDWARE.md).
