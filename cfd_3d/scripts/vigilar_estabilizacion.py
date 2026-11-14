# -*- coding: utf-8 -*-
"""Vigila un caso en marcha y avisa (termina) cuando el flujo se ha estabilizado o cuando el calculo se detiene.

Criterio de estabilidad: el volumen de agua del dominio (fraccion 'Phase-1 volume fraction' del registro de interFoam) deja
de cambiar, es decir, entra lo mismo que sale. Se mide la pendiente de esa fraccion en ventanas de 'ventana' s de tiempo
simulado y se exige que sea menor que 'umbral' (por segundo) en dos ventanas seguidas.

    python vigilar_estabilizacion.py <caso> [--ventana 0.2] [--umbral 2e-4] [--cada 300]
"""
import argparse
import re
import subprocess
import sys
import time


def leer(caso, lineas=6000):
    cmd = ['wsl.exe', '-d', 'Ubuntu', '--', 'bash', '-c',
           'tail -n %d ~/cfd/casos/%s/log.interFoam; echo ===PROC; pgrep -c -f "[m]pirun.*interFoam" || true' % (lineas, caso)]
    r = subprocess.run(cmd, capture_output=True)
    t = r.stdout.decode('utf-8', 'replace').replace('\x00', '')
    log, _, proc = t.partition('===PROC')
    try:
        n = int(proc.strip().split()[0])
    except Exception:
        n = -1
    return log, n


def serie(log):
    pares = {}
    t = None
    for l in log.splitlines():
        m = re.match(r'^Time = ([0-9.eE+-]+)', l)
        if m:
            t = float(m.group(1))
            continue
        m = re.search(r'Phase-1 volume fraction = ([0-9.eE+-]+)', l)
        if m and t is not None:
            pares[t] = float(m.group(1))
    ts = sorted(pares)
    return ts, [pares[x] for x in ts]


def pendiente(ts, fr, t_fin, ventana):
    idx = [i for i, x in enumerate(ts) if t_fin - ventana <= x <= t_fin]
    if len(idx) < 5:
        return None
    x = [ts[i] for i in idx]
    y = [fr[i] for i in idx]
    xm, ym = sum(x) / len(x), sum(y) / len(y)
    return sum((a - xm) * (b - ym) for a, b in zip(x, y)) / max(sum((a - xm) ** 2 for a in x), 1e-30)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('caso')
    ap.add_argument('--ventana', type=float, default=0.2)
    ap.add_argument('--umbral', type=float, default=2e-4)
    ap.add_argument('--cada', type=float, default=300.0)
    a = ap.parse_args()
    seguidas = 0
    while True:
        log, n = leer(a.caso)
        ts, fr = serie(log)
        if ts:
            t = ts[-1]
            p1 = pendiente(ts, fr, t, a.ventana)
            p0 = pendiente(ts, fr, t - a.ventana, a.ventana)
            print('%s | t = %.3f s | fraccion de agua %.5f | pendiente %s /s (ventana previa %s) | procesos interFoam: %d' % (
                time.strftime('%H:%M:%S'), t, fr[-1], ('%.2e' % p1) if p1 is not None else '-',
                ('%.2e' % p0) if p0 is not None else '-', n), flush=True)
            if p1 is not None and p0 is not None and abs(p1) < a.umbral and abs(p0) < a.umbral and t > 0.8:
                seguidas += 1
            else:
                seguidas = 0
            if seguidas >= 2:
                print('ESTABILIZADO en t = %.3f s (pendiente del volumen de agua < %.1e /s en dos ventanas de %.2f s)' %
                      (t, a.umbral, a.ventana), flush=True)
                sys.exit(0)
        if n == 0:
            print('EL CALCULO SE DETUVO en t = %s s' % (ts[-1] if ts else '?'), flush=True)
            sys.exit(1)
        time.sleep(a.cada)
