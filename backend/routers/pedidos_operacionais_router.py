from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase
from routers.propostas_pedidos_router import ConverterPedidoRequest, converter_em_pedido

router = APIRouter(prefix="/crm-documentos", tags=["CRM Pedidos Operacionais"])


class ConverterPedidoOperacionalRequest(BaseModel):
    destinatarios: list[str] = Field(min_length=1)
    observacoes_envio: str | None = None
    responsavel_id: str | None = None
    data_pedido: str | None = None


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail=detalhe)
    return dados[0]


def _opcional(tabela: str, registro_id: str | None) -> dict[str, Any] | None:
    if not registro_id:
        return None
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    return dados[0] if dados else None


def _emails_validos(valores: list[str]) -> list[str]:
    emails: list[str] = []
    for valor in valores:
        email = valor.strip().lower()
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            raise HTTPException(status_code=422, detail=f"Destinatário inválido: {valor}")
        if email not in emails:
            emails.append(email)
    if not emails:
        raise HTTPException(status_code=422, detail="Informe ao menos um destinatário do pedido.")
    return emails


@router.post("/propostas/{proposta_id}/converter-pedido-operacional")
def converter_pedido_operacional(proposta_id: str, dados: ConverterPedidoOperacionalRequest):
    destinatarios = _emails_validos(dados.destinatarios)
    pedidos = converter_em_pedido(
        proposta_id,
        ConverterPedidoRequest(
            responsavel_id=dados.responsavel_id,
            data_pedido=dados.data_pedido,
            origem_comercial="CRM_APP",
        ),
    )
    pedido = pedidos[0] if isinstance(pedidos, list) and pedidos else pedidos
    if not isinstance(pedido, dict) or not pedido.get("id"):
        raise HTTPException(status_code=500, detail="Pedido criado sem identificação válida.")

    dossie = list(pedido.get("dossie_documentos") or [])
    dossie.append(
        {
            "tipo": "DESTINATARIOS_PEDIDO",
            "destinatarios": destinatarios,
            "observacoes_envio": dados.observacoes_envio,
            "status_envio": "PENDENTE",
            "registrado_em": _agora(),
        }
    )
    atualizado = (
        supabase.table("cti_pedidos")
        .update({"dossie_documentos": dossie, "updated_at": _agora()})
        .eq("id", pedido["id"])
        .execute()
        .data
        or []
    )
    return atualizado[0] if atualizado else {**pedido, "dossie_documentos": dossie}


@router.get("/pedidos/{pedido_id}")
def consultar_pedido_operacional(pedido_id: str):
    pedido = _primeiro("cti_pedidos", pedido_id, "Pedido não encontrado")
    proposta = _opcional("cti_propostas", str(pedido.get("proposta_id") or ""))
    item = _opcional("cti_oportunidade_itens", str(pedido.get("item_oportunidade_id") or ""))
    oportunidade_id = (proposta or {}).get("oportunidade_id") or pedido.get("oportunidade_id")
    oportunidade = _opcional("cti_oportunidades", str(oportunidade_id or ""))
    cliente_id = pedido.get("cliente_id") or (proposta or {}).get("cliente_id") or (oportunidade or {}).get("cliente_id")
    cliente = _opcional("cti_clientes", str(cliente_id or ""))

    snapshot = (proposta or {}).get("snapshot_dados") or {}
    cliente_snapshot = snapshot.get("cliente") if isinstance(snapshot, dict) else None
    oportunidade_snapshot = snapshot.get("oportunidade") if isinstance(snapshot, dict) else None
    if not cliente and isinstance(cliente_snapshot, dict):
        cliente = cliente_snapshot
    if not oportunidade and isinstance(oportunidade_snapshot, dict):
        oportunidade = oportunidade_snapshot

    envio = next(
        (registro for registro in reversed(list(pedido.get("dossie_documentos") or [])) if registro.get("tipo") == "DESTINATARIOS_PEDIDO"),
        None,
    )
    return {
        "pedido": pedido,
        "proposta": proposta,
        "item": item,
        "oportunidade": oportunidade,
        "cliente": cliente,
        "envio": envio,
        "integridade": {
            "cliente_cadastrado": bool(cliente_id and _opcional("cti_clientes", str(cliente_id))),
            "cliente_recuperado_snapshot": bool(cliente and not _opcional("cti_clientes", str(cliente_id or ""))),
        },
    }
