# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Gerador de Ficha Geotécnica (PDF) – Didático
- Escolhe uma classe SUCS aleatória (probabilidade igual) dentre: GW, GP, GM, GC, SW, SP, SM, SC, ML, CL, MH, CH
- Gera granulometria coerente, LL/LP (quando aplicável) e NP quando apropriado
- Renderiza 1 página PDF com cabeçalho, tabela de peneiramento e curva granulométrica (sem declarar a classe)
- Não calcula nem mostra PI (IP).
"""
import io, random, datetime
from typing import Tuple, Dict
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Peneiras padrão (mm)
SIEVES_MM = np.array([75.0, 37.5, 19.0, 9.5, 4.75, 2.0, 0.425, 0.075], dtype=float)
SIEVES_LBL = ["3\" (75 mm)", "1½\" (37,5 mm)", "¾\" (19 mm)", "3/8\" (9,5 mm)",
              "#4 (4,75 mm)", "#10 (2,0 mm)", "#40 (0,425 mm)", "#200 (0,075 mm)"]
SUCS_CLASSES = ["GW","GP","GM","GC","SW","SP","SM","SC","ML","CL","MH","CH"]

def _a_line(LL: float) -> float:
    return 0.73*(LL - 20.0)

def _ensure_monotone(p: np.ndarray) -> np.ndarray:
    out = p.copy()
    for i in range(1, len(out)):
        if out[i] < out[i-1]:
            out[i] = out[i-1]
    return np.clip(out, 0.0, 100.0)

def _interp_D_at_percent(sieves: np.ndarray, pass_pct: np.ndarray, target_pct: float) -> float:
    x = np.log10(sieves); y = pass_pct
    if target_pct <= y.min():
        i = int(np.argmin(y)); j = max(i-1, 0)
    elif target_pct >= y.max():
        i = int(np.argmax(y)); j = min(i+1, len(y)-1)
    else:
        idx = int(np.searchsorted(y, target_pct, side="left"))
        i = max(idx-1, 0); j = min(idx, len(y)-1)
    if i == j:
        return float(10**x[i])
    t = (target_pct - y[i]) / (y[j] - y[i] + 1e-12)
    x_t = x[i] + t*(x[j]-x[i])
    return float(10**x_t)

def _make_curve_from_anchors(p4, p10, p40, p200) -> np.ndarray:
    anchors_D = np.array([75.0, 4.75, 2.0, 0.425, 0.075], dtype=float)
    anchors_P = np.array([100.0, p4,  p10,  p40,  p200], dtype=float)
    x_all = np.log10(SIEVES_MM)[::-1]
    x_anc = np.log10(anchors_D)[::-1]
    p_all = np.interp(x_all, x_anc, anchors_P)[::-1]
    return _ensure_monotone(p_all)

def _sample_LL_LP_for(symbol: str):
    if symbol in ("GW","GP","SW","SP"):  # limpos
        return True, None, None
    if symbol in ("GM","SM","ML"):       # abaixo da A-line
        LL = random.uniform(25.0, 45.0)
        PI_A = _a_line(LL); PI = max(1.0, PI_A - random.uniform(3.0, 8.0))
        LP = max(0.0, LL - PI)
        return False, round(LL, 1), round(LP, 1)
    if symbol in ("GC","SC","CL"):       # acima da A-line (LL moderado)
        LL = random.uniform(28.0, 48.0)
        PI_A = _a_line(LL); PI = PI_A + random.uniform(3.0, 10.0)
        LP = max(0.0, LL - PI)
        return False, round(LL, 1), round(LP, 1)
    if symbol == "MH":                   # LL alto, abaixo da A-line
        LL = random.uniform(50.0, 70.0)
        PI_A = _a_line(LL); PI = max(1.0, PI_A - random.uniform(3.0, 10.0))
        LP = max(0.0, LL - PI)
        return False, round(LL, 1), round(LP, 1)
    if symbol == "CH":                   # LL alto, acima da A-line
        LL = random.uniform(50.0, 80.0)
        PI_A = _a_line(LL); PI = PI_A + random.uniform(3.0, 12.0)
        LP = max(0.0, LL - PI)
        return False, round(LL, 1), round(LP, 1)
    return False, None, None

def _gen_coarse_clean(symbol: str):
    is_gravel = symbol.startswith("G")
    p4  = random.uniform(20.0, 45.0) if is_gravel else random.uniform(60.0, 90.0)
    p10 = min(98.0, p4 + random.uniform(5.0, 25.0))
    p40 = min(99.0, p10 + random.uniform(5.0, 30.0))
    p200 = min(4.0, random.uniform(0.0, 4.0))  # finos < 5%
    curve = _make_curve_from_anchors(p4, p10, p40, p200)
    # Ajuste Cu/Cc (GW/SW bem graduados; GP/SP mal graduados) – simplificado
    D10 = _interp_D_at_percent(SIEVES_MM, curve, 10.0)
    D30 = _interp_D_at_percent(SIEVES_MM, curve, 30.0)
    D60 = _interp_D_at_percent(SIEVES_MM, curve, 60.0)
    Cu = D60 / max(D10, 1e-6); Cc = (D30**2) / max(D10*D60, 1e-6)
    if symbol in ("GW","SW"):
        need_Cu = 4.0 if is_gravel else 6.0
        for _ in range(6):
            if (Cu >= need_Cu) and (1.0 <= Cc <= 3.0):
                break
            p10 = min(98.0, p4 + random.uniform(8.0, 30.0))
            p40 = min(99.0, p10 + random.uniform(10.0, 30.0))
            curve = _make_curve_from_anchors(p4, p10, p40, p200)
            D10 = _interp_D_at_percent(SIEVES_MM, curve, 10.0)
            D30 = _interp_D_at_percent(SIEVES_MM, curve, 30.0)
            D60 = _interp_D_at_percent(SIEVES_MM, curve, 60.0)
            Cu = D60 / max(D10, 1e-6); Cc = (D30**2) / max(D10*D60, 1e-6)
    else:
        need_Cu = 4.0 if is_gravel else 6.0
        if (Cu >= need_Cu) and (1.0 <= Cc <= 3.0):
            p10 = p4 + random.uniform(2.0, 8.0)
            p40 = p10 + random.uniform(2.0, 8.0)
            curve = _make_curve_from_anchors(p4, p10, p40, p200)
    meta = {"P4": float(p4), "P10": float(p10), "P40": float(p40), "P200": float(p200)}
    return curve, meta

def _gen_coarse_with_fines(symbol: str):
    is_gravel = symbol.startswith("G")
    p4  = random.uniform(20.0, 45.0) if is_gravel else random.uniform(60.0, 90.0)
    p10 = min(98.0, p4 + random.uniform(10.0, 30.0))
    p40 = min(99.0, p10 + random.uniform(10.0, 30.0))
    p200 = random.uniform(12.0, 35.0)
    p200 = min(p200, p40 - 1.0)
    curve = _make_curve_from_anchors(p4, p10, p40, p200)
    np_flag, LL, LP = _sample_LL_LP_for(symbol)
    meta = {"P4": float(p4), "P10": float(p10), "P40": float(p40), "P200": float(p200)}
    return curve, meta, (np_flag, LL, LP)

def _gen_fine_soil(symbol: str):
    p200 = random.uniform(55.0, 95.0)
    p40  = max(p200 + random.uniform(2.0, 10.0), min(99.0, p200 + 5.0))
    p10  = max(p40  + random.uniform(2.0, 10.0), min(99.0, p40  + 5.0))
    p4   = max(p10  + random.uniform(1.0,  5.0), min(99.0, p10   + 2.0))
    p4   = min(p4, 99.5)
    curve = _make_curve_from_anchors(p4, p10, p40, p200)
    np_flag, LL, LP = _sample_LL_LP_for(symbol)
    meta = {"P4": float(p4), "P10": float(p10), "P40": float(p40), "P200": float(p200)}
    return curve, meta, (np_flag, LL, LP)

def generate_random_sucs_pdf(seed: int|None=None) -> Tuple[bytes, Dict[str,str]]:
    if seed is not None:
        random.seed(seed); np.random.seed(seed)
    symbol = random.choice(SUCS_CLASSES)
    if symbol in ("GW","GP","SW","SP"):
        curve, meta = _gen_coarse_clean(symbol); np_flag, LL, LP = True, None, None
    elif symbol in ("GM","GC","SM","SC"):
        curve, meta, (np_flag, LL, LP) = _gen_coarse_with_fines(symbol)
    else:
        curve, meta, (np_flag, LL, LP) = _gen_fine_soil(symbol)
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
        now = datetime.datetime.now()
        amostra = f"E{random.randint(100,999)}"
        fig.suptitle("FICHA GEOTÉCNICA – AMOSTRA", fontsize=14, fontweight="bold", y=0.98)
        header_text = (
            f"Código: {amostra}\n"
            f"Data: {now.strftime('%d/%m/%Y')}\n"
            f"Observação: Ficha didática gerada automaticamente – use o App para classificar."
        )
        fig.text(0.03, 0.88, header_text, fontsize=10, va="top")
        # Atterberg (sem PI)
        if np_flag:
            att_text = "Limites de Atterberg: NP (não plástico)"
        else:
            att_text = f"Limites de Atterberg: LL = {LL:.1f}  |  LP = {LP:.1f}"
        fig.text(0.03, 0.78, att_text, fontsize=10, va="top")
        # Tabela peneiras
        table_data = [["Peneira", "% Passante"]]
        for lbl, mm, p in zip(SIEVES_LBL, SIEVES_MM, curve):
            table_data.append([lbl, f"{p:.1f}"])
        ax_table = fig.add_axes([0.03, 0.08, 0.42, 0.65]); ax_table.axis("off")
        the_table = ax_table.table(cellText=table_data, loc="center", cellLoc="center")
        the_table.auto_set_font_size(False); the_table.set_fontsize(9); the_table.scale(1.2, 1.4)
        # Curva granulométrica
        ax = fig.add_axes([0.50, 0.12, 0.47, 0.70])
        ax.set_xscale("log"); ax.set_xlim(0.05, 100); ax.set_ylim(0, 100)
        ax.grid(True, which="both", linestyle="--", alpha=0.4)
        ax.plot(SIEVES_MM, curve, marker="o", linewidth=1.5)
        ax.set_xlabel("Diâmetro (mm) – escala log"); ax.set_ylabel("% passante")
        ax.set_title("Curva granulométrica")
        fig.text(0.03, 0.04, "A classe SUCS não é exibida nesta ficha.", fontsize=9)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    return buf.getvalue(), {"amostra": amostra, "sucs_sorteada": symbol}
