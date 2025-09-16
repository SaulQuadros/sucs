#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# streamlit_app.py
# App Streamlit para classificar solos pelo SUCS (conforme DNIT/SUCS)

import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from sucs_core import classify_sucs, classify_dataframe, LINE_A_SLOPE


def build_excel_template_bytes():
    import io
    import pandas as pd
    # Planilha-modelo SUCS: cabeçalhos oficiais e algumas linhas de exemplo
    cols = [
        "grupo_esperado","descricao_sintetica",
        "projeto","tecnico","amostra",
        "pct_retido_200","pct_pedregulho_coarse","pct_areia_coarse",
        "LL","LP","Cu","Cc","organico","turfa"
    ]
    exemplos = [
        dict(grupo_esperado="GW", descricao_sintetica="Cascalho bem graduado", projeto="Demo", tecnico="Equipe",
             amostra="Ex1", pct_retido_200=None, pct_pedregulho_coarse=70, pct_areia_coarse=30,
             LL=None, LP=None, Cu=8, Cc=2.0, organico=False, turfa=False),
        dict(grupo_esperado="SW", descricao_sintetica="Areia bem graduada", projeto="Demo", tecnico="Equipe",
             amostra="Ex2", pct_retido_200=None, pct_pedregulho_coarse=30, pct_areia_coarse=70,
             LL=None, LP=None, Cu=7, Cc=1.5, organico=False, turfa=False),
        dict(grupo_esperado="CL", descricao_sintetica="Silte/argila de baixa plasticidade", projeto="Demo", tecnico="Equipe",
             amostra="Ex3", pct_retido_200=55, pct_pedregulho_coarse=10, pct_areia_coarse=35,
             LL=35, LP=22, Cu=None, Cc=None, organico=False, turfa=False),
    ]
    df = pd.DataFrame.from_records(exemplos, columns=cols)
    bio = io.BytesIO()
    eng = _resolve_xlsx_engine()
    if not eng:
        raise RuntimeError("Nenhum engine Excel disponível. Instale XlsxWriter ou openpyxl.")
    with pd.ExcelWriter(bio, engine=eng) as writer:
        df.to_excel(writer, index=False, sheet_name="exemplos")
    bio.seek(0)
    return bio
