# -*- coding: utf-8 -*-
"""
Auto‑patcher para habilitar o gerador de Ficha (PDF) na página SUCS.
Ele insere:
    import didatica.enable_in_sucs
no arquivo correto, se existir (Variante A ou B).

Uso:
    python patches/patch_sucs_import.py
"""
from __future__ import annotations
import os, io, re, sys, time, datetime

IMPORT_LINE = "import didatica.enable_in_sucs  # ativa o gerador de ficha (PDF)"

CANDIDATES = [
    os.path.join("pages", "sucs_app.py"),       # Variante A
    os.path.join("sucs", "streamlit_app.py"),   # Variante B
]

def insert_import(path: str) -> bool:
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if IMPORT_LINE in src or "import didatica.enable_in_sucs" in src:
        print(f"[=] Já possui o import: {path}")
        return False
    # inserir após o bloco inicial de imports
    lines = src.splitlines(True)
    insert_idx = 0
    for i, ln in enumerate(lines[:200]):  # procurar nos primeiros 200 linhas
        s = ln.strip()
        if s.startswith("import ") or s.startswith("from "):
            insert_idx = i + 1
            continue
        # se já passou pelos imports e encontra uma linha "normal"
        if i > 0:
            break
    lines.insert(insert_idx, IMPORT_LINE + "\n")
    backup = f"{path}.bak_{int(time.time())}"
    with io.open(backup, "w", encoding="utf-8") as f:
        f.write(src)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print(f"[+] Import inserido em: {path} (backup: {backup})")
    return True

def main():
    root = os.getcwd()
    print(f"Raiz do projeto: {root}")
    patched_any = False
    for cand in CANDIDATES:
        if os.path.exists(cand):
            try:
                changed = insert_import(cand)
                patched_any = patched_any or changed
            except Exception as e:
                print(f"[!] Falha ao patchar {cand}: {e}")
        else:
            print(f"[-] Não encontrado: {cand}")
    if not patched_any:
        print("Nada alterado. Se o seu arquivo SUCS tem outro nome/caminho, edite este patch e rode novamente.")
    else:
        print("Concluído. Reinicie/Rerun o app e verifique a barra lateral da página SUCS.")

if __name__ == "__main__":
    main()
