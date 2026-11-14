# -*- coding: utf-8 -*-
"""Sensibilidad a la malla de drenaje (0, 15, 30 %) y a la rugosidad (n de Manning) para A y B a 10 L/s."""
import json
import os
import numpy as np

from geometria_canal import cargar_canal
from flujo_1d import calibrar_kd, perfil_estacionario, resumen
from contracciones import metricas, caudal_en, ancho_fijo
from ejecutar_todo import caso_A, caso_B, RES

if __name__ == '__main__':
    c, m, g = cargar_canal()
    out = {'drenaje': [], 'manning_1d': []}
    print('== perfil 1D sin drenaje, Q = 10 L/s')
    P0 = perfil_estacionario(c)
    resumen(c, P0)
    print('== sensibilidad a la malla de drenaje (2D, dx 4 mm)')
    for fr in (0.0, 0.15, 0.30):
        kd = calibrar_kd(c, fr) if fr else 0.0
        fila = {'fr_1d_A': fr, 'kd': kd}
        for nom, fn in (('A', caso_A), ('B', caso_B)):
            r = fn(c, kd)
            r = r[0] if isinstance(r, tuple) else r
            q = metricas(c, r)
            i = np.searchsorted(r.s, c.s_conteo)
            q['drena'] = 1 - caudal_en(r, i) / 10.0
            fila[nom] = q
        out['drenaje'].append(fila)
        print('drena %2d%% (kd %.4f): A h=%.2f mm (%.1f-%.1f) CV %.1f %%, sale %.1f %% | B h=%.2f mm (%.1f-%.1f) CV %.1f %%, sale %.1f %%' % (
            fr * 100, kd, fila['A']['h_media'], fila['A']['h_min'], fila['A']['h_max'], fila['A']['cv_h'], 100 * fila['A']['drena'],
            fila['B']['h_media'], fila['B']['h_min'], fila['B']['h_max'], fila['B']['cv_h'], 100 * fila['B']['drena']), flush=True)
    print('== rugosidad (1D, sin drenaje, canal angosto)')
    for n in (0.008, 0.010, 0.012, 0.014, 0.016):
        P = perfil_estacionario(c, forma_ancho=ancho_fijo(c), n=n)
        i = np.searchsorted(P['s'], c.s_conteo)
        out['manning_1d'].append({'n': n, 'h_mm': float(P['h'][i] * 1e3), 'V': float(P['V'][i]), 'Fr': float(P['Fr'][i])})
        print('n = %.3f: h = %.2f mm, V = %.2f m/s, Fr = %.1f' % (n, P['h'][i] * 1e3, P['V'][i], P['Fr'][i]))
    json.dump(out, open(os.path.join(RES, 'sensibilidad.json'), 'w'), indent=1, default=float)