# --- Excel engine resolver (XLSX) ---
def _resolve_xlsx_engine():
    """Return a working engine string for pandas.ExcelWriter (prefer xlsxwriter)."""
    try:
        import xlsxwriter  # type: ignore
        return "xlsxwriter"
    except Exception:
        try:
            import openpyxl  # type: ignore
            return "openpyxl"
        except Exception:
            return None

    # monta um exemplo por grupo (mesma lógica dos exemplos gerados anteriormente)
    rows = [
        # grupo, descricao, params...
        ("GW", "Cascalho bem graduado, com/sem areia, poucos finos",
            dict(pct_retido_200=97, pct_pedregulho_coarse=70, pct_areia_coarse=30, LL=25, LP=20, Cu=8, Cc=2.0, organico=False, turfa=False)),
        ("GP", "Cascalho mal graduado, com/sem areia, poucos finos",
            dict(pct_retido_200=96, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=25, LP=20, Cu=2, Cc=0.6, organico=False, turfa=False)),
        ("GM", "Cascalho siltoso (fino abaixo da linha A)",
            dict(pct_retido_200=75, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=40, LP=27, organico=False, turfa=False)),
        ("GC", "Cascalho argiloso (fino acima da linha A)",
            dict(pct_retido_200=75, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=40, LP=20, organico=False, turfa=False)),
        ("SW", "Areia bem graduada, com cascalho, poucos finos",
            dict(pct_retido_200=97, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=25, LP=20, Cu=7, Cc=1.5, organico=False, turfa=False)),
        ("SP", "Areia mal graduada, com cascalho, poucos finos",
            dict(pct_retido_200=96, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=25, LP=20, Cu=3, Cc=0.8, organico=False, turfa=False)),
        ("SM", "Areia siltosa (fino abaixo da linha A)",
            dict(pct_retido_200=75, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=40, LP=27, organico=False, turfa=False)),
        ("SC", "Areia argilosa (fino acima da linha A)",
            dict(pct_retido_200=75, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=40, LP=20, organico=False, turfa=False)),
        ("ML", "Silte de baixo LL; areias muito finas siltosas; pó-de-pedra",
            dict(pct_retido_200=30, LL=35, LP=25, organico=False, turfa=False)),
        ("CL", "Argila de baixa a média plasticidade",
            dict(pct_retido_200=30, LL=35, LP=22, organico=False, turfa=False)),
        ("OL", "Silte orgânico de baixa plasticidade",
            dict(pct_retido_200=30, LL=35, LP=20, organico=True, turfa=False)),
        ("MH", "Silte de alto LL; materiais micáceos/diatomáceos",
            dict(pct_retido_200=30, LL=70, LP=40, organico=False, turfa=False)),
        ("CH", "Argila de alta plasticidade",
            dict(pct_retido_200=30, LL=70, LP=25, organico=False, turfa=False)),
        ("OH", "Silte/argila orgânicos de alto LL",
            dict(pct_retido_200=30, LL=60, LP=30, organico=True, turfa=False)),
        ("Pt", "Turfa",
            dict(pct_retido_200=10, LL=150, LP=50, organico=True, turfa=True)),
    ]
    records = []
    for grupo, desc, params in rows:
        rec = dict(
            grupo_esperado=grupo,
            descricao_sintetica=desc,
            projeto="Demo",
            tecnico="Equipe",
            amostra=grupo,
            pct_retido_200=None,
            pct_pedregulho_coarse=0,
            pct_areia_coarse=0,
            LL=None, LP=None, Cu=None, Cc=None, organico=False, turfa=False
        )
        rec.update(params)
        records.append(rec)
    df = pd.DataFrame.from_records(records, columns=[
        "grupo_esperado","descricao_sintetica",
        "projeto","tecnico","amostra",
        "pct_retido_200","pct_pedregulho_coarse","pct_areia_coarse",
        "LL","LP","Cu","Cc","organico","turfa"
    ])
    # Exporta para Excel em memória
    bio = io.BytesIO()
    # Escolhe engine disponível (XlsxWriter preferido; fallback openpyxl)
    engine = None
    try:
        import xlsxwriter  # noqa: F401
        engine = "xlsxwriter"
    except Exception:
        try:
            import openpyxl  # noqa: F401
            engine = "openpyxl"
        except Exception:
            engine = None
    if engine is None:
        raise RuntimeError("Nenhum engine Excel disponível. Instale XlsxWriter ou openpyxl.")
    with pd.ExcelWriter(bio, engine=engine) as writer:
        df.to_excel(writer, index=False, sheet_name="exemplos")
    bio.seek(0)
    return bio.getvalue()


st.set_page_config(page_title="Classificador SUCS (DNIT)", layout="wide")
st.title("Classificador SUCS — DNIT")

with st.sidebar:
    st.header("Projeto")
    projeto = st.text_input("Nome do projeto")
    tecnico = st.text_input("Técnico responsável")
    amostra = st.text_input("Código da amostra")


