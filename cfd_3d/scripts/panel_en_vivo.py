# -*- coding: utf-8 -*-
"""Panel 'en vivo' de un calculo de OpenFOAM: pagina HTML que se actualiza sola.

Cada 'cada' segundos lee el registro del solver (tiempo simulado, paso, velocidad de calculo, Courant, volumen de agua) y,
si hay un tiempo nuevo escrito, hace una foto 3D de la lamina con pvbatch. Escribe en cfd_3d/vistas/<caso>/:
    en_vivo.html   (abrir en el navegador; se recarga cada 60 s)
    ultimo.png     foto del ultimo tiempo escrito
    t_<tiempo>.png historial de fotos
    volumen.png    volumen de agua del dominio frente al tiempo

    python panel_en_vivo.py <caso> [--cada 900] [--tfin 4]
Requiere matplotlib (entorno simenv).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
VISTAS = os.path.join(AQUI, '..', 'vistas')


def _wslpath(p):
    p = os.path.abspath(p)
    return '/mnt/' + p[0].lower() + p[2:].replace(os.sep, '/')


WSL_USER = os.environ.get('WSL_USER')  # vacio = usuario por defecto de la distro
WSL = ['wsl.exe', '-d', 'Ubuntu'] + (['-u', WSL_USER] if WSL_USER else []) + ['--', 'bash', '-c']
WIN_FOTO = _wslpath(os.path.join(AQUI, 'paraview', 'foto_lamina.py'))
WIN_VISTAS = _wslpath(VISTAS)


def wsl(cmd, timeout=600):
    r = subprocess.run(WSL + [cmd], capture_output=True, timeout=timeout)
    return r.stdout.decode('utf-8', 'replace').replace('\x00', '')


def leer_registro(caso):
    t = wsl('tail -n 8000 ~/cfd/casos/%s/log.interFoam' % caso)
    tiempo, frac = {}, {}
    actual = None
    dt = co = ejec = None
    for l in t.splitlines():
        m = re.match(r'^Time = ([0-9.eE+-]+)', l)
        if m:
            actual = float(m.group(1))
            continue
        m = re.search(r'Phase-1 volume fraction = ([0-9.eE+-]+)', l)
        if m and actual is not None:
            frac[actual] = float(m.group(1))
        m = re.match(r'^deltaT = ([0-9.eE+-]+)', l)
        if m:
            dt = float(m.group(1))
        m = re.match(r'^Courant Number mean: \S+ max: ([0-9.eE+-]+)', l)
        if m:
            co = float(m.group(1))
        m = re.match(r'^ExecutionTime = ([0-9.]+) s\s+ClockTime = ([0-9.]+) s', l)
        if m:
            ejec = (float(m.group(1)), actual)
    return frac, dt, co, ejec


def ultimo_tiempo_escrito(caso):
    s = wsl('ls ~/cfd/casos/%s/processor0 2>/dev/null' % caso).split()
    ts = []
    for x in s:
        try:
            ts.append(float(x))
        except ValueError:
            pass
    return max(ts) if ts else None


def html(caso, t_ult, t_sim, dt, co, vel, eta_txt, fotos, tfin):
    filas = ''.join('<li><a href="%s">t = %s s</a></li>' % (f, f[2:-4]) for f in fotos[-12:][::-1])
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta http-equiv="refresh" content="60">
<title>%(caso)s en vivo</title>
<style>body{font-family:system-ui,Segoe UI,sans-serif;margin:16px;background:#14161a;color:#e6e8ec}
img{max-width:100%%;border-radius:6px}.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:12px 0}
.k{background:#20232a;border-radius:8px;padding:10px 12px}.k b{display:block;font-size:1.3em}a{color:#8ab4f8}</style></head><body>
<h2>Caso %(caso)s</h2><p>Actualizado %(ahora)s. La pagina se recarga sola cada minuto.</p>
<div class="g">
<div class="k">Tiempo simulado<b>%(t_sim).3f s</b>de %(tfin)g s</div>
<div class="k">Paso de tiempo<b>%(dt)s</b></div>
<div class="k">Courant maximo<b>%(co)s</b></div>
<div class="k">Velocidad de calculo<b>%(vel)s</b></div>
<div class="k">Tiempo restante estimado<b>%(eta)s</b>hasta %(tfin)g s</div>
<div class="k">Ultimo tiempo escrito<b>%(t_ult)s s</b></div></div>
<h3>Lamina de agua (superficie libre, color = velocidad)</h3><img src="ultimo.png">
<h3>Volumen de agua del dominio</h3><img src="volumen.png" style="max-width:640px">
<h3>Fotos anteriores</h3><ul>%(filas)s</ul></body></html>""" % dict(
        caso=caso, ahora=time.strftime('%H:%M:%S'), t_sim=t_sim, dt=('%.2e s' % dt) if dt else '-', co=('%.2f' % co) if co else '-',
        vel=vel, eta=eta_txt, tfin=tfin, t_ult=('%.4g' % t_ult) if t_ult is not None else '-', filas=filas)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('caso')
    ap.add_argument('--cada', type=float, default=900.0)
    ap.add_argument('--tfin', type=float, default=4.0)
    a = ap.parse_args()
    carpeta = os.path.join(VISTAS, a.caso)
    os.makedirs(carpeta, exist_ok=True)
    foto_hecha = None
    historial = []
    while True:
        try:
            frac, dt, co, ejec = leer_registro(a.caso)
            t_sim = max(frac) if frac else 0.0
            t_ult = ultimo_tiempo_escrito(a.caso)
            if t_ult is not None and t_ult != foto_hecha and t_ult > 0:
                nombre = 't_%.4g.png' % t_ult
                r = wsl("cd ~; pvbatch '%s' $HOME/cfd/casos/%s '%s/%s/%s' 2>&1 | tail -2" % (WIN_FOTO, a.caso, WIN_VISTAS, a.caso, nombre))
                if os.path.exists(os.path.join(carpeta, nombre)):
                    shutil.copy(os.path.join(carpeta, nombre), os.path.join(carpeta, 'ultimo.png'))
                    historial.append(nombre)
                    foto_hecha = t_ult
            if frac:
                ts = sorted(frac)
                fig, ax = plt.subplots(figsize=(6.4, 2.6))
                ax.plot(ts, [frac[x] for x in ts], lw=1.5)
                ax.set_xlabel('tiempo simulado (s)')
                ax.set_ylabel('fraccion de agua')
                ax.grid(alpha=0.3)
                fig.savefig(os.path.join(carpeta, 'volumen.png'), dpi=110, bbox_inches='tight')
                plt.close(fig)
            vel, eta = '-', '-'
            if ejec and ejec[1]:
                vel = '%.3f s simulados por hora' % (3600.0 * ejec[1] / ejec[0])
                rest = (a.tfin - ejec[1]) * ejec[0] / ejec[1] / 3600.0
                eta = '%.1f h' % max(rest, 0)
            with open(os.path.join(carpeta, 'en_vivo.html'), 'w', encoding='utf-8') as f:
                f.write(html(a.caso, t_ult, t_sim, dt, co, vel, eta, historial, a.tfin))
            print('%s | t = %.3f s | ultimo escrito %s | %s' % (time.strftime('%H:%M:%S'), t_sim, t_ult, vel), flush=True)
        except Exception as e:  # el panel no debe caerse por un fallo puntual
            print('error en el panel: %s' % e, flush=True)
        time.sleep(a.cada)
