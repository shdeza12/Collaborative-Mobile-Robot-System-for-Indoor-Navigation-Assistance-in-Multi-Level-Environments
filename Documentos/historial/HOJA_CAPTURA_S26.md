# Hoja de captura de evidencia — semana 26

Para tener abierta en el teléfono durante las pruebas. Dice qué fotografiar, grabar o capturar en
cada prueba de [`PLAN_S26.md`](PLAN_S26.md), y con qué nombre. La convención completa está en
[`Evidencia/README.md`](../Evidencia/README.md), «Fotos de campo y videos».

**La regla:** lo que no se captura el día de la prueba no se recupera. Un informe sin imagen de la
prueba física pide al jurado que crea lo que no vio.

## Antes de salir

- [ ] Teléfono cargado y con al menos 5 GB libres.
- [ ] Una hoja con el **id de la corrida** escrito en grande (`p4r_04`, `G5_01`…). Se pone en el
      primer cuadro de cada video y de cada serie de fotos: así la imagen se identifica sola, sin
      depender de la hora del teléfono.
- [ ] El flexómetro **dentro del cuadro y con la cifra legible** en cada foto de llegada. Una foto
      de llegada sin la cinta no es una medida, es una ilustración.
- [ ] La grabación de pantalla del teléfono, probada una vez antes.

## Por prueba

| Prueba (§ del plan) | Fotos | Video | Pantalla del PC o del teléfono | Nombre |
|---|---|---|---|---|
| **Red entre pisos 3 y 4** (§2.4) | Cada punto de acceso en su sitio; el cable entre pisos | — | Panel del FiberHome (modo puente, DHCP apagado, canal y ancho); reservas MAC del TP-Link; salida de `medir_latencia_red.py` con el `CUMPLE`; `iw dev mlan0 link` en cada vehículo | `S26_red_<que>.jpg` / `.png` |
| **Radio de giro** (§3.1) | El círculo marcado en el piso, con la cinta sobre el diámetro; una por vehículo y por lado | La maniobra completa | — | `S26_radio_<vehiculo>_<izq\|der>.jpg` |
| **Misiones encadenadas, G-3** (§3.2) | La marca de cada llegada, con la cinta y la cifra legible | Cada tramo, en plano fijo, del arranque a la parada | RViz con la pose de AMCL en la llegada; la fila del CSV | `S26_G3_<id>_llegada.jpg` |
| **Media vuelta** (§3.3) | — | **Completa, salga o no.** Si falla, el video es la evidencia de la limitación del Ackermann en un pasillo de 2,3 m | El plan de Nav2 en RViz | `S26_mediavuelta_<id>.jpg` (fotograma) |
| **Piso 3 con deepy** (§3.4) | La llegada con la cinta | El recorrido | RViz con el mapa del piso 3 y la pose | `S26_piso3_<id>_llegada.jpg` |
| **Misión desde el teléfono** (§4.3) | — | El vehículo y el teléfono **en el mismo cuadro** | **Grabación de pantalla del teléfono**: lista de destinos, etapas y mensaje final | `S26_P4_01_<que>.jpg` |
| **G-5, relevo entre pisos** (§5.1) | La llegada en cada piso, con la cinta | **Un teléfono por piso, grabando a la vez**: es la única forma de mostrar el relevo completo | Pantalla del teléfono del usuario (la petición de subir y la confirmación); terminal del coordinador | `S26_G5_<id>_<piso>.jpg` |

## Al terminar el día

- [ ] Videos a la carpeta compartida del equipo, con el id de la corrida en el nombre.
- [ ] Fotos reducidas a unos 400 KB, renombradas y copiadas a `Documentos/Evidencia/`.
- [ ] Cada foto citada en el informe de la prueba, con una línea que diga qué sostiene.
- [ ] Una fila en el índice de [`Evidencia/README.md`](../Evidencia/README.md) por cada informe nuevo,
      en el mismo commit.
