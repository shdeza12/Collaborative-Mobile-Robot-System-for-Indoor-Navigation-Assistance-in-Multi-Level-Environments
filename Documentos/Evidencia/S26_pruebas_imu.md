# Pruebas de la IMU en los dos vehículos (5 de octubre)

Registro de las siete pruebas de [`PRUEBAS_IMU.md`](../PRUEBAS_IMU.md) sobre la IMU de la tarjeta de
`amss-ez9n` (deepy) y de `amss-jgm9` (racey), con
[`herramientas/probar_imu.py`](../../herramientas/probar_imu.py), que lee el sensor por el bus I2C sin
instalar nada. Las corrió Santiago desde el portátil, por SSH, con cada vehículo sobre el suelo y las
ruedas quietas; Claude preparó las pruebas y analizó las salidas.

## Resultado

Los dos vehículos tienen la misma IMU y funciona: una Bosch BMI160 en el bus I2C 1, dirección 0x68,
integrada en la tarjeta (Pegatron, modelo «AWS DeepRacer», BIOS 0.0.8 del 14 de marzo de 2019,
procesador Intel Atom E3930). En los dos, el giroscopio midió giros de 90° y 360° hechos a mano con
un error de 0,1 % a 1,3 %, y quieto no se desvió más de 0,3° en 60 s una vez restado el sesgo medido
justo antes. Los dos sensores van montados con la misma orientación.

De los criterios, solo uno no se cumple: el módulo de la aceleración en reposo de `amss-jgm9`,
10,268 m/s², por encima del límite de 10,11 m/s². Es un desfase del acelerómetro en el eje vertical,
que no afecta al giroscopio ni al uso previsto de la IMU (§5).

## 1. Resultados

| # | Prueba | `amss-ez9n` | `amss-jgm9` | Criterio |
|---|---|---|---|---|
| 1 | Identidad | `0xd1`, `ERR_REG 0x00`, ±2 g, ±2000 °/s | igual | `0xd1` y sin errores |
| 2 | Despertar | `PMU_STATUS 0x14` | `0x14` | los dos en modo normal |
| 3 | Reposo: muestras | 2683 en 30 s (89/s), ninguna repetida | 2687 (90/s), ninguna repetida | 40/s o más |
| 3 | Reposo: módulo de la aceleración | 10,008 m/s² | **10,268 m/s²** | 9,81 ± 0,3 m/s² |
| 3 | Reposo: giroscopio, media (x, y, z) | 1,224 · −0,294 · 0,648 °/s | −0,505 · −0,637 · 0,464 °/s | menor de 3 °/s |
| 3 | Reposo: giroscopio, desviación (x, y, z) | 0,154 · 0,187 · 0,056 °/s | 0,096 · 0,103 · 0,052 °/s | menor de 0,3 °/s |
| 3 | Reposo: temperatura | 29,1 °C | 24,3 °C | 20 a 50 °C |
| 4 | Inclinar | nariz arriba: y a unos +5,3; costado derecho arriba: x a −4,2 | nariz arriba: y a +3,6; costado derecho arriba: x a −4,3 | cambian los ejes horizontales |
| 5 | 90° a la izquierda | z = −89,6° | z = −90,1° | −90° ± 5° |
| 6a | 90° a la derecha | z = +89,8° | z = +91,2° | +90° ± 5° |
| 6b | Vuelta completa a la izquierda | z = −358,6° | z = −360,8° | −360° ± 10° |
| 7 | Deriva, 60 s quieto | z = 0,0° | z = −0,3° | menos de 5° |

En `amss-ez9n` cumplen las siete pruebas. En `amss-jgm9` cumplen todas salvo el módulo de la
aceleración de la prueba 3.

## 2. Orientación del sensor

Igual en los dos vehículos:

