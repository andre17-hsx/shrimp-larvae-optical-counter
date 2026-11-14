import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from estanq_lib import Region, buscar_fugas, agrupar

def caja(x, y, z, l, w, h):
    return cq.Solid.makeBox(l, w, h, cq.Vector(x, y, z))

def caso(nombre, hueco_x, paso):
    """Cubo hueco de 100 mm con paredes de 3 mm; la placa y-max empieza en x=hueco_x (3 = sin hueco)."""
    placas = {
        'fondo': caja(0, 0, 0, 100, 100, 3), 'tapa': caja(0, 0, 97, 100, 100, 3),
        'x_min': caja(0, 0, 3, 3, 100, 94), 'x_max': caja(97, 0, 3, 3, 100, 94),
        'y_min': caja(3, 0, 3, 94, 3, 94), 'y_max': caja(hueco_x, 97, 3, 97 - hueco_x, 3, 94),
    }
    reg = Region(nombre, (-20, -20, -20), (120, 120, 120), paso)
    for n, s in placas.items():
        reg.agregar(n, s)
    reg.preparar()
    reg.semilla('dentro', (50, 50, 50))
    reg.semilla('fuera', (50, 112, 50))
    t = time.time()
    fugas = buscar_fugas(reg, [('dentro', 'fuera')])
    grupos = agrupar(fugas, paso)
    print('%-30s paso %.1f mm -> %d punto(s), %d fuga(s)  [%.1f s]' % (nombre, paso, len(fugas), len(grupos), time.time() - t))
    for g in grupos:
        print('     centro', [round(float(c), 1) for c in g['centro']], 'caja', [round(float(c)) for c in g['caja'][0]],
              '->', [round(float(c)) for c in g['caja'][1]], 'apertura ~%.0f-%.0f mm' % g['apertura_mm'], g['cerca'])

for paso in (2.0, 1.0):
    caso('cubo cerrado (sin hueco)', 3, paso)
    caso('rendija de 1 mm', 4, paso)
    caso('rendija de 2 mm', 5, paso)
    caso('rendija de 4 mm', 7, paso)
