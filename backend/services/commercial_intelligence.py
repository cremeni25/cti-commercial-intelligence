from collections import Counter

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

    resultado["resumo"] = {
        "total_registros": kpis["volume"],
        "valor_total": kpis["valor"],
        "clientes_unicos": len({_dimensao(registro, "cliente") for registro in analisados}),
        "implementadoras_unicas": len({_dimensao(registro, "implementadora") for registro in analisados}),
    }
    resultado["segmentos"] = {
        nome: segmentos.get(nome, 0)
        for nome in ("TR", "DT", "DD", "UNKNOWN")
    }
    resultado["implementadoras"] = resultado["rankings"]["implementadora"][:10]

    return resultado
