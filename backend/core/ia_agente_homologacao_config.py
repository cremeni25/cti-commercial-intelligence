from __future__ import annotations

import os
from dataclasses import dataclass


def _booleano(nome: str, padrao: bool = False) -> bool:
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "yes", "on", "sim"}


@dataclass(frozen=True)
class IAAgenteHomologacaoConfig:
    habilitada: bool
    somente_leitura: bool
    ambiente: str
    modelo: str
    modelo_web: str

    @property
    def pronta_para_homologacao(self) -> bool:
        return self.habilitada and self.somente_leitura and self.ambiente != "production"


def carregar_ia_agente_homologacao_config() -> IAAgenteHomologacaoConfig:
    return IAAgenteHomologacaoConfig(
        habilitada=_booleano("CTI_IA_AGENTE_HOMOLOGACAO", False),
        somente_leitura=_booleano("CTI_IA_AGENTE_SOMENTE_LEITURA", True),
        ambiente=os.getenv("CTI_AMBIENTE", "production").strip().lower(),
        modelo=os.getenv("OPENAI_AGENT_MODEL", "gpt-4.1-mini").strip(),
        modelo_web=os.getenv("OPENAI_AGENT_WEB_MODEL", "gpt-4.1-mini").strip(),
    )
