# -*- coding: utf-8 -*-
"""
Modelo 3D a ESCALA REAL del contador VAKI Macro 1 Channel.
Reconstruido desde el plano de conjunto C0111-000000 (escala 1:20, 2013).

Salida:  vaki_macro_escala_real.step   -> Fusion 360: Archivo > Abrir > "Abrir desde mi PC"
Unidades: milímetros.

Ejes (los mismos que se usaron para medir el plano):
    X = largo. 0 en la punta de la boca de salida, crece hacia el cajón de entrada.
    Y = ancho. 0 en el eje de la máquina.
    Z = alto.  0 en el suelo.

Las cotas marcadas [PLANO] están acotadas en el dibujo.
Las marcadas [MEDIDO] se midieron sobre el plano a escala 1:20 (±10-20 mm).
Las marcadas [SUPUESTO] NO aparecen en el plano (es un plano de conjunto, solo
muestra el exterior) y hay que validarlas en la Fase 0.
"""
import math
import os
import cadquery as cq

V = cq.Vector

# =====================================================================
# PARÁMETROS
# =====================================================================
DZ = 0      # ajuste de patas telescópicas: -327 = mínimo, 0 = como está dibujado, +273 = máximo
T = 3       # espesor de chapa inox 316 [SUPUESTO]

ZC = 1310 + DZ      # cara inferior del cuerpo [PLANO: 983-1583, dibujado a 1310]

# --- Cajón de entrada -------------------------------------------------
CAJ_X0 = 2055       # arranque del cajón alto [MEDIDO]
CAJ_XCH = 2601      # inicio del chaflán en planta [MEDIDO]
CAJ_XF = 2837       # frente trasero [PLANO: largo total 2837]
CUERPO_W = 1000     # ancho exterior del cuerpo [MEDIDO]
W_INT = CUERPO_W - 2 * T
CAJ_FRENTE_W = 546  # ancho del frente chaflanado [MEDIDO]
CAJ_H = 300         # alto de paredes del cajón [MEDIDO]
ENT_X, ENT_D = 2632, 160            # boca de entrada por el fondo [MEDIDO]

# --- Interior del cajón [SUPUESTO: el plano no muestra el interior] ---
DEFL1_X, DEFL1_PASO = 2502, 70      # deflector de paso inferior
DEFL2_X = 2311                      # placa perforada (enderezador)
VERT_X, VERT_H = 2088, 60           # vertedero bajo + rampa (sin caída libre)

# --- Drenaje ----------------------------------------------------------
REJ_X0, REJ_X1 = 1905, 2025         # rejilla de drenaje en el fondo
SUM_X0, SUM_X1 = 1905, 2106         # sumidero [MEDIDO]
SUM_W = 600                         # [SUPUESTO]

# --- Contracción y canal del sensor -----------------------------------
CON_X0, CON_X1 = 1780, 1905
W_SENSOR = 440      # ancho del canal bajo el sensor [SUPUESTO, inferido del capó]

# --- Alojamiento del sensor [MEDIDO] ----------------------------------
SEN_X0, SEN_X1, SEN_W, SEN_Z1 = 1339, 1780, 510, 1769

# --- Tobogán curvo: (X, Z del fondo, ancho interior, alto de pared) ---
# Fondo MEDIDO sobre el plano; anchos SUPUESTOS siguiendo el contorno del capó.
TOBOGAN = [
    (1780, 1310, W_SENSOR, 100),
    (1600, 1300, W_SENSOR, 100),
    (1405, 1284, W_SENSOR, 100),
    (1339, 1268, 450, 110),
    (1207, 1207, 560, 130),
    (1075, 1130, 700, 130),
    (987, 1053, 820, 130),
    (900, 975, 930, 130),
    (820, 895, 1000, 130),
]

# --- Embudo de salida (X, Z del fondo, ancho, alto de pared) [MEDIDO] --
EMBUDO = [
    (860, 775, 1000, 140),
    (612, 692, 1000, 140),
    (214, 560, 150, 110),
]
SALIDA_D = 165      # tubo de salida [MEDIDO]

# --- Bastidor -------------------------------------------------------
PERFIL = 40                 # tubo cuadrado 40x40x2 [SUPUESTO, ~ancho medido]
Y_BAS = 540                 # línea de patas y largueros [MEDIDO]
X_RUEDA, X_PATA = 1152, 2546            # [MEDIDO]
RUEDA_D, RUEDA_W, Z_EJE = 264, 80, 132  # [MEDIDO]
Z_LARG = ZC - 44            # cara inferior del larguero superior


