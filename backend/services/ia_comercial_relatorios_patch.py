from __future__ import annotations

from typing import Any

from . import ia_comercial_agente_crm as _crm

_PREFIXO_RELATORIO_CRM = "RELATÓRIO CRM —"
_ORIGINAL_GERAR_RESPOSTA_RELATORIOS = _crm.gerar_resposta_agente


def eh_relatorio_crm_isolado(mensagem: str) -> bool:
    return str(mensagem or "").lstrip().upper().startswith(_PREFIXO_RELATORIO_CRM)


def historico_para_execucao(mensagem: str, historico: list[dict[str, Any]] | None):
    if eh_relatorio_crm_isolado(mensagem):
        return []
    return historico or []


def _gerar_resposta_agente_relatorio_isolado(*, mensagem: str, historico, usuario_id: str, tipo_usuario: str):
    isolado = eh_relatorio_crm_isolado(mensagem)
    resposta, metadados = _ORIGINAL_GERAR_RESPOSTA_RELATORIOS(
        mensagem=mensagem,
        historico=historico_para_execucao(mensagem, historico),
        usuario_id=usuario_id,
        tipo_usuario=tipo_usuario,
    )
    if isolado:
        metadados = dict(metadados or {})
        metadados["controle_relatorio_crm"] = "execucao_tematica_isolada_sem_historico"
        metadados["historico_relatorio_reutilizado"] = False
        metadados["snapshot_relatorio_origem"] = "execucao_atual"
    return resposta, metadados


_crm.gerar_resposta_agente = _gerar_resposta_agente_relatorio_isolado
