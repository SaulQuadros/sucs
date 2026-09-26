# -*- coding: utf-8 -*-
# didatica/ex_numerico_mct.py
# Exemplo numérico guiado da classificação MCT, etapa por etapa, com as variáveis explicadas ao lado.
#
# Adaptado de: Quadros, S. G. R. (2025). 1ª Atividade Avaliativa — MCT. Materiais de Pavimentação, PEC/UFJF.
# Dados de Barbosa, D. P. (2021). Estudo da metodologia MCT, com apresentação de exemplo de classificação
# de um solo. TCC — UFJF.
#
# Os valores são o recálculo exato das leituras pelo mesmo núcleo do modo Laboratório (mct_lab), segundo a
# DNIT 258/2023-ME e a DNIT 259/2023-CLA.
from __future__ import annotations

import math
import re
from functools import lru_cache

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from formato import fmt
from mct_core import MCTInput, classify_from_inputs, fronteira_L_N, plot_mct_abaco, plot_point_on_abaco
from mct_lab import (AREA_CM2, GOLPES_REF, calcular, exemplo_barbosa_2021, para_tabelas, plot_af,
                     plot_compactacao, plot_deformabilidade, plot_pi, tabela_cps)

CREDITO = ("Adaptado de: Quadros, S. G. R. (2025). *1ª Atividade Avaliativa — MCT*. Materiais de Pavimentação, "
           "PEC/UFJF. Dados de Barbosa, D. P. (2021), TCC UFJF. Valores recalculados a partir das leituras "
           "(DNIT 258/2023-ME e DNIT 259/2023-CLA).")

# Barbosa (2021): massa seca desprendida e massa seca da parte extrudada do CP 20 (para o exemplo de Pi)
MD_CP20, MEX_CP20 = 19.7, 28.74


@lru_cache(maxsize=1)
def dados():
    serie, cps, _ = exemplo_barbosa_2021()
    R = calcular(cps, serie)
    res = classify_from_inputs(MCTInput(c_=R.c_, d_=R.d_, pi_ref=R.pi_ref, serie="Parsons",
                                        pi_inclinacao_negativa=R.crit_pi_negativa,
                                        mcv_concavidade_para_cima=R.crit_concavidade))
    return serie, cps, R, res


def _cp(cps, nome):
    return next(c for c in cps if c.nome == nome)


def _cruzamento_2mm(R, nome):
    """(n0, a0, n1, a1) do trecho da curva que cruza 2 mm."""
    pts = R.curvas[nome]
    for (n0, a0), (n1, a1) in zip(pts, pts[1:]):
        if a0 >= 2.0 >= a1:
            return n0, a0, n1, a1
    return None


def _latex(expr: str):
    """st.latex com vírgula decimal: no KaTeX, "2,56" vira "2, 56"; "2{,}56" mantém o número junto."""
    st.latex(re.sub(r"(\d),(\d)", r"\1{,}\2", expr))


