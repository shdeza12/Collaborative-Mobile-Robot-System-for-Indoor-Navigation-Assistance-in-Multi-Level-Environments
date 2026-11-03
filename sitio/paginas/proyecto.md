# El proyecto

## El problema

En un edificio de varios pisos, un usuario que no lo conoce tiene que encontrar un salón que puede estar en otro piso. Un robot guía resuelve el recorrido dentro de un piso, pero un robot de ruedas no sube escaleras. La respuesta que propone el proyecto es que dos agentes, robots móviles terrestres, uno por piso, se **repartan el recorrido** y se entreguen al usuario en la escalera, sin que el servicio se corte.

!!! question "Pregunta del proyecto"
    ¿Cómo asistir la orientación de usuarios dentro de entornos interiores con múltiples pisos utilizando sistemas robóticos?

## Objetivo general

Implementar un sistema colaborativo de dos robots móviles terrestres para la guía coordinada y eficiente de asistencia a visitantes en entornos interiores con múltiples pisos, mediante comunicación inter-robot, asignación dinámica de tareas y una interfaz móvil de interacción usuario-robot.

## Objetivos específicos

El objetivo general y los específicos se transcriben como se aprobaron. El segundo nombra el DonkeyCar porque el proyecto empezó con esa plataforma; [el cambio a AWS DeepRacer](proceso/decisiones.md) se explica en las decisiones.

<div class="decisiones" markdown>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 1</div>
### Arquitectura
Modelar la arquitectura funcional del sistema colaborativo de dos robots móviles, definiendo requerimientos, escenarios de operación con múltiples pisos, estrategia de asignación de tareas y esquema de comunicación inter-robot.

[Cómo funciona :material-arrow-right:](como-funciona.md)
</div>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 2</div>
### Plataforma robótica
Desarrollar una plataforma robótica móvil basada en dos vehículos tipo DonkeyCar, integrando los módulos de locomoción, sensado, procesamiento y comunicación necesarios para la operación colaborativa en entornos interiores.

[Proceso :material-arrow-right:](proceso/index.md)
</div>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 3</div>
### Interfaz
Programar una interfaz móvil para interacción humano-robot (HRI) basada en la selección de localizaciones de interés de origen y destino.

[La página del teléfono :material-arrow-right:](como-funciona.md#la-pagina-del-telefono)
</div>

<div class="decision-tarjeta" markdown>
<div class="cuando">Objetivo 4</div>
### Evaluación
Evaluar el desempeño del sistema mediante pruebas experimentales en un entorno interior controlado, utilizando métricas como tiempo de respuesta, tiempo de asignación de robot, tasa de éxito en la entrega de asistencia y continuidad del servicio entre niveles.

[Resultados :material-arrow-right:](resultados.md)
</div>

</div>

## Términos

El sitio nombra cada cosa como el documento final. La [tabla completa](https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments/blob/main/Documentos/TERMINOS.md) está en el repositorio.

| Término | Qué es |
|---|---|
| Agente | Cada uno de los dos robots móviles del sistema, construidos sobre la plataforma AWS DeepRacer y dedicados cada uno a un piso del edificio. Tiene su propia navegación y ejecuta los tramos de la misión que le asigna el coordinador. |
| Usuario | Persona que pide el servicio desde la interfaz y a la que los agentes guían desde su origen hasta su destino. |
| Misión | Una solicitud de guiado completa, desde que el usuario elige origen y destino hasta que el sistema la cierra. |
| Relevo | Traspaso de la responsabilidad de guiar a un usuario, de un agente al otro, en un punto acordado de antemano. |
| Punto de transferencia | Lugar físico, en este trabajo la escalera, donde un agente entrega el guiado y el otro lo recibe. |

## Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| Dos agentes, uno por piso, y una misión a la vez | Varios agentes por piso o varias misiones simultáneas |
| Pasillos interiores, en horarios de baja circulación | Espacios abiertos o con mucha gente |
| El usuario cambia de piso por la escalera, por su cuenta | Que el agente use el ascensor |
| Usuarios que no conocen el edificio | Usuarios con discapacidad visual, que necesitan otra interfaz y una evaluación propia |

El proyecto tiene 36 requisitos, cada uno con una prueba escrita antes de correrla. Al cerrar la toma de datos, 35 están verificados y los cuatro objetivos tienen todos los suyos cumplidos. Queda parcial una restricción: registrar como observación las personas que pasaron por el pasillo durante las pruebas.
