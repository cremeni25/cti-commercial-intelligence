from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import json
from typing import Any

from .crm_router import router, supabase, _normalizar_probabilidade

STATUS_OPORTUNIDADE_ENCERRADA = {"GANHO", "PERDIDO", "CANCELADO", "CONCLUIDO", "ENCERRADO"}
STATUS_PROPOSTA_INATIVA = {"SUBSTITUIDA", "CANCELADA", "EXPIRADA", "REJEITADA", "OBSOLETA"}
STATUS_PROPOSTA_FINAL = {"ACEITA", "CONVERTIDA_PEDIDO"}
ETAPAS_PROBABILIDADE_TOTAL = {"PEDIDO", "DOSSIÊ", "DOSSIE", "CARRIER", "FATURADO", "GANHO", "ENCERRADO"}
ETAPAS_PROBABILIDADE_ZERO = {"PERDIDO", "CANCELADO"}
TITULOS_GENERICOS = {"", "PROPOSTA COMERCIAL", "OPORTUNIDADE", "NOVA OPORTUNIDADE", "OPORTUNIDADE SEM TÍTULO"}
PREFIXO_TIPO_OPORTUNIDADE = "TIPO DA OPORTUNIDADE:"


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


def _data_iso(valor: Any) -> str | None:
    texto = _texto(valor)
    if not texto:
        return None
    candidato = texto[:10]
    try:
        datetime.strptime(candidato, "%Y-%m-%d")
        return candidato
    except ValueError:
        return None


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


