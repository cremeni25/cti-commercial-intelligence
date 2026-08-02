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


def _numero(valor: Any) -> float:
    if valor in (None, ""):
        return 0.0
    try:
        if isinstance(valor, str):
            normalizado = valor.strip().replace("R$", "").replace(" ", "")
            if "," in normalizado:
                normalizado = normalizado.replace(".", "").replace(",", ".")
            return float(normalizado)
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _ler_tabela(nome: str, obrigatoria: bool = False) -> list[dict[str, Any]]:
    try:
        resposta = supabase.table(nome).select("*").execute()
        dados = getattr(resposta, "data", None)
        return dados if isinstance(dados, list) else []
    except Exception as erro:
        print(f"[CRM_NUCLEO] falha ao ler {nome}: {erro}")
        if obrigatoria:
            raise
        return []


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
    return prioridade, int(_numero(proposta.get("versao"))), _texto(proposta.get("created_at"))


def _prioridade_pedido(pedido: dict[str, Any]) -> tuple[int, str]:
    status = _status(pedido.get("status"))
    prioridade = {
        "FATURADO": 60,
        "APROVADO_CARRIER": 50,
        "ENVIADO_CARRIER": 45,
        "CARRIER": 45,
        "DOSSIÊ": 40,
        "DOSSIE": 40,
        "PEDIDO": 30,
    }.get(status, 10)
    return prioridade, _texto(pedido.get("created_at") or pedido.get("data_pedido"))


def _valor_item(item: dict[str, Any]) -> float:
    quantidade = _numero(item.get("quantidade"))
    preco = _numero(item.get("preco_unitario"))
    desconto = _numero(item.get("desconto_percentual"))
    return round(quantidade * preco * (1 - desconto / 100), 2)


def _tem_dossie(pedido: dict[str, Any]) -> bool:
    documentos = pedido.get("dossie_documentos")
    if isinstance(documentos, dict):
        return bool(documentos)
    if isinstance(documentos, list):
        return len(documentos) > 0
    return bool(_texto(documentos))


