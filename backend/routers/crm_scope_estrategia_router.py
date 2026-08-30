from __future__ import annotations

import math
from collections import Counter
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers import drilldown_router as drill
from routers import strategic_layers_router as estrategia
from services.anfir_workbook_contract import _ddd_workbook
from services.base_analytics import valor_float
from services.crm_live_projection import carregar_oportunidades_enriquecidas, equipamentos_registro, familias_registro
from services.historical_commercial_source import carregar_historico_comercial
from services.operational_filters import normalizar_ddd, resolver_periodo

router = APIRouter(prefix="/crm-seguro/estrategia", tags=["crm-seguro-estrategia"])

PERFIS_REGIONAIS = {"REPRES_REGIAO_01", "REPRES_REGIAO_02", "INDICADOR_VIENA_SP"}
PERFIS_REPRESENTANTES = {"REPRES_REGIAO_01", "REPRES_REGIAO_02"}
FECHADOS = {"GANHO", "PERDIDO", "CANCELADO", "CANCELADA", "CONCLUIDO", "CONCLUIDA"}
DDD_011_COMPARTILHADO = "011"
SUBREGIAO_011_POR_PERFIL = {
    "REPRES_REGIAO_01": "REGIAO 01",
    "REPRES_REGIAO_02": "REGIAO 02",
}
RESPONSAVEIS_011_POR_PERFIL = {
    "REPRES_REGIAO_01": {"MONICA", "CARLA"},
    "REPRES_REGIAO_02": {"MICHELE"},
}


def _fold(valor: Any) -> str:
    return drill._fold(valor)


def _consolidado(usuario: UsuarioAutenticado) -> bool:
    return usuario.tipo_usuario == "ADMIN_MASTER" or (
        usuario.tipo_usuario == "DIRETOR_VIENA_SP"
        and bool(usuario.permissoes.get("acesso_total"))
    )


def _perfil_regional(usuario: UsuarioAutenticado) -> dict[str, Any]:
    if usuario.tipo_usuario not in PERFIS_REGIONAIS:
        return {"nome": usuario.nome, "ddds": []}
    try:
        dados = (
            supabase.table("cti_users")
            .select("nome,ddds")
            .eq("id", usuario.id)
            .limit(1)
            .execute()
            .data
            or []
        )
    except Exception:
        dados = []
    registro = dados[0] if dados else {}
    ddds = sorted({ddd for valor in (registro.get("ddds") or []) if (ddd := normalizar_ddd(valor))})
    return {"nome": str(registro.get("nome") or usuario.nome), "ddds": ddds}


def _hist_do_usuario(usuario: UsuarioAutenticado, inicio: date | None, fim: date | None) -> list[dict[str, Any]]:
    registros = [
        item for item in carregar_historico_comercial()
        if estrategia._data_no_intervalo(item.get("data"), inicio, fim)
    ]
    if _consolidado(usuario) or usuario.tipo_usuario not in PERFIS_REGIONAIS:
        return registros
    perfil = _perfil_regional(usuario)
    nome = _fold(perfil["nome"])
    primeiro_nome = nome.split(" ", 1)[0] if nome else ""
    return [
        item for item in registros
        if primeiro_nome
        and (
            _fold(item.get("representante_atual")) == nome
            or _fold(item.get("representante_atual")) == primeiro_nome
            or _fold(item.get("representante_atual")).startswith(f"{primeiro_nome} ")
        )
    ]


def _responsavel_anfir(item: dict[str, Any]) -> str:
    for campo in ("responsavel", "vendedor", "consultor"):
        valor = _fold(item.get(campo))
        if valor:
            return valor
    return ""


def _registro_anfir_no_escopo(item: dict[str, Any], usuario: UsuarioAutenticado, permitidos: set[str]) -> bool:
    ddd_item = _ddd_workbook(item)
    if ddd_item not in permitidos:
        return False
    if usuario.tipo_usuario not in PERFIS_REPRESENTANTES or ddd_item != DDD_011_COMPARTILHADO:
        return True

    sub_regiao = _fold(item.get("sub_regiao"))
    sub_regiao_permitida = SUBREGIAO_011_POR_PERFIL.get(usuario.tipo_usuario, "")
    if sub_regiao_permitida and sub_regiao == sub_regiao_permitida:
        return True

    responsavel = _responsavel_anfir(item)
    primeiro_nome = responsavel.split(" ", 1)[0] if responsavel else ""
    return primeiro_nome in RESPONSAVEIS_011_POR_PERFIL.get(usuario.tipo_usuario, set())


