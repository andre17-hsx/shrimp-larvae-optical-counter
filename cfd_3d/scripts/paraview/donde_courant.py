# -*- coding: utf-8 -*-
"""Donde se concentra el numero de Courant (lo que limita el paso de tiempo) en el ultimo tiempo escrito de un caso.

    pvbatch donde_courant.py <caso_dir_en_WSL> <deltaT>
"""
import os
import sys

import numpy as np
from paraview.simple import *  # noqa: F403
from paraview import servermanager
from vtk.numpy_interface import dataset_adapter as dsa

caso = sys.argv[1]
dt = float(sys.argv[2])
foam = os.path.join(caso, 'caso.foam')
if not os.path.exists(foam):
    open(foam, 'w').close()
r = OpenFOAMReader(FileName=foam)
r.CaseType = 'Decomposed Case'
r.MeshRegions = ['internalMesh']
r.CellArrays = ['alpha.water', 'U']
r.UpdatePipelineInformation()
t = list(r.TimestepValues)[-1]
tam = CellSize(Input=r)
cen = CellCenters(Input=tam)
cen.UpdatePipeline(t)
obj = servermanager.Fetch(cen)
blk = dsa.WrapDataObject(obj)
P = np.vstack([np.asarray(a) for a in blk.Points.Arrays]) if hasattr(blk.Points, 'Arrays') else np.asarray(blk.Points)
U = np.vstack([np.asarray(a) for a in blk.PointData['U'].Arrays]) if hasattr(blk.PointData['U'], 'Arrays') else np.asarray(blk.PointData['U'])
V = np.concatenate([np.asarray(a) for a in blk.PointData['Volume'].Arrays]) if hasattr(blk.PointData['Volume'], 'Arrays') else np.asarray(blk.PointData['Volume'])
A = np.concatenate([np.asarray(a) for a in blk.PointData['alpha.water'].Arrays]) if hasattr(blk.PointData['alpha.water'], 'Arrays') else np.asarray(blk.PointData['alpha.water'])
h = V ** (1.0 / 3.0)
u = np.linalg.norm(U, axis=1)
co = u * dt / h
print('t = %s s | celdas %d | Co max estimado %.2f | |U| max %.2f m/s' % (t, len(V), co.max(), u.max()))
orden = np.argsort(-co)[:15]
print('   x (m)   y (m)   z (m)   |U| m/s   tamano mm   alpha   Co')
for i in orden:
    print('  %6.3f  %6.3f  %6.3f   %6.2f    %6.2f    %5.2f   %5.2f' % (P[i, 0], P[i, 1], P[i, 2], u[i], h[i] * 1e3, A[i], co[i]))
for nombre, m in (('aire (alpha<0.1)', A < 0.1), ('agua (alpha>0.9)', A > 0.9)):
    if m.any():
        print('%s: |U| max %.2f m/s, Co max %.2f, 99 percentil Co %.2f' % (nombre, u[m].max(), co[m].max(), np.percentile(co[m], 99)))
