
# pages/trb_app.py
import io
import pandas as pd
import streamlit as st
from trb_core import classify_trb, classify_dataframe_trb

st.set_page_config(page_title="Classificação TRB (HRB/AASHTO)")
st.title("Classificação TRB (antigo HRB/AASHTO) + Índice de Grupo (IG)")

with st.expander("ℹ️ Ajuda rápida", expanded=False):
    st.markdown(
        "- O grupo é determinado por **eliminação da esquerda para a direita** na tabela TRB.\n"
        "- O **IG (0–20)** mede a “qualidade” do subleito (0 melhor). Não decide o grupo; apenas qualifica.\n"
        "- Campos em % devem obedecer: **#200 ≤ #40 ≤ #10 ≤ 100**, e todos em 0–100.\n"
        "- Use **NP** quando o solo for **não-plástico** (IP=0); nesse caso o LL é ignorado."
    )

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Entrada (Formulário)")
    p10  = st.number_input("% passante #10", 0.0, 100.0, step=0.1)
    p40  = st.number_input("% passante #40", 0.0, 100.0, step=0.1)
    p200 = st.number_input("% passante #200", 0.0, 100.0, step=0.1)
    np_  = st.checkbox("IP é NP (não-plástico)?", value=False)
    ll   = st.number_input("LL (Limite de Liquidez)", 0.0, 200.0, step=0.1, disabled=np_)
    ip   = 0.0 if np_ else st.number_input("IP (Índice de Plasticidade)", 0.0, 200.0, step=0.1)

    if st.button("Classificar (TRB)"):
        try:
            r = classify_trb(p10, p40, p200, ll, ip, is_np=np_)
            st.success(f"Grupo TRB: **{r.group}**  |  IG = **{r.ig}**")
            for item in r.rationale:
                st.caption(f"• {item}")
        except Exception as e:
            st.error(str(e))

with col2:
    st.subheader("Lote (CSV)")
    modelo = pd.DataFrame([
        {"P10": 60, "P40": 45, "P200": 8,  "LL": 28, "IP": 0,  "NP": True},
        {"P10": 80, "P40": 50, "P200": 20, "LL": 35, "IP": 6,  "NP": False},
        {"P10": 90, "P40": 70, "P200": 30, "LL": 42, "IP": 12, "NP": False},
        {"P10": 95, "P40": 80, "P200": 50, "LL": 38, "IP": 12, "NP": False},
    ])
    mem = io.BytesIO(); modelo.to_csv(mem, index=False, encoding="utf-8"); mem.seek(0)
    st.download_button("Baixar planilha-modelo (CSV)", data=mem, file_name="modelo_trb.csv", mime="text/csv")

    up = st.file_uploader("Enviar CSV (modelo acima)", type=["csv"])
    if up is not None:
        head = up.getvalue()[:4096].decode('utf-8-sig', errors='ignore')
        sep = ';' if head.count(';') > head.count(',') else ','
        up.seek(0)
        df = pd.read_csv(up, sep=sep, encoding='utf-8-sig')
        if 'NP' in df.columns:
            df['NP'] = df['NP'].astype(str).str.strip().str.lower().map({
                'true': True, 'false': False, '1': True, '0': False,
                'sim': True, 'não': False, 'nao': False, 'np': True
            }).fillna(False)
        try:
            out = classify_dataframe_trb(df)
            st.dataframe(out, use_container_width=True)
            csv_out = io.BytesIO(); out.to_csv(csv_out, index=False, encoding='utf-8'); csv_out.seek(0)
            st.download_button("Baixar resultados (CSV)", data=csv_out, file_name="resultado_trb.csv", mime="text/csv")
        except Exception as e:
            st.error(str(e))
