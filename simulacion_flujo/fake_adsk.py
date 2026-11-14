# -*- coding: utf-8 -*-
"""Simulación mínima de la API de Fusion 360 (adsk.core / adsk.fusion) para probar el script.
Registra cada extrusión como: marco del plano + lazos 2D + distancia, para reconstruirla luego."""
import math, sys, types, json

# ---------------------------------------------------------------- vectores
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def mul(a, k): return (a[0]*k, a[1]*k, a[2]*k)
def dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    L = math.sqrt(dot(a, a)); return (a[0]/L, a[1]/L, a[2]/L)

class Point3D:
    def __init__(self, x, y, z): self.x, self.y, self.z = x, y, z
    @staticmethod
    def create(x=0, y=0, z=0): return Point3D(x, y, z)
    def t(self): return (self.x, self.y, self.z)
    def distanceTo(self, o): return math.dist(self.t(), o.t())

class Vector3D(Point3D):
    @staticmethod
    def create(x=0, y=0, z=0): return Vector3D(x, y, z)
    def transformBy(self, m):
        v = add(add(mul(m.u, self.x), mul(m.v, self.y)), mul(m.n, self.z))
        self.x, self.y, self.z = v; return True

class Matrix3D:
    def __init__(self, o=(0,0,0), u=(1,0,0), v=(0,1,0), n=(0,0,1)): self.o, self.u, self.v, self.n = o, u, v, n
    @staticmethod
    def create(): return Matrix3D()

class ValueInput:
    def __init__(self, v): self.value = v
    @staticmethod
    def createByReal(v): return ValueInput(v)

class ObjectCollection(list):
    @staticmethod
    def create(): return ObjectCollection()
    def add(self, x): self.append(x); return True
    @property
    def count(self): return len(self)
    def item(self, i): return self[i]

# ---------------------------------------------------------------- planos
class Plane:
    def __init__(self, o, u, v):
        self.o, self.u, self.v = o, norm(u), norm(v); self.n = norm(cross(self.u, self.v))
    @property
    def origin(self): return Point3D(*self.o)

class ConstructionPlane:
    def __init__(self, plane, comp): self.plane, self.comp = plane, comp; self.isLightBulbOn = True; self.name = ''
    @property
    def geometry(self): return self.plane
    def deleteMe(self): self.comp.n_planes -= 1

class PlaneInput:
    def setByOffset(self, base, vi):
        b = base.plane; self.plane = Plane(add(b.o, mul(b.n, vi.value)), b.u, b.v)
    def setByThreePoints(self, a, b, c):
        pa, pb, pc = (p.model() for p in (a, b, c))
        u = sub(pb, pa); n = norm(cross(u, sub(pc, pa))); v = cross(n, norm(u))
        self.plane = Plane(pa, u, v)

class ConstructionPlanes:
    def __init__(self, comp): self.comp = comp
    def createInput(self): return PlaneInput()
    def add(self, inp): self.comp.n_planes += 1; return ConstructionPlane(inp.plane, self.comp)

# ---------------------------------------------------------------- bocetos
class SketchPoint:
    def __init__(self, sk, p): self.sk, self.p = sk, p
    @property
    def geometry(self): return Point3D(*self.p)
    def model(self):
        pl = self.sk.plane; x, y, z = self.p
        return add(add(add(pl.o, mul(pl.u, x)), mul(pl.v, y)), mul(pl.n, z))

class Curve:
    def __init__(self, sk, a, b, muestras, cerrada=False):
        self.startSketchPoint, self.endSketchPoint = a, b; self.muestras = muestras; self.cerrada = cerrada

class SketchPoints:
    def __init__(self, sk): self.sk = sk; self.lst = [SketchPoint(sk, (0, 0, 0))]
    def add(self, p): sp = SketchPoint(self.sk, p.t()); self.lst.append(sp); return sp
    @property
    def count(self): return len(self.lst)
    def item(self, i): return self.lst[i]

def _sp(sk, p): return p if isinstance(p, SketchPoint) else sk.sketchPoints.add(p)

class Lines:
    def __init__(self, sk): self.sk = sk
    def addByTwoPoints(self, a, b):
        a, b = _sp(self.sk, a), _sp(self.sk, b)
        c = Curve(self.sk, a, b, [a.p, b.p]); self.sk.curvas.append(c); return c

