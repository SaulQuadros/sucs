# -*- coding: utf-8 -*-
# didatica/glossario_mct.py
# Glossário de termos técnicos da classificação MCT (DNIT 258/2023-ME e DNIT 259/2023-CLA).
# Fonte única das definições usadas no "Ex. numérico" do app. Os símbolos estão em LaTeX (KaTeX) para
# o st.markdown do Streamlit. Os valores numéricos do exemplo NÃO ficam aqui: são calculados nas etapas.

GLOSSARIO = {
    "mct": dict(
        termo="MCT (Miniatura, Compactado, Tropical)", simbolo="",
        unidade="—", norma="DNIT 259/2023-CLA, seção 1",
        o_que_e="Metodologia de Nogami e Villibor para classificar **solos finos tropicais** (fração que passa na "
                "peneira nº 10, 2 mm) com corpos de prova miniatura (50 mm de diâmetro). Separa os solos de "
                "**comportamento laterítico (L)** dos de **comportamento não laterítico (N)**.",
        no_ensaio="Reúne dois ensaios da DNIT 258/2023-ME: a compactação Mini-MCV e a perda de massa por imersão.",
        nas_equacoes="É o método; o resultado é um dos sete grupos do ábaco."),
    "cp": dict(
        termo="Corpo de prova", simbolo="CP", unidade="—", norma="DNIT 258/2023-ME, seções 4 a 7",
        o_que_e="Amostra compactada no molde cilíndrico de 50 mm do equipamento miniatura, com cerca de 200 g de "
                "solo úmido que passa na peneira nº 10.",
        no_ensaio="Moldam-se vários CPs, cada um com um teor de umidade diferente (tipicamente cinco). Cada CP "
                  "gera uma curva de deformabilidade, um Mini-MCV, uma altura final e um Pi.",
        nas_equacoes="Índice das grandezas medidas (uma linha por CP nas tabelas)."),
    "hc": dict(
        termo="Teor de umidade de compactação", simbolo="$h_c$", unidade="%", norma="DNIT 258/2023-ME, seção 3.11",
        o_que_e="Umidade do solo no momento da compactação, em porcentagem da massa seca.",
        no_ensaio="Determinada em cápsula, com secagem em estufa, para cada CP.",
        nas_equacoes="Abscissa da curva de compactação e denominador de $d'$ ($\\Delta h_c$). Dá a massa seca: "
                     "$M_s = m_u/(1 + h_c/100)$."),
    "n": dict(
        termo="Número de golpes e série de golpes", simbolo="$n$", unidade="golpes (acumulados)",
        norma="DNIT 258/2023-ME, seção 3.6",
        o_que_e="Golpes acumulados do soquete (2,27 kg, queda de 30,5 cm). **Série de Parsons**: 1, 2, 3, 4, 6, 8, "
                "12, 16, 24, 32, 48, 64, 96, 128, 192, 256. **Série Simplificada**: 1, 3, 6, 10, 20, 30, 40, 60… "
                "A de Parsons é recomendada para solos próximos do limite entre as classes L e N (Nota 1).",
        no_ensaio="Após cada número da série, lê-se a altura do CP; para-se quando o afundamento fica desprezível "
                  "ou aos 256 golpes.",
        nas_equacoes="Aparece como $10\\cdot\\log_{10} n$ no eixo das curvas de deformabilidade. Na série de "
                     "Parsons, a curva de compactação de referência é a de 12 golpes."),
    "an_altura": dict(
        termo="Altura do CP após n golpes", simbolo="$A_n$", unidade="mm", norma="DNIT 258/2023-ME, seção 3.7",
        o_que_e="Altura do corpo de prova depois de $n$ golpes.",
        no_ensaio="O extensômetro mede o deslocamento do soquete; a altura vem de "
                  "$A_n = K_a - \\text{leitura}$, com $K_a$ constante do equipamento (Figura A8 da norma).",
        nas_equacoes="Entra no afundamento e no cálculo da massa específica aparente seca."),
    "a4n": dict(
        termo="Altura após 4n golpes", simbolo="$A_{4n}$", unidade="mm", norma="DNIT 258/2023-ME, seção 3.7 a)",
        o_que_e="Altura do CP após o quádruplo dos golpes (ex.: para $n = 3$, $A_{4n} = A_{12}$).",
        no_ensaio="Lida na mesma série de golpes.",
        nas_equacoes="Referência do afundamento na série de Parsons."),
    "afundamento": dict(
        termo="Afundamento", simbolo="$a_n$", unidade="mm", norma="DNIT 258/2023-ME, seção 3.7, Equação (1)",
        o_que_e="Quanto o CP ainda se compacta quando o número de golpes é multiplicado por quatro. Grande: solo "
                "ainda fofo para aquela energia; pequeno: próximo da densidade máxima.",
        no_ensaio="Calculado para cada $n$ que tenha leitura em $4n$.",
        nas_equacoes="Parsons: $a_n = A_n - A_{4n}$. Simplificada: $a_n = A_n - A_f$."),
    "deformabilidade": dict(
        termo="Curva de deformabilidade", simbolo="", unidade="—",
        norma="DNIT 258/2023-ME, seção 3.8; Figuras A9 e A10",
        o_que_e="Para cada umidade, afundamento $a_n$ (ordenadas) contra o número de golpes em escala "
                "logarítmica, plotado como $10\\cdot\\log_{10} n$.",
        no_ensaio="Uma curva por CP; os mais úmidos atingem 2 mm com menos golpes e ficam à esquerda.",
        nas_equacoes="Dela saem o Mini-MCV de cada CP e o coeficiente $c'$."),
    "bn": dict(
        termo="Golpes para afundamento de 2 mm", simbolo="$B_n$", unidade="golpes",
        norma="DNIT 258/2023-ME, seção 3.9",
        o_que_e="Número de golpes em que a curva de deformabilidade cruza $a_n = 2$ mm.",
        no_ensaio="Obtido por interpolação entre os dois pontos da curva que envolvem 2 mm.",
        nas_equacoes="Argumento do logaritmo no Mini-MCV."),
    "mini_mcv": dict(
        termo="Mini-MCV (Moisture Condition Value, miniatura)", simbolo="Mini-MCV", unidade="adimensional",
        norma="DNIT 258/2023-ME, seção 3.9, Equação (3)",
        o_que_e="Medida da energia necessária para compactar o solo naquela umidade: quanto maior, mais golpes "
                "foram precisos (solo mais seco). Há um valor por CP.",
        no_ensaio="Calculado em cada curva de deformabilidade.",
        nas_equacoes="$\\text{Mini-MCV} = 10\\cdot\\log_{10}(B_n)$. É a abscissa das curvas de altura final e de "
                     "Pi, e define a curva de referência (Mini-MCV = 10) para $c'$."),
    "af": dict(
        termo="Altura final do CP", simbolo="$A_f$", unidade="mm",
        norma="DNIT 258/2023-ME, seção 3.7 b); DNIT 259/2023-CLA, seção 3.8",
        o_que_e="Altura do CP após o último golpe aplicado.",
        no_ensaio="Última altura lida de cada CP.",
        nas_equacoes="Na classificação, a curva $A_f$ × Mini-MCV dá a altura final no Mini-MCV = 10, que define o "
                     "critério de densidade de $P_i'$. Na fórmula de Pi, corresponde a $L_{cp}$."),
    "trecho": dict(
        termo="Trecho retilíneo mais inclinado", simbolo="", unidade="—",
        norma="DNIT 259/2023-CLA, seção 3.4; DNIT 258/2023-ME, seções 3.10 e 3.12",
        o_que_e="Parte da curva que é reta (ou assimilável a uma reta) e tem a maior inclinação.",
        no_ensaio="Na norma a escolha é gráfica. No app, é a janela de três pontos consecutivos com maior "
                  "inclinação (reta ajustada), destacada nos gráficos.",
        nas_equacoes="Define $c'$ (na curva de deformabilidade) e $d'$ (no ramo seco da curva de compactação)."),
    "c": dict(
        termo="Coeficiente de argilosidade", simbolo="$c'$", unidade="adimensional (a norma indica mm)",
        norma="DNIT 258/2023-ME, seção 3.10, Equação (4); Figura A10",
        o_que_e="Inclinação do trecho retilíneo mais inclinado da curva de deformabilidade com Mini-MCV = 10. "
                "Valores baixos indicam areias e solos arenosos; altos, argilas.",
        no_ensaio="Como raramente um CP tem Mini-MCV exatamente 10, usa-se a curva interpolada entre as curvas "
                  "vizinhas (Nota 3 da seção 3.10).",
        nas_equacoes="$c' = \\left|\\Delta a_n / \\Delta(\\text{Mini-MCV})\\right|$. É a abscissa do ábaco; na "
                     "região laterítica, $c' < 0{,}70$ → LA; 0,70 a 1,50 → LA′; ≥ 1,50 → LG′."),
    "meas": dict(
        termo="Massa específica aparente seca", simbolo="MEAS", unidade="kg/m³",
        norma="DNIT 258/2023-ME, seção 3.11",
        o_que_e="Massa de sólidos por unidade de volume do CP compactado.",
        no_ensaio="Calculada para cada CP e número de golpes, com a massa seca e a altura naquele golpe "
                  "(área do molde de 50 mm: 19,635 cm²).",
        nas_equacoes="$\\text{MEAS} = M_s/(A\\cdot h)$. É a ordenada da curva de compactação e o numerador de $d'$."),
    "compactacao": dict(
        termo="Curva de compactação Mini-MCV; ramos seco e úmido", simbolo="", unidade="—",
        norma="DNIT 258/2023-ME, seção 3.11; Figura A11",
        o_que_e="Para cada número de golpes, o gráfico MEAS × $h_c$: cresce até um máximo (**ramo seco**) e depois "
                "cai (**ramo úmido**), como no Proctor.",
        no_ensaio="Recomenda-se traçar ao menos cinco curvas: na série de Parsons, 8, 10, 12, 16 e 24 golpes.",
        nas_equacoes="A curva de 12 golpes (Parsons) ou de 10 golpes (Simplificada) é a de referência para $d'$."),
    "d": dict(
        termo="Coeficiente d′", simbolo="$d'$", unidade="kg/m³ por % de umidade",
        norma="DNIT 258/2023-ME, seção 3.12; Figura A11",
        o_que_e="Inclinação do trecho retilíneo mais inclinado do **ramo seco** da curva de compactação de "
                "referência. Ramo seco íngreme (d′ alto) é típico de solos lateríticos argilosos.",
        no_ensaio="Lido na curva de 12 golpes (Parsons) ou 10 golpes (Simplificada).",
        nas_equacoes="$d' = \\Delta\\text{MEAS}/\\Delta h_c$. Entra em $e'$ pelo termo $20/d'$: quanto maior "
                     "$d'$, menor $e'$."),
    "pi": dict(
        termo="Perda de massa por imersão", simbolo="$P_i$", unidade="%",
        norma="DNIT 258/2023-ME, seção 3.13, Equação (6)",
        o_que_e="Porcentagem da massa seca que se desprende da parte extrudada do CP (cerca de 10 mm) imersa em "
                "água. Mede a estabilidade do solo compactado na água: solos lateríticos perdem pouco.",
        no_ensaio="O CP é extrudado cerca de 10 mm e imerso; recolhe-se e seca-se o material desprendido. Há um "
                  "Pi por CP.",
        nas_equacoes="$P_i = 100\\cdot\\dfrac{M_d\\cdot L_{cp}}{M_s\\cdot L_{ex}}\\cdot F_c$. Os valores formam a "
                     "curva Pi × Mini-MCV, da qual se lê $P_i'$."),
    "pi_vars": dict(
        termo="Variáveis da fórmula de Pi", simbolo="$M_d$, $M_s$, $L_{cp}$, $L_{ex}$, $F_c$", unidade="g, mm, —",
        norma="DNIT 258/2023-ME, seção 3.13",
        o_que_e="$M_d$: massa seca desprendida (g). $M_s$: massa seca do CP íntegro (g). $L_{cp}$: altura do CP "
                "íntegro, igual à altura final (mm). $L_{ex}$: altura da parte extrudada, normalmente 10 mm. "
                "$F_c$: 1 para desprendimento normal; 0,5 para desprendimento em monobloco coeso.",
        no_ensaio="$M_s \\cdot L_{ex}/L_{cp}$ é a massa seca da parte extrudada; por isso, com essa massa "
                  "($M_{ex}$), a fórmula fica $P_i = 100\\cdot M_d/M_{ex}\\cdot F_c$.",
        nas_equacoes="Todas entram na Equação (6) da DNIT 258/2023-ME."),
    "densidade": dict(
        termo="Baixa e alta densidade", simbolo="", unidade="—", norma="DNIT 259/2023-CLA, seção 3.8 b)",
        o_que_e="Enquadramento pela altura final no Mini-MCV = 10: $A_f \\geq 48{,}0$ mm → baixa densidade; "
                "$A_f < 48{,}0$ mm → alta densidade. Como a massa do CP é fixa, altura menor significa densidade "
                "maior.",
        no_ensaio="Lida na curva $A_f$ × Mini-MCV.",
        nas_equacoes="Define em qual Mini-MCV (10 ou 15) se lê $P_i'$."),
    "pi_ref": dict(
        termo="Perda de massa por imersão de referência", simbolo="$P_i'$", unidade="%",
        norma="DNIT 259/2023-CLA, seção 3.8",
        o_que_e="Valor de Pi usado na classificação.",
        no_ensaio="Baixa densidade: Pi no Mini-MCV = 10. Alta densidade: Pi no Mini-MCV = 15. Lido na curva Pi × "
                  "Mini-MCV.",
        nas_equacoes="Entra em $e'$ pelo termo $P_i'/100$."),
    "e": dict(
        termo="Índice de laterização", simbolo="$e'$", unidade="adimensional",
        norma="DNIT 259/2023-CLA, seção 3.9, Equação (1)",
        o_que_e="Combina a perda por imersão e a inclinação do ramo seco. **Valores baixos indicam comportamento "
                "laterítico** (pouca perda de massa e ramo seco íngreme).",
        no_ensaio="Calculado a partir de $P_i'$ e $d'$.",
        nas_equacoes="$e' = \\sqrt[3]{P_i'/100 + 20/d'}$. É a ordenada do ábaco; a fronteira entre lateríticos e "
                     "não lateríticos fica em $e' = 1{,}15$ para $c' \\geq 0{,}70$ e sobe até 1,40 para os solos "
                     "arenosos."),
    "abaco": dict(
        termo="Ábaco de classificação (gráfico de referência)", simbolo="", unidade="—",
        norma="DNIT 259/2023-CLA, Anexo A, Figura A1",
        o_que_e="Gráfico $c'$ (0 a 2,5) × $e'$ (0,5 a 2,2) dividido em sete regiões, com vértices cotados em "
                "(0,27; 2,2), (0,45; 1,75), (0,59; 1,4), (0,70; 1,15), (1,7; 1,15) e a vertical $c' = 1{,}5$.",
        no_ensaio="—",
        nas_equacoes="O grupo é a região onde cai o ponto $(c', e')$. Perto da fronteira L|N valem os critérios do "
                     "item 5.1 c)."),
    "grupos": dict(
        termo="Classes e grupos da classificação MCT", simbolo="L, N, A, A′, S′, G′", unidade="—",
        norma="DNIT 259/2023-CLA, Anexos A a C",
        o_que_e="**L** = laterítico; **N** = não laterítico; **A** = areia; **A′** = arenoso; **S′** = siltoso; "
                "**G′** = argiloso. Lateríticos: LA, LA′, LG′. Não lateríticos: NA, NA′, NS′, NG′.",
        no_ensaio="—",
        nas_equacoes="O Anexo B traz as propriedades típicas de cada grupo; o Anexo C, descrições e correlações "
                     "pedológicas."),
}


def texto_markdown(chave: str) -> str:
    """Verbete formatado para o painel de variáveis."""
    g = GLOSSARIO[chave]
    tit = f"**{g['termo']}**" + (f" — {g['simbolo']}" if g["simbolo"] else "")
    meta = f"<span style='color:gray'>Unidade: {g['unidade']} · {g['norma']}</span>"
    partes = [tit, meta, f"*O que é.* {g['o_que_e']}"]
    if g["no_ensaio"] and g["no_ensaio"] != "—":
        partes.append(f"*No ensaio.* {g['no_ensaio']}")
    partes.append(f"*Nas equações.* {g['nas_equacoes']}")
    return "  \n".join(partes)
