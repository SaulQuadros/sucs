
# trb_core.py
from dataclasses import dataclass
from typing import List, Optional

from trb_defs import get_definicao, get_subleito_text, ig_tipico_max

GROUP_DESC = {
    "A-1-a": "Granular de alta qualidade; excelente a bom como subleito.",
    "A-1-b": "Granular bem graduado; geralmente bom como subleito.",
    "A-3":   "Areia fina não plástica; sensível à umidade; bom a regular.",
    "A-2-4": "Granular c/ finos siltosos (LL≤40).",
    "A-2-5": "Granular c/ finos siltosos (LL>40).",
    "A-2-6": "Granular c/ finos argilosos (LL≤40).",
    "A-2-7": "Granular c/ finos argilosos (LL>40).",
    "A-4":   "Silte (LL baixo).",
    "A-5":   "Silte (LL alto), elástico.",
    "A-6":   "Argila (LL baixo).",
    "A-7-5": "Argila (LL alto), IP moderado.",
    "A-7-6": "Argila (LL alto), IP elevado.",
}

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

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def group_index(p200: float, ll: float, ip: float) -> int:
    P1 = _clamp(p200, 35.0, 75.0); a = P1 - 35.0
    P2 = _clamp(p200, 15.0, 55.0); b = P2 - 15.0
    LL1 = _clamp(ll,   40.0, 60.0); c = LL1 - 40.0
    IP1 = _clamp(ip,   10.0, 30.0); d = IP1 - 10.0
    ig = 0.2*a + 0.005*a*c + 0.01*b*d
    ig_i = int(round(max(0.0, min(20.0, ig))))
    return ig_i

def _aviso_ig(group: str, ig: int) -> str:
    tmax = ig_tipico_max(group)
    if ig > tmax:
        return f"Atenção: IG calculado ({ig}) acima da faixa típica para {group} (≤{tmax}). Verifique dados/ensaios."
    return ""

def _build_relatorio(group: str, ig: int, rationale: List[str],
                     p10: float, p40: float, p200: float, ll: float, lp: float,
                     ip: float, is_np: bool, subleito: str, aviso_ig: str) -> str:
    linhas = []
    linhas.append("=== Classificação TRB (HRB/AASHTO) ===")
    linhas.append(f"Grupo: {group}")
    linhas.append(f"Índice de Grupo (IG): {ig} — {ig_label(ig)}")
    if aviso_ig:
        linhas.append(f"⚠ {aviso_ig}")
    linhas.append("")
    linhas.append("Entradas:")
    linhas.append(f"  % passante #10 = {p10:.2f}%")
    linhas.append(f"  % passante #40 = {p40:.2f}%")
    linhas.append(f"  % passante #200 = {p200:.2f}%")
    if is_np:
        linhas.append(f"  IP = NP (não-plástico)")
        linhas.append(f"  LL (ignorado por NP)")
        linhas.append(f"  LP (ignorado por NP)")
    else:
        linhas.append(f"  LL = {ll:.2f}")
        linhas.append(f"  LP = {lp:.2f}")
        linhas.append(f"  IP (LL−LP) = {ip:.2f}")
    linhas.append("")
    linhas.append("Regras acionadas:")
    for r in rationale:
        linhas.append(f"  • {r}")
    linhas.append("")
    linhas.append(f"Interpretação TRB (resumo): {GROUP_DESC.get(group, '—')}")
    from trb_defs import get_definicao
    defin = get_definicao(group, preferir_oficial=True)
    if defin and defin != "—":
        linhas.append("")
        linhas.append("Definição DNIT:")
        linhas.append(defin)
    linhas.append("")
    linhas.append(f"Comportamento como subleito: {subleito}")
    linhas.append("Observação: O IG não define o grupo; apenas qualifica o desempenho do subleito (quanto menor, melhor).")
    return "\n".join(linhas)

