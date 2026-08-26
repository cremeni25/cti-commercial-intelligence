from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase

router = APIRouter(prefix="/crm", tags=["CRM - Governança de atividades"])


class AtividadeAdminUpdate(BaseModel):
    administrador_id: str
    cliente_id: Optional[str] = None
    oportunidade_id: Optional[str] = None
    tipo: Optional[str] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data: Optional[str] = None
    horario: Optional[str] = None
    status: Optional[str] = None


class AtividadeArquivar(BaseModel):
    administrador_id: str
    motivo: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _master(usuario_id: str) -> dict[str, Any]:
    resultado = (
        supabase.table("cti_users")
        .select("id,nome,email,tipo_usuario")
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=403, detail="Usuário administrativo não reconhecido.")
    usuario = resultado.data[0]
    if str(usuario.get("tipo_usuario") or "").upper() != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Ação permitida somente ao ADMIN_MASTER.")
    return usuario


def _atividade(atividade_id: str) -> dict[str, Any]:
    resultado = (
        supabase.table("cti_atividades")
        .select("*")
        .eq("id", atividade_id)
        .limit(1)
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    return resultado.data[0]


def _nomes_clientes(registros: list[dict[str, Any]]) -> dict[str, str]:
    ids = sorted({str(item.get("cliente_id")) for item in registros if item.get("cliente_id")})
    if not ids:
        return {}

    nomes: dict[str, str] = {}
    try:
        operacionais = supabase.table("clientes").select("id,nome").in_("id", ids).execute().data or []
        for item in operacionais:
            if item.get("id") and item.get("nome"):
                nomes[str(item["id"])] = str(item["nome"])
    except Exception:
        pass

    faltantes = [item for item in ids if item not in nomes]
    if faltantes:
        try:
            consolidados = supabase.table("cti_clientes").select("id,cliente").in_("id", faltantes).execute().data or []
            for item in consolidados:
                if item.get("id") and item.get("cliente"):
                    nomes[str(item["id"])] = str(item["cliente"])
        except Exception:
            pass
    return nomes


def _enriquecer(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nomes = _nomes_clientes(registros)
    saida: list[dict[str, Any]] = []
    for item in registros:
        registro = dict(item)
        cliente_id = str(registro.get("cliente_id") or "")
        registro["cliente_nome"] = nomes.get(cliente_id, "")
        saida.append(registro)
    return saida


def _auditar(atividade_id: str, acao: str, usuario_id: str, antes: dict[str, Any], depois: dict[str, Any], motivo: Optional[str] = None) -> None:
    supabase.table("cti_atividades_auditoria").insert({
        "atividade_id": atividade_id,
        "acao": acao,
        "usuario_id": usuario_id,
        "antes": antes,
        "depois": depois,
        "motivo": motivo,
        "created_at": _now(),
    }).execute()


@router.get("/atividades")
def listar_atividades_operacionais():
    registros = (
        supabase.table("cti_atividades")
        .select("*")
        .is_("arquivado_em", "null")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return _enriquecer(registros)


@router.get("/atividades/arquivadas")
def listar_atividades_arquivadas(usuario_id: str):
    _master(usuario_id)
    registros = (
        supabase.table("cti_atividades")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    arquivadas = [item for item in registros if item.get("arquivado_em")]
    return _enriquecer(arquivadas)


@router.put("/atividades/{atividade_id}/administrar")
def administrar_atividade(atividade_id: str, alteracao: AtividadeAdminUpdate):
    _master(alteracao.administrador_id)
    anterior = _atividade(atividade_id)
    if anterior.get("arquivado_em"):
        raise HTTPException(status_code=409, detail="Atividade arquivada não pode ser alterada operacionalmente.")

    campos = ["cliente_id", "oportunidade_id", "tipo", "titulo", "descricao", "data", "horario", "status"]
    payload = {
        campo: getattr(alteracao, campo)
        for campo in campos
        if getattr(alteracao, campo) is not None
    }
    if not payload:
        return _enriquecer([anterior])[0]

    payload["updated_at"] = _now()
    resultado = supabase.table("cti_atividades").update(payload).eq("id", atividade_id).execute()
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    atualizado = resultado.data[0]
    _auditar(atividade_id, "EDICAO_ADMIN_MASTER", alteracao.administrador_id, anterior, atualizado)
    return _enriquecer([atualizado])[0]


@router.put("/atividades/{atividade_id}/arquivar")
def arquivar_atividade(atividade_id: str, comando: AtividadeArquivar):
    _master(comando.administrador_id)
    motivo = comando.motivo.strip()
    if len(motivo) < 5:
        raise HTTPException(status_code=422, detail="Informe o motivo do arquivamento com pelo menos 5 caracteres.")

    anterior = _atividade(atividade_id)
    if anterior.get("arquivado_em"):
        return _enriquecer([anterior])[0]

    payload = {
        "arquivado_em": _now(),
        "arquivado_por": comando.administrador_id,
        "motivo_arquivamento": motivo,
        "updated_at": _now(),
    }
    resultado = supabase.table("cti_atividades").update(payload).eq("id", atividade_id).execute()
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    atualizado = resultado.data[0]
    _auditar(atividade_id, "ARQUIVAMENTO_ADMIN_MASTER", comando.administrador_id, anterior, atualizado, motivo)
    return _enriquecer([atualizado])[0]


@router.get("/dashboard")
def dashboard_crm_operacional():
    def contar(tabela: str, somente_ativas: bool = False) -> int:
        consulta = supabase.table(tabela).select("id", count="exact").limit(1)
        if somente_ativas:
            consulta = consulta.is_("arquivado_em", "null")
        resposta = consulta.execute()
        return int(resposta.count or 0)

    return {
        "oportunidades": contar("cti_oportunidades"),
        "propostas": contar("cti_propostas"),
        "pedidos": contar("cti_pedidos"),
        "atividades": contar("cti_atividades", somente_ativas=True),
        "contexto": {
            "origem": "CRM operacional",
            "periodo": "Registros operacionais ativos",
            "significado": "Atividades arquivadas administrativamente permanecem auditáveis, mas não contam na operação.",
            "criterio_calculo": "Contagem operacional exclui cti_atividades.arquivado_em preenchido.",
            "finalidade_operacional": "Evitar que correções e lançamentos indevidos inflem os indicadores comerciais.",
        },
    }
