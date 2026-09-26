# Diseño — los dos vehículos encendidos a la vez sin pisarse

**Redactado:** 2026-09-25 (S24). **Estado:** mecanismo probado en el portátil; **pendiente de
confirmar en los vehículos**, que es la primera tarea de [`PLAN_S25.md`](PLAN_S25.md).

**Por qué es lo primero.** El sistema real —dos vehículos, coordinador y relevo entre pisos, que
es lo que piden G-5 y RF-27— exige los dos carros encendidos y moviéndose a la vez. Hoy eso **no se
puede hacer**: con los dos encendidos, una orden de tracción mueve los dos (17-sep) y la odometría de
cada uno recibe el láser del otro (23-sep). El único procedimiento que existe es parar el servicio
del otro carro, que vale para pruebas de uno y es incompatible con el sistema. Sin resolver esto, el
sistema real no puede correr.

---

## 1. El problema: qué choca, y qué pasa cuando choca

El software de fábrica de AWS (`deepracer-core`) publica sus tópicos con **nombre global**, sin
espacio de nombres, y los dos vehículos están en el mismo dominio de ROS 2, el 0.

| Tópico | Lo publica | Lo lee | Con los dos encendidos | Medido |
|---|---|---|---|---|
| `/ctrl_pkg/servo_msg` | el puente `cmdvel_to_servo`, la consola de AWS | `servo_pkg` de **cada** carro | **una orden mueve los dos carros** | 17-sep |
| `/ctrl_pkg/raw_pwm` | la consola de AWS | `servo_pkg` de cada carro | ídem | — |
| `/rplidar_ros/scan` | el LiDAR de cada carro | rf2o, AMCL, costmaps | cada carro recibe **los dos** láseres, intercalados | 23-sep |
| `/tf`, `/tf_static` | rf2o, `robot_state_publisher`, AMCL | todo Nav2 | el marco `laser` del driver de AWS tendría dos padres | por diseño |

## 2. Lo que no se puede cambiar

| Restricción | De dónde sale |
|---|---|
| **No tocar `/opt/aws/`**: el servicio de AWS no se edita | una actualización de AWS lo revertiría en silencio (criterio de S20) |
| **Un solo dominio para todo el sistema** | G-4 y RF-15 se alcanzaron con el coordinador y los dos agentes en el mismo grafo; separar dominios los rompe |
| **El coordinador corre en un vehículo** | decisión D6: la acción de Nav2 no es el mismo tipo en Humble y en Jazzy |
| **Marcos con prefijo**: el coordinador manda las metas en `robotN/map` | `coordinador.py:631`, igual que en simulación |
| **Código congelado desde el 18-sep** | la solución tiene que ser de despliegue —configuración y lanzadores—, no funcionalidad nueva |
| **Todo lo que toque el hardware corre como `root`** | regla del dueño de Fast DDS (22-sep) |

## 3. Las opciones que se consideraron

| Opción | Qué es | Veredicto |
|---|---|---|
| **A** · un dominio por vehículo + `domain_bridge` | aislar cada carro y puentear lo común | **descartada**: el coordinador usa **acciones** de Nav2 por robot, y puentearlas entre dominios no es trivial; además rompe el grafo común de G-4 |
| **B** · relanzar LiDAR y servos fuera de `deepracer-core`, con espacio de nombres | el repo tiene `lidar_vehiculo.launch.py` con `namespace:=` | **reserva**: funciona, pero obliga a desmontar el arranque de AWS en los dos carros. Es el plan B del §7 |
| **C** · remapear dentro del arranque de AWS | editar su lanzador | **descartada**: toca `/opt/aws/` |
| **D** · **una partición DDS por vehículo** para los tópicos globales | cada carro solo ve los suyos; lo demás, igual | **elegida** |
| **E** · `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` | que cada proceso solo descubra su máquina | **descartada, está medido**: el 23-sep bloqueó el propio LiDAR del carro, que se anuncia por la interfaz de red |
| **F** · reemitir el láser con otro nombre y marco | un nodo que copie `/rplidar_ros/scan` a `/robotN/scan` | **innecesaria** con D, y sería código nuevo en plena congelación |