class Arcs:
    def __init__(self, sk): self.sk = sk
    def addByThreePoints(self, a, m, b):
        pa, pm, pb = a.t(), m.t(), b.t()
        ax, ay, bx, by, cx, cy = pa[0], pa[1], pm[0], pm[1], pb[0], pb[1]
        d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
        ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
        uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
        r = math.hypot(ax-ux, ay-uy)
        t0, tm, t1 = (math.atan2(p[1]-uy, p[0]-ux) for p in (pa, pm, pb))
        def unw(t, ref):
            while t - ref > math.pi: t -= 2*math.pi
            while t - ref < -math.pi: t += 2*math.pi
            return t
        tm = unw(tm, t0); t1 = unw(t1, tm)
        n = 32; pts = [(ux + r*math.cos(t0+(t1-t0)*k/n), uy + r*math.sin(t0+(t1-t0)*k/n), 0) for k in range(n+1)]
        pts[0], pts[-1] = pa, pb
        sa, sb = self.sk.sketchPoints.add(a), self.sk.sketchPoints.add(b)
        c = Curve(self.sk, sa, sb, pts); self.sk.curvas.append(c); return c

class Circles:
    def __init__(self, sk): self.sk = sk
    def addByCenterRadius(self, c, r):
        cx, cy = c.x, c.y
        pts = [(cx + r*math.cos(2*math.pi*k/64), cy + r*math.sin(2*math.pi*k/64), 0) for k in range(64)]
        cv = Curve(self.sk, None, None, pts, cerrada=True); self.sk.curvas.append(cv); return cv

class Constraints:
    def addCoincident(self, a, b): return True

def area(poly):
    return 0.5*sum(poly[i][0]*poly[(i+1) % len(poly)][1]-poly[(i+1) % len(poly)][0]*poly[i][1] for i in range(len(poly)))

def dentro(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i][:2]; x2, y2 = poly[(i+1) % len(poly)][:2]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: c = not c
    return c

class Profile:
    def __init__(self, sk, lazos): self.sk, self.lazos = sk, lazos
    @property
    def profileLoops(self): return types.SimpleNamespace(count=len(self.lazos))
    def areaProperties(self):
        return types.SimpleNamespace(area=abs(area(self.lazos[0])) - sum(abs(area(l)) for l in self.lazos[1:]))

class Sketch:
    def __init__(self, comp, plane):
        self.comp, self.plane = comp, plane; self.name = ''; self.isComputeDeferred = False; self.isVisible = True
        self.curvas = []; self.sketchPoints = SketchPoints(self)
        self.sketchCurves = types.SimpleNamespace(sketchLines=Lines(self), sketchArcs=Arcs(self), sketchCircles=Circles(self))
        self.geometricConstraints = Constraints()
    @property
    def transform(self): return Matrix3D(self.plane.o, self.plane.u, self.plane.v, self.plane.n)
    def modelToSketchSpace(self, p):
        d = sub(p.t(), self.plane.o); return Point3D(dot(d, self.plane.u), dot(d, self.plane.v), dot(d, self.plane.n))
    def _lazos(self):
        K = lambda p: (round(p[0], 6), round(p[1], 6))
        lazos = [c.muestras for c in self.curvas if c.cerrada]
        abiertas = [c for c in self.curvas if not c.cerrada]
        usadas = [False]*len(abiertas)
        for i, c in enumerate(abiertas):
            if usadas[i]: continue
            usadas[i] = True; cadena = list(c.muestras); ini = K(cadena[0])
            while K(cadena[-1]) != ini:
                fin = K(cadena[-1]); hallada = False
                for j, d in enumerate(abiertas):
                    if usadas[j]: continue
                    if K(d.muestras[0]) == fin: cadena += d.muestras[1:]; usadas[j] = hallada = True; break
                    if K(d.muestras[-1]) == fin: cadena += d.muestras[::-1][1:]; usadas[j] = hallada = True; break
                if not hallada: raise RuntimeError('contorno abierto en %s' % self.name)
            lazos.append(cadena[:-1])
        return lazos
    @property
    def profiles(self):
        lazos = self._lazos(); padres = []
        for i, l in enumerate(lazos):
            cont = [j for j, m in enumerate(lazos) if j != i and dentro(l[0][:2], m)]
            padres.append(min(cont, key=lambda j: abs(area(lazos[j]))) if cont else None)
        prs = [Profile(self, [l] + [lazos[j] for j in range(len(lazos)) if padres[j] == i]) for i, l in enumerate(lazos)]
        return ObjectCollection(prs)

class Sketches:
    def __init__(self, comp): self.comp = comp
    def add(self, pl): comp = self.comp; sk = Sketch(comp, pl.plane); comp.n_sketches += 1; return sk

# ---------------------------------------------------------------- cuerpos y operaciones
REGISTRO = {'cuerpos': [], 'cortes': []}
class Body:
    def __init__(self, comp, piezas): self.comp, self.piezas, self.name = comp, piezas, ''; self.vivo = True

def _pieza(prof, dist):
    pl = prof.sk.plane
    return {'o': pl.o, 'u': pl.u, 'v': pl.v, 'n': pl.n, 'lazos': [[p[:2] for p in l] for l in prof.lazos], 'dist': dist}

