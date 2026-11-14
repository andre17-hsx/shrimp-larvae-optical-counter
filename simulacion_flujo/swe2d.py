# -*- coding: utf-8 -*-
"""Etapa 2: aguas someras 2D (Saint-Venant) promediadas en profundidad, sobre el canal desenrollado.

Coordenadas (s, y): s a lo largo del fondo desde la cresta del vertedero, y transversal.
    dh/dt + d(hu)/ds + d(hv)/dy = 0
    d(hu)/dt + d(hu^2 + g' h^2/2)/ds + d(huv)/dy = g sen(theta) h - h^2/2 dg'/ds - Sf_x
    d(hv)/dt + d(huv)/ds + d(hv^2 + g' h^2/2)/dy = -Sf_y
con g' = g cos(theta(s)) y friccion de Manning. Volumenes finitos, flujo HLL, reconstruccion MUSCL (minmod) y
Runge-Kutta 2. Las paredes (contraccion incluida) son celdas solidas con reflexion.
"""
import math
import numpy as np
from numba import njit, prange

G = 9.81
HMIN = 1e-4


@njit(cache=True, fastmath=True)
def _minmod(a, b):
    if a * b <= 0.0:
        return 0.0
    return a if abs(a) < abs(b) else b


@njit(cache=True, fastmath=True)
def _hll(hl, ul, vl, hr, ur, vr, g):
    """Flujo HLL con 'u' como componente normal a la cara y 'v' como tangencial."""
    cl = math.sqrt(g * hl)
    cr = math.sqrt(g * hr)
    sl = min(ul - cl, ur - cr)
    sr = max(ul + cl, ur + cr)
    f0l = hl * ul
    f1l = hl * ul * ul + 0.5 * g * hl * hl
    f2l = hl * ul * vl
    if sl >= 0.0:
        return f0l, f1l, f2l
    f0r = hr * ur
    f1r = hr * ur * ur + 0.5 * g * hr * hr
    f2r = hr * ur * vr
    if sr <= 0.0:
        return f0r, f1r, f2r
    d = 1.0 / (sr - sl)
    return ((sr * f0l - sl * f0r + sl * sr * (hr - hl)) * d,
            (sr * f1l - sl * f1r + sl * sr * (hr * ur - hl * ul)) * d,
            (sr * f2l - sl * f2r + sl * sr * (hr * vr - hl * vl)) * d)


