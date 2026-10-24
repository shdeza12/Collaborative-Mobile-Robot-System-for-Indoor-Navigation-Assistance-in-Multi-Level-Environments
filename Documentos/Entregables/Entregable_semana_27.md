# Informe de avance de la semana 27

Universidad Santo Tomás · Facultad de Ingeniería Electrónica · Grupo de Estudio y Desarrollo en Robótica (GED)

Sistema colaborativo de robots móviles para asistencia de orientación en entornos interiores con múltiples pisos

Realizado por: Santiago Hernández Ávila y Jonny Alejandro Mejía León

Dirigido por: Ing. Armando Mateus Rojas, Msc.; Ing. Nestor Ivan Ospina, Msc.; Ing. Oscar Mauricio Gélvez Lizarazo, Msc.

Semana 27: 12 al 18 de octubre de 2026, con corte el domingo 18. Fase 6: campaña, análisis y escritura.

> Versión en Markdown para leer en el repositorio. La versión para compilar es
> [`Entregable_semana_27.tex`](Entregable_semana_27.tex), en Overleaf, donde está el logotipo de la
> portada.

---

## 1. Introducción

Este informe presenta el avance de la semana 27 del cronograma (12 al 18 de octubre de 2026), la
última de toma de datos. El corte C-3 del acta de la decisión GO/NO-GO, el viernes 16 de octubre,
pedía dos compuertas: G-5, una misión con relevo entre los dos vehículos, y G-6, las repeticiones de
RF-27, el requisito de la demostración física con entre 5 y 10 misiones. Una misión consiste en
guiar a un usuario de un origen a un destino; el relevo es el traspaso del usuario del vehículo de un
piso al vehículo del otro, en la escalera.

Las dos compuertas se alcanzaron el 16 de octubre en los pisos 3 y 4 del edificio. Nueve misiones
del sorteo corrieron y se completaron con relevo, y la décima no terminó porque el computador
portátil del coordinador se apagó por batería. Con RF-27 verificado, los cuatro objetivos
específicos tienen todos sus requisitos verificados.

| Compuerta | Qué exige | Estado al 18 de octubre |
|---|---|---|
| G-1, actuación | El vehículo responde a las órdenes de dirección y tracción | Alcanzada el 22 de septiembre |
| G-2, odometría | Error de la odometría de hasta 10 % sobre un recorrido medido de al menos 5 m | Alcanzada el 2 de octubre |
| G-3, navegación de un vehículo | Un recorrido de punto a punto con la llegada verificada | Alcanzada el 7 de octubre |
| G-4, coexistencia | Los dos vehículos y el coordinador en la misma red, sin conflicto de nombres | Alcanzada el 22 de septiembre |
| G-5, protocolo completo | Una misión con relevo entre los dos vehículos, con su registro | Alcanzada el 16 de octubre |
| G-6, RF-27 | Entre 5 y 10 misiones del protocolo completo, con su registro | Alcanzada el 16 de octubre, con 9 misiones |

## 2. Objetivos de la semana

El cronograma fija para esta semana el siguiente criterio de cierre:

> *Presentación completa y ensayada al menos una vez de principio a fin.*

El criterio no se cumplió: la presentación no se armó en la semana. El 25 de septiembre, al
replanificar contra las fechas del acta, la campaña de RF-27 pasó a esta semana, y el trabajo se
organizó en `PLAN_S27.md` alrededor del corte C-3. La otra actividad del cronograma, las conclusiones
sobre la viabilidad técnica, tiene ya los datos que la sostienen (secciones 5 y 6).

## 3. Preparación de la campaña

Las diez misiones de G-6 se sortearon el 13 de octubre, antes de cualquier corrida, como pide el
protocolo experimental. Se usó la semilla 20261013, con cinco misiones del piso 3 al 4 y cinco del 4
al 3 entre los salones y el ascensor de cada piso, sin repetir pares y con no más de tres seguidas
en el mismo sentido (`campana_rf27_misiones.csv`).

