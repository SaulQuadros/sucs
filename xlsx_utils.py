# xlsx_utils.py
# Geração de planilhas Excel em memória (XlsxWriter preferido; openpyxl como alternativa).
import io


def resolve_xlsx_engine():
    """Retorna um engine disponível para pandas.ExcelWriter ou None."""
    for mod, name in (("xlsxwriter", "xlsxwriter"), ("openpyxl", "openpyxl")):
        try:
            __import__(mod)
            return name
        except ImportError:
            continue
    return None


def to_xlsx_bytes(df, sheet_name="dados") -> bytes:
    import pandas as pd
    eng = resolve_xlsx_engine()
    if eng is None:
        raise RuntimeError("Nenhum engine Excel disponível. Instale XlsxWriter ou openpyxl.")
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine=eng) as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return bio.getvalue()