@njit(cache=True, parallel=True, fastmath=True)
def _rhs(h, u, v, sol, gef, dgef, gsin, dx, dy, hin, uin, vin, dh, dhu, dhv,
         sxh, sxu, sxv, syh, syu, syv, F0, F1, F2, G0, G1, G2, kdren):
    nx, ny = h.shape
    # --- pendientes limitadas (cero junto a paredes y contornos) ---
    for i in prange(nx):
        for j in range(ny):
            sxh[i, j] = 0.0
            sxu[i, j] = 0.0
            sxv[i, j] = 0.0
            syh[i, j] = 0.0
            syu[i, j] = 0.0
            syv[i, j] = 0.0
            if sol[i, j]:
                continue
            if i > 0 and i < nx - 1 and (not sol[i - 1, j]) and (not sol[i + 1, j]):
                sxh[i, j] = _minmod(h[i, j] - h[i - 1, j], h[i + 1, j] - h[i, j])
                sxu[i, j] = _minmod(u[i, j] - u[i - 1, j], u[i + 1, j] - u[i, j])
                sxv[i, j] = _minmod(v[i, j] - v[i - 1, j], v[i + 1, j] - v[i, j])
            if j > 0 and j < ny - 1 and (not sol[i, j - 1]) and (not sol[i, j + 1]):
                syh[i, j] = _minmod(h[i, j] - h[i, j - 1], h[i, j + 1] - h[i, j])
                syu[i, j] = _minmod(u[i, j] - u[i, j - 1], u[i, j + 1] - u[i, j])
                syv[i, j] = _minmod(v[i, j] - v[i, j - 1], v[i, j + 1] - v[i, j])
    # --- flujos en caras normales a s ---
    for i in prange(nx + 1):
        for j in range(ny):
            f0 = 0.0
            f1 = 0.0
            f2 = 0.0
            if i == 0:
                if not sol[0, j]:
                    f0, f1, f2 = _hll(hin[j], uin[j], vin[j], h[0, j], u[0, j], v[0, j], gef[0])
            elif i == nx:
                if not sol[nx - 1, j]:
                    f0, f1, f2 = _hll(h[nx - 1, j], u[nx - 1, j], v[nx - 1, j],
                                      h[nx - 1, j], u[nx - 1, j], v[nx - 1, j], gef[nx - 1])
            else:
                L = i - 1
                g = 0.5 * (gef[L] + gef[i])
                if sol[L, j] and sol[i, j]:
                    pass
                elif sol[i, j]:
                    hl = h[L, j] + 0.5 * sxh[L, j]
                    ul = u[L, j] + 0.5 * sxu[L, j]
                    vl = v[L, j] + 0.5 * sxv[L, j]
                    f0, f1, f2 = _hll(hl, ul, vl, hl, -ul, vl, g)
                elif sol[L, j]:
                    hr = h[i, j] - 0.5 * sxh[i, j]
                    ur = u[i, j] - 0.5 * sxu[i, j]
                    vr = v[i, j] - 0.5 * sxv[i, j]
                    f0, f1, f2 = _hll(hr, -ur, vr, hr, ur, vr, g)
                else:
                    f0, f1, f2 = _hll(h[L, j] + 0.5 * sxh[L, j], u[L, j] + 0.5 * sxu[L, j], v[L, j] + 0.5 * sxv[L, j],
                                      h[i, j] - 0.5 * sxh[i, j], u[i, j] - 0.5 * sxu[i, j], v[i, j] - 0.5 * sxv[i, j], g)
            F0[i, j] = f0
            F1[i, j] = f1
            F2[i, j] = f2
    # --- flujos en caras normales a y (el papel de u y v se intercambia) ---
    for i in prange(nx):
        g = gef[i]
        for j in range(ny + 1):
            f0 = 0.0
            f1 = 0.0
            f2 = 0.0
            if j == 0:
                if not sol[i, 0]:
                    hr = h[i, 0] - 0.5 * syh[i, 0]
                    ur = u[i, 0] - 0.5 * syu[i, 0]
                    vr = v[i, 0] - 0.5 * syv[i, 0]
                    f0, f1, f2 = _hll(hr, -vr, ur, hr, vr, ur, g)
            elif j == ny:
                if not sol[i, ny - 1]:
                    hl = h[i, ny - 1] + 0.5 * syh[i, ny - 1]
                    ul = u[i, ny - 1] + 0.5 * syu[i, ny - 1]
                    vl = v[i, ny - 1] + 0.5 * syv[i, ny - 1]
                    f0, f1, f2 = _hll(hl, vl, ul, hl, -vl, ul, g)
            else:
                L = j - 1
                if sol[i, L] and sol[i, j]:
                    pass
                elif sol[i, j]:
                    hl = h[i, L] + 0.5 * syh[i, L]
                    ul = u[i, L] + 0.5 * syu[i, L]
                    vl = v[i, L] + 0.5 * syv[i, L]
                    f0, f1, f2 = _hll(hl, vl, ul, hl, -vl, ul, g)
                elif sol[i, L]:
                    hr = h[i, j] - 0.5 * syh[i, j]
                    ur = u[i, j] - 0.5 * syu[i, j]
                    vr = v[i, j] - 0.5 * syv[i, j]
                    f0, f1, f2 = _hll(hr, -vr, ur, hr, vr, ur, g)
                else:
                    f0, f1, f2 = _hll(h[i, L] + 0.5 * syh[i, L], v[i, L] + 0.5 * syv[i, L], u[i, L] + 0.5 * syu[i, L],
                                      h[i, j] - 0.5 * syh[i, j], v[i, j] - 0.5 * syv[i, j], u[i, j] - 0.5 * syu[i, j], g)
            G0[i, j] = f0            # masa
            G2[i, j] = f1            # cantidad de movimiento normal (hv)
            G1[i, j] = f2            # cantidad de movimiento tangencial (hu)
    # --- actualizacion ---
    for i in prange(nx):
        for j in range(ny):
            if sol[i, j]:
                dh[i, j] = 0.0
                dhu[i, j] = 0.0
                dhv[i, j] = 0.0
            else:
                hh = h[i, j]
                dh[i, j] = -(F0[i + 1, j] - F0[i, j]) / dx - (G0[i, j + 1] - G0[i, j]) / dy
                dhu[i, j] = (-(F1[i + 1, j] - F1[i, j]) / dx - (G1[i, j + 1] - G1[i, j]) / dy
                             + hh * gsin[i] - 0.5 * hh * hh * dgef[i])
                dhv[i, j] = -(F2[i + 1, j] - F2[i, j]) / dx - (G2[i, j + 1] - G2[i, j]) / dy
                if kdren[i] > 0.0:
                    # drenaje por la malla: velocidad de paso kd*sqrt(2 g h); el agua sale con la velocidad local
                    dr = kdren[i] * math.sqrt(2.0 * gef[i] * hh)
                    dh[i, j] -= dr
                    dhu[i, j] -= dr * u[i, j]
                    dhv[i, j] -= dr * v[i, j]


