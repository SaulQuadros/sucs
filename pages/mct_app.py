# -*- coding: utf-8 -*-
# pages/mct_app.py
# Classificação MCT de solos finos tropicais — DNIT 259/2023-CLA (ensaios: DNIT 258/2023-ME).
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from didatica.mct_examples import build_excel_template_bytes_mct, template_df_mct
from mct_core import (MCTInput, NORMA_CLA, NORMA_ME, PROPRIEDADES, GRUPOS, build_report,
                      classify_dataframe_mct, classify_from_inputs, plot_mct_abaco, plot_point_on_abaco)

# NÃO chamar st.set_page_config aqui (evita conflito com o script principal)

PROP_LABELS = {"granulometria": "Granulometria típica", "mini_cbr_sem_imersao": "Mini-CBR sem imersão",
               "perda_suporte_imersao": "Perda de suporte por imersão", "expansao": "Expansão",
               "contracao": "Contração", "permeabilidade": "Permeabilidade", "plasticidade": "Plasticidade"}


def sidebar_meta() -> dict:
    st.sidebar.markdown("### 📄 Identificação")
    return {"projeto": st.sidebar.text_input("Nome do projeto", key="mct_meta_projeto").strip(),
            "tecnico": st.sidebar.text_input("Técnico responsável", key="mct_meta_tecnico").strip(),
            "amostra": st.sidebar.text_input("Código da amostra", key="mct_meta_amostra").strip()}


def _br(x, nd=3) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _tri(label: str, key: str):
    v = st.radio(label, ["Não verificado", "Sim", "Não"], horizontal=True, key=key)
    return None if v == "Não verificado" else v == "Sim"


def ui_individual(meta: dict):
    st.subheader("Classificação de uma amostra")
    c1, c2, c3 = st.columns(3)
    with c1:
        c_ = st.number_input("c' — coeficiente de argilosidade", min_value=0.0, max_value=5.0, value=1.20,
                             step=0.01, format="%.2f",
                             help="Inclinação da curva de deformabilidade com Mini-MCV = 10 (DNIT 258/2023-ME).")
        modo_e = st.radio("Índice e'", ["Calcular por d' e Pi'", "Informar e' diretamente"], key="mct_modo_e")
    e_ = d_ = pi_ref = pi_10 = pi_15 = af_10 = None
    serie = "simplificada"
    with c2:
        if modo_e.startswith("Informar"):
            e_ = st.number_input("e' — índice de laterização", min_value=0.0, max_value=5.0, value=1.00,
                                 step=0.01, format="%.3f")
        else:
            d_ = st.number_input("d' — inclinação do ramo seco", min_value=0.1, max_value=2000.0, value=50.0,
                                 step=0.5, help="Parte retilínea mais inclinada do ramo seco da curva de "
                                                "compactação (kg/m³ por % de umidade).")
            serie = st.radio("Série do ensaio Mini-MCV", ["simplificada", "Parsons"], horizontal=True,
                             help="d' da curva de 10 golpes (simplificada) ou de 12 golpes (Parsons).")
    with c3:
        if not modo_e.startswith("Informar"):
            modo_pi = st.radio("Pi'", ["Pela altura final (AF)", "Informar Pi' diretamente"], key="mct_modo_pi")
            if modo_pi.startswith("Informar"):
                pi_ref = st.number_input("Pi' (%)", min_value=0.0, max_value=1000.0, value=20.0, step=1.0)
            else:
                af_10 = st.number_input("AF no Mini-MCV = 10 (mm)", min_value=0.0, max_value=100.0, value=47.0,
                                        step=0.1, help="≥ 48 mm: baixa densidade (Pi' a Mini-MCV 10); "
                                                       "< 48 mm: alta densidade (Pi' a Mini-MCV 15).")
                pi_10 = st.number_input("Pi no Mini-MCV = 10 (%)", min_value=0.0, max_value=1000.0,
                                        value=80.0, step=1.0)
                pi_15 = st.number_input("Pi no Mini-MCV = 15 (%)", min_value=0.0, max_value=1000.0,
                                        value=20.0, step=1.0)

    with st.expander("Ponto próximo da fronteira laterítico × não laterítico (item 5.1 c da norma)"):
        st.caption("Quando o ponto fica próximo da linha L|N, a norma considera o solo laterítico só se "
                   "atender aos dois critérios abaixo.")
        crit1 = _tri("Curva Pi × Mini-MCV com inclinação negativa entre Mini-MCV 10 e 15?", "mct_crit1")
        crit2 = _tri("Curva Mini-MCV × umidade de compactação com concavidade para cima?", "mct_crit2")
        tol = st.slider("Faixa considerada “próxima” (Δe')", 0.0, 0.15, 0.05, 0.01)

    if st.button("Classificar (MCT)", type="primary"):
        try:
            res = classify_from_inputs(MCTInput(c_=c_, d_=d_, pi_ref=pi_ref, pi_10=pi_10, pi_15=pi_15,
                                                af_10=af_10, e_=e_, serie=serie,
                                                pi_inclinacao_negativa=crit1, mcv_concavidade_para_cima=crit2,
                                                meta=meta), tolerancia_LN=tol)
        except Exception as ex:
            st.error(f"Erro ao classificar: {ex}")
            return
        p = res.props
        st.markdown(f"### Resultado: **{res.group}** — {res.classe}, {p['nome'].lower()}")
        m1, m2, m3 = st.columns(3)
        m1.metric("c'", _br(res.c_, 2))
        m2.metric("e'", _br(res.e_))
        m3.metric("Pi'", "—" if res.pi_ref is None else f"{_br(res.pi_ref, 1)}%")
        for w in res.warnings:
            st.warning(w)
        cA, cB = st.columns([1.1, 1])
        with cA:
            fig, ax = plt.subplots(figsize=(7, 5))
            plot_mct_abaco(ax=ax)
            plot_point_on_abaco(res.c_, res.e_, ax=ax)
            st.pyplot(fig, use_container_width=True)
        with cB:
            st.markdown("**Como cheguei aqui**")
            for r in res.rationale:
                st.write("• " + r)
            st.markdown(f"**Propriedades típicas** (Anexo B, {NORMA_CLA})")
            st.table(pd.DataFrame({"Propriedade": [PROP_LABELS[k] for k in PROP_LABELS],
                                   "Valor": [p[k] for k in PROP_LABELS]}).set_index("Propriedade"))
        st.markdown(f"**Descrição (Anexo C):** {res.descricao}")
        st.caption(f"Correlação pedológica/geológica: {res.correlacao} · Classificação resiliente "
                   f"(Tabela 15, Manual IPR-719): {res.resiliente[0]} — {res.resiliente[1]}")
        rel = build_report(res, meta)
        st.download_button("Baixar relatório (.txt)", data=rel.encode("utf-8"),
                           file_name=f"MCT_{(meta.get('amostra') or 'amostra').replace(' ', '_')}.txt",
                           mime="text/plain")


