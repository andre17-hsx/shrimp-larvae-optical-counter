// Figura 1 en vivo: visor 3D (three.js) del modelo real del prototipo con un "mar" de puntos que recorre todo el circuito.
// Se puede girar, mover y acercar libremente. Coordenadas del modelo: las de Fusion (mm), Z hacia arriba.
(function () {
  const root = document.getElementById("fig1");
  if (!root || !window.THREE) return;
  const THREE = window.THREE;
  const box = root.querySelector(".f1box");
  const canvas = box.querySelector("canvas.f1gl");
  const ring = box.querySelector(".f1ring");
  const readout = root.querySelector("[data-readout]");
  const D = DATA.f1;
  const X0 = D.X0;
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  const qIn = root.querySelector("input[data-q]");
  const cIn = root.querySelector("input[data-conc]");
  const sIn = root.querySelector("input[data-speed]");
  const playBtn = root.querySelector("button[data-play]");
  const tbody = root.querySelector("[data-stations]");
  const app = root.closest(".iso");

  // ----- perfil 1D por caudal -----
  const qs = Object.keys(D.prof).map(Number).sort((a, b) => a - b);
  const interpIdx = (arr, v) => {
    let lo = 0;
    let hi = arr.length - 1;
    if (v <= arr[0]) return [0, 0, 0];
    if (v >= arr[hi]) return [hi, hi, 0];
    while (hi - lo > 1) {
      const m = (lo + hi) >> 1;
      if (arr[m] <= v) lo = m;
      else hi = m;
    }
    return [lo, hi, (v - arr[lo]) / (arr[hi] - arr[lo])];
  };
  const prof = (Q, key, s) => {
    let a = 0;
    let b = qs.length - 1;
    for (let i = 0; i < qs.length - 1; i++) if (Q >= qs[i] && Q <= qs[i + 1]) {
      a = i;
      b = i + 1;
    }
    if (Q < qs[0]) a = b = 0;
    if (Q > qs[qs.length - 1]) a = b = qs.length - 1;
    const f = a === b ? 0 : (Q - qs[a]) / (qs[b] - qs[a]);
    const val = (qq) => {
      const p = D.prof[qq];
      const [i, j, t] = interpIdx(p.s, s);
      return p[key][i] + (p[key][j] - p[key][i]) * t;
    };
    return val(qs[a]) + (val(qs[b]) - val(qs[a])) * f;
  };
  const sOfX = (x) => {
    const [i, j, t] = interpIdx(D.canal.x, x);
    return D.canal.s[i] + (D.canal.s[j] - D.canal.s[i]) * t;
  };

  let Q = +qIn.value;
  let conc = +cIn.value;
  let speed = 1;
  let paused = false;
  const nrm = () => Math.random() + Math.random() + Math.random() - 1.5;

  // ----- trayectos: estaciones [cx,cy,cz, e1(3), e2(3), A, B, m, f] -----
  const NF = 13;
  function makeTrack(name, kind, st) {
    const n = st.length;
    const arr = new Float32Array(n * NF);
    for (let i = 0; i < n; i++) for (let j = 0; j < NF; j++) arr[i * NF + j] = st[i][j];
    const cum = new Float32Array(n);
    for (let i = 1; i < n; i++) cum[i] = cum[i - 1] + Math.hypot(arr[i * NF] - arr[(i - 1) * NF], arr[i * NF + 1] - arr[(i - 1) * NF + 1], arr[i * NF + 2] - arr[(i - 1) * NF + 2]);
    return { name, kind, n, arr, cum, total: cum[n - 1], f0: 0.15 };
  }
  const TRK = {};
  for (const [name, t] of Object.entries(D.tracks)) TRK[name] = makeTrack(name, name === "embudo" ? "emb" : name, t.st);

  // lamina del cajon, rampa y canal: depende del caudal
  const LAM = { n: 0, arr: null, cum: null, total: 0, kind: "lam", X: null, bed: null, top: null, i0: 3 };
  function buildLam() {
    const bx = D.bed.x;
    const bz = D.bed.z;
    const bw = D.bed.w;
    const n = bx.length;
    const i0 = LAM.i0;
    const m = n - i0;
    const arr = new Float32Array(m * NF);
    const X = new Float32Array(m);
    const bed = new Float32Array(m);
    const top = new Float32Array(m);
    const h0 = prof(Q, "h", 1);
    const bedCrest = bz[bx.findIndex((x) => x <= X0)];
    const tc = bedCrest + h0;
    for (let i = 0; i < m; i++) {
      const x = bx[i + i0];
      const b = bz[i + i0];
      let t;
      if (x > D.levels.xDefl) t = D.levels.back;
      else if (x > X0 + 250) t = b + 48;
      else if (x > D.levels.xRamp) t = D.levels.front;
      else if (x > X0) {
        const u = (D.levels.xRamp - x) / (D.levels.xRamp - X0);
        t = tc + (D.levels.front - tc) * (1 - u) * (1 - u);
      } else t = b + prof(Q, "h", Math.max(1, sOfX(X0 - x)));
      t = Math.max(t, b + 3);
      X[i] = x;
      bed[i] = b;
      top[i] = t;
      const o = i * NF;
      arr[o] = x;
      arr[o + 1] = 0;
      arr[o + 2] = (b + t) / 2;
      arr[o + 3] = 0;
      arr[o + 4] = 1;
      arr[o + 5] = 0;
      arr[o + 6] = 0;
      arr[o + 7] = 0;
      arr[o + 8] = 1;
      arr[o + 9] = bw[i + i0];
      arr[o + 10] = (t - b) / 2;
      arr[o + 11] = 0;
      arr[o + 12] = 1;
    }
    const cum = new Float32Array(m);
    for (let i = 1; i < m; i++) cum[i] = cum[i - 1] + Math.hypot(X[i] - X[i - 1], (arr[i * NF + 2] - arr[(i - 1) * NF + 2]));
    LAM.n = m;
    LAM.arr = arr;
    LAM.cum = cum;
    LAM.total = cum[m - 1];
    LAM.X = X;
    LAM.bed = bed;
    LAM.top = top;
    TRK.lam = LAM;
  }

  // posicion en un trayecto: u (mm), a en [-1,1], b en [0,1]; deja el resultado en px, py, pz
  let px = 0;
  let py = 0;
  let pz = 0;
  let gA = 0;
  let gX = 0;
  function place(trk, u, a0, b0) {
    const cum = trk.cum;
    const n = trk.n;
    if (u < 0) u = 0;
    if (u > trk.total) u = trk.total;
    let lo = 0;
    let hi = n - 1;
    while (hi - lo > 1) {
      const m = (lo + hi) >> 1;
      if (cum[m] <= u) lo = m;
      else hi = m;
    }
    const t = cum[hi] > cum[lo] ? (u - cum[lo]) / (cum[hi] - cum[lo]) : 0;
    const A = trk.arr;
    const o = lo * NF;
    const q = hi * NF;
    const g = (j) => A[o + j] + (A[q + j] - A[o + j]) * t;
    const m = g(11);
    let f = g(12);
    if (trk.kind === "emb") f = trk.f0 + (0.55 - trk.f0) * m;
    const v = -1 + 2 * f * b0;
    const ch = 1 + (Math.sqrt(Math.max(0, 1 - v * v)) - 1) * m;
    const ua = a0 * ch * g(9);
    const vb = v * g(10);
    px = g(0) + g(3) * ua + g(6) * vb;
    py = g(1) + g(4) * ua + g(7) * vb;
    pz = g(2) + g(5) * ua + g(8) * vb;
    gA = g(9);
    gX = g(0);
  }

  // velocidades (mm/s) de cada tramo con el caudal
  function speedOn(trk, u) {
    const f = Q / 10;
    switch (trk.kind) {
      case "succion":
      case "impulsion":
        return 1177 * f;
      case "difusor": {
        place(trk, u, 0, 0.5);
        return 1177 * f * (55 / gA) * (55 / gA);
      }
      case "emb":
        return 1500 * Math.sqrt(f);
      case "purga":
        return 260 * f;
      default:
        return 500 * f;
    }
  }
  // para la lamina se necesita la X actual: se calcula por separado, sin buscar en cada punto
  function lamSpeed(X) {
    const f = Q / 10;
    if (X > D.levels.xDefl) return 100 * f;
    if (X > X0 + 250) return 290 * f;
    if (X > D.levels.xRamp) return 130 * f;
    if (X > X0) return 420 * Math.pow(f, 0.4);
    return 1000 * prof(Q, "V", Math.max(1, sOfX(X0 - X)));
  }
  function lamIndexAt(u) {
    const cum = LAM.cum;
    let lo = 0;
    let hi = LAM.n - 1;
    while (hi - lo > 1) {
      const m = (lo + hi) >> 1;
      if (cum[m] <= u) lo = m;
      else hi = m;
    }
    return lo;
  }

  buildLam();

  // ----- poblaciones -----
  const O = D.pools.o;
  const Dp = D.pools.d;
  const CAN = O.cana;
  const FIN = D.emb.fin;
  const DIR = D.emb.dir;
  const G = 9810;
  const mkPop = (n, kind, extra = {}) => ({
    n, kind, u: new Float32Array(n), a: new Float32Array(n), b: new Float32Array(n), x: new Float32Array(n), y: new Float32Array(n), z: new Float32Array(n),
    vx: new Float32Array(n), vy: new Float32Array(n), vz: new Float32Array(n), age: new Float32Array(n), ph: new Float32Array(n), ...extra,
  });
  const pops = [];
  const addTrack = (name, n, seg = null) => {
    const p = mkPop(n, "track", { trk: TRK[name], name, seg, u0: 0, u1: TRK[name].total });
    for (let i = 0; i < n; i++) {
      p.u[i] = Math.random() * TRK[name].total;
      p.a[i] = Math.random() * 2 - 1;
      p.b[i] = Math.random();
      p.ph[i] = Math.random() * 6.28;
    }
    pops.push(p);
    return p;
  };
  const pOrigen = mkPop(7000, "origen");
  const pDest = mkPop(4200, "dest");
  const pFall = mkPop(700, "fall");
  pops.push(pOrigen, pDest, pFall);
  const pSuc = addTrack("succion", 700);
  const pImp = addTrack("impulsion", 1500);
  const pDif = addTrack("difusor", 800);
  const lamPops = [addTrack("lam", 3700, [Infinity, D.levels.xDefl]), addTrack("lam", 750, [D.levels.xDefl, D.levels.xRamp]), addTrack("lam", 630, [D.levels.xRamp, X0]), addTrack("lam", 6900, [X0, -Infinity])];
  const pLam = lamPops[3];
  function segBounds() {
    for (const p of lamPops) {
      const first = LAM.X.findIndex((x) => x <= p.seg[0]);
      let last = LAM.X.length - 1;
      for (let i = 0; i < LAM.X.length; i++) if (LAM.X[i] < p.seg[1]) {
        last = i;
        break;
      }
      p.u0 = LAM.cum[Math.max(0, first)];
      p.u1 = LAM.cum[last];
    }
    for (const p of lamPops) if (!p.init) {
      p.init = true;
      for (let i = 0; i < p.n; i++) p.u[i] = p.u0 + Math.random() * (p.u1 - p.u0);
    }
  }
  segBounds();
  const pEmb = addTrack("embudo", 2200);
  const pPur = addTrack("purga", 220);
  let impact = [FIN[0], 0];
  function resetOrigen(p, i, any) {
    p.x[i] = O.x0 + 12 + Math.random() * (O.x1 - O.x0 - 24);
    p.y[i] = O.y0 + 12 + Math.random() * (O.y1 - O.y0 - 24);
    p.z[i] = 10 + Math.random() * (O.z1 - 14);
    p.age[i] = 0;
    void any;
  }
  for (let i = 0; i < pOrigen.n; i++) resetOrigen(pOrigen, i);
  function resetDest(p, i, near) {
    if (near) {
      p.x[i] = impact[0] + nrm() * 90;
      p.y[i] = nrm() * 90;
      p.z[i] = 40 + Math.random() * 70;
    } else {
      p.x[i] = Dp.x0 + 12 + Math.random() * (Dp.x1 - Dp.x0 - 24);
      p.y[i] = Dp.y0 + 12 + Math.random() * (Dp.y1 - Dp.y0 - 24);
      p.z[i] = 8 + Math.random() * (Dp.z1 - 10);
    }
    p.age[i] = near ? 0 : Math.random() * 14;
  }
  for (let i = 0; i < pDest.n; i++) resetDest(pDest, i, false);
  function resetFall(p, i) {
    place(TRK.embudo, TRK.embudo.total, Math.random() * 2 - 1, Math.random());
    const v = 1300 * Math.sqrt(Q / 10) * (0.85 + 0.3 * Math.random());
    p.x[i] = px;
    p.y[i] = py;
    p.z[i] = pz;
    p.vx[i] = DIR[0] * v + nrm() * 40;
    p.vy[i] = nrm() * 40;
    p.vz[i] = DIR[2] * v;
  }
  for (let i = 0; i < pFall.n; i++) {
    resetFall(pFall, i);
    const t0 = Math.random() * 0.25;
    pFall.x[i] += pFall.vx[i] * t0;
    pFall.z[i] += pFall.vz[i] * t0 - 0.5 * G * t0 * t0;
    pFall.vz[i] -= G * t0;
  }
  function findImpact() {
    const v = 1300 * Math.sqrt(Q / 10);
    let t = 0;
    let x = FIN[0];
    let z = FIN[2];
    let vz = DIR[2] * v;
    const dt = 0.002;
    while (z > Dp.z1 + 2 && t < 2) {
      x += DIR[0] * v * dt;
      z += vz * dt;
      vz -= G * dt;
      t += dt;
    }
    impact = [x, 0];
  }

  // grupos de larvas: recorren todo el circuito, del estanque al estanque
  let larvae = [];
  const STAGES = ["pool", "succion", "impulsion", "difusor", "lam", "embudo", "fall", "dest"];
  function newLarvae() {
    const n = Math.max(8, Math.round(conc * 14));
    larvae = [];
    for (let i = 0; i < n; i++) {
      const L = { st: 0, u: 0, a: Math.random() * 2 - 1, b: Math.random(), x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, t: 0 };
      toStage(L, Math.floor(Math.random() * STAGES.length));
      if (L.st >= 1 && L.st <= 5) L.u = Math.random() * TRK[STAGES[L.st]].total * 0.98;
      else if (L.st === 0) L.t = Math.random() * 0.9;
      larvae.push(L);
    }
  }
  function toStage(L, st) {
    L.st = st;
    L.u = 0;
    L.t = 0;
    if (st === 0) {
      L.x = O.x0 + 40 + Math.random() * (O.x1 - O.x0 - 80);
      L.y = O.y0 + 40 + Math.random() * (O.y1 - O.y0 - 80);
      L.z = 20 + Math.random() * 200;
      L.sx = L.x;
      L.sy = L.y;
      L.sz = L.z;
    } else if (st === 6) {
      place(TRK.embudo, TRK.embudo.total, L.a * 0.6, L.b);
      const v = 1300 * Math.sqrt(Q / 10);
      L.x = px;
      L.y = py;
      L.z = pz;
      L.vx = DIR[0] * v;
      L.vy = 0;
      L.vz = DIR[2] * v;
    } else if (st === 7) {
      L.x = impact[0] + nrm() * 160;
      L.y = nrm() * 200;
      L.z = 60 + Math.random() * 40;
    }
  }

  // ----- paso de tiempo -----
  let time = 0;
  function step(dt) {
    const f = Q / 10;
    time += dt;
    // estanque de origen: deriva hacia la canasta de succion con un giro lento
    for (let i = 0; i < pOrigen.n; i++) {
      const dx = CAN[0] - pOrigen.x[i];
      const dy = CAN[1] - pOrigen.y[i];
      const dz = 40 - pOrigen.z[i];
      const dist = Math.hypot(dx, dy, dz) + 1e-3;
      const sp = (28 + 300 * Math.exp(-dist / 230)) * f;
      const sw = 55 * Math.exp(-dist / 600);
      pOrigen.x[i] += ((dx / dist) * sp - (dy / dist) * sw + nrm() * 14) * dt;
      pOrigen.y[i] += ((dy / dist) * sp + (dx / dist) * sw + nrm() * 14) * dt;
      pOrigen.z[i] += ((dz / dist) * sp * 0.6 + nrm() * 8) * dt;
      if (pOrigen.z[i] < 8) pOrigen.z[i] = 8;
      if (pOrigen.z[i] > O.z1 - 4) pOrigen.z[i] = O.z1 - 4;
      if (dist < 42) resetOrigen(pOrigen, i);
    }
    // piscina de destino: se abre desde donde cae el chorro
    for (let i = 0; i < pDest.n; i++) {
      const rx = pDest.x[i] - impact[0];
      const ry = pDest.y[i] - impact[1];
      const r = Math.hypot(rx, ry) + 1;
      const dr = 150 * f * Math.exp(-r / 380);
      pDest.x[i] += ((rx / r) * dr + nrm() * 22) * dt;
      pDest.y[i] += ((ry / r) * dr + nrm() * 22) * dt;
      pDest.z[i] += nrm() * 16 * dt;
      pDest.age[i] += dt;
      if (pDest.x[i] < Dp.x0 + 8 || pDest.x[i] > Dp.x1 - 8 || Math.abs(pDest.y[i]) > Dp.y1 - 8 || pDest.age[i] > 16) resetDest(pDest, i, Math.random() < 0.9);
      if (pDest.z[i] < 8) pDest.z[i] = 8;
      if (pDest.z[i] > Dp.z1 - 2) pDest.z[i] = Dp.z1 - 2;
    }
    // chorro: tiro parabolico desde la boca de la manguera
    for (let i = 0; i < pFall.n; i++) {
      pFall.x[i] += pFall.vx[i] * dt;
      pFall.y[i] += pFall.vy[i] * dt;
      pFall.z[i] += pFall.vz[i] * dt;
      pFall.vz[i] -= G * dt;
      if (pFall.z[i] < Dp.z1) resetFall(pFall, i);
    }
    // tramos
    for (const p of pops) {
      if (p.kind !== "track") continue;
      const trk = p.trk;
      for (let i = 0; i < p.n; i++) {
        let v;
        if (trk.kind === "lam") {
          const j = lamIndexAt(p.u[i]);
          v = lamSpeed(LAM.X[j]);
        } else v = speedOn(trk, p.u[i]);
        p.u[i] += v * dt;
        p.a[i] += nrm() * 0.5 * dt;
        if (p.a[i] > 1) p.a[i] = 2 - p.a[i];
        if (p.a[i] < -1) p.a[i] = -2 - p.a[i];
        if (p.u[i] > p.u1) {
          p.u[i] = p.u0 + (p.u[i] - p.u1);
          p.a[i] = Math.random() * 2 - 1;
          p.b[i] = Math.random();
        }
      }
    }
    // larvas
    for (const L of larvae) {
      if (L.st === 0) {
        const dx = CAN[0] - L.sx;
        const dy = CAN[1] - L.sy;
        const dist = Math.hypot(dx, dy) + 1;
        L.t += (dt * (260 * f + 40)) / dist;
        const t = Math.min(1, L.t);
        const e = t * t * (3 - 2 * t);
        L.x = L.sx + dx * e - (dy / dist) * 120 * Math.sin(Math.PI * e);
        L.y = L.sy + dy * e + (dx / dist) * 120 * Math.sin(Math.PI * e);
        L.z = L.sz + (50 - L.sz) * e;
        if (t >= 1) toStage(L, 1);
      } else if (L.st >= 1 && L.st <= 5) {
        const trk = TRK[STAGES[L.st]];
        let v;
        if (trk.kind === "lam") v = lamSpeed(LAM.X[lamIndexAt(L.u)]);
        else v = speedOn(trk, L.u);
        L.u += v * dt;
        if (L.u >= trk.total) toStage(L, L.st + 1);
      } else if (L.st === 6) {
        L.x += L.vx * dt;
        L.y += L.vy * dt;
        L.z += L.vz * dt;
        L.vz -= G * dt;
        if (L.z < Dp.z1) toStage(L, 7);
      } else {
        L.t += dt;
        L.x += 60 * dt * Math.exp(-(L.x - impact[0]) / 400) * -1 + nrm() * 10 * dt;
        L.y += (Math.sign(L.y || 1) * 45 + nrm() * 30) * dt;
        if (L.t > 6) toStage(L, 0);
      }
    }
  }


  // ================= visor 3D =================
  const MESH = JSON.parse(document.getElementById("f1-mesh").textContent);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1.6, 40, 60000);
  camera.up.set(0, 0, 1);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a94a0, 0.95));
  const sun = new THREE.DirectionalLight(0xffffff, 0.85);
  sun.position.set(-2500, 3000, 5000);
  scene.add(sun);

  const classify = (n) => {
    if (/^(lateral_tobogan|tapa_tobogan|vidrio_protector|PROPUESTA_ventana|pared_lateral|pared_trasera|cubierta|pared_estrechamiento|sumidero_pared|deflector|tapa_sensor|PROPUESTA_piscina_paredes|PROPUESTA_piscina_destino_paredes)/.test(n)) return "glass";
    if (/^(difusor|tubo_drenaje|embudo|acople_salida|PROPUESTA_manguera|PROPUESTA_tuberia)/.test(n)) return "pipe";
    if (/^vertedero_rampa|^malla_cedazo/.test(n)) return "subject";
    if (/^neumatico/.test(n)) return "tire";
    if (/^(fondo|PROPUESTA_piscina_fondo|PROPUESTA_piscina_destino_fondo|sumidero_fondo)/.test(n)) return "floor";
    return "struct";
  };
  const PAL = {
    dark: { struct: 0x9aa3ae, tire: 0x2d2f33, floor: 0x7b838d, subject: 0xf4f4f1, glass: 0x8fc3dc, pipe: 0xb4c2d0, water: 0x3ca8c4, line: 0xdfe4ea },
    light: { struct: 0xe6e6e2, tire: 0x56585c, floor: 0xd8d8d3, subject: 0x2b2b2e, glass: 0x3c7a96, pipe: 0x93a4b6, water: 0x0a7e9c, line: 0x1d1f23 },
  };
  const mats = {};
  const mk = (kind, opts) => {
    mats[kind] = new THREE.MeshStandardMaterial({ roughness: 0.75, metalness: 0.05, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, ...opts });
  };
  mk("struct", {});
  mk("tire", {});
  mk("floor", {});
  mk("subject", {});
  mk("glass", { transparent: true, opacity: 0.13, depthWrite: false, roughness: 0.2 });
  mk("pipe", { transparent: true, opacity: 0.34, depthWrite: false });
  const lineMats = { opaque: new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 }), glass: new THREE.LineBasicMaterial({ transparent: true, opacity: 0.45, depthWrite: false }) };
  const pickable = [];
  const model = new THREE.Group();
  scene.add(model);
  for (const b of MESH) {
    const kind = classify(b.n);
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(Float32Array.from(b.v, (x) => x / 10), 3));
    g.setIndex(b.t);
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, mats[kind]);
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(g, kind === "pipe" ? 85 : 38), kind === "glass" || kind === "pipe" ? lineMats.glass : lineMats.opaque);
    if (kind === "glass") m.renderOrder = e.renderOrder = 5;
    else if (kind === "pipe") m.renderOrder = e.renderOrder = 2;
    else pickable.push(m);
    model.add(m);
    if (!/^embudo/.test(b.n)) model.add(e);
  }
  // agua quieta
  const waterTop = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.3, depthWrite: false, side: THREE.DoubleSide });
  const waterSide = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide });
  const addWater = (arr, mat) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(Float32Array.from(arr), 3));
    const m = new THREE.Mesh(g, mat);
    m.renderOrder = 1;
    scene.add(m);
    return m;
  };
  for (const v of D.water) {
    addWater(v.top, waterTop);
    addWater(v.side, waterSide);
  }
  // lamina sobre rampa y canal: se rehace con el caudal
  let sheetTop = null;
  let sheetSide = null;
  function buildSheet() {
    const top = [];
    const side = [];
    let prev = null;
    for (let i = 0; i < LAM.n; i++) {
      if (LAM.X[i] > D.levels.xRamp) continue;
      const cur = { x: LAM.X[i], w: LAM.arr[i * NF + 9], t: LAM.top[i], b: LAM.bed[i] };
      if (prev) {
        const a = [prev.x, -prev.w, prev.t];
        const b2 = [prev.x, prev.w, prev.t];
        const c = [cur.x, cur.w, cur.t];
        const d2 = [cur.x, -cur.w, cur.t];
        top.push(...a, ...b2, ...c, ...a, ...c, ...d2);
        for (const sgn of [-1, 1]) {
          const p0 = [prev.x, sgn * prev.w, prev.b];
          const p1 = [cur.x, sgn * cur.w, cur.b];
          const p2 = [cur.x, sgn * cur.w, cur.t];
          const p3 = [prev.x, sgn * prev.w, prev.t];
          side.push(...p0, ...p1, ...p2, ...p0, ...p2, ...p3);
        }
      }
      prev = cur;
    }
    for (const m of [sheetTop, sheetSide]) if (m) {
      scene.remove(m);
      m.geometry.dispose();
    }
    sheetTop = addWater(top, waterTop);
    sheetSide = addWater(side, waterSide);
  }

  // particulas: una nube para el agua y otra para los grupos de larvas
  const NW = pops.reduce((s, p) => s + p.n, 0);
  const NL = 400;
  const wpos = new Float32Array(NW * 3);
  const lpos = new Float32Array(NL * 3).fill(-1e5);
  const mkPoints = (arr, size, ring2, order) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(arr, 3));
    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: { uSize: { value: size }, uScale: { value: 1000 }, uColor: { value: new THREE.Color(0x9fe4f2) }, uEdge: { value: new THREE.Color(0x000000) }, uRing: { value: ring2 } },
      vertexShader: "uniform float uSize;uniform float uScale;void main(){vec4 mv=modelViewMatrix*vec4(position,1.);gl_PointSize=clamp(uSize*uScale/-mv.z,1.5,11.);gl_Position=projectionMatrix*mv;}",
      fragmentShader: "uniform vec3 uColor;uniform vec3 uEdge;uniform float uRing;void main(){vec2 c=gl_PointCoord-.5;float r=length(c)*2.;if(r>1.)discard;vec3 col=uColor;if(uRing>0.&&r>.68)col=uEdge;gl_FragColor=vec4(col,.9);}",
    });
    const pts = new THREE.Points(g, mat);
    pts.frustumCulled = false;
    pts.renderOrder = order;
    scene.add(pts);
    return pts;
  };
  const waterPts = mkPoints(wpos, 9, 0, 3);
  const larvaPts = mkPoints(lpos, 30, 1, 4);

  function fillPositions() {
    let k = 0;
    for (const p of pops) {
      const n = p.n;
      if (p.kind === "track") {
        const trk = p.trk;
        for (let i = 0; i < n; i++) {
          let a = p.a[i];
          let b = p.b[i];
          if (trk.kind === "lam") {
            const j = lamIndexAt(p.u[i]);
            if (LAM.X[j] > D.levels.xDefl) {
              a = Math.max(-1, Math.min(1, a + 0.1 * Math.sin(time * 0.45 + p.ph[i])));
              b = Math.max(0, Math.min(1, b + 0.08 * Math.sin(time * 0.6 + p.ph[i] * 2)));
            }
          }
          place(trk, p.u[i], a, b);
          wpos[k++] = px;
          wpos[k++] = py;
          wpos[k++] = pz;
        }
      } else {
        for (let i = 0; i < n; i++) {
          wpos[k++] = p.x[i];
          wpos[k++] = p.y[i];
          wpos[k++] = p.z[i];
        }
      }
    }
    waterPts.geometry.attributes.position.needsUpdate = true;
    lpos.fill(-1e5);
    larvae.forEach((L, i) => {
      if (i >= NL) return;
      if (L.st >= 1 && L.st <= 5) place(TRK[STAGES[L.st]], L.u, L.a, L.b);
      else {
        px = L.x;
        py = L.y;
        pz = L.z;
      }
      lpos[i * 3] = px;
      lpos[i * 3 + 1] = py;
      lpos[i * 3 + 2] = pz;
    });
    larvaPts.geometry.attributes.position.needsUpdate = true;
  }

  // colores segun el tema
  let theme = "";
  function colors() {
    const t = app.getAttribute("data-theme");
    if (t === theme) return;
    theme = t;
    const p = PAL[t === "dark" ? "dark" : "light"];
    for (const k of ["struct", "tire", "floor", "subject", "glass", "pipe"]) mats[k].color.setHex(p[k]);
    lineMats.opaque.color.setHex(p.line);
    lineMats.glass.color.setHex(t === "dark" ? p.glass : p.line);
    waterTop.color.setHex(p.water);
    waterSide.color.setHex(p.water);
    const cs = getComputedStyle(app);
    waterPts.material.uniforms.uColor.value.set(cs.getPropertyValue("--ptl").trim() || "#9fe4f2");
    larvaPts.material.uniforms.uColor.value.set(cs.getPropertyValue("--amber").trim() || "#ffb454");
    larvaPts.material.uniforms.uEdge.value.set(t === "dark" ? "#0b0b0b" : "#ffffff");
  }

  // ----- camara orbital propia: girar, mover y acercar -----
  const cam = { th: (114 * Math.PI) / 180, ph: (52 * Math.PI) / 180, r: 7000, t: new THREE.Vector3(620, -760, 520) };
  const goal = { th: cam.th, ph: cam.ph, r: cam.r, t: cam.t.clone() };
  const clampCam = (c) => {
    c.ph = Math.max(0.06, Math.min(1.72, c.ph));
    c.r = Math.max(120, Math.min(22000, c.r));
  };
  function applyCam() {
    camera.position.set(cam.t.x + cam.r * Math.sin(cam.ph) * Math.cos(cam.th), cam.t.y + cam.r * Math.sin(cam.ph) * Math.sin(cam.th), cam.t.z + cam.r * Math.cos(cam.ph));
    camera.lookAt(cam.t);
  }
  const VIEWS = {
    todo: { th: 114, ph: 52, r: 7000, at: [620, -760, 520] },
    estanque: { th: 125, ph: 55, r: 3600, at: [2380, -1500, 160] },
    caja: { th: 120, ph: 52, r: 1500, at: [2330, 0, 1340] },
    ventana: { th: 118, ph: 50, r: 1100, at: [1060, 0, 1150] },
    embudo: { th: 118, ph: 54, r: 2300, at: [420, 0, 760] },
  };
  const unpress = () => root.querySelectorAll("[data-view-btn]").forEach((b) => b.setAttribute("aria-pressed", "false"));
  function goView(name) {
    const v = VIEWS[name];
    goal.th = (v.th * Math.PI) / 180;
    goal.ph = (v.ph * Math.PI) / 180;
    goal.r = v.r;
    goal.t.set(v.at[0], v.at[1], v.at[2]);
    while (goal.th - cam.th > Math.PI) goal.th -= 2 * Math.PI;
    while (goal.th - cam.th < -Math.PI) goal.th += 2 * Math.PI;
    root.querySelectorAll("[data-view-btn]").forEach((b) => b.setAttribute("aria-pressed", String(b.getAttribute("data-view-btn") === name)));
  }
  root.querySelectorAll("[data-view-btn]").forEach((b) => b.addEventListener("click", () => goView(b.getAttribute("data-view-btn"))));
  root.querySelectorAll("[data-zoom]").forEach((b) => b.addEventListener("click", () => {
    goal.r *= b.getAttribute("data-zoom") === "in" ? 1 / 1.5 : 1.5;
    clampCam(goal);
  }));
  const syncGoal = () => {
    goal.th = cam.th;
    goal.ph = cam.ph;
    goal.r = cam.r;
    goal.t.copy(cam.t);
    unpress();
  };
  let cssW = 1;
  let cssH = 1;
  function resize() {
    const r = box.getBoundingClientRect();
    cssW = Math.max(1, r.width);
    cssH = Math.max(1, r.height);
    const pr = Math.min(2, window.devicePixelRatio || 1);
    renderer.setPixelRatio(pr);
    renderer.setSize(cssW, cssH, false);
    camera.aspect = cssW / cssH;
    camera.updateProjectionMatrix();
    const sc = (cssH * pr) / (2 * Math.tan((camera.fov * Math.PI) / 360));
    waterPts.material.uniforms.uScale.value = sc;
    larvaPts.material.uniforms.uScale.value = sc;
  }
  new ResizeObserver(resize).observe(box);
  const panBy = (dx, dy) => {
    const k = (2 * cam.r * Math.tan((camera.fov * Math.PI) / 360)) / cssH;
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 1);
    cam.t.addScaledVector(right, -dx * k).addScaledVector(up, dy * k);
  };
  const ptrs = new Map();
  let lastPinch = null;
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  canvas.addEventListener("pointerdown", (e) => {
    canvas.setPointerCapture(e.pointerId);
    ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY, b: e.button, sh: e.shiftKey || e.ctrlKey });
    lastPinch = null;
    canvas.style.cursor = "grabbing";
  });
  const endPtr = (e) => {
    ptrs.delete(e.pointerId);
    lastPinch = null;
    if (!ptrs.size) canvas.style.cursor = "";
  };
  canvas.addEventListener("pointerup", endPtr);
  canvas.addEventListener("pointercancel", endPtr);
  function zoomToward(mx, my, factor) {
    const ndc = new THREE.Vector2((mx / cssW) * 2 - 1, -(my / cssH) * 2 + 1);
    const plane = new THREE.Plane();
    const pointAt = () => {
      camera.updateMatrixWorld();
      const dirn = new THREE.Vector3(ndc.x, ndc.y, 0.5).unproject(camera).sub(camera.position).normalize();
      const fwd = new THREE.Vector3();
      camera.getWorldDirection(fwd);
      plane.setFromNormalAndCoplanarPoint(fwd, cam.t);
      return new THREE.Ray(camera.position.clone(), dirn).intersectPlane(plane, new THREE.Vector3());
    };
    applyCam();
    const p1 = pointAt();
    cam.r *= factor;
    clampCam(cam);
    applyCam();
    const p2 = pointAt();
    if (p1 && p2) cam.t.add(p1.sub(p2));
    syncGoal();
  }
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    const r = canvas.getBoundingClientRect();
    zoomToward(e.clientX - r.left, e.clientY - r.top, Math.exp(e.deltaY * (e.ctrlKey ? 0.01 : 0.0016)));
  }, { passive: false });
  const ray = new THREE.Raycaster();
  canvas.addEventListener("dblclick", (e) => {
    const r = canvas.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / cssW) * 2 - 1, -((e.clientY - r.top) / cssH) * 2 + 1), camera);
    const hit = ray.intersectObjects(pickable, false)[0];
    if (hit) {
      goal.t.copy(hit.point);
      goal.r = Math.max(220, cam.r * 0.45);
      unpress();
    } else goView("todo");
  });

  // ----- estaciones: tabla y lectura por cursor -----
  const fmt = (n, d2 = 2) => n.toFixed(d2).replace(".", ",");
  const stationV = (st) => {
    const f = Q / 10;
    if (st.k === "lin") return st.v10 * f;
    if (st.k === "pow") return st.v10 * Math.pow(f, st.e);
    if (st.k === "1d") return prof(Q, "V", st.s);
    return 0;
  };
  const stationText = (st) => {
    const v = stationV(st);
    let t = st.name;
    if (st.k === "1d") t += " · lámina " + fmt(prof(Q, "h", st.s), 1) + " mm a " + fmt(v) + " m/s";
    else if (v > 0) t += " · " + fmt(v) + " m/s";
    return t;
  };
  tbody.innerHTML = "";
  const rows = D.stations.map((st) => {
    const tr = document.createElement("tr");
    tr.innerHTML = '<th scope="row">' + st.name + '</th><td data-v></td><td>' + st.txt + "</td>";
    tbody.appendChild(tr);
    return tr;
  });
  function paintRows() {
    D.stations.forEach((st, i) => {
      const v = stationV(st);
      rows[i].querySelector("[data-v]").textContent = st.k === "1d" ? fmt(prof(Q, "h", st.s), 1) + " mm · " + fmt(v) + " m/s" : v > 0 ? fmt(v) + " m/s" : "en reposo";
    });
  }
  let hoverI = -1;
  function paintReadout() {
    const t = hoverI >= 0 ? stationText(D.stations[hoverI]) : "Q " + Q + " L/s · manguera " + fmt((1.177 * Q) / 10) + " m/s · lámina en la ventana " + fmt(prof(Q, "h", D.canal.s_conteo), 1) + " mm a " + fmt(prof(Q, "V", D.canal.s_conteo)) + " m/s";
    if (readout.textContent !== t) readout.textContent = t;
    rows.forEach((r, i) => r.setAttribute("data-on", String(i === hoverI)));
  }
  const scr = (st) => {
    const v = new THREE.Vector3(st.at[0], st.at[1], st.at[2]).project(camera);
    return [((v.x + 1) / 2) * cssW, ((1 - v.y) / 2) * cssH, v.z];
  };
  canvas.addEventListener("pointermove", (e) => {
    const r = canvas.getBoundingClientRect();
    const me = ptrs.get(e.pointerId);
    if (me) {
      const dx = e.clientX - me.x;
      const dy = e.clientY - me.y;
      me.x = e.clientX;
      me.y = e.clientY;
      if (ptrs.size === 1) {
        if (me.b === 0 && !me.sh) {
          cam.th -= dx * 0.0072;
          cam.ph -= dy * 0.0072;
          clampCam(cam);
        } else panBy(dx, dy);
        syncGoal();
      } else if (ptrs.size === 2) {
        const [a, b] = [...ptrs.values()];
        const d0 = Math.hypot(a.x - b.x, a.y - b.y);
        const cx = (a.x + b.x) / 2;
        const cy = (a.y + b.y) / 2;
        if (lastPinch) {
          zoomToward(cx - r.left, cy - r.top, lastPinch.d / d0);
          panBy(cx - lastPinch.cx, cy - lastPinch.cy);
          syncGoal();
        }
        lastPinch = { d: d0, cx, cy };
      }
      return;
    }
    const mx = e.clientX - r.left;
    const my = e.clientY - r.top;
    let best = -1;
    let bd = 30;
    D.stations.forEach((st, i) => {
      const [x, y, z] = scr(st);
      if (z > 1) return;
      const dd = Math.hypot(x - mx, y - my);
      if (dd < bd) {
        bd = dd;
        best = i;
      }
    });
    if (best !== hoverI) {
      hoverI = best;
      paintReadout();
    }
  });
  canvas.addEventListener("pointerleave", () => {
    hoverI = -1;
    paintReadout();
  });
  rows.forEach((r, i) => {
    r.addEventListener("pointerenter", () => {
      hoverI = i;
      paintReadout();
    });
    r.addEventListener("pointerleave", () => {
      hoverI = -1;
      paintReadout();
    });
  });

  function setLam() {
    buildLam();
    segBounds();
    buildSheet();
    TRK.embudo.f0 = Math.max(0.08, Math.min(0.5, (prof(Q, "h", D.canal.s[D.canal.s.length - 1] - 1) + 3) / D.emb.hh));
    findImpact();
  }
  function update() {
    Q = +qIn.value;
    conc = +cIn.value;
    speed = Math.pow(10, +sIn.value);
    root.querySelector('[data-label="q"]').textContent = String(Q);
    root.querySelector('[data-label="conc"]').textContent = String(conc);
    root.querySelector('[data-label="speed"]').textContent = "×" + fmt(speed, speed < 1 ? 2 : 1);
    setLam();
    paintRows();
    paintReadout();
  }
  qIn.addEventListener("input", update);
  cIn.addEventListener("input", () => {
    update();
    newLarvae();
  });
  sIn.addEventListener("input", update);
  playBtn.addEventListener("click", () => {
    paused = !paused;
    playBtn.setAttribute("aria-pressed", String(!paused));
    playBtn.textContent = paused ? "Reproducir" : "Pausa";
  });

  function render() {
    colors();
    applyCam();
    camera.updateMatrixWorld();
    fillPositions();
    renderer.render(scene, camera);
    if (hoverI >= 0) {
      const [x, y] = scr(D.stations[hoverI]);
      ring.hidden = false;
      ring.style.transform = "translate(" + (x - 9).toFixed(1) + "px," + (y - 9).toFixed(1) + "px)";
    } else ring.hidden = true;
  }
  let frame = 0;
  let last = 0;
  let visible = false;
  function tick(now) {
    const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60;
    last = now;
    const k2 = 1 - Math.exp(-dt * 5);
    if (!ptrs.size) {
      cam.th += (goal.th - cam.th) * k2;
      cam.ph += (goal.ph - cam.ph) * k2;
      cam.r += (goal.r - cam.r) * k2;
      cam.t.lerp(goal.t, k2);
    }
    if (!still.matches && !paused) step(dt * speed);
    render();
    frame = visible ? requestAnimationFrame(tick) : 0;
  }
  new IntersectionObserver((en) => {
    visible = en[en.length - 1].isIntersecting;
    if (visible && !frame) {
      last = 0;
      frame = requestAnimationFrame(tick);
    }
  }, { rootMargin: "100px 0px" }).observe(box);
  update();
  newLarvae();
  resize();
  render();
})();
