#!/usr/bin/env python3
"""La herramienta de escala de traccion no devuelve cifras que no midio.

QUE SE COMPRUEBA Y POR QUE ASI
------------------------------
'medir_escala_traccion.py' contesta la pregunta de RF-14: cuanta velocidad real
da un throttle dado. De ahi sale si 'MAX_SPEED = 4,0 m/s' -la suposicion de la
que cuelgan los tres umbrales de traccion- se parece a la realidad.

Una herramienta que conteste eso mal es peor que no tenerla, porque el numero
va a un requisito. Asi que la prueba no se limita a que con datos buenos salga
algo: se le dan los tres casos que en el pasillo saldrian mal, y tiene que
negarse a dar cifra en los tres.

  1. El CDR se desempaqueta bien, incluido big-endian, y un mensaje de tamaño
     raro REVIENTA en vez de devolver dos numeros creibles y falsos.
  2. La velocidad se mide sobre ventana centrada, y fuera de la trayectoria
     devuelve None y no cero. Un cero ahi es una parada inventada, y las
     paradas son justo lo que se esta midiendo.
  3. Un bag de servo vacio -la trampa de dueños del §10.2 de la hoja de campo-
     falla nombrandola, porque es la causa probable y el sintoma es silencio.
  4. Dos bags que no se solapan en el tiempo fallan, en vez de emparejar cero
     muestras y sacar una tabla vacia con pinta de resultado.
  5. El veredicto se ramifica donde tiene que ramificarse: si el arranque queda
     por encima de los 0,25 m/s de Nav2, el informe dice que RF-14 NO se cierra
     calibrando. Es el resultado incomodo, y es el que mas facil se pierde.
  6. Las cajas con pocas muestras se marcan y no cuentan para el arranque.

    python3 herramientas/prueba_medir_escala_traccion.py
"""
import importlib.util
import pathlib
import struct

RUTA = pathlib.Path(__file__).resolve().parent / 'medir_escala_traccion.py'


