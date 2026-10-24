# Aislamiento de los dos vehículos (bloque A, 28 de septiembre)

Registro del bloque A de [`PLAN_S25.md`](../historial/PLAN_S25.md). El diseño y su justificación están en
[`DISENO_AISLAMIENTO_DOS_CARROS.md`](../DISENO_AISLAMIENTO_DOS_CARROS.md).

## Resultado

El bloque A quedó cerrado el lunes 28 de septiembre, con los dos vehículos. Cada vehículo solo
intercambia los mensajes de servos, LiDAR y transformadas con los procesos de su propia partición, y
un proceso sin perfil no llega a ninguno. Por primera vez los dos vehículos pueden estar encendidos a
la vez sin que uno reciba las órdenes de servo o el láser del otro. La pila del proyecto, en cambio,
todavía corre en un vehículo cada vez (ver «Qué cambia desde hoy»).

Las pruebas las ejecutó Claude por SSH desde el portátil, a petición de Santiago. Las observaciones
del movimiento de las ruedas (A4) las hicieron Santiago y Jonny delante de los vehículos, que estaban
sobre cajas con las ruedas en el aire.

## Los vehículos

| | `amss-ez9n` | `amss-jgm9` |
|---|---|---|
| MAC | `80:91:33:ed:8c:f3` | `80:91:33:f3:e6:ab` |
| Dirección IP el 28-sep | 192.168.0.102 | 192.168.0.104 (era la .101; ver incidencia 1) |
| Batería de tracción (`/i2c_pkg/battery_level`) | `level=8` | `level=8` |
| Estado inicial | `deepracer-core` activo, sin partición instalada, 18 GB libres | igual, 20 GB libres |

## Las pruebas

| Prueba | Qué comprueba | Cómo | `amss-ez9n` | `amss-jgm9` |
|---|---|---|---|---|
| A1 | Que Fast DDS de Jazzy respeta los perfiles igual que el de Humble | [`prueba_particion_carros.sh`](../../herramientas/prueba_particion_carros.sh) en el dominio 87, que no toca el servicio del fabricante | 9 de 9, `PASA` | 9 de 9, `PASA` |
| A2 | Que el servicio del fabricante arranca con su perfil | Perfil elegido por el nombre del equipo (`particion_$(hostname).xml`), instalado en `/etc/deepracer-tesis/particion.xml` con un archivo adicional del servicio; reinicio de `deepracer-core` | `servo_node` con `FASTRTPS_DEFAULT_PROFILES_FILE`; md5 `ff32f591a6d7…`, igual al del repositorio | ídem; md5 `86ad8cd6505d…`, igual al del repositorio |
| A3 | Que el LiDAR solo se ve con el perfil | `ros2 topic hz /rplidar_ros/scan` durante 12 s, con y sin perfil | 6,97 Hz con perfil; ningún barrido sin él | 6,71 Hz con perfil; ningún barrido sin él |
| A4 | Que una orden de dirección solo mueve su vehículo, y que sin perfil no mueve ninguno | [`sonda_direccion.py`](../../herramientas/sonda_direccion.py): centro, +0,6, −0,6, +0,6 y centro, con la tracción en cero | Con perfil: 1 suscriptor emparejado; giraron sus ruedas y las de `amss-jgm9` no. Sin perfil: 0 suscriptores; no se movió ningún vehículo | Con perfil: 1 suscriptor emparejado; giraron sus ruedas y las de `amss-ez9n` no. Sin perfil: 0 suscriptores; no se movió ningún vehículo |
| A5 | Que con los dos encendidos cada odometría ve solo su láser | `ros2 topic hz` en los dos a la vez, 20 s, con perfil | 7,14 Hz | 6,70 Hz |

En A5, la referencia es la medición del 23 de septiembre sin partición: con los dos vehículos
encendidos, cada uno recibía 14,68 Hz, que eran los dos láseres mezclados
([`S24_dos_carros_listos.md`](S24_dos_carros_listos.md)).

