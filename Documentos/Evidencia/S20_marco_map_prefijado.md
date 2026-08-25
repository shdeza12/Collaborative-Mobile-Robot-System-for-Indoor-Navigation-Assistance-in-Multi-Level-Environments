# S20 — El marco `map` se prefija con el namespace

**Fecha del cambio:** 2026-08-24. **Escrito:** 2026-08-25. **Código base:** `25ec8fb`.
**Cubre:** el fallo que dejó una misión del coordinador en `ABORTED` sin decir por qué, y su
corrección.

---

## Por qué existe este archivo

Tres archivos fuente lo citan por nombre —`deepracer_localization_sim.launch.py`,
`deepracer_navigation_sim.launch.py` y `slam_toolbox.launch.py`— y hasta hoy **no existía**. La
corrección se hizo el 24-ago y se documentó únicamente en los comentarios del propio código,
que remitían a un archivo que nadie escribió. Este documento cierra esa cita colgada.

---

## Resultado 1 — el contrato pedía una cosa y los launch hacían la contraria

El §3 de [`CONTRATO_INTERFACES.md`](../CONTRATO_INTERFACES.md), congelado el 2026-08-05, dice
literalmente:

> **Todos los marcos de cada robot llevan el prefijo del namespace, incluido `map`.**

Los tres launch prefijaban `odom` y `base_link` y dejaban `map` a secas, **y lo justificaban por
escrito**. El comentario de `deepracer_localization_sim.launch.py` decía:

> `'global_frame_id'` NO se toca: `'map'` lo publica el `map_server` y es el ancla común.

y el de `slam_toolbox.launch.py`:

> `'map_frame'` NO se prefija: es el ancla común […]. Cada robot vive en su propio
> `ROS_DOMAIN_ID`, así que dos `'map'` simultáneos no colisionan.

O sea que la desviación respecto al contrato no era un descuido: era una decisión razonada,
escrita en tres sitios, y equivocada.

---

## Resultado 2 — el fallo no da error en ningún lado

El nodo coordinador entró el mismo día (`a70f35d`, unas horas antes) y compone el objetivo
siguiendo el contrato —[`coordinador.py:257`](../../Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py):

```python
objetivo.pose.header.frame_id = f"{tramo.robot}/map"
```

Con los launch sin prefijar, ese marco **no existía en el árbol TF**. La cadena de síntomas:

1. El goal llega a `bt_navigator` con `frame_id: robot1/map`.
2. El planificador no puede transformarlo, porque su `global_frame` es `map`.
3. Nav2 no dice «marco desconocido»: entra en los comportamientos de recuperación.
4. Agotadas las recuperaciones, devuelve `ABORTED`.

En ningún punto de esa cadena aparece la palabra «marco». El único rastro es un vehículo que se
recupera en el sitio sin haber avanzado nunca.

Había además un segundo fallo silencioso, ese sin ningún síntoma: si el `map_server` sella su
`OccupancyGrid` con `frame_id: map` mientras el costmap global espera `robot1/map`, **la capa
estática se queda vacía y el costmap no protesta**. El robot navegaría sobre un mapa en blanco.

---

## Resultado 3 — «`map` es el ancla común» era falso por dos motivos

**No es un ancla común.** Son **dos mapas distintos con el mismo nombre**: el piso 1 y el piso 2,
geometrías diferentes, publicados por dos `map_server` independientes. El §3 es explícito en que
son dos árboles TF desconectados y en que **no hace falta** una transformada entre ellos, porque
ningún robot cruza de nivel (D2). Lo que nunca dijo el contrato es que se pudieran llamar igual.

**El aislamiento por dominio DDS es temporal.** El argumento de `slam_toolbox.launch.py` —«cada
robot vive en su propio `ROS_DOMAIN_ID`, así que dos `map` simultáneos no colisionan»— describe
correctamente la situación de hoy y la extrapola a una que no llega. El relevo del hito H3 exige
que los dos agentes compartan grafo; ese día habría dos `map_server` publicando el mismo nombre
de marco con geometrías distintas, que es exactamente el fallo silencioso que el §3 existe para
impedir.

