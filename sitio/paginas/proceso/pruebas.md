# Pruebas de verificación

La demostración con los vehículos se organizó como una escalera de seis pruebas. Cada una tiene un criterio escrito antes de correrla, y la siguiente solo tiene sentido si la anterior se superó. Los criterios los propusieron los autores y los decidió el director; después de la última fecha de revisión, el 16 de octubre, no se tomaron más datos.

<div class="escalera">
  <div class="escalon"><div class="num">Prueba 1 · 22 de septiembre</div><h3>Actuación</h3><div class="criterio">El vehículo responde a las órdenes de dirección y tracción.</div><div class="resultado"><span class="estado-ok">Superada</span><br>Los dos vehículos completaron la prueba de actuación entera.</div></div>
  <div class="escalon"><div class="num">Prueba 2 · 2 de octubre</div><h3>Odometría</h3><div class="criterio">Error de 10 % o menos sobre un recorrido conocido de 5 m o más.</div><div class="resultado"><span class="estado-ok">Superada</span><br>+3,3 % sobre 14,57 m y −4,6 % sobre 6,68 m, con flexómetro.</div></div>
  <div class="escalon"><div class="num">Prueba 3 · 7 de octubre</div><h3>Navegación de un vehículo</h3><div class="criterio">Un recorrido de punto a punto con la llegada verificada a 0,5 m o menos.</div><div class="resultado"><span class="estado-ok">Superada</span><br>Tres tramos encadenados; llegadas medidas a 0,06 m y 0,45 m.</div></div>
  <div class="escalon"><div class="num">Prueba 4 · 22 de septiembre</div><h3>Dos vehículos en la misma red</h3><div class="criterio">Los dos vehículos y el coordinador coexisten sin conflicto de nombres.</div><div class="resultado"><span class="estado-ok">Superada</span><br>Se adelantó porque no dependía de la odometría.</div></div>
  <div class="escalon"><div class="num">Prueba 5 · 16 de octubre</div><h3>Misión con relevo</h3><div class="criterio">Una misión con relevo de extremo a extremo sobre los dos vehículos, con su registro.</div><div class="resultado"><span class="estado-ok">Superada</span><br>Salón 302 → Salón 402 en 132,5 s.</div></div>
  <div class="escalon"><div class="num">Prueba 6 · 16 de octubre</div><h3>Campaña con los vehículos</h3><div class="criterio">Entre 5 y 10 misiones del protocolo completo, con su registro.</div><div class="resultado"><span class="estado-ok">Superada</span><br>9 misiones del sorteo completadas. <a href="../../resultados/#con-los-vehiculos">Ver resultados</a></div></div>
</div>

## La odometría, el paso del que dependía todo

El vehículo no tiene codificadores en las ruedas. Su avance sale de comparar barridos del láser, y durante meses esa medida no sirvió. La gráfica muestra la fracción del avance real que registró, medida con flexómetro, en cada entorno. La franja verde es el criterio de la prueba: entre 90 % y 110 %.

<div class="grafica" data-grafica='{
  "tipo": "barras-h", "titulo": "Avance registrado por la odometría, como porcentaje del avance real",
  "sub": "El estimador es el mismo en todas las filas; lo que cambia es el entorno.",
  "min": 0, "max": 120, "marcas": [0, 25, 50, 75, 100], "unidad": " %", "decimales": 1,
  "banda": [90, 110], "bandaTexto": "criterio", "izquierda": 270,
  "datos": [
    {"etiqueta": "Pasillo simulado, 46,9 m", "valor": 37.9, "nota": "no cumple"},
    {"etiqueta": "Pasillos de los pisos 1 y 2 (a)", "valor": 5.7, "nota": "no cumple"},
    {"etiqueta": "Pasillos de los pisos 1 y 2 (b)", "valor": 1.3, "nota": "no cumple"},
    {"etiqueta": "Hall del piso 2, 6 m", "valor": 73, "nota": "no cumple"},
    {"etiqueta": "Cuarto cerrado, 3 m", "valor": 99.1, "texto": "96,3–101,9 %", "nota": "cumple"},
    {"etiqueta": "Pasillo del piso 4, 6,68 m", "valor": 95.4, "nota": "cumple"},
    {"etiqueta": "Pasillo del piso 4, 14,57 m", "valor": 103.3, "nota": "cumple"},
    {"etiqueta": "Piso 4 con unidad inercial, 8,08 m", "valor": 101.9, "nota": "cumple"}
  ]
}'></div>

En un pasillo recto y uniforme, cada barrido es casi igual al anterior y la información de avance no está en la señal: ningún ajuste del algoritmo la recupera. Por eso la solución fue cambiar de entorno, a un pasillo con hornacinas, casilleros y quiebres.

## La navegación y la precisión de llegada

En la primera sesión en el piso 4 las dos llegadas medidas quedaron a 0,57 y 0,62 m, cortas: la navegación daba la meta por alcanzada a 1,0 m. Con la unidad inercial el margen bajó a 0,5 m, y en la sesión siguiente un vehículo encadenó tres tramos sin que nadie lo tocara.

<figure markdown>
![Recorrido de tres tramos en el piso 4 y regreso a la salida](../img/cadena_piso4.png)
<figcaption>Piso 4, 7 de octubre: tres tramos encadenados (Salón 403, 402 y 401) y el regreso a la salida. Los círculos marcan la tolerancia de 0,5 m.</figcaption>
</figure>

| Tramo | Destino | Tiempo | Recuperaciones | Distancia a la meta | Cómo se midió |
|---|---|---|---|---|---|
| 1 | Salón 403 | 13,5 s | 1 | 0,26 m | estimada |
| 2 | Salón 402 | 27,8 s | 1 | 0,45 m | flexómetro |
| 3 | Salón 401 | 5,2 s | 0 | 0,06 m | flexómetro |
| Regreso | Salida | 62,8 s | 6 | 0,34 m | flexómetro |

!!! warning "Lo que limita la precisión"
    El vehículo no se mueve con órdenes por debajo de 0,40 m/s, así que se aproxima a la meta a esa velocidad y no tiene un régimen de aproximación fina. Es un límite de la plataforma, no del controlador.
