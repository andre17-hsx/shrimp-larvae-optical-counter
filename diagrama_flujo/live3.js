// Figura 3 en vivo: la ventana de conteo sobre el modelo 3D real. Las larvas bajan por el tramo inclinado, el backlight destella
// en cada cuadro y una pantalla propia muestra lo que ve la camara (siluetas, cajas de deteccion, conteo).
(function () {
  const root = document.getElementById("fig3");
  if (!root || !window.THREE) return;
  const THREE = window.THREE;
  const box = root.querySelector(".f3box");
  const canvas = box.querySelector("canvas.f3gl");
  const camCv = box.querySelector("canvas.f3cam");
  const cctx = camCv.getContext("2d");
  const readout = root.querySelector("[data-readout]");
  const app = root.closest(".iso");
  const F = DATA.f3;
  const WIN = F.win;
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  const el = (id) => root.querySelector("input[data-" + id + "], button[data-" + id + "]");
  const inputs = { Q: el("q"), conc: el("conc"), pulse: el("pulse"), fps: el("fps"), fov: el("fov"), slow: el("slow") };
  const out = {};
  root.querySelectorAll("[data-out]").forEach((n) => (out[n.dataset.out] = n));
  const RES_PX = 1456; // pixeles a lo ancho del sensor (IMX296)
  const SENSOR_W = 5.02; // mm: 1456 px de 3,45 um
  const CH_W = 2 * WIN.hw; // ancho del canal
  const FLOW_FOV = Math.min(WIN.len, WIN.blLen); // largo iluminado en el sentido del flujo
  const prof = F.prof;
  const XMIN = -430;
  const XMAX = 430;

  // ----- marco local de la ventana: x aguas abajo sobre la pendiente, y a lo ancho, z sobre el lecho -----
  const th = WIN.theta;
  const Wc = new THREE.Vector3(...WIN.c);
  const tF = new THREE.Vector3(-Math.cos(th), 0, -Math.sin(th));
  const yA = new THREE.Vector3(0, 1, 0);
  const nN = new THREE.Vector3(-Math.sin(th), 0, Math.cos(th));
  const world = (x, y, z, v) => v.copy(Wc).addScaledVector(tF, x).addScaledVector(yA, y).addScaledVector(nN, z);

  // ----- escena -----
  const MESH = JSON.parse(document.getElementById("f1-mesh").textContent);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1.6, 10, 40000);
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
  for (const k of ["struct", "tire", "floor", "subject"]) mk(k, {});
  mk("glass", { transparent: true, opacity: 0.14, depthWrite: false, roughness: 0.2 });
  mk("pipe", { transparent: true, opacity: 0.34, depthWrite: false });
  const lineMats = { opaque: new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 }), glass: new THREE.LineBasicMaterial({ transparent: true, opacity: 0.45, depthWrite: false }) };
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
    scene.add(m);
    if (!/^embudo/.test(b.n)) scene.add(e);
  }

  // lamina de agua sobre el tramo inclinado
  const sheetMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.26, depthWrite: false });
  const sheet = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), sheetMat);
  sheet.matrixAutoUpdate = false;
  sheet.renderOrder = 1;
  scene.add(sheet);
  const basis = new THREE.Matrix4().makeBasis(tF, yA, nN);
  function setSheet(h) {
    const m = new THREE.Matrix4().makeTranslation(Wc.x + nN.x * (h / 2), Wc.y, Wc.z + nN.z * (h / 2));
    m.multiply(basis).multiply(new THREE.Matrix4().makeScale(XMAX - XMIN, CH_W - 6, Math.max(h, 0.8)));
    // el centro de la caja en x es el punto medio del tramo
    const mid = (XMAX + XMIN) / 2;
    m.premultiply(new THREE.Matrix4().makeTranslation(tF.x * mid, 0, tF.z * mid));
    sheet.matrix.copy(m);
    sheet.matrixWorldNeedsUpdate = true;
  }

  // campo de la camara: abanico desde la lente hasta la franja que ve sobre el lecho
  const fanMat = new THREE.MeshBasicMaterial({ color: 0xffb454, transparent: true, opacity: 0.07, depthWrite: false, side: THREE.DoubleSide });
  const fanLine = new THREE.LineBasicMaterial({ color: 0xffb454, transparent: true, opacity: 0.85, depthWrite: false });
  const fanGeo = new THREE.BufferGeometry();
  fanGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(5 * 3 * 3), 3));
  const fan = new THREE.Mesh(fanGeo, fanMat);
  fan.renderOrder = 3;
  scene.add(fan);
  const fanEdgesGeo = new THREE.BufferGeometry();
  fanEdgesGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(8 * 2 * 3), 3));
  const fanEdges = new THREE.LineSegments(fanEdgesGeo, fanLine);
  fanEdges.renderOrder = 6;
  scene.add(fanEdges);
  const LENS = new THREE.Vector3(...F.lens);
  function setFan(fov, fovFlow) {
    const c = [];
    for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) c.push(world((sx * fovFlow) / 2, (sy * fov) / 2, 1, new THREE.Vector3()));
    const tri = [];
    for (let i = 0; i < 4; i++) tri.push(LENS, c[i], c[(i + 1) % 4]);
    tri.push(c[0], c[1], c[2], c[0], c[2], c[3]);
    const pa = fanGeo.attributes.position;
    let k = 0;
    for (const p of tri.slice(0, 12)) {
      pa.array[k++] = p.x;
      pa.array[k++] = p.y;
      pa.array[k++] = p.z;
    }
    pa.needsUpdate = true;
    const e = [];
    for (let i = 0; i < 4; i++) e.push(LENS, c[i], c[i], c[(i + 1) % 4]);
    const ea = fanEdgesGeo.attributes.position;
    k = 0;
    for (const p of e) {
      ea.array[k++] = p.x;
      ea.array[k++] = p.y;
      ea.array[k++] = p.z;
    }
    ea.needsUpdate = true;
    fanGeo.setDrawRange(0, 12);
    fanEdgesGeo.setDrawRange(0, 16);
  }

  // destello del backlight bajo la ventana
  const flashMat = new THREE.MeshBasicMaterial({ color: 0xffd9a0, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const flashM = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), flashMat);
  flashM.matrixAutoUpdate = false;
  flashM.renderOrder = 4;
  scene.add(flashM);
  {
    const m = new THREE.Matrix4().makeTranslation(Wc.x - nN.x * 2.5, Wc.y, Wc.z - nN.z * 2.5);
    m.multiply(basis).multiply(new THREE.Matrix4().makeScale(Math.min(WIN.blLen, 120), 2 * WIN.blHalf, 1));
    flashM.matrix.copy(m);
  }

  // larvas: una linea corta por larva (mas un punto en la cabeza)
  const MAXL = 1200;
  const lpos = new Float32Array(MAXL * 6).fill(-1e5);
  const lcol = new Float32Array(MAXL * 6);
  const lg = new THREE.BufferGeometry();
  lg.setAttribute("position", new THREE.BufferAttribute(lpos, 3));
  lg.setAttribute("color", new THREE.BufferAttribute(lcol, 3));
  const lines = new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ vertexColors: true, depthWrite: false }));
  lines.frustumCulled = false;
  lines.renderOrder = 4;
  scene.add(lines);
  const hpos = new Float32Array(MAXL * 3).fill(-1e5);
  const hcol = new Float32Array(MAXL * 3);
  const hg = new THREE.BufferGeometry();
  hg.setAttribute("position", new THREE.BufferAttribute(hpos, 3));
  hg.setAttribute("color", new THREE.BufferAttribute(hcol, 3));
  const heads = new THREE.Points(hg, new THREE.PointsMaterial({ vertexColors: true, size: 4.5, sizeAttenuation: false, depthWrite: false }));
  heads.frustumCulled = false;
  heads.renderOrder = 4;
  scene.add(heads);

  // ----- tema -----
  let theme = "";
  let colOut = new THREE.Color(0x222222);
  const colIn = new THREE.Color(0xe08a00);
  function colors() {
    const t = app.getAttribute("data-theme");
    if (t === theme) return;
    theme = t;
    const p = PAL[t === "dark" ? "dark" : "light"];
    for (const k of ["struct", "tire", "floor", "subject", "glass", "pipe"]) mats[k].color.setHex(p[k]);
    lineMats.opaque.color.setHex(p.line);
    lineMats.glass.color.setHex(t === "dark" ? p.glass : p.line);
    sheetMat.color.setHex(p.water);
    colOut = new THREE.Color(t === "dark" ? 0xf2f2f2 : 0x15181a);
    colIn.set(t === "dark" ? 0xffb454 : 0xd97706);
  }

  // ----- camara orbital propia -----
  const cam = { th: (116 * Math.PI) / 180, ph: (46 * Math.PI) / 180, r: 1500, t: Wc.clone().addScaledVector(nN, 60) };
  const goal = { th: cam.th, ph: cam.ph, r: cam.r, t: cam.t.clone() };
  const clampCam = (c) => {
    c.ph = Math.max(0.06, Math.min(1.72, c.ph));
    c.r = Math.max(80, Math.min(9000, c.r));
  };
  function applyCam() {
    camera.position.set(cam.t.x + cam.r * Math.sin(cam.ph) * Math.cos(cam.th), cam.t.y + cam.r * Math.sin(cam.ph) * Math.sin(cam.th), cam.t.z + cam.r * Math.cos(cam.ph));
    camera.lookAt(cam.t);
  }
  const VIEWS = {
    ventana: { th: 116, ph: 46, r: 1500, at: Wc.clone().addScaledVector(nN, 60) },
    arriba: { th: 90, ph: 4, r: 1500, at: Wc.clone() },
    lado: { th: 90, ph: 88, r: 1500, at: Wc.clone().addScaledVector(nN, 60) },
    camara: { th: 130, ph: 62, r: 420, at: new THREE.Vector3(F.lens[0], 0, F.lens[2] - 20) },
  };
  function goView(name) {
    const v = VIEWS[name];
    goal.th = (v.th * Math.PI) / 180;
    goal.ph = (v.ph * Math.PI) / 180;
    goal.r = v.r;
    goal.t.copy(v.at);
    while (goal.th - cam.th > Math.PI) goal.th -= 2 * Math.PI;
    while (goal.th - cam.th < -Math.PI) goal.th += 2 * Math.PI;
    root.querySelectorAll("[data-view-btn]").forEach((b) => b.setAttribute("aria-pressed", String(b.getAttribute("data-view-btn") === name)));
  }
  const unpress = () => root.querySelectorAll("[data-view-btn]").forEach((b) => b.setAttribute("aria-pressed", "false"));
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
    const pw = Math.round(Math.min(380, cssW * 0.4));
    const ph = Math.round(pw * 0.5);
    camCv.style.width = pw + "px";
    camCv.style.height = ph + "px";
    camCv.width = pw * pr;
    camCv.height = ph * pr;
    pxr = pr;
  }
  let pxr = 1;
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
  canvas.addEventListener("pointermove", (e) => {
    const me = ptrs.get(e.pointerId);
    if (!me) return;
    const r = canvas.getBoundingClientRect();
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
  });
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
  canvas.addEventListener("dblclick", () => goView("ventana"));

  // ----- calculos de la tabla -----
  const lerpQ = (Q, key) => {
    const qs = Object.keys(prof).map(Number).sort((a, b) => a - b);
    if (Q <= qs[0]) return prof[qs[0]][key];
    for (let i = 1; i < qs.length; i++) {
      if (Q <= qs[i]) {
        const a = prof[qs[i - 1]][key];
        const b = prof[qs[i]][key];
        return a + ((Q - qs[i - 1]) / (qs[i] - qs[i - 1])) * (b - a);
      }
    }
    return prof[qs[qs.length - 1]][key];
  };
  let st = {};
  function params() {
    const Q = +inputs.Q.value;
    const conc = +inputs.conc.value;
    const pulse = +inputs.pulse.value;
    const fps = +inputs.fps.value;
    const fov = +inputs.fov.value;
    const slow = 1 / Math.pow(10, +inputs.slow.value);
    const h = lerpQ(Q, "h");
    const V = lerpQ(Q, "V");
    const Fr = lerpQ(Q, "Fr");
    const res = fov / RES_PX;
    const fovFlow = Math.min(FLOW_FOV, fov * 0.75);
    const blur = (V * 1000 * pulse * 1e-6) / res;
    const step = (V * 1000) / fps;
    const framesPer = fovFlow / step;
    const rateAll = conc * Q;
    const frac = Math.min(1, fov / CH_W);
    const rateFov = rateAll * frac;
    const inView = (rateFov * fovFlow) / (V * 1000);
    const fNeed = (F.lensH * SENSOR_W) / fov; // lente necesario a la altura que tiene la lente en el modelo
    const hNeed = (fov * 12) / SENSOR_W; // altura necesaria con un lente de 12 mm
    const ang = 2 * Math.atan(fov / 2 / F.lensH) * (180 / Math.PI);
    return { Q, conc, pulse, fps, fov, slow, h, V, Fr, res, fovFlow, blur, step, framesPer, rateAll, frac, rateFov, inView, fNeed, hNeed, ang };
  }
  const fmt = (n, d = 1) => n.toFixed(d).replace(".", ",");
  function paintOutputs() {
    const s = st;
    const set = (k, v, bad) => {
      if (!out[k]) return;
      out[k].textContent = v;
      out[k].closest("tr")?.setAttribute("data-warn", bad ? "true" : "false");
    };
    set("h", fmt(s.h) + " mm");
    set("V", fmt(s.V, 2) + " m/s  (Froude " + fmt(s.Fr) + ")");
    set("field", fmt(s.fov, 0) + " mm a lo ancho (" + fmt(s.frac * 100, 0) + " % del canal de " + CH_W + " mm) por " + fmt(s.fovFlow, 0) + " mm en el sentido del flujo", s.frac < 0.999);
    set("lens", "con la lente a " + fmt(F.lensH, 0) + " mm del lecho (como en el modelo) hace falta un lente de " + fmt(s.fNeed, 1) + " mm (" + fmt(s.ang, 0) + "° de ángulo); con un lente de 12 mm tendría que estar a " + fmt(s.hNeed / 1000, 2) + " m", s.fNeed < 4);
    set("res", fmt(s.res, 3) + " mm/px  (larva de 0,45 mm = " + fmt(0.45 / s.res) + " px de ancho)", 0.45 / s.res < 2);
    set("blur", fmt(s.blur) + " px", s.blur > 1);
    set("frames", fmt(s.framesPer) + " cuadros por larva  (" + fmt(s.step, 0) + " mm entre cuadros)", s.framesPer < 3);
    set("inview", fmt(s.inView) + " larvas a la vez en el campo");
    set("rateFov", fmt(s.rateFov, 0) + " larvas por segundo cruzan la franja visible (" + fmt(s.frac * 100, 0) + " % del ancho)");
    set("rateAll", fmt(s.rateAll * 60, 0).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " larvas por minuto en todo el canal");
    set("slow", "×1/" + Math.round(1 / s.slow) + " del tiempo real: un cuadro cada " + fmt(1 / s.fps / s.slow) + " s");
    const w = [];
    if (s.blur > 1) w.push("desenfoque > 1 px: acorta el pulso");
    if (s.framesPer < 3) w.push("menos de 3 cuadros por larva: sube los fps");
    if (0.45 / s.res < 2) w.push("la larva ocupa menos de 2 px");
    const t = "Q " + s.Q + " L/s · lámina " + fmt(s.h) + " mm a " + fmt(s.V, 2) + " m/s" + (w.length ? " · ¡ " + w[0] : "");
    if (readout.textContent !== t) readout.textContent = t;
  }

  // ----- larvas -----
  let larvae = [];
  let clock = 0;
  let nextFrame = 0;
  let counted = 0;
  let pulseAt = -10;
  let spawnCarry = 0;
  let shotBoxes = [];
  const newLarva = (x0) => ({ x: x0 ?? XMIN, y: (Math.random() * 2 - 1) * (WIN.hw - 6), z: 0.8 + Math.random() * Math.max(0.5, st.h - 1.6), len: 11 + Math.random() * 7, wob: Math.random() * 6.28, seen: 0, done: false });
  function step(dt) {
    const v = st.V * 1000 * st.slow;
    spawnCarry += st.rateAll * st.slow * dt;
    while (spawnCarry >= 1 && larvae.length < MAXL) {
      spawnCarry -= 1;
      larvae.push(newLarva());
    }
    spawnCarry = Math.min(spawnCarry, 3);
    for (const L of larvae) L.x += v * dt;
    larvae = larvae.filter((L) => L.x < XMAX);
  }
  // lo que ve la camara en un disparo: siluetas oscuras sobre fondo infrarrojo claro
  function shot() {
    shotBoxes = [];
    for (const L of larvae) {
      if (Math.abs(L.y) > st.fov / 2 || Math.abs(L.x) > st.fovFlow / 2) continue;
      L.seen++;
      shotBoxes.push({ x: L.x, y: L.y, len: L.len });
    }
    pulseAt = clock;
  }
  function countExits() {
    for (const L of larvae) {
      if (!L.done && L.seen >= 2 && L.x > st.fovFlow / 2 && Math.abs(L.y) <= st.fov / 2) {
        L.done = true;
        counted++;
      }
    }
  }
  function drawCam() {
    const w = camCv.width;
    const h = camCv.height;
    cctx.setTransform(1, 0, 0, 1, 0, 0);
    cctx.fillStyle = "#0b0d10";
    cctx.fillRect(0, 0, w, h);
    const pad = 6 * pxr;
    const top = 16 * pxr;
    const bot = 16 * pxr;
    const iw = w - 2 * pad;
    const ih = h - top - bot;
    const lit = Math.max(0, 1 - (clock - pulseAt) / 0.4);
    cctx.fillStyle = "rgb(" + Math.round(150 + 60 * lit) + "," + Math.round(156 + 58 * lit) + "," + Math.round(152 + 52 * lit) + ")";
    cctx.fillRect(pad, top, iw, ih);
    const sx = iw / st.fov;
    const sy = ih / st.fovFlow;
    cctx.strokeStyle = "#15181a";
    cctx.fillStyle = "#15181a";
    cctx.lineCap = "round";
    cctx.lineWidth = Math.max(1.3, 0.45 * sx * 1.6) * 1;
    for (const b of shotBoxes) {
      const px = pad + (b.y + st.fov / 2) * sx;
      const py = top + (b.x + st.fovFlow / 2) * sy;
      const half = (b.len / 2) * sy + Math.max(0.5, st.blur) * st.res * sy * 0.5;
      cctx.beginPath();
      cctx.moveTo(px, py - half);
      cctx.lineTo(px, py + half);
      cctx.stroke();
    }
    cctx.strokeStyle = "#ffb454";
    cctx.lineWidth = Math.max(1, pxr * 0.9);
    for (const b of shotBoxes) {
      const px = pad + (b.y + st.fov / 2) * sx;
      const py = top + (b.x + st.fovFlow / 2) * sy;
      const half = (b.len / 2) * sy + 4 * pxr;
      cctx.strokeRect(px - 4 * pxr, py - half, 8 * pxr, 2 * half);
    }
    cctx.fillStyle = "#9aa4ac";
    cctx.font = 9 * pxr + "px ui-monospace,Menlo,Consolas,monospace";
    cctx.textBaseline = "alphabetic";
    cctx.fillText("cámara · " + fmt(st.fov, 0) + " × " + fmt(st.fovFlow, 0) + " mm (alto ×" + fmt(sy / sx, 0) + ")", pad, 11 * pxr);
    cctx.fillText("contadas " + counted, pad, h - 5 * pxr);
    cctx.textAlign = "right";
    cctx.fillText("850 nm", w - pad, h - 5 * pxr);
    cctx.textAlign = "left";
  }

  const tmp = new THREE.Vector3();
  function placeLarvae() {
    lpos.fill(-1e5);
    hpos.fill(-1e5);
    let i = 0;
    for (const L of larvae) {
      if (i >= MAXL) break;
      const wob = Math.sin(clock * 3 + L.wob) * 0.6;
      world(L.x - L.len / 2, L.y + wob, L.z, tmp);
      lpos[i * 6] = tmp.x;
      lpos[i * 6 + 1] = tmp.y;
      lpos[i * 6 + 2] = tmp.z;
      world(L.x + L.len / 2, L.y - wob, L.z, tmp);
      lpos[i * 6 + 3] = tmp.x;
      lpos[i * 6 + 4] = tmp.y;
      lpos[i * 6 + 5] = tmp.z;
      hpos[i * 3] = tmp.x;
      hpos[i * 3 + 1] = tmp.y;
      hpos[i * 3 + 2] = tmp.z;
      const inF = Math.abs(L.y) <= st.fov / 2 && Math.abs(L.x) <= st.fovFlow / 2;
      const c = inF ? colIn : colOut;
      for (const o of [i * 6, i * 6 + 3, i * 3 + 100000]) {
        if (o >= 100000) {
          hcol[o - 100000] = c.r;
          hcol[o - 100000 + 1] = c.g;
          hcol[o - 100000 + 2] = c.b;
        } else {
          lcol[o] = c.r;
          lcol[o + 1] = c.g;
          lcol[o + 2] = c.b;
        }
      }
      i++;
    }
    lg.attributes.position.needsUpdate = true;
    lg.attributes.color.needsUpdate = true;
    hg.attributes.position.needsUpdate = true;
    hg.attributes.color.needsUpdate = true;
    const k = Math.max(0, 1 - (clock - pulseAt) / 0.45);
    flashMat.opacity = 0.75 * k * k;
  }

  function render() {
    colors();
    applyCam();
    camera.updateMatrixWorld();
    placeLarvae();
    renderer.render(scene, camera);
    drawCam();
  }
  let frame = 0;
  let last = 0;
  let visible = false;
  let paused = false;
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
    if (!still.matches && !paused) {
      clock += dt;
      step(dt);
      nextFrame -= dt;
      if (nextFrame <= 0) {
        nextFrame += 1 / st.fps / st.slow;
        shot();
        countExits();
      }
    }
    render();
    frame = visible ? requestAnimationFrame(tick) : 0;
  }
  function update() {
    st = params();
    setSheet(st.h);
    setFan(st.fov, st.fovFlow);
    paintOutputs();
    root.querySelectorAll("[data-label]").forEach((n) => {
      const i = inputs[n.dataset.label];
      if (!i) return;
      const v = +i.value;
      n.textContent = n.dataset.label === "slow" ? "1/" + Math.round(Math.pow(10, v)) : String(v);
    });
  }
  Object.values(inputs).forEach((i) => i.addEventListener("input", update));
  const playBtn = el("play");
  playBtn.addEventListener("click", () => {
    paused = !paused;
    playBtn.setAttribute("aria-pressed", String(!paused));
    playBtn.textContent = paused ? "Reproducir" : "Pausa";
  });
  update();
  for (let i = 0; i < 90; i++) larvae.push(newLarva(XMIN + Math.random() * (XMAX - XMIN)));
  resize();
  shot();
  render();
  new IntersectionObserver((en) => {
    visible = en[en.length - 1].isIntersecting;
    if (visible && !frame) {
      last = 0;
      frame = requestAnimationFrame(tick);
    }
  }, { rootMargin: "100px 0px" }).observe(box);
})();
