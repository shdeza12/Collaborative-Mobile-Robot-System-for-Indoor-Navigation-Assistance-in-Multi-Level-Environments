# Estado del proyecto — tablero de trazabilidad

> Fuente única de verdad del avance. Se actualiza **al cerrar cada sesión de trabajo**, antes del commit.
> Documento de referencia: `Documentos/Anteproyecto_Jonny_Santi.pdf` (cronograma en Cap. 8).

| | |
|---|---|
| **Semana del cronograma** | S17 de 32 |
| **Fecha de corte** | 2026-08-03 |
| **Fases activas** | Fase 4 — Desarrollo (S11–S17, cerrando) · Fase 5 — Integración (S16–S20, iniciando) |
| **Semanas restantes** | 15 (documento final S25–S30, sustentación S30–S32) |
| **Último entregable formal** | Semana 15 |
| **Entregables pendientes** | S16, S17 |

---

## 1. Avance por objetivo específico

| ID | Objetivo específico (anteproyecto §4.2) | Avance | Evidencia verificable | Responsable |
|----|------------------------------------------|--------|------------------------|-------------|
| **OE1** | Modelar arquitectura funcional: requisitos, escenarios multipiso, asignación de tareas, esquema de comunicación | 🟡 40 % | `Documentos/Evidencia/arquitectura.png` (diagrama completo con protocolo de relevo). **Falta:** documento de requisitos funcionales numerados y matriz de trazabilidad | — |
| **OE2** | Plataforma robótica con **dos** vehículos: locomoción, sensado, procesamiento y **comunicación** | 🟡 25 % | Un robot en Gazebo, `deepracer_sim.launch.py`, stack de sensores validado (S14), SLAM 2D (S15). **Falta:** segundo agente, namespaces, servidor de coordinación, comunicación inter-robot | — |
| **OE3** | Interfaz móvil HRI (selección origen–destino) | 🔴 0 % | Ninguna | — |
| **OE4** | Evaluación con métricas: tiempo de respuesta, tiempo de asignación, tasa de éxito, continuidad entre niveles | 🔴 0 % | Ninguna. No existe instrumentación ni protocolo experimental | — |

**Lectura:** a S17 de 32 (53 % del calendario) el avance técnico agregado está cerca del 20 %. El aporte declarado del proyecto —coordinación inter-robot y protocolo de relevo— aún no tiene implementación.

---

## 2. Camino crítico

Ordenado por dependencia. Nada de lo que sigue puede saltarse.

| # | Hito | Bloquea a | Estado |
|---|------|-----------|--------|
| 1 | **Mapa 2D utilizable** del primer piso (cobertura completa, sin deriva) | AMCL → Nav2 → todo lo demás | 🔴 El mapa actual no sirve (ver §4) |
| 2 | **Navegación autónoma punto a punto** de un robot con restricción Ackermann | Guiado, relevo, métricas | 🔴 No iniciado |
| 3 | **Mundo con segundo piso y zona de transición** | Protocolo de relevo, OE4 | 🔴 No existe |
| 4 | **Segundo agente + servidor de coordinación** | OE2, protocolo de relevo | 🔴 No iniciado |
| 5 | **Protocolo de relevo** (máquina de estados) | OE4, núcleo del aporte | 🔴 No iniciado |
| 6 | **Interfaz HRI** | OE3 | 🔴 No iniciado |
| 7 | **Instrumentación de métricas** | OE4, Fase 6 | 🔴 No iniciado |

---

## 3. Decisión de alcance vigente

**Estrategia adoptada (2026-08-03): validación completa en simulación, hardware como demostración.**

- Los cuatro objetivos específicos se validan en **simulación** (dos robots, dos pisos, relevo, métricas con N repeticiones).
- El prototipo físico queda como **demostración de viabilidad** en un piso, con relevo emulado.
- **Razón:** el aporte declarado es la arquitectura de coordinación, no la locomoción. Con 15 semanas restantes, apostar a dos vehículos físicos + dos pisos reales + app móvil arriesga terminar sin ninguno de los dos.

> ⚠️ **Pendiente:** esta decisión debe presentarse formalmente a los directores (Mateus, Ospina, Gélvez) y quedar en acta antes de S19.

---

## 4. Riesgos abiertos

