# -*- coding: utf-8 -*-
"""Fase 0a: lamina de agua sobre un plano inclinado (2D), para comparar el CFD con la teoria.

Genera un caso de OpenFOAM (interFoam + kOmegaSST) en cfd_3d/casos/<nombre>. El plano esta a 'theta' grados: se trabaja con
ejes alineados con la pendiente (x a lo largo, z normal) y la gravedad inclinada. El agua entra con la profundidad y la velocidad
de Manning (n = 0,010) y se ve si el CFD la mantiene o la corrige: eso mide la friccion de pared que el CFD "cree" para una
pared lisa (o rugosa, con ks) frente a la que asumi en el modelo 1D/2D.

    python f0a_pelicula.py <nombre> [--dx 2e-3] [--dz 0.5e-3] [--ks 0] [--q 0.0198] [--theta 12] [--largo 1.5] [--tfin 3]
"""
import argparse
import math
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
CASOS = os.path.join(AQUI, '..', 'casos')

CAB = """FoamFile
{
    version     2.0;
    format      ascii;
    class       %s;
    object      %s;
}
"""


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)


def cab(clase, objeto):
    return CAB % (clase, objeto)


def manning(q, theta, n=0.010):
    return (q * n / math.sqrt(math.sin(theta))) ** 0.6


