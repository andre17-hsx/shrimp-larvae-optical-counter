# -*- coding: utf-8 -*-
"""Aproximacion subcritica al vertedero: el cajon se estrecha ANTES de la cresta (flujo lento, sin ondas de choque).

Se simula el tramo desde 'x_ini' metros aguas arriba de la cresta hasta 'x_fin' aguas abajo, en 2D. El fondo del
cajon esta a ALTO_VERTEDERO bajo la cresta; aqui se representa con el fondo a la altura de la cresta (calado H sobre
ella), lo cual es la hipotesis DESFAVORABLE (velocidad de aproximacion mayor que la real). La cresta es donde el fondo
empieza a bajar con la pendiente de la malla.
"""
import math
import numpy as np

from geometria_canal import cargar_canal, G
from contracciones import _suave
from swe2d import correr

# c.coef_vert (1,705) y c.factor_nivel (1,022) vienen del script de Fusion (COEF_VERTEDERO, FACTOR_NIVEL); el factor se
# calibro porque con 1,705 b H^1,5 el modelo deja pasar solo 96,8 % del caudal nominal (perdidas en el estrechamiento)


def correr_aproximacion(c, Q=None, x_contra=0.25, tipo='coseno', dx=4e-3, x_ini=0.40, x_fin=0.60, t_fin=6.0,
                        t_prom=4.5, ancho_cajon=None, kd=0.0):
    Q = c.Q if Q is None else Q
    B = c.ancho0 if ancho_cajon is None else ancho_cajon
    b1 = c.ancho1
    nx, ny = int(round((x_ini + x_fin) / dx)), int(round(B / dx))
    s = -x_ini + (np.arange(nx) + 0.5) * dx
    y = -B / 2 + (np.arange(ny) + 0.5) * dx
    b = B + (b1 - B) * _suave((s + x_contra) / x_contra, tipo)
    sol = np.abs(y)[None, :] > (b[:, None] / 2 + 1e-12)
    th = np.where(s < 0, 0.0, c.t_malla)
    gsin, gef = G * np.sin(th), G * np.cos(th)
    dg = np.gradient(gef, s)
    kdren = np.where((s >= 0) & (s < c.s_malla), kd, 0.0)
    He = c.factor_nivel * (Q / (c.coef_vert * b1)) ** (2.0 / 3.0)   # nivel sobre la cresta: q = 1,705 H^1,5 (critico), ajustado
    h0 = np.full((nx, ny), He)
    u0 = Q / (np.maximum(b, 1e-3) * He)
    hu0 = np.where(sol, 0.0, (He * u0)[:, None] * np.ones((1, ny)))
    hv0 = np.zeros((nx, ny))
    h_m, hu_m, hv_m, h2, ser, t = correr(h0, hu0, hv0, sol, gef, dg, gsin, dx, dx, t_fin, t_prom, 0.4, c.n_manning,
                                        He, Q / (B * He), 0.0, 0.0, np.zeros(0, np.int64), np.zeros(0, np.int64), 1e-2,
                                        kdren, np.ones(ny), 1)
    u_m = np.where(h_m > 0, hu_m / np.maximum(h_m, 1e-9), 0.0)
    v_m = np.where(h_m > 0, hv_m / np.maximum(h_m, 1e-9), 0.0)
    return {'s': s, 'y': y, 'sol': sol, 'h': h_m, 'u': u_m, 'v': v_m, 'b': b, 'dx': dx, 'He': He, 'rms': np.sqrt(np.maximum(h2 - h_m ** 2, 0))}


def resumen(r, c):
    s, y, h, u, v, sol = r['s'], r['y'], r['h'], r['u'], r['v'], r['sol']
    for nombre, s0 in (('entrada', s[3]), ('inicio del estrechamiento', -0.25), ('antes de la cresta', -0.02), ('cresta', 0.0), ('a 0,2 m de la cresta', 0.2)):
        i = np.searchsorted(s, s0)
        libre = ~sol[i]
        hh, uu, vv = h[i, libre] * 1e3, u[i, libre], v[i, libre]
        Fr = uu / np.sqrt(G * h[i, libre])
        print('  %-28s s=%+.2f | h %5.1f (%4.1f..%5.1f) mm | u %.2f (%.2f..%.2f) | Fr %.2f..%.2f | v max %.2f m/s' %
              (nombre, s[i], hh.mean(), hh.min(), hh.max(), uu.mean(), uu.min(), uu.max(), Fr.min(), Fr.max(), np.abs(vv).max()))


