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


st.set_page_config(page_title="Classificação TRB (HRB/AASHTO)")
st.title("Classificação TRB (antigo HRB/AASHTO) + Índice de Grupo (IG)")

# === Barra lateral (padrão SUCS) ===
with st.sidebar:
    st.header("Projeto")
    projeto = st.text_input("Nome do projeto")
    tecnico = st.text_input("Técnico responsável")
    amostra = st.text_input("Código da amostra")
    st.divider()
    st.subheader("Planilha‑modelo (TRB)")
    # CSV modelo