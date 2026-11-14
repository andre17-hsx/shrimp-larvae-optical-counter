// Figura 3: la ventana de conteo sobre el modelo REAL (la parte inclinada del canal donde esta la ventana de acrilico, el
// backlight IR debajo, el vidrio protector y la camara lineal con su lente). Visor 3D (three.js) con las mismas mallas que la
// Figura 1 (el JSON de mallas viene en la Figura 1); aqui solo se calcula la geometria local de la ventana.
import fs from "node:fs";
import { topZ } from "./fig1.mjs";

const model = JSON.parse(fs.readFileSync(new URL("./modelo.json", import.meta.url), "utf8"));
const bbox = (name) => {
  const b = model.bodies.find((x) => x.n.startsWith(name));
  const lo = [1e9, 1e9, 1e9];
  const hi = [-1e9, -1e9, -1e9];
  for (let i = 0; i < b.v.length; i += 3) for (let a = 0; a < 3; a++) {
    lo[a] = Math.min(lo[a], b.v[i + a]);
    hi[a] = Math.max(hi[a], b.v[i + a]);
  }
  return { lo, hi };
};

export const BED = { hw: 252 };

export function buildFig3() {
  const win = bbox("PROPUESTA_ventana_acrilico");
  const bl = bbox("PROPUESTA_backlight_IR");
  const lens = bbox("PROPUESTA_lente");
  const names = ["fondo_tobogan", "PROPUESTA_ventana_acrilico"];
  const xc = (win.lo[0] + win.hi[0]) / 2;
  const zA = topZ(names, xc + 70, 0);
  const zB = topZ(names, xc - 70, 0);
  const theta = Math.atan2(zA - zB, 140); // el canal baja hacia -X
  const zc = topZ(names, xc, 0);
  const winLen = (win.hi[0] - win.lo[0]) / Math.cos(theta); // largo de la ventana a lo largo de la pendiente
  const blLen = (bl.hi[0] - bl.lo[0]) / Math.cos(theta);
  const lensP = [(lens.lo[0] + lens.hi[0]) / 2, 0, lens.lo[2]];
  // distancia de la lente al lecho, medida sobre la normal del canal
  const n = [-Math.sin(theta), 0, Math.cos(theta)];
  const d = [lensP[0] - xc, 0, lensP[2] - zc];
  const lensH = d[0] * n[0] + d[2] * n[2];
  const data = {
    win: { c: [xc, 0, zc], theta, len: winLen, blLen, hw: BED.hw, blHalf: (bl.hi[1] - bl.lo[1]) / 2 },
    lens: lensP,
    lensH,
  };
  console.log("figura 3: pendiente %s deg, ventana %s mm, backlight %s mm, lente a %s mm del lecho", ((theta * 180) / Math.PI).toFixed(1), winLen.toFixed(0), blLen.toFixed(0), lensH.toFixed(0));
  const body = `<div class="f3box" style="aspect-ratio:16/10"><canvas class="f3gl" role="img" aria-label="Visor 3D de la ventana de conteo sobre el modelo del prototipo: el tramo inclinado del canal con una lámina delgada de agua, la ventana de acrílico con el backlight infrarrojo debajo, el vidrio protector y la cámara lineal con su lente arriba. Un abanico ámbar muestra el campo de la cámara, que cubre todo el ancho del canal."></canvas><canvas class="f3cam" aria-label="Imagen de la cámara: siluetas oscuras de larvas sobre fondo claro"></canvas></div>`;
  return { body, data };
}
