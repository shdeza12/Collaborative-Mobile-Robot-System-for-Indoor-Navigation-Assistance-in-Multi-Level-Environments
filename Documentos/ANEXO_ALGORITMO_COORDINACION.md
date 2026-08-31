# Anexo · El algoritmo de coordinación: qué se implementó y por qué

**Fecha:** 2026-08-31 (S21)
**Estado:** redactado a petición del director (Armando Mateus), que preguntó qué algoritmo de
coordinación usa el proyecto
**Documentos de referencia:** `REQUISITOS.md` (RF-05, RF-07, RF-10),
`CONTRATO_INTERFACES.md`, `Robot/aws-deepracer/coordinacion/coordinacion/planificador.py`

Este anexo existe porque la respuesta no estaba escrita en ninguna parte. El código de
coordinación lleva funcionando desde el 2026-08-24 y se ejecutó de extremo a extremo el
2026-08-30, pero nadie había dejado por escrito **qué clase de problema resuelve** ni **contra
qué literatura se sitúa**. Sin eso, la pregunta del director no tiene respuesta defendible, y la
sección de coordinación del documento final tampoco.

No introduce alcance nuevo ni cambia una línea de código. Clasifica lo que ya existe.

---

## 1. Qué está implementado, exactamente

Conviene decirlo sin adornos antes de clasificarlo: **no se tomó ningún algoritmo de la
literatura como referencia de diseño.** Lo que hay es un esquema determinista propio, escrito
desde los requisitos. Tiene cuatro propiedades, y las cuatro son verificables en el código:

**Arquitectura centralizada.** Un único nodo `/coordinacion` planifica y despacha. Los agentes
nunca se comunican entre sí; toda la comunicación inter-robot pasa por el coordinador. Es
RF-10, y es una decisión, no una limitación heredada.

**Asignación por partición espacial estática.** El agente se elige por el nivel del punto de
origen. La regla completa es una tabla:

```python
# planificador.py:24
ASIGNACION_POR_DEFECTO = {1: "robot1", 2: "robot2"}
```

Es una consulta de diccionario, O(1). No hay pujas, ni funciones de costo, ni comparación
entre candidatos. El comentario que acompaña a esa línea ya declaraba la intención: cambiar
quién atiende qué piso es cambiar el dato, no la lógica.

**Descomposición secuencial de la misión en tramos, con encuentro en punto fijo.**
`planificar()` compara el nivel de origen con el de destino y devuelve una de dos formas
(`planificador.py:207-240`):

| Caso | Tramos | Etapas | Relevos |
|---|---|---|---|
| Mismo nivel | 2 | `TRAMO_1`, `TRAMO_1` | 0 |
| Niveles distintos | 4 | `TRAMO_1`, `TRAMO_1`, `TRANSFERENCIA`, `TRAMO_2` | 1 |

El punto de encuentro no se elige ni se negocia: es el punto de transferencia declarado del
nivel, leído del catálogo. Y el usuario cruza de nivel por su cuenta, porque ningún robot sube
escaleras (decisión D2).

**Una misión a la vez.** No existe noción de agente ocupado, ni cola, ni replanificación. Se
comprobó por inspección de `coordinador.py`: no hay ninguna estructura de disponibilidad.

---

## 2. Clasificación formal de la asignación

En la taxonomía de Gerkey y Matarić [1], que es la referencia canónica del área, la asignación
implementada es **ST–SR–IA**:

- **ST** (*single-task robots*): cada robot ejecuta una tarea a la vez.
- **SR** (*single-robot tasks*): cada tramo lo ejecuta un solo robot.
- **IA** (*instantaneous assignment*): se asigna al llegar la solicitud, sin planificar
  asignaciones futuras.

Ese trabajo demuestra que la clase ST–SR–IA es una instancia del **Problema de Asignación
Óptima**, y que por tanto admite solución **óptima en tiempo polinómico** mediante el método
húngaro. Es decir: el óptimo no es caro ni exótico, está disponible.

**Y aquí está el argumento que sostiene el diseño.** En este problema, la matriz de costos
tiene **un solo candidato admisible por tarea**, porque D2 confina cada robot a un nivel y
RF-01 fija exactamente dos agentes, uno por nivel. Aplicar el método húngaro a esta instancia
devuelve `{1: robot1, 2: robot2}` — no un resultado parecido, sino el mismo, siempre.

La ausencia de un optimizador no es entonces una carencia de implementación: es una
consecuencia demostrable de la estructura del problema. Un optimizador aquí sería decorado.

---

## 3. Por qué la misión no es ST–SR–IA, y dónde está el aporte

La clasificación anterior describe **la asignación**. No describe **la misión**.

