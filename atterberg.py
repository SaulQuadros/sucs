# atterberg.py
# Regras dos limites de Atterberg comuns ao SUCS e ao TRB.
# DNER-ME 082/94 (limite de plasticidade), observações: o IP é anotado como NP quando o LL ou o LP não puderem
# ser determinados (item 2; em solo extremamente arenoso, ambos como NP, item 3) e quando o LP for igual ou
# maior que o LL (item 4).
from dataclasses import dataclass
from typing import Optional

NORMA_LP = "DNER-ME 082/94"


@dataclass
class Limites:
    np_: bool                       # não plástico (informado ou por LP ≥ LL)
    ip: Optional[float]             # IP (0 se NP); None se incompleto
    nota: Optional[str] = None      # explicação quando o NP decorre de LP ≥ LL
    erro: Optional[str] = None      # combinação que não é resultado de ensaio

    @property
    def completo(self) -> bool:
        return self.erro is None and self.ip is not None


def avaliar(ll: Optional[float], lp: Optional[float], np_informado: bool) -> Limites:
    if np_informado:
        return Limites(True, 0.0)
    if ll is None or lp is None:
        return Limites(False, None)
    if ll <= 0 and lp <= 0:
        return Limites(False, None, erro="Informe LL e LP, ou marque NP se não puderem ser determinados "
                                         f"({NORMA_LP}).")
    if ll <= 0:
        return Limites(False, None, erro="LL = 0 não é resultado de ensaio: se o LL não pôde ser determinado, "
                                         f"marque NP ({NORMA_LP}).")
    if lp <= 0:
        return Limites(False, None, erro="LP = 0 não é resultado de ensaio: se o LP não pôde ser determinado, "
                                         f"marque NP ({NORMA_LP}).")
    if lp >= ll:
        return Limites(True, 0.0, nota=f"LP ≥ LL: o IP é anotado como NP ({NORMA_LP}, item 4).")
    return Limites(False, ll - lp)
