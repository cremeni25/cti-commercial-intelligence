from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from core.cti_taxonomy import normalizar_implementadora, normalizar_produto

SEGMENTOS = {"GERAL", "TR", "DT", "DD", "UNKNOWN"}
STATUS_GANHOS = ("GANH", "APROV", "CONCL", "PEDIDO", "FATUR", "VEND")
STATUS_PERDIDOS = ("PERD", "REJEIT", "CANCEL", "EXPIR")


def _texto(registro, *campos, padrao="NÃO INFORMADO"):
    for campo in campos:
        valor = registro.get(campo)
        if valor not in (None, ""):
            return str(valor).strip()
    return padrao


def _valor(registro):
    for campo in ("valor", "valor_comercial", "valor_total"):
        try:
            if registro.get(campo) not in (None, ""):
                return float(registro[campo])
        except (TypeError, ValueError):
            pass
    return 0.0


def _data(registro):
    valor = registro.get("data_venda") or registro.get("data") or registro.get("created_at")
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor)[:10]
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _segmento(registro):
    produto = normalizar_produto(
        registro.get("produto") or registro.get("linha") or registro.get("modelo_equipamento") or registro.get("modelo")
    )
    return produto if produto in {"TR", "DT", "DD"} else "UNKNOWN"


def _dimensao(registro, nome):
    mapa = {
        "regiao": ("regiao",), "uf": ("estado", "uf"), "dealer": ("autorizado", "dealer", "origem_base"),
        "implementadora": ("implementadora", "implementador"), "cliente": ("empresa", "cliente"),
        "linha": ("linha", "tipo_veiculo"), "segmento": (), "familia": ("familia", "categoria"),
        "produto": ("produto", "modelo", "modelo_equipamento"), "responsavel": ("responsavel",),
    }
    if nome == "segmento":
        return _segmento(registro)
    valor = _texto(registro, *mapa[nome])
    if nome == "implementadora":
        return normalizar_implementadora(valor) or "NÃO INFORMADA"
    return valor.upper() if nome in {"regiao", "uf", "dealer", "linha", "familia", "produto"} else valor


def _status(registro):
    return _texto(registro, "status", padrao="").upper()


def _convertido(registro):
    status = _status(registro)
    return any(token in status for token in STATUS_GANHOS) or bool(registro.get("pedido") or registro.get("numero_pedido"))


def _perdido(registro):
    status = _status(registro)
    return any(token in status for token in STATUS_PERDIDOS) or bool(registro.get("motivo") or registro.get("motivo_perda"))


def _filtrar(registros, filtros):
    resultado = []
    inicio, fim = filtros.get("inicio"), filtros.get("fim")
    for registro in registros:
        data_registro = _data(registro)
        if inicio and (not data_registro or data_registro < inicio):
            continue
        if fim and (not data_registro or data_registro > fim):
            continue
        segmento = filtros.get("segmento", "GERAL")
        if segmento != "GERAL" and _segmento(registro) != segmento:
            continue
        valido = True
        for nome in ("regiao", "uf", "dealer", "implementadora", "cliente", "linha", "familia", "produto"):
            esperado = filtros.get(nome)
            if esperado and _dimensao(registro, nome).casefold() != str(esperado).casefold():
                valido = False
                break
        if valido:
            resultado.append(registro)
    return resultado


def _ranking(registros, nome, limite=20):
    grupos = defaultdict(lambda: {"quantidade": 0, "valor": 0.0})
    total = len(registros)
    for registro in registros:
        chave = _dimensao(registro, nome)
        grupos[chave]["quantidade"] += 1
        grupos[chave]["valor"] += _valor(registro)
    ordenado = sorted(grupos.items(), key=lambda item: (item[1]["quantidade"], item[1]["valor"]), reverse=True)
    return [
        {"nome": nome_item, "quantidade": dados["quantidade"], "valor": round(dados["valor"], 2),
         "participacao_percentual": round(dados["quantidade"] / total * 100, 2) if total else 0}
        for nome_item, dados in ordenado[:limite]
    ]


def _kpis(registros, anteriores=None):
    anteriores = anteriores or []
    def calcular(base):
        total = len(base); valor = sum(_valor(r) for r in base); convertidos = sum(1 for r in base if _convertido(r))
        return {"volume": total, "valor": round(valor, 2), "ticket_medio": round(valor / total, 2) if total else 0,
                "conversao": round(convertidos / total * 100, 2) if total else 0}
    atual, anterior = calcular(registros), calcular(anteriores)
    comparacoes = {}
    for chave, valor_atual in atual.items():
        valor_anterior = anterior[chave]
        diferenca = round(valor_atual - valor_anterior, 2)
        percentual = round(diferenca / valor_anterior * 100, 2) if valor_anterior else (100.0 if valor_atual else 0.0)
        comparacoes[chave] = {"atual": valor_atual, "anterior": valor_anterior, "diferenca": diferenca,
                              "percentual": percentual, "direcao": "alta" if diferenca > 0 else "queda" if diferenca < 0 else "estavel"}
    return {**atual, "comparacoes": comparacoes}


