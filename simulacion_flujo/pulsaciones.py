# -*- coding: utf-8 -*-
"""Respuesta del canal a pulsaciones del caudal (bomba, variador, oleaje del cajon) y ondas de rodillo."""
import numpy as np
from geometria_canal import cargar_canal
from flujo_1d import perfil_estacionario, calibrar_kd
from swe2d import Caso
from contracciones import ancho_fijo


def respuesta(c, f, kd, frec, a=0.05, dx=4e-3, t_fin=6.0, t_ini=2.0, sondas_s=None):
    """Amplitud relativa de la profundidad (en el eje) a la frecuencia de forzado, en varias estaciones."""
    sondas_s = sondas_s or [0.1, 0.4, 0.7, c.s_conteo]
    P = perfil_estacionario(c, forma_ancho=f, kd=kd)
    caso = Caso(c, P, dx=dx, forma_ancho=f, kd=kd)
    caso.ejecutar(t_fin, 1e9, pert_a=a, pert_f=frec, sondas=[(s, 0.0) for s in sondas_s], dt_sonda=1e-3)
    t = caso.serie[:, 0]
    m = t >= t_ini
    out = []
    for k, s in enumerate(sondas_s):
        h = caso.serie[m, k + 1]
        A = np.vstack([np.sin(2 * np.pi * frec * t[m]), np.cos(2 * np.pi * frec * t[m]), np.ones(m.sum())]).T
        co = np.linalg.lstsq(A, h, rcond=None)[0]
        amp = np.hypot(co[0], co[1])
        out.append((s, co[2], amp, h.max() - h.min()))
    return out


if __name__ == '__main__':
    import json
    import os
    c, m, g = cargar_canal()
    f = ancho_fijo(c)
    kd = calibrar_kd(c, 0.15)
    print('Solo el canal (entrada critica en la cresta, sin cajon): caudal Q(1 + 0,05 sen(2 pi f t))')
    print('amplitud del armonico / profundidad media en el eje (sin amplificacion seria 3,3 %)')
    res = []
    for frec in (0.5, 1, 2, 5, 10, 20):
        r = respuesta(c, f, kd, frec, t_fin=8.0, t_ini=4.0)
        res.append({'f': frec, 's': [x[0] for x in r], 'amp_rel': [x[2] / x[1] for x in r]})
        print('f = %4.1f Hz | ' % frec + ' | '.join('s=%.2f m: %.1f %%' % (s_, 100 * a / hm) for s_, hm, a, pp in r))
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados', 'pulsaciones_canal.json')
    json.dump(res, open(ruta, 'w'), indent=1)
