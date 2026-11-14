# Resultado del caso 3D `p2_medio_grueso` (fase 2: cajón, estrechamiento, cresta y primeros 0,53 m de malla/tobogán)

Calculado el 2026-09-24/25. Diseño B del script de Fusion (`Fusion360_VAKI_Macro.py`, 91 cuerpos), agua a 10 L/s, medio ancho con
plano de simetría en y = 0, 1 566 106 celdas (película 2 mm, cresta 1 mm, superficie del cajón 4 mm), interFoam + kOmegaSST, pared
lisa, malla de acero modelada como pared (sin drenaje), 8 procesos, 47 393 s de cálculo (13,2 h) para 4 s simulados.

Análisis: `scripts/analizar_criterios.py` (reparte cada celda por su huella; el reparto por centro de celda da ±17 % de aliasing y
no debe usarse). Campos medios de 2,5 a 4 s (1,5 s). Fotos: `vistas/p2_medio_grueso/final_t4_completa.png`, `final_t4_mitad.png`,
`criterios_t4.png`.

## Estado del cálculo: cuasi-estacionario, no estabilizado en sentido estricto

El volumen de agua del dominio oscila entre 0,3568 y 0,3594 (±0,4 %) con periodo de ~1 s (chapoteo del cajón) y no converge a un
valor fijo; el criterio del vigilante (pendiente < 2·10⁻⁴ /s en dos ventanas seguidas) no llegó a cumplirse
(la pendiente cruza por cero cada ~1 s pero vuelve a subir). La media de 2,5 a 4 s cubre
solo ~1,5 periodos: es una media razonable, no una media convergida. El caudal por semiancho a lo largo de la lámina cierra en
4,83–4,86 L/s de 5,00 (−3 %; error de las medias de U y alpha por separado).

## Lámina sobre la malla y el tobogán (10 L/s)

Profundidad normal h y velocidad V = q/h, media 2,5–4 s, sin la banda de 10 mm junto a la pared lateral. 1D = modelo de
`simulacion_flujo/` con ancho constante (diseño B) y sin drenaje.

| x desde la cresta | CFD h (mm) | CV h | CFD V (m/s) | CV V | 1D n = 0,010 h / V | 1D n = 0,008 h / V |
|---|---|---|---|---|---|---|
| 0,10 m | 19,3 | 5,3 % | 0,99 | 2,2 % | 19,8 / 1,00 | 19,7 / 1,01 |
| 0,20 m | 15,9 | 8,4 % | 1,21 | 1,8 % | 16,6 / 1,19 | 16,4 / 1,21 |
| 0,30 m | 14,1 | 6,7 % | 1,37 | 1,5 % | 14,8 / 1,34 | 14,6 / 1,36 |
| 0,40 m | 12,9 | 5,7 % | 1,51 | 1,4 % | 13,7 / 1,45 | 13,4 / 1,49 |
| 0,50 m | 11,9 | 6,6 % | 1,63 | 1,2 % | 12,9 / 1,54 | 12,5 / 1,59 |

- El 3D concuerda con el 1D en profundidad y velocidad (−4…−7 % en profundidad frente a n = 0,010; +5 % en velocidad a 0,5 m),
  en línea con la fase 0a (n equivalente ≈ 0,008). El modelo 1D/2D usado para dimensionar queda respaldado en la lámina.
- La lámina no es plana a lo ancho: hay ondas oblicuas estacionarias de ±1,3 mm (±10 %) que cruzan el ancho. La velocidad, en
  cambio, es muy pareja (CV 1,2–2,2 %; a 0,5 m entre −3,7 % y +1,8 % de la media).

## Frente a los criterios de aceptación

