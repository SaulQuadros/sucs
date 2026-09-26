# paginas/sucs.py
# Página SUCS — Manual de Pavimentação DNIT (IPR-719/2006).
# Layout: entradas compactas em dois quadros → Classificar → resultado em destaque
# (símbolo, justificativa e gráfico lado a lado). Modo lote separado.
import pandas as pd
import streamlit as st

from estado import aviso_desatualizado, keep, lote, salvar_resultado, ultimo_resultado
from atterberg import avaliar
from projeto import get_meta
from sucs_core import (EXEMPLOS, classify_dataframe, classify_sucs_result, cu_cc, fmt, line_a,
                       plasticity_zone, plot_plasticidade)
from xlsx_utils import to_xlsx_bytes

TEMPLATE_COLS = ["grupo_esperado", "descricao_sintetica", "projeto", "tecnico", "amostra",
                 "P4", "P200", "LL", "LP", "NP", "Cu", "Cc", "D10", "D30", "D60", "organico", "turfa"]
ZONA_TXT = {"M": "abaixo da linha A (siltoso)", "C": "acima da linha A (argiloso)",
            "MC": "zona hachurada (limítrofe)"}


def template_df() -> pd.DataFrame:
    rows = []
    for g, d, p in EXEMPLOS:
        rec = {c: None for c in TEMPLATE_COLS}
        rec.update(grupo_esperado=g, descricao_sintetica=d, projeto="Demo", tecnico="Equipe", amostra=g,
                   NP=False, organico=False, turfa=False)
        rec.update(p)
        rows.append(rec)
    return pd.DataFrame(rows, columns=TEMPLATE_COLS)


def cabecalho():
    c_tit, c_crit, c_ref = st.columns([4, 1.5, 1.8], vertical_alignment="bottom")
    c_tit.title("Classificação SUCS")
    with c_crit.popover("Critérios", use_container_width=True):
        st.markdown("\n".join([
            "- **Mais de 50% retido na #200** → grossa; **50% ou mais passando** → fina.",
            "- Grossa: **G** se 50% ou mais da fração graúda fica retida na #4; senão **S**.",
            "  - Finos **< 5%**: W/P por Cu e Cc (pedregulho Cu ≥ 4; areia Cu ≥ 6; 1 ≤ Cc ≤ 3).",
            "  - Finos **5–12%**: símbolo duplo (ex.: SW-SM, GP-GC).",
            "  - Finos **> 12%**: M abaixo da linha A, C acima, M-C na zona hachurada.",
            "- Fina: linha A IP = 0,73·(LL − 20); **L** se LL ≤ 50, **H** se LL > 50;",
            "  zona hachurada (4 ≤ IP ≤ 7 acima da linha A) → ML-CL; orgânicos abaixo da linha A → OL/OH.",
        ]))
    with c_ref.popover("Referências", use_container_width=True):
        st.markdown("\n".join([
            "- Manual de Pavimentação DNIT, IPR-719/2006 (versão corrigida com a Errata 1): "
            "Tabela 5, Figura 17, fluxograma de identificação, Tabelas 12 e 13.",
            "- Granulometria: DNIT 459/2025-ME.",
            "- Limite de liquidez: DNER-ME 122/94; limite de plasticidade: DNER-ME 082/94.",
        ]))
    st.caption("Sistema Unificado de Classificação de Solos — critérios do Manual de Pavimentação DNIT. "
               "Granulometria e limites são compartilhados com a página TRB (mesma amostra).")