def cargar():
    spec = importlib.util.spec_from_file_location('medir_escala_traccion', RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def csv_trayectoria(poses):
    filas = ['t,fuente,x,y,yaw']
    for t, x, y in poses:
        filas.append(f'{t},odom,{x},{y},0.0')
    return '\n'.join(filas) + '\n'


def recta(t0, t1, v, paso=0.1):
    """Poses de un carro que va recto a 'v' m/s entre t0 y t1."""
    poses = []
    t = t0
    while t <= t1 + 1e-9:
        poses.append((round(t, 6), round((t - t0) * v, 6), 0.0))
        t += paso
    return poses


def cdr(angle, throttle, endian='<'):
    cabecera = b'\x00\x01\x00\x00' if endian == '<' else b'\x00\x00\x00\x00'
    return cabecera + struct.pack(endian + 'ff', angle, throttle)


def main():
    m = cargar()
    fallos = []

    def exigir(condicion, mensaje):
        if not condicion:
            fallos.append(mensaje)

    def exige_fallo(fn, fragmento, mensaje):
        try:
            fn()
        except m.Fallo as e:
            if fragmento.lower() not in str(e).lower():
                fallos.append(f'{mensaje}: fallo, pero sin mencionar '
                              f'{fragmento!r}. Dijo: {e}')
        except Exception as e:  # noqa: BLE001 - cualquier otra cosa es un fallo
            fallos.append(f'{mensaje}: reviento con {type(e).__name__}, '
                          f'que no es Fallo: {e}')
        else:
            fallos.append(f'{mensaje}: NO fallo, y tenia que fallar')

    # 1. El CDR.
    a, t = m.desempaquetar_servo(cdr(-0.25, 0.35))
    exigir(abs(a + 0.25) < 1e-6 and abs(t - 0.35) < 1e-6,
           f'little-endian dio angle={a}, throttle={t}')
    a, t = m.desempaquetar_servo(cdr(-0.25, 0.35, '>'))
    exigir(abs(a + 0.25) < 1e-6 and abs(t - 0.35) < 1e-6,
           f'big-endian dio angle={a}, throttle={t}')
    exige_fallo(lambda: m.desempaquetar_servo(b'\x00\x01\x00\x00' + b'\x00' * 16),
                '12 bytes', 'un mensaje de 20 bytes')

    # 2. La velocidad, y el None fuera de la trayectoria.
    pista = [(p[0], p[1], p[2]) for p in recta(100.0, 110.0, 0.5)]
    v = m.velocidad_en(pista, 105.0)
    exigir(v is not None and abs(v - 0.5) < 0.01, f'a 0,5 m/s midio {v}')
    exigir(m.velocidad_en(pista, 50.0) is None,
           'antes de la trayectoria deberia devolver None, no una velocidad')
    exigir(m.velocidad_en(pista, 200.0) is None,
           'despues de la trayectoria deberia devolver None')
    exigir(m.velocidad_en([(1.0, 0.0, 0.0)], 1.0) is None,
           'con una sola pose no hay velocidad que medir')

    #    Y el caso que solo aparece con rf2o cayendose a ratos: un mensaje de
    #    servo que cae en un HUECO de la odometria. Ahi la ventana existe pero
    #    queda entera a un lado de 't', asi que la velocidad que daria es la de
    #    otro instante. Tiene que ser None. Sin esta comprobacion, poner un 0,0
    #    en su lugar pasa desapercibido, y un cero se lee como parada.
    con_hueco = [(100.0, 0.0, 0.0), (105.2, 2.6, 0.0), (105.4, 2.7, 0.0)]
    exigir(m.velocidad_en(con_hueco, 105.0) is None,
           'una muestra en un hueco de la odometria deberia dar None: la '
           'ventana que le queda esta entera despues del instante que mide')
    con_hueco_antes = [(104.6, 0.0, 0.0), (104.8, 0.1, 0.0), (110.0, 3.0, 0.0)]
    exigir(m.velocidad_en(con_hueco_antes, 105.0) is None,
           'lo mismo con la ventana entera antes del instante')

    # 3. Bag de servo vacio: tiene que nombrar la trampa de dueños.
    exige_fallo(lambda: m.emparejar(pista, []), 'ninguna muestra',
                'una lista de servo vacia')

    # 4. Dos bags que no se solapan.
    lejos = [(500.0 + i * 0.05, 0.0, 0.30) for i in range(40)]
    exige_fallo(lambda: m.emparejar(pista, lejos), 'solapan',
                'un servo que cae fuera de la trayectoria')

    # 5. El veredicto incomodo: arranque por encima de lo que pide Nav2.
    #    Carro a 0,60 m/s con throttle 0,30 -o sea que su minimo util ya supera
    #    los 0,25 m/s de Nav2-.
    pista_rapida = [(p[0], p[1], p[2]) for p in recta(0.0, 20.0, 0.60)]
    servo_rapido = [(1.0 + i * 0.05, 0.0, 0.30) for i in range(360)]
    filas = m.agrupar(m.emparejar(pista_rapida, servo_rapido))
    arranque = m.umbral_arranque(filas)
    exigir(arranque is not None, 'no encontro arranque con el carro moviendose')
    texto = m.informe(filas, arranque, m.max_speed_implicito(filas))
    exigir('NO se cierra calibrando' in texto,
           'con un arranque de 0,60 m/s el informe deberia decir que RF-14 no '
           f'se cierra calibrando, y dice:\n{texto}')

    #    Y el caso contrario: 0,10 m/s cabe por debajo de 0,25.
    pista_lenta = [(p[0], p[1], p[2]) for p in recta(0.0, 60.0, 0.10)]
    servo_lento = [(1.0 + i * 0.05, 0.0, 0.30) for i in range(1000)]
    filas_l = m.agrupar(m.emparejar(pista_lenta, servo_lento))
    texto_l = m.informe(filas_l, m.umbral_arranque(filas_l),
                        m.max_speed_implicito(filas_l))
    exigir('se cierra recalculando' in texto_l,
           f'con 0,10 m/s deberia decir que se cierra recalculando:\n{texto_l}')
    exigir('NO se cierra calibrando' not in texto_l,
           'el caso bueno no puede dar el veredicto del caso malo')

    # 6. Las cajas flacas se marcan y no arrastran el arranque.
    #    Tres muestras a throttle 0,05 -por debajo del minimo de 5- y muchas a
    #    0,30. El arranque no puede salir de la caja flaca.
    servo_mixto = ([(1.0 + i * 0.05, 0.0, 0.05) for i in range(3)]
                   + [(3.0 + i * 0.05, 0.0, 0.30) for i in range(300)])
    filas_m = m.agrupar(m.emparejar(pista_rapida, servo_mixto))
    flacas = [f for f in filas_m if not f['suficiente']]
    exigir(flacas, 'una caja de 3 muestras deberia quedar marcada como flaca')
    arranque_m = m.umbral_arranque(filas_m)
    exigir(arranque_m is not None and arranque_m['suficiente'],
           'el arranque salio de una caja sin muestras suficientes')

    # 7. El MAX_SPEED implicito, que es la cifra que decide si hay factor.
    #    0,60 m/s con throttle 0,30 implica 2,0 m/s, la mitad de los 4,0.
    implicito = m.max_speed_implicito(filas)
    exigir(implicito is not None and abs(implicito - 2.0) < 0.15,
           f'con 0,60 m/s a throttle 0,30 el MAX_SPEED implicito deberia ser '
           f'~2,0 y salio {implicito}')

    # 8. Un CSV sin las columnas que toca no se lee a medias.
    exige_fallo(lambda: m.leer_trayectoria('a,b\n1,2\n'), 'columnas',
                'un CSV con otras columnas')
    exige_fallo(lambda: m.leer_trayectoria(csv_trayectoria([(1.0, 0.0, 0.0)])),
                'poses', 'una trayectoria con una sola pose')

    print()
    if fallos:
        print(f'FALLA — {len(fallos)} comprobacion(es):')
        for mensaje in fallos:
            print(f'  {mensaje}')
        return 1
    print('PASA: la herramienta desempaqueta el CDR sin el tipo de AWS, mide')
    print('      velocidad sobre ventana centrada, se niega a dar cifra cuando')
    print('      los bags no se solapan o el de servo esta vacio, y da el')
    print('      veredicto incomodo cuando el arranque supera lo que pide Nav2.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
