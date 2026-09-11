# Plan de implementación — RF-28, confirmación del usuario en la transición entre pisos

> **Para quien ejecute el plan:** las tareas van en orden y cada una termina en algo
> verificable. Los pasos usan casillas (`- [ ]`). **Tras la Tarea 4 el sistema ya se puede
> probar de verdad en simulación**; las tareas 5 y 6 son regresión y documentación.

**Objetivo:** que una misión entre pisos no arranque el tramo 2 hasta que el usuario confirme
desde la interfaz que ya subió, con alerta a los 60 s y fallo a los 120 s.

**Arquitectura:** el coordinador, al terminar el tramo cuya etapa es `TRANSFERENCIA`, entra en
un bucle de espera que publica la etapa nueva `ESPERANDO_CONFIRMACION = 7` y vigila un tópico
`/coordinacion/confirmacion_piso`. La política de plazos y el enganche de la confirmación viven
en un módulo nuevo **sin ROS**, `espera_confirmacion.py`, para poder probarlos sin simulador.
El planificador no cambia.

**Pila:** ROS 2 Humble, Python 3.10, `rclpy`, `std_msgs/String`, `rosbridge_suite`, JavaScript
sin dependencias en la HRI.

**Diseño de referencia:** `Documentos/DISENO_CONFIRMACION_PISO.md`. Si este plan y ese
documento se contradicen, manda el documento.

## Restricciones globales

- **La confirmación es obligatoria en simulación y en físico, por un solo camino de código.**
  Prohibido un parámetro que salte la rama (RF-16 / decisión D6).
- **Alerta a los 60,0 s. Plazo máximo 120,0 s.** Contados desde que Nav2 confirma la llegada de
  robot2 a su punto de transferencia.
- **Los plazos se miden con `time.time()`** (reloj de pared). Las **marcas** que van al bag se
  siguen sellando con `self._ahora()`. Los dos usos están separados a propósito; ver §4 del
  diseño y el docstring de `_esperar` en `coordinador.py:486-491`.
- **La marca de etapa 7 publica `robot_activo` no vacío** (el robot del piso de destino). Si
  queda vacío, `continuidad` (RF-24) se vuelve falsa en toda misión entre niveles.
- **La HRI habla solo con `/coordinacion`** (RF-19).
- **Todo el texto nuevo va en español**, y los comentarios de código sin tildes, como el resto
  de los archivos del paquete.
- **Los mensajes de commit van en español y sin `Co-Authored-By`.**
- **No empujar nada** hasta completar la batería de verificación del repositorio.
- **RF-28 es funcionalidad añadida, así que la campaña de 30 misiones NO se reejecuta.** Las
  pruebas que este plan manda correr son las del repositorio (que se corren siempre, en cada
  tarea, porque son de segundos) y las tres corridas nuevas de la tarea 7, que son la evidencia
  del comportamiento nuevo. Nada de volver a grabar lo ya grabado: el argumento fila por fila
  está en la §5 del diseño. Si en algún momento una tarea parece exigir repetir una campaña
  anterior, esa tarea está mal escrita — pararse y revisarla.

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg` | el vocabulario de etapas que viaja por el cable |
| `Robot/aws-deepracer/coordinacion/coordinacion/planificador.py` | copia sin ROS del vocabulario de etapas |
| `Robot/aws-deepracer/coordinacion/coordinacion/registrador.py` | nombres de etapa en el registro |
| `Robot/aws-deepracer/coordinacion/coordinacion/espera_confirmacion.py` | **nuevo.** Política de plazos + enganche. Sin ROS |
| `Robot/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py` | **nuevo.** Prueba del anterior |
| `Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py` | cableado ROS: tópico, marcas, bucle |
| `interfaz_web/js/rosbridge.js` | saber publicar un tópico |
| `interfaz_web/js/app.js` | etapa 7 en el panel y el botón de confirmar |
| `interfaz_web/index.html`, `interfaz_web/css/estilo.css` | el botón y su estilo |
| `Documentos/CONTRATO_INTERFACES.md`, `Documentos/REQUISITOS.md` | el contrato y RF-28 |

---

## Tarea 1: La etapa nueva, sincronizada en los tres sitios

**Archivos:**
- Modificar: `Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg` (al final del bloque de constantes, tras la línea 29)
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/planificador.py:68`
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/registrador.py:72-73`
- Prueba: `Robot/aws-deepracer/coordinacion/test/prueba_planificador.py` (caso 9, ya existe)

**Interfaces:**
- Produce: la constante `ESPERANDO_CONFIRMACION = 7` importable desde
  `coordinacion.planificador`, y `EstadoMision.ESPERANDO_CONFIRMACION` desde el mensaje
  compilado. La entrada `7: "ESPERANDO_CONFIRMACION"` en `registrador.ETAPAS`.

**Por qué la constante va en tres archivos y no en uno:** `planificador.py:57-59` deja escrito
que duplica los números a propósito, para no importar `coordinacion_msgs` y poder probarse sin
ROS. El caso 9 de `prueba_planificador.py` lee el `.msg` línea por línea y compara con los
atributos del módulo, así que una desincronización no pasa callada.

- [ ] **Paso 1: añadir la constante solo al mensaje**

En `coordinacion_msgs/msg/EstadoMision.msg`, después de la línea 29 (`uint8 RECIBIDA=6`) y
antes de la línea en blanco que precede a `string mision_id`:

```
# ESPERANDO_CONFIRMACION es la pausa del §4 de DISENO_CONFIRMACION_PISO.md: el robot del
# piso de destino ya esta en su escalera y la mision no arranca el tramo 2 hasta que el
# usuario confirme que subio. Se anade el 2026-09-10 (RF-28), a peticion del director.
#
# Va al final y con numero nuevo por la misma razon que RECIBIDA=6: las constantes no
# viajan por el cable, asi que la serializacion no cambia y un suscriptor ya compilado
# sigue deserializando. Solo vera un valor de etapa que no conoce.
#
# La marca de esta etapa lleva 'robot_activo' con el robot del piso de destino, NUNCA
# vacio: es la condicion que mantiene cierta la continuidad del RF-24.
uint8 ESPERANDO_CONFIRMACION=7
```

- [ ] **Paso 2: correr la prueba de sincronía y verla fallar**

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && python3 src/aws-deepracer/coordinacion/test/prueba_planificador.py
```

Esperado: **FALLA** en el caso 9 con `AttributeError: module 'coordinacion.planificador' has
no attribute 'ESPERANDO_CONFIRMACION'`. Eso es la prueba haciendo su trabajo: el `.msg` tiene
una constante que el `.py` no.

Si en cambio pasa, la prueba no está leyendo el `.msg` que editaste: comprueba la ruta que
construye en su línea 188 y que no estés editando una copia.

- [ ] **Paso 3: añadir la constante al planificador**

En `planificador.py`, justo después de la línea 68 (`RECIBIDA = 6`):

```python
# La pausa en la que la mision espera que el usuario confirme que ya cambio de piso.
# Ver Documentos/DISENO_CONFIRMACION_PISO.md.
ESPERANDO_CONFIRMACION = 7
```

- [ ] **Paso 4: correr la prueba y verla pasar**

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && python3 src/aws-deepracer/coordinacion/test/prueba_planificador.py
```

Esperado: `Todas las comprobaciones pasan`, código de salida 0.

- [ ] **Paso 5: añadir el nombre al registrador**

En `registrador.py`, sustituir las líneas 72-73 por:

```python
ETAPAS = {0: "INACTIVA", 1: "TRAMO_1", 2: "TRANSFERENCIA", 3: "TRAMO_2",
          4: "COMPLETADA", 5: "FALLIDA", 6: "RECIBIDA",
          7: "ESPERANDO_CONFIRMACION"}
