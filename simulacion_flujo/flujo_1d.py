# -*- coding: utf-8 -*-
"""Etapa 1: perfil 1D del agua a lo largo del canal (flujo gradualmente variado, metodo de paso estandar).

Ecuacion de energia sobre el fondo desenrollado, con presion en el fondo corregida por la curvatura del arco:
    H = z + h*(cos(theta) - V^2*kappa/g) + V^2/(2 g)        con V = Q/(b*h),  kappa = 1/R (convexo > 0)
    dH/ds = -Sf                                              Sf de Manning
Condicion de partida: profundidad critica sobre la cresta del vertedero. Se sigue la rama supercritica.
"""
import numpy as np
from scipy.optimize import brentq

from geometria_canal import G, NU


def _f(h, Q, b, cos_t, kappa):
    V = Q / (b * h)
    return h * cos_t - V * V * h * kappa / G + V * V / (2 * G)


def _h_critica(Q, b, cos_t, kappa):
    """Profundidad que minimiza la energia especifica (Fr = 1)."""
    d = lambda h: (_f(h * 1.0001, Q, b, cos_t, kappa) - _f(h * 0.9999, Q, b, cos_t, kappa))
    return brentq(d, 1e-6, 1.0, xtol=1e-9)


def _sf(h, Q, b, n):
    V = Q / (b * h)
    Rh = b * h / (b + 2 * h)
    return n * n * V * V / Rh ** (4.0 / 3.0)


def profundidad_normal(q, sen_t, n):
    """Profundidad normal (canal ancho, Manning) para caudal unitario q y pendiente sen(theta)."""
    return (q * n / np.sqrt(sen_t)) ** 0.6


def perfil_estacionario(c, Q=None, forma_ancho=None, curvatura=True, ds=5e-4, n=None, kd=0.0):
    """kd: coeficiente de drenaje de la malla (velocidad de paso = kd*sqrt(2 g h cos(theta))) sobre s < s_malla.
    El agua drenada sale con la energia local (hipotesis de De Marchi), asi que solo cambia el caudal Q(s)."""
    Q = c.Q if Q is None else Q
    n_m = c.n_manning if n is None else n
    N = int(round(c.L / ds))
    s = np.linspace(0.0, c.L, N + 1)
    th = c.theta(s)
    kap = c.curvatura(s) if curvatura else np.zeros_like(s)
    b = c.ancho(s, forma_ancho)
    z = c.cota(s)
    cos_t, sen_t = np.cos(th), np.sin(th)

    def drenaje(i, h_i):                 # caudal drenado en el tramo [i, i+1]
        if kd <= 0.0 or s[i] >= c.s_malla:
            return 0.0
        return kd * 0.5 * (b[i] + b[i + 1]) * np.sqrt(2 * G * cos_t[i] * h_i) * ds

    h = np.zeros_like(s)
    Qs = np.full_like(s, Q)
    bloqueo = np.zeros(len(s), bool)             # True donde no alcanza la energia (hace falta un resalto)
    h[0] = _h_critica(Q, b[0], cos_t[0], kap[0])
    Hc = z[0] + _f(h[0], Q, b[0], cos_t[0], kap[0])
    for i in range(N):
        Q1 = max(Qs[i] - drenaje(i, h[i]), 1e-6)
        Sf0 = _sf(h[i], Qs[i], b[i], n_m)
        objetivo = Hc - Sf0 * ds - z[i + 1]
        hc = _h_critica(Q1, b[i + 1], cos_t[i + 1], kap[i + 1])
        fmin = _f(hc, Q1, b[i + 1], cos_t[i + 1], kap[i + 1])
        if objetivo <= fmin:                      # sin energia suficiente: se queda en critico (bloqueo)
            h[i + 1] = hc
            Qs[i + 1] = Q1
            bloqueo[i + 1] = True
            Hc = z[i + 1] + fmin
            continue
        g = lambda hh: _f(hh, Q1, b[i + 1], cos_t[i + 1], kap[i + 1]) - objetivo
        h1 = brentq(g, 1e-5, hc, xtol=1e-10)
        for _ in range(2):                        # corrector: Sf medio y drenaje con h medio
            Q1 = max(Qs[i] - drenaje(i, 0.5 * (h[i] + h1)), 1e-6)
            hc = _h_critica(Q1, b[i + 1], cos_t[i + 1], kap[i + 1])
            fmin = _f(hc, Q1, b[i + 1], cos_t[i + 1], kap[i + 1])
            Sf1 = _sf(h1, Q1, b[i + 1], n_m)
            objetivo = Hc - 0.5 * (Sf0 + Sf1) * ds - z[i + 1]
            if objetivo > fmin:
                h1 = brentq(lambda hh: _f(hh, Q1, b[i + 1], cos_t[i + 1], kap[i + 1]) - objetivo, 1e-5, hc,
                            xtol=1e-10)
        h[i + 1] = h1
        Qs[i + 1] = Q1
        Hc = z[i + 1] + _f(h1, Q1, b[i + 1], cos_t[i + 1], kap[i + 1])

    V = Qs / (b * h)
    g_ef = G * cos_t - V * V * kap
    Fr = V / np.sqrt(G * cos_t * h)
    Fr_ef = V / np.sqrt(np.maximum(g_ef, 1e-3) * h)
    Rh = b * h / (b + 2 * h)
    # capa limite turbulenta sobre pared lisa (placa plana, ley 1/7): delta = 0.37 s Re_s^(-1/5)
    Vmed = np.cumsum(V) / (np.arange(len(V)) + 1)
    delta = np.where(s > 0, 0.37 * s * (Vmed * np.maximum(s, 1e-9) / NU) ** (-0.2), 0.0)
    return {'s': s, 'z': z, 'theta': th, 'kappa': kap, 'b': b, 'h': h, 'V': V, 'q': Qs / b, 'Fr': Fr,
            'Fr_ef': Fr_ef, 'g_ef': g_ef, 'hn': profundidad_normal(Qs / b, sen_t, n_m),
            'Re': V * h / NU, 'We': 1000.0 * V * V * h / 0.072, 'delta_cl': delta, 'bloqueo': bloqueo,
            'Rh': Rh, 'Q': Q, 'Qs': Qs, 'n': n_m, 'kd': kd}


