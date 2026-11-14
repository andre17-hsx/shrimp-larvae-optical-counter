# -*- coding: utf-8 -*-
"""Evalua un caso 3D de semiancho (p2_*) frente a los criterios de aceptacion de PLAN_CFD.md.

Cada celda reparte su agua sobre su huella (s x s, s = V^(1/3); las celdas de snappy son cubicas), de modo que el
resultado no depende de como caen los bins respecto a las celdas (el reparto por centro da +-17 % de aliasing cuando la celda
mide 2 mm y el bin 12 mm).

    python analizar_criterios.py <caso> [--fig salida.png]

Usa los campos medios (alpha.waterMean, UMean; promedio de prom_desde a tfin) para lamina y velocidad, y los instantaneos
del ultimo tiempo para el aire atrapado y el contraflujo. Requiere numpy, scipy y matplotlib (entorno simenv).
"""
import argparse
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', '..', 'simulacion_flujo'))
from analizar_3d import cargar, RES  # noqa: E402
from leer_openfoam import leer_campo  # noqa: E402

TH = math.atan(0.2127659574468085)      # pendiente de la malla y del tobogan (12 grados)


def reparto(C, s, w, x0, x1, y1, dx, dy):
    """Suma w (magnitud por celda, ya multiplicada por V) repartida por la huella de cada celda en bins de dx por dy.
    Devuelve el campo por unidad de area del bin."""
    nx = int(math.ceil((x1 - x0) / dx))
    ny = int(math.ceil(y1 / dy))
    out = np.zeros((nx + 2, ny + 2))
    ax, bx = C[:, 0] - s / 2 - x0, C[:, 0] + s / 2 - x0
    ay, by = C[:, 1] - s / 2, C[:, 1] + s / 2
    ix = np.floor(ax / dx).astype(int)
    iy = np.floor(ay / dy).astype(int)
    fx = np.clip((np.minimum(bx, (ix + 1) * dx) - ax) / s, 0, 1)      # fraccion de la huella en el bin ix
    fy = np.clip((np.minimum(by, (iy + 1) * dy) - ay) / s, 0, 1)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    for ddx, wx in ((0, fx), (1, 1 - fx)):
        for ddy, wy in ((0, fy), (1, 1 - fy)):
            np.add.at(out, (ix[ok] + ddx, iy[ok] + ddy), (w * wx * wy)[ok])
    return out[:nx, :ny] / (dx * dy)


def perfil_1d(n):
    from geometria_canal import cargar_canal
    from flujo_1d import perfil_estacionario
    c, m, g = cargar_canal(10.0, n)
    from contracciones import ancho_fijo
    P = perfil_estacionario(c, forma_ancho=ancho_fijo(c), kd=0.0)      # diseno B: ancho constante desde la cresta
    P['t_malla'], P['t1'], P['s_malla'] = c.t_malla, g['t1'], c.s_malla
    return P


