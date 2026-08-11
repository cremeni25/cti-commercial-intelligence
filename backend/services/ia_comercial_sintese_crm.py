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
    fontes_web = [
        fonte for fonte in (metadados.get("fontes") or [])
        if isinstance(fonte, dict) and fonte.get("url")
    ]

    if "web" in evidencias:
        return None, {
            "controle_sintese_factual": "ia003_web_preservada_agente_com_fontes",
            "controle_web_proveniencia": "fontes_url_execucao_atual",
            "web_fontes_sintese": len(fontes_web),
            "web_urls_sintese": [str(fonte.get("url")) for fonte in fontes_web],
            "crm_evidencias": sorted(evidencias & EVIDENCIAS_CRM),
        }

    if evidencias & EVIDENCIAS_CRM:
        return None, {
            "controle_sintese_factual": "crm_operacional_semantico_preservado",
            "controle_crm_operacional": "semantica_backend_e_vinculos_resolvidos",
            "crm_evidencias": sorted(evidencias & EVIDENCIAS_CRM),
        }
    return sintetizar_fatos_base(pergunta_atual, metadados, usuario_id, tipo_usuario)
