"""Composição do briefing comercial: a devolutiva única do agente.

O briefing responde, em uma leitura, às perguntas que o vendedor e o gestor
fazem toda manhã:

1. Como estou? (indicadores — no máximo cinco)
2. O que faço primeiro? (prioridades ranqueadas, uma por negócio)
3. Onde estou perdendo dinheiro? (riscos agregados)
4. Como está o funil? (pipeline por etapa)
5. Posso confiar nos números? (qualidade dos dados)

É uma função pura sobre dados já autorizados: não lê banco, não escreve e não
depende de modelo de linguagem — o que o torna auditável e testável. A IA
conversacional consome este mesmo briefing como ferramenta.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from . import provedores as _provedores  # noqa: F401  (registra os provedores nativos)
from .provedores import ETAPAS_POS_VENDA, oportunidade_aberta
from .sinais import ContextoInteligencia, Sinal, numero, provedores_registrados, status, texto

VERSAO_BRIEFING = "1.0"
# Operação no Brasil (sem horário de verão desde 2019). "Hoje" é a data civil
# local: em UTC, depois das 21h o dia comercial viraria o dia seguinte.
FUSO_OPERACAO = timezone(timedelta(hours=-3), "America/Sao_Paulo")


def hoje_operacional() -> date:
    return datetime.now(FUSO_OPERACAO).date()
LIMITE_PRIORIDADES = 8

ORDEM_ETAPAS = ["OPORTUNIDADE", "ATIVIDADE", "PROPOSTA", "ACEITE", "PEDIDO", "DOSSIÊ", "CARRIER"]
ROTULO_ETAPA = {
    "OPORTUNIDADE": "Oportunidade", "ATIVIDADE": "Em contato", "PROPOSTA": "Proposta",
    "ACEITE": "Aceite", "PEDIDO": "Pedido", "DOSSIÊ": "Dossiê", "DOSSIE": "Dossiê", "CARRIER": "Carrier",
}
ROTULO_SINAL = {
    "FOLLOWUP_ATRASADO": "Follow-ups atrasados",
    "AGENDA_HOJE": "Compromissos de hoje",
    "FECHAMENTO_VENCIDO": "Previsões de fechamento vencidas",
    "PROPOSTA_SEM_RETORNO": "Propostas sem retorno",
    "OPORTUNIDADE_PARADA": "Negócios parados",
    "SEM_PROXIMO_PASSO": "Negócios sem próximo passo",
    "PRONTO_PARA_FECHAR": "Prontos para fechar",
    "PEDIDO_SEM_MOVIMENTO": "Pedidos sem movimento",
}
# Problemas de qualidade: (código, rótulo, teste sobre a oportunidade aberta, impacto)
REGRAS_QUALIDADE = (
    ("SEM_VALOR", "Negócios sem valor", lambda o: numero(o.get("valor")) <= 0, "O forecast fica subestimado."),
    ("SEM_PREVISAO", "Negócios sem previsão de fechamento", lambda o: not texto(o.get("data_fechamento_prevista")), "Não entram no planejamento do mês."),
    ("SEM_CLIENTE", "Negócios sem cliente vinculado", lambda o: not texto(o.get("cliente_id")), "O histórico do cliente fica incompleto."),
    ("SEM_EQUIPAMENTO", "Negócios sem linha/equipamento", lambda o: not (texto(o.get("linha_equipamento")) or texto(o.get("equipamento"))), "A leitura por produto e mercado fica cega."),
)


def _moeda(valor: float) -> str:
    if valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f} mi".replace(".", ",")
    if valor >= 1_000:
        return f"R$ {valor / 1_000:.0f} mil"
    return f"R$ {valor:.0f}"


def _executar_provedores(contexto: ContextoInteligencia) -> tuple[list[Sinal], list[dict[str, Any]]]:
    sinais: list[Sinal] = []
    situacao: list[dict[str, Any]] = []
    for registro in provedores_registrados():
        try:
            produzidos = list(registro.funcao(contexto) or [])
            sinais.extend(produzidos)
            situacao.append({"codigo": registro.codigo, "modulo": registro.modulo, "ok": True, "sinais": len(produzidos)})
        except Exception as erro:  # um módulo com defeito nunca derruba a devolutiva
            situacao.append({"codigo": registro.codigo, "modulo": registro.modulo, "ok": False, "sinais": 0, "erro": type(erro).__name__})
    return sinais, situacao


def _priorizar(sinais: list[Sinal], limite: int) -> list[dict[str, Any]]:
    """Uma prioridade por entidade: o sinal mais forte representa o negócio."""
    por_entidade: dict[tuple[str, str], list[Sinal]] = defaultdict(list)
    for sinal in sinais:
        if sinal.categoria == "qualidade":
            continue
        por_entidade[(sinal.entidade_tipo, sinal.entidade_id)].append(sinal)
    escolhidos: list[dict[str, Any]] = []
    for grupo in por_entidade.values():
        grupo.sort(key=lambda s: s.pontuacao, reverse=True)
        principal = grupo[0].para_dict()
        principal["sinais_relacionados"] = [s.codigo for s in grupo[1:]]
        escolhidos.append(principal)
    escolhidos.sort(key=lambda s: (s["pontuacao"], s["valor"]), reverse=True)
    return escolhidos[:limite]


def _pipeline(abertas: list[dict[str, Any]]) -> dict[str, Any]:
    acumulado: dict[str, dict[str, float]] = {}
    for oportunidade in abertas:
        etapa = status(oportunidade.get("etapa")) or "OPORTUNIDADE"
        etapa = "DOSSIÊ" if etapa == "DOSSIE" else etapa
        linha = acumulado.setdefault(etapa, {"quantidade": 0, "valor": 0.0, "valor_ponderado": 0.0})
        linha["quantidade"] += 1
        linha["valor"] += numero(oportunidade.get("valor"))
        linha["valor_ponderado"] += numero(oportunidade.get("valor_ponderado"))
    ordem = ORDEM_ETAPAS + sorted(set(acumulado) - set(ORDEM_ETAPAS))
    etapas = [
        {"etapa": etapa, "rotulo": ROTULO_ETAPA.get(etapa, etapa.replace("_", " ").title()), "quantidade": int(acumulado[etapa]["quantidade"]),
         "valor": round(acumulado[etapa]["valor"], 2), "valor_ponderado": round(acumulado[etapa]["valor_ponderado"], 2)}
        for etapa in ordem if etapa in acumulado
    ]
    return {
        "etapas": etapas,
        "quantidade_aberta": sum(e["quantidade"] for e in etapas),
        "valor_aberto": round(sum(e["valor"] for e in etapas), 2),
        "valor_ponderado": round(sum(e["valor_ponderado"] for e in etapas), 2),
    }


def _qualidade(abertas: list[dict[str, Any]]) -> dict[str, Any]:
    em_venda = [o for o in abertas if status(o.get("etapa")) not in ETAPAS_POS_VENDA]
    problemas = []
    falhas = 0
    for codigo, rotulo, teste, impacto in REGRAS_QUALIDADE:
        afetadas = [o for o in em_venda if teste(o)]
        falhas += len(afetadas)
        if afetadas:
            problemas.append({
                "codigo": codigo, "rotulo": rotulo, "quantidade": len(afetadas), "impacto": impacto,
                "exemplos": [
                    {"oportunidade_id": texto(o.get("oportunidade_id")), "cliente_nome": texto(o.get("cliente_nome")) or "Cliente não identificado",
                     "rota": f"/oportunidades/{texto(o.get('oportunidade_id'))}", "rota_app": f"/crm-app/oportunidades/{texto(o.get('oportunidade_id'))}"}
                    for o in afetadas[:5]
                ],
            })
    verificacoes = len(em_venda) * len(REGRAS_QUALIDADE)
    indice = 100 if verificacoes == 0 else round(100 * (1 - falhas / verificacoes))
    return {"indice": indice, "negocios_avaliados": len(em_venda), "problemas": problemas}


def _indicadores(pipeline: dict[str, Any], contagem: Counter, valor_em_risco: float, ganhos_mes: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {"codigo": "PIPELINE_ABERTO", "rotulo": "Pipeline aberto", "valor": pipeline["valor_aberto"], "formato": "moeda",
         "detalhe": f"{pipeline['quantidade_aberta']} negócios · ponderado {_moeda(pipeline['valor_ponderado'])}", "tom": "neutro", "rota": "/pipeline", "rota_app": "/crm-app/pipeline"},
        {"codigo": "ACOES_HOJE", "rotulo": "Ações para hoje", "valor": contagem["AGENDA_HOJE"] + contagem["FOLLOWUP_ATRASADO"], "formato": "numero",
         "detalhe": f"{contagem['FOLLOWUP_ATRASADO']} atrasadas · {contagem['AGENDA_HOJE']} agendadas", "tom": "atencao" if contagem["FOLLOWUP_ATRASADO"] else "neutro", "rota": "/atividades", "rota_app": "/crm-app/atividades"},
        {"codigo": "VALOR_EM_RISCO", "rotulo": "Valor em risco", "valor": round(valor_em_risco, 2), "formato": "moeda",
         "detalhe": "Negócios parados, vencidos ou sem retorno", "tom": "atencao" if valor_em_risco > 0 else "positivo", "rota": "/oportunidades", "rota_app": "/crm-app/oportunidades"},
        {"codigo": "PRONTOS_FECHAR", "rotulo": "Prontos para fechar", "valor": contagem["PRONTO_PARA_FECHAR"], "formato": "numero",
         "detalhe": "Alta chance e fechamento em até 30 dias", "tom": "positivo" if contagem["PRONTO_PARA_FECHAR"] else "neutro", "rota": "/forecast", "rota_app": "/crm-app/forecast"},
        {"codigo": "GANHOS_MES", "rotulo": "Ganhos no mês", "valor": round(ganhos_mes["valor"], 2), "formato": "moeda",
         "detalhe": f"{int(ganhos_mes['quantidade'])} negócio{'s' if ganhos_mes['quantidade'] != 1 else ''} fechado{'s' if ganhos_mes['quantidade'] != 1 else ''}", "tom": "positivo" if ganhos_mes["quantidade"] else "neutro", "rota": "/vendas", "rota_app": "/crm-app/vendas"},
    ]


def _ganhos_mes(oportunidades: list[dict[str, Any]], hoje: date) -> dict[str, float]:
    competencia = hoje.strftime("%Y-%m")
    ganhos = [
        o for o in oportunidades
        if status(o.get("etapa") or o.get("status_oportunidade")) in {"GANHO", "FATURADO"}
        and texto(o.get("data_fechamento_real"))[:7] == competencia
    ]
    return {"quantidade": float(len(ganhos)), "valor": sum(numero(o.get("valor")) for o in ganhos)}


def _manchete(contagem: Counter, valor_em_risco: float, prioridades: list[dict[str, Any]], pipeline: dict[str, Any]) -> str:
    if pipeline["quantidade_aberta"] == 0 and not prioridades:
        return "Nenhum negócio aberto na sua carteira. Comece registrando uma interação ou uma nova oportunidade."
    partes = []
    if contagem["FOLLOWUP_ATRASADO"]:
        partes.append(f"{contagem['FOLLOWUP_ATRASADO']} follow-up{'s' if contagem['FOLLOWUP_ATRASADO'] > 1 else ''} atrasado{'s' if contagem['FOLLOWUP_ATRASADO'] > 1 else ''}")
    if valor_em_risco > 0:
        partes.append(f"{_moeda(valor_em_risco)} em negócios que pedem atenção")
    if contagem["PRONTO_PARA_FECHAR"]:
        partes.append(f"{contagem['PRONTO_PARA_FECHAR']} pronto{'s' if contagem['PRONTO_PARA_FECHAR'] > 1 else ''} para fechar")
    if not partes:
        return f"Carteira em dia: {pipeline['quantidade_aberta']} negócios abertos ({_moeda(pipeline['valor_aberto'])}) sem pendências críticas."
    texto_partes = partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " e " + partes[-1]
    inicio = f" Comece por {prioridades[0]['cliente_nome']}." if prioridades and prioridades[0].get("cliente_nome") else ""
    return f"Você tem {texto_partes}.{inicio}"


def montar_briefing(
    oportunidades: list[dict[str, Any]],
    atividades: list[dict[str, Any]],
    *,
    hoje: date | None = None,
    escopo: dict[str, Any] | None = None,
    limite_prioridades: int = LIMITE_PRIORIDADES,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hoje = hoje or hoje_operacional()
    contexto = ContextoInteligencia(hoje=hoje, oportunidades=list(oportunidades or []), atividades=list(atividades or []), extras=dict(extras or {}))
    sinais, situacao_provedores = _executar_provedores(contexto)

    contagem = Counter(s.codigo for s in sinais)
    abertas = [o for o in contexto.oportunidades if oportunidade_aberta(o)]
    pipeline = _pipeline(abertas)

    entidades_em_risco: dict[str, float] = {}
    for sinal in sinais:
        if sinal.categoria == "risco" and sinal.entidade_tipo in {"oportunidade", "pedido"}:
            entidades_em_risco[sinal.entidade_id] = max(entidades_em_risco.get(sinal.entidade_id, 0.0), sinal.valor)
    valor_em_risco = sum(entidades_em_risco.values())

    prioridades = _priorizar(sinais, max(1, limite_prioridades))
    riscos = [
        {"codigo": codigo, "rotulo": ROTULO_SINAL.get(codigo, codigo.replace("_", " ").title()), "quantidade": quantidade,
         "valor": round(sum(s.valor for s in sinais if s.codigo == codigo), 2)}
        for codigo, quantidade in contagem.most_common()
        if any(s.codigo == codigo and s.categoria == "risco" for s in sinais)
    ]

    limitacoes = []
    if any(not p["ok"] for p in situacao_provedores):
        limitacoes.append("Um ou mais módulos não puderam ser analisados nesta leitura; os demais sinais continuam válidos.")
    if not contexto.atividades:
        limitacoes.append("Nenhuma atividade encontrada no escopo: agenda e último contato podem estar incompletos.")

    return {
        "versao": VERSAO_BRIEFING,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "data_referencia": hoje.isoformat(),
        "escopo": escopo or {"tipo": "nao_informado"},
        "manchete": _manchete(contagem, valor_em_risco, prioridades, pipeline),
        "indicadores": _indicadores(pipeline, contagem, valor_em_risco, _ganhos_mes(contexto.oportunidades, hoje)),
        "prioridades": prioridades,
        "riscos": riscos,
        "pipeline": pipeline,
        "qualidade": _qualidade(abertas),
        "sinais_por_codigo": dict(contagem),
        "total_sinais": len(sinais),
        "provedores": situacao_provedores,
        "fontes": ["Núcleo comercial (oportunidades, propostas, pedidos)", "Atividades e agenda"],
        "limitacoes": limitacoes,
    }
