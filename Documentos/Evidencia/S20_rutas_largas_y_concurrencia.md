# S20 — Rutas largas: robot2 en el piso 2, y la concurrencia medida a 90 m

**Fecha:** 2026-08-27, noche. **Código base:** `6961d89` más los arreglos de este mismo día.
**Cubre:** la primera medición de `robot2` con la configuración nueva, y la repetición del hito H3
sobre rutas veinte veces más largas que las suyas.

El hito H3 del 25-ago dejó dicho que dos pilas simultáneas no degradan la navegación. Lo dejó dicho
sobre trayectos de **1,67 m y 1,75 m**. Este informe repite la pregunta a **84 y 90 m**, que es la
escala de la campaña, y además cierra un hueco que se había abierto sin querer: los cambios de
configuración del 27-ago se habían medido solo en `robot1`.

---

## 1. Por qué `robot2` estaba sin medir, y por qué no era lo que parecía

La sospecha de partida era que las correcciones del 27-ago —`xy_goal_tolerance` de 0,25 a 0,15 y los
cinco `alpha` de AMCL de 0,2 a 0,01— se habían aplicado solo a `robot1`. **Es falso.**
`herramientas/robot.sh` lanza para los dos robots el mismo `nav_amcl_demo_sim.launch.py`, que carga
el mismo `nav2_params_nav_amcl_sim_demo.yaml`. Es un archivo único. Los valores nuevos estaban en
`robot2` desde el commit `b6808b0`.

Lo que sí faltaba era **medir** `robot2` con ellos. Sus dos únicas navegaciones medidas —24-ago,
0,190 m, y el hito H3 del 25-ago, 0,143 m— corrieron ambas con la configuración vieja y las dos
pasaron. Así que `robot2` no estaba roto, pero tampoco estaba comprobado.

La hipótesis que motivó la corrida era concreta y **resultó equivocada**: apretar la tolerancia de
parada a 0,15 m tenía que hacer daño justo en `piso2_escalera`, que es la peor aproximación del
sistema —de frente con `yaw = π` contra `Barrera_Escalera`, con el cono ciego de 60° del LiDAR
(R13) apuntando a la única superficie nueva del mapa— y que el 24-ago ya había frenado tarde,
parando a 1,344 m en vez de los 1,500 m declarados. Se esperaba que el vehículo se quedara corto y
que `SimpleProgressChecker` abortara el tramo. No pasó nada de eso.

## 2. Procedimiento

Tres misiones, todas de **condición A** —origen y destino en el mismo nivel, sin relevo—, cada una
con `gzserver` nuevo, compuerta de pre-misión y un bag por misión.

| | `S20_p2_01` | `S20_dos_01_robot1` | `S20_dos_01_robot2` |
|---|---|---|---|
| robot | robot2 | robot1 | robot2 |
| ruta | `piso2_aula_306` → `piso2_escalera` | `piso1_etm10` → `piso1_escalera` | `piso2_aula_306` → `piso2_escalera` |
| corrió | solo | **a la vez que robot2** | **a la vez que robot1** |
| recorrido real | 90,81 m | 83,86 m | 90,46 m |

Las rutas no se escogieron por comodidad. La de `robot1` es **la misma** que sus dos misiones largas
en solitario del 27-ago, así que cada robot repite una ruta de la que ya existe control. Las dos
terminan en el punto de transferencia de su piso, que es donde ocurriría el relevo.

Las dos metas de la corrida simultánea salieron **de una sola orden**, cada una con su
`ROS_DOMAIN_ID`, para que los vehículos se movieran a la vez y no uno detrás de otro. Es la receta
del hito H3.

Los dos coordinadores son **dos procesos distintos**, uno por dominio. Esto mide concurrencia, **no
mide el relevo**: el relevo necesita un solo coordinador que alcance a los dos robots, y eso sigue
bloqueado por la separación de dominios (§10 de `PROTOCOLO_EXPERIMENTAL.md`, séptimo prerrequisito).

## 3. Resultado 1 — `robot2` con la configuración nueva

