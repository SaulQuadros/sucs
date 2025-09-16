
# sucs_core.py
# Núcleo de classificação SUCS (conforme DNIT/SUCS).
# Pode ser importado tanto por scripts de terminal quanto pelo app Streamlit.

from datetime import datetime

LINE_A_SLOPE = 0.73  # IP = 0.73*(LL - 20)


# Mapa SUCS → faixa típica de CBR (ISC)
SUCS_CBR = {
    "GW": "40–80",
    "GP": "30–60",
    "GM": "20–60",
    "GC": "20–40",
    "SW": "20–40",
    "SP": "10–40",
    "SM": "10–40",
    "SC": "5–20",
    "ML": "≤15 (tipicamente 3–15)",
    "CL": "≤15 (tipicamente 3–10)",
    "MH": "≤10–15 (comum ≤10)",
    "CH": "≤15 (tipicamente 3–10)",
    "OL": "≤5 (muito baixos)",
    "OH": "≤5 (muito baixos)",
    "OL/OH": "≤5 (muito baixos)",
    "PT": "~1–3 (muito baixos; evita-se como subleito)",
    "PTA": "~1–3 (muito baixos; evita-se como subleito)",
    "PTB": "~1–3 (muito baixos; evita-se como subleito)",
}

import re
def cbr_for_group(grp: str) -> str | None:
    """Retorna a faixa típica de CBR para a classe SUCS.
    Trata variações como 'SP-SC', 'CL(ML)', 'OL/OH' etc."""
    if not grp:
        return None
    key = re.sub(r"\s+", "", grp.upper())
    key = key.replace("/", "-").replace("(", "-").replace(")", "-")
    key = re.sub(r"-+", "-", key).strip("-")
    # 1) exato
    if key in SUCS_CBR:
        return SUCS_CBR[key]
    # 2) componentes simples
    parts = [p for p in key.split("-") if p]
    for p in parts:
        if p in SUCS_CBR:
            return SUCS_CBR[p]
    # 3) normalizações específicas
    if key in {"OL-OH", "OH-OL"}:
        return SUCS_CBR.get("OL/OH")
    return None



DNIT_DESC = {
    "GW": "Pedregulhos bem graduados ou misturas de areia de pedregulho, com pouco ou nenhum fino.",
    "GP": "Pedregulhos mal graduados ou misturas de areia e pedregulho, com pouco ou nenhum fino.",
    "GM": "Pedregulhos siltosos ou misturas de pedregulho, areia e silte.",
    "GC": "Pedregulhos argilosos ou misturas de pedregulho, areia e argila.",
    "SW": "Areias bem graduadas ou areias pedregulhosas, com pouco ou nenhum fino.",
    "SP": "Areias mal graduadas ou areias pedregulosas, com pouco ou nenhum fino.",
    "SM": "Areias siltosas — misturas de areia e silte.",
    "SC": "Areias argilosas — misturas de areia e argila.",
    "ML": "Siltes inorgânicos; areias muito finas; areias finas siltosas e argilosas.",
    "CL": "Argilas inorgânicas de baixa e média plasticidade; argilas pedregulhosas, arenosas e siltosas.",
    "OL": "Siltes orgânicos; argilas siltosas orgânicas de baixa plasticidade.",
    "MH": "Siltes (micáceos), areias finas/siltes micáceos; siltes elásticos.",
    "CH": "Argilas inorgânicas de alta plasticidade.",
    "OH": "Argilas orgânicas de alta e média plasticidade.",
    "Pt": "Turfos e outros solos altamente orgânicos.",
}
def dnit_description_for_group(grp: str) -> str | None:
    if not grp:
        return None
    # Símbolo duplo (ex.: SW-SM): concatena descrições do primeiro e do segundo símbolo
    if "-" in grp:
        parts = [p.strip() for p in grp.split("-") if p.strip()]
        descs = [DNIT_DESC.get(p) for p in parts if DNIT_DESC.get(p)]
        if not descs:
            return None
        return " / ".join(descs) + " (limítrofe)."
    return DNIT_DESC.get(grp)


def _finalize(grp, report):
    desc = dnit_description_for_group(grp)
    if desc:
        report.append(f"Descrição DNIT: {desc}")
    cbr = cbr_for_group(grp)
    if cbr:
        report.append(f"CBR típico (ISC): {cbr}%")
    return grp, "\n".join(report)
def well_graded_letter(coarse_symbol, Cu, Cc):
    """
    Decide W/P quando finos < 5%.
    - Areias (S): Cu >= 6 e 1 <= Cc <= 3 -> W; senão P
    - Cascalhos (G): Cu >= 4 e 1 <= Cc <= 3 -> W; senão P
    Retorna 'W', 'P' ou None (se Cu/Cc não informados)
    """
    if Cu is None or Cc is None:
        return None
    try:
        Cu = float(Cu); Cc = float(Cc)
    except Exception:
        return None
    if coarse_symbol == "S":
        return "W" if (Cu >= 6 and 1 <= Cc <= 3) else "P"
    return "W" if (Cu >= 4 and 1 <= Cc <= 3) else "P"

def fines_nature(LL, LP):
    """'M' (siltoso) abaixo da linha A; 'C' (argiloso) acima da linha A. Retorna None se faltar dado."""
    try:
        LL = float(LL); LP = float(LP)
    except Exception:
        return None
    IP = max(0.0, LL - LP)
    lineA = LINE_A_SLOPE * (LL - 20.0)
    return "C" if IP >= lineA else "M"

