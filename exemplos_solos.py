# exemplos_solos.py
# Exemplos numéricos compartilhados pelas páginas SUCS e TRB (modo "Uma amostra").
# Cada exemplo traz a granulometria completa (nº 4, 10, 40 e 200, e diâmetros D10/D30/D60 quando a graduação
# importa) e os limites, de modo que o mesmo solo possa ser classificado nos dois sistemas.
# Carregar um exemplo preenche os campos (chaves de keep) e classifica automaticamente nas duas páginas.
import streamlit as st

from estado import definir_valor, keep

# Chaves dos widgets de "Uma amostra" (SUCS e TRB). Campos ausentes em um exemplo voltam ao padrão.
PADRAO = {
    "sucs_p4": None, "trb_p10": None, "trb_p40": None, "comum_p200": None,
    "comum_ll": None, "comum_lp": None, "comum_np": False,
    "sucs_modo_grad": "D10, D30, D60 (mm)", "sucs_d10": None, "sucs_d30": None, "sucs_d60": None,
    "sucs_cu": None, "sucs_cc": None, "sucs_organico": False, "sucs_turfa": False,
}

# (título, descrição, valores, SUCS esperado, TRB esperado) — os esperados são conferidos nos testes.
EXEMPLOS = [
    ("Exemplo 1 — Pedregulho arenoso bem graduado",
     "Material de jazida para base/sub-base: pouco fino e não plástico. Passantes: nº 4 = 45%, nº 10 = 32%, "
     "nº 40 = 16%, nº 200 = 4%; D10 = 0,20 mm, D30 = 1,8 mm, D60 = 9,5 mm; NP.",
     {"sucs_p4": 45.0, "trb_p10": 32.0, "trb_p40": 16.0, "comum_p200": 4.0, "comum_np": True,
      "sucs_d10": 0.20, "sucs_d30": 1.8, "sucs_d60": 9.5},
     "GW", "A-1-a (IG 0)"),
    ("Exemplo 2 — Areia argilosa",
     "Solo arenoso com finos plásticos, comum em subleitos. Passantes: nº 4 = 85%, nº 10 = 72%, nº 40 = 48%, "
     "nº 200 = 22%; LL = 32%, LP = 18%.",
     {"sucs_p4": 85.0, "trb_p10": 72.0, "trb_p40": 48.0, "comum_p200": 22.0, "comum_ll": 32.0, "comum_lp": 18.0},
     "SC", "A-2-6 (IG 0)"),
    ("Exemplo 3 — Argila de alta plasticidade",
     "Solo fino, argiloso, de comportamento ruim como subleito. Passantes: nº 4 = 100%, nº 10 = 98%, "
     "nº 40 = 90%, nº 200 = 78%; LL = 52%, LP = 26%.",
     {"sucs_p4": 100.0, "trb_p10": 98.0, "trb_p40": 90.0, "comum_p200": 78.0, "comum_ll": 52.0, "comum_lp": 26.0},
     "CH", "A-7-6 (IG 17)"),
]
TITULOS = [e[0] for e in EXEMPLOS]
PAGINAS = ("sucs", "trb")
_AUTO = "__auto_classificar__"


def _aplicar(valores: dict) -> None:
    for chave, padrao in PADRAO.items():
        definir_valor(chave, valores.get(chave, padrao))
    for pagina in PAGINAS:
        st.session_state.pop(f"__resultado__{pagina}", None)


def _carregar() -> None:
    _, _, valores, _, _ = EXEMPLOS[TITULOS.index(st.session_state["exemplo_solo"])]
    _aplicar(valores)
    for pagina in PAGINAS:
        st.session_state[_AUTO + pagina] = True


def _limpar() -> None:
    _aplicar({})
    for pagina in PAGINAS:
        st.session_state.pop(_AUTO + pagina, None)


def seletor_exemplos(pagina: str) -> None:
    """Linha com o seletor de exemplos, acima dos quadros de entrada."""
    with st.expander("📘 Exemplos numéricos — carregar um solo pronto"):
        st.caption("Os mesmos três solos servem para SUCS e TRB: ao carregar, os campos das duas páginas são "
                   "preenchidos e classificados. Depois, altere os valores à vontade e clique em **Classificar**.")
        c1, c2, c3 = st.columns([3, 1, 1], vertical_alignment="bottom")
        titulo = c1.selectbox("Exemplo", TITULOS, **keep("exemplo_solo", TITULOS[0]))
        c2.button("Carregar exemplo", on_click=_carregar, key=f"exemplo_carregar_{pagina}", type="primary",
                  use_container_width=True)
        c3.button("Limpar campos", on_click=_limpar, key=f"exemplo_limpar_{pagina}", use_container_width=True)
        st.caption(EXEMPLOS[TITULOS.index(titulo)][1])


def classificar_automatico(pagina: str) -> bool:
    """True uma única vez depois de carregar um exemplo (dispara a classificação na página)."""
    return st.session_state.pop(_AUTO + pagina, False)
