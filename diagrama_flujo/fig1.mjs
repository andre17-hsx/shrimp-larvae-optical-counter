// Figura 1: el circuito completo del agua en un visor 3D (three.js) con las mallas REALES del prototipo (los cuerpos del script
// de Fusion 360, exportados con exportar_modelo.py) y un "mar" de particulas (live1.js). Coordenadas de Fusion, en mm.
import fs from "node:fs";
import * as G from "./kit/lathe.mjs";
import { wInt } from "./fig2.mjs";

const HERE = new URL(".", import.meta.url);
const model = JSON.parse(fs.readFileSync(new URL("./modelo.json", HERE), "utf8"));
export const W1 = 1000;
export const H1 = 640;

// ---------------------------------------------------------------- recorridos del agua (coordenadas de Fusion)
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (a) => {
  const l = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};
const r1 = (v) => Math.round(v * 10) / 10;
const r3 = (v) => Math.round(v * 1000) / 1000;

function resample(pts, step) {
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(...sub(pts[i], pts[i - 1])));
  const total = cum[cum.length - 1];
  const n = Math.max(2, Math.round(total / step) + 1);
  const out = [];
  let j = 1;
  for (let i = 0; i < n; i++) {
    const u = (i / (n - 1)) * total;
    while (j < pts.length - 1 && cum[j] < u) j++;
    const t = (u - cum[j - 1]) / (cum[j] - cum[j - 1] || 1);
    out.push({ p: [0, 1, 2].map((a) => pts[j - 1][a] + (pts[j][a] - pts[j - 1][a]) * t), u });
  }
  return { st: out, total };
}
// estaciones: centro, ejes e1 (a lo ancho) y e2 (hacia arriba), semiejes A y B, mezcla rectangulo-disco m y llenado f
function tube(points, radius, { fillet = 3, step = 12 } = {}) {
  const line = G.fillet(points, radius(0) * fillet, 8);
  const { st, total } = resample(line, step);
  return {
    total,
    st: st.map((s, i) => {
      const a = st[Math.max(0, i - 1)].p;
      const b = st[Math.min(st.length - 1, i + 1)].p;
      const t = unit(sub(b, a));
      const ref = Math.abs(t[2]) < 0.85 ? [0, 0, 1] : [0, 1, 0];
      const e1 = unit(cross(t, ref));
      let e2 = cross(e1, t);
      if (e2[2] < 0 || (Math.abs(e2[2]) < 1e-6 && e2[1] < 0)) e2 = e2.map((v) => -v);
      const rr = radius(s.u / total);
      return [...s.p.map(r1), ...e1.map(r3), ...e2.map(r3), r1(rr), r1(rr), 1, 1];
    }),
  };
}

// altura de la superficie superior de ciertos cuerpos en la vertical (X, Y), leida de las mallas
export function topZ(names, X, Y) {
  let best = -Infinity;
  for (const b of model.bodies) {
    if (!names.some((n) => b.n === n || b.n.startsWith(n))) continue;
    const v = b.v;
    const t = b.t;
    for (let f = 0; f < t.length / 3; f++) {
      const a = t[f * 3] * 3, c = t[f * 3 + 1] * 3, e = t[f * 3 + 2] * 3;
      const ax = v[a], ay = v[a + 1], bx = v[c], by = v[c + 1], cx = v[e], cy = v[e + 1];
      const den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);
      if (Math.abs(den) < 1e-9) continue;
      const l0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den;
      const l1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den;
      const l2 = 1 - l0 - l1;
      if (l0 < -1e-6 || l1 < -1e-6 || l2 < -1e-6) continue;
      best = Math.max(best, l0 * v[a + 2] + l1 * v[c + 2] + l2 * v[e + 2]);
    }
  }
  return best;
}

