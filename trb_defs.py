# trb_defs.py
# Definições por grupo TRB (HRB/AASHTO) conforme o Manual de Pavimentação DNIT (IPR-719/2006,
# versão corrigida com a Errata 1) — Tabela 4 (quadro TRB), Tabelas 11 e 14.

GROUP_DEF_RESUMO = {
    "A-1-a": "Materiais contendo, principalmente, fragmentos de pedra ou pedregulho, com ou sem material "
             "fino bem graduado funcionando como aglutinante.",
    "A-1-b": "Materiais constituídos, principalmente, de areia grossa, com ou sem aglutinante de solo bem graduado.",
    "A-3":   "Areia fina de praia ou de deserto, sem silte ou argila, ou com pequena quantidade de silte não "
             "plástico; inclui misturas de areia fina mal graduada com quantidades limitadas de areia grossa "
             "e pedregulho depositados pelas correntes.",
    "A-2-4": "Material granular (≤ 35% passando na nº 200) com finos siltosos de LL ≤ 40 e IP ≤ 10.",
    "A-2-5": "Material granular (≤ 35% passando na nº 200) com finos siltosos de LL ≥ 41 e IP ≤ 10.",
    "A-2-6": "Material granular (≤ 35% passando na nº 200) com finos argilosos de LL ≤ 40 e IP ≥ 11.",
    "A-2-7": "Material granular (≤ 35% passando na nº 200) com finos argilosos de LL ≥ 41 e IP ≥ 11.",
    "A-4":   "Solos siltosos não plásticos ou moderadamente plásticos (LL ≤ 40, IP ≤ 10).",
    "A-5":   "Solos siltosos de LL elevado (LL ≥ 41, IP ≤ 10), frequentemente micáceos ou diatomáceos, elásticos.",
    "A-6":   "Solos argilosos plásticos de LL baixo (LL ≤ 40, IP ≥ 11).",
    "A-7-5": "Solos argilosos de LL elevado com IP moderado em relação ao LL (IP ≤ LL − 30).",
    "A-7-6": "Solos argilosos de LL elevado com IP alto em relação ao LL (IP > LL − 30), sujeitos a elevada variação de volume.",
}

# Linha "Comportamento como subleito" do quadro TRB
SUBLEITO_TX = {
    "granular": "Excelente a bom.",
    "fino": "Sofrível a mau."
}

# Linha "Índice de Grupo" do quadro TRB (valor máximo por grupo)
IG_TIPICO_MAX = {
    "A-1-a": 0, "A-1-b": 0, "A-3": 0,
    "A-2-4": 0, "A-2-5": 0, "A-2-6": 4, "A-2-7": 4,
    "A-4": 8, "A-5": 12, "A-6": 16, "A-7-5": 20, "A-7-6": 20,
}

# Linha "Materiais constituintes" do quadro TRB
MATERIAIS_CONSTITUINTES = {
    "A-1-a": "Fragmentos de pedras, pedregulho fino e areia.",
    "A-1-b": "Fragmentos de pedras, pedregulho fino e areia.",
    "A-3":   "Fragmentos de pedras, pedregulho fino e areia.",
    "A-2-4": "Pedregulho ou areias siltosos ou argilosos.",
    "A-2-5": "Pedregulho ou areias siltosos ou argilosos.",
    "A-2-6": "Pedregulho ou areias siltosos ou argilosos.",
    "A-2-7": "Pedregulho ou areias siltosos ou argilosos.",
    "A-4":   "Solos siltosos.",
    "A-5":   "Solos siltosos.",
    "A-6":   "Solos argilosos.",
    "A-7-5": "Solos argilosos.",
    "A-7-6": "Solos argilosos.",
}

# Tabela 14 — Valores prováveis de CBR para os grupos da classificação TRB
TRB_CBR = {
    "A-1-a": "40 a mais de 80",
    "A-1-b": "20 a mais de 80",
    "A-2-4": "25 a mais de 80", "A-2-5": "25 a mais de 80",
    "A-2-6": "12 a 30", "A-2-7": "12 a 30",
    "A-3":   "15 a 40",
    "A-4":   "4 a 25",
    "A-5":   "menos de 2 a 10",
    "A-6":   "menos de 2 a 15", "A-7-5": "menos de 2 a 15", "A-7-6": "menos de 2 a 15",
}

# Tabela 11 — Interrelações entre a classificação TRB e a unificada (SUCS)
TRB_PARA_SUCS = {
    #          mais provável               possível               possível, mas improvável
    "A-1-a": ("GW, GP",                    "SW, SP",              "GM, SM"),
    "A-1-b": ("SW, SP, GM, SM",            "GP",                  "—"),
    "A-3":   ("SP",                        "—",                   "SW, GP"),
    "A-2-4": ("GM, SM",                    "GC, SC",              "GW, GP, SW, SP"),
    "A-2-5": ("GM, SM",                    "—",                   "GW, GP, SW, SP"),
    "A-2-6": ("GC, SC",                    "GM, SM",              "GW, GP, SW, SP"),
    "A-2-7": ("GM, GC, SM, SC",            "—",                   "GW, GP, SW, SP"),
    "A-4":   ("ML, OL",                    "CL, SM, SC",          "GM, GC"),
    "A-5":   ("OH, MH, ML, OL",            "—",                   "SM, GM"),
    "A-6":   ("CL",                        "ML, OL, SC",          "GC, SM, GC, SC"),
    "A-7-5": ("OH, MH",                    "ML, OL, CH",          "GM, SM, GC, SC"),
    "A-7-6": ("CH, CL",                    "ML, OL, SC",          "OH, MH, GC, GM, SM"),
}


def get_definicao(group: str) -> str:
    return GROUP_DEF_RESUMO.get(group, "—")


def get_subleito_text(group: str) -> str:
    fam = "granular" if group.startswith(("A-1", "A-2", "A-3")) else "fino"
    return SUBLEITO_TX[fam]


def ig_tipico_max(group: str) -> int:
    return IG_TIPICO_MAX.get(group, 20)


def get_materiais(group: str) -> str:
    return MATERIAIS_CONSTITUINTES.get(group, "—")


def cbr_for_trb(group: str) -> str | None:
    return TRB_CBR.get(group)


def sucs_provavel(group: str) -> tuple[str, str, str] | None:
    return TRB_PARA_SUCS.get(group)
