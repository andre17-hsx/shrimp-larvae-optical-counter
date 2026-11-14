// Rasterizador por software de las mallas reales del modelo (z-buffer, sombreado suave, aristas) para la Figura 1.
// Entrega tres capas por tema: base (cuerpos opacos + agua quieta), vidrio (acrilico y mangueras translucidas) y un mapa de
// profundidad de lo opaco para que las particulas de la capa viva queden tapadas por lo que tienen delante.
import zlib from "node:zlib";
import * as k from "./kit/iso-kit.mjs";

const X0 = 2090; // x' = X0 - X deja el vertedero en x'=0 y la corriente hacia +x' (vista no espejada)
export const toView = ([X, Y, Z]) => [X0 - X, Y, Z];

// ---------------------------------------------------------------- PNG
const CRC = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let i = 0; i < 8; i++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
const crc32 = (buf) => {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 255] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};
const chunk = (type, data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td));
  return Buffer.concat([len, td, crc]);
};
export function pngEncode(w, h, px, ch = 4) {
  const stride = w * ch;
  const out = Buffer.alloc((stride + 1) * h);
  const cand = [Buffer.alloc(stride), Buffer.alloc(stride), Buffer.alloc(stride)];
  for (let y = 0; y < h; y++) {
    let best = 0;
    let bestSum = Infinity;
    for (let f = 0; f < 3; f++) {
      let sum = 0;
      for (let i = 0; i < stride; i++) {
        const cur = px[y * stride + i];
        const left = i >= ch ? px[y * stride + i - ch] : 0;
        const up = y ? px[(y - 1) * stride + i] : 0;
        const v = (cur - (f === 0 ? 0 : f === 1 ? left : up)) & 255;
        cand[f][i] = v;
        sum += v < 128 ? v : 256 - v;
      }
      if (sum < bestSum) {
        bestSum = sum;
        best = f;
      }
    }
    out[y * (stride + 1)] = best;
    cand[best].copy(out, y * (stride + 1) + 1);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = ch === 4 ? 6 : 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr), chunk("IDAT", zlib.deflateSync(out, { level: 9 })), chunk("IEND", Buffer.alloc(0))]);
}

// ---------------------------------------------------------------- clasificacion de cuerpos
export function classify(b) {
  const n = b.n;
  if (/^(lateral_tobogan|tapa_tobogan|vidrio_protector|PROPUESTA_ventana|pared_lateral|pared_trasera|cubierta|pared_estrechamiento|sumidero_pared|deflector|tapa_sensor|PROPUESTA_piscina_paredes|PROPUESTA_piscina_destino_paredes)/.test(n)) return "glass";
  if (/^(difusor|tubo_drenaje|embudo|acople_salida|PROPUESTA_manguera|PROPUESTA_tuberia)/.test(n)) return "pipe";
  if (/^vertedero_rampa|^malla_cedazo/.test(n)) return "subject";
  if (/^neumatico/.test(n)) return "tire";
  if (/^(fondo|PROPUESTA_piscina_fondo|PROPUESTA_piscina_destino_fondo|sumidero_fondo)/.test(n)) return "floor";
  return "struct";
}

const PAL = {
  dark: {
    struct: [[34, 37, 42], [150, 157, 168]], tire: [[16, 17, 19], [66, 68, 73]], floor: [[30, 33, 38], [118, 125, 135]],
    subject: [[110, 110, 112], [248, 248, 246]], glass: [150, 190, 210], pipe: [[70, 82, 94], [172, 188, 204]],
    line: [214, 220, 228], water: [60, 168, 196],
  },
  light: {
    struct: [[148, 150, 155], [243, 243, 239]], tire: [[58, 58, 62], [122, 124, 129]], floor: [[168, 170, 174], [238, 238, 234]],
    subject: [[16, 16, 18], [88, 90, 94]], glass: [60, 110, 135], pipe: [[110, 124, 138], [214, 224, 232]],
    line: [26, 28, 32], water: [10, 126, 156],
  },
};

