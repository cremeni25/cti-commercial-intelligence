from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from html import escape
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase
from routers.propostas_pedidos_router import emitir_proposta
from routers.propostas_primeira_pagina_router import validar_documento_para_emissao
from services.docx_pdf_conversion_service import DocxPdfConversionError, convert_docx_to_pdf
from services.email_transport_service import (
    TransporteEmailNaoConfigurado,
    buscar_email_enviado,
    enviar_email,
)
from services.proposal_document_preview import build_preview_official_proposal
from services.proposal_document_repository import ProposalDocumentRepositoryError

router = APIRouter(prefix="/crm-app/propostas", tags=["CRM App"])

STATUS_PRE_EMISSAO = {"RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"}
STATUS_ENVIAVEL = {"EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO", "ACEITA", "CONVERTIDA_PEDIDO"}


class EnviarPropostaRequest(BaseModel):
    destinatarios: list[str] = Field(min_length=1)
    assunto: str | None = None
    mensagem: str | None = None


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail=detalhe)
    return dados[0]


def _cliente(cliente_id: str) -> dict[str, Any]:
    for tabela in ("clientes", "cti_clientes"):
        try:
            dados = supabase.table(tabela).select("*").eq("id", cliente_id).limit(1).execute().data or []
        except Exception:
            dados = []
        if dados:
            return dados[0]
    return {}


def _emails_validos(valores: list[str]) -> list[str]:
    resultado: list[str] = []
    for bruto in valores:
        email = str(bruto or "").strip().lower()
        if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
            raise HTTPException(status_code=422, detail=f"E-mail inválido: {bruto}")
        if email not in resultado:
            resultado.append(email)
    if not resultado:
        raise HTTPException(status_code=422, detail="Informe ao menos um destinatário válido.")
    return resultado


def _chave_idempotencia(proposta_id: str, destinatarios: list[str], assunto: str, mensagem: str, pdf_sha: str) -> str:
    base = "|".join([proposta_id, ",".join(destinatarios), assunto, mensagem, pdf_sha])
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f"cti-proposta/{proposta_id}/{digest[:40]}"


@router.get("/{proposta_id}/status-envio-provedor")
def status_envio_provedor(proposta_id: str):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    numero = str(proposta.get("numero") or proposta_id)
    assunto = f"Proposta comercial {numero} - CTI"
    try:
        envio = buscar_email_enviado(assunto=assunto)
    except TransporteEmailNaoConfigurado as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao consultar o provedor de e-mail: {exc}") from exc
    return {
        "success": True,
        "proposta_id": proposta_id,
        "numero": numero,
        "encontrado": bool(envio),
        "envio": envio,
    }


@router.post("/{proposta_id}/enviar-email")
def enviar_proposta_por_email(proposta_id: str, dados: EnviarPropostaRequest):
    proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada.")
    item_id = str(proposta.get("item_oportunidade_id") or "")
    oportunidade_id = str(proposta.get("oportunidade_id") or "")
    cliente_id = str(proposta.get("cliente_id") or "")
    if not item_id or not oportunidade_id or not cliente_id:
        raise HTTPException(status_code=422, detail="A proposta não possui os vínculos comerciais necessários para gerar o documento.")

    item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")
    validar_documento_para_emissao(proposta, item)

    status = str(proposta.get("status_documento") or "RASCUNHO").upper()
    if status in STATUS_PRE_EMISSAO:
        emitir_proposta(proposta_id)
        proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada após emissão.")
        status = str(proposta.get("status_documento") or "").upper()
    if status not in STATUS_ENVIAVEL:
        raise HTTPException(status_code=409, detail="A proposta não está em condição de envio.")

    oportunidade = _primeiro("cti_oportunidades", oportunidade_id, "Oportunidade da proposta não encontrada.")
    cliente = _cliente(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente da proposta não encontrado.")

    try:
        preview = build_preview_official_proposal(
            supabase,
            proposta=proposta,
            item=item,
            oportunidade=oportunidade,
            cliente=cliente,
        )
        pdf = convert_docx_to_pdf(bytes(preview["content"]), str(preview["filename"]))
    except (ProposalDocumentRepositoryError, DocxPdfConversionError) as exc:
        raise HTTPException(status_code=503, detail=f"Não foi possível preparar o PDF oficial da proposta: {exc}") from exc

    destinatarios = _emails_validos(dados.destinatarios)
    numero = str(proposta.get("numero") or proposta_id)
    cliente_nome = str(cliente.get("nome") or cliente.get("razao_social") or cliente.get("nome_fantasia") or "Cliente").strip()
    valor = float(proposta.get("valor") or 0)
    valor_br = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    mensagem = str(dados.mensagem or "Segue a proposta comercial para sua análise.").strip()
    assunto = str(dados.assunto or f"Proposta comercial {numero} - CTI").strip()
    html = (
        f"<p>Olá, {escape(cliente_nome)}.</p>"
        f"<p>{escape(mensagem)}</p>"
        f"<p><strong>Proposta:</strong> {escape(numero)}<br>"
        f"<strong>Valor:</strong> {escape(valor_br)}</p>"
        "<p>O documento oficial segue anexado em PDF.</p>"
    )
    texto = f"Olá, {cliente_nome}.\n\n{mensagem}\n\nProposta: {numero}\nValor: {valor_br}\n\nO documento oficial segue anexado em PDF."

    try:
        enviado = enviar_email(
            destinatarios=destinatarios,
            assunto=assunto,
            html=html,
            texto=texto,
            attachments=[{"filename": pdf.filename, "content": base64.b64encode(pdf.content).decode("ascii")}],
            idempotency_key=_chave_idempotencia(proposta_id, destinatarios, assunto, mensagem, pdf.sha256),
        )
    except TransporteEmailNaoConfigurado as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar a proposta: {exc}") from exc

    try:
        supabase.table("cti_propostas").update({
            "status_documento": "ENVIADA",
            "status": "ENVIADA",
            "emitida_em": proposta.get("emitida_em") or _agora(),
        }).eq("id", proposta_id).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"E-mail confirmado pelo provedor ({enviado.message_id}), mas o CTI não conseguiu atualizar o status da proposta. Não reenvie; solicite reconciliação administrativa.",
        ) from exc

    try:
        supabase.table("cti_oportunidade_historico").insert({
            "oportunidade_id": oportunidade_id,
            "tipo": "PROPOSTA_ENVIO",
            "descricao": f"Proposta {numero} enviada por e-mail pelo CRM App.",
            "payload": {
                "proposta_id": proposta_id,
                "destinatarios": destinatarios,
                "provider": enviado.provider,
                "message_id": enviado.message_id,
                "arquivo": pdf.filename,
                "arquivo_sha256": pdf.sha256,
                "paginas": pdf.page_count,
            },
            "created_at": _agora(),
        }).execute()
    except Exception:
        pass

    return {
        "success": True,
        "proposta_id": proposta_id,
        "numero": numero,
        "destinatarios": destinatarios,
        "provider": enviado.provider,
        "message_id": enviado.message_id,
        "arquivo": pdf.filename,
        "sha256": pdf.sha256,
        "paginas": pdf.page_count,
    }
