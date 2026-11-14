// =====================================================================
//  CONTADOR ÓPTICO DE LARVAS DE CAMARÓN — estilo Vaki (line-scan)
//  Modelo 3D paramétrico · Cotas en milímetros
//  Abrir con OpenSCAD (gratis) · F5 = vista rápida · F6 = render · F7 = exportar STL
// =====================================================================
//  Ejes:  X = largo (dirección del flujo) · Y = ancho · Z = alto
// =====================================================================

/* [Vista] */
ver_bastidor    = true;
ver_hidraulica  = true;
ver_optica      = true;
ver_control     = true;
ver_capo        = true;   // false = quita el capó y deja ver cámara + backlight
capo_corte      = true;   // true = capó "en corte" (se ve el interior)
alfa_capo       = 0.30;   // transparencia del capó

/* [Bastidor] */
bas_L    = 1200;   // largo
bas_W    = 500;    // ancho
bas_H    = 700;    // altura de rieles superiores
perfil   = 40;     // perfil de aluminio T-slot 40x40
rueda_d  = 100;

/* [Canal de conteo] */
canal_w     = 150;   // ancho útil (define la resolución: 150/2048 = 0,073 mm/px)
pared_h     = 55;
pared_t     = 8;
lecho_t     = 10;    // espesor del acrílico
canal_L     = 480;   // longitud a lo largo de la pendiente
canal_ang   = 35;    // inclinación
canal_x0    = 480;
canal_z0    = 900;

/* [Bandeja ancha de recepción] */
bandeja_w   = 430;   // ancho en la entrada (se estrecha hasta canal_w)
bandeja_L   = 180;

/* [Cajón / tanque de entrada (stilling box)] */
cajon_L     = 270;   // largo (X)
cajon_W     = 430;   // ancho (Y) — igual que la bandeja
cajon_prof  = 170;   // profundidad de agua = ALTURA DEL VERTEDERO
                     // (el labio queda EXACTAMENTE al nivel donde arranca la
                     //  bandeja, para que el agua no caiga en cascada)
cajon_fb    = 70;    // francobordo: paredes por encima del vertedero
cajon_boca  = 80;    // diámetro de la boca de entrada (conexión de manguera)
cajon_H     = cajon_prof + cajon_fb;   // altura total de paredes

/* [Zona de imagen] */
img_dist      = 250;   // distancia desde el inicio del canal
camara_alt    = 400;   // lente -> lámina (lente 35 mm C-mount)
capo_L        = 270;
capo_W        = 320;
capo_H        = 470;

/* [Colector / dewatering] */
col_L    = 250;
col_W    = 320;
col_H    = 260;

// ---------- Colores ----------
C_ALU   = [0.74,0.76,0.78];
C_INOX  = [0.82,0.84,0.86];
C_ACRIL = [0.62,0.82,0.92];
C_AGUA  = [0.30,0.62,0.85];
C_CAM   = [0.11,0.13,0.17];
C_LUZ   = [0.95,0.55,0.10];
C_CAPO  = [0.88,0.90,0.92];
C_TUBO  = [0.35,0.55,0.75];
C_VERDE = [0.18,0.55,0.28];
C_ROJO  = [0.78,0.20,0.15];
C_NEG   = [0.14,0.14,0.16];
C_LINEA = [0.90,0.08,0.08];   // marcador de la línea de imagen (rojo)

// =====================================================================
//  AUXILIARES
// =====================================================================
module tslot(largo, eje="x") {
    color(C_ALU)
    if      (eje=="x") cube([largo, perfil, perfil]);
    else if (eje=="y") cube([perfil, largo, perfil]);
    else               cube([perfil, perfil, largo]);
}

// Riostra diagonal entre dos puntos
module riostra(p1, p2, t=26) {
    color(C_ALU) hull() {
        translate(p1) cube(t, center=true);
        translate(p2) cube(t, center=true);
    }
}

