# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import pandas as pd

def build_excel_template_bytes_mct() -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_mcv = pd.DataFrame({
            "golpes": [1, 2, 3, 4, 5, 6],
            "mini_mcv": [6.0, 7.5, 9.0, 10.0, 12.0, 14.0],
            "altura_rel": [1.10, 1.12, 1.15, 1.18, 1.22, 1.26],
        })
        df_mcv.to_excel(writer, index=False, sheet_name="mini_mcv")

        df_comp = pd.DataFrame({
            "umidade_%": [6, 7, 8, 9, 10, 11, 12],
            "gamma_aparente": [1.86, 1.88, 1.91, 1.93, 1.94, 1.93, 1.90],
            "marca_ramo_seco": [1, 1, 1, 1, 0, 0, 0],
        })
        df_comp.to_excel(writer, index=False, sheet_name="compact_10")

        df_im = pd.DataFrame({
            "mini_mcv": [8, 9, 10, 11, 12],
            "perda_%": [2.5, 3.0, 4.2, 5.1, 6.0],
            "deltaH_mm": [2, 2, 2, 2, 2],
        })
        df_im.to_excel(writer, index=False, sheet_name="imersao")

    return buffer.getvalue()

def sample_inputs() -> list[dict]:
    return [
        {"C_": 1.8, "e_": 8.0},
        {"C_": 2.5, "e_": 15.0},
        {"C_": 3.8, "e_": 28.0},
        {"C_": 6.0, "e_": 42.0},
    ]
