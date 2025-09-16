# pages/trb_app.py
import io
import pandas as pd
import streamlit as st
from trb_core import classify_trb, classify_dataframe_trb, GROUP_DESC, ig_label

# --- Excel engine resolver (XLSX) ---
def _resolve_xlsx_engine():
    """Return a working engine string for pandas.ExcelWriter (prefer xlsxwriter)."""
    try:
        import xlsxwriter  # type: ignore
        return "xlsxwriter"
    except Exception:
        try:
            import openpyxl  # type: ignore
            return "openpyxl"
        except Exception:
            return None


def build_excel_template_bytes_trb():
    exemplos = [
        ("A-1-a", "Granular de alta qualidade", dict(P10=45, P40=25, P200=10, LL=30, LP=26, NP=False)),
        ("A-1-b", "Granular bom",               dict(P10=70, P40=45, P200=20, LL=35, LP=29, NP=False)),
        ("A-3",   "Areia fina NP",              dict(P10=95, P40=80, P200=8,  LL=0,  LP=0,  NP=True)),
        ("A-2-4", "Granular c/ silte (LL≤40)",  dict(P10=85, P40=60, P200=30, LL=35, LP=27, NP=False)),
        ("A-2-5", "Granular c/ silte (LL>40)",  dict(P10=85, P40=60, P200=30, LL=45, LP=37, NP=False)),
        ("A-2-6", "Granular c/ argila (LL≤40)", dict(P10=85, P40=60, P200=30, LL=35, LP=23, NP=False)),
        ("A-2-7", "Granular c/ argila (LL>40)", dict(P10=85, P40=60, P200=30, LL=45, LP=33, NP=False)),
        ("A-4",   "Silte LL baixo",             dict(P10=80, P40=60, P200=50, LL=35, LP=27, NP=False)),
        ("A-5",   "Silte LL alto",              dict(P10=80, P40=60, P200=50, LL=50, LP=40, NP=False)),
        ("A-6",   "Argila LL baixo",            dict(P10=80, P40=60, P200=50, LL=35, LP=22, NP=False)),
        ("A-7-5", "Argila LL alto menos plást.",dict(P10=90, P40=70, P200=60, LL=55, LP=35, NP=False)),
        ("A-7-6", "Argila LL alto mais plást.", dict(P10=90, P40=70, P200=60, LL=55, LP=25, NP=False)),
    ]
    rows = []
    for g, desc, params in exemplos:
        row = dict(**{"Nome do projeto":""}, **{"Técnico responsável":""}, **{"Código da amostra":""},
                   Grupo_esperado=g, descricao_sintetica=desc)
        row.update(params)
        rows.append(row)
    df = pd.DataFrame(rows, columns=[
        "Nome do projeto","Técnico responsável","Código da amostra",
        "Grupo_esperado","descricao_sintetica","P10","P40","P200","LL","LP","NP"
    ])
    mem = io.BytesIO()
    try:
        with pd.ExcelWriter(mem, engine=_resolve_xlsx_engine()) as xw:
            df.to_excel(xw, index=False, sheet_name="modelo_trb")
    except Exception:
        with pd.ExcelWriter(mem, engine=_resolve_xlsx_engine()) as xw:
            df.to_excel(xw, index=False, sheet_name="modelo_trb")
    mem.seek(0)
    return mem




