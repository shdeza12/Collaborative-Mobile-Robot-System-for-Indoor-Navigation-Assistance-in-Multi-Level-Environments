# Plan de la semana 22 — del lunes 7 al domingo 13 de septiembre de 2026

Se escribe el domingo 2026-09-06 por la noche, antes de que abra la semana, siguiendo la costumbre
que [`PLAN_S20.md`](PLAN_S20.md) fijó y explicó en su primer párrafo.

> **Corregido el lunes 2026-09-07 por la mañana.** Los encabezados del §4 asignaban mal los días
> —empezaban en «Lunes 8» cuando el 8 de septiembre es martes—, con lo que todo el reparto quedaba
> corrido un día respecto al título. Se reetiquetan del 7 al 13. El contenido de cada jornada no
> cambia; el colchón pasa de un día a dos (sábado 12 y domingo 13).

Manda el [cronograma S17–S32](CRONOGRAMA_S17_S32.md) §S22. Este documento **no lo reinterpreta**:
reordena la semana dentro de él, y el único cambio de fondo —adelantar el G2 del viernes al martes—
tiene su motivo escrito en §2.1.

---

## 1. Dónde estamos al empezar

El cronograma fija para S22 este criterio de cierre:

> *«Desde un teléfono se selecciona origen y destino, y el sistema completa el guiado con relevo en
> simulación sin intervención manual.»*

Y fija cuatro actividades: la interfaz web (OE3), la integración de extremo a extremo, el despliegue
sobre los vehículos físicos según el resultado del GO/NO-GO, y emitir el entregable de S21.

**De esas cuatro, una ya está hecha y otra no se puede hacer todavía.** El entregable de S21
([PDF](Entregables/Entregable_semana_21.pdf), 22 páginas) se emitió el 2026-09-05, el mismo día de
la campaña. Y el despliegue sobre los vehículos «según el resultado del go/no-go» no tiene resultado
que consultar, porque **el GO/NO-GO no está resuelto**.

| Lo que ya está | Lo que no |
|---|---|
| La campaña de OE4 corrida, analizada y con veredicto `VALIDA`, 0 de 30 descartes | **El G2 no se corrió.** No hay M1, no hay M2, no hay GO/NO-GO |
| RF-17, RF-18 y RF-19 verificados contra un `coordinador` real | RF-20 solo probado en emulación, nunca en un teléfono físico |
| `interfaz_web/` **ya está en `main`** (ver §1.2) | La cadena completa teléfono → coordinador → dos robots vivos nunca se ha corrido entera |
| El relevo ejecutado con los dos robots vivos, 15 veces en campaña | RF-08: no existe publicador de `/<ns>/estado`. Es el **único rojo de OE1** |
| Los dos defectos de la cadena `/cmd_vel` corregidos desde el 27-ago | La **escala** de esa cadena: el escalón mínimo cae en 0,40 m/s y Nav2 pide 0,25 y 0,05 |
| `coordinacion_msgs` compilado y con round-trip real en Humble | Nunca se ha compilado en la tarjeta Jazzy del carro |
| RF-25 con esquema versionado y 30 registros validados | `salud_del_banco.controladores_activos` sale **vacío en 30 de 30**. RF-25 sigue 🟡 por un campo |

**Aritmética de la que sale el orden de la semana.** La congelación de código es **S23, del 14 al 20
de septiembre**. Esta es la **penúltima semana en la que se puede escribir funcionalidad**. Todo lo
que sea código nuevo entra ahora o no entra.

### 1.1 El G2 se cayó del calendario en silencio, y eso es lo primero que hay que arreglar

El [`PLAN` de S21 dentro de `ESTADO.md`](../ESTADO.md) tenía para el viernes 4 por la mañana:

> *«G2 por la mañana (recta de ≥ 20 m sobre el vehículo) · Bag evaluable contra M1 y M2, y el
> GO/NO-GO resuelto. **G2 es lo único que impide que el GO/NO-GO de S21 devuelva un GO falso.**»*

Comprobado el 2026-09-06 contra los archivos, no contra el tablero:

- En `Evidencia/` el último `S21_*` es `S21_metricas_campana_oe4.json`. Existe
  [`S21_preparacion_G2.md`](Evidencia/S21_preparacion_G2.md) —la preparación— y ningún resultado.
- **No hay ningún M1 ni ningún M2 calculado** en ningún documento del repositorio.
- En `~/tesis_evidencia/` no hay un solo bag del pasillo posterior al 4-sep: todo lo del 4 y del 5
  son los `S21_OE4_NN` de la campaña, y el primero es del viernes a las 19:21.