Dicho de otro modo: el aislamiento por dominio no hacía correcto el marco sin prefijar, solo
**aplazaba la colisión** hasta el punto del proyecto donde más caro sale.

---

## Qué se cambió

| Archivo | Cambio |
|---|---|
| `deepracer_localization_sim.launch.py` | Añade `amcl…global_frame_id` y `map_server…frame_id` a `<ns>/map` |
| `deepracer_navigation_sim.launch.py` | Añade `bt_navigator…global_frame` y `global_costmap…global_frame` a `<ns>/map` |
| `slam_toolbox.launch.py` | Añade `slam_toolbox…map_frame` a `<ns>/map` |
| `scripts/evaluar_navegacion.py` | El marco del goal se **deduce** del namespace en vez de estar fijo en `'map'` |
| `nav2_robot1_view.rviz`, `robot1_completo.rviz`, `robot2_completo.rviz` | `Fixed Frame` → `robotN/map` |
| `herramientas/verificar_contrato.py` | La ausencia de `<ns>/map` pasa de aviso a **fallo** cuando hay `<ns>/odom` en el árbol |

Dos precisiones sobre el alcance:

- **Los YAML no se tocaron.** `nav2_params*.yaml` sigue diciendo `map` a secas, y está bien: ese
  es el caso sin namespace, donde el marco sin prefijo es el correcto. La reescritura ocurre en
  el launch y **solo si hay prefijo**.
- **El último cambio es el que importa a futuro.** `verificar_contrato.py` daba un `info`
  tranquilizador —«no existe `robot1/map` (normal si no hay AMCL/SLAM levantado)»— que se
  imprimía igual con AMCL levantada. La excusa tapaba el fallo. Ahora, si hay `<ns>/odom` en el
  árbol, la localización está publicando y la falta de `<ns>/map` es un fallo declarado.

---

## Verificación

La corrección se comprobó en la corrida del hito H3 del 2026-08-25
([`S20_hito_h3_dos_agentes.md`](S20_hito_h3_dos_agentes.md)): los dos objetivos se enviaron con
`frame_id: robot1/map` y `frame_id: robot2/map`, los dos se completaron, y las dos llegadas se
midieron contra `/odom` —0,281 m y 0,143 m— en vez de aceptarse por el `SUCCEEDED` de Nav2.

---

## Lo que no está respaldado por un registro

Los comentarios de los dos launch de navegación afirman que la misión abortada terminó **«tras un
`BackUp` de 0,41 m»**. Esa cifra **no tiene log en el repositorio**: no está en
`Documentos/Evidencia/logs/` ni quedó fila de bitácora ese día. Se anota aquí tal como se escribió
el 24-ago, y se marca como no verificable a posteriori.

Conviene además no confundirla con los **0,413 m** que aparecen el mismo día en la entrada de R12:
esos son el **error de posición** de una misión a ETM1 que Nav2 dio por `SUCCEEDED`, un suceso
distinto y posterior (`076af48`, después de esta corrección). La coincidencia de las dos primeras
cifras es solo eso.

---

## Qué queda abierto

- **El comentario de `slam_toolbox.launch.py` atribuye `robot1/map` al URDF** («porque así los
  publica el URDF»). El URDF publica `odom`, `base_link` y `laser`; `map` lo publica el propio
  `slam_toolbox` —o AMCL— y por eso hace falta el parámetro. La corrección es correcta; la razón
  escrita al lado, no del todo.
- **El caso que el cambio anticipa todavía no se ha probado:** los dos robots en un mismo dominio
  DDS. Mientras sigan aislados, ninguna corrida distingue entre el marco prefijado y el que no.
