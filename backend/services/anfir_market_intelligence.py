from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

from services.operational_filters import data_registro


CATEGORIAS_COMPETITIVAS = (
    "CARRIER",
    "TK",
    "NACIONAL",
    "USADO_CARRIER",
    "USADO_CONCORRENTE",
    "SEM_CONTATO",
    "OUTROS",
    "NAO_CLASSIFICADO",
)


def _normalizar(valor) -> str:
    texto = str(valor or "").strip().upper()
    texto = "".join(
        caractere for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"\s+", " ", texto)


def _texto_util(valor) -> str:
    texto = str(valor or "").strip()
    return "" if _normalizar(texto) in {"", "0", "80", "#N/A", "NAN", "NONE"} else texto


def categoria_competitiva(registro: dict) -> str:
    status = _normalizar(registro.get("status"))
    if not status or status in {"0", "80"}:
        return "NAO_CLASSIFICADO"
    compacto = re.sub(r"[^A-Z0-9]", "", status)
    if "USADOCARRIER" in compacto:
        return "USADO_CARRIER"
    if "USADOCONCORRENTE" in compacto or "USADOTK" in compacto:
        return "USADO_CONCORRENTE"
    if "SEMCONTATO" in compacto:
        return "SEM_CONTATO"
    if status == "TK" or "THERMO KING" in status:
        return "TK"
    if "NACIONAL" in status:
        return "NACIONAL"
    if "CARRIER" in status:
        return "CARRIER"
    return "OUTROS"


def causa_estrategica(registro: dict) -> str:
    motivo = _normalizar(_texto_util(registro.get("motivo")))
    ocorrencia = _normalizar(_texto_util(registro.get("ocorrencia")))
    texto = f"{motivo} {ocorrencia}"
    if "NAO PARTICIPAMOS" in motivo or "NAO PARTICIPOU" in motivo:
        return "COBERTURA_COMERCIAL"
    if "SEM CONTATO" in texto or categoria_competitiva(registro) == "SEM_CONTATO":
        return "SEM_CONTATO"
    if "RELACIONAMENTO" in texto:
        return "RELACIONAMENTO"
    if "PRECO" in texto or "VALOR" in texto or "MAIS ALTO" in texto:
        return "PRECO_VALOR"
    if "CONDICAO DE PAGAMENTO" in texto or "PAGAMENTO" in motivo or "CREDITO" in texto:
        return "CONDICAO_FINANCEIRA"
    if any(token in texto for token in ("SEM SOLUCAO TECNICA", "SOLUCAO TECNICA", "KIT ELETRICO", "TECNIC", "PRODUTO")):
        return "TECNICO_PRODUTO"
    if any(token in texto for token in ("USADO", "REAPROVEIT", "REFORMA", "LEGALIZ")):
        return "USADO_REAPROVEITAMENTO"
    if motivo:
        return "OUTRA_CAUSA_ESTRUTURADA"
    return "SEM_CAUSA_ESTRUTURADA"


def temas_observacao(registro: dict) -> list[str]:
    texto = _normalizar(_texto_util(registro.get("ocorrencia")))
    if not texto:
        return []
    temas = []
    regras = (
        ("CONCORRENTE_TK", ("THERMO KING", " TK ", "A500", "SLXI")),
        ("CONCORRENTE_NACIONAL", ("NACIONAL", "FRIGOKING", "RODOFRIO", "THERMOFLEX", "THERMOSTAR", "TITON")),
        ("IMPLEMENTADORA_INTEGRADA", ("IMPLEMENTADORA", "FABRICA O EQUIPAMENTO", "FABRICANTE DO EQUIPAMENTO", "INCLUSO NO VALOR")),
        ("PRECO_VALOR", ("PRECO", "VALOR", "MAIS CARO", "MAIS ALTO")),
        ("RELACIONAMENTO", ("RELACIONAMENTO", "CONTATO", "VISITA")),
        ("TECNICO_PRODUTO", ("TECNIC", "PRODUTO", "KIT ELETRICO", "SOLUCAO")),
        ("USADO_REAPROVEITAMENTO", ("USADO", "REAPROVEIT", "REFORMA", "LEGALIZ")),
        ("POS_VENDA_MANUTENCAO", ("MANUTENCAO", "POS VENDA", "POS-VENDA", "HORAS DE MANUTENCAO")),
        ("TESTE_DEMO", ("DEMO", "TESTE", "DEMONSTR")),
    )
    cercado = f" {texto} "
    for tema, tokens in regras:
        if any(token in cercado for token in tokens):
            temas.append(tema)
    if not temas:
        temas.append("CONTEXTO_LIVRE")
    return temas


