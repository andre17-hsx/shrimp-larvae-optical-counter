# -*- coding: utf-8 -*-
"""
Contador de camaron (base VAKI Macro 1 Channel, tobogan de 20 grados y tapa de sensor estilo Sincere)
- modelo parametrico a escala real para Fusion 360.

Ejes (orientacion de modelado "Z arriba"):
    X = largo  (0 en la punta de la boca de salida, crece hacia el cajon de entrada)
    Y = ancho  (0 en el eje de la maquina)
    Z = alto   (0 en el suelo)
Todas las cotas del script estan en milimetros.
"""
import adsk.core
import adsk.fusion
import math
import traceback

# =====================================================================
# COTAS DEL PLANO (mm)
# =====================================================================
LARGO_TOTAL = 2837
ANCHO_TOTAL = 1283
ALTO_MIN = 1700
ALTO_MAX = 2300
ALTO_SOPORTE_MIN = 983
ALTO_SOPORTE_MAX = 1583
RAMPA_MIN = 470
RAMPA_MAX = 1070

# =====================================================================
# AJUSTES DE OPERACION
# =====================================================================
AJUSTE_PATAS = 0.545        # 0 = patas al minimo, 1 = al maximo (0.545 = altura dibujada)
ALTO_SALIDA = 570           # altura del eje de la boca de salida (RAMPA_MIN..RAMPA_MAX)

# =====================================================================
# GEOMETRIA (mm)
# =====================================================================
T = 3                                   # espesor de chapa inox
ANCHO_CUERPO = 1000
ALTO_CAJON = 300
ALTO_CANAL = 100
X_CAJON = 2055                          # arranque del cajon alto
X_CHAFLAN = LARGO_TOTAL - 236           # inicio del chaflan en planta
ANCHO_FRENTE = 546                      # frente trasero chaflanado
# Entrada por el fondo, sin plato ni obstaculos: la boca es el extremo ancho de un cono difusor que baja la velocidad
# del agua de ~1.2 m/s (manguera) a ~0.2 m/s antes de entrar al cajon, asi el chorro no golpea nada y no rompe la
# superficie (carga cinetica de 2 mm). X_ENTRADA deja libre la riostra trasera superior del bastidor.
X_ENTRADA, D_ENTRADA = 2672, 260
LARGO_DIFUSOR = 560                     # largo del cono, del fondo del cajon hacia abajo (unos 7.6 grados de semiangulo)
X_DEFLECTOR = 2340                      # 250 mm aguas arriba del vertedero (2 a 3 veces el calado)
DEFLECTOR_PASO_INFERIOR = 50            # hueco libre bajo el deflector (queda sumergido ~45%)
X_VERTEDERO, ALTO_VERTEDERO = 2090, 60  # la cresta del vertedero fija la pendiente de la malla
# Rampa curva (cuarto de circulo) entre el fondo del cajon y la cara de subida de la cresta, en vez de la esquina de
# 90 grados de antes. El CFD (p2_medio_grueso) mostro ahi un remolino pegado a la esquina (hasta -0.47 m/s de
# retorno, vuelta cada ~0.8 s, en una zona de ~55x35 mm) que coincide casi exactamente con este radio. Con
# RADIO_RAMPA_CRESTA = ALTO_VERTEDERO el cuarto de circulo es tangente al fondo (horizontal) en su arranque y
# tangente a la cara de la cresta (vertical) justo en la cresta, sin dejar tramo recto residual.
RADIO_RAMPA_CRESTA = ALTO_VERTEDERO
# Forma de la rampa: 'parabola' (adoptada) o 'circulo' (cuarto de circulo de RADIO_RAMPA_CRESTA, version anterior).
# La parabola sigue el borde inferior del flujo activo medido en el CFD de la rampa circular (p2_rampa_sinlabio): a
# 110 mm de la cresta el flujo empieza a separarse del fondo, a 60 mm va 14 mm arriba, a 30 mm va 35 mm arriba y llega
# a la cresta a 60 mm. z = ALTO_VERTEDERO * s^RAMPA_EXP con s = (distancia aguas arriba de la cresta -> 0..1).
# Arranca tangente al fondo y llega a la cresta con ~46 grados de subida (el flujo luego baja 12 grados por la malla).
RAMPA_FORMA = 'parabola'
RAMPA_LARGO, RAMPA_EXP = 115, 2.0       # mm de largo horizontal de la rampa y exponente de la parabola
N_RAMPA_CRESTA = 24                     # segmentos de la polilinea de la rampa
LABIO_ABAJO, LABIO_ARRIBA, ALTO_LABIO = 6, 9, 5  # labio sobre la cresta: mm que sobresale aguas abajo, aguas arriba, alto
CON_LABIO = False  # sin labio: la rampa curva termina directo en la malla inclinada (CFD p2_rampa_sinlabio: casi sin remolino en la esquina)
# Hidraulica: caudal de diseno. Fija el nivel en el cajon (cresta) y la lamina en el conteo (perfil 1D del agua)
CAUDAL_DISENO = 10.0                    # L/s
MANNING_N = 0.010                       # chapa inoxidable lisa
# Cresta: el flujo pasa por profundidad critica, Q = 1.705 b H^1.5; FACTOR_NIVEL (calibrado con la simulacion 2D)
# sube H un 2 % para que el modelo deje pasar el caudal nominal (simulacion_flujo/aproximacion.py)
COEF_VERTEDERO, FACTOR_NIVEL = 1.705, 1.022
D_MANGUERA = 110                        # diametro de succion, impulsion y purga
# Instalacion de referencia (PROPUESTA, no es parte de la maquina): de piscina a piscina con una sola
# bomba con variador de frecuencia, que fija el caudal sin estrangular ni recircular la larva.
PISCINA = (1600, 3100, -2600, -1000, 350)  # piscina de origen: x0, x1, y0, y1, alto del borde
ESP_PISCINA = 5
ALTO_DESTINO = 150                       # borde de la piscina de destino (bajo la boca de salida)
BOMBA = (2150, 2450, -900, -650, 160)    # x0, x1, y0, y1, alto
VARIADOR = (1930, 2110, -900, -760, 300)  # variador de frecuencia: fija el caudal sin estrangular
X_IMPULSION, Y_IMPULSION = 2210, -700    # salida de la bomba hacia la maquina
Z_IMPULSION = 330                        # altura del tramo horizontal (pasa bajo las riostras)
XY_SUCCION = (2430, -850)                # toma de la bomba
Y_PISCINA = -1500                        # eje de las bajadas dentro de la piscina
LARGO_MANGUERA_SALIDA = 500              # maximo; se acorta para acabar sobre la piscina de destino
# Estrechamiento del cajon ANTES de la cresta, con el agua todavia lenta (no genera ondas de choque): del ancho
# del cuerpo al ancho del canal en L_ESTRECH (forma de coseno) y L_ESTRECH_RECTO rectos justo antes de la cresta.
# Asi la cresta, la malla y el canal tienen el mismo ancho. Ver simulacion_flujo/INFORME_FLUJO.md (propuesta B).
L_ESTRECH, L_ESTRECH_RECTO, N_ESTRECH = 250, 150, 25    # N_ESTRECH: tramos de la polilinea que aproxima el coseno
# Malla de drenaje tipo cedazo (inox 316) que forma el fondo inclinado: va de la cresta del vertedero
# a la entrada del tobogan (estilo Sincere). Debajo, marco y soportes siguiendo la misma pendiente.
MALLA_MESH, ABERTURA_MALLA = 30, 0.55   # 30 mesh = 0.55 mm de abertura (PL8+). 20 mesh = 0.9 mm (PL15+)
ESP_MALLA = 1                           # espesor representativo del tejido en el modelo
MARCO_MALLA, ALTO_SOPORTE = 20, 10      # ancho de la pletina del marco y alto de marco/soportes
PASO_SOPORTE = 100                      # separacion entre barras de soporte bajo la malla
PROF_SUMIDERO = 115                     # del nivel del fondo del cajon al fondo del sumidero
X_DRENAJE = 1955
X_BRIDA, ESP_BRIDA = 1802, 6
ANCHO_TOBOGAN = 510                     # ancho exterior del canal y del tobogan
ANCHO_CANAL = ANCHO_TOBOGAN - 2 * T

# Perfil del tobogan: recta inicial + arco tangente + recta final (pendiente suave, estilo Sincere).
# La recta inicial sigue la misma pendiente que la malla, asi la lamina de agua entra sin quiebre.
PENDIENTE_INICIAL = ALTO_VERTEDERO / float(X_VERTEDERO - (X_BRIDA + ESP_BRIDA))
X_INICIO_CURVA = 1557
RADIO_CURVA = 915
ANGULO_FINAL = 20.0
X_FIN_TOBOGAN = 820
ALTO_TOBOGAN = 100                      # alto libre (perpendicular al fondo) del tobogan cerrado

# Estacion de conteo en el tramo recto final. Distancias medidas sobre el fondo desde el final del
# tobogan hacia arriba. Backlight IR en una carcasa bajo el fondo, camara lineal en la tapa del sensor.
S_ESCANEO = 250                         # linea de escaneo
LARGO_VENTANA = 50                      # largo de las ventanas (acrilico en el fondo, vidrio en la tapa)
CARCASA_BARRA = (-40, 40, 60)           # carcasa del backlight respecto a S_ESCANEO: (desde, hasta, prof.)
# Tapa del sensor (estilo Sincere): caja baja achaflanada sobre la estacion, con display y agarraderas
LARGO_TAPA_SENSOR = 360
ALTO_TAPA_SENSOR = 150
CHAFLAN_TAPA = 40
HOLGURA_TAPA = 1                        # luz entre la tapa del sensor y la tapa del tobogan

# Embudo y salida
LARGO_EMBUDO = 700                      # transicion de la boca del tobogan (rectangular) a circular
D_SALIDA, LARGO_TUBO = 165, 150
D_ACOPLE, LARGO_ACOPLE = 200, 55

