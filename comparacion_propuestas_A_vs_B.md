# Comparación de propuestas para conteo óptico de larvas

Documento de apoyo para presentar a la empresa las dos arquitecturas evaluadas.

- **Propuesta A — Global Shutter + Estroboscopia** (arquitectura de la propuesta técnica actual)
- **Propuesta B — Line-scan / cámara lineal** (principio del referente comercial Vaki)

Ambas usan el **mismo canal abierto de lámina delgada** y el mismo principio de retroiluminación (silueta). Difieren en cámara, iluminación, cómputo y electrónica.

---

## Tabla comparativa

| Dimensión | A · Global Shutter + Estrobo | B · Line-scan |
|---|---|---|
| Cámara | ✓ GS IMX296 (~$70) | ✗ Lineal GigE (~$1000–2500) |
| Óptica | ✓ C-mount 12 mm (económica) | ✗ Lente line-scan (cara) |
| Iluminación | LED IR **pulsado** (µs) | LED lineal **continuo** + disipador |
| Cómputo | ✓ Raspberry Pi 5 | ✗ PC industrial (no Pi) |
| Electrónica de disparo | ✗ Pico + driver + sincronía µs | ✓ Ninguna (luz siempre ON) |
| Consumo / calor | ✓ Muy bajo (duty 0,25%) | ✗ Alto (luz continua) |
| Resolución por larva | Buena (0,12 mm/px) | ✓ Altísima (0,088 mm/px) |
| Throughput (caudal) | 0,5–1 millón/h | ✓ Millones/h |
| Variación de caudal | ✓ Absorbida por tracking | ✗ Distorsiona (necesita encoder) |
| Puesta a punto | Calibrar la sincronía | ✗ Alineación línea-luz delicada |
| Costo por nodo | ✓ ~$400–900 | ✗ Miles de USD |
| Escala a N compuertas | ✓ Sí (permanente por compuerta) | ✗ No económico (unidad móvil) |

✓ = ventaja · ✗ = desventaja

---

## Diferencia conceptual clave

- **A (estrobo):** cámara de área que congela el movimiento con un flash de µs. Requiere **sincronizar** cámara y LED con precisión de microsegundos (por eso el Pi Pico). A cambio, la iluminación pulsa con duty ~0,25 % → casi no consume ni calienta.
- **B (line-scan):** cámara de una sola línea; la imagen 2D se forma con el movimiento del flujo. **No** requiere sincronía de µs (la luz está siempre encendida), pero esa luz continua consume y calienta, y hace falta un PC industrial para el alto flujo de datos.

---

## Recomendación

| Objetivo de la operación | Propuesta recomendada |
|---|---|
| Cubrir **muchas compuertas** de forma permanente y a bajo costo | **A · Global Shutter + Estrobo** |
| Caudales de nursery (0,5–1 M/h) por compuerta | **A** |
| Instalación sellada (bajo calor/consumo) | **A** |
| **Un único punto** con caudal masivo (millones/h) | **B · Line-scan** |
| **Máxima resolución** (separar larvas pegadas, medir talla/biomasa) | **B** |
| Unidad móvil rotativa entre compuertas | **B** |

**Conclusión:** para el objetivo declarado del proyecto —cobertura permanente y distribuida de múltiples compuertas al menor costo por punto— la **Propuesta A** es la más adecuada. La **Propuesta B** queda justificada solo si en el futuro se requiere un punto de caudal masivo o medición de talla de alta precisión, alineado con lo que ofrece el equipo comercial de referencia.

---

## Archivos relacionados

- Propuesta A: `hito_a_guia_montaje.md`, `optica_camara_lente_referencia.md`, `sincronia_camara_led_referencia.md`, `banco_led_ir_referencia.md`, `firmware_pico_hito_a.py`
- Propuesta B: `linescan_bom_y_prueba.md`
- Canal común: `plano_canal_abierto_medidas.md`
