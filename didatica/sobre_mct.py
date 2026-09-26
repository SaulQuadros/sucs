# -*- coding: utf-8 -*-
# didatica/sobre_mct.py
# Menu "Sobre o MCT": Introdução, Fundamentos e Fluxograma de ensaios, no mesmo roteiro do Ex. numérico.
# Conteúdo baseado nas normas DNIT vigentes (lista IPR de 24/09/2026), no Manual de Pavimentação IPR-719 e
# na aula 03 de Materiais de Pavimentação.
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.patches import FancyBboxPatch

FONTES = ("Fontes: DNIT 228/2023-ME, 254/2023-ME, 258/2023-ME, 259/2023-CLA, 444/2023-CLA e 445/2023-ES; "
          "Manual de Pavimentação DNIT (IPR-719/2006); Nogami e Villibor (1981, 1995).")


def introducao():
    st.markdown("""
**Por que o método existe.** As classificações tradicionais, SUCS e TRB (HRB/AASHTO), foram desenvolvidas em
países de clima temperado e se baseiam em granulometria e limites de Atterberg. Aplicadas aos solos tropicais,
elas correlacionam mal com o comportamento em obra. O Manual de Pavimentação do DNIT registra que *“as diferenças
de propriedades que caracterizam os solos lateríticos e saprolíticos, retratados na classificação MCT, não se
refletem no gráfico de plasticidade ou no grupo das classificações tradicionais”* (IPR-719, p. 76). Um solo
laterítico pode cair em A-6 ou A-7 e, compactado, ter ótimo desempenho; um saprolítico pode ter boa
classificação e ser expansivo ou erodível.

**Quem criou.** A metodologia MCT (**M**iniatura, **C**ompactado, **T**ropical) foi desenvolvida por
**Job Shuji Nogami** e **Douglas Fadul Villibor** e apresentada em 1981, “com a finalidade básica de melhor
caracterizar os solos tropicais” (IPR-719, p. 66). Ela foi simplificada com a adaptação, para corpos de prova
miniatura, do ensaio MCV (*Moisture Condition Value*) de Parsons (1976), de onde vem o **Mini-MCV**.

**Objetivo.** Classificar os solos finos tropicais pelo **comportamento** que apresentam compactados:
**laterítico (L)** ou **não laterítico (N)**, e pelo caráter granulométrico (areias, arenosos, siltosos,
argilosos). O ponto central é medir propriedades mecânicas e hidráulicas em corpos de prova compactados, e não
só índices físicos. Com isso, o método orienta a escolha de solos para camadas de pavimento, reforço, subleito,
aterros e revestimento primário, e viabilizou o uso de solos lateríticos em pavimentos de baixo custo.
""")
    st.markdown("**O MCT no DNIT hoje**")
    st.markdown("""
- **Métodos de ensaio e classificação** (revisados em 2023): DNIT 228/2023-ME (compactação miniatura),
  DNIT 254/2023-ME (Mini-CBR e expansão), DNIT 258/2023-ME (Mini-MCV e perda de massa por imersão),
  DNIT 259/2023-CLA (classificação de solos finos) e DNIT 444/2023-CLA (G-MCT, solos grossos).
- **Onde é exigido:** a **DNIT 445/2023-ES — Revestimento primário** manda classificar pela MCT
  (DNIT 259-CLA) os materiais finos, com 95% passando na peneira nº 10, com os ensaios Mini-MCV e perda por
  imersão (DNIT 258-ME). O grupo define a **prioridade de escolha** (Tabela B1). Para os lateríticos,
  exige-se ainda Mini-CBR ≥ 12% e expansão < 0,5% (DNIT 254-ME). A fração grossa é avaliada pela
  DNIT 444-CLA.
- **Manual de Pavimentação (IPR-719):** apresenta a classificação MCT ao lado da SUCS e da TRB (Tabela 9,
  Figura 19) e a relação MCT × classificação resiliente (Tabela 15).
- **Atenção:** a DNIT 098/2007-ES (base com solo laterítico) identifica o solo laterítico pela relação
  sílica-sesquióxidos < 2 (DNER-ME 030/94), e não pela MCT.
""")
    st.markdown("**Prioridade de escolha para revestimento primário** (DNIT 445/2023-ES, Tabela B1)")
    st.markdown("| Grupo MCT | LA′ | LG′ | NA′ | LA | NA | NS′ | NG′ |\n|---|---|---|---|---|---|---|---|\n"
                "| Prioridade | 1º | 2º | 3º | 4º | 5º | não recomendado | não recomendado |")
    st.markdown("""
**Resultado principal.** O **grupo MCT**, um de sete (LA, LA′, LG′, NA, NA′, NS′, NG′), obtido pelo ponto
(c′, e′) no ábaco da DNIT 259/2023-CLA. Com o grupo vêm as **propriedades típicas** (Anexo B: Mini-CBR,
perda de suporte por imersão, expansão, contração, permeabilidade, plasticidade) e a **indicação de uso**
(Anexo C e, para revestimento primário, a Tabela B1 da DNIT 445/2023-ES).
""")


