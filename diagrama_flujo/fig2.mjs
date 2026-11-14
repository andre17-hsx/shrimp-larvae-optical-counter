// Figura 2: corte longitudinal del cajon (desde el deflector), la rampa y la malla, con el flujo del CFD.
// Coordenadas en mm: x aguas abajo desde la cresta, y a lo ancho (la mitad dibujada es y <= 0, el plano de corte es y = 0),
// z hacia arriba desde el fondo del cajon.
import * as k from "./kit/iso-kit.mjs";
import { faceXZ, waterTop } from "./lib.mjs";
import { makeScene } from "./scene.mjs";

export const W2 = 1000;
export const H2 = 560;
export const VARIANTS = ["original", "circular", "parabola"];
export const X0 = -344;
export const X1 = 345;

const SLOPE = 0.2127659574468085;
const T = 3;
const AV = 60;
const WALL = 300;
const XDEF = -250;
const zChute = (x) => AV - SLOPE * x;

export function wInt(x, d) {
  const e = d.planta.estrech;
  if (x >= -150) return 252;
  if (x <= -400) {
    if (x >= d.planta.x_chaflan) return 497;
    return 270 + Math.max(0, (x - d.planta.x_fondo) / (d.planta.x_chaflan - d.planta.x_fondo)) * 227;
  }
  for (let i = 1; i < e.length; i++) {
    const [xa, ya] = e[i - 1];
    const [xb, yb] = e[i];
    if (x <= xa && x >= xb) return ya + ((x - xa) / (xb - xa)) * (yb - ya);
  }
  return 497;
}

export function rampRing(variant) {
  if (variant === "original") return [[-T, 0], [0, 0], [0, AV], [-T, AV]];
  const pts = [];
  const n = 24;
  for (let i = 0; i <= n; i++) {
    if (variant === "circular") {
      const th = ((i / n) * Math.PI) / 2;
      pts.push([-AV + AV * Math.sin(th), AV * (1 - Math.cos(th))]);
    } else {
      const s = i / n;
      pts.push([-115 * (1 - s), AV * s * s]);
    }
  }
  pts.push([0, 0]);
  return pts;
}

export function rampBottom(variant, x) {
  if (x > 0) return zChute(x);
  if (variant === "original") return x > -T ? AV : 0;
  const ring = rampRing(variant).slice(0, -1);
  if (x <= ring[0][0]) return 0;
  for (let i = 1; i < ring.length; i++) {
    if (x <= ring[i][0]) return ring[i - 1][1] + ((x - ring[i - 1][0]) / (ring[i][0] - ring[i - 1][0])) * (ring[i][1] - ring[i - 1][1]);
  }
  return AV;
}

export function levelAt(d, variant, x) {
  const n = d.cfd[variant].nivel;
  if (x <= n[0][0]) return n[0][1];
  for (let i = 1; i < n.length; i++) {
    if (x <= n[i][0]) return n[i - 1][1] + ((x - n[i - 1][0]) / (n[i][0] - n[i - 1][0])) * (n[i][1] - n[i - 1][1]);
  }
  return n[n.length - 1][1];
}

export function projection2() {
  return k.fitProjection(
    [[X0, -480, -240], [X0, -480, 330], [X0, 20, 330], [X1, -480, 330], [X1, 20, -240], [X0, 20, -240], [X1, -480, -240]],
    W2, H2, { pad: 16, azimuth: 60, elevation: 21 },
  );
}

const GRID = [];
for (let x = X0; x < 0; x += 8) GRID.push(x);
GRID.push(0);

