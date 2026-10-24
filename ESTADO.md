# Estado del proyecto

Tablero corto del avance. El proyecto cumplió sus cuatro objetivos específicos. Se actualiza los viernes en la noche, con el corte de la semana. La bitácora
completa hasta el 24 de octubre de 2026 (lecturas de avance, decisiones, riesgos cerrados y discrepancias)
está en [`Documentos/historial/ESTADO_bitacora.md`](Documentos/historial/ESTADO_bitacora.md), y el
recorrido semana a semana en [`CRONOLOGIA.md`](Documentos/DocumentoFinal/CRONOLOGIA.md).

| | |
|---|---|
| **Semana en curso** | S28 (19 al 25 de octubre de 2026), fase 6: análisis y escritura |
| **Fecha de corte** | 2026-10-24 (viernes). Ajustes de la página y cancelación verificados con el teléfono y los dos vehículos el 23-oct ([`S28_campo_pagina_cancelacion.md`](Documentos/Evidencia/S28_campo_pagina_cancelacion.md)); arreglo de la media vuelta después de cancelar (`d25e45e`); README corto, documentos de sesiones pasadas en [`historial/`](Documentos/historial/) y mundos de Gazebo en [`simulacion/`](simulacion/) |
| **Último entregable formal** | Semana 28 ([`Entregable_semana_28.tex`](Documentos/Entregables/Entregable_semana_28.tex) y su versión [`.md`](Documentos/Entregables/Entregable_semana_28.md)) |
| **Documento final** | Compila en el portátil: 94 páginas, sin errores ([`DocumentoFinal/`](Documentos/DocumentoFinal/)). El director pide entre 60 y 80 |

## Objetivos específicos

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="sitio/paginas/img/readme_objetivos_oscuro.png">
  <img alt="Los cuatro objetivos específicos cumplidos: arquitectura funcional (10 de 10 requisitos), plataforma robótica (6 de 6), interfaz para el usuario (6 de 6) y evaluación experimental (7 de 7)" src="sitio/paginas/img/readme_objetivos_claro.png">
</picture>

| Objetivo | Evidencia principal |
|---|---|
| OE1 · Arquitectura funcional | Coordinación y relevo en simulación y con los vehículos |
| OE2 · Plataforma con dos vehículos | Locomoción, sensado, odometría y red medidos en campo |
| OE3 · Interfaz web | Confirmación de cambio de piso y cancelación, probadas en teléfono con los vehículos |
| OE4 · Evaluación | 30 misiones en simulación y 9 de 9 con los vehículos ([`S27_campana_rf27.md`](Documentos/Evidencia/S27_campana_rf27.md)) |

Matriz completa en [`REQUISITOS.md`](Documentos/REQUISITOS.md): 36 requisitos, 35 verificados y uno
parcial, la restricción RNF-03 (operación en condiciones controladas), a falta de anotar las personas que
pasaron por el pasillo durante las misiones.

## Pendiente

1. RNF-03: revisar en los videos de la campaña las personas en el pasillo, misión por misión.
2. Documento final: bajarlo de 94 a entre 60 y 80 páginas; corregir el «20 %» del hall del piso 2 (es 25 %).
3. Simulación de dos robots: desde la actualización de ROS del 6 de octubre no completa el relevo; causa no
   aislada (riesgo R16 de la bitácora).
4. Registro de misión: la etapa de cancelación sale como `8` y no como `CANCELANDO`.
5. Imagen `coordinador_jazzy` del portátil: reconstruirla con el agente nuevo.
6. Siete archivos de código copiados en los vehículos citan en comentarios la ruta vieja de planes ya
   movidos a `historial/`; se actualizan en los dos vehículos la próxima vez que estén encendidos.