# Materiales y apariencias especiales (se buscan en las bibliotecas de Fusion, ingles o espanol)
#   clave: (materiales exactos, materiales parciales, apariencias exactas, apariencias parciales,
#           palabras obligatorias en la apariencia, color RGBA de la apariencia)
MATERIALES = {
    'vidrio': (['Glass', 'Vidrio'], ['glass', 'vidrio'],
               ['Glass - Clear', 'Glass (Clear)', 'Vidrio - Transparente', 'Vidrio (transparente)'],
               ['glass', 'vidrio'], None, (200, 230, 240, 90)),
    'acrilico': (['Acrylic', 'Acrílico', 'Acrilico', 'PMMA', 'Polycarbonate', 'Policarbonato'],
                 ['acryl', 'acríl', 'acril', 'pmma', 'polycarbonate', 'policarbonato'],
                 ['Plastic - Transparent', 'Plástico - Transparente', 'Acrylic - Clear'],
                 ['transparent', 'clear', 'transparente'],
                 ['plastic', 'plástico', 'plastico', 'acryl', 'acr'], (170, 215, 255, 110)),
    'malla': (['Stainless Steel', 'Steel, Stainless 316', 'Acero inoxidable'], ['stainless', 'inoxidable'],
              ['Metal - Mesh', 'Mesh - Steel', 'Metal - Perforated'],
              ['mesh', 'malla', 'perforat', 'perforad', 'screen'], None, (70, 72, 78, 255)),
}
EXCLUIR_MATERIAL = ['fiber', 'fibra', 'wool', 'lana', 'filled', 'relleno', 'frost', 'esmerilado']

# Bastidor
PERFIL, E_PERFIL = 40, 2
Y_BASTIDOR = 540
X_LARGUEROS = (1015, 2601)
X_RUEDA, D_RUEDA, ANCHO_RUEDA, Z_EJE = 1152, 264, 80, 132
X_PATA = 2546
LADO_PATA, LADO_CAMISA = 42, 50

# =====================================================================
app = None
ui = None
NUEVO = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
CORTE = adsk.fusion.FeatureOperations.CutFeatureOperation
UNION = adsk.fusion.FeatureOperations.JoinFeatureOperation
INTERSECCION = adsk.fusion.FeatureOperations.IntersectFeatureOperation
_planos = {}
_bocetos_puntos = {}
_por_material = {'vidrio': [], 'acrilico': [], 'malla': []}


# =====================================================================
# UTILIDADES
# =====================================================================
def cm(v):
    return v / 10.0


def P(x, y, z):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def VI(v):
    return adsk.core.ValueInput.createByReal(v)


def plano(comp, base, valor):
    """Plano paralelo a XY/XZ/YZ en la coordenada de modelo indicada (verifica el sentido)."""
    bases = {'XY': comp.xYConstructionPlane,
             'XZ': comp.xZConstructionPlane,
             'YZ': comp.yZConstructionPlane}
    if abs(valor) < 1e-9:
        return bases[base]
    clave = (comp.name, base, round(valor, 4))
    if clave in _planos:
        return _planos[clave]
    for signo in (1, -1):
        entrada = comp.constructionPlanes.createInput()
        entrada.setByOffset(bases[base], VI(cm(signo * valor)))
        pl = comp.constructionPlanes.add(entrada)
        o = pl.geometry.origin
        real = {'XY': o.z, 'XZ': o.y, 'YZ': o.x}[base]
        if abs(real - cm(valor)) < 1e-6:
            pl.isLightBulbOn = False
            pl.name = 'Plano_%s_%g' % (base, valor)
            _planos[clave] = pl
            return pl
        pl.deleteMe()
    raise RuntimeError('No se pudo crear el plano %s = %g mm' % (base, valor))


def plano_3p(comp, a, b, c):
    """Plano oblicuo por tres puntos de modelo."""
    sk = _bocetos_puntos.get(comp.name)
    if sk is None:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'Puntos_de_construccion'
        _bocetos_puntos[comp.name] = sk
    pts = [sk.sketchPoints.add(sk.modelToSketchSpace(P(*p))) for p in (a, b, c)]
    entrada = comp.constructionPlanes.createInput()
    entrada.setByThreePoints(pts[0], pts[1], pts[2])
    pl = comp.constructionPlanes.add(entrada)
    pl.isLightBulbOn = False
    return pl


def boceto(comp, pl, nombre):
    sk = comp.sketches.add(pl)
    sk.name = 'Sk_' + nombre
    sk.isComputeDeferred = True
    return sk


def S(sk, p):
    return sk.modelToSketchSpace(P(*p))


def poligono(sk, puntos):
    lineas = sk.sketchCurves.sketchLines
    pts = [S(sk, p) for p in puntos]
    primera = anterior = None
    for i in range(len(pts)):
        ini = anterior.endSketchPoint if anterior else pts[0]
        fin = primera.startSketchPoint if i == len(pts) - 1 else pts[i + 1]
        ln = lineas.addByTwoPoints(ini, fin)
        if primera is None:
            primera = ln
        anterior = ln


def circulo(sk, centro, r):
    sk.sketchCurves.sketchCircles.addByCenterRadius(S(sk, centro), cm(r))


def contorno(sk, inicio, segmentos):
    """Contorno cerrado con rectas ('L', p) y arcos por tres puntos ('A', p_medio, p_final)."""
    lineas = sk.sketchCurves.sketchLines
    arcos = sk.sketchCurves.sketchArcs
    actual = inicio
    for s in segmentos:
        if s[0] == 'L':
            lineas.addByTwoPoints(S(sk, actual), S(sk, s[1]))
            actual = s[1]
        else:
            arcos.addByThreePoints(S(sk, actual), S(sk, s[1]), S(sk, s[2]))
            actual = s[2]
    lineas.addByTwoPoints(S(sk, actual), S(sk, inicio))
    # Une los extremos coincidentes para que el contorno quede cerrado
    pts = [sk.sketchPoints.item(i) for i in range(sk.sketchPoints.count)]
    coords = [p.geometry for p in pts]
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if coords[i].distanceTo(coords[j]) < 1e-6:
                try:
                    sk.geometricConstraints.addCoincident(pts[i], pts[j])
                except Exception:
                    pass


def perfil(sk, anillo=False):
    """Perfil de mayor area con 1 lazo (o con 2 lazos si anillo=True)."""
    sk.isComputeDeferred = False
    mejor = None
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        lazos = pr.profileLoops.count
        if (anillo and lazos == 2) or (not anillo and lazos == 1):
            area = pr.areaProperties().area
            if mejor is None or area > mejor[0]:
                mejor = (area, pr)
    if mejor is None:
        raise RuntimeError('El boceto %s no tiene un perfil valido' % sk.name)
    return mejor[1]


def extruir(comp, sk, prof, distancia, hacia, nombre, operacion=None):
    """Extrusion simple hacia la direccion de modelo 'hacia', sea cual sea la normal del boceto."""
    n = adsk.core.Vector3D.create(0, 0, 1)
    n.transformBy(sk.transform)
    signo = 1 if (n.x * hacia[0] + n.y * hacia[1] + n.z * hacia[2]) >= 0 else -1
    ext = comp.features.extrudeFeatures.addSimple(prof, VI(signo * cm(distancia)), operacion or NUEVO)
    if operacion in (None, NUEVO):
        cuenta = ext.bodies.count
        for i in range(cuenta):
            ext.bodies.item(i).name = nombre if cuenta == 1 else '%s_%02d' % (nombre, i + 1)
        return ext.bodies.item(0) if cuenta else None
    return None


def caja(comp, x0, x1, y0, y1, z0, z1, nombre):
    sk = boceto(comp, plano(comp, 'XY', z0), nombre)
    poligono(sk, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)])
    return extruir(comp, sk, perfil(sk), z1 - z0, (0, 0, 1), nombre)


def _seccion(eje, ini):
    if eje == 'X':
        return 'YZ', (lambda u, v: (ini, u, v)), (1, 0, 0)
    if eje == 'Y':
        return 'XZ', (lambda u, v: (u, ini, v)), (0, 1, 0)
    return 'XY', (lambda u, v: (u, v, ini)), (0, 0, 1)


def tubo_cuadrado(comp, eje, cu, cv, ini, largo, lado, espesor, nombre):
    """Tubo cuadrado a lo largo de un eje; (cu, cv) = centro de la seccion, ini = coordenada inicial."""
    base, punto, direccion = _seccion(eje, ini)
    sk = boceto(comp, plano(comp, base, ini), nombre)
    medidas = (lado / 2.0, lado / 2.0 - espesor) if espesor > 0 else (lado / 2.0,)
    for h in medidas:
        poligono(sk, [punto(cu - h, cv - h), punto(cu + h, cv - h),
                      punto(cu + h, cv + h), punto(cu - h, cv + h)])
    return extruir(comp, sk, perfil(sk, anillo=espesor > 0), largo, direccion, nombre)


def cilindro(comp, eje, cu, cv, ini, largo, r_ext, r_int, nombre):
    base, punto, direccion = _seccion(eje, ini)
    sk = boceto(comp, plano(comp, base, ini), nombre)
    circulo(sk, punto(cu, cv), r_ext)
    if r_int > 0:
        circulo(sk, punto(cu, cv), r_int)
    return extruir(comp, sk, perfil(sk, anillo=r_int > 0), largo, direccion, nombre)


def placa_xz(comp, y0, ancho, pts_xz, nombre, segmentos=None):
    """Placa con contorno en el plano XZ (y = y0), extruida 'ancho' en +Y."""
    sk = boceto(comp, plano(comp, 'XZ', y0), nombre)
    if segmentos is None:
        poligono(sk, [(x, y0, z) for x, z in pts_xz])
    else:
        contorno(sk, (pts_xz[0], y0, pts_xz[1]),
                 [(s[0],) + tuple((p[0], y0, p[1]) for p in s[1:]) for s in segmentos])
    return extruir(comp, sk, perfil(sk), ancho, (0, 1, 0), nombre)


def placa_oblicua(comp, esquinas, espesor, hacia, nombre):
    """Placa plana definida por 4 esquinas coplanares (modelo), con espesor hacia 'hacia'."""
    pl = plano_3p(comp, esquinas[0], esquinas[1], esquinas[2])
    sk = boceto(comp, pl, nombre)
    poligono(sk, esquinas)
    return extruir(comp, sk, perfil(sk), espesor, hacia, nombre)


def seccion_loft(comp, pl, nombre, rect=None, centro=None, r=None):
    """Perfil de una sola curva cerrada (rectangulo o circulo) para un loft."""
    sk = boceto(comp, pl, nombre)
    if rect:
        poligono(sk, rect)
    else:
        circulo(sk, centro, r)
    return perfil(sk)


