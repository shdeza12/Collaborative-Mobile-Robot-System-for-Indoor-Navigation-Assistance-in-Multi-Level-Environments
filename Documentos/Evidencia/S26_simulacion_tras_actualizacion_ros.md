# La simulación de dos robots después de la actualización de ROS del 6 de octubre

> **Seguimiento, 26 de octubre.** En el portátil, con sus paquetes de ROS actualizados el 16 de
> septiembre y el 15 de octubre, la misión con relevo se completó en 3 de 3 corridas:
> [`S29_simulacion_relevo_portatil.md`](S29_simulacion_relevo_portatil.md). La causa de lo que se
> describe aquí sigue sin aislarse.

Sesión del 6 de octubre en el PC de escritorio del equipo. Se siguió
[`GUIA_ARRANQUE.md`](../GUIA_ARRANQUE.md) al pie de la letra, como lo haría alguien que no estuvo en
el desarrollo, para comprobar que la simulación sigue funcionando con los cambios de la semana 26
(niveles 3 y 4 y opción B en el coordinador). Extractos de consola:
[`logs/S26_simulacion_tf_robot1.txt`](logs/S26_simulacion_tf_robot1.txt).

## Resultado

1. **El primer fallo era del workspace, no de la simulación.** `robot.sh robot1 nav2` moría con
   `executable 'agente' not found`: el ejecutable entró en `setup.py` el 7-sep (`725560f`) y el
   workspace se compiló por última vez el 4-sep. Recompilado, arranca. **Ninguna comprobación del
   proyecto lo detectaba**, y ahora tres lo hacen (§1).
2. **Con el código nuevo, el coordinador se comporta igual que antes en simulación**: 31 puntos y
   asignación `{1: robot1, 2: robot2}`. En la corrida que llegó más lejos, el relevo, la asignación
   del segundo robot y la confirmación de piso (RF-28) funcionaron.
3. **Pero hoy, en este equipo, la misión con relevo no se completa.** En las cuatro corridas con las
   dos pilas, tres fallaron porque **Nav2 de robot1 deja de aceptar la transformada `map → odom`
   aunque AMCL la sigue publicando**, y la cuarta llegó hasta el último tramo de robot2. Con robot1
   solo salió bien una vez y falló otra con la misma firma (§2 y §3), así que no depende de que haya
   dos pilas.
4. **La causa no está demostrada.** La sospecha principal, con datos, es la actualización de 452
   paquetes de ROS que se instaló ese mismo día a las 12:16, que incluye `rclcpp`, `tf2`, `tf2_ros`
   y `message_filters` (§4). Falta la prueba que la confirme o la descarte.

---

## 1. El workspace desactualizado, y por qué nada lo detectaba

| Comprobación | Qué miraba | Por qué no lo vio |
|---|---|---|
| `verificar_instalacion.sh` | Que existiera `install/setup.bash` y «los seis paquetes» | El proyecto tiene ocho: `coordinacion` y `coordinacion_msgs` no estaban en la lista fija. Y existir no es estar al día |
| `robot.sh` | Que existiera `install/setup.bash` | Igual |

Se añadió `herramientas/comprobar_workspace.py`, con su prueba `prueba_comprobar_workspace.py`
(15 de 15, y validada mutando el código: tres defectos introducidos, tres detectados). Distingue lo
que con `--symlink-install` exige recompilar —un ejecutable nuevo, un archivo nuevo que nunca se
instaló, un cambio en `setup.py`, `package.xml`, `CMakeLists.txt`, mensajes o C++— de lo que no lo
exige, como editar un `.py` o un `.yaml` ya instalado. Esa distinción evita las falsas alarmas.

Lo usan dos sitios:

- **`robot.sh`** se niega a lanzar con el workspace atrasado, antes de levantar Gazebo. Reproducido
  ocultando el ejecutable `agente`: sale con código 1, nombra el paquete y el motivo, e imprime la
  orden de recompilar. Ningún `gzserver` llega a arrancar.
- **`verificar_instalacion.sh`** tiene una comprobación nueva, «el workspace está al día con el
  código». Además ahora descubre los paquetes en lugar de usar la lista fija, comprueba que el
  enlace del workspace apunte a **este** repositorio y no solo que sea un enlace, y compara rutas
  resueltas y no texto. Esto último quitó un fallo falso: la variable `GAZEBO_MODEL_PATH` estaba bien
  puesta, y el script recomendaba añadir una cuarta línea duplicada a un `~/.bashrc` que ya tenía tres.

