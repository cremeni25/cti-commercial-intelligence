"""Campanhas por grupo da carteira, posts do Canal e autorização LGPD (gestão)."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.carteira_setorizada_router import _gestao
from services import campanhas_comerciais as campanhas

router = APIRouter(prefix="/crm-seguro/campanhas", tags=["Campanhas comerciais"])


def _exigir_gestao(usuario: UsuarioAutenticado) -> None:
    if not _gestao(usuario):
        raise HTTPException(status_code=403, detail="Campanhas disponíveis para a gestão.")


def _codigo(codigo: str) -> str:
    codigo = codigo.upper()
    if codigo not in campanhas.CAMPANHAS:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    return codigo


class EdicaoCampanha(BaseModel):
    mensagem: str = Field(min_length=20, max_length=1500)
    aprovar: bool = False


class Envio(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")


class Autorizacao(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    status: str = Field(pattern="^(AUTORIZADO|RECUSADO)$")
    origem: str = Field(default="WhatsApp", max_length=80)


@router.get("")
def listar(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_gestao(usuario)
    return {"campanhas": campanhas.resumo_campanhas(), "texto_autorizacao": campanhas.TEXTO_AUTORIZACAO, "posts_canal": campanhas.posts_do_canal()}


@router.get("/{codigo}")
def detalhe(codigo: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_gestao(usuario)
    return campanhas.publico_detalhado(_codigo(codigo))


@router.put("/{codigo}")
def editar(codigo: str, corpo: EdicaoCampanha, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_gestao(usuario)
    try:
        return campanhas.salvar_campanha(_codigo(codigo), corpo.mensagem, corpo.aprovar, str(usuario.id))
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro


@router.post("/{codigo}/enviado")
def enviado(codigo: str, corpo: Envio, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_gestao(usuario)
    try:
        campanhas.marcar_enviado(_codigo(codigo), corpo.cliente_id, str(usuario.id))
    except ValueError as erro:
        raise HTTPException(status_code=409, detail=str(erro)) from erro
    return {"ok": True}


@router.get("/{codigo}/exportacao")
def exportar(codigo: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_gestao(usuario)
    dados = campanhas.publico_detalhado(_codigo(codigo))
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["empresa", "cidade", "responsavel", "whatsapp", "autorizacao", "mensagem"])
    for c in dados["clientes"]:
        if c["autorizacao"] != "RECUSADO":
            escritor.writerow([c["nome"], c.get("cidade") or "", c.get("responsavel_nome") or "", c.get("telefone") or "", c["autorizacao"], c["mensagem"]])
    return Response(content="﻿" + saida.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="campanha-{dados["codigo"].lower()}.csv"'})


@router.post("/autorizacoes")
def autorizar(corpo: Autorizacao, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _exigir_gestao(usuario)
    return campanhas.registrar_consentimento(corpo.cliente_id, corpo.status, corpo.origem, str(usuario.id))
