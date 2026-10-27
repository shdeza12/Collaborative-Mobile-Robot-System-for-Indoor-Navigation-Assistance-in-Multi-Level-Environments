# Estado del proyecto

Tablero corto del avance. El proyecto cumplió sus cuatro objetivos específicos. Se actualiza los viernes en la noche, con el corte de la semana. La bitácora
completa hasta el 24 de octubre de 2026 (lecturas de avance, decisiones, riesgos cerrados y discrepancias)
está en [`Documentos/historial/ESTADO_bitacora.md`](Documentos/historial/ESTADO_bitacora.md), y el
recorrido semana a semana en [`CRONOLOGIA.md`](Documentos/DocumentoFinal/CRONOLOGIA.md).

| | |
|---|---|
| **Semana en curso** | S29 (26 de octubre al 1 de noviembre de 2026), fase 6: análisis y escritura |
| **Fecha de corte** | 2026-10-27 (lunes). Revisión del documento recortado con las anotaciones de los autores: los robots se llaman «agente»; edificio Gregorio (pisos 2 y 3) y cambio al Calatayud (pisos 3 y 4); impersonal en todo el texto; menos remisiones y menciones al director; fechas exactas; figuras de los nodos, del planificador, de la instrumentación y del error de llegada; contrato de interfaces en tabla; conclusiones y trabajos futuros reescritos |
| **Último entregable formal** | Semana 28 ([`Entregable_semana_28.tex`](Documentos/Entregables/Entregable_semana_28.tex) y su versión [`.md`](Documentos/Entregables/Entregable_semana_28.md)) |
| **Documento final** | Compila en el portátil, sin errores ([`DocumentoFinal/`](Documentos/DocumentoFinal/)): la versión vigente tiene 94 páginas y la recortada (`main_recorte.tex`), 79. El director pide entre 60 y 80 |

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

Matriz completa en [`REQUISITOS.md`](Documentos/REQUISITOS.md): los 36 requisitos verificados. RNF-03 (operación en condiciones controladas) se cerró el 27 de octubre: en la campaña solo estuvieron en el pasillo los dos autores y quien hizo de usuario.

## Pendiente

1. Documento final: la versión recortada (79 páginas) ya tiene la revisión del 27-oct, los trabajos futuros reducidos a cinco líneas y el anexo A con los siete videos del proyecto. Faltan los preliminares, confirmar la grafía del edificio Calatayud y decidir si se recorta la bibliografía (62 entradas); después, fundir el recorte en `capitulos/`.
2. Registro de misión: la etapa de cancelación sale como `8` y no como `CANCELANDO`.
3. Imagen `coordinador_jazzy` del portátil: reconstruirla con el agente nuevo.
4. Siete archivos de código copiados en los vehículos citan en comentarios la ruta vieja de planes ya
   movidos a `historial/`; se actualizan en los dos vehículos la próxima vez que estén encendidos.
