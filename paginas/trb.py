# paginas/trb.py
# Classificação TRB (HRB/AASHTO) — Tabela 4 do Manual de Pavimentação DNIT (IPR-719/2006).
# Mesmo padrão da página SUCS: entradas em dois quadros → Classificar → resultado em destaque.
import io

import pandas as pd
import streamlit as st

from didatica.generator_pdf import generate_random_sucs_pdf
from estado import aviso_desatualizado, keep, lote, salvar_resultado, ultimo_resultado
from formato import fmt
from projeto import get_meta
from trb_core import EXEMPLOS, classify_dataframe_trb, classify_trb, ig_conta, ig_label, plot_trb
from trb_defs import cbr_for_trb, get_definicao, get_materiais, sucs_provavel
from xlsx_utils import resolve_xlsx_engine, to_xlsx_bytes

META_COLS = ["Nome do projeto", "Técnico responsável", "Código da amostra"]
CINZA = "<span style='color:gray;font-size:0.8rem'>{}</span>"


def template_df() -> pd.DataFrame:
    rows = [{**{c: "" for c in META_COLS}, "Grupo_esperado": g, "descricao_sintetica": d, **p}
            for g, d, p in EXEMPLOS]
    return pd.DataFrame(rows, columns=META_COLS + ["Grupo_esperado", "descricao_sintetica",
                                                   "P10", "P40", "P200", "LL", "LP", "NP"])


def build_results_xlsx_trb(df: pd.DataFrame) -> bytes:
    preferred = META_COLS + ["P10", "P40", "P200", "LL", "LP", "IP_calc", "Grupo_TRB", "IG", "Subleito",
                             "Materiais constituintes", "CBR provável (%)", "aviso_ig", "relatorio"]
    df = df[[c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]]
    if resolve_xlsx_engine() != "xlsxwriter":
        return to_xlsx_bytes(df, "Resultados")
    mem = io.BytesIO()
    with pd.ExcelWriter(mem, engine="xlsxwriter") as xw:
        df.to_excel(xw, index=False, sheet_name="Resultados")
        wb, ws = xw.book, xw.sheets["Resultados"]
        wrap = wb.add_format({"text_wrap": True, "valign": "top"})
        hdr = wb.add_format({"bold": True, "bg_color": "#F2F2F2"})
        ws.set_row(0, None, hdr)
        widths = {"relatorio": 96, "aviso_ig": 48, "Materiais constituintes": 26, "CBR provável (%)": 16}
        for i, col in enumerate(df.columns):
            ws.set_column(i, i, widths.get(col, 14), wrap if col in ("relatorio", "aviso_ig") else None)
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)
        if "Grupo_TRB" in df.columns and "IG" in df.columns:
            ok = df[df["Grupo_TRB"] != "ERRO"]
            res = (ok.groupby("Grupo_TRB")["IG"].agg(["count", "min", "max", "mean"])
                   .rename(columns={"count": "n", "min": "IG_min", "max": "IG_max", "mean": "IG_médio"}))
            res.to_excel(xw, index=True, sheet_name="Resumo")
    return mem.getvalue()


def cabecalho():
    c_tit, c_crit, c_ref = st.columns([4, 1.5, 1.8], vertical_alignment="bottom")
    c_tit.title("Classificação TRB")
    with c_crit.popover("Critérios", use_container_width=True):
        st.markdown("\n".join([
            "- Eliminação da **esquerda para a direita** no quadro TRB.",
            "- **≤ 35%** passando na #200 → granular (A-1, A-3, A-2); **> 35%** → silto-argiloso (A-4 a A-7).",
            "- A-1-a: #10 ≤ 50, #40 ≤ 30, #200 ≤ 15, IP ≤ 6 · A-1-b: #40 ≤ 50, #200 ≤ 25, IP ≤ 6.",
            "- A-3: #40 ≥ 51, #200 ≤ 10, NP.",
            "- A-2 e finos: LL ≤ 40 ou ≥ 41; IP ≤ 10 ou ≥ 11. A-7-5: IP ≤ LL − 30; A-7-6: IP > LL − 30.",
            "- **IG = 0,2a + 0,005ac + 0,01bd** (0 a 20): a = P − 35 (0–40), b = P − 15 (0–40), "
            "c = LL − 40 (0–20), d = IP − 10 (0–20). O IG não define o grupo; qualifica o subleito.",
            "- Valores decimais: LL > 40 conta como “41 mín.”; IP > 10 como “11 mín.”.",
        ]))
    with c_ref.popover("Referências", use_container_width=True):
        st.markdown("\n".join([
            "- Manual de Pavimentação DNIT, IPR-719/2006 (versão corrigida com a Errata 1): Tabela 4 "
            "(quadro TRB), Índice de Grupo, Tabelas 11 e 14.",
            "- Granulometria: DNIT 459/2025-ME.",
            "- Limite de liquidez: DNER-ME 122/94; limite de plasticidade: DNER-ME 082/94.",
        ]))
    st.caption("Transportation Research Board (HRB/AASHTO) — quadro do Manual de Pavimentação DNIT. "
               "A #200 e os limites são compartilhados com a página SUCS (mesma amostra).")


