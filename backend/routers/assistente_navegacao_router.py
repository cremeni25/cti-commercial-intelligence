"""Pergunte ao CTI e busca universal (qualquer usuário autenticado; dados no escopo de cada um)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.carteira_setorizada_router import _gestao
from services import assistente_navegacao as assistente

router = APIRouter(prefix="/crm-seguro/assistente", tags=["Pergunte ao CTI"])


def _escopo(usuario: UsuarioAutenticado) -> tuple[str | None, bool]:
    if _gestao(usuario):
        return None, True
    p = usuario.permissoes or {}
    pode = bool(p.get("clientes_visualizar") or p.get("oportunidades_visualizar") or p.get("oportunidades_editar"))
    return str(usuario.id), pode


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=2, max_length=500)


@router.post("/perguntar")
def perguntar(corpo: Pergunta, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    responsavel, pode = _escopo(usuario)
    return assistente.perguntar(corpo.pergunta, responsavel, pode)


@router.get("/buscar")
def buscar(q: str = Query(min_length=1, max_length=120), usuario: UsuarioAutenticado = Depends(usuario_atual)):
    responsavel, pode = _escopo(usuario)
    return assistente.buscar(q, responsavel, pode)
