# Sistema Robótico Colaborativo para Asistencia en Navegación en Interiores Multinivel

> Trabajo de grado — Ingeniería Electrónica
> Universidad Santo Tomás · Facultad de Ingeniería Electrónica
> GED (Grupo de Estudio y Desarrollo en Robótica)

Sistema colaborativo de dos robots móviles terrestres para la guía coordinada de visitantes
en entornos interiores con múltiples pisos. Cada agente opera en un nivel dedicado y un
servidor central asigna tareas dinámicamente, ejecutando un protocolo de relevo en la zona
de transición vertical. El usuario solicita su destino desde una interfaz móvil.

El aporte del proyecto es la **arquitectura de coordinación entre agentes**, no la locomoción.

El estado de avance detallado se mantiene en [`ESTADO.md`](ESTADO.md).

---

## Requisitos

| Componente | Versión | A tener en cuenta |
|------------|---------|-------------------|
| Sistema operativo | Ubuntu 22.04 LTS | Otras versiones no están probadas |
| Middleware | ROS 2 **Humble** | Foxy no sirve: el código se migró y usa `joint_state_broadcaster` y el estado `active` |
| Simulador | Gazebo **Classic** 11 | No confundir con Ignition / Gazebo Sim: el plugin Ackermann del proyecto es de Classic |
| Python | 3.10 | El que trae Ubuntu 22.04 |