def _anfir_do_usuario(
    usuario: UsuarioAutenticado,
    contexto: str,
    periodo: str,
    uf: str | None,
    ddd: str | None,
    inicio: date | None,
    fim: date | None,
):
    registros, inicio_efetivo, fim_efetivo = estrategia._anfir(contexto, periodo, uf, ddd, inicio, fim)
    if _consolidado(usuario) or usuario.tipo_usuario not in PERFIS_REGIONAIS:
        return registros, inicio_efetivo, fim_efetivo
    perfil = _perfil_regional(usuario)
    permitidos = set(perfil["ddds"])
    if not permitidos:
        return [], inicio_efetivo, fim_efetivo
    solicitado = normalizar_ddd(ddd)
    if solicitado and solicitado not in permitidos:
        return [], inicio_efetivo, fim_efetivo
    filtrados = [item for item in registros if _registro_anfir_no_escopo(item, usuario, permitidos)]
    return filtrados, inicio_efetivo, fim_efetivo


def _crm_do_usuario(usuario: UsuarioAutenticado) -> list[dict[str, Any]]:
    registros = carregar_oportunidades_enriquecidas()
    if _consolidado(usuario) or usuario.tipo_usuario not in PERFIS_REGIONAIS:
        return registros
    return [item for item in registros if str(item.get("responsavel_id") or "") == str(usuario.id)]


def _familias(counter: Counter) -> list[dict[str, Any]]:
    return [
        {"nome": estrategia.EQUIPAMENTOS[slug]["nome"], "quantidade_registros": counter.get(slug, 0)}
        for slug in estrategia.EQUIPAMENTOS
    ]


def _metadata_escopo(usuario: UsuarioAutenticado) -> dict[str, Any]:
    if _consolidado(usuario):
        return {"modo": "CONSOLIDADO_GESTAO", "usuario": usuario.nome}
    if usuario.tipo_usuario in PERFIS_REGIONAIS:
        perfil = _perfil_regional(usuario)
        metadata = {"modo": "REGIONAL", "usuario": perfil["nome"], "ddds_autorizados": perfil["ddds"]}
        if usuario.tipo_usuario in PERFIS_REPRESENTANTES and DDD_011_COMPARTILHADO in perfil["ddds"]:
            metadata["sub_regiao_011"] = SUBREGIAO_011_POR_PERFIL.get(usuario.tipo_usuario)
            metadata["regra_011"] = "DDD compartilhado: somente registros atribuídos à região comercial do usuário"
        return metadata
    return {"modo": "PERFIL_ATUAL", "usuario": usuario.nome}


@router.get("/mapa")
def mapa_seguro(
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    anf, inicio_efetivo, fim_efetivo = _anfir_do_usuario(usuario, contexto, periodo, uf, ddd, inicio, fim)
    historico = _hist_do_usuario(usuario, inicio_efetivo, fim_efetivo)
    crm = _crm_do_usuario(usuario)

    familias_anfir = Counter(estrategia._familia_registro_anfir(item) for item in anf)
    familias_hist = Counter(estrategia._familia_historico(item) for item in historico)
    familias_crm: Counter[str] = Counter()
    for item in crm:
        for familia in estrategia._familias_crm(item):
            familias_crm[familia] += 1

    realizado = estrategia._camada_anfir(anf)
    realizado["familias"] = _familias(familias_anfir)
    historico_cam = estrategia._camada_historico(historico)
    historico_cam["familias"] = _familias(familias_hist)
    em_curso = estrategia._camada_crm(crm)
    em_curso["familias"] = _familias(familias_crm)

    return {
        "regra": "CORRELACAO_SEM_FUSAO",
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
            "escopo_usuario": _metadata_escopo(usuario),
        },
        "realizado": realizado,
        "historico_comercial": historico_cam,
        "em_curso": em_curso,
    }