def fundamentos():
    st.markdown("""
**1. Solos tropicais: lateríticos e saprolíticos.** Em clima tropical úmido, os horizontes superficiais bem
drenados sofrem **laterização**: lixiviação de bases e sílica, enriquecimento em óxidos e hidróxidos de ferro e
alumínio e predominância de caulinita. O resultado são agregações estáveis e cores avermelhadas ou amareladas.
Abaixo deles ficam os **solos saprolíticos**, jovens, que guardam minerais e estrutura da rocha de origem (micas,
argilominerais que podem ser expansivos) e são heterogêneos.

**2. Comportamento compactado.** Os lateríticos compactados perdem pouca massa na água, têm baixa expansão e
alta capacidade de suporte, podendo apresentar contração. Os não lateríticos tendem a ser sensíveis à água:
expansão, erodibilidade e perda de suporte com imersão. Essa diferença não aparece na granulometria nem nos
limites de Atterberg; por isso a MCT mede o comportamento diretamente, em corpos de prova compactados.

**3. Por que miniatura.** Os corpos de prova têm 50 mm de diâmetro e usam a fração que passa na peneira nº 10
(2 mm). É preciso pouca amostra (mínimo de 2,5 kg da fração fina), e os ensaios são rápidos e repetíveis. Daí o
foco em **solos finos**; os solos grossos são tratados pela G-MCT (DNIT 444/2023-CLA).

**4. Mini-MCV: a energia de compactação.** Em cada umidade, o corpo de prova recebe golpes crescentes até
parar de se compactar. O Mini-MCV = 10·log₁₀(B<sub>n</sub>) mede quantos golpes foram necessários: solo seco
exige muitos golpes (Mini-MCV alto); solo úmido, poucos (Mini-MCV baixo). É a referência comum para comparar
os corpos de prova.

**5. Os dois eixos da classificação.**
- **c′ (coeficiente de argilosidade):** inclinação da curva de deformabilidade com Mini-MCV = 10. Cresce com o
  caráter argiloso do solo: separa areias (c′ baixo) de arenosos e argilosos (c′ alto).
- **e′ (índice de laterização):** e′ = ∛(Pi′/100 + 20/d′). Solos lateríticos têm **Pi′ baixo** (estáveis na
  água) e **d′ alto** (ramo seco íngreme), portanto **e′ baixo**.

O Pi′ é lido no Mini-MCV 10 ou 15, conforme a densidade do solo compactado (altura final ≥ ou < 48 mm), para
comparar os solos em condição de compactação equivalente.

**6. O ábaco.** No gráfico c′ × e′ (Figura A1 da DNIT 259/2023-CLA), a fronteira entre lateríticos (abaixo) e
não lateríticos (acima) fica em e′ = 1,15 para c′ ≥ 0,70 e sobe até 1,40 para os solos arenosos. As verticais
c′ = 0,70 e 1,50 e as linhas inclinadas separam os grupos. Perto da fronteira L|N, a norma recomenda a série de
Parsons e aplica dois critérios de desempate (item 5.1 c).
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------------------------- fluxograma
AZUL, AZUL_CLARO, CINZA, CINZA_CLARO = "#1F4E79", "#DCE8F5", "#555555", "#F2F2F2"


def _caixa(ax, x, y, w, h, texto, destaque=False, fs=10.5, negrito=False):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=AZUL_CLARO if destaque else CINZA_CLARO,
                                ec=AZUL if destaque else CINZA, lw=2.0 if destaque else 1.0))
    ax.text(x, y, texto, ha="center", va="center", fontsize=fs, fontweight="bold" if negrito else "normal",
            color="#10263d" if destaque else "#222222", linespacing=1.25)


def _seta(ax, x0, y0, x1, y1, destaque=False):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", lw=1.8 if destaque else 1.0,
                                color=AZUL if destaque else CINZA, shrinkA=0, shrinkB=0))


def plot_fluxograma():
    """Fluxograma da metodologia MCT (redesenhado): destaca o caminho da classificação."""
    fig, ax = plt.subplots(figsize=(12, 8.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8.4); ax.axis("off")
    _caixa(ax, 6, 7.8, 3.4, 0.7, "METODOLOGIA MCT\n(Nogami e Villibor)", fs=10, negrito=True)
    # linha de distribuição
    ax.plot([2, 10], [7.1, 7.1], color=CINZA, lw=1.0)
    ax.plot([6, 6], [7.45, 7.1], color=CINZA, lw=1.0)
    for x in (2, 10):
        _seta(ax, x, 7.1, x, 6.85)
    _seta(ax, 6, 7.1, 6, 6.85, destaque=True)
    # grupos
    _caixa(ax, 2, 6.45, 3.3, 0.8, "Grupo Mini-CBR\ne ensaios associados", negrito=True)
    _caixa(ax, 6, 6.45, 3.3, 0.8, "Grupo Mini-MCV\n(classificação)", destaque=True, negrito=True)
    _caixa(ax, 10, 6.45, 3.3, 0.8, "Ensaios in situ", negrito=True)
    # grupo Mini-CBR
    _seta(ax, 2, 6.05, 2, 5.55)
    _caixa(ax, 2, 5.15, 3.3, 0.8, "Compactação Mini-Proctor\nDNIT 228/2023-ME")
    _seta(ax, 2, 4.75, 2, 4.25)
    _caixa(ax, 2, 3.85, 3.3, 0.8, "Mini-CBR e expansão\nDNIT 254/2023-ME")
    _seta(ax, 2, 3.45, 2, 2.95)
    _caixa(ax, 2, 2.3, 3.3, 1.3, "Ensaios associados*\ncontração · infiltrabilidade\npermeabilidade\npenetração da imprimadura")
    # grupo Mini-MCV (classificação)
    _seta(ax, 6, 6.05, 6, 5.55, destaque=True)
    _caixa(ax, 6, 5.15, 3.3, 0.8, "Compactação Mini-MCV\nDNIT 258/2023-ME → c′ e d′", destaque=True)
    _seta(ax, 6, 4.75, 6, 4.25, destaque=True)
    _caixa(ax, 6, 3.85, 3.3, 0.8, "Perda de massa por imersão\nDNIT 258/2023-ME → Pi′", destaque=True)
    _seta(ax, 6, 3.45, 6, 2.95, destaque=True)
    _caixa(ax, 6, 2.55, 3.3, 0.8, "c′ · d′ · Pi′\ne′ = ∛(Pi′/100 + 20/d′)", destaque=True)
    _seta(ax, 6, 2.15, 6, 1.65, destaque=True)
    _caixa(ax, 6, 1.1, 3.3, 1.1, "CLASSIFICAÇÃO MCT\nDNIT 259/2023-CLA (finos)\nDNIT 444/2023-CLA (G-MCT, grossos)",
           destaque=True, negrito=True, fs=10)
    # in situ
    for y, txt in ((5.15, "Mini-CBR com\npenetrômetro*"), (4.05, "Mini-CBR de campo —\nprocedimento dinâmico*"),
                   (2.95, "Mini-MCV —\ncontrole de umidade*")):
        _caixa(ax, 10.55, y, 2.5, 0.85, txt, fs=9.6)
    ax.plot([9.1, 9.1], [6.05, 2.95], color=CINZA, lw=1.0)
    for y in (5.15, 4.05, 2.95):
        _seta(ax, 9.1, y, 9.4, y)
    ax.plot([9.1, 10], [6.05, 6.05], color=CINZA, lw=1.0)
    # legenda
    ax.add_patch(FancyBboxPatch((0.35, 0.25), 0.35, 0.25, boxstyle="round,pad=0.01", fc=AZUL_CLARO, ec=AZUL, lw=2))
    ax.text(0.85, 0.37, "ensaios e etapas que fornecem a classificação MCT", fontsize=9.5, va="center")
    ax.text(0.35, -0.05, "* procedimentos da metodologia MCT sem norma DNIT vigente (lista IPR de 24/09/2026)",
            fontsize=9, color=CINZA)
    fig.tight_layout()
    return fig


def fluxograma():
    st.markdown("A metodologia MCT reúne três grupos de ensaios em equipamento miniatura. **Só o grupo do "
                "Mini-MCV fornece a classificação**: a compactação Mini-MCV e a perda de massa por imersão "
                "(ambas da DNIT 258/2023-ME) dão c′, d′ e Pi′, e a DNIT 259/2023-CLA classifica. O Mini-Proctor "
                "(DNIT 228/2023-ME) molda os corpos de prova do Mini-CBR e dos ensaios associados, que "
                "caracterizam o comportamento, mas não entram no ábaco.")
    st.pyplot(plot_fluxograma(), use_container_width=True)
    st.markdown("""
| Ensaio | Norma vigente | O que fornece |
|---|---|---|
| Compactação Mini-MCV | DNIT 258/2023-ME | curvas de deformabilidade (Mini-MCV, **c′**) e de compactação (**d′**) |
| Perda de massa por imersão | DNIT 258/2023-ME | **Pi** de cada CP → **Pi′** |
| Classificação | DNIT 259/2023-CLA · DNIT 444/2023-CLA | **grupo MCT** (finos) · **G-MCT** (grossos) |
| Compactação Mini-Proctor | DNIT 228/2023-ME | curva de compactação miniatura (umidade ótima, MEAS máxima) |
| Mini-CBR e expansão | DNIT 254/2023-ME | capacidade de suporte e expansão |
""")
    st.caption(FONTES)


ETAPAS_SOBRE = [
    ("Introdução", introducao, ["mct", "normas", "lateritico", "saprolitico", "grupos"]),
    ("Fundamentos", fundamentos, ["lateritico", "saprolitico", "mini_mcv", "c", "e", "abaco"]),
    ("Fluxograma de ensaios", fluxograma, ["mini_proctor", "mini_cbr", "mini_mcv", "pi", "g_mct"],
     {"largura_total": True}),
]