def loft(comp, secciones, nombre):
    entrada = comp.features.loftFeatures.createInput(NUEVO)
    for pr in secciones:
        entrada.loftSections.add(pr)
    entrada.isSolid = True
    cuerpo = comp.features.loftFeatures.add(entrada).bodies.item(0)
    cuerpo.name = nombre
    return cuerpo


def combinar(comp, objetivo, herramientas, operacion):
    coleccion = adsk.core.ObjectCollection.create()
    for h in herramientas:
        coleccion.add(h)
    entrada = comp.features.combineFeatures.createInput(objetivo, coleccion)
    entrada.operation = operacion
    entrada.isKeepToolBodies = False
    comp.features.combineFeatures.add(entrada)


def _items(coleccion):
    try:
        return [coleccion.item(i) for i in range(coleccion.count)]
    except Exception:
        return []


def _buscar(bibliotecas, atributo, exactos, parciales, obligatorio=None):
    for lib in bibliotecas:
        for nombre in exactos:
            try:
                x = getattr(lib, atributo).itemByName(nombre)
                if x:
                    return x
            except Exception:
                pass
    for lib in bibliotecas:
        for x in _items(getattr(lib, atributo)):
            nm = x.name.lower()
            if any(p in nm for p in parciales) and not any(e in nm for e in EXCLUIR_MATERIAL) \
                    and (obligatorio is None or any(o in nm for o in obligatorio)):
                return x
    return None


def asignar_materiales(app, design):
    """Material fisico + apariencia propia: vidrio y acrilico transparentes, malla de inox con aspecto de tejido."""
    informe = []
    bibliotecas = _items(app.materialLibraries)
    for clave, (m_ex, m_par, a_ex, a_par, obligatorio, rgba) in MATERIALES.items():
        cuerpos = _por_material[clave]
        if not cuerpos:
            continue
        texto = clave + ': '
        material = _buscar(bibliotecas, 'materials', m_ex, m_par)
        if material:
            for b in cuerpos:
                b.material = material
            texto += material.name
        # Apariencia propia en el diseno (copia de una de biblioteca). Se tine si es transparente o si
        # no hubo apariencia especifica y se usa la del material.
        base = _buscar(bibliotecas, 'appearances', a_ex, a_par, obligatorio)
        tenir = clave != 'malla' or base is None
        if base is None and material:
            base = material.appearance
        if base is not None:
            nombre = 'Contador_' + clave
            apariencia = design.appearances.itemByName(nombre)
            if not apariencia:
                apariencia = design.appearances.addByCopy(base, nombre)
                for prop in _items(apariencia.appearanceProperties) if tenir else []:
                    color = adsk.core.ColorProperty.cast(prop)
                    if color and color.id in ('transparent_color', 'generic_diffuse', 'glazing_transmittance_map',
                                              'metal_color'):
                        try:
                            color.value = adsk.core.Color.create(*rgba)
                        except Exception:
                            pass
            for b in cuerpos:
                b.appearance = apariencia
            texto += ' / apariencia: ' + base.name
        if not material and base is None:
            texto += 'no se encontro en la biblioteca (asignar a mano)'
        informe.append(texto)
    return informe


