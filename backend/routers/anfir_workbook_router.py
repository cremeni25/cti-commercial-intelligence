from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.crm_scope_estrategia_router import (
    _consolidado,
    _metadata_escopo,
    _perfil_regional,
    _registro_anfir_no_escopo,
)
from services.anfir_competitive_classification_store import remover_classificacao, salvar_classificacao
from services.anfir_competitive_intelligence import consolidar_competitividade_anfir_2026
from services.anfir_market_scope import particionar_mercado_disputavel
from services.anfir_read_cache import fonte_anfir
from services.anfir_workbook_contract import consolidar_workbook_anfir_2026
from services.commercial_client_scope import filtrar_carteira_exata_responsavel, filtrar_por_responsabilidade_cliente
from services.operational_filters import filtrar_registros


router = APIRouter()


class ClassificacaoConcorrenteInput(BaseModel):
    fabricante: str | None = None
    observacao: str | None = None


def _usuario_alvo(responsavel_id: str, solicitante: UsuarioAutenticado) -> UsuarioAutenticado:
    if not _consolidado(solicitante):
        raise HTTPException(status_code=403, detail="Filtro por responsável disponível somente para usuários Master.")
    dados = (
        supabase.table("cti_users")
        .select("id,auth_id,email,nome,tipo_usuario,ativo")
        .eq("id", responsavel_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not dados or dados[0].get("ativo") is False:
        raise HTTPException(status_code=422, detail="Responsável comercial inválido ou inativo.")
    item = dados[0]
    return UsuarioAutenticado(
        id=str(item.get("id") or responsavel_id),
        auth_id=str(item.get("auth_id") or item.get("id") or responsavel_id),
        email=str(item.get("email") or ""),
        nome=str(item.get("nome") or "Responsável"),
        tipo_usuario=str(item.get("tipo_usuario") or "USUARIO_CTI"),
        permissoes={},
    )


def _registros_2026(responsavel_id: str | None, usuario: UsuarioAutenticado):
    """Base ANFIR bruta Viena SP/2026 com o mesmo escopo canônico do Mapa Comercial.

    Sem responsável selecionado, Master/Direção preserva a base bruta para a auditoria
    597 -> exclusões -> Mercado Real. Quando existe responsável, ou quando o próprio usuário
    regional acessa a tela, a carteira é resolvida pela mesma identidade comercial canônica
    usada em ANFIR, Histórico/Funil e CRM.
    """
    usuario_efetivo = _usuario_alvo(responsavel_id, usuario) if responsavel_id else usuario
    inicio = date(2026, 1, 1)
    fim = date(2026, 12, 31)
    registros = filtrar_registros(
        fonte_anfir(),
        contexto="viena-sp",
        uf=None,
        ddd=None,
        inicio=inicio,
        fim=fim,
    )

    if responsavel_id or not _consolidado(usuario_efetivo):
        registros = filtrar_carteira_exata_responsavel(
            list(registros),
            str(usuario_efetivo.id),
            usuario_efetivo.nome,
        )

    return list(registros), usuario_efetivo


def _metadata_comercial(responsavel_id: str | None, usuario: UsuarioAutenticado, usuario_efetivo: UsuarioAutenticado) -> dict:
    if responsavel_id:
        return _metadata_escopo(usuario_efetivo)
    if _consolidado(usuario):
        return {"modo": "TODA_EQUIPE", "usuario": "Toda a equipe comercial"}
    return _metadata_escopo(usuario)


def _fabricantes_ativos() -> list[str]:
    dados = supabase.table("cti_fabricantes").select("nome,ativo").eq("ativo", True).execute().data or []
    return sorted({str(item.get("nome") or "").strip().upper() for item in dados if str(item.get("nome") or "").strip()})


def _classificacoes_cti() -> dict[str, str]:
    try:
        dados = (
            supabase.table("cti_anfir_concorrente_classificacao")
            .select("anf_ir_id,fabricante_cti")
            .execute()
            .data
            or []
        )
    except Exception:
        return {}
    return {
        str(item.get("anf_ir_id")): str(item.get("fabricante_cti") or "").strip().upper()
        for item in dados
        if item.get("anf_ir_id") and str(item.get("fabricante_cti") or "").strip()
    }


def _normalizar_status(valor: object) -> str:
    texto = str(valor or "").strip().upper()
    substituicoes = str.maketrans("ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ", "AAAAAEEEEIIIIOOOOOUUUUC")
    return texto.translate(substituicoes).replace(" ", "")


@router.get("/analytics/anfir-workbook-2026")
def anfif_workbook_2026(
    responsavel_id: str | None = Query(default=None),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Contrato funcional e seguro da auditoria ANFIR Carrier/JOV 2026."""
    registros, usuario_efetivo = _registros_2026(responsavel_id, usuario)
    disputavel, _, resumo_mercado = particionar_mercado_disputavel(registros)
    payload = consolidar_workbook_anfir_2026(disputavel)
    payload["mercado_viena"] = resumo_mercado
    metadata = payload.setdefault("metadata", {})
    metadata["escopo_usuario"] = _metadata_comercial(responsavel_id, usuario, usuario_efetivo)
    metadata["filtro_responsavel_id"] = responsavel_id
    metadata["filtro_aplicado_por_master"] = bool(responsavel_id)
    metadata["denominador_comercial"] = "MERCADO_DISPUTAVEL_VIENA"
    metadata["regra_escopo"] = "CARTEIRA_COMERCIAL_CANONICA"
    return payload


@router.get("/analytics/anfir-competitividade-2026")
def anfir_competitividade_2026(
    responsavel_id: str | None = Query(default=None),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Inteligência competitiva por fabricante, segmento e mês, respeitando o mesmo escopo canônico do Mapa."""
    registros, usuario_efetivo = _registros_2026(responsavel_id, usuario)
    disputavel, _, resumo_mercado = particionar_mercado_disputavel(registros)
    payload = consolidar_competitividade_anfir_2026(disputavel, _fabricantes_ativos(), _classificacoes_cti())
    metadata = payload.setdefault("metadata", {})
    metadata["escopo_usuario"] = _metadata_comercial(responsavel_id, usuario, usuario_efetivo)
    metadata["filtro_responsavel_id"] = responsavel_id
    metadata["filtro_aplicado_por_master"] = bool(responsavel_id)
    metadata["edicao_classificacao_cti"] = bool(_consolidado(usuario))
    metadata["denominador_comercial"] = "MERCADO_DISPUTAVEL_VIENA"
    metadata["mercado_viena"] = resumo_mercado
    metadata["regra_escopo"] = "CARTEIRA_COMERCIAL_CANONICA"
    return payload


@router.patch("/analytics/anfir-competitividade-2026/registros/{registro_id}/fabricante")
def classificar_fabricante_concorrente(
    registro_id: str,
    entrada: ClassificacaoConcorrenteInput,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Classifica a marca concorrente em camada CTI sem alterar o registro bruto Carrier/JOV."""
    if not _consolidado(usuario):
        raise HTTPException(status_code=403, detail="Somente usuários Master podem alterar a classificação competitiva CTI.")

    registros, _ = _registros_2026(None, usuario)
    registros, _, _ = particionar_mercado_disputavel(registros)
    registro = next((item for item in registros if str(item.get("id") or "") == registro_id), None)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro ANFIR não encontrado no escopo Viena SP 2026.")

    fabricante = str(entrada.fabricante or "").strip().upper()
    if not fabricante:
        remover_classificacao(registro_id)
        return {"ok": True, "registro_id": registro_id, "fabricante_cti": None, "acao": "CLASSIFICACAO_REMOVIDA"}

    fabricantes = set(_fabricantes_ativos())
    if fabricante not in fabricantes:
        raise HTTPException(status_code=422, detail="Fabricante não pertence à taxonomia ativa do CTI.")
    if fabricante == "CARRIER":
        raise HTTPException(status_code=422, detail="A classificação complementar é exclusiva para concorrentes.")

    status_fonte = _normalizar_status(registro.get("status"))
    if status_fonte in {"CARRIER", "TK"}:
        raise HTTPException(status_code=422, detail="CARRIER e TK são categorias oficiais da fonte e não podem ser reclassificadas nesta função.")
    if status_fonte == "NACIONAL" and fabricante == "THERMOKING":
        raise HTTPException(status_code=422, detail="Um registro oficial NACIONAL não pode ser reclassificado como Thermo King.")

    permitido = status_fonte in {"NACIONAL", "USADOCONCORRENTE", "", "NAOCLASSIFICADO"}
    if not permitido:
        raise HTTPException(status_code=422, detail="Este status Carrier/JOV não aceita classificação complementar de fabricante.")

    salvar_classificacao(
        registro_id,
        fabricante,
        str(entrada.observacao or "").strip() or None,
        str(usuario.id),
    )
    return {
        "ok": True,
        "registro_id": registro_id,
        "fabricante_cti": fabricante,
        "status_fonte": registro.get("status"),
        "fonte_preservada": True,
    }
