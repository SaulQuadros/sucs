# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple, List
import math
import numpy as np
import matplotlib.pyplot as plt

@dataclass
class MCTInput:
    C_: Optional[float] = None
    d_: Optional[float] = None
    Pi: Optional[float] = None
    e_: Optional[float] = None
    meta: Dict[str, Any] = None

@dataclass
class MCTResult:
    group: str
    e_: float
    C_: float
    rationale: List[str]
    props: Dict[str, Any]
    cbr_tipico: Optional[str]
    warnings: List[str]
    is_demo: bool = False

def _validate_inputs(inp: MCTInput) -> List[str]:
    w: List[str] = []
    if inp.C_ is not None and not (0.0 <= inp.C_ <= 10.0):
        w.append("Valor de C' fora da faixa usual [0, 10].")
    if inp.d_ is not None and not (0.0 <= inp.d_ <= 50.0):
        w.append("Valor de d' fora da faixa [0, 50] (×10³).")
    if inp.Pi is not None and not (0.0 <= inp.Pi <= 100.0):
        w.append("Valor de Pi fora da faixa [0, 100] %.")
    if inp.e_ is not None and not (0.0 <= inp.e_ <= 100.0):
        w.append("Valor de e' fora da faixa [0, 100].")
    return w

def compute_e_prime(d_: float, Pi: float) -> float:
    """PLACEHOLDER (DEMO): substitua pela expressão OFICIAL do Manual DNIT (seção do ábaco)."""
    if d_ is None or Pi is None:
        raise ValueError("Para calcular e', informe d' e Pi.")
    for x in (d_, Pi):
        if not isinstance(x, (int, float)) or math.isnan(float(x)):
            raise ValueError("d' e Pi devem ser números.")
        if x < 0:
            raise ValueError("d' e Pi não podem ser negativos.")
    return float(0.6 * d_ + 0.4 * Pi)

def classify_mct(e_: float, C_: float) -> Tuple[str, List[str]]:
    """PLACEHOLDER (DEMO): substitua pelos limites oficiais (retas/inequações do ábaco)."""
    r: List[str] = []
    if e_ < 10 and C_ < 2:
        g = "NA (DEMO)"; r.append("Região provisória: e'<10 e C'<2.")
    elif e_ < 20 and C_ < 4:
        g = "NS (DEMO)"; r.append("Região provisória: 10≤e'<20 e C'<4.")
    elif e_ < 35:
        g = "LA (DEMO)"; r.append("Região provisória: 20≤e'<35.")
    else:
        g = "LG (DEMO)"; r.append("Região provisória: e'≥35 ou C' elevado.")
    r.append("ATENÇÃO: usar limites oficiais do ábaco MCT do DNIT.")
    return g, r

def typical_properties_for(group: str) -> Dict[str, Any]:
    base = {
        "NA": {"permeabilidade": "baixa a média", "plasticidade": "baixa", "expansão": "baixa"},
        "NS": {"permeabilidade": "média", "plasticidade": "média", "expansão": "média"},
        "LA": {"permeabilidade": "média a alta", "plasticidade": "média-alta", "expansão": "média"},
        "LG": {"permeabilidade": "alta", "plasticidade": "alta", "expansão": "alta"},
    }
    key = group.split()[0]
    return base.get(key, {})

def cbr_range_for(group: str) -> Optional[str]:
    faixas = {
        "NA": "CBR típico: 5–10% (ilustrativo)",
        "NS": "CBR típico: 8–20% (ilustrativo)",
        "LA": "CBR típico: 15–40% (ilustrativo)",
        "LG": "CBR típico: 30–80% (ilustrativo)",
    }
    return faixas.get(group.split()[0])

def classify_from_inputs(inp: MCTInput, *, allow_demo: bool = True) -> MCTResult:
    w = _validate_inputs(inp)
    C = inp.C_
    e = inp.e_
    if e is None:
        if inp.d_ is None or inp.Pi is None:
            raise ValueError("Informe e' ou (d' e Pi) para classificar.")
        e = compute_e_prime(inp.d_, inp.Pi)
    if C is None:
        raise ValueError("Informe C' para classificar.")
    if allow_demo:
        g, r = classify_mct(e, C); demo = True
    else:
        raise NotImplementedError("Classificação oficial do ábaco ainda não implementada.")
    return MCTResult(group=g, e_=float(e), C_=float(C), rationale=r,
                     props=typical_properties_for(g), cbr_tipico=cbr_range_for(g),
                     warnings=w, is_demo=demo)

def plot_mct_abaco(ax=None, show_demo_limits: bool = True):
    created = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5)); created = True
    ax.set_xlabel("C' (inclinação no mini-MCV=10)")
    ax.set_ylabel("e' (índice composto)")
    ax.set_xlim(0, 10); ax.set_ylim(0, 60)
    ax.grid(True, ls="--", alpha=0.35)
    if show_demo_limits:
        ax.plot([0,10],[10,10], lw=1, alpha=0.7); ax.plot([0,10],[20,20], lw=1, alpha=0.7); ax.plot([0,10],[35,35], lw=1, alpha=0.7)
        ax.plot([2,2],[0,60], lw=1, alpha=0.7); ax.plot([4,4],[0,60], lw=1, alpha=0.7)
        ax.text(1.0,5.0,"NA (DEMO)", fontsize=9); ax.text(2.5,12.0,"NS (DEMO)", fontsize=9)
        ax.text(3.0,27.0,"LA (DEMO)", fontsize=9); ax.text(6.0,45.0,"LG (DEMO)", fontsize=9)
    ax.set_title("Ábaco MCT – ESQUELETO (limites provisórios)")
    if created: return fig, ax
    return ax

def plot_point_on_abaco(C_: float, e_: float, ax=None, annotate: bool = True):
    created = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(6,5)); created=True
    plot_mct_abaco(ax=ax, show_demo_limits=True)
    ax.scatter([C_],[e_], s=60, zorder=5)
    if annotate:
        ax.annotate(f"(C'={C_:.2f}, e'={e_:.2f})", (C_, e_), xytext=(5,8), textcoords="offset points", fontsize=9)
    if created: return fig, ax
    return ax
