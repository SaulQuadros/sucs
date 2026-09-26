# -*- coding: utf-8 -*-
# mct_core.py
# Classificação MCT de solos finos tropicais conforme a norma DNIT 259/2023-CLA
# (ensaios pela DNIT 258/2023-ME). Pode ser importado por scripts ou pelo app Streamlit.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math

import matplotlib.pyplot as plt

from formato import fmt

NORMA_CLA = "DNIT 259/2023-CLA"
NORMA_ME = "DNIT 258/2023-ME"

# ---------------------------------------------------------------------------
# Ábaco (Figura A1 da DNIT 259/2023-CLA) — vértices cotados na própria figura
# Eixo x: coeficiente c'; eixo y: índice e'.
# ---------------------------------------------------------------------------
C_MIN, C_MAX = 0.0, 2.5
E_MIN, E_MAX = 0.5, 2.2

# Linha inclinada NA | (NS', NA', LA): (0,27; 2,2) → (0,45; 1,75) → (0,59; 1,4) → (0,70; 1,15)
LINHA_NA = [(0.27, 2.20), (0.45, 1.75), (0.59, 1.40), (0.70, 1.15)]
# Linha inclinada NS' | NA': (0,45; 1,75) → (1,7; 1,15)
LINHA_NS_NA = [(0.45, 1.75), (1.70, 1.15)]
E_NA_LA = 1.40     # tracejada horizontal NA | LA (c' de 0 a 0,59)
E_N_L = 1.15       # tracejada horizontal N | L (c' ≥ 0,70)
C_LA_LA = 0.70     # vertical LA | LA'
C_A_G = 1.50       # vertical LA' | LG' e NS' | NG'
C_NA_NG = 1.70     # fim da linha NS'|NA' sobre e' = 1,15

GRUPOS = ("LA", "LA'", "LG'", "NA", "NA'", "NS'", "NG'")

# Anexo B (normativo) da DNIT 259/2023-CLA — propriedades típicas dos grupos
# (idêntico à Tabela 9 do Manual de Pavimentação IPR-719/2006).
PROPRIEDADES = {
    "NA":  {"classe": "Não laterítico", "nome": "Areias",
            "granulometria": "Areias, areias siltosas, siltes (q)",
            "mini_cbr_sem_imersao": "Alta a média", "perda_suporte_imersao": "Baixa a média",
            "expansao": "Baixa", "contracao": "Baixa a média",
            "permeabilidade": "Alta a média", "plasticidade": "Baixa a NP"},
    "NA'": {"classe": "Não laterítico", "nome": "Arenosos",
            "granulometria": "Areias siltosas, areias argilosas",
            "mini_cbr_sem_imersao": "Alta", "perda_suporte_imersao": "Baixa",
            "expansao": "Baixa", "contracao": "Baixa a média",
            "permeabilidade": "Baixa", "plasticidade": "Média a NP"},
    "NS'": {"classe": "Não laterítico", "nome": "Siltosos",
            "granulometria": "Siltes (k, m), siltes arenosos e argilosos",
            "mini_cbr_sem_imersao": "Alta a média", "perda_suporte_imersao": "Alta",
            "expansao": "Alta", "contracao": "Média",
            "permeabilidade": "Média a alta", "plasticidade": "Média a alta"},
    "NG'": {"classe": "Não laterítico", "nome": "Argilosos",
            "granulometria": "Argilas, argilas arenosas, argilas siltosas",
            "mini_cbr_sem_imersao": "Alta", "perda_suporte_imersao": "Alta",
            "expansao": "Alta a média", "contracao": "Alta a média",
            "permeabilidade": "Baixa a média", "plasticidade": "Alta"},
    "LA":  {"classe": "Laterítico", "nome": "Areias",
            "granulometria": "Areias com pouca argila",
            "mini_cbr_sem_imersao": "Alta", "perda_suporte_imersao": "Baixa",
            "expansao": "Baixa", "contracao": "Baixa",
            "permeabilidade": "Baixa a média", "plasticidade": "NP a baixa"},
    "LA'": {"classe": "Laterítico", "nome": "Arenosos",
            "granulometria": "Areias argilosas, argilas arenosas",
            "mini_cbr_sem_imersao": "Alta a muito alta", "perda_suporte_imersao": "Baixa",
            "expansao": "Baixa", "contracao": "Baixa a média",
            "permeabilidade": "Baixa", "plasticidade": "Baixa a média"},
    "LG'": {"classe": "Laterítico", "nome": "Argilosos",
            "granulometria": "Argilas, argilas arenosas",
            "mini_cbr_sem_imersao": "Alta", "perda_suporte_imersao": "Baixa",
            "expansao": "Baixa", "contracao": "Baixa a alta",
            "permeabilidade": "Baixa", "plasticidade": "Média a alta"},
}