@njit(cache=True, parallel=True, fastmath=True)
def _primitivas(h, hu, hv, sol, u, v):
    nx, ny = h.shape
    for i in prange(nx):
        for j in range(ny):
            if sol[i, j]:
                u[i, j] = 0.0
                v[i, j] = 0.0
            else:
                hh = max(h[i, j], HMIN)
                u[i, j] = hu[i, j] / hh
                v[i, j] = hv[i, j] / hh


@njit(cache=True, parallel=True, fastmath=True)
def _dt_cfl(h, u, v, sol, gef, dx, dy, cfl):
    nx, ny = h.shape
    m = np.zeros(nx)
    for i in prange(nx):
        mm = 0.0
        for j in range(ny):
            if not sol[i, j]:
                c = math.sqrt(gef[i] * max(h[i, j], HMIN))
                a = (abs(u[i, j]) + c) / dx + (abs(v[i, j]) + c) / dy
                if a > mm:
                    mm = a
        m[i] = mm
    return cfl / m.max()


@njit(cache=True, parallel=True, fastmath=True)
def _friccion(h, hu, hv, sol, dt, n):
    nx, ny = h.shape
    for i in prange(nx):
        for j in range(ny):
            if not sol[i, j]:
                hh = max(h[i, j], HMIN)
                uu = hu[i, j] / hh
                vv = hv[i, j] / hh
                fac = 1.0 / (1.0 + dt * G * n * n * math.sqrt(uu * uu + vv * vv) / hh ** (4.0 / 3.0))
                hu[i, j] *= fac
                hv[i, j] *= fac


