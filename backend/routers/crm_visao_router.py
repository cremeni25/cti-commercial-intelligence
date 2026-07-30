from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-visao", tags=["crm-visao"])
ETAPAS = ["OPORTUNIDADE", "ATIVIDADES", "PROPOSTA", "NEGOCIACAO", "PEDIDO", "GANHO", "PERDIDO"]


def _lista(tabela: str, ordem: str = "created_at") -> list[dict[str, Any]]:
    return supabase.table(tabela).select("*").order(ordem, desc=True).execute().data or []


def _clientes_por_id() -> dict[str, str]:
    clientes = _lista("clientes")
    resultado: dict[str, str] = {}
    for cliente in clientes:
        identificador = str(cliente.get("id") or "").strip()
        nome = str(
            cliente.get("nome")
            or cliente.get("razao_social")
            or cliente.get("nome_fantasia")
            or ""
        ).strip()
        if identificador and nome:
            resultado[identificador] = nome
    return resultado


def _nome_cliente(oportunidade: dict[str, Any], clientes: dict[str, str]) -> str:
    cliente_id = str(oportunidade.get("cliente_id") or "").strip()
    return (
        str(oportunidade.get("cliente_nome") or "").strip()
        or clientes.get(cliente_id, "")
        or cliente_id
        or "Cliente não informado"
    )


def _fator(valor: Any) -> float:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(numero if numero <= 1 else numero / 100, 1.0))


def _dentro_periodo(item: dict[str, Any], inicio: date | None, fim: date | None) -> bool:
    referencia = item.get("created_at") or item.get("updated_at") or item.get("data_fechamento_prevista")
    if not referencia:
        return True
    try:
        data_item = datetime.fromisoformat(str(referencia).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            data_item = date.fromisoformat(str(referencia)[:10])
        except ValueError:
            return True
    if inicio and data_item < inicio:
        return False
    if fim and data_item > fim:
        return False
    return True


@router.get("/oportunidades")
def oportunidades_visao(inicio: date | None = None, fim: date | None = None):
    clientes = _clientes_por_id()
    oportunidades = [
        item
        for item in _lista("cti_oportunidades")
        if str(item.get("origem") or "").strip().upper() == "CRM_APP"
        and _dentro_periodo(item, inicio, fim)
    ]
    return [
        {
            **item,
            "cliente_nome": _nome_cliente(item, clientes),
        }
        for item in oportunidades
    ]


@router.get("/pipeline")
def pipeline_visao(inicio: date | None = None, fim: date | None = None):
    clientes = _clientes_por_id()
    oportunidades = [
        item
        for item in _lista("cti_oportunidades")
        if str(item.get("origem") or "").strip().upper() == "CRM_APP"
        and _dentro_periodo(item, inicio, fim)
    ]
    ids = {item.get("id") for item in oportunidades if item.get("id")}
    movimentos = [
        item for item in _lista("cti_pipeline") if item.get("oportunidade_id") in ids
    ]
    ultimo: dict[str, dict[str, Any]] = {}
    for movimento in movimentos:
        oportunidade_id = str(movimento.get("oportunidade_id") or "")
        if oportunidade_id and oportunidade_id not in ultimo:
            ultimo[oportunidade_id] = movimento

    cards = []
    for oportunidade in oportunidades:
        oportunidade_id = str(oportunidade.get("id") or "")
        movimento = ultimo.get(oportunidade_id, {})
        etapa = str(
            movimento.get("nova_etapa")
            or movimento.get("etapa")
            or oportunidade.get("status")
            or "OPORTUNIDADE"
        ).upper()
        if etapa not in ETAPAS:
            etapa = "OPORTUNIDADE"
        valor = float(oportunidade.get("valor_estimado") or 0)
        probabilidade = _fator(oportunidade.get("probabilidade"))
        cards.append(
            {
                "id": oportunidade_id,
                "oportunidade_id": oportunidade_id,
                "titulo": oportunidade.get("titulo") or "Oportunidade sem título",
                "cliente_id": oportunidade.get("cliente_id"),
                "cliente_nome": _nome_cliente(oportunidade, clientes),
                "responsavel_id": oportunidade.get("responsavel_id"),
                "etapa": etapa,
                "valor_estimado": valor,
                "probabilidade": probabilidade,
                "valor_ponderado": round(valor * probabilidade, 2),
                "equipamento": oportunidade.get("equipamento") or oportunidade.get("linha_equipamentos"),
                "data_fechamento_prevista": oportunidade.get("data_fechamento_prevista"),
                "ultima_movimentacao": movimento.get("created_at") or movimento.get("updated_at") or oportunidade.get("updated_at") or oportunidade.get("created_at"),
            }
        )

    contagem = Counter(card["etapa"] for card in cards)
    return {
        "etapas": ETAPAS,
        "cards": cards,
        "resumo": {
            "total_oportunidades": len(cards),
            "valor_total": round(sum(card["valor_estimado"] for card in cards), 2),
            "valor_ponderado": round(sum(card["valor_ponderado"] for card in cards), 2),
            "por_etapa": {etapa: contagem.get(etapa, 0) for etapa in ETAPAS},
        },
    }