def quadro_granulometria():
    """Retorna (entradas, grossa): grossa = True/False, ou None enquanto a #200 não for informada
    (ou os dados forem inconsistentes)."""
    with st.container(border=True):
        st.markdown("**Granulometria** — % passante")
        # Ordem da Tabela 5: a nº 200 decide grossa × fina; a nº 4 só entra nos solos grossos (fração graúda).
        c200, c4 = st.columns(2)
        p200 = c200.number_input("Peneira nº 200 (0,075 mm)", 0.0, 100.0, step=0.1, placeholder="—",
                                 help="Mais de 50% retido → graduação grossa; 50% ou mais passando → fina.",
                                 **keep("comum_p200", None))
        grossa = None if p200 is None else (100.0 - p200) > 50.0
        p4 = c4.number_input("Peneira nº 4 (4,75 mm)", 0.0, 100.0, step=0.1, placeholder="—",
                             disabled=grossa is not True,
                             help="Só para solos grossos: separa pedregulho (retido na nº 4) de areia na fração "
                                  "graúda.", **keep("sucs_p4", None))
        g = {"P4": p4 if grossa else None, "P200": p200, "Cu": None, "Cc": None, "D10": None, "D30": None,
             "D60": None}
        if p200 is None:
            st.caption("Informe a % passante na nº 200: ela define se o solo é de graduação grossa ou fina.")
            return g, None
        finos, retido = p200, 100.0 - p200
        txt = f"Finos **{fmt(finos)}%** · retido na #200 {fmt(retido)}% → **{'grossa' if grossa else 'fina'}**"
        if not grossa:
            st.caption(txt + "  \nSolo de graduação fina: a classificação usa LL e LP; a peneira nº 4 não entra "
                             "(Tabela 5 do Manual IPR-719).")
            return g, grossa
        if p4 is None:
            st.caption(txt + "  \nInforme a % passante na nº 4 para separar pedregulho de areia.")
            return g, None
        if p4 < p200:
            st.error("A % passante na nº 4 não pode ser menor que na nº 200: todo o material que passa na nº 200 "
                     "também passa na nº 4.")
            return g, None
        ped = 100.0 * (100.0 - p4) / retido
        txt += (f"  \nFração graúda: pedregulho {fmt(ped)}% · areia {fmt(100 - ped)}% → "
                f"**{'pedregulho (G)' if ped >= 50 else 'areia (S)'}**")
        st.caption(txt)
        if abs(p4 - p200) < 1e-9:
            st.info("Passante na nº 4 igual ao da nº 200: a fração areia é nula (granulometria descontínua). "
                    "É possível, mas confira o ensaio.")

        if grossa and finos <= 12.0:
            st.markdown("**Graduação** (decide W/P)")
            modo = st.radio("Graduação", ["D10, D30, D60 (mm)", "Cu e Cc", "Não informar"], horizontal=True,
                            label_visibility="collapsed", **keep("sucs_modo_grad", "D10, D30, D60 (mm)"))
            if modo.startswith("D10"):
                c1, c2, c3 = st.columns(3)
                g["D10"] = c1.number_input("D10", 0.0, 100.0, step=0.01, format="%.3f", placeholder="—",
                                           **keep("sucs_d10", None))
                g["D30"] = c2.number_input("D30", 0.0, 100.0, step=0.01, format="%.3f", placeholder="—",
                                           **keep("sucs_d30", None))
                g["D60"] = c3.number_input("D60", 0.0, 100.0, step=0.01, format="%.3f", placeholder="—",
                                           **keep("sucs_d60", None))
                cu, cc = cu_cc(g["D10"], g["D30"], g["D60"])
                if cu is not None:
                    st.caption(f"Cu = {fmt(cu, 2)} · Cc = {fmt(cc, 2)}")
            elif modo == "Cu e Cc":
                c1, c2 = st.columns(2)
                g["Cu"] = c1.number_input("Cu", 0.0, 1000.0, step=0.1, placeholder="—", **keep("sucs_cu", None))
                g["Cc"] = c2.number_input("Cc", 0.0, 1000.0, step=0.01, placeholder="—", **keep("sucs_cc", None))
        elif grossa:
            st.caption("Finos acima de 12%: a graduação (W/P) não entra na classificação.")
        return g, grossa


def quadro_plasticidade(grossa):
    liberado = grossa is not None
    with st.container(border=True):
        st.markdown("**Plasticidade** — limites de Atterberg")
        cll, clp, cnp = st.columns([1, 1, 0.8], vertical_alignment="bottom")
        NP = cnp.checkbox("NP", disabled=not liberado,
                          help="Não plástico (DNER-ME 082/94): LL ou LP não determinável, ou LP ≥ LL.",
                          **keep("comum_np", False))
        LL = cll.number_input("LL (%)", 0.0, 300.0, step=0.1, disabled=NP or not liberado, placeholder="—",
                              **keep("comum_ll", None))
        LP = clp.number_input("LP (%)", 0.0, 300.0, step=0.1, disabled=NP or not liberado, placeholder="—",
                              **keep("comum_lp", None))
        lim = avaliar(LL, LP, NP)
        if not liberado:
            st.caption("Liberado depois da granulometria.")
        elif lim.erro:
            st.error(lim.erro)
        elif lim.np_:
            if lim.nota:
                st.info(lim.nota)
            st.caption("IP = **NP** → finos não plásticos (tratados como siltosos)")
        elif not lim.completo:
            st.caption("Informe LL e LP, ou marque NP.")
        else:
            z = plasticity_zone(LL, LP)
            st.caption(f"IP = **{fmt(lim.ip)}** · linha A em {fmt(line_a(LL))} → {ZONA_TXT[z]}")
        st.markdown("**Matéria orgânica**")
        co, ct = st.columns(2)
        organico = co.checkbox("Evidência orgânica", disabled=bool(grossa),
                               help="Cor escura, odor ou queda do LL após secagem em estufa. Aplica-se a solos "
                                    "finos abaixo da linha A: OL (LL ≤ 50) ou OH (LL > 50).",
                               **keep("sucs_organico", False))
        turfa = ct.checkbox("Turfa", help="Material altamente orgânico e fibroso → PT.",
                            **keep("sucs_turfa", False))
    return {"LL": None if NP else LL, "LP": None if NP else LP, "NP": NP,
            "organico": organico and not grossa, "turfa": turfa}, lim.erro is None