def quadro_granulometria():
    with st.container(border=True):
        st.markdown("**Granulometria** — % passante")
        c10, c40, c200 = st.columns(3)
        p10 = c10.number_input("Peneira nº 10", 0.0, 100.0, step=0.1, placeholder="—", **keep("trb_p10", None))
        p40 = c40.number_input("Peneira nº 40", 0.0, 100.0, step=0.1, placeholder="—", **keep("trb_p40", None))
        p200 = c200.number_input("Peneira nº 200", 0.0, 100.0, step=0.1, placeholder="—",
                                 **keep("comum_p200", None))
        if None in (p10, p40, p200):
            st.caption("Informe a % passante nas peneiras nº 10, 40 e 200.")
            return (p10, p40, p200), None
        if not (p200 <= p40 <= p10):
            st.warning("As peneiras devem obedecer: #200 ≤ #40 ≤ #10.")
            return (p10, p40, p200), None
        granular = p200 <= 35.0
        st.caption(f"#200 = **{fmt(p200)}%** → **{'granular (≤ 35%)' if granular else 'silto-argiloso (> 35%)'}**")
        return (p10, p40, p200), granular


def quadro_plasticidade():
    with st.container(border=True):
        st.markdown("**Plasticidade** — limites de Atterberg")
        cll, clp, cnp = st.columns([1, 1, 0.8], vertical_alignment="bottom")
        np_ = cnp.checkbox("NP", help="Não plástico. No TRB o LL, se houver, ainda entra no IG.",
                           **keep("comum_np", False))
        ll = cll.number_input("LL (%)", 0.0, 300.0, step=0.1, placeholder="—", **keep("comum_ll", None))
        lp = clp.number_input("LP (%)", 0.0, 300.0, step=0.1, disabled=np_, placeholder="—",
                              **keep("comum_lp", None))
        if np_:
            st.caption("IP = **NP**" + (f" · LL = {fmt(ll)} ({'≤ 40' if ll <= 40 else '≥ 41'})" if ll is not None else ""))
            return {"ll": ll or 0.0, "lp": 0.0, "np": True}, True
        if ll is None or lp is None:
            st.caption("Informe LL e LP, ou marque NP.")
            return {"ll": ll, "lp": lp, "np": False}, False
        if lp > ll:
            st.warning("LP maior que LL: verifique os ensaios (ou marque NP).")
            return {"ll": ll, "lp": lp, "np": False}, False
        ip = ll - lp
        st.caption(f"IP = **{fmt(ip)}** ({'≤ 10' if ip <= 10 else '≥ 11'}) · LL {'≤ 40' if ll <= 40 else '≥ 41'}"
                   + (f" · LL − 30 = {fmt(ll - 30)}" if ll > 40 and ip > 10 else ""))
        return {"ll": ll, "lp": lp, "np": False}, True


def mostrar_resultado(r, meta):
    with st.container(border=True):
        ch, cig = st.columns([3, 1], vertical_alignment="center")
        ch.markdown(f"<div style='font-size:2.6rem;font-weight:700;line-height:1.1'>{r.group}</div>",
                    unsafe_allow_html=True)
        cig.metric("Índice de Grupo", r.ig, help=ig_label(r.ig))
        st.markdown(get_definicao(r.group))
        if r.aviso_ig:
            st.warning(r.aviso_ig)
        c_txt, c_graf = st.columns([1, 1.15], gap="large")
        with c_txt:
            st.markdown("**Como cheguei aqui**")
            st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(r.rationale, 1)))
            st.markdown(f"**Índice de Grupo** — {ig_label(r.ig)}  \n`{ig_conta(r.ig_detalhe)}`")
            m1, m2 = st.columns(2)
            m1.markdown(f"**Subleito**  \n{r.subleito}  \n" + CINZA.format("Quadro TRB"), unsafe_allow_html=True)
            m2.markdown(f"**CBR provável**  \n{cbr_for_trb(r.group)}%  \n" + CINZA.format("Tabela 14, Manual IPR-719"),
                        unsafe_allow_html=True)
            sp = sucs_provavel(r.group)
            m1.markdown(f"**Materiais**  \n{get_materiais(r.group)}", unsafe_allow_html=True)
            m2.markdown(f"**SUCS provável**  \n{sp[0]}" + (f"; possível {sp[1]}" if sp[1] != "—" else "")
                        + "  \n" + CINZA.format("Tabela 11, Manual IPR-719"), unsafe_allow_html=True)
        with c_graf:
            st.pyplot(plot_trb(r.ll if (r.ll or not r.np_) else None, r.ip, r.granular, r.np_),
                      use_container_width=True)
        rel = (f"Nome do projeto: {meta['projeto'] or '-'}\nTécnico responsável: {meta['tecnico'] or '-'}\n"
               f"Código da amostra: {meta['amostra'] or '-'}\n\n") + r.relatorio
        with st.expander("Relatório completo"):
            st.code(rel, language=None)
        st.download_button("Baixar relatório (.txt)", data=rel.encode("utf-8"),
                           file_name=f"TRB_{(meta['amostra'] or 'amostra').replace(' ', '_')}.txt", mime="text/plain")


