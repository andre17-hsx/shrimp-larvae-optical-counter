# Especificaciones de construcción — prototipo Fase 1

Cajón + deflector + estrechamiento + cresta + malla real + primeros 500 mm de canal, tomado directamente del script
`Fusion360_VAKI_Macro/Fusion360_VAKI_Macro.py` (constantes citadas tal cual; ninguna medida de este documento está
supuesta). Objetivo: validar con agua real, antes de fabricar en acero, lo que el cálculo (CFD) no puede cerrar por sí
solo. Ver el protocolo de pruebas completo en `cfd_3d/PLAN_MAQUETA.md`; este documento es el paquete de construcción.

Diagrama de referencia: [`perfil_fase1.png`](perfil_fase1.png) (planta y corte longitudinal, generado desde el script).

## 0. Alcance y simplificaciones respecto a la máquina real

**Incluye:** el cajón completo (cuerpo ancho + frente achaflanado + estrechamiento), el deflector, la rampa curva
de la cresta (sin labio), la malla real de acero inoxidable, el canal recto hasta 500 mm después de la cresta (antes de que empiece el
arco) y el cono difusor de entrada.

**Excluye (queda para una Fase 2):** el arco (R = 915 mm), el tramo final y la ventana de conteo, la tapa/cubierta
cerrada del tobogán, las patas telescópicas reales, la válvula de drenaje real.

**Simplificaciones deliberadas** (afectan a la estética y a la plomería, no a la hidráulica que se está validando):
- **Sin tapa, abierto por arriba.** La máquina real se cierra para controlar la luz y la higiene; la maqueta se deja
  abierta para poder filmar y medir desde arriba. Por eso las paredes de este documento tienen una altura fija
  razonable en vez de seguir el perfil escalonado que en la máquina real encaja contra la tapa.
- **Bandeja de recolección bajo la malla, no el sumidero con válvula real.** El sumidero real mide 115 mm de
  profundidad (`PROF_SUMIDERO`) con tubo y válvula de bola; aquí basta con recolectar y medir el agua que drena,
  así que alcanza con una bandeja estanca bajo la malla, con una salida a manguera hacia un recipiente aparte.
- **Sin patas telescópicas.** Se apoya en un soporte o mesa de laboratorio a la altura que sea cómoda para trabajar.

## 1. Sistema de referencia

Mismo criterio que en todo el CFD, para poder comparar directamente con `RESULTADOS_P2.md`:
- **x** = distancia horizontal desde la cresta, positiva **aguas abajo**. x = 0 es la cresta del vertedero.
- **y** = distancia desde el eje longitudinal (plano de simetría). La maqueta se construye a **ancho completo**, no a
  medio ancho como el CFD.
- **z** = altura sobre el fondo del cajón, salvo que se diga lo contrario.

## 2. Estaciones clave (verificadas contra el script)

| x (mm desde la cresta) | Qué es | Ancho interior |
|---|---|---|
| −747 | Frente del cajón (cara más aguas arriba) | — |
| −511 | Fin del chaflán del frente | 546 mm |
| −400 | Empieza el estrechamiento (cuerpo ancho recto termina aquí) | 994 mm |
| −250 | Deflector (placa de paso inferior) | ≈673–682 mm (ver §4) |
| −150 | Termina la curva de coseno, empieza el tramo recto final del estrechamiento | 504 mm |
| 0 | **Cresta del vertedero** | 504 mm |
| +282 | Fin de la malla (empieza el canal recto sólido) | 504 mm |
| +500 | **Corte de la Fase 1** (el arco empieza en +533 mm; no se llega a construir) | 504 mm |

## 3. Cajón — cuerpo, frente y estrechamiento

| Magnitud | Valor | Constante del script |
|---|---|---|
| Ancho exterior del cuerpo recto | 1000 mm | `ANCHO_CUERPO` |
| Espesor de las paredes (referencia de diseño) | 3 mm | `T` |
| Ancho interior del cuerpo recto | 994 mm | `ANCHO_CUERPO − 2T` |
| Alto de las paredes del cajón | 300 mm | `ALTO_CAJON` |
| Ancho exterior en el frente (chaflanado) | 546 mm | `ANCHO_FRENTE` |
| Ancho final en la cresta (interior) | 504 mm | `ANCHO_CANAL` |
| Nivel de diseño en el cajón a 10 L/s | 112,5 mm sobre el fondo | `g['NIVEL']` — **el CFD midió 122 mm real; usar 122 mm como referencia de trabajo** |
| Borde libre sobre el nivel | 187,5 mm (con el NIVEL de diseño); ~178 mm con el nivel medido por CFD | `g['MARGEN_CAJON']` |

