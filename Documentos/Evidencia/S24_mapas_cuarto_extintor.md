# S24 · Los tres mapas del cuarto sobre hardware, y la medida que se sale del cuarto

**Fecha:** 2026-09-24 · **Vehículos:** `amss-jgm9` (`.101`) y `amss-ez9n` (`.102`)
**Origen:** los peldaños 4 y 5 de [`GUION_NAV2_HARDWARE.md`](../GUION_NAV2_HARDWARE.md), la primera
vez que la cadena `slam_toolbox` publica `/map` sobre el vehículo real.

## 1. Por qué existe este documento

El 24-sep se dieron por buenos los mapas del cuarto y **se escribió en `ESTADO.md` que el mapa del
extintor dibujaba «el cuarto cerrado de 3,50 × 1,20 m»**. Esa frase es falsa por dos motivos
distintos, y los dos importan:

1. **3,50 × 1,20 m es el tamaño del lienzo del PGM, no del cuarto.** El lienzo son 70 × 24 celdas a
   0,05 m. De esas 1680 celdas, **924 son desconocidas** —más de la mitad— y solo 498 son espacio
   libre. Medir un mapa por su lienzo es medir el papel, no el dibujo.
2. **El cuarto no sale cerrado.** Tiene una abertura en la pared izquierda y por ella se ve más
   espacio.

El defecto lo detectó el operador mirando la imagen: *«puedo ver una medida que se sale del
escenario de 1,60 m × 76 cm»*. Este documento mide lo que había que medir, y el resultado **no es
que el mapa esté mal**.

## 2. Qué se mide, y cómo

Las celdas de un mapa de `map_server` toman exactamente tres valores, y confundirlos fue el primer
error de este análisis:

| Valor | Significado |
|---|---|
| `0` | ocupado |
| `205` | **desconocido** |
| `254` | libre |

La primera pasada clasificó «mayor que 200» como libre, con lo que metió las 924 desconocidas
dentro del espacio libre y devolvió el lienzo entero. **La extensión de un mapa se mide sobre las
celdas `254`**, no sobre el lienzo ni sobre el umbral de una imagen.

## 3. Los tres mapas

| Archivo | Lienzo | Libre total | Veredicto |
|---|---|---|---|
| [`S24_mapa_cuarto_HARDWARE_derivado.png`](S24_mapa_cuarto_HARDWARE_derivado.png) | 85 × 57 | 3,95 × 2,40 m | **Inservible**, y sirve de control |
| [`S24_mapa_cuarto_HARDWARE.png`](S24_mapa_cuarto_HARDWARE.png) | 75 × 35 | 2,30 × 0,85 m | Limpio |
| [`S24_mapa_extintor_HARDWARE.png`](S24_mapa_extintor_HARDWARE.png) | 70 × 24 | 2,35 × 0,95 m | Limpio, con el obstáculo |

**El primero es basura y conviene conservarlo**, porque es el contraste que hace creíbles a los
otros dos: son trazos diagonales barridos, sin una sola pared recta ni un contorno cerrado, la
firma de una pose que deriva. **Así es como se ve un mapa que falló.** Los otros dos no se parecen
a eso en nada.

## 4. La medida que se sale, separada de la que no

Partiendo cada mapa limpio por la columna donde está la abertura:

| | Sala principal | Lóbulo izquierdo |
|---|---|---|
| `S24_mapa_cuarto_HARDWARE` | **1,50 × 0,80 m** | **0,80 × 0,40 m** |
| `S24_mapa_extintor_HARDWARE` | **1,60 × 0,95 m** | **0,75 × 0,35 m** |
| **Cuarto real, con flexómetro** | **1,60 × 0,76 m** | — |

**La sala principal está bien.** 1,50 y 1,60 m contra 1,60 m reales: dos celdas de error en el peor
caso, y cero en el mejor. El ancho da 0,80 y 0,95 contra 0,76: una celda en el primero, y en el
segundo el exceso no es la pared sino un bolsillo de celdas libres por debajo del muro inferior,
visible en el dibujo.

**Lo que se sale es el lóbulo**, y es lo que el operador vio: 1,60 + 0,75 = 2,35 m de extensión
total.

## 5. El lóbulo no es un error de SLAM, y esto es lo que lo demuestra

Es la parte que decide, así que conviene separar las dos hipótesis antes de elegir:

