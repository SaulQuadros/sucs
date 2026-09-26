# trb_core.py
# Classificação TRB (HRB/AASHTO) conforme a Tabela 4 do Manual de Pavimentação DNIT (IPR-719/2006).
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import math

from formato import fmt

from trb_defs import (get_definicao, get_subleito_text, ig_tipico_max, get_materiais,
                      cbr_for_trb, sucs_provavel)

# Rótulo rápido por grupo (para UI)
GROUP_DESC = {
    "A-1-a": "Pedregulho/fragmentos de pedra com ou sem finos bem graduados; excelente a bom como subleito.",
    "A-1-b": "Areia grossa com ou sem aglutinante bem graduado; excelente a bom como subleito.",
    "A-3":   "Areia fina não plástica; excelente a bom como subleito.",
    "A-2-4": "Granular c/ finos siltosos (LL ≤ 40, IP ≤ 10).",
    "A-2-5": "Granular c/ finos siltosos (LL ≥ 41, IP ≤ 10).",
    "A-2-6": "Granular c/ finos argilosos (LL ≤ 40, IP ≥ 11).",
    "A-2-7": "Granular c/ finos argilosos (LL ≥ 41, IP ≥ 11).",
    "A-4":   "Silte (LL ≤ 40, IP ≤ 10).",
    "A-5":   "Silte (LL ≥ 41, IP ≤ 10), elástico.",
    "A-6":   "Argila (LL ≤ 40, IP ≥ 11).",
    "A-7-5": "Argila (LL ≥ 41, IP ≥ 11), IP ≤ LL − 30.",
    "A-7-6": "Argila (LL ≥ 41, IP ≥ 11), IP > LL − 30.",
}

# Os limites do quadro são inteiros ("40 máx." / "41 mín."). Para valores com decimais,
# adota-se a fronteira no limite máximo: LL > 40 → "41 mín."; IP > 10 → "11 mín."; #40 > 50 → "51 mín.".
LL_LIM = 40.0
IP_LIM = 10.0


def ig_label(ig: int) -> str:
    if ig <= 3:     return "IG baixo (melhor desempenho)"
    if ig <= 9:     return "IG moderado"
    return "IG alto (atenção: baixo desempenho)"


@dataclass
class TRBResult:
    group: str
    ig: int
    rationale: List[str]
    relatorio: str
    subleito: str
    aviso_ig: str
    ig_detalhe: dict = field(default_factory=dict)   # a, b, c, d, ig_bruto
    p200: Optional[float] = None
    ll: Optional[float] = None
    ip: Optional[float] = None
    np_: bool = False

    @property
    def granular(self) -> bool:
        return self.group.startswith(("A-1", "A-2", "A-3"))


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def group_index_detalhe(p200: float, ll: float, ip: float) -> dict:
    """Parcelas do Índice de Grupo (Manual IPR-719): IG = 0,2a + 0,005ac + 0,01bd."""
    a = _clamp(p200, 35.0, 75.0) - 35.0
    b = _clamp(p200, 15.0, 55.0) - 15.0
    c = _clamp(ll, 40.0, 60.0) - 40.0
    d = _clamp(ip, 10.0, 30.0) - 10.0
    bruto = 0.2 * a + 0.005 * a * c + 0.01 * b * d
    return {"a": a, "b": b, "c": c, "d": d, "ig_bruto": bruto, "ig": int(round(max(0.0, min(20.0, bruto))))}


def ig_conta(det: dict) -> str:
    """Texto da conta do IG, ex.: 'IG = 0,2·20 + 0,005·20·15 + 0,01·40·15 = 11,5 → 12'."""
    return (f"IG = 0,2·{fmt(det['a'], 0)} + 0,005·{fmt(det['a'], 0)}·{fmt(det['c'], 0)} + "
            f"0,01·{fmt(det['b'], 0)}·{fmt(det['d'], 0)} = {fmt(det['ig_bruto'], 2)} → {det['ig']}")


