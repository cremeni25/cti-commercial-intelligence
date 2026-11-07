"""Tabela de aplicação como fonte da IA Comercial.

Permite à IA responder "qual equipamento atende um baú de 5,5 m a -18 °C?"
com os dados oficiais da tabela (uma linha por equipamento x tamanho de baú),
sem depender do PDF.
"""
from __future__ import annotations

from typing import Any

from services import ia_comercial_universo as universo

FONTE = "tabela_aplicacao"
DESCRICAO = (
    "Tabela de aplicação Carrier/Viena: para cada equipamento (modelo, linha, refrigerante, acoplamento, "
    "isolamento) e cada tamanho de baú (comprimento em metros e volume em m³), a temperatura mínima "
    "alcançada em °C (campo temperatura_minima_c). Um equipamento atende uma temperatura desejada quando "
    "temperatura_minima_c é menor ou igual a ela. Vale para baús novos com o isolamento descrito em condicao. "
    "Use para indicar o equipamento adequado a um baú e a uma temperatura."
)
_ORIGINAL = None
_ATIVADO = False


def linhas_tabela() -> list[dict[str, Any]]:
    from services.catalogo_vitrine import tabela_aplicacao

    tabela = tabela_aplicacao()
    if not tabela:
        return []
    linhas = []
    for equipamento in tabela["equipamentos"]:
        for tamanho, temperatura in zip(tabela["tamanhos"], equipamento["temperaturas"]):
            if temperatura is None:
                continue
            linhas.append({
                "modelo": equipamento["modelo"],
                "linha": equipamento["linha"],
                "refrigerante": equipamento.get("refrigerante"),
                "acoplamento": equipamento.get("acoplamento"),
                "isolamento_mm": equipamento.get("isolamento_mm"),
                "tamanho_bau": tamanho["codigo"],
                "comprimento_bau_m": tamanho["comprimento_m"],
                "volume_bau_m3": tamanho["volume_m3"],
                "temperatura_minima_c": temperatura,
                "condicao": tabela.get("condicao"),
            })
    return linhas


def _carregar_fontes_com_aplicacao(usuario_id: str, tipo_usuario: str):
    fontes, metadados = _ORIGINAL(usuario_id, tipo_usuario)
    try:
        fontes[FONTE] = linhas_tabela()
    except Exception:
        fontes[FONTE] = []
    metadados[FONTE] = {"total_registros": len(fontes[FONTE]), "modo": "somente_leitura", "origem": "TABELA_APLICACAO"}
    return fontes, metadados


def ativar() -> None:
    global _ATIVADO, _ORIGINAL
    if _ATIVADO:
        return
    _ORIGINAL = universo._carregar_fontes
    universo.FONTES_PUBLICAS[FONTE] = DESCRICAO
    universo._carregar_fontes = _carregar_fontes_com_aplicacao
    _ATIVADO = True


ativar()
