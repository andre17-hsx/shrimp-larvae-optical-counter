# -*- coding: utf-8 -*-
"""Superficie libre del agua como mapa de alturas z(x, y), sin huecos, a partir del campo medio (alpha.waterMean = 0.5).

La isosuperficie de ParaView falla en las celdas poliedricas de las interfaces de refinamiento de snappyHexMesh ('cell with a
non-manifold triangulation ... cannot be contoured') y deja grietas. La superficie libre es univaluada en z, asi que se
reconstruye por columnas: para cada nodo (x, y) de una rejilla regular se toman las celdas cuya huella lo cubre y se busca el
cruce de alpha = 0.5 mas alto. La velocidad del vertice es |UMean| de la celda de agua mas alta de la columna.

    python superficie_altura.py [--caso p2_medio_grueso] [--h 0.004]
Escribe en cfd_3d/informe_preliminar/datos/: superficie_pos.f32, superficie_vel.f32, superficie_idx.u32 (mismo formato que
exportar_visor.py). Requiere numpy y scipy (entorno simenv).
"""
import argparse
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from analizar_3d import cargar  # noqa: E402

DAT = os.path.join(AQUI, '..', 'informe_preliminar', 'datos')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--caso', default='p2_medio_grueso')
    ap.add_argument('--h', type=float, default=0.004, help='paso de la rejilla (m)')
    ap.add_argument('--salto', type=float, default=0.008, help='no unir nodos vecinos con mas de este salto de altura (m)')
    ap.add_argument('--salida', default=None, help='carpeta de salida (por defecto informe_preliminar/datos)')
    a = ap.parse_args()
    DAT_ = a.salida or DAT
    t, aM, UM, C, V = cargar(a.caso)
    s = V ** (1.0 / 3.0)
    m = aM > 0.02
    Cw, aw, Uw, sw = C[m], aM[m], UM[m], s[m]
    tree = cKDTree(Cw[:, :2])
    h = a.h
    xs = np.arange(-0.744, 0.533 + 1e-9, h)
    ys = np.arange(0.0, 0.497 + 1e-9, h)
    z = np.full((len(xs), len(ys)), np.nan)
    v = np.zeros_like(z)
    rmax = 0.012
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            ye = max(y, 0.0022)      # la primera capa de celdas empieza a ~0,6 mm del plano de simetria (snappy quita la lamina delgada)
            idx = tree.query_ball_point((x, ye), rmax)
            if not idx:
                continue
            idx = np.asarray(idx)
            cx = Cw[idx]
            holg = 0.1 * sw[idx] + 1e-5                                # holgura: nodos sobre la cara de una celda o en y = 0
            ok = (np.abs(cx[:, 0] - x) <= sw[idx] / 2 + holg) & (np.abs(cx[:, 1] - ye) <= sw[idx] / 2 + holg)
            if not ok.any():
                continue
            idx = idx[ok]
            o = np.argsort(Cw[idx, 2])
            idx = idx[o]
            al = aw[idx]
            zc = Cw[idx, 2]
            k = np.where(al >= 0.5)[0]
            if not len(k):
                continue
            k = k[-1]                                              # celda de agua mas alta (alpha >= 0.5)
            if k + 1 < len(idx) and zc[k + 1] - zc[k] < 1.6 * sw[idx[k]]:
                a0, a1, z0, z1 = al[k], al[k + 1], zc[k], zc[k + 1]  # celda vecina de arriba con algo de agua
            else:
                a0, a1, z0, z1 = al[k], 0.0, zc[k], zc[k] + sw[idx[k]]   # arriba solo aire
            z[i, j] = z0 + (a0 - 0.5) / max(a0 - a1, 1e-9) * (z1 - z0)
            v[i, j] = np.linalg.norm(Uw[idx[k]])
    # relleno de huecos de un nodo de ancho (interfaces de refinamiento, celdas deformadas): un nodo invalido con vecinos validos
    # a ambos lados (en x, en y o en diagonal) toma su promedio; solo se rellenan huecos internos, no el contorno del agua
    for _ in range(3):
        nuevo = z.copy()
        nv = v.copy()
        val = ~np.isnan(z)
        for i in range(1, len(xs) - 1):
            for j in range(1, len(ys) - 1):
                if val[i, j]:
                    continue
                for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
                    if val[i + di, j + dj] and val[i - di, j - dj]:
                        nuevo[i, j] = 0.5 * (z[i + di, j + dj] + z[i - di, j - dj])
                        nv[i, j] = 0.5 * (v[i + di, j + dj] + v[i - di, j - dj])
                        break
        z, v = nuevo, nv
    valido = ~np.isnan(z)
    print('rejilla %d x %d, nodos validos %d' % (len(xs), len(ys), valido.sum()))
    # triangulos: cuadrantes con 4 nodos validos y sin saltos bruscos de altura
    tri = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if not all(valido[p] for p in q):
                continue
            zz = [z[p] for p in q]
            if max(zz) - min(zz) > a.salto:
                continue
            tri.append((q[0], q[1], q[2]))
            tri.append((q[0], q[2], q[3]))
    usados = sorted({p for t3 in tri for p in t3})
    nuevo = {p: n for n, p in enumerate(usados)}
    pos = np.array([[xs[p[0]], ys[p[1]], z[p]] for p in usados], dtype=np.float32)
    vel = np.array([v[p] for p in usados], dtype=np.float32)
    idxs = np.array([[nuevo[p] for p in t3] for t3 in tri], dtype=np.uint32)
    assert len(pos) < 65536, 'demasiados vertices para indices de 16 bits: subir --h'
    pos.tofile(os.path.join(DAT_, 'superficie_pos.f32'))
    vel.tofile(os.path.join(DAT_, 'superficie_vel.f32'))
    idxs.astype('<u4').tofile(os.path.join(DAT_, 'superficie_idx.u32'))
    print('superficie: %d vertices, %d triangulos, z %.3f..%.3f m, |U| %.2f..%.2f m/s, y min %.4f' % (
        len(pos), len(idxs), pos[:, 2].min(), pos[:, 2].max(), vel.min(), vel.max(), pos[:, 1].min()))
    # aristas de borde restantes (deben quedar solo en los bordes reales del agua)
    from collections import Counter
    e = np.concatenate([idxs[:, [0, 1]], idxs[:, [1, 2]], idxs[:, [2, 0]]]).astype(np.int64)
    e.sort(axis=1)
    cnt = Counter((e[:, 0] * len(pos) + e[:, 1]).tolist())
    b = np.array([k for k, c in cnt.items() if c == 1])
    b0, b1 = b // len(pos), b % len(pos)
    L = np.linalg.norm(pos[b0] - pos[b1], axis=1)
    mid = 0.5 * (pos[b0] + pos[b1])
    print('aristas de borde: %d (%.2f m); junto al plano de simetria (y < 6 mm): %d' % (len(b), L.sum(), (mid[:, 1] < 0.006).sum()))


if __name__ == '__main__':
    main()
