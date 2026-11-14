# Canal abierto de lámina delgada — Hoja de medidas (Rev. B)

**Proyecto:** Conteo óptico de larvas de camarón — Fase 1 (banco)
**Enfoque:** flume/canal abierto con backlight IR inferior y cámara superior. Las larvas nunca salen del agua.
**Cotas en mm.**

---

## 1. Secciones del canal (de entrada a salida)

| Tramo | Función | Medida |
|---|---|---|
| Caja de calma (stilling box) | Amortigua turbulencia de entrada | 200 ancho × ~150 largo × 120 alto |
| Vertedero (labio nivelado) | Reparte agua en lámina uniforme, a todo el ancho | labio horizontal a todo lo ancho (200) |
| Enderezador de flujo (peine) | Elimina corrientes cruzadas | fila de álabes verticales, paso ~30 |
| Rampa de aceleración | Lleva la lámina a velocidad estable | pendiente 3–5°, largo ~80 |
| **Zona de conteo (shelf plano)** | Plano de imagen fijo, cámara perpendicular | **140 (largo) × 200 (ancho), horizontal** |
| Rampa de salida | Evacúa hacia el retorno | pendiente 3–5°, largo ~60 |
| Vertedero/labio de salida + launder | Devuelve agua+larvas a la tubería destino | full ancho |

**Largo total del flume ≈ 400 mm** (más caja de calma y launder de salida).

## 2. Lámina de agua (parámetro crítico)

| Parámetro | Valor |
|---|---|
| Espesor de lámina en zona de conteo | **4–6 mm** |
| Ancho útil de imagen | 180 (de los 200 totales; se descartan ~10 mm de cada pared por menisco) |
| Altura de paredes laterales | 40 |

## 3. Óptica

| Elemento | Ubicación |
|---|---|
| Cámara | Encima, perpendicular al shelf, dentro de capó opaco anti-luz ambiental |
| Backlight LED IR 850 nm + difusor | Debajo del acrílico del shelf, apuntando hacia arriba (retroiluminación) |
| Campo de visión (FOV) | 140 × 180 mm sobre el shelf |

## 4. Materiales

| Pieza | Material | Espesor |
|---|---|---|
| Lecho del canal (bed) | Acrílico colado óptico | 8–10 |
| Paredes laterales | Acrílico | 6 |
| Caja de calma / launder | Acrílico o PVC | 6–8 |
| Estructura de soporte + tornillos niveladores | Perfil (aluminio anodizado o inox) | — |

## 5. Reglas de fabricación / puesta a punto

1. **Labio del vertedero perfectamente nivelado** — de esto depende que la lámina sea uniforme en todo el ancho. Nivelar en sitio con tornillos.
2. **Shelf de conteo horizontal y plano** — es el plano de enfoque; cualquier alabeo desenfoca los bordes.
3. **Enderezador de flujo obligatorio** — sin él, los remolinos de la entrada arrastran larvas en diagonal y falsean el conteo por línea virtual.
4. **Pendiente ajustable (3–5°)** con tornillos niveladores → permite calibrar la velocidad de la lámina sin refabricar.
5. **Backlight con difusor**, no LED desnudo → evita puntos brillantes que saturan el sensor.
6. **Capó opaco sobre la cámara** → la luz ambiental (sol) es el mayor enemigo del contraste; el IR 850 nm + filtro pasa-IR en el lente ayuda a rechazarla.

## 6. Punto abierto a resolver en banco: caudal vs. ancho

La lámina delgada limita el caudal por metro de ancho. Dos caminos:
- **Ensanchar el canal** para pasar más caudal a la misma profundidad (a más caudal, más ancho).
- **Regular (throttle) la compuerta** para que el flujo se ajuste a la capacidad del contador → se cuenta el 100 % pero a ritmo controlado (la transferencia dura un poco más).

Se dimensiona con el **caudal real medido** en la compuerta piloto. Para el banco (Fase 1) se arranca con 200 mm de ancho y se mide qué caudal admite manteniendo lámina de 4–6 mm y buen conteo.

---

*Rev. B reemplaza el enfoque de celda cerrada (Rev. A). Ventajas: sin manipulación/mortalidad de larvas, sin grumos por deshidratación, plano de enfoque fijo, fabricación más simple y limpieza más fácil.*
