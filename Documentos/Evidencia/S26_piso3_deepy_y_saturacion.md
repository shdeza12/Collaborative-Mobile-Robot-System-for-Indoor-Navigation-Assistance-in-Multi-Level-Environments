# Piso 3 con deepy, primeras medias vueltas del agente e intento de G-5 (8 de octubre, tarde)

Sesión en los pisos 3 y 4 con `amss-ez9n` (deepy, `robot1`) y `amss-jgm9` (racey, `robot2`). Primero
corrió deepy solo en el piso 3: cuatro tramos encadenados, un quinto después de dar media vuelta, y
las primeras medias vueltas con `media_vuelta.py` (§3.3 y §3.4 de [`PLAN_S26.md`](../historial/PLAN_S26.md)).
Después se intentó G-5 con las dos cadenas a la vez y el coordinador en racey, y no se pudo correr.
El equipo colocó los vehículos y acompañó las maniobras; Claude lanzó las cadenas y las corridas por
SSH y analizó los registros. Este informe se escribió el 13-oct con lo que quedó en el portátil.

Datos:

- en el portátil, `~/tesis_evidencia/campo_2026-10-08/`: el registro de cada corrida (`p3d_01.log` a
  `p3d_05.log`), los de las medias vueltas (`p3d_media_vuelta*.log`) y los de cada arranque
  (`arranque_*.log`); el registro de carga de deepy de la tarde está copiado en
  `~/tesis_evidencia/lab_2026-10-09/carga_deepy_2026-10-08_piso3.csv`;
- en deepy, sin copiar: el CSV de la campaña (`campana_s26_deepy.csv`) y las grabaciones
  `campana_p3d_01` a `05` y `mv_p3d_04`, `04b` y `05` ([`PLAN_S27.md`](../historial/PLAN_S27.md) §2.5).

## Resultado

1. Las cinco corridas de deepy en el piso 3 terminaron en SUCCEEDED, sin recuperaciones de Nav2. No
   se midieron con flexómetro.
2. En las cinco, al forzar a AMCL a recalcular su pose al terminar, la pose saltó entre 0,61 y 0,86 m.
   Las llegadas de 0,10 a 0,27 m que anotó `ESTADO.md` son las de después del salto.
3. La media vuelta del agente giró 160° frente al Salón 301 y 167° junto a la escalera, en un solo
   tiempo cada una. El primer intento no se movió porque aún no había TF del LiDAR.
4. Con las dos cadenas en la red, las tarjetas se saturaron. La de deepy pasó de una carga de 6 a una
   de 17 a 33, con el procesador al 84-95 %. El aumento estaba en los procesos de AWS y en los demás
   procesos, mientras Nav2 bajaba. G-5 no se corrió.

## 1. Las corridas del piso 3

Salida frente a las escaleras, mirando al norte, en (22,10, 1,06). Cada corrida parte de donde terminó
la anterior, sin pose inicial nueva. Las cifras son de `corrida_nav2.py`.

| Corrida | Tramo | Avance pedido | AMCL | `/odom` | Nav2 | AMCL al terminar Nav2 | Tras recalcular | Salto |
|---|---|---|---|---|---|---|---|---|
| p3d_01 | salida → Salón 303 | 4,966 m | 5,185 m | 5,100 m | 10,7 s | 0,418 m | 0,219 m | 0,64 m |
| p3d_02 | 303 → Salón 302 | 7,741 m | 7,934 m | 8,010 m | 9,7 s | 0,523 m | 0,196 m | 0,71 m |
| p3d_03 | 302 → Salón 301 | 2,854 m | 3,069 m | 3,188 m | 4,1 s | 0,523 m | 0,268 m | 0,69 m |
| p3d_04 | 301 → escalera | 16,238 m | 16,189 m | 16,572 m | 16,2 s | 0,688 m | 0,101 m | 0,61 m |
| p3d_05 | escalera → Salón 303 | 5,667 m | 5,819 m | 5,867 m | 6,4 s | 0,765 m | 0,162 m | 0,86 m |

Entre p3d_03 y p3d_04 el vehículo dio media vuelta en el Salón 301, y entre p3d_04 y p3d_05 junto a
la escalera (§2). Según `/odom`, el vehículo recorrió entre 0,13 y 0,33 m más de lo pedido en cada
corrida. Ninguna orden de avance quedó por debajo de 0,40 m/s.

AMCL corrige su pose cuando el vehículo avanza 0,25 m o gira 0,2 rad. Al detenerse, la pose que
publica es la de su última corrección, y el salto al forzarla mide cuánto iba atrasada. Sin cinta no
se sabe cuál de las dos estaba más cerca del vehículo. El 7-oct, en el piso 4, la pose recalculada
quedó a 0,10 m o menos de la cinta
([`S26_piso4_cadena_media_vuelta.md`](S26_piso4_cadena_media_vuelta.md)).

## 2. Las medias vueltas

