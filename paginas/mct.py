# -*- coding: utf-8 -*-
# paginas/mct.py
# Classificação MCT de solos finos tropicais — DNIT 259/2023-CLA (ensaios: DNIT 258/2023-ME).
# Mesmo padrão das páginas SUCS e TRB: entradas em dois quadros → Classificar → resultado em destaque.
# A configuração da página (st.set_page_config) fica no roteador sucs_app.py.
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from didatica.mct_examples import build_excel_template_bytes_mct, template_df_mct
from estado import aviso_desatualizado, keep, lote, salvar_resultado, ultimo_resultado
from formato import fmt
from mct_core import (GRUPOS, NORMA_CLA, NORMA_ME, PROPRIEDADES, MCTInput, build_report,
                      classify_dataframe_mct, classify_from_inputs, compute_e_prime, pi_referencia,
                      plot_mct_abaco, plot_point_on_abaco)
from projeto import get_meta

PROP_LABELS = {"granulometria": "Granulometria típica", "mini_cbr_sem_imersao": "Mini-CBR sem imersão",
               "perda_suporte_imersao": "Perda de suporte por imersão", "expansao": "Expansão",
               "contracao": "Contração", "permeabilidade": "Permeabilidade", "plasticidade": "Plasticidade"}
CINZA = "<span style='color:gray;font-size:0.8rem'>{}</span>"


def cabecalho():
    c_tit, c_crit, c_ref = st.columns([5, 1.2, 1.5], vertical_alignment="bottom")
    c_tit.title("Classificação MCT")
    with c_crit.popover("Critérios", use_container_width=True):
        st.markdown("\n".join([
            "- Solos finos tropicais: fração que passa na peneira nº 10 (2 mm).",
            "- **Pi'**: altura final do CP no Mini-MCV 10 **≥ 48 mm** (baixa densidade) → Pi no Mini-MCV 10; "
            "**< 48 mm** (alta densidade) → Pi no Mini-MCV 15.",
            "- **e' = ∛(Pi'/100 + 20/d')**, com d' da curva de 10 golpes (série simplificada) ou 12 (Parsons).",
            "- Ábaco (Figura A1): vértices (0,27; 2,2), (0,45; 1,75), (0,59; 1,4), (0,70; 1,15), (1,7; 1,15) "
            "e vertical c' = 1,5. Abaixo da fronteira: lateríticos (L); acima: não lateríticos (N).",
            "- Perto da fronteira L|N: laterítico só se a curva Pi × Mini-MCV tiver inclinação negativa entre "
            "10 e 15 **e** a curva Mini-MCV × umidade tiver concavidade para cima (item 5.1 c).",
        ]))
    with c_ref.popover("Referências", use_container_width=True):
        st.markdown("\n".join([
            f"- {NORMA_CLA}: classificação de solos finos tropicais (Figura A1, Anexos B e C).",
            f"- {NORMA_ME}: ensaios Mini-MCV e perda de massa por imersão (c', d', Pi).",
            "- Manual de Pavimentação DNIT, IPR-719/2006: Tabela 15 (MCT × classificação resiliente).",
        ]))
    st.caption("Metodologia MCT (Miniatura, Compactado, Tropical) — comportamento laterítico ou não laterítico "
               "de solos finos tropicais.")


def _tri(label: str, key: str):
    v = st.radio(label, ["Não verificado", "Sim", "Não"], horizontal=True, **keep(key, "Não verificado"))
    return None if v == "Não verificado" else v == "Sim"


def quadro_mini_mcv():
    with st.container(border=True):
        st.markdown("**Ensaio Mini-MCV** — c' e d'")
        c_ = st.number_input("c' — coeficiente de argilosidade", min_value=0.0, max_value=5.0, step=0.01,
                             format="%.2f", placeholder="—",
                             help="Inclinação da curva de deformabilidade com Mini-MCV = 10 (DNIT 258/2023-ME).",
                             **keep("mct_c", None))
        modo_e = st.radio("Índice e'", ["Calcular por d' e Pi'", "Informar e' diretamente"], horizontal=True,
                          **keep("mct_modo_e", "Calcular por d' e Pi'"))
        e_ = d_ = None
        serie = "simplificada"
        if modo_e.startswith("Informar"):
            e_ = st.number_input("e' — índice de laterização", min_value=0.0, max_value=5.0, step=0.01,
                                 format="%.3f", placeholder="—", **keep("mct_e", None))
        else:
            cd, cs = st.columns([1, 1.2], vertical_alignment="bottom")
            d_ = cd.number_input("d' — ramo seco", min_value=0.1, max_value=2000.0, step=0.5, placeholder="—",
                                 help="Parte retilínea mais inclinada do ramo seco da curva de compactação "
                                      "(kg/m³ por % de umidade).", **keep("mct_d", None))
            serie = cs.radio("Série", ["simplificada", "Parsons"], horizontal=True,
                             help="d' da curva de 10 golpes (simplificada) ou de 12 golpes (Parsons).",
                             **keep("mct_serie", "simplificada"))
    return {"c_": c_, "e_": e_, "d_": d_, "serie": serie}, modo_e.startswith("Informar")


