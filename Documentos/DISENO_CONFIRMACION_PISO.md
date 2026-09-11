# Diseño — Confirmación del usuario en la transición entre pisos

**Autor:** Santiago Hernández Ávila
**Fecha:** 2026-09-10 (S22 de 32)
**Origen:** reunión con el director Armando. De las cinco situaciones de usuario que
planteó, esta es la tercera: *«que el usuario indique al segundo robot de la misión que
ya se encuentra arriba, para darle continuidad a la asistencia»*.
**Estado:** diseño aprobado por el autor el 2026-09-10. Implementación pendiente.

---

## 1. El problema

Hoy una misión entre pisos no le pregunta nada al usuario. El planificador produce cuatro
tramos (`planificador.py:226-240`):

| # | robot | destino | etapa publicada |
|---|---|---|---|
| 1 | robot1 | origen que pidió el usuario | `TRAMO_1` |
| 2 | robot1 | `piso1_escalera` | `TRAMO_1` |
| 3 | **robot2** | `piso2_escalera` | `TRANSFERENCIA` |
| 4 | robot2 | destino final | `TRAMO_2` |

El coordinador los recorre en un `for` secuencial (`coordinador.py:233-257`) y pasa del
tramo 3 al tramo 4 **en cuanto Nav2 confirma que robot2 llegó a su escalera**. El usuario
no ha dicho que haya subido. Si va despacio, robot2 arranca el guiado sin él y la misión
se completa con el usuario todavía en el piso 1: el sistema registra un éxito que no
ocurrió.

Hay que notar qué robot espera. **El tramo 3 ya es de robot2**: mientras el usuario sube,
robot2 conduce hasta `piso2_escalera`. Robot1 termina su trabajo al final del tramo 2 y
deja de publicarse como robot activo. Así que la espera no retiene a robot1 — retiene a
robot2, parado en la escalera del piso de destino.

## 2. Decisiones

| # | Decisión | Razón |
|---|---|---|
| D-C1 | La confirmación es **obligatoria**, en simulación y en físico, por un solo camino de código | RF-16 / decisión D6: *«el mismo código fuente se despliega en los dos destinos»*. Un parámetro booleano que saltara la rama dejaría el banco de simulación midiendo un sistema distinto del que se entrega |
| D-C2 | La espera va **entre el tramo 3 y el tramo 4**, no como un tramo nuevo del planificador | El planificador no cambia, el array `plan` del registro no cambia, y la espera no es navegación: meterla como `Tramo` obligaría a que `_navegar` aprendiera a no navegar |
| D-C3 | Estado nuevo `ESPERANDO_CONFIRMACION = 7`, al final de `EstadoMision.msg` | Mismo procedimiento que `RECIBIDA = 6` el 2026-08-29, y por la razón que ese archivo ya documenta (líneas 25-28): las constantes **no viajan por el cable**, así que el formato de serialización no cambia y un suscriptor ya compilado sigue deserializando |
| D-C4 | La marca de etapa 7 publica `robot_activo = robot2` (nunca vacío) | Es la condición que preserva `continuidad` (RF-24). Ver §5 |
| D-C5 | Canal: tópico `/coordinacion/confirmacion_piso`, tipo `std_msgs/String`, contenido = `mision_id` | **Tópico y no servicio porque `ros2 bag` no graba servicios** — la misma lección ya escrita en `EstadoMision.msg:49-51`. Con tópico, el instante en que el usuario confirmó queda en el bag y es evidencia. `std_msgs/String` y no un mensaje propio para no tocar `coordinacion_msgs` a una semana del congelamiento de código (S23) |
| D-C6 | La HRI sigue hablando **solo** con `/coordinacion` | RF-19. El tópico vive bajo ese espacio de nombres |
| D-C7 | Alerta a los **60 s**, plazo máximo **120 s**, contados **desde que robot2 llega a `piso2_escalera`**, con **reloj de pared** | Decisión del autor. Se cuenta desde la llegada de robot2 y no desde el inicio de la transferencia para que un robot2 lento no le consuma tiempo al usuario. Reloj de pared y no `/clock`: ver §4 |
| D-C8 | La alerta es un **cambio de `mensaje_usuario`** dentro de la misma etapa 7, no un canal nuevo | El coordinador es el único sitio donde se redacta presentación (`EstadoMision.msg:40-42`). Y deja una segunda marca en el bag, que es la prueba de que la alerta salió |
| D-C9 | Al agotarse los 120 s: `FALLIDA` con motivo `«el usuario no confirmó la llegada al piso N»` | Reutiliza el camino de fallo que ya existe (`coordinador.py:249-257`), así que el registro y el veredicto se comportan igual que ante cualquier otro fallo |
| D-C10 | La confirmación se **engancha**: se retiene la última cuyo `mision_id` coincide con la misión en curso, y se limpia al arrancar cada misión | Sin esto, un usuario que sube rápido y confirma *antes* de que robot2 llegue pulsa contra nadie y se queda 120 s esperando un plazo que ya cumplió. Limpiar al arrancar impide que una pulsación vieja auto-confirme la misión siguiente |
| D-C11 | El bucle de espera también consulta `goal_handle.is_cancel_requested` | Es inerte hoy (ver §3) pero queda correcto sin trabajo extra cuando se arregle la cancelación |

