// Figura 2 en vivo: particulas sobre las lineas de corriente del CFD, rampa seleccionable y lectura por estacion.
(function () {
  const root = document.getElementById("fig2");
  if (!root) return;
  const stage = root.querySelector(".iso-stage");
  const svg = stage.querySelector("svg");
  const fig = svg.querySelector(".fig2");
  const readout = root.querySelector("[data-readout]");
  const P = DATA.f2.P;
  const VAR = DATA.f2.variants;
  const raw = DATA.f2.info;
  const lerp = (arr, x) => {
    if (x <= arr[0][0]) return arr[0][1];
    for (let i = 1; i < arr.length; i++) if (x <= arr[i][0]) return arr[i - 1][1] + ((x - arr[i - 1][0]) / (arr[i][0] - arr[i - 1][0])) * (arr[i][1] - arr[i - 1][1]);
    return arr[arr.length - 1][1];
  };
  const info = {};
  for (const v of DATA.f2.variants) {
    const r = raw[v];
    const bot = (x) => {
      if (x > 0) return 60 - 0.2127659574468085 * x;
      if (r.ring.length === 4) return x > -3 ? 60 : 0;
      return Math.max(0, lerp(r.ring, x));
    };
    info[v] = {
      name: r.name,
      back: r.back,
      level: (x) => Math.max(lerp(r.nivel, x), bot(x)),
      bottom: bot,
      h: (x) => lerp(r.hx, x),
      v: (x) => lerp(r.vx, x),
    };
  }
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  const NS = "http://www.w3.org/2000/svg";
  let on = DATA.f2.start;
  let speed = 0.5;
  let clock = 0;
  let frame = 0;
  let last = 0;
  let visible = false;
  let station = null;
  let paused = false;
  const parts = {};
  for (const v of VAR) {
    const layer = svg.querySelector('g[data-pts="' + v + '"]');
    const mk = (arr) => arr.map((L) => ({ x: L[0], y: L[1], z: L[2], t: L[3], T: L[3][L[3].length - 1] }));
    const lines = mk(DATA.f2.lines[v]);
    const corner = mk(DATA.f2.corner[v]);
    const dots = [];
    const add = (L, i, n, hot) => {
      for (let j = 0; j < n; j++) {
        const c = document.createElementNS(NS, "circle");
        c.setAttribute("class", "pt");
        c.setAttribute("r", hot ? "1.9" : "1.6");
        if (hot) c.setAttribute("data-fix", "");
        layer.appendChild(c);
        dots.push({ c, L, hot, off: ((i * 0.6180339 + j / n) % 1) * (L.T + 2) });
      }
    };
    lines.forEach((L, i) => add(L, i, 2, false));
    corner.forEach((L, i) => add(L, i + 7, 3, true));
    parts[v] = dots;
  }
  const marker = svg.querySelector(".marker");
  const markerDot = svg.querySelector(".marker-dot");

  function place(L, tau) {
    let lo = 0;
    let hi = L.t.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (L.t[mid] <= tau) lo = mid;
      else hi = mid;
    }
    const f = Math.min(1, Math.max(0, (tau - L.t[lo]) / Math.max(1e-6, L.t[hi] - L.t[lo])));
    const x = L.x[lo] + (L.x[hi] - L.x[lo]) * f;
    const y = L.y[lo] + (L.y[hi] - L.y[lo]) * f;
    const z = L.z[lo] + (L.z[hi] - L.z[lo]) * f;
    return [x, -y, z, Math.hypot(L.x[hi] - L.x[lo], L.y[hi] - L.y[lo], L.z[hi] - L.z[lo]) / Math.max(1e-6, (L.t[hi] - L.t[lo]) * 1000)];
  }

  function draw() {
    const set = parts[on];
    for (const d of set) {
      const cycle = d.L.T + 2;
      const tau = (clock + d.off) % cycle;
      if (tau > d.L.T) {
        d.c.setAttribute("opacity", "0");
        continue;
      }
      const [x, y, z, v] = place(d.L, tau);
      const [sx, sy] = iso([x, y, z], P);
      const a = Math.min(1, tau / 0.5, (d.L.T - tau) / 0.4);
      d.c.setAttribute("cx", sx.toFixed(1));
      d.c.setAttribute("cy", sy.toFixed(1));
      d.c.setAttribute("opacity", (0.25 + 0.75 * Math.max(0, a)).toFixed(2));
      if (d.hot || v > 0.8) d.c.setAttribute("data-hot", "");
      else d.c.removeAttribute("data-hot");
    }
  }

  function text() {
    const i = info[on];
    let t = i.name;
    if (station !== null) {
      t += " · x = " + Math.round(station) + " mm";
      if (station < 0) t += " · agua a " + i.level(station).toFixed(0) + " mm";
      else if (station >= 100) t += " · lámina " + i.h(station).toFixed(1) + " mm · " + i.v(station).toFixed(2) + " m/s";
      else t += " · agua a " + i.level(station).toFixed(0) + " mm";
    } else t += " · retorno fuerte " + String(i.back).replace(".", ",") + " mL";
    if (readout.textContent !== t) readout.textContent = t;
  }

  function tick(now) {
    const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60;
    last = now;
    if (!still.matches && !paused) clock += dt * speed;
    draw();
    frame = visible ? requestAnimationFrame(tick) : 0;
  }
  const run = () => {
    if (!frame && visible) {
      last = 0;
      frame = requestAnimationFrame(tick);
    }
  };
  function choose(v) {
    on = v;
    fig.setAttribute("data-on", v);
    root.querySelectorAll("[data-pick]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.pick === v)));
    root.querySelectorAll("[data-row]").forEach((r) => (r.hidden = false));
    root.querySelectorAll("tr[data-row]").forEach((r) => r.setAttribute("data-on", String(r.dataset.row === v)));
    text();
    draw();
    moveMarker();
    run();
  }
  root.querySelectorAll("[data-pick]").forEach((b) => b.addEventListener("click", () => choose(b.dataset.pick)));
  const speedInput = root.querySelector("[data-speed]");
  const speedText = root.querySelector("[data-speed-text]");
  const setSpeed = () => {
    speed = Math.pow(10, +speedInput.value);
    speedText.textContent = "×" + speed.toFixed(speed < 1 ? 2 : 1).replace(".", ",") + " del tiempo real";
  };
  speedInput.addEventListener("input", setSpeed);
  setSpeed();
  const playBtn = root.querySelector("[data-play]");
  playBtn.addEventListener("click", () => {
    const p = playBtn.getAttribute("aria-pressed") === "true";
    playBtn.setAttribute("aria-pressed", String(!p));
    playBtn.textContent = p ? "Reproducir" : "Pausa";
    paused = p;
  });

  const surface = (v) => {
    const out = [];
    for (let x = -740; x <= 520; x += 10) out.push([x, info[v].level(x)]);
    return out;
  };
  const tops = {};
  for (const v of VAR) tops[v] = surface(v).map(([x, z]) => ({ x, z, s: iso([x, 0, z], P) }));
  function moveMarker() {
    if (station === null) {
      marker.setAttribute("opacity", "0");
      markerDot.setAttribute("opacity", "0");
      return;
    }
    const z = info[on].level(station);
    const bottom = info[on].bottom(station);
    const a = iso([station, 0, z], P);
    const b = iso([station, 0, bottom], P);
    marker.setAttribute("d", "M" + a[0].toFixed(1) + " " + a[1].toFixed(1) + "L" + b[0].toFixed(1) + " " + b[1].toFixed(1));
    markerDot.setAttribute("cx", a[0].toFixed(1));
    markerDot.setAttribute("cy", a[1].toFixed(1));
    marker.setAttribute("opacity", "1");
    markerDot.setAttribute("opacity", "1");
  }
  stage.addEventListener("pointermove", (e) => {
    const box = svg.getBoundingClientRect();
    const vx = ((e.clientX - box.left) / box.width) * DATA.f2.W;
    const vy = ((e.clientY - box.top) / box.height) * DATA.f2.H;
    let best = null;
    let bd = 1e9;
    for (const p of tops[on]) {
      const dd = Math.hypot(p.s[0] - vx, p.s[1] - vy);
      if (dd < bd) {
        bd = dd;
        best = p;
      }
    }
    station = bd < 60 ? best.x : null;
    moveMarker();
    text();
  });
  stage.addEventListener("pointerleave", () => {
    station = null;
    moveMarker();
    text();
  });
  stage.addEventListener("keydown", (e) => {
    const i = VAR.indexOf(on);
    if (e.key === "ArrowRight" || e.key === "ArrowDown") choose(VAR[Math.min(VAR.length - 1, i + 1)]);
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") choose(VAR[Math.max(0, i - 1)]);
    else if (e.key >= "1" && e.key <= "3") choose(VAR[+e.key - 1]);
    else return;
    e.preventDefault();
  });
  new IntersectionObserver((en) => {
    visible = en[en.length - 1].isIntersecting;
    if (visible) run();
  }, { rootMargin: "100px 0px" }).observe(stage);
  choose(on);
})();
