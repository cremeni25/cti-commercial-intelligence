from datetime import datetime, timezone
from typing import Any
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/crm-app/oportunidades", tags=["CRM App"])

CONFIRMACAO_ARQUIVAR = "ARQUIVAR HISTORICO DE HOMOLOGACAO"
CONFIRMACAO_RESTAURAR = "RESTAURAR LOTE"


class ArquivarHomologacaoPayload(BaseModel):
    oportunidade_ids: list[str]
    confirmacao: str
    motivo: str = "Registros criados para teste/homologação"


class PreviaHomologacaoPayload(BaseModel):
    oportunidade_ids: list[str]


class RestaurarHomologacaoPayload(BaseModel):
    confirmacao: str


def _admin(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente ADMIN_MASTER pode administrar registros de teste.")
    return usuario


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dados(tabela: str) -> list[dict[str, Any]]:
    try:
        return supabase.table(tabela).select("*").execute().data or []
    except Exception:
        return []


def _normalizar_confirmacao(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor.replace("\u00a0", " "))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.upper().split())


def _ids_ativos() -> set[str]:
    return {str(item.get("id")) for item in _dados("cti_oportunidades") if item.get("id")}


def _validar_ids_ativos(ids: list[str]) -> list[str]:
    selecionados = sorted({item.strip() for item in ids if item.strip()})
    if not selecionados:
        return []
    ativos = _ids_ativos()
    invalidos = [item for item in selecionados if item not in ativos]
    if invalidos:
        raise HTTPException(status_code=409, detail="A prévia ficou desatualizada. Recarregue a tela antes de continuar.")
    return selecionados


