# -*- coding: utf-8 -*-
"""Pruebas del resolvedor 2D contra soluciones conocidas."""
import math
import time
import numpy as np
from scipy.optimize import brentq

from swe2d import correr, G


def prueba_uniforme(dx=4e-3):
    """Flujo uniforme en un plano de 12 grados: debe conservar la profundidad normal de Manning."""
    th, n, Q, b, L = math.radians(12.0), 0.010, 0.010, 0.5, 1.0
    q = Q / b
    hn = (q * n / math.sqrt(math.sin(th))) ** 0.6
    un = q / hn
    nx, ny = int(L / dx), int(b / dx)
    sol = np.zeros((nx, ny), bool)
    gsin = np.full(nx, G * math.sin(th))
    gef = np.full(nx, G * math.cos(th))
    dg = np.zeros(nx)
    res = {}
    for nombre, f in (('empezando en la profundidad normal', 1.0), ('empezando 40 % mas profundo', 1.4)):
        h = np.full((nx, ny), hn * f)
        hu = h * un
        hv = np.zeros((nx, ny))
        h_m, hu_m, hv_m, h2_m, ser, t = correr(h, hu, hv, sol, gef, dg, gsin, dx, dx, 1.5, 1.0, 0.4, n, hn, un,
                                              0.0, 0.0, np.zeros(0, np.int64), np.zeros(0, np.int64), 1e-2, np.zeros(nx), np.ones(ny), 0)
        # profundidad en el tramo final (la condicion de entrada es la normal)
        hf = h_m[int(0.8 * nx):, :].mean()
        res[nombre] = (hf, hn)
        print('  %-38s h_final = %.3f mm | h normal (Manning) = %.3f mm | desvio %+.2f %%' %
              (nombre, hf * 1e3, hn * 1e3, 100 * (hf / hn - 1)))
    return res


def teoria_resalto(F1, theta):
    """Angulo de la onda oblicua (aguas someras) y cociente de profundidades para una desviacion 'theta'."""
    def f(beta):
        r = math.sqrt(1 + 8 * F1 ** 2 * math.sin(beta) ** 2)
        return math.tan(beta) * (r - 3) / (2 * math.tan(beta) ** 2 + r - 1) - math.tan(theta)
    beta = brentq(f, math.asin(1.0 / F1) + 1e-6, math.radians(80))
    r = math.sqrt(1 + 8 * F1 ** 2 * math.sin(beta) ** 2)
    return beta, 0.5 * (r - 1)


def prueba_resalto(dx, F1=3.0, theta_deg=10.0):
    """Cuña en una pared de un canal horizontal sin friccion: comparar angulo de la onda y salto de h."""
    theta = math.radians(theta_deg)
    h1 = 0.02
    u1 = F1 * math.sqrt(G * h1)
    b, L, s0 = 1.2, 1.4, 0.3
    nx, ny = int(L / dx), int(b / dx)
    s = (np.arange(nx) + 0.5) * dx
    y = -b / 2 + (np.arange(ny) + 0.5) * dx
    ypared = b / 2 - np.maximum(s - s0, 0.0) * math.tan(theta)           # la pared superior se cierra
    sol = y[None, :] > ypared[:, None]
    gsin = np.zeros(nx)
    gef = np.full(nx, G)
    dg = np.zeros(nx)
    h = np.full((nx, ny), h1)
    hu = np.where(sol, 0.0, h1 * u1)
    hv = np.zeros((nx, ny))
    t0 = time.time()
    h_m, hu_m, hv_m, h2_m, ser, t = correr(h, hu, hv, sol, gef, dg, gsin, dx, dx, 1.4, 0.8, 0.4, 0.0, h1, u1,
                                          0.0, 0.0, np.zeros(0, np.int64), np.zeros(0, np.int64), 1e-2, np.zeros(nx), np.ones(ny), 0)
    beta_t, cociente_t = teoria_resalto(F1, theta)
    # angulo medido: para cada s posterior a s0 se busca la posicion del frente (h = mitad del salto) desde la pared
    h2 = h1 * cociente_t
    frente = []
    for i in range(int((s0 + 0.10) / dx), int((s0 + 0.45) / dx), 4):
        col = h_m[i, :]
        libre = ~sol[i, :]
        jj = np.where(libre & (col > 0.5 * (h1 + h2)))[0]
        if len(jj):
            frente.append((s[i], y[jj.min()]))
    frente = np.array(frente)
    pend = np.polyfit(frente[:, 0], frente[:, 1], 1)[0]
    beta_num = math.atan(-pend)           # angulo del frente respecto al eje del flujo
    # profundidad detras de la onda: cerca de la pared, tramo final
    i0 = int((s0 + 0.42) / dx)
    j = np.where(~sol[i0, :])[0][-6]
    h_det = h_m[i0, j]
    print('  dx = %.1f mm | F1 = %.1f, desviacion %.0f grados | onda: teoria %.1f grados, simulada %.1f grados | '
          'h2/h1: teoria %.3f, simulada %.3f (%+.1f %%) [%.0f s]' %
          (dx * 1e3, F1, theta_deg, math.degrees(beta_t), math.degrees(beta_num), cociente_t, h_det / h1,
           100 * (h_det / h1 / cociente_t - 1), time.time() - t0))
    return math.degrees(beta_t), math.degrees(beta_num), cociente_t, h_det / h1


if __name__ == '__main__':
    print('Prueba 1: flujo uniforme en un plano inclinado (Manning)')
    prueba_uniforme()
    print('Prueba 2: onda oblicua (resalto) en una desviacion de la pared, sin friccion')
    for dx in (8e-3, 4e-3, 2e-3):
        prueba_resalto(dx)
    for dx in (8e-3, 4e-3):
        prueba_resalto(dx, F1=2.0, theta_deg=8.0)
    for dx in (8e-3, 4e-3):
        prueba_resalto(dx, F1=4.0, theta_deg=15.0)