def _grafico(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# --------------------------------------------------------------------------------------------- etapas
def etapa_dados():
    serie, cps, R, _ = dados()
    st.markdown("Cinco corpos de prova, compactados com umidades diferentes na **série de Parsons** "
                "(1 a 256 golpes). Em cada golpe da série lê-se a **altura do CP**. Cada CP tem 200 g de solo "
                "úmido; a massa seca sai da umidade de compactação.")
    with st.container(border=True):
        st.markdown("**Como as umidades são definidas** (DNIT 258/2023-ME, seção 6, alíneas f a j)")
        st.markdown(
            "- A amostra que passa na peneira nº 10 é dividida em **cinco porções** de cerca de 500 g.\n"
            "- Uma delas recebe água até uma umidade **próxima da ótima presumível** (porção nº 3).\n"
            "- Das outras, **duas ficam mais secas e duas mais úmidas**, com umidades sucessivamente crescentes e "
            "diferença entre pontos consecutivos de cerca de **1% a 2% (solos arenosos)** ou **2% a 3% (solos "
            "argilosos e siltosos)**.\n"
            "- As porções repousam em câmara úmida por pelo menos 12 h e são compactadas em **ordem decrescente "
            "de umidade**; a umidade real de cada CP é determinada em cápsula.")
        st.dataframe(pd.DataFrame({"CP": [c.nome for c in cps], "Umidade h_c (%)": [c.hc for c in cps],
                                   "Diferença para o anterior (pontos %)": ["—"] + [
                                       fmt(b.hc - a.hc) for a, b in zip(cps, cps[1:])]}).set_index("CP").T,
                     use_container_width=True)
        st.caption("No exemplo, os passos ficam em torno de 2%, com a porção central em 27,1%. Os números 6, 8, 19, "
                   "20 e 22 são a identificação dos CPs no laboratório, não uma sequência.")
    _latex(r"M_s = \frac{m_u}{1 + h_c/100}")
    c6 = _cp(cps, "CP6")
    _latex(rf"M_{{s,\,CP6}} = \frac{{200}}{{1 + {fmt(c6.hc)}/100}} = {fmt(c6.ms)}\ \text{{g}}")
    alt, _ = para_tabelas(serie, cps)
    alt = alt.rename(columns={"golpes": "n (golpes)"}).set_index("n (golpes)")
    st.markdown("**Alturas do CP (mm)** — $A_n$ para cada número de golpes")
    st.dataframe(alt, use_container_width=True, height=300)
    st.dataframe(pd.DataFrame({"CP": [c.nome for c in cps], "h_c (%)": [c.hc for c in cps],
                               "M_s (g)": [round(c.ms, 1) for c in cps]}).set_index("CP").T,
                 use_container_width=True)
    st.caption("Na planilha de Barbosa (2021), leitura do extensômetro + altura = 93,79 mm em todas as linhas: "
               "é a constante K_a do equipamento (altura = K_a − leitura).")


def etapa_afundamento():
    serie, cps, R, _ = dados()
    st.markdown("O **afundamento** mede quanto o CP ainda se compacta quando os golpes são quadruplicados. "
                "Na série de Parsons, compara-se a altura em $n$ com a altura em $4n$.")
    _latex(r"a_n = A_n - A_{4n}")
    c6 = _cp(cps, "CP6")
    _latex(rf"a_{{1,\,CP6}} = A_1 - A_4 = {fmt(c6.alturas[1], 2)} - {fmt(c6.alturas[4], 2)} "
             rf"= {fmt(c6.alturas[1] - c6.alturas[4], 2)}\ \text{{mm}}")
    ns = sorted({n for c in cps for n, _ in R.curvas[c.nome]})
    tab = pd.DataFrame({c.nome: [dict(R.curvas[c.nome]).get(n) for n in ns] for c in cps}, index=ns)
    tab.index.name = "n (golpes)"
    st.markdown("**Afundamentos $a_n$ (mm)**")
    st.dataframe(tab.round(2).astype(object).where(tab.notna(), "—"), use_container_width=True, height=300)
    with st.container(border=True):
        st.markdown("**Por que os CPs têm quantidades diferentes de afundamentos**")
        st.markdown("A compactação de cada CP termina quando ocorre o primeiro destes casos (DNIT 258/2023-ME, "
                    "procedimento, alínea h): **(i)** na série de Parsons, a diferença entre as leituras dos golpes "
                    "**4n e n é inferior a 2 mm**; **(ii)** na série Simplificada, a diferença entre dois pontos "
                    "consecutivos é inferior a 0,1 mm; **(iii)** há intensa exsudação de água no topo e na base; "
                    "**(iv)** o número de golpes atinge **256** (Parsons) ou 250 (Simplificada).")
        ult = {c.nome: max(c.alturas) for c in cps}
        c22, c6 = _cp(cps, "CP22"), _cp(cps, "CP6")
        st.markdown(f"- **CP 22** ({fmt(c22.hc)}%, o mais úmido): no golpe {ult['CP22']} = 4 × 6, "
                    f"$a_6$ = {fmt(c22.alturas[6], 2)} − {fmt(c22.alturas[24], 2)} = "
                    f"{fmt(c22.alturas[6] - c22.alturas[24], 2)} mm < 2 mm → critério (i).\n"
                    f"- **CP 6** ({fmt(c6.hc)}%, o mais seco): chegou a {ult['CP6']} golpes → critério (iv).")
        st.markdown("Como $a_n = A_n - A_{4n}$, só há afundamento para os $n$ cujo quádruplo foi lido: o CP 22 "
                    "(até 24 golpes) tem $a_n$ para n ≤ 6 (5 valores); o CP 6 (até 256), para n ≤ 64 (12 valores). "
                    "Os pontos ausentes ficariam abaixo de 2 mm e não alteram o Mini-MCV nem o c′.")


def etapa_deformabilidade():
    _, _, R, _ = dados()
    st.markdown("Plota-se, para cada CP, o afundamento contra o número de golpes em escala logarítmica, "
                "usando $10\\cdot\\log_{10} n$ no eixo horizontal (Figura A10 da DNIT 258/2023-ME). "
                "A linha pontilhada horizontal marca **2 mm**; a vertical, o valor **10** do eixo.")
    _grafico(plot_deformabilidade(R, destacar=False))
    st.markdown("Os CPs mais úmidos (CP 22, CP 20) chegam a 2 mm com poucos golpes e ficam à esquerda; os mais "
                "secos (CP 6) precisam de muitos golpes e ficam à direita.")


def etapa_mini_mcv():
    _, cps, R, _ = dados()
    st.markdown("O **Mini-MCV** de cada CP é $10\\cdot\\log_{10}$ do número de golpes $B_n$ em que a curva "
                "cruza 2 mm. Interpola-se linearmente, no eixo $10\\cdot\\log_{10} n$, entre os dois pontos "
                "vizinhos.")
    _latex(r"\text{Mini-MCV} = 10\cdot\log_{10}(B_n)")
    n0, a0, n1, a1 = _cruzamento_2mm(R, "CP19")
    x0, x1 = 10 * math.log10(n0), 10 * math.log10(n1)
    m = R.mcv["CP19"]
    st.markdown(f"**CP 19:** $a_{{{n0}}} = {fmt(a0, 2)}$ mm e $a_{{{n1}}} = {fmt(a1, 2)}$ mm envolvem 2 mm.")
    _latex(rf"\text{{Mini-MCV}}_{{CP19}} = {fmt(x0, 2)} + \frac{{{fmt(a0, 2)} - 2}}{{{fmt(a0, 2)} - {fmt(a1, 2)}}}"
             rf"\,({fmt(x1, 2)} - {fmt(x0, 2)}) = {fmt(m, 2)}\qquad B_n = 10^{{{fmt(m / 10, 3)}}} = {fmt(10 ** (m / 10), 1)}")
    linhas = []
    for c in cps:
        cr = _cruzamento_2mm(R, c.nome)
        linhas.append({"CP": c.nome, "h_c (%)": c.hc, "trecho que cruza 2 mm": f"n = {cr[0]} → {cr[2]}",
                       "B_n (golpes)": round(10 ** (R.mcv[c.nome] / 10), 1), "Mini-MCV": round(R.mcv[c.nome], 2)})
    st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)
    st.caption("Quanto mais seco o CP, maior o Mini-MCV (mais energia para compactá-lo).")


