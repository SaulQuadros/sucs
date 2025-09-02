
# sucs_core.py
# Núcleo de classificação SUCS (conforme DNIT/SUCS).
# Pode ser importado tanto por scripts de terminal quanto pelo app Streamlit.

from datetime import datetime

LINE_A_SLOPE = 0.73  # IP = 0.73*(LL - 20)

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
        return "Pt", "\n".join(report)

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
            return grp, "\n".join(report)

        if 5.0 <= pct_finos <= 12.0:
            nat = fines_nature(LL, LP)
            Cu = data.get("Cu", None); Cc = data.get("Cc", None)
            W_or_P = well_graded_letter(coarse_symbol, Cu, Cc)
            base = coarse_symbol if W_or_P is None else coarse_symbol + W_or_P
            second = coarse_symbol if nat is None else coarse_symbol + ("M" if nat=="M" else "C")
            grp = f"{base}-{second}".replace("GG","G").replace("SS","S")
            report.append(f"  Finos 5–12% (limítrofe): {grp}")
            return grp, "\n".join(report)

        # >12% finos
        nat = fines_nature(LL, LP)
        if nat is None:
            grp = coarse_symbol + "?"
            report.append("  Finos > 12%: LL/LP ausentes para natureza dos finos (M/C).")
        else:
            grp = (coarse_symbol + nat).replace("GG","G").replace("SS","S")
            report.append(f"  Finos > 12% e finos {'siltosos' if nat=='M' else 'argilosos'} -> {grp}")
        return grp, "\n".join(report)

    else:
        # Fração fina (solos finos)
        if organico:
            if LL is None:
                grp = "O?"
            else:
                grp = "OL" if LL < 50.0 else "OH"
            report.append(f"  Solo com aspecto orgânico -> {grp}")
            return grp, "\n".join(report)

        nat = fines_nature(LL, LP)  # 'M' ou 'C'
        if nat is None or LL is None:
            report.append("  LL/LP ausentes: não é possível posicionar no gráfico de plasticidade.")
            return "M?/C?", "\n".join(report)
        L_or_H = "L" if LL < 50.0 else "H"
        grp = (("M" if nat=="M" else "C") + L_or_H)
        report.append(f"  Solo fino: {'silte' if nat=='M' else 'argila'}; LL {'< 50' if L_or_H=='L' else '≥ 50'} -> {grp}")
        return grp, "\n".join(report)

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
