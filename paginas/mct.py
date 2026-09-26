# -*- coding: utf-8 -*-
# paginas/mct.py
# Classificação MCT de solos finos tropicais — DNIT 259/2023-CLA (ensaios: DNIT 258/2023-ME).
# Mesmo padrão das páginas SUCS e TRB: entradas em dois quadros → Classificar → resultado em destaque.
# A configuração da página (st.set_page_config) fica no roteador sucs_app.py.
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from didatica.ex_numerico_mct import CREDITO, ETAPAS
from didatica.glossario_mct import texto_markdown
from didatica.mct_examples import build_excel_template_bytes_mct, template_df_mct
from estado import (aviso_desatualizado, definir_editor, definir_valor, editor_persistente, keep, lote,
                    salvar_resultado, ultimo_resultado)
from formato import fmt
from mct_core import (GRUPOS, NORMA_CLA, NORMA_ME, PROPRIEDADES, MCTInput, build_report, tabela_anexo_b_html,
                      classify_dataframe_mct, classify_from_inputs, compute_e_prime, pi_referencia,
                      plot_mct_abaco, plot_point_on_abaco)
from mct_lab import (EXEMPLOS_LAB, SERIES, calcular, de_tabelas, numerico, para_tabelas, plot_af, plot_compactacao,
                     plot_deformabilidade, plot_pi, tabela_cps)
from projeto import get_meta
from xlsx_utils import resolve_xlsx_engine

PROP_LABELS = {"granulometria": "Granulometria típica", "mini_cbr_sem_imersao": "Mini-CBR sem imersão",
               "perda_suporte_imersao": "Perda de suporte por imersão", "expansao": "Expansão",
               "contracao": "Contração", "permeabilidade": "Permeabilidade", "plasticidade": "Plasticidade"}
CINZA = "<span style='color:gray;font-size:0.8rem'>{}</span>"


def cabecalho():
    c_tit, c_crit, c_ref = st.columns([4, 1.5, 1.8], vertical_alignment="bottom")
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


def _carregar_exemplo():
    serie, cps, fonte = EXEMPLOS_LAB[st.session_state["mct_lab_exemplo"]]()
    alturas, dados = para_tabelas(serie, cps)
    definir_editor("mct_lab_alturas", alturas)
    definir_editor("mct_lab_dados", dados)
    st.session_state["__copia__mct_lab_serie"] = serie
    st.session_state["__mct_lab_fonte"] = fonte
    st.session_state.pop("__resultado__mct_lab", None)


def _limpar_lab():
    serie = st.session_state.get("mct_lab_serie", "Parsons")
    golpes = SERIES[serie]
    definir_editor("mct_lab_alturas", numerico(pd.DataFrame({"golpes": golpes, **{f"CP{i}": [None] * len(golpes)
                                                                                    for i in range(1, 6)}})))
    definir_editor("mct_lab_dados", numerico(pd.DataFrame([{"CP": f"CP{i}", "hc (%)": None, "massa úmida (g)": 200.0,
                                                            "Md desprendida (g)": None, "Lex (mm)": 10.0, "Fc": 1.0,
                                                            "Pi direto (%)": None} for i in range(1, 6)])))
    st.session_state.pop("__mct_lab_fonte", None)
    st.session_state.pop("__resultado__mct_lab", None)


def _modelo_lab_xlsx() -> bytes:
    import io
    serie, cps, fonte = EXEMPLOS_LAB[next(iter(EXEMPLOS_LAB))]()
    alturas, dados = para_tabelas(serie, cps)
    info = pd.DataFrame({"Instruções": [
        "Aba 'alturas': uma linha por nº de golpes acumulado e uma coluna por corpo de prova (altura do CP, mm).",
        "Aba 'cps': uma linha por corpo de prova; o nome em 'CP' deve ser igual ao cabeçalho da coluna em 'alturas'.",
        "Pi = 100·(Md·Lcp)/(Ms·Lex)·Fc, com Ms pela massa úmida e hc, e Lcp = altura final; ou informe 'Pi direto (%)'.",
        f"Série: {serie}. Exemplo preenchido: {fonte}."]})
    mem = io.BytesIO()
    with pd.ExcelWriter(mem, engine=resolve_xlsx_engine()) as xw:
        alturas.to_excel(xw, index=False, sheet_name="alturas")
        dados.to_excel(xw, index=False, sheet_name="cps")
        info.to_excel(xw, index=False, sheet_name="instrucoes")
    return mem.getvalue()


