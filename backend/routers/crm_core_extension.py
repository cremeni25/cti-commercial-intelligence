from __future__ import annotations

from collections import defaultdict
from typing import Any

from .crm_router import router, supabase, _normalizar_probabilidade

STATUS_OPORTUNIDADE_ENCERRADA = {"GANHO", "PERDIDO", "CANCELADO", "CONCLUIDO", "ENCERRADO"}
STATUS_PROPOSTA_INATIVA = {"SUBSTITUIDA", "CANCELADA", "EXPIRADA", "REJEITADA", "OBSOLETA"}
STATUS_PROPOSTA_FINAL = {"ACEITA", "CONVERTIDA_PEDIDO"}
ETAPAS_PROBABILIDADE_TOTAL = {"PEDIDO", "DOSSIÊ", "DOSSIE", "CARRIER", "FATURADO", "GANHO", "ENCERRADO"}
ETAPAS_PROBABILIDADE_ZERO = {"PERDIDO", "CANCELADO"}


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _status(valor: Any) -> str:
    return _texto(valor).upper().replace(" ", "_")


def _prioridade_proposta(proposta: dict[str, Any]) -> tuple[int, int, str]:
    status = _status(proposta.get("status_documento") or proposta.get("status"))
    prioridade = {
        "CONVERTIDA_PEDIDO": 70,
        "ACEITA": 60,
        "APROVADA": 60,
        "EM_NEGOCIACAO": 50,
        "VISUALIZADA": 45,
        "ENVIADA": 40,
        "EMITIDA": 35,
        "APROVADA_INTERNA": 30,
        "EM_REVISAO": 20,
        "RASCUNHO": 10,
        "ELABORACAO": 10,
    }.get(status, 0)
    return prioridade, int(proposta.get("versao") or 0), _texto(proposta.get("created_at"))


def _valor_item(item: dict[str, Any]) -> float:
    quantidade = float(item.get("quantidade") or 0)
    preco = float(item.get("preco_unitario") or 0)
    desconto = float(item.get("desconto_percentual") or 0)
    return round(quantidade * preco * (1 - desconto / 100), 2)


def _etapa_comercial(
    oportunidade: dict[str, Any],
    itens: list[dict[str, Any]],
    propostas: list[dict[str, Any]],
    pedidos: list[dict[str, Any]],
) -> str:
    status_oportunidade = _status(oportunidade.get("status")) or "OPORTUNIDADE"
    if status_oportunidade in ETAPAS_PROBABILIDADE_ZERO:
        return status_oportunidade
    if status_oportunidade in {"FATURADO", "ENCERRADO", "CONCLUIDO"}:
        return "ENCERRADO" if status_oportunidade == "CONCLUIDO" else status_oportunidade
    if pedidos:
        status_pedidos = {_status(item.get("status")) for item in pedidos}
        if "FATURADO" in status_pedidos:
            return "FATURADO"
        if status_pedidos & {"ENVIADO_CARRIER", "CARRIER", "APROVADO_CARRIER"}:
            return "CARRIER"
        if any(item.get("dossie_documentos") for item in pedidos):
            return "DOSSIÊ"
        return "PEDIDO"
    propostas_ativas = [
        proposta for proposta in propostas
        if _status(proposta.get("status_documento") or proposta.get("status")) not in STATUS_PROPOSTA_INATIVA
    ]
    if any(_status(item.get("status_documento")) in STATUS_PROPOSTA_FINAL for item in propostas_ativas):
        return "ACEITE"
    if propostas_ativas:
        return "PROPOSTA"
    if itens:
        return "ATIVIDADE"
    return "OPORTUNIDADE"


def _probabilidade(etapa: str, oportunidade: dict[str, Any]) -> float:
    if etapa in ETAPAS_PROBABILIDADE_TOTAL:
        return 1.0
    if etapa in ETAPAS_PROBABILIDADE_ZERO:
        return 0.0
    return _normalizar_probabilidade(oportunidade.get("probabilidade"))


