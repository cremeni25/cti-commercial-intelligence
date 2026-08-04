from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase

router = APIRouter(prefix="/master/testes-campo", tags=["MASTER - Testes de Campo"])


class RegistrarTesteCampo(BaseModel):
    campanha: str = Field(min_length=3, max_length=80)
    oportunidade_id: str
    cliente_id: str | None = None
    criado_por: str
    observacao: str = "TESTE DE CAMPO"


class LimparCampanha(BaseModel):
    executado_por: str
    confirmacao: str


def _normalizar_campanha(value: str) -> str:
    campanha = "_".join(value.strip().upper().split())
    if not campanha:
        raise HTTPException(status_code=422, detail="Informe a campanha de teste.")
    return campanha


def _rows(table: str, column: str, values: list[str]) -> list[dict[str, Any]]:
    if not values:
        return []
    return supabase.table(table).select("*").in_(column, values).execute().data or []


def _ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("id")) for row in rows if row.get("id")]


def _mapear_campanha(campanha: str) -> dict[str, Any]:
    registros = (
        supabase.table("cti_testes_campo")
        .select("*")
        .eq("campanha", campanha)
        .eq("status", "ATIVO")
        .execute()
        .data
        or []
    )
    oportunidades = list(dict.fromkeys(str(row.get("oportunidade_id")) for row in registros if row.get("oportunidade_id")))
    clientes = list(dict.fromkeys(str(row.get("cliente_id")) for row in registros if row.get("cliente_id")))
    itens = _rows("cti_oportunidade_itens", "oportunidade_id", oportunidades)
    propostas = _rows("cti_propostas", "oportunidade_id", oportunidades)
    proposta_ids = _ids(propostas)
    aceites = _rows("cti_proposta_aceites", "proposta_id", proposta_ids)
    pedidos_por_proposta = _rows("cti_pedidos", "proposta_id", proposta_ids)
    pedidos_por_oportunidade = _rows("cti_pedidos", "oportunidade_id", oportunidades)
    pedidos_por_id = {str(row.get("id")): row for row in [*pedidos_por_proposta, *pedidos_por_oportunidade] if row.get("id")}
    pedidos = list(pedidos_por_id.values())
    pedido_ids = _ids(pedidos)
    envios = _rows("cti_envios_carrier", "pedido_id", pedido_ids)
    historico = _rows("cti_oportunidade_historico", "oportunidade_id", oportunidades)
    pipeline = _rows("cti_pipeline", "oportunidade_id", oportunidades)
    return {
        "campanha": campanha,
        "registros": registros,
        "oportunidades": oportunidades,
        "clientes": clientes,
        "itens": itens,
        "propostas": propostas,
        "aceites": aceites,
        "pedidos": pedidos,
        "envios": envios,
        "historico": historico,
        "pipeline": pipeline,
    }