@router.get("/equipamentos/{slug}")
def equipamento_seguro(
    slug: str,
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    config = estrategia.EQUIPAMENTOS.get(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Equipamento não configurado")
    anf_base, inicio_efetivo, fim_efetivo = _anfir_do_usuario(usuario, contexto, periodo, uf, ddd, inicio, fim)
    anf = [item for item in anf_base if estrategia._familia_registro_anfir(item) == slug]
    historico = [item for item in _hist_do_usuario(usuario, inicio_efetivo, fim_efetivo) if estrategia._familia_historico(item) == slug]
    crm = [item for item in _crm_do_usuario(usuario) if slug in estrategia._familias_crm(item)]
    return {
        "slug": slug,
        "nome": config["nome"],
        "regra": "CAMADAS_SEPARADAS_SEM_FUSAO",
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
            "escopo_usuario": _metadata_escopo(usuario),
        },
        "realizado": estrategia._camada_anfir(anf),
        "historico_comercial": estrategia._camada_historico(historico),
        "em_curso": estrategia._camada_crm(crm),
    }


@router.get("/detalhamento/resumo-historico")
def resumo_historico_seguro(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    registros = _hist_do_usuario(usuario, None, None)
    return {
        "total_registros": len(registros),
        "total_unidades": int(sum(drill._numero(item.get("quantidade")) for item in registros)),
        "valor_nominal": round(sum(drill._numero(item.get("valor_total")) for item in registros), 2),
        "abas": drill._ranking_historico(registros, "aba_origem"),
        "anos": drill._ranking_historico(registros, "ano"),
        "canais": drill._ranking_historico(registros, "canal_venda"),
        "representantes": drill._ranking_historico(registros, "representante_atual"),
        "status": drill._ranking_historico(registros, "status"),
        "equipamentos": drill._ranking_historico(registros, "equipamento", 20),
        "implementadoras": drill._ranking_historico(registros, "implementadora", 20),
        "motivos_perda": drill._ranking_historico(registros, "motivo_perda", 20),
    }


@router.get("/detalhamento")
def detalhamento_seguro(
    camada: str,
    campo: str | None = None,
    valor: str | None = None,
    familia: str | None = None,
    contexto: str = "brasil",
    periodo: str = "TODO_HISTORICO",
    uf: str | None = None,
    ddd: str | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    busca: str | None = None,
    ordenar: str | None = None,
    direcao: str = "asc",
    pagina: int = 1,
    limite: int = 50,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    camada = camada.strip().lower()
    if camada not in drill.CAMPOS:
        raise HTTPException(status_code=422, detail="Camada de detalhamento inválida.")
    if campo and campo not in drill.CAMPOS[camada] and campo != "familia":
        raise HTTPException(status_code=422, detail="Campo de detalhamento não suportado para esta camada.")

    if camada == "anfir":
        registros, inicio_efetivo, fim_efetivo = _anfir_do_usuario(usuario, contexto, periodo, uf, ddd, inicio, fim)
        if familia:
            registros = [item for item in registros if estrategia._familia_registro_anfir(item) == familia]
    elif camada == "historico":
        inicio_efetivo, fim_efetivo = resolver_periodo(periodo, inicio, fim)
        registros = _hist_do_usuario(usuario, inicio_efetivo, fim_efetivo)
        if familia:
            registros = [item for item in registros if estrategia._familia_historico(item) == familia]
    else:
        inicio_efetivo, fim_efetivo = inicio, fim
        registros = [item for item in _crm_do_usuario(usuario) if str(item.get("status") or "").upper() not in FECHADOS]
        if familia:
            registros = [item for item in registros if familia in familias_registro(item)]

    if campo == "familia" and valor:
        if camada == "anfir":
            registros = [item for item in registros if estrategia._familia_registro_anfir(item) == valor]
        elif camada == "historico":
            registros = [item for item in registros if estrategia._familia_historico(item) == valor]
        else:
            registros = [item for item in registros if valor in familias_registro(item)]
    elif campo and valor:
        if camada == "anfir":
            registros = drill._filtrar_anfir_semantico(list(registros), campo, valor)
        else:
            registros = [item for item in registros if drill._corresponde(item, drill.CAMPOS[camada][campo], valor)]

    registros = drill._buscar(list(registros), busca)
    registros = drill._ordenar(registros, ordenar, direcao)
    pagina = max(1, pagina)
    limite = max(10, min(limite, 100))
    total = len(registros)
    paginas = max(1, math.ceil(total / limite)) if total else 1
    if pagina > paginas:
        pagina = paginas
    inicio_idx = (pagina - 1) * limite
    fim_idx = inicio_idx + limite

    return {
        "camada": camada,
        "campo": campo,
        "valor": valor,
        "familia": familia,
        "total_registros": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": paginas,
        "metadata": {
            "contexto": contexto,
            "periodo": periodo,
            "uf": uf,
            "ddd": ddd,
            "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None,
            "fim": fim_efetivo.isoformat() if fim_efetivo else None,
            "escopo_usuario": _metadata_escopo(usuario),
        },
        "registros": [drill._projetar(item, camada) for item in registros[inicio_idx:fim_idx]],
    }
