# -*- coding: utf-8 -*-
"""Dominio de fluido (agua + aire) del modelo de Fusion para el CFD 3D, a partir de las constantes y funciones del propio
script (Fusion360_VAKI_Macro.py), asi el CFD y el modelo no se desincronizan.

Sistema de coordenadas del CFD (mm dentro de este script, metros en el STL):
    x = X_VERTEDERO - X     (positivo hacia aguas abajo; la cresta esta en x = 0)
    y = Y                   (se simula el semiancho y >= 0; y = 0 es plano de simetria)
    z = Z - ZC              (0 = fondo del cajon; la cresta esta en z = ALTO_VERTEDERO)

Dominio = interseccion del prisma de la planta interior (paredes del estrechamiento, cajon ancho, pared trasera) con el
prisma del perfil lateral (fondo del cajon, escalon del vertedero con su labio, malla, tobogan recto, cubierta), menos el
deflector, mas un tubo corto bajo el fondo que hace de entrada (el cono difusor se estudia aparte).

Simplificaciones (documentadas): la regla de nivel (2 mm) no se incluye; la cuña de 0 a 1,3 mm bajo el extremo del labio se
rellena; el tramo aguas abajo termina en el inicio del arco (X1).

Uso (con el entorno que tiene cadquery):   python geometria_cfd.py [--fin-x 1557]
Escribe ../geometria/dominio.stl (un solido por parche) y ../geometria/dominio_info.json.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import cadquery as cq

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', 'simulacion_flujo'))
from geometria_canal import _cargar_script, SCRIPT_FUSION  # noqa: E402

SALIDA = os.path.join(AQUI, '..', 'geometria')


def construir(x_fin_X=None, r_entrada_ext=None, losa=None, x_in_losa=-0.40, con_labio=None):
    m, g = _cargar_script(SCRIPT_FUSION)
    XV, ZC, T = m.X_VERTEDERO, g['ZC'], m.T
    S = m.PENDIENTE_INICIAL
    AV = m.ALTO_VERTEDERO
    hm = m.ANCHO_CANAL / 2.0
    X0, X1 = g['X0'], g['X1'] if x_fin_X is None else x_fin_X
    x0c, x1c = XV - X0, XV - X1
    zm = lambda x: AV - x * S                                      # fondo / malla, a la altura de la cresta AV en x = 0
    zt_int = g['techo'][0][1] - ZC                                 # cara inferior de la cubierta / tapa en X0
    alto_c = m.ALTO_CAJON
    x_atras = -800.0
    # ---- rampa curva en la base de la cresta (cuarto de circulo, ver RADIO_RAMPA_CRESTA en el script de Fusion):
    # reemplaza la esquina de 90 grados que en p2_medio_grueso mostro un remolino pegado a la esquina (hasta -0.47
    # m/s de retorno, vuelta cada ~0.8 s). Mismo radio y misma discretizacion que construir_canal_superior().
    rampa = [(-d, z) for d, z in m.perfil_rampa_cresta()]
    # ---- perfil lateral (x, z), sentido antihorario
    if con_labio is None:
        con_labio = getattr(m, 'CON_LABIO', True)
    labio = ([(-m.LABIO_ARRIBA, AV), (-m.LABIO_ARRIBA, AV + m.ALTO_LABIO),
              (m.LABIO_ABAJO, AV + m.ALTO_LABIO), (m.LABIO_ABAJO, zm(m.LABIO_ABAJO))] if con_labio else [])
    perfil = [(x_atras, 0)] + rampa + labio + [(x0c, zm(x0c)), (x1c, zm(x1c)),
              (x1c, zt_int - (x1c - x0c) * S), (x0c, zt_int), (XV - 1861, zt_int),
              (XV - m.X_CAJON, alto_c - T), (XV - m.X_CAJON, alto_c), (x_atras, alto_c)]
    # ---- planta interior, semiancho y >= 0 (x, y)
    dentro = m.curva_estrechamiento()                              # (X, y) de la brida (X0) a x_fin, cara interior
    XCH, XF, h, f = m.X_CHAFLAN, m.LARGO_TOTAL, m.ANCHO_CUERPO / 2.0, m.ANCHO_FRENTE / 2.0
    ext = [(XCH, -h), (XF, -f), (XF, f), (XCH, h)]
    rectas = [m.recta_offset(ext[i], ext[i + 1], T, 1) for i in range(3)]
    interior = [m.cruce_x(rectas[0], XCH), m.cruce(rectas[0], rectas[1]), m.cruce(rectas[1], rectas[2]),
                m.cruce_x(rectas[2], XCH)]
    planta = [(x1c, 0.0), (x1c, hm)] + [(XV - X, y) for X, y in dentro if XV - X < x1c - 1e-9] \
        + [(XV - interior[3][0], interior[3][1]), (XV - interior[2][0], interior[2][1]), (XV - interior[2][0], 0.0)]
    if losa:                                                      # corte 2D: rectangulo de ancho 'losa' mm
        x_in = x_in_losa * 1e3
        planta = [(x1c, 0.0), (x1c, losa), (x_in, losa), (x_in, 0.0)]
    # ---- prismas e interseccion
    prisma_planta = cq.Workplane('XY').workplane(offset=-200).polyline(planta).close().extrude(700, clean=False)
    prisma_perfil = cq.Workplane('XZ').polyline(perfil).close().extrude(-900, clean=False)      # hacia +Y
    dom = prisma_planta.intersect(prisma_perfil, clean=False)
    # ---- deflector de paso inferior (placa entre las paredes, con hueco libre abajo)
    xd0, xd1 = XV - (m.X_DEFLECTOR + T), XV - m.X_DEFLECTOR
    defl = cq.Workplane('XY').box(xd1 - xd0, 900, 400, centered=False).translate((xd0, 0, m.DEFLECTOR_PASO_INFERIOR))
    dom = dom.cut(defl, clean=False)
    if losa:
        return m, g, dom, dict(x0c=x0c, x1c=x1c, xin=x_in_losa * 1e3, r_in=0.0, largo_tubo=0.0, zm=zm, AV=AV, alto_c=alto_c,
                               xcaj=XV - m.X_CAJON, hm=hm, S=S, losa=losa, x_in=x_in_losa * 1e3, x_malla0=(m.LABIO_ABAJO if con_labio else 0.0))
    # ---- tubo de entrada bajo el fondo (radio interior del extremo ancho del difusor)
    r_in = (m.D_ENTRADA / 2.0 - T) if r_entrada_ext is None else r_entrada_ext
    xin = XV - m.X_ENTRADA
    largo_tubo = 60.0
    tubo = cq.Workplane('XY').workplane(offset=-largo_tubo).center(xin, 0).circle(r_in).extrude(largo_tubo)
    mitad = cq.Workplane('XY').box(2000, 900, 400, centered=False).translate((-1000, 0, -200))
    tubo = tubo.intersect(mitad, clean=False)
    dom = dom.union(tubo, clean=False)
    return m, g, dom, dict(x0c=x0c, x1c=x1c, xin=xin, r_in=r_in, largo_tubo=largo_tubo, zm=zm, AV=AV, alto_c=alto_c,
                           xcaj=XV - m.X_CAJON, hm=hm, S=S, x_malla0=(m.LABIO_ABAJO if con_labio else 0.0))


def clasificar(dom, p):
    """Reparte las caras del dominio en parches."""
    parches = {k: [] for k in ('inlet', 'outlet', 'atmosphere', 'symmetry', 'malla', 'paredes')}
    tol = 1e-4
    for cara in dom.faces().vals():
        bb = cara.BoundingBox()
        c = cara.Center()
        n = cara.normalAt(c)
        if abs(bb.ymin) < tol and abs(bb.ymax) < tol:
            parches['symmetry'].append(cara)
        elif p.get('losa') and abs(bb.ymin - p['losa']) < tol and abs(bb.ymax - p['losa']) < tol:
            parches['symmetry'].append(cara)
        elif p.get('losa') and abs(bb.xmin - p['x_in']) < tol and abs(bb.xmax - p['x_in']) < tol:
            parches['inlet'].append(cara)
        elif (not p.get('losa')) and abs(bb.zmin + p['largo_tubo']) < tol and abs(bb.zmax + p['largo_tubo']) < tol:
            parches['inlet'].append(cara)
        elif abs(bb.xmin - p['x1c']) < tol and abs(bb.xmax - p['x1c']) < tol:
            parches['outlet'].append(cara)
        elif abs(bb.zmin - p['alto_c']) < tol and abs(bb.zmax - p['alto_c']) < tol and n.z > 0.9:
            parches['atmosphere'].append(cara)
        elif (n.z < -0.9 * math.cos(math.atan(p["S"]))
              and bb.xmin > p['x_malla0'] - 0.1 and bb.xmax < p['x0c'] + tol
              and all(abs(v.Z - p['zm'](v.X)) < 1e-3 for v in cara.Vertices())):
            parches['malla'].append(cara)
        else:
            parches['paredes'].append(cara)
    return parches


def escribir_stl(ruta, parches, escala=1e-3):
    """STL ASCII con un 'solid' por parche (metros)."""
    ntri = {}
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        for nombre, caras in parches.items():
            if not caras:
                continue
            f.write('solid %s\n' % nombre)
            n = 0
            for cara in caras:
                V, Tr = cara.tessellate(0.02, 0.1)
                P = np.array([[v.x, v.y, v.z] for v in V]) * escala
                for a, b, c in Tr:
                    A, B, C = P[a], P[b], P[c]
                    nn = np.cross(B - A, C - A)
                    L = np.linalg.norm(nn)
                    if L < 1e-18:
                        continue
                    nn /= L
                    f.write('  facet normal %.6e %.6e %.6e\n    outer loop\n' % tuple(nn))
                    for Q in (A, B, C):
                        f.write('      vertex %.9e %.9e %.9e\n' % tuple(Q))
                    f.write('    endloop\n  endfacet\n')
                    n += 1
            f.write('endsolid %s\n' % nombre)
            ntri[nombre] = n
    return ntri


def zonas(p):
    """Solidos cerrados (STL) que marcan donde refinar la malla: pelicula sobre la malla y el tobogan, zona de la cresta y
    superficie libre en el cajon. Coordenadas en mm, mismos ejes que el dominio."""
    AV, S, zm, x1c = p['AV'], p['S'], p['zm'], p['x1c']
    ymax = 900.0

    def prisma(pts):
        return cq.Workplane('XZ').polyline(pts).close().extrude(-ymax, clean=False).translate((0, -100, 0))

    z = {}
    z['pelicula'] = prisma([(-15, AV - 15), (-15, AV + 40), (x1c, zm(x1c) + 30), (x1c, zm(x1c) - 5), (6, zm(6) - 5), (6, AV - 15)])
    z['cresta'] = prisma([(-12, AV - 12), (-12, AV + 25), (45, AV + 25), (45, zm(45) - 4), (6, zm(6) - 4), (6, AV - 12)])
    z['superficie_cajon'] = prisma([(-800, 85), (-800, 140), (-15, 140), (-15, 85)])
    return z


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fin-x', type=float, default=None, help='X (mm) del plano de salida; por defecto el inicio del arco')
    ap.add_argument('--losa', type=float, default=None, help='ancho (mm) de un corte 2D con simetria a ambos lados')
    ap.add_argument('--x-in', type=float, default=-0.40, help='x (m) de la entrada del corte 2D')
    ap.add_argument('--sin-labio', action='store_true', help='variante sin labio: la rampa termina directo en la malla')
    ap.add_argument('--nombre', default=None, help='prefijo de los archivos de salida (por defecto dominio o dominio_losa)')
    a = ap.parse_args()
    m, g, dom, p = construir(a.fin_x, losa=a.losa, x_in_losa=a.x_in, con_labio=False if a.sin_labio else None)
    nombre = a.nombre or ('dominio_losa' if a.losa else 'dominio')
    sol = dom.solids().vals()
    print('solidos: %d | valido: %s | volumen: %.3f L' % (len(sol), all(s.isValid() for s in sol),
                                                          sum(s.Volume() for s in sol) / 1e6))
    parches = clasificar(dom, p)
    os.makedirs(SALIDA, exist_ok=True)
    ntri = escribir_stl(os.path.join(SALIDA, nombre + '.stl'), parches)
    for k, sz in zonas(p).items():
        escribir_stl(os.path.join(SALIDA, 'zona_%s.stl' % k), {'zona': sz.faces().vals()})
    bb = dom.val().BoundingBox()
    areas = {k: sum(c.Area() for c in v) / 1e6 for k, v in parches.items()}
    info = {
        'unidades': 'm', 'x_cresta': 0.0,
        'caja': [bb.xmin * 1e-3, bb.ymin * 1e-3, bb.zmin * 1e-3, bb.xmax * 1e-3, bb.ymax * 1e-3, bb.zmax * 1e-3],
        'parches_caras': {k: len(v) for k, v in parches.items()}, 'parches_triangulos': ntri, 'parches_area_m2': areas,
        'x_salida_m': p['x1c'] * 1e-3, 'x_inicio_malla_m': 0.0, 'x_fin_malla_m': p['x0c'] * 1e-3,
        'entrada': {'x_m': p['xin'] * 1e-3, 'y_m': 0.0, 'radio_m': p['r_in'] * 1e-3, 'z_base_m': -p['largo_tubo'] * 1e-3},
        'nivel_cajon_m': g['NIVEL'] * 1e-3, 'alto_vertedero_m': p['AV'] * 1e-3,
        'caudal_diseno_Ls': m.CAUDAL_DISENO, 'pendiente_malla': p['S'], 'ancho_canal_m': 2 * p['hm'] * 1e-3,
        'losa_m': (a.losa * 1e-3) if a.losa else None,
        'punto_en_agua_m': [-0.30, (a.losa * 0.5e-3) if a.losa else 0.05, 0.05],
    }
    json.dump(info, open(os.path.join(SALIDA, nombre + '_info.json'), 'w'), indent=1)
    print('parches (caras):', info['parches_caras'])
    print('parches (triangulos):', ntri)
    print('parches (area m2):', {k: round(v, 4) for k, v in areas.items()})
    print('caja (m): x %.3f..%.3f | y %.3f..%.3f | z %.3f..%.3f' % (bb.xmin * 1e-3, bb.xmax * 1e-3, bb.ymin * 1e-3, bb.ymax * 1e-3,
                                                              bb.zmin * 1e-3, bb.zmax * 1e-3))