Instalar ROS 2 Humble siguiendo la [guía oficial](https://docs.ros.org/en/humble/Installation.html),
y luego las dependencias de simulación:

```bash
sudo apt update && sudo apt install -y \
  gazebo libgazebo-dev \
  ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-teleop-twist-keyboard ros-humble-xacro ros-humble-rviz2 \
  python3-colcon-common-extensions python3-rosdep python3-pil
```

---

## Instalación

Seis pasos. El último comprueba los cinco anteriores, así que no hay que fiarse de que
"pareció funcionar". Las rutas de ejemplo son `~/Tesis` para el repositorio y
`~/deepracer_sim_ws` para el workspace; si se usan otras, ajustarlas en todos los pasos.

### 1. Clonar el repositorio

```bash
git clone https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments.git ~/Tesis
```

Eso trae `main`, que es la última versión verificada y la que conviene en general.

<details>
<summary><b>Alternativa: descargar una versión fija (un tag)</b></summary>

Un tag es un punto del historial que ya no se mueve. Sirve para reproducir un resultado o
para reportar un fallo sin ambigüedad sobre qué código se tenía. El vigente es
**`v0.2.2-dos-niveles-y-evidencia`**; los publicados se listan con
`git ls-remote --tags <url del repositorio>`.

**Por consola:**

```bash
git clone --branch v0.2.2-dos-niveles-y-evidencia \
  https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments.git ~/Tesis
```

Git avisará de que el repositorio queda en estado *detached HEAD*. **No es un error**:
significa que se está sobre un punto fijo del historial en vez de sobre una rama que avanza.
Para instalar y simular no cambia nada; solo importa si se van a hacer commits.

**Por la web de GitHub, sin usar git:** abrir el repositorio → pestaña **Releases** (o
**Tags**) → en `v0.2.2-dos-niveles-y-evidencia`, **Source code (zip)**. Descomprimirlo y
**renombrar la carpeta**, porque GitHub le quita la `v` al tag y el nombre no coincide con
el de las instrucciones:

```bash
unzip ~/Descargas/*-0.2.2-dos-niveles-y-evidencia.zip -d ~
mv ~/*-0.2.2-dos-niveles-y-evidencia ~/Tesis
```

El ZIP no trae la carpeta `.git`: se puede instalar y simular igual, pero no consultar el
historial ni actualizar con `git pull`. Los permisos de ejecución de los scripts **sí** se
conservan; si aun así algo da `Permission denied`, `chmod +x herramientas/*.sh`.

Desde aquí, los pasos 2 a 6 son idénticos.

</details>

### 2. Crear el workspace enlazando los paquetes

Los paquetes ROS 2 viven en `Robot/aws-deepracer/`, pero se compilan desde un workspace de
colcon aparte, que **enlaza** esa carpeta:

```bash
mkdir -p ~/deepracer_sim_ws/src
ln -s ~/Tesis/Robot/aws-deepracer ~/deepracer_sim_ws/src/aws-deepracer
```

> **Un enlace, nunca una copia.** Con `cp -r` el código que se ejecuta deja de ser el que
> está bajo control de versiones, y ambos divergen sin avisar. En este proyecto eso ya pasó
> —incidente R7—: durante semanas se compiló una copia mientras se editaba el repositorio,
> así que los arreglos de SLAM nunca llegaron a ejecutarse y la cartografía de ese periodo
> quedó invalidada. El paso 6 comprueba explícitamente que sea un enlace.

### 3. Resolver dependencias

```bash
cd ~/deepracer_sim_ws
sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

`sudo rosdep init` solo hace falta la primera vez en el equipo; si ya estaba inicializado
avisa y no pasa nada.

### 4. Compilar

```bash
colcon build --symlink-install
```

Esperado: `Summary: 6 packages finished`, en algo menos de un minuto y sin ninguna
advertencia. Si aparece cualquier paquete en `failed`, no seguir al paso siguiente.

### 5. Variables de entorno

Los mundos y los modelos SDF viven en la raíz del repositorio, **fuera** del workspace, así
que Gazebo no los encuentra solo. El paso 4 termina dentro de `~/deepracer_sim_ws`; antes
de ejecutar el bloque de aquí hay que volver a la raíz del repositorio (la carpeta que se
clonó o descomprimió en el paso 1):

```bash
# Ir a la raíz del repositorio: aquí va la ruta donde se descargó el código
cd ~/Tesis

# Red de seguridad: si esto NO lista el archivo, la ruta del cd de arriba no es la
# correcta. Hay que parar y corregirla antes de seguir: las órdenes siguientes usan
# $PWD, y desde otra carpeta escribirían una GAZEBO_MODEL_PATH que apunta a un sitio
# sin mundos, con el fallo silencioso que se describe más abajo.
ls pasillo_grande.world

grep -v '^[[:space:]]*#' ~/.bashrc 2>/dev/null | grep -qF 'deepracer_sim_ws/install/setup.bash' || echo 'source ~/deepracer_sim_ws/install/setup.bash' >> ~/.bashrc

grep -v '^[[:space:]]*#' ~/.bashrc 2>/dev/null | grep -F GAZEBO_MODEL_PATH | grep -qF "$PWD" || echo "export GAZEBO_MODEL_PATH=\"\$GAZEBO_MODEL_PATH:$PWD\"" >> ~/.bashrc

exec bash
```

> **Por qué se comprueba antes de añadir.** Repetir este paso es lo habitual cuando algo
> falla a mitad de instalación. Con un `>>` a ciegas, cada intento agrega las líneas otra
> vez y `~/.bashrc` acaba con varias copias que se pisan entre sí; el `grep ... ||` de
> delante añade cada línea solo si no está ya.
>
> **La comprobación pregunta por el efecto, no por el texto:** ¿hay alguna línea activa que
> meta *esta* ruta en `GAZEBO_MODEL_PATH`? Antes comparaba la línea entera con `grep -qxF`,
> y eso solo reconoce su propia forma exacta: una línea equivalente escrita a mano —sin las
> comillas, con otro espaciado— no coincidía y la orden añadía una segunda copia de la misma
> ruta. Pasó de verdad, en el equipo de desarrollo, con una línea puesta el 11 de agosto.
>
> El `grep -v '^[[:space:]]*#'` descarta las líneas comentadas, para que una línea desactivada
> a propósito no cuente como puesta y deje la orden sin hacer nada. `-F` compara texto
> literal: sin ella, una carpeta con corchetes o puntos en el nombre se leería como expresión
> regular y la comprobación dejaría de proteger **sin dar ningún error**. Y las comillas
> alrededor del valor son lo que permite que la ruta lleve espacios sin que la siguiente
> terminal arranque con `not a valid identifier`.
>
> `exec bash` no es decorativo: escribir en `~/.bashrc` **no cambia la terminal ya abierta**.
> Sin recargar, todo lo que se lance desde aquí seguirá sin ver la variable.

La primera línea evita tener que hacer `source` en cada terminal nueva. La segunda añade la
raíz del repositorio a `GAZEBO_MODEL_PATH`, y la necesitan los mundos que incluyen modelos
externos con `model://`: **`mundo_definitivo.world`**, que es el mundo vigente y el que los
launch cargan por defecto, `pasillo_grande.world`, `pasillo_test.world`,
`USTA_WORLD/usta_test.world` y `primer_piso_dos_niveles.world`. Solo `primer_piso.world` y
`primer_piso_v2.world` llevan la geometría embebida y funcionan sin ella.

> Esta variable dejó de ser opcional el 2026-08-20. Mientras el mundo vigente fue
> `primer_piso_v2.world`, con la geometría embebida, olvidarla solo rompía mundos que había
> que pedir a mano con `world:=`. Ahora la necesita el mundo por defecto, así que sin ella
> **el lanzamiento normal abre un mundo vacío** —plano gris y sol— sin dar error.

> **Por qué es una trampa.** Sin la variable Gazebo **no aborta**: devuelve código de salida
> 0 y carga el mundo incompleto —plano gris y sol, pero sin pasillo—, dejando una sola línea
> perdida en su salida: `Error Code 12 Msg: Unable to find uri[model://pasillo_grande]`.
> Y encima **funciona igual sin la variable si se lanza desde la raíz del repositorio**,
> porque Gazebo también busca en el directorio actual. Por eso este fallo no aparece nunca en
> el equipo de quien escribe las instrucciones, y sí en el de quien lanza desde otra carpeta.

Existe una tercera variable opcional, `TESIS_WORLDS_DIR`, para apuntar a otro checkout del
repositorio. No hace falta declararla: por defecto cada launch deduce la raíz a partir de la
ubicación real de su propio archivo, de modo que los mundos salen siempre del mismo clon que
el código que se está ejecutando.

### 6. Verificar la instalación

```bash
~/Tesis/herramientas/verificar_instalacion.sh
```

Comprueba entorno, workspace, los seis paquetes, los recursos instalados, el URDF y sus
mallas, el parseo de los seis launch files y las variables de entorno —**sin levantar Gazebo
ni ningún nodo**—, y explica junto a cada fallo qué hacer; cuando existe un comando exacto
que lo corrige, lo imprime solo en su línea, listo para copiar. Debe terminar en:

```
  31 comprobaciones pasan, 0 fallan.
```

Mientras haya fallos no tiene sentido lanzar la simulación. El script existe porque unas
instrucciones de instalación se prueban una sola vez, en el equipo de quien las escribió,
donde todo ya funcionaba.

---

## Uso

El procedimiento completo de mapeo está en
[`Documentos/guia_simulacion_slam.md`](Documentos/guia_simulacion_slam.md). Resumen de las
cuatro terminales:

**Terminal A — Gazebo y spawn del robot**

```bash
ros2 launch deepracer_bringup deepracer_sim.launch.py
```

Carga el mundo vigente **del mismo repositorio del que se compiló el código**: la raíz se
deduce de la ubicación real del archivo de lanzamiento, no del `$HOME` ni de una ruta fija.
Para usar otro mundo, `world:=<ruta al .world>`.

Verificar en el log que los **7 controladores** (`joint_state_broadcaster`, 4 ruedas y
2 hinges de dirección) queden en estado `active`.

**Terminal B — SLAM**

```bash
ros2 launch deepracer_bringup slam_toolbox.launch.py
```

**Terminal C — Teleoperación**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Terminal D — Visualización**

```bash
rviz2
```

En RViz: `Fixed Frame` = `map`, y en el display `Map` la propiedad
`Durability Policy` = `Transient Local` (con `Volatile` el mapa nunca llega).

### Navegación autónoma sobre un mapa ya construido

Un solo comando levanta Gazebo, el robot, AMCL y la pila Nav2, sobre
`mundo_definitivo.world` y el mapa de su piso 1:

```bash
ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py
```

> **Sobre el mapa que trae por defecto.** `maps/mundo_definitivo_piso1.yaml` no salió de un
> recorrido de SLAM: lo generó `herramientas/generar_mapa_desde_mundo.py` leyendo la
> geometría del `.world`, así que su fidelidad es exacta —0 de 4725 obstáculos sin pared
> real detrás—. Es la misma vía por la que se cerró el riesgo R10 el 2026-08-14, aplicada al
> mundo nuevo: no hay cartografía inventada que corregir.
>
> Aun así `herramientas/verificar_mapa.py` lo **rechaza**, y conviene saber por qué antes de
> tomarlo por un defecto del mapa: el mundo trae los dos pasillos lado a lado en Y, este mapa
> cubre solo uno, y la herramienta mide la cobertura contra el mundo entero. De ahí el 29,7 %
> en Y. La herramienta sabe separar niveles por altura (su tercer argumento), pero aquí los
> dos pisos están a la misma z y separados en Y, y eso todavía no lo sabe expresar.

Argumentos disponibles (`--show-args` los lista): `world`, `map`, `params`, `namespace`.
El objetivo se envía desde RViz con la herramienta **2D Goal Pose**, o por línea de comandos:

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0}, orientation: {w: 1.0}}}}"
```

### Dos robots (en desarrollo)

El argumento `namespace` permite correr dos agentes aislados, cada uno con su propia pila
Nav2 y sus marcos TF prefijados (`robot1/base_link`). Requiere además separar el simulador
y el grafo DDS de cada instancia:

```bash
# Terminal 1
GAZEBO_MASTER_URI=http://localhost:11345 ROS_DOMAIN_ID=1 \
  ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot1

