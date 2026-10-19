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

## 2. Antecedente interno sin referencia · `capitulos/06-marco-referencial.tex`

El anteproyecto menciona un trabajo de la Universidad Santo Tomás sobre asistencia
a personas invidentes en la primera planta, atribuido a **Parra Buitrago (2021)**.
Allí se cita por nombre y año, pero **no figura en la bibliografía**.

No está en el §2.1 porque no se ha podido localizar la referencia completa. Es el
antecedente más próximo en contexto institucional y merece quedar bien citado.
**Falta:** la referencia, o el dato que permita completarla.

## 3. Marco legal y ambiental · `capitulos/06-marco-referencial.tex` §2.4 y §2.5

Están redactados **solo con lo que se pudo verificar**: las dos políticas CONPES
que ya citaba el anteproyecto y la NTC 1486, que la plantilla institucional
declara como su base.

Quedan tres puntos sin redactar, a propósito, porque una cita normativa mal hecha
es peor que un vacío señalado:

- accesibilidad en edificaciones,
- tratamiento de datos personales,
- uso del espectro.

**Falta decidir** cuáles de los tres aplican de verdad a un prototipo de este
alcance, y si las dos secciones se desarrollan por completo o basta con el
encuadre actual.

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

Quedan dos datos que, si llegan, cambian una frase:

| Dato | Dónde iría |
|---|---|
| Si hubo personas en el pasillo durante las misiones de la campaña | §4.3.1, condiciones de las pruebas |
| La prueba de los ajustes de la página con un teléfono y los vehículos | §3.4.5; hoy dice que se verificaron con pruebas automáticas |
