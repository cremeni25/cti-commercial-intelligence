from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.crm_atividades_governanca_router import (
    AtividadeCreate,
    criar_atividade_operacional,
)
from routers.crm_router import (
    AtividadeUpdate,
    atualizar_atividade,
    concluir_atividade,
    obter_atividade,
    obter_oportunidade,
)
from routers.negociacoes_router import agenda_comercial

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-atividades"])

PERFIS_ESCOPO_PROPRIO = {
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
    "INDICADOR_VIENA_SP",
}


def _visao_consolidada(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _usa_escopo_proprio(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario in PERFIS_ESCOPO_PROPRIO


def _atividade_autorizada(atividade_id: str, usuario: UsuarioAutenticado) -> dict:
    atividade = obter_atividade(atividade_id)
    if _visao_consolidada(usuario) or not _usa_escopo_proprio(usuario):
        return atividade
    if str(atividade.get("usuario_id") or atividade.get("responsavel_id") or "") == str(usuario.id):
        return atividade
    raise HTTPException(status_code=404, detail="Atividade comercial não encontrada")


def _validar_oportunidade(oportunidade_id: str | None, usuario: UsuarioAutenticado) -> None:
    if not oportunidade_id or not _usa_escopo_proprio(usuario):
        return
    oportunidade = obter_oportunidade(str(oportunidade_id))
    if str(oportunidade.get("responsavel_id") or "") != str(usuario.id):
        raise HTTPException(status_code=404, detail="Negociação relacionada não encontrada")


def _filtrar_agenda(payload: dict, usuario: UsuarioAutenticado) -> dict:
    if _visao_consolidada(usuario) or not _usa_escopo_proprio(usuario):
        return payload
    itens = [
        item
        for item in list(payload.get("itens") or [])
        if str(item.get("usuario_id") or item.get("responsavel_id") or "") == str(usuario.id)
    ]
    resumo = {
        "total": len(itens),
        "atrasadas": sum(1 for item in itens if item.get("situacao") == "ATRASADA"),
        "hoje": sum(1 for item in itens if item.get("situacao") == "HOJE"),
        "futuras": sum(1 for item in itens if item.get("situacao") == "FUTURA"),
        "sem_data": sum(1 for item in itens if item.get("situacao") == "SEM_DATA"),
        "concluidas": sum(1 for item in itens if item.get("situacao") == "CONCLUIDA"),
    }
    return {**payload, "itens": itens, "resumo": resumo}


def _como_dict(registro) -> dict:
    if isinstance(registro, dict):
        return dict(registro)
    model_dump = getattr(registro, "model_dump", None)
    if callable(model_dump):
        return dict(model_dump())
    return {}


def _enriquecer_responsaveis(itens: list) -> list[dict]:
    normalizados = [_como_dict(item) for item in itens]
    ids = sorted(
        {
            str(item.get("usuario_id") or item.get("responsavel_id") or "").strip()
            for item in normalizados
            if str(item.get("usuario_id") or item.get("responsavel_id") or "").strip()
        }
    )
    if not ids:
        return normalizados

    resposta = (
        supabase.table("cti_users")
        .select("id,nome,email")
        .in_("id", ids)
        .execute()
    )
    usuarios = getattr(resposta, "data", None) or []
    por_id = {str(item.get("id")): item for item in usuarios}

    enriquecidos: list[dict] = []
    for item in normalizados:
        responsavel_id = str(item.get("usuario_id") or item.get("responsavel_id") or "").strip()
        usuario = por_id.get(responsavel_id)
        if usuario:
            item["responsavel_id"] = responsavel_id
            item["responsavel_nome"] = str(usuario.get("nome") or usuario.get("email") or "Usuário CTI")
        enriquecidos.append(item)
    return enriquecidos


def _enriquecer_atividade(atividade) -> dict:
    itens = _enriquecer_responsaveis([atividade])
    return itens[0] if itens else _como_dict(atividade)


def _enriquecer_agenda(payload: dict) -> dict:
    itens = _enriquecer_responsaveis(list(payload.get("itens") or []))
    return {**payload, "itens": itens}


@router.get("/agenda")
def agenda_segura(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    payload = _filtrar_agenda(agenda_comercial(), usuario)
    return _enriquecer_agenda(payload)


@router.get("/atividades/{atividade_id}")
def obter_atividade_segura(
    atividade_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    return _enriquecer_atividade(_atividade_autorizada(atividade_id, usuario))


@router.post("/atividades")
def criar_atividade_segura(
    atividade: AtividadeCreate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _validar_oportunidade(atividade.oportunidade_id, usuario)
    if _usa_escopo_proprio(usuario):
        atividade = atividade.model_copy(update={"usuario_id": str(usuario.id)})
    return criar_atividade_operacional(atividade)


@router.put("/atividades/{atividade_id}")
def atualizar_atividade_segura(
    atividade_id: str,
    atividade: AtividadeUpdate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _atividade_autorizada(atividade_id, usuario)
    _validar_oportunidade(atividade.oportunidade_id, usuario)
    if _usa_escopo_proprio(usuario):
        if atividade.usuario_id is not None and str(atividade.usuario_id) != str(usuario.id):
            raise HTTPException(status_code=403, detail="Não é permitido transferir o responsável desta atividade")
        atividade = atividade.model_copy(update={"usuario_id": str(usuario.id)})
    return atualizar_atividade(atividade_id, atividade)


@router.put("/atividades/{atividade_id}/concluir")
def concluir_atividade_segura(
    atividade_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _atividade_autorizada(atividade_id, usuario)
    return concluir_atividade(atividade_id)
