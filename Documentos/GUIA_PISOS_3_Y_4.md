# Guía del sitio nuevo: pisos 3 y 4

**Fecha:** 2026-10-02
**Para quién:** Santiago, que lleva las pruebas de campo. Escrita para poder
arrancar sin preguntarle nada a Jonny, que levantó el plano y ya no tiene acceso
al equipo donde se generó todo.

---

## 0. Qué hay, en una frase

Dos plantas del edificio levantadas con flexómetro, y de ese levantamiento salen
**el mundo de Gazebo y el mapa de navegación a la vez**, de modo que simulación y
edificio coinciden porque vienen de la misma fuente.

| | Oeste | Este | Cierre | |
|---|---|---|---|---|
| **Piso 4** | 25,615 m | 25,534 m | 8 cm | **0,32 %** |
| **Piso 3** | 25,345 m | 25,504 m | 16 cm | **0,62 %** |

El criterio es ±2 %. Para comparar, el modelo del piso 2 tenía un **20 %** de
error en el ancho del hall, y ahí es donde AMCL acumulaba 2,62 m el 30-sep.

---

## 1. Por qué existe este sitio

La sesión del 30-sep midió el hall del piso 2 y el modelo lo daba 0,84 m más
ancho de lo que es: 4,24 m contra 3,40 m. El §10 de
[`ENTORNO_DE_EVALUACION.md`](ENTORNO_DE_EVALUACION.md) ya declaraba que la
correspondencia entre el modelo y el edificio era *«un supuesto no verificado»*,
y al verificar **una sola** medida resultó falsa. Las demás nunca se comprobaron.

Estos dos pisos invierten el orden: primero se mide, después se modela.

---

## 2. Los archivos

| Qué | Dónde |
|---|---|
| Mundos de Gazebo | `piso3.world`, `piso4.world` |
| Modelos | `piso3/model.sdf`, `piso4/model.sdf` |
| **Mapas de navegación** | `Robot/aws-deepracer/deepracer_bringup/maps/piso{3,4}.{pgm,yaml}` |
| **Catálogo de destinos** | `Robot/aws-deepracer/deepracer_bringup/config/puntos_interes_pisos34.yaml` |
| Generador | `herramientas/generar_piso_desde_medidas.py` |
| Mapas anotados | `Documentos/Evidencia/S25_mapa_piso{3,4}_anotado.png` |

### Para regenerar, si hace falta corregir una medida

Las medidas están en una tabla al principio del generador, una por planta. Se
cambia el número y:

```bash
python3 herramientas/generar_piso_desde_medidas.py piso4
python3 herramientas/generar_mapa_desde_mundo.py simulacion/piso4.world \
        Robot/aws-deepracer/deepracer_bringup/maps/piso4.yaml --semilla 5.0 1.2
```

El generador **avisa solo si las dos paredes no cierran** dentro del 2 %. Esa
comprobación encontró cinco errores antes de generar nada: tres de lectura del
plano y dos de modelado.

> La semilla `5.0 1.2` es un punto dentro del pasillo. Sin ella el relleno
> arranca en (0,0), que cae sobre el muro oeste.

> El generador escribe `piso4.yaml.pgm` y `piso4.yaml.yaml`; hay que renombrarlos
> a `piso4.pgm` / `piso4.yaml` y corregir la línea `image:` del yaml.

---

## 3. Los diez destinos

Las poses **no salen de la geometría teórica sino del mapa ya generado**: para
cada vano se busca el bloque libre contiguo de esa abscisa y la parada se coloca
en su centro, desplazada 0,35 m hacia la pared del destino.

Las diez se comprobaron contra el mapa: **todas en celda libre**, con 0,60 a
0,96 m al muro más cercano, o sea por encima del radio de inflación (0,55) y del
de giro (0,35). **Ninguna debería dar `"Start occupied"`.**

| Piso 3 | x | y | | Piso 4 | x | y |
|---|---|---|---|---|---|---|
| Salón 301 | 6,20 | 2,00 | | Salón 401 | 6,20 | 2,03 |
| Salón 302 | 9,31 | 2,21 | | Salón 402 | 9,31 | 2,15 |
| Ascensor | 16,54 | 1,30 | | Ascensor | 16,39 | 1,36 |
| Salón 303 | 17,22 | 2,00 | | Salón 403 | 17,22 | 2,06 |
| **Escaleras** | 22,10 | 0,64 | | **Escaleras** | 24,39 | 0,82 |

El eje x corre a lo largo del pasillo del extremo norte (x = 0) al sur; el eje y
lo cruza, con la pared oeste en y = 0. Los salones están al este; ascensor y
escalera, al oeste. **El yaw va a 0 en todas**, alineado con el pasillo, porque
el vehículo no gira sobre su eje.

