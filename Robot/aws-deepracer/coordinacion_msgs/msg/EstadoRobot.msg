# Lo que un robot dice de si mismo. Lo publica cada agente en su propio
# namespace, /robotN/estado_robot, y lo consume el coordinador.
#
# Definido en Documentos/CONTRATO_INTERFACES.md seccion 5. Si cambia aqui,
# cambia alli: son el mismo contrato escrito dos veces.

# Constantes de 'estado'. Se declaran para que nadie escriba el numero suelto.
uint8 LIBRE=0
uint8 NAVEGANDO=1
uint8 EN_TRANSFERENCIA=2
uint8 ERROR=3

# OJO CON 'pose'. No rellenarlo suscribiendose a /robotN/amcl_pose: ese topico
# es TRANSIENT_LOCAL y nav2_amcl solo publica cuando el robot se mueve, asi que
# un robot quieto entrega la ultima muestra caducada sin dar ningun error. Medido
# el 2026-08-24: 0 mensajes en 10 s parado, 12 en movimiento. Leer en su lugar la
# TF map -> <ns>/odom, que si se republica a ~9,5 Hz aunque el robot este quieto.

string robot_id                 # "robot1" | "robot2"
uint8 nivel                     # 1 | 2
geometry_msgs/PoseStamped pose  # en el marco <ns>/map
uint8 estado                    # LIBRE | NAVEGANDO | EN_TRANSFERENCIA | ERROR
string detalle                  # texto libre para diagnostico
builtin_interfaces/Time stamp
