# El proyecto

## El problema

En un edificio de varios pisos, una persona que no lo conoce tiene que encontrar un salón que puede estar en otro piso. Un robot guía resuelve el recorrido dentro de un piso, pero un robot de ruedas no sube escaleras. La pregunta del proyecto es si dos robots, uno por piso, pueden **repartirse el recorrido** y entregar a la persona de uno al otro en la escalera, sin que el servicio se corte.

!!! question "Pregunta del proyecto"
    ¿Cómo puede un sistema de dos robots móviles guiar a una persona entre los pisos de un edificio, coordinando el traspaso en la escalera, con tiempos de respuesta y una tasa de éxito medibles?

## Objetivo general

Implementar un sistema colaborativo de dos robots móviles terrestres para guiar a visitantes en un edificio de varios pisos, con comunicación entre los robots, asignación dinámica de tareas y una interfaz móvil.

## Objetivos específicos

<div class="decisiones" markdown>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 1</div>
### Arquitectura
Modelar la arquitectura funcional: requisitos, escenarios de varios pisos, asignación de tareas y comunicación entre los robots.

[Cómo funciona :material-arrow-right:](como-funciona.md)
</div>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 2</div>
### Plataforma robótica
Desarrollar dos vehículos con locomoción, sensado, procesamiento y comunicación para operar juntos en interiores.

[Proceso :material-arrow-right:](proceso/index.md)
</div>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 3</div>
### Interfaz
Programar una interfaz móvil en la que el usuario elige el origen y el destino.

[La página del teléfono :material-arrow-right:](como-funciona.md#la-pagina-del-telefono)
</div>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 4</div>
### Evaluación
Medir el tiempo de respuesta, el tiempo de asignación, la tasa de éxito y la continuidad del servicio entre pisos.

[Resultados :material-arrow-right:](resultados.md)
</div>

</div>

## Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| Dos robots, uno por piso, y una misión a la vez | Varios robots por piso o varias misiones simultáneas |
| Pasillos interiores, en horarios de baja circulación | Espacios abiertos o con mucha gente |
| La persona cambia de piso por la escalera, por su cuenta | Que el robot use el ascensor |
| Visitantes que no conocen el edificio | Personas con discapacidad visual, que necesitan otra interfaz y una evaluación con usuarios |

El proyecto tiene 36 requisitos, cada uno con una prueba escrita antes de correrla. Al cerrar la toma de datos, 35 están verificados y los cuatro objetivos tienen todos los suyos cumplidos. Queda parcial una restricción: registrar como observación las personas que pasaron por el pasillo durante las pruebas.
