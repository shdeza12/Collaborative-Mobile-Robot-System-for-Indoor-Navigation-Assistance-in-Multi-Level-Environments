# RF-16 sobre hardware: el mismo código fuente compila y corre en Humble y en Jazzy

*2026-09-22. Los dos vehículos físicos y el portátil. Recogida de evidencia ya producida durante la
jornada de G-4.*

## 0. Qué faltaba, y por qué se recoge ahora

`REQUISITOS.md` llama a RF-16 **«el requisito de mayor riesgo del proyecto»**: la simulación corre
sobre **ROS 2 Humble** y las dos unidades de cómputo de los vehículos sobre **Jazzy**. Se verificó
el 2026-08-18 con la pregunta 4 del spike —`S19_spike_p4_humble_jazzy.md`— y aquella medida se tomó
**sin encender hardware**: fue análisis de definiciones, no una compilación.

El `MAPA_TRABAJO_RESTANTE.md` §2.1 lo registra sin ambigüedad: a RF-16 le falta *«compilar en Jazzy,
**nunca intentado**»*, y lo marca como uno de los dos requisitos **no bloqueados por nada**.

Hoy se intentó, dos veces, sobre los dos vehículos. Este documento recoge esa medida, que se produjo
como preparativo de la compuerta G-4 y se habría quedado sin registrar.

## 1. La prueba que podía fallar: ¿es «el mismo código fuente»?

Todo lo demás sobra si la fuente del carro no es la del repositorio. Es la única afirmación del
requisito que se puede falsear de un solo golpe, así que se comprueba primero y por hash, no por
inspección.

Se compararon **22 ficheros** —`.py`, `.msg`, `.action`, `package.xml`, `CMakeLists.txt`,
`setup.py`, `setup.cfg`— de `coordinacion` y `coordinacion_msgs` entre el repositorio y
`~/coordinacion_ws/src` de cada vehículo.

**Los 22 md5 coinciden en los tres sitios.** No hay un solo byte de diferencia, ni un parche de
compatibilidad, ni un `if ROS_DISTRO`. «Sin cambios» es literal.

## 2. Los tres destinos

| Destino | Distribución ROS 2 | Sistema | Python |
|---|---|---|---|
| Portátil (simulación) | **Humble** | Ubuntu 22.04.5 LTS | 3.10.12 |
| `amss-jgm9` (192.168.0.101) | **Jazzy** | Ubuntu 24.04.4 LTS | 3.12.3 |
| `amss-ez9n` (192.168.0.102) | **Jazzy** | Ubuntu 24.04.4 LTS | 3.12.3 |

No es solo un salto de distribución de ROS: son **dos versiones mayores de Python** y dos de Ubuntu.

## 3. La compilación en Jazzy

`colcon build --symlink-install` sobre `coordinacion` y `coordinacion_msgs`, en cada vehículo.

| Qué se mide | Por qué | `amss-jgm9` | `amss-ez9n` |
|---|---|---|---|
| Códigos de retorno de las tareas de colcon | Un `returncode` distinto de 0 es un fallo de construcción | **4 de 4 en `0`** | **4 de 4 en `0`** |
| Tamaño de `stderr.log` de cada paquete | «Sin errores» admite avisos; cero bytes no admite nada | **0 bytes** en los dos paquetes | **0 bytes** en los dos paquetes |
| Duración | Para saber qué cuesta rehacerlo en campo | ~168 s | ~162 s |

**Cero bytes de diagnóstico** es un resultado más fuerte que «compiló»: no hubo ni un aviso de
obsolescencia al pasar de Python 3.10 a 3.12, que era el riesgo concreto.

## 4. Las cinco baterías, en los tres destinos

Los bancos del proyecto son guiones sueltos que devuelven 0 o 1; no hay `pytest`. Se corrieron los
cinco en cada sitio.

| Banco | Portátil (Humble) | `amss-jgm9` (Jazzy) | `amss-ez9n` (Jazzy) |
|---|---|---|---|
| `prueba_agente.py` | **40 de 40** | 37 de 37, **1 omitida** | 37 de 37, **1 omitida** |
| `prueba_espera_confirmacion.py` | 18, 0 fallan | 18, 0 fallan | 18, 0 fallan |
| `prueba_planificador.py` | **930 planes** verificados | 930 planes | 930 planes |
| `prueba_registrador.py` | 41 | 41 | 41 |
| `prueba_round_trip.py` | pasa | pasa | pasa |

Los quince `SALIDA=0`.

## 5. La única cifra que no coincidía, y por qué no es un defecto

40 en el portátil frente a 37 + 1 omitida en los carros **no cuadra por uno, sino por tres**. Se
persiguió hasta el fondo antes de dar por buena ninguna de las dos cifras.

