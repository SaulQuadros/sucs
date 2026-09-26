# sucs_app.py
# App Streamlit para classificar solos pelo SUCS — Manual de Pavimentação DNIT (IPR-719/2006).

import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from sucs_core import (classify_sucs, classify_dataframe, cu_cc, line_a,
                       LINE_A_SLOPE, HATCH_IP, LL_LH, EXEMPLOS)
from xlsx_utils import to_xlsx_bytes

TEMPLATE_COLS = ["grupo_esperado", "descricao_sintetica", "projeto", "tecnico", "amostra",
                 "pct_retido_200", "pct_pedregulho_coarse", "pct_areia_coarse",
                 "LL", "LP", "NP", "Cu", "Cc", "D10", "D30", "D60", "organico", "turfa"]



def template_df() -> pd.DataFrame:
    rows = []
    for g, d, p in EXEMPLOS:
        rec = {c: None for c in TEMPLATE_COLS}
        rec.update(grupo_esperado=g, descricao_sintetica=d, projeto="Demo", tecnico="Equipe", amostra=g,
                   NP=False, organico=False, turfa=False)
        rec.update(p)
        rows.append(rec)
    return pd.DataFrame(rows, columns=TEMPLATE_COLS)


def plot_plasticidade(LL: float, IP: float, NP: bool):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    x_max = max(100.0, LL + 10)
    ll_4 = 20 + HATCH_IP[0] / LINE_A_SLOPE   # linha A cruza IP = 4
    ll_7 = 20 + HATCH_IP[1] / LINE_A_SLOPE   # linha A cruza IP = 7
    ax.plot([ll_4, x_max], [HATCH_IP[0], line_a(x_max)], color="black", lw=1.4)
    ax.text(x_max * 0.82, line_a(x_max * 0.82) + 2, "Linha A", rotation=33, fontsize=9)
    u_4, u_7 = 8 + HATCH_IP[0] / 0.9, 8 + HATCH_IP[1] / 0.9  # limite esquerdo (linha U: IP = 0,9·(LL − 8))
    ax.fill([u_4, ll_4, ll_7, u_7], [4, 4, 7, 7], hatch="///",
            fill=False, edgecolor="gray", lw=0.8)
    ax.text(12, 5.1, "ML-CL", fontsize=8)
    ax.axvline(LL_LH, color="black", lw=1.0, ls="--")
    for txt, x, y in [("CL", 38, 22), ("CH", 70, 45), ("ML ou OL", 30, 1.5), ("MH ou OH", 72, 18)]:
        ax.text(x, y, txt, fontsize=9, fontweight="bold")
    if not NP:
        ax.scatter([LL], [IP], color="tab:red", zorder=5)
        ax.annotate(f"({LL:.0f}; {IP:.0f})", (LL, IP), xytext=(6, 6), textcoords="offset points", fontsize=8)
    ax.set_xlim(0, x_max); ax.set_ylim(0, max(60.0, IP + 10, line_a(x_max) + 5))
    ax.set_xlabel("Limite de liquidez LL (%)"); ax.set_ylabel("Índice de plasticidade IP (%)")
    ax.set_title("Gráfico de plasticidade (Figura 17, Manual IPR-719)", fontsize=10)
    ax.grid(True, ls=":", alpha=0.5)
    return fig


st.set_page_config(page_title="Classificador SUCS (DNIT)", layout="wide")
st.title("Classificador SUCS — DNIT")
st.caption("Critérios da Tabela 5, Figura 17 e fluxograma de identificação do Manual de Pavimentação DNIT "
           "(IPR-719/2006, versão corrigida com a Errata 1). Granulometria: DNIT 459/2025-ME; "
           "limites: DNER-ME 122/94 (LL) e DNER-ME 082/94 (LP).")

with st.sidebar:
    st.header("Projeto")
    projeto = st.text_input("Nome do projeto")
    tecnico = st.text_input("Técnico responsável")
    amostra = st.text_input("Código da amostra")

with st.expander("ℹ️ Ajuda rápida", expanded=False):
    st.markdown("\n".join([
        "- **Mais de 50% retido na #200** → granulação **grossa**; **50% ou mais passando** → **fina**.",
        "- Grossa: **G** quando 50% ou mais da fração graúda fica retida na #4; senão **S**.",
        "  - Finos **< 5%**: W/P por **Cu** e **Cc** (pedregulho: Cu ≥ 4; areia: Cu ≥ 6; ambos 1 ≤ Cc ≤ 3).",
        "  - Finos **5–12%**: caso limite, **símbolo duplo** (ex.: SW-SM, GP-GC).",
        "  - Finos **> 12%**: GM/SM abaixo da linha A; GC/SC acima; **GM-GC/SM-SC** na zona hachurada.",
        "- Fina: **linha A** IP = 0,73·(LL − 20); **L** se LL ≤ 50, **H** se LL > 50.",
        "  - Zona hachurada (4 ≤ IP ≤ 7, acima da linha A) → **ML-CL**.",
        "  - Orgânicos (cor, odor, queda do LL após secagem em estufa) abaixo da linha A → **OL/OH**; turfa → **PT**.",
    ]))
    st.divider()
    st.subheader("Planilha-modelo (SUCS)")
    _df_modelo = template_df()
    try:
        st.download_button("Baixar planilha-modelo (Excel)", data=to_xlsx_bytes(_df_modelo, "exemplos"),
                           file_name="SUCS_todos_os_grupos.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_model_sucs_xlsx_main")
    except Exception as _e:
        st.caption("Não foi possível gerar o modelo em Excel: " + str(_e))
    st.download_button("Baixar planilha-modelo (CSV)", data=_df_modelo.to_csv(index=False).encode("utf-8"),
                       file_name="SUCS_todos_os_grupos.csv", mime="text/csv", key="dl_model_sucs_csv_main")

