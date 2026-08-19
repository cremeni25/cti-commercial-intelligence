from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any


DOMINIOS_ALVO = {
    "COMERCIAL": "CRM_COMERCIAL",
    "MERCADO_ANFIR": "CTI_ANFIR",
    "TERRITORIAL": "CTI_TERRITORIAL",
    "FINANCEIRO": "CTI_FINANCEIRO",
}

CHAVES_ENTIDADE = {
    "CLIENTE": ("cnpj", "cpf_cnpj", "cliente", "empresa", "razao_social", "nome"),
    "OPORTUNIDADE": ("oportunidade", "numero_oportunidade", "id_oportunidade"),
    "PEDIDO": ("pedido", "numero_pedido", "id_pedido"),
    "VENDA": ("venda", "numero_venda", "id_venda"),
    "ANFIR": ("chassi", "placa", "implementadora", "fabricante_equipamento", "modelo"),
    "TERRITORIO": ("cep", "cidade", "municipio", "estado", "uf", "regiao", "ddd"),
    "FINANCEIRO": ("valor", "receita", "margem", "custo", "pagamento", "faturamento"),
}

# Dentro de um mesmo registro comercial podem coexistir referências ao ciclo
# anterior (ex.: uma venda mantém numero_pedido e id_oportunidade). A natureza
# canônica deve refletir o estágio mais avançado explicitamente presente.
PRECEDENCIA_CICLO_COMERCIAL = ("VENDA", "PEDIDO", "OPORTUNIDADE", "CLIENTE")

NATUREZA_POR_ENTIDADE = {
    "ANFIR": "MERCADO_REALIZADO",
    "CLIENTE": "CRM_CADASTRAL",
    "OPORTUNIDADE": "FUNIL_COMERCIAL",
    "PEDIDO": "CRM_EXECUCAO_POS_OPORTUNIDADE",
    "VENDA": "COMERCIAL_REALIZADO",
    "TERRITORIO": "INTELIGENCIA_TERRITORIAL",
    "FINANCEIRO": "INTELIGENCIA_FINANCEIRA",
    "REGISTRO_COMERCIAL": "CRM_COMERCIAL_NAO_CLASSIFICADO",
}

CAMADA_DASHBOARD_POR_NATUREZA = {
    "MERCADO_REALIZADO": "REALIZADO_MERCADO",
    "CRM_CADASTRAL": "CADASTRO_CRM",
    "FUNIL_COMERCIAL": "EM_CURSO_FUNIL",
    "CRM_EXECUCAO_POS_OPORTUNIDADE": "EXECUCAO_COMERCIAL",
    "COMERCIAL_REALIZADO": "REALIZADO_COMERCIAL",
    "INTELIGENCIA_TERRITORIAL": "DIMENSAO_TERRITORIAL",
    "INTELIGENCIA_FINANCEIRA": "DIMENSAO_FINANCEIRA",
    "CRM_COMERCIAL_NAO_CLASSIFICADO": "STAGING_COMERCIAL",
}


def _normalizar_chave(chave: Any) -> str:
    return str(chave or "").strip().casefold().replace(" ", "_").replace("-", "_")


def normalizar_dados(dados: dict[str, Any] | None) -> dict[str, Any]:
    saida: dict[str, Any] = {}
    for chave, valor in (dados or {}).items():
        nome = _normalizar_chave(chave)
        if not nome:
            continue
        saida[nome] = valor
    return saida


def _possui_sinal(entidade: str, dados: dict[str, Any]) -> bool:
    return any(dados.get(chave) not in (None, "") for chave in CHAVES_ENTIDADE[entidade])


def inferir_entidade(classificacao: str, dados: dict[str, Any]) -> str:
    classe = str(classificacao or "").upper()

    if classe == "MERCADO_ANFIR":
        return "ANFIR"
    if classe == "TERRITORIAL":
        return "TERRITORIO"
    if classe == "FINANCEIRO":
        return "FINANCEIRO"

    # COMERCIAL é uma família de registros, não uma natureza única. Cada linha
    # deve ser classificada individualmente para não transformar cliente em
    # oportunidade nem oportunidade em venda.
    for entidade in PRECEDENCIA_CICLO_COMERCIAL:
        if _possui_sinal(entidade, dados):
            return entidade
    return "REGISTRO_COMERCIAL"


