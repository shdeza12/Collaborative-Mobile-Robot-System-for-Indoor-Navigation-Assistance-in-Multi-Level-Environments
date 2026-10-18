---
title: Inicio
hide:
  - navigation
  - toc
---

<div class="portada" markdown>
<div markdown>
<div class="etiqueta">Proyecto de grado · Universidad Santo Tomás · 2026</div>

# Dos robots que guían a una persona entre los pisos de un edificio

<p class="entrada">La persona pide su destino desde el teléfono. El robot de su piso la lleva hasta la escalera, y el robot del otro piso la recibe y termina el recorrido.</p>

[Ver el proceso :material-timeline-text-outline:](proceso/index.md){ .md-button .md-button--primary }
[Ver los resultados :material-chart-box-outline:](resultados.md){ .md-button }
[Replicarlo :material-wrench-outline:](replicar.md){ .md-button }
</div>

<figure markdown>
![La página del teléfono durante una misión: el robot guía al usuario y la página muestra el paso en que va](img/interfaz_seguimiento.png){ width="380" }
<figcaption>La página del teléfono durante una misión.</figcaption>
</figure>
</div>

<div class="cifras">
  <div class="cifra"><div class="valor">9 de 9</div><div class="que">misiones con relevo completadas con los vehículos reales, en los pisos 3 y 4</div></div>
  <div class="cifra"><div class="valor">26 de 30</div><div class="que">misiones completadas en simulación; los 4 fallos fueron de precisión de llegada</div></div>
  <div class="cifra"><div class="valor">0,87 s</div><div class="que">mediana desde la solicitud hasta que el vehículo empieza a moverse</div></div>
  <div class="cifra"><div class="valor">0,23 m</div><div class="que">error de llegada mediano en los vehículos, según su localización</div></div>
</div>

## Cómo funciona, en cuatro pasos

<div class="pasos">
  <div class="paso"><strong>Pide su destino</strong>Desde el navegador del teléfono, sin instalar nada: elige dónde está y a dónde va.</div>
  <div class="paso"><strong>El robot de su piso lo guía</strong>Va a recogerlo y lo lleva hasta la escalera.</div>
  <div class="paso"><strong>Cambia de piso</strong>Sube o baja por su cuenta y lo confirma en el teléfono.</div>
  <div class="paso"><strong>El otro robot termina</strong>El robot del piso de llegada ya lo espera en la escalera y lo lleva al destino.</div>
</div>

[Ver la arquitectura y el relevo en detalle :material-arrow-right:](como-funciona.md)

## Cómo se llegó hasta aquí

El proyecto no salió en línea recta. Empezó con otra plataforma, en un simulador, con un seguidor de paredes que no funcionó, y llegó al edificio después de cambiar de piso, de computador de a bordo y de forma de medir. La sección [Proceso](proceso/index.md) cuenta ese camino con sus decisiones, sus errores y las pruebas que los resolvieron.

<div class="pasos">
  <div class="paso"><strong>Simulación</strong>El vehículo en Gazebo, con su modelo de dirección tipo automóvil.</div>
  <div class="paso"><strong>Coordinación</strong>El coordinador que asigna robots y organiza el relevo.</div>
  <div class="paso"><strong>Interfaz</strong>La página web del teléfono.</div>
  <div class="paso"><strong>Vehículos reales</strong>Dos AWS DeepRacer navegando el edificio.</div>
  <div class="paso"><strong>Evaluación</strong>Treinta misiones en simulación y nueve con los vehículos.</div>
</div>
