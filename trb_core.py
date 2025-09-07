
# trb_core.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TRBResult:
    group: str
    ig: int
    rationale: List[str]

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

def classify_trb(p10: float, p40: float, p200: float, ll: float, ip: float, is_np: bool=False) -> TRBResult:
    R: List[str] = []
    if is_np:
        ip = 0.0
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
    return TRBResult(group=g, ig=ig, rationale=R)

def classify_dataframe_trb(df, cols_map: Optional[dict]=None):
    import pandas as pd
    c = {'P10':'P10','P40':'P40','P200':'P200','LL':'LL','IP':'IP','NP':'NP'}
    if cols_map:
        c.update(cols_map)
    out = []
    for _, row in df.iterrows():
        p10  = float(row.get(c['P10'], 0))
        p40  = float(row.get(c['P40'], 0))
        p200 = float(row.get(c['P200'], 0))
        np_  = bool(row.get(c['NP'], False))
        if np_:
            ll = 0.0
            ip = 0.0
        else:
            ll = float(row.get(c['LL'], 0))
            ip = float(row.get(c['IP'], 0))
        r = classify_trb(p10, p40, p200, ll, ip, is_np=np_)
        out.append({**row, 'Grupo_TRB': r.group, 'IG': r.ig})
    return pd.DataFrame(out)