ROTULOS_ANEXO_B = {"granulometria": "Granulometria típica", "mini_cbr_sem_imersao": "Mini-CBR sem imersão",
                   "perda_suporte_imersao": "Perda de suporte por imersão", "expansao": "Expansão",
                   "contracao": "Contração", "permeabilidade": "Permeabilidade", "plasticidade": "Plasticidade"}
ORDEM_ANEXO_B = ["NA", "NA'", "NS'", "NG'", "LA", "LA'", "LG'"]   # como no Anexo B da DNIT 259/2023-CLA


def tabela_anexo_b_html() -> str:
    """Anexo B em HTML: largura total, texto quebrado dentro das células e cabeçalho agrupado por classe,
    para que todos os grupos fiquem legíveis sem rolagem nem ajuste manual de colunas."""
    borda = "1px solid rgba(128,128,128,0.35)"
    cel = f"border:{borda};padding:6px 8px;vertical-align:top;overflow-wrap:break-word;hyphens:auto"
    cab = cel + ";text-align:center;background:rgba(128,128,128,0.10);font-weight:600"
    n_n = sum(g.startswith("N") for g in ORDEM_ANEXO_B)
    # hifenização em pt-BR nas colunas estreitas; rolagem horizontal só abaixo de 540 px (celular)
    html = ["<div style='overflow-x:auto'>",
            "<table lang='pt-BR' style='width:100%;min-width:540px;table-layout:fixed;border-collapse:collapse;"
            "font-size:0.9rem'>",
            "<colgroup><col style='width:16%'>" + "<col>" * len(ORDEM_ANEXO_B) + "</colgroup>",
            f"<tr><th style='{cab}'>Classes</th>"
            f"<th colspan='{n_n}' style='{cab}'>N — solos de comportamento não laterítico</th>"
            f"<th colspan='{len(ORDEM_ANEXO_B) - n_n}' style='{cab}'>L — solos de comportamento laterítico</th></tr>",
            f"<tr><th style='{cab}'>Grupos</th>" + "".join(
                f"<th style='{cab}'>{g}<br><span style='font-weight:400'>{PROPRIEDADES[g]['nome']}</span></th>"
                for g in ORDEM_ANEXO_B) + "</tr>"]
    for k, rotulo in ROTULOS_ANEXO_B.items():
        html.append(f"<tr><th style='{cel};text-align:left;font-weight:600'>{rotulo}</th>"
                    + "".join(f"<td style='{cel}'>{PROPRIEDADES[g][k]}</td>" for g in ORDEM_ANEXO_B) + "</tr>")
    html.append("</table></div>")
    return "".join(html)


# Anexo C (normativo) da DNIT 259/2023-CLA — breve descrição e correlação pedológica/geológica
DESCRICOES = {
    "LA":  ("São solos pouco coesivos e com alto módulo de resiliência, compostos por areias com poucos "
            "finos. Apresentam-se, geralmente, em formato de grumos subarredondados e colorações de "
            "tendência avermelhada em função da oxidação do elemento ferro.",
            "Neossolo quartzarênico (NQ)"),
    "LA'": ("São os melhores solos para construção de base e sub-base de pavimentos. Apresentam razoável "
            "coesão e alto módulo de resiliência. São compostos por areias argilosas e finos lateríticos.",
            "Latossolos (L) ou Argissolos (P) de textura média-arenosa"),
    "LG'": ("São solos que podem apresentar elevada contração em camadas compactadas e menores capacidades "
            "de suporte e módulo de resiliência. São compostos por argilas, argilas siltosas, argilas "
            "arenosas e siltes argilosos.",
            "Latossolos (L) ou Argissolos (P) de textura média-argilosa"),
    "NA":  ("São solos pouco expansivos e baixo coeficiente de argilosidade, sendo os melhores a serem usados "
            "aqueles próximos ao grupo LA. São compostos por quartzos e/ou micas nas frações areias, siltes "
            "e suas misturas.",
            "Provenientes da alteração de arenitos e quartzitos"),
    "NA'": ("São solos que podem apresentar coeficiente de argilosidade médio. Os que contêm alta porcentagem "
            "de finos (fração argila) apresentam elevada expansão, sendo os piores. Os melhores são aqueles "
            "próximos aos grupos LA e LA' com módulo de resiliência satisfatório. São compostos por areias "
            "quartzosas com finos e mica na fração areia.",
            "Saprólitos de rochas ricas em quartzo como arenitos, granitos e gnaisses"),
    "NS'": ("São solos muito resilientes e não recomendados como camada final de terraplenagem e outras do "
            "pavimento. Não são bons para constituir misturas de solo-agregado. São solos que compreendem "
            "siltes e siltes arenosos, e coeficiente de argilosidade baixo a médio.",
            "Solos provenientes de alteração de rochas como basalto, diabásio e metabasito"),
    "NG'": ("São solos que apresentam alto coeficiente de argilosidade, elevada expansão, plasticidade, "
            "compressão e contração. Compostos por argilas, argila siltosa, argila arenosa, e silte argiloso.",
            "Saprólitos de rochas como basalto, diabásio, metabasito, gnaisses"),
}

