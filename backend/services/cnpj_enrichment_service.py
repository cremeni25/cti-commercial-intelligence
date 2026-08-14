from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"


def somente_digitos(valor: Any) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def cnpj_valido(valor: Any) -> bool:
    cnpj = somente_digitos(valor)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    for tamanho, pesos in ((12, [5,4,3,2,9,8,7,6,5,4,3,2]), (13, [6,5,4,3,2,9,8,7,6,5,4,3,2])):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(tamanho))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if int(cnpj[tamanho]) != digito:
            return False
    return True


def _texto(payload: dict[str, Any], *chaves: str) -> str | None:
    for chave in chaves:
        valor = payload.get(chave)
        if valor not in (None, ""):
            texto = str(valor).strip()
            if texto:
                return texto
    return None


def normalizar_empresa(payload: dict[str, Any], cnpj: str) -> dict[str, Any]:
    telefone = _texto(payload, "ddd_telefone_1", "telefone")
    ddd = somente_digitos(telefone)[:2] if telefone else None
    return {
        "cnpj": cnpj,
        "nome": _texto(payload, "razao_social", "nome"),
        "nome_fantasia": _texto(payload, "nome_fantasia", "fantasia"),
        "situacao_cadastral": _texto(payload, "descricao_situacao_cadastral", "situacao"),
        "inscricao_estadual": None,
        "endereco": _texto(payload, "logradouro"),
        "numero": _texto(payload, "numero"),
        "complemento": _texto(payload, "complemento"),
        "bairro": _texto(payload, "bairro"),
        "cidade": _texto(payload, "municipio"),
        "estado": (_texto(payload, "uf") or "").upper() or None,
        "cep": somente_digitos(_texto(payload, "cep")) or None,
        "fone": telefone,
        "email": (_texto(payload, "email") or "").lower() or None,
        "ddd": ddd,
        "cnae": _texto(payload, "cnae_fiscal"),
        "cnae_descricao": _texto(payload, "cnae_fiscal_descricao"),
        "fonte": "BrasilAPI / Minha Receita",
    }


def consultar_cnpj_publico(valor: Any, timeout: float = 8.0) -> dict[str, Any]:
    cnpj = somente_digitos(valor)
    if not cnpj_valido(cnpj):
        return {"ok": False, "tipo": "CNPJ_INVALIDO", "cnpj": cnpj, "detail": "CNPJ inválido."}

    base_url = os.getenv("CNPJ_LOOKUP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    request = Request(
        f"{base_url}/{cnpj}",
        headers={"Accept": "application/json", "User-Agent": "CTI-Commercial-Intelligence/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as erro:
        if erro.code == 404:
            return {"ok": False, "tipo": "NAO_ENCONTRADO", "cnpj": cnpj, "detail": "CNPJ não encontrado na fonte cadastral."}
        return {"ok": False, "tipo": "FONTE_INDISPONIVEL", "cnpj": cnpj, "detail": f"Fonte cadastral indisponível ({erro.code})."}
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {"ok": False, "tipo": "FONTE_INDISPONIVEL", "cnpj": cnpj, "detail": "Fonte cadastral temporariamente indisponível."}

    if not isinstance(payload, dict):
        return {"ok": False, "tipo": "RESPOSTA_INVALIDA", "cnpj": cnpj, "detail": "Resposta cadastral inválida."}
    return {"ok": True, "tipo": "ENCONTRADO", "cnpj": cnpj, "dados": normalizar_empresa(payload, cnpj)}