def _mesclar_clientes(*fontes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    por_id: dict[str, dict[str, Any]] = {}
    sem_id: list[dict[str, Any]] = []
    for fonte in fontes:
        for cliente in fonte:
            cliente_id = _texto(cliente.get("id"))
            if cliente_id:
                existente = por_id.get(cliente_id, {})
                por_id[cliente_id] = {**cliente, **existente} if existente else cliente
            else:
                sem_id.append(cliente)
    return [*por_id.values(), *sem_id]


def _prioridade_proposta(proposta: dict[str, Any]) -> tuple[int, int, str]:
    status = _status(proposta.get("status_documento") or proposta.get("status"))
    prioridade = {"CONVERTIDA_PEDIDO":70,"ACEITA":60,"APROVADA":60,"EM_NEGOCIACAO":50,"VISUALIZADA":45,"ENVIADA":40,"EMITIDA":35,"APROVADA_INTERNA":30,"EM_REVISAO":20,"RASCUNHO":10,"ELABORACAO":10}.get(status,0)
    return prioridade, int(_numero(proposta.get("versao"))), _texto(proposta.get("created_at"))


def _prioridade_pedido(pedido: dict[str, Any]) -> tuple[int, str]:
    status = _status(pedido.get("status"))
    prioridade = {"FATURADO":60,"APROVADO_CARRIER":50,"ENVIADO_CARRIER":45,"CARRIER":45,"DOSSIÊ":40,"DOSSIE":40,"PEDIDO":30}.get(status,10)
    return prioridade, _texto(pedido.get("created_at") or pedido.get("data_pedido"))


def _valor_item(item: dict[str, Any]) -> float:
    quantidade = _numero(item.get("quantidade"))
    preco_negociado = item.get("preco_negociado_unitario")
    if preco_negociado not in (None, ""):
        return round(quantidade * _numero(preco_negociado), 2)
    preco = _numero(item.get("preco_unitario"))
    desconto = _numero(item.get("desconto_percentual"))
    return round(quantidade * preco * (1 - desconto / 100), 2)


def _tem_dossie(pedido: dict[str, Any]) -> bool:
    if _status(pedido.get("status")) in {"DOSSIÊ", "DOSSIE", "EM_PREPARACAO", "PREPARANDO_DOSSIE"}:
        return True
    documentos = pedido.get("dossie_documentos")
    if isinstance(documentos, dict): return bool(documentos)
    if isinstance(documentos, list): return len(documentos) > 0
    texto = _texto(documentos)
    if not texto or texto.lower() in {"null", "none", "[]", "{}", "false"}: return False
    try: return bool(json.loads(texto))
    except (TypeError, ValueError, json.JSONDecodeError): return False


def _etapa_comercial(oportunidade: dict[str, Any], atividades: list[dict[str, Any]], propostas: list[dict[str, Any]], pedidos: list[dict[str, Any]]) -> str:
    status_oportunidade = _status(oportunidade.get("status")) or "OPORTUNIDADE"
    encerrada_por_data = bool(_texto(oportunidade.get("data_fechamento_real")))
    if encerrada_por_data or status_oportunidade in STATUS_OPORTUNIDADE_ENCERRADA or status_oportunidade == "FATURADO":
        if status_oportunidade in {"GANHO", "PERDIDO", "CANCELADO", "FATURADO"}: return status_oportunidade
        return "ENCERRADO"
    if pedidos:
        status_pedidos = {_status(item.get("status")) for item in pedidos}
        if "FATURADO" in status_pedidos: return "FATURADO"
        if status_pedidos & {"ENVIADO_CARRIER", "CARRIER", "APROVADO_CARRIER"}: return "CARRIER"
        if any(_tem_dossie(item) for item in pedidos): return "DOSSIÊ"
        return "PEDIDO"
    propostas_ativas = [p for p in propostas if _status(p.get("status_documento") or p.get("status")) not in STATUS_PROPOSTA_INATIVA]
    if any(_status(p.get("status_documento") or p.get("status")) in STATUS_PROPOSTA_FINAL for p in propostas_ativas): return "ACEITE"
    if propostas_ativas: return "PROPOSTA"
    if atividades: return "ATIVIDADE"
    return "OPORTUNIDADE"


def _probabilidade(etapa: str, oportunidade: dict[str, Any]) -> float:
    if etapa in ETAPAS_PROBABILIDADE_TOTAL: return 1.0
    if etapa in ETAPAS_PROBABILIDADE_ZERO: return 0.0
    return _normalizar_probabilidade(oportunidade.get("probabilidade"))


def _nome_cliente(cliente: dict[str, Any], *fontes: dict[str, Any] | None) -> str:
    for campo in ("razao_social", "nome_fantasia", "nome", "cliente", "cliente_nome"):
        valor = cliente.get(campo)
        if _texto(valor): return _texto(valor)
    for fonte in fontes:
        if not fonte: continue
        for campo in ("cliente_nome", "razao_social", "nome_fantasia", "nome", "cliente", "titulo_cliente"):
            valor = fonte.get(campo)
            if _texto(valor): return _texto(valor)
    return "Cliente não identificado"


def _tipo_oportunidade_da_descricao(oportunidade: dict[str, Any]) -> str:
    descricao = _texto(oportunidade.get("descricao"))
    if not descricao: return ""
    for linha in descricao.splitlines():
        limpa = linha.strip()
        if limpa.upper().startswith(PREFIXO_TIPO_OPORTUNIDADE): return limpa.split(":", 1)[1].strip()
    return ""


def _titulo_comercial(oportunidade: dict[str, Any], cliente_nome: str, item: dict[str, Any] | None, proposta: dict[str, Any] | None) -> str:
    titulo = _texto(oportunidade.get("titulo"))
    if titulo.upper() not in TITULOS_GENERICOS: return titulo
    tipo_descricao = _tipo_oportunidade_da_descricao(oportunidade)
    if tipo_descricao: return tipo_descricao
    return "Oportunidade comercial"


@router.get("/nucleo-comercial")
def nucleo_comercial():
    oportunidades = _ler_tabela("cti_oportunidades", obrigatoria=True)
    itens = _ler_tabela("cti_oportunidade_itens")
    atividades = _ler_tabela("cti_atividades")
    propostas = _ler_tabela("cti_propostas")
    pedidos = _ler_tabela("cti_pedidos")
    clientes = _mesclar_clientes(_ler_tabela("cti_clientes"), _ler_tabela("clientes"))
    itens_por_oportunidade: dict[str,list[dict[str,Any]]] = defaultdict(list)
    atividades_por_oportunidade: dict[str,list[dict[str,Any]]] = defaultdict(list)
    propostas_por_oportunidade: dict[str,list[dict[str,Any]]] = defaultdict(list)
    pedidos_por_oportunidade: dict[str,list[dict[str,Any]]] = defaultdict(list)
    proposta_por_id = {str(i.get("id")):i for i in propostas if i.get("id")}
    cliente_por_id = {str(i.get("id")):i for i in clientes if i.get("id")}
    for item in itens:
        oid=str(item.get("oportunidade_id") or "")
        if oid: itens_por_oportunidade[oid].append(item)
    for atividade in atividades:
        oid=str(atividade.get("oportunidade_id") or "")
        if oid: atividades_por_oportunidade[oid].append(atividade)
    for proposta in propostas:
        oid=str(proposta.get("oportunidade_id") or "")
        if oid: propostas_por_oportunidade[oid].append(proposta)
    for pedido in pedidos:
        oid=str(pedido.get("oportunidade_id") or "")
        if not oid:
            proposta=proposta_por_id.get(str(pedido.get("proposta_aceita_id") or pedido.get("proposta_id") or ""),{})
            oid=str(proposta.get("oportunidade_id") or "")
        if oid: pedidos_por_oportunidade[oid].append(pedido)
    resultado=[]
    for oportunidade in oportunidades:
        oid=str(oportunidade.get("id") or "")
        if not oid: continue
        itens_o=itens_por_oportunidade.get(oid,[]); atividades_o=atividades_por_oportunidade.get(oid,[]); propostas_o=propostas_por_oportunidade.get(oid,[]); pedidos_o=pedidos_por_oportunidade.get(oid,[])
        propostas_ativas=[p for p in propostas_o if _status(p.get("status_documento") or p.get("status")) not in STATUS_PROPOSTA_INATIVA]
        proposta_vigente=max(propostas_ativas,key=_prioridade_proposta) if propostas_ativas else None
        pedido_vigente=max(pedidos_o,key=_prioridade_pedido) if pedidos_o else None
        item_vigente=itens_o[0] if itens_o else None
        etapa=_etapa_comercial(oportunidade,atividades_o,propostas_o,pedidos_o); probabilidade=_probabilidade(etapa,oportunidade)
        valor_itens=round(sum(_valor_item(i) for i in itens_o if _status(i.get("status")) not in ETAPAS_PROBABILIDADE_ZERO and not i.get("arquivado_em")),2)
        valor=(_numero(pedido_vigente.get("valor") if pedido_vigente else None) if etapa in {"PEDIDO","DOSSIÊ","DOSSIE","CARRIER","FATURADO"} and pedido_vigente else 0.0) or valor_itens or _numero(oportunidade.get("valor_estimado")) or _numero(proposta_vigente.get("valor") if proposta_vigente else None)
        cliente_id=oportunidade.get("cliente_id") or (proposta_vigente or {}).get("cliente_id") or (item_vigente or {}).get("cliente_id") or (pedido_vigente or {}).get("cliente_id")
        cliente=cliente_por_id.get(str(cliente_id or ""),{}); cliente_nome=_nome_cliente(cliente,oportunidade,proposta_vigente,item_vigente,pedido_vigente)
        data_inclusao=_data_iso(oportunidade.get("created_at")); data_prevista=_data_iso(oportunidade.get("data_fechamento_prevista")); data_real=_data_iso(oportunidade.get("data_fechamento_real")); competencia=(data_prevista or data_inclusao or "")[:7]
        titulo=_titulo_comercial(oportunidade,cliente_nome,item_vigente,proposta_vigente); status_canonico=etapa if data_real else oportunidade.get("status")
        resultado.append({"oportunidade_id":oid,"titulo":titulo,"cliente_id":cliente_id,"cliente_nome":cliente_nome,"responsavel_id":oportunidade.get("responsavel_id"),"created_at":oportunidade.get("created_at"),"updated_at":oportunidade.get("updated_at"),"data_inclusao":data_inclusao,"linha_equipamento":(item_vigente or {}).get("linha_produto"),"equipamento":(item_vigente or {}).get("equipamento"),"etapa":etapa,"status_oportunidade":status_canonico,"probabilidade":probabilidade,"valor":round(valor,2),"valor_ponderado":round(valor*probabilidade,2),"competencia":competencia,"data_fechamento_prevista":data_prevista,"data_fechamento_real":data_real,"motivo_encerramento":oportunidade.get("motivo_encerramento"),"observacao_encerramento":oportunidade.get("observacao_encerramento"),"proposta_id":proposta_vigente.get("id") if proposta_vigente else None,"proposta_numero":proposta_vigente.get("numero") if proposta_vigente else None,"status_proposta":(proposta_vigente.get("status_documento") or proposta_vigente.get("status")) if proposta_vigente else None,"pedido_id":pedido_vigente.get("id") if pedido_vigente else None,"pedido_numero":pedido_vigente.get("numero") if pedido_vigente else None,"status_pedido":pedido_vigente.get("status") if pedido_vigente else None,"quantidade_itens":len([i for i in itens_o if not i.get("arquivado_em")]),"quantidade_atividades":len(atividades_o),"quantidade_propostas_ativas":len(propostas_ativas),"encerrada":bool(data_real) or etapa in STATUS_OPORTUNIDADE_ENCERRADA or etapa in {"FATURADO","ENCERRADO"}})
    return sorted(resultado,key=lambda i:(i.get("competencia") or "",i.get("titulo") or ""),reverse=True)
