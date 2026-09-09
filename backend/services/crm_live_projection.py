from __future__ import annotations

import os
from collections import defaultdict
from threading import RLock
from time import monotonic
from typing import Any

from core.supabase_client import supabase


FAMILIAS = {
    "trailer": ("TRAILER", "VECTOR", "X4"),
    "diesel-truck": ("DIESEL", "SUPRA"),
    "direct-drive": ("DIRECT", "CITIMAX", "XARIOS", "D6", "D7"),
}

# O Mapa dispara leituras de visão e insights praticamente ao mesmo tempo.
# Sem esta janela curta, cada chamada repete quatro consultas completas ao CRM.
# O TTL é deliberadamente pequeno para preservar a percepção de tempo real.
_CRM_CACHE_TTL_SECONDS = float(os.getenv("CTI_CRM_READ_CACHE_SECONDS", "5") or 5)
_crm_cache_lock = RLock()
_crm_cache: dict[str, Any] = {
    "expires_at": 0.0,
    "source_id": None,
    "registros": None,
}


def _texto(*valores: Any) -> str:
    return " ".join(str(valor or "") for valor in valores).upper()


def _lista_segura(tabela: str) -> list[dict[str, Any]]:
    try:
        return supabase.table(tabela).select("*").execute().data or []
    except Exception:
        return []


def _source_id() -> int:
    # Mantém os testes isolados: monkeypatch de _lista_segura invalida o cache.
    return id(_lista_segura)


def _unicos(valores: list[Any]) -> list[str]:
    saida: list[str] = []
    vistos: set[str] = set()
    for valor in valores:
        texto = str(valor or "").strip()
        chave = texto.upper()
        if texto and chave not in vistos:
            vistos.add(chave)
            saida.append(texto)
    return saida


def _contexto_descricao(descricao: Any) -> dict[str, str]:
    texto = str(descricao or "")
    if "[CONTEXTO CTI]" not in texto:
        return {}
    resultado: dict[str, str] = {}
    for bloco in texto.split("[CONTEXTO CTI]")[1:]:
        for linha in bloco.splitlines():
            if ":" not in linha:
                continue
            chave, valor = linha.split(":", 1)
            chave = chave.strip().lower()
            valor = valor.strip()
            if chave and valor and chave not in resultado:
                resultado[chave] = valor
    return resultado


def familia_item(item: dict[str, Any]) -> str | None:
    texto = _texto(item.get("linha_produto"), item.get("nome_comercial"), item.get("equipamento"), item.get("modelo_base"))
    for slug, termos in FAMILIAS.items():
        if any(termo in texto for termo in termos):
            return slug
    return None


def familias_registro(registro: dict[str, Any]) -> list[str]:
    familias = registro.get("familias")
    if isinstance(familias, list):
        return [str(item) for item in familias if item]
    texto = _texto(registro.get("linha_equipamentos"), registro.get("equipamento"), registro.get("titulo"), registro.get("descricao"))
    return [slug for slug, termos in FAMILIAS.items() if any(termo in texto for termo in termos)]


def equipamentos_registro(registro: dict[str, Any]) -> list[str]:
    valores = registro.get("equipamentos")
    if isinstance(valores, list):
        return _unicos(valores)
    valor = registro.get("equipamento") or registro.get("linha_equipamentos")
    return _unicos([valor])


def _carregar_oportunidades_enriquecidas_sem_cache() -> list[dict[str, Any]]:
    oportunidades = _lista_segura("cti_oportunidades")
    itens_ativos = [item for item in _lista_segura("cti_oportunidade_itens") if not item.get("arquivado_em")]
    por_oportunidade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in itens_ativos:
        oportunidade_id = str(item.get("oportunidade_id") or "").strip()
        if oportunidade_id:
            por_oportunidade[oportunidade_id].append(item)

    nomes_clientes: dict[str, str] = {}
    for tabela in ("clientes", "cti_clientes"):
        for cliente in _lista_segura(tabela):
            cliente_id = str(cliente.get("id") or "").strip()
            nome = str(cliente.get("nome") or cliente.get("razao_social") or cliente.get("nome_fantasia") or "").strip()
            if cliente_id and nome and cliente_id not in nomes_clientes:
                nomes_clientes[cliente_id] = nome

    saida: list[dict[str, Any]] = []
    for oportunidade in oportunidades:
        oportunidade_id = str(oportunidade.get("id") or "").strip()
        itens = por_oportunidade.get(oportunidade_id, [])
        equipamentos = _unicos([item.get("nome_comercial") or item.get("equipamento") or item.get("modelo_base") for item in itens])
        linhas = _unicos([item.get("linha_produto") for item in itens])
        familias = _unicos([familia_item(item) for item in itens])
        contexto = _contexto_descricao(oportunidade.get("descricao"))
        cliente_id = str(oportunidade.get("cliente_id") or "").strip()
        cliente_nome = str(oportunidade.get("cliente_nome") or nomes_clientes.get(cliente_id) or "").strip()

        enriquecida = {
            **oportunidade,
            "cliente_nome": cliente_nome or oportunidade.get("cliente_nome"),
            "equipamentos": equipamentos,
            "equipamento": ", ".join(equipamentos) if equipamentos else oportunidade.get("equipamento"),
            "linhas_equipamentos": linhas,
            "linha_equipamentos": ", ".join(linhas) if linhas else oportunidade.get("linha_equipamentos"),
            "familias": familias or familias_registro(oportunidade),
            "quantidade_total": sum(int(item.get("quantidade") or 0) for item in itens),
            "itens_ativos": len(itens),
            "estado": oportunidade.get("estado") or contexto.get("uf"),
            "municipio": oportunidade.get("municipio") or contexto.get("municipio"),
            "ddd": oportunidade.get("ddd") or contexto.get("ddd"),
        }
        saida.append(enriquecida)
    return saida


def carregar_oportunidades_enriquecidas() -> list[dict[str, Any]]:
    agora = monotonic()
    origem = _source_id()
    registros = _crm_cache.get("registros")
    if (
        registros is not None
        and _crm_cache.get("source_id") == origem
        and agora < float(_crm_cache.get("expires_at") or 0)
    ):
        return [dict(item) for item in registros]

    # Serializa somente a reconstrução da projeção. A segunda leitura concorrente
    # do Mapa recebe a projeção já pronta, em vez de disparar quatro SELECTs novos.
    with _crm_cache_lock:
        agora = monotonic()
        origem = _source_id()
        registros = _crm_cache.get("registros")
        if (
            registros is not None
            and _crm_cache.get("source_id") == origem
            and agora < float(_crm_cache.get("expires_at") or 0)
        ):
            return [dict(item) for item in registros]

        carregados = _carregar_oportunidades_enriquecidas_sem_cache()
        _crm_cache["registros"] = carregados
        _crm_cache["source_id"] = origem
        _crm_cache["expires_at"] = monotonic() + max(_CRM_CACHE_TTL_SECONDS, 1.0)
        return [dict(item) for item in carregados]


def invalidar_cache_oportunidades_enriquecidas() -> None:
    with _crm_cache_lock:
        _crm_cache["expires_at"] = 0.0
        _crm_cache["source_id"] = None
        _crm_cache["registros"] = None
