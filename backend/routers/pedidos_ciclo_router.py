from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase

router = APIRouter(prefix="/carrier-operacional", tags=["Ciclo Operacional do Pedido"])

ETAPAS = ["PEDIDO", "CARRIER", "FATURADO", "ENTREGUE", "INSTALADO", "ENCERRADO"]


class AtualizarCicloRequest(BaseModel):
    etapa: str
    numero_nf: str | None = None
    observacao: str | None = None


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def buscar_pedido(pedido_id: str) -> dict[str, Any]:
    dados = supabase.table("cti_pedidos").select("*").eq("id", pedido_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return dados[0]


@router.get("/pedidos/{pedido_id}/ciclo")
def obter_ciclo(pedido_id: str):
    pedido = buscar_pedido(pedido_id)
    atual = str(pedido.get("status_ciclo") or "PEDIDO").upper()
    return {
        "pedido_id": pedido_id,
        "status_ciclo": atual,
        "etapas": ETAPAS,
        "carrier_confirmado_em": pedido.get("carrier_confirmado_em"),
        "faturado_em": pedido.get("faturado_em"),
        "numero_nf": pedido.get("numero_nf"),
        "entregue_em": pedido.get("entregue_em"),
        "instalado_em": pedido.get("instalado_em"),
        "encerrado_em": pedido.get("encerrado_em"),
        "observacao_acompanhamento": pedido.get("observacao_acompanhamento"),
        "pode_encerrar": bool(pedido.get("instalado_em")),
    }


@router.post("/pedidos/{pedido_id}/ciclo")
def atualizar_ciclo(pedido_id: str, dados: AtualizarCicloRequest):
    pedido = buscar_pedido(pedido_id)
    etapa = dados.etapa.strip().upper()
    if etapa not in ETAPAS[1:]:
        raise HTTPException(status_code=422, detail="Etapa operacional inválida.")

    atual = str(pedido.get("status_ciclo") or "PEDIDO").upper()
    atual_idx = ETAPAS.index(atual) if atual in ETAPAS else 0
    novo_idx = ETAPAS.index(etapa)
    if novo_idx > atual_idx + 1:
        raise HTTPException(status_code=422, detail=f"Conclua primeiro a etapa {ETAPAS[atual_idx + 1]}.")
    if etapa == "FATURADO" and not (dados.numero_nf or pedido.get("numero_nf")):
        raise HTTPException(status_code=422, detail="Informe o número da NF para confirmar o faturamento.")
    if etapa == "ENCERRADO" and not pedido.get("instalado_em"):
        raise HTTPException(status_code=422, detail="O ciclo só pode ser encerrado após a instalação do equipamento.")

    payload: dict[str, Any] = {
        "status_ciclo": etapa,
        "updated_at": agora(),
    }
    if dados.observacao is not None:
        payload["observacao_acompanhamento"] = dados.observacao.strip() or None
    if etapa == "CARRIER":
        payload["carrier_confirmado_em"] = pedido.get("carrier_confirmado_em") or agora()
        payload["status_envio_carrier"] = "ENVIADO"
        payload["enviado_carrier_em"] = pedido.get("enviado_carrier_em") or agora()
    elif etapa == "FATURADO":
        payload["faturado_em"] = pedido.get("faturado_em") or agora()
        payload["numero_nf"] = (dados.numero_nf or str(pedido.get("numero_nf") or "")).strip()
    elif etapa == "ENTREGUE":
        payload["entregue_em"] = pedido.get("entregue_em") or agora()
    elif etapa == "INSTALADO":
        payload["instalado_em"] = pedido.get("instalado_em") or agora()
    elif etapa == "ENCERRADO":
        payload["encerrado_em"] = pedido.get("encerrado_em") or agora()
        payload["status"] = "CONCLUIDO"

    atualizado = supabase.table("cti_pedidos").update(payload).eq("id", pedido_id).execute().data or []
    return atualizado[0] if atualizado else {**pedido, **payload}


@router.get("/ciclo-resumo")
def resumo_ciclo():
    pedidos = supabase.table("cti_pedidos").select("status_ciclo,carrier_confirmado_em,faturado_em,entregue_em,instalado_em,encerrado_em").execute().data or []
    contagem = {etapa: 0 for etapa in ETAPAS}
    for pedido in pedidos:
        etapa = str(pedido.get("status_ciclo") or "PEDIDO").upper()
        contagem[etapa if etapa in contagem else "PEDIDO"] += 1
    return {
        "total_pedidos": len(pedidos),
        "por_etapa": contagem,
        "enviados_carrier": sum(1 for p in pedidos if p.get("carrier_confirmado_em")),
        "faturados": sum(1 for p in pedidos if p.get("faturado_em")),
        "entregues": sum(1 for p in pedidos if p.get("entregue_em")),
        "instalados": sum(1 for p in pedidos if p.get("instalado_em")),
        "encerrados": sum(1 for p in pedidos if p.get("encerrado_em")),
    }
