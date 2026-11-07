"""Funil de vendas atual e NEGOCIAÇÕES como fontes da IA Comercial.

Mesma regra do histórico comercial homologado: os dados trazem a carteira de
toda a equipe, então só o ADMIN_MASTER consulta pela IA até existir regra
determinística de carteira por vendedor nessas planilhas.
"""
from __future__ import annotations

from services import ia_comercial_universo as universo
from services import planilhas_comerciais

FONTES = {
    "funil_vendas_atual": (
        "Funil de vendas atual (planilha 'funil de vendas 2026' da Viena SP), abas BACKLOG, OPORTUNIDADE e "
        "INTERMEDIAÇÃO-OEM: cliente, equipamento, quantidade, valores, previsão, probabilidade, status "
        "reconstruído, motivo de perda, canal, implementadora e representante. Versão mais recente que o "
        "historico_comercial homologado; somente leitura, não é o Pipeline do CRM."
    ),
    "negociacoes_andamento": (
        "Planilha NEGOCIAÇÕES, aba EM ANDAMENTO (desde 2020): código da negociação, data, vendedor, cliente, CNPJ, "
        "linha e modelo do equipamento, quantidade, valores, condição de pagamento, instalação, canal, data de "
        "follow-up e status escrito pela equipe (crédito, documentação, faturamento etc.)."
    ),
    "vendas_realizadas": (
        "Planilha NEGOCIAÇÕES, aba VENDAS (desde 2022): vendas faturadas por mês, com cliente, linha e modelo do "
        "equipamento, quantidade, valor unitário, valor de instalação, condição de pagamento, datas de emissão e "
        "instalação, instalador e vendedor. Use para histórico real de vendas, recorrência de cliente e mix."
    ),
}
_ORIGINAL = None
_ATIVADO = False


def _carregar_fontes_com_planilhas(usuario_id: str, tipo_usuario: str):
    fontes, metadados = _ORIGINAL(usuario_id, tipo_usuario)
    autorizado = str(tipo_usuario or "").upper() == "ADMIN_MASTER"
    for fonte in FONTES:
        try:
            fontes[fonte] = planilhas_comerciais.registros(fonte) if autorizado else []
        except Exception:
            fontes[fonte] = []
        metadados[fonte] = {"autorizado": autorizado, "total_registros": len(fontes[fonte]), "modo": "somente_leitura", "nao_promove_crm": True}
    return fontes, metadados


def ativar() -> None:
    global _ATIVADO, _ORIGINAL
    if _ATIVADO:
        return
    _ORIGINAL = universo._carregar_fontes
    universo.FONTES_PUBLICAS.update(FONTES)
    universo._carregar_fontes = _carregar_fontes_com_planilhas
    _ATIVADO = True


ativar()
