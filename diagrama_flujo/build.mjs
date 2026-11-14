// Diagrama de flujo del contador de postlarvas: pagina HTML autonoma con tres figuras isometricas en vivo.
//   node build.mjs            -> diagrama_flujo.html
import { readFileSync, writeFileSync } from "node:fs";
import * as k from "./kit/iso-kit.mjs";
import { kitScript } from "./scripts/inline-kit.mjs";
import { FIG_CSS } from "./theme.mjs";
import { buildFig2, W2, H2, VARIANTS, rampRing, rampBottom } from "./fig2.mjs";
import { buildFig3 } from "./fig3.mjs";
import { runAudit } from "./scene.mjs";
import { buildFig1 } from "./fig1.mjs";
import * as G from "./kit/lathe.mjs";

const HERE = new URL(".", import.meta.url);
const d = JSON.parse(readFileSync(new URL("./data.json", HERE), "utf8"));
const read = (f) => readFileSync(new URL(f, HERE), "utf8");
const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ---------------------------------------------------------------- Figura 2
const f2 = buildFig2(d);
const NAMES = { original: "Muro de 90° con labio", circular: "Rampa circular (R = 60 mm), sin labio", parabola: "Rampa parabólica (115 mm), sin labio" };
const METRICS = {
  original: { back: 12.1, mod: 66.8, max: -0.47, dwell: "0,32 s", worst: "4,6 s", rear: 122, front: 108, h: 11.9, note: "t = 4 s, promedio de 2,5 a 4 s" },
  circular: { back: 0.8, mod: 16.9, max: -0.33, dwell: "0,20 s", worst: "2,2 s", rear: 118, front: 104, h: 12.6, note: "t = 4 s, promedio de 2,5 a 4 s" },
  parabola: { back: 0, mod: 0, max: null, dwell: "0,09 s", worst: "0,7 s", rear: 115, front: 100, h: 13.2, note: "t = 4 s, aún no estable (se está continuando hasta 6 s)" },
};
const TABLE_H = { original: [19.29, 15.85, 14.08, 12.87, 11.94], circular: [21.07, 16.86, 14.9, 13.58, 12.57], parabola: [22.17, 17.77, 15.64, 14.24, 13.18] };
const TABLE_V = { original: [0.99, 1.21, 1.37, 1.51, 1.63], circular: [0.94, 1.18, 1.35, 1.49, 1.62], parabola: [0.94, 1.18, 1.35, 1.49, 1.62] };
const XS = [100, 200, 300, 400, 500];
const crop = (L, x0) => {
  const i = L.findIndex((p) => p[0] > x0);
  if (i < 0) return null;
  const t0 = L[Math.max(0, i - 1)][3];
  const e = L.findIndex((p) => p[0] > 340);
  return L.slice(Math.max(0, i - 1), e < 0 ? L.length : e + 1).map((p) => [p[0], p[1], p[2], p[3] - t0]);
};
const thin = (lines, n, x0 = -340) => {
  const cut = lines.map((L) => (x0 === null ? L : crop(L, x0))).filter(Boolean);
  const step = Math.max(1, Math.floor(cut.length / n));
  return cut.filter((_, i) => i % step === 0).slice(0, n).map((L) => {
    const keep = [];
    let lastP = null;
    L.forEach((p, i) => {
      if (!lastP || Math.hypot(p[0] - lastP[0], p[1] - lastP[1], p[2] - lastP[2]) >= 12 || i === L.length - 1) {
        keep.push(p);
        lastP = p;
      }
    });
    return [keep.map((p) => Math.round(p[0])), keep.map((p) => Math.round(p[1])), keep.map((p) => Math.round(p[2])), keep.map((p) => Math.round(p[3] * 100) / 100)];
  });
};
const D2 = {
  P: f2.P, W: W2, H: H2, start: "parabola", variants: VARIANTS,
  lines: Object.fromEntries(VARIANTS.map((v) => [v, thin(d.cfd[v].lineas, 80)])),
  corner: Object.fromEntries(VARIANTS.map((v) => [v, thin(d.cfd[v].esquina, 24, null)])),
  info: Object.fromEntries(VARIANTS.map((v) => [v, {
    name: NAMES[v], back: METRICS[v].back,
    nivel: d.cfd[v].nivel, ring: rampRing(v).slice(0, v === "original" ? 4 : -1),
    hx: XS.map((x, i) => [x, TABLE_H[v][i]]), vx: XS.map((x, i) => [x, TABLE_V[v][i]]),
  }])),
};

