# Qué documento seguir

Para cada tarea, el documento vigente. Los planes semanales, hojas de campo, guiones y guías de sesiones
ya pasadas están en [`historial/`](historial/): son el registro de cómo se hizo cada prueba y los cita la
bitácora de [`ESTADO.md`](../ESTADO.md), pero no se siguen hoy sin contrastarlos con lo vigente.

**Regla:** una guía nueva entra en este índice en el mismo commit en que se crea, y una guía superada pasa
a `historial/`, no se borra.

*Estado al 2026-11-03.*

| Quiero… | Seguir | Y tener a mano |
|---|---|---|
| Instalar el proyecto en un equipo nuevo | [`guia_instalacion.md`](guia_instalacion.md), pasos 1 a 6 | `herramientas/verificar_instalacion.sh` debe terminar en `0 fallan` |
| Correr el sistema completo en simulación: dos robots, coordinador, interfaz y una misión medida | [`GUIA_ARRANQUE.md`](GUIA_ARRANQUE.md) | [`GUIA_EJECUCION.md`](GUIA_EJECUCION.md) para diagnosticar una pieza suelta |
| Correr el sistema en simulación en los pisos 3 y 4 de Catalayud, sin medir | [`GUIA_PISOS_3_Y_4.md`](GUIA_PISOS_3_Y_4.md), sección 8 | [`Evidencia/S30_simulacion_catalayud.md`](Evidencia/S30_simulacion_catalayud.md) |
| Repetir la campaña en simulación | [`RUNBOOK_CAMPANA.md`](RUNBOOK_CAMPANA.md) | [`PROTOCOLO_EXPERIMENTAL.md`](PROTOCOLO_EXPERIMENTAL.md) |
| Construir o verificar un mapa en simulación | [`guia_simulacion_slam.md`](guia_simulacion_slam.md) | — |
| Navegar un robot simulado sobre un mapa | [`guia_navegacion_nav2.md`](guia_navegacion_nav2.md) | — |
| Arrancar los dos vehículos y el coordinador para una misión | [`historial/PLAN_S27.md`](historial/PLAN_S27.md) §2.2, el procedimiento usado el 16 y el 23 de octubre | [`ACTA_GO_NOGO.md`](ACTA_GO_NOGO.md) para las pruebas de verificación |
| Mostrarles el sistema a los jurados: ensayo, arranque, recorrido y contingencia | [`GUION_SESION_JURADOS.md`](GUION_SESION_JURADOS.md) | [`Evidencia/S30_segunda_mision_y_cancelacion.md`](Evidencia/S30_segunda_mision_y_cancelacion.md) |
| Navegar un vehículo real en los pisos 3 y 4 | [`GUIA_PISOS_3_Y_4.md`](GUIA_PISOS_3_Y_4.md) | — |
| Montar la red entre los dos pisos | [`TOPOLOGIA_RED.md`](TOPOLOGIA_RED.md) | Medida de la latencia en [`historial/HOJA_CAMPO_SEGUNDO_DEEPRACER.md`](historial/HOJA_CAMPO_SEGUNDO_DEEPRACER.md) §5 |
| Comprobar la IMU de un vehículo | [`PRUEBAS_IMU.md`](PRUEBAS_IMU.md) | — |
| Entender por qué los dos vehículos no se interfieren en la red | [`DISENO_AISLAMIENTO_DOS_CARROS.md`](DISENO_AISLAMIENTO_DOS_CARROS.md) | — |
| Conducir un vehículo con el mando | [`GUIA_TELEOP_MANDO.md`](GUIA_TELEOP_MANDO.md) | — |
| Registrar la evidencia de una prueba | La convención de [`Evidencia/README.md`](Evidencia/README.md) | [`historial/HOJA_CAPTURA_S26.md`](historial/HOJA_CAPTURA_S26.md) como ejemplo |
| Consultar las interfaces entre coordinador, agentes e interfaz | [`CONTRATO_INTERFACES.md`](CONTRATO_INTERFACES.md) | — |
| Escribir algo que van a leer el jurado, el director o el público | [`TERMINOS.md`](TERMINOS.md) | [Glosario del documento](DocumentoFinal/capitulos/03-glosario-abreviaturas.tex) |
| Saber dónde está el proyecto | [`ESTADO.md`](../ESTADO.md) | [`CRONOGRAMA_S17_S32.md`](CRONOGRAMA_S17_S32.md) |
| Saber qué toca esta semana | [`PLAN_S30.md`](PLAN_S30.md) | [`GUION_SESION_JURADOS.md`](GUION_SESION_JURADOS.md) |