// Tramo de tubo/manguera entre dos puntos (los codos siempre quedan unidos)
module tubo(p1, p2, d) {
    hull() {
        translate(p1) sphere(d=d, $fn=26);
        translate(p2) sphere(d=d, $fn=26);
    }
}

module rueda() {
    color(C_NEG) {
        translate([0,0,-25]) cube([56,56,50], center=true);
        translate([0,0,-50-rueda_d/2]) rotate([90,0,0])
            cylinder(h=34, d=rueda_d, center=true, $fn=36);
    }
}

// Posición absoluta sobre el canal, a distancia d de su inicio
function cpos(d) = [canal_x0 + d*cos(canal_ang), 0, canal_z0 - d*sin(canal_ang)];

// =====================================================================
//  1 · BASTIDOR (perfil T-slot + ruedas)
// =====================================================================
module bastidor() {
    // largueros longitudinales (abajo y arriba)
    for (y = [-bas_W/2, bas_W/2-perfil])
        for (z = [0, bas_H-perfil])
            translate([0, y, z]) tslot(bas_L, "x");
    // travesaños SOLO en los extremos arriba (el centro queda libre
    // para que cuelgue el colector); abajo sí lleva uno central
    for (x = [0, bas_L-perfil]) {
        translate([x, -bas_W/2, bas_H-perfil]) tslot(bas_W, "y");
        translate([x, -bas_W/2, 0])            tslot(bas_W, "y");
    }
    translate([bas_L/2-perfil/2, -bas_W/2, 0]) tslot(bas_W, "y");
    // columnas
    for (x = [0, bas_L-perfil])
        for (y = [-bas_W/2, bas_W/2-perfil])
            translate([x, y, 0]) tslot(bas_H, "z");
    // riostras diagonales laterales
    for (s = [-1,1]) {
        y = s*(bas_W/2-perfil/2);
        riostra([perfil, y, perfil], [bas_L*0.45, y, bas_H-perfil]);
        riostra([bas_L-perfil, y, perfil], [bas_L*0.55, y, bas_H-perfil]);
    }
    // ruedas
    for (x = [perfil, bas_L-perfil])
        for (y = [-bas_W/2+perfil/2, bas_W/2-perfil/2])
            translate([x, y, 0]) rueda();
}

// =====================================================================
//  2 · BANDEJA ANCHA DE RECEPCIÓN (embudo: ancho -> canal)
//      Equivale a la "pala" ancha del Vaki
// =====================================================================
module bandeja() {
    // fondo que se estrecha
    color(C_INOX)
    hull() {
        translate([0, -bandeja_w/2, 0])      cube([2, bandeja_w, lecho_t]);
        translate([bandeja_L-2, -canal_w/2-pared_t, 0]) cube([2, canal_w+2*pared_t, lecho_t]);
    }
    // paredes laterales convergentes
    color(C_INOX)
    for (s = [-1,1])
        hull() {
            translate([0, s*bandeja_w/2 - (s>0?pared_t:0), 0])       cube([2, pared_t, pared_h+25]);
            translate([bandeja_L-2, s*canal_w/2 - (s>0?0:pared_t), 0]) cube([2, pared_t, pared_h]);
        }
    // agua en la bandeja
    color(C_AGUA, 0.5)
    hull() {
        translate([2, -bandeja_w/2+pared_t, lecho_t]) cube([2, bandeja_w-2*pared_t, 8]);
        translate([bandeja_L-4, -canal_w/2, lecho_t]) cube([2, canal_w, 6]);
    }
}

// =====================================================================
//  2b · CAJÓN / TANQUE DE ENTRADA (stilling box)
//      Aquí llega la manguera de la bomba. El agua se calma, atraviesa
//      los enderezadores y REBOSA por el vertedero hacia la bandeja.
// =====================================================================
// El origen del cajón se calcula DESDE el punto donde arranca la bandeja:
// el labio del vertedero debe quedar a ese mismo nivel (sin caída libre).
function cajon_org() = let(p = cpos(-bandeja_L))
                      [p[0]-cajon_L, p[2]-cajon_prof];

