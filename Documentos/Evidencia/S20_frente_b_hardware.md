# Frente B — el vehículo real: sensado bajo la pila, odometría láser, mapa del laboratorio y teleoperación

**Semana 20 · 2026-08-28.** Jornada en el laboratorio con **un solo** vehículo: la tarjeta de
cómputo original del DeepRacer, Ubuntu Server 24.04 con ROS 2 Jazzy (`deepracer-custom-car`). El
riesgo **R11** —el segundo DeepRacer en intervención técnica— sigue vivo, así que todo lo que sigue
está deliberadamente acotado a lo que se responde con un vehículo.

El objetivo de la jornada era la mitad de hardware del criterio de cierre de S20: *«el mapa real
del laboratorio queda guardado y verificado con `herramientas/verificar_mapa.py`»*. **El mapa
quedó guardado; la verificación, como está escrita, no es aplicable al banco físico**, y la §5
explica por qué. Por el camino se cerró un pendiente de S19, se falsó una hipótesis propia y
apareció el primer control manual del vehículo desde ROS 2.

---

## 1. El LiDAR ya convive con la pila del vehículo

S19 dejó abierto un defecto de una sola línea: el lanzador de fábrica invoca un ejecutable
`rplidar_node` y lo que el paquete instala se llama `rplidar_composition`. Las dos salidas posibles
estaban planteadas desde el 21-ago —enlace simbólico, o editar el lanzador bajo
`/opt/aws/deepracer/`—.

Se eligió el **enlace simbólico**. El motivo no es comodidad: editar un archivo dentro de
`/opt/aws/deepracer/` lo deja expuesto a que cualquier actualización del paquete de AWS lo
sobrescriba sin avisar, y el fallo reaparecería semanas después sin relación aparente con nada que
hubiéramos tocado. El enlace vive fuera de ese árbol.

Con eso, **el LiDAR y la pila de control corren a la vez**, que es lo que S19 no había conseguido.
El hito 8 del camino crítico deja de tener este bloqueo.

## 2. Convivir cuesta un 6,6 % de frecuencia de barrido

Que dos cosas convivan no significa que convivan gratis. Medido sobre `/rplidar_ros/scan`:

| Condición | Frecuencia |
|---|---|
| LiDAR aislado (medido el 2026-08-21) | 6,80 Hz |
| LiDAR bajo la pila completa del vehículo | **6,35 Hz** |

Son **−6,6 %**. No invalida nada de lo medido después —la odometría láser de la §3 se tomó en esta
condición, no en la aislada—, pero es una cifra que hay que tener a mano cuando se compare el banco
físico con el simulado en S26: el sensor del carro no entrega lo mismo trabajando solo que
trabajando acompañado, y el simulado no tiene ese efecto.

Queda anotado, sin perseguir la causa. Perseguirla habría consumido la jornada y no bloquea nada.

## 3. Odometría láser: repite bien, y por eso mismo se le puede medir un error de escala

### 3.1 Qué se midió y contra qué

Se recorrió una recta del laboratorio de ida y vuelta tres veces, leyendo la transformada
`map → base_link`, y se contrastó contra **flexómetro**: la recta mide **3,000 m** reales. Esa
cifra es la referencia externa, y es lo único que convierte el ejercicio en una calibración en vez
de en una comprobación de consistencia interna.

### 3.2 Resultados

| Magnitud | Valor |
|---|---|
| Recta real (flexómetro) | **3,000 m** |
| Cinco estimaciones | 3,106 · 3,055 · 3,120 · 3,080 · 3,080 m |
| Media | **3,088 m** |
| Desviación típica | 0,025 m |
| Error contra el flexómetro | **+0,088 m = +2,9 %** |
| Deriva de cierre sobre ~18,4 m recorridos | 0,033 m = **0,18 %** |
| Ruido con el vehículo en reposo | 8–10 mm |

### 3.3 Por qué el error es sistemático y no ruido

La estimación **más baja de las cinco** (3,055 m) sigue estando a 2,2 desviaciones típicas por
encima de los 3,000 m. Ninguna de las cinco se acerca al valor real por debajo. Un error de ruido
repartiría las estimaciones a ambos lados; estas están todas del mismo lado.

### 3.4 Y por qué la deriva de cierre, que es excelente, no lo detecta

