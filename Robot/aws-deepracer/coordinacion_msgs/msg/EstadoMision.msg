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
# RECIBIDA es el estado que existe entre 'llego la solicitud' y 'ya hay agente
# elegido'. Se anade el 2026-08-29, despues del primer piloto de RF-25, porque
# ese hueco NO EXISTIA: el coordinador fijaba etapa y robot_activo en la misma
# llamada y publicaba una vez, asi que t_solicitud y t_robot_activo caian en el
# mismo mensaje y el TIEMPO DE ASIGNACION -una de las cuatro metricas de OE4-
# valia exactamente cero, se ejecutara lo que se ejecutara. Un cero no es una
# medida. La §3.5 del esquema ya definia t_solicitud como el instante en que el
# servidor ACEPTA el goal; lo que faltaba era publicarlo.
#
# Va al final y con numero nuevo a proposito: las constantes no viajan por el
# cable -no son campos-, asi que el formato de serializacion no cambia y un
# suscriptor ya compilado sigue deserializando. Solo vera un valor de etapa que
# no conoce, y por eso la HRI de S22 debe tratar RECIBIDA como 'preparando'.
uint8 RECIBIDA=6

string mision_id
string origen_id                # el punto de partida que pidio el usuario
string destino_id               # el destino FINAL, no el del tramo en curso
uint8 etapa
string robot_activo
PuntoInteres destino_actual
float32 distancia_restante
string mensaje_usuario          # texto ya redactado en espanol para mostrar tal cual

# 'mensaje_usuario' se redacta EN EL COORDINADOR, no en el navegador ni en la
# HRI. El frontend lo muestra literal. Asi no se duplica logica de presentacion
# en JavaScript.

# 'destino_id' NO es lo mismo que 'destino_actual.id': en una mision entre
# niveles, durante el tramo 1 el destino ACTUAL es el punto de transferencia y
# el destino de la MISION sigue siendo el del otro piso. Los dos hacen falta:
# uno para lo que la HRI muestra ahora, otro para saber que se pidio.
#
# Estan aqui, y no solo en el goal de GuiarUsuario.action, porque un goal de
# accion viaja por un SERVICIO y 'ros2 bag' no graba servicios. Sin estos dos
# campos el bloque 'solicitud' del registro de mision (RF-25) no se puede
# componer desde el bag. Se descubrio el 2026-08-26 escribiendo PLAN_RF25.md,
# antes de grabar la primera corrida. Ver §3.4 de ESQUEMA_REGISTRO_MISION.md.
