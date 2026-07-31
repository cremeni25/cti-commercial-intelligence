from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase

router = APIRouter(prefix="/crm-visao", tags=["crm-visao"])
ETAPAS = ["OPORTUNIDADE", "ATIVIDADES", "PROPOSTA", "NEGOCIACAO", "PEDIDO", "GANHO", "PERDIDO"]


def _lista(tabela: str, ordem: str = "created_at") -> list[dict[str, Any]]:
    return supabase.table(tabela).select("*").order(ordem, desc=True).execute().data or []


def _nome_registro_cliente(cliente: dict[str, Any] | None) -> str:
    if not cliente:
        return ""
    return str(
        cliente.get("nome")
        or cliente.get("razao_social")
        or cliente.get("nome_fantasia")
        or cliente.get("empresa")
        or ""
    ).strip()


def _clientes_por_id() -> dict[str, str]:
    resultado: dict[str, str] = {}
    for cliente in _lista("clientes"):
        identificador = str(cliente.get("id") or "").strip()
        nome = _nome_registro_cliente(cliente)
        if identificador and nome:
            resultado[identificador] = nome
    return resultado


def _cliente_por_id(cliente_id: str) -> dict[str, Any] | None:
    if not cliente_id:
        return None
    registros = (
        supabase.table("clientes")
        .select("*")
        .eq("id", cliente_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    return registros[0] if registros else None


def _nome_cliente(oportunidade: dict[str, Any], clientes: dict[str, str] | None = None) -> str:
    cliente_id = str(oportunidade.get("cliente_id") or "").strip()
    nome_embutido = str(
        oportunidade.get("cliente_nome")
        or oportunidade.get("nome_cliente")
        or oportunidade.get("empresa_nome")
        or ""
    ).strip()
    if nome_embutido:
        return nome_embutido
    if clientes and cliente_id in clientes:
        return clientes[cliente_id]
    cliente = _cliente_por_id(cliente_id)
    return _nome_registro_cliente(cliente)


def _fator(valor: Any) -> float:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(numero if numero <= 1 else numero / 100, 1.0))


def _dentro_periodo(item: dict[str, Any], inicio: date | None, fim: date | None) -> bool:
    referencia = item.get("created_at") or item.get("updated_at") or item.get("data_fechamento_prevista")
    if not referencia:
        return True
    try:
        data_item = datetime.fromisoformat(str(referencia).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            data_item = date.fromisoformat(str(referencia)[:10])
        except ValueError:
            return True
    if inicio and data_item < inicio:
        return False
    if fim and data_item > fim:
        return False
    return True


def _registros_vinculados(tabela: str, oportunidade_id: str) -> list[dict[str, Any]]:
    return (
        supabase.table(tabela)
        .select("*")
        .eq("oportunidade_id", oportunidade_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


def _data_evento(registro: dict[str, Any]) -> str:
    return str(
        registro.get("updated_at")
        or registro.get("created_at")
        or registro.get("data")
        or registro.get("data_pedido")
        or ""
    )


def _contexto_historico(historico: list[dict[str, Any]]) -> dict[str, Any]:
    for registro in historico:
        payload = registro.get("payload")
        if not isinstance(payload, dict):
            continue
        contexto = payload.get("contexto_comercial")
        if isinstance(contexto, dict):
            return contexto
    return {}


@router.get("/oportunidades")
def oportunidades_visao(inicio: date | None = None, fim: date | None = None):
    clientes = _clientes_por_id()
    oportunidades = [
        item
        for item in _lista("cti_oportunidades")
        if str(item.get("origem") or "").strip().upper() == "CRM_APP"
        and _dentro_periodo(item, inicio, fim)
    ]
    return [{**item, "cliente_nome": _nome_cliente(item, clientes)} for item in oportunidades]


@router.get("/oportunidades/{oportunidade_id}/detalhes")
def detalhes_oportunidade(oportunidade_id: str):
    oportunidades = (
        supabase.table("cti_oportunidades")
        .select("*")
        .eq("id", oportunidade_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not oportunidades:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

    oportunidade = oportunidades[0]
    if str(oportunidade.get("origem") or "").strip().upper() != "CRM_APP":
        raise HTTPException(status_code=404, detail="Oportunidade operacional não encontrada.")

    atividades = _registros_vinculados("cti_atividades", oportunidade_id)
    pipeline = _registros_vinculados("cti_pipeline", oportunidade_id)
    historico = _registros_vinculados("cti_oportunidade_historico", oportunidade_id)
    propostas = _registros_vinculados("cti_propostas", oportunidade_id)
    pedidos = _registros_vinculados("cti_pedidos", oportunidade_id)
    contexto = _contexto_historico(historico)

    cliente_id = str(oportunidade.get("cliente_id") or "").strip()
    cliente = _cliente_por_id(cliente_id)
    cliente_nome = _nome_cliente(oportunidade)

    oportunidade = {
        **oportunidade,
        "cliente_id": cliente_id or None,
        "cliente_nome": cliente_nome,
        "cliente": cliente,
        "contexto_comercial": contexto,
    }

    eventos: list[dict[str, Any]] = []
    for tipo, registros in (
        ("HISTORICO", historico),
        ("ATIVIDADE", atividades),
        ("PIPELINE", pipeline),
        ("PROPOSTA", propostas),
        ("PEDIDO", pedidos),
    ):
        for registro in registros:
            eventos.append(
                {
                    "tipo": tipo,
                    "data_hora": _data_evento(registro),
                    "titulo": registro.get("titulo")
                    or registro.get("descricao")
                    or registro.get("numero")
                    or registro.get("nova_etapa")
                    or registro.get("etapa")
                    or tipo.title(),
                    "status": registro.get("status")
                    or registro.get("nova_etapa")
                    or registro.get("etapa"),
                    "responsavel_id": registro.get("usuario_id") or registro.get("responsavel_id"),
                    "registro": registro,
                }
            )
    eventos.sort(key=lambda item: item.get("data_hora") or "", reverse=True)

    return {
        "oportunidade": oportunidade,
        "cliente": cliente,
        "itens": [],
        "resumo": {
            "atividades": len(atividades),
            "movimentacoes_pipeline": len(pipeline),
            "propostas": len(propostas),
            "pedidos": len(pedidos),
        },
        "atividades": atividades,
        "pipeline": pipeline,
        "historico": historico,
        "propostas": propostas,
        "pedidos": pedidos,
        "eventos": eventos,
    }


@router.get("/pipeline")
def pipeline_visao(inicio: date | None = None, fim: date | None = None):
    clientes = _clientes_por_id()
    oportunidades = [
        item
        for item in _lista("cti_oportunidades")
        if str(item.get("origem") or "").strip().upper() == "CRM_APP"
        and _dentro_periodo(item, inicio, fim)
    ]
    ids = {item.get("id") for item in oportunidades if item.get("id")}
    movimentos = [item for item in _lista("cti_pipeline") if item.get("oportunidade_id") in ids]
    ultimo: dict[str, dict[str, Any]] = {}
    for movimento in movimentos:
        oportunidade_id = str(movimento.get("oportunidade_id") or "")
        if oportunidade_id and oportunidade_id not in ultimo:
            ultimo[oportunidade_id] = movimento

    cards = []
    for oportunidade in oportunidades:
        oportunidade_id = str(oportunidade.get("id") or "")
        movimento = ultimo.get(oportunidade_id, {})
        etapa = str(
            movimento.get("nova_etapa")
            or movimento.get("etapa")
            or oportunidade.get("status")
            or "OPORTUNIDADE"
        ).upper()
        if etapa not in ETAPAS:
            etapa = "OPORTUNIDADE"
        valor = float(oportunidade.get("valor_estimado") or 0)
        probabilidade = _fator(oportunidade.get("probabilidade"))
        cards.append(
            {
                "id": oportunidade_id,
                "oportunidade_id": oportunidade_id,
                "titulo": oportunidade.get("titulo") or "Oportunidade sem título",
                "cliente_id": oportunidade.get("cliente_id"),
                "cliente_nome": _nome_cliente(oportunidade, clientes),
                "responsavel_id": oportunidade.get("responsavel_id"),
                "etapa": etapa,
                "valor_estimado": valor,
                "probabilidade": probabilidade,
                "valor_ponderado": round(valor * probabilidade, 2),
                "equipamento": oportunidade.get("equipamento") or oportunidade.get("linha_equipamentos"),
                "data_fechamento_prevista": oportunidade.get("data_fechamento_prevista"),
                "ultima_movimentacao": movimento.get("created_at")
                or movimento.get("updated_at")
                or oportunidade.get("updated_at")
                or oportunidade.get("created_at"),
            }
        )

    contagem = Counter(card["etapa"] for card in cards)
    return {
        "etapas": ETAPAS,
        "cards": cards,
        "resumo": {
            "total_oportunidades": len(cards),
            "valor_total": round(sum(card["valor_estimado"] for card in cards), 2),
            "valor_ponderado": round(sum(card["valor_ponderado"] for card in cards), 2),
            "por_etapa": {etapa: contagem.get(etapa, 0) for etapa in ETAPAS},
        },
    }
