# Estado del proyecto

Tablero corto del avance. El proyecto cumplió sus cuatro objetivos específicos. Se actualiza los viernes en la noche, con el corte de la semana. La bitácora
completa hasta el 24 de octubre de 2026 (lecturas de avance, decisiones, riesgos cerrados y discrepancias)
está en [`Documentos/historial/ESTADO_bitacora.md`](Documentos/historial/ESTADO_bitacora.md), y el
recorrido semana a semana en [`CRONOLOGIA.md`](Documentos/DocumentoFinal/CRONOLOGIA.md).

| | |
|---|---|
| **Semana en curso** | S31 (9 al 15 de noviembre de 2026): elaboración del documento final |
| **Fecha de corte** | 2026-11-12 (jueves). Correcciones del director al documento, registradas en [`CORRECCIONES_2026-11-11.md`](Documentos/DocumentoFinal/CORRECCIONES_2026-11-11.md) y aplicadas en [`main_definitivo.pdf`](Documentos/DocumentoFinal/main_definitivo.pdf), antes `main_objetivos.pdf` (65 hojas, 51 numeradas): estado del arte comparado trabajo por trabajo, capítulo de discusión, conclusiones orientadas a cada objetivo, trabajos futuros desde la literatura, red sin direcciones MAC y con el portátil y el teléfono en 5 GHz. Fusionado el pull request 8 de Jonny, con su dedicatoria. Corte anterior, 2026-11-09: propuesta del documento por objetivos enviada al director. |
| **Último entregable formal** | Semana 29 ([`Entregable_semana_29.tex`](Documentos/Entregables/Entregable_semana_29.tex) y su versión [`.md`](Documentos/Entregables/Entregable_semana_29.md)) |
| **Documento final** | Compila en el portátil, sin errores ([`DocumentoFinal/`](Documentos/DocumentoFinal/)): la versión definitiva es [`main_definitivo.pdf`](Documentos/DocumentoFinal/main_definitivo.pdf), con 51 páginas numeradas y 65 hojas, las dos dedicatorias y las correcciones del director del 11 y el 12 de noviembre. La versión que se le entregó para revisión está en el commit `8fa9f2a`; `main.pdf`, `main_60.pdf`, `main_propuesta.pdf` y `main_integrada.pdf` son versiones anteriores o alternativas. La revisión de referencias y redacción del 4 de noviembre está en [`REVISION_2026-11-04.md`](Documentos/DocumentoFinal/REVISION_2026-11-04.md). |

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

Matriz completa en [`REQUISITOS.md`](Documentos/REQUISITOS.md): los 36 requisitos verificados. RNF-03 (operación en condiciones controladas) se cerró el 27 de octubre: en la campaña solo estuvieron en el pasillo los dos autores, que hicieron de usuario.

## Pendiente

1. Documento final: faltan la dedicatoria de Jonny, en `capitulos/01-dedicatoria-agradecimientos.tex`, y el nombre del Vicerrector Académico General, que la plantilla incluye. La versión definitiva es `main_definitivo` (antes `main_objetivos`; 65 hojas, 51 numeradas), con las correcciones del director del 11 de noviembre.
2. Presustentación (2 a 6 de noviembre, fuera del cronograma; día sin confirmar): la propuesta de presentación está en [`Presustentacion.pptx`](Documentos/Presentacion/Presustentacion.pptx), con la plantilla de la presentación del anteproyecto: 39 diapositivas y notas del orador que suman 17 min 20 s. Se arma con `python3 herramientas/presentacion_sustentacion.py` y falta la revisión de los autores. La tarjeta de acceso del jurado, con los códigos QR de la red y de la página, se genera ese día con `python3 herramientas/tarjeta_jurado.py`, con el portátil ya en la red `DEEPRACER` (pide la clave al ejecutarse).
3. Registro de misión: la etapa de cancelación sale como `8` y no como `CANCELANDO`.
4. Imagen `coordinador_jazzy` del portátil: reconstruirla con el agente nuevo.
5. Siete archivos de código copiados en los vehículos citan en comentarios la ruta vieja de planes ya
   movidos a `historial/`; se actualizan en los dos vehículos la próxima vez que estén encendidos.
