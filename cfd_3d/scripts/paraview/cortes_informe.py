# -*- coding: utf-8 -*-
"""Cortes longitudinales del campo medio (y = 0.10 m) para el informe: velocidad en el agua (alpha medio >= 0.5) y contorno de
las paredes del dominio.

    pvbatch cortes_informe.py <caso_dir_en_WSL> <carpeta_salida>
"""
import os
import sys

from paraview.simple import *  # noqa: F403

caso, salida = sys.argv[1], sys.argv[2]
foam = os.path.join(caso, 'caso.foam')
Y0 = float(os.environ.get('Y0', '0.10'))


TIEMPO = None


def vista_ortogonal(cx, cz, escala, ancho, alto):
    v = CreateRenderView()
    v.ViewSize = [ancho, alto]
    v.UseColorPaletteForBackground = 0
    v.Background = [1, 1, 1]
    v.OrientationAxesVisibility = 0
    v.CameraParallelProjection = 1
    v.CameraPosition = [cx, -3.0, cz]
    v.CameraFocalPoint = [cx, Y0, cz]
    v.CameraViewUp = [0, 0, 1]
    v.CameraParallelScale = escala
    v.ViewTime = TIEMPO
    return v


rf = OpenFOAMReader(FileName=foam)
rf.CaseType = 'Decomposed Case'
rf.MeshRegions = ['internalMesh']
rf.CellArrays = ['alpha.waterMean', 'UMean']
rf.UpdatePipelineInformation()
t = list(rf.TimestepValues)[-1]
TIEMPO = t
mb = MergeBlocks(Input=rf)
# recorte por celdas completas (las celdas poliedricas de snappy no siempre se pueden cortar con Slice)
sl = Clip(Input=mb)
sl.ClipType = 'Plane'
sl.ClipType.Origin = [0, Y0, 0]
sl.ClipType.Normal = [0, 1, 0]
sl.Crinkleclip = 1
sl.Invert = 0
sl.UpdatePipeline(t)
print('limites tras el recorte (y debe empezar en %.2f):' % Y0, sl.GetDataInformation().GetBounds())
th = Threshold(Input=sl)
th.Scalars = ['CELLS', 'alpha.waterMean']
th.LowerThreshold = 0.5
th.UpperThreshold = 1.2
th.ThresholdMethod = 'Between'
calc = Calculator(Input=th, AttributeType='Cell Data', ResultArrayName='vel', Function='mag(UMean)')

rp = OpenFOAMReader(FileName=foam)
rp.CaseType = 'Decomposed Case'
rp.MeshRegions = ['patch/paredes', 'patch/malla']
rp.CellArrays = []
rm = MergeBlocks(Input=rp)
sp = Slice(Input=rm)
sp.SliceType = 'Plane'
sp.SliceType.Origin = [0, Y0, 0]
sp.SliceType.Normal = [0, 1, 0]

for nombre, f in (('recorte', sl), ('agua', th), ('vel', calc)):
    f.UpdatePipeline(t)
    print(nombre, 'celdas:', f.GetDataInformation().GetNumberOfCells(), 'arrays celda:', [f.CellData.GetArray(i).GetName() for i in range(len(f.CellData))] if hasattr(f.CellData, 'GetArray') else '?')
lut = GetColorTransferFunction('vel')
lut.ApplyPreset('Turbo', True)


def foto(nombre, cx, cz, escala, ancho, alto, vmax):
    v = vista_ortogonal(cx, cz, escala, ancho, alto)
    d = Show(calc, v)
    d.Representation = 'Surface'
    ColorBy(d, ('CELLS', 'vel'))
    lut.RescaleTransferFunction(0.0, vmax)
    d.SetScalarBarVisibility(v, False)
    dl = Show(sp, v)
    dl.ColorArrayName = ['POINTS', '']
    dl.DiffuseColor = [0.12, 0.16, 0.2]
    dl.AmbientColor = [0.12, 0.16, 0.2]
    dl.LineWidth = 3.0
    v.ViewTime = t
    Render(v)
    SaveScreenshot(os.path.join(salida, nombre), v, ImageResolution=[ancho, alto])
    Hide(calc, v)
    Hide(sp, v)
    print('listo', nombre, t)


os.makedirs(salida, exist_ok=True)
foto('corte_completo.png', -0.11, 0.09, 0.17, 2200, 560, 2.0)
foto('corte_cresta.png', 0.0, 0.085, 0.10, 1800, 600, 1.0)
