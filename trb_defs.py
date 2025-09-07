
# trb_defs.py
# Definições/Resumos para grupos TRB (HRB/AASHTO) segundo DNIT (resumo autoral).
# Substitua/complete por texto oficial, se desejar, mantendo as chaves.

GROUP_DEF_RESUMO = {
    "A-1-a": "Materiais granulares de alta qualidade, com baixos finos; desempenho excelente a bom como subleito.",
    "A-1-b": "Granulares bem graduados, um pouco mais finos que A-1-a; geralmente bons como subleito.",
    "A-3":   "Areias finas predominantemente não plásticas; sensíveis à umidade; desempenho bom a regular.",
    "A-2-4": "Granulares com finos predominantemente siltosos (LL ≤ 40); comportamento regular a bom.",
    "A-2-5": "Granulares com finos siltosos (LL > 40); desempenho típico regular.",
    "A-2-6": "Granulares com finos argilosos (LL ≤ 40); comportamento regular a sofrível.",
    "A-2-7": "Granulares com finos argilosos (LL > 40); comportamento sofrível.",
    "A-4":   "Siltes de baixa plasticidade; comportamento regular a sofrível.",
    "A-5":   "Siltes de alta plasticidade; comportamento sofrível a mau.",
    "A-6":   "Argilas de baixa plasticidade (LL ≤ 40); comportamento sofrível a mau.",
    "A-7-5": "Argilas de alta plasticidade com IP relativamente menor (≤ LL−30); mau como subleito.",
    "A-7-6": "Argilas de alta plasticidade com IP relativamente maior (> LL−30); mau como subleito.",
}

# Opcional: mapa para textos oficiais completos (preencha futuramente)
GROUP_DEF_OFICIAL = {
    # "A-7": "Grupo A-7 - ... (cole aqui o texto oficial completo do DNIT)"
}

def get_definicao(group: str, preferir_oficial: bool = False) -> str:
    if preferir_oficial and group in GROUP_DEF_OFICIAL:
        return GROUP_DEF_OFICIAL[group]
    return GROUP_DEF_RESUMO.get(group, "—")
