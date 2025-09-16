# Gerador de Ficha (PDF) para SUCS – Integração rápida

Este pacote habilita o **🧪 Gerar Ficha (PDF)** também na página **SUCS** do seu App.
Ele funciona em **duas variantes comuns** de projeto. Escolha a que corresponde ao seu repositório:

## Variante A — `pages/sucs_app.py`
1. Garanta que a pasta `didatica/` esteja na **raiz** do projeto (mesmo nível de `pages/`).
2. No topo de `pages/sucs_app.py`, adicione **uma linha**:
   ```python
   import didatica.enable_in_sucs  # ativa o gerador de ficha (PDF)
   ```
3. Salve e rode o App → na barra lateral da página SUCS surgirá o expander:
   **🧪 Gerar Ficha (PDF)**

## Variante B — `sucs/streamlit_app.py`
1. Garanta que a pasta `didatica/` esteja na **raiz do pacote `sucs/`** (isto é, crie `sucs/didatica/` e mova esta pasta para dentro de `sucs/` se for o seu caso).
2. No topo de `sucs/streamlit_app.py`, adicione **uma linha**:
   ```python
   import didatica.enable_in_sucs  # ativa o gerador de ficha (PDF)
   ```
3. Salve e rode o App → na barra lateral da página SUCS surgirá o expander:
   **🧪 Gerar Ficha (PDF)**

> Dica: Se aparecer `ModuleNotFoundError: didatica`, crie um arquivo **vazio** `didatica/__init__.py` na mesma pasta do `enable_in_sucs.py`.

### Dependências
- `numpy>=1.23`
- `matplotlib>=3.5`

### Sobre o PDF
- Classe SUCS é escolhida **uniformemente** (probabilidade igual).
- **Sem PI (IP)**: o PDF mostra apenas **LL** e **LP** (ou **NP**).
- Traz **tabela de peneiramento** e **curva granulométrica** em escala semilog.
- Gera **uma ficha por vez** — clique novamente para uma nova ficha.

