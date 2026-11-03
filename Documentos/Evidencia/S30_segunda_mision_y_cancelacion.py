#!/usr/bin/env python3
"""Segunda mision con otra en curso, y cancelacion sin el telefono que la lanzo. Con robots falsos."""
import importlib.util
import tempfile
import time
from pathlib import Path

RUTA = Path(__file__).resolve().parents[2] / 'Robot/aws-deepracer/coordinacion/test/prueba_coordinador_vehiculo.py'
spec = importlib.util.spec_from_file_location('pcv', RUTA)
pcv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcv)

from action_msgs.msg import GoalStatus
from action_msgs.srv import CancelGoal
from coordinacion_msgs.action import GuiarUsuario
from std_msgs.msg import String

ESTADOS = {4: 'SUCCEEDED', 5: 'CANCELED', 6: 'ABORTED'}
trazas = []


def _estado(self, m):
    if not trazas or (trazas[-1][1], trazas[-1][2]) != (m.mision_id, m.etapa):
        trazas.append((time.time(), m.mision_id, m.etapa))


pcv.Usuario._estado = _estado   # sin confirmar sola: cada telefono confirma cuando se le dice


def esperar_etapa(etapa, plazo=30, mision=None):
    t0 = time.time()
    while time.time() - t0 < plazo:
        for _t, m, e in trazas:
            if e == etapa and (mision is None or m == mision):
                return m
        time.sleep(0.05)
    return None


def pedir(u, o, d):
    f = u.cliente.send_goal_async(GuiarUsuario.Goal(origen_id=o, destino_id=d))
    pcv.esperar(f, 10)
    return f.result()


def resultado(g, plazo):
    f = g.get_result_async()
    pcv.esperar(f, plazo)
    r = f.result()
    if r is None:
        return 'sin resultado en el plazo'
    return f"{ESTADOS.get(r.status, r.status)}, exito={r.result.exito}, relevos={r.result.num_relevos}, motivo={r.result.motivo_fallo!r}"


clase = pcv.cargar_coordinador(None)

print('=== 1. Segundo telefono pide una mision mientras la primera espera la confirmacion')
with tempfile.TemporaryDirectory() as reg:
    robots, u, _c, ej = pcv.montar('hardware', reg, clase)
    r1, r2 = robots['robot1'], robots['robot2']
    u.cliente.wait_for_server(timeout_sec=10)
    t0 = time.time()
    ga = pedir(u, 'piso4_salon_403', 'piso3_salon_303')
    print('A (403 -> 303) aceptada:', ga.accepted)
    ma = esperar_etapa(pcv.ESPERANDO_CONFIRMACION)
    print(f'A espera confirmacion a los {time.time()-t0:.1f} s, mision {ma}; metas r1={len(r1.metas)} r2={len(r2.metas)}')
    n1, n2 = len(r1.metas), len(r2.metas)
    gb = pedir(u, 'piso3_salon_301', 'piso4_salon_401')
    print('B (301 -> 401) aceptada:', gb.accepted)
    time.sleep(3)
    print('metas nuevas tras B: r1', [tuple(round(v, 2) for v in m) for m in r1.metas[n1:]], 'r2', [tuple(round(v, 2) for v in m) for m in r2.metas[n2:]])
    print('A confirma con su mision_id (lo que haria el telefono A)')
    u.pub_conf.publish(String(data=ma))
    time.sleep(3)
    print('etapas vistas (mision, etapa):')
    for t, m, e in trazas:
        print(f'  {t-t0:6.1f} s  {m}  etapa {e}')
    mb = next((m for _t, m, _e in trazas if m and m != ma), None)
    print('mision de B:', mb)
    if mb:
        me = esperar_etapa(pcv.ESPERANDO_CONFIRMACION, 20, mb)
        print('B en confirmacion:', me)
        if me:
            u.pub_conf.publish(String(data=mb))
    print('resultado A:', resultado(ga, 140))
    print('resultado B:', resultado(gb, 60))
    print('estados finales de la traza:')
    for t, m, e in trazas[-8:]:
        print(f'  {t-t0:6.1f} s  {m}  etapa {e}')
    print('registros escritos:', len(pcv.registros_de(reg)))
    pcv.desmontar(ej)

trazas.clear()
print('=== 2. Cancelar desde fuera, sin el identificador de la meta (pagina recargada)')
with tempfile.TemporaryDirectory() as reg:
    robots, u, _c, ej = pcv.montar('hardware', reg, clase)
    u.cliente.wait_for_server(timeout_sec=10)
    ga = pedir(u, 'piso4_salon_403', 'piso3_salon_303')
    ma = esperar_etapa(pcv.ESPERANDO_CONFIRMACION)
    print('mision en espera de confirmacion:', ma)
    c = u.create_client(CancelGoal, '/coordinacion/guiar_usuario/_action/cancel_goal')
    print('servicio disponible:', c.wait_for_service(timeout_sec=5))
    f = c.call_async(CancelGoal.Request())
    pcv.esperar(f, 10)
    r = f.result()
    print('return_code', r.return_code, 'metas en cancelacion', len(r.goals_canceling))
    print('resultado:', resultado(ga, 60))
    print('etapas:', [e for _t, _m, e in trazas])
    print('registros escritos:', len(pcv.registros_de(reg)))
    pcv.desmontar(ej)
