# sucs_core.py
# Núcleo de classificação SUCS conforme o Manual de Pavimentação DNIT (IPR-719/2006, versão corrigida
# com a Errata 1): Tabela 5, Figura 17 (gráfico de plasticidade) e fluxograma de identificação em
# laboratório. Pode ser importado tanto por scripts de terminal quanto pelo app Streamlit.

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import math
import re

from formato import fmt  # noqa: F401 (reexportado para as páginas)

LINE_A_SLOPE = 0.73      # linha A: IP = 0,73·(LL − 20)
HATCH_IP = (4.0, 7.0)    # zona hachurada (limítrofe) acima da linha A
LL_LH = 50.0             # L: LL ≤ 50 ; H: LL > 50 (Tabela 5)

# Tabela 13 — Valores prováveis de CBR para os grupos de SUCS
SUCS_CBR = {
    "GW": "40 a mais de 80",
    "GP": "30 a mais de 60",
    "GM": "20 a mais de 60",
    "GC": "20 a 40", "SW": "20 a 40",
    "SP": "10 a 40", "SM": "10 a 40",
    "SC": "5 a 20",
    "ML": "15 a menos de 2", "CL": "15 a menos de 2", "CH": "15 a menos de 2",
    "MH": "10 a menos de 2",
    "OL": "5 a menos de 2", "OH": "5 a menos de 2",
}

# Tabela 12 — Interrelações entre a classificação unificada e TRB
SUCS_PARA_TRB = {
    #       mais provável                     possível                     possível, mas improvável
    "GW": ("A-1-a",                           "—",                         "A-2-4, A-2-5, A-2-6, A-2-7"),
    "GP": ("A-1-a",                           "A-1-b",                     "A-3, A-2-4, A-2-5, A-2-6, A-2-7"),
    "GM": ("A-1-b, A-2-4, A-2-5, A-2-7",      "A-2-6",                     "A-4, A-5, A-6, A-7, A-7-6, A-1-a"),
    "GC": ("A-2-6, A-2",                      "A-2-4, A-6",                "A-4, A-7-6, A-7-5"),
    "SW": ("A-1-b",                           "A-1-a",                     "A-3, A-2-4, A-2-5, A-2-6, A-2-7"),
    "SP": ("A-3, A-1-b",                      "A-1-a",                     "A-2-4, A-2-5, A-2-6, A-2-7"),
    "SM": ("A-1-b, A-2-4, A-2-5, A-2-7",      "A-2-6, A-4, A-5",           "A-6, A-7-5, A-7-6, A-1-a"),
    "SC": ("A-2-6, A-2-7",                    "A-2-4, A-6, A-4, A-7-6",    "A-7-5"),
    "ML": ("A-4, A-5",                        "A-6, A-7-5",                "—"),
    "CL": ("A-6, A-7-6",                      "A-6, A-7-5, A-4",           "—"),
    "OL": ("A-4, A-5",                        "A-6, A-7-5, A-7-6",         "—"),
    "CH": ("A-7-6",                           "A-7-5",                     "—"),
    "OH": ("A-7-5, A-5",                      "—",                         "A-7-6"),
    "PT": ("—",                               "—",                         "—"),
}

# Tabela 5 — descrição dos grupos
DNIT_DESC = {
    "GW": "Pedregulhos bem graduados ou misturas de areia e pedregulho, com pouco ou nenhum fino.",
    "GP": "Pedregulhos mal graduados ou misturas de areia e pedregulho, com pouco ou nenhum fino.",
    "GM": "Pedregulhos siltosos ou misturas de pedregulho, areia e silte.",
    "GC": "Pedregulhos argilosos, ou mistura de pedregulho, areia e argila.",
    "SW": "Areias bem graduadas ou areias pedregulhosas, com pouco ou nenhum fino.",
    "SP": "Areias mal graduadas ou areias pedregulhosas, com pouco ou nenhum fino.",
    "SM": "Areias siltosas — misturas de areia e silte.",
    "SC": "Areias argilosas — misturas de areia e argila.",
    "ML": "Siltes inorgânicos — areias muito finas — areias finas siltosas e argilosas.",
    "CL": "Argilas inorgânicas de baixa e média plasticidade — argilas pedregulhosas, arenosas e siltosas.",
    "OL": "Siltes orgânicos — argilas siltosas orgânicas de baixa plasticidade.",
    "MH": "Siltes — areias finas ou siltes micáceos — siltes elásticos.",
    "CH": "Argilas inorgânicas de alta plasticidade.",
    "OH": "Argilas orgânicas de alta e média plasticidade.",
    "PT": "Turfas e outros solos altamente orgânicos.",
}


