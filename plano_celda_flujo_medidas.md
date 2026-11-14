# Celda de flujo óptica — Hoja de medidas y lista de corte (Rev. A)

**Proyecto:** Conteo óptico de larvas de camarón — Fase 1 (banco)
**Fecha:** Julio 2026
**Todas las cotas en milímetros (mm).**

> ⚠️ **Supuesto de partida:** tubería de la compuerta = Ø50 mm interior (2"). El diámetro del lado redondo de los adaptadores DEBE ajustarse al diámetro real medido en la compuerta antes de fabricar. Todo lo demás (canal y ventanas) se mantiene igual salvo que el caudal real exija otra sección.

---

## 1. Canal rectangular (sección óptica) — 1 pieza

| Dimensión | Valor |
|---|---|
| Ancho interior del canal (paso de agua) | 50 |
| Alto interior del canal (gap óptico cámara–LED) | 12 |
| Longitud (dirección del flujo) | 70 |
| Espesor de pared | 5 |
| Ancho exterior (50 + 2×5) | 60 |
| Alto exterior antes de puertos de ventana | 22 |
| Material | PVC o HDPE mecanizado / perfil rectangular |

**Aberturas de ventana:** una en la cara superior y una en la inferior (las caras de 50 mm de ancho), perfectamente enfrentadas.
- Abertura visible: **44 (ancho) × 60 (largo)**
- Centradas en la cara.
- 8 orificios Ø5.5 alrededor de cada abertura para pernos M5 (3 arriba, 3 abajo, 1 a cada lado; separación regular ~30 mm).

---

## 2. Ventanas de acrílico — 2 piezas (idénticas)

| Dimensión | Valor |
|---|---|
| Ancho de placa | 74 |
| Largo de placa | 90 |
| Espesor | 8 |
| Abertura óptica útil (coincide con la del canal) | 44 × 60 |
| Orificios de perno | 8 × Ø5.5, mismo patrón que el canal |
| Material | Acrílico colado (cast) óptico, o vidrio borosilicato |

*El área central (44×60) queda transparente y libre; los 15 mm de margen perimetral son la zona de apoyo de la junta y los pernos.*

---

## 3. Adaptadores redondo → rectangular — 2 piezas (idénticas)

| Dimensión | Valor |
|---|---|
| Lado redondo — diámetro interior | **Ø50** (= ajustar a tubería real) |
| Lado redondo — profundidad de encaje/encolado a tubería | 40 |
| Lado rectangular — sección interior | 50 × 12 (= sección del canal) |
| Longitud de la transición | 75 |
| Ángulo de transición | < 15° respecto al eje (transición gradual, sin escalón) |
| Material | PVC/HDPE mecanizado o impresión 3D en PETG/ABS grueso |

---

## 4. Longitud total ensamblada

`adaptador 75 + canal 70 + adaptador 75 + encajes ≈ **300 mm** (más los tramos de tubería redonda a cada extremo).`

---

## 5. Juntas y tornillería

| Ítem | Especificación | Cant. |
|---|---|---|
| Junta plana entre ventana y canal | EPDM o Viton, recortada a la forma de la placa con calado central de 44×60 | 2 |
| Pernos | M5 × longitud según stack (canal 5 + junta + acrílico 8) — inox 316 | 16 |
| Tuercas + arandelas | M5 inox 316 (arandela ancha para repartir presión sobre acrílico) | 16 |

---

## 6. Reglas críticas de fabricación (repetidas del plano)

1. **Enfrentamiento de ventanas:** cortar ambas aberturas con la misma plantilla y el tubo fijo en prensa. El eje óptico cámara↔LED depende de esto.
2. **Sellado de esquinas:** usar junta plana recortada (no o-ring circular); las esquinas del rectángulo son el punto más propenso a fuga.
3. **Apriete del acrílico:** en cruz y progresivo, con arandelas anchas. El acrílico se fisura si se aprieta puntual o desigual.
4. **Transición suave** en los adaptadores (<15°) para no generar turbulencia ni burbujas frente a la ventana.
5. **Montaje horizontal** del canal (ventanas arriba/abajo) para evitar acumulación de burbujas en la ventana superior.
6. **Prueba de estanqueidad** a baja presión ANTES de montar cámara/LED.

---

## 7. Lista de corte resumida (para el taller)

| # | Pieza | Material | Medida bruta | Cant. |
|---|---|---|---|---|
| 1 | Canal rectangular | PVC/HDPE | 60 × 22 × 70 (ext.) | 1 |
| 2 | Ventana | Acrílico 8 mm | 74 × 90 | 2 |
| 3 | Adaptador R→Rect | PVC/HDPE o impresión 3D | Ø ext. tubería × 75 largo | 2 |
| 4 | Junta | EPDM/Viton 2-3 mm | 74 × 90 con calado 44×60 | 2 |

*Nota: para el banco (Fase 1) se puede fabricar todo en plástico. El paso a inox 316 sólo se justificaría más adelante si se detecta abrasión o exigencia mecánica en campo.*
