# -*- coding: utf-8 -*-
"""Biblioteca de comprobacion de estanqueidad: cuerpos CadQuery -> celdas -> busqueda de caminos de fuga."""
import time
import numpy as np
from scipy import ndimage as ndi

VECINOS6 = None


def triangulos(forma, tol=0.2, ang=0.3):
    verts, tris = forma.tessellate(tol, ang)
    V = np.array([[v.x, v.y, v.z] for v in verts], float)
    T = np.array(tris, int)
    return V, T


class Region:
    """Caja de analisis discretizada en celdas cubicas de lado 'paso' (mm)."""

    def __init__(self, nombre, minimo, maximo, paso, zcap=None):
        self.nombre, self.paso, self.zcap = nombre, float(paso), zcap
        # retícula desplazada una fraccion de celda: evita que caras a cotas redondas caigan justo en el borde
        self.min = np.array(minimo, float) - 0.37 * self.paso
        self.dims = np.ceil((np.array(maximo, float) - self.min) / self.paso).astype(int)
        self.barrera = np.zeros(self.dims, bool)
        self.indices = {}          # cuerpo -> indices lineales (para saber que cuerpos rodean una fuga)
        self.semillas = {}

    # ---- coordenadas ----
    def a_celda(self, p):
        return tuple(np.floor((np.asarray(p, float) - self.min) / self.paso).astype(int))

    def a_mm(self, ijk):
        return self.min + (np.asarray(ijk, float) + 0.5) * self.paso

    # ---- barrera ----
    def agregar(self, nombre, forma):
        V, T = triangulos(forma)
        P = V[T]                                             # (m,3,3)
        lo = (P.min(1) - self.min) / self.paso
        hi = (P.max(1) - self.min) / self.paso
        dentro = (hi >= -1).all(1) & (lo <= self.dims + 1).all(1)
        P, lo, hi = P[dentro], lo[dentro], hi[dentro]
        if len(P) == 0:
            self.indices[nombre] = np.zeros(0, np.int64)
            return
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nn = np.linalg.norm(n, axis=1)
        eps = 1e-6
        salida = []
        for t in range(len(P)):
            A, B, C = P[t]
            # se proyecta por los TRES ejes: asi todo segmento entre centros de celdas vecinas que cruce el
            # triangulo deja marcada una de las dos celdas (cierre estanco por construccion)
            for a in range(3):
                if abs(n[t, a]) < 1e-9 * max(nn[t], 1e-30):
                    continue
                u, v = [k for k in range(3) if k != a]
                i0, i1 = max(int(np.floor(lo[t, u])), 0), min(int(np.floor(hi[t, u])), self.dims[u] - 1)
                j0, j1 = max(int(np.floor(lo[t, v])), 0), min(int(np.floor(hi[t, v])), self.dims[v] - 1)
                if i1 < i0 or j1 < j0:
                    continue
                d = (B[v] - C[v]) * (A[u] - C[u]) + (C[u] - B[u]) * (A[v] - C[v])
                if abs(d) < 1e-12:
                    continue
                iu = np.arange(i0, i1 + 1)
                jv = np.arange(j0, j1 + 1)
                UU = (self.min[u] + (iu + 0.5) * self.paso)[:, None]
                VV = (self.min[v] + (jv + 0.5) * self.paso)[None, :]
                l1 = ((B[v] - C[v]) * (UU - C[u]) + (C[u] - B[u]) * (VV - C[v])) / d
                l2 = ((C[v] - A[v]) * (UU - C[u]) + (A[u] - C[u]) * (VV - C[v])) / d
                l3 = 1.0 - l1 - l2
                m = (l1 >= -eps) & (l2 >= -eps) & (l3 >= -eps)
                if not m.any():
                    continue
                W = l1 * A[a] + l2 * B[a] + l3 * C[a]
                ii, jj = np.nonzero(m)
                k = np.floor((W[ii, jj] - self.min[a]) / self.paso).astype(int)
                ok = (k >= 0) & (k < self.dims[a])
                if not ok.any():
                    continue
                xyz = np.empty((ok.sum(), 3), int)
                xyz[:, u] = iu[ii[ok]]
                xyz[:, v] = jv[jj[ok]]
                xyz[:, a] = k[ok]
                salida.append(xyz)
        if not salida:
            self.indices[nombre] = np.zeros(0, np.int64)
            return
        xyz = np.concatenate(salida)
        lin = np.unique(np.ravel_multi_index(xyz.T, self.dims))
        self.barrera.flat[lin] = True
        self.indices[nombre] = lin

    # ---- fluido ----
    def preparar(self):
        self.edt = ndi.distance_transform_edt(~self.barrera).astype(np.float32)
        D = np.ones(self.dims, bool)
        if self.zcap is not None:
            kmax = int(np.floor((self.zcap - self.min[2]) / self.paso))
            D[:, :, kmax + 1:] = False
        self.D = D
        self.fluido = D & ~self.barrera

    def semilla(self, nombre, punto, radio_mm=14.0):
        """Celda de fluido con mayor holgura dentro de un cubo alrededor de 'punto'."""
        c = np.array(self.a_celda(punto))
        r = int(np.ceil(radio_mm / self.paso))
        lo = np.maximum(c - r, 0)
        hi = np.minimum(c + r + 1, self.dims)
        sub = np.where(self.fluido[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]],
                       self.edt[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]], -1.0)
        if sub.max() < 0:
            raise RuntimeError('La semilla %s cae dentro de una pared o fuera del dominio (%s)' % (nombre, punto))
        loc = np.unravel_index(sub.argmax(), sub.shape)
        self.semillas[nombre] = tuple(int(lo[q] + loc[q]) for q in range(3))
        return self.semillas[nombre]