## 2. Las corridas

Todas en simulación, con Gazebo sin ventana (`gui:=false`), desde la raíz del repositorio y con la
misión `piso1_representacion → piso2_ieee` de la guía (§5.2 b), salvo la del renglón «aislada».

| Corrida | Pilas | Misión lanzada | Resultado | Dónde falló |
|---|---|---|---|---|
| `PRUEBA_B_01` | dos | unos 2 min después de la compuerta | **Colgada**: 400 s sin avanzar, hasta cancelarla a mano | robot1, tramo 1 |
| `PRUEBA_B_02` | dos | unos 4 min después de la compuerta | Nav2 abortó tras 157,4 s | robot1, tramo 1 |
| aislada | **solo robot1** | inmediatamente | ✅ **Completada** en 52,9 s, llegadas a 0,106 m | — |
| aislada 2, tras el depurado | **solo robot1** | inmediatamente | Nav2 abortó tras 158,4 s, con 2.818 `Transform data too old` y 0 errores de modelo | robot1, tramo 1 |
| `PRUEBA_B_03` | dos | inmediatamente | Tramos 1, 2 y 3 bien (0,178, 0,169 y 0,099 m) y confirmación de piso a los 2,8 s; Nav2 abortó en el tramo 4 | robot2, tramo 4 |
| `PRUEBA_B_04` | dos | inmediatamente | Nav2 abortó tras 158,6 s | robot1, tramo 1 |

Las dos primeras se apartaron de la guía, que pide lanzar la misión en cuanto la compuerta da
`LISTA`. Pero `PRUEBA_B_04` se lanzó sin demora y falló igual, así que la espera no explica el fallo.

El fallo de `PRUEBA_B_03` no se puede atribuir: la campaña de N = 30 midió un 86,7 % de éxito en
simulación, así que un fallo aislado de robot2 cabe en la variabilidad ya conocida.

`PRUEBA_B_01` no cuenta como corrida: a mitad de su grabación se relanzó el Gazebo de robot1, y el
propio grabador lo marcó con un RTF negativo. El RTF de `PRUEBA_B_02` fue de **0,9922**, dentro de
RNF-06, así que la carga del equipo no explica el fallo.

## 3. El fallo de robot1, medido

Lo que se sabe, cada punto con su medida:

1. **AMCL de robot1 publica `map → odom` sin cortes.** Leído de los bags: 1.494 mensajes en
   `PRUEBA_B_02` y 1.539 en `PRUEBA_B_04`, con un hueco máximo de 0,20 s. Lo mismo que robot2.
2. **El controlador de Nav2 de robot1 no los acepta.** Su buffer TF se queda con un `map → odom`
   viejo: en `PRUEBA_B_02` lo ve en 115,7 s cuando ya va por 276,4 s; en `PRUEBA_B_04`, en 55,0 s
   cuando va por 128,3 s. Con ese eslabón congelado no hay pose en el mapa, y Nav2 termina abortando.
3. **No es un rechazo que tf2 anuncie.** No aparece ni un `TF_OLD_DATA` ni un aviso de salto de
   reloj en ningún log.
4. **No es el coordinador.** En la primera corrida el error ya estaba en el log más de un minuto
   antes de que el coordinador arrancara: lo produjo el agente de robot1 al buscar su propia pose.
5. **No es el láser atrasado.** Los sellos de `/scan` iban al día con su reloj, en los dos robots.
6. **La compuerta no lo detecta.** `esperar_nav2.sh` y `verificar_condicion_inicial.py` comparan
   `/amcl_pose` con `/odom`. `/amcl_pose` no se republica con el robot quieto, así que pasan aunque
   el buffer de Nav2 ya esté congelado.
7. **El coordinador no siempre falla rápido.** En `PRUEBA_B_01` estuvo 400 s esperando sin dar
   error; en las otras, Nav2 abortó a los ~158 s.

## 4. La sospecha: la actualización de ROS de ese mismo día

El código de la simulación casi no cambió desde el 10-sep, cuando el relevo en simulación funcionaba
(`S22_RF20_telefono_C_02`). Desde esa fecha, el único commit que tocó un archivo de la simulación es
`7788d94` (11-sep), que renombra controladores. Los parámetros de AMCL de la simulación no cambiaron.

