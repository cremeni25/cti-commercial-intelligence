from __future__ import annotations

import json
from typing import Any

from services.ia_comercial_cti import _consulta_segura

DOMINIOS_TABELAS = {
    "clientes": ("clientes", "cti_clientes"),
    "oportunidades": ("cti_oportunidades",),
    "itens": ("cti_oportunidade_itens",),
    "propostas": ("cti_propostas",),
    "aceites": ("cti_proposta_aceites",),
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


def _mapa_por_id(registros: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in registros if isinstance(item, dict) and item.get("id")}


def _agrupar(registros: list[dict[str, Any]], campo: str) -> dict[str, list[dict[str, Any]]]:
    resultado: dict[str, list[dict[str, Any]]] = {}
    for item in registros:
        chave = str(item.get(campo) or "")
        if chave:
            resultado.setdefault(chave, []).append(item)
    return resultado


def _cliente_publico(cliente: dict[str, Any] | None) -> dict[str, Any] | None:
    if not cliente:
        return None
    return {
        "id": cliente.get("id"),
        "nome": cliente.get("nome") or cliente.get("cliente"),
        "cidade": cliente.get("cidade"),
        "uf": cliente.get("uf") or cliente.get("estado"),
    }


def _escopo_autorizado(usuario_id: str, tipo_usuario: str) -> dict[str, list[dict[str, Any]]]:
    escopo = {dominio: _carregar_dominio(dominio) for dominio in DOMINIOS_TABELAS}
    if tipo_usuario == "ADMIN_MASTER":
        return escopo

    oportunidades = [x for x in escopo["oportunidades"] if str(x.get("responsavel_id") or "") == usuario_id]
    oportunidade_ids = {str(x.get("id")) for x in oportunidades if x.get("id")}
    cliente_ids = {str(x.get("cliente_id")) for x in oportunidades if x.get("cliente_id")}
    clientes = [x for x in escopo["clientes"] if str(x.get("id") or "") in cliente_ids]
    itens = [x for x in escopo["itens"] if str(x.get("oportunidade_id") or "") in oportunidade_ids]
    propostas = [x for x in escopo["propostas"] if str(x.get("oportunidade_id") or "") in oportunidade_ids]
    proposta_ids = {str(x.get("id")) for x in propostas if x.get("id")}
    aceites = [x for x in escopo["aceites"] if str(x.get("proposta_id") or "") in proposta_ids]
    pedidos = [
        x for x in escopo["pedidos"]
        if str(x.get("proposta_id") or "") in proposta_ids
        or str(x.get("proposta_aceita_id") or "") in proposta_ids
        or str(x.get("cliente_id") or "") in cliente_ids
    ]
    pedido_ids = {str(x.get("id")) for x in pedidos if x.get("id")}
    atividades = [
        x for x in escopo["atividades"]
        if str(x.get("usuario_id") or x.get("responsavel_id") or "") == usuario_id
        or str(x.get("oportunidade_id") or "") in oportunidade_ids
        or str(x.get("cliente_id") or "") in cliente_ids
    ]
    vendas = [
        x for x in escopo["vendas"]
        if str(x.get("pedido_id") or "") in pedido_ids
        or str(x.get("oportunidade_id") or "") in oportunidade_ids
        or str(x.get("cliente_id") or "") in cliente_ids
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


def _semantica_ciclo_pedido(pedido: dict[str, Any]) -> dict[str, Any]:
    etapa = str(pedido.get("status_ciclo") or "PEDIDO").strip().upper()
    if etapa not in ETAPAS_PEDIDO:
        etapa = "PEDIDO"
    indice = ETAPAS_PEDIDO.index(etapa)
    encerrado = etapa == "ENCERRADO" or bool(pedido.get("encerrado_em"))
    proxima = None if encerrado else ETAPAS_PEDIDO[indice + 1]
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

    if indice >= ETAPAS_PEDIDO.index("FATURADO"):
        for campo, texto in (
            ("faturado_em", "etapa FATURADO ou posterior sem faturado_em"),
            ("numero_nf", "etapa FATURADO ou posterior sem numero_nf"),
            ("numero_serie_nf", "etapa FATURADO ou posterior sem numero_serie_nf"),
        ):
            if not pedido.get(campo):
                inconsistencias.append(texto)
    if indice >= ETAPAS_PEDIDO.index("ENTREGUE") and not pedido.get("entregue_em"):
        inconsistencias.append("etapa ENTREGUE ou posterior sem entregue_em")
    if indice >= ETAPAS_PEDIDO.index("INSTALADO"):
        if not pedido.get("instalado_em"):
            inconsistencias.append("etapa INSTALADO ou posterior sem instalado_em")
        if not pedido.get("numero_serie_instalado"):
            inconsistencias.append("etapa INSTALADO ou posterior sem numero_serie_instalado")
    if encerrado and not pedido.get("encerrado_em"):
        inconsistencias.append("pedido encerrado sem encerrado_em")
    if pedido.get("numero_serie_nf") and pedido.get("numero_serie_instalado") and str(pedido.get("numero_serie_nf")).strip().upper() != str(pedido.get("numero_serie_instalado")).strip().upper():
        inconsistencias.append("número de série instalado diverge do número de série da NF")

    return {
        "etapa_atual": etapa,
        "proxima_etapa": proxima,
        "encerrado": encerrado,
        "pendencias_operacionais": pendencias,
        "inconsistencias_qualidade": inconsistencias,
        "regra": "PEDIDO → CARRIER → FATURADO → ENTREGUE → INSTALADO → ENCERRADO",
    }


def _semantica_proposta(proposta: dict[str, Any], aceite: dict[str, Any] | None, pedidos: list[dict[str, Any]]) -> dict[str, Any]:
    status = str(proposta.get("status") or proposta.get("status_documento") or "").strip().upper()
    aceita = bool(proposta.get("aceita_em")) or bool(aceite and (aceite.get("aceito_em") or str(aceite.get("status") or "").upper() in {"ACEITO", "ACEITA", "APROVADO"}))
    recusada = bool(proposta.get("recusada_em")) or bool(aceite and (aceite.get("recusado_em") or str(aceite.get("status") or "").upper() in {"RECUSADO", "RECUSADA"}))
    pedido_gerado = bool(pedidos)
    pendencias: list[str] = []
    inconsistencias: list[str] = []
    if aceita and not pedido_gerado:
        pendencias.append("gerar pedido a partir da proposta aceita")
    if pedido_gerado and not aceita:
        inconsistencias.append("existe pedido vinculado sem evidência de aceite da proposta")
    if aceita and recusada:
        inconsistencias.append("proposta contém evidências simultâneas de aceite e recusa")
    return {
        "status_registrado": status,
        "aceita": aceita,
        "recusada": recusada,
        "pedido_gerado": pedido_gerado,
        "pendencias_operacionais": pendencias,
        "inconsistencias_qualidade": inconsistencias,
    }


def _enriquecer_propostas(registros: list[dict[str, Any]], escopo: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    clientes = _mapa_por_id(escopo["clientes"])
    oportunidades = _mapa_por_id(escopo["oportunidades"])
    itens = _mapa_por_id(escopo["itens"])
    aceites_por_proposta = _agrupar(escopo["aceites"], "proposta_id")
    pedidos_por_proposta: dict[str, list[dict[str, Any]]] = {}
    for pedido in escopo["pedidos"]:
        for chave in {str(pedido.get("proposta_id") or ""), str(pedido.get("proposta_aceita_id") or "")} - {""}:
            pedidos_por_proposta.setdefault(chave, []).append(pedido)
    saida = []
    for proposta in registros:
        item = dict(proposta)
        aceite = (aceites_por_proposta.get(str(item.get("id") or "")) or [None])[-1]
        pedidos = pedidos_por_proposta.get(str(item.get("id") or ""), [])
        oportunidade = oportunidades.get(str(item.get("oportunidade_id") or ""))
        item_opp = itens.get(str(item.get("item_oportunidade_id") or ""))
        item["vinculos_resolvidos"] = {
            "cliente": _cliente_publico(clientes.get(str(item.get("cliente_id") or ""))),
            "oportunidade": {"id": oportunidade.get("id"), "titulo": oportunidade.get("titulo"), "status": oportunidade.get("status")} if oportunidade else None,
            "item_oportunidade": {"id": item_opp.get("id"), "linha_produto": item_opp.get("linha_produto"), "equipamento": item_opp.get("equipamento"), "equipamento_codigo": item_opp.get("equipamento_codigo"), "quantidade": item_opp.get("quantidade"), "valor_total": item_opp.get("valor_total")} if item_opp else None,
            "aceite": {"id": aceite.get("id"), "status": aceite.get("status"), "metodo": aceite.get("metodo"), "aceito_em": aceite.get("aceito_em"), "recusado_em": aceite.get("recusado_em")} if aceite else None,
            "pedidos": [{"id": p.get("id"), "numero": p.get("numero"), "status": p.get("status"), "status_ciclo": p.get("status_ciclo")} for p in pedidos],
        }
        item["semantica_proposta"] = _semantica_proposta(item, aceite, pedidos)
        saida.append(item)
    return saida


def _enriquecer_pedidos(registros: list[dict[str, Any]], escopo: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    clientes = _mapa_por_id(escopo["clientes"])
    propostas = _mapa_por_id(escopo["propostas"])
    oportunidades = _mapa_por_id(escopo["oportunidades"])
    itens = _mapa_por_id(escopo["itens"])
    aceites = _mapa_por_id(escopo["aceites"])
    vendas_por_pedido = _agrupar(escopo["vendas"], "pedido_id")
    atividades_por_oportunidade = _agrupar(escopo["atividades"], "oportunidade_id")
    saida = []
    for pedido in registros:
        item = dict(pedido)
        proposta = propostas.get(str(item.get("proposta_aceita_id") or item.get("proposta_id") or ""))
        oportunidade = oportunidades.get(str((proposta or {}).get("oportunidade_id") or ""))
        item_opp = itens.get(str(item.get("item_oportunidade_id") or ""))
        aceite = aceites.get(str(item.get("aceite_id") or ""))
        vendas = vendas_por_pedido.get(str(item.get("id") or ""), [])
        atividades = atividades_por_oportunidade.get(str((oportunidade or {}).get("id") or ""), [])
        item["vinculos_resolvidos"] = {
            "cliente": _cliente_publico(clientes.get(str(item.get("cliente_id") or ""))),
            "proposta": {"id": proposta.get("id"), "numero": proposta.get("numero"), "status": proposta.get("status"), "status_documento": proposta.get("status_documento"), "aceita_em": proposta.get("aceita_em")} if proposta else None,
            "aceite": {"id": aceite.get("id"), "status": aceite.get("status"), "metodo": aceite.get("metodo"), "aceito_em": aceite.get("aceito_em")} if aceite else None,
            "oportunidade": {"id": oportunidade.get("id"), "titulo": oportunidade.get("titulo"), "status": oportunidade.get("status")} if oportunidade else None,
            "item_oportunidade": {"id": item_opp.get("id"), "linha_produto": item_opp.get("linha_produto"), "equipamento": item_opp.get("equipamento"), "equipamento_codigo": item_opp.get("equipamento_codigo"), "quantidade": item_opp.get("quantidade"), "valor_total": item_opp.get("valor_total")} if item_opp else None,
            "vendas": [{"id": v.get("id"), "valor": v.get("valor"), "data_venda": v.get("data_venda"), "equipamento_codigo": v.get("equipamento_codigo")} for v in vendas],
            "atividades": [{"id": a.get("id"), "tipo": a.get("tipo"), "status": a.get("status"), "data_atividade": a.get("data_atividade"), "descricao": a.get("descricao")} for a in atividades],
        }
        item["semantica_ciclo"] = _semantica_ciclo_pedido(item)
        saida.append(item)
    return saida


def _enriquecer_atividades(registros: list[dict[str, Any]], escopo: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    clientes = _mapa_por_id(escopo["clientes"])
    oportunidades = _mapa_por_id(escopo["oportunidades"])
    saida = []
    for atividade in registros:
        item = dict(atividade)
        oportunidade = oportunidades.get(str(item.get("oportunidade_id") or ""))
        item["vinculos_resolvidos"] = {
            "cliente": _cliente_publico(clientes.get(str(item.get("cliente_id") or ""))),
            "oportunidade": {"id": oportunidade.get("id"), "titulo": oportunidade.get("titulo"), "status": oportunidade.get("status")} if oportunidade else None,
        }
        saida.append(item)
    return saida


def _enriquecer_vendas(registros: list[dict[str, Any]], escopo: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    clientes = _mapa_por_id(escopo["clientes"])
    oportunidades = _mapa_por_id(escopo["oportunidades"])
    pedidos = _mapa_por_id(escopo["pedidos"])
    equipamentos = _mapa_por_id(_consulta_segura("equipamentos"))
    catalogo = {str(x.get("codigo")): x for x in _consulta_segura("cti_catalogo_equipamentos") if isinstance(x, dict) and x.get("codigo")}
    saida = []
    for venda in registros:
        item = dict(venda)
        oportunidade = oportunidades.get(str(item.get("oportunidade_id") or ""))
        pedido = pedidos.get(str(item.get("pedido_id") or ""))
        equipamento_catalogo = catalogo.get(str(item.get("equipamento_codigo") or ""))
        equipamento_legado = equipamentos.get(str(item.get("equipamento_id") or ""))
        item["vinculos_resolvidos"] = {
            "cliente": _cliente_publico(clientes.get(str(item.get("cliente_id") or ""))),
            "oportunidade": {"id": oportunidade.get("id"), "titulo": oportunidade.get("titulo"), "status": oportunidade.get("status")} if oportunidade else None,
            "pedido": {"id": pedido.get("id"), "numero": pedido.get("numero"), "status": pedido.get("status"), "status_ciclo": pedido.get("status_ciclo")} if pedido else None,
            "equipamento": ({"origem": "catalogo_comercial", "codigo": equipamento_catalogo.get("codigo"), "modelo": equipamento_catalogo.get("modelo_base") or equipamento_catalogo.get("nome_comercial"), "linha": equipamento_catalogo.get("linha")} if equipamento_catalogo else ({"origem": "equipamentos_legado", "id": equipamento_legado.get("id"), "modelo": equipamento_legado.get("modelo"), "linha": equipamento_legado.get("linha")} if equipamento_legado else None)),
        }
        saida.append(item)
    return saida


def consultar_dominio_semantico(dominio: str, usuario_id: str, tipo_usuario: str, *, termo: str | None = None, status: str | None = None, limite: int = 30, offset: int = 0) -> dict[str, Any]:
    if dominio not in DOMINIOS_TABELAS:
        return {"erro": "Domínio CTI não autorizado.", "dominio": dominio}
    limite = max(1, min(int(limite or 30), 100))
    offset = max(0, int(offset or 0))
    escopo = _escopo_autorizado(usuario_id, tipo_usuario)
    registros = escopo.get(dominio, [])

    if dominio == "propostas":
        registros = _enriquecer_propostas(registros, escopo)
    elif dominio == "pedidos":
        registros = _enriquecer_pedidos(registros, escopo)
    elif dominio == "atividades":
        registros = _enriquecer_atividades(registros, escopo)
    elif dominio == "vendas":
        registros = _enriquecer_vendas(registros, escopo)

    if termo:
        alvo = _normalizar(termo)
        registros = [x for x in registros if alvo in _normalizar(json.dumps(x, ensure_ascii=False, default=str))]
    if status:
        alvo = _normalizar(status)
        registros = [x for x in registros if _normalizar(x.get("status")) == alvo]

    total = len(registros)
    pagina = registros[offset: offset + limite]
    return {
        "dominio": dominio,
        "escopo": "global" if tipo_usuario == "ADMIN_MASTER" else "usuario_autorizado",
        "total_encontrado": total,
        "offset": offset,
        "limite": limite,
        "tem_mais": offset + len(pagina) < total,
        "resultado": pagina,
    }