module cajon_entrada() {
    o    = cajon_org();
    x0   = o[0];  z0 = o[1];
    pinz = z0 + cajon_prof;    // nivel del labio == inicio de la bandeja
    esp  = 8;
    // fondo
    color(C_INOX) translate([x0, -cajon_W/2, z0]) cube([cajon_L, cajon_W, esp]);
    // paredes: trasera y laterales con francobordo
    color(C_INOX) {
        translate([x0, -cajon_W/2, z0])       cube([esp, cajon_W, cajon_H]);
        translate([x0, -cajon_W/2, z0])       cube([cajon_L, esp, cajon_H]);
        translate([x0,  cajon_W/2-esp, z0])   cube([cajon_L, esp, cajon_H]);
        // pared frontal = VERTEDERO, su borde queda al nivel de la bandeja
        translate([x0+cajon_L-esp, -cajon_W/2, z0]) cube([esp, cajon_W, cajon_prof]);
    }
    // agua (llega justo al labio y rebosa)
    color(C_AGUA, 0.55)
        translate([x0+esp, -cajon_W/2+esp, z0+esp])
            cube([cajon_L-2*esp, cajon_W-2*esp, cajon_prof-esp-2]);
    // enderezadores de flujo (sobresalen del agua)
    color(C_INOX)
    for (i = [1:3])
        translate([x0+cajon_L*0.42, -cajon_W/2 + i*cajon_W/4 - 3, z0+esp])
            cube([cajon_L*0.50, 6, cajon_prof+15]);
    // LABIO / CRESTA del vertedero: enrasado con la bandeja y con chaflán
    // a la misma pendiente, para que el agua pase sin cascada.
    color(C_ROJO) {
        translate([x0+cajon_L-esp-14, -cajon_W/2, pinz-6])
            cube([esp+14, cajon_W, 6]);
        // chaflán de transición hacia el plano inclinado
        translate([x0+cajon_L, 0, pinz]) rotate([0, canal_ang, 0])
            translate([0, -cajon_W/2, -6]) cube([46, cajon_W, 6]);
    }
    // lámina de agua que sale por el vertedero (continuidad visual)
    color(C_AGUA, 0.5)
        translate([x0+cajon_L, 0, pinz]) rotate([0, canal_ang, 0])
            translate([0, -cajon_W/2+esp, 0]) cube([50, cajon_W-2*esp, 7]);
    // boca de entrada por el FONDO (aquí conecta la manguera de la bomba)
    color(C_TUBO)
        translate([x0+cajon_L*0.35, 0, z0-75]) cylinder(h=85, d=cajon_boca, $fn=30);
    color([0.55,0.57,0.60])   // brida
        translate([x0+cajon_L*0.35, 0, z0-18]) cylinder(h=14, d=cajon_boca+34, $fn=30);
    // patas de soporte hasta el bastidor
    color(C_ALU)
    for (x = [x0+20, x0+cajon_L-60])
        for (y = [-175, 175-perfil])
            translate([x, y, bas_H-perfil]) cube([perfil, perfil, z0-bas_H+perfil]);
}

// Punto donde la manguera se conecta al cajón
function cajon_boca_pos() = let(o = cajon_org())
                            [o[0]+cajon_L*0.35, 0, o[1]-70];

// =====================================================================
//  3 · CANAL INCLINADO TRANSPARENTE (zona de conteo)
// =====================================================================
module canal_local() {
    // lecho de acrílico
    color(C_ACRIL, 0.45)
        translate([0, -(canal_w/2+pared_t), -lecho_t])
            cube([canal_L, canal_w+2*pared_t, lecho_t]);
    // paredes
    color(C_ACRIL, 0.35)
    for (s = [-1,1])
        translate([0, s*canal_w/2 - (s>0?0:pared_t), 0])
            cube([canal_L, pared_t, pared_h]);
    // lámina de agua
    color(C_AGUA, 0.5)
        translate([0, -canal_w/2, 0]) cube([canal_L, canal_w, 5]);
    // LÍNEA de imagen (lo que capta la cámara lineal)
    color(C_LINEA)
        translate([img_dist-3, -canal_w/2, 5]) cube([6, canal_w, 2.5]);
}