Este es el punto que conviene tener claro para la sustentación, porque es contraintuitivo: **una
deriva de cierre del 0,18 % parece decir que la odometría es muy buena, y no contradice un error de
escala del 2,9 %**.

Un error de escala multiplica la distancia estimada por un factor constante. Al ir, la sobreestima;
al volver, la sobreestima igual pero en sentido contrario. Las dos se **cancelan** al cerrar el
circuito. La deriva de cierre mide la consistencia del sistema consigo mismo, no su acuerdo con el
mundo.

De ahí la lección de método: **repetibilidad sin referencia externa no es calibración.** Sin el
flexómetro, estos datos habrían pasado por una validación exitosa de la odometría.

### 3.5 Dos causas candidatas, sin discriminar

1. **Error de escala del propio sensor o del estimador** —el LiDAR reporta distancias un 2,9 %
   largas, o el registro láser acumula esa proporción.
2. **Colocación del vehículo** en cada extremo de la recta: el punto que el flexómetro mide y el
   punto que la odometría toma como origen no tienen por qué coincidir, y un desfase de ~4,4 cm en
   cada extremo produce exactamente esta cifra.

La sospecha se inclina por la **segunda**, pero es una corazonada y no se declara resuelta.

**Prueba que discrimina, pendiente:** medir con flexómetro un tramo de pared del laboratorio y
compararlo contra el mismo tramo medido sobre el `.pgm` del mapa. Esa comparación **no involucra la
colocación del vehículo**, así que si el 2,9 % reaparece, la causa es el sensor; si desaparece, era
la colocación.

## 4. Una hipótesis propia, falsada

Los tópicos del vehículo se veían con los publicadores y suscriptores en `_NODE_NAME_UNKNOWN_`.
La hipótesis de trabajo fue que se debía al transporte de Fast DDS y que forzar
`FASTDDS_BUILTIN_TRANSPORTS=UDPv4` restauraría los nombres.

**No los restauró.** La hipótesis era falsa y se deja escrita como falsa.

Lo que sí produjo el episodio es una corrección de método más útil que la hipótesis: se había puesto
*«que se resuelvan los nombres de nodo»* como criterio de paso, y **es un mal criterio**. Es un
indicador elegido por conveniencia, no la magnitud que importa. Lo que importa es si los datos
cruzan en cada sentido, y eso se comprueba por separado: el sentido vehículo→portátil con la
llegada de mensajes, y el sentido portátil→vehículo **solo** con las ruedas moviéndose.

## 5. El mapa del laboratorio, y por qué `verificar_mapa.py` no lo puede verificar

### 5.1 El artefacto

`mapas/mapa_laboratorio.pgm` + `.yaml`, generado con `map_saver_cli` sobre el vehículo y copiado al
portátil. Medido sobre la imagen:

| Magnitud | Valor |
|---|---|
| Rejilla | 247 × 311 = 76 817 celdas, 0,05 m/celda |
| Extensión de la rejilla | 12,35 × 15,55 m |
| Extensión del **contenido** | **8,45 × 6,90 m** |
| Ocupado (valor 0) | 538 celdas — 0,70 % |
| Libre (valor 254) | 11 035 celdas — 14,37 % — **27,6 m²** |
| Desconocido (valor 205) | 65 244 celdas — 84,93 % |
| Frontera libre↔desconocido | 1 655 celdas = **15,00 %** del espacio libre |

Los umbrales del `.yaml` son coherentes con la imagen: el valor 205 normalizado da 0,196078 contra
un `free_thresh` de 0,196, una diferencia de 0,00008.

### 5.2 La herramienta pide un `.world`, y un laboratorio real no tiene

`herramientas/verificar_mapa.py` toma `<mapa.yaml> <mundo.world> [altura]`. Su prueba principal
—fidelidad— compara cada obstáculo mapeado contra las paredes extraídas del `.world`. **Un
laboratorio físico no tiene `.world`**, así que la prueba principal no tiene contra qué correr.

Se ejecutó **a mano únicamente la mitad de la herramienta que no depende del mundo** (las cifras de
la tabla anterior). No se forzó el resto.

### 5.3 El umbral de frontera tampoco es el adecuado aquí

La herramienta exige frontera ≤ 1 %. Este mapa da **15,00 %**, y eso **no** significa que el mapa
esté mal: significa que se está aplicando la regla equivocada.

