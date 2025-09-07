
# trb_defs.py
GROUP_DEF_RESUMO = {
    "A-1-a": "Materiais granulares de alta qualidade, com baixos finos e bem graduados; uso favorável como subleito.",
    "A-1-b": "Semelhante ao A-1-a, porém com fração fina um pouco maior; geralmente bom como subleito.",
    "A-3":   "Areias finas predominantemente não plásticas (praia/duna), sensíveis à umidade; desempenho bom a regular.",
    "A-2-4": "Granulares com finos siltosos (LL ≤ 40).",
    "A-2-5": "Granulares com finos siltosos (LL > 40).",
    "A-2-6": "Granulares com finos argilosos (LL ≤ 40).",
    "A-2-7": "Granulares com finos argilosos (LL > 40).",
    "A-4":   "Solos siltosos, baixa a moderada plasticidade.",
    "A-5":   "Solos siltosos de alta plasticidade (micáceos/diatomáceos), elásticos.",
    "A-6":   "Solos argilosos plásticos de LL baixo.",
    "A-7-5": "Argilas de LL alto com IP moderado (IP ≤ LL − 30).",
    "A-7-6": "Argilas de LL alto com IP elevado (IP > LL − 30).",
}

GROUP_DEF_OFICIAL = {}

SUBLEITO_TX = {
    "granular": "Excelente a bom.",
    "fino": "Sofrível a mau."
}

IG_TIPICO_MAX = {
    "A-1-a": 0, "A-1-b": 0, "A-3": 0,
    "A-2-4": 12, "A-2-5": 12, "A-2-6": 12, "A-2-7": 12,
    "A-4": 8, "A-5": 12, "A-6": 16, "A-7-5": 20, "A-7-6": 20,
}

def get_definicao(group: str, preferir_oficial: bool = False) -> str:
    if preferir_oficial and group in GROUP_DEF_OFICIAL:
        return GROUP_DEF_OFICIAL[group]
    return GROUP_DEF_RESUMO.get(group, "—")

def get_subleito_text(group: str) -> str:
    fam = "granular" if group.startswith(("A-1", "A-2", "A-3")) else "fino"
    return SUBLEITO_TX[fam]

def ig_tipico_max(group: str) -> int:
    return IG_TIPICO_MAX.get(group, 20)
