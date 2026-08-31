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
        "descricao": "Resultado de mercado já encerrado e consolidado pela fonte Carrier/JOV.",
    },
    "CRM": {
        "natureza": "PROCESSO_COMERCIAL_OPERACIONAL",
        "temporalidade": "PRESENTE_OPERACIONAL",
        "origem_canonica": "crm",
        "pode_compor_funil": True,
        "uso": ["CRM_APP", "FUNIL", "DASHBOARD_EXECUTIVO_EM_CURSO", "IA"],
        "descricao": "Ação comercial diária: agenda, visita, prospecção, contato e desfecho operacional recente.",
    },
    "FUNIL": {
        "natureza": "CICLO_DE_OPORTUNIDADE",
        "temporalidade": "PASSADO_ENCERRADO_E_EM_CURSO_BACKLOG",
        "origem_canonica": "crm_oportunidades",
        "pode_compor_funil": True,
        "uso": ["PIPELINE", "FORECAST", "DASHBOARD_EXECUTIVO_EM_CURSO", "IA"],
        "descricao": "Ponte temporal entre ações recentes e resultados: contém negócios encerrados, backlog e prospecções em andamento.",
    },
}

DASHBOARDS = {
    "DASHBOARD_EXECUTIVO": {
        "realizado": "ANFIR",
        "em_curso": "FUNIL",
        "operacional": "CRM",
        "regra": "CAMADAS_SEPARADAS_SEM_FUSAO",
        "principio_transversal": "MESMA_VERDADE_FACTUAL_LEITURAS_DIFERENTES",
        "descricao": "ANFIR, Funil e CRM não são somados como universos independentes. São correlacionados por cliente/negócio mantendo cada fonte íntegra.",
    },
    "INTELIGENCIA_MERCADO": {
        "fonte": "ANFIR",
        "regra": "SOMENTE_FATOS_REALIZADOS",
        "metricas_funil_permitidas": False,
        "descricao": "Analisa mercado já realizado; não representa conversão, perdas de oportunidade ou pipeline.",
    },
}

CORRELACAO_TRANSVERSAL = {
    "entidade": "CLIENTE_NEGOCIO",
    "chaves_prioritarias": ["CNPJ", "CLIENTE_ID", "NOME_CIDADE_EXATOS_UNICOS", "CHASSI_QUANDO_APLICAVEL"],
    "fontes_preservadas": True,
    "fusao_dados_brutos": False,
    "regra_desfecho": "Uma cadeia CRM → Funil → ANFIR/Venda só é confirmada quando as evidências pertencem ao mesmo cliente reconciliado e respeitam a ordem temporal.",
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
    if origem in NATUREZAS and destino in NATUREZAS and origem != destino:
        return {
            "permitido": True,
            "modo": "CORRELACAO_ANALITICA",
            "transversal": True,
            "fusao_registros": False,
            "promocao_automatica": False,
            "contrato": CORRELACAO_TRANSVERSAL,
        }
    return {
        "permitido": origem in NATUREZAS and destino in NATUREZAS,
        "modo": "MESMA_NATUREZA" if origem == destino else "CONTRATO_ESPECIFICO_NECESSARIO",
        "fusao_registros": origem == destino,
        "promocao_automatica": False,
    }