def etapa_c():
    _, _, R, _ = dados()
    det = R.c_detalhe
    (n1, n2), (m1, m2), w = det["cps"], det["mcv"], det["peso_superior"]
    (xa, ya), (xb, yb) = det["linha"]
    st.markdown("O **coeficiente de argilosidade** é a inclinação do trecho retilíneo mais inclinado da curva "
                "de deformabilidade com **Mini-MCV = 10** (DNIT 258/2023-ME, seção 3.10). Nenhum CP tem exatamente "
                "10; por isso, essa curva é **interpolada** entre as duas vizinhas (Nota 3).")
    _latex(r"c' = \left|\frac{\Delta a_n}{\Delta(\text{Mini-MCV})}\right|")
    st.markdown(f"**1. Curva interpolada.** As vizinhas são **{n1}** (Mini-MCV {fmt(m1, 2)}) e **{n2}** (Mini-MCV "
                f"{fmt(m2, 2)}). Cada uma é deslocada no eixo para cruzar 2 mm em 10, e a curva com Mini-MCV = 10 é "
                f"a média ponderada das duas, com peso maior para a mais próxima de 10:")
    _latex(rf"w_{{{n2}}} = \frac{{10 - {fmt(m1, 2)}}}{{{fmt(m2, 2)} - {fmt(m1, 2)}}} = {fmt(w, 2)}\qquad "
           rf"w_{{{n1}}} = 1 - {fmt(w, 2)} = {fmt(1 - w, 2)}")
    st.markdown("Por construção, a curva interpolada (tracejada no gráfico) passa por **(10; 2 mm)**.")
    st.markdown(f"**2. Trecho retilíneo mais inclinado** da curva interpolada: de 10·log n = {fmt(xa, 2)} "
                f"(n = {fmt(10 ** (xa / 10), 2)} golpes; aₙ = {fmt(ya, 2)} mm) a {fmt(xb, 2)} "
                f"(aₙ = {fmt(yb, 2)} mm), destacado com o triângulo amarelo:")
    _latex(rf"c' = \frac{{{fmt(ya, 2)} - {fmt(yb, 2)}}}{{{fmt(xb, 2)} - {fmt(xa, 2)}}} = "
           rf"\frac{{{fmt(ya - yb, 2)}}}{{{fmt(xb - xa, 2)}}} = {fmt(R.c_, 2)}")
    _grafico(plot_deformabilidade(R, destacar=True))
    st.caption("Na região laterítica do ábaco: c′ < 0,70 → areias (LA); 0,70 a 1,50 → arenosos (LA′); "
               "≥ 1,50 → argilosos (LG′).")


