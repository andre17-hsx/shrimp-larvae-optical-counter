# Simulación del flujo del canal de conteo

Simula el agua (y las larvas como trazadores) en el canal del modelo 3D, con la geometría leída directamente de
`Fusion360_VAKI_Macro/Fusion360_VAKI_Macro.py`, de modo que el modelo y la simulación no se desincronizan.
Los resultados y su interpretación están en [`INFORME_FLUJO.md`](INFORME_FLUJO.md).

## Requisitos

```
pip install numpy scipy numba matplotlib
```

No hace falta Fusion 360: `fake_adsk.py` simula lo justo de `adsk` para importar el script y leer sus constantes.
Si la ruta del script es otra: `set SCRIPT_MODELO=C:\ruta\Fusion360_VAKI_Macro.py`.

## Cómo se usa

| Comando | Qué hace | Tiempo |
|---|---|---|
| `python geometria_canal.py` | imprime la geometría desenrollada (largos, arco, contracción, línea de conteo) | 1 s |
| `python verificar_swe.py` | pruebas del resolvedor 2D contra soluciones conocidas | 2 min |
| `python ejecutar_todo.py` | casos finales A y B, barrido de caudal, pulsaciones, larvas y figuras | 12 min |
| `python sensibilidad.py` | malla de drenaje (0/15/30 %) y rugosidad de Manning | 5 min |
| `python entrada_desigual.py` | B con entrada desigual al cajón (inclinada, chorro central o lateral, ondulada) | 4 min |
| `python pulsaciones.py` | respuesta del canal solo a pulsaciones del caudal | 1 min |
| `python regenerar_figuras.py` | rehace las figuras desde `resultados/` sin simular | 20 s |

Después de cambiar el modelo de Fusion (constantes o geometría) basta volver a correr `ejecutar_todo.py`.

## Archivos

| Archivo | Contenido |
|---|---|
| `geometria_canal.py` | canal desenrollado (coordenada `s` sobre el fondo, ancho, pendiente, curvatura del arco) |
| `flujo_1d.py` | etapa 1: perfil 1D del agua (paso estándar, energía + Manning + curvatura), drenaje de la malla |
| `swe2d.py` | etapa 2: aguas someras 2D (volúmenes finitos, HLL, MUSCL, Runge-Kutta 2), numba en paralelo |
| `contracciones.py` | familias de contracción y métricas de uniformidad en la ventana de conteo |
| `aproximacion.py` | cajón + canal en un solo dominio, con el estrechamiento antes de la cresta (diseño B) |
| `larvas.py`, `analisis_larvas.py` | trazadores pasivos con dispersión turbulenta y estadística de solapamiento |
| `pulsaciones.py` | respuesta a pulsaciones del caudal (bomba, variador) |
| `graficos*.py`, `regenerar_figuras.py` | figuras |
| `resultados/` | figuras, `resultados_finales.json`, `sensibilidad.json`, campos 2D (`final_A.npz`, `final_B.npz`) |

## Qué es cada caso

- **A** — diseño anterior del modelo (ya no está en el script): las paredes de contracción de 47° iban sobre la malla,
  ya con el flujo supercrítico.
- **B** — diseño actual del modelo: el estrechamiento (994 → 504 mm) está en el cajón, antes de la cresta, con flujo lento:
  `L_ESTRECH` = 250 mm en forma de coseno y `L_ESTRECH_RECTO` = 150 mm rectos justo antes de la cresta (constantes del
  script). El coseno del modelo termina a 988 mm (la chapa apoya en la pared lateral) y el de la simulación a 994 mm:
  diferencia despreciable.

## Modelo y supuestos

- Ecuaciones de Saint-Venant 2D promediadas en profundidad sobre el canal desenrollado, con `g cos θ(s)`,
  fricción de Manning (n = 0,010 chapa lisa) y paredes como celdas sólidas con reflexión.
- Drenaje de la malla como sumidero `w = kd · √(2 g h cos θ)` sobre la malla; el agua drenada sale con su velocidad.
  `kd` **no está medido**: se calibra para que la malla drene un porcentaje del caudal (15 % por defecto).
- El cajón se representa con el fondo a la altura de la cresta (calado H sobre ella): hipótesis desfavorable.
- Larvas: trazadores pasivos con factor de velocidad 0,75–1,0 (van cerca del fondo), dispersión lateral `D = 0,15 h u*`.
  Solapamiento con huellas rectangulares 10 × 1,5 mm, estiradas por la relación de velocidades (cámara lineal).

## Lo que este modelo NO representa

Entrada de aire y salpicaduras, ondas capilares de la superficie (We ≈ 500), flujos secundarios 3D en el cajón y la
cresta, la capa límite de las paredes laterales, tensión superficial en los bordes, y el comportamiento real de las
larvas (nado, adherencia, choques). Para eso: maqueta transparente 1:1 o una simulación 3D con superficie libre
(OpenFOAM, interFoam) de la zona cresta + primeros 0,5 m.
