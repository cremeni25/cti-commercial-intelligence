from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.crm_router import obter_oportunidade
from routers.negociacoes_router import timeline_oportunidade

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-negocio-historico"])


def _visao_consolidada(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _usa_escopo_proprio(usuario: UsuarioAutenticado) -> bool:
    return not _visao_consolidada(usuario)


def _oportunidade_autorizada(oportunidade_id: str, usuario: UsuarioAutenticado) -> dict:
    oportunidade = obter_oportunidade(oportunidade_id)
    if _visao_consolidada(usuario):
        return oportunidade
    if str(oportunidade.get("responsavel_id") or "") == str(usuario.id):
        return oportunidade
    raise HTTPException(status_code=404, detail="Oportunidade comercial não encontrada")


def _evento_atividade(registro: dict, *, antecedente: bool = False) -> dict:
    descricao = str(registro.get("descricao") or "").strip()
    titulo = str(registro.get("titulo") or "Interação comercial").strip()
    if descricao:
        titulo = descricao
    return {
        "tipo": "HISTORICO_CLIENTE" if antecedente else "ATIVIDADE",
        "data_hora": registro.get("concluida_em") or registro.get("updated_at") or registro.get("created_at") or registro.get("data"),
        "titulo": titulo,
        "status": registro.get("status") or "CONCLUIDA",
        "responsavel_id": registro.get("usuario_id"),
        "registro": registro,
    }


def _historico_cliente_sem_vinculo(cliente_id: str, usuario: UsuarioAutenticado) -> list[dict]:
    if not cliente_id:
        return []
    consulta = (
        supabase.table("cti_atividades_registros")
        .select("*")
        .eq("cliente_id", cliente_id)
        .order("created_at", desc=True)
    )
    registros = consulta.execute().data or []
    saida: list[dict] = []
    for item in registros:
        if item.get("arquivado_em"):
            continue
        if item.get("oportunidade_id"):
            continue
        if _usa_escopo_proprio(usuario) and str(item.get("usuario_id") or "") != str(usuario.id):
            continue
        saida.append(item)
    return saida


@router.get("/timeline/{oportunidade_id}")
def timeline_oportunidade_segura(
    oportunidade_id: str,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    oportunidade = _oportunidade_autorizada(oportunidade_id, usuario)
    payload = timeline_oportunidade(oportunidade_id)
    eventos = list(payload.get("eventos") or [])

    ids_existentes = {
        str(((evento.get("registro") or {}) if isinstance(evento.get("registro"), dict) else {}).get("id") or "")
        for evento in eventos
    }

    normalizados: list[dict] = []
    for evento in eventos:
        registro = evento.get("registro") if isinstance(evento.get("registro"), dict) else {}
        if str(evento.get("tipo") or "").upper() == "ATIVIDADE":
            normalizados.append(_evento_atividade(registro))
        else:
            normalizados.append(evento)

    cliente_id = str(oportunidade.get("cliente_id") or "").strip()
    for atividade in _historico_cliente_sem_vinculo(cliente_id, usuario):
        if str(atividade.get("id") or "") in ids_existentes:
            continue
        normalizados.append(_evento_atividade(atividade, antecedente=True))

    normalizados.sort(key=lambda item: str(item.get("data_hora") or ""), reverse=True)
    return {
        **payload,
        "eventos": normalizados,
        "historico_cliente_incluido": True,
    }
