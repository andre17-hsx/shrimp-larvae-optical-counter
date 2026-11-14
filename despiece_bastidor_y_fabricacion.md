# Despiece de fabricación — Contador line-scan estilo Vaki

Calculado directamente desde la geometría de `modelo_3d_contador_vaki.scad`.
**Todas las cotas en milímetros.**

> Si cambias parámetros en el `.scad` (p. ej. `bas_L`, `canal_ang`), este despiece deja de ser válido: hay que recalcularlo.

---

## 1. Perfil de aluminio estructural T-slot 40 × 40

### 1.1 Lista de corte

| # | Pieza | Largo | Cant. | Subtotal | Corte |
|---|---|---:|---:|---:|---|
| 1 | Larguero longitudinal (2 inferiores + 2 superiores) | **1200** | 4 | 4800 | recto 90° |
| 2 | Travesaño de extremo (2 superiores + 2 inferiores) | **500** | 4 | 2000 | recto 90° |
| 3 | Travesaño central inferior | **500** | 1 | 500 | recto 90° |
| 4 | Columna vertical | **700** | 4 | 2800 | recto 90° |
| 5 | Riostra diagonal lateral | **796** | 4 | 3184 | **a 51° en ambos extremos** |
| 6 | Poste soporte del canal — alto (inicio) | **230** | 2 | 460 | recto 90° |
| 7 | Poste soporte del canal — medio | **92** | 2 | 184 | recto 90° |
| 8 | Pata del cajón de entrada | **173** | 4 | 692 | recto 90° |
| 9 | Poste de la pantalla táctil | **560** | 1 | 560 | recto 90° |
| | **TOTAL** | | **26 piezas** | **15 180 mm** | **= 15,18 m** |

### 1.2 Cuánto comprar (con corte optimizado, kerf 3 mm)

| Barra estándar | Barras necesarias | Total | Desperdicio |
|---|---:|---:|---:|
| **4000 mm** ✅ **recomendado** | **4** | 16,0 m | **0,82 m (5 %)** |
| 6000 mm | 3 | 18,0 m | 2,82 m (16 %) |
| 3000 mm | 6 | 18,0 m | 2,82 m (16 %) |

**Recomendación: 4 barras de 4 m** — es la opción con menos desperdicio.

### 1.3 Plan de corte (si compras barras de 6 m)

| Barra | Cortes | Usado | Sobra |
|---|---|---:|---:|
| 1 | 1200 + 1200 + 1200 + 1200 + 796 + 230 + 92 | 5939 | 61 |
| 2 | 796 + 796 + 796 + 700 + 700 + 700 + 700 + 560 + 173 | 5948 | 52 |
| 3 | 500 + 500 + 500 + 500 + 500 + 230 + 173 + 173 + 173 + 92 | 3371 | 2629 |

*Los sobrantes de la barra 3 sirven de reserva para ajustes en obra.*

### 1.4 Accesorios de unión (estimado)

| Ítem | Cant. aprox. | Nota |
|---|---:|---|
| Escuadras de unión 90° para perfil 40×40 | **40** | ~35 uniones + repuestos |
| Tuercas en T M8 | **160** | 4 por escuadra |
| Tornillos cabeza cilíndrica M8 | **160** | idem |
| Tapas de extremo 40×40 | **30** | extremos a la vista |
| Placas base / niveladores | 4 | bajo las columnas |

---

## 2. Chapa de acero inoxidable 316 (1,5–2 mm)

### 2.1 Cajón de entrada (stilling box)

| Pieza | Medida | Cant. |
|---|---|---:|
| Fondo | 270 × 430 | 1 |
| Pared trasera | 430 × 240 | 1 |
| Paredes laterales | 270 × 240 | 2 |
| Pared frontal (vertedero) | 430 × 170 | 1 |
| Tabiques enderezadores | 135 × 185 | 3 |
| Labio / cresta del vertedero | 430 × 60 (plegado) | 1 |

### 2.2 Bandeja de transición (embudo 430 → 166)

| Pieza | Medida | Cant. |
|---|---|---:|
| Fondo (trapecio) | 180 largo, 430 → 166 ancho | 1 |
| Paredes laterales (trapecio) | 180 largo, 80 → 55 alto | 2 |

### 2.3 Colector / dewatering

| Pieza | Medida | Cant. |
|---|---|---:|
| Fondo | 250 × 320 | 1 |
| Paredes largas | 250 × 260 | 2 |
| Paredes cortas | 320 × 260 | 2 |
| Marco de la malla | 250 × 320 | 1 |
| Malla inox (apertura fina) | 240 × 310 | 1 |

**Superficie total de chapa ≈ 1,1 m²** → comprar **1 plancha de 1220 × 2440 mm** (sobra material para el capó y refuerzos).

---

## 3. Acrílico / policarbonato

| Pieza | Medida | Espesor | Cant. |
|---|---|---|---:|
| Lecho del canal (zona de imagen) | 480 × 166 | **10 mm** | 1 |
| Paredes laterales del canal | 480 × 55 | 8 mm | 2 |

> El lecho es la **ventana óptica**: pedir acrílico **colado (cast)**, no extruido, y protegerlo con film hasta el montaje. Cualquier rayadura se traduce en ruido en la imagen.

---

## 4. Capó / cabezal óptico

| Pieza | Medida | Material | Cant. |
|---|---|---|---:|
| Techo | 270 × 320 | chapa 1,5 mm o ABS | 1 |
| Laterales | 270 × 470 | idem | 2 |
| Frontal / trasero | 320 × 470 | idem | 2 |
| Faldón inferior | 270 × 55 | idem | 2 |

Interior pintado **negro mate** (reduce reflejos). Debe poder abrirse o desmontarse para limpiar la ventana y ajustar el foco.

---

## 5. Notas de fabricación

1. **Riostras diagonales**: son las únicas piezas con corte en ángulo (**51°**). Confirmar el ángulo midiendo en el bastidor ya armado antes de cortar las 4.
2. **Orden de armado**: primero el prisma del bastidor (columnas + largueros + travesaños), verificar **escuadra y diagonales iguales**, y recién ahí montar las riostras.
3. **Nivelación**: el labio del vertedero y el canal deben quedar **perfectamente nivelados en el eje transversal**; usar los niveladores de las patas. Un desnivel lateral hace que la lámina de agua se corra hacia un lado y falsee el conteo.
4. **Soldadura inox**: soldar el cajón y el colector con TIG y pasivar los cordones (ambiente salino).
5. **Sellado**: juntas de EPDM/Viton entre el acrílico y la estructura del canal; nunca silicona común.
6. **Acceso**: dejar el canal desmontable sin desarmar el capó ni el bastidor (limpieza y recambio).

---

## 6. Resumen de compra (materiales de construcción)

| Material | Cantidad |
|---|---|
| Perfil T-slot 40×40 | **4 barras de 4 m** (16 m) |
| Escuadras + tuercas T + tornillos M8 | 40 / 160 / 160 |
| Chapa inox 316, 1,5–2 mm | 1 plancha 1220 × 2440 |
| Acrílico colado 10 mm | 500 × 200 |
| Acrílico colado 8 mm | 500 × 150 |
| Malla inox fina | 250 × 320 |
| Ruedas Ø100 con freno | 4 |
| Juntas EPDM/Viton | según desarrollo |
