# Resultados

Hubo dos campañas, y se reportan por separado porque miden cosas distintas. La de **simulación** mide el sistema completo con relevo en condiciones controladas. La de los **agentes físicos** mide hasta dónde llega la plataforma física en el edificio.

## La tasa de éxito

Una misión cuenta como exitosa si termina sin fallar, con un relevo cuando es entre pisos, y con el agente a menos de la tolerancia del destino: 0,25 m en simulación y 0,5 m con los agentes físicos. El punto es la tasa observada; la línea, el intervalo de confianza del 95 % (Wilson).

<div class="grafica" data-grafica='{
  "tipo": "intervalos", "titulo": "Misiones completadas, con su intervalo de confianza",
  "min": 40, "max": 100, "marcas": [40, 50, 60, 70, 80, 90, 100], "izquierda": 250,
  "datos": [
    {"etiqueta": "Simulación, las 30", "valor": 86.7, "bajo": 70.3, "alto": 94.7, "texto": "26 de 30", "serie": 1},
    {"etiqueta": "Simulación, mismo piso", "valor": 80.0, "bajo": 54.8, "alto": 93.0, "texto": "12 de 15", "serie": 1},
    {"etiqueta": "Simulación, con relevo", "valor": 93.3, "bajo": 70.2, "alto": 98.8, "texto": "14 de 15", "serie": 1},
    {"etiqueta": "Agentes físicos, con relevo", "valor": 100, "bajo": 70.1, "alto": 100, "texto": "9 de 9", "serie": 2}
  ],
  "leyenda": [[1, "Simulación"], [2, "Agentes físicos"]]
}'></div>

!!! abstract "Lo que se puede afirmar"
    Con estas muestras, que la tasa de éxito **supera el 70 %**, en simulación y con los agentes físicos. Nada más estrecho: con 30 misiones el intervalo mide 24 puntos de ancho, y eso solo se reduce con más repeticiones. Los intervalos de las misiones con y sin relevo se solapan, así que no se puede decir que una sea mejor que la otra.

Los cuatro fallos de la simulación se quedaron cortos: a 0,295, 0,284, 0,311 y 0,347 m del destino, frente a 0,25 m. Ninguno fue de coordinación; los cuatro son de precisión en la aproximación final.

## En simulación

<div class="dos-graficas" markdown>

<div class="grafica" data-grafica='{
  "tipo": "barras-v", "titulo": "Tiempo de respuesta de las 30 misiones",
  "sub": "El reloj de la simulación avanza de a 100 ms, así que el tiempo se reporta por escalones.",
  "min": 0, "max": 16, "marcas": [0, 5, 10, 15], "decimales": 0, "unidad": "misiones",
  "ejeX": "tiempo desde la solicitud hasta el primer movimiento",
  "columnas": ["Tiempo de respuesta", "Misiones"],
  "datos": [
    {"etiqueta": "0,1 s", "valor": 10}, {"etiqueta": "0,2 s", "valor": 15},
    {"etiqueta": "0,3 s", "valor": 4}, {"etiqueta": "0,4 s", "valor": 1}
  ]
}'></div>

<div markdown>
**Lo que dicen estos números**

- El agente arranca en **menos de medio segundo** en las 30 misiones.
- La **asignación** del agente tarda tan poco que el reloj de la simulación no la ve. Medida aparte con el reloj del sistema: mediana entre 154 y 175 µs, máximo 306 µs.
- El **error de llegada** tiene mediana de 0,106 m, entre 0,019 y 0,347 m.
- La simulación corrió a tiempo real: factor mínimo de 0,9917 en las 30 misiones.
</div>

</div>

<figure markdown>
![Una misión con relevo entre los dos procesos de simulación, uno por piso](img/simulacion_relevo.png)
<figcaption>Una misión con relevo en simulación: cada piso corre en su propio proceso, y el coordinador reparte los tramos.</figcaption>
</figure>

