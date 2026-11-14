# -*- coding: utf-8 -*-
"""Genera un caso de OpenFOAM (interFoam + kOmegaSST) sobre el dominio del modelo, mallado con snappyHexMesh.

Requiere haber corrido antes geometria_cfd.py (STL en ../geometria). Modos:

  losa   corte 2D del modelo (ancho pequeno con simetria a ambos lados): fase 1, cresta y primera parte del tobogan.
  medio  semiancho 3D del cajon, estrechamiento, cresta y tobogan recto: fase 2.

    python caso_snappy.py <nombre> --modo losa --base 8e-3 --n-pelicula 4 --n-cresta 5 --n-sup 3 --Q 10 --tfin 8 --np 4
"""
import argparse
import json
import math
import os
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(AQUI, '..', 'geometria')
GEO_PREF = None
CASOS = os.path.join(AQUI, '..', 'casos')

CAB = """FoamFile
{
    version     2.0;
    format      ascii;
    class       %s;
    object      %s;
}
"""


def w(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)


def cab(clase, obj):
    return CAB % (clase, obj)


PARCHES = ('inlet', 'outlet', 'atmosphere', 'symmetry', 'malla', 'paredes')


def campos(d, U0, k0, w0, ks):
    """Condiciones de contorno por parche. inlet: caudal con altura variable; atmosphere: presion total."""
    def bloque(nombre, dic):
        return '    %s\n    {\n%s\n    }\n' % (nombre, '\n'.join('        %s' % l for l in dic))

    nut_pared = ['type nutkRoughWallFunction;', 'Ks uniform %g;' % ks, 'Cs uniform 0.5;', 'value uniform 0;'] if ks > 0 else \
        ['type nutkWallFunction;', 'value uniform 0;']
    sim = ['type symmetry;']
    # U
    U = cab('volVectorField', 'U') + 'dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField\n{\n'
    U += bloque('inlet', ['type variableHeightFlowRateInletVelocity;', 'flowRate $inletFlowRate;', 'alpha alpha.water;',
                          'value uniform (0 0 0);'])
    U += bloque('outlet', ['type zeroGradient;'])
    U += bloque('atmosphere', ['type pressureInletOutletVelocity;', 'value uniform (0 0 0);'])
    U += bloque('symmetry', sim)
    U += bloque('malla', ['type noSlip;'])
    U += bloque('fondo', ['type zeroGradient;'])
    U += bloque('paredes', ['type noSlip;']) + '}\n'
    U = U.replace('internalField uniform (0 0 0);', '#include "include/condiciones"\ninternalField uniform (0 0 0);', 1)
    w(os.path.join(d, '0.orig', 'U'), U)
    # alpha
    a = cab('volScalarField', 'alpha.water') + 'dimensions [0 0 0 0 0 0 0];\ninternalField uniform 0;\nboundaryField\n{\n'
    a += bloque('inlet', ['type variableHeightFlowRate;', 'lowerBound 0;', 'upperBound 1;', 'value uniform 0;'])
    a += bloque('outlet', ['type zeroGradient;'])
    a += bloque('atmosphere', ['type inletOutlet;', 'inletValue uniform 0;', 'value uniform 0;'])
    a += bloque('symmetry', sim)
    a += bloque('malla', ['type zeroGradient;'])
    a += bloque('fondo', ['type zeroGradient;'])
    a += bloque('paredes', ['type zeroGradient;']) + '}\n'
    w(os.path.join(d, '0.orig', 'alpha.water'), a)
    # p_rgh
    p = cab('volScalarField', 'p_rgh') + 'dimensions [1 -1 -2 0 0 0 0];\ninternalField uniform 0;\nboundaryField\n{\n'
    p += bloque('inlet', ['type zeroGradient;'])
    p += bloque('outlet', ['type zeroGradient;'])
    p += bloque('atmosphere', ['type totalPressure;', 'p0 uniform 0;'])
    p += bloque('symmetry', sim)
    p += bloque('malla', ['type fixedFluxPressure;', 'value uniform 0;'])
    p += bloque('fondo', ['type zeroGradient;'])
    p += bloque('paredes', ['type fixedFluxPressure;', 'value uniform 0;']) + '}\n'
    w(os.path.join(d, '0.orig', 'p_rgh'), p)
    # k, omega
    k = cab('volScalarField', 'k') + 'dimensions [0 2 -2 0 0 0 0];\ninternalField uniform %g;\nboundaryField\n{\n' % k0
    k += bloque('inlet', ['type fixedValue;', 'value uniform %g;' % k0])
    k += bloque('outlet', ['type inletOutlet;', 'inletValue uniform %g;' % k0, 'value uniform %g;' % k0])
    k += bloque('atmosphere', ['type inletOutlet;', 'inletValue uniform %g;' % k0, 'value uniform %g;' % k0])
    k += bloque('symmetry', sim)
    k += bloque('malla', ['type kqRWallFunction;', 'value uniform %g;' % k0])
    k += bloque('fondo', ['type zeroGradient;'])
    k += bloque('paredes', ['type kqRWallFunction;', 'value uniform %g;' % k0]) + '}\n'
    w(os.path.join(d, '0.orig', 'k'), k)
    o = cab('volScalarField', 'omega') + 'dimensions [0 0 -1 0 0 0 0];\ninternalField uniform %g;\nboundaryField\n{\n' % w0
    o += bloque('inlet', ['type fixedValue;', 'value uniform %g;' % w0])
    o += bloque('outlet', ['type inletOutlet;', 'inletValue uniform %g;' % w0, 'value uniform %g;' % w0])
    o += bloque('atmosphere', ['type inletOutlet;', 'inletValue uniform %g;' % w0, 'value uniform %g;' % w0])
    o += bloque('symmetry', sim)
    o += bloque('malla', ['type omegaWallFunction;', 'value uniform %g;' % w0])
    o += bloque('fondo', ['type zeroGradient;'])
    o += bloque('paredes', ['type omegaWallFunction;', 'value uniform %g;' % w0]) + '}\n'
    w(os.path.join(d, '0.orig', 'omega'), o)
    n = cab('volScalarField', 'nut') + 'dimensions [0 2 -1 0 0 0 0];\ninternalField uniform 0;\nboundaryField\n{\n'
    for nombre in ('inlet', 'outlet', 'atmosphere'):
        n += bloque(nombre, ['type calculated;', 'value uniform 0;'])
    n += bloque('symmetry', sim)
    n += bloque('malla', nut_pared)
    n += bloque('fondo', ['type calculated;', 'value uniform 0;'])
    n += bloque('paredes', nut_pared) + '}\n'
    w(os.path.join(d, '0.orig', 'nut'), n)