```

Sin esta entrada, `marca()` cae en su `ETAPAS.get(etapa, str(etapa))` (línea 106) y el registro
escribiría `"etapa": "7"`: un número donde el esquema y todo el análisis esperan un nombre.

- [ ] **Paso 6: comprobar que el registrador sigue intacto**

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && python3 src/aws-deepracer/coordinacion/test/prueba_registrador.py
```

Esperado: 0 en `[MAL]`, código de salida 0.

- [ ] **Paso 7: commit**

```bash
cd ~/Documents/Tesis && git add Robot/aws-deepracer/coordinacion_msgs/msg/EstadoMision.msg Robot/aws-deepracer/coordinacion/coordinacion/planificador.py Robot/aws-deepracer/coordinacion/coordinacion/registrador.py && git commit -m "RF-28: la etapa ESPERANDO_CONFIRMACION existe en los tres sitios que la nombran"
```

---

## Tarea 2: La política de plazos y el enganche, sin ROS

**Archivos:**
- Crear: `Robot/aws-deepracer/coordinacion/coordinacion/espera_confirmacion.py`
- Crear: `Robot/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py`

**Interfaces:**
- Consume: nada. Módulo autónomo, sin importar ROS ni el resto del paquete.
- Produce, para la Tarea 3:
  - `ALERTA_S = 60.0` y `PLAZO_S = 120.0`, constantes de módulo.
  - `fase(transcurrido_s, alerta_s=ALERTA_S, plazo_s=PLAZO_S) -> str`, que devuelve
    exactamente una de las cadenas `"esperando"`, `"alerta"` o `"agotada"`.
  - `class Enganche` con `reiniciar(mision_id)`, `recibir(mision_id)` y
    `consumir(mision_id) -> bool`.

**Por qué un archivo aparte:** es la única parte de RF-28 que se puede probar en un segundo y
sin simulador. Dentro de `coordinador.py` quedaría atada a `rclpy` y solo sería comprobable
corriendo Gazebo, que es justo lo que hace que los errores de plazos se descubran tarde.

- [ ] **Paso 1: escribir la prueba, que todavía no puede pasar**

Crear `Robot/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py`:

```python
#!/usr/bin/env python3
"""Agota la politica de plazos y el enganche de RF-28. Sin ROS y sin simulador.

    python3 src/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py

Por que existe. Los dos fallos que esta logica puede tener son invisibles en una
corrida suelta: una alerta que se reemite en cada tick del bucle -y llena el bag
de marcas- y una confirmacion que llega antes de que nadie escuche -y deja al
usuario esperando 120 s un plazo que ya cumplio-. Ninguno de los dos da error.
Aqui se fuerzan los dos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coordinacion.espera_confirmacion import (  # noqa: E402
    ALERTA_S, PLAZO_S, Enganche, fase)

OK = FALLOS = 0


def comprueba(titulo, condicion, detalle=""):
    global OK, FALLOS
    if condicion:
        OK += 1
        print(f"  [OK ] {titulo} {detalle}")
    else:
        FALLOS += 1
        print(f"  [MAL] {titulo} {detalle}")


def main():
    print("\n1. Los plazos son los que pidio el director")
    comprueba("la alerta es a los 60 s", ALERTA_S == 60.0, f"-> {ALERTA_S}")
    comprueba("el plazo maximo es 120 s", PLAZO_S == 120.0, f"-> {PLAZO_S}")

    print("\n2. Las tres fases, y sus bordes exactos")
    comprueba("en 0 s se espera", fase(0.0) == "esperando")
    comprueba("en 59,9 s todavia se espera", fase(59.9) == "esperando")
    comprueba("en 60,0 s exactos ya hay alerta", fase(60.0) == "alerta")
    comprueba("en 119,9 s sigue en alerta", fase(119.9) == "alerta")
    comprueba("en 120,0 s exactos se agota", fase(120.0) == "agotada")
    comprueba("en 120,1 s sigue agotada", fase(120.1) == "agotada")

    print("\n3. Un tiempo negativo no inventa una fase")
    # Puede pasar si el reloj da un salto atras. Mejor 'esperando' que 'agotada':
    # un salto de reloj no debe matar una mision en curso.
    comprueba("un transcurrido negativo se trata como espera",
              fase(-5.0) == "esperando")

    print("\n4. Los plazos se pueden estrechar para probar sin esperar 2 minutos")
    comprueba("con plazos cortos, 1,5 s ya es alerta",
              fase(1.5, alerta_s=1.0, plazo_s=3.0) == "alerta")
    comprueba("con plazos cortos, 3,0 s ya es agotada",
              fase(3.0, alerta_s=1.0, plazo_s=3.0) == "agotada")

    print("\n5. El enganche solo honra la mision en curso")
    e = Enganche()
    e.reiniciar("m1")
    comprueba("sin confirmacion no hay nada que consumir",
              e.consumir("m1") is False)

    e.recibir("m1")
    comprueba("una confirmacion de la mision en curso se consume",
              e.consumir("m1") is True)
    comprueba("y no se puede consumir dos veces",
              e.consumir("m1") is False)

    print("\n6. Una confirmacion de otra mision se ignora")
    e = Enganche()
    e.reiniciar("m2")
    e.recibir("m1")
    comprueba("llega 'm1' mientras corre 'm2': no sirve",
              e.consumir("m2") is False)

    print("\n7. Una pulsacion vieja no auto-confirma la mision siguiente")
    # El caso real: el usuario pulsa confirmar al final de la mision anterior y
    # ese mensaje queda guardado. Sin reiniciar(), la mision siguiente arrancaria
    # el tramo 2 sin preguntar a nadie.
    e = Enganche()
    e.reiniciar("m1")
    e.recibir("m1")
    e.reiniciar("m2")
    comprueba("tras reiniciar, la confirmacion anterior no vale",
              e.consumir("m2") is False)

    print("\n8. La confirmacion temprana se engancha y se honra")
    # El usuario sube rapido y pulsa mientras robot2 todavia va hacia su
    # escalera. Si esto no funcionara, esperaria los 120 s completos.
    e = Enganche()
    e.reiniciar("m1")
    e.recibir("m1")          # llega durante TRANSFERENCIA, nadie espera aun
    comprueba("la confirmacion adelantada sigue valida al llegar la espera",
              e.consumir("m1") is True)

    print("\n9. Un mision_id vacio no confirma nada")
    # Un mensaje mal formado, o el tick de una HRI recien cargada.
    e = Enganche()
    e.reiniciar("m1")
    e.recibir("")
    comprueba("una confirmacion sin mision_id se ignora",
              e.consumir("m1") is False)

    print("\n" + "=" * 62)
    print(f"{OK} comprobaciones pasan, {FALLOS} fallan.")
    print("=" * 62)
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Paso 2: correr la prueba y verla fallar**

```bash
cd ~/deepracer_sim_ws && python3 src/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py
```

Esperado: **FALLA** con `ModuleNotFoundError: No module named
'coordinacion.espera_confirmacion'`. No hace falta `source` del overlay: la prueba añade el
directorio del paquete a `sys.path` por sí misma (igual que `prueba_registrador.py`).

- [ ] **Paso 3: escribir el módulo**

Crear `Robot/aws-deepracer/coordinacion/coordinacion/espera_confirmacion.py`:

```python
#!/usr/bin/env python3
"""Politica de plazos y enganche de la confirmacion de piso (RF-28).

Sin ROS a proposito, igual que planificador.py: asi se prueba en un segundo con
test/prueba_espera_confirmacion.py y no hace falta Gazebo para saber si los
plazos estan bien. El cableado -el topico, las marcas, el bucle- vive en
coordinador.py.

Ver Documentos/DISENO_CONFIRMACION_PISO.md.
"""