def modo_amostra(meta):
    c_g, c_p = st.columns([1.15, 1], gap="medium")
    with c_g:
        (p10, p40, p200), granular = quadro_granulometria()
    with c_p:
        plast, plast_ok = quadro_plasticidade()
    entrada = {"p10": p10, "p40": p40, "p200": p200, **plast}
    pronto = granular is not None and plast_ok
    if st.button("Classificar", type="primary", disabled=not pronto,
                 help=None if pronto else "Preencha a granulometria e os limites (ou NP)."):
        try:
            salvar_resultado("trb", entrada, classify_trb(p10, p40, p200, plast["ll"], plast["lp"],
                                                          is_np=plast["np"]))
        except Exception as e:
            salvar_resultado("trb", entrada, str(e))

    ultimo = ultimo_resultado("trb", entrada)
    if ultimo:
        r, desatualizado = ultimo
        if desatualizado:
            aviso_desatualizado()
        if isinstance(r, str):
            st.error(r)
        else:
            mostrar_resultado(r, meta)


def modo_lote(meta):
    st.markdown("Uma linha por amostra. Colunas: **P10**, **P40**, **P200** (% passante), **LL**, **LP** "
                "(ou **IP**) e **NP** (sim/não). A planilha-modelo traz um exemplo por grupo.")
    modelo = template_df()
    c1, c2, _ = st.columns([1, 1, 2])
    try:
        c1.download_button("Planilha-modelo (Excel)", data=to_xlsx_bytes(modelo, "modelo_trb"),
                           file_name="TRB_modelo.xlsx", use_container_width=True,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        c1.caption(f"Excel indisponível: {e}")
    c2.download_button("Planilha-modelo (CSV)", data=modelo.to_csv(index=False).encode("utf-8"),
                       file_name="TRB_modelo.csv", mime="text/csv", use_container_width=True)

    def processar(df):
        if "NP" in df.columns:
            df["NP"] = df["NP"].astype(str).str.strip().str.lower().map({
                "true": True, "false": False, "1": True, "0": False, "1.0": True, "0.0": False,
                "sim": True, "não": False, "nao": False, "np": True}).fillna(False)
        else:
            df["NP"] = False
        for col, val in zip(META_COLS, (meta["projeto"], meta["tecnico"], meta["amostra"])):
            if col not in df.columns and val:
                df[col] = val
        out = classify_dataframe_trb(df)
        if "Grupo_esperado" in out.columns:
            out.insert(0, "confere", out["Grupo_esperado"].astype(str) == out["Grupo_TRB"].astype(str))
        return out

    up = st.file_uploader("Enviar planilha (CSV ou Excel)", type=["csv", "xlsx"], key="trb_lote")
    try:
        res_lote = lote("trb", up, processar)
        if res_lote:
            out, nome, reaproveitado = res_lote
            if reaproveitado:
                st.caption(f"Último lote processado: **{nome}**")
            st.dataframe(out, use_container_width=True)
            d1, d2, _ = st.columns([1, 1, 2])
            d1.download_button("Baixar resultados (XLSX)", data=build_results_xlsx_trb(out),
                               file_name="resultado_trb.xlsx", use_container_width=True,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            d2.download_button("Baixar resultados (CSV)", data=out.to_csv(index=False).encode("utf-8"),
                               file_name="resultado_trb.csv", mime="text/csv", use_container_width=True)
    except Exception as e:
        st.error(str(e))


def ficha_exercicio():
    """Informação complementar: fica na barra lateral."""
    with st.sidebar.expander("🧪 Ficha de exercício (PDF)", expanded=False):
        st.caption("Ficha aleatória com granulometria e limites (sem a classe), para exercício de "
                   "classificação TRB e SUCS.")
        if st.button("Gerar ficha (PDF)", key="didatica_btn_pdf"):
            try:
                st.session_state["__ficha_pdf__"] = generate_random_sucs_pdf()
            except Exception as _e:
                st.caption(f"Não foi possível gerar a ficha: {_e}")
        if "__ficha_pdf__" in st.session_state:
            _pdf_bytes, _meta = st.session_state["__ficha_pdf__"]
            st.download_button(f"Baixar ficha {_meta['amostra']} (PDF)", data=_pdf_bytes,
                               file_name=f"Ficha_{_meta['amostra']}.pdf", mime="application/pdf",
                               key="didatica_dl_pdf")


cabecalho()
_meta = get_meta()
_modo = st.segmented_control("Modo", ["Uma amostra", "Lote (CSV/Excel)"], label_visibility="collapsed",
                             required=True, **keep("trb_modo", "Uma amostra"))
if _modo == "Lote (CSV/Excel)":
    modo_lote(_meta)
else:
    modo_amostra(_meta)
ficha_exercicio()
