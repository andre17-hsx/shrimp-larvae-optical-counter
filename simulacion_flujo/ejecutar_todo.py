# -*- coding: utf-8 -*-
"""Corre los casos finales (diseno anterior A y diseno nuevo B), el barrido de caudal, las pulsaciones y las larvas,
y guarda resultados/ (json, npz y figuras). Tarda unos 10 minutos.

A = diseno anterior: paredes de contraccion de 47 grados sobre la malla (994 -> 504 mm en 0,23 m). Ya no esta en el modelo.
B = diseno actual del modelo: el estrechamiento esta AGUAS ARRIBA de la cresta, en el cajon (flujo lento): L_ESTRECH de
    largo con forma de coseno y L_ESTRECH_RECTO de tramo recto de 504 mm justo antes de la cresta (constantes del script).
La malla drena FR_DREN del caudal en A (calibrado); B usa la misma malla (kd) y drena algo menos porque es mas angosta.
"""
import json
import os
import time

import numpy as np

from geometria_canal import cargar_canal
from flujo_1d import calibrar_kd, perfil_estacionario
from swe2d import Caso
from contracciones import forma, metricas, caudal_en, ancho_fijo
from aproximacion import correr_completo
import analisis_larvas
import graficos_final as gf

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados')
FR_DREN = 0.15
B_TIPO = 'coseno'


def caso_A(c, kd, Q=None, dx=4e-3, **kw):
    f = forma(c, c.s_cont0, c.s_cont1, 'lineal')
    P = perfil_estacionario(c, Q=Q, forma_ancho=f, kd=kd)
    return Caso(c, P, dx=dx, forma_ancho=f, kd=kd).ejecutar(3.5, 2.5, **kw), P


def caso_B(c, kd, Q=None, dx=4e-3, **kw):
    return correr_completo(c, Q=Q, x_contra=c.l_estrech, x_recto=c.l_recto, tipo=B_TIPO, kd=kd, dx=dx,
                           x_ini=c.l_estrech + c.l_recto + 0.15, **kw)


def main():
    os.makedirs(RES, exist_ok=True)
    c, m, g = cargar_canal()
    kd = calibrar_kd(c, FR_DREN)
    log = {'kd': kd, 'fr_dren_A': FR_DREN}
    t0 = time.time()

    # ---- 1) casos base a 10 L/s, malla fina
    dx = 3e-3
    A, PA = caso_A(c, kd, dx=dx)
    B = caso_B(c, kd, dx=dx)
    for nom, r in (('A', A), ('B', B)):
        q = metricas(c, r)
        i = np.searchsorted(r.s, c.s_conteo)
        q['Q_conteo'] = caudal_en(r, i)
        log['base_' + nom] = q
        print(nom, {k: round(float(v), 3) for k, v in q.items()}, '[%.0f s]' % (time.time() - t0), flush=True)
    np.savez_compressed(os.path.join(RES, 'final_A.npz'), h=A.h_m, u=A.u_m, v=A.v_m, s=A.s, y=A.y, sol=A.sol)
    np.savez_compressed(os.path.join(RES, 'final_B.npz'), h=B.h_m, u=B.u_m, v=B.v_m, s=B.s, y=B.y, sol=B.sol)
    PB = perfil_estacionario(c, forma_ancho=ancho_fijo(c), kd=kd)
    gf.figura_planta(c, A, B, PA, PB, os.path.join(RES, 'fig1_planta_A_vs_B.png'))

    # ---- 2) barrido de caudal
    barrido = {'A': [], 'B': []}
    for Q in (4, 6, 8, 10, 12, 15):
        for nom, fn in (('A', caso_A), ('B', caso_B)):
            r = fn(c, kd, Q=Q * 1e-3)
            r = r[0] if isinstance(r, tuple) else r
            q = metricas(c, r)
            i = np.searchsorted(r.s, c.s_conteo)
            q['Q'] = Q
            q['drena'] = 1 - caudal_en(r, i) / Q
            barrido[nom].append(q)
        print('Q = %g L/s hecho [%.0f s]' % (Q, time.time() - t0), flush=True)
    log['barrido'] = barrido
    gf.figura_barrido(barrido, os.path.join(RES, 'fig2_barrido_caudal.png'))

    # ---- 3) pulsaciones del caudal (diseno B)
    puls = []
    est = [0.1, 0.4, 0.7, c.s_conteo]
    for frec in (0.5, 1, 2, 5, 10, 20):
        r = caso_B(c, kd, dx=4e-3, t_fin=8.0, t_prom=1e9, pert_a=0.05, pert_f=frec, sondas=[(s, 0.0) for s in est])
        t = r.serie[:, 0]
        msk = t >= 4.0
        fila = []
        for k, s in enumerate(est):
            h = r.serie[msk, k + 1]
            A_ = np.vstack([np.sin(2 * np.pi * frec * t[msk]), np.cos(2 * np.pi * frec * t[msk]), np.ones(msk.sum())]).T
            co = np.linalg.lstsq(A_, h, rcond=None)[0]
            fila.append(float(np.hypot(co[0], co[1]) / co[2]))
        puls.append({'f': frec, 's': est, 'amp_rel': fila})
        print('pulsacion %g Hz: ' % frec, ['%.1f %%' % (100 * x) for x in fila], flush=True)
    log['pulsaciones'] = puls
    gf.figura_pulsaciones(puls, os.path.join(RES, 'fig3_pulsaciones.png'))   # (pulsaciones.py agrega la curva del canal solo)

    # ---- 4) larvas
    log['larvas'], trs = analisis_larvas.correr(A, B)
    tasas = np.array(log['larvas']['tasas'])
    gf.figura_larvas(c, A, B, trs, tasas, log['larvas'], os.path.join(RES, 'fig4_larvas.png'))
    json.dump(log, open(os.path.join(RES, 'resultados_finales.json'), 'w'), indent=1, default=float)
    print('listo [%.0f s]' % (time.time() - t0))


if __name__ == '__main__':
    main()
