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


def enviar_email(
    *,
    destinatarios: list[str],
    assunto: str,
    html: str,
    texto: str | None = None,
    attachments: Sequence[Mapping[str, str]] | None = None,
) -> EmailEnviado:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    remetente = os.getenv("CTI_EMAIL_FROM", "CTI Pedidos <pedidos@send.cti-intelligence.com>").strip()
    reply_to = os.getenv("CTI_EMAIL_REPLY_TO", "").strip()
    if not api_key or not remetente:
        raise TransporteEmailNaoConfigurado(
            "O transporte de e-mail ainda não está configurado. Defina RESEND_API_KEY e CTI_EMAIL_FROM no Render."
        )

    payload: dict[str, Any] = {
        "from": remetente,
        "to": destinatarios,
        "subject": assunto,
        "html": html,
    }
    if texto:
        payload["text"] = texto
    if reply_to:
        payload["reply_to"] = reply_to
    attachment_payload = _attachments_payload(attachments)
    if attachment_payload:
        payload["attachments"] = attachment_payload

    try:
        resposta = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
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
    )
