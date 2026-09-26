# formato.py
# Formatação numérica no padrão brasileiro (vírgula decimal), usada nos textos e relatórios.


def fmt(x, nd=1) -> str:
    """Número com vírgula decimal: fmt(7.345, 2) → '7,35'."""
    return f"{x:.{nd}f}".replace(".", ",")
