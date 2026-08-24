# Un destino del edificio. Es la forma en mensaje de una entrada de
# deepracer_bringup/config/puntos_interes.yaml, que es la fuente de verdad:
# el coordinador carga el YAML y republica la lista latched, y la HRI arma sus
# desplegables de origen y destino desde ahi.
#
# Definido en Documentos/CONTRATO_INTERFACES.md seccion 5.
#
# El YAML tiene dos campos que este mensaje NO lleva, a proposito:
#   'holgura_m'  - distancia libre alrededor de la pose. Es un dato de
#                  verificacion del mapa, no algo que la HRI deba mostrar.
#   'provisional'- marca de que la pose aun no se confirmo contra el edificio.
#                  Sirve para no medir la campana de S24 sobre poses inventadas.
# Si en algun momento la HRI necesita avisar "este destino es provisional",
# habra que anadir el campo aqui y en el contrato, no improvisarlo en el nodo.

string id                       # "piso1_escalera"
string nombre                   # "Escalera del primer piso"  <- lo que ve el usuario
uint8 nivel                     # 1 | 2
bool es_transferencia           # true en un punto de relevo; false en un destino corriente
geometry_msgs/Pose pose         # en el marco robotN/map del nivel correspondiente
