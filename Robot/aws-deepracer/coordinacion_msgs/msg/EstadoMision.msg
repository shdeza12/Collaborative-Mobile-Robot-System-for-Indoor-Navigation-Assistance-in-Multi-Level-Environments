# El progreso de una mision de guiado, tal como lo ve el usuario.
# Lo publica el coordinador y viaja tambien como feedback de GuiarUsuario.action.
#
# Definido en Documentos/CONTRATO_INTERFACES.md seccion 5.

# Constantes de 'etapa'.
# Cuando origen y destino estan en el mismo nivel no hay relevo: la mision pasa
# de TRAMO_1 directo a COMPLETADA, sin TRANSFERENCIA ni TRAMO_2. La HRI no debe
# tener una rama especial para ese caso.
uint8 INACTIVA=0
uint8 TRAMO_1=1
uint8 TRANSFERENCIA=2
uint8 TRAMO_2=3
uint8 COMPLETADA=4
uint8 FALLIDA=5

string mision_id
uint8 etapa
string robot_activo
PuntoInteres destino_actual
float32 distancia_restante
string mensaje_usuario          # texto ya redactado en espanol para mostrar tal cual

# 'mensaje_usuario' se redacta EN EL COORDINADOR, no en el navegador ni en la
# HRI. El frontend lo muestra literal. Asi no se duplica logica de presentacion
# en JavaScript.