st.set_page_config(page_title="Classificador TRB - DNIT")
st.title("Classificador TRB - DNIT")
with st.expander("ℹ️ Ajuda rápida", expanded=False):
    st.markdown(
        "\n".join([
            "- O grupo é determinado por **eliminação da esquerda para a direita** na tabela TRB (HRB/AASHTO).",
            "- O **IG (0–20)** mede a “qualidade” do subleito (0 melhor). **Não decide** o grupo; apenas qualifica.",
            "- Campos em % devem obedecer: **#200 ≤ #40 ≤ #10 ≤ 100**, e todos em 0–100.",
            "- Use **NP** quando o solo for **não-plástico** (IP = 0); nesse caso o LL e o LP são ignorados.",
        ])
    )
    st.divider()
    st.subheader("Planilha-modelo (TRB)")
    # CSV modelo
    _modelo_csv = pd.DataFrame([
        {"Nome do projeto": "", "Técnico responsável": "", "Código da amostra": "",
         "P10": 60, "P40": 45, "P200": 8,  "LL": 28, "LP": 24, "NP": True},
        {"Nome do projeto": "", "Técnico responsável": "", "Código da amostra": "",
         "P10": 80, "P40": 50, "P200": 20, "LL": 35, "LP": 29, "NP": False},
        {"Nome do projeto": "", "Técnico responsável": "", "Código da amostra": "",
         "P10": 90, "P40": 70, "P200": 30, "LL": 42, "LP": 30, "NP": False},
        {"Nome do projeto": "", "Técnico responsável": "", "Código da amostra": "",
         "P10": 95, "P40": 80, "P200": 50, "LL": 38, "LP": 26, "NP": False},
    ])
    _csv_buf = io.BytesIO(); _modelo_csv.to_csv(_csv_buf, index=False, encoding="utf-8"); _csv_buf.seek(0)
    st.download_button("Baixar planilha-modelo (CSV)", data=_csv_buf, file_name="modelo_trb.csv",
                       mime="text/csv", key="dl_model_trb_csv_help")
    # Excel modelo
    try:
        _xlsx_buf = build_excel_template_bytes_trb()
        st.download_button("Baixar planilha-modelo (Excel)", data=_xlsx_buf, file_name="modelo_trb.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_model_trb_xlsx_help")
    except Exception as _e:
        st.caption("Não foi possível gerar o modelo em Excel: " + str(_e))

# === Barra lateral (padrão SUCS) ===
with st.sidebar:
    st.header("Projeto")
    projeto = st.text_input("Nome do projeto")
    tecnico = st.text_input("Técnico responsável")
    amostra = st.text_input("Código da amostra")



col1, col2 = st.columns([2, 1])
def build_results_xlsx_trb(df: pd.DataFrame) -> io.BytesIO:
    preferred = ["Nome do projeto","Técnico responsável","Código da amostra",
                 "P10","P40","P200","LL","LP","IP_calc","Grupo_TRB","IG","Subleito","Materiais constituintes","aviso_ig","relatorio"]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    df = df[cols]
    mem = io.BytesIO()
    try:
        with pd.ExcelWriter(mem, engine=_resolve_xlsx_engine()) as xw:
            df.to_excel(xw, index=False, sheet_name="Resultados")
            wb = xw.book
            ws = xw.sheets["Resultados"]
            wrap = wb.add_format({"text_wrap": True, "valign": "top"})
            hdr  = wb.add_format({"bold": True, "bg_color": "#F2F2F2"})
            warn = wb.add_format({"bg_color": "#FFF3CD"})
            ws.set_row(0, None, hdr)
            width_map = {
                "Nome do projeto":20, "Técnico responsável":22, "Código da amostra":18,
                "P10":10, "P40":10, "P200":10, "LL":8, "LP":8, "IP_calc":9,
                "Grupo_TRB":12, "IG":6, "Subleito":18, "Materiais constituintes":26, "aviso_ig":48, "relatorio":96
            }
            for idx, col in enumerate(df.columns, start=1):
                w = width_map.get(col, 12)
                ws.set_column(idx-1, idx-1, w, wrap if col in ("relatorio","aviso_ig") else None)
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(df), len(df.columns)-1)
            if "aviso_ig" in df.columns:
                col_idx = df.columns.get_loc("aviso_ig")
                ws.conditional_format(1, col_idx, len(df), col_idx, {
                    "type": "text", "criteria": "not containing", "value": "", "format": warn
                })
            if "Grupo_TRB" in df.columns and "IG" in df.columns:
                res = (
                    df.groupby("Grupo_TRB")["IG"]
                      .agg(["count","min","max","mean"])
                      .sort_index()
                      .rename(columns={"count":"n","min":"IG_min","max":"IG_max","mean":"IG_médio"})
                )
                res.to_excel(xw, index=True, sheet_name="Resumo")
                ws2 = xw.sheets["Resumo"]
                ws2.set_row(0, None, hdr)
                ws2.set_column(0, 0, 14)
                for c in range(1, 5):
                    ws2.set_column(c, c, 12)
    except Exception:
        with pd.ExcelWriter(mem, engine=_resolve_xlsx_engine()) as xw:
            df.to_excel(xw, index=False, sheet_name="Resultados")
    mem.seek(0)
    return mem