### 3.1 Planta del estrechamiento (pared curva hacia la cresta)

La pared del estrechamiento **ya es, en el propio modelo de Fusion, una polilínea de 25 tramos rectos** (no una
curva continua), así que esta tabla es exacta, no una aproximación mía. Es la cara **interior** de la pared; el
semiancho y está medido desde el eje.

| # | x (mm desde la cresta) | y — semiancho interior (mm) | tramo (mm) | ángulo con el tramo anterior |
|---|---|---|---|---|
| 0 | −400,0 | 497,00 | — | — |
| 1 | −390,0 | 496,03 | 10,05 | — |
| 2 | −380,0 | 493,15 | 10,41 | −10,6° |
| 3 | −370,0 | 488,40 | 11,07 | −9,3° |
| 4 | −360,0 | 481,85 | 11,95 | −7,8° |
| 5 | −350,0 | 473,60 | 12,96 | −6,3° |
| 6 | −340,0 | 463,80 | 14,01 | −4,9° |
| 7 | −330,0 | 452,58 | 15,03 | −3,8° |
| 8 | −320,0 | 440,14 | 15,97 | −2,9° |
| 9 | −310,0 | 426,66 | 16,78 | −2,2° |
| 10 | −300,0 | 412,35 | 17,45 | −1,6° |
| 11 | −290,0 | 397,45 | 17,94 | −1,1° |
| 12 | −280,0 | 382,19 | 18,25 | −0,6° |
| 13 | −270,0 | 366,81 | 18,35 | −0,2° |
| 14 | −260,0 | 351,55 | 18,25 | +0,2° |
| 15 | −250,0 | 336,65 | 17,94 | +0,6° |
| 16 | −240,0 | 322,34 | 17,45 | +1,1° |
| 17 | −230,0 | 308,86 | 16,78 | +1,6° |
| 18 | −220,0 | 296,42 | 15,97 | +2,2° |
| 19 | −210,0 | 285,20 | 15,03 | +2,9° |
| 20 | −200,0 | 275,40 | 14,01 | +3,8° |
| 21 | −190,0 | 267,15 | 12,96 | +4,9° |
| 22 | −180,0 | 260,60 | 11,95 | +6,3° |
| 23 | −170,0 | 255,85 | 11,07 | +7,8° |
| 24 | −160,0 | 252,97 | 10,41 | +9,3° |
| 25 | −150,0 | 252,00 | 10,05 | +10,6° |
| 26 | +282,0 | 252,00 | 432,00 | +5,5° |

**Largo total desarrollado, por lado: 794,1 mm.**

**Archivos de coordenadas** (mismos datos que esta tabla, listos para usar):
- [`pared_curva_planta.dxf`](pared_curva_planta.dxf) — el perfil en planta (las dos paredes), para hacer las costillas
  del molde si se termoforma, o para reconstruir la pieza en cualquier programa de CAD.
- [`pared_curva_desarrollo.dxf`](pared_curva_desarrollo.dxf) — **el panel real a cortar**: la tira ya desplegada
  (794,1 mm de largo, alto variable de 300 a 180 mm según la regla del §3.3), con las líneas de doblez marcadas.
  Cortar este contorno de una sola pieza y doblar en cada línea (termoformado), o cortarla también por las líneas de
  doblez para el método facetado (§ más abajo).
- [`pared_curva_coordenadas.csv`](pared_curva_coordenadas.csv) — la misma tabla en una hoja de cálculo.

**Cómo construirla (dos opciones, según tu taller):**
- **Termoformada (mejor fidelidad):** cortar en el láser una tira recta de 794 mm × 300 mm de alto y unas costillas
  de MDF o acrílico grueso con el perfil de la tabla, para usarlas como molde. Calentar la tira con pistola de calor
  o termoformadora de tiras y doblarla sobre el molde. La curva es muy suave (nunca más de ~10,6° entre tramos de
  10–18 mm), así que no hace falta calentar toda la tira a la vez, se puede ir tramo a tramo.