def quadro_imersao(e_direto: bool, d_):
    with st.container(border=True):
        st.markdown("**Perda de massa por imersão** — Pi'")
        pi = {"pi_ref": None, "pi_10": None, "pi_15": None, "af_10": None}
        if e_direto:
            st.caption("Não se aplica: e' informado diretamente.")
            return pi, None
        modo_pi = st.radio("Pi'", ["Pela altura final (AF)", "Informar Pi' diretamente"], horizontal=True,
                           label_visibility="collapsed", **keep("mct_modo_pi", "Pela altura final (AF)"))
        texto = None
        if modo_pi.startswith("Informar"):
            pi["pi_ref"] = st.number_input("Pi' (%)", min_value=0.0, max_value=1000.0, step=1.0, placeholder="—",
                                           **keep("mct_pi_ref", None))
            pi_val = pi["pi_ref"]
            if pi_val is not None:
                texto = f"Pi' = {fmt(pi_val)}% (informado)"
        else:
            pi["af_10"] = st.number_input("AF no Mini-MCV = 10 (mm)", min_value=0.0, max_value=100.0, step=0.1,
                                          placeholder="—", help="Altura final do corpo de prova.",
                                          **keep("mct_af10", None))
            c10, c15 = st.columns(2)
            pi["pi_10"] = c10.number_input("Pi no Mini-MCV 10 (%)", min_value=0.0, max_value=1000.0, step=1.0,
                                           placeholder="—", **keep("mct_pi10", None))
            pi["pi_15"] = c15.number_input("Pi no Mini-MCV 15 (%)", min_value=0.0, max_value=1000.0, step=1.0,
                                           placeholder="—", **keep("mct_pi15", None))
            pi_val = None
            if pi["af_10"] is not None:
                try:
                    pi_val, _, texto = pi_referencia(pi["pi_10"], pi["pi_15"], pi["af_10"])
                except ValueError as ex:
                    texto = str(ex)
        e_prev = None
        if pi_val is not None and d_:
            e_prev = compute_e_prime(d_, pi_val)
            texto = (texto + "  \n" if texto else "") + (
                f"e' = ∛({fmt(pi_val)}/100 + 20/{fmt(d_)}) = **{fmt(e_prev, 3)}**")
        elif pi_val is not None:
            texto += "  \nInforme d' para calcular e'."
        st.caption(texto or "Informe AF e os valores de Pi (ou Pi' diretamente).")
        return pi, e_prev


def mostrar_resultado(res, meta):
    p = res.props
    with st.container(border=True):
        ch, cc, ce = st.columns([2.4, 1, 1], vertical_alignment="center")
        ch.markdown(f"<div style='font-size:2.6rem;font-weight:700;line-height:1.1'>{res.group}</div>"
                    f"<div style='font-size:1.05rem'>{res.classe} · {p['nome'].lower()}</div>",
                    unsafe_allow_html=True)
        cc.metric("c'", fmt(res.c_, 2))
        ce.metric("e'", fmt(res.e_, 3))
        st.markdown(res.descricao)
        for w in res.warnings:
            st.warning(w)
        c_txt, c_graf = st.columns([1, 1.15], gap="large")
        with c_txt:
            st.markdown("**Como cheguei aqui**")
            st.markdown("\n".join(f"{i}. {r}" for i, r in enumerate(res.rationale, 1)))
            m1, m2 = st.columns(2)
            m1.markdown(f"**Correlação pedológica/geológica**  \n{res.correlacao}  \n"
                        + CINZA.format(f"Anexo C, {NORMA_CLA}"), unsafe_allow_html=True)
            m2.markdown(f"**Classe resiliente**  \n{res.resiliente[0]} — {res.resiliente[1]}  \n"
                        + CINZA.format("Tabela 15, Manual IPR-719"), unsafe_allow_html=True)
        with c_graf:
            fig, ax = plt.subplots(figsize=(6.4, 4.6))
            plot_mct_abaco(ax=ax)
            plot_point_on_abaco(res.c_, res.e_, ax=ax, label=res.group)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
        with st.expander(f"Propriedades típicas do grupo {res.group} (Anexo B, {NORMA_CLA})", expanded=True):
            st.table(pd.DataFrame({"Propriedade": list(PROP_LABELS.values()),
                                   "Valor": [p[k] for k in PROP_LABELS]}).set_index("Propriedade"))
        rel = build_report(res, meta)
        with st.expander("Relatório completo"):
            st.code(rel, language=None)
        st.download_button("Baixar relatório (.txt)", data=rel.encode("utf-8"),
                           file_name=f"MCT_{(meta.get('amostra') or 'amostra').replace(' ', '_')}.txt",
                           mime="text/plain")


