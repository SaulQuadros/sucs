# Patch de Título: "Plasticidade (Atterberg)" → "Limites de Atterberg"

Este utilitário substitui, de forma segura (com backup), o texto dos títulos
e labels no seu projeto para padronizar como **Limites de Atterberg**.

## Como usar
1. Extraia este ZIP na **raiz do seu projeto**.
2. Rode no terminal:
   ```bash
   python patches/replace_title.py
   ```
   - Por padrão, ele varre o diretório atual.
   - Para apontar outro caminho:
     ```bash
     python patches/replace_title.py /caminho/do/projeto
     ```
3. O script faz backup de cada arquivo alterado com a extensão `.bak`.

## O que é alterado
- Procura pela string exata: `Plasticidade (Atterberg)`
- Substitui por: `Limites de Atterberg`
- Em arquivos `.py`, `.md`, `.txt` (recursivo).

> Observação: O gerador de PDF que enviei já exibe "Limites de Atterberg"
> na ficha. Este patch é útil para alinhar **demais telas, abas, subheaders**,
> por exemplo: `st.subheader("Plasticidade (Atterberg)")`,
> `st.markdown("### Plasticidade (Atterberg)")`, títulos de gráficos etc.
