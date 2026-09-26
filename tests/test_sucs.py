import pandas as pd
import pytest

from sucs_core import classify_sucs, classify_dataframe, cu_cc, plasticity_zone


def s(**k):
    return classify_sucs(k)[0]


@pytest.mark.parametrize("kw, esperado", [
    (dict(pct_retido_200=97, pct_pedregulho_coarse=70, pct_areia_coarse=30, NP=True, Cu=8, Cc=2.0), "GW"),
    (dict(pct_retido_200=96, pct_pedregulho_coarse=60, pct_areia_coarse=40, NP=True, Cu=2, Cc=0.6), "GP"),
    (dict(pct_retido_200=75, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=40, LP=27), "GM"),
    (dict(pct_retido_200=75, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=40, LP=20), "GC"),
    (dict(pct_retido_200=97, pct_pedregulho_coarse=30, pct_areia_coarse=70, NP=True, Cu=7, Cc=1.5), "SW"),
    (dict(pct_retido_200=96, pct_pedregulho_coarse=30, pct_areia_coarse=70, NP=True, Cu=3, Cc=0.8), "SP"),
    (dict(pct_retido_200=75, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=40, LP=27), "SM"),
    (dict(pct_retido_200=75, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=40, LP=20), "SC"),
    (dict(pct_retido_200=30, LL=35, LP=25), "ML"),
    (dict(pct_retido_200=30, LL=35, LP=22), "CL"),
    (dict(pct_retido_200=30, LL=35, LP=25, organico=True), "OL"),
    (dict(pct_retido_200=30, LL=70, LP=40), "MH"),
    (dict(pct_retido_200=30, LL=70, LP=25), "CH"),
    (dict(pct_retido_200=30, LL=60, LP=35, organico=True), "OH"),
    (dict(pct_retido_200=10, LL=150, LP=50, organico=True, turfa=True), "PT"),
])
def test_um_exemplo_por_grupo(kw, esperado):
    assert s(**kw) == esperado


def test_ip_baixo_com_ll_baixo_e_silte():
    # antes: linha A negativa para LL < 20 → CL
    assert s(pct_retido_200=30, LL=15, LP=13) == "ML"


def test_zona_hachurada():
    assert s(pct_retido_200=30, LL=25, LP=19) == "ML-CL"
    assert s(pct_retido_200=70, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=25, LP=19) == "SM-SC"
    assert s(pct_retido_200=70, pct_pedregulho_coarse=70, pct_areia_coarse=30, LL=25, LP=19) == "GM-GC"


def test_ip_entre_4_e_7_abaixo_da_linha_a_e_silte():
    assert plasticity_zone(40, 34) == "M"   # IP 6 < linha A (14,6)


def test_finos_5_a_12_simbolo_duplo_valido():
    assert s(pct_retido_200=92, pct_pedregulho_coarse=30, pct_areia_coarse=70,
             LL=30, LP=15, Cu=7, Cc=2) == "SW-SC"
    assert s(pct_retido_200=92, pct_pedregulho_coarse=70, pct_areia_coarse=30,
             LL=30, LP=26, Cu=2, Cc=2) == "GP-GM"


def test_finos_5_a_12_sem_cu_cc_indica_pendencia():
    g = s(pct_retido_200=92, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=30, LP=15)
    assert g == "SW/SP-SC"


def test_ll_50_e_baixo():
    # Tabela 5: L quando LL ≤ 50
    assert s(pct_retido_200=10, LL=50, LP=20) == "CL"
    assert s(pct_retido_200=10, LL=50.5, LP=20) == "CH"


def test_50_por_cento_retido_e_fino():
    # Tabela 5: grosso = mais de 50% retido; fino = 50% ou mais passando
    assert s(pct_retido_200=50, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=35, LP=22) == "CL"


def test_cu_cc_por_diametros():
    cu, cc = cu_cc(0.1, 0.35, 0.9)
    assert cu == pytest.approx(9.0) and cc == pytest.approx(0.35**2 / 0.09)
    assert s(pct_retido_200=97, pct_pedregulho_coarse=30, pct_areia_coarse=70, NP=True,
             D10=0.1, D30=0.3, D60=0.9) == "SW"


def test_lote_com_celulas_vazias_nao_quebra():
    df = pd.DataFrame([
        dict(pct_retido_200=97, pct_pedregulho_coarse=70, pct_areia_coarse=30, LL=None, LP=None, Cu=8, Cc=2),
        dict(pct_retido_200=None, pct_pedregulho_coarse=70, pct_areia_coarse=30),
    ])
    res = classify_dataframe(df)
    assert list(res["grupo"]) == ["GW", "ERRO"]


def test_planilha_modelo_confere():
    from sucs_core import EXEMPLOS
    for g, _, p in EXEMPLOS:
        assert s(**p) == g, g


def test_entrada_por_passante_equivale_a_retido():
    from sucs_core import classify_sucs_result
    # 8% passando na #200, 75% na #4 → retido 92%, pedregulho 25, areia 67 → S
    r = classify_sucs_result(dict(P4=75, P200=8, LL=30, LP=15, Cu=7, Cc=2))
    assert r.group == "SW-SC" and r.pct_finos == pytest.approx(8.0)
    assert s(pct_retido_200=92, pct_pedregulho_coarse=25, pct_areia_coarse=67, LL=30, LP=15, Cu=7, Cc=2) == "SW-SC"


def test_passante_4_menor_que_200_e_erro():
    with pytest.raises(ValueError):
        s(P4=10, P200=20, LL=30, LP=20)


def test_resultado_estruturado():
    from sucs_core import classify_sucs_result
    r = classify_sucs_result(dict(P4=75, P200=8, LL=30, LP=15))
    assert r.group == "SW/SP-SC" and not r.completo
    assert any("Cu e Cc" in a for a in r.avisos)
    assert r.passos[0].startswith("92,0% retido")          # vírgula decimal
    assert "SC: 5 a 20" in r.cbr and r.trb[0] == "SW"



def test_sucs_lp_maior_que_ll_e_np():
    # DNER-ME 082/94, item 4
    assert s(P4=100, P200=70, LL=30, LP=35) == "ML"
    with pytest.raises(ValueError, match="LP = 0"):
        s(P4=100, P200=70, LL=30, LP=0)