## 4. El diseño

**Dos capas.** La de **hardware** es privada de cada vehículo: los cinco tópicos del §1 van en una
partición DDS con el nombre del carro. La del **sistema** es común: todo lo nuestro va con espacio
de nombres `/robot1` o `/robot2` y marcos con prefijo `robotN/`, exactamente como en simulación, y
sigue en la partición por defecto.

```
            amss-jgm9  (robot1)                         amss-ez9n  (robot2)
  ┌──────────────────────────────────────┐   ┌──────────────────────────────────────┐
  │ partición "amss-jgm9"  (privada)     │   │ partición "amss-ez9n"  (privada)     │
  │   /rplidar_ros/scan   /tf /tf_static │   │   /rplidar_ros/scan   /tf /tf_static │
  │   /ctrl_pkg/servo_msg  raw_pwm       │   │   /ctrl_pkg/servo_msg  raw_pwm       │
  ├──────────────────────────────────────┤   ├──────────────────────────────────────┤
  │ partición por defecto  (común)       │◄─►│ partición por defecto  (común)       │
  │   /robot1/odom  /robot1/cmd_vel      │   │   /robot2/odom  /robot2/cmd_vel      │
  │   /robot1/navigate_to_pose  …        │   │   /robot2/navigate_to_pose  …        │
  │   coordinador, rosbridge, interfaz   │   │                                      │
  │   /coordinacion/*                    │   │                                      │
  └──────────────────────────────────────┘   └──────────────────────────────────────┘
```

**Por qué la TF también va en la partición.** El driver de AWS pone el barrido en el marco `laser`,
sin prefijo, y no se puede cambiar sin tocar `/opt/aws/`. Con una TF compartida, ese marco tendría
dos padres, uno por carro. Con una TF **privada por carro**, cada uno tiene su árbol completo
—`robotN/map → robotN/odom → robotN/base_link → robotN/laser → laser`, con la última una identidad
estática— y no hay conflicto. **Nadie necesita la TF del otro carro**: el coordinador usa
`/robotN/odom` y las acciones, la interfaz solo usa `/coordinacion/*`, el registro de misión solo lee
el estado de la misión y las `/robotN/odom`, y el agente consulta la TF de su propio vehículo.
Comprobado leyendo el código el 2026-09-25.

**Dónde corre cada cosa:**

| Pieza | `amss-jgm9` | `amss-ez9n` |
|---|---|---|
| `deepracer-core` (AWS), con el perfil de su carro | ✓ | ✓ |
| rf2o, `map_server` + AMCL, Nav2, puente de servos, agente | `/robot1` | `/robot2` |
| coordinador, `rosbridge`, interfaz | ✓ | — |

**La regla operativa, una sola:** *todo proceso que corra en un vehículo carga el perfil de ese
vehículo.* Un proceso sin él **no ve** los tópicos de hardware y **no da error**. Es lo que se quiere
para las órdenes de tracción —nadie mueve un carro por olvido— y es una trampa al depurar: un
`ros2 topic echo /rplidar_ros/scan` sin el perfil se queda mudo.

## 5. Cómo se aplica

Los perfiles están en el repo, uno por vehículo:
[`particion_amss-ez9n.xml`](../Robot/aws-deepracer/deepracer_bringup/config/particion_amss-ez9n.xml)
y [`particion_amss-jgm9.xml`](../Robot/aws-deepracer/deepracer_bringup/config/particion_amss-jgm9.xml).

**1. Instalar en cada vehículo el perfil de ese vehículo, con un nombre común.** En `amss-ez9n` se
instala `particion_amss-ez9n.xml` como `/etc/deepracer-tesis/particion.xml`; en `amss-jgm9`, el
suyo con el mismo nombre. **Así ningún script necesita saber en qué vehículo corre**: todos apuntan a
la misma ruta, y lo que cambia es qué fichero hay instalado en ella. Está fuera de `/opt/aws/`, y
fuera de `~/tesis/`, para que una copia o una limpieza de las herramientas no lo arrastre: de él
depende que el vehículo se pueda mover.

