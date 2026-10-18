# Cómo funciona

## Las piezas del sistema

El sistema tiene tres piezas. Un **coordinador** decide y manda. Dos **agentes**, uno por vehículo y por piso, ejecutan. Y una **página web** es la vía por la que la persona pide el servicio. El coordinador corre en un computador portátil; cada vehículo lleva su propia navegación.

```mermaid
flowchart LR
  T["Página web<br/>en el teléfono"] <-->|"solicitud y estado"| C["Coordinador<br/>en el portátil"]
  C <-->|"órdenes y posición"| A1["Vehículo del piso 3<br/>agente y navegación"]
  C <-->|"órdenes y posición"| A2["Vehículo del piso 4<br/>agente y navegación"]
  A1 ---|entrega| E{{"Escalera:<br/>punto de relevo"}}
  A2 ---|recibe| E
```

Tres reglas ordenan la comunicación:

- El coordinador manda a un vehículo solo con la acción de navegación de ROS 2 (o pidiéndole una media vuelta); nunca le envía velocidades.
- La página habla solo con el coordinador, nunca con los vehículos.
- El texto que lee la persona lo redacta el coordinador, y la página lo muestra tal cual. Así la lógica no se duplica en el navegador.

Los dos vehículos no se ven entre sí: cada uno solo se anuncia al portátil. Esta topología en estrella salió de una prueba fallida, cuando con los dos vehículos hablándose todo con todo las tarjetas se saturaron ([ver la decisión](proceso/decisiones.md#coordinador-en-el-portatil)).

## Una misión con relevo

Si el origen y el destino están en el mismo piso, la misión tiene dos tramos del mismo robot: ir a recoger a la persona y llevarla. Si están en pisos distintos, tiene cuatro, y el punto de encuentro es siempre la escalera.

```mermaid
sequenceDiagram
  autonumber
  actor U as Persona
  participant P as Página
  participant C as Coordinador
  participant R3 as Robot del piso 3
  participant R4 as Robot del piso 4
  U->>P: Salón 302 → Salón 401
  P->>C: solicitud
  C->>R3: ve a recoger al usuario
  R3-->>C: llegó (posición verificada)
  C->>R3: guíalo hasta la escalera
  R3-->>C: en la escalera (posición verificada)
  C->>R4: ve a tu escalera
  R4-->>C: en la escalera
  C->>P: espera de confirmación: "¿Ya está en el piso 4?"
  U->>P: Ya estoy en el piso 4
  P->>C: confirmación
  C->>R4: guíalo al Salón 401
  R4-->>C: llegó (posición verificada)
  C->>P: Ha llegado a Salón 401
```

El coordinador no confía en que la navegación diga «llegué». Espera 1,5 s a que el vehículo se detenga y compara su posición con el punto de destino; si queda a más de 0,5 m, la misión falla con ese motivo.

??? info "Las etapas de una misión"
    | Etapa | Qué pasa |
    |---|---|
    | Recibida | El coordinador aceptó la solicitud y todavía no asignó robot |
    | Primer tramo | El robot del piso de origen va a recoger a la persona y la guía |
    | Transferencia | El robot del otro piso va a su escalera |
    | Esperando confirmación | El sistema espera que la persona confirme que cambió de piso |
    | Segundo tramo | El robot del piso de destino la guía hasta el final |
    | Completada | Terminó con la llegada verificada |
    | Fallida | Terminó sin cumplirse, con el motivo en el texto |
    | Cancelando | La persona canceló y el robot vuelve a su escalera |

## La asignación de robots

Cada piso tiene un robot asignado, y esa correspondencia es configuración, no código. El coordinador elige el robot según el piso del origen y del destino. Con un solo robot posible por piso, un método de optimización como el húngaro devolvería la misma tabla, así que no hace falta. El método importa cuando haya dos o más robots por piso, y queda como trabajo futuro.

## La página del teléfono

Es una página web, no una aplicación: un visitante ocasional no va a instalar nada para preguntar por un salón. No usa bibliotecas externas, porque la red del edificio puede no tener internet.

<div class="dos-graficas" markdown>
<figure markdown>
![La página durante el guiado](img/interfaz_seguimiento.png){ width="320" }
<figcaption>Durante el guiado: el robot activo, hacia dónde va, la distancia y el paso de la misión.</figcaption>
</figure>
<figure markdown>
![La página esperando la confirmación del cambio de piso](img/interfaz_confirmacion.png){ width="320" }
<figcaption>En el relevo: la página pide confirmar el cambio de piso. Si pasan 60 s avisa, y a los 120 s la misión falla.</figcaption>
</figure>
</div>

Dos funciones se añadieron al ver el sistema en uso, a pedido del director: la **confirmación del cambio de piso**, para que la misión no se dé por completada con la persona todavía en el piso equivocado, y la **cancelación**, que devuelve el robot activo a su escalera.