const body2 = f2.body;
const svg2 = k.figureSvg({
  width: W2, height: H2,
  label: "Corte longitudinal del cajón de entrada del contador, con su rampa de subida a la cresta, la malla y el inicio del canal. Partículas que siguen las líneas de corriente calculadas muestran por dónde pasa el agua.",
  body: `<g class="fig2" data-on="parabola">${body2}</g>`,
});
const rows2 = VARIANTS.map((v) => {
  const m = METRICS[v];
  return `<tr data-row="${v}"><th scope="row">${esc(NAMES[v])}</th><td class="num">${String(m.back).replace(".", ",")} mL</td><td class="num">${String(m.mod).replace(".", ",")} mL</td><td class="num">${m.dwell}</td><td class="num">${m.worst}</td><td class="num">${m.rear} / ${m.front} mm</td><td class="num">${String(m.h).replace(".", ",")} mm</td></tr>`;
}).join("");
const fig2 = k.plateHtml({
  fig: "Fig 2",
  title: "Cajón, rampa y malla",
  hint: "Pasa el cursor para leer · 1, 2, 3 cambian de rampa",
  readout: "",
  keys: [
    { mark: "lit", label: "La rampa de la cresta (lo que cambió)" },
    { mark: "raised", label: "Malla de acero, 30 mesh" },
    { mark: "dashed", label: "Acrílico transparente" },
    { mark: "blue", label: "Agua y partículas del flujo calculado" },
  ],
  caption:
    "Corte por el plano de simetría del cajón. Las partículas siguen las líneas de corriente del flujo medio del CFD (OpenFOAM, 10 L/s). Con el muro de 90° se forma un remolino en la esquina; con la rampa el agua sube siguiendo la curva y casi no queda agua detenida.",
  body: `<div class="iso-stage" tabindex="0" role="group" aria-label="Corte del cajón: flechas o 1, 2 y 3 cambian la rampa">${svg2}</div>`,
});
const controls2 = `<div class="ctl" role="group" aria-label="Controles de la figura 2">
  <span class="grp" role="group" aria-label="Forma de la rampa"><button class="btn" type="button" data-pick="original" aria-pressed="false">1 · Muro de 90°</button><button class="btn" type="button" data-pick="circular" aria-pressed="false">2 · Rampa circular</button><button class="btn" type="button" data-pick="parabola" aria-pressed="true">3 · Rampa parabólica</button></span>
  <span class="grp"><button class="btn" type="button" data-play aria-pressed="true">Pausa</button><label>Velocidad <input type="range" data-speed min="-1.2" max="0.8" step="0.05" value="0.1" aria-label="Velocidad de la animación"></label><span class="mono" data-speed-text></span></span>
</div>
<div class="tbl"><table><caption>Lo que midió el cálculo en cada versión (10 L/s)</caption><thead><tr><th scope="col">Versión</th><th scope="col">Retorno fuerte en la esquina</th><th scope="col">Retorno moderado</th><th scope="col">Tiempo medio de una partícula en la esquina</th><th scope="col">Peor caso</th><th scope="col">Nivel del cajón (atrás / delante)</th><th scope="col">Lámina a 0,5 m</th></tr></thead><tbody>${rows2}</tbody></table><p class="note">El diseño parabólico se calculó hasta t = 4 s y su nivel todavía bajaba; el cálculo se sigue hasta 6 s para fijarlo. Los otros dos están a t = 4 s.</p></div>`;


