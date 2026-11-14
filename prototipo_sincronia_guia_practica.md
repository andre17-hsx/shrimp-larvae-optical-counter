# Prototipo de sincronía cámara–LED — Guía práctica

**Objetivo:** obtener imágenes congeladas (motion-freeze) con el estroboscopio antes de escribir el algoritmo.
**Estrategia:** dos hitos separados. Primero congelar (sin trigger), luego sincronizar (trigger real).

---

## Idea clave

En una **caja oscura**, si la única luz es el flash del LED, la exposición efectiva es la duración del pulso (µs), no la de la cámara. Por eso:
- Para **probar el congelado** NO hace falta sincronizar → Hito A.
- Para que **cada frame** quede bien iluminado de forma determinística → Hito B (trigger).

---

## Material mínimo del prototipo

| Ítem | Nota |
|---|---|
| Raspberry Pi 5 + Raspberry Pi Global Shutter Camera (IMX296) | La cámara del sistema |
| Lente C-mount (cualquiera, para el banco; el 12 mm si ya lo tenés) | — |
| MCU: **Raspberry Pi Pico** (recomendado) o ESP32 | 3,3 V nativo, timers/PIO precisos |
| MOSFET N logic-level + Rg (10–47 Ω) + Rgs (10 kΩ) | Driver del LED |
| Unos pocos LED IR 850 nm + Rs + C_res (~1000 µF) + fuente 12 V | No hace falta el banco completo aún |
| Difusor (papel vegetal/opal sirve para prototipo) | Uniformidad |
| **Analizador lógico USB barato (~$10) o osciloscopio** | Muy recomendado para el Hito B |
| Caja/tela opaca para oscurecer | Crítico para el Hito A |
| Objeto de prueba en movimiento (ver abajo) | Para evaluar el congelado |

**Objeto de prueba sugerido:** un disco impreso con marcas radiales o un patrón, girando con un motorcito (o un ventilador). Sabés la velocidad de borde → podés estimar el arrastre esperado y verificar que se congela. Alternativa simple: una regla o patrón pegado a un ventilador.

---

## HITO A — Congelar sin trigger (empezá acá)

### Cableado
- MCU genera un pulso repetido en un pin → gate del MOSFET (vía Rg) → LED.
- La cámara NO se conecta al MCU todavía. Corre libre.
- Masa común entre MCU y driver.

### Firmware del MCU (Raspberry Pi Pico, MicroPython — pulso simple)

```python
from machine import Pin
import time

led = Pin(15, Pin.OUT)   # → gate del MOSFET (vía Rg)
PULSE_US = 50            # ancho del flash (µs)
PERIOD_MS = 20           # 50 Hz

while True:
    led.on()
    time.sleep_us(PULSE_US)
    led.off()
    time.sleep_ms(PERIOD_MS)
```

*(Para pulsos de µs más precisos conviene PIO/timer, pero para el Hito A esto basta.)*

### Cámara (en la Pi) — exposición larga, free-run
Oscurecé la escena. Corré una vista previa con exposición larga y ganancia moderada:

```bash
rpicam-hello -t 0 --shutter 30000 --gain 2 --awbgains 1,1
```
- `--shutter 30000` = 30 ms de exposición. Como la única luz es el flash de 50 µs, la imagen sale congelada.
- Si ves negro: subí brillo del LED (más corriente / más LEDs) o ganancia.
- Si ves movida (arrastre): el pulso es muy largo, o entra luz ambiental → mejorá la caja oscura.

### Qué deberías ver
- Con el objeto girando, las marcas aparecen **nítidas** (congeladas), no como estelas.
- Puede haber frames más oscuros o dobles imágenes: es normal sin sincronía (a veces caen 0 o 2 pulsos por exposición). No importa para este hito: solo querés confirmar que **cuando el flash ilumina, la imagen queda congelada**.

### Ajustes de este hito
- **Ancho de pulso**: bajalo hasta que el arrastre desaparezca; subilo si falta luz. Rango útil 30–80 µs.
- **Brillo**: corriente de pico (Rs), nº de LEDs, o abrir diafragma.
- **Difusor**: que no se vean los LED individuales como puntos.

---

## HITO B — Sincronía real por trigger externo

Cuando el congelado ya funciona, pasás a que **cada frame** tenga su flash, disparando cámara y LED juntos.