def modo_laboratorio(meta):
    st.markdown("Das leituras do ensaio aos coeficientes: informe as **alturas do corpo de prova** em cada nº de "
                "golpes e os **dados de cada CP**. O app calcula Mini-MCV, c', d', a altura final e o Pi' "
                "(DNIT 258/2023-ME) e classifica (DNIT 259/2023-CLA).")
    with st.container(border=True):
        c1, c2, c3 = st.columns([2.2, 1, 1], vertical_alignment="bottom")
        c1.selectbox("Exemplo com dados publicados", list(EXEMPLOS_LAB), key="mct_lab_exemplo")
        c2.button("Carregar exemplo", on_click=_carregar_exemplo, use_container_width=True)
        c3.button("Limpar tabelas", on_click=_limpar_lab, use_container_width=True)
        c4, c5, c6 = st.columns([1.2, 1, 1.4], vertical_alignment="bottom")
        serie = c4.radio("Série de golpes", ["Parsons", "Simplificada"], horizontal=True,
                         **keep("mct_lab_serie", "Parsons"))
        try:
            c5.download_button("Planilha-modelo", data=_modelo_lab_xlsx(), file_name="MCT_laboratorio_modelo.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        except Exception as ex:
            c5.caption(f"Excel indisponível: {ex}")
        arq = c6.file_uploader("Enviar planilha preenchida", type=["xlsx"], key="mct_lab_arquivo",
                               label_visibility="collapsed")
        if arq is not None and st.session_state.get("__mct_lab_arq") != (arq.name, arq.size):
            try:
                abas = pd.read_excel(arq, sheet_name=None)
                definir_editor("mct_lab_alturas", numerico(abas["alturas"]))
                definir_editor("mct_lab_dados", numerico(abas["cps"]))
                st.session_state["__mct_lab_arq"] = (arq.name, arq.size)
                st.session_state["__mct_lab_fonte"] = f"planilha {arq.name}"
                st.rerun()
            except Exception as ex:
                st.error(f"Não foi possível ler a planilha (abas 'alturas' e 'cps'): {ex}")
        if st.session_state.get("__mct_lab_fonte"):
            st.caption(f"Dados carregados: {st.session_state['__mct_lab_fonte']}")

    if "__editor_salvo__mct_lab_alturas" not in st.session_state:
        _limpar_lab()
    ca, cd = st.columns([1.35, 1], gap="medium")
    with ca:
        st.markdown("**Alturas do corpo de prova (mm)** por nº de golpes acumulado")
        alturas = editor_persistente("mct_lab_alturas", pd.DataFrame(), num_rows="dynamic", hide_index=True,
                                     use_container_width=True, height=420)
    with cd:
        st.markdown("**Dados de cada corpo de prova**")
        dados = editor_persistente("mct_lab_dados", pd.DataFrame(), num_rows="dynamic", hide_index=True,
                                   use_container_width=True)
        st.caption("hc: umidade de compactação. Ms = massa úmida/(1 + hc). Pi = 100·(Md·Lcp)/(Ms·Lex)·Fc, "
                   "com Lcp = altura final; ou preencha 'Pi direto (%)'.")

    cps = de_tabelas(alturas, dados)
    entrada = {"serie": serie, "alturas": alturas.to_json(), "dados": dados.to_json()}
    if st.button("Calcular", type="primary", disabled=len(cps) < 2,
                 help=None if len(cps) >= 2 else "Preencha ao menos dois corpos de prova."):
        try:
            salvar_resultado("mct_lab", entrada, calcular(cps, serie))
            st.session_state["__mct_lab_token"] = st.session_state.get("__mct_lab_token", 0) + 1
        except Exception as ex:
            salvar_resultado("mct_lab", entrada, str(ex))

    ultimo = ultimo_resultado("mct_lab", entrada)
    if not ultimo:
        return
    R, desatualizado = ultimo
    if desatualizado:
        aviso_desatualizado()
    if isinstance(R, str):
        st.error(R)
        return

    with st.container(border=True):
        st.markdown("**Resultados do ensaio**")
        st.dataframe(tabela_cps(R), hide_index=True, use_container_width=True)
        g1, g2 = st.columns(2)
        g1.pyplot(plot_deformabilidade(R), use_container_width=True)
        g2.pyplot(plot_compactacao(R), use_container_width=True)
        g3, g4 = st.columns(2)
        g3.pyplot(plot_af(R), use_container_width=True)
        g4.pyplot(plot_pi(R), use_container_width=True)
        st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(R.passos, 1)))
        for a in R.avisos:
            st.warning(a)
        st.caption("O “trecho retilíneo mais inclinado” é escolhido automaticamente (janela de 3 pontos de maior "
                   "inclinação, destacada em cinza nos gráficos). Ajuste os valores abaixo se a sua leitura for outra.")

    tk = st.session_state.get("__mct_lab_token", 0)
    with st.container(border=True):
        st.markdown("**Coeficientes adotados** — valores calculados; altere se necessário")
        k1, k2, k3 = st.columns(3)
        c_ = k1.number_input("c'", min_value=0.0, max_value=5.0, step=0.01, format="%.2f", placeholder="—",
                             **keep(f"mct_lab_c_{tk}", None if R.c_ is None else round(R.c_, 2)))
        d_ = k2.number_input("d' (kg/m³/%)", min_value=0.1, max_value=2000.0, step=0.5, format="%.1f",
                             placeholder="—", **keep(f"mct_lab_d_{tk}", None if R.d_ is None else round(R.d_, 1)))
        pi_ = k3.number_input("Pi' (%)", min_value=0.0, max_value=1000.0, step=0.1, format="%.1f", placeholder="—",
                              **keep(f"mct_lab_pi_{tk}", None if R.pi_ref is None else round(R.pi_ref, 1)))
        opc = ["Não verificado", "Sim", "Não"]
        pad = lambda v: "Não verificado" if v is None else ("Sim" if v else "Não")
        q1, q2 = st.columns(2)
        cr1 = q1.radio("Pi × Mini-MCV com inclinação negativa entre 10 e 15?", opc, horizontal=True,
                       **keep(f"mct_lab_cr1_{tk}", pad(R.crit_pi_negativa)))
        cr2 = q2.radio("Mini-MCV × umidade com concavidade para cima?", opc, horizontal=True,
                       **keep(f"mct_lab_cr2_{tk}", pad(R.crit_concavidade)))
        st.caption("Critérios do item 5.1 c) avaliados a partir dos dados (usados só se o ponto ficar perto da "
                   "fronteira L|N).")
    if None in (c_, d_, pi_):
        st.info("Faltam coeficientes para classificar: complete os dados do ensaio ou informe os valores acima.")
        return
    try:
        res = classify_from_inputs(MCTInput(c_=c_, d_=d_, pi_ref=pi_, meta=meta,
                                            serie="Parsons" if R.serie == "Parsons" else "simplificada",
                                            pi_inclinacao_negativa=None if cr1 == opc[0] else cr1 == "Sim",
                                            mcv_concavidade_para_cima=None if cr2 == opc[0] else cr2 == "Sim"))
    except Exception as ex:
        st.error(f"Erro ao classificar: {ex}")
        return
    mostrar_resultado(res, meta)


