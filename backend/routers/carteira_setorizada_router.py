"""Carteira setorizada, ficha única da empresa e dicionário comercial."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.glossario_comercial import GLOSSARIO
from services import carteira_setorizada as carteira

router = APIRouter(prefix="/crm-seguro", tags=["Carteira setorizada"])


def _gestao(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (usuario.tipo_usuario == "DIRETOR_VIENA_SP" and bool((usuario.permissoes or {}).get("acesso_total")))


def _pode_ver_carteira(usuario: UsuarioAutenticado) -> None:
    p = usuario.permissoes or {}
    if _gestao(usuario) or p.get("clientes_visualizar") or p.get("oportunidades_visualizar") or p.get("oportunidades_editar"):
        return
    raise HTTPException(status_code=403, detail="Carteira disponível para a equipe comercial.")


@router.get("/carteira/setorizacao")
def setorizacao(
    grupo: str | None = Query(default=None, max_length=40),
    sinal: str | None = Query(default=None, max_length=40),
    responsavel_id: str | None = Query(default=None, max_length=80),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _pode_ver_carteira(usuario)
    # Gestão vê toda a empresa (ou filtra um responsável); a equipe vê só a própria carteira.
    alvo = responsavel_id if _gestao(usuario) else str(usuario.id)
    return carteira.setorizacao(responsavel_id=alvo, grupo=grupo or None, sinal=sinal or None)


@router.get("/carteira/empresa/{cliente_id}")
def ficha_empresa(cliente_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    _pode_ver_carteira(usuario)
    dados = carteira.ficha(cliente_id)
    if not dados:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    if not _gestao(usuario) and dados.get("responsavel_id") != str(usuario.id):
        raise HTTPException(status_code=403, detail="Cliente fora da sua carteira.")
    return dados


@router.get("/glossario")
def glossario(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {"termos": GLOSSARIO}
