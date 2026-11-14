# -*- coding: utf-8 -*-
"""Figuras finales: diseno anterior (A) frente al diseno nuevo, ya aplicado al modelo (B)."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
CA, CB = '#c0392b', '#1f77b4'


def _mapa(ax, r, campo, vmin, vmax, cmap, c, s_min=None):
    m = np.ma.masked_where(r.sol, campo)
    ax.imshow(m.T, origin='lower', aspect='equal', cmap=cmap, vmin=vmin, vmax=vmax,
              extent=[r.s[0] - r.dx / 2, r.s[-1] + r.dx / 2, r.y[0] - r.dy / 2, r.y[-1] + r.dy / 2])
    ax.set_facecolor('#e4e4e4')
    ax.axvline(c.s_conteo, color='k', ls='--', lw=1.1)
    ax.axvline(0, color='k', lw=0.6, ls=':')
    ax.set_xlim(s_min if s_min is not None else r.s[0], r.s[-1])
    ax.set_ylabel('y (m)')
    return ax


def figura_planta(c, A, B, PA, PB, ruta):
    from contracciones import metricas
    fig = plt.figure(figsize=(14, 9.5))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.35, 0.07, 1.0], hspace=0.38, wspace=0.18)
    for k, (r, tit) in enumerate(((A, 'A: diseno anterior\n(paredes de contraccion de 47 grados sobre la malla)'),
                                  (B, 'B: diseno nuevo, ya en el modelo\n(estrechamiento en el cajon, antes de la cresta)'))):
        ax = fig.add_subplot(gs[0, k])
        _mapa(ax, r, r.h_m * 1e3, 0, 20, 'viridis', c, s_min=-0.55)
        ax.set_title(tit, fontsize=10)
        ax.text(c.s_conteo - 0.02, 0.47, 'linea de conteo', ha='right', va='top', fontsize=8)
        ax.text(0.01, -0.47, 'cresta', fontsize=8, va='bottom')
        ax.set_xlabel('s: distancia desde la cresta (m)')
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(0, 20))
    cax = fig.add_subplot(gs[1, :])
    fig.colorbar(sm, cax=cax, orientation='horizontal',
                 label='profundidad del agua (mm); el cajon, a la izquierda de la cresta, esta fuera de escala')
    ax1 = fig.add_subplot(gs[2, 0])
    ax2 = fig.add_subplot(gs[2, 1])
    for r, col, nom in ((A, CA, 'A'), (B, CB, 'B')):
        i0, i1 = np.searchsorted(r.s, [c.s_conteo - 0.025, c.s_conteo + 0.025])
        libre = ~r.sol[i0:i1 + 1].any(axis=0)
        y = r.y[libre] * 1e3
        ax1.plot(y, r.h_m[i0:i1 + 1][:, libre].mean(axis=0) * 1e3, color=col, lw=2, label=nom)
        ax2.plot(y, r.u_m[i0:i1 + 1][:, libre].mean(axis=0), color=col, lw=2, label=nom)
        q = metricas(c, r)
        dy = 0.05 + 0.1 * (nom == 'B')
        ax1.text(0.02, dy, '%s: variacion a lo ancho (CV) = %.1f %%' % (nom, q['cv_h']), color=col, transform=ax1.transAxes)
        ax2.text(0.02, dy, '%s: variacion a lo ancho (CV) = %.1f %%' % (nom, q['cv_u']), color=col, transform=ax2.transAxes)
    ax1.set_ylim(0, None)
    ax1.set_xlabel('y (mm), en la ventana de conteo')
    ax1.set_ylabel('profundidad (mm)')
    ax1.set_title('Lamina de agua a lo ancho en la linea de conteo')
    ax1.legend(frameon=False, loc='upper right')
    ax2.set_ylim(0, 2.6)
    ax2.set_xlabel('y (mm)')
    ax2.set_ylabel('velocidad (m/s)')
    ax2.set_title('Velocidad a lo ancho en la linea de conteo')
    ax2.legend(frameon=False, loc='upper right')
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def figura_barrido(barrido, ruta):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
    for nom, col in (('A', CA), ('B', CB)):
        Q = [q['Q'] for q in barrido[nom]]
        axs[0].plot(Q, [q['h_media'] for q in barrido[nom]], color=col, lw=2, marker='o', label=nom + ' (media)')
        axs[0].fill_between(Q, [q['h_min'] for q in barrido[nom]], [q['h_max'] for q in barrido[nom]], color=col, alpha=0.2)
        axs[1].plot(Q, [q['cv_h'] for q in barrido[nom]], color=col, lw=2, marker='o', label=nom)
    axs[0].set_xlabel('caudal de entrada (L/s)')
    axs[0].set_ylabel('profundidad en la ventana de conteo (mm)')
    axs[0].set_title('Lamina: media y rango a lo ancho')
    axs[0].legend(frameon=False)
    axs[1].set_xlabel('caudal de entrada (L/s)')
    axs[1].set_ylabel('CV de la profundidad a lo ancho (%)')
    axs[1].axhspan(0, 5, color='#2ecc71', alpha=0.15)
    axs[1].text(4.1, 0.6, 'uniforme (< 5 %)', color='#1e8449')
    axs[1].set_title('Uniformidad a lo ancho')
    axs[1].legend(frameon=False)
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def figura_pulsaciones(puls, ruta, canal=None):
    """puls: canal con el cajon modelado; canal: solo el canal (entrada critica en la cresta), opcional."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    f = [p['f'] for p in puls]
    for datos, ls, nom in ((puls, '-', 'con el cajon'), (canal, '--', 'solo el canal')):
        if datos is None:
            continue
        ax.plot(f, [100 * p['amp_rel'][-1] for p in datos], ls=ls, marker='o', lw=2, label='%s, en la linea de conteo' % nom)
        ax.plot(f, [100 * p['amp_rel'][2] for p in datos], ls=ls, marker='s', lw=1, alpha=0.6, label='%s, s = 0,7 m' % nom)
    ax.axhline(3.3, color='k', ls=':', lw=0.9)
    ax.text(0.52, 2.55, 'sin amplificar: 3,3 %', fontsize=8)
    ax.set_xscale('log')
    ax.set_xticks(f)
    ax.set_xticklabels([('%g' % x) for x in f])
    ax.set_xlabel('frecuencia de la pulsacion del caudal (Hz)')
    ax.set_ylabel('amplitud de la profundidad en el eje (% de la media)')
    ax.set_title('Una pulsacion de +-5 % del caudal, cuanto se ve en la lamina')
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylim(0, None)
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def figura_larvas(c, A, B, trs, tasas, larv, ruta):
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.5))
    ax = axs[0]
    for nom, col in (('A', CA), ('B', CB)):
        for orient, ls in (('alineada', '-'), ('aleatoria', '--')):
            ax.plot(tasas, [100 * x[1] for x in larv[nom][orient]], color=col, ls=ls, marker='o', ms=3,
                    label='%s, larvas %s' % (nom, orient))
    ax.axhline(1, color='k', lw=0.6, ls=':')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('larvas por segundo en el canal')
    ax.set_ylabel('conteo perdido por solapamiento (%)')
    ax.set_title('Larvas que se tapan entre si en la imagen')
    ax.legend(frameon=False, fontsize=8)
    ax = axs[1]
    for nom, col in (('A', CA), ('B', CB)):
        tr = trs[nom]
        ok = np.isfinite(tr['y'])
        ax.hist(tr['y'][ok] * 1e3, bins=np.linspace(-260, 260, 53), density=True, histtype='step', color=col, lw=2, label=nom)
    ax.set_xlabel('y de la larva al cruzar la linea de conteo (mm)')
    ax.set_ylabel('densidad de probabilidad')
    ax.set_title('Donde caen las larvas a lo ancho del canal')
    ax.legend(frameon=False)
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)
