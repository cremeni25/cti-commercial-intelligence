from __future__ import annotations

import re
import unicodedata
from typing import Any

from core.supabase_client import supabase

CAMPOS_EMPRESA = (
    "empresa",
    "cliente",
    "cliente_nome",
    "transportadora",
    "razao_social",
    "razão social",
    "nome_cliente",
    "nome_proprietario",
)
CAMPOS_CNPJ = ("cnpj", "cliente_cnpj", "cnpj_cliente", "documento")
CAMPOS_RESPONSAVEL = (
    "responsavel",
    "responsavel_nome",
    "vendedor",
    "consultor",
    "representante_atual",
    "representante",
)
CAMPOS_RESPONSAVEL_ID = ("responsavel_id", "responsavel_comercial_id", "vendedor_id", "consultor_id")


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^A-Z0-9]", "", texto)


def _somente_digitos(valor: Any) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _nome_empresa(registro: dict[str, Any]) -> str:
    for campo in CAMPOS_EMPRESA:
        valor = registro.get(campo)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ""


def _cnpj_empresa(registro: dict[str, Any]) -> str:
    for campo in CAMPOS_CNPJ:
        valor = _somente_digitos(registro.get(campo))
        if len(valor) >= 14:
            return valor[-14:]
    return ""


def _responsavel_registro(registro: dict[str, Any]) -> str:
    for campo in CAMPOS_RESPONSAVEL:
        valor = str(registro.get(campo) or "").strip()
        if valor:
            return valor
    return ""


def _responsavel_id_registro(registro: dict[str, Any]) -> str:
    for campo in CAMPOS_RESPONSAVEL_ID:
        valor = str(registro.get(campo) or "").strip()
        if valor:
            return valor
    return ""


def _mapa_clientes() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    try:
        dados = (
            supabase.table("clientes")
            .select("id,nome,cnpj,responsavel_comercial_id,responsabilidade_tipo,sub_regiao")
            .execute()
            .data
            or []
        )
    except Exception:
        return {}, {}
    por_nome: dict[str, dict[str, Any]] = {}
    por_cnpj: dict[str, dict[str, Any]] = {}
    for item in dados:
        chave_nome = _fold(item.get("nome"))
        if chave_nome:
            por_nome[chave_nome] = item
        chave_cnpj = _somente_digitos(item.get("cnpj"))
        if len(chave_cnpj) >= 14:
            por_cnpj[chave_cnpj[-14:]] = item
    return por_nome, por_cnpj


def _mapas_clientes() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Aceita o contrato novo (nome, CNPJ) e o mapa legado usado pelos testes/homologações."""
    mapa = _mapa_clientes()
    if isinstance(mapa, tuple):
        return mapa
    if isinstance(mapa, dict):
        return mapa, {}
    return {}, {}


def _cliente_reconciliado(
    registro: dict[str, Any],
    por_nome: dict[str, dict[str, Any]],
    por_cnpj: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    cnpj = _cnpj_empresa(registro)
    if cnpj and cnpj in por_cnpj:
        return por_cnpj[cnpj]
    nome = _fold(_nome_empresa(registro))
    return por_nome.get(nome) if nome else None


def filtrar_por_responsabilidade_cliente(
    registros: list[dict[str, Any]],
    usuario_id: str,
) -> list[dict[str, Any]]:
    """Refina um escopo territorial usando a responsabilidade comercial efetiva.

    Registros sem cliente reconciliado continuam obedecendo ao filtro territorial anterior.
    Quando há cliente reconciliado e responsável explícito, este prevalece. Assim uma conta
    direta Master não reaparece para o vendedor apenas porque está fisicamente no território.
    """
    por_nome, por_cnpj = _mapas_clientes()
    if not por_nome and not por_cnpj:
        return registros
    saida: list[dict[str, Any]] = []
    for registro in registros:
        cliente = _cliente_reconciliado(registro, por_nome, por_cnpj)
        if not cliente:
            saida.append(registro)
            continue
        responsavel_id = str(cliente.get("responsavel_comercial_id") or "")
        if not responsavel_id or responsavel_id == str(usuario_id):
            saida.append(registro)
    return saida


def filtrar_carteira_exata_responsavel(
    registros: list[dict[str, Any]],
    usuario_id: str,
    nome_usuario: str,
) -> list[dict[str, Any]]:
    """Seleciona a mesma carteira canônica em ANFIR, Histórico/Funil e CRM.

    A identidade do cliente reconciliado no cadastro CTI é a regra prioritária e vale para
    qualquer fonte. Quando ainda não existe reconciliação, a função usa primeiro o ID de
    responsável existente no registro e depois o nome de responsabilidade/autoria da fonte.
    Isso impede que ANFIR, Histórico e CRM decidam carteiras diferentes para o mesmo cenário.
    """
    por_nome, por_cnpj = _mapas_clientes()
    nome = str(nome_usuario or "").strip()
    primeiro_nome = nome.split(" ", 1)[0] if nome else ""
    chaves_nome = {_fold(nome), _fold(primeiro_nome)} - {""}
    saida: list[dict[str, Any]] = []
    for registro in registros:
        cliente = _cliente_reconciliado(registro, por_nome, por_cnpj) if (por_nome or por_cnpj) else None
        if cliente:
            responsavel_id = str(cliente.get("responsavel_comercial_id") or "")
            if responsavel_id:
                if responsavel_id == str(usuario_id):
                    saida.append(registro)
                continue

        responsavel_id_fonte = _responsavel_id_registro(registro)
        if responsavel_id_fonte:
            if responsavel_id_fonte == str(usuario_id):
                saida.append(registro)
            continue

        responsavel_fonte = _fold(_responsavel_registro(registro))
        if responsavel_fonte and any(
            responsavel_fonte == chave or responsavel_fonte.startswith(chave)
            for chave in chaves_nome
        ):
            saida.append(registro)
    return saida
