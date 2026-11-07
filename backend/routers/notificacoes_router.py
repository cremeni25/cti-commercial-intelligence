"""Inscrição no resumo diário (Web Push) e disparo agendado.

- ``/crm-seguro/notificacoes/*``: autenticado; cada pessoa só gerencia os
  próprios aparelhos.
- ``/interno/notificacoes/resumo-diario``: chamado pelo agendamento. Não usa
  sessão de usuário: exige o cabeçalho ``X-CTI-Cron-Token`` igual a
  ``CTI_CRON_TOKEN`` (comparação em tempo constante). Sem o token configurado,
  o endpoint fica desligado.
"""
from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from services import notificacoes_push as push

router = APIRouter(tags=["Notificações"])
ROTA_DISPARO = "/interno/notificacoes/resumo-diario"


class ChavesAssinatura(BaseModel):
    p256dh: str = Field(min_length=1, max_length=200)
    auth: str = Field(min_length=1, max_length=100)


class AssinaturaRequest(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000)
    keys: ChavesAssinatura


class RemoverAssinaturaRequest(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000)


def _indisponivel() -> HTTPException:
    return HTTPException(status_code=503, detail="O resumo no celular ainda está sendo ativado no servidor. Tente novamente mais tarde.")


@router.get("/crm-seguro/notificacoes/config")
def config_notificacoes(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {"disponivel": push.push_configurado(), "chave_publica": push.chave_publica() or None}


@router.post("/crm-seguro/notificacoes/assinatura", status_code=201)
def assinar(dados: AssinaturaRequest, request: Request, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    if not push.push_configurado():
        raise _indisponivel()
    try:
        return push.salvar_assinatura(str(usuario.id), dados.model_dump(), request.headers.get("user-agent", ""))
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    except push.PushIndisponivel:
        raise _indisponivel()


@router.post("/crm-seguro/notificacoes/assinatura/remover")
def remover(dados: RemoverAssinaturaRequest, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    try:
        push.remover_assinatura(str(usuario.id), dados.endpoint)
    except push.PushIndisponivel:
        raise _indisponivel()
    return {"ativo": False}


@router.post("/crm-seguro/notificacoes/teste")
def enviar_teste(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Envia uma notificação de teste somente para os aparelhos do próprio usuário."""
    if not push.push_configurado():
        raise _indisponivel()
    try:
        assinaturas = push.assinaturas_ativas(str(usuario.id))
    except push.PushIndisponivel:
        raise _indisponivel()
    if not assinaturas:
        raise HTTPException(status_code=404, detail="Nenhum aparelho ativo para este usuário.")
    mensagem = {"title": "CTI · resumo diário ativado", "body": "Você receberá suas prioridades nos dias úteis pela manhã.", "url": push.URL_DESTINO, "tag": "cti-teste"}
    return push.enviar_para_assinaturas(assinaturas, mensagem)


@router.post(ROTA_DISPARO)
def disparar_resumo_diario(x_cti_cron_token: str | None = Header(default=None)):
    esperado = os.getenv("CTI_CRON_TOKEN", "").strip()
    if not esperado:
        raise HTTPException(status_code=503, detail="Disparo agendado desligado (CTI_CRON_TOKEN ausente).")
    if not x_cti_cron_token or not hmac.compare_digest(x_cti_cron_token.encode(), esperado.encode()):
        raise HTTPException(status_code=401, detail="Token de agendamento inválido.")
    try:
        return push.enviar_resumo_diario()
    except push.PushIndisponivel:
        raise _indisponivel()
