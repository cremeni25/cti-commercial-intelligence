from __future__ import annotations

from typing import Any

from . import ia_comercial_agente_crm as _agente
from .ia_comercial_artefatos import construir_artefatos, detectar_intencao_artefato


_ORIGINAL_GERAR_RESPOSTA = _agente.gerar_resposta_agente


def gerar_resposta_agente(
    mensagem: str,
    historico: list[dict[str, str]] | None,
    usuario_id: str,
    tipo_usuario: str,
) -> tuple[str, dict[str, Any]]:
    resposta_texto, metadados = _ORIGINAL_GERAR_RESPOSTA(
        mensagem=mensagem,
        historico=historico,
        usuario_id=usuario_id,
        tipo_usuario=tipo_usuario,
    )
    metadados = dict(metadados or {})
    solicitados = detectar_intencao_artefato(mensagem)
    if solicitados:
        artefatos = construir_artefatos(
            mensagem=mensagem,
            resposta_texto=resposta_texto,
            historico=historico or [],
            fontes=metadados.get("fontes") or [],
        )
        metadados["artefatos"] = artefatos
        metadados["ia009_artefatos_solicitados"] = sorted(solicitados)
        metadados["controle_artefatos"] = "geracao_deterministica_pos_sintese_sem_sql_livre"
        metadados["artefatos_auditaveis"] = True
    return resposta_texto, metadados


_agente.gerar_resposta_agente = gerar_resposta_agente
