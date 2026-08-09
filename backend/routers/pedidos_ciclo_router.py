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
    numero_serie_nf: str | None = None
    numero_serie_instalado: str | None = None
    observacao: str | None = None


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def buscar_pedido(pedido_id: str) -> dict[str, Any]:
    dados = supabase.table("cti_pedidos").select("*").eq("id", pedido_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return dados[0]


def _envio_real_confirmado(pedido: dict[str, Any]) -> tuple[bool, str | None]:
    dossie = pedido.get("dossie_documentos") or []
    if not isinstance(dossie, list):
        return False, None
    for registro in reversed(dossie):
        if not isinstance(registro, dict):
            continue
        if registro.get("tipo") == "ENVIO_PEDIDO" and str(registro.get("status_envio") or "").upper() == "ENVIADO":
            return True, str(registro.get("enviado_em") or "") or None
    return False, None


def _sincronizar_carrier(pedido: dict[str, Any]) -> dict[str, Any]:
    confirmado, enviado_em = _envio_real_confirmado(pedido)
    atual = str(pedido.get("status_ciclo") or "PEDIDO").upper()
    if confirmado and atual == "PEDIDO":
        instante = enviado_em or agora()
        atualizado = (
            supabase.table("cti_pedidos")
            .update({
                "status_ciclo": "CARRIER",
                "status_envio_carrier": "ENVIADO",
                "carrier_confirmado_em": pedido.get("carrier_confirmado_em") or instante,
                "enviado_carrier_em": pedido.get("enviado_carrier_em") or instante,
                "updated_at": agora(),
            })
            .eq("id", pedido["id"])
            .execute()
            .data
            or []
        )
        return atualizado[0] if atualizado else pedido
    return pedido


@router.get("/ciclos")
def listar_ciclos():
    pedidos = supabase.table("cti_pedidos").select("*").order("created_at", desc=True).execute().data or []
    return [
        {k: sincronizado.get(k) for k in (
            "id", "numero", "item_oportunidade_id", "status_ciclo", "status_envio_carrier",
            "carrier_confirmado_em", "faturado_em", "numero_nf", "numero_serie_nf",
            "entregue_em", "instalado_em", "numero_serie_instalado", "encerrado_em",
            "observacao_acompanhamento"
        )}
        for sincronizado in (_sincronizar_carrier(pedido) for pedido in pedidos)
    ]


@router.get("/pedidos/{pedido_id}/ciclo")
def obter_ciclo(pedido_id: str):
    pedido = _sincronizar_carrier(buscar_pedido(pedido_id))
    atual = str(pedido.get("status_ciclo") or "PEDIDO").upper()
    envio_confirmado, _ = _envio_real_confirmado(pedido)
    return {
        "pedido_id": pedido_id,
        "status_ciclo": atual,
        "etapas": ETAPAS,
        "envio_carrier_confirmado": envio_confirmado,
        "carrier_confirmado_em": pedido.get("carrier_confirmado_em"),
        "faturado_em": pedido.get("faturado_em"),
        "numero_nf": pedido.get("numero_nf"),
        "numero_serie_nf": pedido.get("numero_serie_nf"),
        "entregue_em": pedido.get("entregue_em"),
        "instalado_em": pedido.get("instalado_em"),
        "numero_serie_instalado": pedido.get("numero_serie_instalado"),
        "encerrado_em": pedido.get("encerrado_em"),
        "observacao_acompanhamento": pedido.get("observacao_acompanhamento"),
        "pode_encerrar": bool(pedido.get("instalado_em")),
        "serie_divergente": bool(
            pedido.get("numero_serie_nf")
            and pedido.get("numero_serie_instalado")
            and str(pedido.get("numero_serie_nf")).strip().upper()
            != str(pedido.get("numero_serie_instalado")).strip().upper()
        ),
    }


@router.post("/pedidos/{pedido_id}/ciclo")
def atualizar_ciclo(pedido_id: str, dados: AtualizarCicloRequest):
    pedido = _sincronizar_carrier(buscar_pedido(pedido_id))
    etapa = dados.etapa.strip().upper()
    if etapa not in ETAPAS[1:]:
        raise HTTPException(status_code=422, detail="Etapa operacional inválida.")
    if etapa == "CARRIER":
        raise HTTPException(
            status_code=409,
            detail="A etapa CARRIER não pode ser confirmada manualmente. Ela é liberada somente após envio real do pedido por e-mail e gravação do protocolo de envio.",
        )

    atual = str(pedido.get("status_ciclo") or "PEDIDO").upper()
    atual_idx = ETAPAS.index(atual) if atual in ETAPAS else 0
    novo_idx = ETAPAS.index(etapa)
    if novo_idx > atual_idx + 1:
        raise HTTPException(status_code=422, detail=f"Conclua primeiro a etapa {ETAPAS[atual_idx + 1]}.")
    if atual == "PEDIDO":
        raise HTTPException(status_code=409, detail="Envie primeiro o pedido à CARRIER e confirme o protocolo real de e-mail.")
    if etapa == "FATURADO":
        if not (dados.numero_nf or pedido.get("numero_nf")):
            raise HTTPException(status_code=422, detail="Informe o número da NF para confirmar o faturamento.")
        if not (dados.numero_serie_nf or pedido.get("numero_serie_nf")):
            raise HTTPException(status_code=422, detail="Informe o número de série constante na NF para garantir o rastreio do equipamento.")
    if etapa == "INSTALADO" and not (dados.numero_serie_instalado or pedido.get("numero_serie_instalado")):
        raise HTTPException(status_code=422, detail="Informe o número de série efetivamente instalado.")
    if etapa == "ENCERRADO" and not pedido.get("instalado_em"):
        raise HTTPException(status_code=422, detail="O ciclo só pode ser encerrado após a instalação do equipamento.")

    payload: dict[str, Any] = {"status_ciclo": etapa, "updated_at": agora()}
    if dados.observacao is not None:
        payload["observacao_acompanhamento"] = dados.observacao.strip() or None
    if etapa == "FATURADO":
        payload["faturado_em"] = pedido.get("faturado_em") or agora()
        payload["numero_nf"] = (dados.numero_nf or str(pedido.get("numero_nf") or "")).strip()
        payload["numero_serie_nf"] = (dados.numero_serie_nf or str(pedido.get("numero_serie_nf") or "")).strip().upper()
    elif etapa == "ENTREGUE":
        payload["entregue_em"] = pedido.get("entregue_em") or agora()
    elif etapa == "INSTALADO":
        payload["instalado_em"] = pedido.get("instalado_em") or agora()
        payload["numero_serie_instalado"] = (dados.numero_serie_instalado or str(pedido.get("numero_serie_instalado") or "")).strip().upper()
    elif etapa == "ENCERRADO":
        payload["encerrado_em"] = pedido.get("encerrado_em") or agora()
        payload["status"] = "CONCLUIDO"

    atualizado = supabase.table("cti_pedidos").update(payload).eq("id", pedido_id).execute().data or []
    return atualizado[0] if atualizado else {**pedido, **payload}


@router.get("/ciclo-resumo")
def resumo_ciclo():
    pedidos = [_sincronizar_carrier(p) for p in (supabase.table("cti_pedidos").select("*").execute().data or [])]
    contagem = {etapa: 0 for etapa in ETAPAS}
    for pedido in pedidos:
        etapa = str(pedido.get("status_ciclo") or "PEDIDO").upper()
        contagem[etapa if etapa in contagem else "PEDIDO"] += 1
    divergencias = sum(
        1 for p in pedidos
        if p.get("numero_serie_nf") and p.get("numero_serie_instalado")
        and str(p.get("numero_serie_nf")).strip().upper() != str(p.get("numero_serie_instalado")).strip().upper()
    )
    return {
        "total_pedidos": len(pedidos),
        "por_etapa": contagem,
        "enviados_carrier": sum(1 for p in pedidos if p.get("carrier_confirmado_em")),
        "faturados": sum(1 for p in pedidos if p.get("faturado_em")),
        "entregues": sum(1 for p in pedidos if p.get("entregue_em")),
        "instalados": sum(1 for p in pedidos if p.get("instalado_em")),
        "encerrados": sum(1 for p in pedidos if p.get("encerrado_em")),
        "divergencias_numero_serie": divergencias,
    }
