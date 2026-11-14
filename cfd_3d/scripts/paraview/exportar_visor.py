# -*- coding: utf-8 -*-
"""Exporta de un caso 3D (medio ancho) los datos para el visor web: superficie libre del agua (campo medio, coloreada por la
velocidad), lineas de corriente del campo medio y una imagen de las lineas.

    pvbatch exportar_visor.py <caso_dir_en_WSL> <carpeta_salida> [n_semillas]
Escribe en <carpeta_salida>: superficie_pos.f32, superficie_vel.f32, superficie_idx.u32, lineas_pos.f32, lineas_vel.f32,
lineas_s.f32 (abscisa curvilinea), lineas_n.u32 (puntos por linea) y meta.json. Coordenadas en metros (x aguas abajo,
y ancho desde el eje, z hacia arriba, z = 0 en el fondo del cajon).
"""
import json
import os
import sys

import numpy as np
from paraview.simple import *  # noqa: F403
from paraview import servermanager
from vtk.util import numpy_support as ns

caso = sys.argv[1]
salida = sys.argv[2]
n_sem = int(sys.argv[3]) if len(sys.argv) > 3 else 360
os.makedirs(salida, exist_ok=True)
foam = os.path.join(caso, 'caso.foam')
if not os.path.exists(foam):
    open(foam, 'w').close()

rf = OpenFOAMReader(FileName=foam)
rf.CaseType = 'Decomposed Case'
rf.MeshRegions = ['internalMesh']
rf.CellArrays = ['alpha.waterMean', 'UMean']
rf.UpdatePipelineInformation()
tiempos = list(rf.TimestepValues)
t = tiempos[-1]
mb = MergeBlocks(Input=rf)
pd = CellDatatoPointData(Input=mb)
pd.UpdatePipeline(t)

# ---------------- superficie libre (alpha medio = 0.5) ----------------
sup = Contour(Input=pd)
sup.ContourBy = ['POINTS', 'alpha.waterMean']
sup.Isosurfaces = [0.5]
sup.ComputeScalars = 0
tri = Triangulate(Input=sup)
red = Decimate(Input=tri)
red.TargetReduction = float(os.environ.get('REDUCCION', '0.55'))
red.PreserveTopology = 1
red.UpdatePipeline(t)
s = servermanager.Fetch(red)
P = ns.vtk_to_numpy(s.GetPoints().GetData()).astype(np.float32)
V = ns.vtk_to_numpy(s.GetPointData().GetArray('UMean')).astype(np.float32)
conn = ns.vtk_to_numpy(s.GetPolys().GetConnectivityArray()).astype(np.uint32)
off = ns.vtk_to_numpy(s.GetPolys().GetOffsetsArray())
assert (np.diff(off) == 3).all(), 'la superficie no es de triangulos'
vel = np.linalg.norm(V, axis=1).astype(np.float32)
P.tofile(os.path.join(salida, 'superficie_pos.f32'))
vel.tofile(os.path.join(salida, 'superficie_vel.f32'))
conn.tofile(os.path.join(salida, 'superficie_idx.u32'))
print('superficie: %d vertices, %d triangulos, |U| %.2f..%.2f' % (len(P), len(conn) // 3, vel.min(), vel.max()))

# ---------------- lineas de corriente del campo medio ----------------
st = StreamTracer(Input=pd, SeedType='Point Cloud')
st.Vectors = ['POINTS', 'UMean']
st.IntegrationDirection = 'FORWARD'
st.IntegratorType = 'Runge-Kutta 4-5'
st.MaximumStreamlineLength = float(os.environ.get('LARGO_MAX', '4.0'))
st.MaximumSteps = 20000
st.TerminalSpeed = 5e-3
st.SeedType.Center = [-0.582, 0.05, -0.02]      # dentro del tubo de entrada (disco de radio 0,127 m en z = -0,06)
st.SeedType.Radius = 0.06
st.SeedType.NumberOfPoints = n_sem
st.UpdatePipeline(t)
L = servermanager.Fetch(st)
Pl = ns.vtk_to_numpy(L.GetPoints().GetData()).astype(np.float64)
Ul = ns.vtk_to_numpy(L.GetPointData().GetArray('UMean')).astype(np.float64)
Al = ns.vtk_to_numpy(L.GetPointData().GetArray('alpha.waterMean')).astype(np.float64)
lc = ns.vtk_to_numpy(L.GetLines().GetConnectivityArray())
lo = ns.vtk_to_numpy(L.GetLines().GetOffsetsArray())
print('lineas de corriente crudas:', len(lo) - 1)
ds = float(os.environ.get('DS', '0.006'))
pos, veloc, abs_s, cuenta = [], [], [], []
cortadas = 0
motivos = {'llega_lamina': 0, 'sale_del_agua_antes': 0, 'sale_del_agua_en_lamina': 0, 'se_detiene_en_agua': 0}
for k in range(len(lo) - 1):
    idx = lc[lo[k]:lo[k + 1]]
    # solo agua: la linea se corta en el primer punto con alpha medio < 0.5 (el campo medio mezcla fases en la interfaz y
    # una linea puede pasar al aire y parecer que 'sale disparada')
    fuera = np.where(Al[idx] < 0.5)[0]
    x_max_agua = Pl[idx[:fuera[0]] if len(fuera) else idx][:, 0].max() if (len(fuera) == 0 or fuera[0] > 0) else -9
    if len(fuera):
        cortadas += 1
        idx = idx[:fuera[0]]
        motivos['sale_del_agua_en_lamina' if x_max_agua > 0.15 else 'sale_del_agua_antes'] += 1
    else:
        motivos['llega_lamina' if x_max_agua > 0.15 else 'se_detiene_en_agua'] += 1
    if len(idx) < 5:
        continue
    p = Pl[idx]
    u = np.linalg.norm(Ul[idx], axis=1)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    sc = np.concatenate([[0.0], np.cumsum(seg)])
    if sc[-1] < 0.05:
        continue
    n = max(int(sc[-1] / ds), 8)
    g = np.linspace(0, sc[-1], n)
    pos.append(np.stack([np.interp(g, sc, p[:, i]) for i in range(3)], axis=1))
    veloc.append(np.interp(g, sc, u))
    abs_s.append(g)
    cuenta.append(n)
pos = np.concatenate(pos).astype(np.float32)
veloc = np.concatenate(veloc).astype(np.float32)
abs_s = np.concatenate(abs_s).astype(np.float32)
cuenta = np.array(cuenta, dtype=np.uint32)
pos.tofile(os.path.join(salida, 'lineas_pos.f32'))
veloc.tofile(os.path.join(salida, 'lineas_vel.f32'))
abs_s.tofile(os.path.join(salida, 'lineas_s.f32'))
cuenta.tofile(os.path.join(salida, 'lineas_n.u32'))
sale = sum(1 for k in range(len(cuenta)))
print('lineas: %d, puntos %d, ds %.1f mm | cortadas al salir del agua: %d' % (len(cuenta), len(pos), ds * 1e3, cortadas))
print('motivos de fin de las lineas:', motivos)
json.dump({'motivos': motivos, 't': float(t), 'ds': ds, 'lineas': int(len(cuenta)), 'puntos': int(len(pos)), 'vertices': int(len(P)),
           'triangulos': int(len(conn) // 3)}, open(os.path.join(salida, 'meta.json'), 'w'))
