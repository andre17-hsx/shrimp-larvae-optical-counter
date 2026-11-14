# -*- coding: utf-8 -*-
"""Genera el caso de la fase 3 (malla, tobogan, arco y linea de conteo, con drenaje en la malla) para OpenFOAM.

Requiere: geometria_linea.py (STL en ../geometria) y los resultados del caso de la fase 2 (campo medio).
    - Entrada: plano x = x_in justo aguas abajo del labio; el perfil de velocidad y de fraccion de agua se toma del campo medio
      del caso p2_medio_grueso (timeVaryingMappedFixedValue), con el mismo caudal y las mismas ondas laterales.
    - Malla de acero: velocidad normal uniforme hacia fuera (surfaceNormalFixedValue), calibrada con el modelo 1D para que el
      tramo de malla drene una fraccion del caudal total (--drenaje 0.15, 0.30, 0 = sin drenaje). El coeficiente real esta sin medir.
    - Salida: presion (prghPressure). Tapa del tobogan como pared. Limitador de velocidad del aire (limitVelocity, 6 m/s).

    python caso_linea.py <nombre> --drenaje 0.15 [--base 0.016 --n-pelicula 3 --tfin 2.7 --prom-desde 1.5 --np 8] [--solo-malla]
Requiere numpy, scipy (entorno simenv).
"""
import argparse
import json
import math
import os
import shutil
import sys

import numpy as np
from scipy.spatial import cKDTree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', '..', 'simulacion_flujo'))
from caso_snappy import w, cab  # noqa: E402

GEO = os.path.join(AQUI, '..', 'geometria')
CASOS = os.path.join(AQUI, '..', 'casos')
PLANTILLA = os.path.join(CASOS, 'p2_medio_grueso')          # de aqui se copian constant/ y system/{fvSchemes,fvSolution,decomposeParDict}


def v_drenaje(frac, x_in, area_malla):
    """Velocidad normal uniforme (m/s, hacia fuera) que reproduce en la malla (desde x_in) el drenaje del modelo 1D calibrado a
    'frac' del caudal total sobre toda la malla."""
    from geometria_canal import cargar_canal
    from flujo_1d import perfil_estacionario, calibrar_kd
    from contracciones import ancho_fijo
    c, m, g = cargar_canal(10.0)
    f = ancho_fijo(c)
    kd = calibrar_kd(c, frac, forma_ancho=f, Q=0.010)
    P = perfil_estacionario(c, forma_ancho=f, kd=kd)
    q_in = float(np.interp(x_in / math.cos(c.t_malla), P['s'], P['Qs']))
    q_out = float(np.interp(c.s_malla, P['s'], P['Qs']))
    drenado_semiancho = 0.5 * (q_in - q_out)
    return drenado_semiancho / area_malla, kd, q_in, q_out


def datos_entrada(d, x_in, z_lo, z_hi, hm, paso=2e-3, caso='p2_medio_grueso', q_objetivo=5.0e-3):
    """Escribe constant/boundaryData/inlet (points, 0/U, 0/alpha.water) con el campo medio del caso de la fase 2."""
    from analizar_3d import cargar
    t, aM, UM, C, V = cargar(caso)
    m = np.abs(C[:, 0] - x_in) < 0.006
    tree = cKDTree(C[m])
    ys = np.arange(0.0005, hm + 1e-9, paso)
    zs = np.arange(z_lo, z_hi + 1e-9, paso)
    P = np.array([(x_in, y, z) for y in ys for z in zs])
    _, i = tree.query(P)
    U, a = UM[m][i], aM[m][i]
    q0 = float((a * U[:, 0]).sum() * paso * paso)
    U = U * (q_objetivo / q0)                    # el campo medio da un caudal ~5 % mayor que el nominal: se reescala a 10 L/s totales
    base = os.path.join(d, 'constant', 'boundaryData', 'inlet')
    os.makedirs(os.path.join(base, '0'), exist_ok=True)
    # formato "raw" de OpenFOAM (como constant/boundaryData del tutorial pitzDailyExptInlet): sin cabecera ni promedio
    def lista(vals, fmt):
        return '%d\n(\n%s\n)\n' % (len(vals), '\n'.join(fmt % tuple(v) if isinstance(v, (tuple, np.ndarray)) else fmt % v for v in vals))
    w(os.path.join(base, 'points'), lista(P, '(%.6g %.6g %.6g)'))
    w(os.path.join(base, '0', 'U'), lista(U, '(%.6g %.6g %.6g)'))
    w(os.path.join(base, '0', 'alpha.water'), lista(np.clip(a, 0.0, 1.0), '%.6g'))
    q = float((a * U[:, 0]).sum() * paso * paso)
    return len(P), q, q0


