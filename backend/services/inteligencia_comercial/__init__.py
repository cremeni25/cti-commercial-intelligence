"""Agente de Inteligência Comercial do CTI.

Organiza a leitura comercial em uma devolutiva única e priorizada
(``montar_briefing``) e oferece pontos de extensão para que novos módulos
contribuam com sinais (``registrar_provedor``). Ver
``docs/AGENTE_INTELIGENCIA_COMERCIAL.md``.
"""
from .briefing import VERSAO_BRIEFING, montar_briefing
from .servico import filtrar_escopo, gerar_briefing
from .sinais import ContextoInteligencia, Sinal, provedores_registrados, registrar_provedor, remover_provedor

__all__ = [
    "VERSAO_BRIEFING",
    "ContextoInteligencia",
    "Sinal",
    "filtrar_escopo",
    "gerar_briefing",
    "montar_briefing",
    "provedores_registrados",
    "registrar_provedor",
    "remover_provedor",
]
