from collections import Counter

from core.data_semantics import contrato_dashboard, contrato_fonte
from services.anfir_market_intelligence import consolidar_inteligencia_mercado
from services.commercial_intelligence_v18 import (
    SEGMENTOS,
    _dimensao,
    _filtrar,
    _segmento,
    consolidar_inteligencia as _consolidar_inteligencia_v18,
    opcoes_filtros,
)
from services.operational_filters import data_registro, resolver_ddd_registro


def _preparar_registro_anfir(registro):
    payload = dict(registro)
    data = data_registro(payload)
    if data and not payload.get("data_venda"):
        payload["data_venda"] = data.isoformat()
    ddd = resolver_ddd_registro(payload)
    if ddd and not payload.get("ddd"):
        payload["ddd"] = ddd
    return payload


def consolidar_inteligencia(registros, contexto="brasil", segmento="GERAL", filtros=None, comparacao=None):
    base = [_preparar_registro_anfir(item) for item in (registros or [])]
    resultado = _consolidar_inteligencia_v18(
        base,
        contexto=contexto,
        segmento=segmento,
        filtros=filtros,
        comparacao=comparacao,
    )

    filtros_efetivos = {**(filtros or {}), "segmento": segmento if segmento in SEGMENTOS else "GERAL"}
    analisados = _filtrar(base, filtros_efetivos)
    anteriores = _filtrar(base, comparacao) if comparacao else []
    kpis = resultado["kpis"]
    segmentos = Counter(_segmento(registro) for registro in base)

    clientes_unicos = len({_dimensao(registro, "cliente") for registro in analisados})
    implementadoras_unicas = len({_dimensao(registro, "implementadora") for registro in analisados})

    resultado["resumo"] = {
        "total_registros": kpis["volume"],
        "valor_total": kpis["valor"],
        "clientes_unicos": clientes_unicos,
        "implementadoras_unicas": implementadoras_unicas,
    }
    resultado["segmentos"] = {nome: segmentos.get(nome, 0) for nome in ("TR", "DT", "DD", "UNKNOWN")}
    resultado["implementadoras"] = resultado["rankings"]["implementadora"][:10]

    resultado["kpis"]["conversao"] = None
    resultado["kpis"]["comparacoes"].pop("conversao", None)
    for ponto in resultado.get("serie_temporal", []):
        ponto["conversao"] = None
        ponto["perdas"] = None

    resultado["metricas_funil"] = {
        "disponiveis": False,
        "motivo": "A origem desta leitura é ANFIR: fatos de mercado já realizados, não oportunidades do Funil.",
    }
    resultado["oportunidades_perdidas"] = {
        "disponivel": False,
        "quantidade": None,
        "valor": None,
        "motivo": "Oportunidades perdidas devem ser calculadas exclusivamente a partir do CRM/Funil.",
    }
    resultado["clientes_sem_registro_recente"] = [
        {
            "nome": item.get("nome"),
            "dias_sem_registro": item.get("dias_sem_compra"),
            "ultimo_registro": item.get("ultima_compra"),
        }
        for item in resultado.get("clientes_inativos", [])
    ]
    resultado["clientes_inativos"] = []

    resultado["inteligencia_mercado"] = consolidar_inteligencia_mercado(analisados, anteriores)
    mercado = resultado["inteligencia_mercado"]["mercado"]
    for chave in ("competencia_min", "competencia_max"):
        if mercado.get(chave):
            mercado[chave] = mercado[chave].isoformat()

    resultado.setdefault("metadata", {}).update({
        "origem": "cti_anfir",
        "natureza_dados": "FATO_MERCADO_REALIZADO",
        "contrato_fonte": contrato_fonte("ANFIR"),
        "contrato_dashboard": contrato_dashboard("INTELIGENCIA_MERCADO"),
        "motor_mercado": "ANFIR_INTELLIGENCE_002",
        "nao_representa": ["FUNIL", "PIPELINE", "OPORTUNIDADE_ABERTA", "CONVERSAO_CRM"],
    })

    return resultado
