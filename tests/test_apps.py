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
    at = _app("sucs_app.py")
    at.number_input[0].set_value(30.0).run()                  # % retido #200
    lls = [n for n in at.number_input if n.label.startswith("Limite")]
    lls[0].set_value(25.0); lls[1].set_value(19.0); at.run()
    _click(at, "Classificar")
    assert "ML-CL" in at.success[0].value


def test_trb_ip_decimal():
    at = _app("pages/trb_app.py")
    vals = [80.0, 60.0, 30.0, 30.0, 19.5]                     # #10, #40, #200, LL, LP
    for n, v in zip(at.number_input, vals):
        n.set_value(v)
    at.run()
    _click(at, "Classificar")
    assert "A-2-6" in at.success[0].value


def test_mct_individual():
    at = _app("pages/mct_app.py")
    _click(at, "Classificar")
    # padrão: c' = 1,20; d' = 50; AF = 47 → Pi' = Pi(15) = 20 → e' = 0,843 → LA'
    assert any("LA'" in m.value for m in at.markdown)


def test_mct_quadro():
    at = _app("pages/mct_app.py")
    at.radio[0].set_value("Quadro dos grupos").run()
    assert not at.exception
