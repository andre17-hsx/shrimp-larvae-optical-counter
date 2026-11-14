# Comprobación de estanqueidad del contador

Detecta huecos por donde escaparía el agua (o entraría a la carcasa del backlight) en el modelo generado por
`Fusion360_VAKI_Macro.py`. No sustituye la prueba hidrostática del prototipo.

## Qué hace
1. **Celdas** (`analisis_modelo.py`): convierte las piezas en celdas de 2 mm (cajón, malla, sumidero) o 3 mm
   (tobogán, embudo) y busca caminos entre el agua, el exterior, el sumidero y la carcasa del backlight.
   Encuentra huecos de unas 2 celdas de ancho o más (≈4 mm y ≈6 mm respectivamente).
2. **Distancia exacta** (`cercanias.py`): mide entre cuerpos vecinos y lista los que NO se tocan pero quedan
   a menos de 8 mm. Cubre las rendijas que la resolución de celdas no ve.
3. **Prueba de control** (`autotest.py`): cajas sintéticas cerradas y con rendijas, para verificar la herramienta.

## Supuestos
- Entrada, salida y desagüe del sumidero se toman como cerrados con tapones (válvula cerrada durante el conteo).
- La malla cuenta como barrera (la separación agua-sumidero por otro camino es una fuga).
- El cajón está abierto por arriba: solo se evalúa por debajo del nivel de agua de diseño.
- Se excluyen bastidor, tapa del sensor e instalación (no contienen agua).

## Uso
    pip install cadquery scipy scikit-image
    python autotest.py                 # prueba de control
    python analisis_modelo.py A1 A2b A2a A3
    python cercanias.py
    python choques_configuraciones.py  # cuerpos válidos y choques en las 5 combinaciones de patas y altura de salida
    # otro script del modelo:  SCRIPT_MODELO=ruta/al/script.py python analisis_modelo.py A1
    # defecto provocado:       QUITAR=nombre_de_cuerpo python analisis_modelo.py A1

Zonas: A1 = cajón + malla + sumidero, A2b = tobogán + carcasa backlight, A2a = embudo + tubo + acople, A3 = difusor de entrada
(cono bajo el fondo del cajón; la manguera se cierra con un tapón).

## Resultado sobre el modelo actual
Con el estrechamiento del cajón antes de la cresta (diseño B de `../simulacion_flujo/INFORME_FLUJO.md`) , entrada sin plato y contorno del cuerpo que sigue el estrechamiento: 91 cuerpos,
todos válidos, **0 choques** en las 5 configuraciones y **0 fugas** en las cuatro zonas. Una prueba provocada (quitando
`pared_estrechamiento_der`) es detectada como fuga de agua al exterior. Los pares separados por menos de 3 mm son
los mismos de antes (menos los de las piezas que desaparecieron), más malla ↔ brida a 2 mm (la malla ahora cabe en la ventana de la brida y el fondo del tobogán cierra
ese paso).

Historia: dos defectos encontrados y corregidos en el script (con el diseño anterior):
- Carcasa del backlight abierta por ambos lados (franja de 12 mm entre el borde del fondo y sus paredes).
- Cuña de 0,5 a 5,1 mm entre la cubierta y la parte alta de las paredes de contracción.
