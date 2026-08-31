from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date
from typing import Any

from core.supabase_client import supabase
from services.historical_commercial_source import carregar_historico_comercial

STATUS_CARRIER = {"CARRIER"}
STATUS_CONCORRENTE = {"TK", "NACIONAL"}
STATUS_FUNIL_ENCERRADO = {"GANHO", "PERDIDO", "ENCERRADO", "FECHADO", "FATURADO", "VENDIDO", "CANCELADO", "CANCELADA"}
STATUS_FUNIL_BACKLOG = {"BACKLOG", "EM ANDAMENTO", "ABERTO", "ABERTA", "PROPOSTA", "NEGOCIACAO", "NEGOCIAÇÃO"}
STATUS_FUNIL_PROSPECCAO = {"PROSPECT", "PROSPECCAO", "PROSPECÇÃO", "LEAD"}


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^A-Z0-9]", "", texto)


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


def _temporalidade_funil_historico(status: Any) -> str:
    texto = str(status or "").strip().upper()
    if any(chave in texto for chave in STATUS_FUNIL_ENCERRADO):
        return "PASSADO_CONFIRMADO"
    if any(chave in texto for chave in STATUS_FUNIL_BACKLOG):
        return "EM_CURSO_BACKLOG"
    if any(chave in texto for chave in STATUS_FUNIL_PROSPECCAO):
        return "PROSPECCAO"
    return "HISTORICO_INDETERMINADO"