!!! info "Comprobación en los pisos 3 y 4, 2 de noviembre"
    Después de las dos campañas, el sistema se corrió en simulación en los pisos 3 y 4: 13 misiones encadenadas, 10 completadas y 3 canceladas a propósito, ninguna fallida, con llegadas entre 0,067 y 0,206 m. Es una comprobación de funcionamiento: no se grabó como la campaña y no entra en las tasas de esta página. [Ver la evidencia](https://github.com/shdeza12/Collaborative-Mobile-Robot-System-for-Indoor-Navigation-Assistance-in-Multi-Level-Environments/blob/main/Documentos/Evidencia/S30_simulacion_catalayud.md).

<div class="galeria" markdown>

<figure markdown>
![El mundo del piso 3 en Gazebo, con su agente en la salida y el barrido del láser en azul](img/simulacion_catalayud_piso3.png)
<figcaption>El piso 3 en Gazebo, con su agente en la salida, frente a la escalera.</figcaption>
</figure>

<figure markdown>
![El mundo del piso 4 en Gazebo, con su agente en la salida y el barrido del láser en azul](img/simulacion_catalayud_piso4.png)
<figcaption>El piso 4 en Gazebo, con su agente en la salida, frente a la escalera.</figcaption>
</figure>

</div>

## Con los agentes físicos

Nueve misiones del sorteo, en su orden y sin reubicar los agentes entre una y otra, entre los pisos 3 y 4 del edificio. Todas con relevo en la escalera.

<div class="dos-graficas" markdown>

<div class="grafica" data-grafica='{
  "tipo": "barras-v", "titulo": "Duración de cada misión",
  "sub": "Desde la solicitud hasta la llegada. Incluye el tiempo que el usuario tarda en cambiar de piso.",
  "min": 0, "max": 120, "marcas": [0, 30, 60, 90, 120], "decimales": 0, "unidad": "s", "rotulos": false,
  "ejeX": "número de misión", "columnas": ["Misión", "Duración"],
  "datos": [
    {"etiqueta": "1", "nombre": "1 · Ascensor (piso 3) → Salón 403", "valor": 52.3, "texto": "52"},
    {"etiqueta": "2", "nombre": "2 · Salón 302 → Salón 401", "valor": 90.1, "texto": "90"},
    {"etiqueta": "3", "nombre": "3 · Salón 401 → Salón 302", "valor": 87.6, "texto": "88"},
    {"etiqueta": "4", "nombre": "4 · Salón 403 → Salón 303", "valor": 78.9, "texto": "79"},
    {"etiqueta": "5", "nombre": "5 · Salón 402 → Salón 301", "valor": 105.4, "texto": "105"},
    {"etiqueta": "6", "nombre": "6 · Salón 301 → Salón 401", "valor": 89.8, "texto": "90"},
    {"etiqueta": "7", "nombre": "7 · Ascensor (piso 4) → Salón 301", "valor": 81.7, "texto": "82"},
    {"etiqueta": "8", "nombre": "8 · Salón 302 → Salón 403", "valor": 81.8, "texto": "82"},
    {"etiqueta": "9", "nombre": "9 · Salón 303 → Salón 402", "valor": 92.6, "texto": "93"}
  ]
}'></div>

<div class="grafica" data-grafica='{
  "tipo": "barras-v", "estilo": "puntos", "titulo": "Distancia al destino al llegar",
  "sub": "Según la localización del propio agente, 1,5 s después de detenerse.",
  "min": 0, "max": 0.6, "marcas": [0, 0.1, 0.2, 0.3, 0.4, 0.5], "decimalesEje": 1, "decimales": 2, "unidad": "m",
  "umbral": 0.5, "umbralTexto": "tolerancia 0,5 m", "ejeX": "número de misión", "rotulos": false,
  "columnas": ["Misión", "Distancia al destino"],
  "datos": [
    {"etiqueta": "1", "nombre": "1 · Ascensor (piso 3) → Salón 403", "valor": 0.435},
    {"etiqueta": "2", "nombre": "2 · Salón 302 → Salón 401", "valor": 0.202},
    {"etiqueta": "3", "nombre": "3 · Salón 401 → Salón 302", "valor": 0.143},
    {"etiqueta": "4", "nombre": "4 · Salón 403 → Salón 303", "valor": 0.420},
    {"etiqueta": "5", "nombre": "5 · Salón 402 → Salón 301", "valor": 0.285},
    {"etiqueta": "6", "nombre": "6 · Salón 301 → Salón 401", "valor": 0.226},
    {"etiqueta": "7", "nombre": "7 · Ascensor (piso 4) → Salón 301", "valor": 0.234},
    {"etiqueta": "8", "nombre": "8 · Salón 302 → Salón 403", "valor": 0.214},
    {"etiqueta": "9", "nombre": "9 · Salón 303 → Salón 402", "valor": 0.299}
  ]
}'></div>

</div>

<div class="cifras">
  <div class="cifra"><div class="valor">87,6 s</div><div class="que">duración mediana de una misión entre pisos</div></div>
  <div class="cifra"><div class="valor">0,87 s</div><div class="que">mediana desde la solicitud hasta el primer movimiento</div></div>
  <div class="cifra"><div class="valor">0,3 ms</div><div class="que">en asignar el agente, con el reloj del portátil</div></div>
  <div class="cifra"><div class="valor">9 de 9</div><div class="que">misiones sin interrupción del guiado en el relevo</div></div>
</div>

!!! warning "Cómo leer estas cifras"
    - La distancia de llegada de esta campaña es la que da la localización de cada agente. La prueba de navegación ya la había comprobado con medidas directas: el 7 de octubre esa localización quedó a 0,10 m o menos de la medida en el avance, y por eso no fue necesario repetir la medida.
    - Las misiones 1 y 2 se completaron en un segundo intento: el primero de la 1 terminó a 0,526 m del destino, fuera de la tolerancia, y el de la 2 sin poder verificar la llegada. Por decisión del equipo, la tasa cuenta una corrida por misión.
    - Antes de la primera misión válida, la navegación de los dos agentes se detuvo y hubo que reiniciarla; la causa no se estableció.
    - La misión 10 no terminó: el computador del coordinador se apagó por batería.