def _num(x):
    """float ou None (aceita None, NaN, '' e texto)."""
    if x is None or isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def _bool(x) -> bool:
    if isinstance(x, str):
        return x.strip().lower() in {"true", "1", "sim", "s", "yes", "x"}
    v = _num(x)
    return bool(v) if v is not None else bool(x) if isinstance(x, bool) else False


def _parts(grp: str):
    return [p for p in re.split(r"[-/()\s]+", (grp or "").upper()) if p]


def cbr_for_group(grp: str):
    """CBR provável (Tabela 13). Para símbolos duplos, informa a faixa de cada componente."""
    parts = [p for p in _parts(grp) if p in SUCS_CBR]
    if not parts:
        return None
    if len(parts) == 1:
        return SUCS_CBR[parts[0]]
    return "; ".join(f"{p}: {SUCS_CBR[p]}" for p in dict.fromkeys(parts))


def trb_for_group(grp: str):
    """Correspondência TRB (Tabela 12) do primeiro símbolo com entrada na tabela."""
    for p in _parts(grp):
        if p in SUCS_PARA_TRB:
            return p, SUCS_PARA_TRB[p]
    return None


def dnit_description_for_group(grp: str):
    parts = [p for p in _parts(grp) if p in DNIT_DESC]
    if not parts:
        return None
    if len(parts) == 1:
        return DNIT_DESC[parts[0]]
    return " / ".join(DNIT_DESC[p] for p in dict.fromkeys(parts)) + " (limítrofe)."


def cu_cc(D10, D30, D60):
    """Cu = D60/D10 e Cc = D30²/(D60·D10). Retorna (Cu, Cc) ou (None, None)."""
    d10, d30, d60 = _num(D10), _num(D30), _num(D60)
    if not d10 or not d30 or not d60 or d10 <= 0 or d60 <= 0:
        return None, None
    return d60 / d10, d30 ** 2 / (d60 * d10)


def well_graded_letter(coarse_symbol, Cu, Cc):
    """W/P: pedregulhos Cu ≥ 4 e 1 ≤ Cc ≤ 3; areias Cu ≥ 6 e 1 ≤ Cc ≤ 3. None se faltar dado."""
    Cu, Cc = _num(Cu), _num(Cc)
    if Cu is None or Cc is None:
        return None
    cu_min = 6.0 if coarse_symbol == "S" else 4.0
    Cu, Cc = round(Cu, 6), round(Cc, 6)  # evita 0,9999999 < 1 por arredondamento
    return "W" if (Cu >= cu_min and 1.0 <= Cc <= 3.0) else "P"


def line_a(LL: float) -> float:
    return LINE_A_SLOPE * (LL - 20.0)


def plasticity_zone(LL, LP, NP=False):
    """Posição no gráfico de plasticidade (Figura 17):
    'M' abaixo da linha A (ou IP < 4, ou NP); 'C' acima da linha A (IP > 7);
    'MC' zona hachurada (4 ≤ IP ≤ 7 e acima da linha A). None se faltar dado."""
    if _bool(NP):
        return "M"
    LL, LP = _num(LL), _num(LP)
    if LL is None or LP is None:
        return None
    IP = LL - LP
    if IP < HATCH_IP[0] or IP < line_a(LL):
        return "M"
    if IP <= HATCH_IP[1]:
        return "MC"
    return "C"


# Compatibilidade com versões anteriores
def fines_nature(LL, LP):
    z = plasticity_zone(LL, LP)
    return None if z is None else ("C" if z == "C" else "M")


