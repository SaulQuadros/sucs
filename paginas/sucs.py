# paginas/sucs.py
# Página SUCS — Manual de Pavimentação DNIT (IPR-719/2006).

import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from sucs_core import (classify_sucs, classify_dataframe, cu_cc, line_a,
                       LINE_A_SLOPE, HATCH_IP, LL_LH, EXEMPLOS)
from estado import aviso_desatualizado, keep, lote, salvar_resultado, ultimo_resultado
from projeto import get_meta
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


st.title("Classificador SUCS — DNIT")
st.caption("Critérios da Tabela 5, Figura 17 e fluxograma de identificação do Manual de Pavimentação DNIT "
           "(IPR-719/2006, versão corrigida com a Errata 1). Granulometria: DNIT 459/2025-ME; "
           "limites: DNER-ME 122/94 (LL) e DNER-ME 082/94 (LP).")

meta = get_meta()
projeto, tecnico, amostra = meta["projeto"], meta["tecnico"], meta["amostra"]

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
    pct_retido_200 = st.number_input("% retido na peneira #200", 0.0, 100.0, step=0.1,
                                     **keep("sucs_ret200", 0.0))
    fines = 100.0 - pct_retido_200
    coarse = pct_retido_200 > 50.0
    st.caption(f"% de finos (passando na #200) = {fines:.1f}% → granulação {'grossa' if coarse else 'fina'}")
    if coarse:
        pct_pedregulho = st.number_input("% de pedregulho (> #4) na fração graúda", 0.0, 100.0, step=0.1,
                                         **keep("sucs_pedregulho", 0.0))
        pct_areia = 100.0 - pct_pedregulho
        st.caption(f"% de areia (entre #4 e #200) na fração graúda = {pct_areia:.1f}%")
    else:
        pct_pedregulho = pct_areia = 0.0

    allowed_grad = coarse and fines <= 12.0
    Cu = Cc = D10 = D30 = D60 = None
    if allowed_grad:
        st.markdown("**Graduação (W/P)**")
        modo_grad = st.radio("Informar", ["D10, D30, D60 (mm)", "Cu e Cc", "Não informar"], horizontal=True,
                             **keep("sucs_modo_grad", "D10, D30, D60 (mm)"))
        if modo_grad.startswith("D10"):
            c1, c2, c3 = st.columns(3)
            D10 = c1.number_input("D10", 0.0, 100.0, step=0.01, format="%.3f", **keep("sucs_d10", 0.10))
            D30 = c2.number_input("D30", 0.0, 100.0, step=0.01, format="%.3f", **keep("sucs_d30", 0.30))
            D60 = c3.number_input("D60", 0.0, 100.0, step=0.01, format="%.3f", **keep("sucs_d60", 0.90))
            _cu, _cc = cu_cc(D10, D30, D60)
            if _cu is not None:
                st.caption(f"Cu = {_cu:.2f} ; Cc = {_cc:.2f}")
        elif modo_grad == "Cu e Cc":
            c1, c2 = st.columns(2)
            Cu = c1.number_input("Cu", 0.0, 1000.0, step=0.1, **keep("sucs_cu", 6.0))
            Cc = c2.number_input("Cc", 0.0, 1000.0, step=0.01, **keep("sucs_cc", 1.5))
    elif coarse:
        st.caption("Finos > 12%: a graduação (W/P) não entra na classificação.")

with col2:
    st.subheader("Plasticidade (Atterberg)")
    NP = st.checkbox("Não plástico (NP)", **keep("sucs_np", False))
    LL = st.number_input("Limite de Liquidez (LL)", 0.0, 300.0, step=0.1, disabled=NP, **keep("sucs_ll", 0.0))
    LP = st.number_input("Limite de Plasticidade (LP)", 0.0, 300.0, step=0.1, disabled=NP, **keep("sucs_lp", 0.0))
    IP = 0.0 if NP else LL - LP
    st.metric("IP = LL − LP", "NP" if NP else f"{IP:.2f}")
    st.pyplot(plot_plasticidade(LL, IP, NP))

with col3:
    st.subheader("Matéria orgânica")
    organico = st.checkbox("Evidência orgânica (cor escura, odor, queda do LL após secagem em estufa)",
                           disabled=coarse,
                           help="Aplica-se a solos finos abaixo da linha A (OL se LL ≤ 50, OH se LL > 50).",
                           **keep("sucs_organico", False))
    turfa = st.checkbox("Altamente orgânico, fibroso (turfa)", help="Classifica como PT.",
                        **keep("sucs_turfa", False))

entrada = {"pct_retido_200": pct_retido_200,
           "pct_pedregulho_coarse": pct_pedregulho, "pct_areia_coarse": pct_areia,
           "LL": None if NP else LL, "LP": None if NP else LP, "NP": NP,
           "Cu": Cu, "Cc": Cc, "D10": D10, "D30": D30, "D60": D60,
           "organico": organico and not coarse, "turfa": turfa}

st.divider()
if st.button("Classificar (formulário acima)", type="primary"):
    try:
        salvar_resultado("sucs", entrada, classify_sucs({**entrada, **meta}))
    except ValueError as e:
        salvar_resultado("sucs", entrada, str(e))

ultimo = ultimo_resultado("sucs", entrada)
if ultimo:
    saida, desatualizado = ultimo
    if desatualizado:
        aviso_desatualizado()
    if isinstance(saida, str):
        st.error(saida)
    else:
        grupo, relatorio = saida
        st.success(f"**Grupo SUCS:** {grupo}")
        st.text(relatorio)
        st.download_button("Baixar relatório (.txt)", relatorio, file_name=f"sucs_{amostra or 'amostra'}.txt")


def _processar_lote(df):
    res = classify_dataframe(df)
    if "grupo_esperado" in res.columns:
        res.insert(1, "confere", res["grupo_esperado"].astype(str) == res["grupo"].astype(str))
    return res


st.divider()
st.subheader("Classificação em lote (CSV / Excel)")
st.caption("Colunas: " + ", ".join(TEMPLATE_COLS[2:]) + ". Use a planilha-modelo acima como base.")
uploaded = st.file_uploader("Envie o arquivo", type=["csv", "xlsx"], key="sucs_lote")
try:
    r = lote("sucs", uploaded, _processar_lote)
    if r:
        res, nome, reaproveitado = r
        if reaproveitado:
            st.caption(f"Último lote processado: **{nome}**")
        st.dataframe(res, use_container_width=True)
        st.download_button("Baixar resultados (CSV)", res.to_csv(index=False).encode("utf-8"),
                           file_name="resultados_sucs.csv", mime="text/csv")
except Exception as e:
    st.error(str(e))
