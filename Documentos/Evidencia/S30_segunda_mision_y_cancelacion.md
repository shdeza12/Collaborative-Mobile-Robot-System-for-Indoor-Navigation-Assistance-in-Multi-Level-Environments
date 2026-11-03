# Segunda misión con otra en curso y cancelación sin el teléfono (1 de noviembre)

Prueba en el portátil, sin los vehículos, para fijar las reglas de la sesión con los jurados
([`GUION_SESION_JURADOS.md`](../GUION_SESION_JURADOS.md)). Usa el nodo real del coordinador y los robots falsos de
`prueba_coordinador_vehiculo.py`, que se mueven a 10 m/s para no esperar lo que tardaría un vehículo. Se corrió dos
veces, con el mismo resultado, y no se cambió código.

Programa: [`S30_segunda_mision_y_cancelacion.py`](S30_segunda_mision_y_cancelacion.py).

```bash
source ~/deepracer_sim_ws/install/setup.bash
```

```bash
ROS_DOMAIN_ID=93 ROS_LOCALHOST_ONLY=1 python3 Documentos/Evidencia/S30_segunda_mision_y_cancelacion.py
```

## Segunda misión con otra en curso

La página desactiva «Iniciar guiado» solo en el teléfono que lanzó la misión (`refrescarBotonIr` en
`interfaz_web/js/app.js`). El servidor de la acción no tiene `goal_callback` y usa un grupo reentrante
(`coordinador.py`), así que acepta y ejecuta en paralelo cualquier meta que le llegue.

La misión A, Salón 403 → Salón 303, se dejó esperando la confirmación del piso. Desde otro cliente se pidió la misión
B, Salón 301 → Salón 401, y se confirmó A con su identificador, como lo haría su teléfono.

| Instante | Qué pasó |
|---|---|
| 10,5 s | A espera la confirmación. B se acepta y robot1, que esperaba al usuario de A en su escalera, recibe de inmediato la meta del Salón 301 |
| 13,5 s | Se confirma A. No tiene efecto: B reinició el enganche de la confirmación |
| 29,0 s | B se completa con un relevo |
| 70,5 s | A publica de nuevo la espera, con el aviso de los 60 s |
| 130,5 s | A falla: «el usuario no confirmó la llegada al piso 3 en 120 s» |

Queda un solo registro, el de B: las dos misiones comparten el registro en curso del coordinador, y A pierde el suyo.

La confirmación es un tópico, y el botón aparece en todo teléfono que tenga la página abierta, sea o no el que lanzó
la misión (`pintarPanel` en `app.js`). Eso sale de leer el código; no se probó.

El sistema atiende una misión a la vez, y el documento final declara las misiones simultáneas fuera del alcance. Por
eso no se corrige para la sesión: se resuelve con la regla de un solo teléfono.

## Cancelación sin el teléfono que lanzó la misión

Al recargar la página se pierde el identificador de la meta y «Cancelar» queda desactivado (`estado.metaId`, en
`app.js`). Con la misión A en espera de confirmación se llamó al servicio de cancelación de la acción con la petición
vacía, que cancela todas las metas:

| Dato | Resultado |
|---|---|
| Respuesta del servicio | `return_code` 0, una meta en cancelación |
| Resultado de la misión | `CANCELED`, «Cancelada por el usuario» |
| Etapas | … → 7 (esperando confirmación) → 8 (cancelando) → 5 (fallida) |
| Registro | Escrito |

La misma orden se probó en el contenedor `coordinador_jazzy`, con la imagen del 18 de octubre y una misión viva: devolvió
`return_code=0` con la meta en `goals_canceling`. En esa prueba no había robots, así que la vuelta a la escalera
solo se vio con los robots falsos.

Pendiente: probarla con los vehículos en el ensayo.