El mismo día se corrigió la verificación de llegada del coordinador. Con las grabaciones del 7 de
octubre se comprobó que, cuando el sistema de navegación (Nav2) daba la meta por alcanzada, el
vehículo seguía moviéndose y la pose (posición y orientación) leída en ese instante lo ubicaba entre 0,53 m y 0,96 m de la
meta; un segundo después estaba entre 0,09 m y 0,53 m. El coordinador espera ahora 1,5 s antes de
comparar la pose con el punto de destino. La prueba del coordinador con vehículos simulados pasa 19
de 19 escenarios, incluidos el de la inercia y el de la media vuelta que el coordinador pide al
vehículo cuando el destino queda detrás.

## 4. Revisión de los requisitos de la plataforma robótica

El 15 de octubre se revisaron los requisitos RF-11 a RF-14 y RF-16 del segundo objetivo específico
(OE2, la plataforma robótica con dos vehículos) contra la prueba escrita de cada uno y la evidencia
de campo ya registrada: G-2, G-3 y la prueba del sistema completo en el laboratorio del 9 de
octubre. Los cinco pasaron a verificados. OE2 quedó con sus seis requisitos verificados.

## 5. Prueba del protocolo completo (G-5)

La primera sesión del 16 de octubre, entre las 17:38 y las 17:56, corrió doce misiones elegidas
por el equipo, sin seguir el sorteo. Se trata como una sesión exploratoria. De ella sale G-5: la
misión del Salón 302, en el piso 3, al Salón 402, en el piso 4, se completó con relevo en 132,5 s,
con un error de llegada de 0,444 m y 61,1 s entre el final del primer tramo y el inicio del
segundo. El registro de la misión es `G5_01.json`.

## 6. Campaña de RF-27 (G-6)

La segunda sesión, entre las 18:30 y las 19:35, corrió las misiones del sorteo en su orden, sin reubicar los vehículos entre
una y otra. El vehículo `amss-ez9n` atendió el piso 3 y `amss-jgm9` el piso 4; el coordinador y la
grabación corrieron en el portátil. Las misiones 1 a 9 se completaron, todas con relevo.

| N.º | Origen → destino | Tiempo total (s) | Respuesta (s) | Espera en el relevo (s) | Error de llegada (m) |
|---|---|---|---|---|---|
| 1 | Ascensor (piso 3) → Salón 403 | 52,3 | 0,51 | 21,06 | 0,435 |
| 2 | Salón 302 → Salón 401 | 90,1 | 0,27 | 0,85 | 0,202 |
| 3 | Salón 401 → Salón 302 | 87,6 | 3,90 | 12,92 | 0,143 |
| 4 | Salón 403 → Salón 303 | 78,9 | 1,25 | 0,71 | 0,420 |
| 5 | Salón 402 → Salón 301 | 105,4 | 0,66 | 0,68 | 0,285 |
| 6 | Salón 301 → Salón 401 | 89,8 | 2,97 | 27,48 | 0,226 |
| 7 | Ascensor (piso 4) → Salón 301 | 81,7 | 0,87 | 1,22 | 0,234 |
| 8 | Salón 302 → Salón 403 | 81,8 | 0,95 | 26,76 | 0,214 |
| 9 | Salón 303 → Salón 402 | 92,6 | 0,63 | 0,73 | 0,299 |

El tiempo de respuesta va de la solicitud al primer movimiento del vehículo. La espera en el relevo
va desde que el vehículo del primer piso termina su tramo hasta que el del segundo empieza el suyo,
y depende de cuánto tarda la persona en subir o bajar y confirmar.

| Métrica | Resultado |
|---|---|
| Tasa de éxito (RF-23) | 9 de 9, intervalo de confianza del 95 % (Wilson) del 70,1 % al 100 % |
| Tiempo de respuesta (RF-21) | Mediana 0,87 s, de 0,27 s a 3,90 s |
| Tiempo de asignación (RF-22) | 0,3 ms, con el reloj del portátil |
| Continuidad entre niveles (RF-24) | 9 de 9 misiones sin interrupción del guiado; espera mediana de 1,22 s |
| Error de llegada | Mediana 0,234 m, de 0,143 m a 0,435 m; las nueve por debajo de 0,5 m |
| Tiempo total de la misión | Mediana 87,6 s, de 52,3 s a 105,4 s |

