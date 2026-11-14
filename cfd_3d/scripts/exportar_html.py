# -*- coding: utf-8 -*-
"""Exporta la pagina del informe (cfd_3d/informe_preliminar/index.html) como UN solo archivo HTML autonomo: imagenes, cuadros de
la animacion y datos 3D incrustados. Solo necesita internet para la libreria 3D y la tipografia (o, con --three, usa una copia
local de three.min.js incrustada, y funciona sin conexion).

    python exportar_html.py [--three ruta/a/three.min.js] [--salida nombre.html]
"""
import argparse
import base64
import json
import mimetypes
import os
import re

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'informe_preliminar')


def datauri(ruta):
    mime = mimetypes.guess_type(ruta)[0] or 'application/octet-stream'
    return 'data:%s;base64,%s' % (mime, base64.b64encode(open(ruta, 'rb').read()).decode('ascii'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--three', default=None)
    ap.add_argument('--salida', default='Informe_flujo_prototipo.html')
    a = ap.parse_args()
    t = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    fin_estilo = t.index('</style>') + len('</style>')
    cabeza, cuerpo = t[:fin_estilo], t[fin_estilo:]
    # imagenes
    def img(m):
        return 'src="%s"' % datauri(os.path.join(RAIZ, m.group(1)))
    cuerpo = re.sub(r'src="(img/[^"]+)"', img, cuerpo)
    cuerpo = cuerpo.replace("url(img/final_t4.jpg)", "url(%s)" % datauri(os.path.join(RAIZ, 'img', 'final_t4.jpg')))
    # cuadros de la animacion
    n = len(json.load(open(os.path.join(RAIZ, 'frames', 'tiempos.json'))))
    cuadros = [datauri(os.path.join(RAIZ, 'frames', 'f%02d.jpg' % i)) for i in range(n)]
    viejo = "function fname(i){return 'frames/f'+(i<10?'0':'')+i+'.jpg';}"
    assert viejo in cuerpo
    cuerpo = cuerpo.replace(viejo, "var FRAMES=%s;function fname(i){return FRAMES[i];}" % json.dumps(cuadros))
    # datos 3d
    datos = open(os.path.join(RAIZ, 'datos3d.js'), encoding='ascii').read()
    assert '<script src="datos3d.js"></script>' in cuerpo
    cuerpo = cuerpo.replace('<script src="datos3d.js"></script>', '<script>' + datos + '</script>')
    # libreria 3d
    tag = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
    assert tag in cuerpo
    if a.three:
        cuerpo = cuerpo.replace(tag, '<script>' + open(a.three, encoding='utf-8').read() + '</script>')
    pre = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
           '<style>html{color-scheme:light}[hidden]{display:none!important}img{max-width:100%}</style>\n')
    html = pre + cabeza + '\n</head>\n<body>\n' + cuerpo + '\n</body>\n</html>\n'
    for resto in ('src="img/', 'frames/f', 'datos3d.js', "url(img/"):
        assert resto not in html, resto
    ruta = os.path.join(RAIZ, a.salida)
    open(ruta, 'w', encoding='utf-8').write(html)
    print('escrito %s (%.1f MB) | libreria 3d: %s' % (os.path.abspath(ruta), len(html.encode('utf-8')) / 1e6, 'incrustada' if a.three else 'desde internet (cdnjs)'))


if __name__ == '__main__':
    main()