def etapa_meas():
    _, cps, R, _ = dados()
    nref = GOLPES_REF["Parsons"]
    st.markdown(f"A **massa específica aparente seca** de cada CP, em cada golpe, é a massa seca dividida pelo "
                f"volume do cilindro (área de 19,635 cm²). Para a curva de referência da série de Parsons usa-se "
                f"a altura a **{nref} golpes**.")
    _latex(r"\text{MEAS} = \frac{M_s}{A\cdot h}")
    c6 = _cp(cps, "CP6")
    h = c6.alturas[nref]
    _latex(rf"\text{{MEAS}}_{{CP6,\,{nref}}} = \frac{{{fmt(c6.ms)}\ \text{{g}}}}{{{fmt(AREA_CM2, 3)}\ \text{{cm}}^2"
             rf"\times {fmt(h / 10, 3)}\ \text{{cm}}}} = {fmt(c6.meas(nref) / 1000, 3)}\ \text{{g/cm}}^3 = "
             rf"{fmt(c6.meas(nref), 0)}\ \text{{kg/m}}^3")
    st.dataframe(pd.DataFrame({"CP": [c.nome for c in cps], "h_c (%)": [c.hc for c in cps],
                               f"h a {nref} golpes (mm)": [c.alturas.get(nref) for c in cps],
                               f"MEAS {nref} golpes (kg/m³)": [round(c.meas(nref)) for c in cps]}),
                 hide_index=True, use_container_width=True)
    st.markdown("Com a MEAS de cada CP em vários números de golpes, traçam-se as **curvas de compactação** "
                "(Figura A11). A de 12 golpes, em vermelho, é a de referência.")
    _grafico(plot_compactacao(R, destacar=False))


def etapa_d():
    _, _, R, _ = dados()
    jan = R.d_detalhe["janela"]
    (xa, ya), (xb, yb) = R.d_detalhe["linha"]
    st.markdown("O **coeficiente d′** é a inclinação do trecho retilíneo mais inclinado do **ramo seco** da "
                "curva de 12 golpes (DNIT 258/2023-ME, seção 3.12). O ramo seco vai do CP mais seco até o ponto "
                "de MEAS máxima.")
    _latex(r"d' = \frac{\Delta\,\text{MEAS}}{\Delta h_c}")
    pts = " · ".join(f"({fmt(h)}%; {fmt(v, 0)})" for h, v in jan)
    st.markdown(f"Trecho retilíneo mais inclinado: pontos {pts} kg/m³, com a reta ajustada a eles "
                f"(triângulo amarelo no gráfico):")
    _latex(rf"d' = \frac{{{fmt(yb, 0)} - {fmt(ya, 0)}}}{{{fmt(xb)} - {fmt(xa)}}} = "
           rf"\frac{{{fmt(yb - ya, 0)}\ \text{{kg/m}}^3}}{{{fmt(xb - xa)}\ \%}} = {fmt(R.d_, 1)}\ \text{{kg/m}}^3/\%")
    _grafico(plot_compactacao(R, destacar=True))
    st.caption("Ramo seco íngreme (d′ alto) é típico de solos lateríticos argilosos; ramo suave (d′ baixo), de "
               "solos saprolíticos e siltosos. O Manual de Pavimentação descreve d′ como a inclinação "
               "“multiplicada por 10³”, que é a passagem de g/cm³ para kg/m³.")


