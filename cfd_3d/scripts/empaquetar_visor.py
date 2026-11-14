# -*- coding: utf-8 -*-
"""Empaqueta para la pagina del informe: datos3d.js (superficie del agua, lineas de corriente y paredes, cuantizados) y los
cuadros JPEG de la animacion del arranque.

    python empaquetar_visor.py
Lee cfd_3d/informe_preliminar/datos/*.f32|u32 (exportar_visor.py) y cfd_3d/vistas/p2_medio_grueso/t_*.png.
"""
import base64
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from stl_util import leer_stl  # noqa: E402

RAIZ = os.path.join(AQUI, '..', 'informe_preliminar')
DAT = os.path.join(RAIZ, 'datos')
BB = np.array([[-0.76, -0.005, -0.07], [0.55, 0.50, 0.31]])       # cuadro de cuantizacion (m)
VMAX = 2.5


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode('ascii')


def q16(p):
    return np.clip(np.round((p - BB[0]) / (BB[1] - BB[0]) * 65535), 0, 65535).astype('<u2')


def main(dat=None, stl_nombre='dominio.stl', salida='datos3d.js', var='DATOS3D', con_cuadros=True):
    DAT_ = dat or DAT
    sp = np.fromfile(os.path.join(DAT_, 'superficie_pos.f32'), '<f4').reshape(-1, 3)
    sv = np.fromfile(os.path.join(DAT_, 'superficie_vel.f32'), '<f4')
    si = np.fromfile(os.path.join(DAT_, 'superficie_idx.u32'), '<u4')
    assert si.max() < 65536
    lp = np.fromfile(os.path.join(DAT_, 'lineas_pos.f32'), '<f4').reshape(-1, 3)
    lv = np.fromfile(os.path.join(DAT_, 'lineas_vel.f32'), '<f4')
    ls = np.fromfile(os.path.join(DAT_, 'lineas_s.f32'), '<f4')
    ln = np.fromfile(os.path.join(DAT_, 'lineas_n.u32'), '<u4').astype(np.int64)
    off = np.concatenate([[0], np.cumsum(ln)])
    largo = np.array([ls[off[i + 1] - 1] for i in range(len(ln))], dtype='<f4')
    stl = leer_stl(os.path.join(AQUI, '..', 'geometria', stl_nombre))
    paredes = np.concatenate([stl['paredes'], stl['malla']]).astype('<f4')
    q8 = lambda v: np.clip(np.round(v / VMAX * 255), 0, 255).astype('u1')
    d = {
        'bbox': BB.tolist(), 'velMax': VMAX,
        'sup': {'nv': int(len(sp)), 'nt': int(len(si) // 3), 'pos': b64(q16(sp)), 'vel': b64(q8(sv)), 'idx': b64(si.astype('<u2'))},
        'lin': {'n': int(len(ln)), 'np': int(len(lp)), 'pos': b64(q16(lp)), 'vel': b64(q8(lv)), 'cuenta': b64(ln.astype('<u2')),
                'largo': b64(largo)},
        'paredes': {'nt': int(len(paredes)), 'pos': b64(paredes)},
    }
    js = 'window.%s = ' % var + json.dumps(d, separators=(',', ':')) + ';\n'
    open(os.path.join(RAIZ, salida), 'w', encoding='ascii').write(js)
    print('datos3d.js: %.2f MB' % (len(js) / 1e6))
    if not con_cuadros:
        return
    # cuadros de la animacion
    fr = os.path.join(RAIZ, 'frames')
    os.makedirs(fr, exist_ok=True)
    for f in glob.glob(os.path.join(fr, '*.jpg')):
        os.remove(f)
    fs = sorted(glob.glob(os.path.join(AQUI, '..', 'vistas', 'p2_medio_grueso', 't_*.png')),
                key=lambda f: float(re.search(r't_([0-9.]+)\.png', f).group(1)))
    ts = []
    for k, f in enumerate([f for f in fs if float(re.search(r't_([0-9.]+)\.png', f).group(1)) >= 0.2]):
        t = float(re.search(r't_([0-9.]+)\.png', f).group(1))
        im = Image.open(f).convert('RGB').crop((360, 200, 1240, 720))
        im.save(os.path.join(fr, 'f%02d.jpg' % k), quality=82, optimize=True)
        ts.append(t)
    json.dump(ts, open(os.path.join(RAIZ, 'frames', 'tiempos.json'), 'w'))
    print('cuadros:', len(ts), 'tiempos', ts[0], '...', ts[-1], '| peso total %.1f MB' % (
        sum(os.path.getsize(os.path.join(fr, x)) for x in os.listdir(fr)) / 1e6))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--sinlabio':
        main(os.path.join(RAIZ, 'datos_sinlabio'), 'dominio_sinlabio.stl', 'datos3d_sinlabio.js', 'DATOS3D_SINLABIO', False)
    else:
        main()
