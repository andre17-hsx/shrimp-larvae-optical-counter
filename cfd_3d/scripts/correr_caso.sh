#!/bin/bash
# Corre un caso de OpenFOAM dentro de WSL y trae los resultados a Windows.
#   uso (desde WSL):  bash correr_caso.sh <nombre_del_caso> [prioridad]
# El caso vive en cfd_3d/casos/<nombre> (Windows). Se copia a ~/cfd/casos/<nombre> (disco de Linux, mas rapido),
# se ejecuta su ./Allrun y se copian de vuelta a cfd_3d/resultados/<nombre> los registros y el ultimo tiempo.
# 'prioridad' = valor de nice (0 por defecto; 10 para no molestar en el uso normal de Windows).
source /usr/lib/openfoam/openfoam2512/etc/bashrc
NOM=$1
PRIO=${2:-0}
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$HOME/cfd/casos/$NOM"
rm -rf "$DEST"
mkdir -p "$HOME/cfd/casos"
cp -r "$BASE/casos/$NOM" "$DEST"
cd "$DEST" || exit 1
tr -d '\r' < Allrun > Allrun.lf && mv Allrun.lf Allrun
t0=$(date +%s)
nice -n "$PRIO" bash ./Allrun
t1=$(date +%s)
echo "tiempo de pared: $((t1 - t0)) s" | tee log.tiempo
# resultados: registros + ultimo tiempo (+ mallas de referencia)
RES="$BASE/resultados/$NOM"
rm -rf "$RES"
mkdir -p "$RES"
cp log.* "$RES"/ 2>/dev/null
ultimo=$(ls -d [0-9]* 2>/dev/null | grep -v '^0$' | sort -g | tail -1)
[ -n "$ultimo" ] && cp -r "$ultimo" "$RES"/
[ -d constant/polyMesh ] && cp -r 0.orig "$RES"/ 2>/dev/null
echo "resultados en $RES (ultimo tiempo: $ultimo)"
