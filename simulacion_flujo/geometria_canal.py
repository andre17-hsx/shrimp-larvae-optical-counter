# -*- coding: utf-8 -*-
"""Geometria del canal de conteo para la simulacion de flujo.

Se lee del mismo script de Fusion 360 (constantes y geometria()), asi el modelo 3D y la simulacion no se
desincronizan. Se trabaja con la coordenada s medida sobre el fondo, desde la cresta del vertedero hasta el
final del tobogan (X = XE), con el canal "desenrollado": recta de la malla -> recta inicial -> arco -> recta final.
"""
import os
import sys
import math
import importlib.util
from dataclasses import dataclass

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT_FUSION = os.environ.get(
    'SCRIPT_MODELO',
    os.path.join(AQUI, '..', 'Fusion360_VAKI_Macro', 'Fusion360_VAKI_Macro.py'))

X_CONTRACCION_A = 2030   # mm: paredes de contraccion sobre la malla del diseno anterior (caso A, solo para comparar)
G = 9.81          # m/s2
NU = 1.05e-6      # m2/s, agua salobre a ~25 C


def _cargar_script(ruta):
    sys.path.insert(0, AQUI)
    import fake_adsk  # noqa: F401  (instala un 'adsk' simulado: solo hace falta para importar el script)
    spec = importlib.util.spec_from_file_location('modelo_fusion', ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, m.geometria()


@dataclass
class Canal:
    """Canal desenrollado. Todas las longitudes en metros, angulos en radianes."""
    L: float                 # largo total, de la cresta al final del tobogan
    s_malla: float           # fin de la malla inclinada
    s_arco0: float           # inicio del arco
    s_arco1: float           # fin del arco
    s_cont0: float           # inicio de la contraccion sobre la malla (diseno anterior, caso A)
    s_cont1: float           # fin de la contraccion sobre la malla (diseno anterior, caso A)
    s_conteo: float          # linea de escaneo
    ancho0: float            # ancho aguas arriba (cajon)
    ancho1: float            # ancho del canal de conteo
    t_malla: float
    t_final: float
    radio: float
    Q: float                 # caudal de diseno, m3/s
    n_manning: float
    z_cresta: float          # cota de la cresta sobre el fondo del cajon (m)
    nivel: float             # nivel de agua en el cajon sobre su fondo (m)
    l_estrech: float = 0.25  # estrechamiento del cajon antes de la cresta (modelo actual, caso B): parte curva (m)
    l_recto: float = 0.15    # ... y tramo recto justo antes de la cresta (m)
    coef_vert: float = 1.705  # Q = coef b H^1.5 sobre la cresta (flujo critico)
    factor_nivel: float = 1.022  # calibrado para que pase el caudal nominal

    # ---- perfil geometrico en funcion de s ----
    def theta(self, s):
        """Angulo del fondo con la horizontal (positivo = bajando)."""
        s = np.asarray(s, float)
        t = np.where(s <= self.s_arco0, self.t_malla,
                     np.where(s >= self.s_arco1, self.t_final,
                              self.t_malla + (s - self.s_arco0) / self.radio))
        return t

    def curvatura(self, s):
        """1/R en el arco (convexo: el centro de curvatura queda bajo el fondo), 0 fuera de el."""
        s = np.asarray(s, float)
        return np.where((s > self.s_arco0) & (s < self.s_arco1), 1.0 / self.radio, 0.0)

    def ancho(self, s, forma=None):
        """Ancho libre b(s). 'forma' permite probar otras contracciones: funcion s -> b."""
        s = np.asarray(s, float)
        if forma is not None:
            return forma(s)
        u = np.clip((s - self.s_cont0) / (self.s_cont1 - self.s_cont0), 0.0, 1.0)
        return self.ancho0 + (self.ancho1 - self.ancho0) * u

    def cota(self, s, paso=2e-4):
        """Cota z del fondo (m) respecto a la cresta, integrando sen(theta)."""
        s = np.asarray(s, float)
        grid = np.arange(0.0, self.L + paso, paso)
        z = -np.concatenate([[0.0], np.cumsum(np.sin(self.theta(0.5 * (grid[1:] + grid[:-1]))) * np.diff(grid))])
        return np.interp(s, grid, z)


def cargar_canal(Q_ls=None, n=None, ruta=SCRIPT_FUSION):
    m, g = _cargar_script(ruta)
    mm = 1e-3
    t_m = math.atan(m.ALTO_VERTEDERO / float(m.X_VERTEDERO - g['X0']))
    L_malla = math.hypot(m.X_VERTEDERO - g['X0'], m.ALTO_VERTEDERO) * mm
    t1, t2 = g['t1'], g['t2']
    L_ini = (g['X0'] - g['X1']) / math.cos(t1) * mm
    R = m.RADIO_CURVA * mm
    L_arco = R * (t2 - t1)
    L_fin = (g['X2'] - g['XE']) / math.cos(t2) * mm
    s_a0 = L_malla + L_ini
    s_a1 = s_a0 + L_arco
    L = s_a1 + L_fin
    cont0 = (m.X_VERTEDERO - X_CONTRACCION_A) / math.cos(t_m) * mm
    cont1 = L_malla
    ancho0 = (m.ANCHO_CUERPO - 2 * m.T) * mm
    ancho1 = m.ANCHO_CANAL * mm
    return Canal(L=L, s_malla=L_malla, s_arco0=s_a0, s_arco1=s_a1, s_cont0=cont0, s_cont1=cont1,
                 s_conteo=L - m.S_ESCANEO * mm, ancho0=ancho0, ancho1=ancho1,
                 t_malla=t_m, t_final=t2, radio=R,
                 Q=(Q_ls if Q_ls is not None else m.CAUDAL_DISENO) / 1000.0,
                 n_manning=(n if n is not None else m.MANNING_N),
                 z_cresta=m.ALTO_VERTEDERO * mm, nivel=g['NIVEL'] * mm,
                 l_estrech=m.L_ESTRECH * mm, l_recto=m.L_ESTRECH_RECTO * mm,
                 coef_vert=m.COEF_VERTEDERO, factor_nivel=m.FACTOR_NIVEL), m, g


if __name__ == '__main__':
    c, m, g = cargar_canal()
    print('Canal desenrollado (desde la cresta del vertedero):')
    print('  largo total            %.3f m' % c.L)
    print('  malla inclinada        0 .. %.3f m  (%.1f grados)' % (c.s_malla, math.degrees(c.t_malla)))
    print('  arco                   %.3f .. %.3f m  (R = %.3f m, de %.1f a %.1f grados)' %
          (c.s_arco0, c.s_arco1, c.radio, math.degrees(c.t_malla), math.degrees(c.t_final)))
    print('  estrechamiento (modelo actual, caso B): %.0f mm de coseno + %.0f mm rectos antes de la cresta (de %.0f a %.0f mm)' %
          (c.l_estrech * 1e3, c.l_recto * 1e3, c.ancho0 * 1e3, c.ancho1 * 1e3))
    print('  contraccion sobre la malla (diseno anterior, caso A): %.3f .. %.3f m' % (c.s_cont0, c.s_cont1))
    print('  linea de conteo        s = %.3f m  (a %.0f mm del final)' % (c.s_conteo, m.S_ESCANEO))
    ang = math.degrees(math.atan((c.ancho0 - c.ancho1) / 2 / (c.s_cont1 - c.s_cont0)))
    print('  angulo de cada pared del caso A: %.1f grados respecto al flujo' % ang)
    print('  caudal %.1f L/s, n = %.3f, nivel en el cajon %.1f mm, cresta a %.0f mm' %
          (c.Q * 1e3, c.n_manning, c.nivel * 1e3, c.z_cresta * 1e3))
