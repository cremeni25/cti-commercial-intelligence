from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers import clientes_oportunidade_router as legado
from routers.clientes_oportunidade_router import ClienteOportunidadeCreate

router = APIRouter(prefix="/crm-seguro", tags=["crm-seguro-cliente-referencia"])

PERFIS_ESCOPO_PROPRIO = {
    "REPRES_REGIAO_01",
    "REPRES_REGIAO_02",
    "INDICADOR_VIENA_SP",
}


def _usa_escopo_proprio(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario in PERFIS_ESCOPO_PROPRIO


def _cliente_operacional_por_id(cliente_id: str) -> dict | None:
    if not cliente_id:
        return None
    registros = supabase.table("clientes").select("*").eq("id", cliente_id).limit(1).execute().data or []
    return registros[0] if registros else None


def _resolver_cliente(dados: ClienteOportunidadeCreate) -> tuple[dict, dict]:
    cliente_id = str(dados.cliente.id or "").strip()
    existente = _cliente_operacional_por_id(cliente_id)
    if existente:
        return existente, {
            "mode": "referencia_existente",
            "removed_fields": (),
            "detail": "Cadastro existente apenas referenciado; nenhuma edição cadastral implícita foi executada.",
        }
    return legado._criar_ou_atualizar_cliente(dados.cliente)


def _criar_oportunidade(dados: ClienteOportunidadeCreate, cliente: dict, compat_cliente: dict) -> dict:
    cliente_id = str(cliente.get("id") or "")
    if not cliente_id:
        raise HTTPException(status_code=500, detail="Cliente resolvido sem identificador.")

    oportunidade = dados.oportunidade
    contexto = legado._contexto_comercial(dados)
    probabilidade = legado._normalizar_probabilidade(oportunidade.probabilidade)
    valor_estimado = legado._normalizar_valor(oportunidade.valor_estimado)
    descricao = legado._descricao_com_contexto(oportunidade.descricao, contexto)
    titulo = legado._titulo_canonico(oportunidade.titulo, oportunidade.descricao)
    payload = {
        "cliente_id": cliente_id,
        "responsavel_id": oportunidade.responsavel_id,
        "titulo": titulo,
        "descricao": descricao,
        "origem": "CRM_APP",
        "status": "OPORTUNIDADE",
        "valor_estimado": valor_estimado,
        "probabilidade": probabilidade,
        "data_fechamento_prevista": oportunidade.data_fechamento_prevista,
    }
    criado, compat_oportunidade = legado.insert_schema_compatible(
        legado.supabase,
        "cti_oportunidades",
        payload,
        protected_fields={"cliente_id", "titulo"},
    )
    if not criado:
        raise HTTPException(status_code=500, detail="A oportunidade não retornou registro após a inserção.")

    oportunidade_criada = criado[0]
    oportunidade_id = oportunidade_criada.get("id")
    avisos: list[str] = []
    agora = datetime.now(timezone.utc)
    legado._registrar_auxiliar(
        "cti_pipeline",
        {
            "oportunidade_id": oportunidade_id,
            "etapa_anterior": None,
            "nova_etapa": "OPORTUNIDADE",
            "etapa": "OPORTUNIDADE",
            "usuario_id": oportunidade.responsavel_id,
            "observacao": "Primeira movimentação automática da oportunidade.",
            "data": agora.date().isoformat(),
            "hora": agora.time().replace(microsecond=0).isoformat(),
        },
        avisos,
        "pipeline",
    )
    legado._registrar_auxiliar(
        "cti_oportunidade_historico",
        {
            "oportunidade_id": oportunidade_id,
            "tipo": "OPORTUNIDADE",
            "descricao": "Oportunidade criada pelo App CRM.",
            "usuario_id": oportunidade.responsavel_id,
            "payload": {
                "oportunidade": oportunidade_criada,
                "contexto_comercial": contexto,
                "backend_version": legado.CRM_APP_BACKEND_VERSION,
            },
            "created_at": legado._now(),
        },
        avisos,
        "histórico",
    )
    return {
        "cliente": cliente,
        "oportunidade": oportunidade_criada,
        "contexto_comercial": contexto,
        "normalizacao": {"valor_estimado": valor_estimado, "probabilidade": probabilidade},
        "compatibilidade": {"cliente": compat_cliente, "oportunidade": compat_oportunidade},
        "backend_version": legado.CRM_APP_BACKEND_VERSION,
        "avisos": avisos,
    }


@router.post("/cliente-oportunidade")
def criar_cliente_oportunidade_por_referencia(
    dados: ClienteOportunidadeCreate,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    if _usa_escopo_proprio(usuario):
        oportunidade = dados.oportunidade.model_copy(update={"responsavel_id": str(usuario.id)})
        dados = dados.model_copy(update={"oportunidade": oportunidade})
    cliente, compat_cliente = _resolver_cliente(dados)
    return _criar_oportunidade(dados, cliente, compat_cliente)