- **R3 sigue diciendo hoy, en el tablero:** *«Sigue 🔴 para el vehículo físico, pendiente de la
  corrida de ≥ 20 m»*.
- El cierre de S21 escribe *«el camino crítico queda con dos hitos amarillos»* y **no menciona G2**.

**Lectura, sin rebajarla:** la campaña de OE4 se comió la mañana del viernes y el G2 desapareció sin
que nadie lo anotara. Es la misma forma de fallo que el proyecto se reprochó el 26-ago —*«el GO/NO-GO
estaba calibrado para no verlo»*— en otra versión: ahora ni siquiera está calibrado, está sin correr.
Y el resultado de la semana fue tan bueno que tapó la omisión, que es exactamente cuando estas cosas
pasan desapercibidas.

### 1.2 Corrección de tablero: la HRI ya está fusionada

`ESTADO.md` dice hoy *«`interfaz_web/`, rama `interfaz-hri-web`, **sin PR aún**»*. Verificado el
2026-09-06:

```bash
git rev-list --count main..origin/interfaz-hri-web
```

devuelve **0**: la rama no tiene ni un commit que `main` no tenga, `interfaz_web/` está en el árbol
de trabajo y `ac2a3b3` figura en `git branch --contains`. **La integración de la HRI al repositorio
no es trabajo pendiente de esta semana**; lo que queda de OE3 es RF-20 en un teléfono de verdad y el
criterio de cierre de arriba. Se corrige en el corte del viernes.

---

## 2. Por qué la semana va en este orden

### 2.1 El G2 se adelanta del viernes al martes, y el motivo es que ya se cayó una vez

En S21 el G2 estaba el viernes y otra cosa se lo llevó por delante. Ponerlo otra vez al final de la
semana es repetir la apuesta con menos margen, porque detrás ya no hay una semana de desarrollo sino
la de congelación.

Con el G2 el martes: si sale mal —batería otra vez, mapa curvo otra vez, el «caso plátano» del 3-sep—
quedan **tres días de la misma semana** para repetirlo. Con el G2 el viernes, un fallo se arrastra a
S23, que es cuando el código ya no se puede tocar.

### 2.2 Las tres cosas del carro son una sola salida

G2, la calibración de escala de `/cmd_vel` (RF-14) y compilar `coordinacion_msgs` en la tarjeta Jazzy
son tres pendientes distintos que necesitan **el mismo carro encendido en el mismo sitio**. Tratarlos
como tres tareas es planificar tres salidas donde cabe una. Van juntos el martes, en ese orden de
prioridad: si el día se acorta, lo que se sacrifica es lo último.

Y ninguno de los tres está bloqueado por **R11**: los tres se hacen con el vehículo que sí hay.

### 2.3 RF-08 va el lunes porque es el único rojo de OE1 y es código

RF-08 —cada agente publica su estado a 2 Hz en `/<ns>/estado`— **no está en rojo por descuido de
registro: no hay publicador**. Es el único requisito rojo de OE1, el objetivo que está al 80 %, y
además la prueba de RF-06 se apoya en él (*«el segundo agente permanece en estado `LIBRE`»*).

Va el lunes y no el viernes por una razón sola: **es lo único de la lista que es código nuevo puro**,
y el código nuevo tiene fecha de caducidad el 20 de septiembre. Lo demás de la semana es integración,
medición o limpieza, y eso sí se puede hacer en S23.

---

## 3. La enmienda de M1 y M2, ya tomada