# Tabela 15 do Manual de Pavimentação IPR-719/2006 — interrelação MCT × classificação resiliente
RESILIENTE = {
    "NA":  ("III", "grau de resiliência alto"),
    "LA":  ("III", "grau de resiliência alto"),
    "NA'": ("II - III", "grau de resiliência médio e alto"),
    "NS'": ("II - III", "grau de resiliência médio a alto"),
    "NG'": ("II - I", "grau de resiliência médio a baixo"),
    "LA'": ("II - I", "grau de resiliência médio a baixo"),
    "LG'": ("I - II", "grau de resiliência baixo"),
}


@dataclass
class MCTInput:
    c_: float                          # coeficiente de argilosidade c'
    d_: Optional[float] = None         # coeficiente d' (ramo seco, 10 ou 12 golpes)
    pi_ref: Optional[float] = None     # Pi' já determinado (%)
    pi_10: Optional[float] = None      # Pi (%) no Mini-MCV = 10
    pi_15: Optional[float] = None      # Pi (%) no Mini-MCV = 15
    af_10: Optional[float] = None      # altura final (mm) do CP no Mini-MCV = 10
    e_: Optional[float] = None         # e' já calculado (dispensa d' e Pi')
    serie: str = "simplificada"        # "simplificada" (d' a 10 golpes) ou "Parsons" (12 golpes)
    # Critérios de desempate próximo da linha L|N (item 5.1 c): None = não informado
    pi_inclinacao_negativa: Optional[bool] = None
    mcv_concavidade_para_cima: Optional[bool] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCTResult:
    group: str
    c_: float
    e_: float
    pi_ref: Optional[float]
    densidade: Optional[str]
    rationale: List[str]
    warnings: List[str]

    @property
    def classe(self) -> str:
        return "Laterítico" if self.group.startswith("L") else "Não laterítico"

    @property
    def props(self) -> Dict[str, str]:
        return PROPRIEDADES[self.group]

    @property
    def descricao(self) -> str:
        return DESCRICOES[self.group][0]

    @property
    def correlacao(self) -> str:
        return DESCRICOES[self.group][1]

    @property
    def resiliente(self) -> Tuple[str, str]:
        return RESILIENTE[self.group]