Con nueve misiones, lo que el intervalo permite afirmar es que la tasa de éxito supera el 70 %.

Se declaran tres desviaciones del protocolo, decididas por el equipo el 18 de octubre:

1. El error de llegada es el de la localización del propio vehículo (AMCL, la localización sobre el
   mapa con el LiDAR, el sensor láser de distancias), comparada con el punto de destino 1,5 s después de que Nav2 diera la meta por
   alcanzada. El protocolo pide una medida externa con flexómetro sobre marcas en el piso, y en esta
   campaña no se tomó. La referencia disponible es la del 7 de octubre en el piso 4, donde AMCL
   quedó a 0,10 m o menos de la medida con flexómetro en el avance y a 5 cm o menos en lo lateral. Los registros
   llevan la fuente de la medida, y el análisis la declara.
2. Las misiones 1 y 2 se completaron en un segundo intento. En el primero, la 1 terminó con el
   vehículo a 0,526 m del Ascensor, fuera de la tolerancia de 0,5 m, y la 2 sin la pose necesaria
   para verificar la llegada. Esos intentos no entran en la tasa.
3. La campaña se grabó en un solo archivo, partido después por misión con la ventana de tiempo de
   cada registro del coordinador.

La misión 10 (Salón 403 → Ascensor del piso 3) no se cuenta: el portátil se apagó por batería 18 s
después de pedirla. En un intento anterior se eligió por error el Ascensor del piso 4 como destino;
ese intento no es una misión del sorteo.

## 7. Incidencias de la campaña

Antes de la primera misión válida, entre las 18:34 y las 18:58, ocho intentos de la misión 1
fallaron con la navegación detenida en los dos vehículos. En `amss-ez9n` el navegador tenía detenida la
transformada entre el mapa y la odometría (la relación entre los dos marcos de referencia) desde las 18:21, aunque la localización la seguía
publicando; en `amss-jgm9` el gestor de Nav2 lo apagó porque el planificador dejó de responder
durante 60 s. Se reiniciaron las cadenas de navegación de los dos vehículos, y la de `amss-jgm9` una
segunda vez. Desde las 19:10 las nueve misiones corrieron sin intervenir los vehículos. La causa de
las transformadas detenidas no se estableció; coincidió con cadenas que llevaban horas encendidas y
con la carga de las tarjetas entre 10 y 14.

El portátil se apagó dos veces por batería, a las 17:58 y a las 19:35. Las dos grabaciones se
recuperaron, y las originales quedan respaldadas con sus sumas de verificación.

## 8. Cambios en la interfaz y en las herramientas de registro

En la etapa de espera del relevo, la página mostraba «¿Ya subió?» también cuando el usuario bajaba
del piso 4 al 3. Ahora el título depende del sentido («Suba con calma al piso 4», «Baje con calma
al piso 3») y el botón nombra el piso. El título de una misión fallida pasó de «Camino bloqueado» a
«No se pudo completar», porque la misión también falla cuando el vehículo se detiene fuera de la
tolerancia. En campo, sin embargo, el teléfono siguió mostrando la versión anterior: el servidor de la
página solo enviaba la fecha de cada archivo, y con eso el navegador usó la copia que tenía guardada
sin consultar al servidor, incluso al recargar. Se reprodujo el 18 de octubre en el navegador del
portátil y se corrigió con un servidor que pide al navegador consultar cada archivo antes de usar su
copia. Los textos nuevos quedan por verse en el teléfono.

Para la campaña sin flexómetro, el programa que compone los registros admite una segunda fuente de la
llegada, la localización del agente, que queda escrita en cada registro y nunca como medida con
flexómetro. Una herramienta nueva parte una grabación de varias misiones en una por misión.

## 9. Documento final

Los capítulos 2 (marco referencial) y 3 (desarrollo) se reescribieron. El marco referencial se
apoyó en la literatura, con 29 referencias nuevas verificadas, y el desarrollo amplió las etapas y
los cuatro objetivos con tres figuras nuevas. El documento se revisó completo para que el lector de
la tesis no dependa de los códigos internos del proyecto. Desde el 15 de octubre compila en el
equipo del proyecto: 79 páginas, sin errores ni referencias sin resolver.

