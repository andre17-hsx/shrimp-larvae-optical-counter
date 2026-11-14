// Escena con auditoria: cada pieza se dibuja y se registra con su forma real; las claves de pintura salen de la geometria.
import * as k from "./kit/iso-kit.mjs";
import * as G from "./kit/lathe.mjs";
import * as A from "./kit/audit.mjs";
import { profilePrism } from "./lib.mjs";

export function makeScene(P, piece = "m") {
  const R = A.recorder(P);
  const S = (paths, style) => k.solidSvg(paths, style);
  const Y = G.frameOf([0, 0, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]); // eje a = y, u = x, v = z
  const wrap = (svg, glass) => (glass ? `<g class="glass">${svg}</g>` : svg);
  const put = (name, at, svg, shapes, opts = {}) => R.put({ name, at, svg, shapes, piece, ...opts });
  const api = {
    R, S, Y, put,
    slab(name, plan, z, h, style = { tone: "mid" }, { steps = 3, bevel = 0.5, glass = false, extra = "", bias = 0, meta = {} } = {}) {
      const shape = R.solid(A.slab(plan, z, h, { name, ...meta }, steps));
      put(name, [plan.x + plan.w / 2, plan.y + plan.d / 2, z + h / 2], wrap(S(k.slabOf(plan, z, h, P, steps, bevel), style) + extra, glass), [shape], { bias });
      return shape;
    },
    cyl(name, cx, cy, r, z, h, style = { tone: "mid" }, { steps = 28, bevel = 0, glass = false, extra = "", bias = 0, meta = {} } = {}) {
      const shape = R.solid(A.cylinder(cx, cy, r, z, h, { name, ...meta }));
      put(name, [cx, cy, z + h / 2], wrap(S(k.cylinder(cx, cy, r, z, h, P, steps, bevel), style) + extra, glass), [shape], { bias });
      return shape;
    },
    ext(name, ring, z, h, style = { tone: "mid" }, { glass = false, extra = "", bias = 0, at, meta = {} } = {}) {
      const shape = R.solid(A.extruded(ring, z, h, { name, ...meta }));
      const cx = ring.reduce((a, p) => a + p[0], 0) / ring.length;
      const cy = ring.reduce((a, p) => a + p[1], 0) / ring.length;
      put(name, at ?? [cx, cy, z + h / 2], wrap(S(k.extrude(ring, z, h, P, { convex: false }), style) + extra, glass), [shape], { bias });
      return shape;
    },
    /** perfil (x, z) extruido en y de y0 a y1 */
    pris(name, ring, y0, y1, style = { tone: "mid" }, { glass = false, extra = "", bias = 0, at, meta = {} } = {}) {
      const shape = R.solid(A.prism(Y, ring, y0, y1, { name, ...meta }));
      const cx = ring.reduce((a, p) => a + p[0], 0) / ring.length;
      const cz = ring.reduce((a, p) => a + p[1], 0) / ring.length;
      put(name, at ?? [cx, (y0 + y1) / 2, cz], wrap(S(profilePrism(ring, y0, y1, P), style) + extra, glass), [shape], { bias });
      return shape;
    },
    lat(name, F, profile, style = { tone: "mid" }, { glass = false, extra = "", bias = 0, at, meta = {}, options = {} } = {}) {
      const shape = R.solid(A.solid(F, profile, { name, ...meta }));
      const mid = G.pointOf(F, profile[Math.floor(profile.length / 2)][0], 0, 0);
      put(name, at ?? mid, wrap(S(G.solidOf(profile, F, P, options), style) + extra, glass), [shape], { bias });
      return shape;
    },
    /** ordena por clave y devuelve el svg con las ranuras (slots) insertadas despues del ultimo elemento nombrado */
    compose(slots = []) {
      A.settle(R, P);
      R.items.sort((a, b) => a.key - b.key);
      const out = [];
      const index = new Map();
      R.items.forEach((it, i) => index.set(it.name, i));
      const after = new Map();
      for (const s of slots) {
        const at = Math.max(...s.after.map((n) => (index.has(n) ? index.get(n) : -1)));
        if (at < 0) throw new Error("ranura sin elementos: " + s.after.join(","));
        after.set(at, (after.get(at) ?? "") + s.svg);
      }
      R.items.forEach((it, i) => {
        out.push(`<g class="it" data-name="${it.name}">${it.svg}</g>`);
        if (after.has(i)) out.push(after.get(i));
      });
      return out.join("");
    },
  };
  return api;
}

export function runAudit(label, R, P, opts = {}) {
  const result = A.audit(R, P, opts);
  console.log("\n=== " + label + " ===");
  console.log(A.report(result));
  return A.failures(result);
}
