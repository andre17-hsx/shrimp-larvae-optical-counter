# Óptica del nodo — Cámara, lente y parámetros (referencia)

**Proyecto:** Conteo óptico de larvas de camarón — Fase 1
**Enfoque:** canal abierto de lámina delgada, backlight IR inferior, cámara superior.

---

## 1. Sensor / cámara seleccionada

**Raspberry Pi Global Shutter Camera (Sony IMX296)**

| Característica | Valor | Por qué importa |
|---|---|---|
| Obturador | Global shutter | Congela larvas en movimiento sin deformación (rolling shutter las "estira") |
| Resolución | 1456 × 1088 px (1,58 MP) | Suficiente para conteo por blobs |
| Sensor | 5,0 × 3,75 mm (1/2,9") | Base del cálculo de FOV |
| Píxel | 3,45 µm | — |
| Montura | C/CS | Acepta lentes industriales |
| Trigger externo | Sí (pad XTR) | Sincronía por hardware con el strobe |
| Filtro IR-cut | No trae | Funciona con LED 850 nm |
| Frame rate | 60 fps a resolución completa | Cumple con margen |

## 2. Cálculo de FOV y resolución

- Ancho útil de imagen (a través del canal): **180 mm** → mapea al lado largo del sensor (5,0 mm)
- Magnificación: `m = 5,0 / 180 = 0,0278`
- **Resolución en objeto: 180 / 1456 = 0,124 mm/px**
- FOV a lo largo del flujo (lado corto): 3,75 / m = **135 mm**

**Larva sobre el sensor:**
| Dimensión larva | Tamaño real | En píxeles |
|---|---|---|
| Ancho | 0,3–0,6 mm | 2,4–4,8 px |
| Largo | 7–12 mm | 57–97 px |

→ Adecuado para detectar (blob) y trackear.

## 3. Lente y distancia de trabajo

Fórmula: `distancia lente→lámina = f × (1 + 1/m) = f × 37`

| Focal | Dist. lente→lámina | Capó total | Nota |
|---|---|---|---|
| 8 mm | ~30 cm | ~36 cm | Compacto, más distorsión en bordes |
| **12 mm** ✅ | **~44 cm** | **~50 cm** | **Recomendado (equilibrio)** |
| 16 mm | ~59 cm | ~65 cm | Menos perspectiva, más alto |
| 25 mm | ~92 cm | ~1 m | Poco práctico |

**Lente elegido: C-mount 12 mm, apto NIR (850 nm). Cámara ~50 cm sobre la lámina.**

## 4. Apertura y profundidad de campo

`DOF ≈ 2·N·c / m²` (c = 2 px = 6,9 µm)

| Apertura | DOF |
|---|---|
| f/2,8 | ~50 mm |
| **f/4** ✅ | **~70 mm** |

La lámina es de 4–6 mm → **la DOF no es restricción**. Usar **f/4** para máxima nitidez en todo el campo.

## 5. Pulso del strobe (congelar movimiento)

A velocidad de flujo ~0,5 m/s, para arrastre < ½ px (0,062 mm):
`t_pulso < 0,062 / 500 = 124 µs`

→ **Pulso LED de 30–80 µs** (arrastre < 0,4 px, imagen nítida).

## 6. Frame rate

Tránsito de larva por el FOV (135 mm a 0,5 m/s) = 0,27 s.
Para 8–10 frames por larva: `fps ≈ 37`.
→ **Operar a 40–60 fps.** A mayor velocidad de flujo, recortar ROI para subir fps.

## 7. Resumen de configuración

| Parámetro | Valor |
|---|---|
| Cámara | RPi Global Shutter (IMX296) |
| Lente | C-mount 12 mm, NIR |
| Altura cámara | ~44 cm lente→agua (~50 cm capó) |
| Apertura | f/4 |
| Resolución objeto | 0,124 mm/px |
| FOV | 180 × 135 mm |
| Pulso strobe | 30–80 µs |
| Frame rate | 40–60 fps |

## 8. Avisos prácticos

1. **Enfocar con el IR real encendido**, no con luz visible (hay corrimiento de foco a 850 nm).
2. **Lente que transmita a 850 nm** (evitar recubrimiento IR-cut) + **filtro pasa-largo 850 nm** sobre el lente → rechaza luz solar ambiental, contraste estable a cualquier hora.
3. **Capó opaco** sobre la cámara → la luz ambiental es el mayor enemigo del contraste.

## 9. Opción futura: enfoque "IA por ojos"

Para separar larvas pegadas o descartar mudas/detritos por deep learning (tipo Sincere Aqua) se necesita ~0,07 mm/px → sensor **global shutter 5 MP** (Sony IMX264/265, 2448×2048, 2/3"), mismo lente 12–16 mm. Mayor costo y datos. Para Fase 1 (conteo por blobs), el IMX296 es la opción correcta.