// ---------------------------------------------------------------- Figura 3
const f3 = buildFig3();
const sC = d.canal.s_conteo;
const PROF3 = {};
for (const [Q, p] of Object.entries(d.perfil1d)) {
  let i = 0;
  while (i < p.s.length - 1 && p.s[i] < sC) i++;
  PROF3[Q] = { h: p.h[i], V: p.V[i], Fr: p.Fr[i] };
}
const slider = (id, label, min, max, step, value, unit) => `<label>${label} <input type="range" data-${id} min="${min}" max="${max}" step="${step}" value="${value}" aria-label="${label}"><span class="mono" data-label="${id}">${value}</span>${unit ? `<span>${unit}</span>` : ""}</label>`;
const fig3 = k.plateHtml({
  fig: "Fig 3",
  title: "Ventana de conteo, en el modelo 3D",
  hint: "Arrastra: girar · clic derecho o Mayús: mover · rueda: zoom",
  readout: "",
  keys: [
    { mark: "lit", label: "Larvas dentro del campo de la cámara" },
    { mark: "dashed", label: "Campo de la cámara: todo el ancho del canal" },
    { mark: "blue", label: "Lámina de agua sobre el tramo inclinado" },
  ],
  caption:
    "Es el tramo inclinado del modelo de Fusion 360: la ventana de acrílico, el backlight infrarrojo debajo, el vidrio protector y la cámara lineal con su lente. El abanico ámbar es el campo de la cámara, que cubre los 504 mm del canal. La pantalla de la esquina es lo que ve la cámara en cada destello. El movimiento está en cámara lenta; los números de la tabla son los reales a la velocidad de la lámina.",
  body: `<div class="iso-stage" data-view>${f3.body}</div>`,
});
const controls3 = `<div class="ctl" role="group" aria-label="Controles de la figura 3">
  ${slider("q", "Caudal", 4, 15, 1, 10, "L/s")}
  ${slider("conc", "Larvas por litro", 5, 20, 1, 10, "")}
  ${slider("pulse", "Pulso del destello", 20, 125, 5, 60, "µs")}
  ${slider("fps", "Cuadros por segundo", 30, 120, 5, 60, "")}
  ${slider("fov", "Ancho que ve la cámara", 150, 504, 6, 504, "mm")}
  <span class="grp" role="group" aria-label="Vista"><button class="btn" type="button" data-zoom="in" aria-label="Acercar">+</button><button class="btn" type="button" data-zoom="out" aria-label="Alejar">−</button>${[["ventana", "Ventana"], ["arriba", "Desde arriba"], ["lado", "De lado"], ["camara", "Cámara"]].map(([v, t]) => `<button class="btn" type="button" data-view-btn="${v}" aria-pressed="${v === "ventana"}">${t}</button>`).join("")}</span>
  <span class="grp"><label>Cámara lenta ×1/<input type="range" data-slow min="1.5" max="3" step="0.05" value="2.1" aria-label="Factor de cámara lenta"><span class="mono" data-label="slow">126</span></label><button class="btn" type="button" data-play aria-pressed="true">Pausa</button></span>
</div>
<div class="tbl"><table><caption>Lo que implica cada ajuste, a la velocidad real de la lámina</caption><tbody>
<tr><th scope="row">Lámina en la línea de conteo</th><td data-out="h"></td></tr>
<tr><th scope="row">Velocidad del agua</th><td data-out="V"></td></tr>
<tr><th scope="row">Campo de la cámara</th><td data-out="field"></td></tr>
<tr><th scope="row">Lente necesario para cubrir el canal</th><td data-out="lens"></td></tr>
<tr><th scope="row">Resolución en la lámina</th><td data-out="res"></td></tr>
<tr><th scope="row">Desenfoque por movimiento durante el pulso</th><td data-out="blur"></td></tr>
<tr><th scope="row">Cuadros en los que sale cada larva</th><td data-out="frames"></td></tr>
<tr><th scope="row">Larvas en el campo a la vez</th><td data-out="inview"></td></tr>
<tr><th scope="row">Larvas que cruzan la franja visible</th><td data-out="rateFov"></td></tr>
<tr><th scope="row">Larvas en todo el canal</th><td data-out="rateAll"></td></tr>
<tr><th scope="row">Cámara lenta de la animación</th><td data-out="slow"></td></tr>
</tbody></table><p class="note">Óptica de referencia: cámara de obturador global (Sony IMX296, 1456 px de ancho), lente C-mount de 12 mm a unos 44 cm sobre el agua, f/4, backlight de 42 LED a 850 nm con difusor. Se supone velocidad pareja a lo ancho (variación de 1 a 2 % en el CFD). Una línea en ámbar indica un ajuste fuera de lo cómodo. El largo del campo en el sentido del flujo es el de la ventana y el backlight del modelo; el lente se calcula con el sensor de 5,02 mm de ancho.</p></div>`;