def resta(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def avanza(p, v, k):
    return (p[0] + v[0] * k, p[1] + v[1] * k, p[2] + v[2] * k)


def cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unitario(v):
    L = math.sqrt(sum(c * c for c in v))
    return (v[0] / L, v[1] / L, v[2] / L), L


def perpendicular(d):
    return unitario(cruz(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))[0]


def eje_construccion(comp, p0, p1):
    """Eje de construccion por dos puntos de modelo (para las revoluciones)."""
    sk = _bocetos_puntos.get(comp.name)
    if sk is None:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = 'Puntos_de_construccion'
        _bocetos_puntos[comp.name] = sk
    pts = [sk.sketchPoints.add(sk.modelToSketchSpace(P(*p))) for p in (p0, p1)]
    entrada = comp.constructionAxes.createInput()
    entrada.setByTwoPoints(pts[0], pts[1])
    eje = comp.constructionAxes.add(entrada)
    eje.isLightBulbOn = False
    return eje


def codo(comp, esquina, d_ent, d_sal, r_ext, r_int, radio, nombre):
    """Codo de 90 grados entre dos tramos rectos: revolucion de la seccion anular alrededor del eje
    del codo. Los extremos quedan tangentes a los tramos (a 'radio' de la esquina)."""
    t1 = avanza(esquina, d_ent, -radio)                   # punto de tangencia de entrada
    eje_v = unitario(cruz(d_ent, d_sal))[0]
    centro = avanza(t1, d_sal, radio)
    pl = plano_3p(comp, t1, avanza(t1, d_sal, 100), avanza(t1, eje_v, 100))
    sk = boceto(comp, pl, nombre)
    circulo(sk, t1, r_ext)
    circulo(sk, t1, r_int)
    entrada = comp.features.revolveFeatures.createInput(
        perfil(sk, anillo=True), eje_construccion(comp, centro, avanza(centro, eje_v, 100)), NUEVO)
    entrada.setAngleExtent(False, VI(math.pi / 2.0))
    cuerpo = comp.features.revolveFeatures.add(entrada).bodies.item(0)
    cuerpo.name = nombre
    return cuerpo


def tuberia(comp, puntos, r_ext, r_int, radio, nombre):
    """Tuberia poligonal (giros de 90 grados) con tramos rectos y codos, unida en un solo cuerpo."""
    tramos, dirs = [], []
    for i in range(len(puntos) - 1):
        d, L = unitario(resta(puntos[i + 1], puntos[i]))
        dirs.append((d, L))
    for i, (d, L) in enumerate(dirs):
        recorte_ini = 0.0 if i == 0 else radio
        recorte_fin = 0.0 if i == len(dirs) - 1 else radio
        if L - recorte_ini - recorte_fin <= 0:
            raise RuntimeError('Tramo demasiado corto para el radio de codo en %s' % nombre)
        tramos.append(tubo_oblicuo(comp, avanza(puntos[i], d, recorte_ini), d, perpendicular(d),
                                   L - recorte_ini - recorte_fin, r_ext, r_int, '%s_tramo_%d' % (nombre, i + 1)))
    for i in range(1, len(dirs)):
        tramos.append(codo(comp, puntos[i], dirs[i - 1][0], dirs[i][0], r_ext, r_int, radio,
                           '%s_codo_%d' % (nombre, i)))
    if len(tramos) > 1:
        combinar(comp, tramos[0], tramos[1:], UNION)
    tramos[0].name = nombre
    return tramos[0]


def tubo_oblicuo(comp, inicio, direccion, normal, largo, r_ext, r_int, nombre):
    """Tubo recto en cualquier direccion; el boceto va en el plano perpendicular a 'direccion'."""
    u = perpendicular(direccion)
    pl = plano_3p(comp, inicio, avanza(inicio, u, 100), avanza(inicio, cruz(direccion, u), 100))
    sk = boceto(comp, pl, nombre)
    circulo(sk, inicio, r_ext)
    if r_int > 0:
        circulo(sk, inicio, r_int)
    return extruir(comp, sk, perfil(sk, anillo=r_int > 0), largo, direccion, nombre)


def recta_offset(p1, p2, d, lado):
    """Recta paralela a p1-p2 desplazada d hacia el lado indicado (+1 izquierda, -1 derecha)."""
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(vx, vy)
    vx, vy = vx / L, vy / L
    nx, ny = -vy * lado, vx * lado
    return (p1[0] + nx * d, p1[1] + ny * d), (vx, vy)


def cruce(r1, r2):
    (p, u), (q, v) = r1, r2
    den = u[0] * v[1] - u[1] * v[0]
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
    return p[0] + u[0] * t, p[1] + u[1] * t


def cruce_x(r, x):
    (p, u) = r
    t = (x - p[0]) / u[0]
    return x, p[1] + u[1] * t


def cruce_y(r, y):
    (p, u) = r
    t = (y - p[1]) / u[1]
    return p[0] + u[0] * t, y


# =====================================================================
# GEOMETRIA DERIVADA
# =====================================================================
def geometria():
    g = {}
    g['ZC'] = ALTO_SOPORTE_MIN + AJUSTE_PATAS * (ALTO_SOPORTE_MAX - ALTO_SOPORTE_MIN)
    g['ZR'] = g['ZC'] - T - PERFIL                  # cara inferior de los largueros
    g['X0'] = X_BRIDA + ESP_BRIDA                   # inicio del tobogan (cara aguas arriba de la brida)
    g['t1'] = math.atan(PENDIENTE_INICIAL)
    g['t2'] = math.radians(ANGULO_FINAL)
    g['X1'] = X_INICIO_CURVA
    g['Z1'] = g['ZC'] - (g['X0'] - g['X1']) * PENDIENTE_INICIAL
    tm = (g['t1'] + g['t2']) / 2.0
    g['Xm'] = g['X1'] - RADIO_CURVA * (math.sin(tm) - math.sin(g['t1']))
    g['Zm'] = g['Z1'] + RADIO_CURVA * (math.cos(tm) - math.cos(g['t1']))
    g['X2'] = g['X1'] - RADIO_CURVA * (math.sin(g['t2']) - math.sin(g['t1']))
    g['Z2'] = g['Z1'] + RADIO_CURVA * (math.cos(g['t2']) - math.cos(g['t1']))
    g['XE'] = X_FIN_TOBOGAN
    g['ZE'] = g['Z2'] - (g['X2'] - g['XE']) * math.tan(g['t2'])
    g['techo'] = techo_tobogan(g, ALTO_TOBOGAN)                 # cara inferior de la tapa del tobogan
    g['techo_ext'] = techo_tobogan(g, ALTO_TOBOGAN + T)         # cara superior de la tapa
    g['H_EMB'] = g['techo'][4][1] - g['ZE']                     # alto de la boca del tobogan en X = XE
    # Estacion de conteo en el tramo recto final: ventanas con cortes verticales
    c2, s2 = math.cos(g['t2']), math.sin(g['t2'])
    s_recta = (g['X2'] - g['XE']) / c2                          # largo del tramo recto del fondo
    x_c = g['XE'] + S_ESCANEO * c2 - (ALTO_TOBOGAN + T / 2.0) * s2   # eje de la camara a la altura de la tapa
    g['VF'] = (g['XE'] + (S_ESCANEO - LARGO_VENTANA / 2.0) * c2, g['XE'] + (S_ESCANEO + LARGO_VENTANA / 2.0) * c2)
    g['VT'] = (x_c - LARGO_VENTANA / 2.0 * c2, x_c + LARGO_VENTANA / 2.0 * c2)
    g['U_TAPA'] = (S_ESCANEO - LARGO_TAPA_SENSOR / 2.0, S_ESCANEO + LARGO_TAPA_SENSOR / 2.0)
    fuera = (g['U_TAPA'][0] < 0 or g['U_TAPA'][1] > s_recta - 20 or
             S_ESCANEO + CARCASA_BARRA[1] > s_recta or g['VT'][1] > g['techo_ext'][3][0])
    if fuera:
        raise RuntimeError('La estacion de conteo y su tapa deben quedar en el tramo recto final '
                           '(%.0f mm de largo)' % s_recta)
    # Hidraulica del caudal de diseno: cresta con el ancho del canal (Q = 1.705 b H^1.5, ver COEF_VERTEDERO) y
    # lamina en el conteo por el perfil 1D del agua (perfil_conteo). Distancias en mm, calculos en SI.
    caudal = CAUDAL_DISENO / 1000.0
    b_vert = ANCHO_CANAL / 1000.0
    g['H_VERT'] = 1000.0 * FACTOR_NIVEL * (caudal / (COEF_VERTEDERO * b_vert)) ** (2.0 / 3.0)
    g['NIVEL'] = ALTO_VERTEDERO + g['H_VERT']                   # calado en el cajon sobre su fondo
    g['MARGEN_CAJON'] = ALTO_CAJON - g['NIVEL']                 # borde libre hasta el canto del cajon
    g['V_MANGUERA'] = caudal / (math.pi * (D_MANGUERA / 2000.0 - T / 1000.0) ** 2)
    g['V_BOCA'] = caudal / (math.pi * (D_ENTRADA / 2000.0 - T / 1000.0) ** 2)
    h_c, v_c, fr_c = perfil_conteo(g)
    g['LAMINA'], g['V_CONTEO'], g['FR_CONTEO'] = 1000.0 * h_c, v_c, fr_c
    largo = LARGO_EMBUDO + LARGO_TUBO + LARGO_ACOPLE
    s = (g['ZE'] + g['H_EMB'] / 2.0 - ALTO_SALIDA) / largo
    g['alfa_limitado'] = s < math.sin(math.radians(5)) or s > math.sin(math.radians(60))
    s = min(max(s, math.sin(math.radians(5))), math.sin(math.radians(60)))
    g['alfa'] = math.asin(s)
    g['Z_SALIDA'] = g['ZE'] + g['H_EMB'] / 2.0 - largo * s
    return g


def perfil_conteo(g):
    """Lamina (m), velocidad (m/s) y Froude en la linea de escaneo, por el perfil 1D del agua (metodo del paso
    estandar): parte de la profundidad critica en la cresta y sigue la rama supercritica con la ecuacion de energia
    H = z + h (cos t - V^2 k / g) + V^2 / 2g (k = 1/R en el arco convexo) y la friccion de Manning, ancho constante
    ANCHO_CANAL. NO incluye el agua que drena la malla (la adelgaza). Misma formulacion que
    simulacion_flujo/flujo_1d.py; la friccion es solo de fondo y paredes lisas."""
    G = 9.81
    Q, b, n, R = CAUDAL_DISENO / 1000.0, ANCHO_CANAL / 1000.0, MANNING_N, RADIO_CURVA / 1000.0
    t1, t2 = g['t1'], g['t2']
    s_a0 = (math.hypot(X_VERTEDERO - g['X0'], ALTO_VERTEDERO) + (g['X0'] - g['X1']) / math.cos(t1)) / 1000.0
    s_a1 = s_a0 + R * (t2 - t1)
    s_fin = s_a1 + (g['X2'] - g['XE']) / math.cos(t2) / 1000.0 - S_ESCANEO / 1000.0     # linea de escaneo
    tita = lambda x: t1 if x <= s_a0 else (t2 if x >= s_a1 else t1 + (x - s_a0) / R)
    kap = lambda x: 1.0 / R if s_a0 < x < s_a1 else 0.0

    def energia(h, x):
        v = Q / (b * h)
        return h * math.cos(tita(x)) - v * v * h * kap(x) / G + v * v / (2 * G)

    def critica(x):                                    # h que minimiza la energia especifica (Fr = 1)
        c, k = math.cos(tita(x)), kap(x)
        lo, hi_ = 1e-4, 1.0
        for _ in range(60):
            h = 0.5 * (lo + hi_)
            d = c + Q * Q * k / (b * b * G * h * h) - Q * Q / (G * b * b * h ** 3)
            lo, hi_ = (h, hi_) if d < 0 else (lo, h)
        return 0.5 * (lo + hi_)

    def resolver(objetivo, x, h_max):                  # energia(h) = objetivo, rama supercritica (h < h_max)
        lo, hi_ = 1e-5, h_max
        for _ in range(60):
            h = 0.5 * (lo + hi_)
            lo, hi_ = (lo, h) if energia(h, x) < objetivo else (h, hi_)
        return 0.5 * (lo + hi_)

    def friccion(h):
        v = Q / (b * h)
        return n * n * v * v / (b * h / (b + 2 * h)) ** (4.0 / 3.0)

    pasos = int(round(s_fin / 0.002))
    ds = s_fin / pasos
    h, z, x = critica(0.0), 0.0, 0.0
    carga = energia(h, x)
    for _ in range(pasos):
        x1 = x + ds
        z1 = z - math.sin(tita(x + ds / 2.0)) * ds
        h_crit = critica(x1)
        e_min = energia(h_crit, x1)
        f0 = friccion(h)
        objetivo = carga - f0 * ds - z1
        h1 = resolver(objetivo, x1, h_crit) if objetivo > e_min else h_crit
        objetivo = carga - 0.5 * (f0 + friccion(h1)) * ds - z1          # corrector con la friccion media
        if objetivo > e_min:
            h1 = resolver(objetivo, x1, h_crit)
        h, z, x = h1, z1, x1
        carga = z + energia(h, x)
    v = Q / (b * h)
    return h, v, v / math.sqrt(G * math.cos(tita(x)) * h)


def techo_tobogan(g, d):
    """Curva paralela al fondo a distancia perpendicular d (recta + arco concentrico + recta).
    Devuelve [inicio_en_X0, inicio_arco, medio_arco, fin_arco, fin_en_XE] (x, z)."""
    t1, t2 = g['t1'], g['t2']
    tm = (t1 + t2) / 2.0
    sobre = lambda x, z, t: (x - d * math.sin(t), z + d * math.cos(t))
    p1, pm, p2 = sobre(g['X1'], g['Z1'], t1), sobre(g['Xm'], g['Zm'], tm), sobre(g['X2'], g['Z2'], t2)
    p0 = (g['X0'], p1[1] + (g['X0'] - p1[0]) * math.tan(t1))
    p3 = (g['XE'], p2[1] - (p2[0] - g['XE']) * math.tan(t2))
    return [p0, p1, pm, p2, p3]


def punto_rampa(g, u, v, y=0.0):
    """Punto del tramo recto final: u sobre el fondo desde XE (hacia arriba), v perpendicular al fondo."""
    c2, s2 = math.cos(g['t2']), math.sin(g['t2'])
    return (g['XE'] + u * c2 - v * s2, y, g['ZE'] + u * s2 + v * c2)


def z_fondo(g, x):
    """Cara superior del fondo del tobogan."""
    if x >= g['X1']:
        return g['ZC'] - (g['X0'] - x) * PENDIENTE_INICIAL
    if x >= g['X2']:
        s = math.sin(g['t1']) + (g['X1'] - x) / RADIO_CURVA
        return g['Z1'] + RADIO_CURVA * (math.sqrt(1 - s * s) - math.cos(g['t1']))
    return g['Z2'] - (g['X2'] - x) * math.tan(g['t2'])


def curva_fondo(g, dz=0.0):
    """Segmentos del fondo desde el inicio del tobogan hasta su final (desplazados dz en Z)."""
    return [('L', (g['X1'], g['Z1'] + dz)),
            ('A', (g['Xm'], g['Zm'] + dz), (g['X2'], g['Z2'] + dz)),
            ('L', (g['XE'], g['ZE'] + dz))]


def perfil_rampa_cresta():
    """Perfil de la rampa de la cresta: lista de (d, z) con d = mm aguas arriba de la cresta (de mayor a 0) y z = mm
    sobre el fondo del cajon, desde el arranque tangente al fondo hasta (0, ALTO_VERTEDERO)."""
    n = N_RAMPA_CRESTA
    if RAMPA_FORMA == 'circulo':
        R = RADIO_RAMPA_CRESTA
        return [(R * (1 - math.sin(k * math.pi / 2 / n)), R * (1 - math.cos(k * math.pi / 2 / n))) for k in range(n + 1)]
    return [(RAMPA_LARGO * (1 - k / n), ALTO_VERTEDERO * (k / n) ** RAMPA_EXP) for k in range(n + 1)]


def curva_estrechamiento():
    """Cara interior de la pared del estrechamiento (lado +Y), de la brida hacia el cajon: recta a ANCHO_CANAL/2
    hasta L_ESTRECH_RECTO antes de la cresta y luego, en L_ESTRECH, forma de coseno hasta la cara interior de la pared
    lateral del cajon ancho (la pared del estrechamiento pasa a ser esa pared lateral). Polilinea de N_ESTRECH
    tramos."""
    x_ini, x_recto = X_BRIDA + ESP_BRIDA, X_VERTEDERO + L_ESTRECH_RECTO
    y_ini, y_fin = ANCHO_CANAL / 2.0, ANCHO_CUERPO / 2.0 - T
    pts = [(x_ini, y_ini), (x_recto, y_ini)]
    for k in range(1, N_ESTRECH + 1):
        u = k / float(N_ESTRECH)
        pts.append((x_recto + L_ESTRECH * u, y_ini + (y_fin - y_ini) * 0.5 * (1 - math.cos(math.pi * u))))
    return pts


def y_estrechamiento(x):
    """Y de la cara interior de la pared del estrechamiento en x (sobre la misma polilinea que la pared)."""
    pts = curva_estrechamiento()
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    raise ValueError('x = %.1f fuera del estrechamiento' % x)


# =====================================================================
# COMPONENTE_SOPORTE
# =====================================================================
def construir_soporte(comp, g):
    a, e = PERFIL, E_PERFIL
    ZR = g['ZR']
    for s, lado in ((-1, 'izq'), (1, 'der')):
        y = s * Y_BASTIDOR
        # Largueros superiores: apoyan sobre las patas (las patas terminan en su cara inferior)
        tubo_cuadrado(comp, 'X', y, ZR + a / 2.0, X_LARGUEROS[0],
                      X_LARGUEROS[1] - X_LARGUEROS[0], a, e, 'larguero_superior_' + lado)
        # Pata delantera (rueda)
        tubo_cuadrado(comp, 'Z', X_RUEDA, y, Z_EJE - 20, ZR - (Z_EJE - 20), a, e,
                      'pata_delantera_' + lado)
        # Pata trasera telescopica: camisa fija bajo el larguero + pata deslizante + pie
        tubo_cuadrado(comp, 'Z', X_PATA, y, ZR - 150, 150, LADO_CAMISA, 3, 'camisa_telescopica_' + lado)
        tubo_cuadrado(comp, 'Z', X_PATA, y, 25, ZR - 30 - 25, LADO_PATA, e, 'pata_telescopica_' + lado)
        caja(comp, X_PATA - 60, X_PATA + 60, y - 60, y + 60, 15, 25, 'pie_' + lado)
        # Riostra horizontal entre caras de patas
        x_ini, x_fin = X_RUEDA + a / 2.0, X_PATA - LADO_PATA / 2.0
        tubo_cuadrado(comp, 'X', y, 467, x_ini, x_fin - x_ini, a, e, 'riostra_horizontal_' + lado)
        # Riostra diagonal con cortes verticales contra las caras de las patas
        z1, z2 = ZR - 192, 540
        hv = a / math.cos(math.atan2(z1 - z2, x_fin - x_ini))
        placa_xz(comp, y - a / 2.0, a,
                 [(x_ini, z1 - hv / 2), (x_fin, z2 - hv / 2), (x_fin, z2 + hv / 2), (x_ini, z1 + hv / 2)],
                 'riostra_diagonal_' + lado)
        # Rueda (neumatico + llanta) y eje
        y_rueda = ANCHO_TOTAL / 2.0 - ANCHO_RUEDA if s > 0 else -ANCHO_TOTAL / 2.0
        cilindro(comp, 'Y', X_RUEDA, Z_EJE, y_rueda, ANCHO_RUEDA, D_RUEDA / 2.0, 75, 'neumatico_' + lado)
        cilindro(comp, 'Y', X_RUEDA, Z_EJE, y_rueda + 5, ANCHO_RUEDA - 10, 75, 10, 'llanta_' + lado)
        y_eje = y + a / 2.0 if s > 0 else -ANCHO_TOTAL / 2.0
        cilindro(comp, 'Y', X_RUEDA, Z_EJE, y_eje, ANCHO_TOTAL / 2.0 - Y_BASTIDOR - a / 2.0,
                 10, 0, 'eje_' + lado)
    # Travesanos entre caras interiores de patas y largueros
    tubo_cuadrado(comp, 'Y', X_RUEDA, 450, -Y_BASTIDOR + a / 2.0, 2 * Y_BASTIDOR - a, a, e,
                  'travesano_delantero')
    tubo_cuadrado(comp, 'Y', X_PATA, 420, -Y_BASTIDOR + LADO_PATA / 2.0, 2 * Y_BASTIDOR - LADO_PATA,
                  a, e, 'travesano_trasero_inferior')
    tubo_cuadrado(comp, 'Y', 2498, ZR + a / 2.0, -Y_BASTIDOR + a / 2.0, 2 * Y_BASTIDOR - a, a, e,
                  'travesano_trasero_superior')
    # Apoyo del tobogan: travesano bajo el fondo + postes hasta el larguero
    z_sop = min(z_fondo(g, x) for x in range(1230, 1271, 5)) - T - 5
    tubo_cuadrado(comp, 'Y', 1250, z_sop - a / 2.0, -Y_BASTIDOR - a / 2.0, 2 * Y_BASTIDOR + a, a, e,
                  'travesano_bajo_tobogan')
    for s, lado in ((-1, 'izq'), (1, 'der')):
        tubo_cuadrado(comp, 'Z', 1250, s * Y_BASTIDOR, z_sop, ZR - z_sop, a, e, 'poste_tobogan_' + lado)


# =====================================================================
# COMPONENTE_CANAL_SUPERIOR (cajon de entrada, cuyo contorno se estrecha hasta el canal, con malla y sumidero)
# =====================================================================
def construir_canal_superior(comp, g):
    ZC, X0 = g['ZC'], g['X0']
    h, hi, f = ANCHO_CUERPO / 2.0, ANCHO_CUERPO / 2.0 - T, ANCHO_FRENTE / 2.0
    XF, XCH = LARGO_TOTAL, X_CHAFLAN
    w_sen = ANCHO_TOBOGAN / 2.0                           # semiancho exterior del canal y de las paredes del estrechamiento
    hm = ANCHO_CANAL / 2.0                                # semiancho libre de la cresta, la malla y el canal
    XV, AV = X_VERTEDERO, ALTO_VERTEDERO
    z_malla = lambda x: ZC + (x - X0) * AV / (XV - X0)    # cara superior de la malla inclinada
    # Alturas de la tapa del tobogan en la brida: el canal cierra justo contra ellas (sin holguras)
    zt_int, zt_ext = g['techo'][0][1], g['techo_ext'][0][1]

    # Contorno del cuerpo desde la brida hasta el cajon ancho: SIGUE la pared del estrechamiento. 'dentro' es su cara
    # interior y 'fuera' la exterior (chapa de espesor T, esquinas a inglete); desde x_fin siguen las paredes laterales
    # rectas del cajon. No hay zonas muertas a los lados del agua.
    x_fin = X_VERTEDERO + L_ESTRECH_RECTO + L_ESTRECH
    dentro = curva_estrechamiento()
    fuera_r = [recta_offset(dentro[i], dentro[i + 1], T, 1) for i in range(len(dentro) - 1)]
    fuera = ([cruce_x(fuera_r[0], dentro[0][0])] + [cruce(fuera_r[i], fuera_r[i + 1]) for i in range(len(fuera_r) - 1)]
             + [cruce_x(fuera_r[-1], x_fin)])
    fuera = [(x, min(y, h)) for x, y in fuera]                         # sin salirse del ancho del cuerpo
    borde = [(x, y) for x, y in fuera if x > XV]                       # contorno exterior aguas arriba de la cresta

    # Brida de union: placa cortada por la propia seccion del tobogan, asi la ventana sigue su
    # pendiente y las chapas del tobogan entran a ras, sin holguras
    brida = caja(comp, X_BRIDA, X0, -w_sen - 20, w_sen + 20, ZC - 30, ZC + 130, 'brida_union')
    dz = ESP_BRIDA * PENDIENTE_INICIAL
    hueco = placa_xz(comp, -w_sen, 2 * w_sen,
                     [(X_BRIDA, zt_ext - dz), (X0, zt_ext), (X0, ZC - T), (X_BRIDA, ZC - T - dz)],
                     'brida_ventana')
    combinar(comp, brida, [hueco], CORTE)

    # Fondo del cajon (hasta el vertedero; de ahi al tobogan el fondo es la malla inclinada), a ras del contorno
    z_f = ZC - T
    sk = boceto(comp, plano(comp, 'XY', z_f), 'fondo_cajon')
    poligono(sk, [(XV, -w_sen, z_f)] + [(x, -y, z_f) for x, y in borde] +
             [(XCH, -h, z_f), (XF, -f, z_f), (XF, f, z_f), (XCH, h, z_f)] +
             [(x, y, z_f) for x, y in borde[::-1]] + [(XV, w_sen, z_f)])
    circulo(sk, (X_ENTRADA, 0, ZC - T), D_ENTRADA / 2.0 - T)         # paso libre = interior del difusor
    extruir(comp, sk, perfil(sk, anillo=True), T, (0, 0, 1), 'fondo_cajon')

    # Paredes laterales del cajon ancho: solo hasta donde empieza el estrechamiento (x_fin); de ahi hacia la brida
    # las paredes son las del estrechamiento. Sin rebose: el caudal se regula en la impulsion y la cresta absorbe
    # cualquier exceso razonable.
    lateral = [(x_fin, ZC), (XCH, ZC), (XCH, ZC + ALTO_CAJON), (x_fin, ZC + ALTO_CAJON)]
    placa_xz(comp, -h, T, lateral, 'pared_lateral_izq')
    placa_xz(comp, hi, T, lateral, 'pared_lateral_der')

    # Regla para leer el nivel en el cajon (H sobre la cresta, Q = 1.705 x b x H^1.5), en la cara interior de la
    # pared del estrechamiento, en su tramo recto
    caja(comp, X_VERTEDERO + 30, X_VERTEDERO + L_ESTRECH_RECTO - 20, hm - 2, hm, ZC + ALTO_VERTEDERO, ZC + 150,
         'regla_nivel_H')

    # Pared trasera (chaflanes + frente) como un solo anillo con esquinas a inglete
    ext = [(XCH, -h), (XF, -f), (XF, f), (XCH, h)]
    rectas = [recta_offset(ext[i], ext[i + 1], T, 1) for i in range(3)]
    interior = [cruce_x(rectas[0], XCH), cruce(rectas[0], rectas[1]),
                cruce(rectas[1], rectas[2]), cruce_x(rectas[2], XCH)]
    sk = boceto(comp, plano(comp, 'XY', ZC), 'pared_trasera')
    poligono(sk, [(x, y, ZC) for x, y in ext + interior[::-1]])
    extruir(comp, sk, perfil(sk), ALTO_CAJON, (0, 0, 1), 'pared_trasera')

    # Cubierta del tramo bajo: del ancho exterior del canal, apoyada sobre las paredes del estrechamiento y a ras de
    # las caras interior y exterior de la tapa del tobogan
    cubierta = [(X0, zt_int), (1861, zt_int), (X_CAJON, ZC + ALTO_CAJON - T),
                (X_CAJON, ZC + ALTO_CAJON), (1861, zt_ext), (X0, zt_ext)]
    placa_xz(comp, -w_sen, 2 * w_sen, cubierta, 'cubierta_tramo_bajo')

    # Difusor de entrada: cono de D_MANGUERA a D_ENTRADA soldado bajo el fondo del cajon (loft exterior menos loft
    # interior). Sin plato ni obstaculos: el agua sube lenta (V_BOCA) y sin chocar contra nada. La manguera de
    # impulsion se conecta a su extremo inferior.
    r_b, r_t = D_MANGUERA / 2.0, D_ENTRADA / 2.0
    z_b, z_t = ZC - T - LARGO_DIFUSOR, ZC - T
    pl_b, pl_t = plano(comp, 'XY', z_b), plano(comp, 'XY', z_t)
    cono = loft(comp, [seccion_loft(comp, pl_b, 'difusor_ext_inf', centro=(X_ENTRADA, 0, z_b), r=r_b),
                       seccion_loft(comp, pl_t, 'difusor_ext_sup', centro=(X_ENTRADA, 0, z_t), r=r_t)],
                'difusor_entrada_D%d' % D_ENTRADA)
    combinar(comp, cono, [loft(comp, [
        seccion_loft(comp, pl_b, 'difusor_hueco_inf', centro=(X_ENTRADA, 0, z_b), r=r_b - T),
        seccion_loft(comp, pl_t, 'difusor_hueco_sup', centro=(X_ENTRADA, 0, z_t), r=r_t - T)],
        'difusor_hueco')], CORTE)

    # Deflector de paso inferior: tapa la parte alta y deja pasar el agua por debajo. Va de pared a pared del
    # estrechamiento (sus lados siguen la cara interior de las paredes)
    z_d = ZC + DEFLECTOR_PASO_INFERIOR
    y_d1, y_d2 = y_estrechamiento(X_DEFLECTOR), y_estrechamiento(X_DEFLECTOR + T)
    sk = boceto(comp, plano(comp, 'XY', z_d), 'deflector_paso_inferior')
    poligono(sk, [(X_DEFLECTOR, -y_d1, z_d), (X_DEFLECTOR + T, -y_d2, z_d),
                  (X_DEFLECTOR + T, y_d2, z_d), (X_DEFLECTOR, y_d1, z_d)])
    extruir(comp, sk, perfil(sk), ZC + ALTO_CAJON - z_d, (0, 0, 1), 'deflector_paso_inferior')

    # Vertedero: rampa curva (cuarto de circulo, RADIO_RAMPA_CRESTA) entre el fondo del cajon y la cresta, en vez de
    # la esquina de 90 grados. theta=0 en el arranque (tangente al fondo, aguas arriba) y theta=90 grados en la
    # cresta (tangente a la vertical). X(theta) = XV + R(1-sin theta), Z(theta) = ZC + R(1-cos theta).
    rampa = [(XV + d, ZC + z) for d, z in perfil_rampa_cresta()]
    placa_xz(comp, -hm, 2 * hm, rampa + [(XV, ZC)], 'vertedero_rampa_%s' % RAMPA_FORMA)
    # Labio: el agua cae sobre la malla inclinada que empieza en la cresta
    if CON_LABIO:
        caja(comp, XV - LABIO_ABAJO, XV + LABIO_ARRIBA, -hm, hm, ZC + AV, ZC + AV + ALTO_LABIO, 'labio_vertedero')

    # Malla de drenaje tipo cedazo (inox 316): ES el fondo inclinado entre el vertedero y el tobogan, de pared a
    # pared del estrechamiento. Debajo, marco perimetral y soportes que siguen la misma pendiente.
    nombre_malla = 'malla_cedazo_inox316_%dmesh_%s' % (MALLA_MESH, ('%.2fmm' % ABERTURA_MALLA).replace('.', 'p'))
    _por_material['malla'].append(
        placa_xz(comp, -hm, 2 * hm, [(X0, ZC), (XV, ZC + AV), (XV, ZC + AV - ESP_MALLA), (X0, ZC - ESP_MALLA)],
                 nombre_malla))
    m, alto = MARCO_MALLA, ALTO_SOPORTE
    bajo = lambda x, dz: (x, z_malla(x) - ESP_MALLA - dz)  # punto bajo la malla

    def pieza_bajo_malla(x0, x1, y0, ancho, nombre):
        placa_xz(comp, y0, ancho, [bajo(x0, 0), bajo(x1, 0), bajo(x1, alto), bajo(x0, alto)], nombre)

    pieza_bajo_malla(X0, X0 + m, -hm, 2 * hm, 'marco_malla_inferior')
    pieza_bajo_malla(XV - m, XV, -hm, 2 * hm, 'marco_malla_superior')
    pieza_bajo_malla(X0 + m, XV - m, -hm, m, 'marco_malla_izq')
    pieza_bajo_malla(X0 + m, XV - m, hm - m, m, 'marco_malla_der')
    n_sop = int((hm - m - 10) // PASO_SOPORTE)
    for i in range(-n_sop, n_sop + 1):
        pieza_bajo_malla(X0 + m, XV - m, i * PASO_SOPORTE - 3, 6, 'soporte_malla_%02d' % (i + n_sop + 1))

    # Sumidero bajo toda la malla: sus paredes laterales son la prolongacion hacia abajo de las paredes del
    # estrechamiento (mismo espesor y mismo plano), la de aguas arriba se apoya contra el fondo del cajon y la de
    # aguas abajo contra la brida. Desague centrado con valvula.
    zf = ZC - PROF_SUMIDERO                              # cara superior del fondo del sumidero
    caja(comp, X0, XV, -w_sen, -hm, zf, ZC, 'sumidero_pared_izq')
    caja(comp, X0, XV, hm, w_sen, zf, ZC, 'sumidero_pared_der')
    caja(comp, X0, X0 + T, -hm, hm, zf, ZC - 30, 'sumidero_pared_brida')   # arriba cierra la brida
    caja(comp, XV, XV + T, -w_sen, w_sen, zf, ZC - T, 'sumidero_pared_vertedero')
    sk = boceto(comp, plano(comp, 'XY', zf - T), 'sumidero_fondo')
    poligono(sk, [(X0, -w_sen, zf - T), (XV + T, -w_sen, zf - T), (XV + T, w_sen, zf - T), (X0, w_sen, zf - T)])
    circulo(sk, (X_DRENAJE, 0, zf - T), 52)
    extruir(comp, sk, perfil(sk, anillo=True), T, (0, 0, 1), 'sumidero_fondo')
    cilindro(comp, 'Z', X_DRENAJE, 0, zf - 215 - T, 215, 55, 52, 'tubo_drenaje_agua')
    cilindro(comp, 'Z', X_DRENAJE, 0, zf - 135, 45, 75, 55, 'valvula_drenaje')
    caja(comp, X_DRENAJE - 10, X_DRENAJE + 10, -160, -75, zf - 122, zf - 102, 'manija_valvula')

    # Paredes del estrechamiento: son las paredes del cuerpo entre la brida y x_fin. Continuan las paredes del
    # tobogan (cara interior a ANCHO_CANAL/2) sobre la malla y el cajon, y abren en coseno hasta las paredes
    # laterales del cajon ancho (ver curva_estrechamiento). Apoyan sobre el sumidero y el fondo del cajon y suben
    # hasta la cubierta (o hasta el canto del cajon): planta de la pared intersectada con su perfil lateral.
    perfil_lateral = [(X0, ZC), (x_fin, ZC), (x_fin, ZC + ALTO_CAJON), (X_CAJON, ZC + ALTO_CAJON),
                      (X_CAJON, ZC + ALTO_CAJON - T), (1861, zt_int), (X0, zt_int)]
    for s, lado in ((-1, 'izq'), (1, 'der')):
        z_bajo = ZC - 20
        sk = boceto(comp, plano(comp, 'XY', z_bajo), 'pared_estrechamiento_' + lado)
        poligono(sk, [(x, s * y, z_bajo) for x, y in dentro + fuera[::-1]])
        pared = extruir(comp, sk, perfil(sk), ALTO_CAJON + 40, (0, 0, 1), 'pared_estrechamiento_' + lado)
        combinar(comp, pared, [placa_xz(comp, -h, 2 * h, perfil_lateral, 'perfil_estrechamiento_' + lado)],
                 INTERSECCION)


# =====================================================================
# COMPONENTE_RAMPA_INCLINADA (tobogan cerrado, carcasa del escaner, embudo y articulacion)
# =====================================================================
def construir_rampa(comp, g):
    ZC, X0, XE, ZE = g['ZC'], g['X0'], g['XE'], g['ZE']
    w2 = ANCHO_CANAL / 2.0
    wo = w2 + T

    ti, te = g['techo'], g['techo_ext']
    c2, s2 = math.cos(g['t2']), math.sin(g['t2'])
    t2 = s2 / c2
    recta = lambda p, x: p[1] + (x - p[0]) * t2          # recta final (ANGULO_FINAL) por el punto p

    # Fondo del tobogan (banda de espesor T), partido en la ventana de acrilico de la estacion de conteo
    xf0, xf1 = g['VF']
    zf0, zf1 = recta((XE, ZE), xf0), recta((XE, ZE), xf1)
    retorno = [('L', (xf1, zf1 - T)), ('L', (g['X2'], g['Z2'] - T)),
               ('A', (g['Xm'], g['Zm'] - T), (g['X1'], g['Z1'] - T)), ('L', (X0, ZC - T))]
    placa_xz(comp, -wo, 2 * wo, (X0, ZC), 'fondo_tobogan',
             segmentos=curva_fondo(g)[:2] + [('L', (xf1, zf1))] + retorno)
    placa_xz(comp, -wo, 2 * wo, [(xf0, zf0), (XE, ZE), (XE, ZE - T), (xf0, zf0 - T)], 'fondo_tobogan_salida')
    _por_material['acrilico'].append(
        placa_xz(comp, -wo, 2 * wo, [(xf1, zf1), (xf0, zf0), (xf0, zf0 - T), (xf1, zf1 - T)],
                 'PROPUESTA_ventana_acrilico'))

    # Laterales (del fondo a la tapa)
    lateral = curva_fondo(g) + [('L', ti[4]), ('L', ti[3]), ('A', ti[2], ti[1]), ('L', ti[0])]
    placa_xz(comp, -wo, T, (X0, ZC), 'lateral_tobogan_izq', segmentos=lateral)
    placa_xz(comp, w2, T, (X0, ZC), 'lateral_tobogan_der', segmentos=lateral)

    # Tapa del tobogan paralela al fondo (desde la brida), partida en la ventana de vidrio
    xt0, xt1 = g['VT']
    zi0, zi1, ze0, ze1 = recta(ti[4], xt0), recta(ti[4], xt1), recta(te[4], xt0), recta(te[4], xt1)
    tapa = [('L', ti[1]), ('A', ti[2], ti[3]), ('L', (xt1, zi1)), ('L', (xt1, ze1)), ('L', te[3]),
            ('A', te[2], te[1]), ('L', te[0])]
    placa_xz(comp, -wo, 2 * wo, ti[0], 'tapa_tobogan', segmentos=tapa)
    placa_xz(comp, -wo, 2 * wo, [(xt0, zi0), ti[4], te[4], (xt0, ze0)], 'tapa_tobogan_salida')
    _por_material['vidrio'].append(
        placa_xz(comp, -wo, 2 * wo, [(xt1, zi1), (xt0, zi0), (xt0, ze0), (xt1, ze1)], 'vidrio_protector'))

    # Carcasa hueca bajo el fondo (abierta hacia la ventana) con la barra de backlight IR
    s_a, s_b, prof = S_ESCANEO + CARCASA_BARRA[0], S_ESCANEO + CARCASA_BARRA[1], CARCASA_BARRA[2]
    q = lambda s, dd: (XE + s * c2 + dd * s2, ZE - T + s * s2 - dd * c2)   # punto bajo el fondo
    ancho = wo                                            # paredes de la carcasa a ras del borde del fondo
    carcasa = placa_xz(comp, -ancho, 2 * ancho, [q(s_a, 0), q(s_b, 0), q(s_b, prof), q(s_a, prof)],
                       'carcasa_backlight')
    hueco = placa_xz(comp, -ancho + T, 2 * (ancho - T),
                     [q(s_a + T, 0), q(s_b - T, 0), q(s_b - T, prof - T), q(s_a + T, prof - T)], 'carcasa_hueco')
    combinar(comp, carcasa, [hueco], CORTE)
    sv0, sv1 = S_ESCANEO - LARGO_VENTANA / 2.0, S_ESCANEO + LARGO_VENTANA / 2.0
    placa_xz(comp, -w2 + 10, 2 * (w2 - 10), [q(sv0, prof - T - 15), q(sv1, prof - T - 15),
                                           q(sv1, prof - T), q(sv0, prof - T)], 'PROPUESTA_backlight_IR')

    # Camara lineal (bajo la tapa del sensor), perpendicular a la lamina de agua sobre la linea de escaneo
    base = (XE + S_ESCANEO * c2, 0.0, ZE + S_ESCANEO * s2)  # punto de la linea de escaneo en el fondo
    eje = (-s2, 0.0, c2)                                   # normal al fondo, hacia arriba
    a_lo_largo = (c2, 0.0, s2)
    punto = lambda dist: (base[0] + eje[0] * dist, 0.0, base[2] + eje[2] * dist)
    tubo_oblicuo(comp, punto(ALTO_TOBOGAN + 10), eje, a_lo_largo, 30, 18, 0, 'PROPUESTA_lente')
    tubo_oblicuo(comp, punto(ALTO_TOBOGAN + 40), eje, a_lo_largo, 45, 30, 0, 'PROPUESTA_camara_lineal')

    # Embudo: transicion de rectangulo a circulo (loft). Entra con la misma seccion del tobogan
    # (plano vertical X = XE) y sale en un circulo del diametro del tubo, perpendicular al eje.
    al = g['alfa']
    ca, sa = math.cos(al), math.sin(al)
    H = g['H_EMB']
    r = D_SALIDA / 2.0
    d = (-ca, 0.0, -sa)                                   # eje de salida
    n = (-sa, 0.0, ca)                                    # "arriba" del plano de la boca
    c = (XE - LARGO_EMBUDO * ca, 0.0, ZE + H / 2.0 - LARGO_EMBUDO * sa)   # centro de la boca circular
    tr = lambda p, v, k: (p[0] + v[0] * k, p[1] + v[1] * k, p[2] + v[2] * k)
    pl_entrada = plano(comp, 'YZ', XE)
    pl_boca = plano_3p(comp, c, tr(c, (0, 1, 0), 100), tr(c, n, 100))
    zs = te[4][1]                                         # cara superior de la tapa en X = XE
    exterior = [(XE, -wo, ZE - T), (XE, wo, ZE - T), (XE, wo, zs), (XE, -wo, zs)]
    interior = [(XE, -w2, ZE), (XE, w2, ZE), (XE, w2, ZE + H), (XE, -w2, ZE + H)]
    cuerpo = loft(comp, [seccion_loft(comp, pl_entrada, 'embudo_entrada_ext', rect=exterior),
                         seccion_loft(comp, pl_boca, 'embudo_boca_ext', centro=c, r=r)], 'embudo')
    hueco = loft(comp, [seccion_loft(comp, pl_entrada, 'embudo_entrada_int', rect=interior),
                        seccion_loft(comp, pl_boca, 'embudo_boca_int', centro=c, r=r - T)], 'embudo_hueco')
    combinar(comp, cuerpo, [hueco], CORTE)

    # Tubo de salida: arranca exactamente en la boca circular del embudo (mismo diametro) y se une
    tubo = tubo_oblicuo(comp, c, d, n, LARGO_TUBO, r, r - T, 'tubo_salida_D165')
    combinar(comp, cuerpo, [tubo], UNION)
    # Acople: a tope con el final del tubo, mismo diametro interior (paso continuo)
    tubo_oblicuo(comp, tr(c, d, LARGO_TUBO), d, n, LARGO_ACOPLE, D_ACOPLE / 2.0, r - T, 'acople_salida')

    # Articulacion: el embudo pivota para regular la altura de salida.
    # El eje va bajo el final del tobogan (aguas arriba de XE): queda libre para cualquier inclinacion.
    xp, zp = XE + 20, ZE - 25
    for s, lado in ((-1, 'izq'), (1, 'der')):
        y0 = wo + 1 if s > 0 else -(wo + 7)
        sk = boceto(comp, plano(comp, 'XZ', y0), 'soporte_pivote_' + lado)
        poligono(sk, [(xp - 60, y0, ZE - 65), (xp + 60, y0, ZE - 65), (xp, y0, ZE + 15)])
        circulo(sk, (xp, y0, zp), 15)
        extruir(comp, sk, perfil(sk, anillo=True), 6, (0, 1, 0), 'soporte_pivote_' + lado)
    cilindro(comp, 'Y', xp, zp, -(wo + 7), 2 * (wo + 7), 15, 0, 'eje_pivote')


# =====================================================================
# COMPONENTE_TAPA_SENSOR (estilo Sincere: caja baja achaflanada sobre la estacion de conteo)
# =====================================================================
def achaflanado(a0, a1, b_bajo, b_alto, ch, d):
    """Contorno (a, b) de un rectangulo con las dos esquinas superiores achaflanadas a 45 grados,
    desplazado d hacia adentro (el borde inferior queda en b_bajo)."""
    k = d * (math.sqrt(2) - 1)
    return [(a0 + d, b_bajo), (a1 - d, b_bajo), (a1 - d, b_alto - ch - k), (a1 - ch - k, b_alto - d),
            (a0 + ch + k, b_alto - d), (a0 + d, b_alto - ch - k)]


def construir_tapa_sensor(comp, g):
    c2, s2 = math.cos(g['t2']), math.sin(g['t2'])
    u0, u1 = g['U_TAPA']
    wl = ANCHO_TOBOGAN / 2.0
    vb = ALTO_TOBOGAN + T + HOLGURA_TAPA                  # apoya sobre la tapa del tobogan
    vt = vb + ALTO_TAPA_SENSOR
    ch = CHAFLAN_TAPA
    normal, a_lo_largo = (-s2, 0.0, c2), (c2, 0.0, s2)
    xz = lambda uv: (punto_rampa(g, uv[0], uv[1])[0], punto_rampa(g, uv[0], uv[1])[2])

    def prisma_lateral(d, b_bajo, nombre):
        """Perfil a lo largo de la pendiente (plano XZ), extruido en Y."""
        return placa_xz(comp, -(wl + 50), 2 * (wl + 50),
                        [xz(p) for p in achaflanado(u0, u1, b_bajo, vt, ch, d)], nombre)

    def prisma_seccion(d, b_bajo, nombre):
        """Seccion transversal (perpendicular a la pendiente), extruida a lo largo de la pendiente."""
        a = punto_rampa(g, u0 - 10, vb)
        pl = plano_3p(comp, a, punto_rampa(g, u0 - 10, vb, 100), punto_rampa(g, u0 - 10, vb + 100))
        sk = boceto(comp, pl, nombre)
        poligono(sk, [punto_rampa(g, u0 - 10, v, y) for y, v in achaflanado(-wl, wl, b_bajo, vt, ch, d)])
        return extruir(comp, sk, perfil(sk), u1 - u0 + 20, a_lo_largo, nombre)

    # Caja hueca abierta por abajo: (lateral ∩ seccion) exterior menos (lateral ∩ seccion) interior
    tapa = prisma_lateral(0, vb, 'tapa_sensor')
    combinar(comp, tapa, [prisma_seccion(0, vb - 5, 'tapa_sensor_seccion')], INTERSECCION)
    hueco = prisma_lateral(T, vb - 20, 'tapa_sensor_hueco')
    combinar(comp, hueco, [prisma_seccion(T, vb - 20, 'tapa_sensor_hueco_seccion')], INTERSECCION)
    combinar(comp, tapa, [hueco], CORTE)

    # Display LED del contador sobre la cara superior
    esquinas = [punto_rampa(g, S_ESCANEO - 70, vt, -25), punto_rampa(g, S_ESCANEO + 70, vt, -25),
                punto_rampa(g, S_ESCANEO + 70, vt, 25), punto_rampa(g, S_ESCANEO - 70, vt, 25)]
    placa_oblicua(comp, esquinas, 8, normal, 'display_contador')

    # Agarraderas: una cerca de cada extremo (postes perpendiculares a la cara superior + barra en Y)
    alto = 40
    for i, u_h in enumerate((u0 + ch + 45, u1 - ch - 45)):
        postes = [tubo_oblicuo(comp, punto_rampa(g, u_h, vt, s * 80), normal, a_lo_largo, alto, 7, 0,
                               'agarradera_poste_%d_%s' % (i + 1, lado))
                  for s, lado in ((-1, 'izq'), (1, 'der'))]
        x_b, _, z_b = punto_rampa(g, u_h, vt + alto)
        barra = cilindro(comp, 'Y', x_b, z_b, -100, 200, 9, 0, 'agarradera_tapa_%d' % (i + 1))
        combinar(comp, barra, postes, UNION)


# =====================================================================
# COMPONENTE_INSTALACION_PROPUESTA (de piscina a piscina: bomba con variador, sin estrangulamiento)
# =====================================================================
def construir_instalacion(comp, g):
    ZC, XE, ZE = g['ZC'], g['XE'], g['ZE']
    px0, px1, py0, py1, p_alto = PISCINA
    e = ESP_PISCINA

    # Piscina / canal de cosecha (referencia) y bomba
    sk = boceto(comp, plano(comp, 'XY', 0), 'PROPUESTA_piscina')
    poligono(sk, [(px0, py0, 0), (px1, py0, 0), (px1, py1, 0), (px0, py1, 0)])
    poligono(sk, [(px0 + e, py0 + e, 0), (px1 - e, py0 + e, 0), (px1 - e, py1 - e, 0), (px0 + e, py1 - e, 0)])
    extruir(comp, sk, perfil(sk, anillo=True), p_alto, (0, 0, 1), 'PROPUESTA_piscina_paredes')
    caja(comp, px0 + e, px1 - e, py0 + e, py1 - e, 0, e, 'PROPUESTA_piscina_fondo')
    bx0, bx1, by0, by1, b_alto = BOMBA
    caja(comp, bx0, bx1, by0, by1, 0, b_alto, 'PROPUESTA_bomba')
    vx0, vx1, vy0, vy1, v_alto = VARIADOR
    caja(comp, vx0, vx1, vy0, vy1, 0, v_alto, 'PROPUESTA_variador_frecuencia')

    # Succion: de la piscina a la bomba, por encima del borde, con canasta en el extremo
    r_man = D_MANGUERA / 2.0
    xs, ys = XY_SUCCION
    cilindro(comp, 'Z', xs, Y_PISCINA, 60, 60, r_man + 35, 0, 'PROPUESTA_canasta_succion')
    tuberia(comp, [(xs, Y_PISCINA, 120), (xs, Y_PISCINA, p_alto + 100), (xs, ys, p_alto + 100),
                   (xs, ys, b_alto)], r_man, r_man - T, D_MANGUERA, 'PROPUESTA_manguera_succion')

    # Impulsion: de la bomba al difusor de entrada, Ø110 en toda la linea (1.2 m/s a 10 L/s). El tramo horizontal
    # pasa por debajo de las riostras del bastidor y baja lo necesario para que la subida hasta el difusor
    # (al menos 140 mm) quepa con las patas al minimo.
    z_red = ZC - T - LARGO_DIFUSOR                      # extremo inferior del difusor
    z_imp = min(Z_IMPULSION, z_red - 140)
    tuberia(comp, [(X_IMPULSION, Y_IMPULSION, b_alto), (X_IMPULSION, Y_IMPULSION, z_imp),
                   (X_ENTRADA, Y_IMPULSION, z_imp), (X_ENTRADA, 0, z_imp),
                   (X_ENTRADA, 0, z_red)], r_man, r_man - T, D_MANGUERA, 'PROPUESTA_tuberia_impulsion')

    # Valvula de mariposa solo de corte (abierta del todo en operacion: no se estrangula la larva), en el tramo
    # horizontal. El caudal se fija con el variador, leyendo la carga H en la regla del cajon.
    y_val = -350
    cilindro(comp, 'Y', X_ENTRADA, z_imp, y_val, 60, r_man + 25, r_man, 'PROPUESTA_valvula_corte')
    caja(comp, X_ENTRADA - 10, X_ENTRADA + 10, y_val + 20, y_val + 40, z_imp + r_man + 25, z_imp + r_man + 145,
         'PROPUESTA_manija_valvula_corte')

    # Purga del sumidero: de la valvula al suelo (agua de drenaje, no vuelve a la piscina)
    z_purga = ZC - PROF_SUMIDERO - 215 - T
    tuberia(comp, [(X_DRENAJE, 0, z_purga), (X_DRENAJE, 0, 120), (1400, 0, 120)],
            r_man, r_man - T, D_MANGUERA, 'PROPUESTA_manguera_purga')

    # Salida del producto: manguera acoplada a la boca, descargando sobre la piscina de destino.
    # Se acorta lo necesario para acabar 100 mm sobre el borde de esa piscina.
    al = g['alfa']
    ca, sa = math.cos(al), math.sin(al)
    d, n = (-ca, 0.0, -sa), (-sa, 0.0, ca)
    r = D_SALIDA / 2.0
    c = (XE - LARGO_EMBUDO * ca, 0.0, ZE + g['H_EMB'] / 2.0 - LARGO_EMBUDO * sa)
    boca = avanza(c, d, LARGO_TUBO + LARGO_ACOPLE)
    largo = min(LARGO_MANGUERA_SALIDA, (boca[2] - ALTO_DESTINO - 100) / max(sa, 0.05))
    tubo_oblicuo(comp, boca, d, n, largo, r - T, r - 2 * T, 'PROPUESTA_manguera_salida')

    # Piscina de destino, bajo la descarga
    dx1 = avanza(boca, d, largo)[0] + 150
    dx0, dy = dx1 - 1550, 800
    sk = boceto(comp, plano(comp, 'XY', 0), 'PROPUESTA_piscina_destino')
    poligono(sk, [(dx0, -dy, 0), (dx1, -dy, 0), (dx1, dy, 0), (dx0, dy, 0)])
    poligono(sk, [(dx0 + e, -dy + e, 0), (dx1 - e, -dy + e, 0), (dx1 - e, dy - e, 0), (dx0 + e, dy - e, 0)])
    extruir(comp, sk, perfil(sk, anillo=True), ALTO_DESTINO, (0, 0, 1), 'PROPUESTA_piscina_destino_paredes')
    caja(comp, dx0 + e, dx1 - e, -dy + e, dy - e, 0, e, 'PROPUESTA_piscina_destino_fondo')


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================
def run(context):
    global app, ui
    progreso = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        _planos.clear()
        _bocetos_puntos.clear()
        for lista in _por_material.values():
            del lista[:]

        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent

        g = geometria()
        progreso = ui.createProgressDialog()
        constructores = (('Componente_Soporte', construir_soporte),
                         ('Componente_Canal_Superior', construir_canal_superior),
                         ('Componente_Rampa_Inclinada', construir_rampa),
                         ('Componente_Tapa_Sensor', construir_tapa_sensor),
                         ('Componente_Instalacion_PROPUESTA', construir_instalacion))
        progreso.show('Contador de camaron', 'Construyendo %v de %m componentes...', 0, len(constructores))

        componentes = []
        for i, (nombre, constructor) in enumerate(constructores):
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = nombre
            constructor(comp, g)
            componentes.append(comp)
            progreso.progressValue = i + 1
            adsk.doEvents()

        for sk in _bocetos_puntos.values():
            sk.isVisible = False
        try:
            materiales = asignar_materiales(app, design)
        except Exception as e:
            materiales = ['no se pudieron asignar (%s); asignar vidrio/acrilico a mano' % e]
        progreso.hide()
        progreso = None
        app.activeViewport.fit()

        cuerpos = sum(c.bRepBodies.count for c in componentes)
        alto_total = max(g['ZC'] + ALTO_CAJON,
                         punto_rampa(g, g['U_TAPA'][1] - CHAFLAN_TAPA, ALTO_TOBOGAN + T + HOLGURA_TAPA +
                                     ALTO_TAPA_SENSOR + 50)[2])
        avisos = []
        if not (RAMPA_MIN <= ALTO_SALIDA <= RAMPA_MAX):
            avisos.append('ALTO_SALIDA esta fuera del rango RAMPA_MIN..RAMPA_MAX.')
        if g['alfa_limitado']:
            avisos.append('La inclinacion del embudo se limito a 5-60 grados; '
                          'la salida real es %.0f mm.' % g['Z_SALIDA'])
        ui.messageBox(
            'Modelo generado: %d cuerpos en %d componentes.\n\n'
            'Nivel del cuerpo: %.0f mm (rango %d-%d)\n'
            'Tobogan: pendiente final %.0f grados; linea de escaneo a %d mm del final\n'
            'Altura total: %.0f mm (referencia Vaki: %d-%d)\n'
            'Salida: %.0f mm (rango %d-%d) - embudo a %.1f grados\n\n'
            'HIDRAULICA con %.1f L/s (%.0f m3/h):\n'
            '- carga sobre el vertedero H = %.0f mm; nivel en el cajon = %.0f mm\n'
            '- borde libre hasta el canto del cajon = %.0f mm\n'
            '- entrada por el fondo sin plato: %.2f m/s en la boca D%d (%.2f m/s en la manguera D%d)\n'
            '- lamina en el conteo = %.1f mm a %.2f m/s, Froude %.1f (perfil 1D del agua, SIN el drenaje de la\n'
            '  malla, que la adelgaza; ver simulacion_flujo/INFORME_FLUJO.md)\n'
            '- linea de camara %.1f kHz con pixel de %.2f mm en el sentido del flujo (%d pixeles en el ancho)\n\n'
            'Materiales:\n- %s%s'
            % (cuerpos, len(componentes), g['ZC'], ALTO_SOPORTE_MIN, ALTO_SOPORTE_MAX,
               ANGULO_FINAL, S_ESCANEO, alto_total, ALTO_MIN, ALTO_MAX,
               g['Z_SALIDA'], RAMPA_MIN, RAMPA_MAX, math.degrees(g['alfa']),
               CAUDAL_DISENO, CAUDAL_DISENO * 3.6, g['H_VERT'], g['NIVEL'],
               g['MARGEN_CAJON'], g['V_BOCA'], D_ENTRADA, g['V_MANGUERA'], D_MANGUERA,
               g['LAMINA'], g['V_CONTEO'], g['FR_CONTEO'],
               g['V_CONTEO'] / (ANCHO_CANAL / 2048.0), ANCHO_CANAL / 2048.0, 2048,   # kHz: (m/s x 1000 mm) / (mm por pixel) / 1000
               '\n- '.join(materiales),
               ('\n\nAVISOS:\n- ' + '\n- '.join(avisos)) if avisos else ''))
    except Exception:
        if progreso:
            progreso.hide()
        if ui:
            ui.messageBox('Error al generar el modelo:\n\n%s' % traceback.format_exc())


def stop(context):
    pass
