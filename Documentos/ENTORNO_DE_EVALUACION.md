# Entorno de evaluación y escalamiento de pruebas

**Fecha:** 2026-08-06 (S17)
**Estado:** aprobado — pendiente de reflejarse en `Cronograma_S17_S32.tex` y `Entregable_semana_17.tex`
**Documento de referencia:** `Anteproyecto_Jonny_Santi.pdf`

Este documento fija dónde se evalúa el sistema y en qué orden se prueban las cosas. No
introduce alcance nuevo: es el resultado de la actividad *Análisis del entorno de evaluación*
que el propio anteproyecto programó en Fase 2 (Cuadro 8.1, S9–S11) y que hasta ahora no
se había documentado.

---

## 1. Pregunta de investigación

El anteproyecto no la formula de manera explícita: el capítulo 2 tiene una sola sección
(«2.1 Planteamiento») y no existe un apartado de pregunta de investigación, pese a que el
cronograma del anteproyecto sí incluye la actividad «Formulación de pregunta de
investigación — S3». Se formula aquí, destilada del párrafo de cierre del planteamiento, y
debe incorporarse al documento final.

> **¿Puede un esquema de relevo entre robots móviles de bajo costo, cada uno dedicado a un
> nivel y coordinados mediante comunicación inter-robot, mantener la continuidad del
> servicio de orientación a un visitante a través de las discontinuidades verticales de un
> edificio, sin hardware especializado para transiciones verticales ni intervención sobre la
> infraestructura?**

El argumento es de **sustitución**: donde la literatura resuelve el cambio de piso con
locomoción sobre escalones o con intervención electrónica sobre los ascensores —caro e
invasivo—, aquí se sustituye ese hardware por coordinación. Lo que atraviesa el piso es la
comunicación entre agentes, no el robot.

Toda decisión de este documento se justifica contra esta pregunta.

---

## 2. Encuadre: esto no es una replanificación

El anteproyecto **nunca nombra un sitio de pruebas**. La palabra «pasillo» no aparece en el
documento. Lo que compromete es:

| Fuente | Texto |
|---|---|
| §4.3 Alcance | «un entorno interior previamente definido» |
| §4.3 Alcance | «un espacio previamente delimitado», «condiciones controladas» |
| §4.3 Alcance | «un entorno interior con multiples pisos» |
| §4.3 Alcance | «un punto de transición vertical —como una zona de escaleras o ascensores—» |
| OE4 | «pruebas experimentales en un entorno interior controlado» |

La única mención a la primera planta de la universidad (§6.1.1) aparece al citar el trabajo
previo de Parra Buitrago (2021) en el estado del arte; no es un compromiso de escenario.

En consecuencia, los mundos `pasillo_usta/` (7×3 m), `pasillo_grande/` (15×5 m) y
`USTA_WORLD/` no son compromisos del anteproyecto: son las instancias que se eligieron
durante Fase 4 para desarrollar el wall-follower, contra el criterio de esa fase (disponer de
un pasillo donde seguir paredes). Ese criterio ya no es el vigente.

---

## 3. Criterio de selección

Del alcance se derivan cuatro condiciones que el entorno de evaluación debe cumplir:

1. Interior.
2. Controlado (condiciones repetibles).
3. Con **múltiples niveles**.
4. Con **punto de transición vertical**.

Un espacio de un solo nivel falla en (3) y (4). Como la pregunta de investigación es
precisamente sobre cómo se atraviesa la discontinuidad vertical, en un espacio de un nivel
la pregunta **no se puede plantear**, no solo responder peor.

---

## 4. Entorno de evaluación: `primer_piso` replicado en dos niveles

**Base:** `primer_piso_v2.world` (17 elementos de colisión, frente a 9 de la versión 1).
Paredes de 2,5 m de alto y 0,15 m de espesor, con tramos de hasta 44,25 m y 12,25 m. Corresponde a la
primera planta del edificio de la USTA.

**Fidelidad de la duplicación.** El segundo piso real del edificio es idéntico al primero.
Replicar la planta con desplazamiento vertical no es una simplificación de modelado: es la
geometría real. Este es el argumento más fuerte del entorno elegido y hay que enunciarlo
así en el documento final.

**Implementación** (2026-08-14). La planta se extrajo de `primer_piso_v2.world` a un modelo
reutilizable, `primer_piso/`, y el entorno vive en `primer_piso_dos_niveles.world`, que la
instancia dos veces:

| Elemento | Valor |
|---|---|
| `primer_piso_n1` (nivel 1) | pose `20.9036 1.43563 0` |
| `primer_piso_n2` (nivel 2) | pose `20.9036 1.43563 3.0` |
| Separación vertical | **3,0 m** |
| `losa_nivel_2` (suelo del nivel 2) | caja `50 × 20 × 0,1` en `22.5 1.5 2.95`; cara superior en z = 3,0 |
| **Zona de transición** | centro **(41,40 · 3,03)**, cuadrado de 1,5 × 1,5 m |

