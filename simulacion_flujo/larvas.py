# -*- coding: utf-8 -*-
"""Seguimiento de larvas como trazadores pasivos sobre el campo 2D promediado y estadistica de solapamiento
en la linea de conteo.

Cada larva: se suelta en la cresta con probabilidad proporcional al caudal local (la concentracion de larvas en el
agua es uniforme), avanza con la velocidad del agua por un factor 'kf' (esta cerca del fondo, donde el agua va mas
lenta que el promedio) y se dispersa lateralmente por turbulencia: D_y = 0,15 h u*.
Solapamiento: dos larvas se solapan en la imagen de la camara lineal si sus huellas (largo x ancho) se cruzan.
"""
import math
import numpy as np
from numba import njit
from scipy.ndimage import distance_transform_edt, map_coordinates

G = 9.81


def _rellenar(campo, sol):
    """Sustituye las celdas solidas por el valor fluido mas cercano (para interpolar cerca de las paredes)."""
    idx = distance_transform_edt(sol, return_distances=False, return_indices=True)
    return campo[tuple(idx)]


def seguir(caso, n=6000, kf=(0.75, 1.0), seed=1, dt=1e-3, s_fin=None, n_manning=0.010, s_ini=0.0):
    """Suelta larvas en s_ini (por defecto la cresta) y las sigue hasta s_fin (por defecto la linea de conteo).
    Devuelve dict con y de salida, tiempo de transito, velocidad de la larva al cruzar s_fin, y_inicial."""
    rng = np.random.default_rng(seed)
    c = caso.c
    s_fin = c.s_conteo if s_fin is None else s_fin
    dx = caso.dx
    sol = caso.sol
    s0 = caso.s[0] - 0.5 * dx                # borde izquierdo del dominio (no siempre es la cresta)
    u = _rellenar(caso.u_m, sol)
    v = _rellenar(caso.v_m, sol)
    h = _rellenar(caso.h_m, sol)
    # caudal unitario en la entrada (primera columna libre)
    i_ini = int(np.searchsorted(caso.s, s_ini))
    q0 = (caso.h_m[i_ini] * caso.u_m[i_ini]) * (~sol[i_ini])
    p = q0 / q0.sum()
    y0 = rng.choice(caso.y, size=n, p=p) + rng.uniform(-0.5, 0.5, n) * caso.dy
    s = np.full(n, caso.s[i_ini])
    y = y0.copy()
    fk = rng.uniform(kf[0], kf[1], n)
    t = np.zeros(n)
    vivo = np.ones(n, bool)
    y_sal = np.full(n, np.nan)
    v_sal = np.full(n, np.nan)
    t_sal = np.full(n, np.nan)
    ymax = caso.y[-1] + 0.5 * caso.dy
    for _ in range(4000):
        if not vivo.any():
            break
        i = ((s[vivo] - s0) / dx) - 0.5
        j = (y[vivo] - caso.y[0]) / caso.dy
        co = np.vstack([i, j])
        uu = map_coordinates(u, co, order=1, mode='nearest') * fk[vivo]
        vv = map_coordinates(v, co, order=1, mode='nearest') * fk[vivo]
        hh = map_coordinates(h, co, order=1, mode='nearest')
        ust = np.sqrt(G) * n_manning * np.hypot(uu, vv) / np.maximum(hh, 1e-4) ** (1 / 6)
        Dy = 0.15 * hh * ust
        ynew = y[vivo] + vv * dt + np.sqrt(2 * Dy * dt) * rng.standard_normal(vivo.sum())
        snew = s[vivo] + uu * dt
        # paredes: si cae en celda solida, se queda donde estaba (rebote)
        jn = np.clip(np.round((ynew - caso.y[0]) / caso.dy).astype(int), 0, caso.ny - 1)
        inew = np.clip(np.round((snew - s0) / dx - 0.5).astype(int), 0, caso.nx - 1)
        choque = sol[inew, jn]
        ynew = np.where(choque, y[vivo], ynew)
        idx = np.where(vivo)[0]
        y[idx] = ynew
        s[idx] = snew
        t[idx] += dt
        sale = snew >= s_fin
        if sale.any():
            k = idx[sale]
            y_sal[k] = y[k]
            v_sal[k] = uu[sale]
            t_sal[k] = t[k]
            vivo[k] = False
    return {'y0': y0, 'y': y_sal, 'u': v_sal, 't': t_sal, 'kf': fk}


