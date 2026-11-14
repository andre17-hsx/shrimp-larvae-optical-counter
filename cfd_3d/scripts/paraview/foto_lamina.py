# -*- coding: utf-8 -*-
"""Foto (PNG) de la lamina de agua en el ultimo tiempo escrito de un caso, sin abrir la ventana de ParaView.

    pvbatch foto_lamina.py <caso_dir_en_WSL> <salida.png> [velocidad_max]
Ejemplo:
    pvbatch foto_lamina.py ~/cfd/casos/p2_medio_grueso /tmp/lamina.png
"""
import os
import sys

from paraview.simple import *  # noqa: F403

# El calculo simula solo el semiancho y >= 0 (plano de simetria en y = 0). Por defecto se muestra reflejado para ver la
# maquina completa; VER_MITAD=1 muestra solo lo simulado.
MITAD = os.environ.get('VER_MITAD', '0') == '1'

caso = sys.argv[1]
salida = sys.argv[2]
vmax = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
foam = os.path.join(caso, 'caso.foam')
if not os.path.exists(foam):
    open(foam, 'w').close()

vista = CreateRenderView()
vista.ViewSize = [1600, 900]
vista.UseColorPaletteForBackground = 0
vista.Background = [0.12, 0.13, 0.16]
vista.OrientationAxesVisibility = 1

rf = OpenFOAMReader(FileName=foam)
rf.CaseType = 'Decomposed Case' if os.path.isdir(os.path.join(caso, 'processor0')) else 'Reconstructed Case'
rf.MeshRegions = ['internalMesh']
rf.CellArrays = ['alpha.water', 'U']
rf.UpdatePipelineInformation()
tiempos = list(rf.TimestepValues) if hasattr(rf.TimestepValues, '__iter__') else [rf.TimestepValues]
t = tiempos[-1]
pf = CellDatatoPointData(Input=rf)
sup = Contour(Input=pf)
sup.ContourBy = ['POINTS', 'alpha.water']
sup.Isosurfaces = [0.5]
sup.ComputeScalars = 1
sup_v = sup if MITAD else Reflect(Input=sup, PlaneMode='Y Min')   # copia reflejada en y < 0
d = Show(sup_v, vista)
ColorBy(d, ('POINTS', 'U', 'Magnitude'))
lut = GetColorTransferFunction('U')
lut.ApplyPreset('Turbo', True)
lut.RescaleTransferFunction(0.0, vmax)
d.SetScalarBarVisibility(vista, True)
GetScalarBar(lut, vista).Title = 'velocidad (m/s)'

rp = OpenFOAMReader(FileName=foam)
rp.CaseType = rf.CaseType
rp.MeshRegions = ['patch/paredes', 'patch/malla']
rp.CellArrays = []
rp_v = rp if MITAD else Reflect(Input=rp, PlaneMode='Y Min')
dp = Show(rp_v, vista)
dp.ColorArrayName = ['POINTS', '']
dp.DiffuseColor = [0.75, 0.78, 0.85]
dp.Opacity = 0.12

vista.ViewTime = t
vista.CameraPosition = [0.30, -0.70, 0.55] if MITAD else [0.35, -1.05, 0.70]
vista.CameraFocalPoint = [-0.12, 0.22, 0.06] if MITAD else [-0.12, 0.0, 0.05]
vista.CameraViewUp = [0.0, 0.0, 1.0]
Render(vista)
SaveScreenshot(salida, vista, ImageResolution=[1600, 900])
print('foto guardada en %s (t = %s s)' % (salida, t))
