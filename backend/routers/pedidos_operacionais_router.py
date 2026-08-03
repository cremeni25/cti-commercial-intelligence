from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
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


class AtualizarDestinatariosPedidoRequest(BaseModel):
    destinatarios: list[str] = Field(min_length=1)
    observacoes_envio: str | None = None


class EnviarPedidoRequest(BaseModel):
    assunto: str | None = None
    mensagem: str | None = None


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


def _dossie_normalizado(valor: Any) -> list[dict[str, Any]]:
    if not isinstance(valor, list):
        return []
    return [registro for registro in valor if isinstance(registro, dict)]


def _ultimo_registro(pedido: dict[str, Any], tipo: str) -> dict[str, Any] | None:
    return next(
        (registro for registro in reversed(_dossie_normalizado(pedido.get("dossie_documentos"))) if registro.get("tipo") == tipo),
        None,
    )


def _persistir_dossie(pedido_id: str, dossie: list[dict[str, Any]], extras: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"dossie_documentos": dossie}
    if extras:
        payload.update(extras)
    atualizado = supabase.table("cti_pedidos").update(payload).eq("id", pedido_id).execute().data or []
    if not atualizado:
        raise HTTPException(status_code=500, detail="O pedido não confirmou a atualização operacional.")
    return atualizado[0]


def _registrar_destinatarios(pedido: dict[str, Any], destinatarios: list[str], observacoes: str | None) -> dict[str, Any]:
    dossie = [registro for registro in _dossie_normalizado(pedido.get("dossie_documentos")) if registro.get("tipo") != "DESTINATARIOS_PEDIDO"]
    dossie.append({
        "tipo": "DESTINATARIOS_PEDIDO",
        "destinatarios": destinatarios,
        "observacoes_envio": observacoes,
        "status_envio": "PENDENTE",
        "registrado_em": _agora(),
    })
    return _persistir_dossie(str(pedido["id"]), dossie)


