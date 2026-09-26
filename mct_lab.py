# -*- coding: utf-8 -*-
# mct_lab.py
# Modo laboratório da classificação MCT: das leituras do ensaio Mini-MCV e da perda de massa por
# imersão (DNIT 258/2023-ME) aos coeficientes c', d', Pi' e e' e ao grupo (DNIT 259/2023-CLA).
#
# Etapas (seções da DNIT 258/2023-ME):
#   3.7  afundamento: Parsons an = An − A4n ; Simplificada an = An − Af
#   3.9  Mini-MCV = 10·log10(Bn), Bn = nº de golpes para an = 2 mm (interpolação em 10·log n)
#   3.10 c' = |Δan / Δ(Mini-MCV)| no trecho retilíneo mais inclinado da curva com Mini-MCV = 10
#        (interpolada entre as curvas vizinhas, Nota 3)
#   3.12 d' = inclinação do trecho retilíneo mais inclinado do ramo seco da curva de compactação
#        de referência (10 golpes na Simplificada, 12 na de Parsons)
#   3.13 Pi = 100 · (Md · Lcp) / (Ms · Lex) · Fc
# e da DNIT 259/2023-CLA: 3.8 Pi' pela altura final no Mini-MCV 10; 3.9 e'; 5.1 c) desempate L|N.
#
# "Trecho retilíneo mais inclinado" envolve julgamento. Aqui ele é escolhido automaticamente como a
# janela de 3 pontos consecutivos com maior inclinação (regressão linear; 2 pontos se só houver 2),
# e o app permite ao usuário substituir o valor adotado.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

import numpy as np

from formato import fmt

AREA_CM2 = 19.635                 # cilindro de 50 mm (π·2,5²)
SERIES = {
    "Parsons": [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256],
    "Simplificada": [1, 3, 6, 10, 20, 30, 40, 60, 80, 100, 120, 140, 160, 180, 200, 250],
}
GOLPES_REF = {"Parsons": 12, "Simplificada": 10}
CURVAS_COMPACTACAO = {"Parsons": [8, 10, 12, 16, 24], "Simplificada": [3, 6, 10, 20, 30]}


@dataclass
class CorpoDeProva:
    nome: str
    hc: float                               # umidade de compactação (%)
    alturas: Dict[int, float]               # nº de golpes acumulado → altura do CP (mm)
    massa_umida: float = 200.0              # g
    md: Optional[float] = None              # massa seca desprendida na imersão (g)
    lex: float = 10.0                       # comprimento saliente extrudado (mm)
    fc: float = 1.0                         # fator de correção do desprendimento
    pi_direto: Optional[float] = None       # Pi (%) já calculado (dispensa md)

    @property
    def ms(self) -> float:
        return self.massa_umida / (1.0 + self.hc / 100.0)

    @property
    def golpes(self) -> List[int]:
        return sorted(self.alturas)

    @property
    def af(self) -> float:
        """Altura final: após o último golpe aplicado."""
        return self.alturas[self.golpes[-1]]

    def meas(self, n: int) -> Optional[float]:
        """Massa específica aparente seca (kg/m³) após n golpes."""
        a = self.alturas.get(n)
        return None if a is None else self.ms / (AREA_CM2 * a / 10.0) * 1000.0

    @property
    def pi(self) -> Optional[float]:
        if self.pi_direto is not None:
            return self.pi_direto
        if self.md is None:
            return None
        return 100.0 * (self.md * self.af) / (self.ms * self.lex) * self.fc


def afundamentos(cp: CorpoDeProva, serie: str) -> List[Tuple[int, float]]:
    """Curva de deformabilidade: lista (n, an)."""
    gs = cp.golpes
    if serie == "Parsons":
        return [(n, cp.alturas[n] - cp.alturas[4 * n]) for n in gs if 4 * n in cp.alturas]
    return [(n, cp.alturas[n] - cp.af) for n in gs[:-1]]


def mini_mcv(curva: List[Tuple[int, float]], limite: float = 2.0) -> Optional[float]:
    """10·log10(Bn), interpolando linearmente em 10·log n onde an cruza 2 mm (primeiro cruzamento)."""
    for (n0, a0), (n1, a1) in zip(curva, curva[1:]):
        if a0 >= limite >= a1 and a0 != a1:
            x0, x1 = 10 * math.log10(n0), 10 * math.log10(n1)
            return x0 + (a0 - limite) / (a0 - a1) * (x1 - x0)
    return None


