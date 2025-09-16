# -*- coding: utf-8 -*-
"""
Habilita o bloco "🧪 Gerar Ficha (PDF)" no sidebar da página SUCS.
Uso: acrescente apenas esta linha no topo do seu arquivo SUCS (qualquer variante):
    import didatica.enable_in_sucs  # ativa o gerador de ficha (PDF)
"""
import streamlit as st
from didatica.generator_pdf import generate_random_sucs_pdf

try:
    with st.sidebar.expander("🧪 Gerar Ficha (PDF)", expanded=False):
        st.caption("Gera uma ficha aleatória (SUCS) com curva granulométrica. Uma por vez.")
        if st.button("Gerar ficha (PDF)", key="didatica_btn_pdf_sucs"):
            _pdf_bytes, _meta = generate_random_sucs_pdf()
            st.success("Ficha gerada. Faça o download abaixo.")
            st.download_button("Baixar Ficha (PDF)",
                               data=_pdf_bytes,
                               file_name=f"Ficha_{_meta['amostra']}.pdf",
                               mime="application/pdf",
                               key="didatica_dl_pdf_sucs")
except Exception as _e:
    st.sidebar.caption(f"Não foi possível habilitar o gerador de ficha: {_e}")
