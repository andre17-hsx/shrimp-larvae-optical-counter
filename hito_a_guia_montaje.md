# Hito A — Guía de montaje en banco

**Objetivo:** capturar una imagen **congelada** de un objeto en movimiento con el flash IR, sin sincronizar la cámara.
**Principio:** en caja oscura, el flash es la única luz → la exposición efectiva es el pulso (µs).

Ver los widgets de esta sesión: *distribución física/geometría* y *cableado del driver (9 LED)*.

---

## 1. Lista de materiales (con valores)

### Componentes principales (cómputo, cámara, control)
| Ref | Componente | Modelo / valor |
|---|---|---|
| Pi5 | **Raspberry Pi 5** (4/8 GB) + fuente USB-C 27 W + microSD ≥32 GB (Raspberry Pi OS) + disipador/ventilador |
| CAM | **Raspberry Pi Global Shutter Camera** (Sony IMX296), montura C/CS, sin IR-cut |
| LENTE | **Lente C-mount 12 mm**, apto NIR 850 nm |
| CABLE | **Cable/adaptador CSI para Pi 5** (15→22 pin) |
| MCU | **Raspberry Pi Pico** (RP2040) + cable micro-USB — GP15 → Rg → gate |
| PROTO | **Protoboard** + jumpers |

### Driver del LED
| Ref | Componente | Valor / modelo |
|---|---|---|
| LED1–9 | LED IR 850 nm 5 mm | genérico 850 nm (o Vishay TSHG6200) — **3 strings de 3 en serie** |
| Q1 | MOSFET N logic-level | **IRLB8721PbF** (o IRLZ44N) |
| Rs ×3 | Resistencia de corriente (una por string) | **56 Ω, 2 W** |
| Rg | Resistencia de gate | **47 Ω, ¼ W** |
| Rgs | Pull-down de gate | **10 kΩ, ¼ W** |
| C_res | Reservorio | **470 µF / 25 V** + **100 nF** cerámico |
| PSU | Fuente | **12 V DC**, ≥ 0,5 A |

### Óptica / banco
| Ref | Componente | Valor |
|---|---|---|
| Difusor | papel vegetal/opal sobre acrílico | ~80 × 80 mm |
| Soporte | trípode/brazo para la cámara | altura ~145 mm |
| Objeto | disco con marcas sobre motorcito/ventilador | velocidad conocida |
| Instrumentos | multímetro (y analizador lógico para Hito B) | — |

**Corriente:** ~0,13 A por string · pico total ≈ 0,4 A · media <1 mA (sin calor).

**Por qué Pi 5 y Pico:** la Pi corre Linux (no tiempo real → jitter de ms) y hace la visión; el Pico da los pulsos de µs con jitter ~0. Cada uno hace lo que el otro no puede. En el Hito B el Pico también generará el trigger de la cámara.

---

## 2. Cableado

```
+12V ──┬── string1: 3×LED serie ─ Rs(56Ω) ─┐
       ├── string2: 3×LED serie ─ Rs(56Ω) ─┤ (bus de drenaje)
       ├── string3: 3×LED serie ─ Rs(56Ω) ─┴─ Q1(Drain)
       └── C_res(470µF) ∥ 100nF ── GND       Q1(Source) ── GND

Pico GP15 ── Rg(47Ω) ── Q1(Gate) ──┬── Rgs(10kΩ) ── GND

GND común: PSU(−) = Pico GND = Q1 Source = C_res(−)
```
- Los 3 drains de las strings se unen y van al **único** MOSFET.
- Pinout **IRLB8721 (TO-220, cara frontal): G – D – S**. Verificar en datasheet.
- Los LED no necesitan diodo flyback.

---

## 3. Distribución física

| Parámetro | Valor |
|---|---|
| Rejilla de LED | **3×3, paso ~20 mm** (~50×50 mm), centrada bajo el FOV |
| Gap LED → difusor | **~25 mm** |
| Acrílico + difusor | **~80×80 mm** (≥ FOV) |
| Objeto de prueba | entre difusor y cámara (silueta) |
| **Altura cámara (lente→objeto)** | **~145 mm** (lente 12 mm) → FOV 60×45 mm |
| Cámara | f/4 · exposición 30 ms · gain 2 |

Regla del FOV: `FOV_ancho ≈ 0,42 × distancia` (lente 12 mm). El área iluminada debe ser ≥ el FOV.

---

## 4. Secuencia de puesta en marcha (orden seguro)

1. **Armar el driver** en protoboard. Revisar polaridad de LED, del electrolítico y pinout del MOSFET.
2. **Unir todas las masas** (PSU−, Pico GND, Source, C_res−).
3. **Cargar `firmware_pico_hito_a.py`** en el Pico con Thonny. Arranca con GP15 en LOW (LED apagado).
4. **Prueba sin instrumentos**: con el Pico pulsando, mirar los LED con la **cámara del celular** → se ven como puntos violáceos = encienden.
5. **Medir corriente**: poner `MODE = "BLINK"` en el firmware, medir la caída en un Rs → `I = V / 56 ≈ 0,13 A`. Volver a `MODE = "STROBE"`.
6. **Montar** caja oscura + difusor + cámara + objeto (entre difusor y cámara).
7. **Cámara**: `rpicam-hello -t 0 --shutter 30000 --gain 2` y oscurecer la escena.
   - Captura: `rpicam-still --shutter 30000 --gain 2 -o congelado.jpg`
8. **Poner el objeto en movimiento** y capturar. Ajustes:
   - Oscuro → Rs a 47 Ω, más brillo o subir `--gain`.
   - Arrastre → bajar `PULSE_US` (hasta 30) y/o mejorar el oscurecimiento.
   - Se ven los LED como puntos → alejar/añadir difusor.

---

## 5. Comandos de cámara (Raspberry Pi 5)

```bash
# Vista previa con exposición larga (única luz = flash)
rpicam-hello -t 0 --shutter 30000 --gain 2

# Captura de imagen fija
rpicam-still --shutter 30000 --gain 2 -o congelado.jpg
```

---

## 6. Criterio de éxito

- ✅ El objeto en movimiento aparece como **silueta nítida** (sin estela) cuando el flash lo ilumina.
- ✅ Se ve el efecto de `PULSE_US` y del brillo sobre la imagen.
- Frames oscuros o dobles ocasionales son normales sin sincronía → se resuelven en el **Hito B**.

---

## 7. Seguridad

- **Nunca dejar los LED en DC** con Rs de pulso (podría exceder el CW de un 5 mm). El firmware arranca en LOW; Rgs garantiza apagado.
- IR 850 nm invisible pero real: no mirar los LED de cerca a alta corriente prolongada.
- Respetar la corriente de **pico** del datasheet del LED.

---

## 8. Siguiente paso

Con el Hito A validado → **Hito B**: conectar GP15… (TRIG) al pad **XTR** de la cámara, activar el modo trigger del IMX296, y calibrar el retardo del pulso por barrido de brillo (ver `prototipo_sincronia_guia_practica.md`).