**Fuera de alcance de este diseño**, aunque el punto 9 es su punto de enganche natural: el
*homing* (que el robot vuelva a su punto inicial tras un fallo o una cancelación) y las
otras cuatro situaciones que planteó el director.

## 3. Hallazgo colateral: la cancelación no funciona

Al verificar cómo está construido el `ActionServer` apareció un defecto que no es de este
punto pero que conviene dejar escrito. `coordinador.py:128-130` crea el servidor con
`execute_callback` y `callback_group` y nada más. Los tres defaults de rclpy
(`/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/action/server.py:166-178`) son:

| Callback omitido | Default | Efecto aquí |
|---|---|---|
| `goal_callback` | `GoalResponse.ACCEPT` | nada rechaza una segunda misión simultánea |
| `handle_accepted_callback` | `goal_handle.execute()` | se ejecuta de inmediato, sin cola |
| `cancel_callback` | **`CancelResponse.REJECT`** | el servidor rechaza toda cancelación |

Por el tercero, `goal_handle.is_cancel_requested` **nunca llega a ser verdadero** y el
chequeo de `coordinador.py:234` es código muerto: el botón de la interfaz envía el cancel,
rosbridge lo transmite, rclpy lo rechaza en silencio y la HRI se queda con *«Enviando la
cancelacion...»* congelado (`app.js:155`). Hoy **no cancela nada, nunca**. Se arregla en el
punto 1 del director, registrando un `cancel_callback` que devuelva `ACCEPT` y propagando
la cancelación al goal de Nav2 en curso.

Y por los dos primeros: **el sistema es de una misión a la vez por suposición, no por
candado**. Con `ReentrantCallbackGroup` (`coordinador.py:98`) y `MultiThreadedExecutor`
(`coordinador.py:568`), dos misiones correrían en hilos paralelos sobre un solo
`self.estado` y un solo `self.registro`; la segunda pisaría el registro de la primera
(`coordinador.py:201`), y la que terminara primero pondría `self.registro = None`, de modo
que el `cerrar()` de la otra se saltaría por el guard de la línea 283 y ese registro no se
escribiría nunca. El guardián `_ya_hay_coordinador` impide un segundo *coordinador*, no una
segunda *misión*. No se corrige en este diseño; queda anotado.

## 4. Comportamiento

```
tramo 3 (TRANSFERENCIA): robot2 -> piso2_escalera
   Nav2 confirma llegada
   |
   +-- ¿hay confirmación enganchada para esta mision_id?  (D-C10)
   |      sí -> se consume y se sigue al tramo 4
   |      no -> entra a esperar, t0 = ahora
   |
   marca etapa 7, robot2, piso2_escalera
   "¿Ya está en el piso 2? Confírmelo para continuar."
   |
   bucle a 20 Hz:
     llega confirmación con mision_id correcto  -> sale, sigue al tramo 4
     cancelación pedida                         -> sale, CANCELADA   (inerte hoy, §3)
     t - t0 >= 60 s, una sola vez               -> marca etapa 7 otra vez,
                                                   "Seguimos esperando su confirmación.
                                                    Quedan 60 segundos."
     t - t0 >= 120 s                            -> marca FALLIDA, abort,
                                                   motivo = "el usuario no confirmó
                                                   la llegada al piso 2"
   |
tramo 4 (TRAMO_2): robot2 -> destino final
```

**El plazo se mide con `time.time()`, reloj de pared, y no con `_ahora()`.** Esta decisión
se corrigió el 2026-09-10 después de escribir la primera versión de este documento, y la
razón está en el docstring de `_esperar` (`coordinador.py:486-491`), que ya distingue los
dos usos del tiempo en este nodo:

