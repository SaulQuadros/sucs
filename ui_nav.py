# ui/nav.py
import streamlit as st

def nav_selector(current: str = "SUCS"):
    """Renderiza um seletor na sidebar para navegar entre SUCS e TRB.
    current: página atual ("SUCS" ou "TRB") para marcar o rádio corretamente.
    """
    st.sidebar.subheader("Classificador")
    options = ["SUCS", "TRB"]
    idx = options.index(current) if current in options else 0

    def _go():
        sel = st.session_state.get("_nav_sel")
        if sel == current:
            return
        try:
            if sel == "SUCS":
                st.switch_page("streamlit_app.py")         # Home/SUCS
            elif sel == "TRB":
                st.switch_page("pages/trb_app.py")         # Página TRB
        except Exception:
            # fallback: apenas exibe links se switch_page não existir na versão do Streamlit
            st.sidebar.page_link("streamlit_app.py", label="Ir para SUCS")
            st.sidebar.page_link("pages/trb_app.py", label="Ir para TRB")

    st.sidebar.radio("Escolha o classificador:", options, index=idx, key="_nav_sel", on_change=_go)
