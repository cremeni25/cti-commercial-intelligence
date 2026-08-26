from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.supabase_client import supabase


FAMILIAS = {
    "trailer": ("TRAILER", "VECTOR", "X4"),
    "diesel-truck": ("DIESEL", "SUPRA"),
    "direct-drive": ("DIRECT", "CITIMAX", "XARIOS", "D6", "D7"),
}


def _texto(*valores: Any) -> str:
    return " ".join(str(valor or "") for valor in valores).upper()


def _lista_segura(tabela: str) -> list[dict[str, Any]]:
    try:
        return supabase.table(tabela).select("*").execute().data or []
    except Exception:
        return []


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


def carregar_oportunidades_enriquecidas() -> list[dict[str, Any]]:
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