module canal() {
    translate([canal_x0, 0, canal_z0]) rotate([0, canal_ang, 0]) canal_local();
    // bandeja ancha justo antes del canal, con la misma pendiente
    translate([canal_x0, 0, canal_z0]) rotate([0, canal_ang, 0])
        translate([-bandeja_L, 0, -lecho_t]) bandeja();
    // soportes del canal al bastidor (solo donde el canal va POR ENCIMA
    // del bastidor; más abajo lo sostiene la caja colectora)
    for (d = [0, canal_L*0.5]) {
        p = cpos(d);
        h = p[2] - lecho_t - (bas_H - perfil);
        if (h > perfil)
            color(C_ALU)
            for (s = [-1, 1])
                translate([p[0] + (d>0 ? -20 : 60),
                           s*(canal_w/2+pared_t) - (s>0 ? -10 : perfil+10),
                           bas_H-perfil])
                    cube([perfil, perfil, h]);
    }
}

// =====================================================================
//  4 · CABEZAL ÓPTICO — capó + cámara lineal + backlight
// =====================================================================
module cabezal_optico() {
    p = cpos(img_dist);
    base_z = p[2] + 55;
    // --- capó (bloquea el sol y protege la óptica) ---
    if (ver_capo) {
        color(C_CAPO, alfa_capo)
        difference() {
            translate([p[0]-capo_L/2, -capo_W/2, base_z])
                difference() {
                    cube([capo_L, capo_W, capo_H]);
                    translate([7,7,-2]) cube([capo_L-14, capo_W-14, capo_H-5]);
                }
            // corte de un cuadrante para ver el interior
            if (capo_corte)
                translate([p[0]-capo_L/2-5, -capo_W/2-5, base_z+capo_H*0.30])
                    cube([capo_L/2+5, capo_W/2+5, capo_H]);
        }
        // faldón lateral del capó (baja hacia el canal)
        color(C_CAPO, alfa_capo)
        for (s=[-1,1])
            if (!(capo_corte && s<0))
            translate([p[0]-capo_L/2, s*(capo_W/2-7)-(s>0?0:7), p[2]+5])
                cube([capo_L, 7, 55]);
    }
    // --- cámara lineal Basler + lente C-mount ---
    color(C_CAM)
        translate([p[0]-42, -42, p[2]+camara_alt]) cube([84, 84, 76]);
    color([0.26,0.28,0.31])
        translate([p[0], 0, p[2]+camara_alt-52]) cylinder(h=56, d=44, $fn=44);
    // conector Ethernet (GigE)
    color([0.20,0.45,0.20])
        translate([p[0]-52, -14, p[2]+camara_alt+20]) cube([12, 28, 22]);
    // --- haz óptico hacia la línea ---
    color([0.90,0.30,0.15], 0.16)
        translate([p[0], 0, p[2]+6])
            linear_extrude(height=camara_alt-58, scale=0.30)
                square([30, canal_w], center=true);
    // --- backlight lineal continuo (bajo el acrílico) ---
    translate([canal_x0, 0, canal_z0]) rotate([0, canal_ang, 0]) {
        color(C_LUZ)
            translate([img_dist-35, -canal_w/2-12, -lecho_t-30])
                cube([70, canal_w+24, 24]);
        color([0.45,0.45,0.48])   // disipador
            translate([img_dist-45, -canal_w/2-18, -lecho_t-52])
                cube([90, canal_w+36, 22]);
    }
}