# Los dos plazos, en segundos de RELOJ DE PARED. Decididos el 2026-09-10 con el
# director: aviso al minuto, corte a los dos minutos.
#
# De pared y no de simulacion, y esto no es un detalle: quien sube las escaleras
# es una persona real en los dos bancos, asi que su paciencia se mide en
# segundos reales. Con RTF 0,5 estos 120 s de simulacion serian 240 s de espera
# real. Y si Gazebo muere durante la espera, /clock se detiene y un plazo medido
# en tiempo de simulacion no venceria NUNCA: el coordinador se colgaria justo en
# el caso para el que existe el plazo. Es el mismo razonamiento del docstring de
# _esperar() en coordinador.py.
ALERTA_S = 60.0
PLAZO_S = 120.0


def fase(transcurrido_s, alerta_s=ALERTA_S, plazo_s=PLAZO_S):
    """En que fase esta una espera que lleva 'transcurrido_s' segundos.

    Devuelve "esperando", "alerta" o "agotada". Los limites son cerrados por
    abajo: a los 60,0 s exactos ya es "alerta", y a los 120,0 s ya es "agotada".

    Un 'transcurrido_s' negativo devuelve "esperando". Solo puede venir de un
    salto del reloj hacia atras, y ante eso es mejor seguir esperando que matar
    una mision en curso.
    """
    if transcurrido_s >= plazo_s:
        return "agotada"
    if transcurrido_s >= alerta_s:
        return "alerta"
    return "esperando"


class Enganche:
    """Retiene la confirmacion del usuario hasta que alguien la consuma.

    EL FALLO QUE ESTO IMPIDE. El usuario puede subir mas rapido que el robot del
    piso de destino y pulsar 'ya estoy arriba' mientras ese robot todavia va
    hacia su escalera, es decir antes de que exista la espera. Sin enganche ese
    mensaje no lo recoge nadie y el usuario agota los 120 s completos habiendo
    cumplido su parte en 10 s.

    Y EL FALLO QUE IMPIDE AL REVES. Una confirmacion de una mision anterior no
    puede servir para la siguiente, o la siguiente arrancaria su tramo 2 sin
    preguntarle nada a nadie. De ahi que se guarde el mision_id y que
    reiniciar() lo borre al empezar cada mision.
    """

    def __init__(self):
        self._mision = None        # la mision en curso, o None
        self._confirmada = None    # la mision cuya confirmacion esta retenida

    def reiniciar(self, mision_id):
        """Empieza una mision. Descarta cualquier confirmacion retenida."""
        self._mision = mision_id
        self._confirmada = None

    def recibir(self, mision_id):
        """Llego un mensaje al topico. Se retiene solo si es de esta mision."""
        if mision_id and mision_id == self._mision:
            self._confirmada = mision_id

    def consumir(self, mision_id):
        """¿Hay confirmacion para 'mision_id'? La gasta si la hay."""
        if self._confirmada is not None and self._confirmada == mision_id:
            self._confirmada = None
            return True
        return False
```

- [ ] **Paso 4: correr la prueba y verla pasar**

```bash
cd ~/deepracer_sim_ws && python3 src/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py
```

Esperado: `18 comprobaciones pasan, 0 fallan.`, código de salida 0.

Las 18 son: 2 de los plazos, 6 de los bordes de fase, 1 del tiempo negativo, 2 de los plazos
estrechados, 3 del enganche básico, y 1 por cada uno de los grupos 6 a 9. Si sale otro número,
se pegó el archivo a medias.

- [ ] **Paso 5: commit**

```bash
cd ~/Documents/Tesis && git add Robot/aws-deepracer/coordinacion/coordinacion/espera_confirmacion.py Robot/aws-deepracer/coordinacion/test/prueba_espera_confirmacion.py && git commit -m "RF-28: la politica de plazos y el enganche, probables sin simulador"
```

---

## Tarea 3: El coordinador espera la confirmación

**Archivos:**
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py` (importaciones línea 45-48; `__init__` tras la línea 130; el bucle de tramos en 233-257; un método nuevo)

**Interfaces:**
- Consume: `ALERTA_S`, `PLAZO_S`, `Enganche`, `fase` de `coordinacion.espera_confirmacion`;
  `ESPERANDO_CONFIRMACION` y `TRANSFERENCIA` de `coordinacion.planificador`.
- Produce: el tópico `/coordinacion/confirmacion_piso` (`std_msgs/String`, contenido =
  `mision_id`), con un suscriptor en este nodo. Y marcas de etapa 7 en
  `/coordinacion/estado_mision`.

- [ ] **Paso 1: añadir las importaciones**

En `coordinador.py`, sustituir el bloque de las líneas 45-48 por:

```python
from coordinacion.planificador import (
    ASIGNACION_POR_DEFECTO, COMPLETADA, ErrorPlanificacion,
    ESPERANDO_CONFIRMACION, FALLIDA, INACTIVA, RECIBIDA, TRANSFERENCIA,
    condicion_de, generar_mision_id, planificar, yaw_a_cuaternion,
)
from coordinacion.espera_confirmacion import ALERTA_S, PLAZO_S, Enganche, fase
```

`TRANSFERENCIA` no estaba importado: hasta ahora el coordinador nunca necesitó distinguir ese
tramo de los demás.

Y añadir `from std_msgs.msg import String` junto a las otras importaciones de mensajes, después
de la línea 35 (`from nav_msgs.msg import Odometry`).

- [ ] **Paso 2: declarar la dependencia del paquete**

En `Robot/aws-deepracer/coordinacion/package.xml`, justo después de la línea
`<exec_depend>nav_msgs</exec_depend>`, añadir:

```xml
  <exec_depend>std_msgs</exec_depend>
```

**`exec_depend` y no `depend`**: el archivo declara las siete dependencias que ya tiene con
`exec_depend`, porque es un paquete `ament_python` y no compila nada. Mezclar `depend` aquí
funcionaría, pero rompería la uniformidad del archivo sin ganar nada.

Comprobar que quedó, y que no estaba ya:

```bash
grep -n "std_msgs" Robot/aws-deepracer/coordinacion/package.xml
```

Sin esta línea el paquete funciona hoy por accidente —`nav_msgs` arrastra `std_msgs` al
entorno— y se rompería el día que alguien quite `nav_msgs`.

- [ ] **Paso 3: crear el enganche y la suscripción**

En `__init__`, justo después del bloque del `ActionServer` (línea 130) y antes del
`self.get_logger().info("Coordinador listo...")`:

```python
        # RF-28. El usuario avisa por aqui de que ya cambio de piso. Topico y no
        # servicio a proposito: 'ros2 bag' NO graba servicios, y el instante de
        # la confirmacion tiene que quedar en el bag para poder comprobarlo
        # despues. Es la misma razon por la que origen_id y destino_id estan en
        # EstadoMision y no solo en el goal.
        self.enganche = Enganche()
        self.create_subscription(
            String, "/coordinacion/confirmacion_piso",
            self._confirmacion, 10, callback_group=self.grupo)
```

**El `callback_group=self.grupo` no es decoración: de él depende que RF-28 funcione.** El bucle
de espera del paso 6 bloquea dentro de `_ejecutar`, que es el `execute_callback` de la acción.
Si la suscripción cayera en el grupo mutuamente excluyente por defecto, su callback no podría
ejecutarse mientras `_ejecutar` tiene el turno, el mensaje del usuario no se procesaría nunca y
**la espera se agotaría siempre a los 120 s**, con la HRI haciendo su parte bien. Funciona
porque `self.grupo` es un `ReentrantCallbackGroup` (`coordinador.py:98`) y el executor es
`MultiThreadedExecutor` (`coordinador.py:568`). Si alguien cambia cualquiera de esas dos cosas,
esto se rompe en silencio.

- [ ] **Paso 4: escribir el callback del tópico**

Añadir este método justo antes de `_marcar` (antes de la línea 326):

```python
    def _confirmacion(self, msg):
        """El usuario dice que ya cambio de piso (RF-28)."""
        self.enganche.recibir(msg.data)
        self.get_logger().info(f"confirmacion de piso recibida: '{msg.data}'")
```

Se registra en el log aunque el `mision_id` no case: un mensaje que llega y no sirve es
exactamente lo que hay que poder ver cuando la espera no avanza.

