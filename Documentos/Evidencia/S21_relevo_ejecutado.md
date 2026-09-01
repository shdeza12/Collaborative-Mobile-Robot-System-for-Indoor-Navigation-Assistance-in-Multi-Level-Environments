# El relevo entre pisos, ejecutado — el aporte declarado deja de ser un plan

**S21 · 2026-08-30.** Una misión de dos niveles se completó de extremo a extremo con **dos robots
vivos y un relevo entre ellos**, en un solo PC. Es el resultado central del proyecto y hasta hoy
existía solo como función pura probada sin simulador.

Cierra el **hito 5** y desbloquea la **condición B** del protocolo, que es la mitad de la campaña de
OE4.

Bag: `S21_dominio_unico_001` (53,3 MiB, fuera del repositorio por tamaño).
Lo que lo hizo posible: [`S21_bloqueo_dominios.md`](S21_bloqueo_dominios.md).

---

## 1. La misión

`piso1_representacion` → `piso2_lab_313`. Origen en el nivel 1, destino en el nivel 2, luego el
planificador tiene que partirla en dos y meter un relevo en el punto de transferencia.

| | |
|---|---|
| Resultado | `exito: true` |
| Relevos | **1** |
| Duración | 47,6 s |
| Etapas | `RECIBIDA` → `TRAMO_1` → `TRAMO_1` → `TRANSFERENCIA` → `TRAMO_2` → `COMPLETADA` |

**Las llegadas se juzgan contra `/odom`, nunca contra el `SUCCEEDED` de Nav2** —regla del 12-ago, y
la razón de que exista R12—:

| | recorrido | error de llegada | criterio |
|---|---|---|---|
| `robot1` (nivel 1) | 1,45 m | **0,128 m** | 0,25 m |
| `robot2` (nivel 2) | 9,63 m | **0,077 m** | 0,25 m |

Las dos dentro, y la del piso 2 con holgura de 3×. El tramo del `robot1` es corto porque el origen
sorteado cae cerca del punto de transferencia; eso no lo invalida, pero sí conviene decirlo antes de
que alguien lea 1,45 m como si fuera una travesía.

## 2. Que las dos pilas convivieran no es una impresión, es un conteo

El bag lleva **54.322 mensajes en 16 tópicos** a lo largo de 333,2 s.

| Tópico | Mensajes | Qué prueba |
|---|---|---|
| `/clock` | 3.332 | el reloj de referencia, el de `robot1` |
| `/robot2/clock` | **3.324** | **el modo de fallo del 26-ago, cerrado** |
| `/tf` | 29.666 | las dos pilas publican al mismo tópico |
| `/robot1/odom` · `/robot2/odom` | 4.971 · 4.961 | las dos pilas vivas todo el rato |
| `/robot1/cmd_vel` · `/robot2/cmd_vel` | 373 · **580** | **los dos robots recibieron mando** |
| `/robot1/plan` · `/robot2/plan` | 19 · 29 | los dos Nav2 planificaron de verdad |
| `/coordinacion/estado_mision` | 339 | el coordinador alcanzó a los dos |

Dos cifras merecen el detalle:

**`/robot2/clock` con 3.324 mensajes.** El 26-ago un intento parecido produjo un bag con **cero**
mensajes y sin ningún error, porque `ros2 bag record --use-sim-time` está cableado a `/clock` y
rechaza `--ros-args`. De ahí sale el diseño asimétrico de relojes del §5.3 del documento de
dominios. Que aquí haya 3.324 es la comprobación de que la asimetría funciona.

**580 mensajes en `/robot2/cmd_vel`.** Es lo que distingue «hubo un relevo» de «el coordinador dijo
que hubo un relevo». El segundo robot no fue notificado: fue conducido.

### 2.1 Los dos árboles TF comparten `/tf` sin colisionar

La preocupación desde el 24-ago era que dos árboles en un mismo tópico se pisaran, empezando por
`map`. Se midió sobre el bag entero: de **94.981 transformadas**, las que tienen marco hijo **sin
prefijo son 0**. No «no se observaron problemas»: cero, contadas.

### 2.2 RTF 0,9981, y contradice una medida anterior

`rtf.json` del bag: **RTF 0,9981** (335,5 s de simulación en 336,128 s de pared), medido con marcas
de `/clock` alrededor de la grabación. Cumple RNF-06, que pide ≥ 0,99, **con las dos pilas completas
y los dos Nav2 arriba**.

