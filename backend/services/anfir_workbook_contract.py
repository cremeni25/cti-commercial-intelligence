from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict

from services.anfir_workbook_semantics import (
    categoria_workbook_2026,
    causa_workbook_2026,
    extrair_observacao_workbook,
    temas_workbook_2026,
)
from services.operational_filters import MUNICIPIO_DDD_SP, data_registro, resolver_ddd_registro
from services.product_line_classifier import classificar_linha


SEGMENTOS = ("TR", "DT", "DD")
NOMES_SEGMENTOS = {"TR": "Trailer", "DT": "Diesel Truck", "DD": "Direct Drive"}
DDD_VIENA = ("011", "012", "013", "014", "015", "018")
RESPONSAVEIS_DDD = {
    "011": "COMPARTILHADO — REGRA INTERNA CTI",
    "012": "MÔNICA",
    "013": "MICHELE",
    "014": "NATHAN",
    "015": "A CONFIRMAR",
    "018": "NATHAN",
}


def _texto(valor) -> str:
    texto = str(valor or "").strip()
    return "" if texto.upper() in {"", "0", "80", "NAN", "NONE", "#N/A"} else texto


def _sem_acento(valor) -> str:
    texto = str(valor or "").strip().upper()
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _ddd_workbook(registro: dict) -> str | None:
    estado = str(registro.get("estado") or registro.get("uf") or "").strip().upper()
    cidade = _sem_acento(registro.get("cidade") or registro.get("municipio"))
    if estado == "SP" and cidade in MUNICIPIO_DDD_SP:
        return MUNICIPIO_DDD_SP[cidade]
    return resolver_ddd_registro(registro)


def _linha(registro: dict) -> str:
    return classificar_linha(registro) or "UNKNOWN"


def _implementadora(registro: dict) -> str:
    return _texto(registro.get("implementadora") or registro.get("implementador")) or "NÃO INFORMADA"


def _cliente(registro: dict) -> str:
    return _texto(registro.get("cliente") or registro.get("empresa")) or "NÃO INFORMADO"


def _percentual(parte: int, total: int) -> float:
    return round(parte / total * 100, 2) if total else 0.0