def classify_sucs(data):
    """
    data: dict com chaves
      projeto, tecnico, amostra
      pct_retido_200 (0-100)
      pct_pedregulho_coarse, pct_areia_coarse (na fração > #200)
      LL, LP
      Cu, Cc (opcionais)
      organico (bool), turfa (bool)
    Retorna (grupo, relatorio_txt)
    """
    report = []
    projeto = data.get("projeto","")
    tecnico = data.get("tecnico","")
    amostra = data.get("amostra","")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report += [f"Projeto: {projeto}", f"Técnico: {tecnico}", f"Amostra: {amostra}", f"Data/hora: {now}", ""]

    pct_ret_200 = float(data.get("pct_retido_200", 0.0))
    pct_finos = max(0.0, 100.0 - pct_ret_200)

    LL = data.get("LL", None)
    LP = data.get("LP", None)
    IP = None
    if LL is not None and LP is not None:
        try:
            LL = float(LL); LP = float(LP)
            IP = max(0.0, LL - LP)
        except Exception:
            LL = LP = None

    organico = bool(data.get("organico", False))
    turfa = bool(data.get("turfa", False))

    report.append("Entradas")
    report.append(f"  % retido na #200: {pct_ret_200:.2f}%  |  % de finos: {pct_finos:.2f}%")
    if LL is not None and LP is not None:
        report.append(f"  LL = {LL:.2f} ; LP = {LP:.2f}  -> IP = {IP:.2f}")
    else:
        report.append("  LL/LP: não informados")

    # Turfa tem prioridade
    if turfa:
        report.append("Observação: material altamente orgânico (turfa).")
        return _finalize("Pt", report)

    # Split grossa vs fina
    if pct_ret_200 >= 50.0:
        # Fração grossa -> G vs S pela fração > #200 (pedregulho vs areia)
        pg = float(data.get("pct_pedregulho_coarse", 0.0))
        ps = float(data.get("pct_areia_coarse", 0.0))
        total = pg + ps
        if total > 0:
            pgn = 100.0 * pg / total
            psn = 100.0 * ps / total
        else:
            pgn = psn = 50.0
        coarse_symbol = "G" if pgn >= psn else "S"
        report.append(f"  Fração grossa predominante: {'cascalho (G)' if coarse_symbol=='G' else 'areia (S)'} "
                      f"(> #200: pedregulho {pgn:.1f}%, areia {psn:.1f}%)")

        if pct_finos < 5.0:
            Cu = data.get("Cu", None)
            Cc = data.get("Cc", None)
            W_or_P = well_graded_letter(coarse_symbol, Cu, Cc)
            if W_or_P is None:
                grp = coarse_symbol + "?"
                report.append("  Finos < 5%: seria GW/GP ou SW/SP; informe Cu/Cc para decidir W/P.")
            else:
                grp = coarse_symbol + W_or_P
                report.append(f"  Finos < 5% e graduação {'boa' if W_or_P=='W' else 'má'} -> {grp}")
            return _finalize(grp, report)

        if 5.0 <= pct_finos <= 12.0:
            nat = fines_nature(LL, LP)
            Cu = data.get("Cu", None); Cc = data.get("Cc", None)
            W_or_P = well_graded_letter(coarse_symbol, Cu, Cc)
            base = coarse_symbol if W_or_P is None else coarse_symbol + W_or_P
            second = coarse_symbol if nat is None else coarse_symbol + ("M" if nat=="M" else "C")
            grp = f"{base}-{second}".replace("GG","G").replace("SS","S")
            report.append(f"  Finos 5–12% (limítrofe): {grp}")
            return _finalize(grp, report)

        # >12% finos
        nat = fines_nature(LL, LP)
        if nat is None:
            grp = coarse_symbol + "?"
            report.append("  Finos > 12%: LL/LP ausentes para natureza dos finos (M/C).")
        else:
            grp = (coarse_symbol + nat).replace("GG","G").replace("SS","S")
            report.append(f"  Finos > 12% e finos {'siltosos' if nat=='M' else 'argilosos'} -> {grp}")
        return _finalize(grp, report)

    else:
        # Fração fina (solos finos)
        if organico:
            if LL is None:
                grp = "O?"
            else:
                grp = "OL" if LL < 50.0 else "OH"
            report.append(f"  Solo com aspecto orgânico -> {grp}")
            return _finalize(grp, report)

        nat = fines_nature(LL, LP)  # 'M' ou 'C'
        if nat is None or LL is None:
            report.append("  LL/LP ausentes: não é possível posicionar no gráfico de plasticidade.")
            return _finalize("M?/C?", report)
        L_or_H = "L" if LL < 50.0 else "H"
        grp = (("M" if nat=="M" else "C") + L_or_H)
        report.append(f"  Solo fino: {'silte' if nat=='M' else 'argila'}; LL {'< 50' if L_or_H=='L' else '≥ 50'} -> {grp}")
        return _finalize(grp, report)

def classify_dataframe(df):
    """Aplica classify_sucs linha a linha e retorna df com colunas 'grupo' e 'relatorio'."""
    out_groups = []
    out_reports = []
    for _, row in df.iterrows():
        data = row.to_dict()
        grp, rep = classify_sucs(data)
        out_groups.append(grp)
        out_reports.append(rep)
    res = df.copy()
    res["grupo"] = out_groups
    res["relatorio"] = out_reports
    return res
