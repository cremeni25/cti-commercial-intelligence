from __future__ import annotations

import inspect

from services import email_transport_service as transport
from routers.crm_app_proposta_envio_router import _chave_idempotencia, enviar_proposta_por_email


class _Resposta:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.content = b"{}"

    def json(self):
        return self._payload


def test_envio_resend_recebe_chave_idempotencia(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_teste")
    monkeypatch.setenv("CTI_EMAIL_FROM", "CTI <cti@example.com>")
    capturado = {}

    def fake_post(url, *, headers, json, timeout):
        capturado.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _Resposta(200, {"id": "email-123"})

    monkeypatch.setattr(transport.httpx, "post", fake_post)
    enviado = transport.enviar_email(
        destinatarios=["destino@example.com"],
        assunto="Assunto",
        html="<p>Teste</p>",
        idempotency_key="cti/proposta/123",
    )

    assert enviado.message_id == "email-123"
    assert capturado["headers"]["Idempotency-Key"] == "cti/proposta/123"


def test_busca_envio_confirmado_por_assunto_e_destinatario(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_teste")
    monkeypatch.setenv("CTI_EMAIL_FROM", "CTI <cti@example.com>")

    def fake_get(url, *, headers, params, timeout):
        return _Resposta(200, {
            "data": [{
                "id": "email-456",
                "to": ["destino@example.com"],
                "from": "CTI <cti@example.com>",
                "subject": "Proposta comercial PROP-1 - CTI",
                "created_at": "2026-08-26T15:59:00Z",
                "last_event": "delivered",
            }]
        })

    monkeypatch.setattr(transport.httpx, "get", fake_get)
    encontrado = transport.buscar_email_enviado(
        assunto="Proposta comercial PROP-1 - CTI",
        destinatarios=["destino@example.com"],
    )

    assert encontrado is not None
    assert encontrado["id"] == "email-456"
    assert encontrado["last_event"] == "delivered"


def test_chave_idempotencia_e_estavel_para_mesmo_payload():
    args = ("proposta-1", ["destino@example.com"], "Assunto", "Mensagem", "sha-pdf")
    assert _chave_idempotencia(*args) == _chave_idempotencia(*args)
    assert _chave_idempotencia(*args) != _chave_idempotencia(
        "proposta-1", ["outro@example.com"], "Assunto", "Mensagem", "sha-pdf"
    )


def test_pos_envio_nao_tenta_gravar_updated_at_inexistente():
    codigo = inspect.getsource(enviar_proposta_por_email)
    assert '"updated_at"' not in codigo
