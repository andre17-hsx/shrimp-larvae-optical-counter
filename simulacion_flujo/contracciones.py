# -*- coding: utf-8 -*-
"""Familias de contracciones (ancho del canal en funcion de s) y metricas de uniformidad en la linea de conteo."""
import math
import numpy as np

from geometria_canal import cargar_canal
from flujo_1d import perfil_estacionario
from swe2d import Caso


def _suave(u, tipo):
    u = np.clip(u, 0.0, 1.0)
    if tipo == 'lineal':
        return u
    if tipo == 'coseno':
        return 0.5 * (1.0 - np.cos(math.pi * u))
    if tipo == 'quintica':
        return u ** 3 * (10 - 15 * u + 6 * u * u)
    raise ValueError(tipo)


def forma(c, s0, s1, tipo='lineal'):
    """b(s): ancho0 hasta s0, ancho1 desde s1, transicion 'tipo' entre ambos."""
    def f(s):
        s = np.asarray(s, float)
        return c.ancho0 + (c.ancho1 - c.ancho0) * _suave((s - s0) / (s1 - s0), tipo)
    return f


def ancho_fijo(c):
    """Sin contraccion en el tobogan: el canal ya tiene el ancho final desde la cresta (la contraccion pasa
    aguas arriba, con flujo lento, donde no genera ondas de choque)."""
    return lambda s: np.full_like(np.asarray(s, float), c.ancho1)


def angulo_max(c, f):
    s = np.linspace(0, c.L, 4000)
    db = np.gradient(f(s), s)
    return math.degrees(math.atan(np.abs(db).max() / 2))


def metricas(c, caso, ventana=0.025):
    """Uniformidad de la lamina en la ventana de conteo (s_conteo +- ventana)."""
    i0, i1 = np.searchsorted(caso.s, [c.s_conteo - ventana, c.s_conteo + ventana])
    libre = ~caso.sol[i0:i1 + 1, :].any(axis=0)
    h = caso.h_m[i0:i1 + 1][:, libre].mean(axis=0) * 1e3
    u = caso.u_m[i0:i1 + 1][:, libre].mean(axis=0)
    q = h * u
    return {'h_media': h.mean(), 'h_min': h.min(), 'h_max': h.max(), 'cv_h': 100 * h.std() / h.mean(),
            'u_min': u.min(), 'u_max': u.max(), 'cv_u': 100 * u.std() / u.mean(), 'cv_q': 100 * q.std() / q.mean(),
            'h_pico_dominio': caso.h_m.max() * 1e3, 'rms_t': float(caso.h_rms.max()) * 1e3}


def correr_forma(c, f, dx=6e-3, Q=None, t_fin=3.5, t_prom=2.5, **kw):
    P = perfil_estacionario(c, Q=Q, forma_ancho=f)
    caso = Caso(c, P, dx=dx, forma_ancho=f, **kw).ejecutar(t_fin, t_prom)
    return caso, P


def caudal_en(caso, i):
    """Caudal (L/s) que cruza la columna i (promedio temporal)."""
    return float((caso.h_m[i, :] * caso.u_m[i, :]).sum() * caso.dy * 1e3)


def correr_forma(c, f, dx=6e-3, Q=None, t_fin=3.5, t_prom=2.5, kd=0.0, **kw):
    P = perfil_estacionario(c, Q=Q, forma_ancho=f, kd=kd)
    caso = Caso(c, P, dx=dx, forma_ancho=f, kd=kd, **kw).ejecutar(t_fin, t_prom)
    return caso, P
