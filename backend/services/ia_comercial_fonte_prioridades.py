"""Expõe os sinais do Agente de Inteligência à IA Comercial conversacional.

A IA usa uma arquitetura universal (catálogo + consulta) em vez de uma
ferramenta por entidade. Por isso os sinais entram como mais uma *fonte* do
universo autorizado — ``prioridades_comerciais`` — e podem ser filtrados,
agrupados e ranqueados como qualquer outra. Assim, perguntas como "o que eu
faço primeiro hoje?" ou "quais negócios estão parados?" usam exatamente a
mesma leitura que a Central de Inteligência mostra na tela.

Escopo: ADMIN_MASTER enxerga a equipe; demais perfis, somente a própria
carteira — a mesma regra conservadora já aplicada pela IA.
Uma falha aqui nunca derruba a IA: a fonte fica vazia e o motivo é
registrado nos metadados.
"""
from __future__ import annotations

import time
from typing import Any

from services import ia_comercial_universo as universo

FONTE = "prioridades_comerciais"
DESCRICAO = (
    "Sinais priorizados pelo Agente de Inteligência Comercial sobre a carteira autorizada: follow-ups atrasados, "
    "compromissos de hoje, propostas sem retorno, negócios parados, previsões vencidas, negócios sem próximo passo, "
    "negócios prontos para fechar e pedidos sem movimento. Cada registro traz codigo, categoria, severidade, titulo, "
    "explicacao, acao_recomendada, cliente_nome, valor, dias e pontuacao (maior = mais urgente). Use para responder "
    "o que priorizar, onde há risco e quais ações tomar; é leitura derivada do CRM, não um registro novo."
)
_TTL_SEGUNDOS = 60.0
_CACHE: dict[tuple[str, str], tuple[float, list[dict[str, Any]]]] = {}
_ORIGINAL_CARREGAR_FONTES = None
_ATIVADO = False


def _sinais(usuario_id: str, tipo_usuario: str) -> list[dict[str, Any]]:
    from services.inteligencia_comercial import gerar_briefing

    chave = (str(usuario_id), str(tipo_usuario or "").upper())
    agora = time.monotonic()
    em_cache = _CACHE.get(chave)
    if em_cache and agora - em_cache[0] < _TTL_SEGUNDOS:
        return em_cache[1]
    briefing = gerar_briefing(
        usuario_id=str(usuario_id),
        consolidado=chave[1] == "ADMIN_MASTER",
        limite_prioridades=500,
    )
    registros = [
        {k: v for k, v in item.items() if k not in {"rota", "rota_app"}}
        for item in briefing.get("prioridades", [])
    ]
    _CACHE[chave] = (agora, registros)
    return registros


def _carregar_fontes_com_prioridades(usuario_id: str, tipo_usuario: str):
    fontes, metadados = _ORIGINAL_CARREGAR_FONTES(usuario_id, tipo_usuario)
    try:
        registros = _sinais(usuario_id, tipo_usuario)
        erro = None
    except Exception as exc:  # leitura derivada: nunca bloqueia a IA
        registros, erro = [], type(exc).__name__
    fontes[FONTE] = registros
    metadados[FONTE] = {
        "total_registros": len(registros),
        "modo": "somente_leitura",
        "origem": "AGENTE_INTELIGENCIA_COMERCIAL",
        "erro": erro,
    }
    return fontes, metadados


def ativar_fonte_prioridades() -> None:
    global _ATIVADO, _ORIGINAL_CARREGAR_FONTES
    if _ATIVADO:
        return
    _ORIGINAL_CARREGAR_FONTES = universo._carregar_fontes
    universo.FONTES_PUBLICAS[FONTE] = DESCRICAO
    universo._carregar_fontes = _carregar_fontes_com_prioridades
    _ATIVADO = True


ativar_fonte_prioridades()