@dataclass
class SUCSResult:
    group: str
    entradas: List[str] = field(default_factory=list)   # dados usados (já com derivados)
    passos: List[str] = field(default_factory=list)     # regras acionadas, em ordem
    avisos: List[str] = field(default_factory=list)     # pendências e observações
    pct_finos: Optional[float] = None
    LL: Optional[float] = None
    IP: Optional[float] = None
    NP: bool = False

    @property
    def completo(self) -> bool:
        """False quando falta dado para fechar o símbolo (ex.: 'SW/SP-SC')."""
        return "/" not in self.group

    @property
    def descricao(self) -> Optional[str]:
        return dnit_description_for_group(self.group)

    @property
    def cbr(self) -> Optional[str]:
        return cbr_for_group(self.group)

    @property
    def trb(self):
        return trb_for_group(self.group)

    def relatorio(self, meta: Optional[dict] = None) -> str:
        L = ["=== Classificação SUCS — Manual de Pavimentação DNIT (IPR-719) ==="]
        meta = meta or {}
        for k, rot in (("projeto", "Projeto"), ("tecnico", "Técnico"), ("amostra", "Amostra")):
            if meta.get(k):
                L.append(f"{rot}: {meta[k]}")
        L += [f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}", f"Grupo: {self.group}", "",
              "Entradas:"] + [f"  {x}" for x in self.entradas]
        L += ["", "Regras acionadas:"] + [f"  • {x}" for x in self.passos]
        if self.avisos:
            L += ["", "Avisos:"] + [f"  ⚠ {x}" for x in self.avisos]
        L.append("")
        if self.descricao:
            L.append(f"Descrição (Tabela 5, Manual IPR-719): {self.descricao}")
        if self.cbr:
            L.append(f"CBR provável (Tabela 13, Manual IPR-719): {self.cbr}%")
        if self.trb:
            s, (mp, pp, pi) = self.trb
            L.append(f"TRB (Tabela 12, Manual IPR-719) para {s}: mais provável {mp}; possível {pp}; "
                     f"possível, mas improvável {pi}")
        return "\n".join(L)


def _retido_e_fracoes(data):
    """Aceita % passante (P4, P200) ou a forma antiga (pct_retido_200, pedregulho/areia da fração graúda).
    Retorna (pct_retido_200, pct_pedregulho_coarse, pct_areia_coarse, P4, P200)."""
    p200, p4 = _num(data.get("P200")), _num(data.get("P4"))
    if p200 is not None:
        if not (0.0 <= p200 <= 100.0):
            raise ValueError("% passante na #200 deve estar entre 0 e 100.")
        if p4 is not None:
            if not (p200 <= p4 <= 100.0):
                raise ValueError("As peneiras devem obedecer: #200 ≤ #4 ≤ 100.")
            return 100.0 - p200, 100.0 - p4, p4 - p200, p4, p200
        return 100.0 - p200, _num(data.get("pct_pedregulho_coarse")), _num(data.get("pct_areia_coarse")), None, p200
    ret = _num(data.get("pct_retido_200"))
    if ret is None or not (0.0 <= ret <= 100.0):
        raise ValueError("Informe a % passante na #200 (ou a % retida na #200), entre 0 e 100.")
    return ret, _num(data.get("pct_pedregulho_coarse")), _num(data.get("pct_areia_coarse")), None, None


