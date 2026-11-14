# Plan de pruebas de la maqueta transparente

Objetivo: comprobar con agua real, **antes de cortar acero**, lo que ninguna simulación puede cerrar y que decide si el diseño
funciona. Cada prueba tiene el valor que predice el cálculo (`RESULTADOS_P2.md`, fase 3 en curso) y un umbral propuesto de «pasa».
Los umbrales son una propuesta para acordar, no criterios ya confirmados.

## Qué decide esta maqueta

| Incógnita | Por qué no la cierra la simulación |
|---|---|
| Superficie del agua en la línea de conteo (rugosidad, espuma, gotas) | El cálculo no resuelve ondas capilares de 2–3 mm, espuma ni rocío; afecta a la imagen |
| Drenaje real de la malla de 30 mesh | Es un supuesto (15–30 %) sin medir; define el caudal mínimo de trabajo |
| Imagen real con la cámara y el backlight elegidos | Aún no están elegidos; se eligen a partir de estas pruebas |
| Trato a la larva a ~2 m/s y retención en el cajón | El CFD da velocidades, no cómo reacciona el animal ni cuántas quedan atrás |
| Máquina desnivelada o entrada descentrada | El cálculo es simétrico |

## Alcance de la maqueta

Recorrido completo 1:1, con ancho completo (504 mm): cono difusor y entrada, cajón con deflector, rampa curva de la cresta (R = 60 mm, sin labio; ver `prototipo_fase1/ESPECIFICACIONES_FASE1.md` §5), malla de 12° (con la **malla real de acero inoxidable de 30 mesh**), tobogán recto, arco de radio 915 mm y tramo recto final
hasta la línea de conteo, con la tapa y una ventana transparente en la línea de conteo. Cotas del script de Fusion 360.

Materiales sugeridos: acrílico transparente para paredes, cajón y tapa; PVC o acrílico para el fondo del tobogán; la ventana del
fondo de la línea de conteo en el mismo material que tendrá la máquina; cinta o regla graduada pegada en el costado; sin rugosidad
añadida (la pared del acero pulido es hidráulicamente lisa).

Diferencia a tener en cuenta: el acrílico moja distinto que el acero (ángulo de contacto). Con láminas de 8–12 mm y ~2 m/s pesa
poco, pero conviene repetir las pruebas 5 y 6 (superficie y ondas) con una chapa de acero pulido en el tobogán si se puede.

## Instrumentación mínima

- Caudal: tanque con nivel o caudalímetro; comprobación con cubeta y cronómetro. Rango de 4 a 15 L/s.
- Nivel del agua: regla o calibrador de puntas en el cajón (delante y detrás del deflector) y sobre la lámina.
- Velocidad: video lateral y cenital (120–240 imágenes por segundo, un smartphone sirve) con trazadores (papel picado, granos de
  arroz, burbujas) y una regla en el encuadre.
- Drenaje: cubeta bajo la malla y otra a la salida del tobogán; medir los dos caudales.
- Imagen: la cámara candidata (smartphone o global shutter) y un backlight de 850 nm y otro de 940 nm; ventana de la línea de conteo.
- Colorante alimentario y partículas para las pruebas de entrada y retención.

## Pruebas, valores esperados y umbral propuesto

Caudal de referencia 10 L/s salvo que se indique. «Esperado» = resultado del cálculo.