def _evidencias_funil_historico(clientes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    por_nome: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cliente in clientes:
        chave = _fold(cliente.get("nome"))
        if chave:
            por_nome[chave].append(cliente)

    saida: list[dict[str, Any]] = []
    for indice, row in enumerate(carregar_historico_comercial(), start=1):
        chave = _fold(row.get("cliente"))
        candidatos = por_nome.get(chave, []) if chave else []
        cliente = candidatos[0] if len(candidatos) == 1 else None
        origem_id = f"{row.get('arquivo_sha256')}:{row.get('aba_origem')}:{row.get('linha_origem') or indice}"
        saida.append({
            "id": origem_id,
            "fonte": "FUNIL",
            "fonte_registro_id": origem_id,
            "cliente_id": cliente.get("id") if cliente else None,
            "cliente_nome": row.get("cliente"),
            "temporalidade": _temporalidade_funil_historico(row.get("status")),
            "evento": "FUNIL_HISTORICO",
            "estado_comercial": str(row.get("status") or "INDETERMINADO").strip().upper(),
            "data_evento": row.get("data"),
            "segmento": None,
            "equipamento": row.get("equipamento"),
            "quantidade": row.get("quantidade"),
            "valor": row.get("valor_total"),
            "responsavel_id": None,
            "metodo_reconciliacao": "NOME_EXATO_UNICO" if cliente else "SEM_RECONCILIACAO",
            "confianca": 0.80 if cliente else 0,
            "metadata": {
                "origem_funil": "HISTORICO_COMERCIAL_2023_2026",
                "representante_original": row.get("representante_original"),
                "representante_atual": row.get("representante_atual"),
                "previsao": row.get("previsao"),
                "probabilidade": row.get("probabilidade"),
                "motivo_perda": row.get("motivo_perda"),
                "observacao": row.get("observacao"),
                "implementadora": row.get("implementadora"),
            },
        })
    return saida


def _evidencias_operacionais(clientes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nomes = {str(c.get("id")): c.get("nome") for c in clientes if c.get("id")}
    saida: list[dict[str, Any]] = []

    for row in _paginar_tabela("cti_atividades"):
        if row.get("arquivado_em") or bool(row.get("registro_teste")):
            continue
        cliente_id = row.get("cliente_id")
        saida.append({
            "id": f"CRM:{row.get('id')}", "fonte": "CRM", "fonte_registro_id": str(row.get("id")),
            "cliente_id": cliente_id, "cliente_nome": nomes.get(str(cliente_id)) if cliente_id else None,
            "temporalidade": "PRESENTE_OPERACIONAL", "evento": "ACAO_COMERCIAL",
            "estado_comercial": str(row.get("status") or "REGISTRADA").upper(),
            "data_evento": row.get("data") or row.get("data_atividade") or row.get("created_at"),
            "segmento": None, "equipamento": None, "quantidade": None, "valor": None,
            "responsavel_id": row.get("usuario_id"),
            "metodo_reconciliacao": "CLIENTE_ID" if cliente_id else "SEM_RECONCILIACAO",
            "confianca": 1 if cliente_id else 0,
            "metadata": {"tipo": row.get("tipo"), "titulo": row.get("titulo"), "descricao": row.get("descricao"), "oportunidade_id": row.get("oportunidade_id")},
        })

    for row in _paginar_tabela("cti_oportunidades"):
        if row.get("arquivado_em") or bool(row.get("registro_teste")):
            continue
        cliente_id = row.get("cliente_id")
        status = str(row.get("status") or "ABERTA").upper()
        temporalidade = "PASSADO_CONFIRMADO" if status in {"GANHO", "PERDIDO", "ENCERRADO", "FECHADO"} else "EM_CURSO_BACKLOG"
        saida.append({
            "id": f"FUNIL:{row.get('id')}", "fonte": "FUNIL", "fonte_registro_id": str(row.get("id")),
            "cliente_id": cliente_id, "cliente_nome": nomes.get(str(cliente_id)) if cliente_id else None,
            "temporalidade": temporalidade, "evento": "OPORTUNIDADE", "estado_comercial": status,
            "data_evento": row.get("data_fechamento_real") or row.get("data_fechamento_prevista") or row.get("data_abertura") or row.get("created_at"),
            "segmento": None, "equipamento": None, "quantidade": None, "valor": row.get("valor_estimado"),
            "responsavel_id": row.get("responsavel_id"),
            "metodo_reconciliacao": "CLIENTE_ID" if cliente_id else "SEM_RECONCILIACAO", "confianca": 1 if cliente_id else 0,
            "metadata": {"titulo": row.get("titulo"), "origem": row.get("origem"), "probabilidade": row.get("probabilidade"), "data_abertura": row.get("data_abertura"), "data_fechamento_prevista": row.get("data_fechamento_prevista"), "data_fechamento_real": row.get("data_fechamento_real")},
        })

    for row in _paginar_tabela("vendas"):
        if row.get("arquivado_em") or bool(row.get("registro_teste")):
            continue
        cliente_id = row.get("cliente_id")
        saida.append({
            "id": f"VENDA:{row.get('id')}", "fonte": "VENDA", "fonte_registro_id": str(row.get("id")),
            "cliente_id": cliente_id, "cliente_nome": nomes.get(str(cliente_id)) if cliente_id else None,
            "temporalidade": "PASSADO_CONFIRMADO", "evento": "VENDA_CONFIRMADA", "estado_comercial": "GANHO",
            "data_evento": row.get("data_venda"), "segmento": None, "equipamento": row.get("equipamento_codigo"),
            "quantidade": None, "valor": row.get("valor"), "responsavel_id": None,
            "metodo_reconciliacao": "CLIENTE_ID" if cliente_id else "SEM_RECONCILIACAO", "confianca": 1 if cliente_id else 0,
            "metadata": {"tipo_venda": row.get("tipo_venda"), "pedido_id": row.get("pedido_id"), "oportunidade_id": row.get("oportunidade_id"), "observacao": row.get("observacao")},
        })
    return saida


def _ordem_temporal_valida(eventos: list[dict[str, Any]]) -> bool:
    crm = sorted(filter(None, (_data(e.get("data_evento")) for e in eventos if e.get("fonte") == "CRM")))
    funil = sorted(filter(None, (_data(e.get("data_evento")) for e in eventos if e.get("fonte") == "FUNIL")))
    fechamento = sorted(filter(None, (_data(e.get("data_evento")) for e in eventos if e.get("fonte") in {"ANFIR", "VENDA"})))
    if not (crm and funil and fechamento):
        return False
    return crm[0] <= funil[-1] <= fechamento[-1]


def _confianca_cadeia(eventos: list[dict[str, Any]]) -> float:
    relevantes = [float(e.get("confianca") or 0) for e in eventos if e.get("fonte") in {"CRM", "FUNIL", "ANFIR", "VENDA"}]
    return round(min(relevantes), 2) if relevantes else 0


def _desfecho(eventos: list[dict[str, Any]]) -> str:
    if any(e.get("fonte") == "VENDA" for e in eventos):
        return "SUCESSO_COMERCIAL_CONFIRMADO"
    status_anfir = {str(e.get("estado_comercial") or "").strip().upper() for e in eventos if e.get("fonte") == "ANFIR"}
    if status_anfir & STATUS_CARRIER:
        return "SUCESSO_COMERCIAL_CONFIRMADO"
    if status_anfir & STATUS_CONCORRENTE:
        return "RESULTADO_CONCORRENTE_CONFIRMADO"
    funil = [e for e in eventos if e.get("fonte") == "FUNIL"]
    if any(str(e.get("temporalidade") or "") == "EM_CURSO_BACKLOG" for e in funil):
        return "EM_CURSO_BACKLOG"
    if any(str(e.get("temporalidade") or "") == "PROSPECCAO" for e in funil):
        return "PROSPECCAO_OU_ACAO_ATIVA"
    if any(e.get("fonte") == "CRM" for e in eventos):
        return "PROSPECCAO_OU_ACAO_ATIVA"
    return "SEM_DESFECHO_COMERCIAL"


def consolidar_verdade_comercial(*, usuario_id: str | None = None, master: bool = False, responsavel_id: str | None = None, limite_clientes: int = 200) -> dict[str, Any]:
    evidencias = [e for e in _paginar_tabela("cti_evidencias_comerciais", "id,fonte,fonte_registro_id,cliente_id,cliente_nome,temporalidade,evento,estado_comercial,data_evento,segmento,equipamento,quantidade,valor,responsavel_id,metodo_reconciliacao,confianca,metadata") if e.get("fonte") == "ANFIR"]
    clientes = _paginar_tabela("clientes", "id,nome,cnpj,cidade,ddd,sub_regiao,responsavel_comercial_id,responsabilidade_tipo")
    evidencias.extend(_evidencias_funil_historico(clientes))
    evidencias.extend(_evidencias_operacionais(clientes))
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
        confianca_cadeia = _confianca_cadeia(eventos) if cadeia_completa else 0
        ordem_temporal = _ordem_temporal_valida(eventos) if cadeia_completa else False
        jornadas.append({
            "cliente_id": cliente_id, "cliente_nome": cliente.get("nome") or eventos[0].get("cliente_nome") or "Cliente",
            "cnpj": cliente.get("cnpj"), "cidade": cliente.get("cidade"), "ddd": cliente.get("ddd"), "sub_regiao": cliente.get("sub_regiao"),
            "responsavel_comercial_id": cliente.get("responsavel_comercial_id"), "origens": origens, "quantidade_evidencias": len(eventos),
            "primeiro_evento": datas[0].isoformat() if datas else None, "ultimo_evento": datas[-1].isoformat() if datas else None,
            "desfecho": desfecho, "cadeia_crm_funil_realizado": cadeia_completa, "ordem_temporal_confirmada": ordem_temporal,
            "confianca_cadeia": confianca_cadeia, "cadeia_confirmada": bool(cadeia_completa and ordem_temporal and confianca_cadeia >= 0.80),
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
        "contrato": {"principio": "MESMA_VERDADE_FACTUAL_LEITURAS_DIFERENTES", "fontes_preservadas": True, "fusao_dados_brutos": False,
                     "anfir": "PASSADO_CONFIRMADO", "funil": "PASSADO_ENCERRADO_E_EM_CURSO_BACKLOG_E_PROSPECCAO", "crm": "PRESENTE_OPERACIONAL_ACAO_DIARIA",
                     "regra_sucesso": "CRM/Funil/ANFIR ou Venda pertencem ao mesmo cliente reconciliado; a cadeia só é confirmada quando há ordem temporal coerente e confiança mínima."},
        "filtro_responsavel_id": responsavel_id,
        "resumo": {"evidencias": len(evidencias), "clientes_reconciliados": len(jornadas), "evidencias_sem_cliente_reconciliado": sem_cliente,
                   "por_fonte": dict(sorted(por_fonte.items())), "por_temporalidade": dict(sorted(por_temporalidade.items())), "por_desfecho": dict(sorted(por_desfecho.items())),
                   "cadeias_crm_funil_realizado": sum(1 for j in jornadas if j["cadeia_crm_funil_realizado"]),
                   "cadeias_temporais_confirmadas": sum(1 for j in jornadas if j["ordem_temporal_confirmada"]),
                   "cadeias_confirmadas": sum(1 for j in jornadas if j["cadeia_confirmada"])},
        "jornadas": jornadas[: max(1, min(limite_clientes, 500))],
    }