---

## 4. Una prueba de navegación, paso a paso

### 4.1 · Llevar los mapas al vehículo

```bash
scp Robot/aws-deepracer/deepracer_bringup/maps/piso4.pgm \
    Robot/aws-deepracer/deepracer_bringup/maps/piso4.yaml \
    Robot/aws-deepracer/deepracer_bringup/maps/piso3.pgm \
    Robot/aws-deepracer/deepracer_bringup/maps/piso3.yaml \
    deepracer@<IP>:~/tesis/
```

### 4.2 · Arrancar la cadena

```bash
CARRO=<IP> MAPA=/home/deepracer/tesis/piso4.yaml POSE_X=24.45 POSE_Y=1.21 POSE_YAW=3.1416 ESCALA=<escala> bash herramientas/nav2_mapa_guardado.sh   # ruta fija del vehiculo
```

**`ESCALA` va siempre, y es distinta en cada vehículo:** `1.0` en racey (`amss-jgm9`) y `0.85` en
deepy (`amss-ez9n`). El guion pone `0.9` si no se le dice nada, y con `0.9` racey no arranca sin
empujarlo y deepy llega a 1,58 m/s (2-oct, conclusión 3 de
[`S25_pisos34_campo.md`](Evidencia/S25_pisos34_campo.md)). *Esta orden no llevaba `ESCALA` hasta el
6-oct: escrita el 2-oct, es anterior a que se midiera la escala de cada vehículo.*

Para una misión **coordinada** (con el coordinador y el relevo) hacen falta además `NS=robot1` o
`NS=robot2`, `IMU=true` y `MARGEN=0.5`; las órdenes completas están en
[`PLAN_S26.md`](historial/PLAN_S26.md) §4.2.

`POSE_X`, `POSE_Y` y `POSE_YAW` son la salida del vehículo y hay que pasarlas siempre: sin ellas el
guion pone (1,0, 0,0), que en los mapas de los pisos 3 y 4 cae sobre la pared oeste. La salida
usada el 2 de octubre en el piso 4 es la de arriba: frente a las escaleras, con el centro del
vehículo a 1,00 m de la pared sur y a 1,25 m de la pared este, mirando al norte (yaw π). En el piso
3 la equivalente es (22,10, 1,06). `POSE_YAW` existe desde el 2 de octubre; sin él, AMCL arranca
mirando a +x.

Ese guion impone el orden que costó la noche del 24-sep: puente, escala,
`map_server` **activo**, AMCL, y solo entonces el launch de Nav2. Al revés, la
capa estática del costmap queda vacía y el planificador aborta con
**`"Start occupied"`** en cualquier meta, apuntando al punto de partida en vez de
a la causa. No manda la meta a propósito.

### 4.3 · Probar el plan SIN mover el vehículo

**Esto es lo que más tiempo ahorra.** Separa «el planificador no puede» de «el
controlador no mueve», sin arriesgar el carro:

```bash
ssh deepracer@<IP> "sudo -n bash -s" <<'EOF'
export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml
source /opt/ros/jazzy/setup.bash && source ~deepracer/nav_ws/install/setup.bash
ros2 action send_goal /compute_path_to_pose nav2_msgs/action/ComputePathToPose \
  "{goal: {header: {frame_id: map}, pose: {position: {x: 17.22, y: 2.06, z: 0.0}, \
  orientation: {w: 1.0}}}, use_start: false}"
EOF
```

`SUCCEEDED` = el planificador puede. `ABORTED` = mirar el log del
`planner_server`, que dice por qué. Sin el perfil de la partición la orden no encuentra el servidor
de Nav2, y con `use_start: false` parte de la pose de AMCL, así que va después del §4.2.

### 4.4 · La meta de verdad

Grabar primero, y mandar la meta mirando el vehículo. Comandos completos en la
salida del guion del §4.2.

---

## 5. Lo que hay que vigilar

### 5.1 · El tramo estrecho

El pasillo del piso 4 baja a **2,16 m** en su parte más estrecha. Con
`inflation_radius: 0.55` quedan **1,06 m** de banda central: el vehículo cabe,
pero sin holgura.

**Si `compute_path_to_pose` aborta ahí, no es el mapa: es la inflación
estrangulando el corredor.** Se baja a 0,35 y se vuelve a probar — pero conviene
anotarlo, porque cambiar la inflación cambia cómo esquiva obstáculos.

### 5.2 · El error de llegada va a salir alto