| | control robot1 `rutas_03` | control robot1 `rutas_04` | **robot2 `p2_01`** |
|---|---|---|---|
| recorrido | 83,53 m | 84,52 m | **90,81 m** |
| error de llegada | 0,117 m | 0,129 m | **0,124 m** |
| tasa de deriva de AMCL | 0,0049 m/m | 0,0044 m/m | **0,0039 m/m** |
| peor error de AMCL | 0,407 m | 0,374 m | **0,353 m** |

`robot2` queda medido, y en la peor aproximación del sistema. En el instante de parada Nav2 se creía
a 0,121 m de la meta y estaba a 0,102 m: **0,020 m de error de localización**, la mejor cifra
registrada en el proyecto. La hipótesis del §1 queda descartada con medida.

### El error de AMCL en el piso 2 no crece de forma monótona

| recorrido | 0 m | 18,7 m | **37,1 m** | 53,3 m | 71,5 m | 90,4 m |
|---|---|---|---|---|---|---|
| error | 0,039 | 0,145 | **0,320** | 0,067 | 0,067 | 0,052 |

Sube hasta 0,320 m a mitad del pasillo largo y después **baja** hasta 0,052 m. En el piso 1 crecía y
no volvía. Todo el error sigue estando en X, que en el pasillo largo del piso 2 es la dirección
longitudinal, o sea la firma de R3 otra vez; pero la forma de **S** del piso 2 —canal oeste, tramo
norte-sur, pasillo largo, apéndice sur— devuelve geometría en los extremos y el filtro se vuelve a
anclar. Es lo que se había previsto antes de correr —que los `alpha` importan menos en el piso 2 que
en el tubo uniforme del piso 1— y ahora está medido.

## 4. Resultado 2 — la concurrencia a escala de campaña

**robot1, `piso1_etm10` → `piso1_escalera`**

| | solo (`rutas_03`) | solo (`rutas_04`) | concurrente |
|---|---|---|---|
| error de llegada | 0,117 m | 0,129 m | **0,151 m** |
| tasa de deriva | 0,0049 m/m | 0,0044 m/m | **0,0040 m/m** |
| peor error de AMCL | 0,407 m | 0,374 m | **0,338 m** |

**robot2, `piso2_aula_306` → `piso2_escalera`**

| | solo (`p2_01`) | concurrente |
|---|---|---|
| error de llegada | 0,124 m | **0,078 m** |
| tasa de deriva | 0,0039 m/m | **0,0023 m/m** |
| peor error de AMCL | 0,353 m | **0,204 m** |

Las cinco misiones cumplen el criterio del §3.3 —≤ 0,25 m contra `/odom`— y ninguna se acercó a
fallarlo. `robot2` mejora en las tres columnas; `robot1` empeora en la llegada final y mejora en
localización. **Con una corrida por condición eso no es una medida de efecto**, es variación entre
corridas, exactamente la misma reserva que ya se escribió para H3. Lo que sí queda descartada, ahora
a 90 m y no a 1,7 m, es la degradación gruesa.

### Un dato que parece concluyente y no lo es

`robot2` tardó **186,7 s** las dos veces, sola y concurrente, idéntico a la décima de segundo. La
lectura tentadora —«la concurrencia no cuesta nada»— es incorrecta. `tiempo_total_s` sale del reloj
de **simulación**, y el reloj de simulación se frena junto con el simulador: si dos `gzserver`
compiten por la CPU, el tiempo simulado no se entera, solo se estira el tiempo de pared. Dos
corridas idénticas en tiempo simulado prueban que **la trayectoria es determinista**, que ya es un
resultado útil, pero no dicen nada sobre contención.

La contención solo aparece en el **factor de tiempo real**, y ese número no se puede recuperar de un
bag sellado en tiempo de simulación.

## 5. Lo que queda abierto: el RTF bajo carga

No se muestreó el RTF **durante** la corrida. Lo que hay es la medición inmediatamente posterior,
con las dos pilas vivas pero **los dos vehículos parados**:

| | dominio 0 | dominio 2 |
|---|---|---|
| RTF, dos pilas en reposo | **0,993** | **0,994** |

Cumplen el RNF-06 (≥ 0,99) por tres y cuatro milésimas. Bajo carga de navegación puede caer por
debajo, y **no se sabe**. La comparación con el 0,996 medido el 25-ago no es limpia, porque aquella
también fue en reposo pero con una máquina en otro estado.

