from collections import Counter
from datetime import date, datetime, timezone
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


def _data_iso(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return None


def _situacao_atividade(atividade: dict[str, Any], hoje: date | None = None) -> str:
    status = str(atividade.get("status") or "PENDENTE").upper()
    if status in {"CONCLUIDA", "CONCLUÍDA", "CANCELADA"}:
        return "CONCLUIDA" if status != "CANCELADA" else "CANCELADA"
    referencia = hoje or datetime.now(timezone.utc).date()
    data_atividade = _data_iso(atividade.get("data"))
    if not data_atividade:
        return "SEM_DATA"
    if data_atividade < referencia:
        return "ATRASADA"
    if data_atividade == referencia:
        return "HOJE"
    return "FUTURA"


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


@router.get("/crm/agenda")
def agenda_comercial():
    """Consolida atividades existentes em uma agenda operacional, sem duplicar dados."""
    atividades = _lista("cti_atividades")
    oportunidades = {item.get("id"): item for item in _lista("cti_oportunidades")}

    itens = []
    for atividade in atividades:
        oportunidade = oportunidades.get(atividade.get("oportunidade_id"), {})
        itens.append({
            **atividade,
            "situacao": _situacao_atividade(atividade),
            "oportunidade_titulo": oportunidade.get("titulo"),
            "cliente_id": atividade.get("cliente_id") or oportunidade.get("cliente_id"),
            "responsavel_id": atividade.get("usuario_id") or oportunidade.get("responsavel_id"),
        })

    ordem_situacao = {"ATRASADA": 0, "HOJE": 1, "FUTURA": 2, "SEM_DATA": 3, "CONCLUIDA": 4, "CANCELADA": 5}
    itens.sort(key=lambda item: (ordem_situacao.get(item["situacao"], 9), item.get("data") or "9999-12-31", item.get("horario") or "23:59"))
    contagem = Counter(item["situacao"] for item in itens)

    return {
        "itens": itens,
        "resumo": {
            "total": len(itens),
            "atrasadas": contagem.get("ATRASADA", 0),
            "hoje": contagem.get("HOJE", 0),
            "futuras": contagem.get("FUTURA", 0),
            "sem_data": contagem.get("SEM_DATA", 0),
            "concluidas": contagem.get("CONCLUIDA", 0),
        },
    }


@router.get("/crm/timeline/{oportunidade_id}")
def timeline_oportunidade(oportunidade_id: str):
    """Monta a linha do tempo comercial a partir das tabelas operacionais já existentes."""
    oportunidade = supabase.table("cti_oportunidades").select("*").eq("id", oportunidade_id).execute().data or []
    if not oportunidade:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")

    fontes = [
        ("HISTORICO", "cti_oportunidade_historico"),
        ("ATIVIDADE", "cti_atividades"),
        ("PIPELINE", "cti_pipeline"),
        ("PROPOSTA", "cti_propostas"),
        ("PEDIDO", "cti_pedidos"),
        ("PERDA", "cti_perdas"),
    ]
    eventos: list[dict[str, Any]] = []
    for tipo, tabela in fontes:
        registros = supabase.table(tabela).select("*").eq("oportunidade_id", oportunidade_id).execute().data or []
        for registro in registros:
            eventos.append({
                "tipo": tipo,
                "data_hora": registro.get("updated_at") or registro.get("created_at") or registro.get("data"),
                "titulo": registro.get("titulo") or registro.get("descricao") or registro.get("numero") or tipo.title(),
                "status": registro.get("status") or registro.get("nova_etapa") or registro.get("etapa"),
                "responsavel_id": registro.get("usuario_id") or registro.get("responsavel_id"),
                "registro": registro,
            })

    eventos.sort(key=lambda item: item.get("data_hora") or "", reverse=True)
    return {"oportunidade": oportunidade[0], "eventos": eventos}
