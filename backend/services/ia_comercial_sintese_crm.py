from __future__ import annotations

from typing import Any

from services.ia_comercial_sintese_factual import sintetizar_fatos_execucao as sintetizar_fatos_base


EVIDENCIAS_CRM = {"propostas", "pedidos", "atividades"}


def sintetizar_fatos_execucao(
    pergunta_atual: str,
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
):
    evidencias = {str(x) for x in (metadados.get("evidencias_atendidas") or [])}
    if evidencias & EVIDENCIAS_CRM:
        return None, {
            "controle_sintese_factual": "crm_operacional_semantico_preservado",
            "controle_crm_operacional": "semantica_backend_e_vinculos_resolvidos",
            "crm_evidencias": sorted(evidencias & EVIDENCIAS_CRM),
        }
    return sintetizar_fatos_base(pergunta_atual, metadados, usuario_id, tipo_usuario)
