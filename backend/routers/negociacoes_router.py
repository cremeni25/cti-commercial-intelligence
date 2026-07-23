from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase

router = APIRouter()

ETAPAS_PIPELINE = [
    "OPORTUNIDADE",
    "ATIVIDADES",
    "PROPOSTA",
    "NEGOCIACAO",
    "PEDIDO",
    "GANHO",
    "PERDIDO",
]


class Negociacao(BaseModel):
    cliente: str
    cidade: str | None = None
    estado: str | None = None
    produto: str | None = None
    valor: float | None = None
    status: str | None = None


def _lista(tabela: str, ordem: str = "created_at") -> list[dict[str, Any]]:
    try:
        return supabase.table(tabela).select("*").order(ordem, desc=True).execute().data or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao consultar {tabela}: {exc}") from exc


def _fator_probabilidade(valor: Any) -> float:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0
    if numero <= 0:
        return 0
    return min(numero if numero <= 1 else numero / 100, 1)


@router.post("/negociacoes")
def criar_negociacao(negociacao: Negociacao):
    try:
        return supabase.table("negociacoes").insert(negociacao.model_dump()).execute().data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/negociacoes")
def listar_negociacoes():
    return _lista("negociacoes")


@router.get("/crm/pipeline/quadro")
def quadro_pipeline():
    """Retorna uma fotografia atual do pipeline, sem duplicar movimentações históricas."""
    oportunidades = _lista("cti_oportunidades")
    movimentacoes = _lista("cti_pipeline")

    ultima_movimentacao: dict[str, dict[str, Any]] = {}
    for movimento in movimentacoes:
        oportunidade_id = movimento.get("oportunidade_id")
        if oportunidade_id and oportunidade_id not in ultima_movimentacao:
            ultima_movimentacao[oportunidade_id] = movimento

    cards = []
    for oportunidade in oportunidades:
        oportunidade_id = oportunidade.get("id")
        movimento = ultima_movimentacao.get(oportunidade_id, {})
        etapa = (
            movimento.get("nova_etapa")
            or movimento.get("etapa")
            or oportunidade.get("status")
            or "OPORTUNIDADE"
        ).upper()
        if etapa not in ETAPAS_PIPELINE:
            etapa = "OPORTUNIDADE"

        valor = float(oportunidade.get("valor_estimado") or 0)
        probabilidade = _fator_probabilidade(oportunidade.get("probabilidade"))
        cards.append({
            "id": oportunidade_id,
            "oportunidade_id": oportunidade_id,
            "titulo": oportunidade.get("titulo") or "Oportunidade sem título",
            "cliente_id": oportunidade.get("cliente_id"),
            "responsavel_id": oportunidade.get("responsavel_id"),
            "etapa": etapa,
            "valor_estimado": valor,
            "probabilidade": probabilidade,
            "valor_ponderado": round(valor * probabilidade, 2),
            "equipamento": oportunidade.get("equipamento") or oportunidade.get("linha_equipamentos"),
            "implementadora": oportunidade.get("implementadora"),
            "municipio": oportunidade.get("municipio"),
            "estado": oportunidade.get("estado"),
            "data_fechamento_prevista": oportunidade.get("data_fechamento_prevista"),
            "ultima_movimentacao": movimento.get("created_at") or movimento.get("updated_at") or oportunidade.get("updated_at") or oportunidade.get("created_at"),
        })

    contagem = Counter(card["etapa"] for card in cards)
    valor_total = sum(card["valor_estimado"] for card in cards)
    valor_ponderado = sum(card["valor_ponderado"] for card in cards)

    return {
        "etapas": ETAPAS_PIPELINE,
        "cards": cards,
        "resumo": {
            "total_oportunidades": len(cards),
            "valor_total": round(valor_total, 2),
            "valor_ponderado": round(valor_ponderado, 2),
            "por_etapa": {etapa: contagem.get(etapa, 0) for etapa in ETAPAS_PIPELINE},
        },
    }
