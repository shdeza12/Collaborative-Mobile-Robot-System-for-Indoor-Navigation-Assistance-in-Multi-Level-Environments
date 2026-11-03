# Términos del proyecto

Una sola palabra para cada cosa en todo lo que leen o escuchan personas ajenas al equipo: el documento final, la
presentación y su guion, el sitio, el README y lo que se les dice a los jurados.

Decisiones de los autores: «agente», el 27 de octubre de 2026; «el usuario» y «piso», el 3 de noviembre. Se dice «piso» porque así lo nombra el título del proyecto. Las definiciones
están en el [glosario del documento](DocumentoFinal/capitulos/03-glosario-abreviaturas.tex).

## Los términos

| Para nombrar | Se dice | En lugar de |
|---|---|---|
| Cada uno de los dos robots del proyecto | agente; agentes físicos cuando se contrasta con la simulación | robot, vehículo, carro, unidad, el DeepRacer, deepy, racey, `amss-…` |
| Quien pide el servicio y es guiado | el usuario | la persona, el visitante |
| Cada piso del edificio | piso | planta, nivel |
| La plataforma de hardware | AWS DeepRacer | el DeepRacer, el carro |
| Lo que el usuario abre en el teléfono | la página, o la interfaz web | la aplicación, la app |
| El nodo que reparte los tramos | el coordinador | el servidor central, el nodo central |
| El computador del coordinador | el portátil; la primera vez, el computador portátil | el laptop, el PC |
| El computador de cada agente | la tarjeta | la placa, el computador de a bordo |
| El sensor de distancia | el láser; LiDAR solo al definirlo | el LiDAR |
| El sensor inercial | la unidad inercial; IMU solo en las abreviaturas | la IMU |
| Una solicitud de guiado completa | la misión, dividida en tramos | la tarea, el viaje |
| El traspaso del guiado entre agentes | el relevo | la entrega, el cambio de robot |
| El lugar del relevo | la escalera; el punto de transferencia en lo técnico | el punto de relevo |
| La maniobra para girar en un pasillo estrecho | la media vuelta | el volteo, el giro en U |
| Los equipos de la red | el enrutador y el punto de acceso | el router, el encaminador, el AP |
| Las pruebas y los requisitos | por su contenido: la prueba de odometría, el requisito de latencia | G-2, RF-15, OE1, compuerta |

La primera mención de los agentes en un documento lleva aposición: «dos agentes, robots móviles terrestres, uno por piso».

## Lo que se conserva

- Los textos oficiales, literales: el título, la pregunta problema y los objetivos, que dicen «robots», «visitantes»,
  «vehículos tipo DonkeyCar» y «niveles». También la métrica que sale del cuarto objetivo, «continuidad entre niveles».
- «Robot» para los de otros trabajos o en general: «un robot de ruedas no sube escaleras». También sistema multirrobot,
  interacción humano-robot y ROS.
- «Personas» cuando no son el usuario: quienes pasan por el pasillo, quien acompaña a un agente en una prueba, los
  participantes de los trabajos citados.
- «Vehículo» en enunciados generales sobre vehículos tipo automóvil: la restricción Ackermann, el A\* híbrido.
- «Planta» como plano del piso: «levantar la planta con flexómetro».
- «De varios niveles» al describir un trabajo ajeno, con las palabras de ese trabajo.
- Lo que no se traduce: `robot1`, `robot2`, `robot.sh`, `nivel:=3` y demás comandos, rutas y nombres de archivo, y las
  etiquetas de LaTeX como `tab:sim-vehiculos`, que el lector no ve.
- Las capturas de la página, que dicen «robot» porque así le habla la página al usuario.

## Dónde aplica

| Texto | Cómo queda |
|---|---|
| Documento final, versión recortada | Aplicado en todo |
| Documento final, versión larga | Aplicado en los preliminares, la introducción y la contextualización, que comparte con la recortada, y «el usuario» y «piso» en los demás capítulos. Conserva «vehículo» y «nivel» hasta fundirla con la recortada, que la reemplaza |
| Presentación y su guion | Aplicado en todo |
| Sitio y README | Aplicado en todo. Las páginas semanales salen de `sitio/generar_semanas.py`, que aplica estos términos al publicar la cronología, los informes y la evidencia. Los títulos de los documentos de evidencia conservan sus códigos y nombres |
| Lo que se les dice a los jurados | Las frases entre comillas de [`GUION_SESION_JURADOS.md`](GUION_SESION_JURADOS.md) |
| Guías, planes, bitácora y evidencia | No aplica. Son textos del equipo, y ahí siguen «vehículo», deepy, racey y RF-15. Lo ya entregado no se reescribe |

## Comprobación

Antes de publicar un capítulo, con la raíz del repositorio como carpeta de trabajo:

```bash
grep -nE '\b(la|una|esa|esta) persona\b|\bvisitantes?\b|\bveh[ií]culos?\b|\bniveles?\b|\bplantas?\b|\bLiDAR\b' Documentos/DocumentoFinal/capitulos_recorte/*.tex
```

- Esperado: solo lo que permite la sección «Lo que se conserva».
- Si aparece otra cosa: se cambia por el término de la tabla, frase por frase, porque cambia la concordancia («la persona
  confirma» pasa a «el usuario confirma», y «la lleva» a «lo lleva»).
- Cierre: el capítulo compila y el recortado sigue dentro de las 80 páginas.