Lo que sí cambió fue el sistema. El 6 de octubre a las 12:16 se actualizaron **452 paquetes de ROS**,
y la primera simulación de ese día fue a las 13:29. Entre los actualizados están justo las piezas
de un buffer TF que deja de aceptar datos:

| Paquete | Antes | Después |
|---|---|---|
| `rclcpp` | 16.0.19 | 16.0.21 |
| `tf2`, `tf2_ros` | 0.25.22 | 0.25.23 |
| `message_filters` | 4.3.19 | 4.3.20 |
| `rclpy` | 3.3.21 | 3.3.22 |
| `nav2_amcl`, `nav2_controller`, `rmw_fastrtps_cpp` | compilación de julio y agosto | compilación del 7 y 8 de septiembre |

**Es una coincidencia en el tiempo y en los componentes, no una prueba.** Lo que la decidiría es un
A/B, con la misma guía y el mismo código:

- en el portátil de campo, si no se ha actualizado (`grep 2026-10 /var/log/apt/history.log`), o
- en este equipo, volviendo a las versiones anteriores de esos paquetes.

## 5. Otras observaciones de la sesión

- **`rosbridge` no estaba instalado en este equipo, y ningún documento lo pedía.** El §4 de
  `GUIA_ARRANQUE.md` lo usa para la interfaz del teléfono, y como la interfaz no es un paquete ROS,
  `rosdep` nunca lo instalaba. Se añadió al README junto con `rosbag2-storage-mcap`, por la misma
  razón, y el verificador comprueba ahora las dos.
- **Dos pruebas de DDS fallaban de forma intermitente, y las dos en el cierre, no en lo que verifican.**
  Corregidas el mismo día:
  - `prueba_round_trip.py` abortaba con «terminate called without an active exception» **después**
    de imprimir que todo pasaba, en 1 de cada 6 corridas: nunca esperaba al hilo del ejecutor ni
    destruía los nodos. Es la lección que `prueba_dos_dominios_accion.py` ya tenía escrita en su
    cierre. **Y había un defecto peor: salía con código 0 aunque fallara una comprobación**, así que
    la batería la habría contado como aprobada. Era la única de las 32 con ese defecto. Comprobado
    con mutación: con una comprobación forzada a fallar, antes salía con 0 y ahora con 1. Después
    del arreglo, 20 de 20 corridas limpias.
  - `prueba_dos_dominios_accion.py` convertía en fallo un veredicto PASA cuando su servidor auxiliar
    no terminaba en 5 s con SIGTERM. Ahora, si no se va por las buenas, se mata. Comprobado con un
    servidor que ignora SIGTERM: el código anterior reproduce exactamente el `TimeoutExpired` del día
    y sale con 1; el nuevo pasa y sale con 0.
- **El grabador detectó el problema por sí solo.** En `PRUEBA_B_02` avisó al empezar: «el criterio 1
  del §8 NO se cumple (AMCL no sabe donde esta)». La instrumentación funcionó; lo que no hay es una
  compuerta que impida lanzar la misión en ese caso.

## 6. Lo que cambia en el trabajo

- **Para G-5 y la campaña física**, este fallo no aplica directamente: el coordinador y los agentes
  corren en los vehículos, en Jazzy. Pero el portátil de campo, en Humble, compone los registros y
  sirve la interfaz. **Recomendación: no actualizar los paquetes de ROS del portátil de campo antes
  del corte C-3 (16 de octubre).**
- **La simulación no se puede usar para datos nuevos** mientras no se resuelva el §4. Los 30
  registros de la campaña de OE4 no se ven afectados: se tomaron en septiembre y se regeneran desde
  sus bags (`S23_reproducibilidad_de_los_registros.md`).

## 7. Pendiente

1. El A/B del §4, para confirmar o descartar la actualización como causa.
2. Decidir si la compuerta debe comprobar también que el `map → odom` de Nav2 esté fresco, y no solo
   `/amcl_pose`. Toca `esperar_nav2.sh`, que es herramienta y no código congelado.
3. Decidir si el coordinador debe tener un plazo propio por tramo, para que una misión no quede
   colgada como en `PRUEBA_B_01`. Ese sí es código congelado y la decisión es del equipo.