@njit(cache=True, fastmath=True)
def correr(h, hu, hv, sol, gef, dgef, gsin, dx, dy, t_fin, t_prom, cfl, n_man,
           h_in0, u_in0, pert_a, pert_f, sondas_i, sondas_j, dt_sonda, kdren, fq, modo_fq):
    """Avanza hasta t_fin. Devuelve promedios temporales (desde t_prom), series en sondas y el tiempo final."""
    nx, ny = h.shape
    u = np.zeros((nx, ny))
    v = np.zeros((nx, ny))
    h1 = np.zeros((nx, ny))
    hu1 = np.zeros((nx, ny))
    hv1 = np.zeros((nx, ny))
    dh = np.zeros((nx, ny))
    dhu = np.zeros((nx, ny))
    dhv = np.zeros((nx, ny))
    sxh = np.zeros((nx, ny))
    sxu = np.zeros((nx, ny))
    sxv = np.zeros((nx, ny))
    syh = np.zeros((nx, ny))
    syu = np.zeros((nx, ny))
    syv = np.zeros((nx, ny))
    F0 = np.zeros((nx + 1, ny))
    F1 = np.zeros((nx + 1, ny))
    F2 = np.zeros((nx + 1, ny))
    G0 = np.zeros((nx, ny + 1))
    G1 = np.zeros((nx, ny + 1))
    G2 = np.zeros((nx, ny + 1))
    hin = np.zeros(ny)
    uin = np.zeros(ny)
    vin = np.zeros(ny)
    h_m = np.zeros((nx, ny))
    hu_m = np.zeros((nx, ny))
    hv_m = np.zeros((nx, ny))
    h2_m = np.zeros((nx, ny))
    n_s = len(sondas_i)
    max_muestras = int((t_fin) / dt_sonda) + 2
    serie = np.zeros((max_muestras, n_s + 1))
    k_serie = 0
    t_sonda = 0.0
    t = 0.0
    w_tot = 0.0
    while t < t_fin:
        qf = 1.0 + pert_a * math.sin(2.0 * math.pi * pert_f * t)
        for j in range(ny):
            if not sol[0, j]:
                if modo_fq == 0:
                    qj = qf * fq[j]              # caudal unitario local relativo (entrada critica en cada j)
                    hin[j] = h_in0 * qj ** (2.0 / 3.0)
                    uin[j] = u_in0 * qj ** (1.0 / 3.0)
                else:
                    hin[j] = h_in0 * qf ** (2.0 / 3.0)          # entrada lenta: nivel plano, la velocidad se reparte
                    uin[j] = u_in0 * qf ** (1.0 / 3.0) * fq[j]
        _primitivas(h, hu, hv, sol, u, v)
        dt = _dt_cfl(h, u, v, sol, gef, dx, dy, cfl)
        if t + dt > t_fin:
            dt = t_fin - t
        # Runge-Kutta 2 (Heun)
        _rhs(h, u, v, sol, gef, dgef, gsin, dx, dy, hin, uin, vin, dh, dhu, dhv,
             sxh, sxu, sxv, syh, syu, syv, F0, F1, F2, G0, G1, G2, kdren)
        for i in range(nx):
            for j in range(ny):
                if sol[i, j]:
                    h1[i, j] = h[i, j]
                    hu1[i, j] = 0.0
                    hv1[i, j] = 0.0
                else:
                    h1[i, j] = max(h[i, j] + dt * dh[i, j], HMIN)
                    hu1[i, j] = hu[i, j] + dt * dhu[i, j]
                    hv1[i, j] = hv[i, j] + dt * dhv[i, j]
        _primitivas(h1, hu1, hv1, sol, u, v)
        _rhs(h1, u, v, sol, gef, dgef, gsin, dx, dy, hin, uin, vin, dh, dhu, dhv,
             sxh, sxu, sxv, syh, syu, syv, F0, F1, F2, G0, G1, G2, kdren)
        for i in range(nx):
            for j in range(ny):
                if not sol[i, j]:
                    h[i, j] = max(0.5 * (h[i, j] + h1[i, j] + dt * dh[i, j]), HMIN)
                    hu[i, j] = 0.5 * (hu[i, j] + hu1[i, j] + dt * dhu[i, j])
                    hv[i, j] = 0.5 * (hv[i, j] + hv1[i, j] + dt * dhv[i, j])
        _friccion(h, hu, hv, sol, dt, n_man)
        t += dt
        if t >= t_prom:
            for i in range(nx):
                for j in range(ny):
                    h_m[i, j] += h[i, j] * dt
                    hu_m[i, j] += hu[i, j] * dt
                    hv_m[i, j] += hv[i, j] * dt
                    h2_m[i, j] += h[i, j] * h[i, j] * dt
            w_tot += dt
        if t >= t_sonda and k_serie < max_muestras:
            serie[k_serie, 0] = t
            for k in range(n_s):
                serie[k_serie, k + 1] = h[sondas_i[k], sondas_j[k]]
            k_serie += 1
            t_sonda += dt_sonda
    if w_tot > 0.0:
        h_m /= w_tot
        hu_m /= w_tot
        hv_m /= w_tot
        h2_m /= w_tot
    return h_m, hu_m, hv_m, h2_m, serie[:k_serie], t