- [ ] **Paso 5: reiniciar el enganche al arrancar cada misión**

En `_ejecutar`, después de la **línea 204**, que es donde cierra la llamada a `RegistroMision`
que empieza en la 201 (la llamada ocupa cuatro líneas, 201-204; el final es
`t_solicitud=t0, condicion=self.condicion) if self.ruta_registros else None`), y antes del
`self.get_logger().info(f"Mision: ...")` de la línea 206:

```python
        # Cualquier confirmacion anterior deja de valer: si no, una pulsacion
        # tardia de la mision pasada arrancaria el tramo 2 de esta sin preguntar.
        self.enganche.reiniciar(mision_id)
```

- [ ] **Paso 6: escribir el bucle de espera**

Añadir este método justo después de `_navegar` (es decir, después de la línea 481,
`return True, ""`, y antes de `def _esperar`):

```python
    def _esperar_confirmacion(self, tramo, goal_handle, mision_id):
        """La pausa de RF-28: el tramo 2 no arranca sin el visto bueno del usuario.

        Devuelve (True, "") si el usuario confirmo, y (False, motivo) si se
        agoto el plazo o se cancelo la mision.

        El robot que espera es el del piso de DESTINO -el tramo de
        TRANSFERENCIA ya es suyo, porque mientras el usuario sube el conduce
        hasta su escalera-, y se publica en 'robot_activo' siempre lleno: con
        ese campo vacio la continuidad del RF-24 se vuelve falsa en toda mision
        entre niveles.
        """
        nivel = tramo.punto.get("nivel", "")
        if self.enganche.consumir(mision_id):
            self.get_logger().info(
                "    el usuario ya habia confirmado antes de que el robot "
                "llegara: se sigue sin esperar")
            return True, ""

        self._marcar(ESPERANDO_CONFIRMACION, tramo.robot, tramo.punto,
                     f"¿Ya esta en el piso {nivel}? Confirmelo para continuar.",
                     mision_id)
        self._feedback(goal_handle)
        self.get_logger().info(
            f"    esperando confirmacion del usuario (alerta a {ALERTA_S:.0f} s, "
            f"plazo {PLAZO_S:.0f} s)")

        # time.time() y no self._ahora(): ver el docstring de _esperar y la §4
        # del diseno. El plazo es de paciencia humana, y si Gazebo muere /clock
        # se para y un plazo en tiempo de simulacion no venceria nunca.
        t0 = time.time()
        avisado = False
        while True:
            if goal_handle.is_cancel_requested:
                # Inerte mientras el servidor no registre un cancel_callback
                # -hoy rclpy rechaza toda cancelacion por defecto-, pero queda
                # correcto para cuando se arregle.
                return False, "Cancelada por el usuario durante la espera"

            if self.enganche.consumir(mision_id):
                espera = time.time() - t0
                self.get_logger().info(
                    f"    confirmado por el usuario tras {espera:.1f} s")
                return True, ""

            estado = fase(time.time() - t0)
            if estado == "agotada":
                return False, (
                    f"el usuario no confirmo la llegada al piso {nivel} en "
                    f"{PLAZO_S:.0f} s")
            if estado == "alerta" and not avisado:
                # UNA sola vez, no en cada vuelta del bucle: a 20 Hz serian
                # 1200 marcas por minuto en el bag y el conteo de transiciones
                # dejaria de significar nada.
                avisado = True
                restante = PLAZO_S - ALERTA_S
                self._marcar(
                    ESPERANDO_CONFIRMACION, tramo.robot, tramo.punto,
                    f"Seguimos esperando su confirmacion. Quedan "
                    f"{restante:.0f} segundos.", mision_id)
                self._feedback(goal_handle)
                self.get_logger().warn(
                    f"    alerta: {ALERTA_S:.0f} s sin confirmacion")

            time.sleep(0.05)
```

- [ ] **Paso 7: enganchar la espera al bucle de tramos**

En `_ejecutar`, dentro del `for` de los tramos, entre el bloque `if not ok:` que termina en la
línea 257 (`return self._cerrar_registro(res, tramo.punto)`) y la línea 259
(`destino = next(...)`), añadir —con la indentación del cuerpo del `for`, cuatro niveles—:

```python
            # RF-28. Terminado el tramo de TRANSFERENCIA el robot del piso de
            # destino ya esta en su escalera, pero el usuario puede no haber
            # subido todavia. Sin esta pausa el tramo 2 arrancaba solo y la
            # mision podia completarse con el usuario en el otro piso.
            if tramo.etapa == TRANSFERENCIA:
                ok, motivo = self._esperar_confirmacion(
                    tramo, goal_handle, mision_id)
                if not ok:
                    self._marcar(FALLIDA, tramo.robot, tramo.punto,
                                 f"Mision detenida: {motivo}", mision_id)
                    self._feedback(goal_handle)
                    goal_handle.abort()
                    res.exito, res.motivo_fallo = False, motivo
                    res.tiempo_total_s = self._ahora() - t0
                    res.num_relevos = relevos
                    return self._cerrar_registro(res, tramo.punto)
```

Cuidado con dos cosas al pegarlo: tiene que quedar **dentro** del `for`, y el `t0` que usa
`res.tiempo_total_s` es el de `_ejecutar` (el inicio de la misión), que es distinto del `t0`
local de `_esperar_confirmacion` (el inicio de la espera). No renombrar ninguno de los dos.

- [ ] **Paso 8: compilar**

```bash
cd ~/deepracer_sim_ws && source /opt/ros/humble/setup.bash && colcon build --symlink-install --packages-select coordinacion_msgs coordinacion
```

Esperado: `Summary: 2 packages finished`, 0 con error. `coordinacion_msgs` va primero porque
la constante nueva del `.msg` tiene que regenerarse antes de que `coordinacion` la use.

- [ ] **Paso 9: comprobar que la constante llegó al mensaje compilado**

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && python3 -c "from coordinacion_msgs.msg import EstadoMision; print(EstadoMision.ESPERANDO_CONFIRMACION)"
```

Esperado: `7`. Si sale `AttributeError`, el `colcon build` reutilizó artefactos viejos: borrar
`build/coordinacion_msgs` e `install/coordinacion_msgs` y repetir el paso 8.

- [ ] **Paso 10: arrancar el coordinador solo y ver que escucha el tópico**

El coordinador arranca sin Gazebo ni Nav2 —sus clientes de `navigate_to_pose` no esperan a
nadie hasta que hay misión—, así que esto se comprueba en una terminal sin simulador. En la
primera:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p prefijo_mision:=PRUEBARF28
```

Esperado: termina imprimiendo `Coordinador listo.` con el número de puntos.

En una segunda terminal:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic info /coordinacion/confirmacion_piso
```

Esperado: `Type: std_msgs/msg/String`, `Publisher count: 0`, **`Subscription count: 1`**. Si
sale 0 suscriptores, el `create_subscription` del paso 3 no se ejecutó: revisar que quedó
dentro de `__init__` y antes del `return`.

- [ ] **Paso 11: comprobar que el callback recibe**

Con el coordinador del paso anterior todavía vivo, en la segunda terminal:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic pub --once /coordinacion/confirmacion_piso std_msgs/msg/String "{data: 'prueba'}"
```

Esperado: en la terminal del coordinador aparece
`confirmacion de piso recibida: 'prueba'`. Después, parar el coordinador con `Ctrl-C`.

Que no confirme nada es lo correcto: no hay misión en curso, así que `Enganche.recibir`
descarta el `mision_id` por no coincidir. El log demuestra que el cable está puesto.

- [ ] **Paso 12: commit**

```bash
cd ~/Documents/Tesis && git add Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py Robot/aws-deepracer/coordinacion/package.xml && git commit -m "RF-28: el tramo 2 no arranca sin que el usuario confirme el cambio de piso"
```

---

## Tarea 4: La interfaz publica la confirmación y entiende la etapa 7