def modo_amostra(meta):
    c_m, c_i = st.columns(2, gap="medium")
    with c_m:
        mcv, e_direto = quadro_mini_mcv()
    with c_i:
        pi, e_prev = quadro_imersao(e_direto, mcv["d_"])
    with st.expander("Ponto próximo da fronteira laterítico × não laterítico (item 5.1 c da norma)"):
        st.caption("Perto da linha L|N, a norma considera o solo laterítico só se atender aos dois critérios.")
        crit1 = _tri("Curva Pi × Mini-MCV com inclinação negativa entre Mini-MCV 10 e 15?", "mct_crit1")
        crit2 = _tri("Curva Mini-MCV × umidade de compactação com concavidade para cima?", "mct_crit2")
        tol = st.slider("Faixa considerada “próxima” (Δe')", 0.0, 0.15, step=0.01, **keep("mct_tol", 0.05))

    entrada = {**mcv, **pi, "pi_inclinacao_negativa": crit1, "mcv_concavidade_para_cima": crit2, "tol": tol}
    pronto = mcv["c_"] is not None and (mcv["e_"] is not None if e_direto else e_prev is not None)
    if st.button("Classificar", type="primary", disabled=not pronto,
                 help=None if pronto else "Informe c' e os dados para e' (d' e Pi', ou e' diretamente)."):
        dados = {k: v for k, v in entrada.items() if k != "tol"}
        try:
            salvar_resultado("mct", entrada, classify_from_inputs(MCTInput(**dados, meta=meta), tolerancia_LN=tol))
        except Exception as ex:
            salvar_resultado("mct", entrada, f"Erro ao classificar: {ex}")

    ultimo = ultimo_resultado("mct", entrada)
    if ultimo:
        res, desatualizado = ultimo
        if desatualizado:
            aviso_desatualizado()
        if isinstance(res, str):
            st.error(res)
        else:
            mostrar_resultado(res, meta)


def _processar_lote(df):
    out = classify_dataframe_mct(df)
    if "grupo_esperado" in out.columns:
        out.insert(0, "confere", out["grupo_esperado"].astype(str) == out["Grupo_MCT"].astype(str))
    return out


def modo_lote():
    st.markdown("Uma linha por amostra. Colunas: **c**, **d** e **Pi_ref**, ou **Pi_10**, **Pi_15** e **AF_10** (mm) "
                "para a norma escolher Pi'; opcionalmente **e** (e' já calculado) e **serie**.")
    c1, c2, _ = st.columns([1, 1, 2])
    try:
        c1.download_button("Planilha-modelo (Excel)", data=build_excel_template_bytes_mct(),
                           file_name="MCT_modelo.xlsx", use_container_width=True,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as ex:
        c1.caption(f"Excel indisponível: {ex}")
    c2.download_button("Planilha-modelo (CSV)", data=template_df_mct().to_csv(index=False).encode("utf-8"),
                       file_name="MCT_modelo.csv", mime="text/csv", use_container_width=True)
    up = st.file_uploader("Enviar planilha (CSV ou Excel)", type=["csv", "xlsx"], key="mct_lote")
    try:
        r_lote = lote("mct", up, _processar_lote)
        if not r_lote:
            return
        out, nome, reaproveitado = r_lote
        if reaproveitado:
            st.caption(f"Último lote processado: **{nome}**")
        st.dataframe(out, use_container_width=True)
        ok = out[out["Grupo_MCT"] != "ERRO"]
        c_g, c_d = st.columns([1.3, 1])
        if len(ok):
            fig, ax = plt.subplots(figsize=(7, 5))
            plot_mct_abaco(ax=ax)
            for _, r in ok.iterrows():
                c = r.get("c", r.get("C"))
                plot_point_on_abaco(float(c), float(r["e_calc"]), ax=ax, label=str(r.get("amostra") or r["Grupo_MCT"]))
            c_g.pyplot(fig, use_container_width=True)
        c_d.download_button("Baixar resultados (CSV)", data=out.to_csv(index=False).encode("utf-8"),
                            file_name="resultado_mct.csv", mime="text/csv")
    except Exception as ex:
        st.error(str(ex))


def modo_quadro():
    c_t, c_g = st.columns([1.4, 1], gap="large")
    with c_t:
        st.markdown(f"**Anexo B — Propriedades típicas dos grupos** ({NORMA_CLA})")
        st.dataframe(pd.DataFrame({g: {**{"Classe": PROPRIEDADES[g]["classe"]},
                                       **{PROP_LABELS[k]: PROPRIEDADES[g][k] for k in PROP_LABELS}}
                                   for g in GRUPOS}), use_container_width=True)
    with c_g:
        fig, _ = plot_mct_abaco()
        st.pyplot(fig, use_container_width=True)


cabecalho()
_meta = get_meta()
_modo = st.segmented_control("Modo", ["Uma amostra", "Lote (CSV/Excel)", "Quadro dos grupos"],
                             label_visibility="collapsed", required=True, **keep("mct_modo", "Uma amostra"))
if _modo == "Lote (CSV/Excel)":
    modo_lote()
elif _modo == "Quadro dos grupos":
    modo_quadro()
else:
    modo_amostra(_meta)
st.caption("Próxima etapa: modo laboratório, que calculará c', d' e Pi a partir das leituras do ensaio "
           "Mini-MCV (DNIT 258/2023-ME).")
