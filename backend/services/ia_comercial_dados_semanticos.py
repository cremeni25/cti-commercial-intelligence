from __future__ import annotations

import json
from typing import Any

from services.ia_comercial_cti import _consulta_segura

DOMINIOS_TABELAS = {
    "clientes": ("clientes", "cti_clientes"),
    "oportunidades": ("cti_oportunidades",),
    "itens": ("cti_oportunidade_itens",),
    "propostas": ("cti_propostas",),
    "pedidos": ("cti_pedidos",),
    "atividades": ("cti_atividades",),
    "vendas": ("vendas",),
}

ETAPAS_PEDIDO = ["PEDIDO", "CARRIER", "FATURADO", "ENTREGUE", "INSTALADO", "ENCERRADO"]


def _normalizar(valor: Any) -> str:
    return str(valor or "").strip().casefold()


def _carregar_dominio(dominio: str) -> list[dict[str, Any]]:
    tabelas = DOMINIOS_TABELAS.get(dominio)
    if not tabelas:
        return []
    for tabela in tabelas:
        registros = _consulta_segura(tabela)
        if registros:
            return registros
    return []


def _escopo_autorizado(usuario_id: str, tipo_usuario: str) -> dict[str, list[dict[str, Any]]]:
    oportunidades = _carregar_dominio("oportunidades")
    clientes = _carregar_dominio("clientes")
    propostas = _carregar_dominio("propostas")
    pedidos = _carregar_dominio("pedidos")
    atividades = _carregar_dominio("atividades")
    itens = _carregar_dominio("itens")
    vendas = _carregar_dominio("vendas")

    if tipo_usuario == "ADMIN_MASTER":
        return {
            "clientes": clientes,
            "oportunidades": oportunidades,
            "itens": itens,
            "propostas": propostas,
            "pedidos": pedidos,
            "atividades": atividades,
            "vendas": vendas,
        }

    oportunidades = [
        item
        for item in oportunidades
        if str(item.get("responsavel_id") or "") == usuario_id
    ]
    oportunidade_ids = {str(item.get("id")) for item in oportunidades if item.get("id")}
    cliente_ids = {str(item.get("cliente_id")) for item in oportunidades if item.get("cliente_id")}

    clientes = [item for item in clientes if str(item.get("id") or "") in cliente_ids]
    propostas = [item for item in propostas if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    proposta_ids = {str(item.get("id")) for item in propostas if item.get("id")}
    pedidos = [
        item
        for item in pedidos
        if (
            str(item.get("proposta_id") or "") in proposta_ids
            or str(item.get("proposta_aceita_id") or "") in proposta_ids
            or str(item.get("cliente_id") or "") in cliente_ids
        )
    ]
    itens = [item for item in itens if str(item.get("oportunidade_id") or "") in oportunidade_ids]
    atividades = [
        item
        for item in atividades
        if str(item.get("responsavel_id") or item.get("usuario_id") or "") == usuario_id
    ]
    pedido_ids = {str(item.get("id")) for item in pedidos if item.get("id")}
    vendas = [
        item
        for item in vendas
        if (
            str(item.get("pedido_id") or "") in pedido_ids
            or str(item.get("oportunidade_id") or "") in oportunidade_ids
            or str(item.get("cliente_id") or "") in cliente_ids
        )
    ]

    return {
        "clientes": clientes,
        "oportunidades": oportunidades,
        "itens": itens,
        "propostas": propostas,
        "pedidos": pedidos,
        "atividades": atividades,
        "vendas": vendas,
    }


def _mapa_por_id(registros: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in registros
        if isinstance(item, dict) and item.get("id")
    }


def _cliente_publico(cliente: dict[str, Any] | None) -> dict[str, Any] | None:
    if not cliente:
        return None
    return {
        "id": cliente.get("id"),
        "nome": cliente.get("nome") or cliente.get("cliente"),
        "cidade": cliente.get("cidade"),
        "uf": cliente.get("uf") or cliente.get("estado"),
    }


def _semantica_ciclo_pedido(pedido: dict[str, Any]) -> dict[str, Any]:
    etapa = str(pedido.get("status_ciclo") or "PEDIDO").strip().upper()
    if etapa not in ETAPAS_PEDIDO:
        etapa = "PEDIDO"
    indice = ETAPAS_PEDIDO.index(etapa)
    encerrado = etapa == "ENCERRADO" or bool(pedido.get("encerrado_em"))
    proxima_etapa = None if encerrado else ETAPAS_PEDIDO[min(indice + 1, len(ETAPAS_PEDIDO) - 1)]

    pendencias: list[str] = []
    inconsistencias: list[str] = []

    if etapa == "PEDIDO":
        if not pedido.get("enviado_carrier_em") and str(pedido.get("status_envio_carrier") or "").upper() != "ENVIADO":
            pendencias.append("enviar pedido à Carrier e registrar o protocolo real de envio")
        else:
            inconsistencias.append("pedido ainda em PEDIDO apesar de existir indicação de envio à Carrier")
    elif etapa == "CARRIER":
        pendencias.append("registrar faturamento com número da NF e número de série constante na NF")
    elif etapa == "FATURADO":
        pendencias.append("registrar entrega do equipamento")
    elif etapa == "ENTREGUE":
        pendencias.append("registrar instalação e número de série efetivamente instalado")
    elif etapa == "INSTALADO":
        pendencias.append("encerrar o ciclo operacional")

    if ETAPAS_PEDIDO.index(etapa) >= ETAPAS_PEDIDO.index("FATURADO"):
        if not pedido.get("faturado_em"):
            inconsistencias.append("etapa FATURADO ou posterior sem faturado_em")
        if not pedido.get("numero_nf"):
            inconsistencias.append("etapa FATURADO ou posterior sem numero_nf")
        if not pedido.get("numero_serie_nf"):
            inconsistencias.append("etapa FATURADO ou posterior sem numero_serie_nf")
    if ETAPAS_PEDIDO.index(etapa) >= ETAPAS_PEDIDO.index("ENTREGUE") and not pedido.get("entregue_em"):
        inconsistencias.append("etapa ENTREGUE ou posterior sem entregue_em")
    if ETAPAS_PEDIDO.index(etapa) >= ETAPAS_PEDIDO.index("INSTALADO"):
        if not pedido.get("instalado_em"):
            inconsistencias.append("etapa INSTALADO ou posterior sem instalado_em")
        if not pedido.get("numero_serie_instalado"):
            inconsistencias.append("etapa INSTALADO ou posterior sem numero_serie_instalado")
    if encerrado and not pedido.get("encerrado_em"):
        inconsistencias.append("pedido encerrado sem encerrado_em")
    if (
        pedido.get("numero_serie_nf")
        and pedido.get("numero_serie_instalado")
        and str(pedido.get("numero_serie_nf")).strip().upper()
        != str(pedido.get("numero_serie_instalado")).strip().upper()
    ):
        inconsistencias.append("número de série instalado diverge do número de série da NF")

    return {
        "etapa_atual": etapa,
        "proxima_etapa": proxima_etapa,
        "encerrado": encerrado,
        "pendencias_operacionais": pendencias,
        "inconsistencias_qualidade": inconsistencias,
        "regra": "PEDIDO → CARRIER → FATURADO → ENTREGUE → INSTALADO → ENCERRADO; CARRIER depende de envio real/protocolo, FATURADO exige NF e série, INSTALADO exige série instalada e ENCERRADO exige instalação",
    }


def _enriquecer_pedidos(
    pedidos: list[dict[str, Any]],
    escopo: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    clientes_por_id = _mapa_por_id(escopo.get("clientes", []))
    propostas_por_id = _mapa_por_id(escopo.get("propostas", []))
    oportunidades_por_id = _mapa_por_id(escopo.get("oportunidades", []))
    itens_por_id = _mapa_por_id(escopo.get("itens", []))
    vendas_por_pedido: dict[str, list[dict[str, Any]]] = {}
    for venda in escopo.get("vendas", []):
        pedido_id = str(venda.get("pedido_id") or "")
        if pedido_id:
            vendas_por_pedido.setdefault(pedido_id, []).append(venda)

    resultado: list[dict[str, Any]] = []
    for pedido in pedidos:
        if not isinstance(pedido, dict):
            continue
        item = dict(pedido)
        proposta_id = str(item.get("proposta_aceita_id") or item.get("proposta_id") or "")
        proposta = propostas_por_id.get(proposta_id)
        oportunidade = oportunidades_por_id.get(str((proposta or {}).get("oportunidade_id") or ""))
        item_oportunidade = itens_por_id.get(str(item.get("item_oportunidade_id") or ""))
        cliente = clientes_por_id.get(str(item.get("cliente_id") or ""))
        vendas_vinculadas = vendas_por_pedido.get(str(item.get("id") or ""), [])

        item["vinculos_resolvidos"] = {
            "cliente": _cliente_publico(cliente),
            "proposta": (
                {
                    "id": proposta.get("id"),
                    "numero": proposta.get("numero"),
                    "status": proposta.get("status"),
                    "status_documento": proposta.get("status_documento"),
                    "aceita_em": proposta.get("aceita_em"),
                }
                if proposta
                else None
            ),
            "oportunidade": (
                {
                    "id": oportunidade.get("id"),
                    "nome": oportunidade.get("nome") or oportunidade.get("titulo"),
                    "status": oportunidade.get("status"),
                }
                if oportunidade
                else None
            ),
            "item_oportunidade": (
                {
                    "id": item_oportunidade.get("id"),
                    "linha_produto": item_oportunidade.get("linha_produto"),
                    "equipamento": item_oportunidade.get("equipamento"),
                    "equipamento_codigo": item_oportunidade.get("equipamento_codigo"),
                    "quantidade": item_oportunidade.get("quantidade"),
                    "valor_total": item_oportunidade.get("valor_total"),
                }
                if item_oportunidade
                else None
            ),
            "vendas": [
                {
                    "id": venda.get("id"),
                    "valor": venda.get("valor"),
                    "data_venda": venda.get("data_venda"),
                    "equipamento_codigo": venda.get("equipamento_codigo"),
                }
                for venda in vendas_vinculadas
            ],
        }
        item["semantica_ciclo"] = _semantica_ciclo_pedido(item)
        resultado.append(item)
    return resultado


def _enriquecer_vendas(
    vendas: list[dict[str, Any]],
    clientes: list[dict[str, Any]],
    oportunidades: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    clientes_por_id = _mapa_por_id(clientes)
    oportunidades_por_id = _mapa_por_id(oportunidades)
    equipamentos_por_id = _mapa_por_id(_consulta_segura("equipamentos"))
    catalogo_por_codigo = {
        str(item.get("codigo")): item
        for item in _consulta_segura("cti_catalogo_equipamentos")
        if isinstance(item, dict) and item.get("codigo")
    }

    resultado: list[dict[str, Any]] = []
    for venda in vendas:
        if not isinstance(venda, dict):
            continue
        item = dict(venda)
        cliente = clientes_por_id.get(str(item.get("cliente_id") or ""))
        oportunidade = oportunidades_por_id.get(str(item.get("oportunidade_id") or ""))
        equipamento_legado = equipamentos_por_id.get(str(item.get("equipamento_id") or ""))
        equipamento_catalogo = catalogo_por_codigo.get(str(item.get("equipamento_codigo") or ""))

        item["vinculos_resolvidos"] = {
            "cliente": _cliente_publico(cliente),
            "oportunidade": (
                {
                    "id": oportunidade.get("id"),
                    "nome": oportunidade.get("nome") or oportunidade.get("titulo"),
                    "status": oportunidade.get("status"),
                }
                if oportunidade
                else None
            ),
            "equipamento": (
                {
                    "origem": "catalogo_comercial",
                    "codigo": equipamento_catalogo.get("codigo"),
                    "modelo": equipamento_catalogo.get("modelo_base") or equipamento_catalogo.get("nome_comercial"),
                    "linha": equipamento_catalogo.get("linha"),
                }
                if equipamento_catalogo
                else (
                    {
                        "origem": "equipamentos_legado",
                        "id": equipamento_legado.get("id"),
                        "modelo": equipamento_legado.get("modelo"),
                        "linha": equipamento_legado.get("linha"),
                        "observacao": equipamento_legado.get("observacao"),
                    }
                    if equipamento_legado
                    else None
                )
            ),
        }
        resultado.append(item)
    return resultado


def consultar_dominio_semantico(
    dominio: str,
    usuario_id: str,
    tipo_usuario: str,
    *,
    termo: str | None = None,
    status: str | None = None,
    limite: int = 30,
    offset: int = 0,
) -> dict[str, Any]:
    if dominio not in DOMINIOS_TABELAS:
        return {"erro": "Domínio CTI não autorizado.", "dominio": dominio}

    limite = max(1, min(int(limite or 30), 100))
    offset = max(0, int(offset or 0))
    escopo = _escopo_autorizado(usuario_id, tipo_usuario)
    registros = escopo.get(dominio, [])

    if dominio == "vendas":
        registros = _enriquecer_vendas(
            registros,
            escopo.get("clientes", []),
            escopo.get("oportunidades", []),
        )
    elif dominio == "pedidos":
        registros = _enriquecer_pedidos(registros, escopo)

    if termo:
        alvo = _normalizar(termo)
        registros = [
            item
            for item in registros
            if alvo in _normalizar(json.dumps(item, ensure_ascii=False, default=str))
        ]

    if status:
        alvo_status = _normalizar(status)
        registros = [item for item in registros if _normalizar(item.get("status")) == alvo_status]

    total = len(registros)
    pagina = registros[offset : offset + limite]

    return {
        "dominio": dominio,
        "escopo": "global" if tipo_usuario == "ADMIN_MASTER" else "usuario_autorizado",
        "total_encontrado": total,
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + len(pagina) < total,
        "resultado": pagina,
    }
