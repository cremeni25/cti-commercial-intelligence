"""Provedores nativos de sinais: agenda, pipeline, propostas e pedidos.

Os limiares ficam em ``LIMIARES`` para que a gestão comercial possa calibrá-los
sem mexer nas regras. Todas as regras respeitam o status registrado: uma
oportunidade encerrada (ganha, perdida, cancelada, faturada) nunca recebe
recomendação de avanço.
"""
from __future__ import annotations

import os

from .sinais import (
    ContextoInteligencia,
    Sinal,
    atividade_pendente,
    data,
    numero,
    registrar_provedor,
    status,
    texto,
)


def _limiar(nome: str, padrao: int) -> int:
    try:
        return max(1, int(os.getenv(f"CTI_INTELIGENCIA_{nome}", padrao)))
    except ValueError:
        return padrao


LIMIARES = {
    "FOLLOWUP_CRITICO_DIAS": _limiar("FOLLOWUP_CRITICO_DIAS", 7),
    "OPORTUNIDADE_PARADA_DIAS": _limiar("OPORTUNIDADE_PARADA_DIAS", 21),
    "OPORTUNIDADE_PARADA_CRITICA_DIAS": _limiar("OPORTUNIDADE_PARADA_CRITICA_DIAS", 45),
    "PROPOSTA_SEM_RETORNO_DIAS": _limiar("PROPOSTA_SEM_RETORNO_DIAS", 7),
    "PEDIDO_PARADO_DIAS": _limiar("PEDIDO_PARADO_DIAS", 14),
    "JANELA_FECHAMENTO_DIAS": _limiar("JANELA_FECHAMENTO_DIAS", 30),
    "PROBABILIDADE_QUENTE": _limiar("PROBABILIDADE_QUENTE", 70),
}

ETAPAS_ENCERRADAS = {"GANHO", "PERDIDO", "CANCELADO", "CANCELADA", "ENCERRADO", "ENCERRADA", "FATURADO", "CONCLUIDO"}
ETAPAS_POS_VENDA = {"PEDIDO", "DOSSIÊ", "DOSSIE", "CARRIER"}
STATUS_PROPOSTA_AGUARDANDO = {"EMITIDA", "ENVIADA", "VISUALIZADA", "EM_NEGOCIACAO", "AGUARDANDO_ACEITE", "APROVADA_INTERNA"}


def oportunidade_aberta(oportunidade: dict) -> bool:
    if oportunidade.get("encerrada"):
        return False
    if texto(oportunidade.get("data_fechamento_real")):
        return False
    return status(oportunidade.get("etapa") or oportunidade.get("status_oportunidade")) not in ETAPAS_ENCERRADAS


def _rotas_oportunidade(oid: str) -> tuple[str, str]:
    return f"/oportunidades/{oid}", f"/crm-app/oportunidades/{oid}"


def _nome(oportunidade: dict) -> str:
    return texto(oportunidade.get("cliente_nome")) or "Cliente não identificado"


def ultimo_contato(oportunidade: dict, contexto: ContextoInteligencia):
    """Data mais recente de qualquer movimento registrado na oportunidade."""
    candidatos = [data(oportunidade.get("updated_at")), data(oportunidade.get("created_at"))]
    for atividade in contexto.atividades_da_oportunidade(texto(oportunidade.get("oportunidade_id"))):
        for campo in ("concluida_em", "updated_at", "created_at"):
            candidatos.append(data(atividade.get(campo)))
        data_atividade = data(atividade.get("data"))
        if data_atividade and data_atividade <= contexto.hoje:
            candidatos.append(data_atividade)
    validos = [item for item in candidatos if item and item <= contexto.hoje]
    return max(validos) if validos else None