def trecho_mais_inclinado(pontos: List[Tuple[float, float]], crescente: bool = False):
    """Janela de 3 pontos consecutivos (ou 2) com maior inclinação. Retorna (inclinação, pontos da janela).
    crescente=False procura a maior queda (curvas de deformabilidade); True, a maior subida (ramo seco)."""
    if len(pontos) < 2:
        return None, []
    tam = 3 if len(pontos) >= 3 else 2
    melhor = (None, [])
    for i in range(len(pontos) - tam + 1):
        jan = pontos[i:i + tam]
        xs, ys = np.array([p[0] for p in jan]), np.array([p[1] for p in jan])
        incl = float(np.polyfit(xs, ys, 1)[0])
        valor = incl if crescente else -incl
        if melhor[0] is None or valor > melhor[0]:
            melhor = (valor, jan)
    return melhor


def _interp(x0, y0, x1, y1, x):
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def interpolar_em_mcv(pares: List[Tuple[float, float]], alvo: float) -> Optional[float]:
    """Valor de uma grandeza (altura final, Pi) no Mini-MCV alvo, por interpolação linear entre os CPs."""
    pts = sorted(pares)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= alvo <= x1 and x1 != x0:
            return _interp(x0, y0, x1, y1, alvo)
    return None


def linha_da_janela(jan):
    """Extremos da reta ajustada ao trecho retilíneo: ((x_ini, y_ini), (x_fim, y_fim))."""
    xs, ys = [p[0] for p in jan], [p[1] for p in jan]
    b, a = np.polyfit(xs, ys, 1)
    return (xs[0], a + b * xs[0]), (xs[-1], a + b * xs[-1])


def curva_mcv10(curvas, viz1, viz2, espacamento_min: float = 0.3):
    """Curva de deformabilidade com Mini-MCV = 10, interpolada entre as curvas vizinhas (Nota 3, seção 3.10).
    Cada vizinha é deslocada no eixo 10·log n para cruzar 2 mm em 10; a curva interpolada é a média ponderada
    pela proximidade do Mini-MCV de cada uma a 10. Por construção, passa por (10; 2 mm).
    Retorna (lista de pontos (x, a_n), peso da vizinha de Mini-MCV maior)."""
    (n1, m1), (n2, m2) = viz1, viz2
    w2 = 1.0 if abs(m2 - m1) < 1e-9 else (10.0 - m1) / (m2 - m1)

    def desloc(nome, m):
        return [(10 * math.log10(n) + (10.0 - m), a) for n, a in curvas[nome]]

    p1, p2 = desloc(n1, m1), desloc(n2, m2)
    lo, hi = max(p1[0][0], p2[0][0]), min(p1[-1][0], p2[-1][0])
    xs = []
    for x in sorted({x for x, _ in p1 + p2 if lo <= x <= hi}):
        if not xs or x - xs[-1] >= espacamento_min:     # funde nós quase coincidentes das duas curvas
            xs.append(x)
    if lo <= 10.0 <= hi and 10.0 not in xs:              # inclui o ponto (10; 2 mm), sem remover nós reais
        xs = sorted(xs + [10.0])

    def val(p, x):
        return float(np.interp(x, [q[0] for q in p], [q[1] for q in p]))

    return [(x, (1 - w2) * val(p1, x) + w2 * val(p2, x)) for x in xs], w2


@dataclass
class ResultadoLab:
    serie: str
    cps: List[CorpoDeProva]
    curvas: Dict[str, List[Tuple[int, float]]]
    mcv: Dict[str, Optional[float]]
    c_: Optional[float] = None
    c_detalhe: dict = field(default_factory=dict)
    d_: Optional[float] = None
    d_detalhe: dict = field(default_factory=dict)
    af10: Optional[float] = None
    densidade: Optional[str] = None
    pi_ref: Optional[float] = None
    mcv_pi: Optional[int] = None
    crit_pi_negativa: Optional[bool] = None
    crit_concavidade: Optional[bool] = None
    passos: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)

    @property
    def completo(self) -> bool:
        return None not in (self.c_, self.d_, self.pi_ref)


