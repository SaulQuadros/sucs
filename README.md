# SoilClass — Classificação de solos SUCS, TRB e MCT (DNIT)

App Streamlit para classificar solos e geomateriais para pavimentação, com as regras do
**Manual de Pavimentação DNIT (IPR-719/2006, versão corrigida com a Errata 1)** e das normas DNIT vigentes
(lista IPR de 24/09/2026).

| Página | Classificação | Referências |
|---|---|---|
| `paginas/sucs.py` | SUCS | Manual IPR-719: Tabela 5, Figura 17, fluxograma de identificação, Tabelas 12 e 13 |
| `paginas/trb.py` | TRB (HRB/AASHTO) + Índice de Grupo | Manual IPR-719: Tabela 4, Tabelas 11 e 14 |
| `paginas/mct.py` | MCT (solos finos tropicais) | DNIT 259/2023-CLA (Figura A1, Anexos B e C); ensaios DNIT 258/2023-ME; Tabela 15 do Manual |

Ensaios de caracterização: granulometria **DNIT 459/2025-ME** (substitui DNER-ME 051/94 e 080/94),
LL **DNER-ME 122/94**, LP **DNER-ME 082/94**.

## ▶️ Executar localmente

```bash
pip install -r requirements.txt
streamlit run sucs_app.py
```

Testes automatizados (regras, planilhas-modelo e páginas):

```bash
pip install pytest
pytest
```

## ☁️ Streamlit Community Cloud

- **Main file path:** `sucs_app.py` — roteador com o menu da barra superior (`st.navigation`); as páginas ficam em `paginas/`.
- Endereços: `/` (SUCS), `/trb_app` (TRB), `/mct_app` (MCT).
- Configuração em `.streamlit/config.toml`. Não precisa de secrets.
- `mct_app.py` na raiz apenas abre o app completo (compatibilidade).

## 🧭 Menu

O menu fica na barra superior. Cada chave de `MENUS` em `sucs_app.py` é um menu suspenso
(hoje: **Classificação de Solos** → SUCS, TRB, MCT). Novos módulos entram como novas chaves.
Para usar o menu lateral em vez da barra superior, troque `position="top"` por `position="sidebar"`.

A barra superior define o conteúdo da página; a barra lateral traz informações complementares (projeto).
O que o usuário preenche é preservado ao trocar de página (`estado.py`): todo widget de entrada deve usar
`**keep("chave_unica", valor_padrão)` em vez de `value=`/`index=`. O último resultado de cada página e o
último lote processado também são mantidos; se os dados mudarem depois da classificação, o app avisa.

## ⚙️ Regras implementadas (resumo)

**SUCS**
- Mais de 50% retido na #200 → grossa; 50% ou mais passando → fina.
- G quando 50% ou mais da fração graúda fica retida na #4; senão S.
- Finos < 5%: W/P por Cu e Cc (pedregulho Cu ≥ 4; areia Cu ≥ 6; 1 ≤ Cc ≤ 3). Cu/Cc podem vir de D10, D30, D60.
- Finos 5–12%: símbolo duplo (ex.: SW-SM, GP-GC).
- Finos > 12%: GM/SM abaixo da linha A, GC/SC acima, GM-GC/SM-SC na zona hachurada.
- Finos: linha A IP = 0,73(LL − 20); L se LL ≤ 50; zona hachurada (4 ≤ IP ≤ 7 acima da linha A) → ML-CL;
  orgânicos abaixo da linha A → OL/OH; turfa → PT.

**TRB**
- Eliminação da esquerda para a direita no quadro; A-1 sem critério de LL; A-3 exige NP.
- Limites inteiros com valores decimais: LL > 40 = "41 mín."; IP > 10 = "11 mín."; #40 > 50 = "51 mín.".
- IG = 0,2a + 0,005ac + 0,01bd, com aviso quando excede o máximo do quadro para o grupo.

**MCT**
- Pi' (item 3.8): AF no Mini-MCV 10 ≥ 48 mm → Pi a Mini-MCV 10; AF < 48 mm → Pi a Mini-MCV 15.
- e' = ∛(Pi'/100 + 20/d'), com d' da curva de 10 golpes (série simplificada) ou 12 (Parsons).
- Ábaco da Figura A1 pelos vértices cotados: (0,27; 2,2), (0,45; 1,75), (0,59; 1,4), (0,70; 1,15), (1,7; 1,15) e c' = 1,5.
- Critério de desempate perto da fronteira L|N (item 5.1 c).

## 📁 Estrutura

```
sucs_app.py            ponto de entrada: menu superior (MENUS) e barra lateral do projeto
projeto.py             identificação do projeto, compartilhada entre as páginas
estado.py              preserva campos, resultados e lotes ao navegar pelo menu
paginas/sucs.py        página SUCS
paginas/trb.py         página TRB
paginas/mct.py         página MCT
sucs_core.py           regras SUCS
trb_core.py, trb_defs.py   regras e tabelas TRB
mct_core.py            regras e ábaco MCT
xlsx_utils.py          geração de planilhas Excel
didatica/              ficha de exercício (PDF) e modelo de planilha MCT
tests/                 testes automatizados (pytest)
samples.csv            exemplo de lote SUCS (um solo por grupo)
```

## 📜 Licença
MIT — veja `LICENSE`.
