# Plan de validación por CFD 3D (OpenFOAM, superficie libre)

Objetivo: comprobar con agua 3D real, **antes de fabricar**, que el diseño actual del contador (`Fusion360_VAKI_Macro.py`)
da la lámina que necesita la cámara y no maltrata a la larva. La simulación 2D de `../simulacion_flujo/` es una
estimación; este plan la reemplaza por cálculos más completos y, donde no alcanza, dice qué hay que medir.

## Herramientas y equipo

- OpenFOAM v2512 (OpenCFD, ESI) en Ubuntu 26.04 sobre WSL2. `interFoam` (VOF), turbulencia `kOmegaSST`, mallado con
  `blockMesh` / `snappyHexMesh`.
- Equipo: i7-13620H (10 núcleos), 15,7 GB de RAM (WSL: 12 GB, 12 hilos, 8 GB de swap), sin GPU. Una malla cómoda tiene
  hasta ~5–6 millones de celdas; por eso el canal se simula por tramos y con la mitad del ancho (simetría).

## Fases

| Fase | Pregunta | Método | Se acepta si |
|---|---|---|---|
| **0. Prueba del método** | ¿Este montaje acierta problemas con respuesta conocida? | Lámina sobre plano de 12° (frente a Manning y a pared lisa), salto oblicuo (teoría), descarga sobre la cresta (q = 1,705 H^1,5) | Errores dentro de ~10 % en profundidad y ~5° en ángulo de onda, con la malla que se usará |
| **1. Cresta, corte 2D fino** | ¿El escalón de 60 mm despega el flujo o mete aire? ¿Hay control crítico en la cresta? | 2D vertical: cajón → escalón → malla a 12°, tres tamaños de celda | Sin recirculación mayor que ~1 calado, sin aire arrastrado, q = 1,705 H^1,5 ± 5 % |
| **2. 3D: cajón, estrechamiento y cresta** | ¿Llega uniforme a la malla? ¿Cuánto influyen el deflector y la entrada? | Medio ancho (simetría), celdas de 3–4 mm en el cajón y ~1 mm cerca de la cresta | Variación de lámina < 5 % a 0,5 m de la cresta |
| **3. 3D: arco y línea de conteo** | ¿La lámina en la ventana es uniforme, sin espuma ni ondas? | Medio ancho, celdas de ~1 mm, entrada mapeada desde la fase 2 | Ver criterios abajo |
| **4. Cono difusor** | ¿Se despega el flujo? ¿A qué velocidad entra al cajón? | RANS estacionario monofásico, luego superficie libre | Sin retorno de flujo persistente; < 0,3 m/s al entrar al cajón |
| **5. Malla real** | Coeficiente de drenaje | Prueba de banco con un trozo de malla (no es CFD) | Se mide, no se supone |

Cada fase deja sus resultados en `resultados/<caso>/`, con los registros de OpenFOAM, y se documenta aquí.

## Criterios de aceptación (confirmados por el usuario el 2026-09-24, sin cambios)

En la ventana de conteo, entre 6 y 12 L/s:

1. Variación de la lámina a lo ancho (CV) **< 5 %**.
2. Velocidad uniforme dentro de **±3 %** (para que el píxel de la cámara lineal sea constante).
3. **Sin despegue** con recirculación en la cresta ni en el cono difusor.
4. Velocidad de entrada al cajón **< 0,3 m/s**.
5. **Sin aire** arrastrado bajo la superficie en el conteo (fracción de aire < 1 % en la lámina).
6. Lámina de **al menos 5 mm** en la ventana (óptica del backlight).

## Lo que este plan NO cierra por sí solo

- El **drenaje real de la malla de 30 mesh** (aberturas de 0,55 mm): no se puede resolver en la malla de cálculo; entra como
  coeficiente medido (fase 5).
- La **rugosidad real** de la chapa: cambia el espesor y la velocidad de la lámina (ver fase 0).
- El **comportamiento de la larva** (nado, adherencia, choque): el CFD da el campo de velocidades, no cómo reacciona el animal.
- Un CFD sin comparar con un ensayo sigue siendo una estimación mejor fundada. Se recomienda una **maqueta transparente
  1:1** del tramo cajón + cresta + primeros 0,6 m y comparar la lámina con la fase 2.

## Cómo se corre

Los casos se generan desde Windows (`scripts/*.py` escriben en `casos/<nombre>/`) y se ejecutan en WSL:

```
wsl -d Ubuntu -- bash "<repo>/cfd_3d/scripts/correr_caso.sh" <caso> [nice]
```

`correr_caso.sh` copia el caso al disco de Linux, corre su `Allrun` y trae de vuelta los registros y el último tiempo.
