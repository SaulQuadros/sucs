# Auto‑patch SUCS (inserção do import)

Este pacote adiciona automaticamente o import do gerador de ficha (PDF) na página **SUCS**.

## Como usar
1. Extraia o ZIP **na raiz do seu projeto** (onde ficam as pastas `pages/` ou `sucs/`).
2. Garanta que `didatica/` fique no local correto (raiz do projeto).
3. Rode:
   ```bash
   python patches/patch_sucs_import.py
   ```
   - Ele detecta e edita **`pages/sucs_app.py`** (Variante A) ou **`sucs/streamlit_app.py`** (Variante B), se existirem.
   - É criado um **backup** ao lado do arquivo original.
4. Reinicie o app e, na página SUCS, confira o expander: **🧪 Gerar Ficha (PDF)**.

## Observações
- Se usar a estrutura Variante B, você também pode mover `didatica/` para dentro de `sucs/` e ajustar manualmente o import caso prefira.
- Dependências: `numpy` e `matplotlib` (já usadas pelo gerador).
