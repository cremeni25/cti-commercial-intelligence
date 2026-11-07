"""Endpoints do Agente de Inteligência Comercial e do registro de módulos.

Somente leitura. O escopo segue a regra oficial do CRM seguro: Master e
Diretor com acesso total enxergam a equipe (e podem filtrar um
responsável); todos os demais perfis enxergam apenas a própria carteira.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.modulos_plataforma import modulos_para_usuario
from services.inteligencia_comercial import gerar_briefing, provedores_registrados

router = APIRouter(prefix="/crm-seguro", tags=["Inteligência Comercial"])


def _visao_consolidada(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP" and bool((usuario.permissoes or {}).get("acesso_total"))
    )


@router.get("/inteligencia/briefing")
def briefing_comercial(
    responsavel_id: str | None = Query(default=None),
    limite: int = Query(default=8, ge=1, le=30),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    consolidado = _visao_consolidada(usuario)
    if responsavel_id and not consolidado and str(responsavel_id) != str(usuario.id):
        raise HTTPException(status_code=403, detail="Filtro por responsável disponível somente para a gestão.")
    return gerar_briefing(
        usuario_id=str(usuario.id),
        consolidado=consolidado,
        responsavel_id=responsavel_id if consolidado else None,
        limite_prioridades=limite,
    )


@router.get("/plataforma/modulos")
def modulos_plataforma(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return {
        "modulos": modulos_para_usuario(usuario.tipo_usuario, usuario.permissoes or {}),
        "provedores_inteligencia": [
            {"codigo": p.codigo, "modulo": p.modulo, "descricao": p.descricao} for p in provedores_registrados()
        ],
    }
