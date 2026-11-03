# La red en campo, con la topología definitiva (9 de octubre)

Comprobación de la red en los pisos 3 y 4 con los dos agentes ya repartidos, **uno en cada punto de
acceso**, que es el montaje que el sistema usa de verdad. Las medidas se tomaron por SSH desde el
portátil durante la sesión de campo.

> **Procedencia, dicha entera.** Estas cifras se midieron el 9 de octubre y quedaron en la
> transcripción de la sesión de trabajo, **no en un fichero**; este informe se escribe el 3 de
> noviembre a partir de esa transcripción. No hay registro JSON como el de RF-15, y por eso se
> reportan por lo que son: tiempos de ida y vuelta de ICMP, no la medida del instrumento del
> proyecto. El §4 dice cómo repetirlas si hace falta.

## Resultado

Con cada agente en el punto de acceso de su piso, **el enlace dejó de ser un factor limitante**:
ida y vuelta por debajo de 2,2 ms, sin pérdidas y sin paquetes duplicados.

| | deepy (`amss-ez9n`) | racey (`amss-jgm9`) |
|---|---|---|
| Punto de acceso | `DEEPRACER_P3-5G` · piso 3 | `DEEPRACER_P4-5G` · piso 4 |
| Banda y canal | 5220 MHz · **canal 44** | 5180 MHz · **canal 36** |
| Señal | −51 dBm | −59 dBm |
| Velocidad de recepción | 300 Mbit/s | 360 Mbit/s |
| Dirección | `192.168.0.102` | `192.168.0.104` |
| **Ida y vuelta al enrutador** | **2,13 ms** (mín 1,49 · máx 4,08 · desv. 0,56) | **1,99 ms** (mín 1,44 · máx 3,40 · desv. 0,49) |
| Pérdida | 0 % | 0 % |

Veinte paquetes por vehículo, desde el propio vehículo hacia `192.168.0.1`. Se mide desde el
vehículo y no desde el portátil a propósito: el portátil estaba en la banda de 2,4 GHz y medir desde
él mide su propio enlace, que es el peor de la cadena (§3).

## 1. Sin bucle de capa 2

Cuarenta paquetes a cada destino, contando duplicados, que es la firma del bucle del 7 de octubre
([`S26_bucle_capa2_y_red_dos_AP.md`](S26_bucle_capa2_y_red_dos_AP.md)):

| Destino | Recibidos | Duplicados |
|---|---|---|
| Enrutador | 40 | **0** |
| deepy | 40 | **0** |
| racey | 40 | **0** |

El bucle no reapareció pese a que el punto de acceso del piso 3 seguía anunciando su SSID de malla
(`fhmesh_8C5FAD37AA40`, canal 44, señal 29). **Anunciar no es emparejarse:** el bucle necesita que el
enlace de malla se establezca, y con el enlace de subida por cable no se estableció. Aun así queda
anotado como riesgo latente: si esos dos equipos llegaran a enlazarse por aire estando los dos
cableados, el bucle vuelve.

## 2. Una sola subred y un solo servidor de direcciones

| Dirección | Equipo |
|---|---|
| `192.168.0.1` | enrutador, servidor de direcciones |
| `192.168.0.102` | deepy |
| `192.168.0.104` | racey |

Las dos direcciones de los vehículos son las reservadas por dirección física, así que no cambian
entre sesiones. Es lo que corrigió el problema del 8 de octubre, cuando un punto de acceso quedó
repartiendo direcciones de una subred propia y los dos vehículos no podían verse.

## 3. Por qué no se mide desde el portátil

Durante la sesión, los barridos desde el portátil daban promedios de 20 a 24 ms con picos de 140 ms,
mientras los vehículos medían por debajo de 2,2 ms contra el mismo enrutador. **La diferencia es el
portátil**, que seguía asociado al enlace de respaldo de 2,4 GHz, en la banda donde se contaron 33
redes ajenas en el sitio.

Conviene dejarlo escrito porque es un error fácil de cometer y conduce a conclusiones falsas sobre la
red: medir desde el portátil mide el peor enlace de la cadena, no el de los vehículos. Es la misma
razón por la que RF-15 está definido entre los dos vehículos y no contra un tercero.

## 4. Lo que no se midió, y cómo se obtendría

**Decisión de los autores, 3 de noviembre: esta medida no se repite.** RF-15 queda verificado con los dos registros en la
misma sala, y con un vehículo en cada piso quedan las medidas de este informe. Las órdenes de abajo se dejan por si hicieran
falta.

**RF-15 nunca se repitió en esta topología.** Los dos registros que existen
—[`S23_RF15_carroA_carroB.json`](registros/S23_RF15_carroA_carroB.json) en 2,4 GHz y
[`S26_RF15_5GHz_carroA_carroB.json`](registros/S26_RF15_5GHz_carroA_carroB.json) en 5 GHz— se tomaron
con **los dos vehículos en la misma sala y el mismo punto de acceso**. Con uno en cada piso y el
cable entre plantas de por medio no se ha medido.

Las cifras de este informe **no la sustituyen**: son ICMP contra el enrutador, no mensajes de ROS 2
entre los dos agentes con las cotas inscritas del requisito.

Para cerrarlo hacen falta dos órdenes, con un agente en cada piso. En el que responde:

```
source /opt/ros/jazzy/setup.bash && python3 ~/medir_latencia_red.py --rol eco
```

Y en el otro:

```
source /opt/ros/jazzy/setup.bash && python3 ~/medir_latencia_red.py --rol emisor \
    --n 600 --hz 10 --etiqueta pisos34_topologia_final --salida /tmp/rf15_pisos34.json
```

El medidor trae las cotas escritas —mediana ≤ 100 ms, p95 ≤ 250 ms, pérdida 0 %— y emite su propio
veredicto, así que no hay que interpretarlo a mano.