`prueba_agente.py:116-129` busca `Documentos/CONTRATO_INTERFACES.md` subiendo por el árbol de
directorios. Si lo encuentra, ejecuta **tres** comprobaciones sobre la tabla normativa: que haya una
sola fila para `EstadoRobot`, que declare `/<ns>/estado` y que declare 2 Hz. Si no lo encuentra,
llama a `omite(...)` **una vez**.

En el vehículo solo se copiaron los dos paquetes, no el repositorio, así que no hay `Documentos/`
por encima y el banco lo dice con todas las letras:

```
[OMI] La fila de EstadoRobot en CONTRATO_INTERFACES.md -- no hay Documentos/ por encima;
      se corre fuera del repositorio
```

**37 + 3 = 40.** La aritmética cierra exacta, y lo que no se ejecuta en el carro **verifica el
documento, no el código**: son las tres comprobaciones que impiden que la tabla del contrato y la
implementación se separen. No tienen sentido donde no hay contrato que leer, y su ausencia no dice
nada sobre la portabilidad.

Se anota porque una diferencia de cifras entre dos destinos es exactamente el sitio donde un lector
crítico buscará el truco, y la respuesta tiene que estar escrita antes de que la busque.

## 6. Qué cierra esto de RF-16, y qué no

El criterio de aceptación de RF-16 tiene dos mitades:

> «Compilar el coordinador **sin cambios en las dos distribuciones** y **completar una misión en cada
> mundo por separado**.»

**La primera mitad queda verificada sobre hardware real.** Y no solo compila: ese mismo binario
corrió esta tarde en los dos vehículos durante la compuerta G-4 —`coordinador` en uno, `agente` en
cada uno, publicando y emparejando entre máquinas—, así que lo probado no es que el paquete se
construya, sino que **el código ejecuta su función en Jazzy**.

Lo que esto mejora respecto del 2026-08-18 es la **calidad de la evidencia**, no el veredicto: la
medida de agosto comparaba definiciones sin encender hardware; esta compila, instala y ejecuta.

**La segunda mitad sigue abierta,** y depende de **G-3** (navegación de un vehículo), cuyo corte es
C-1, viernes 2 de octubre. Sin Nav2 corriendo a bordo no hay misión que completar. **RF-16 sigue en
🟡**, con mejor evidencia debajo.

**Lo que sigue sin sostenerse es RF-16b** —una misión con un robot simulado y otro físico a la vez—,
tachado desde el 2026-08-18: `nav2_msgs/NavigateToPose` tiene distinta definición en las dos
distribuciones, y lo portable es la fuente, no el grafo. Nada de lo medido hoy lo reabre.

## 7. De paso, dos apuntes del `MAPA_TRABAJO_RESTANTE.md` que quedan resueltos

- **§5.7, «espacios de nombres `/robot1` y `/robot2` sobre hardware, nunca ejercitados fuera de
  simulación»:** ejercitados hoy, y es justo lo que mide G-4
  ([`S24_compuerta_G4_dos_en_el_grafo.md`](S24_compuerta_G4_dos_en_el_grafo.md)).
- **§5.6, «`ros2 node list` entre máquinas»:** medido, con respuesta negativa. `ros2 node list`
  **no es utilizable** como instrumento en este montaje: devolvió 21, 15, 10, 0 y «un nodo habiendo
  tres» en corridas sucesivas del mismo día. Lo que sí es fiable es `ros2 topic info --verbose`, que
  nombra nodo y espacio de nombres de cada extremo. **La declaración escrita de R11 sigue
  pendiente**, pero ya tiene con qué escribirse.

## 8. Trazabilidad

| Afirmación | Fuente |
|---|---|
| RF-16 es «el requisito de mayor riesgo del proyecto» y se midió sin hardware | `REQUISITOS.md:148-151` |
| Enunciado y criterio de aceptación de RF-16 | `REQUISITOS.md:119` |
| A RF-16 le faltaba «compilar en Jazzy, nunca intentado» | `MAPA_TRABAJO_RESTANTE.md`, §2.1 |
| Los 22 ficheros de fuente son idénticos | `md5sum` sobre el repositorio y sobre `~/coordinacion_ws/src` de cada carro, hoy |
| Distribución, sistema y Python de cada destino | `printenv ROS_DISTRO`, `lsb_release -ds`, `python3 --version` en cada máquina |
| Compilación sin diagnóstico | `~/coordinacion_ws/log/latest_build/*/stderr.log` (0 bytes) y `events.log` (4 × `returncode: 0`) |
| El bloque del contrato aporta 3 comprobaciones o 1 omisión | `Robot/aws-deepracer/coordinacion/test/prueba_agente.py:116-129` |
| El proyecto no usa `pytest` | `PLAN_RF25.md:29-31` |
| RF-16b es imposible sin trabajo nuevo | `REQUISITOS.md:120`, fila tachada del 2026-08-18 |
| El código ejecuta su función en Jazzy, no solo compila | [`S24_compuerta_G4_dos_en_el_grafo.md`](S24_compuerta_G4_dos_en_el_grafo.md) |