| ID | Riesgo | Impacto | Mitigación | Estado |
|----|--------|---------|------------|--------|
| R1 | **El mapa guardado no es utilizable.** `primer_piso.pgm` cubre 23,0 m × 15,7 m; el mundo mide 58,2 m × 6,7 m. Presenta deriva y paredes dobladas | Bloquea AMCL y Nav2 → bloquea todo | Repetir la sesión de mapeo a velocidad baja, con cierre de bucle, y verificar cobertura antes de guardar | 🔴 Abierto |
| R2 | **Ackermann vs. Nav2.** El controlador por defecto (DWB) asume tracción diferencial; el DeepRacer no gira sobre su eje | Trayectorias inejecutables | Usar Smac Hybrid-A* + controlador con restricción no holonómica (previsto en el diagrama de arquitectura) | 🔴 Abierto |
| R3 | **Ambigüedad de localización.** Pasillo largo de paredes lisas y repetitivas → AMCL propenso a divergir | Falsos negativos en las métricas de OE4 | Evaluar landmarks en el mundo o fusión con odometría visual | 🟡 Identificado |
| R4 | **Pared sur abierta en el SDF** deja celdas desconocidas | Afecta planificación, no solo el mapa | Cerrar la geometría en `primer_piso_v2.world` | 🟡 Identificado (desde S14) |
| R5 | **Fases 2 y 3 sin artefacto verificable.** No existe documento de requisitos | Imposibilita §7.4 del anteproyecto ("comparación con requisitos") | Reconstruir la matriz RF↔OE↔prueba | 🔴 Abierto |
| R6 | **Discrepancias informe ↔ repositorio** (ver §5) | Credibilidad de la evidencia ante el jurado | Corregir en el entregable de cierre de fase | 🔴 Abierto |

---

## 5. Discrepancias detectadas entre informes y artefactos

Registradas el 2026-08-03 para corrección explícita:

| Informe dice | Artefacto en disco | Acción |
|---|---|---|
| S15: mapa guardado como `primer_piso_mapa.pgm/.yaml` vía servicio `/slam_toolbox/save_map` | `primer_piso.pgm/.yaml`; la guía operativa instruye `map_saver_cli` | Unificar nombre y procedimiento |
| S15 Tabla 1 y §5: `resolution = 0.05` m/celda | `primer_piso.yaml` declara `resolution: 0.06` | Corregir el informe o regenerar el mapa |
| S15 §3.4: "la extensión del mapa es consistente con las dimensiones del pasillo (44 m × 5 m)" | El mapa cubre 23,0 m × 15,7 m | Afirmación no sostenida por el artefacto |
| S15 Tabla 2: "Captura del quiebre en L — Satisfactorio" | No es identificable en el mapa guardado | Reevaluar tras repetir el mapeo |

---

## 6. Desviaciones respecto al anteproyecto

Deben justificarse por escrito en el documento final:

| Anteproyecto | Realidad | Justificación |
|---|---|---|
| Plataforma DonkeyCar (presupuesto: chasis, PCA9685) | AWS DeepRacer | Pendiente de redactar |
| Simulador CoppeliaSim | Gazebo Classic 11 | Pendiente de redactar |
| ROS 2 "Humble o Jazzy" | Humble | Cerrar la ambigüedad |

---

## 7. Bitácora de decisiones

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-08-03 | Se restablece el vínculo git del directorio local con el repositorio remoto | El directorio de trabajo era una copia sin historial; `primer_piso_v2.world` (18-jun) llevaba 7 semanas sin respaldo |
| 2026-08-03 | Se adopta `ESTADO.md` como tablero único de trazabilidad | Los informes semanales registraban actividad, pero no el estado agregado frente a los objetivos |
| 2026-08-03 | Alcance: validación en simulación, hardware como demostración | Ver §3 |

---

## 8. Próximos pasos (S17–S18)

1. Reconstruir la **matriz de requisitos RF↔OE↔prueba** (cierra R5 y habilita §7.4 del anteproyecto).
2. Repetir la **sesión de mapeo** con verificación de cobertura antes de guardar (cierra R1).
3. Definir el **protocolo experimental de OE4** — determina qué instrumentar en el código antes de escribirlo.
4. Emitir los **entregables S16 y S17** pendientes.
5. Llevar la **decisión de alcance** a los directores.