def calcular(cps: List[CorpoDeProva], serie: str) -> ResultadoLab:
    if serie not in SERIES:
        raise ValueError("Série deve ser 'Parsons' ou 'Simplificada'.")
    cps = [cp for cp in cps if len(cp.alturas) >= 2]
    if len(cps) < 2:
        raise ValueError("Informe ao menos dois corpos de prova com leituras de altura.")
    curvas = {cp.nome: afundamentos(cp, serie) for cp in cps}
    mcv = {cp.nome: mini_mcv(curvas[cp.nome]) for cp in cps}
    R = ResultadoLab(serie=serie, cps=cps, curvas=curvas, mcv=mcv)
    for cp in cps:
        if mcv[cp.nome] is None:
            R.avisos.append(f"{cp.nome}: a curva de deformabilidade não cruza 2 mm; Mini-MCV não determinado.")
    R.passos.append("Mini-MCV = 10·log(Bn), com Bn para afundamento de 2 mm: " + "; ".join(
        f"{cp.nome} (hc {fmt(cp.hc)}%) = {fmt(mcv[cp.nome], 2)}" for cp in cps if mcv[cp.nome] is not None))

    # --- c': curva de deformabilidade com Mini-MCV = 10 (real ou interpolada, Nota 3 da seção 3.10) --------
    validos = sorted(((m, cp.nome) for cp in cps if (m := mcv[cp.nome]) is not None))
    abaixo = [v for v in validos if v[0] <= 10.0]
    acima = [v for v in validos if v[0] >= 10.0]
    if abaixo and acima:
        (m1, n1), (m2, n2) = abaixo[-1], acima[0]
        curva10, w2 = curva_mcv10(curvas, (n1, m1), (n2, m2))
        s, jan = trecho_mais_inclinado(curva10)
        R.c_ = s
        R.c_detalhe = {"cps": (n1, n2), "mcv": (m1, m2), "peso_superior": w2, "curva": curva10, "janela": jan,
                       "linha": linha_da_janela(jan)}
        (xa, ya), (xb, yb) = R.c_detalhe["linha"]
        R.passos.append(
            f"c': curva com Mini-MCV = 10 interpolada entre {n1} (Mini-MCV {fmt(m1, 2)}) e {n2} (Mini-MCV "
            f"{fmt(m2, 2)}); trecho retilíneo mais inclinado de 10·log n = {fmt(xa, 2)} a {fmt(xb, 2)}: "
            f"c' = {fmt(ya - yb, 2)}/{fmt(xb - xa, 2)} = {fmt(R.c_, 2)}")
    else:
        R.avisos.append("Os Mini-MCV dos corpos de prova não envolvem o valor 10; c' não determinado "
                        "(a norma pede curvas dos dois lados de Mini-MCV = 10).")

    # --- d': ramo seco da curva de compactação de referência ---------------------------------------
    nref = GOLPES_REF[serie]
    comp = sorted((cp.hc, cp.meas(nref)) for cp in cps if cp.meas(nref) is not None)
    if len(comp) >= 2:
        i_max = max(range(len(comp)), key=lambda i: comp[i][1])
        seco = comp[:i_max + 1]
        if len(seco) >= 2:
            s, jan = trecho_mais_inclinado(seco, crescente=True)
            R.d_ = s
            R.d_detalhe = {"golpes": nref, "pontos": comp, "ramo_seco": seco, "janela": jan,
                           "linha": linha_da_janela(jan)}
            R.passos.append(f"d': ramo seco da curva de {nref} golpes, trecho mais inclinado entre hc "
                            f"{fmt(jan[0][0])}% e {fmt(jan[-1][0])}% → d' = {fmt(R.d_, 1)} kg/m³/%")
        else:
            R.avisos.append(f"A curva de {nref} golpes não tem ramo seco (máximo no CP mais seco); d' não determinado.")
    else:
        R.avisos.append(f"Faltam alturas a {nref} golpes para traçar a curva de compactação de referência.")

    # --- Pi': altura final e perda por imersão × Mini-MCV --------------------------------------------
    af_pts = [(mcv[cp.nome], cp.af) for cp in cps if mcv[cp.nome] is not None]
    R.af10 = interpolar_em_mcv(af_pts, 10.0)
    pi_pts = [(mcv[cp.nome], cp.pi) for cp in cps if mcv[cp.nome] is not None and cp.pi is not None]
    if R.af10 is None:
        R.avisos.append("Não foi possível interpolar a altura final no Mini-MCV = 10.")
    else:
        R.densidade = "baixa" if R.af10 >= 48.0 else "alta"
        R.mcv_pi = 10 if R.densidade == "baixa" else 15
        R.pi_ref = interpolar_em_mcv(pi_pts, float(R.mcv_pi))
        R.passos.append(f"Altura final no Mini-MCV 10 = {fmt(R.af10, 2)} mm "
                        f"({'≥' if R.densidade == 'baixa' else '<'} 48 mm) → {R.densidade} densidade → "
                        f"Pi' = Pi no Mini-MCV {R.mcv_pi}"
                        + (f" = {fmt(R.pi_ref, 1)}%" if R.pi_ref is not None else ""))
        if R.pi_ref is None:
            R.avisos.append(f"Não foi possível interpolar Pi no Mini-MCV = {R.mcv_pi}: faltam valores de Pi "
                            "nos dois lados desse Mini-MCV.")

    # --- critérios do item 5.1 c) da DNIT 259/2023-CLA ------------------------------------------------
    p10, p15 = interpolar_em_mcv(pi_pts, 10.0), interpolar_em_mcv(pi_pts, 15.0)
    if p10 is not None and p15 is not None:
        R.crit_pi_negativa = p15 < p10
    mh = [(cp.hc, mcv[cp.nome]) for cp in cps if mcv[cp.nome] is not None]
    if len(mh) >= 3:
        a = float(np.polyfit([h for h, _ in mh], [m for _, m in mh], 2)[0])
        R.crit_concavidade = a > 0
    return R


