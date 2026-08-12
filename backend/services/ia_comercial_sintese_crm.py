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
