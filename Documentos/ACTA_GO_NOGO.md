# Acta del punto de decisión GO / NO-GO sobre el alcance de la demostración física

**Actividad 28 del cronograma · Responsables: ambos autores · Fecha: 2026-09-21 (S24)**

*Propuesta de los autores, para comunicar a los directores. Las decisiones del §6 no son nuestras.*

## 0. Por qué se resuelve hoy y no cuando se despeje

El cronograma situaba esta decisión en S21. Lleva tres semanas abierta, y no por olvido: en S21 el
ensayo G2 se cayó del calendario y en S22 se corrió pero **el pasillo no dio mapa**. Cada semana que
pasa la decide por omisión, y decidir por omisión es lo único que no se puede defender.

Su requisito previo formal —la actividad 27, navegación autónoma sobre un vehículo físico— **está
bloqueado**, y ese es precisamente el dato con el que hay que decidir. Esperar a que se desbloquee
para decidir el alcance invierte el orden: el alcance es lo que dice cuánto se invierte en
desbloquearlo.

## 1. La decisión

**GO pleno: la demostración física se intenta con los dos vehículos reales.**

El motivo no es optimismo sobre el calendario. Es que un intento con criterios de fallo escritos de
antemano produce evidencia en los dos desenlaces: si sale, es la demostración; si no sale, es una
caracterización medida de por qué esta plataforma no sostiene el protocolo, que es un resultado de
ingeniería y no una excusa.

**Lo que hace válida esa afirmación es el §4, no el §1.** Un fallo con criterio previo es un
resultado. Un fallo sin criterio previo es una anécdota que se redacta después de verlo, y el §3 de
[`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) lo prohíbe expresamente. Por eso esta acta
no se limita a decir «lo intentamos».

## 2. Lo que ya está en pie sobre hardware

Ninguna de estas filas es una expectativa; todas tienen fecha y artefacto.

| Pieza | Evidencia |
|---|---|
| Dos vehículos operativos, Ubuntu 24.04 + ROS 2 Jazzy, misma red | [`S24_desempate_camara_vehiculo.md`](Evidencia/S24_desempate_camara_vehiculo.md) §1 |
| LiDAR real publicando `/scan` usable, +23 mm de cota superior de error | [`S19_spike_p1_p2_hardware.md`](Evidencia/S19_spike_p1_p2_hardware.md) §1 |
| Mapa real del laboratorio, 8,45 × 6,90 m de contenido | [`S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md) §5 |
| `odom → base_link` con TF correcta en hardware, dentro de 1 mm | Tarea 1.1 del [`MAPA_TRABAJO_RESTANTE.md`](MAPA_TRABAJO_RESTANTE.md), 2026-09-21 |
| Latencia acotada entre los dos vehículos (RF-15) | [`REQUISITOS.md`](REQUISITOS.md), RF-15 ✅ |
| Un coordinador que alcanza a los dos robots | [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md), cerrado el 2026-08-30 |
| Control del vehículo desde ROS 2, sin la interfaz web del fabricante | [`S20_frente_b_hardware.md`](Evidencia/S20_frente_b_hardware.md) §6 |
| La tarjeta publica imagen (160 × 120, elevable a 640 × 480) | [`S24_desempate_camara_vehiculo.md`](Evidencia/S24_desempate_camara_vehiculo.md) §3 |

Y el resultado que la demostración física **no** tiene que volver a producir: el protocolo de relevo
entre niveles está ejecutado y medido **30 veces en simulación**, con **93,3 % de acierto** y
**continuidad entre niveles 14/14**. Ese es el aporte declarado del proyecto, y ya está sostenido.

## 3. Los dos bloqueos, medidos

### 3.1 No existe el peldaño de odometría, y el sitio que manda D3 lo impide

La cadena de Nav2 se sostiene en orden: TF, **odometría**, `/scan`, mapa, localización, costmaps,
planificador. El primer peldaño se cerró hoy. **El segundo no existe en hardware.**

Y no es un problema de ajuste. Está medido que **ninguno de los dos pisos del pasillo real contiene
la información de avance** que el estimador necesita:

| Recinto | Rayos informativos | Veredicto |
|---|---|---|
| Piso 1 del pasillo real | **5,1 %** | por debajo del que ya fracasó |
| Piso 2 del pasillo real | **5,9 %** | por debajo del que ya fracasó |
| Pasillo simulado cuyo mapa se rechazó | 6,8 % | referencia de fracaso |
| Caja cerrada de 7,70 × 2,70 m (simulada) | **13,8 %** | único mapa que el proyecto ha aceptado con SLAM |