with st.expander("ℹ️ Ajuda rápida", expanded=False):
    st.markdown(
        "\n".join([
            "- O SUCS inicia pela **fração fina (#200)**:",
            "  - Se **% passante #200 < 50%** → material **coarse** (areia/cascalho).",
            "  - Se **% passante #200 ≥ 50%** → material **fino** (siltes/argilas).",
            "- Para **grossa**:",
            "  - Separar **cascalho × areia** na #4 (pedregulho > #4).",
            "  - Quando finos **< 5%**, usar **Cu** e **Cc**: **W** (bem graduado) ou **P** (mal graduado).",
            "  - Quando **5% ≤ finos ≤ 12%**, usar sufixos mistos (**GW-GM**, **SW-SC**, etc.).",
            "  - Quando **fins > 12%**, a classificação passa a depender da plasticidade.",
            "- Para **finos**:",
            "  - Usar **LL** e **LP** (Atterberg).",
            "  - **Linha A**: IP = 0,73(LL − 20). Abaixo → **M** (siltoso); acima → **C** (argiloso).",
            "- **Materiais orgânicos** → sufixo **O**; **turfa** → **Pt** (classificação específica).",
        ])
    )
    st.divider()
    st.subheader("Planilha-modelo (SUCS)")
    try:
        _xlsx_buf_sucs = build_excel_template_bytes()
        st.download_button(
            "Baixar planilha-modelo (Excel)",
            data=_xlsx_buf_sucs,
            file_name="SUCS_todos_os_grupos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_model_sucs_xlsx_main",
        )
    except Exception as _e:
        st.caption("Não foi possível gerar o modelo em Excel: " + str(_e))

    # CSV modelo (mesmas colunas)
    _modelo_cols = [
        "grupo_esperado","descricao_sintetica","projeto","tecnico","amostra",
        "pct_retido_200","pct_pedregulho_coarse","pct_areia_coarse",
        "LL","LP","Cu","Cc","organico","turfa"
    ]
    _modelo_rows = [
        {"grupo_esperado":"GW","descricao_sintetica":"Cascalho bem graduado","projeto":"","tecnico":"","amostra":"",
         "pct_retido_200":97,"pct_pedregulho_coarse":70,"pct_areia_coarse":30,"LL":None,"LP":None,"Cu":8,"Cc":2.0,"organico":False,"turfa":False},
        {"grupo_esperado":"SW","descricao_sintetica":"Areia bem graduada","projeto":"","tecnico":"","amostra":"",
         "pct_retido_200":97,"pct_pedregulho_coarse":30,"pct_areia_coarse":70,"LL":None,"LP":None,"Cu":7,"Cc":1.5,"organico":False,"turfa":False},
        {"grupo_esperado":"CL","descricao_sintetica":"Baixa plasticidade","projeto":"","tecnico":"","amostra":"",
         "pct_retido_200":55,"pct_pedregulho_coarse":10,"pct_areia_coarse":35,"LL":35,"LP":22,"Cu":None,"Cc":None,"organico":False,"turfa":False},
    ]
    _df_modelo = pd.DataFrame.from_records(_modelo_rows, columns=_modelo_cols)
    _csv_buf = io.BytesIO(); _df_modelo.to_csv(_csv_buf, index=False, encoding="utf-8"); _csv_buf.seek(0)
    st.download_button(
        "Baixar planilha-modelo (CSV)",
        data=_csv_buf,
        file_name="SUCS_todos_os_grupos.csv",
        mime="text/csv",
        key="dl_model_sucs_csv_main",
    )
col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    st.subheader("Granulometria")
    pct_retido_200 = st.number_input(
        "% retido na peneira #200", 0.0, 100.0, step=0.1)
    fines = max(0.0, 100.0 - pct_retido_200)
    st.caption(f"≥ 50% retido ⇒ granulação grossa; < 50% ⇒ fina | % de finos (passando #200) = {fines:.1f}%")

    coarse = pct_retido_200 >= 50.0
    st.markdown("**Na fração > #200 (apenas se grossa):**")
    if coarse:
        pct_pedregulho = st.number_input("% pedregulho (> #4)", 0.0, 100.0, step=0.1)
        pct_areia = max(0.0, min(100.0, 100.0 - pct_pedregulho))
        st.number_input("% areia (entre #4 e #200)", value=pct_areia, step=0.1, disabled=True)
    else:
        pct_pedregulho = 0.0
        pct_areia = 0.0

with col2:
    st.subheader("Plasticidade (Atterberg)")
    LL = st.number_input("Limite de Liquidez (LL)", 0.0, 200.0, step=0.1)
    LP = st.number_input("Limite de Plasticidade (LP)", 0.0, 200.0, step=0.1)
    IP = max(0.0, LL - LP)
    st.metric("IP = LL − LP", f"{IP:.2f}")
    # Gráfico de plasticidade simples
    fig, ax = plt.subplots()
    # Linha A (IP = 0,73*(LL-20)) — desenhada desde LL=0
    x_max = max(60, LL + 10)
    xs = [0, x_max]
    ys = [LINE_A_SLOPE*(xs[0]-20), LINE_A_SLOPE*(xs[1]-20)]
    ax.plot(xs, ys)  # linha A
    # Segmento horizontal tracejado: IP = 5 até intersectar a linha A
    IP_GUIDE = 5.0
    x_int = (IP_GUIDE / LINE_A_SLOPE) + 20.0
    ax.hlines(IP_GUIDE, 0, min(x_int, x_max), linestyles='--', linewidth=1)


    # Guias verticais pedidas
    ax.axvline(30, linestyle='--', linewidth=1)
    ax.axvline(50, linestyle='--', linewidth=1)

    # Ponto (LL, IP)
    ax.scatter([LL], [IP])

    # Limites dos eixos: começar em 0 para não exibir IP negativo
    y_line_end = LINE_A_SLOPE*(x_max - 20)
    y_max = max(40, IP + 10, y_line_end + 5, 5 + 10)  # garante espaço para a guia IP=5
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)

    # Rótulos das guias após definir limites
    ylim = ax.get_ylim()
    ax.text(30, ylim[1]*0.95, "LL=30", rotation=90, va='top', ha='right', fontsize=9)
    ax.text(50, ylim[1]*0.95, "LL=50", rotation=90, va='top', ha='right', fontsize=9)

    ax.set_xlabel("LL")
    ax.set_ylabel("IP")
    ax.set_title("Gráfico de Plasticidade (linha A e ponto da amostra)")
    st.pyplot(fig)