// ---------------------------------------------------------------- Figura 1
const f1 = buildFig1(d);
const D1 = f1.D1;
const fig1 = k.plateHtml({
  fig: "Fig 1",
  title: "El circuito del agua, sobre el modelo 3D",
  hint: "Arrastra: girar · clic derecho o Mayús: mover · rueda: zoom · doble clic: enfocar",
  readout: "",
  keys: [
    { mark: "blue", label: "Puntos azules: el agua" },
    { mark: "lit", label: "Puntos ámbar: larvas" },
    { mark: "dashed", label: "Acrílico y mangueras translúcidos" },
  ],
  caption: "Visor 3D con las mallas del modelo de Fusion 360 tal como las genera el script (90 piezas, con la unión rampa a embudo y la tapa del sensor). El agua de los estanques, el cajón y el canal sigue las alturas del cálculo; la lámina sobre el canal es el perfil 1D calibrado con el CFD. Los puntos son una ilustración del flujo medio: no son larvas reales.",
  body: `<div class="iso-stage" data-view>${f1.body}</div>`,
});
const controls1 = `<div class="ctl" role="group" aria-label="Controles de la figura 1">
  ${slider1("q", "Caudal", 4, 15, 1, 10, "L/s")}
  ${slider1("conc", "Larvas por litro", 5, 20, 1, 10, "")}
  <span class="grp" role="group" aria-label="Vista"><button class="btn" type="button" data-zoom="in" aria-label="Acercar">+</button><button class="btn" type="button" data-zoom="out" aria-label="Alejar">−</button>${[["todo", "Todo"], ["estanque", "Estanque y bomba"], ["caja", "Cajón y rampa"], ["ventana", "Ventana y cámara"], ["embudo", "Embudo y salida"]].map(([v, t]) => `<button class="btn" type="button" data-view-btn="${v}" aria-pressed="${v === "todo"}">${t}</button>`).join("")}</span>
  <span class="grp"><label>Velocidad de la animación <input type="range" data-speed min="-1" max="0.6" step="0.05" value="0" aria-label="Velocidad de la animación"><span class="mono" data-label="speed">×1,0</span></label><button class="btn" type="button" data-play aria-pressed="true">Pausa</button></span>
</div>
<div class="tbl"><table><caption>Tramo por tramo, con el caudal elegido</caption><thead><tr><th scope="col">Tramo</th><th scope="col">Velocidad</th><th scope="col">Qué hace</th></tr></thead><tbody data-stations></tbody></table></div>`;
function slider1(id, label, min, max, step, value, unit) {
  return `<label>${label} <input type="range" data-${id} min="${min}" max="${max}" step="${step}" value="${value}" aria-label="${label}"><span class="mono" data-label="${id}">${value}</span>${unit ? `<span>${unit}</span>` : ""}</label>`;
}