| # | Criterio | Resultado | Veredicto |
|---|---|---|---|
| 1 | CV de la lámina < 5 % (fase 2: a 0,5 m de la cresta) | 6,6 % a 0,5 m (5,3–8,4 % entre 0,1 y 0,5 m) | **No se cumple** en este cálculo |
| 2 | Velocidad uniforme ±3 % | −3,7 % / +1,8 % a 0,5 m; CV 1,2 % | Al límite: el mínimo (−3,7 %) rebasa ±3 %; CV 1,2 % |
| 3 | Sin despegue con recirculación en cresta ni cono | 0,00 % de contraflujo en la lámina (x ≥ 0,1 m). Remolino esperado en el fondo del cajón frente a la cresta (Ux medio −0,2 m/s). Burbuja de separación de 2–4 mm en el labio (x ≈ 0,02 m) | Cumple en la lámina; cono no simulado |
| 4 | Entrada al cajón < 0,3 m/s | Máximo 0,26 m/s en la zona de entrada; la entrada es una condición de contorno (disco horizontal al fondo de un tubo de 60 mm bajo el cajón, con 0,197 m/s uniformes hacia arriba); el cono difusor no está en este cálculo | **No evaluado** (fase 4) |
| 5 | Sin aire arrastrado (< 1 %) | Aire atrapado resuelto: 0,00 % (lámina), 0,01 % (cresta), 0,00 % (cajón) | Cumple, con la salvedad de que no se ven burbujas < 2 mm ni auto-aireación |
| 6 | Lámina ≥ 5 mm | 11,9 mm a 0,5 m | Cumple aquí; la ventana de conteo está más abajo y con drenaje (no simulada) |

## Hallazgo importante para el diseño: el deflector sube el nivel de la parte trasera del cajón

El agua de la parte trasera del cajón (x < −0,27 m) sube a **≈122 mm** sobre el fondo, no a los **112,5 mm** de diseño (`NIVEL`).
Justo al cruzar el deflector (x = −0,25 m) el nivel cae a **≈108 mm** y sigue en 108–110 mm hasta la cresta, de modo que el
compartimento delantero (el que alimenta la cresta) está a 108–110 mm, no lejos del valor de diseño. Ese escalón de ~14 mm es
parejo a lo ancho de todo el cajón y coincide con el paso bajo el deflector, por donde el agua va a 0,26–0,33 m/s de media
(máximo 0,46 m/s; diseño: 0,30 m/s). Es consistente con una pérdida de carga en ese paso; no lo probé quitando el deflector, así
que es una atribución probable, no demostrada. Corrige mi primera lectura (que culpaba al labio y al estrechamiento).

- Estructura: `MARGEN_CAJON` pasa de 187 a ~178 mm en la parte trasera (paredes de 300 mm). No compromete nada.
- Lámina: ~5 % más rápida y ~5 % más delgada que el 1D con n = 0,010, como ya mostraba el 3D arriba.
- Nivel de trabajo (regla de nivel, sensor, tapa): la parte trasera trabaja a ~122 mm y la delantera a ~109 mm a 10 L/s; la
  fase 1 (corte 2D fino de la cresta) confirmará el nivel delantero, y una variante sin deflector, el efecto de este.
- Flujo en el cajón (corte `corte_completo.png`): el agua entra por el cono (0,15–0,25 m/s), pasa bajo el deflector pegada al
  fondo, sube por el frente de la cresta y sale por encima; sobre esa corriente, en el compartimento delantero, hay agua casi
  quieta o con retorno lento (< 0,1 m/s). De las 643 líneas de corriente del flujo medio que salen de la entrada, 59 % llegan a la lámina dentro del agua (5–12 s,
  mediana 7,4 s; hasta la cresta, mediana 7,0 s; cerca de los 6 s de renovación del cajón), 17 % se detienen en zonas casi
  estancadas (< 5 mm/s) y 24 % tocan la superficie libre del cajón, donde el campo medio mezcla fases y no permite seguirlas
  (sin conclusión). Corrige la cifra anterior de «29 % estancadas», que contaba también líneas que se cruzaban al aire.
- Salpicadura: en el campo instantáneo (t = 4 s) solo 0,2 % del agua de la zona de la lámina (4,7 de 2 199 mL) está a más de
  5 mm sobre la superficie media, ~0,13 mL a más de 10 mm (2 celdas) y nada a más de 20 mm. El aire 2–12 mm sobre la lámina va a
  1,1–2,2 m/s (mediana 1,7). Las líneas de corriente que en una versión del visor parecían «salir disparadas» sobre la lámina
  eran trazadores que pasaban al aire; ahora se cortan al salir del agua. Con celdas de 2 mm no se resuelven gotas ni rocío.

## Lo que este resultado NO demuestra

