from __future__ import annotations

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


def inferir_entidade(classificacao: str, dados: dict[str, Any]) -> str:
    chaves = set(dados)
    classe = str(classificacao or "").upper()

    if classe == "MERCADO_ANFIR":
        return "ANFIR"
    if classe == "TERRITORIAL":
        return "TERRITORIO"
    if classe == "FINANCEIRO":
        return "FINANCEIRO"

    for entidade in ("PEDIDO", "VENDA", "OPORTUNIDADE", "CLIENTE"):
        if any(chave in chaves for chave in CHAVES_ENTIDADE[entidade]):
            return entidade
    return "REGISTRO_COMERCIAL"


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
    conflitos: list[dict[str, Any]] = []

    if not dados:
        conflitos.append({"tipo": "SEM_DADOS_ESTRUTURADOS", "mensagem": "Registro sem campos estruturados para promoção operacional."})

    if entidade == "CLIENTE" and not any(dados.get(campo) for campo in ("cnpj", "cpf_cnpj", "cliente", "empresa", "razao_social", "nome")):
        conflitos.append({"tipo": "IDENTIFICADOR_AUSENTE", "mensagem": "Cliente sem identificador mínimo."})

    status = "CONFLITO" if conflitos else "VALIDO"
    acao = "REVISAR" if conflitos else "CANDIDATO_INSERIR_OU_ATUALIZAR"

    return {
        "indice_semantico": indice,
        "entidade_sugerida": entidade,
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
    return {
        "classificacao": classe,
        "dominio_alvo": DOMINIOS_ALVO[classe],
        "status": "PREPARADA",
        "total_itens": len(itens),
        "total_validos": validos,
        "total_conflitos": conflitos,
        "pronto_promocao": False,
        "promocao_operacional_automatica": False,
        "itens": itens,
        "regra": "CTI_RECONCILIACAO_CONTROLADA_V1",
    }


def pode_aprovar(plano: dict[str, Any]) -> bool:
    return (
        plano.get("status") in {"PREPARADA", "EM_REVISAO"}
        and int(plano.get("total_itens") or 0) > 0
        and int(plano.get("total_conflitos") or 0) == 0
    )