**Archivos:**
- Modificar: `interfaz_web/js/rosbridge.js` (constructor línea 14-23; `onopen` línea 27-32; método nuevo tras la línea 100)
- Modificar: `interfaz_web/js/app.js` (líneas 16-17, 103-108, 176-190; bloque de eventos)
- Modificar: `interfaz_web/index.html:46-49`
- Modificar: `interfaz_web/css/estilo.css` (tras la línea 118)

**Interfaces:**
- Consume: el tópico `/coordinacion/confirmacion_piso` (`std_msgs/String`, contenido =
  `mision_id`) y la etapa `7` de `EstadoMision`, ambos de la Tarea 3.
- Produce: `Puente.publicar(topic, type, msg)` en `rosbridge.js`.

- [ ] **Paso 1: que el puente sepa publicar**

En `rosbridge.js`, en el constructor, después de la línea 19
(`this.acciones = new Map();`):

```js
    this.publicados = new Map();    // topic -> type, para re-anunciar al reconectar
```

En `onopen`, después de la línea que vuelve a pedir las suscripciones, añadir:

```js
      // Un socket nuevo tampoco hereda los anuncios de publicacion.
      for (const [topic, type] of this.publicados) this._enviar({ op: "advertise", topic, type });
```

Y al final de la clase, después de `cancelarMeta` (línea 98-100):

```js
  /** Publica en un topico. Lo anuncia la primera vez y al reconectar. */
  publicar(topic, type, msg) {
    if (!this.publicados.has(topic)) {
      this.publicados.set(topic, type);
      this._enviar({ op: "advertise", topic, type });
    }
    this._enviar({ op: "publish", topic, msg });
  }
```

El `advertise` y el `publish` salen por el mismo socket y en ese orden, y rosbridge los
procesa en orden de llegada, así que no hace falta esperar entre los dos.

- [ ] **Paso 2: añadir la etapa 7 al vocabulario de la HRI**

En `app.js`, sustituir las líneas 16-17 por:

```js
const ETAPA = { INACTIVA: 0, TRAMO_1: 1, TRANSFERENCIA: 2, TRAMO_2: 3, COMPLETADA: 4, FALLIDA: 5, RECIBIDA: 6, ESPERANDO_CONFIRMACION: 7 };
const NOMBRE_ETAPA = { 0: "INACTIVA", 1: "TRAMO_1", 2: "TRANSFERENCIA", 3: "TRAMO_2", 4: "COMPLETADA", 5: "FALLIDA", 6: "RECIBIDA", 7: "ESPERANDO_CONFIRMACION" };
```

Sin esto el panel escribe `desconocida (7)` en su etiqueta.

- [ ] **Paso 3: que el panel sepa qué decir en la etapa 7**

En `claveYTitulo`, añadir un caso **antes del `default`, que está en la línea 186**; es decir,
pegarlo tras la línea 185 (`? ["espera", "Espera al robot"] : ["sigueme", "Sígueme"];`), que
cierra el caso conjunto de `TRAMO_1`/`TRAMO_2`:

```js
    case ETAPA.ESPERANDO_CONFIRMACION: return ["confirmar", "¿Ya subió?"];
```

Sin este caso la etapa 7 cae en el `default` y el panel diría *«Sin misión activa»* en plena
misión, que es peor que no mostrar nada.

- [ ] **Paso 4: que la barra de etapas no se apague**

Sustituir la línea 190 y el cuerpo del `map` de `panel-etapas` (líneas 210-215) para que la
etapa 7 ilumine el paso del relevo:

```js
const ORDEN_ETAPAS = [[6, "Preparando"], [1, "Tramo 1"], [2, "Relevo"], [3, "Tramo 2"], [4, "Fin"]];
```

(la constante no cambia) y dentro del `map`, sustituir la línea 213 (`else if (n === e.etapa) clase += " on";`) por:

```js
    // La etapa 7 no tiene paso propio en la barra: es la pausa DENTRO del
    // relevo, asi que ilumina "Relevo" y el usuario no ve la barra apagarse.
    else if (n === e.etapa || (e.etapa === ETAPA.ESPERANDO_CONFIRMACION && n === 2)) clase += " on";
```

- [ ] **Paso 5: añadir el botón al HTML**

En `index.html`, sustituir el bloque de las líneas 46-49 por:

```html
  <div class="acciones">
    <button id="btn-ir" class="boton grande primario" type="button" disabled>Iniciar guiado</button>
    <button id="btn-cancelar" class="boton grande secundario" type="button" disabled>Cancelar</button>
  </div>
  <!-- RF-28: solo aparece en la etapa ESPERANDO_CONFIRMACION. Lo muestra app.js. -->
  <div class="acciones" id="acciones-confirmar" hidden>
    <button id="btn-confirmar" class="boton grande confirmar" type="button">Ya estoy en el otro piso</button>
  </div>
```

- [ ] **Paso 6: darle estilo al botón y al panel**

En `css/estilo.css`, después de la línea 118, añadir:

```css
.panel.confirmar::before { background: var(--ambar); } .panel.confirmar h2 { color: #ffd08a; }
.boton.confirmar { background: var(--ambar); color: #17110a; border-color: var(--ambar); }
```

Se reutiliza el ámbar que ya usa `.panel.espera`, porque es lo mismo que le pasa al usuario:
el sistema está parado esperándolo a él.

- [ ] **Paso 7: publicar al pulsar, y mostrar el botón solo en la etapa 7**

Primero, que el `mision_id` esté siempre disponible. `estado.ultimoEstadoMision` (declarado en
la línea 39) solo se rellena en la suscripción al tópico (línea 59); la llamada a `pintarPanel`
que viene del feedback de la acción (línea 148) **no lo actualiza**. Sustituir la línea 148 por:

```js
    { onFeedback: (valores) => { estado.ultimoEstadoMision = valores.estado; pintarPanel(valores.estado); }, onResult: alTerminar },
```

Sin esto el botón podría aparecer (lo pinta el feedback) con `ultimoEstadoMision` todavía en
`null`, y el `click` saldría por el `return` sin publicar nada: un botón que no hace nada y sin
error en pantalla, que es el peor fallo posible en esta pantalla.

Después del bloque del botón de cancelar (líneas 153-157), añadir:

```js
$("btn-confirmar").addEventListener("click", () => {
  const e = estado.ultimoEstadoMision;
  if (!e || !e.mision_id) return;
  // El mision_id va en el cuerpo para que el coordinador pueda descartar una
  // pulsacion de una mision anterior. Ver Enganche en espera_confirmacion.py.
  puente.publicar("/coordinacion/confirmacion_piso", "std_msgs/msg/String",
                  { data: e.mision_id });
  $("nota").textContent = "Confirmacion enviada.";
});
```

Y en `pintarPanel`, justo después de la línea 198 (`$("panel-frase").textContent = ...`):

```js
  // RF-28: el boton de confirmar existe solo mientras el coordinador lo espera.
  // Visible en cualquier otra etapa seria una forma de confirmar una mision que
  // no esta preguntando nada.
  $("acciones-confirmar").hidden = e.etapa !== ETAPA.ESPERANDO_CONFIRMACION;
```

Y en `pintarPanelSinDatos`, añadir la misma línea con `true` fijo, dentro del cuerpo de la
función (tras su primera línea `const panel = $("panel");`):

```js
  $("acciones-confirmar").hidden = true;
```

Sin esto, una pérdida de conexión en plena etapa 7 dejaría el botón en pantalla sin nadie
escuchando al otro lado.

- [ ] **Paso 8: comprobar que el JavaScript no tiene errores de sintaxis**

```bash
cd ~/Documents/Tesis && node --check interfaz_web/js/rosbridge.js && node --check interfaz_web/js/app.js && echo SINTAXIS_OK
```

Esperado: `SINTAXIS_OK`. Si `node` no está instalado, saltar este paso y confiar en la consola
del navegador del paso siguiente.

- [ ] **Paso 9: comprobar el botón contra el coordinador, sin simulador**