def campos(d, k0, w0, vn):
    def bloque(nombre, dic):
        return '    %s\n    {\n%s\n    }\n' % (nombre, '\n'.join('        %s' % l for l in dic))
    sim = ['type symmetry;']
    nutp = ['type nutkWallFunction;', 'value uniform 0;']
    esc = lambda clase, obj, dim, valor: cab(clase, obj) + 'dimensions %s;\ninternalField uniform %s;\nboundaryField\n{\n' % (dim, valor)
    U = esc('volVectorField', 'U', '[0 1 -1 0 0 0 0]', '(0 0 0)')
    U += bloque('inlet', ['type timeVaryingMappedFixedValue;', 'mapMethod nearest;', 'offset (0 0 0);', 'setAverage off;', 'value uniform (0 0 0);'])
    U += bloque('outlet', ['type pressureInletOutletVelocity;', 'value uniform (0 0 0);'])
    U += bloque('symmetry', sim)
    U += bloque('malla', ['type surfaceNormalFixedValue;', 'refValue uniform %.6g;' % vn])
    U += bloque('fondo', ['type zeroGradient;'])
    U += bloque('paredes', ['type noSlip;']) + '}\n'
    w(os.path.join(d, '0.orig', 'U'), U)
    a = esc('volScalarField', 'alpha.water', '[0 0 0 0 0 0 0]', '0')
    a += bloque('inlet', ['type timeVaryingMappedFixedValue;', 'mapMethod nearest;', 'offset 0;', 'setAverage off;', 'value uniform 0;'])
    a += bloque('outlet', ['type inletOutlet;', 'inletValue uniform 0;', 'value uniform 0;'])
    a += bloque('symmetry', sim)
    a += bloque('malla', ['type zeroGradient;'])
    a += bloque('fondo', ['type zeroGradient;'])
    a += bloque('paredes', ['type zeroGradient;']) + '}\n'
    w(os.path.join(d, '0.orig', 'alpha.water'), a)
    p = esc('volScalarField', 'p_rgh', '[1 -1 -2 0 0 0 0]', '0')
    p += bloque('inlet', ['type fixedFluxPressure;', 'value uniform 0;'])
    p += bloque('outlet', ['type prghPressure;', 'p uniform 0;', 'value uniform 0;'])
    p += bloque('symmetry', sim)
    p += bloque('malla', ['type fixedFluxPressure;', 'value uniform 0;'])
    p += bloque('fondo', ['type zeroGradient;'])
    p += bloque('paredes', ['type fixedFluxPressure;', 'value uniform 0;']) + '}\n'
    w(os.path.join(d, '0.orig', 'p_rgh'), p)
    for nombre, v0, wall in (('k', k0, 'kqRWallFunction'), ('omega', w0, 'omegaWallFunction')):
        dim = '[0 2 -2 0 0 0 0]' if nombre == 'k' else '[0 0 -1 0 0 0 0]'
        f = esc('volScalarField', nombre, dim, '%g' % v0)
        f += bloque('inlet', ['type fixedValue;', 'value uniform %g;' % v0])
        f += bloque('outlet', ['type inletOutlet;', 'inletValue uniform %g;' % v0, 'value uniform %g;' % v0])
        f += bloque('symmetry', sim)
        f += bloque('malla', ['type %s;' % wall, 'value uniform %g;' % v0])
        f += bloque('fondo', ['type zeroGradient;'])
        f += bloque('paredes', ['type %s;' % wall, 'value uniform %g;' % v0]) + '}\n'
        w(os.path.join(d, '0.orig', nombre), f)
    n = esc('volScalarField', 'nut', '[0 2 -1 0 0 0 0]', '0')
    for nombre in ('inlet', 'outlet'):
        n += bloque(nombre, ['type calculated;', 'value uniform 0;'])
    n += bloque('symmetry', sim)
    n += bloque('malla', nutp)
    n += bloque('fondo', ['type calculated;', 'value uniform 0;'])
    n += bloque('paredes', nutp) + '}\n'
    w(os.path.join(d, '0.orig', 'nut'), n)


