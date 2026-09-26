import os

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = st_testing.AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _app(rel):
    at = AppTest.from_file(os.path.join(ROOT, rel), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def _click(at, label):
    next(b for b in at.button if b.label.startswith(label)).click().run()
    assert not at.exception, at.exception


def test_sucs_fino_zona_hachurada():
    at = _app("paginas/sucs.py")
    at.number_input(key="comum_p200").set_value(70.0)
    at.number_input(key="comum_ll").set_value(25.0)
    at.number_input(key="comum_lp").set_value(19.0).run()
    _click(at, "Classificar")
    assert any("ML-CL" in m.value for m in at.markdown)


def test_sucs_grosso_por_passante():
    at = _app("paginas/sucs.py")
    for k, v in [("sucs_p4", 75.0), ("comum_p200", 8.0), ("comum_ll", 30.0), ("comum_lp", 15.0)]:
        at.number_input(key=k).set_value(v)
    at.run()
    at.number_input(key="sucs_d10").set_value(0.1)
    at.number_input(key="sucs_d30").set_value(0.3)
    at.number_input(key="sucs_d60").set_value(0.9).run()
    _click(at, "Classificar")
    assert any("SW-SC" in m.value for m in at.markdown)


def test_sucs_modo_lote():
    at = _app("paginas/sucs.py")
    at.segmented_control(key="sucs_modo").set_value("Lote (CSV/Excel)").run()
    assert not at.exception


def test_trb_ip_decimal():
    at = _app("paginas/trb.py")
    vals = [80.0, 60.0, 30.0, 30.0, 19.5]                     # #10, #40, #200, LL, LP
    for n, v in zip(at.number_input, vals):
        n.set_value(v)
    at.run()
    _click(at, "Classificar")
    assert "A-2-6" in at.success[0].value


def test_mct_individual():
    at = _app("paginas/mct.py")
    _click(at, "Classificar")
    # padrão: c' = 1,20; d' = 50; AF = 47 → Pi' = Pi(15) = 20 → e' = 0,843 → LA'
    assert any("LA'" in m.value for m in at.markdown)


def test_mct_quadro():
    at = _app("paginas/mct.py")
    at.radio[0].set_value("Quadro dos grupos").run()
    assert not at.exception


def test_menu_navega_pelas_tres_paginas():
    at = _app("sucs_app.py")                                  # abre na página padrão (SUCS)
    assert at.title[0].value.startswith("Classificação SUCS")
    for pagina, titulo in [("paginas/trb.py", "Classificador TRB"), ("paginas/mct.py", "Classificação MCT"),
                           ("paginas/sucs.py", "Classificação SUCS")]:
        at.switch_page(pagina).run()
        assert not at.exception, at.exception
        assert at.title[0].value.startswith(titulo)


def test_projeto_persiste_entre_paginas():
    at = _app("sucs_app.py")
    at.text_input(key="meta_projeto").set_value("BR-393").run()
    at.switch_page("paginas/mct.py").run()
    assert not at.exception, at.exception
    assert at.text_input(key="meta_projeto").value == "BR-393"


# --- Preservação do que foi preenchido ao navegar pelo menu -----------------------------------

def _ir(at, pagina):
    at.switch_page(pagina).run()
    assert not at.exception, at.exception


def test_campos_preservados_ao_navegar_entre_as_tres_paginas():
    at = _app("sucs_app.py")
    at.number_input(key="sucs_p4").set_value(60.0)
    at.number_input(key="comum_p200").set_value(20.0)
    at.number_input(key="comum_ll").set_value(40.0)
    at.number_input(key="comum_lp").set_value(20.0).run()
    _ir(at, "paginas/trb.py")
    at.number_input(key="trb_p40").set_value(35.0)
    at.checkbox(key="comum_np").check().run()
    _ir(at, "paginas/mct.py")
    at.radio(key="mct_modo_e").set_value("Informar e' diretamente").run()
    at.number_input(key="mct_e").set_value(1.3)
    at.number_input(key="mct_c").set_value(0.9).run()
    _ir(at, "paginas/sucs.py")
    assert at.number_input(key="sucs_p4").value == 60.0
    assert at.number_input(key="comum_p200").value == 20.0
    assert at.checkbox(key="comum_np").value is True              # marcado no TRB
    _ir(at, "paginas/trb.py")
    assert at.number_input(key="trb_p40").value == 35.0
    _ir(at, "paginas/mct.py")
    assert at.radio(key="mct_modo_e").value == "Informar e' diretamente"
    assert at.number_input(key="mct_e").value == 1.3 and at.number_input(key="mct_c").value == 0.9


def test_granulometria_e_limites_compartilhados_sucs_trb():
    at = _app("sucs_app.py")
    at.number_input(key="comum_p200").set_value(45.0)
    at.number_input(key="comum_ll").set_value(38.0)
    at.number_input(key="comum_lp").set_value(22.0).run()
    _ir(at, "paginas/trb.py")
    assert (at.number_input(key="comum_p200").value, at.number_input(key="comum_ll").value,
            at.number_input(key="comum_lp").value) == (45.0, 38.0, 22.0)


def test_campo_condicional_volta_com_o_valor():
    at = _app("sucs_app.py")
    at.number_input(key="sucs_p4").set_value(75.0)
    at.number_input(key="comum_p200").set_value(8.0).run()       # grosso, finos 8% → graduação visível
    at.number_input(key="sucs_d10").set_value(0.2).run()
    at.number_input(key="comum_p200").set_value(30.0).run()      # finos > 12%: graduação some
    at.number_input(key="comum_p200").set_value(8.0).run()       # volta
    assert at.number_input(key="sucs_d10").value == 0.2


def test_resultado_preservado_e_marcado_quando_desatualizado():
    at = _app("sucs_app.py")
    _ir(at, "paginas/trb.py")
    for k, v in [("trb_p10", 80.0), ("trb_p40", 60.0), ("comum_p200", 30.0), ("comum_ll", 30.0), ("comum_lp", 19.5)]:
        at.number_input(key=k).set_value(v)
    at.run()
    _click(at, "Classificar")
    _ir(at, "paginas/mct.py")
    _ir(at, "paginas/trb.py")
    assert "A-2-6" in at.success[0].value and not at.warning
    at.number_input(key="comum_ll").set_value(45.0).run()
    assert any("alterados" in w.value for w in at.warning)


def test_resultado_mct_preservado():
    at = _app("sucs_app.py")
    _ir(at, "paginas/mct.py")
    _click(at, "Classificar")
    _ir(at, "paginas/sucs.py")
    _ir(at, "paginas/mct.py")
    assert any("LA'" in m.value for m in at.markdown)


def test_sucs_estado_inicial_sem_conclusoes():
    at = _app("paginas/sucs.py")
    botao = next(b for b in at.button if b.label == "Classificar")
    assert botao.disabled
    textos = " ".join(c.value for c in at.caption)
    assert "grossa" not in textos and "linha A" not in textos