| Registro | Dónde | Espacio libre medido | Resultado |
|---|---|---|---|
| `p3d_media_vuelta.log` | Salón 301 | — | No se movió: «sin TF del LiDAR» y «sin TF del mapa» al arrancar |
| `p3d_media_vuelta_b.log` | Salón 301 | 1,74 m a la izquierda, 0,22 m a la derecha | 160° en un tiempo, marcha atrás hacia la izquierda |
| `p3d_media_vuelta_escalera.log` | Junto a la escalera | 1,50 m a la izquierda, 0,86 m a la derecha | 167° en un tiempo, alejándose del vano |

El primer intento arrancó la maniobra antes de que llegaran la TF del LiDAR y la del mapa. Desde
`5f463cc` la maniobra espera hasta 10 s a tenerlas. Al soltar el mando después de la marcha atrás, el
vehículo siguió rodando unos 0,8 m a 0,9 m/s. Desde `75b1904` el tramo que se revisa por delante crece
con la velocidad: 0,25 + 0,9·|v| m, con un mínimo de 0,40 m.

## 3. El intento de G-5 y la saturación de las tarjetas

Secuencia de los arranques, de los registros del portátil:

| Hora | Vehículo | Arranque | Resultado |
|---|---|---|---|
| 18:23 | deepy | Cadena del piso 3 | Lista; corridas p3d_01 a p3d_05 |
| 18:45 | racey | Cadena del piso 4 | AMCL no quedó activo |
| 18:50 | racey | Cadena del piso 4 | Lista, con el controlador `inactive` |
| 19:17 | racey | Cadena del piso 4 | `bt_navigator` y `behavior_server` sin configurar |
| 19:42 | deepy | Descubrimiento local | El LiDAR no publicaba |
| 19:44 y 19:45 | los dos | Descubrimiento local | Listas, con nodos de Nav2 sin configurar; en racey el chequeo de la IMU, rf2o y el filtro falló |
| 20:14 | deepy | Esquema híbrido | Lista, con nodos de Nav2 sin configurar |
| 20:16 y 20:18 | racey | Esquema híbrido | El LiDAR no publicaba |

Carga de la tarjeta de deepy en ventanas de 5 minutos (registro de carga, hora local):

| Ventana | Carga de 1 minuto, media (máxima) | Procesador | Nav2 | Procesos de AWS | Otros |
|---|---|---|---|---|---|
| 18:25 a 18:44 | 5,9 a 6,5 (hasta 12,8) | 52-63 % | 32-46 % | 7-13 % | 3-6 % |
| 18:45 | 17,5 (33,6) | 74 % | 31 % | 20 % | 27 % |
| 18:50 | 23,9 (37,8) | 84 % | 21 % | 30 % | 48 % |
| 18:55 | 33,0 (39,1) | 95 % | 15 % | 42 % | 63 % |
| 19:00 | 27,0 (41,1) | 85 % | 16 % | 30 % | 48 % |
| 19:05 a 19:14 | 6,9 a 7,4 (hasta 18,3) | 58-63 % | 12-13 % | 8-11 % | 16-21 % |
| 19:20 | 30,4 (38,9) | 95 % | 19 % | 40 % | 62 % |

La carga sube cuando arranca la cadena de racey y baja cuando se detiene. Lo que crece son los
procesos de AWS y los demás procesos, que no hacen más trabajo con dos vehículos que con uno; lo que
cambia es con cuántos participantes de la red se comunican. Con el descubrimiento por difusión, los
unos cuarenta procesos de las dos cadenas se anunciaban a todos los demás. Esa noche, con el
descubrimiento limitado al interior de cada vehículo, racey bajó a carga 1,6 y su tráfico inalámbrico
a unos 600 paquetes por segundo, frente a unos 2000 (`ESTADO.md`, entrada del 8-oct).

Con el descubrimiento local, el coordinador en racey dejó de ver la navegación de deepy: Fast DDS solo
anuncia a los participantes 0 a 3 de cada equipo par, y cada vehículo tiene unos quince. El esquema
híbrido (`45a6389`) no se pudo probar: el LiDAR de racey dejó de publicar en dos arranques seguidos, y
al final racey se cayó de la red.

## 4. Lo que cambió después

- El 9-oct el coordinador y el grabador pasaron al portátil, en un contenedor con Jazzy, y cada
  vehículo tiene al portátil como único par. En el laboratorio, con todo el sistema, las tarjetas
  quedaron al 54 % y al 59 % en reposo
  ([`S26_laboratorio_carga_dos_vehiculos.md`](S26_laboratorio_carga_dos_vehiculos.md)).
- El 13-oct, a raíz del §1, se revisó cómo verifica el coordinador una llegada en el vehículo, y se
  corrigió para medir con el vehículo ya asentado ([`PLAN_S27.md`](../historial/PLAN_S27.md) §1.5).

## 5. Pendiente

- Copiar de deepy el CSV y las grabaciones del 8-oct (jueves 15).
- Las llegadas del piso 3 no se pueden comparar con cinta: no se midieron.
