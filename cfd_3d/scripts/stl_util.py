# -*- coding: utf-8 -*-
"""Lectura de STL ASCII con varios 'solid' (uno por parche) y corte por un plano y = cte."""
import numpy as np


def leer_stl(ruta):
    """Devuelve {nombre: array (N, 3, 3)} con los triangulos de cada solid (metros)."""
    out, nombre, cur = {}, None, []
    for l in open(ruta, encoding='utf-8', errors='replace'):
        l = l.strip()
        if l.startswith('solid '):
            nombre = l.split(None, 1)[1]
            cur = []
        elif l.startswith('vertex'):
            cur.append([float(v) for v in l.split()[1:4]])
        elif l.startswith('endsolid'):
            out[nombre] = np.array(cur, dtype=np.float64).reshape(-1, 3, 3)
    return out


def cortar_y(tris, y0):
    """Segmentos (M, 2, 2) en (x, z) de la interseccion de los triangulos con el plano y = y0."""
    seg = []
    for T in tris:
        d = T[:, 1] - y0
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if d[a] == 0 and d[b] == 0:
                continue
            if (d[a] <= 0 <= d[b]) or (d[b] <= 0 <= d[a]):
                if d[a] == d[b]:
                    continue
                u = d[a] / (d[a] - d[b])
                p = T[a] + u * (T[b] - T[a])
                pts.append((p[0], p[2]))
        if len(pts) >= 2:
            seg.append([pts[0], pts[1]])
    return np.array(seg)