Tres terminales. En la primera, el coordinador:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 run coordinacion coordinador --ros-args -p prefijo_mision:=PRUEBARF28
```

En la segunda, rosbridge y el servidor de la página (el procedimiento del §4.1 de
`RUNBOOK_CAMPANA.md`). En la tercera, el escucha:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic echo /coordinacion/confirmacion_piso
```

En el navegador: la página carga, el LED queda verde. **El botón «Ya estoy en el otro piso» no
debe estar visible**, porque la etapa es INACTIVA. Eso ya es una comprobación.

Para forzar su aparición sin correr una misión, en la tercera terminal:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic pub --once /coordinacion/estado_mision coordinacion_msgs/msg/EstadoMision "{mision_id: 'FALSA_1', etapa: 7, robot_activo: 'robot2', mensaje_usuario: 'Prueba de etapa 7'}"
```

Esperado en el navegador: el panel se pone ámbar, el título dice **«¿Ya subió?»**, la etiqueta
dice `ESPERANDO_CONFIRMACION`, el paso «Relevo» de la barra queda iluminado, y **aparece el
botón**. Al pulsarlo, el `ros2 topic echo` imprime `data: FALSA_1`.

Si el panel dice «Sin misión activa», falta el paso 3. Si dice `desconocida (7)`, falta el
paso 2. Si el botón no aparece, falta el paso 7 o el `hidden` del HTML. Si el `echo` no imprime
nada, falta el `publicar` del paso 1: mirar la consola del navegador.

Nota: ese `estado_mision` falso lo publica `ros2 topic pub`, no el coordinador, y a 1 Hz el
coordinador lo sobrescribirá con su `INACTIVA`. Es normal que el panel alterne; basta con ver
el botón aparecer y el `echo` imprimir.

- [ ] **Paso 10: commit**

```bash
cd ~/Documents/Tesis && git add interfaz_web/js/rosbridge.js interfaz_web/js/app.js interfaz_web/index.html interfaz_web/css/estilo.css && git commit -m "RF-28: la interfaz publica la confirmacion de piso y dibuja la etapa 7"
```

---

## Tarea 5: Regresión — la etapa 7 no estropea ninguna métrica

**Archivos:**
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/registrador.py` (no el código: solo
  se verifica; ver el paso 1)
- Modificar: `Robot/aws-deepracer/coordinacion/test/prueba_registrador.py` (caso nuevo al final
  de `main`, antes del resumen)
- Modificar: `herramientas/prueba_componer_registro.py` (caso nuevo)

**Interfaces:**
- Consume: `registrador.ETAPAS[7]` de la Tarea 1 y `RegistroMision.marca` con `etapa=7`.
- Produce: nada que consuma otra tarea.

**Por qué esta tarea existe aunque el diseño ya razone que nada se rompe:** porque el
razonamiento está en un documento y la comprobación tiene que estar en un archivo que se
ejecuta. `continuidad` es la variable de respuesta principal de RF-24; un falso `true` o un
falso `false` ahí invalida la campaña entera.

- [ ] **Paso 1: escribir el caso de regresión en el registrador**

**Cuidado con la forma del archivo: `prueba_registrador.py` NO tiene `main()`.** Son 177 líneas
de código suelto a nivel de módulo, organizado en secciones numeradas (`# --- 1. relevo`, …,
`# --- 6. el archivo`), con `comprueba()` y `traza()` definidos arriba (líneas 26 y 38) y un
bloque de resumen en las últimas ocho líneas que hace `sys.exit(1)` si hay fallos. El código
nuevo va **como una sección 7, antes de ese bloque de resumen**, es decir antes del
`print("\n" + "=" * 62)` final.

Añadir al final del archivo, justo antes de ese `print`:

```python
# ------------------------------------------- 7. la espera de RF-28
# Que la pausa de la confirmacion no toque ninguna de las cuatro metricas. El
# razonamiento esta en la §5 de DISENO_CONFIRMACION_PISO.md; aqui se ejecuta.
# 'continuidad' es la variable de respuesta principal del RF-24: un falso true o
# un falso false ahi invalida la campana entera, asi que se comprueban los dos
# sentidos.
print("\n7. La pausa de confirmacion de piso no altera las metricas (RF-28)")

reg7 = RegistroMision("RF28_B_1", "piso1_etm1", "piso2_aula_307",
                      {"1": "robot1", "2": "robot2"}, t_solicitud=10.0)
reg7.marca(10.0, 6, "")                          # RECIBIDA, robot vacio por diseno
reg7.marca(10.2, 1, "robot1", "piso1_etm1")
traza(reg7, "robot1", 10.5, 0.5, [0.5] * 40)
reg7.marca(30.0, 2, "robot2", "piso2_escalera")
traza(reg7, "robot2", 30.5, 0.5, [0.5] * 20)
# La pausa, donde va de verdad: entre TRANSFERENCIA y TRAMO_2. Dos marcas,
# porque la segunda es la alerta del minuto.
reg7.marca(41.0, 7, "robot2", "piso2_escalera")
reg7.marca(101.0, 7, "robot2", "piso2_escalera")
reg7.marca(120.0, 3, "robot2", "piso2_aula_307")
traza(reg7, "robot2", 120.5, 0.5, [0.5] * 40)
reg7.marca(141.0, 4, "robot2", "piso2_aula_307")
reg7.cerrar(141.0, True, "", 1, {"x": 0.0, "y": 0.0, "yaw": 0.0})
m7 = reg7.metricas()

comprueba("la continuidad sigue cierta con la etapa 7 dentro de la ventana",
          m7["continuidad"] is True, f"-> {m7['continuidad']}")
# hueco_relevo_s mide desde el INICIO de la TRANSFERENCIA (t=30.0) hasta el
# primer movimiento de robot2 (t=30.5), asi que la espera, que viene despues, no
# puede tocarlo. Si saliera ~91 s, estaria midiendo desde la marca equivocada.
comprueba("el hueco de relevo no lo toca la espera",
          m7["hueco_relevo_s"] == 0.5, f"-> {m7['hueco_relevo_s']}")

nombres7 = [x["etapa"] for x in reg7.marcas if x["etapa_num"] == 7]
comprueba("la etapa 7 se escribe con nombre y no como numero",
          nombres7 == ["ESPERANDO_CONFIRMACION"] * 2, f"-> {nombres7}")

# Y el error que el diseno prohibe: etapa 7 con robot_activo vacio. TIENE que
# dar continuidad falsa. Si diera verdadera, la comprobacion del RF-24 no
# estaria mirando estas marcas y el requisito no estaria medido.
reg7b = RegistroMision("RF28_B_2", "piso1_etm1", "piso2_aula_307",
                       {"1": "robot1", "2": "robot2"}, t_solicitud=10.0)
reg7b.marca(10.0, 6, "")
reg7b.marca(10.2, 1, "robot1", "piso1_etm1")
traza(reg7b, "robot1", 10.5, 0.5, [0.5] * 40)
reg7b.marca(30.0, 2, "robot2", "piso2_escalera")
traza(reg7b, "robot2", 30.5, 0.5, [0.5] * 20)
reg7b.marca(41.0, 7, "", "piso2_escalera")       # el error, a proposito
reg7b.marca(120.0, 3, "robot2", "piso2_aula_307")
reg7b.marca(141.0, 4, "robot2", "piso2_aula_307")
reg7b.cerrar(141.0, True, "", 1, {"x": 0.0, "y": 0.0, "yaw": 0.0})

comprueba("un robot vacio en la etapa 7 SI rompe la continuidad",
          reg7b.metricas()["continuidad"] is False,
          f"-> {reg7b.metricas()['continuidad']}")
```

Las claves de `asignacion` van como cadenas (`{"1": ..., "2": ...}`) y no como enteros, igual
que en las otras seis secciones y que en el coordinador, que hace
`{str(k): v for k, v in self.asignacion.items()}` en su línea 203.

