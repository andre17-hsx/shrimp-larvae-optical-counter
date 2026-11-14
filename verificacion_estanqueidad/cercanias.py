# -*- coding: utf-8 -*-
"""Rendijas finas: pares de cuerpos de la barrera de agua que NO se tocan pero quedan a menos de 3 mm."""
import os, sys, time, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analisis_modelo as A
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

TOL_CERCA = 8.0      # mm: cubre la zona ciega entre esta medicion y la resolucion de las celdas (3-6 mm)
TOL_CONTACTO = 0.01  # mm: por debajo de esto se consideran en contacto (cierre)


def main():
    m, g, datos, cuerpos = A.cargar()
    b = A.barreras(cuerpos)
    cajas = []
    for n, s in b:
        bb = s.BoundingBox()
        cajas.append((bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
    t0 = time.time()
    contacto, finas, medidas = 0, [], 0
    for i, j in itertools.combinations(range(len(b)), 2):
        a, c = cajas[i], cajas[j]
        if (a[0] > c[1] + TOL_CERCA or c[0] > a[1] + TOL_CERCA or a[2] > c[3] + TOL_CERCA or
                c[2] > a[3] + TOL_CERCA or a[4] > c[5] + TOL_CERCA or c[4] > a[5] + TOL_CERCA):
            continue
        d = BRepExtrema_DistShapeShape(b[i][1].wrapped, b[j][1].wrapped).Value()
        medidas += 1
        if d <= TOL_CONTACTO:
            contacto += 1
        elif d <= TOL_CERCA:
            finas.append((d, b[i][0], b[j][0]))
    finas.sort()
    print('cuerpos en la barrera: %d | pares medidos con distancia exacta: %d | en contacto (cierran): %d | '
          'separados por 0,01-3 mm: %d  [%.0f s]' % (len(b), medidas, contacto, len(finas), time.time() - t0))
    for d, x, y in finas:
        print('   %.3f mm   %s  <->  %s' % (d, x, y))
    json.dump({'pares': medidas, 'contacto': contacto, 'finas': finas},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cercanias.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
