from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase
from routers.pedidos_operacionais_router import (
    _agora,
    _dossie_normalizado,
    _emails_validos,
    _html_pedido,
    _pacote_pedido,
)
from services.email_transport_service import (
    TransporteEmailNaoConfigurado,
    enviar_email,
)
from services.proposal_order_document_service import (
    ProposalOrderDocumentError,
    load_official_document_attachment,
    upsert_official_document_in_dossier,
)

router = APIRouter(prefix="/crm-documentos", tags=["Pedidos com documento oficial"])


class EnviarPedidoOficialRequest(BaseModel):
    confirmar: bool = False


def _ultimo_registro(dossie: list[dict[str, Any]], tipo: str) -> dict[str, Any] | None:
    return next((item for item in reversed(dossie) if item.get("tipo") == tipo), None)


@router.post("/pedidos/{pedido_id}/enviar-documento-oficial")
def enviar_pedido_com_documento_oficial(
    pedido_id: str,
    dados: EnviarPedidoOficialRequest,
):
    if not dados.confirmar:
        raise HTTPException(status_code=409, detail="Confirme expressamente o envio do pedido oficial.")

    pacote = _pacote_pedido(pedido_id)
    pedido = pacote["pedido"]
    proposta = pacote.get("proposta") or {}
    envio = pacote.get("envio") or {}
    if not proposta:
        raise HTTPException(status_code=409, detail="O pedido não possui proposta de origem vinculada.")

    dossie = _dossie_normalizado(pedido.get("dossie_documentos"))
    protocolo_existente = _ultimo_registro(dossie, "ENVIO_PEDIDO_OFICIAL")
    if protocolo_existente and protocolo_existente.get("status_envio") == "ENVIADO":
        return _pacote_pedido(pedido_id)

    try:
        attachment = load_official_document_attachment(supabase, proposta)
    except ProposalOrderDocumentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    destinatarios = _emails_validos(list(envio.get("destinatarios") or []))
    assunto, html, texto = _html_pedido(pacote)
    try:
        resultado = enviar_email(
            destinatarios=destinatarios,
            assunto=assunto,
            html=html,
            texto=texto,
            attachments=[attachment.resend_payload()],
        )
    except TransporteEmailNaoConfigurado as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Não foi possível enviar o pedido oficial: {exc}") from exc

    enviado_em = _agora()
    dossie = upsert_official_document_in_dossier(dossie, attachment)
    for registro in reversed(dossie):
        if registro.get("tipo") == "DESTINATARIOS_PEDIDO":
            registro["status_envio"] = "ENVIADO"
            registro["enviado_em"] = enviado_em
            break
    dossie.append(
        {
            "tipo": "ENVIO_PEDIDO_OFICIAL",
            "status_envio": "ENVIADO",
            "provider": resultado.provider,
            "message_id": resultado.message_id,
            "remetente": resultado.remetente,
            "destinatarios": resultado.destinatarios,
            "assunto": assunto,
            "anexo": {
                "filename": attachment.filename,
                "sha256": attachment.sha256,
                "bucket": attachment.bucket,
                "path": attachment.path,
                "template_code": attachment.template_code,
                "template_version": attachment.template_version,
                "immutable": True,
            },
            "enviado_em": enviado_em,
        }
    )

    atualizado = (
        supabase.table("cti_pedidos")
        .update({"dossie_documentos": dossie})
        .eq("id", pedido_id)
        .execute()
        .data
        or []
    )
    if not atualizado:
        raise HTTPException(
            status_code=500,
            detail=(
                "O e-mail oficial foi aceito pelo provedor, mas o CTI não conseguiu registrar o protocolo. "
                f"Protocolo externo: {resultado.message_id}"
            ),
        )
    return _pacote_pedido(pedido_id)