// ---------------------------------------------------------------- Pagina
const PAGE_CSS = `
*{box-sizing:border-box}
#app{min-height:100vh;background:var(--anatomy-page);color:var(--anatomy-text);font:15px/1.65 "IBM Plex Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased;padding-block:1px}
.page{width:min(1040px,100% - 32px);margin:40px auto 90px}
h1{font-size:clamp(1.8rem,4.2vw,2.5rem);line-height:1.12;letter-spacing:-.015em;margin:6px 0 14px;color:var(--anatomy-strong);font-weight:600;text-wrap:balance}
h2{font-size:1.3rem;margin:48px 0 6px;color:var(--anatomy-strong);font-weight:600;text-wrap:balance}
.eyebrow{font:500 11px/1.3 var(--anatomy-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--anatomy-muted)}
.lead{max-width:68ch;font-size:1.06rem;color:var(--anatomy-text)}
.prose{max-width:70ch}
.tbl{overflow-x:auto;margin:8px 0 0}
table{border-collapse:collapse;width:100%;min-width:640px;font-size:13px}
caption{text-align:left;font:500 11px/1.4 var(--anatomy-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--anatomy-muted);padding:6px 0}
th,td{padding:8px 10px;border-bottom:1px solid var(--anatomy-faint);text-align:left;vertical-align:top}
thead th{font:500 11px/1.3 var(--anatomy-mono);letter-spacing:.04em;color:var(--anatomy-muted);border-bottom:1px solid var(--anatomy-lo)}
tbody th{font-weight:500;color:var(--anatomy-strong)}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr[data-on="true"] th,tr[data-on="true"] td{background:var(--anatomy-shade-3)}
.steps{margin:18px 0 0;padding:0;list-style:none;display:grid;gap:0;counter-reset:s;border:1px solid var(--anatomy-faint);max-width:70ch}
.steps li{counter-increment:s;padding:9px 14px 9px 50px;border-bottom:1px solid var(--anatomy-faint);position:relative}
.steps li:last-child{border-bottom:0}
.steps li::before{content:counter(s);position:absolute;left:14px;top:8px;width:24px;height:24px;border:1px solid var(--anatomy-lo);border-radius:50%;font:500 12px/22px var(--anatomy-mono);text-align:center;color:var(--anatomy-text)}
.steps b{color:var(--anatomy-strong);font-weight:600}
.note{font-size:12.5px;color:var(--anatomy-muted);max-width:80ch}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--anatomy-lo);font-size:12.5px;color:var(--anatomy-muted);display:grid;gap:6px}
`;
const FONT = `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap">`;
const THEME_JS = `
(function(){
  const b = document.getElementById("app"), h = document.documentElement;
  const pick = () => { const t = h.getAttribute("data-theme"); return t === "dark" || t === "light" ? t : matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"; };
  const apply = () => b.setAttribute("data-theme", pick());
  apply();
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", apply);
  new MutationObserver(apply).observe(h, { attributes: true, attributeFilter: ["data-theme"] });
})();`;

