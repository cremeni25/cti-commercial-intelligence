from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers import strategic_layers_router as estrategia
from routers.crm_scope_estrategia_router import FECHADOS
from routers.crm_scope_mapa_equipe_router import (
    _deduplicar,
    _historico_carteira,
    _pode_gerir,
    _resolver_alvo,
    _usuario_regional,
    _crm_carteira,
)
from services.commercial_client_scope import filtrar_anfir_por_responsavel_comercial
from services.crm_live_projection import carregar_oportunidades_enriquecidas
from services.historical_commercial_source import carregar_historico_comercial
from services.product_line_classifier import classificar_linha

router = APIRouter(prefix="/crm-seguro/mapa-equipe", tags=["crm-seguro-mapa-insights"])


def _valor(item: dict[str, Any]) -> float:
    try:
        return float(item.get("valor_estimado") or 0)
    except (TypeError, ValueError):
        return 0.0


def _quantidade(item: dict[str, Any]) -> int:
    try:
        return int(item.get("quantidade") or 0)
    except (TypeError, ValueError):
        return 0


def _linha_nome(item: dict[str, Any]) -> str:
    codigo = classificar_linha(item)
    return {"TR": "Trailer", "DT": "Diesel Truck", "DD": "Direct Drive"}.get(codigo, "Não classificado")


def _historico_do_escopo(usuario: UsuarioAutenticado, alvo: UsuarioAutenticado | None, equipe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = list(carregar_historico_comercial())
    if alvo is not None:
        return _historico_carteira(alvo, base)

    todos: list[dict[str, Any]] = []
    for registro in equipe:
        todos.extend(_historico_carteira(_usuario_regional(registro), base))
    return _deduplicar(todos)


def _evolucao_linhas(historico: list[dict[str, Any]]) -> list[dict[str, Any]]:
    por_ano: dict[int, Counter[str]] = defaultdict(Counter)
    for item in historico:
        ano = item.get("ano")
        if ano not in (2023, 2024, 2025, 2026):
            continue
        por_ano[int(ano)][_linha_nome(item)] += _quantidade(item)

    return [
        {
            "ano": ano,
            "trailer": int(por_ano[ano].get("Trailer", 0)),
            "diesel_truck": int(por_ano[ano].get("Diesel Truck", 0)),
            "direct_drive": int(por_ano[ano].get("Direct Drive", 0)),
            "nao_classificado": int(por_ano[ano].get("Não classificado", 0)),
        }
        for ano in (2023, 2024, 2025, 2026)
    ]


def _perdas(historico: list[dict[str, Any]]) -> dict[str, Any]:
    com_motivo = [item for item in historico if str(item.get("motivo_perda") or "").strip()]
    motivos = Counter(str(item.get("motivo_perda") or "").strip() for item in com_motivo)
    linhas = Counter(_linha_nome(item) for item in com_motivo)
    anos = Counter(str(item.get("ano") or "Sem ano") for item in com_motivo)
    return {
        "total_registros_com_motivo": len(com_motivo),
        "motivos": [{"nome": nome, "quantidade": qtd} for nome, qtd in motivos.most_common(10)],
        "por_linha": [{"nome": nome, "quantidade": qtd} for nome, qtd in linhas.most_common()],
        "por_ano": [{"nome": nome, "quantidade": qtd} for nome, qtd in sorted(anos.items())],
    }


def _regioes(usuario: UsuarioAutenticado, alvo: UsuarioAutenticado | None, equipe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mercado_total, _, _ = estrategia._anfir(
        "viena-sp",
        "PERSONALIZADO",
        None,
        None,
        date(2026, 1, 1),
        date(2026, 12, 31),
    )
    crm_base = carregar_oportunidades_enriquecidas()

    registros = equipe if alvo is None else [item for item in equipe if str(item.get("id")) == str(alvo.id)]
    saida: list[dict[str, Any]] = []
    for registro in registros:
        responsavel = _usuario_regional(registro)
        anf = filtrar_anfir_por_responsavel_comercial(
            list(mercado_total),
            str(responsavel.id),
            responsavel.nome,
        )
        crm = _crm_carteira(responsavel, crm_base)
        ativos = [item for item in crm if str(item.get("status") or "").upper() not in FECHADOS]
        saida.append({
            "id": responsavel.id,
            "nome": responsavel.nome,
            "codigo_regional": registro.get("codigo_regional"),
            "ddds": registro.get("ddds") or [],
            "mercado_2026": len(anf),
            "clientes_mercado": len({str(item.get("cliente") or item.get("empresa") or item.get("transportadora") or "").strip().upper() for item in anf if str(item.get("cliente") or item.get("empresa") or item.get("transportadora") or "").strip()}),
            "crm_ativos": len(ativos),
            "pipeline_ativo": round(sum(_valor(item) for item in ativos), 2),
        })
    return sorted(saida, key=lambda item: (-int(item["mercado_2026"]), str(item["nome"])))


@router.get("/insights")
def insights_mapa(
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    alvo, equipe = _resolver_alvo(usuario, responsavel_id)
    historico = _historico_do_escopo(usuario, alvo, equipe)
    consolidado = _pode_gerir(usuario)

    return {
        "escopo": {
            "consolidado": consolidado,
            "modo": "TODA_EQUIPE" if alvo is None else "RESPONSAVEL",
            "responsavel_id": None if alvo is None else alvo.id,
            "responsavel_nome": "Toda a equipe comercial" if alvo is None else alvo.nome,
            "regra": "MASTER_GESTAO_PODE_CONSOLIDAR; DEMAIS_USUARIOS_SEMPRE_RECEBEM_APENAS_O_PROPRIO_LOGIN",
        },
        "regioes": _regioes(usuario, alvo, equipe),
        "evolucao_linhas": _evolucao_linhas(historico),
        "perdas": _perdas(historico),
    }
