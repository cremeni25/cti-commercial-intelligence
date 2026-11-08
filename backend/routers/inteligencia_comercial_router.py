"""Endpoints do Agente de Inteligência Comercial e do registro de módulos.

Somente leitura. O escopo segue a regra oficial do CRM seguro: Master e
Diretor com acesso total enxergam a equipe (e podem filtrar um
responsável); todos os demais perfis enxergam apenas a própria carteira.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.modulos_plataforma import modulos_para_usuario
from services.catalogo_vitrine import carregar_vitrine
from services.inteligencia_comercial import gerar_briefing, provedores_registrados
from services.inteligencia_comercial.briefing import hoje_operacional
from services.inteligencia_comercial.feedback import (
    MOTIVOS,
    FeedbackIndisponivel,
    carregar_feedback,
    registrar_feedback,
    resumo_aprendizado,
)

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


class AjusteSinalRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=60)
    entidade_tipo: str = Field(min_length=1, max_length=30)
    entidade_id: str = Field(min_length=1, max_length=80)
    decisao: Literal["NAO_SE_APLICA", "ADIAR"]
    motivo: str = Field(default="OUTRO", max_length=40)
    observacao: str | None = Field(default=None, max_length=500)
    adiar_ate: date | None = None


def _sinal_no_escopo(briefing: dict, ajuste: AjusteSinalRequest) -> bool:
    for item in briefing.get("prioridades", []):
        if item.get("entidade_tipo") == ajuste.entidade_tipo and str(item.get("entidade_id")) == ajuste.entidade_id:
            return ajuste.codigo == item.get("codigo") or ajuste.codigo in (item.get("sinais_relacionados") or [])
    return False


@router.post("/inteligencia/feedback", status_code=201)
def ajustar_sinal(ajuste: AjusteSinalRequest, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Registra "não se aplica" ou "adiar" para um sinal que o usuário enxerga."""
    if ajuste.motivo not in MOTIVOS:
        raise HTTPException(status_code=422, detail="Motivo não reconhecido.")
    hoje = hoje_operacional()
    if ajuste.adiar_ate and ajuste.adiar_ate <= hoje:
        raise HTTPException(status_code=422, detail="Escolha uma data futura para adiar.")
    briefing = gerar_briefing(usuario_id=str(usuario.id), consolidado=_visao_consolidada(usuario), limite_prioridades=500)
    if not _sinal_no_escopo(briefing, ajuste):
        raise HTTPException(status_code=404, detail="Este alerta não está mais ativo na sua carteira.")
    try:
        registro = registrar_feedback(
            usuario_id=str(usuario.id), codigo=ajuste.codigo, entidade_tipo=ajuste.entidade_tipo,
            entidade_id=ajuste.entidade_id, decisao=ajuste.decisao, motivo=ajuste.motivo,
            observacao=ajuste.observacao, hoje=hoje, adiar_ate=ajuste.adiar_ate,
        )
    except FeedbackIndisponivel:
        raise HTTPException(status_code=503, detail="O ajuste de alertas ainda está sendo ativado no banco. Use agendar ou concluir enquanto isso.")
    return {"registrado": True, "suprimir_ate": registro.get("suprimir_ate")}


