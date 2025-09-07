
# pages/trb_app.py
import io
import pandas as pd
import streamlit as st
from trb_core import classify_trb, classify_dataframe_trb, GROUP_DESC, ig_label

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

def build_excel_template_bytes_trb():
    import pandas as pd
    exemplos = [
        ("A-1-a", "Granular de alta qualidade", dict(P10=45,P40=25,P200=10,LL=30,IP=4,NP=False)),
        ("A-1-b", "Granular bom",               dict(P10=70,P40=45,P200=20,LL=35,IP=6,NP=False)),
        ("A-3",   "Areia fina NP",              dict(P10=95,P40=80,P200=8, LL=0, IP=0,NP=True)),
        ("A-2-4", "Granular c/ silte (LL≤40)",  dict(P10=85,P40=60,P200=30,LL=35,IP=8,NP=False)),
        ("A-2-5", "Granular c/ silte (LL>40)",  dict(P10=85,P40=60,P200=30,LL=45,IP=8,NP=False)),
        ("A-2-6", "Granular c/ argila (LL≤40)", dict(P10=85,P40=60,P200=30,LL=35,IP=12,NP=False)),
        ("A-2-7", "Granular c/ argila (LL>40)", dict(P10=85,P40=60,P200=30,LL=45,IP=12,NP=False)),
        ("A-4",   "Silte LL baixo",             dict(P10=80,P40=60,P200=50,LL=35,IP=8,NP=False)),
        ("A-5",   "Silte LL alto",              dict(P10=80,P40=60,P200=50,LL=50,IP=8,NP=False)),
        ("A-6",   "Argila LL baixo",            dict(P10=80,P40=60,P200=50,LL=35,IP=12,NP=False)),
        ("A-7-5", "Argila LL alto menos plást.",dict(P10=90,P40=70,P200=60,LL=55,IP=20,NP=False)),
        ("A-7-6", "Argila LL alto mais plást.", dict(P10=90,P40=70,P200=60,LL=55,IP=30,NP=False)),
    ]
    rows = []
    for g, desc, params in exemplos:
        row = dict(Grupo_esperado=g, descricao_sintetica=desc); row.update(params); rows.append(row)
    df = pd.DataFrame(rows)
    mem = io.BytesIO()
    try:
        with pd.ExcelWriter(mem, engine="xlsxwriter") as xw:
            df.to_excel(xw, index=False, sheet_name="modelo_trb")
    except Exception:
        with pd.ExcelWriter(mem, engine="openpyxl") as xw:
            df.to_excel(xw, index=False, sheet_name="modelo_trb")
    mem.seek(0)
    return mem

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
            st.success(f"Grupo TRB: **{r.group}**  |  IG = **{r.ig}** ({ig_label(r.ig)})")
            st.caption(f"Interpretação TRB: {GROUP_DESC.get(r.group, '—')}")
            st.text_area("Relatório (texto)", r.relatorio, height=220)
            mem = io.BytesIO(r.relatorio.encode("utf-8"))
            st.download_button("Baixar relatório (.txt)", data=mem, file_name="relatorio_trb.txt", mime="text/plain")
        except Exception as e:
            st.error(str(e))

with col2:
    st.subheader("Lote (CSV / Excel)")
    modelo_csv = pd.DataFrame([
        {"P10": 60, "P40": 45, "P200": 8,  "LL": 28, "IP": 0,  "NP": True},
        {"P10": 80, "P40": 50, "P200": 20, "LL": 35, "IP": 6,  "NP": False},
        {"P10": 90, "P40": 70, "P200": 30, "LL": 42, "IP": 12, "NP": False},
        {"P10": 95, "P40": 80, "P200": 50, "LL": 38, "IP": 12, "NP": False},
    ])
    csv_buf = io.BytesIO(); modelo_csv.to_csv(csv_buf, index=False, encoding="utf-8"); csv_buf.seek(0)
    st.download_button("Baixar planilha-modelo (CSV)", data=csv_buf, file_name="modelo_trb.csv", mime="text/csv")

    xlsx_buf = build_excel_template_bytes_trb()
    st.download_button("Baixar planilha-modelo (Excel)", data=xlsx_buf, file_name="modelo_trb.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    up = st.file_uploader("Enviar CSV (ou Excel .xlsx)", type=["csv","xlsx"])
    if up is not None:
        try:
            name = up.name.lower()
            if name.endswith(".xlsx"):
                df = pd.read_excel(up)
            else:
                head = up.getvalue()[:4096].decode('utf-8-sig', errors='ignore')
                sep = ';' if head.count(';') > head.count(',') else ','
                up.seek(0)
                df = pd.read_csv(up, sep=sep, encoding='utf-8-sig')

            if 'NP' in df.columns:
                df['NP'] = df['NP'].astype(str).str.strip().str.lower().map({
                    'true': True, 'false': False, '1': True, '0': False,
                    'sim': True, 'não': False, 'nao': False, 'np': True
                }).fillna(False)

            out = classify_dataframe_trb(df)
            st.dataframe(out, use_container_width=True)

            out_csv = io.BytesIO(); out.to_csv(out_csv, index=False, encoding='utf-8'); out_csv.seek(0)
            st.download_button("Baixar resultados (CSV)", data=out_csv, file_name="resultado_trb.csv", mime="text/csv")
        except Exception as e:
            st.error(str(e))
