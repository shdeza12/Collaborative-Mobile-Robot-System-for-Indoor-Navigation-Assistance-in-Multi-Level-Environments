# Estado del proyecto

Tablero corto del avance. Se actualiza los viernes en la noche, con el corte de la semana. La bitácora
completa hasta el 24 de octubre de 2026 (lecturas de avance, decisiones, riesgos cerrados y discrepancias)
está en [`Documentos/historial/ESTADO_bitacora.md`](Documentos/historial/ESTADO_bitacora.md), y el
recorrido semana a semana en [`CRONOLOGIA.md`](Documentos/DocumentoFinal/CRONOLOGIA.md).

| | |
|---|---|
| **Semana en curso** | S28 (19 al 25 de octubre de 2026), fase 6: análisis y escritura |
| **Fecha de corte** | 2026-10-24 (viernes). Ajustes de la página y cancelación verificados con el teléfono y los dos vehículos el 23-oct ([`S28_campo_pagina_cancelacion.md`](Documentos/Evidencia/S28_campo_pagina_cancelacion.md)); arreglo de la media vuelta después de cancelar (`d25e45e`); README corto y documentos de sesiones pasadas en [`historial/`](Documentos/historial/) |
| **Último entregable formal** | Semana 28 ([`Entregable_semana_28.tex`](Documentos/Entregables/Entregable_semana_28.tex) y su versión [`.md`](Documentos/Entregables/Entregable_semana_28.md)) |
| **Documento final** | Compila en el portátil: 94 páginas, sin errores ([`DocumentoFinal/`](Documentos/DocumentoFinal/)). El director pide entre 60 y 80 |
| **Planificación** | [`CRONOGRAMA_S17_S32.md`](Documentos/CRONOGRAMA_S17_S32.md) |

## Objetivos específicos

| Objetivo | Avance | Requisitos | Evidencia principal |
|---|---|---|---|
| OE1 · Arquitectura funcional | 100 % | 10 de 10 | Coordinación y relevo en simulación y con los vehículos |
| OE2 · Plataforma con dos vehículos | 100 % | 6 de 6 | Locomoción, sensado, odometría y red medidos en campo (revisión del 15-oct) |
| OE3 · Interfaz web | 100 % | 6 de 6 | Confirmación de cambio de piso y cancelación, probadas en teléfono con los vehículos |
| OE4 · Evaluación | 100 % | 7 de 7 | 30 misiones en simulación y 9 de 9 con los vehículos ([`S27_campana_rf27.md`](Documentos/Evidencia/S27_campana_rf27.md)) |

Matriz completa en [`REQUISITOS.md`](Documentos/REQUISITOS.md): 36 requisitos, 35 verificados y uno
parcial, la restricción RNF-03 (operación en condiciones controladas), a falta de anotar las personas que
pasaron por el pasillo durante las misiones.

## Pendiente

1. RNF-03: revisar en los videos de la campaña las personas en el pasillo, misión por misión.
2. Documento final: bajarlo de 94 a entre 60 y 80 páginas; corregir el «20 %» del hall del piso 2 (es 25 %).
3. Reorganización del repositorio: los mundos y modelos de la raíz a una carpeta de simulación.
4. Registro de misión: la etapa de cancelación sale como `8` y no como `CANCELANDO`.
5. Imagen `coordinador_jazzy` del portátil: reconstruirla con el agente nuevo.
6. Siete archivos de código copiados en los vehículos citan en comentarios la ruta vieja de planes ya
   movidos a `historial/`; se actualizan en los dos vehículos la próxima vez que estén encendidos.

## Riesgos abiertos

Según la bitácora; el detalle de cada uno, en su §4.

| Riesgo | Estado |
|---|---|
| R3 · La posición a lo largo de un pasillo uniforme no es observable con el láser | Causa medida y acotada; los pisos 3 y 4 se eligieron por eso |
| R8 · Dos distribuciones de ROS 2: Humble en la simulación y el portátil, Jazzy en los vehículos | Caracterizado; el coordinador corre en Jazzy dentro de un contenedor |
| R13 · El láser simulado tiene un hueco de unos 90° y no coincide con el del vehículo | Rebajado el 8-sep; sigue abierto como amenaza a la comparación entre simulación y vehículos |
| R15 · El mapa de la campaña en simulación leía como libre su espacio desconocido | Defecto corregido; falta decidir cómo reportarlo |
| R16 · La simulación de dos robots dejó de completar el relevo tras la actualización de ROS del 6-oct | Abierto, causa no aislada |
