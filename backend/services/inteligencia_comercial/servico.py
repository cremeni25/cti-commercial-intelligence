"""Carga das fontes autorizadas para o briefing.

Isola o acesso ao banco da regra (briefing.py) para que a regra permaneça
pura e testável. Toda leitura reaproveita as funções canônicas já usadas
pelas telas do CRM — o agente enxerga exatamente o que o usuário enxerga.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .briefing import montar_briefing
from .sinais import texto


def _carregar_oportunidades() -> list[dict[str, Any]]:
    from routers.crm_core_extension import nucleo_comercial

    return nucleo_comercial()


def _carregar_atividades() -> list[dict[str, Any]]:
    from routers.crm_atividades_governanca_router import listar_atividades_operacionais

    return listar_atividades_operacionais() or []


def filtrar_escopo(
    oportunidades: list[dict[str, Any]],
    atividades: list[dict[str, Any]],
    responsavel_id: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sem responsável: visão consolidada. Com responsável: somente a carteira dele."""
    if not responsavel_id:
        return oportunidades, atividades
    alvo = str(responsavel_id)
    proprias = [o for o in oportunidades if texto(o.get("responsavel_id")) == alvo]
    ids = {texto(o.get("oportunidade_id")) for o in proprias}
    atividades_proprias = [
        a for a in atividades
        if texto(a.get("usuario_id") or a.get("responsavel_id")) == alvo or texto(a.get("oportunidade_id")) in ids
    ]
    return proprias, atividades_proprias


def gerar_briefing(
    *,
    usuario_id: str,
    consolidado: bool,
    responsavel_id: str | None = None,
    hoje: date | None = None,
    limite_prioridades: int = 8,
) -> dict[str, Any]:
    oportunidades = _carregar_oportunidades()
    limitacoes_carga: list[str] = []
    try:
        atividades = _carregar_atividades()
    except Exception:
        atividades = []
        limitacoes_carga.append("Atividades indisponíveis nesta leitura; sinais de agenda foram omitidos.")

    filtro = responsavel_id if consolidado else usuario_id
    oportunidades, atividades = filtrar_escopo(oportunidades, atividades, filtro or None)
    escopo = {
        "tipo": "consolidado" if consolidado and not responsavel_id else "individual",
        "responsavel_id": filtro or None,
    }
    briefing = montar_briefing(oportunidades, atividades, hoje=hoje, escopo=escopo, limite_prioridades=limite_prioridades)
    briefing["limitacoes"] = limitacoes_carga + briefing["limitacoes"]
    return briefing
