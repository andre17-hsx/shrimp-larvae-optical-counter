# -*- coding: utf-8 -*-
"""Validez de los cuerpos y choques del modelo en las 5 combinaciones extremas de patas (AJUSTE_PATAS) y altura de
salida (ALTO_SALIDA). Para cada una genera una copia del script con esos valores, la simula con fake_adsk y reconstruye
los solidos con reconstruir.py (que cuenta los choques de mas de 1 mm3).

    python choques_configuraciones.py [ruta/al/script.py]
"""
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, '..', 'Fusion360_VAKI_Macro', 'Fusion360_VAKI_Macro.py')
CONFIGS = ((None, None), (0, 470), (1, 1070), (0, 1070), (1, 470))       # (None, None) = valores del script

if __name__ == '__main__':
    texto = open(SCRIPT, encoding='utf-8').read()
    tmp = os.path.join(AQUI, 'script_config_tmp.py')
    for patas, salida in CONFIGS:
        t = texto
        if patas is not None:
            t = re.sub(r'^AJUSTE_PATAS = [0-9.]+', 'AJUSTE_PATAS = %s' % patas, t, flags=re.M)
            t = re.sub(r'^ALTO_SALIDA = [0-9]+', 'ALTO_SALIDA = %s' % salida, t, flags=re.M)
        open(tmp, 'w', encoding='utf-8').write(t)
        subprocess.run([sys.executable, os.path.join(AQUI, 'fake_adsk.py'), tmp, os.path.join(AQUI, 'fusion_sim.json')],
                       check=True, stdout=subprocess.DEVNULL)
        r = subprocess.run([sys.executable, os.path.join(AQUI, 'reconstruir.py')], capture_output=True, text=True, check=True)
        lineas = [l for l in r.stdout.splitlines()
                  if l.startswith(('cuerpos reconstruidos', 'choques')) or ('mm3' in l and '<->' in l)]
        print('AJUSTE_PATAS=%s ALTO_SALIDA=%s' % (patas if patas is not None else 'del script', salida if salida is not None else 'del script'))
        for l in lineas:
            print('   ' + l)
    os.remove(tmp)
