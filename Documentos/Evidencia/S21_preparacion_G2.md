# G2, tres días antes: lo que habría quemado la mañana del viernes

**S21 · 2026-09-01.** El G2 está en el cronograma para el **viernes 4 por la mañana**: una recta de
≥ 20 m sobre el vehículo, evaluada contra **M1 ≥ 0,90** (desplazamiento registrado ÷ real) y
**M2 ≤ 0,50 m** (error de `/amcl_pose` contra cinta). Es lo único que impide que el GO/NO-GO de S21
devuelva un **GO falso**.

Se revisó hoy, desde el escritorio, si esa mañana podía salir. **No podía.** Hay tres cosas, y
ninguna se habría visto hasta tener el carro montado y la cinta puesta.

---

## 1. Los bags del carro no se abren en este PC

La tarjeta corre **Jazzy**; el PC de análisis corre **Humble**. Un bag grabado allí falla aquí:

```
RuntimeError: Exception on parsing info file:
yaml-cpp: error at line 15, column 11: bad conversion
```

**No es culpa del `.mcap`**, que es autodescriptivo y no cambió. Es del `metadata.yaml` que lo
acompaña. Jazzy la escribe en **versión 9**, donde `offered_qos_profiles` es una secuencia YAML
anidada con los enums en texto (`reliable`, `volatile`); Humble espera ahí una **cadena** con el
YAML dentro y los enums como **enteros** de `rmw/types.h`. Su `yaml-cpp` intenta convertir secuencia
→ string y aborta. La «línea 15, columna 11» es exactamente el guion del primer elemento.

**Resuelto:** [`herramientas/adaptar_bag_jazzy.py`](../../herramientas/adaptar_bag_jazzy.py) traduce
la metadata y deja el bag adaptado en otra carpeta, con enlaces simbólicos a los `.mcap` originales
—la evidencia del carro no se toca ni se duplica—. 24 comprobaciones, incluida la conversión de la
metadata real del 28-ago. Rechaza en vez de adivinar en los dos casos que importan: un enum de QoS
fuera de tabla, y una metadata ya adaptada.

```
python3 herramientas/adaptar_bag_jazzy.py mapas/bag_mapa_1451 -o /tmp/g2_1451
```

## 2. Falta el plugin de almacenamiento, y esto sí necesita contraseña

Bloqueo **independiente** del anterior. Con la metadata ya arreglada, el error cambia:

```
[rosbag2_storage]: Could not load/open plugin with storage id 'mcap'
```

Humble no trae el lector de `mcap` de serie. El paquete existe en apt
(`0.15.16-1jammy`), pero pide `sudo`:

```
sudo apt install ros-humble-rosbag2-storage-mcap
```

**Hay que ejecutarlo antes del viernes.** Que el error del §1 desapareciera y saliera éste en su
lugar es la prueba de que los dos bloqueos son reales y de que el primero ya está quitado.

## 3. El mapa que M2 necesita no existe, y no se puede construir desde lo que hay

M2 mide `/amcl_pose`. AMCL necesita un **mapa del pasillo de ≥ 20 m**. En el repositorio solo hay
mapas de simulación (`mundo_definitivo_piso*`, `primer_piso*`); del pasillo físico no hay ninguno.

La materia prima serían los cinco bags del 28-ago. **No sirven**, y no solo por lo del §1:

| bag | duración | mensajes | tópicos |
|---|---|---|---|
| `bag_mapa_1445` | 57,9 s | 378 | `/rplidar_ros/scan` |
| `bag_mapa_1447` | 87,8 s | 575 | `/rplidar_ros/scan` |
| `bag_mapa_1450` | 5,1 s | 35 | `/rplidar_ros/scan` |
| `bag_mapa_1451` | 257,6 s | 1.703 | `/rplidar_ros/scan` |
| `bag_mapa_1456` | — | — | **sin `metadata.yaml`** |

**Un solo tópico en los cinco.** `slam_toolbox` necesita además la TF `odom → base_link` para
componer los barridos; sin `/tf` ni `/odom` no hay mapeo fuera de línea que valga. Y a
`bag_mapa_1456` le falta la metadata entera: eso está dentro del `.mcap` y recuperarlo exige el
lector del §2. No se le copia la de un bag hermano —los recuentos y los instantes serían de otra
corrida—, así que el guion se niega y lo dice.