# =====================================================================
# UTILIDADES GEOMÉTRICAS
# =====================================================================
def caja(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)).val())


def poligono(puntos):
    return cq.Wire.makePolygon([V(*p) for p in puntos], close=True)


def extruir(puntos, vector):
    return cq.Solid.extrudeLinear(poligono(puntos), [], V(*vector))


def placa_xz(pts_xz, y0, esp):
    """Placa con contorno en el plano XZ, extruida en Y."""
    return extruir([(x, y0, z) for x, z in pts_xz], (0, esp, 0))


def base_perp(v):
    a = V(0, 0, 1) if abs(v.z) < 0.9 else V(1, 0, 0)
    u = v.cross(a).normalized()
    return u, v.cross(u).normalized()


def barra(p1, p2, a=PERFIL, e=2):
    """Tubo cuadrado hueco entre dos puntos."""
    p1, p2 = V(*p1), V(*p2)
    v = p2 - p1
    u, w = base_perp(v.normalized())

    def seccion(s):
        h = s / 2
        return cq.Wire.makePolygon([p1 + u * h + w * h, p1 - u * h + w * h,
                                    p1 - u * h - w * h, p1 + u * h - w * h], close=True)
    exterior = cq.Solid.extrudeLinear(seccion(a), [], v)
    return exterior.cut(cq.Solid.extrudeLinear(seccion(a - 2 * e), [], v))


def cilindro(p1, p2, d, hueco=0.0):
    p1, p2 = V(*p1), V(*p2)
    v = p2 - p1
    s = cq.Solid.makeCylinder(d / 2, v.Length, p1, v.normalized())
    if hueco:
        s = s.cut(cq.Solid.makeCylinder(d / 2 - hueco, v.Length, p1, v.normalized()))
    return s


def perfil_u(x, zf, w, h, t=T):
    """Sección en U (canal abierto) en el plano X = x."""
    a = w / 2
    pts = [(-a - t, zf + h), (-a - t, zf - t), (a + t, zf - t), (a + t, zf + h),
           (a, zf + h), (a, zf), (-a, zf), (-a, zf + h)]
    return cq.Wire.makePolygon([V(x, y, z) for y, z in pts], close=True)


def canal_u(estaciones, ruled=False):
    secciones = [perfil_u(x, z + DZ, w, h) for x, z, w, h in estaciones]
    return cq.Solid.makeLoft(secciones, ruled)


def loft_cuad(q1, q2):
    return cq.Solid.makeLoft([poligono(q1), poligono(q2)], True)


