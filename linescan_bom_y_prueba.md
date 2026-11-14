# Propuesta B — Line-scan (cámara lineal): BOM y montaje de prueba

**Enfoque:** cámara lineal (una fila de píxeles) + luz lineal continua. La imagen 2D se forma con el movimiento del flujo. Es el principio del referente comercial **Vaki**.
**Objetivo del prototipo:** validar conteo por línea a alta resolución sobre el mismo canal abierto.

---

## 1. Lista de materiales

### Componentes principales
| Ref | Componente | Modelo / valor orientativo | Función |
|---|---|---|---|
| CAM | **Cámara lineal GigE Vision** | Basler racer raL2048 (2048 px) o similar · **~$1000–2500** | Captura línea a línea (kHz) |
| LENTE | **Lente para line-scan** (C-mount / M42 según sensor) | apto NIR si se usa 850 nm · **~$300–800** | Proyecta el ancho del canal sobre la línea |
| PC | **PC industrial / laptop** con NIC GigE dedicada (jumbo frames) | mini-PC Intel i5+ · **~$500–1200** | Ingesta + OpenCV + conteo (la Raspberry Pi NO alcanza) |
| CABLE | Cable Ethernet **Cat6** apantallado | según distancia | Enlace cámara↔PC |
| LUZ | **Luz LINEAL continua** (LED line light / backlight lineal) alta potencia | **~$200–600** | Retroiluminación de la línea |
| DRV | **Driver de corriente constante** (continuo) + **disipador** | según potencia de la luz | Alimenta la luz (no conmuta) |
| PSU | Fuente **12–24 V** de mayor potencia | según luz | Consumo continuo |
| ENC | (Opcional) **Sensor de caudal / encoder** o control de bomba | — | Fija la tasa de línea → evita distorsión |

### Óptica / banco (se reutiliza del canal abierto)
| Ref | Componente | Nota |
|---|---|---|
| Canal | Mismo canal abierto de lámina delgada (Rev. C) | El flume no cambia |
| Soporte | Montaje rígido de cámara (alineación fina en 3 ejes) | Alineación crítica |
| Instrumentos | PC con SDK del fabricante (pylon/Aravis) | Captura y ajuste |

**Nota:** el line-scan **no lleva** Pi Pico, ni driver MOSFET de pulsos, ni sincronía de µs.

---

## 2. Conexión (resumen)

```
Cámara lineal ──GigE (Cat6)──► PC industrial (NIC GigE) ── SDK + OpenCV
       ▲ (trigger opcional)
       └── Sensor de caudal / encoder  (o free-run para conteo)

Luz lineal continua ◄── Driver corriente constante ◄── Fuente 12–24 V
   (+ disipador)
```
- Electrónica de disparo: **ninguna** compleja. La luz está encendida de forma continua.
- El "trigger" solo es necesario si se quiere geometría exacta (tasa de línea ligada al caudal).

---

## 3. Geometría óptica

- Resolución a lo ancho: `ancho_canal / nº_píxeles` → ej. **180 mm / 2048 ≈ 0,088 mm/px** (muy fina).
- Distancia de trabajo: `WD ≈ f · (1 + longitud_sensor / ancho_FOV)`; depende del modelo de cámara/lente.
- **Tasa de línea** = `velocidad_flujo / resolución` → ej. 0,5 m/s ÷ 0,088 mm ≈ **5,7 kHz** (la cámara da mucho más).
  - Si el caudal varía y la tasa es fija → la imagen se estira/comprime. Para **conteo** puede tolerarse; para **medir talla** hace falta encoder/control de caudal.

---

## 4. Montaje de la prueba

1. **Montar la cámara lineal** sobre el canal, perpendicular al flujo, con soporte de ajuste fino (3 ejes).
2. **Instalar la luz lineal** debajo del acrílico, **alineada exactamente** con la línea que ve la cámara (paso más delicado).
3. **Conectar** la cámara al PC por GigE (habilitar jumbo frames en la NIC).
4. **Instalar el SDK** del fabricante (pylon de Basler, o **Aravis** open-source para GigE Vision) + OpenCV.
5. **Enfocar y alinear**: con flujo de agua limpia, ajustar foco y verificar que la línea iluminada coincide con la línea de la cámara (imagen brillante y nítida a lo ancho).
6. **Fijar la tasa de línea**: empezar en free-run alto (p.ej. 10 kHz) y ajustar hasta que las larvas no salgan estiradas/comprimidas; o ligarla a un sensor de caudal.
7. **Pasar larvas** y verificar el conteo por cruce de línea contra un conteo manual de referencia.

---

## 5. Ventajas y desventajas (resumen)

**Ventajas**
- Resolución altísima a lo ancho (miles de px) → separa mejor larvas juntas y permite medir talla.
- Throughput enorme (millones/h) → maneja caudales masivos.
- **Electrónica más simple**: sin Pico, sin driver de pulsos, sin sincronía de µs.
- Referente probado en la industria (Vaki).

**Desventajas**
- **Costo alto**: cámara + óptica lineales + PC industrial → miles de USD por nodo.
- **Iluminación continua**: consumo alto + **calor** dentro de caja sellada (problema para instalación permanente).
- **Alineación crítica** cámara-línea-luz → puesta a punto delicada.
- **Distorsión geométrica** si el caudal varía (necesita encoder; en flujo no hay eje mecánico).
- **No escala económicamente** a muchas compuertas → como Vaki, unidad móvil rotativa.

---

## 6. Cuándo conviene

- Un **único punto** de caudal masivo, o cuando se necesita **máxima resolución** (talla/biomasa por larva).
- Hay presupuesto para equipo industrial y una unidad móvil rotativa basta.
- Para cobertura **permanente de muchas compuertas a bajo costo**, la Propuesta A (Global Shutter + Estrobo) es más adecuada.