def _num(x) -> Optional[float]:
    """Converte para float; None/NaN/'' viram None."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def _interp(pts: List[Tuple[float, float]], x: float, *, by: str = "c") -> float:
    """Interpolação linear por trechos numa polilinha (extrapola nas pontas).
    by='c' devolve e'(c'); by='e' devolve c'(e')."""
    pts = sorted((e, c) for c, e in pts) if by == "e" else sorted(pts)
    segs = list(zip(pts, pts[1:]))
    (x0, y0), (x1, y1) = next((s for s in segs if x <= s[1][0]), segs[-1])
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def pi_referencia(pi_10: Optional[float], pi_15: Optional[float], af_10: Optional[float]) -> Tuple[float, str, str]:
    """Pi' conforme item 3.8 da DNIT 259/2023-CLA.
    AF (Mini-MCV = 10) ≥ 48 mm → baixa densidade → Pi' = Pi no Mini-MCV 10;
    AF < 48 mm → alta densidade → Pi' = Pi no Mini-MCV 15.
    Retorna (Pi', densidade, justificativa)."""
    af = _num(af_10)
    if af is None:
        raise ValueError("Informe a altura final AF do corpo de prova no Mini-MCV = 10 para escolher Pi'.")
    if af >= 48.0:
        v = _num(pi_10)
        if v is None:
            raise ValueError("AF ≥ 48 mm (baixa densidade): informe Pi no Mini-MCV = 10.")
        return v, "baixa", f"AF = {fmt(af, 1)} mm ≥ 48,0 mm → baixa densidade → Pi' = Pi(Mini-MCV 10) = {fmt(v, 1)}%"
    v = _num(pi_15)
    if v is None:
        raise ValueError("AF < 48 mm (alta densidade): informe Pi no Mini-MCV = 15.")
    return v, "alta", f"AF = {fmt(af, 1)} mm < 48,0 mm → alta densidade → Pi' = Pi(Mini-MCV 15) = {fmt(v, 1)}%"


def compute_e_prime(d_: float, pi_ref: float) -> float:
    """Índice de laterização, Equação (1) da DNIT 259/2023-CLA: e' = ∛(Pi'/100 + 20/d')."""
    d = _num(d_); p = _num(pi_ref)
    if d is None or p is None:
        raise ValueError("Para calcular e', informe d' e Pi'.")
    if d <= 0:
        raise ValueError("d' deve ser maior que zero.")
    if p < 0:
        raise ValueError("Pi' não pode ser negativo.")
    return (p / 100.0 + 20.0 / d) ** (1.0 / 3.0)


def fronteira_L_N(c_: float) -> float:
    """e' da fronteira entre solos lateríticos (abaixo) e não lateríticos (acima)."""
    if c_ <= 0.59:
        return E_NA_LA
    if c_ < C_LA_LA:
        return _interp(LINHA_NA, c_)
    return E_N_L


def classify_mct(c_: float, e_: float) -> Tuple[str, List[str]]:
    """Localiza o ponto (c', e') no gráfico da Figura A1 da DNIT 259/2023-CLA."""
    r: List[str] = []
    lim = fronteira_L_N(c_)
    if e_ <= lim:
        r.append(f"e' = {fmt(e_, 3)} ≤ {fmt(lim, 3)} (fronteira L|N para c' = {fmt(c_, 3)}) → comportamento laterítico (L)")
        if c_ < C_LA_LA:
            g = "LA"; r.append(f"c' < {fmt(C_LA_LA, 2)} → LA")
        elif c_ < C_A_G:
            g = "LA'"; r.append(f"{fmt(C_LA_LA, 2)} ≤ c' < {fmt(C_A_G, 2)} → LA'")
        else:
            g = "LG'"; r.append(f"c' ≥ {fmt(C_A_G, 2)} → LG'")
        return g, r

    r.append(f"e' = {fmt(e_, 3)} > {fmt(lim, 3)} (fronteira L|N para c' = {fmt(c_, 3)}) → comportamento não laterítico (N)")
    c_na = _interp(LINHA_NA, e_, by="e")
    if c_ < c_na:
        r.append(f"c' < {fmt(c_na, 3)} (linha inclinada NA para e' = {fmt(e_, 3)}) → NA")
        return "NA", r
    if c_ >= C_NA_NG:
        r.append(f"c' ≥ {fmt(C_NA_NG, 2)} → NG'")
        return "NG'", r
    if c_ < LINHA_NS_NA[0][0]:
        r.append(f"c' ≥ {fmt(c_na, 3)} e acima do vértice (0,45; 1,75) → NS'")
        return "NS'", r
    e_lim = _interp(LINHA_NS_NA, c_)
    if e_ > e_lim:
        if c_ < C_A_G:
            r.append(f"e' > {fmt(e_lim, 3)} (linha NS'|NA') e c' < {fmt(C_A_G, 2)} → NS'")
            return "NS'", r
        r.append(f"e' > {fmt(e_lim, 3)} (linha NS'|NA') e c' ≥ {fmt(C_A_G, 2)} → NG'")
        return "NG'", r
    r.append(f"e' ≤ {fmt(e_lim, 3)} (linha NS'|NA') e c' < {fmt(C_NA_NG, 2)} → NA'")
    return "NA'", r


def _swap_L_N(group: str, c_: float) -> str:
    """Grupo do outro lado da fronteira L|N, para o mesmo c'."""
    if group.startswith("L"):
        e_test = fronteira_L_N(c_) + 1e-6
    else:
        e_test = fronteira_L_N(c_)
    return classify_mct(c_, e_test)[0]


def fronteiras_proximas(c_: float, e_: float, tol: float = 0.03) -> List[str]:
    """Fronteiras do ábaco (exceto a L|N, tratada pelo item 5.1 c) a menos de `tol` do ponto.
    Informativo: indica onde uma leitura gráfica pode levar ao grupo vizinho."""
    g = classify_mct(c_, e_)[0]
    avisos = []

    def vizinho(c2, e2):
        return classify_mct(c2, e2)[0]

    lateritico = e_ <= fronteira_L_N(c_)
    if lateritico:
        for cv in (C_LA_LA, C_A_G):
            if abs(c_ - cv) <= tol:
                g2 = vizinho(2 * cv - c_ + (1e-6 if c_ <= cv else -1e-6), e_)
                if g2 != g:
                    avisos.append(f"c' = {fmt(c_, 3)} a {fmt(abs(c_ - cv), 3)} da vertical c' = {fmt(cv, 2)} "
                                  f"(fronteira {g} | {g2})")
    else:
        c_na = _interp(LINHA_NA, e_, by="e")
        if abs(c_ - c_na) <= tol:
            g2 = vizinho(2 * c_na - c_, e_)
            if g2 != g:
                avisos.append(f"c' = {fmt(c_, 3)} a {fmt(abs(c_ - c_na), 3)} da linha inclinada NA "
                              f"(fronteira {g} | {g2})")
        if LINHA_NS_NA[0][0] <= c_ <= C_NA_NG:
            e_l = _interp(LINHA_NS_NA, c_)
            if abs(e_ - e_l) <= tol:
                g2 = vizinho(c_, 2 * e_l - e_)
                if g2 != g:
                    avisos.append(f"e' = {fmt(e_, 3)} a {fmt(abs(e_ - e_l), 3)} da linha inclinada "
                                  f"(0,45; 1,75)–(1,7; 1,15) (fronteira {g} | {g2})")
        if e_ > _interp(LINHA_NS_NA, C_A_G) and abs(c_ - C_A_G) <= tol:
            g2 = vizinho(2 * C_A_G - c_, e_)
            if g2 != g:
                avisos.append(f"c' = {fmt(c_, 3)} a {fmt(abs(c_ - C_A_G), 3)} da vertical c' = 1,50 "
                              f"(fronteira {g} | {g2})")
    return avisos


def classify_from_inputs(inp: MCTInput, *, tolerancia_LN: float = 0.05) -> MCTResult:
    """Classificação completa: valida entradas, obtém Pi', calcula e' e aplica o ábaco.
    tolerancia_LN: faixa de e' em torno da fronteira L|N considerada "próxima" (item 5.1 c)."""
    w: List[str] = []
    r: List[str] = []
    c = _num(inp.c_)
    if c is None:
        raise ValueError("Informe c'.")
    if c < 0:
        raise ValueError("c' não pode ser negativo.")

    pi_ref = _num(inp.pi_ref)
    dens = None
    e = _num(inp.e_)
    if e is None:
        if pi_ref is None:
            pi_ref, dens, txt = pi_referencia(inp.pi_10, inp.pi_15, inp.af_10)
            r.append(txt)
        else:
            r.append(f"Pi' informado diretamente = {fmt(pi_ref, 1)}%")
        e = compute_e_prime(inp.d_, pi_ref)
        golpes = 12 if str(inp.serie).lower().startswith("p") else 10
        r.append(f"e' = ∛(Pi'/100 + 20/d') = ∛({fmt(pi_ref, 1)}/100 + 20/{fmt(_num(inp.d_), 1)}) = {fmt(e, 3)} "
                 f"(d' da curva de {golpes} golpes, série {inp.serie})")
    else:
        r.append(f"e' informado diretamente = {fmt(e, 3)}")

    if not (C_MIN <= c <= C_MAX):
        w.append(f"c' = {fmt(c, 2)} fora do domínio do gráfico ({C_MIN}–{C_MAX}); classificação por extrapolação.")
    if not (E_MIN <= e <= E_MAX):
        w.append(f"e' = {fmt(e, 2)} fora do domínio do gráfico ({E_MIN}–{E_MAX}); classificação por extrapolação.")

    g, rg = classify_mct(c, e)
    r += rg

    dist = e - fronteira_L_N(c)
    if abs(dist) <= tolerancia_LN:
        crit = (inp.pi_inclinacao_negativa, inp.mcv_concavidade_para_cima)
        if None in crit:
            w.append(f"Ponto próximo da fronteira L|N (Δe' = {'+' if dist >= 0 else '−'}{fmt(abs(dist), 3)}). A norma manda verificar: "
                     "(i) curva Pi × Mini-MCV com inclinação negativa entre Mini-MCV 10 e 15; "
                     "(ii) curva Mini-MCV × hc com concavidade para cima. Informe os dois critérios.")
        else:
            laterit = all(crit)
            novo = g if g.startswith("L") == laterit else _swap_L_N(g, c)
            r.append("Ponto próximo da fronteira L|N: critérios do item 5.1 c) "
                     f"{'atendidos' if laterit else 'não atendidos'} → "
                     f"{'laterítico' if laterit else 'não laterítico'}"
                     + (f" (grupo ajustado de {g} para {novo})" if novo != g else ""))
            g = novo

    for f in fronteiras_proximas(c, e):
        w.append("Ponto próximo de fronteira do ábaco: " + f + ". Leituras gráficas podem indicar o grupo "
                 "vizinho; confira os coeficientes.")
    return MCTResult(group=g, c_=c, e_=e, pi_ref=pi_ref, densidade=dens, rationale=r, warnings=w)


def classify_dataframe_mct(df):
    """Classifica um DataFrame. Colunas aceitas (maiúsc./minúsc. indiferentes):
    c, d, Pi_ref | (Pi_10, Pi_15, AF_10), e (opcional), serie (opcional)."""
    import pandas as pd
    cols = {str(k).strip().lower().replace("'", ""): k for k in df.columns}

    def g(row, *names):
        for n in names:
            if n in cols:
                return row[cols[n]]
        return None

    out = []
    for _, row in df.iterrows():
        rec = row.to_dict()
        try:
            res = classify_from_inputs(MCTInput(
                c_=_num(g(row, "c", "c_")), d_=_num(g(row, "d", "d_")),
                pi_ref=_num(g(row, "pi_ref", "pi")), pi_10=_num(g(row, "pi_10")),
                pi_15=_num(g(row, "pi_15")), af_10=_num(g(row, "af_10", "af")),
                e_=_num(g(row, "e", "e_")), serie=str(g(row, "serie") or "simplificada")))
            rec.update({"e_calc": round(res.e_, 3), "Pi_ref_usado": res.pi_ref,
                        "Grupo_MCT": res.group, "Classe": res.classe,
                        "avisos": " | ".join(res.warnings), "relatorio": build_report(res)})
        except Exception as ex:
            rec.update({"Grupo_MCT": "ERRO", "avisos": str(ex)})
        out.append(rec)
    return pd.DataFrame(out)


def build_report(res: MCTResult, meta: Optional[Dict[str, str]] = None) -> str:
    p = res.props
    L = [f"=== Classificação MCT — {NORMA_CLA} ==="]
    if meta:
        L += [f"Projeto: {meta.get('projeto') or '-'}", f"Técnico: {meta.get('tecnico') or '-'}",
              f"Amostra: {meta.get('amostra') or '-'}"]
    L += [f"Grupo: {res.group} — {res.classe}, {p['nome'].lower()}",
          f"c' = {fmt(res.c_, 3)}   e' = {fmt(res.e_, 3)}" + (f"   Pi' = {fmt(res.pi_ref, 1)}%" if res.pi_ref is not None else ""),
          "", "Regras acionadas:"]
    L += [f"  • {x}" for x in res.rationale]
    if res.warnings:
        L += ["", "Avisos:"] + [f"  ⚠ {x}" for x in res.warnings]
    L += ["", f"Propriedades típicas (Anexo B, {NORMA_CLA}):",
          f"  Granulometria típica: {p['granulometria']}",
          f"  Mini-CBR sem imersão: {p['mini_cbr_sem_imersao']}",
          f"  Perda de suporte por imersão: {p['perda_suporte_imersao']}",
          f"  Expansão: {p['expansao']}",
          f"  Contração: {p['contracao']}",
          f"  Permeabilidade: {p['permeabilidade']}",
          f"  Plasticidade: {p['plasticidade']}",
          "", f"Descrição (Anexo C): {res.descricao}",
          f"Correlação pedológica/geológica: {res.correlacao}",
          f"Classificação resiliente (Tabela 15, Manual IPR-719): {res.resiliente[0]} — {res.resiliente[1]}"]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Gráfico
# ---------------------------------------------------------------------------
def plot_mct_abaco(ax=None):
    """Desenha o gráfico de classificação (Figura A1 da DNIT 259/2023-CLA)."""
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(7, 5))
    kw = dict(color="black", lw=1.4)
    dash = dict(color="black", lw=1.2, ls="--")
    xs, ys = zip(*LINHA_NA[:3]); ax.plot(xs, ys, **kw)                       # 0,27→0,59 (contínua)
    ax.plot([LINHA_NA[2][0], LINHA_NA[3][0]], [LINHA_NA[2][1], LINHA_NA[3][1]], **dash)  # 0,59→0,70
    xs, ys = zip(*LINHA_NS_NA); ax.plot(xs, ys, **kw)
    ax.plot([0, 0.59], [E_NA_LA, E_NA_LA], **dash)
    ax.plot([C_LA_LA, C_MAX], [E_N_L, E_N_L], **dash)
    ax.plot([C_LA_LA, C_LA_LA], [E_MIN, E_N_L], **kw)
    ax.plot([C_A_G, C_A_G], [E_MIN, E_N_L], **kw)
    ax.plot([C_A_G, C_A_G], [_interp(LINHA_NS_NA, C_A_G), E_MAX], **kw)
    for txt, x, y in [("NA", 0.22, 1.78), ("NS'", 0.95, 1.9), ("NG'", 2.0, 1.7), ("NA'", 1.25, 1.28),
                      ("LA", 0.3, 0.9), ("LA'", 1.05, 0.8), ("LG'", 2.0, 0.8)]:
        ax.text(x, y, txt, fontsize=11, fontweight="bold", ha="center")
    ax.set_xlim(C_MIN, C_MAX); ax.set_ylim(E_MIN, E_MAX)
    ax.set_xlabel("Coeficiente c'"); ax.set_ylabel("Índice e'")
    ax.grid(True, ls=":", alpha=0.5)
    ax.set_title(f"Classificação MCT — Figura A1, {NORMA_CLA}", fontsize=10)
    return (ax.figure, ax) if created else ax


