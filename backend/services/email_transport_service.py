from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import httpx


@dataclass(frozen=True)
class EmailEnviado:
    provider: str
    message_id: str
    remetente: str
    destinatarios: list[str]
    cc: list[str]
    cco: list[str]


class TransporteEmailNaoConfigurado(RuntimeError):
    pass


def configuracao_email() -> dict[str, str | bool]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    remetente = os.getenv("CTI_EMAIL_FROM", "CTI Pedidos <pedidos@send.cti-intelligence.com>").strip()
    reply_to = os.getenv("CTI_EMAIL_REPLY_TO", "").strip()
    return {
        "configurado": bool(api_key and remetente),
        "remetente": remetente,
        "reply_to": reply_to,
    }


def _configuracao_resend() -> tuple[str, str, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    remetente = os.getenv("CTI_EMAIL_FROM", "CTI Pedidos <pedidos@send.cti-intelligence.com>").strip()
    reply_to = os.getenv("CTI_EMAIL_REPLY_TO", "").strip()
    if not api_key or not remetente:
        raise TransporteEmailNaoConfigurado(
            "O transporte de e-mail ainda não está configurado. Defina RESEND_API_KEY e CTI_EMAIL_FROM no Render."
        )
    return api_key, remetente, reply_to


def _attachments_payload(
    attachments: Sequence[Mapping[str, str]] | None,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in attachments or []:
        filename = str(item.get("filename") or "").strip()
        content = str(item.get("content") or "").strip()
        if not filename or not content:
            raise ValueError("Todo anexo deve possuir filename e content em base64.")
        result.append({"filename": filename, "content": content})
    return result


def buscar_email_enviado(*, assunto: str, destinatarios: Sequence[str] | None = None) -> dict[str, Any] | None:
    """Localiza no Resend um envio já confirmado, sem acessar conteúdo do corpo do e-mail."""
    api_key, _, _ = _configuracao_resend()
    try:
        resposta = httpx.get(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"limit": 100},
            timeout=20.0,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Falha ao consultar o provedor de e-mail: {exc}") from exc

    dados = resposta.json() if resposta.content else {}
    if resposta.status_code >= 400:
        detalhe = dados.get("message") if isinstance(dados, dict) else None
        raise RuntimeError(detalhe or f"O provedor recusou a consulta ({resposta.status_code}).")

    esperados = {str(item).strip().lower() for item in destinatarios or [] if str(item).strip()}
    itens = dados.get("data") if isinstance(dados, dict) else []
    for item in itens or []:
        if str(item.get("subject") or "").strip() != str(assunto or "").strip():
            continue
        encontrados = {str(valor).strip().lower() for valor in item.get("to") or [] if str(valor).strip()}
        if esperados and encontrados != esperados:
            continue
        return {
            "id": str(item.get("id") or "").strip(),
            "to": list(item.get("to") or []),
            "from": str(item.get("from") or "").strip(),
            "subject": str(item.get("subject") or "").strip(),
            "created_at": str(item.get("created_at") or "").strip(),
            "last_event": str(item.get("last_event") or "").strip(),
        }
    return None


def enviar_email(
    *,
    destinatarios: list[str],
    assunto: str,
    html: str,
    texto: str | None = None,
    attachments: Sequence[Mapping[str, str]] | None = None,
    idempotency_key: str | None = None,
    cc: Sequence[str] | None = None,
    cco: Sequence[str] | None = None,
) -> EmailEnviado:
    api_key, remetente, reply_to = _configuracao_resend()
    cc_lista = [str(item).strip() for item in cc or [] if str(item).strip()]
    cco_lista = [str(item).strip() for item in cco or [] if str(item).strip()]

    payload: dict[str, Any] = {
        "from": remetente,
        "to": destinatarios,
        "subject": assunto,
        "html": html,
    }
    if cc_lista:
        payload["cc"] = cc_lista
    if cco_lista:
        payload["bcc"] = cco_lista
    if texto:
        payload["text"] = texto
    if reply_to:
        payload["reply_to"] = reply_to
    attachment_payload = _attachments_payload(attachments)
    if attachment_payload:
        payload["attachments"] = attachment_payload

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if idempotency_key:
        headers["Idempotency-Key"] = str(idempotency_key)[:256]

    try:
        resposta = httpx.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Falha de comunicação com o provedor de e-mail: {exc}") from exc

    dados = resposta.json() if resposta.content else {}
    if resposta.status_code >= 400:
        detalhe = dados.get("message") if isinstance(dados, dict) else None
        raise RuntimeError(detalhe or f"O provedor recusou o envio ({resposta.status_code}).")

    message_id = str(dados.get("id") or "").strip() if isinstance(dados, dict) else ""
    if not message_id:
        raise RuntimeError("O provedor confirmou o envio sem retornar protocolo.")

    return EmailEnviado(
        provider="RESEND",
        message_id=message_id,
        remetente=remetente,
        destinatarios=destinatarios,
        cc=cc_lista,
        cco=cco_lista,
    )