def generar(nombre, modo, base, n_pel, n_cre, n_sup, Q_Ls, tfin, npr, ks, nivel, ancho_losa, x_in, prom_desde, solo_malla=False):
    d = os.path.join(CASOS, nombre)
    if os.path.isdir(d):
        shutil.rmtree(d)
    pref = GEO_PREF or ('dominio_losa' if modo == 'losa' else 'dominio')
    info = json.load(open(os.path.join(GEO, pref + '_info.json')))
    g = 9.81
    b = info['ancho_canal_m']
    Q = Q_Ls * 1e-3
    if modo == 'losa':
        caudal = Q * (ancho_losa * 1e-3) / b                      # el corte lleva la parte proporcional del caudal
    else:
        caudal = Q / 2.0                                          # semiancho
    q = Q / b
    hn = 0.0085                                                   # orden de magnitud de la lamina, solo para k y omega
    U0 = q / hn
    k0 = 1.5 * (0.05 * U0) ** 2
    w0 = math.sqrt(k0) / (0.5477 * 0.07 * hn)
    # ---- geometria
    tri = os.path.join(d, 'constant', 'triSurface')
    os.makedirs(tri, exist_ok=True)
    for f in (pref + '.stl', 'zona_pelicula.stl', 'zona_cresta.stl', 'zona_superficie_cajon.stl'):
        shutil.copy(os.path.join(GEO, f), os.path.join(tri, f.replace(pref, 'dominio')))
    # ---- constant
    w(os.path.join(d, 'constant', 'g'), cab('uniformDimensionedVectorField', 'g') +
      'dimensions [0 1 -2 0 0 0 0];\nvalue (0 0 -%g);\n' % g)
    w(os.path.join(d, 'constant', 'transportProperties'), cab('dictionary', 'transportProperties') + """
phases (water air);
water { transportModel Newtonian; nu 1e-06; rho 1000; }
air   { transportModel Newtonian; nu 1.48e-05; rho 1; }
sigma 0.072;
""")
    w(os.path.join(d, 'constant', 'turbulenceProperties'), cab('dictionary', 'turbulenceProperties') + """
simulationType RAS;
RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }
""")
    # ---- malla de fondo (desfasada para que los planos del STL no coincidan con caras de celdas)
    x0, x1 = info['caja'][0] - 0.0113 * base / 8e-3, info['caja'][3] + 0.0127 * base / 8e-3
    z0, z1 = info['caja'][2] - 0.0091 * base / 8e-3, info['caja'][5] + 0.0117 * base / 8e-3
    if modo == 'losa':
        y0, y1 = -0.0008, -0.0008 + base
    else:
        y0, y1 = -0.0007 * base / 8e-3, info['caja'][4] + 0.0113 * base / 8e-3
    nxb, nyb, nzb = [max(1, int(round((hi - lo) / base))) for lo, hi in ((x0, x1), (y0, y1), (z0, z1))]
    w(os.path.join(d, 'system', 'blockMeshDict'), cab('dictionary', 'blockMeshDict') + """
scale 1;
vertices ( (%(x0).7g %(y0).7g %(z0).7g) (%(x1).7g %(y0).7g %(z0).7g) (%(x1).7g %(y1).7g %(z0).7g) (%(x0).7g %(y1).7g %(z0).7g)
           (%(x0).7g %(y0).7g %(z1).7g) (%(x1).7g %(y0).7g %(z1).7g) (%(x1).7g %(y1).7g %(z1).7g) (%(x0).7g %(y1).7g %(z1).7g) );
blocks ( hex (0 1 2 3 4 5 6 7) (%(nx)d %(ny)d %(nz)d) simpleGrading (1 1 1) );
edges ();
boundary ( fondo { type patch; faces ((0 3 2 1) (4 5 6 7) (0 4 7 3) (1 2 6 5) (0 1 5 4) (3 7 6 2)); } );
""" % dict(x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1, nx=nxb, ny=nyb, nz=nzb))
    # ---- snappyHexMesh
    reg = ''.join('            %s { name %s; }\n' % (r, r) for r in PARCHES)
    tipos = (('inlet', 'patch', 2), ('outlet', 'patch', 2), ('atmosphere', 'patch', 2), ('symmetry', 'symmetry', 2),
             ('malla', 'wall', n_pel), ('paredes', 'wall', 2))
    regsup = ''.join('                %s { level (%d %d); patchInfo { type %s; } }\n' % (r, n, n, t) for r, t, n in tipos)
    w(os.path.join(d, 'system', 'snappyHexMeshDict'), cab('dictionary', 'snappyHexMeshDict') + """
castellatedMesh true;
snap            true;
addLayers       false;
geometry
{
    dominio.stl
    {
        type triSurfaceMesh;
        name dominio;
        regions
        {
%(reg)s        }
    }
    zona_pelicula.stl        { type triSurfaceMesh; name zona_pelicula; }
    zona_cresta.stl          { type triSurfaceMesh; name zona_cresta; }
    zona_superficie_cajon.stl { type triSurfaceMesh; name zona_superficie_cajon; }
}
castellatedMeshControls
{
    maxLocalCells 50000000;
    maxGlobalCells 50000000;
    minRefinementCells 0;
    maxLoadUnbalance 0.2;
    nCellsBetweenLevels 3;
    features ();
    refinementSurfaces
    {
        dominio
        {
            level (2 2);
            regions
            {
%(regsup)s            }
        }
    }
    resolveFeatureAngle 30;
    refinementRegions
    {
        zona_pelicula        { mode inside; levels ((1e15 %(np)d)); }
        zona_cresta          { mode inside; levels ((1e15 %(nc)d)); }
        zona_superficie_cajon { mode inside; levels ((1e15 %(ns)d)); }
    }
    locationInMesh (%(px).5g %(py).5g %(pz).5g);
    allowFreeStandingZoneFaces true;
}
snapControls
{
    nSmoothPatch 3; tolerance 2.0; nSolveIter 60; nRelaxIter 5;
    nFeatureSnapIter 10; implicitFeatureSnap true; explicitFeatureSnap false; multiRegionFeatureSnap true;
}
addLayersControls { relativeSizes true; layers {} expansionRatio 1.2; finalLayerThickness 0.5; minThickness 0.1; nGrow 0;
    featureAngle 130; nRelaxIter 5; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50; }
meshQualityControls
{
    maxNonOrtho 65; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-13; minTetQuality 1e-30;
    minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.02; minVolRatio 0.01; minTriangleTwist -1;
    nSmoothScale 4; errorReduction 0.75;
    relaxed { maxNonOrtho 75; }
}
mergeTolerance 1e-6;
""" % dict(reg=reg, regsup=regsup, nm=n_pel, np=n_pel, nc=n_cre, ns=n_sup, px=info['punto_en_agua_m'][0], py=info['punto_en_agua_m'][1],
           pz=info['punto_en_agua_m'][2]))
    # ---- solver
    w(os.path.join(d, 'system', 'fvSchemes'), cab('dictionary', 'fvSchemes') + """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(rhoPhi,U) Gauss linearUpwind grad(U);
    div(phi,alpha) Gauss vanLeer;
    div(phirb,alpha) Gauss linear;
    "div\\(phi,(k|omega)\\)" Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
wallDist { method meshWave; }
""")
    w(os.path.join(d, 'system', 'fvSolution'), cab('dictionary', 'fvSolution') + """
solvers
{
    "alpha.water.*"
    {
        nAlphaCorr 2; nAlphaSubCycles 1; cAlpha 1; MULESCorr yes; nLimiterIter 3;
        solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0;
    }
    "pcorr.*" { solver PCG; preconditioner { preconditioner GAMG; tolerance 1e-5; relTol 0; smoother GaussSeidel; }
                tolerance 1e-5; relTol 0; maxIter 50; }
    p_rgh { solver GAMG; tolerance 1e-8; relTol 0.01; smoother GaussSeidel; maxIter 50; }
    p_rghFinal { $p_rgh; tolerance 1e-8; relTol 0; }
    "(U|k|omega).*" { solver smoothSolver; smoother symGaussSeidel; nSweeps 1; tolerance 1e-7; relTol 0.1; }
}
PIMPLE { momentumPredictor no; nOuterCorrectors 1; nCorrectors 3; nNonOrthogonalCorrectors 1; }
relaxationFactors { equations { ".*" 1; } }
""")
    w(os.path.join(d, 'system', 'controlDict'), cab('dictionary', 'controlDict') + """
application interFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime %(tfin)g;
deltaT 1e-5; writeControl adjustable; writeInterval 0.05; purgeWrite 3;
writeFormat ascii; writePrecision 8; writeCompression off; timeFormat general; timePrecision 6;
runTimeModifiable yes;
adjustTimeStep yes; maxCo 0.5; maxAlphaCo 0.5; maxDeltaT 2e-3;
functions
{
    promedios
    {
        type fieldAverage; libs (fieldFunctionObjects);
        writeControl writeTime; timeStart %(tp)g;
        fields ( U { mean on; prime2Mean off; base time; } alpha.water { mean on; prime2Mean off; base time; }
                 p_rgh { mean on; prime2Mean off; base time; } );
    }
    caudales
    {
        type surfaceFieldValue; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 200; log true;
        writeFields false; regionType patch; name outlet; operation sum; fields ( phi );
    }
}
""" % dict(tfin=tfin, tp=prom_desde))
    w(os.path.join(d, 'system', 'decomposeParDict'), cab('dictionary', 'decomposeParDict') +
      'numberOfSubdomains %d;\nmethod scotch;\n' % npr)
    # ---- condiciones y campos iniciales
    w(os.path.join(d, '0.orig', 'include', 'condiciones'), 'inletFlowRate %.8g;\n' % caudal)
    campos(d, U0, k0, w0, ks)
    xr = info['x_salida_m']
    w(os.path.join(d, 'system', 'setFieldsDict'), cab('dictionary', 'setFieldsDict') + """
defaultFieldValues ( volScalarFieldValue alpha.water 0 );
regions
(
    boxToCell { box (-2 -2 -1) (-0.004 2 %g); fieldValues ( volScalarFieldValue alpha.water 1 ); }
);
""" % nivel)
    w(os.path.join(d, 'Allrun'), """#!/bin/bash
source /usr/lib/openfoam/openfoam2512/etc/bashrc
NP=%d
blockMesh > log.blockMesh 2>&1
snappyHexMesh -overwrite > log.snappy 2>&1
checkMesh > log.checkMesh 2>&1
[ "%s" = "1" ] && exit 0
cp -r 0.orig 0
setFields > log.setFields 2>&1
if [ $NP -gt 1 ]; then
  decomposePar > log.decompose 2>&1
  mpirun --use-hwthread-cpus -np $NP interFoam -parallel > log.interFoam 2>&1
  reconstructPar -latestTime > log.reconstruct 2>&1
else
  interFoam > log.interFoam 2>&1
fi
postProcess -func writeCellCentres -latestTime > log.C 2>&1
postProcess -func writeCellVolumes -latestTime > log.V 2>&1
""" % (npr, '1' if solo_malla else '0'))
    print('caso %s (%s): fondo %dx%dx%d celdas de %.1f mm | niveles: pelicula %d (%.2f mm), cresta %d (%.2f mm), superficie %d (%.2f mm) | '
          'caudal %.4g m3/s' % (nombre, modo, nxb, nyb, nzb, base * 1e3, n_pel, base * 1e3 / 2 ** n_pel, n_cre,
                                base * 1e3 / 2 ** n_cre, n_sup, base * 1e3 / 2 ** n_sup, caudal))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('nombre')
    ap.add_argument('--modo', choices=('losa', 'medio'), default='losa')
    ap.add_argument('--base', type=float, default=8e-3)
    ap.add_argument('--n-pelicula', type=int, default=4)
    ap.add_argument('--n-cresta', type=int, default=5)
    ap.add_argument('--n-sup', type=int, default=3)
    ap.add_argument('--Q', type=float, default=10.0, help='caudal total en L/s')
    ap.add_argument('--tfin', type=float, default=8.0)
    ap.add_argument('--prom-desde', type=float, default=5.0)
    ap.add_argument('--np', type=int, default=4)
    ap.add_argument('--ks', type=float, default=0.0)
    ap.add_argument('--nivel', type=float, default=0.113, help='nivel inicial del agua en el cajon (m sobre su fondo)')
    ap.add_argument('--ancho-losa', type=float, default=2.0, help='mm')
    ap.add_argument('--geo-prefijo', default=None, help='prefijo del STL del dominio en geometria/ (por defecto dominio)')
    ap.add_argument('--solo-malla', action='store_true', help='solo genera y revisa la malla')
    a = ap.parse_args()
    GEO_PREF = a.geo_prefijo
    generar(a.nombre, a.modo, a.base, a.n_pelicula, a.n_cresta, a.n_sup, a.Q, a.tfin, a.np, a.ks, a.nivel, a.ancho_losa, None,
            a.prom_desde, a.solo_malla)
