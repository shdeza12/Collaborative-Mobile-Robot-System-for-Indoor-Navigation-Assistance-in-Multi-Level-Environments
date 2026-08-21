# Plan de la semana 19 — jueves 20 y viernes 21 de agosto de 2026

Se escribe el 2026-08-19 por la noche. Existe porque los dos primeros días de la semana se
trabajaron sin plan escrito, y sin plan no hay forma de saber si un día se desvió: solo queda la
sensación de haber estado ocupado.

Manda el [cronograma S17–S32](CRONOGRAMA_S17_S32.md) §S19. Este documento no lo reinterpreta: lo
reparte entre los dos días que quedan.

---

## 1. Dónde estamos contra el criterio de cierre de S19

El cronograma fija cuatro condiciones. Al terminar el miércoles:

| # | Condición de cierre | Estado |
|---|---|---|
| 1 | Informe del spike con las **preguntas 1, 2 y 4** respondidas y su impacto en el plan | ✅ [`Evidencia/S19_spike_p4_humble_jazzy.md`](Evidencia/S19_spike_p4_humble_jazzy.md) + [`Evidencia/S19_spike_p1_p2_hardware.md`](Evidencia/S19_spike_p1_p2_hardware.md) |
| 2 | **Matriz de requisitos** publicada | 🔴 Sin empezar |
| 3 | **Protocolo experimental de OE4**, escrito antes de instrumentar nada | 🔴 Sin empezar |
| 4 | Los **dos agentes navegando simultáneamente**, cada uno en su nivel | 🔴 Sin empezar |

Queda **una de cuatro** hecha y quedan **dos días**. La pregunta 3 del spike sigue fuera del criterio
por depender de **R11**, y eso no ha cambiado.

**Por qué se desvió el miércoles.** El día se fue entero en el frente B. Parte fue inevitable —hubo
que abrir un cortafuegos para que las dos máquinas se vieran— y parte fue decisión mía: adelanté la
comprobación en hardware de la pregunta 4, que el cronograma marca explícitamente como *«ninguno, no
necesita hardware encendido»*. Con el vehículo prendido, el recurso escaso era el vehículo. Queda
anotado para no repetirlo.

---

## 2. Jueves 20 — los dos entregables de mesa

Ninguno necesita hardware ni simulación. Van primero por eso: no dependen de que nada arranque.

### 2.1 Matriz de requisitos RF ↔ OE ↔ prueba *(bloque principal)*

Cierra el riesgo **R5** y desbloquea **OE1**, que está en 55 % y no sube porque falta este artefacto.
La materia prima ya existe: [`REQUISITOS.md`](REQUISITOS.md) tiene los 34 requisitos con su fuente y
su prueba. Lo que falta es la **traza**: qué objetivo específico sostiene cada requisito y con qué
evidencia concreta se da por verificado.

Sirve para §7.4 del anteproyecto —*«comparación con requisitos: validar que cada especificación
inicial se cumpla»*—, que es una sección que hay que escribir sí o sí para sustentar.

**Criterio de cierre:** cada uno de los 34 requisitos con su OE y su prueba, y **ningún OE sin al
menos un requisito**. Si aparece un OE huérfano, es un hueco de especificación, no un error de
tabla.

### 2.2 Protocolo experimental de OE4

**OE4 está en 0 % y es el objetivo que sustenta la evaluación del proyecto.** Sin protocolo no hay
campaña, y sin campaña no hay resultados que defender.

Se escribe **antes** de instrumentar nada, y eso es deliberado: un protocolo redactado después de
ver los datos se acomoda a lo que salió. Tiene que fijar qué se mide (tiempo de respuesta, tiempo de
asignación, tasa de éxito, continuidad entre niveles), cómo, cuántas repeticiones, con qué criterio
de éxito y qué se hace con una corrida fallida.

**Depende de un dato que no existe:** `puntos_interes.yaml` no tiene contenido definido, y de ahí
salen los orígenes y destinos de las 30 repeticiones. Hay un borrador sin versionar en
`Robot/aws-deepracer/deepracer_bringup/config/`. Definirlo es parte de esta tarea, no un requisito
previo.

**Criterio de cierre:** el protocolo permite que otra persona repita la campaña sin preguntarnos
nada.

### 2.3 Si sobra la tarde — cerrar RF-14 de verdad

Compilar `cmdvel_to_servo_pkg` **en el vehículo**, contra su propio `deepracer_interfaces_pkg`, con
la salida remapeada a `/ctrl_pkg/servo_msg`, y teleoperar con `teleop_twist_keyboard` en local.

Es opcional y va al final a propósito: es lo único de la lista que puede romper el vehículo, y es lo
único que no forma parte del criterio de cierre.

**Con el vehículo en alto.** La tracción es binaria: `teleop_twist_keyboard` sale en 0,5 m/s, por
encima del umbral de 0,4, y eso da tracción 0,7341 directa. Con las ruedas en el suelo, arranca a
fondo.

---

## 3. Viernes 21 — la condición de cierre que queda, y el corte

### 3.1 `robot1` en el nivel 1 y `robot2` en el nivel 2, a la vez

Único resto del frente A. Por separado ya está demostrado en S18; falta simultáneo. Es la cuarta
condición de cierre y no debería dar sorpresas, pero se hace el viernes por la mañana y no por la
tarde: si aparece un defecto, hay margen.

### 3.2 Corte semanal *(viernes por la noche)*

- Actualizar [`ESTADO.md`](../ESTADO.md): avance de **OE2** —por primera vez con sensado y control
  físicos medidos, no declarados—, R8 con su comprobación en hardware, y la bitácora.
- Emitir el entregable de S19.
- Commit. Está pendiente de versionar: `herramientas/verificar_lidar.py`,
  `Robot/aws-deepracer/deepracer_bringup/config/puntos_interes.yaml`, el `.xlsx` del cronograma y los
  dos documentos de hoy.
- **Hay 8 commits sin subir y `main` no tiene upstream.** Avisar a Jonny antes de empujar: la rama
  es compartida.

---

## 4. Lo que este plan no resuelve, y hay que mirar de frente

Faltan **13 semanas** de 32 y el reparto de avance es desigual:

| Objetivo | Avance | Semana en que se construye |
|---|---|---|
| OE1 | 55 % | S20 (nodo de coordinación) |
| OE2 | 40 % | S19–S21 |
| **OE3** — interfaz HRI web | **0 %** | Sin semana asignada con nombre propio |
| **OE4** — evaluación con métricas | **0 %** | Protocolo S19, instrumentación S20–S21, campaña S22+ |

**OE3 en 0 % a trece semanas del final es el punto que más debe preocupar**, porque es un objetivo
del anteproyecto y no está asignado a ninguna semana concreta del cronograma. No se resuelve en este
plan; se registra aquí para que no se descubra en S28.

**Y queda un bloqueador de hardware vivo:** el driver del YDLidar para Jazzy. S20 pide *«mapear el
laboratorio real con el DeepRacer físico»* y hoy conectar el LiDAR al vehículo lo deja sin pila de
control (§4.1 del informe del spike). Si no se resuelve, S20 pierde su mitad de hardware.

**Y sigue faltando la declaración escrita de Jonny** sobre qué vehículo está intervenido, qué se le
hizo y cuándo vuelve (**R11**). Sin eso, la pregunta 3 del spike y la paridad entre vehículos no
tienen fecha, solo intención.
