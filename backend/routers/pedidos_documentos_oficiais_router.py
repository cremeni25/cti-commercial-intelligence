from __future__ import annotations

from typing import Any, Mapping

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase
from routers.pedidos_operacionais_router import _agora, _dossie_normalizado, _emails_validos, _html_pedido, _pacote_pedido
from services.email_transport_service import TransporteEmailNaoConfigurado, enviar_email
from services.proposal_order_document_service import ProposalOrderDocumentError, load_official_document_attachment, upsert_official_document_in_dossier

router = APIRouter(prefix="/crm-documentos", tags=["Pedidos com documento oficial"])


class EnviarPedidoOficialRequest(BaseModel):
    confirmar: bool = False


def _ultimo_registro(dossie: list[dict[str, Any]], tipo: str) -> dict[str, Any] | None:
    return next((item for item in reversed(dossie) if item.get("tipo") == tipo), None)


def _documento_atual(proposta: Mapping[str, Any]) -> Mapping[str, Any] | None:
    snapshot = proposta.get("snapshot_dados")
    if not isinstance(snapshot, Mapping):
        return None
    arquivo = snapshot.get("arquivo_documento")
    return arquivo if isinstance(arquivo, Mapping) and arquivo.get("sha256") else None


def _protocolo_ja_cobre_documento(protocolo: Mapping[str, Any] | None, proposta: Mapping[str, Any]) -> bool:
    if not protocolo or protocolo.get("status_envio") != "ENVIADO":
        return False
    atual = _documento_atual(proposta)
    if atual is None:
        return False
    anexo = protocolo.get("anexo")
    return isinstance(anexo, Mapping) and str(anexo.get("sha256") or "") == str(atual.get("sha256") or "")


@router.post("/pedidos/{pedido_id}/enviar-documento-oficial")
def enviar_pedido_com_documento_oficial(pedido_id: str, dados: EnviarPedidoOficialRequest):
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
    if _protocolo_ja_cobre_documento(protocolo_existente, proposta):
        return _pacote_pedido(pedido_id)

    try:
        attachment = load_official_document_attachment(supabase, proposta)
    except ProposalOrderDocumentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if protocolo_existente and protocolo_existente.get("status_envio") == "ENVIADO":
        anexo_anterior = protocolo_existente.get("anexo")
        if isinstance(anexo_anterior, Mapping) and str(anexo_anterior.get("sha256") or "") == attachment.sha256:
            return _pacote_pedido(pedido_id)

    destinatarios = _emails_validos(list(envio.get("destinatarios") or []), campo="Para")
    cc = _emails_validos(list(envio.get("cc") or []), obrigatorio=False, campo="CC")
    cco = _emails_validos(list(envio.get("cco") or []), obrigatorio=False, campo="CCO")
    assunto, html, texto = _html_pedido(pacote)
    try:
        resultado = enviar_email(
            destinatarios=destinatarios,
            cc=cc,
            cco=cco,
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
    dossie.append({
        "tipo": "ENVIO_PEDIDO_OFICIAL", "status_envio": "ENVIADO", "provider": resultado.provider,
        "message_id": resultado.message_id, "remetente": resultado.remetente, "destinatarios": resultado.destinatarios,
        "cc": resultado.cc, "cco": resultado.cco,
        "assunto": assunto, "anexo": {"filename": attachment.filename, "sha256": attachment.sha256, "bucket": attachment.bucket,
        "path": attachment.path, "template_code": attachment.template_code, "template_version": attachment.template_version, "immutable": True},
        "enviado_em": enviado_em,
    })

    atualizado = supabase.table("cti_pedidos").update({"dossie_documentos": dossie}).eq("id", pedido_id).execute().data or []
    if not atualizado:
        raise HTTPException(status_code=500, detail=f"O e-mail oficial foi aceito pelo provedor, mas o CTI não conseguiu registrar o protocolo. Protocolo externo: {resultado.message_id}")
    return _pacote_pedido(pedido_id)