@registrar_provedor("agenda", modulo="atividades", descricao="Follow-ups atrasados e compromissos do dia.")
def provedor_agenda(contexto: ContextoInteligencia) -> list[Sinal]:
    valores = {texto(o.get("oportunidade_id")): numero(o.get("valor")) for o in contexto.oportunidades}
    sinais: list[Sinal] = []
    for atividade in contexto.atividades:
        if not atividade_pendente(atividade):
            continue
        quando = data(atividade.get("data"))
        if not quando or quando > contexto.hoje:
            continue
        atividade_id = texto(atividade.get("id"))
        cliente = texto(atividade.get("cliente_nome")) or texto(atividade.get("parceiro_nome")) or "Sem cliente vinculado"
        assunto = texto(atividade.get("titulo")) or texto(atividade.get("tipo")).title() or "Atividade comercial"
        oid = texto(atividade.get("oportunidade_id"))
        valor = valores.get(oid, 0.0)
        responsavel = texto(atividade.get("responsavel_id") or atividade.get("usuario_id"))
        if quando == contexto.hoje:
            sinais.append(Sinal(
                codigo="AGENDA_HOJE", categoria="acao", severidade="media",
                titulo=f"Hoje: {assunto} — {cliente}",
                explicacao="Compromisso comercial agendado para hoje.",
                acao_recomendada="Realize o contato e registre o resultado logo em seguida para manter o histórico vivo.",
                entidade_tipo="atividade", entidade_id=atividade_id, cliente_nome=cliente, cliente_id=texto(atividade.get("cliente_id")), responsavel_id=responsavel,
                valor=valor, dias=0, rota="/atividades", rota_app="/crm-app/atividades",
                evidencias=(f"Atividade {atividade_id} com data {quando.isoformat()}",),
            ))
            continue
        atraso = (contexto.hoje - quando).days
        sinais.append(Sinal(
            codigo="FOLLOWUP_ATRASADO", categoria="acao",
            severidade="alta" if atraso >= LIMIARES["FOLLOWUP_CRITICO_DIAS"] else "media",
            titulo=f"Follow-up atrasado há {atraso} dia{'s' if atraso != 1 else ''}: {cliente}",
            explicacao=f"“{assunto}” estava previsto para {quando.strftime('%d/%m/%Y')} e continua pendente.",
            acao_recomendada="Faça o contato hoje; se não fizer mais sentido, conclua ou reagende a atividade com o motivo.",
            entidade_tipo="atividade", entidade_id=atividade_id, cliente_nome=cliente, cliente_id=texto(atividade.get("cliente_id")), responsavel_id=responsavel,
            valor=valor, dias=atraso, rota="/atividades", rota_app="/crm-app/atividades",
            evidencias=(f"Atividade {atividade_id} pendente desde {quando.isoformat()}",),
        ))
    return sinais


@registrar_provedor("pipeline", modulo="oportunidades", descricao="Negócios parados, sem próximo passo, vencidos ou prontos para fechar.")
def provedor_pipeline(contexto: ContextoInteligencia) -> list[Sinal]:
    sinais: list[Sinal] = []
    for oportunidade in contexto.oportunidades:
        if not oportunidade_aberta(oportunidade):
            continue
        etapa = status(oportunidade.get("etapa"))
        if etapa in ETAPAS_POS_VENDA:
            continue  # tratado pelo provedor de pedidos
        oid = texto(oportunidade.get("oportunidade_id"))
        if not oid:
            continue
        rota, rota_app = _rotas_oportunidade(oid)
        cliente = _nome(oportunidade)
        valor = numero(oportunidade.get("valor"))
        responsavel = texto(oportunidade.get("responsavel_id"))
        titulo_negocio = texto(oportunidade.get("titulo")) or "Oportunidade comercial"
        base = dict(entidade_tipo="oportunidade", entidade_id=oid, cliente_nome=cliente, cliente_id=texto(oportunidade.get("cliente_id")), responsavel_id=responsavel, valor=valor, rota=rota, rota_app=rota_app)

        previsto = data(oportunidade.get("data_fechamento_prevista"))
        if previsto and previsto < contexto.hoje:
            atraso = (contexto.hoje - previsto).days
            sinais.append(Sinal(
                codigo="FECHAMENTO_VENCIDO", categoria="risco", severidade="alta",
                titulo=f"Previsão de fechamento vencida: {cliente}",
                explicacao=f"{titulo_negocio} deveria fechar em {previsto.strftime('%d/%m/%Y')} ({atraso} dias atrás) e segue aberto.",
                acao_recomendada="Confirme com o cliente o novo prazo e atualize a previsão — ou encerre como perdido com o motivo.",
                dias=atraso, evidencias=(f"data_fechamento_prevista={previsto.isoformat()}", f"etapa={etapa or 'OPORTUNIDADE'}"), **base,
            ))

        contato = ultimo_contato(oportunidade, contexto)
        parado = (contexto.hoje - contato).days if contato else None
        aguardando_proposta = etapa == "PROPOSTA" or status(oportunidade.get("status_proposta")) in STATUS_PROPOSTA_AGUARDANDO
        if aguardando_proposta and parado is not None and parado >= LIMIARES["PROPOSTA_SEM_RETORNO_DIAS"]:
            numero_proposta = texto(oportunidade.get("proposta_numero"))
            sinais.append(Sinal(
                codigo="PROPOSTA_SEM_RETORNO", categoria="risco", severidade="alta",
                titulo=f"Proposta sem retorno há {parado} dias: {cliente}",
                explicacao=f"Proposta {numero_proposta or 'vigente'} enviada e sem nenhum movimento registrado desde {contato.strftime('%d/%m/%Y')}.",
                acao_recomendada="Ligue para o decisor, entenda objeções (preço, prazo, concorrente) e registre o retorno.",
                dias=parado, evidencias=(f"status_proposta={texto(oportunidade.get('status_proposta')) or etapa}", f"ultimo_movimento={contato.isoformat()}"), **base,
            ))
        elif parado is not None and parado >= LIMIARES["OPORTUNIDADE_PARADA_DIAS"]:
            sinais.append(Sinal(
                codigo="OPORTUNIDADE_PARADA", categoria="risco",
                severidade="alta" if parado >= LIMIARES["OPORTUNIDADE_PARADA_CRITICA_DIAS"] else "media",
                titulo=f"Negócio parado há {parado} dias: {cliente}",
                explicacao=f"{titulo_negocio} não tem interação registrada desde {contato.strftime('%d/%m/%Y')}.",
                acao_recomendada="Retome o contato com uma razão concreta (nova condição, disponibilidade, visita técnica).",
                dias=parado, evidencias=(f"ultimo_movimento={contato.isoformat()}",), **base,
            ))

        proximos = [
            a for a in contexto.atividades_da_oportunidade(oid)
            if atividade_pendente(a) and (data(a.get("data")) or contexto.hoje) >= contexto.hoje
        ]
        if not proximos:
            sinais.append(Sinal(
                codigo="SEM_PROXIMO_PASSO", categoria="acao", severidade="media",
                titulo=f"Sem próximo passo agendado: {cliente}",
                explicacao=f"{titulo_negocio} está aberto e não tem nenhuma atividade futura planejada.",
                acao_recomendada="Agende o próximo contato agora — negócio sem data marcada tende a esfriar.",
                dias=parado, evidencias=("nenhuma atividade pendente com data futura",), **base,
            ))

        probabilidade = numero(oportunidade.get("probabilidade"))
        probabilidade = probabilidade * 100 if 0 < probabilidade <= 1 else probabilidade
        if previsto and contexto.hoje <= previsto and (previsto - contexto.hoje).days <= LIMIARES["JANELA_FECHAMENTO_DIAS"] and probabilidade >= LIMIARES["PROBABILIDADE_QUENTE"]:
            faltam = (previsto - contexto.hoje).days
            sinais.append(Sinal(
                codigo="PRONTO_PARA_FECHAR", categoria="oportunidade", severidade="alta",
                titulo=f"Pronto para fechar: {cliente} ({int(probabilidade)}%)",
                explicacao=f"{titulo_negocio} tem {int(probabilidade)}% de chance e previsão de fechamento em {faltam} dia{'s' if faltam != 1 else ''}.",
                acao_recomendada="Priorize: remova a última objeção e conduza ao aceite da proposta.",
                dias=None, evidencias=(f"probabilidade={int(probabilidade)}", f"data_fechamento_prevista={previsto.isoformat()}"), **base,
            ))
    return sinais