def etapa_pi():
    _, cps, R, _ = dados()
    st.markdown("A **perda de massa por imersão** de cada CP é a fração da parte extrudada (cerca de 10 mm) que "
                "se desprende na água.")
    _latex(r"P_i = 100\cdot\frac{M_d\cdot L_{cp}}{M_s\cdot L_{ex}}\cdot F_c")
    st.markdown("Como $M_s\\,L_{ex}/L_{cp}$ é a massa seca da parte extrudada ($M_{ex}$), a mesma equação "
                "pode ser escrita como:")
    _latex(r"P_i = 100\cdot\frac{M_d}{M_{ex}}\cdot F_c\qquad M_{ex} = \frac{M_s\,L_{ex}}{L_{cp}}")
    _latex(rf"P_{{i,\,CP20}} = 100\cdot\frac{{{fmt(MD_CP20)}\ \text{{g}}}}{{{fmt(MEX_CP20, 2)}\ \text{{g}}}}"
             rf"\cdot 1 = {fmt(100 * MD_CP20 / MEX_CP20, 1)}\ \%")
    st.dataframe(tabela_cps(R)[["CP", "Mini-MCV", "Altura final (mm)", "Pi (%)"]], hide_index=True,
                 use_container_width=True)
    (n1, n2), (m1, m2) = R.c_detalhe["cps"], R.c_detalhe["mcv"]
    a1, a2 = _cp(cps, n1).af, _cp(cps, n2).af
    p1, p2 = _cp(cps, n1).pi, _cp(cps, n2).pi
    st.markdown(f"**Altura final no Mini-MCV = 10**, interpolada entre {n1} e {n2}:")
    _latex(rf"A_f(10) = {fmt(a1, 2)} + ({fmt(a2, 2)} - {fmt(a1, 2)})\,\frac{{10 - {fmt(m1, 2)}}}"
             rf"{{{fmt(m2, 2)} - {fmt(m1, 2)}}} = {fmt(R.af10, 2)}\ \text{{mm}}")
    _latex(rf"A_f(10) = {fmt(R.af10, 2)}\ \text{{mm}}\ \geq\ 48{{,}}0\ \text{{mm}}\ \Rightarrow\ "
           r"\text{baixa densidade}")
    st.markdown("Solo de baixa densidade: $P_i'$ é o Pi no **Mini-MCV = 10** (DNIT 259/2023-CLA, seção 3.8).")
    _latex(rf"P_i' = {fmt(p1, 2)} + ({fmt(p2, 2)} - {fmt(p1, 2)})\,\frac{{10 - {fmt(m1, 2)}}}"
             rf"{{{fmt(m2, 2)} - {fmt(m1, 2)}}} = {fmt(R.pi_ref, 1)}\ \%")
    g1, g2 = st.columns(2)
    with g1:
        _grafico(plot_af(R))
    with g2:
        _grafico(plot_pi(R))


def etapa_e():
    _, _, R, res = dados()
    st.markdown("O **índice de laterização** combina a perda por imersão e a inclinação do ramo seco.")
    _latex(rf"e' = \sqrt[3]{{\frac{{P_i'}}{{100}} + \frac{{20}}{{d'}}}} = "
             rf"\sqrt[3]{{\frac{{{fmt(R.pi_ref, 1)}}}{{100}} + \frac{{20}}{{{fmt(R.d_, 1)}}}}} = "
             rf"\sqrt[3]{{{fmt(R.pi_ref / 100 + 20 / R.d_, 4)}}} = {fmt(res.e_, 3)}")
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    plot_mct_abaco(ax=ax)
    plot_point_on_abaco(res.c_, res.e_, ax=ax, label=res.group)
    fig.tight_layout()
    c_g, c_t = st.columns([1.5, 1])
    with c_g:
        _grafico(fig)
    with c_t:
        lim = fronteira_L_N(res.c_)
        st.markdown(f"Ponto ($c'$ = {fmt(res.c_, 2)}; $e'$ = {fmt(res.e_, 3)}):")
        st.markdown(f"- $c' \\geq 1{{,}}50$ → argiloso (G′)\n- $e' = {fmt(res.e_, 3)} \\leq {fmt(lim, 2)}$ → "
                    f"laterítico (L), a {fmt(lim - res.e_, 2)} da fronteira: os critérios de desempate do item "
                    f"5.1 c) não são necessários.")
        st.markdown(f"<div style='font-size:2.2rem;font-weight:700'>{res.group}</div>"
                    f"{res.classe} · {res.props['nome'].lower()}", unsafe_allow_html=True)
        st.markdown(res.descricao)
    st.caption("Barbosa (2021) obteve c′ = 2,45 e e′ = 0,928, também LG′. A pequena diferença vem da leitura "
               "gráfica do trecho retilíneo e da interpolação da curva com Mini-MCV = 10.")