EX_CHAVE = "mct_ex_etapa"
EX_CSS = ("<style>.st-key-mct_ex_vars p, .st-key-mct_ex_vars li, .st-key-mct_ex_vars span "
          "{font-size:0.86rem !important; line-height:1.42}</style>")


def _ex_ir(delta: int):
    i = st.session_state.get(EX_CHAVE, 0) + delta
    definir_valor(EX_CHAVE, max(0, min(len(ETAPAS) - 1, i)))


def _ex_abrir_laboratorio():
    definir_valor("mct_modo", "Laboratório")
    st.session_state["mct_lab_exemplo"] = next(k for k in EXEMPLOS_LAB if k.startswith("Barbosa"))
    _carregar_exemplo()


def _ex_navegacao(i: int, sufixo: str):
    n = len(ETAPAS)
    c1, c2, c3 = st.columns([1, 3, 1], vertical_alignment="center")
    c1.button("◀ Anterior", key=f"ex_ant_{sufixo}", on_click=_ex_ir, args=(-1,), disabled=i == 0,
              use_container_width=True)
    c3.button("Próxima ▶", key=f"ex_prox_{sufixo}", on_click=_ex_ir, args=(1,), disabled=i == n - 1,
              use_container_width=True)
    return c2


def modo_ex_numerico():
    st.markdown(EX_CSS, unsafe_allow_html=True)
    st.markdown("**Exemplo numérico — classificação MCT, série de Parsons.** Siga as etapas com os botões; ao lado "
                "de cada cálculo, o painel explica as variáveis usadas.")
    st.caption(CREDITO)
    opcoes_estado = keep(EX_CHAVE, 0)
    i = st.session_state[EX_CHAVE]
    meio = _ex_navegacao(i, "topo")
    meio.selectbox("Etapa", range(len(ETAPAS)), format_func=lambda k: f"{k + 1} · {ETAPAS[k][0]}",
                   label_visibility="collapsed", **opcoes_estado)
    st.progress((i + 1) / len(ETAPAS), text=f"Etapa {i + 1} de {len(ETAPAS)}")
    titulo, funcao, chaves = ETAPAS[i]
    c_calc, c_vars = st.columns([1.75, 1], gap="large")
    with c_calc:
        st.subheader(f"{i + 1}. {titulo}")
        funcao()
        if i == len(ETAPAS) - 1:
            st.button("Abrir no modo Laboratório", type="primary", on_click=_ex_abrir_laboratorio)
    with c_vars:
        with st.container(border=True, key="mct_ex_vars"):
            st.markdown("**Variáveis desta etapa**")
            for k, chave in enumerate(chaves):
                if k:
                    st.divider()
                st.markdown(texto_markdown(chave), unsafe_allow_html=True)
    _ex_navegacao(i, "base")


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
    st.markdown(f"**Anexo B — Propriedades típicas dos grupos de solos** ({NORMA_CLA})")
    st.markdown(tabela_anexo_b_html(), unsafe_allow_html=True)
    st.caption("Granulometria típica: q = quartzo; m = micas; k = caulinita. Propriedades de corpos de prova "
               "compactados na umidade ótima, energia normal, com sobrecarga padrão quando pertinente.")
    _, c_g, _ = st.columns([1, 2, 1])
    with c_g:
        fig, _ = plot_mct_abaco()
        st.pyplot(fig, use_container_width=True)


cabecalho()
_meta = get_meta()
_modo = st.segmented_control("Modo", ["Uma amostra", "Laboratório", "Lote (CSV/Excel)", "Quadro dos grupos",
                                      "Ex. numérico"],
                             label_visibility="collapsed", required=True, **keep("mct_modo", "Uma amostra"))
if _modo == "Lote (CSV/Excel)":
    modo_lote()
elif _modo == "Laboratório":
    modo_laboratorio(_meta)
elif _modo == "Quadro dos grupos":
    modo_quadro()
elif _modo == "Ex. numérico":
    modo_ex_numerico()
else:
    modo_amostra(_meta)
