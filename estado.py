# estado.py
# Preserva o que o usuário preencheu ao navegar entre as páginas do menu superior.
#
# O Streamlit apaga o estado de um widget quando ele não é desenhado numa execução (ao trocar de
# página, ou quando um campo condicional some). Aqui cada valor ganha uma cópia de segurança em uma
# chave comum do session_state, que o Streamlit não apaga, e é restaurado quando o widget volta.
# Também guarda o último resultado de cada página e o último lote processado.
import pandas as pd
import streamlit as st

_COPIA = "__copia__"


def keep(key: str, default) -> dict:
    """Argumentos para um widget cujo valor deve sobreviver à troca de página.
    Uso: st.number_input("LL", 0.0, 300.0, **keep("sucs_ll", 0.0))  — sem value=/index=."""
    ss = st.session_state
    # Sempre restaura da cópia: além de sobreviver à troca de página, isso permite que a mesma chave seja
    # usada em páginas diferentes (ex.: #200 e limites compartilhados entre SUCS e TRB) — sem isso o
    # Streamlit trata o widget da outra página como novo e volta ao valor padrão. A cópia é atualizada
    # pelo on_change, que o Streamlit executa antes do script.
    if _COPIA + key in ss:
        ss[key] = ss[_COPIA + key]
    elif key not in ss:
        ss[key] = default
    ss[_COPIA + key] = ss[key]
    return {"key": key, "on_change": _copiar, "args": (key,)}


def _copiar(key: str) -> None:
    st.session_state[_COPIA + key] = st.session_state[key]


# ---------------------------------------------------------------------------
# Último resultado de cada página
# ---------------------------------------------------------------------------
def salvar_resultado(pagina: str, entrada: dict, saida) -> None:
    st.session_state[f"__resultado__{pagina}"] = {"entrada": dict(entrada), "saida": saida}


def ultimo_resultado(pagina: str, entrada_atual: dict):
    """Retorna (saida, desatualizado) do último resultado da página, ou None.
    desatualizado=True quando os dados do formulário mudaram depois da classificação."""
    r = st.session_state.get(f"__resultado__{pagina}")
    if r is None:
        return None
    return r["saida"], r["entrada"] != dict(entrada_atual)


def aviso_desatualizado() -> None:
    st.warning("Os dados foram alterados depois desta classificação. Clique em **Classificar** para atualizar.")


# ---------------------------------------------------------------------------
# Lote (CSV/Excel)
# ---------------------------------------------------------------------------
def ler_tabela(arquivo) -> pd.DataFrame:
    """Lê CSV (separador , ou ; detectado) ou Excel enviado pelo st.file_uploader."""
    if arquivo.name.lower().endswith(".xlsx"):
        return pd.read_excel(arquivo)
    head = arquivo.getvalue()[:4096].decode("utf-8-sig", errors="ignore")
    sep = ";" if head.count(";") > head.count(",") else ","
    arquivo.seek(0)
    return pd.read_csv(arquivo, sep=sep, encoding="utf-8-sig")


def lote(pagina: str, arquivo, processar):
    """Processa o arquivo enviado e guarda o resultado; sem arquivo (ex.: voltou de outra página),
    devolve o último lote processado. Retorna (df_resultado, nome_arquivo, reaproveitado) ou None."""
    chave = f"__lote__{pagina}"
    if arquivo is not None:
        ident = (arquivo.name, arquivo.size)
        guardado = st.session_state.get(chave)
        if guardado is None or guardado["ident"] != ident:
            df = processar(ler_tabela(arquivo))
            st.session_state[chave] = guardado = {"ident": ident, "nome": arquivo.name, "df": df}
        return guardado["df"], guardado["nome"], False
    guardado = st.session_state.get(chave)
    if guardado is None:
        return None
    return guardado["df"], guardado["nome"], True


def limpar_lote(pagina: str) -> None:
    st.session_state.pop(f"__lote__{pagina}", None)