Ese 1 % está calibrado sobre los mundos simulados, cuyos vanos se sellaron a propósito con paneles
sintéticos (24-ago) precisamente para que el espacio libre quede cerrado. El laboratorio real es una
sala abierta con huecos, puertas y muebles: su frontera es **abierta por construcción**, no por
mapeo incompleto. Las 1 655 celdas de frontera se reparten en 782 sitios distintos, que es la firma
de un recinto abierto y no la de un mapa al que le falta una zona.

### 5.4 Conclusión sobre el criterio de S20

El criterio de cierre dice *«guardado y verificado con `herramientas/verificar_mapa.py`»*. **La
primera mitad está cumplida; la segunda no es aplicable al banco físico tal como está redactada.**
No se declara cumplida por analogía ni se ajustan los umbrales para que pase: eso convertiría la
verificación en un trámite. Lo que corresponde es reescribir el criterio para el banco físico, y esa
es una decisión de protocolo, no de código.

## 6. Teleoperación desde ROS 2, puenteando la cadena rota

### 6.1 Por qué no se usó `/cmd_vel`

La cadena `/cmd_vel → cmdvel_to_servo → servo` tiene **dos defectos independientes** ya
documentados: `servo_pkg` escucha en `/ctrl_pkg/servo_msg` mientras nuestro lanzador publica en
`/cmdvel_to_servo_pkg/servo_msg`, y la conversión de tracción tiene sus tres ramas en orden tal que
la primera se traga todas las demás.

Arreglar los dos era el camino largo. Para **teleoperar** basta publicar `ServoCtrlMsg` directamente
en `/ctrl_pkg/servo_msg`, que es donde el vehículo realmente escucha.

### 6.2 Resultado

**Funcionó.** El vehículo se conduce con el teclado: `w`/`s` tracción, `a`/`d` dirección, `x`
centrar, espacio parar, `q` salir. Es el **primer control del vehículo desde ROS 2** sin la interfaz
web, y cierra por la vía del puente el pendiente de OE2 *«control desde ROS 2 en vez de la web»*.

### 6.3 Dos decisiones de seguridad, y no son adorno

- **Hombre muerto:** sin tecla durante 0,6 s, la tracción se pone a cero. Al salir, el programa
  restaura la terminal y publica diez mensajes en cero.
- **Se ejecuta *en* el vehículo, nunca desde el portátil.** Si se corriera por red y el wifi cayera,
  `servo_pkg` se quedaría con el último valor recibido: un vehículo acelerando sin nadie al mando.

### 6.4 El fallo que no era software

A mitad de sesión el teleoperador *«dejó de leer»*. Se plantearon tres candidatas —desemparejamiento
DDS, bloqueo de escritura por SSH, estado de la terminal— y se preparó una versión instrumentada.

**Las tres eran falsas: se estaban descargando las baterías.** Queda anotado como patrón, porque es
de los que más tiempo hacen perder: *un fallo de alimentación se manifiesta como software que se
degrada progresivamente*, y todos los candidatos de software parecen plausibles mientras dura.

## 7. Segunda reproducción del `active` que miente

Durante la jornada, `deepracer-core` **se reinició solo**. `systemctl` seguía informando
`active (running)` y nada en la salida lo delataba: se detectó porque los **GID de los publicadores
cambiaron** entre dos consultas al mismo tópico.

Es la **segunda** vez que se observa el mismo patrón. Se registra como tal: un servicio que informa
`active` no es prueba de que el proceso que había siga vivo, y en este vehículo hay que verificarlo
por los identificadores del grafo, no por `systemctl`.

## 8. Lo que queda abierto

1. **La prueba que discrimina el error de escala** (§3.5): flexómetro contra `.pgm`.
2. **El criterio de S20 para el banco físico** (§5.4): decisión de protocolo.
3. **`coordinacion_msgs` sin compilar** en la tarjeta Jazzy.
4. **Las dos cámaras** siguen enumerando en USB sin comprobar que publiquen en ROS.
5. **El segundo vehículo** (R11), del que depende la pregunta 3 del spike de S19.
6. Los cinco bags de la jornada (~15 MB) están **fuera del repositorio**, en el portátil. Son
   irrepetibles sin vehículo, baterías y laboratorio: falta decidir dónde se respaldan.
