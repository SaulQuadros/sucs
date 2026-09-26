# sucs_core.py
# Núcleo de classificação SUCS conforme o Manual de Pavimentação DNIT (IPR-719/2006, versão corrigida
# com a Errata 1): Tabela 5, Figura 17 (gráfico de plasticidade) e fluxograma de identificação em
# laboratório. Pode ser importado tanto por scripts de terminal quanto pelo app Streamlit.

from datetime import datetime
import math
import re

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


def _finalize(grp, report):
    desc = dnit_description_for_group(grp)
    if desc:
        report.append(f"Descrição (Tabela 5, Manual IPR-719): {desc}")
    cbr = cbr_for_group(grp)
    if cbr:
        report.append(f"CBR provável (Tabela 13, Manual IPR-719): {cbr}%")
    trb = trb_for_group(grp)
    if trb:
        s, (mp, p, pi) = trb
        report.append(f"TRB (Tabela 12, Manual IPR-719) para {s}: mais provável {mp}; possível {p}; "
                      f"possível, mas improvável {pi}")
    return grp, "\n".join(report)


def classify_sucs(data):
    """
    data: dict com chaves
      projeto, tecnico, amostra
      pct_retido_200 (0-100)
      pct_pedregulho_coarse, pct_areia_coarse (na fração > #200; qualquer escala, são normalizados)
      LL, LP ; NP (bool, opcional)
      Cu, Cc (opcionais) ou D10, D30, D60 em mm (opcionais)
      organico (bool), turfa (bool)
    Retorna (grupo, relatorio_txt)
    """
    report = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report += [f"Projeto: {data.get('projeto') or ''}", f"Técnico: {data.get('tecnico') or ''}",
               f"Amostra: {data.get('amostra') or ''}", f"Data/hora: {now}", ""]

    pct_ret_200 = _num(data.get("pct_retido_200"))
    if pct_ret_200 is None or not (0.0 <= pct_ret_200 <= 100.0):
        raise ValueError("Informe a % retida na peneira #200 (0 a 100).")
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

    Cu, Cc = _num(data.get("Cu")), _num(data.get("Cc"))
    if Cu is None or Cc is None:
        Cu2, Cc2 = cu_cc(data.get("D10"), data.get("D30"), data.get("D60"))
        if Cu2 is not None:
            Cu, Cc = Cu2, Cc2
            report.append(f"Cu = D60/D10 = {Cu:.2f} ; Cc = D30²/(D60·D10) = {Cc:.2f}")

    organico = _bool(data.get("organico", False))
    turfa = _bool(data.get("turfa", False))

    report.append("Entradas")
    report.append(f"  % retido na #200: {pct_ret_200:.2f}%  |  % de finos: {pct_finos:.2f}%")
    if NP:
        report.append("  IP = NP (não plástico)")
    elif IP is not None:
        report.append(f"  LL = {LL:.2f} ; LP = {LP:.2f}  -> IP = {IP:.2f}  (linha A: {line_a(LL):.2f})")
    else:
        report.append("  LL/LP: não informados")
    if Cu is not None and Cc is not None:
        report.append(f"  Cu = {Cu:.2f} ; Cc = {Cc:.2f}")

    if turfa:
        report.append("Observação: material altamente orgânico (turfa).")
        return _finalize("PT", report)

    zone = plasticity_zone(LL, LP, NP)

    # Tabela 5: mais de 50% retido na #200 → granulação grossa
    if pct_ret_200 > 50.0:
        pg = _num(data.get("pct_pedregulho_coarse")) or 0.0
        ps = _num(data.get("pct_areia_coarse")) or 0.0
        total = pg + ps
        if total <= 0:
            raise ValueError("Solo grosso: informe % de pedregulho e de areia na fração > #200.")
        pgn = 100.0 * pg / total
        # Tabela 5: pedregulho quando 50% ou mais da fração graúda fica retida na #4
        coarse = "G" if pgn >= 50.0 else "S"
        report.append(f"  Granulação grossa (> 50% retido na #200); fração graúda: pedregulho {pgn:.1f}%, "
                      f"areia {100 - pgn:.1f}% -> {'pedregulho (G)' if coarse == 'G' else 'areia (S)'}")

        wp = well_graded_letter(coarse, Cu, Cc)
        if pct_finos < 5.0:
            if wp is None:
                grp = f"{coarse}W/{coarse}P"
                report.append("  Finos < 5%: informe Cu e Cc (ou D10, D30, D60) para decidir W (bem) ou P (mal graduado).")
            else:
                grp = coarse + wp
                report.append(f"  Finos < 5% e graduação {'boa' if wp == 'W' else 'má'} -> {grp}")
            return _finalize(grp, report)

        if pct_finos <= 12.0:
            # Caso limite: símbolo duplo pela granulometria e pela plasticidade (ex.: GW-GM)
            second = None if zone is None else coarse + ("M" if zone == "M" else "C")
            first = None if wp is None else coarse + wp
            grp = f"{first or coarse + 'W/' + coarse + 'P'}-{second or coarse + 'M/' + coarse + 'C'}"
            report.append(f"  Finos entre 5% e 12% (caso limite, símbolo duplo): {grp}")
            if first is None:
                report.append("  Informe Cu e Cc (ou D10, D30, D60) para decidir W/P.")
            if second is None:
                report.append("  Informe LL e LP (ou NP) para decidir M/C.")
            elif zone == "MC":
                report.append("  Finos na zona hachurada: adotado o sufixo C (fino plástico).")
            return _finalize(grp, report)

        # Finos > 12%
        if zone is None:
            grp = f"{coarse}M/{coarse}C"
            report.append("  Finos > 12%: informe LL e LP (ou NP) para decidir M/C.")
        elif zone == "MC":
            grp = f"{coarse}M-{coarse}C"
            report.append(f"  Finos > 12% na zona hachurada (4 ≤ IP ≤ 7, acima da linha A) -> {grp}")
        else:
            grp = coarse + ("M" if zone == "M" else "C")
            report.append(f"  Finos > 12% {'abaixo' if zone == 'M' else 'acima'} da linha A -> {grp}")
        return _finalize(grp, report)

    # Granulação fina (50% ou mais passando na #200)
    report.append("  Granulação fina (50% ou mais passando na #200)")
    if zone is None:
        report.append("  LL/LP ausentes: não é possível posicionar no gráfico de plasticidade.")
        return _finalize("ML/CL", report)
    LLv = LL if LL is not None else 0.0
    LH = "L" if LLv <= LL_LH else "H"
    if organico:
        if zone == "M":
            grp = "O" + LH
            report.append(f"  Orgânico, abaixo da linha A, LL {'≤' if LH == 'L' else '>'} 50 -> {grp}")
            return _finalize(grp, report)
        report.append("  Aviso: marcado como orgânico, mas o ponto está acima da linha A; "
                      "o Manual classifica pela plasticidade (CL/CH).")
    if zone == "MC":
        grp = "ML-CL"
        report.append("  Zona hachurada (4 ≤ IP ≤ 7, acima da linha A) -> ML-CL")
    else:
        grp = ("M" if zone == "M" else "C") + LH
        report.append(f"  {'Silte (abaixo' if zone == 'M' else 'Argila (acima'} da linha A); "
                      f"LL {'≤' if LH == 'L' else '>'} 50 -> {grp}")
    return _finalize(grp, report)


