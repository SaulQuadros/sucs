# paginas/trb.py
# Classificação TRB (HRB/AASHTO) — Tabela 4 do Manual de Pavimentação DNIT (IPR-719/2006).
import io

import pandas as pd
import streamlit as st

from didatica.generator_pdf import generate_random_sucs_pdf
from trb_core import classify_trb, classify_dataframe_trb, GROUP_DESC, ig_label, EXEMPLOS
from trb_defs import cbr_for_trb, sucs_provavel
from estado import aviso_desatualizado, keep, lote, salvar_resultado, ultimo_resultado
from projeto import get_meta
from xlsx_utils import resolve_xlsx_engine, to_xlsx_bytes

META_COLS = ["Nome do projeto", "Técnico responsável", "Código da amostra"]


def template_df() -> pd.DataFrame:
    rows = [{**{c: "" for c in META_COLS}, "Grupo_esperado": g, "descricao_sintetica": d, **p}
            for g, d, p in EXEMPLOS]
    return pd.DataFrame(rows, columns=META_COLS + ["Grupo_esperado", "descricao_sintetica",
                                                   "P10", "P40", "P200", "LL", "LP", "NP"])


def build_results_xlsx_trb(df: pd.DataFrame) -> bytes:
    preferred = META_COLS + ["P10", "P40", "P200", "LL", "LP", "IP_calc", "Grupo_TRB", "IG", "Subleito",
                             "Materiais constituintes", "CBR provável (%)", "aviso_ig", "relatorio"]
    df = df[[c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]]
    if resolve_xlsx_engine() != "xlsxwriter":
        return to_xlsx_bytes(df, "Resultados")
    mem = io.BytesIO()
    with pd.ExcelWriter(mem, engine="xlsxwriter") as xw:
        df.to_excel(xw, index=False, sheet_name="Resultados")
        wb, ws = xw.book, xw.sheets["Resultados"]
        wrap = wb.add_format({"text_wrap": True, "valign": "top"})
        hdr = wb.add_format({"bold": True, "bg_color": "#F2F2F2"})
        ws.set_row(0, None, hdr)
        widths = {"relatorio": 96, "aviso_ig": 48, "Materiais constituintes": 26, "CBR provável (%)": 16}
        for i, col in enumerate(df.columns):
            ws.set_column(i, i, widths.get(col, 14), wrap if col in ("relatorio", "aviso_ig") else None)
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)
        if "Grupo_TRB" in df.columns and "IG" in df.columns:
            ok = df[df["Grupo_TRB"] != "ERRO"]
            res = (ok.groupby("Grupo_TRB")["IG"].agg(["count", "min", "max", "mean"])
                   .rename(columns={"count": "n", "min": "IG_min", "max": "IG_max", "mean": "IG_médio"}))
            res.to_excel(xw, index=True, sheet_name="Resumo")
    return mem.getvalue()


st.title("Classificador TRB — DNIT")
st.caption("Quadro de classificação (Tabela 4), Índice de Grupo e Tabelas 11 e 14 do Manual de Pavimentação "
           "DNIT (IPR-719/2006, versão corrigida com a Errata 1). Granulometria: DNIT 459/2025-ME.")

with st.expander("ℹ️ Ajuda rápida", expanded=False):
    st.markdown("\n".join([
        "- O grupo é determinado por **eliminação da esquerda para a direita** no quadro TRB.",
        "- **IG = 0,2a + 0,005ac + 0,01bd** (0 a 20); **não decide** o grupo, apenas qualifica o subleito (0 melhor).",
        "- Limites inteiros do quadro com valores decimais: LL > 40 conta como “41 mín.”, IP > 10 como “11 mín.”.",
        "- Campos em %: **#200 ≤ #40 ≤ #10 ≤ 100**.",
        "- Marque **NP** para solo não plástico (IP = NP). O LL, se houver, continua entrando no IG.",
    ]))

st.subheader("Planilha-modelo (TRB)")
_modelo = template_df()
c_a, c_b = st.columns(2)
c_a.download_button("Baixar planilha-modelo (CSV)", data=_modelo.to_csv(index=False).encode("utf-8"),
                    file_name="modelo_trb.csv", mime="text/csv", key="dl_model_trb_csv_help")
try:
    c_b.download_button("Baixar planilha-modelo (Excel)", data=to_xlsx_bytes(_modelo, "modelo_trb"),
                        file_name="modelo_trb.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_model_trb_xlsx_help")
except Exception as _e:
    st.caption("Não foi possível gerar o modelo em Excel: " + str(_e))

meta = get_meta()
projeto, tecnico, amostra = meta["projeto"], meta["tecnico"], meta["amostra"]

st.subheader("Granulometria (% passante)")
cg1, cg2, cg3 = st.columns(3)
p10 = cg1.number_input("% passante #10", 0.0, 100.0, step=0.1, **keep("trb_p10", 0.0))
p40 = cg2.number_input("% passante #40", 0.0, 100.0, step=0.1, **keep("trb_p40", 0.0))
p200 = cg3.number_input("% passante #200", 0.0, 100.0, step=0.1, **keep("trb_p200", 0.0))

