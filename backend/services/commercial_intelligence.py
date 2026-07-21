from collections import Counter, defaultdict
from datetime import datetime, timezone

from core.cti_taxonomy import normalizar_implementadora, normalizar_produto

SEGMENTOS = {"GERAL", "TR", "DT", "DD", "UNKNOWN"}


def _segmento(registro):
    produto = normalizar_produto(
        registro.get("produto")
        or registro.get("linha")
        or registro.get("modelo_equipamento")
        or registro.get("modelo")
    )
    return produto if produto in {"TR", "DT", "DD"} else "UNKNOWN"


def _valor(registro):
    try:
        return float(registro.get("valor") or 0)
    except (TypeError, ValueError):
        return 0.0


def _data(registro):
    return registro.get("data_venda") or registro.get("data") or registro.get("created_at")


def consolidar_inteligencia(registros, contexto="brasil", segmento="GERAL"):
    segmento = str(segmento or "GERAL").upper()
    if segmento not in SEGMENTOS:
        segmento = "GERAL"

    base = [dict(item) for item in (registros or [])]
    analisados = base if segmento == "GERAL" else [r for r in base if _segmento(r) == segmento]

    por_segmento = Counter(_segmento(r) for r in base)
    por_implementadora = Counter()
    por_estado = Counter()
    por_cliente = Counter()
    por_fabricante = Counter()
    valores = defaultdict(float)

    datas = []
    for registro in analisados:
        implementadora = normalizar_implementadora(
            registro.get("implementadora") or registro.get("implementador")
        ) or "NÃO INFORMADA"
        estado = str(registro.get("estado") or "NÃO INFORMADO").upper()
        cliente = str(registro.get("empresa") or registro.get("cliente") or "NÃO INFORMADO").strip()
        fabricante = str(registro.get("fabricante_equipamento") or "NÃO INFORMADO").upper()

        por_implementadora[implementadora] += 1
        por_estado[estado] += 1
        por_cliente[cliente] += 1
        por_fabricante[fabricante] += 1
        valores[estado] += _valor(registro)
        if _data(registro):
            datas.append(str(_data(registro)))

    total = len(analisados)
    market_share = [
        {
            "fabricante": nome,
            "quantidade": quantidade,
            "participacao_percentual": round((quantidade / total * 100), 2) if total else 0,
        }
        for nome, quantidade in por_fabricante.most_common()
    ]

    return {
        "metadata": {
            "contexto_operacional": contexto,
            "segmento": segmento,
            "periodo_analisado": {
                "inicio": min(datas) if datas else None,
                "fim": max(datas) if datas else None,
            },
            "ultima_atualizacao": datetime.now(timezone.utc).isoformat(),
            "origem": "cti_anfir",
            "criterio_calculo": "registros históricos concluídos, normalizados pela taxonomia oficial do CTI",
        },
        "resumo": {
            "total_registros": total,
            "valor_total": round(sum(_valor(r) for r in analisados), 2),
            "clientes_unicos": len(por_cliente),
            "implementadoras_unicas": len(por_implementadora),
        },
        "segmentos": {nome: por_segmento.get(nome, 0) for nome in ["TR", "DT", "DD", "UNKNOWN"]},
        "market_share": market_share,
        "implementadoras": [
            {"nome": nome, "quantidade": quantidade}
            for nome, quantidade in por_implementadora.most_common(10)
        ],
        "crescimento_regional": [
            {"estado": estado, "quantidade": quantidade, "valor": round(valores[estado], 2)}
            for estado, quantidade in por_estado.most_common()
        ],
        "clientes": [
            {"nome": nome, "quantidade": quantidade}
            for nome, quantidade in por_cliente.most_common(10)
        ],
        "tendencias": {
            "segmento_lider": por_segmento.most_common(1)[0][0] if por_segmento else None,
            "implementadora_lider": por_implementadora.most_common(1)[0][0] if por_implementadora else None,
            "estado_lider": por_estado.most_common(1)[0][0] if por_estado else None,
        },
        "empty_state": None if total else "Não há registros históricos para o contexto e segmento selecionados.",
    }
