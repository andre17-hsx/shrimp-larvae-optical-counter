# -*- coding: utf-8 -*-
"""Dominio de fluido de la fase 3: la malla, el tobogan recto, el arco y el tramo final (linea de conteo), a partir del
mismo script de Fusion 360 que usa geometria_cfd.py. Empieza justo aguas abajo del labio de la cresta (x_in, 60 mm por
defecto) y termina en el final del tobogan (X = XE). Semiancho (y >= 0, y = 0 es plano de simetria). Va con la tapa
(cubierta) del tobogan como pared: el aire solo entra y sale por la entrada y por la salida.

Sistema de coordenadas (mm en el script, metros en el STL): x = X_VERTEDERO - X (positivo aguas abajo, cresta en x = 0),
y = Y, z = Z - ZC.

Uso (entorno con cadquery):   python geometria_linea.py [--x-in 60]
Escribe ../geometria/dominio_linea.stl (un solido por parche: inlet, outlet, symmetry, malla, paredes),
zona_pelicula_linea.stl y dominio_linea_info.json.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import cadquery as cq

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', '..', 'simulacion_flujo'))
from geometria_canal import _cargar_script, SCRIPT_FUSION  # noqa: E402
from geometria_cfd import escribir_stl, SALIDA  # noqa: E402


def construir(x_in=60.0, n_arco=24):
    m, g = _cargar_script(SCRIPT_FUSION)
    XV, ZC, T = m.X_VERTEDERO, g['ZC'], m.T
    S, AV = m.PENDIENTE_INICIAL, m.ALTO_VERTEDERO
    hm = m.ANCHO_CANAL / 2.0
    X0, X1, X2, XE = g['X0'], g['X1'], g['X2'], g['XE']
    x0c, x1c, xEc = XV - X0, XV - X1, XV - XE
    t1, t2, R, Z1 = g['t1'], g['t2'], m.RADIO_CURVA, g['Z1']
    d = m.ALTO_TOBOGAN
    zm = lambda x: AV - x * S
    fondo = lambda x: m.z_fondo(g, XV - x) - ZC
    # ---- fondo: malla, recta, arco (tangente), recta final
    bed = [(x_in, zm(x_in)), (x0c, zm(x0c)), (x1c, fondo(x1c))]
    ths = np.linspace(t1, t2, n_arco + 1)
    arc = [(XV - (X1 - R * (math.sin(th) - math.sin(t1))), Z1 + R * (math.cos(th) - math.cos(t1)) - ZC, th) for th in ths]
    bed += [(x, z) for x, z, th in arc[1:]]
    bed.append((xEc, fondo(xEc)))
    # ---- cara inferior de la tapa: paralela al fondo a 'd' mm (recta, arco concentrico, recta), luego como en fase 2
    zt_int = g['techo'][0][1] - ZC                                # a la altura de la brida (x0c)
    roof = []
    p3x = arc[-1][0] - (xEc - arc[-1][0]) * 0                      # (solo para claridad)
    x_fin_z = fondo(xEc)
    # punto final de la tapa: fin del tobogan, d mm por encima del fondo, medido perpendicular a la pendiente final
    roof.append((xEc + d * math.sin(t2) * 0 + 0.0, g['techo'][4][1] - ZC))
    for x, z, th in reversed(arc):
        roof.append((x + d * math.sin(th), z + d * math.cos(th)))
    roof.append((x0c, zt_int))                                     # fin de la recta paralela a la malla, en x0c
    x229 = XV - 1861
    xcaj = XV - m.X_CAJON
    roof.append((x229, zt_int))
    z_in = zt_int + (x229 - x_in) / (x229 - xcaj) * ((m.ALTO_CAJON - T) - zt_int)     # tramo a 45 grados hacia el cajon
    roof.append((x_in, z_in))
    perfil = bed + roof
    planta = [(x_in, 0.0), (x_in, hm), (xEc, hm), (xEc, 0.0)]
    prisma_planta = cq.Workplane('XY').workplane(offset=-600).polyline(planta).close().extrude(1400, clean=False)
    prisma_perfil = cq.Workplane('XZ').polyline(perfil).close().extrude(-900, clean=False)      # hacia +Y
    dom = prisma_planta.intersect(prisma_perfil, clean=False)
    p = dict(x_in=x_in, xEc=xEc, x0c=x0c, x1c=x1c, S=S, zm=zm, fondo=fondo, hm=hm, z_in=z_in, bed=bed, roof=roof)
    return m, g, dom, p


def clasificar(dom, p):
    parches = {k: [] for k in ('inlet', 'outlet', 'symmetry', 'malla', 'paredes')}
    tol = 1e-4
    for cara in dom.faces().vals():
        bb = cara.BoundingBox()
        n = cara.normalAt(cara.Center())
        if abs(bb.ymin) < tol and abs(bb.ymax) < tol:
            parches['symmetry'].append(cara)
        elif abs(bb.xmin - p['x_in']) < tol and abs(bb.xmax - p['x_in']) < tol:
            parches['inlet'].append(cara)
        elif abs(bb.xmin - p['xEc']) < tol and abs(bb.xmax - p['xEc']) < tol:
            parches['outlet'].append(cara)
        elif (n.z < -0.9 * math.cos(math.atan(p['S'])) and bb.xmin > p['x_in'] - tol and bb.xmax < p['x0c'] + tol
              and all(abs(v.Z - p['zm'](v.X)) < 1e-3 for v in cara.Vertices())):
            parches['malla'].append(cara)
        else:
            parches['paredes'].append(cara)
    return parches


def zona_pelicula(p, abajo=5.0):
    """Zona de refinamiento sobre el fondo: 42 mm en la entrada (la lamina alli mide ~30 mm), bajando a 24 mm aguas abajo."""
    xs = list(np.arange(p['x_in'] - 5.0, p['xEc'] + 5.0, 20.0)) + [p['xEc'] + 5.0]
    f = p['fondo']
    grosor = lambda x: max(24.0, 42.0 - (x - p['x_in']) * 0.08)
    z_fondo = lambda x: p['zm'](x) if x <= p['x0c'] else f(x)
    sup = [(x, z_fondo(x) + grosor(x)) for x in xs]
    inf = [(x, z_fondo(x) - abajo) for x in reversed(xs)]
    return cq.Workplane('XZ').polyline(sup + inf).close().extrude(-900, clean=False).translate((0, -100, 0))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--x-in', type=float, default=60.0, help='x (mm) del plano de entrada, desde la cresta')
    a = ap.parse_args()
    m, g, dom, p = construir(a.x_in)
    sol = dom.solids().vals()
    print('solidos: %d | valido: %s | volumen: %.3f L' % (len(sol), all(s.isValid() for s in sol), sum(s.Volume() for s in sol) / 1e6))
    parches = clasificar(dom, p)
    os.makedirs(SALIDA, exist_ok=True)
    ntri = escribir_stl(os.path.join(SALIDA, 'dominio_linea.stl'), parches)
    escribir_stl(os.path.join(SALIDA, 'zona_pelicula_linea.stl'), {'zona': zona_pelicula(p).faces().vals()})
    bb = dom.val().BoundingBox()
    areas = {k: sum(c.Area() for c in v) / 1e6 for k, v in parches.items()}
    xm = 0.5 * (p['x_in'] + 900.0)
    info = {
        'unidades': 'm', 'caja': [bb.xmin * 1e-3, bb.ymin * 1e-3, bb.zmin * 1e-3, bb.xmax * 1e-3, bb.ymax * 1e-3, bb.zmax * 1e-3],
        'parches_triangulos': ntri, 'parches_area_m2': areas, 'x_in_m': p['x_in'] * 1e-3, 'x_salida_m': p['xEc'] * 1e-3,
        'x_fin_malla_m': p['x0c'] * 1e-3, 'ancho_canal_m': 2 * p['hm'] * 1e-3, 'z_fondo_in_m': p['zm'](p['x_in']) * 1e-3,
        'z_techo_in_m': p['z_in'] * 1e-3, 'pendiente_malla': p['S'],
        'punto_en_aire_m': [xm * 1e-3, 0.10, (p['fondo'](xm) + 45.0) * 1e-3],
    }
    json.dump(info, open(os.path.join(SALIDA, 'dominio_linea_info.json'), 'w'), indent=1)
    print('parches (triangulos):', ntri)
    print('parches (area m2):', {k: round(v, 4) for k, v in areas.items()})
    print('caja (m): x %.3f..%.3f | y %.3f..%.3f | z %.3f..%.3f' % (bb.xmin * 1e-3, bb.xmax * 1e-3, bb.ymin * 1e-3, bb.ymax * 1e-3,
                                                              bb.zmin * 1e-3, bb.zmax * 1e-3))
    print('entrada: z de %.1f a %.1f mm | salida x = %.1f mm' % (info['z_fondo_in_m'] * 1e3, info['z_techo_in_m'] * 1e3, p['xEc']))