// =====================================================================
//  5 · COLECTOR + MALLA DEWATERING + DOS SALIDAS
// =====================================================================
module colector() {
    p  = cpos(canal_L);
    bx = p[0] - 25;
    bz = p[2] - col_H + 30;
    // caja colectora (cuelga entre los rieles superiores)
    color(C_INOX, 0.92)
    translate([bx, -col_W/2, bz])
        difference() {
            cube([col_L, col_W, col_H]);
            translate([7,7,8]) cube([col_L-14, col_W-14, col_H]);
        }
    // malla de dewatering
    color([0.55,0.57,0.60])
    for (i = [0:11])
        translate([bx+12+i*((col_L-24)/11), -col_W/2+9, bz+col_H*0.5])
            cube([5, col_W-18, 5]);
    // ---- SALIDA INTERMEDIA: drenaje de AGUA (baja y sale del bastidor) ----
    xd = bx + col_L*0.32;
    color(C_TUBO) {
        tubo([xd, 0, bz+10], [xd, 0, 115], 62);
        tubo([xd, 0, 115], [xd, -bas_W/2-90, 115], 62);
    }
    color(C_ROJO) {   // válvula de regulación
        translate([xd, 0, bz-150]) cylinder(h=44, d=98, $fn=28);
        translate([xd, 0, bz-128]) rotate([0,90,0])
            cylinder(h=100, d=16, $fn=16, center=true);
    }
    // ---- SALIDA FINAL: camarón -> piscina destino (manguera flexible) ----
    color(C_VERDE) {
        tubo([bx+col_L-20, 0, bz+col_H*0.30], [bx+col_L+120, 0, bz+col_H*0.10], 74);
        tubo([bx+col_L+120, 0, bz+col_H*0.10], [bas_L+150, 0, bz-40], 74);
    }
}

// =====================================================================
//  6 · HIDRÁULICA DE ENTRADA (bomba de bajo cizallamiento + manguera)
// =====================================================================
module hidraulica_entrada() {
    bp = cajon_boca_pos();       // boca de entrada del cajón
    xb = bp[0];                  // la bomba se alinea bajo la boca
    // bomba / soplador de bajo cizallamiento (peso abajo, en el bastidor)
    color([0.28,0.31,0.36])
        translate([xb-115, -140, perfil]) cube([230, 240, 195]);
    color(C_NEG)
        translate([xb, -20, perfil+195]) cylinder(h=32, d=100, $fn=26);
    // IMPULSIÓN: sube vertical y entra por el FONDO del cajón (no cruza el canal)
    color([0.80,0.54,0.30])
        tubo([xb, 0, perfil+205], bp, 72);
    // SUCCIÓN: desde el estanque, entra por fuera del bastidor
    color([0.80,0.54,0.30]) {
        tubo([xb-115, -60, perfil+100], [-120, -60, 190], 72);
        tubo([-120, -60, 190], [-230, -60, 90], 72);
    }
}

// =====================================================================
//  7 · CONTROL — PC industrial, gabinete y pantalla táctil
// =====================================================================
module control() {
    // gabinete eléctrico + PC (colgado del larguero)
    color([0.85,0.86,0.88])
        translate([bas_L-360, bas_W/2-perfil-70, bas_H-perfil-320])
            cube([320, 70, 310]);
    color(C_NEG)   // ventilación
    for (i=[0:5])
        translate([bas_L-340+i*50, bas_W/2-perfil-72, bas_H-perfil-150])
            cube([30, 3, 90]);
    // poste de la pantalla
    color(C_ALU)
        translate([bas_L-300, -bas_W/2, bas_H-perfil]) cube([perfil, perfil, 560]);
    // pantalla táctil inclinada
    translate([bas_L-300, -bas_W/2+perfil/2, bas_H+480]) rotate([0,-14,0]) {
        color(C_NEG)          translate([-18,-170,0]) cube([46, 340, 270]);
        color([0.16,0.38,0.58]) translate([-20,-155,16]) cube([44, 310, 232]);
    }
}

// =====================================================================
//  ENSAMBLE
// =====================================================================
if (ver_bastidor)   bastidor();
if (ver_hidraulica) { cajon_entrada(); canal(); colector(); hidraulica_entrada(); }
if (ver_optica)     cabezal_optico();
if (ver_control)    control();
