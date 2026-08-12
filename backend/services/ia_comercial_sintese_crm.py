from __future__ import annotations

from typing import Any

from services import ia_comercial_sintese_crm_legacy as _legacy


def _auditar_ferramentas_multifonte(
    metadados: dict[str, Any],
    evidencias: set[str],
) -> None:
    """Compatibiliza a auditoria IA-004 com a leitura universal CTI.

    A arquitetura universal já valida fonte, RBAC e modo somente leitura no
    backend. Para execuções que exigem universo_cti, a IA-004 deve apenas
    impedir que uma ferramenta CTI fora das duas interfaces universais escape
    para a execução; não deve reaplicar a antiga allowlist por domínio.
    """
    if "universo_cti" not in evidencias:
        return _legacy._auditar_ferramentas_multifonte_original(metadados, evidencias)

    permitidas = {"catalogar_universo_cti", "consultar_universo_cti"}
    indevidas: list[str] = []
    for item in metadados.get("ferramentas") or []:
        if not isinstance(item, dict) or item.get("tipo") != "CTI":
            continue
        nome = str(item.get("ferramenta") or "")
        if nome not in permitidas:
            indevidas.append(nome or "ferramenta_cti_desconhecida")

    if indevidas:
        raise _legacy.base.IAComercialOpenAIError(
            "A execução multi-fonte tentou consultar uma fonte interna fora do escopo universal autorizado.",
            codigo="AGENT_MULTISOURCE_SCOPE_VIOLATION",
        )


# Preserva a implementação histórica como fachada, mas troca somente o ponto
# incompatível com universo_cti + web.
_legacy._auditar_ferramentas_multifonte_original = _legacy._auditar_ferramentas_multifonte
_legacy._auditar_ferramentas_multifonte = _auditar_ferramentas_multifonte

# Reexporta toda a API histórica, inclusive helpers privados usados pelas
# camadas IA-006/IA-007 e pela suíte de regressão.
globals().update(
    {
        nome: valor
        for nome, valor in vars(_legacy).items()
        if not nome.startswith("__")
    }
)


# A leitura universal resolveu descoberta/consulta, mas rankings executivos
# também precisam preservar a semântica da métrica. O modelo não pode elevar
# frequência de registros internos a porte, liderança ou ranking nacional sem
# evidência externa comparável.
_ORIGINAL_SINTESE_UNIVERSAL = _legacy.crm._instrucao_sintese_final_universal


def _instrucao_sintese_final_universal_com_metricas(evidencias: set[str]) -> str:
    instrucao = _ORIGINAL_SINTESE_UNIVERSAL(evidencias)
    if "universo_cti" not in evidencias:
        return instrucao

    regras = (
        " REGRA UNIVERSAL DE RANKING E MÉTRICA: quando a consulta interna usar count, sum, avg, min, max "
        "ou outra métrica, nomeie explicitamente essa métrica na resposta. Um ranking por quantidade/frequência "
        "de registros do CTI é somente um ranking do universo CTI consultado; não o chame de maior do Brasil, "
        "líder nacional, maior empresa, maior fabricante, maior implementadora, maior cliente ou equivalente por porte "
        "sem uma fonte externa que sustente exatamente essa conclusão por uma métrica comparável. "
        "Se o pedido do usuário usar 'maiores' e os dados internos sustentarem apenas frequência histórica, responda "
        "primeiro 'mais frequentes/maior número de registros no CTI' e trate o ranking nacional como questão externa separada. "
        "Não converta volume histórico de ocorrências em faturamento, produção, market share, frota, capacidade instalada "
        "ou porte empresarial. "
        " REGRA DE CRUZAMENTO CTI + WEB: a web deve validar/enriquecer as mesmas entidades retornadas pelo CTI quando o "
        "objetivo for cruzamento. Se a web trouxer outras entidades ou outro ranking, apresente-o em seção separada como "
        "ranking externo e informe a métrica/fonte; não misture as listas como se fossem uma única classificação. "
        "Se não houver fonte externa comparável para todas as entidades ou para a métrica nacional solicitada, declare "
        "essa limitação explicitamente em vez de concluir que o ranking interno representa o Brasil. "
        " REGRA DE AFIRMAÇÃO EXECUTIVA: não escreva conclusões genéricas como 'isso demonstra relevância', 'forte presença', "
        "'liderança' ou 'competitividade' como fatos, salvo quando uma evidência da execução sustentar diretamente a conclusão; "
        "caso contrário, qualifique como inferência ou omita."
    )
    return instrucao + regras


_legacy.crm._instrucao_sintese_final_universal = _instrucao_sintese_final_universal_com_metricas

_INSTRUCOES_RANKING_WEB = """

RANKINGS, PORTE E COMPARAÇÃO EXTERNA — REGRA TRANSVERSAL:
- Antes da síntese, preserve a métrica de cada consulta. `count` mede quantidade/frequência de registros; não mede automaticamente porte, produção, faturamento, participação de mercado ou liderança nacional.
- Quando o usuário pedir maiores, líderes, principais ou ranking nacional e houver web disponível, procure evidência externa da MESMA categoria e uma métrica objetiva comparável (por exemplo produção, emplacamentos, faturamento, market share ou ranking setorial publicado).
- Se a web não fornecer uma métrica comparável e verificável, não force um ranking nacional. Entregue o ranking interno com seu critério real e declare que a posição nacional não pôde ser comprovada pela evidência externa coletada.
- Em cruzamento CTI + web, priorize validar as entidades retornadas pelo CTI. Entidades externas adicionais podem ser relevantes, mas devem aparecer separadas e nunca substituir silenciosamente o ranking interno.
"""

if _INSTRUCOES_RANKING_WEB not in _legacy.crm._INSTRUCOES_UNIVERSAIS:
    _legacy.crm._INSTRUCOES_UNIVERSAIS += _INSTRUCOES_RANKING_WEB