def tabela_cps(R: ResultadoLab):
    """Resumo por corpo de prova (para exibição)."""
    import pandas as pd
    nref = GOLPES_REF[R.serie]
    return pd.DataFrame([{"CP": cp.nome, "hc (%)": cp.hc, "Ms (g)": round(cp.ms, 1),
                          "Mini-MCV": None if R.mcv[cp.nome] is None else round(R.mcv[cp.nome], 2),
                          "Altura final (mm)": cp.af,
                          f"MEAS {nref} golpes (kg/m³)": None if cp.meas(nref) is None else round(cp.meas(nref)),
                          "Pi (%)": None if cp.pi is None else round(cp.pi, 1)} for cp in R.cps])


# ---------------------------------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------------------------------
def _fig(titulo, xl, yl):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.set_title(titulo, fontsize=10); ax.set_xlabel(xl); ax.set_ylabel(yl)
    ax.grid(True, ls=":", alpha=0.5)
    return fig, ax


def _triangulo(ax, p_ini, p_fim, rot_vertical, rot_horizontal, descendente=True):
    """Triângulo de inclinação (amarelo) sobre a reta do trecho retilíneo, com os catetos rotulados."""
    (xa, ya), (xb, yb) = p_ini, p_fim
    amarelo = "#E8B900"
    if descendente:                       # c′: cateto vertical em xa, horizontal em yb
        ax.plot([xa, xa, xb], [ya, yb, yb], color=amarelo, lw=2.2, zorder=6)
        ax.annotate(rot_vertical, (xa, (ya + yb) / 2), xytext=(-6, 0), textcoords="offset points", ha="right",
                    va="center", fontsize=8.5, color="#7a5d00", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
        ax.annotate(rot_horizontal, ((xa + xb) / 2, yb), xytext=(0, -9), textcoords="offset points", ha="center",
                    va="top", fontsize=8.5, color="#7a5d00", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
    else:                                 # d′: cateto horizontal em ya, vertical em xb
        ax.plot([xa, xb, xb], [ya, ya, yb], color=amarelo, lw=2.2, zorder=6)
        ax.annotate(rot_horizontal, ((xa + xb) / 2, ya), xytext=(0, -9), textcoords="offset points", ha="center",
                    va="top", fontsize=8.5, color="#7a5d00", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
        ax.annotate(rot_vertical, (xb, (ya + yb) / 2), xytext=(6, 0), textcoords="offset points", ha="left",
                    va="center", fontsize=8.5, color="#7a5d00", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))


def plot_deformabilidade(R: ResultadoLab, destacar: bool = True):
    fig, ax = _fig("Curvas de deformabilidade (Figura A10)", "Mini-MCV = 10·log₁₀(nº de golpes)",
                   "Afundamento aₙ (mm)")
    for cp in R.cps:
        pts = R.curvas[cp.nome]
        ax.plot([10 * math.log10(n) for n, _ in pts], [a for _, a in pts], marker="o", ms=3.5, lw=1.2,
                label=f"{cp.nome} (hc {fmt(cp.hc)}%)")
    ax.axhline(2.0, color="gray", ls=":", lw=1); ax.axvline(10.0, color="gray", ls=":", lw=1)
    det = R.c_detalhe
    if destacar and det.get("curva"):
        cx, cy = zip(*det["curva"])
        ax.plot(cx, cy, color="black", ls="--", lw=1.8, zorder=5, label="Interpolada (Mini-MCV = 10)")
        ax.scatter([10], [2], color="black", s=22, zorder=7)
        (xa, ya), (xb, yb) = det["linha"]
        ax.plot([xa, xb], [ya, yb], color="black", lw=4.0, alpha=0.8, zorder=6,
                label=f"Trecho retilíneo: c′ = {fmt(ya - yb, 2)}/{fmt(xb - xa, 2)} = {fmt(R.c_, 2)}")
        _triangulo(ax, (xa, ya), (xb, yb), f"Δaₙ = {fmt(ya - yb, 2)}", f"ΔMini-MCV = {fmt(xb - xa, 2)}")
        ax.annotate(f"({fmt(xa, 2)}; {fmt(ya, 2)})\nn = {fmt(10 ** (xa / 10), 2)} golpes", (xa, ya), xytext=(-10, 10),
                    textcoords="offset points", ha="right", fontsize=8, color="#333",
                    arrowprops=dict(arrowstyle="-", color="#999", lw=0.8),
                    bbox=dict(fc="white", ec="#ccc", lw=0.6, pad=2))
    ax.legend(fontsize=7.3, loc="upper right", framealpha=0.95)
    fig.tight_layout()
    return fig


def plot_compactacao(R: ResultadoLab, destacar: bool = True):
    fig, ax = _fig("Curvas de compactação Mini-MCV (Figura A11)", "Umidade de compactação hc (%)", "MEAS (kg/m³)")
    nref = GOLPES_REF[R.serie]
    for n in CURVAS_COMPACTACAO[R.serie]:
        pts = sorted((cp.hc, cp.meas(n)) for cp in R.cps if cp.meas(n) is not None)
        if len(pts) >= 2:
            ax.plot(*zip(*pts), marker="o", ms=3.5, lw=2.2 if n == nref else 1.0,
                    color="tab:red" if n == nref else None, label=f"{n} golpes" + (" (referência)" if n == nref else ""))
    det = R.d_detalhe
    if destacar and det.get("linha"):
        (xa, ya), (xb, yb) = det["linha"]
        ax.plot([xa, xb], [ya, yb], color="black", lw=4.0, alpha=0.8, zorder=6,
                label=f"Trecho retilíneo: d′ = {fmt(yb - ya, 0)}/{fmt(xb - xa, 1)} = {fmt(R.d_, 1)}")
        _triangulo(ax, (xa, ya), (xb, yb), f"ΔMEAS = {fmt(yb - ya, 0)} kg/m³", f"Δhc = {fmt(xb - xa, 1)}%",
                   descendente=False)
    ax.legend(fontsize=7.3, loc="lower right", framealpha=0.95)
    fig.tight_layout()
    return fig


def _chamada(ax, x, y, texto_y, texto_ponto, cor="tab:red"):
    """Linhas de chamada do ponto (x, y) até os eixos, com o valor lido no eixo vertical."""
    x0, y0 = ax.get_xlim()[0], ax.get_ylim()[0]
    ax.plot([x, x], [y0, y], color=cor, ls="--", lw=1.0, zorder=4)
    ax.plot([x0, x], [y, y], color=cor, ls="--", lw=1.0, zorder=4)
    ax.scatter([x], [y], color=cor, s=40, zorder=6)
    ax.annotate(texto_y, (x0, y), xytext=(4, 3), textcoords="offset points", fontsize=8.5, color=cor)
    ax.annotate(texto_ponto, (x, y), xytext=(8, 8), textcoords="offset points", fontsize=9, color=cor,
                bbox=dict(fc="white", ec=cor, lw=0.6, alpha=0.95, pad=2))


def plot_af(R: ResultadoLab):
    fig, ax = _fig("Altura final × Mini-MCV (DNIT 259/2023-CLA, seção 3.8)", "Mini-MCV", "Altura final do CP (mm)")
    pts = sorted((R.mcv[cp.nome], cp.af) for cp in R.cps if R.mcv[cp.nome] is not None)
    if pts:
        ax.plot(*zip(*pts), marker="o", color="tab:blue", label="CPs")
        for (m, a), cp in zip(pts, sorted((c for c in R.cps if R.mcv[c.nome] is not None), key=lambda c: R.mcv[c.nome])):
            ax.annotate(cp.nome, (m, a), xytext=(0, -12), textcoords="offset points", ha="center", fontsize=7.5,
                        color="tab:blue")
    ax.axhline(48, color="tab:orange", ls="-", lw=1.2)
    ax.text(0.99, 48, "48 mm: limite entre alta e baixa densidade", transform=ax.get_yaxis_transform(), ha="right",
            va="bottom", color="tab:orange", fontsize=8)
    lo, hi = ax.get_ylim()
    ax.set_ylim(min(lo, 47.5), hi)
    if R.af10 is not None:
        _chamada(ax, 10, R.af10, f"Af(10) = {fmt(R.af10, 2)} mm", f"{fmt(R.af10, 2)} mm → {R.densidade} densidade")
    fig.tight_layout()
    return fig


def plot_pi(R: ResultadoLab):
    fig, ax = _fig("Perda de massa por imersão × Mini-MCV", "Mini-MCV", "Pi (%)")
    pts = sorted((R.mcv[cp.nome], cp.pi, cp.nome) for cp in R.cps if R.mcv[cp.nome] is not None and cp.pi is not None)
    if pts:
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", color="tab:green")
        for m, v, nome in pts:
            ax.annotate(nome, (m, v), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7.5,
                        color="tab:green")
    for mm in (10, 15):
        ax.axvline(mm, color="gray", ls=":", lw=1)
    lo, hi = ax.get_ylim()
    ax.set_ylim(min(lo, 0), hi)
    if R.pi_ref is not None:
        _chamada(ax, R.mcv_pi, R.pi_ref, f"Pi′ = {fmt(R.pi_ref, 1)}%",
                 f"Pi′ = {fmt(R.pi_ref, 1)}% (Mini-MCV {R.mcv_pi}; {R.densidade} densidade)")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------------------------------
# Exemplos embutidos (dados publicados)
# ---------------------------------------------------------------------------------------------------
def exemplo_dnit_258() -> Tuple[str, List[CorpoDeProva], str]:
    """DNIT 258/2023-ME, Figura A8 (adaptado de Villibor e Alves, 2019): série Simplificada.
    Referência da norma: c' = 1,20 (Figura A10) e d' = 75 kg/m³/% (Figura A11)."""
    s = [3, 6, 10, 20, 30, 40, 60, 80, 100, 120, 140, 160, 180]
    dados = [  # hc, massa úmida, Md, alturas
        ("CP1", 19.9, [56.31, 52.48, 50.78, 50.56, 50.38, 50.32], 47.58),
        ("CP2", 17.9, [57.58, 53.93, 51.27, 49.01, 48.86, 48.61, 48.54], 30.50),
        ("CP3", 15.8, [58.33, 54.73, 51.96, 49.32, 48.42, 47.64, 47.28, 47.26, 47.23], 14.81),
        ("CP4", 13.7, [63.67, 60.16, 57.68, 54.13, 52.63, 51.73, 50.93, 50.66, 50.58, 50.51, 50.46], 31.75),
        ("CP5", 11.6, [69.93, 66.58, 64.08, 60.93, 58.89, 57.66, 56.16, 55.26, 54.46, 54.19, 54.11, 54.04, 53.99],
         37.35),
    ]
    cps = [CorpoDeProva(nome, hc, dict(zip(s, alt)), 200.0, md=md) for nome, hc, alt, md in dados]
    return "Simplificada", cps, "DNIT 258/2023-ME, Figura A8 (adaptado de Villibor e Alves, 2019)"


def exemplo_barbosa_2021() -> Tuple[str, List[CorpoDeProva], str]:
    """BARBOSA, D. P. (2021). Estudo da metodologia MCT, com apresentação de exemplo de classificação de
    um solo. TCC — UFJF. Série de Parsons; Pi por CP conforme o trabalho. Resultado de referência: LG'."""
    p = SERIES["Parsons"]
    dados = [
        ("CP6", 23.1, [79.59, 75.24, 72.71, 70.78, 67.8, 65.74, 62.87, 60.53, 57.93, 55.92, 53.23, 51.39, 50,
                       49.9, 50.13, 49.7], 0.0),
        ("CP8", 25.2, [80.84, 75.59, 71.89, 69.39, 65.29, 62.41, 58.58, 55.94, 52.67, 50.99, 50.44, 50.49,
                       50.59, 50.38], 0.0),
        ("CP19", 27.1, [79.30, 72.25, 67.95, 64.87, 60.29, 57.62, 54.04, 52.14, 51.58, 51.71, 51.79, 51.72], 0.0),
        ("CP20", 29.0, [76.09, 68.66, 64.19, 60.95, 56.52, 54.04, 52.92, 52.86, 52.96, 52.98], 68.55),
        ("CP22", 31.0, [73.24, 64.64, 60.27, 57.17, 54.24, 54.01, 53.97, 53.97, 53.89], 117.54),
    ]
    cps = [CorpoDeProva(nome, hc, dict(zip(p, alt)), 200.0, pi_direto=pi) for nome, hc, alt, pi in dados]
    return "Parsons", cps, "Barbosa (2021), TCC UFJF — série de Parsons"


EXEMPLOS_LAB = {"DNIT 258/2023 — Figura A8 (série Simplificada)": exemplo_dnit_258,
                "Barbosa (2021), TCC UFJF (série de Parsons)": exemplo_barbosa_2021}


# ---------------------------------------------------------------------------------------------------
# Conversão para/de tabelas (planilha-modelo e editor do app)
# ---------------------------------------------------------------------------------------------------
def para_tabelas(serie: str, cps: List[CorpoDeProva]):
    """(alturas, dados_cp): alturas com uma linha por nº de golpes e uma coluna por CP."""
    import pandas as pd
    golpes = sorted({n for cp in cps for n in cp.alturas} | set(SERIES[serie][:1]))
    alturas = pd.DataFrame({"golpes": golpes, **{cp.nome: [cp.alturas.get(n) for n in golpes] for cp in cps}})
    dados = pd.DataFrame([{"CP": cp.nome, "hc (%)": cp.hc, "massa úmida (g)": cp.massa_umida,
                           "Md desprendida (g)": cp.md, "Lex (mm)": cp.lex, "Fc": cp.fc,
                           "Pi direto (%)": cp.pi_direto} for cp in cps])
    return numerico(alturas), numerico(dados)


def numerico(df):
    """Colunas numéricas como float (células vazias aparecem em branco no editor, não como 'None')."""
    import pandas as pd
    df = df.copy()
    for c in df.columns:
        if c != "CP":
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    if "golpes" in df.columns:
        df["golpes"] = df["golpes"].astype("Int64")
    return df


def de_tabelas(alturas, dados) -> List[CorpoDeProva]:
    """Monta os corpos de prova a partir das duas tabelas (células vazias são ignoradas)."""
    def num(v):
        try:
            x = float(v)
        except (TypeError, ValueError):
            return None
        return None if math.isnan(x) else x

    cps = []
    for _, lin in dados.iterrows():
        nome = str(lin.get("CP") or "").strip()
        hc = num(lin.get("hc (%)"))
        if not nome or hc is None or nome not in alturas.columns:
            continue
        alt = {}
        for _, row in alturas.iterrows():
            n, a = num(row.get("golpes")), num(row.get(nome))
            if n is not None and a is not None:
                alt[int(n)] = a
        cps.append(CorpoDeProva(nome, hc, alt, num(lin.get("massa úmida (g)")) or 200.0,
                                md=num(lin.get("Md desprendida (g)")), lex=num(lin.get("Lex (mm)")) or 10.0,
                                fc=num(lin.get("Fc")) or 1.0, pi_direto=num(lin.get("Pi direto (%)"))))
    return cps