@registrar_provedor("pedidos", modulo="pedidos", descricao="Pedidos em andamento sem movimento.")
def provedor_pedidos(contexto: ContextoInteligencia) -> list[Sinal]:
    sinais: list[Sinal] = []
    for oportunidade in contexto.oportunidades:
        etapa = status(oportunidade.get("etapa"))
        if etapa not in ETAPAS_POS_VENDA or not oportunidade_aberta(oportunidade):
            continue
        contato = ultimo_contato(oportunidade, contexto)
        parado = (contexto.hoje - contato).days if contato else None
        if parado is None or parado < LIMIARES["PEDIDO_PARADO_DIAS"]:
            continue
        pedido_id = texto(oportunidade.get("pedido_id"))
        oid = texto(oportunidade.get("oportunidade_id"))
        cliente = _nome(oportunidade)
        sinais.append(Sinal(
            codigo="PEDIDO_SEM_MOVIMENTO", categoria="risco", severidade="media",
            titulo=f"Pedido sem movimento há {parado} dias: {cliente}",
            explicacao=f"Pedido {texto(oportunidade.get('pedido_numero')) or pedido_id or ''} está na etapa {etapa.title()} sem atualização registrada.".replace("  ", " "),
            acao_recomendada="Confira dossiê, aprovação Carrier e prazo de entrega; atualize o cliente sobre o andamento.",
            entidade_tipo="pedido" if pedido_id else "oportunidade", entidade_id=pedido_id or oid,
            cliente_nome=cliente, cliente_id=texto(oportunidade.get("cliente_id")), responsavel_id=texto(oportunidade.get("responsavel_id")), valor=numero(oportunidade.get("valor")),
            dias=parado,
            rota=f"/pedidos/{pedido_id}" if pedido_id else f"/oportunidades/{oid}",
            rota_app=f"/crm-app/pedidos/{pedido_id}" if pedido_id else f"/crm-app/oportunidades/{oid}",
            evidencias=(f"etapa={etapa}", f"ultimo_movimento={contato.isoformat()}"),
        ))
    return sinais
