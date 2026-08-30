from __future__ import annotations

import re
import unicodedata
from typing import Any

from core.supabase_client import supabase

CAMPOS_EMPRESA = ("empresa", "cliente", "transportadora", "razao_social", "razão social", "nome_cliente", "nome_proprietario")


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^A-Z0-9]", "", texto)


def _nome_empresa(registro: dict[str, Any]) -> str:
    for campo in CAMPOS_EMPRESA:
        valor = registro.get(campo)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ""


def _mapa_clientes() -> dict[str, dict[str, Any]]:
    try:
        dados = (
            supabase.table("clientes")
            .select("id,nome,cnpj,responsavel_comercial_id,responsabilidade_tipo,sub_regiao")
            .execute()
            .data
            or []
        )
    except Exception:
        return {}
    mapa: dict[str, dict[str, Any]] = {}
    for item in dados:
        chave = _fold(item.get("nome"))
        if chave:
            mapa[chave] = item
    return mapa


def filtrar_por_responsabilidade_cliente(
    registros: list[dict[str, Any]],
    usuario_id: str,
) -> list[dict[str, Any]]:
    """Refina um escopo territorial usando a responsabilidade comercial efetiva.

    Registros sem cliente reconciliado continuam obedecendo ao filtro territorial anterior.
    Quando há cliente reconciliado e responsável explícito, este prevalece. Assim uma conta
    direta Master não reaparece para o vendedor apenas porque está fisicamente no território.
    """
    mapa = _mapa_clientes()
    if not mapa:
        return registros
    saida: list[dict[str, Any]] = []
    for registro in registros:
        cliente = mapa.get(_fold(_nome_empresa(registro)))
        if not cliente:
            saida.append(registro)
            continue
        responsavel_id = str(cliente.get("responsavel_comercial_id") or "")
        if not responsavel_id or responsavel_id == str(usuario_id):
            saida.append(registro)
    return saida