- Solo cubre hasta x = 0,53 m (0,25 m después de la malla). El arco y la línea de conteo (fase 3) no están simulados.
- La malla se modeló como pared: sin drenaje (fase 5, se mide en banco).
- Una sola malla (película 2 mm) y una media de 1,5 s: la amplitud de las ondas laterales (±1,3 mm, menos que una celda) puede
  cambiar con la resolución. Sin una segunda malla no se puede decir si son físicas o numéricas.
- El plano de simetría obliga a un flujo simétrico (no ve máquina desnivelada ni entrada descentrada).
- El cono difusor y la manguera no están en el cálculo.

## Siguientes pasos propuestos

1. Convergencia de malla de la lámina (p. ej. película 4 mm en ~1 h y, si conviene, una franja fina), para saber si las ondas
   laterales de ±10 % son reales.
2. Fase 1: corte 2D fino de la cresta (nivel del cajón y coeficiente de descarga con tres tamaños de celda).
3. Fase 3: arco y línea de conteo, con la lámina de entrada mapeada de este cálculo.
4. Fase 4: cono difusor. Fase 5: prueba de banco de la malla.

## Valoración de diseño con lo visto hasta ahora (2026-09-25, provisional)

Lámina en la línea de conteo (modelo 1D con ancho constante, sin CFD; el 3D lo respalda a ±5 % hasta x = 0,5 m). Drenaje = fracción
del caudal que pasa por la malla (no medido):

| Q (L/s) | sin drenaje, n 0,010 / 0,008 | 15 % | 30 % |
|---|---|---|---|
| 4 | 5,0 / 4,5 mm | 4,5 / 4,0 | 3,9 / 3,5 |
| 6 | 6,6 / 6,0 | 5,8 / 5,3 | 5,1 / 4,6 |
| 8 | 8,1 / 7,5 | 7,2 / 6,6 | 6,2 / 5,7 |
| 10 | 9,6 / 9,0 | 8,4 / 7,9 | 7,3 / 6,7 |
| 12 | 11,0 / 10,5 | 9,7 / 9,1 | 8,3 / 7,7 |
| 15 | 13,2 / 12,6 | 11,5 / 10,9 | 9,8 / 9,3 |

Velocidad de la lámina 1,4–2,35 m/s según caudal y drenaje: con píxel de 0,25 mm la cámara lineal necesita entre ~6 y ~9,5 kHz;
la frecuencia debe seguir al caudal o el píxel se estira hasta ±12 %.

Respaldado (3D + 1D/2D concuerdan): lámina delgada supercrítica, estable, con velocidad pareja a lo ancho (CV 1–2 %), sin aire ni
contraflujo; el estrechamiento previo a la cresta (diseño B) reparte el agua. No respaldado todavía: superficie rugosa o con
espuma en la línea de conteo (ninguna simulación lo resuelve; solo una maqueta con la cámara y el backlight), arco y línea de
conteo en 3D, drenaje real de la malla, cono difusor, retención de larvas en la piscina permanente (33 L, ~330 larvas a 10/L) y
tolerancia biológica a 2 m/s y a la caída final.

## ¿Importa que la variación de profundidad sea 6,6 % y no 5 %? (análisis, 2026-09-25)

El 5 % del criterio 1 fue un margen prudente propuesto al definir los criterios, no un límite derivado de la óptica. Efecto real
de la variación medida a 0,5 m de la cresta (mitad del rango ±1,38 mm = ±11,6 %; CV 6,6 %; profundidad media 11,9 mm) sobre el
brillo de un backlight que atraviesa la lámina una vez (Beer-Lambert; coeficientes de absorción del agua aproximados de la
bibliografía, la longitud de onda real del backlight no se conoce):

| Longitud de onda | α (1/cm) | Transmitancia media | Variación de brillo (mitad del rango) | (desv. típica) |
|---|---|---|---|---|
| 850 nm | ~0,043 | 95 % | ±0,6 % | ±0,3 % |
| 905 nm | ~0,06 | 93 % | ±0,8 % | ±0,5 % |
| 940 nm | ~0,27 | 72 % | ±3,7 % | ±2,1 % |
| 980 nm | ~0,45 | 58 % | ±6,2 % | ±3,5 % |

- Escala espacial: la profundidad cambia como máximo 0,5–0,8 mm entre bins vecinos de 10 mm (el largo de una larva) y hasta 2,3–3,1 mm
  en 100 mm; con 940 nm son ≈2 % de brillo por larva. Es una variación lenta comparada con la larva.
