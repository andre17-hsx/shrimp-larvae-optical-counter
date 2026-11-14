# Sincronía cámara – LED estroboscópico (referencia)

**Proyecto:** Conteo óptico de larvas de camarón — Fase 1
**Principio:** el MCU es el maestro de tiempos. Dispara la cámara y el LED con timers por hardware, de modo que el pulso de luz cae siempre dentro de la ventana de exposición.

---

## 1. Idea central (por qué funciona)

La escena está a oscuras (capó opaco + filtro pasa-IR). La cámara sólo "ve" algo durante los microsegundos en que el LED está encendido. Por lo tanto:

> **El desenfoque de movimiento lo determina la duración del PULSO LED (30–80 µs), no el tiempo de exposición de la cámara.**

Esto permite usar una exposición cómoda (~200 µs) para que la sincronía sea robusta, mientras el pulso corto congela a la larva.

## 2. Arquitectura de señales

```
                 CAM_TRIG (3,3V) ┌──────────────┐  CSI-2  ┌───────────────┐
   ┌──────────────┐  ───────────►│ Cámara IMX296│────────►│ Raspberry Pi 5│
   │ MCU sincronía │             │  (pad XTR)   │         │ OpenCV+conteo │
   │ STM32 / ESP32 │             └──────────────┘         └───────────────┘
   │  timer HW     │
   └──────────────┘  LED_PULSE (3,3V) ┌──────────────┐ corriente ┌──────────┐
                     ───────────────► │ Driver MOSFET │──────────►│ LED IR   │
                                      └──────────────┘           │ 850 nm   │
                                                                 └──────────┘
```

- **CAM_TRIG:** flanco que inicia la exposición de la cámara (entrada de trigger externo, pad XTR).
- **LED_PULSE:** pulso que enciende el LED vía MOSFET, ubicado dentro de la exposición.
- Ambas señales salen del MISMO MCU → relación temporal determinística.

## 3. Diagrama de tiempos (por frame)

Escala de frame: período 20 ms (50 fps).
Escala de detalle (µs) dentro de un frame:

```
CAM_TRIG   ┐_____________________________________  (flanco en t=0)
           └┘
EXPOSICIÓN  _______▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁___________  (t_lat … t_lat+t_exp)
                   |◄──── t_exp ≈ 200 µs ────►|
LED_PULSE   _____________▁▁▁▁▁▁________________  (30–80 µs, DENTRO de la exposición)
```

Secuencia:
1. `t=0` — MCU genera flanco en CAM_TRIG.
2. `t_lat` — la cámara empieza a integrar (latencia trigger→exposición; **medir con osciloscopio**).
3. `t_led_on` — MCU enciende LED_PULSE, con margen dentro de la ventana.
4. `t_led_on + t_pulse` — MCU apaga el LED (t_pulse = 30–80 µs).
5. Fin de exposición y lectura del frame.
6. Repetir cada 20 ms.

**Regla:** `LED_PULSE ⊂ EXPOSICIÓN` en todos los frames, con margen a ambos lados.

## 4. Driver del LED (MOSFET) — componentes

| Componente | Valor / tipo | Función |
|---|---|---|
| Q1 | MOSFET N logic-level, bajo Rds(on), conmutación rápida | Corta el pulso de corriente al LED |
| Rg | 10–47 Ω | Limita corriente de gate, controla el flanco |
| Rgs | 10 kΩ (pulldown a GND) | Evita gate flotante (LED apagado por defecto) |
| Rs | Dimensionar al pico de corriente (o usar driver de corriente constante) | Fija la corriente del banco LED |
| C_res | 220–1000 µF, baja ESR, junto al LED | Reservorio que entrega el pico sin caer el riel |
| Gate driver | Opcional (si el banco LED es grande) | Flancos rápidos con MOSFET de gate grande |
| +V | p.ej. 12 V (según nº de LEDs en serie) | Alimentación del banco |

**Sobreexcitación pulsada:** un LED IR admite corriente de pico muy superior a la nominal cuando el ciclo de trabajo es bajo (pulsos de µs a 50 Hz → duty ~0,25 %). Respetar el límite de corriente de pico del datasheet del LED.

## 5. Niveles y jitter

- **3,3 V nativo** en STM32/ESP32 = compatible directo con el pad XTR de la cámara → **sin level-shifter**.
- **Masa común** obligatoria entre MCU, cámara y driver del LED.
- Generar los flancos con **timers/PWM por hardware**, nunca con `delay()` por software → jitter mínimo y frame rate estable.

## 6. Pseudocódigo del firmware (concepto)

```c
// Configuración (una vez)
FRAME_PERIOD_US = 20000;   // 50 fps
T_LED_ON_US     = 90;      // ubicado dentro de la exposición (ajustar tras medir t_lat)
T_PULSE_US      = 50;      // 30–80 µs

timer_master.set_period(FRAME_PERIOD_US);

// En cada desbordamiento del timer maestro (inicio de frame):
on_frame_start() {
    pulse(CAM_TRIG, width=14us);           // flanco de disparo de la cámara
    timer_led.one_shot(delay=T_LED_ON_US,  // pulso LED retardado y acotado
                       width=T_PULSE_US,
                       pin=LED_PULSE);
}
```

> Ambos disparos anclados al mismo timer maestro → la relación CAM_TRIG↔LED_PULSE no deriva.

## 7. Validación en banco (obligatoria antes de contar)

1. Osciloscopio en CAM_TRIG, señal de exposición (si la cámara la expone) y LED_PULSE.
2. **Medir t_lat** real (flanco de trigger → inicio de integración).
3. Ajustar `T_LED_ON_US` para que el pulso quede centrado en la exposición, con margen.
4. Capturar imagen de un objeto en movimiento conocido y verificar que no hay arrastre (< ½ px).
5. Confirmar estabilidad del frame rate (sin frames perdidos ni jitter visible).

## 8. Alternativa ideal (si la cámara expone salida de "flash/strobe")

Algunas cámaras industriales dan una señal de salida que está en alto exactamente durante la integración. Si estuviera disponible, se podría usar esa salida para disparar el LED → el pulso queda atado al ciclo real de exposición (aún más robusto). En la RPi Global Shutter Camera se trabaja con el **pad XTR de entrada**, por lo que se adopta el esquema con el MCU como maestro (sección 3).
