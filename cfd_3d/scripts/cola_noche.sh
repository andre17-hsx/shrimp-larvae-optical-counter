#!/bin/bash
# Corre varios casos uno tras otro (para dejarlos toda la noche).
#   uso (desde WSL):  bash cola_noche.sh <caso1> <caso2> ...
# Cada caso se ejecuta con correr_caso.sh (prioridad nice 5). El avance queda en cfd_3d/resultados/cola.log y la salida de
# cada caso en cfd_3d/resultados/cola_<caso>.out. Si un caso falla, se sigue con el siguiente.
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$BASE/resultados"
for c in "$@"; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') inicio $c" >> "$BASE/resultados/cola.log"
  bash "$BASE/scripts/correr_caso.sh" "$c" 5 > "$BASE/resultados/cola_$c.out" 2>&1
  echo "$(date '+%Y-%m-%d %H:%M:%S') fin $c (codigo $?)" >> "$BASE/resultados/cola.log"
done
echo "$(date '+%Y-%m-%d %H:%M:%S') cola terminada" >> "$BASE/resultados/cola.log"