def _variacao(atual: int, anterior: int):
    diferenca = atual - anterior
    percentual = round(diferenca / anterior * 100, 2) if anterior else (100.0 if atual else 0.0)
    return {
        "atual": atual,
        "anterior": anterior,
        "diferenca": diferenca,
        "percentual": percentual,
        "direcao": "alta" if diferenca > 0 else "queda" if diferenca < 0 else "estavel",
    }


def _distribuicao_competitiva(registros):
    contagem = Counter(categoria_competitiva(r) for r in registros)
    total = len(registros)
    classificados = total - contagem.get("NAO_CLASSIFICADO", 0)
    distribuicao = []
    for categoria in CATEGORIAS_COMPETITIVAS:
        quantidade = contagem.get(categoria, 0)
        distribuicao.append({
            "categoria": categoria,
            "quantidade": quantidade,
            "participacao_mercado_percentual": round(quantidade / total * 100, 2) if total else 0.0,
            "participacao_classificados_percentual": round(quantidade / classificados * 100, 2) if classificados else 0.0,
        })
    return distribuicao, classificados


def _causas(registros, limite=15):
    causas = Counter(causa_estrategica(r) for r in registros)
    total = len(registros)
    return [
        {
            "causa": causa,
            "quantidade": quantidade,
            "participacao_percentual": round(quantidade / total * 100, 2) if total else 0.0,
        }
        for causa, quantidade in causas.most_common(limite)
    ]


def _motivos_originais(registros, limite=15):
    motivos = Counter()
    for registro in registros:
        motivo = _texto_util(registro.get("motivo"))
        if motivo:
            motivos[motivo] += 1
    total = sum(motivos.values())
    return [
        {
            "motivo": motivo,
            "quantidade": quantidade,
            "participacao_motivos_percentual": round(quantidade / total * 100, 2) if total else 0.0,
        }
        for motivo, quantidade in motivos.most_common(limite)
    ]


def _temas(registros, limite=15):
    contagem = Counter()
    clientes = defaultdict(set)
    for registro in registros:
        cliente = _texto_util(registro.get("cliente") or registro.get("empresa"))
        for tema in temas_observacao(registro):
            contagem[tema] += 1
            if cliente:
                clientes[tema].add(cliente)
    return [
        {"tema": tema, "ocorrencias": quantidade, "clientes_distintos": len(clientes[tema])}
        for tema, quantidade in contagem.most_common(limite)
    ]


