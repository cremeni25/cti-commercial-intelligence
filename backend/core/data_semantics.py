from __future__ import annotations

from typing import Any


NATUREZAS = {
    "ANFIR": {
        "natureza": "FATO_MERCADO_REALIZADO",
        "temporalidade": "PASSADO_CONFIRMADO",
        "origem_canonica": "cti_anfir",
        "pode_compor_funil": False,
        "pode_criar_oportunidade": False,
        "uso": ["INTELIGENCIA_MERCADO", "DASHBOARD_EXECUTIVO_REALIZADO", "ANALYTICS", "IA"],
    },
    "CRM": {
        "natureza": "PROCESSO_COMERCIAL_OPERACIONAL",
        "temporalidade": "CORRENTE_E_HISTORICA",
        "origem_canonica": "crm",
        "pode_compor_funil": True,
        "uso": ["CRM_APP", "FUNIL", "DASHBOARD_EXECUTIVO_EM_CURSO", "IA"],
    },
    "FUNIL": {
        "natureza": "CICLO_DE_OPORTUNIDADE",
        "temporalidade": "ABERTA_OU_ENCERRADA",
        "origem_canonica": "crm_oportunidades",
        "pode_compor_funil": True,
        "uso": ["PIPELINE", "FORECAST", "DASHBOARD_EXECUTIVO_EM_CURSO", "IA"],
    },
}

DASHBOARDS = {
    "DASHBOARD_EXECUTIVO": {
        "realizado": "ANFIR",
        "em_curso": "FUNIL",
        "regra": "CAMADAS_SEPARADAS_SEM_FUSAO",
        "descricao": "Realizado usa fatos confirmados; em curso usa negócios vivos do CRM/Funil.",
    },
    "INTELIGENCIA_MERCADO": {
        "fonte": "ANFIR",
        "regra": "SOMENTE_FATOS_REALIZADOS",
        "metricas_funil_permitidas": False,
        "descricao": "Analisa mercado já realizado; não representa conversão, perdas de oportunidade ou pipeline.",
    },
}


def contrato_fonte(nome: str) -> dict[str, Any]:
    chave = str(nome or "").upper()
    if chave not in NATUREZAS:
        raise ValueError(f"Natureza de dados desconhecida: {nome}")
    return {"fonte": chave, **NATUREZAS[chave]}


def contrato_dashboard(nome: str) -> dict[str, Any]:
    chave = str(nome or "").upper()
    if chave not in DASHBOARDS:
        raise ValueError(f"Dashboard desconhecido: {nome}")
    return {"dashboard": chave, **DASHBOARDS[chave]}


def validar_correlacao(origem: str, destino: str) -> dict[str, Any]:
    origem = str(origem or "").upper()
    destino = str(destino or "").upper()
    if origem == "ANFIR" and destino in {"CRM", "FUNIL"}:
        return {
            "permitido": True,
            "modo": "CORRELACAO_ANALITICA",
            "fusao_registros": False,
            "promocao_automatica": False,
        }
    return {
        "permitido": origem in NATUREZAS and destino in NATUREZAS,
        "modo": "MESMA_NATUREZA" if origem == destino else "CONTRATO_ESPECIFICO_NECESSARIO",
        "fusao_registros": origem == destino,
        "promocao_automatica": False,
    }