Esto **choca con la medida del 26-ago**, que dio 0,955 y 0,811 con las dos pilas en un portátil y
sirvió de argumento para repartir los robots en dos máquinas. Las dos medidas no se han conciliado.
La sospecha razonable es que la de agosto llevaba la **GUI de Gazebo** abierta y ésta no, pero
**nadie lo anotó en ninguna de las dos**, así que es una sospecha y no un hallazgo. Hasta repetirlo
declarando la GUI, ninguna de las dos cifras justifica una decisión de despliegue. Queda anotado en
el comentario de `DOMINIO_FORZADO` de `herramientas/robot.sh`.

## 3. El desfase entre simuladores no es constante

Los dos `gzserver` arrancan por separado, así que sus relojes no coinciden. En esta corrida el
desfase fue de **4,20 s**; en una anterior fue de **143 s**. Depende del orden y del retraso de
arranque, nada más.

Se propaga tal cual a los sellos de las cabeceras de `/tf`, y por eso los avisos `TF_OLD_DATA`
aparecen **solo cuando el desfase es grande**: con 143 s salieron, con 4,20 s no salió ninguno. Es
decir, **la ausencia de avisos no es señal de que el problema no exista** — es señal de que hoy
arrancaron seguidos. Quien vea `TF_OLD_DATA` en una corrida futura debería mirar el desfase antes
que cualquier otra cosa.

## 4. Lo que esta corrida NO demuestra

Se dice explícitamente para que nadie la cite de más:

1. **Es UNA corrida, no una campaña.** El protocolo pide **N = 30 con sorteo por semilla**. Esto es
   n = 1 y sin sortear. No sostiene ninguna afirmación sobre *tasa de éxito*.
2. ~~**No hay registro compuesto de esta misión.**~~ **Resuelto el 2026-09-01.** El registro está en
   [`registros/S21_dominio_unico_001.json`](registros/S21_dominio_unico_001.json), validado contra
   el esquema 1.1.0. Sigue siendo n = 1 y sin sortear —lo de arriba manda—, pero ya está en el
   formato que la campaña agrega. Componerlo destapó dos defectos del compositor, los dos
   arreglados antes de escribirlo:

   - **RF-24 salía `continua: false` en una misión que nunca perdió la custodia.** `continuidad_de()`
     recortaba la ventana comparando tiempos para excluir el `RECIBIDA` de agente vacío, y aquí
     `RECIBIDA` y `TRAMO_1` comparten sello —los dos en t=402,400— porque `/clock` va a 10 Hz y la
     asignación tarda microsegundos. Como eso pasa en toda misión, RF-24 habría dado 0 % de
     continuidad por construcción: el mismo defecto estructural del punto 3, por otra vía. Ahora la
     ventana se recorta por posición en la secuencia, no por tiempo.
   - **La procedencia guardaba media escena.** Desde el 23-ago el mundo es del nivel, así que una
     condición B usa dos mundos y dos mapas, y `procedencia.mundo`/`.mapa` son cadenas sueltas. Se
     añadió `escenario_por_robot` al esquema —opcional, para no invalidar lo ya compuesto— y el
     compositor lo deriva de los robots que corrieron en vez de pedirlo por bandera.
3. **El tiempo de asignación de esta corrida no vale**, y no por esta corrida: todo sello del bag
   está cuantizado a 100 ms y la asignación tarda ~0,17 ms. Los seis intervalos entre marcas de esta
   misión son múltiplos exactos de 0,1 s, lo que lo confirma. La cifra sale del banco, no de aquí
   ([`S21_banco_tiempo_asignacion.md`](S21_banco_tiempo_asignacion.md)).
4. **Nada de esto se ha probado en el carro físico.** Es un PC con Humble. La tarjeta del vehículo
   corre Jazzy y todavía no tiene `coordinacion_msgs` compilado.
5. **El tramo del `robot1` fue de 1,45 m.** Un relevo con los dos tramos largos sigue sin verse.

## 5. Cómo se reproduce

Con el workspace compilado y **sin exportar ningún dominio** —ése es el punto: el 0 es el defecto de
ROS 2, así que cualquier terminal ve la misión entera—:

```
herramientas/robot.sh robot1 nav2
herramientas/robot.sh robot2 nav2
herramientas/grabar_mision.sh S21_dominio_unico_001
ros2 action send_goal /coordinacion/guiar_usuario coordinacion_msgs/action/GuiarUsuario "{origen_id: 'piso1_representacion', destino_id: 'piso2_lab_313'}"
```

**Antes de medir nada, comprobar la pose inicial de los dos robots.** Las pilas van derivando ~17 mm
por minuto en reposo, y esta corrida empezó contaminada —0,535 m y 0,745 m de error inicial— hasta
que se relanzaron las dos, que las dejó en 0,020 m. Medir sobre una pose contaminada da un error de
llegada que no es del sistema, es del tiempo que el simulador llevaba encendido.
