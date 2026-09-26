# -*- coding: utf-8 -*-
# Planilha-modelo para classificação MCT em lote (DNIT 259/2023-CLA).
from __future__ import annotations

import pandas as pd

from mct_core import EXEMPLOS

TEMPLATE_COLS = ["grupo_esperado", "descricao", "amostra", "c", "d", "Pi_ref",
                 "Pi_10", "Pi_15", "AF_10", "e", "serie"]


def template_df_mct() -> pd.DataFrame:
    rows = []
    for g, desc, p in EXEMPLOS:
        rec = {c: None for c in TEMPLATE_COLS}
        rec.update(grupo_esperado=g, descricao=desc, amostra=g, serie="simplificada", **p)
        rows.append(rec)
    return pd.DataFrame(rows, columns=TEMPLATE_COLS)


def build_excel_template_bytes_mct() -> bytes:
    from xlsx_utils import to_xlsx_bytes
    return to_xlsx_bytes(template_df_mct(), "modelo_mct")