def camino_evitando_paredes(fluido, edt, a, b, K=30.0):
    """Camino de costo minimo (6-vecinos) donde las celdas pegadas a paredes cuestan mucho: solo se
    aprieta por lo estrecho cuando no hay alternativa, es decir, en la fuga. None si no hay camino."""
    from skimage.graph import MCP
    cost = np.where(fluido, 1.0 + K / np.maximum(edt, 1.0) ** 3, np.inf)
    m = MCP(cost, fully_connected=False)
    costos, _ = m.find_costs([a], [b])
    if not np.isfinite(costos[b]):
        return None
    return np.array(m.traceback(b))


def cuerpos_cercanos(reg, ijk, ventana=3):
    lo = np.maximum(np.array(ijk) - ventana, 0)
    hi = np.minimum(np.array(ijk) + ventana + 1, reg.dims)
    X, Y, Z = np.meshgrid(*[np.arange(lo[q], hi[q]) for q in range(3)], indexing='ij')
    win = np.ravel_multi_index((X.ravel(), Y.ravel(), Z.ravel()), reg.dims)
    res = []
    for nombre, lin in reg.indices.items():
        if lin.size and np.isin(win, lin).any():
            res.append(nombre)
    return res


def buscar_fugas(reg, pares, max_iter=25, log=print):
    """Para cada par de semillas que sigan conectadas: localiza el paso mas estrecho del camino mas corto,
    lo tapona y repite hasta que no queden caminos. Devuelve la lista de fugas."""
    fugas = []
    fluido = reg.fluido.copy()
    for it in range(max_iter):
        hallada = False
        lab, _n = ndi.label(fluido)                  # 6-vecinos
        for (na, nb) in pares:
            a, b = reg.semillas[na], reg.semillas[nb]
            if lab[a] == 0 or lab[a] != lab[b]:
                continue                             # sellado entre estos dos
            ruta = camino_evitando_paredes(fluido, reg.edt, a, b)
            if ruta is None:
                continue
            e = reg.edt[ruta[:, 0], ruta[:, 1], ruta[:, 2]]
            k = int(e.argmin())
            cel = tuple(int(x) for x in ruta[k])
            emin = float(e[k])
            fugas.append({'par': (na, nb), 'punto': reg.a_mm(cel), 'celda': cel, 'edt': emin,
                          'apertura_mm': ((2 * emin - 1) * reg.paso, 2 * emin * reg.paso),
                          'largo_camino_mm': len(ruta) * reg.paso,
                          'cerca': cuerpos_cercanos(reg, cel)})
            # tapon esferico: quita las celdas estrechas (pegadas a paredes) alrededor del paso de fuga
            Rmm = max(60.0, 3.0 * emin * reg.paso)
            R = int(np.ceil(Rmm / reg.paso))
            lo = np.maximum(np.array(cel) - R, 0)
            hi = np.minimum(np.array(cel) + R + 1, reg.dims)
            sl = tuple(slice(lo[q], hi[q]) for q in range(3))
            X, Y, Z = np.meshgrid(*[np.arange(lo[q], hi[q]) for q in range(3)], indexing='ij')
            esfera = (X - cel[0]) ** 2 + (Y - cel[1]) ** 2 + (Z - cel[2]) ** 2 <= R * R
            sub = fluido[sl]
            sub[esfera & (reg.edt[sl] <= emin + 1.0)] = False
            fugas[-1]['radio_tapon_mm'] = Rmm
            hallada = True
            break
        if not hallada:
            break
    return fugas


def agrupar(fugas, paso):
    """Une fugas del mismo par cuyos puntos estan a menos de 2 radios de tapon: es la misma rendija."""
    n = len(fugas)
    padre = list(range(n))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if fugas[i]['par'] != fugas[j]['par']:
                continue
            d = float(np.linalg.norm(fugas[i]['punto'] - fugas[j]['punto']))
            if d <= 1.05 * (fugas[i]['radio_tapon_mm'] + fugas[j]['radio_tapon_mm']):
                padre[raiz(i)] = raiz(j)
    grupos = {}
    for i in range(n):
        grupos.setdefault(raiz(i), []).append(fugas[i])
    res = []
    for g in grupos.values():
        pts = np.array([f['punto'] for f in g])
        cerca = sorted({c for f in g for c in f['cerca']})
        res.append({'par': g[0]['par'], 'n_puntos': len(g), 'centro': pts.mean(0),
                    'caja': (pts.min(0) - paso / 2, pts.max(0) + paso / 2),
                    'apertura_mm': (min(f['apertura_mm'][0] for f in g), max(f['apertura_mm'][1] for f in g)),
                    'cerca': cerca, 'puntos': pts})
    res.sort(key=lambda r: -r['n_puntos'])
    return res