def generar(nombre, dx, dz, ks, q, theta_deg, largo, tfin, Hmax=0.05):
    th = math.radians(theta_deg)
    h0 = manning(q, th)
    U0 = q / h0
    ancho = 0.01                                  # espesor de la celda en y (2D)
    nx = int(round(largo / dx))
    nz0 = max(int(round(h0 / dz)), 4)
    # region de aire: celdas que crecen hacia arriba (razon 6 entre la ultima y la primera)
    nz1 = 30
    d = os.path.join(CASOS, nombre)
    g = 9.81
    # ---- constant
    escribir(os.path.join(d, 'constant', 'g'),
             cab('uniformDimensionedVectorField', 'g') + 'dimensions      [0 1 -2 0 0 0 0];\nvalue           (%.6f 0 %.6f);\n' %
             (g * math.sin(th), -g * math.cos(th)))
    escribir(os.path.join(d, 'constant', 'transportProperties'), cab('dictionary', 'transportProperties') + """
phases          (water air);
water { transportModel Newtonian; nu 1e-06; rho 1000; }
air   { transportModel Newtonian; nu 1.48e-05; rho 1; }
sigma           0.072;
""")
    escribir(os.path.join(d, 'constant', 'turbulenceProperties'), cab('dictionary', 'turbulenceProperties') + """
simulationType  RAS;
RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }
""")
    # ---- malla
    L, y, H = largo, ancho / 2, Hmax
    escribir(os.path.join(d, 'system', 'blockMeshDict'), cab('dictionary', 'blockMeshDict') + """
scale 1;
vertices
(
    (0 %(ny)g 0) (%(L)g %(ny)g 0) (%(L)g %(y)g 0) (0 %(y)g 0)
    (0 %(ny)g %(h0).8g) (%(L)g %(ny)g %(h0).8g) (%(L)g %(y)g %(h0).8g) (0 %(y)g %(h0).8g)
    (0 %(ny)g %(H)g) (%(L)g %(ny)g %(H)g) (%(L)g %(y)g %(H)g) (0 %(y)g %(H)g)
);
blocks
(
    hex (0 1 2 3 4 5 6 7)   (%(nx)d 1 %(nz0)d) simpleGrading (1 1 1)
    hex (4 5 6 7 8 9 10 11) (%(nx)d 1 %(nz1)d) simpleGrading (1 1 6)
);
edges ();
boundary
(
    inletWater { type patch; faces ((0 4 7 3)); }
    outlet     { type patch; faces ((1 2 6 5) (5 6 10 9)); }
    bottom     { type wall;  faces ((0 3 2 1)); }
    atmosphere { type patch; faces ((8 9 10 11) (4 8 11 7)); }
    frontAndBack { type empty; faces ((0 1 5 4) (4 5 9 8) (3 7 6 2) (7 11 10 6)); }
);
""" % {'ny': -y, 'L': L, 'y': y, 'h0': h0, 'H': H, 'nx': nx, 'nz0': nz0, 'nz1': nz1})
    escribir(os.path.join(d, 'system', 'setFieldsDict'), cab('dictionary', 'setFieldsDict') + """
defaultFieldValues ( volScalarFieldValue alpha.water 0 volVectorFieldValue U (0 0 0) );
regions
(
    boxToCell { box (-1 -1 -1) (%g 1 %.8g); fieldValues ( volScalarFieldValue alpha.water 1 volVectorFieldValue U (%.5f 0 0) ); }
);
""" % (L + 1, h0, U0))
    escribir(os.path.join(d, 'system', 'fvSchemes'), cab('dictionary', 'fvSchemes') + """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default             none;
    div(rhoPhi,U)       Gauss linearUpwind grad(U);
    div(phi,alpha)      Gauss vanLeer;
    div(phirb,alpha)    Gauss linear;
    "div\\(phi,(k|omega)\\)" Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
wallDist { method meshWave; }
""")
    escribir(os.path.join(d, 'system', 'fvSolution'), cab('dictionary', 'fvSolution') + """
solvers
{
    "alpha.water.*"
    {
        nAlphaCorr 1; nAlphaSubCycles 1; cAlpha 1; MULESCorr yes; nLimiterIter 3;
        solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0;
    }
    "pcorr.*" { solver PCG; preconditioner { preconditioner GAMG; tolerance 1e-5; relTol 0; smoother GaussSeidel; } tolerance 1e-5; relTol 0; maxIter 50; }
    p_rgh { solver GAMG; tolerance 5e-9; relTol 0.01; smoother GaussSeidel; maxIter 50; }
    p_rghFinal { $p_rgh; tolerance 5e-9; relTol 0; }
    "(U|k|omega).*" { solver smoothSolver; smoother symGaussSeidel; nSweeps 1; tolerance 1e-7; relTol 0.1; }
}
PIMPLE { momentumPredictor yes; nCorrectors 3; nNonOrthogonalCorrectors 0; }
relaxationFactors { equations { ".*" 1; } }
""")
    escribir(os.path.join(d, 'system', 'controlDict'), cab('dictionary', 'controlDict') + """
application interFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime %g;
deltaT 1e-5; writeControl adjustable; writeInterval %g; purgeWrite 2;
writeFormat ascii; writePrecision 8; writeCompression off; timeFormat general; timePrecision 6;
runTimeModifiable yes;
adjustTimeStep yes; maxCo 0.5; maxAlphaCo 0.5; maxDeltaT 1e-3;
""" % (tfin, tfin))
    # ---- campos iniciales
    k0 = 1.5 * (0.05 * U0) ** 2
    w0 = math.sqrt(k0) / (0.5477 * 0.07 * h0)
    ks_txt = ('nutkRoughWallFunction; Ks uniform %g; Cs uniform 0.5; value uniform 0' % ks) if ks > 0 else 'nutkWallFunction; value uniform 0'
    escribir(os.path.join(d, '0.orig', 'U'), cab('volVectorField', 'U') + """
dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0);
boundaryField
{
    inletWater { type fixedValue; value uniform (%.5f 0 0); }
    bottom { type noSlip; }
    atmosphere { type pressureInletOutletVelocity; value uniform (0 0 0); }
    outlet { type inletOutlet; inletValue uniform (0 0 0); value uniform (0 0 0); }
    frontAndBack { type empty; }
}
""" % U0)
    escribir(os.path.join(d, '0.orig', 'alpha.water'), cab('volScalarField', 'alpha.water') + """
dimensions [0 0 0 0 0 0 0]; internalField uniform 0;
boundaryField
{
    inletWater { type fixedValue; value uniform 1; }
    bottom { type zeroGradient; }
    atmosphere { type inletOutlet; inletValue uniform 0; value uniform 0; }
    outlet { type zeroGradient; }
    frontAndBack { type empty; }
}
""")
    escribir(os.path.join(d, '0.orig', 'p_rgh'), cab('volScalarField', 'p_rgh') + """
dimensions [1 -1 -2 0 0 0 0]; internalField uniform 0;
boundaryField
{
    atmosphere { type totalPressure; p0 uniform 0; }
    inletWater { type fixedFluxPressure; value uniform 0; }
    bottom { type fixedFluxPressure; value uniform 0; }
    outlet { type fixedFluxPressure; value uniform 0; }
    frontAndBack { type empty; }
}
""")
    escribir(os.path.join(d, '0.orig', 'k'), cab('volScalarField', 'k') + """
dimensions [0 2 -2 0 0 0 0]; internalField uniform %g;
boundaryField
{
    inletWater { type fixedValue; value uniform %g; }
    bottom { type kqRWallFunction; value uniform %g; }
    atmosphere { type inletOutlet; inletValue uniform %g; value uniform %g; }
    outlet { type inletOutlet; inletValue uniform %g; value uniform %g; }
    frontAndBack { type empty; }
}
""" % (k0, k0, k0, k0, k0, k0, k0))
    escribir(os.path.join(d, '0.orig', 'omega'), cab('volScalarField', 'omega') + """
dimensions [0 0 -1 0 0 0 0]; internalField uniform %g;
boundaryField
{
    inletWater { type fixedValue; value uniform %g; }
    bottom { type omegaWallFunction; value uniform %g; }
    atmosphere { type inletOutlet; inletValue uniform %g; value uniform %g; }
    outlet { type inletOutlet; inletValue uniform %g; value uniform %g; }
    frontAndBack { type empty; }
}
""" % (w0, w0, w0, w0, w0, w0, w0))
    escribir(os.path.join(d, '0.orig', 'nut'), cab('volScalarField', 'nut') + """
dimensions [0 2 -1 0 0 0 0]; internalField uniform 0;
boundaryField
{
    inletWater { type calculated; value uniform 0; }
    bottom { type %s; }
    atmosphere { type calculated; value uniform 0; }
    outlet { type calculated; value uniform 0; }
    frontAndBack { type empty; }
}
""" % ks_txt)
    escribir(os.path.join(d, 'Allrun'), """#!/bin/bash
source /usr/lib/openfoam/openfoam2512/etc/bashrc
cp -r 0.orig 0
blockMesh > log.blockMesh 2>&1
checkMesh > log.checkMesh 2>&1
setFields > log.setFields 2>&1
interFoam > log.interFoam 2>&1
postProcess -func writeCellCentres -latestTime > log.C 2>&1
postProcess -func writeCellVolumes -latestTime > log.V 2>&1
""")
    print('caso %s: nx=%d, nz0=%d (dz=%.3f mm), nz1=%d | h0=%.3f mm, U0=%.3f m/s, k0=%.4g, omega0=%.4g, ks=%g m' %
          (nombre, nx, nz0, 1e3 * h0 / nz0, nz1, 1e3 * h0, U0, k0, w0, ks))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('nombre')
    ap.add_argument('--dx', type=float, default=2e-3)
    ap.add_argument('--dz', type=float, default=0.5e-3)
    ap.add_argument('--ks', type=float, default=0.0)
    ap.add_argument('--q', type=float, default=0.0198)
    ap.add_argument('--theta', type=float, default=12.0)
    ap.add_argument('--largo', type=float, default=1.5)
    ap.add_argument('--tfin', type=float, default=3.0)
    a = ap.parse_args()
    generar(a.nombre, a.dx, a.dz, a.ks, a.q, a.theta, a.largo, a.tfin)