def classify_sucs_result(data) -> SUCSResult:
    """
    data: dict com
      P4, P200 (% passante)  — ou, na forma antiga, pct_retido_200 + pct_pedregulho_coarse/pct_areia_coarse
      LL, LP ; NP (bool)
      Cu, Cc (opcionais) ou D10, D30, D60 em mm (opcionais)
      organico (bool), turfa (bool)
    """
    pct_ret_200, pg, ps, P4, P200 = _retido_e_fracoes(data)
    pct_finos = 100.0 - pct_ret_200

    NP = _bool(data.get("NP", False))
    LL, LP = _num(data.get("LL")), _num(data.get("LP"))
    IP = None
    if NP:
        IP = 0.0
    elif LL is not None and LP is not None:
        if LP > LL:
            raise ValueError("LP maior que LL: verifique os ensaios (ou marque NP).")
        IP = LL - LP

    E: List[str] = []
    passos: List[str] = []
    avisos: List[str] = []

    Cu, Cc = _num(data.get("Cu")), _num(data.get("Cc"))
    cu_por_d = False
    if Cu is None or Cc is None:
        Cu2, Cc2 = cu_cc(data.get("D10"), data.get("D30"), data.get("D60"))
        if Cu2 is not None:
            Cu, Cc, cu_por_d = Cu2, Cc2, True

    if P4 is not None:
        E.append(f"% passante: #4 = {fmt(P4)}% ; #200 = {fmt(P200)}%")
    elif P200 is not None:
        E.append(f"% passante na #200 = {fmt(P200)}%")
    E.append(f"% de finos = {fmt(pct_finos)}% ; % retido na #200 = {fmt(pct_ret_200)}%")
    if NP:
        E.append("IP = NP (não plástico)")
    elif IP is not None:
        E.append(f"LL = {fmt(LL)} ; LP = {fmt(LP)} → IP = {fmt(IP)} (linha A: {fmt(line_a(LL))})")
    else:
        E.append("LL/LP: não informados")
    if Cu is not None and Cc is not None:
        E.append(f"Cu = {fmt(Cu, 2)} ; Cc = {fmt(Cc, 2)}" + (" (calculados por D10, D30, D60)" if cu_por_d else ""))

    organico = _bool(data.get("organico", False))
    turfa = _bool(data.get("turfa", False))

    def out(grp):
        return SUCSResult(grp, E, passos, avisos, pct_finos, LL, IP, NP)

    if turfa:
        passos.append("Material altamente orgânico, fibroso (turfa) → PT")
        return out("PT")

    zone = plasticity_zone(LL, LP, NP)

    # Tabela 5: mais de 50% retido na #200 → granulação grossa
    if pct_ret_200 > 50.0:
        passos.append(f"{fmt(pct_ret_200)}% retido na #200 (> 50%) → granulação grossa")
        pg, ps = pg or 0.0, ps or 0.0
        if pg + ps <= 0:
            raise ValueError("Solo grosso: informe a % passante na #4 (ou pedregulho e areia da fração graúda).")
        pgn = 100.0 * pg / (pg + ps)
        coarse = "G" if pgn >= 50.0 else "S"
        passos.append(f"Fração graúda: pedregulho {fmt(pgn)}% e areia {fmt(100 - pgn)}% → "
                      + ("pedregulho (G): 50% ou mais retido na #4" if coarse == "G" else "areia (S)"))
        wp = well_graded_letter(coarse, Cu, Cc)
        grad_txt = None if wp is None else (
            f"Cu = {fmt(Cu, 2)} {'≥' if Cu >= (6 if coarse == 'S' else 4) else '<'} {6 if coarse == 'S' else 4} e "
            f"Cc = {fmt(Cc, 2)} {'dentro' if 1 <= round(Cc, 6) <= 3 else 'fora'} de 1 a 3 → "
            f"{'bem graduado (W)' if wp == 'W' else 'mal graduado (P)'}")

        if pct_finos < 5.0:
            passos.append(f"Finos {fmt(pct_finos)}% (< 5%) → a graduação decide W/P")
            if wp is None:
                avisos.append("Informe Cu e Cc (ou D10, D30, D60) para decidir W (bem) ou P (mal graduado).")
                return out(f"{coarse}W/{coarse}P")
            passos.append(grad_txt)
            return out(coarse + wp)

        if pct_finos <= 12.0:
            passos.append(f"Finos {fmt(pct_finos)}% (entre 5% e 12%) → caso limite, símbolo duplo")
            first = None if wp is None else coarse + wp
            if grad_txt:
                passos.append(grad_txt)
            else:
                avisos.append("Informe Cu e Cc (ou D10, D30, D60) para decidir W/P.")
            second = None if zone is None else coarse + ("M" if zone == "M" else "C")
            if zone is None:
                avisos.append("Informe LL e LP (ou NP) para decidir M/C.")
            elif zone == "MC":
                passos.append("Finos na zona hachurada → sufixo C (fino plástico)")
            else:
                passos.append(f"Finos {'abaixo' if zone == 'M' else 'acima'} da linha A → sufixo {second}")
            return out(f"{first or coarse + 'W/' + coarse + 'P'}-{second or coarse + 'M/' + coarse + 'C'}")

        passos.append(f"Finos {fmt(pct_finos)}% (> 12%) → a plasticidade dos finos decide M/C")
        if zone is None:
            avisos.append("Informe LL e LP (ou NP) para decidir M/C.")
            return out(f"{coarse}M/{coarse}C")
        if zone == "MC":
            passos.append("Finos na zona hachurada (4 ≤ IP ≤ 7, acima da linha A) → símbolo duplo")
            return out(f"{coarse}M-{coarse}C")
        passos.append(f"Finos {'abaixo' if zone == 'M' else 'acima'} da linha A → {coarse}{'M' if zone == 'M' else 'C'}")
        return out(coarse + ("M" if zone == "M" else "C"))

    # Granulação fina (50% ou mais passando na #200)
    passos.append(f"{fmt(pct_finos)}% passando na #200 (≥ 50%) → granulação fina")
    if zone is None:
        avisos.append("Informe LL e LP (ou NP) para posicionar no gráfico de plasticidade.")
        return out("ML/CL")
    LLv = LL if LL is not None else 0.0
    LH = "L" if LLv <= LL_LH else "H"
    passos.append(f"LL = {fmt(LLv)} {'≤' if LH == 'L' else '>'} 50 → {'baixa (L)' if LH == 'L' else 'alta (H)'} compressibilidade")
    if organico:
        if zone == "M":
            passos.append(f"Orgânico e abaixo da linha A → O{LH}")
            return out("O" + LH)
        avisos.append("Marcado como orgânico, mas o ponto está acima da linha A: "
                      "o Manual classifica pela plasticidade.")
    if zone == "MC":
        passos.append("Zona hachurada (4 ≤ IP ≤ 7, acima da linha A) → ML-CL")
        return out("ML-CL")
    if zone == "M":
        passos.append("Abaixo da linha A (ou IP < 4) → silte (M)" if not NP else "Não plástico → silte (M)")
    else:
        passos.append("Acima da linha A → argila (C)")
    return out(("M" if zone == "M" else "C") + LH)


