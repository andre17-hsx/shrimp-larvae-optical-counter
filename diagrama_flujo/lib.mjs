// Ayudas de dibujo propias del diagrama: prismas con perfil, caras en un plano, medias piezas de revolucion y superficies del agua.
import * as k from "./kit/iso-kit.mjs";

export const mm = (n) => Math.round(n * 10) / 10;
const SH = 4;

export function viewVec(P) {
  const { sinA, cosA, sinE, cosE } = k.cameraOf(P);
  return [cosA * cosE, sinA * cosE, sinE];
}

const area = (pts) => {
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const [ax, ay] = pts[i];
    const [bx, by] = pts[(i + 1) % pts.length];
    a += ax * by - bx * ay;
  }
  return a / 2;
};
export const ccw = (pts) => (area(pts) < 0 ? [...pts].reverse() : pts);
const poly = (pts) => k.pathOf(ccw(pts), true);

export function shadeOfPlan(nx, ny, P) {
  const { sinA, cosA } = k.cameraOf(P);
  const lit = (nx * -sinA + ny * cosA + 1) / 2;
  return Math.min(SH - 1, Math.max(0, Math.floor(lit * SH)));
}

/** Prisma cuyo perfil esta en el plano (x, z) y se extruye en y de y0 a y1 (y1 mas cerca del espectador).
 *  Devuelve el mismo objeto que `slabOf` para pintarlo con solidSvg. */
export function profilePrism(ring, y0, y1, P) {
  const pts = ccw(ring);
  const n = pts.length;
  const v = viewVec(P);
  const near = pts.map(([x, z]) => k.iso([x, y1, z], P));
  const far = pts.map(([x, z]) => k.iso([x, y0, z], P));
  const norm = pts.map(([ax, az], i) => {
    const [bx, bz] = pts[(i + 1) % n];
    const dx = bx - ax;
    const dz = bz - az;
    const len = Math.hypot(dx, dz) || 1;
    return [dz / len, -dx / len];
  });
  const vis = norm.map(([nx, nz]) => nx * v[0] + nz * v[2] > 1e-6);
  const buckets = Array.from({ length: SH }, () => []);
  const tops = [];
  const parts = [poly(near)];
  const outline = [k.pathOf([...near, near[0]])];
  const crease = [];
  const order = [...Array(n).keys()].filter((i) => vis[i]).sort((a, b) => (pts[a][0] + pts[(a + 1) % n][0]) - (pts[b][0] + pts[(b + 1) % n][0]));
  for (const i of order) {
    const j = (i + 1) % n;
    const quad = poly([far[i], far[j], near[j], near[i]]);
    parts.push(quad);
    const [nx, nz] = norm[i];
    if (nz > 0.55) tops.push(quad);
    else buckets[shadeOfPlan(nx, 0, P)].push(quad);
    outline.push(k.pathOf([far[i], far[j]]));
  }
  buckets[shadeOfPlan(0, 1, P)].push(poly(near));
  for (let i = 0; i < n; i++) {
    const prev = (i + n - 1) % n;
    if (vis[prev] !== vis[i]) outline.push(k.pathOf([near[i], far[i]]));
    else if (vis[i]) {
      const dot = norm[prev][0] * norm[i][0] + norm[prev][1] * norm[i][1];
      if (dot < 0.9) crease.push(k.pathOf([near[i], far[i]]));
    }
  }
  return { fill: parts.join(""), outline: outline.join(""), crease: crease.join(""), top: tops.join(""), shades: buckets.map((b) => b.join("")) };
}

/** Prisma con perfil en el plano (y, z) extruido en x de x0 a x1 (x1 mas cerca). */
export function profilePrismX(ring, x0, x1, P) {
  const pts = ccw(ring);
  const n = pts.length;
  const v = viewVec(P);
  const near = pts.map(([y, z]) => k.iso([x1, y, z], P));
  const far = pts.map(([y, z]) => k.iso([x0, y, z], P));
  const norm = pts.map(([ay, az], i) => {
    const [by, bz] = pts[(i + 1) % n];
    const dy = by - ay;
    const dz = bz - az;
    const len = Math.hypot(dy, dz) || 1;
    return [dz / len, -dy / len];
  });
  const vis = norm.map(([ny, nz]) => ny * v[1] + nz * v[2] > 1e-6);
  const buckets = Array.from({ length: SH }, () => []);
  const tops = [];
  const parts = [poly(near)];
  const outline = [k.pathOf([...near, near[0]])];
  const crease = [];
  const order = [...Array(n).keys()].filter((i) => vis[i]).sort((a, b) => (pts[a][0] + pts[(a + 1) % n][0]) - (pts[b][0] + pts[(b + 1) % n][0]));
  for (const i of order) {
    const j = (i + 1) % n;
    const quad = poly([far[i], far[j], near[j], near[i]]);
    parts.push(quad);
    const [ny, nz] = norm[i];
    if (nz > 0.55) tops.push(quad);
    else buckets[shadeOfPlan(0, ny, P)].push(quad);
    outline.push(k.pathOf([far[i], far[j]]));
  }
  buckets[shadeOfPlan(1, 0, P)].push(poly(near));
  for (let i = 0; i < n; i++) {
    const prev = (i + n - 1) % n;
    if (vis[prev] !== vis[i]) outline.push(k.pathOf([near[i], far[i]]));
  }
  return { fill: parts.join(""), outline: outline.join(""), crease: crease.join(""), top: tops.join(""), shades: buckets.map((b) => b.join("")) };
}

