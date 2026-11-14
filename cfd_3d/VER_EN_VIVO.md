# Cómo ver el cálculo mientras corre

El cálculo escribe una "foto" del estado completo cada 0,05 s simulados (unos 20–30 minutos de cálculo por foto). No es
una película fluida: cada vez que aparece un tiempo nuevo se puede ver ese estado.

## Opción 1: página que se actualiza sola (sin abrir nada más)

`cfd_3d/vistas/p2_medio_grueso/en_vivo.html`: abrir con el navegador. Se recarga cada minuto y muestra el tiempo simulado, el
paso de tiempo, el número de Courant, el tiempo restante estimado, la foto 3D de la lámina de agua y el volumen de agua.
La genera `scripts/panel_en_vivo.py` (queda corriendo en segundo plano; una foto nueva por cada tiempo escrito).

## Opción 2: ParaView, para girar y explorar

1. Abrir una terminal de Windows (PowerShell) y ejecutar:

```
wsl -d Ubuntu -- paraview --script="<repo>/cfd_3d/scripts/paraview/ver_lamina.py"
```

2. Se abre ParaView con la superficie libre del agua (color = velocidad) y las paredes translúcidas, en el último tiempo escrito.
3. Para seguir el cálculo: en el panel **Properties**, botón **Reload Files** (flechas circulares) y luego **Last Frame** (▶| en la barra superior).

En ParaView también se puede: colorear por otra variable (`alpha.water`, `p_rgh`), cortar con **Slice** (por ejemplo a lo largo del eje y = 0 para
ver el perfil de la lámina sobre la cresta) y ver la malla con **Surface With Edges**. Para otro caso, definir la variable de entorno
`CASO_FOAM=~/cfd/casos/<caso>/caso.foam` antes del comando.

## Opción 3: una foto puntual desde la terminal

```
wsl -d Ubuntu -- pvbatch "<repo>/cfd_3d/scripts/paraview/foto_lamina.py" ~/cfd/casos/p2_medio_grueso "<salida>/foto.png"
```

## La malla

`snappyHexMesh` refina, recorta y ajusta la malla en unos 5 minutos. La malla final de cualquier caso se ve en ParaView (sección
"La malla" arriba). Para ver las etapas intermedias (refinada, recortada, ajustada) hay que correr `snappyHexMesh` sin `-overwrite`;
se puede pedir para los casos nuevos.

## Qué mirar

- **Color de la lámina:** azul oscuro = agua casi quieta (cajón), verde-amarillo = 1–2 m/s (lámina sobre la malla).
- **Frente de agua:** al principio la lámina avanza sobre la malla seca; no es el flujo definitivo. El flujo se compara con los
  criterios de aceptación solo cuando el volumen de agua deja de cambiar (ver `scripts/vigilar_estabilizacion.py`).