class ExtrudeFeatures:
    def __init__(self, comp): self.comp = comp
    def addSimple(self, prof, vi, op):
        prs = list(prof) if isinstance(prof, ObjectCollection) else [prof]
        if op == 'CUT':
            REGISTRO['cortes'].append({'comp': self.comp.name, 'pieza': _pieza(prs[0], vi.value),
                                       'antes_de': len(REGISTRO['cuerpos'])})
            return types.SimpleNamespace(bodies=ObjectCollection())
        bs = ObjectCollection()
        for p in prs:
            b = Body(self.comp, [_pieza(p, vi.value)]); self.comp.bodies.append(b); REGISTRO['cuerpos'].append(b); bs.add(b)
        return types.SimpleNamespace(bodies=bs)

class CombineInput:
    def __init__(self, t, tools): self.t, self.tools = t, tools; self.operation = None; self.isKeepToolBodies = True

class CombineFeatures:
    def __init__(self, comp): self.comp = comp
    def createInput(self, t, tools): return CombineInput(t, tools)
    def add(self, inp):
        for b in inp.tools:
            inp.t.piezas.append({'tipo': 'cuerpo', 'piezas': b.piezas, 'op': inp.operation or 'JOIN'})
            b.vivo = False; self.comp.bodies.remove(b)

class LoftInput:
    def __init__(self, op): self.op = op; self.loftSections = ObjectCollection(); self.isSolid = False
class LoftFeatures:
    def __init__(self, comp): self.comp = comp
    def createInput(self, op): return LoftInput(op)
    def add(self, inp):
        assert inp.op == 'NEW' and inp.isSolid and len(inp.loftSections) >= 2
        secs = []
        for pr in inp.loftSections:
            assert len(pr.lazos) == 1, 'seccion de loft con varios lazos'
            pl = pr.sk.plane; secs.append({'o': pl.o, 'u': pl.u, 'v': pl.v, 'lazo': [p[:2] for p in pr.lazos[0]]})
        b = Body(self.comp, [{'tipo': 'loft', 'secciones': secs}]); self.comp.bodies.append(b); REGISTRO['cuerpos'].append(b)
        return types.SimpleNamespace(bodies=ObjectCollection([b]))

class AxisInput:
    def setByTwoPoints(self, a, b):
        self.pts = (a.model(), b.model())
class ConstructionAxes:
    def __init__(self, comp): self.comp = comp
    def createInput(self): return AxisInput()
    def add(self, inp): return types.SimpleNamespace(pts=inp.pts, isLightBulbOn=True)

class RevolveInput:
    def __init__(self, prof, eje, op): self.prof, self.eje, self.op = prof, eje, op; self.ang = None
    def setAngleExtent(self, sim, vi): self.ang = vi.value
class RevolveFeatures:
    def __init__(self, comp): self.comp = comp
    def add(self, inp):
        assert inp.op == 'NEW'
        pl = inp.prof.sk.plane
        pieza = {'tipo': 'revol', 'o': pl.o, 'u': pl.u, 'v': pl.v,
                 'lazos': [[q[:2] for q in l] for l in inp.prof.lazos],
                 'eje': [list(inp.eje.pts[0]), list(inp.eje.pts[1])], 'ang': inp.ang}
        b = Body(self.comp, [pieza]); self.comp.bodies.append(b); REGISTRO['cuerpos'].append(b)
        return types.SimpleNamespace(bodies=ObjectCollection([b]))
    def createInput(self, prof, eje, op): return RevolveInput(prof, eje, op)

class Component:
    def __init__(self, name='root'):
        self.name = name; self.bodies = []; self.n_planes = 0; self.n_sketches = 0
        self.xYConstructionPlane = ConstructionPlane(Plane((0,0,0), (1,0,0), (0,1,0)), self)
        self.xZConstructionPlane = ConstructionPlane(Plane((0,0,0), (1,0,0), (0,0,1)), self)   # normal -Y (caso difícil)
        self.yZConstructionPlane = ConstructionPlane(Plane((0,0,0), (0,1,0), (0,0,1)), self)
        self.constructionPlanes = ConstructionPlanes(self); self.sketches = Sketches(self)
        self.constructionAxes = ConstructionAxes(self)
        self.features = types.SimpleNamespace(extrudeFeatures=ExtrudeFeatures(self), combineFeatures=CombineFeatures(self), loftFeatures=LoftFeatures(self), revolveFeatures=RevolveFeatures(self))
        self.occurrences = types.SimpleNamespace(addNewComponent=self._nuevo); self.hijos = []
    def _nuevo(self, m):
        c = Component('sin_nombre'); self.hijos.append(c); return types.SimpleNamespace(component=c)
    @property
    def bRepBodies(self): return types.SimpleNamespace(count=len(self.bodies))

