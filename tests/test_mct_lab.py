"""Modo laboratório MCT validado com dois conjuntos de dados publicados:

1. DNIT 258/2023-ME, Anexo A, Figura A8 (planilha da série Simplificada, adaptada de Villibor e Alves, 2019),
   com c' = 1,20 (Figura A10) e d' = 75 kg/m³/% (Figura A11) obtidos graficamente pela norma.
2. BARBOSA, D. P. (2021). Estudo da metodologia MCT, com apresentação de exemplo de classificação de um solo.
   TCC — UFJF (série de Parsons): c' = 2,45 e e' = 0,928 → LG' no TCC; c' = 2,22, d' = 40, Pi' = 26,4%,
   e' = 0,914 → LG' na releitura do professor (PEC/UFJF, 2025).
"""
import pytest

from mct_core import MCTInput, classify_from_inputs
from mct_lab import (CorpoDeProva, afundamentos, calcular, de_tabelas, exemplo_barbosa_2021, exemplo_dnit_258,
                     mini_mcv, para_tabelas)


def test_dnit_planilha_a8():
    serie, cps, _ = exemplo_dnit_258()
    R = calcular(cps, serie)
    # MEAS e Pi idênticos aos da planilha da norma
    assert [round(cp.meas(3)) for cp in cps] == [1509, 1500, 1508, 1407, 1305]
    assert [round(cp.pi, 1) for cp in cps] == [143.5, 87.3, 40.5, 91.1, 112.5]
    # Mini-MCV: norma 7,8 · 10,5 · 13,1 · 15,0 · 18,0 (lidos em curvas suavizadas)
    assert [round(R.mcv[cp.nome], 1) for cp in cps] == [8.0, 11.0, 13.2, 15.0, 18.0]
    assert R.c_ == pytest.approx(1.20, abs=0.06)          # norma: 1,20
    assert 60 <= R.d_ <= 75                               # norma: 75 (leitura gráfica); regressão: ≈ 64
    assert R.densidade == "baixa" and R.mcv_pi == 10


def test_barbosa_2021_parsons():
    serie, cps, _ = exemplo_barbosa_2021()
    R = calcular(cps, serie)
    assert [round(R.mcv[cp.nome], 2) for cp in cps] == [17.79, 13.87, 10.96, 8.56, 6.76]
    assert [round(cp.meas(12)) for cp in cps] == [1316, 1389, 1483, 1492, 1441]
    assert 2.2 <= R.c_ <= 2.45                            # releitura 2,22; TCC 2,45
    assert R.d_ == pytest.approx(40, abs=2)               # 40
    assert R.af10 == pytest.approx(52.2, abs=0.1) and R.densidade == "baixa"
    assert R.pi_ref == pytest.approx(26.4, abs=1.2)       # 26,4
    assert R.crit_pi_negativa is True and R.crit_concavidade is True
    res = classify_from_inputs(MCTInput(c_=R.c_, d_=R.d_, pi_ref=R.pi_ref))
    assert res.e_ == pytest.approx(0.914, abs=0.01) and res.group == "LG'"


def test_afundamento_das_duas_series():
    cp = CorpoDeProva("x", 20, {1: 60.0, 4: 55.0, 16: 50.0, 64: 49.0})
    assert afundamentos(cp, "Parsons") == [(1, 5.0), (4, 5.0), (16, 1.0)]
    assert afundamentos(cp, "Simplificada") == [(1, 11.0), (4, 6.0), (16, 1.0)]
    assert mini_mcv([(4, 5.0), (16, 1.0)]) == pytest.approx(6.02 + 0.75 * 6.02, abs=0.01)


def test_tabelas_ida_e_volta():
    serie, cps, _ = exemplo_barbosa_2021()
    alt, dados = para_tabelas(serie, cps)
    de_volta = de_tabelas(alt, dados)
    assert [c.alturas for c in de_volta] == [c.alturas for c in cps]
    assert [c.pi for c in de_volta] == [c.pi for c in cps]


def test_poucos_dados_e_erro():
    with pytest.raises(ValueError):
        calcular([CorpoDeProva("x", 20, {1: 60.0, 4: 55.0})], "Parsons")


def test_c_na_curva_interpolada_com_mini_mcv_10():
    import numpy as np
    for fn in (exemplo_barbosa_2021, exemplo_dnit_258):
        serie, cps, _ = fn()
        R = calcular(cps, serie)
        cx, cy = zip(*R.c_detalhe["curva"])
        assert float(np.interp(10.0, cx, cy)) == pytest.approx(2.0, abs=1e-9)    # passa por (10; 2 mm)
        (xa, ya), (xb, yb) = R.c_detalhe["linha"]
        assert (ya - yb) / (xb - xa) == pytest.approx(R.c_, rel=1e-9)            # triângulo = c′
        (ha, ma), (hb, mb) = R.d_detalhe["linha"]
        assert (mb - ma) / (hb - ha) == pytest.approx(R.d_, rel=1e-9)            # triângulo = d′