- **Facetada (solo con láser/CNC, sin termoformado):** cortar paneles planos rectos entre los puntos de la tabla y
  unirlos con pegamento de acrílico (Weld-On #3 o #4) en las juntas, respetando los ángulos de la última columna.
  Con los 25 tramos el resultado es prácticamente indistinguible de la curva continua (el mayor tramo recto mide
  18,3 mm). Si se prefiere menos juntas, se puede unir de a dos o tres tramos consecutivos: el error que se introduce
  es pequeño porque la curva ya es muy suave (sagita máxima de la curva real sobre una cuerda de ~36 mm: bajo 1 mm).

El tramo 26 (432 mm, ancho constante 504 mm) cruza la cresta: es la pared del estrechamiento en su parte recta final
(−150 a 0), la propia cresta, y la pared lateral de la malla (0 a +282). Es un solo panel recto, sin dobleces.

### 3.2 Frente achaflanado (zona de entrada, X_CHAFLAN a LARGO_TOTAL)

| Punto | x (mm) | y — semiancho (mm) |
|---|---|---|
| Frente (cara más aguas arriba) | −747 | 273 (mitad de 546) |
| Fin del chaflán | −511 | 500 (mitad de 1000) |

Panel trapezoidal plano por lado, 236 mm de largo, de 273 a 500 mm de semiancho. Es donde en la máquina real está la
brida de conexión de la manguera; en la maqueta puede ser una pared ciega con un agujero para el cono difusor (ver
§6) y, si se quiere, una tapa removible para poder limpiar el cajón.

### 3.3 Altura de las paredes (simplificación de la Fase 1, ver §0)

| Tramo | Altura recomendada | Medida desde |
|---|---|---|
| Cuerpo del cajón (x de −747 a −400) | 300 mm (igual que `ALTO_CAJON`) | fondo del cajón (z = 0) |
| Estrechamiento (x de −400 a 0) | Baja linealmente de 300 a 180 mm | fondo del cajón |
| Malla y canal recto (x de 0 a 500) | 180 mm constante, medida perpendicular a la malla | **superficie de la malla/canal**, no el fondo del cajón |

Con el nivel medido por CFD (~122 mm atrás, ~108–110 mm adelante del deflector) y una lámina de 10–20 mm sobre la
malla, 180 mm deja de sobra para no rebosar y para que quepan los instrumentos.

## 4. Deflector

| Magnitud | Valor |
|---|---|
| Posición | x = −250 mm (250 mm aguas arriba de la cresta) |
| Espesor | 3 mm (`T`) |
| Alto | de z = 50 mm a z = 300 mm sobre el fondo del cajón (250 mm de alto) |
| Hueco libre bajo el deflector | 50 mm (`DEFLECTOR_PASO_INFERIOR`) |
| Ancho (va de pared a pared del estrechamiento en ese punto) | interior ≈ 673,3 mm en x = −250, ≈ 682,2 mm en x = −247 (con el espesor de 3 mm) |

Una sola placa plana rectangular, cortada para calzar de pared a pared del estrechamiento en esa posición (el ancho
del estrechamiento en ese punto sale de la tabla del §3.1, interpolando entre los puntos 14 y 15).

## 5. Cresta con rampa curva y sin labio

Cambio de diseño respecto a la primera versión (muro vertical de 90° con labio de 5 mm). Se decidió con tres corridas
de CFD idénticas en todo salvo la geometría (10 L/min, malla de 1,57 M celdas, promedio de 2,5 a 4 s):

| | Muro de 90° + labio | Rampa R=60 + labio | **Rampa R=60, sin labio (adoptado)** |
|---|---|---|---|
| Volumen con retorno fuerte (Ux < −0,25 m/s) en la esquina | 12,1 mL | 5,5 mL | **0,8 mL** |
| Retorno máximo | −0,47 m/s | −0,49 m/s | **−0,33 m/s** |
| Tiempo medio de una partícula en la zona de la esquina | 0,32 s | 0,23 s | **0,20 s** |
| Nivel del cajón, parte trasera | 122 mm | 122 mm | **118 mm** |
| Espesor de lámina a x = 500 mm | 11,9 mm | 11,9 mm | **12,6 mm** |

Fuentes: `cfd_3d/resultados/p2_medio_grueso`, `p2_rampa_R60`, `p2_rampa_sinlabio`. Detalles y límites en la sección
«Qué falta validar» de abajo.

| Magnitud | Valor |
|---|---|
| Alto de la cresta (`ALTO_VERTEDERO`) | 60 mm sobre el fondo del cajón |
| Radio de la rampa (`RADIO_RAMPA_CRESTA`) | 60 mm (= alto de la cresta) |
| Forma | cuarto de círculo: tangente al fondo (horizontal) en x = −60 mm y tangente vertical en x = 0, z = 60 |
| Ancho | 504 mm (`ANCHO_CANAL`) |
| Labio | **ninguno** (`CON_LABIO = False`; `LABIO_ABAJO/ARRIBA/ALTO_LABIO` quedan en el script solo para la variante de prueba) |
| Unión con la malla | la rampa termina en x = 0, z = 60 mm y la malla (12°) arranca en ese mismo punto |

**Perfil de la rampa** (17 puntos del script, `N_RAMPA_CRESTA = 16`; x desde la cresta, z sobre el fondo del cajón).
Archivos para corte: [`rampa_cresta_perfil.dxf`](rampa_cresta_perfil.dxf) (perfil cerrado para las costillas) y
[`rampa_cresta_coordenadas.csv`](rampa_cresta_coordenadas.csv).

| # | x (mm) | z (mm) | | # | x (mm) | z (mm) |
|---|---|---|---|---|---|---|
| 0 | −60,000 | 0,000 | | 9 | −13,619 | 21,936 |
| 1 | −54,119 | 0,289 | | 10 | −10,112 | 26,666 |
| 2 | −48,295 | 1,153 | | 11 | −7,085 | 31,716 |
| 3 | −42,583 | 2,584 | | 12 | −4,567 | 37,039 |
| 4 | −37,039 | 4,567 | | 13 | −2,584 | 42,583 |
| 5 | −31,716 | 7,085 | | 14 | −1,153 | 48,295 |
| 6 | −26,666 | 10,112 | | 15 | −0,289 | 54,119 |
| 7 | −21,936 | 13,619 | | 16 | 0,000 | 60,000 |
| 8 | −17,574 | 17,574 | | | | |

**Cómo construirla:** la rampa es una superficie cilíndrica (se desarrolla sin distorsión). Largo del arco desarrollado:
π/2 × 60 = **94,25 mm**, por 504 mm de ancho.
- *Opción A (recomendada para la maqueta):* lámina de acrílico de 3–4 mm calentada y formada sobre un molde de radio
  60 mm, apoyada en 3 o más **costillas** cortadas con el perfil del DXF (una en cada extremo y una cada ~170 mm) y pegada
  al fondo y a la malla. Tiene que quedar sin escalón: la lámina debe llegar tangente al fondo del cajón y su borde
  superior debe quedar a ras con el extremo de la malla.
- *Opción B:* bloque macizo o impreso en 3D con ese perfil.
- *Opción C (más simple, solo para una primera prueba):* pegar 16 tiras planas siguiendo la polilínea de la tabla.
- Cualquiera que sea, el borde donde la rampa se une con la malla **debe ser un filo vivo sin rebabas ni escalón**, como
  en el CFD. Un escalón de 1–2 mm ahí cambiaría el comportamiento del flujo.

### Qué falta validar (límites de la comparación de CFD)

- La lámina sale **0,7 mm más gruesa** a 0,5 m (12,6 contra 11,9 mm) y casi 2 mm a 0,1 m, con la misma velocidad a 0,5 m (≈ una celda de la malla del CFD). Hay que
  confirmar en la maqueta (pruebas 2 y 3 del plan) que sigue dentro del espesor que necesita el conteo.
- El nivel del cajón baja ≈ 4 mm, que coincide con quitar los 5 mm de labio. **Rehacer la calibración de
  `COEF_VERTEDERO`** (= 1,705 hasta ahora) con esta cresta antes de usar el nivel como medida de caudal.
- Los resultados son de un solo caudal (10 L/min) y de campo promedio. El seguimiento de partículas usa una difusión
  turbulenta supuesta, no medida: sirve para comparar diseños, no como cifra absoluta.
- Por eso la maqueta debería poder **montar y quitar un labio** (15 × 504 × 5 mm, pegado con cinta por ahora) para
  comprobar físicamente que sin él es mejor, antes de fijar el diseño en acero.

## 6. Malla real (30 mesh, acero inoxidable 316)

**Especificación de compra**, tomada literalmente del comentario del script (línea 79 y 874 de
`Fusion360_VAKI_Macro.py`):

> `MALLA_MESH, ABERTURA_MALLA = 30, 0.55` — 30 mesh = 0,55 mm de abertura (referencia de catálogo del diseñador: PL8+).
> Material: acero inoxidable 316 ("Steel, Stainless 316" / cedazo tipo tejido).

| Magnitud | Valor |
|---|---|
| Designación | 30 mesh (30 aberturas por pulgada) |
| Abertura | 0,55 mm |
| Diámetro de alambre (típico para 30 mesh 316, **confirmar con el proveedor**) | ≈ 0,30 mm |
| Material | Acero inoxidable 316 |
| Largo del panel (a lo largo de la pendiente, entre la cresta y x = +282 mm) | 282 / cos(12°) = **288,3 mm** |
| Ancho del panel | 504 mm (`ANCHO_CANAL`) |
| Pendiente | 12,01° (`PENDIENTE_INICIAL` = 0,2128 = tan(ángulo)) |

Pedir el trozo de malla de **290 × 510 mm** (con margen para el marco). Al pedir, especificar «malla tipo cedazo,
tejido llano, 30 mesh (abertura 0,55 mm), acero inoxidable 316» — es la única pieza de la maqueta que debe ser el
material real, porque la prueba #4 del plan de pruebas (banco de la malla) mide el drenaje real, que no se puede
estimar con una malla de otro material o abertura.

### 6.1 Marco y soportes bajo la malla

| Pieza | Medidas |
|---|---|
| Marco perimetral (`MARCO_MALLA`) | pletina de 20 mm de ancho, bordeando los 4 lados del hueco de la malla |
| Alto del marco/soportes (`ALTO_SOPORTE`) | 10 mm |
| Soportes transversales bajo la malla | cada 100 mm (`PASO_SOPORTE`), barras de 6 mm de ancho |

Sirven para que la malla no se hunda con el peso del agua; en la maqueta puede ser un marco de acrílico o PVC con
varillas cada 100 mm, pegado o atornillado bajo el hueco de la malla.

## 7. Canal recto después de la malla (x = 282 a 500 mm)

Continuación del canal a la misma pendiente (12°) y el mismo ancho interior (504 mm), en material sólido (no malla).
Sirve de zona de desarrollo de la lámina antes de donde empezaría el arco (x = 533 mm; el corte de la Fase 1 en
x = 500 mm deja 33 mm de margen). Al final, un pico o boquilla simple para dirigir el agua a un recipiente de
recolección (no hace falta construir el arco).

Esta zona es la que se compara directamente con la tabla de `RESULTADOS_P2.md` (espesor y velocidad de la lámina a
0,3 y 0,5 m de la cresta).

## 8. Bandeja de recolección bajo la malla

Simplificación del sumidero real (§0). Una bandeja estanca bajo toda la malla (282 mm × 504 mm en planta, al menos
50–80 mm de profundidad), con una salida a manguera para medir el caudal que atraviesa la malla (prueba #4). No hace
falta la válvula ni el tubo de 215 mm de la máquina real: para medir basta con una salida abierta a un recipiente
graduado.

## 9. Cono difusor de entrada

| Magnitud | Valor |
|---|---|
| Diámetro chico (conexión a la manguera) | 110 mm (`D_MANGUERA`) |
| Diámetro grande (boca, bajo el fondo del cajón) | 260 mm (`D_ENTRADA`) |
| Largo (altura del cono) | 560 mm (`LARGO_DIFUSOR`) |
| Posición en planta | x = −582 mm (bajo el frente achaflanado del cajón) |

### 9.1 Desarrollo plano (patrón para enrollar en lámina)

Un tronco de cono se puede cortar como un sector de corona circular y enrollarlo. Con estos diámetros y este largo:

| Magnitud | Valor |
|---|---|
| Radio menor (generatriz) | 414,3 mm |
| Radio mayor (generatriz) | 979,3 mm |
| Ángulo del sector | 47,79° |
| Generatriz (largo de la pared, en línea recta) | 565,0 mm |

Cortar un sector de corona circular entre radio 414,3 mm y 979,3 mm, con una abertura de 47,79°, en una lámina de
acrílico o PVC flexible; enrollar y pegar el borde recto para formar el cono, con el radio menor hacia la manguera
(110 mm) y el radio mayor hacia el cajón (260 mm).

**Alternativa más simple:** si 560 mm de cono es mucho para el banco de pruebas de la Fase 1, se puede acortar el
cono (menos difusión, entrada algo más rápida) o sustituirlo por un embudo comercial de ángulo parecido — es una
simplificación aceptable para esta fase, ya que el cono en detalle es la prueba #9 del plan de pruebas y puede
repetirse por separado si hace falta.

## 10. Materiales sugeridos

| Pieza | Material | Espesor |
|---|---|---|
| Paredes del cajón, estrechamiento, deflector | Acrílico transparente (colado, no extruido, para que el pegamento por disolvente selle bien) | 5–6 mm |
| Fondo del cajón y bandeja de recolección | Acrílico o PVC rígido | 6–8 mm |
| Cono difusor | Acrílico flexible o PVC | 2–3 mm |
| Marco y soportes de la malla | Acrílico o PVC | 5 mm |
| Malla | Acero inoxidable 316, 30 mesh, abertura 0,55 mm (§6) | — |
| Pegado | Adhesivo por disolvente para acrílico (Weld-On #3 para juntas de precisión, #4 para juntas más abiertas o piezas grandes) | — |

## 11. Lista de piezas (Fase 1)

| # | Pieza | Medidas | Cantidad |
|---|---|---|---|
| 1 | Pared lateral, cuerpo+estrechamiento (desarrollo, §3.1) | 794 × 300→180 mm (altura variable, ver §3.3) | 2 (izq/der, espejadas) |
| 2 | Pared del frente achaflanado | trapecio, 236 mm de largo, 273→500 mm de semiancho, 300 mm de alto | 2 (izq/der) |
| 3 | Pared trasera / frente del cajón | 546 mm de ancho × 300 mm de alto, con agujero de Ø254 mm centrado en x=−582 para el cono | 1 |
| 4 | Fondo del cajón | según el contorno en planta (§3.1–3.2), con agujero de Ø254 mm en x=−582 para el cono | 1 |
| 5 | Deflector | ≈678 × 250 mm | 1 |
| 6 | Rampa curva de la cresta | arco desarrollado 94,25 × 504 mm (R = 60 mm), acrílico de 3–4 mm formado en caliente | 1 |
| 7 | Costillas de la rampa | perfil del `rampa_cresta_perfil.dxf` | 3 |
| 7b | Labio de prueba (opcional, para la comparación) | 15 × 504 × 5 mm | 1 |
| 8 | Malla 30 mesh, inox 316 | 290 × 510 mm | 1 |
| 9 | Marco de la malla | pletinas de 20 mm, perímetro 288×504 mm | 4 |
| 10 | Soportes bajo la malla | barras de 6 mm de ancho, 504 mm de largo | ~6 (cada 100 mm) |
| 11 | Pared del canal recto (x = 282 a 500 mm) | 218/cos(12°) = 222,9 × altura 180 mm | 2 (izq/der) |
| 12 | Fondo/rampa del canal recto | 222,9 × 504 mm | 1 |
| 13 | Bandeja de recolección bajo la malla | 282 × 504 mm en planta, 50–80 mm de profundidad | 1 |
| 14 | Cono difusor (desarrollo, §9.1) | sector de corona, radio 414,3–979,3 mm, 47,79° | 1 |

## 12. Instrumentación y siguiente paso

Ver `cfd_3d/PLAN_MAQUETA.md` para el protocolo completo de pruebas, los valores esperados del cálculo y los umbrales
propuestos. Las pruebas que cubre esta Fase 1: **1** (nivel del cajón), **2** y **3** (espesor y velocidad de la
lámina hasta x = 500 mm), **4** (drenaje de la malla, banco de pruebas), **7** (aire y salpicadura en la cresta, con y sin el labio de prueba) y
**9** (entrada y cono difusor). Las pruebas 5, 6, 8, 10 y 11 (superficie en la línea de conteo, ondas laterales en
esa línea, retención en el cajón, nivelación, larvas) esperan a la Fase 2, que agrega el arco y el tramo final.
