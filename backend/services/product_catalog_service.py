from __future__ import annotations

import os
import re
import unicodedata
from functools import lru_cache
from typing import Any

from supabase import create_client

from services.product_line_classifier import ALIASES_LINHA, MODELOS_OFICIAIS

TERMOS_GENERICOS_BLOQUEADOS = {
    "CAMINHAO", "TRUCK", "VAN", "FURGAO", "VUC", "CARRETA", "SEMIRREBOQUE",
    "SEMI REBOQUE", "VEICULO", "IMPLEMENTO",
}


def normalizar_alias(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").strip())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = re.sub(r"[^A-Za-z0-9]+", " ", texto).upper()
    return re.sub(r"\s+", " ", texto).strip()


def validar_alias(alias: str) -> str:
    normalizado = normalizar_alias(alias)
    if not normalizado:
        raise ValueError("Alias obrigatório.")
    if normalizado in TERMOS_GENERICOS_BLOQUEADOS:
        raise ValueError("Termo genérico de veículo não pode classificar linha de produto.")
    return normalizado


def _fallback_catalog() -> dict[str, Any]:
    linhas = []
    nomes = {"TR": "Trailer", "DT": "Diesel Truck", "DD": "Direct Drive"}
    for codigo in ("TR", "DT", "DD"):
        modelos = [
            {"canonical_name": canonico, "active": True, "aliases": list(aliases)}
            for canonico, aliases in MODELOS_OFICIAIS[codigo].items()
        ]
        linhas.append({
            "code": codigo,
            "name": nomes[codigo],
            "active": True,
            "aliases": sorted(ALIASES_LINHA[codigo]),
            "models": modelos,
        })
    return {"source": "fallback", "editable": False, "lines": linhas}


@lru_cache(maxsize=1)
def _client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def listar_catalogo() -> dict[str, Any]:
    client = _client()
    if client is None:
        return _fallback_catalog()
    try:
        linhas = client.table("cti_product_lines").select("*").order("code").execute().data or []
        modelos = client.table("cti_product_models").select("*").order("canonical_name").execute().data or []
        aliases = client.table("cti_product_aliases").select("*").order("alias").execute().data or []
        modelos_por_linha: dict[str, list[dict]] = {}
        aliases_por_modelo: dict[str, list[str]] = {}
        aliases_por_linha: dict[str, list[str]] = {}
        for item in aliases:
            if item.get("model_id"):
                aliases_por_modelo.setdefault(item["model_id"], []).append(item["alias"])
            if item.get("line_id"):
                aliases_por_linha.setdefault(item["line_id"], []).append(item["alias"])
        for modelo in modelos:
            modelo["aliases"] = aliases_por_modelo.get(modelo["id"], [])
            modelos_por_linha.setdefault(modelo["line_id"], []).append(modelo)
        for linha in linhas:
            linha["aliases"] = aliases_por_linha.get(linha["id"], [])
            linha["models"] = modelos_por_linha.get(linha["id"], [])
        return {"source": "supabase", "editable": True, "lines": linhas}
    except Exception:
        return _fallback_catalog()


def criar_modelo(line_id: str, canonical_name: str, actor: str | None = None) -> dict:
    client = _client()
    if client is None:
        raise RuntimeError("Supabase não configurado.")
    nome = str(canonical_name or "").strip().upper()
    if not nome:
        raise ValueError("Nome canônico obrigatório.")
    registro = client.table("cti_product_models").insert({"line_id": line_id, "canonical_name": nome}).execute().data[0]
    _auditar("MODEL", registro.get("id"), "CREATE", None, registro, actor)
    listar_catalogo.cache_clear() if hasattr(listar_catalogo, "cache_clear") else None
    return registro


def criar_alias(alias: str, model_id: str | None = None, line_id: str | None = None, actor: str | None = None) -> dict:
    if bool(model_id) == bool(line_id):
        raise ValueError("Informe exatamente um destino: modelo ou linha.")
    client = _client()
    if client is None:
        raise RuntimeError("Supabase não configurado.")
    normalizado = validar_alias(alias)
    payload = {"alias": alias.strip().upper(), "alias_normalized": normalizado, "model_id": model_id, "line_id": line_id}
    registro = client.table("cti_product_aliases").insert(payload).execute().data[0]
    _auditar("ALIAS", registro.get("id"), "CREATE", None, registro, actor)
    return registro


def definir_ativo(tabela: str, entity_type: str, entity_id: str, active: bool, actor: str | None = None) -> dict:
    if tabela not in {"cti_product_lines", "cti_product_models", "cti_product_aliases"}:
        raise ValueError("Entidade inválida.")
    client = _client()
    if client is None:
        raise RuntimeError("Supabase não configurado.")
    anterior = client.table(tabela).select("*").eq("id", entity_id).single().execute().data
    atualizado = client.table(tabela).update({"active": active}).eq("id", entity_id).execute().data[0]
    _auditar(entity_type, entity_id, "ACTIVATE" if active else "DEACTIVATE", anterior, atualizado, actor)
    return atualizado


def _auditar(entity_type: str, entity_id: str | None, action: str, before: dict | None, after: dict | None, actor: str | None):
    client = _client()
    if client is None:
        return
    client.table("cti_product_taxonomy_audit").insert({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "before_data": before,
        "after_data": after,
        "actor": actor,
    }).execute()