| Hipótesis | Qué predice |
|---|---|
| **(a) Deriva de SLAM** | La pared izquierda se duplica o se emborrona. El artefacto depende de la trayectoria, así que **cambia entre corridas** |
| **(b) Espacio real visto por una abertura** | Aparece una segunda cámara **con sus propias paredes arriba y abajo**, en el mismo sitio y del mismo tamaño en cualquier corrida |

Tres medidas separan las dos, y las tres apuntan a (b):

1. **El lóbulo se reproduce en dos corridas independientes con una celda de diferencia**: 0,80 ×
   0,40 m y 0,75 × 0,35 m. Una deriva no se repite así; depende de por dónde pasó el vehículo.
2. **El lóbulo tiene contorno propio y cerrado**, con muro arriba y abajo, no dos rayas paralelas
   sueltas. Una pared duplicada por deriva deja el hueco abierto por los extremos.
3. **Y la que más pesa: la sala principal no está estirada.** Si hubiera un error de escala o una
   deriva acumulada capaz de añadir 0,75 m, la sala se llevaría su parte y no mediría 1,60 m contra
   1,60 m reales. **El error está localizado fuera de la sala, no repartido**, y eso es
   incompatible con la deriva.

**Conclusión: el mapa es geométricamente sano. Lo que dice es que el cuarto no estaba cerrado** —
hay un vano en la pared izquierda, de unos 0,30 m de luz, y a través de él el LiDAR midió ~0,78 m
más de espacio.

> **Lo que falta para cerrarlo, y no se puede cerrar desde el escritorio.** Las tres medidas de
> arriba son consistentes con (b) pero **ninguna es una observación del vano**. La comprobación que
> zanja esto cuesta diez segundos y hay que hacerla en el sitio: **mirar si hay una abertura en esa
> pared** —una puerta entornada, un hueco bajo un mueble, la separación entre el muro y lo que
> tenga apoyado—. Si la hay, este documento queda confirmado y el cuarto real es de 1,60 × 0,76 m
> **más** lo que se vea por el vano. Si **no** la hay, entonces (b) es falsa, las tres medidas de
> arriba necesitan otra explicación, y el hallazgo pasa a ser mucho más grave de lo que parece
> ahora. **Hasta entonces esto es una hipótesis bien sostenida, no un hecho.**

## 6. El extintor sí quedó separado, que era la pregunta

En [`S24_mapa_extintor_HARDWARE.png`](S24_mapa_extintor_HARDWARE.png) hay una mancha ocupada de
**5 × 3 celdas = 0,25 × 0,15 m**, aislada en mitad del espacio libre y sin tocar ninguna pared. El
extintor mide unos 15–20 cm de diámetro, así que la mancha lo sobreestima en una celda por lado,
que es lo que hace el inflado de un mapa de ocupación.

**Eso contesta la pregunta con la que se hizo la pasada:** el sistema distingue un obstáculo suelto
del contorno del recinto, y no lo funde con la pared más cercana. Es el requisito mínimo para que
el `local_costmap` de Nav2 tenga algo que esquivar.

## 7. Qué queda en pie y qué no

| Afirmación | Estado |
|---|---|
| La cadena SLAM publica `/map` sobre hardware y `map → base_link` resuelve | **En pie.** Peldaños 4 y 5 |
| El mapa distingue un obstáculo aislado de las paredes | **En pie**, §6 |
| La sala mapea a 1,60 × 0,76 m reales con ≤ 2 celdas de error | **En pie**, §4 |
| «El mapa dibuja el cuarto cerrado de 3,50 × 1,20 m» | **Retirada.** Era el lienzo, y el cuarto no está cerrado |
| El espacio de más es un fallo de mapeo | **Retirada**, §5 |
| El espacio de más es un vano real en la pared izquierda | **Hipótesis sostenida por tres medidas, pendiente de comprobación física** |

## 8. Lección de método

**Un mapa no se mide por el tamaño de su imagen.** Más de la mitad de las celdas de un mapa de SLAM
son desconocidas, así que el lienzo siempre es mayor —aquí, más del doble en el eje largo— y
siempre parece confirmar que se mapeó mucho.

Y la segunda, que es la que costó: **«el mapa da más de la cuenta» no implica «el mapa está mal»**.
La pregunta útil no es cuánto se pasa, sino **dónde** se pasa. Repartido por toda la figura sería
escala o deriva; concentrado fuera de la sala y reproducible entre corridas es geometría que no
sabíamos que estaba ahí. Separar el exceso del resto antes de juzgarlo es lo que cambió el
veredicto de «mapa defectuoso» a «cuarto abierto».