| # | Prueba | Cómo se mide | Esperado | Umbral propuesto de «pasa» |
|---|---|---|---|---|
| 1 | Nivel del cajón según caudal (4, 6, 8, 10, 12, 15 L/s) | Regla, detrás y delante del deflector | 122 mm detrás y 108 mm delante a 10 L/s | Dentro de ±6 mm a 10 L/s; anotar la curva completa |
| 2 | Espesor de la lámina a lo largo (0,1; 0,3; 0,5 m y línea de conteo) | Calibrador de puntas o video lateral con regla | 12,4 mm a 0,5 m sin drenaje; 8–10 mm en la línea de conteo (1D) | Dentro de ±1,5 mm; siempre ≥ 5 mm entre 8 y 12 L/s |
| 3 | Velocidad de la lámina | Video de trazadores, distancia entre cuadros | ~1,6 m/s a 0,5 m; ~2 m/s en la línea de conteo | Dentro de ±10 % |
| 4 | Drenaje de la malla (a 6, 8, 10, 12 L/s) | Caudal bajo la malla frente al caudal total | Supuesto 15–30 % | Medido; debe dejar ≥ 5 mm de lámina en la línea de conteo al caudal mínimo de trabajo |
| 5 | Superficie en la línea de conteo bajo el backlight | Video con la cámara candidata, agua sin larvas | Sin espuma ni ondas cortas | Sin objetos falsos parecidos a larvas por minuto (agua sin larvas); variación de brillo del fondo dentro de ±10 % antes de la corrección y ±3 % después |
| 6 | Ondas laterales de la profundidad | Espesor en 5 puntos a lo ancho, a 0,3 y 0,5 m | Desviación típica de 0,8–1,0 mm (±1,4 mm de amplitud) | Efecto en el brillo del fondo dentro de lo asumido en el punto 5 |
| 7 | Aire y salpicadura en la cresta | Video lento de la cresta y de la lámina (repetir con un labio de 5 mm montado, para comparar) | Sin aire arrastrado; sin agua fuera del canal | Ninguna salpicadura fuera del canal; sin burbujas > 1 mm bajo la lámina |
| 8 | Cajón: circulación y retención | Colorante en la entrada; tiempo hasta que sale | Renovación de ~6 s; 59 % de las líneas del flujo medio llegan a la lámina en 5–12 s | Definir con la ficha del lote: fracción del colorante que queda tras el enjuague de ~10 s |
| 9 | Entrada y cono difusor | Colorante en la boca del cono | 0,20 m/s en la boca; sin despegue | Sin retorno persistente; < 0,3 m/s en la boca |
| 10 | Nivelación | Inclinar la máquina ±1° de lado | El cálculo es simétrico; sin dato | La lámina sigue cubriendo todo el ancho y la asimetría es visible pero no rompe el conteo |
| 11 | Larvas (ensayo aparte, con larvas o sustitutos) | Video de entrada y salida; supervivencia a 24–48 h frente a un control | Tránsito ~0,85 s; todas llegan a la línea de conteo | A definir con el técnico: daño o mortalidad aceptable a ~2 m/s y en la caída final |

## Orden sugerido

1. Banco de la malla (prueba 4) con un trozo de malla a 12°: es lo más barato y fija el caudal mínimo.
2. Cajón, cresta y primeros 0,6 m con agua (pruebas 1, 2, 3, 7 y 9).
3. Recorrido completo con la línea de conteo, la ventana y la cámara (pruebas 2, 3, 5 y 6). Aquí se eligen la longitud de onda del
   backlight y la cámara.
4. Enjuague y retención (prueba 8), nivelación (10) y larvas (11).

## Criterios para dar luz verde al acero

Todas a la vez: pruebas 1, 2, 3 y 9 dentro de sus umbrales (el cálculo describe el flujo); la 4 medida y compatible con el caudal
mínimo de trabajo; la 5, 6 y 7 sin defectos que impidan detectar larvas o que las pierdan; la 8 y la 11 aceptables para el uso
previsto. Si alguna falla, se corrige la maqueta o el diseño (geometría de la cresta, deflector, pendiente, tapa) y se repite esa
prueba antes de cortar acero.

## Qué aporta el cálculo en paralelo

La fase 3 (arco y línea de conteo con la malla drenando al 15 % y al 30 %) da la predicción con la que se comparan las pruebas 2,
3, 5 y 6 en la línea de conteo. El cálculo y la maqueta se validan entre sí: si difieren, la maqueta manda y el modelo se ajusta.