# Terminal 2
GAZEBO_MASTER_URI=http://localhost:11346 ROS_DOMAIN_ID=2 \
  ros2 launch deepracer_bringup nav_amcl_demo_sim.launch.py namespace:=robot2 y:=2.0
```

Con `namespace` vacío (el valor por defecto) el comportamiento es exactamente el de un solo
robot, sin prefijos. El estado y las limitaciones de este modo están en
[`Documentos/Evidencia/S17_nav2_namespaces.md`](Documentos/Evidencia/S17_nav2_namespaces.md).

---

## Guardar y verificar un mapa

En simulación, `map_saver_cli` requiere `use_sim_time`, de lo contrario agota su espera
antes de recibir el mapa:

```bash
ros2 run nav2_map_server map_saver_cli -f /tmp/mapa_candidato \
  --ros-args -p use_sim_time:=true
```

Antes de aceptar un mapa como definitivo, validarlo contra la geometría del mundo:

```bash
python3 herramientas/verificar_mapa.py /tmp/mapa_candidato.yaml mundo_definitivo.world
```

La herramienta compara la extensión mapeada con la del archivo `.world` y rechaza el mapa
si la cobertura es insuficiente. Devuelve código de salida distinto de cero cuando falla,
por lo que puede encadenarse en scripts.

En un mundo de varios niveles hay que decir **cuál** se está verificando, con un tercer
argumento: la altura del corte horizontal, en metros sobre el suelo del mundo. Por defecto
son 0,30 m, la altura del LiDAR sobre el nivel 1:

```bash
python3 herramientas/verificar_mapa.py Robot/aws-deepracer/deepracer_bringup/maps/primer_piso_definitivo.yaml primer_piso_dos_niveles.world 3.30
```

Un mapa 2D es un corte, no una sombra: proyectar todo al plano metería la losa del nivel 2
—una caja de 50 × 20 m— como si fuera pared, y taparía el mapa entero. Ese tercer argumento
es también la forma de comprobar que **el mismo mapa sirve para los dos niveles**: los dos
cortes dan `ACEPTADO` con las mismas cifras, que es la evidencia de que las dos plantas son
la misma geometría. `generar_mapa_desde_mundo.py` acepta la misma opción como `--altura`.

---

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| `Robot/aws-deepracer/` | Paquetes ROS 2 del robot (ver [`Robot/README.md`](Robot/README.md)) |
| `Documentos/` | Anteproyecto, entregables semanales y guías operativas |
| `Documentos/Evidencia/` | Capturas, registros de terminal e informes de sesión. Cada archivo con su pie de foto en [`Documentos/Evidencia/README.md`](Documentos/Evidencia/README.md): qué muestra, de cuándo es y qué afirmación sostiene |
| `herramientas/` | Verificadores y utilidades (ver abajo) |
| `*.world` | Mundos de Gazebo. El vigente es `mundo_definitivo.world` desde el 2026-08-20, y es también el **entorno de evaluación de OE4**: los dos pisos son dos pasillos distintos, uno al lado del otro en Y —piso 1 arriba (eje y≈10,0), piso 2 abajo (eje y≈−4,5)—, no una planta duplicada en altura. Cada robot corre en su propio `gzserver` con su `ROS_DOMAIN_ID`, así que nunca comparten escena y no hace falta elevar un nivel. Sustituye a `primer_piso_dos_niveles.world`, que hacía lo segundo y queda como referencia |
| `USTA_WORLD/`, `pasillo_grande/`, `pasillo_usta/` | Modelos SDF de entornos |
| `ESTADO.md` | Tablero de avance, riesgos y decisiones |

### Las herramientas

Ninguna levanta Gazebo ni ningún nodo, y todas devuelven código de salida distinto de
cero cuando fallan, de modo que se pueden encadenar:

| Herramienta | Responde a |
|---|---|
| `verificar_instalacion.sh` | ¿el código compila y funciona **en este equipo**? (31 comprobaciones) |
| `verificar_repositorio.sh` | ¿los documentos dicen la verdad y las rutas no son las de una máquina concreta? (11 comprobaciones) |
| `verificar_mapa.py` | ¿este mapa representa de verdad la geometría de su `.world`? |
| `verificar_contrato.py` | ¿la simulación cumple el contrato de interfaces? (requiere la simulación corriendo) |
| `medir_rtf.py` | ¿a qué fracción del tiempo real corre la simulación? (requiere la simulación corriendo) |
| `lanzar_sim.sh` | limpia procesos huérfanos de Gazebo y lanza la simulación |

El segundo existe porque el primero no cubría nada de lo escrito: había 30 comprobaciones
sobre el código y ninguna sobre la documentación, así que el código convergía y los
documentos divergían.

---

## Plataforma robótica

El modelo de vehículo proviene del proyecto open source
[AWS DeepRacer](https://github.com/aws-deepracer/aws-deepracer), migrado de ROS 2 Foxy a
Humble. Las modificaciones realizadas y la justificación del cambio de plataforma respecto
al anteproyecto están documentadas en [`Robot/README.md`](Robot/README.md).

El código de terceros conserva su licencia original Apache 2.0, junto con los archivos
`LICENSE` y `NOTICE`.

---

## Autores

- Santiago Hernández Ávila
- Jonny Alejandro Mejía León

**Directores:** Ing. Armando Mateus Rojas, MSc. · Ing. Nestor Ivan Ospina, MSc. ·
Ing. Oscar Mauricio Gélvez Lizarazo, MSc.