def s_de_x(P, x):
    """Abscisa desenrollada s (m) del 1D para la coordenada horizontal x (m) desde la cresta; theta local."""
    xm = P['s_malla'] * math.cos(P['t_malla'])
    if x <= xm:
        return x / math.cos(P['t_malla']), P['t_malla']
    return P['s_malla'] + (x - xm) / math.cos(P['t1']), P['t1']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('caso')
    ap.add_argument('--fig', default=None)
    a = ap.parse_args()
    t, aM, UM, C, V = cargar(a.caso)
    base = os.path.join(RES, a.caso)
    d = os.path.join(base, [x for x in os.listdir(base) if x.replace('.', '', 1).isdigit() and abs(float(x) - t) < 1e-9][0])   # nombre exacto (p. ej. 3.950089 tras un reinicio)
    aI = leer_campo(os.path.join(d, 'alpha.water'))
    UI = leer_campo(os.path.join(d, 'U'))
    s = V ** (1.0 / 3.0)
    Q_medio = 10e-3 / 2                      # semiancho
    print('%s: t = %g s | celdas %d | medias %s' % (a.caso, t, len(V), 'si' if os.path.exists(os.path.join(d, 'alpha.waterMean')) else 'NO'))

    # ---------------- lamina y velocidad sobre la malla y el tobogan ----------------
    dx, dy = 10e-3, 10e-3
    x0, x1, y1 = 0.0, 0.53, 0.26
    sel = (C[:, 0] > x0 - 0.01) & (C[:, 0] < x1 + 0.01) & (aM > 1e-4) & (s <= dx)
    hv = reparto(C[sel], s[sel], aM[sel] * V[sel], x0, x1, y1, dx, dy)                 # profundidad vertical (m)
    qx = reparto(C[sel], s[sel], aM[sel] * UM[sel, 0] * V[sel], x0, x1, y1, dx, dy)    # caudal por ancho, horizontal (m2/s)
    xc = x0 + dx * (np.arange(hv.shape[0]) + 0.5)
    yc = dy * (np.arange(hv.shape[1]) + 0.5)
    cen = yc < 0.242                          # se deja fuera la banda junto a la pared lateral (borde de la lamina)
    P1 = perfil_1d(0.010)
    P8 = perfil_1d(0.008)
    print('\nProfundidad normal a la pared h = h_vertical cos(12 deg) y velocidad V = q / h. Comparacion con el 1D (Q = 10 L/s):')
    print('  x (m) | CFD h (mm)  CV h | rango h (mm) | V (m/s) rango | CV V | Q semiancho | 1D n=0.010: h, V | 1D n=0.008: h, V')
    res = {}
    for xt in (0.10, 0.20, 0.30, 0.40, 0.50):
        i = int(round((xt - x0) / dx - 0.5))
        s1, th_loc = s_de_x(P1, xt)
        h = hv[i - 1:i + 2].mean(axis=0)[cen] * math.cos(th_loc)
        q = qx[i - 1:i + 2].mean(axis=0)[cen]
        Vv = q / h
        Qs = qx[i - 1:i + 2].mean(axis=0).sum() * dy
        j = int(np.searchsorted(P1['s'], s1))
        res[xt] = (h, Vv, Qs)
        print('  %.2f  | %5.2f  %5.1f %% | %5.2f..%5.2f | %4.2f  %4.2f..%4.2f | %4.1f %% | %.2f L/s | %5.2f, %4.2f | %5.2f, %4.2f' % (
            xt, h.mean() * 1e3, 100 * h.std() / h.mean(), h.min() * 1e3, h.max() * 1e3, Vv.mean(), Vv.min(), Vv.max(),
            100 * Vv.std() / Vv.mean(), Qs * 1e3, P1['h'][j] * 1e3, P1['V'][j], P8['h'][j] * 1e3, P8['V'][j]))

    # ---------------- aire atrapado bajo la superficie (instantaneo) ----------------
    # por columna (bins de 8 mm): cota de la superficie = mayor z con alpha > 0.5; aire = celdas con alpha < 0.5 mas de dos
    # celdas por debajo de esa cota
    print('\nAire atrapado (campo instantaneo, t = %g s): celdas con alpha < 0.5 por debajo de la superficie libre local' % t)
    b = 8e-3
    m = (C[:, 0] > -0.75) & (C[:, 0] < 0.53)
    ki = np.floor((C[:, 0] + 0.75) / b).astype(int) * 1000 + np.floor(C[:, 1] / b).astype(int)
    agua = m & (aI > 0.5)
    ztop = {}
    for k, z in zip(ki[agua], C[agua, 2]):
        if z > ztop.get(k, -9):
            ztop[k] = z
    zt = np.array([ztop.get(k, -9.0) for k in ki])
    aire = m & (aI < 0.5) & (C[:, 2] < zt - 2 * s) & (zt > -9)
    zonas = (('cajon (x < -0.10)', C[:, 0] < -0.10), ('cresta (-0.10..0.10)', (C[:, 0] >= -0.10) & (C[:, 0] < 0.10)),
             ('lamina (x >= 0.10)', C[:, 0] >= 0.10))
    for nom, z in zonas:
        vol_agua = (aI[z & m] * V[z & m]).sum()
        vol_aire = V[aire & z].sum()
        print('  %-22s agua %.3f L | aire atrapado %.4f L | %.2f %% del agua' % (nom, vol_agua * 1e3, vol_aire * 1e3, 100 * vol_aire / max(vol_agua, 1e-12)))
    if aire.any():
        o = np.argsort(-V[aire])[:5]
        idx = np.where(aire)[0][o]
        for i in idx:
            print('     burbuja mayor: x=%.3f y=%.3f z=%.3f  celda %.1f mm' % (C[i, 0], C[i, 1], C[i, 2], s[i] * 1e3))

    # ---------------- contraflujo (recirculacion) ----------------
    print('\nContraflujo (Ux < -0.05 m/s, agua con alpha > 0.5, campo instantaneo):')
    for nom, z in (('cajon  x < -0.10', C[:, 0] < -0.10), ('cresta -0.10..0.10', (C[:, 0] >= -0.10) & (C[:, 0] < 0.10)),
                   ('lamina x >= 0.10', C[:, 0] >= 0.10)):
        w = z & m & (aI > 0.5)
        rev = w & (UI[:, 0] < -0.05)
        print('  %-20s %.2f %% del agua (%.3f L)' % (nom, 100 * V[rev].sum() / max(V[w].sum(), 1e-12), V[rev].sum() * 1e3))
    # perfil vertical de Ux sobre la cresta a y ~ 0.1 (medio)
    print('\nUx media (m/s) por altura sobre la cresta, y = 0.09..0.11 m (campo medio):')
    for xx in (-0.06, -0.02, 0.0, 0.02, 0.05):
        w = (np.abs(C[:, 0] - xx) < 0.003) & (np.abs(C[:, 1] - 0.10) < 0.01) & (aM > 0.5)
        zs = np.round(C[w, 2] * 1e3 / 3).astype(int) * 3
        if not w.any():
            continue
        linea = ' '.join('z%+4d:%5.2f' % (zz, UM[w, 0][zs == zz].mean()) for zz in sorted(set(zs))[:14])
        print('  x=%+.2f  %s' % (xx, linea))

    # ---------------- variacion temporal (media vs instantanea) ----------------
    hi = reparto(C[sel], s[sel], np.where(sel, aI * V, 0)[sel], x0, x1, y1, dx, dy)
    print('\nLamina instantanea frente a la media en x = 0.5: CV instantaneo %.1f %% | media %.1f %%' % (
        100 * (hi[48:51].mean(axis=0)[cen]).std() / hi[48:51].mean(axis=0)[cen].mean(),
        100 * (hv[48:51].mean(axis=0)[cen]).std() / hv[48:51].mean(axis=0)[cen].mean()))

    if a.fig:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 2, figsize=(13, 8))
        im = ax[0, 0].imshow(hv.T * math.cos(TH) * 1e3, origin='lower', extent=[x0, x1, 0, y1], vmin=8, vmax=24, aspect='equal')
        plt.colorbar(im, ax=ax[0, 0], label='profundidad normal (mm)')
        ax[0, 0].set_title('Profundidad (media 2.5-4 s)')
        ax[0, 0].set_xlabel('x desde la cresta (m)')
        ax[0, 0].set_ylabel('y desde el eje (m)')
        Vm = np.where(hv > 5e-3, qx / np.maximum(hv * math.cos(TH), 1e-9), np.nan)
        im = ax[0, 1].imshow(Vm.T, origin='lower', extent=[x0, x1, 0, y1], vmin=0.8, vmax=1.8, aspect='equal')
        plt.colorbar(im, ax=ax[0, 1], label='velocidad V = q/h (m/s)')
        ax[0, 1].set_title('Velocidad de la lamina')
        for xt, (h, Vv, Qs) in res.items():
            ax[1, 0].plot(yc[cen] * 1e3, h * 1e3, label='x = %.1f m' % xt)
            ax[1, 1].plot(yc[cen] * 1e3, Vv, label='x = %.1f m' % xt)
        ax[1, 0].set_xlabel('y (mm)')
        ax[1, 0].set_ylabel('profundidad (mm)')
        ax[1, 0].legend()
        ax[1, 0].grid(alpha=.3)
        ax[1, 1].set_xlabel('y (mm)')
        ax[1, 1].set_ylabel('V (m/s)')
        ax[1, 1].grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(a.fig, dpi=110)
        print('figura:', a.fig)


if __name__ == '__main__':
    main()
