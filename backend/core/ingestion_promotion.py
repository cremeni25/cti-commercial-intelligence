from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from core.supabase_client import supabase
from repositories.cti_repository import repository
from backend.services.schema_compat import insert_schema_compatible, update_schema_compatible


SUPORTE = {
    ("CTI_ANFIR", "ANFIR"),
    ("CRM_COMERCIAL", "CLIENTE"),
}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _digitos(valor: Any) -> str:
    return re.sub(r"\D", "", _texto(valor))


def suporte_promocao(dominio: str, entidade: str) -> dict[str, Any]:
    chave = (str(dominio or "").upper(), str(entidade or "").upper())
    if chave in SUPORTE:
        return {"suportado": True, "dominio": chave[0], "entidade": chave[1], "regra": "CTI_PROMOCAO_CONTROLADA_V1"}
    motivo = {
        "CTI_TERRITORIAL": "Domínio territorial ainda não possui estrutura canônica suficiente para promoção de CEP/cidade/região.",
        "CTI_FINANCEIRO": "Domínio financeiro ainda não possui tabela canônica operacional própria.",
        "CRM_COMERCIAL": "Entidade comercial exige relacionamentos operacionais próprios antes da promoção.",
    }.get(chave[0], "Domínio/entidade sem adaptador canônico de promoção.")
    return {"suportado": False, "dominio": chave[0], "entidade": chave[1], "motivo": motivo, "regra": "CTI_PROMOCAO_CONTROLADA_V1"}


def validar_lote(reconciliacao: dict[str, Any], itens: list[dict[str, Any]]) -> dict[str, Any]:
    if str(reconciliacao.get("status") or "") != "PRONTO_PROMOCAO":
        raise ValueError("Reconciliação não está PRONTO_PROMOCAO.")
    if not itens:
        raise ValueError("Reconciliação sem itens para promover.")
    bloqueios = []
    for item in itens:
        if str(item.get("status_item") or "") != "PRONTO_PROMOCAO":
            bloqueios.append({"item_id": item.get("id"), "motivo": "ITEM_NAO_PRONTO"})
            continue
        suporte = suporte_promocao(str(reconciliacao.get("dominio_alvo") or ""), str(item.get("entidade_sugerida") or ""))
        if not suporte["suportado"]:
            bloqueios.append({"item_id": item.get("id"), "entidade": item.get("entidade_sugerida"), "motivo": suporte.get("motivo")})
    return {"aprovado": not bloqueios, "bloqueios": bloqueios, "total": len(itens), "regra": "CTI_PROMOCAO_CONTROLADA_V1"}


def _payload_cliente(dados: dict[str, Any]) -> dict[str, Any]:
    nome = _texto(dados.get("nome") or dados.get("razao_social") or dados.get("cliente") or dados.get("empresa"))
    if len(nome) < 2:
        raise ValueError("Cliente sem nome/razão social válido.")
    categoria = _texto(dados.get("categoria") or dados.get("segmento") or "TRANSPORTADORA").upper()
    return {
        "nome": nome,
        "cnpj": _digitos(dados.get("cnpj") or dados.get("cpf_cnpj")) or None,
        "inscricao_estadual": _texto(dados.get("inscricao_estadual")) or None,
        "endereco": _texto(dados.get("endereco") or dados.get("logradouro")) or None,
        "numero": _texto(dados.get("numero")) or None,
        "complemento": _texto(dados.get("complemento")) or None,
        "bairro": _texto(dados.get("bairro")) or None,
        "cidade": _texto(dados.get("cidade") or dados.get("municipio")) or None,
        "estado": _texto(dados.get("estado") or dados.get("uf")).upper() or None,
        "cep": _digitos(dados.get("cep")) or None,
        "contato": _texto(dados.get("contato") or dados.get("responsavel")) or None,
        "fone": _texto(dados.get("fone") or dados.get("telefone")) or None,
        "email": _texto(dados.get("email")).lower() or None,
        "email_xml": _texto(dados.get("email_xml")).lower() or None,
        "categoria": categoria,
        "segmento": categoria,
        "ddd": _digitos(dados.get("ddd")) or None,
        "sub_regiao": _texto(dados.get("sub_regiao")) or None,
        "status": "ATIVO",
        "updated_at": _agora(),
    }


def promover_cliente(dados: dict[str, Any]) -> dict[str, Any]:
    payload = _payload_cliente(dados)
    existente = []
    if payload.get("cnpj"):
        existente = supabase.table("clientes").select("*").eq("cnpj", payload["cnpj"]).limit(1).execute().data or []
    if not existente:
        existente = supabase.table("clientes").select("*").ilike("nome", payload["nome"]).limit(1).execute().data or []
    if existente:
        registro_id = str(existente[0]["id"])
        dados_atualizados, compat = update_schema_compatible(supabase, "clientes", registro_id, payload)
        return {"acao": "ATUALIZADO", "registro": (dados_atualizados or existente)[0], "compatibilidade": compat, "tabela": "clientes"}
    criado, compat = insert_schema_compatible(supabase, "clientes", payload, protected_fields={"nome"})
    if not criado:
        raise RuntimeError("Falha ao criar cliente canônico.")
    return {"acao": "INSERIDO", "registro": criado[0], "compatibilidade": compat, "tabela": "clientes"}


def promover_anfir(dados: dict[str, Any], *, chave_canonica: str, fonte_nome: str | None = None) -> dict[str, Any]:
    registro = dict(dados)
    registro["hash_registro"] = _texto(registro.get("hash_registro")) or chave_canonica
    registro["origem_dado"] = _texto(registro.get("origem_dado")) or "BACKOFFICE_FONTES"
    registro["arquivo_origem"] = _texto(registro.get("arquivo_origem")) or _texto(fonte_nome) or None
    registro["pipeline"] = _texto(registro.get("pipeline")) or "CTI_PROMOCAO_CONTROLADA_V1"
    registro["ativo"] = True if registro.get("ativo") is None else bool(registro.get("ativo"))
    resultado = repository.persistir_registros_idempotente([registro])
    if resultado.get("erros"):
        raise RuntimeError(str(resultado.get("amostra_erros") or "Erro ao promover registro ANFIR."))
    acao = "INSERIDO" if resultado.get("inseridos") else "ATUALIZADO" if resultado.get("atualizados") else "DUPLICADO_IGNORADO"
    return {"acao": acao, "resultado": resultado, "tabela": "cti_anfir", "hash_registro": registro["hash_registro"]}


def promover_item(dominio: str, item: dict[str, Any], *, fonte_nome: str | None = None) -> dict[str, Any]:
    entidade = str(item.get("entidade_sugerida") or "").upper()
    suporte = suporte_promocao(dominio, entidade)
    if not suporte["suportado"]:
        raise ValueError(str(suporte.get("motivo")))
    dados = item.get("dados_normalizados") if isinstance(item.get("dados_normalizados"), dict) else {}
    if dominio == "CRM_COMERCIAL" and entidade == "CLIENTE":
        return promover_cliente(dados)
    if dominio == "CTI_ANFIR" and entidade == "ANFIR":
        return promover_anfir(dados, chave_canonica=str(item.get("chave_canonica") or ""), fonte_nome=fonte_nome)
    raise ValueError("Adaptador de promoção não resolvido.")