### Cableado adicional
- Pin TRIG del MCU → **pad XTR** de la GS Camera (3,3 V, directo, sin level-shifter).
- **GND del MCU ↔ GND de la cámara** (imprescindible).
- El pin LED_PULSE del MCU sigue yendo al driver.

### Activar el modo trigger del IMX296 (en la Pi)
> El método exacto depende de tu versión de OS/driver — **verificá con la documentación vigente de la Raspberry Pi GS Camera**. El enfoque canónico es cargar el driver `imx296` con el parámetro de modo trigger:

```bash
# Ejemplo orientativo — confirmar sintaxis con tu versión:
sudo rmmod imx296
sudo modprobe imx296 trigger_mode=1
```
En modo trigger, la cámara **solo produce frames cuando llega un flanco por XTR**. Si no hay pulsos, no hay frames (buena señal de que el modo está activo).

### Firmware del MCU — un timer maestro dispara ambos
Concepto: en cada inicio de frame, emitir el flanco de TRIG y, tras un **retardo calibrado**, el pulso de LED.

```python
# Pseudocódigo (usar timer HW / PIO para precisión de µs)
FRAME_US   = 20000    # 50 fps
T_LED_US   = 150      # RETARDO del pulso — se calibra (ver abajo)
PULSE_US   = 50

def on_frame():           # dispara cada FRAME_US con un timer HW
    pulse(TRIG,  14)      # flanco de disparo de la cámara
    schedule(T_LED_US, lambda: pulse(LED_PULSE, PULSE_US))  # pulso retardado
```

### Calibrar el retardo T_LED_US (sin osciloscopio) — método del barrido
La cámara integra desde `t_lat` (latencia trigger→exposición) durante `t_exp`. El pulso LED debe caer dentro. Para encontrar la ventana:

1. Poné el objeto quieto y una exposición corta fija en la Pi (p.ej. `--shutter 200`).
2. Barré `T_LED_US` de 0 a ~300 µs en pasos de 10–20 µs.
3. Para cada valor, medí el **brillo medio** de la imagen (a ojo, o con un script que promedie píxeles).
4. Vas a ver una curva tipo meseta: **oscuro → brillante (meseta) → oscuro**. La meseta ES la ventana de integración.
5. **Fijá `T_LED_US` en el CENTRO de la meseta** → el pulso queda seguro dentro de la exposición en cada frame, con margen a ambos lados.

Script rápido para medir brillo medio de una captura:
```bash
rpicam-still -t 200 --shutter 200 -o test.jpg --nopreview
python3 -c "import cv2,sys; print(cv2.imread('test.jpg',0).mean())"
```

### Verificación con analizador lógico / osciloscopio
- Canal 1 = TRIG, Canal 2 = LED_PULSE.
- Confirmá visualmente que **LED_PULSE cae dentro de la ventana** (coherente con el centro hallado).
- Medí el jitter frame a frame: debe ser mínimo (por eso se usan timers HW, no `sleep` por software).

### Resultado esperado
- Cada frame sale iluminado y congelado.
- Frame rate estable (sin frames perdidos).
- Las larvas/objeto se ven como **siluetas oscuras nítidas** sobre fondo claro.

---

## Fallos típicos y solución

| Síntoma | Causa probable | Solución |
|---|---|---|
| Frames negros intermitentes | Pulso fuera de la exposición o en el blanking | Centrar T_LED_US en la meseta |
| Doble imagen fantasma | 2 pulsos en una exposición (Hito A) | 1 pulso por frame; bajar exposición |
| Sigue habiendo arrastre | Pulso muy largo o LED no apaga rápido | Acortar pulso; revisar MOSFET/Rgs; verificar que el LED corta limpio |
| Bandas / parpadeo | Luz ambiental entrando | Mejorar caja oscura/capó + filtro pasa-IR 850 |
| No aparece ningún frame (Hito B) | Modo trigger activo pero sin pulsos válidos | Revisar cableado XTR, nivel 3,3 V, GND común, que el MCU esté pulsando |
| Imagen con puntos brillantes | LED sin difusor | Añadir/alejar difusor |

---

## Criterio de éxito del prototipo

✅ En movimiento conocido, la silueta sale **nítida** (arrastre < ~1 px estimado).
✅ En Hito B, **todos** los frames iluminados y frame rate estable.
✅ Fondo uniforme (tras difusor) → base lista para el algoritmo de conteo.

Con esto validado, recién ahí tiene sentido programar detección + tracking + conteo.
