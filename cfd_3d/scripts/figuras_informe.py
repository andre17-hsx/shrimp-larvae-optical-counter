# -*- coding: utf-8 -*-
"""Graficas del informe preliminar (fondo blanco; se muestran sobre una lamina clara en la pagina).

    python figuras_informe.py [--caso p2_medio_grueso] [--log4mm ruta_log_interFoam_mm4]
Escribe en cfd_3d/informe_preliminar/img/. Requiere numpy, scipy, matplotlib y Pillow (entorno simenv).
"""
import argparse
import math
import os
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', '..', 'simulacion_flujo'))
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from analizar_3d import cargar, RES  # noqa: E402
from analizar_criterios import reparto, perfil_1d, s_de_x  # noqa: E402

IMG = os.path.join(AQUI, '..', 'informe_preliminar', 'img')
os.makedirs(IMG, exist_ok=True)
# paleta serena (sin rojos ni naranjas); los nombres AMBER y RED se conservan por compatibilidad: ahora son azul e indigo
TEAL, AMBER, RED, SLATE, GREEN, GRID = '#0B7A8C', '#2F62A3', '#5B57A6', '#33485A', '#2C7A4B', '#D5DEE5'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.edgecolor': SLATE, 'axes.labelcolor': SLATE,
                     'xtick.color': SLATE, 'ytick.color': SLATE, 'text.color': SLATE, 'axes.grid': True, 'grid.color': GRID,
                     'grid.linewidth': 0.8, 'axes.spines.top': False, 'axes.spines.right': False})
TH = math.atan(0.2127659574468085)


def fig_espesor_caudal():
    from geometria_canal import cargar_canal
    from flujo_1d import perfil_estacionario, calibrar_kd
    from contracciones import ancho_fijo
    c, m, g = cargar_canal(10.0, 0.010)
    f = ancho_fijo(c)
    j = int(np.searchsorted(np.linspace(0, c.L, int(round(c.L / 5e-4)) + 1), c.s_conteo))
    Qs = np.array([4.0, 6.0, 8.0, 10.0, 12.0, 15.0])      # calibrar_kd no converge para todos los caudales enteros
    res = {}
    for fr in (0.0, 0.15, 0.30):
        for n in (0.010, 0.008):
            h = []
            for Q in Qs:
                kd = 0.0 if fr == 0 else calibrar_kd(c, fr, forma_ancho=f, Q=Q / 1000.0)
                P = perfil_estacionario(c, Q=Q / 1000.0, forma_ancho=f, n=n, kd=kd)
                h.append(P['h'][j] * 1e3)
            res[(fr, n)] = np.array(h)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.axvspan(6, 12, color=TEAL, alpha=0.07, lw=0)
    ax.text(9, 15.3, 'rango de trabajo 6–12 L/s', ha='center', va='top', color=TEAL, fontsize=10)
    for fr, col, lab in ((0.0, TEAL, 'sin drenaje'), (0.15, AMBER, 'malla drena 15 %'), (0.30, RED, 'malla drena 30 %')):
        a, b = res[(fr, 0.010)], res[(fr, 0.008)]
        ax.fill_between(Qs, b, a, color=col, alpha=0.25, lw=0)
        ax.plot(Qs, 0.5 * (a + b), color=col, lw=2, marker='o', ms=4)
        ax.text(Qs[-1] + 0.15, 0.5 * (a[-1] + b[-1]), lab, color=col, va='center', fontsize=10)
    ax.axhline(5, color=SLATE, lw=1.4, ls='--')
    ax.text(12.4, 5.25, 'mínimo 5 mm (óptica del backlight)', color=SLATE, fontsize=10)
    ax.set_xlim(4, 17.6)
    ax.set_ylim(3, 15.5)
    ax.set_xlabel('caudal (L/s)')
    ax.set_ylabel('espesor de la lámina en la línea de conteo (mm)')
    fig.text(0.125, 0.005, 'Banda = de n de Manning 0,008 (arriba, más delgada) a 0,010; modelo 1D del canal del prototipo, sin CFD.',
             fontsize=8.5, color=SLATE)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(IMG, 'espesor_caudal.png'), dpi=150)
    plt.close(fig)
    return res