/** Escena auditable de una version de la rampa. */
export function buildScene2(d, variant) {
  const P = projection2();
  const sc = makeScene(P, "f2");
  const { slab, cyl, ext, pris, R } = sc;
  const at = (p) => k.iso(p, P);
  const L = (dd, style) => k.lineSvg(dd, style);
  const Dt = (pts, style) => k.dotsSvg(pts, style);
  const wG = GRID.map((x) => wInt(x, d));
  const wPoly = (x) => {
    for (let i = 1; i < GRID.length; i++) if (x <= GRID[i]) return wG[i - 1] + ((x - GRID[i - 1]) / (GRID[i] - GRID[i - 1])) * (wG[i] - wG[i - 1]);
    return wG[wG.length - 1];
  };
  const xs = GRID.filter((x) => x >= X0);
  const floorRing = [...xs.map((x) => [x, -wPoly(x) - T]), [0, 0], [X0, 0]];
  const wallBand = [...xs.map((x) => [x, -wPoly(x)]), ...[...xs].reverse().map((x) => [x, -wPoly(x) - T])];

  // ---------- bastidor ----------
  const cm = [-300, -180, -60];
  for (const x of cm) {
    slab(`cross${x}`, { x: x - 15, y: -218, w: 30, d: 234, r: 1.5 }, -82, 30, { tone: "lo" }, { bevel: 0.6 });
    slab(`stand.footA${x}`, { x: x - 15, y: -218, w: 30, d: 28, r: 1 }, -90, 8, { tone: "lo", crease: "none" }, { bevel: 0 });
    slab(`stand.footB${x}`, { x: x - 15, y: -12, w: 30, d: 28, r: 1 }, -90, 8, { tone: "lo", crease: "none" }, { bevel: 0 });
  }
  for (const y of [-200, -40]) {
    slab(`rail${y}`, { x: X0, y, w: -4 - X0, d: 40, r: 2 }, -52, 49, { tone: "mid" }, { bevel: 0.8, extra: L(k.lineOnTop([X0, y + 20], [-4, y + 20], -3, P), { tone: "faint" }) + Dt(cm.map((x) => at([x, y + 20, -3])), { size: 0.5 }) });
  }

  // ---------- piso del cajon y paredes de acrilico ----------
  ext("floor", floorRing, -T, T, { tone: "mid", crease: "faint" }, { at: [-170, -120, -1.5] });
  ext("wall.far", wallBand, 0, WALL, { tone: "mid", crease: "faint" }, { glass: true, at: [-170, -250, 150] });
  // deflector: placa trapezoidal que sigue la pared inclinada
  const wd0 = wPoly(XDEF - T);
  const wd1 = wPoly(XDEF);
  ext("deflector", [[XDEF - T, -wd0], [XDEF, -wd1], [XDEF, 0], [XDEF - T, 0]], 50, WALL - 50, { tone: "mid", crease: "faint" }, {
    glass: true, at: [XDEF - 1.5, -wd1 / 2, 175],
    extra: Dt([-1, 1].flatMap((s) => [58, 292].map((z) => at([XDEF, -wd1 * 0.5 + s * wd1 * 0.4, z]))), { size: 0.5 }),
  });

  // ---------- rampa de la cresta ----------
  if (variant === "original") {
    pris("ramp.wall", rampRing("original"), -252, 0, { tone: "hi", crease: "faint" });
    pris("ramp.lip", [[-9, AV], [6, AV], [6, AV + 5], [-9, AV + 5]], -252, 0, { tone: "hi", crease: "faint" });
  } else {
    pris("ramp", rampRing(variant), -252, 0, { tone: "hi", lit: true, crease: "faint" });
  }

  // ---------- malla, chute y sumidero ----------
  const zc = zChute;
  const meshLines = [];
  for (let y = -238; y < 0; y += 14) meshLines.push(k.pathOf([at([0, y, zc(0)]), at([282, y, zc(282)])]));
  pris("mesh", [[0, zc(0)], [282, zc(282)], [282, zc(282) - 1], [0, zc(0) - 1]], -252, 0, { tone: "hi", crease: "none" }, { extra: L(meshLines.join(""), { tone: "faint" }), at: [141, -126, (zc(0) + zc(282)) / 2] });
  for (const x of [50, 150, 250]) {
    pris(`mesh.bar${x}`, [[x - 3, zc(x - 3) - 1], [x + 3, zc(x + 3) - 1], [x + 3, zc(x + 3) - 12], [x - 3, zc(x - 3) - 12]], -249, -3, { tone: "lo", crease: "none" });
  }
  pris("chute.floor", [[282, zc(282)], [X1, zc(X1)], [X1, zc(X1) - T], [282, zc(282) - T]], -252, 0, { tone: "mid", crease: "faint" });
  pris("chute.wall", [[0, zc(0) - T], [X1, zc(X1) - T], [X1, zc(X1) - T + 180], [0, zc(0) - T + 180]], -255, -252, { tone: "mid", crease: "none" }, { glass: true });
  // sumidero: bandeja de acrilico bajo la malla
  slab("sump.floor", { x: 8, y: -252, w: 268, d: 252, r: 0 }, -122, 3, { tone: "mid", crease: "faint" }, { steps: 1, bevel: 0, glass: true });
  pris("sump.far", [[8, -119], [276, -119], [276, zc(276) - 1], [8, zc(8) - 1]], -252, -249, { tone: "mid", crease: "none" }, { glass: true });
  pris("sump.near", [[8, -119], [276, -119], [276, zc(276) - 1], [8, zc(8) - 1]], -3, 0, { tone: "mid", crease: "none" }, { glass: true });
  slab("sump.end0", { x: 8, y: -249, w: 3, d: 246, r: 0 }, -119, zc(11) - 1 + 119, { tone: "mid", crease: "none" }, { steps: 1, bevel: 0, glass: true });
  slab("sump.end1", { x: 273, y: -249, w: 3, d: 246, r: 0 }, -119, zc(276) - 1 + 119, { tone: "mid", crease: "none" }, { steps: 1, bevel: 0, glass: true });
  // valvula de drenaje bajo el sumidero (pieza sobre pieza, sin solaparse)
  const vx = d.planta.x_drenaje;
  cyl("valve.pipe1", vx, -126, 22, -150, 28, { tone: "mid", crease: "none" });
  cyl("valve.body", vx, -126, 34, -180, 30, { tone: "hi" }, { steps: 32, bevel: 0.6 });
  cyl("valve.pipe2", vx, -126, 22, -230, 50, { tone: "mid", crease: "none" });
  cyl("valve.flange", vx, -126, 30, -236, 6, { tone: "mid" }, { steps: 32 });
  slab("valve.lever", { x: vx - 3, y: -92, w: 6, d: 60, r: 1 }, -172, 4, { tone: "mid", crease: "none" }, { steps: 2, bevel: 0.4 });
  // regla de nivel H, con su cero en la cresta, en la cara exterior de la pared
  slab("ruler", { x: -130, y: -252 - T - 3, w: 100, d: 3, r: 0 }, AV, 90, { tone: "lo", crease: "none" }, { steps: 1, bevel: 0 });

  return { P, R, sc, wPoly };
}

