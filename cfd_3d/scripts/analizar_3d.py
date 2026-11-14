# -*- coding: utf-8 -*-
"""Analiza un caso de snappy (losa o medio): profundidad h(x, y) y caudal unitario q(x, y) de la lamina de agua sobre la
malla y el tobogan, a partir de alpha.water y U (medias si existen), con los centros y volumenes de celda.

    python analizar_3d.py <caso> [--dx 4e-3] [--dy 4e-3] [--x0 0.0] [--fig salida.png]
"""
import argparse
import os
import re

import numpy as np

from leer_openfoam import leer_campo

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(AQUI, '..', 'resultados')


def cargar(caso):
    d = os.path.join(RES, caso)
    tiempos = sorted([x for x in os.listdir(d) if re.match(r'^[0-9.]+(e[-+]?[0-9]+)?$', x) and x != '0'], key=float)
    t = tiempos[-1]
    ruta = os.path.join(d, t)
    a = leer_campo(os.path.join(ruta, 'alpha.waterMean' if os.path.exists(os.path.join(ruta, 'alpha.waterMean')) else 'alpha.water'))
    U = leer_campo(os.path.join(ruta, 'UMean' if os.path.exists(os.path.join(ruta, 'UMean')) else 'U'))
    C = leer_campo(os.path.join(ruta, 'C'))
    V = leer_campo(os.path.join(ruta, 'V'))
    return float(t), a, U, C, V


def mapa(caso, dx=4e-3, dy=4e-3, x_max=0.53, y_max=None):
    t, a, U, C, V = cargar(caso)
    ymaxd = C[:, 1].max() + 1e-6 if y_max is None else y_max
    # solo la lamina sobre la malla y el tobogan (x >= 0)
    m = (C[:, 0] >= 0.0) & (C[:, 0] < x_max)
    xs = np.arange(0.0, x_max + dx, dx)
    ys = np.arange(0.0, ymaxd + dy, dy)
    ix = np.clip(((C[m, 0]) / dx).astype(int), 0, len(xs) - 2)
    iy = np.clip(((C[m, 1]) / dy).astype(int), 0, len(ys) - 2)
    h = np.zeros((len(xs) - 1, len(ys) - 1))
    q = np.zeros_like(h)
    np.add.at(h, (ix, iy), a[m] * V[m] / (dx * dy))
    np.add.at(q, (ix, iy), a[m] * U[m, 0] * V[m] / (dx * dy))
    return t, xs, ys, h, q


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('caso')
    ap.add_argument('--dx', type=float, default=4e-3)
    ap.add_argument('--dy', type=float, default=4e-3)
    ap.add_argument('--fig', default=None)
    a = ap.parse_args()
    t, xs, ys, h, q = mapa(a.caso, a.dx, a.dy)
    losa = h.shape[1] <= 2
    print('%s: t = %g s, mapa %d x %d' % (a.caso, t, h.shape[0], h.shape[1]))
    xc = 0.5 * (xs[1:] + xs[:-1])
    if losa:
        print('   x (m)   h (mm)   q (m2/s)   V = q/h (m/s)')
        for x0 in (0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5):
            i = np.searchsorted(xc, x0)
            print('  %5.2f   %6.2f   %8.5f   %6.2f' % (xc[i], h[i, 0] * 1e3, q[i, 0], q[i, 0] / max(h[i, 0], 1e-9)))
    else:
        yc = 0.5 * (ys[1:] + ys[:-1])
        for x0 in (0.1, 0.2, 0.3, 0.4, 0.5):
            i = np.searchsorted(xc, x0)
            sl = slice(max(i - 2, 0), i + 3)
            hh = h[sl].mean(axis=0)
            qq = q[sl].mean(axis=0)
            ok = (yc < 0.245) & (hh > 1e-4)
            if ok.sum() < 3:
                continue
            print('  x = %.2f m: h %.2f mm (%.2f..%.2f) | CV h %.1f %% | V %.2f m/s (%.2f..%.2f) | CV V %.1f %%' % (
                xc[i], hh[ok].mean() * 1e3, hh[ok].min() * 1e3, hh[ok].max() * 1e3, 100 * hh[ok].std() / hh[ok].mean(),
                (qq[ok] / hh[ok]).mean(), (qq[ok] / hh[ok]).min(), (qq[ok] / hh[ok]).max(),
                100 * (qq[ok] / hh[ok]).std() / (qq[ok] / hh[ok]).mean()))
    if a.fig:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(11, 4))
        if losa:
            ax.plot(xc, h[:, 0] * 1e3)
            ax.set_xlabel('x desde la cresta (m)')
            ax.set_ylabel('profundidad (mm)')
        else:
            im = ax.imshow((h.T * 1e3), origin='lower', extent=[xs[0], xs[-1], ys[0], ys[-1]], aspect='equal', vmin=0, vmax=15)
            plt.colorbar(im, label='profundidad (mm)')
            ax.set_xlabel('x desde la cresta (m)')
            ax.set_ylabel('y (m)')
        fig.savefig(a.fig, dpi=120, bbox_inches='tight')
