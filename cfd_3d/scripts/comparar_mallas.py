# -*- coding: utf-8 -*-
"""Compara la profundidad de la lamina a lo ancho entre dos casos 3D de semiancho (p. ej. pelicula de 2 mm y de 4 mm).

    python comparar_mallas.py p2_medio_grueso p2_medio_mm4 [--fig salida.png]
Imprime, para cada distancia x de la cresta: profundidad media, desviacion tipica a lo ancho, correlacion de los perfiles y
cociente de amplitudes. Requiere numpy y matplotlib (entorno simenv).
"""
import argparse
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from analizar_3d import cargar  # noqa: E402
from analizar_criterios import reparto  # noqa: E402

TH = math.atan(0.2127659574468085)


def perfiles(caso):
    t, aM, UM, C, V = cargar(caso)
    s = V ** (1.0 / 3.0)
    dx = dy = 10e-3
    x0, x1, y1 = 0.0, 0.53, 0.26
    sel = (C[:, 0] > x0 - 0.01) & (C[:, 0] < x1 + 0.01) & (aM > 1e-4) & (s <= dx)
    hv = reparto(C[sel], s[sel], aM[sel] * V[sel], x0, x1, y1, dx, dy) * math.cos(TH)
    yc = dy * (np.arange(hv.shape[1]) + 0.5)
    return t, hv, yc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--fig', default=None)
    ap.add_argument('--etq-a', dest='etq_a', default='caso A')
    ap.add_argument('--etq-b', dest='etq_b', default='caso B')
    o = ap.parse_args()
    ta, ha, yc = perfiles(o.a)
    tb, hb, _ = perfiles(o.b)
    cen = yc < 0.242
    print('%s (t=%g) frente a %s (t=%g), profundidad normal (mm), 10 mm de ancho de bin' % (o.a, ta, o.b, tb))
    print('  x (m) | media A  media B | desv.tip A  B (mm) | CV A    B    | correlacion | amplitud B/A')
    filas = []
    for xt in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50):
        i = int(round(xt / 0.01 - 0.5))
        pa = ha[i - 1:i + 2].mean(axis=0)[cen] * 1e3
        pb = hb[i - 1:i + 2].mean(axis=0)[cen] * 1e3
        da, db = pa - pa.mean(), pb - pb.mean()
        r = float(np.corrcoef(da, db)[0, 1])
        filas.append((xt, pa, pb))
        print('  %.2f  | %5.2f   %5.2f  |  %4.2f  %4.2f      | %4.1f %%  %4.1f %% |   %+.2f     |   %.2f' % (
            xt, pa.mean(), pb.mean(), da.std(), db.std(), 100 * da.std() / pa.mean(), 100 * db.std() / pb.mean(), r, db.std() / da.std()))
    # zona de ondas estacionarias: promedio en x = 0.30-0.50
    ra = np.mean([np.corrcoef(p[1] - p[1].mean(), p[2] - p[2].mean())[0, 1] for p in filas if p[0] >= 0.30])
    ca = np.mean([(p[1].std() / p[1].mean()) for p in filas if p[0] >= 0.30]) * 100
    cb = np.mean([(p[2].std() / p[2].mean()) for p in filas if p[0] >= 0.30]) * 100
    print('\nx = 0,30-0,50 m: correlacion media %.2f | CV medio A %.1f %%, B %.1f %%' % (ra, ca, cb))
    if o.fig:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        S = '#33485A'
        plt.rcParams.update({'font.size': 11, 'axes.edgecolor': S, 'axes.labelcolor': S, 'xtick.color': S, 'ytick.color': S,
                             'text.color': S, 'axes.spines.top': False, 'axes.spines.right': False})
        fig, ax = plt.subplots(1, 3, figsize=(13, 3.9), sharey=True)
        for a_, (xt, pa, pb) in zip(ax, [f for f in filas if f[0] in (0.20, 0.35, 0.50)]):
            a_.plot(yc[cen] * 1e3, pa, color='#0B7A8C', lw=2.2, label=o.etq_a)
            a_.plot(yc[cen] * 1e3, pb, color='#2F62A3', lw=2.2, ls='--', label=o.etq_b)
            a_.set_title('a %.2f m de la cresta' % xt, fontsize=11)
            a_.set_xlabel('y desde el eje (mm)')
            a_.grid(alpha=.35, color='#D5DEE5')
        ax[0].set_ylabel('profundidad normal (mm)')
        ax[0].legend(frameon=False, fontsize=10)
        fig.tight_layout()
        fig.savefig(o.fig, dpi=140)

if __name__ == '__main__':
    main()
