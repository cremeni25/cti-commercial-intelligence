from __future__ import annotations

from typing import Any

from routers import ia_comercial_acoes_router as acoes
from services import ia_comercial_dados_semanticos as dados
from services import ia_comercial_universo as universo

PERFIS_CONSOLIDADOS = {"ADMIN_MASTER", "DIRETOR_VIENA_SP"}


def _id(valor: Any) -> str:
    return str(valor or "").strip()


def escopo_crm_autorizado(usuario_id: str, tipo_usuario: str) -> dict[str, list[dict[str, Any]]]:
    """Monta o universo CRM da IA pela cadeia comercial real, sem herdar registros apenas por cliente compartilhado."""
    bruto = {dominio: dados._carregar_dominio(dominio) for dominio in dados.DOMINIOS_TABELAS}
    perfil = _id(tipo_usuario).upper()
    usuario = _id(usuario_id)

    if perfil in PERFIS_CONSOLIDADOS:
        return bruto

    oportunidades = [
        item for item in bruto["oportunidades"]
        if _id(item.get("responsavel_id")) == usuario
    ]
    oportunidade_ids = {_id(item.get("id")) for item in oportunidades if item.get("id")}

    itens = [
        item for item in bruto["itens"]
        if _id(item.get("oportunidade_id")) in oportunidade_ids
    ]
    item_ids = {_id(item.get("id")) for item in itens if item.get("id")}

    propostas = [
        item for item in bruto["propostas"]
        if _id(item.get("oportunidade_id")) in oportunidade_ids
        or _id(item.get("item_oportunidade_id")) in item_ids
    ]
    proposta_ids = {_id(item.get("id")) for item in propostas if item.get("id")}

    aceites = [
        item for item in bruto["aceites"]
        if _id(item.get("proposta_id")) in proposta_ids
    ]
    aceite_ids = {_id(item.get("id")) for item in aceites if item.get("id")}

    pedidos = [
        item for item in bruto["pedidos"]
        if _id(item.get("proposta_id")) in proposta_ids
        or _id(item.get("proposta_aceita_id")) in proposta_ids
        or _id(item.get("item_oportunidade_id")) in item_ids
        or _id(item.get("aceite_id")) in aceite_ids
    ]
    pedido_ids = {_id(item.get("id")) for item in pedidos if item.get("id")}

    atividades = [
        item for item in bruto["atividades"]
        if _id(item.get("usuario_id") or item.get("responsavel_id")) == usuario
        or _id(item.get("oportunidade_id")) in oportunidade_ids
    ]

    vendas = [
        item for item in bruto["vendas"]
        if _id(item.get("pedido_id")) in pedido_ids
        or _id(item.get("oportunidade_id")) in oportunidade_ids
        or _id(item.get("proposta_id")) in proposta_ids
        or _id(item.get("item_oportunidade_id")) in item_ids
    ]

    cliente_ids: set[str] = set()
    for colecao in (oportunidades, propostas, pedidos, atividades, vendas):
        cliente_ids.update(
            _id(item.get("cliente_id"))
            for item in colecao
            if item.get("cliente_id")
        )
    clientes = [
        item for item in bruto["clientes"]
        if _id(item.get("id")) in cliente_ids
    ]

    return {
        "clientes": clientes,
        "oportunidades": oportunidades,
        "itens": itens,
        "propostas": propostas,
        "aceites": aceites,
        "pedidos": pedidos,
        "atividades": atividades,
        "vendas": vendas,
    }


def aplicar_patch_rbac_ia() -> None:
    # Ambos os módulos importam a função histórica por referência. Substituí-la
    # nos pontos de consumo mantém leitura e ações controladas no mesmo escopo.
    universo._escopo_autorizado = escopo_crm_autorizado
    acoes._escopo_autorizado = escopo_crm_autorizado


aplicar_patch_rbac_ia()