def ui_lote():
    st.subheader("Classificação em lote (CSV / Excel)")
    st.caption("Colunas: **c**, **d** e **Pi_ref**, ou **Pi_10**, **Pi_15** e **AF_10** (mm) para a norma escolher "
               "Pi'; opcionalmente **e** (e' já calculado) e **serie**. A planilha-modelo traz um exemplo por grupo.")
    c1, c2 = st.columns(2)
    try:
        c1.download_button("Baixar planilha-modelo (Excel)", data=build_excel_template_bytes_mct(),
                           file_name="modelo_mct.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as ex:
        c1.caption(f"Não foi possível gerar o Excel: {ex}")
    c2.download_button("Baixar planilha-modelo (CSV)", data=template_df_mct().to_csv(index=False).encode("utf-8"),
                       file_name="modelo_mct.csv", mime="text/csv")
    up = st.file_uploader("Enviar arquivo", type=["csv", "xlsx"], key="mct_lote")
    if up is None:
        return
    try:
        if up.name.lower().endswith(".xlsx"):
            df = pd.read_excel(up)
        else:
            head = up.getvalue()[:4096].decode("utf-8-sig", errors="ignore")
            sep = ";" if head.count(";") > head.count(",") else ","
            up.seek(0)
            df = pd.read_csv(up, sep=sep, encoding="utf-8-sig")
        out = classify_dataframe_mct(df)
        if "grupo_esperado" in out.columns:
            out.insert(0, "confere", out["grupo_esperado"].astype(str) == out["Grupo_MCT"].astype(str))
        st.dataframe(out, use_container_width=True)
        ok = out[out["Grupo_MCT"] != "ERRO"]
        if len(ok):
            fig, ax = plt.subplots(figsize=(7, 5))
            plot_mct_abaco(ax=ax)
            for _, r in ok.iterrows():
                c = r.get("c", r.get("C"))
                lbl = str(r.get("amostra") or r["Grupo_MCT"])
                plot_point_on_abaco(float(c), float(r["e_calc"]), ax=ax, label=lbl)
            st.pyplot(fig, use_container_width=False)
        st.download_button("Baixar resultados (CSV)", data=out.to_csv(index=False).encode("utf-8"),
                           file_name="resultado_mct.csv", mime="text/csv")
    except Exception as ex:
        st.error(str(ex))


def main():
    st.title("Classificação MCT — solos finos tropicais")
    st.caption(f"Conforme a norma **{NORMA_CLA}** (Figura A1, Anexos B e C), com ensaios Mini-MCV e perda de "
               f"massa por imersão pela **{NORMA_ME}**. e' = ∛(Pi'/100 + 20/d').")
    meta = sidebar_meta()
    modo = st.radio("Modo", ["Uma amostra", "Lote (CSV/Excel)", "Quadro dos grupos"], horizontal=True)
    if modo == "Uma amostra":
        ui_individual(meta)
    elif modo.startswith("Lote"):
        ui_lote()
    else:
        st.markdown(f"**Anexo B — Propriedades típicas dos grupos** ({NORMA_CLA})")
        st.dataframe(pd.DataFrame({g: {**{"Classe": PROPRIEDADES[g]["classe"]},
                                       **{PROP_LABELS[k]: PROPRIEDADES[g][k] for k in PROP_LABELS}}
                                   for g in GRUPOS}), use_container_width=True)
        fig, _ = plot_mct_abaco()
        st.pyplot(fig, use_container_width=False)
    st.info("Próxima etapa: modo laboratório, que calculará c', d' e Pi a partir das leituras do ensaio "
            "Mini-MCV (DNIT 258/2023-ME).")


main()