La losa existe porque `ground_plane` solo está en z = 0: sin ella el nivel 2 no tiene suelo.

**La zona de transición no tiene `<collision>`, y es deliberado.** Es una marca, no un
obstáculo: no debe estorbar la navegación ni aparecer en el mapa de ocupación. Vive dentro de
`primer_piso/model.sdf`, así que al instanciarse el modelo dos veces cae en las mismas
coordenadas x-y de las dos plantas — que es justo lo que el esquema de relevo necesita.

**De dónde salen esas coordenadas.** No se estimaron a ojo: se derivaron de la geometría. La
planta es un pasillo de ~44 m con un recinto terminal en el extremo este, acotado por
`Wall_19` al sur (y = 2,00), `Wall_17` al norte (y = 4,07) y `Wall_15` al oeste (x = 39,78,
que solo llega hasta y = 2,06 y por eso deja el paso abierto). El recinto abarca
`x ∈ [39,85 · 42,95]` e `y ∈ [2,08 · 3,99]`; su centro es (41,40 · 3,03) y la marca de 1,5 m
deja ~0,20 m de holgura en y y ~0,80 m en x.

**Confirmado el 2026-08-14:** ese recinto es el descanso de la escalera real del edificio. La
derivación geométrica y la planta real coinciden, lo que refuerza el argumento de §4 sobre la
fidelidad del entorno.

**Qué NO se modela, y por qué:**

- **Escaleras transitables.** Ningún vehículo sube escaleras. El alcance excluye
  explícitamente «interactuar mecánicamente con la infraestructura del edificio, como
  accionar puertas o presionar botones de ascensores», y el esquema de relevo no lo
  necesita: el agente 1 entrega en el punto de transición del nivel de origen y el agente 2
  ya está en el nivel de destino. Modelar locomoción sobre escalones sería resolver el
  problema que la tesis argumenta que no hay que resolver.
- **El laboratorio GED.** Ver §5, etapa 2.

**Rol de los mundos de Fase 4.** `pasillo_usta/`, `pasillo_grande/` y `USTA_WORLD/` se
conservan y se declaran como escenarios de desarrollo del wall-follower. No se borran ni se
presentan como entorno de evaluación.

---

## 5. Escalamiento de pruebas

Tres etapas, cada una con una pregunta distinta. No son alternativas: son secuencia.

| Etapa | Dónde | Qué responde | Evidencia que produce |
|---|---|---|---|
| 1 | Simulación: `primer_piso` × 2 niveles | ¿El esquema de relevo mantiene la continuidad del servicio entre niveles? | 30 repeticiones del protocolo, las cuatro métricas del OE4 |
| 2 | Laboratorio GED, 4×4 m, un nivel | ¿El hardware hace lo que la simulación dice? | Locomoción bajo ROS 2, localización, latencia inter-robot, *handshake* del relevo |
| 3 | Pasillo real USTA, dos plantas | ¿Se sostiene en el espacio que se simuló? | Comparación directa simulación–real sobre la misma geometría |

**Por qué el laboratorio no es entorno de evaluación.** Son 16 m² en un solo nivel. El
vehículo tiene un círculo de giro de 0,57 m de diámetro real (0,70 m con el
`minimum_turning_radius: 0.35` configurado), de modo que en 4 m caben unos cinco círculos de
giro; los recorridos caerían a 2–3 m y las métricas de navegación se degeneran. Una sala
cuadrada vacía es además el peor caso para AMCL: el LiDAR de 10 m ve las cuatro paredes
desde cualquier punto, lo que deja la pose mal condicionada bajo rotación. Y sobre todo, no
tiene discontinuidad vertical: la pregunta de investigación no se puede plantear ahí.

**Por qué el laboratorio tampoco se modela en Gazebo.** Su único uso posible como modelo
sería medir la brecha simulación–realidad. Esa brecha se mide en la etapa 3, donde el mapa
simulado *es* esa misma planta, así que la medición es directa y más significativa. Un
modelo menos y una tanda de repeticiones menos.

**Etapa 3: el premio.** Con acceso confirmado a las dos plantas y al descanso de la
escalera, el relevo físico entre pisos se demuestra sobre la geometría exacta que se simuló.
Es la mejor evidencia que el proyecto puede producir, y responde la pregunta de
investigación en el mundo físico, no solo en simulación.

---

## 6. Compuerta entre etapas 2 y 3

**Criterio:** un vehículo navega punto a punto de forma autónoma en el laboratorio, con
localización estable.