- **La persona que sube las escaleras vive en tiempo de pared.** Con RTF 0,5 darle 120 s de
  tiempo de simulación serían 240 s reales de espera. El plazo es de paciencia humana, no
  de dinámica simulada, y no debe depender de a qué velocidad corra Gazebo.
- **Si Gazebo muere durante la espera, `/clock` se detiene** y un plazo medido en tiempo de
  simulación no vencería nunca: el coordinador se quedaría colgado justo en el caso para el
  que existe el plazo. Es el mismo fallo que ese docstring ya advierte.

Las **marcas** que van al bag siguen sellándose con `_ahora()`, como todas las demás, porque
sí son marcas de métrica. Consecuencia al verificar: la separación en tiempo de simulación
entre las dos marcas de etapa 7 vale `60 s × RTF`, no 60 s. Con el RTF que mide
`herramientas/medir_rtf.py` en cada corrida, eso se comprueba sin ambigüedad.

## 5. Lo que no se rompe, y dónde se verificó

| Riesgo | Verificado en | Resultado |
|---|---|---|
| `continuidad` (RF-24), medida en vivo | `registrador.py:195-199` | pasa: exige `etapa_num != 0` y `robot` no vacío; 7 ≠ 0 y la marca lleva robot2 (D-C4) |
| `continuidad`, recompuesta del bag | `componer_registro.py:327-329` | pasa: la ventana va de `TRAMO_1` con agente a `COMPLETADA` y rechaza solo `INACTIVA` y robot vacío |
| `hueco_relevo_s` | `registrador.py:185` | intacto: mide `primer movimiento de robot2 − t(TRANSFERENCIA)`, es decir el **inicio** de la transferencia, antes de que exista la espera |
| Clasificación A/B de la misión | `componer_registro.py:403-405` | intacta: depende de que aparezcan `TRANSFERENCIA` o `TRAMO_2` |
| Corte de misiones dentro de un bag | `componer_registro.py:441` | intacto: `TERMINALES = (COMPLETADA, FALLIDA)`; 7 no es terminal |
| Validación del registro contra el esquema | `esquema_registro_mision.json:88-97` | pasa, y por una razón más fuerte de lo que parece: el único `etapa` del esquema está dentro del array `plan`, y ese array lo produce el planificador, que no cambia (D-C2). La etapa 7 no llega a aparecer ahí. De todas formas el campo es `{"type": "integer"}`, sin enumeración |
| El `marcas` del esquema no es el `marcas` del registro en vivo | `esquema_registro_mision.json`, propiedad `marcas` | **cuidado al verificar**, no es un riesgo del cambio: el esquema describe el registro **compuesto** del bag, cuyo `marcas` es un objeto con los siete instantes de la §3.5 y `additionalProperties: false`. El `marcas` que escribe `registrador.py` es una **lista** de cambios de etapa. El recuento de marcas de etapa 7 se comprueba en el registro **en vivo**; la validación contra el esquema, solo en el **compuesto** |
| Suscriptores ya compilados de `EstadoMision` | `EstadoMision.msg:25-28` | pasan: las constantes no son campos, la serialización no cambia |

**La campaña de 30 misiones NO se reejecuta por este cambio.** RF-28 es funcionalidad
*añadida*: no modifica el planificador (D-C2), ni las fórmulas de las cuatro métricas de OE4,
ni la serialización de `EstadoMision`, ni ninguna de las siete marcas de la §3.5. La tabla de
arriba es el argumento, fila por fila y con el archivo y la línea donde se comprobó. Las
misiones ya grabadas siguen siendo medidas válidas de lo que medían: una misión de clase B sin
etapa 7 es el mismo relevo de antes.

Lo que sí necesita evidencia propia es **el comportamiento nuevo**, y se obtiene con el piloto
de la tarea 7 del plan: una misión entre pisos confirmada por el usuario y otra dejada vencer.
Eso es una corrida añadida al expediente, no una repetición de la campaña. La campaña de S24
conserva su sitio en el cronograma como lo que ya era (§6 de `TALLER2_TRANSICION.md`), sin que
RF-28 le agregue trabajo.

## 6. Qué hay que tocar

