# Prototipo de conteo estilo Vaki (cámara lineal) — diseño completo

**Enfoque definitivo:** cámara lineal (line-scan) sobre plano inclinado transparente, con backlight continuo, tipo el sistema comercial Vaki. Unidad móvil con bombeo, tolva, separación de agua y PC/pantalla.

---

## 1. Principio de funcionamiento

1. Una **bomba de bajo cizallamiento** sube agua+larvas desde el estanque.
2. Descarga en un **cajón/tanque de entrada (stilling box)** por su **fondo**. Dentro, el agua **se calma**, atraviesa unos **tabiques enderezadores** y **rebosa por el vertedero** a todo lo ancho. Este cajón es clave: convierte un chorro turbulento de manguera en una lámina uniforme, y evita que la manguera cruce la zona de caída.
3. El agua pasa a la **bandeja ancha** que embuda hasta el ancho del canal, y baja por el **plano inclinado transparente (~35°)**; la gravedad da el movimiento.
4. En la zona de imagen, bajo un **cabezal óptico con capó** (que bloquea la luz solar y protege la óptica) van, a oscuras: la **ventana transparente** de la bandeja, la **cámara lineal** y la **iluminación**. La cámara capta una sola línea a lo ancho; el **backlight lineal continuo** ilumina desde el lado opuesto → cada larva se ve como silueta oscura.
5. La imagen 2D se forma con el movimiento del flujo; cada larva se cuenta al cruzar la línea.
6. Al pie del plano, una **malla de dewatering** separa el exceso de agua. El sistema tiene **dos salidas**:
   - **Salida intermedia (con válvula):** drena solo el **agua** separada → evita inundar la piscina destino.
   - **Salida final (manguera flexible):** lleva el **camarón** (+ poca agua) al destino. **Es la única salida de camarón** — todo el conteo sale por aquí, para que el número cuadre con lo entregado.
7. Un **PC industrial + pantalla táctil** ejecuta el conteo y lo muestra en vivo.

> El **cabezal óptico (capó)** es lo mismo que en la máquina de referencia: crea oscuridad controlada sobre la zona de imagen (como una caja negra) y protege cámara/óptica del agua, sol y polvo. La **válvula** de la salida intermedia también puede usarse como bypass/desvío durante el arranque.

---

## 2. Lista de materiales (BOM)

### Cámara, óptica y cómputo
| Ref | Componente | Modelo / valor orientativo |
|---|---|---|
| CAM | Cámara lineal **GigE Vision** 2048 px | Basler racer raL2048 o similar · ~$1000–2500 |
| LENTE | Lente para line-scan (C-mount/M42 según sensor) | ~$300–800 |
| PC | PC industrial (i5+) con NIC GigE dedicada (jumbo frames) | ~$500–1200 |
| HMI | Pantalla táctil industrial | ~$200–500 |
| CABLE | Ethernet Cat6 apantallado | según distancia |

### Iluminación (continua)
| Ref | Componente | Nota |
|---|---|---|
| LUZ | **Luz LINEAL continua** de alta potencia (line light / barra LED) ≥ ancho del canal | backlight; ~$200–600 |
| DRV | **Driver de corriente constante** (continuo) + disipador | según potencia |
| PSU | Fuente 24 V de alta potencia | consumo continuo |

### Hidráulica y mecánica
| Ref | Componente | Nota |
|---|---|---|
| BOMBA | **Bomba de bajo cizallamiento** (air-lift, tornillo/peristáltica, o gravedad/sifón) | ¡crítico! no dañar las larvas |
| CAJÓN | **Cajón/tanque de entrada (stilling box)** ~270 × 430 × 230 mm, con **tabiques enderezadores** y **vertedero** a todo el ancho | recibe la manguera por el fondo, calma el flujo y lo reparte en lámina |
| BANDEJA | Bandeja ancha que embuda de 430 → 150 mm | lleva la lámina al canal de conteo |
| PLANO | **Plano inclinado transparente** (acrílico/vidrio) + paredes laterales | zona de imagen; ~35° ajustable |
| CAPÓ | **Cabezal óptico / capó** sobre la zona de imagen | aloja cámara+luz+ventana; bloquea el sol y protege la óptica |
| MALLA | **Malla / rejilla de dewatering** al pie del plano | separa el exceso de agua tras el conteo |
| VÁLV | **Válvula** en la salida intermedia de agua | regula el drenaje; sirve de bypass en el arranque |
| SAL-A | **Salida intermedia**: tubería de drenaje de agua | solo agua |
| SAL-C | **Salida final**: manguera flexible de camarón al destino | única salida de camarón |
| BASTIDOR | Estructura inox/aluminio sobre ruedas | unidad móvil |
| MANGUERAS | Entrada/descarga | grado alimentario/marino |