- [ ] **Paso 2: correr la prueba del registrador**

```bash
cd ~/deepracer_sim_ws && python3 src/aws-deepracer/coordinacion/test/prueba_registrador.py
```

Esperado: 0 en `[MAL]` y la última línea `Todas las comprobaciones pasan (N).`, código de
salida 0. Si *«la etapa 7 se escribe con nombre»* falla, falta el paso 5 de la Tarea 1. Si
*«un robot vacio en la etapa 7 SI rompe la continuidad»* falla, la comprobación de RF-24 no
está mirando estas marcas y hay que leer `registrador.py:195-200` antes de seguir: sin eso, la
regla D-C4 del diseño no está verificada por nada.

- [ ] **Paso 3: el mismo caso en el compositor que lee del bag**

Va **al final de la función `pruebas_de_continuidad()`**, que ocupa las líneas 458-581 de
`herramientas/prueba_componer_registro.py`; es decir, pegarlo como último bloque de esa función,
justo antes de `def pruebas_de_escenario(esquema):` (línea 582). Ya se llama desde `main()`
(línea 1013), así que no hay que registrar nada.

Dos cosas de la forma de este archivo, para no inventar nombres: el ayudante se llama
`check(nombre, ok, detalle="")`, y los `estados` son tuplas de **cuatro** elementos
`(t, etapa, robot_activo, mision_id)`. `continuidad_de(estados, marcas, condicion)` recibe en
`marcas` un **diccionario de instantes** —no la lista de marcas del registro—, como ya hace el
caso `limpia` de la línea 474.

```python
    # --- RF-28: la pausa de la confirmacion de piso -----------------------
    # La espera va entre TRANSFERENCIA y TRAMO_2 y publica robot_activo lleno
    # (D-C4 del diseno), asi que no puede romper la continuidad. Se comprueban
    # los DOS sentidos: que con robot no la rompe, y que sin robot SI la rompe.
    # El segundo es el que demuestra que esta funcion esta mirando de verdad
    # estas marcas y no pasandolas por alto.
    ESPERANDO_CONFIRMACION = 7
    con_espera = [
        (10.0, INACTIVA, "", ""), (10.15, RECIBIDA, "", "m1"),
        (10.2, TRAMO_1, "robot1", "m1"), (40.0, TRANSFERENCIA, "robot2", "m1"),
        (41.0, ESPERANDO_CONFIRMACION, "robot2", "m1"),
        (101.0, ESPERANDO_CONFIRMACION, "robot2", "m1"),
        (120.0, TRAMO_2, "robot2", "m1"), (141.0, COMPLETADA, "robot2", "m1"),
        (151.0, INACTIVA, "", ""),
    ]
    marcas_espera = {"t_solicitud": 10.15, "t_robot_activo": 10.2,
                     "t_completada": 141.0}
    c = continuidad_de(con_espera, marcas_espera, "B")
    check("RF-28: la espera con robot lleno no rompe la continuidad",
          c["continua"] is True, f"-> {c}")
    check("RF-28: la ventana sigue llegando hasta COMPLETADA",
          c["ventana"] == [10.2, 141.0], f"-> {c['ventana']}")

    sin_robot = [e if e[1] != ESPERANDO_CONFIRMACION else (e[0], e[1], "", e[3])
                 for e in con_espera]
    c = continuidad_de(sin_robot, marcas_espera, "B")
    check("RF-28: la espera con robot vacio SI rompe la continuidad",
          c["continua"] is False and c["instantes_sin_agente"] == [41.0, 101.0],
          f"-> {c}")

    # Y que las siete marcas de la §3.5 siguen saliendo en orden: la etapa 7 no
    # es ninguna de ellas, asi que aparecer entre dos no puede desordenarlas.
    mar = marcas_de(con_espera, {}, "B")
    check("RF-28: la espera no desordena las marcas de la §3.5",
          marcas_en_orden(mar), f"-> {mar}")
```

Las cuatro funciones que usa (`check`, `continuidad_de`, `marcas_de`, `marcas_en_orden`) y las
siete constantes de etapa ya están definidas o importadas en ese archivo (líneas 36 y 43), así
que no hay que tocar las importaciones.

- [ ] **Paso 4: correr la prueba del compositor**

```bash
cd ~/Documents/Tesis && source ~/deepracer_sim_ws/install/setup.bash && python3 herramientas/prueba_componer_registro.py
```

Esperado: `0 fallo(s).` y código de salida 0.

**El `source` hace falta, y no es opcional:** la última sección de ese archivo
(`pruebas_de_bag`, línea 713) fabrica un bag sintético e importa `rclpy.serialization`. Sin el
overlay sourceado muere con `ModuleNotFoundError: No module named 'rclpy'` **después** de haber
impreso todas las comprobaciones en verde, así que se ve una pantalla de `[OK ]` y un código de
salida 1. Comprobado el 2026-09-10: es fallo de entorno, no de la etapa 7.

- [ ] **Paso 5: commit**

```bash
cd ~/Documents/Tesis && git add Robot/aws-deepracer/coordinacion/test/prueba_registrador.py herramientas/prueba_componer_registro.py && git commit -m "RF-28: regresion de que la etapa 7 no altera continuidad ni hueco de relevo"
```

---

## Tarea 6: Contrato y requisito

**Archivos:**
- Modificar: `Documentos/CONTRATO_INTERFACES.md` (§4, la lista de interfaces de `/coordinacion`; §5, el vocabulario de `EstadoMision`)
- Modificar: `Documentos/REQUISITOS.md` (tabla de requisitos de OE3, y las tablas de recuento)
- Modificar: `Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py` (cabecera, líneas 9-13)

**Interfaces:**
- Consume: todo lo anterior. No produce nada para otra tarea.

- [ ] **Paso 1: el tópico en la cabecera del coordinador**

En `coordinador.py`, en la lista de interfaces de la cabecera (líneas 10-13), añadir tras la
línea de `puntos_interes`:

```
    /coordinacion/confirmacion_piso  std_msgs/String         (la escucha, RF-28)
```

- [ ] **Paso 2: el tópico y la etapa en el contrato**

En `Documentos/CONTRATO_INTERFACES.md`, en la §4 añadir la fila del tópico nuevo con su tipo
(`std_msgs/String`), su sentido (la HRI publica, el coordinador escucha) y su contenido (el
`mision_id` de la misión que se confirma, y que un `mision_id` que no sea el de la misión en
curso se descarta). En la §5, añadir `ESPERANDO_CONFIRMACION = 7` al vocabulario de etapas, con
la regla de presentación: la HRI muestra el botón de confirmar **solo** en esa etapa, y
`robot_activo` nunca viaja vacío en ella.

- [ ] **Paso 3: RF-28 en la tabla de requisitos**

En `Documentos/REQUISITOS.md`, añadir a la tabla de OE3 —después de RF-20— la fila:

| **RF-28** | En una misión entre niveles, el tramo del piso de destino no inicia hasta que el usuario confirma el cambio de piso desde la interfaz. Se avisa a los 60 s y la misión falla a los 120 s sin confirmación | Registro de una misión B con marcas de `ESPERANDO_CONFIRMACION`, más las tres corridas del §7 del diseño | 🔴 | S22 |

Y actualizar los recuentos: la tabla de cobertura por objetivo y el total de requisitos, que
hoy dice 34. Comprobar cuántos sitios lo nombran antes de editar:

```bash
grep -n "34\b" Documentos/REQUISITOS.md | head
```

- [ ] **Paso 4: comprobar que el repositorio sigue coherente**

```bash
cd ~/Documents/Tesis && ./herramientas/verificar_repositorio.sh
```

Esperado: 12/12. Si alguna comprobación de conteo de requisitos falla, es el paso 3 a medias.

- [ ] **Paso 5: commit**

```bash
cd ~/Documents/Tesis && git add Documentos/CONTRATO_INTERFACES.md Documentos/REQUISITOS.md Robot/aws-deepracer/coordinacion/coordinacion/coordinador.py && git commit -m "RF-28: queda en el contrato de interfaces y en la tabla de requisitos"
```