def analisis_cfd(caso):
    t, aM, UM, C, V = cargar(caso)
    s = V ** (1.0 / 3.0)
    dx = dy = 10e-3
    x0, x1, y1 = 0.0, 0.53, 0.26
    sel = (C[:, 0] > x0 - 0.01) & (C[:, 0] < x1 + 0.01) & (aM > 1e-4) & (s <= dx)
    hv = reparto(C[sel], s[sel], aM[sel] * V[sel], x0, x1, y1, dx, dy)
    qx = reparto(C[sel], s[sel], aM[sel] * UM[sel, 0] * V[sel], x0, x1, y1, dx, dy)
    return t, hv, qx, dx, dy, x0, x1, y1


def fig_cfd(caso):
    t, hv, qx, dx, dy, x0, x1, y1 = analisis_cfd(caso)
    xc = x0 + dx * (np.arange(hv.shape[0]) + 0.5)
    yc = dy * (np.arange(hv.shape[1]) + 0.5)
    cen = yc < 0.242
    P1, P8 = perfil_1d(0.010), perfil_1d(0.008)
    # --- comparacion con el 1D
    xs = np.array([0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50])
    Hm, Hlo, Hhi, Vm, Vlo, Vhi, cvh = [], [], [], [], [], [], []
    for xt in xs:
        i = int(round((xt - x0) / dx - 0.5))
        s1, th = s_de_x(P1, xt)
        h = hv[i - 1:i + 2].mean(axis=0)[cen] * math.cos(th)
        q = qx[i - 1:i + 2].mean(axis=0)[cen]
        v = q / h
        Hm.append(h.mean() * 1e3); Hlo.append(h.min() * 1e3); Hhi.append(h.max() * 1e3)
        Vm.append(v.mean()); Vlo.append(v.min()); Vhi.append(v.max()); cvh.append(100 * h.std() / h.mean())
    Hm, Hlo, Hhi, Vm, Vlo, Vhi = map(np.array, (Hm, Hlo, Hhi, Vm, Vlo, Vhi))
    sg = np.linspace(0.05, 0.53, 60)
    idx = [np.searchsorted(P1['s'], s_de_x(P1, x)[0]) for x in sg]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for k, (Pk, lab, col, ls) in enumerate(((P1, '1D, n = 0,010', SLATE, '-'), (P8, '1D, n = 0,008', AMBER, '--'))):
        ax[0].plot(sg, [Pk['h'][i] * 1e3 for i in idx], color=col, ls=ls, lw=2, label=lab)
        ax[1].plot(sg, [Pk['V'][i] for i in idx], color=col, ls=ls, lw=2, label=lab)
    ax[0].fill_between(xs, Hlo, Hhi, color=TEAL, alpha=0.22, lw=0, label='CFD 3D: mín–máx a lo ancho')
    ax[0].plot(xs, Hm, 'o-', color=TEAL, lw=2, ms=5, label='CFD 3D: media a lo ancho')
    ax[1].fill_between(xs, Vlo, Vhi, color=TEAL, alpha=0.22, lw=0)
    ax[1].plot(xs, Vm, 'o-', color=TEAL, lw=2, ms=5, label='CFD 3D')
    ax[0].set_ylabel('profundidad normal (mm)')
    ax[1].set_ylabel('velocidad de la lámina (m/s)')
    for a in ax:
        a.set_xlabel('distancia desde la cresta (m)')
    ax[0].legend(frameon=False, fontsize=9)
    ax[1].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, 'cfd_vs_1d.png'), dpi=150)
    plt.close(fig)
    # --- mapas y perfiles
    fig = plt.figure(figsize=(12.5, 7.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05], hspace=0.42, wspace=0.28)
    a1, a2, a3, a4 = (fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1]))
    hv = hv.copy(); qx = qx.copy()
    hv[:, yc > 0.248] = 0.0; qx[:, yc > 0.248] = 0.0        # banda parcial junto a la pared
    H = hv.T * math.cos(TH) * 1e3
    im = a1.imshow(np.where(hv.T > 5e-3, H, np.nan), origin='lower', extent=[x0, x1, 0, y1], vmin=8, vmax=22, aspect='equal', cmap='viridis')
    fig.colorbar(im, ax=a1, label='profundidad normal (mm)', fraction=0.046, pad=0.03)
    a1.set_title('Profundidad de la lámina (campo medio)', fontsize=11)
    Vm2 = np.where(hv > 5e-3, qx / np.maximum(hv * math.cos(TH), 1e-9), np.nan)
    im2 = a2.imshow(Vm2.T, origin='lower', extent=[x0, x1, 0, y1], vmin=0.8, vmax=1.8, aspect='equal', cmap='viridis')
    fig.colorbar(im2, ax=a2, label='velocidad (m/s)', fraction=0.046, pad=0.03)
    a2.set_title('Velocidad de la lámina', fontsize=11)
    for a in (a1, a2):
        a.set_xlabel('x desde la cresta (m)')
        a.set_ylabel('y desde el eje (m)')
        a.grid(False)
        a.axvline(0.282, color='white', lw=1, ls=':')
        a.text(0.284, 0.245, 'fin de la malla', color='white', fontsize=8, va='top')
    cols = [TEAL, '#4E8F3A', AMBER, RED, SLATE]
    for xt, col in zip((0.1, 0.2, 0.3, 0.4, 0.5), cols):
        i = int(round((xt - x0) / dx - 0.5))
        s1, th = s_de_x(P1, xt)
        h = hv[i - 1:i + 2].mean(axis=0)[cen] * math.cos(th)
        q = qx[i - 1:i + 2].mean(axis=0)[cen]
        a3.plot(yc[cen] * 1e3, h * 1e3, color=col, lw=2, label='x = %.1f m' % xt)
        a4.plot(yc[cen] * 1e3, q / h, color=col, lw=2, label='x = %.1f m' % xt)
    a3.set_xlabel('y desde el eje (mm)')
    a3.set_ylabel('profundidad normal (mm)')
    a3.set_title('Reparto a lo ancho: profundidad (ondas estacionarias de ±1,3 mm)', fontsize=10.5)
    a4.set_xlabel('y desde el eje (mm)')
    a4.set_ylabel('velocidad (m/s)')
    a4.set_title('Reparto a lo ancho: velocidad (mucho más pareja)', fontsize=10.5)
    a3.legend(frameon=False, fontsize=9, ncol=2)
    fig.savefig(os.path.join(IMG, 'mapas_lamina.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    return cvh, xs


def fig_cortes(caso, y0=0.10):
    """Cortes longitudinales del campo medio a y = y0: velocidad, vectores y contorno de las paredes."""
    from matplotlib.collections import PatchCollection, LineCollection
    from matplotlib.patches import Rectangle
    from matplotlib.colors import PowerNorm
    from stl_util import leer_stl, cortar_y
    t, aM, UM, C, V = cargar(caso)
    s = V ** (1.0 / 3.0)
    m = (np.abs(C[:, 1] - y0) <= s / 2) & (aM > 0.5)
    x, z, sz = C[m, 0], C[m, 2], s[m]
    U = UM[m]
    vel = np.linalg.norm(U, axis=1)
    stl = leer_stl(os.path.join(AQUI, '..', 'geometria', 'dominio_sinlabio.stl'))
    seg = np.concatenate([cortar_y(stl[k], y0) for k in ('paredes', 'malla') if len(stl[k])])
    for nombre, (xa, xb, za, zb), w, vmax, quiver, gam in (
            ('corte_completo.png', (-0.76, 0.55, -0.075, 0.215), 13.0, 2.0, False, 0.5),
            ('corte_cresta.png', (-0.30, 0.32, -0.012, 0.165), 12.0, 1.2, True, 0.6)):
        h = w * (zb - za) / (xb - xa) + 0.9
        fig, ax = plt.subplots(figsize=(w, h))
        sel = (x > xa - 0.01) & (x < xb + 0.01) & (z > za - 0.01) & (z < zb + 0.01)
        pc = PatchCollection([Rectangle((xi - si / 2, zi - si / 2), si, si) for xi, zi, si in zip(x[sel], z[sel], sz[sel])],
                             cmap='turbo', norm=PowerNorm(gam, vmin=0, vmax=vmax), linewidths=0.6, antialiased=False)
        pc.set_array(vel[sel])
        pc.set_edgecolor('face')
        ax.add_collection(pc)
        ax.add_collection(LineCollection(seg, colors=SLATE, linewidths=2.2))
        if quiver:
            g = 0.012
            ix = np.round(x[sel] / g).astype(int)
            iz = np.round(z[sel] / g).astype(int)
            _, first = np.unique(ix * 100000 + iz, return_index=True)
            xs_, zs_ = x[sel][first], z[sel][first]
            ax.quiver(xs_, zs_, U[sel][first, 0], U[sel][first, 2], color='white', scale=14, width=0.0017,
                      headwidth=4, headlength=4.5, alpha=0.9)
        if quiver:
            bb = dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85)
            ax.text(-0.245, 0.158, 'deflector (placa de 3 mm)', fontsize=9.5, color=SLATE, va='top', bbox=bb)
            ax.text(-0.29, -0.0065, 'fondo del cajón (z = 0)', fontsize=9.5, color=SLATE, va='center', bbox=bb)
            ar = dict(arrowstyle='-|>', color=SLATE, lw=1.0)
            ax.annotate('rampa curva de la cresta (R = 60 mm)', xy=(-0.017, 0.022), xytext=(0.03, 0.006), fontsize=9.5, color=SLATE, va='center', bbox=bb, arrowprops=ar)
            ax.annotate('sin labio', xy=(0.0, 0.06), xytext=(0.05, 0.145), fontsize=9.5, color=SLATE, va='center', bbox=bb, arrowprops=ar)
            ax.text(0.19, -0.004, 'malla a 12°', fontsize=9.5, color=SLATE, va='center', bbox=bb)
        ax.set_xlim(xa, xb)
        ax.set_ylim(za, zb)
        ax.set_aspect('equal')
        ax.grid(False)
        ax.set_xlabel('x desde la cresta (m)')
        ax.set_ylabel('z sobre el fondo del cajón (m)')
        cb = fig.colorbar(pc, ax=ax, fraction=0.025, pad=0.01)
        cb.set_label('velocidad media (m/s)')
        fig.savefig(os.path.join(IMG, nombre), dpi=140, bbox_inches='tight')
        plt.close(fig)


def fig_esquema(y0=0.003):
    """Esquema del corte longitudinal en el eje con cada componente rotulado (cotas del modelo de Fusion)."""
    from matplotlib.collections import LineCollection
    from stl_util import leer_stl, cortar_y
    stl = leer_stl(os.path.join(AQUI, '..', 'geometria', 'dominio_sinlabio.stl'))
    seg = np.concatenate([cortar_y(stl[k], y0) for k in ('paredes', 'malla') if len(stl[k])])
    fig, ax = plt.subplots(figsize=(14, 6.6))
    ax.add_collection(LineCollection(seg, colors=SLATE, linewidths=2.0))
    ax.fill_between([-0.744, -0.253], 0, 0.118, color=TEAL, alpha=0.10, lw=0)
    ax.fill_between([-0.25, -0.003], 0, 0.104, color=TEAL, alpha=0.10, lw=0)
    ax.plot([-0.744, -0.253], [0.118, 0.118], color=TEAL, lw=1.6, ls='--')
    ax.plot([-0.25, -0.003], [0.104, 0.104], color=TEAL, lw=1.6, ls='--')
    kw = dict(arrowprops=dict(arrowstyle='-|>', color=SLATE, lw=1.0), fontsize=10, color=SLATE, va='center')
    ax.annotate('Pared trasera (x = -744 mm)', xy=(-0.744, 0.26), xytext=(-0.70, 0.29), **kw)
    ax.annotate('Deflector: placa de 3 mm en X = 2340 (x = -250 mm),\nde z = 50 a 300 mm. Deja 50 mm libres abajo', xy=(-0.2515, 0.20),
                xytext=(-0.66, 0.225), **kw)
    ax.annotate('Nivel del agua atrás: ≈118 mm (cálculo)', xy=(-0.5, 0.118), xytext=(-0.66, 0.16), color=TEAL, fontsize=10, va='center',
                arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=1.0))
    ax.annotate('Nivel delante del deflector: ≈104 mm', xy=(-0.13, 0.104), xytext=(-0.24, 0.165), color=TEAL, fontsize=10, va='center',
                arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=1.0))
    ax.annotate('Fondo del cajón (z = 0)', xy=(-0.40, 0.0), xytext=(-0.44, -0.045), **kw)
    ax.annotate('Tubo de entrada del cono difusor\n(el agua sube por aquí; disco a z = -60 mm)', xy=(-0.58, -0.06), xytext=(-0.73, -0.095), **kw)
    ax.annotate('Rampa curva de la cresta:\ncuarto de círculo, R = 60 mm\n(z = 0 a 60 mm, en X = 2090)', xy=(-0.02, 0.014), xytext=(-0.26, -0.07), **kw)
    ax.annotate('Sin labio: la rampa\ntermina directo en la malla', xy=(0.0, 0.06), xytext=(-0.17, 0.215), **kw)
    ax.annotate('Malla de 30 mesh a 12°\n(x de 0 a 282 mm)', xy=(0.14, 0.03), xytext=(0.12, -0.075), **kw)
    ax.annotate('Tobogán a 12° hasta x = 533 mm\n(fin del dominio calculado)', xy=(0.42, -0.033), xytext=(0.30, -0.10), **kw)
    ax.annotate('Tapa sobre la lámina: baja a 45° y\nsigue paralela al tobogán', xy=(0.13, 0.2016), xytext=(0.20, 0.28), **kw)
    ax.set_xlim(-0.78, 0.56)
    ax.set_ylim(-0.115, 0.32)
    ax.set_aspect('equal')
    ax.grid(False)
    ax.set_xlabel('x medido desde la cresta, positivo aguas abajo (m)')
    ax.set_ylabel('z sobre el fondo del cajón (m)')
    ax.set_title('Corte longitudinal en el eje de la máquina, a 3 mm del plano de simetría (paredes de la geometría calculada)', fontsize=11, loc='left')
    fig.savefig(os.path.join(IMG, 'esquema_cajon.png'), dpi=140, bbox_inches='tight')
    plt.close(fig)


