# -*- coding: utf-8 -*-
"""Datos del diagrama de flujo: perfil 1D del canal, lineas de corriente del CFD y planta del cajon.
Escribe diagrama_flujo/data.json (milimetros y segundos). Se corre con el entorno que tiene numpy, scipy y numba:
    python datos.py
"""
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, '..')
sys.path.insert(0, os.path.join(RAIZ, 'simulacion_flujo'))
sys.path.insert(0, os.path.join(RAIZ, 'cfd_3d', 'scripts'))
from geometria_canal import cargar_canal, _cargar_script, SCRIPT_FUSION  # noqa: E402
from flujo_1d import perfil_estacionario  # noqa: E402
from analizar_3d import cargar  # noqa: E402

rng = np.random.default_rng(7)
salida = {}

# ---------------- perfil 1D por caudal (Manning n = 0,008, el equivalente que calibro el CFD) ----------------
c, _m, _g = cargar_canal()
s_geo = np.arange(0.0, c.L + 1e-9, 0.005)
th = c.theta(s_geo)
xh = np.concatenate([[0.0], np.cumsum(np.cos(0.5 * (th[1:] + th[:-1])) * np.diff(s_geo))])
zz = c.cota(s_geo)
salida['canal'] = {
    's': [round(v * 1e3, 1) for v in s_geo[::2]], 'x': [round(v * 1e3, 1) for v in xh[::2]],
    'z': [round(v * 1e3, 1) for v in zz[::2]], 'theta': [round(math.degrees(v), 2) for v in th[::2]],
    'b': [round(float(v) * 1e3, 1) for v in c.ancho(s_geo[::2])],
    's_malla': c.s_malla * 1e3, 's_arco0': c.s_arco0 * 1e3, 's_arco1': c.s_arco1 * 1e3, 's_conteo': c.s_conteo * 1e3,
    'L': c.L * 1e3, 'radio': c.radio * 1e3, 'ancho1': c.ancho1 * 1e3,
}
i_cont = int(np.searchsorted(s_geo, c.s_conteo))
salida['canal']['x_conteo'] = round(float(xh[i_cont]) * 1e3, 1)
salida['canal']['z_conteo'] = round(float(zz[i_cont]) * 1e3, 1)
perfiles = {}
for Q in (4, 6, 8, 10, 12, 15):
    P = perfil_estacionario(c, Q=Q * 1e-3, n=0.008)
    idx = np.arange(0, len(P['s']), 20)
    perfiles[str(Q)] = {
        's': [round(float(P['s'][k]) * 1e3, 1) for k in idx],
        'h': [round(float(P['h'][k]) * 1e3, 2) for k in idx],
        'V': [round(float(P['V'][k]), 3) for k in idx],
        'Fr': [round(float(P['Fr'][k]), 2) for k in idx],
    }
    k = min(np.searchsorted(P['s'], c.s_conteo), len(P['s']) - 1)
    print('Q %2d L/s | conteo h = %.2f mm V = %.2f m/s Fr = %.1f' % (Q, P['h'][k] * 1e3, P['V'][k], P['Fr'][k]))
salida['perfil1d'] = perfiles

# ---------------- planta del cajon (semiancho y >= 0) ----------------
m, g = _cargar_script(SCRIPT_FUSION)
XV = m.X_VERTEDERO
dentro = m.curva_estrechamiento()
salida['planta'] = {
    'estrech': [[round(XV - X, 1), round(y, 1)] for X, y in dentro],
    'x_chaflan': XV - m.X_CHAFLAN, 'x_fondo': XV - m.LARGO_TOTAL, 'semi_cuerpo': m.ANCHO_CUERPO / 2.0,
    'semi_frente': m.ANCHO_FRENTE / 2.0, 'semi_canal': m.ANCHO_CANAL / 2.0, 'x_deflector': XV - m.X_DEFLECTOR,
    'x_entrada': XV - m.X_ENTRADA, 'x_drenaje': XV - m.X_DRENAJE, 'alto_cajon': m.ALTO_CAJON, 'alto_cresta': m.ALTO_VERTEDERO,
}

