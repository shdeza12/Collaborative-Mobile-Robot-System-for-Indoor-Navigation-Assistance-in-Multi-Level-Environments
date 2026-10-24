# Documento final — lo que falta por completar

**Última revisión:** 2026-10-19
**Estado del documento:** la toma de datos cerró el 16 de octubre (corte C-3 del
[`ACTA_GO_NOGO.md`](../ACTA_GO_NOGO.md)) y los resultados del sistema completo,
las conclusiones, los trabajos futuros y el resumen están redactados con esos
datos. Ya no queda ningún bloque «Apartado en curso» en el PDF. Lo que falta son
los datos institucionales y las decisiones de §1 a §4.

Esta lista estaba dentro del PDF, en bloques «Nota para la revisión». Se sacaron
de ahí —no son texto del documento— pero los pendientes son reales y siguen
abiertos, así que viven aquí. El texto original sigue en los capítulos, apagado
con `\ustanotasrevisorfalse` en `main.tex`; se vuelve a ver borrando esa línea.

---

## 1. Datos institucionales · `capitulos/00-autoridades.tex` y `main.tex`

Tres datos que **no se deben transcribir de una plantilla**, porque cambian y una
equivocación se ve en la primera página.

| Qué | Qué dice hoy el documento | Qué hace falta |
|---|---|---|
| Autoridades académicas | `NOMBRES COMPLETOS` | Verificarlos en la fuente oficial de la Universidad |
| Grupo de investigación | «GED — Grupo de Estudio y Desarrollo en Robótica» | Confirmarlo. Es el nombre que llevan el anteproyecto y los ocho entregables semanales; si el oficial fuera «Investigación y Desarrollo», hay que corregirlo **en todos ellos**, no solo aquí |
| Línea de investigación | «Robótica y Sistemas Autónomos» | Confirmar la denominación exacta con el director |

## 2. Antecedente interno sin referencia · cerrado el 2026-10-20

El anteproyecto atribuía a **Parra Buitrago (2021)** un trabajo de la Universidad sobre asistencia a
personas invidentes, sin referencia completa. Decisión de los autores: no se incluye. Se borró la nota
que pedía la referencia.

## 3. Marco legal y ambiental · cerrado el 2026-10-20

Quedan como están: las dos políticas CONPES, la NTC 1486 y el alcance de la operación. Decisión de los
autores: por ahora no se desarrollan accesibilidad en edificaciones, datos personales ni uso del
espectro. Se borró la nota al revisor que lo preguntaba.

## 4. Dedicatoria · `capitulos/01-dedicatoria-agradecimientos.tex`

La escriben los autores, una página por autor. Está comentada con las
instrucciones para activarla: una página con el título y nada debajo es peor que
no ponerla. Los agradecimientos sí están escritos.

---

## 5. Resultados del sistema completo · cerrado el 2026-10-19

Los apartados que esperaban datos (la navegación y la llegada, el sistema completo
con los dos vehículos, las conclusiones del segundo y el cuarto objetivo y los
trabajos futuros) están redactados con la evidencia de
[`S27_campana_rf27.md`](../Evidencia/S27_campana_rf27.md). La figura de etapas
de la campaña sale de `herramientas/figura_campana_vehiculos.py`.

El 19 de octubre se añadió al desarrollo la sección «Recorrido del trabajo»
(DonkeyCar, migración a Humble, primeros entornos, integración en simulación y
vehículos físicos). Su fuente es [`CRONOLOGIA.md`](CRONOLOGIA.md), que reúne
semana a semana los entregables 10 a 27 y los commits.

Queda un dato que, si llega, cambia una frase (el otro se cerró el 23 de octubre):

| Dato | Dónde iría |
|---|---|
| Si hubo personas en el pasillo durante las misiones de la campaña | Resultados, «Condiciones de las pruebas» del sistema completo |
| ~~La prueba de los ajustes de la página con un teléfono y los vehículos~~ | Hecha el 2026-10-23 ([`S28_campo_pagina_cancelacion.md`](../Evidencia/S28_campo_pagina_cancelacion.md)); escrita en «Ajustes tras las pruebas con los vehículos» y, con la cancelación en los vehículos, en «Cancelación» |
