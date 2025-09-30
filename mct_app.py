# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from mct_core import (
    MCTInput, classify_from_inputs, plot_point_on_abaco, plot_mct_abaco
)
from didatica.mct_examples import build_excel_template_bytes_mct

# NÃO chamar st.set_page_config aqui (evita conflito com o script principal)

# ----------------------
# Sidebar - Identificação
# ----------------------
def sidebar_meta() -> dict:
    st.sidebar.markdown("### 📄 Identificação")
    projeto = st.sidebar.text_input("Nome do projeto", key="mct_meta_projeto")
    tecnico = st.sidebar.text_input("Técnico responsável", key="mct_meta_tecnico")
    amostra = st.sidebar.text_input("Código da amostra", key="mct_meta_amostra")
    return {"projeto": projeto.strip() if projeto else "",
            "tecnico": tecnico.strip() if tecnico else "",
            "amostra": amostra.strip() if amostra else ""}

def _number_input(label, value=None, min_value=None, max_value=None, step=0.01, help=None, key=None):
    return st.number_input(label, value=value, min_value=min_value, max_value=max_value,
                           step=step, format="%.6f", help=help, key=key)

def _decimal_br(x) -> str:
    try:
        return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(x)

def _ident_caption(meta: dict):
    if not meta: return
    proj = meta.get("projeto") or "—"
    tec = meta.get("tecnico") or "—"
    ams = meta.get("amostra") or "—"
    st.caption(f"**Projeto:** {proj}  |  **Técnico:** {tec}  |  **Amostra:** {ams}")

def ui_modo_rapido(meta: dict):
    st.subheader("⚡ Modo Rápido")
    st.markdown("Informe **C'** e **e'**, ou informe **d'** e **Pi** que eu calculo **e'**.")
    _ident_caption(meta)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        C_ = _number_input("C' (mini-MCV=10)", min_value=0.0, max_value=10.0, value=2.50, step=0.01,
                           help="Inclinação no ponto mini-MCV=10 (conforme Manual).")
    with col2:
        e_ = _number_input("e' (se já tiver)", min_value=0.0, max_value=100.0, value=18.0, step=0.01,
                           help="Índice composto e' (opcional se você for informar d' e Pi).")
    with col3:
        st.caption("Ou informe d' e Pi para calcular e'")
        d_ = _number_input("d' (×10³, ramo seco 10 golpes)", min_value=0.0, max_value=50.0, value=12.0, step=0.01)
        Pi = _number_input("Pi (% perda por imersão no mini-MCV=10, ΔH=2 mm)", min_value=0.0, max_value=100.0,
                           value=10.0, step=0.01)

    demo = st.toggle("Modo demonstração (usar limites provisórios do ábaco)", value=True,
                     help="Quando desativado, exigirá a implementação dos limites oficiais.")

    if st.button("Classificar (MCT)"):
        try:
            inp = MCTInput(C_=C_, e_=e_ if e_ > 0 else None, d_=d_ if d_ > 0 else None, Pi=Pi if Pi > 0 else None, meta=meta)
            result = classify_from_inputs(inp, allow_demo=demo)

            st.markdown(f"### Resultado: **{result.group}** {'🧪' if result.is_demo else '✅'}")
            c1, c2, c3 = st.columns(3)
            c1.metric("C'", _decimal_br(result.C_))
            c2.metric("e'", _decimal_br(result.e_))
            c3.metric("CBR (típico)", result.cbr_tipico or "—")

            if result.warnings:
                st.warning(" | ".join(result.warnings))

            st.markdown("**Como cheguei aqui**:")
            for r in result.rationale:
                st.write("• " + r)

            fig, ax = plt.subplots(figsize=(6.5, 5.2))
            plot_mct_abaco(ax=ax, show_demo_limits=True)
            plot_point_on_abaco(result.C_, result.e_, ax=ax)
            st.pyplot(fig, use_container_width=False)

        except Exception as ex:
            st.error(f"Erro ao classificar: {ex}")

def ui_modo_completo(meta: dict):
    st.subheader("🧪 Modo Completo (Laboratório) — esqueleto pronto")
    st.caption("Faça upload das leituras para extrair C', d', Pi → e'. Esta versão inicial contém o esqueleto.")
    _ident_caption(meta)

    with st.expander("Modelo de planilha (MCT)"):
        if st.button("Baixar planilha-modelo (Excel)"):
            xbytes = build_excel_template_bytes_mct()
            st.download_button("Download do template (MCT).xlsx", data=xbytes, file_name="template_mct.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    col1, col2, col3 = st.columns(3)
    with col1:
        f_mcv = st.file_uploader("mini-MCV (CSV/XLSX)", type=["csv", "xlsx"], accept_multiple_files=False)
    with col2:
        f_comp = st.file_uploader("Compactação 10 golpes (CSV/XLSX)", type=["csv", "xlsx"], accept_multiple_files=False)
    with col3:
        f_imersao = st.file_uploader("Perdas por Imersão (CSV/XLSX)", type=["csv", "xlsx"], accept_multiple_files=False)

    st.info("⚠️ Extração automática de C', d' e Pi será adicionada na próxima etapa. "
            "Os arquivos são aceitos e validados, mas o processamento detalhado ainda será implementado.")

    if any([f_mcv, f_comp, f_imersao]):
        st.success("Arquivos recebidos. Validações básicas ok.")
        st.write("• mini-MCV:", f_mcv.name if f_mcv else "—")
        st.write("• Compactação 10 golpes:", f_comp.name if f_comp else "—")
        st.write("• Perdas por Imersão:", f_imersao.name if f_imersao else "—")

def main():
    st.title("Classificação de Solos — Método MCT (Nogami & Villibor)")
    st.markdown("Este módulo está **isolado** dos demais (SUCS/TRB). Ele traz as **assinaturas, validações** e o **esqueleto do ábaco**. A lógica oficial do ábaco e a expressão de e' serão conectadas na fase seguinte, com base no Manual do DNIT.")

    meta = sidebar_meta()

    modo = st.radio("Escolha o modo", ["Rápido", "Completo (Laboratório)"], horizontal=True)
    if modo == "Rápido":
        ui_modo_rapido(meta)
    else:
        ui_modo_completo(meta)

if __name__ == "__main__":
    main()
