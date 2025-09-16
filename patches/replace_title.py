# -*- coding: utf-8 -*-
"""
Substitui o título "Plasticidade (Atterberg)" por "Limites de Atterberg"
em arquivos .py, .md, .txt do projeto (recursivo).
Uso:
    python patches/replace_title.py [<raiz_do_projeto>]
Se nenhum caminho for passado, usa o diretório atual.
Cria backups com extensão .bak
"""
from __future__ import annotations
import os, sys, io

OLD = "Plasticidade (Atterberg)"
NEW = "Limites de Atterberg"
EXTS = {".py", ".md", ".txt"}

def patch_file(path: str) -> bool:
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    if OLD not in src:
        return False
    bak = path + ".bak"
    with io.open(bak, "w", encoding="utf-8") as f:
        f.write(src)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(src.replace(OLD, NEW))
    print(f"[OK] {path}  (backup: {bak})")
    return True

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    changed = 0
    for base, dirs, files in os.walk(root):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXTS:
                p = os.path.join(base, fn)
                try:
                    if patch_file(p):
                        changed += 1
                except Exception as e:
                    print(f"[ERRO] {p}: {e}")
    if changed == 0:
        print("Nada a alterar. (Nenhuma ocorrência encontrada.)")
    else:
        print(f"Concluído. Arquivos alterados: {changed}")

if __name__ == "__main__":
    main()