def group_index(p200: float, ll: float, ip: float) -> int:
    """Índice de Grupo: IG = 0,2a + 0,005ac + 0,01bd (Manual IPR-719), com
    a = P−35 (0 a 40), b = P−15 (0 a 40), c = LL−40 (0 a 20), d = IP−10 (0 a 20)."""
    a = _clamp(p200, 35.0, 75.0) - 35.0
    b = _clamp(p200, 15.0, 55.0) - 15.0
    c = _clamp(ll, 40.0, 60.0) - 40.0
    d = _clamp(ip, 10.0, 30.0) - 10.0
    ig = 0.2 * a + 0.005 * a * c + 0.01 * b * d
    return int(round(max(0.0, min(20.0, ig))))


def _aviso_ig(group: str, ig: int) -> str:
    tmax = ig_tipico_max(group)
    if ig > tmax:
        return (f"Atenção: IG calculado ({ig}) acima do máximo do quadro TRB para {group} (≤ {tmax}). "
                "Verifique dados/ensaios.")
    return ""


def _build_relatorio(group: str, ig: int, rationale: List[str],
                     p10: float, p40: float, p200: float, ll: float, lp: float,
                     ip: float, is_np: bool, subleito: str, aviso_ig: str) -> str:
    linhas = ["=== Classificação TRB (HRB/AASHTO) — Manual de Pavimentação DNIT (IPR-719) ===",
              f"Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
              f"Grupo: {group}",
              f"Índice de Grupo (IG): {ig} — {ig_label(ig)}"]
    if aviso_ig:
        linhas.append(f"⚠ {aviso_ig}")
    linhas += ["", "Entradas:",
               f"  % passante #10 = {fmt(p10, 2)}%",
               f"  % passante #40 = {fmt(p40, 2)}%",
               f"  % passante #200 = {fmt(p200, 2)}%"]
    if is_np:
        linhas.append("  IP = NP (não plástico)")
        if ll > 0:
            linhas.append(f"  LL = {fmt(ll, 2)}")
    else:
        linhas += [f"  LL = {fmt(ll, 2)}", f"  LP = {fmt(lp, 2)}", f"  IP (LL−LP) = {fmt(ip, 2)}"]
    linhas += ["", "Regras acionadas:"] + [f"  • {r}" for r in rationale]
    linhas += ["", f"Definição: {get_definicao(group)}",
               f"Materiais constituintes: {get_materiais(group)}",
               f"Comportamento como subleito: {subleito}"]
    cbr = cbr_for_trb(group)
    if cbr:
        linhas.append(f"CBR provável (Tabela 14, Manual IPR-719): {cbr}%")
    sp = sucs_provavel(group)
    if sp:
        linhas.append(f"SUCS (Tabela 11, Manual IPR-719): mais provável {sp[0]}; possível {sp[1]}; "
                      f"possível, mas improvável {sp[2]}")
    linhas.append("Observação: o IG não define o grupo; qualifica o solo como subleito (quanto menor, melhor).")
    return "\n".join(linhas)


