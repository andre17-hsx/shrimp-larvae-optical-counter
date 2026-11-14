# Banco LED IR de retroiluminación estroboscópica (referencia)

**Proyecto:** Conteo óptico de larvas de camarón — Fase 1
**Función:** backlight uniforme de 850 nm bajo el acrílico, pulsado en sincronía con la cámara. Las larvas aparecen como siluetas oscuras sobre fondo claro.

---

## 1. Requisitos

| Parámetro | Valor |
|---|---|
| Área a iluminar | ≥ FOV (180 × 135 mm); panel ~200 × 150 mm |
| Longitud de onda | 850 nm (IR, casa con la QE del IMX296 y es invisible para la larva) |
| Régimen | Pulsado: 30–80 µs a 50 Hz → duty ~0,25 % |
| Uniformidad objetivo | ±10 % en el FOV (para que un umbral global funcione) |
| Tipo | Retroiluminación (backlight) con difusor |

## 2. Distribución física

- **~42 LEDs** en rejilla **8 × 6**, paso **~25 mm** → panel ~200 × 150 mm.
- LEDs de **emisión ancha (20–30°+)** para mezclarse bien tras el difusor.
- **Difusor opal** (acrílico difusor o film) a **20–30 mm** por encima del plano de LEDs.
- Apilado (de abajo a arriba): plano LED → gap aire 20–30 mm → difusor → acrílico del lecho → lámina de agua → (cámara arriba).

## 3. Cableado eléctrico

| Ítem | Valor |
|---|---|
| Configuración | 7 strings de 6 LED en serie (42 LED) |
| Vf por string | ~9 V (6 × 1,5 V) |
| Riel de alimentación | +12 V |
| Rs por string | ≈ 6 Ω (fija ~0,5 A por string) |
| Corriente por string | 0,5 A (pico, durante el pulso) |
| **Pico total** | **≈ 3,5 A** durante 30–80 µs |

## 4. Reservorio, fuente y térmico (la ventaja del estrobo)

- **Corriente media** = 3,5 A × 0,25 % ≈ **9 mA**.
- **Potencia media** ≈ 12 V × 9 mA ≈ **0,1 W** → **calor despreciable, sin disipador**.
- **Condensador reservorio** `C_res ≈ 1000 µF` baja ESR, junto al banco: entrega el pico de 3,5 A; la fuente solo repone la media.
  - Cálculo: `C = I_pico · t_pulso / ΔV = 3,5 A · 80 µs / 0,5 V ≈ 560 µF` → se redondea a 1000 µF con margen.
- **Fuente**: 12 V / ≥1 A sobra.
- **MOSFET Q1** (el mismo del driver de sincronía): N logic-level, >10 A, conmutación rápida. El pico de 3,5 A es trivial para él.

## 5. Balance de luz — palancas si la imagen sale oscura

Como el pulso es corto (µs), hay que depositar suficiente luz en poco tiempo. Subir en este orden:

1. **Corriente de pico** (bajar Rs o subir +V) — palanca principal.
2. **Ancho de pulso** (hasta ~100 µs; más allá empieza el arrastre de movimiento).
3. **Abrir diafragma** f/4 → f/2,8 (×2 de luz; la DOF sigue en ~50 mm, sobra).
4. **Ganancia del sensor** (último recurso: añade ruido).

Diseñar el banco con margen y **corriente ajustable** (Rs seleccionable o fuente regulable) para calibrar en banco.

## 6. Uniformidad

- Difusor obligatorio; nunca LED desnudo (haría puntos brillantes que saturan).
- Si aparecen puntos calientes (LED individuales visibles en la imagen): alejar el difusor o añadir una 2ª capa difusora.
- **Corrección de campo plano (flat-field) en software:** guardar una imagen de fondo sin larvas y dividir cada frame por ella → anula el ±10 % residual y cualquier gradiente. Es lo que garantiza que un umbral global segmente bien.

## 7. Sobreexcitación pulsada (seguridad del LED)

Un LED IR admite corriente de **pico** muy superior a la nominal continua cuando el duty es bajo. A duty ~0,25 % hay mucho margen, pero **respetar siempre el límite de corriente de pico del datasheet** del LED elegido (suele especificarse para una anchura de pulso y duty dados).

## 8. Puesta a punto en banco

1. Ajustar Rs/pulso hasta que el **fondo llegue a ~70 %** del rango del sensor a f/4, con el pulso dentro de la exposición.
2. Aplicar **corrección flat-field**.
3. Verificar ausencia de puntos calientes.
4. Confirmar que las larvas se ven como **siluetas oscuras nítidas** sobre fondo claro y uniforme.

## 9. Alternativa comercial

Existen backlights de iluminación estroboscópica de visión artificial ya diseñados para disparo pulsado (con su driver). Son más caros pero ahorran el diseño del array + difusor. Para Fase 1, el array propio da control total y bajo costo; evaluar el comercial si la uniformidad propia no alcanza el objetivo.