def classify_sucs(data):
    """Compatibilidade: retorna (grupo, relatório em texto)."""
    r = classify_sucs_result(data)
    return r.group, r.relatorio({k: data.get(k) for k in ("projeto", "tecnico", "amostra")})


# Planilha-modelo: um exemplo por grupo (conferidos em tests/test_sucs.py). Granulometria em % passante.
EXEMPLOS = [
    ("GW", "Pedregulho bem graduado, poucos finos", dict(P4=30, P200=3, NP=True, Cu=8, Cc=2.0)),
    ("GP", "Pedregulho mal graduado, poucos finos", dict(P4=40, P200=4, NP=True, Cu=2, Cc=0.6)),
    ("GM", "Pedregulho siltoso", dict(P4=40, P200=25, LL=40, LP=27)),
    ("GC", "Pedregulho argiloso", dict(P4=40, P200=25, LL=40, LP=20)),
    ("SW", "Areia bem graduada (Cu/Cc pelos diâmetros)", dict(P4=70, P200=3, NP=True, D10=0.1, D30=0.3, D60=0.9)),
    ("SP", "Areia mal graduada", dict(P4=70, P200=4, NP=True, Cu=3, Cc=0.8)),
    ("SM", "Areia siltosa", dict(P4=80, P200=25, LL=40, LP=27)),
    ("SC", "Areia argilosa", dict(P4=80, P200=25, LL=40, LP=20)),
    ("SW-SC", "Areia bem graduada com 8% de finos argilosos", dict(P4=75, P200=8, LL=30, LP=15, Cu=7, Cc=2)),
    ("SM-SC", "Areia com finos na zona hachurada", dict(P4=80, P200=30, LL=25, LP=19)),
    ("ML", "Silte de baixa compressibilidade", dict(P4=100, P200=70, LL=35, LP=25)),
    ("CL", "Argila de baixa a média plasticidade", dict(P4=100, P200=70, LL=35, LP=22)),
    ("ML-CL", "Fino na zona hachurada", dict(P4=100, P200=70, LL=25, LP=19)),
    ("OL", "Silte orgânico de baixa plasticidade", dict(P4=100, P200=70, LL=35, LP=25, organico=True)),
    ("MH", "Silte elástico (LL alto)", dict(P4=100, P200=70, LL=70, LP=40)),
    ("CH", "Argila de alta plasticidade", dict(P4=100, P200=70, LL=70, LP=25)),
    ("OH", "Argila orgânica de LL alto", dict(P4=100, P200=70, LL=60, LP=35, organico=True)),
    ("PT", "Turfa", dict(P4=100, P200=90, LL=150, LP=50, organico=True, turfa=True)),
]