/** Capas que no son solidos: agua por version. */
export function waterLayers(d, P) {
  const at = (p) => k.iso(p, P);
  const xsAll = [];
  for (let x = X0; x <= X1; x += 5) xsAll.push(x);
  const out = {};
  for (const v of VARIANTS) {
    const zs = xsAll.map((x) => Math.max(levelAt(d, v, x), rampBottom(v, x)));
    const sec = xsAll.map((x, i) => [x, zs[i]]);
    for (let i = xsAll.length - 1; i >= 0; i--) sec.push([xsAll[i], rampBottom(v, xsAll[i])]);
    const strips = waterTop(xsAll, zs, () => 0, (x) => -wInt(x, d), P);
    const light = strips.filter((s) => s.slope > -0.12).map((s) => s.d).join("");
    const dark = strips.filter((s) => s.slope <= -0.12).map((s) => s.d).join("");
    out[v] = `<path class="water-sec" d="${faceXZ(sec, 0, P)}"/><path class="water-top" d="${light}"/><path class="water-top" data-steep d="${dark}"/><path class="water-edge" d="${k.pathOf(xsAll.map((x, i) => at([x, 0, zs[i]])))}"/>`;
  }
  return out;
}

export function buildFig2(d) {
  const scenes = Object.fromEntries(VARIANTS.map((v) => [v, buildScene2(d, v)]));
  const main = scenes.parabola;
  const P = main.P;
  // el svg de la rampa de cada version va en la ranura de la rampa de la escena principal
  const rampSvg = VARIANTS.map((v) => {
    const names = v === "original" ? ["ramp.wall", "ramp.lip"] : ["ramp"];
    const items = names.map((n) => scenes[v].R.items.find((it) => it.name === n).svg).join("");
    return `<g data-v="${v}">${items}</g>`;
  }).join("");
  const rampItem = main.R.items.find((it) => it.name === "ramp");
  rampItem.svg = rampSvg;
  const water = waterLayers(d, P);
  const waterSlot = VARIANTS.map((v) => `<g data-v="${v}">${water[v]}</g>`).join("");
  const pts = VARIANTS.map((v) => `<g data-v="${v}" data-pts="${v}"></g>`).join("");
  const all = ["floor", "wall.far", "deflector", "ramp", "mesh", "chute.floor", "chute.wall", "sump.floor", "valve.lever", "ruler"];
  const body = main.sc.compose([
    { after: all, svg: waterSlot + pts + `<path class="marker" opacity="0" d=""/><circle class="marker-dot" opacity="0" r="2.6" cx="0" cy="0"/>` },
  ]);
  return { P, body, scenes };
}
