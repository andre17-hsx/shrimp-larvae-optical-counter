# -*- coding: utf-8 -*-
"""Vistas del dominio (STL por parches) para revisar la geometria antes de mallar."""
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

AQUI = os.path.dirname(os.path.abspath(__file__))
COLOR = {'inlet': '#2ca02c', 'outlet': '#d62728', 'atmosphere': '#9ecae1', 'symmetry': '#dddddd', 'malla': '#333333',
         'paredes': '#1f77b4'}


def leer(ruta):
    parches, actual = {}, None
    for linea in open(ruta, encoding='utf-8'):
        t = linea.split()
        if not t:
            continue
        if t[0] == 'solid':
            actual = t[1]
            parches[actual] = []
        elif t[0] == 'vertex':
            parches[actual].append([float(x) for x in t[1:4]])
    return {k: np.array(v).reshape(-1, 3, 3) for k, v in parches.items()}


if __name__ == '__main__':
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, '..', 'geometria', 'dominio.stl')
    salida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, '..', 'geometria', 'dominio_vistas.png')
    P = leer(ruta)
    fig, axs = plt.subplots(3, 1, figsize=(13, 12))
    vistas = ((axs[0], 0, 1, 'Planta (x, y): flujo hacia la derecha; y = 0 es el plano de simetria', 2),
              (axs[1], 0, 2, 'Perfil (x, z)', 1),
              (axs[2], 0, 2, 'Perfil, zona de la cresta (x, z) en metros', 1))
    for ax, i, j, tit, eje_prof in vistas:
        for nombre, tri in P.items():
            # los triangulos casi perpendiculares al plano de la vista se ven como lineas: se omiten
            n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-30)
            ok = np.abs(n[:, eje_prof]) > 0.05
            if nombre == 'symmetry' and eje_prof == 2:
                continue
            ax.add_collection(PolyCollection(tri[ok][:, :, [i, j]], facecolor=COLOR.get(nombre, 'k'), edgecolor='none',
                                             alpha=0.55 if nombre in ('symmetry', 'atmosphere') else 0.8, label=nombre))
        ax.set_aspect('equal')
        ax.set_title(tit, fontsize=10)
    axs[0].autoscale_view()
    axs[1].autoscale_view()
    axs[2].set_xlim(-0.06, 0.12)
    axs[2].set_ylim(-0.02, 0.15)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLOR.values()]
    axs[0].legend(handles, COLOR.keys(), ncol=6, loc='upper left', fontsize=8)
    fig.savefig(salida, dpi=100, bbox_inches='tight')
    print('vistas en', salida)
