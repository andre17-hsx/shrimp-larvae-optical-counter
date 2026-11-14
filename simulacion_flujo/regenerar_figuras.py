# -*- coding: utf-8 -*-
"""Regenera las figuras a partir de resultados/ (sin volver a simular)."""
import json
import os
from types import SimpleNamespace

import numpy as np

from geometria_canal import cargar_canal
import analisis_larvas
import graficos_final as gf

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')


def _cargar(nombre, c):
    d = np.load(os.path.join(RES, nombre))
    r = SimpleNamespace(c=c, h_m=d['h'], u_m=d['u'], v_m=d['v'], s=d['s'], y=d['y'], sol=d['sol'])
    r.dx = r.s[1] - r.s[0]
    r.dy = r.y[1] - r.y[0]
    r.nx, r.ny = r.h_m.shape
    r.h_rms = np.zeros_like(r.h_m)
    return r


if __name__ == '__main__':
    c, m, g = cargar_canal()
    A, B = _cargar('final_A.npz', c), _cargar('final_B.npz', c)
    log = json.load(open(os.path.join(RES, 'resultados_finales.json')))
    gf.figura_planta(c, A, B, None, None, os.path.join(RES, 'fig1_planta_A_vs_B.png'))
    gf.figura_barrido(log['barrido'], os.path.join(RES, 'fig2_barrido_caudal.png'))
    ruta_p = os.path.join(RES, 'pulsaciones_canal.json')
    canal = json.load(open(ruta_p)) if os.path.exists(ruta_p) else None
    gf.figura_pulsaciones(log['pulsaciones'], os.path.join(RES, 'fig3_pulsaciones.png'), canal)
    log['larvas'], trs = analisis_larvas.correr(A, B)
    tasas = np.array(log['larvas']['tasas'])
    gf.figura_larvas(c, A, B, trs, tasas, log['larvas'], os.path.join(RES, 'fig4_larvas.png'))
    json.dump(log, open(os.path.join(RES, 'resultados_finales.json'), 'w'), indent=1, default=float)
    print('figuras regeneradas')