def _prioridades(registros, limite=40):
    grupos = defaultdict(lambda: {
        "volume": 0, "score": 0, "segmentos": Counter(), "categorias": Counter(),
        "causas": Counter(), "implementadoras": Counter(), "meses": set(),
    })
    for registro in registros:
        categoria = categoria_competitiva(registro)
        if categoria == "CARRIER":
            continue
        cliente = _texto_util(registro.get("cliente") or registro.get("empresa")) or "NÃO INFORMADO"
        causa = causa_estrategica(registro)
        segmento = _texto_util(registro.get("linha") or registro.get("produto")) or "NÃO INFORMADO"
        implementadora = _texto_util(registro.get("implementadora") or registro.get("implementador")) or "NÃO INFORMADA"
        grupo = grupos[cliente]
        grupo["volume"] += 1
        grupo["segmentos"][segmento] += 1
        grupo["categorias"][categoria] += 1
        grupo["causas"][causa] += 1
        grupo["implementadoras"][implementadora] += 1
        data = data_registro(registro)
        if data:
            grupo["meses"].add(data.strftime("%Y-%m"))

        grupo["score"] += 1
        grupo["score"] += {
            "SEM_CONTATO": 5,
            "TK": 4,
            "NACIONAL": 3,
            "USADO_CONCORRENTE": 2,
            "OUTROS": 1,
            "NAO_CLASSIFICADO": 1,
            "USADO_CARRIER": 0,
        }.get(categoria, 0)
        grupo["score"] += {
            "COBERTURA_COMERCIAL": 6,
            "SEM_CONTATO": 5,
            "RELACIONAMENTO": 4,
            "PRECO_VALOR": 3,
            "CONDICAO_FINANCEIRA": 3,
            "TECNICO_PRODUTO": 3,
            "USADO_REAPROVEITAMENTO": 2,
        }.get(causa, 0)

    ordenados = sorted(grupos.items(), key=lambda item: (item[1]["score"], item[1]["volume"]), reverse=True)
    retorno = []
    for cliente, dados in ordenados[:limite]:
        retorno.append({
            "cliente": cliente,
            "score_prioridade": dados["score"],
            "volume": dados["volume"],
            "meses_com_ocorrencia": len(dados["meses"]),
            "segmentos": [{"nome": k, "quantidade": v} for k, v in dados["segmentos"].most_common()],
            "categorias_competitivas": [{"nome": k, "quantidade": v} for k, v in dados["categorias"].most_common()],
            "causas": [{"nome": k, "quantidade": v} for k, v in dados["causas"].most_common()],
            "implementadoras": [{"nome": k, "quantidade": v} for k, v in dados["implementadoras"].most_common(3)],
            "criterio_score": "volume + categoria competitiva + causa estratégica; maior score = maior necessidade de ação",
        })
    return retorno


def consolidar_inteligencia_mercado(registros, anteriores=None):
    atuais = [dict(r) for r in (registros or [])]
    anteriores = [dict(r) for r in (anteriores or [])]
    distribuicao, classificados = _distribuicao_competitiva(atuais)
    por_categoria = {item["categoria"]: item for item in distribuicao}
    carrier = por_categoria["CARRIER"]

    nao_participamos = sum(1 for r in atuais if causa_estrategica(r) == "COBERTURA_COMERCIAL")
    sem_contato = sum(1 for r in atuais if categoria_competitiva(r) == "SEM_CONTATO")
    concorrencia_direta = sum(1 for r in atuais if categoria_competitiva(r) in {"TK", "NACIONAL", "USADO_CONCORRENTE"})

    return {
        "mercado": {
            "volume": len(atuais),
            "comparacao": _variacao(len(atuais), len(anteriores)),
            "competencia_min": min((data_registro(r) for r in atuais if data_registro(r)), default=None),
            "competencia_max": max((data_registro(r) for r in atuais if data_registro(r)), default=None),
        },
        "competitividade": {
            "registros_classificados": classificados,
            "cobertura_classificacao_percentual": round(classificados / len(atuais) * 100, 2) if atuais else 0.0,
            "distribuicao": distribuicao,
            "carrier_observado": {
                "quantidade": carrier["quantidade"],
                "participacao_observada_percentual": carrier["participacao_mercado_percentual"],
                "natureza": "PRESENCA_COMPETITIVA_OBSERVADA_ANFIR",
                "nao_e": "MARKET_SHARE_CONTABIL_RECONCILIADO",
            },
        },
        "causas_estrategicas": _causas(atuais),
        "motivos_originais": _motivos_originais(atuais),
        "cobertura_comercial": {
            "nao_participamos_proposta": nao_participamos,
            "sem_contato": sem_contato,
            "concorrencia_direta_observada": concorrencia_direta,
            "percentual_nao_participacao": round(nao_participamos / len(atuais) * 100, 2) if atuais else 0.0,
        },
        "inteligencia_observacoes": {
            "temas": _temas(atuais),
            "metodo": "extração temática conservadora; o texto original permanece em ocorrencia e prevalece sobre a classificação",
        },
        "prioridades_recuperacao": _prioridades(atuais),
        "avisos_metodologicos": [
            "ANFIR representa mercado realizado; não é Funil nem oportunidade aberta.",
            "Participação Carrier neste bloco é presença competitiva observada na ANFIR, não market share contábil definitivo.",
            "Market share oficial exige reconciliação posterior com vendas/instalações Carrier na mesma competência e território.",
            "Temas de observação são sinais auxiliares e não substituem o texto original registrado pela Carrier/Viena.",
        ],
    }