def classify_trb(p10: float, p40: float, p200: float, ll: float, lp: float, is_np: bool = False) -> TRBResult:
    """Classifica por eliminação da esquerda para a direita no quadro TRB.
    is_np=True indica solo não plástico (IP = NP); o LL, se informado, ainda é usado."""
    R: List[str] = []
    ll = 0.0 if ll is None or (isinstance(ll, float) and math.isnan(ll)) else float(ll)
    lp = 0.0 if lp is None or (isinstance(lp, float) and math.isnan(lp)) else float(lp)
    if not (0.0 <= p200 <= p40 <= p10 <= 100.0):
        raise ValueError("As peneiras devem obedecer: #200 ≤ #40 ≤ #10 ≤ 100, e todos em 0–100%.")
    if not is_np and lp > ll:
        raise ValueError("LP maior que LL: verifique os ensaios (ou marque NP).")
    ip = 0.0 if is_np else ll - lp
    np_ = is_np or ip == 0.0

    granular = p200 <= 35.0
    R.append(f"% passante na #200 = {fmt(p200)}% → {'material granular (≤ 35%)' if granular else 'material silto-argiloso (> 35%)'}")
    if granular:
        if p10 <= 50.0 and p40 <= 30.0 and p200 <= 15.0 and ip <= 6.0:
            g = "A-1-a"; R.append("Atende #10 ≤ 50, #40 ≤ 30, #200 ≤ 15, IP ≤ 6")
        elif p40 <= 50.0 and p200 <= 25.0 and ip <= 6.0:
            g = "A-1-b"; R.append("Atende #40 ≤ 50, #200 ≤ 25, IP ≤ 6")
        elif p40 > 50.0 and p200 <= 10.0 and np_:
            g = "A-3"; R.append("Areia fina NP: #40 ≥ 51, #200 ≤ 10, IP = NP")
        elif ip <= IP_LIM:
            g = "A-2-4" if ll <= LL_LIM else "A-2-5"
            R.append(f"A-2: IP ≤ 10 e LL {'≤ 40' if ll <= LL_LIM else '≥ 41'}")
        else:
            g = "A-2-6" if ll <= LL_LIM else "A-2-7"
            R.append(f"A-2: IP ≥ 11 e LL {'≤ 40' if ll <= LL_LIM else '≥ 41'}")
    else:
        if ip <= IP_LIM:
            g = "A-4" if ll <= LL_LIM else "A-5"
            R.append(f"IP ≤ 10 e LL {'≤ 40' if ll <= LL_LIM else '≥ 41'}")
        elif ll <= LL_LIM:
            g = "A-6"; R.append("IP ≥ 11 e LL ≤ 40")
        elif ip <= ll - 30.0:
            g = "A-7-5"; R.append(f"LL ≥ 41, IP ≥ 11 e IP ≤ LL − 30 ({fmt(ll - 30.0)})")
        else:
            g = "A-7-6"; R.append(f"LL ≥ 41, IP ≥ 11 e IP > LL − 30 ({fmt(ll - 30.0)})")
    det = group_index_detalhe(p200, ll, ip)
    ig = det["ig"]
    subleito = get_subleito_text(g)
    aviso = _aviso_ig(g, ig)
    relatorio = _build_relatorio(g, ig, R, p10, p40, p200, ll, lp, ip, np_, subleito, aviso)
    linha_ig = f"Índice de Grupo (IG): {ig} — {ig_label(ig)}"
    relatorio = relatorio.replace(linha_ig, linha_ig + "\n  " + ig_conta(det), 1)
    return TRBResult(group=g, ig=ig, rationale=R, relatorio=relatorio, subleito=subleito, aviso_ig=aviso,
                     ig_detalhe=det, p200=p200, ll=ll, ip=ip, np_=np_)


def _f(v, default=0.0) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    return default if math.isnan(x) else x


def classify_dataframe_trb(df, cols_map: Optional[dict] = None):
    import pandas as pd
    c = {'P10': 'P10', 'P40': 'P40', 'P200': 'P200', 'LL': 'LL', 'LP': 'LP', 'IP': 'IP', 'NP': 'NP'}
    if cols_map:
        c.update(cols_map)
    out = []
    for _, row in df.iterrows():
        rec = row.to_dict()
        try:
            p10, p40, p200 = _f(row.get(c['P10'])), _f(row.get(c['P40'])), _f(row.get(c['P200']))
            np_ = bool(row.get(c['NP'], False))
            ll = _f(row.get(c['LL']))
            if np_:
                lp = 0.0
            elif c['LP'] in df.columns and not pd.isna(row.get(c['LP'])):
                lp = _f(row.get(c['LP']))
            else:
                lp = max(0.0, ll - _f(row.get(c['IP'])))
            r = classify_trb(p10, p40, p200, ll, lp, is_np=np_)
            rec.update({'IP_calc': 0.0 if np_ else ll - lp, 'Grupo_TRB': r.group, 'IG': r.ig,
                        'Subleito': r.subleito, 'Materiais constituintes': get_materiais(r.group),
                        'CBR provável (%)': cbr_for_trb(r.group),
                        'relatorio': r.relatorio, 'aviso_ig': r.aviso_ig})
        except Exception as ex:
            rec.update({'Grupo_TRB': 'ERRO', 'aviso_ig': str(ex)})
        out.append(rec)
    return pd.DataFrame(out)


