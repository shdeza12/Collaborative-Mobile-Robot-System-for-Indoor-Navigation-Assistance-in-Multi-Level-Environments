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

## Semana a semana

El proyecto no salió en línea recta: empezó con otra plataforma, en un simulador, con un seguidor de paredes que no funcionó, y llegó al edificio después de cambiar de piso, de computador de a bordo y de forma de medir. Cada tarjeta abre la página de una semana, con lo que se hizo, sus imágenes y lo que se concluyó.

<!-- semanas:inicio -->
### Fases 2 y 3 · requisitos y diseño conceptual

<div class="semanas-grid">
<a class="semana-tarjeta" href="semanas/s10/"><img src="semanas/img/s10_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 10 · abril</span><span class="titulo">Limitaciones de la plataforma DonkeyCar</span></span></a>
<a class="semana-tarjeta" href="semanas/s11/"><img src="semanas/img/s11_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 11 · abril</span><span class="titulo">Modelo propio del DonkeyCar y primera arquitectura</span></span></a>
<a class="semana-tarjeta" href="semanas/s12/"><img src="semanas/img/s12_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 12 · abril</span><span class="titulo">Adopción del modelo AWS DeepRacer y migración a ROS 2 Humble</span></span></a>
</div>

### Fase 4 · desarrollo progresivo de la solución

<div class="semanas-grid">
<a class="semana-tarjeta" href="semanas/s13/"><img src="semanas/img/s13_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 13 · mayo</span><span class="titulo">Primeros entornos y seguidor de paredes</span></span></a>
<a class="semana-tarjeta" href="semanas/s14/"><img src="semanas/img/s14_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 14 · mayo</span><span class="titulo">Sensores en el modelo del primer piso</span></span></a>
<a class="semana-tarjeta" href="semanas/s15/"><img src="semanas/img/s15_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 15 · mayo</span><span class="titulo">Primer mapa con SLAM</span></span></a>
<a class="semana-tarjeta" href="semanas/s16/"><img src="semanas/img/s16_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 16 · junio</span><span class="titulo">Receso de mitad de año</span></span></a>
</div>

### Fase 5 · integración del sistema y pruebas

<div class="semanas-grid">
<a class="semana-tarjeta" href="semanas/s17/"><img src="semanas/img/s17_5.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 17 · 3 al 9 de agosto</span><span class="titulo">Vehículo físico liberado y Nav2 en Humble</span></span></a>
<a class="semana-tarjeta" href="semanas/s18/"><img src="semanas/img/s18_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 18 · 10 al 16 de agosto</span><span class="titulo">Dos agentes aislados y entorno de dos niveles</span></span></a>
<a class="semana-tarjeta" href="semanas/s19/"><img src="semanas/img/s19_3.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 19 · 17 al 23 de agosto</span><span class="titulo">Diagnóstico del vehículo y protocolo</span></span></a>
<a class="semana-tarjeta" href="semanas/s20/"><img src="semanas/img/s20_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 20 · 24 al 30 de agosto</span><span class="titulo">Coordinador, primera misión y relevo en simulación</span></span></a>
<a class="semana-tarjeta" href="semanas/s21/"><img src="semanas/img/s21_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 21 · 31 de agosto al 6 de septiembre</span><span class="titulo">Campaña de treinta misiones</span></span></a>
<a class="semana-tarjeta" href="semanas/s22/"><img src="semanas/img/s22_5.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 22 · 7 al 13 de septiembre</span><span class="titulo">Interfaz en el teléfono e información de avance</span></span></a>
<a class="semana-tarjeta" href="semanas/s23/"><img src="semanas/img/s23_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 23 · 14 al 20 de septiembre</span><span class="titulo">Segundo vehículo y congelación del código</span></span></a>
<a class="semana-tarjeta" href="semanas/s24/"><img src="semanas/img/s24_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 24 · 21 al 27 de septiembre</span><span class="titulo">Decisión de la demostración física y navegación real</span></span></a>
<a class="semana-tarjeta" href="semanas/s25/"><img src="semanas/img/s25_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 25 · 28 de septiembre al 4 de octubre</span><span class="titulo">Aislamiento, piso 2 y paso a los pisos 3 y 4</span></span></a>
<a class="semana-tarjeta" href="semanas/s26/"><img src="semanas/img/s26_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 26 · 5 al 11 de octubre</span><span class="titulo">Unidad inercial, red, llegada verificada y coordinador al portátil</span></span></a>
</div>

### Fase 6 · campaña, análisis y escritura

<div class="semanas-grid">
<a class="semana-tarjeta" href="semanas/s27/"><img src="semanas/img/s27_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 27 · 12 al 18 de octubre</span><span class="titulo">Campaña con los dos vehículos</span></span></a>
<a class="semana-tarjeta" href="semanas/s28/"><img src="semanas/img/s28_1.jpg" alt="" loading="lazy"><span class="texto"><span class="num">Semana 28 · desde el 19 de octubre</span><span class="titulo">Documento final</span></span></a>
</div>
<!-- semanas:fin -->
