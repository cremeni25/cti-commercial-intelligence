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

# Continuidade comercial homologada: CARLA é referência histórica e MÔNICA
# assumiu integralmente a região. O alias interpreta a identidade histórica;
# nunca altera o registro bruto nem transfere registros por território.
ALIASES_RESPONSAVEL_ATUAL = {"CARLA": "MONICA"}


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


def _eh_anfir_realizado(registro: dict[str, Any]) -> bool:
    """Identifica o realizado ANFIR sem confundir Funil/CRM com a fonte passada."""
    aba = str(registro.get("aba_origem") or "").strip().upper()
    pipeline = str(registro.get("pipeline") or "").strip().upper()
    versao = str(registro.get("versao_parser") or "").strip()
    return (
        aba.startswith("RELATORIO PERFORMANCE ")
        or versao.startswith("3.1")
        or pipeline == "UPLOAD_ANFIR_OPERACIONAL"
        and "REPRESENTACAO: JOV" in str(registro.get("ocorrencia") or "").upper()
    )


def _primeiro_nome(valor: Any) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return ""
    primeiro = texto.split(" ", 1)[0]
    normalizado = _fold(primeiro)
    return ALIASES_RESPONSAVEL_ATUAL.get(normalizado, normalizado)


def _perfil_usuario(usuario_id: str) -> dict[str, Any]:
    try:
        dados = (
            supabase.table("cti_users")
            .select("id,nome,tipo_usuario,ddds,codigo_regional,ativo")
            .eq("id", usuario_id)
            .limit(1)
            .execute()
            .data
            or []
        )
    except Exception:
        dados = []
    return dados[0] if dados else {}


def _anfir_pertence_ao_responsavel(
    registro: dict[str, Any],
    usuario_id: str,
    nome_usuario: str,
    perfil: dict[str, Any] | None = None,
    territoriais: list[dict[str, Any]] | None = None,
) -> bool:
    """Resolve ANFIR realizada exclusivamente pela autoria gravada na fonte.

    Responsável explícito (id ou nome) prevalece. Registro sem responsável permanece
    sem atribuição individual. DDD, sub-região, carteira atual e território nunca
    reescrevem a autoria histórica da ANFIR.
    """
    responsavel_id = _responsavel_id_registro(registro)
    if responsavel_id:
        return responsavel_id == str(usuario_id)

    perfil = perfil or _perfil_usuario(str(usuario_id))
    nome_alvo = _primeiro_nome(perfil.get("nome") or nome_usuario)
    responsavel_fonte = _primeiro_nome(_responsavel_registro(registro))
    return bool(responsavel_fonte and nome_alvo and responsavel_fonte == nome_alvo)


def filtrar_anfir_por_responsavel_comercial(
    registros: list[dict[str, Any]],
    usuario_id: str,
    nome_usuario: str,
) -> list[dict[str, Any]]:
    """Filtra ANFIR 2026 pela autoria da própria ANFIR, sem transferência posterior.

    A carteira atual do cliente é outra dimensão comercial e não pode sobrescrever o
    responsável histórico. Registros sem responsável não são inferidos por DDD.
    """
    perfil = _perfil_usuario(str(usuario_id))
    return [
        registro
        for registro in registros
        if _anfir_pertence_ao_responsavel(registro, str(usuario_id), nome_usuario, perfil)
    ]


def filtrar_por_responsabilidade_cliente(
    registros: list[dict[str, Any]],
    usuario_id: str,
) -> list[dict[str, Any]]:
    """Refina fontes de carteira atual pela responsabilidade comercial do cliente.

    Esta função não deve ser usada para reatribuir ANFIR realizada.
    """
    por_nome, por_cnpj = _mapas_clientes()
    if not por_nome and not por_cnpj:
        return registros
    saida: list[dict[str, Any]] = []
    for registro in registros:
        if _eh_anfir_realizado(registro):
            # ANFIR não recebe responsabilidade a partir da carteira atual.
            saida.append(registro)
            continue
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
    """Seleciona responsabilidade sem misturar autoria, carteira e território.

    ANFIR realizada usa exclusivamente a autoria da própria fonte. CRM e Funil usam a
    autoria do registro; somente quando ela inexiste a carteira atual pode ser fallback.
    """
    perfil = _perfil_usuario(str(usuario_id))
    por_nome, por_cnpj = _mapas_clientes()
    nome = str(nome_usuario or "").strip()
    primeiro_nome = nome.split(" ", 1)[0] if nome else ""
    chaves_nome = {_fold(nome), _fold(primeiro_nome)} - {""}
    saida: list[dict[str, Any]] = []

    for registro in registros:
        if _eh_anfir_realizado(registro):
            if _anfir_pertence_ao_responsavel(registro, str(usuario_id), nome_usuario, perfil):
                saida.append(registro)
            continue

        responsavel_id_fonte = _responsavel_id_registro(registro)
        if responsavel_id_fonte:
            if responsavel_id_fonte == str(usuario_id):
                saida.append(registro)
            continue

        responsavel_fonte = _fold(_responsavel_registro(registro))
        if responsavel_fonte:
            if any(
                responsavel_fonte == chave or responsavel_fonte.startswith(chave)
                for chave in chaves_nome
            ):
                saida.append(registro)
            continue

        cliente = _cliente_reconciliado(registro, por_nome, por_cnpj) if (por_nome or por_cnpj) else None
        if cliente:
            responsavel_id = str(cliente.get("responsavel_comercial_id") or "")
            if responsavel_id and responsavel_id == str(usuario_id):
                saida.append(registro)

    return saida