def _impacto_homologacao(selecionados: set[str] | None = None) -> dict[str, Any]:
    oportunidades_ativas = _dados("cti_oportunidades")
    oportunidades = oportunidades_ativas if selecionados is None else [
        item for item in oportunidades_ativas if str(item.get("id") or "") in selecionados
    ]
    oportunidade_ids = {str(item.get("id")) for item in oportunidades if item.get("id")}
    itens = [item for item in _dados("cti_oportunidade_itens") if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    item_ids = {str(item.get("id")) for item in itens if item.get("id")}
    pipeline = [item for item in _dados("cti_pipeline") if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    propostas = [item for item in _dados("cti_propostas") if str(item.get("oportunidade_id") or "") in oportunidade_ids or str(item.get("item_oportunidade_id") or "") in item_ids]
    proposta_ids = {str(item.get("id")) for item in propostas if item.get("id")}
    aceites = [item for item in _dados("cti_proposta_aceites") if str(item.get("proposta_id") or "") in proposta_ids]
    aceite_ids = {str(item.get("id")) for item in aceites if item.get("id")}
    pedidos = [item for item in _dados("cti_pedidos") if str(item.get("proposta_id") or "") in proposta_ids or str(item.get("proposta_aceita_id") or "") in proposta_ids or str(item.get("item_oportunidade_id") or "") in item_ids or str(item.get("aceite_id") or "") in aceite_ids]
    pedido_ids = {str(item.get("id")) for item in pedidos if item.get("id")}
    atividades = [item for item in _dados("cti_atividades") if str(item.get("oportunidade_id") or "") in oportunidade_ids or str(item.get("proposta_id") or "") in proposta_ids or str(item.get("pedido_id") or "") in pedido_ids]
    envios = [item for item in _dados("cti_envios_carrier") if str(item.get("proposta_id") or "") in proposta_ids or str(item.get("pedido_id") or "") in pedido_ids]
    vendas = [item for item in _dados("vendas") if str(item.get("oportunidade_id") or "") in oportunidade_ids or str(item.get("pedido_id") or "") in pedido_ids or str(item.get("item_oportunidade_id") or "") in item_ids]

    cliente_ids = {str(item.get("cliente_id")) for item in oportunidades if item.get("cliente_id")}
    clientes = {str(item.get("id")): item for item in _dados("clientes") if str(item.get("id") or "") in cliente_ids}
    oportunidades_resumo = [{
        "id": item.get("id"),
        "titulo": item.get("titulo"),
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "cliente_id": item.get("cliente_id"),
        "cliente_nome": (clientes.get(str(item.get("cliente_id"))) or {}).get("nome"),
    } for item in oportunidades]
    resumo = {
        "oportunidades": len(oportunidades), "itens": len(itens), "pipeline": len(pipeline),
        "atividades": len(atividades), "propostas": len(propostas), "aceites": len(aceites),
        "pedidos": len(pedidos), "envios": len(envios), "vendas": len(vendas),
        "clientes_mestre_preservados": len(cliente_ids),
    }
    return {
        "oportunidade_ids": sorted(oportunidade_ids),
        "resumo": resumo,
        "oportunidades": oportunidades_resumo,
        "aviso_clientes": "Os cadastros mestres de clientes são preservados; esta ação arquiva apenas o histórico transacional das oportunidades selecionadas.",
        "confirmacao_exigida": CONFIRMACAO_ARQUIVAR,
    }


@router.get("/homologacao/previa")
def previa_homologacao(usuario: UsuarioAutenticado = Depends(_admin)):
    _ = usuario
    return _impacto_homologacao()


@router.post("/homologacao/previa-selecao")
def previa_homologacao_selecao(dados: PreviaHomologacaoPayload, usuario: UsuarioAutenticado = Depends(_admin)):
    _ = usuario
    ids = _validar_ids_ativos(dados.oportunidade_ids)
    return _impacto_homologacao(set(ids))


@router.post("/homologacao/arquivar")
def arquivar_homologacao(dados: ArquivarHomologacaoPayload, usuario: UsuarioAutenticado = Depends(_admin)):
    if _normalizar_confirmacao(dados.confirmacao) != CONFIRMACAO_ARQUIVAR:
        raise HTTPException(status_code=422, detail=f"Digite a confirmação: {CONFIRMACAO_ARQUIVAR}")
    ids = _validar_ids_ativos(dados.oportunidade_ids)
    if not ids:
        raise HTTPException(status_code=422, detail="Selecione pelo menos uma oportunidade.")
    try:
        resposta = supabase.rpc("cti_arquivar_homologacao_crm", {
            "p_oportunidade_ids": ids,
            "p_usuario_id": usuario.id,
            "p_motivo": dados.motivo.strip() or "Registros criados para teste/homologação",
        }).execute().data
    except Exception as erro:
        raise HTTPException(status_code=409, detail=f"Não foi possível arquivar o lote: {erro}") from erro
    return resposta or {"success": True}


@router.get("/homologacao/lotes")
def listar_lotes_homologacao(usuario: UsuarioAutenticado = Depends(_admin)):
    _ = usuario
    return supabase.table("cti_crm_homologacao_auditoria").select("*").eq("acao", "ARQUIVAR_HOMOLOGACAO").order("created_at", desc=True).execute().data or []


@router.post("/homologacao/lotes/{lote_id}/restaurar")
def restaurar_lote_homologacao(lote_id: str, dados: RestaurarHomologacaoPayload, usuario: UsuarioAutenticado = Depends(_admin)):
    if _normalizar_confirmacao(dados.confirmacao) != CONFIRMACAO_RESTAURAR:
        raise HTTPException(status_code=422, detail=f"Digite a confirmação: {CONFIRMACAO_RESTAURAR}")
    try:
        resposta = supabase.rpc("cti_restaurar_homologacao_crm", {"p_lote_id": lote_id, "p_usuario_id": usuario.id}).execute().data
    except Exception as erro:
        raise HTTPException(status_code=409, detail=f"Não foi possível restaurar o lote: {erro}") from erro
    return resposta or {"success": True}


@router.post("/{oportunidade_id}/arquivar-teste")
def arquivar_teste(oportunidade_id: str, usuario: UsuarioAutenticado = Depends(_admin)):
    try:
        resposta = supabase.rpc("cti_arquivar_homologacao_crm", {
            "p_oportunidade_ids": [oportunidade_id],
            "p_usuario_id": usuario.id,
            "p_motivo": "Registro criado para teste/homologação",
        }).execute().data
    except Exception as erro:
        raise HTTPException(status_code=409, detail=f"Não foi possível arquivar a oportunidade e seus vínculos: {erro}") from erro
    return resposta or {"success": True}


@router.get("/testes-arquivados")
def listar_testes_arquivados(usuario: UsuarioAutenticado = Depends(_admin)):
    _ = usuario
    return supabase.table("cti_oportunidades_registros").select("*").eq("registro_teste", True).not_.is_("arquivado_em", "null").order("arquivado_em", desc=True).execute().data or []


@router.post("/{oportunidade_id}/restaurar-teste")
def restaurar_teste(oportunidade_id: str, usuario: UsuarioAutenticado = Depends(_admin)):
    registros = supabase.table("cti_oportunidades_registros").select("*").eq("id", oportunidade_id).limit(1).execute().data or []
    if not registros:
        raise HTTPException(status_code=404, detail="Oportunidade arquivada não encontrada.")
    atual = registros[0]
    lote_id = atual.get("lote_arquivamento_id")
    if lote_id:
        return supabase.rpc("cti_restaurar_homologacao_crm", {"p_lote_id": str(lote_id), "p_usuario_id": usuario.id}).execute().data
    if not atual.get("arquivado_em"):
        return {"success": True, "oportunidade": atual, "already_active": True}
    status_restaurado = str(atual.get("status_antes_arquivamento") or "OPORTUNIDADE")
    payload = {"registro_teste": False, "arquivado_em": None, "arquivado_por": None, "motivo_arquivamento": None, "status": status_restaurado, "status_antes_arquivamento": None, "updated_at": _agora()}
    atualizado = supabase.table("cti_oportunidades_registros").update(payload).eq("id", oportunidade_id).execute().data or []
    return {"success": True, "oportunidade": atualizado[0] if atualizado else {**atual, **payload}}
