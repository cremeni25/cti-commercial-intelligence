from collections import Counter

from core.data_semantics import contrato_dashboard, contrato_fonte
from services.commercial_intelligence_v18 import (
    SEGMENTOS,
    STATUS_GANHOS,
    STATUS_PERDIDOS,
    _dimensao,
    _filtrar,
    _segmento,
    consolidar_inteligencia as _consolidar_inteligencia_v18,
    opcoes_filtros,
)


def consolidar_inteligencia(registros, contexto="brasil", segmento="GERAL", filtros=None, comparacao=None):
    """Consolida inteligência exclusivamente sobre fatos realizados da base ANFIR.

    O motor v18 permanece responsável por filtros/rankings e série histórica, mas
    métricas próprias de Funil não são publicadas como verdade quando a origem é
    ``cti_anfir``.
    """
    base = [dict(item) for item in (registros or [])]
    resultado = _consolidar_inteligencia_v18(
        base,
        contexto=contexto,
        segmento=segmento,
        filtros=filtros,
        comparacao=comparacao,
    )

    filtros_efetivos = {**(filtros or {}), "segmento": segmento if segmento in SEGMENTOS else "GERAL"}
    analisados = _filtrar(base, filtros_efetivos)
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
    resultado["segmentos"] = {
        nome: segmentos.get(nome, 0)
        for nome in ("TR", "DT", "DD", "UNKNOWN")
    }
    resultado["implementadoras"] = resultado["rankings"]["implementadora"][:10]

    # ANFIR é fato de mercado realizado. Conversão e perda de oportunidade
    # pertencem ao CRM/Funil e não podem ser inferidas desta base.
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

    resultado.setdefault("metadata", {}).update({
        "origem": "cti_anfir",
        "natureza_dados": "FATO_MERCADO_REALIZADO",
        "contrato_fonte": contrato_fonte("ANFIR"),
        "contrato_dashboard": contrato_dashboard("INTELIGENCIA_MERCADO"),
        "nao_representa": ["FUNIL", "PIPELINE", "OPORTUNIDADE_ABERTA", "CONVERSAO_CRM"],
    })

    return resultado