with col1:
    st.subheader("Granulometria")
    cg1, cg2, cg3 = st.columns(3)
    with cg1:
        p10  = st.number_input("% passante #10", 0.0, 100.0, step=0.1)
    with cg2:
        p40  = st.number_input("% passante #40", 0.0, 100.0, step=0.1)
    with cg3:
        p200 = st.number_input("% passante #200", 0.0, 100.0, step=0.1)

    st.subheader("Plasticidade (Atterberg)")
    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        np_  = st.checkbox("IP é NP (não-plástico)?", value=False)
    with cp2:
        ll   = st.number_input("LL (Limite de Liquidez)", 0.0, 200.0, step=0.1, disabled=np_)
    with cp3:
        lp   = st.number_input("LP (Limite de Plasticidade)", 0.0, 200.0, step=0.1, disabled=np_)
    ip_calc = 0.0 if np_ else max(0.0, ll - lp)
    st.caption(f"IP calculado (LL − LP) = **{ip_calc:.2f}**")

    if st.button("Classificar (TRB)"):
        try:
            r = classify_trb(p10, p40, p200, ll, lp, is_np=np_)
            st.success(f"Grupo TRB: **{r.group}**  |  IG = **{r.ig}** ({ig_label(r.ig)})")
            st.caption(f"Interpretação TRB: {GROUP_DESC.get(r.group, '—')}")
            st.caption(f"Comportamento como subleito: **{r.subleito}**")
            if r.aviso_ig:
                st.warning(r.aviso_ig)
            # Cabeçalho de identificação (padrão SUCS)
            meta_hdr = (f"Nome do projeto: {projeto or '-'}\n"
                        f"Técnico responsável: {tecnico or '-'}\n"
                        f"Código da amostra: {amostra or '-'}\n\n")
            rel = meta_hdr + r.relatorio
            st.text(rel)
            mem = io.BytesIO(rel.encode("utf-8"))
            fname = f"TRB_{(amostra or 'amostra').replace(' ', '_')}.txt"
            st.download_button("Baixar relatório (.txt)", data=mem, file_name=fname, mime="text/plain")
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.subheader("Lote (CSV / Excel)")
    
    
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
    
            # Normaliza NP e injeta metadados da sidebar se não vierem
            if 'NP' in df.columns:
                df['NP'] = df['NP'].astype(str).str.strip().str.lower().map({
                    'true': True, 'false': False, '1': True, '0': False,
                    'sim': True, 'não': False, 'nao': False, 'np': True
                }).fillna(False)
    
            for col, val in {"Nome do projeto": projeto, "Técnico responsável": tecnico, "Código da amostra": amostra}.items():
                if col not in df.columns and val:
                    df[col] = val
    
            out = classify_dataframe_trb(df)
            st.dataframe(out, use_container_width=True)
    
            xlsx_out = build_results_xlsx_trb(out)
            st.download_button("Baixar resultados (XLSX)", data=xlsx_out,
                               file_name="resultado_trb.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
            out_csv = io.BytesIO(); out.to_csv(out_csv, index=False, encoding="utf-8"); out_csv.seek(0)
            st.download_button("Baixar resultados (CSV)", data=out_csv, file_name="resultado_trb.csv", mime="text/csv")
        except Exception as e:
            st.error(str(e))