**2. Al servicio de AWS, por un *drop-in* de systemd**, que no toca `/opt/aws/` y se revierte
borrando un fichero: `/etc/systemd/system/deepracer-core.service.d/particion.conf` con

```ini
[Service]
Environment=FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml
```

y después `sudo systemctl daemon-reload && sudo systemctl restart deepracer-core`. Las órdenes
exactas, con su comprobación, están en el §1 de [`PLAN_S25.md`](PLAN_S25.md).

**3. A todo lo nuestro**, exportando la misma variable antes de lanzar:
`export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml`. El script de arranque
[`nav2_mapa_guardado.sh`](../herramientas/nav2_mapa_guardado.sh) y los de campaña la tienen que
llevar; es parte del §3 de [`PLAN_S25.md`](PLAN_S25.md).

**Para deshacerlo:** borrar el `particion.conf`, `daemon-reload` y reiniciar el servicio. El
vehículo vuelve a su estado de fábrica; el fichero de `/etc/deepracer-tesis/` sin el *drop-in* no
lo lee nadie.

## 6. Lo comprobado y lo que falta

**Comprobado en el portátil (Humble), el 2026-09-25**, con
[`prueba_particion_carros.sh`](../herramientas/prueba_particion_carros.sh) sobre los dos perfiles del
repo:

| Tópico | Lee | Publica | Resultado |
|---|---|---|---|
| `/ctrl_pkg/servo_msg` | ez9n | ez9n | recibe |
| | ez9n | jgm9 | **no recibe** |
| | ez9n | sin perfil | **no recibe** |
| `/rplidar_ros/scan` | los mismos tres casos | | igual |
| `/tf_static` | ez9n | ez9n | la ve |
| | jgm9 | ez9n | **no la ve** |
| `/robot1/estado` (sin partición) | ez9n | jgm9 | **recibe**: el grafo común no se rompe |

**9 de 9.** La prueba se niega a correr en el dominio 0, el de los vehículos.

**Lo que falta, en este orden, y es la primera tarea de la semana:**

1. La misma prueba **en un vehículo**: que el rmw de Jazzy respete los perfiles igual que el de
   Humble.
2. El *drop-in* en **un** vehículo y, **con las ruedas en el aire**, que una orden desde el otro
   vehículo **no lo mueva** y una desde él mismo sí.
3. Los dos vehículos encendidos: cada uno se mueve solo con sus órdenes, y la odometría de cada uno
   solo ve su láser.

## 7. Si la partición no funciona en el vehículo

**Plan B, opción B del §3:** arrancar el LiDAR y los servos fuera de `deepracer-core`, con espacio de
nombres, usando `lidar_vehiculo.launch.py` —que ya acepta `namespace:=`— y parando esas dos piezas del
servicio de AWS. Cuesta más y desmonta el arranque de fábrica, pero no depende de DDS.

**Y si tampoco eso llega a tiempo:** el acta ya tiene escrito el repliegue —la demostración con **un
solo vehículo real**—. Conviene decidirlo como tarde el **viernes 9 de octubre**, no el 15.

## 8. Límites conocidos

- **Los servicios de AWS siguen chocando**: `/i2c_pkg/battery_level`, `/ctrl_pkg/*`, `/servo_pkg/*`
  existen con el mismo nombre en los dos carros, y con los dos encendidos una llamada la puede
  contestar el otro. **El sistema no los usa**; para leer la batería de un carro concreto, léela antes
  de encender el otro.
- **Fast DDS 3 renombra** `<publisher>`/`<subscriber>` a `<data_writer>`/`<data_reader>`. Jazzy usa
  Fast DDS 2.14; si alguna vez se actualiza, los perfiles hay que traducirlos.
- **Depurar exige el perfil**: cualquier `ros2 topic echo`, `tf2_echo` o `ros2 bag record` de un tópico
  de hardware tiene que cargarlo, o no verá nada.