const main = `
<div class="eyebrow">Contador óptico de postlarvas · diseño de flujo</div>
<h1>Cómo se mueve el agua hasta la cámara</h1>
<p class="lead">El agua con larvas sale del estanque, se frena en el cono, se reparte en el cajón, sube por la rampa, cruza la malla y baja por un canal en lámina delgada hasta la ventana, donde una cámara cuenta las siluetas. Las tres figuras de esta página se mueven con datos del modelo: el cálculo del flujo (CFD con OpenFOAM) y el perfil 1D del canal.</p>
<ol class="steps">
  <li><b>Bombear.</b> La bomba y su variador fijan el caudal, de 4 a 15 L/s (diseño: 10 L/s).</li>
  <li><b>Calmar.</b> El cono y el cajón bajan el agua de 1,2 a 0,2 m/s sin choques; el deflector la reparte a lo ancho.</li>
  <li><b>Nivelar.</b> La rampa y la cresta entregan una lámina pareja sobre la malla de acero.</li>
  <li><b>Acelerar.</b> El canal inclinado y el arco la adelgazan a unos 9 mm y la llevan a más de 2 m/s.</li>
  <li><b>Mirar.</b> Un destello infrarrojo congela las larvas y la cámara las cuenta.</li>
</ol>
<section id="f1"><h2>De punta a punta</h2><p class="prose">Es el modelo 3D del prototipo, pieza por pieza, con el agua como una nube de puntos que sigue el recorrido real: estanque, bomba, cono, cajón, rampa, canal, embudo y piscina de destino. Mueve el caudal, gira, mueve y acerca con el ratón, el dedo o los botones y mira qué cambia. Cada punto ámbar es una larva (ilustrativa).</p><div id="fig1">${fig1}${controls1}</div></section>
<section id="f2"><h2>El cajón: de dónde sale una lámina pareja</h2><p class="prose">Es el tramo que más cambió. Elige una rampa y mira cómo cambia el recorrido de las partículas cerca de la esquina de la cresta (puntos ámbar).</p><div id="fig2">${fig2}${controls2}</div></section>
<section id="f3"><h2>La ventana de conteo: qué ve la cámara</h2><p class="prose">Es la parte inclinada del modelo donde se cuentan las larvas. Gira la vista, cambia el caudal, el pulso o los cuadros por segundo y mira qué pasa con el desenfoque y con cuántas veces se ve cada larva. El abanico ámbar cubre todo el ancho del canal.</p><div id="fig3">${fig3}${controls3}</div></section>
<section id="respaldo"><h2>Qué respalda cada cifra</h2>
<div class="tbl"><table><thead><tr><th scope="col">Dato</th><th scope="col">De dónde sale</th><th scope="col">Estado</th></tr></thead><tbody>
<tr><th scope="row">Lámina y velocidad en el canal</th><td>Perfil 1D con Manning n = 0,008, calibrado con el CFD (a 0,5 m de la cresta coincide dentro de 2 a 5 %)</td><td>Respaldado</td></tr>
<tr><th scope="row">Recorrido del agua en el cajón y la rampa</th><td>Líneas de corriente del flujo medio del CFD (1,6 millones de celdas, promedio de 2,5 a 4 s)</td><td>Respaldado</td></tr>
<tr><th scope="row">Rampa parabólica</th><td>El mismo cálculo, aún sin llegar a un nivel estable en el cajón</td><td>En curso (hasta 6 s)</td></tr>
<tr><th scope="row">Velocidad en mangueras, cono y deflector</th><td>Caudal dividido por el área de la sección, y CFD bajo el deflector (0,29 m/s)</td><td>Respaldado</td></tr>
<tr><th scope="row">Drenaje de la malla de acero</th><td>El CFD la trata como pared cerrada; el drenaje real no está medido</td><td>Por medir en banco</td></tr>
<tr><th scope="row">Óptica, destello y cuadros</th><td>Referencia de la cámara IMX296 con lente de 12 mm; las fórmulas de la tabla son directas</td><td>Referencia, se valida en la maqueta</td></tr>
<tr><th scope="row">Ancho que ve la cámara</th><td>180 mm en la referencia de óptica; el canal mide 504 mm</td><td>Por decidir</td></tr>
<tr><th scope="row">Larvas</th><td>Los puntos siguen el flujo medio; no modelan a la larva real ni su reacción al agua</td><td>Ilustrativo</td></tr>
</tbody></table></div></section>
<footer><span>Datos: <code>cfd_3d/resultados</code> (p2_medio_grueso, p2_rampa_sinlabio, p2_rampa_parabola), <code>simulacion_flujo</code>, el script de Fusion 360 y las notas de óptica y backlight del proyecto.</span><span>La Figura 1 usa las mallas del modelo de Fusion 360; los estanques, la bomba, el variador y las mangueras son piezas de propuesta del modelo, con medidas tentativas.</span></footer>
`;
const THREE_JS = read("vendor/three.min.js").replace(/<\/(script)/gi, "<\\/$1");
const SCRIPT = kitScript() + `\nconst DATA = ${JSON.stringify({ f1: D1, f2: D2, f3: { ...f3.data, prof: PROF3 } })};\n` + read("live1.js") + "\n" + read("live2.js") + "\n" + read("live3.js");
const BODY_CSS = `body{margin:0;background:#f2f2ef}@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) body{background:#0b0b0b}}:root[data-theme="dark"] body{background:#0b0b0b}`;
const TITLE = "Diagrama de flujo del contador";
const FRAG = `<title>${TITLE}</title>${FONT}<style>${BODY_CSS}${k.ISO_CSS}${FIG_CSS}${PAGE_CSS}</style><div id="app" class="iso" data-theme="light"><main class="page">${main}</main></div><script>${THEME_JS}</script><script>${THREE_JS}</script><script type="module">${SCRIPT.replace(/<\/(script)/gi, "<\\/$1")}</script>`;
const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>${FRAG}</body></html>`;
writeFileSync(new URL("./diagrama_flujo.html", HERE), html);
writeFileSync(new URL("./diagrama_flujo_artifact.html", HERE), FRAG);
console.log("diagrama_flujo.html", (html.length / 1e6).toFixed(2), "MB");
if (process.argv.includes("--audit")) {
  const only = (process.argv.find((a) => a.startsWith("--only=")) || "").slice(7);
  const want = (n) => !only || only.split(",").includes(n);
  let fails = 0;
  if (want("2")) for (const v of VARIANTS) fails += runAudit("Figura 2, rampa " + v, f2.scenes[v].R, f2.P, {});
  console.log(fails ? "\nauditoria con " + fails + " problemas" : "\nauditoria pasada");
  process.exitCode = fails ? 1 : 0;
}