El relevo impone una **restricción de precedencia**: el `TRAMO_2` de robot2 no puede comenzar
hasta que robot1 haya completado su tramo y el usuario haya cruzado físicamente de nivel. Las
agendas de los dos agentes quedan acopladas.

La taxonomía de 2004 está construida para tareas **independientes** y no cubre ese caso; sus
propios autores lo delimitan así. La extensión que sí lo cubre es la taxonomía **iTax** de
Korsah, Stentz y Dias [2], que clasifica los problemas por su grado de interrelación y que
nació precisamente porque la taxonomía clásica no trata utilidades y restricciones
interrelacionadas. En ella, esta misión cae en **XD** (*cross-schedule dependencies*): la
categoría de las dependencias entre agendas que surgen de tareas cooperativas y restricciones
de precedencia.

De ahí se sigue la lectura correcta del proyecto: **la asignación es trivial y demostrablemente
óptima; el aporte vive en una clase de problema que la taxonomía estándar del área no
contempla.** No es una conclusión nueva —`REQUISITOS.md:70` ya afirmaba, antes de existir esta
clasificación, que «RF-07 es el aporte declarado del proyecto»—, pero hasta ahora era una
afirmación sin respaldo formal. Ahora lo tiene.

---

## 4. Alternativas consideradas, y por qué se descartan

Se descartan por análisis, no por desconocimiento. Esa distinción importa: las cuatro se
evaluaron contra la estructura real del problema.

| Familia | Mecanismo | Qué requiere | Qué daría aquí | Veredicto |
|---|---|---|---|---|
| **Lo implementado** | Tabla `nivel → robot`, O(1) | Un agente por zona | La asignación forzada | Óptimo por estructura |
| **Método húngaro / OAP** | Minimiza el costo total en asignación 1-a-1, en tiempo polinómico | Matriz de costos con ≥ 2 candidatos por tarea | Resultado **idéntico** a la tabla | Sin efecto: un solo candidato admisible |
| **Contract Net y subastas** (Smith; MURDOCH, de Gerkey y Matarić) | El coordinador anuncia la tarea, los agentes pujan con su costo, gana el menor | Varios postores elegibles | Una subasta de **un solo postor** | Sin efecto, y añade latencia y mensajería |
| **CBBA** (consenso sobre pujas) | Asignación descentralizada por consenso entre agentes | Flota sin coordinador central | Contradice RF-10 | Rompe la arquitectura declarada |
| **iTax / scheduling con precedencias** | Modela dependencias entre agendas | Tareas con precedencia | **Describe lo que ya se hace** | Es el marco correcto para nombrar el relevo |

Ninguna de ellas cambiaría una sola decisión del sistema actual. Eso defiende el diseño, y a la
vez conviene reconocer lo que implica: no hay dónde colocar un algoritmo más sofisticado sin
inventar antes un problema que este sistema no tiene.

---

## 5. Límite conocido

La comparación destapa una carencia real, y no es de algoritmo sino de capacidad: **no hay
concurrencia**. Una segunda solicitud mientras una misión está en curso tiene comportamiento
indefinido, porque no existe noción de agente ocupado ni cola de espera.

Formalmente está fuera de alcance —ninguno de los requisitos RF-01 a RF-10 declara misiones
concurrentes, y el protocolo experimental ejecuta las 30 corridas de forma secuencial—, pero
la respuesta debe estar preparada y no improvisarse: *está fuera del alcance declarado, y es
justamente el punto donde una subasta empezaría a aportar algo.*

---

## 6. Trabajo futuro con fundamento

Toda la literatura del §4 se vuelve pertinente en cuanto se levante **una** suposición: que hay
un solo robot elegible por tarea. Ocurriría con dos o más agentes por nivel, con agentes
capaces de servir varios niveles, o con misiones concurrentes. En ese momento la matriz de
costos deja de tener un único candidato, el problema deja de estar forzado, y el método húngaro
o el Contract Net pasan a decidir de verdad.

Es una extensión natural del trabajo, no un relleno de sección.

---

## Referencias

[1] B. P. Gerkey y M. J. Matarić, «A Formal Analysis and Taxonomy of Task Allocation in
Multi-Robot Systems», *The International Journal of Robotics Research*, vol. 23, n.º 9,
pp. 939–954, septiembre de 2004. DOI: 10.1177/0278364904045564

[2] G. A. Korsah, A. Stentz y M. B. Dias, «A Comprehensive Taxonomy for Multi-Robot Task
Allocation», *The International Journal of Robotics Research*, vol. 32, n.º 12, pp. 1495–1512,
2013. DOI: 10.1177/0278364913496484