---

## Tarea 7: Las tres corridas reales

**Archivos:** ninguno. Esta tarea produce evidencia, no código.

**Requisito previo:** tareas 1 a 4 completas y el workspace compilado.

El procedimiento de arranque de la simulación, rosbridge y la página es el del
`RUNBOOK_CAMPANA.md`. Las tres corridas usan **la misma misión entre pisos** y se diferencian
solo en lo que hace la persona.

**Dos cosas que hay que tener montadas antes de empezar, o las corridas no sirven de evidencia:**

1. **El coordinador tiene que llevar `ruta_registros`.** El parámetro vale `""` por defecto
   (`coordinador.py:84`), y con él vacío `self.registro` se queda en `None` (línea 204): la
   misión corre bien pero **no se escribe ningún registro**, y el recuento de marcas de etapa 7
   no se puede comprobar en ninguna parte. Lanzarlo con
   `-p ruta_registros:=$HOME/registros_rf28`.
2. **Un cuarto terminal capturando los textos.** Ni el registro en vivo ni el compuesto guardan
   `mensaje_usuario` —`marca()` guarda `t`, `etapa`, `etapa_num`, `robot`, `punto_id` y
   `extraordinaria`, nada más—, así que el texto de la alerta hay que recogerlo del tópico:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 topic echo /coordinacion/estado_mision --field mensaje_usuario | tee /tmp/rf28_textos.txt
```

**Y hay que saber que en cada corrida salen DOS documentos distintos, con la misma palabra
«marcas» significando cosas distintas:**

| Documento | Quién lo escribe | Qué es `marcas` ahí | Para qué sirve aquí |
|---|---|---|---|
| `~/registros_rf28/mision_*.json` | el coordinador, en vivo | **lista** de cambios de etapa, con `etapa` como nombre y `etapa_num` | contar las marcas de etapa 7 y medir su separación |
| el que compone `componer_registro.py` del bag | el PC, después | **diccionario** de los siete instantes de la §3.5 | validar contra el esquema y leer la continuidad |

El esquema `esquema_registro_mision.json` describe el **segundo**, no el primero (su `marcas` es
un objeto con `additionalProperties: false`). No intentar validar el registro en vivo contra él.

Medir el RTF antes de cada corrida, porque hace falta para interpretar los tiempos del bag:

```bash
cd ~/deepracer_sim_ws && source install/setup.bash && python3 ~/Documents/Tesis/herramientas/medir_rtf.py --segundos 20
```

- [ ] **Corrida A — confirmación temprana.** Pulsar el botón a los ~10 s de que aparezca.
  Esperado: la misión sigue al tramo 2 y termina en `COMPLETADA`. En el registro **en vivo**,
  `metricas.continuidad: true` y **una sola** marca con `"etapa": "ESPERANDO_CONFIRMACION"`.

- [ ] **Corrida B — confirmación tras la alerta.** Dejar pasar el minuto y pulsar hacia los
  75 s. Esperado, en tres sitios distintos:
  - en el **panel**, a los 60 s de reloj de pared el texto cambia a *«Seguimos esperando su
    confirmacion. Quedan 60 segundos.»* (captura);
  - en el **log del coordinador**, la línea `alerta: 60 s sin confirmacion`, una sola vez;
  - en `/tmp/rf28_textos.txt`, los dos textos de la etapa 7, distintos;
  - en el registro **en vivo**, **dos** marcas de `ESPERANDO_CONFIRMACION`, separadas en tiempo
    de simulación por `60 s × RTF` (no por 60 s: el plazo es de pared, las marcas son de
    `/clock`). Con el RTF del paso anterior eso se comprueba sin ambigüedad.

  La misión termina en `COMPLETADA` y `continuidad: true`.

- [ ] **Corrida C — sin confirmar.** No pulsar. Esperado: a los 120 s de reloj de pared la
  misión pasa a `FALLIDA` con motivo *«el usuario no confirmó la llegada al piso 2»*, y el
  panel se pone rojo con «Camino bloqueado». El registro en vivo se escribe igual —el
  `_cerrar_registro` va en todas las salidas de `_ejecutar`, incluidas las de fallo— con
  `cierre.exito_declarado: false` y el motivo redactado.

- [ ] **Contar las marcas de etapa 7 en las tres**

```bash
for f in ~/registros_rf28/mision_*.json; do python3 -c "import json,sys; d=json.load(open(sys.argv[1])); m=[x for x in d['marcas'] if x['etapa']=='ESPERANDO_CONFIRMACION']; print(sys.argv[1].split('/')[-1], len(m), [x['t'] for x in m], d['metricas']['continuidad'])" "$f"; done
```

Esperado: `1` marca en A, `2` en B separadas por `60 s × RTF`, `2` en C (la inicial y la de la
alerta). `continuidad` verdadera en A y B.

- [ ] **Componer y validar las tres desde el bag**

Para cada corrida, componer el registro y validarlo:

```bash
cd ~/Documents/Tesis && python3 herramientas/componer_registro.py <ruta_del_bag> --salida /tmp/rf28_X.json && python3 -c "import json,jsonschema;jsonschema.validate(json.load(open('/tmp/rf28_X.json')),json.load(open('Documentos/esquema_registro_mision.json')));print('ESQUEMA OK')"
```

Antes de correrlo, confirmar los nombres reales de los argumentos:

```bash
python3 herramientas/componer_registro.py --help
```

Esperado en A y B: `ESQUEMA OK` y `"continuidad": true`. En C: `ESQUEMA OK`, veredicto no
exitoso y el motivo redactado.

**Criterio de cierre de RF-28:** las tres corridas se comportan como arriba, los registros
validan, y ninguna de las dos corridas exitosas sale con `continuidad: false`. Un
`continuidad: false` en A o B es un fallo del diseño —la condición de la marca con robot no
vacío— y no una anomalía del banco: hay que volver al paso 6 de la Tarea 3 antes de dar nada
por bueno.

- [ ] **Guardar la evidencia**

Copiar los tres registros **compuestos** a `Documentos/Evidencia/registros/` con nombres
`S22_RF28_A.json`, `_B.json` y `_C.json`, y escribir
`Documentos/Evidencia/S22_RF28_confirmacion.md` con: el RTF medido en cada corrida, lo que hizo
la persona, el resultado, la salida del conteo de marcas de etapa 7, los dos textos de
`/tmp/rf28_textos.txt` en la corrida B, y capturas del panel en la etapa 7 y en la alerta.

- [ ] **Commit**

```bash
cd ~/Documents/Tesis && git add Documentos/Evidencia/registros/S22_RF28_A.json Documentos/Evidencia/registros/S22_RF28_B.json Documentos/Evidencia/registros/S22_RF28_C.json Documentos/Evidencia/S22_RF28_confirmacion.md && git commit -m "RF-28 cerrado: las tres corridas de la confirmacion de piso"
```

- [ ] **Poner RF-28 en verde** en `Documentos/REQUISITOS.md` y actualizar `ESTADO.md`, en el
  corte del viernes.

---

## Lo que este plan NO hace

- **No arregla la cancelación**, que hoy no funciona en absoluto: `rclpy` rechaza toda
  cancelación por defecto y el chequeo de `coordinador.py:234` es código muerto. Está
  documentado en la §3 del diseño. Es el punto 1 del director y necesita su propio plan.
- **No impide dos misiones simultáneas.** El `ActionServer` acepta todo goal que le llegue y lo
  ejecuta de inmediato; el guardián solo impide un segundo *coordinador*. También en la §3 del
  diseño.
- **No implementa el homing.** Su punto de enganche natural es el camino de fallo de la Tarea 3,
  paso 7, pero es el punto 6 del director y va aparte.
- **No toca la pausa, la alerta de vehículo bloqueado ni la batería**: puntos 2, 4 y 5.