col1, col2, col3 = st.columns([1.2, 1.2, 1])

with col1:
    st.subheader("Granulometria")
    pct_retido_200 = st.number_input("% retido na peneira #200", 0.0, 100.0, step=0.1)
    fines = 100.0 - pct_retido_200
    coarse = pct_retido_200 > 50.0
    st.caption(f"% de finos (passando na #200) = {fines:.1f}% → granulação {'grossa' if coarse else 'fina'}")
    if coarse:
        pct_pedregulho = st.number_input("% de pedregulho (> #4) na fração graúda", 0.0, 100.0, step=0.1)
        pct_areia = 100.0 - pct_pedregulho
        st.caption(f"% de areia (entre #4 e #200) na fração graúda = {pct_areia:.1f}%")
    else:
        pct_pedregulho = pct_areia = 0.0

    allowed_grad = coarse and fines <= 12.0
    Cu = Cc = D10 = D30 = D60 = None
    if allowed_grad:
        st.markdown("**Graduação (W/P)**")
        modo_grad = st.radio("Informar", ["D10, D30, D60 (mm)", "Cu e Cc", "Não informar"], horizontal=True)
        if modo_grad.startswith("D10"):
            c1, c2, c3 = st.columns(3)
            D10 = c1.number_input("D10", 0.0, 100.0, value=0.10, step=0.01, format="%.3f")
            D30 = c2.number_input("D30", 0.0, 100.0, value=0.30, step=0.01, format="%.3f")
            D60 = c3.number_input("D60", 0.0, 100.0, value=0.90, step=0.01, format="%.3f")
            _cu, _cc = cu_cc(D10, D30, D60)
            if _cu is not None:
                st.caption(f"Cu = {_cu:.2f} ; Cc = {_cc:.2f}")
        elif modo_grad == "Cu e Cc":
            c1, c2 = st.columns(2)
            Cu = c1.number_input("Cu", 0.0, 1000.0, value=6.0, step=0.1)
            Cc = c2.number_input("Cc", 0.0, 1000.0, value=1.5, step=0.01)
    elif coarse:
        st.caption("Finos > 12%: a graduação (W/P) não entra na classificação.")

with col2:
    st.subheader("Plasticidade (Atterberg)")
    NP = st.checkbox("Não plástico (NP)")
    LL = st.number_input("Limite de Liquidez (LL)", 0.0, 300.0, step=0.1, disabled=NP)
    LP = st.number_input("Limite de Plasticidade (LP)", 0.0, 300.0, step=0.1, disabled=NP)
    IP = 0.0 if NP else LL - LP
    st.metric("IP = LL − LP", "NP" if NP else f"{IP:.2f}")
    st.pyplot(plot_plasticidade(LL, IP, NP))

with col3:
    st.subheader("Matéria orgânica")
    organico = st.checkbox("Evidência orgânica (cor escura, odor, queda do LL após secagem em estufa)",
                           disabled=coarse,
                           help="Aplica-se a solos finos abaixo da linha A (OL se LL ≤ 50, OH se LL > 50).")
    turfa = st.checkbox("Altamente orgânico, fibroso (turfa)", help="Classifica como PT.")

st.divider()
if st.button("Classificar (formulário acima)", type="primary"):
    data = {"projeto": projeto, "tecnico": tecnico, "amostra": amostra,
            "pct_retido_200": pct_retido_200,
            "pct_pedregulho_coarse": pct_pedregulho, "pct_areia_coarse": pct_areia,
            "LL": None if NP else LL, "LP": None if NP else LP, "NP": NP,
            "Cu": Cu, "Cc": Cc, "D10": D10, "D30": D30, "D60": D60,
            "organico": organico, "turfa": turfa}
    try:
        grupo, relatorio = classify_sucs(data)
        st.success(f"**Grupo SUCS:** {grupo}")
        st.text(relatorio)
        st.download_button("Baixar relatório (.txt)", relatorio, file_name=f"sucs_{amostra or 'amostra'}.txt")
    except ValueError as e:
        st.error(str(e))

st.divider()
st.subheader("Classificação em lote (CSV / Excel)")
st.caption("Colunas: " + ", ".join(TEMPLATE_COLS[2:]) + ". Use a planilha-modelo acima como base.")
uploaded = st.file_uploader("Envie o arquivo", type=["csv", "xlsx"])
if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded)
        else:
            head = uploaded.getvalue()[:4096].decode("utf-8-sig", errors="ignore")
            sep = ";" if head.count(";") > head.count(",") else ","
            uploaded.seek(0)
            df = pd.read_csv(uploaded, sep=sep, encoding="utf-8-sig")
        res = classify_dataframe(df)
        if "grupo_esperado" in res.columns:
            res.insert(1, "confere", res["grupo_esperado"].astype(str) == res["grupo"].astype(str))
        st.dataframe(res, use_container_width=True)
        st.download_button("Baixar resultados (CSV)", res.to_csv(index=False).encode("utf-8"),
                           file_name="resultados_sucs.csv", mime="text/csv")
    except Exception as e:
        st.error(str(e))
