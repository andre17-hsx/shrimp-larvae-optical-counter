# CFD 3D del contador (OpenFOAM en WSL)

Ver [`PLAN_CFD.md`](PLAN_CFD.md) para el plan por fases, los criterios de aceptación y lo que el CFD no puede cerrar solo.

## Qué hay aquí

| Carpeta / archivo | Contenido |
|---|---|
| `scripts/geometria_cfd.py` | Construye el dominio de fluido (agua + aire) desde las constantes y funciones de `Fusion360_VAKI_Macro.py` y lo exporta como STL por parches (`inlet`, `outlet`, `atmosphere`, `symmetry`, `malla`, `paredes`) y zonas de refinamiento. Necesita CadQuery (el entorno de `verificacion_estanqueidad`). |
| `scripts/caso_snappy.py` | Genera un caso completo (`interFoam` + `kOmegaSST`, mallado con `snappyHexMesh`) sobre ese dominio: `--modo losa` (corte 2D) o `--modo medio` (semiancho 3D). |
| `scripts/f0a_pelicula.py`, `analizar_f0a.py` | Fase 0: lámina sobre plano inclinado frente a la teoría. |
| `scripts/correr_caso.sh` | Copia un caso a WSL, lo ejecuta y trae los resultados a `resultados/<caso>/`. |
| `scripts/analizar_criterios.py` | Evalúa un caso 3D de semiancho frente a los criterios de aceptación (lámina, velocidad, aire atrapado, contraflujo, comparación con el 1D). Ver el resultado en [`RESULTADOS_P2.md`](RESULTADOS_P2.md). |
| `geometria/` | STL del dominio, `dominio_info.json` y `dominio_vistas.png` para revisarlo. |
| `casos/` | Casos generados (se pueden borrar y regenerar). |
| `resultados/` | Registros de OpenFOAM y último tiempo de cada caso. |

Para ver un cálculo mientras corre (página que se actualiza sola, ParaView o una foto puntual): [`VER_EN_VIVO.md`](VER_EN_VIVO.md).

## Uso rápido

1. `python scripts/geometria_cfd.py` (dominio 3D) y `python scripts/geometria_cfd.py --losa 2` (corte 2D de 2 mm).
2. `python scripts/caso_snappy.py <nombre> --modo losa|medio [...]` genera el caso en `casos/<nombre>/`.
3. Ejecutar en WSL (mantiene la ventana abierta mientras corre):

```
wsl -d Ubuntu -- bash "<repo>/cfd_3d/scripts/correr_caso.sh" <nombre> 5
```

El `5` es la prioridad (`nice`): más alto = más amable con Windows.

## Ojo con WSL

WSL apaga su máquina virtual cuando ya no hay ninguna ventana o comando de Windows conectado. Un cálculo largo debe lanzarse
desde un comando que siga abierto (por ejemplo `scripts/lanzar_noche.bat`), no con `nohup` dentro de Linux.
