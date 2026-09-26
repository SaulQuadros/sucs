# projeto.py
# Identificação do projeto na barra lateral, compartilhada por todas as páginas do app.
import streamlit as st

from estado import keep

CAMPOS = (("projeto", "Nome do projeto"), ("tecnico", "Técnico responsável"), ("amostra", "Código da amostra"))


def render_sidebar() -> None:
    """Desenhada pelo roteador (sucs_app.py) a cada execução; os valores persistem ao trocar de página."""
    with st.sidebar:
        st.header("Projeto")
        for chave, rotulo in CAMPOS:
            st.text_input(rotulo, **keep(f"meta_{chave}", ""))


def get_meta() -> dict:
    return {chave: (st.session_state.get(f"meta_{chave}") or "").strip() for chave, _ in CAMPOS}
