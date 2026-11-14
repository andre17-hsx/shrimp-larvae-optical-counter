# -*- coding: utf-8 -*-
"""Vista de la lamina de agua de un caso de OpenFOAM en ParaView.

Uso (desde WSL, se abre en tu pantalla con WSLg):
    paraview --script=<repo>/cfd_3d/scripts/paraview/ver_lamina.py
o dentro de ParaView:  View > Python Shell > Run Script.

Variable de entorno CASO_FOAM = ruta del archivo .foam (por defecto el caso p2_medio_grueso).
Muestra la superficie libre del agua (alpha.water = 0,5) coloreada por velocidad, y las paredes y la malla translucidas.
Para seguir un calculo en marcha: boton "Reload Files" (icono de flechas circulares en Properties) y luego "Last Frame".
"""
import os

from paraview.simple import *  # noqa: F403

# El calculo simula solo el semiancho y >= 0 (plano de simetria en y = 0). Por defecto se muestra reflejado para ver la
# maquina completa; VER_MITAD=1 muestra solo lo simulado.
MITAD = os.environ.get('VER_MITAD', '0') == '1'

CASO = os.environ.get('CASO_FOAM', os.path.expanduser('~/cfd/casos/p2_medio_grueso/caso.foam'))

vista = GetActiveViewOrCreate('RenderView')
vista.UseColorPaletteForBackground = 0
vista.Background = [0.12, 0.13, 0.16]

# ---- volumen de fluido -> superficie libre
rf = OpenFOAMReader(registrationName='fluido', FileName=CASO)
rf.CaseType = 'Decomposed Case'
rf.MeshRegions = ['internalMesh']
rf.CellArrays = ['alpha.water', 'U']
rf.UpdatePipelineInformation()
pf = CellDatatoPointData(registrationName='a_puntos', Input=rf)
sup = Contour(registrationName='superficie_libre', Input=pf)
sup.ContourBy = ['POINTS', 'alpha.water']
sup.Isosurfaces = [0.5]
sup.ComputeScalars = 1
sup_v = sup if MITAD else Reflect(Input=sup, PlaneMode='Y Min')   # copia reflejada en y < 0
d = Show(sup_v, vista)
ColorBy(d, ('POINTS', 'U', 'Magnitude'))
lut = GetColorTransferFunction('U')
lut.ApplyPreset('Turbo', True)
lut.RescaleTransferFunction(0.0, 3.0)
d.SetScalarBarVisibility(vista, True)
GetScalarBar(lut, vista).Title = 'velocidad del agua (m/s)'

# ---- paredes y malla, translucidas
rp = OpenFOAMReader(registrationName='paredes', FileName=CASO)
rp.CaseType = 'Decomposed Case'
rp.MeshRegions = ['patch/paredes', 'patch/malla']
rp.CellArrays = []
rp_v = rp if MITAD else Reflect(Input=rp, PlaneMode='Y Min')
dp = Show(rp_v, vista)
dp.ColorArrayName = ['POINTS', '']
dp.DiffuseColor = [0.75, 0.78, 0.85]
dp.Opacity = 0.12

# ---- ultimo tiempo escrito y camara
escena = GetAnimationScene()
escena.UpdateAnimationUsingDataTimeSteps()
escena.GoToLast()
vista.CameraPosition = [0.30, -0.70, 0.55] if MITAD else [0.35, -1.05, 0.70]
vista.CameraFocalPoint = [-0.12, 0.22, 0.06] if MITAD else [-0.12, 0.0, 0.05]
vista.CameraViewUp = [0.0, 0.0, 1.0]
Render(vista)