def z_fondo_tobogan(x):
    """Interpolación lineal del fondo del tobogán (para ubicar piezas)."""
    pts = sorted((p[0], p[1] + DZ) for p in TOBOGAN)
    for (xa, za), (xb, zb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return za + (zb - za) * (x - xa) / (xb - xa)
    raise ValueError(x)


# =====================================================================
# COLORES
# =====================================================================
INOX = cq.Color(0.80, 0.82, 0.85)
BASTIDOR = cq.Color(0.55, 0.57, 0.60)
NEGRO = cq.Color(0.10, 0.10, 0.12)
ACRILICO = cq.Color(0.60, 0.85, 0.95, 0.35)
VIDRIO = cq.Color(0.75, 0.90, 1.00, 0.30)
CAPO = cq.Color(0.86, 0.88, 0.90, 0.55)
NARANJA = cq.Color(0.95, 0.55, 0.10)
ROJO = cq.Color(0.80, 0.15, 0.12)
AZUL = cq.Color(0.30, 0.50, 0.80)
VERDE = cq.Color(0.20, 0.55, 0.28)


# =====================================================================
# 1 · BASTIDOR
# =====================================================================
def bastidor():
    a = cq.Assembly(name="Bastidor")
    for i, s in enumerate((-1, 1)):
        y = s * Y_BAS
        lado = "izq" if s < 0 else "der"
        # patas delanteras (con rueda) y traseras (telescópicas)
        a.add(barra((X_RUEDA, y, Z_EJE), (X_RUEDA, y, Z_LARG + PERFIL)),
              name=f"pata_delantera_{lado}", color=BASTIDOR)
        a.add(barra((X_PATA, y, 700 + DZ), (X_PATA, y, Z_LARG + PERFIL), a=50, e=3),
              name=f"pata_trasera_exterior_{lado}", color=BASTIDOR)
        a.add(barra((X_PATA, y, 25), (X_PATA, y, 1000 + DZ), a=42, e=2),
              name=f"pata_trasera_telescopica_{lado}", color=INOX)
        a.add(caja(X_PATA - 60, X_PATA + 60, y - 60, y + 60, 15, 25),
              name=f"pie_{lado}", color=NEGRO)
        a.add(cilindro((X_PATA, y - 35, 1150 + DZ), (X_PATA, y + 35, 1150 + DZ), 12),
              name=f"pasador_altura_{lado}", color=ROJO)
        # largueros
        a.add(barra((1015, y, Z_LARG + PERFIL / 2), (2601, y, Z_LARG + PERFIL / 2)),
              name=f"larguero_superior_{lado}", color=BASTIDOR)
        a.add(barra((X_RUEDA + 20, y, 467), (X_PATA - 25, y, 467)),
              name=f"riostra_horizontal_{lado}", color=BASTIDOR)
        a.add(barra((X_RUEDA + 20, y, 1075 + DZ), (X_PATA - 25, y, 513)),
              name=f"riostra_diagonal_{lado}", color=BASTIDOR)
        # rueda
        yr = s * (Y_BAS + 61)       # ancho total con ruedas = 1283 [PLANO]
        a.add(cilindro((X_RUEDA, yr - RUEDA_W / 2, Z_EJE), (X_RUEDA, yr + RUEDA_W / 2, Z_EJE),
                       RUEDA_D).cut(cilindro((X_RUEDA, yr - 50, Z_EJE),
                                             (X_RUEDA, yr + 50, Z_EJE), 150)),
              name=f"rueda_{lado}", color=NEGRO)
        a.add(cilindro((X_RUEDA, yr - RUEDA_W / 2 + 5, Z_EJE),
                       (X_RUEDA, yr + RUEDA_W / 2 - 5, Z_EJE), 150),
              name=f"llanta_{lado}", color=ROJO)
        a.add(cilindro((X_RUEDA, y, Z_EJE), (X_RUEDA, yr + s * 40, Z_EJE), 20),
              name=f"eje_{lado}", color=BASTIDOR)
        # soporte del tobogán (poste)
        z_sop = z_fondo_tobogan(1250) - T - 45
        a.add(barra((1250, y, z_sop), (1250, y, Z_LARG)),
              name=f"poste_soporte_tobogan_{lado}", color=BASTIDOR)
    # travesaños
    a.add(barra((X_RUEDA, -Y_BAS + 20, 450), (X_RUEDA, Y_BAS - 20, 450)),
          name="travesano_delantero", color=BASTIDOR)
    a.add(barra((X_PATA, -Y_BAS + 25, 420), (X_PATA, Y_BAS - 25, 420)),
          name="travesano_trasero_inferior", color=BASTIDOR)
    a.add(barra((X_PATA, -Y_BAS + 20, Z_LARG + PERFIL / 2), (X_PATA, Y_BAS - 20, Z_LARG + PERFIL / 2)),
          name="travesano_trasero_superior", color=BASTIDOR)
    z_sop = z_fondo_tobogan(1250) - T - 25
    a.add(barra((1250, -Y_BAS + 20, z_sop), (1250, Y_BAS - 20, z_sop)),
          name="travesano_bajo_tobogan", color=BASTIDOR)
    return a


# =====================================================================
# 2 · CAJÓN DE ENTRADA
# =====================================================================
def cajon_entrada():
    a = cq.Assembly(name="Cajon_entrada")
    h = CUERPO_W / 2
    f = CAJ_FRENTE_W / 2
    # contorno en planta (exterior) del cuerpo desde la brida hasta el frente
    planta = [(1802, -h), (CAJ_XCH, -h), (CAJ_XF, -f), (CAJ_XF, f), (CAJ_XCH, h), (1802, h)]

    # fondo del cajón (desde el vertedero hasta el frente) con la boca de entrada
    fondo = extruir([(VERT_X - T, -h), (CAJ_XCH, -h), (CAJ_XF, -f), (CAJ_XF, f),
                     (CAJ_XCH, h), (VERT_X - T, h)], (0, 0, T))
    fondo = fondo.translate(V(0, 0, ZC - T)).cut(
        cilindro((ENT_X, 0, ZC - 10), (ENT_X, 0, ZC + 10), ENT_D))
    a.add(fondo, name="fondo_cajon", color=INOX)

    # paredes laterales: perfil con la cubierta inclinada (tramo 1802-2055)
    perfil_lat = [(1802, ZC), (CAJ_XCH, ZC), (CAJ_XCH, ZC + CAJ_H), (CAJ_X0, ZC + CAJ_H),
                  (1861, ZC + 100), (1802, ZC + 100)]
    a.add(placa_xz(perfil_lat, -h, T), name="pared_lateral_izq", color=INOX)
    a.add(placa_xz(perfil_lat, h - T, T), name="pared_lateral_der", color=INOX)

    # paredes chaflanadas y frente
    def pared(p, q, nombre):
        (x1, y1), (x2, y2) = p, q
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * T, dx / L * T
        base = [(x1, y1, ZC), (x2, y2, ZC), (x2 + nx, y2 + ny, ZC), (x1 + nx, y1 + ny, ZC)]
        a.add(extruir(base, (0, 0, CAJ_H)), name=nombre, color=INOX)
    pared((CAJ_XCH, -h), (CAJ_XF, -f), "chaflan_izq")
    pared((CAJ_XF, -f), (CAJ_XF, f), "frente_trasero")
    pared((CAJ_XF, f), (CAJ_XCH, h), "chaflan_der")

    # cubierta del tramo bajo (brida -> cajón alto)
    cubierta = [(1802, ZC + 100 - T), (1861, ZC + 100 - T), (CAJ_X0, ZC + CAJ_H - T),
                (CAJ_X0, ZC + CAJ_H), (1861, ZC + 100), (1802, ZC + 100)]
    a.add(placa_xz(cubierta, -h, CUERPO_W), name="cubierta_tramo_bajo", color=INOX)

    # boca de entrada por el fondo + brida  (conexión de la bomba)
    a.add(cilindro((ENT_X, 0, ZC - 105), (ENT_X, 0, ZC), ENT_D, hueco=T),
          name="boca_entrada_D160", color=AZUL)
    a.add(cilindro((ENT_X, 0, ZC - 115), (ENT_X, 0, ZC - 105), 240, hueco=40),
          name="brida_entrada", color=INOX)

    # deflector de paso inferior [SUPUESTO]
    a.add(caja(DEFL1_X, DEFL1_X + T, -h + T, h - T, ZC + DEFL1_PASO, ZC + CAJ_H - 20),
          name="deflector_paso_inferior", color=INOX)
    # placa perforada enderezadora [SUPUESTO]
    perf = (cq.Workplane("YZ", origin=(DEFL2_X, 0, ZC + 120))
            .rect(W_INT, 240).extrude(T)
            .faces(">X").workplane()
            .rarray(60, 50, 15, 4).hole(30))
    a.add(perf.val(), name="placa_perforada_enderezadora", color=INOX)
    # vertedero bajo + labio + rampa sin caída libre [SUPUESTO]
    a.add(caja(VERT_X, VERT_X + T, -h + T, h - T, ZC, ZC + VERT_H),
          name="vertedero", color=INOX)
    a.add(caja(VERT_X - 8, VERT_X + T + 8, -h + T, h - T, ZC + VERT_H - 5, ZC + VERT_H),
          name="labio_vertedero", color=ROJO)
    rampa = [(VERT_X, ZC), (VERT_X, ZC + VERT_H), (VERT_X - 60, ZC)]
    a.add(placa_xz(rampa, -h + T, W_INT), name="rampa_vertedero", color=INOX)
    return a


# =====================================================================
# 3 · DRENAJE (rejilla + sumidero + válvula)
# =====================================================================
def drenaje():
    a = cq.Assembly(name="Drenaje")
    # rejilla de barras longitudinales (el animal resbala a lo largo)
    barras = None
    n = int(W_INT // 15)
    for i in range(n):
        y = -W_INT / 2 + 7.5 + i * 15
        b = caja(REJ_X0, REJ_X1, y - 2, y + 2, ZC - 10, ZC)
        barras = b if barras is None else barras.fuse(b)
    a.add(barras, name="rejilla_drenaje_barras", color=INOX)
    a.add(caja(REJ_X0 - 10, REJ_X0, -W_INT / 2, W_INT / 2, ZC - 10, ZC),
          name="marco_rejilla_a", color=INOX)
    # fondo ciego entre la rampa y la rejilla
    a.add(caja(REJ_X1, VERT_X - 60 + 1, -W_INT / 2, W_INT / 2, ZC - T, ZC),
          name="fondo_ciego_rejilla", color=INOX)
    # sumidero [MEDIDO en posición y alto]
    sum1 = (cq.Workplane("XY").box(SUM_X1 - SUM_X0, SUM_W, 105, centered=False)
            .translate((SUM_X0, -SUM_W / 2, ZC - 115)).faces(">Z").shell(-T).val())
    a.add(sum1, name="sumidero", color=INOX)
    a.add(cilindro((2009, 0, ZC - 330), (2009, 0, ZC - 115), 110, hueco=T),
          name="tubo_drenaje_agua", color=AZUL)
    a.add(cilindro((2009, 0, ZC - 250), (2009, 0, ZC - 205), 150),
          name="valvula_drenaje", color=ROJO)
    a.add(cilindro((2009, -160, ZC - 227), (2009, 0, ZC - 227), 18),
          name="manija_valvula", color=ROJO)
    return a


# =====================================================================
# 4 · CONTRACCIÓN + CANAL DEL SENSOR + TOBOGÁN CURVO
# =====================================================================
def canal():
    a = cq.Assembly(name="Canal_y_tobogan")
    contr = canal_u([(CON_X1, ZC - DZ, W_INT, 100), (CON_X0, ZC - DZ, W_SENSOR, 100)], ruled=True)
    a.add(contr, name="contraccion", color=INOX)

    tob = canal_u(TOBOGAN)
    # ventana óptica en el fondo, bajo el sensor
    tob = tob.cut(caja(1470, 1690, -180, 180, ZC - 60, ZC + 20))
    a.add(tob, name="tobogan_curvo", color=INOX)

    z1, z2 = z_fondo_tobogan(1470), z_fondo_tobogan(1690)
    ventana = loft_cuad([(1470, -185, z1 - 8), (1470, 185, z1 - 8), (1470, 185, z1), (1470, -185, z1)],
                        [(1690, -185, z2 - 8), (1690, 185, z2 - 8), (1690, 185, z2), (1690, -185, z2)])
    a.add(ventana, name="ventana_acrilico_fondo", color=ACRILICO)
    # brida de unión (el tobogán se desmonta aquí)
    a.add(caja(1799, 1805, -CUERPO_W / 2 - 20, CUERPO_W / 2 + 20, ZC - 30, ZC + 130),
          name="brida_union", color=INOX)
    return a


# =====================================================================
# 5 · SENSOR (alojamiento Vaki + propuesta óptica del proyecto)
# =====================================================================
def sensor():
    a = cq.Assembly(name="Sensor")
    z0 = ZC + 100
    z1 = SEN_Z1 + DZ
    caja_sen = (cq.Workplane("XY").box(SEN_X1 - SEN_X0, SEN_W, z1 - z0, centered=False)
                .translate((SEN_X0, -SEN_W / 2, z0)).faces("<Z").shell(-T).val())
    a.add(caja_sen, name="alojamiento_sensor", color=INOX)
    a.add(caja(SEN_X0 + T, SEN_X1 - T, -SEN_W / 2 + T, SEN_W / 2 - T, z0, z0 + 6),
          name="vidrio_protector", color=VIDRIO)
    # asas de la tapa [MEDIDO]
    for x in (1360, 1760):
        a.add(barra((x, 0, z1), (x, 0, z1 + 40), a=20), name=f"asa_poste_{x}", color=INOX)
    a.add(barra((1350, 0, z1 + 40), (1770, 0, z1 + 40), a=20), name="asa_tapa", color=INOX)
    # ---- propuesta del proyecto (NO es parte del Vaki: el Vaki usa escáner IR) ----
    xc = (1470 + 1690) / 2
    a.add(caja(xc - 45, xc + 45, -45, 45, z1 - 140, z1 - 25), name="PROPUESTA_camara", color=NEGRO)
    a.add(cilindro((xc, 0, z1 - 200), (xc, 0, z1 - 140), 55), name="PROPUESTA_lente", color=NEGRO)
    zb = z_fondo_tobogan(1690) - 75
    a.add(caja(1470, 1690, -200, 200, zb - 45, zb), name="PROPUESTA_backlight_IR", color=NARANJA)
    return a


# =====================================================================
# 6 · CAPÓ DEL TOBOGÁN
# =====================================================================
def capo():
    a = cq.Assembly(name="Capo")
    xs, xe = SEN_X0, 640
    zt1, zt2 = SEN_Z1 + DZ, 1097 + DZ
    wa, wb = SEN_W / 2, CUERPO_W / 2
    zb1, zb2 = z_fondo_tobogan(1339) - 15, 860 + DZ
    a.add(loft_cuad([(xs, -wa, zt1 - T), (xs, wa, zt1 - T), (xs, wa, zt1), (xs, -wa, zt1)],
                    [(xe, -wb, zt2 - T), (xe, wb, zt2 - T), (xe, wb, zt2), (xe, -wb, zt2)]),
          name="capo_techo", color=CAPO)
    for s, lado in ((-1, "izq"), (1, "der")):
        ya1, yb1 = s * wa, s * (wa - T)
        ya2, yb2 = s * wb, s * (wb - T)
        a.add(loft_cuad([(xs, ya1, zb1), (xs, yb1, zb1), (xs, yb1, zt1), (xs, ya1, zt1)],
                        [(xe, ya2, zb2), (xe, yb2, zb2), (xe, yb2, zt2), (xe, ya2, zt2)]),
              name=f"capo_lateral_{lado}", color=CAPO)
    return a


# =====================================================================
# 7 · SALIDA (articulación + embudo + boca)
# =====================================================================
def salida():
    a = cq.Assembly(name="Salida")
    a.add(canal_u(EMBUDO, ruled=True), name="embudo", color=INOX)
    # boca de salida siguiendo la pendiente del embudo
    d = V(-1, 0, -(EMBUDO[1][1] - EMBUDO[2][1]) / (EMBUDO[1][0] - EMBUDO[2][0])).normalized()
    p0 = V(214, 0, 560 + DZ + 55)
    p1 = p0 + d * 150
    p2 = p1 + d * 45        # la punta del acople queda en X ≈ 0 (origen de la cota 2837)
    a.add(cilindro(p0.toTuple(), p1.toTuple(), SALIDA_D, hueco=T), name="tubo_salida_D165", color=INOX)
    a.add(cilindro(p1.toTuple(), p2.toTuple(), 200, hueco=18), name="acople_salida", color=VERDE)
    # articulación: el embudo pivota para regular la altura de salida [PLANO: 470-1070]
    zp = 890 + DZ
    a.add(cilindro((880, -CUERPO_W / 2 - 40, zp), (880, CUERPO_W / 2 + 40, zp), 30),
          name="eje_pivote", color=BASTIDOR)
    for s, lado in ((-1, "izq"), (1, "der")):
        y0 = s * (CUERPO_W / 2 + 3)
        tri = [(780, 760 + DZ), (990, 1000 + DZ), (990, 780 + DZ)]
        a.add(placa_xz(tri, y0 if s > 0 else y0 - 6, 6), name=f"placa_pivote_{lado}", color=INOX)
        a.add(barra((880, s * (CUERPO_W / 2 + 10), zp), (880, s * 632, zp - 60), a=20),
              name=f"palanca_ajuste_salida_{lado}", color=ROJO)
    return a


# =====================================================================
# ENSAMBLE Y EXPORTACIÓN
# =====================================================================
def construir():
    maquina = cq.Assembly(name="VAKI_Macro_1_Channel_escala_real")
    for sub in (bastidor(), cajon_entrada(), drenaje(), canal(), sensor(), capo(), salida()):
        maquina.add(sub, name=sub.name)
    return maquina


if __name__ == "__main__":
    aqui = os.path.dirname(os.path.abspath(__file__))
    m = construir()
    ruta = os.path.join(aqui, "vaki_macro_escala_real.step")
    m.export(ruta)
    bb = m.toCompound().BoundingBox()
    print("STEP guardado:", ruta)
    print("Envolvente  X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f" %
          (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
    print("Largo %.0f  Ancho %.0f  Alto %.0f" % (bb.xlen, bb.ylen, bb.zmax))