if __name__ == '__main__':
    c, m, g = cargar_canal()
    for x_c in (0.25, 0.40):
        print('estrechamiento subcritico de %.0f mm de largo (994 -> 504 mm), coseno' % (x_c * 1e3))
        r = correr_aproximacion(c, x_contra=x_c)
        resumen(r, c)


class Completo:
    """Aproximacion + canal completo en un mismo dominio 2D (compatible con contracciones.metricas y larvas)."""
    pass


def correr_completo(c, Q=None, x_contra=0.25, tipo="coseno", dx=6e-3, x_ini=0.40, t_fin=9.0, t_prom=7.5, kd=0.0,
                    fq=None, ancho_final=None, x_recto=0.0, pert_a=0.0, pert_f=0.0, sondas=(), dt_sonda=1e-3):
    """Del cajon (fondo a la altura de la cresta, calado He) hasta el final del tobogan, con el estrechamiento
    subcritico de 'x_contra' metros que termina 'x_recto' metros antes de la cresta. ancho_final: ancho del canal (por defecto el del diseno)."""
    Q = c.Q if Q is None else Q
    B = c.ancho0
    b1 = c.ancho1 if ancho_final is None else ancho_final
    nx, ny = int(round((x_ini + c.L) / dx)), int(round(B / dx))
    s = -x_ini + (np.arange(nx) + 0.5) * dx
    y = -B / 2 + (np.arange(ny) + 0.5) * dx
    b = B + (b1 - B) * _suave((s + x_recto + x_contra) / x_contra, tipo)     # tramo recto de 'x_recto' antes de la cresta
    sol = np.abs(y)[None, :] > (b[:, None] / 2 + 1e-12)
    th = np.where(s < 0, 0.0, c.theta(np.maximum(s, 0.0)))
    gsin, gef = G * np.sin(th), G * np.cos(th)
    dg = np.gradient(gef, s)
    kdren = np.where((s >= 0) & (s < c.s_malla), kd, 0.0)
    He = c.factor_nivel * (Q / (c.coef_vert * b1)) ** (2.0 / 3.0)
    u0 = Q / (np.maximum(b, 1e-3) * He)
    h0 = np.full((nx, ny), He)
    hu0 = np.where(sol, 0.0, (He * u0)[:, None] * np.ones((1, ny)))
    fq = np.ones(ny) if fq is None else np.asarray(fq, float)
    si = np.array([np.searchsorted(s, s0) for s0, _ in sondas], np.int64) if sondas else np.zeros(0, np.int64)
    sj = np.array([np.searchsorted(y, y0) for _, y0 in sondas], np.int64) if sondas else np.zeros(0, np.int64)
    h_m, hu_m, hv_m, h2, ser, t = correr(h0, hu0, np.zeros((nx, ny)), sol, gef, dg, gsin, dx, dx, t_fin, t_prom, 0.4,
                                        c.n_manning, He, Q / (B * He), pert_a, pert_f, si, sj, dt_sonda, kdren, fq, 1)
    r = Completo()
    r.c, r.dx, r.dy, r.s, r.y, r.sol, r.nx, r.ny = c, dx, dx, s, y, sol, nx, ny
    r.h_m = h_m
    r.u_m = np.where(h_m > 0, hu_m / np.maximum(h_m, 1e-9), 0.0)
    r.v_m = np.where(h_m > 0, hv_m / np.maximum(h_m, 1e-9), 0.0)
    r.h_rms = np.sqrt(np.maximum(h2 - h_m ** 2, 0.0))
    r.b = b
    r.He = He
    r.serie = ser
    return r