# Planilha-modelo: um exemplo por grupo (conferidos em tests/test_sucs.py).
EXEMPLOS = [
    ("GW", "Pedregulho bem graduado, poucos finos", dict(pct_retido_200=97, pct_pedregulho_coarse=70, pct_areia_coarse=30, NP=True, Cu=8, Cc=2.0)),
    ("GP", "Pedregulho mal graduado, poucos finos", dict(pct_retido_200=96, pct_pedregulho_coarse=60, pct_areia_coarse=40, NP=True, Cu=2, Cc=0.6)),
    ("GM", "Pedregulho siltoso", dict(pct_retido_200=75, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=40, LP=27)),
    ("GC", "Pedregulho argiloso", dict(pct_retido_200=75, pct_pedregulho_coarse=60, pct_areia_coarse=40, LL=40, LP=20)),
    ("SW", "Areia bem graduada (Cu/Cc pelos diâmetros)", dict(pct_retido_200=97, pct_pedregulho_coarse=30, pct_areia_coarse=70, NP=True, D10=0.1, D30=0.3, D60=0.9)),
    ("SP", "Areia mal graduada", dict(pct_retido_200=96, pct_pedregulho_coarse=30, pct_areia_coarse=70, NP=True, Cu=3, Cc=0.8)),
    ("SM", "Areia siltosa", dict(pct_retido_200=75, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=40, LP=27)),
    ("SC", "Areia argilosa", dict(pct_retido_200=75, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=40, LP=20)),
    ("SW-SC", "Areia bem graduada com 8% de finos argilosos", dict(pct_retido_200=92, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=30, LP=15, Cu=7, Cc=2)),
    ("SM-SC", "Areia com finos na zona hachurada", dict(pct_retido_200=70, pct_pedregulho_coarse=30, pct_areia_coarse=70, LL=25, LP=19)),
    ("ML", "Silte de baixa compressibilidade", dict(pct_retido_200=30, LL=35, LP=25)),
    ("CL", "Argila de baixa a média plasticidade", dict(pct_retido_200=30, LL=35, LP=22)),
    ("ML-CL", "Fino na zona hachurada", dict(pct_retido_200=30, LL=25, LP=19)),
    ("OL", "Silte orgânico de baixa plasticidade", dict(pct_retido_200=30, LL=35, LP=25, organico=True)),
    ("MH", "Silte elástico (LL alto)", dict(pct_retido_200=30, LL=70, LP=40)),
    ("CH", "Argila de alta plasticidade", dict(pct_retido_200=30, LL=70, LP=25)),
    ("OH", "Argila orgânica de LL alto", dict(pct_retido_200=30, LL=60, LP=35, organico=True)),
    ("PT", "Turfa", dict(pct_retido_200=10, LL=150, LP=50, organico=True, turfa=True)),
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