- Estacionariedad: la correlación entre el campo medio (2,5–4 s) y el instantáneo (t = 4 s) es 0,70–0,73; alrededor de la mitad
  de la varianza es un patrón fijo y la otra mitad fluctúa. Un ajuste de campo plano fijo quita solo parte; un fondo adaptativo
  (mediana móvil por columna) es lo adecuado.
- Lo que no incluye: refracción y dispersión de rugosidad, espuma y burbujas (más graves para la imagen), ni el contraste real de la
  larva bajo el backlight.
- Además, la velocidad es pareja (CV 1,2–2,2 %), así que la variación de profundidad no deforma el píxel de la cámara lineal.

## Drenaje de la malla: qué está y qué no está en el cálculo 3D (2026-09-25)

En el caso 3D la malla es una pared cerrada (`malla`: U `noSlip`, `p_rgh` `fixedFluxPressure`, alpha `zeroGradient`): no pasa agua
hacia el sumidero. El drenaje sí está en el modelo 1D y en el 2D (`simulacion_flujo/`, coeficiente `kd` calibrado a 15 % y 30 %
del caudal; el criterio de 0,1 m/s por las aberturas da un máximo de ~3,6 L/s), pero su valor real no está medido (fase 5).

Efecto estimado con el 1D (10 L/s, canal de diseño B, x medida desde la cresta):

| Drenaje | x = 0,10 m | x = 0,282 m (fin de la malla) | x = 0,50 m | caudal que sigue |
|---|---|---|---|---|
| 0 % (como el 3D) | 19,8 mm, 1,00 m/s | 15,1 mm, 1,31 m/s | 12,8 mm, 1,54 m/s | 10,0 L/s |
| 15 % | 18,4 mm, 1,02 m/s | 12,8 mm, 1,32 m/s | 11,1 mm, 1,53 m/s | 8,5 L/s |
| 30 % | 16,9 mm, 1,03 m/s | 10,5 mm, 1,32 m/s | 9,3 mm, 1,50 m/s | 7,0 L/s |

(n = 0,008 da 0,3–0,5 mm menos en profundidad y +0,03–0,05 m/s.) Conclusiones: aguas arriba de la malla (cajón, deflector,
cresta) el drenaje no cambia el flujo (régimen supercrítico); aguas abajo la lámina se adelgaza 13–27 % a 0,5 m y la velocidad
casi no cambia (−1 a −3 %), así que la conclusión de velocidad pareja es robusta y las profundidades del 3D son el techo sin
drenaje. No se sabe cómo cambiaría el patrón de ondas laterales. Para la fase 3 conviene añadir el drenaje como condición de
contorno en la malla (velocidad normal proporcional a la raíz de la carga, calibrada a 15 % y 30 %) y medir el coeficiente real
en banco.

## Convergencia de malla de la película: 2 mm frente a 4 mm (2026-09-26)

Caso `p2_medio_mm4` (película de 4 mm, cresta de 1 mm, cajón de 4 mm; 1 097 202 celdas frente a 1 566 106). Igual que `p2_medio_grueso`
salvo por la película y por un limitador de velocidad del aire (`limitVelocity`, 6 m/s, `constant/fvOptions`) que se añadió al
reiniciar en t = 2,35 s: el aire desarrolló un chorro numérico de hasta 18,5 m/s junto a la pared lateral y la tapa (interfaces de
refinamiento) que llevó el paso de tiempo a 3·10⁻⁵ s. El limitador solo actúa sobre el aire (el agua no pasa de 2,4 m/s) y recorta
al 0,5–1,6 % de las celdas. Promedio de 2,5 a 3,95 s (1,45 s; el último tiempo escrito tras el reinicio es 3,950089), frente a 2,5–4 s.
Comparación con `scripts/comparar_mallas.py` (figura `vistas/comparacion_mallas_2mm_4mm.png`).

| x (m) | h media 2 mm / 4 mm (mm) | CV h 2 mm / 4 mm | correlación de perfiles | amplitud 4 mm / 2 mm |
|---|---|---|---|---|
| 0,10 | 19,3 / 20,2 | 5,3 / 6,0 % | +0,72 | 1,18 |
| 0,20 | 15,9 / 16,1 | 8,4 / 6,8 % | +0,88 | 0,83 |
| 0,30 | 14,1 / 14,0 | 6,7 / 5,4 % | +0,81 | 0,80 |
| 0,40 | 12,9 / 13,1 | 5,7 / 4,9 % | +0,66 | 0,87 |
| 0,50 | 11,9 / 12,4 | 6,6 / 4,3 % | +0,71 | 0,68 |