@router.post("/registrar")
def registrar_teste_campo(dados: RegistrarTesteCampo):
    campanha = _normalizar_campanha(dados.campanha)
    oportunidade = (
        supabase.table("cti_oportunidades")
        .select("id,cliente_id,titulo,descricao")
        .eq("id", dados.oportunidade_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not oportunidade:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")
    registro = oportunidade[0]
    payload = {
        "campanha": campanha,
        "oportunidade_id": dados.oportunidade_id,
        "cliente_id": dados.cliente_id or registro.get("cliente_id"),
        "criado_por": dados.criado_por,
        "observacao": "TESTE DE CAMPO",
        "status": "ATIVO",
    }
    existente = (
        supabase.table("cti_testes_campo")
        .select("*")
        .eq("campanha", campanha)
        .eq("oportunidade_id", dados.oportunidade_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if existente:
        return {"ok": True, "already_registered": True, "registro": existente[0]}
    criado = supabase.table("cti_testes_campo").insert(payload).execute().data or []
    supabase.table("cti_oportunidade_historico").insert({
        "oportunidade_id": dados.oportunidade_id,
        "tipo": "TESTE_CAMPO",
        "descricao": "TESTE DE CAMPO",
        "usuario_id": dados.criado_por,
        "payload": {"teste_campo": True, "campanha": campanha},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"ok": True, "already_registered": False, "registro": criado[0] if criado else payload}


@router.get("")
def listar_campanhas():
    rows = supabase.table("cti_testes_campo").select("*").order("created_at", desc=True).execute().data or []
    campanhas: dict[str, dict[str, Any]] = {}
    for row in rows:
        nome = str(row.get("campanha") or "SEM_CAMPANHA")
        item = campanhas.setdefault(nome, {"campanha": nome, "ativos": 0, "encerrados": 0, "created_at": row.get("created_at")})
        if str(row.get("status")) == "ATIVO":
            item["ativos"] += 1
        else:
            item["encerrados"] += 1
    return list(campanhas.values())


@router.get("/{campanha}/previsualizar")
def previsualizar_campanha(campanha: str):
    mapa = _mapear_campanha(_normalizar_campanha(campanha))
    return {
        "campanha": mapa["campanha"],
        "contagens": {
            "oportunidades": len(mapa["oportunidades"]),
            "itens": len(mapa["itens"]),
            "propostas": len(mapa["propostas"]),
            "aceites": len(mapa["aceites"]),
            "pedidos": len(mapa["pedidos"]),
            "envios": len(mapa["envios"]),
            "historico": len(mapa["historico"]),
            "pipeline": len(mapa["pipeline"]),
            "clientes_candidatos": len(mapa["clientes"]),
        },
        "ids": {
            "oportunidades": mapa["oportunidades"],
            "propostas": _ids(mapa["propostas"]),
            "pedidos": _ids(mapa["pedidos"]),
        },
        "confirmacao_exigida": f"EXCLUIR {mapa['campanha']}",
    }


@router.post("/{campanha}/limpar")
def limpar_campanha(campanha: str, dados: LimparCampanha):
    nome = _normalizar_campanha(campanha)
    esperado = f"EXCLUIR {nome}"
    if dados.confirmacao.strip().upper() != esperado:
        raise HTTPException(status_code=422, detail=f"Confirmação inválida. Digite exatamente: {esperado}")
    mapa = _mapear_campanha(nome)
    if not mapa["oportunidades"]:
        raise HTTPException(status_code=404, detail="Nenhuma oportunidade ativa registrada nesta campanha.")

    ids_relatorio = {
        "oportunidades": mapa["oportunidades"],
        "itens": _ids(mapa["itens"]),
        "propostas": _ids(mapa["propostas"]),
        "aceites": _ids(mapa["aceites"]),
        "pedidos": _ids(mapa["pedidos"]),
        "envios": _ids(mapa["envios"]),
        "historico": _ids(mapa["historico"]),
        "pipeline": _ids(mapa["pipeline"]),
    }
    contagens = {key: len(value) for key, value in ids_relatorio.items()}
    digest = hashlib.sha256(json.dumps(ids_relatorio, sort_keys=True).encode("utf-8")).hexdigest()

    for table, ids in (
        ("cti_envios_carrier", ids_relatorio["envios"]),
        ("cti_pedidos", ids_relatorio["pedidos"]),
        ("cti_proposta_aceites", ids_relatorio["aceites"]),
        ("cti_propostas", ids_relatorio["propostas"]),
        ("cti_pipeline", ids_relatorio["pipeline"]),
        ("cti_oportunidade_historico", ids_relatorio["historico"]),
        ("cti_oportunidade_itens", ids_relatorio["itens"]),
        ("cti_oportunidades", ids_relatorio["oportunidades"]),
    ):
        if ids:
            supabase.table(table).delete().in_("id", ids).execute()

    agora = datetime.now(timezone.utc).isoformat()
    supabase.table("cti_testes_campo").update({
        "status": "EXCLUIDO",
        "encerrado_em": agora,
        "encerrado_por": dados.executado_por,
    }).eq("campanha", nome).eq("status", "ATIVO").execute()
    auditoria = {
        "campanha": nome,
        "executado_por": dados.executado_por,
        "executado_em": agora,
        "contagens": contagens,
        "ids_processados": ids_relatorio,
        "hash_relatorio": digest,
        "observacao": "Limpeza controlada de TESTE DE CAMPO",
    }
    supabase.table("cti_testes_campo_auditoria").insert(auditoria).execute()
    return {"ok": True, "campanha": nome, "contagens": contagens, "hash_relatorio": digest}