| Eje del sensor | Apunta hacia | Evidencia |
|---|---|---|
| x | la izquierda | Con el costado derecho arriba, x baja a unos −4,2 m/s² |
| y | adelante | Con la nariz arriba, y sube a unos +3,6 a +5,3 m/s² |
| z | abajo | En reposo, z marca entre −9,99 y −10,26 m/s² |

Para la URDF, el marco de la IMU está girado 180° en roll y 90° en yaw respecto a `base_link`
(`rpy="3.1416 0 1.5708"`). Un giro del vehículo a la izquierda sale negativo en el giroscopio z.

En reposo, x e y no marcan cero (0,35 y 0,42 m/s² en `amss-ez9n`; 0,31 y −0,27 en `amss-jgm9`): el
sensor está unos 2° a 3° fuera de la vertical, por el suelo, el montaje o el desfase del sensor. Por
eso, al girar sobre la vertical, una parte del giro aparece en x e y: de 3° a 20° en las pruebas 5 y
6, más cuanto más se bambolea el vehículo al girarlo a mano. En z no tiene efecto apreciable.

## 3. Sesgo del giroscopio

| Vehículo | Corrida | x | y | z |
|---|---|---|---|---|
| `amss-ez9n` | Prueba 5 | 1,215 | −0,310 | 0,656 |
| `amss-ez9n` | Prueba 6a | 1,224 | −0,283 | 0,649 |
| `amss-ez9n` | Prueba 6b | 1,248 | −0,285 | 0,649 |
| `amss-ez9n` | Prueba 7 | 1,239 | −0,290 | 0,652 |
| `amss-jgm9` | Prueba 5 | −0,512 | −0,636 | 0,472 |
| `amss-jgm9` | Prueba 6a | −0,513 | −0,615 | 0,473 |
| `amss-jgm9` | Prueba 7 | −0,516 | −0,613 | 0,473 |
| `amss-jgm9` | Prueba 6b | −0,540 | −0,630 | 0,476 |

Los valores están en grados/s. En cada vehículo el sesgo en z se mantuvo dentro de 0,01 °/s durante
la sesión, pero es distinto entre los dos (0,65 y 0,47 °/s). Por eso cada vehículo necesita su propia
calibración, que consiste en medir el sesgo con el vehículo quieto al arrancar. Sin restarlo, el rumbo acumularía de 28° a 39°
por minuto.

## 4. Lo que estas pruebas no cubren

- La vibración con los motores en marcha: los vehículos se giraron siempre a mano.
- La variación del sesgo con la temperatura en una sesión larga.

Las dos se miden en las corridas con IMU y sin ella del piso 4 ([`PLAN_S26.md`](../historial/PLAN_S26.md) §3.2).

## 5. El acelerómetro de `amss-jgm9`

En reposo, el módulo de la aceleración de `amss-jgm9` es 10,268 m/s², un 4,7 % por encima de 9,81, y
el de `amss-ez9n` 10,008 m/s², un 2 % por encima. La diferencia está en el eje vertical (z), porque
los ejes horizontales marcan menos de 0,45 m/s². Es un desfase del acelerómetro, que se corrige
restando el valor medido en reposo. No afecta a la integración prevista: para el rumbo se usa el
giroscopio, y en un vehículo que se mueve en el plano el acelerómetro solo daría la inclinación. El
criterio de la prueba no se cambia; el resultado queda como está.

## 6. Para integrarla

1. Un controlador que publique `sensor_msgs/Imu` (el paquete de la comunidad, o un nodo propio sobre
   la misma lectura de `probar_imu.py`).
2. El marco `imu_link` en `deepracer_hardware.urdf`, con la orientación del §2.
3. La calibración del sesgo con el vehículo quieto al arrancar, en cada vehículo.
4. El filtro EKF que combine la velocidad de giro con rf2o ([`PLAN_S26.md`](../historial/PLAN_S26.md) §2.3), y
   las corridas con IMU y sin ella en el piso 4 (§3.2).