def _q(registros: list[dict], ano: int, trimestre: int) -> int:
    return sum(1 for registro in registros if (data := data_registro(registro)) and data.year == ano and ((data.month - 1) // 3 + 1) == trimestre)


def _status_por_segmento(registros: list[dict]):
    retorno = []
    for codigo in SEGMENTOS:
        itens = [r for r in registros if _linha(r) == codigo]
        total = len(itens)
        categorias = Counter(categoria_workbook_2026(r) for r in itens)
        nao_participou = sum(1 for r in itens if causa_workbook_2026(r) == "COBERTURA_COMERCIAL")
        q1, q2 = _q(itens, 2026, 1), _q(itens, 2026, 2)
        retorno.append({
            "codigo": codigo,
            "segmento": NOMES_SEGMENTOS[codigo],
            "mercado": total,
            "carrier": categorias.get("CARRIER", 0),
            "carrier_percentual_observado": _percentual(categorias.get("CARRIER", 0), total),
            "tk": categorias.get("TK", 0),
            "nacional": categorias.get("NACIONAL", 0),
            "usado_concorrente": categorias.get("USADO_CONCORRENTE", 0),
            "usado_carrier": categorias.get("USADO_CARRIER", 0),
            "sem_contato": categorias.get("SEM_CONTATO", 0),
            "nao_classificado": categorias.get("NAO_CLASSIFICADO", 0),
            "nao_participou": nao_participou,
            "q1": q1,
            "q2": q2,
            "q2_vs_q1_percentual": round((q2 - q1) / q1 * 100, 2) if q1 else None,
        })
    return retorno


def _mensal(registros: list[dict]):
    nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    linhas = []
    for mes_num in range(1, 13):
        itens = [r for r in registros if (d := data_registro(r)) and d.year == 2026 and d.month == mes_num]
        if not itens:
            continue
        contagem = Counter(_linha(r) for r in itens)
        linhas.append({"mes": nomes[mes_num], "competencia": f"2026-{mes_num:02d}", "trailer": contagem.get("TR", 0), "diesel_truck": contagem.get("DT", 0), "direct_drive": contagem.get("DD", 0), "total": len(itens)})
    return linhas


def _territorio(registros: list[dict]):
    linhas = []
    for ddd in DDD_VIENA:
        itens = [r for r in registros if _ddd_workbook(r) == ddd]
        contagem = Counter(_linha(r) for r in itens)
        linhas.append({"ddd": ddd, "mercado": len(itens), "trailer": contagem.get("TR", 0), "diesel_truck": contagem.get("DT", 0), "direct_drive": contagem.get("DD", 0), "responsavel": RESPONSAVEIS_DDD[ddd]})
    return linhas


def _leitura_cliente(dados: dict) -> str:
    if dados["nao_participou"] >= 3: return "Recuperar cobertura: cliente aparece repetidamente sem participação Carrier."
    if dados["sem_contato"] >= 3: return "Ativar contato e qualificar decisor/necessidade antes da próxima compra."
    if dados["preco"] >= 2: return "Trabalhar valor total, comparação técnica e condição comercial."
    if dados["relacionamento"] >= 2: return "Plano de relacionamento e cadência comercial."
    if dados["gap_tecnico"] >= 2: return "Validar aderência de produto/solução técnica."
    if dados["tk"] >= 3: return "Conta de conversão competitiva relevante."
    return "Qualificar oportunidade e histórico."


def _oportunidades_prioritarias(registros: list[dict], limite: int = 40):
    grupos = defaultdict(lambda: {"mercado": 0, "nao_carrier": 0, "carrier": 0, "nao_participou": 0, "sem_contato": 0, "tk": 0, "nacional": 0, "preco": 0, "relacionamento": 0, "gap_tecnico": 0})
    for registro in registros:
        cliente = _cliente(registro)
        categoria = categoria_workbook_2026(registro)
        causa = causa_workbook_2026(registro)
        dados = grupos[cliente]
        dados["mercado"] += 1
        if categoria == "CARRIER": dados["carrier"] += 1
        else: dados["nao_carrier"] += 1
        if causa == "COBERTURA_COMERCIAL": dados["nao_participou"] += 1
        if categoria == "SEM_CONTATO": dados["sem_contato"] += 1
        if categoria == "TK": dados["tk"] += 1
        if categoria == "NACIONAL": dados["nacional"] += 1
        if causa == "PRECO_VALOR": dados["preco"] += 1
        if causa == "RELACIONAMENTO": dados["relacionamento"] += 1
        if causa == "GAP_TECNICO_PRODUTO": dados["gap_tecnico"] += 1
    retorno = []
    for cliente, dados in grupos.items():
        score = dados["nao_carrier"] + 2 * (dados["nao_participou"] + dados["sem_contato"]) + dados["preco"] + dados["relacionamento"] + dados["gap_tecnico"]
        prioridade = "ALTA" if score >= 15 else "MÉDIA" if score >= 9 else "MONITORAR"
        retorno.append({"prioridade": prioridade, "cliente": cliente, "score_transparente": score, **dados, "leitura_sugerida": _leitura_cliente(dados), "criterio_score": "não Carrier + 2×(não participou + sem contato) + preço + relacionamento + gap técnico"})
    retorno.sort(key=lambda item: (item["score_transparente"], item["mercado"]), reverse=True)
    return retorno[:limite]


def _implementadoras(registros: list[dict], limite: int = 30):
    grupos = defaultdict(Counter)
    for registro in registros:
        grupos[_implementadora(registro)][_linha(registro)] += 1
    retorno = []
    for nome, contagem in grupos.items():
        total = sum(contagem.values())
        if nome == "NÃO INFORMADA": continue
        dominante = max(SEGMENTOS, key=lambda codigo: contagem.get(codigo, 0))
        retorno.append({"implementadora": nome, "mercado_elegivel": total, "trailer": contagem.get("TR", 0), "diesel_truck": contagem.get("DT", 0), "direct_drive": contagem.get("DD", 0), "leitura": f"Canal relevante em {NOMES_SEGMENTOS[dominante]}; cruzar status competitivo e clientes para plano de relacionamento."})
    retorno.sort(key=lambda item: item["mercado_elegivel"], reverse=True)
    return retorno[:limite]


TEMA_CONTRATO = {
    "TECNICA_PRODUTO": ("Há casos em que a limitação percebida de solução/produto influencia a decisão; exige validação técnica antes de classificar como perda por preço.", "Alerta de gap técnico + fila para engenharia/produto"),
    "POS_VENDA": ("Condições e promessas de manutenção/pós-venda aparecem como argumento competitivo e precisam ser comparadas de forma objetiva.", "Comparativo de oferta/pós-venda e objeções"),
    "PRECO_VALOR": ("Preço/valor aparece, mas não deve ser tratado isoladamente; em vários casos está combinado com produto, pós-venda ou solução do concorrente.", "Motivo de perda com contexto; não apenas campo 'preço'"),
    "USADO_LEGALIZACAO": ("Uso/reaproveitamento de equipamento ou implemento altera a oportunidade: muitas ocorrências são renovação/legalização, não compra nova convencional.", "Radar de renovação/substituição de frota"),
    "INTEGRACAO_FABRICANTE": ("Quando implementadora/fabricante também fornece a solução frigorífica, a decisão pode ocorrer antes do contato comercial da Viena.", "Mapa de influência das implementadoras"),
    "CONCORRENTE_NACIONAL": ("Marcas nacionais aparecem com grande frequência nas observações e precisam de estratégia própria, separada de Carrier x TK.", "Mapa competitivo por marca nacional"),
    "CONCORRENTE_TK": ("Há evidência textual de concorrência TK e modelos específicos; permite construir inteligência por modelo e argumento competitivo.", "Mapa Carrier x TK por modelo/conta"),
    "RELACIONAMENTO": ("Observações registram necessidade de contato e construção de relacionamento, mostrando perda anterior à etapa de proposta.", "Ação de cobertura/relacionamento"),
    "PARTICIPACAO_TESTE": ("Há casos com participação, teste ou demo que não converteram; isso permite medir efetividade da ação comercial.", "Funil teste/demo → proposta → venda"),
    "CONTEXTO_CLIENTE": ("Cliente final, operação e região ajudam a separar comprador formal, usuário final e contexto real da decisão.", "Enriquecimento de conta e operação"),
    "CONTEXTO_LIVRE": ("Texto explicativo relevante, mas sem regra segura para classificação automática; deve permanecer disponível para leitura e IA contextual.", "Contexto para IA e análise humana; nunca classificação cega"),
}


def _observacoes(registros: list[dict]):
    contagem = Counter()
    clientes = defaultdict(set)
    observacoes = defaultdict(set)
    uteis = 0
    for registro in registros:
        texto = extrair_observacao_workbook(registro)
        if texto: uteis += 1
        for tema in temas_workbook_2026(registro):
            contagem[tema] += 1
            clientes[tema].add(_cliente(registro))
            if texto: observacoes[tema].add(texto)
    temas = []
    for tema, quantidade in contagem.most_common():
        leitura, uso = TEMA_CONTRATO.get(tema, ("Sinal qualitativo extraído da observação original; requer leitura contextual.", "Contexto para análise humana/IA; não usar como classificação cega"))
        temas.append({"tema": tema, "ocorrencias": quantidade, "clientes_unicos": len(clientes[tema]), "observacoes_unicas": len(observacoes[tema]), "leitura_comercial": leitura, "uso_no_cti": uso})
    return {"temas": temas, "registros_elegiveis": len(registros), "com_observacao_util": uteis, "cobertura_observacoes_percentual": _percentual(uteis, len(registros)), "sem_observacao_util": len(registros) - uteis, "regra": "Texto original preservado; temas derivados são auxiliares e podem coexistir."}


def consolidar_workbook_anfir_2026(registros: list[dict]):
    registros = [dict(r) for r in registros if (d := data_registro(r)) and d.year == 2026]
    segmentos = _status_por_segmento(registros)
    categorias = Counter(categoria_workbook_2026(r) for r in registros)
    nao_participou = sum(1 for r in registros if causa_workbook_2026(r) == "COBERTURA_COMERCIAL")
    q1, q2 = _q(registros, 2026, 1), _q(registros, 2026, 2)
    leituras = [
        "Direct Drive é o maior mercado elegível e também o maior espaço competitivo: forte presença de fabricantes nacionais, baixa presença Carrier observada e grande incidência de não participação nas propostas.",
        "Trailer possui a posição competitiva mais forte da Carrier na ANFIR elegível. A defesa da base e o tratamento de TK devem ser prioridade, sem atribuir todas as perdas a preço.",
        "Diesel Truck apresenta mercado mais fragmentado: nacionais, usados, sem contato e equipamentos Carrier usados indicam oportunidade de renovação e reconquista, além da disputa tradicional com TK.",
        "O DDD 011 concentra a maior parte do mercado. Como há sobreposição comercial interna, esta leitura não atribui arbitrariamente os registros a uma única vendedora.",
        "Sem contato e não participamos da proposta são indicadores de cobertura comercial e devem virar fila de ação no CTI, não apenas estatística histórica.",
        "A presença Carrier é classificação observada na ANFIR. Market share oficial só deve ser publicado após reconciliação com vendas/instalações Carrier na mesma competência e território.",
    ]
    return {
        "metadata": {"nome_contrato": "Auditoria_ANFIR_Carrier_JOV_2026_Inteligencia_Viena_Observacoes", "competencia": "2026", "natureza": "FOTOGRAFIA_ANFIR_CARRIER_JOV_VIENA", "market_share_oficial": False},
        "inteligencia_viena": {"mercado_elegivel": len(registros), "carrier_observada": categorias.get("CARRIER", 0), "carrier_presenca_percentual": _percentual(categorias.get("CARRIER", 0), len(registros)), "sem_contato": categorias.get("SEM_CONTATO", 0), "nao_participamos_proposta": nao_participou, "dados_status_a_qualificar": categorias.get("NAO_CLASSIFICADO", 0), "q1": q1, "q2": q2, "q2_vs_q1_percentual": round((q2 - q1) / q1 * 100, 2) if q1 else None, "segmentos": segmentos, "mensal": _mensal(registros), "territorio": _territorio(registros), "leituras_estrategicas": leituras},
        "oportunidades_prioritarias": _oportunidades_prioritarias(registros),
        "implementadoras_mercado": _implementadoras(registros),
        "inteligencia_observacoes": _observacoes(registros),
    }
