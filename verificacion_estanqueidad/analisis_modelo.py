# -*- coding: utf-8 -*-
"""Comprobacion de estanqueidad del modelo del contador (script de Fusion 360 simulado)."""
import os, sys, time, json, math, importlib.util
import numpy as np
import cadquery as cq

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from estanq_lib import Region, buscar_fugas, agrupar
import fake_adsk

SCRIPT = os.environ.get('SCRIPT_MODELO', os.path.join(AQUI, '..', 'Fusion360_VAKI_Macro', 'Fusion360_VAKI_Macro.py'))
EXCL_COMP = {'Componente_Soporte', 'Componente_Tapa_Sensor', 'Componente_Instalacion_PROPUESTA'}
EXCL_NOM = {'PROPUESTA_camara_lineal', 'PROPUESTA_lente', 'PROPUESTA_backlight_IR'}


def cargar():
    datos = fake_adsk.ejecutar(SCRIPT, os.path.join(AQUI, 'fusion_sim.json'))
    assert not datos['cortes'], 'hay cortes de extrusion sin tratar'
    spec = importlib.util.spec_from_file_location('modelo_script', SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    g = m.geometria()
    ruta = os.path.join(AQUI, 'reconstruir.py')
    ns = {'__file__': ruta}
    exec(open(ruta, encoding='utf-8').read().split('cuerpos = []')[0], ns)
    cuerpos = []
    for c in datos['componentes']:
        for b in c['cuerpos']:
            cuerpos.append((c['nombre'], b['nombre'], ns['cuerpo_de'](b['piezas'])))
    return m, g, datos, cuerpos


def barreras(cuerpos):
    return [(n, s) for comp, n, s in cuerpos if comp not in EXCL_COMP and n not in EXCL_NOM]


def tapon_salida(datos):
    for c in datos['componentes']:
        for b in c['cuerpos']:
            if b['nombre'] == 'acople_salida':
                p = b['piezas'][0]
                cx, cy = np.array(p['lazos'][0]).mean(0)
                o, u, v, n = (np.array(p[k]) for k in ('o', 'u', 'v', 'n'))
                fin = 10 * (o + u * cx + v * cy) + 10 * n * p['dist']
                d = n * np.sign(p['dist'])
                return cq.Solid.makeCylinder(105, 3, cq.Vector(*fin), cq.Vector(*d))
    raise RuntimeError('no se encontro acople_salida')


def analizar(reg, cuerpos_b, extras, semillas, pares, etiqueta, max_iter=40):
    t0 = time.time()
    for n, s in cuerpos_b + extras:
        reg.agregar(n, s)
    t1 = time.time()
    reg.preparar()
    for nombre, punto in semillas.items():
        reg.semilla(nombre, punto)
    t2 = time.time()
    print('[%s] celdas %s (%.1f M) paso %.0f mm | voxelizado %.0f s, preparacion %.0f s' %
          (etiqueta, tuple(reg.dims), np.prod(reg.dims) / 1e6, reg.paso, t1 - t0, t2 - t1), flush=True)
    print('      semillas (mm):', {k: [round(float(c), 1) for c in reg.a_mm(v)] for k, v in reg.semillas.items()},
          flush=True)
    from scipy import ndimage as ndi
    lab, _ = ndi.label(reg.fluido)
    vol = {k: float((lab == lab[v]).sum()) * reg.paso ** 3 / 1e6 for k, v in reg.semillas.items()}
    print('      volumen conectado a cada semilla (L):', {k: round(x, 1) for k, x in vol.items()}, flush=True)
    del lab
    fugas = buscar_fugas(reg, pares, max_iter=max_iter)
    grupos = agrupar(fugas, reg.paso)
    print('[%s] %d punto(s) de fuga en %d grupo(s)  [%.0f s]' % (etiqueta, len(fugas), len(grupos),
                                                                time.time() - t2), flush=True)
    for gr in grupos:
        print('   %s -> %s | %d punto(s) | centro %s | caja %s..%s | apertura ~%.0f-%.0f mm | cerca de %s' %
              (gr['par'][0], gr['par'][1], gr['n_puntos'], [round(float(c)) for c in gr['centro']],
               [round(float(c)) for c in gr['caja'][0]], [round(float(c)) for c in gr['caja'][1]],
               gr['apertura_mm'][0], gr['apertura_mm'][1], gr['cerca']), flush=True)
    return grupos


def main(que):
    m, g, datos, cuerpos = cargar()
    b = barreras(cuerpos)
    quitar = [x for x in os.environ.get('QUITAR', '').split(',') if x]
    if quitar:
        b = [(n, sh) for n, sh in b if n not in quitar]
        print('*** PRUEBA DE DEFECTO PROVOCADO: se quitan', quitar, flush=True)
    ag = os.environ.get('AGUJERO')
    if ag:                                   # defecto provocado: agujero pasante en la pared derecha del cajon
        x, y, z, r = [float(v) for v in ag.split(',')]
        cil = cq.Solid.makeCylinder(r, 30, cq.Vector(x, y - 15, z), cq.Vector(0, 1, 0))
        b = [(n, sh.cut(cil) if n == 'pared_lateral_der' else sh) for n, sh in b]
        print('*** PRUEBA: agujero de radio %.0f mm en pared_lateral_der en (%.0f, %.0f, %.0f)' % (r, x, y, z), flush=True)
    ZC, ZE, XE, T = g['ZC'], g['ZE'], g['XE'], m.T
    zf = ZC - m.PROF_SUMIDERO
    c2, s2 = math.cos(g['t2']), math.sin(g['t2'])
    resultados = {}
    print('modelo: %d cuerpos, %d como barrera de agua' % (len(cuerpos), len(b)), flush=True)

    if 'A1' in que:
        tap = [('TAPON_drenaje', cq.Solid.makeCylinder(53, 3, cq.Vector(m.X_DRENAJE, 0, zf - T - 23),
                                                       cq.Vector(0, 0, 1)))]
        reg = Region('cajon', (1780, -560, ZC - 145), (2850, 560, ZC + g['NIVEL'] + 2), 2.0, zcap=ZC + g['NIVEL'])
        resultados['A1'] = analizar(
            reg, b, tap,
            {'agua': (2200, 0, ZC + 30), 'sumidero': (1990, 50, ZC - 95), 'exterior': (2300, -535, ZC + 25)},
            [('agua', 'exterior'), ('sumidero', 'exterior'), ('agua', 'sumidero')],
            'cajon + malla + sumidero')

    if 'A3' in que:
        # difusor de entrada: cono bajo el fondo del cajon. La manguera (instalacion, no es barrera) se cierra con un
        # tapon bajo su extremo inferior.
        z_b = ZC - T - m.LARGO_DIFUSOR
        tap = [('TAPON_difusor', cq.Solid.makeCylinder(m.D_MANGUERA / 2.0 + 5, 3, cq.Vector(m.X_ENTRADA, 0, z_b - 3),
                                                        cq.Vector(0, 0, 1)))]
        reg = Region('difusor', (m.X_ENTRADA - 140, -140, z_b - 10), (m.X_ENTRADA + 140, 140, ZC + 20), 2.0, zcap=ZC + 20)
        resultados['A3'] = analizar(
            reg, b, tap,
            {'agua': (m.X_ENTRADA, 0, ZC - 200), 'exterior': (m.X_ENTRADA + 125, 0, ZC - 300)},
            [('agua', 'exterior')], 'difusor de entrada')

    if 'A2b' in que:
        zx = lambda x: m.z_fondo(g, x)
        q = (XE + m.S_ESCANEO * c2 + 20 * s2, 0.0, ZE - T + m.S_ESCANEO * s2 - 20 * c2)
        reg = Region('tobogan', (800, -300, ZE - 110), (1830, 300, ZC + 112), 3.0)
        resultados['A2b'] = analizar(
            reg, b, [],
            {'agua': (1300, 0, zx(1300) + 12), 'exterior': (1300, 285, zx(1300) + 12), 'carcasa': q},
            [('agua', 'exterior'), ('agua', 'carcasa'), ('carcasa', 'exterior')],
            'tobogan + carcasa backlight')

    if 'A2a' in que:
        tap = tapon_salida(datos)
        bb = tap.BoundingBox()
        al = g['alfa']
        ca, sa = math.cos(al), math.sin(al)
        H = g['H_EMB']
        c = np.array([XE - m.LARGO_EMBUDO * ca, 0.0, ZE + H / 2.0 - m.LARGO_EMBUDO * sa])
        p_in = c + np.array([ca, 0.0, sa]) * 250
        reg = Region('embudo', (bb.xmin - 25, -300, bb.zmin - 25), (840, 300, ZE + H + 40), 3.0)
        resultados['A2a'] = analizar(
            reg, b, [('TAPON_salida', tap)],
            {'agua': tuple(p_in), 'exterior': ((bb.xmin + 840) / 2, 285, (bb.zmin + ZE) / 2)},
            [('agua', 'exterior')], 'embudo + tubo + acople')

    salida = {k: [{'par': list(g_['par']), 'n_puntos': g_['n_puntos'], 'centro': g_['centro'].tolist(),
                   'caja': [g_['caja'][0].tolist(), g_['caja'][1].tolist()],
                   'apertura_mm': list(g_['apertura_mm']), 'cerca': g_['cerca'],
                   'puntos': g_['puntos'].tolist()} for g_ in v] for k, v in resultados.items()}
    json.dump(salida, open(os.path.join(AQUI, 'fugas_%s%s.json' % ('_'.join(que), '_prueba' if quitar else '')), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:] or ['A1', 'A2b', 'A2a', 'A3'])