@njit(cache=True)
def _sat(ax, ay, bx, by):
    """Solapamiento de dos poligonos convexos de 4 vertices (teorema del eje separador)."""
    for p in range(2):
        px, py = (ax, ay) if p == 0 else (bx, by)
        for k in range(4):
            ex = px[(k + 1) % 4] - px[k]
            ey = py[(k + 1) % 4] - py[k]
            nx, ny = -ey, ex
            amin = amax = ax[0] * nx + ay[0] * ny
            bmin = bmax = bx[0] * nx + by[0] * ny
            for m in range(1, 4):
                da = ax[m] * nx + ay[m] * ny
                db = bx[m] * nx + by[m] * ny
                amin = min(amin, da); amax = max(amax, da)
                bmin = min(bmin, db); bmax = max(bmax, db)
            if amax < bmin or bmax < amin:
                return False
    return True


@njit(cache=True)
def _pares(X, Y, ang, est, L, w, ventana):
    """Cuenta larvas solapadas y pares. Huella en la imagen: rectangulo LxW girado 'ang' y estirado 'est' a lo largo
    del flujo (la camara lineal muestrea a tiempo fijo: una larva mas lenta se ve mas larga)."""
    N = len(X)
    sol = np.zeros(N, np.bool_)
    pares = 0
    cx = np.array([-0.5, 0.5, 0.5, -0.5]) * L
    cy = np.array([-0.5, -0.5, 0.5, 0.5]) * w
    ax = np.zeros(4); ay = np.zeros(4); bx = np.zeros(4); by = np.zeros(4)
    for i in range(N):
        ci, si = math.cos(ang[i]), math.sin(ang[i])
        for k in range(4):
            ax[k] = X[i] + (cx[k] * ci - cy[k] * si) * est[i]
            ay[k] = Y[i] + (cx[k] * si + cy[k] * ci)
        j = i + 1
        while j < N and X[j] - X[i] < ventana:
            if abs(Y[j] - Y[i]) < ventana:
                cj, sj = math.cos(ang[j]), math.sin(ang[j])
                for k in range(4):
                    bx[k] = X[j] + (cx[k] * cj - cy[k] * sj) * est[j]
                    by[k] = Y[j] + (cx[k] * sj + cy[k] * cj)
                if _sat(ax, ay, bx, by):
                    sol[i] = True
                    sol[j] = True
                    pares += 1
            j += 1
    return sol, pares


def solapamiento(tr, tasa, largo=10e-3, ancho=1.5e-3, T=60.0, seed=2, orient='aleatoria', sd_giro_deg=15.0):
    """Proceso de Poisson de llegadas 'tasa' (larvas/s). Devuelve (fraccion de larvas que se solapan con otra,
    fraccion de conteo perdido = pares fusionados / total, N).

    orient: 'aleatoria' (angulo uniforme respecto al flujo: peor caso) o 'alineada' (con el flujo, +-sd_giro)."""
    rng = np.random.default_rng(seed)
    ok = np.isfinite(tr['y'])
    N = rng.poisson(tasa * T)
    k = rng.integers(0, ok.sum(), N)
    y = tr['y'][ok][k]
    u = tr['u'][ok][k]
    tt = rng.uniform(0, T, N) + tr['t'][ok][k]
    u_ref = float(np.median(tr['u'][ok]))
    order = np.argsort(tt)
    tt, y, u = tt[order], y[order], u[order]
    ang = rng.uniform(0, np.pi, N) if orient == 'aleatoria' else np.radians(sd_giro_deg) * rng.standard_normal(N)
    X = u_ref * tt                                    # coordenada en la imagen a lo largo del flujo (m)
    est = u_ref / u
    sol, pares = _pares(X, y, ang, est, largo, ancho, 0.05)
    return sol.mean(), pares / max(N, 1), N