def plot_trb(ll=None, ip=None, granular=True, np_=False):
    """Gráfico LL × IP com as zonas do quadro TRB (LL 40/41, IP 10/11 e IP = LL − 30 para o A-7)."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    x_max, y_max = 100.0, 60.0
    ax.axvline(40.5, color="black", lw=1.2)
    ax.axhline(10.5, color="black", lw=1.2)
    ax.plot([40.5, 90.0], [10.5, 60.0], color="black", lw=1.2, ls="--" if granular else "-")
    ax.fill([0, y_max, 0], [0, y_max, y_max], color="lightgray", alpha=0.35, zorder=0)  # IP > LL
    ax.text(8, 50, "IP > LL\n(impossível)", fontsize=8, color="gray")
    if granular:
        zonas = [("A-2-4", 18, 4), ("A-2-5", 65, 4), ("A-2-6", 30, 17), ("A-2-7", 65, 30)]
    else:
        zonas = [("A-4", 20, 4), ("A-5", 68, 4), ("A-6", 30, 17), ("A-7-5", 72, 22), ("A-7-6", 52, 38)]
    for txt, x, y in zonas:
        ax.text(x, y, txt, fontsize=11, fontweight="bold", ha="center")
    if np_:
        ax.text(0.5, 0.93, "Amostra não plástica (NP): IP = 0", transform=ax.transAxes, ha="center",
                fontsize=9, color="dimgray")
    if ll is not None and ip is not None:
        ax.scatter([ll], [ip], color="tab:red", s=55, zorder=5)
        ax.annotate(f"LL {fmt(ll, 0)} · IP {fmt(ip, 0)}", (ll, ip), xytext=(8, 8), textcoords="offset points",
                    fontsize=9, color="tab:red", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="tab:red", lw=0.6, alpha=0.95))
    ax.set_xlim(0, x_max); ax.set_ylim(0, y_max)
    ax.set_xlabel("Limite de liquidez LL (%)"); ax.set_ylabel("Índice de plasticidade IP (%)")
    ax.set_title(f"Quadro TRB — {'materiais granulares (A-2)' if granular else 'materiais silto-argilosos'}",
                 fontsize=10)
    ax.grid(True, ls=":", alpha=0.5)
    fig.tight_layout()
    return fig


# Planilha-modelo: um exemplo por grupo (conferidos em tests/test_trb.py).
EXEMPLOS = [
    ("A-1-a", "Pedregulho com pouco fino",        dict(P10=45, P40=25, P200=10, LL=30, LP=26, NP=False)),
    ("A-1-b", "Areia grossa com aglutinante",     dict(P10=70, P40=45, P200=20, LL=35, LP=29, NP=False)),
    ("A-3",   "Areia fina NP",                    dict(P10=95, P40=80, P200=8,  LL=None, LP=None, NP=True)),
    ("A-2-4", "Granular c/ silte (LL ≤ 40)",      dict(P10=85, P40=60, P200=30, LL=35, LP=27, NP=False)),
    ("A-2-5", "Granular c/ silte (LL ≥ 41)",      dict(P10=85, P40=60, P200=30, LL=45, LP=37, NP=False)),
    ("A-2-6", "Granular c/ argila (LL ≤ 40)",     dict(P10=85, P40=60, P200=30, LL=35, LP=23, NP=False)),
    ("A-2-7", "Granular c/ argila (LL ≥ 41)",     dict(P10=85, P40=60, P200=30, LL=45, LP=33, NP=False)),
    ("A-4",   "Silte LL baixo",                   dict(P10=80, P40=60, P200=50, LL=35, LP=27, NP=False)),
    ("A-5",   "Silte LL alto",                    dict(P10=80, P40=60, P200=50, LL=50, LP=40, NP=False)),
    ("A-6",   "Argila LL baixo",                  dict(P10=80, P40=60, P200=50, LL=35, LP=22, NP=False)),
    ("A-7-5", "Argila LL alto, menos plástica",   dict(P10=90, P40=70, P200=60, LL=55, LP=35, NP=False)),
    ("A-7-6", "Argila LL alto, mais plástica",    dict(P10=90, P40=70, P200=60, LL=55, LP=25, NP=False)),
]
