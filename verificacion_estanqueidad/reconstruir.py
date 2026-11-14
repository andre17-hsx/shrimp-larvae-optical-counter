# -*- coding: utf-8 -*-
"""Reconstruye en CadQuery los sólidos que produciría el script de Fusion y verifica choques."""
import json, sys, os, itertools
import cadquery as cq

SP = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(SP, 'fusion_sim.json')))

import math
def _seccion(sec, N=96):
    o, u, v, pts = sec['o'], sec['u'], sec['v'], sec['lazo']
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    res = []
    for k in range(N):
        a = 2 * math.pi * k / N; dx, dy = math.cos(a), math.sin(a); mejor = None
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            ex, ey = q[0] - p[0], q[1] - p[1]; den = dx * ey - dy * ex
            if abs(den) < 1e-12: continue
            t = ((p[0] - cx) * ey - (p[1] - cy) * ex) / den; s_ = ((p[0] - cx) * dy - (p[1] - cy) * dx) / den
            if t > 0 and -1e-9 <= s_ <= 1 + 1e-9 and (mejor is None or t < mejor): mejor = t
        x, y = cx + dx * mejor, cy + dy * mejor
        res.append(cq.Vector(*[10 * (o[i] + u[i] * x + v[i] * y) for i in range(3)]))
    return cq.Wire.makePolygon(res, close=True)

def cuerpo_de(piezas):
    s = None
    for p in piezas:
        x = solido(p)
        op = p.get('op', 'CUT' if p.get('resta') else 'JOIN')
        if s is None: s = x
        elif op == 'CUT': s = s.cut(x)
        elif op == 'INTERSECT': s = s.intersect(x)
        else: s = s.fuse(x)
    return s

def solido(p):
    if p.get('tipo') == 'revol':
        o, u, v = p['o'], p['u'], p['v']
        to3 = lambda q: cq.Vector(*[10 * (o[i] + u[i] * q[0] + v[i] * q[1]) for i in range(3)])
        wires = [cq.Wire.makePolygon([to3(q) for q in lazo], close=True) for lazo in p['lazos']]
        a0 = cq.Vector(*[10 * c for c in p['eje'][0]]); a1 = cq.Vector(*[10 * c for c in p['eje'][1]])
        return cq.Solid.revolve(wires[0], wires[1:], math.degrees(p['ang']), a0, a1)
    if p.get('tipo') == 'cuerpo':
        return cuerpo_de(p['piezas'])
    if p.get('tipo') == 'loft':
        return cq.Solid.makeLoft([_seccion(s) for s in p['secciones']], ruled=True)
    o, u, v, n = p['o'], p['u'], p['v'], p['n']
    to3 = lambda q: cq.Vector(*[10 * (o[i] + u[i] * q[0] + v[i] * q[1]) for i in range(3)])
    wires = [cq.Wire.makePolygon([to3(q) for q in lazo], close=True) for lazo in p['lazos']]
    vec = cq.Vector(*[10 * n[i] * p['dist'] for i in range(3)])
    return cq.Solid.extrudeLinear(wires[0], wires[1:], vec)

cuerpos = []   # (componente, nombre, idx, solido)
for c in d['componentes']:
    for b in c['cuerpos']:
        s = cuerpo_de(b['piezas'])
        cuerpos.append([c['nombre'], b['nombre'], b['idx'], s])
for corte in d['cortes']:
    herramienta = solido(corte['pieza'])
    for cu in cuerpos:
        if cu[0] == corte['comp'] and cu[2] < corte['antes_de']:
            cu[3] = cu[3].cut(herramienta)

invalidos = [c[1] for c in cuerpos if not c[3].isValid() or c[3].Volume() <= 0]
for c in d['componentes']:
    for b in c['cuerpos']:
        if b.get('material') or b.get('apariencia'): print('material', b['nombre'], b.get('material'), b.get('apariencia'))
print('cuerpos reconstruidos:', len(cuerpos), '| invalidos o volumen<=0:', invalidos or 'ninguno')

choques = []
bbs = [c[3].BoundingBox() for c in cuerpos]
for i, j in itertools.combinations(range(len(cuerpos)), 2):
    a, b = bbs[i], bbs[j]
    if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
        continue
    v = cuerpos[i][3].intersect(cuerpos[j][3]).Volume()
    if v > 1.0:
        choques.append((round(v, 1), cuerpos[i][0][11:], cuerpos[i][1], cuerpos[j][0][11:], cuerpos[j][1]))
print('choques (volumen comun > 1 mm3):', len(choques))
for ch in sorted(choques, reverse=True):
    print('  %9.1f mm3   %s/%s  <->  %s/%s' % ch)

bb = cq.Compound.makeCompound([c[3] for c in cuerpos]).BoundingBox()
print('envolvente: X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f' % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))

colores = {'Componente_Tapa_Sensor': (0.82, 0.84, 0.87), 'Componente_Instalacion_PROPUESTA': (0.35, 0.55, 0.75), 'Componente_Soporte': (0.55, 0.57, 0.60), 'Componente_Canal_Superior': (0.80, 0.82, 0.85),
           'Componente_Rampa_Inclinada': (0.62, 0.74, 0.86)}
especiales = {'PROPUESTA_backlight_IR': (0.95, 0.55, 0.1), 'carcasa': (0.8, 0.82, 0.85), 'PROPUESTA_camara': (0.1, 0.1, 0.12),
              'PROPUESTA_lente': (0.1, 0.1, 0.12), 'labio_vertedero': (0.8, 0.15, 0.12),
              'valvula_drenaje': (0.8, 0.15, 0.12), 'manija_valvula': (0.8, 0.15, 0.12),
              'acople_salida': (0.2, 0.55, 0.28), 'vidrio_protector': (0.55, 0.85, 0.95), 'PROPUESTA_acrilico': (0.55, 0.85, 0.95),
              'sumidero': (0.85, 0.7, 0.2), 'malla_cedazo': (0.25, 0.25, 0.28), 'marco_malla': (0.5, 0.5, 0.55), 'soporte_malla': (0.5, 0.5, 0.55), 'pasacables': (0.95, 0.95, 0.95), 'pantalla': (0.12, 0.12, 0.14), 'display': (0.85, 0.1, 0.1), 'carcasa_barra': (0.95, 0.55, 0.1), 'tapa_tobogan': (0.45, 0.6, 0.75), 'perilla': (0.1, 0.1, 0.12), 'agarradera': (0.1, 0.1, 0.12), 'boca_entrada': (0.3, 0.5, 0.8),
              'tubo_drenaje_agua': (0.3, 0.5, 0.8)}
grupos = {}
OCULTAR = os.environ.get('OCULTAR', '').split(',')
for comp, nombre, _, s in cuerpos:
    if nombre in OCULTAR: continue
    col = next((v for k, v in especiales.items() if nombre.startswith(k)), None)
    if col is None:
        col = (0.12, 0.12, 0.14) if nombre.startswith('neumatico') else colores[comp]
    grupos.setdefault(col, []).append(s)
os.makedirs(os.path.join(SP, 'fsim_stl'), exist_ok=True)
lineas = []
for i, (col, ss) in enumerate(grupos.items()):
    ruta = os.path.join(SP, 'fsim_stl', 'g%d.stl' % i)
    cq.exporters.export(cq.Compound.makeCompound(ss), ruta, tolerance=0.4, angularTolerance=0.2)
    lineas.append('color([%s]) import("%s");' % (','.join(map(str, col)), 'fsim_stl/g%d.stl' % i))
open(os.path.join(SP, 'fsim.scad'), 'w').write('\n'.join(lineas) + '\n')