Consecuencia: **la pregunta de la concurrencia queda medio respondida.** La calidad de navegación no
se degrada a 90 m; el coste en reloj de pared sigue sin medir. Es la carencia nº 2 del registrador
—el RTF no se recupera de un bag— con consecuencia concreta por primera vez, y se cierra cuando
`grabar_mision.sh` escriba el `condiciones.json` previsto, que muestrea el RTF durante la corrida en
vez de deducirlo después.

## 6. Tres defectos encontrados por el camino

**(a) La compuerta de pre-misión se colgaba sin plazo.** `esperar_nav2.sh robot2` quedó **138 s**
detenida en `ros2 lifecycle get /robot2/controller_server`, mientras ese mismo comando respondía
`active` al instante desde otra terminal. Un cliente creado mientras el servidor levanta su servicio
puede no emparejar nunca, y `wait_for_service` no tiene plazo. La espera ocurría **dentro** de la
sustitución de comando, antes de la línea que evalúa el plazo de 120 s de la propia compuerta: por
eso no se rendía nunca. Corregido acotando cada llamada con `timeout`, que hace que la vuelta
siguiente del bucle —que ya existía— cree un cliente nuevo.

**(b) `diagnosticar_llegada.py` comparaba contra el spawn del otro robot.** El argumento `--spawn`
tenía como valor por defecto una constante con la pose de `robot1`, así que con `--robot robot2` la
pieza 1 acusó **15,868 m** de desvío en una corrida que había arrancado a **0,039 m** de su pose
declarada. Corregido leyendo la fila de `POSE_INICIAL` del robot pedido. Comprobado en los dos
robots.

**(c) El criterio de éxito y la tolerancia de parada dejaron de ser el mismo número, y la
documentación no se había enterado.** El §3.3 del protocolo justificaba los 0,25 m diciendo que eran
la `xy_goal_tolerance` de Nav2. Desde el 27-ago la tolerancia es 0,15. **El arreglo no era igualar
los números otra vez**, sino escribir por qué deben diferir: la tolerancia decide cuándo Nav2
**para**, contra lo que **cree** AMCL; el criterio decide cuándo la llegada se **acepta**, contra la
verdad de terreno. Igualarlos dejaba margen cero, y eso ya costó una llegada medida —parada
creyéndose a 0,240 m, estando a 0,297 m—. Bajar el criterio a 0,15 habría declarado fallida la
primera etapa de `S20_rutas_03`, que llegó a 0,204 m. Se corrigió la justificación del §3.3, la
tabla del §5 —donde `xy_goal_tolerance`, `yaw_goal_tolerance` y los `alpha` estaban obsoletos— y el
comentario de `coordinador.py:51`, dejando **el valor 0,25 intacto**.

## 7. La campaña de condición A empieza el 2026-08-27

La tabla de configuración congelada del §5 dice que si uno de sus valores cambia, las corridas
anteriores dejan de ser comparables con las posteriores. El 27-ago cambiaron tres. La consecuencia
se aplica sin excepción y ahora está escrita en el protocolo:

- **Control de la configuración vieja:** `S20_piloto_*`, `S20_rutas_01`, `S20_rutas_02`,
  `S20_localizacion`. Se conservan y se usan, pero solo como término de comparación —es contra ellos
  como se atribuye la mejora—.
- **Campaña:** `S20_rutas_03`, `S20_rutas_04`, `S20_p2_01`, `S20_dos_01_robot1`,
  `S20_dos_01_robot2`.

## 8. Una advertencia sobre la corrida `S20_p2_01`

La misión se lanzó **sin que la compuerta llegara a autorizarla**: estaba colgada por el defecto (a).
La corrida se acepta igualmente, y no por indulgencia, sino porque sus dos condiciones se comprueban
hacia atrás. Los parámetros no cambian en caliente y la compuerta los verificó al terminar —
`xy_goal_tolerance` 0,15 y los cinco `alpha` en 0,01—; y la condición inicial la mide el propio bag:
arrancó en (−21,891, −8,340) contra la declarada (−21,889, −8,379), **0,039 m**.

Queda anotado porque la próxima vez puede no salir bien, y entonces la corrida no valdrá.