### Opcionales
| Ref | Componente | Nota |
|---|---|---|
| CAUDAL | Sensor de caudal / encoder | fija la tasa de línea → evita distorsión |
| TORRE | Torre semáforo | estado operativo |

> **No lleva:** Pi Pico, driver MOSFET de pulsos, ni sincronía de µs. La luz es continua.

---

## 3. Parámetros de diseño

| Parámetro | Valor de partida |
|---|---|
| Ancho del canal | ~150 mm |
| Resolución a lo ancho | 150 mm / 2048 px ≈ **0,073 mm/px** |
| Espesor de lámina | 3–6 mm |
| Inclinación | ~35° (ajustable con niveladores) |
| Distancia de trabajo | `WD ≈ f · (1 + longitud_sensor / ancho_FOV)` |
| Tasa de línea | `velocidad_flujo / resolución` → ej. 0,6 m/s ÷ 0,073 mm ≈ **8,2 kHz** |
| Iluminación | backlight lineal continuo, alineado exacto con la línea |

---

## 4. Conexión (resumen)

**Datos/control:**
```
Cámara lineal ──GigE (Cat6)──► PC industrial ──HDMI/USB──► Pantalla táctil
Sensor de caudal ──(opcional)──► PC
PC ──control──► Bomba + relé (arranque/paro)
```
**Potencia (continua):**
```
Red AC ─► Fuente 24 V ─► Driver CC (continuo) ─► Luz LINEAL
Red AC ─► PC        Red AC ─► Bomba
```

---

## 5. Secuencia de armado

1. **Bastidor + plano inclinado**: montar el plano transparente en el bastidor con ángulo ajustable (~35°), con paredes laterales que contengan la lámina.
2. **Tolva + vertedero**: en la parte alta, con el labio a todo el ancho y nivelado → lámina uniforme.
3. **Bomba e hidráulica**: instalar bomba de bajo cizallamiento y mangueras de entrada.
4. **Backlight**: montar la luz lineal en el lado opuesto a la cámara (bajo/detrás del plano transparente), **alineada exactamente** con la línea que verá la cámara.
5. **Cámara lineal**: montar sobre soporte de ajuste fino (3 ejes), perpendicular al flujo, enfocada a la línea.
6. **Cabezal óptico (capó)**: cerrar la zona de imagen con un capó que aloje cámara+luz+ventana, bloquee la luz solar y proteja la óptica (dejar acceso para limpieza/ajuste).
7. **Dewatering y dos salidas** al pie del plano: montar la **malla** que separa el agua; la **salida intermedia con válvula** para drenar esa agua; y la **salida final (manguera flexible)** que lleva el camarón al destino.
8. **Cómputo**: PC industrial + pantalla; NIC GigE con jumbo frames; instalar SDK (pylon/Aravis) + OpenCV.
9. **Cableado de potencia**: fuente 24 V → driver CC → luz; AC a PC y bomba; tierra de seguridad.

---

## 6. Puesta en marcha y prueba

1. **Agua limpia primero**: con flujo sin larvas, ajustar foco y verificar que la línea iluminada coincide con la línea de la cámara (imagen brillante y nítida a lo ancho).
2. **Ajustar la lámina**: caudal de bomba + inclinación hasta lograr una lámina fina y pareja (3–6 mm), sin turbulencia en la zona de imagen.
3. **Fijar la tasa de línea**: empezar alto (p.ej. 10 kHz) y ajustar hasta que las larvas no salgan estiradas/comprimidas; o ligarla al sensor de caudal.
4. **Prueba de conteo**: pasar un lote conocido de larvas y comparar el conteo automático contra el conteo manual de referencia; calcular error %.
5. **Ajuste fino**: umbrales de detección, alineación, brillo del backlight, velocidad de flujo.