def plot_point_on_abaco(c_: float, e_: float, ax=None, label: Optional[str] = None):
    created = ax is None
    if created:
        fig, ax = plt.subplots(figsize=(7, 5))
        plot_mct_abaco(ax=ax)
    x = min(max(c_, C_MIN), C_MAX); y = min(max(e_, E_MIN), E_MAX)
    ax.scatter([x], [y], s=60, zorder=5, color="tab:red")
    ax.annotate(label or f"(c'={fmt(c_, 2)}; e'={fmt(e_, 2)})", (x, y), xytext=(6, 8),
                textcoords="offset points", fontsize=9)
    return (ax.figure, ax) if created else ax


# Planilha-modelo: um exemplo por grupo (conferidos em tests/test_mct.py).
# Colunas: c (c'), d (d'), Pi_ref (Pi') ou Pi_10, Pi_15 e AF_10 (mm), e (e' direto), serie.
EXEMPLOS = [
    ("LA",  "Areia laterítica",                  dict(c=0.40, d=40, Pi_ref=30)),
    ("LA'", "Arenoso laterítico (Pi' pela AF)",  dict(c=1.20, d=50, Pi_10=80, Pi_15=20, AF_10=46.5)),
    ("LG'", "Argiloso laterítico",               dict(c=1.80, d=60, Pi_ref=40)),
    ("NA",  "Areia não laterítica",              dict(c=0.20, d=15, Pi_ref=200)),
    ("NA'", "Arenoso não laterítico",            dict(c=1.00, d=20, Pi_10=150, Pi_15=90, AF_10=49.0)),
    ("NS'", "Siltoso não laterítico",            dict(c=1.00, d=10, Pi_ref=250)),
    ("NG'", "Argiloso não laterítico",           dict(c=2.00, d=15, Pi_ref=150)),
]
