# -*- coding: utf-8 -*-
"""Analiza los casos f0a (lamina sobre plano inclinado): profundidad y caudal a lo largo, frente a la teoria.

    python analizar_f0a.py f0a_base [f0a_fino ...]
"""
import glob
import math
import os
import sys

import numpy as np

from leer_openfoam import leer_campo

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(AQUI, '..', 'resultados')
NU = 1e-6
G = 9.81


def profundidad_lisa(q, theta):
    """Profundidad normal para pared hidraulicamente lisa (Prandtl-Karman), canal ancho: R = h."""
    S = math.sin(theta)
    def resid(h):
        V = q / h
        Re = 4 * h * V / NU
        f = 0.02
        for _ in range(60):
            f = (2 * math.log10(Re * math.sqrt(f)) - 0.8) ** -2
        return f * V * V / (8 * G * h) - S
    lo, hi = 1e-3, 5e-2
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        (lo, hi) = (mid, hi) if resid(mid) > 0 else (lo, mid)
    return 0.5 * (lo + hi)


def perfil_columnas(caso):
    d = os.path.join(RES, caso)
    tiempos = sorted([x for x in os.listdir(d) if re.match(r'^[0-9.]+(e[-+]?[0-9]+)?$', x) and x != '0'],
                     key=float) if os.path.isdir(d) else []
    t = tiempos[-1]
    a = leer_campo(os.path.join(d, t, 'alpha.water'))
    U = leer_campo(os.path.join(d, t, 'U'))
    C = leer_campo(os.path.join(d, t, 'C'))
    V = leer_campo(os.path.join(d, t, 'V'))
    return float(t), a, U, C, V


import re  # noqa: E402


if __name__ == '__main__':
    q_teo = 0.0198
    th = math.radians(12.0)
    hM = (q_teo * 0.010 / math.sqrt(math.sin(th))) ** 0.6
    hL = profundidad_lisa(q_teo, th)
    print('Teoria: Manning n=0,010 -> h = %.2f mm (V = %.2f m/s) | pared lisa (Prandtl) -> h = %.2f mm (V = %.2f m/s)' %
          (hM * 1e3, q_teo / hM, hL * 1e3, q_teo / hL))
    for caso in sys.argv[1:]:
        t, a, U, C, V = perfil_columnas(caso)
        xs = np.round(C[:, 0], 6)
        ux = np.unique(xs)
        dx = ux[1] - ux[0]
        dy = 0.01
        h, q = np.zeros(len(ux)), np.zeros(len(ux))
        idx = np.searchsorted(ux, xs)
        np.add.at(h, idx, a * V / (dx * dy))
        np.add.at(q, idx, a * U[:, 0] * V / (dx * dy))
        print('\n%s (t = %g s, %d celdas, dx = %.2f mm)' % (caso, t, len(a), dx * 1e3))
        print('   x (m)   h (mm)   q/q_in   V=q/h (m/s)')
        for x0 in (0.1, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.45):
            i = np.searchsorted(ux, x0)
            print('  %5.2f   %6.2f   %6.3f   %6.2f' % (ux[i], h[i] * 1e3, q[i] / q_teo, q[i] / max(h[i], 1e-9)))
        j = np.searchsorted(ux, 1.2)
        print('   x > 1.2 m: h medio = %.2f mm | Manning %.2f | pared lisa %.2f' % (h[j:].mean() * 1e3, hM * 1e3, hL * 1e3))