with col3:
    st.subheader("Características")
    allowed_grad = coarse and (fines < 5.0)
    use_grad = st.checkbox(
        "Usar Cu/Cc para decidir W/P (somente grossa com finos < 5%)",
        value=False,
        help="Cu/Cc só se aplicam a solos de granulação grossa (G/S) com finos < 5%.",
        disabled=not allowed_grad,
    )
    Cu = st.number_input("Cu (uniformidade)", 0.0, 1000.0, step=0.1, value=6.0, disabled=not (use_grad and allowed_grad))
    Cc = st.number_input("Cc (curvatura)", 0.0, 1000.0, step=0.01, value=1.5, disabled=not (use_grad and allowed_grad))    # Orgânico discreto (LL ≤ 50 → OL) primeiro; orgânico marcante (LL > 50 → OH) em seguida
    organico_discreto_allowed = (LL <= 50.0)
    organico_marcante_allowed = (LL > 50.0)
    organico_discreto = st.checkbox(
        "Evidência orgânica discreta (para classificar como OL)",
        value=False,
        disabled=not organico_discreto_allowed,
        help="Use quando LL ≤ 50 e houver indícios de matéria orgânica (cor/odor) ou redução do LL após secagem em estufa maior que ~30 pontos (critérios usuais em ASTM D2487/D4318)."
    )
    organico_marcante = st.checkbox(
        "Aspecto orgânico marcante (cor escura, odor, fibras)?",
        value=False,
        disabled=not organico_marcante_allowed,
        help="Use quando LL > 50 e houver forte evidência macroscópica (cor escura intensa, odor, fibras). Classifica como OH se marcado."
    )
    organico = (organico_discreto or organico_marcante)
    turfa = st.checkbox("Altamente orgânico (turfa)?", value=False, disabled=not organico,
                        help="Para materiais altamente orgânicos e fibrosos. Classifica como Pt.")

st.divider()
if st.button("Classificar (formulário acima)"):
    # Validação: se grossa, exigir soma ≈ 100 para pedregulho+areia
    if coarse:
        total_coarse = pct_pedregulho + pct_areia
        if abs(total_coarse - 100.0) > 1.0:
            st.error("A soma pedregulho + areia deve ser 100% (±1%) para a fração > #200.", icon="❌")
            st.stop()

    data = {
        "projeto": projeto, "tecnico": tecnico, "amostra": amostra,
        "pct_retido_200": pct_retido_200,
        "pct_pedregulho_coarse": pct_pedregulho,
        "pct_areia_coarse": pct_areia,
        "LL": LL, "LP": LP,
        "Cu": (Cu if (use_grad and allowed_grad) else None),
        "Cc": (Cc if (use_grad and allowed_grad) else None),
        "organico": organico, "turfa": turfa,
    }
    grupo, relatorio = classify_sucs(data)
    st.success(f"**Grupo SUCS:** {grupo}")
    st.text(relatorio)
    st.download_button("Baixar relatório (.txt)", relatorio, file_name=f"sucs_{amostra or 'amostra'}.txt")

st.divider()
st.subheader("Classificação em lote (CSV)")
st.caption("Colunas esperadas: projeto,tecnico,amostra,pct_retido_200,pct_pedregulho_coarse,pct_areia_coarse,LL,LP,Cu,Cc,organico,turfa")
uploaded = st.file_uploader("Envie o CSV", type=["csv"])
if uploaded is not None:
    df = pd.read_csv(uploaded)
    res = classify_dataframe(df)
    st.dataframe(res, use_container_width=True)
    buf = io.StringIO()
    res.to_csv(buf, index=False)
    st.download_button("Baixar resultados (CSV)", buf.getvalue(), file_name="resultados_sucs.csv")