| Archivo | Cambio |
|---|---|
| `coordinacion_msgs/msg/EstadoMision.msg` | constante `uint8 ESPERANDO_CONFIRMACION=7` y su nota de por qué |
| `coordinacion/coordinacion/planificador.py` | la misma constante, que este archivo duplica a propósito (líneas 57-59) para no depender de `coordinacion_msgs`. El caso 9 de `prueba_planificador.py` compara los dos sitios y revienta si se desincronizan |
| `coordinacion/coordinacion/registrador.py` | la entrada `7: "ESPERANDO_CONFIRMACION"` en el diccionario `ETAPAS` (líneas 72-73). Sin ella, `marca()` cae en su `ETAPAS.get(etapa, str(etapa))` y el registro escribiría `"etapa": "7"`, un número donde el esquema espera un nombre |
| `coordinacion/coordinacion/espera_confirmacion.py` | **archivo nuevo**, sin ROS: la política de plazos y el enganche por `mision_id`, que es la lógica que se puede probar sin simulador |
| `coordinacion/coordinacion/coordinador.py` | suscripción al tópico; uso del enganche; el bucle de espera tras cada tramo `TRANSFERENCIA` |
| `interfaz_web/js/rosbridge.js` | método para **publicar** un tópico (`advertise` + `publish`); hoy solo sabe suscribirse y mandar metas |
| `interfaz_web/js/app.js` | `ETAPA` y `NOMBRE_ETAPA` (línea 16-17), o el panel dirá *«desconocida (7)»*; `claveYTitulo` (176-188), o caerá en el `default` y dirá *«Sin misión activa»* en plena misión; `ORDEN_ETAPAS` (190), donde 7 ilumina *«Relevo»*; botón de confirmar, visible **solo** en etapa 7 |
| `interfaz_web/index.html`, `css/` | el botón y su estilo |
| `Documentos/CONTRATO_INTERFACES.md` | el tópico nuevo y el estado nuevo |
| `Documentos/REQUISITOS.md` | **RF-28** — el primer número libre; RF-27 es hoy el último. Trazado a OE3, porque es comportamiento de la interfaz de usuario. Las otras cuatro situaciones del director, y el *homing*, tomarán RF-29 y siguientes cuando se diseñen |

## 7. Cómo se comprueba que funciona

1. **Prueba pura nueva** `Robot/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py`,
   sin ROS ni simulador, junto a las otras pruebas del paquete:
   - la política de plazos en `0 s`, `59,9 s`, `60 s`, `119,9 s`, `120 s`, `120,1 s`;
   - que la alerta se emite **una sola vez** y no en cada tick del bucle;
   - el enganche: confirmación con `mision_id` ajeno se ignora; confirmación anterior al
     arranque de la misión se ignora; confirmación temprana se honra y se consume.
2. **Regresión** en `herramientas/prueba_componer_registro.py` y en
   `Robot/aws-deepracer/coordinacion/test/prueba_registrador.py`: una secuencia B que
   incluya marcas de etapa 7 con robot no vacío → `continuidad` sigue verdadera, la
   condición sigue siendo `B`, y las marcas siguen siendo monótonas.
3. **Tres corridas reales en simulación**, una por camino:
   - confirmar a los ~10 s → `COMPLETADA`, `continuidad: true`;
   - confirmar pasados los 60 s → la alerta aparece en el teléfono y hay dos marcas de
     etapa 7 en el bag con textos distintos;
   - no confirmar → `FALLIDA` a los 120 s, con el motivo redactado.

   Cada una se comprueba desde el bag con `componer_registro.py` y se valida contra
   `esquema_registro_mision.json`.
4. **Revisión de la HRI**: en etapa 7 el panel muestra el título correcto y el botón de
   confirmar; en cualquier otra etapa el botón no está.

   Esto se comprueba con `interfaz_web/prueba_confirmacion_piso.js`, que carga los dos
   archivos reales de `interfaz_web/js` sobre un DOM mínimo y el WebSocket nativo de Node,
   contra el rosbridge y el coordinador reales. El equipo no tiene navegador automatizable
   —solo Firefox, sin geckodriver, selenium ni playwright—, así que el dibujado de píxeles se
   verifica una vez a mano, con captura de pantalla; todo lo demás (qué etapa enciende el
   botón, qué publica al pulsarlo, y que desaparece al salir de la etapa 7) queda automatizado
   y vuelve a correrse en cada cambio.

Una corrida cuyo registro valide pero cuyo `continuidad` salga `false` es un fallo de este
diseño, no una anomalía del banco: la condición D-C4 existe precisamente para eso.

## 6. Plan de implementación

Las siete tareas, con los archivos exactos y los comandos de verificación de cada paso, están
en `Documentos/PLAN_RF28_CONFIRMACION.md`.