Fuentes: [`S23_informacion_avance_piso1.md`](Evidencia/S23_informacion_avance_piso1.md) y
[`S23_informacion_avance_piso2.md`](Evidencia/S23_informacion_avance_piso2.md).

Esto choca de frente con **D3**, que sitúa la etapa 3 —la que produce la evidencia— en el pasillo
real de la USTA, y con **D4**, que descartó el laboratorio como entorno de evaluación por ser «16 m²
en un solo nivel, sin discontinuidad vertical». El conflicto es real y no lo resuelven los autores:
va al §6.

### 3.2 La cadena de actuación está bloqueada en uno de los dos vehículos

En el carro `.101` (`amss-jgm9`), `servo_pkg` dejó de atender tras una pérdida de potencia de
tracción y **no se recupera** con reinicio del servicio, reinicio del sistema ni reasiento de
batería, con el registro de systemd limpio. Documentado como anomalía abierta, no como diagnóstico,
en [`S24_actuacion_bloqueada_servo.md`](Evidencia/S24_actuacion_bloqueada_servo.md).

El carro `.102` (`amss-ez9n`) no se ha sometido a la misma prueba. **Ese es el desempate**: dice si
el bloqueo es de un vehículo o de la plataforma, y cuesta minutos.

### 3.3 Un tercer obstáculo que el GO pleno añade y el parcial no

Los remapeos del nodo de cámara son **absolutos**, no relativos. Envolver el lanzador en un
namespace por robot **no los mueve**, así que dos vehículos en el mismo grafo colisionan en los
mismos nombres de tópico. Resolverlo exige tocar esos remapeos o lanzar el nodo por cuenta propia
([`S24_desempate_camara_vehiculo.md`](Evidencia/S24_desempate_camara_vehiculo.md) §6). Los dos
vehículos comparten además `machine-id`, anotado como primera hipótesis si el descubrimiento entre
ellos falla de forma inexplicable.

## 4. Los criterios de fallo, escritos antes de correr

Esta es la parte que convierte un eventual fracaso en evidencia. **Ninguno de estos criterios se
modifica después de ver un resultado.** Cada uno se declara alcanzado o no alcanzado, con su
registro, y el conjunto se publica tal como quede.

| Hito | Criterio objetivo | Qué significa no alcanzarlo |
|---|---|---|
| **G-1 · Actuación** | El carro `.102` responde a `ServoCtrlMsg` moviendo las ruedas, y el `.101` se recupera o se diagnostica | Si fallan los dos: la plataforma no sostiene la demostración, y eso es el resultado |
| **G-2 · Odometría** | `odom → base_link` publica un desplazamiento con error ≤ 10 % sobre un recorrido conocido de ≥ 5 m, en el sitio que fije el §6 | El peldaño 2 no es construible con el sensor disponible en el tiempo disponible |
| **G-3 · Navegación de uno** | Un vehículo completa punto a punto con Nav2, llegada verificada contra `/odom` y no contra el `SUCCEEDED` de Nav2 | La navegación autónoma física no se alcanza; el protocolo no puede correr sobre hardware |
| **G-4 · Dos en el mismo grafo** | Los dos vehículos y el coordinador coexisten sin colisión de nombres, y el coordinador registra a los dos agentes | El GO pleno no es alcanzable; se revierte a un vehículo real |
| **G-5 · Protocolo completo** | Una misión con relevo de extremo a extremo sobre los dos vehículos, con su registro compuesto | La demostración física queda acotada a pruebas atómicas |
| **G-6 · RF-27** | N entre 5 y 10 repeticiones con registro, según D1 | La campaña física no alcanza N; se reporta lo corrido con su n real |

**La llegada se verifica contra `/odom`, nunca contra el `SUCCEEDED` de Nav2.** Nav2 ya declaró
éxito donde la odometría lo desmiente, y por eso el coordinador comprueba cada llegada por su cuenta.

**Los criterios de la campaña no se tocan**: el umbral de llegada de 0,25 m y el techo de descarte
del 20 % rigen tal como están escritos, y si parte de las corridas falla por construcción, eso se
reporta como resultado. Cambiarlos ahora sería mover el criterio después de conocer el problema.

## 5. Los puntos de corte, con fecha

Intentar el GO pleno sin fecha de reversión no es ambición: es quedarse sin semanas para escribir. La
ventana de sustentación es **S28–S29 (19 oct – 1 nov)**, y el documento final necesita las dos
semanas previas. Por tanto:

| Corte | Fecha | Condición | Si no se cumple |
|---|---|---|---|
| **C-0** | **Vie 25 sep** (S24) | G-1 alcanzado | Se abre el diagnóstico de plataforma como línea propia, y se replantea el alcance en S25 |
| **C-1** | **Vie 2 oct** (S25) | G-2 y G-3 alcanzados | Se revierte a **NO-GO**: RF-27 se declara no alcanzable y la evidencia queda en la campaña de simulación, con este acta como justificación |
| **C-2** | **Vie 9 oct** (S26) | G-4 alcanzado | Se revierte a **GO parcial**: **un solo vehículo real**, y el segundo piso queda cubierto por la campaña de simulación. RF-16 no se sostiene por esta vía |
| **C-3** | **Vie 16 oct** (S27) | G-5 y G-6 alcanzados | Se reporta lo corrido con su n real y se cierra la toma de datos, pase lo que pase |

**Después de C-3 no se toman más datos.** Lo que haya el 16 de octubre es lo que se defiende.

**Por qué el repliegue de C-2 no puede ser «uno real y uno simulado».** Una versión anterior de esta
fila lo proponía, y nuestra propia evidencia ya lo había refutado. R8 (medido el 2026-08-18) establece
que `nav2_msgs/NavigateToPose` cambia de definición entre Humble y Jazzy —en Humble el result es
`std_msgs/Empty`, en Jazzy lleva `error_code` y `error_msg`—, y ese es el único camino de mando del
`CONTRATO_INTERFACES.md`. Un coordinador en Humble no encuentra servidor en un robot Jazzy, y no lo
reporta: falla en silencio. El mismo código fuente sirve para los dos destinos, pero no a la vez. Es
la decisión D6: portabilidad de fuente, no interoperabilidad de grafo.

**Y por qué no se iguala la distro.** Se evaluó bajar los vehículos de Jazzy a Humble. No procede, por
tres razones verificadas: (a) `deepracer-custom-car` no publica objetivo 22.04 + Humble para la tarjeta
original `amd64` —su matriz APT lo marca «No», y solo ofrece flashear a 24.04 o el stack sobre un 20.04
existente—; (b) no sería un downgrade sino una reinstalación del sistema operativo, que destruiría el
estado ya medido en hardware (`/scan`, el mapa del laboratorio, el teleoperado por
`/ctrl_pkg/servo_msg`, `coordinacion_msgs` 19/19, RF-15 600/600); y (c) no toca ninguno de los dos
bloqueadores reales, G-1 y G-2, que son indiferentes a la distro. El camino inverso tampoco existe:
`gazebo_ros2_control` no está liberado para Jazzy, así que la simulación no puede subir.

## 6. Lo que no deciden los autores

Dos puntos que exceden esta acta y se llevan a los directores:

1. **El sitio de la etapa 3.** D3 lo fija en el pasillo real, y el §3.1 muestra medido que el
   pasillo no da la información de avance que la odometría necesita. O se cambia el sitio con la
   medición como justificación, o se acepta correr donde está medido que el estimador falla. **No se
   corre nada de la etapa 3 hasta que esto esté por escrito.**
2. **N = 5 o N = 10 en RF-27.** D1 deja el rango abierto. ASTM F3244-21 respalda numéricamente el 10
   —cero fallos en 10 repeticiones dan 80 % de fiabilidad con 85 % de confianza— y no respalda el 5.

## 7. Firmas

| | Nombre | Fecha |
|---|---|---|
| Autor | Santiago Hernández Ávila | |
| Autor | Jonny Mejía | |
| Comunicada a los directores el | | |

## 8. Trazabilidad

| Afirmación | Fuente |
|---|---|
| La decisión llevaba abierta desde S21 y por qué | `ESTADO.md` §de riesgos y bitácora; `PLAN_S22.md` |
| 5,1 % y 5,9 % de información de avance | `S23_informacion_avance_piso1.md`, `S23_informacion_avance_piso2.md` |
| 6,8 % del pasillo simulado rechazado, 13,8 % de la caja | §3.5 de `MAPA_TRABAJO_RESTANTE.md` |
| `servo_pkg` no se recupera en el `.101` | `S24_actuacion_bloqueada_servo.md` |
| Remapeos de cámara absolutos y `machine-id` compartido | `S24_desempate_camara_vehiculo.md` §1 y §6 |
| 30 misiones, 93,3 % de acierto, continuidad 14/14 | `REQUISITOS.md`, RF-07 y RF-24 |
| D1, D3 y D4 | `CRONOGRAMA_S17_S32.md` §4 |
| Umbral de llegada 0,25 m y techo de descarte 20 % | `PROTOCOLO_EXPERIMENTAL.md` |
| Fechas de S24 a S29 | `Actividad_1_Corte_1_Cronograma_2026-2.xlsx`, hoja `Cronograma` |