def _serie(registros, anteriores=None):
    por_mes = defaultdict(lambda: {"volume": 0, "valor": 0.0, "convertidos": 0, "perdas": 0})
    for registro in registros:
        data_registro = _data(registro)
        if not data_registro:
            continue
        chave = data_registro.strftime("%Y-%m")
        por_mes[chave]["volume"] += 1; por_mes[chave]["valor"] += _valor(registro)
        por_mes[chave]["convertidos"] += int(_convertido(registro)); por_mes[chave]["perdas"] += int(_perdido(registro))
    return [{"periodo": chave, "volume": dados["volume"], "valor": round(dados["valor"], 2),
             "ticket_medio": round(dados["valor"] / dados["volume"], 2) if dados["volume"] else 0,
             "conversao": round(dados["convertidos"] / dados["volume"] * 100, 2) if dados["volume"] else 0,
             "perdas": dados["perdas"]} for chave, dados in sorted(por_mes.items())]


def opcoes_filtros(registros, filtros):
    base = [dict(item) for item in registros or []]
    resposta = {}
    for dimensao in ("regiao", "uf", "dealer", "implementadora", "cliente", "linha", "segmento", "familia", "produto"):
        filtros_sem_dimensao = {**filtros, dimensao: None}
        filtrados = _filtrar(base, filtros_sem_dimensao)
        contagem = Counter(_dimensao(r, dimensao) for r in filtrados)
        resposta[dimensao] = [{"valor": valor, "contagem": contagem[valor]} for valor in sorted(contagem, key=str.casefold)]
    return resposta


def consolidar_inteligencia(registros: Iterable[dict], contexto="brasil", segmento="GERAL", filtros=None, comparacao=None):
    base = [dict(item) for item in (registros or [])]
    filtros = {**(filtros or {}), "segmento": segmento if segmento in SEGMENTOS else "GERAL"}
    analisados = _filtrar(base, filtros)
    anteriores = _filtrar(base, comparacao) if comparacao else []
    perdas = [r for r in analisados if _perdido(r)]
    hoje = date.today()
    clientes_inativos = []
    for nome, itens in _agrupar(analisados, "cliente").items():
        datas = [d for d in (_data(r) for r in itens) if d]
        ultima = max(datas) if datas else None
        dias = (hoje - ultima).days if ultima else None
        if dias is not None and dias >= 30:
            clientes_inativos.append({"nome": nome, "dias_sem_compra": dias, "ultima_compra": ultima.isoformat()})
    potencial_campos = ("potencial", "potencial_mercado", "mercado_total", "valor_potencial")
    potencial = sum(float(r.get(c) or 0) for r in analisados for c in potencial_campos if isinstance(r.get(c), (int, float)))
    return {
        "metadata": {"contexto_operacional": contexto, "segmento": filtros["segmento"], "filtros": {k: (v.isoformat() if isinstance(v, date) else v) for k,v in filtros.items() if v},
                     "ultima_atualizacao": datetime.now(timezone.utc).isoformat(), "origem": "cti_anfir"},
        "kpis": _kpis(analisados, anteriores),
        "segmentos": dict(Counter(_segmento(r) for r in base)),
        "rankings": {nome: _ranking(analisados, nome) for nome in ("uf", "dealer", "implementadora", "cliente", "linha", "familia", "produto")},
        "serie_temporal": _serie(analisados, anteriores),
        "oportunidades_perdidas": {"quantidade": len(perdas), "valor": round(sum(_valor(r) for r in perdas), 2),
                                  "motivos": _ranking(perdas, "produto", 10), "status_mapeados": list(STATUS_PERDIDOS)},
        "clientes_inativos": sorted(clientes_inativos, key=lambda x: x["dias_sem_compra"], reverse=True)[:50],
        "implementadoras_inativas": [],
        "heatmap": [{"regiao": _dimensao(r, "regiao"), "uf": _dimensao(r, "uf")} for r in analisados[:200]],
        "drilldown": {nome: _ranking(analisados, nome, 50) for nome in ("regiao", "uf", "implementadora", "cliente", "linha", "familia", "produto")},
        "potencial": {"valor": round(potencial, 2) if potencial else None, "campos_verificados": list(potencial_campos),
                      "status": "calculado" if potencial else "fonte_real_ausente"},
        "registros": analisados[:100],
        "empty_state": None if analisados else "Não há registros para os filtros selecionados.",
    }


def _agrupar(registros, dimensao):
    grupos = defaultdict(list)
    for registro in registros:
        grupos[_dimensao(registro, dimensao)].append(registro)
    return grupos