def natureza_canonica(entidade: str) -> str:
    return NATUREZA_POR_ENTIDADE.get(str(entidade or "").upper(), "NAO_CLASSIFICADA")


def camada_dashboard(natureza: str) -> str:
    return CAMADA_DASHBOARD_POR_NATUREZA.get(str(natureza or "").upper(), "STAGING_GOVERNADO")


def chave_canonica(entidade: str, dados: dict[str, Any], indice: int) -> str:
    candidatos = CHAVES_ENTIDADE.get(entidade, tuple())
    partes = [f"{chave}={dados.get(chave)}" for chave in candidatos if dados.get(chave) not in (None, "")]
    if not partes:
        partes = [f"indice={indice}", json.dumps(dados, ensure_ascii=False, sort_keys=True, default=str)]
    digest = hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()
    return digest


def avaliar_item(classificacao: str, item: dict[str, Any]) -> dict[str, Any]:
    indice = int(item.get("indice") or 0)
    dados = normalizar_dados(item.get("dados") if isinstance(item.get("dados"), dict) else {})
    entidade = inferir_entidade(classificacao, dados)
    natureza = natureza_canonica(entidade)
    camada = camada_dashboard(natureza)
    conflitos: list[dict[str, Any]] = []

    if not dados:
        conflitos.append({"tipo": "SEM_DADOS_ESTRUTURADOS", "mensagem": "Registro sem campos estruturados para promoção operacional."})

    if entidade == "REGISTRO_COMERCIAL":
        conflitos.append({
            "tipo": "NATUREZA_COMERCIAL_NAO_IDENTIFICADA",
            "mensagem": "Registro comercial sem sinal suficiente para distinguir cliente, oportunidade, pedido ou venda.",
        })

    if entidade == "CLIENTE" and not any(dados.get(campo) for campo in ("cnpj", "cpf_cnpj", "cliente", "empresa", "razao_social", "nome")):
        conflitos.append({"tipo": "IDENTIFICADOR_AUSENTE", "mensagem": "Cliente sem identificador mínimo."})

    status = "CONFLITO" if conflitos else "VALIDO"
    acao = "REVISAR" if conflitos else "CANDIDATO_INSERIR_OU_ATUALIZAR"

    return {
        "indice_semantico": indice,
        "entidade_sugerida": entidade,
        "natureza_canonica": natureza,
        "camada_dashboard": camada,
        "acao_sugerida": acao,
        "chave_canonica": chave_canonica(entidade, dados, indice),
        "dados_origem": item.get("dados") if isinstance(item.get("dados"), dict) else {},
        "dados_normalizados": dados,
        "conflitos": conflitos,
        "status_item": status,
    }


def preparar_plano(classificacao: str, registros: list[dict[str, Any]]) -> dict[str, Any]:
    classe = str(classificacao or "").upper()
    if classe not in DOMINIOS_ALVO:
        raise ValueError("Classificação não elegível para reconciliação operacional.")

    itens = [avaliar_item(classe, item) for item in registros]
    conflitos = sum(1 for item in itens if item["status_item"] == "CONFLITO")
    validos = len(itens) - conflitos
    naturezas = dict(Counter(str(item["natureza_canonica"]) for item in itens))
    camadas = dict(Counter(str(item["camada_dashboard"]) for item in itens))
    return {
        "classificacao": classe,
        "dominio_alvo": DOMINIOS_ALVO[classe],
        "status": "PREPARADA",
        "total_itens": len(itens),
        "total_validos": validos,
        "total_conflitos": conflitos,
        "naturezas": naturezas,
        "camadas_dashboard": camadas,
        "lote_misto_naturezas": len(naturezas) > 1,
        "roteamento_por_registro": True,
        "pronto_promocao": False,
        "promocao_operacional_automatica": False,
        "itens": itens,
        "regra": "CTI_RECONCILIACAO_CONTROLADA_V3_NATUREZA_POR_REGISTRO",
    }


def pode_aprovar(plano: dict[str, Any]) -> bool:
    return (
        plano.get("status") in {"PREPARADA", "EM_REVISAO"}
        and int(plano.get("total_itens") or 0) > 0
        and int(plano.get("total_conflitos") or 0) == 0
    )