- **Las ondas laterales de la lámina son una característica robusta del flujo, no ruido numérico:** los perfiles a lo ancho de las
  dos mallas se parecen (correlación media 0,72 entre x = 0,30 y 0,50 m; 0,63–0,88 en todo el tramo) y los picos caen en los mismos sitios.
- **Su amplitud no está convergida y crece al refinar:** CV medio de 4,8 % (4 mm) a 6,2 % (2 mm) entre x = 0,30 y 0,50 m; con celdas más
  gruesas la difusión numérica las amortigua. Por tanto 6,6 % no es una sobreestimación por la malla; con 1 mm podría ser algo mayor o
  estabilizarse (dos mallas no bastan para saberlo).
- Profundidad media: 0,2–0,5 mm más gruesa con 4 mm (tendencia ya vista en la fase 0a). Velocidad: 1,61 m/s (4 mm) frente a 1,63 (2 mm)
  a 0,5 m; CV de velocidad 1,1–3,0 % frente a 1,2–2,2 %.
- Sin aire atrapado (0,00 %) ni contraflujo en la lámina (0,00 %), igual que con 2 mm.
- Nivel del cajón: 121,3 / 108 mm (trasero/delantero) con 4 mm frente a 122,0 / 108 mm con 2 mm; velocidad bajo el deflector 0,27–0,34
  m/s frente a 0,26–0,33: los niveles y el escalón del deflector son independientes de la malla dentro de ~1 mm.
- Consecuencia para el diseño: la conclusión de la valoración sobre el brillo del fondo no cambia (±1,4 mm de profundidad son ±0,6–0,8 %
  de brillo con 850–905 nm y ±3,7 % con 940 nm); las ondas son reales en el cálculo, así que hay que medirlas en la maqueta y
  en la línea de conteo (fase 3), no descartarlas como artefacto.

## Fase 3 (arco y línea de conteo con drenaje): montaje del cálculo (2026-09-26)

Caso `lin_d15` (y luego `lin_d30`), scripts `geometria_linea.py` + `caso_linea.py`, guion `correr_caso.sh`. Dominio de semiancho desde
x = 0,06 m (justo aguas abajo del labio) hasta el final del tobogán (x = 1,27 m), con la malla, el tobogán recto, el arco (R = 915 mm,
de 12° a 20°) y el tramo recto final con la tapa como pared: 34,2 L, 1 164 317 celdas (película 2 mm), no ortogonalidad máxima 46°.
- **Entrada:** plano en x = 0,06 m con el perfil de velocidad y de fracción de agua del campo medio de `p2_medio_grueso`
  (`timeVaryingMappedFixedValue`, vecino más cercano; datos en formato «raw» sin cabecera), reescalado a 5,00 L/s de agua por el
  semiancho (el campo medio daba 5,24). Medido en el cálculo al arrancar: 4,76 L/s de agua entrando (interpolación de la entrada).
- **Drenaje:** velocidad normal uniforme hacia fuera en la malla (`surfaceNormalFixedValue`), calibrada con el modelo 1D para que la
  malla drene el 15 % del caudal total (`lin_d15`: 0,0098 m/s, 0,56 L/s en el semiancho, kd 0,0177) o el 30 % (`lin_d30`). Es un
  drenaje uniforme, sin dependencia de la carga, y el coeficiente real no está medido. Medido en el cálculo: 0,558 L/s.
- **Salida:** presión (`prghPressure`, `pressureInletOutletVelocity`); tapa y paredes noSlip; `limitVelocity` 6 m/s en el aire desde
  el inicio (en la fase 2 aparecieron chorros numéricos de aire de hasta 18 m/s con la malla de 4 mm).
- **Tiempo:** canal seco al inicio; 2,7 s de simulación con promedio de 1,5 a 2,7 s; ~0,2–0,3 s de flujo por hora de cálculo.
- Limitaciones: la entrada es un promedio (sin fluctuaciones turbulentas); el drenaje es uniforme; las ventanas y la carcasa del sensor
  de la línea de conteo no están en el dominio; se parte con la malla y el canal secos.