def leer_vol(ruta):
    tt, fr = {}, {}
    act = None
    for l in open(ruta, encoding='utf-8', errors='replace'):
        m = re.match(r'^Time = ([0-9.eE+-]+)', l)
        if m:
            act = float(m.group(1))
            continue
        m = re.search(r'Phase-1 volume fraction = ([0-9.eE+-]+)', l)
        if m and act is not None:
            fr[act] = float(m.group(1))
    ts = np.array(sorted(fr))
    return ts, np.array([fr[x] for x in ts])


def fig_volumen(caso, log4):
    fig, ax = plt.subplots(figsize=(9, 3.6))
    t2, v2 = leer_vol(os.path.join(RES, caso, 'log.interFoam'))
    k = np.arange(0, len(t2), max(len(t2) // 1500, 1))
    ax.plot(t2[k], v2[k], color=TEAL, lw=1.6, label='película 2 mm (1,57 M celdas)')
    if log4 and os.path.exists(log4):
        t4, v4 = leer_vol(log4)
        k = np.arange(0, len(t4), max(len(t4) // 1500, 1))
        ax.plot(t4[k], v4[k], color=AMBER, lw=1.6, label='película 4 mm (1,10 M celdas), hasta t = %.2f s' % t4[-1])
    ax.axvspan(2.5, 4.0, color=SLATE, alpha=0.07, lw=0)
    ax.text(3.25, 0.3603, 'ventana del promedio', ha='center', va='top', fontsize=9)
    ax.set_xlim(0.5, 4.0)
    ax.set_ylim(0.353, 0.3605)
    ax.set_xlabel('tiempo simulado (s)')
    ax.set_ylabel('fracción de agua del dominio')
    ax.legend(frameon=False, fontsize=9, loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, 'volumen.png'), dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--caso', default='p2_medio_grueso')
    ap.add_argument('--log4mm', default=None)
    a = ap.parse_args()
    fig_espesor_caudal()
    print('espesor_caudal listo')
    cvh, xs = fig_cfd(a.caso)
    print('cfd listo; CV h:', dict(zip(xs.round(2), np.round(cvh, 1))))
    fig_volumen(a.caso, a.log4mm)
    print('volumen listo')
    fig_cortes(a.caso)
    print('cortes listos')