## Incidencias

1. Dirección IP. Durante el fin de semana el servidor DHCP le dio la 192.168.0.101 a otro equipo
   (MAC `20:4e:f6:4e:3f:23`) y `amss-jgm9` pasó a la 192.168.0.104. Los vehículos se encontraron por
   su MAC, y la clave SSH de la .104 (`SHA256:EQVlBUAa0do0ntHYxXS8/w9wm5HgA7keJbZjQ9blHI4`) coincide
   con la que tenía `amss-jgm9` en la .101. Antes de cada sesión conviene buscarlos así:
   `for i in $(seq 1 254); do (ping -c1 -W1 192.168.0.$i >/dev/null 2>&1 &); done; sleep 3; ip neigh | grep -iE '80:91:33:ed:8c:f3|80:91:33:f3:e6:ab'`
2. Primer intento de A4. Con `ros2 topic pub`, un proceso por posición y 3 a 5 s por posición, no
   se vio girar la dirección. Se comprobó, en este orden, que la batería estaba conectada
   (`level=8`) y que `ctrl_node` no publicaba nada (0 mensajes en 8 s). También, que la QoS era
   compatible (`servo_node` escucha en `BEST_EFFORT`) y que el transporte con perfil funcionaba
   (123 mensajes publicados, 33 recibidos por un oyente con perfil que arrancó tarde). La causa es que
   `ros2 topic pub` tarda 2 o 3 s en arrancar y emparejarse, así que en ventanas tan cortas casi no
   llegaba nada al servo. Se sustituyó por `sonda_direccion.py`, un solo proceso que publica a 20 Hz,
   espera a emparejarse e informa cuántos suscriptores encontró. Con ella las cuatro observaciones de
   A4 salieron como se esperaba.
3. Regularidad de los barridos. La frecuencia media fue normal en todas las mediciones, pero la
   desviación entre barridos subió en algunas: 0,111 s en `amss-jgm9` en A3 (8 muestras) y 0,075 s
   en `amss-ez9n` en A5 (117 muestras). Como alterna entre vehículos, parece carga momentánea del
   procesador. Queda por vigilar en las grabaciones de G-2, con el criterio de 0,020 s de
   [`HOJA_CAMPO_G2.md`](../historial/HOJA_CAMPO_G2.md).

## Qué cambia desde hoy

Todo proceso que se lance a mano en un vehículo y lea `/rplidar_ros/scan`, `/tf` o `/tf_static`, o
publique en `/ctrl_pkg/servo_msg` o `/ctrl_pkg/raw_pwm`, tiene que cargar el perfil:
`export FASTRTPS_DEFAULT_PROFILES_FILE=/etc/deepracer-tesis/particion.xml`. Sin él no recibe nada y no
da ningún error. Los scripts del repositorio ya lo cargan solos (`nav2_mapa_guardado.sh`,
`correr_corrida_nav2.sh`, `mapear_conduciendo.sh`, `lanzar_bag.inc`).

Los dos vehículos pueden estar encendidos a la vez: el LiDAR y los servos de cada uno ya no
llegan al otro (A5). Lo que todavía no puede correr en los dos a la vez es la pila del proyecto
(el puente de velocidad, rf2o, el SLAM, Nav2 y las grabaciones), porque la partición solo cubre los
cinco tópicos del fabricante. `/cmd_vel`, `/odom` y `/map` son comunes: el `/cmd_vel` que publica la
pila de un vehículo llega también al puente del otro y lo mueve, y cada odometría recibe la del
otro. Eso lo resuelven los espacios de nombres del bloque C de [`PLAN_S25.md`](../historial/PLAN_S25.md).
Hasta entonces, la pila corre en un vehículo cada vez.

## Cómo deshacerlo

En cada vehículo:
`ssh deepracer@<IP> "sudo -n rm -f /etc/systemd/system/deepracer-core.service.d/particion.conf && sudo -n systemctl daemon-reload && sudo -n systemctl restart deepracer-core"`