# ---------------------------------------------------------------- aplicación
MENSAJES = []
class Design:
    def __init__(self):
        self.rootComponent = Component(); self.designType = None
        self.appearances = Coleccion([])
        self.appearances.addByCopy = lambda base, nombre: self.appearances.lst.append(Apariencia(nombre, base)) or self.appearances.lst[-1]
        self.fusionUnitsManager = types.SimpleNamespace(distanceDisplayUnits=None)
    @staticmethod
    def cast(x): return x

class Coleccion:
    def __init__(self, lst): self.lst = lst
    @property
    def count(self): return len(self.lst)
    def item(self, i): return self.lst[i]
    def itemByName(self, n): return next((x for x in self.lst if x.name == n), None)
class ColorProperty:
    def __init__(self, id): self.id = id; self.value = None
    @staticmethod
    def cast(x): return x if isinstance(x, ColorProperty) else None
class Apariencia:
    def __init__(self, nombre, base=None):
        self.name = nombre; self.base = base
        self.appearanceProperties = Coleccion([ColorProperty('generic_diffuse'), types.SimpleNamespace(id='x')])
class Material:
    def __init__(self, nombre): self.name = nombre; self.appearance = Apariencia(nombre + '_ap')
BIBLIOTECA = types.SimpleNamespace(materials=Coleccion([Material(n) for n in ('Steel', 'Glass Fiber', 'Glass', 'Acrylic', 'Stainless Steel')]),
    appearances=Coleccion([Apariencia(n) for n in ('Steel - Satin', 'Glass - Clear', 'Plastic - Transparent', 'Metal - Mesh')]))
class App:
    def __init__(self):
        self.activeProduct = None
        self.userInterface = types.SimpleNamespace(messageBox=lambda m: MENSAJES.append(m),
            createProgressDialog=lambda: types.SimpleNamespace(show=lambda *a: None, hide=lambda: None, progressValue=0))
        self.documents = types.SimpleNamespace(add=self._doc)
        self.activeViewport = types.SimpleNamespace(fit=lambda: None)
        self.materialLibraries = Coleccion([BIBLIOTECA])
    def _doc(self, t): self.activeProduct = Design(); return object()
_APP = App()

core = types.ModuleType('adsk.core'); fusion = types.ModuleType('adsk.fusion'); adsk = types.ModuleType('adsk')
core.Point3D, core.Vector3D, core.Matrix3D, core.ValueInput, core.ObjectCollection = Point3D, Vector3D, Matrix3D, ValueInput, ObjectCollection
core.ColorProperty = ColorProperty; core.Color = types.SimpleNamespace(create=lambda *a: a)
core.Application = types.SimpleNamespace(get=lambda: _APP)
core.DocumentTypes = types.SimpleNamespace(FusionDesignDocumentType=0)
fusion.FeatureOperations = types.SimpleNamespace(NewBodyFeatureOperation='NEW', CutFeatureOperation='CUT', JoinFeatureOperation='JOIN', IntersectFeatureOperation='INTERSECT')
fusion.Design = Design
fusion.DesignTypes = types.SimpleNamespace(ParametricDesignType=1)
fusion.DistanceUnits = types.SimpleNamespace(MillimeterDistanceUnits='mm')
adsk.core, adsk.fusion, adsk.doEvents = core, fusion, (lambda: None)
sys.modules['adsk'], sys.modules['adsk.core'], sys.modules['adsk.fusion'] = adsk, core, fusion


def ejecutar(ruta_script, salida_json):
    import importlib.util
    spec = importlib.util.spec_from_file_location('script_fusion', ruta_script)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.run(None)
    root = _APP.activeProduct.rootComponent
    datos = {'mensajes': MENSAJES, 'componentes': [], 'cortes': REGISTRO['cortes']}
    for c in root.hijos:
        datos['componentes'].append({'nombre': c.name, 'planos': c.n_planes, 'bocetos': c.n_sketches,
                                     'cuerpos': [{'nombre': b.name, 'piezas': b.piezas,
                                                  'material': getattr(getattr(b, 'material', None), 'name', None),
                                                  'apariencia': getattr(getattr(b, 'appearance', None), 'name', None), 'idx': REGISTRO['cuerpos'].index(b)}
                                                 for b in c.bodies]})
    with open(salida_json, 'w') as f: json.dump(datos, f)
    return datos

if __name__ == '__main__':
    d = ejecutar(sys.argv[1], sys.argv[2])
    print('\n'.join(d['mensajes']))
    for c in d['componentes']:
        print('%-28s cuerpos=%3d  bocetos=%3d  planos=%3d' % (c['nombre'], len(c['cuerpos']), c['bocetos'], c['planos']))
