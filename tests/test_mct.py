import pandas as pd
import pytest

from mct_core import (MCTInput, classify_from_inputs, classify_mct, compute_e_prime,
                      pi_referencia, classify_dataframe_mct)


def test_formula_e_linha():
    # e' = ∛(Pi'/100 + 20/d')
    assert compute_e_prime(60, 40) == pytest.approx((0.40 + 20 / 60) ** (1 / 3))


@pytest.mark.parametrize("c, e, grupo", [
    (0.3, 0.9, "LA"), (0.3, 1.3, "LA"),          # abaixo da tracejada 1,4
    (1.0, 0.8, "LA'"), (2.0, 0.8, "LG'"),
    (0.2, 1.8, "NA"), (0.3, 1.5, "NA"),
    (0.9, 1.9, "NS'"), (0.35, 2.1, "NS'"),
    (1.0, 1.3, "NA'"), (1.6, 1.17, "NA'"),         # abaixo da linha NS'|NA' e c' < 1,7
    (2.0, 1.7, "NG'"), (1.6, 1.2, "NG'"), (1.6, 1.5, "NG'"), (1.8, 1.2, "NG'"),
])
def test_regioes_do_abaco(c, e, grupo):
    assert classify_mct(c, e)[0] == grupo


def test_fronteiras_cotadas():
    assert classify_mct(0.69, 1.15)[0] == "LA"
    assert classify_mct(0.70, 1.15)[0] == "LA'"
    assert classify_mct(0.70, 1.16)[0] == "NA'"
    assert classify_mct(1.50, 1.00)[0] == "LG'"


def test_pi_referencia_por_densidade():
    assert pi_referencia(120, 60, 49.0)[:2] == (120, "baixa")
    assert pi_referencia(120, 60, 47.5)[:2] == (60, "alta")
    with pytest.raises(ValueError):
        pi_referencia(120, None, 47.5)


def test_classificacao_completa():
    r = classify_from_inputs(MCTInput(c_=1.8, d_=60, pi_ref=40))
    assert r.group == "LG'" and r.e_ == pytest.approx(0.902, abs=1e-3)
    assert "Latossolos" in r.correlacao


def test_desempate_perto_da_fronteira():
    base = dict(c_=1.0, e_=1.13)  # LA' mas a 0,02 da fronteira
    assert classify_from_inputs(MCTInput(**base)).warnings
    r = classify_from_inputs(MCTInput(**base, pi_inclinacao_negativa=False, mcv_concavidade_para_cima=True))
    assert r.group == "NA'"
    r = classify_from_inputs(MCTInput(c_=1.0, e_=1.17, pi_inclinacao_negativa=True, mcv_concavidade_para_cima=True))
    assert r.group == "LA'"


def test_lote():
    df = pd.DataFrame([{"c": 1.8, "d": 60, "Pi_ref": 40}, {"c": 0.3, "d": 20, "Pi_10": 250, "Pi_15": 90, "AF_10": 50}])
    out = classify_dataframe_mct(df)
    assert list(out["Grupo_MCT"]) == ["LG'", "NA"]


def test_planilha_modelo_confere():
    from mct_core import EXEMPLOS
    df = pd.DataFrame([dict(grupo_esperado=g, **p) for g, _, p in EXEMPLOS])
    out = classify_dataframe_mct(df)
    assert list(out["Grupo_MCT"]) == list(out["grupo_esperado"])


# Resultados publicados em MEDRADO, W. A. Caracterização geotécnica de solo da região norte de Minas
# Gerais para aplicação em obras rodoviárias. Dissertação (Mestrado Profissional) — UFOP, Tabelas 4.7
# (ensaios COPPE/UFRJ) e 4.8 (ensaios LENC). O e' confere nos seis; S-1076 fica a 0,024 da linha
# NS'|NA' (publicado NA', leitura exata dá NS') e LENC 1 foi publicado como limítrofe NA'/NA.
PUBLICADOS = [
    ("S-1077", 0.18, 26.7, 430, 1.72, {"NA"}),
    ("S-1070", 0.25, 24.1, 380, 1.67, {"NA"}),
    ("S-1076", 0.62, 9.1, 265, 1.69, {"NA'", "NS'"}),
    ("LENC 1", 0.52, 69.5, 313, 1.51, {"NA'", "NA"}),
    ("LENC 2", 0.54, 17.5, 315, 1.62, {"NA'"}),
    ("LENC 3", 0.58, 23.8, 225, 1.45, {"NA'"}),
]


@pytest.mark.parametrize("nome, c, d, pi, e_pub, grupos", PUBLICADOS)
def test_resultados_publicados(nome, c, d, pi, e_pub, grupos):
    r = classify_from_inputs(MCTInput(c_=c, d_=d, pi_ref=pi))
    assert r.e_ == pytest.approx(e_pub, abs=0.01)   # publicados com 2 casas
    assert r.group in grupos


def test_aviso_de_fronteira_proxima():
    r = classify_from_inputs(MCTInput(c_=0.62, d_=9.1, pi_ref=265))      # S-1076
    assert r.group == "NS'" and any("NS' | NA'" in w for w in r.warnings)
    r = classify_from_inputs(MCTInput(c_=1.8, d_=60, pi_ref=40))         # longe de fronteiras
    assert not r.warnings
