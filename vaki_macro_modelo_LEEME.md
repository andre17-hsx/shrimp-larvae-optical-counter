# Modelo 3D a escala real — VAKI Macro 1 Channel

Reconstruido desde el plano `Macro-1-Channel-layout-drawing.pdf` (C0111-000000, escala 1:20).

## Archivos

| Archivo | Qué es |
|---|---|
| `vaki_macro_escala_real.step` | **El modelo para Fusion 360** (sólidos, en mm, con nombres y colores) |
| `modelo_vaki_macro_escala_real.py` | Generador. Todas las cotas son parámetros al inicio del archivo |
| `vaki_macro_render_*.png` | Vistas isométrica, lateral y superior para revisión rápida |
| `drawing_anotado_*.png` | El plano original con los componentes identificados |

## Abrir en Fusion 360

1. **Archivo → Abrir → Abrir desde mi PC…** y elegir `vaki_macro_escala_real.step`.
2. Fusion lo sube a la nube y lo traduce (tarda un minuto). Las unidades quedan en milímetros.
3. En el navegador aparecen 7 componentes con sus piezas nombradas:

```
VAKI_Macro_1_Channel_escala_real
├── Bastidor         patas, pata telescópica, largueros, riostras, ruedas
├── Cajon_entrada    fondo, paredes, chaflanes, boca Ø160, deflector, placa perforada, vertedero
├── Drenaje          rejilla, sumidero, tubo y válvula de drenaje
├── Canal_y_tobogan  contracción, tobogán curvo, ventana de acrílico, brida
├── Sensor           alojamiento, vidrio protector, asas + PROPUESTA_camara/lente/backlight
├── Capo             techo y laterales del capó
└── Salida           embudo, tubo Ø165, acople, pivote y palancas de ajuste
```

**Consejos en Fusion:**
- El capó tapa el tobogán. Apaga la visibilidad del componente **Capo** (ícono del ojo) para ver el interior.
- Si la transparencia del capó no se importa: clic derecho sobre el componente → *Control de opacidad*.
- Las piezas llegan como **cuerpos sólidos sin historial** (así funciona STEP). Para cambiar medidas hay dos caminos: editar con *Presionar/Tirar* en Fusion, o cambiar el parámetro en el `.py` y regenerar.

## Medidas y su origen

| Pieza | Medida (mm) | Origen |
|---|---|---|
| Largo total | 2837 | Plano (modelo: 2840) |
| Ancho total con ruedas | 1283 | Plano (modelo: 1282) |
| Alto total (config. dibujada) | ~1820 | Medido (modelo: 1819) |
| Nivel del cuerpo | 983–1583 (dibujado a 1310) | Plano |
| Ancho del cuerpo | 1000 | Medido |
| Cajón de entrada | 780 × 1000 × 300 alto, extremo chaflanado | Medido |
| Boca de entrada (por el fondo) | Ø160 | Medido |
| Sumidero de drenaje | 200 de largo, bajo el vertedero | Medido |
| Alojamiento del sensor | 441 × 510 × 359 alto | Medido |
| Perfil del tobogán curvo | fondo de Z 1310 a Z 895 en 960 mm | Medido |
| Embudo | 1000 → 150 de ancho | Medido |
| Tubo de salida | Ø165 | Medido |
| Ruedas | Ø264 | Medido |
| Patas telescópicas | 600 de recorrido | Plano |

Las medidas "Medido" salieron del plano a escala 1:20, con margen de ±10–20 mm.

## Supuestos (NO están en el plano — validar en la Fase 0)

El plano es de conjunto: solo muestra el exterior. Todo lo interior es supuesto:

| Supuesto | Valor usado | Parámetro en el `.py` |
|---|---|---|
| **Ancho del canal bajo el sensor** | 440 mm (inferido del contorno del capó) | `W_SENSOR` |
| Ancho interior del tobogán a lo largo de la curva | de 440 a 1000 mm | `TOBOGAN` |
| Contracción de 956 a 440 mm antes del sensor | en 125 mm | `CON_X0`, `CON_X1` |
| Deflector de paso inferior en el cajón | hueco de 70 mm | `DEFL1_X`, `DEFL1_PASO` |
| Placa perforada enderezadora | agujeros Ø30 | `DEFL2_X` |
| Vertedero bajo **con rampa** (sin caída libre) | 60 mm de alto | `VERT_X`, `VERT_H` |
| Rejilla de drenaje de barras longitudinales | paso 15 mm | `REJ_X0`, `REJ_X1` |
| Ancho del sumidero | 600 mm | `SUM_W` |
| Espesor de chapa | 3 mm inox 316 | `T` |
| Tubo del bastidor | 40 × 40 × 2 | `PERFIL` |

## Lo que NO es del Vaki

Las piezas con prefijo **PROPUESTA_** (cámara, lente, backlight IR y ventana de acrílico en el fondo) son la adaptación de nuestro proyecto. Hasta donde sabemos, el Vaki original usa un escáner infrarrojo.

**Ojo con la altura de la cámara:** el alojamiento del Vaki mide solo ~360 mm de alto. Dentro del alojamiento queda una distancia de trabajo de ~270 mm. Para cubrir los 440 mm del canal a esa distancia hace falta un lente gran angular (~5–7 mm, según el tamaño del sensor), o un alojamiento más alto, o un espejo a 45° que doble el camino óptico.

## Regenerar el modelo

Requiere Python con CadQuery. Se probó con Python 3.11 y CadQuery 2.8:

```
py -3.11 -m pip install cadquery
py -3.11 modelo_vaki_macro_escala_real.py
```

Para cambiar la altura de las patas: `DZ = -327` (mínimo), `0` (como está dibujado), `+273` (máximo).
