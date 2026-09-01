from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_router import _proposta_autorizada
from services.cliente_documentos_financeiros import (
    anexar_documento,
    atualizar_cadastro_financeiro,
    desvincular_documento,
    listar_dossie,
    url_temporaria,
    vincular_documento,
)

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-financeiro"])


def _cliente_da_proposta(proposta: dict) -> str:
    cliente_id = str(proposta.get("cliente_id") or "").strip()
    if not cliente_id:
        raise HTTPException(status_code=422, detail="A proposta não possui cliente vinculado.")
    return cliente_id


class VinculoDocumentoRequest(BaseModel):
    documento_id: str


class CadastroFinanceiroRequest(BaseModel):
    status: str
    validado_carrier_em: date | None = None
    observacao: str | None = None


@router.get("/propostas/{proposta_id}/dossie-financeiro")
def obter_dossie_financeiro_proposta(
    proposta_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _proposta_autorizada(proposta_id, usuario)
    return listar_dossie(_cliente_da_proposta(proposta), proposta_id)


@router.post("/propostas/{proposta_id}/dossie-financeiro/documentos")
async def anexar_documento_financeiro_proposta(
    proposta_id: str,
    categoria: str = Form(...),
    observacao: str | None = Form(default=None),
    arquivo: UploadFile = File(...),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _proposta_autorizada(proposta_id, usuario)
    cliente_id = _cliente_da_proposta(proposta)
    documento = await anexar_documento(
        cliente_id=cliente_id,
        proposta_id=proposta_id,
        categoria=categoria,
        observacao=observacao,
        arquivo=arquivo,
        usuario_id=str(usuario.id),
    )
    return {"ok": True, "documento": documento}


@router.post("/propostas/{proposta_id}/dossie-financeiro/vincular")
def vincular_documento_financeiro_proposta(
    proposta_id: str,
    dados: VinculoDocumentoRequest,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _proposta_autorizada(proposta_id, usuario)
    return vincular_documento(
        proposta_id=proposta_id,
        documento_id=dados.documento_id,
        cliente_id=_cliente_da_proposta(proposta),
        usuario_id=str(usuario.id),
    )


@router.delete("/propostas/{proposta_id}/dossie-financeiro/documentos/{documento_id}/vinculo")
def desvincular_documento_financeiro_proposta(
    proposta_id: str,
    documento_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _proposta_autorizada(proposta_id, usuario)
    return desvincular_documento(proposta_id=proposta_id, documento_id=documento_id)


@router.get("/propostas/{proposta_id}/dossie-financeiro/documentos/{documento_id}/url")
def abrir_documento_financeiro_proposta(
    proposta_id: str,
    documento_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _proposta_autorizada(proposta_id, usuario)
    return url_temporaria(documento_id=documento_id, cliente_id=_cliente_da_proposta(proposta))


@router.put("/propostas/{proposta_id}/dossie-financeiro/cadastro")
def atualizar_cadastro_financeiro_proposta(
    proposta_id: str,
    dados: CadastroFinanceiroRequest,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    proposta = _proposta_autorizada(proposta_id, usuario)
    return atualizar_cadastro_financeiro(
        cliente_id=_cliente_da_proposta(proposta),
        status=dados.status,
        validado_carrier_em=dados.validado_carrier_em,
        observacao=dados.observacao,
        usuario_id=str(usuario.id),
    )
