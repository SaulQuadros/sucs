import pytest

from trb_core import classify_trb, group_index


@pytest.mark.parametrize("args, esperado", [
    ((45, 25, 10, 30, 26), "A-1-a"),
    ((70, 45, 20, 35, 29), "A-1-b"),
    ((95, 80, 8, 0, 0, True), "A-3"),
    ((85, 60, 30, 35, 27), "A-2-4"),
    ((85, 60, 30, 45, 37), "A-2-5"),
    ((85, 60, 30, 35, 23), "A-2-6"),
    ((85, 60, 30, 45, 33), "A-2-7"),
    ((80, 60, 50, 35, 27), "A-4"),
    ((80, 60, 50, 50, 40), "A-5"),
    ((80, 60, 50, 35, 22), "A-6"),
    ((90, 70, 60, 55, 35), "A-7-5"),
    ((90, 70, 60, 55, 25), "A-7-6"),
])
def test_um_exemplo_por_grupo(args, esperado):
    assert classify_trb(*args).group == esperado


def test_ip_entre_10_e_11_nao_cai_em_lacuna():
    # antes: A-2-7 e A-7-6 com LL 30
    assert classify_trb(80, 60, 30, 30, 19.5).group == "A-2-6"
    assert classify_trb(90, 80, 60, 30, 19.5).group == "A-6"
    assert classify_trb(80, 60, 30, 30, 20.5).group == "A-2-4"


def test_a1_nao_tem_criterio_de_ll():
    # Quadro TRB: A-1 exige apenas IP ≤ 6
    assert classify_trb(40, 20, 10, 45, 41).group == "A-1-a"


def test_np_em_solo_granular_nao_a3():
    assert classify_trb(40, 20, 10, 0, 0, is_np=True).group == "A-1-a"
    assert classify_trb(85, 60, 30, 0, 0, is_np=True).group == "A-2-4"


def test_a3_exige_np():
    assert classify_trb(95, 80, 8, 20, 18).group != "A-3"


def test_indice_de_grupo():
    # IG = 0,2a + 0,005ac + 0,01bd
    assert group_index(10, 30, 5) == 0
    assert group_index(75, 60, 30) == 20
    # a=20, b=40, c=15, d=15 → 4 + 1,5 + 6 = 11,5 → 12
    assert group_index(55, 55, 25) == 12


def test_aviso_ig_usa_maximo_do_quadro():
    r = classify_trb(85, 60, 35, 35, 5)  # A-2-6 com IP 30 → IG = 0,01·20·20 = 4
    assert r.group == "A-2-6" and r.ig == 4 and r.aviso_ig == ""


def test_peneiras_invalidas():
    with pytest.raises(ValueError):
        classify_trb(40, 60, 10, 30, 20)


def test_lp_maior_que_ll():
    with pytest.raises(ValueError):
        classify_trb(80, 60, 50, 30, 35)


def test_planilha_modelo_confere():
    import pandas as pd
    from trb_core import EXEMPLOS, classify_dataframe_trb
    df = pd.DataFrame([dict(Grupo_esperado=g, **p) for g, _, p in EXEMPLOS])
    out = classify_dataframe_trb(df)
    assert list(out["Grupo_TRB"]) == list(out["Grupo_esperado"])


def test_detalhe_do_ig():
    r = classify_trb(90, 70, 55, 55, 30)       # a=20, b=40, c=15, d=15
    d = r.ig_detalhe
    assert (d["a"], d["b"], d["c"], d["d"]) == (20, 40, 15, 15)
    assert d["ig_bruto"] == pytest.approx(11.5) and r.ig == 12
    assert not r.granular and r.rationale[0].startswith("% passante na #200 = 55,0%")