---

## 7. Riesgos y mitigaciones (específicos de este enfoque)

| Riesgo | Mitigación |
|---|---|
| **Daño a larvas** por la bomba | Bomba de bajo cizallamiento; o alimentación por gravedad/sifón; caudal suave |
| **Alineación cámara-línea-luz** delicada | Soporte de ajuste fino en 3 ejes; procedimiento de alineación con agua limpia |
| **Distorsión geométrica** si el caudal varía | Sensor de caudal/encoder para fijar la tasa de línea; o inclinación que dé velocidad estable |
| **Calor** de la luz continua | Disipador; unidad abierta (no sellada) lo tolera |
| **Costo alto por unidad** | Unidad móvil única (rotativa entre compuertas), como el modelo Vaki |
| **Biofouling / suciedad** del plano | Plano desmontable; limpieza entre lotes; corrección flat-field en software |

---

## 8. Diferencias clave vs. el enfoque estroboscópico (referencia)

| | Line-scan (este diseño) | Global Shutter + Estrobo |
|---|---|---|
| Electrónica de disparo | Ninguna (luz continua) | Pico + driver + sincronía µs |
| Cómputo | PC industrial | Raspberry Pi |
| Iluminación | Continua (calor) | Pulsada (frío) |
| Resolución / throughput | Muy alta / millones/h | Buena / 0,5–1 M/h |
| Costo por unidad | Alto (miles USD) | Bajo ($400–900) |
| Modelo de despliegue | Unidad móvil rotativa | Nodo fijo por compuerta |

Ver comparación completa en `comparacion_propuestas_A_vs_B.md`.

---

## 9. Modelo 3D

Archivo: **`modelo_3d_contador_vaki.scad`** (OpenSCAD, paramétrico, cotas en mm).

**Cómo usarlo:** abrir con OpenSCAD (gratuito) · `F5` vista rápida · `F6` render final · `F7` exportar **STL** para fabricación/impresión 3D.

**Parámetros principales** (editables al inicio del archivo):

| Parámetro | Valor | Qué controla |
|---|---|---|
| `bas_L / bas_W / bas_H` | 1200 / 500 / 700 | Dimensiones del bastidor |
| `perfil` | 40 | Perfil de aluminio T-slot 40×40 |
| `canal_w` | 150 | Ancho del canal (define la resolución: 150/2048 = 0,073 mm/px) |
| `canal_ang` | 35 | Inclinación del plano |
| `canal_L` | 560 | Longitud del canal |
| `camara_alt` | 400 | Distancia lente → lámina (lente 35 mm C-mount) |
| `img_dist` | 300 | Posición de la línea de imagen sobre el canal |

**Interruptores de vista:** `ver_bastidor`, `ver_hidraulica`, `ver_optica`, `ver_control`, `ver_capo`, `capo_corte`.

**Vistas renderizadas incluidas:**
- `vista_1_isometrica.png` — conjunto general
- `vista_2_lateral.png` — elevación lateral (muestra los 35° y el recorrido del flujo)
- `vista_3_interior.png` — sin capó: cámara, haz óptico y backlight visibles
- `vista_4_zona_imagen.png` — detalle de la zona de conteo

**Dimensiones generales de la máquina:** ~1,20 m (largo) × 0,50 m (ancho) × ~1,6 m (alto con capó), sobre ruedas.

---

## 10. Software (siguiente etapa)

- SDK del fabricante (pylon de Basler / **Aravis** open-source) para adquisición GigE Vision.
- Procesamiento en OpenCV: segmentación de silueta (umbral sobre fondo uniforme), conteo por cruce de línea, filtro por tamaño/forma para descartar mudas/detritos.
- (Opcional, tipo Vaki) detección por IA de pares de ojos para separar larvas pegadas.
- Interfaz en la pantalla táctil: conteo en vivo, histórico, exportación.
