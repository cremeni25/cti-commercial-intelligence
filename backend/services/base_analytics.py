from collections import Counter, defaultdict

from core.cti_taxonomy import aliases_implementadora, normalizar_implementadora


def valor_float(valor):
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def filtrar_registros(registros, origem_base, autorizado=None):
    return [
        r for r in registros
        if r.get("origem_base") == origem_base
        and (autorizado is None or r.get("autorizado") == autorizado)
    ]


def consolidar_dashboard(registros):
    total_registros = len(registros)
    clientes = {r.get("cliente") for r in registros if r.get("cliente")}
    estados = {r.get("estado") for r in registros if r.get("estado")}
    municipios = {r.get("cidade") for r in registros if r.get("cidade")}
    implementadoras = {
        normalizar_implementadora(r.get("implementadora"))
        for r in registros
        if r.get("implementadora")
    }
    faturamento_total = sum(valor_float(r.get("valor")) for r in registros)
    status = Counter(r.get("status") or "OUTROS" for r in registros)
    linhas = Counter(r.get("linha") or "OUTROS" for r in registros)
    tipos = Counter(r.get("tipo_veiculo") or "OUTROS" for r in registros)
    ranking_impl = Counter(
        normalizar_implementadora(r.get("implementadora"))
        for r in registros
        if r.get("implementadora")
    )
    ranking_clientes = Counter(r.get("cliente") for r in registros if r.get("cliente"))
    return {
        "contexto": {
            "origem": "Base histórica consolidada de uploads CTI",
            "periodo": "Período disponível nos registros filtrados pelo Contexto Operacional Global",
            "significado": "Operações concluídas, pedidos faturados, equipamentos entregues e implementações já realizadas.",
            "criterio_calculo": "Consolidação dos registros persistidos após filtros de origem, autorizado e escopo operacional.",
            "relacionamento": "Inteligência Histórica; não alimenta automaticamente oportunidades do CRM operacional.",
            "finalidade_operacional": "Analisar histórico comercial e territorial sem alterar o fluxo futuro do CRM.",
        },
        "territorialidade": ["Estado", "DDD", "Sub-Região", "Município", "Bairro", "Responsável Comercial"],
        "total_registros": total_registros,
        "total_clientes": len(clientes),
        "total_estados": len(estados),
        "total_municipios": len(municipios),
        "total_implementadoras": len(implementadoras),
        "faturamento_total": round(faturamento_total, 2),
        "ticket_medio": round(faturamento_total / total_registros, 2) if total_registros else 0,
        "distribuicao_status": dict(status),
        "distribuicao_linha": dict(linhas),
        "distribuicao_tipo_veiculo": dict(tipos),
        "ranking_implementadoras": [
            {"nome": nome, "quantidade": quantidade}
            for nome, quantidade in ranking_impl.most_common()
        ],
        "ranking_clientes": [
            {"nome": nome, "quantidade": quantidade}
            for nome, quantidade in ranking_clientes.most_common()
        ],
        "alertas": ["Nenhum alerta operacional calculado."],
    }


def consolidar_implementadoras(registros):
    dados = {}
    for r in registros:
        nome = normalizar_implementadora(r.get("implementadora"))
        if not nome:
            continue
        item = dados.setdefault(nome, {
            "nome": nome,
            "quantidade_registros": 0,
            "valor_total": 0,
            "estados": set(),
            "municipios": set(),
            "clientes_set": set(),
            "clientes": 0,
            "linhas_produto": set(),
            "status": {"aprovados": 0, "perdidos": 0, "outros": 0},
            "score_operacional": None,
            "score_comercial": None,
            "aliases": aliases_implementadora(nome),
        })
        item["quantidade_registros"] += 1
        item["valor_total"] += valor_float(r.get("valor"))
        if r.get("estado"):
            item["estados"].add(r.get("estado"))
        if r.get("cidade"):
            item["municipios"].add(r.get("cidade"))
        if r.get("cliente"):
            item["clientes_set"].add(r.get("cliente"))
        if r.get("linha"):
            item["linhas_produto"].add(r.get("linha"))
        status = str(r.get("status") or "").upper()
        if "APROV" in status or "GANH" in status:
            item["status"]["aprovados"] += 1
        elif "PERD" in status:
            item["status"]["perdidos"] += 1
        else:
            item["status"]["outros"] += 1
    resultado = []
    for item in dados.values():
        item["valor_total"] = round(item["valor_total"], 2)
        item["estados"] = sorted(item["estados"])
        item["municipios"] = sorted(item["municipios"])
        item["clientes"] = len(item.pop("clientes_set"))
        item["linhas_produto"] = sorted(item["linhas_produto"])
        resultado.append(item)
    return sorted(resultado, key=lambda x: x["quantidade_registros"], reverse=True)


def consolidar_clientes(registros):
    clientes = Counter(r.get("cliente") for r in registros if r.get("cliente"))
    return [{"nome": nome, "quantidade_registros": qtd} for nome, qtd in clientes.most_common()]


def consolidar_territorial(registros):
    estados = Counter(r.get("estado") for r in registros if r.get("estado"))
    municipios = Counter(r.get("cidade") for r in registros if r.get("cidade"))
    return {
        "estados": [{"nome": nome, "quantidade_registros": qtd} for nome, qtd in estados.most_common()],
        "municipios": [{"nome": nome, "quantidade_registros": qtd} for nome, qtd in municipios.most_common()],
    }


def consolidar_historico(registros):
    anos = defaultdict(int)
    for r in registros:
        if r.get("ano_referencia"):
            anos[str(r.get("ano_referencia"))] += 1
    return [{"ano": ano, "quantidade_registros": qtd} for ano, qtd in sorted(anos.items())]