// ---------------------------------------------------------------- malla: normales suaves y aristas
function prepare(body, V) {
  const v = body.v;
  const nv = v.length / 3;
  const pts = new Float64Array(nv * 3);
  for (let i = 0; i < nv; i++) {
    const q = toView([v[i * 3], v[i * 3 + 1], v[i * 3 + 2]]);
    pts.set(q, i * 3);
  }
  const t = body.t;
  const nt = t.length / 3;
  const fn = new Float64Array(nt * 3);
  const fa = new Float64Array(nt);
  for (let f = 0; f < nt; f++) {
    const [a, b, c] = [t[f * 3], t[f * 3 + 1], t[f * 3 + 2]];
    const ux = pts[b * 3] - pts[a * 3], uy = pts[b * 3 + 1] - pts[a * 3 + 1], uz = pts[b * 3 + 2] - pts[a * 3 + 2];
    const wx = pts[c * 3] - pts[a * 3], wy = pts[c * 3 + 1] - pts[a * 3 + 1], wz = pts[c * 3 + 2] - pts[a * 3 + 2];
    let nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx;
    const l = Math.hypot(nx, ny, nz) || 1;
    nx /= l; ny /= l; nz /= l;
    if (nx * V[0] + ny * V[1] + nz * V[2] < 0) { nx = -nx; ny = -ny; nz = -nz; }
    fn[f * 3] = nx; fn[f * 3 + 1] = ny; fn[f * 3 + 2] = nz;
    fa[f] = l;
  }
  // soldar vertices por posicion
  const key = (i) => Math.round(pts[i * 3] * 4) + "," + Math.round(pts[i * 3 + 1] * 4) + "," + Math.round(pts[i * 3 + 2] * 4);
  const weld = new Int32Array(nv);
  const map = new Map();
  for (let i = 0; i < nv; i++) {
    const kk = key(i);
    if (!map.has(kk)) map.set(kk, map.size);
    weld[i] = map.get(kk);
  }
  const inc = Array.from({ length: map.size }, () => []);
  for (let f = 0; f < nt; f++) for (let c = 0; c < 3; c++) inc[weld[t[f * 3 + c]]].push(f);
  const cs = Math.cos((42 * Math.PI) / 180);
  const cn = new Float32Array(nt * 9);
  for (let f = 0; f < nt; f++) {
    for (let c = 0; c < 3; c++) {
      const w = weld[t[f * 3 + c]];
      let sx = 0, sy = 0, sz = 0;
      for (const g of inc[w]) {
        const d = fn[g * 3] * fn[f * 3] + fn[g * 3 + 1] * fn[f * 3 + 1] + fn[g * 3 + 2] * fn[f * 3 + 2];
        if (d > cs) { sx += fn[g * 3] * fa[g]; sy += fn[g * 3 + 1] * fa[g]; sz += fn[g * 3 + 2] * fa[g]; }
      }
      const l = Math.hypot(sx, sy, sz) || 1;
      cn[f * 9 + c * 3] = sx / l; cn[f * 9 + c * 3 + 1] = sy / l; cn[f * 9 + c * 3 + 2] = sz / l;
    }
  }
  // aristas de rasgo: borde libre o diedro grande
  const em = new Map();
  for (let f = 0; f < nt; f++) for (let c = 0; c < 3; c++) {
    const a = weld[t[f * 3 + c]], b = weld[t[f * 3 + ((c + 1) % 3)]];
    if (a === b) continue;
    const kk = a < b ? a + "_" + b : b + "_" + a;
    const e = em.get(kk);
    if (e) e.faces.push(f);
    else em.set(kk, { faces: [f], a: t[f * 3 + c], b: t[f * 3 + ((c + 1) % 3)] });
  }
  const edges = [];
  const ce = Math.cos((46 * Math.PI) / 180);
  // el diedro se mide con la normal geometrica sin voltear hacia la camara
  const raw = (f) => {
    const [a, b, c] = [t[f * 3], t[f * 3 + 1], t[f * 3 + 2]];
    const ux = pts[b * 3] - pts[a * 3], uy = pts[b * 3 + 1] - pts[a * 3 + 1], uz = pts[b * 3 + 2] - pts[a * 3 + 2];
    const wx = pts[c * 3] - pts[a * 3], wy = pts[c * 3 + 1] - pts[a * 3 + 1], wz = pts[c * 3 + 2] - pts[a * 3 + 2];
    const nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx;
    const l = Math.hypot(nx, ny, nz) || 1;
    if (l < 0.08 * Math.hypot(ux, uy, uz) * Math.hypot(wx, wy, wz)) return null;
    return [nx / l, ny / l, nz / l];
  };
  for (const e of em.values()) {
    let keep = e.faces.length === 1;
    if (e.faces.length === 2) {
      const n1 = raw(e.faces[0]);
      const n2 = raw(e.faces[1]);
      keep = !!n1 && !!n2 && Math.abs(n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2]) < ce;
    }
    if (keep) edges.push([e.a, e.b]);
  }
  return { pts, t, nt, fn, cn, edges, nv };
}

