
# streamlit_app.py
# App Streamlit para classificar solos pelo SUCS (conforme DNIT/SUCS)

import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from sucs_core import classify_sucs, classify_dataframe, LINE_A_SLOPE

st.set_page_config(page_title="Classificador SUCS (DNIT)", layout="wide")
st.title("Classificador SUCS — DNIT")

with st.sidebar:
    st.header("Projeto")
    projeto = st.text_input("Nome do projeto")
    tecnico = st.text_input("Técnico responsável")
    amostra = st.text_input("Código da amostra")

col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    st.subheader("Granulometria")
    pct_retido_200 = st.number_input("% retido na peneira #200", 0.0, 100.0, step=0.1)
    st.caption("≥ 50% retido ⇒ granulação grossa; < 50% ⇒ granulação fina.")
    st.markdown("**Na fração > #200 (se grossa):**")
    pct_pedregulho = st.number_input("% pedregulho (> #4)", 0.0, 100.0, step=0.1)
    pct_areia = st.number_input("% areia (entre #4 e #200)", 0.0, 100.0, step=0.1)

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
    st.subheader("Opcional")
    use_grad = st.checkbox("Usar Cu/Cc para decidir W/P quando finos < 5%", value=False)
    Cu = st.number_input("Cu (uniformidade)", 0.0, 1000.0, step=0.1, value=0.0 if not use_grad else 6.0)
    Cc = st.number_input("Cc (curvatura)", 0.0, 1000.0, step=0.01, value=1.5 if not use_grad else 1.5)
    organico = st.checkbox("Aspecto orgânico marcante (cor escura, odor, fibras)?", value=False)
    turfa = st.checkbox("Altamente orgânico (turfa)?", value=False) if organico else False

st.divider()
if st.button("Classificar (formulário acima)"):
    data = {
        "projeto": projeto, "tecnico": tecnico, "amostra": amostra,
        "pct_retido_200": pct_retido_200,
        "pct_pedregulho_coarse": pct_pedregulho,
        "pct_areia_coarse": pct_areia,
        "LL": LL, "LP": LP,
        "Cu": Cu if use_grad else None, "Cc": Cc if use_grad else None,
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