**Decidida el 2026-09-06, antes de salir al pasillo**, como obliga el §7 del protocolo experimental.
Queda escrita en el bloque G2 de [`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md) §S21; el fundamento
completo está en el §4 de [`S21_preparacion_G2.md`](Evidencia/S21_preparacion_G2.md).

| | Antes | Ahora | Función |
|---|---|---|---|
| **M1** — desplazamiento registrado ÷ real | ≥ 0,90 | **\|ratio − 1\| ≤ 0,10**, de dos lados | **Puerta** |
| **M2** — error de `/amcl_pose` contra cinta | ≤ 0,50 m | Se reporta el valor, sin umbral | **Medida** |

- **M1 pasa a dos lados** porque, tal como estaba, no podía fallar: toleraba un 10 % cuando el peor
  error jamás medido es 5,7 %, y sin cota superior el **+2,9 % largo** del carro pasaba por
  definición. Los tres casos ya medidos lo pasan: 1,029 · 0,943 · 0,987.
- **M2 baja de puerta a medida** porque su resultado se calcula sin correrla: 0,029 × 20 m = 0,58 m,
  y R3 dice que AMCL no corrige ese eje en un pasillo uniforme. Se corre igual, porque **la pregunta
  abierta de verdad es cuánto recupera AMCL con geometría real** —marcos de puerta, mobiliario,
  gente—, y eso se responde con un número.
- **El GO/NO-GO ramifica solo sobre M1.** Un M2 alto no manda parar: R3 está documentado y el 26-ago
  se decidió no construir la solución de localización dentro de este trabajo. Si M2 sale por encima
  de 0,50 m se registra como **limitación medida** y el cronograma no se renegocia.

---

## 4. La semana, día a día

### Lunes 7 — Preparación del carro y RF-08

| | |
|---|---|
| **Comando** | `git pull && bash herramientas/verificar_repositorio.sh` |
| **Resultado esperado** | 12/12 |
| **Si difiere** | Arreglar antes de seguir; un repositorio que se contradice invalida todo lo que se escriba encima esta semana |

**Tarea 1 — poner la batería a cargar.** Sin comando y es la más importante del día. El «caso plátano»
del 3-sep —mapa de 47,50 × 29,05 m sobre una recta de 20,08 m— tiene como causa más probable la
batería, y no por descarte: a las 23:47 con el carro agonizando `/scan` daba `max 0,464 s` entre
barridos y `std dev 0,072`; recargado, a las 00:36, con el mismo sensor y los mismos procesos, daba
`max 0,177 s` y `std dev 0,008`. **Nueve veces más estable.** El bag que salió curvo se grabó entre
esas dos medidas.

- **Criterio de cierre:** carro a plena carga la noche del lunes, y una batería de repuesto cargada si
  la hay.

**Tarea 2 — releer la hoja de campo y marcar lo que falte.**
[`HOJA_CAMPO_G2.md`](HOJA_CAMPO_G2.md) tiene los seis bloques del martes escritos paso a paso, con la
lista de lo que hay que llevar (§3) y la regla de decisión del caso plátano (§7). No se reescribe: se
lee y se comprueba que el material de §3 existe.

**Tarea 3 — RF-08: publicador de `/<ns>/estado` a 2 Hz.**

| | |
|---|---|
| **Dónde** | `Robot/aws-deepracer/coordinacion/coordinacion/` — el mensaje `EstadoRobot.msg` **ya existe** en `coordinacion_msgs/msg/`, así que no hay contrato que negociar |
| **Orden** | Prueba primero, como el resto de la instrumentación del proyecto (`prueba_banco_tiempo_asignacion.py`, `prueba_medir_g2.py`, `prueba_grabar_mision.py` se escribieron así) |
| **Comando de comprobación** | `ros2 topic hz /robot1/estado` con la simulación viva |
| **Resultado esperado** | ~2 Hz, y el campo `estado` cambia de `LIBRE` a ocupado al iniciar una misión |
| **Si difiere** | Si publica pero no a 2 Hz, es el temporizador. Si no publica, comprobar el espacio de nombres: la separación del proyecto es por namespace, no por dominio, desde el 30-ago |
| **Criterio de cierre** | RF-08 pasa de 🔴 a 🟢 en `REQUISITOS.md`, con la salida de `topic hz` guardada en `Evidencia/logs/` |

> **Ojo con la trampa que este proyecto ya conoce:** una prueba que compruebe solo *«el tópico
> existe»* es una prueba que no puede fallar, de la misma clase que la de RF-22. La prueba tiene que
> comprobar **frecuencia** y **cambio de valor**, que es lo que dice el requisito.

---

### Martes 8 — Salida al pasillo: G2, escala de `/cmd_vel`, `coordinacion_msgs` en Jazzy

**El procedimiento no se improvisa: está en [`HOJA_CAMPO_G2.md`](HOJA_CAMPO_G2.md).** Lo que sigue es
el orden del día y los criterios, no una segunda versión de la guía.

| Bloque | Qué | Tiempo | Criterio |
|---|---|---|---|
| 1 | Medir y marcar la recta (cruces, no rayas, en los dos extremos) | 25 min | La recta de ≥ 20 m **existe** y está medida. Si no existe, G2 tal como está escrito no es válido y hay que parar a redefinirlo |
| 2 | Arrancar el LiDAR y comprobar que publica | 10 min | **Publicador y grabador con el mismo dueño.** Es la causa raíz del 4-sep: el transporte pasa por buzones `/dev/shm/fastrtps_port70NN` y el publicador tiene que poder escribir en el del suscriptor. El fallo es **silencio, no error** |
| 3 | Pasada de mapeo, grabando | 15 min | `grep message_count` **antes de recoger**, y `comprobar_movimiento_bag.py` dice `SIRVE` |
| 4 | Construir el mapa **allí mismo** | 10 min | El mapa mide lo que mide el pasillo. **Caso plátano:** si mide más del doble, comprobar batería, repetir **una** vez, y si vuelve a salir curvo **parar y no correr las seis pasadas de localización** — se miden contra ese mapa |
| 5 | Montar el mando | 20 min | Teleop responde |
| 6 | Seis pasadas de localización, tres por sentido | 40 min | Mínimo duro: **una por sentido**, para no volver con nada |

**Análisis, en el portátil, el mismo martes:**

```bash
bash herramientas/localizar_desde_bag.sh <bag> && python3 herramientas/medir_g2.py <trayectoria.csv> --largo 20.08 --json Documentos/Evidencia/S22_G2_resultado.json
```

| | |
|---|---|
| **Resultado esperado** | M1 y M2 con cifras separadas **por sentido** — el 26-ago hubo un factor de cuatro entre este y oeste, y promediar lo borra |
| **Predicción anticipada** | `medir_g2.py` ya reproduce el §4: M1 = 1,029 y M2 = 0,58 m sobre 20 m. El martes el resultado se **contrasta contra un número escrito de antemano**, no solo se registra |
| **Si el bag es de la tarjeta Jazzy** | `python3 herramientas/adaptar_bag_jazzy.py <bag>` primero: Jazzy escribe `metadata.yaml` en versión 9 y el `yaml-cpp` de Humble aborta con `bad conversion` en la línea 15 |
| **Criterio de cierre** | `Evidencia/S22_G2_resultado.md` con M1, M2 **y el GO/NO-GO resuelto por escrito**, en una frase que diga GO o NO-GO y qué implica |

**Si sobra tiempo, en este orden:**

1. **Escala de `/cmd_vel` (RF-14).** El escalón más bajo de la cadena cae en 0,40 m/s y Nav2 pide
   **0,25 en curva y 0,05 en la aproximación**, así que hoy devuelve **cero justo donde Nav2 la
   usa**. Es calibración contra el vehículo, no mapeo: los dos defectos de mapeo están corregidos
   desde el 27-ago con 19 comprobaciones en `prueba_mapeo_servo.py`. **Criterio:** una tabla de
   throttle contra velocidad medida, con al menos un punto por debajo de 0,25 m/s.
2. **`coordinacion_msgs` en la tarjeta Jazzy.** `colcon build --packages-select coordinacion_msgs`
   sobre la tarjeta. **Criterio:** compila; y si no compila, el error queda anotado, porque eso sería
   R8 materializándose y hay que saberlo antes de S23.

---

### Miércoles 9 — Integración de extremo a extremo en simulación

Esta es la actividad que el cronograma nombra como *«integrar los cuatro módulos de extremo a extremo
en simulación»*, y es la primera vez que las cuatro piezas —Gazebo con los dos robots, el coordinador,
`rosbridge_websocket` y la HRI— corren **a la vez**. La verificación del 2-sep fue contra un
`coordinador` real pero **sin Gazebo y sin robots**.

| Paso | Comando | Resultado esperado |
|---|---|---|
| 1 | `herramientas/lanzar_sim.sh <mundo>` con los dos espacios de nombres | Los dos robots vivos, controladores activos |
| 2 | El coordinador | Un solo `/coordinacion`. **Dos coordinadores vivos es un fallo conocido**: fue lo que el 4-sep se confundió con un «estado 6» de Nav2 |
| 3 | `rosbridge_websocket` | Puerto escuchando |
| 4 | La HRI desde el navegador del portátil | Catálogo de 31 puntos con QoS `transient_local` |

| | |
|---|---|
| **Si difiere** | Si el catálogo llega vacío, es el QoS. Si la misión no arranca, comprobar que hay **un** coordinador y no dos |
| **Criterio de cierre** | Una misión de dos niveles lanzada **desde el navegador**, completada con relevo, sin tocar la terminal después de pulsar |

---

### Jueves 10 — RF-20 en un teléfono físico y la corrida del criterio de cierre

| | |
|---|---|
| **Qué** | Lo mismo del miércoles, pero desde el teléfono, en la misma red y **sin salida a internet** |
| **Por qué importa el «sin internet»** | RF-20 lo exige, y por eso la HRI se escribió sin CDN y sin `roslib.js`. Probarlo con internet disponible **no prueba el requisito** |
| **Resultado esperado** | Carga, catálogo, selección origen–destino, misión completa con relevo, mensajes al usuario legibles en la pantalla del móvil |
| **Si difiere** | Si carga pero no conecta, es la IP del `rosbridge` —`localhost` no vale desde el móvil—. Si no carga, es el cortafuegos del portátil |
| **Criterio de cierre** | **El criterio de cierre de S22 entero**, grabado en bag y con su registro compuesto, más capturas del teléfono en `Evidencia/` |

Es la corrida que se le enseña al jurado. Conviene grabarla en vídeo además del bag.

---

### Viernes 11 — Limpieza y corte semanal

Tres tareas de tamaño conocido, en orden de valor:

| # | Tarea | Criterio de cierre |
|---|---|---|
| 1 | **`controladores_activos` sale vacío en 30 de 30.** El compositor lo escribe como `{}` (`componer_registro.py:931,935`) mientras el registrador sí lo llena (`registrador.py:268,284`). **Es un campo, y es lo único que mantiene RF-25 en 🟡** | RF-25 pasa a 🟢, con un registro nuevo que traiga `"7/7"` |
| 2 | **R12 — la misión de 85 cúspides.** Estrato B12, contra una mediana de 7 y un máximo de 13 en el resto. El bag está conservado. Investigarla **ahora sí se puede**: la campaña ya está cerrada y analizada, así que no es tocar datos después de verlos, es explicar una anomalía anotada | R12 pasa a 🟢 con la causa escrita, o se documenta por qué no se pudo |
| 3 | **Barrer `PROTOCOLO_EXPERIMENTAL.md` buscando más pruebas que no pueden fallar.** Pendiente declarado el 5-sep. Ya hay **dos** precedentes: RF-22 y la puerta M1 | Cada §3.x y §4 revisado con una frase que diga si su criterio puede fallar |

**Corte semanal por la noche**, según la regla del 2026-08-18:

- `ESTADO.md`: avance por OE, camino crítico, riesgos, bitácora. **Incluir la corrección de §1.2**
  (la HRI ya está en `main`) y el resultado del GO/NO-GO.
- Entregable S22.
- Batería completa antes de empujar: `verificar_repositorio.sh` 12/12, `colcon build` limpio de los
  8 paquetes del repositorio, las pruebas `prueba_*.py` en verde, barrido de enlaces rotos.
- Commit y push.

---

### Sábado 12 y domingo 13 — Colchón

No llevan tarea propia **a propósito**. Se reservan para lo que se salga de los cinco días anteriores,
que en este proyecto ha sido la norma y no la excepción: S19 se cerró sin documento, S20 y S21
corrieron el corte del viernes al sábado.

Si nada se salió, entra el arrastre: los tres pendientes que quedaron fuera de §5 por prioridad.

---

## 5. Lo que NO entra en S22, y conviene decirlo por escrito

- **RF-15** (latencia de red entre los dos vehículos) — atado a **R11**, el segundo DeepRacer en
  intervención técnica desde el 2026-08-14, **abierto y sin caracterizar**. No depende de horas de
  trabajo. Sigue pendiente que Jonny declare por escrito qué vehículo es y cuándo vuelve.
- **RF-27** (campaña física de 5 a 10 corridas) — es S24–S25 y depende del resultado del G2.
- **No se repite ninguna misión de la campaña de OE4.** Está `VALIDA` con 0 de 30 descartes. Repetir
  una campaña válida sin una razón declarada de antemano es cocinar los datos, y el §6.3 del
  protocolo lo prohíbe.
- **No se redacta el capítulo de resultados.** Es S24 y S26. Meterlo aquí desplaza código que después
  de la congelación ya no se puede escribir.
- **No se toca el URDF del LiDAR (R13)**, aunque sim y hardware no sean comparables en esa variable.
  Cambiarlo invalida la comparación con las corridas anteriores, incluida la campaña de 30 misiones
  que se acaba de cerrar. Es una decisión de validez externa para el documento, no un arreglo.

---

## 6. El criterio de éxito de la semana

Para que el viernes no se discuta, tres cosas y en este orden:

1. **El GO/NO-GO está resuelto por escrito**, con M1 y M2 medidos y el veredicto contrastado contra la
   predicción del §4. *Un NO-GO también cumple este criterio* — lo que no lo cumple es volver a
   terminar la semana sin el número.
2. **El criterio de cierre del cronograma se cumple:** desde un teléfono se selecciona origen y
   destino y el sistema completa el guiado con relevo, sin intervención manual.
3. **RF-08 deja de ser rojo**, y con él OE1 se queda sin ningún requisito pendiente que dependa solo
   de escribir código.

Lo que **no** es criterio de esta semana: la demostración física con los dos vehículos. Eso depende
de R11, y R11 no depende de nosotros.