@router.get("/nucleo-comercial")
def nucleo_comercial():
    oportunidades = supabase.table("cti_oportunidades").select("*").execute().data or []
    itens = supabase.table("cti_oportunidade_itens").select("*").execute().data or []
    propostas = supabase.table("cti_propostas").select("*").execute().data or []
    pedidos = supabase.table("cti_pedidos").select("*").execute().data or []
    clientes = supabase.table("cti_clientes").select("id,nome,razao_social,nome_fantasia").execute().data or []

    itens_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    propostas_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pedidos_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    proposta_por_id = {str(item.get("id")): item for item in propostas if item.get("id")}
    cliente_por_id = {str(item.get("id")): item for item in clientes if item.get("id")}

    for item in itens:
        itens_por_oportunidade[str(item.get("oportunidade_id") or "")].append(item)
    for proposta in propostas:
        propostas_por_oportunidade[str(proposta.get("oportunidade_id") or "")].append(proposta)
    for pedido in pedidos:
        proposta = proposta_por_id.get(str(pedido.get("proposta_aceita_id") or pedido.get("proposta_id") or ""), {})
        oportunidade_id = str(proposta.get("oportunidade_id") or "")
        if oportunidade_id:
            pedidos_por_oportunidade[oportunidade_id].append(pedido)

    resultado = []
    for oportunidade in oportunidades:
        oportunidade_id = str(oportunidade.get("id") or "")
        itens_oportunidade = itens_por_oportunidade.get(oportunidade_id, [])
        propostas_oportunidade = propostas_por_oportunidade.get(oportunidade_id, [])
        pedidos_oportunidade = pedidos_por_oportunidade.get(oportunidade_id, [])
        propostas_ativas = [
            proposta for proposta in propostas_oportunidade
            if _status(proposta.get("status_documento") or proposta.get("status")) not in STATUS_PROPOSTA_INATIVA
        ]
        proposta_vigente = max(propostas_ativas, key=_prioridade_proposta) if propostas_ativas else None
        etapa = _etapa_comercial(oportunidade, itens_oportunidade, propostas_oportunidade, pedidos_oportunidade)
        probabilidade = _probabilidade(etapa, oportunidade)
        valor_itens = round(sum(
            _valor_item(item)
            for item in itens_oportunidade
            if _status(item.get("status")) not in ETAPAS_PROBABILIDADE_ZERO
        ), 2)
        valor = float(
            (pedidos_oportunidade[0].get("valor") if pedidos_oportunidade else None)
            or (proposta_vigente.get("valor") if proposta_vigente else None)
            or valor_itens
            or oportunidade.get("valor_estimado")
            or 0
        )
        cliente = cliente_por_id.get(str(oportunidade.get("cliente_id") or ""), {})
        cliente_nome = (
            cliente.get("razao_social")
            or cliente.get("nome_fantasia")
            or cliente.get("nome")
            or oportunidade.get("cliente_nome")
            or "Cliente não identificado"
        )
        resultado.append({
            "oportunidade_id": oportunidade_id,
            "titulo": oportunidade.get("titulo") or "Oportunidade sem título",
            "cliente_id": oportunidade.get("cliente_id"),
            "cliente_nome": cliente_nome,
            "responsavel_id": oportunidade.get("responsavel_id"),
            "etapa": etapa,
            "status_oportunidade": oportunidade.get("status"),
            "probabilidade": probabilidade,
            "valor": round(valor, 2),
            "valor_ponderado": round(valor * probabilidade, 2),
            "competencia": _texto(oportunidade.get("data_fechamento_prevista") or oportunidade.get("created_at"))[:7],
            "data_fechamento_prevista": oportunidade.get("data_fechamento_prevista"),
            "proposta_id": proposta_vigente.get("id") if proposta_vigente else None,
            "proposta_numero": proposta_vigente.get("numero") if proposta_vigente else None,
            "status_proposta": proposta_vigente.get("status_documento") if proposta_vigente else None,
            "pedido_id": pedidos_oportunidade[0].get("id") if pedidos_oportunidade else None,
            "pedido_numero": pedidos_oportunidade[0].get("numero") if pedidos_oportunidade else None,
            "status_pedido": pedidos_oportunidade[0].get("status") if pedidos_oportunidade else None,
            "quantidade_itens": len(itens_oportunidade),
            "quantidade_propostas_ativas": len(propostas_ativas),
            "encerrada": etapa in STATUS_OPORTUNIDADE_ENCERRADA or etapa in {"FATURADO", "ENCERRADO"},
        })

    return sorted(resultado, key=lambda item: (item.get("competencia") or "", item.get("titulo") or ""), reverse=True)