**Lo que explícitamente NO es la compuerta:** el relevo completo entre dos vehículos. El
relevo es el núcleo del cumplimiento del proyecto; usarlo como precondición para avanzar
haría que el objetivo dependiera de su propio logro previo y bloquearía la secuencia. El
relevo se desarrolla en paralelo y su evidencia garantizada vive en la etapa 1, que no
depende de hardware ni de permisos.

---

## 7. Punto de decisión: el segundo vehículo (S21)

Riesgo dominante que queda. Hoy hay un DeepRacer liberado y verificado en marcha; el segundo
no está verificado.

- **Si hay dos vehículos operativos:** el relevo físico se demuestra con dos vehículos
  reales, uno por planta.
- **Si solo hay uno:** la demostración física del relevo se hace con un vehículo real y uno
  simulado, y se declara como tal.

En ninguno de los dos casos se mueven las fechas, y en ninguno se compromete la evidencia
del relevo, que ya está cubierta por la etapa 1.

---

## 8. Qué se mide

Las cuatro métricas del OE4 no tienen el mismo peso frente a la pregunta de investigación:

| Métrica | Rol |
|---|---|
| **Continuidad del servicio entre niveles** | **Variable de respuesta principal** |
| Tasa de éxito en la entrega de asistencia | Apoyo |
| Tiempo de asignación de robot | Apoyo |
| Tiempo de respuesta | Apoyo |

Si el protocolo experimental no se construye alrededor de la continuidad, mide magnitudes
correctas para una pregunta distinta de la que el proyecto plantea.

---

## 9. Limitaciones declaradas

Se enuncian en el documento final; no se ocultan.

1. **Las repeticiones en el pasillo se hacen en franjas de baja circulación.** El alcance
   exige condiciones controladas. Las personas como obstáculos dinámicos se pueden registrar
   como observación cualitativa, pero no entran en las 30 repeticiones: introducirían
   varianza no controlada.
2. **El laboratorio no representa el entorno de operación.** Su función es verificar la
   plataforma, no el sistema.
3. **Los vehículos no atraviesan físicamente el punto de transición.** Es una consecuencia
   deliberada del esquema de relevo, no una carencia.
4. **Toda la evidencia cartográfica anterior al 2026-08-05 está invalidada** por
   `max_laser_range: 12.0` frente a un LiDAR de 10,0 m de alcance real. Los mapas
   `primer_piso.pgm` y `primer_piso_v2.pgm` deben rehacerse.

---

## 10. Actividad nueva: mapeo físico de las dos plantas

Aparece a raíz del acceso confirmado al pasillo, y tiene doble propósito:

1. **Insumo operativo:** los mapas que necesita AMCL para navegar en la etapa 3.
2. **Validación del modelo:** el mapa SLAM del primer piso real, contrastado contra el
   modelo `primer_piso_v2`, da una comprobación *en metros* de si el entorno simulado
   representa el edificio. Hasta ahora eso era un supuesto no verificado.

Debe rehacerse en cualquier caso por la limitación 4 de §9.

---

## 11. Efecto sobre los documentos ya emitidos

**`Documentos/Entregables/Cronograma_S17_S32.tex`**

- S18: sustituir «medir el laboratorio y modelar su planta, duplicada en dos niveles» por
  «replicar `primer_piso_v2` en dos niveles con zona de transición vertical».
- S18, criterio de cierre: sustituir «el mundo del laboratorio carga en el simulador con sus
  dos niveles» por la referencia a `primer_piso`.
- S21: cambiar el objeto del punto de decisión — ya no es el acceso al pasillo (confirmado),
  sino el segundo vehículo.
- S21/S22: la compuerta de paso al pasillo es la de §6.
- S22 y S25: las pruebas físicas se reordenan según el escalamiento; las repeticiones de
  evaluación ocurren en el pasillo, no en el laboratorio.
- Añadir el mapeo físico de las dos plantas (§10).

**`Documentos/Entregables/Entregable_semana_17.tex`**

- Sección de próximos pasos: sustituir «Modelado del laboratorio GED en formato SDF,
  duplicado en dos niveles» por lo anterior.
- Incorporar la formulación explícita de la pregunta de investigación (§1).

---

## 12. Trazabilidad al anteproyecto

| Decisión de este documento | Ancla en el anteproyecto |
|---|---|
| Documentar la selección del entorno | Cuadro 8.1, Fase 2: «Análisis del entorno de evaluación, S9–S11» |
| Entorno interior, controlado, con múltiples niveles y transición vertical | §4.3 Alcance |
| Ningún vehículo sube escaleras ni acciona ascensores | §4.3 Alcance (exclusiones) |
| El relevo entre agentes dedicados por nivel es el objeto de estudio | §2.1 Planteamiento, párrafo de cierre |
| Continuidad del servicio como variable principal | OE4 |
| Dos agentes físicos | §4.3 Alcance, OE2 |
