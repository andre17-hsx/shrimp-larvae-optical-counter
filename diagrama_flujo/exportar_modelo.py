# -*- coding: utf-8 -*-
"""Exporta el modelo REAL del prototipo (los cuerpos que produce el script de Fusion 360) como mallas de triangulos, mas
las lineas centrales del recorrido del agua. Escribe diagrama_flujo/modelo.json (mm, coordenadas de Fusion: X, Y, Z).
Se corre con el entorno que tiene CadQuery:   ..\\.venv_cad\\Scripts\\python.exe exportar_modelo.py
"""
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
VER = os.path.join(AQUI, '..', 'verificacion_estanqueidad')
sys.path.insert(0, VER)
os.chdir(VER)
import analisis_modelo as am  # noqa: E402

m, g, datos, cuerpos = am.cargar()
bodies = []
for comp, nombre, s in cuerpos:
    v, t = s.tessellate(1.5, 0.3)
    bodies.append({
        'n': nombre, 'c': comp,
        'v': [round(c, 1) for p in v for c in (p.x, p.y, p.z)],
        't': [i for tri in t for i in tri],
    })

# ---- lineas centrales del recorrido del agua (coordenadas de Fusion) ----
ZC, XE, ZE = g['ZC'], g['XE'], g['ZE']
T = m.T
xs, ys = m.XY_SUCCION
p_alto = m.PISCINA[4]
b_alto = m.BOMBA[4]
z_red = ZC - T - m.LARGO_DIFUSOR
z_imp = min(m.Z_IMPULSION, z_red - 140)
al = g['alfa']
ca, sa = math.cos(al), math.sin(al)
d = (-ca, 0.0, -sa)
r = m.D_SALIDA / 2.0
c = (XE - m.LARGO_EMBUDO * ca, 0.0, ZE + g['H_EMB'] / 2.0 - m.LARGO_EMBUDO * sa)
av = lambda p, v, k: (p[0] + v[0] * k, p[1] + v[1] * k, p[2] + v[2] * k)
boca = av(c, d, m.LARGO_TUBO + m.LARGO_ACOPLE)
largo = min(m.LARGO_MANGUERA_SALIDA, (boca[2] - m.ALTO_DESTINO - 100) / max(sa, 0.05))
fin = av(boca, d, largo)
rutas = {
    'succion': [(xs, m.Y_PISCINA, 120), (xs, m.Y_PISCINA, p_alto + 100), (xs, ys, p_alto + 100), (xs, ys, b_alto)],
    'impulsion': [(m.X_IMPULSION, m.Y_IMPULSION, b_alto), (m.X_IMPULSION, m.Y_IMPULSION, z_imp), (m.X_ENTRADA, m.Y_IMPULSION, z_imp),
                  (m.X_ENTRADA, 0, z_imp), (m.X_ENTRADA, 0, z_red)],
    'difusor': {'eje': (m.X_ENTRADA, 0), 'z0': z_red, 'z1': ZC - T, 'r0': m.D_MANGUERA / 2.0, 'r1': m.D_ENTRADA / 2.0},
    'embudo': {'xe': XE, 'ze': ZE, 'h': g['H_EMB'], 'alfa': math.degrees(al), 'c': c, 'boca': boca, 'fin': fin, 'r': r,
               'semiancho': m.ANCHO_CANAL / 2.0, 'largo_embudo': m.LARGO_EMBUDO, 'largo_tubo': m.LARGO_TUBO, 'largo_acople': m.LARGO_ACOPLE},
    'purga': [(m.X_DRENAJE, 0, ZC - m.PROF_SUMIDERO - 215 - T), (m.X_DRENAJE, 0, 120), (1400, 0, 120)],
    'piscina_origen': {'x0': m.PISCINA[0], 'x1': m.PISCINA[1], 'y0': m.PISCINA[2], 'y1': m.PISCINA[3], 'alto': m.PISCINA[4]},
    'canasta': (xs, m.Y_PISCINA, 60),
    'x_vertedero': m.X_VERTEDERO, 'zc': ZC, 'x_conteo_h': None,
}
dx1 = fin[0] + 150
rutas['piscina_destino'] = {'x0': dx1 - 1550, 'x1': dx1, 'y0': -800, 'y1': 800, 'alto': m.ALTO_DESTINO}
json.dump({'bodies': bodies, 'rutas': rutas}, open(os.path.join(AQUI, 'modelo.json'), 'w'), separators=(',', ':'))
print('cuerpos', len(bodies), 'triangulos', sum(len(b['t']) // 3 for b in bodies), 'embudo alfa %.1f' % math.degrees(al))
print('boca', [round(v) for v in boca], 'fin', [round(v) for v in fin], 'destino x', round(dx1 - 1550), round(dx1))
