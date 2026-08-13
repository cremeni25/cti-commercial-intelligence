from __future__ import annotations

import base64
from datetime import datetime, timezone
from html import escape
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase
from routers.propostas_pedidos_router import emitir_proposta
from services.docx_pdf_conversion_service import DocxPdfConversionError, convert_docx_to_pdf
from services.email_transport_service import TransporteEmailNaoConfigurado, enviar_email
from services.proposal_document_preview import build_preview_official_proposal
from services.proposal_document_repository import ProposalDocumentRepositoryError

router = APIRouter(prefix="/crm-app/oportunidades", tags=["CRM App"])

STATUS_PRE_EMISSAO = {"RASCUNHO", "EM_REVISAO", "APROVADA_INTERNA"}
STATUS_ENVIAVEL = {"EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO", "ACEITA", "CONVERTIDA_PEDIDO"}


class EnviarPropostasOportunidadeRequest(BaseModel):
    proposta_ids: list[str] = Field(min_length=1)
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


@router.post("/{oportunidade_id}/enviar-propostas-email")
def enviar_propostas_oportunidade_por_email(oportunidade_id: str, dados: EnviarPropostasOportunidadeRequest):
    oportunidade = _primeiro("cti_oportunidades", oportunidade_id, "Oportunidade não encontrada.")
    cliente_id = str(oportunidade.get("cliente_id") or "")
    if not cliente_id:
        raise HTTPException(status_code=422, detail="A oportunidade não possui cliente vinculado.")
    cliente = _cliente(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente da oportunidade não encontrado.")

    proposta_ids = []
    for bruto in dados.proposta_ids:
        proposta_id = str(bruto or "").strip()
        if proposta_id and proposta_id not in proposta_ids:
            proposta_ids.append(proposta_id)
    if not proposta_ids:
        raise HTTPException(status_code=422, detail="Informe ao menos uma proposta da oportunidade.")

    anexos: list[dict[str, str]] = []
    propostas_preparadas: list[dict[str, Any]] = []
    valor_total = 0.0

    for proposta_id in proposta_ids:
        proposta = _primeiro("cti_propostas", proposta_id, f"Proposta {proposta_id} não encontrada.")
        if str(proposta.get("oportunidade_id") or "") != oportunidade_id:
            raise HTTPException(status_code=409, detail="Todas as propostas devem pertencer à mesma oportunidade.")
        status = str(proposta.get("status_documento") or "RASCUNHO").upper()
        if status in STATUS_PRE_EMISSAO:
            emitir_proposta(proposta_id)
            proposta = _primeiro("cti_propostas", proposta_id, "Proposta não encontrada após emissão.")
            status = str(proposta.get("status_documento") or "").upper()
        if status not in STATUS_ENVIAVEL:
            raise HTTPException(status_code=409, detail=f"A proposta {proposta.get('numero') or proposta_id} não está em condição de envio.")

        item_id = str(proposta.get("item_oportunidade_id") or "")
        if not item_id:
            raise HTTPException(status_code=422, detail="Uma das propostas não possui item comercial vinculado.")
        item = _primeiro("cti_oportunidade_itens", item_id, "Item comercial da proposta não encontrado.")

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
            raise HTTPException(status_code=503, detail=f"Não foi possível preparar um dos PDFs oficiais: {exc}") from exc

        anexos.append({"filename": pdf.filename, "content": base64.b64encode(pdf.content).decode("ascii")})
        propostas_preparadas.append({
            "id": proposta_id,
            "numero": str(proposta.get("numero") or proposta_id),
            "item_id": item_id,
            "equipamento": str(item.get("nome_comercial") or item.get("equipamento") or "Equipamento"),
            "quantidade": int(item.get("quantidade") or 1),
            "valor": float(proposta.get("valor") or 0),
            "arquivo": pdf.filename,
            "sha256": pdf.sha256,
            "paginas": pdf.page_count,
        })
        valor_total += float(proposta.get("valor") or 0)

    destinatarios = _emails_validos(dados.destinatarios)
    cliente_nome = str(cliente.get("nome") or cliente.get("razao_social") or cliente.get("nome_fantasia") or "Cliente").strip()
    titulo_oportunidade = str(oportunidade.get("titulo") or "Negociação comercial").strip()
    mensagem = str(dados.mensagem or "Seguem as propostas comerciais dos equipamentos negociados para sua análise.").strip()
    assunto = str(dados.assunto or f"Propostas comerciais - {titulo_oportunidade} - CTI").strip()
    valor_br = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    lista_html = "".join(
        f"<li><strong>{escape(item['numero'])}</strong> — {escape(item['equipamento'])} — {item['quantidade']} un.</li>"
        for item in propostas_preparadas
    )
    html = (
        f"<p>Olá, {escape(cliente_nome)}.</p>"
        f"<p>{escape(mensagem)}</p>"
        f"<p><strong>Negociação:</strong> {escape(titulo_oportunidade)}<br>"
        f"<strong>Valor total negociado:</strong> {escape(valor_br)}</p>"
        f"<ul>{lista_html}</ul>"
        "<p>Cada proposta oficial segue anexada separadamente em PDF, preservando o modelo e as condições de cada equipamento.</p>"
    )
    texto = (
        f"Olá, {cliente_nome}.\n\n{mensagem}\n\nNegociação: {titulo_oportunidade}\n"
        f"Valor total negociado: {valor_br}\n\n" +
        "\n".join(f"- {item['numero']} | {item['equipamento']} | {item['quantidade']} un." for item in propostas_preparadas) +
        "\n\nCada proposta oficial segue anexada separadamente em PDF."
    )

    try:
        enviado = enviar_email(
            destinatarios=destinatarios,
            assunto=assunto,
            html=html,
            texto=texto,
            attachments=anexos,
        )
    except TransporteEmailNaoConfigurado as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar as propostas: {exc}") from exc

    agora = _agora()
    for proposta in propostas_preparadas:
        supabase.table("cti_propostas").update({
            "status_documento": "ENVIADA",
            "status": "ENVIADA",
            "updated_at": agora,
        }).eq("id", proposta["id"]).execute()

    try:
        supabase.table("cti_oportunidade_historico").insert({
            "oportunidade_id": oportunidade_id,
            "tipo": "PROPOSTAS_ENVIO_CONJUNTO",
            "descricao": f"{len(propostas_preparadas)} proposta(s) enviadas em um único processo pelo CRM App.",
            "payload": {
                "proposta_ids": [item["id"] for item in propostas_preparadas],
                "destinatarios": destinatarios,
                "provider": enviado.provider,
                "message_id": enviado.message_id,
                "arquivos": [{"arquivo": item["arquivo"], "sha256": item["sha256"], "paginas": item["paginas"]} for item in propostas_preparadas],
                "valor_total": round(valor_total, 2),
            },
            "created_at": agora,
        }).execute()
    except Exception:
        pass

    return {
        "success": True,
        "oportunidade_id": oportunidade_id,
        "propostas": propostas_preparadas,
        "destinatarios": destinatarios,
        "provider": enviado.provider,
        "message_id": enviado.message_id,
        "valor_total": round(valor_total, 2),
    }