def calibrar_kd(c, fraccion, forma_ancho=None, Q=None):
    """kd con el que la malla drena la 'fraccion' del caudal (perfil 1D)."""
    def f(kd):
        P = perfil_estacionario(c, Q=Q, forma_ancho=forma_ancho, kd=kd, ds=1e-3)
        return 1.0 - P['Qs'][np.searchsorted(P['s'], c.s_malla)] / P['Q'] - fraccion
    return brentq(f, 1e-4, 0.4, xtol=1e-6)


def resumen(c, P, log=print):
    i = np.searchsorted(P['s'], c.s_conteo)
    log('Perfil 1D (Q = %.1f L/s, n = %.3f%s)' % (P['Q'] * 1e3, P['n'],
                                             ', drena %.0f %% por la malla' % (100 * (1 - P['Qs'][-1] / P['Q'])) if P['kd'] else ''))
    for nombre, s in (('cresta', 0.0), ('inicio contraccion', c.s_cont0), ('fin contraccion / entrada canal', c.s_cont1),
                      ('inicio arco', c.s_arco0), ('fin arco', c.s_arco1), ('linea de conteo', c.s_conteo),
                      ('final del tobogan', c.L)):
        k = min(np.searchsorted(P['s'], s), len(P['s']) - 1)
        log('  %-32s s = %.3f m | h = %5.1f mm | V = %.2f m/s | Fr = %4.1f | hn = %5.1f mm' %
            (nombre, P['s'][k], P['h'][k] * 1e3, P['V'][k], P['Fr'][k], P['hn'][k] * 1e3))
    log('  Reynolds en el conteo Re = V h / nu = %.0f | Weber = %.0f' % (P['Re'][i], P['We'][i]))
    j = np.argmax(P['delta_cl'] >= P['h'])
    if P['delta_cl'][j] >= P['h'][j]:
        log('  la capa limite turbulenta llega a la superficie libre en s = %.2f m' % P['s'][j])
    log('  bloqueo (falta energia): %s' % ('SI, entre s = %.3f y %.3f m' % (P['s'][P['bloqueo']].min(),
                                                                          P['s'][P['bloqueo']].max())
                                         if P['bloqueo'].any() else 'no'))