class Caso:
    """Malla y condiciones del canal para el solver."""

    def __init__(self, c, P, dx=2e-3, forma_ancho=None, ancho_dominio=None, inicio='perfil1d', kd=0.0):
        self.c, self.dx, self.dy = c, dx, dx
        B = c.ancho0 if ancho_dominio is None else ancho_dominio
        self.nx = int(round(c.L / dx))
        self.ny = int(round(B / dx))
        self.s = (np.arange(self.nx) + 0.5) * dx
        self.y = -B / 2 + (np.arange(self.ny) + 0.5) * dx
        b = c.ancho(self.s, forma_ancho)
        self.sol = np.abs(self.y)[None, :] > (b[:, None] / 2 + 1e-12)
        th = c.theta(self.s)
        self.gsin = G * np.sin(th)
        self.gef = G * np.cos(th)
        self.dgef = np.gradient(self.gef, self.s)
        # estado inicial: perfil 1D a lo ancho de cada seccion
        h1 = np.interp(self.s, P['s'], P['h'])
        u1 = np.interp(self.s, P['s'], P['V'])
        self.h = np.where(self.sol, h1[:, None], h1[:, None]).copy()
        self.hu = np.where(self.sol, 0.0, (h1 * u1)[:, None] * np.ones((1, self.ny)))
        self.hv = np.zeros((self.nx, self.ny))
        if inicio == 'profundo':          # arranque distinto: canal lleno de agua lenta (comprueba que no hay histeresis)
            self.h = np.full((self.nx, self.ny), 0.04)
            self.hu = np.where(self.sol, 0.0, 0.04 * 0.25)
        self.h_in0, self.u_in0 = P['h'][0], P['V'][0]
        self.b = b
        self.kdren = np.where(self.s < c.s_malla, kd, 0.0)      # la malla drena solo hasta su borde inferior

    def ejecutar(self, t_fin, t_prom, cfl=0.4, pert_a=0.0, pert_f=0.0, sondas=(), dt_sonda=1e-3, fq=None):
        si = np.array([np.searchsorted(self.s, s) for s, _ in sondas], np.int64) if sondas else np.zeros(0, np.int64)
        sj = np.array([np.searchsorted(self.y, y) for _, y in sondas], np.int64) if sondas else np.zeros(0, np.int64)
        fq = np.ones(self.ny) if fq is None else np.asarray(fq, float)
        h_m, hu_m, hv_m, h2_m, serie, t = correr(
            self.h, self.hu, self.hv, self.sol, self.gef, self.dgef, self.gsin, self.dx, self.dy, t_fin, t_prom,
            cfl, self.c.n_manning, self.h_in0, self.u_in0, pert_a, pert_f, si, sj, dt_sonda, self.kdren, fq, 0)
        self.h_m, self.u_m, self.v_m = h_m, np.where(h_m > 0, hu_m / np.maximum(h_m, 1e-9), 0.0), \
            np.where(h_m > 0, hv_m / np.maximum(h_m, 1e-9), 0.0)
        self.h_rms = np.sqrt(np.maximum(h2_m - h_m ** 2, 0.0))
        self.serie = serie
        self.t = t
        return self
