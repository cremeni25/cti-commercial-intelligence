"""Dicionário comercial do CTI: um nome para cada coisa.

As telas, os relatórios, a IA e (na próxima etapa) o agente e o atendimento
automático usam estes termos. Os sinônimos antigos continuam aceitos nas
buscas e importações, mas são traduzidos para o termo oficial.
"""
from __future__ import annotations

GLOSSARIO: list[dict[str, object]] = [
    {"termo": "Cliente", "definicao": "Empresa identificada pelo CNPJ. Todo o histórico (negócios, visitas, compras, frota) pertence ao cliente, não a quem o atendeu.", "sinonimos": ["empresa", "conta", "razão social", "transportadora"]},
    {"termo": "Responsável comercial", "definicao": "Pessoa da equipe que cuida do cliente hoje. Pode mudar; o histórico de quem foi responsável fica guardado.", "sinonimos": ["vendedor", "representante", "consultor", "carteira de"]},
    {"termo": "Carteira", "definicao": "Conjunto de clientes de um responsável comercial.", "sinonimos": ["território", "região"]},
    {"termo": "Negócio", "definicao": "Oportunidade de venda para um cliente, do primeiro contato ao ganho ou perda.", "sinonimos": ["oportunidade", "negociação", "deal"]},
    {"termo": "Proposta", "definicao": "Documento comercial enviado ao cliente dentro de um negócio.", "sinonimos": ["orçamento", "cotação"]},
    {"termo": "Pedido", "definicao": "Negócio fechado em formalização e faturamento.", "sinonimos": ["ordem", "PO"]},
    {"termo": "Venda", "definicao": "Pedido faturado. Conta como compra do cliente.", "sinonimos": ["faturamento", "NF"]},
    {"termo": "Atividade", "definicao": "Ação registrada com o cliente: visita, ligação, WhatsApp, e-mail, reunião. Fica no nome de quem a fez.", "sinonimos": ["interação", "follow-up", "visita"]},
    {"termo": "Frota registrada", "definicao": "Equipamentos de refrigeração do cliente identificados na base de mercado (ANFIR), de qualquer fabricante.", "sinonimos": ["frota", "parque instalado"]},
    {"termo": "Implementadora", "definicao": "Fabricante do baú/carroceria onde o equipamento é instalado.", "sinonimos": ["implementador", "encarroçadora"]},
    {"termo": "Concorrência", "definicao": "Equipamentos de outros fabricantes na frota do cliente (Thermo King e nacionais).", "sinonimos": ["concorrente", "TK", "nacional"]},
    {"termo": "Grupo do cliente", "definicao": "Setorização automática: cliente ativo (comprou em até 24 meses), cliente inativo, prospect com frota e prospect.", "sinonimos": ["segmento de relacionamento", "status do cliente"]},
    {"termo": "Porte", "definicao": "Tamanho da frota registrada: grande (20+), média (5 a 19), pequena (1 a 4).", "sinonimos": ["tamanho da frota"]},
    {"termo": "Janela de renovação", "definicao": "Cliente cujo equipamento mais novo conhecido tem 6 anos ou mais: momento de oferecer troca.", "sinonimos": ["renovação de frota", "recompra"]},
    {"termo": "Acervo comercial", "definicao": "Todo o histórico da empresa, preservado mesmo quando pessoas saem: cópias semanais e exportação completa.", "sinonimos": ["histórico", "backup"]},
]


def termo_oficial(palavra: str) -> str | None:
    alvo = str(palavra or "").strip().casefold()
    for item in GLOSSARIO:
        if alvo == str(item["termo"]).casefold() or alvo in {str(s).casefold() for s in item["sinonimos"]}:  # type: ignore[union-attr]
            return str(item["termo"])
    return None