def etapa_resumo():
    serie, cps, R, res = dados()
    st.markdown("Encadeamento completo, dos dados do ensaio ao grupo:")
    linhas = [
        ("CP", "Corpos de prova", "—", "5 (umidades de 23,1 a 31,0%)"),
        ("$h_c$", "Umidade de compactação", "%", "23,1 · 25,2 · 27,1 · 29,0 · 31,0"),
        ("$A_n$", "Altura do CP após n golpes", "mm", "série de Parsons, 1 a 256 golpes"),
        ("$a_n$", "Afundamento $A_n - A_{4n}$", "mm", "ex.: 8,81 (CP 6, n = 1)"),
        ("Mini-MCV", "$10\\log_{10}B_n$", "—", " · ".join(fmt(R.mcv[c.nome], 2) for c in cps)),
        ("$c'$", "Coeficiente de argilosidade", "—", fmt(R.c_, 2)),
        ("MEAS", "Massa específica aparente seca (12 golpes)", "kg/m³",
         " · ".join(fmt(c.meas(12), 0) for c in cps)),
        ("$d'$", "Inclinação do ramo seco", "kg/m³/%", fmt(R.d_, 1)),
        ("$P_i$", "Perda de massa por imersão", "%", " · ".join(fmt(c.pi, 1) for c in cps)),
        ("$A_f(10)$", "Altura final no Mini-MCV = 10", "mm", f"{fmt(R.af10, 2)} → baixa densidade"),
        ("$P_i'$", "Pi de referência (Mini-MCV = 10)", "%", fmt(R.pi_ref, 1)),
        ("$e'$", "Índice de laterização", "—", fmt(res.e_, 3)),
        ("Grupo", "Ábaco da Figura A1 (DNIT 259/2023-CLA)", "—", f"**{res.group}** — {res.classe.lower()}, "
                                                                  f"{res.props['nome'].lower()}"),
    ]
    md = "| Símbolo | Grandeza | Unidade | Valor no exemplo |\n|---|---|---|---|\n" + "\n".join(
        f"| {a} | {b} | {c} | {d} |" for a, b, c, d in linhas)
    st.markdown(md)
    st.markdown("Para refazer o cálculo interativamente, alterar leituras ou ajustar os trechos retilíneos, "
                "abra o exemplo no modo **Laboratório**.")


# (título curto, função, chaves do glossário exibidas no painel)
ETAPAS = [
    ("Dados do ensaio", etapa_dados, ["cp", "hc", "n", "an_altura"]),
    ("Afundamento", etapa_afundamento, ["a4n", "afundamento"]),
    ("Curvas de deformabilidade", etapa_deformabilidade, ["deformabilidade", "n"]),
    ("Mini-MCV", etapa_mini_mcv, ["bn", "mini_mcv"]),
    ("Coeficiente c′", etapa_c, ["trecho", "c"]),
    ("MEAS e curvas de compactação", etapa_meas, ["meas", "compactacao"]),
    ("Coeficiente d′", etapa_d, ["trecho", "d"]),
    ("Pi, altura final e Pi′", etapa_pi, ["pi", "pi_vars", "af", "densidade", "pi_ref"]),
    ("Índice e′, ábaco e grupo", etapa_e, ["e", "abaco", "grupos"]),
    ("Resumo", etapa_resumo, ["mct"]),
]