/** Una cara plana en el plano y = cte con puntos (x, z). */
export const faceXZ = (pts, y, P) => k.pathOf(pts.map(([x, z]) => k.iso([x, y, z], P)), true);
/** Cara en el plano x = cte con puntos (y, z). */
export const faceYZ = (pts, x, P) => k.pathOf(pts.map(([y, z]) => k.iso([x, y, z], P)), true);
/** Cara horizontal a z = cte con puntos (x, y). */
export const faceXY = (pts, z, P) => k.pathOf(pts.map(([x, y]) => k.iso([x, y, z], P)), true);

/** Superficie de agua: tiras entre dos bordes a y = ya(x) y y = yb(x), a la altura z(x). Devuelve un trazado por tira con un tono. */
export function waterTop(xs, zs, ya, yb, P) {
  const out = [];
  for (let i = 0; i < xs.length - 1; i++) {
    const quad = [
      k.iso([xs[i], ya(xs[i]), zs[i]], P),
      k.iso([xs[i], yb(xs[i]), zs[i]], P),
      k.iso([xs[i + 1], yb(xs[i + 1]), zs[i + 1]], P),
      k.iso([xs[i + 1], ya(xs[i + 1]), zs[i + 1]], P),
    ];
    const slope = (zs[i + 1] - zs[i]) / Math.max(1e-6, xs[i + 1] - xs[i]);
    out.push({ d: k.pathOf(quad, true), slope, x: xs[i] });
  }
  return out;
}

/** Media pieza de revolucion alrededor de un eje vertical en (cx, cy): la mitad con y <= cy vista por dentro, y su seccion en y = cy.
 *  profile = [[r, z], ...] de arriba a abajo. */
export function halfRevolveZ(profile, cx, cy, P, steps = 28) {
  const faces = [];
  const ang = (i) => -Math.PI / 2 - (Math.PI * i) / steps; // de y negativo hacia ... recorre la mitad y <= cy
  const at = (r, z, a) => [cx + r * Math.cos(a + Math.PI / 2 + Math.PI / 2 - Math.PI / 2), cy + r * Math.sin(a), z];
  void at;
  const pt = (r, z, t) => [cx + r * Math.cos(Math.PI + t * Math.PI), cy + r * Math.sin(Math.PI + t * Math.PI), z]; // t de 0 a 1: de x- pasando por y- a x+
  for (let s = 0; s < profile.length - 1; s++) {
    for (let i = 0; i < steps; i++) {
      const t0 = i / steps;
      const t1 = (i + 1) / steps;
      const q = [pt(profile[s][0], profile[s][1], t0), pt(profile[s][0], profile[s][1], t1), pt(profile[s + 1][0], profile[s + 1][1], t1), pt(profile[s + 1][0], profile[s + 1][1], t0)];
      const tm = (t0 + t1) / 2;
      const nx = -Math.cos(Math.PI + tm * Math.PI);
      const ny = -Math.sin(Math.PI + tm * Math.PI);
      faces.push({ d: k.pathOf(q.map((p3) => k.iso(p3, P)), true), shade: shadeOfPlan(nx, ny, P), depth: q.reduce((a, p3) => a + k.depthOf(p3, P), 0) / 4 });
    }
  }
  faces.sort((a, b) => a.depth - b.depth);
  const section = [];
  for (const [r, z] of profile) section.push([cx - r, z]);
  for (const [r, z] of [...profile].reverse()) section.push([cx + r, z]);
  return { faces, section: faceXZ(section, cy, P) };
}

export function shadeFaces(faces, tone = "mid") {
  const groups = Array.from({ length: SH }, () => []);
  for (const f of faces) groups[f.shade].push(f.d);
  return groups.map((g, i) => (g.length ? `<path class="iso-shade" data-shade="${i}" d="${g.join("")}"/>` : "")).join("");
}