def _smtp_config() -> dict[str, Any]:
    host = os.getenv("CTI_SMTP_HOST", "").strip()
    porta = int(os.getenv("CTI_SMTP_PORT", "587") or "587")
    usuario = os.getenv("CTI_SMTP_USER", "").strip()
    senha = os.getenv("CTI_SMTP_PASSWORD", "")
    remetente = os.getenv("CTI_SMTP_FROM", usuario).strip()
    nome = os.getenv("CTI_SMTP_FROM_NAME", "CTI Comercial").strip()
    tls = os.getenv("CTI_SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "nao", "não"}
    ssl_direto = os.getenv("CTI_SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "sim"}
    configurado = bool(host and remetente and (not usuario or senha))
    return {"host": host, "porta": porta, "usuario": usuario, "senha": senha, "remetente": remetente, "nome": nome, "tls": tls, "ssl": ssl_direto, "configurado": configurado}


def _pacote_pedido(pedido_id: str) -> dict[str, Any]:
    pedido = _primeiro("cti_pedidos", pedido_id, "Pedido não encontrado")
    proposta = _opcional("cti_propostas", str(pedido.get("proposta_id") or pedido.get("proposta_aceita_id") or ""))
    item = _opcional("cti_oportunidade_itens", str(pedido.get("item_oportunidade_id") or ""))
    oportunidade_id = (proposta or {}).get("oportunidade_id") or pedido.get("oportunidade_id")
    oportunidade = _opcional("cti_oportunidades", str(oportunidade_id or ""))
    cliente_id = pedido.get("cliente_id") or (proposta or {}).get("cliente_id") or (oportunidade or {}).get("cliente_id")
    cliente_cadastrado = _opcional("cti_clientes", str(cliente_id or ""))
    cliente = cliente_cadastrado

    snapshot = (proposta or {}).get("snapshot_dados") or {}
    cliente_snapshot = snapshot.get("cliente") if isinstance(snapshot, dict) else None
    oportunidade_snapshot = snapshot.get("oportunidade") if isinstance(snapshot, dict) else None
    if not cliente and isinstance(cliente_snapshot, dict):
        cliente = cliente_snapshot
    if not oportunidade and isinstance(oportunidade_snapshot, dict):
        oportunidade = oportunidade_snapshot

    nome_cliente = None
    fontes = [cliente, oportunidade, oportunidade_snapshot if isinstance(oportunidade_snapshot, dict) else None, snapshot if isinstance(snapshot, dict) else None]
    for fonte in fontes:
        if not isinstance(fonte, dict):
            continue
        nome_cliente = fonte.get("razao_social") or fonte.get("nome") or fonte.get("cliente_nome") or fonte.get("empresa")
        if nome_cliente:
            break
    if not cliente and nome_cliente:
        cliente = {"nome": nome_cliente, "razao_social": nome_cliente, "origem": "DOSSIE_COMERCIAL"}

    return {
        "pedido": pedido,
        "proposta": proposta,
        "item": item,
        "oportunidade": oportunidade,
        "cliente": cliente,
        "envio": _ultimo_registro(pedido, "DESTINATARIOS_PEDIDO"),
        "ultimo_envio": _ultimo_registro(pedido, "ENVIO_PEDIDO"),
        "integridade": {
            "cliente_cadastrado": bool(cliente_cadastrado),
            "cliente_recuperado_snapshot": bool(cliente and not cliente_cadastrado),
        },
    }


def _corpo_email(pacote: dict[str, Any], mensagem: str | None) -> str:
    pedido = pacote["pedido"]
    proposta = pacote.get("proposta") or {}
    item = pacote.get("item") or {}
    cliente = pacote.get("cliente") or {}
    envio = pacote.get("envio") or {}
    cliente_nome = cliente.get("razao_social") or cliente.get("nome") or "Cliente não identificado"
    linhas = [
        "PEDIDO COMERCIAL — CTI",
        "",
        f"Pedido: {pedido.get('numero') or pedido.get('id')}",
        f"Cliente: {cliente_nome}",
        f"Equipamento: {item.get('equipamento') or 'Não informado'}",
        f"Valor: R$ {float(pedido.get('valor') or 0):,.2f}",
        f"Proposta de origem: {proposta.get('numero') or 'Não informada'}",
        "",
    ]
    if mensagem:
        linhas.extend([mensagem.strip(), ""])
    observacoes = envio.get("observacoes_envio")
    if observacoes:
        linhas.extend(["Observações:", str(observacoes), ""])
    linhas.extend(["Mensagem enviada automaticamente pelo CTI Comercial."])
    return "\n".join(linhas)


@router.post("/propostas/{proposta_id}/converter-pedido-operacional")
def converter_pedido_operacional(proposta_id: str, dados: ConverterPedidoOperacionalRequest):
    destinatarios = _emails_validos(dados.destinatarios)
    pedidos = converter_em_pedido(proposta_id, ConverterPedidoRequest(responsavel_id=dados.responsavel_id, data_pedido=dados.data_pedido, origem_comercial="CRM_APP"))
    pedido = pedidos[0] if isinstance(pedidos, list) and pedidos else pedidos
    if not isinstance(pedido, dict) or not pedido.get("id"):
        raise HTTPException(status_code=500, detail="Pedido criado sem identificação válida.")
    return _registrar_destinatarios(pedido, destinatarios, dados.observacoes_envio)


@router.post("/pedidos/{pedido_id}/destinatarios")
def atualizar_destinatarios_pedido(pedido_id: str, dados: AtualizarDestinatariosPedidoRequest):
    pedido = _primeiro("cti_pedidos", pedido_id, "Pedido não encontrado")
    return _registrar_destinatarios(pedido, _emails_validos(dados.destinatarios), dados.observacoes_envio)


@router.get("/pedidos/transporte/status")
def status_transporte_pedidos():
    config = _smtp_config()
    return {"configurado": config["configurado"], "provedor": "SMTP", "remetente": config["remetente"] or None}


@router.post("/pedidos/{pedido_id}/enviar")
def enviar_pedido(pedido_id: str, dados: EnviarPedidoRequest):
    pacote = _pacote_pedido(pedido_id)
    pedido = pacote["pedido"]
    envio = pacote.get("envio") or {}
    destinatarios = _emails_validos(list(envio.get("destinatarios") or []))
    config = _smtp_config()
    if not config["configurado"]:
        raise HTTPException(status_code=503, detail="Transporte de e-mail não configurado. Cadastre CTI_SMTP_HOST, CTI_SMTP_FROM e, quando aplicável, CTI_SMTP_USER e CTI_SMTP_PASSWORD no Render.")

    assunto = (dados.assunto or f"Pedido comercial {pedido.get('numero') or pedido_id}").strip()
    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = f"{config['nome']} <{config['remetente']}>"
    mensagem["To"] = ", ".join(destinatarios)
    mensagem.set_content(_corpo_email(pacote, dados.mensagem))

    tentativa = _agora()
    try:
        if config["ssl"]:
            servidor = smtplib.SMTP_SSL(config["host"], config["porta"], timeout=30, context=ssl.create_default_context())
        else:
            servidor = smtplib.SMTP(config["host"], config["porta"], timeout=30)
        with servidor:
            servidor.ehlo()
            if config["tls"] and not config["ssl"]:
                servidor.starttls(context=ssl.create_default_context())
                servidor.ehlo()
            if config["usuario"]:
                servidor.login(config["usuario"], config["senha"])
            servidor.send_message(mensagem)
    except Exception as exc:
        dossie = _dossie_normalizado(pedido.get("dossie_documentos"))
        dossie.append({"tipo": "ENVIO_PEDIDO", "status_envio": "FALHA", "destinatarios": destinatarios, "assunto": assunto, "tentado_em": tentativa, "erro": str(exc)[:500]})
        _persistir_dossie(pedido_id, dossie, {"status_envio_carrier": "FALHA"})
        raise HTTPException(status_code=502, detail="O servidor de e-mail rejeitou o envio. A falha foi registrada no pedido.") from exc

    enviado_em = _agora()
    dossie = _dossie_normalizado(pedido.get("dossie_documentos"))
    dossie.append({"tipo": "ENVIO_PEDIDO", "status_envio": "ENVIADO", "destinatarios": destinatarios, "assunto": assunto, "tentado_em": tentativa, "enviado_em": enviado_em, "provedor": "SMTP"})
    atualizado = _persistir_dossie(pedido_id, dossie, {"status_envio_carrier": "ENVIADO", "enviado_carrier_em": enviado_em})
    return {"pedido": atualizado, "status": "ENVIADO", "destinatarios": destinatarios, "enviado_em": enviado_em}


@router.get("/pedidos/{pedido_id}")
def consultar_pedido_operacional(pedido_id: str):
    return _pacote_pedido(pedido_id)
