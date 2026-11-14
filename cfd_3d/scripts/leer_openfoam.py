# -*- coding: utf-8 -*-
"""Lectura minima de campos ASCII de OpenFOAM (internalField) sin dependencias fuera de numpy."""
import re
import numpy as np


def leer_campo(ruta):
    """Devuelve un array (N,) para escalares o (N, 3) para vectores. Soporta 'uniform' y 'nonuniform'."""
    t = open(ruta, encoding='utf-8', errors='replace').read()
    m = re.search(r'internalField\s+uniform\s+([^;]+);', t)
    if m:
        v = m.group(1).strip()
        if v.startswith('('):
            return np.array([float(x) for x in v.strip('()').split()])
        return float(v)
    m = re.search(r'internalField\s+nonuniform\s+List<(scalar|vector|symmTensor|tensor)>\s*(\d+)\s*\(', t)
    if not m:
        raise ValueError('no se pudo leer internalField en %s' % ruta)
    n = int(m.group(2))
    cuerpo = t[m.end():]
    if m.group(1) == 'scalar':
        fin = cuerpo.index('\n)')
        return np.array(cuerpo[:fin].split(), float)[:n]
    fin = cuerpo.index('\n)\n')
    filas = re.findall(r'\(([^()]*)\)', cuerpo[:fin])
    a = np.array([[float(x) for x in f.split()] for f in filas])
    return a[:n]