def generar(nombre, drenaje, base, n_pel, tfin, prom_desde, npr, solo_malla, x_in_mm):
    d = os.path.join(CASOS, nombre)
    if os.path.isdir(d):
        shutil.rmtree(d)
    info = json.load(open(os.path.join(GEO, 'dominio_linea_info.json')))
    x_in = info['x_in_m']
    # ---- geometria
    tri = os.path.join(d, 'constant', 'triSurface')
    os.makedirs(tri, exist_ok=True)
    shutil.copy(os.path.join(GEO, 'dominio_linea.stl'), os.path.join(tri, 'dominio.stl'))
    shutil.copy(os.path.join(GEO, 'zona_pelicula_linea.stl'), os.path.join(tri, 'zona_pelicula.stl'))
    for f in ('g', 'transportProperties', 'turbulenceProperties'):
        shutil.copy(os.path.join(PLANTILLA, 'constant', f), os.path.join(d, 'constant', f))
    for f in ('fvSchemes', 'fvSolution', 'decomposeParDict'):
        os.makedirs(os.path.join(d, 'system'), exist_ok=True)
        t = open(os.path.join(PLANTILLA, 'system', f), encoding='utf-8').read().replace('\r', '')
        if f == 'decomposeParDict':
            t = t.replace('numberOfSubdomains 8;', 'numberOfSubdomains %d;' % npr)
        w(os.path.join(d, 'system', f), t)
    # ---- drenaje y entrada
    area_malla = info['parches_area_m2']['malla']
    vn, kd, q_in1d, q_out1d = (0.0, 0.0, 0.0, 0.0) if drenaje <= 0 else v_drenaje(drenaje, x_in, area_malla)
    npts, q_map, q_orig = datos_entrada(d, x_in, info['z_fondo_in_m'] - 0.001, info['z_techo_in_m'], info['ancho_canal_m'] / 2.0)
    print('entrada mapeada: %d puntos; caudal de agua del semiancho en el campo medio %.2f L/s, reescalado a %.2f L/s' % (npts, q_orig * 1e3, q_map * 1e3))
    print('drenaje %.0f %% (1D, toda la malla): kd %.4f | 1D entre x_in y el fin de la malla: %.2f -> %.2f L/s | velocidad normal %.4f m/s '
          '(%.2f L/s en el semiancho)' % (drenaje * 100, kd, q_in1d * 1e3, q_out1d * 1e3, vn, vn * area_malla * 1e3))
    # ---- turbulencia de entrada (misma logica que la fase 2)
    q = 0.010 / info['ancho_canal_m']
    hn = 0.0085
    U0 = q / hn
    k0 = 1.5 * (0.05 * U0) ** 2
    w0 = math.sqrt(k0) / (0.5477 * 0.07 * hn)
    campos(d, k0, w0, vn)
    # ---- malla de fondo (desfasada para que los planos del STL no coincidan con caras de celdas)
    cj = info['caja']
    f = base / 8e-3
    x0, x1 = cj[0] - 0.0113 * f, cj[3] + 0.0127 * f
    y0, y1 = -0.0007 * f, cj[4] + 0.0113 * f
    z0, z1 = cj[2] - 0.0091 * f, cj[5] + 0.0117 * f
    nx, ny, nz = [max(1, int(round((hi - lo) / base))) for lo, hi in ((x0, x1), (y0, y1), (z0, z1))]
    w(os.path.join(d, 'system', 'blockMeshDict'), cab('dictionary', 'blockMeshDict') + """
scale 1;
vertices ( (%(x0).7g %(y0).7g %(z0).7g) (%(x1).7g %(y0).7g %(z0).7g) (%(x1).7g %(y1).7g %(z0).7g) (%(x0).7g %(y1).7g %(z0).7g)
           (%(x0).7g %(y0).7g %(z1).7g) (%(x1).7g %(y0).7g %(z1).7g) (%(x1).7g %(y1).7g %(z1).7g) (%(x0).7g %(y1).7g %(z1).7g) );
blocks ( hex (0 1 2 3 4 5 6 7) (%(nx)d %(ny)d %(nz)d) simpleGrading (1 1 1) );
edges ();
boundary ( fondo { type patch; faces ((0 3 2 1) (4 5 6 7) (0 4 7 3) (1 2 6 5) (0 1 5 4) (3 7 6 2)); } );
""" % dict(x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1, nx=nx, ny=ny, nz=nz))
    regiones = [('inlet', 'patch', 2), ('outlet', 'patch', 2), ('symmetry', 'symmetry', 2), ('malla', 'wall', n_pel), ('paredes', 'wall', 2)]
    reg = ''.join('            %s { name %s; }\n' % (r, r) for r, t, n in regiones)
    regsup = ''.join('                %s { level (%d %d); patchInfo { type %s; } }\n' % (r, n, n, t) for r, t, n in regiones)
    px, py, pz = info['punto_en_aire_m']
    snappy = open(os.path.join(PLANTILLA, 'system', 'snappyHexMeshDict'), encoding='utf-8').read().replace('\r', '')
    i0, i1 = snappy.index('castellatedMesh true;'), snappy.index('snapControls')
    nuevo = """castellatedMesh true;
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
    }
    locationInMesh (%(px).5g %(py).5g %(pz).5g);
    allowFreeStandingZoneFaces true;
}
""" % dict(reg=reg, regsup=regsup, np=n_pel, px=px, py=py, pz=pz)
    w(os.path.join(d, 'system', 'snappyHexMeshDict'), snappy[:i0] + nuevo + snappy[i1:])
    # ---- control
    fun = lambda nom, parche: """    %s
    {
        type surfaceFieldValue; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 200; log true;
        writeFields false; regionType patch; name %s; operation sum; fields ( phi alphaPhi0.water );
    }
""" % (nom, parche)
    w(os.path.join(d, 'system', 'controlDict'), cab('dictionary', 'controlDict') + """
application interFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime %g;
deltaT 1e-5; writeControl adjustable; writeInterval 0.05; purgeWrite 3;
writeFormat ascii; writePrecision 8; writeCompression off; timeFormat general; timePrecision 6;
runTimeModifiable yes;
adjustTimeStep yes; maxCo 0.5; maxAlphaCo 0.5; maxDeltaT 2e-3;
functions
{
    promedios
    {
        type fieldAverage; libs (fieldFunctionObjects);
        writeControl writeTime; timeStart %g;
        fields ( U { mean on; prime2Mean off; base time; } alpha.water { mean on; prime2Mean off; base time; }
                 p_rgh { mean on; prime2Mean off; base time; } );
    }
%s%s%s}
""" % (tfin, prom_desde, fun('caudal_entrada', 'inlet'), fun('caudal_salida', 'outlet'), fun('caudal_malla', 'malla')))
    w(os.path.join(d, 'constant', 'fvOptions'), """FoamFile { version 2.0; format ascii; class dictionary; object fvOptions; }
limitU
{
    type            limitVelocity;
    active          yes;
    selectionMode   all;
    max             6;
}
""")
    w(os.path.join(d, 'Allrun'), """#!/bin/bash
source /usr/lib/openfoam/openfoam2512/etc/bashrc
NP=%d
blockMesh > log.blockMesh 2>&1
snappyHexMesh -overwrite > log.snappy 2>&1
checkMesh > log.checkMesh 2>&1
[ "%d" = "1" ] && exit 0
cp -r 0.orig 0
decomposePar > log.decompose 2>&1
mpirun --use-hwthread-cpus -np $NP interFoam -parallel > log.interFoam 2>&1
reconstructPar -latestTime > log.reconstruct 2>&1
postProcess -func writeCellCentres -latestTime > log.C 2>&1
postProcess -func writeCellVolumes -latestTime > log.V 2>&1
""" % (npr, 1 if solo_malla else 0))
    print('caso %s: fondo %dx%dx%d celdas de %.0f mm; pelicula nivel %d (%.2f mm); tfin %g s; promedio desde %g s' % (
        nombre, nx, ny, nz, base * 1e3, n_pel, base * 1e3 / 2 ** n_pel, tfin, prom_desde))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('nombre')
    ap.add_argument('--drenaje', type=float, default=0.15, help='fraccion del caudal total drenada por toda la malla (0 = sin drenaje)')
    ap.add_argument('--base', type=float, default=16e-3)
    ap.add_argument('--n-pelicula', type=int, default=3)
    ap.add_argument('--tfin', type=float, default=2.7)
    ap.add_argument('--prom-desde', type=float, default=1.5)
    ap.add_argument('--np', type=int, default=8)
    ap.add_argument('--solo-malla', action='store_true')
    a = ap.parse_args()
    generar(a.nombre, a.drenaje, a.base, a.n_pelicula, a.tfin, a.prom_desde, a.np, a.solo_malla, 60.0)
