from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from core.supabase_client import supabase

STATUS_CARRIER = {"CARRIER"}
STATUS_CONCORRENTE = {"TK", "NACIONAL"}
STATUS_FUNIL_ENCERRADO = {"GANHO", "PERDIDO", "ENCERRADO", "FECHADO"}


def _paginar_tabela(nome: str, campos: str = "*") -> list[dict[str, Any]]:
    saida: list[dict[str, Any]] = []
    pagina = 0
    limite = 1000
    while True:
        dados = supabase.table(nome).select(campos).range(pagina * limite, (pagina + 1) * limite - 1).execute().data or []
        saida.extend(dados)
        if len(dados) < limite:
            break
        pagina += 1
    return saida


def _data(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _ordem_temporal_valida(eventos: list[dict[str, Any]]) -> bool:
    crm = sorted(filter(None, (_data(e.get("data_evento")) for e in eventos if e.get("fonte") == "CRM")))
    funil = sorted(filter(None, (_data(e.get("data_evento")) for e in eventos if e.get("fonte") == "FUNIL")))
    fechamento = sorted(filter(None, (_data(e.get("data_evento")) for e in eventos if e.get("fonte") in {"ANFIR", "VENDA"})))
    if not (crm and funil and fechamento):
        return False
    return crm[0] <= funil[-1] <= fechamento[-1]


def _desfecho(eventos: list[dict[str, Any]]) -> str:
    if any(e.get("fonte") == "VENDA" for e in eventos):
        return "SUCESSO_COMERCIAL_CONFIRMADO"
    status_anfir = {str(e.get("estado_comercial") or "").strip().upper() for e in eventos if e.get("fonte") == "ANFIR"}
    if status_anfir & STATUS_CARRIER:
        return "SUCESSO_COMERCIAL_CONFIRMADO"
    if status_anfir & STATUS_CONCORRENTE:
        return "RESULTADO_CONCORRENTE_CONFIRMADO"
    funil = [e for e in eventos if e.get("fonte") == "FUNIL"]
    if any(str(e.get("estado_comercial") or "").upper() not in STATUS_FUNIL_ENCERRADO for e in funil):
        return "EM_CURSO_BACKLOG"
    if any(e.get("fonte") == "CRM" for e in eventos):
        return "PROSPECCAO_OU_ACAO_ATIVA"
    return "SEM_DESFECHO_COMERCIAL"


def consolidar_verdade_comercial(*, usuario_id: str | None = None, master: bool = False, responsavel_id: str | None = None, limite_clientes: int = 200) -> dict[str, Any]:
    evidencias = _paginar_tabela("cti_evidencias_comerciais", "id,fonte,fonte_registro_id,cliente_id,cliente_nome,temporalidade,evento,estado_comercial,data_evento,segmento,equipamento,quantidade,valor,responsavel_id,metodo_reconciliacao,confianca,metadata")
    clientes = _paginar_tabela("clientes", "id,nome,cnpj,cidade,ddd,sub_regiao,responsavel_comercial_id,responsabilidade_tipo")
    mapa_clientes = {str(c.get("id")): c for c in clientes if c.get("id")}

    alvo = str(responsavel_id or usuario_id or "")
    deve_filtrar = bool(alvo) and (not master or bool(responsavel_id))
    if deve_filtrar:
        ids_permitidos = {str(c.get("id")) for c in clientes if c.get("id") and str(c.get("responsavel_comercial_id") or "") in {"", alvo}}
        evidencias = [e for e in evidencias if (e.get("cliente_id") and str(e.get("cliente_id")) in ids_permitidos) or (not e.get("cliente_id") and str(e.get("responsavel_id") or "") == alvo)]

    por_cliente: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sem_cliente = 0
    for evidencia in evidencias:
        cliente_id = str(evidencia.get("cliente_id") or "")
        if not cliente_id:
            sem_cliente += 1
            continue
        por_cliente[cliente_id].append(evidencia)

    jornadas: list[dict[str, Any]] = []
    for cliente_id, eventos in por_cliente.items():
        origens = sorted({str(e.get("fonte")) for e in eventos})
        cliente = mapa_clientes.get(cliente_id, {})
        datas = sorted(d for d in (_data(e.get("data_evento")) for e in eventos) if d)
        desfecho = _desfecho(eventos)
        cadeia_completa = {"CRM", "FUNIL"}.issubset(origens) and bool({"ANFIR", "VENDA"} & set(origens))
        jornadas.append({
            "cliente_id": cliente_id,
            "cliente_nome": cliente.get("nome") or eventos[0].get("cliente_nome") or "Cliente",
            "cnpj": cliente.get("cnpj"),
            "cidade": cliente.get("cidade"),
            "ddd": cliente.get("ddd"),
            "sub_regiao": cliente.get("sub_regiao"),
            "responsavel_comercial_id": cliente.get("responsavel_comercial_id"),
            "origens": origens,
            "quantidade_evidencias": len(eventos),
            "primeiro_evento": datas[0].isoformat() if datas else None,
            "ultimo_evento": datas[-1].isoformat() if datas else None,
            "desfecho": desfecho,
            "cadeia_crm_funil_realizado": cadeia_completa,
            "ordem_temporal_confirmada": _ordem_temporal_valida(eventos) if cadeia_completa else False,
            "evidencias": sorted(eventos, key=lambda e: str(e.get("data_evento") or "")),
        })

    prioridade = {"SUCESSO_COMERCIAL_CONFIRMADO": 0, "RESULTADO_CONCORRENTE_CONFIRMADO": 1, "EM_CURSO_BACKLOG": 2, "PROSPECCAO_OU_ACAO_ATIVA": 3, "SEM_DESFECHO_COMERCIAL": 4}
    jornadas.sort(key=lambda j: (prioridade.get(j["desfecho"], 9), j.get("cliente_nome") or ""))

    por_fonte: dict[str, int] = defaultdict(int)
    por_temporalidade: dict[str, int] = defaultdict(int)
    por_desfecho: dict[str, int] = defaultdict(int)
    for e in evidencias:
        por_fonte[str(e.get("fonte") or "DESCONHECIDA")] += 1
        por_temporalidade[str(e.get("temporalidade") or "DESCONHECIDA")] += 1
    for j in jornadas:
        por_desfecho[j["desfecho"]] += 1

    return {
        "contrato": {
            "principio": "MESMA_VERDADE_FACTUAL_LEITURAS_DIFERENTES",
            "fontes_preservadas": True,
            "fusao_dados_brutos": False,
            "anfir": "PASSADO_CONFIRMADO",
            "funil": "PASSADO_ENCERRADO_E_EM_CURSO_BACKLOG",
            "crm": "PRESENTE_OPERACIONAL_ACAO_DIARIA",
            "regra_sucesso": "CRM/FUNIL correlacionados ao mesmo cliente e desfecho CARRIER/VENDA confirmado por fonte realizada",
        },
        "filtro_responsavel_id": responsavel_id,
        "resumo": {
            "evidencias": len(evidencias),
            "clientes_reconciliados": len(jornadas),
            "evidencias_sem_cliente_reconciliado": sem_cliente,
            "por_fonte": dict(sorted(por_fonte.items())),
            "por_temporalidade": dict(sorted(por_temporalidade.items())),
            "por_desfecho": dict(sorted(por_desfecho.items())),
            "cadeias_crm_funil_realizado": sum(1 for j in jornadas if j["cadeia_crm_funil_realizado"]),
            "cadeias_temporais_confirmadas": sum(1 for j in jornadas if j["ordem_temporal_confirmada"]),
        },
        "jornadas": jornadas[: max(1, min(limite_clientes, 500))],
    }