// ---------------------------------------------------------------- lienzo
class Canvas {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.rgb = new Float32Array(w * h * 3); // premultiplicado
    this.a = new Float32Array(w * h);
  }
  over(i, r, g, b, al) {
    const k3 = i * 3;
    const ia = 1 - al;
    this.rgb[k3] = r * al + this.rgb[k3] * ia;
    this.rgb[k3 + 1] = g * al + this.rgb[k3 + 1] * ia;
    this.rgb[k3 + 2] = b * al + this.rgb[k3 + 2] * ia;
    this.a[i] = al + this.a[i] * ia;
  }
  png() {
    const px = Buffer.alloc(this.w * this.h * 4);
    for (let i = 0; i < this.w * this.h; i++) {
      const a = this.a[i];
      if (a > 0.002) {
        px[i * 4] = Math.min(255, Math.round(this.rgb[i * 3] / a));
        px[i * 4 + 1] = Math.min(255, Math.round(this.rgb[i * 3 + 1] / a));
        px[i * 4 + 2] = Math.min(255, Math.round(this.rgb[i * 3 + 2] / a));
        px[i * 4 + 3] = Math.min(255, Math.round(a * 255));
      }
    }
    return pngEncode(this.w, this.h, px, 4);
  }
}

export function makeRenderer(model, P, W, H, S) {
  const w = W * S;
  const h = H * S;
  const cam = (p) => {
    const [sx, sy] = k.iso(p, P);
    return [sx * S, sy * S, k.depthOf(p, P)];
  };
  const toward = k.towardViewer(P);
  const sE = Math.sin((P.elevation * Math.PI) / 180);
  const cE = Math.cos((P.elevation * Math.PI) / 180);
  const V = [toward[0] * cE, toward[1] * cE, sE]; // hacia la camara
  const Lraw = [-0.45, 0.55, 0.85];
  const Ll = Math.hypot(...Lraw);
  const L = Lraw.map((v) => v / Ll);
  const bodies = model.bodies.map((b) => ({ ...b, kind: classify(b) }));
  const prep = bodies.map((b) => prepare(b, V));
  const projected = prep.map((p) => {
    const sp = new Float64Array(p.nv * 3);
    for (let i = 0; i < p.nv; i++) {
      const [x, y, d] = cam([p.pts[i * 3], p.pts[i * 3 + 1], p.pts[i * 3 + 2]]);
      sp[i * 3] = x; sp[i * 3 + 1] = y; sp[i * 3 + 2] = d;
    }
    return sp;
  });
  const shade = (n) => Math.max(0, Math.min(1, 0.48 + 0.52 * (n[0] * L[0] + n[1] * L[1] + n[2] * L[2])));

  // ---- pasada opaca: z-buffer
  const depth = new Float32Array(w * h).fill(-1e9);
  const ids = new Int32Array(w * h).fill(-1);
  const inten = new Float32Array(w * h);
  const kindAt = new Uint8Array(w * h);
  const kinds = ["struct", "tire", "floor", "subject"];
  function fillTri(sp, tri, cn, f, bodyId, kindIdx) {
    const a = tri[0], b = tri[1], c = tri[2];
    const x0 = sp[a * 3], y0 = sp[a * 3 + 1], d0 = sp[a * 3 + 2];
    const x1 = sp[b * 3], y1 = sp[b * 3 + 1], d1 = sp[b * 3 + 2];
    const x2 = sp[c * 3], y2 = sp[c * 3 + 1], d2 = sp[c * 3 + 2];
    const den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2);
    if (Math.abs(den) < 1e-9) return;
    const minx = Math.max(0, Math.floor(Math.min(x0, x1, x2))), maxx = Math.min(w - 1, Math.ceil(Math.max(x0, x1, x2)));
    const miny = Math.max(0, Math.floor(Math.min(y0, y1, y2))), maxy = Math.min(h - 1, Math.ceil(Math.max(y0, y1, y2)));
    const i0 = shade([cn[f * 9], cn[f * 9 + 1], cn[f * 9 + 2]]);
    const i1 = shade([cn[f * 9 + 3], cn[f * 9 + 4], cn[f * 9 + 5]]);
    const i2 = shade([cn[f * 9 + 6], cn[f * 9 + 7], cn[f * 9 + 8]]);
    for (let y = miny; y <= maxy; y++) {
      for (let x = minx; x <= maxx; x++) {
        const px = x + 0.5, py = y + 0.5;
        const l0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / den;
        const l1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / den;
        const l2 = 1 - l0 - l1;
        if (l0 < -1e-4 || l1 < -1e-4 || l2 < -1e-4) continue;
        const dd = l0 * d0 + l1 * d1 + l2 * d2;
        const i = y * w + x;
        if (dd > depth[i]) {
          depth[i] = dd;
          ids[i] = bodyId;
          inten[i] = l0 * i0 + l1 * i1 + l2 * i2;
          kindAt[i] = kindIdx;
        }
      }
    }
  }
  bodies.forEach((b, bi) => {
    if (b.kind === "glass" || b.kind === "pipe") return;
    const p = prep[bi];
    const ki = kinds.indexOf(b.kind);
    for (let f = 0; f < p.nt; f++) fillTri(projected[bi], [p.t[f * 3], p.t[f * 3 + 1], p.t[f * 3 + 2]], p.cn, f, bi, ki);
  });

  // ---- lineas con prueba de profundidad
  function lineTo(canvas, x0, y0, d0, x1, y1, d1, col, al, width, tol, useDepth) {
    const n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0)));
    for (let s = 0; s <= n; s++) {
      const t = s / n;
      const x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t, d = d0 + (d1 - d0) * t;
      for (let oy = 0; oy < width; oy++) for (let ox = 0; ox < width; ox++) {
        const xi = Math.round(x) + ox - (width >> 1), yi = Math.round(y) + oy - (width >> 1);
        if (xi < 0 || yi < 0 || xi >= w || yi >= h) continue;
        const i = yi * w + xi;
        if (useDepth && d < depth[i] - tol) continue;
        canvas.over(i, col[0], col[1], col[2], al);
      }
    }
  }

  // ---- agua quieta: volumenes translucidos, listados de lejos a cerca
  function waterFaces(vols) {
    const tris = [];
    for (const vol of vols) for (const q of vol.quads) {
      const pts = q.map((p) => cam(toView(p)));
      const cx = (pts[0][2] + pts[1][2] + pts[2][2] + pts[3][2]) / 4;
      tris.push({ pts, d: cx, top: q.top, vol });
    }
    tris.sort((a, b) => a.d - b.d);
    return tris;
  }
  function blendPoly(canvas, pts, col, al, dtest, tol) {
    const [a, b, c, d] = pts;
    for (const tri of [[a, b, c], [a, c, d]]) {
      const [p0, p1, p2] = tri;
      const den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1]);
      if (Math.abs(den) < 1e-9) continue;
      const minx = Math.max(0, Math.floor(Math.min(p0[0], p1[0], p2[0]))), maxx = Math.min(w - 1, Math.ceil(Math.max(p0[0], p1[0], p2[0])));
      const miny = Math.max(0, Math.floor(Math.min(p0[1], p1[1], p2[1]))), maxy = Math.min(h - 1, Math.ceil(Math.max(p0[1], p1[1], p2[1])));
      for (let y = miny; y <= maxy; y++) for (let x = minx; x <= maxx; x++) {
        const px = x + 0.5, py = y + 0.5;
        const l0 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) / den;
        const l1 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) / den;
        const l2 = 1 - l0 - l1;
        if (l0 < -1e-4 || l1 < -1e-4 || l2 < -1e-4) continue;
        const dd = l0 * p0[2] + l1 * p1[2] + l2 * p2[2];
        const i = y * w + x;
        if (dtest && dd < depth[i] - tol) continue;
        canvas.over(i, col[0], col[1], col[2], al);
      }
    }
  }

  function renderTheme(theme, waterVols) {
    const pal = PAL[theme];
    const base = new Canvas(w, h);
    // opacos
    for (let i = 0; i < w * h; i++) {
      if (ids[i] < 0) continue;
      const [sh, li] = pal[kinds[kindAt[i]]];
      const t = inten[i];
      base.rgb[i * 3] = sh[0] + (li[0] - sh[0]) * t;
      base.rgb[i * 3 + 1] = sh[1] + (li[1] - sh[1]) * t;
      base.rgb[i * 3 + 2] = sh[2] + (li[2] - sh[2]) * t;
      base.a[i] = 1;
    }
    // siluetas por cambio de cuerpo o salto de profundidad
    const sil = new Uint8Array(w * h);
    for (let y = 0; y < h - 1; y++) for (let x = 0; x < w - 1; x++) {
      const i = y * w + x;
      for (const j of [i + 1, i + w]) {
        const a = ids[i], b = ids[j];
        if (a < 0 && b < 0) continue;
        if (a !== b || Math.abs(depth[i] - depth[j]) > 22) {
          const near = a < 0 ? j : b < 0 ? i : depth[i] >= depth[j] ? i : j;
          sil[near] = 1;
        }
      }
    }
    const lc = pal.line;
    for (let i = 0; i < w * h; i++) if (sil[i]) for (const j of [i, i + 1, i + w]) if (j < w * h) base.over(j, lc[0], lc[1], lc[2], 0.62);
    // aristas de rasgo de los cuerpos opacos
    bodies.forEach((b, bi) => {
      if (b.kind === "glass" || b.kind === "pipe") return;
      const sp = projected[bi];
      for (const [a, c] of prep[bi].edges) lineTo(base, sp[a * 3], sp[a * 3 + 1], sp[a * 3 + 2], sp[c * 3], sp[c * 3 + 1], sp[c * 3 + 2], lc, 0.5, 2, 7, true);
    });
    // agua quieta
    const wc = pal.water;
    for (const f of waterFaces(waterVols)) blendPoly(base, f.pts, wc, f.top ? 0.3 : 0.2, true, 4);
    // mangueras (sobre el agua, bajo los puntos) y vidrio (sobre los puntos): translucidos, de lejos a cerca
    const glass = new Canvas(w, h);
    const pass = (canvas, kind) => {
      const tris = [];
      bodies.forEach((b, bi) => {
        if (b.kind !== kind) return;
        const p = prep[bi];
        const sp = projected[bi];
        for (let f = 0; f < p.nt; f++) {
          const a = p.t[f * 3], bb = p.t[f * 3 + 1], c = p.t[f * 3 + 2];
          tris.push({ bi, f, a, b: bb, c, d: (sp[a * 3 + 2] + sp[bb * 3 + 2] + sp[c * 3 + 2]) / 3 });
        }
      });
      tris.sort((u, v) => u.d - v.d);
      for (const t of tris) {
        const p = prep[t.bi];
        const sp = projected[t.bi];
        const f = t.f;
        const pv = (j) => [sp[j * 3], sp[j * 3 + 1], sp[j * 3 + 2]];
        let col;
        let al;
        if (kind === "pipe") {
          const [sh, li] = pal.pipe;
          const it = shade([p.cn[f * 9], p.cn[f * 9 + 1], p.cn[f * 9 + 2]]);
          col = [sh[0] + (li[0] - sh[0]) * it, sh[1] + (li[1] - sh[1]) * it, sh[2] + (li[2] - sh[2]) * it];
          al = 0.5;
        } else {
          col = pal.glass;
          const facing = Math.abs(p.fn[f * 3] * V[0] + p.fn[f * 3 + 1] * V[1] + p.fn[f * 3 + 2] * V[2]);
          al = 0.05 + 0.11 * (1 - facing);
        }
        const v2 = pv(t.c);
        blendPoly(canvas, [pv(t.a), pv(t.b), v2, v2], col, al, true, 4);
      }
      bodies.forEach((b, bi) => {
        if (b.kind !== kind) return;
        const sp = projected[bi];
        for (const [a, c] of prep[bi].edges) lineTo(canvas, sp[a * 3], sp[a * 3 + 1], sp[a * 3 + 2], sp[c * 3], sp[c * 3 + 1], sp[c * 3 + 2], kind === "pipe" ? lc : pal.glass, kind === "pipe" ? 0.5 : 0.7, 2, 7, true);
      });
    };
    pass(base, "pipe");
    pass(glass, "glass");
    return { base: base.png(), glass: glass.png() };
  }

  // ---- profundidad para la capa viva: 16 bits en (R,G), a escala 1x
  function depthPng() {
    let lo = Infinity;
    let hi = -Infinity;
    for (let i = 0; i < w * h; i++) if (depth[i] > -1e8) {
      lo = Math.min(lo, depth[i]);
      hi = Math.max(hi, depth[i]);
    }
    const px = Buffer.alloc(W * H * 3);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      let m = -1e9;
      for (let oy = 0; oy < S; oy++) for (let ox = 0; ox < S; ox++) m = Math.max(m, depth[(y * S + oy) * w + x * S + ox]);
      const q = m < -1e8 ? 0 : 1 + Math.round(((m - lo) / (hi - lo)) * 65533);
      px[(y * W + x) * 3] = q >> 8;
      px[(y * W + x) * 3 + 1] = q & 255;
    }
    return { png: pngEncode(W, H, px, 3), lo, hi };
  }

  // alturas de la superficie superior a lo largo de una recta vertical (para el lecho real)
  function topZ(names, X, Y) {
    let best = -Infinity;
    bodies.forEach((b, bi) => {
      if (!names.some((n) => b.n === n || b.n.startsWith(n))) return;
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
    });
    return best;
  }
  return { renderTheme, depthPng, topZ, cam, w, h, bodies };
}