**Consecuencia para el viernes: son DOS pasadas, no una.** Primero recorrer el pasillo con SLAM
vivo en el carro para producir el mapa; después, una segunda pasada con AMCL contra ese mapa,
grabando `/scan`, `/odom`, `/tf` y `/amcl_pose`. Planificarlo como una sola pasada es lo que
convierte la mañana en media jornada perdida.

---

## 4. Y además, los dos umbrales están mal puestos

Esto no es de logística, es del criterio. Evaluando M1 y M2 contra los números que el proyecto **ya
midió**:

| caso medido | ratio | M1 ≥ 0,90 | error a 20 m | M2 ≤ 0,50 m |
|---|---|---|---|---|
| carro, circuito de 18,4 m contra flexómetro | 1,029 | **PASA** | 0,58 m | FALLA |
| rf2o fuera de línea, tramo este (1,71 m de 29,94 m) | 0,943 | **PASA** | 1,14 m | FALLA |
| rf2o fuera de línea, tramo oeste (0,33 m de 24,98 m) | 0,987 | **PASA** | 0,26 m | PASA |

**M1 no puede fallar.** Su umbral de 0,90 tolera un 10 % de error y el peor jamás medido es 5,7 %.
Peor aún, está escrito **a un solo lado**: un ratio «≥ 0,90» no tiene cota superior, así que el
**+2,9 % largo** —que es el defecto real, el que motivó el hallazgo «repetibilidad no es
calibración» del 29-ago— pasa por definición, y pasaría igual a +50 %. Es exactamente la crítica
que el 26-ago se le hizo al GO/NO-GO original —*«calibrado para no verlo»*—, reaparecida en el
criterio que se escribió para corregirla.

*Corrección propuesta:* que sea de dos lados, **|registrado ÷ real − 1| ≤ 0,10**. Con eso el +2,9 %
sigue pasando, pero por margen y no por construcción, y un sesgo largo grande se vería.

**El resultado de M2 ya está determinado antes de correrlo.** Con el +2,9 % medido, 0,029 × 20 m =
**0,58 m > 0,50 m**, y R3 dice que en un pasillo uniforme el eje longitudinal no es observable, así
que AMCL no lo va a corregir. Una puerta cuyo resultado se calcula con los datos de la semana pasada
no está gateando nada.

*Pero conviene correrlo igual*, y no como puerta sino como **medida**: el pasillo real tiene marcos
de puerta, mobiliario y gente, y el propio `ESTADO.md` dice que el pasillo simulado es «más pobre
que el real», o sea que **5,7 % es un piso, no una estimación**. En simulación el piso 2, con forma
de S, hizo que AMCL se reanclara (0,320 m → 0,052 m). La pregunta abierta de verdad es cuánto
recupera AMCL con geometría real, y esa sí vale la mañana.

*Lo que queda por decidir, y es decisión de protocolo, no de código:* si M2 falla, **eso no dice
«parar»** — R3 ya está documentado y ya se decidió no construir la solución ahora. Hay que
reescribir sobre qué ramifica el GO/NO-GO antes de tener el número, no después. Enlaza con el
arrastre ya declarado *«verificación del mapa físico»*.

---

## 5. Lista de preparación, en orden

1. `sudo apt install ros-humble-rosbag2-storage-mcap` — **pide contraseña, hacerlo antes del jueves.**
2. Comprobar que abre: `python3 herramientas/adaptar_bag_jazzy.py mapas/bag_mapa_1451 -o /tmp/g2_1451 && ros2 bag info /tmp/g2_1451`
3. Decidir los umbrales del §4 **antes** de salir al pasillo. Fijarlos después de ver el dato es lo
   que el §6.3 del protocolo prohíbe.
4. Planificar la mañana como **dos pasadas**: mapa con SLAM, luego localización con AMCL.
5. En la segunda pasada grabar `/scan`, `/odom`, `/tf` y `/amcl_pose`. Los bags del 28-ago fallaron
   por grabar solo el primero.