## 10. Aporte a los objetivos específicos

| Actividad | Objetivo | Aporte |
|---|---|---|
| Revisión de RF-11 a RF-14 y RF-16 | OE2 | La plataforma con dos vehículos queda con sus seis requisitos verificados |
| Prueba del protocolo completo | OE2, OE4 | G-5 alcanzada con una misión con relevo entre los dos vehículos |
| Campaña de RF-27 | OE4 | Las cuatro métricas medidas en los vehículos, con 9 misiones |
| Confirmación del cambio de piso según el sentido | OE3 | La interfaz indica si el usuario sube o baja |

| Objetivo | Avance | Aporte de la semana | Pendiente |
|---|---|---|---|
| OE1 | 100 % | — | — |
| OE2 | 100 % | RF-11 a RF-14 y RF-16 verificados | — |
| OE3 | 100 % | Texto de la confirmación según el sentido | — |
| OE4 | 100 % | RF-27 verificado con 9 misiones | — |

El avance de cada objetivo es el promedio de sus requisitos según su estado en la matriz de
requisitos. Con RF-27 verificado, el promedio de los cuatro objetivos pasa del 92,0 % de la semana 26
al 100 %, frente al 84,4 % del calendario (semana 27 de 32). De la matriz queda parcial la
restricción RNF-03, que pide registrar como observación las personas que pasan durante las pruebas.

## 11. Estado del cronograma y trabajo previsto

| Parte del criterio de cierre | Estado | Evidencia |
|---|---|---|
| Presentación completa y ensayada | No cumplida | — |
| Conclusiones sobre la viabilidad técnica | Con los datos de la campaña; sin redactar | `S27_campana_rf27.md` |

El corte C-3 cerró la toma de datos el 16 de octubre. Para las semanas siguientes el equipo prevé:

1. Redactar en el documento final los resultados del sistema completo y las conclusiones.
2. Registrar las observaciones de personas en el pasillo durante la campaña, para RNF-03.

## 12. Conclusiones

1. G-5 y G-6 se alcanzaron el 16 de octubre: nueve misiones del sorteo se completaron con relevo
   entre los dos vehículos, cada una con su registro.
2. Las nueve misiones dan 9 de 9 éxitos, con un intervalo de confianza del 95 % del 70,1 % al 100 %,
   y un error de llegada mediano de 0,234 m según la localización del vehículo, sin medida externa.
3. El sistema respondió a cada solicitud en una mediana de 0,87 s y asignó el vehículo en 0,3 ms;
   una misión entre pisos tomó una mediana de 87,6 s.
4. Con RF-27 verificado, los cuatro objetivos específicos tienen todos sus requisitos verificados.
5. Antes de la campaña, la navegación se detuvo en los dos vehículos y hubo que reiniciarla; la causa
   queda sin establecer.

## Anexo. Evidencia citada

| Documento | Qué respalda |
|---|---|
| `Documentos/ACTA_GO_NOGO.md` | Compuertas, corte C-3 y desviaciones declaradas |
| `Documentos/historial/PLAN_S27.md` | Secciones 2 y 3 |
| `Documentos/Evidencia/campana_rf27_misiones.csv` | Sorteo de la sección 3 |
| `Documentos/REQUISITOS.md` | Secciones 4 y 10 |
| `Documentos/Evidencia/S27_campana_rf27.md` | Secciones 5, 6 y 7 |
| `Documentos/Evidencia/S27_metricas_rf27.json` | Métricas de la sección 6 |
| `Documentos/Evidencia/registros/G5_01.json` y `RF27_G6_01.json` a `RF27_G6_09.json` | Registros de las secciones 5 y 6 |
| `Documentos/Evidencia/S26_piso4_cadena_media_vuelta.md` | Referencia de AMCL contra el flexómetro (sección 6) |
| `Documentos/ESQUEMA_REGISTRO_MISION.md` | Fuente de la llegada sin flexómetro (sección 8) |
| `ESTADO.md` | Secciones 3, 4, 9 y 10 |
| `Documentos/CRONOGRAMA_S17_S32.md` | Secciones 2 y 11 |
