# -*- coding: utf-8 -*-
"""Estadistica de larvas para los casos A y B: transito, reparto a lo ancho y solapamiento segun la tasa."""
import numpy as np

from larvas import seguir, solapamiento

TASAS = np.array([30, 60, 100, 200, 300, 500, 1000, 2000])


def correr(A, B, n=10000):
    larv, trs = {}, {}
    for nom, r in (('A', A), ('B', B)):
        tr = seguir(r, n=n, dt=1e-3, s_ini=0.0)          # desde la cresta hasta la linea de conteo
        trs[nom] = tr
        ok = np.isfinite(tr['y'])
        larv[nom] = {'transito_s': float(tr['t'][ok].mean()), 'sd_transito_s': float(tr['t'][ok].std()),
                     'u': float(tr['u'][ok].mean()), 'sd_u': float(tr['u'][ok].std()), 'llegan': float(ok.mean()),
                     'sd_y_mm': float(tr['y'][ok].std() * 1e3)}
        for orient in ('alineada', 'aleatoria'):
            larv[nom][orient] = [solapamiento(tr, float(t), orient=orient, T=(60 if t < 1000 else 20))[:2] for t in TASAS]
    return {'tasas': TASAS.tolist(), **larv}, trs
