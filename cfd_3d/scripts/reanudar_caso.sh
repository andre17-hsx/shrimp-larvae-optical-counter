#!/bin/bash
# Reanuda un caso paralelo ya mallado desde su ultimo guardado y, al terminar, reconstruye y copia resultados a Windows.
#   uso (desde WSL):  bash reanudar_caso.sh <nombre_del_caso> [prioridad]
source /usr/lib/openfoam/openfoam2512/etc/bashrc
NOM=$1
PRIO=${2:-10}
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HOME/cfd/casos/$NOM" || exit 1
sed -i 's/startFrom *startTime;/startFrom latestTime;/' system/controlDict
[ -f log.interFoam ] && mv log.interFoam "log.interFoam.parte$(date +%s)"
nice -n "$PRIO" mpirun --use-hwthread-cpus -np 8 interFoam -parallel > log.interFoam 2>&1
reconstructPar -latestTime > log.reconstruct 2>&1
postProcess -func writeCellCentres -latestTime > log.C 2>&1
postProcess -func writeCellVolumes -latestTime > log.V 2>&1
RES="$BASE/resultados/$NOM"
rm -rf "$RES"
mkdir -p "$RES"
cp log.* "$RES"/ 2>/dev/null
ultimo=$(ls -d [0-9]* 2>/dev/null | grep -v '^0$' | sort -g | tail -1)
[ -n "$ultimo" ] && cp -r "$ultimo" "$RES"/
cp -r 0.orig "$RES"/ 2>/dev/null
echo "listo: $ultimo"