El vehículo no se mueve por debajo de 0,40 m/s, así que se aproxima a la meta a 0,40 y no tiene
régimen de aproximación fina (§2 de
[`S24_nav2_navegacion_mapa_guardado.md`](Evidencia/S24_nav2_navegacion_mapa_guardado.md)). Desde el
30 de septiembre el lanzador da la meta por alcanzada a 1,0 m para que el vehículo no retroceda
buscándola, y el puente sube las órdenes por debajo de 0,40 m/s a su escalón más bajo. Con ese margen
Nav2 puede parar hasta 1 m antes: el 2 de octubre las dos llegadas medidas quedaron 0,49 m y 0,57 m
cortas ([`S25_pisos34_campo.md`](Evidencia/S25_pisos34_campo.md)). G-3 se mide con flexómetro contra
0,5 m.

Desde el 5-oct el margen ya no está fijo en el lanzador: es el argumento `margen_llegada`, que en el
guion se pasa como `MARGEN=`, con 1,0 m por defecto. **Las misiones coordinadas necesitan
`MARGEN=0.5`**: el coordinador acepta la llegada a 0,5 m o menos, así que con 1,0 m una llegada entre
0,5 y 1,0 m se rechaza y la misión falla ([`PLAN_S26.md`](historial/PLAN_S26.md) §4.1). Si la IMU permite bajar
el margen a 0,5 m se decide con las misiones encadenadas del miércoles 7 (§3.2 del plan).

**Anotar el error de cada corrida, no intentar arreglarlo en campo.**

### 5.3 · La capa de obstáculos

Comprobar que escucha `/rplidar_ros/scan` y no `scan`. Es condición de
seguridad: sin ella el vehículo no ve obstáculos nuevos.

---

## 6. Lo que falta, y es decisión de los dos

### 6.1 · El relevo entre los pisos 3 y 4 no puede correr todavía

> **Resuelto el 2026-10-05.** El equipo aprobó los dos cambios y están en el coordinador: los
> parámetros `robot_nivel_3` y `robot_nivel_4`, vacíos por defecto para que la simulación no cambie,
> y la opción B, con la que en el vehículo la llegada se juzga con la pose en el mapa que publica el
> agente, porque `/odom` arranca en (0, 0). Detalle y pruebas en [`PLAN_S26.md`](historial/PLAN_S26.md) §4.1;
> las órdenes para lanzarlo en los vehículos, en el §4.2. Lo que sigue se deja como se escribió el
> 2-oct, porque explica por qué hacía falta.

`coordinador.py` declara `robot_nivel_1` y `robot_nivel_2`, y nada más (líneas
98-99 y 109-112). Con el catálogo de los pisos 3 y 4 **no encuentra robot para
esos niveles** y la misión no planifica.

Se comprobó: con la asignación `{3: robot1, 4: robot2}` pasada a mano, las **90
combinaciones planifican y ninguna falla**, y el plan de relevo sale correcto
—incluido el «Suba al piso 4» que distingue el sentido—. O sea que el
planificador está bien; lo que falta son dos parámetros en el coordinador.

**Son cuatro líneas, pero tocan fichero de Santi con el código congelado desde el
18-sep.** Por eso no se hizo: se acuerda primero.

Para una prueba de navegación de un solo piso **no hace falta nada de esto**.

### 6.2 · Por qué el catálogo va aparte

Se intentó meter los pisos 3 y 4 en `puntos_interes.yaml` y la prueba del
planificador lo rechazó en el acto: **710 de 930 combinaciones fallaban**. La
causa no es el catálogo sino que hay dos robots y cuatro niveles piden cuatro.
Separarlos evita además poder pedir una misión del piso 1 a un salón del piso 4,
que no existe como recorrido.

### 6.3 · El ascensor es destino, no transferencia

El robot guía **hasta** el ascensor, pero el cambio de piso va siempre por la
escalera. Marcarlo como segundo punto de transferencia haría fallar a
`_transferencia_de()`, que exige exactamente uno por nivel. Su propio comentario
dice que ahí es donde habría que decidir cuál —«presumiblemente la más cercana al
punto anterior»— y eso es tocar el núcleo del aporte declarado. **Queda para
trabajos futuros**, donde encaja bien porque el código ya nombra la decisión.

---

## 7. Una lección del levantamiento, para la próxima planta

El piso 3 quedó con 90 cm de descuadre y la sospecha recayó sobre los lockers,
porque 9,10 m contra los 3,00 m del piso 4 era el valor más raro, y bajarlos a
8,20 cerraba al milímetro. **Era falso.** Los números estaban todos bien; lo que
estaba mal era la interpretación de dos de ellos: una cota de 0,39 m que es
ensanche y no largo, y otra de 0,70 m que es profundidad de un saliente y no su
largo.

**En un plano a mano no se distingue si una cota va a lo largo o a lo ancho**, y
esa ambigüedad cuesta más que un número mal leído: produce un descuadre que
parece de medida y manda a remedir lo que estaba bien. Conviene anotarlo en el
propio plano.
