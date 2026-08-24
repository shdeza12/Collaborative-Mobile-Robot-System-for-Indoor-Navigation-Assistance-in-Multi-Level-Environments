# El catalogo de destinos del edificio, entero, en un solo mensaje.
#
# POR QUE EXISTE ESTE MENSAJE (2026-08-24). El §4 de CONTRATO_INTERFACES.md
# declaraba /coordinacion/puntos_interes de tipo 'PuntoInteres[] (latched)', y
# ese tipo no se puede publicar: un topico de ROS 2 transporta UN mensaje, no un
# arreglo. 'PuntoInteres[]' es sintaxis valida para un CAMPO, no para un tipo.
# El §5 cerraba con "cuatro definiciones, nada mas", asi que el hueco estaba en
# los dos sitios. Este es el quinto, y el contrato ya quedo corregido.
#
# Se publica LATCHED (QoS TRANSIENT_LOCAL, depth 1) desde el coordinador. Es el
# caso en que 'latched' es correcto: el catalogo cambia solo cuando alguien edita
# puntos_interes.yaml, y la HRI se conecta cuando el usuario abre el navegador,
# mucho despues de que el coordinador arrancara. Sin retencion, la HRI se queda
# con los desplegables vacios hasta que el catalogo cambie, que puede ser nunca.
#
# OJO, y no es el mismo caso que amcl_pose. Alli 'latched' engano dos veces el
# 2026-08-24 porque el dato ES perecedero: una pose vieja parece actual. Aqui el
# dato no caduca, y por eso retenerlo es lo correcto. La regla que separa los dos
# casos: retener catalogos, nunca retener medidas.

# Fuente de verdad: deepracer_bringup/config/puntos_interes.yaml. El coordinador
# lo carga y lo republica; nadie mas lee ese archivo.
string origen                   # ruta del YAML del que salio, para diagnostico
builtin_interfaces/Time stamp   # cuando se cargo

PuntoInteres[] puntos