st.subheader("Plasticidade (Atterberg)")
cp1, cp2, cp3 = st.columns(3)
np_ = cp1.checkbox("Não plástico (NP)", **keep("trb_np", False))
ll = cp2.number_input("LL (Limite de Liquidez)", 0.0, 300.0, step=0.1, **keep("trb_ll", 0.0))
lp = cp3.number_input("LP (Limite de Plasticidade)", 0.0, 300.0, step=0.1, disabled=np_, **keep("trb_lp", 0.0))
st.caption("IP = **NP**" if np_ else f"IP calculado (LL − LP) = **{ll - lp:.2f}**")

entrada = {"p10": p10, "p40": p40, "p200": p200, "ll": ll, "lp": 0.0 if np_ else lp, "np": np_}
if st.button("Classificar (TRB)", type="primary"):
    try:
        salvar_resultado("trb", entrada, classify_trb(entrada["p10"], entrada["p40"], entrada["p200"],
                                                      entrada["ll"], entrada["lp"], is_np=np_))
    except Exception as e:
        salvar_resultado("trb", entrada, str(e))

ultimo = ultimo_resultado("trb", entrada)
if ultimo:
    r, desatualizado = ultimo
    if desatualizado:
        aviso_desatualizado()
    if isinstance(r, str):
        st.error(r)
    else:
        st.success(f"Grupo TRB: **{r.group}**  |  IG = **{r.ig}** ({ig_label(r.ig)})")
        st.caption(f"Interpretação TRB: {GROUP_DESC.get(r.group, '—')}")
        st.caption(f"Comportamento como subleito: **{r.subleito}**  |  "
                   f"CBR provável (Tabela 14): **{cbr_for_trb(r.group)}%**")
        sp = sucs_provavel(r.group)
        st.caption(f"SUCS mais provável (Tabela 11): **{sp[0]}**; possível: {sp[1]}")
        if r.aviso_ig:
            st.warning(r.aviso_ig)
        rel = (f"Nome do projeto: {projeto or '-'}\nTécnico responsável: {tecnico or '-'}\n"
               f"Código da amostra: {amostra or '-'}\n\n") + r.relatorio
        st.text(rel)
        st.download_button("Baixar relatório (.txt)", data=rel.encode("utf-8"),
                           file_name=f"TRB_{(amostra or 'amostra').replace(' ', '_')}.txt", mime="text/plain")


def _processar_lote(df):
    if "NP" in df.columns:
        df["NP"] = df["NP"].astype(str).str.strip().str.lower().map({
            "true": True, "false": False, "1": True, "0": False, "1.0": True, "0.0": False,
            "sim": True, "não": False, "nao": False, "np": True}).fillna(False)
    else:
        df["NP"] = False
    for col, val in zip(META_COLS, (projeto, tecnico, amostra)):
        if col not in df.columns and val:
            df[col] = val
    out = classify_dataframe_trb(df)
    if "Grupo_esperado" in out.columns:
        out.insert(0, "confere", out["Grupo_esperado"].astype(str) == out["Grupo_TRB"].astype(str))
    return out


st.divider()
st.subheader("Lote (CSV / Excel)")
up = st.file_uploader("Enviar CSV (ou Excel .xlsx)", type=["csv", "xlsx"], key="trb_lote")
try:
    res_lote = lote("trb", up, _processar_lote)
    if res_lote:
        out, nome, reaproveitado = res_lote
        if reaproveitado:
            st.caption(f"Último lote processado: **{nome}**")
        st.dataframe(out, use_container_width=True)
        st.download_button("Baixar resultados (XLSX)", data=build_results_xlsx_trb(out),
                           file_name="resultado_trb.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Baixar resultados (CSV)", data=out.to_csv(index=False).encode("utf-8"),
                           file_name="resultado_trb.csv", mime="text/csv")
except Exception as e:
    st.error(str(e))

# === Didática: ficha de exercício (PDF) ===
with st.sidebar.expander("🧪 Gerar ficha de exercício (PDF)", expanded=False):
    st.caption("Gera uma ficha aleatória com granulometria e limites (sem a classe), "
               "para exercício de classificação TRB e SUCS.")
    if st.button("Gerar ficha (PDF)", key="didatica_btn_pdf"):
        try:
            st.session_state["__ficha_pdf__"] = generate_random_sucs_pdf()
        except Exception as _e:
            st.caption(f"Não foi possível gerar a ficha: {_e}")
    if "__ficha_pdf__" in st.session_state:
        _pdf_bytes, _meta = st.session_state["__ficha_pdf__"]
        st.download_button(f"Baixar ficha {_meta['amostra']} (PDF)", data=_pdf_bytes,
                           file_name=f"Ficha_{_meta['amostra']}.pdf", mime="application/pdf",
                           key="didatica_dl_pdf")