export function buildFig1(d) {
  const R = { topZ };
  const ZC = model.rutas.zc;
  const XV = model.rutas.x_vertedero;
  const em = model.rutas.embudo;
  const XE = em.xe;
  const ZE = em.ze;
  const levelBack = ZC + 118;
  const levelFront = ZC + 104;

  // ---- lecho real: altura de la superficie superior en y = 0 a lo largo de toda la corriente (de las mallas)
  const BEDN = ["fondo_cajon", "vertedero_rampa", "malla_cedazo", "fondo_tobogan", "PROPUESTA_ventana_acrilico"];
  const bedX = [];
  const bedZ = [];
  let last = ZC;
  for (let X = 2850; X >= XE - 10; X -= 6) {
    let z = R.topZ(BEDN, X, 0);
    if (!Number.isFinite(z)) z = last;
    last = z;
    bedX.push(X);
    bedZ.push(r1(z));
  }
  const wAt = bedX.map((X) => r1(wInt(XV - X, d)));
  const bedAt = (X) => bedZ[Math.max(0, Math.min(bedZ.length - 1, Math.round((2850 - X) / 6)))];

  // ---- agua quieta (volumenes translucidos)
  const po = model.rutas.piscina_origen;
  const pd = model.rutas.piscina_destino;
  const box = (x0, x1, y0, y1, z0, z1) => {
    const q = (a, b, c, e, top) => Object.assign([a, b, c, e], { top });
    return [
      q([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], true),
      q([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]),
      q([x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]),
      q([x0, y0, z0], [x0, y1, z0], [x0, y1, z1], [x0, y0, z1]),
      q([x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]),
    ];
  };
  const prism = (Xa, Xb, level) => {
    const qs = [];
    const xs = [];
    for (let X = Xa; X >= Xb; X -= 12) xs.push(X);
    if (xs[xs.length - 1] !== Xb) xs.push(Xb);
    const w = (X) => wInt(XV - X, d) - 1;
    for (let i = 1; i < xs.length; i++) {
      const [xa, xb] = [xs[i - 1], xs[i]];
      qs.push(Object.assign([[xa, -w(xa), level], [xa, w(xa), level], [xb, w(xb), level], [xb, -w(xb), level]], { top: true }));
      qs.push([[xa, -w(xa), ZC], [xb, -w(xb), ZC], [xb, -w(xb), level], [xa, -w(xa), level]]);
      qs.push([[xa, w(xa), ZC], [xb, w(xb), ZC], [xb, w(xb), level], [xa, w(xa), level]]);
    }
    qs.push([[Xa, -w(Xa), ZC], [Xa, w(Xa), ZC], [Xa, w(Xa), level], [Xa, -w(Xa), level]]);
    qs.push([[Xb, -w(Xb), ZC], [Xb, w(Xb), ZC], [Xb, w(Xb), level], [Xb, -w(Xb), level]]);
    return qs;
  };
  const vols = [
    { quads: box(po.x0 + 5, po.x1 - 5, po.y0 + 5, po.y1 - 5, 5, 270) },
    { quads: box(pd.x0 + 5, pd.x1 - 5, pd.y0 + 5, pd.y1 - 5, 5, 110) },
    { quads: prism(XV + 744, XV + 254, levelBack) },
    { quads: prism(XV + 250, XV + 116, levelFront) },
  ];

  const flat = (vol) => {
    const top = [];
    const side = [];
    for (const q of vol.quads) {
      const dst = q.top ? top : side;
      for (const i of [0, 1, 2, 0, 2, 3]) dst.push(...q[i].map(r1));
    }
    return { top, side };
  };
  const waterVols = vols.map(flat);

  // ---- trayectos tubulares (estaciones)
  const rt = model.rutas;
  const succion = tube(rt.succion, () => 55);
  const impulsion = tube(rt.impulsion, () => 55);
  const dif = rt.difusor;
  const difusor = tube([[dif.eje[0], dif.eje[1], dif.z0], [dif.eje[0], dif.eje[1], dif.z1 + 3]], (t) => dif.r0 + (dif.r1 - dif.r0) * t, { step: 14 });
  // embudo: del rectangulo en el extremo del canal al disco de la manguera, luego tubo, acople y manguera
  const al = (em.alfa * Math.PI) / 180;
  const ca = Math.cos(al);
  const sa = Math.sin(al);
  const dir = [-ca, 0, -sa];
  const e2 = [-sa, 0, ca];
  const p0 = [XE, 0, ZE + em.h / 2];
  const along = (p, t) => [p[0] + dir[0] * t, p[1], p[2] + dir[2] * t];
  const Lloft = em.largo_embudo;
  const Ltail = em.largo_tubo + em.largo_acople;
  const Lhose = Math.hypot(em.fin[0] - em.boca[0], em.fin[2] - em.boca[2]);
  const totalE = Lloft + Ltail + Lhose;
  const embudo = { total: totalE, st: [] };
  for (let s = 0; s <= totalE + 0.01; s += 12) {
    const tt = Math.min(1, s / Lloft);
    const A = 252 + (em.r - 252) * tt;
    const B = em.h / 2 + (em.r - em.h / 2) * tt;
    embudo.st.push([...along(p0, s).map(r1), 0, 1, 0, ...e2.map(r3), r1(A), r1(B), r3(tt), 0]);
  }
  const purga = tube(rt.purga, () => 28, { fillet: 3 });
  const out = {};
  for (const [n, t] of Object.entries({ succion, impulsion, difusor, embudo, purga })) out[n] = { total: r1(t.total), st: t.st };

  const stations = [
    { name: "Estanque de origen", at: [2350, -1850, 280], k: "none", txt: "El agua con las larvas espera en reposo; la canasta de succión la deja entrar a la bomba." },
    { name: "Succión y bomba", at: [2430, -850, 300], k: "lin", v10: 1.177, txt: "La bomba toma el agua del estanque; su variador fija el caudal." },
    { name: "Manguera de impulsión", at: [2440, -700, 330], k: "lin", v10: 1.177, txt: "La manguera de 110 mm es el tramo más rápido de la parte presurizada." },
    { name: "Cono difusor", at: [2672, 0, 1000], k: "lin", v10: 0.197, txt: "Se ensancha de 110 a 260 mm: el agua entra al cajón a 0,2 m/s, sin chocar con una pared." },
    { name: "Cajón", at: [2560, 0, ZC + 90], k: "lin", v10: 0.1, txt: "Agua casi quieta con una circulación lenta; ahí se reparte a lo ancho." },
    { name: "Deflector", at: [XV + 252, 0, ZC + 30], k: "lin", v10: 0.29, txt: "Obliga al agua a pasar por debajo, pegada al fondo, y parejiza la corriente." },
    { name: "Rampa de la cresta", at: [XV + 60, 0, ZC + 62], k: "pow", v10: 0.42, e: 0.4, txt: "El agua sube siguiendo la curva y casi no queda agua detenida en la esquina." },
    { name: "Malla de acero", at: [XV - 150, 0, bedAt(XV - 150) + 6], k: "1d", s: 150, txt: "Parte del agua puede escurrirse al sumidero; el drenaje real se medirá en banco." },
    { name: "Tobogán y arco", at: [XV - 620, 0, bedAt(XV - 620) + 6], k: "1d", s: 700, txt: "La lámina se adelgaza y se acelera; el arco la pasa de 12° a 20°." },
    { name: "Ventana de conteo", at: [XV - d.canal.x_conteo, 0, bedAt(XV - d.canal.x_conteo) + 6], k: "1d", s: d.canal.s_conteo, txt: "La cámara mira desde arriba y el backlight infrarrojo ilumina desde abajo." },
    { name: "Embudo", at: [520, 0, 860], k: "lin", v10: 1.2, txt: "El rectángulo del canal se convierte en el círculo de 165 mm de la manguera de salida." },
    { name: "Piscina de destino", at: [-900, 0, 100], k: "none", txt: "Las larvas contadas caen a la piscina de destino, donde se dispersan." },
  ];

  const mesh = model.bodies.map((b) => ({ n: b.n, v: b.v.map((x) => Math.round(x * 10)), t: b.t }));
  const body = `<div class="f1box" style="aspect-ratio:16/10"><canvas class="f1gl" role="img" aria-label="Visor 3D del circuito completo del agua sobre el modelo del prototipo: estanque de origen con bomba, manguera al cono difusor, cajón con deflector y rampa parabólica, malla, canal con ventana de conteo y cámara, embudo y manguera de salida hasta la piscina de destino. Una nube de puntos azules recorre todo el circuito y puntos ámbar marcan grupos de larvas."></canvas><div class="f1ring" hidden></div></div><script type="application/json" id="f1-mesh">${JSON.stringify(mesh)}</script>`;

  const D1 = {
    X0: XV, ZC, ZE, XE,
    bed: { x: bedX, z: bedZ, w: wAt },
    levels: { back: levelBack, front: levelFront, xDefl: XV + 252, xRamp: XV + 115 },
    tracks: out,
    emb: { hh: em.h, r: em.r, p0, dir, boca: em.boca, fin: em.fin },
    pools: { o: { x0: po.x0, x1: po.x1, y0: po.y0, y1: po.y1, z1: 270, cana: rt.canasta }, d: { x0: pd.x0, x1: pd.x1, y0: pd.y0, y1: pd.y1, z1: 110 } },
    stations,
    water: waterVols,
    canal: { s: d.canal.s, x: d.canal.x, s_conteo: d.canal.s_conteo },
    prof: d.perfil1d,
  };
  return { body, D1, stations, ZC, XE, ZE };
}