@router.get("/inteligencia/aprendizado")
def aprendizado_agente(dias: int = Query(default=90, ge=7, le=365), usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Quais alertas a equipe mais dispensa, e por quê. Somente gestão."""
    if not _visao_consolidada(usuario):
        raise HTTPException(status_code=403, detail="Leitura de calibração disponível somente para a gestão.")
    return resumo_aprendizado(carregar_feedback(desde=hoje_operacional() - timedelta(days=dias)))


def _permissao(usuario: UsuarioAutenticado, *chaves: str) -> bool:
    return any((usuario.permissoes or {}).get(chave) is True for chave in chaves)


@router.get("/catalogo/vitrine")
def vitrine_catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """Catálogo para consulta da equipe: equipamentos, materiais e (se permitido) preço de tabela."""
    gestao = _visao_consolidada(usuario)
    if not (gestao or _permissao(usuario, "oportunidades_visualizar", "oportunidades_editar", "propostas_visualizar", "propostas_emitir")):
        raise HTTPException(status_code=403, detail="Catálogo disponível para a equipe comercial.")
    ver_precos = gestao or _permissao(usuario, "propostas_visualizar", "propostas_emitir")
    return carregar_vitrine(ver_precos=ver_precos, hoje=hoje_operacional())


TAMANHO_MAXIMO_MATERIAL = 15 * 1024 * 1024


@router.post("/catalogo/materiais", status_code=201)
async def anexar_material_interno(
    titulo: str = Form(..., min_length=2, max_length=120),
    arquivo: UploadFile = File(...),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Master anexa um PDF interno ao Catálogo (fica no cofre privado, nunca público)."""
    import re
    import unicodedata
    from datetime import datetime, timezone

    from services import cofre_agente as cofre
    from services.catalogo_vitrine import INDICE_MATERIAIS_INTERNOS, PASTA_MATERIAIS_INTERNOS

    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente o Master anexa materiais ao Catálogo.")
    conteudo = await arquivo.read(TAMANHO_MAXIMO_MATERIAL + 1)
    if len(conteudo) > TAMANHO_MAXIMO_MATERIAL:
        raise HTTPException(status_code=413, detail="Arquivo acima de 15 MB.")
    if not conteudo.startswith(b"%PDF"):
        raise HTTPException(status_code=422, detail="Envie um arquivo PDF.")
    base = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    nome = (re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "material")[:60] + ".pdf"
    try:
        cofre.gravar_binario(cofre.caminho(PASTA_MATERIAIS_INTERNOS, nome), conteudo, "application/pdf")
        indice = [i for i in (cofre.ler(INDICE_MATERIAIS_INTERNOS, []) or []) if isinstance(i, dict) and i.get("arquivo") != nome]
        indice.append({"titulo": titulo.strip(), "arquivo": nome, "tipo": "catalogo", "enviado_em": datetime.now(timezone.utc).isoformat(), "enviado_por": str(usuario.id)})
        cofre.gravar(INDICE_MATERIAIS_INTERNOS, indice)
    except cofre.CofreIndisponivel:
        raise HTTPException(status_code=503, detail="Armazenamento indisponível no momento. Tente novamente.")
    return {"titulo": titulo.strip(), "arquivo": nome}


@router.get("/planilhas-comerciais/resumo")
def resumo_planilhas_comerciais(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    """O que o CTI já leu do funil e das NEGOCIAÇÕES. Somente gestão."""
    if not _visao_consolidada(usuario):
        raise HTTPException(status_code=403, detail="Resumo das planilhas disponível somente para a gestão.")
    from services.planilhas_comerciais import resumo

    return resumo()


LIMITE_PLANILHA = 25 * 1024 * 1024


def _planilha(arquivo: UploadFile | None, rotulo: str) -> tuple[str, bytes] | None:
    if arquivo is None or not arquivo.filename:
        return None
    if not arquivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=415, detail=f"{rotulo}: envie o arquivo do Excel (.xlsx).")
    conteudo = arquivo.file.read(LIMITE_PLANILHA + 1)
    if not conteudo:
        raise HTTPException(status_code=400, detail=f"{rotulo}: arquivo vazio.")
    if len(conteudo) > LIMITE_PLANILHA:
        raise HTTPException(status_code=413, detail=f"{rotulo}: arquivo acima de 25 MB.")
    return arquivo.filename, conteudo


@router.post("/planilhas-comerciais/carga")
def carregar_planilhas_comerciais(
    funil: UploadFile | None = File(default=None),
    negociacoes: UploadFile | None = File(default=None),
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    """Master envia o funil e/ou as NEGOCIAÇÕES; o CTI lê e guarda no cofre privado."""
    if usuario.tipo_usuario != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente o Master atualiza as planilhas comerciais.")
    from services.cofre_agente import CofreIndisponivel
    from zipfile import BadZipFile

    from services.planilhas_comerciais import atualizar_pacote

    parte_funil = _planilha(funil, "Funil de vendas")
    parte_neg = _planilha(negociacoes, "NEGOCIAÇÕES")
    if not parte_funil and not parte_neg:
        raise HTTPException(status_code=400, detail="Envie ao menos uma planilha.")
    try:
        return atualizar_pacote(parte_funil, parte_neg, str(usuario.id))
    except CofreIndisponivel as erro:
        raise HTTPException(status_code=503, detail="Cofre do agente indisponível; tente de novo em instantes.") from erro
    except BadZipFile as erro:
        raise HTTPException(status_code=422, detail="O arquivo não é uma planilha do Excel válida.") from erro
    except (ValueError, KeyError) as erro:
        raise HTTPException(status_code=422, detail=f"Planilha fora do formato esperado: {erro}") from erro


chave_router = APIRouter(tags=["Ingestão cifrada"])


@chave_router.get("/ingestao-cifrada/chave-publica")
def chave_publica_ingestao():
    """Chave pública para cifrar cargas que passam pelo repositório público.

    Só serve para CIFRAR; abrir exige a chave privada, que nunca sai do cofre.
    """
    from services.cofre_agente import CofreIndisponivel
    from services.cofre_cifrado import ALG, chave_publica_b64

    try:
        return {"alg": ALG, "chave_publica": chave_publica_b64()}
    except CofreIndisponivel as erro:
        raise HTTPException(status_code=503, detail="Cofre do agente indisponível no momento.") from erro
