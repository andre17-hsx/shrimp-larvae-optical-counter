// Estilos propios del diagrama (el agua, el vidrio, las variantes) sobre los tokens del kit.
export const FIG_CSS = `
.iso{--water:#0d8aa3;--water-ink:#0b7a8c;--ptl:#0a5f70;--amber:#b86a00}
.iso[data-theme="dark"]{--water:#35b6cf;--water-ink:#53c6dc;--ptl:#9fe4f2;--amber:#ffb454}
.iso .glass .iso-fill{fill:none}
.iso .glass .iso-shade,.iso .glass .iso-top{opacity:.38}
.iso .cone .iso-fill{fill:var(--anatomy-paper)}
.iso .water-sec{fill:var(--water);opacity:.26;stroke:none}
.iso .water-top{fill:var(--water);opacity:.16;stroke:none}
.iso .water-top[data-steep]{opacity:.32}
.iso .water-cone{fill:var(--water);opacity:.2;stroke:none}
.iso .water-edge{fill:none;stroke:var(--water-ink);stroke-width:1.1;stroke-linejoin:round;stroke-linecap:round}
.iso .fig2 [data-v]{display:none}
.iso .fig2[data-on="original"] [data-v="original"],.iso .fig2[data-on="circular"] [data-v="circular"],.iso .fig2[data-on="parabola"] [data-v="parabola"]{display:inline}
.iso .pt{fill:var(--ptl);stroke:none}
.iso .pt[data-hot]{fill:var(--amber)}
.iso .marker{stroke:var(--amber);stroke-width:1;fill:none;stroke-dasharray:3 3}
.iso .marker-dot{fill:var(--amber);stroke:none}
.iso .ctl{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:14px 0 4px;font-size:13px;color:var(--anatomy-text)}
.iso .ctl .grp{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.iso .btn{font:inherit;font-size:12.5px;padding:6px 11px;border:1px solid var(--anatomy-lo);background:var(--anatomy-card);color:var(--anatomy-strong);cursor:pointer;border-radius:0}
.iso .btn:hover{border-color:var(--anatomy-mid)}
.iso .btn[aria-pressed="true"]{background:var(--anatomy-strong);color:var(--anatomy-card);border-color:var(--anatomy-strong)}
.iso .btn:focus-visible,.iso input:focus-visible,.iso .iso-stage:focus-visible{outline:2px solid var(--water-ink);outline-offset:2px}
.iso input[type=range]{accent-color:var(--water-ink);min-width:150px}
.iso .mono{font-family:var(--anatomy-mono);font-variant-numeric:tabular-nums}
.iso .iso-stage{position:relative;touch-action:pan-y}
.iso .larva{fill:none;stroke:var(--anatomy-hi);stroke-width:1.4;stroke-linecap:round}
.iso .larva[data-in="1"]{stroke:var(--amber);stroke-width:1.9}
.iso .flash-face{fill:var(--amber);stroke:none}
.iso .lamp{fill:var(--amber);stroke:var(--anatomy-lo);stroke-width:.5}
.iso .hood-face{fill:var(--anatomy-shade-1);opacity:.3;stroke:none}
.iso .hood-face[data-near]{opacity:.14}
.iso .scr-bg{fill:#0b0d10}
.iso .scr-frame{fill:none;stroke:var(--anatomy-lo);stroke-width:.8}
.iso .scr-ir{fill:#c9d0cb}
.iso .scr-larva{fill:#15181a}
.iso .scr-box{fill:none;stroke:var(--amber);stroke-width:.7}
.iso .scr-text{fill:#9aa4ac;font-family:var(--anatomy-mono)}
.iso .water3 .iso-fill{fill:var(--water);opacity:.2}
.iso .water3 .iso-shade,.iso .water3 .iso-top{opacity:.22}
.iso .water3 .iso-edge{stroke:var(--water-ink)}
.iso .ctl label{display:inline-flex;gap:6px;align-items:center}
.iso .ctl .mono{min-width:3.2em;text-align:right}
.iso tr[data-warn="true"] td{color:var(--amber)}
.iso .water1 .iso-fill{fill:var(--water);opacity:.22}
.iso .water1 .iso-shade,.iso .water1 .iso-top{opacity:.2}
.iso .water1 .iso-edge{stroke:var(--water-ink);opacity:.7}
.iso .ribbon-side{fill:var(--water);opacity:.55;stroke:var(--water-ink);stroke-width:.6}
.iso .ribbon-top{fill:var(--water);opacity:.3;stroke:none}
.iso .pt.larv{fill:var(--amber);stroke:var(--anatomy-card);stroke-width:.6}
.iso tr[data-on="true"] th,.iso tr[data-on="true"] td{background:var(--anatomy-shade-3)}
.iso .f1box{position:relative;overflow:hidden;width:100%}
.iso .f1box canvas{position:absolute;left:0;top:0;width:100%;height:100%;touch-action:none;cursor:grab;display:block}
.iso .f3box{position:relative;overflow:hidden;width:100%}
.iso .f3box canvas.f3gl{position:absolute;left:0;top:0;width:100%;height:100%;touch-action:none;cursor:grab;display:block}
.iso .f3box canvas.f3cam{position:absolute;right:10px;bottom:10px;border:1px solid var(--anatomy-lo);background:#0b0d10;pointer-events:none}
.iso .f1ring{position:absolute;left:0;top:0;width:18px;height:18px;border:2px solid var(--amber);border-radius:50%;pointer-events:none}
@media (max-width:640px){
.iso .iso-plate{overflow:hidden;padding:44px 8px 96px}
.iso .iso-plate .iso-svg{width:132%;margin-left:-16%}
.iso .iso-plate-corner[data-corner="readout"],.iso .iso-plate-corner[data-corner="hint"]{position:absolute;left:0;right:0;white-space:normal;text-align:left;bottom:auto}
.iso .iso-plate-corner[data-corner="hint"]{top:auto;bottom:34px}
.iso .iso-plate-corner[data-corner="readout"]{bottom:0}
.iso .iso-plate-corners{inset:12px}
}
`;