def classify_trb(p10: float, p40: float, p200: float, ll: float, lp: float, is_np: bool=False) -> TRBResult:
    R: List[str] = []
    if is_np:
        ip = 0.0
    else:
        ip = max(0.0, ll - lp)
    if not (0.0 <= p200 <= p40 <= p10 <= 100.0):
        raise ValueError("As peneiras devem obedecer: #200 ≤ #40 ≤ #10 ≤ 100, e todos em 0–100%.")
    granular = (p200 <= 35.0)
    R.append(f"{'Granular' if granular else 'Silto-argiloso'} por %passante #200 = {p200:.1f}%")
    if granular:
        if (p10 <= 50.0 and p40 <= 30.0 and p200 <= 15.0 and ll <= 40.0 and ip <= 6.0):
            g = "A-1-a"; R.append("Atende #10≤50, #40≤30, #200≤15, LL≤40, IP≤6")
        elif (p40 <= 50.0 and p200 <= 25.0 and ll <= 40.0 and ip <= 6.0):
            g = "A-1-b"; R.append("Atende #40≤50, #200≤25, LL≤40, IP≤6")
        elif (p40 >= 51.0 and p200 <= 10.0 and ip == 0.0):
            g = "A-3"; R.append("Areia fina NP: #40≥51, #200≤10, IP=NP")
        else:
            if ip <= 10.0 and ll <= 40.0:
                g = "A-2-4"; R.append("IP≤10 e LL≤40")
            elif ip <= 10.0 and ll > 40.0:
                g = "A-2-5"; R.append("IP≤10 e LL>40")
            elif ip >= 11.0 and ll <= 40.0:
                g = "A-2-6"; R.append("IP≥11 e LL≤40")
            else:
                g = "A-2-7"; R.append("IP≥11 e LL>40")
    else:
        if ll <= 40.0 and ip <= 10.0:
            g = "A-4"; R.append("LL≤40 e IP≤10")
        elif ll > 40.0 and ip <= 10.0:
            g = "A-5"; R.append("LL>40 e IP≤10")
        elif ll <= 40.0 and ip >= 11.0:
            g = "A-6"; R.append("LL≤40 e IP≥11")
        else:
            if ip <= (ll - 30.0):
                g = "A-7-5"; R.append("LL>40, IP≥11 e IP ≤ LL−30")
            else:
                g = "A-7-6"; R.append("LL>40, IP≥11 e IP > LL−30")
    ig = group_index(p200, ll, ip)
    from trb_defs import get_subleito_text, ig_tipico_max
    subleito = get_subleito_text(g)
    aviso = _aviso_ig(g, ig)
    relatorio = _build_relatorio(g, ig, R, p10, p40, p200, ll, lp, ip, is_np, subleito, aviso)
    return TRBResult(group=g, ig=ig, rationale=R, relatorio=relatorio, subleito=subleito, aviso_ig=aviso)

def classify_dataframe_trb(df, cols_map: Optional[dict]=None):
    import pandas as pd
    c = {'P10':'P10','P40':'P40','P200':'P200','LL':'LL','LP':'LP','IP':'IP','NP':'NP'}
    if cols_map:
        c.update(cols_map)
    out = []
    for _, row in df.iterrows():
        p10  = float(row.get(c['P10'], 0))
        p40  = float(row.get(c['P40'], 0))
        p200 = float(row.get(c['P200'], 0))
        np_  = bool(row.get(c['NP'], False))
        if np_:
            ll = 0.0; lp = 0.0; ip = 0.0
        else:
            ll = float(row.get(c['LL'], 0))
            if c['LP'] in df.columns:
                lp = float(row.get(c['LP'], 0))
                ip = max(0.0, ll - lp)
            else:
                ip = float(row.get(c['IP'], 0))
                lp = max(0.0, ll - ip)
        r = classify_trb(p10, p40, p200, ll, lp, is_np=np_)
        out.append({**row,
            'IP_calc': max(0.0, ll - lp) if not np_ else 0.0,
            'Grupo_TRB': r.group, 'IG': r.ig, 'Subleito': r.subleito,
            'relatorio': r.relatorio, 'aviso_ig': r.aviso_ig})
    return pd.DataFrame(out)