# ---------------- lineas de corriente del campo medio ----------------
CASOS = [
    ('original', 'p2_medio_grueso'),
    ('circular', 'p2_rampa_sinlabio'),
    ('parabola', 'p2_rampa_parabola_t4'),
]
cfd = {}
for clave, caso in CASOS:
    t, aM, UM, C, V = cargar(caso)
    ok = aM > 0.5
    Pw, Uw = C[ok], UM[ok]
    arbol = cKDTree(Pw)

    def vel(p):
        d, j = arbol.query(p, k=4)
        w = 1.0 / (d + 1e-6)
        w /= w.sum()
        return (Uw[j] * w[:, None]).sum(0), d.min()

    # semillas: disco dentro del tubo de entrada, z = -0,03 m, radio 0,10 m, semiancho (y >= 0)
    sem = []
    while len(sem) < 130:
        r = 0.10 * math.sqrt(rng.random())
        a = math.pi * rng.random()
        sem.append((-0.582 + r * math.cos(a), r * math.sin(a), -0.03))
    lineas = []
    for p0 in sem:
        p = np.array(p0, float)
        ruta = [(p[0], p[1], p[2], 0.0)]
        tt = 0.0
        ultimo = p.copy()
        for _ in range(9000):
            v, dm = vel(p)
            sp = float(np.linalg.norm(v))
            if dm > 0.022 or sp < 1e-3:
                break
            h = min(0.003, 0.003 * max(sp, 0.05) / sp) if sp > 0 else 0.003
            v2, dm2 = vel(p + 0.5 * h * v / sp)
            sp2 = float(np.linalg.norm(v2))
            if sp2 < 1e-3:
                break
            paso = h * v2 / sp2
            p = p + paso
            tt += h / sp2
            if np.linalg.norm(p - ultimo) >= 0.010:
                ruta.append((p[0], p[1], p[2], tt))
                ultimo = p.copy()
            if p[0] > 0.52 or tt > 40:
                break
        llega = ruta[-1][0] > 0.20
        if llega and len(ruta) > 8:
            lineas.append([[round(a * 1e3, 1), round(b * 1e3, 1), round(cz * 1e3, 1), round(d, 3)] for a, b, cz, d in ruta])

    # trayectorias sembradas en la esquina de la cresta (x -70..-5 mm, z 3..35 mm, cerca del plano central): muestran el remolino
    esq = []
    for _ in range(60):
        p = np.array([-0.005 - 0.065 * rng.random(), 0.09 + 0.02 * rng.random(), 0.003 + 0.032 * rng.random()])
        ruta = [(p[0], p[1], p[2], 0.0)]
        tt = 0.0
        ultimo = p.copy()
        for _ in range(7000):
            v, dm = vel(p)
            sp = float(np.linalg.norm(v))
            if dm > 0.022 or sp < 1e-3:
                break
            h = 0.002
            v2, dm2 = vel(p + 0.5 * h * v / sp)
            sp2 = float(np.linalg.norm(v2))
            if sp2 < 1e-3:
                break
            p = p + h * v2 / sp2
            tt += h / sp2
            if np.linalg.norm(p - ultimo) >= 0.006:
                ruta.append((p[0], p[1], p[2], tt))
                ultimo = p.copy()
            if p[0] > 0.12 or tt > 14:
                break
        if tt >= 1.2 and len(ruta) > 10:
            esq.append([[round(a * 1e3, 1), round(b * 1e3, 1), round(cz * 1e3, 1), round(d, 3)] for a, b, cz, d in ruta])
    atrapadas = sum(1 for l in esq if l[-1][0] < 100)
    print('  esquina: %d trayectorias, %d siguen en la zona al final (%.0f%%)' % (len(esq), atrapadas, 100 * atrapadas / max(1, len(esq))))
    tiempos = [l[-1][3] for l in lineas]
    print('%s: %d lineas llegan a la lamina, tiempo mediana %.1f s (p10 %.1f, p90 %.1f)' % (
        clave, len(lineas), np.median(tiempos), np.percentile(tiempos, 10), np.percentile(tiempos, 90)))
    # nivel libre en el plano central (y = 0,10 +- 0,02): cruce de alpha = 0,5 por columnas de x
    niv = []
    for x0 in np.arange(-0.74, 0.535, 0.02):
        w = (np.abs(C[:, 0] - x0) < 0.006) & (np.abs(C[:, 1] - 0.10) < 0.02)
        z = C[w, 2]
        a = aM[w]
        o = np.argsort(z)
        z, a = z[o], a[o]
        k = np.where(a >= 0.5)[0]
        if not len(k):
            niv.append(None)
            continue
        k = k[-1]
        zz_ = z[k] + (a[k] - 0.5) / max(a[k] - (a[k + 1] if k + 1 < len(z) else 0.0), 1e-9) * ((z[k + 1] - z[k]) if k + 1 < len(z) else 0.0)
        niv.append([round(x0 * 1e3, 0), round(float(zz_) * 1e3, 1)])
    cfd[clave] = {'caso': caso, 'lineas': lineas, 'esquina': esq, 'nivel': [v for v in niv if v is not None]}
salida['cfd'] = cfd

with open(os.path.join(AQUI, 'data.json'), 'w', encoding='utf8') as f:
    json.dump(salida, f, separators=(',', ':'), ensure_ascii=False)
print('data.json: %.0f kB' % (os.path.getsize(os.path.join(AQUI, 'data.json')) / 1e3))