def classify_dataframe(df):
    """Aplica classify_sucs linha a linha e retorna df com colunas 'grupo' e 'relatorio'."""
    out_groups, out_reports = [], []
    for _, row in df.iterrows():
        try:
            grp, rep = classify_sucs(row.to_dict())
        except Exception as ex:
            grp, rep = "ERRO", str(ex)
        out_groups.append(grp)
        out_reports.append(rep)
    res = df.copy()
    res["grupo"] = out_groups
    res["relatorio"] = out_reports
    return res


def plot_plasticidade(LL=None, IP=None, NP=False, label=None):
    """Gráfico de plasticidade (Figura 17 do Manual IPR-719) com o ponto da amostra, se houver."""
    import matplotlib.pyplot as plt
    tem_ponto = (not NP) and LL is not None and IP is not None
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    x_max = max(100.0, (LL or 0) + 10)
    ll_4 = 20 + HATCH_IP[0] / LINE_A_SLOPE   # linha A cruza IP = 4
    ll_7 = 20 + HATCH_IP[1] / LINE_A_SLOPE   # linha A cruza IP = 7
    u_4, u_7 = 8 + HATCH_IP[0] / 0.9, 8 + HATCH_IP[1] / 0.9  # limite esquerdo (linha U: IP = 0,9·(LL − 8))
    ax.plot([ll_4, x_max], [HATCH_IP[0], line_a(x_max)], color="black", lw=1.4)
    ax.text(x_max * 0.80, line_a(x_max * 0.80) + 2.5, "Linha A", rotation=33, fontsize=9)
    ax.fill([u_4, ll_4, ll_7, u_7], [4, 4, 7, 7], hatch="///", fill=False, edgecolor="gray", lw=0.8)
    ax.text(12, 8, "ML-CL", fontsize=8, color="dimgray")
    ax.axvline(LL_LH, color="black", lw=1.0, ls="--")
    ax.text(LL_LH + 1, 57, "LL = 50", fontsize=8, color="dimgray")
    for txt, x, y in [("CL", 36, 24), ("CH", 68, 46), ("ML ou OL", 30, 1.5), ("MH ou OH", 70, 16)]:
        ax.text(x, y, txt, fontsize=10, fontweight="bold")
    y_max = max(60.0, line_a(x_max) + 5)
    if tem_ponto:
        y_max = max(y_max, IP + 10)
        ax.scatter([LL], [IP], color="tab:red", s=55, zorder=5)
        ax.annotate(label or f"LL {fmt(LL, 0)} · IP {fmt(IP, 0)}", (LL, IP), xytext=(8, 8),
                    textcoords="offset points", fontsize=9, color="tab:red", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="tab:red", lw=0.6, alpha=0.95))
    elif NP:
        ax.text(0.5, 0.93, "Amostra não plástica (NP): sem ponto no gráfico", transform=ax.transAxes,
                ha="center", fontsize=9, color="dimgray")
    ax.set_xlim(0, x_max); ax.set_ylim(0, y_max)
    ax.set_xlabel("Limite de liquidez LL (%)"); ax.set_ylabel("Índice de plasticidade IP (%)")
    ax.set_title("Gráfico de plasticidade — Figura 17, Manual IPR-719", fontsize=10)
    ax.grid(True, ls=":", alpha=0.5)
    fig.tight_layout()
    return fig
