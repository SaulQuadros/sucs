# sucs_app.py
# Ponto de entrada do app (main file no Streamlit Community Cloud) e menu de navegação.
# Cada chave do dicionário é um menu da barra superior; novos módulos entram como novas chaves.
import streamlit as st

from projeto import render_sidebar

st.set_page_config(page_title="SoilClass — DNIT", layout="wide")

MENUS = {
    "Classificação de Solos": [
        st.Page("paginas/sucs.py", title="SUCS", url_path="sucs", default=True),
        st.Page("paginas/trb.py", title="TRB", url_path="trb_app"),
        st.Page("paginas/mct.py", title="MCT", url_path="mct_app"),
    ],
}

pagina = st.navigation(MENUS, position="top")
render_sidebar()
pagina.run()
