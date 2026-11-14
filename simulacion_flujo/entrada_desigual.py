# -*- coding: utf-8 -*-
"""Sensibilidad de la propuesta B a una entrada desigual al cajon (velocidad de entrada no uniforme, nivel plano)."""
import json
import os
import numpy as np

from geometria_canal import cargar_canal
from flujo_1d import calibrar_kd
from contracciones import metricas
from ejecutar_todo import caso_B, RES

if __name__ == '__main__':
    c, m, g = cargar_canal()
    kd = calibrar_kd(c, 0.15)
    dx = 4e-3
    ny = int(round(c.ancho0 / dx))
    x = (-c.ancho0 / 2 + (np.arange(ny) + 0.5) * dx) / (c.ancho0 / 2)
    casos = (('uniforme', np.ones(ny)),
             ('inclinada +-25 % (mas caudal a un lado)', 1 + 0.25 * x),
             ('inclinada +-50 %', 1 + 0.5 * x),
             ('chorro central +100 %', 1 + 1.0 * np.exp(-(x / 0.4) ** 2)),
             ('chorro pegado a un lado +100 %', 1 + 1.0 * np.exp(-((x - 0.5) / 0.25) ** 2)),
             ('ondulada, 2 crestas +-50 %', 1 + 0.5 * np.cos(2 * np.pi * x)))
    res = []
    for nom, fq in casos:
        r = caso_B(c, kd, dx=dx, fq=fq / fq.mean())
        q = metricas(c, r)
        res.append({'caso': nom, **q})
        print('%-42s h %.2f (%.1f-%.1f) mm | CV h %5.1f %% | u %.2f-%.2f m/s | CV u %.1f %%' %
              (nom, q['h_media'], q['h_min'], q['h_max'], q['cv_h'], q['u_min'], q['u_max'], q['cv_u']), flush=True)
    json.dump(res, open(os.path.join(RES, 'entrada_desigual.json'), 'w'), indent=1, default=float)
