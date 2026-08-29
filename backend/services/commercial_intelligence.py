from collections import Counter

from core.data_semantics import contrato_dashboard, contrato_fonte
from services.anfir_market_intelligence import consolidar_inteligencia_mercado
from services.commercial_intelligence_v18 import (
    SEGMENTOS,
    _dimensao,
    _filtrar,
    _segmento,
    consolidar_inteligencia as _consolidar_inteligencia_v18,
    opcoes_filtros as _opcoes_filtros_v18,
)
from services.operational_filters import data_registro, resolver_ddd_registro


def _preparar_registro_anfir(registro):
    payload = dict(registro)
    data = data_registro(payload)
    # Esta camada trabalha exclusivamente com fatos ANFIR. A data usada pelo
    # motor legado deve representar a competência ANFIR resolvida, mesmo quando
    # um registro histórico carrega uma data_venda técnica conflitante.
    # A correção ocorre somente na cópia analítica em memória; o banco não é
    # reescrito por esta função.
    if data:
        payload["data_venda"] = data.isoformat()
    ddd = resolver_ddd_registro(payload)
    if ddd and not payload.get("ddd"):
        payload["ddd"] = ddd
    return payload


def _tendencia_trimestral_comparavel(registros):
    """Compara os dois últimos trimestres completos da mesma competência anual.

    ANFIR é uma fotografia mensal de mercado. Um trimestre ainda em formação não
    deve ser comparado a um trimestre completo, e a fotografia corrente não deve
    ser comparada automaticamente a snapshots históricos metodologicamente
    distintos. Por isso, a tendência executiva usa apenas trimestres completos
    dentro do mesmo ano/fonte quando houver dois deles disponíveis.
    """
    datas = [data_registro(registro) for registro in registros]
    datas = [data for data in datas if data]
    if not datas:
        return None

    ultima = max(datas)
    trimestre_ultima = (ultima.month - 1) // 3 + 1
    trimestre_completo = trimestre_ultima if ultima.month % 3 == 0 else trimestre_ultima - 1
    if trimestre_completo < 2:
        return None

    trimestre_anterior = trimestre_completo - 1
    ano = ultima.year

    def no_trimestre(data, trimestre):
        return data.year == ano and ((data.month - 1) // 3 + 1) == trimestre

    atual = sum(1 for data in datas if no_trimestre(data, trimestre_completo))
    anterior = sum(1 for data in datas if no_trimestre(data, trimestre_anterior))
    if not anterior:
        return None

    diferenca = atual - anterior
    percentual = round(diferenca / anterior * 100, 2)
    return {
        "atual": atual,
        "anterior": anterior,
        "diferenca": diferenca,
        "percentual": percentual,
        "direcao": "alta" if diferenca > 0 else "queda" if diferenca < 0 else "estavel",
        "periodo_atual": f"{ano}-Q{trimestre_completo}",
        "periodo_anterior": f"{ano}-Q{trimestre_anterior}",
        "metodo": "TRIMESTRES_COMPLETOS_MESMA_FONTE",
        "comparavel": True,
    }


def opcoes_filtros(registros, filtros):
    base = [_preparar_registro_anfir(item) for item in (registros or [])]
    return _opcoes_filtros_v18(base, filtros)


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

    # O comparativo de segmentos precisa refletir exatamente o mesmo recorte
    # temporal e dimensional da leitura geral. Removemos apenas o filtro de
    # segmento para contar TR/DT/DD dentro do universo ativo, sem voltar à base
    # histórica completa.
    filtros_segmentos = {**(filtros or {}), "segmento": "GERAL"}
    universo_segmentos = _filtrar(base, filtros_segmentos)
    segmentos = Counter(_segmento(registro) for registro in universo_segmentos)

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

    # Quando não há uma comparação histórica explicitamente aplicável, usamos
    # uma tendência interna comparável da própria fotografia ANFIR. Isso evita
    # afirmar crescimento/queda a partir de janelas históricas incompatíveis.
    if not anteriores:
        tendencia = _tendencia_trimestral_comparavel(analisados)
        if tendencia:
            mercado["comparacao"] = tendencia

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