def mostrar_resultado(r, meta):
    with st.container(border=True):
        if r.completo:
            st.markdown(f"<div style='font-size:2.6rem;font-weight:700;line-height:1.1'>{r.group}</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:2.2rem;font-weight:700;line-height:1.1;color:#b26a00'>"
                        f"{r.group} <span style='font-size:1rem;font-weight:500'>(incompleto)</span></div>",
                        unsafe_allow_html=True)
        if r.descricao:
            st.markdown(r.descricao)
        for a in r.avisos:
            st.warning(a)
        c_txt, c_graf = st.columns([1, 1.15], gap="large")
        with c_txt:
            st.markdown("**Como cheguei aqui**")
            st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(r.passos, 1)))
            m1, m2 = st.columns(2)
            if r.cbr:
                m1.markdown(f"**CBR provável**  \n{r.cbr}%  \n<span style='color:gray;font-size:0.8rem'>"
                            f"Tabela 13, Manual IPR-719</span>", unsafe_allow_html=True)
            if r.trb:
                s, (mp, pp, _) = r.trb
                m2.markdown(f"**TRB provável** ({s})  \n{mp}" + (f"; possível {pp}" if pp != "—" else "")
                            + "  \n<span style='color:gray;font-size:0.8rem'>Tabela 12, Manual IPR-719</span>",
                            unsafe_allow_html=True)
        with c_graf:
            if r.NP or r.LL is not None:
                st.pyplot(plot_plasticidade(r.LL, r.IP, r.NP), use_container_width=True)
            else:
                st.caption("Informe LL e LP para posicionar a amostra no gráfico de plasticidade.")
        rel = r.relatorio(meta)
        with st.expander("Relatório completo"):
            st.code(rel, language=None)
        st.download_button("Baixar relatório (.txt)", rel.encode("utf-8"),
                           file_name=f"SUCS_{(meta.get('amostra') or 'amostra').replace(' ', '_')}.txt",
                           mime="text/plain")


def modo_amostra(meta):
    c_g, c_p = st.columns(2, gap="medium")
    with c_g:
        g, grossa = quadro_granulometria()
    with c_p:
        p, limites_ok = quadro_plasticidade(grossa)
    entrada = {**g, **p}

    if st.button("Classificar", type="primary", disabled=grossa is None or not limites_ok,
                 help="Complete a granulometria (nº 200 e, para solo grosso, nº 4)." if grossa is None else None):
        try:
            salvar_resultado("sucs", entrada, classify_sucs_result(entrada))
        except ValueError as e:
            salvar_resultado("sucs", entrada, str(e))

    ultimo = ultimo_resultado("sucs", entrada)
    if ultimo:
        saida, desatualizado = ultimo
        if desatualizado:
            aviso_desatualizado()
        if isinstance(saida, str):
            st.error(saida)
        else:
            mostrar_resultado(saida, meta)


def _processar_lote(df):
    res = classify_dataframe(df)
    if "grupo_esperado" in res.columns:
        res.insert(1, "confere", res["grupo_esperado"].astype(str) == res["grupo"].astype(str))
    return res


def modo_lote():
    st.markdown("Uma linha por amostra. Colunas: **P4** e **P200** (% passante), **LL**, **LP**, **NP**, "
                "**Cu**/**Cc** ou **D10**/**D30**/**D60** (mm), **organico**, **turfa**. "
                "Arquivos no formato antigo (pct_retido_200, pct_pedregulho_coarse, pct_areia_coarse) também são aceitos.")
    modelo = template_df()
    c1, c2, _ = st.columns([1, 1, 2])
    try:
        c1.download_button("Planilha-modelo (Excel)", data=to_xlsx_bytes(modelo, "exemplos"),
                           file_name="SUCS_modelo.xlsx", use_container_width=True,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        c1.caption(f"Excel indisponível: {e}")
    c2.download_button("Planilha-modelo (CSV)", data=modelo.to_csv(index=False).encode("utf-8"),
                       file_name="SUCS_modelo.csv", mime="text/csv", use_container_width=True)
    uploaded = st.file_uploader("Enviar planilha (CSV ou Excel)", type=["csv", "xlsx"], key="sucs_lote")
    try:
        r = lote("sucs", uploaded, _processar_lote)
        if r:
            res, nome, reaproveitado = r
            if reaproveitado:
                st.caption(f"Último lote processado: **{nome}**")
            st.dataframe(res, use_container_width=True)
            st.download_button("Baixar resultados (CSV)", res.to_csv(index=False).encode("utf-8"),
                               file_name="resultados_sucs.csv", mime="text/csv")
    except Exception as e:
        st.error(str(e))


cabecalho()
_meta = get_meta()
_modo = st.segmented_control("Modo", ["Uma amostra", "Lote (CSV/Excel)"], label_visibility="collapsed", required=True,
                             **keep("sucs_modo", "Uma amostra"))
if _modo == "Lote (CSV/Excel)":
    modo_lote()
else:
    modo_amostra(_meta)