def _etapa_comercial(
    oportunidade: dict[str, Any],
    atividades: list[dict[str, Any]],
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
        if any(_tem_dossie(item) for item in pedidos):
            return "DOSSIÊ"
        return "PEDIDO"
    propostas_ativas = [
        proposta for proposta in propostas
        if _status(proposta.get("status_documento") or proposta.get("status")) not in STATUS_PROPOSTA_INATIVA
    ]
    if any(_status(item.get("status_documento") or item.get("status")) in STATUS_PROPOSTA_FINAL for item in propostas_ativas):
        return "ACEITE"
    if propostas_ativas:
        return "PROPOSTA"
    if atividades:
        return "ATIVIDADE"
    return "OPORTUNIDADE"


def _probabilidade(etapa: str, oportunidade: dict[str, Any]) -> float:
    if etapa in ETAPAS_PROBABILIDADE_TOTAL:
        return 1.0
    if etapa in ETAPAS_PROBABILIDADE_ZERO:
        return 0.0
    return _normalizar_probabilidade(oportunidade.get("probabilidade"))


def _nome_cliente(cliente: dict[str, Any], oportunidade: dict[str, Any]) -> str:
    for campo in ("razao_social", "nome_fantasia", "nome", "cliente_nome"):
        valor = cliente.get(campo)
        if _texto(valor):
            return _texto(valor)
    for campo in ("cliente_nome", "titulo_cliente"):
        valor = oportunidade.get(campo)
        if _texto(valor):
            return _texto(valor)
    return "Cliente não identificado"


@router.get("/nucleo-comercial")
def nucleo_comercial():
    oportunidades = _ler_tabela("cti_oportunidades", obrigatoria=True)
    itens = _ler_tabela("cti_oportunidade_itens")
    atividades = _ler_tabela("cti_atividades")
    propostas = _ler_tabela("cti_propostas")
    pedidos = _ler_tabela("cti_pedidos")
    clientes = _ler_tabela("cti_clientes")

    itens_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    atividades_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    propostas_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pedidos_por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)

    proposta_por_id = {str(item.get("id")): item for item in propostas if item.get("id")}
    cliente_por_id = {str(item.get("id")): item for item in clientes if item.get("id")}

    for item in itens:
        oportunidade_id = str(item.get("oportunidade_id") or "")
        if oportunidade_id:
            itens_por_oportunidade[oportunidade_id].append(item)

    for atividade in atividades:
        oportunidade_id = str(atividade.get("oportunidade_id") or "")
        if oportunidade_id:
            atividades_por_oportunidade[oportunidade_id].append(atividade)

    for proposta in propostas:
        oportunidade_id = str(proposta.get("oportunidade_id") or "")
        if oportunidade_id:
            propostas_por_oportunidade[oportunidade_id].append(proposta)

    for pedido in pedidos:
        oportunidade_id = str(pedido.get("oportunidade_id") or "")
        if not oportunidade_id:
            proposta_id = str(pedido.get("proposta_aceita_id") or pedido.get("proposta_id") or "")
            proposta = proposta_por_id.get(proposta_id, {})
            oportunidade_id = str(proposta.get("oportunidade_id") or "")
        if oportunidade_id:
            pedidos_por_oportunidade[oportunidade_id].append(pedido)

    resultado: list[dict[str, Any]] = []
    for oportunidade in oportunidades:
        oportunidade_id = str(oportunidade.get("id") or "")
        if not oportunidade_id:
            continue

        itens_oportunidade = itens_por_oportunidade.get(oportunidade_id, [])
        atividades_oportunidade = atividades_por_oportunidade.get(oportunidade_id, [])
        propostas_oportunidade = propostas_por_oportunidade.get(oportunidade_id, [])
        pedidos_oportunidade = pedidos_por_oportunidade.get(oportunidade_id, [])

        propostas_ativas = [
            proposta for proposta in propostas_oportunidade
            if _status(proposta.get("status_documento") or proposta.get("status")) not in STATUS_PROPOSTA_INATIVA
        ]
        proposta_vigente = max(propostas_ativas, key=_prioridade_proposta) if propostas_ativas else None
        pedido_vigente = max(pedidos_oportunidade, key=_prioridade_pedido) if pedidos_oportunidade else None

        etapa = _etapa_comercial(
            oportunidade,
            atividades_oportunidade,
            propostas_oportunidade,
            pedidos_oportunidade,
        )
        probabilidade = _probabilidade(etapa, oportunidade)

        valor_itens = round(sum(
            _valor_item(item)
            for item in itens_oportunidade
            if _status(item.get("status")) not in ETAPAS_PROBABILIDADE_ZERO
        ), 2)
        valor = (
            _numero(pedido_vigente.get("valor") if pedido_vigente else None)
            or _numero(proposta_vigente.get("valor") if proposta_vigente else None)
            or valor_itens
            or _numero(oportunidade.get("valor_estimado"))
        )

        cliente = cliente_por_id.get(str(oportunidade.get("cliente_id") or ""), {})
        cliente_nome = _nome_cliente(cliente, oportunidade)

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
            "status_proposta": (
                proposta_vigente.get("status_documento") or proposta_vigente.get("status")
                if proposta_vigente else None
            ),
            "pedido_id": pedido_vigente.get("id") if pedido_vigente else None,
            "pedido_numero": pedido_vigente.get("numero") if pedido_vigente else None,
            "status_pedido": pedido_vigente.get("status") if pedido_vigente else None,
            "quantidade_itens": len(itens_oportunidade),
            "quantidade_atividades": len(atividades_oportunidade),
            "quantidade_propostas_ativas": len(propostas_ativas),
            "encerrada": etapa in STATUS_OPORTUNIDADE_ENCERRADA or etapa in {"FATURADO", "ENCERRADO"},
        })

    return sorted(
        resultado,
        key=lambda item: (item.get("competencia") or "", item.get("titulo") or ""),
        reverse=True,
    )
